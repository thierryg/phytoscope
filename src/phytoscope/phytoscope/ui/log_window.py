# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/log_window.py
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

"""La fenêtre du journal — voir le fichier, savoir où il est, l'emporter.

Un journal qui ne se lit pas ne sert à rien. Jusqu'ici le fichier existait, à
un endroit que l'utilisateur devait deviner, et il fallait un terminal pour le
consulter. Cette fenêtre répond aux trois questions qu'on se pose quand quelque
chose s'est mal passé :

* **où est-il ?** — le chemin est écrit en toutes lettres, sélectionnable, et
  copiable d'un bouton ; la taille et l'heure de dernière écriture avec ;
* **que dit-il, maintenant ?** — le contenu se complète tout seul, sans qu'on
  ait à rouvrir quoi que ce soit ; une ligne qui s'écrit pendant la séance
  apparaît dans la seconde ;
* **comment l'envoyer ?** — un bouton en fait une copie à l'endroit choisi,
  avec les fichiers de rotation si on le demande, parce qu'un incident survenu
  il y a une heure est souvent dans `phytoscope.log.1` et non dans le fichier
  courant.

Deux choix méritent d'être expliqués.

**La lecture est incrémentale.** On ne relit pas tout le fichier deux fois par
seconde : on retient la position atteinte et on ne lit que ce qui s'est ajouté.
Un journal de deux mégaoctets ne coûte donc rien à surveiller. Si le fichier
rapetisse — rotation, ou vidage depuis les réglages —, on s'en aperçoit et on
repart du début.

**La fenêtre n'est pas modale.** On veut lire le journal *pendant* que la
séance tourne, précisément pour voir apparaître la ligne au moment où le
problème se produit.
"""
from __future__ import annotations

import os
import shutil
import time
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFileDialog,
                               QHBoxLayout, QLabel, QLineEdit, QMessageBox,
                               QPlainTextEdit, QPushButton, QVBoxLayout)

from ..core import logging_setup as jl
from ..i18n import t
from . import fonts

#  Deux fois par seconde : assez pour voir la ligne s'écrire, assez peu pour
#  ne rien coûter — on ne lit de toute façon que l'ajout.
PERIODE_MS = 500
#  Au-delà, on coupe le début : un QPlainTextEdit de plusieurs centaines de
#  milliers de lignes fait ramer l'interface, et le fichier reste complet.
LIGNES_MAX = 5000


def fichiers_de_rotation(chemin: str) -> List[str]:
    """Le journal et ses archives, du plus récent au plus ancien."""
    if not chemin:
        return []
    presents = [chemin] if os.path.exists(chemin) else []
    i = 1
    while os.path.exists(f"{chemin}.{i}"):
        presents.append(f"{chemin}.{i}")
        i += 1
    return presents


