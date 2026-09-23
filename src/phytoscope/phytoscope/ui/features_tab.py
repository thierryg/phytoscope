# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/features_tab.py
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

"""L'onglet « Descripteurs » : six façons de regarder le même signal.

Un signal végétal ne se laisse pas read d'une seule manière. La courbe brute
montre les événements mais cache les périodicités ; la FFT montre les
périodicités mais efface le temps ; l'ondelette montre les deux, au prix d'une
résolution partout moyenne. Cet onglet met les six représentations côte à côte,
avec, pour chacune, ce qu'elle apporte **et ce qu'elle ne dit pas**.

Le calcul n'a lieu que lorsque l'onglet est visible : la fenêtre principale
n'appelle ``refresh`` que sur l'onglet affiché. Une analyse en ondelettes coûte
quelques dizaines de millisecondes ; la faire tourner en permanence derrière un
oscilloscope serait payer cher une image que personne ne regarde.

Le signal est décimé avant analyse au-delà de :data:`POINTS_MAX` points. Ce
n'est pas une approximation gênante : la décimation moyenne des blocs
consécutifs, ce qui est un filtre passe-bas, et la bande qui nous intéresse est
mille fois plus basse que la fréquence d'échantillonnage.
"""
from __future__ import annotations

import math
import os
from typing import Optional, Tuple

import numpy as np
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QMessageBox, QPushButton, QScrollArea,
                               QSizePolicy, QSpinBox, QStackedWidget,
                               QVBoxLayout, QWidget)

from ..core.dsp import decimate
from ..core.features import (DESCRIPTORS, cepstre, lpc, mfcc,
                             ondelettes_morlet, spectre_instantane)
from ..core.logging_setup import get_logger
from .widgets import TracePlot
from ..i18n import t
from . import fonts

log = get_logger(__name__)

POINTS_MAX = 16384          # au-delà, on décime : l'œil ne verra pas la différence

FENETRES = [(30.0, "30 s"), (60.0, "1 min"), (120.0, "2 min"),
            (300.0, "5 min"), (600.0, "10 min")]


# ---------------------------------------------------------------------------
#  Carte de densité — le scalogramme et le spectre de Mel
# ---------------------------------------------------------------------------
class Heatmap(QWidget):
    """Énergie en fonction du temps et de la fréquence, en fausses couleurs.

    Dessinée au QPainter depuis une image construite en NumPy : aucune
    dépendance de plus, et le coût tient dans la conversion d'un tableau en
    QImage — quelques millisecondes pour une image de 48 × 1 200.
    """

    def __init__(self, palette: dict, parent=None):
        super().__init__(parent)
        self.p = palette
        self._db: Optional[np.ndarray] = None            # (n_freq, n_temps)
        self._freqs: Optional[np.ndarray] = None
        self._t0 = 0.0
        self._t1 = 1.0
        self._plage_db = 60.0                            # dynamique affichée
        self._image: Optional[QImage] = None
        self._tampon: Optional[np.ndarray] = None        # référence obligatoire
        self.y_label = t("frequency (Hz)")
        self.setMinimumHeight(140)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # -- données -------------------------------------------------------------
    def set_data(self, db: np.ndarray, freqs: np.ndarray, t0: float,
                 t1: float, plage_db: float = 60.0) -> None:
        self._db = db
        self._freqs = freqs
        self._t0, self._t1 = float(t0), float(t1)
        self._plage_db = max(float(plage_db), 6.0)
        self._construire()
        self.update()

    def _construire(self) -> None:
        if self._db is None or self._db.size == 0:
            self._image = None
            return
        d = np.asarray(self._db, dtype=float)
        haut = float(np.nanmax(d))
        bas = haut - self._plage_db
        norm = np.clip((d - bas) / max(haut - bas, 1e-9), 0.0, 1.0)
        norm = norm[::-1, :]                    # les hautes fréquences en haut
        rgb = _fausses_couleurs(norm, self.p)
        h, w, _ = rgb.shape
        self._tampon = np.ascontiguousarray(rgb)
        self._image = QImage(self._tampon.data, w, h, 3 * w, QImage.Format_RGB888)

    # -- rendu ---------------------------------------------------------------
    def paintEvent(self, ev):                            # pragma: no cover
        qp = QPainter(self)
        qp.fillRect(self.rect(), QColor(self.p["background3"]))
        r = self.rect().adjusted(56, 10, -12, -26)
        if self._image is not None:
            qp.setRenderHint(QPainter.SmoothPixmapTransform, True)
            qp.drawImage(QRectF(r), self._image)
        qp.setPen(QPen(QColor(self.p["line"]), 1))
        qp.drawRect(r)

        qp.setFont(fonts.mono(7.5))
        qp.setPen(QColor(self.p["text2"]))
        if self._freqs is not None and self._freqs.size > 1:
            #  Les échelles sont géométriques : les graduations le sont aussi.
            for i in range(5):
                part = i / 4.0
                idx = int(round(part * (self._freqs.size - 1)))
                y = r.bottom() - r.height() * part
                qp.drawText(QRectF(0, y - 8, 52, 16),
                            Qt.AlignRight | Qt.AlignVCenter,
                            _hz(float(self._freqs[idx])))
        qp.drawText(QRectF(r.left(), r.bottom() + 4, 90, 16), Qt.AlignLeft,
                    f"{self._t0:.0f} s")
        qp.drawText(QRectF(r.right() - 90, r.bottom() + 4, 90, 16), Qt.AlignRight,
                    f"{self._t1:.0f} s")
        qp.drawText(QRectF(r.left(), 0, r.width(), 12), Qt.AlignHCenter,
                    t("{axe} — {db:.0f} dB dynamic range").format(
                        axe=self.y_label, db=self._plage_db))
        qp.end()


