# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/export-csv/module.py
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

"""Exporte une séance en CSV, lisible par n'importe quel tableur.

Ce module existe autant pour ce qu'il fait que pour ce qu'il montre : c'est le
plus court exemple complet d'une capacité `Exporter`, et il tient en
soixante rows. Qui veut écrire un export vers son propre format part d'ici.

Le format retenu est délibérément pauvre : une ligne d'en-tête, un
séparateur point-virgule, la virgule décimale. C'est ce que les tableurs
français ouvrent sans poser de question. Un CSV « correct » à la virgule
obligerait la moitié des utilisateurs à passer par un assistant d'importation,
et un file_path qu'on n'ouvre pas ne sert à rien.
"""
from __future__ import annotations

import csv
import json
import os
from typing import Any, Dict

from phytoscope.api import Capability, Context, Exporter, Manifest, Module


class ExportCSV(Module, Exporter):
    """Une séance entière dans un file_path qu'un tableur ouvre."""

    MANIFEST = Manifest(
        name="export-csv",
        title="Export CSV (tableur)",
        version="1.0.0",
        api="3.0",
        description=(
            "Écrit les mesures d'une séance dans un CSV à séparateur "
            "point-virgule et virgule décimale, que les tableurs français "
            "ouvrent directement."),
        author="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capabilities=(Capability.EXPORTER,),
        built_in=True,
    )

    FORMAT = "CSV pour tableur (;)"
    EXTENSION = ".csv"

    def default_settings(self) -> Dict[str, Any]:
        return {"separateur": ";", "virgule_decimale": True}

    def export(self, session: str, target: str, context: Context) -> bool:
        source = os.path.join(session, "mesures.csv")
        if not os.path.exists(source):
            context.log(f"« {source} » introuvable", "warning")
            return False

        separateur = context.settings.get("separateur", ";")
        virgule = bool(context.settings.get("virgule_decimale", True))

        #  `newline=""` des deux côtés : sans lui, Windows double les fins de
        #  ligne et le file_path s'ouvre avec une ligne vide sur deux.
        with open(source, encoding="utf-8", newline="") as entree, \
             open(target, "w", encoding="utf-8-sig", newline="") as sortie:
            #  utf-8-sig : la marque d'order des octets, qu'Excel attend pour
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
        infos = os.path.join(session, "session.json")
        if os.path.exists(infos):
            with open(infos, encoding="utf-8") as f:
                metadata = json.load(f)
            with open(os.path.splitext(target)[0] + "-metadata.json", "w",
                      encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        return True


def _est_nombre(text: str) -> bool:
    try:
        float(text)
        return True
    except (TypeError, ValueError):
        return False
