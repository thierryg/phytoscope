# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/plot_tab.py
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

"""Traceur — un gnuplot intégré, pour tracer autre chose que le signal raw.

Pourquoi imiter gnuplot ? Parce que c'est la langue commune des gens qui
tracent des courbes depuis quarante ans, parce qu'elle est concise, et
parce qu'un réglage tapé est un réglage qu'on peut noter, relire et
reproduire — ce qu'un clic ne permet pas.

L'onglet offre donc deux entrées équivalentes : un panneau de réglages pour
qui préfère la souris, et une ligne de commande pour qui préfère écrire.
Les deux agissent sur le même état, et le panneau se met à jour quand une
commande est tapée.

Commandes reconnues (sous-ensemble volontairement restreint) :

    plot <source> [with <style>] [title "..."]   trace une source
    replot                                       retrace tout
    clear                                        efface les courbes
    set title|xlabel|ylabel "..."                légendes
    set xrange [a:b] | set yrange [a:b]          bornes (« * » = automatique)
    set logscale x|y|xy   /  unset logscale      échelles logarithmiques
    set grid | unset grid                        grille
    set key on|off                               légende
    set style <style>                            style par défaut
    set samples <n>                              points maximum tracés
    set window <seconds>                        durée analysée
    export png|svg|dat|gp <file_path>              exportation
    help                                         aide

Sources disponibles : signal, raw, spectre, densite, histogramme,
autocorrelation, allan, events, bloc.

Motif de conception : *Command* — chaque instruction est un obj exécutable
enregistré dans une table, ce qui rend l'ajout d'une commande trivial.
"""
from __future__ import annotations

import math
import os
import re
import shlex
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog,
                               QFormLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPlainTextEdit,
                               QPushButton, QSpinBox, QSplitter, QVBoxLayout,
                               QWidget, QScrollArea)

from ..core import analysis
from ..core.dsp import decimate
from ..core.logging_setup import get_logger
from .widgets import HAVE_PYQTGRAPH, TracePlot
from ..i18n import t
from . import fonts

log = get_logger(__name__)

STYLES = ("lines", "points", "linespoints", "impulses", "steps", "dots", "boxes")

SOURCES: Dict[str, str] = {
    "signal": "filtered signal, against time",
    "raw": "signal before filtering",
    "spectre": "power spectral density (dB)",
    "densite": "amplitude density (V/√Hz)",
    "histogramme": "distribution of amplitudes",
    "autocorrelation": "normalised autocorrelation",
    "allan": "Allan deviation (stability)",
    "events": "amplitude of the detected events",
    "bloc": "last block from the sampler",
}


# ---------------------------------------------------------------------------
#  État du tracé
# ---------------------------------------------------------------------------
@dataclass
class PlotState:
    """Tout ce qui décrit le graphique — sérialisable en script gnuplot."""
    title: str = ""
    xlabel: str = "temps (s)"
    ylabel: str = "tension (V)"
    xrange: Tuple[Optional[float], Optional[float]] = (None, None)
    yrange: Tuple[Optional[float], Optional[float]] = (None, None)
    logx: bool = False
    logy: bool = False
    grid: bool = True
    key: bool = True
    style: str = "lines"
    samples: int = 4000
    window_s: float = 60.0
    courbes: List[Tuple[str, str, str]] = field(default_factory=list)  # source, style, title

    def to_gnuplot(self) -> str:
        """Script gnuplot équivalent — pour refaire la figure hors du logiciel."""
        rows = ["#!/usr/bin/env gnuplot",
                  "# Généré par PhytoScope — les données sont dans le .dat associé",
                  "set terminal pngcairo size 1200,700 font 'Lato,11'",
                  "set output 'figure.png'"]
        if self.title:
            rows.append(f'set title "{self.title}"')
        rows.append(f'set xlabel "{self.xlabel}"')
        rows.append(f'set ylabel "{self.ylabel}"')
        if self.logx:
            rows.append("set logscale x")
        if self.logy:
            rows.append("set logscale y")
        rows.append("set grid" if self.grid else "unset grid")
        rows.append("set key on" if self.key else "unset key")
        bornes = lambda r: (f"[{'*' if r[0] is None else r[0]}:"       # noqa: E731
                            f"{'*' if r[1] is None else r[1]}]")
        rows.append(f"set xrange {bornes(self.xrange)}")
        rows.append(f"set yrange {bornes(self.yrange)}")
        if self.courbes:
            morceaux = []
            for i, (source, style, title) in enumerate(self.courbes):
                morceaux.append(f"'donnees.dat' index {i} with {style} "
                                f"title \"{title or source}\"")
            rows.append("plot " + ", \\\n     ".join(morceaux))
        return "\n".join(rows) + "\n"


