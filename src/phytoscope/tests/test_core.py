# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_core.py
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
        lib, paquet, cmd, presente = preflight.analyser_import_casse(
            "libGL.so.1: cannot open shared object file")
        assert lib.startswith("lib")
        #  Si le système a la bibliothèque, il n'y a rien à installer : c'est
        #  l'interpréteur qui ne l'atteint pas. Les deux cas sont légitimes
        #  selon la machine qui exécute les tests, mais ils s'excluent.
        assert presente != bool(cmd)

    def test_bibliotheque_presente_ne_propose_aucun_paquet(self):
        """Ne jamais conseiller d'installer un paquet déjà présent.

        Le défaut a existé : sur une machine où `python3` est celui de
        Homebrew, l'interpréteur ne voit pas /lib/x86_64-linux-gnu et le
        bilan de démarrage conseillait « sudo apt install libgl1 » alors que
        libgl1 était installé.
        """
        import phytoscope.core.preflight as pf
        reel = pf.presente_sur_le_systeme
        pf.presente_sur_le_systeme = lambda nom: "/lib/x86_64-linux-gnu/" + nom
        try:
            lib, paquet, cmd, presente = pf.analyser_import_casse(
                "libGL.so.1: cannot open shared object file")
        finally:
            pf.presente_sur_le_systeme = reel
        assert presente is True
        assert paquet == "" and cmd == ""

    def test_interpreteur_du_systeme_nest_pas_etranger(self):
        import sys as _sys
        if _sys.executable.startswith(("/usr/", "/bin/")) or "/.venv/" in _sys.executable:
            assert preflight.interpreteur_etranger() == ""

    def test_rapport_complet(self):
        r = preflight.run()
        assert r.python_version
        assert len(r.resultats) == len(preflight.REQUIREMENTS)
        assert isinstance(r.peut_demarrer, bool)

    def test_environnement_detecte(self):
        env = preflight.inspecter_environnement()
        assert env.executable
        assert env.version

class TestCaptureTrames:
    """Démarrer une capture, dans les trois formats.

    Le défaut que ces tests ferment : `FrameCapture.start()` testait un nom
    `mode` qui n'existait plus depuis une refonte, et levait donc NameError
    dès qu'on démarrait une capture — dans les trois formats. Aucun test ne
    démarrait de capture, et le mode mise au point était ainsi cassé sans
    que rien ne le dise. Trouvé par ruff (F821) le 2026-09-18.
    """

    def _reglages(self, tmp_path, format_):
        from phytoscope.config import Settings
        s = Settings()
        s.diagnostics.capture_format = format_
        #  On détourne le répertoire de capture : un test n'écrit jamais dans
        #  les dossiers de qui l'exécute.
        s.capture_dir = lambda: str(tmp_path)
        return s

    @pytest.mark.parametrize("format_,attendu", [
        ("texte", True),
        ("hexa", True),
        ("binaire", False),
    ])
    def test_demarrage_dans_les_trois_formats(self, tmp_path, format_, attendu):
        from phytoscope.core.usbdiag import FrameCapture
        capture = FrameCapture(self._reglages(tmp_path, format_))
        chemin = capture.start()
        try:
            assert chemin, f"la capture {format_} n'a pas démarré"
            assert capture.active
            assert os.path.exists(chemin)
        finally:
            capture.stop()

        #  L'en-tête est du texte : il n'a de sens que hors du format binaire.
        with open(chemin, "rb") as f:
            debut = f.read(200)
        assert debut.startswith(b"#") is attendu

    def test_le_format_binaire_ne_recoit_pas_d_entete_texte(self, tmp_path):
        from phytoscope.core.usbdiag import FrameCapture
        capture = FrameCapture(self._reglages(tmp_path, "binaire"))
        chemin = capture.start()
        try:
            assert chemin and chemin.endswith(".bin")
        finally:
            capture.stop()
        assert os.path.getsize(chemin) == 0


