#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/build_windows.py
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

"""Génère les paquets Windows 10 et 11 : archive portable, .exe et .msi.

Trois formes, trois usages :

``PhytoScope-X.Y.Z-Windows-portable.zip``
    On décompresse, on double-clique. Rien ne s'installe, rien n'est inscrit
    dans la base de registre : c'est ce qu'il faut sur un poste où l'on n'a
    pas le droit d'installer, ou sur une clé USB qu'on promène d'un atelier à
    l'autre.

``PhytoScope-X.Y.Z-Windows.exe``
    L'installateur NSIS, posé dans le profil de l'utilisateur
    (``%LOCALAPPDATA%``) : **aucun privilège d'administration n'est demandé**,
    ce qui compte en salle de classe. Raccourcis, entrée dans « Applications
    et fonctionnalités », désinstallateur.

``PhytoScope-X.Y.Z.msi``
    Le format que Windows comprend nativement, celui qu'un service
    informatique déploie par stratégie de groupe ou par Intune, et qui
    s'installe sans un clic : ``msiexec /i PhytoScope-X.Y.Z.msi /qn``. C'est
    ce que produisent les outils commerciaux du genre InstallShield ; ici il
    est fabriqué depuis Debian par ``wixl``, de msitools. Il s'installe pour
    toute la machine et demande donc, lui, les droits d'administration.

Les trois embarquent **l'interpréteur Python**, Qt, NumPy et le logiciel : la
machine qui reçoit n'a besoin de rien.

.. code-block:: console

    python3 packaging/build_windows.py            # les trois
    python3 packaging/build_windows.py --msi      # seulement le MSI

Ce script est autonome : il ne dépend que de `common.py`, et se lance seul ou
par le Makefile du même dossier (`make windows`).
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import uuid
import zipfile
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    ABI_WINDOWS, GABARITS, GRIS, LOGICIEL, PYTHON_WINDOWS, OUTPUT_ROOT,
    VERT, Identite, appliquer_les_arguments, arguments_communs, bien,
    copier_le_logiciel, deplier_les_roues, dire, dossier_sortie, echec,
    ecrire, ecrire_les_documents, ecrire_les_empreintes, environnement_nsis,
    environnement_wixl, etape, executer, fabriquer_icone, lisible, remplir,
    souci, telecharger_les_roues, trouver_makensis, trouver_wixl,
    _python_embarquable, _zipper,
    JAUNE)

#  Un code de mise à niveau fixe, et pour toujours : c'est lui qui dit à
#  Windows que la version 1.6 remplace la 1.5 au lieu de s'installer à côté.
#  Le changer un jour ferait cohabiter deux PhytoScope sur la même machine.
CODE_MISE_A_NIVEAU = "5E2A1C34-9B7D-4F86-A0E1-7C3D9F5B2A48"
GUID_RACCOURCIS = "C71B4E09-3D52-4A18-9F6C-2B8E0D47A135"
GUID_BUREAU = "9A4F7C21-6E83-4D05-B172-8F3A5C60E9D4"


def construire_windows(id_: Identite, faire_zip: bool = True,
                       faire_exe: bool = True,
                       faire_msi: bool = True) -> List[str]:
    dire("\nWindows 10 et 11 — installateur et archive portable\n", JAUNE)
    produits: List[str] = []

    with tempfile.TemporaryDirectory(prefix="phyto-win-") as bac:
        charge = os.path.join(bac, "charge")
        os.makedirs(charge, exist_ok=True)

        etape(f"interpréteur Python {PYTHON_WINDOWS} (distribution embarquable)")
        if not _python_embarquable(os.path.join(charge, "python")):
            echec("interpréteur Windows non récupéré — cible abandonnée")
            return produits

        etape("bibliothèques Windows")
        roues = os.path.join(bac, "roues")
        #  Une seule version ici : l'interpréteur est embarqué, on sait donc
        #  exactement lequel tournera.
        if not telecharger_les_roues("windows", roues, [PYTHON_WINDOWS[:4]]):
            return produits
        etape("installation des bibliothèques dans la charge")
        #  On déplie les roues dans le dossier de l'interpréteur embarqué
        #  plutôt que de les y laisser : l'utilisateur ne doit rien avoir à
        #  faire, et « pip » n'existe pas dans une distribution embarquable.
        site = os.path.join(charge, "python", "Lib", "site-packages")
        if not deplier_les_roues(roues, site, "win_amd64", PYTHON_WINDOWS[:4]):
            return produits

        etape("logiciel et lanceurs")
        copier_le_logiciel(os.path.join(charge, "app"))
        for nom in ("PhytoScope.cmd", "Diagnostic.cmd"):
            #  Fins de ligne CRLF : un .cmd en LF se comporte mal sur
            #  certaines versions de Windows.
            texte = open(os.path.join(GABARITS, "windows", nom),
                         encoding="utf-8").read()
            with open(os.path.join(charge, nom), "w", encoding="utf-8",
                      newline="\r\n") as f:
                f.write(texte)
        shutil.copy2(os.path.join(LOGICIEL, "LICENSE.txt"),
                     os.path.join(charge, "LICENSE.txt"))
        shutil.copy2(os.path.join(LOGICIEL, "README.txt"),
                     os.path.join(charge, "LISEZ-MOI.txt"))
        icone = os.path.join(charge, "phytoscope.ico")
        if not fabriquer_icone(icone, "ico"):
            souci("icône .ico non fabriquée (PySide6 absent de cette machine)")
            icone = ""

        #  1. l'archive portable : elle ne dépend d'aucun outil.
        if faire_zip:
            etape("archive portable")
            zip_cible = os.path.join(
                dossier_sortie(id_, "Windows"), f"PhytoScope-{id_.version}-Windows-portable.zip")
            _zipper(charge, zip_cible,
                    racine_interne=f"PhytoScope-{id_.version}")
            bien(f"{os.path.basename(zip_cible)}  "
                 f"({lisible(os.path.getsize(zip_cible))})")
            produits.append(zip_cible)

        #  2. le MSI, pour le déploiement en parc.
        if faire_msi:
            msi = _construire_msi(id_, charge, icone, bac)
            if msi:
                produits.append(msi)

        #  3. l'installateur NSIS, pour l'utilisateur seul.
        if not faire_exe:
            return produits
        makensis = trouver_makensis()
        if not makensis:
            souci("makensis absent — pas d'installateur .exe")
            dire("      make deps   (ou : python3 build.py --deps)", GRIS)
            return produits

        etape("installateur NSIS")
        exe = os.path.join(dossier_sortie(id_, "Windows"), f"PhytoScope-{id_.version}-Windows.exe")
        script = os.path.join(bac, "phytoscope.nsi")
        ecrire(script, remplir(
            os.path.join(GABARITS, "windows", "phytoscope.nsi"),
            dict(id_.jetons(), SORTIE=exe, CHARGE=charge,
             ICONE=icone or os.path.join(charge, "app", "phytoscope"),
             FICHIER_LICENCE=os.path.join(charge, "LICENSE.txt"))))
        if executer([makensis, "-V2", script], env=environnement_nsis()):
            bien(f"{os.path.basename(exe)}  ({lisible(os.path.getsize(exe))})")
            produits.append(exe)
    return produits


def _construire_msi(id_: Identite, charge: str, icone: str,
                    bac: str) -> Optional[str]:
    """Le paquet MSI, assemblé par wixl à partir d'un descriptif WiX.

    Un MSI exige que **chaque composant porte un identifiant fixe** : c'est
    par lui que Windows reconnaît, lors d'une mise à jour, le fichier qu'il
    faut remplacer. On les dérive donc du chemin par un UUID de version 5,
    qui est déterministe — deux fabrications du même logiciel donnent les
    mêmes identifiants, et la mise à jour d'un parc se passe bien.
    """
    wixl = trouver_wixl()
    if not wixl:
        souci("wixl absent — pas de paquet .msi")
        dire("      make deps   (ou : python3 build.py --deps)", GRIS)
        return None

    etape("paquet MSI")
    #  MSI n'accepte qu'une version à trois nombres. Un suffixe comme « -rc1 »
    #  n'y a pas sa place : on le laisse au nom du fichier.
    nombres = id_.version.split("-")[0].split(".")[:3]
    while len(nombres) < 3:
        nombres.append("0")
    version_msi = ".".join(nombres)

    espace = uuid.UUID(CODE_MISE_A_NIVEAU)
    composants: List[str] = []
    #  wixl résout les chemins `Source` depuis son répertoire courant, et
    #  refuse les chemins absolus. On décrit donc l'arborescence en relatif et
    #  l'on se place dans la charge au moment de l'appeler.
    fragment = _fragment_wix(charge, espace, composants)
    fragment += ['    <ComponentGroup Id="Fichiers">']
    fragment += [f'      <ComponentRef Id="{c}"/>' for c in composants]
    fragment += ["    </ComponentGroup>", "  </Fragment>", "</Wix>"]

    source_fichiers = os.path.join(bac, "fichiers.wxs")
    ecrire(source_fichiers, "\n".join(fragment) + "\n")

    source_principale = os.path.join(bac, "phytoscope.wxs")
    ecrire(source_principale, remplir(
        os.path.join(GABARITS, "windows", "phytoscope.wxs"),
        dict(id_.jetons(), VERSION_MSI=version_msi,
             UPGRADE_CODE=CODE_MISE_A_NIVEAU,
             GUID_RACCOURCIS=GUID_RACCOURCIS, GUID_BUREAU=GUID_BUREAU,
             ICONE=os.path.basename(icone) if icone else "phytoscope.ico")))

    cible = os.path.join(dossier_sortie(id_, "Windows"), f"PhytoScope-{id_.version}.msi")
    if not executer([wixl, "-a", "x64", "-o", cible,
                     source_principale, source_fichiers],
                    cwd=charge, env=environnement_wixl()):
        return None
    bien(f"{os.path.basename(cible)}  ({lisible(os.path.getsize(cible))})")
    return cible


def _echapper(texte: str) -> str:
    return (texte.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _fragment_wix(charge: str, espace, composants: List[str]) -> List[str]:
    """Le descriptif WiX de l'arborescence, écrit récursivement.

    Récursif et non itératif : refermer les balises `<Directory>` au bon
    moment avec `os.walk` demanderait de suivre soi-même la pile des
    dossiers, et la moindre erreur produit un XML déséquilibré que wixl
    rejette par un message peu parlant.
    """
    lignes = ['<?xml version="1.0" encoding="utf-8"?>',
              '<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">',
              "  <Fragment>",
              '    <DirectoryRef Id="INSTALLDIR">']
    composants.clear()

    def identifiant(prefixe: str, chemin: str) -> str:
        return f"{prefixe}{uuid.uuid5(espace, chemin).hex[:24]}"

    def descendre(absolu: str, relatif: str, marge: str) -> None:
        entrees = sorted(os.listdir(absolu))
        for nom in entrees:
            complet = os.path.join(absolu, nom)
            chemin = f"{relatif}/{nom}" if relatif else nom
            if os.path.isdir(complet):
                lignes.append(f'{marge}<Directory Id="{identifiant("d", chemin)}" '
                              f'Name="{_echapper(nom)}">')
                descendre(complet, chemin, marge + "  ")
                lignes.append(f"{marge}</Directory>")
            else:
                cid = identifiant("c", chemin)
                guid = str(uuid.uuid5(espace, "composant:" + chemin)).upper()
                composants.append(cid)
                #  Relatif à la charge : c'est depuis là que wixl est lancé.
                relatif_source = chemin
                #  `extend` et non `+=` : dans une fonction imbriquée, `+=`
                #  ferait de `lignes` une variable locale, et Python lèverait
                #  `UnboundLocalError` avant même la première écriture.
                lignes.extend([
                    f'{marge}<Component Id="{cid}" Guid="{{{guid}}}" Win64="yes">',
                    f'{marge}  <File Id="{identifiant("f", chemin)}" '
                    f'Name="{_echapper(nom)}" '
                    f'Source="{_echapper(relatif_source)}" KeyPath="yes"/>',
                    f"{marge}</Component>",
                ])

    descendre(charge, "", "      ")
    lignes.append("    </DirectoryRef>")
    return lignes


def _tout(args) -> bool:
    """Aucune option de cible : on les fait toutes."""
    cibles = [v for c, v in vars(args).items()
              if c in ("zip", "exe", "msi", "pkg")]
    return not any(cibles)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="build_windows.py",
        description="Fabrique les paquets Windows de PhytoScope.")
    arguments_communs(p)
    p.add_argument("--zip", action="store_true",
                   help="seulement l'archive portable")
    p.add_argument("--exe", action="store_true",
                   help="seulement l'installateur NSIS")
    p.add_argument("--msi", action="store_true",
                   help="seulement le paquet MSI")
    args = p.parse_args(argv)

    id_ = appliquer_les_arguments(args)
    dire(f"\n  PhytoScope {id_.version}-{id_.release} — Windows 10 et 11", VERT)
    produits = [x for x in construire_windows(id_, faire_zip=_tout(args) or args.zip,
                              faire_exe=_tout(args) or args.exe,
                              faire_msi=_tout(args) or args.msi) if x]
    if produits:
        ecrire_les_empreintes(id_)
        ecrire_les_documents(id_)
    for f in produits:
        dire(f"    {os.path.relpath(f, OUTPUT_ROOT)}", GRIS)
    return 0 if produits else 1


if __name__ == "__main__":
    sys.exit(main())
