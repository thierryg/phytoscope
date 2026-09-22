# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/settings_tab.py
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

"""Réglages — assistant d'auto-configuration, puis tout le reste.

Deux niveaux cohabitent volontairement :

* **l'assistant**, qui écoute quelques secondes et propose un jeu complet de
  réglages en expliquant chacun de ses choix ;
* **les réglages détaillés**, où rien n'est caché — jusqu'au coefficient de
  qualité du réjecteur et au facteur de conversion en volts.

Un logiciel de mesure qui cache ses constantes n'est pas un instrument :
c'est une boîte noire. L'onglet « Expert » est donc toujours accessible.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QAbstractItemView, QCheckBox, QComboBox,
                               QDoubleSpinBox, QFileDialog, QFormLayout,
                               QGroupBox, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPlainTextEdit, QProgressBar,
                               QPushButton, QScrollArea, QSpinBox,
                               QTabWidget, QTableWidget, QTableWidgetItem,
                               QVBoxLayout, QWidget)

from ..core import autoconfig
from ..core.sources import AudioSource
from ..music.midi_out import MidiOut
from ..music.synth import AudioOutput
from ..i18n import t


class SettingsTab(QWidget):
    def __init__(self, engine, palette: dict, on_apply, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.on_apply = on_apply
        self._auto_timer: Optional[QTimer] = None
        self._auto_result = None

        tabs = QTabWidget()
        tabs.addTab(self._page_assistant(), t("Assistant"))
        tabs.addTab(_scroll(self._page_acquisition()), t("Acquisition"))
        tabs.addTab(_scroll(self._page_processing()), t("Traitement"))
        tabs.addTab(_scroll(self._page_music()), t("Musique"))
        tabs.addTab(_scroll(self._page_recording()), t("Enregistrement"))
        tabs.addTab(_scroll(self._page_ui()), t("Interface"))
        tabs.addTab(_scroll(self._page_modules()), t("Modules"))
        tabs.addTab(_scroll(self._page_expert()), t("Expert"))

        bar = QHBoxLayout()
        self.btn_apply = QPushButton(t("Appliquer"))
        self.btn_apply.clicked.connect(self._apply)
        self.btn_save = QPushButton(t("Enregistrer les réglages"))
        self.btn_save.clicked.connect(self._save)
        self.btn_reset = QPushButton(t("Revenir aux valeurs par défaut"))
        self.btn_reset.clicked.connect(self._reset)
        self.lab_path = QLabel("")
        self.lab_path.setStyleSheet(f"color:{palette['texte2']};font-size:8pt;")
        bar.addWidget(self.btn_apply)
        bar.addWidget(self.btn_save)
        bar.addWidget(self.btn_reset)
        bar.addStretch(1)
        bar.addWidget(self.lab_path)

        lay = QVBoxLayout(self)
        lay.addWidget(tabs, 1)
        lay.addLayout(bar)
        self._load()

    # ------------------------------------------------------------- assistant
    def _page_assistant(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        intro = QLabel(
            t("L'assistant écoute le signal pendant quelques secondes, mesure le "
            "bruit, la dérive et la présence du réseau, puis propose un jeu "
            "complet de réglages — en expliquant chaque choix. Rien n'est "
            "appliqué sans votre accord."))
        intro.setWordWrap(True)
        lay.addWidget(intro)

        row = QHBoxLayout()
        self.sp_auto_seconds = QSpinBox()
        self.sp_auto_seconds.setRange(3, 120)
        self.sp_auto_seconds.setValue(12)
        self.sp_auto_seconds.setSuffix(t(" s d'écoute"))
        self.btn_auto = QPushButton(t("Lancer l'auto-configuration"))
        self.btn_auto.clicked.connect(self._start_auto)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        row.addWidget(self.sp_auto_seconds)
        row.addWidget(self.btn_auto)
        row.addWidget(self.progress, 1)
        lay.addLayout(row)

        self.auto_report = QPlainTextEdit()
        self.auto_report.setReadOnly(True)
        self.auto_report.setPlaceholderText(
            t("Le rapport de mesure et la justification de chaque réglage "
            "s'afficheront ici."))
        lay.addWidget(self.auto_report, 1)

        row2 = QHBoxLayout()
        self.btn_auto_apply = QPushButton(t("Appliquer les réglages proposés"))
        self.btn_auto_apply.setEnabled(False)
        self.btn_auto_apply.clicked.connect(self._apply_auto)
        row2.addWidget(self.btn_auto_apply)
        row2.addStretch(1)
        lay.addLayout(row2)
        return w

    def _start_auto(self) -> None:
        self.btn_auto.setEnabled(False)
        self.btn_auto_apply.setEnabled(False)
        self.auto_report.setPlainText("Écoute en cours…\n")
        self._auto_seconds = self.sp_auto_seconds.value()
        self._auto_elapsed = 0
        self._auto_timer = QTimer(self)
        self._auto_timer.timeout.connect(self._auto_tick)
        self._auto_timer.start(250)

    def _auto_tick(self) -> None:
        self._auto_elapsed += 0.25
        self.progress.setValue(int(100 * self._auto_elapsed / self._auto_seconds))
        if self._auto_elapsed < self._auto_seconds:
            return
        self._auto_timer.stop()
        self.progress.setValue(100)
        self.btn_auto.setEnabled(True)
        x = self.engine.recent(self._auto_seconds, raw=True)
        fs = self.engine.settings.acquisition.sample_rate
        res = autoconfig.analyse(x, fs,
                                 self.engine.settings.acquisition.input_range_v,
                                 self.engine.settings)
        self._auto_result = res
        lines = ["MESURES", "-------"] + res.summary()
        if res.warnings:
            lines += ["", "AVERTISSEMENTS", "--------------"] + \
                ["• " + w for w in res.warnings]
        if res.reasons:
            lines += ["", "RÉGLAGES PROPOSÉS", "-----------------"] + \
                ["• " + r for r in res.reasons]
        self.auto_report.setPlainText("\n".join(lines))
        self.btn_auto_apply.setEnabled(res.ok)

    def _apply_auto(self) -> None:
        if self._auto_result is None:
            return
        changed = autoconfig.apply(self._auto_result, self.engine.settings)
        self._load()
        self._apply()
        txt = self.auto_report.toPlainText()
        txt += "\n\nAPPLIQUÉ\n--------\n" + \
            ("\n".join("• " + c for c in changed) or "• rien à changer")
        self.auto_report.setPlainText(txt)

    # ----------------------------------------------------------- acquisition
    def _page_acquisition(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        box = QGroupBox(t("Source du signal"))
        f = QFormLayout(box)
        self.cb_source = QComboBox()
        for key, label in (("auto", t("Détection automatique (recommandé)")),
                           ("phytosense", t("Carte PhytoSense (classe audio)")),
                           ("audio", t("Entrée audio quelconque")),
                           ("serie", t("Port série (montage maison)")),
                           ("simulation", t("Générateur interne (sans matériel)"))):
            self.cb_source.addItem(label, key)
        self.cb_device = QComboBox()
        self.cb_device.setEditable(True)
        self.btn_scan = QPushButton(t("Rechercher les périphériques"))
        self.btn_scan.clicked.connect(self._scan_devices)
        self.sp_rate = QDoubleSpinBox()
        self.sp_rate.setRange(1.0, 48000.0)
        self.sp_rate.setDecimals(1)
        self.sp_rate.setSuffix(t(" Hz"))
        self.sp_channels = QSpinBox()
        self.sp_channels.setRange(1, 4)
        f.addRow(t("Source"), self.cb_source)
        f.addRow(t("Périphérique"), self.cb_device)
        f.addRow("", self.btn_scan)
        f.addRow(t("Échantillonnage"), self.sp_rate)
        f.addRow(t("Voies"), self.sp_channels)
        lay.addWidget(box)

        box2 = QGroupBox(t("Étalonnage de l'entrée"))
        f2 = QFormLayout(box2)
        self.sp_full_scale = QDoubleSpinBox()
        self.sp_full_scale.setRange(0.001, 100.0)
        self.sp_full_scale.setDecimals(4)
        self.sp_full_scale.setSuffix(t(" V"))
        self.sp_vpu = QDoubleSpinBox()
        self.sp_vpu.setRange(1e-9, 1e6)
        self.sp_vpu.setDecimals(9)
        self.cb_gain = QComboBox()
        self.cb_gain.addItem("automatique", 0)
        for g in (1, 2, 5, 10, 20, 50, 100, 200):
            self.cb_gain.addItem(f"×{g}", g)
        self.chk_invert = QCheckBox(t("inverser le signe du signal"))
        f2.addRow(t("Pleine échelle"), self.sp_full_scale)
        f2.addRow(t("Volts par unité source"), self.sp_vpu)
        f2.addRow(t("Gain matériel"), self.cb_gain)
        f2.addRow(self.chk_invert)
        lay.addWidget(box2)
        lay.addStretch(1)
        return w

    def _scan_devices(self) -> None:
        self.cb_device.clear()
        #  L'interface hôte est affichée : sous Windows le même matériel
        #  apparaît quatre fois, et c'est le seul moyen de savoir lequel on
        #  choisit. La valeur stockée reste le nom seul, pour ne pas invalider
        #  les fichiers de réglages existants — `AudioSource.resoudre()` se
        #  charge de retrouver la bonne occurrence au moment d'ouvrir.
        for d in AudioSource.list_devices():
            api = f" — {d['api']}" if d.get("api") else ""
            self.cb_device.addItem(
                f"{d['name']}{api}  ({d['channels']} voies)", d["name"])
        from ..core.protocol import ControlLink
        for p in ControlLink.discover():
            self.cb_device.addItem(f"série : {p}", p)
        if self.cb_device.count() == 0:
            self.cb_device.addItem(t("aucun périphérique détecté"), "")

    # ------------------------------------------------------------- traitement
    def _page_processing(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        box = QGroupBox(t("Filtrage"))
        f = QFormLayout(box)
        self.sp_hp = _spin(0.0, 100.0, 4, " Hz")
        self.sp_lp = _spin(0.0, 20000.0, 2, " Hz")
        self.cb_notch = QComboBox()
        for v, lab in ((0.0, t("désactivé")), (50.0, t("50 Hz (Europe)")),
                       (60.0, t("60 Hz (Amérique, Japon)"))):
            self.cb_notch.addItem(lab, v)
        self.sp_notch_q = _spin(1.0, 200.0, 1, "")
        self.sp_detrend = _spin(1.0, 3600.0, 1, " s")
        f.addRow(t("Passe-haut"), self.sp_hp)
        f.addRow(t("Passe-bas"), self.sp_lp)
        f.addRow(t("Réjecteur réseau"), self.cb_notch)
        f.addRow(t("Facteur Q du réjecteur"), self.sp_notch_q)
        f.addRow(t("Constante de la ligne de base"), self.sp_detrend)
        lay.addWidget(box)

        box2 = QGroupBox(t("Détection d'événements"))
        f2 = QFormLayout(box2)
        self.sp_sigma = _spin(0.5, 20.0, 2, " σ")
        self.sp_refractory = _spin(10.0, 10000.0, 0, " ms")
        self.sp_minamp = _spin(0.0, 10000.0, 1, " µV")
        f2.addRow(t("Seuil"), self.sp_sigma)
        f2.addRow(t("Période réfractaire"), self.sp_refractory)
        f2.addRow(t("Amplitude minimale"), self.sp_minamp)
        lay.addWidget(box2)
        help_ = QLabel(
            t("Le seuil est exprimé en écarts-types du signal courant : un "
            "montage bruyant déclenche donc autant qu'un montage propre. "
            "L'amplitude minimale, elle, est absolue : c'est elle qui empêche "
            "de sonifier le bruit de fond quand la plante ne fait rien."))
        help_.setWordWrap(True)
        help_.setStyleSheet(f"color:{self.p['texte2']};")
        lay.addWidget(help_)
        lay.addStretch(1)
        return w

    # ---------------------------------------------------------------- musique
    def _page_music(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        box = QGroupBox(t("Nuances et durées"))
        f = QFormLayout(box)
        self.sp_vmin = QSpinBox(); self.sp_vmin.setRange(1, 127)
        self.sp_vmax = QSpinBox(); self.sp_vmax.setRange(1, 127)
        self.sp_dmin = _spin(0.05, 30.0, 2, " s")
        self.sp_dmax = _spin(0.05, 60.0, 2, " s")
        self.sp_quant = _spin(0.0, 4000.0, 0, " ms")
        f.addRow(t("Nuance minimale"), self.sp_vmin)
        f.addRow(t("Nuance maximale"), self.sp_vmax)
        f.addRow(t("Durée minimale"), self.sp_dmin)
        f.addRow(t("Durée maximale"), self.sp_dmax)
        f.addRow(t("Quantification rythmique"), self.sp_quant)
        lay.addWidget(box)

        box2 = QGroupBox(t("Sortie MIDI"))
        f2 = QFormLayout(box2)
        self.chk_midi = QCheckBox(t("activer la sortie MIDI"))
        self.cb_midi_port = QComboBox()
        self.cb_midi_port.setEditable(True)
        self.btn_midi_scan = QPushButton(t("Rechercher les ports MIDI"))
        self.btn_midi_scan.clicked.connect(self._scan_midi)
        self.sp_midi_channel = QSpinBox(); self.sp_midi_channel.setRange(1, 16)
        f2.addRow(self.chk_midi)
        f2.addRow(t("Port"), self.cb_midi_port)
        f2.addRow("", self.btn_midi_scan)
        f2.addRow(t("Canal"), self.sp_midi_channel)
        lay.addWidget(box2)
        lay.addStretch(1)
        return w

    def _scan_midi(self) -> None:
        self.cb_midi_port.clear()
        ports = MidiOut.list_ports()
        if not ports:
            self.cb_midi_port.addItem(t("aucun port — un port virtuel sera créé"), "")
        for p in ports:
            self.cb_midi_port.addItem(p, p)

    # --------------------------------------------------------- enregistrement
    def _page_recording(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        box = QGroupBox(t("Fichiers"))
        f = QFormLayout(box)
        self.ed_dir = QLineEdit()
        self.btn_dir = QPushButton(t("Choisir…"))
        self.btn_dir.clicked.connect(self._pick_dir)
        self.chk_auto_rec = QCheckBox(t("démarrer l'enregistrement au lancement"))
        self.chk_wav = QCheckBox(t("signal brut (WAV 24 bits)"))
        self.chk_audio = QCheckBox(t("rendu musical (WAV 16 bits)"))
        self.chk_csv = QCheckBox(t("événements et notes (CSV)"))
        self.chk_raw_csv = QCheckBox(t("toutes les valeurs en CSV (fichiers volumineux)"))
        self.sp_echantillon = QDoubleSpinBox()
        self.sp_echantillon.setRange(2.0, 600.0)
        self.sp_echantillon.setDecimals(0)
        self.sp_echantillon.setSuffix(t(" s"))
        self.sp_echantillon.setToolTip(
            t("Durée gardée par la capture rapide (Ctrl+E). Le logiciel tient "
              "dix minutes de signal en mémoire : on peut donc remonter loin "
              "en arrière, après coup."))
        row = QHBoxLayout()
        row.addWidget(self.ed_dir, 1)
        row.addWidget(self.btn_dir)
        f.addRow(t("Répertoire"), row)
        f.addRow(self.chk_auto_rec)
        f.addRow(self.chk_wav)
        f.addRow(self.chk_audio)
        f.addRow(self.chk_csv)
        f.addRow(self.chk_raw_csv)
        f.addRow(t("Durée d'un échantillon (Ctrl+E)"), self.sp_echantillon)
        lay.addWidget(box)

        #  L'espace disque : ce qui reste, pour combien de temps, et à partir
        #  de quand le logiciel refermera la séance de lui-même.
        boite_disque = QGroupBox(t("Espace disque"))
        fd = QFormLayout(boite_disque)
        self.chk_disque = QCheckBox(t("surveiller l'espace pendant l'enregistrement"))
        self.chk_disque.setToolTip(
            t("Le rendu musical écrit environ trois cents mégaoctets par "
              "heure : un disque de démonstration se remplit en une nuit."))
        self.sp_reserve = QDoubleSpinBox()
        self.sp_reserve.setRange(50.0, 100000.0)
        self.sp_reserve.setDecimals(0)
        self.sp_reserve.setSuffix(t(" Mo"))
        self.sp_reserve.setToolTip(
            t("L'enregistrement est clos proprement en deçà. Cette réserve "
              "n'est pas pour le logiciel mais pour le système."))
        self.sp_alerte = QDoubleSpinBox()
        self.sp_alerte.setRange(1.0, 600.0)
        self.sp_alerte.setDecimals(0)
        self.sp_alerte.setSuffix(t(" min"))
        self.lab_disque = QLabel("")
        self.lab_disque.setWordWrap(True)
        self.lab_disque.setStyleSheet(f"color:{self.p['texte2']};")
        fd.addRow(self.chk_disque)
        fd.addRow(t("Réserve à préserver"), self.sp_reserve)
        fd.addRow(t("Prévenir quand il reste"), self.sp_alerte)
        fd.addRow(self.lab_disque)
        lay.addWidget(boite_disque)

        box2 = QGroupBox(t("Métadonnées de la séance"))
        f2 = QFormLayout(box2)
        self.ed_plante = QLineEdit()
        self.ed_lieu = QLineEdit()
        self.ed_operateur = QLineEdit()
        self.ed_notes = QPlainTextEdit()
        self.ed_notes.setMaximumHeight(90)
        f2.addRow(t("Plante"), self.ed_plante)
        f2.addRow(t("Lieu"), self.ed_lieu)
        f2.addRow(t("Opérateur"), self.ed_operateur)
        f2.addRow(t("Notes"), self.ed_notes)
        lay.addWidget(box2)
        lay.addStretch(1)
        return w

    def _pick_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(self, t("Répertoire des séances"),
                                             self.ed_dir.text())
        if d:
            self.ed_dir.setText(d)
            self.engine.settings.recording.directory = d
            self._maj_disque()

    def _maj_disque(self) -> None:
        """Ce que le disque choisi peut encaisser, en clair.

        Affiché ici et pas seulement pendant l'enregistrement : c'est avant de
        lancer une séance de nuit qu'il faut savoir qu'on n'a la place que pour
        deux heures.
        """
        from ..core import disk_space
        chemin = self.ed_dir.text() or self.engine.settings.recording.directory
        etat = disk_space.mesurer(chemin)
        if not etat.mesure:
            self.lab_disque.setText(t("Répertoire introuvable — il sera créé "
                                      "au premier enregistrement."))
            return
        reglages = self.engine.settings
        debit = disk_space.debit_mo_par_heure(reglages)
        reste = disk_space.autonomie_heures(etat.libre_mo,
                                        float(self.sp_reserve.value()), debit)
        self.lab_disque.setText(t(
            "{libre} libres sur {total} · {debit:.0f} Mo par heure "
            "d'enregistrement · autonomie {duree}").format(
                libre=disk_space.formater_mo(etat.libre_mo),
                total=disk_space.formater_mo(etat.total_mo),
                debit=debit, duree=disk_space.formater_duree(reste)))

    # -------------------------------------------------------------- interface
    def _page_ui(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self._groupe_langue())
        box = QGroupBox(t("Apparence"))
        f = QFormLayout(box)
        self.cb_theme = QComboBox()
        for key, lab in (("sombre", t("Sombre (défaut)")), ("clair", t("Clair")),
                         ("contraste", t("Contraste renforcé (accessibilité)"))):
            self.cb_theme.addItem(lab, key)
        self.sp_refresh = QSpinBox(); self.sp_refresh.setRange(5, 60)
        self.sp_refresh.setSuffix(t(" images/s"))
        self.sp_font = _spin(0.8, 2.0, 2, " ×")
        f.addRow(t("Thème"), self.cb_theme)
        f.addRow(t("Rafraîchissement"), self.sp_refresh)
        f.addRow(t("Taille du texte"), self.sp_font)
        lay.addWidget(box)
        note = QLabel(t("Le thème et la taille du texte s'appliquent immédiatement. "
                      "Le contraste renforcé respecte le niveau AAA des règles "
                      "d'accessibilité."))
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{self.p['texte2']};")
        lay.addWidget(note)
        lay.addStretch(1)
        return w

    # ------------------------------------------------------------------ langue
    def _groupe_langue(self) -> QWidget:
        """Le choix de la langue, et de quoi en ajouter une.

        Le taux de couverture est affiché sans fard : une langue traduite aux
        trois quarts reste utilisable — le quart manquant s'affiche en
        français — mais l'utilisateur a le droit de le savoir avant de choisir.
        """
        from ..i18n import LANGUE_SOURCE, langues_disponibles

        boite = QGroupBox(t("Langue"))
        f = QFormLayout(boite)
        self.cb_langue = QComboBox()
        cles = len(self._cles_traduisibles())
        for code, nom, nom_fr, n, sens in langues_disponibles():
            if code == LANGUE_SOURCE:
                origine = t("langue d'origine")
                libelle = f"{nom} — {origine}"
            else:
                part = 100.0 * n / max(cles, 1)
                libelle = f"{nom} — {t(nom_fr)} · {part:.0f} %"
            self.cb_langue.addItem(libelle, code)
        _set_data(self.cb_langue, self.engine.settings.ui.language)

        self.btn_modele_langue = QPushButton(t("Écrire un modèle de traduction…"))
        self.btn_modele_langue.setToolTip(
            t("Produit un fichier JSON contenant tous les libellés du logiciel, "
              "à traduire avec un éditeur de texte."))
        self.btn_modele_langue.clicked.connect(self._ecrire_modele_langue)

        note = QLabel(t("Le changement de langue prend effet au redémarrage. "
                        "Pour ajouter une langue : écrivez un modèle, "
                        "traduisez-le, et déposez-le dans le dossier "
                        "« langues » — elle apparaîtra dans cette liste au "
                        "démarrage suivant. Ce qui n'est pas traduit reste "
                        "affiché en français."))
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{self.p['texte2']};")

        f.addRow(t("Langue de l'interface"), self.cb_langue)
        f.addRow(self.btn_modele_langue)
        f.addRow(note)
        return boite

    _cles_cache = None                    # inventaire calculé une seule fois

    def _cles_traduisibles(self) -> list:
        if self._cles_cache is None:
            from ..i18n import collecter_cles
            try:
                self._cles_cache = collecter_cles()
            except Exception:                          # noqa: BLE001
                self._cles_cache = []
        return self._cles_cache

    def _ecrire_modele_langue(self) -> None:
        from ..i18n import DOSSIER, ecrire_modele
        code = self.cb_langue.currentData() or ""
        defaut = os.path.join(DOSSIER, f"{code or 'xx'}.json")
        chemin, _ = QFileDialog.getSaveFileName(
            self, t("Écrire un modèle de traduction"), defaut,
            t("Catalogue de traduction (*.json)"))
        if not chemin:
            return
        cles = self._cles_traduisibles()
        try:
            neuves = ecrire_modele(chemin, cles, code)
        except OSError as exc:
            QMessageBox.warning(self, t("Traduction"),
                                t("Écriture impossible : {erreur}").format(erreur=exc))
            return
        QMessageBox.information(
            self, t("Traduction"),
            t("{total} libellés écrits dans :\n{chemin}\n\n"
              "{neuves} restent à traduire. Les valeurs laissées vides "
              "s'afficheront en français.").format(
                  total=len(cles), chemin=os.path.abspath(chemin), neuves=neuves))

    # ----------------------------------------------------------------- expert
    def _page_modules(self) -> QWidget:
        """Lister les modules, et en activer ou désactiver un.

        Un module désactivé n'est pas désinstallé : son dossier reste, il
        cesse simplement d'être chargé. C'est ce qu'on veut quand on soupçonne
        un module d'être en cause — on l'écarte, on redémarre, on voit.
        """
        w = QWidget()
        lay = QVBoxLayout(w)

        entete = QLabel(t(
            "Les modules étendent le logiciel : analyses, représentations, "
            "sonifications, formats d'export. Décocher un module le laisse en "
            "place mais l'empêche d'être chargé au prochain démarrage."))
        entete.setWordWrap(True)
        entete.setStyleSheet(f"color:{self.p['texte2']};")
        lay.addWidget(entete)

        self.liste_modules = QTableWidget(0, 5)
        self.liste_modules.setHorizontalHeaderLabels(
            ["", t("Module"), t("Version"), t("Fournit"), t("État")])
        self.liste_modules.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.liste_modules.setAlternatingRowColors(True)
        self.liste_modules.verticalHeader().setVisible(False)
        self.liste_modules.horizontalHeader().setStretchLastSection(True)
        self.liste_modules.itemSelectionChanged.connect(self._module_choisi)
        lay.addWidget(self.liste_modules, 1)

        #  Le détail du module choisi : sa description, son auteur, ses
        #  réglages. Une liste seule ne dit pas ce qu'un module fait.
        self.detail_module = QLabel(t("Choisissez un module pour le décrire."))
        self.detail_module.setWordWrap(True)
        self.detail_module.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.detail_module.setOpenExternalLinks(True)
        self.detail_module.setStyleSheet(
            f"background:{self.p['fond3']};border:1px solid {self.p['trait']};"
            f"border-radius:5px;padding:8px;")
        self.detail_module.setMinimumHeight(110)
        lay.addWidget(self.detail_module)

        barre = QHBoxLayout()
        self.chk_modules_actifs = QCheckBox(t("Charger les modules au démarrage"))
        self.chk_modules_actifs.setToolTip(t(
            "Décocher démarre le logiciel SANS aucun module. C'est le mode "
            "sans échec : à employer quand un module empêche l'ouverture."))
        self.chk_modules_actifs.setChecked(
            getattr(self.engine.settings.modules, "charger_au_demarrage", True))
        self.chk_modules_actifs.stateChanged.connect(self._marquer_redemarrage)
        barre.addWidget(self.chk_modules_actifs)
        barre.addStretch(1)

        self.btn_modules_dossier = QPushButton(t("Ouvrir le dossier des modules"))
        self.btn_modules_dossier.setToolTip(t(
            "C'est là qu'on dépose un module écrit soi-même. Le SDK, livré "
            "avec le code source, contient un exemple et un outil qui en crée "
            "un nouveau."))
        self.btn_modules_dossier.clicked.connect(self._ouvrir_dossier_modules)
        barre.addWidget(self.btn_modules_dossier)
        lay.addLayout(barre)

        self.lab_modules_redemarrage = QLabel("")
        self.lab_modules_redemarrage.setStyleSheet(
            f"color:{self.p['or']};font-weight:bold;")
        lay.addWidget(self.lab_modules_redemarrage)

        self._remplir_modules()
        return w

    def _remplir_modules(self) -> None:
        registre = getattr(self.engine, "modules", None)
        if registre is None:
            return
        desactives = set(getattr(self.engine.settings.modules, "desactives", ()))
        lignes = registre.rapport()
        self.liste_modules.setRowCount(len(lignes))
        self._cases_modules = {}
        for i, l in enumerate(lignes):
            case = QCheckBox()
            case.setChecked(l["nom"] not in desactives)
            #  Un module intégré se désactive comme les autres : c'est le
            #  seul moyen de savoir si c'est lui qui pose problème.
            case.stateChanged.connect(
                lambda _=0, nom=l["nom"]: self._basculer_module(nom))
            conteneur = QWidget()
            boite = QHBoxLayout(conteneur)
            boite.setContentsMargins(6, 0, 0, 0)
            boite.addWidget(case)
            boite.addStretch(1)
            self.liste_modules.setCellWidget(i, 0, conteneur)
            self._cases_modules[l["nom"]] = case

            etat = l["faute"] or t(l["etat"])
            for col, valeur in enumerate((l["titre"], l["version"],
                                          l["capacites"] or t("aucune"), etat),
                                         start=1):
                cellule = QTableWidgetItem(str(valeur))
                cellule.setData(Qt.UserRole, l["nom"])
                if l["faute"]:
                    cellule.setForeground(QColor(self.p["alerte"]))
                    cellule.setToolTip(l["faute"])
                self.liste_modules.setItem(i, col, cellule)
        self.liste_modules.resizeColumnsToContents()

    def _basculer_module(self, nom: str) -> None:
        case = self._cases_modules.get(nom)
        if case is None:
            return
        desactives = list(getattr(self.engine.settings.modules, "desactives", []))
        if case.isChecked():
            desactives = [d for d in desactives if d != nom]
        elif nom not in desactives:
            desactives.append(nom)
        self.engine.settings.modules.desactives = sorted(desactives)
        self._marquer_redemarrage()

    def _marquer_redemarrage(self) -> None:
        #  On ne recharge PAS à chaud. Recharger un module dont des objets
        #  sont déjà référencés ailleurs laisse deux versions en mémoire et
        #  produit des bogues qu'on ne sait pas lire. Un redémarrage coûte
        #  trois secondes ; un bogue de rechargement coûte une soirée.
        self.engine.settings.modules.charger_au_demarrage = \
            self.chk_modules_actifs.isChecked()
        self.lab_modules_redemarrage.setText(
            t("⟳ Le changement prendra effet au prochain démarrage."))

    def _module_choisi(self) -> None:
        lignes = self.liste_modules.selectedItems()
        if not lignes:
            return
        nom = lignes[0].data(Qt.UserRole)
        registre = getattr(self.engine, "modules", None)
        m = registre.modules.get(nom) if registre else None
        if m is None:
            return
        man = m.manifeste
        morceaux = [f"<b>{man.titre}</b> — {man.version}"]
        if man.description:
            morceaux.append(t(man.description))
        details = []
        if man.auteur:
            details.append(f"{t('Auteur')} : {man.auteur}")
        if man.licence:
            details.append(f"{t('Licence')} : {man.licence}")
        details.append(f"API : {man.api}")
        details.append(f"{t('Origine')} : {t(m.origine)}")
        if man.exige:
            details.append(f"{t('Exige')} : {', '.join(man.exige)}")
        if man.depend_de:
            details.append(f"{t('Dépend de')} : {', '.join(man.depend_de)}")
        morceaux.append("<span style='color:%s'>%s</span>"
                        % (self.p["texte2"], " · ".join(details)))
        if man.site:
            morceaux.append(f"<a href='{man.site}' style='color:{self.p['accent2']}'>"
                            f"{man.site}</a>")
        if m.faute:
            morceaux.append("<span style='color:%s'><b>%s</b> %s</span>"
                            % (self.p["alerte"], t("Écarté :"), m.faute))
        self.detail_module.setText("<br/>".join(morceaux))

    def _ouvrir_dossier_modules(self) -> None:
        import os
        from ..api import Registre
        dossier = Registre.dossier_utilisateur()
        os.makedirs(dossier, exist_ok=True)
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QColor, QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(dossier))

    def _page_expert(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        box = QGroupBox(t("Profils de réglages"))
        f = QFormLayout(box)
        self.cb_profile = QComboBox()
        self.btn_profile_load = QPushButton(t("Charger"))
        self.btn_profile_load.clicked.connect(self._load_profile)
        self.ed_profile = QLineEdit()
        self.btn_profile_save = QPushButton(t("Enregistrer sous ce nom"))
        self.btn_profile_save.clicked.connect(self._save_profile)
        f.addRow(t("Profils disponibles"), self.cb_profile)
        f.addRow("", self.btn_profile_load)
        f.addRow(t("Nouveau profil"), self.ed_profile)
        f.addRow("", self.btn_profile_save)
        lay.addWidget(box)

        box2 = QGroupBox(t("Diagnostic"))
        f2 = QFormLayout(box2)
        self.lab_diag = QPlainTextEdit()
        self.lab_diag.setReadOnly(True)
        self.btn_diag = QPushButton(t("Rafraîchir le diagnostic"))
        self.btn_diag.clicked.connect(self._diagnose)
        f2.addRow(self.btn_diag)
        f2.addRow(self.lab_diag)
        lay.addWidget(box2, 1)
        return w

    def _diagnose(self) -> None:
        import platform
        import sys as _sys
        from .. import __version__
        lines = [f"PhytoScope {__version__}",
                 f"Python {_sys.version.split()[0]} — {platform.platform()}"]
        for mod in ("numpy", "PySide6", "pyqtgraph", "sounddevice", "serial",
                    "rtmidi"):
            try:
                m = __import__(mod)
                v = getattr(m, "__version__", "présent")
                lines.append(f"  {mod:<12} {v}")
            except Exception:
                lines.append(f"  {mod:<12} ABSENT")
        st = self.engine.state
        lines += ["", f"Source : {st.source_name} ({st.source_kind})",
                  f"Échantillons : {st.samples}",
                  f"Blocs perdus : {st.dropped_blocks}",
                  f"Charge du fil de traitement : {st.cpu_load * 100:.0f} %"]
        if st.board is not None:
            lines += ["", "Carte : " + st.board.describe()]
        lines += ["", "Sorties audio détectées :"]
        lines += ["  " + n for n in AudioOutput.list_devices()[:12]] or ["  aucune"]
        self.lab_diag.setPlainText("\n".join(lines))

    def _load_profile(self) -> None:
        name = self.cb_profile.currentText()
        if not name:
            return
        from ..config import Settings
        path = os.path.join(self.engine.settings.profiles_dir(), f"{name}.json")
        loaded = Settings.load(path)
        self.engine.settings.__dict__.update(loaded.__dict__)
        self._load()
        self._apply()

    def _save_profile(self) -> None:
        name = self.ed_profile.text().strip()
        if not name:
            return
        self._collect()
        self.engine.settings.export_profile(name)
        self._refresh_profiles()

    def _refresh_profiles(self) -> None:
        self.cb_profile.clear()
        self.cb_profile.addItems(self.engine.settings.list_profiles())

    # ------------------------------------------------------- charge / collecte
    def _load(self) -> None:
        s = self.engine.settings
        a, p, m, r, u = (s.acquisition, s.processing, s.music, s.recording, s.ui)
        _set_data(self.cb_source, a.source)
        self.cb_device.setEditText(a.device)
        self.sp_rate.setValue(a.sample_rate)
        self.sp_channels.setValue(max(a.channels, 1))
        self.sp_full_scale.setValue(a.input_range_v)
        self.sp_vpu.setValue(a.volts_per_unit)
        _set_data(self.cb_gain, a.hardware_gain)
        self.chk_invert.setChecked(a.invert)

        self.sp_hp.setValue(p.highpass_hz)
        self.sp_lp.setValue(p.lowpass_hz)
        _set_data(self.cb_notch, p.notch_hz)
        self.sp_notch_q.setValue(p.notch_q)
        self.sp_detrend.setValue(p.detrend_seconds)
        self.sp_sigma.setValue(p.event_threshold_sigma)
        self.sp_refractory.setValue(p.event_refractory_ms)
        self.sp_minamp.setValue(p.event_min_amplitude_uv)

        self.sp_vmin.setValue(m.velocity_min)
        self.sp_vmax.setValue(m.velocity_max)
        self.sp_dmin.setValue(m.note_len_min_s)
        self.sp_dmax.setValue(m.note_len_max_s)
        self.sp_quant.setValue(m.quantize_ms)
        self.chk_midi.setChecked(m.midi_enabled)
        self.cb_midi_port.setEditText(m.midi_port)
        self.sp_midi_channel.setValue(m.midi_channel)

        self.ed_dir.setText(r.directory)
        self.chk_auto_rec.setChecked(r.auto_start)
        self.chk_wav.setChecked(r.write_wav)
        self.chk_audio.setChecked(r.write_audio)
        self.chk_csv.setChecked(r.write_csv)
        self.chk_raw_csv.setChecked(r.write_raw_csv)
        self.ed_plante.setText(s.metadata.get("plante", ""))
        self.ed_lieu.setText(s.metadata.get("lieu", ""))
        self.ed_operateur.setText(s.metadata.get("operateur", ""))
        self.ed_notes.setPlainText(s.metadata.get("notes", ""))

        self.sp_echantillon.setValue(r.sample_seconds)
        self.chk_disque.setChecked(r.watch_disk)
        self.sp_reserve.setValue(r.reserve_mb)
        self.sp_alerte.setValue(r.warn_minutes)
        self._maj_disque()
        _set_data(self.cb_theme, u.theme)
        _set_data(self.cb_langue, u.language)
        self.sp_refresh.setValue(u.refresh_hz)
        self.sp_font.setValue(u.accessible_font_scale)
        self.lab_path.setText(s.default_path())
        self._refresh_profiles()

    def _collect(self) -> None:
        s = self.engine.settings
        a, p, m, r, u = (s.acquisition, s.processing, s.music, s.recording, s.ui)
        a.source = self.cb_source.currentData()
        a.device = (self.cb_device.currentData()
                    if self.cb_device.currentData() else self.cb_device.currentText())
        a.sample_rate = self.sp_rate.value()
        a.channels = self.sp_channels.value()
        a.input_range_v = self.sp_full_scale.value()
        a.volts_per_unit = self.sp_vpu.value()
        a.hardware_gain = int(self.cb_gain.currentData() or 0)
        a.invert = self.chk_invert.isChecked()

        p.highpass_hz = self.sp_hp.value()
        p.lowpass_hz = self.sp_lp.value()
        p.notch_hz = float(self.cb_notch.currentData() or 0.0)
        p.notch_q = self.sp_notch_q.value()
        p.detrend_seconds = self.sp_detrend.value()
        p.event_threshold_sigma = self.sp_sigma.value()
        p.event_refractory_ms = self.sp_refractory.value()
        p.event_min_amplitude_uv = self.sp_minamp.value()

        m.velocity_min = self.sp_vmin.value()
        m.velocity_max = max(self.sp_vmax.value(), self.sp_vmin.value())
        m.note_len_min_s = self.sp_dmin.value()
        m.note_len_max_s = max(self.sp_dmax.value(), self.sp_dmin.value())
        m.quantize_ms = self.sp_quant.value()
        m.midi_enabled = self.chk_midi.isChecked()
        m.midi_port = (self.cb_midi_port.currentData()
                       if self.cb_midi_port.currentData()
                       else self.cb_midi_port.currentText())
        m.midi_channel = self.sp_midi_channel.value()

        r.directory = self.ed_dir.text().strip() or r.directory
        r.auto_start = self.chk_auto_rec.isChecked()
        r.write_wav = self.chk_wav.isChecked()
        r.write_audio = self.chk_audio.isChecked()
        r.write_csv = self.chk_csv.isChecked()
        r.write_raw_csv = self.chk_raw_csv.isChecked()
        s.metadata.update({"plante": self.ed_plante.text(),
                           "lieu": self.ed_lieu.text(),
                           "operateur": self.ed_operateur.text(),
                           "notes": self.ed_notes.toPlainText()})

        r.sample_seconds = float(self.sp_echantillon.value())
        r.watch_disk = self.chk_disque.isChecked()
        r.reserve_mb = float(self.sp_reserve.value())
        r.warn_minutes = float(self.sp_alerte.value())
        u.theme = self.cb_theme.currentData()
        u.language = self.cb_langue.currentData() or "fr"
        u.refresh_hz = self.sp_refresh.value()
        u.accessible_font_scale = self.sp_font.value()

    # -- actions -------------------------------------------------------------
    def _apply(self) -> None:
        avant = self.engine.settings.ui.language
        self._collect()
        self.engine.apply_settings()
        if self.on_apply:
            self.on_apply()
        if self.engine.settings.ui.language != avant:
            self._proposer_redemarrage()

    def _proposer_redemarrage(self) -> None:
        """La langue ne change qu'au redémarrage : autant le proposer.

        Les libellés sont traduits à la construction de l'interface, non à
        l'affichage. Les réécrire à chaud demanderait que chaque widget se
        souvienne de sa phrase d'origine — beaucoup de code pour une opération
        qu'on fait une fois. On propose donc de relancer, après avoir sauvé les
        réglages : un enregistrement en cours est clos proprement au passage.
        """
        from ..i18n import langue_courante, meta
        nom = meta(self.engine.settings.ui.language)["nom"]
        reponse = QMessageBox.question(
            self, t("Langue"),
            t("L'interface sera en {langue} au prochain démarrage.\n\n"
              "Redémarrer maintenant ?").format(langue=nom),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        try:
            self.engine.settings.save()
        except OSError:                                # pragma: no cover
            pass
        if reponse != QMessageBox.Yes:
            return
        import sys as _sys
        from PySide6.QtCore import QProcess
        from PySide6.QtWidgets import QApplication
        fenetre = self.window()
        arret = getattr(fenetre, "arret_immediat", None)
        if callable(arret):
            arret()
        commande, arguments = _commande_de_relance()
        QProcess.startDetached(commande, arguments)
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _save(self) -> None:
        self._collect()
        path = self.engine.settings.save()
        QMessageBox.information(self, t("Réglages enregistrés"), path)

    def _reset(self) -> None:
        from ..config import Settings
        if QMessageBox.question(self, t("Réinitialiser"),
                                t("Revenir à tous les réglages par défaut ?")) \
                != QMessageBox.Yes:
            return
        fresh = Settings()
        self.engine.settings.__dict__.update(fresh.__dict__)
        self._load()
        self._apply()

    def refresh(self, state) -> None:
        #  Une fois toutes les cinq secondes suffit : c'est un disque, pas un
        #  signal.
        import time as _t
        if _t.monotonic() - getattr(self, "_disque_vu", 0.0) > 5.0:
            self._disque_vu = _t.monotonic()
            try:
                self._maj_disque()
            except Exception:                          # noqa: BLE001
                pass
        pass


# ---------------------------------------------------------------------------
def _spin(lo: float, hi: float, decimals: int, suffix: str) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(lo, hi)
    s.setDecimals(decimals)
    s.setSuffix(suffix)
    s.setSingleStep(10 ** -decimals if decimals else 1.0)
    return s


def _set_data(combo: QComboBox, value) -> None:
    for i in range(combo.count()):
        if combo.itemData(i) == value:
            combo.setCurrentIndex(i)
            return


def _scroll(w: QWidget) -> QScrollArea:
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(w)
    sa.setFrameShape(QScrollArea.NoFrame)
    return sa


def _commande_de_relance():
    """De quoi relancer le logiciel, quelle que soit la façon dont il fut lancé.

    `sys.argv[0]` n'est pas toujours relançable. Lancé par
    ``python -m phytoscope``, il vaut ``…/phytoscope/__main__.py`` ; réexécuter
    ce fichier directement casse tous les imports relatifs — ``from .config
    import Settings`` ne trouve plus son paquet. On reconstruit donc la
    commande : ``-m phytoscope`` dans ce cas, le script tel quel s'il en est un,
    et l'exécutable lui-même s'il s'agit d'un binaire gelé.
    """
    import os
    import sys
    if getattr(sys, "frozen", False):                  # PyInstaller et consorts
        return sys.executable, list(sys.argv[1:])
    premier = sys.argv[0] if sys.argv else ""
    nom = os.path.basename(premier)
    if nom == "__main__.py" or not premier:
        return sys.executable, ["-m", "phytoscope"] + list(sys.argv[1:])
    return sys.executable, [premier] + list(sys.argv[1:])
