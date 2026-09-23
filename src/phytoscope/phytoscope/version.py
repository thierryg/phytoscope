# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/version.py
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

"""Identité et version du logiciel — source unique de vérité.

Ce fichier est le seul endroit où figurent le numéro de version, le nom de
l'auteur et les coordonnées. Tout le reste — la fenêtre « À propos », les
métadonnées des séances enregistrées, l'en-tête des archives de diffusion —
les lit ici. L'outil `tools/release.py` est le seul à écrire dedans.

Numérotation sémantique :

    MAJEUR . MINEUR . CORRECTIF

* **majeur**    : le format des séances enregistrées change, ou une
                  habitude de l'utilisateur est cassée ;
* **mineur**    : nouvelle fonction, format compatible ;
* **correctif** : correction de bogue, aucune fonction nouvelle.

Une version portant le suffixe `-dev` n'est pas une version diffusée.
"""
from __future__ import annotations

import os
from typing import Dict, List, Tuple

# --- Identité ---------------------------------------------------------------
APP_NAME = "PhytoScope"
APP_TAGLINE = "Listen to, measure and record plant signals"

#  Le numéro de version vit dans le fichier `VERSION`, à côté d'ici, et non
#  dans ce module. Motif : la fabrique de paquets, les documents et le
#  logiciel doivent lire le MÊME endroit. Tant que le numéro était écrit en
#  Python, `pyproject.toml` en gardait une copie qui a dérivé pendant cinq
#  versions — elle annonçait encore 1.0.0.
_ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER_VERSION = os.path.join(_ICI, "VERSION")
FICHIER_AUTEURS = os.path.join(_ICI, "AUTHORS")


def lire_fichier_cle_valeur(chemin: str) -> Dict[str, str]:
    """Analyse un fichier « clé = valeur », rien de plus.

    Aucune bibliothèque n'est chargée pour cela, et aucune exception n'en
    sort : un fichier absent ou abîmé ne doit pas empêcher le logiciel de
    démarrer. On retombe alors sur les valeurs de secours, et la fenêtre
    « À propos » affiche « 0.0.0 », ce qui se remarque.
    """
    valeurs: Dict[str, str] = {}
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "=" not in ligne:
                    continue
                cle, _, valeur = ligne.partition("=")
                valeurs[cle.strip().lower()] = valeur.strip()
    except OSError:
        pass
    return valeurs


def lire_le_fichier_version(chemin: str = "") -> Dict[str, str]:
    """Le fichier `VERSION`, analysé."""
    return lire_fichier_cle_valeur(chemin or FICHIER_VERSION)


def lire_le_fichier_auteurs(chemin: str = "") -> Dict[str, str]:
    """Le fichier `AUTHORS`, analysé."""
    return lire_fichier_cle_valeur(chemin or FICHIER_AUTEURS)


_V = lire_le_fichier_version()
_A = lire_le_fichier_auteurs()


def _nombres(texte: str) -> Tuple[int, int, int]:
    morceaux = (texte or "0.0.0").split("-")[0].split(".")
    while len(morceaux) < 3:
        morceaux.append("0")
    try:
        return tuple(int(m) for m in morceaux[:3])           # type: ignore
    except ValueError:                                       # pragma: no cover
        return (0, 0, 0)


VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH = _nombres(_V.get("version", ""))
VERSION_SUFFIX = _V.get("suffixe", "")      # "", "-rc1", "-dev"…

RELEASE_DATE = _V.get("date", "")
RELEASE_NAME = _V.get("nom", "")            # nom de code de la version

#  Deux niveaux d'attribution, et ils ne disent pas la même chose :
#  l'ÉDITEUR est l'atelier qui publie, l'AUTEUR la personne qui a écrit. Les
#  deux viennent du fichier `AUTHORS`, que lisent aussi la fabrique de paquets
#  et la génération du certificat de signature : une seule source, pas de
#  copie à maintenir.
AUTHOR = _A.get("editeur", "Bretagne Namasté")
AUTHOR_NAME = _A.get("auteur", "")
AUTHOR_EMAIL = _A.get("courriel", "")
AUTHOR_PHONE = _A.get("telephone", "")
WEBSITE = _A.get("site", "https://bretagne-namaste.com")
CONTACT = _A.get("contact", "contact@bretagne-namaste.com")
COPYRIGHT = _A.get("droits", "© 2026 Bretagne Namasté")
LICENSE = _A.get("licence", "MIT")
LICENSE_FILE = "LICENSE.txt"

