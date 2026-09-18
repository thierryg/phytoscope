# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/widgets.py
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

"""Widgets communs : tracés, afficheurs, voyants.

Le tracé utilise **pyqtgraph** s'il est installé (interaction, zoom, très
bonnes performances) et bascule sinon sur un tracé maison au QPainter. Cette
seconde voie n'est pas un pis-aller : elle garantit que le logiciel reste
utilisable sur une machine où l'on ne peut rien installer de plus.
"""
from __future__ import annotations

import math
import time
from typing import List, Optional, Sequence, Tuple

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QSizePolicy,
                               QToolButton, QVBoxLayout, QWidget)

from ..i18n import t
from . import polices

try:                                                   # pragma: no cover
    import pyqtgraph as pg
    HAVE_PYQTGRAPH = True
except Exception:                                      # pragma: no cover
    pg = None
    HAVE_PYQTGRAPH = False


# ---------------------------------------------------------------------------
#  Tracé de signal
# ---------------------------------------------------------------------------
class TracePlot(QWidget):
    """Courbe temps réel, avec grille, curseurs et marqueurs d'événement.

    Quand pyqtgraph est présent, la molette zoome et le glisser déplace. C'est
    précieux — et c'est aussi la première façon de se perdre : on zoome, le
    signal sort du cadre, et l'on croit l'acquisition arrêtée. Un petit bouton
    de retour à l'origine **apparaît donc dès que la vue est déplacée**, et
    disparaît dès qu'elle est revenue. Un bouton toujours visible serait du
    bruit ; un bouton absent serait un piège.
    """

    #  Émis quand la vue passe de « cadrée » à « déplacée », ou l'inverse.
    zoom_modifie = Signal(bool)

    def __init__(self, palette: dict, y_label: str = "µV", parent=None):
        super().__init__(parent)
        self.p = palette
        self.y_label = y_label
        self._x: Optional[np.ndarray] = None
        self._y: Optional[np.ndarray] = None
        self._marks: List[float] = []
        self._y_range: Tuple[float, float] = (-1.0, 1.0)
        self._x_range: Tuple[float, float] = (0.0, 60.0)
        self._auto = True
        self._log_y = False
        #  120 px : assez pour lire une courbe, assez peu pour que la
        #  fenêtre tienne sur l'écran d'un portable de treize pouces.
        self.setMinimumHeight(120)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self._pg_plot = None
        self._pg_curve = None
        self._zoome = False

        #  Le bouton de retour à l'origine, posé par-dessus la courbe. Il est
        #  créé caché : rien à faire tant que la vue n'a pas bougé.
        self.btn_zoom = QToolButton(self)
        self.btn_zoom.setText("⟲")
        self.btn_zoom.setToolTip(t("Revenir au cadrage d'origine (Ctrl+0)"))
        self.btn_zoom.setCursor(Qt.PointingHandCursor)
        self.btn_zoom.setStyleSheet(
            f"QToolButton{{background:{palette['fond3']};color:{palette['or']};"
            f"border:1px solid {palette['or']};border-radius:4px;"
            f"padding:2px 7px;font-weight:bold;}}"
            f"QToolButton:hover{{background:{palette['accent']};color:#fff;}}")
        self.btn_zoom.clicked.connect(self.reinitialiser_zoom)
        self.btn_zoom.hide()

        if HAVE_PYQTGRAPH:
            pg.setConfigOptions(antialias=True, background=palette["fond3"],
                                foreground=palette["texte2"])
            self._pg_plot = pg.PlotWidget()
            self._pg_plot.showGrid(x=True, y=True, alpha=0.22)
            self._pg_plot.setLabel("left", y_label)
            self._pg_plot.setLabel("bottom", "temps", units="s")
            self._pg_curve = self._pg_plot.plot(
                pen=pg.mkPen(palette["trace"], width=1.6))
            lay = QVBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.addWidget(self._pg_plot)
            #  « Manually » : seuls les gestes de l'utilisateur comptent. Les
            #  recadrages automatiques dus à l'arrivée de données ne doivent
            #  évidemment pas faire surgir le bouton.
            vue = self._pg_plot.getViewBox()
            vue.sigRangeChangedManually.connect(self._vue_deplacee)
            self.btn_zoom.raise_()

    # -- API -----------------------------------------------------------------
    def set_data(self, x: np.ndarray, y: np.ndarray) -> None:
        self._x, self._y = x, y
        if self._auto and y.size:
            span = float(np.max(np.abs(y))) or 1.0
            self._y_range = (-span * 1.25, span * 1.25)
        if x.size:
            self._x_range = (float(x[0]), float(x[-1]))
        if self._pg_curve is not None:
            self._pg_curve.setData(x, y)
            if self._auto:
                self._pg_plot.enableAutoRange("y", True)
        else:
            self.update()

    def set_y_range(self, lo: float, hi: float) -> None:
        self._auto = False
        self._y_range = (lo, hi)
        if self._pg_plot is not None:
            self._pg_plot.setYRange(lo, hi, padding=0)
        else:
            self.update()

    def set_auto_range(self, on: bool) -> None:
        self._auto = on
        if self._pg_plot is not None:
            self._pg_plot.enableAutoRange("y", on)

    def set_marks(self, marks: Sequence[float]) -> None:
        self._marks = list(marks)[-200:]
        if self._pg_plot is None:
            self.update()

    # -- état du cadrage -----------------------------------------------------
    def _vue_deplacee(self, *_):
        self._changer_zoom(True)

    def _changer_zoom(self, zoome: bool) -> None:
        if zoome == self._zoome:
            return
        self._zoome = zoome
        self.btn_zoom.setVisible(zoome)
        if zoome:
            self._placer_bouton()
        self.zoom_modifie.emit(zoome)

    def est_zoome(self) -> bool:
        """Vrai si l'utilisateur a déplacé ou agrandi la vue."""
        return self._zoome

    def _placer_bouton(self) -> None:
        taille = self.btn_zoom.sizeHint()
        self.btn_zoom.setGeometry(self.width() - taille.width() - 12, 8,
                                  taille.width(), taille.height())
        self.btn_zoom.raise_()

    def resizeEvent(self, ev):                         # pragma: no cover
        super().resizeEvent(ev)
        if self._zoome:
            self._placer_bouton()

    def reinitialiser_zoom(self) -> None:
        """Revient au cadrage d'origine : tout le signal, échelle automatique.

        Avec pyqtgraph, la molette et le glisser déplacent et zooment le tracé.
        C'est précieux — et c'est aussi la première façon de se perdre : on
        zoome, le signal « disparaît », et l'on croit l'acquisition arrêtée.
        Un bouton et un raccourci ramènent donc toujours à l'origine.
        """
        self._auto = True
        if self._pg_plot is not None:
            vue = self._pg_plot.getViewBox()
            vue.enableAutoRange(axis="xy", enable=True)
            vue.autoRange()
        else:
            if self._y is not None and self._y.size:
                span = float(np.max(np.abs(self._y))) or 1.0
                self._y_range = (-span * 1.25, span * 1.25)
            if self._x is not None and self._x.size:
                self._x_range = (float(self._x[0]), float(self._x[-1]))
        self._changer_zoom(False)
        self.update()

    def set_pen_color(self, color: str) -> None:
        if self._pg_curve is not None:
            self._pg_curve.setPen(pg.mkPen(color, width=1.6))
        self.p = dict(self.p, trace=color)

    # -- tracé maison --------------------------------------------------------
    def paintEvent(self, ev):                          # pragma: no cover
        if self._pg_plot is not None:
            return
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        r = self.rect().adjusted(46, 10, -10, -26)
        qp.fillRect(self.rect(), QColor(self.p["fond3"]))
        qp.setPen(QPen(QColor(self.p["grille"]), 1))
        for i in range(1, 8):
            x = r.left() + r.width() * i / 8
            qp.drawLine(int(x), r.top(), int(x), r.bottom())
        for i in range(1, 6):
            y = r.top() + r.height() * i / 6
            qp.drawLine(r.left(), int(y), r.right(), int(y))
        qp.setPen(QPen(QColor(self.p["trait"]), 1))
        qp.drawRect(r)

        lo, hi = self._y_range
        if hi - lo < 1e-15:
            hi = lo + 1e-15
        qp.setFont(polices.mono(7.5))
        qp.setPen(QColor(self.p["texte2"]))
        for i in range(4):
            v = hi - (hi - lo) * i / 3
            y = r.top() + r.height() * i / 3
            qp.drawText(QRectF(0, y - 8, 42, 16),
                        Qt.AlignRight | Qt.AlignVCenter, _fmt(v))
        if self._x is not None and self._x.size:
            qp.drawText(QRectF(r.left(), r.bottom() + 4, 80, 16),
                        Qt.AlignLeft, f"{self._x[0]:.0f} s")
            qp.drawText(QRectF(r.right() - 80, r.bottom() + 4, 80, 16),
                        Qt.AlignRight, f"{self._x[-1]:.0f} s")

        if self._y is None or self._y.size < 2:
            qp.end()
            return
        x0, x1 = self._x_range
        if x1 - x0 < 1e-9:
            x1 = x0 + 1e-9
        n = self._y.size
        step = max(1, n // max(r.width(), 1))
        path = QPainterPath()
        first = True
        for i in range(0, n, step):
            px = r.left() + (self._x[i] - x0) / (x1 - x0) * r.width()
            py = r.top() + (hi - self._y[i]) / (hi - lo) * r.height()
            py = max(r.top(), min(float(py), r.bottom()))
            if first:
                path.moveTo(QPointF(px, py))
                first = False
            else:
                path.lineTo(QPointF(px, py))
        qp.setPen(QPen(QColor(self.p["trace"]), 1.6))
        qp.drawPath(path)

        qp.setPen(QPen(QColor(self.p["or"]), 1, Qt.DashLine))
        for m in self._marks:
            if x0 <= m <= x1:
                px = r.left() + (m - x0) / (x1 - x0) * r.width()
                qp.drawLine(int(px), r.top(), int(px), r.bottom())
        qp.end()


def _fmt(v: float) -> str:
    a = abs(v)
    if a >= 1:
        return f"{v:.2f}"
    if a >= 1e-3:
        return f"{v * 1e3:.1f}m"
    if a >= 1e-6:
        return f"{v * 1e6:.1f}µ"
    return f"{v * 1e9:.0f}n"


# ---------------------------------------------------------------------------
#  Afficheurs
# ---------------------------------------------------------------------------
class VuMetre(QWidget):
    """Vumètre à aiguille — l'aiguille dit ce qu'un nombre ne dit pas.

    Un afficheur numérique donne la valeur ; il ne donne pas le **mouvement**.
    Or ce qu'on cherche devant une plante, c'est justement le mouvement : une
    dérive qui s'installe, une crête qui revient, un bruit qui monte quand on
    touche le câble. L'œil lit une aiguille d'un coup d'œil, et il compare deux
    aiguilles sans y penser ; il faut lire un nombre, puis le comparer au
    précédent qu'on a oublié.

    Trois choix de conception, tous empruntés aux appareils de mesure réels :

    **La balistique.** L'aiguille ne saute pas : elle suit la valeur avec une
    constante de temps de 150 ms, comme le mouvement d'un vumètre à cadre
    mobile. Sans cela, elle tremblerait à trente images par seconde et serait
    illisible — on afficherait de l'agitation, pas une mesure.

    **La mémoire de crête.** Un repère marque le maximum atteint et redescend
    lentement (deux secondes de tenue, puis chute). C'est ce qui permet de voir
    une pointe brève qu'on aurait manquée en clignant des yeux.

    **L'échelle qui s'adapte, mais par paliers.** Une échelle continue rendrait
    toute comparaison impossible d'un instant à l'autre. L'échelle saute donc
    dans la suite 1–2–5, et sa valeur est écrite sous le cadran : on sait
    toujours ce que vaut le fond d'échelle.
    """

    #  Constantes de mouvement, en secondes.
    TAU_MONTEE = 0.15          # le temps que met l'aiguille à rejoindre la valeur
    CRETE_TENUE = 2.0          # la crête reste affichée
    CRETE_CHUTE = 0.6          # puis retombe

    def __init__(self, palette: dict, titre: str, unite: str = "",
                 maximum: float = 100.0, centre_zero: bool = False,
                 auto: bool = True, seuils=(0.6, 0.85), parent=None):
        super().__init__(parent)
        self.p = palette
        self.titre = titre
        self.unite = unite
        self.maximum = float(maximum)
        self.centre_zero = bool(centre_zero)
        self.auto = bool(auto)
        self.seuils = seuils        # fractions du fond d'échelle : ambre, rouge
        self._valeur = 0.0          # la valeur demandée
        self._aiguille = 0.0        # la position réelle, amortie
        self._crete = 0.0
        self._crete_t = 0.0
        self._t = time.monotonic()
        self.setMinimumSize(150, 132)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    # -- API -----------------------------------------------------------------
    def set_value(self, valeur: float) -> None:
        """Nouvelle valeur mesurée. L'aiguille s'en approche, elle n'y saute pas."""
        try:
            valeur = float(valeur)
        except (TypeError, ValueError):
            return
        if valeur != valeur:                           # NaN
            return
        self._valeur = valeur

        maintenant = time.monotonic()
        dt = max(min(maintenant - self._t, 0.5), 0.0)
        self._t = maintenant

        #  Filtre du premier ordre : c'est exactement le comportement d'un
        #  cadre mobile amorti, et cela se calcule en une ligne.
        alpha = 1.0 - math.exp(-dt / self.TAU_MONTEE) if dt > 0 else 1.0
        self._aiguille += (valeur - self._aiguille) * alpha

        ampleur = abs(valeur)
        if ampleur >= abs(self._crete):
            self._crete = valeur
            self._crete_t = maintenant
        elif maintenant - self._crete_t > self.CRETE_TENUE:
            chute = (maintenant - self._crete_t - self.CRETE_TENUE) / self.CRETE_CHUTE
            self._crete *= max(1.0 - chute * dt / self.CRETE_CHUTE, 0.0)

        if self.auto:
            self._ajuster_echelle(max(ampleur, abs(self._crete)))
        self.update()

    def _ajuster_echelle(self, besoin: float) -> None:
        """Échelle par paliers 1–2–5 : on ne compare que ce qui est comparable."""
        if besoin <= 0:
            return
        cible = besoin * 1.15
        if cible <= self.maximum * 0.9 and cible > self.maximum * 0.28:
            return                                     # l'échelle actuelle convient
        decade = 10.0 ** math.floor(math.log10(cible))
        for facteur in (1.0, 2.0, 5.0, 10.0):
            if cible <= facteur * decade:
                self.maximum = facteur * decade
                return

    def set_echelle(self, maximum: float) -> None:
        self.auto = False
        self.maximum = max(float(maximum), 1e-12)
        self.update()

    # -- rendu ---------------------------------------------------------------
    def _fraction(self, valeur: float) -> float:
        """Position sur le cadran, de 0 (gauche) à 1 (droite)."""
        m = self.maximum or 1.0
        if self.centre_zero:
            return min(max(0.5 + valeur / (2.0 * m), 0.0), 1.0)
        return min(max(valeur / m, 0.0), 1.0)

    def paintEvent(self, ev):                          # pragma: no cover
        qp = QPainter(self)
        qp.setRenderHint(QPainter.Antialiasing, True)
        w, h = self.width(), self.height()
        qp.fillRect(self.rect(), QColor(self.p["fond3"]))
        qp.setPen(QPen(QColor(self.p["trait"]), 1))
        qp.drawRoundedRect(0, 0, w - 1, h - 1, 5, 5)

        #  Le cadran : un arc de 140°, centre bas, comme un galvanomètre.
        cx, cy = w / 2.0, h - 34.0
        rayon = min(w / 2.0 - 14.0, h - 56.0)
        if rayon < 20:
            qp.end()
            return
        depart, etendue = 200.0, -220.0                # degrés, sens horaire

        def angle(fraction):
            return depart + etendue * fraction

        def point(fraction, r):
            a = math.radians(angle(fraction))
            return QPointF(cx + r * math.cos(a), cy - r * math.sin(a))

        #  Les zones : vert jusqu'au premier seuil, ambre, puis rouge.
        bornes = [0.0] + list(self.seuils) + [1.0]
        couleurs = [self.p["accent"], self.p["or"], self.p["alerte"]]
        for (a, b), couleur in zip(zip(bornes[:-1], bornes[1:]), couleurs):
            if self.centre_zero:
                #  Symétrique : les zones vont du centre vers les deux bords.
                for signe in (-1.0, 1.0):
                    f1 = 0.5 + signe * a / 2.0
                    f2 = 0.5 + signe * b / 2.0
                    qp.setPen(QPen(QColor(couleur), 4, Qt.SolidLine, Qt.FlatCap))
                    self._arc(qp, cx, cy, rayon, angle(min(f1, f2)), angle(max(f1, f2)))
            else:
                qp.setPen(QPen(QColor(couleur), 4, Qt.SolidLine, Qt.FlatCap))
                self._arc(qp, cx, cy, rayon, angle(a), angle(b))

        #  Graduations.
        qp.setPen(QPen(QColor(self.p["texte2"]), 1))
        for i in range(11):
            f = i / 10.0
            longue = (i % 5 == 0)
            p1 = point(f, rayon - 6)
            p2 = point(f, rayon - (14 if longue else 10))
            qp.drawLine(p1, p2)

        #  La mémoire de crête, en or.
        if abs(self._crete) > 1e-15:
            qp.setPen(QPen(QColor(self.p["or"]), 2))
            fc = self._fraction(self._crete)
            qp.drawLine(point(fc, rayon - 16), point(fc, rayon - 2))

        #  L'aiguille.
        f = self._fraction(self._aiguille)
        depasse = abs(self._aiguille) > self.maximum * (1.0 if not self.centre_zero else 1.0)
        couleur = self.p["alerte"] if depasse else self.p["trace"]
        qp.setPen(QPen(QColor(couleur), 2.2))
        qp.drawLine(QPointF(cx, cy), point(f, rayon - 12))
        qp.setBrush(QColor(couleur))
        qp.drawEllipse(QPointF(cx, cy), 3.2, 3.2)
        qp.setBrush(Qt.NoBrush)

        #  Le titre, la valeur et le fond d'échelle.
        qp.setFont(polices.texte(7.0))
        qp.setPen(QColor(self.p["texte2"]))
        qp.drawText(QRectF(4, 3, w - 8, 12), Qt.AlignHCenter, self.titre)

        qp.setFont(polices.mono(9.5, gras=True))
        qp.setPen(QColor(couleur))
        qp.drawText(QRectF(4, h - 27, w - 8, 15), Qt.AlignHCenter,
                    f"{self._valeur:+.1f} {self.unite}" if self.centre_zero
                    else f"{self._valeur:.2f} {self.unite}")

        qp.setFont(polices.texte(6.2))
        qp.setPen(QColor(self.p["texte2"]))
        borne = self._fond_echelle()
        echelle = f"± {borne}" if self.centre_zero else f"0 – {borne}"
        qp.drawText(QRectF(4, h - 12, w - 8, 11), Qt.AlignHCenter, echelle)
        qp.end()

    def _fond_echelle(self) -> str:
        """Le fond d'échelle en clair : « 200 µV », « 2 mV », jamais « 2000.00 ».

        Une échelle qu'on doit déchiffrer ne sert à rien : on la lit du coin de
        l'œil, ou pas du tout.
        """
        m = self.maximum
        unite = (self.unite or "").strip()
        if unite.startswith("µV") and m >= 1000.0:
            reste = unite[2:]
            valeur = m / 1000.0
            texte = f"{valeur:g} mV{reste}"
        else:
            texte = f"{m:g} {unite}".strip()
        return texte

    @staticmethod
    def _arc(qp, cx, cy, rayon, a1, a2) -> None:       # pragma: no cover
        """Arc entre deux angles, en degrés, sens trigonométrique."""
        rect = QRectF(cx - rayon, cy - rayon, 2 * rayon, 2 * rayon)
        debut = min(a1, a2)
        etendue = abs(a2 - a1)
        qp.drawArc(rect, int(debut * 16), int(etendue * 16))


class Readout(QFrame):
    """Grand afficheur numérique, à la manière d'un multimètre de paillasse."""

    def __init__(self, title: str, unit: str, palette: dict, parent=None):
        super().__init__(parent)
        self.p = palette
        self.setFrameShape(QFrame.StyledPanel)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)
        self.title = QLabel(title)
        self.title.setStyleSheet(f"color:{palette['texte2']};letter-spacing:1px;")
        self.value = QLabel("—")
        self.value.setObjectName("valeur")
        self.unit = QLabel(unit)
        self.unit.setObjectName("unite")
        row = QHBoxLayout()
        row.addWidget(self.value)
        row.addWidget(self.unit, alignment=Qt.AlignBottom)
        row.addStretch(1)
        lay.addWidget(self.title)
        lay.addLayout(row)

    def set_value(self, text: str, alert: bool = False) -> None:
        self.value.setText(text)
        col = self.p["alerte"] if alert else self.p["trace"]
        self.value.setStyleSheet(polices.css_mono(26) + f"color:{col};")

    def set_unit(self, unit: str) -> None:
        self.unit.setText(unit)


