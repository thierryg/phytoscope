# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/startup_dialog.py
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

"""Fenêtre de démarrage — ce qui manque, et comment l'obtenir, sans terminal.

Beaucoup d'utilisateurs ne lisent jamais la console. Cette fenêtre montre le
même rapport que `--check`, distingue les trois causes d'échec (paquet
absent, paquet présent mais inutilisable, environnement verrouillé) et
propose l'installation d'un clic, avec la sortie de pip affichée en direct.

Elle ne s'ouvre que lorsqu'il y a quelque chose à dire : une installation
complète démarre directement sur la fenêtre principale.
"""
from __future__ import annotations

import sys
from typing import List, Optional

from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHBoxLayout,
                               QLabel, QPlainTextEdit, QProgressBar,
                               QPushButton, QVBoxLayout)

from ..core import preflight
from ..core.logging_setup import get_logger
from . import theme
from ..i18n import t
from . import fonts

log = get_logger(__name__)


class _Installateur(QThread):
    """Installe les paquets dans un fil séparé, sans figer la fenêtre."""

    ligne = Signal(str)
    termine = Signal(bool)

    def __init__(self, paquets: List[str], env, parent=None):
        super().__init__(parent)
        self.paquets = paquets
        self.env = env

    def run(self) -> None:                             # pragma: no cover
        ok = preflight.installer(self.paquets, env=self.env,
                                 sortie=self.ligne.emit)
        self.termine.emit(ok)


class StartupDialog(QDialog):
    """Rapport de démarrage, avec installation assistée."""

    def __init__(self, rapport: preflight.PreflightReport, settings, parent=None):
        super().__init__(parent)
        self.rapport = rapport
        self.settings = settings
        self.p = theme.palette(settings.ui.theme)
        self._installateur: Optional[_Installateur] = None

        self.setWindowTitle(t("PhytoScope — pre-flight checks"))
        self.setMinimumSize(760, 560)
        try:
            from .icon import app_icon
            self.setWindowIcon(app_icon())
        except Exception:                              # pragma: no cover
            pass
        self.setStyleSheet(theme.stylesheet(settings.ui.theme,
                                            settings.ui.accessible_font_scale))

        lay = QVBoxLayout(self)

        titre = QLabel(t("Pre-flight checks"))
        titre.setObjectName("titre")
        lay.addWidget(titre)

        self.etat = QLabel(self._phrase_etat())
        self.etat.setWordWrap(True)
        lay.addWidget(self.etat)

        self.tableau = QLabel(rapport.to_html())
        self.tableau.setTextFormat(Qt.RichText)
        self.tableau.setWordWrap(True)
        lay.addWidget(self.tableau)

        conseils = rapport.conseils()
        if conseils:
            self.conseils = QLabel("<b>À faire :</b><br>" +
                                   "<br>".join("• " + c for c in conseils))
            self.conseils.setTextFormat(Qt.RichText)
            self.conseils.setWordWrap(True)
            self.conseils.setStyleSheet(f"color:{self.p['gold']};")
            lay.addWidget(self.conseils)

        self.journal = QPlainTextEdit()
        self.journal.setReadOnly(True)
        self.journal.setFont(fonts.mono(8))
        self.journal.setVisible(False)
        self.journal.setMaximumHeight(200)
        lay.addWidget(self.journal, 1)

        self.progression = QProgressBar()
        self.progression.setRange(0, 0)
        self.progression.setVisible(False)
        lay.addWidget(self.progression)

        self.chk_ne_plus_afficher = QCheckBox(
            t("Do not show this window again while nothing changes"))
        lay.addWidget(self.chk_ne_plus_afficher)

        boutons = QHBoxLayout()
        paquets = rapport.paquets_a_installer(tous=True)
        self.btn_installer = QPushButton(
            t("Install the missing packages ({n})").format(
                n=len(paquets)))
        self.btn_installer.setEnabled(bool(paquets) and
                                      bool(preflight.strategies(rapport.env)))
        self.btn_installer.clicked.connect(self._installer)
        self.btn_copier = QPushButton(t("Copy the system command"))
        self.btn_copier.setEnabled(bool(rapport.commande_systeme()))
        self.btn_copier.clicked.connect(self._copier)
        self.btn_continuer = QPushButton(t("Continue"))
        self.btn_continuer.setDefault(True)
        self.btn_continuer.clicked.connect(self.accept)
        self.btn_quitter = QPushButton(t("Quit"))
        self.btn_quitter.clicked.connect(self.reject)

        boutons.addWidget(self.btn_installer)
        boutons.addWidget(self.btn_copier)
        boutons.addStretch(1)
        boutons.addWidget(self.btn_quitter)
        boutons.addWidget(self.btn_continuer)
        lay.addLayout(boutons)

        self.btn_continuer.setEnabled(rapport.peut_demarrer)

    # -- contenu -------------------------------------------------------------
    def _phrase_etat(self) -> str:
        r = self.rapport
        if r.peut_demarrer and not r.casses and not r.absents:
            return "Tout est en place."
        if r.peut_demarrer:
            return ("Le logiciel peut démarrer, mais certaines fonctions seront "
                    "indisponibles. Vous pouvez continuer et corriger plus tard.")
        if r.casses:
            return ("Des bibliothèques du système manquent. Les paquets Python "
                    "sont bien installés : les réinstaller ne changerait rien. "
                    "Il faut installer les paquets du système d'exploitation, "
                    "ce qui demande les droits d'administration.")
        return "Des paquets Python nécessaires ne sont pas installés."

    # -- actions -------------------------------------------------------------
    def _copier(self) -> None:
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(self.rapport.commande_systeme())
        self.btn_copier.setText(t("Command copied ✓"))

    def _installer(self) -> None:
        paquets = self.rapport.paquets_a_installer(tous=True)
        if not paquets:
            return
        self.btn_installer.setEnabled(False)
        self.journal.setVisible(True)
        self.progression.setVisible(True)
        self.journal.appendPlainText(f"Installation de : {' '.join(paquets)}\n")
        self._installateur = _Installateur(paquets, self.rapport.env, self)
        self._installateur.ligne.connect(self.journal.appendPlainText)
        self._installateur.termine.connect(self._fin_installation)
        self._installateur.start()

    def _fin_installation(self, ok: bool) -> None:
        self.progression.setVisible(False)
        self.journal.appendPlainText(
            "\n✓ Installation terminée." if ok else
            "\n✗ L'installation a échoué. Essayez : make install")
        nouveau = preflight.run(self.settings)
        self.rapport = nouveau
        self.tableau.setText(nouveau.to_html())
        self.etat.setText(self._phrase_etat())
        self.btn_continuer.setEnabled(nouveau.peut_demarrer)
        self.btn_installer.setEnabled(bool(nouveau.paquets_a_installer(tous=True)))
        if ok and nouveau.peut_demarrer:
            self.etat.setText(t("Everything is in place. Some libraries will only be taken into account at the next start."))

    # -- utilisation ---------------------------------------------------------
    def exec_si_necessaire(self) -> bool:
        """Affiche la fenêtre si besoin ; renvoie True s'il faut continuer."""
        r = self.rapport
        if r.peut_demarrer and not r.casses and not r.absents:
            return True
        if r.peut_demarrer and self.settings.ui.__dict__.get("skip_startup_check"):
            return True
        resultat = self.exec()
        if self.chk_ne_plus_afficher.isChecked():
            try:
                self.settings.ui.__dict__["skip_startup_check"] = True
                self.settings.save()
            except Exception:                          # pragma: no cover
                log.warning("Préférence de démarrage non enregistrée")
        return resultat == QDialog.Accepted
