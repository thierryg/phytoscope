#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/languages.py
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

"""Les libellés des installateurs, dans onze langues.

Une seule source — `langues/installateur.json` — et deux sorties, parce que
les deux installateurs ne parlent pas le même langage :

* pour le `.run`, un fichier de **variables shell** par langue, que
  l'installateur charge après que l'utilisateur a choisi. Pas de JSON : un
  script `/bin/sh` n'a pas d'analyseur JSON, et en écrire un à coups de `sed`
  serait le plus sûr moyen de casser sur une apostrophe ;
* pour NSIS, un bloc de `LangString`, que `makensis` compile dans l'exécutable.
  NSIS sait afficher lui-même un choix de langue au démarrage — on lui donne
  donc de quoi le remplir.

Pourquoi demander la langue plutôt que la devenir
-------------------------------------------------

La contrainte `C-31` interdit la détection automatique de la locale, et cette
interdiction vaut aussi ici. Une machine dont l'environnement dit `fr_FR`
peut très bien être celle d'un atelier où l'on travaille en anglais ; deviner
produit un logiciel qu'il faut ensuite reconfigurer, et l'installateur est
justement le moment où poser la question coûte le moins cher.

Le choix est **écrit dans les réglages** (`reglages.json`, clé `language`),
que PhytoScope lit à chaque démarrage. L'installateur et le logiciel parlent
donc la même langue sans se concerter.

Usage :
    python3 packaging/languages.py --shell <dossier>   fichiers .sh par langue
    python3 packaging/languages.py --nsis              bloc LangString
    python3 packaging/languages.py --verifier          contrôle le catalogue
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Tuple

ICI = os.path.dirname(os.path.abspath(__file__))
CATALOGUE = os.path.join(ICI, "langues", "installateur.json")

#  Le nom que NSIS donne à chaque langue. Il doit correspondre exactement aux
#  fichiers de `Contrib/Language files` : une faute et `makensis` s'arrête.
NOMS_NSIS = {
    "fr": "French", "en": "English", "es": "Spanish", "pt": "Portuguese",
    "it": "Italian", "id": "Indonesian", "ru": "Russian",
    "zh": "SimpChinese", "ja": "Japanese", "ko": "Korean", "ar": "Arabic",
}

#  Les champs nommés d'un libellé : ils doivent survivre à la traduction.
_CHAMPS = re.compile(r"\{(\w+)\}")


def charger() -> Tuple[List[Dict[str, str]], Dict[str, Dict[str, str]]]:
    """Rend (langues, libellés)."""
    with open(CATALOGUE, encoding="utf-8") as f:
        d = json.load(f)
    return d["_langues"], d["libelles"]


def verifier() -> int:
    """Contrôle la cohérence du catalogue ; rend le nombre de fautes.

    Trois contrôles, et chacun vient d'une faute réelle possible :

    * une langue déclarée mais absente d'un libellé ferait afficher une
      variable vide, donc une ligne blanche ;
    * un `{champ}` perdu à la traduction produirait un texte tronqué là où
      l'installateur croit substituer ;
    * un `{champ}` inventé produirait un `{truc}` affiché tel quel.
    """
    langues, libelles = charger()
    codes = [l["code"] for l in langues]
    fautes = 0

    for cle, traductions in sorted(libelles.items()):
        manquantes = [c for c in codes if not traductions.get(c)]
        if manquantes:
            print(f"  ! {cle} : absent en {', '.join(manquantes)}")
            fautes += 1

        reference = set(_CHAMPS.findall(traductions.get("fr", "")))
        for code in codes:
            if not traductions.get(code):
                continue
            champs = set(_CHAMPS.findall(traductions[code]))
            if champs != reference:
                perdus = reference - champs
                inventes = champs - reference
                detail = []
                if perdus:
                    detail.append("perdus : " + ", ".join(sorted(perdus)))
                if inventes:
                    detail.append("inventés : " + ", ".join(sorted(inventes)))
                print(f"  ! {cle} [{code}] : {' ; '.join(detail)}")
                fautes += 1

    total = len(libelles) * len(codes)
    if fautes == 0:
        print(f"  ✓ {len(libelles)} libellés × {len(codes)} langues "
              f"= {total} traductions, toutes présentes et cohérentes.")
    return fautes


def _echapper_shell(texte: str) -> str:
    """Rend le texte posable entre guillemets doubles dans un script sh.

    Les quatre caractères qui comptent : la barre oblique inverse d'abord —
    sans quoi l'échappement des suivants serait lui-même échappé —, puis le
    guillemet, le dollar et l'accent grave, qui déclencheraient une
    substitution.
    """
    for avant, apres in (("\\", "\\\\"), ('"', '\\"'),
                         ("$", "\\$"), ("`", "\\`")):
        texte = texte.replace(avant, apres)
    return texte


def ecrire_shell(dossier: str) -> List[str]:
    """Un fichier de variables par langue ; rend la liste des fichiers."""
    langues, libelles = charger()
    os.makedirs(dossier, exist_ok=True)
    produits = []

    for langue in langues:
        code = langue["code"]
        chemin = os.path.join(dossier, f"{code}.sh")
        lignes = [
            "#  Libellés de l'installateur PhytoScope — "
            f"{langue['nom']} ({code}).",
            "#",
            "#  FICHIER GÉNÉRÉ par packaging/languages.py — ne pas éditer à la",
            "#  main (C-45). La source est packaging/langues/installateur.json.",
            f"T_LANGUE_CODE=\"{code}\"",
            f"T_LANGUE_NOM=\"{_echapper_shell(langue['nom'])}\"",
            f"T_LANGUE_SENS=\"{langue['direction']}\"",
            "",
        ]
        for cle in sorted(libelles):
            valeur = libelles[cle].get(code) or libelles[cle].get("fr", "")
            lignes.append(f'T_{cle}="{_echapper_shell(valeur)}"')
        lignes.append("")

        with open(chemin, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(lignes))
        produits.append(chemin)

    #  La liste des langues, pour le menu : le code, le nom, dans l'ordre.
    #  L'installateur la lit avant d'avoir choisi, donc avant de pouvoir
    #  charger un catalogue.
    index = os.path.join(dossier, "index.sh")
    with open(index, "w", encoding="utf-8", newline="\n") as f:
        f.write("#  FICHIER GÉNÉRÉ par packaging/languages.py — ne pas éditer.\n")
        f.write("#  Les langues offertes, dans l'ordre d'affichage.\n")
        f.write("LANGUES_CODES=\"" + " ".join(l["code"] for l in langues) + "\"\n")
        for l in langues:
            f.write(f"LANGUE_NOM_{l['code']}=\"{_echapper_shell(l['nom'])}\"\n")
    produits.append(index)
    return produits


def bloc_nsis() -> str:
    """Le bloc `LangString` à insérer dans le script NSIS."""
    langues, libelles = charger()
    lignes = [
        ";  Libellés de l'installateur, en onze langues.",
        ";",
        ";  BLOC GÉNÉRÉ par packaging/languages.py — ne pas éditer à la main",
        ";  (C-45). La source est packaging/langues/installateur.json.",
        ";",
        ";  NSIS affiche lui-même le choix de la langue au démarrage, par",
        ";  MUI_LANGDLL_DISPLAY : ces chaînes le remplissent.",
        "",
    ]
    for langue in langues:
        code = langue["code"]
        nsis = NOMS_NSIS.get(code)
        if not nsis:
            continue
        lignes.append(f'!insertmacro MUI_LANGUAGE "{nsis}"')
    lignes.append("")

    for cle in sorted(libelles):
        for langue in langues:
            code = langue["code"]
            nsis = NOMS_NSIS.get(code)
            if not nsis:
                continue
            valeur = libelles[cle].get(code) or libelles[cle].get("fr", "")
            #  NSIS échappe par `$\"` et veut ses retours à la ligne en `$\r$\n`.
            valeur = (valeur.replace('"', '$\\"')
                            .replace("\n", "$\\r$\\n"))
            lignes.append(f'LangString {cle} ${{LANG_{nsis.upper()}}} "{valeur}"')
        lignes.append("")
    return "\n".join(lignes)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--shell", metavar="DOSSIER",
                   help="écrit un fichier de variables par langue")
    p.add_argument("--nsis", action="store_true",
                   help="écrit le bloc LangString sur la sortie standard")
    p.add_argument("--verifier", action="store_true",
                   help="contrôle la cohérence du catalogue")
    args = p.parse_args(argv)

    if args.verifier or not (args.shell or args.nsis):
        return 1 if verifier() else 0
    if args.shell:
        produits = ecrire_shell(args.shell)
        print(f"  ✓ {len(produits)} fichiers écrits dans {args.shell}")
    if args.nsis:
        print(bloc_nsis())
    return 0


if __name__ == "__main__":
    sys.exit(main())
