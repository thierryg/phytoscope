# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_fingerprint.py
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

"""Tests de l'empreinte de mesure.

Ce que ces tests protègent est autant déontologique que technique : une
empreinte doit **séparer deux montages différents** et **rapprocher deux
mesures du même montage**, sans jamais prétendre identifier un végétal. Si la
ressemblance ne distinguait rien, l'afficher serait trompeur ; si elle
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
        e = emp.calculer(x, FS, evs, nom="essai")
        valeurs = e.valeurs()
        assert len(valeurs) == len(emp.DESCRIPTEURS)
        assert e.bruit_uv > 0 and e.duree_s == pytest.approx(120.0)
        assert e.evenements_min > 0
        assert all(v == v for v in valeurs.values())    # aucun NaN

    def test_signal_trop_court(self):
        e = emp.calculer(np.zeros(10), FS)
        assert e.duree_s == 0.0 and e.bruit_uv == 0.0

    def test_le_bruit_se_retrouve(self):
        x, evs = montage(bruit_uv=12.0)
        e = emp.calculer(x, FS, evs)
        #  L'empreinte mesure le signal complet (bruit + dérive) : on vérifie
        #  l'ordre de grandeur, pas l'égalité.
        assert 5.0 < e.bruit_uv < 60.0

    def test_aller_retour_json(self):
        x, evs = montage()
        e = emp.calculer(x, FS, evs, nom="ficus")
        relu = emp.Empreinte.from_dict(json.loads(json.dumps(e.to_dict())))
        assert relu.nom == "ficus"
        assert relu.valeurs() == e.valeurs()

    def test_lignes_lisibles(self):
        e = emp.calculer(*montage()[:1], FS)
        for libelle, valeur in e.lignes():
            assert libelle and valeur


class TestRessemblance:
    def test_une_empreinte_se_ressemble(self):
        x, evs = montage()
        e = emp.calculer(x, FS, evs)
        score, detail = emp.ressembler(e, e)
        assert score == pytest.approx(1.0)
        assert len(detail) == len(emp.DESCRIPTEURS)

    def test_deux_moments_du_meme_montage_se_ressemblent(self):
        a = emp.calculer(*montage(3.0, 20.0, graine=1)[:1], FS)
        b = emp.calculer(*montage(3.3, 23.0, graine=2)[:1], FS)
        assert emp.ressembler(a, b)[0] > 0.85

    def test_un_contact_degrade_se_distingue(self):
        bon = emp.calculer(*montage(3.0, 20.0, graine=1)[:1], FS)
        sec = emp.calculer(*montage(60.0, 500.0, graine=3)[:1], FS)
        proche, lointain = emp.ressembler(bon, bon)[0], emp.ressembler(bon, sec)[0]
        assert lointain < proche - 0.1

    def test_la_ressemblance_est_symetrique(self):
        a = emp.calculer(*montage(graine=1)[:1], FS)
        b = emp.calculer(*montage(20.0, 100.0, graine=5)[:1], FS)
        assert emp.ressembler(a, b)[0] == pytest.approx(emp.ressembler(b, a)[0])

    def test_qualification_prudente(self):
        #  Aucun seuil ne doit produire le mot « identique ».
        for borne, phrase in emp.SEUILS:
            assert "identi" not in phrase.lower()
            assert emp.qualifier(borne) == phrase
        assert emp.qualifier(0.99).startswith("le même montage")
        assert emp.qualifier(0.10) == "un autre montage"


class TestRegistre:
    def test_ajouter_relire_retirer(self, tmp_path):
        chemin = str(tmp_path / "montages.json")
        r = emp.Registre(chemin)
        assert r.empreintes == []
        e = emp.calculer(*montage()[:1], FS, nom="ficus du salon")
        r.ajouter(e)
        assert len(emp.Registre(chemin).empreintes) == 1
        r.retirer("ficus du salon")
        assert emp.Registre(chemin).empreintes == []

    def test_un_nom_ne_se_duplique_pas(self, tmp_path):
        chemin = str(tmp_path / "montages.json")
        r = emp.Registre(chemin)
        for graine in (1, 2, 3):
            r.ajouter(emp.calculer(*montage(graine=graine)[:1], FS, nom="même nom"))
        assert len(r.empreintes) == 1

    def test_reconnaitre_classe_par_ressemblance(self, tmp_path):
        chemin = str(tmp_path / "montages.json")
        r = emp.Registre(chemin)
        r.ajouter(emp.calculer(*montage(3.0, 20.0, graine=1)[:1], FS, nom="frais"))
        r.ajouter(emp.calculer(*montage(80.0, 600.0, graine=9)[:1], FS, nom="sec"))
        courant = emp.calculer(*montage(3.2, 22.0, graine=2)[:1], FS)
        classement = r.reconnaitre(courant)
        assert [e.nom for e, _ in classement][0] == "frais"
        assert classement[0][1] > classement[1][1]

    def test_fichier_illisible_ne_bloque_pas(self, tmp_path):
        chemin = tmp_path / "montages.json"
        chemin.write_text("{pas du json", encoding="utf-8")
        assert emp.Registre(str(chemin)).empreintes == []
