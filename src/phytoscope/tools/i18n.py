#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/i18n.py
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

"""Outil des traductions : extraire les libellés, créer et vérifier un catalogue.

    python3 tools/i18n.py --cles                 la liste des libellés traduisibles
    python3 tools/i18n.py --modele it            crée ou complète langues/it.json
    python3 tools/i18n.py --modeles              complète toutes les langues livrées
    python3 tools/i18n.py --couverture           l'état de chaque traduction
    python3 tools/i18n.py --inutiles it          les clés du catalogue qui n'existent plus

Deux sources de libellés, parce que l'interface en a deux :

* les appels ``t("…")`` dans le code, trouvés par analyse syntaxique — jamais
  par expression régulière, qui se tromperait sur les chaînes à cheval sur
  plusieurs lignes ;
* les **tables de données** — noms d'instruments, de gammes, de profils, de
  descripteurs, de grammaires, textes de l'aide — dont le contenu est traduit au
  moment de l'affichage. Elles sont importées puis parcourues, ce qui évite de
  les décrire deux fois.

Ajouter une langue : ``--modele <code>``, traduire le fichier produit, et c'est
tout. Le logiciel découvre les catalogues présents à chaque démarrage.
"""
from __future__ import annotations

import ast
import json
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

from phytoscope import i18n                                    # noqa: E402

SOURCES = ("phytoscope/ui", "phytoscope/core", "phytoscope/music", "phytoscope")


# ---------------------------------------------------------------------------
#  L'inventaire vit dans phytoscope/i18n.py : l'outil et le bouton « Écrire un
#  modèle » des réglages voient ainsi exactement la même liste.
# ---------------------------------------------------------------------------
def toutes_les_cles() -> list:
    return i18n.collecter_cles()


# ---------------------------------------------------------------------------
#  3. Commandes
# ---------------------------------------------------------------------------
def main(argv) -> int:
    cles = toutes_les_cles()

    if "--cles" in argv:
        for c in cles:
            print(c)
        print(f"\n{len(cles)} libellés traduisibles", file=sys.stderr)
        return 0

    if "--couverture" in argv:
        print(f"{len(cles)} libellés traduisibles\n")
        print(f"  {'code':<6} {'langue':<22} {'traduits':>9}  couverture")
        print("  " + "─" * 56)
        for code, nom, nom_fr, n, sens in i18n.langues_disponibles():
            if code == i18n.LANGUE_SOURCE:
                print(f"  {code:<6} {nom:<22} {'—':>9}  langue source")
                continue
            table = i18n.catalogue(code)
            faits = sum(1 for c in cles if table.get(c))
            part = 100.0 * faits / max(len(cles), 1)
            drapeau = "  ← à compléter" if part < 99.0 else ""
            print(f"  {code:<6} {nom:<22} {faits:>9}  {part:5.1f} %{drapeau}")
        return 0

    if "--inutiles" in argv:
        code = argv[argv.index("--inutiles") + 1]
        connues = set(cles)
        for c in sorted(i18n.catalogue(code)):
            if c not in connues:
                print(c)
        return 0

    if "--modele" in argv or "--modeles" in argv:
        if "--modeles" in argv:
            codes = [c for c, _, _, _ in i18n.LIVREES if c != i18n.LANGUE_SOURCE]
        else:
            codes = [argv[argv.index("--modele") + 1]]
        for code in codes:
            chemin = i18n.chemin_catalogue(code)
            neuves = i18n.ecrire_modele(chemin, cles, code)
            print(f"  · {code}.json — {len(cles)} clés, {neuves} à traduire")
        return 0

    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
