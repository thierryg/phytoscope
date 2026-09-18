# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/help_dialog.py
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
from . import polices

#  Les raccourcis, par groupe : ce qu'on fait pendant une séance d'abord,
#  le reste ensuite. La colonne de droite dit la fonction, pas le nom du
#  bouton — c'est la fonction qu'on cherche quand on ouvre cette page.
RACCOURCIS = [
    ("Pendant la séance", [
        ("Ctrl+R", "démarrer ou arrêter l'enregistrement"),
        ("Ctrl+M", "poser un marqueur horodaté dans la séance"),
        ("Ctrl+E", "garder sur le disque le signal qui vient de passer — un "
                   "échantillon, sans rien démarrer ni arrêter"),
        ("Ctrl+K", "couper le son sans interrompre la mesure ni "
                   "l'enregistrement"),
        ("Ctrl+Shift+." if sys.platform == "darwin" else "Ctrl+.",
         "silence : coupe immédiatement toutes les notes en cours"),
        ("Ctrl+A", "ouvrir l'assistant d'auto-configuration"),
    ]),
    ("La fenêtre", [
        ("F1", "cette fenêtre d'aide"),
        ("Maj+F1", "fenêtre « À propos » : version, composants, rapport "
                   "d'environnement"),
        ("Ctrl+L", "ouvrir le journal du logiciel : le fichier en direct, "
                   "son emplacement, et de quoi en enregistrer une copie"),
        ("Ctrl+0", "ramener tous les tracés de l'onglet à leur cadrage "
                   "d'origine — après un zoom à la molette"),
        ("Ctrl+Tab", "passer à l'onglet suivant"),
        ("Ctrl+Maj+Tab", "passer à l'onglet précédent"),
        ("Tab / Maj+Tab", "passer d'une commande à la suivante, ou à la "
                          "précédente"),
        ("Espace", "cocher ou décocher la case, actionner le bouton qui a "
                   "le focus"),
        ("Échap", "fermer la fenêtre de dialogue en cours sans rien appliquer"),
        ("Ctrl+Q", "quitter en refermant proprement la séance en cours"),
    ]),
    ("Onglet Traceur — ligne de commande", [
        ("Entrée", "exécuter la commande saisie"),
        ("↑", "rappeler la commande précédente de l'historique"),
        ("↓", "revenir à la commande suivante de l'historique"),
    ]),
    ("Champs de saisie, listes et tableaux", [
        ("Ctrl+C / Ctrl+V", "copier, coller — dans tout champ de texte"),
        ("Ctrl+A", "tout sélectionner, lorsque le focus est dans un champ "
                   "de texte (ailleurs : auto-configuration)"),
        ("↑ ↓ ← →", "se déplacer dans une liste, un tableau ou une valeur "
                    "numérique"),
        ("Page préc. / Page suiv.", "faire défiler une liste ou un tableau "
                                    "d'un écran"),
    ]),
    ("Depuis le terminal", [
        ("Ctrl+C", "interrompre le logiciel : la séance en cours est close, "
                   "les réglages sauvés, puis le programme s'arrête. Un "
                   "second Ctrl+C termine sans attendre."),
        #  L'entrée reste présente sur les trois systèmes, et dit elle-même
        #  où elle s'applique : la retirer sous Windows ferait varier
        #  l'inventaire des libellés d'un système à l'autre, et un même
        #  catalogue de traduction ne pourrait plus les servir tous.
        ("Ctrl+Z", "suspendre le processus — sur Unix et macOS seulement, "
                   "Windows n'ayant pas de signal de suspension. "
                   "L'acquisition s'arrête aussi : « fg » la reprend, mais le "
                   "signal manquant est perdu."),
    ]),
]

#  Raccourcis dont le programme ne peut pas témoigner — fournis par Qt ou par
#  le système — et qu'il ne faut donc pas chercher parmi les actions.
FOURNIS_PAR_QT = {"Ctrl+Tab", "Ctrl+Maj+Tab", "Tab / Maj+Tab", "Espace",
                  "Échap", "Entrée", "↑", "↓", "↑ ↓ ← →", "Ctrl+C / Ctrl+V",
                  "Page préc. / Page suiv.", "Ctrl+C", "Ctrl+Z"}

