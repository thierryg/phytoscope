#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/sbom.py
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

"""La nomenclature logicielle du projet entier — logiciel **et** micrologiciel.

Il existait déjà `src/phytoscope/tools/sbom.py`, qui recense les
bibliothèques Python. Il reste, et il est livré dans les paquets : c'est la
nomenclature du *logiciel*, celle qui accompagne ce qu'on installe.

Ce script-ci répond à une autre question — « de quoi est fait **le projet** ? »
— et couvre donc aussi le micrologiciel RP2350, dont les dépendances ne sont
pas des paquets Python : le Pico SDK, TinyUSB, la chaîne de compilation ARM.
Sans elles, la nomenclature était incomplète, et une nomenclature incomplète
donne une fausse assurance : elle sert à répondre « cette faille me
concerne-t-elle ? », et une réponse fondée sur une liste partielle vaut moins
que pas de réponse.

Deux sources, aucune recopie
----------------------------

* la partie **logiciel** est demandée à `src/phytoscope/tools/sbom.py`, qui
  relève les versions **réellement installées** ; la redire ici la ferait
  diverger au premier ajout de dépendance ;
* la partie **micrologiciel** est lue dans les fichiers qui font foi :
  `src/firmware/_make_.sh` pour les versions du Pico SDK et de la chaîne ARM,
  `src/firmware/CMakeLists.txt` pour les bibliothèques réellement liées.
  Écrire ces versions à la main dans un tableau serait le plus sûr moyen de
  les voir vieillir en silence.

Usage :
    python3 tools/sbom.py                    le relevé, en texte
    python3 tools/sbom.py --json             CycloneDX 1.6 sur la sortie
    python3 tools/sbom.py --ecrire           écrit sbom.cdx.json à la racine
    python3 tools/sbom.py --verifier         est-il à jour ? (code 1 sinon)
    python3 tools/sbom.py --logiciel-seul    régénère aussi celui du logiciel
"""
from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import re
import subprocess
import sys
import uuid
from typing import Dict, List, Optional

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGICIEL = os.path.join(RACINE, "src", "phytoscope")
FIRMWARE = os.path.join(RACINE, "src", "firmware")
SORTIE = os.path.join(RACINE, "sbom.cdx.json")
SORTIE_LOGICIEL = os.path.join(LOGICIEL, "sbom.cdx.json")

VERT, JAUNE, ROUGE, GRIS, NEUTRE = (
    "\033[0;32m", "\033[0;33m", "\033[0;31m", "\033[0;90m", "\033[0m")


def dire(texte: str = "", couleur: str = "") -> None:
    print(f"{couleur}{texte}{NEUTRE}" if couleur else texte)


# ---------------------------------------------------------------------------
#  Le micrologiciel
# ---------------------------------------------------------------------------
#  Ce que le micrologiciel emporte, et qui ne vient pas de PyPI. L'éditeur et
#  la licence sont écrits ici — ils ne changent pas —, mais **jamais la
#  version** : celle-là est lue dans les fichiers du projet.
TIERS_FIRMWARE = {
    "pico-sdk": {
        "editeur": "Raspberry Pi Ltd",
        "licence": "BSD-3-Clause",
        "role": "bibliothèque de base du RP2350 : horloges, DMA, multicœur",
        "url": "https://github.com/raspberrypi/pico-sdk",
        "purl": "pkg:github/raspberrypi/pico-sdk@{version}",
    },
    "tinyusb": {
        "editeur": "Ha Thach et contributeurs",
        "licence": "MIT",
        "role": "pile USB : port série virtuel et MIDI",
        "url": "https://github.com/hathach/tinyusb",
        #  Livrée *dans* le Pico SDK : sa version suit celle du SDK, et
        #  l'annoncer indépendamment serait inventer un numéro.
        "version_suit": "pico-sdk",
    },
    "arm-gnu-toolchain": {
        "editeur": "Arm Ltd",
        "licence": "GPL-3.0-with-GCC-exception",
        "role": "compilateur croisé — outil de construction, non embarqué",
        "url": "https://developer.arm.com/downloads/-/arm-gnu-toolchain-downloads",
        "scope": "excluded",
    },
    "picotool": {
        "editeur": "Raspberry Pi Ltd",
        "licence": "BSD-3-Clause",
        "role": "produit le .uf2 — outil de construction, non embarqué",
        "url": "https://github.com/raspberrypi/picotool",
        "version_suit": "pico-sdk",
        "scope": "excluded",
    },
}


def _lire_version(chemin: str, variable: str) -> str:
    """La valeur d'une variable de script shell — « SDK_VERSION="2.3.1" »."""
    try:
        with open(chemin, encoding="utf-8") as f:
            texte = f.read()
    except OSError:
        return ""
    m = re.search(rf'^\s*{variable}\s*=\s*"?([^"\s#]+)"?', texte, re.M)
    return m.group(1) if m else ""


