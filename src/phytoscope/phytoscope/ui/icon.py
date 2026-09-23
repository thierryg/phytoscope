# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/icon.py
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

"""L'emblème du logiciel : une fleur de lotus blanche.

Le lotus est dessiné par le programme, jamais chargé depuis une image
matricielle : il reste net à toutes les tailles, de l'icône de 16 pixels
dans la barre des tâches jusqu'à la vignette de 512 pixels d'un paquet
d'installation. Le même tracé sert à produire un fichier SVG, pour les
gestionnaires de bureau qui préfèrent un fichier.

Construction : trois couronnes de pétales (arrière, milieu, avant), chacune
formée de pétales lancéolés tracés par deux courbes de Bézier symétriques,
plus un cœur. Le blanc est nuancé par un dégradé très doux, sans quoi la
fleur paraît plate sur fond clair.
"""
from __future__ import annotations

import math
from typing import List, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QIcon, QLinearGradient, QPainter,
                           QPainterPath, QPen, QPixmap, QRadialGradient)

# Couronnes : (nombre de pétales, décalage angulaire, longueur, largeur, teinte)
COURONNES: Tuple[Tuple[int, float, float, float, float], ...] = (
    (8, 0.0, 0.46, 0.155, 0.80),      # arrière, plus sombre
    (8, 22.5, 0.40, 0.150, 0.92),     # milieu
    (5, 0.0, 0.31, 0.140, 1.00),      # avant, le plus clair
)


def _petale(longueur: float, largeur: float) -> QPainterPath:
    """Pétale lancéolé, pointe vers le haut, base à l'origine."""
    p = QPainterPath()
    p.moveTo(0.0, 0.0)
    p.cubicTo(largeur, -longueur * 0.35, largeur * 0.72, -longueur * 0.82,
              0.0, -longueur)
    p.cubicTo(-largeur * 0.72, -longueur * 0.82, -largeur, -longueur * 0.35,
              0.0, 0.0)
    p.closeSubpath()
    return p


def dessiner_lotus(peintre: QPainter, taille: float,
                   couleur: str = "#FFFFFF", contour: str = "#C8D6CE",
                   coeur: str = "#E8D9A8") -> None:
    """Trace la fleur dans un carré de côté `taille`, centrée."""
    peintre.setRenderHint(QPainter.Antialiasing, True)
    cx, cy = taille / 2.0, taille * 0.60
    base = QColor(couleur)

    for n, decalage, longueur, largeur, teinte in COURONNES:
        L = longueur * taille
        W = largeur * taille
        chemin_petale = _petale(L, W)
        for i in range(n):
            angle = decalage + i * (360.0 / n)
            peintre.save()
            peintre.translate(cx, cy)
            peintre.rotate(angle)
            degrade = QLinearGradient(0, 0, 0, -L)
            sombre = QColor(base)
            sombre.setRedF(min(base.redF() * teinte, 1.0))
            sombre.setGreenF(min(base.greenF() * teinte, 1.0))
            sombre.setBlueF(min(base.blueF() * teinte, 1.0))
            degrade.setColorAt(0.0, sombre)
            degrade.setColorAt(1.0, base)
            peintre.setBrush(QBrush(degrade))
            peintre.setPen(QPen(QColor(contour), max(taille * 0.006, 0.6)))
            peintre.drawPath(chemin_petale)
            peintre.restore()

    # cœur de la fleur
    r = taille * 0.075
    halo = QRadialGradient(QPointF(cx, cy - r * 0.2), r * 1.6)
    halo.setColorAt(0.0, QColor(coeur))
    halo.setColorAt(1.0, QColor(coeur).darker(120))
    peintre.setBrush(QBrush(halo))
    peintre.setPen(Qt.NoPen)
    peintre.drawEllipse(QPointF(cx, cy - r * 0.2), r, r * 0.86)

    # étamines
    peintre.setPen(QPen(QColor(coeur).darker(150), max(taille * 0.008, 0.7)))
    for i in range(7):
        a = math.radians(-160 + i * 20)
        x1 = cx + math.cos(a) * r * 0.5
        y1 = cy - r * 0.2 + math.sin(a) * r * 0.4
        x2 = cx + math.cos(a) * r * 1.5
        y2 = cy - r * 0.2 + math.sin(a) * r * 1.2
        peintre.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def lotus_pixmap(taille: int = 256, couleur: str = "#FFFFFF",
                 fond: Optional[str] = None) -> QPixmap:
    """Vignette de la fleur, sur fond transparent par défaut."""
    pm = QPixmap(taille, taille)
    pm.fill(QColor(fond) if fond else Qt.transparent)
    peintre = QPainter(pm)
    try:
        dessiner_lotus(peintre, float(taille), couleur)
    finally:
        peintre.end()
    return pm


