# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_api_modules.py
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

"""L'interface des modules : le contrat, la découverte, et surtout l'isolement.

Ce qui est éprouvé ici n'est pas que l'API « fonctionne » — cela se verrait
tout de suite. C'est qu'elle **tient ses promesses** quand un module se
comporte mal : qu'une faute désactive son auteur et personne d'autre, qu'un
module visant une version inconnue soit refusé avant d'être exécuté, et qu'un
abonné fautif soit débranché plutôt que toléré.

Ce sont les seules promesses que quelqu'un d'extérieur nous fera confiance
d'avoir tenues.
"""
from __future__ import annotations

import os
import textwrap

import numpy as np
import pytest

from phytoscope.api import (BUS, EVENEMENTS, VERSION_API, Capacite, Contexte,
                            EtatModule, Grandeur, Manifeste, Module, Registre,
                            Trace, compatible)


# ---------------------------------------------------------------------------
#  Le contrat de version
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("demande,attendu", [
    ("1.0", True),      # exactement la nôtre
    ("1", False),       # mal formé : on refuse plutôt que de deviner
    ("0.9", False),     # majeur différent
    ("2.0", False),     # majeur différent
    ("1.9", False),     # mineur que nous ne savons pas encore honorer
    ("", False),
    ("bonjour", False),
])
def test_la_compatibilite_de_version(demande, attendu):
    assert compatible(demande, "1.0") is attendu


def test_un_module_vise_toute_la_serie_majeure():
    """Un module écrit pour 1.0 doit tourner sur 1.1, 1.2, 1.3…

    C'est LA promesse de l'API. Si cet essai casse, c'est qu'on a rompu le
    contrat sans s'en apercevoir.
    """
    for mineur in range(0, 10):
        assert compatible("1.0", f"1.{mineur}")


# ---------------------------------------------------------------------------
#  Le manifeste
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nom,valide", [
    ("mon-module", True), ("a1", True), ("abc-123-xyz", True),
    ("Mon-Module", False),      # majuscules
    ("mon_module", False),      # tiret bas
    ("1module", False),         # commence par un chiffre
    ("a", False),               # trop court
    ("", False), ("mon module", False), ("mon/module", False),
])
def test_la_forme_du_nom(nom, valide):
    assert Manifeste(nom=nom).valide is valide


def test_un_manifeste_dit_pourquoi_il_est_refuse():
    """« Refusé » sans raison enverrait l'auteur chercher dans le vide."""
    defauts = Manifeste(nom="Mauvais Nom", api="9.9",
                        capacites=("inexistante",)).defauts()
    assert len(defauts) == 3
    assert any("nom" in d for d in defauts)
    assert any("9.9" in d for d in defauts)
    assert any("inexistante" in d for d in defauts)


def test_le_titre_retombe_sur_le_nom():
    assert Manifeste(nom="mon-module").titre == "mon-module"


# ---------------------------------------------------------------------------
#  Ce que les capacités échangent
# ---------------------------------------------------------------------------
def test_une_grandeur_se_met_en_forme_toute_seule():
    assert Grandeur(cle="x", libelle="X", valeur=3.14159).texte == "3.14"


def test_une_trace_refuse_des_tailles_incoherentes():
    """Une courbe fausse en silence est pire qu'une courbe absente."""
    with pytest.raises(ValueError, match="abscisses"):
        Trace(x=np.zeros(10), y=np.zeros(11))


# ---------------------------------------------------------------------------
#  Le bus d'événements
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def bus_propre():
    BUS.vider()
    yield
    BUS.vider()


def test_les_evenements_sont_tous_documentes():
    """Un événement publié sans description n'est découvrable par personne."""
    for nom, description in EVENEMENTS.items():
        assert nom and "." in nom, f"« {nom} » n'est pas un nom d'événement"
        assert len(description) > 20, f"« {nom} » n'est pas expliqué"


