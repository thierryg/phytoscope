# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_features.py
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

"""Tests des descripteurs avancés : FFT, ondelettes, MFCC, LPC, cepstre.

Chaque test construit un signal **dont on connaît la réponse** — une sinusoïde
à 2 Hz, un train d'impulsions de période connue, un processus autorégressif
d'ordre deux — et vérifie que l'outil la retrouve. C'est la seule façon de
tester une transformée : comparer à une vérité, pas à une sortie de référence
que personne n'a vérifiée.
"""
import math

import numpy as np
import pytest

from phytoscope.core.features import (DESCRIPTEURS, banc_de_mel, cepstre, lpc,
                                      mfcc, ondelettes_morlet,
                                      spectre_instantane)

FS = 250.0


def sinus(f, duree=8.0, fs=FS, amplitude=1.0, phase=0.0):
    t = np.arange(int(duree * fs)) / fs
    return amplitude * np.sin(2 * np.pi * f * t + phase)


class TestSpectre:
    def test_retrouve_la_frequence(self):
        s = spectre_instantane(sinus(5.0), FS)
        assert s.pic_hz == pytest.approx(5.0, abs=0.2)

    def test_retrouve_l_amplitude(self):
        #  La correction de gain de fenêtre est le point délicat : sans elle,
        #  une fenêtre de Hann divise l'amplitude lue par deux.
        s = spectre_instantane(sinus(5.0, amplitude=3.0), FS)
        assert s.pic_amplitude == pytest.approx(3.0, rel=0.05)

    def test_resolution_vaut_l_inverse_de_la_duree(self):
        s = spectre_instantane(sinus(5.0, duree=10.0), FS)
        assert s.resolution_hz == pytest.approx(0.1, rel=0.01)

    def test_bourrage_n_ajoute_pas_de_resolution(self):
        court = spectre_instantane(sinus(5.0, duree=4.0), FS, zero_padding=1)
        long = spectre_instantane(sinus(5.0, duree=4.0), FS, zero_padding=4)
        assert long.frequences_hz.size > court.frequences_hz.size
        assert long.resolution_hz == pytest.approx(court.resolution_hz)

    def test_signal_vide_ne_leve_rien(self):
        s = spectre_instantane(np.zeros(0), FS)
        assert s.amplitude.size == 0
        assert math.isnan(s.pic_hz)


class TestOndelettes:
    def test_la_crete_suit_la_frequence(self):
        s = ondelettes_morlet(sinus(3.0, duree=20.0), FS, n_echelles=40,
                              decimation=10)
        crete = s.ridge()
        assert np.median(crete) == pytest.approx(3.0, rel=0.15)

    def test_situe_une_bouffee_dans_le_temps(self):
        #  Vingt secondes de silence, une bouffée de 2 s au milieu : la FFT la
        #  noierait, l'ondelette doit la placer.
        x = np.zeros(int(20 * FS))
        debut = int(9 * FS)
        x[debut:debut + int(2 * FS)] = sinus(6.0, duree=2.0)
        s = ondelettes_morlet(x, FS, n_echelles=32, decimation=5)
        i, j = np.unravel_index(int(np.argmax(s.module)), s.module.shape)
        assert s.temps_s[j] == pytest.approx(10.0, abs=1.5)
        assert s.frequences_hz[i] == pytest.approx(6.0, rel=0.3)

    def test_decimation_reduit_la_largeur(self):
        x = sinus(2.0, duree=12.0)
        plein = ondelettes_morlet(x, FS, n_echelles=16)
        reduit = ondelettes_morlet(x, FS, n_echelles=16, decimation=10)
        assert reduit.module.shape[1] == pytest.approx(plein.module.shape[1] / 10,
                                                       rel=0.05)

    def test_signal_trop_court(self):
        s = ondelettes_morlet(np.zeros(4), FS)
        assert s.module.size == 0


