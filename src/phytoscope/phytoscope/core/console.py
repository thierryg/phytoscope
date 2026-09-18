# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/console.py
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

"""Sortie console colorisée — lisible, et neutralisée quand il le faut.

La couleur aide vraiment quand il s'agit de repérer une dépendance manquante
dans vingt lignes de diagnostic. Elle nuit dès qu'on redirige la sortie dans
un fichier ou qu'on la relit dans un journal.

Les conventions respectées ici sont celles qu'attendent les utilisateurs de
terminal :

* pas de couleur si la sortie n'est pas un terminal ;
* pas de couleur si la variable d'environnement ``NO_COLOR`` est définie
  (norme no-color.org) ;
* couleur forcée si ``FORCE_COLOR`` ou ``CLICOLOR_FORCE`` est définie ;
* activation du mode ANSI sous Windows 10 et suivants.
"""
from __future__ import annotations

import os
import sys
from typing import Optional

# --- Séquences ANSI ---------------------------------------------------------
RESET = "\033[0m"
GRAS = "\033[1m"
ESTOMPE = "\033[2m"
ITALIQUE = "\033[3m"
SOULIGNE = "\033[4m"

NOIR, ROUGE, VERT, JAUNE = "\033[30m", "\033[31m", "\033[32m", "\033[33m"
BLEU, MAGENTA, CYAN, BLANC = "\033[34m", "\033[35m", "\033[36m", "\033[37m"
VERT_CLAIR, JAUNE_CLAIR = "\033[92m", "\033[93m"
ROUGE_CLAIR, CYAN_CLAIR = "\033[91m", "\033[96m"
GRIS = "\033[90m"


def _couleur_active() -> bool:
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") or os.environ.get("CLICOLOR_FORCE"):
        return True
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    if sys.platform.startswith("win"):
        return _activer_ansi_windows()
    return os.environ.get("TERM", "") not in ("", "dumb")


def _activer_ansi_windows() -> bool:                   # pragma: no cover
    """Active les séquences ANSI sans écraser le reste du mode console.

    L'ancienne version posait la valeur 7 d'autorité, ce qui remettait à zéro
    tous les autres bits du mode — l'écho et le traitement de ligne compris.
    On lit donc le mode courant et l'on n'ajoute que le bit voulu.
    """
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        poignee = kernel32.GetStdHandle(-11)           # STD_OUTPUT_HANDLE
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(poignee, ctypes.byref(mode)):
            return False
        VIRTUEL = 0x0004       # ENABLE_VIRTUAL_TERMINAL_PROCESSING
        return bool(kernel32.SetConsoleMode(poignee, mode.value | VIRTUEL))
    except Exception:
        return False


def forcer_utf8() -> None:
    """Écrire en UTF-8 sur la sortie standard, quel que soit le système.

    Dans une vraie console Windows, Python passe par l'API UTF-16 et les
    caractères « ✓ », « ─ » ou « µ » s'affichent. Mais **dès que la sortie est
    redirigée** — `run.py --check > rapport.txt`, un tube, une tâche planifiée,
    une intégration continue —, l'encodage retombe sur cp1252 et le premier
    `print()` non ASCII lève `UnicodeEncodeError`. Autrement dit : cela casse
    précisément quand on cherche à diagnostiquer, et c'est alors le rapport
    entier qui est perdu.

    `errors="replace"` plutôt qu'une exception : un caractère de remplacement
    dans un rapport vaut mieux qu'un rapport qui n'existe pas.
    """
    for flux in (sys.stdout, sys.stderr):
        #  Un point d'entrée graphique sous Windows n'a pas de console du
        #  tout : `sys.stdout` vaut alors `None`.
        if flux is None or not hasattr(flux, "reconfigure"):
            continue
        try:
            flux.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):                  # pragma: no cover
            pass


ACTIF = _couleur_active()


def colorier(texte: str, *codes: str) -> str:
    """Applique des codes ANSI, ou rien si la couleur est désactivée."""
    if not ACTIF or not codes:
        return texte
    return "".join(codes) + texte + RESET


# --- Raccourcis sémantiques -------------------------------------------------
def succes(t: str) -> str:
    return colorier(t, VERT_CLAIR, GRAS)


def erreur(t: str) -> str:
    return colorier(t, ROUGE_CLAIR, GRAS)


def alerte(t: str) -> str:
    return colorier(t, JAUNE_CLAIR)


def info(t: str) -> str:
    return colorier(t, CYAN_CLAIR)


def discret(t: str) -> str:
    return colorier(t, GRIS)


def titre(t: str) -> str:
    return colorier(t, GRAS, VERT)


# --- Éléments d'affichage ---------------------------------------------------
PUCES = {"ok": "✓", "err": "✗", "warn": "!", "info": "·", "attente": "…"}


def ligne_statut(etat: str, libelle: str, detail: str = "",
                 largeur: int = 22) -> str:
    """« [✓] numpy        2.1.0   traitement du signal »"""
    puce = PUCES.get(etat, "·")
    couleur = {"ok": succes, "err": erreur, "warn": alerte,
               "info": info}.get(etat, discret)
    return f"  {couleur('[' + puce + ']')} {libelle:<{largeur}} {discret(detail)}"


def replier(texte: str, largeur: int, indent: str = "") -> list:
    """Replie un texte long sans couper les mots ; conserve l'indentation."""
    brut = _sans_ansi(texte)
    if len(brut) <= largeur:
        return [texte]
    mots = brut.split(" ")
    lignes, courante = [], ""
    for mot in mots:
        if not courante:
            courante = mot
        elif len(courante) + 1 + len(mot) <= largeur:
            courante += " " + mot
        else:
            lignes.append(courante)
            courante = indent + mot
    if courante:
        lignes.append(courante)
    return lignes


def encadre(titre_: str, lignes, largeur: int = 78) -> str:
    """Encadré ASCII — lisible même sans couleur, avec repli des lignes longues."""
    utile = largeur - 4
    haut = "┌" + "─" * (largeur - 2) + "┐"
    bas = "└" + "─" * (largeur - 2) + "┘"
    sep = "├" + "─" * (largeur - 2) + "┤"
    out = [colorier(haut, VERT),
           colorier("│", VERT) + f" {titre_[:utile]:<{utile}} " + colorier("│", VERT),
           colorier(sep, VERT)]
    for ligne in lignes:
        for morceau in replier(ligne, utile, indent="    "):
            brut = _sans_ansi(morceau)
            bourrage = " " * max(utile - len(brut), 0)
            out.append(colorier("│", VERT) + f" {morceau}{bourrage} " +
                       colorier("│", VERT))
    out.append(colorier(bas, VERT))
    return "\n".join(out)


def _sans_ansi(texte: str) -> str:
    import re
    return re.sub(r"\033\[[0-9;]*m", "", texte)


def barre(fraction: float, largeur: int = 30) -> str:
    """Barre de progression textuelle."""
    fraction = min(max(fraction, 0.0), 1.0)
    plein = int(fraction * largeur)
    return ("█" * plein) + ("░" * (largeur - plein)) + f" {fraction * 100:3.0f} %"


def demander_oui_non(question: str, defaut: bool = True) -> bool:
    """Question fermée en console ; renvoie le défaut si l'entrée est absente."""
    suffixe = " [O/n] " if defaut else " [o/N] "
    try:
        if not sys.stdin or not sys.stdin.isatty():
            return defaut
        reponse = input(colorier(question + suffixe, CYAN_CLAIR)).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    if not reponse:
        return defaut
    return reponse[0] in ("o", "y", "1")