ONGLETS = [
    ("Oscilloscope", "Le signal dans le temps, de 5 s à 1 h. L'onglet de la "
     "séance : c'est celui qu'on regarde."),
    ("Multimètre", "Les chiffres — tension, bruit, dérive, qualité du contact. "
     "À consulter avant de lancer une heure d'enregistrement."),
    ("Analyseur", "Le spectre, avec détection automatique du réseau. Un pic à "
     "50 Hz signale un problème de blindage, pas un signal végétal."),
    ("Descripteurs", "Six représentations du même signal : forme d'onde, FFT, "
     "ondelettes, MFCC, prédiction linéaire, cepstre. Chacune affiche ce "
     "qu'elle montre et ce qu'elle ne permet pas de conclure."),
    ("Traceur", "Un gnuplot intégré : neuf sources, échelles logarithmiques, "
     "exportation en PNG, SVG, données et script."),
    ("Écoute", "Timbre, gamme, tonique, diapason — et le journal des notes "
     "avec la règle qui a produit chacune."),
    ("Parole", "Le mode vocal : un dictionnaire de mots au lieu d'une gamme. "
     "Ce n'est pas une traduction, et l'onglet le rappelle en permanence — "
     "chaque énoncé est accompagné des valeurs qui l'ont déclenché."),
    ("Bibliothèque", "Les séances enregistrées, avec relecture accélérée "
     "jusqu'à six cents fois."),
    ("Diagnostic", "Lien USB, échantillonnage, sortie sonore, journal. "
     "Le premier endroit où aller quand quelque chose cloche."),
    ("Réglages", "Sept pages, de l'assistant automatique à la page Expert où "
     "rien n'est caché."),
]

DEMARRAGE = [
    ("1", "Brancher les électrodes", "Une pince sur une feuille humidifiée, "
     "une tige dans le substrat. Le contact met dix à trente minutes à se "
     "stabiliser : c'est normal, et c'est mesurable."),
    ("2", "Vérifier le contact", "Onglet Multimètre : la qualité du contact "
     "doit afficher « correct » ou « excellent ». Sinon, humidifier."),
    ("3", "Lancer l'auto-configuration", "Ctrl+A. L'assistant écoute douze "
     "secondes, mesure, propose — et explique chacun de ses choix."),
    ("4", "Écouter", "Onglet Écoute : choisir un profil. « Découverte » rend "
     "chaque événement audible ; « Méditation » espace les notes."),
    ("5", "Enregistrer", "Ctrl+R. Une séance est un répertoire : WAV, CSV et "
     "JSON, tous lisibles sans ce logiciel."),
]


class HelpDialog(QDialog):
    """Aide générale. Un seul bouton : OK."""

    def __init__(self, palette: dict, parent=None):
        super().__init__(parent)
        self.p = palette
        self.setWindowTitle(f"Aide — {V.APP_NAME}")
        self.setMinimumSize(700, 560)
        try:
            from .icon import app_icon
            self.setWindowIcon(app_icon())
        except Exception:                              # pragma: no cover
            pass

        tabs = QTabWidget()
        tabs.addTab(self._page_demarrage(), t("Prise en main"))
        tabs.addTab(self._page_raccourcis(), t("Raccourcis"))
        tabs.addTab(self._page_onglets(), t("Les onglets"))
        tabs.addTab(self._page_ailleurs(), t("Pour aller plus loin"))

        boutons = QDialogButtonBox(QDialogButtonBox.Ok)
        boutons.accepted.connect(self.accept)
        ok = boutons.button(QDialogButtonBox.Ok)
        if ok is not None:
            ok.setText(t("OK"))
            ok.setDefault(True)
        self.btn_apropos = QPushButton(t("À propos…"))
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
        intro = QLabel(t("Cinq gestes, dans cet ordre. Le logiciel fonctionne "
                       "aussi sans matériel : la source « Générateur interne » "
                       "produit un signal statistiquement crédible."))
        intro.setWordWrap(True)
        intro.setStyleSheet(f"color:{self.p['texte2']};")
        lay.addWidget(intro)
        for numero, titre, texte in DEMARRAGE:
            bloc = QLabel(f"<b style='color:{self.p['or']}'>{numero}. {t(titre)}</b>"
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
                f"color:{self.p['or']};font-weight:bold;padding-top:10px;")
            lay.addWidget(entete)
            for touches, role in lignes:
                ligne = QHBoxLayout()
                #  Affiché tel que le système le présente : sur macOS, Qt
                #  traduit `Ctrl` en ⌘, et l'utilisateur chercherait en vain
                #  une touche « Ctrl » sur son clavier.
                touche = QLabel(_afficher(touches))
                touche.setFont(polices.mono(10, gras=True))
                touche.setFixedWidth(150)
                touche.setAlignment(Qt.AlignRight | Qt.AlignTop)
                touche.setStyleSheet(f"color:{self.p['trace']};")
                r = QLabel(t(role))
                r.setWordWrap(True)
                ligne.addWidget(touche)
                ligne.addWidget(r, 1)
                lay.addLayout(ligne)

        note = QLabel(
            t("Cette liste est vérifiée à l'ouverture : tout raccourci installé "
            "dans la fenêtre principale et absent d'ici y est ajouté "
            "automatiquement. Les raccourcis d'édition courants (Tab, Échap, "
            "copier-coller) viennent de la boîte à outils graphique et valent "
            "pour toutes les applications du système."))
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{self.p['texte2']};font-size:8pt;"
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
        b_site = QPushButton(t("Ouvrir le site"))
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
