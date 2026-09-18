# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/midi_out.py
#
#  Version  : 1.5.1
#  Date     : 2026-09-18
#  Éditeur  : Bretagne Namasté
#  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Site     : https://bretagne-namaste.com
#  Contact  : contact@bretagne-namaste.com
#  Licence  : MIT — voir LICENCE.txt
#
#  SPDX-License-Identifier: MIT
#  fin de l'attribution
#  ==========================================================================

"""Sortie MIDI — pour confier le timbre à un vrai instrument.

Le synthétiseur interne suffit pour écouter ; la sortie MIDI sert dès qu'on
veut jouer la plante dans un séquenceur, un synthétiseur matériel ou un
orgue d'église virtuel. Elle est facultative : si `python-rtmidi` n'est pas
installé, le logiciel le signale une fois et continue.
"""
from __future__ import annotations

import sys
import threading
import time
from typing import List, Optional, Tuple

NOTE_ON = 0x90
NOTE_OFF = 0x80
PROGRAM_CHANGE = 0xC0
CONTROL_CHANGE = 0xB0


class MidiOut:
    def __init__(self) -> None:
        self._port = None
        self._name = ""
        self.last_error = ""
        self._pending: List[Tuple[float, int, int]] = []   # (échéance, note, canal)
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    # -- ports ---------------------------------------------------------------
    @staticmethod
    def list_ports() -> List[str]:
        try:
            import rtmidi
        except ImportError:
            return []
        try:
            out = rtmidi.MidiOut()
            names = out.get_ports()
            del out
            return list(names)
        except Exception:                              # pragma: no cover
            return []

    def open(self, name: str = "", virtual_name: str = "PhytoScope") -> bool:
        try:
            import rtmidi
        except ImportError:
            self.last_error = ("python-rtmidi n'est pas installé. "
                               "Installez-le avec : pip install python-rtmidi")
            return False
        try:
            port = rtmidi.MidiOut()
            ports = port.get_ports()
            if name and name in ports:
                port.open_port(ports.index(name))
                self._name = name
            elif ports and not name:
                port.open_port(0)
                self._name = ports[0]
            elif sys.platform.startswith("win"):
                #  L'interface MIDI de Windows ne sait pas créer de port
                #  virtuel : RtMidi lève, et l'utilisateur n'a aucun moyen de
                #  deviner qu'il lui faut un pilote de bouclage. On le lui dit
                #  plutôt que de lui rendre un échec muet.
                self.last_error = (
                    "aucun port MIDI disponible. Windows ne permet pas de "
                    "créer un port virtuel : branchez un instrument, ou "
                    "installez un pilote de bouclage tel que loopMIDI.")
                return False
            else:
                port.open_virtual_port(virtual_name)
                self._name = virtual_name + " (virtuel)"
            self._port = port
        except Exception as exc:
            self.last_error = f"ouverture MIDI impossible : {exc}"
            if sys.platform.startswith("win"):
                self.last_error += (
                    " Sous Windows, un port virtuel est impossible : branchez "
                    "un instrument ou installez loopMIDI.")
            return False
        self._running = True
        self._thread = threading.Thread(target=self._run, name="midi", daemon=True)
        self._thread.start()
        return True

    def close(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=0.5)
            self._thread = None
        with self._lock:
            pend = list(self._pending)
            self._pending.clear()
        for _, note, ch in pend:
            self._send(NOTE_OFF | (ch & 0x0F), note, 0)
        if self._port is not None:
            try:
                self._port.close_port()
            finally:
                self._port = None

    @property
    def is_open(self) -> bool:
        return self._port is not None

    @property
    def port_name(self) -> str:
        return self._name

    # -- messages ------------------------------------------------------------
    def _send(self, status: int, d1: int, d2: int) -> None:
        if self._port is None:
            return
        try:
            self._port.send_message([status & 0xFF, d1 & 0x7F, d2 & 0x7F])
        except Exception as exc:                       # pragma: no cover
            self.last_error = str(exc)

    def program(self, program: int, channel: int = 1) -> None:
        if self._port is None:
            return
        try:
            self._port.send_message([PROGRAM_CHANGE | ((channel - 1) & 0x0F),
                                     program & 0x7F])
        except Exception:                              # pragma: no cover
            pass

    def note(self, midi: int, velocity: int, duration: float,
             channel: int = 1) -> None:
        """Joue une note ; l'extinction est programmée automatiquement."""
        ch = (channel - 1) & 0x0F
        self._send(NOTE_ON | ch, midi, max(1, min(velocity, 127)))
        with self._lock:
            self._pending.append((time.monotonic() + max(duration, 0.05), midi, ch))

    def control(self, cc: int, value: int, channel: int = 1) -> None:
        self._send(CONTROL_CHANGE | ((channel - 1) & 0x0F), cc, value)

    def panic(self) -> None:
        for ch in range(16):
            self._send(CONTROL_CHANGE | ch, 123, 0)    # all notes off
        with self._lock:
            self._pending.clear()

    # -- extinction différée -------------------------------------------------
    def _run(self) -> None:
        while self._running:
            now = time.monotonic()
            due = []
            with self._lock:
                keep = []
                for item in self._pending:
                    (due if item[0] <= now else keep).append(item)
                self._pending = keep
            for _, note, ch in due:
                self._send(NOTE_OFF | ch, note, 0)
            time.sleep(0.005)
