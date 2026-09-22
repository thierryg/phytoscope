# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/diag_tab.py
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

"""Diagnostic — USB, journal, échantillonnage, sortie sonore.

Quatre panneaux, qui répondent aux quatre questions posées quand « ça ne
marche pas » :

* **USB** : qu'est-ce qui est branché, sous quel VID/PID, et le lien tient-il ?
* **Journal** : qu'a fait le logiciel, et à quel niveau de détail ?
* **Échantillonnage** : que prélève-t-on exactement, et avec quel gain de bruit ?
* **Sortie sonore** : entend-on quelque chose, et à quel niveau ?

C'est aussi ici que s'activent les fonctions de mise au point : capture des
trames dans un fichier, et passage du journal en mode « debug ».
"""
from __future__ import annotations

import os
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QGuiApplication
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
                               QDoubleSpinBox, QFileDialog, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QMessageBox,
                               QPlainTextEdit, QPushButton, QScrollArea,
                               QSpinBox,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QVBoxLayout, QWidget)

from ..core import logging_setup, usbdiag
from ..core.logging_setup import get_logger
from ..core.sampling import FENETRES
from .widgets import LevelBar
from ..i18n import t
from . import fonts

log = get_logger(__name__)


class DiagTab(QWidget):
    """Onglet de diagnostic et de mise au point."""

    def __init__(self, engine, palette: dict, on_apply=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.on_apply = on_apply
        self._rapport: Optional[usbdiag.UsbReport] = None

        tabs = QTabWidget()
        tabs.addTab(_rouleau(self._page_usb()), t("Lien USB"))
        tabs.addTab(_rouleau(self._page_echantillonnage()), t("Échantillonnage"))
        tabs.addTab(_rouleau(self._page_audio()), t("Sortie sonore"))
        tabs.addTab(_rouleau(self._page_modules()), t("Modules"))
        tabs.addTab(_rouleau(self._page_journal()), t("Journal"))
        lay = QVBoxLayout(self)
        lay.addWidget(tabs)
        self._compteur = 0
        self._scanner()

    # ------------------------------------------------------------------ USB
    def _page_usb(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        barre = QHBoxLayout()
        self.btn_scan = QPushButton(t("Analyser le bus USB"))
        self.btn_scan.clicked.connect(self._scanner)
        self.btn_copier_usb = QPushButton(t("Copier le rapport"))
        self.btn_copier_usb.clicked.connect(self._copier_usb)
        self.lab_verdict = QLabel("—")
        self.lab_verdict.setWordWrap(True)
        barre.addWidget(self.btn_scan)
        barre.addWidget(self.btn_copier_usb)
        barre.addStretch(1)
        lay.addLayout(barre)
        lay.addWidget(self.lab_verdict)

        self.table_usb = QTableWidget(0, 6)
        self.table_usb.setHorizontalHeaderLabels(
            [t("VID:PID"), t("Fabricant"), t("Produit"), t("N° de série"), t("Port"), t("Source")])
        self.table_usb.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_usb.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_usb.setAlternatingRowColors(True)
        lay.addWidget(self.table_usb, 1)

        gmon = QGroupBox(t("Surveillance du lien"))
        f = QFormLayout(gmon)
        self.lab_lien = QLabel("inactive")
        self.chk_surveiller = QCheckBox(t("surveiller la présence de la carte"))
        self.chk_surveiller.stateChanged.connect(self._surveillance)
        self.sp_periode = QDoubleSpinBox()
        self.sp_periode.setRange(1.0, 60.0)
        self.sp_periode.setValue(self.engine.settings.diagnostics.usb_poll_seconds)
        self.sp_periode.setSuffix(t(" s"))
        f.addRow(self.chk_surveiller)
        f.addRow(t("Période"), self.sp_periode)
        f.addRow(t("État"), self.lab_lien)
        lay.addWidget(gmon)

        gcap = QGroupBox(t("Capture des trames (mise au point)"))
        f2 = QFormLayout(gcap)
        self.chk_debug = QCheckBox(t("mode de mise au point"))
        self.chk_debug.setChecked(self.engine.settings.diagnostics.debug_mode)
        self.chk_debug.stateChanged.connect(self._mode_debug)
        self.cb_format = QComboBox()
        for k, v in (("texte", t("texte — lisible immédiatement")),
                     ("hexa", t("hexadécimal — analyse fine")),
                     ("binaire", t("binaire — compact"))):
            self.cb_format.addItem(v, k)
        self.sp_max = QSpinBox()
        self.sp_max.setRange(1000, 5_000_000)
        self.sp_max.setValue(self.engine.settings.diagnostics.capture_max_frames)
        self.btn_capture = QPushButton(t("Démarrer la capture"))
        self.btn_capture.setCheckable(True)
        self.btn_capture.clicked.connect(self._capture)
        self.lab_capture = QLabel("inactive")
        self.btn_ouvrir_capture = QPushButton(t("Ouvrir le dossier des captures"))
        self.btn_ouvrir_capture.clicked.connect(self._ouvrir_captures)
        f2.addRow(self.chk_debug)
        f2.addRow(t("Format"), self.cb_format)
        f2.addRow(t("Plafond de trames"), self.sp_max)
        f2.addRow(self.btn_capture)
        f2.addRow(t("État"), self.lab_capture)
        f2.addRow(self.btn_ouvrir_capture)
        lay.addWidget(gcap)
        return w

    def _scanner(self) -> None:
        try:
            self._rapport = usbdiag.diagnose(self.engine.settings)
        except Exception as exc:                       # noqa: BLE001
            log.exception("Diagnostic USB impossible")
            self.lab_verdict.setText(f"diagnostic impossible : {exc}")
            return
        rep = self._rapport
        self.table_usb.setRowCount(len(rep.devices))
        for i, d in enumerate(rep.devices):
            for j, texte in enumerate(d.to_row()):
                item = QTableWidgetItem(texte)
                if d.is_phytosense:
                    item.setFont(QFont("", -1, QFont.Bold))
                self.table_usb.setItem(i, j, item)
        self.table_usb.resizeColumnsToContents()
        couleur = self.p["trace"] if rep.target else self.p["or"]
        conseils = ("<br>".join("• " + a for a in rep.advice)) if rep.advice else ""
        self.lab_verdict.setText(f"<b style='color:{couleur}'>{rep.verdict}</b>"
                                 + (f"<br>{conseils}" if conseils else ""))

    def _copier_usb(self) -> None:
        if self._rapport is None:
            return
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(self._rapport.as_text())
        self.btn_copier_usb.setText(t("Rapport copié ✓"))

    def _surveillance(self) -> None:
        self.engine.settings.diagnostics.usb_poll_seconds = self.sp_periode.value()
        if self.chk_surveiller.isChecked():
            self.engine.monitor.on_change = self.engine._usb_change
            self.engine.monitor.start()
        else:
            self.engine.monitor.stop()

    def _mode_debug(self) -> None:
        actif = self.chk_debug.isChecked()
        self.engine.settings.diagnostics.debug_mode = actif
        if actif and self.cb_niveau.currentData() not in ("DEBUG",):
            index = self.cb_niveau.findData("DEBUG")
            if index >= 0:
                self.cb_niveau.setCurrentIndex(index)

    def _capture(self) -> None:
        d = self.engine.settings.diagnostics
        d.capture_format = self.cb_format.currentData()
        d.capture_max_frames = self.sp_max.value()
        if self.btn_capture.isChecked():
            chemin = self.engine.start_capture()
            if chemin:
                self.btn_capture.setText(t("Arrêter la capture"))
            else:
                self.btn_capture.setChecked(False)
                QMessageBox.warning(self, t("Capture"),
                                    self.engine.capture.last_error or
                                    "capture impossible")
        else:
            self.engine.stop_capture()
            self.btn_capture.setText(t("Démarrer la capture"))

    def _ouvrir_captures(self) -> None:
        import subprocess
        import sys as _sys
        chemin = self.engine.settings.capture_dir()
        os.makedirs(chemin, exist_ok=True)
        try:
            if _sys.platform.startswith("win"):
                os.startfile(chemin)                   # noqa: S606
            elif _sys.platform == "darwin":
                subprocess.Popen(["open", chemin])
            else:
                subprocess.Popen(["xdg-open", chemin])
        except Exception as exc:                       # noqa: BLE001
            QMessageBox.information(self, t("Captures"), chemin + f"\n\n({exc})")

    # -------------------------------------------------------- échantillonnage
    def _page_echantillonnage(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        s = self.engine.settings.sampling

        g = QGroupBox(t("Prélèvement"))
        f = QFormLayout(g)
        self.cb_mode = QComboBox()
        for k, v in (("continu", t("continu — écoute, aucun découpage")),
                     ("bloc", t("bloc — analyse par tranches fenêtrées")),
                     ("declenche", t("déclenché — comme un oscilloscope"))):
            self.cb_mode.addItem(v, k)
        _choisir(self.cb_mode, s.mode)
        self.sp_bloc = QSpinBox()
        self.sp_bloc.setRange(16, 1 << 20)
        self.sp_bloc.setValue(s.block_samples)
        self.sp_decim = QSpinBox()
        self.sp_decim.setRange(1, 4096)
        self.sp_decim.setValue(s.decimation)
        self.sp_moy = QSpinBox()
        self.sp_moy.setRange(1, 1024)
        self.sp_moy.setValue(s.averaging)
        self.cb_fenetre = QComboBox()
        for k, v in FENETRES.items():
            self.cb_fenetre.addItem(t(v), k)
        _choisir(self.cb_fenetre, s.window)
        f.addRow(t("Mode"), self.cb_mode)
        f.addRow(t("Taille du bloc"), self.sp_bloc)
        f.addRow(t("Décimation"), self.sp_decim)
        f.addRow(t("Moyennage de blocs"), self.sp_moy)
        f.addRow(t("Fenêtre"), self.cb_fenetre)
        lay.addWidget(g)

        g2 = QGroupBox(t("Déclenchement"))
        f2 = QFormLayout(g2)
        self.cb_trig_mode = QComboBox()
        for k, v in (("auto", t("auto — trace même sans déclenchement")),
                     ("normal", t("normal — n'affiche que sur déclenchement")),
                     ("unique", t("unique — une seule capture"))):
            self.cb_trig_mode.addItem(v, k)
        _choisir(self.cb_trig_mode, s.trigger_mode)
        self.cb_trig_edge = QComboBox()
        for k, v in (("montant", t("front montant")), ("descendant", t("front descendant")),
                     ("les_deux", t("les deux"))):
            self.cb_trig_edge.addItem(v, k)
        _choisir(self.cb_trig_edge, s.trigger_edge)
        self.sp_niveau = QDoubleSpinBox()
        self.sp_niveau.setRange(0.1, 1e6)
        self.sp_niveau.setDecimals(1)
        self.sp_niveau.setSuffix(t(" µV"))
        self.sp_niveau.setValue(s.trigger_level_uv)
        self.sp_pre = QDoubleSpinBox()
        self.sp_pre.setRange(0.0, 90.0)
        self.sp_pre.setSuffix(t(" %"))
        self.sp_pre.setValue(s.pretrigger_percent)
        self.sp_holdoff = QDoubleSpinBox()
        self.sp_holdoff.setRange(0.0, 60000.0)
        self.sp_holdoff.setSuffix(t(" ms"))
        self.sp_holdoff.setValue(s.holdoff_ms)
        f2.addRow(t("Mode"), self.cb_trig_mode)
        f2.addRow(t("Front"), self.cb_trig_edge)
        f2.addRow(t("Niveau"), self.sp_niveau)
        f2.addRow(t("Pré-déclenchement"), self.sp_pre)
        f2.addRow(t("Temps mort"), self.sp_holdoff)
        lay.addWidget(g2)

        barre = QHBoxLayout()
        self.btn_ech_appliquer = QPushButton(t("Appliquer"))
        self.btn_ech_appliquer.clicked.connect(self._appliquer_echantillonnage)
        self.btn_ech_vider = QPushButton(t("Vider les blocs"))
        self.btn_ech_vider.clicked.connect(lambda: self.engine.sampler.clear())
        barre.addWidget(self.btn_ech_appliquer)
        barre.addWidget(self.btn_ech_vider)
        barre.addStretch(1)
        lay.addLayout(barre)

        self.lab_ech = QLabel("")
        self.lab_ech.setWordWrap(True)
        self.lab_ech.setStyleSheet(f"color:{self.p['texte2']};")
        lay.addWidget(self.lab_ech)
        lay.addStretch(1)
        return w

    def _appliquer_echantillonnage(self) -> None:
        s = self.engine.settings.sampling
        s.mode = self.cb_mode.currentData()
        s.block_samples = self.sp_bloc.value()
        s.decimation = self.sp_decim.value()
        s.averaging = self.sp_moy.value()
        s.window = self.cb_fenetre.currentData()
        s.trigger_mode = self.cb_trig_mode.currentData()
        s.trigger_edge = self.cb_trig_edge.currentData()
        s.trigger_level_uv = self.sp_niveau.value()
        s.pretrigger_percent = self.sp_pre.value()
        s.holdoff_ms = self.sp_holdoff.value()
        self.engine.sampler.reconfigure()
        if self.on_apply:
            self.on_apply()

    # ---------------------------------------------------------- sortie sonore
    def _page_audio(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        a = self.engine.settings.audio_out

        g = QGroupBox(t("Amplification"))
        f = QFormLayout(g)
        self.sp_gain = QDoubleSpinBox()
        self.sp_gain.setRange(-60.0, 12.0)
        self.sp_gain.setSuffix(t(" dB"))
        self.sp_gain.setValue(a.gain_db)
        self.sp_boost = QDoubleSpinBox()
        self.sp_boost.setRange(0.0, 36.0)
        self.sp_boost.setSuffix(t(" dB"))
        self.sp_boost.setValue(a.boost_db)
        self.sp_presence = QDoubleSpinBox()
        self.sp_presence.setRange(0.0, 18.0)
        self.sp_presence.setSuffix(t(" dB"))
        self.sp_presence.setValue(a.presence_boost_db)
        self.chk_comp = QCheckBox("compresseur")
        self.chk_comp.setChecked(a.compressor)
        self.sp_seuil = QDoubleSpinBox()
        self.sp_seuil.setRange(-60.0, 0.0)
        self.sp_seuil.setSuffix(t(" dB"))
        self.sp_seuil.setValue(a.comp_threshold_db)
        self.sp_ratio = QDoubleSpinBox()
        self.sp_ratio.setRange(1.0, 20.0)
        self.sp_ratio.setValue(a.comp_ratio)
        self.chk_lim = QCheckBox("limiteur")
        self.chk_lim.setChecked(a.limiter)
        self.cb_mode_audio = QComboBox()
        for k, v in (("ecriture", t("écriture bloquante — robuste (défaut)")),
                     ("rappel", t("rappel — tampon circulaire"))):
            self.cb_mode_audio.addItem(v, k)
        _choisir(self.cb_mode_audio, a.mode)
        self.cb_bloc_audio = QComboBox()
        for n in (512, 1024, 2048, 4096, 8192):
            self.cb_bloc_audio.addItem(f"{n} échantillons", n)
        _choisir(self.cb_bloc_audio, a.block_size)
        self.cb_latence = QComboBox()
        for k, v in (("0.2", t("0,2 s — réactif")), ("0.3", t("0,3 s")),
                     ("0.5", t("0,5 s — recommandé")), ("1.0", t("1,0 s — très sûr")),
                     ("high", t("laisser le système choisir"))):
            self.cb_latence.addItem(v, k)
        _choisir(self.cb_latence, str(a.latency))
        f.addRow(t("Gain"), self.sp_gain)
        f.addRow(t("Amplification"), self.sp_boost)
        f.addRow(t("Présence (1–4 kHz)"), self.sp_presence)
        f.addRow(self.chk_comp)
        f.addRow(t("Seuil de compression"), self.sp_seuil)
        f.addRow(t("Rapport"), self.sp_ratio)
        f.addRow(self.chk_lim)
        lay.addWidget(g)

        gflux = QGroupBox(t("Flux audio — à ajuster si le son craque"))
        f3 = QFormLayout(gflux)
        f3.addRow(t("Mode"), self.cb_mode_audio)
        f3.addRow(t("Taille de bloc"), self.cb_bloc_audio)
        f3.addRow(t("Latence"), self.cb_latence)
        aide = QLabel(
            t("Un bloc plus grand et une latence plus longue suppriment les "
            "craquements sur une machine chargée, au prix de quelques "
            "centaines de millisecondes de retard — sans conséquence ici, "
            "puisque la plante n'attend pas de réponse. Ces réglages ne "
            "prennent effet qu'au redémarrage de l'acquisition."))
        aide.setWordWrap(True)
        aide.setStyleSheet(f"color:{self.p['texte2']};font-size:8pt;")
        f3.addRow(aide)
        lay.addWidget(gflux)

        g2 = QGroupBox(t("Bips de repérage"))
        f2 = QFormLayout(g2)
        self.chk_bip = QCheckBox(t("activer les bips"))
        self.chk_bip.setChecked(a.beep_enabled)
        self.chk_bip_ev = QCheckBox(t("à chaque événement détecté"))
        self.chk_bip_ev.setChecked(a.beep_on_event)
        self.chk_bip_sat = QCheckBox(t("en cas de saturation"))
        self.chk_bip_sat.setChecked(a.beep_on_saturation)
        self.sp_bip_gain = QDoubleSpinBox()
        self.sp_bip_gain.setRange(-40.0, 6.0)
        self.sp_bip_gain.setSuffix(t(" dB"))
        self.sp_bip_gain.setValue(a.beep_gain_db)
        f2.addRow(self.chk_bip)
        f2.addRow(self.chk_bip_ev)
        f2.addRow(self.chk_bip_sat)
        f2.addRow(t("Niveau du bip"), self.sp_bip_gain)
        lay.addWidget(g2)

        barre = QHBoxLayout()
        self.btn_audio_appliquer = QPushButton(t("Appliquer"))
        self.btn_audio_appliquer.clicked.connect(self._appliquer_audio)
        self.btn_test = QPushButton(t("Essai du haut-parleur (1 kHz)"))
        self.btn_test.clicked.connect(self.engine.test_haut_parleur)
        self.btn_bip = QPushButton(t("Bip d'essai"))
        self.btn_bip.clicked.connect(lambda: self.engine.output.bip("marqueur"))
        barre.addWidget(self.btn_audio_appliquer)
        barre.addWidget(self.btn_test)
        barre.addWidget(self.btn_bip)
        barre.addStretch(1)
        lay.addLayout(barre)

        self.niveau = LevelBar(self.p)
        lay.addWidget(QLabel(t("Niveau de sortie")))
        lay.addWidget(self.niveau)
        self.lab_audio = QLabel("")
        self.lab_audio.setWordWrap(True)
        self.lab_audio.setStyleSheet(f"color:{self.p['texte2']};")
        lay.addWidget(self.lab_audio)

        lay.addWidget(self._groupe_voix())
        lay.addStretch(1)
        return w

    def _groupe_voix(self) -> QWidget:
        """Ce qui est installé pour prononcer les énoncés du mode Parole.

        Cette liste répond à la question posée chaque fois : « pourquoi le
        logiciel n'a-t-il rien dit ? ». Elle distingue la synthèse absente de
        la synthèse présente mais coupée, ce qui n'a rien à voir.
        """
        from ..music.voice import strategies_disponibles

        g = QGroupBox(t("Synthèse vocale (mode Parole)"))
        f = QVBoxLayout(g)
        aucune = True
        for nom, description, disponible in strategies_disponibles():
            if nom == "silencieuse":
                continue
            if disponible:
                aucune = False
            etat = "présente" if disponible else "absente"
            couleur = self.p["trace"] if disponible else self.p["texte2"]
            ligne = QLabel(f"<b style='color:{couleur}'>{etat:>8}</b>  "
                           f"<b>{nom}</b> — {description}")
            ligne.setTextFormat(Qt.RichText)
            ligne.setWordWrap(True)
            f.addWidget(ligne)
        conseil = QLabel(
            "Aucune synthèse n'est installée : les énoncés restent écrits et "
            "enregistrés, mais rien ne sera prononcé. Sous Linux : "
            "« sudo apt install espeak-ng », ou « pip install pyttsx3 »."
            if aucune else
            "Tout se passe hors ligne : aucun texte ne quitte cette machine.")
        conseil.setWordWrap(True)
        conseil.setStyleSheet(
            f"color:{self.p['alerte'] if aucune else self.p['texte2']};"
            f"font-size:8pt;")
        f.addWidget(conseil)
        return g

    def _appliquer_audio(self) -> None:
        a = self.engine.settings.audio_out
        a.gain_db = self.sp_gain.value()
        a.boost_db = self.sp_boost.value()
        a.presence_boost_db = self.sp_presence.value()
        a.compressor = self.chk_comp.isChecked()
        a.comp_threshold_db = self.sp_seuil.value()
        a.comp_ratio = self.sp_ratio.value()
        a.limiter = self.chk_lim.isChecked()
        a.beep_enabled = self.chk_bip.isChecked()
        a.beep_on_event = self.chk_bip_ev.isChecked()
        a.beep_on_saturation = self.chk_bip_sat.isChecked()
        a.beep_gain_db = self.sp_bip_gain.value()
        a.mode = self.cb_mode_audio.currentData()
        a.block_size = int(self.cb_bloc_audio.currentData())
        a.latency = self.cb_latence.currentData()
        self.engine.output.apply_settings()
        if self.on_apply:
            self.on_apply()

    # -------------------------------------------------------------- journal
    def _page_modules(self) -> QWidget:
        """L'état de chaque module — et pourquoi celui qui manque n'est pas là.

        C'est la page qu'on regarde quand un module qu'on vient d'écrire ne
        s'affiche nulle part. Elle dit en une phrase ce qui s'est passé :
        manifeste invalide, API visée inconnue, bibliothèque absente, faute au
        chargement. Sans elle, on chercherait dans le journal, et l'on
        commencerait par douter de soi.
        """
        w = QWidget()
        lay = QVBoxLayout(w)

        entete = QLabel(t(
            "Les modules étendent le logiciel : analyses, représentations, "
            "sonifications, formats d'export. Ceux qui sont livrés avec lui "
            "passent par la même interface de programmation que les vôtres — "
            "c'est ce qui garantit qu'elle suffit."))
        entete.setWordWrap(True)
        entete.setStyleSheet(f"color:{self.p['texte2']};")
        lay.addWidget(entete)

        self.table_modules = QTableWidget(0, 6)
        self.table_modules.setHorizontalHeaderLabels(
            [t("Module"), t("Version"), t("API"), t("Origine"), t("État"),
             t("Capacités — ou pourquoi il est écarté")])
        self.table_modules.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_modules.setAlternatingRowColors(True)
        self.table_modules.verticalHeader().setVisible(False)
        self.table_modules.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(self.table_modules, 1)

        barre = QHBoxLayout()
        self.lab_modules = QLabel("—")
        self.lab_modules.setStyleSheet(f"color:{self.p['texte2']};")
        self.btn_modules_rafraichir = QPushButton(t("Rafraîchir"))
        self.btn_modules_rafraichir.clicked.connect(self._lire_modules)
        self.btn_modules_dossier = QPushButton(t("Ouvrir le dossier des modules"))
        self.btn_modules_dossier.setToolTip(t(
            "C'est là qu'on dépose un module écrit soi-même. Le SDK, livré "
            "avec le code source, contient un exemple complet et un outil qui "
            "en crée un nouveau."))
        self.btn_modules_dossier.clicked.connect(self._ouvrir_dossier_modules)
        barre.addWidget(self.lab_modules, 1)
        barre.addWidget(self.btn_modules_rafraichir)
        barre.addWidget(self.btn_modules_dossier)
        lay.addLayout(barre)

        self._lire_modules()
        return w

    def _lire_modules(self) -> None:
        registre = getattr(self.engine, "modules", None)
        if registre is None:
            self.lab_modules.setText(t("Registre des modules indisponible."))
            return
        lignes = registre.rapport()
        self.table_modules.setRowCount(len(lignes))
        couleurs = {"actif": self.p["trace"], "en_faute": self.p["alerte"],
                    "incompatible": self.p["alerte"],
                    "desactive": self.p["texte2"]}
        for i, l in enumerate(lignes):
            #  Quand un module est écarté, c'est la RAISON qui occupe la
            #  dernière colonne : c'est ce qu'on est venu chercher.
            derniere = l["faute"] or l["capacites"]
            for col, valeur in enumerate((l["titre"], l["version"], l["api"],
                                          t(l["origine"]), t(l["etat"]),
                                          derniere)):
                cellule = QTableWidgetItem(str(valeur))
                if col == 4:
                    cellule.setForeground(QColor(
                        couleurs.get(l["etat"], self.p["texte"])))
                if l["faute"]:
                    cellule.setToolTip(l["faute"])
                self.table_modules.setItem(i, col, cellule)
        self.table_modules.resizeColumnsToContents()

        actifs = sum(1 for l in lignes if l["etat"] == "actif")
        ecartes = sum(1 for l in lignes if l["etat"] in ("en_faute",
                                                         "incompatible"))
        from ..api import VERSION_API
        texte = t("{actifs} module(s) actif(s) sur {total} — API {api}").format(
            actifs=actifs, total=len(lignes), api=VERSION_API)
        if ecartes:
            texte += "  ·  " + t("{n} écarté(s)").format(n=ecartes)
        self.lab_modules.setText(texte)

    def _ouvrir_dossier_modules(self) -> None:
        from ..api import Registre
        dossier = Registre.dossier_utilisateur()
        os.makedirs(dossier, exist_ok=True)
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(dossier))

    def _page_journal(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        barre = QHBoxLayout()
        self.cb_niveau = QComboBox()
        for k, v in logging_setup.NIVEAUX_FR.items():
            self.cb_niveau.addItem(f"{k} — {t(v)}", k)
        _choisir(self.cb_niveau, logging_setup.current_level())
        self.cb_niveau.currentIndexChanged.connect(self._changer_niveau)
        self.btn_rafraichir = QPushButton(t("Rafraîchir"))
        self.btn_rafraichir.clicked.connect(self._lire_journal)
        self.btn_vider = QPushButton(t("Vider"))
        self.btn_vider.clicked.connect(self._vider_journal)
        self.btn_ouvrir_journal = QPushButton(t("Enregistrer une copie…"))
        self.btn_ouvrir_journal.clicked.connect(self._copier_journal)
        barre.addWidget(QLabel(t("Niveau")))
        barre.addWidget(self.cb_niveau, 1)
        barre.addWidget(self.btn_rafraichir)
        barre.addWidget(self.btn_vider)
        barre.addWidget(self.btn_ouvrir_journal)
        lay.addLayout(barre)

        self.lab_fichier = QLabel(logging_setup.log_path() or "(aucun fichier)")
        self.lab_fichier.setStyleSheet(f"color:{self.p['texte2']};font-size:8pt;")
        lay.addWidget(self.lab_fichier)

        self.vue_journal = QPlainTextEdit()
        self.vue_journal.setReadOnly(True)
        self.vue_journal.setFont(fonts.mono(8))
        lay.addWidget(self.vue_journal, 1)

        bas = QHBoxLayout()
        self.chk_suivre = QCheckBox(t("suivre en continu"))
        bas.addWidget(self.chk_suivre)
        bas.addStretch(1)
        #  Cet aperçu relit tout le fichier et n'en garde que 500 lignes : il
        #  suffit pour un coup d'œil au milieu d'un diagnostic. Pour chercher
        #  vraiment — filtre, lecture incrémentale, archives de rotation —, la
        #  fenêtre dédiée fait mieux, et on y va d'ici.
        self.btn_fenetre_journal = QPushButton(t("Ouvrir dans une fenêtre…"))
        self.btn_fenetre_journal.setToolTip(
            t("Fenêtre du journal : lecture en direct, filtre, et copie vers "
              "l'emplacement de votre choix (Ctrl+L)"))
        self.btn_fenetre_journal.clicked.connect(self._ouvrir_fenetre_journal)
        bas.addWidget(self.btn_fenetre_journal)
        lay.addLayout(bas)
        self._lire_journal()
        return w

    def _ouvrir_fenetre_journal(self) -> None:
        """Passe la main à la fenêtre du journal, qu'elle soit ouverte ou non."""
        fenetre = self.window()
        if hasattr(fenetre, "_journal"):
            fenetre._journal()
            return
        #  Onglet instancié seul — dans un essai, par exemple : on ouvre quand
        #  même, sans dépendre de la fenêtre principale.
        from .log_window import LogWindow
        if getattr(self, "_fen_journal", None) is None:
            self._fen_journal = LogWindow(self.p, self.engine.settings, self)
        self._fen_journal.show()
        self._fen_journal.raise_()

    def _changer_niveau(self) -> None:
        niveau = self.cb_niveau.currentData()
        applique = logging_setup.set_level(niveau)
        self.engine.settings.logging.level = applique
        self._lire_journal()

    def _lire_journal(self) -> None:
        self.lab_fichier.setText(logging_setup.log_path() or t("(aucun fichier)"))
        self.vue_journal.setPlainText(logging_setup.tail(500))
        self.vue_journal.verticalScrollBar().setValue(
            self.vue_journal.verticalScrollBar().maximum())

    def _vider_journal(self) -> None:
        if logging_setup.clear():
            self._lire_journal()

    def _copier_journal(self) -> None:
        source = logging_setup.log_path()
        if not source or not os.path.exists(source):
            return
        cible, _ = QFileDialog.getSaveFileName(self, t("Enregistrer le journal"),
                                               "phytoscope.log", t("Journal (*.log)"))
        if not cible:
            return
        try:
            import shutil
            shutil.copyfile(source, cible)
        except OSError as exc:                         # pragma: no cover
            QMessageBox.warning(self, t("Copie impossible"), str(exc))

    # -------------------------------------------------------------- rendu
    def refresh(self, state) -> None:
        self._compteur += 1
        self.lab_ech.setText(self.engine.sampler.summary())
        self.lab_lien.setText(self.engine.monitor.summary())
        self.lab_capture.setText(self.engine.capture.status())
        m = self.engine.output.metrics
        self.niveau.set_value(m.peak)
        from ..core import audio_quiet
        audio = self.engine.audio
        self.lab_audio.setText(
            f"{self.engine.output.resume()}<br>"
            f"mode « {audio.mode} » · bloc {audio.block} · "
            f"latence {audio.latency} · avance {audio.remplissage * 100:.0f} %<br>"
            f"décrochages : {audio.underruns} signalés par PortAudio, "
            f"{audio.famines} trous de rendu, "
            f"{audio_quiet.messages_captes()} messages ALSA captés")
        self.lab_audio.setTextFormat(Qt.RichText)
        if self.chk_suivre.isChecked() and self._compteur % 30 == 0:
            self._lire_journal()


def _rouleau(w: QWidget) -> QScrollArea:
    """Enveloppe une page dans une zone défilante.

    Sans cela, la page la plus haute impose sa taille à toute la fenêtre, et
    l'on ne peut plus réduire celle-ci sous la hauteur de l'écran.
    """
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setFrameShape(QScrollArea.NoFrame)
    sa.setWidget(w)
    return sa


def _choisir(combo: QComboBox, valeur) -> None:
    for i in range(combo.count()):
        if combo.itemData(i) == valeur:
            combo.setCurrentIndex(i)
            return
