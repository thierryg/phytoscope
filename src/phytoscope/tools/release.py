#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/release.py
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

"""Gestion des versions et fabrication des archives de diffusion.

Une seule source de vérité — `phytoscope/VERSION` — et un outil qui la
modifie proprement, tient le journal des modifications à jour et fabrique
l'archive. Aucune dépendance : cet outil doit fonctionner sur une machine
nue, y compris pour préparer une version depuis une clé USB.

    python3 tools/release.py show
    python3 tools/release.py bump patch --name "Sève d'automne"
    python3 tools/release.py check
    python3 tools/release.py dist
    python3 tools/release.py tag

Cycle conseillé :

    1. développer ; la version porte le suffixe -dev
    2. `bump minor` ou `bump patch` : retire le suffixe, date la version,
       ouvre une section dans CHANGELOG.txt
    3. compléter la section du journal à la main
    4. `check` puis `dist`, enfin `tag`
"""
from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
import tarfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#  Le numéro vit dans un fichier de données, pas dans du code : c'est
#  ainsi que la fabrique de paquets, les documents et le logiciel lisent
#  tous le même endroit (voir `phytoscope/VERSION`).
VERSION_FILE = os.path.join(ROOT, "phytoscope", "VERSION")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.txt")
DIST = os.path.join(ROOT, "dist")

INCLUDE = ["phytoscope", "tests", "tools", "run.py", "Makefile", "make.bat",
           "requirements.txt", "requirements-dev.txt", "pyproject.toml",
           "README.txt", "CHANGELOG.txt", "LICENCE.txt"]
EXCLUDE_DIRS = {"__pycache__", ".venv", ".git", "dist", "build",
                ".pytest_cache", ".ruff_cache"}


# ---------------------------------------------------------------------------
#  Lecture et écriture de version.py
# ---------------------------------------------------------------------------
def read_version() -> dict:
    """Relit `phytoscope/VERSION` — « clé = valeur », une par ligne."""
    valeurs = {}
    with open(VERSION_FILE, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#") or "=" not in ligne:
                continue
            cle, _, valeur = ligne.partition("=")
            valeurs[cle.strip().lower()] = valeur.strip()

    morceaux = valeurs.get("version", "0.0.0").split(".")
    while len(morceaux) < 3:
        morceaux.append("0")
    out = {"major": int(morceaux[0]), "minor": int(morceaux[1]),
           "patch": int(morceaux[2]), "suffix": valeurs.get("suffixe", ""),
           "date": valeurs.get("date", ""), "name": valeurs.get("nom", "")}
    out["string"] = f"{out['major']}.{out['minor']}.{out['patch']}{out['suffix']}"
    return out


def write_version(major: int, minor: int, patch: int, suffix: str,
                  date: str, name: str) -> None:
    """Réécrit `phytoscope/VERSION` en conservant ses commentaires.

    On remplace les valeurs ligne à ligne plutôt que de réécrire le fichier :
    les commentaires expliquent pourquoi ce fichier existe et où il est lu,
    et les perdre à la première publication serait dommage.
    """
    lignes = open(VERSION_FILE, encoding="utf-8").read().splitlines()
    nouvelles = {"version": f"{major}.{minor}.{patch}", "nom": name,
                 "date": date, "suffixe": suffix}
    sortie = []
    for ligne in lignes:
        nu = ligne.strip()
        if nu and not nu.startswith("#") and "=" in nu:
            cle = nu.partition("=")[0].strip().lower()
            if cle in nouvelles:
                sortie.append(f"{cle} = {nouvelles.pop(cle)}".rstrip())
                continue
        sortie.append(ligne)
    #  Une clé absente du fichier est ajoutée plutôt que perdue.
    for cle, valeur in nouvelles.items():
        sortie.append(f"{cle} = {valeur}".rstrip())

    tmp = VERSION_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(sortie) + "\n")
    os.replace(tmp, VERSION_FILE)


# ---------------------------------------------------------------------------
#  Journal des modifications
# ---------------------------------------------------------------------------
HEADER_RE = re.compile(r"^(\d+\.\d+\.\d+[^\s]*)\s+—\s+(\d{4}-\d{2}-\d{2})",
                       re.MULTILINE)


def changelog_has(version: str) -> bool:
    if not os.path.exists(CHANGELOG):
        return False
    return any(m.group(1) == version
               for m in HEADER_RE.finditer(open(CHANGELOG, encoding="utf-8").read()))


def changelog_open_section(version: str, date: str, name: str) -> None:
    """Insère une section vide en tête du journal, à compléter à la main."""
    text = open(CHANGELOG, encoding="utf-8").read() if os.path.exists(CHANGELOG) else ""
    marker = "=" * 78
    section = (f"{version} — {date} « {name} »\n"
               f"{'-' * 78}\n"
               f"  Ajouté\n"
               f"    · (à compléter)\n"
               f"  Modifié\n"
               f"    · (à compléter)\n"
               f"  Corrigé\n"
               f"    · (à compléter)\n\n")
    if marker in text:
        head, rest = text.split(marker, 1)
        rest = rest.lstrip("\n")
        text = head + marker + "\n\n" + section + rest
    else:
        text = section + text
    with open(CHANGELOG, "w", encoding="utf-8") as f:
        f.write(text)