def bibliotheques_liees() -> List[str]:
    """Les bibliothèques que `CMakeLists.txt` lie réellement.

    On lit le fichier plutôt que de tenir une liste : une bibliothèque
    ajoutée au micrologiciel doit apparaître à la nomenclature sans qu'on y
    pense, et une bibliothèque retirée doit en disparaître.
    """
    chemin = os.path.join(FIRMWARE, "CMakeLists.txt")
    try:
        with open(chemin, encoding="utf-8") as f:
            texte = f.read()
    except OSError:
        return []
    #  `target_link_libraries(cible  a b c )` — on prend le bloc, puis les
    #  identifiants, en écartant le nom de la cible et les mots-clés CMake.
    bloc = re.search(r"target_link_libraries\s*\(([^)]*)\)", texte, re.S)
    if not bloc:
        return []
    mots = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", bloc.group(1))
    exclus = {"phytosense", "PRIVATE", "PUBLIC", "INTERFACE"}
    return [m for m in mots if m not in exclus]


def inventaire_firmware() -> List[Dict[str, str]]:
    """Ce dont le micrologiciel est fait, versions lues dans les sources."""
    #  `_make_.sh` est le script de COMPILATION : c'est lui qui fixe la
    #  version du SDK. `build.sh`, à côté, est l'enveloppe qui range le
    #  livrable — il n'a pas à connaître ces versions.
    build = os.path.join(FIRMWARE, "_make_.sh")
    version_sdk = _lire_version(build, "SDK_VERSION")
    version_arm = _lire_version(build, "ARM_VERSION")
    versions = {"pico-sdk": version_sdk, "arm-gnu-toolchain": version_arm}

    lignes = []
    for nom, info in TIERS_FIRMWARE.items():
        version = versions.get(nom, "")
        if not version and info.get("version_suit"):
            version = versions.get(info["version_suit"], "")
        lignes.append({
            "nom": nom,
            "version": version or "—",
            "editeur": info["editeur"],
            "licence": info["licence"],
            "role": info["role"],
            "url": info["url"],
            "purl": info.get("purl", "").format(version=version) if version else "",
            "scope": info.get("scope", "required"),
        })
    return lignes


def sources_firmware() -> List[str]:
    """Les fichiers du micrologiciel que nous avons écrits."""
    if not os.path.isdir(FIRMWARE):
        return []
    return sorted(
        f for f in os.listdir(FIRMWARE)
        if f.endswith((".c", ".h")) and os.path.isfile(os.path.join(FIRMWARE, f)))


# ---------------------------------------------------------------------------
#  Le logiciel — demandé à son propre outil
# ---------------------------------------------------------------------------
def inventaire_logiciel() -> List[Dict[str, object]]:
    """Le relevé du logiciel, produit par son outil et non recopié ici."""
    chemin = os.path.join(LOGICIEL, "tools", "sbom.py")
    if not os.path.exists(chemin):
        dire(f"  ! introuvable : {chemin}", JAUNE)
        return []
    #  Chargé par son chemin : ce n'est pas un module installable, et
    #  l'importer autrement demanderait de bricoler sys.path des deux côtés.
    spec = importlib.util.spec_from_file_location("sbom_logiciel", chemin)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        return module.inventaire()
    except Exception as exc:                           # noqa: BLE001
        dire(f"  ! relevé du logiciel impossible : {exc}", JAUNE)
        return []


def _identite() -> Dict[str, str]:
    """Version, éditeur et contact, lus où ils font foi."""
    defaut = {"version": "?", "auteur": "Bretagne Namasté",
              "contact": "contact@bretagne-namaste.com",
              "site": "https://bretagne-namaste.com"}
    fichier = os.path.join(LOGICIEL, "phytoscope", "VERSION")
    version = _lire_cle_valeur(fichier, "version")
    auteurs = os.path.join(LOGICIEL, "phytoscope", "AUTHORS")
    return {
        "version": version or defaut["version"],
        "auteur": _lire_cle_valeur(auteurs, "editeur") or defaut["auteur"],
        "contact": _lire_cle_valeur(auteurs, "contact") or defaut["contact"],
        "site": _lire_cle_valeur(auteurs, "site") or defaut["site"],
    }


def _lire_cle_valeur(chemin: str, cle: str) -> str:
    """Un fichier « clé = valeur », volontairement pauvre — voir VERSION."""
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if ligne.startswith("#") or "=" not in ligne:
                    continue
                k, _, v = ligne.partition("=")
                if k.strip() == cle:
                    return v.strip()
    except OSError:
        pass
    return ""


