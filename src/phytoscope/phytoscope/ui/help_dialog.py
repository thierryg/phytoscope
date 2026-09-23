# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/help_dialog.py
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

"""Fenêtre d'aide — ce qu'il faut savoir sans lire le document.

Quatre onglets : la prise en main en cinq gestes, les raccourcis, ce que
contient chaque onglet du logiciel, et où trouver le reste. Un seul bouton,
« OK », parce qu'une fenêtre d'information ne demande aucune décision.

La page des raccourcis est **complétée par le programme lui-même** : la liste
écrite ci-dessous est confrontée aux actions réellement installées dans la
fenêtre principale, et tout raccourci qui existerait sans être documenté est
ajouté d'office, signalé comme non décrit. Une liste de raccourcis fausse est
pire qu'une liste absente — celle-ci ne peut pas mentir longtemps.
"""
from __future__ import annotations

import sys

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QFont, QKeySequence
from PySide6.QtWidgets import (QDialogButtonBox, QDialog, QHBoxLayout, QLabel,
                               QPushButton, QScrollArea, QTabWidget,
                               QVBoxLayout, QWidget)

from .. import version as V
from . import theme
from ..i18n import t
from . import fonts

#  Les raccourcis, par groupe : ce qu'on fait pendant une séance d'abord,
#  le reste ensuite. La colonne de droite dit la fonction, pas le nom du
#  bouton — c'est la fonction qu'on cherche quand on ouvre cette page.
RACCOURCIS = [
    ("During the session", [
        ("Ctrl+R", "start or stop recording"),
        ("Ctrl+M", "drop a time-stamped marker in the session"),
        ("Ctrl+E", "keep on disk the signal that has just gone by — a sample, without starting or stopping anything"),
        ("Ctrl+K", "mute without interrupting the measurement or the recording"),
        ("Ctrl+Shift+." if sys.platform == "darwin" else "Ctrl+.",
         "silence: immediately cuts every note currently sounding"),
        ("Ctrl+A", "open the auto-setup wizard"),
    ]),
    ("The window", [
        ("F1", "this help window"),
        ("Maj+F1", "the “About” window: version, components, environment report"),
        ("Ctrl+L", "open the application log: the file live, where it is, and the means to save a copy of it"),
        ("Ctrl+0", "bring every plot in the tab back to its original framing — after a zoom with the wheel"),
        ("Ctrl+Tab", "go to the next tab"),
        ("Ctrl+Maj+Tab", "go to the previous tab"),
        ("Tab / Maj+Tab", "move to the next control, or to the previous one"),
        ("Espace", "tick or untick the box, press the button that has the focus"),
        ("Échap", "close the current dialog without applying anything"),
        ("Ctrl+Q", "quit, closing the current session cleanly"),
    ]),
    ("Plotter tab — command line", [
        ("Entrée", "run the typed command"),
        ("↑", "recall the previous command from the history"),
        ("↓", "go back to the next command in the history"),
    ]),
    ("Text fields, lists and tables", [
        ("Ctrl+C / Ctrl+V", "copy, paste — in any text field"),
        ("Ctrl+A", "select all, when the focus is in a text field (elsewhere: auto-setup)"),
        ("↑ ↓ ← →", "move through a list, a table or a numeric value"),
        ("Page préc. / Page suiv.", "scroll a list or a table by one screen"),
    ]),
    ("From the terminal", [
        ("Ctrl+C", "interrupt the software: the current session is closed, the settings saved, then the program stops. A second Ctrl+C ends it without waiting."),
        #  L'entrée reste présente sur les trois systèmes, et dit elle-même
        #  où elle s'applique : la retirer sous Windows ferait varier
        #  l'inventaire des libellés d'un système à l'autre, et un même
        #  catalogue de traduction ne pourrait plus les servir tous.
        ("Ctrl+Z", "suspend the process — on Unix and macOS only, Windows having no suspend signal. Acquisition stops too: « fg » resumes it, but the missing signal is lost."),
    ]),
]

#  Raccourcis dont le programme ne peut pas témoigner — fournis par Qt ou par
#  le système — et qu'il ne faut donc pas chercher parmi les actions.
FOURNIS_PAR_QT = {"Ctrl+Tab", "Ctrl+Maj+Tab", "Tab / Maj+Tab", "Espace",
                  "Échap", "Entrée", "↑", "↓", "↑ ↓ ← →", "Ctrl+C / Ctrl+V",
                  "Page préc. / Page suiv.", "Ctrl+C", "Ctrl+Z"}