# ---------------------------------------------------------------------------
#  Interpréteur de commandes (motif Command)
# ---------------------------------------------------------------------------
class Interpreter:
    """Analyse et exécute les commandes ; ne connaît rien de Qt."""

    def __init__(self, state: PlotState, on_change: Callable[[], None],
                 on_export: Callable[[str, str], str]):
        self.state = state
        self.on_change = on_change
        self.on_export = on_export
        self.commandes: Dict[str, Callable[[List[str]], str]] = {
            "plot": self._plot, "replot": self._replot, "clear": self._clear,
            "set": self._set, "unset": self._unset, "export": self._export,
            "help": self._help, "?": self._help, "show": self._show,
        }

    def execute(self, ligne: str) -> str:
        ligne = (ligne or "").strip()
        if not ligne or ligne.startswith("#"):
            return ""
        try:
            jetons = shlex.split(ligne)
        except ValueError as exc:
            return f"erreur de syntaxe : {exc}"
        cmd = jetons[0].lower()
        fn = self.commandes.get(cmd)
        if fn is None:
            return (f"commande inconnue : « {cmd} ». "
                    "Tapez « help » pour la entries.")
        try:
            resultat = fn(jetons[1:])
        except Exception as exc:                       # noqa: BLE001
            log.exception("Commande « %s » en erreur", ligne)
            return f"erreur : {exc}"
        self.on_change()
        return resultat

    # -- commandes -----------------------------------------------------------
    def _plot(self, args: List[str]) -> str:
        if not args:
            return "usage : plot <source> [with <style>] [title \"...\"]"
        source = args[0].lower()
        if source not in SOURCES:
            return (f"source inconnue : « {source} ». Disponibles : "
                    + ", ".join(SOURCES))
        style = self.state.style
        title = ""
        i = 1
        while i < len(args):
            mot = args[i].lower()
            if mot == "with" and i + 1 < len(args):
                style = args[i + 1].lower()
                i += 2
            elif mot in ("title", "t") and i + 1 < len(args):
                title = args[i + 1]
                i += 2
            else:
                i += 1
        if style not in STYLES:
            return f"style inconnu : « {style} ». Disponibles : " + ", ".join(STYLES)
        self.state.courbes = [(source, style, title)]
        return f"tracé : {source} ({SOURCES[source]})"

    def _replot(self, _args: List[str]) -> str:
        return "retracé"

    def _clear(self, _args: List[str]) -> str:
        self.state.courbes.clear()
        return "courbes effacées"

    def _set(self, args: List[str]) -> str:
        if not args:
            return "usage : set <paramètre> <value>"
        key = args[0].lower()
        reste = args[1:]
        s = self.state
        if key == "title":
            s.title = " ".join(reste)
        elif key == "xlabel":
            s.xlabel = " ".join(reste)
        elif key == "ylabel":
            s.ylabel = " ".join(reste)
        elif key in ("xrange", "yrange"):
            bornes = self._bornes(" ".join(reste))
            if bornes is None:
                return "usage : set xrange [min:max]  (« * » pour automatique)"
            setattr(s, key, bornes)
        elif key == "logscale":
            axes = (reste[0].lower() if reste else "y")
            s.logx = "x" in axes
            s.logy = "y" in axes
        elif key == "grid":
            s.grid = True
        elif key == "key":
            s.key = not reste or reste[0].lower() not in ("off", "0", "no")
        elif key == "style":
            if not reste or reste[0].lower() not in STYLES:
                return "styles : " + ", ".join(STYLES)
            s.style = reste[0].lower()
        elif key == "samples":
            s.samples = max(int(float(reste[0])), 32)
        elif key == "window":
            s.window_s = max(float(reste[0]), 1.0)
        else:
            return f"paramètre inconnu : « {key} »"
        return f"{key} → {' '.join(reste) if reste else 'activé'}"

    def _unset(self, args: List[str]) -> str:
        if not args:
            return "usage : unset <paramètre>"
        key = args[0].lower()
        s = self.state
        if key == "logscale":
            s.logx = s.logy = False
        elif key == "grid":
            s.grid = False
        elif key == "key":
            s.key = False
        elif key == "title":
            s.title = ""
        elif key in ("xrange", "yrange"):
            setattr(s, key, (None, None))
        else:
            return f"paramètre inconnu : « {key} »"
        return f"{key} désactivé"

    def _export(self, args: List[str]) -> str:
        if len(args) < 2:
            return "usage : export png|svg|dat|gp <file_path>"
        return self.on_export(args[0].lower(), args[1])

    def _show(self, _args: List[str]) -> str:
        s = self.state
        return (f"style={s.style} samples={s.samples} window={s.window_s:g}s "
                f"logx={s.logx} logy={s.logy} grid={s.grid} key={s.key}")

    def _help(self, _args: List[str]) -> str:
        rows = ["Commandes :",
                  "  plot <source> [with <style>] [title \"...\"]",
                  "  replot | clear | show | help",
                  "  set title|xlabel|ylabel \"text\"",
                  "  set xrange [a:b] | set yrange [a:b]   (« * » = auto)",
                  "  set logscale x|y|xy | unset logscale",
                  "  set grid | unset grid | set key on|off",
                  "  set style <style> | set samples <n> | set window <s>",
                  "  export png|svg|dat|gp <file_path>",
                  "",
                  "Sources :"]
        rows += [f"  {k:<16} {v}" for k, v in SOURCES.items()]
        rows += ["", "Styles : " + ", ".join(STYLES)]
        return "\n".join(rows)

    @staticmethod
    def _bornes(text: str) -> Optional[Tuple[Optional[float], Optional[float]]]:
        m = re.match(r"^\s*\[?\s*([^:\]]*)\s*:\s*([^\]]*)\s*\]?\s*$", text or "")
        if not m:
            return None

        def read(v: str) -> Optional[float]:
            v = v.strip()
            if not v or v == "*":
                return None
            try:
                return float(v)
            except ValueError:
                return None
        return (read(m.group(1)), read(m.group(2)))


