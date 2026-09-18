# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_samples.py
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

"""Tests des échantillons et de la surveillance du disque.

Ce que ces tests protègent : la **fidélité** de ce qu'on relit. Un échantillon
qui se recharge avec une amplitude fausse ou une cadence fausse est pire qu'un
échantillon absent, parce qu'on le croit.
"""
import json
import os

import numpy as np
import pytest

from phytoscope.config import Settings
from phytoscope.core import espace, samples


def signal(n=2500, amplitude=1.5e-4, graine=3):
    rng = np.random.default_rng(graine)
    t = np.arange(n) / 250.0
    return amplitude * np.sin(2 * np.pi * 0.7 * t) + rng.normal(0, 1e-6, n)


class TestEcriture:
    def test_aller_retour_fidele(self, tmp_path):
        x = signal()
        chemin = samples.ecrire(x, 250.0, str(tmp_path), etiquette="ficus")
        ref = samples.lister(str(tmp_path))[0]
        y, fs = samples.charger(ref)
        assert fs == 250.0
        assert y.shape == (x.size, 1)
        #  L'erreur doit rester sous le pas de quantification, soit mille fois
        #  moins que le bruit propre d'une bonne électrode.
        assert float(np.max(np.abs(y[:, 0] - x))) < ref.full_scale_v / 8388607.0 * 1.5

    def test_pleine_echelle_adaptee(self, tmp_path):
        #  Un signal de 150 µV ne doit pas être écrit à ±2,5 V.
        chemin = samples.ecrire(signal(amplitude=1.5e-4), 250.0, str(tmp_path))
        ref = samples.lister(str(tmp_path))[0]
        assert ref.full_scale_v == pytest.approx(2e-4)
        assert ref.meta["pas_de_quantification_v"] < 1e-9

    def test_echelle_ronde(self):
        for crete, attendu in ((9e-5, 2e-4), (3e-4, 5e-4), (1.1e-3, 2e-3),
                               (1e-9, 1e-5)):
            x = np.array([crete, -crete])
            assert samples.echelle_adaptee(x) == pytest.approx(attendu)

    def test_metadonnees_conservees(self, tmp_path):
        samples.ecrire(signal(), 250.0, str(tmp_path), etiquette="ficus",
                       metadonnees={"plante": "Ficus", "lieu": "salon"})
        ref = samples.lister(str(tmp_path))[0]
        assert ref.plante == "Ficus" and ref.lieu == "salon"
        assert ref.complet

    def test_jamais_ecraser(self, tmp_path):
        a = samples.ecrire(signal(), 250.0, str(tmp_path), etiquette="x")
        b = samples.ecrire(signal(), 250.0, str(tmp_path), etiquette="x")
        assert a != b
        assert len(samples.lister(str(tmp_path))) == 2

    def test_signal_vide_refuse(self, tmp_path):
        with pytest.raises(ValueError):
            samples.ecrire(np.zeros(0), 250.0, str(tmp_path))


class TestLectureDegradee:
    def test_wav_seul_reste_lisible(self, tmp_path):
        """Sans son JSON, la forme est intacte et l'échelle est supposée."""
        samples.ecrire(signal(), 250.0, str(tmp_path), etiquette="orphelin")
        ref = samples.lister(str(tmp_path))[0]
        os.remove(ref.json_path)
        ref = samples.lister(str(tmp_path))[0]
        assert not ref.complet
        y, fs = samples.charger(ref, pleine_echelle_defaut=2.5)
        assert fs == 250.0 and y.size > 0

    def test_json_illisible_ne_bloque_pas(self, tmp_path):
        samples.ecrire(signal(), 250.0, str(tmp_path))
        ref = samples.lister(str(tmp_path))[0]
        open(ref.json_path, "w").write("{pas du json")
        ref = samples.lister(str(tmp_path))[0]
        assert samples.charger(ref)[0] is not None

    def test_dossier_absent(self, tmp_path):
        assert samples.lister(str(tmp_path / "nulle-part")) == []


