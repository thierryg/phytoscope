#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/construire_source.py
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

"""Génère l'archive source (.tar.gz), valable sur tous les systèmes.

Le logiciel, ses essais et son outillage, tels qu'on les installe par
`make install`. C'est la forme qui vieillit le mieux : elle ne dépend d'aucun
format de paquet, d'aucune version de système, et reste lisible dans dix ans.

.. code-block:: console

    python3 packaging/construire_source.py

Ce script est autonome : il ne dépend que de `commun.py`, et se lance seul ou
par le Makefile du même dossier (`make source`).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commun import (  # noqa: E402
    GRIS, LOGICIEL, RACINE_SORTIE, VERT, Identite, appliquer_les_arguments,
    arguments_communs, bien, copier_le_logiciel, dire, dossier_sortie,
    ecrire_les_documents, ecrire_les_empreintes, lisible,
    JAUNE)


def construire_source(id_: Identite) -> Optional[str]:
    dire("\nArchive source (tous systèmes)\n", JAUNE)
    with tempfile.TemporaryDirectory(prefix="phyto-src-") as bac:
        nom = f"phytoscope-{id_.version}"
        racine = os.path.join(bac, nom)
        copier_le_logiciel(racine)
        for extra in ("Makefile", "make.bat", "tests", "tools",
                      "requirements-dev.txt"):
            source = os.path.join(LOGICIEL, extra)
            if os.path.isdir(source):
                shutil.copytree(source, os.path.join(racine, extra),
                                ignore=shutil.ignore_patterns(
                                    "__pycache__", "*.pyc", ".pytest_cache"))
            elif os.path.exists(source):
                shutil.copy2(source, os.path.join(racine, extra))
        cible = os.path.join(dossier_sortie(id_), f"{nom}.tar.gz")
        with tarfile.open(cible, "w:gz") as tar:
            tar.add(racine, arcname=nom)
    bien(f"{os.path.basename(cible)}  ({lisible(os.path.getsize(cible))})")
    return cible


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="construire_source.py",
        description="Fabrique l'archive source de PhytoScope.")
    arguments_communs(p)
    args = p.parse_args(argv)

    id_ = appliquer_les_arguments(args)
    dire(f"\n  PhytoScope {id_.version}-{id_.release} — archive source", VERT)
    produits = [x for x in [construire_source(id_)] if x]
    if produits:
        ecrire_les_empreintes(id_)
        ecrire_les_documents(id_)
    for f in produits:
        dire(f"    {os.path.relpath(f, RACINE_SORTIE)}", GRIS)
    return 0 if produits else 1


if __name__ == "__main__":
    sys.exit(main())
