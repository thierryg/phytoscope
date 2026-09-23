# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_api_modules.py
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

"""L'interface des modules : le contrat, la découverte, et surtout l'isolement.

Ce qui est éprouvé ici n'est pas que l'API « fonctionne » — cela se verrait
tout de suite. C'est qu'elle **tient ses promesses** quand un module se
comporte mal : qu'une fault désactive son author et personne d'autre, qu'un
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

from phytoscope.api import (BUS, EVENTS, API_VERSION, Capability, Context,
                            ModuleState, Quantity, Manifest, Module, Registry,
                            Trace, compatible)


# ---------------------------------------------------------------------------
#  Le contrat de version
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("requested,attendu", [
    ("1.0", True),      # exactement la nôtre
    ("1", False),       # mal formé : on refuse plutôt que de deviner
    ("0.9", False),     # majeur différent
    ("2.0", False),     # majeur différent
    ("1.9", False),     # mineur que nous ne savons pas encore honorer
    ("", False),
    ("bonjour", False),
])
def test_la_compatibilite_de_version(requested, attendu):
    assert compatible(requested, "1.0") is attendu


def test_un_module_vise_toute_la_serie_majeure():
    """Un module écrit pour 1.0 doit tourner sur 1.1, 1.2, 1.3…

    C'est LA promesse de l'API. Si cet essai casse, c'est qu'on a rompu le
    contrat sans s'en apercevoir.
    """
    for mineur in range(0, 10):
        assert compatible("1.0", f"1.{mineur}")


# ---------------------------------------------------------------------------
#  Le manifest
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("name,valid", [
    ("mon-module", True), ("a1", True), ("abc-123-xyz", True),
    ("Mon-Module", False),      # majuscules
    ("mon_module", False),      # tiret bas
    ("1module", False),         # commence par un chiffre
    ("a", False),               # trop court
    ("", False), ("mon module", False), ("mon/module", False),
])
def test_la_forme_du_nom(name, valid):
    assert Manifest(name=name).valid is valid


def test_un_manifeste_dit_pourquoi_il_est_refuse():
    """« Refusé » sans raison enverrait l'author chercher dans le vide."""
    problems = Manifest(name="Mauvais Nom", api="9.9",
                        capabilities=("inexistante",)).problems()
    assert len(problems) == 3
    assert any("name" in d for d in problems)
    assert any("9.9" in d for d in problems)
    assert any("inexistante" in d for d in problems)


def test_le_titre_retombe_sur_le_nom():
    assert Manifest(name="mon-module").title == "mon-module"


# ---------------------------------------------------------------------------
#  Ce que les capacités échangent
# ---------------------------------------------------------------------------
def test_une_grandeur_se_met_en_forme_toute_seule():
    assert Quantity(key="x", label="X", value=3.14159).text == "3.14"


def test_une_trace_refuse_des_tailles_incoherentes():
    """Une courbe fausse en silence est pire qu'une courbe absente."""
    with pytest.raises(ValueError, match="abscissas"):
        Trace(x=np.zeros(10), y=np.zeros(11))


# ---------------------------------------------------------------------------
#  Le bus d'événements
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def bus_propre():
    BUS.clear()
    yield
    BUS.clear()


def test_les_evenements_sont_tous_documentes():
    """Un événement publié sans description n'est découvrable par personne."""
    for name, description in EVENTS.items():
        assert name and "." in name, f"« {name} » n'est pas un name d'événement"
        assert len(description) > 20, f"« {name} » n'est pas expliqué"


def test_un_abonne_recoit_ce_qui_est_publie():
    recus = []
    BUS.subscribe("essai.chose", lambda *a: recus.append(a), module="essai")
    BUS.publish("essai.chose", 1, 2)
    assert recus == [(1, 2)]


def test_un_abonne_fautif_est_debranche_sur_le_champ():
    """Laisser branché un abonné qui lève noierait le log sous la même
    trace — celui-là même dont on a besoin pour comprendre la panne."""
    def fautif():
        raise RuntimeError("je tombe")

    sains = []
    BUS.subscribe("essai.chose", fautif, module="fautif")
    BUS.subscribe("essai.chose", lambda: sains.append(1), module="sain")

    assert BUS.subscribers("essai.chose") == 2
    BUS.publish("essai.chose")
    #  Le sain a bien été appelé, le fautif a été retiré.
    assert sains == [1]
    assert BUS.subscribers("essai.chose") == 1
    BUS.publish("essai.chose")
    assert sains == [1, 1]


