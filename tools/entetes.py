#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/entetes.py
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

"""Pose et tient à jour l'en-tête d'attribution de chaque fichier source.

Version, date, auteur, éditeur, licence, site : la même chose en tête de tous
les fichiers du dépôt, quel que soit leur langage. Un fichier qui voyage seul —
recopié dans un forum, joint à un courriel, retrouvé sur une clé dix ans plus
tard — doit dire d'où il vient et à quelles conditions on peut s'en servir.

D'où viennent les valeurs
-------------------------

**De nulle part ailleurs que des fichiers de référence** :

* ``src/phytoscope/phytoscope/VERSION`` — la version et sa date ;
* ``src/phytoscope/phytoscope/AUTEURS`` — l'éditeur, l'auteur, le site.

Les mêmes que lit le logiciel pour sa fenêtre « À propos » et la fabrique de
paquets pour estampiller le ``.deb``. Une troisième copie ici finirait par
diverger, comme la version de ``pyproject.toml`` a divergé pendant cinq
versions.

Deux licences, et c'est voulu
-----------------------------

``C-53`` : le logiciel et le micrologiciel sont sous **MIT**, le matériel sous
**CERN-OHL-P v2**. L'outil le sait : un fichier sous ``hardware/``
reçoit la seconde. Écrire MIT sur un plan de circuit serait faux, et un jour
quelqu'un s'en servirait en le croyant.

Comment l'outil reste sûr
-------------------------

**Il est idempotent.** L'en-tête est délimité par deux marques ; le relancer
remplace l'ancien au lieu d'en empiler un second. C'est ce qui permet de
l'exécuter à chaque publication.

**Il respecte ce qui doit venir en premier.** Un ``#!`` reste en première
ligne, une déclaration d'encodage en deuxième — sans quoi Python et le shell
cesseraient de fonctionner. L'en-tête vient après, et avant la docstring.

**Il ne réécrit rien qu'il ne sache relire.** Chaque fichier modifié est
recompilé (Python) ou revérifié (shell) avant d'être écrit. Un fichier qu'on
ne sait pas valider n'est pas touché.

**Il n'écrit rien sans qu'on le demande.** Par défaut il montre ce qu'il
ferait ; ``--ecrire`` applique.

.. code-block:: console

    python3 tools/entetes.py                 ce qui serait changé
    python3 tools/entetes.py --ecrire        appliquer
    python3 tools/entetes.py --verifier      échoue s'il en manque (intégration)
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGICIEL = os.path.join(RACINE, "src", "phytoscope")
FICHIER_VERSION = os.path.join(LOGICIEL, "phytoscope", "VERSION")
FICHIER_AUTEURS = os.path.join(LOGICIEL, "phytoscope", "AUTEURS")

#  Les marques qui délimitent l'en-tête. Sans elles, on ne saurait pas
#  distinguer notre bloc d'un commentaire écrit par quelqu'un, et relancer
#  l'outil empilerait les en-têtes.
DEBUT = "PhytoScope — attribution"
FIN = "fin de l'attribution"

#  Ce qu'on ne touche pas, et pourquoi.
EXCLUS = (
    ".venv", "__pycache__", ".git", ".pytest_cache", ".ruff_cache",
    "build/paquets",            # produits, régénérés à chaque fabrication
    "build/",                   # idem
    "pico-sdk",                 # le SDK de Raspberry Pi : pas notre code
    #  Le code TIERS ne reçoit JAMAIS notre en-tête. Poser « © Bretagne
    #  Namasté » et « SPDX-License-Identifier: MIT » sur le micrologiciel
    #  Biotron, qui est en GPL-3.0, était une fausse déclaration de licence ;
    #  sur LEDFader et MIDI Sprout, une fausse déclaration de paternité. Les
    #  32 fichiers concernés ont été rendus à leur en-tête d'origine le
    #  2026-09-18. Chaque projet garde sa licence : voir sources/schemas/LISEZ-MOI.md.
    "sources/schemas",
    "sources/code",             # archives de dépôts tiers
    "sources/software",         # idem
    ".ecarte",                  # doublons et environnements mis à l'écart
    "references",               # documents sous droits, hors dépôt
    "LICENSES",                 # textes de licence officiels, non modifiables
    "site-packages", "node_modules", "dist",
)

#  Les fichiers qui ne doivent surtout pas recevoir d'en-tête.
NOMS_EXCLUS = {
    "VERSION", "AUTEURS",       # fichiers de données, lus par analyse stricte
    "LICENCE.txt", "LICENSE",
    "pico_sdk_import.cmake",    # recopié du SDK à chaque construction
    #  Un fichier « control » Debian n'admet AUCUN commentaire : dpkg-deb
    #  refuse le paquet avec « field name '#' must be followed by colon ».
    #  L'en-tête y a été posé une fois, le 2026-09-18, et le .deb a disparu
    #  de la fabrication sans que rien d'autre ne le signale.
    "control",
    #  Même raison, autres formats à en-tête strict : la première ligne est
    #  imposée et ne peut pas être un commentaire.
    "SHA256SUMS.txt",
}


# ---------------------------------------------------------------------------
#  D'où viennent les valeurs
# ---------------------------------------------------------------------------
def lire_cle_valeur(chemin: str) -> Dict[str, str]:
    valeurs: Dict[str, str] = {}
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "=" not in ligne:
                    continue
                cle, _, valeur = ligne.partition("=")
                valeurs[cle.strip().lower()] = valeur.strip()
    except OSError as exc:
        print(f"✗ {chemin} illisible : {exc}", file=sys.stderr)
    return valeurs


@dataclass
class Identite:
    version: str = "0.0.0"
    date: str = ""
    editeur: str = "Bretagne Namasté"
    auteur: str = ""
    courriel: str = ""
    contact: str = ""
    site: str = ""

    @classmethod
    def lire(cls) -> "Identite":
        v = lire_cle_valeur(FICHIER_VERSION)
        a = lire_cle_valeur(FICHIER_AUTEURS)
        return cls(
            version=v.get("version", "0.0.0") + v.get("suffixe", ""),
            date=v.get("date", ""),
            editeur=a.get("editeur", "Bretagne Namasté"),
            auteur=a.get("auteur", ""),
            courriel=a.get("courriel", ""),
            contact=a.get("contact", ""),
            site=a.get("site", ""))


#  Les deux licences du projet (`C-53`).
LICENCES = {
    "MIT": ("MIT", "MIT"),
    "CERN": ("CERN-OHL-P v2", "CERN-OHL-P-2.0"),
}


def licence_de(chemin: str) -> Tuple[str, str]:
    """MIT partout, sauf le matériel — qui est sous CERN-OHL-P v2 (`C-53`)."""
    relatif = os.path.relpath(chemin, RACINE).replace(os.sep, "/")
    if relatif.startswith("hardware/"):
        return LICENCES["CERN"]
    return LICENCES["MIT"]


# ---------------------------------------------------------------------------
#  Les styles de commentaire
# ---------------------------------------------------------------------------
@dataclass
class Style:
    """Comment commenter dans ce langage, et ce qui doit rester en tête."""
    ouvrir: str = ""
    prefixe: str = "#  "
    fermer: str = ""
    #  Les lignes qui doivent impérativement précéder l'en-tête : un `#!` en
    #  deuxième ligne n'est plus un `#!`, et Python ne lit la déclaration
    #  d'encodage que dans les deux premières lignes.
    garder_en_tete: Tuple[re.Pattern, ...] = ()


DIESE = Style(garder_en_tete=(re.compile(r"^#!"),
                              re.compile(r"^#.*coding[:=]")))
C = Style(ouvrir="/*", prefixe=" *  ", fermer=" */")
XML = Style(ouvrir="<!--", prefixe="  ", fermer="-->",
            garder_en_tete=(re.compile(r"^<\?xml"),))
POINT_VIRGULE = Style(prefixe=";  ")

STYLES: Dict[str, Style] = {
    ".py": DIESE, ".sh": DIESE, ".bash": DIESE, ".cmake": DIESE,
    ".toml": DIESE, ".cfg": DIESE, ".yml": DIESE, ".yaml": DIESE,
    ".spec": DIESE, ".desktop": DIESE, ".mk": DIESE,
    ".c": C, ".h": C, ".cpp": C, ".hpp": C, ".css": C,
    ".wxs": XML, ".xml": XML, ".plist": XML, ".svg": XML,
    ".nsi": POINT_VIRGULE,
}
#  Les fichiers sans extension, reconnus par leur nom.
PAR_NOM: Dict[str, Style] = {
    "Makefile": DIESE, "makefile": DIESE, "GNUmakefile": DIESE,
    "CMakeLists.txt": DIESE, "control": DIESE, "postinst": DIESE,
    "prerm": DIESE, "lanceur": DIESE, "postinstall": DIESE,
}
#  `.bat` et `.cmd` : « rem » plutôt que « # », et pas d'accents — une console
#  Windows en cp850 les rendrait illisibles.
LOT = Style(prefixe="rem  ")
STYLES[".bat"] = LOT
STYLES[".cmd"] = LOT


def sans_accents(texte: str) -> str:
    """Le texte réduit à l'ASCII — la forme que reçoivent les `.bat`.

    Sert deux fois : à écrire l'en-tête de ces fichiers, et à le *retrouver*
    ensuite. Sans cette seconde lecture, la marque « PhytoScope — attribution »
    posée sans son tiret cadratin n'était plus reconnue, et chaque exécution
    empilait un en-tête de plus.
    """
    return "".join(c for c in unicodedata.normalize("NFKD", texte)
                   if not unicodedata.combining(c) and c.isascii())


def style_de(chemin: str) -> Optional[Style]:
    nom = os.path.basename(chemin)
    if nom in PAR_NOM:
        return PAR_NOM[nom]
    return STYLES.get(os.path.splitext(nom)[1].lower())


# ---------------------------------------------------------------------------
#  Fabriquer l'en-tête
# ---------------------------------------------------------------------------
def entete(chemin: str, id_: Identite, style: Style) -> str:
    """Le bloc d'attribution, mis en forme pour ce langage."""
    licence, spdx = licence_de(chemin)
    relatif = os.path.relpath(chemin, RACINE).replace(os.sep, "/")
    sans_accent = style.prefixe.startswith("rem")

    def net(texte: str) -> str:
        return texte if not sans_accent else sans_accents(texte)

    #  Le numéro seul, sans le nom de code : l'en-tête sert à identifier une
    #  révision, et un nom de code ne l'identifie pas — il vit dans le journal
    #  des versions et dans « À propos », où il a du sens.
    lignes = [
        f"{DEBUT} — {relatif}",
        "",
        f"Version  : {id_.version}",
        f"Date     : {id_.date}",
        f"Éditeur  : {id_.editeur}",
    ]
    if id_.auteur:
        auteur = id_.auteur + (f" <{id_.courriel}>" if id_.courriel else "")
        lignes.append(f"Auteur   : {auteur}")
    lignes += [
        f"Site     : {id_.site}",
        f"Contact  : {id_.contact}",
        f"Licence  : {licence} — voir LICENCE.txt",
        "",
        f"SPDX-License-Identifier: {spdx}",
        FIN,
    ]

    barre = "=" * 74
    corps = [style.prefixe.rstrip() if not l else style.prefixe + net(l)
             for l in lignes]
    bloc = ([style.prefixe + barre] + corps + [style.prefixe + barre])
    if style.ouvrir:
        bloc = [style.ouvrir] + bloc + [style.fermer]
    return "\n".join(bloc) + "\n"


