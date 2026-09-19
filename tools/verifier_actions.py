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
échoue, c'est un travail qui ne démarre pas. Le contrôle de sécurité devient
donc muet sans que rien ne le dise. La seconde n'avait pas encore échoué
parce que son workflow ne tourne qu'à l'horaire.

Une coquille d'un caractère dans un `uses:` ne se voit ni à la relecture, ni
au `yamllint`, ni à `zizmor` : tous trois lisent le fichier, aucun ne
demande à GitHub si la cible existe. C'est ce que fait cet outil.

Pourquoi `git ls-remote` et non l'API GitHub
--------------------------------------------

La première version interrogeait `api.github.com`. Elle a échoué au premier
essai sérieux : **403, limite de requêtes dépassée** — soixante appels par
heure sans jeton, et l'outil en consomme un par référence. Deux
conséquences, l'une gênante et l'autre grave :

  · en local, contrôler seize références épuisait le quart du quota horaire
    de la machine, partagé avec tout le reste ;
  · en intégration, cette étape est délibérément **non tolérante** — c'est
    la seule du travail qui peut refuser une fusion. Un 403 n'était pas
    rattrapé (seuls `URLError` et `TimeoutError` l'étaient) : une limite de
    quota aurait bloqué une fusion pour une raison étrangère aux workflows.

`git ls-remote` répond à la même question, **sans quota, sans jeton et sans
compte** : le protocole d'annonce des références est public. Un appel par
dépôt, treize au lieu de seize, et rien à réarmer.

Ce que le changement a permis de gagner
---------------------------------------

`ls-remote` donne toutes les étiquettes d'un coup, là où l'API répondait
étiquette par étiquette. On peut donc contrôler une chose que l'API ne
donnait pas : que l'empreinte épinglée soit **bien celle de la version
annoncée en commentaire**. Sans cela, `@abc123… # v2.6.2` peut désigner
n'importe quoi, et le commentaire ment sans que personne le sache.

Pour une étiquette annotée, `ls-remote` publie deux lignes — l'objet
étiquette, puis l'empreinte du commit sous `^{}`. C'est la seconde qu'on
épingle, et c'est celle que compare cet outil.

Ce qu'il ne contrôle pas
------------------------

Rien de ce que l'action fait, ni si ses paramètres sont les bons — un `uses:`
valide peut recevoir une entrée qui n'existe plus. Il répond à une seule
question, celle qui a échoué : **cette référence désigne-t-elle quelque
chose, et dit-elle la vérité ?**

Usage :
    python3 tools/verifier_actions.py            contrôle .github/workflows/
    python3 tools/verifier_actions.py --epingle   exige en plus une empreinte
                                                  de commit pour les actions
                                                  tierces

Sans réseau, l'outil le dit et sort en 0 : il ne doit pas transformer une
coupure en échec de fabrication. En 1 si une référence est introuvable, si
un commentaire de version est démenti par l'empreinte, ou si `--epingle` est
demandé et qu'une action tierce flotte.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOWS = os.path.join(RACINE, ".github", "workflows")

#  Les actions publiées par GitHub : on les suit par étiquette majeure,
#  comme tout le monde, parce que c'est GitHub qui les signe et que la
#  chaîne d'approvisionnement est celle du coureur lui-même.
MAISON = ("actions/", "github/")

#  Une empreinte de commit : quarante caractères hexadécimaux.
EMPREINTE = re.compile(r"^[0-9a-f]{40}$")

#  `uses: proprietaire/depot[/chemin]@reference`, et le commentaire qui suit
#  s'il y en a un — c'est lui qui dit la version en clair.
USES = re.compile(r"^\s*(?:-\s+)?uses:\s*(?P<ref>[^\s#]+)"
                  r"(?:\s*#\s*(?P<note>.*))?")

#  « v0.36.0 » ou « 0.36.0 » dans le commentaire.
VERSION_NOTEE = re.compile(r"\b(v?\d+(?:\.\d+)+)\b")


def references() -> list[tuple[str, str, str, int]]:
    """(référence, commentaire, fichier, ligne) pour chaque `uses:` distant."""
    trouvees = []
    for nom in sorted(os.listdir(WORKFLOWS)):
        if not nom.endswith((".yml", ".yaml")):
            continue
        with open(os.path.join(WORKFLOWS, nom), encoding="utf-8") as f:
            for numero, ligne in enumerate(f, 1):
                trouve = USES.match(ligne)
                if not trouve:
                    continue
                ref = trouve.group("ref")
                if ref.startswith(("./", "docker://")) or "@" not in ref:
                    continue
                trouvees.append((ref, trouve.group("note") or "", nom, numero))
    return trouvees


class ReseauMuet(Exception):
    """Le dépôt distant n'a pas répondu — ce n'est pas un échec de contrôle."""


def annonces(depot: str) -> dict[str, str]:
    """Les références publiées par un dépôt : {nom de référence: empreinte}.

    Un seul appel par dépôt. Les étiquettes annotées apparaissent deux fois,
    la seconde suffixée `^{}` et portant l'empreinte du commit : c'est celle
    qu'on épingle.
    """
    url = f"https://github.com/{depot}"
    try:
        issue = subprocess.run(
            ["git", "ls-remote", "--heads", "--tags", url],
            capture_output=True, text=True, timeout=60,
            #  Un dépôt privé ou inexistant ferait autrement attendre une
            #  invite de mot de passe, indéfiniment, dans la CI.
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0",
                 "GIT_ASKPASS": "", "GCM_INTERACTIVE": "never"})
    except FileNotFoundError as erreur:
        raise ReseauMuet(f"git introuvable ({erreur})") from erreur
    except subprocess.TimeoutExpired as erreur:
        raise ReseauMuet(f"{depot} : délai dépassé") from erreur

    if issue.returncode != 0:
        detail = (issue.stderr or "").strip().splitlines()
        premier = detail[-1] if detail else f"code {issue.returncode}"
        #  Un dépôt qui n'existe pas se distingue d'un réseau coupé : le
        #  premier est un défaut du dépôt, le second non.
        if "not found" in premier.lower() or "repository" in premier.lower():
            return {}
        raise ReseauMuet(f"{depot} : {premier}")

    publiees = {}
    for ligne in issue.stdout.splitlines():
        empreinte, _, nom = ligne.partition("\t")
        if nom:
            publiees[nom.strip()] = empreinte.strip()
    return publiees


