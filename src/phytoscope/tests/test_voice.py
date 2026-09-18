# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_voice.py
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

"""Tests du mode vocal : dictionnaire, moteur lexical, sortie parlée.

Aucun de ces tests ne fait parler la machine : la stratégie « silencieuse »
existe précisément pour que le logiciel — et sa vérification — fonctionnent sur
une machine sans synthèse vocale, ce qui est le cas de la plupart des serveurs
d'intégration.
"""
import json
import os

import pytest

from phytoscope.config import Settings
from phytoscope.core.dsp import Event
from phytoscope.music.lexicon import (CSV_HEADER_VOCAL, GRAMMAIRES,
                                      LEXIQUE_PAR_DEFAUT, Lexique, VocalMapper)
from phytoscope.music.voice import VoiceOutput, strategies_disponibles


def reglages(**voix):
    s = Settings()
    s.voice.enabled = True
    s.voice.spoken = False
    for cle, valeur in voix.items():
        setattr(s.voice, cle, valeur)
    return s


def evenement(t=10.0, sigma=5.0, pente=1e-5):
    return Event(index=int(t * 250), time_s=t, amplitude_v=sigma * 1e-5,
                 slope_v_s=pente, sigma=sigma)


class TestLexique:
    def test_dictionnaire_livre_complet(self):
        lex = Lexique()
        for cle in Lexique.REQUIS:
            assert lex.registres.get(cle), cle

    def test_registre_manquant_est_complete(self):
        lex = Lexique({"nom": "bancal", "registres": {"sujet": ["je"]}})
        assert lex.registres["verbe_montee"]
        assert lex.registres["sujet"] == ["je"]

    def test_choisir_est_borne(self):
        lex = Lexique()
        mots = lex.registres["intensite"]
        assert lex.choisir("intensite", -3.0) == mots[0]
        assert lex.choisir("intensite", 12.0) == mots[-1]

    def test_choisir_registre_inconnu(self):
        assert Lexique().choisir("inexistant", 0.5) == "…"

    def test_aller_retour_sur_disque(self, tmp_path):
        chemin = str(tmp_path / "dico.json")
        origine = Lexique()
        origine.enregistrer(chemin)
        relu = Lexique.charger(chemin)
        assert relu.nom == origine.nom
        assert relu.registres == origine.registres

    def test_le_modele_livre_est_un_json_valide(self):
        assert json.loads(json.dumps(LEXIQUE_PAR_DEFAUT))


class TestVocalMapper:
    def test_produit_un_enonce(self):
        m = VocalMapper(reglages())
        e = m.map_event(evenement())
        assert e is not None
        assert e.texte
        assert e.texte[0].isupper()

    def test_desactive_ne_produit_rien(self):
        s = reglages()
        s.voice.enabled = False
        assert VocalMapper(s).map_event(evenement()) is None

    def test_densite_respectee(self):
        m = VocalMapper(reglages(density_per_min=6.0))       # un toutes les 10 s
        assert m.map_event(evenement(t=100.0)) is not None
        assert m.map_event(evenement(t=103.0)) is None
        assert m.map_event(evenement(t=115.0)) is not None

    def test_direction_suit_la_pente(self):
        m = VocalMapper(reglages())
        montee = m.map_event(evenement(t=10.0, pente=+1e-5))
        descente = m.map_event(evenement(t=1000.0, pente=-1e-5))
        assert montee.direction == +1
        assert descente.direction == -1

    def test_intensite_croit_avec_sigma(self):
        m = VocalMapper(reglages(density_per_min=600.0))
        faible = m.map_event(evenement(t=10.0, sigma=3.6))
        fort = m.map_event(evenement(t=1000.0, sigma=30.0))
        assert fort.intensite01 > faible.intensite01

    def test_couleur_vient_de_l_analyseur(self):
        m = VocalMapper(reglages())
        m.set_couleur_hz(25.0)
        e = m.map_event(evenement())
        assert e.couleur_hz == pytest.approx(25.0)
        assert 0.0 <= e.couleur01 <= 1.0

    def test_grammaire_inconnue_retombe_sur_le_defaut(self):
        m = VocalMapper(reglages(grammar="klingon"))
        assert m.map_event(evenement()).grammaire == "contemplative"

    def test_grammaire_minimale_donne_un_seul_mot(self):
        m = VocalMapper(reglages(grammar="minimale"))
        assert len(m.map_event(evenement()).texte.split()) == 1

    def test_ligne_csv_correspond_a_l_entete(self):
        e = VocalMapper(reglages()).map_event(evenement())
        assert len(e.to_row()) == len(CSV_HEADER_VOCAL)

    def test_justification_contient_les_valeurs(self):
        e = VocalMapper(reglages()).map_event(evenement(sigma=7.5))
        assert "σ=7.5" in e.reason
        assert "montée" in e.reason or "descente" in e.reason

    def test_enonce_immuable(self):
        e = VocalMapper(reglages()).map_event(evenement())
        with pytest.raises(Exception):
            e.texte = "autre chose"

    def test_reproductible(self):
        a = VocalMapper(reglages()).map_event(evenement())
        b = VocalMapper(reglages()).map_event(evenement())
        assert a.texte == b.texte

    def test_regles_expliquees(self):
        lignes = VocalMapper(reglages()).describe_rules()
        assert any("traduit" in l for l in lignes)      # l'avertissement y est
        assert len(lignes) >= 6

    def test_dictionnaire_externe_est_charge(self, tmp_path):
        chemin = str(tmp_path / "perso.json")
        Lexique({"nom": "perso", "registres":
                 {"verbe_montee": ["ALPHA"], "verbe_descente": ["OMEGA"]}}
                ).enregistrer(chemin)
        m = VocalMapper(reglages(lexicon_path=chemin, grammar="minimale"))
        assert m.lexique.nom == "perso"
        assert m.map_event(evenement(pente=+1e-5)).texte == "ALPHA"

    def test_dictionnaire_illisible_garde_celui_d_origine(self, tmp_path):
        chemin = str(tmp_path / "casse.json")
        with open(chemin, "w", encoding="utf-8") as f:
            f.write("{ceci n'est pas du JSON")
        m = VocalMapper(reglages(lexicon_path=chemin))
        assert m.lexique.taille() > 0
        assert m.map_event(evenement()) is not None