def test_un_abonne_recoit_ce_qui_est_publie():
    recus = []
    BUS.abonner("essai.chose", lambda *a: recus.append(a), module="essai")
    BUS.publier("essai.chose", 1, 2)
    assert recus == [(1, 2)]


def test_un_abonne_fautif_est_debranche_sur_le_champ():
    """Laisser branché un abonné qui lève noierait le journal sous la même
    trace — celui-là même dont on a besoin pour comprendre la panne."""
    def fautif():
        raise RuntimeError("je tombe")

    sains = []
    BUS.abonner("essai.chose", fautif, module="fautif")
    BUS.abonner("essai.chose", lambda: sains.append(1), module="sain")

    assert BUS.abonnes("essai.chose") == 2
    BUS.publier("essai.chose")
    #  Le sain a bien été appelé, le fautif a été retiré.
    assert sains == [1]
    assert BUS.abonnes("essai.chose") == 1
    BUS.publier("essai.chose")
    assert sains == [1, 1]


def test_sabonner_a_un_evenement_inexistant_nest_pas_une_erreur():
    """C'est ce qui permet à un module d'être chargeable sur une version
    ancienne tout en profitant d'un événement récent."""
    BUS.abonner("evenement.qui.nexiste.pas", lambda: None, module="essai")
    assert BUS.publier("autre.chose") == 0


