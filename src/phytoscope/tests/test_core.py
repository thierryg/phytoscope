# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_core.py
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

"""Tests des réglages, de l'échantillonnage, de l'analyse et des sources."""
import os
import queue
import tempfile
import time

import numpy as np
import pytest

from phytoscope.config import Settings
from phytoscope.core import analysis, preflight
from phytoscope.core.sampling import Sampler, window, window_gains
from phytoscope.core.sources import FileSource, SimulatedSource


class TestSettings:
    def test_aller_retour_json(self):
        s = Settings()
        s.music.scale = "hirajoshi"
        s.music.diapason_hz = 432.0
        s.processing.notch_hz = 60.0
        with tempfile.TemporaryDirectory() as d:
            chemin = os.path.join(d, "r.json")
            s.save(chemin)
            relu = Settings.load(chemin)
        assert relu.music.scale == "hirajoshi"
        assert relu.music.diapason_hz == 432.0
        assert relu.processing.notch_hz == 60.0

    def test_fichier_corrompu_ne_bloque_pas(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = os.path.join(d, "r.json")
            open(chemin, "w").write("{ceci n'est pas du json")
            assert Settings.load(chemin).music.scale  # valeurs par défaut

    def test_sections_presentes(self):
        s = Settings()
        for section in ("acquisition", "sampling", "processing", "music",
                        "audio_out", "recording", "logging", "diagnostics", "ui"):
            assert hasattr(s, section)


class TestOptionsDeSeance:
    """Une option de ligne de commande vaut pour la séance, pas pour toujours.

    Le piège que ces tests ferment : lancer une fois « --simulation » pour une
    démonstration, et découvrir six mois plus tard que le logiciel n'ouvre plus
    jamais la carte. Ou lancer « --lang ko » pour un essai, et retrouver son
    interface en coréen au démarrage suivant.
    """

    def _fichier(self, d):
        chemin = os.path.join(d, "r.json")
        depart = Settings()
        depart.ui.language = "fr"
        depart.acquisition.source = "auto"
        depart.save(chemin)
        return chemin

    def test_une_valeur_imposee_ne_sécrit_pas(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = self._fichier(d)
            s = Settings.load(chemin)
            s.forcer("ui", "language", "ko")
            s.forcer("acquisition", "source", "simulation")
            assert s.ui.language == "ko"          # pendant la séance
            assert s.acquisition.source == "simulation"
            s.save(chemin)
            relu = Settings.load(chemin)
            assert relu.ui.language == "fr"       # sur le disque, rien n'a bougé
            assert relu.acquisition.source == "auto"

    def test_le_choix_de_lutilisateur_lemporte(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = self._fichier(d)
            s = Settings.load(chemin)
            s.forcer("ui", "language", "ko")
            s.ui.language = "ja"                  # changé dans l'interface
            s.save(chemin)
            assert Settings.load(chemin).ui.language == "ja"

    def test_deux_impositions_successives(self):
        with tempfile.TemporaryDirectory() as d:
            chemin = self._fichier(d)
            s = Settings.load(chemin)
            s.forcer("ui", "language", "ko")
            s.forcer("ui", "language", "ar")      # p. ex. langue inconnue → repli
            s.save(chemin)
            assert Settings.load(chemin).ui.language == "fr"

    def test_champ_inconnu_ignoré(self):
        s = Settings()
        s.forcer("ui", "champ_qui_nexiste_pas", 1)
        s.forcer("section_absente", "theme", 1)   # ne doit rien lever

    def test_letat_en_memoire_reste_complet(self):
        #  to_dict() sans argument décrit la séance telle qu'elle tourne :
        #  c'est ce qui est consigné dans seance.json.
        s = Settings()
        s.forcer("acquisition", "source", "simulation")
        assert s.to_dict()["acquisition"]["source"] == "simulation"
        assert s.to_dict(persistant=True)["acquisition"]["source"] == "auto"


class TestFenetres:
    def test_gain_coherent_du_rectangle(self):
        c, n = window_gains("rectangle", 1024)
        assert c == pytest.approx(1.0)
        assert n == pytest.approx(1.0)

    def test_hann_attenue_de_moitie(self):
        c, _ = window_gains("hann", 1024)
        assert c == pytest.approx(0.5, abs=0.01)

    def test_toutes_les_fenetres_positives_au_centre(self):
        for nom in ("rectangle", "hann", "hamming", "blackman", "flattop"):
            w = window(nom, 256)
            assert w[128] > 0.5, nom


class TestSampler:
    def test_mode_continu_ne_produit_pas_de_bloc(self):
        s = Settings()
        s.sampling.mode = "continu"
        ech = Sampler(s)
        ech.feed(0, np.zeros(1000))
        assert ech.blocks_kept == 0

    def test_mode_bloc_decoupe(self):
        s = Settings()
        s.sampling.mode = "bloc"
        s.sampling.block_samples = 128
        s.sampling.window = "rectangle"
        recus = []
        ech = Sampler(s)
        ech.on_block = recus.append
        ech.feed(0, np.arange(512, dtype=float))
        assert len(recus) == 4
        assert recus[0].data.size == 128

    def test_decimation_reduit_la_cadence(self):
        s = Settings()
        s.sampling.mode = "bloc"
        s.sampling.block_samples = 64
        s.sampling.decimation = 4
        s.sampling.window = "rectangle"
        recus = []
        ech = Sampler(s)
        ech.on_block = recus.append
        ech.feed(0, np.ones(1024))
        assert len(recus) == 4                      # 1024 / 4 / 64
        assert recus[0].sample_rate == pytest.approx(
            s.acquisition.sample_rate / 4)


class TestAnalyse:
    def test_derive_mesuree(self):
        fs = 250.0
        t = np.arange(int(fs * 60)) / fs
        x = 1e-6 * t                                 # 1 µV par seconde
        d = analysis.derive(x, fs)
        assert d.pente_uv_par_min == pytest.approx(60.0, rel=0.01)
        assert d.r2 > 0.999
        assert d.significative()

    def test_spectre_en_v_par_racine_de_hertz(self):
        fs, n = 1000.0, 8192
        x = np.random.default_rng(5).normal(0, 1e-6, n)
        sp = analysis.spectre(x, fs)
        plancher = sp.plancher(50, 400)
        attendu = 1e-6 * np.sqrt(2.0 / fs)
        assert plancher == pytest.approx(attendu, rel=0.3)

    def test_allan_decroit_pour_du_bruit_blanc(self):
        fs = 100.0
        x = np.random.default_rng(6).normal(0, 1.0, 20000)
        res = analysis.allan_deviation(x, fs)
        assert res.pente < -0.3

    def test_statistiques_evenements(self):
        temps = list(range(0, 600, 10))              # parfaitement régulier
        st = analysis.statistiques_evenements(temps, duree_s=600)
        assert st.n == 60
        assert st.cv < 0.1                           # très régulier

    def test_rapport_complet_produit_du_texte(self):
        x = np.random.default_rng(8).normal(0, 1e-6, 5000)
        rapport = analysis.rapport_complet(x, 250.0)
        assert "RAPPORT DE MESURE" in rapport
        assert "AVERTISSEMENT" in rapport


class TestSources:
    def test_generateur_interne_produit_des_blocs(self):
        f = queue.Queue(maxsize=64)
        src = SimulatedSource(f, sample_rate=250.0, realtime=False)
        src.start()
        time.sleep(0.25)
        src.stop()
        assert not f.empty()
        index, bloc = f.get()
        assert bloc.ndim == 2
        assert np.isfinite(bloc).all()

    def test_relecture_de_fichier(self):
        f = queue.Queue(maxsize=256)
        donnees = np.linspace(0, 1, 500).reshape(-1, 1)
        src = FileSource(f, donnees, 250.0, speed=100.0)
        src.start()
        time.sleep(0.5)
        src.stop()
        assert f.qsize() > 0


class TestPreflight:
    def test_analyse_une_bibliotheque_connue(self):
        lib, paquet, cmd = preflight.analyser_import_casse(
            "libGL.so.1: cannot open shared object file")
        assert lib.startswith("lib")

    def test_rapport_complet(self):
        r = preflight.run()
        assert r.python_version
        assert len(r.resultats) == len(preflight.REQUIREMENTS)
        assert isinstance(r.peut_demarrer, bool)

    def test_environnement_detecte(self):
        env = preflight.inspecter_environnement()
        assert env.executable
        assert env.version
