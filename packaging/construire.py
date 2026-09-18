#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/construire.py
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

"""Fabrique les paquets d'installation de PhytoScope, depuis Debian/Ubuntu/Mint.

Ce script est un **aiguillage** : il appelle, dans le bon ordre, les
générateurs qui font le travail. Chaque système a le sien, autonome et
lançable seul :

==========================  ===========================================
`construire_debian.py`      `.deb` — Debian, Ubuntu, Mint
`construire_fedora.py`      `.rpm` — Fedora, Red Hat, Rocky, AlmaLinux
`construire_windows.py`     `.zip` portable, `.exe` (NSIS), `.msi` (wixl)
`construire_macos.py`       `.zip` du paquet `.app`, `.pkg` (installateur)
`construire_source.py`      `.tar.gz` — tous systèmes
==========================  ===========================================

Le `Makefile` du même dossier fait la même chose, en plus court :
``make debian``, ``make windows``, ``make tout``.

Pourquoi tout se construit depuis Linux
---------------------------------------

Trois mécanismes le permettent :

* ``pip download --platform`` **télécharge les roues d'un autre système**. On
  récupère donc depuis Debian les paquets Windows et macOS de NumPy, de Qt et
  du reste, sans jamais démarrer ces systèmes.
* Python publie pour Windows une **distribution « embarquable »** : une
  archive contenant l'interpréteur complet. On la place dans le paquet, et le
  logiciel n'exige alors **rien** de la machine Windows — pas même Python.
* Les outils qui produisent les installateurs existent sous Linux : **NSIS**
  (``makensis``) pour le `.exe`, **msitools** (``wixl``) pour le `.msi`. Le
  `.pkg` de macOS, lui, est écrit entièrement par `macos_pkg.py`, faute de
  `pkgbuild`, de `xar` et de `mkbom`.

Ce que le script ne fait pas, et pourquoi
-----------------------------------------

**Il ne signe rien.** Une signature Windows exige un certificat payant ; une
signature macOS exige un compte développeur Apple et un Mac. Les deux systèmes
afficheront donc un avertissement à la première ouverture, et le `LISEZ-MOI`
de chaque paquet explique comment passer outre — c'est honnête, et cela vaut
mieux qu'un faux sentiment de sécurité.

Utilisation
-----------

.. code-block:: console

    python3 packaging/construire.py --outils      # ce qui manque, et comment
    python3 packaging/construire.py --deps        # installe NSIS et msitools
    python3 packaging/construire.py --tout        # les cinq cibles
    python3 packaging/construire.py --windows     # une seule
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Callable, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from commun import (  # noqa: E402
    GRIS, RACINE_SORTIE, ROUGE, VERT, VARIABLE_SORTIE, Identite,
    appliquer_les_arguments, arguments_communs, dire, dossier_fabrication,
    echec, ecrire_les_documents, ecrire_les_empreintes, etat_des_outils,
    installer_les_outils, lisible, souci, tous_les_paquets)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="construire.py",
        description="Fabrique les paquets d'installation de PhytoScope, "
                    "depuis Debian, Ubuntu ou Mint.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Le Makefile du même dossier fait la même chose, en plus "
               "court :\n  make outils · make deps · make debian · make "
               "windows · make tout\n")
    p.add_argument("--tout", action="store_true", help="toutes les cibles")
    p.add_argument("--deb", "--debian", dest="deb", action="store_true",
                   help="Debian, Ubuntu, Mint")
    p.add_argument("--rpm", "--fedora", dest="rpm", action="store_true",
                   help="Fedora, Red Hat, Rocky, AlmaLinux")
    p.add_argument("--windows", action="store_true",
                   help="Windows 10 et 11 : .zip, .exe et .msi")
    p.add_argument("--macos", action="store_true",
                   help="macOS : archive du .app et installateur .pkg")
    p.add_argument("--source", action="store_true", help="archive source")
    p.add_argument("--outils", action="store_true",
                   help="dire ce qui est installé et ce qui manque")
    p.add_argument("--deps", action="store_true",
                   help="installer NSIS et msitools dans ~/.local/opt, "
                        "sans privilèges")
    p.add_argument("--hors-ligne", action="store_true",
                   help="embarquer les bibliothèques, pour une installation "
                        "sans connexion (atelier, salle de classe)")
    p.add_argument("--nettoyer", action="store_true",
                   help="vider build/paquets avant de construire")
    arguments_communs(p)
    args = p.parse_args(argv)

    if args.deps:
        ok = installer_les_outils()
        etat_des_outils()
        return 0 if ok else 1
    if args.outils:
        etat_des_outils()
        return 0

    demandees = {"source": args.source, "deb": args.deb, "rpm": args.rpm,
                 "macos": args.macos, "windows": args.windows}
    if args.tout or not any(demandees.values()):
        demandees = dict.fromkeys(demandees, True)

    id_ = appliquer_les_arguments(args)

    if args.nettoyer and os.path.isdir(RACINE_SORTIE):
        import shutil
        shutil.rmtree(RACINE_SORTIE)

    #  Le dossier est choisi ICI, une fois, et imposé aux générateurs par
    #  l'environnement : sans cela chacun créerait le sien, et les paquets
    #  d'une même fabrication se retrouveraient éparpillés.
    dossier = dossier_fabrication(id_)
    os.environ[VARIABLE_SORTIE] = dossier

    dire(f"\n  PhytoScope {id_.version}-{id_.release}"
         f"{id_.mention_nom} — fabrication des paquets", VERT)
    dire(f"  {id_.auteur} · {id_.site}", GRIS)
    dire(f"  sortie : {os.path.relpath(dossier, os.path.dirname(RACINE_SORTIE))}\n",
         GRIS)

    options_communes = ["--version", id_.version, "--release", id_.release,
                        "--sortie", dossier]

    #  Du plus rapide au plus long : une panne d'outil se voit alors en dix
    #  secondes, et non au bout du quart d'heure que demande la compression
    #  de l'installateur Windows.
    ordre: List[Tuple[str, str, List[str]]] = [
        ("source", "construire_source", []),
        ("deb", "construire_debian", ["--hors-ligne"] if args.hors_ligne else []),
        ("rpm", "construire_fedora", ["--hors-ligne"] if args.hors_ligne else []),
        ("macos", "construire_macos", ["--hors-ligne"] if args.hors_ligne else []),
        ("windows", "construire_windows", []),
    ]

    faits, rates = 0, []
    debut = time.time()
    for cle, module, options in ordre:
        if not demandees[cle]:
            continue
        #  Chaque générateur est isolé : une panne sur l'un — un outil absent,
        #  un téléchargement coupé — ne doit pas faire perdre les autres. Une
        #  fabrication de vingt minutes qui ne rend rien parce que la dernière
        #  cible a échoué est une fabrication perdue.
        try:
            generateur = __import__(module)
            if generateur.main(options_communes + options) == 0:
                faits += 1
            else:
                rates.append(cle)
        except KeyboardInterrupt:
            raise
        except Exception as exc:                       # noqa: BLE001
            echec(f"cible « {cle} » abandonnée : {type(exc).__name__}: {exc}")
            rates.append(cle)

    ecrire_les_empreintes(id_)
    documents = ecrire_les_documents(id_)

    dire(f"\n  {faits} cible(s) en {time.time() - debut:.0f} s, "
         f"{len(documents)} documents\n", VERT if faits else ROUGE)
    dire(f"  {os.path.relpath(dossier, os.path.dirname(RACINE_SORTIE))}/", GRIS)
    for chemin in tous_les_paquets(id_):
        relatif = os.path.relpath(chemin, dossier)
        dire(f"    {relatif:<52} {lisible(os.path.getsize(chemin)):>9}", GRIS)
    if rates:
        souci(f"cible(s) en échec : {', '.join(rates)}")
    print()
    return 0 if faits and not rates else 1


if __name__ == "__main__":
    sys.exit(main())
