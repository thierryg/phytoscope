# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/mapper.py
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

"""Le moteur de correspondance : du microvolt à la note.

C'est ici que se joue l'honnêteté du logiciel. Toute sonification est une
interprétation ; la seule façon de rester loyal est de rendre chaque règle
explicite, réglable, et consignée dans le fichier de séance — de sorte
qu'on puisse, six mois plus tard, savoir pourquoi cette note-là a sonné.

Règles appliquées, dans l'ordre :

1. l'amplitude de l'événement, normalisée par l'écart-type courant, donne
   la **hauteur** (plus l'écart est grand, plus la note est aiguë) ;
2. la pente donne la **nuance** (une montée brusque frappe plus fort) ;
3. la durée depuis l'événement précédent donne la **longueur** de la note ;
4. une contrainte de densité empêche la saturation rythmique ;
5. une contrainte d'anti-répétition évite de rejouer trois fois la même note.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from ..core.dsp import Event
from .instruments import get as get_instrument
from .scales import build_notes, note_name, quantize


@dataclass
class Note:
    """Une note décidée par le moteur, prête à être jouée et consignée."""
    midi: int
    velocity: int
    duration: float
    time_s: float
    instrument: str
    source_event: Optional[Event] = None
    reason: str = ""

    def name(self) -> str:
        return note_name(self.midi)

    def to_row(self) -> List[str]:
        e = self.source_event
        return [f"{self.time_s:.4f}", str(self.midi), self.name(),
                str(self.velocity), f"{self.duration:.3f}", self.instrument,
                f"{(e.amplitude_v if e else 0.0):.9f}",
                f"{(e.sigma if e else 0.0):.2f}", self.reason]


CSV_HEADER = ["temps_s", "midi", "note", "velocite", "duree_s", "instrument",
              "amplitude_v", "sigma", "regle"]


class Mapper:
    """Transforme un flux d'événements en un flux de notes."""

    def __init__(self, settings):
        self.settings = settings
        self.notes: List[int] = []
        self.last_note: Optional[int] = None
        self.repeat_count = 0
        self.last_time = -1e9
        self.recent: List[float] = []          # horodatage des dernières notes
        self.refresh()

    # -- configuration -------------------------------------------------------
    def refresh(self) -> None:
        m = self.settings.music
        self.notes = build_notes(m.scale, m.root, m.octave_low, m.octave_span)

    @property
    def tonic_midi(self) -> int:
        return self.notes[0] if self.notes else 62

    # -- cœur ----------------------------------------------------------------
    def map_event(self, ev: Event, now: Optional[float] = None) -> Optional[Note]:
        m = self.settings.music
        if not m.enabled or not self.notes:
            return None
        now = ev.time_s if now is None else now

        # 1. densité : on refuse poliment les événements trop rapprochés
        min_gap = 60.0 / max(m.density_per_min, 1.0)
        self.recent = [t for t in self.recent if now - t < 60.0]
        if now - self.last_time < min_gap:
            return None

        # 2. hauteur : l'amplitude en sigma, comprimée puis projetée
        sigma = max(ev.sigma, 0.0)
        position = _compress(sigma, knee=self.settings.processing.event_threshold_sigma)
        midi = quantize(position, self.notes)
        reason = f"σ={sigma:.1f} → {position:.2f}"

        # 3. anti-répétition : au bout de deux fois, on décale d'un degré
        if midi == self.last_note:
            self.repeat_count += 1
            if self.repeat_count >= 2:
                idx = self.notes.index(midi)
                idx = min(idx + 1, len(self.notes) - 1) if idx + 1 < len(self.notes) \
                    else max(idx - 1, 0)
                midi = self.notes[idx]
                reason += " (anti-répétition)"
                self.repeat_count = 0
        else:
            self.repeat_count = 0

        # 4. nuance : la pente, rapportée à une pente de référence
        slope = abs(ev.slope_v_s)
        v01 = _compress(slope / 1e-4, knee=1.0)
        velocity = int(m.velocity_min + v01 * (m.velocity_max - m.velocity_min))
        velocity = max(1, min(velocity, 127))

        # 5. durée : plus l'événement est isolé, plus la note respire
        gap = min(now - self.last_time, 30.0)
        d01 = min(gap / 20.0, 1.0)
        duration = m.note_len_min_s + d01 * (m.note_len_max_s - m.note_len_min_s)

        self.last_note = midi
        self.last_time = now
        self.recent.append(now)
        return Note(midi=midi, velocity=velocity, duration=duration, time_s=now,
                    instrument=m.instrument, source_event=ev, reason=reason)

    # -- bourdon -------------------------------------------------------------
    def drone_note(self) -> Optional[int]:
        m = self.settings.music
        if not (m.enabled and m.drone_enabled and self.notes):
            return None
        return self.tonic_midi

    def gm_program(self) -> int:
        return get_instrument(self.settings.music.instrument).gm_program

    def describe_rules(self) -> List[str]:
        m = self.settings.music
        return [
            f"Gamme : {m.scale} sur {m.root}, {len(self.notes)} notes disponibles",
            f"Hauteur ← amplitude de l'événement (en écarts-types)",
            f"Nuance ← pente au déclenchement, entre {m.velocity_min} et {m.velocity_max}",
            f"Durée ← temps écoulé depuis la note précédente "
            f"({m.note_len_min_s:g} à {m.note_len_max_s:g} s)",
            f"Densité maximale : {m.density_per_min:g} notes par minute",
        ]


def _compress(x: float, knee: float = 3.5) -> float:
    """Compression douce vers [0, 1] — linéaire au début, saturante ensuite."""
    if x <= 0:
        return 0.0
    return min(1.0, (x / knee) / (1.0 + x / (knee * 2.2)))
