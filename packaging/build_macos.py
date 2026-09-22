#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/build_macos.py
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

"""Génère les paquets macOS : l'archive du paquet .app, et l'installateur .pkg.

Deux formes, deux habitudes :

``PhytoScope-X.Y.Z-macOS.zip``
    Contient ``PhytoScope.app``, qu'on glisse dans Applications. C'est la
    manière la plus répandue sur macOS, et la plus facile à défaire : on jette
    l'icône à la corbeille.

``PhytoScope-X.Y.Z.pkg``
    L'installateur d'Apple : double-clic, un assistant, l'application posée
    dans ``/Applications`` pour tous les comptes. C'est ce qu'attend un parc de
    machines, et ce qui s'installe sans interface par
    ``installer -pkg … -target /``.

Le ``.pkg`` est écrit intégralement par `macos_pkg.py` : ni `pkgbuild` — qui
n'existe que sur macOS — ni `xar` et `mkbom`, que Debian n'empaquette plus.
Voir ce module pour l'anatomie du format.

**Une seule cible pour les deux architectures.** Qt n'est publié pour macOS
qu'en « universal2 », c'est-à-dire en binaire double contenant Intel et Apple
Silicon : produire un paquet par architecture donnerait deux archives dont
l'essentiel serait identique.

.. code-block:: console

    python3 packaging/build_macos.py                # zip + pkg
    python3 packaging/build_macos.py --pkg          # seulement le .pkg
    python3 packaging/build_macos.py --hors-ligne   # avec les bibliothèques

Ce script est autonome : il ne dépend que de `common.py` et de `macos_pkg.py`,
et se lance seul ou par le Makefile du même dossier (`make macos`).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import macos_pkg  # noqa: E402
import platform  # noqa: E402

from common import (  # noqa: E402
    GABARITS, GRIS, LOGICIEL, PYTHONS_MACOS, RACINE_SORTIE, VERT, Identite,
    appliquer_les_arguments, arguments_communs, bien, copier_le_logiciel,
    dire, dossier_sortie, echec, ecrire, ecrire_les_documents,
    ecrire_les_empreintes, etape, fabriquer_icone, icone_svg, lisible,
    remplir, souci, telecharger_les_roues, _zipper,
    JAUNE, PYTHON_AUTONOME, _python_autonome, cible_pbs)

IDENTIFIANT = "com.bretagne-namaste.phytoscope"


def construire_macos(id_: Identite, embarquer: bool = False,
                     faire_zip: bool = True,
                     faire_pkg: bool = True,
                     arch_python: str = "") -> List[str]:
    """Un paquet .app unique, pour Intel et Apple Silicon.

    Un seul paquet, et non deux : Qt n'est publié pour macOS qu'en
    « universal2 », c'est-à-dire en binaire double contenant les deux
    architectures. Produire un paquet par architecture donnait deux archives
    de 450 Mo dont 400 Mo identiques — pour un gain nul, puisque le fichier
    lourd était de toute façon le même.
    """
    dire("\nmacOS — paquet .app (Intel et Apple Silicon)\n", JAUNE)
    with tempfile.TemporaryDirectory(prefix="phyto-mac-") as bac:
        app = os.path.join(bac, "PhytoScope.app")
        macos = os.path.join(app, "Contents", "MacOS")
        ressources = os.path.join(app, "Contents", "Resources")
        os.makedirs(macos, exist_ok=True)
        os.makedirs(ressources, exist_ok=True)

        etape("logiciel")
        copier_le_logiciel(os.path.join(ressources, "app"))

        #  L'interpréteur voyage avec l'application. Sans lui, le lanceur ne
        #  pouvait que s'arrêter en disant « brew install python » : une
        #  application qui exige d'abord un gestionnaire de paquets tiers
        #  n'est pas « prête après l'installation ». Et Homebrew est
        #  précisément ce qu'il faut éviter — son interpréteur ne voit pas les
        #  bibliothèques du système.
        #
        #  Ce sont des binaires RELOGEABLES : ils fonctionnent depuis le
        #  paquet, sans être installés et sans privilèges (C-55).
        #
        #  Une réserve, dite franchement : python-build-standalone ne publie
        #  pas d'« universal2 ». On livre donc l'architecture demandée — celle
        #  de la machine qui fabrique par défaut. Un paquet fabriqué sur Intel
        #  n'apportera pas d'interpréteur utilisable sur Apple Silicon, et le
        #  lanceur retombera alors sur python.org ou sur celui d'Apple.
        arch = arch_python or platform.machine().lower()
        etape(f"Python autonome {PYTHON_AUTONOME} ({cible_pbs('macos', arch) or arch})")
        if not _python_autonome(os.path.join(ressources, "python"), "macos", arch):
            souci("l'application exigera un Python déjà présent")

        if embarquer:
            #  Qt pèse à lui seul 450 Mo en « universal2 ». Un paquet de
            #  500 Mo se justifie pour un atelier sans réseau ; il se justifie
            #  mal pour un téléchargement ordinaire, où la première ouverture
            #  peut très bien aller chercher les bibliothèques.
            etape("bibliothèques macOS (Intel et Apple Silicon)")
            if not telecharger_les_roues("macos",
                                         os.path.join(ressources, "roues"),
                                         PYTHONS_MACOS):
                souci("bibliothèques incomplètes — paquet abandonné")
                return []

        ecrire(os.path.join(app, "Contents", "Info.plist"),
               remplir(os.path.join(GABARITS, "macos", "Info.plist"),
                       id_.jetons()))
        ecrire(os.path.join(macos, "phytoscope"),
               open(os.path.join(GABARITS, "macos", "lanceur"),
                    encoding="utf-8").read(), executable=True)
        ecrire(os.path.join(ressources, "phytoscope.svg"), icone_svg())
        #  L'icône que `Info.plist` annonce. Sans elle, le Finder affiche
        #  l'icône générique d'une application inconnue.
        if not fabriquer_icone(os.path.join(ressources, "phytoscope.icns"),
                               "icns"):
            souci("icône .icns non fabriquée (PySide6 introuvable)")
        #  PkgInfo : quatre octets hérités du Système 7, que le Finder lit
        #  encore pour reconnaître un paquet applicatif.
        ecrire(os.path.join(app, "Contents", "PkgInfo"), "APPL????")

        ecrire(os.path.join(bac, "LISEZ-MOI.txt"), _lisez_moi_macos(id_))
        shutil.copy2(os.path.join(LOGICIEL, "LICENCE.txt"),
                     os.path.join(bac, "LICENCE.txt"))

        marque = "-horsligne" if embarquer else ""
        produits: List[str] = []

        if faire_zip:
            etape("archive du paquet .app")
            cible = os.path.join(
                dossier_sortie(id_, "MacOSX"), f"PhytoScope-{id_.version}-macOS{marque}.zip")
            _zipper(bac, cible)
            bien(f"{os.path.basename(cible)}  "
                 f"({lisible(os.path.getsize(cible))})")
            produits.append(cible)

        if faire_pkg:
            etape("installateur .pkg")
            produits += _construire_pkg(id_, bac, app, marque)
    return produits


def _construire_pkg(id_: Identite, bac: str, app: str,
                    marque: str) -> List[str]:
    """Écrit l'installateur, puis le relit pour vérifier ce qu'on a écrit.

    On ne peut pas soumettre le paquet à `installer(8)` sans Mac ; on peut en
    revanche contrôler que les trois formats qui le composent — XAR, cpio et
    BOM — se relisent et décrivent **le même ensemble de fichiers**. Une
    charge utile et une nomenclature qui divergent sont la panne classique du
    paquet fabriqué à la main : l'installateur copie, puis refuse.
    """
    #  Le .pkg ne doit contenir que le paquet .app : le LISEZ-MOI et la
    #  licence sont affichés par l'assistant, pas déposés dans Applications.
    charge = os.path.join(bac, "_charge_pkg")
    os.makedirs(charge, exist_ok=True)
    shutil.copytree(app, os.path.join(charge, "PhytoScope.app"),
                    symlinks=True)

    licence = ""
    chemin_licence = os.path.join(LOGICIEL, "LICENCE.txt")
    if os.path.exists(chemin_licence):
        licence = open(chemin_licence, encoding="utf-8").read()

    cible = os.path.join(dossier_sortie(id_, "MacOSX"), f"PhytoScope-{id_.version}{marque}.pkg")
    try:
        #  Le script d'apres-installation pose les deux questions — icône sur
        #  le Bureau, lancement immédiat — et dépose le désinstallateur.
        with open(os.path.join(GABARITS, "macos", "postinstall"),
                  encoding="utf-8") as f:
            apres = f.read()
        macos_pkg.ecrire_pkg(
            charge, cible, IDENTIFIANT, id_.version, "PhytoScope",
            destination="/Applications", licence=licence,
            bienvenue=_bienvenue(id_), postinstall=apres)
        rapport = macos_pkg.verifier_pkg(
            cible, attendus=["./PhytoScope.app/Contents/MacOS/phytoscope",
                             "./PhytoScope.app/Contents/Info.plist"])
    except (OSError, ValueError) as exc:
        echec(f"paquet .pkg : {exc}")
        return []

    bien(f"{os.path.basename(cible)}  ({lisible(os.path.getsize(cible))})")
    dire(f"      {rapport['fichiers']} fichiers, charge et nomenclature "
         f"concordantes, version {rapport['version']}", GRIS)
    souci("le .pkg n'a pas été soumis à l'installateur de macOS — "
          "il n'y a pas de Mac ici")
    return [cible]


def _bienvenue(id_: Identite) -> str:
    return f"""PhytoScope {id_.version}

