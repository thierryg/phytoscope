# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/sdk/bonjour-monde/test_bonjour_monde.py
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

"""Essais du module « bonjour-monde » — sans logiciel lancé, sans matériel.

C'est le point le plus utile de ce fichier : on éprouve un module **sans rien
démarrer**. Un contexte de fausse monnaie, un signal fabriqué, et l'on appelle
les méthodes. Développer un module ne demande donc ni plante sur le bureau, ni
carte branchée, ni même que PhytoScope tourne.

Copiez ce fichier en même temps que `module.py` : vos essais ressembleront à
ceux-ci.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Dict, List

import numpy as np
import pytest


# ---------------------------------------------------------------------------
#  De quoi faire tourner un module sans logiciel
# ---------------------------------------------------------------------------
class ContexteDEssai:
    """Un faux contexte : la même surface, sans rien derrière.

    On implémente ce dont le module se sert, et rien d'autre. Si un essai
    échoue parce qu'une méthode manque ici, c'est le signe que le module
    emploie une partie de l'API qu'il faudra aussi éprouver.
    """

    def __init__(self, reglages: Dict[str, Any] | None = None) -> None:
        self.reglages: Dict[str, Any] = dict(reglages or {})
        self.abonnements: Dict[str, List] = {}
        self.journal_ecrit: List[str] = []
        self.frequence_hz = 250.0
        self.pleine_echelle_v = 2.5
        self.reseau_hz = 50.0

    def abonner(self, evenement: str, rappel) -> None:
        self.abonnements.setdefault(evenement, []).append(rappel)

    def journal(self, message: str, niveau: str = "info") -> None:
        self.journal_ecrit.append(f"{niveau}: {message}")

    def message(self, texte: str) -> None:
        self.journal_ecrit.append(f"message: {texte}")

    def traduire(self, texte: str) -> str:
        return texte                      # en essai, la langue source suffit

    def dossier(self) -> str:
        import tempfile
        return tempfile.mkdtemp(prefix="essai-module-")

    def signal(self, secondes: float = 60.0, brut: bool = False) -> np.ndarray:
        return signal_dessai(secondes)

    def instants_evenements(self) -> List[float]:
        return []

    def etat(self):
        from types import SimpleNamespace
        return SimpleNamespace(duree_s=120.0, source="essai", en_marche=True,
                               relecture=False)


def signal_dessai(secondes: float = 30.0, fs: float = 250.0) -> np.ndarray:
    """Un signal plausible : du bruit, une dérive lente, quelques bouffées."""
    n = int(secondes * fs)
    t = np.arange(n) / fs
    r = np.random.default_rng(42)
    x = r.normal(0.0, 3e-6, n)                    # bruit de fond, 3 µV
    x += 4e-5 * np.sin(2 * np.pi * t / 400.0)     # dérive lente
    for t0 in np.arange(5.0, secondes, 7.0):      # bouffées d'activité
        x += 1.2e-4 * np.exp(-((t - t0) / 1.5) ** 2)
    return x


@pytest.fixture()
def module():
    """Charge `module.py` du même dossier, sans l'installer."""
    ici = os.path.dirname(os.path.abspath(__file__))
    chemin = os.path.join(ici, "module.py")
    spec = importlib.util.spec_from_file_location("module_bonjour_monde", chemin)
    paquet = importlib.util.module_from_spec(spec)
    #  Inscrit AVANT l'exécution : `@dataclass` va chercher
    #  `sys.modules[cls.__module__]` et échouerait sur un module absent.
    sys.modules["module_bonjour_monde"] = paquet
    spec.loader.exec_module(paquet)
    return paquet


@pytest.fixture()
def instance(module):
    """Le module, construit et installé, avec un contexte d'essai."""
    from phytoscope.api import Module
    classe = next(o for o in vars(module).values()
                  if isinstance(o, type) and issubclass(o, Module)
                  and o is not Module)
    contexte = ContexteDEssai(reglages=classe(ContexteDEssai())
                              .reglages_par_defaut())
    obj = classe(contexte)
    obj.installer()
    return obj


# ---------------------------------------------------------------------------
#  Le manifeste
# ---------------------------------------------------------------------------
def test_le_manifeste_est_valide(module):
    """Un manifeste refusé, et le module n'est jamais chargé."""
    from phytoscope.api import Module
    classe = next(o for o in vars(module).values()
                  if isinstance(o, type) and issubclass(o, Module)
                  and o is not Module)
    manifeste = classe.MANIFESTE
    assert manifeste.defauts() == [], manifeste.defauts()
    assert manifeste.nom == "bonjour-monde"
    assert manifeste.capacites, "un module sans capacité ne sert à rien"


def test_le_manifeste_vise_une_api_connue(module):
    from phytoscope.api import VERSION_API, compatible
    from phytoscope.api import Module
    classe = next(o for o in vars(module).values()
                  if isinstance(o, type) and issubclass(o, Module)
                  and o is not Module)
    assert compatible(classe.MANIFESTE.api, VERSION_API)


# ---------------------------------------------------------------------------
#  Le travail
# ---------------------------------------------------------------------------
def test_analyser_rend_des_grandeurs_completes(instance):
    """Chaque grandeur doit dire ce qu'elle signifie."""
    contexte = instance.contexte
    grandeurs = instance.analyser(signal_dessai(30.0), 250.0, contexte)
    assert grandeurs, "le module n'a rien rendu sur un signal valide"
    for g in grandeurs:
        assert g.cle and g.libelle, "clé et libellé sont obligatoires"
        assert g.texte, "la valeur affichée ne doit pas être vide"
        assert len(g.sens) > 20, (
            f"« {g.cle} » n'explique pas ce qu'elle signifie — "
            "l'interface l'écrira à votre place, et cela se verra")
        assert np.isfinite(g.valeur)


def test_un_signal_vide_ne_fait_pas_lever(instance):
    """« Rien à dire » se dit par une liste vide, jamais par une exception."""
    assert instance.analyser(np.zeros(0), 250.0, instance.contexte) == []


def test_les_reglages_sont_respectes(module):
    """Un réglage à faux doit se voir dans le résultat."""
    from phytoscope.api import Module
    classe = next(o for o in vars(module).values()
                  if isinstance(o, type) and issubclass(o, Module)
                  and o is not Module)
    contexte = ContexteDEssai(reglages={"saluer": False})
    obj = classe(contexte)
    obj.installer()
    cles = {g.cle for g in obj.analyser(signal_dessai(20.0), 250.0, contexte)}
    assert "salut" not in cles
    assert "echantillons" in cles


# ---------------------------------------------------------------------------
#  Les abonnements
# ---------------------------------------------------------------------------
def test_le_module_sabonne_a_ce_quil_annonce(instance):
    from phytoscope.api import EVENEMENT_DETECTE
    assert EVENEMENT_DETECTE in instance.contexte.abonnements


def test_le_rappel_compte_les_evenements(instance):
    from phytoscope.api import EVENEMENT_DETECTE
    rappels = instance.contexte.abonnements[EVENEMENT_DETECTE]
    for i in range(5):
        for rappel in rappels:
            rappel(float(i), 1e-4)
    grandeurs = {g.cle: g for g in
                 instance.analyser(signal_dessai(20.0), 250.0, instance.contexte)}
    assert grandeurs["evenements-vus"].valeur == 5.0


def test_arreter_ne_leve_pas(instance):
    """La fermeture doit être silencieuse, même si rien ne s'est passé."""
    instance.arreter()
    assert any("au revoir" in m for m in instance.contexte.journal_ecrit)
