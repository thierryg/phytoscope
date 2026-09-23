#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/impacted_pdfs.py
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

"""Dit quelles publications il faut refaire, au vu des fichiers modifiés.

Pourquoi cet outil existe
-------------------------

Refaire les dix publications prend une douzaine de minutes : la série pèse
84 Mo de PDF à elle seule. Corriger une coquille dans un fragment du
hors-série n'a aucune raison de reconstruire l'ouvrage de 478 pages.

L'outil prend une liste de chemins modifiés et rend les commandes à lancer.
Il est **volontairement prudent** : un chemin qu'il ne sait pas rattacher
déclenche tout. Se tromper en refaisant trop coûte des minutes ; se tromper
en refaisant trop peu publie un PDF périmé, et cela ne se voit pas.

Usage
-----

    python3 tools/impacted_pdfs.py <chemin> [<chemin>…]
    git diff --name-only HEAD~1 | python3 tools/impacted_pdfs.py -

    --commandes   (défaut) les commandes à lancer, une par ligne
    --cibles      les noms des cibles concernées
    --pdf         les fichiers PDF qui seront réécrits
"""
import os
import sys

#  Une cible = un script à lancer, et les PDF qu'il réécrit.
#  « prealables » sont les générateurs à relancer avant, dans l'ordre.
CIBLES = {
    "ouvrage": {
        "commande": "python3 pdf-src/build.py",
        "prealables": ["python3 pdf-src/assets/svg/gen.py"],
        "pdf": ["La-Musique-des-Plantes.pdf"],
    },
    "serie-v1": {
        "commande": "python3 pdf-src/build_tree.py v1",
        "prealables": ["python3 pdf-src/assets/svg/gen_tt.py"],
        "pdf": ["arbre-parlant-dublin-analyse-scientifique.pdf"],
    },
    "serie-v2": {
        "commande": "python3 pdf-src/build_tree.py v2",
        "prealables": ["python3 pdf-src/assets/svg/gen_tt.py"],
        "pdf": ["plant-biocommunication-and-ai.pdf"],
    },
    "serie-v3": {
        "commande": "python3 pdf-src/build_tree.py v3",
        "prealables": ["python3 pdf-src/assets/svg/gen_tt.py"],
        "pdf": ["workshop-build-a-talking-tree.pdf"],
    },
    "annexe": {
        "commande": "python3 pdf-src/build_appendix.py",
        "prealables": ["python3 pdf-src/assets/svg/gen_sch.py"],
        "pdf": ["arbre-parlant-annexe-schemas-bom-programmes.pdf"],
    },
    "carte": {
        "commande": "python3 pdf-src/build_board.py",
        "prealables": [
            "python3 pdf-src/assets/svg/gen_board.py",
            "python3 tools/gen_bom.py",
        ],
        "pdf": [
            "La-Carte-PhytoSense.pdf",
            "PhytoSense-schematics.pdf",
            "PhytoSense-bom-accessories.pdf",
            "PhytoSense-pcb.pdf",
        ],
    },
    "sdk": {
        "commande": "python3 pdf-src/build_sdk.py",
        "prealables": ["python3 pdf-src/assets/svg/gen_sdk.py"],
        "pdf": ["writing-a-phytoscope-module.pdf"],
    },
    #  Les documents de référence de `sources/` : un dossier, un HTML, un
    #  PDF, sans illustration à produire au préalable. Ils ne partagent ni
    #  charte ni fragment avec les publications, d'où des cibles à part.
    "reference-midi": {
        "commande": "python3 sources/build_references.py midi",
        "prealables": [],
        "pdf": ["MIDI-Protocol-Reference.pdf"],
    },
    "reference-usb": {
        "commande": "python3 sources/build_references.py usb",
        "prealables": [],
        "pdf": ["USB-Device-Reference.pdf"],
    },
}

TOUT = tuple(CIBLES)
SERIE = ("serie-v1", "serie-v2", "serie-v3")

#  Ce qui partage la charte : book.css sert à l'ouvrage, au hors-série et au
#  guide du SDK ; tree.css n'appartient qu'à la série.
CSS = {
    "pdf-src/book.css": ("ouvrage", "carte", "sdk", "annexe"),
    "pdf-src/board.css": ("carte", "sdk"),
    "pdf-src/tree.css": SERIE + ("annexe",),
    "pdf-src/fonts.css": TOUT,
}

#  Les illustrations sont rangées par préfixe ; c'est une convention du dépôt,
#  tenue par les cinq générateurs.
PREFIXES_SVG = {
    "tt-": SERIE,
    "carte-": ("carte",),
    "pcb-": ("carte",),
    "gabarit-": ("carte",),
    "sdk-": ("sdk",),
    "logiciel-": ("ouvrage",),
    "sch-": ("annexe",) + ("serie-v3",),
}

GENERATEURS = {
    "gen.py": ("ouvrage",) + SERIE,
    "gen_board.py": ("carte",),
    "gen_tt.py": SERIE,
    "gen_sch.py": ("annexe", "serie-v3"),
    "gen_sdk.py": ("sdk",),
}

#  Les outils qui écrivent des fragments : toucher au générateur revient à
#  toucher au fragment qu'il produit.
OUTILS = {
    "tools/gen_bom.py": ("carte",),
    "tools/gen_code_annex.py": ("ouvrage",),
    "tools/gen_glossary.py": ("ouvrage",) + SERIE,
    "tools/gen_index.py": ("ouvrage",) + SERIE,
    "tools/gen_credits.py": ("ouvrage",) + SERIE,
    "tools/gen-appendix-parts.py": ("annexe",),
}