class LevelBar(QWidget):
    """Barre de niveau avec crête maintenue — surveille la saturation."""

    def __init__(self, palette: dict, parent=None):
        super().__init__(parent)
        self.p = palette
        self.value = 0.0
        self.peak = 0.0
        self._hold = 0
        self.setMinimumHeight(18)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, v: float) -> None:
        self.value = max(0.0, min(v, 1.2))
        if self.value >= self.peak:
            self.peak, self._hold = self.value, 40
        elif self._hold > 0:
            self._hold -= 1
        else:
            self.peak = max(self.value, self.peak * 0.96)
        self.update()

    def paintEvent(self, ev):                          # pragma: no cover
        qp = QPainter(self)
        r = self.rect().adjusted(0, 3, 0, -3)
        qp.fillRect(r, QColor(self.p["fond3"]))
        w = int(r.width() * min(self.value, 1.0))
        col = self.p["trace"] if self.value < 0.85 else self.p["alerte"]
        qp.fillRect(r.left(), r.top(), w, r.height(), QColor(col))
        px = int(r.width() * min(self.peak, 1.0))
        qp.setPen(QPen(QColor(self.p["or"]), 2))
        qp.drawLine(r.left() + px, r.top(), r.left() + px, r.bottom())
        qp.setPen(QPen(QColor(self.p["trait"]), 1))
        qp.drawRect(r)
        qp.end()


