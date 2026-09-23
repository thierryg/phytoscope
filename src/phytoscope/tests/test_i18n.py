# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_i18n.py
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

"""Translation tests: the mechanism, the shipped catalogs, the coverage.

The most useful test in this file is `test_every_catalog_is_complete`: it
checks that **every shipped catalog translates all of the labels**. Adding a
label to the code without translating it therefore fails the suite, which is
exactly the moment it can still be fixed for nothing — rather than finding it
in a screenshot sent by a user.

The keys are English, and have been since 2026-09-22. English is the source
language: the labels written in the code *are* the English text, so there is
no `en.json` to keep in step with anything. French became a catalog like the
nine others, and the French strings still in this file — `"Multimètre"`,
`"Ceci"` — are what `fr.json` is expected to return, which makes them
**data**, not prose.
"""
import json
import os

import pytest

from phytoscope import i18n


@pytest.fixture(autouse=True)
def back_to_the_source():
    """Every test starts from the source language: it is global state."""
    yield
    i18n.definir_langue(i18n.LANGUE_SOURCE)


class TestMechanism:
    def test_english_is_the_source(self):
        i18n.definir_langue("en")
        assert i18n.t("Oscilloscope") == "Oscilloscope"
        assert i18n.langue_courante() == "en"

    def test_a_plain_translation(self):
        i18n.definir_langue("fr")
        assert i18n.t("Multimeter") == "Multimètre"

    def test_an_unknown_label_falls_back_to_the_source(self):
        i18n.definir_langue("fr")
        assert i18n.t("a phrase that exists nowhere") == \
            "a phrase that exists nowhere"

    def test_what_is_missing_is_counted(self):
        i18n.definir_langue("fr")
        i18n.t("a label absent from the catalog, for the test")
        assert "a label absent from the catalog, for the test" \
            in i18n.missing("fr")

    def test_an_unknown_language_falls_back_to_the_source(self):
        assert i18n.definir_langue("klingon") == "en"

    def test_the_empty_string(self):
        i18n.definir_langue("fr")
        assert i18n.t("") == ""

    def test_reading_direction(self):
        assert i18n.meta("en")["direction"] == "ltr"
        assert i18n.meta("ar")["direction"] == "rtl"
        i18n.definir_langue("ar")
        assert i18n.direction_courante() == "rtl"

    def test_an_empty_value_counts_as_absent(self, tmp_path, monkeypatch):
        #  A half-filled catalog has to stay usable.
        dossier = tmp_path / "languages"
        dossier.mkdir()
        (dossier / "xx.json").write_text(json.dumps({
            "_langue": {"name": "Essai", "english_name": "test",
                        "direction": "ltr"},
            "Oscilloscope": "", "Multimeter": "Ceci"}), encoding="utf-8")
        monkeypatch.setattr(i18n, "DOSSIER", str(dossier))
        i18n._chargees.pop("xx", None)
        table = i18n.catalogue("xx")
        assert "Oscilloscope" not in table
        assert table["Multimeter"] == "Ceci"

    def test_a_missing_catalog_raises_nothing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(i18n, "DOSSIER", str(tmp_path))
        i18n._chargees.pop("zz", None)
        assert i18n.catalogue("zz") == {}


class TestTemplate:
    def test_writing_a_template(self, tmp_path):
        chemin = str(tmp_path / "xx.json")
        n = i18n.ecrire_modele(chemin, ["Un", "Deux"], "")
        assert n == 2
        donnees = json.load(open(chemin, encoding="utf-8"))
        assert donnees["Un"] == "" and donnees["Deux"] == ""
        assert "_langue" in donnees

    def test_filling_in_keeps_existing_translations(self, tmp_path):
        chemin = str(tmp_path / "fr.json")
        #  Starting from the real French catalog: known keys stay
        #  translated, new ones arrive empty.
        cles = ["Multimeter", "A brand-new label"]
        n = i18n.ecrire_modele(chemin, cles, "fr")
        donnees = json.load(open(chemin, encoding="utf-8"))
        assert donnees["Multimeter"] == "Multimètre"
        assert donnees["A brand-new label"] == ""
        assert n == 1