# ---------------------------------------------------------------------------
#  Le registre : découverte sans exécution
# ---------------------------------------------------------------------------
def _ecrire_module(dossier, nom, corps):
    chemin = os.path.join(dossier, nom)
    os.makedirs(chemin, exist_ok=True)
    with open(os.path.join(chemin, "module.py"), "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(corps))
    return chemin


class FauxMoteur:
    class state:
        running = True
        elapsed_s = 100.0
    _evenements_recents = [1.0, 2.0]

    def recent(self, secondes, raw=False):
        return np.random.default_rng(0).normal(0, 3e-6, int(secondes * 250))

    def _message(self, texte):
        pass


@pytest.fixture()
def registre(tmp_path, monkeypatch):
    from phytoscope.config import Settings
    monkeypatch.setattr(Registre, "dossier_integres",
                        staticmethod(lambda: str(tmp_path / "integres")))
    monkeypatch.setattr(Registre, "dossier_utilisateur",
                        staticmethod(lambda: str(tmp_path / "utilisateur")))
    os.makedirs(tmp_path / "integres", exist_ok=True)
    os.makedirs(tmp_path / "utilisateur", exist_ok=True)
    return Registre(FauxMoteur(), Settings())


def test_le_manifeste_est_lu_sans_executer_le_module(registre, tmp_path):
    """Exécuter un module pour savoir s'il faut l'exécuter serait absurde."""
    _ecrire_module(str(tmp_path / "utilisateur"), "explosif", '''
        raise SystemExit("ce module explose à l'import")

        from phytoscope.api import Capacite, Manifeste, Module

        class Explosif(Module):
            MANIFESTE = Manifeste(nom="explosif", api="9.9")
    ''')
    trouves = registre.decouvrir()
    #  Découvert malgré tout : le manifeste a été lu, sans importer.
    assert [m.nom for m in trouves] == ["explosif"]
    assert trouves[0].etat == EtatModule.INCOMPATIBLE
    assert "9.9" in trouves[0].faute


def test_les_capacites_declarees_par_constante_sont_lues(registre, tmp_path):
    """`capacites=(Capacite.ANALYSEUR,)` est plus lisible qu'une chaîne nue —
    encore faut-il que le lecteur de manifeste sache la résoudre."""
    _ecrire_module(str(tmp_path / "utilisateur"), "avec-constantes", '''
        from phytoscope.api import Capacite, Manifeste, Module

        class Avec(Module):
            MANIFESTE = Manifeste(
                nom="avec-constantes", api="1.0",
                capacites=(Capacite.ANALYSEUR, Capacite.DESCRIPTEUR))
    ''')
    trouves = registre.decouvrir()
    assert trouves[0].manifeste.capacites == ("analyseur", "descripteur")


def test_une_bibliotheque_absente_ecarte_avant_limport(registre, tmp_path):
    _ecrire_module(str(tmp_path / "utilisateur"), "exigeant", '''
        from phytoscope.api import Manifeste, Module

        class Exigeant(Module):
            MANIFESTE = Manifeste(nom="exigeant", api="1.0",
                                  exige=("bibliotheque-qui-nexiste-pas",))
    ''')
    m = registre.decouvrir()[0]
    assert m.etat == EtatModule.INCOMPATIBLE
    assert "pip install" in m.faute


# ---------------------------------------------------------------------------
#  Le registre : l'isolement
# ---------------------------------------------------------------------------
BON = '''
    from phytoscope.api import Analyseur, Capacite, Grandeur, Manifeste, Module

    class Bon(Module, Analyseur):
        MANIFESTE = Manifeste(nom="{nom}", api="1.0",
                              capacites=(Capacite.ANALYSEUR,))

        def analyser(self, x, fs, contexte):
            return [Grandeur(cle="taille", libelle="Taille",
                             valeur=float(x.size), sens="Le nombre de points.")]
'''


def test_un_module_qui_tombe_ne_fait_pas_tomber_les_autres(registre, tmp_path):
    """La promesse principale de l'API."""
    _ecrire_module(str(tmp_path / "utilisateur"), "bon", BON.format(nom="bon"))
    _ecrire_module(str(tmp_path / "utilisateur"), "mauvais", '''
        from phytoscope.api import Analyseur, Capacite, Manifeste, Module

        class Mauvais(Module, Analyseur):
            MANIFESTE = Manifeste(nom="mauvais", api="1.0",
                                  capacites=(Capacite.ANALYSEUR,))

            def analyser(self, x, fs, contexte):
                raise ValueError("je tombe")
    ''')
    registre.decouvrir()
    assert registre.charger_tout() == 2

    mauvais = registre.modules["mauvais"]
    assert registre.appeler(mauvais, "analyser", np.zeros(100), 250.0,
                            mauvais.contexte, defaut="repli") == "repli"
    assert mauvais.etat == EtatModule.EN_FAUTE
    assert "ValueError" in mauvais.faute

    #  Le bon module continue de fonctionner.
    bon = registre.modules["bon"]
    assert bon.utilisable
    resultat = registre.appeler(bon, "analyser", np.zeros(100), 250.0,
                                bon.contexte, defaut=[])
    assert resultat[0].valeur == 100.0
    assert [m.nom for m in registre.actifs()] == ["bon"]


def test_une_faute_a_linstallation_desactive_le_module(registre, tmp_path):
    _ecrire_module(str(tmp_path / "utilisateur"), "fragile", '''
        from phytoscope.api import Manifeste, Module

        class Fragile(Module):
            MANIFESTE = Manifeste(nom="fragile", api="1.0")

            def installer(self):
                raise RuntimeError("je tombe en m'installant")
    ''')
    registre.decouvrir()
    registre.charger_tout()
    assert registre.modules["fragile"].etat == EtatModule.EN_FAUTE
    assert "installation" in registre.modules["fragile"].faute


def test_un_module_desactive_nest_pas_charge(registre, tmp_path):
    _ecrire_module(str(tmp_path / "utilisateur"), "bon", BON.format(nom="bon"))
    registre._reglages.modules.desactives = ["bon"]
    registre.decouvrir()
    assert registre.charger_tout() == 0
    assert registre.modules["bon"].etat == EtatModule.DESACTIVE


# ---------------------------------------------------------------------------
#  L'ordre de chargement
# ---------------------------------------------------------------------------
def test_les_dependances_sont_chargees_avant(registre, tmp_path):
    for nom, depend in (("zzz-base", ()), ("aaa-dessus", ("zzz-base",))):
        _ecrire_module(str(tmp_path / "utilisateur"), nom, f'''
            from phytoscope.api import Manifeste, Module

            class M(Module):
                MANIFESTE = Manifeste(nom="{nom}", api="1.0",
                                      depend_de={depend!r})
        ''')
    registre.decouvrir()
    ordre = registre._ordonner()
    assert ordre.index("zzz-base") < ordre.index("aaa-dessus")


def test_un_cycle_de_dependances_ne_bloque_pas_le_chargement(registre, tmp_path):
    """Mieux vaut charger dans un ordre discutable que ne rien charger."""
    for nom, autre in (("alpha", "beta"), ("beta", "alpha")):
        _ecrire_module(str(tmp_path / "utilisateur"), nom, f'''
            from phytoscope.api import Manifeste, Module

            class M(Module):
                MANIFESTE = Manifeste(nom="{nom}", api="1.0",
                                      depend_de=("{autre}",))
        ''')
    registre.decouvrir()
    assert sorted(registre._ordonner()) == ["alpha", "beta"]


# ---------------------------------------------------------------------------
#  Les modules livrés avec le logiciel
# ---------------------------------------------------------------------------
def test_les_modules_integres_sont_tous_valides():
    """Ils passent par la même API que les autres : s'ils sont refusés, c'est
    l'API qu'il faut corriger, pas leur faire un passe-droit."""
    dossier = Registre.dossier_integres()
    assert os.path.isdir(dossier), "le dossier des modules intégrés a disparu"

    from phytoscope.config import Settings
    registre = Registre(FauxMoteur(), Settings())
    trouves = [m for m in registre.decouvrir() if m.origine == "integre"]
    assert len(trouves) >= 4, "les modules livrés ont disparu"
    for m in trouves:
        assert m.manifeste.defauts() == [], f"{m.nom} : {m.manifeste.defauts()}"
        assert m.manifeste.capacites, f"{m.nom} ne fournit rien"
        assert m.manifeste.description, f"{m.nom} ne se décrit pas"
        assert m.etat != EtatModule.INCOMPATIBLE, m.faute


def test_les_modules_integres_se_chargent_et_travaillent():
    from phytoscope.config import Settings
    registre = Registre(FauxMoteur(), Settings())
    registre.decouvrir()
    registre.charger_tout()

    analyseurs = registre.fournisseurs(Capacite.ANALYSEUR)
    assert analyseurs, "aucun analyseur intégré ne s'est chargé"

    x = np.random.default_rng(1).normal(0, 3e-6, 30000)
    rendues = 0
    for m in analyseurs:
        for g in registre.appeler(m, "analyser", x, 250.0, m.contexte,
                                  defaut=[]) or []:
            assert g.cle and g.libelle
            assert len(g.sens) > 20, f"{m.nom}/{g.cle} n'explique rien"
            rendues += 1
    assert rendues >= 10, "les analyseurs intégrés n'ont presque rien rendu"


def test_le_sdk_livre_un_exemple_qui_se_charge():
    """Un SDK dont l'exemple ne fonctionne pas est pire qu'aucun SDK."""
    #  tests/ → src/phytoscope/ → src/. Le SDK a rejoint le code lors du
    #  rangement du 2026-09-18 : il est en src/sdk/, non plus à la racine.
    src = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    exemple = os.path.join(src, "sdk", "bonjour-monde", "module.py")
    if not os.path.exists(exemple):
        pytest.skip("SDK absent de cette copie de travail")

    from phytoscope.config import Settings
    registre = Registre(FauxMoteur(), Settings())
    manifeste = registre._lire_manifeste(exemple, "bonjour-monde")
    assert manifeste is not None
    assert manifeste.defauts() == []
    assert Capacite.ANALYSEUR in manifeste.capacites
