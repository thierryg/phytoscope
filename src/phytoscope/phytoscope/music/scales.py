# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/scales.py
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

"""Gammes, modes et quantification.

Une gamme est décrite par ses intervalles en demi-tons depuis la tonique.
Le choix de la gamme est le réglage qui change le plus l'écoute : il est
donc exposé au premier plan de l'interface, et documenté ici pour que
chacun puisse en ajouter une.
"""
from __future__ import annotations

import math
from typing import Dict, List, Tuple

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_NAMES_FR = ["Do", "Do#", "Ré", "Ré#", "Mi", "Fa", "Fa#", "Sol", "Sol#",
                 "La", "La#", "Si"]

# ---------------------------------------------------------------------------
#  Diapasons
#
#  Les appareils du commerce (Music of the Plants U1 Pro et Bamboo) proposent
#  trois références : 440 Hz, la norme ISO 16 ; 432 Hz, prisée dans les
#  milieux du son thérapeutique ; et 426,7 Hz, qui correspond au « la » de
#  Verdi tel qu'on le retrouve dans certaines reconstitutions historiques.
#
#  Il faut le dire nettement : aucune étude contrôlée n'établit d'effet
#  physiologique propre au 432 Hz. Le réglage est fourni parce qu'il est
#  demandé, qu'il change réellement la couleur sonore, et que rien n'oblige
#  une écoute à se justifier — mais il est présenté comme un choix
#  esthétique, pas comme une propriété de la plante.
# ---------------------------------------------------------------------------
DIAPASONS: Dict[str, Tuple[float, str]] = {
    "440": (440.0, "440 Hz — norme ISO 16, accord d'orchestre"),
    "432": (432.0, "432 Hz — accord dit « naturel », usage thérapeutique"),
    "426.7": (426.7, "426,7 Hz — accord historique dit « de Verdi »"),
    "415": (415.0, "415 Hz — diapason baroque, un demi-ton plus bas"),
}

DIAPASON_DEFAUT = 440.0


