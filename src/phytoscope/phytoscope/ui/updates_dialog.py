#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/updates_dialog.py
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

"""La fenêtre « Mises à jour des bibliothèques ».

Elle interroge PyPI, affiche ce qui existe de plus récent, et n'installe que
ce qu'on lui demande d'installer.

Trois choix de conception, et leurs raisons
-------------------------------------------

**L'interrogation se fait dans un fil séparé.** Huit requêtes réseau à six
secondes de délai font quarante-huit secondes dans le pire des cas : conduites
dans le fil de l'interface, elles la figeraient, et Qt afficherait « ne répond
pas ». Le fil rend la main à chaque réponse, la barre avance, et « Annuler »
a un sens.

**Rien n'est coché d'avance.** Proposer une liste pré-cochée fait cliquer
« Installer » sans lire, et une mise à jour majeure de PySide6 ou de NumPy
peut casser la portabilité que `.ai/portabilite.md` tient à jour. C'est à
qui utilise le logiciel de décider, écart par écart.

**L'installation montre ce qu'elle fait.** La sortie de `pip` défile dans la
fenêtre, ligne à ligne, plutôt que derrière une roue qui tourne : quand cela
échoue — et cela échoue, pour une roue absente ou un compilateur manquant —
le message est la seule chose utile.
"""
from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox,
                               QHBoxLayout, QHeaderView, QLabel, QMessageBox,
                               QPlainTextEdit, QProgressBar, QPushButton,
                               QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from . import fonts
from ..core import dependency_updates as M
from ..core.logging_setup import get_logger
from ..i18n import t

log = get_logger(__name__)

#  Une couleur par état, et le mot qui va avec. Les couleurs reprennent celles
#  du reste de l'interface : vert « sève », or, cuivre.
_ETATS = {
    "a_jour":     ("#7FE0A8", "à jour"),
    "correctif":  ("#7FBEE0", "correctif"),
    "mineure":    ("#E0C073", "mise à jour mineure"),
    "majeure":    ("#E0955A", "mise à jour majeure"),
    "absente":    ("#E06C5A", "absente"),
    "inconnue":   ("#8D9A93", "non vérifiée"),
}


# ---------------------------------------------------------------------------
#  Les fils
# ---------------------------------------------------------------------------
class _FilVerification(QThread):
    """Interroge l'index sans figer l'interface."""

    avance = Signal(int, int, str)
    fini = Signal(object)

    def __init__(self, racine_exigences: str = "", parent=None):
        super().__init__(parent)
        self._racine = racine_exigences
        self._arret = False

    def demander_l_arret(self) -> None:
        self._arret = True

    def run(self) -> None:                             # pragma: no cover
        try:
            rapport = M.verifier(
                racine_exigences=self._racine,
                avancement=lambda f, tt, n: self.avance.emit(f, tt, n),
                arret=lambda: self._arret)
        except Exception as exc:                       # noqa: BLE001
            log.error("Vérification des mises à jour impossible : %s", exc)
            rapport = M.Rapport(erreur=str(exc))
        self.fini.emit(rapport)


class _FilInstallation(QThread):
    """Lance pip, et transmet sa sortie ligne à ligne."""

    ligne = Signal(str)
    fini = Signal(bool)

    def __init__(self, paquets: List[str], parent=None):
        super().__init__(parent)
        self._paquets = paquets

    def run(self) -> None:                             # pragma: no cover
        from ..core import preflight
        try:
            ok = preflight.installer(self._paquets,
                                     sortie=lambda s: self.ligne.emit(s))
        except Exception as exc:                       # noqa: BLE001
            self.ligne.emit(f"! {exc}")
            ok = False
        self.fini.emit(ok)


