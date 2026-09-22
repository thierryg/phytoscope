# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_quantities.py
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

"""Les grandeurs scientifiques doivent être justes, pas seulement plausibles.

Un chiffre affiché dans un multimètre est cru sur parole. Ces essais vérifient
donc les valeurs contre la physique — un bruit blanc d'amplitude connue doit
donner la densité qu'on calcule au crayon, et la résistance qui va avec.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from phytoscope.core import quantities as gr


def _bruit_blanc(rms_v: float, fs: float = 250.0, duree_s: float = 120.0,
                 graine: int = 0) -> np.ndarray:
    return np.random.default_rng(graine).normal(0.0, rms_v, int(duree_s * fs))


def test_signal_trop_court_ne_produit_rien():
    g = gr.mesurer(np.zeros(10), 250.0)
    assert len(g) == 0
    assert g.to_dict() == {}


def test_densite_de_bruit_conforme_au_calcul():
    """Un bruit blanc de 2 µV eff. sur 125 Hz de bande fait 179 nV/√Hz."""
    fs = 250.0
    x = _bruit_blanc(2e-6, fs)
    attendu = 2e-6 / math.sqrt(fs / 2)
    mesure = gr.mesurer(x, fs).get("plancher").valeur
    assert mesure == pytest.approx(attendu, rel=0.10)


def test_resistance_equivalente_suit_johnson_nyquist():
    """R = Sv / 4kT, vérifié sur un bruit dont on connaît la densité."""
    fs = 250.0
    rms = 2e-6
    densite = rms / math.sqrt(fs / 2)
    attendu = densite ** 2 / (4 * gr.BOLTZMANN * gr.TEMPERATURE_K)
    mesure = gr.mesurer(_bruit_blanc(rms, fs), fs).get("resistance").valeur
    assert mesure == pytest.approx(attendu, rel=0.25)
    assert 1e5 < mesure < 1e8          # l'ordre de grandeur d'un tissu végétal


def test_resistance_croit_avec_le_bruit():
    """Un contact qui sèche : le bruit monte, le majorant doit suivre en R²."""
    fs = 250.0
    faible = gr.mesurer(_bruit_blanc(1e-6, fs, graine=1), fs).get("resistance").valeur
    fort = gr.mesurer(_bruit_blanc(10e-6, fs, graine=1), fs).get("resistance").valeur
    assert fort / faible == pytest.approx(100.0, rel=0.3)


def test_le_reseau_est_vu_et_signale():
    fs = 250.0
    t = np.arange(int(120 * fs)) / fs
    propre = _bruit_blanc(2e-6, fs, graine=3)
    sale = propre + 50e-6 * np.sin(2 * np.pi * 50.0 * t)
    sans = gr.mesurer(propre, fs, reseau_hz=50.0).get("reseau")
    avec = gr.mesurer(sale, fs, reseau_hz=50.0).get("reseau")
    assert avec.valeur > sans.valeur + 20.0
    assert avec.alerte and not sans.alerte


def test_marge_de_saturation_et_alerte():
    fs = 250.0
    x = _bruit_blanc(1e-6, fs, graine=4)
    assert gr.mesurer(x, fs, pleine_echelle_v=2.5).get("marge").valeur > 99.0
    serre = gr.mesurer(x + 0.0, fs, pleine_echelle_v=3e-6).get("marge")
    assert serre.valeur < 10.0 and serre.alerte


def test_normalite_distingue_gaussien_et_impulsionnel():
    fs = 250.0
    gauss = gr.mesurer(_bruit_blanc(2e-6, fs, graine=5), fs).get("normalite")
    x = _bruit_blanc(2e-6, fs, graine=5).copy()
    x[::500] += 2e-4                        # de fortes impulsions régulières
    impulsif = gr.mesurer(x, fs).get("normalite")
    assert gauss.valeur > 0.05 and not gauss.alerte
    assert impulsif.valeur < 0.05 and impulsif.alerte


def test_facteur_de_crete_du_bruit_gaussien():
    """Autour de 4 pour du gaussien sur 30 000 points."""
    facteur = gr.mesurer(_bruit_blanc(2e-6, graine=6), 250.0).get("crete").valeur
    assert 3.0 < facteur < 6.0


def test_fano_tu_quand_les_evenements_sont_trop_rares():
    g = gr.mesurer(_bruit_blanc(2e-6, graine=7), 250.0,
                   evenements_s=[1.0, 20.0, 60.0])
    fano = g.get("fano")
    assert fano.texte == "— (n = 3)" and fano.valeur == 0.0
    assert g.get("cv") is None               # pas de statistique sans données
    g2 = gr.mesurer(_bruit_blanc(2e-6, graine=7), 250.0,
                    evenements_s=list(np.arange(1.0, 120.0, 5.0)))
    assert g2.get("cv") is not None
    assert g2.get("evenements").valeur > 0


def test_chaque_grandeur_est_documentee_et_mise_en_forme():
    """Aucun nombre ne doit s'afficher sans dire ce qu'il veut dire."""
    g = gr.mesurer(_bruit_blanc(2e-6, graine=8), 250.0,
                   evenements_s=list(np.arange(1.0, 120.0, 4.0)))
    assert len(g) >= 14
    cles = set(g.to_dict())
    for attendue in ("plancher", "resistance", "reseau", "crete", "pente",
                     "correlation", "normalite", "bits", "marge"):
        assert attendue in cles
    for item in g:
        assert item.libelle and item.texte and len(item.sens) > 40
        assert math.isfinite(item.valeur)


def test_resistance_annoncee_comme_majorant():
    """La déontologie du projet : ce nombre ne doit pas se faire passer pour
    une mesure d'impédance."""
    g = gr.mesurer(_bruit_blanc(2e-6, graine=9), 250.0)
    sens = g.get("resistance").sens
    assert "MAJORANT" in sens
    assert "Johnson" in sens


def test_la_colonne_valeur_ne_contient_aucun_mot_a_traduire():
    """La valeur affichée doit être lisible dans les onze langues.

    Un chiffre suivi de « au-dessus du plancher » resterait en français dans
    l'interface japonaise : les mots appartiennent à la colonne d'à côté, la
    valeur ne porte que des symboles d'unité, qui sont internationaux.
    """
    autorises = {"µV", "nV", "mV", "V", "Ω", "kΩ", "MΩ", "GΩ", "dB", "Hz",
                 "√Hz", "nV/√Hz", "dB/dec", "µV/min", "ms", "s", "min", "%",
                 "bits", "RMS", "p", "n", "/min", "—", "=", "→", "(", ")"}
    g = gr.mesurer(_bruit_blanc(2e-6, graine=12), 250.0,
                   evenements_s=list(np.arange(1.0, 120.0, 4.0)))
    for item in g:
        for mot in item.texte.replace("(", " ").replace(")", " ").split():
            propre = mot.strip("()=")
            if not propre or propre in autorises:
                continue
            #  Un nombre, éventuellement signé, reste évidemment permis.
            assert propre.replace("+", "").replace("-", "").replace(".", "") \
                .replace(",", "").isdigit(), f"{item.cle} : « {mot} » à traduire"
