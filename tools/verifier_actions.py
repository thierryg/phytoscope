#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/verifier_actions.py
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

"""Contrôle que chaque action référencée par les workflows existe vraiment.

Pourquoi cet outil existe
-------------------------

Deux références du dépôt ne désignaient rien :

    aquasecurity/trivy-action@0.28.0    il fallait « v0.28.0 »
    ossf/scorecard-action@v2            aucune étiquette flottante « v2 »

La première a fait échouer « Analyse de l'arborescence (trivy) » dès
« Set up job », c'est-à-dire **avant** que `continue-on-error: true` ne
puisse s'appliquer : une action qui ne se résout pas n'est pas une étape qui
échoue, c'est un travail qui ne démarre pas. La seconde n'avait pas encore
échoué parce que son workflow ne tourne qu'à l'horaire — elle aurait échoué
la nuit suivante, sans que personne regarde.

Une coquille d'un caractère dans un `uses:` ne se voit ni à la relecture, ni
au `yamllint`, ni à `zizmor` : tous trois lisent le fichier, aucun ne
demande à GitHub si la cible existe. C'est ce que fait cet outil.

Ce qu'il contrôle, et ce qu'il ne contrôle pas
----------------------------------------------

Il résout chaque référence en étiquette, puis en branche, puis en commit. Il
ne dit rien de ce que l'action fait, ni si ses paramètres sont les bons — un
`uses:` valide peut très bien recevoir une entrée qui n'existe plus. Il
répond à une seule question, celle qui vient d'échouer : **cette référence
désigne-t-elle quelque chose ?**

Usage :
    python3 tools/verifier_actions.py            contrôle .github/workflows/
    python3 tools/verifier_actions.py --epingle   exige en plus une empreinte
                                                  de commit pour les actions
                                                  tierces

Sans réseau, l'outil le dit et sort en 0 : il ne doit pas transformer une
coupure de réseau en échec de fabrication. En 1 si une référence est
introuvable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = os.path.join(RACINE, ".github", "workflows")

#  Les actions publiées par GitHub : on les suit par étiquette majeure,
#  comme tout le monde, parce que c'est GitHub qui les signe et que la
#  chaîne d'approvisionnement est la même que celle du coureur.
MAISON = ("actions/", "github/")

#  Une empreinte de commit : quarante caractères hexadécimaux.
EMPREINTE = re.compile(r"^[0-9a-f]{40}$")

#  `uses: proprietaire/depot[/chemin]@reference`, en ignorant les actions
#  locales (« ./.github/... ») et les conteneurs (« docker://... »).
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)")


def references() -> list[tuple[str, str, int]]:
    """(référence, fichier, ligne) pour chaque `uses:` distant."""
    trouvees = []
    for nom in sorted(os.listdir(WORKFLOWS)):
        if not nom.endswith((".yml", ".yaml")):
            continue
        chemin = os.path.join(WORKFLOWS, nom)
        with open(chemin, encoding="utf-8") as f:
            for numero, ligne in enumerate(f, 1):
                trouve = USES.match(ligne)
                if not trouve:
                    continue
                ref = trouve.group(1)
                if ref.startswith(("./", "docker://")) or "@" not in ref:
                    continue
                trouvees.append((ref, nom, numero))
    return trouvees


def _interroger(url: str) -> dict | None:
    """Rend l'objet JSON, ou None sur 404. Lève sur tout le reste."""
    requete = urllib.request.Request(
        url, headers={"Accept": "application/vnd.github+json",
                      "User-Agent": "phytoscope-verifier-actions"})
    #  Dans la CI, le jeton relève la limite de 60 à 1000 appels par heure.
    jeton = os.environ.get("GITHUB_TOKEN")
    if jeton:
        requete.add_header("Authorization", f"Bearer {jeton}")
    try:
        with urllib.request.urlopen(requete, timeout=30) as reponse:
            return json.load(reponse)
    except urllib.error.HTTPError as erreur:
        if erreur.code == 404:
            return None
        raise


def resoudre(reference: str) -> tuple[str, str] | None:
    """(genre, empreinte) si la référence existe, sinon None."""
    chemin, _, ref = reference.partition("@")
    depot = "/".join(chemin.split("/")[:2])
    if EMPREINTE.match(ref):
        #  Une empreinte se vérifie directement : c'est le cas le plus
        #  fréquent depuis qu'on épingle les actions tierces.
        objet = _interroger(f"https://api.github.com/repos/{depot}/commits/{ref}")
        return ("commit", ref) if objet else None
    for genre, chemin_api in (("étiquette", "tags"), ("branche", "heads")):
        objet = _interroger(
            f"https://api.github.com/repos/{depot}/git/ref/{chemin_api}/{ref}")
        if objet:
            return (genre, objet["object"]["sha"])
    return None


def principal(argv: list[str] | None = None) -> int:
    analyseur = argparse.ArgumentParser(
        description="Contrôle que chaque action référencée existe.")
    analyseur.add_argument(
        "--epingle", action="store_true",
        help="exige une empreinte de commit pour les actions tierces")
    args = analyseur.parse_args(argv)

    trouvees = references()
    if not trouvees:
        print("  aucun « uses: » distant — rien à contrôler")
        return 0

    #  Une même action référencée dix fois ne s'interroge qu'une.
    uniques: dict[str, tuple[str, int]] = {}
    for ref, fichier, ligne in trouvees:
        uniques.setdefault(ref, (fichier, ligne))

    introuvables: list[tuple[str, str, int]] = []
    non_epinglees: list[tuple[str, str, int]] = []

    for ref in sorted(uniques):
        fichier, ligne = uniques[ref]
        try:
            issue = resoudre(ref)
        except (urllib.error.URLError, TimeoutError) as erreur:
            print(f"  réseau indisponible ({erreur}) — contrôle abandonné,")
            print("  ce qui n'est pas un échec : voir la docstring.")
            return 0
        if issue is None:
            print(f"  ! {ref}")
            print(f"      introuvable — {fichier}:{ligne}")
            introuvables.append((ref, fichier, ligne))
            continue
        genre, empreinte = issue
        print(f"  · {ref:62s} {genre} {empreinte[:12]}")

        chemin = ref.partition("@")[0]
        tierce = not chemin.startswith(MAISON)
        if args.epingle and tierce and not EMPREINTE.match(ref.partition("@")[2]):
            non_epinglees.append((ref, fichier, ligne))

    if non_epinglees:
        print()
        print("  ! action tierce non épinglée par empreinte de commit :")
        for ref, fichier, ligne in non_epinglees:
            print(f"      {ref}  ({fichier}:{ligne})")
        print("    Une étiquette se déplace ; une empreinte non.")

    if introuvables:
        print()
        print(f"  {len(introuvables)} référence(s) introuvable(s).")
        print("  Attention au « v » : les étiquettes de la plupart des")
        print("  actions en portent un, et une étiquette majeure flottante")
        print("  (« @v2 ») n'existe pas partout.")
        return 1

    if non_epinglees:
        return 1

    print()
    print(f"  ✓ {len(uniques)} référence(s) contrôlée(s), toutes résolues")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