class TestMajDependances:
    """La vérification des mises à jour — sans toucher au réseau.

    Aucun test n'interroge PyPI : une suite qui dépend d'un index distant
    échoue dans un train, et ment sur ce qu'elle vérifie. L'accès réseau est
    donc remplacé partout où il apparaît.
    """

    # -- comparaison de versions -------------------------------------------
    @pytest.mark.parametrize("a,b,attendu", [
        ("2.2.6", "2.3.0", -1),
        ("2.3.0", "2.2.6", 1),
        ("6.11.2", "6.11.2", 0),
        ("1.26", "1.26.0", 0),          # « 1.26 » et « 1.26.0 » sont la même
        ("1.9.0", "1.10.0", -1),        # 10 > 9, et non l'ordre lexical
        ("1.5.8", "1.5.10", -1),
        #  Le piège que le comparateur referme : ramasser tous les nombres de
        #  « 3.0.0rc1 » donne (3,0,0,1), qui se compare APRÈS (3,0,0).
        ("3.0.0rc1", "3.0.0", -1),
        ("3.0.0", "3.0.0rc1", 1),
        ("2.0.0a1", "2.0.0", -1),
        ("2.0.0b2", "2.0.0a1", 1),      # beta après alpha
        ("2.0.0rc2", "2.0.0rc1", 1),
        ("2.0.0.dev3", "2.0.0a1", -1),  # développement avant tout
        ("1.26.0.post1", "1.26.0", 1),  # post-diffusion après
        ("1.2.3+local", "1.2.3", 0),    # la partie locale n'ordonne pas
        ("", "1.0", -1),
    ])
    def test_comparaison(self, a, b, attendu):
        from phytoscope.core import dependency_updates as M
        assert M.comparer_versions(a, b) == attendu

    @pytest.mark.parametrize("installee,disponible,attendu", [
        ("2.2.6", "3.0.0", "majeure"),
        ("2.2.6", "2.3.0", "mineure"),
        ("2.2.6", "2.2.9", "correctif"),
        ("2.2.6", "2.2.6", ""),
        ("2.3.0", "2.2.6", ""),         # plus récent que l'index : rien à dire
    ])
    def test_ampleur(self, installee, disponible, attendu):
        from phytoscope.core import dependency_updates as M
        assert M.ampleur(installee, disponible) == attendu

    # -- lecture des exigences ---------------------------------------------
    def test_lecture_des_exigences(self, tmp_path):
        from phytoscope.core import dependency_updates as M
        fichier = tmp_path / "requirements.txt"
        fichier.write_text(
            "# un commentaire\n"
            "\n"
            "numpy>=1.24            # tout le traitement du signal\n"
            "PySide6>=6.5\n"
            "pyserial>=3.5 ; sys_platform != 'emscripten'\n"
            "python-rtmidi\n"
            "-r autre.txt\n"
            "--index-url https://exemple\n", encoding="utf-8")
        e = M.lire_exigences(str(fichier))
        assert e == {"numpy": ">=1.24", "pyside6": ">=6.5",
                     "pyserial": ">=3.5", "python-rtmidi": ""}

    def test_fichier_absent_ne_leve_rien(self, tmp_path):
        from phytoscope.core import dependency_updates as M
        assert M.lire_exigences(str(tmp_path / "absent.txt")) == {}

    # -- état d'une dépendance ---------------------------------------------
    def test_etats(self):
        from phytoscope.core import dependency_updates as M
        assert M.Dependance("numpy", installee="", disponible="2.0").etat == "missing"
        assert M.Dependance("numpy", installee="1.0", disponible="").etat == "inconnue"
        assert M.Dependance("numpy", installee="1.0", disponible="1.0").etat == "a_jour"
        assert M.Dependance("numpy", installee="1.0", disponible="2.0").etat == "majeure"
        assert M.Dependance("numpy", installee="1.0", disponible="1.0").a_jour

    # -- la vérification, réseau remplacé ----------------------------------
    def _sans_reseau(self, monkeypatch, reponses):
        """Remplace l'interrogation de l'index par une table."""
        from phytoscope.core import dependency_updates as M
        monkeypatch.setattr(
            M, "derniere_version",
            lambda dist, delai=0, index="": reponses.get(dist, ("", "absent du bouchon")))
        monkeypatch.setattr(M, "version_installee", lambda dist: "1.0.0")
        return M

    def test_verification_trouve_une_mise_a_jour(self, monkeypatch):
        M = self._sans_reseau(monkeypatch, {"numpy": ("2.0.0", "")})
        r = M.verifier(distributions=["numpy"])
        assert len(r.dependances) == 1
        assert r.a_mettre_a_jour and r.a_mettre_a_jour[0].ampleur == "majeure"
        assert not r.hors_ligne

    def test_verification_tout_a_jour(self, monkeypatch):
        M = self._sans_reseau(monkeypatch, {"numpy": ("1.0.0", "")})
        r = M.verifier(distributions=["numpy"])
        assert not r.a_mettre_a_jour
        assert "à jour" in r.resume

    def test_index_injoignable_se_dit_en_une_phrase(self, monkeypatch):
        """Un échec unanime est un problème de réseau, pas huit problèmes."""
        M = self._sans_reseau(monkeypatch, {})
        r = M.verifier()
        assert r.hors_ligne
        assert "injoignable" in r.erreur
        assert r.resume == r.erreur

    def test_une_dependance_absente_n_est_pas_interrogee(self, monkeypatch):
        """Ce qu'il lui faut est une installation, pas une mise à jour."""
        from phytoscope.core import dependency_updates as M
        interrogees = []

        def _index(dist, delai=0, index=""):
            interrogees.append(dist)
            return "2.0.0", ""

        monkeypatch.setattr(M, "derniere_version", _index)
        monkeypatch.setattr(M, "version_installee", lambda dist: "")
        r = M.verifier(distributions=["numpy"])
        assert interrogees == []
        assert r.absentes and r.absentes[0].distribution == "numpy"

    def test_l_arret_est_respecte(self, monkeypatch):
        M = self._sans_reseau(monkeypatch, {"numpy": ("2.0.0", "")})
        r = M.verifier(arret=lambda: True)
        #  Arrêt avant la première interrogation : aucune version relevée.
        assert all(not d.disponible for d in r.dependances)

    def test_la_liste_vient_de_preflight(self):
        """Une seule source pour les dépendances : sinon elles divergent."""
        from phytoscope.core import dependency_updates as M
        from phytoscope.core import preflight
        noms = {d.distribution for d in M._dependances_du_logiciel()}
        assert noms == {r.paquet for r in preflight.REQUIREMENTS}
