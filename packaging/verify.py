#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/verify.py
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

"""Relit les paquets produits et contrôle qu'ils disent ce qu'on a voulu.

Un paquet ne se vérifie pas en le regardant : il se vérifie en l'ouvrant. Ce
script rouvre chacun de ceux qui se trouvent dans `build/paquets` et contrôle,
selon son format :

* **`.deb`** — métadonnées lisibles par `dpkg-deb`, version conforme, présence
  du lanceur, de l'entrée de menu et du logiciel ;
* **`.rpm`** — idem par `rpm -qip` et `rpm -qlp` ;
* **`.msi`** — document composé OLE valide, tables lisibles par `msiinfo` ;
* **`.pkg`** — les trois formats imbriqués (XAR, cpio, BOM) se relisent et
  décrivent le même ensemble de fichiers ;
* **`.zip`** — contenu attendu, et **bit d'exécution conservé** pour le
  lanceur du paquet `.app`, faute de quoi macOS refuse de l'ouvrir ;
* **`.exe`** — véritable exécutable Windows (signature `PE`) ;
* **`.tar.gz`** — s'ouvre, et contient le logiciel.

Ce qui n'est pas vérifié, et ne peut pas l'être ici : qu'un paquet
**s'installe**. Il n'y a sur cette machine ni Windows, ni macOS, ni Fedora.
Le script le dit plutôt que de le laisser croire.

.. code-block:: console

    python3 packaging/verify.py        ou    make verifier
"""
from __future__ import annotations

import os
import subprocess
import sys
import tarfile
import zipfile
from typing import Callable, Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import macos_pkg  # noqa: E402
from common import (  # noqa: E402
    GRIS, JAUNE, RACINE_SORTIE, ROUGE, VERT, Identite, bien, dire, echec,
    environnement_wixl, fabrications, lisible, souci, trouver_wixl)


def _sortie(commande: List[str], env=None) -> str:
    try:
        r = subprocess.run(commande, capture_output=True, timeout=180, env=env)
        return r.stdout.decode("utf-8", "replace")
    except (OSError, subprocess.TimeoutExpired):
        return ""


def verifier_deb(chemin: str, id_: Identite) -> List[str]:
    infos = _sortie(["dpkg-deb", "-I", chemin])
    contenu = _sortie(["dpkg-deb", "-c", chemin])
    soucis = []
    if f"Version: {id_.version}" not in infos:
        soucis.append("la version annoncée ne correspond pas")
    for attendu in ("./usr/bin/phytoscope",
                    "./usr/share/applications/phytoscope.desktop",
                    "./usr/share/phytoscope/run.py"):
        if attendu not in contenu:
            soucis.append(f"absent : {attendu}")
    if "postinst" not in infos:
        soucis.append("script d'après-installation absent")
    return soucis


def verifier_rpm(chemin: str, id_: Identite) -> List[str]:
    infos = _sortie(["rpm", "-qip", chemin])
    contenu = _sortie(["rpm", "-qlp", chemin])
    soucis = []
    if f"Version     : {id_.version}" not in infos.replace("\t", " "):
        if id_.version not in infos:
            soucis.append("la version annoncée ne correspond pas")
    for attendu in ("/usr/bin/phytoscope", "/usr/share/phytoscope/run.py"):
        if attendu not in contenu:
            soucis.append(f"absent : {attendu}")
    return soucis


def verifier_msi(chemin: str, id_: Identite) -> List[str]:
    soucis = []
    with open(chemin, "rb") as f:
        if f.read(8) != b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            soucis.append("ce n'est pas un document composé OLE")
            return soucis
    outil = os.path.join(os.path.dirname(trouver_wixl() or ""), "msiinfo")
    if not os.path.exists(outil):
        souci("msiinfo absent — le MSI n'est contrôlé que par sa signature")
        return soucis
    env = environnement_wixl()
    tables = _sortie([outil, "tables", chemin], env=env)
    for table in ("File", "Component", "Directory", "Feature", "Property"):
        if table not in tables:
            soucis.append(f"table MSI absente : {table}")
    proprietes = _sortie([outil, "export", chemin, "Property"], env=env)
    if id_.version.split("-")[0] not in proprietes:
        soucis.append("la version annoncée ne correspond pas")
    return soucis


def verifier_pkg(chemin: str, id_: Identite) -> List[str]:
    try:
        rapport = macos_pkg.verifier_pkg(
            chemin, attendus=["./PhytoScope.app/Contents/MacOS/phytoscope",
                              "./PhytoScope.app/Contents/Info.plist"])
    except (OSError, ValueError) as exc:
        return [str(exc)]
    soucis = []
    if rapport["version"] != id_.version:
        soucis.append(f"version annoncée : {rapport['version']}")
    if rapport["destination"] != "/Applications":
        soucis.append(f"destination : {rapport['destination']}")
    return soucis


def verifier_zip(chemin: str, id_: Identite) -> List[str]:
    soucis = []
    with zipfile.ZipFile(chemin) as z:
        noms = z.namelist()
        abime = z.testzip()
        if abime:
            soucis.append(f"membre abîmé : {abime}")
        if "macOS" in os.path.basename(chemin):
            lanceur = "PhytoScope.app/Contents/MacOS/phytoscope"
            if lanceur not in noms:
                soucis.append("le lanceur du paquet .app est absent")
            else:
                mode = z.getinfo(lanceur).external_attr >> 16
                if not mode & 0o111:
                    soucis.append("le lanceur n'a pas son bit d'exécution — "
                                  "macOS refusera d'ouvrir l'application")
        else:
            for morceau in ("python/pythonw.exe", "PhytoScope.cmd", "app/run.py"):
                if not any(n.endswith(morceau) for n in noms):
                    soucis.append(f"absent : {morceau}")
    return soucis