Ce paquet installe PhytoScope dans le dossier Applications.

PhytoScope a besoin de Python 3.9 ou plus récent. S'il manque, l'application
vous le dira à la première ouverture ; le plus simple est alors :

    brew install python

À la première ouverture, PhytoScope prépare son environnement Python — une à
deux minutes, une seule fois. macOS demandera ensuite l'autorisation
d'accéder au microphone : c'est par l'entrée audio que le signal de la plante
arrive.

Cette application n'est pas signée par un compte développeur Apple. Si macOS
refuse de l'ouvrir, faites un clic droit sur son icône puis « Ouvrir ».

{id_.auteur} — {id_.site} — licence MIT
Aucune télémétrie, aucun compte, aucun réseau."""


def _lisez_moi_macos(id_: Identite) -> str:
    return f"""PhytoScope {id_.version} — installation sur macOS
==================================================

1. Glissez PhytoScope.app dans votre dossier Applications.

2. À la PREMIÈRE ouverture, faites un clic droit sur l'icône et choisissez
   « Ouvrir », puis confirmez.

   Pourquoi ce détour : l'application n'est pas signée par un compte
   développeur Apple. macOS refuse par défaut d'ouvrir une application non
   signée téléchargée sur le web, et le double-clic ne donne alors aucune
   explication utile. Le clic droit « Ouvrir » est la manière prévue par Apple
   de passer outre en connaissance de cause. Une seule fois suffit.

   Si macOS bloque malgré tout :
       xattr -dr com.apple.quarantine /Applications/PhytoScope.app

