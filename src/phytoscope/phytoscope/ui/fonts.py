# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/fonts.py
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

"""Les polices — une pile de replis, et la même taille apparente partout.

Deux problèmes se règlent ici, et nulle part ailleurs.

**Une police nommée seule n'existe pas partout.** « DejaVu Sans Mono » est
installée d'office sur presque toutes les distributions GNU/Linux ; elle n'est
présente ni sous Windows ni sous macOS. Qt, faute de la trouver, substitue ce
qu'il veut — souvent une police **proportionnelle**. Or un tableau de valeurs
mesurées repose entièrement sur des chiffres de largeur égale : dès que la
substitution est proportionnelle, les colonnes se décalent et l'afficheur
devient illisible. On déclare donc une **pile** de familles, dans l'ordre de
préférence, et l'on dit en plus à Qt de quel **genre** de police il s'agit
(`QFont.Monospace`) : même si aucune famille de la pile n'existe, le repli
choisi par le système reste à chasse fixe.

**Le point n'a pas la même taille selon le système.** Qt résout une taille
exprimée en points contre la résolution logique de l'écran : 96 ppp sous
Windows et sous X11/Wayland, **72 ppp sous macOS**. Une police déclarée à 9
points paraît donc un tiers plus petite sur un Mac que sur un PC — à la limite
de la lisibilité pour les graduations des cadrans, qui descendent à 6,2 points.
On corrige d'un facteur 4/3 sur Darwin, de sorte qu'une taille demandée ici
désigne la **même taille apparente** sur les trois systèmes.

Tout le reste de l'interface passe par ce module ; un essai de portabilité
vérifie qu'aucun fichier ne nomme une police en dur.
"""
from __future__ import annotations

import sys
from typing import Optional, Sequence

from PySide6.QtGui import QFont

__all__ = ["mono", "texte", "PILE_MONO", "PILE_TEXTE", "css_mono", "facteur"]

#  Dans l'ordre : le choix du projet, puis le défaut de macOS, celui de
#  Windows, celui des distributions sans DejaVu, et enfin l'antiquité qui
#  existe partout. Le dernier terme n'est pas une famille mais un genre : Qt
#  le comprend comme tel et prend ce que le système appelle « à chasse fixe ».
PILE_MONO: Sequence[str] = (
    "DejaVu Sans Mono",     # GNU/Linux, et installée volontiers ailleurs
    "Menlo",                # macOS depuis 10.6
    "Consolas",             # Windows depuis Vista
    "Liberation Mono",      # distributions sans DejaVu (Fedora, RHEL)
    "Courier New",          # partout, y compris les machines très anciennes
    "monospace",
)

PILE_TEXTE: Sequence[str] = (
    "DejaVu Sans",
    "Helvetica Neue",       # macOS
    "Segoe UI",             # Windows
    "Liberation Sans",
    "Arial",
    "sans-serif",
)


def facteur() -> float:
    """Correction de taille propre au système.

    macOS raisonne à 72 points par pouce logique, les autres à 96. Sans cette
    correction, toute l'interface serait un tiers plus petite sur un Mac.
    """
    return 96.0 / 72.0 if sys.platform == "darwin" else 1.0


def _batir(pile: Sequence[str], taille_pt: Optional[float], gras: bool,
           genre) -> QFont:
    f = QFont()
    #  `setFamilies` prend la pile entière ; `setFamily` n'en prendrait qu'une.
    f.setFamilies(list(pile))
    f.setStyleHint(genre, QFont.PreferMatch)
    if taille_pt is not None:
        f.setPointSizeF(float(taille_pt) * facteur())
    if gras:
        f.setBold(True)
    return f


def mono(taille_pt: Optional[float] = None, gras: bool = False) -> QFont:
    """Police à chasse fixe — valeurs mesurées, journaux, colonnes alignées."""
    return _batir(PILE_MONO, taille_pt, gras, QFont.Monospace)


def texte(taille_pt: Optional[float] = None, gras: bool = False) -> QFont:
    """Police de texte courant — libellés, graduations, légendes."""
    return _batir(PILE_TEXTE, taille_pt, gras, QFont.SansSerif)


def css_mono(taille_pt: Optional[float] = None) -> str:
    """La même pile, pour une feuille de style Qt.

    Les feuilles de style ne connaissent pas `setStyleHint` : on y écrit la
    liste des familles, en terminant par le genre générique.
    """
    familles = ", ".join(f"'{n}'" if " " in n else n for n in PILE_MONO)
    regle = f"font-family: {familles};"
    if taille_pt is not None:
        regle += f" font-size: {float(taille_pt) * facteur():.1f}pt;"
    return regle