class Led(QLabel):
    """Voyant d'état, avec libellé."""

    def __init__(self, text: str, palette: dict, parent=None):
        super().__init__(text, parent)
        self.p = palette
        self.set_state("off")

    def set_state(self, state: str) -> None:
        colors = {"ok": self.p["trace"], "warn": self.p["or"],
                  "err": self.p["alerte"], "off": self.p["texte2"]}
        c = colors.get(state, self.p["texte2"])
        self.setStyleSheet(f"color:{c};font-weight:bold;")


class StatusStrip(QFrame):
    """Bandeau d'état — l'information qui ne doit jamais mentir."""

    def __init__(self, palette: dict, fields: Sequence[str], parent=None,
                 libelles=None):
        """`fields` sont les **clés internes**, jamais traduites : c'est par
        elles que le reste du code désigne une case. `libelles` donne le texte
        affiché, traduit — les deux ne doivent pas être confondus, sous peine
        qu'un changement de langue casse les mises à jour."""
        super().__init__(parent)
        self.p = palette
        self.setFrameShape(QFrame.StyledPanel)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        self.labels = {}
        libelles = dict(libelles or {})
        for f in fields:
            box = QVBoxLayout()
            cap = QLabel(libelles.get(f, f).upper())
            cap.setStyleSheet(f"color:{palette['texte2']};font-size:7pt;"
                              f"letter-spacing:1px;")
            val = QLabel("—")
            val.setStyleSheet(polices.css_mono() + "font-weight:bold;"
                              + f"color:{palette['texte']};")
            box.addWidget(cap)
            box.addWidget(val)
            lay.addLayout(box)
            lay.addSpacing(10)
            self.labels[f] = val
        lay.addStretch(1)

    def set(self, field: str, text: str, state: str = "normal") -> None:
        lab = self.labels.get(field)
        if lab is None:
            return
        colors = {"normal": self.p["texte"], "ok": self.p["trace"],
                  "warn": self.p["or"], "err": self.p["alerte"]}
        lab.setText(text)
        lab.setStyleSheet(polices.css_mono() + "font-weight:bold;"
                          + f"color:{colors.get(state, self.p['texte'])};")