def cibles_pour(chemin: str) -> tuple[str, ...]:
    """Rend les cibles qu'un chemin modifié rend périmées."""
    c = chemin.strip().replace(os.sep, "/").lstrip("./")
    if not c:
        return ()

    # --- les scripts de fabrication ---------------------------------------
    if c == "pdf-src/build.py":
        return ("ouvrage",)
    if c == "pdf-src/build_tree.py":
        return SERIE
    if c == "pdf-src/build_board.py":
        #  build_sdk.py emprunte le moule du hors-série : le modifier touche
        #  aussi le guide du SDK.
        return ("carte", "sdk")
    if c == "pdf-src/build_sdk.py":
        return ("sdk",)
    if c == "pdf-src/build_appendix.py":
        return ("annexe",)
    if c in OUTILS:
        return OUTILS[c]

    # --- la nomenclature alimente la BOM du hors-série ---------------------
    if c.startswith("hardware/"):
        return ("carte", "annexe")

    # --- les documents de référence de sources/ ---------------------------
    #  Avant les règles `sources/` plus larges, parce que ces deux dossiers
    #  ne nourrissent aucune publication : ils SONT leur propre publication.
    if c == "sources/build_references.py":
        return ("reference-midi", "reference-usb")
    if c.startswith("sources/midi/"):
        return ("reference-midi",)
    if c.startswith("sources/usb/"):
        return ("reference-usb",)

    # --- les listings de programmes de l'annexe de codes -------------------
    if c.startswith("sources/reverse/") or c.startswith("sources/schematics/"):
        return ("ouvrage",)

    # --- les chartes graphiques -------------------------------------------
    if c in CSS:
        return CSS[c]

    # --- les fragments : un dossier par publication -----------------------
    DOSSIERS = {
        "pdf-src/the-music-of-plants/": ("ouvrage",),
        "pdf-src/talking-tree-dublin/": ("serie-v1",),
        "pdf-src/plant-biocommunication-and-ai/": ("serie-v2",),
        "pdf-src/workshop-build-a-talking-tree/": ("serie-v3",),
        "pdf-src/talking-tree-appendix/": ("annexe",),
        "pdf-src/the-phytosense-board/": ("carte",),
        "pdf-src/phytosense-schematics/": ("carte",),
        "pdf-src/phytosense-bom-accessories/": ("carte",),
        "pdf-src/phytosense-pcb/": ("carte",),
        "pdf-src/writing-a-phytoscope-module/": ("sdk",),
        #  Les tableaux partagés servent au hors-série et à ses fascicules,
        #  et l'annexe technique reprend la même nomenclature.
        "pdf-src/common/": ("carte", "annexe"),
    }
    for prefixe, cibles in DOSSIERS.items():
        if c.startswith(prefixe):
            return cibles

    # --- les illustrations et leurs générateurs ---------------------------
    if c.startswith("pdf-src/assets/svg/"):
        nom = c.rsplit("/", 1)[-1]
        if nom in GENERATEURS:
            return GENERATEURS[nom]
        for prefixe, cibles in PREFIXES_SVG.items():
            if nom.startswith(prefixe):
                return cibles
        #  Une illustration sans préfixe est partagée par l'ouvrage et la
        #  série (c'est gen.py qui les produit).
        return ("ouvrage",) + SERIE

    # --- polices et photographies : partagées ------------------------------
    if c.startswith("pdf-src/assets/"):
        return TOUT

    # --- les assemblages intermédiaires sont des produits ------------------
    if c.startswith("pdf-src/_") or c.startswith("build/"):
        return ()

    # --- tout le reste de pdf-src/ : on ne sait pas, donc on refait tout ---
    if c.startswith("pdf-src/"):
        return TOUT

    return ()


def main(argv: list[str]) -> int:
    sortie = "commandes"
    for opt in ("--commandes", "--cibles", "--pdf"):
        if opt in argv:
            sortie = opt[2:]
            argv = [a for a in argv if a != opt]

    chemins = argv[1:]
    if chemins == ["-"] or not chemins:
        chemins = sys.stdin.read().split("\n")

    retenues: set[str] = set()
    for chemin in chemins:
        retenues.update(cibles_pour(chemin))

    #  L'ordre du dictionnaire est l'ordre de fabrication : le plus lourd
    #  d'abord, pour qu'une panne se voie tôt.
    ordonnees = [c for c in CIBLES if c in retenues]

    if not ordonnees:
        #  Rien à refaire : on le dit sur la sortie d'erreur, pour que la
        #  sortie standard reste vide et directement consommable par un shell.
        print("  · aucune publication touchée", file=sys.stderr)
        return 0

    if sortie == "cibles":
        print("\n".join(ordonnees))
    elif sortie == "pdf":
        for c in ordonnees:
            for f in CIBLES[c]["pdf"]:
                print(f"build/{f}")
    else:
        prealables: list[str] = []
        for c in ordonnees:
            for p in CIBLES[c]["prealables"]:
                if p not in prealables:
                    prealables.append(p)
        for p in prealables:
            print(p)
        for c in ordonnees:
            print(CIBLES[c]["commande"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
