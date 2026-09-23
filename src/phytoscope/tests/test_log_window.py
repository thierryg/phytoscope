# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_log_window.py
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

"""La fenêtre du journal : elle doit suivre le fichier, pas le relire.

Ce qui est vérifié ici, c'est le comportement qu'on ne voit pas : la lecture
incrémentale, le rattrapage après une rotation, et le fait qu'une fenêtre
fermée cesse vraiment d'interroger le disque.
"""
from __future__ import annotations

import os

import pytest

pytest.importorskip("PySide6")

from phytoscope.core import logging_setup as jl          # noqa: E402
from phytoscope.ui.log_window import (LIGNES_MAX, LogWindow,               # noqa: E402
                                      fichiers_de_rotation)
from phytoscope.ui.theme import palette                  # noqa: E402


@pytest.fixture()
def journal(tmp_path, qapp):
    """Un journal isolé — jamais celui de l'utilisateur."""
    chemin = str(tmp_path / "phytoscope.log")
    jl.setup(level="INFO", path=chemin)
    yield chemin, jl.get_logger("essai")
    jl.setup(level="ERROR", path=str(tmp_path / "apres.log"))


def _vider_le_tampon() -> None:
    for h in jl.get_logger().handlers:
        h.flush()


def test_la_fenetre_montre_le_chemin_du_fichier(journal, qapp):
    chemin, log = journal
    log.info("bonjour")
    _vider_le_tampon()
    f = LogWindow(palette("sombre"))
    assert f.lab_chemin.text() == chemin
    assert "bonjour" in f.vue.toPlainText()


def test_les_lignes_ecrites_ensuite_apparaissent(journal, qapp):
    """Le temps réel : sans rouvrir, sans relire tout le fichier."""
    _chemin, log = journal
    log.info("avant")
    _vider_le_tampon()
    f = LogWindow(palette("sombre"))
    position = f._position
    log.warning("après")
    _vider_le_tampon()
    f._rafraichir()
    contenu = f.vue.toPlainText()
    assert "avant" in contenu and "après" in contenu
    assert f._position > position          # on a bien avancé, pas recommencé


def test_la_lecture_est_incrementale(journal, qapp):
    """On ne relit que l'ajout : c'est ce qui rend la surveillance gratuite."""
    _chemin, log = journal
    for i in range(20):
        log.info("ligne %d", i)
    _vider_le_tampon()
    f = LogWindow(palette("sombre"))
    tout = f._position
    log.info("une de plus")
    _vider_le_tampon()
    avant = f._position
    f._rafraichir()
    assert avant == tout
    assert 0 < f._position - avant < 200   # une seule ligne relue, pas vingt


def test_un_fichier_qui_rapetisse_est_relu_depuis_le_debut(journal, qapp):
    """Rotation ou vidage : lire à l'ancienne position couperait une ligne."""
    _chemin, log = journal
    for i in range(10):
        log.info("ancienne ligne %d", i)
    _vider_le_tampon()
    f = LogWindow(palette("sombre"))
    assert "ancienne ligne 9" in f.vue.toPlainText()
    jl.clear()
    log.info("toute neuve")
    _vider_le_tampon()
    f._rafraichir()
    contenu = f.vue.toPlainText()
    assert "toute neuve" in contenu
    assert "ancienne ligne" not in contenu


def test_le_filtre_ne_garde_que_les_lignes_voulues(journal, qapp):
    _chemin, log = journal
    log.info("un renseignement")
    log.error("un incident")
    _vider_le_tampon()
    f = LogWindow(palette("sombre"))
    f.filtre.setText("incident")
    contenu = f.vue.toPlainText()
    assert "un incident" in contenu
    assert "un renseignement" not in contenu
    f.filtre.setText("")
    assert "un renseignement" in f.vue.toPlainText()


def test_la_copie_reprend_le_fichier_a_lidentique(journal, qapp, tmp_path):
    chemin, log = journal
    log.error("à conserver")
    _vider_le_tampon()
    cible = tmp_path / "copie.log"
    import shutil
    shutil.copyfile(chemin, str(cible))
    assert "à conserver" in cible.read_text(encoding="utf-8")
    assert cible.stat().st_size == os.path.getsize(chemin)