3. PhytoScope a besoin de Python 3.9 ou plus récent. Le plus simple :
       brew install python
   Sinon, téléchargez-le sur python.org. L'application vous le dira si
   nécessaire.

4. À la première ouverture, PhytoScope prépare son environnement Python
   (une à deux minutes, une seule fois). Les bibliothèques sont déjà dans le
   paquet : aucune connexion n'est nécessaire.

5. macOS demandera l'autorisation d'accéder au microphone. C'est par l'entrée
   audio que le signal de la plante arrive — carte PhytoSense, carte son ou
   montage série. Sans cette autorisation, la mesure reste muette.

Vos réglages :   ~/Library/Application Support/PhytoScope
Vos séances :    ~/Documents/PhytoScope

{id_.auteur} — {id_.site}
Licence MIT. Aucune télémétrie, aucun compte, aucun réseau.
"""


def _tout(args) -> bool:
    """Aucune option de cible : on les fait toutes."""
    cibles = [v for c, v in vars(args).items()
              if c in ("zip", "exe", "msi", "pkg")]
    return not any(cibles)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="build_macos.py",
        description="Fabrique les paquets macOS de PhytoScope.")
    arguments_communs(p)
    p.add_argument("--zip", action="store_true",
                   help="seulement l'archive du paquet .app")
    p.add_argument("--pkg", action="store_true",
                   help="seulement l'installateur .pkg")
    p.add_argument("--arch", default="", metavar="ARCH",
                   choices=["", "x86_64", "arm64"],
                   help="architecture de l'interpréteur embarqué "
                        "(x86_64 ou arm64 ; par défaut celle de cette machine)")
    p.add_argument("--hors-ligne", action="store_true",
                   help="embarquer les bibliothèques (Qt pèse 450 Mo en "
                        "« universal2 ») pour une installation sans connexion")
    args = p.parse_args(argv)

    id_ = appliquer_les_arguments(args)
    dire(f"\n  PhytoScope {id_.version}-{id_.release} — macOS (Intel et Apple Silicon)", VERT)
    produits = [x for x in construire_macos(id_, args.hors_ligne,
                            faire_zip=_tout(args) or args.zip,
                            faire_pkg=_tout(args) or args.pkg,
                            arch_python=args.arch) if x]
    if produits:
        ecrire_les_empreintes(id_)
        ecrire_les_documents(id_)
    for f in produits:
        dire(f"    {os.path.relpath(f, RACINE_SORTIE)}", GRIS)
    return 0 if produits else 1


if __name__ == "__main__":
    sys.exit(main())