# ---------------------------------------------------------------------------
#  Onglet
# ---------------------------------------------------------------------------
class PlotTab(QWidget):
    """Traceur scientifique — panneau de réglages et ligne de commande."""

    def __init__(self, engine, palette: dict, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.state = PlotState()
        self.state.courbes = [("signal", "lines", "")]
        self._dernier: Optional[Tuple[np.ndarray, np.ndarray]] = None
        self.interp = Interpreter(self.state, self._appliquer_etat, self._exporter)

        self.plot = TracePlot(palette, "V")

        # --- panneau de réglages ------------------------------------------
        panneau = QWidget()
        pv = QVBoxLayout(panneau)
        pv.setContentsMargins(0, 0, 0, 0)

        gsrc = QGroupBox(t("Data"))
        f1 = QFormLayout(gsrc)
        self.cb_source = QComboBox()
        for k, v in SOURCES.items():
            self.cb_source.addItem(f"{k} — {t(v)}", k)
        self.cb_source.currentIndexChanged.connect(self._depuis_panneau)
        self.sp_window = QDoubleSpinBox()
        self.sp_window.setRange(1.0, 3600.0)
        self.sp_window.setValue(60.0)
        self.sp_window.setSuffix(t(" s"))
        self.sp_window.valueChanged.connect(self._depuis_panneau)
        self.sp_samples = QSpinBox()
        self.sp_samples.setRange(64, 200000)
        self.sp_samples.setValue(4000)
        self.sp_samples.valueChanged.connect(self._depuis_panneau)
        f1.addRow(t("Source"), self.cb_source)
        f1.addRow(t("Analysed duration"), self.sp_window)
        f1.addRow(t("Plotted points"), self.sp_samples)
        pv.addWidget(gsrc)

        gaff = QGroupBox(t("Display"))
        f2 = QFormLayout(gaff)
        self.cb_style = QComboBox()
        self.cb_style.addItems(STYLES)
        self.cb_style.currentIndexChanged.connect(self._depuis_panneau)
        self.chk_logx = QCheckBox(t("log scale on x"))
        self.chk_logy = QCheckBox(t("log scale on y"))
        self.chk_grid = QCheckBox(t("grid"))
        self.chk_grid.setChecked(True)
        self.chk_key = QCheckBox(t("key"))
        self.chk_key.setChecked(True)
        for c in (self.chk_logx, self.chk_logy, self.chk_grid, self.chk_key):
            c.stateChanged.connect(self._depuis_panneau)
        self.ed_title = QLineEdit()
        self.ed_title.editingFinished.connect(self._depuis_panneau)
        f2.addRow(t("Style"), self.cb_style)
        f2.addRow(t("Title"), self.ed_title)
        f2.addRow(self.chk_logx)
        f2.addRow(self.chk_logy)
        f2.addRow(self.chk_grid)
        f2.addRow(self.chk_key)
        pv.addWidget(gaff)

        gexp = QGroupBox(t("Export"))
        f3 = QVBoxLayout(gexp)
        for label, genre in ((t("PNG image…"), "png"), (t("SVG image…"), "svg"),
                               (t("Data (text)…"), "dat"),
                               (t("gnuplot script…"), "gp"),
                               (t("Measurement report…"), "report")):
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, g=genre: self._exporter_dialogue(g))
            f3.addWidget(b)
        pv.addWidget(gexp)

        self.lab_info = QLabel("")
        self.lab_info.setWordWrap(True)
        self.lab_info.setStyleSheet(f"color:{palette['text2']};font-size:8pt;")
        pv.addWidget(self.lab_info)
        pv.addStretch(1)

        # --- console -------------------------------------------------------
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setFont(fonts.mono(8))
        self.console.setMaximumHeight(130)
        self.console.setPlainText(
            "Traceur PhytoScope — tapez « help » pour la entries des commandes.\n")
        self.entree = QLineEdit()
        self.entree.setPlaceholderText(t("plot spectre with lines title \"bruit\""))
        self.entree.setFont(fonts.mono(9))
        self.entree.returnPressed.connect(self._commande)
        self._historique: List[str] = []
        self._h_index = 0

        gauche = QWidget()
        gl = QVBoxLayout(gauche)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.addWidget(self.plot, 1)
        gl.addWidget(self.console)
        ligne = QHBoxLayout()
        ligne.addWidget(QLabel(t("gnuplot>")))
        ligne.addWidget(self.entree, 1)
        gl.addLayout(ligne)

        #  Le panneau défile : c'est lui, sinon, qui fixe la hauteur minimale
        #  de toute la fenêtre.
        rouleau = QScrollArea()
        rouleau.setWidgetResizable(True)
        rouleau.setFrameShape(QScrollArea.NoFrame)
        rouleau.setWidget(panneau)
        split = QSplitter(Qt.Horizontal)
        split.addWidget(gauche)
        split.addWidget(rouleau)
        split.setSizes([900, 320])
        lay = QVBoxLayout(self)
        lay.addWidget(split)

        self._compteur = 0
        self._appliquer_etat()

    # -- passerelles panneau / commandes -------------------------------------
    def _depuis_panneau(self, *_):
        s = self.state
        source = self.cb_source.currentData()
        style = self.cb_style.currentText()
        s.courbes = [(source, style, "")]
        s.style = style
        s.window_s = self.sp_window.value()
        s.samples = self.sp_samples.value()
        s.logx = self.chk_logx.isChecked()
        s.logy = self.chk_logy.isChecked()
        s.grid = self.chk_grid.isChecked()
        s.key = self.chk_key.isChecked()
        s.title = self.ed_title.text()
        self._appliquer_etat()

    def _appliquer_etat(self) -> None:
        """Répercute l'état sur le panneau et sur le graphique."""
        s = self.state
        for widget, value, setter in (
                (self.sp_window, s.window_s, "setValue"),
                (self.sp_samples, s.samples, "setValue"),
                (self.chk_logx, s.logx, "setChecked"),
                (self.chk_logy, s.logy, "setChecked"),
                (self.chk_grid, s.grid, "setChecked"),
                (self.chk_key, s.key, "setChecked")):
            widget.blockSignals(True)
            getattr(widget, setter)(value)
            widget.blockSignals(False)
        if s.courbes:
            source = s.courbes[0][0]
            for i in range(self.cb_source.count()):
                if self.cb_source.itemData(i) == source:
                    self.cb_source.blockSignals(True)
                    self.cb_source.setCurrentIndex(i)
                    self.cb_source.blockSignals(False)
                    break
        self.refresh(self.engine.state, force=True)

    def _commande(self) -> None:
        ligne = self.entree.text()
        if not ligne.strip():
            return
        self.console.appendPlainText(f"> {ligne}")
        resultat = self.interp.execute(ligne)
        if resultat:
            self.console.appendPlainText(resultat)
        self._historique.append(ligne)
        self._h_index = len(self._historique)
        self.entree.clear()

    def keyPressEvent(self, event):                    # pragma: no cover
        if self.entree.hasFocus() and self._historique:
            if event.key() == Qt.Key_Up:
                self._h_index = max(0, self._h_index - 1)
                self.entree.setText(self._historique[self._h_index])
                return
            if event.key() == Qt.Key_Down:
                self._h_index = min(len(self._historique), self._h_index + 1)
                self.entree.setText(self._historique[self._h_index]
                                    if self._h_index < len(self._historique) else "")
                return
        super().keyPressEvent(event)

    # -- calcul des données --------------------------------------------------
    def _donnees(self, source: str) -> Tuple[np.ndarray, np.ndarray, str, str]:
        """Renvoie (x, y, libellé x, libellé y) pour la source demandée."""
        fs = self.engine.settings.acquisition.sample_rate
        s = self.state
        raw = source == "raw"

        if source in ("signal", "raw"):
            y = self.engine.recent(s.window_s, raw=raw)
            duree = y.size / max(fs, 1e-9)
            if y.size > s.samples:
                y = decimate(y, int(math.ceil(y.size / s.samples)))
            t_fin = self.engine.state.elapsed_s
            x = (np.linspace(max(t_fin - duree, 0.0), t_fin, y.size)
                 if y.size else y)
            return x, y, "temps (s)", "tension (V)"

        if source == "bloc":
            bloc = self.engine.sampler.last_block
            if bloc is None:
                return np.zeros(0), np.zeros(0), "temps (s)", "tension (V)"
            y = bloc.data
            x = np.arange(y.size) / max(bloc.sample_rate, 1e-9)
            return x, y, "temps dans le bloc (s)", "tension (V)"

        x_sig = self.engine.recent(s.window_s)
        if x_sig.size < 64:
            return np.zeros(0), np.zeros(0), "", ""

        if source in ("spectre", "densite"):
            sp = analysis.spectre(x_sig, fs, nperseg=min(8192, x_sig.size))
            if source == "spectre":
                y = 10 * np.log10(np.maximum(sp.psd_v2_hz, 1e-30))
                return sp.freqs, y, "frequency (Hz)", "densité (dB V²/Hz)"
            return sp.freqs, sp.asd_v_rthz, "frequency (Hz)", "densité (V/√Hz)"

        if source == "histogramme":
            centres, densite = analysis.histogramme(x_sig, bins=min(128, s.samples))
            return centres, densite, "tension (V)", "densité de probabilité"

        if source == "autocorrelation":
            lags, corr = analysis.autocorrelation(x_sig, fs,
                                                  max_lag_s=s.window_s / 4)
            return lags, corr, "décalage (s)", "corrélation"

        if source == "allan":
            res = analysis.allan_deviation(x_sig, fs)
            return res.taus, res.deviations, "durée d'intégration (s)", "σ(τ) (V)"

        if source == "events":
            rec = getattr(self.engine, "_evenements_recents", None)
            if not rec:
                return np.zeros(0), np.zeros(0), "temps (s)", "amplitude (V)"
            x = np.asarray([e.time_s for e in rec])
            y = np.asarray([e.amplitude_v for e in rec])
            return x, y, "temps (s)", "amplitude (V)"

        return np.zeros(0), np.zeros(0), "", ""

    # -- rendu ---------------------------------------------------------------
    def refresh(self, state, force: bool = False) -> None:
        self._compteur += 1
        if not force and self._compteur % 4:
            return
        if not self.state.courbes:
            return
        source, style, _titre = self.state.courbes[0]
        try:
            x, y, xl, yl = self._donnees(source)
        except Exception as exc:                       # noqa: BLE001
            log.exception("Calcul de la source « %s » impossible", source)
            self.lab_info.setText(t("error: {erreur}").format(erreur=exc))
            return
        if x.size == 0:
            self.lab_info.setText(t("not enough data yet"))
            return
        self._dernier = (x, y)
        s = self.state
        if s.xlabel in ("", "temps (s)"):
            s.xlabel = xl
        s.ylabel = yl
        if s.logy:
            y = np.log10(np.maximum(np.abs(y), 1e-30))
        if s.logx:
            kept = x > 0
            x, y = x[kept], y[kept]
        self.plot.set_data(x, y)
        if s.yrange[0] is not None and s.yrange[1] is not None:
            self.plot.set_y_range(s.yrange[0], s.yrange[1])
        else:
            self.plot.set_auto_range(True)
        self.lab_info.setText(
            f"{source} — {x.size} points · x ∈ [{x.min():.4g} ; {x.max():.4g}] "
            f"· y ∈ [{y.min():.4g} ; {y.max():.4g}]"
            + ("  (échelle log en y : values en log₁₀)" if s.logy else ""))

    # -- exportation ---------------------------------------------------------
    def _exporter_dialogue(self, genre: str) -> None:
        extensions = {"png": "Image PNG (*.png)", "svg": "Image SVG (*.svg)",
                      "dat": "Données (*.dat *.txt)", "gp": "Script gnuplot (*.gp)",
                      "report": "Rapport (*.txt)"}
        fallback = {"png": "figure.png", "svg": "figure.svg", "dat": "donnees.dat",
                  "gp": "figure.gp", "report": "report.txt"}
        path, _ = QFileDialog.getSaveFileName(
            self, t("Export"), fallback.get(genre, "output"),
            extensions.get(genre, "Tous (*)"))
        if not path:
            return
        message = self._exporter(genre, path)
        self.console.appendPlainText(message)

    def _exporter(self, genre: str, path: str) -> str:
        try:
            if genre == "gp":
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.state.to_gnuplot())
                dat = os.path.join(os.path.dirname(path) or ".", "donnees.dat")
                self._ecrire_dat(dat)
                return f"script écrit : {path} (et {os.path.basename(dat)})"
            if genre == "dat":
                self._ecrire_dat(path)
                return f"données écrites : {path}"
            if genre == "report":
                fs = self.engine.settings.acquisition.sample_rate
                x = self.engine.recent(self.state.window_s)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(analysis.rapport_complet(x, fs) + "\n")
                return f"report écrit : {path}"
            if genre in ("png", "svg"):
                return self._exporter_image(genre, path)
        except OSError as exc:
            log.error("Exportation impossible : %s", exc)
            return f"erreur d'écriture : {exc}"
        return f"format inconnu : {genre}"

    def _ecrire_dat(self, path: str) -> None:
        if self._dernier is None:
            raise OSError("aucune donnée à écrire")
        x, y = self._dernier
        s = self.state
        source = s.courbes[0][0] if s.courbes else "signal"
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# PhytoScope — source « {source} »\n")
            f.write(f"# {s.xlabel}\t{s.ylabel}\n")
            for a, b in zip(x.tolist(), y.tolist()):
                f.write(f"{a:.9g}\t{b:.9g}\n")

    def _exporter_image(self, genre: str, path: str) -> str:
        if HAVE_PYQTGRAPH and getattr(self.plot, "_pg_plot", None) is not None:
            try:
                import pyqtgraph.exporters as exporters
                if genre == "png":
                    exp = exporters.ImageExporter(self.plot._pg_plot.plotItem)
                    exp.parameters()["width"] = 1600
                else:
                    exp = exporters.SVGExporter(self.plot._pg_plot.plotItem)
                exp.export(path)
                return f"image écrite : {path}"
            except Exception as exc:                   # noqa: BLE001
                log.warning("Exporter pyqtgraph indisponible : %s", exc)
        pm = self.plot.grab()
        if pm.save(path):
            return f"image écrite : {path}"
        return "écriture de l'image impossible"