# ---------------------------------------------------------------------------
#  Rendus
# ---------------------------------------------------------------------------
def en_texte(logiciel, firmware) -> str:
    id_ = _identite()
    lignes = [
        "",
        f"  PhytoScope {id_['version']} — nomenclature du projet",
        "",
        "  LOGICIEL — src/phytoscope/  (bibliothèques Python)",
        "",
    ]
    for d in logiciel:
        marque = "·" if d["etat"] == "installé" else " "
        obligatoire = "requise " if d["obligatoire"] else "optionnelle"
        lignes.append(f"   {marque} {d['paquet']:<16} {d['version']:<12} "
                      f"{obligatoire:<12} {d['licence']:<26} {d['role']}")

    lignes += ["", "  MICROLOGICIEL — src/firmware/  (RP2350, C)", ""]
    for d in firmware:
        portee = "livrée " if d["scope"] == "required" else "outil  "
        lignes.append(f"   · {d['nom']:<20} {d['version']:<12} "
                      f"{portee:<12} {d['licence']:<26} {d['role']}")

    liees = bibliotheques_liees()
    if liees:
        lignes += ["",
                   "    Bibliothèques liées, d'après CMakeLists.txt :",
                   "      " + ", ".join(liees)]
    sources = sources_firmware()
    if sources:
        lignes += [f"    Nos sources : {len(sources)} fichiers "
                   f"({', '.join(sources[:4])}…)"]

    manquantes = [d["nom"] for d in firmware if d["version"] == "—"]
    if manquantes:
        lignes += ["", f"  ! version indéterminée : {', '.join(manquantes)}"]

    lignes += ["",
               f"  {len([d for d in logiciel if d['etat'] == 'installé'])} "
               f"composants logiciels, {len(firmware)} composants "
               f"micrologiciels.", ""]
    return "\n".join(lignes)


def en_cyclonedx(logiciel, firmware) -> dict:
    """CycloneDX 1.6, avec un sous-ensemble par nature de produit.

    Deux composants imbriqués plutôt qu'une liste plate : « de quoi est fait
    le logiciel » et « de quoi est fait le micrologiciel » sont deux
    questions, et un outil d'analyse qui lit ce document doit pouvoir les
    séparer — le compilateur ARM n'est pas embarqué dans le produit, il sert
    à le construire, d'où le `scope: excluded`.
    """
    id_ = _identite()

    composants_logiciel = []
    for d in logiciel:
        if d["etat"] == "absent":
            continue
        composants_logiciel.append({
            "type": "library",
            "name": d["paquet"],
            "version": d["version"],
            "purl": f"pkg:pypi/{d['paquet']}@{d['version']}",
            "publisher": d["editeur"],
            "description": d["role"],
            "licenses": [{"license": {"id": d["licence"]}}],
            "scope": "required" if d["obligatoire"] else "optional",
        })

    composants_firmware = []
    for d in firmware:
        composant = {
            "type": "library",
            "name": d["nom"],
            "version": d["version"],
            "publisher": d["editeur"],
            "description": d["role"],
            "licenses": [{"license": {"id": d["licence"]}}],
            "scope": d["scope"],
            "externalReferences": [{"type": "website", "url": d["url"]}],
        }
        if d["purl"]:
            composant["purl"] = d["purl"]
        composants_firmware.append(composant)

    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.6",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
            "tools": {"components": [{
                "type": "application", "name": "phytoscope-sbom-projet",
                "version": id_["version"], "publisher": id_["auteur"]}]},
            "authors": [{"name": id_["auteur"], "email": id_["contact"]}],
            "component": {
                "type": "application",
                "name": "PhytoScope",
                "version": id_["version"],
                "publisher": id_["auteur"],
                "description": "Écouter les plantes sans raconter d'histoires "
                               "— logiciel, micrologiciel et matériel.",
                "licenses": [{"license": {"id": "MIT"}}],
                "externalReferences": [{"type": "website",
                                        "url": id_["site"]}],
            },
        },
        "components": [
            {
                "type": "application",
                "name": "phytoscope-logiciel",
                "version": id_["version"],
                "description": "Le logiciel d'acquisition et de sonification "
                               "(Python 3, Qt 6).",
                "licenses": [{"license": {"id": "MIT"}}],
                "components": composants_logiciel,
            },
            {
                "type": "firmware",
                "name": "phytosense-firmware",
                "version": id_["version"],
                "description": "Le micrologiciel de la carte PhytoSense One "
                               "(RP2350, C).",
                "licenses": [{"license": {"id": "MIT"}}],
                "components": composants_firmware,
            },
        ],
    }


