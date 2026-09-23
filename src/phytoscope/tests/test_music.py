# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_music.py
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

"""Tests des gammes, du diapason, des profils et du moteur de correspondance."""
import pytest

from phytoscope.config import Settings
from phytoscope.core.dsp import Event
from phytoscope.music import profiles, scales
from phytoscope.music.mapper import Mapper


class TestGammes:
    def test_toutes_les_gammes_commencent_par_la_tonique(self):
        for cle, (_, degres) in scales.SCALES.items():
            assert degres[0] == 0, cle

    def test_degres_strictement_croissants(self):
        for cle, (_, degres) in scales.SCALES.items():
            assert degres == sorted(set(degres)), cle

    def test_construction_des_notes(self):
        notes = scales.build_notes("pentatonique_majeure", "C", 3, 2)
        assert len(notes) == 10
        assert notes == sorted(notes)
        assert all(0 <= n <= 127 for n in notes)

    def test_quantification_dans_les_bornes(self):
        notes = scales.build_notes("majeure", "D", 3, 3)
        assert scales.quantize(0.0, notes) == notes[0]
        assert scales.quantize(1.0, notes) == notes[-1]
        assert scales.quantize(-5.0, notes) == notes[0]


class TestDiapason:
    def test_la_de_reference(self):
        assert scales.midi_to_hz(69, 440.0) == pytest.approx(440.0)
        assert scales.midi_to_hz(69, 432.0) == pytest.approx(432.0)

    def test_octave_double_la_frequence(self):
        assert scales.midi_to_hz(81) == pytest.approx(2 * scales.midi_to_hz(69))

    def test_conversion_reciproque(self):
        for midi in (40, 60, 69, 90):
            f = scales.midi_to_hz(midi, 432.0)
            assert scales.hz_to_midi(f, 432.0) == pytest.approx(midi)

    def test_ecart_432_contre_440(self):
        ecart = scales.ecart_cents(scales.midi_to_hz(69, 432.0), 69, 440.0)
        assert ecart == pytest.approx(-31.8, abs=0.5)


class TestProfils:
    def test_douze_profils(self):
        assert len(profiles.PROFILS) == 12

    def test_cles_uniques(self):
        cles = [p.key for p in profiles.PROFILS]
        assert len(cles) == len(set(cles))

    def test_chaque_profil_reference_une_gamme_connue(self):
        for p in profiles.PROFILS:
            assert p.scale in scales.SCALES, p.key

    def test_application_modifie_bien_les_reglages(self):
        s = Settings()
        profil = profiles.get("meditation")
        profil.appliquer(s)
        assert s.music.scale == profil.scale
        assert s.music.diapason_hz == profil.diapason_hz
        assert s.music.profile == "meditation"

    def test_banque_general_midi_complete(self):
        assert len(profiles.GM_INSTRUMENTS) == 128
        assert "Kalimba" in profiles.gm_name(108)


class TestMapper:
    def _evenement(self, sigma=5.0, amplitude=1e-4, t=10.0):
        return Event(index=int(t * 250), time_s=t, amplitude_v=amplitude,
                     slope_v_s=1e-4, sigma=sigma)

    def test_produit_une_note_dans_la_gamme(self):
        s = Settings()
        m = Mapper(s)
        note = m.map_event(self._evenement())
        assert note is not None
        assert note.midi in m.notes
        assert 1 <= note.velocity <= 127

    def test_densite_limite_le_debit(self):
        s = Settings()
        s.music.density_per_min = 6.0          # une note toutes les 10 s
        m = Mapper(s)
        assert m.map_event(self._evenement(t=100.0)) is not None
        assert m.map_event(self._evenement(t=101.0)) is None
        assert m.map_event(self._evenement(t=115.0)) is not None

    def test_muet_si_desactive(self):
        s = Settings()
        s.music.enabled = False
        assert Mapper(s).map_event(self._evenement()) is None

    def test_amplitude_plus_forte_donne_note_plus_aigue(self):
        s = Settings()
        s.music.density_per_min = 600.0
        m = Mapper(s)
        basse = m.map_event(self._evenement(sigma=3.5, t=10.0))
        haute = m.map_event(self._evenement(sigma=30.0, t=20.0))
        assert haute.midi >= basse.midi

    def test_regles_documentees(self):
        assert len(Mapper(Settings()).describe_rules()) >= 5
