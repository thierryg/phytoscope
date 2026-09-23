# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_quantities.py
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

"""Les grandeurs scientifiques doivent être justes, pas seulement plausibles.

Un chiffre affiché dans un multimètre est cru sur parole. Ces essais vérifient
donc les values contre la physique — un bruit blanc d'amplitude connue doit
donner la densité qu'on calcule au crayon, et la résistance qui va avec.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from phytoscope.core import quantities as gr


def _bruit_blanc(rms_v: float, fs: float = 250.0, duration_s: float = 120.0,
                 graine: int = 0) -> np.ndarray:
    return np.random.default_rng(graine).normal(0.0, rms_v, int(duration_s * fs))


def test_signal_trop_court_ne_produit_rien():
    g = gr.measure(np.zeros(10), 250.0)
    assert len(g) == 0
    assert g.to_dict() == {}


def test_densite_de_bruit_conforme_au_calcul():
    """Un bruit blanc de 2 µV eff. sur 125 Hz de bande fait 179 nV/√Hz."""
    fs = 250.0
    x = _bruit_blanc(2e-6, fs)
    attendu = 2e-6 / math.sqrt(fs / 2)
    mesure = gr.measure(x, fs).get("plancher").value
    assert mesure == pytest.approx(attendu, rel=0.10)


def test_resistance_equivalente_suit_johnson_nyquist():
    """R = Sv / 4kT, vérifié sur un bruit dont on connaît la densité."""
    fs = 250.0
    rms = 2e-6
    densite = rms / math.sqrt(fs / 2)
    attendu = densite ** 2 / (4 * gr.BOLTZMANN * gr.TEMPERATURE_K)
    mesure = gr.measure(_bruit_blanc(rms, fs), fs).get("resistance").value
    assert mesure == pytest.approx(attendu, rel=0.25)
    assert 1e5 < mesure < 1e8          # l'order de grandeur d'un tissu végétal


def test_resistance_croit_avec_le_bruit():
    """Un contact qui sèche : le bruit monte, le majorant doit suivre en R²."""
    fs = 250.0
    faible = gr.measure(_bruit_blanc(1e-6, fs, graine=1), fs).get("resistance").value
    fort = gr.measure(_bruit_blanc(10e-6, fs, graine=1), fs).get("resistance").value
    assert fort / faible == pytest.approx(100.0, rel=0.3)


def test_le_reseau_est_vu_et_signale():
    fs = 250.0
    t = np.arange(int(120 * fs)) / fs
    propre = _bruit_blanc(2e-6, fs, graine=3)
    sale = propre + 50e-6 * np.sin(2 * np.pi * 50.0 * t)
    sans = gr.measure(propre, fs, mains_hz=50.0).get("reseau")
    avec = gr.measure(sale, fs, mains_hz=50.0).get("reseau")
    assert avec.value > sans.value + 20.0
    assert avec.alert and not sans.alert


def test_marge_de_saturation_et_alerte():
    fs = 250.0
    x = _bruit_blanc(1e-6, fs, graine=4)
    assert gr.measure(x, fs, full_scale_v=2.5).get("marge").value > 99.0
    serre = gr.measure(x + 0.0, fs, full_scale_v=3e-6).get("marge")
    assert serre.value < 10.0 and serre.alert


def test_normalite_distingue_gaussien_et_impulsionnel():
    fs = 250.0
    gauss = gr.measure(_bruit_blanc(2e-6, fs, graine=5), fs).get("normalite")
    x = _bruit_blanc(2e-6, fs, graine=5).copy()
    x[::500] += 2e-4                        # de fortes impulsions régulières
    impulsif = gr.measure(x, fs).get("normalite")
    assert gauss.value > 0.05 and not gauss.alert
    assert impulsif.value < 0.05 and impulsif.alert


def test_facteur_de_crete_du_bruit_gaussien():
    """Autour de 4 pour du gaussien sur 30 000 points."""
    facteur = gr.measure(_bruit_blanc(2e-6, graine=6), 250.0).get("crete").value
    assert 3.0 < facteur < 6.0


def test_fano_tu_quand_les_evenements_sont_trop_rares():
    g = gr.measure(_bruit_blanc(2e-6, graine=7), 250.0,
                   event_times_s=[1.0, 20.0, 60.0])
    fano = g.get("fano")
    assert fano.text == "— (n = 3)" and fano.value == 0.0
    assert g.get("cv") is None               # pas de statistique sans données
    g2 = gr.measure(_bruit_blanc(2e-6, graine=7), 250.0,
                    event_times_s=list(np.arange(1.0, 120.0, 5.0)))
    assert g2.get("cv") is not None
    assert g2.get("events").value > 0


def test_chaque_grandeur_est_documentee_et_mise_en_forme():
    """Aucun nombre ne doit s'afficher sans dire ce qu'il veut dire."""
    g = gr.measure(_bruit_blanc(2e-6, graine=8), 250.0,
                   event_times_s=list(np.arange(1.0, 120.0, 4.0)))
    assert len(g) >= 14
    cles = set(g.to_dict())
    for attendue in ("plancher", "resistance", "reseau", "crete", "pente",
                     "correlation", "normalite", "bits", "marge"):
        assert attendue in cles
    for item in g:
        assert item.label and item.text and len(item.meaning) > 40
        assert math.isfinite(item.value)


def test_resistance_annoncee_comme_majorant():
    """La déontologie du projet : ce nombre ne doit pas se faire passer pour
    une mesure d'impédance."""
    g = gr.measure(_bruit_blanc(2e-6, graine=9), 250.0)
    meaning = g.get("resistance").meaning
    assert "UPPER BOUND" in meaning
    assert "Johnson" in meaning


def test_la_colonne_valeur_ne_contient_aucun_mot_a_traduire():
    """La value affichée doit être lisible dans les onze langues.

    Un chiffre suivi de « au-dessus du plancher » resterait en français dans
    l'interface japonaise : les mots appartiennent à la colonne d'à côté, la
    value ne porte que des symboles d'unité, qui sont internationaux.
    """
    autorises = {"µV", "nV", "mV", "V", "Ω", "kΩ", "MΩ", "GΩ", "dB", "Hz",
                 "√Hz", "nV/√Hz", "dB/dec", "µV/min", "ms", "s", "min", "%",
                 "bits", "RMS", "p", "n", "/min", "—", "=", "→", "(", ")"}
    g = gr.measure(_bruit_blanc(2e-6, graine=12), 250.0,
                   event_times_s=list(np.arange(1.0, 120.0, 4.0)))
    for item in g:
        for mot in item.text.replace("(", " ").replace(")", " ").split():
            propre = mot.strip("()=")
            if not propre or propre in autorises:
                continue
            #  Un nombre, éventuellement signé, reste évidemment permis.
            assert propre.replace("+", "").replace("-", "").replace(".", "") \
                .replace(",", "").isdigit(), f"{item.key} : « {mot} » à translate"
