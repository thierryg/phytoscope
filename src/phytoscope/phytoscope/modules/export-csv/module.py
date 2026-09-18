# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/export-csv/module.py
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

"""Exporte une séance en CSV, lisible par n'importe quel tableur.

Ce module existe autant pour ce qu'il fait que pour ce qu'il montre : c'est le
plus court exemple complet d'une capacité `Exportateur`, et il tient en
soixante lignes. Qui veut écrire un export vers son propre format part d'ici.

Le format retenu est délibérément pauvre : une ligne d'en-tête, un
séparateur point-virgule, la virgule décimale. C'est ce que les tableurs
français ouvrent sans poser de question. Un CSV « correct » à la virgule
obligerait la moitié des utilisateurs à passer par un assistant d'importation,
et un fichier qu'on n'ouvre pas ne sert à rien.
"""
from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict

from phytoscope.api import Capacite, Contexte, Exportateur, Manifeste, Module


class ExportCSV(Module, Exportateur):
    """Une séance entière dans un fichier qu'un tableur ouvre."""

    MANIFESTE = Manifeste(
        nom="export-csv",
        titre="Export CSV (tableur)",
        version="1.0.0",
        api="1.0",
        description=(
            "Écrit les mesures d'une séance dans un CSV à séparateur "
            "point-virgule et virgule décimale, que les tableurs français "
            "ouvrent directement."),
        auteur="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capacites=(Capacite.EXPORTATEUR,),
        integre=True,
    )

    FORMAT = "CSV pour tableur (;)"
    EXTENSION = ".csv"

    def reglages_par_defaut(self) -> Dict[str, Any]:
        return {"separateur": ";", "virgule_decimale": True}

    def exporter(self, seance: str, cible: str, contexte: Contexte) -> bool:
        source = os.path.join(seance, "mesures.csv")
        if not os.path.exists(source):
            contexte.journal(f"« {source} » introuvable", "warning")
            return False

        separateur = contexte.reglages.get("separateur", ";")
        virgule = bool(contexte.reglages.get("virgule_decimale", True))

        #  `newline=""` des deux côtés : sans lui, Windows double les fins de
        #  ligne et le fichier s'ouvre avec une ligne vide sur deux.
        with open(source, encoding="utf-8", newline="") as entree, \
             open(cible, "w", encoding="utf-8-sig", newline="") as sortie:
            #  utf-8-sig : la marque d'ordre des octets, qu'Excel attend pour
            #  reconnaître l'UTF-8. Sans elle, les accents sont abîmés.
            lecteur = csv.reader(entree)
            ecrivain = csv.writer(sortie, delimiter=separateur)
            for rang, ligne in enumerate(lecteur):
                if rang and virgule:
                    ligne = [c.replace(".", ",") if _est_nombre(c) else c
                             for c in ligne]
                ecrivain.writerow(ligne)

        #  Les métadonnées à côté : la pleine échelle, la plante, la cadence.
        #  Un CSV sans son échelle est joli mais inexploitable (`C-11`).
        infos = os.path.join(seance, "seance.json")
        if os.path.exists(infos):
            with open(infos, encoding="utf-8") as f:
                metadonnees = json.load(f)
            with open(os.path.splitext(cible)[0] + "-metadonnees.json", "w",
                      encoding="utf-8") as f:
                json.dump(metadonnees, f, ensure_ascii=False, indent=2)
        return True


def _est_nombre(texte: str) -> bool:
    try:
        float(texte)
        return True
    except (TypeError, ValueError):
        return False