def test_les_archives_de_rotation_sont_retrouvees(journal, qapp, tmp_path):
    chemin, log = journal
    log.info("courant")
    _vider_le_tampon()
    for i in (1, 2):
        open(f"{chemin}.{i}", "w", encoding="utf-8").write(f"archive {i}\n")
    trouves = fichiers_de_rotation(chemin)
    assert trouves == [chemin, f"{chemin}.1", f"{chemin}.2"]
    assert fichiers_de_rotation("") == []


def test_une_fenetre_fermee_ninterroge_plus_le_disque(journal, qapp):
    """Une minuterie qui tourne pour une fenêtre invisible est une faute."""
    _chemin, log = journal
    log.info("peu importe")
    _vider_le_tampon()
    f = LogWindow(palette("sombre"))
    f.show()
    assert f.timer.isActive()
    f.hide()
    assert not f.timer.isActive()


def test_le_nombre_de_lignes_affichees_est_borne(journal, qapp):
    """Un journal de 200 000 lignes ne doit pas figer l'interface."""
    _chemin, log = journal
    f = LogWindow(palette("sombre"))
    assert f.vue.maximumBlockCount() == LIGNES_MAX


def test_la_taille_est_dite_en_octets_quand_le_fichier_est_petit(journal, qapp):
    chemin, log = journal
    log.error("court")
    _vider_le_tampon()
    f = LogWindow(palette("sombre"))
    f._rafraichir(force=True)
    assert " o," in f.lab_etat.text() or " o " in f.lab_etat.text()


class TestTheme:
    """The palette, and the stylesheet built from it.

    Why this class exists. `theme.py` builds a Qt stylesheet by interpolating
    palette entries into an f-string:

        gridline-color: {p['grille']};

    The palette key is `grid`, and has always been. So that line raised
    `KeyError: 'grille'` every time the stylesheet was built — a crash at
    startup, reported on 2026-09-22 with a fatal-error dialog saying nothing
    but `'grille'`.

    Nothing caught it, because an f-string is not checked by anything: not by
    the linter, not by the type checker, and not by a test that never builds
    the stylesheet. So this one builds it, for every theme.
    """

    def test_every_theme_has_the_same_keys(self):
        """A key present in one palette and absent from another is a crash.

        The stylesheet is the same text for all three themes, so any key it
        reads must exist in all three.
        """
        from phytoscope.ui import theme
        reference = None
        for nom in theme.PALETTES:
            cles = set(theme.PALETTES[nom])
            if reference is None:
                reference, premier = cles, nom
                continue
            assert cles == reference, (
                f"{nom} and {premier} do not declare the same keys: "
                f"{cles ^ reference}")

    def test_every_theme_builds_its_stylesheet(self):
        """The test the 'grille' crash needed, and did not have."""
        from phytoscope.ui import theme
        for nom in theme.PALETTES:
            feuille = theme.stylesheet(nom)
            assert feuille and len(feuille) > 500, nom
            #  A Qt stylesheet is CSS, so it is full of braces: asserting
            #  that none remain was wrong, and this test failed on its first
            #  run for that reason. What matters is that no *placeholder*
            #  survived — `{p[` is the shape one would take.
            assert "{p[" not in feuille, f"{nom}: placeholder left unresolved"
            #  And that the palette really was interpolated: every colour is
            #  a hex triplet, so at least a few must appear.
            import re
            couleurs = re.findall(r"#[0-9A-Fa-f]{6}", feuille)
            assert len(couleurs) >= 8, f"{nom}: only {len(couleurs)} colours"

    def test_the_stylesheet_reads_no_key_that_does_not_exist(self):
        """Read the source and check every `p['…']` against the palette.

        Building the stylesheet would already fail on a missing key, so this
        is belt and braces — but it names the offending key and line, which
        a bare KeyError does not.
        """
        import ast
        import os
        import re
        from phytoscope.ui import theme

        chemin = os.path.join(os.path.dirname(os.path.abspath(theme.__file__)),
                              "theme.py")
        with open(chemin, encoding="utf-8") as f:
            source = f.read()

        definies = set()
        for noeud in ast.walk(ast.parse(source)):
            if isinstance(noeud, ast.Dict):
                for cle in noeud.keys:
                    if isinstance(cle, ast.Constant) and \
                            isinstance(cle.value, str):
                        definies.add(cle.value)

        lues = set(re.findall(r"p\[['\"](\w+)['\"]\]", source))
        absentes = sorted(lues - definies)
        assert not absentes, (
            f"the stylesheet reads {absentes}, which no palette declares")
