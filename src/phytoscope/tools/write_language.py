#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/write_language.py
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

"""Écrit dans les réglages la langue choisie à l'installation.

Les installateurs posent la question au tout début — c'est le moment où elle
coûte le moins cher — et le logiciel lit `ui.language` dans `reglages.json` à
chaque démarrage. Ce petit outil fait le lien, et il est appelé par les
installateurs des trois systèmes.

Pourquoi un fichier à part plutôt que quelques lignes dans chaque
installateur : parce qu'il y en a trois, qu'ils sont écrits en shell, en NSIS
et en AppleScript, et qu'aucun des trois ne sait relire du JSON. Bricoler un
JSON à coups de `sed` ou de `StrCpy` est le plus sûr moyen d'effacer les
réglages de qui s'en sert.

Il **fusionne** : une réinstallation par-dessus une installation existante ne
doit changer que la langue.

Usage :
    python3 tools/write_language.py <code> [<chemin du fichier>]

Sans chemin, il écrit là où le logiciel lit :
`$XDG_CONFIG_HOME/phytoscope/reglages.json` sous Linux,
`%APPDATA%\\PhytoScope\\reglages.json` sous Windows,
`~/Library/Application Support/PhytoScope/reglages.json` sous macOS.
"""
from __future__ import annotations

import json
import os
import sys

#  Which languages the software speaks. Writing an unknown code breaks
#  nothing — the software falls back to its source language — but refusing it
#  at once beats letting the installer believe it succeeded.
#
#  The list is READ FROM DISK rather than written here. A hardcoded copy is a
#  fourth list of languages to keep in step with the other three, and the one
#  that would go stale unnoticed: nothing fails when it is short, the code is
#  simply refused. A catalogue sitting next to this script is the authority.
def langues_connues() -> tuple:
    """The language codes this installation can actually display."""
    ici = os.path.dirname(os.path.abspath(__file__))
    codes = set()
    for base in (ici, os.path.dirname(ici)):
        dossier = os.path.join(base, "phytoscope", "languages")
        if os.path.isdir(dossier):
            codes |= {
                nom[:-5] for nom in os.listdir(dossier) if nom.endswith(".json")
            }
    #  The source language needs no catalogue, so it never appears on disk.
    codes.add("en")
    return tuple(sorted(codes))


def chemin_des_reglages() -> str:
    """Là où le logiciel lit ses réglages, sur ce système-ci."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "PhytoScope", "reglages.json")
    if sys.platform == "darwin":
        return os.path.expanduser(
            "~/Library/Application Support/PhytoScope/reglages.json")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "phytoscope", "reglages.json")


def ecrire(langue: str, chemin: str = "") -> int:
    """Set `ui.language`, touch nothing else, and return an exit status."""
    connues = langues_connues()
    if langue not in connues:
        print(f"unknown language: {langue!r} — expected one of "
              f"{', '.join(connues)}", file=sys.stderr)
        return 2

    chemin = chemin or chemin_des_reglages()
    try:
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
    except OSError as exc:
        print(f"dossier des réglages inaccessible : {exc}", file=sys.stderr)
        return 1

    #  Un fichier illisible ou tronqué est traité comme absent : on préfère
    #  repartir d'un réglage propre plutôt que refuser d'écrire la langue.
    reglages: dict = {}
    try:
        with open(chemin, encoding="utf-8") as f:
            charge = json.load(f)
        if isinstance(charge, dict):
            reglages = charge
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        print(f"réglages existants illisibles ({exc}) — ils seront remplacés",
              file=sys.stderr)

    #  On écrit là où le fichier porte déjà la clé, et sous « ui » par
    #  défaut : c'est ce que le logiciel écrit lui-même.
    if isinstance(reglages.get("ui"), dict):
        reglages["ui"]["language"] = langue
    elif "language" in reglages:
        reglages["language"] = langue
    else:
        reglages.setdefault("ui", {})["language"] = langue

    try:
        #  Écriture en deux temps : un fichier temporaire puis un
        #  remplacement atomique. Une coupure au milieu d'un `json.dump`
        #  laisserait des réglages tronqués, et le logiciel démarrerait sans.
        provisoire = chemin + ".nouveau"
        with open(provisoire, "w", encoding="utf-8") as f:
            json.dump(reglages, f, ensure_ascii=False, indent=2)
        os.replace(provisoire, chemin)
    except OSError as exc:
        print(f"réglages non écrits : {exc}", file=sys.stderr)
        return 1

    print(f"langue = {langue} — {chemin}")
    return 0


def main(argv: list) -> int:
    if len(argv) < 2:
        print(__doc__.strip().split("Usage :")[-1].strip(), file=sys.stderr)
        return 2
    return ecrire(argv[1], argv[2] if len(argv) > 2 else "")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