def _fausses_couleurs(norm: np.ndarray, p: dict) -> np.ndarray:
    """Rampe fond → vert sève → or → blanc, cohérente avec la charte.

    Une rampe qui monte en luminosité **et** en saturation reste lisible en
    noir et blanc et pour un œil qui confond le rouge et le vert : c'est la
    seule raison de ne pas reprendre les rampes habituelles.
    """
    etapes = [(0.0, QColor(p["background3"])), (0.35, QColor(p["accent"])),
              (0.72, QColor(p["gold"])), (1.0, QColor("#FFFFFF"))]
    h, w = norm.shape
    out = np.zeros((h, w, 3), dtype=np.uint8)
    for (a, ca), (b, cb) in zip(etapes[:-1], etapes[1:]):
        m = (norm >= a) & (norm <= b)
        if not m.any():
            continue
        part = ((norm[m] - a) / max(b - a, 1e-9))[:, None]
        debut = np.array([ca.red(), ca.green(), ca.blue()], dtype=float)
        fin = np.array([cb.red(), cb.green(), cb.blue()], dtype=float)
        out[m] = (debut + (fin - debut) * part).astype(np.uint8)
    return out


def _hz(f: float) -> str:
    if f >= 10:
        return f"{f:.0f} Hz"
    if f >= 1:
        return f"{f:.2f} Hz"
    if f >= 0.01:
        return f"{f * 1000:.0f} mHz"
    return f"{f * 1000:.1f} mHz"


