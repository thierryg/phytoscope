# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/profiles.py
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

"""Profils musicaux préréglés et banque General MIDI.

Les appareils du commerce (Ginkgo, Bamboo, U1 Pro) proposent des « profils » :
un réglage complet — instrument, gamme, fréquence de base, tempo maximal —
rappelé d'un bouton. Trois profils sur le Ginkgo, douze sur le Bamboo et le
U1 Pro. C'est une bonne idée, parce que régler douze paramètres devant une
plante et vingt personnes n'est pas une situation propice.

Ce module fournit donc douze profils équivalents, plus la banque des
cent vingt-huit timbres General MIDI pour qui pilote un synthétiseur externe.

Chaque profil est documenté par ce qu'il cherche à obtenir : un profil n'est
pas un réglage « meilleur », c'est un parti pris d'écoute.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Profile:
    """Un réglage musical complet, rappelable d'un geste."""
    key: str
    label: str
    description: str
    scale: str
    root: str
    instrument: str
    diapason_hz: float = 440.0
    octave_low: int = 3
    octave_span: int = 3
    density_per_min: float = 24.0
    note_len_min_s: float = 0.25
    note_len_max_s: float = 4.0
    reverb: float = 0.35
    chorus: float = 0.0
    spatial: float = 0.0
    polyphony_voices: int = 3
    drone: bool = True
    gm_program: int = -1

    def appliquer(self, settings) -> List[str]:
        """Applique le profil ; renvoie la liste des changements."""
        m = settings.music
        avant = (m.scale, m.root, m.instrument, m.diapason_hz)
        m.scale = self.scale
        m.root = self.root
        m.instrument = self.instrument
        m.diapason_hz = self.diapason_hz
        m.octave_low = self.octave_low
        m.octave_span = self.octave_span
        m.density_per_min = self.density_per_min
        m.note_len_min_s = self.note_len_min_s
        m.note_len_max_s = self.note_len_max_s
        m.reverb = self.reverb
        m.chorus = self.chorus
        m.spatial = self.spatial
        m.polyphony_voices = self.polyphony_voices
        m.drone_enabled = self.drone
        m.gm_program = self.gm_program
        m.profile = self.key
        return [f"gamme {avant[0]} → {self.scale}",
                f"tonique {avant[1]} → {self.root}",
                f"timbre {avant[2]} → {self.instrument}",
                f"diapason {avant[3]:g} → {self.diapason_hz:g} Hz"]


PROFILS: Tuple[Profile, ...] = (
    Profile("meditation", "1 · Meditation",
            "Notes rares et longues, bourdon tenu : pour une séance assise.",
            "pentatonique_majeure", "D", "verre", 432.0, 2, 3, 8.0, 3.0, 9.0,
            0.55, 0.2, 0.4, 1, True),
    Profile("decouverte", "2 · Discovery",
            "Chaque événement s'entend distinctement : le profil qui fait "
            "comprendre ce que mesure l'appareil.",
            "pentatonique_majeure", "C", "kalimba", 440.0, 3, 3, 30.0, 0.2, 2.0,
            0.25, 0.0, 0.0, 3, False),
    Profile("atelier", "3 · Workshop",
            "Lisible dans une salle bruyante, avec du relief et peu de traîne.",
            "majeure", "G", "marimba", 440.0, 3, 3, 36.0, 0.15, 1.5,
            0.2, 0.1, 0.0, 3, False),
    Profile("foret", "4 · Forest",
            "Registre grave, cordes lentes : pour un arbre, dehors.",
            "dorien", "A", "cordes", 432.0, 2, 3, 12.0, 2.0, 8.0,
            0.6, 0.3, 0.5, 3, True),
    Profile("aube", "5 · Dawn",
            "Clair et aérien, sans basse : accompagne un lever de jour.",
            "lydien", "F", "flute", 440.0, 4, 2, 20.0, 0.6, 3.0,
            0.4, 0.15, 0.2, 2, False),
    Profile("nuit", "6 · Night",
            "Cloches espacées sur un bourdon grave : veille nocturne.",
            "hirajoshi", "E", "cloche", 432.0, 2, 3, 6.0, 2.0, 10.0,
            0.65, 0.1, 0.6, 2, True),
    Profile("japon", "7 · Japan",
            "Gamme in sen, harpe : intervalles serrés, couleur modale.",
            "in_sen", "A", "harpe", 440.0, 3, 2, 18.0, 0.5, 4.0,
            0.35, 0.0, 0.1, 3, True),
    Profile("inde", "8 · India",
            "Rāga Bhairav sur bourdon : la référence tonale ne bouge jamais.",
            "raga_bhairav", "C", "cordes", 432.0, 3, 2, 14.0, 1.0, 6.0,
            0.5, 0.2, 0.3, 2, True),
    Profile("celtique", "9 · Celtic",
            "Mixolydien à la harpe, tempo souple.",
            "mixolydien", "D", "harpe", 440.0, 3, 3, 22.0, 0.4, 3.5,
            0.4, 0.1, 0.2, 3, True),
    Profile("minimaliste", "10 · Minimalist",
            "Une seule voix, piano feutré : rien ne masque le signal.",
            "pentatonique_mineure", "A", "piano_feutre", 440.0, 3, 2, 16.0,
            0.8, 5.0, 0.3, 0.0, 0.0, 1, False),
    Profile("mesure", "11 · Measurement",
            "Sinus pur, gamme chromatique : la note suit l'amplitude sans "
            "aucun habillage. C'est le profil à utiliser pour vérifier "
            "l'étalonnage — et pour se rappeler ce que fait vraiment "
            "l'appareil.",
            "chromatique", "C", "sinus", 440.0, 4, 2, 60.0, 0.15, 1.0,
            0.0, 0.0, 0.0, 1, False),
    Profile("verdi", "12 · Historical",
            "Diapason de Verdi à 426,7 Hz, cordes : une autre couleur.",
            "mineure_naturelle", "D", "cordes", 426.7, 3, 3, 18.0, 1.0, 5.0,
            0.45, 0.25, 0.3, 3, True),
)


