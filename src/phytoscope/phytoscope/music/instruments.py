# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/instruments.py
#
#  Version   : 1.6.0
#  Date      : 2026-09-23
#  Publisher : Bretagne Namasté
#  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Website   : https://bretagne-namaste.com
#  Contact   : contact@bretagne-namaste.com
#  License   : MIT — see LICENSE.txt
#
#  SPDX-License-Identifier: MIT
#  end of attribution
#  ==========================================================================

"""Instruments : le timbre et son enveloppe.

Chaque instrument est une recette additive simple — quelques partiels, une
enveloppe ADSR, un peu de désaccord — plus un numéro de programme General
MIDI pour ceux qui préfèrent piloter un synthétiseur externe.

Le choix est volontairement restreint à des timbres qui supportent la
lenteur : une plante ne joue pas vite, et un timbre percussif brillant
devient vite fatigant sur une séance d'une heure.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass
class Instrument:
    key: str
    label: str
    partials: List[Tuple[float, float]]   # (rapport de fréquence, amplitude)
    attack: float                          # secondes
    decay: float
    sustain: float                         # niveau relatif 0..1
    release: float
    gm_program: int                        # numéro General MIDI (0..127)
    detune_cents: float = 0.0
    description: str = ""
    octave_shift: int = 0

    def envelope_total(self) -> float:
        return self.attack + self.decay + self.release


INSTRUMENTS: Dict[str, Instrument] = {}


def _add(inst: Instrument) -> None:
    INSTRUMENTS[inst.key] = inst


_add(Instrument(
    "kalimba", "Kalimba", [(1, 1.0), (2.01, 0.34), (3.04, 0.12), (5.1, 0.05)],
    0.004, 0.55, 0.06, 0.9, 108, 2.0,
    "Sharp attack, quick decay: every event stays distinct."))
_add(Instrument(
    "piano_feutre", "Muted piano", [(1, 1.0), (2, 0.28), (3, 0.09), (4, 0.04)],
    0.008, 1.2, 0.18, 1.4, 0, 1.0,
    "The most legible one for understanding what the plant is doing."))
_add(Instrument(
    "cordes", "Strings", [(1, 1.0), (2, 0.4), (3, 0.22), (4, 0.12), (5, 0.06)],
    0.45, 0.6, 0.72, 1.8, 48, 6.0,
    "Slow attacks: the events melt into a pad."))
_add(Instrument(
    "flute", "Flute", [(1, 1.0), (2, 0.14), (3, 0.05)],
    0.12, 0.2, 0.85, 0.5, 73, 2.0,
    "Pure breath, few harmonics: very close to a sine."))
_add(Instrument(
    "cloche", "Bell", [(1, 1.0), (2.76, 0.52), (5.4, 0.28), (8.9, 0.12)],
    0.002, 2.4, 0.0, 2.8, 14, 0.0,
    "Inharmonic partials: every note sounds like an event."))
_add(Instrument(
    "bourdon", "Drone", [(1, 1.0), (1.5, 0.3), (2, 0.5), (3, 0.16)],
    2.0, 1.0, 0.9, 3.0, 89, 8.0,
    "A continuous tone on the root: the background of the session.", -1))
_add(Instrument(
    "harpe", "Harp", [(1, 1.0), (2, 0.36), (3, 0.16), (4, 0.07), (6, 0.03)],
    0.005, 0.9, 0.1, 1.2, 46, 1.5,
    "A compromise between the kalimba and the piano; it takes arpeggios well."))
_add(Instrument(
    "verre", "Glass harmonica", [(1, 1.0), (2, 0.2), (3.1, 0.3), (4.2, 0.1)],
    0.9, 0.5, 0.86, 2.2, 92, 4.0,
    "Glassy, very slow timbre: for meditation sessions."))
_add(Instrument(
    "marimba", "Marimba", [(1, 1.0), (3.9, 0.4), (10.2, 0.1)],
    0.003, 0.45, 0.02, 0.6, 12, 0.0,
    "Wooden, short and round: legible outdoors."))
_add(Instrument(
    "sinus", "Pure sine", [(1, 1.0)], 0.02, 0.1, 0.9, 0.3, 80, 0.0,
    "No timbre at all: used to check tuning and calibration."))


def instrument_list() -> List[Tuple[str, str]]:
    return [(k, v.label) for k, v in INSTRUMENTS.items()]


def get(key: str) -> Instrument:
    return INSTRUMENTS.get(key, INSTRUMENTS["kalimba"])
