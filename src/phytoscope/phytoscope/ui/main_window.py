# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/main_window.py
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

"""Fenêtre principale : barre d'outils, onglets, bandeau d'état.

Un seul chronomètre rafraîchit toute l'interface, à la cadence choisie par
l'utilisateur. L'interface ne calcule rien : elle lit l'instantané publié
par le moteur. C'est ce qui permet de baisser le rafraîchissement à 5 im/s
sur un vieux portable sans rien perdre de la mesure ni de l'enregistrement.
"""
from __future__ import annotations

import sys

import os
from typing import Optional

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QHBoxLayout,
                               QInputDialog, QLabel, QMainWindow, QMessageBox,
                               QPushButton, QSizePolicy, QSlider, QStatusBar,
                               QTabWidget, QToolBar, QVBoxLayout, QWidget)

from .. import APP_NAME, APP_TAGLINE, VERSION, __version__
from ..core.logging_setup import get_logger

_log = get_logger(__name__)
from ..version import RELEASE_NAME
from ..core.engine import Engine
from . import theme
from .diag_tab import DiagTab
from .features_tab import FeaturesTab
from .library_tab import LibraryTab
from .plot_tab import PlotTab
from .settings_tab import SettingsTab
from .tabs import ListenTab, MeterTab, ScopeTab, SpectrumTab
from .voice_tab import VoiceTab
from .widgets import StatusStrip
from ..i18n import t