def resoudre(reference: str, publiees: dict[str, str]) -> tuple[str, str] | None:
    """(genre, empreinte) si la référence existe, sinon None."""
    version = reference.partition("@")[2]

    if EMPREINTE.match(version):
        #  Une empreinte épinglée : on la cherche parmi celles annoncées.
        #  Elle doit être la cible d'une étiquette ou d'une branche — un
        #  commit quelconque de l'historique ne se vérifie pas ainsi, et
        #  épingler autre chose qu'une version publiée n'aurait pas de sens.
        noms = [nom.replace("refs/tags/", "").replace("refs/heads/", "")
                       .removesuffix("^{}")
                for nom, empreinte in publiees.items() if empreinte == version]
        if not noms:
            return None
        #  Plusieurs étiquettes désignent souvent le même commit : « v2 » et
        #  « v2.3.9 » par exemple. On annonce la plus précise, sans quoi le
        #  compte rendu dit « v2 » pour une empreinte épinglée sur v2.3.9 et
        #  laisse croire à un flottement.
        return ("commit", max(noms, key=lambda n: (n.count("."), len(n))))

    for prefixe, genre in (("refs/tags/", "étiquette"),
                           ("refs/heads/", "branche")):
        #  Pour une étiquette annotée, l'empreinte du commit est sous `^{}`.
        pele = publiees.get(f"{prefixe}{version}^{{}}")
        brute = publiees.get(f"{prefixe}{version}")
        if pele or brute:
            return (genre, pele or brute or "")
    return None


