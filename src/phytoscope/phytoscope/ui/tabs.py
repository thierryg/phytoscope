# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/tabs.py
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

"""Les quatre instruments : oscilloscope, multimètre, analyseur, écoute."""
from __future__ import annotations

import math
import os
from typing import List, Optional

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
                               QDoubleSpinBox, QFormLayout, QGridLayout,
                               QGroupBox, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QPushButton, QScrollArea,
                               QSlider, QSpinBox, QSplitter, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget)

from ..core.dsp import decimate, welch_psd
from ..music.instruments import instrument_list, get as get_instrument
from ..music.scales import (NOTE_NAMES_FR, build_notes, diapason_list,
                            ecart_cents, midi_to_hz, note_name, scale_names)
from .widgets import LevelBar, Readout, TracePlot, VuMetre
from ..i18n import t
from . import fonts


# ---------------------------------------------------------------------------
#  Oscilloscope
# ---------------------------------------------------------------------------
class ScopeTab(QWidget):
    """Le signal dans le temps — l'onglet qu'on regarde le plus."""

    WINDOWS = [(5, "5 s"), (15, "15 s"), (60, "1 min"), (300, "5 min"),
               (900, "15 min"), (3600, "1 h")]
    SENSITIVITIES = [(2e-6, "2 µV"), (10e-6, "10 µV"), (50e-6, "50 µV"),
                     (200e-6, "200 µV"), (1e-3, "1 mV"), (10e-3, "10 mV")]

    def __init__(self, engine, palette: dict, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.marks: List[float] = []

        self.plot = TracePlot(palette, "volts")
        self.level = LevelBar(palette)

        right = QVBoxLayout()
        box = QGroupBox(t("Quick settings"))
        form = QFormLayout(box)
        self.cb_window = QComboBox()
        for v, lab in self.WINDOWS:
            self.cb_window.addItem(lab, v)
        self.cb_window.setCurrentIndex(2)
        self.cb_window.currentIndexChanged.connect(self._apply_range)
        self.cb_sens = QComboBox()
        self.cb_sens.addItem(t("automatic"), 0.0)
        for v, lab in self.SENSITIVITIES:
            self.cb_sens.addItem(lab + " / div", v)
        self.cb_sens.currentIndexChanged.connect(self._apply_range)
        self.chk_raw = QCheckBox(t("raw signal (before filtering)"))
        self.chk_raw.setToolTip(t("Shows what really enters the converter: essential for diagnosis."))
        self.chk_baseline = QCheckBox(t("follow the baseline"))
        self.chk_baseline.setChecked(True)
        form.addRow(t("Window"), self.cb_window)
        form.addRow(t("Sensitivity"), self.cb_sens)
        form.addRow(self.chk_raw)
        form.addRow(self.chk_baseline)
        right.addWidget(box)

        stats = QGroupBox(t("Measurements"))
        g = QGridLayout(stats)
        self.r_value = Readout("INSTANTANÉ", "µV", palette)
        self.r_rms = Readout("EFFICACE (30 s)", "µV", palette)
        g.addWidget(self.r_value, 0, 0)
        g.addWidget(self.r_rms, 1, 0)
        right.addWidget(stats)

        marks = QGroupBox(t("Markers"))
        mv = QVBoxLayout(marks)
        for label in ("Début", "Contact", "Arrosage", "Speech", "Fin"):
            b = QPushButton(label)
            b.clicked.connect(lambda _=False, t=label: self._mark(t))
            mv.addWidget(b)
        right.addWidget(marks)
        right.addStretch(1)

        lay = QHBoxLayout(self)
        left = QVBoxLayout()
        left.addWidget(self.plot, 1)
        lv = QHBoxLayout()
        lv.addWidget(QLabel(t("input level")))
        lv.addWidget(self.level, 1)
        left.addLayout(lv)
        lay.addLayout(left, 1)
        lay.addWidget(_colonne_defilante(right))
        self._apply_range()

    def _apply_range(self) -> None:
        v = self.cb_sens.currentData()
        if v:
            self.plot.set_y_range(-v * 3, v * 3)
        else:
            self.plot.set_auto_range(True)

    def _mark(self, label: str) -> None:
        self.engine.mark(label)
        self.marks.append(self.engine.state.elapsed_s)
        self.plot.set_marks(self.marks)

    def refresh(self, state) -> None:
        window = float(self.cb_window.currentData())
        y = self.engine.recent(window, raw=self.chk_raw.isChecked())
        if y.size == 0:
            return
        fs = self.engine.settings.acquisition.sample_rate
        # La durée réellement disponible peut être plus courte que la fenêtre
        # demandée au début d'une séance : c'est elle qui fixe l'axe des temps,
        # sinon l'échelle ment tant que le tampon n'est pas rempli.
        duree = y.size / max(fs, 1e-9)
        maxpts = 4000
        if y.size > maxpts:
            y = decimate(y, int(math.ceil(y.size / maxpts)))
        t_fin = state.elapsed_s
        x = np.linspace(max(t_fin - duree, 0.0), t_fin, y.size)
        self.plot.set_data(x, y)
        self.r_value.set_value(f"{state.value_v * 1e6:+.1f}", state.saturated)
        self.r_rms.set_value(f"{state.rms_v * 1e6:.2f}")
        full = self.engine.settings.acquisition.input_range_v or 1.0
        self.level.set_value(abs(state.value_v + state.baseline_v) / full)


# ---------------------------------------------------------------------------
#  Multimètre
# ---------------------------------------------------------------------------
class MeterTab(QWidget):
    """Les chiffres — et les aiguilles qui en montrent le mouvement.

    Les deux ne font pas le même travail. Le nombre se recopie dans un carnet ;
    l'aiguille se lit d'un coup d'œil et se compare sans effort à sa voisine.
    Devant une plante, ce qu'on guette est un mouvement — une dérive qui
    s'installe, un bruit qui monte quand on touche le câble : c'est l'aiguille
    qui le donne. Les deux sont donc affichés, l'un sous l'autre.
    """

    def __init__(self, engine, palette: dict, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        lay = QVBoxLayout(self)
        haut = QWidget()
        haut_lay = QVBoxLayout(haut)
        haut_lay.setContentsMargins(0, 0, 0, 0)

        #  Quatre vumètres : la tension instantanée et la dérive sont signées
        #  — leur zéro est au milieu du cadran —, le bruit et l'amplitude
        #  crête à crête partent de zéro.
        self.vus = {}
        rang = QHBoxLayout()
        cadrans = (
            ("tension", t("VOLTAGE"), "µV", 100.0, True),
            ("efficace", t("RMS NOISE"), "µV", 50.0, False),
            ("crete", t("PEAK TO PEAK"), "µV", 200.0, False),
            ("derive", t("DRIFT"), "µV/min", 200.0, True),
        )
        for key, title, unite, maxi, signe in cadrans:
            vu = VuMetre(palette, title, unite, maximum=maxi, centre_zero=signe)
            self.vus[key] = vu
            rang.addWidget(vu)
        haut_lay.addLayout(rang)

        g = QGridLayout()
        self.readouts = {}
        #  Les six premiers sont instantanés ; les deux derniers sont calculés
        #  sur une fenêtre glissante, et n'apparaissent donc qu'au bout de
        #  quelques seconds de signal.
        fields = [("tension", "VOLTAGE", "µV"), ("efficace", "RMS NOISE", "µV"),
                  ("crete", "PEAK TO PEAK", "µV"), ("derive", "DRIFT", "µV/min"),
                  ("ligne", "LIGNE DE BASE", "mV"), ("events", "ÉVÉNEMENTS", ""),
                  ("resistance", "RÉSISTANCE ÉQUIV.", ""),
                  ("plancher", "PLANCHER DE BRUIT", "nV/√Hz"),
                  ("reseau", "RÉSEAU", "dB")]
        for i, (key, title, unit) in enumerate(fields):
            r = Readout(title, unit, palette)
            self.readouts[key] = r
            g.addWidget(r, i // 3, i % 3)
        self.readouts["resistance"].setToolTip(t(
            "An upper bound derived from Johnson-Nyquist thermal noise, not an ohmmeter reading: the source cannot be more resistive than this. It is its VARIATION that tells you something — a drying contact sends this number up by a decade."))
        self.readouts["plancher"].setToolTip(t(
            "Noise density of the chain, measured above the biological band. This is the rig's noise, not the plant's."))
        self.readouts["reseau"].setToolTip(t(
            "How far the mains rises above the noise floor, on the signal BEFORE the notch filter. Past 20 dB it is the shielding that needs attention: the notch hides the problem without solving it."))
        haut_lay.addLayout(g)

        box = QGroupBox(t("Impedance and contact"))
        form = QFormLayout(box)
        self.lab_impedance = QLabel(t("measurement unavailable on this source"))
        self.lab_contact = QLabel("—")
        self.btn_test = QPushButton(t("Run the board self-test"))
        self.btn_test.clicked.connect(self._self_test)
        form.addRow(t("Electrodes"), self.lab_impedance)
        form.addRow(t("Contact quality"), self.lab_contact)
        form.addRow(self.btn_test)
        haut_lay.addWidget(box)
        haut_lay.addStretch(1)

        #  En bas, deux pages : le log des mesures, et l'fingerprint du
        #  montage — qui n'identifie pas la plante, et le dit.
        bas = QTabWidget()
        self.log = QListWidget()
        self.log.setAlternatingRowColors(True)
        page_journal = QWidget()
        pj = QVBoxLayout(page_journal)
        pj.setContentsMargins(0, 0, 0, 0)
        pj.addWidget(self.log)
        bas.addTab(page_journal, t("Measurement log"))
        bas.addTab(self._page_empreinte(), t("Setup fingerprint"))
        bas.addTab(self._page_grandeurs(), t("Scientific quantities"))
        self._bas = bas
        self._prochain_calcul = 0.0

        #  Un séparateur mobile : sur un petit écran, l'utilisateur décide de
        #  ce qu'il veut voir en grand. Sans lui, les cadrans et les chiffres
        #  écrasent le bas de la page.
        #  Le haut défile plutôt que de se faire rogner : un afficheur
        #  numérique coupé en deux ne se lit pas, et c'est justement ce qu'on
        #  vient y chercher.
        rouleau_haut = QScrollArea()
        rouleau_haut.setWidgetResizable(True)
        rouleau_haut.setFrameShape(QScrollArea.NoFrame)
        rouleau_haut.setWidget(haut)
        partage = QSplitter(Qt.Vertical)
        partage.addWidget(rouleau_haut)
        partage.addWidget(bas)
        partage.setSizes([470, 300])
        partage.setStretchFactor(1, 1)
        lay.addWidget(partage, 1)

    # -- grandeurs scientifiques ---------------------------------------------
    def _page_grandeurs(self) -> QWidget:
        """Ce que les six grands nombres ne disent pas.

        Les afficheurs du haut donnent l'état du signal ; ils ne disent pas si
        la mesure vaut quelque chose. Cette page répond à la question suivante :
        d'où vient ce bruit, quelle résistance il suppose, jusqu'où l'on peut
        moyenner, et si un seuil en écarts-types a encore un meaning ici.
        """
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 0)

        entete = QLabel(t(
            "Computed every two seconds on the latest window of RAW signal — before the notch and the low-pass, otherwise you would be measuring your own filters rather than your rig. Each row states what the number says, and what it does not — hover over it to read the full explanation."))
        entete.setWordWrap(True)
        entete.setStyleSheet(f"color:{self.p['text2']};")
        lay.addWidget(entete)

        self.table_grandeurs = QTableWidget(0, 3)
        self.table_grandeurs.setHorizontalHeaderLabels(
            [t("Quantity"), t("Value"), t("What it tells you")])
        self.table_grandeurs.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_grandeurs.setAlternatingRowColors(True)
        self.table_grandeurs.verticalHeader().setVisible(False)
        self.table_grandeurs.setWordWrap(True)
        entetes = self.table_grandeurs.horizontalHeader()
        entetes.setStretchLastSection(True)
        lay.addWidget(self.table_grandeurs, 1)

        barre = QHBoxLayout()
        self.lab_fenetre_grandeurs = QLabel("—")
        self.lab_fenetre_grandeurs.setStyleSheet(f"color:{self.p['text2']};")
        self.btn_copier_grandeurs = QPushButton(t("Copy to the log"))
        self.btn_copier_grandeurs.setToolTip(
            t("Copies the current values into the measurement log, so they turn up in the session report."))
        self.btn_copier_grandeurs.clicked.connect(self._journaliser_grandeurs)
        barre.addWidget(self.lab_fenetre_grandeurs)
        barre.addStretch(1)
        barre.addWidget(self.btn_copier_grandeurs)
        lay.addLayout(barre)
        self._grandeurs = []
        self._duree_grandeurs = 0.0
        self._fs_grandeurs = 250.0
        return w

    def _fenetre_grandeurs(self) -> float:
        """Assez longue pour que 0,01 Hz ait un meaning, sans plomber l'affichage."""
        return 120.0

    def _calculer_grandeurs(self) -> None:
        """Interroge les modules qui fournissent la capacité « analyseur ».

        Le calcul ne vit plus ici : il est passé dans des modules, et cette
        page n'est qu'un afficheur. Ce qui change tout pour la suite — add
        une grandeur ne requested plus de toucher à l'interface, et un module
        écrit par quelqu'un d'autre s'y affiche de la même façon que les
        nôtres.
        """
        from ..api import Capability

        registre = getattr(self.engine, "modules", None)
        if registre is None:
            return
        providers = registre.providers(Capability.ANALYSER)
        if not providers:
            self.lab_fenetre_grandeurs.setText(
                t("No analysis module active — see the Diagnostics tab."))
            self._grandeurs = []
            self.table_grandeurs.setRowCount(0)
            return

        fs = float(self.engine.settings.acquisition.sample_rate)
        collectees = []
        duree_reelle = 0.0
        for m in providers:
            instance = m.instance
            fenetre = float(getattr(instance, "WINDOW_S", 120.0))
            #  Chaque module dit s'il veut le signal raw ou traité. Le raw
            #  pour tout ce qui mesure du bruit : filtrer avant de measure le
            #  bruit revient à measure son propre filtre (`C-1B`).
            raw = bool(getattr(instance, "RAW_SIGNAL", True))
            x = self.engine.recent(fenetre, raw=raw)
            if x.size < max(64, int(4 * fs)):
                continue
            duree_reelle = max(duree_reelle, x.size / fs)
            #  Sous protection : une fault désactive le module, pas la page.
            rendues = registre.call(m, "analyse", x, fs, m.context,
                                       fallback=[])
            for g in (rendues or []):
                collectees.append((m, g))

        if not collectees:
            self.lab_fenetre_grandeurs.setText(
                t("Waiting for signal — a few seconds are needed."))
            return

        self._grandeurs = collectees
        self._duree_grandeurs = duree_reelle
        self._fs_grandeurs = fs
        self._peindre_grandeurs()

    def _peindre_grandeurs(self) -> None:
        collectees = self._grandeurs
        if not collectees:
            return
        self.table_grandeurs.setRowCount(len(collectees))
        for i, (module, item) in enumerate(collectees):
            label = QTableWidgetItem(self._composer(item.label, item))
            value = QTableWidgetItem(item.text)
            value.setFont(fonts.mono())
            if item.alert:
                value.setForeground(QColor(self.p["alert"]))
            #  Un module qui ne dit pas ce que son nombre signifie est chargé
            #  quand même — mais cela se voit (`C-15`).
            phrase = (self._composer(item.meaning, item) if item.meaning
                      else t("(module « {name} » does not explain this value)").format(name=module.name))
            meaning = QTableWidgetItem(phrase)
            for col, cellule in enumerate((label, value, meaning)):
                cellule.setToolTip(f"{module.manifest.title} — {phrase}")
                self.table_grandeurs.setItem(i, col, cellule)
        self.table_grandeurs.resizeColumnsToContents()
        self.table_grandeurs.resizeRowsToContents()

        modules = sorted({m.manifest.title for m, _ in collectees})
        self.lab_fenetre_grandeurs.setText(
            t("Window: {duree:.0f} s at {fs:.0f} Hz — {modules}").format(
                duree=getattr(self, "_duree_grandeurs", 0.0),
                fs=getattr(self, "_fs_grandeurs", 250.0),
                modules=", ".join(modules)))

        #  Les trois afficheurs du haut se nourrissent du même calcul.
        par_cle = {g.key: g for _, g in collectees}
        r = self.readouts
        res = par_cle.get("resistance")
        if res is not None:
            text, _, unite = res.text.rpartition(" ")
            r["resistance"].set_value(text or "—", res.alert)
            r["resistance"].set_unit(unite if text else "")
        plancher = par_cle.get("plancher")
        if plancher is not None and plancher.value > 0:
            r["plancher"].set_value(f"{plancher.value * 1e9:.0f}")
        reseau = par_cle.get("reseau")
        if reseau is not None:
            r["reseau"].set_value(f"{reseau.value:+.0f}", reseau.alert)

    @staticmethod
    def _composer(gabarit: str, item) -> str:
        """Traduire, puis remplir les trous — jamais l'inverse.

        Les libellés des modules sont des GABARITS : « Écart d'Allan à {tau} s »
        et non « Écart d'Allan à 1 s ». Une phrase où le nombre est déjà
        incrusté ne peut pas entrer dans un catalogue de traduction.

        Les paramètres textuels — le régime de bruit, par exemple — sont eux
        aussi traduits : ce sont des mots, pas des nombres.
        """
        text = t(gabarit)
        params = getattr(item, "params", None) or {}
        if not params:
            return text
        values = {c: (t(v) if isinstance(v, str) and not v[:1].isdigit() else v)
                   for c, v in params.items()}
        try:
            return text.format(**values)
        except (KeyError, IndexError, ValueError):
            #  Une traduction dont les accolades ont été abîmées ne doit pas
            #  faire disparaître la ligne : on montre le français.
            try:
                return gabarit.format(**values)
            except (KeyError, IndexError, ValueError):
                return gabarit

    def _journaliser_grandeurs(self) -> None:
        if not self._grandeurs:
            self._calculer_grandeurs()
        if not self._grandeurs:
            return
        self._log("── " + t("Scientific quantities") +
                  f" ({getattr(self, '_duree_grandeurs', 0.0):.0f} s) ──")
        for module, item in self._grandeurs:
            self._log(f"   {self._composer(item.label, item)} : {item.text}")

    # -- fingerprint du montage ------------------------------------------------
    def _page_empreinte(self) -> QWidget:
        """Les descripteurs du montage, et les montages déjà connus."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 0)

        warning = QLabel(t(
            "⚠ This does not identify a plant. These are the descriptors of the setup — plant, electrodes, substrate, cable, board — as it is right now. Two measurements of the same plant two days apart often differ more than two neighbouring plants on the same afternoon."))
        warning.setWordWrap(True)
        warning.setStyleSheet(
            f"color:{self.p['gold']};border:1px solid {self.p['gold']};"
            f"border-radius:4px;padding:6px;")
        lay.addWidget(warning)

        corps = QHBoxLayout()
        self.table_empreinte = QTableWidget(0, 2)
        self.table_empreinte.setHorizontalHeaderLabels([t("Descriptor"), t("Value")])
        self.table_empreinte.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_empreinte.setAlternatingRowColors(True)
        self.table_empreinte.verticalHeader().setVisible(False)
        self.table_empreinte.horizontalHeader().setStretchLastSection(True)
        corps.addWidget(self.table_empreinte, 3)

        self.liste_montages = QListWidget()
        self.liste_montages.setAlternatingRowColors(True)
        droite = QVBoxLayout()
        droite.addWidget(QLabel(t("Known setups, by resemblance")))
        droite.addWidget(self.liste_montages, 1)
        corps.addLayout(droite, 4)
        lay.addLayout(corps, 1)

        barre = QHBoxLayout()
        self.btn_empreinte = QPushButton(t("Compute the fingerprint"))
        self.btn_empreinte.setToolTip(
            t("Analyses the last two minutes of signal held in memory."))
        self.btn_empreinte.clicked.connect(self._calculer_empreinte)
        self.btn_retenir = QPushButton(t("Remember this setup…"))
        self.btn_retenir.clicked.connect(self._retenir_montage)
        self.btn_oublier = QPushButton(t("Forget"))
        self.btn_oublier.clicked.connect(self._oublier_montage)
        barre.addWidget(self.btn_empreinte)
        barre.addStretch(1)
        barre.addWidget(self.btn_retenir)
        barre.addWidget(self.btn_oublier)
        lay.addLayout(barre)
        self._empreinte = None
        return w

    def _registre(self):
        from ..config import config_dir
        from ..core.fingerprint import Registry
        if getattr(self, "_reg", None) is None:
            self._reg = Registry(os.path.join(config_dir(), "montages.json"))
        return self._reg

    def _calculer_empreinte(self) -> None:
        from ..core import fingerprint as emp
        x = self.engine.recent(120.0)
        if x.size < 64:
            self._log(t("Not enough signal yet for a fingerprint."))
            return
        fs = float(self.engine.settings.acquisition.sample_rate)
        instants = [t_ev for t_ev in getattr(self.engine, "_evenements_recents", [])
                    if self.engine.state.elapsed_s - t_ev <= x.size / fs]
        self._empreinte = emp.compute(
            x, fs, instants, name=self.engine.settings.metadata.get("plante", ""),
            metadata={"source": self.engine.state.source_name})

        rows = self._empreinte.rows()
        self.table_empreinte.setRowCount(len(rows))
        for i, (label, value) in enumerate(rows):
            self.table_empreinte.setItem(i, 0, QTableWidgetItem(t(label)))
            self.table_empreinte.setItem(i, 1, QTableWidgetItem(value))
        self.table_empreinte.resizeColumnsToContents()

        self.liste_montages.clear()
        for connu, score in self._registre().recognise(self._empreinte):
            self.liste_montages.addItem(
                f"{score * 100:5.1f} %   {connu.name}   —   {t(emp.qualify(score))}")
        if not self.liste_montages.count():
            self.liste_montages.addItem(
                t("No setup remembered yet. “Remember this setup…” keeps one."))

    def _retenir_montage(self) -> None:
        from PySide6.QtWidgets import QInputDialog
        if self._empreinte is None:
            self._calculer_empreinte()
        if self._empreinte is None:
            return
        fallback = self._empreinte.name or self.engine.settings.metadata.get("plante", "")
        name, ok = QInputDialog.getText(self, t("Remember this setup"),
                                       t("Under what name?"), text=fallback)
        if not ok or not name.strip():
            return
        self._empreinte.name = name.strip()
        self._registre().add(self._empreinte)
        self._log(t("Setup remembered: {name}").format(name=name.strip()))
        self._calculer_empreinte()

    def _oublier_montage(self) -> None:
        item = self.liste_montages.currentItem()
        if item is None:
            return
        text = item.text()
        if "—" not in text or "%" not in text:
            return
        name = text.split("%", 1)[1].split("—")[0].strip()
        self._registre().remove(name)
        self._log(t("Setup forgotten: {name}").format(name=name))
        self._calculer_empreinte()

    def _self_test(self) -> None:
        rep = self.engine.control.self_test()
        if rep is None:
            self._log("Auto-test indisponible : aucune carte PhytoSense connectée.")
            return
        for line in rep.summary_lines():
            self._log(line)

    def _log(self, text: str) -> None:
        self.log.insertItem(0, text)
        while self.log.count() > 300:
            self.log.takeItem(self.log.count() - 1)

    def refresh(self, state) -> None:
        #  Les aiguilles d'abord : elles amortissent elles-mêmes, il suffit de
        #  leur donner la value brute à chaque rafraîchissement.
        self.vus["tension"].set_value(state.value_v * 1e6)
        self.vus["efficace"].set_value(state.rms_v * 1e6)
        self.vus["crete"].set_value(state.pp_v * 1e6)
        self.vus["derive"].set_value(state.drift_v_per_min * 1e6)

        r = self.readouts
        r["tension"].set_value(f"{state.value_v * 1e6:+.1f}", state.saturated)
        r["efficace"].set_value(f"{state.rms_v * 1e6:.2f}")
        r["crete"].set_value(f"{state.pp_v * 1e6:.1f}")
        r["derive"].set_value(f"{state.drift_v_per_min * 1e6:+.1f}")
        r["ligne"].set_value(f"{state.baseline_v * 1e3:+.3f}")
        r["events"].set_value(str(state.events_total))
        # qualité du contact : déduite du bruit et de la dérive
        noise = state.rms_v * 1e6
        drift = abs(state.drift_v_per_min) * 1e6
        if state.saturated:
            txt, ok = "saturation — vérifier le gain ou une électrode débranchée", False
        elif noise > 60:
            txt, ok = "bruit élevé — contact sec ou blindage absent", False
        elif drift > 400:
            txt, ok = "dérive forte — l'électrode se stabilise encore", False
        elif noise < 3:
            txt, ok = "excellent", True
        else:
            txt, ok = "correct", True
        self.lab_contact.setText(txt)
        self.lab_contact.setStyleSheet(
            f"color:{self.p['trace'] if ok else self.p['alert']};font-weight:bold;")

        #  Les grandeurs scientifiques coûtent quelques millisecondes : on les
        #  recalcule toutes les deux seconds, et seulement quand leur page est
        #  sous les yeux — inutile de faire tourner une FFT pour personne.
        maintenant = state.elapsed_s
        if maintenant >= self._prochain_calcul:
            self._prochain_calcul = maintenant + 2.0
            if self.isVisible() and self._bas.currentIndex() == 2:
                self._calculer_grandeurs()


# ---------------------------------------------------------------------------
#  Analyser de spectre
# ---------------------------------------------------------------------------
class SpectrumTab(QWidget):
    """Le spectre — où l'on voit tout de suite si le réseau parasite la mesure."""

    def __init__(self, engine, palette: dict, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.plot = TracePlot(palette, "dB (V²/Hz)")
        self.plot.set_pen_color(palette["trace2"])

        ctl = QHBoxLayout()
        self.cb_window = QComboBox()
        for v, lab in ((30, t("30 s")), (60, t("1 min")), (300, t("5 min"))):
            self.cb_window.addItem(lab, v)
        self.cb_window.setCurrentIndex(1)
        self.chk_log = QCheckBox(t("logarithmic scale"))
        self.chk_log.setChecked(True)
        self.lab_mains = QLabel("—")
        ctl.addWidget(QLabel(t("Analysed duration")))
        ctl.addWidget(self.cb_window)
        ctl.addWidget(self.chk_log)
        ctl.addStretch(1)
        ctl.addWidget(QLabel(t("Mains:")))
        ctl.addWidget(self.lab_mains)

        lay = QVBoxLayout(self)
        lay.addLayout(ctl)
        lay.addWidget(self.plot, 1)
        self.info = QLabel(
            t("A peak at 50 Hz means the setup is picking up the mains: check the shielding, the guard and the ground before enabling the notch."))
        self.info.setWordWrap(True)
        self.info.setStyleSheet(f"color:{palette['text2']};")
        lay.addWidget(self.info)
        self._count = 0

    def refresh(self, state) -> None:
        self._count += 1
        if self._count % 6:                # le spectre n'a pas besoin de 30 im/s
            return
        fs = self.engine.settings.acquisition.sample_rate
        x = self.engine.recent(float(self.cb_window.currentData()))
        if x.size < 256:
            return
        f, p = welch_psd(x, fs, nperseg=min(2048, x.size))
        if self.chk_log.isChecked():
            y = 10 * np.log10(np.maximum(p, 1e-30))
        else:
            y = p
        self.plot.set_data(f, y)
        from ..core.dsp import dominant_mains
        m = dominant_mains(x, fs)
        self.lab_mains.setText(f"{m:g} Hz détecté" if m else "non détecté")
        self.lab_mains.setStyleSheet(
            f"color:{self.p['alert'] if m else self.p['trace']};font-weight:bold;")


# ---------------------------------------------------------------------------
#  Écoute
# ---------------------------------------------------------------------------
class ListenTab(QWidget):
    """Le choix musical — et le log de ce qui a été joué."""

    def __init__(self, engine, palette: dict, on_change, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.on_change = on_change
        m = engine.settings.music

        lay = QHBoxLayout(self)
        left = QVBoxLayout()

        box = QGroupBox(t("Instrument"))
        form = QFormLayout(box)
        self.cb_instrument = QComboBox()
        for key, label in instrument_list():
            self.cb_instrument.addItem(t(label), key)
        _select(self.cb_instrument, m.instrument)
        self.cb_instrument.currentIndexChanged.connect(self._changed)
        self.lab_desc = QLabel("")
        self.lab_desc.setWordWrap(True)
        self.lab_desc.setStyleSheet(f"color:{palette['text2']};")
        form.addRow(t("Timbre"), self.cb_instrument)
        form.addRow(self.lab_desc)
        left.addWidget(box)

        box2 = QGroupBox(t("Scale"))
        f2 = QFormLayout(box2)
        self.cb_scale = QComboBox()
        for key, label in scale_names():
            self.cb_scale.addItem(t(label), key)
        _select(self.cb_scale, m.scale)
        self.cb_scale.currentIndexChanged.connect(self._changed)
        self.cb_root = QComboBox()
        for n in NOTE_NAMES_FR:
            self.cb_root.addItem(n, n)
        _select(self.cb_root, m.root, by_text=True)
        self.cb_root.currentIndexChanged.connect(self._changed)
        self.sp_octave = QSpinBox()
        self.sp_octave.setRange(0, 7)
        self.sp_octave.setValue(m.octave_low)
        self.sp_octave.valueChanged.connect(self._changed)
        self.sp_span = QSpinBox()
        self.sp_span.setRange(1, 5)
        self.sp_span.setValue(m.octave_span)
        self.sp_span.valueChanged.connect(self._changed)
        f2.addRow(t("Scale"), self.cb_scale)
        f2.addRow(t("Root"), self.cb_root)
        f2.addRow(t("Low octave"), self.sp_octave)
        f2.addRow(t("Range (octaves)"), self.sp_span)
        left.addWidget(box2)

        box3 = QGroupBox(t("Playing"))
        f3 = QFormLayout(box3)
        self.sl_density = _slider(1, 120, int(m.density_per_min), self._changed)
        self.sl_reverb = _slider(0, 100, int(m.reverb * 100), self._changed)
        self.sl_gain = _slider(-40, 6, int(m.master_gain_db), self._changed)
        self.chk_drone = QCheckBox(t("drone on the root"))
        self.chk_drone.setChecked(m.drone_enabled)
        self.chk_drone.stateChanged.connect(self._changed)
        self.chk_mute = QCheckBox(t("mute (keep detection)"))
        self.chk_mute.stateChanged.connect(self._changed)
        f3.addRow(t("Density (notes/min)"), self.sl_density)
        f3.addRow(t("Reverb"), self.sl_reverb)
        f3.addRow(t("Volume (dB)"), self.sl_gain)
        f3.addRow(self.chk_drone)
        f3.addRow(self.chk_mute)
        left.addWidget(box3)
        left.addStretch(1)
        lay.addLayout(left)

        # --- colonne de droite : ce qui est joué, et pourquoi --------------
        droite = QTabWidget()

        page_notes = QWidget()
        pn = QVBoxLayout(page_notes)
        pn.addWidget(QLabel(t("Notes played (most recent first)")))
        self.list_notes = QListWidget()
        self.list_notes.setAlternatingRowColors(True)
        self.list_notes.setFont(fonts.mono(8))
        pn.addWidget(self.list_notes, 1)
        self.lab_rules = QLabel("")
        self.lab_rules.setWordWrap(True)
        self.lab_rules.setStyleSheet(f"color:{palette['text2']};font-size:8pt;")
        pn.addWidget(self.lab_rules)
        droite.addTab(page_notes, t("Log"))

        page_gamme = QWidget()
        pg = QVBoxLayout(page_gamme)
        self.lab_gamme = QLabel("")
        self.lab_gamme.setWordWrap(True)
        self.lab_gamme.setStyleSheet(f"color:{palette['gold']};font-weight:bold;")
        pg.addWidget(self.lab_gamme)
        self.table_notes = QTableWidget(0, 5)
        self.table_notes.setHorizontalHeaderLabels(
            [t("Degree"), t("Note"), t("MIDI"), t("Frequency"), t("Deviation / 440 Hz")])
        self.table_notes.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_notes.setAlternatingRowColors(True)
        self.table_notes.setFont(fonts.mono(8))
        pg.addWidget(self.table_notes, 1)
        droite.addTab(page_gamme, t("Scale and frequencies"))

        page_sci = QWidget()
        ps = QVBoxLayout(page_sci)
        self.lab_sci = QLabel("")
        self.lab_sci.setWordWrap(True)
        self.lab_sci.setTextFormat(Qt.RichText)
        ps.addWidget(self.lab_sci)
        ps.addStretch(1)
        droite.addTab(page_sci, t("Measured quantities"))

        lay.addWidget(droite, 1)
        self._changed()
        self._remplir_gamme()

    def _changed(self, *_):
        m = self.engine.settings.music
        m.instrument = self.cb_instrument.currentData()
        m.scale = self.cb_scale.currentData()
        m.root = self.cb_root.currentData()
        m.octave_low = self.sp_octave.value()
        m.octave_span = self.sp_span.value()
        m.density_per_min = float(self.sl_density.value())
        m.reverb = self.sl_reverb.value() / 100.0
        m.master_gain_db = float(self.sl_gain.value())
        m.drone_enabled = self.chk_drone.isChecked()
        m.enabled = not self.chk_mute.isChecked()
        self.lab_desc.setText(t(get_instrument(m.instrument).description))
        self.lab_rules.setText("\n".join(self.engine.mapper.describe_rules()))
        if self.on_change:
            self.on_change()

    # -- tableau de la gamme -------------------------------------------------
    def _remplir_gamme(self) -> None:
        """Affiche les notes disponibles, leur fréquence et leur écart.

        C'est le tableau qui manque à tous les appareils du commerce : il
        permet de vérifier à l'oreille et au fréquencemètre que la note
        annoncée est bien celle qui sort.
        """
        m = self.engine.settings.music
        diapason = float(getattr(m, "diapason_hz", 440.0))
        notes = build_notes(m.scale, m.root, m.octave_low, m.octave_span)
        self.lab_gamme.setText(
            t("{gamme} on {note} — concert pitch {diapason:g} Hz — {n} notes, {etendue} octave(s) from octave {basse}").format(
                  gamme=m.scale, note=m.root, diapason=diapason,
                  n=len(notes), etendue=m.octave_span, basse=m.octave_low))
        self.table_notes.setRowCount(len(notes))
        for i, midi in enumerate(notes):
            f = midi_to_hz(midi, diapason)
            ecart = ecart_cents(f, midi, 440.0)
            cellules = (str(i + 1), note_name(midi), str(midi),
                        f"{f:9.3f} Hz", f"{ecart:+6.1f} cents")
            for j, text in enumerate(cellules):
                self.table_notes.setItem(i, j, QTableWidgetItem(text))
        self.table_notes.resizeColumnsToContents()

    def recharger(self) -> None:
        """Resynchronise les commandes depuis les réglages (appel extérieur)."""
        m = self.engine.settings.music
        for combo, value in ((self.cb_instrument, m.instrument),
                              (self.cb_scale, m.scale)):
            combo.blockSignals(True)
            _select(combo, value)
            combo.blockSignals(False)
        self.cb_root.blockSignals(True)
        _select(self.cb_root, m.root, by_text=True)
        self.cb_root.blockSignals(False)
        for widget, value in ((self.sp_octave, m.octave_low),
                               (self.sp_span, m.octave_span),
                               (self.sl_density, int(m.density_per_min)),
                               (self.sl_reverb, int(m.reverb * 100)),
                               (self.sl_gain, int(m.master_gain_db))):
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)
        self.lab_desc.setText(t(get_instrument(m.instrument).description))
        self.lab_rules.setText("\n".join(self.engine.mapper.describe_rules()))
        self._remplir_gamme()

    def add_note(self, note) -> None:
        #  Une ligne de tableau à colonnes fixes : seule l'abréviation est
        #  de la prose. Traduire la ligne entière casserait l'alignement.
        self.list_notes.insertItem(
            0, f"{note.time_s:8.1f} s   {note.name():<6}  "
               f"{t('vel.')} {note.velocity:3d}   "
               f"{note.duration:.1f} s   [{note.reason}]")
        while self.list_notes.count() > 400:
            self.list_notes.takeItem(self.list_notes.count() - 1)

    def refresh(self, state) -> None:
        """Met à jour les grandeurs scientifiques affichées."""
        m = self.engine.settings.music
        p = self.engine.settings.processing
        diapason = float(getattr(m, "diapason_hz", 440.0))
        derniere = state.last_note
        if derniere is not None:
            f = midi_to_hz(derniere.midi, diapason)
            note_txt = (f"{derniere.name()} — {f:.2f} Hz — "
                        f"MIDI {derniere.midi} — vélocité {derniere.velocity}")
        else:
            note_txt = "aucune note encore jouée"
        seuil_v = max(p.event_threshold_sigma * state.sigma_v,
                      p.event_min_amplitude_uv * 1e-6)
        taux = (state.events_total / max(state.elapsed_s, 1e-9)) * 60.0
        self.lab_sci.setText(f"""
        <table cellspacing='5'>
        <tr><td><b>Dernière note</b></td><td>{note_txt}</td></tr>
        <tr><td><b>Diapason</b></td><td>{diapason:g} Hz</td></tr>
        <tr><td><b>Polyphonie</b></td><td>{m.polyphony_voices} voix
            ({self.engine.synth.active_voices} active(s))</td></tr>
        <tr><td colspan='2'><hr></td></tr>
        <tr><td><b>Tension instantanée</b></td>
            <td>{state.value_v * 1e6:+.2f} µV</td></tr>
        <tr><td><b>Bruit efficace (30 s)</b></td>
            <td>{state.rms_v * 1e6:.3f} µV</td></tr>
        <tr><td><b>Écart-type courant</b></td>
            <td>{state.sigma_v * 1e6:.3f} µV</td></tr>
        <tr><td><b>Seuil de déclenchement</b></td>
            <td>{seuil_v * 1e6:.2f} µV ({p.event_threshold_sigma:g} σ)</td></tr>
        <tr><td><b>Dérive</b></td>
            <td>{state.drift_v_per_min * 1e6:+.1f} µV/min</td></tr>
        <tr><td><b>Ligne de base</b></td>
            <td>{state.baseline_v * 1e3:+.4f} mV</td></tr>
        <tr><td colspan='2'><hr></td></tr>
        <tr><td><b>Événements</b></td>
            <td>{state.events_total} — soit {taux:.1f} par minute</td></tr>
        <tr><td><b>Notes jouées</b></td><td>{state.notes_total}</td></tr>
        <tr><td><b>Rendement</b></td>
            <td>{(100.0 * state.notes_total / max(state.events_total, 1)):.0f} %
            des événements deviennent une note</td></tr>
        <tr><td><b>Sortie audio</b></td>
            <td>crête {state.audio_peak_db:+.1f} dB ·
            réduction {state.audio_reduction_db:+.1f} dB</td></tr>
        </table>""")


def _colonne_defilante(disposition, largeur: int = 260) -> QScrollArea:
    """Met une colonne de commandes dans une zone défilante.

    Une colonne haute impose sinon sa hauteur à toute la fenêtre, qu'on ne peut
    alors plus réduire sous la taille de l'écran — le défaut est invisible sur
    un grand moniteur et bloquant sur un portable.
    """
    contenu = QWidget()
    contenu.setLayout(disposition)
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QScrollArea.NoFrame)
    sa.setWidget(contenu)
    sa.setMinimumWidth(largeur)
    sa.setMaximumWidth(largeur + 120)
    return sa


def _slider(lo: int, hi: int, value: int, cb) -> QSlider:
    s = QSlider(Qt.Horizontal)
    s.setRange(lo, hi)
    s.setValue(value)
    s.valueChanged.connect(cb)
    return s


def _select(combo: QComboBox, value, by_text: bool = False) -> None:
    for i in range(combo.count()):
        if (combo.itemText(i) if by_text else combo.itemData(i)) == value:
            combo.setCurrentIndex(i)
            return