# ---------------------------------------------------------------------------
#  La fenêtre
# ---------------------------------------------------------------------------
class MajDialog(QDialog):
    """« Aide → Mises à jour des bibliothèques… »."""

    def __init__(self, palette: Optional[dict] = None,
                 racine_exigences: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle(t("Mises à jour des bibliothèques"))
        self.setMinimumSize(760, 520)
        self._palette = palette or {}
        self._racine = racine_exigences
        self._rapport: Optional[M.Rapport] = None
        self._fil: Optional[QThread] = None
        self._cases: List[QCheckBox] = []

        disposition = QVBoxLayout(self)

        # -- ce que fait cette fenêtre, dit une fois ------------------------
        intro = QLabel(t(
            "PhytoScope compare les bibliothèques installées à ce que publie "
            "l'index des paquets Python. Rien n'est installé sans votre "
            "demande explicite."))
        intro.setWordWrap(True)
        disposition.addWidget(intro)

        avertissement = QLabel(t(
            "Une mise à jour majeure change une interface : relisez les notes "
            "de version avant de l'installer."))
        avertissement.setWordWrap(True)
        police = QFont()
        police.setItalic(True)
        avertissement.setFont(police)
        avertissement.setStyleSheet("color: #E0C073;")
        disposition.addWidget(avertissement)

        # -- le tableau ----------------------------------------------------
        self.table = QTableWidget(0, 6, self)
        self.table.setHorizontalHeaderLabels([
            "", t("Bibliothèque"), t("Rôle"), t("Exigée"),
            t("Installée"), t("Disponible")])
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        entetes = self.table.horizontalHeader()
        entetes.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        entetes.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        entetes.setSectionResizeMode(2, QHeaderView.Stretch)
        for col in (3, 4, 5):
            entetes.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        disposition.addWidget(self.table, 1)

        # -- avancement et verdict -----------------------------------------
        self.barre = QProgressBar(self)
        self.barre.setVisible(False)
        disposition.addWidget(self.barre)

        self.verdict = QLabel("")
        self.verdict.setWordWrap(True)
        disposition.addWidget(self.verdict)

        # -- la sortie de pip, cachée jusqu'à ce qu'elle serve -------------
        self.journal = QPlainTextEdit(self)
        self.journal.setReadOnly(True)
        self.journal.setMaximumHeight(160)
        self.journal.setVisible(False)
        self.journal.setFont(fonts.mono(9))
        disposition.addWidget(self.journal)

        # -- les boutons ----------------------------------------------------
        barre_boutons = QHBoxLayout()
        self.btn_verifier = QPushButton(t("Vérifier maintenant"))
        self.btn_verifier.clicked.connect(self._verifier)
        barre_boutons.addWidget(self.btn_verifier)

        self.btn_installer = QPushButton(t("Installer la sélection"))
        self.btn_installer.setEnabled(False)
        self.btn_installer.clicked.connect(self._installer)
        barre_boutons.addWidget(self.btn_installer)

        self.btn_tout = QPushButton(t("Tout sélectionner"))
        self.btn_tout.setEnabled(False)
        self.btn_tout.clicked.connect(self._tout_selectionner)
        barre_boutons.addWidget(self.btn_tout)

        barre_boutons.addStretch(1)
        fermer = QDialogButtonBox(QDialogButtonBox.Close)
        fermer.rejected.connect(self.reject)
        barre_boutons.addWidget(fermer)
        disposition.addLayout(barre_boutons)

        #  Rien n'est interrogé à l'ouverture : une fenêtre qui part sur le
        #  réseau dès qu'on l'ouvre surprend, et le réseau n'est pas toujours
        #  celui qu'on croit. C'est un clic.
        self.verdict.setText(t("Cliquez sur « Vérifier maintenant »."))

    # -- vérification --------------------------------------------------------
    def _verifier(self) -> None:
        if self._fil is not None and self._fil.isRunning():
            #  Second clic pendant l'interrogation : c'est une annulation.
            if isinstance(self._fil, _FilVerification):
                self._fil.demander_l_arret()
            return

        self.table.setRowCount(0)
        self._cases.clear()
        self.btn_installer.setEnabled(False)
        self.btn_tout.setEnabled(False)
        self.btn_verifier.setText(t("Annuler"))
        self.barre.setVisible(True)
        self.barre.setValue(0)
        self.verdict.setText(t("Interrogation de l'index des paquets…"))

        fil = _FilVerification(self._racine, self)
        fil.avance.connect(self._avancement)
        fil.fini.connect(self._verification_finie)
        self._fil = fil
        fil.start()

    def _avancement(self, fait: int, total: int, nom: str) -> None:
        self.barre.setMaximum(max(total, 1))
        self.barre.setValue(fait)
        if nom:
            self.verdict.setText(t("Interrogation de {nom}…").format(nom=nom))

    def _verification_finie(self, rapport) -> None:
        self._fil = None
        self._rapport = rapport
        self.barre.setVisible(False)
        self.btn_verifier.setText(t("Vérifier de nouveau"))
        self._remplir(rapport)

        self.verdict.setText(rapport.resume)
        if rapport.erreur:
            self.verdict.setStyleSheet("color: #E0955A;")
        elif rapport.a_mettre_a_jour:
            self.verdict.setStyleSheet("color: #E0C073;")
        else:
            self.verdict.setStyleSheet("color: #7FE0A8;")

        #  On n'active « Installer » que s'il y a quelque chose à installer.
        a_faire = bool(rapport.a_mettre_a_jour or rapport.absentes)
        self.btn_tout.setEnabled(a_faire)
        self.btn_installer.setEnabled(False)   # tant que rien n'est coché

    def _remplir(self, rapport) -> None:
        #  Ce qui demande une action d'abord : on ne fait pas chercher.
        ordre = {"absente": 0, "majeure": 1, "mineure": 2, "correctif": 3,
                 "inconnue": 4, "a_jour": 5}
        dependances = sorted(rapport.dependances,
                             key=lambda d: (ordre.get(d.etat, 9),
                                            d.distribution.lower()))
        self.table.setRowCount(len(dependances))
        for i, d in enumerate(dependances):
            couleur, mot = _ETATS.get(d.etat, ("#8D9A93", d.etat))

            #  La case à cocher n'existe que là où elle a un sens.
            if d.ampleur or d.absente:
                case = QCheckBox()
                case.setToolTip(t(mot))
                case.setProperty("distribution", d.distribution)
                case.stateChanged.connect(self._selection_changee)
                enveloppe = QWidget()
                mise = QHBoxLayout(enveloppe)
                mise.setContentsMargins(6, 0, 0, 0)
                mise.addWidget(case)
                self.table.setCellWidget(i, 0, enveloppe)
                self._cases.append(case)
            else:
                puce = QTableWidgetItem("●")
                puce.setForeground(Qt.GlobalColor.gray)
                self.table.setItem(i, 0, puce)

            nom = QTableWidgetItem(d.distribution)
            nom.setToolTip(t(mot) + (f" — {d.erreur}" if d.erreur else ""))
            police = nom.font()
            police.setBold(bool(d.ampleur) or d.absente)
            nom.setFont(police)
            self.table.setItem(i, 1, nom)

            role = t(d.role) if d.role else ""
            if not d.obligatoire:
                role += t("  (facultative)")
            self.table.setItem(i, 2, QTableWidgetItem(role))
            self.table.setItem(i, 3, QTableWidgetItem(d.exigence or "—"))
            self.table.setItem(i, 4, QTableWidgetItem(d.installee or t("absente")))

            dispo = QTableWidgetItem(d.disponible or (d.erreur or "?"))
            from PySide6.QtGui import QColor
            dispo.setForeground(QColor(couleur))
            self.table.setItem(i, 5, dispo)

    def _selection_changee(self) -> None:
        self.btn_installer.setEnabled(bool(self._selection()))

    def _selection(self) -> List[str]:
        return [c.property("distribution") for c in self._cases if c.isChecked()]

    def _tout_selectionner(self) -> None:
        tout = not all(c.isChecked() for c in self._cases)
        for c in self._cases:
            c.setChecked(tout)
        self.btn_tout.setText(t("Tout désélectionner") if tout
                              else t("Tout sélectionner"))

    # -- installation --------------------------------------------------------
    def _installer(self) -> None:
        paquets = self._selection()
        if not paquets:
            return

        majeures = [d.distribution for d in (self._rapport.a_mettre_a_jour
                                             if self._rapport else [])
                    if d.ampleur == "majeure" and d.distribution in paquets]
        question = t("Installer {n} bibliothèque(s) ?").format(n=len(paquets))
        detail = "\n".join("  · " + p for p in paquets)
        if majeures:
            detail += "\n\n" + t(
                "Dont {n} mise(s) à jour MAJEURE(S) : elles changent une "
                "interface et peuvent empêcher le logiciel de démarrer. "
                "Le journal dira ce qui s'est passé, et « Contrôles avant "
                "vol » ce qui manque.").format(n=len(majeures))
        if QMessageBox.question(self, t("Confirmer"), question + "\n\n" + detail,
                                QMessageBox.Yes | QMessageBox.No,
                                QMessageBox.No) != QMessageBox.Yes:
            return

        self.journal.setVisible(True)
        self.journal.clear()
        self.btn_installer.setEnabled(False)
        self.btn_verifier.setEnabled(False)
        self.btn_tout.setEnabled(False)
        self.verdict.setText(t("Installation en cours…"))

        fil = _FilInstallation(paquets, self)
        fil.ligne.connect(self._journal_ligne)
        fil.fini.connect(self._installation_finie)
        self._fil = fil
        fil.start()

    def _journal_ligne(self, ligne: str) -> None:
        self.journal.appendPlainText(ligne)

    def _installation_finie(self, ok: bool) -> None:
        self._fil = None
        self.btn_verifier.setEnabled(True)
        if ok:
            self.verdict.setText(t(
                "Installation terminée. Redémarrez PhytoScope pour que les "
                "nouvelles versions soient chargées."))
            self.verdict.setStyleSheet("color: #7FE0A8;")
        else:
            self.verdict.setText(t(
                "Installation en échec — le détail est ci-dessous. Les "
                "anciennes versions restent en place."))
            self.verdict.setStyleSheet("color: #E06C5A;")
        #  On revérifie pour montrer l'état réel, et non l'état espéré.
        self._verifier()

    # -- fermeture -----------------------------------------------------------
    def reject(self) -> None:
        """Ne pas laisser un fil courir derrière une fenêtre fermée."""
        if self._fil is not None and self._fil.isRunning():
            if isinstance(self._fil, _FilVerification):
                self._fil.demander_l_arret()
            #  Une installation en cours, elle, ne s'interrompt pas : couper
            #  pip au milieu laisse l'environnement à moitié écrit.
            elif isinstance(self._fil, _FilInstallation):
                QMessageBox.information(
                    self, t("Installation en cours"),
                    t("Attendez la fin de l'installation : interrompre pip "
                      "laisserait l'environnement Python à moitié écrit."))
                return
            self._fil.wait(2000)
        super().reject()