# ---------------------------------------------------------------------------
#  Vérification
# ---------------------------------------------------------------------------
def _signature(document: dict) -> List[List[str]]:
    """Ce qui compte pour dire « à jour » : les composants, pas la date.

    Le document porte l'horodatage de sa production et un numéro de série
    tiré au hasard : les comparer ferait une révision par jour, sans qu'une
    seule dépendance ait bougé.
    """
    trouves = []

    def parcourir(liste):
        for c in liste or []:
            if c.get("version") is not None and c.get("name"):
                trouves.append([c.get("name", ""), str(c.get("version", "")),
                                c.get("scope", "")])
            parcourir(c.get("components"))

    parcourir(document.get("components"))
    return sorted(trouves)


def verifier() -> int:
    """Le fichier versionné correspond-il à ce qu'on relèverait maintenant ?"""
    if not os.path.exists(SORTIE):
        dire(f"\n  ! {os.path.relpath(SORTIE, RACINE)} n'existe pas.", JAUNE)
        dire("      python3 tools/sbom.py --ecrire\n", GRIS)
        return 1
    try:
        with open(SORTIE, encoding="utf-8") as f:
            ancien = json.load(f)
    except (OSError, ValueError) as exc:
        dire(f"\n  ! {os.path.relpath(SORTIE, RACINE)} illisible : {exc}\n", ROUGE)
        return 1

    neuf = en_cyclonedx(inventaire_logiciel(), inventaire_firmware())
    a, b = _signature(ancien), _signature(neuf)
    if a == b:
        dire(f"\n  ✓ {os.path.relpath(SORTIE, RACINE)} est à jour "
             f"({len(b)} composants).\n", VERT)
        return 0

    dire(f"\n  ! {os.path.relpath(SORTIE, RACINE)} ne correspond plus :\n", JAUNE)
    avant = {n: (v, s) for n, v, s in a}
    apres = {n: (v, s) for n, v, s in b}
    for nom in sorted(set(avant) | set(apres)):
        if avant.get(nom) != apres.get(nom):
            va = avant.get(nom, ("absent",))[0]
            vb = apres.get(nom, ("absent",))[0]
            dire(f"      {nom:<24} {va}  →  {vb}", GRIS)
    dire("")
    dire("      python3 tools/sbom.py --ecrire", GRIS)
    dire("")
    return 1


# ---------------------------------------------------------------------------
#  Ligne de commande
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="sbom.py",
        description="Nomenclature logicielle du projet — logiciel et micrologiciel.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Sans option : le relevé, en texte.")
    p.add_argument("--json", action="store_true",
                   help="CycloneDX 1.6 sur la sortie standard")
    p.add_argument("--ecrire", action="store_true",
                   help=f"écrit {os.path.relpath(SORTIE, RACINE)}")
    p.add_argument("--verifier", action="store_true",
                   help="le fichier versionné est-il à jour ? (code 1 sinon)")
    p.add_argument("--logiciel-seul", action="store_true",
                   help="régénère aussi src/phytoscope/sbom.cdx.json, "
                        "celui qui est livré dans les paquets")
    p.add_argument("-o", "--output", metavar="FICHIER",
                   help="écrire ailleurs que dans sbom.cdx.json")
    args = p.parse_args(argv)

    if args.verifier:
        return verifier()

    logiciel = inventaire_logiciel()
    firmware = inventaire_firmware()

    #  Celui du logiciel est livré dans les paquets : on le régénère par son
    #  propre outil, jamais en recopiant une partie de ce document — les deux
    #  n'ont pas la même portée, et les confondre les ferait divergеr.
    if args.logiciel_seul:
        r = subprocess.run(
            [sys.executable, os.path.join(LOGICIEL, "tools", "sbom.py"),
             "--json", "-o", SORTIE_LOGICIEL],
            capture_output=True, text=True)
        if r.returncode == 0:
            dire(f"  ✓ {os.path.relpath(SORTIE_LOGICIEL, RACINE)}", VERT)
        else:
            dire(f"  ✗ {r.stderr.strip()[:200]}", ROUGE)
            return 1

    document = en_cyclonedx(logiciel, firmware)

    if args.json and not args.ecrire and not args.output:
        print(json.dumps(document, ensure_ascii=False, indent=2))
        return 0

    if args.ecrire or args.output:
        cible = args.output or SORTIE
        os.makedirs(os.path.dirname(os.path.abspath(cible)), exist_ok=True)
        with open(cible, "w", encoding="utf-8") as f:
            json.dump(document, f, ensure_ascii=False, indent=2)
            f.write("\n")
        n = len(_signature(document))
        dire(f"  ✓ {os.path.relpath(cible, RACINE)} — {n} composants", VERT)
        return 0

    print(en_texte(logiciel, firmware))
    return 0


if __name__ == "__main__":
    sys.exit(main())