ONGLETS = [
    ("Oscilloscope", "The signal over time, from 5 s to 1 h. The session tab: this is the one you watch."),
    ("Multimeter", "The numbers — voltage, noise, drift, contact quality. To be consulted before starting an hour of recording."),
    ("Analyser", "The spectrum, with automatic mains detection. A peak at 50 Hz points to a shielding problem, not to a plant signal."),
    ("Descriptors", "Six representations of the same signal: waveform, FFT, wavelets, MFCC, linear prediction, cepstrum. Each one states what it shows and what it does not allow you to conclude."),
    ("Plotter", "A built-in gnuplot: nine sources, logarithmic scales, export to PNG, SVG, data and script."),
    ("Listening", "Timbre, scale, root, tuning — and the log of notes with the rule that produced each one."),
    ("Speech", "Speech mode: a dictionary of words instead of a scale. It is not a translation, and the tab says so permanently — every utterance comes with the values that triggered it."),
    ("Library", "The recorded sessions, with replay accelerated up to six hundred times."),
    ("Diagnostics", "USB link, sampling, audio output, log. The first place to go when something is wrong."),
    ("Settings", "Seven pages, from the automatic wizard to the Expert page where nothing is hidden."),
]

DEMARRAGE = [
    ("1", "Connect the electrodes", "A clip on a moistened leaf, a probe in the substrate. The contact takes ten to thirty minutes to settle: this is normal, and it is measurable."),
    ("2", "Check the contact", "Multimeter tab: contact quality must read “fair” or “excellent”. If it does not, moisten."),
    ("3", "Run the auto-setup", "Ctrl+A. The wizard listens for twelve seconds, measures, proposes — and explains every one of its choices."),
    ("4", "Listen", "Listening tab: choose a preset. “Discovery” makes every event audible; “Meditation” spaces the notes out."),
    ("5", "Record", "Ctrl+R. A session is a folder: WAV, CSV and JSON, all readable without this software."),
]


