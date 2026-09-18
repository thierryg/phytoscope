# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_i18n.py
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

"""Tests de la traduction : mécanisme, catalogues livrés, couverture.

Le test le plus utile de ce fichier est le dernier : il vérifie que **chaque
catalogue livré traduit la totalité des libellés**. Ajouter un libellé au code
sans le traduire fait donc échouer la vérification, ce qui est exactement le
moment où l'on peut encore le corriger sans effort — plutôt que de le découvrir
dans une capture d'écran envoyée par un utilisateur.
"""
import json
import os

import pytest

from phytoscope import i18n


@pytest.fixture(autouse=True)
def revenir_au_francais():
    """Chaque test repart du français : la langue est un état global."""
    yield
    i18n.definir_langue("fr")


class TestMecanisme:
    def test_le_francais_est_la_source(self):
        i18n.definir_langue("fr")
        assert i18n.t("Oscilloscope") == "Oscilloscope"
        assert i18n.langue_courante() == "fr"

    def test_traduction_simple(self):
        i18n.definir_langue("en")
        assert i18n.t("Multimètre") == "Multimeter"

    def test_libelle_inconnu_retombe_sur_le_francais(self):
        i18n.definir_langue("en")
        assert i18n.t("phrase qui n'existe nulle part") == \
            "phrase qui n'existe nulle part"

    def test_le_manquant_est_compté(self):
        i18n.definir_langue("en")
        i18n.t("libellé absent du catalogue, pour le test")
        assert "libellé absent du catalogue, pour le test" in i18n.manquantes("en")

    def test_langue_inconnue_retombe_sur_le_francais(self):
        assert i18n.definir_langue("klingon") == "fr"

    def test_chaine_vide(self):
        i18n.definir_langue("en")
        assert i18n.t("") == ""

    def test_direction_de_lecture(self):
        assert i18n.meta("fr")["direction"] == "ltr"
        assert i18n.meta("ar")["direction"] == "rtl"
        i18n.definir_langue("ar")
        assert i18n.direction_courante() == "rtl"

    def test_valeur_vide_vaut_absence(self, tmp_path, monkeypatch):
        #  Un catalogue à moitié rempli doit rester utilisable.
        dossier = tmp_path / "langues"
        dossier.mkdir()
        (dossier / "xx.json").write_text(json.dumps({
            "_langue": {"nom": "Essai", "nom_fr": "essai", "direction": "ltr"},
            "Oscilloscope": "", "Multimètre": "Ceci"}), encoding="utf-8")
        monkeypatch.setattr(i18n, "DOSSIER", str(dossier))
        i18n._chargees.pop("xx", None)
        table = i18n.catalogue("xx")
        assert "Oscilloscope" not in table
        assert table["Multimètre"] == "Ceci"

    def test_catalogue_absent_ne_leve_rien(self, tmp_path, monkeypatch):
        monkeypatch.setattr(i18n, "DOSSIER", str(tmp_path))
        i18n._chargees.pop("zz", None)
        assert i18n.catalogue("zz") == {}


class TestModele:
    def test_ecrire_un_modele(self, tmp_path):
        chemin = str(tmp_path / "xx.json")
        n = i18n.ecrire_modele(chemin, ["Un", "Deux"], "")
        assert n == 2
        donnees = json.load(open(chemin, encoding="utf-8"))
        assert donnees["Un"] == "" and donnees["Deux"] == ""
        assert "_langue" in donnees

    def test_completer_garde_les_traductions(self, tmp_path):
        chemin = str(tmp_path / "en.json")
        #  On part du vrai catalogue anglais : les clés connues restent
        #  traduites, les nouvelles arrivent vides.
        cles = ["Multimètre", "Un libellé tout neuf"]
        n = i18n.ecrire_modele(chemin, cles, "en")
        donnees = json.load(open(chemin, encoding="utf-8"))
        assert donnees["Multimètre"] == "Multimeter"
        assert donnees["Un libellé tout neuf"] == ""
        assert n == 1


class TestInventaire:
    def test_les_libelles_sont_trouves(self):
        cles = i18n.collecter_cles()
        assert len(cles) > 400
        for attendu in ("Oscilloscope", "Multimètre", "Calculer maintenant",
                        "activer le mode vocal", "Kalimba", "Domaine temporel"):
            assert attendu in cles

    def test_aucun_doublon(self):
        cles = i18n.collecter_cles()
        assert len(cles) == len(set(cles))

    def test_aucune_cle_technique(self):
        #  Une feuille de style ou un nom d'objet dans le catalogue signalerait
        #  que l'enrobage a dérapé.
        for cle in i18n.collecter_cles():
            assert "color:" not in cle, cle
            assert not cle.startswith("#"), cle