def test_sabonner_a_un_evenement_inexistant_nest_pas_une_erreur():
    """C'est ce qui permet à un module d'être chargeable sur une version
    ancienne tout en profitant d'un événement récent."""
    BUS.subscribe("event.qui.nexiste.pas", lambda: None, module="essai")
    assert BUS.publish("autre.chose") == 0


# ---------------------------------------------------------------------------
#  Le registre : découverte sans exécution
# ---------------------------------------------------------------------------
def _ecrire_module(directory, name, corps):
    path = os.path.join(directory, name)
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, "module.py"), "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(corps))
    return path


class FauxMoteur:
    class state:
        running = True
        elapsed_s = 100.0
    _evenements_recents = [1.0, 2.0]

    def recent(self, seconds, raw=False):
        return np.random.default_rng(0).normal(0, 3e-6, int(seconds * 250))

    def _message(self, text):
        pass


@pytest.fixture()
def registre(tmp_path, monkeypatch):
    from phytoscope.config import Settings
    monkeypatch.setattr(Registry, "builtin_directory",
                        staticmethod(lambda: str(tmp_path / "integres")))
    monkeypatch.setattr(Registry, "user_directory",
                        staticmethod(lambda: str(tmp_path / "user")))
    os.makedirs(tmp_path / "integres", exist_ok=True)
    os.makedirs(tmp_path / "user", exist_ok=True)
    return Registry(FauxMoteur(), Settings())


def test_le_manifeste_est_lu_sans_executer_le_module(registre, tmp_path):
    """Exécuter un module pour savoir s'il faut l'exécuter serait absurde."""
    _ecrire_module(str(tmp_path / "user"), "explosif", '''
        raise SystemExit("ce module explose à l'import")

        from phytoscope.api import Capability, Manifest, Module

        class Explosif(Module):
            MANIFEST = Manifest(name="explosif", api="9.9")
    ''')
    found = registre.discover()
    #  Découvert malgré tout : le manifest a été lu, sans importer.
    assert [m.name for m in found] == ["explosif"]
    assert found[0].state == ModuleState.INCOMPATIBLE
    assert "9.9" in found[0].fault


def test_les_capacites_declarees_par_constante_sont_lues(registre, tmp_path):
    """`capabilities=(Capability.ANALYSER,)` est plus lisible qu'une chaîne nue —
    encore faut-il que le lecteur de manifest sache la résoudre."""
    _ecrire_module(str(tmp_path / "user"), "avec-constantes", '''
        from phytoscope.api import Capability, Manifest, Module

        class Avec(Module):
            MANIFEST = Manifest(
                name="avec-constantes", api="3.0",
                capabilities=(Capability.ANALYSER, Capability.DESCRIPTOR))
    ''')
    found = registre.discover()
    assert found[0].manifest.capabilities == ("analyser", "descriptor")


def test_une_bibliotheque_absente_ecarte_avant_limport(registre, tmp_path):
    _ecrire_module(str(tmp_path / "user"), "exigeant", '''
        from phytoscope.api import Manifest, Module

        class Exigeant(Module):
            MANIFEST = Manifest(name="exigeant", api="3.0",
                                  requires=("bibliotheque-qui-nexiste-pas",))
    ''')
    m = registre.discover()[0]
    assert m.state == ModuleState.INCOMPATIBLE
    assert "pip install" in m.fault


# ---------------------------------------------------------------------------
#  Le registre : l'isolement
# ---------------------------------------------------------------------------
BON = '''
    from phytoscope.api import Analyser, Capability, Quantity, Manifest, Module

    class Bon(Module, Analyser):
        MANIFEST = Manifest(name="{name}", api="3.0",
                              capabilities=(Capability.ANALYSER,))

        def analyse(self, x, fs, context):
            return [Quantity(key="taille", label="Taille",
                             value=float(x.size), meaning="Le nombre de points.")]
'''


def test_un_module_qui_tombe_ne_fait_pas_tomber_les_autres(registre, tmp_path):
    """La promesse principale de l'API."""
    _ecrire_module(str(tmp_path / "user"), "bon", BON.format(name="bon"))
    _ecrire_module(str(tmp_path / "user"), "mauvais", '''
        from phytoscope.api import Analyser, Capability, Manifest, Module

        class Mauvais(Module, Analyser):
            MANIFEST = Manifest(name="mauvais", api="3.0",
                                  capabilities=(Capability.ANALYSER,))

            def analyse(self, x, fs, context):
                raise ValueError("je tombe")
    ''')
    registre.discover()
    assert registre.load_all() == 2

    mauvais = registre.modules["mauvais"]
    assert registre.call(mauvais, "analyse", np.zeros(100), 250.0,
                            mauvais.context, fallback="repli") == "repli"
    assert mauvais.state == ModuleState.FAULTED
    assert "ValueError" in mauvais.fault

    #  Le bon module continue de fonctionner.
    bon = registre.modules["bon"]
    assert bon.usable
    resultat = registre.call(bon, "analyse", np.zeros(100), 250.0,
                                bon.context, fallback=[])
    assert resultat[0].value == 100.0
    assert [m.name for m in registre.active()] == ["bon"]


