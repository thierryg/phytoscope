#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/check_syntax.py
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

"""Vérifie que tous les fichiers du logiciel sont syntaxiquement corrects.

Utile avant de distribuer une archive : cela ne demande aucune dépendance,
donc cela fonctionne même sur une machine où rien n'est installé.
"""
import ast
import glob
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    files = sorted(glob.glob(os.path.join(ROOT, "phytoscope", "**", "*.py"),
                             recursive=True))
    files += [os.path.join(ROOT, "run.py")]
    files += sorted(glob.glob(os.path.join(ROOT, "tests", "*.py")))
    bad = 0
    for f in files:
        if not os.path.exists(f):
            continue
        try:
            ast.parse(open(f, encoding="utf-8").read(), filename=f)
        except SyntaxError as exc:
            print(f"ERREUR  {os.path.relpath(f, ROOT)}:{exc.lineno}  {exc.msg}")
            bad += 1
    print(f"✗ {bad} fichier(s) en erreur" if bad
          else f"✓ syntaxe correcte — {len(files)} fichiers")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