# ---------------------------------------------------------------------------
#  Poser l'en-tête
# ---------------------------------------------------------------------------
def retirer_ancien(lignes: List[str], style: Style) -> List[str]:
    """Retire les en-têtes déjà posés, pour les remplacer.

    C'est ce qui rend l'outil idempotent : sans cela, chaque exécution
    ajouterait un bloc de plus. On boucle — et l'on n'en retire pas qu'un —
    afin de réparer les fichiers où un tel empilement a déjà eu lieu.
    """
    while True:
        reduites = _retirer_un(lignes, style)
        if reduites is None:
            return lignes
        lignes = reduites


def _retirer_un(lignes: List[str], style: Style) -> Optional[List[str]]:
    """Le premier en-tête ôté, ou None s'il n'y en a plus."""
    #  Comparaison sans accents : dans un `.bat`, la marque a été écrite en
    #  ASCII et ne contient plus son tiret cadratin.
    marque = sans_accents(DEBUT)
    debut = fin = None
    for i, ligne in enumerate(lignes[:40]):
        nette = sans_accents(ligne)
        if marque in nette and debut is None:
            debut = i
        elif FIN in nette and debut is not None:
            fin = i
            break
    if debut is None or fin is None:
        return None

    def encadrement(ligne: str) -> bool:
        """La ligne habille-t-elle l'en-tête — une barre, un délimiteur ?

        Les délimiteurs de bloc (`<!--`, `*/`) comptent : oubliés, ils
        restaient dans le fichier en commentaire vide à chaque exécution.
        """
        nue = ligne.strip()
        if not nue:
            return False
        if style.ouvrir and nue in (style.ouvrir.strip(), style.fermer.strip()):
            return True
        return set(nue) <= set("#=* /;rem")

    #  Étendre aux barres et aux délimiteurs de bloc qui encadrent.
    while debut > 0 and encadrement(lignes[debut - 1]):
        debut -= 1
    apres = fin + 1
    while apres < len(lignes) and encadrement(lignes[apres]):
        apres += 1
    apres = _sauter_blocs_vides(lignes, apres, style)
    #  La ligne vide qui suivait l'en-tête part avec lui.
    if apres < len(lignes) and not lignes[apres].strip():
        apres += 1
    return lignes[:debut] + lignes[apres:]


