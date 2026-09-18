# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_dsp.py
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

"""Tests du traitement du signal.

Les tests portent sur des propriétés vérifiables analytiquement : gain d'un
filtre à une fréquence connue, continuité du filtrage par blocs, position
d'un pic spectral. On ne teste pas « que le code s'exécute » — on teste
qu'il donne le bon nombre.
"""
import math

import numpy as np
import pytest

from phytoscope.core.dsp import (Baseline, Biquad, EventDetector, RunningStats,
                                 build_chain, decimate, dominant_mains,
                                 welch_psd)

FS = 250.0


def sinus(f, n, fs=FS, amplitude=1.0):
    return amplitude * np.sin(2 * np.pi * f * np.arange(n) / fs)


class TestBiquad:
    def test_passe_bas_laisse_passer_le_continu(self):
        f = Biquad.lowpass(10.0, FS)
        y = f.process(np.ones(2000))
        assert y[-1] == pytest.approx(1.0, abs=1e-3)

    def test_passe_haut_bloque_le_continu(self):
        f = Biquad.highpass(1.0, FS)
        y = f.process(np.ones(4000))
        assert abs(y[-1]) < 1e-2

    def test_gain_a_la_coupure_vaut_moins_trois_decibels(self):
        fc = 20.0
        f = Biquad.lowpass(fc, FS)
        x = sinus(fc, 4000)
        y = f.process(x)
        gain = np.max(np.abs(y[2000:])) / np.max(np.abs(x[2000:]))
        assert gain == pytest.approx(1 / math.sqrt(2), rel=0.08)

    def test_notch_attenue_sa_frequence(self):
        f = Biquad.notch(50.0, FS, q=30)
        y = f.process(sinus(50.0, 6000))
        assert np.max(np.abs(y[4000:])) < 0.25

    def test_filtrage_par_blocs_identique_au_flux_entier(self):
        x = np.random.default_rng(3).standard_normal(1000)
        entier = Biquad.lowpass(20.0, FS).process(x)
        par_blocs = Biquad.lowpass(20.0, FS)
        morceaux = [par_blocs.process(x[i:i + 64]) for i in range(0, 1000, 64)]
        assert np.allclose(entier, np.concatenate(morceaux), atol=1e-12)


class TestChaine:
    def test_chaine_vide_si_tout_desactive(self):
        assert build_chain(FS, 0, 0, 0).cells == []

    def test_notch_ajoute_aussi_l_harmonique(self):
        # 50 Hz et 150 Hz : deux cellules, si la fréquence de Nyquist le permet
        assert len(build_chain(1000.0, 0, 0, 50.0).cells) == 2


class TestBaseline:
    def test_supprime_la_composante_continue(self):
        b = Baseline(FS, tau_s=1.0)
        y = b.process(np.full(2000, 5.0))
        assert abs(y[-1]) < 1e-3

    def test_conserve_la_variation_rapide(self):
        b = Baseline(FS, tau_s=60.0)
        x = np.full(500, 2.0)
        x[250:] += 1.0
        y = b.process(x)
        assert y[260] == pytest.approx(1.0, abs=0.05)


class TestStats:
    def test_efficace_d_un_sinus(self):
        s = RunningStats(FS, window_s=4.0)
        s.push(sinus(5.0, 1000))
        assert s.rms == pytest.approx(1 / math.sqrt(2), rel=0.05)

    def test_fenetre_glissante_bornee(self):
        s = RunningStats(FS, window_s=1.0)
        for _ in range(20):
            s.push(np.ones(100))
        assert s.view().size == s.n


class TestDetection:
    def test_detecte_une_impulsion_franche(self):
        d = EventDetector(FS, sigma=3.0, refractory_ms=100, min_amplitude_v=0.0)
        rng = np.random.default_rng(7)
        x = rng.normal(0, 1e-6, 2000)
        x[1000] = 5e-5
        evenements = d.process(x, 0)
        assert any(abs(e.index - 1000) <= 2 for e in evenements)

    def test_periode_refractaire_respectee(self):
        d = EventDetector(FS, sigma=2.0, refractory_ms=1000, min_amplitude_v=0.0)
        x = np.random.default_rng(1).normal(0, 1e-6, 1000)
        x[100] = x[110] = x[120] = 1e-4
        evenements = d.process(x, 0)
        assert len(evenements) == 1

    def test_amplitude_minimale_filtre_le_bruit(self):
        d = EventDetector(FS, sigma=1.0, refractory_ms=10,
                          min_amplitude_v=1.0)          # seuil inatteignable
        x = np.random.default_rng(1).normal(0, 1e-6, 1000)
        assert d.process(x, 0) == []


class TestSpectre:
    def test_pic_a_la_bonne_frequence(self):
        f, p = welch_psd(sinus(20.0, 4096), FS, nperseg=1024)
        assert f[int(np.argmax(p))] == pytest.approx(20.0, abs=1.0)

    def test_detection_du_reseau(self):
        x = sinus(50.0, 8192, amplitude=1.0) + \
            np.random.default_rng(2).normal(0, 0.01, 8192)
        assert dominant_mains(x, FS) == 50.0

    def test_pas_de_reseau_dans_du_bruit_blanc(self):
        x = np.random.default_rng(4).normal(0, 1.0, 8192)
        assert dominant_mains(x, FS) is None


class TestDecimation:
    def test_conserve_la_moyenne(self):
        x = np.arange(100, dtype=float)
        assert decimate(x, 10).mean() == pytest.approx(x.mean(), rel=1e-9)

    def test_facteur_un_ne_change_rien(self):
        x = np.arange(10, dtype=float)
        assert np.array_equal(decimate(x, 1), x)