# Matériel de référence décrit par le document compagnon
HARDWARE = "PhytoSense One — révision B"
COMPANION_DOC = "La Carte PhytoSense — conditionnement et interface USB"


# --- Dérivés ----------------------------------------------------------------
VERSION_TUPLE: Tuple[int, int, int] = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)
VERSION = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}{VERSION_SUFFIX}"
FULL_NAME = f"{APP_NAME} {VERSION}"

#  Le titre de la version, tel qu'il s'affiche — et le seul endroit qui
#  décide si le nom de code paraît. Le fichier `VERSION` peut le laisser
#  vide : alors rien n'en paraît, et surtout pas une paire de guillemets
#  vides. Sept endroits composaient cette ligne eux-mêmes ; ils la
#  demandent désormais ici.
TITRE_VERSION = f"{VERSION} « {RELEASE_NAME} »" if RELEASE_NAME else VERSION
FULL_TITLE = f"{APP_NAME} {TITRE_VERSION}"

#  L'attribution complète, telle qu'elle s'affiche et telle qu'elle
#  s'inscrit dans les paquets.
AUTHORS = f"{AUTHOR} — {AUTHOR_NAME}" if AUTHOR_NAME else AUTHOR
MAINTAINER = (f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>" if AUTHOR_NAME and AUTHOR_EMAIL
              else f"{AUTHOR} <{CONTACT}>")


def is_release() -> bool:
    """Vrai si cette version est destinée à être diffusée."""
    return VERSION_SUFFIX == ""


def user_agent() -> str:
    return f"{APP_NAME}/{VERSION} (+{WEBSITE})"


def release_info() -> Dict[str, str]:
    """Tout ce qui identifie cette version, pour les métadonnées de séance."""
    return {
        "application": APP_NAME,
        "version": VERSION,
        "nom_de_version": RELEASE_NAME,
        "date": RELEASE_DATE,
        "auteur": AUTHOR,
        "site": WEBSITE,
        "contact": CONTACT,
        "licence": LICENSE,
        "materiel": HARDWARE,
    }


def dependencies() -> List[Tuple[str, str, str, bool]]:
    """(module, version installée ou « absent », rôle, obligatoire)."""
    import importlib
    rows = [
        ("numpy", "traitement du signal", True),
        ("PySide6", "interface graphique Qt 6", True),
        ("pyqtgraph", "tracés temps réel accélérés", False),
        ("sounddevice", "entrée et sortie audio (PortAudio)", False),
        ("serial", "contrôle de la carte, montages série", False),
        ("rtmidi", "sortie MIDI", False),
        ("pyttsx3", "synthèse vocale du mode Parole", False),
    ]
    out: List[Tuple[str, str, str, bool]] = []
    for name, role, required in rows:
        try:
            mod = importlib.import_module(name)
            version = str(getattr(mod, "__version__", "présent"))
        except Exception:
            version = "absent"
        out.append((name, version, role, required))
    return out


def environment_report() -> str:
    """Rapport copiable-collable, à joindre à un signalement de bogue."""
    import platform
    import sys
    lines = [
        f"{FULL_TITLE} — {RELEASE_DATE}",
        f"{AUTHOR} · {WEBSITE} · {CONTACT}",
        "",
        f"Python     {sys.version.split()[0]}",
        f"Système    {platform.platform()}",
        f"Machine    {platform.machine()}",
        "",
        "Dépendances :",
    ]
    for name, version, role, required in dependencies():
        marque = "!!" if (version == "absent" and required) else \
                 ("--" if version == "absent" else "ok")
        lines.append(f"  [{marque}] {name:<12} {version:<12} {role}")
    return "\n".join(lines)