def verifier_exe(chemin: str, id_: Identite) -> List[str]:
    with open(chemin, "rb") as f:
        tete = f.read(2)
        f.seek(0x3C)
        decalage = int.from_bytes(f.read(4), "little")
        f.seek(decalage)
        signature = f.read(4)
    soucis = []
    if tete != b"MZ" or signature[:2] != b"PE":
        soucis.append("ce n'est pas un exécutable Windows")
    return soucis


def verifier_targz(chemin: str, id_: Identite) -> List[str]:
    with tarfile.open(chemin, "r:gz") as tar:
        noms = tar.getnames()
    return [] if any(n.endswith("/run.py") for n in noms) else \
        ["le logiciel est absent de l'archive"]


VERIFICATEURS: List[Tuple[str, Callable]] = [
    (".deb", verifier_deb), (".rpm", verifier_rpm), (".msi", verifier_msi),
    (".pkg", verifier_pkg), (".zip", verifier_zip), (".exe", verifier_exe),
    (".tar.gz", verifier_targz),
]


def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    p = argparse.ArgumentParser(
        prog="verify.py",
        description="Rouvre les paquets produits et contrôle leur structure.")
    p.add_argument("dossier", nargs="?", default="",
                   help="la fabrication à vérifier ; par défaut, la plus "
                        "récente de build/paquets")
    args = p.parse_args(argv)

    base = os.path.abspath(args.dossier) if args.dossier else ""
    if not base:
        candidats = fabrications()
        if not candidats:
            echec(f"aucune fabrication dans {RACINE_SORTIE}")
            return 1
        base = candidats[0]
    if not os.path.isdir(base):
        echec(f"{base} n'existe pas")
        return 1

    id_ = Identite.lire()
    dire(f"\n  Vérification — {os.path.basename(base)}\n", VERT)

    #  Les paquets vivent dans les sous-dossiers de système, et l'archive
    #  source à la racine : on parcourt donc tout l'arbre.
    paquets = []
    for dossier, _, noms in os.walk(base):
        for nom in sorted(noms):
            #  Les accompagnements ne sont pas des paquets : signatures,
            #  empreintes, documents et certificat sont contrôlés à part.
            if not nom.endswith((".sha256", ".txt", ".p7s", ".pem", ".crt")):
                paquets.append(os.path.join(dossier, nom))
    if not paquets:
        echec("aucun paquet dans cette fabrication")
        return 1

    total_soucis = 0
    systeme_courant = None
    for chemin in sorted(paquets):
        relatif = os.path.relpath(chemin, base)
        systeme = os.path.dirname(relatif) or "(racine)"
        if systeme != systeme_courant:
            dire(f"\n  {systeme}", JAUNE)
            systeme_courant = systeme
        nom = os.path.basename(chemin)
        verificateur = next((v for suffixe, v in VERIFICATEURS
                             if nom.endswith(suffixe)), None)
        if verificateur is None:
            dire(f"  · {nom} — format non reconnu, ignoré", GRIS)
            continue
        try:
            soucis = verificateur(chemin, id_)
        except Exception as exc:                       # noqa: BLE001
            soucis = [f"{type(exc).__name__}: {exc}"]
        taille = lisible(os.path.getsize(chemin))
        if soucis:
            echec(f"{nom:<46} {taille:>9}")
            for s_ in soucis:
                dire(f"        {s_}", ROUGE)
            total_soucis += len(soucis)
        else:
            bien(f"{nom:<46} {taille:>9}")

        #  L'empreinte individuelle et la signature doivent être là.
        for suffixe, quoi in ((".sha256", "empreinte"), (".p7s", "signature")):
            if not os.path.exists(chemin + suffixe):
                echec(f"        {quoi} absente : {nom}{suffixe}")
                total_soucis += 1

    #  Les documents d'accompagnement.
    dire("")
    for dossier in [base] + [os.path.join(base, d) for d in sorted(os.listdir(base))
                             if os.path.isdir(os.path.join(base, d))]:
        absents = [d for d in ("readme.txt", "install.txt", "licence.txt",
                               "changelog.txt")
                   if not os.path.exists(os.path.join(dossier, d))]
        etiquette = os.path.relpath(dossier, base)
        etiquette = "(racine)" if etiquette == "." else etiquette
        if absents:
            echec(f"documents absents dans {etiquette} : {', '.join(absents)}")
            total_soucis += len(absents)
        else:
            bien(f"documents présents dans {etiquette}")

    #  Le récapitulatif des empreintes.
    sha = os.path.join(base, f"phytoscope-{id_.version}.sha256")
    if os.path.exists(sha):
        r = subprocess.run(["sha256sum", "-c", os.path.basename(sha)],
                           cwd=base, capture_output=True)
        if r.returncode == 0:
            bien("empreintes SHA-256 conformes")
        else:
            echec("empreintes SHA-256 : au moins un fichier a changé")
            total_soucis += 1
    else:
        souci("pas de récapitulatif d'empreintes")

    dire("")
    souci("aucun de ces paquets n'a été INSTALLÉ : il n'y a sur cette "
          "machine\n    ni Windows, ni macOS, ni Fedora. Ce qui est vérifié "
          "ici, c'est leur\n    structure et leur cohérence interne.")
    dire("")
    return 0 if total_soucis == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
