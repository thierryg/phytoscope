# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/instruments.py
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
    "Attaque nette, extinction rapide : chaque événement reste distinct."))
_add(Instrument(
    "piano_feutre", "Piano feutré", [(1, 1.0), (2, 0.28), (3, 0.09), (4, 0.04)],
    0.008, 1.2, 0.18, 1.4, 0, 1.0,
    "Le plus lisible pour comprendre ce que fait la plante."))
_add(Instrument(
    "cordes", "Cordes", [(1, 1.0), (2, 0.4), (3, 0.22), (4, 0.12), (5, 0.06)],
    0.45, 0.6, 0.72, 1.8, 48, 6.0,
    "Entrées lentes : les événements se fondent en nappe."))
_add(Instrument(
    "flute", "Flûte", [(1, 1.0), (2, 0.14), (3, 0.05)],
    0.12, 0.2, 0.85, 0.5, 73, 2.0,
    "Souffle pur, peu d'harmoniques : très proche du sinus."))
_add(Instrument(
    "cloche", "Cloche", [(1, 1.0), (2.76, 0.52), (5.4, 0.28), (8.9, 0.12)],
    0.002, 2.4, 0.0, 2.8, 14, 0.0,
    "Partiels inharmoniques : chaque note sonne comme un événement."))
_add(Instrument(
    "bourdon", "Bourdon (drone)", [(1, 1.0), (1.5, 0.3), (2, 0.5), (3, 0.16)],
    2.0, 1.0, 0.9, 3.0, 89, 8.0,
    "Tenue continue accordée sur la tonique : le fond de la séance.", -1))
_add(Instrument(
    "harpe", "Harpe", [(1, 1.0), (2, 0.36), (3, 0.16), (4, 0.07), (6, 0.03)],
    0.005, 0.9, 0.1, 1.2, 46, 1.5,
    "Compromis entre la kalimba et le piano ; supporte les arpèges."))
_add(Instrument(
    "verre", "Verre frotté", [(1, 1.0), (2, 0.2), (3.1, 0.3), (4.2, 0.1)],
    0.9, 0.5, 0.86, 2.2, 92, 4.0,
    "Timbre vitreux, très lent : pour les séances de méditation."))
_add(Instrument(
    "marimba", "Marimba", [(1, 1.0), (3.9, 0.4), (10.2, 0.1)],
    0.003, 0.45, 0.02, 0.6, 12, 0.0,
    "Bois, bref et rond : lisible en extérieur."))
_add(Instrument(
    "sinus", "Sinus pur", [(1, 1.0)], 0.02, 0.1, 0.9, 0.3, 80, 0.0,
    "Aucun timbre : sert à vérifier la justesse et l'étalonnage."))


def instrument_list() -> List[Tuple[str, str]]:
    return [(k, v.label) for k, v in INSTRUMENTS.items()]


def get(key: str) -> Instrument:
    return INSTRUMENTS.get(key, INSTRUMENTS["kalimba"])