def profile_list() -> List[Tuple[str, str]]:
    return [(p.key, p.label) for p in PROFILS]


def get(key: str) -> Optional[Profile]:
    for p in PROFILS:
        if p.key == key:
            return p
    return None


# ---------------------------------------------------------------------------
#  Banque General MIDI
# ---------------------------------------------------------------------------
#  Les cent vingt-huit timbres de la norme General MIDI, dans l'ordre des
#  numéros de programme. Ils ne servent qu'à la sortie MIDI : le rendu réel
#  dépend du synthétiseur qui les reçoit.
GM_FAMILLES = (
    "Piano", "Percussions chromatiques", "Orgue", "Guitare", "Basse",
    "Cordes solo", "Ensembles", "Cuivres", "Anches", "Flûtes",
    "Synthé — thèmes", "Synthé — nappes", "Synthé — effets", "Ethnique",
    "Percussions", "Effets sonores")

GM_INSTRUMENTS: Tuple[str, ...] = (
    "Piano à queue", "Piano droit", "Piano électrique", "Piano-forte",
    "Piano Rhodes", "Piano chorus", "Clavecin", "Clavinet",
    "Célesta", "Glockenspiel", "Boîte à musique", "Vibraphone",
    "Marimba", "Xylophone", "Cloches tubulaires", "Dulcimer",
    "Orgue Hammond", "Orgue percussif", "Orgue rock", "Orgue d'église",
    "Harmonium", "Accordéon", "Harmonica", "Bandonéon",
    "Guitare nylon", "Guitare acier", "Guitare jazz", "Guitare claire",
    "Guitare étouffée", "Guitare saturée", "Guitare distordue", "Harmoniques",
    "Basse acoustique", "Basse doigt", "Basse médiator", "Basse fretless",
    "Basse slap 1", "Basse slap 2", "Basse synthé 1", "Basse synthé 2",
    "Violon", "Alto", "Violoncelle", "Contrebasse",
    "Cordes trémolo", "Cordes pizzicato", "Harp", "Timbales",
    "Ensemble à cordes 1", "Ensemble à cordes 2", "Cordes synthé 1",
    "Cordes synthé 2", "Chœur « aah »", "Voix « ooh »", "Voix synthé",
    "Coup d'orchestre",
    "Trompette", "Trombone", "Tuba", "Trompette bouchée",
    "Cor d'harmonie", "Section de cuivres", "Cuivres synthé 1", "Cuivres synthé 2",
    "Saxophone soprano", "Saxophone alto", "Saxophone ténor", "Saxophone baryton",
    "Hautbois", "Cor anglais", "Basson", "Clarinette",
    "Piccolo", "Flûte traversière", "Flûte à bec", "Flûte de pan",
    "Bouteille soufflée", "Shakuhachi", "Sifflet", "Ocarina",
    "Synthé carré", "Synthé dent de scie", "Calliope", "Chiff",
    "Charang", "Voix synthé", "Quintes", "Basse et thème",
    "Nappe nouvelle", "Nappe chaude", "Nappe polysynthé", "Nappe chœur",
    "Nappe archet", "Nappe métallique", "Nappe halo", "Nappe balayée",
    "Pluie", "Bande-son", "Cristal", "Atmosphère",
    "Brillance", "Lutins", "Échos", "Science-fiction",
    "Sitar", "Banjo", "Shamisen", "Koto",
    "Kalimba", "Cornemuse", "Vielle", "Shanai",
    "Clochette", "Agogô", "Steel drums", "Woodblock",
    "Taiko", "Tom mélodique", "Tom synthé", "Cymbale inversée",
    "Frette de guitare", "Souffle", "Bord de mer", "Chant d'oiseau",
    "Sonnerie de téléphone", "Hélicoptère", "Applaudissements", "Coup de feu",
)


def gm_name(program: int) -> str:
    """Nom du timbre General MIDI (programme 0 à 127)."""
    if 0 <= program < len(GM_INSTRUMENTS):
        return f"{program + 1:3d} — {GM_INSTRUMENTS[program]}"
    return f"{program} — hors norme"


def gm_family(program: int) -> str:
    return GM_FAMILLES[min(max(program, 0) // 8, len(GM_FAMILLES) - 1)]


def gm_list() -> List[Tuple[int, str]]:
    return [(i, gm_name(i)) for i in range(len(GM_INSTRUMENTS))]
