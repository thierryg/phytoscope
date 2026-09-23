# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/library_tab.py
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

"""Bibliothèque : retrouver, relire et exporter — séances et échantillons.

Deux choses s'y gardent, et elles ne se ressemblent pas.

**Une séance** est un engagement : on la décide, elle dure, elle produit un
répertoire complet — signal, rendu musical, événements, notes, marqueurs,
réglages. C'est la pièce d'archive.

**Un échantillon** est un réflexe : la plante vient de faire quelque chose, on
appuie sur un bouton, et la minute écoulée est sauvée. Un fichier, pas un
répertoire ; quelques secondes, pas des heures. C'est le carnet de croquis.

Les deux se **rejouent dans le moteur** plutôt que de s'afficher en courbe :
filtres, détection, descripteurs, musique et mode vocal fonctionnent alors
exactement comme devant une plante vivante. C'est ce qui permet de régler une
sonification tranquillement, le soir, sur la séance du matin.
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import List, Optional

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog,
                               QHBoxLayout, QInputDialog, QLabel, QMessageBox,
                               QPlainTextEdit, QPushButton, QSplitter,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from ..core import samples
from ..core import session as sess
from ..core.dsp import decimate
from ..i18n import t
from .widgets import TracePlot


class LibraryTab(QWidget):
    """La mémoire du logiciel — sans elle, une séance n'existe pas."""

    def __init__(self, engine, palette: dict, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.refs: List[sess.SessionRef] = []
        self.echantillons: List[samples.EchantillonRef] = []
        self.current: Optional[sess.SessionRef] = None
        self.courant_ech: Optional[samples.EchantillonRef] = None

        # --- barre commune ---------------------------------------------------
        top = QHBoxLayout()
        self.btn_reload = QPushButton(t("Refresh"))
        self.btn_reload.clicked.connect(self.reload)
        self.btn_open = QPushButton(t("Open the folder"))
        self.btn_open.clicked.connect(self._open_folder)
        self.btn_charger = QPushButton(t("Load a recording…"))
        self.btn_charger.setToolTip(
            t("Replays a file taken from anywhere: a sample, the signal.wav of a session, or any WAV. While replaying, live acquisition is suspended."))
        self.btn_charger.clicked.connect(self._charger_fichier)
        self.cb_speed = QComboBox()
        for v, lab in ((1, t("×1 (real time)")), (10, t("×10")), (60, t("×60")),
                       (600, t("×600"))):
            self.cb_speed.addItem(lab, v)
        self.btn_play = QPushButton(t("Replay"))
        self.btn_play.setCheckable(True)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_live = QPushButton(t("Back to live"))
        self.btn_live.setToolTip(
            t("Closes the replay and hands control back to the connected plant."))
        self.btn_live.clicked.connect(self._revenir_en_direct)
        top.addWidget(self.btn_reload)
        top.addWidget(self.btn_open)
        top.addWidget(self.btn_charger)
        top.addStretch(1)
        top.addWidget(QLabel(t("Replay speed")))
        top.addWidget(self.cb_speed)
        top.addWidget(self.btn_play)
        top.addWidget(self.btn_live)

        # --- page des séances ------------------------------------------------
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            [t("Date"), t("Plant"), t("Duration"), t("Events"), t("Notes"),
             t("Folder")])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.itemSelectionChanged.connect(self._selected)
        self.table.setAlternatingRowColors(True)

        self.btn_export = QPushButton(t("Export the summary…"))
        self.btn_export.clicked.connect(self._export)
        bas_seances = QHBoxLayout()
        bas_seances.addStretch(1)
        bas_seances.addWidget(self.btn_export)

        page_seances = QWidget()
        ps = QVBoxLayout(page_seances)
        ps.setContentsMargins(0, 0, 0, 0)
        ps.addWidget(self.table, 1)
        ps.addLayout(bas_seances)

        # --- page des échantillons -------------------------------------------
        self.table_ech = QTableWidget(0, 6)
        self.table_ech.setHorizontalHeaderLabels(
            [t("Date"), t("Duration"), t("Plant"), t("Rate"), t("Full scale"),
             t("File")])
        self.table_ech.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_ech.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_ech.itemSelectionChanged.connect(self._selection_echantillon)
        self.table_ech.setAlternatingRowColors(True)

        self.btn_capturer = QPushButton(t("⧉ Capture now"))
        self.btn_capturer.setToolTip(
            t("Keeps the signal that has just gone by — the same as Ctrl+E in the toolbar."))
        self.btn_capturer.clicked.connect(self._capturer)
        self.btn_renommer = QPushButton(t("Rename…"))
        self.btn_renommer.clicked.connect(self._renommer)
        self.btn_supprimer = QPushButton(t("Delete"))
        self.btn_supprimer.clicked.connect(self._supprimer)
        bas_ech = QHBoxLayout()
        bas_ech.addWidget(self.btn_capturer)
        bas_ech.addStretch(1)
        bas_ech.addWidget(self.btn_renommer)
        bas_ech.addWidget(self.btn_supprimer)

        page_ech = QWidget()
        pe = QVBoxLayout(page_ech)
        pe.setContentsMargins(0, 0, 0, 0)
        pe.addWidget(self.table_ech, 1)
        pe.addLayout(bas_ech)

        self.pages = QTabWidget()
        self.pages.addTab(page_seances, t("Sessions"))
        self.pages.addTab(page_ech, t("Samples"))
        self.pages.currentChanged.connect(lambda _: self._maj_boutons())

        # --- aperçu commun ---------------------------------------------------
        self.plot = TracePlot(palette, "µV")
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMaximumHeight(150)

        split = QSplitter(Qt.Vertical)
        haut = QWidget()
        hl = QVBoxLayout(haut)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.addWidget(self.pages)
        bas = QWidget()
        bl = QVBoxLayout(bas)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(self.plot, 1)
        bl.addWidget(self.detail)
        split.addWidget(haut)
        split.addWidget(bas)
        split.setSizes([260, 400])

        lay = QVBoxLayout(self)
        lay.addLayout(top)
        lay.addWidget(split, 1)
        self.reload()

    # ------------------------------------------------------------------ liste
    def reload(self) -> None:
        self._recharger_seances()
        self.recharger_echantillons()
        self._maj_boutons()

    def _recharger_seances(self) -> None:
        directory = self.engine.settings.recording.directory
        self.refs = sess.scan(directory)
        self.table.setRowCount(len(self.refs))
        for i, r in enumerate(self.refs):
            for j, text in enumerate((r.pretty_date(), r.plante or "—",
                                      r.pretty_duration(), str(r.events),
                                      str(r.notes), os.path.basename(r.path))):
                self.table.setItem(i, j, QTableWidgetItem(text))
        self.table.resizeColumnsToContents()
        if not self.refs:
            self.detail.setPlainText(t(
                "No session in:\n{dossier}\n\nStart a recording from the toolbar (Ctrl+R), or simply keep what has just gone by with Ctrl+E: the folder will be created.").format(
                    dossier=directory))

    def recharger_echantillons(self) -> None:
        """Appelée aussi depuis la fenêtre principale, après une capture."""
        dossier = samples.dossier_par_defaut(self.engine.settings)
        self.echantillons = samples.lister(dossier)
        self.table_ech.setRowCount(len(self.echantillons))
        for i, r in enumerate(self.echantillons):
            echelle = (f"{r.full_scale_v * 1e6:.0f} µV" if r.full_scale_v < 1e-3
                       else f"{r.full_scale_v * 1e3:.1f} mV")
            if not r.complet:
                echelle = t("assumed")
            for j, texte in enumerate((r.pretty_date(), r.pretty_duration(),
                                       r.plante or "—", f"{r.sample_rate:g} Hz",
                                       echelle, os.path.basename(r.path))):
                self.table_ech.setItem(i, j, QTableWidgetItem(texte))
        self.table_ech.resizeColumnsToContents()

    # -------------------------------------------------------------- sélection
    def _selected(self) -> None:
        rows = {i.row() for i in self.table.selectedItems()}
        if not rows:
            return
        ref = self.refs[min(rows)]
        self.current = ref
        self.detail.setPlainText(sess.export_summary(ref))
        data, fs = sess.load_signal(ref)
        self._apercu(data, fs)
        marks = sess.load_marks(ref)
        self.plot.set_marks([float(m.get("temps_s", 0) or 0) for m in marks])
        self._maj_boutons()

    def _selection_echantillon(self) -> None:
        rows = {i.row() for i in self.table_ech.selectedItems()}
        if not rows:
            return
        ref = self.echantillons[min(rows)]
        self.courant_ech = ref
        self.plot.set_marks([])
        data, fs = samples.charger(
            ref, self.engine.settings.acquisition.input_range_v)
        self._apercu(data, fs)
        self.detail.setPlainText(self._resume_echantillon(ref, data, fs))
        self._maj_boutons()

    def _apercu(self, data, fs: float) -> None:
        if data is None or not data.size:
            self.plot.set_data(np.zeros(0), np.zeros(0))
            return
        y = data[:, 0]
        if y.size > 6000:
            y = decimate(y, int(np.ceil(y.size / 6000)))
        x = np.linspace(0.0, data.shape[0] / fs, y.size)
        self.plot.set_data(x, y * 1e6)

    def _resume_echantillon(self, ref, data, fs: float) -> str:
        lignes = [
            t("Sample: {nom}").format(nom=ref.name),
            t("Date: {date}   Duration: {duree}").format(
                date=ref.pretty_date(), duree=ref.pretty_duration()),
            t("Sampling: {fs:g} Hz on {voies} channel(s)").format(
                fs=ref.sample_rate, voies=ref.channels),
        ]
        if data is not None and data.size:
            y = data[:, 0]
            lignes.append(t("Amplitude: {pp:.1f} µV peak to peak, {eff:.2f} µV RMS").format(
                                pp=float(y.max() - y.min()) * 1e6,
                                eff=float(np.std(y)) * 1e6))
        if ref.plante or ref.lieu:
            lignes.append(t("Plant: {plante}   Place: {lieu}").format(
                plante=ref.plante or "—", lieu=ref.lieu or "—"))
        evenements = (ref.meta or {}).get("evenements_dans_la_fenetre")
        if evenements is not None:
            lignes.append(t("Events within the window: {n}").format(n=evenements))
        if not ref.complet:
            lignes.append(t("This file has no companion JSON: the amplitude shown is assumed from the current settings; the shape of the signal is intact."))
        lignes.append(ref.path)
        return "\n".join(lignes)

    # ----------------------------------------------------------------- actions
    def _maj_boutons(self) -> None:
        echantillons = self.pages.currentIndex() == 1
        quelque_chose = bool(self.courant_ech if echantillons else self.current)
        self.btn_play.setEnabled(quelque_chose)
        self.btn_export.setEnabled(self.current is not None)
        self.btn_renommer.setEnabled(self.courant_ech is not None)
        self.btn_supprimer.setEnabled(self.courant_ech is not None)
        self.btn_live.setEnabled(bool(self.engine.state.replaying))

    def _open_folder(self) -> None:
        if self.pages.currentIndex() == 1:
            path = samples.dossier_par_defaut(self.engine.settings)
        else:
            path = self.current.path if self.current else \
                self.engine.settings.recording.directory
        os.makedirs(path, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(path)                     # noqa: S606
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as exc:                       # pragma: no cover
            QMessageBox.warning(self, t("Cannot open"), str(exc))

    def _capturer(self) -> None:
        chemin = self.engine.capturer_echantillon()
        if chemin:
            self.recharger_echantillons()
            self.pages.setCurrentIndex(1)
            self.table_ech.selectRow(0)

    def _charger_fichier(self) -> None:
        """Rejoue un enregistrement choisi dans l'arborescence.

        On accepte n'importe quel WAV : un échantillon, le `signal.wav` d'une
        séance, ou un fichier reçu d'un correspondant. La pleine échelle est
        celle du JSON compagnon s'il existe ; sinon celle des réglages, et on
        le dit plutôt que de laisser croire à une mesure.
        """
        depart = samples.dossier_par_defaut(self.engine.settings)
        chemin, _ = QFileDialog.getOpenFileName(
            self, t("Load a recording"), depart,
            t("Recordings (*.wav);;All files (*)"))
        if not chemin:
            return
        ref = samples.EchantillonRef(path=chemin,
                                     name=os.path.splitext(os.path.basename(chemin))[0])
        samples._entete_wav(ref)
        samples._relire_json(ref)
        data, fs = samples.charger(
            ref, self.engine.settings.acquisition.input_range_v)
        if data is None or not data.size:
            QMessageBox.warning(self, t("Replay"),
                                t("This file contains no readable signal."))
            return
        self.courant_ech = ref
        self._apercu(data, fs)
        self.detail.setPlainText(self._resume_echantillon(ref, data, fs))
        vitesse = float(self.cb_speed.currentData())
        if self.engine.rejouer(data, fs, vitesse, nom=ref.name):
            self.btn_play.setChecked(True)
            self.btn_play.setText(t("Stop the replay"))
            self._maj_boutons()

    def _toggle_play(self) -> None:
        """Rejoue la sélection **dans le moteur** — tout le logiciel suit."""
        if not self.btn_play.isChecked():
            self.engine.arreter_relecture(revenir_en_direct=True)
            self.btn_play.setText(t("Replay"))
            self._maj_boutons()
            return

        vitesse = float(self.cb_speed.currentData())
        if self.pages.currentIndex() == 1 and self.courant_ech is not None:
            data, fs = samples.charger(
                self.courant_ech, self.engine.settings.acquisition.input_range_v)
            nom = self.courant_ech.name
        elif self.current is not None:
            data, fs = sess.load_signal(self.current)
            nom = self.current.name
        else:
            self.btn_play.setChecked(False)
            return

        if data is None or not data.size:
            QMessageBox.information(self, t("Replay"),
                                    t("This session contains no signal."))
            self.btn_play.setChecked(False)
            return
        if not self.engine.rejouer(data, fs, vitesse, nom=nom):
            self.btn_play.setChecked(False)
            return
        self.btn_play.setText(t("Stop the replay"))
        self._maj_boutons()

    def _revenir_en_direct(self) -> None:
        self.engine.arreter_relecture(revenir_en_direct=True)
        self.btn_play.setChecked(False)
        self.btn_play.setText(t("Replay"))
        self._maj_boutons()

    def _renommer(self) -> None:
        if self.courant_ech is None:
            return
        nouveau, ok = QInputDialog.getText(
            self, t("Rename the sample"), t("New name:"),
            text=self.courant_ech.name)
        if not ok or not nouveau.strip():
            return
        samples.renommer(self.courant_ech, nouveau)
        self.courant_ech = None
        self.recharger_echantillons()

    def _supprimer(self) -> None:
        if self.courant_ech is None:
            return
        reponse = QMessageBox.question(
            self, t("Delete the sample"),
            t("Permanently delete “{nom}”?\n\nThe WAV file and its JSON will be erased.").format(nom=self.courant_ech.name),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reponse != QMessageBox.Yes:
            return
        samples.supprimer(self.courant_ech)
        self.courant_ech = None
        self.recharger_echantillons()
        self.plot.set_data(np.zeros(0), np.zeros(0))
        self.detail.setPlainText("")

    def _export(self) -> None:
        if self.current is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, t("Export the summary"), f"{self.current.name}.txt",
            t("Text (*.txt)"))
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(sess.export_summary(self.current) + "\n")
        except OSError as exc:                         # pragma: no cover
            QMessageBox.warning(self, t("Cannot write"), str(exc))

    # ------------------------------------------------------------ rafraîchi
    def refresh(self, state) -> None:
        if state.replaying and state.replay_length > 0:
            self.btn_play.setText(t("Stop — {position:.0f} s / {duree:.0f} s").format(
                position=state.replay_position, duree=state.replay_length))
            if not self.btn_play.isChecked():
                self.btn_play.setChecked(True)
        self.btn_live.setEnabled(bool(state.replaying))