SCALES: Dict[str, Tuple[str, List[int]]] = {
    "pentatonique_majeure": ("Pentatonique majeure", [0, 2, 4, 7, 9]),
    "pentatonique_mineure": ("Pentatonique mineure", [0, 3, 5, 7, 10]),
    "majeure":              ("Majeure (ionien)", [0, 2, 4, 5, 7, 9, 11]),
    "mineure_naturelle":    ("Mineure naturelle (éolien)", [0, 2, 3, 5, 7, 8, 10]),
    "dorien":               ("Dorien", [0, 2, 3, 5, 7, 9, 10]),
    "lydien":               ("Lydien", [0, 2, 4, 6, 7, 9, 11]),
    "mixolydien":           ("Mixolydien", [0, 2, 4, 5, 7, 9, 10]),
    "hirajoshi":            ("Hirajōshi (Japon)", [0, 2, 3, 7, 8]),
    "in_sen":               ("In sen (Japon)", [0, 1, 5, 7, 10]),
    "raga_bhairav":         ("Rāga Bhairav (Inde)", [0, 1, 4, 5, 7, 8, 11]),
    "hijaz":                ("Hijaz (maqâm)", [0, 1, 4, 5, 7, 8, 10]),
    "chromatique":          ("Chromatique (aucune quantification)",
                             [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
    "harmoniques":          ("Série harmonique (justesse naturelle)",
                             [0, 2, 4, 7, 9, 10]),
    # --- gammes supplémentaires, pour atteindre les dix-neuf proposées par
    #     les appareils du commerce et couvrir d'autres traditions ---------
    "phrygien":             ("Phrygien", [0, 1, 3, 5, 7, 8, 10]),
    "locrien":              ("Locrien", [0, 1, 3, 5, 6, 8, 10]),
    "mineure_harmonique":   ("Mineure harmonique", [0, 2, 3, 5, 7, 8, 11]),
    "mineure_melodique":    ("Mineure mélodique", [0, 2, 3, 5, 7, 9, 11]),
    "blues":                ("Blues", [0, 3, 5, 6, 7, 10]),
    "tons_entiers":         ("Par tons entiers", [0, 2, 4, 6, 8, 10]),
    "diminuee":             ("Diminuée (ton–demi-ton)", [0, 2, 3, 5, 6, 8, 9, 11]),
    "egyptienne":           ("Égyptienne (suspendue)", [0, 2, 5, 7, 10]),
    "kumoi":                ("Kumoï (Japon)", [0, 2, 3, 7, 9]),
    "iwato":                ("Iwato (Japon)", [0, 1, 5, 6, 10]),
    "raga_todi":            ("Rāga Todi (Inde)", [0, 1, 3, 6, 7, 8, 11]),
    "raga_yaman":           ("Rāga Yaman (Inde)", [0, 2, 4, 6, 7, 9, 11]),
    "hongroise":            ("Tsigane hongroise", [0, 2, 3, 6, 7, 8, 11]),
}


def scale_names() -> List[Tuple[str, str]]:
    """(clé, libellé) de toutes les gammes, dans l'ordre de déclaration."""
    return [(k, v[0]) for k, v in SCALES.items()]


def root_index(name: str) -> int:
    """Indice chromatique d'une tonique écrite « D », « Ré » ou « D#»."""
    n = name.strip().replace("b", "#").capitalize()
    for table in (NOTE_NAMES, NOTE_NAMES_FR):
        for i, v in enumerate(table):
            if v.lower() == n.lower():
                return i
    return 2  # ré par défaut : agréable et grave sur la plupart des timbres


def build_notes(scale: str, root: str, octave_low: int = 3,
                octave_span: int = 3) -> List[int]:
    """Liste des numéros MIDI utilisables, du grave à l'aigu."""
    steps = SCALES.get(scale, SCALES["pentatonique_majeure"])[1]
    r = root_index(root)
    notes: List[int] = []
    for octave in range(octave_low, octave_low + max(octave_span, 1)):
        base = (octave + 1) * 12 + r          # C4 = 60 avec cette convention
        for s in steps:
            n = base + s
            if 0 <= n <= 127:
                notes.append(n)
    return sorted(set(notes))


def quantize(value01: float, notes: List[int]) -> int:
    """Projette une valeur normalisée [0, 1] sur la gamme."""
    if not notes:
        return 60
    v = min(max(value01, 0.0), 1.0)
    return notes[min(int(v * len(notes)), len(notes) - 1)]


def note_name(midi: int, french: bool = True) -> str:
    table = NOTE_NAMES_FR if french else NOTE_NAMES
    return f"{table[midi % 12]}{midi // 12 - 1}"


def midi_to_hz(midi: float, a4: float = DIAPASON_DEFAUT) -> float:
    """Fréquence d'une note, pour un diapason donné.

    Le numéro 69 est le « la » de référence ; toutes les autres notes s'en
    déduisent par la relation tempérée à douze degrés égaux.
    """
    return a4 * (2.0 ** ((midi - 69.0) / 12.0))


def hz_to_midi(freq: float, a4: float = DIAPASON_DEFAUT) -> float:
    """Numéro de note (non entier) correspondant à une fréquence."""
    if freq <= 0:
        return 0.0
    return 69.0 + 12.0 * math.log2(freq / a4)


def diapason_list() -> List[Tuple[str, str]]:
    return [(k, v[1]) for k, v in DIAPASONS.items()]


def ecart_cents(freq: float, midi: int, a4: float = DIAPASON_DEFAUT) -> float:
    """Écart, en centièmes de demi-ton, entre une fréquence et une note."""
    ref = midi_to_hz(midi, a4)
    if freq <= 0 or ref <= 0:
        return 0.0
    return 1200.0 * math.log2(freq / ref)


def describe_scale(scale: str, root: str, a4: float = DIAPASON_DEFAUT,
                   octave_low: int = 3, octave_span: int = 3) -> List[str]:
    """Description lisible d'une gamme : degrés, notes, fréquences.

    C'est le genre de tableau qu'on veut avoir sous les yeux quand on
    explique à quelqu'un ce que fait l'appareil — et qui manque dans tous
    les logiciels comparables.
    """
    nom, degres = SCALES.get(scale, SCALES["pentatonique_majeure"])
    notes = build_notes(scale, root, octave_low, octave_span)
    lignes = [f"{nom} sur {root} — diapason {a4:g} Hz",
              f"Degrés (demi-tons) : {', '.join(str(d) for d in degres)}",
              f"{len(notes)} notes disponibles, de {note_name(notes[0])} "
              f"({midi_to_hz(notes[0], a4):.2f} Hz) à {note_name(notes[-1])} "
              f"({midi_to_hz(notes[-1], a4):.2f} Hz)" if notes else "aucune note"]
    return lignes