# ---------------------------------------------------------------------------
#  Commandes
# ---------------------------------------------------------------------------
def cmd_show(_args) -> int:
    v = read_version()
    print(f"Version   : {v['string']}")
    print(f"Nom       : {v['name']}")
    print(f"Date      : {v['date']}")
    print(f"Diffusable: {'oui' if not v['suffix'] else 'non (suffixe ' + v['suffix'] + ')'}")
    print(f"Journal   : {'section présente' if changelog_has(v['string']) else 'SECTION MANQUANTE'}")
    return 0


def cmd_bump(args) -> int:
    v = read_version()
    major, minor, patch = v["major"], v["minor"], v["patch"]
    if args.level == "major":
        major, minor, patch = major + 1, 0, 0
    elif args.level == "minor":
        minor, patch = minor + 1, 0
    elif args.level == "patch":
        patch += 1
    suffix = args.suffix or ""
    date = args.date or datetime.date.today().isoformat()
    name = args.name or v["name"]
    version = f"{major}.{minor}.{patch}{suffix}"
    write_version(major, minor, patch, suffix, date, name)
    if not changelog_has(version):
        changelog_open_section(version, date, name)
    print(f"✓ version {v['string']} → {version} « {name} » ({date})")
    print("  Complétez maintenant la section ouverte dans CHANGELOG.txt,")
    print("  puis lancez :  python3 tools/release.py check")
    return 0


def cmd_check(_args) -> int:
    v = read_version()
    problems = []
    if v["suffix"]:
        problems.append(f"la version porte le suffixe « {v['suffix'] } » : "
                        "ce n'est pas une version diffusable")
    if not changelog_has(v["string"]):
        problems.append(f"aucune section {v['string']} dans CHANGELOG.txt")
    for name in ("README.txt", "LICENCE.txt", "CHANGELOG.txt",
                 "requirements.txt"):
        if not os.path.exists(os.path.join(ROOT, name)):
            problems.append(f"fichier manquant : {name}")
    rc = subprocess.call([sys.executable,
                          os.path.join(ROOT, "tools", "check_syntax.py")])
    if rc != 0:
        problems.append("des fichiers Python ne compilent pas")
    if os.path.exists(CHANGELOG):
        body = open(CHANGELOG, encoding="utf-8").read()
        if "(à compléter)" in body.split("=" * 78)[-1][:2000]:
            problems.append("le journal contient encore « (à compléter) »")
    print()
    if problems:
        print("✗ La version n'est pas prête :")
        for p in problems:
            print("   ·", p)
        return 1
    print(f"✓ {v['string']} « {v['name'] } » est prête à être diffusée.")
    return 0


def _walk_files():
    for entry in INCLUDE:
        path = os.path.join(ROOT, entry)
        if os.path.isfile(path):
            yield path
        elif os.path.isdir(path):
            for base, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for f in files:
                    if f.endswith((".pyc", ".pyo", ".log")):
                        continue
                    yield os.path.join(base, f)


def cmd_dist(args) -> int:
    v = read_version()
    os.makedirs(DIST, exist_ok=True)
    stem = f"phytoscope-{v['string']}"
    files = sorted(_walk_files())

    tar_path = os.path.join(DIST, stem + ".tar.gz")
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in files:
            tar.add(f, arcname=os.path.join(stem, os.path.relpath(f, ROOT)))

    zip_path = os.path.join(DIST, stem + ".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, os.path.join(stem, os.path.relpath(f, ROOT)))

    sums = []
    try:
        import hashlib
        for path in (tar_path, zip_path):
            h = hashlib.sha256(open(path, "rb").read()).hexdigest()
            sums.append(f"{h}  {os.path.basename(path)}")
        with open(os.path.join(DIST, stem + ".sha256"), "w",
                  encoding="utf-8") as f:
            f.write("\n".join(sums) + "\n")
    except Exception:                                  # pragma: no cover
        pass

    print(f"✓ {len(files)} fichiers archivés")
    for path in (tar_path, zip_path):
        print(f"  {os.path.relpath(path, ROOT)}  "
              f"({os.path.getsize(path) / 1024:.0f} ko)")
    for s in sums:
        print("  " + s)
    return 0


def cmd_tag(_args) -> int:
    v = read_version()
    tag = "v" + v["string"]
    try:
        subprocess.check_call(["git", "rev-parse", "--git-dir"], cwd=ROOT,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("Ce répertoire n'est pas un dépôt git : aucune étiquette posée.")
        return 0
    message = f"PhytoScope {v['string']} « {v['name']} »"
    rc = subprocess.call(["git", "tag", "-a", tag, "-m", message], cwd=ROOT)
    if rc == 0:
        print(f"✓ étiquette {tag} posée — poussez-la avec : git push origin {tag}")
    return rc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gestion des versions de PhytoScope.")
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("show", help="affiche la version courante").set_defaults(
        func=cmd_show)

    b = sub.add_parser("bump", help="incrémente la version")
    b.add_argument("level", choices=("major", "minor", "patch"))
    b.add_argument("--name", default=None, help="nom de code de la version")
    b.add_argument("--suffix", default="", help="suffixe (-rc1, -dev…)")
    b.add_argument("--date", default=None, help="date au format AAAA-MM-JJ")
    b.set_defaults(func=cmd_bump)

    sub.add_parser("check", help="vérifie que la version est diffusable"
                   ).set_defaults(func=cmd_check)
    sub.add_parser("dist", help="fabrique les archives").set_defaults(func=cmd_dist)
    sub.add_parser("tag", help="pose l'étiquette git").set_defaults(func=cmd_tag)

    args = ap.parse_args(argv)
    if not getattr(args, "func", None):
        ap.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
