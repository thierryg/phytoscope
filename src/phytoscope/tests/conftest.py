# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/conftest.py
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

"""Réglages communs aux essais.

Deux précautions valent d'être expliquées.

**Aucun essai ne doit toucher la configuration de l'utilisateur.** Une séance
de mise au point a déjà écrit « langue : coréen » dans le fichier de réglages
d'une vraie installation ; on ne recommence pas. ``XDG_CONFIG_HOME`` et ses
équivalents sont donc détournés vers un dossier temporaire pour toute la
campagne.

**Qt tourne sans écran.** La plateforme ``offscreen`` permet de construire de
vraies fenêtres, de les peindre et de les interroger dans une intégration
continue dépourvue de serveur graphique.
"""
from __future__ import annotations

import os
import tempfile

import pytest

_bac = tempfile.mkdtemp(prefix="phytoscope-essais-")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["XDG_CONFIG_HOME"] = os.path.join(_bac, "config")
os.environ["XDG_DATA_HOME"] = os.path.join(_bac, "data")
os.environ["XDG_CACHE_HOME"] = os.path.join(_bac, "cache")
#  macOS et Windows ne lisent pas XDG : on neutralise aussi leurs chemins.
os.environ["HOME"] = os.environ.get("HOME", _bac)
os.environ.setdefault("APPDATA", os.path.join(_bac, "AppData"))


@pytest.fixture(scope="session")
def qapp():
    """L'unique QApplication de la campagne — Qt n'en tolère pas deux."""
    PySide6 = pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    yield app
    app.processEvents()
