# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/voice_tab.py
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

"""L'onglet « Parole » : le mode vocal, ses mots et sa justification.

Cet onglet est le jumeau de l'onglet « Écoute ». On y choisit un dictionnaire
au lieu d'une gamme, une grammaire au lieu d'un timbre, et l'on y lit ce qui a
été dit — avec, à chaque ligne, les valeurs mesurées qui l'ont déclenché.

L'avertissement figure en haut de l'onglet, en permanence et non dans une aide
qu'on ouvre une fois : **ce n'est pas une traduction.** Un dispositif qui fait
parler une plante avec des mots humains produit inévitablement l'illusion d'un
dialogue ; la seule parade honnête est de rappeler la règle sous les yeux de
celui qui écoute, et de lui donner les moyens de la vérifier.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QListWidget, QMessageBox, QPushButton,
                               QScrollArea, QSlider, QSpinBox, QTabWidget,
                               QVBoxLayout, QWidget)

from ..core.logging_setup import get_logger
from ..music.lexicon import (GRAMMAIRES, LEXIQUE_PAR_DEFAUT, Lexique,
                             lexiques_livres)
from ..music.voice import strategies_disponibles
from ..i18n import t
from . import fonts

log = get_logger(__name__)

AVERTISSEMENT = (
    "Ce n'est pas une traduction. La plante n'a pas de langage ; ces mots "
    "sont ceux du dictionnaire choisi, appliqués à des grandeurs mesurées "
    "selon des règles affichées ci-contre. Ce qui se dit ici est un dialogue "
    "entre vous et votre propre grille de lecture.")


class VoiceTab(QWidget):
    """Réglages du moteur lexical, de la voix, et journal des énoncés."""

    def __init__(self, engine, palette: dict, on_change=None, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.p = palette
        self.on_change = on_change
        v = engine.settings.voice

        racine = QVBoxLayout(self)

        bandeau = QLabel("⚠  " + t(AVERTISSEMENT))
        bandeau.setWordWrap(True)
        bandeau.setStyleSheet(
            f"background:{palette['fond3']};color:{palette['or']};"
            f"border:1px solid {palette['or']};border-radius:5px;padding:7px;")
        racine.addWidget(bandeau)

        lay = QHBoxLayout()
        racine.addLayout(lay, 1)
        gauche = QVBoxLayout()

        # --- le dictionnaire ------------------------------------------------
        boite = QGroupBox(t("Dictionnaire"))
        fd = QFormLayout(boite)
        self.chk_actif = QCheckBox(t("activer le mode vocal"))
        self.chk_actif.setChecked(v.enabled)
        self.chk_actif.setToolTip(
            t("La plante « parle » à la place de jouer : mêmes événements, "
              "mêmes seuils, des mots au lieu de notes."))
        self.chk_actif.stateChanged.connect(self._modifie)
        self.chk_musique = QCheckBox(t("couper la musique pendant la parole"))
        self.chk_musique.setChecked(v.mute_music)
        self.chk_musique.setToolTip(
            t("Une voix et un synthétiseur qui jouent ensemble se couvrent "
              "l'un l'autre. La détection, elle, continue comme avant."))
        self.chk_musique.stateChanged.connect(self._modifie)
        self.cb_dico = QComboBox()
        self.cb_dico.addItem(t("— suivre la langue de l'interface —"), "")
        for code, titre in lexiques_livres():
            self.cb_dico.addItem(titre, code)
        _choisir(self.cb_dico, v.lexicon_code)
        self.cb_dico.currentIndexChanged.connect(self._changer_dico)
        self.lab_lexique = QLabel("")
        self.lab_lexique.setWordWrap(True)
        self.lab_lexique.setStyleSheet(f"color:{palette['texte2']};")
        bl = QHBoxLayout()
        b_charger = QPushButton(t("Ouvrir…"))
        b_charger.clicked.connect(self._charger)
        b_modele = QPushButton(t("Écrire un modèle…"))
        b_modele.setToolTip(t("Enregistre le dictionnaire livré dans un fichier "
                            "JSON, à modifier avec un éditeur de texte."))
        b_modele.clicked.connect(self._ecrire_modele)
        b_defaut = QPushButton(t("Revenir au dictionnaire livré"))
        b_defaut.clicked.connect(self._defaut)
        bl.addWidget(b_charger)
        bl.addWidget(b_modele)
        fd.addRow(self.chk_actif)
        fd.addRow(self.chk_musique)
        fd.addRow(t("Dictionnaire"), self.cb_dico)
        fd.addRow(self.lab_lexique)
        fd.addRow(bl)
        fd.addRow(b_defaut)
        gauche.addWidget(boite)

        # --- la grammaire ---------------------------------------------------
        boite2 = QGroupBox(t("Grammaire"))
        fg = QFormLayout(boite2)
        self.cb_grammaire = QComboBox()
        for cle, g in GRAMMAIRES.items():
            self.cb_grammaire.addItem(t(str(g["titre"])), cle)
        _choisir(self.cb_grammaire, v.grammar)
        self.cb_grammaire.currentIndexChanged.connect(self._modifie)
        self.lab_grammaire = QLabel("")
        self.lab_grammaire.setWordWrap(True)
        self.lab_grammaire.setStyleSheet(f"color:{palette['texte2']};")
        self.cb_sujet = QComboBox()
        self.cb_sujet.setToolTip(t("Qui parle. C'est vous qui le décidez : "
                                 "le signal ne dit rien à ce sujet."))
        self.cb_sujet.currentIndexChanged.connect(self._modifie)
        self.sl_densite = QSlider(Qt.Horizontal)
        self.sl_densite.setRange(1, 60)
        self.sl_densite.setValue(int(v.density_per_min))
        self.sl_densite.valueChanged.connect(self._modifie)
        self.sp_tempo = QDoubleSpinBox()
        self.sp_tempo.setRange(5.0, 1800.0)
        self.sp_tempo.setSuffix(t(" s"))
        self.sp_tempo.setValue(float(v.tempo_scale_s))
        self.sp_tempo.setToolTip(t("Silence au bout duquel le registre « tempo » "
                                 "atteint son dernier mot."))
        self.sp_tempo.valueChanged.connect(self._modifie)
        fg.addRow(t("Assemblage"), self.cb_grammaire)
        fg.addRow(self.lab_grammaire)
        fg.addRow(t("Sujet"), self.cb_sujet)
        fg.addRow(t("Densité (énoncés/min)"), self.sl_densite)
        fg.addRow(t("Échelle du temps"), self.sp_tempo)
        gauche.addWidget(boite2)

        # --- la voix --------------------------------------------------------
        boite3 = QGroupBox(t("Voix"))
        fv = QFormLayout(boite3)
        self.chk_parler = QCheckBox(t("prononcer à voix haute"))
        self.chk_parler.setChecked(v.spoken)
        self.chk_parler.stateChanged.connect(self._modifie)
        self.chk_muet = QCheckBox(t("couper la voix (garder les énoncés écrits)"))
        self.chk_muet.setChecked(v.muted)
        self.chk_muet.stateChanged.connect(self._modifie)
        self.cb_moteur = QComboBox()
        self.cb_moteur.addItem(t("automatique"), "auto")
        for nom, description, disponible in strategies_disponibles():
            etiquette = f"{nom} — {description}"
            self.cb_moteur.addItem(etiquette if disponible
                                   else f"{nom} (absent)", nom)
            if not disponible:
                i = self.cb_moteur.count() - 1
                self.cb_moteur.model().item(i).setEnabled(False)
        _choisir(self.cb_moteur, v.backend)
        self.cb_moteur.currentIndexChanged.connect(self._modifie)
        self.cb_voix = QComboBox()
        self.cb_voix.addItem(t("voix par défaut"), "")
        _choisir(self.cb_voix, v.voice_id)
        self.cb_voix.currentIndexChanged.connect(self._modifie)
        self.sp_debit = QSpinBox()
        self.sp_debit.setRange(60, 400)
        self.sp_debit.setSuffix(t(" mots/min"))
        self.sp_debit.setValue(int(v.rate_wpm))
        self.sp_debit.valueChanged.connect(self._modifie)
        self.sl_volume = QSlider(Qt.Horizontal)
        self.sl_volume.setRange(0, 100)
        self.sl_volume.setValue(int(v.volume * 100))
        self.sl_volume.valueChanged.connect(self._modifie)
        b_essai = QPushButton(t("Essayer la voix"))
        b_essai.clicked.connect(self._essai)
        self.lab_voix = QLabel("")
        self.lab_voix.setWordWrap(True)
        self.lab_voix.setStyleSheet(f"color:{palette['texte2']};font-size:8pt;")
        fv.addRow(self.chk_parler)
        fv.addRow(self.chk_muet)
        fv.addRow(t("Synthèse"), self.cb_moteur)
        fv.addRow(t("Voix"), self.cb_voix)
        fv.addRow(t("Débit"), self.sp_debit)
        fv.addRow(t("Volume"), self.sl_volume)
        fv.addRow(b_essai)
        fv.addRow(self.lab_voix)
        gauche.addWidget(boite3)

        #  Le mode vocal parle rarement — six énoncés par minute au plus, et
        #  seulement sur événement. Sans ce voyant, on croit qu'il ne marche
        #  pas alors qu'il attend simplement que la plante fasse quelque chose.
        self.lab_veille = QLabel("")
        self.lab_veille.setWordWrap(True)
        self.lab_veille.setTextFormat(Qt.RichText)
        self.lab_veille.setStyleSheet(
            f"background:{palette['fond3']};border:1px solid {palette['trait']};"
            f"border-radius:5px;padding:7px;")
        gauche.addWidget(self.lab_veille)
        gauche.addStretch(1)
        #  La colonne de gauche est haute : sur un petit écran, elle défile
        #  plutôt que d'imposer sa taille à toute la fenêtre.
        colonne = QWidget()
        colonne.setLayout(gauche)
        rouleau = QScrollArea()
        rouleau.setWidgetResizable(True)
        rouleau.setFrameShape(QScrollArea.NoFrame)
        rouleau.setWidget(colonne)
        rouleau.setMinimumWidth(360)
        lay.addWidget(rouleau)

        # --- colonne de droite ---------------------------------------------
        droite = QTabWidget()

        page_journal = QWidget()
        pj = QVBoxLayout(page_journal)
        pj.addWidget(QLabel(t("Énoncés (le plus récent en haut)")))
        self.liste = QListWidget()
        self.liste.setAlternatingRowColors(True)
        self.liste.setWordWrap(True)
        pj.addWidget(self.liste, 1)
        b_copier = QPushButton(t("Copier le journal"))
        b_copier.clicked.connect(self._copier)
        pj.addWidget(b_copier)
        droite.addTab(page_journal, t("Journal"))

        page_regles = QWidget()
        pr = QVBoxLayout(page_regles)
        self.lab_regles = QLabel("")
        self.lab_regles.setWordWrap(True)
        self.lab_regles.setTextFormat(Qt.RichText)
        pr.addWidget(self.lab_regles)
        pr.addStretch(1)
        droite.addTab(page_regles, t("Règles appliquées"))

        page_mots = QWidget()
        pm = QVBoxLayout(page_mots)
        self.lab_mots = QLabel("")
        self.lab_mots.setWordWrap(True)
        self.lab_mots.setTextFormat(Qt.RichText)
        self.lab_mots.setFont(fonts.mono(8))
        pm.addWidget(self.lab_mots)
        pm.addStretch(1)
        droite.addTab(page_mots, t("Registres"))

        page_mesure = QWidget()
        px = QVBoxLayout(page_mesure)
        self.lab_mesure = QLabel("")
        self.lab_mesure.setWordWrap(True)
        self.lab_mesure.setTextFormat(Qt.RichText)
        px.addWidget(self.lab_mesure)
        px.addStretch(1)
        droite.addTab(page_mesure, t("Grandeurs mesurées"))

        lay.addWidget(droite, 1)

        self._modifie()
        self._remplir_sujets()
        self._remplir_registres()

    # ------------------------------------------------------------------ état
    def _modifie(self, *_):
        v = self.engine.settings.voice
        v.enabled = self.chk_actif.isChecked()
        v.grammar = self.cb_grammaire.currentData()
        v.density_per_min = float(self.sl_densite.value())
        v.tempo_scale_s = float(self.sp_tempo.value())
        v.spoken = self.chk_parler.isChecked()
        v.muted = self.chk_muet.isChecked()
        v.mute_music = self.chk_musique.isChecked()
        v.lexicon_code = self.cb_dico.currentData() or ""
        v.backend = self.cb_moteur.currentData() or "auto"
        v.voice_id = self.cb_voix.currentData() or ""
        v.rate_wpm = int(self.sp_debit.value())
        v.volume = self.sl_volume.value() / 100.0
        n = max(self.cb_sujet.count() - 1, 1)
        v.subject_position = self.cb_sujet.currentIndex() / n

        g = GRAMMAIRES.get(v.grammar, GRAMMAIRES["contemplative"])
        self.lab_grammaire.setText(t(str(g["description"])))
        lex = self.engine.vocal.lexique
        self.lab_lexique.setText(
            t("{nom} — {mots} mots · {registres} registres").format(
                nom=lex.nom, mots=lex.taille(), registres=len(lex.registres))
            + "\n" + (v.lexicon_path if v.lexicon_path
                      else t("Dictionnaire livré avec le logiciel.")))
        self.lab_regles.setText("<br>".join(self.engine.vocal.describe_rules()))
        #  On n'appelle que ce qui concerne la voix : ouvrir ou fermer la
        #  synthèse. Passer par le rappel général reconstruirait toute la
        #  chaîne de traitement à chaque mouvement de curseur, et viderait la
        #  mémoire de signal pour un changement de dictionnaire.
        try:
            self.engine.appliquer_voix()
        except Exception:                              # noqa: BLE001
            log.exception("Ouverture de la synthèse vocale impossible")
        self._maj_etat_voix()

    def _maj_etat_voix(self) -> None:
        sortie = self.engine.voice
        self.lab_voix.setText(t("État : {etat}").format(etat=sortie.etat()))
        voix = sortie.voix_disponibles()
        if voix and self.cb_voix.count() <= 1:
            self.cb_voix.blockSignals(True)
            for identifiant in voix[:60]:
                self.cb_voix.addItem(identifiant.split("/")[-1], identifiant)
            _choisir(self.cb_voix, self.engine.settings.voice.voice_id)
            self.cb_voix.blockSignals(False)

    # -- dictionnaires -------------------------------------------------------
    def _remplir_sujets(self) -> None:
        lex = self.engine.vocal.lexique
        sujets = lex.registres.get("sujet", ["je"])
        self.cb_sujet.blockSignals(True)
        self.cb_sujet.clear()
        for mot in sujets:
            self.cb_sujet.addItem(mot, mot)
        position = self.engine.settings.voice.subject_position
        i = int(round(position * max(len(sujets) - 1, 0)))
        self.cb_sujet.setCurrentIndex(min(max(i, 0), len(sujets) - 1))
        self.cb_sujet.blockSignals(False)

    def _remplir_registres(self) -> None:
        lex = self.engine.vocal.lexique
        lignes = [f"<b>{lex.nom}</b> — {lex.langue}"]
        if lex.auteur:
            lignes.append(f"Auteur : {lex.auteur}")
        if lex.note:
            lignes.append(f"<i>{lex.note}</i>")
        lignes.append("<br>")
        for cle in sorted(lex.registres):
            mots = " · ".join(lex.registres[cle])
            lignes.append(f"<b>{cle}</b><br>&nbsp;&nbsp;{mots}<br>")
        self.lab_mots.setText("<br>".join(lignes))

    def _changer_dico(self, *_):
        """Une liste déroulante pour les dictionnaires livrés, un par langue."""
        v = self.engine.settings.voice
        v.lexicon_code = self.cb_dico.currentData() or ""
        v.lexicon_path = ""                  # un choix chasse l'autre
        self.engine.vocal._suivi = False     # forcer la relecture du fichier
        self.engine.vocal.refresh()
        self._remplir_sujets()
        self._remplir_registres()
        self._modifie()

    def _charger(self) -> None:
        chemin, _ = QFileDialog.getOpenFileName(
            self, t("Ouvrir un dictionnaire"), "",
            t("Dictionnaire PhytoScope (*.json)"))
        if not chemin:
            return
        try:
            lex = Lexique.charger(chemin)
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.warning(self, t("Dictionnaire"),
                                f"Fichier illisible :\n{exc}")
            return
        self.engine.settings.voice.lexicon_path = chemin
        self.engine.settings.voice.lexicon_code = ""
        self.cb_dico.blockSignals(True)
        _choisir(self.cb_dico, "")
        self.cb_dico.blockSignals(False)
        self.engine.vocal.lexique = lex
        self._remplir_sujets()
        self._remplir_registres()
        self._modifie()

    def _ecrire_modele(self) -> None:
        chemin, _ = QFileDialog.getSaveFileName(
            self, t("Écrire un modèle de dictionnaire"),
            "dictionnaire-phytoscope.json",
            t("Dictionnaire PhytoScope (*.json)"))
        if not chemin:
            return
        try:
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(LEXIQUE_PAR_DEFAUT, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            QMessageBox.warning(self, t("Dictionnaire"),
                                f"Écriture impossible :\n{exc}")
            return
        QMessageBox.information(
            self, t("Dictionnaire"),
            f"Modèle écrit dans :\n{os.path.abspath(chemin)}\n\n"
            "Modifiez les listes de mots avec un éditeur de texte, puis "
            "ouvrez le fichier avec « Ouvrir… ». L'ordre compte : du plus "
            "faible au plus fort sur l'axe concerné.")

    def _defaut(self) -> None:
        self.engine.settings.voice.lexicon_path = ""
        self.engine.vocal._suivi = False
        self.engine.vocal.refresh()
        self._remplir_sujets()
        self._remplir_registres()
        self._modifie()

    # -- voix ----------------------------------------------------------------
    def _essai(self) -> None:
        v = self.engine.settings.voice
        self.engine.appliquer_voix()
        if not self.engine.voice.actif:
            v_ancien = v.enabled, v.spoken
            v.enabled, v.spoken = True, True
            self.engine.appliquer_voix()
            v.enabled, v.spoken = v_ancien
        lex = self.engine.vocal.lexique
        essai = " ".join([lex.choisir("sujet", v.subject_position),
                          lex.choisir("verbe_montee", 0.6),
                          lex.choisir("intensite", 0.6)])
        if not self.engine.voice.dire(essai):
            QMessageBox.information(
                self, t("Voix"),
                t("Aucune synthèse vocale n'a pu être ouverte.\n\n"
                "Sous Linux : « sudo apt install espeak-ng » ou "
                "« pip install pyttsx3 ».\n"
                "Les énoncés restent écrits et enregistrés."))
        self._maj_etat_voix()

    def _copier(self) -> None:
        from PySide6.QtWidgets import QApplication
        lignes = [self.liste.item(i).text() for i in range(self.liste.count())]
        QApplication.clipboard().setText("\n".join(lignes))

    def _maj_veille(self, state) -> None:
        """Dit, en trois lignes, pourquoi on n'entend rien — ou ce qu'on entend."""
        v = self.engine.settings.voice
        p = self.p
        if not v.enabled:
            self.lab_veille.setText(
                f"<b style='color:{p['texte2']}'>" + t("Mode vocal arrêté") +
                "</b><br>" + t("Cochez « activer le mode vocal » ci-dessus."))
            return
        sortie = self.engine.voice
        if not v.spoken:
            voix = t("écrite seulement")
        elif v.muted:
            voix = t("coupée")
        elif sortie.backend in ("", "—", "silencieuse"):
            voix = t("aucune synthèse installée")
        else:
            voix = sortie.backend
        dernier = state.last_enonce
        if dernier is not None:
            phrase = (f"<span style='color:{p['trace']}'>« {dernier.texte} »</span>"
                      "<br>" + t("il y a {n:.0f} s").format(
                          n=max(state.elapsed_s - dernier.time_s, 0.0)))
        else:
            phrase = t("aucun énoncé pour l'instant — le mode vocal attend un "
                       "événement, il n'en invente pas.")
        self.lab_veille.setText(
            f"<b style='color:{p['or']}'>" + t("En écoute") + "</b> · " + voix +
            " · " + t("{n} énoncés").format(n=state.enonces_total) + "<br>" +
            phrase)

    # -- appelé par la fenêtre principale ------------------------------------
    def ajouter_enonce(self, enonce) -> None:
        self.liste.insertItem(
            0, f"{enonce.time_s:8.1f} s   « {enonce.texte} »\n"
               f"{'':12}{enonce.reason}")
        while self.liste.count() > 300:
            self.liste.takeItem(self.liste.count() - 1)

    def recharger(self) -> None:
        """Resynchronise les commandes depuis les réglages (appel extérieur)."""
        v = self.engine.settings.voice
        for widget, valeur in ((self.chk_actif, v.enabled),
                               (self.chk_parler, v.spoken),
                               (self.chk_muet, v.muted),
                               (self.chk_musique, v.mute_music)):
            widget.blockSignals(True)
            widget.setChecked(valeur)
            widget.blockSignals(False)
        for combo, valeur in ((self.cb_grammaire, v.grammar),
                              (self.cb_moteur, v.backend),
                              (self.cb_voix, v.voice_id),
                              (self.cb_dico, v.lexicon_code)):
            combo.blockSignals(True)
            _choisir(combo, valeur)
            combo.blockSignals(False)
        self._remplir_sujets()
        self._remplir_registres()

    def refresh(self, state) -> None:
        self._maj_veille(state)
        v = self.engine.settings.voice
        dernier = state.last_enonce
        texte = f"« {dernier.texte} »" if dernier is not None else "rien encore"
        taux = (state.enonces_total / max(state.elapsed_s, 1e-9)) * 60.0
        rendement = 100.0 * state.enonces_total / max(state.events_total, 1)
        self.lab_mesure.setText(f"""
        <table cellspacing='5'>
        <tr><td><b>Dernier énoncé</b></td><td>{texte}</td></tr>
        <tr><td><b>Énoncés</b></td><td>{state.enonces_total} —
            soit {taux:.2f} par minute</td></tr>
        <tr><td><b>Rendement</b></td>
            <td>{rendement:.0f} % des événements deviennent une phrase</td></tr>
        <tr><td colspan='2'><hr></td></tr>
        <tr><td><b>Centre de gravité spectral</b></td>
            <td>{state.centroid_hz:.4f} Hz — c'est l'axe « couleur »</td></tr>
        <tr><td><b>Écart-type courant</b></td>
            <td>{state.sigma_v * 1e6:.3f} µV — c'est l'axe « intensité »</td></tr>
        <tr><td><b>Événements détectés</b></td><td>{state.events_total}</td></tr>
        <tr><td colspan='2'><hr></td></tr>
        <tr><td><b>Synthèse vocale</b></td>
            <td>{state.voice_backend or 'arrêtée'}</td></tr>
        <tr><td><b>Prononcés / abandonnés</b></td>
            <td>{state.voice_spoken} / {state.voice_dropped}</td></tr>
        <tr><td><b>Densité maximale</b></td>
            <td>{v.density_per_min:g} énoncés par minute</td></tr>
        </table>""")


def _rien(valeur, defaut="—"):
    return valeur if valeur else defaut


def _choisir(combo: QComboBox, valeur) -> None:
    for i in range(combo.count()):
        if combo.itemData(i) == valeur:
            combo.setCurrentIndex(i)
            return