class LogWindow(QDialog):
    """Le journal, en direct, avec son chemin et de quoi l'emporter."""

    def __init__(self, palette: dict, settings=None, parent=None):
        super().__init__(parent)
        self.p = palette
        self.settings = settings
        self._position = 0          # octets déjà lus
        self._empreinte = (-1, -1.0)  # (taille, date de modification)
        self.setWindowTitle(t("Journal du logiciel"))
        self.setMinimumSize(760, 460)
        self.resize(980, 620)
        #  Non modale, et elle survit à la fermeture : on la rouvre telle
        #  qu'on l'a laissée, filtre compris.
        self.setModal(False)

        lay = QVBoxLayout(self)

        # -- où est le fichier ------------------------------------------------
        self.lab_chemin = QLineEdit(jl.log_path() or t("(aucun fichier)"))
        self.lab_chemin.setReadOnly(True)
        self.lab_chemin.setFont(fonts.mono())
        self.lab_chemin.setToolTip(
            t("Emplacement du fichier de journal. Sélectionnable : on peut le "
              "copier et le coller dans un terminal ou un courriel."))
        btn_chemin = QPushButton(t("Copier le chemin"))
        btn_chemin.clicked.connect(self._copier_chemin)
        btn_dossier = QPushButton(t("Ouvrir le dossier"))
        btn_dossier.clicked.connect(self._ouvrir_dossier)
        ligne = QHBoxLayout()
        ligne.addWidget(QLabel(t("Fichier :")))
        ligne.addWidget(self.lab_chemin, 1)
        ligne.addWidget(btn_chemin)
        ligne.addWidget(btn_dossier)
        lay.addLayout(ligne)

        # -- le contenu -------------------------------------------------------
        self.vue = QPlainTextEdit()
        self.vue.setReadOnly(True)
        self.vue.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.vue.setFont(fonts.mono(9))
        self.vue.setMaximumBlockCount(LIGNES_MAX)
        lay.addWidget(self.vue, 1)

        # -- filtre et niveau -------------------------------------------------
        outils = QHBoxLayout()
        self.filtre = QLineEdit()
        self.filtre.setPlaceholderText(
            t("Filtrer : ne montrer que les lignes contenant…"))
        self.filtre.textChanged.connect(self._relire_entierement)
        outils.addWidget(self.filtre, 1)

        outils.addWidget(QLabel(t("Niveau :")))
        self.cb_niveau = QComboBox()
        for code in jl.NIVEAUX:
            self.cb_niveau.addItem(t(jl.NIVEAUX_FR[code]), code)
        self._choisir_niveau(jl.current_level())
        self.cb_niveau.currentIndexChanged.connect(self._changer_niveau)
        self.cb_niveau.setToolTip(
            t("Change ce qui sera écrit à partir de maintenant. Les lignes "
              "déjà dans le fichier ne changent pas."))
        outils.addWidget(self.cb_niveau)

        self.cb_suivre = QCheckBox(t("Suivre la fin"))
        self.cb_suivre.setChecked(True)
        self.cb_suivre.setToolTip(
            t("Descend automatiquement sur la dernière ligne écrite. "
              "Décochez pour lire tranquillement plus haut."))
        outils.addWidget(self.cb_suivre)
        lay.addLayout(outils)

        # -- état et actions --------------------------------------------------
        self.lab_etat = QLabel("—")
        self.lab_etat.setStyleSheet(f"color:{palette['texte2']};")
        self.btn_copie = QPushButton(t("Enregistrer une copie…"))
        self.btn_copie.setToolTip(
            t("Écrit une copie du journal à l'endroit de votre choix — pour "
              "l'archiver avec la séance ou le joindre à un signalement."))
        self.btn_copie.clicked.connect(self._enregistrer_copie)
        self.btn_vider = QPushButton(t("Vider le journal"))
        self.btn_vider.clicked.connect(self._vider)
        btn_fermer = QPushButton(t("Fermer"))
        btn_fermer.clicked.connect(self.hide)
        bas = QHBoxLayout()
        bas.addWidget(self.lab_etat, 1)
        bas.addWidget(self.btn_copie)
        bas.addWidget(self.btn_vider)
        bas.addWidget(btn_fermer)
        lay.addLayout(bas)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._rafraichir)
        self._relire_entierement()

    # ------------------------------------------------------------------ vie
    def showEvent(self, event) -> None:            # noqa: N802 (API Qt)
        super().showEvent(event)
        self.lab_chemin.setText(jl.log_path() or t("(aucun fichier)"))
        self._relire_entierement()
        self.timer.start(PERIODE_MS)

    def hideEvent(self, event) -> None:            # noqa: N802 (API Qt)
        #  Fermée, elle ne lit plus rien : une fenêtre invisible qui réveille
        #  le disque deux fois par seconde serait une faute.
        self.timer.stop()
        super().hideEvent(event)

    # -------------------------------------------------------------- lecture
    def _chemin(self) -> str:
        return jl.log_path()

    def _ajouter(self, texte: str) -> None:
        """N'écrit que les lignes retenues par le filtre."""
        motif = self.filtre.text().strip().lower()
        for ligne in texte.splitlines():
            if motif and motif not in ligne.lower():
                continue
            self.vue.appendPlainText(ligne)

    def _relire_entierement(self) -> None:
        self.vue.clear()
        self._position = 0
        self._empreinte = (-1, -1.0)
        self._rafraichir(force=True)
        self._descendre()

    def _rafraichir(self, force: bool = False) -> None:
        chemin = self._chemin()
        if not chemin or not os.path.exists(chemin):
            self.lab_etat.setText(t("Aucun fichier de journal pour l'instant."))
            return
        try:
            info = os.stat(chemin)
        except OSError as exc:
            self.lab_etat.setText(t("Journal illisible : {erreur}").format(erreur=exc))
            return
        empreinte = (info.st_size, info.st_mtime)
        if empreinte == self._empreinte and not force:
            return
        self._empreinte = empreinte

        #  Le fichier a rapetissé : rotation, ou vidage. On repart du début,
        #  sans quoi on lirait au milieu d'une ligne.
        if info.st_size < self._position:
            self.vue.clear()
            self._position = 0
        try:
            with open(chemin, "r", encoding="utf-8", errors="replace") as f:
                f.seek(self._position)
                ajout = f.read()
                self._position = f.tell()
        except OSError as exc:
            self.lab_etat.setText(t("Journal illisible : {erreur}").format(erreur=exc))
            return
        if ajout:
            self._ajouter(ajout)
            if self.cb_suivre.isChecked():
                self._descendre()
        self._maj_etat(info)

    def _descendre(self) -> None:
        barre = self.vue.verticalScrollBar()
        barre.setValue(barre.maximum())

    def _maj_etat(self, info) -> None:
        #  « 0 ko » pour un fichier de 79 octets serait un mensonge poli :
        #  en dessous du kilo-octet, on donne les octets.
        octets = info.st_size
        if octets < 1024:
            taille = f"{octets} o"
        elif octets < 1024 * 1024:
            taille = f"{octets / 1024:.0f} ko"
        else:
            taille = f"{octets / (1024 * 1024):.1f} Mo"
        archives = max(len(fichiers_de_rotation(self._chemin())) - 1, 0)
        texte = t("{taille}, dernière écriture à {heure}").format(
            taille=taille, heure=time.strftime("%H:%M:%S",
                                               time.localtime(info.st_mtime)))
        if archives:
            texte += "  ·  " + t("{n} fichier(s) de rotation").format(n=archives)
        if self.filtre.text().strip():
            texte += "  ·  " + t("filtre actif")
        self.lab_etat.setText(texte)

    # -------------------------------------------------------------- actions
    def _copier_chemin(self) -> None:
        chemin = self._chemin()
        if chemin:
            QGuiApplication.clipboard().setText(chemin)
            self.lab_etat.setText(t("Chemin copié dans le presse-papiers."))

    def _ouvrir_dossier(self) -> None:
        chemin = self._chemin()
        if not chemin:
            return
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(chemin)))

    def _choisir_niveau(self, code: str) -> None:
        for i in range(self.cb_niveau.count()):
            if self.cb_niveau.itemData(i) == code:
                self.cb_niveau.blockSignals(True)
                self.cb_niveau.setCurrentIndex(i)
                self.cb_niveau.blockSignals(False)
                return

    def _changer_niveau(self) -> None:
        code = self.cb_niveau.currentData()
        applique = jl.set_level(code)
        if self.settings is not None and hasattr(self.settings, "logging"):
            self.settings.logging.level = applique
        self.lab_etat.setText(
            t("Niveau de journalisation : {niveau}").format(niveau=applique))

    def _enregistrer_copie(self) -> None:
        """Une copie du fichier, à l'endroit choisi, archives comprises."""
        sources = fichiers_de_rotation(self._chemin())
        if not sources:
            QMessageBox.information(
                self, t("Journal du logiciel"),
                t("Il n'y a pas encore de fichier de journal à copier."))
            return

        defaut = os.path.join(
            os.path.expanduser("~"),
            time.strftime("phytoscope-%Y%m%d-%H%M.log"))
        cible, _ = QFileDialog.getSaveFileName(
            self, t("Enregistrer une copie du journal"), defaut,
            t("Journaux (*.log *.txt);;Tous les fichiers (*)"))
        if not cible:
            return

        emporter_tout = False
        if len(sources) > 1:
            reponse = QMessageBox.question(
                self, t("Journal du logiciel"),
                t("Il existe {n} fichier(s) de rotation plus anciens. Les "
                  "inclure dans la copie ?\n\nUn incident survenu il y a "
                  "quelque temps s'y trouve souvent plutôt que dans le "
                  "fichier courant.").format(n=len(sources) - 1),
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            emporter_tout = reponse == QMessageBox.Yes

        try:
            if emporter_tout:
                #  Du plus ancien au plus récent : le fichier obtenu se lit
                #  dans l'ordre du temps, ce qui est le seul ordre utile.
                with open(cible, "w", encoding="utf-8") as sortie:
                    for source in reversed(sources):
                        sortie.write(f"\n===== {os.path.basename(source)} =====\n")
                        with open(source, "r", encoding="utf-8",
                                  errors="replace") as entree:
                            shutil.copyfileobj(entree, sortie)
            else:
                shutil.copyfile(sources[0], cible)
        except OSError as exc:
            QMessageBox.warning(
                self, t("Journal du logiciel"),
                t("Copie impossible : {erreur}").format(erreur=exc))
            return
        self.lab_etat.setText(
            t("Copie enregistrée : {chemin}").format(chemin=cible))

    def _vider(self) -> None:
        reponse = QMessageBox.question(
            self, t("Vider le journal"),
            t("Effacer le contenu du fichier de journal ? Les archives de "
              "rotation ne sont pas touchées."),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reponse != QMessageBox.Yes:
            return
        if jl.clear():
            self._relire_entierement()
            self.lab_etat.setText(t("Journal vidé."))
        else:
            self.lab_etat.setText(t("Le journal n'a pas pu être vidé."))