class MainWindow(QMainWindow):
    note_played = Signal(object)
    enonce_dit = Signal(object)
    message_arrived = Signal(str)
    carte_arrivee = Signal()

    def __init__(self, settings, splash=None):
        super().__init__()
        self._splash = splash
        self._arrete = False
        #  Ce qu'on a déjà annoncé aux modules, pour ne publier
        #  que les changements.
        self._dernier_etat_modules = {}
        self.settings = settings
        self.engine = Engine(settings)
        self.engine.on_note = self._on_note_threadsafe
        self.engine.on_enonce = self._on_enonce_threadsafe
        self.engine.on_message = self._on_message_threadsafe
        self.note_played.connect(self._on_note)
        self.enonce_dit.connect(self._on_enonce)
        self.message_arrived.connect(self._on_message)
        self.carte_arrivee.connect(self._basculer_sur_carte)

        self.setWindowTitle(f"{APP_NAME} {VERSION} — {APP_TAGLINE}")
        self.resize(1280, 820)
        #  Une taille minimale explicite, sinon Qt retient celle que réclame la
        #  page la plus haute — plus d'un millier de pixels — et la fenêtre ne
        #  peut plus être réduite sur l'écran d'un portable. Les pages hautes
        #  défilent à l'intérieur de leur onglet.
        self.setMinimumSize(880, 520)
        self.p = theme.palette(settings.ui.theme)

        # L'emblème : une fleur de lotus blanche, dessinée par le programme.
        try:
            from .icon import app_icon
            icone = app_icon()
            self.setWindowIcon(icone)
            app = QApplication.instance()
            if app is not None:
                app.setWindowIcon(icone)
        except Exception:                              # pragma: no cover
            pass

        # Le chronomètre doit exister AVANT les onglets : leur construction
        # déclenche déjà des rappels de réglages, qui l'interrogent.
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)

        self._build_toolbar()
        self._build_menus()

        self.tabs = QTabWidget()
        self.tab_scope = ScopeTab(self.engine, self.p)
        self.tab_meter = MeterTab(self.engine, self.p)
        self.tab_spectrum = SpectrumTab(self.engine, self.p)
        self.tab_listen = ListenTab(self.engine, self.p, self._settings_changed)
        self.tab_voice = VoiceTab(self.engine, self.p, self._settings_changed)
        self.tab_features = FeaturesTab(self.engine, self.p,
                                        self._settings_changed)
        self.tab_plot = PlotTab(self.engine, self.p)
        self.tab_library = LibraryTab(self.engine, self.p)
        self.tab_diag = DiagTab(self.engine, self.p, self._settings_changed)
        self.tab_settings = SettingsTab(self.engine, self.p, self._settings_changed)
        for w, name in ((self.tab_scope, t("Oscilloscope")),
                        (self.tab_meter, t("Multimeter")),
                        (self.tab_spectrum, t("Analyser")),
                        (self.tab_features, t("Descriptors")),
                        (self.tab_plot, t("Plotter")),
                        (self.tab_listen, t("Listening")),
                        (self.tab_voice, t("Speech")),
                        (self.tab_library, t("Library")),
                        (self.tab_diag, t("Diagnostics")),
                        (self.tab_settings, t("Settings"))):
            self.tabs.addTab(w, name)

        #  À gauche la clé interne, à droite le libellé traduit : le reste du
        #  code désigne les cases par la clé, qui ne change jamais de langue.
        cases = {"state": t("state"), "source": t("source"), "duration": t("duration"),
                 "clock": t("clock"), "saturation": t("saturation"),
                 "drift": t("drift"), "events": t("events"),
                 "output": t("output"), "recording": t("recording")}
        self.strip = StatusStrip(self.p, list(cases), libelles=cases)

        self.banniere = QLabel("")
        self.banniere.setVisible(False)
        self.banniere.setStyleSheet(
            f"background:{self.p['background3']};color:{self.p['gold']};"
            f"border:1px solid {self.p['gold']};border-radius:5px;padding:6px;")

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.addWidget(self.banniere)
        lay.addWidget(self.tabs, 1)
        lay.addWidget(self.strip)
        self.setCentralWidget(central)

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage(t("Ready."))
        self._etape("démarrage de l'acquisition…")

        self.apply_theme()
        self._etape("ouverture du moteur audio…")
        self.engine.start()
        self._surveiller_carte()
        self.timer.start(max(int(1000 / max(settings.ui.refresh_hz, 1)), 16))

    # ---------------------------------------------------------------- barre
    def _build_toolbar(self) -> None:
        """Barre d'outils : tout ce qui doit rester accessible en permanence.

        Le principe retenu est qu'aucun réglage courant ne doit obliger à
        changer d'onglet pendant une séance : volume, coupure du son, timbre,
        gamme et profil sont donc ici, et agissent à chaud.
        """
        tb = QToolBar(t("Main"))
        tb.setMovable(False)
        tb.setObjectName("barre-principale")
        self.addToolBar(tb)

        self.act_record = QAction(t("● Record"), self)
        self.act_record.setCheckable(True)
        self.act_record.setShortcut(QKeySequence("Ctrl+R"))
        self.act_record.setToolTip(t("Start or stop recording (Ctrl+R)"))
        self.act_record.triggered.connect(self._toggle_record)
        tb.addAction(self.act_record)

        self.act_mark = QAction(t("Marker…"), self)
        self.act_mark.setShortcut(QKeySequence("Ctrl+M"))
        self.act_mark.setToolTip(t("Drop a time-stamped annotation (Ctrl+M)"))
        self.act_mark.triggered.connect(self._mark)
        tb.addAction(self.act_mark)

        #  La capture d'échantillon : un geste, et la minute écoulée est gardée.
        #  Elle vit à côté de l'enregistrement parce qu'elle répond à la même
        #  question — « garder ce qui vient de se passer » — sans rien engager.
        self.act_sample = QAction(t("⧉ Sample"), self)
        self.act_sample.setShortcut(QKeySequence("Ctrl+E"))
        self.act_sample.setToolTip(
            t("Keeps on disk the signal that has just gone by, without starting a recording (Ctrl+E)"))
        self.act_sample.triggered.connect(self._capturer_echantillon)
        tb.addAction(self.act_sample)

        tb.addSeparator()

        # --- choix musicaux, applicables à chaud ---------------------------
        from ..music.instruments import instrument_list
        from ..music.profiles import profile_list
        from ..music.scales import diapason_list, scale_names

        tb.addWidget(QLabel(t(" Preset ")))
        self.cb_profil = QComboBox()
        self.cb_profil.setToolTip(t("A complete musical setting, recalled in one gesture"))
        self.cb_profil.addItem(t("— custom —"), "")
        for cle, libelle in profile_list():
            self.cb_profil.addItem(t(libelle), cle)
        self.cb_profil.currentIndexChanged.connect(self._profil_change)
        tb.addWidget(self.cb_profil)

        tb.addWidget(QLabel(t(" Timbre ")))
        self.cb_instrument = QComboBox()
        self.cb_instrument.setToolTip(t("Timbre of the internal synthesiser"))
        for cle, libelle in instrument_list():
            self.cb_instrument.addItem(t(libelle), cle)
        _choisir(self.cb_instrument, self.settings.music.instrument)
        self.cb_instrument.currentIndexChanged.connect(self._musique_change)
        tb.addWidget(self.cb_instrument)

        tb.addWidget(QLabel(t(" Scale ")))
        self.cb_gamme = QComboBox()
        for cle, libelle in scale_names():
            self.cb_gamme.addItem(t(libelle), cle)
        _choisir(self.cb_gamme, self.settings.music.scale)
        self.cb_gamme.currentIndexChanged.connect(self._musique_change)
        tb.addWidget(self.cb_gamme)

        tb.addWidget(QLabel(t(" Tuning ")))
        self.cb_diapason = QComboBox()
        self.cb_diapason.setToolTip(t("Frequency of the reference A"))
        for cle, libelle in diapason_list():
            self.cb_diapason.addItem(cle + " Hz", float(cle))
        _choisir(self.cb_diapason, float(self.settings.music.diapason_hz))
        self.cb_diapason.currentIndexChanged.connect(self._musique_change)
        tb.addWidget(self.cb_diapason)

        tb.addSeparator()

        # --- volume, toujours accessible -----------------------------------
        self.act_mute = QAction(t("🔇 Mute"), self)
        self.act_mute.setCheckable(True)
        self.act_mute.setShortcut(QKeySequence("Ctrl+K"))
        self.act_mute.setToolTip(t("Mute without stopping the measurement (Ctrl+K)"))
        self.act_mute.triggered.connect(self._muet)
        tb.addAction(self.act_mute)

        tb.addWidget(QLabel(t(" Volume ")))
        self.sl_volume = QSlider(Qt.Horizontal)
        self.sl_volume.setRange(-40, 12)
        self.sl_volume.setValue(int(self.settings.music.master_gain_db))
        self.sl_volume.setFixedWidth(130)
        self.sl_volume.setToolTip(t("Output volume, in decibels"))
        self.sl_volume.valueChanged.connect(self._volume_change)
        tb.addWidget(self.sl_volume)
        self.lab_volume = QLabel(f"{self.settings.music.master_gain_db:+.0f} dB")
        self.lab_volume.setFixedWidth(52)
        tb.addWidget(self.lab_volume)

        self.act_test_hp = QAction(t("Speaker test"), self)
        self.act_test_hp.setToolTip(t("Emits a 1 kHz beep to check the output"))
        self.act_test_hp.triggered.connect(self._test_hp)
        tb.addAction(self.act_test_hp)

        tb.addSeparator()
        self.act_restart = QAction(t("Restart"), self)
        self.act_restart.setToolTip(t("Restarts acquisition and detects the source again"))
        self.act_restart.triggered.connect(self._restart)
        tb.addAction(self.act_restart)

        self.act_auto = QAction(t("Auto-setup"), self)
        self.act_auto.setShortcut(QKeySequence("Ctrl+A"))
        self.act_auto.triggered.connect(self._goto_auto)
        tb.addAction(self.act_auto)

        #  Le zoom est une fonction de pyqtgraph ; le retour à l'origine, lui,
        #  doit être à portée de main, sinon l'utilisateur croit l'acquisition
        #  arrêtée alors qu'il a simplement zoomé hors du signal.
        self.act_zoom = QAction(t("⟲ Reset zoom"), self)
        self.act_zoom.setShortcut(QKeySequence("Ctrl+0"))
        self.act_zoom.setToolTip(
            t("Brings every plot in this tab back to its original framing (Ctrl+0)"))
        self.act_zoom.triggered.connect(self._reinitialiser_zoom)
        #  Grisée tant qu'aucun tracé n'est déplacé : l'état du bouton dit
        #  quelque chose de vrai sur l'écran.
        self.act_zoom.setEnabled(False)
        tb.addAction(self.act_zoom)

        self.act_panic = QAction(t("Silence"), self)
        #  ⌘. est depuis toujours « annuler l'opération en cours » sur macOS :
        #  Cocoa peut l'intercepter, et l'utilisateur ne s'attend pas à couper
        #  le son en le tapant. On y met ⌘⇧. — libre, et voisin.
        self.act_panic.setShortcut(QKeySequence(
            "Ctrl+Shift+." if sys.platform == "darwin" else "Ctrl+."))
        self.act_panic.setToolTip(
            t("Silences every note being played ({touches})").format(
                touches=self.act_panic.shortcut().toString()))
        self.act_panic.triggered.connect(self._panic)
        tb.addAction(self.act_panic)

        # Espace élastique : pousse « À propos » et « Quitter » à droite.
        vide = QWidget()
        vide.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(vide)

        #  La langue, à portée de main : la chercher dans les réglages quand
        #  l'interface est dans une langue qu'on ne lit pas est une épreuve.
        from ..i18n import LANGUE_SOURCE, langues_disponibles
        tb.addWidget(QLabel(" 🌐 "))
        self.cb_langue = QComboBox()
        self.cb_langue.setToolTip(t("Interface language — takes effect on restart"))
        for code, nom, nom_fr, n, sens in langues_disponibles():
            self.cb_langue.addItem(nom, code)
        _choisir(self.cb_langue, self.settings.ui.language)
        self.cb_langue.currentIndexChanged.connect(self._langue_change)
        tb.addWidget(self.cb_langue)

        #  L'aide, « À propos » et « Quitter » vivent dans la barre de menus :
        #  une barre d'outils qui déborde les escamote sans prévenir, et c'est
        #  exactement ce qui s'est produit. Les raccourcis, eux, restent
        #  attachés aux mêmes actions et fonctionnent partout.
        self.act_help = QAction(t("Help"), self)
        self.act_help.setShortcut(QKeySequence("F1"))
        self.act_help.setShortcutContext(Qt.ApplicationShortcut)
        self.act_help.setToolTip(t("Getting started, shortcuts, description of the tabs (F1)"))
        self.act_help.triggered.connect(self._aide)
        tb.addAction(self.act_help)

        self.act_about = QAction(t("About"), self)
        self.act_about.setShortcut(QKeySequence("Shift+F1"))
        self.act_about.setShortcutContext(Qt.ApplicationShortcut)
        self.act_about.setToolTip(t("Version, author, installed components (Shift+F1)"))
        self.act_about.triggered.connect(self._about)

        #  Le journal : accessible sans terminal et sans chercher où le
        #  fichier se trouve — c'est la première chose qu'on demande quand
        #  quelque chose s'est mal passé.
        self.act_journal = QAction(t("Application log…"), self)
        self.act_journal.setShortcut(QKeySequence("Ctrl+L"))
        self.act_journal.setShortcutContext(Qt.ApplicationShortcut)
        self.act_journal.setToolTip(
            t("Shows the log file live, says where it is, and lets you save a copy of it (Ctrl+L)"))
        self.act_journal.triggered.connect(self._journal)
        self.addAction(self.act_journal)

        self.act_quit = QAction(t("Quit"), self)
        self.act_quit.setShortcut(QKeySequence("Ctrl+Q"))
        self.act_quit.setShortcutContext(Qt.ApplicationShortcut)
        self.act_quit.triggered.connect(self._quitter)
        self.addAction(self.act_quit)

    # ---------------------------------------------------------------- menus
    def _build_menus(self) -> None:
        """Une barre de menus, parce qu'une barre d'outils peut déborder.

        Leçon apprise à mes dépens : en ajoutant des boutons, la barre d'outils
        a dépassé la largeur de la fenêtre, et Qt a discrètement rangé l'aide,
        « À propos » et « Quitter » derrière un chevron « » ». Une barre de
        menus, elle, ne tronque jamais rien — et c'est de toute façon là qu'on
        cherche l'aide et la version d'un logiciel.

        Les mêmes objets `QAction` servent ici et dans la barre d'outils : un
        seul raccourci, un seul état, aucune divergence possible.
        """
        barre = self.menuBar()
        barre.setNativeMenuBar(False)      # même disposition sur les trois systèmes

        seance = barre.addMenu(t("&Session"))
        seance.addAction(self.act_record)
        seance.addAction(self.act_mark)
        seance.addAction(self.act_sample)
        self.act_charger = QAction(t("Load a recording…"), self)
        self.act_charger.setToolTip(
            t("Replays a file taken from anywhere; live acquisition is then suspended."))
        self.act_charger.triggered.connect(self._charger_enregistrement)
        seance.addAction(self.act_charger)
        seance.addSeparator()
        seance.addAction(self.act_auto)
        seance.addAction(self.act_restart)
        seance.addSeparator()
        seance.addAction(self.act_quit)

        affichage = barre.addMenu(t("&View"))
        affichage.addAction(self.act_zoom)
        affichage.addSeparator()
        affichage.addAction(self.act_mute)
        affichage.addAction(self.act_panic)
        affichage.addAction(self.act_test_hp)
        affichage.addSeparator()
        self.menu_langue = affichage.addMenu(t("Language"))
        self._remplir_menu_langue()

        aide = barre.addMenu(t("&Help"))
        aide.addAction(self.act_help)
        aide.addAction(self.act_about)
        aide.addSeparator()
        aide.addAction(self.act_journal)
        aide.addSeparator()
        self.act_maj = QAction(t("Library updates…"), self)
        self.act_maj.setToolTip(
            t("Compares the installed Python libraries with what the package index publishes. Installs nothing unless you ask."))
        self.act_maj.triggered.connect(self._mises_a_jour)
        aide.addAction(self.act_maj)
        aide.addSeparator()
        self.act_site = QAction(t("Open the website"), self)
        self.act_site.triggered.connect(self._ouvrir_site)
        aide.addAction(self.act_site)

    def _mises_a_jour(self) -> None:
        """Ouvre la fenêtre des mises à jour des bibliothèques Python.

        La racine des exigences lui est passée pour qu'elle puisse afficher
        la contrainte déclarée (« >=1.24 ») à côté de la version installée :
        sans elle, on ne sait pas si une version ancienne est un retard ou un
        choix.
        """
        import os

        from .updates_dialog import MajDialog

        #  requirements.txt vit à la racine du logiciel, deux niveaux au-dessus
        #  de ce fichier — et non dans le paquet Python, qui voyage seul dans
        #  une installation.
        racine = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        if not os.path.exists(os.path.join(racine, "requirements.txt")):
            racine = ""
        MajDialog(getattr(self, "palette_couleurs", None), racine, self).exec()

    def _remplir_menu_langue(self) -> None:
        """Les langues disponibles, cochables, dans le menu Affichage."""
        from PySide6.QtGui import QActionGroup
        from ..i18n import langues_disponibles
        self.menu_langue.clear()
        groupe = QActionGroup(self)
        groupe.setExclusive(True)
        for code, nom, nom_fr, n, sens in langues_disponibles():
            action = QAction(nom, self)
            action.setCheckable(True)
            action.setChecked(code == self.settings.ui.language)
            action.setData(code)
            action.triggered.connect(
                lambda _=False, c=code: self._choisir_langue(c))
            groupe.addAction(action)
            self.menu_langue.addAction(action)

    def _choisir_langue(self, code: str) -> None:
        _choisir(self.cb_langue, code)     # la liste de la barre d'outils suit

    def _journal(self) -> None:
        """Ouvre la fenêtre du journal, ou la ramène au premier plan.

        Une seule instance, gardée d'un appel à l'autre : le filtre saisi et
        la position de lecture survivent à la fermeture, ce qui compte quand
        on cherche un incident en plusieurs fois.
        """
        from .log_window import LogWindow
        if getattr(self, "_fen_journal", None) is None:
            self._fen_journal = LogWindow(self.p, self.settings, self)
        self._fen_journal.show()
        self._fen_journal.raise_()
        self._fen_journal.activateWindow()

    def _ouvrir_site(self) -> None:
        import webbrowser
        from ..version import WEBSITE
        webbrowser.open(WEBSITE)

    def _charger_enregistrement(self) -> None:
        """Passe la main à la bibliothèque, qui sait charger et rejouer."""
        self.tabs.setCurrentWidget(self.tab_library)
        charger = getattr(self.tab_library, "_charger_fichier", None)
        if callable(charger):
            charger()

    # ------------------------------------------------- réglages à chaud
    def _profil_change(self) -> None:
        """Applique un profil complet sans interrompre l'acquisition."""
        cle = self.cb_profil.currentData()
        if not cle:
            return
        from ..music.profiles import get as get_profil
        profil = get_profil(cle)
        if profil is None:
            return
        changements = profil.appliquer(self.settings)
        for combo, valeur in ((self.cb_instrument, self.settings.music.instrument),
                              (self.cb_gamme, self.settings.music.scale),
                              (self.cb_diapason, float(self.settings.music.diapason_hz))):
            combo.blockSignals(True)
            _choisir(combo, valeur)
            combo.blockSignals(False)
        self.engine.apply_settings()
        self._rafraichir_onglets_musique()
        self.statusBar().showMessage(
            f"Profil « {profil.label} » appliqué — " + " · ".join(changements), 8000)

    def _musique_change(self) -> None:
        """Timbre, gamme ou diapason : pris en compte immédiatement."""
        m = self.settings.music
        m.instrument = self.cb_instrument.currentData() or m.instrument
        m.scale = self.cb_gamme.currentData() or m.scale
        diapason = self.cb_diapason.currentData()
        if diapason:
            m.diapason_hz = float(diapason)
        m.profile = ""
        self.cb_profil.blockSignals(True)
        self.cb_profil.setCurrentIndex(0)
        self.cb_profil.blockSignals(False)
        self.engine.apply_settings()
        self._rafraichir_onglets_musique()

    def _rafraichir_onglets_musique(self) -> None:
        for onglet in (self.tab_listen, self.tab_voice):
            recharger = getattr(onglet, "recharger", None)
            if callable(recharger):
                try:
                    recharger()
                except Exception:                      # noqa: BLE001
                    _log.exception("Rafraîchissement d'un onglet de jeu")

    def _capturer_echantillon(self) -> None:
        """Ctrl+E : garder ce qui vient de passer, sans rien engager."""
        chemin = self.engine.capturer_echantillon()
        if chemin:
            self.statusBar().showMessage(
                t("Sample kept: {fichier}").format(
                    fichier=os.path.basename(chemin)), 8000)
            recharger = getattr(self.tab_library, "recharger_echantillons", None)
            if callable(recharger):
                recharger()

    def _reinitialiser_zoom(self) -> None:
        """Ctrl+0 : tous les tracés de l'onglet courant reviennent à l'origine."""
        traces = self._traces_de_l_onglet()
        deplaces = [p for p in traces if p.est_zoome()]
        for trace in traces:
            trace.reinitialiser_zoom()
        self.statusBar().showMessage(
            t("Zoom reset ({n} plot(s))").format(
                n=len(deplaces) or len(traces)), 4000)
        self._maj_bouton_zoom()

    def _traces_de_l_onglet(self) -> list:
        from .widgets import TracePlot
        onglet = self.tabs.currentWidget()
        return onglet.findChildren(TracePlot) if onglet is not None else []

    def _maj_bouton_zoom(self) -> None:
        """Active l'action de la barre d'outils si un tracé est déplacé."""
        zoome = any(p.est_zoome() for p in self._traces_de_l_onglet())
        if zoome != self.act_zoom.isEnabled():
            self.act_zoom.setEnabled(zoome)

    def _langue_change(self) -> None:
        """Le sélecteur de la barre d'outils. Le redémarrage est proposé."""
        code = self.cb_langue.currentData()
        if not code or code == self.settings.ui.language:
            return
        self.settings.ui.language = code
        try:
            self.settings.save()
        except OSError:                                # pragma: no cover
            pass
        reglages = getattr(self, "tab_settings", None)
        proposer = getattr(reglages, "_proposer_redemarrage", None)
        if callable(proposer):
            proposer()

    def _volume_change(self, valeur: int) -> None:
        """Le volume agit immédiatement, même pendant un enregistrement."""
        self.settings.music.master_gain_db = float(valeur)
        self.lab_volume.setText(f"{valeur:+d} dB")
        if not self.act_mute.isChecked():
            self.engine.synth.master = 10 ** (valeur / 20.0)

    def _muet(self, coche: bool) -> None:
        """Coupe le son sans rien interrompre : la mesure continue."""
        if coche:
            self.engine.synth.master = 0.0
            self.act_mute.setText(t("🔈 Unmute"))
            self.statusBar().showMessage(
                t("Sound muted — measurement and recording continue."), 5000)
        else:
            self.engine.synth.master = 10 ** (self.sl_volume.value() / 20.0)
            self.act_mute.setText(t("🔇 Mute"))

    def _quitter(self) -> None:
        """Fermeture propre : l'enregistrement en cours est clos d'abord."""
        if self.engine.state.recording:
            reponse = QMessageBox.question(
                self, t("Quit"),
                t("A recording is in progress.\n\nDo you want to close it and quit?"),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reponse != QMessageBox.Yes:
                return
        self.close()

    def _etape(self, texte: str) -> None:
        """Répercute l'avancement sur l'écran d'accueil, s'il est encore là."""
        if self._splash is not None:
            try:
                self._splash.etape(texte)
            except Exception:                          # pragma: no cover
                pass

    # ------------------------------------------------- attente de la carte
    def _surveiller_carte(self) -> None:
        """Après le démarrage, guette l'arrivée d'une carte sur le bus USB.

        Le logiciel ne reste jamais bloqué : il travaille sur la source
        disponible (générateur interne au besoin) et bascule automatiquement
        sur la carte dès qu'elle apparaît. Le bandeau prévient l'utilisateur
        sans lui imposer de fenêtre modale.
        """
        st = self.engine.state
        if st.source_kind in ("audio", "serie") and st.board is not None:
            self.banniere.setVisible(False)
            return
        self.banniere.setText(
            t("  Waiting for a PhytoSense board on the USB-C port — meanwhile listening works on: {source}").format(
                  source=st.source_name or "—"))
        self.banniere.setVisible(True)
        self.engine.monitor.on_change = self._carte_detectee
        self.engine.monitor.start()

    def _maj_bandeau_relecture(self, st) -> None:
        """Pendant une relecture, le bandeau dit ce qui se passe réellement.

        L'acquisition est **suspendue** : aucune donnée n'entre plus par la
        carte ni par l'entrée audio. Le taire serait le meilleur moyen de faire
        prendre un enregistrement pour une plante.
        """
        if not st.replaying:
            if getattr(self, "_bandeau_relecture", False):
                self._bandeau_relecture = False
                self.banniere.setVisible(False)
                self._surveiller_carte()
            return
        self._bandeau_relecture = True
        reste = max(st.replay_length - st.replay_position, 0.0)
        self.banniere.setText(t(
            "⏵ Replaying “{nom}” — live acquisition is suspended. {position:.0f} s of {duree:.0f} s, {reste:.0f} s to go. “Back to live” hands control back to the plant.").format(
                nom=st.replay_name or "—", position=st.replay_position,
                duree=st.replay_length, reste=reste))
        self.banniere.setVisible(True)

    def _carte_detectee(self, present: bool) -> None:
        """Rappelé par le fil de surveillance : jamais d'accès Qt direct ici."""
        if present:
            self.carte_arrivee.emit()

    def _basculer_sur_carte(self) -> None:
        self.banniere.setText(t("  Board detected — switching source…"))
        self.statusBar().showMessage(t("PhytoSense board detected: switching."), 6000)
        enregistrait = self.engine.state.recording
        try:
            self.engine.stop()
            self.engine.start()
            if enregistrait:
                self.engine.start_recording()
        except Exception:                              # noqa: BLE001
            _log.exception("Bascule sur la carte impossible")
        self._surveiller_carte()

    # ---------------------------------------------------------------- thème
    def apply_theme(self) -> None:
        self.p = theme.palette(self.settings.ui.theme)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(theme.stylesheet(self.settings.ui.theme,
                                               self.settings.ui.accessible_font_scale))

    # -------------------------------------------------------------- actions
    def _toggle_record(self, checked: bool) -> None:
        if checked:
            path = self.engine.start_recording(self.settings.metadata.get("plante", ""))
            if path is None:
                self.act_record.setChecked(False)
                return
            self.act_record.setText(t("■ Stop"))
        else:
            self.engine.stop_recording()
            self.act_record.setText(t("● Record"))
            self.tab_library.reload()

    def _mark(self) -> None:
        text, ok = QInputDialog.getText(self, "Marqueur",
                                        "Étiquette à insérer dans la séance :")
        if ok and text.strip():
            self.engine.mark(text.strip())

    def _restart(self) -> None:
        was_recording = self.engine.state.recording
        self.engine.stop()
        self.engine.start()
        if was_recording:
            self.engine.start_recording()

    def _goto_auto(self) -> None:
        self.tabs.setCurrentWidget(self.tab_settings)

    def _panic(self) -> None:
        self.engine.synth.all_off()
        if self.engine.midi.is_open:
            self.engine.midi.panic()
        self.statusBar().showMessage(t("All notes cut."), 3000)

    def _test_hp(self) -> None:
        """Bip d'essai — la façon la plus rapide de savoir si le son sort."""
        self.engine.test_haut_parleur()
        self.statusBar().showMessage(
            t("1 kHz test beep emitted. If you hear nothing: Diagnostics tab → Audio output."), 6000)

    def _aide(self) -> None:
        """Fenêtre d'aide — un seul bouton, OK."""
        from .help_dialog import HelpDialog
        HelpDialog(self.p, self).exec()

    def _about(self) -> None:
        """Fenêtre « À propos » — version, auteur, composants, licence."""
        from .about import AboutDialog
        AboutDialog(self.p, self).exec()

    def _settings_changed(self) -> None:
        """Rappel commun à tous les onglets après modification d'un réglage."""
        self.apply_theme()
        try:
            self.engine.apply_settings()
        except Exception:                              # noqa: BLE001
            _log.exception("Application des réglages impossible")
        timer = getattr(self, "timer", None)
        if timer is not None:
            timer.setInterval(
                max(int(1000 / max(self.settings.ui.refresh_hz, 1)), 16))

    # ------------------------------------------------------------ callbacks
    def _on_note_threadsafe(self, note) -> None:
        self.note_played.emit(note)

    def _on_enonce_threadsafe(self, enonce) -> None:
        #  Appelé depuis le fil de traitement : on passe par un signal, seule
        #  façon correcte de toucher à l'interface depuis un autre fil.
        self.enonce_dit.emit(enonce)

    def _on_message_threadsafe(self, text: str) -> None:
        self.message_arrived.emit(text)

    def _on_note(self, note) -> None:
        self.tab_listen.add_note(note)
        #  Les modules sont prévenus DEPUIS LE FIL DE L'INTERFACE, jamais
        #  depuis celui des données : un module lent ralentit l'affichage, il
        #  ne fait pas tomber un échantillon (`C-20`, `C-28`).
        from ..api import NOTE_PLAYED
        self.engine.publish(NOTE_PLAYED, int(getattr(note, "midi", 0)),
                            int(getattr(note, "velocity", 0)))

    def _on_enonce(self, enonce) -> None:
        self.tab_voice.ajouter_enonce(enonce)
        self.statusBar().showMessage(f"« {enonce.texte} »", 6000)
        from ..api import UTTERANCE_PRODUCED
        self.engine.publish(UTTERANCE_PRODUCED, str(enonce.texte))

    def _on_message(self, text: str) -> None:
        self.statusBar().showMessage(text, 8000)

    # -------------------------------------------------------------- modules
    def _publier_aux_modules(self, st) -> None:
        """Annonce aux modules ce qui a changé depuis le dernier passage.

        On compare des compteurs plutôt que de brancher des rappels dans le
        moteur : c'est ce qui garantit que les modules sont prévenus **depuis
        le fil de l'interface**, à la cadence de rafraîchissement, et jamais
        depuis le fil d'acquisition.

        Le prix à payer est une latence d'un rafraîchissement — quelques
        dizaines de millisecondes. C'est sans conséquence pour un module, et
        cela vaut mieux que de laisser un module inconnu s'exécuter sur le
        chemin des données.
        """
        from ..api import (DISK_ALERT, EVENT_DETECTED, MEASUREMENT_STOPPED,
                           MEASUREMENT_STARTED, SESSION_STARTED, SESSION_ENDED,
                           SOURCE_CHANGED)
        precedent = self._dernier_etat_modules

        if st.running != precedent.get("running"):
            self.engine.publish(
                MEASUREMENT_STARTED if st.running else MEASUREMENT_STOPPED,
                self.engine.modules.modules and
                next(iter(self.engine.modules.modules.values())).context.state()
                if self.engine.modules.modules else None)
        if st.source_name != precedent.get("source"):
            self.engine.publish(SOURCE_CHANGED, str(st.source_name))

        #  Les événements : on en publie autant qu'il en est apparu, avec leur
        #  instant et leur amplitude réels quand on les a.
        nouveaux = int(st.events_total) - int(precedent.get("events", 0))
        if 0 < nouveaux <= 32:
            ev = st.last_event
            for _ in range(nouveaux):
                self.engine.publish(
                    EVENT_DETECTED,
                    float(getattr(ev, "time_s", st.elapsed_s)),
                    float(getattr(ev, "amplitude_v", 0.0)))

        if st.recording != precedent.get("recording"):
            self.engine.publish(
                SESSION_STARTED if st.recording else SESSION_ENDED,
                str(st.record_dir or ""))

        if st.disk_alert and not precedent.get("disk_alert"):
            self.engine.publish(DISK_ALERT, float(st.disk_free_mb))

        self._dernier_etat_modules = {
            "running": st.running, "source": st.source_name,
            "events": int(st.events_total), "recording": st.recording,
            "disk_alert": st.disk_alert,
        }

    # ----------------------------------------------------------- rafraîchi
    def _refresh(self) -> None:
        st = self.engine.state
        self._publier_aux_modules(st)
        current = self.tabs.currentWidget()
        if hasattr(current, "refresh"):
            current.refresh(st)

        self._maj_bouton_zoom()
        self._maj_bandeau_relecture(st)
        if st.replaying:
            self.strip.set("state", t("replay"), "warn")
        else:
            self.strip.set("state", t("acquiring") if st.running else t("stopped"),
                           "ok" if st.running else "err")
        self.strip.set("source", st.source_name[:26] or "—")
        self.strip.set("duration", _hms(st.elapsed_s))
        board = st.board
        self.strip.set("clock", t("ADC ±1 ppm") if board else t("host"),
                       "ok" if board else "warn")
        self.strip.set("saturation", t("YES") if st.saturated else t("no"),
                       "err" if st.saturated else "ok")
        self.strip.set("drift", f"{st.drift_v_per_min * 1e6:+.0f} µV/min",
                       "warn" if abs(st.drift_v_per_min) > 3e-4 else "normal")
        self.strip.set("events", t("{n} / {m} notes").format(
            n=st.events_total, m=st.notes_total))
        self.strip.set("output", f"{st.audio_peak_db:+.0f} dB",
                       "err" if st.audio_peak_db > -1.0 else "normal")
        if st.recording:
            #  Pendant l'enregistrement, l'espace restant compte autant que la
            #  durée écoulée : c'est lui qui décidera de la fin.
            from ..core.disk_space import formater_mo
            texte = "● " + _hms(st.record_elapsed)
            if st.disk_free_mb > 0:
                texte += " · " + formater_mo(st.disk_free_mb)
            self.strip.set("recording", texte,
                           "warn" if st.disk_alert else "err")
        else:
            self.strip.set("recording", t("stopped"))

    # --------------------------------------------------------------- sortie
    def arret_immediat(self) -> None:
        """Arrêt sans question — Ctrl+C dans le terminal, ou signal du système.

        Aucune fenêtre de confirmation n'est ouverte : une interruption n'est pas
        une invitation à débattre. L'enregistrement en cours est clos comme il
        l'aurait été par le menu, et les réglages sont sauvés.
        """
        if self._arrete:
            return
        self._arrete = True
        try:
            self.timer.stop()
        except Exception:                              # pragma: no cover
            pass
        try:
            self.engine.stop()
        except Exception:                              # pragma: no cover
            _log.exception("Arrêt du moteur imparfait")
        try:
            self.settings.save()
        except Exception:                              # pragma: no cover
            _log.exception("Réglages non sauvés")

    def closeEvent(self, event) -> None:
        try:
            self.arret_immediat()
        finally:
            super().closeEvent(event)


def _hms(seconds: float) -> str:
    s = int(max(seconds, 0))
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def _choisir(combo: QComboBox, valeur) -> None:
    """Sélectionne l'entrée dont la donnée vaut `valeur`, si elle existe."""
    for i in range(combo.count()):
        if combo.itemData(i) == valeur:
            combo.setCurrentIndex(i)
            return