def _sauter_blocs_vides(lignes: List[str], depart: int, style: Style) -> int:
    """Ramasse les commentaires vides laissés par l'ancien défaut.

    Un `<!--` suivi d'un `-->` et de rien d'autre : c'est ce que produisait
    une suppression qui ne savait pas reconnaître les délimiteurs de bloc.
    On les efface au passage plutôt que par une réparation à la main.
    """
    if not style.ouvrir:
        return depart
    i = depart
    while True:
        j = i
        while j < len(lignes) and not lignes[j].strip():
            j += 1
        if (j + 1 < len(lignes)
                and lignes[j].strip() == style.ouvrir.strip()
                and lignes[j + 1].strip() == style.fermer.strip()):
            i = j + 2
        else:
            return i


def poser(chemin: str, id_: Identite) -> Optional[str]:
    """Rend le contenu du fichier avec son en-tête, ou None s'il est déjà bon."""
    style = style_de(chemin)
    if style is None:
        return None
    try:
        with open(chemin, encoding="utf-8") as f:
            original = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    lignes = original.split("\n")
    lignes = retirer_ancien(lignes, style)

    #  Ce qui doit rester en première place : `#!`, déclaration d'encodage,
    #  déclaration XML.
    tete: List[str] = []
    reste = lignes
    for motif in style.garder_en_tete:
        if reste and motif.match(reste[0]):
            tete.append(reste[0])
            reste = reste[1:]

    #  Une ligne vide entre l'en-tête et la suite, sauf si la suite en a déjà.
    suite = reste
    while suite and not suite[0].strip():
        suite = suite[1:]

    neuf = "\n".join(tete) + ("\n" if tete else "")
    neuf += entete(chemin, id_, style) + "\n" + "\n".join(suite)
    if not neuf.endswith("\n"):
        neuf += "\n"
    return None if neuf == original else neuf