def note_tenue(reference: str, note: str,
               publiees: dict[str, str]) -> str | None:
    """La version annoncée en commentaire correspond-elle à l'empreinte ?

    Rend None si tout va bien, sinon ce qui ne colle pas. Un commentaire
    absent n'est pas traité ici : c'est l'affaire des essais hors ligne.
    """
    version = reference.partition("@")[2]
    if not EMPREINTE.match(version) or not note:
        return None
    dite = VERSION_NOTEE.search(note)
    if not dite:
        return None
    etiquette = dite.group(1)
    candidates = [etiquette] if etiquette.startswith("v") else \
                 [f"v{etiquette}", etiquette]
    for nom in candidates:
        attendue = (publiees.get(f"refs/tags/{nom}^{{}}")
                    or publiees.get(f"refs/tags/{nom}"))
        if attendue is None:
            continue
        if attendue != version:
            return (f"le commentaire annonce {nom}, qui est "
                    f"{attendue[:12]}… et non {version[:12]}…")
        return None
    return f"le commentaire annonce {etiquette}, qui n'est pas une étiquette"


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

    #  Une même action référencée dix fois ne s'interroge qu'une, et un même
    #  dépôt ne s'annonce qu'une fois quelles que soient ses actions.
    uniques: dict[str, tuple[str, str, int]] = {}
    for ref, note, fichier, ligne in trouvees:
        uniques.setdefault(ref, (note, fichier, ligne))

    cache: dict[str, dict[str, str]] = {}
    introuvables: list[str] = []
    menteuses: list[str] = []
    flottantes: list[str] = []

    for ref in sorted(uniques):
        note, fichier, ligne = uniques[ref]
        depot = "/".join(ref.partition("@")[0].split("/")[:2])
        if depot not in cache:
            try:
                cache[depot] = annonces(depot)
            except ReseauMuet as erreur:
                print(f"  réseau indisponible ({erreur}) — contrôle")
                print("  abandonné, ce qui n'est pas un échec : voir la")
                print("  docstring de cet outil.")
                return 0
        publiees = cache[depot]

        issue = resoudre(ref, publiees)
        if issue is None:
            print(f"  ! {ref}")
            print(f"      introuvable — {fichier}:{ligne}")
            introuvables.append(f"{fichier}:{ligne} — {ref}")
            continue
        genre, precision = issue
        print(f"  · {ref:62s} {genre} {precision}")

        souci = note_tenue(ref, note, publiees)
        if souci:
            print(f"      ! {souci}")
            menteuses.append(f"{fichier}:{ligne} — {souci}")

        tierce = not ref.partition("@")[0].startswith(MAISON)
        if args.epingle and tierce and not EMPREINTE.match(ref.partition("@")[2]):
            flottantes.append(f"{fichier}:{ligne} — {ref}")

    if flottantes:
        print()
        print("  ! action(s) tierce(s) non épinglée(s) par empreinte :")
        for quoi in flottantes:
            print(f"      {quoi}")
        print("    Une étiquette se déplace ; une empreinte non.")

    if menteuses:
        print()
        print("  ! commentaire(s) de version démenti(s) par l'empreinte :")
        for quoi in menteuses:
            print(f"      {quoi}")
        print("    Un commentaire faux est pire qu'aucun commentaire.")

    if introuvables:
        print()
        print(f"  {len(introuvables)} référence(s) introuvable(s) :")
        for quoi in introuvables:
            print(f"      {quoi}")
        print("    Attention au « v » : les étiquettes de la plupart des")
        print("    actions en portent un, et une étiquette majeure")
        print("    flottante (« @v2 ») n'existe pas partout.")

    if introuvables or menteuses or flottantes:
        return 1

    print()
    print(f"  ✓ {len(uniques)} référence(s) contrôlée(s) sur "
          f"{len(cache)} dépôt(s), toutes résolues")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
