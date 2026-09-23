#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/verify_svg.py
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

"""Contrôle qu'un fichier SVG est du XML bien formé.

Pourquoi un outil pour si peu : une illustration mal formée ne casse pas la
fabrication. WeasyPrint la laisse tomber et compose un cadre vide, le PDF
sort avec le bon nombre de pages, et personne ne s'en aperçoit avant de
tourner la page à l'impression. Le défaut a existé — `timeline.svg` portait
un « & » nu, parce que le générateur n'échappait pas le texte qu'on lui
donnait (voir le journal du 2026-09-18). Le générateur a été corrigé ; ce
contrôle est là pour que la prochaine fois se voie tout de suite.

Usage :
    python3 tools/verify_svg.py [fichier.svg ...]

Sans argument, contrôle toutes les illustrations de `pdf-src/assets/svg/`.
Sort en 1 dès qu'un fichier est mal formé, et dit lequel et où.
"""
import glob
import sys
import xml.parsers.expat


def controler(chemin: str) -> str | None:
    """Rend None si le fichier est bien formé, sinon la raison."""
    analyseur = xml.parsers.expat.ParserCreate()
    try:
        with open(chemin, "rb") as f:
            analyseur.ParseFile(f)
    except xml.parsers.expat.ExpatError as e:
        return f"ligne {e.lineno}, colonne {e.offset} : {xml.parsers.expat.ErrorString(e.code)}"
    except OSError as e:
        return f"illisible : {e}"
    return None


def main(argv: list[str]) -> int:
    fichiers = argv[1:] or sorted(glob.glob("pdf-src/assets/svg/*.svg"))
    if not fichiers:
        print("  aucune illustration à contrôler")
        return 0

    mauvais = [(f, r) for f in fichiers if (r := controler(f))]

    print(f"  · {len(fichiers)} illustration(s) contrôlée(s)")
    for chemin, raison in mauvais:
        print(f"  ! {chemin} — {raison}")
    if mauvais:
        print("\n  Ces fichiers sont produits par un générateur : corrigez le")
        print("  générateur, puis relancez-le (C-45 — on n'édite pas un")
        print("  fichier généré).")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