class TestGrammaires:
    def test_toutes_ont_titre_description_et_gabarits(self):
        for cle, g in GRAMMAIRES.items():
            assert g["titre"] and g["description"] and g["gabarits"], cle

    def test_tous_les_jetons_existent_dans_le_dictionnaire(self):
        import re
        lex = Lexique()
        connus = set(lex.registres) | {"verbe"}
        for cle, g in GRAMMAIRES.items():
            for gabarit in g["gabarits"]:
                for jeton in re.findall(r"\{(\w+)\}", gabarit):
                    assert jeton in connus, f"{cle} : {jeton}"


class TestVoiceOutput:
    def test_strategies_listees(self):
        strategies = strategies_disponibles()
        assert len(strategies) >= 5
        noms = [nom for nom, _, _ in strategies]
        assert "silencieuse" in noms
        assert dict((n, d) for n, d, _ in strategies)["silencieuse"]

    def test_la_silencieuse_est_toujours_disponible(self):
        assert [ok for nom, _, ok in strategies_disponibles()
                if nom == "silencieuse"] == [True]

    def test_cycle_de_vie(self):
        sortie = VoiceOutput(reglages(backend="silencieuse"))
        assert sortie.demarrer() is False               # silencieuse = pas de voix
        assert sortie.actif is True
        assert sortie.backend == "silencieuse"
        assert "aucune synthèse" in sortie.etat()
        sortie.arreter()
        assert sortie.actif is False

    def test_file_bornee_abandonne_plutot_que_d_accumuler(self):
        s = reglages(backend="silencieuse")
        s.voice.spoken = True
        sortie = VoiceOutput(s, profondeur=2)
        sortie._actif = True                            # sans lancer le fil
        assert sortie.dire("un") is True
        assert sortie.dire("deux") is True
        assert sortie.dire("trois") is False
        assert sortie.abandons == 1
        sortie.vider()
        assert sortie.dire("quatre") is True

    def test_ne_dit_rien_quand_elle_est_arretee(self):
        assert VoiceOutput(reglages()).dire("bonjour") is False

    def test_etat_lisible_a_l_arret(self):
        assert VoiceOutput(reglages()).etat() == "arrêtée"


class TestInterruption:
    def test_nettoyages_enregistres_une_seule_fois(self):
        from phytoscope.core import interrupt
        appels = []
        fonction = lambda: appels.append(1)             # noqa: E731
        interrupt.ajouter_nettoyage(fonction)
        interrupt.ajouter_nettoyage(fonction)
        assert interrupt._nettoyages.count(fonction) == 1
        interrupt._nettoyer()
        assert appels == [1]
        interrupt._nettoyages.remove(fonction)

    def test_un_nettoyage_qui_echoue_n_empeche_pas_les_suivants(self):
        from phytoscope.core import interrupt
        trace = []

        def casse():
            raise RuntimeError("volontaire")

        interrupt.ajouter_nettoyage(casse)
        interrupt.ajouter_nettoyage(lambda: trace.append("suite"))
        interrupt._nettoyer()
        assert trace == ["suite"]
        interrupt._nettoyages.clear()

    def test_installation_dans_le_fil_principal(self):
        from phytoscope.core import interrupt
        assert interrupt.installer() is True
