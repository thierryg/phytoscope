# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/disk_space.py
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

"""Espace disque : combien il en reste, pour combien de temps, et quand s'arrêter.

Une séance longue écrit sans relâche. Le compte est vite fait, et il surprend :

======================  ===========================  ==================
Fichier                 Débit                        En une heure
======================  ===========================  ==================
signal.wav              3 octets × fs × voies        2,6 Mo à 250 Hz
musique.wav             2 octets × 44 100            317 Mo
evenements.csv          quelques octets par événement quelques kilo-octets
======================  ===========================  ==================

C'est le rendu musical qui remplit le disque — trois cents mégaoctets l'heure,
soit un disque de démonstration plein en une nuit. Un logiciel de mesure qui
remplit le disque de son hôte est un logiciel malpoli ; pire, il perd la fin de
la séance, c'est-à-dire souvent ce qu'on attendait.

D'où trois règles :

1. on **mesure** l'espace restant pendant l'enregistrement, pas avant ;
2. on **prévient** tant qu'il est encore temps de faire de la place ;
3. on **arrête proprement** un peu avant la saturation, en refermant les
   fichiers — un enregistrement clos vaut infiniment mieux qu'un enregistrement
   tronqué par une erreur d'écriture.

La réserve par défaut est de 500 Mo. Elle n'est pas là pour le logiciel mais
pour le système : un disque réellement plein empêche d'enregistrer les réglages,
d'écrire le journal, et parfois d'ouvrir une session.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from typing import Optional

__all__ = ["Espace", "mesurer", "debit_mo_par_heure", "autonomie_heures",
           "formater_mo", "formater_duree"]

MO = 1024.0 * 1024.0


@dataclass
class Espace:
    """L'état du disque qui accueille les séances."""
    chemin: str = ""
    total_mo: float = 0.0
    libre_mo: float = 0.0
    mesure: bool = False              # faux si le chemin n'existe pas encore

    @property
    def utilise_pourcent(self) -> float:
        if self.total_mo <= 0:
            return 0.0
        return 100.0 * (1.0 - self.libre_mo / self.total_mo)


def mesurer(chemin: str) -> Espace:
    """Espace du volume qui contient `chemin`, même si le dossier n'existe pas.

    On remonte l'arborescence jusqu'au premier répertoire existant : demander
    l'espace libre d'un dossier qu'on s'apprête à créer est le cas normal, pas
    une erreur.
    """
    candidat = os.path.abspath(chemin or ".")
    while candidat and not os.path.isdir(candidat):
        parent = os.path.dirname(candidat)
        if parent == candidat:
            break
        candidat = parent
    try:
        usage = shutil.disk_usage(candidat)
    except OSError:
        return Espace(chemin=chemin)
    return Espace(chemin=chemin, total_mo=usage.total / MO,
                  libre_mo=usage.free / MO, mesure=True)


def debit_mo_par_heure(settings) -> float:
    """Ce que la séance en cours écrira en une heure, d'après les réglages.

    Une estimation, pas une mesure : les CSV dépendent du nombre d'événements,
    qu'on ne peut pas connaître d'avance. Elle est volontairement un peu
    pessimiste — mieux vaut annoncer une autonomie plus courte que la vraie.
    """
    r = settings.recording
    fs = float(settings.acquisition.sample_rate or 250.0)
    voies = max(int(settings.acquisition.channels or 1), 1)
    octets = 0.0
    if r.write_wav:
        octets += 3.0 * fs * voies                     # WAV 24 bits
    if r.write_audio:
        octets += 2.0 * 44100.0                        # rendu musical, 16 bits
    if r.write_raw_csv:
        octets += 24.0 * fs * voies                    # une ligne par échantillon
    if r.write_csv:
        octets += 64.0 / 60.0                          # quelques lignes par minute
    return octets * 3600.0 / MO


def autonomie_heures(libre_mo: float, reserve_mo: float, debit: float) -> float:
    """Durée d'enregistrement restante avant d'atteindre la réserve."""
    if debit <= 0:
        return float("inf")
    return max(libre_mo - reserve_mo, 0.0) / debit


def formater_mo(mo: float) -> str:
    """« 512 Mo », « 3,2 Go », « 1,1 To » — avec la virgule française."""
    if mo >= 1024.0 * 1024.0:
        return f"{mo / 1024.0 / 1024.0:.1f} To".replace(".", ",")
    if mo >= 1024.0:
        return f"{mo / 1024.0:.1f} Go".replace(".", ",")
    return f"{mo:.0f} Mo"


def formater_duree(heures: float) -> str:
    """« 3 h 20 », « 45 min », « moins d'une minute »."""
    if heures == float("inf"):
        return "—"
    minutes = int(round(heures * 60.0))
    if minutes <= 0:
        return "< 1 min"
    if minutes < 60:
        return f"{minutes} min"
    return f"{minutes // 60} h {minutes % 60:02d}"
