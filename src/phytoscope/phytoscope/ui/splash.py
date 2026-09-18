# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/splash.py
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

"""Écran d'accueil — la fleur, le nom, et ce que fait le logiciel pendant ce temps.

Un écran d'accueil n'a d'utilité que s'il informe. Celui-ci affiche donc
l'étape en cours du démarrage : contrôles, moteur audio, recherche de la
carte. Il s'efface dès que la fenêtre principale est prête.
"""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from .. import version as V
from . import theme


class Splash(QSplashScreen):
    """Écran d'accueil dessiné par le programme, sans fichier image."""

    LARGEUR = 560
    HAUTEUR = 340

    def __init__(self, theme_name: str = "sombre"):
        self.p = theme.palette(theme_name)
        super().__init__(self._fond(), Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self._etape = "démarrage…"

    # -- dessin --------------------------------------------------------------
    def _fond(self) -> QPixmap:
        from .icon import dessiner_lotus
        pm = QPixmap(self.LARGEUR, self.HAUTEUR)
        pm.fill(QColor(self.p["fond3"]))
        qp = QPainter(pm)
        try:
            qp.setRenderHint(QPainter.Antialiasing, True)
            qp.setPen(QColor(self.p["trait"]))
            qp.drawRect(0, 0, self.LARGEUR - 1, self.HAUTEUR - 1)

            qp.save()
            qp.translate(36, 70)
            dessiner_lotus(qp, 180.0, "#FFFFFF", self.p["trait"])
            qp.restore()

            f = QFont()
            f.setPointSize(30)
            f.setBold(True)
            qp.setFont(f)
            qp.setPen(QColor(self.p["or"]))
            qp.drawText(240, 118, V.APP_NAME)

            f.setPointSize(11)
            f.setBold(False)
            f.setItalic(True)
            qp.setFont(f)
            qp.setPen(QColor(self.p["texte2"]))
            qp.drawText(242, 146, "Écoute et mesure des signaux végétaux")

            f.setItalic(False)
            f.setPointSize(10)
            qp.setFont(f)
            qp.setPen(QColor(self.p["texte"]))
            qp.drawText(242, 186, f"version {V.TITRE_VERSION}")
            qp.setPen(QColor(self.p["texte2"]))
            qp.drawText(242, 208, V.AUTHOR)
            qp.drawText(242, 228, V.WEBSITE)

            qp.setPen(QColor(self.p["trait"]))
            qp.drawLine(36, 268, self.LARGEUR - 36, 268)
        finally:
            qp.end()
        return pm

    # -- étapes --------------------------------------------------------------
    def etape(self, texte: str) -> None:
        """Affiche l'étape en cours et laisse Qt repeindre."""
        self._etape = texte
        self.showMessage("   " + texte,
                         Qt.AlignBottom | Qt.AlignLeft,
                         QColor(self.p["trace"]))
        app = QApplication.instance()
        if app is not None:
            app.processEvents()

    def terminer(self, fenetre) -> None:
        """Efface l'écran d'accueil dès que la fenêtre est affichée."""
        self.finish(fenetre)