# ---------------------------------------------------------------------------
#  L'onglet
# ---------------------------------------------------------------------------
class FeaturesTab(QWidget):
    """Choix de la représentation, réglages, tracé, et lecture des résultats."""

    ORDRE = ("temporel", "frequentiel", "ondelettes", "mfcc", "lpc", "cepstre")

    def __init__(self, engine, palette: dict, on_change=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.on_change = on_change
        self._dernier = 0.0
        self._resultat = None
        self._x_courant = np.zeros(0)
        self._fs_courant = 0.0

        f = engine.settings.features
        lay = QHBoxLayout(self)

        # --- colonne de gauche : quoi compute, et comment ------------------
        gauche = QVBoxLayout()

        boite = QGroupBox(t("Representation"))
        fg = QFormLayout(boite)
        self.cb_repr = QComboBox()
        for key in self.ORDRE:
            self.cb_repr.addItem(t(DESCRIPTORS[key][0]), key)
        #  Puis celles que les modules apportent. On les AJOUTE plutôt que de
        #  remplacer les six natives : celles-ci ont chacune un rendu propre —
        #  le scalogramme est une image, pas une courbe — et les faire passer
        #  par la représentation générique de l'API serait une régression.
        #  L'API sert à étendre, pas à appauvrir ce qui existe.
        self._descripteurs_de_modules = {}
        for m in self._modules_descripteurs():
            key = f"module:{m.name}"
            self._descripteurs_de_modules[key] = m
            self.cb_repr.addItem(
                t(m.manifest.title) + "  ·  " + t("module"), key)
        _choisir(self.cb_repr, f.representation)
        self.cb_repr.currentIndexChanged.connect(self._changer_representation)
        self.cb_fenetre = QComboBox()
        for v, lab in FENETRES:
            self.cb_fenetre.addItem(lab, v)
        _choisir(self.cb_fenetre, f.window_s)
        self.cb_fenetre.currentIndexChanged.connect(self._reglages_modifies)
        fg.addRow(t("Tool"), self.cb_repr)
        fg.addRow(t("Analysed window"), self.cb_fenetre)
        gauche.addWidget(boite)

        # Une page de réglages par outil : rien d'inutile à l'écran.
        self.pages = QStackedWidget()
        self._pages_par_cle = {}
        for key in self.ORDRE:
            page = self._page_reglages(key, f)
            self._pages_par_cle[key] = self.pages.count()
            self.pages.addWidget(page)
        gauche.addWidget(self.pages)

        boite3 = QGroupBox(t("Computation"))
        f3 = QVBoxLayout(boite3)
        self.chk_auto = QCheckBox(t("recompute automatically"))
        self.chk_auto.setChecked(f.auto_refresh_s > 0)
        self.chk_auto.setToolTip(
            t("Computation only happens while this tab is showing."))
        self.chk_auto.stateChanged.connect(self._reglages_modifies)
        self.sp_periode = QDoubleSpinBox()
        self.sp_periode.setRange(0.5, 60.0)
        self.sp_periode.setSuffix(t(" s"))
        self.sp_periode.setValue(max(f.auto_refresh_s, 0.5))
        self.sp_periode.valueChanged.connect(self._reglages_modifies)
        bt = QPushButton(t("Compute now"))
        bt.clicked.connect(lambda: self._calculer(force=True))
        bx = QPushButton(t("Export the data…"))
        bx.clicked.connect(self._exporter)
        f3.addWidget(self.chk_auto)
        f3.addWidget(self.sp_periode)
        f3.addWidget(bt)
        f3.addWidget(bx)
        gauche.addWidget(boite3)
        gauche.addStretch(1)
        colonne = QWidget()
        colonne.setLayout(gauche)
        rouleau = QScrollArea()
        rouleau.setWidgetResizable(True)
        rouleau.setFrameShape(QScrollArea.NoFrame)
        rouleau.setWidget(colonne)
        rouleau.setMinimumWidth(300)
        lay.addWidget(rouleau)

        # --- colonne de droite : le tracé et sa lecture ---------------------
        droite = QVBoxLayout()
        self.title = QLabel("")
        self.title.setObjectName("title")
        self.title.setWordWrap(True)
        droite.addWidget(self.title)

        self.trace = TracePlot(palette, "amplitude")
        self.carte = Heatmap(palette)
        self.carte.setVisible(False)
        droite.addWidget(self.trace, 1)
        droite.addWidget(self.carte, 1)

        self.lecture = QLabel("")
        self.lecture.setTextFormat(Qt.RichText)
        self.lecture.setWordWrap(True)
        droite.addWidget(self.lecture)

        self.warning = QLabel("")
        self.warning.setWordWrap(True)
        self.warning.setStyleSheet(
            f"color:{palette['text2']};font-size:8pt;")
        droite.addWidget(self.warning)
        lay.addLayout(droite, 1)

        self._changer_representation()

    # -- pages de réglages ---------------------------------------------------
    def _page_reglages(self, key: str, f) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(0, 0, 0, 0)
        if key == "frequentiel":
            self.cb_fen_fft = QComboBox()
            for name in ("hann", "hamming", "blackman", "rectangulaire"):
                self.cb_fen_fft.addItem(name, name)
            _choisir(self.cb_fen_fft, f.fft_window)
            self.cb_fen_fft.currentIndexChanged.connect(self._reglages_modifies)
            self.sp_bourrage = QSpinBox()
            self.sp_bourrage.setRange(1, 8)
            self.sp_bourrage.setValue(max(int(f.fft_zero_padding), 1))
            self.sp_bourrage.setToolTip(
                t("Pads the signal with zeros: it adds no information, but it interpolates the curve and makes a peak easier to read."))
            self.sp_bourrage.valueChanged.connect(self._reglages_modifies)
            form.addRow(t("Windowing"), self.cb_fen_fft)
            form.addRow(t("Zero padding"), self.sp_bourrage)
        elif key == "ondelettes":
            self.sp_echelles = QSpinBox()
            self.sp_echelles.setRange(8, 128)
            self.sp_echelles.setValue(int(f.wavelet_scales))
            self.sp_echelles.valueChanged.connect(self._reglages_modifies)
            self.sp_omega = QDoubleSpinBox()
            self.sp_omega.setRange(3.0, 20.0)
            self.sp_omega.setSingleStep(0.5)
            self.sp_omega.setValue(float(f.wavelet_omega0))
            self.sp_omega.setToolTip(
                t("Time / frequency trade-off. 6 is the usual value: raising it sharpens frequency and blurs time."))
            self.sp_omega.valueChanged.connect(self._reglages_modifies)
            self.sp_fmin = QDoubleSpinBox()
            self.sp_fmin.setRange(0.0, 100.0)
            self.sp_fmin.setDecimals(3)
            self.sp_fmin.setSuffix(t(" Hz  (0 = auto)"))
            self.sp_fmin.setValue(float(f.wavelet_f_min_hz))
            self.sp_fmin.valueChanged.connect(self._reglages_modifies)
            self.sp_fmax = QDoubleSpinBox()
            self.sp_fmax.setRange(0.0, 1000.0)
            self.sp_fmax.setDecimals(2)
            self.sp_fmax.setSuffix(t(" Hz  (0 = auto)"))
            self.sp_fmax.setValue(float(f.wavelet_f_max_hz))
            self.sp_fmax.valueChanged.connect(self._reglages_modifies)
            form.addRow(t("Scales"), self.sp_echelles)
            form.addRow(t("ω₀"), self.sp_omega)
            form.addRow(t("Low frequency"), self.sp_fmin)
            form.addRow(t("High frequency"), self.sp_fmax)
        elif key == "mfcc":
            self.sp_coef = QSpinBox()
            self.sp_coef.setRange(4, 40)
            self.sp_coef.setValue(int(f.mfcc_count))
            self.sp_coef.valueChanged.connect(self._reglages_modifies)
            self.sp_filtres = QSpinBox()
            self.sp_filtres.setRange(8, 64)
            self.sp_filtres.setValue(int(f.mfcc_filters))
            self.sp_filtres.valueChanged.connect(self._reglages_modifies)
            self.sp_trame = QDoubleSpinBox()
            self.sp_trame.setRange(0.5, 60.0)
            self.sp_trame.setSuffix(t(" s"))
            self.sp_trame.setValue(float(f.mfcc_frame_s))
            self.sp_trame.setToolTip(
                t("Duration over which the signal is assumed stationary. In speech: 25 ms. Here: a few seconds."))
            self.sp_trame.valueChanged.connect(self._reglages_modifies)
            form.addRow(t("Coefficients"), self.sp_coef)
            form.addRow(t("Mel filters"), self.sp_filtres)
            form.addRow(t("Frame duration"), self.sp_trame)
        elif key == "lpc":
            self.sp_ordre = QSpinBox()
            self.sp_ordre.setRange(0, 48)
            self.sp_ordre.setSpecialValueText("automatic")
            self.sp_ordre.setValue(int(f.lpc_order))
            self.sp_ordre.valueChanged.connect(self._reglages_modifies)
            form.addRow(t("Model order"), self.sp_ordre)
        elif key == "cepstre":
            self.sp_qmin = QDoubleSpinBox()
            self.sp_qmin.setToolTip(
                t("Quefrency — an anagram of “frequency”, and not a typo: it is the accepted name for the abscissa of a cepstrum, which is measured in seconds."))
            self.sp_qmin.setRange(0.0, 600.0)
            self.sp_qmin.setDecimals(2)
            self.sp_qmin.setSuffix(t(" s  (0 = auto)"))
            self.sp_qmin.setValue(float(f.cepstrum_q_min_s))
            self.sp_qmin.valueChanged.connect(self._reglages_modifies)
            self.sp_qmax = QDoubleSpinBox()
            self.sp_qmax.setToolTip(
                t("Beyond a third of the analysed window there are not enough repetitions to conclude anything."))
            self.sp_qmax.setRange(0.0, 3600.0)
            self.sp_qmax.setDecimals(1)
            self.sp_qmax.setSuffix(t(" s  (0 = auto)"))
            self.sp_qmax.setValue(float(f.cepstrum_q_max_s))
            self.sp_qmax.valueChanged.connect(self._reglages_modifies)
            form.addRow(t("Minimum quefrency"), self.sp_qmin)
            form.addRow(t("Maximum quefrency"), self.sp_qmax)
        else:                                            # temporel
            lab = QLabel(t("The waveform as it leaves the filters.\nNo settings: nothing is computed."))
            lab.setWordWrap(True)
            form.addRow(lab)
        return page

    # -- réglages ------------------------------------------------------------
    def _changer_representation(self, *_):
        key = self.cb_repr.currentData()
        self.pages.setCurrentIndex(self._pages_par_cle[key])
        title, sous_titre, warning = DESCRIPTORS[key]
        self.title.setText(f"{t(title)} — {t(sous_titre)}")
        self.warning.setText(t(warning))
        carte = key in ("ondelettes", "mfcc")
        self.carte.setVisible(carte)
        self.trace.setVisible(not carte)
        self._reglages_modifies()
        self._calculer(force=True)

    def _reglages_modifies(self, *_):
        f = self.engine.settings.features
        f.representation = self.cb_repr.currentData()
        f.window_s = float(self.cb_fenetre.currentData())
        f.auto_refresh_s = (float(self.sp_periode.value())
                            if self.chk_auto.isChecked() else 0.0)
        f.fft_window = self.cb_fen_fft.currentData()
        f.fft_zero_padding = int(self.sp_bourrage.value())
        f.wavelet_scales = int(self.sp_echelles.value())
        f.wavelet_omega0 = float(self.sp_omega.value())
        f.wavelet_f_min_hz = float(self.sp_fmin.value())
        f.wavelet_f_max_hz = float(self.sp_fmax.value())
        f.mfcc_count = int(self.sp_coef.value())
        f.mfcc_filters = int(self.sp_filtres.value())
        f.mfcc_frame_s = float(self.sp_trame.value())
        f.lpc_order = int(self.sp_ordre.value())
        f.cepstrum_q_min_s = float(self.sp_qmin.value())
        f.cepstrum_q_max_s = float(self.sp_qmax.value())
        #  Volontairement, aucun callback vers le engine : ces réglages ne
        #  concernent que l'affichage. Les répercuter déclencherait une
        #  reconstruction de la chaîne de traitement, donc la perte de la
        #  mémoire de signal — c'est-à-dire de ce qu'on est en train
        #  d'analyse. Ils sont sauvés à la fermeture, comme les autres.

    # -- le calcul -----------------------------------------------------------
    def _signal(self) -> Tuple[np.ndarray, float]:
        """Le signal à analyse, décimé s'il est trop long, et sa cadence."""
        f = self.engine.settings.features
        x = self.engine.recent(f.window_s)
        fs = float(self.engine.settings.acquisition.sample_rate)
        if x.size > POINTS_MAX:
            facteur = int(math.ceil(x.size / POINTS_MAX))
            x = decimate(x, facteur)
            fs = fs / facteur
        return x, fs

    def _calculer(self, force: bool = False) -> None:
        import time as _t
        f = self.engine.settings.features
        if not force:
            if f.auto_refresh_s <= 0:
                return
            if _t.monotonic() - self._dernier < f.auto_refresh_s:
                return
        self._dernier = _t.monotonic()

        x, fs = self._signal()
        self._x_courant, self._fs_courant = x, fs
        if x.size < 64 or fs <= 0:
            self.lecture.setText("<i>Pas encore assez de signal.</i>")
            return
        key = f.representation
        try:
            if str(key).startswith("module:"):
                self._tracer_module(key, x, fs)
            elif key == "temporel":
                self._tracer_temporel(x, fs)
            elif key == "frequentiel":
                self._tracer_spectre(x, fs, f)
            elif key == "ondelettes":
                self._tracer_ondelettes(x, fs, f)
            elif key == "mfcc":
                self._tracer_mfcc(x, fs, f)
            elif key == "lpc":
                self._tracer_lpc(x, fs, f)
            elif key == "cepstre":
                self._tracer_cepstre(x, fs, f)
        except Exception as exc:                         # noqa: BLE001
            log.exception("Calcul de descripteur impossible")
            self.lecture.setText(f"<b>Calcul impossible :</b> {exc}")

    # -- les représentations apportées par les modules -----------------------
    def _modules_descripteurs(self):
        """Les modules active qui fournissent la capacité « descripteur »."""
        registre = getattr(self.engine, "modules", None)
        if registre is None:
            return []
        from ..api import Capability
        return registre.providers(Capability.DESCRIPTOR)

    def _tracer_module(self, key: str, x: np.ndarray, fs: float) -> None:
        """Dessine ce qu'un module rend — une ou plusieurs courbes.

        Rendu générique : abscisses, ordonnées, échelles, et l'warning
        sous la courbe. Un module qui veut davantage écrira sa propre lecture
        dans cet warning ; le jour où plusieurs le demanderont, l'API
        gagnera une capacité de rendu — pas avant.
        """
        m = self._descripteurs_de_modules.get(key)
        if m is None:
            self.lecture.setText(
                "<i>" + t("This module is no longer active.") + "</i>")
            return

        registre = self.engine.modules
        instance = m.instance
        #  Le module dit s'il veut le signal raw ; on le lui redemande, car
        #  celui qu'on a sous la main est celui de l'onglet.
        raw = bool(getattr(instance, "RAW_SIGNAL", False))
        fenetre = float(getattr(instance, "WINDOW_S", 60.0))
        signal = self.engine.recent(fenetre, raw=raw)
        if signal.size < 64:
            signal = x

        traces = registre.call(m, "describe", signal, fs, m.context,
                                  fallback=[])
        if not traces:
            self.lecture.setText(
                "<i>" + t("This module returned nothing for this signal.") + "</i>")
            return

        #  Plusieurs courbes : on prend la première et l'on dit qu'il y en a
        #  d'autres. Superposer des grandeurs d'unités différentes sur un même
        #  axe produirait un graphique qui ne veut rien dire.
        trace = traces[0]
        self.trace.y_label = t(trace.y_label) or "µV"
        self.trace.set_data(trace.x, trace.y)
        self._resultat = (key, trace.x, trace.y)

        rows = [f"<b>{t(trace.title)}</b>"]
        if trace.warning:
            rows.append(t(trace.warning))
        rows.append(
            f"<span style='color:{self.p['text2']}'>"
            + t("Provided by module « {name} » {version}").format(
                name=m.manifest.title, version=m.manifest.version)
            + "</span>")
        if len(traces) > 1:
            rows.append(
                f"<span style='color:{self.p['text2']}'>"
                + t("This module returns {n} representations; the first is shown.").format(n=len(traces)) + "</span>")
        self.lecture.setText("<br/>".join(rows))

    # -- les six tracés ------------------------------------------------------
    def _tracer_temporel(self, x: np.ndarray, fs: float) -> None:
        temps = np.arange(x.size) / fs
        self.trace.y_label = "µV"
        self.trace.set_data(temps, x * 1e6)
        self._resultat = ("temporel", temps, x)
        self.lecture.setText(_tableau([
            (t("Duration"), f"{x.size / fs:.1f} s"),
            (t("Rate after decimation"), f"{fs:.2f} Hz"),
            (t("Peak-to-peak amplitude"), f"{(x.max() - x.min()) * 1e6:.2f} µV"),
            (t("RMS value"), f"{np.std(x) * 1e6:.3f} µV"),
        ]))

    def _tracer_spectre(self, x: np.ndarray, fs: float, f) -> None:
        s = spectre_instantane(x, fs, f.fft_window, int(f.fft_zero_padding))
        kept = s.frequences_hz > 0
        self.trace.y_label = "dB (V)"
        self.trace.set_data(s.frequences_hz[kept], s.amplitude_db[kept])
        self._resultat = ("frequentiel", s.frequences_hz, s.amplitude)
        self.lecture.setText(_tableau([
            (t("Main peak"), t("{freq} at {amp:.2f} µV").format(
                freq=_hz(s.pic_hz), amp=s.pic_amplitude * 1e6)),
            (t("Resolution"), t("{mhz:.2f} mHz (= 1 / {duree:.0f} s)").format(
                mhz=s.resolution_hz * 1000, duree=s.duration_s)),
            (t("Windowing"), s.fenetre),
            (t("What the resolution forbids"),
             t("two lines closer than {mhz:.2f} mHz stay merged, whatever the zero padding").format(
                   mhz=s.resolution_hz * 1000)),
        ]))

    def _tracer_ondelettes(self, x: np.ndarray, fs: float, f) -> None:
        deci = int(f.wavelet_decimation) or max(int(x.size / 1200), 1)
        s = ondelettes_morlet(
            x, fs,
            f_min=f.wavelet_f_min_hz or None,
            f_max=f.wavelet_f_max_hz or None,
            n_echelles=int(f.wavelet_scales),
            omega0=float(f.wavelet_omega0),
            decimation=deci)
        if s.module.size == 0:
            self.lecture.setText("<i>Signal trop court pour une ondelette.</i>")
            return
        self.carte.y_label = t("frequency (Hz), geometric scale")
        self.carte.set_data(s.module_db, s.frequences_hz, 0.0,
                            float(s.temps_s[-1]) if s.temps_s.size else 0.0)
        self._resultat = ("ondelettes", s.frequences_hz, s.module)
        crete = s.ridge()
        i, j = np.unravel_index(int(np.argmax(s.module)), s.module.shape)
        self.lecture.setText(_tableau([
            (t("Energy maximum"), t("{freq} at t = {temps:.1f} s").format(
                freq=_hz(float(s.frequences_hz[i])), temps=float(s.temps_s[j]))),
            (t("Median ridge"), _hz(float(np.median(crete))) if crete.size else "—"),
            (t("Band explored"), t("{bas} → {haut} over {n} scales").format(
                bas=_hz(float(s.frequences_hz[0])),
                haut=_hz(float(s.frequences_hz[-1])),
                n=s.frequences_hz.size)),
            (t("Cone of influence"),
             t("the first and last {n:.0f} seconds of the low band are contaminated by the edges").format(
                   n=s.cone_influence_s.max())),
        ]))

    def _tracer_mfcc(self, x: np.ndarray, fs: float, f) -> None:
        s = mfcc(x, fs, n_coef=int(f.mfcc_count), n_filtres=int(f.mfcc_filters),
                 fenetre_s=float(f.mfcc_frame_s), recouvrement=float(f.mfcc_overlap))
        if s.spectre_mel_db.size == 0:
            self.lecture.setText("<i>Signal trop court pour une trame.</i>")
            return
        self.carte.y_label = t("mel filters (Hz)")
        self.carte.set_data(s.spectre_mel_db, s.frequences_mel_hz, 0.0,
                            float(s.temps_s[-1]) if s.temps_s.size else 0.0)
        self._resultat = ("mfcc", s.temps_s, s.coefficients)
        moy = s.moyenne()
        apercu = "  ".join(f"{v:+.2f}" for v in moy[:6]) if moy.size else "—"
        self.lecture.setText(_tableau([
            (t("Frames analysed"), t("{n} of {duree:g} s").format(
                n=s.coefficients.shape[0], duree=f.mfcc_frame_s)),
            (t("First six coefficients (mean)"), apercu),
            (t("Filter band"), t("{bas} → {haut}").format(
                bas=_hz(float(s.frequences_mel_hz[0])),
                haut=_hz(float(s.frequences_mel_hz[-1])))),
            (t("Honest use"), "comparer deux séquences entre elles ; "
                              "l'échelle de Mel décrit l'oreille humaine, "
                              "pas la plante"),
        ]))

    def _tracer_lpc(self, x: np.ndarray, fs: float, f) -> None:
        s = lpc(x, fs, order=int(f.lpc_order) or None)
        if s.frequences_hz.size == 0:
            self.lecture.setText("<i>Modèle impossible sur ce signal.</i>")
            return
        self.trace.y_label = "dB"
        self.trace.set_data(s.frequences_hz, s.enveloppe_db)
        self._resultat = ("lpc", s.frequences_hz, s.enveloppe_db)
        res = "  ".join(f"{v:.3f} Hz" for v in s.formants_hz[:5]) or t("none")
        self.lecture.setText(_tableau([
            (t("Model order"), t("{n} poles").format(n=s.order)),
            (t("Prediction gain"), f"{s.gain_prediction_db:.1f} dB"),
            (t("Resonances found"), res),
            (t("What this is not"), "des formants : une plante n'a pas de "
                                    "conduit vocal. Ces résonances sont celles "
                                    "de l'électrode, du milieu et de la carte"),
        ]))

    def _tracer_cepstre(self, x: np.ndarray, fs: float, f) -> None:
        s = cepstre(x, fs, q_min_s=f.cepstrum_q_min_s or None,
                    q_max_s=f.cepstrum_q_max_s or None)
        if s.quefrence_s.size == 0:
            self.lecture.setText("<i>Signal trop court.</i>")
            return
        self.trace.y_label = t("amplitude")
        self.trace.set_data(s.quefrence_s, s.cepstre)
        self._resultat = ("cepstre", s.quefrence_s, s.cepstre)
        periode = s.periode_detectee_s
        self.lecture.setText(_tableau([
            (t("Quefrency peak <i>(an anagram of “frequency”:<br>the abscissa of a cepstrum, in seconds)</i>"),
             f"{periode:.2f} s" if periode == periode else "—"),
            (t("Corresponding periodicity"),
             t("{freq} — that is one cycle every {periode:.1f} s").format(
                 freq=_hz(s.frequence_detectee_hz), periode=periode)
             if periode == periode else t("none")),
            (t("Peak height"), f"{s.pic_valeur:.4f}"),
            (t("A word of caution"), "un pic isolé sur un signal court n'est pas une "
                         "périodicité : il faut plusieurs répétitions dans la "
                         "fenêtre pour conclure"),
        ]))

    # -- export --------------------------------------------------------------
    def _exporter(self) -> None:
        if self._resultat is None:
            QMessageBox.information(self, t("Export"),
                                    t("Nothing has been computed yet."))
            return
        key, a, b = self._resultat
        path, _ = QFileDialog.getSaveFileName(
            self, t("Export the descriptor"), f"phytoscope-{key}.csv",
            t("Comma-separated values (*.csv)"))
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fic:
                fic.write(f"# PhytoScope — descripteur « {key} »\n")
                fic.write(f"# fenêtre {self._x_courant.size / max(self._fs_courant, 1e-9):.1f} s "
                          f"à {self._fs_courant:.3f} Hz\n")
                b = np.asarray(b)
                if b.ndim == 1:
                    fic.write("abscisse,value\n")
                    for u, v in zip(np.asarray(a).ravel(), b.ravel()):
                        fic.write(f"{u:.9g},{v:.9g}\n")
                else:
                    fic.write("ligne," + ",".join(f"c{i}" for i in
                                                  range(b.shape[1])) + "\n")
                    for i, ligne in enumerate(b):
                        fic.write(f"{i}," + ",".join(f"{v:.9g}" for v in ligne)
                                  + "\n")
        except OSError as exc:
            QMessageBox.warning(
                    self, t("Export"),
                    t("Cannot write: {erreur}").format(erreur=exc))
            return
        QMessageBox.information(
            self, t("Export"),
            t("Written to:\n{path}").format(
                path=os.path.abspath(path)))

    # -- appelé par la fenêtre principale ------------------------------------
    def refresh(self, state) -> None:
        self._calculer(force=False)


def _tableau(rows) -> str:
    corps = "".join(f"<tr><td><b>{k}</b></td><td>{v}</td></tr>"
                    for k, v in rows)
    return f"<table cellspacing='6'>{corps}</table>"


def _choisir(combo: QComboBox, value) -> None:
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return