class HelpDialog(QDialog):
    """Aide générale. Un seul bouton : OK."""

    def __init__(self, palette: dict, parent=None):
        super().__init__(parent)
        self.p = palette
        self.setWindowTitle(t("Help — {app}").format(app=V.APP_NAME))
        self.setMinimumSize(700, 560)
        try:
            from .icon import app_icon
            self.setWindowIcon(app_icon())
        except Exception:                              # pragma: no cover
            pass

        tabs = QTabWidget()
        tabs.addTab(self._page_demarrage(), t("Getting started"))
        tabs.addTab(self._page_raccourcis(), t("Shortcuts"))
        tabs.addTab(self._page_onglets(), t("The tabs"))
        tabs.addTab(self._page_ailleurs(), t("Going further"))

        boutons = QDialogButtonBox(QDialogButtonBox.Ok)
        boutons.accepted.connect(self.accept)
        ok = boutons.button(QDialogButtonBox.Ok)
        if ok is not None:
            ok.setText(t("OK"))
            ok.setDefault(True)
        self.btn_apropos = QPushButton(t("About…"))
        self.btn_apropos.clicked.connect(self._apropos)
        boutons.addButton(self.btn_apropos, QDialogButtonBox.ActionRole)

        lay = QVBoxLayout(self)
        lay.addWidget(tabs, 1)
        lay.addWidget(boutons)

    # -- pages ---------------------------------------------------------------
    def _enveloppe(self, widget: QWidget) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setWidget(widget)
        sa.setFrameShape(QScrollArea.NoFrame)
        return sa

    def _page_demarrage(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        intro = QLabel(t("Five steps, in this order. The software also works with no hardware at all: the “internal generator” source produces a statistically credible signal."))
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color:{self.p['text2']};")
        lay.addWidget(intro)
        for numero, titre, texte in DEMARRAGE:
            bloc = QLabel(f"<b style='color:{self.p['gold']}'>{numero}. {t(titre)}</b>"
                          f"<br>{t(texte)}")
            bloc.setTextFormat(Qt.RichText)
            bloc.setWordWrap(True)
            bloc.setStyleSheet("padding:6px 0;")
            lay.addWidget(bloc)
        lay.addStretch(1)
        return self._enveloppe(w)

    def _page_raccourcis(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        groupes = [(titre, list(lignes)) for titre, lignes in RACCOURCIS]
        oublies = self._raccourcis_non_documentes(groupes)
        if oublies:
            groupes.append(("Autres actions de la barre d'outils", oublies))

        for titre, lignes in groupes:
            entete = QLabel(t(titre))
            entete.setStyleSheet(
                f"color:{self.p['gold']};font-weight:bold;padding-top:10px;")
            lay.addWidget(entete)
            for touches, role in lignes:
                ligne = QHBoxLayout()
                #  Affiché tel que le système le présente : sur macOS, Qt
                #  traduit `Ctrl` en ⌘, et l'utilisateur chercherait en vain
                #  une touche « Ctrl » sur son clavier.
                touche = QLabel(_afficher(touches))
                touche.setFont(fonts.mono(10, gras=True))
                touche.setFixedWidth(150)
                touche.setAlignment(Qt.AlignRight | Qt.AlignTop)
                touche.setStyleSheet(f"color:{self.p['trace']};")
                r = QLabel(t(role))
                r.setWordWrap(True)
                ligne.addWidget(touche)
                ligne.addWidget(r, 1)
                lay.addLayout(ligne)

        note = QLabel(
            t("This list is checked when the window opens: any shortcut installed in the main window and missing from here is added automatically. The usual editing shortcuts (Tab, Esc, copy-paste) come from the graphical toolkit and apply to every application on the system."))
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{self.p['text2']};font-size:8pt;"
                           f"padding-top:12px;")
        lay.addWidget(note)
        lay.addStretch(1)
        return self._enveloppe(w)

    def _raccourcis_non_documentes(self, groupes) -> list:
        """Les raccourcis réellement installés que le tableau ci-dessus ignore.

        On interroge la fenêtre principale plutôt que de faire confiance à une
        liste écrite à la main : un raccourci ajouté au code sans être
        documenté apparaîtra ici, ce qui est la seule façon de s'en apercevoir.
        """
        fenetre = self.parent()
        if fenetre is None:
            return []
        connus = {_normaliser(touches) for _, lignes in groupes
                  for touches, _ in lignes}
        connus |= {_normaliser(x) for x in FOURNIS_PAR_QT}
        trouves = []
        try:
            actions = fenetre.findChildren(QAction)
        except Exception:                              # noqa: BLE001
            return []
        for action in actions:
            sequence = action.shortcut().toString()
            if not sequence or _normaliser(sequence) in connus:
                continue
            connus.add(_normaliser(sequence))
            libelle = (action.toolTip() or action.text() or "").strip()
            libelle = libelle.replace("&", "")
            trouves.append((sequence, libelle + "  (non décrit ci-dessus)"))
        return sorted(trouves)

    def _page_onglets(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        for nom, texte in ONGLETS:
            bloc = QLabel(f"<b style='color:{self.p['accent2']}'>{t(nom)}</b>"
                          f"<br>{t(texte)}")
            bloc.setTextFormat(Qt.RichText)
            bloc.setWordWrap(True)
            bloc.setStyleSheet("padding:4px 0;")
            lay.addWidget(bloc)
        lay.addStretch(1)
        return self._enveloppe(w)

    def _page_ailleurs(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        texte = QLabel(
            f"<p>Ce logiciel accompagne le document <i>La Carte PhytoSense — "
            f"conditionnement analogique et interface USB</i>, qui explique "
            f"l'électronique, les protocoles de mesure et ce qu'on a le droit "
            f"d'affirmer à partir de ces données.</p>"
            f"<p><b>Le fichier README.txt</b>, à côté du programme, contient "
            f"l'installation détaillée pour les trois systèmes et un chapitre "
            f"de dépannage.</p>"
            f"<p><b>En cas de problème :</b> onglet Diagnostic, puis "
            f"<i>Copier le rapport d'environnement</i> dans la fenêtre "
            f"À propos. C'est ce qu'il faut joindre à un signalement.</p>"
            f"<p><a href='{V.WEBSITE}' style='color:{self.p['accent2']}'>"
            f"{V.WEBSITE}</a><br>"
            f"<a href='mailto:{V.CONTACT}' style='color:{self.p['accent2']}'>"
            f"{V.CONTACT}</a></p>")
        texte.setTextFormat(Qt.RichText)
        texte.setWordWrap(True)
        texte.setOpenExternalLinks(True)
        lay.addWidget(texte)

        ligne = QHBoxLayout()
        b_site = QPushButton(t("Open the website"))
        b_site.clicked.connect(lambda: webbrowser.open(V.WEBSITE))
        ligne.addWidget(b_site)
        ligne.addStretch(1)
        lay.addLayout(ligne)
        lay.addStretch(1)
        return self._enveloppe(w)

    # -- actions -------------------------------------------------------------
    def _apropos(self) -> None:
        from .about import AboutDialog
        AboutDialog(self.p, self).exec()


def _afficher(touches: str) -> str:
    """Le raccourci écrit comme le système le présente à l'utilisateur.

    Sur macOS, Qt rend `Ctrl+R` sous la forme `⌘R`, `Shift` sous la forme `⇧`
    et `Alt` sous la forme `⌥`. Cette page listait jusqu'ici les combinaisons
    en dur, si bien qu'un utilisateur de Mac lisait « Ctrl+R » pour une
    combinaison qui est en réalité ⌘R.

    Les libellés qui ne sont pas des raccourcis Qt — « Tab / Maj+Tab »,
    « ↑ », « Entrée » — sont rendus tels quels : `QKeySequence` ne saurait
    qu'en faire, et ils sont déjà lisibles.
    """
    brut = touches.strip()
    if "/" in brut or " " in brut.replace("Maj+", "").replace("Ctrl+", ""):
        return brut
    rendu = _normaliser(brut)
    return rendu or brut


def _normaliser(touches: str) -> str:
    """Forme canonique d'un raccourci, pour comparer sans se tromper.

    « Maj+F1 » et « Shift+F1 » désignent la même chose : le premier est ce
    qu'on écrit en français, le second ce que Qt renvoie. Sans cette
    normalisation, la page signalerait comme non documenté un raccourci qui
    l'est parfaitement.
    """
    brut = touches.strip().replace("Maj+", "Shift+")
    try:
        rendu = QKeySequence(brut).toString()
    except Exception:                                  # noqa: BLE001
        return brut
    return rendu or brut