def app_icon(couleur: str = "#FFFFFF") -> QIcon:
    """Icône multi-résolutions de l'application.

    Aux très petites tailles, le contour est renforcé : sans cela, une fleur
    blanche disparaît sur une barre des tâches claire.
    """
    icone = QIcon()
    for taille in (16, 24, 32, 48, 64, 128, 256, 512):
        pm = QPixmap(taille, taille)
        pm.fill(Qt.transparent)
        peintre = QPainter(pm)
        try:
            contour = "#7E9A8B" if taille <= 32 else "#C8D6CE"
            dessiner_lotus(peintre, float(taille), couleur, contour)
        finally:
            peintre.end()
        icone.addPixmap(pm)
    return icone


# ---------------------------------------------------------------------------
#  Version SVG, pour les gestionnaires de bureau et les paquets
# ---------------------------------------------------------------------------
def lotus_svg(taille: int = 512, couleur: str = "#FFFFFF",
              contour: str = "#C8D6CE", coeur: str = "#E8D9A8") -> str:
    """Le même tracé, écrit en SVG — sans dépendre de Qt."""
    cx, cy = taille / 2.0, taille * 0.60
    morceaux: List[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {taille} {taille}" '
        f'width="{taille}" height="{taille}">',
        '<defs>',
        f'  <radialGradient id="coeur"><stop offset="0%" stop-color="{coeur}"/>'
        f'<stop offset="100%" stop-color="{QColor(coeur).darker(120).name()}"/>'
        f'</radialGradient>',
        '</defs>',
    ]
    for n, decalage, longueur, largeur, teinte in COURONNES:
        L = longueur * taille
        W = largeur * taille
        c = QColor(couleur)
        c = QColor.fromRgbF(min(c.redF() * teinte, 1.0),
                            min(c.greenF() * teinte, 1.0),
                            min(c.blueF() * teinte, 1.0))
        d = (f"M 0,0 C {W},{-L * 0.35} {W * 0.72},{-L * 0.82} 0,{-L} "
             f"C {-W * 0.72},{-L * 0.82} {-W},{-L * 0.35} 0,0 Z")
        for i in range(n):
            angle = decalage + i * (360.0 / n)
            morceaux.append(
                f'<path d="{d}" fill="{c.name()}" stroke="{contour}" '
                f'stroke-width="{max(taille * 0.006, 0.6):.2f}" '
                f'transform="translate({cx:.1f},{cy:.1f}) rotate({angle:.1f})"/>')
    r = taille * 0.075
    morceaux.append(f'<ellipse cx="{cx:.1f}" cy="{cy - r * 0.2:.1f}" '
                    f'rx="{r:.1f}" ry="{r * 0.86:.1f}" fill="url(#coeur)"/>')
    for i in range(7):
        a = math.radians(-160 + i * 20)
        x1 = cx + math.cos(a) * r * 0.5
        y1 = cy - r * 0.2 + math.sin(a) * r * 0.4
        x2 = cx + math.cos(a) * r * 1.5
        y2 = cy - r * 0.2 + math.sin(a) * r * 1.2
        morceaux.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" '
                        f'y2="{y2:.1f}" stroke="{QColor(coeur).darker(150).name()}" '
                        f'stroke-width="{max(taille * 0.008, 0.7):.2f}"/>')
    morceaux.append("</svg>")
    return "\n".join(morceaux)


def ecrire_assets(repertoire: str) -> List[str]:
    """Écrit lotus.svg et quelques PNG — utilisé par l'outil de publication."""
    import os
    os.makedirs(repertoire, exist_ok=True)
    ecrits = []
    chemin_svg = os.path.join(repertoire, "lotus.svg")
    with open(chemin_svg, "w", encoding="utf-8") as f:
        f.write(lotus_svg())
    ecrits.append(chemin_svg)
    for taille in (48, 128, 256):
        chemin = os.path.join(repertoire, f"lotus-{taille}.png")
        if lotus_pixmap(taille).save(chemin, "PNG"):
            ecrits.append(chemin)
    return ecrits
