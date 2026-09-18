#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/build_sdk.py
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

"""Build du hors-série développeur « Écrire un module pour PhytoScope ».

    build/Ecrire-un-module-PhytoScope.pdf

Le document décrit l'interface de programmation des modules, le SDK, et ce
qu'un module a le droit de faire. Il est fabriqué à partir des fragments de
`pdf-src/parts-sdk/`, par le même moule que les deux autres ouvrages — mêmes
feuilles de style, même sommaire cliquable, mêmes métadonnées.

Le contenu est le même que celui de `src/sdk/docs/`, mis en page pour l'impression.
Deux formes, une source de vérité : le Markdown se lit dans le dépôt, le PDF
s'imprime et s'emporte.

Usage :
    python3 build_sdk.py
"""
import os
import sys

RACINE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RACINE)

#  On emprunte le moule du hors-série : lecture des fragments, numérotation
#  des figures, sommaire, contrôles. Le recopier aurait garanti qu'il dérive.
import build_carte as moule

moule.PARTS = os.path.join(moule.SRC, "ecrire-un-module-phytoscope")

ORDRE = [
    "00-cover",
    "01-titlepage",
    "02-notice",
    "03-toc",
    "04-premier-module",
    "05-anatomie",
    "06-capacites",
    "07-evenements",
    "08-pieges",
    "09-fin",
]

DOCUMENT = {
    "out": "Ecrire-un-module-PhytoScope.pdf",
    "title": "Écrire un module pour PhytoScope",
    "running": "Écrire un module pour PhytoScope",
    "description": (
        "L'interface de programmation des modules de PhytoScope, le SDK, et "
        "ce qu'un module a le droit de faire : les cinq capacités, les "
        "événements, les essais sans matériel, et les pièges."),
    "keywords": ("PhytoScope, module, greffon, SDK, API, Python, "
                 "extension, plugin, biosignal, plante"),
    "order": ORDRE,
}


def main(argv):
    #  `build` de build_carte lit ses fragments dans `moule.PARTS`, que l'on
    #  vient de rediriger : il produit donc notre document sans modification.
    return 0 if moule.build("sdk", DOCUMENT) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
