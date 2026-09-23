# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/about.py
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

"""Fenêtre « À propos » — identité, composants, licence et nouveautés.

Une fenêtre « À propos » sert à trois choses, et le logiciel les traite
toutes les trois : dire qui a écrit le programme et comment le joindre,
montrer exactement quelles briques sont installées (première question posée
à quiconque signale un bogue), et rappeler les termes de la licence.
"""
from __future__ import annotations

import os
import webbrowser
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication, QPainter, QPixmap
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFrame, QHBoxLayout,
                               QLabel, QPlainTextEdit, QPushButton, QTabWidget,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from .. import version as V
from ..i18n import t
from . import fonts


def _root() -> str:
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _read(name: str, limit: int = 40000) -> str:
    path = os.path.join(_root(), name)
    try:
        with open(path, encoding="utf-8") as f:
            return f.read(limit)
    except OSError:
        return f"(fichier {name} introuvable dans {_root()})"


class AboutDialog(QDialog):
    """Quatre onglets : identité, composants, nouveautés, licence."""

    def __init__(self, palette: dict, parent=None):
        super().__init__(parent)
        self.p = palette
        self.setWindowTitle(t("About {app}").format(app=V.APP_NAME))
        self.setMinimumSize(660, 520)

        tabs = QTabWidget()
        tabs.addTab(self._page_identity(), t("About"))
        tabs.addTab(self._page_components(), t("Components"))
        tabs.addTab(self._page_news(), t("What's new"))
        tabs.addTab(self._page_license(), t("License"))

        # Un bouton « OK » et rien d'autre : c'est ce qu'attend la main qui
        # cherche à refermer une fenêtre d'information.
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        bouton_ok = buttons.button(QDialogButtonBox.Ok)
        if bouton_ok is not None:
            bouton_ok.setText(t("OK"))
            bouton_ok.setDefault(True)
            bouton_ok.setAutoDefault(True)
        self.btn_copy = QPushButton(t("Copy the environment report"))
        self.btn_copy.setToolTip(t("Attach this to any bug report."))
        self.btn_copy.clicked.connect(self._copy_report)
        buttons.addButton(self.btn_copy, QDialogButtonBox.ActionRole)

        lay = QVBoxLayout(self)
        lay.addWidget(tabs, 1)
        lay.addWidget(buttons)

    # ------------------------------------------------------------- identité
    def _page_identity(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(24, 20, 24, 20)

        head = QHBoxLayout()
        logo = QLabel()
        from .icon import lotus_pixmap
        logo.setPixmap(lotus_pixmap(112))
        logo.setFixedSize(112, 112)
        head.addWidget(logo, 0, Qt.AlignTop)

        box = QVBoxLayout()
        title = QLabel(V.APP_NAME)
        f = QFont()
        f.setPointSize(24)
        f.setBold(True)
        title.setFont(f)
        title.setStyleSheet(f"color:{self.p['gold']};")
        sub = QLabel(V.APP_TAGLINE)
        sub.setStyleSheet(f"color:{self.p['text2']};font-style:italic;")
        ver = QLabel(f"Version <b>{V.VERSION}</b>"
                     + (f" « {V.RELEASE_NAME} »" if V.RELEASE_NAME else "")
                     + f" — {V.RELEASE_DATE}")
        ver.setTextFormat(Qt.RichText)
        box.addWidget(title)
        box.addWidget(sub)
        box.addSpacing(6)
        box.addWidget(ver)
        head.addLayout(box, 1)
        lay.addLayout(head)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet(f"color:{self.p['line']};")
        lay.addSpacing(10)
        lay.addWidget(line)
        lay.addSpacing(10)

        info = QLabel(
            f"<table cellspacing='6'>"
            #  Deux lignes, parce qu'elles ne disent pas la même chose :
            #  l'atelier qui publie, et la personne qui a écrit.
            f"<tr><td style='color:{self.p['text2']}'>{t('Publisher')}</td>"
            f"<td><b>{V.AUTHOR}</b></td></tr>"
            + (f"<tr><td style='color:{self.p['text2']}'>{t('Author')}</td>"
               f"<td><b>{V.AUTHOR_NAME}</b>"
               + (f" &nbsp;<a href='mailto:{V.AUTHOR_EMAIL}' "
                  f"style='color:{self.p['accent2']}'>{V.AUTHOR_EMAIL}</a>"
                  if V.AUTHOR_EMAIL else "")
               + (f"<br><span style='color:{self.p['text2']}'>"
                  f"{V.AUTHOR_PHONE}</span>" if V.AUTHOR_PHONE else "")
               + "</td></tr>" if V.AUTHOR_NAME else "") +
            f"<tr><td style='color:{self.p['text2']}'>{t('Website')}</td>"
            f"<td><a href='{V.WEBSITE}' style='color:{self.p['accent2']}'>"
            f"{V.WEBSITE}</a></td></tr>"
            f"<tr><td style='color:{self.p['text2']}'>{t('Contact')}</td>"
            f"<td><a href='mailto:{V.CONTACT}' style='color:{self.p['accent2']}'>"
            f"{V.CONTACT}</a></td></tr>"
            f"<tr><td style='color:{self.p['text2']}'>Licence</td>"
            f"<td>{V.LICENSE} — {V.COPYRIGHT}</td></tr>"
            f"<tr><td style='color:{self.p['text2']}'>Matériel</td>"
            f"<td>{V.HARDWARE}</td></tr>"
            f"<tr><td style='color:{self.p['text2']}'>Document</td>"
            f"<td><i>{V.COMPANION_DOC}</i></td></tr>"
            f"</table>")
        info.setTextFormat(Qt.RichText)
        info.setOpenExternalLinks(True)
        lay.addWidget(info)

        lay.addStretch(1)
        creed = QLabel(
            "<i>Ce logiciel ne traduit pas la plante : il la mesure, et propose "
            "une écoute de cette mesure. La différence entre les deux est tout "
            "le sujet du document qui l'accompagne.</i>")
        creed.setWordWrap(True)
        creed.setTextFormat(Qt.RichText)
        creed.setStyleSheet(f"color:{self.p['text2']};")
        lay.addWidget(creed)

        row = QHBoxLayout()
        b_site = QPushButton(t("Open the website"))
        b_site.clicked.connect(lambda: webbrowser.open(V.WEBSITE))
        b_mail = QPushButton(t("Email the author"))
        b_mail.clicked.connect(
            lambda: webbrowser.open(f"mailto:{V.CONTACT}"
                                    f"?subject={V.APP_NAME}%20{V.VERSION}"))
        row.addWidget(b_site)
        row.addWidget(b_mail)
        row.addStretch(1)
        lay.addLayout(row)
        return w

    # ----------------------------------------------------------- composants
    def _page_components(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        intro = QLabel(t("What is actually installed on this machine. Red lines prevent the software from starting; amber lines only limit it."))
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color:{self.p['text2']};")
        lay.addWidget(intro)

        rows = V.dependencies()
        table = QTableWidget(len(rows), 4)
        table.setHorizontalHeaderLabels([t("Component"), t("Version"), t("Role"), t("Status")])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        for i, (name, ver, role, required) in enumerate(rows):
            absent = (ver == "absent")
            statut = ("manquant" if absent and required else
                      "facultatif, absent" if absent else "présent")
            couleur = (self.p["alert"] if absent and required else
                       self.p["gold"] if absent else self.p["trace"])
            for j, text in enumerate((name, ver, role, statut)):
                item = QTableWidgetItem(text)
                if j == 3:
                    item.setForeground(Qt.GlobalColor.white)
                    item.setToolTip(couleur)
                table.setItem(i, j, item)
            table.item(i, 3).setText(statut)
        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(table, 1)

        self.report = QPlainTextEdit(V.environment_report())
        self.report.setReadOnly(True)
        self.report.setMaximumHeight(170)
        lay.addWidget(QLabel(t("Environment report")))
        lay.addWidget(self.report)
        return w

    # ------------------------------------------------------------ nouveautés
    def _page_news(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        text = QPlainTextEdit(_read("CHANGELOG.txt"))
        text.setReadOnly(True)
        text.setFont(fonts.mono(9))
        lay.addWidget(text)
        return w

    # --------------------------------------------------------------- licence
    def _page_license(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        text = QPlainTextEdit(_read(V.LICENSE_FILE))
        text.setReadOnly(True)
        text.setFont(fonts.mono(9))
        lay.addWidget(text)
        return w

    # ---------------------------------------------------------------- outils
    def _copy_report(self) -> None:
        cb = QGuiApplication.clipboard()
        if cb is not None:
            cb.setText(V.environment_report())
        self.btn_copy.setText(t("Report copied ✓"))