class TestMel:
    def test_banc_couvre_la_bande(self):
        banc = banc_de_mel(20, 1024, FS)
        assert banc.shape == (20, 513)
        assert banc.sum() > 0

    def test_filtres_positifs_et_bornes(self):
        banc = banc_de_mel(12, 512, FS)
        assert banc.min() >= 0.0
        assert banc.max() <= 1.0 + 1e-9


class TestMFCC:
    def test_forme_des_coefficients(self):
        s = mfcc(sinus(4.0, duree=60.0), FS, n_coef=13, fenetre_s=8.0)
        assert s.coefficients.shape[1] == 13
        assert s.coefficients.shape[0] == s.temps_s.size
        assert s.delta.shape == s.coefficients.shape

    def test_deux_signaux_identiques_donnent_les_memes_coefficients(self):
        a = mfcc(sinus(4.0, duree=40.0), FS).moyenne()
        b = mfcc(sinus(4.0, duree=40.0), FS).moyenne()
        assert np.allclose(a, b)

    def test_deux_signaux_differents_se_distinguent(self):
        grave = mfcc(sinus(0.5, duree=40.0), FS).moyenne()
        aigu = mfcc(sinus(20.0, duree=40.0), FS).moyenne()
        assert not np.allclose(grave, aigu, atol=1e-3)

    def test_signal_plus_court_qu_une_trame(self):
        s = mfcc(sinus(4.0, duree=2.0), FS, fenetre_s=8.0)
        assert s.coefficients.shape[0] == 1


class TestLPC:
    def test_modele_stable_sur_du_bruit(self):
        rng = np.random.default_rng(20260917)
        s = lpc(rng.normal(size=4000), FS, ordre=8)
        assert s.ordre == 8
        assert s.erreur_residuelle > 0
        assert s.enveloppe_db.size == 512

    def test_retrouve_une_resonance(self):
        #  Processus autorégressif d'ordre 2 : un pôle à 10 Hz, module 0,97.
        rng = np.random.default_rng(7)
        f0, r = 10.0, 0.97
        theta = 2 * np.pi * f0 / FS
        a1, a2 = -2 * r * math.cos(theta), r * r
        n = 8000
        x = np.zeros(n)
        bruit = rng.normal(size=n)
        for i in range(2, n):
            x[i] = -a1 * x[i - 1] - a2 * x[i - 2] + bruit[i]
        s = lpc(x, FS, ordre=6)
        assert s.formants_hz.size >= 1
        assert min(abs(s.formants_hz - f0)) < 1.5

    def test_bruit_blanc_predit_mal(self):
        rng = np.random.default_rng(3)
        blanc = lpc(rng.normal(size=6000), FS, ordre=10)
        assert blanc.gain_prediction_db < 3.0

    def test_signal_trop_court(self):
        s = lpc(np.zeros(4), FS)
        assert s.ordre == 0


class TestCepstre:
    def test_retrouve_une_periode(self):
        #  Train d'impulsions toutes les 2 s : le cepstre doit voir 2 s.
        n = int(60 * FS)
        x = np.zeros(n)
        x[::int(2.0 * FS)] = 1.0
        s = cepstre(x, FS)
        assert s.periode_detectee_s == pytest.approx(2.0, abs=0.1)
        assert s.frequence_detectee_hz == pytest.approx(0.5, abs=0.03)

    def test_bornes_respectees(self):
        n = int(40 * FS)
        x = np.zeros(n)
        x[::int(1.0 * FS)] = 1.0
        s = cepstre(x, FS, q_min_s=3.0, q_max_s=6.0)
        assert 3.0 <= s.pic_quefrence_s <= 6.0

    def test_signal_trop_court(self):
        s = cepstre(np.zeros(8), FS)
        assert s.cepstre.size == 0


class TestTableDesDescripteurs:
    def test_six_entrees_completes(self):
        assert len(DESCRIPTEURS) == 6
        for cle, valeur in DESCRIPTEURS.items():
            titre, resume, avertissement = valeur
            assert titre and resume and avertissement, cle
