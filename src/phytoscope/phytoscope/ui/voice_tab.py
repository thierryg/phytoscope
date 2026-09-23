# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/voice_tab.py
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
    "This is not a translation. The plant has no language; these words are those of the chosen dictionary, applied to measured quantities according to the rules shown opposite. What is said here is a dialogue between you and your own frame of reading.")


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
            f"background:{palette['background3']};color:{palette['gold']};"
            f"border:1px solid {palette['gold']};border-radius:5px;padding:7px;")
        racine.addWidget(bandeau)

        lay = QHBoxLayout()
        racine.addLayout(lay, 1)
        gauche = QVBoxLayout()

        # --- le dictionnaire ------------------------------------------------
        boite = QGroupBox(t("Dictionary"))
        fd = QFormLayout(boite)
        self.chk_actif = QCheckBox(t("enable speech mode"))
        self.chk_actif.setChecked(v.enabled)
        self.chk_actif.setToolTip(
            t("The plant “speaks” instead of playing: same events, same thresholds, words instead of notes."))
        self.chk_actif.stateChanged.connect(self._modifie)
        self.chk_musique = QCheckBox(t("mute the music while speaking"))
        self.chk_musique.setChecked(v.mute_music)
        self.chk_musique.setToolTip(
            t("A voice and a synthesiser playing together cover each other. Detection, meanwhile, carries on as before."))
        self.chk_musique.stateChanged.connect(self._modifie)
        self.cb_dico = QComboBox()
        self.cb_dico.addItem(t("— follow the interface language —"), "")
        for code, titre in lexiques_livres():
            self.cb_dico.addItem(titre, code)
        _choisir(self.cb_dico, v.lexicon_code)
        self.cb_dico.currentIndexChanged.connect(self._changer_dico)
        self.lab_lexique = QLabel("")
        self.lab_lexique.setWordWrap(True)
        self.lab_lexique.setStyleSheet(f"color:{palette['text2']};")
        bl = QHBoxLayout()
        b_charger = QPushButton(t("Open…"))
        b_charger.clicked.connect(self._charger)
        b_modele = QPushButton(t("Write a template…"))
        b_modele.setToolTip(t("Saves the bundled dictionary to a JSON file, to be edited with a text editor."))
        b_modele.clicked.connect(self._ecrire_modele)
        b_defaut = QPushButton(t("Back to the bundled dictionary"))
        b_defaut.clicked.connect(self._defaut)
        bl.addWidget(b_charger)
        bl.addWidget(b_modele)
        fd.addRow(self.chk_actif)
        fd.addRow(self.chk_musique)
        fd.addRow(t("Dictionary"), self.cb_dico)
        fd.addRow(self.lab_lexique)
        fd.addRow(bl)
        fd.addRow(b_defaut)
        gauche.addWidget(boite)

        # --- la grammaire ---------------------------------------------------
        boite2 = QGroupBox(t("Grammar"))
        fg = QFormLayout(boite2)
        self.cb_grammaire = QComboBox()
        for cle, g in GRAMMAIRES.items():
            self.cb_grammaire.addItem(t(str(g["titre"])), cle)
        _choisir(self.cb_grammaire, v.grammar)
        self.cb_grammaire.currentIndexChanged.connect(self._modifie)
        self.lab_grammaire = QLabel("")
        self.lab_grammaire.setWordWrap(True)
        self.lab_grammaire.setStyleSheet(f"color:{palette['text2']};")
        self.cb_sujet = QComboBox()
        self.cb_sujet.setToolTip(t("Who is speaking. You decide: the signal says nothing about it."))
        self.cb_sujet.currentIndexChanged.connect(self._modifie)
        self.sl_densite = QSlider(Qt.Horizontal)
        self.sl_densite.setRange(1, 60)
        self.sl_densite.setValue(int(v.density_per_min))
        self.sl_densite.valueChanged.connect(self._modifie)
        self.sp_tempo = QDoubleSpinBox()
        self.sp_tempo.setRange(5.0, 1800.0)
        self.sp_tempo.setSuffix(t(" s"))
        self.sp_tempo.setValue(float(v.tempo_scale_s))
        self.sp_tempo.setToolTip(t("The silence after which the “tempo” register reaches its last word."))
        self.sp_tempo.valueChanged.connect(self._modifie)
        fg.addRow(t("Assembly"), self.cb_grammaire)
        fg.addRow(self.lab_grammaire)
        fg.addRow(t("Subject"), self.cb_sujet)
        fg.addRow(t("Density (utterances/min)"), self.sl_densite)
        fg.addRow(t("Time scale"), self.sp_tempo)
        gauche.addWidget(boite2)

        # --- la voix --------------------------------------------------------
        boite3 = QGroupBox(t("Voice"))
        fv = QFormLayout(boite3)
        self.chk_parler = QCheckBox(t("speak out loud"))
        self.chk_parler.setChecked(v.spoken)
        self.chk_parler.stateChanged.connect(self._modifie)
        self.chk_muet = QCheckBox(t("mute the voice (keep the written utterances)"))
        self.chk_muet.setChecked(v.muted)
        self.chk_muet.stateChanged.connect(self._modifie)
        self.cb_moteur = QComboBox()
        self.cb_moteur.addItem(t("automatic"), "auto")
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
        self.cb_voix.addItem(t("default voice"), "")
        _choisir(self.cb_voix, v.voice_id)
        self.cb_voix.currentIndexChanged.connect(self._modifie)
        self.sp_debit = QSpinBox()
        self.sp_debit.setRange(60, 400)
        self.sp_debit.setSuffix(t(" words/min"))
        self.sp_debit.setValue(int(v.rate_wpm))
        self.sp_debit.valueChanged.connect(self._modifie)
        self.sl_volume = QSlider(Qt.Horizontal)
        self.sl_volume.setRange(0, 100)
        self.sl_volume.setValue(int(v.volume * 100))
        self.sl_volume.valueChanged.connect(self._modifie)
        b_essai = QPushButton(t("Try the voice"))
        b_essai.clicked.connect(self._essai)
        self.lab_voix = QLabel("")
        self.lab_voix.setWordWrap(True)
        self.lab_voix.setStyleSheet(f"color:{palette['text2']};font-size:8pt;")
        fv.addRow(self.chk_parler)
        fv.addRow(self.chk_muet)
        fv.addRow(t("Synthesis"), self.cb_moteur)
        fv.addRow(t("Voice"), self.cb_voix)
        fv.addRow(t("Speech rate"), self.sp_debit)
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
            f"background:{palette['background3']};border:1px solid {palette['line']};"
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
        pj.addWidget(QLabel(t("Utterances (most recent first)")))
        self.liste = QListWidget()
        self.liste.setAlternatingRowColors(True)
        self.liste.setWordWrap(True)
        pj.addWidget(self.liste, 1)
        b_copier = QPushButton(t("Copy the log"))
        b_copier.clicked.connect(self._copier)
        pj.addWidget(b_copier)
        droite.addTab(page_journal, t("Log"))

        page_regles = QWidget()
        pr = QVBoxLayout(page_regles)
        self.lab_regles = QLabel("")
        self.lab_regles.setWordWrap(True)
        self.lab_regles.setTextFormat(Qt.RichText)
        pr.addWidget(self.lab_regles)
        pr.addStretch(1)
        droite.addTab(page_regles, t("Rules applied"))

        page_mots = QWidget()
        pm = QVBoxLayout(page_mots)
        self.lab_mots = QLabel("")
        self.lab_mots.setWordWrap(True)
        self.lab_mots.setTextFormat(Qt.RichText)
        self.lab_mots.setFont(fonts.mono(8))
        pm.addWidget(self.lab_mots)
        pm.addStretch(1)
        droite.addTab(page_mots, t("Registers"))

        page_mesure = QWidget()
        px = QVBoxLayout(page_mesure)
        self.lab_mesure = QLabel("")
        self.lab_mesure.setWordWrap(True)
        self.lab_mesure.setTextFormat(Qt.RichText)
        px.addWidget(self.lab_mesure)
        px.addStretch(1)
        droite.addTab(page_mesure, t("Measured quantities"))

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
            t("{nom} — {mots} words · {registres} registers").format(
                nom=lex.nom, mots=lex.taille(), registres=len(lex.registres))
            + "\n" + (v.lexicon_path if v.lexicon_path
                      else t("Dictionary shipped with the software.")))
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
        self.lab_voix.setText(t("State: {etat}").format(etat=sortie.etat()))
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
            self, t("Open a dictionary"), "",
            t("PhytoScope dictionary (*.json)"))
        if not chemin:
            return
        try:
            lex = Lexique.charger(chemin)
        except (OSError, ValueError, TypeError) as exc:
            QMessageBox.warning(
                self, t("Dictionary"),
                t("The file cannot be read:\n{erreur}").format(erreur=exc))
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
            self, t("Write a dictionary template"),
            "dictionnaire-phytoscope.json",
            t("PhytoScope dictionary (*.json)"))
        if not chemin:
            return
        try:
            with open(chemin, "w", encoding="utf-8") as f:
                json.dump(LEXIQUE_PAR_DEFAUT, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            QMessageBox.warning(
                self, t("Dictionary"),
                t("Writing failed:\n{erreur}").format(erreur=exc))
            return
        QMessageBox.information(
            self, t("Dictionary"),
            t("Template written to:\n{chemin}\n\nEdit the word lists with a text editor, then open the file with “Open…”. Order matters: weakest to strongest along the axis concerned.").format(chemin=os.path.abspath(chemin)))

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
                self, t("Voice"),
                t("No speech synthesis could be opened.\n\nOn Linux: “sudo apt install espeak-ng” or “pip install pyttsx3”.\nUtterances are still written and recorded."))
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
                f"<b style='color:{p['text2']}'>" + t("Speech mode stopped") +
                "</b><br>" + t("Tick “enable speech mode” above."))
            return
        sortie = self.engine.voice
        if not v.spoken:
            voix = t("written only")
        elif v.muted:
            voix = t("muted")
        elif sortie.backend in ("", "—", "silencieuse"):
            voix = t("no synthesis installed")
        else:
            voix = sortie.backend
        dernier = state.last_enonce
        if dernier is not None:
            phrase = (f"<span style='color:{p['trace']}'>« {dernier.texte} »</span>"
                      "<br>" + t("{n:.0f} s ago").format(
                          n=max(state.elapsed_s - dernier.time_s, 0.0)))
        else:
            phrase = t("no utterance yet — speech mode waits for an event, it does not invent any.")
        self.lab_veille.setText(
            f"<b style='color:{p['gold']}'>" + t("Listening") + "</b> · " + voix +
            " · " + t("{n} utterances").format(n=state.enonces_total) + "<br>" +
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