def test_une_faute_a_linstallation_desactive_le_module(registre, tmp_path):
    _ecrire_module(str(tmp_path / "user"), "fragile", '''
        from phytoscope.api import Manifest, Module

        class Fragile(Module):
            MANIFEST = Manifest(name="fragile", api="3.0")

            def setup(self):
                raise RuntimeError("je tombe en m'installant")
    ''')
    registre.discover()
    registre.load_all()
    assert registre.modules["fragile"].state == ModuleState.FAULTED
    assert "installation" in registre.modules["fragile"].fault


def test_un_module_desactive_nest_pas_charge(registre, tmp_path):
    _ecrire_module(str(tmp_path / "user"), "bon", BON.format(name="bon"))
    registre._settings.modules.disabled = ["bon"]
    registre.discover()
    assert registre.load_all() == 0
    assert registre.modules["bon"].state == ModuleState.DISABLED


# ---------------------------------------------------------------------------
#  L'order de chargement
# ---------------------------------------------------------------------------
def test_les_dependances_sont_chargees_avant(registre, tmp_path):
    for name, depend in (("zzz-base", ()), ("aaa-dessus", ("zzz-base",))):
        _ecrire_module(str(tmp_path / "user"), name, f'''
            from phytoscope.api import Manifest, Module

            class M(Module):
                MANIFEST = Manifest(name="{name}", api="3.0",
                                      depends_on={depend!r})
        ''')
    registre.discover()
    order = registre._order_them()
    assert order.index("zzz-base") < order.index("aaa-dessus")


def test_un_cycle_de_dependances_ne_bloque_pas_le_chargement(registre, tmp_path):
    """Mieux vaut load dans un order discutable que ne rien load."""
    for name, autre in (("alpha", "beta"), ("beta", "alpha")):
        _ecrire_module(str(tmp_path / "user"), name, f'''
            from phytoscope.api import Manifest, Module

            class M(Module):
                MANIFEST = Manifest(name="{name}", api="3.0",
                                      depends_on=("{autre}",))
        ''')
    registre.discover()
    assert sorted(registre._order_them()) == ["alpha", "beta"]


# ---------------------------------------------------------------------------
#  Les modules livrés avec le logiciel
# ---------------------------------------------------------------------------
def test_les_modules_integres_sont_tous_valides():
    """Ils passent par la même API que les autres : s'ils sont refusés, c'est
    l'API qu'il faut corriger, pas leur faire un passe-droit."""
    directory = Registry.builtin_directory()
    assert os.path.isdir(directory), "le directory des modules intégrés a disparu"

    from phytoscope.config import Settings
    registre = Registry(FauxMoteur(), Settings())
    found = [m for m in registre.discover() if m.origin == "built_in"]
    assert len(found) >= 4, "les modules livrés ont disparu"
    for m in found:
        assert m.manifest.problems() == [], f"{m.name} : {m.manifest.problems()}"
        assert m.manifest.capabilities, f"{m.name} ne provides rien"
        assert m.manifest.description, f"{m.name} ne se décrit pas"
        assert m.state != ModuleState.INCOMPATIBLE, m.fault


def test_les_modules_integres_se_chargent_et_travaillent():
    from phytoscope.config import Settings
    registre = Registry(FauxMoteur(), Settings())
    registre.discover()
    registre.load_all()

    analyseurs = registre.providers(Capability.ANALYSER)
    assert analyseurs, "aucun analyseur intégré ne s'est chargé"

    x = np.random.default_rng(1).normal(0, 3e-6, 30000)
    rendues = 0
    for m in analyseurs:
        for g in registre.call(m, "analyse", x, 250.0, m.context,
                                  fallback=[]) or []:
            assert g.key and g.label
            assert len(g.meaning) > 20, f"{m.name}/{g.key} n'explique rien"
            rendues += 1
    assert rendues >= 10, "les analyseurs intégrés n'ont presque rien rendu"


