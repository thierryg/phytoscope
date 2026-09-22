#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/build_fedora.py
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

"""Génère le paquet RPM — Fedora, Red Hat, Rocky, AlmaLinux, CentOS.

Même disposition que le paquet Debian, et pour les mêmes raisons : un
environnement Python privé plutôt qu'une dépendance sur `python3-pyside6`, que
les dépôts de Red Hat ne fournissent pas tous.

Le paquet est construit par `rpmbuild`, que Debian empaquette sous le nom
`rpm` : aucune machine Fedora n'est nécessaire.

.. code-block:: console

    python3 packaging/build_fedora.py [--hors-ligne]

Ce script est autonome : il ne dépend que de `common.py`, et se lance seul ou
par le Makefile du même dossier (`make fedora`).
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

from common import (  # noqa: E402
    GABARITS, GRIS, LOGICIEL, PYTHONS_COUVERTS, RACINE_SORTIE, VERT, Identite,
    appliquer_les_arguments, arguments_communs, bien, copier_le_logiciel,
    dire, dossier_sortie, ecrire, ecrire_les_documents, ecrire_les_empreintes,
    etape, executer, echec, icone_svg, lisible, remplir, telecharger_les_roues,
    JAUNE)


def construire_rpm(id_: Identite, embarquer: bool) -> Optional[str]:
    dire("\nPaquet Red Hat (.rpm) — Fedora, RHEL, Rocky, AlmaLinux\n", JAUNE)
    if not shutil.which("rpmbuild"):
        echec("rpmbuild absent : sudo apt install rpm")
        return None

    with tempfile.TemporaryDirectory(prefix="phyto-rpm-") as bac:
        arbre = {n: os.path.join(bac, n) for n in
                 ("BUILD", "RPMS", "SOURCES", "SPECS", "SRPMS")}
        for d in arbre.values():
            os.makedirs(d, exist_ok=True)

        nom = f"phytoscope-{id_.version}"
        marque = "-horsligne" if embarquer else ""
        racine = os.path.join(bac, nom)
        partage = os.path.join(racine, "usr", "share", "phytoscope")
        etape("copie du logiciel")
        copier_le_logiciel(partage)
        if embarquer:
            etape("roues Linux (installation hors ligne)")
            telecharger_les_roues("linux", os.path.join(partage, "roues"),
                                  PYTHONS_COUVERTS)
        ecrire(os.path.join(racine, "usr", "bin", "phytoscope"),
               open(os.path.join(GABARITS, "debian", "lanceur"),
                    encoding="utf-8").read(), executable=True)
        #  Deux outils que l'utilisateur appelle quand IL le décide : `apt` et
        #  `dnf` installent sans interaction, souvent sans session graphique.
        #  Poser la question de l'icône à ce moment-là serait la poser à la
        #  mauvaise personne.
        for outil, cible in (("icone-bureau.sh", "phytoscope-icone-bureau"),
                             ("desinstaller.sh", "phytoscope-desinstaller")):
            ecrire(os.path.join(racine, "usr", "bin", cible),
                   open(os.path.join(GABARITS, "debian", outil),
                        encoding="utf-8").read(), executable=True)
        os.makedirs(os.path.join(racine, "usr", "share", "applications"),
                    exist_ok=True)
        shutil.copy2(os.path.join(GABARITS, "debian", "phytoscope.desktop"),
                     os.path.join(racine, "usr", "share", "applications",
                                  "phytoscope.desktop"))
        ecrire(os.path.join(racine, "usr", "share", "icons", "hicolor",
                            "scalable", "apps", "phytoscope.svg"), icone_svg())

        etape("archive source")
        archive = os.path.join(arbre["SOURCES"], f"{nom}.tar.gz")
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(racine, arcname=nom)

        valeurs = dict(id_.jetons(),
                       DATE_RPM=time.strftime("%a %b %d %Y"))
        spec = os.path.join(arbre["SPECS"], "phytoscope.spec")
        ecrire(spec, remplir(os.path.join(GABARITS, "fedora",
                                          "phytoscope.spec"), valeurs))

        etape("assemblage")
        if not executer(["rpmbuild", "--define", f"_topdir {bac}",
                         "-bb", spec]):
            return None

        produits = []
        for dossier, _, fichiers in os.walk(arbre["RPMS"]):
            for f in fichiers:
                if f.endswith(".rpm"):
                    cible = os.path.join(
                        dossier_sortie(id_, "Linux"),
                        f.replace(".rpm", f"{marque}.rpm") if marque else f)
                    shutil.copy2(os.path.join(dossier, f), cible)
                    produits.append(cible)
    for p in produits:
        bien(f"{os.path.basename(p)}  ({lisible(os.path.getsize(p))})")
    return produits[0] if produits else None


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="build_fedora.py",
        description="Fabrique le paquet RPM de PhytoScope.")
    arguments_communs(p)
    p.add_argument("--hors-ligne", action="store_true",
                   help="embarquer les bibliothèques (Python 3.9 à 3.13) pour "
                        "une installation sans connexion")
    args = p.parse_args(argv)

    id_ = appliquer_les_arguments(args)
    dire(f"\n  PhytoScope {id_.version}-{id_.release} — Fedora, Red Hat, Rocky, AlmaLinux", VERT)
    produits = [x for x in [construire_rpm(id_, args.hors_ligne)] if x]
    if produits:
        ecrire_les_empreintes(id_)
        ecrire_les_documents(id_)
    for f in produits:
        dire(f"    {os.path.relpath(f, RACINE_SORTIE)}", GRIS)
    return 0 if produits else 1


if __name__ == "__main__":
    sys.exit(main())