def relisible(chemin: str, contenu: str) -> bool:
    """Le fichier modifié se relit-il ? On n'écrit pas ce qu'on casse."""
    extension = os.path.splitext(chemin)[1].lower()
    if extension == ".py":
        try:
            compile(contenu, chemin, "exec")
            return True
        except SyntaxError as exc:
            print(f"    ✗ {os.path.relpath(chemin, RACINE)} : {exc}",
                  file=sys.stderr)
            return False
    if extension in (".sh", ".bash") or os.path.basename(chemin) in (
            "postinst", "prerm", "lanceur", "postinstall"):
        try:
            r = subprocess.run(["sh", "-n", "-"], input=contenu.encode(),
                               capture_output=True, timeout=30)
            #  Un script auto-extractible contient une archive binaire après
            #  son en-tête : `sh -n` s'y étrangle, ce qui est normal.
            if r.returncode != 0 and b"@@CHARGE@@" not in contenu.encode():
                message = r.stderr.decode("utf-8", "replace").strip()
                if "unexpected" in message and len(contenu) > 200_000:
                    return True          # une charge binaire, pas une faute
                print(f"    ✗ {os.path.relpath(chemin, RACINE)} : {message}",
                      file=sys.stderr)
                return False
        except (OSError, subprocess.TimeoutExpired):
            pass
    return True