class TestInventory:
    def test_the_labels_are_found(self):
        cles = i18n.collecter_cles()
        assert len(cles) > 400
        for attendu in ("Oscilloscope", "Multimeter", "Compute now",
                        "enable speech mode", "Kalimba", "Time domain"):
            assert attendu in cles

    def test_no_duplicates(self):
        cles = i18n.collecter_cles()
        assert len(cles) == len(set(cles))

    def test_no_technical_key(self):
        #  A stylesheet or an object name in the catalog would mean the
        #  wrapping has slipped somewhere.
        for cle in i18n.collecter_cles():
            assert "color:" not in cle, cle
            assert not cle.startswith("#"), cle


class TestShippedCatalogs:
    def test_every_catalog_is_valid_json(self):
        for code in i18n.codes_presents():
            if code == i18n.LANGUE_SOURCE:
                continue
            with open(i18n.chemin_catalogue(code), encoding="utf-8") as f:
                donnees = json.load(f)
            assert "_langue" in donnees, code
            for champ in ("name", "english_name", "direction"):
                assert donnees["_langue"].get(champ), f"{code}: {champ}"

    def test_every_present_catalog_is_declared(self):
        """A shipped language shows a readable name, not its code.

        This test said the opposite until 2026-09-22: it required a catalog
        for every **declared** language. That held while eleven were
        announced and eleven written; it stopped holding when the table began
        announcing forty-eight, thirty-seven of which are still to write.

        The useful direction is this one. A language declared without a
        catalog appears nowhere — `codes_presents()` keeps only what exists —
        so it misleads nobody. A language present but *not* declared, on the
        other hand, would show up in the menu under its code ("bn") instead
        of its name ("বাংলা"), which is a visible defect.
        """
        declarees = {code for code, _, _, _ in i18n.LIVREES}
        for code in i18n.codes_presents():
            assert code in declarees, (
                f"catalog “{code}” is present but missing from "
                f"LIVREES: it would show under its code, not its name")

    def test_the_language_table_has_no_duplicates(self):
        """No repeated code, native name, or French name.

        Asked for explicitly when the list was extended to forty-eight
        languages — and the list as supplied did contain repeats: "English"
        three times, "Hindi" three times, a dozen others twice. A duplicate
        code would silently hide a language, because the second entry wins in
        any dictionary built from the table.
        """
        codes = [c for c, _, _, _ in i18n.LIVREES]
        natifs = [n for _, n, _, _ in i18n.LIVREES]
        francais = [n for _, _, n, _ in i18n.LIVREES]
        for quoi, liste in (("code", codes), ("native name", natifs),
                            ("French name", francais)):
            doubles = sorted({x for x in liste if liste.count(x) > 1})
            assert not doubles, f"duplicate {quoi}(s): {doubles}"

    def test_every_declared_language_has_a_reading_direction(self):
        """And it is "ltr" or "rtl", nothing else.

        Three of them read right to left: Arabic, Hebrew and Persian. A typo
        here breaks nothing visibly — it simply lays the interface out
        backwards for those three.
        """
        for code, _, _, direction in i18n.LIVREES:
            assert direction in ("ltr", "rtl"), f"{code}: {direction!r}"
        rtl = {c for c, _, _, d in i18n.LIVREES if d == "rtl"}
        assert rtl == {"ar", "he", "fa"}, rtl

    def test_every_catalog_is_complete(self):
        """Every shipped catalog translates all of the labels."""
        cles = i18n.collecter_cles()
        for code in i18n.codes_presents():
            if code == i18n.LANGUE_SOURCE:
                continue
            table = i18n.catalogue(code)
            absents = [c for c in cles if not table.get(c)]
            assert not absents, (
                f"{code}: {len(absents)} untranslated label(s), "
                f"for instance {absents[:3]}")

    def test_substitution_fields_are_preserved(self):
        """A translation that loses a {field} would raise KeyError in use."""
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
                assert attendus == obtenus, f"{code}: “{cle}”"

    def test_no_stale_key(self):
        """A catalog must not keep labels the code has dropped."""
        connues = set(i18n.collecter_cles())
        for code in i18n.codes_presents():
            if code == i18n.LANGUE_SOURCE:
                continue
            with open(i18n.chemin_catalogue(code), encoding="utf-8") as f:
                donnees = json.load(f)
            perimees = [k for k in donnees
                        if not k.startswith("_") and k not in connues]
            assert not perimees, f"{code}: {perimees[:3]}"