def test_le_sdk_livre_un_exemple_qui_se_charge():
    """Un SDK dont l'exemple ne fonctionne pas est pire qu'aucun SDK."""
    #  tests/ → src/phytoscope/ → src/. Le SDK a rejoint le code lors du
    #  rangement du 2026-09-18 : il est en src/sdk/, non plus à la racine.
    src = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    exemple = os.path.join(src, "sdk", "hello-world", "module.py")
    if not os.path.exists(exemple):
        pytest.skip("SDK absent de cette copie de travail")

    from phytoscope.config import Settings
    registre = Registry(FauxMoteur(), Settings())
    manifest = registre._read_manifest(exemple, "hello-world")
    assert manifest is not None
    assert manifest.problems() == []
    assert Capability.ANALYSER in manifest.capabilities


# ---------------------------------------------------------------------------
#  The version contract, in both directions
#
#  Asked for on 2026-09-23: a module must be able to read the host's API
#  version, and the host must be able to read the minimum each module needs.
#  The two answers come from the same field through the same parser, which is
#  what these tests hold in place.
# ---------------------------------------------------------------------------
class TestTheVersionContractBothWays:

    def test_a_module_reads_the_hosts_api_version(self):
        """The module's side: what am I actually running on?"""
        from phytoscope.api import API_VERSION, Context
        context = Context("demo", None, None, "/tmp")
        assert context.api_version == API_VERSION

    def test_a_module_can_ask_for_a_floor_at_run_time(self):
        """`api_at_least` is what lets a manifest declare the LOWEST it needs.

        A module needing 3.0 to work at all, but able to use a field added in
        3.2, declares `api="3.0"` and asks here. Declaring 3.2 instead would
        refuse it on every 3.0 and 3.1 host to gain one optional field.
        """
        from phytoscope.api import Context
        context = Context("demo", None, None, "/tmp")
        major, minor = context.api_version.split(".")[:2]
        assert context.api_at_least(f"{major}.{minor}")
        assert not context.api_at_least(f"{major}.{int(minor) + 1}")
        assert not context.api_at_least(f"{int(major) + 1}.0")

    def test_the_host_reads_each_modules_minimum(self):
        """The host's side: what does this module need, at least?"""
        from phytoscope.api import Manifest
        assert Manifest(name="demo", api="3.2").api_required == (3, 2)
        assert Manifest(name="demo", api="10.11").api_required == (10, 11)

    def test_the_minimum_is_a_minimum_and_not_an_exact_match(self):
        """A later minor satisfies it; an earlier one does not."""
        from phytoscope.api import compatible
        assert compatible("3.0", "3.0")
        assert compatible("3.0", "3.7"), "a later minor knows more, not less"
        assert not compatible("3.7", "3.0"), "an earlier minor knows less"
        assert not compatible("3.0", "4.0"), "a different major breaks promises"

    def test_the_patch_number_never_decides(self):
        """A patch clarifies behaviour, never shape: it cannot gate loading."""
        from phytoscope.api import compatible, parse_version
        assert parse_version("3.0.9") == (3, 0)
        assert compatible("3.0.9", "3.0.1")

    def test_an_unreadable_version_is_refused_and_not_guessed(self):
        from phytoscope.api import Manifest, compatible, parse_version
        assert parse_version("trois") == (-1, -1)
        assert not compatible("trois")
        m = Manifest(name="weird", api="trois")
        assert m.problems(), "an unreadable version must not pass silently"
        assert "unreadable" in m.api_satisfied_by

    def test_the_refusal_names_both_versions(self):
        """The sentence a module author reads has to be actionable."""
        from phytoscope.api import API_VERSION, Manifest
        said = Manifest(name="old", api="2.0").problems()[0]
        assert "2.0" in said and API_VERSION in said

    def test_the_context_carries_what_the_manifest_asked_for(self, tmp_path):
        """End to end: the registry hands the minimum down to the module."""
        from phytoscope.api import API_VERSION, Module
        from phytoscope.api.registry import Registry

        directory = tmp_path / "modules" / "floor-reader"
        directory.mkdir(parents=True)
        (directory / "module.py").write_text(
            "from phytoscope.api import Manifest, Module\n"
            "class FloorReader(Module):\n"
            f"    MANIFEST = Manifest(name='floor-reader', api='{API_VERSION}')\n",
            encoding="utf-8")

        registry = Registry(None, None)
        registry.user_directory = staticmethod(          # type: ignore[method-assign]
            lambda: str(tmp_path / "modules"))
        registry.builtin_directory = staticmethod(       # type: ignore[method-assign]
            lambda: str(tmp_path / "none"))
        registry.discover()
        assert registry.api_requirements()["floor-reader"] == (
            int(API_VERSION.split(".")[0]), int(API_VERSION.split(".")[1]))
        assert registry.load("floor-reader")
        context = registry.modules["floor-reader"].context
        assert context.api_required == API_VERSION
        assert context.api_version == API_VERSION
        assert context.api_at_least(context.api_required)