class TestGestion:
    def test_renommer_emporte_le_json(self, tmp_path):
        samples.ecrire(signal(), 250.0, str(tmp_path), etiquette="avant")
        ref = samples.lister(str(tmp_path))[0]
        nouveau = samples.renommer(ref, "après la pluie")
        assert os.path.exists(nouveau)
        assert os.path.exists(os.path.splitext(nouveau)[0] + ".json")
        assert not os.path.exists(ref.path)

    def test_supprimer_efface_les_deux(self, tmp_path):
        samples.ecrire(signal(), 250.0, str(tmp_path))
        ref = samples.lister(str(tmp_path))[0]
        samples.supprimer(ref)
        assert samples.lister(str(tmp_path)) == []


class TestEspaceDisque:
    def test_mesure_un_dossier_existant(self, tmp_path):
        e = espace.mesurer(str(tmp_path))
        assert e.mesure and e.total_mo > 0 and e.libre_mo >= 0

    def test_mesure_un_dossier_a_creer(self, tmp_path):
        #  Demander l'espace d'un dossier qu'on s'apprête à créer est le cas
        #  normal, pas une erreur.
        e = espace.mesurer(str(tmp_path / "pas" / "encore" / "la"))
        assert e.mesure and e.total_mo > 0

    def test_debit_domine_par_le_rendu_musical(self):
        s = Settings()
        avec = espace.debit_mo_par_heure(s)
        s.recording.write_audio = False
        sans = espace.debit_mo_par_heure(s)
        assert avec > 100.0 and sans < 10.0

    def test_autonomie(self):
        assert espace.autonomie_heures(1000.0, 500.0, 100.0) == pytest.approx(5.0)
        assert espace.autonomie_heures(100.0, 500.0, 100.0) == 0.0
        assert espace.autonomie_heures(1000.0, 0.0, 0.0) == float("inf")

    def test_formats_lisibles(self):
        assert espace.formater_mo(512) == "512 Mo"
        assert espace.formater_mo(2048) == "2,0 Go"
        assert espace.formater_duree(1.5) == "1 h 30"
        assert espace.formater_duree(0.25) == "15 min"
        assert espace.formater_duree(0.0) == "< 1 min"


class TestRelecture:
    """Rejouer, c'est **suspendre l'entrée** — pas mélanger deux signaux.

    Le danger de la relecture n'est pas technique, il est déontologique : si
    l'acquisition continuait pendant qu'on rejoue un enregistrement, on ne
    saurait plus ce qu'on écoute. La source vivante est donc arrêtée, et rendue
    telle qu'elle était au retour.
    """

    def _moteur(self, tmp_path):
        from phytoscope.core.engine import Engine
        s = Settings()
        s.acquisition.source = "simulation"
        s.recording.directory = str(tmp_path)
        s.music.enabled = False
        return Engine(s)

    def test_la_source_vivante_est_arretee(self, tmp_path):
        import time
        e = self._moteur(tmp_path)
        e.start()
        time.sleep(1.0)
        vivante = e.source
        assert vivante.running
        assert e.rejouer(signal(), 250.0, vitesse=50.0, nom="essai")
        try:
            assert not vivante.running, "l'entrée en direct doit être suspendue"
            assert e.state.replaying
            assert e.state.replay_name == "essai"
            assert e.source is not vivante
        finally:
            e.arreter_relecture(revenir_en_direct=False)
            e.stop()

    def test_la_cadence_du_fichier_est_rendue(self, tmp_path):
        import time
        e = self._moteur(tmp_path)
        e.start()
        time.sleep(0.5)
        depart = e.settings.acquisition.sample_rate
        e.rejouer(signal(), 1000.0, nom="autre cadence")
        try:
            assert e.settings.acquisition.sample_rate == 1000.0
        finally:
            e.arreter_relecture(revenir_en_direct=False)
        assert e.settings.acquisition.sample_rate == depart
        e.stop()

    def test_signal_vide_refuse(self, tmp_path):
        e = self._moteur(tmp_path)
        assert e.rejouer(np.zeros(0), 250.0) is False
        assert not e.state.replaying

    def test_arreter_sans_relecture_ne_fait_rien(self, tmp_path):
        e = self._moteur(tmp_path)
        e.arreter_relecture(revenir_en_direct=False)   # ne doit rien lever
        assert not e.state.replaying
