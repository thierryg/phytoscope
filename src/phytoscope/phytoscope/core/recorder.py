# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/recorder.py
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

"""Enregistrement d'une séance.

Une séance est un **répertoire**, pas un fichier. Il contient :

    2026-09-17_140233_ficus/
    ├── seance.json          métadonnées, réglages complets, étalonnage
    ├── signal.wav           signal brut, 24 bits, une piste par voie
    ├── musique.wav          rendu sonore (facultatif)
    ├── evenements.csv       un événement par ligne
    ├── notes.csv            une note par ligne
    ├── enonces.csv          un énoncé par ligne, si le mode vocal est actif
    └── marqueurs.csv        annotations posées pendant la séance

Ce choix a une raison : six mois plus tard, on veut pouvoir ouvrir le
répertoire et comprendre sans le logiciel. Le WAV s'ouvre dans Audacity, les
CSV dans un tableur, le JSON dans un éditeur de texte. Rien n'est enfermé.
"""
from __future__ import annotations

import csv
import json
import os
import struct
import threading
import time
import wave
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from .dsp import Event
from . import noms


# ---------------------------------------------------------------------------
#  Écriture WAV 24 bits
# ---------------------------------------------------------------------------
class Wave24Writer:
    """Écrit un WAV PCM 24 bits — format lisible par tous les éditeurs audio.

    Le signal est stocké en pleine échelle ±`full_scale` volts ; le facteur
    exact est consigné dans `seance.json`, faute de quoi le fichier serait
    joli mais inexploitable.
    """

    def __init__(self, path: str, sample_rate: int, channels: int,
                 full_scale_v: float = 2.5):
        self.path = path
        self.channels = channels
        self.full_scale = full_scale_v if full_scale_v > 0 else 1.0
        self.frames = 0
        self._wav = wave.open(path, "wb")
        self._wav.setnchannels(channels)
        self._wav.setsampwidth(3)
        self._wav.setframerate(int(round(sample_rate)))

    def write(self, data: np.ndarray) -> None:
        if data.ndim == 1:
            data = data[:, None]
        x = np.clip(data / self.full_scale, -1.0, 1.0 - 1e-9)
        ints = (x * 8388607.0).astype(np.int32)
        flat = ints.reshape(-1)
        raw = bytearray(flat.size * 3)
        for i, v in enumerate(flat.tolist()):
            v &= 0xFFFFFF
            raw[3 * i] = v & 0xFF
            raw[3 * i + 1] = (v >> 8) & 0xFF
            raw[3 * i + 2] = (v >> 16) & 0xFF
        self._wav.writeframes(bytes(raw))
        self.frames += data.shape[0]

    def close(self) -> None:
        try:
            self._wav.close()
        except Exception:                              # pragma: no cover
            pass


class Wave16Writer:
    """Écrit le rendu musical en 16 bits — ce qu'on envoie à un ami."""

    def __init__(self, path: str, sample_rate: int, channels: int = 1):
        self.path = path
        self.frames = 0
        self._wav = wave.open(path, "wb")
        self._wav.setnchannels(channels)
        self._wav.setsampwidth(2)
        self._wav.setframerate(int(round(sample_rate)))

    def write(self, data: np.ndarray) -> None:
        x = np.clip(np.asarray(data, dtype=np.float64), -1.0, 1.0)
        self._wav.writeframes((x * 32767.0).astype("<i2").tobytes())
        self.frames += x.shape[0]

    def close(self) -> None:
        try:
            self._wav.close()
        except Exception:                              # pragma: no cover
            pass


# ---------------------------------------------------------------------------
#  Séance
# ---------------------------------------------------------------------------
@dataclass
class SessionMeta:
    """Ce qu'il faut savoir pour relire une séance dans dix ans."""
    name: str = ""
    started_utc: str = ""
    ended_utc: str = ""
    duration_s: float = 0.0
    sample_rate: float = 250.0
    channels: int = 1
    full_scale_v: float = 2.5
    source_kind: str = ""
    source_name: str = ""
    board: Dict[str, Any] = field(default_factory=dict)
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, str] = field(default_factory=dict)
    clock: Dict[str, Any] = field(default_factory=dict)
    counts: Dict[str, int] = field(default_factory=dict)
    software: str = ""