# ---------------------------------------------------------------------------
#  Parcourir le dépôt
# ---------------------------------------------------------------------------
def a_traiter() -> List[str]:
    trouves: List[str] = []
    for dossier, sous, fichiers in os.walk(RACINE):
        relatif = os.path.relpath(dossier, RACINE).replace(os.sep, "/")
        if any(x in relatif + "/" for x in EXCLUS):
            sous[:] = []
            continue
        sous[:] = [d for d in sorted(sous)
                   if not any(x in d for x in EXCLUS)]
        for nom in sorted(fichiers):
            if nom in NOMS_EXCLUS:
                continue
            chemin = os.path.join(dossier, nom)
            if style_de(chemin) is not None:
                trouves.append(chemin)
    return trouves


def main(argv: Optional[Sequence[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="entetes.py",
        description="Pose l'en-tête d'attribution sur tous les fichiers source.")
    p.add_argument("--ecrire", action="store_true",
                   help="appliquer ; sans cette option, on montre seulement")
    p.add_argument("--verifier", action="store_true",
                   help="échouer s'il manque un en-tête (intégration continue)")
    p.add_argument("--seulement", default="", metavar="MOTIF",
                   help="ne traiter que les chemins contenant ce texte")
    args = p.parse_args(argv)

    id_ = Identite.lire()
    print(f"\n  PhytoScope {id_.version} — en-têtes d'attribution")
    print(f"  {id_.editeur} · {id_.auteur} · {id_.site}\n")

    fichiers = [f for f in a_traiter()
                if not args.seulement or args.seulement in f]
    a_changer: List[Tuple[str, str]] = []
    refuses = 0
    for chemin in fichiers:
        neuf = poser(chemin, id_)
        if neuf is None:
            continue
        if not relisible(chemin, neuf):
            refuses += 1
            continue
        a_changer.append((chemin, neuf))

    par_type: Dict[str, int] = {}
    for chemin, _ in a_changer:
        cle = os.path.splitext(chemin)[1].lower() or os.path.basename(chemin)
        par_type[cle] = par_type.get(cle, 0) + 1

    if args.verifier:
        if a_changer:
            print(f"  ✗ {len(a_changer)} fichier(s) sans en-tête à jour :")
            for chemin, _ in a_changer[:20]:
                print(f"      {os.path.relpath(chemin, RACINE)}")
            if len(a_changer) > 20:
                print(f"      … et {len(a_changer) - 20} autres")
            print("\n      python3 tools/entetes.py --ecrire\n")
            return 1
        print(f"  ✓ {len(fichiers)} fichiers, tous à jour.\n")
        return 0

    if not a_changer:
        print(f"  ✓ {len(fichiers)} fichiers examinés, tous déjà à jour.\n")
        return 0

    for cle, n in sorted(par_type.items(), key=lambda kv: -kv[1]):
        print(f"    {cle:<14} {n:>4}")
    print(f"\n  {len(a_changer)} fichier(s) à mettre à jour "
          f"sur {len(fichiers)} examinés.")
    if refuses:
        print(f"  {refuses} écarté(s) : le résultat ne se relisait pas.")

    if not args.ecrire:
        print("\n  Rien n'a été écrit. Pour appliquer :")
        print("      python3 tools/entetes.py --ecrire\n")
        return 0

    for chemin, neuf in a_changer:
        with open(chemin, "w", encoding="utf-8", newline="\n") as f:
            f.write(neuf)
    print(f"\n  ✓ {len(a_changer)} fichier(s) écrits.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