class TestFirstLaunch:
    """On first launch the interface is in English — without exception.

    Two separate claims, and both are deliberate.

    **The default is the source language.** It was French until 2026-09-22,
    when the repository moved to English and French became one catalog among
    the others. A default that is the source language cannot be missing or
    half-translated, which is the only defensible property for a first launch.

    **The software does not consult the system locale** (`C-31`). A machine
    whose environment says `fr_FR` may be a shared workstation, a cloned
    image, or a bench where the work is done in English. Guessing produces a
    program that has to be reconfigured, and does it behind the back of
    whoever is using it. The installers ask the question instead, at the very
    beginning, and write the answer down.

    These tests exist so that automatic detection is not added by accident.
    """

    def test_fresh_settings(self):
        from phytoscope.config import Settings
        assert Settings().ui.language == "en"

    def test_no_settings_file_at_all(self, tmp_path):
        from phytoscope.config import Settings
        s = Settings.load(str(tmp_path / "absent.json"))
        assert s.ui.language == "en"

    def test_a_file_without_the_language_key(self, tmp_path):
        #  A file written by a version predating the translation work.
        from phytoscope.config import Settings
        chemin = tmp_path / "reglages.json"
        chemin.write_text(json.dumps({"ui": {"theme": "clair"}}), encoding="utf-8")
        s = Settings.load(str(chemin))
        assert s.ui.theme == "clair"
        assert s.ui.language == "en"

    def test_a_corrupt_file(self, tmp_path):
        from phytoscope.config import Settings
        chemin = tmp_path / "reglages.json"
        chemin.write_text("{this is not JSON", encoding="utf-8")
        assert Settings.load(str(chemin)).ui.language == "en"

    def test_the_system_locale_has_no_influence(self, monkeypatch):
        from phytoscope.config import Settings
        for variable in ("LANG", "LC_ALL", "LC_MESSAGES", "LANGUAGE"):
            monkeypatch.setenv(variable, "ja_JP.UTF-8")
        assert Settings().ui.language == "en"
        assert i18n.definir_langue(Settings().ui.language) == "en"
        assert i18n.t("Multimeter") == "Multimeter"

    def test_an_empty_or_absent_language(self):
        assert i18n.definir_langue("") == "en"
        assert i18n.definir_langue(None) == "en"

    def test_the_users_choice_is_kept(self, tmp_path):
        from phytoscope.config import Settings
        chemin = str(tmp_path / "reglages.json")
        s = Settings()
        s.ui.language = "ja"
        s.save(chemin)
        assert Settings.load(chemin).ui.language == "ja"