class TestCataloguesLivres:
    def test_chaque_catalogue_est_un_json_valide(self):
        for code in i18n.codes_presents():
            if code == i18n.LANGUE_SOURCE:
                continue
            with open(i18n.chemin_catalogue(code), encoding="utf-8") as f:
                donnees = json.load(f)
            assert "_langue" in donnees, code
            for champ in ("nom", "nom_fr", "direction"):
                assert donnees["_langue"].get(champ), f"{code} : {champ}"

    def test_les_onze_langues_annoncees_sont_presentes(self):
        presents = set(i18n.codes_presents())
        for code, _, _, _ in i18n.LIVREES:
            assert code in presents, code

    def test_couverture_complete(self):
        """Chaque catalogue livré traduit la totalité des libellés."""
        cles = i18n.collecter_cles()
        for code in i18n.codes_presents():
            if code == i18n.LANGUE_SOURCE:
                continue
            table = i18n.catalogue(code)
            absents = [c for c in cles if not table.get(c)]
            assert not absents, (
                f"{code} : {len(absents)} libellés non traduits, "
                f"par exemple {absents[:3]}")

    def test_les_champs_de_substitution_sont_preserves(self):
        """Une traduction qui perd un {champ} produirait un KeyError à l'usage."""
        import re
        cles = i18n.collecter_cles()
        for code in i18n.codes_presents():
            if code == i18n.LANGUE_SOURCE:
                continue
            table = i18n.catalogue(code)
            for cle in cles:
                trad = table.get(cle)
                if not trad:
                    continue
                attendus = set(re.findall(r"\{(\w+)[^}]*\}", cle))
                obtenus = set(re.findall(r"\{(\w+)[^}]*\}", trad))
                assert attendus == obtenus, f"{code} : « {cle} »"

    def test_aucune_cle_perimee(self):
        """Un catalogue ne doit pas garder des libellés que le code a retirés."""
        connues = set(i18n.collecter_cles())
        for code in i18n.codes_presents():
            if code == i18n.LANGUE_SOURCE:
                continue
            with open(i18n.chemin_catalogue(code), encoding="utf-8") as f:
                donnees = json.load(f)
            perimees = [k for k in donnees
                        if not k.startswith("_") and k not in connues]
            assert not perimees, f"{code} : {perimees[:3]}"


class TestPremierLancement:
    """Au premier lancement, l'interface est en français — sans exception.

    Le logiciel ne consulte pas la locale du système : c'est un choix, pas un
    oubli. L'ouvrage, les planches et le dictionnaire du mode vocal sont en
    français ; une interface qui ne correspondrait pas à sa documentation
    coûterait plus cher qu'elle ne rapporterait. Ces tests existent pour qu'une
    détection automatique ne soit pas ajoutée par mégarde.
    """

    def test_reglages_neufs(self):
        from phytoscope.config import Settings
        assert Settings().ui.language == "fr"

    def test_aucun_fichier_de_reglages(self, tmp_path):
        from phytoscope.config import Settings
        s = Settings.load(str(tmp_path / "absent.json"))
        assert s.ui.language == "fr"

    def test_fichier_sans_la_clé_de_langue(self, tmp_path):
        #  Un fichier écrit par une version antérieure à la traduction.
        from phytoscope.config import Settings
        chemin = tmp_path / "reglages.json"
        chemin.write_text(json.dumps({"ui": {"theme": "clair"}}), encoding="utf-8")
        s = Settings.load(str(chemin))
        assert s.ui.theme == "clair"
        assert s.ui.language == "fr"

    def test_fichier_corrompu(self, tmp_path):
        from phytoscope.config import Settings
        chemin = tmp_path / "reglages.json"
        chemin.write_text("{ceci n'est pas du JSON", encoding="utf-8")
        assert Settings.load(str(chemin)).ui.language == "fr"

    def test_la_locale_du_systeme_n_influe_pas(self, monkeypatch):
        from phytoscope.config import Settings
        for variable in ("LANG", "LC_ALL", "LC_MESSAGES", "LANGUAGE"):
            monkeypatch.setenv(variable, "ja_JP.UTF-8")
        assert Settings().ui.language == "fr"
        assert i18n.definir_langue(Settings().ui.language) == "fr"
        assert i18n.t("Multimètre") == "Multimètre"

    def test_langue_vide_ou_absente(self):
        assert i18n.definir_langue("") == "fr"
        assert i18n.definir_langue(None) == "fr"

    def test_le_choix_de_l_utilisateur_est_conservé(self, tmp_path):
        from phytoscope.config import Settings
        chemin = str(tmp_path / "reglages.json")
        s = Settings()
        s.ui.language = "ja"
        s.save(chemin)
        assert Settings.load(chemin).ui.language == "ja"