class Recorder:
    """Enregistre une séance complète, en écrivant au fil de l'eau.

    Rien n'est gardé en mémoire : une séance de huit heures occupe autant de
    RAM qu'une séance de dix secondes. Les fichiers sont refermés proprement
    même si l'application est interrompue, grâce au `flush` régulier des CSV.
    """

    def __init__(self, directory: str, settings, source_info=None,
                 board=None, audio_rate: int = 44100):
        self.settings = settings
        self.root = directory
        self.dir = ""
        self.active = False
        self.lock = threading.Lock()
        self.t0 = 0.0
        self.samples = 0
        self.audio_rate = audio_rate
        self.source_info = source_info
        self.board = board
        self._sig: Optional[Wave24Writer] = None
        self._mus: Optional[Wave16Writer] = None
        self._events_f = None
        self._events = None
        self._notes_f = None
        self._notes = None
        self._marks_f = None
        self._marks = None
        self._enonces_f = None
        self._enonces = None
        self.n_events = 0
        self.n_notes = 0
        self.n_marks = 0
        self.n_enonces = 0
        self.last_error = ""

    # -- cycle de vie --------------------------------------------------------
    def start(self, label: str = "") -> Optional[str]:
        from ..music.lexicon import CSV_HEADER_VOCAL
        from ..music.mapper import CSV_HEADER as NOTE_HEADER
        with self.lock:
            if self.active:
                return self.dir
            stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            slug = _slug(label or self.settings.metadata.get("plante", "") or "seance")
            self.dir = os.path.join(self.root, f"{stamp}_{slug}")
            try:
                os.makedirs(self.dir, exist_ok=True)
            except OSError as exc:
                self.last_error = f"création du répertoire impossible : {exc}"
                return None
            rec = self.settings.recording
            fs = self.settings.acquisition.sample_rate
            ch = max(self.settings.acquisition.channels, 1)
            fsv = self.settings.acquisition.input_range_v
            try:
                if rec.write_wav:
                    self._sig = Wave24Writer(os.path.join(self.dir, "signal.wav"),
                                             int(round(fs)), ch, fsv)
                if rec.write_audio:
                    self._mus = Wave16Writer(os.path.join(self.dir, "musique.wav"),
                                             self.audio_rate, 1)
                if rec.write_csv:
                    self._events_f = open(os.path.join(self.dir, "evenements.csv"),
                                          "w", newline="", encoding="utf-8")
                    self._events = csv.writer(self._events_f)
                    self._events.writerow(["index", "temps_s", "amplitude_v",
                                           "pente_v_s", "sigma", "voie"])
                    self._notes_f = open(os.path.join(self.dir, "notes.csv"),
                                         "w", newline="", encoding="utf-8")
                    self._notes = csv.writer(self._notes_f)
                    self._notes.writerow(NOTE_HEADER)
                if rec.write_csv and getattr(self.settings, "voice", None) \
                        and self.settings.voice.enabled \
                        and self.settings.voice.write_csv:
                    self._enonces_f = open(os.path.join(self.dir, "enonces.csv"),
                                           "w", newline="", encoding="utf-8")
                    self._enonces = csv.writer(self._enonces_f)
                    self._enonces.writerow(CSV_HEADER_VOCAL)
                self._marks_f = open(os.path.join(self.dir, "marqueurs.csv"),
                                     "w", newline="", encoding="utf-8")
                self._marks = csv.writer(self._marks_f)
                self._marks.writerow(["temps_s", "horodatage_utc", "etiquette"])
            except OSError as exc:
                self.last_error = f"ouverture des fichiers impossible : {exc}"
                self._close_all()
                return None
            self.t0 = time.time()
            self.samples = 0
            self.n_events = self.n_notes = self.n_marks = self.n_enonces = 0
            self.active = True
            self._write_meta(final=False)
            return self.dir

    def stop(self) -> Optional[str]:
        with self.lock:
            if not self.active:
                return None
            self.active = False
            self._write_meta(final=True)
            self._close_all()
            return self.dir

    def _close_all(self) -> None:
        for obj in (self._sig, self._mus):
            if obj is not None:
                obj.close()
        for f in (self._events_f, self._notes_f, self._marks_f,
                  self._enonces_f):
            if f is not None:
                try:
                    f.close()
                except Exception:                      # pragma: no cover
                    pass
        self._sig = self._mus = None
        self._events_f = self._notes_f = self._marks_f = None
        self._enonces_f = None
        self._events = self._notes = self._marks = self._enonces = None

    # -- écritures -----------------------------------------------------------
    def write_signal(self, data: np.ndarray) -> None:
        if not self.active or self._sig is None:
            if self.active:
                self.samples += data.shape[0]
            return
        with self.lock:
            if self._sig is not None:
                self._sig.write(data)
                self.samples = self._sig.frames

    def write_audio(self, data: np.ndarray) -> None:
        if not self.active or self._mus is None:
            return
        with self.lock:
            if self._mus is not None:
                self._mus.write(data)

    def write_event(self, ev: Event) -> None:
        if not self.active or self._events is None:
            return
        with self.lock:
            if self._events is not None:
                self._events.writerow(ev.to_row())
                self.n_events += 1
                if self.n_events % 20 == 0 and self._events_f:
                    self._events_f.flush()

    def write_note(self, note) -> None:
        if not self.active or self._notes is None:
            return
        with self.lock:
            if self._notes is not None:
                self._notes.writerow(note.to_row())
                self.n_notes += 1
                if self.n_notes % 20 == 0 and self._notes_f:
                    self._notes_f.flush()

    def write_enonce(self, enonce) -> None:
        if not self.active or self._enonces is None:
            return
        with self.lock:
            if self._enonces is not None:
                self._enonces.writerow(enonce.to_row())
                self.n_enonces += 1
                if self.n_enonces % 10 == 0 and self._enonces_f:
                    self._enonces_f.flush()

    def write_mark(self, label: str, time_s: float) -> None:
        if not self.active or self._marks is None:
            return
        with self.lock:
            if self._marks is not None:
                self._marks.writerow([f"{time_s:.4f}",
                                      datetime.now(timezone.utc).isoformat(),
                                      label])
                self.n_marks += 1
                if self._marks_f:
                    self._marks_f.flush()

    # -- métadonnées ---------------------------------------------------------
    def _write_meta(self, final: bool) -> None:
        from .. import __version__, APP_NAME
        fs = self.settings.acquisition.sample_rate
        meta = SessionMeta(
            name=os.path.basename(self.dir),
            started_utc=datetime.fromtimestamp(self.t0, timezone.utc).isoformat(),
            ended_utc=datetime.now(timezone.utc).isoformat() if final else "",
            duration_s=self.samples / fs if fs else 0.0,
            sample_rate=fs,
            channels=max(self.settings.acquisition.channels, 1),
            full_scale_v=self.settings.acquisition.input_range_v,
            source_kind=getattr(self.source_info, "kind", ""),
            source_name=getattr(self.source_info, "name", ""),
            board=(self.board.raw if self.board is not None else {}),
            settings=self.settings.to_dict(),
            metadata=dict(self.settings.metadata),
            clock={"unix_start": self.t0, "samples": self.samples},
            counts={"evenements": self.n_events, "notes": self.n_notes,
                    "enonces": self.n_enonces, "marqueurs": self.n_marks},
            software=f"{APP_NAME} {__version__}")
        try:
            with open(os.path.join(self.dir, "seance.json"), "w",
                      encoding="utf-8") as f:
                json.dump(asdict(meta), f, ensure_ascii=False, indent=2)
        except OSError as exc:                         # pragma: no cover
            self.last_error = str(exc)

    @property
    def elapsed(self) -> float:
        fs = self.settings.acquisition.sample_rate
        return self.samples / fs if fs else 0.0


def _slug(text: str) -> str:
    """Nom de dossier de séance — voir `core.noms` pour le pourquoi."""
    return noms.assainir(text, defaut="seance", longueur=40)