class TestLanguageChosenAtInstallTime:
    """The language picked during installation, and whether it survives.

    The installers ask the question first thing and write the answer into the
    settings, which the software then reads back. These tests cover the link
    between them — `tools/write_language.py` — and the installers' label
    catalog.
    """

    def _tool(self):
        import importlib.util
        chemin = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "tools", "write_language.py")
        spec = importlib.util.spec_from_file_location("write_language", chemin)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_it_writes_the_language(self, tmp_path):
        outil = self._tool()
        cible = tmp_path / "reglages.json"
        assert outil.ecrire("ja", str(cible)) == 0
        assert json.loads(cible.read_text(encoding="utf-8"))["ui"]["language"] == "ja"

    def test_it_merges_without_erasing(self, tmp_path):
        """Reinstalling must change the language and nothing else.

        This is the whole reason the tool exists: patching a JSON file with
        `sed` from three different installers would sooner or later write
        over the settings of whoever uses the software.
        """
        outil = self._tool()
        cible = tmp_path / "reglages.json"
        cible.write_text(json.dumps({
            "ui": {"theme": "nuit", "language": "fr"},
            "audio_out": {"volume": 0.8},
        }), encoding="utf-8")
        assert outil.ecrire("ko", str(cible)) == 0
        d = json.loads(cible.read_text(encoding="utf-8"))
        assert d["ui"]["language"] == "ko"
        assert d["ui"]["theme"] == "nuit"          # kept
        assert d["audio_out"]["volume"] == 0.8     # kept

    def test_it_refuses_an_unknown_code(self, tmp_path):
        outil = self._tool()
        cible = tmp_path / "reglages.json"
        assert outil.ecrire("klingon", str(cible)) == 2
        assert not cible.exists()

    def test_an_unreadable_file_is_not_a_blocker(self, tmp_path):
        """Fresh settings beat refusing to write the language."""
        outil = self._tool()
        cible = tmp_path / "reglages.json"
        cible.write_text("ceci n'est pas du json", encoding="utf-8")
        assert outil.ecrire("ar", str(cible)) == 0
        assert json.loads(cible.read_text(encoding="utf-8"))["ui"]["language"] == "ar"

    def test_the_accepted_codes_are_the_softwares(self):
        """A shipped language the tool refused would be unreachable.

        The tool reads the codes off disk rather than carrying a copy of the
        list, so this check is no longer about two lists agreeing — it is
        about the reading working at all. A hardcoded fourth list was removed
        on 2026-09-23 for exactly that reason: nothing failed when it went
        stale, the code was simply refused.
        """
        outil = self._tool()
        livrees = {c for c, *_ in i18n.langues_disponibles()}
        connues = set(outil.langues_connues())
        assert livrees <= connues, (
            f"shipped but refused: {livrees - connues}")

    def test_the_source_language_needs_no_catalogue(self):
        """English ships no catalogue file, and must still be accepted."""
        outil = self._tool()
        assert i18n.LANGUE_SOURCE in outil.langues_connues()

    def test_the_first_launch_flag_is_never_written(self, tmp_path, monkeypatch):
        """It observes the launch; it is not a setting.

        Writing it would make the next launch believe it is still the first —
        and the language question would come back forever.
        """
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        from phytoscope.config import Settings
        premier = Settings.load()
        assert premier.premier_lancement is True
        premier.save()
        ecrit = json.loads((tmp_path / "phytoscope" / "reglages.json")
                           .read_text(encoding="utf-8"))
        assert "premier_lancement" not in ecrit
        assert Settings.load().premier_lancement is False


class TestInstallerCatalog:
    """The installers' label catalog, in every language the software ships."""

    def _catalog(self):
        #  tests/ -> src/phytoscope/ -> src/ -> the repository root.
        racine = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))))
        chemin = os.path.join(racine, "packaging", "languages",
                              "installateur.json")
        if not os.path.exists(chemin):
            pytest.skip("installer catalog absent from this working copy")
        with open(chemin, encoding="utf-8") as f:
            return json.load(f)

    def test_every_software_language_has_every_label(self):
        """An installer must not go mute in a language the software speaks.

        That is the requirement, and it reads in this direction: the
        languages are the **software's** — the installer catalog stopped
        declaring its own on 2026-09-22 — and each of them must translate all
        fifty-one labels. A missing label would render an empty shell
        variable, which is a blank line in the middle of an installation.
        """
        d = self._catalog()
        codes = [c for c, *_ in i18n.langues_disponibles()]
        assert codes, "no shipped language at all?"
        for cle, traductions in d["libelles"].items():
            manquantes = [c for c in codes if not traductions.get(c)]
            assert not manquantes, (
                f"{cle}: missing in {', '.join(manquantes)} — the installer "
                f"would be mute where the software speaks")

    def test_substitution_fields_survive_translation(self):
        """A lost {field} would print truncated text."""
        import re
        d = self._catalog()
        champs = re.compile(r"\{(\w+)\}")
        for cle, traductions in d["libelles"].items():
            reference = set(champs.findall(traductions["fr"]))
            for code, texte in traductions.items():
                assert set(champs.findall(texte)) == reference, (
                    f"{cle} [{code}]: fields {set(champs.findall(texte))} "
                    f"instead of {reference}")

    def test_the_catalog_no_longer_declares_its_languages(self):
        """There is one list of languages now, and it is the software's.

        The catalog used to carry a second one, `_langues`, which a test
        compared against the software's. Comparing means noticing the drift
        after the fact; removing the second list prevents it. This test keeps
        that door shut: if `_langues` comes back, somebody has started
        maintaining two lists again.
        """
        d = self._catalog()
        assert "_langues" not in d, (
            "the catalog declares its own languages again: the list must come "
            "from the software, via packaging/languages.langues_du_logiciel()")
