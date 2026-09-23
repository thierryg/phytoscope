# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_fingerprint.py
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

"""Tests de l'fingerprint de mesure.

Ce que ces tests protègent est autant déontologique que technique : une
fingerprint doit **séparer deux montages différents** et **rapprocher deux
mesures du même montage**, sans jamais prétendre identifier un végétal. Si la
resemblance ne distinguait rien, l'afficher serait trompeur ; si elle
distinguait trop, on lui ferait dire ce qu'elle ne sait pas.
"""
import json

import numpy as np
import pytest

from phytoscope.core import fingerprint as emp

FS = 250.0


def montage(bruit_uv=3.0, derive_uv_min=20.0, graine=1, duree=120.0,
            evenements_par_min=3.0):
    """Un signal de montage : bruit blanc, bruit lent, dérive, événements."""
    r = np.random.default_rng(graine)
    n = int(duree * FS)
    t = np.arange(n) / FS
    x = r.normal(0, bruit_uv * 1e-6, n)
    x += np.cumsum(r.normal(0, bruit_uv * 1e-7, n)) * 0.02
    x += (derive_uv_min * 1e-6 / 60.0) * t
    evs = list(np.sort(r.uniform(0, duree, int(duree / 60 * evenements_par_min))))
    return x, evs


class TestCalcul:
    def test_descripteurs_renseignes(self):
        x, evs = montage()
        e = emp.compute(x, FS, evs, name="essai")
        values = e.values()
        assert len(values) == len(emp.DESCRIPTORS)
        assert e.bruit_uv > 0 and e.duration_s == pytest.approx(120.0)
        assert e.evenements_min > 0
        assert all(v == v for v in values.values())    # aucun NaN

    def test_signal_trop_court(self):
        e = emp.compute(np.zeros(10), FS)
        assert e.duration_s == 0.0 and e.bruit_uv == 0.0

    def test_le_bruit_se_retrouve(self):
        x, evs = montage(bruit_uv=12.0)
        e = emp.compute(x, FS, evs)
        #  L'fingerprint mesure le signal complet (bruit + dérive) : on vérifie
        #  l'order de grandeur, pas l'égalité.
        assert 5.0 < e.bruit_uv < 60.0

    def test_aller_retour_json(self):
        x, evs = montage()
        e = emp.compute(x, FS, evs, name="ficus")
        relu = emp.Fingerprint.from_dict(json.loads(json.dumps(e.to_dict())))
        assert relu.name == "ficus"
        assert relu.values() == e.values()

    def test_lignes_lisibles(self):
        e = emp.compute(*montage()[:1], FS)
        for label, value in e.rows():
            assert label and value


class TestRessemblance:
    def test_une_empreinte_se_ressemble(self):
        x, evs = montage()
        e = emp.compute(x, FS, evs)
        score, detail = emp.resemble(e, e)
        assert score == pytest.approx(1.0)
        assert len(detail) == len(emp.DESCRIPTORS)

    def test_deux_moments_du_meme_montage_se_ressemblent(self):
        a = emp.compute(*montage(3.0, 20.0, graine=1)[:1], FS)
        b = emp.compute(*montage(3.3, 23.0, graine=2)[:1], FS)
        assert emp.resemble(a, b)[0] > 0.85

    def test_un_contact_degrade_se_distingue(self):
        bon = emp.compute(*montage(3.0, 20.0, graine=1)[:1], FS)
        sec = emp.compute(*montage(60.0, 500.0, graine=3)[:1], FS)
        proche, lointain = emp.resemble(bon, bon)[0], emp.resemble(bon, sec)[0]
        assert lointain < proche - 0.1

    def test_la_ressemblance_est_symetrique(self):
        a = emp.compute(*montage(graine=1)[:1], FS)
        b = emp.compute(*montage(20.0, 100.0, graine=5)[:1], FS)
        assert emp.resemble(a, b)[0] == pytest.approx(emp.resemble(b, a)[0])

    def test_qualification_prudente(self):
        #  No threshold may produce the word "identical" — in any language.
        #  The English wording says "the same setup, most likely", and the
        #  hedge is the point: the fingerprint compares rigs, it does not
        #  identify a plant.
        for borne, phrase in emp.THRESHOLDS:
            assert "identi" not in phrase.lower()
            assert emp.qualify(borne) == phrase
        assert emp.qualify(0.99).startswith("the same setup")
        assert emp.qualify(0.10) == "a different setup"


class TestRegistre:
    def test_ajouter_relire_retirer(self, tmp_path):
        path = str(tmp_path / "montages.json")
        r = emp.Registry(path)
        assert r.empreintes == []
        e = emp.compute(*montage()[:1], FS, name="ficus du salon")
        r.add(e)
        assert len(emp.Registry(path).empreintes) == 1
        r.remove("ficus du salon")
        assert emp.Registry(path).empreintes == []

    def test_un_nom_ne_se_duplique_pas(self, tmp_path):
        path = str(tmp_path / "montages.json")
        r = emp.Registry(path)
        for graine in (1, 2, 3):
            r.add(emp.compute(*montage(graine=graine)[:1], FS, name="même name"))
        assert len(r.empreintes) == 1

    def test_reconnaitre_classe_par_ressemblance(self, tmp_path):
        path = str(tmp_path / "montages.json")
        r = emp.Registry(path)
        r.add(emp.compute(*montage(3.0, 20.0, graine=1)[:1], FS, name="frais"))
        r.add(emp.compute(*montage(80.0, 600.0, graine=9)[:1], FS, name="sec"))
        courant = emp.compute(*montage(3.2, 22.0, graine=2)[:1], FS)
        classement = r.recognise(courant)
        assert [e.name for e, _ in classement][0] == "frais"
        assert classement[0][1] > classement[1][1]

    def test_fichier_illisible_ne_bloque_pas(self, tmp_path):
        path = tmp_path / "montages.json"
        path.write_text("{pas du json", encoding="utf-8")
        assert emp.Registry(str(path)).empreintes == []
