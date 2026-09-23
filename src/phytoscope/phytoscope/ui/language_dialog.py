#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/language_dialog.py
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

"""La question de la langue, posée une fois.

Elle s'affiche au **premier** démarrage, avant la fenêtre principale, et
jamais ensuite : le choix part dans `reglages.json`, que le logiciel relit à
chaque fois.

Pourquoi demander, et non deviner
---------------------------------

La contrainte `C-31` interdit la détection automatique de la locale. Ce n'est
pas une coquetterie : une machine dont l'environnement dit `fr_FR` peut être
celle d'un atelier où l'on travaille en anglais, celle d'un poste partagé, ou
celle d'une image système clonée. Deviner produit un logiciel qu'il faut
reconfigurer, et le fait à l'insu de qui s'en sert.

Pourquoi ici, alors que les installateurs la posent déjà
--------------------------------------------------------

Le `.run`, le `.exe` et le `.app` la posent. Le `.deb` et le `.rpm` ne
peuvent pas : `apt` et `dnf` installent sans rien demander, et c'est
précisément ce qu'on attend d'eux. Cette fenêtre couvre ces deux cas — et
celui de qui lance le logiciel depuis les sources.

Chaque langue est écrite **dans sa propre langue**. C'est la seule façon
d'être lisible par quelqu'un qui ne comprend pas celle qui est affichée : un
lecteur coréen reconnaît « 한국어 », pas « coréen ».
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QLabel, QListWidget,
                               QListWidgetItem, QVBoxLayout)

from ..core.logging_setup import get_logger

log = get_logger(__name__)

#  « Choisissez votre langue », dans les onze langues. Ce libellé-là ne peut
#  pas passer par `t()` : au moment où il s'affiche, la langue n'est pas
#  encore choisie. On les montre donc toutes, empilées — ce qui est aussi le
#  moyen le plus sûr d'être compris.
INVITES = (
    "Choisissez votre langue",
    "Choose your language",
    "Elija su idioma",
    "选择语言",
)


class LangueDialog(QDialog):
    """La liste des langues, au premier démarrage."""

    def __init__(self, langue_courante: str = "fr", parent=None):
        super().__init__(parent)
        self.setWindowTitle("PhytoScope")
        self.setMinimumWidth(380)
        self._choix = langue_courante

        disposition = QVBoxLayout(self)

        titre = QLabel(" · ".join(INVITES))
        titre.setWordWrap(True)
        titre.setAlignment(Qt.AlignmentFlag.AlignCenter)
        police = titre.font()
        police.setPointSize(max(police.pointSize() + 1, 10))
        titre.setFont(police)
        disposition.addWidget(titre)

        self.liste = QListWidget(self)
        for code, nom, sens in self._langues():
            item = QListWidgetItem(nom)
            item.setData(Qt.ItemDataRole.UserRole, code)
            #  L'arabe s'écrit de droite à gauche : son nom aussi.
            if sens == "rtl":
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                      | Qt.AlignmentFlag.AlignVCenter)
            self.liste.addItem(item)
            if code == langue_courante:
                self.liste.setCurrentItem(item)
        if self.liste.currentRow() < 0:
            self.liste.setCurrentRow(0)
        #  Un double-clic vaut « valider » : c'est ce qu'on essaie d'abord.
        self.liste.itemDoubleClicked.connect(lambda _: self.accept())
        disposition.addWidget(self.liste)

        note = QLabel(
            t("You can change this later under “Display → Language”."))
        note.setWordWrap(True)
        note.setStyleSheet("color: #8D9A93;")
        disposition.addWidget(note)

        boutons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        boutons.accepted.connect(self.accept)
        disposition.addWidget(boutons)

    @staticmethod
    def _langues() -> List[Tuple[str, str, str]]:
        """(code, nom dans sa langue, sens) — français compris.

        La liste vient de `i18n.langues_disponibles()`, qui énumère les
        catalogues réellement présents : ajouter une langue au logiciel la
        fait apparaître ici sans qu'on y touche.
        """
        from ..i18n import langues_disponibles
        trouvees = []
        for code, nom, _nom_fr, _n, sens in langues_disponibles():
            trouvees.append((code, nom, sens or "ltr"))
        if not any(c == "fr" for c, _, _ in trouvees):
            trouvees.insert(0, ("fr", "Français", "ltr"))
        return trouvees

    def langue(self) -> str:
        """Le code retenu."""
        item = self.liste.currentItem()
        if item is None:
            return self._choix
        return str(item.data(Qt.ItemDataRole.UserRole) or self._choix)


def demander_si_premier_lancement(settings) -> Optional[str]:
    """Pose la question si c'est le premier démarrage ; rend le code retenu.

    Rend `None` si la question n'avait pas à être posée. Le réglage est écrit
    par l'appelant, avec le reste : on n'écrit pas deux fois le même fichier.
    """
    if not getattr(settings, "premier_lancement", False):
        return None
    dialogue = LangueDialog(settings.ui.language)
    dialogue.exec()
    retenue = dialogue.langue()
    log.warning("Premier démarrage : langue choisie = %s", retenue)
    return retenue
