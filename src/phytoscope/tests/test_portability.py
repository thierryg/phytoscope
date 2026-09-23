# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_portability.py
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

"""Portabilité : ce qui doit rester vrai sur les trois systèmes.

Ces essais tournent sous Linux, mais ils vérifient des propriétés qui ne se
voient qu'ailleurs — une police sans repli, un chemin construit à la main, un
identifiant USB qui a cessé de suivre le micrologiciel. Les attraper ici coûte
une seconde ; les attraper sur la machine d'un utilisateur coûte une soirée.
"""
from __future__ import annotations

import ast
import os
import re

import pytest

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAQUET = os.path.join(RACINE, "phytoscope")
#  Le micrologiciel a quitté `sources/` lors du rangement du 2026-09-18 :
#  ce n'était pas de la matière de référence, c'est notre développement.
#  RACINE désigne src/phytoscope/, donc son voisin est src/firmware/.
FIRMWARE = os.path.normpath(os.path.join(
    RACINE, "..", "firmware", "usb_descriptors.c"))


def _sources_python():
    for dossier, _, fichiers in os.walk(PAQUET):
        if "__pycache__" in dossier:
            continue
        for nom in sorted(fichiers):
            if nom.endswith(".py"):
                chemin = os.path.join(dossier, nom)
                with open(chemin, encoding="utf-8") as f:
                    yield chemin, f.read()


# ---------------------------------------------------------------------------
#  Identifiants USB
# ---------------------------------------------------------------------------
def test_les_identifiants_usb_suivent_le_micrologiciel():
    """Le logiciel cherchait la carte là où elle n'est pas.

    Le micrologiciel fixe le couple VID/PID ; le logiciel le suit. L'inverse
    n'a aucun sens, et la divergence ne se voit qu'avec une carte en main —
    d'où cet essai, qui lit la source du micrologiciel.
    """
    if not os.path.exists(FIRMWARE):
        pytest.skip("micrologiciel absent de cette copie de travail")
    source = open(FIRMWARE, encoding="utf-8").read()
    vid = int(re.search(r"#define\s+PHYTO_VID\s+(0x[0-9A-Fa-f]+)", source).group(1), 16)
    pid = int(re.search(r"#define\s+PHYTO_PID\s+(0x[0-9A-Fa-f]+)", source).group(1), 16)

    from phytoscope.config import DiagnosticsSettings
    from phytoscope.core import protocol, usbdiag
    assert (protocol.USB_VID, protocol.USB_PID) == (vid, pid)
    assert (usbdiag.PHYTOSENSE_VID, usbdiag.PHYTOSENSE_PID) == (vid, pid)
    d = DiagnosticsSettings()
    assert (d.expected_vid, d.expected_pid) == (vid, pid)
    assert (vid, pid) in usbdiag.CARTES_CONNUES


def test_le_vid_appartient_a_la_plage_libre():
    """`0x2E8A` est à Raspberry Pi ; nous n'avons aucun titre à y attribuer
    un PID. `0x1209` est la plage de pid.codes, faite pour cela."""
    from phytoscope.core import protocol
    assert protocol.USB_VID == 0x1209


# ---------------------------------------------------------------------------
#  Chemins
# ---------------------------------------------------------------------------
def test_aucun_chemin_nest_construit_par_concatenation():
    """Un `+ "/"` fonctionne sous Unix et casse sous Windows."""
    motif = re.compile(r'\+\s*["\']/')
    fautes = [f"{c}:{i}" for c, src in _sources_python()
              for i, ligne in enumerate(src.splitlines(), 1)
              if motif.search(ligne) and "http" not in ligne]
    assert not fautes, "chemins concaténés : " + ", ".join(fautes)


def test_aucun_open_texte_sans_encodage():
    """Sous Windows, `open()` sans `encoding=` lit en cp1252 : les accents des
    catalogues et des journaux deviennent illisibles."""
    fautes = []
    for chemin, source in _sources_python():
        for noeud in ast.walk(ast.parse(source, chemin)):
            if not (isinstance(noeud, ast.Call)
                    and isinstance(noeud.func, ast.Name)
                    and noeud.func.id == "open"):
                continue
            mode = ""
            if len(noeud.args) > 1 and isinstance(noeud.args[1], ast.Constant):
                mode = str(noeud.args[1].value)
            for mc in noeud.keywords:
                if mc.arg == "mode" and isinstance(mc.value, ast.Constant):
                    mode = str(mc.value.value)
            if "b" in mode:                      # le binaire n'a pas d'encodage
                continue
            if not any(mc.arg == "encoding" for mc in noeud.keywords):
                fautes.append(f"{os.path.basename(chemin)}:{noeud.lineno}")
    assert not fautes, "open() sans encoding : " + ", ".join(fautes)


# ---------------------------------------------------------------------------
#  Polices
# ---------------------------------------------------------------------------
def test_aucune_police_nest_nommee_en_dur():
    """« DejaVu Sans Mono » n'existe ni sous Windows ni sous macOS.

    Nommée sans repli, Qt lui substitue souvent une police **proportionnelle**,
    et l'alignement des colonnes de valeurs disparaît. Tout passe donc par
    `ui.polices`, qui déclare une pile de replis et le rôle de la police.
    """
    autorises = {"fonts.py", "theme.py"}      # la pile de replis vit là
    fautes = [f"{os.path.basename(c)}:{i}" for c, src in _sources_python()
              for i, ligne in enumerate(src.splitlines(), 1)
              if "DejaVu" in ligne and os.path.basename(c) not in autorises]
    assert not fautes, "police codée en dur : " + ", ".join(fautes)


# ---------------------------------------------------------------------------
#  Appels système réservés à un seul système
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("interdit", [
    "os.statvfs",       # absent de Windows — `shutil.disk_usage` est portable
    "os.uname",         # absent de Windows
    "os.system",        # coquille du shell, dépend du système
    "signal.SIGHUP", "signal.SIGQUIT", "signal.SIGUSR1", "signal.SIGALRM",
    "import fcntl", "import termios", "import pwd", "import grp",
    "import resource",
])
def test_pas_dappel_reserve_a_unix(interdit):
    fautes = [f"{os.path.basename(c)}:{i}" for c, src in _sources_python()
              for i, ligne in enumerate(src.splitlines(), 1)
              if interdit in ligne and not ligne.lstrip().startswith("#")]
    assert not fautes, f"{interdit} : " + ", ".join(fautes)


# ---------------------------------------------------------------------------
#  Empaquetage
# ---------------------------------------------------------------------------
def _construire():
    """L'outillage commun de la fabrique, importé sans rien construire.

    C'est `common.py` et non `build.py` : le second n'est qu'un
    aiguillage vers les générateurs de chaque système, tandis que le premier
    porte l'identité du logiciel et les gabarits, qui sont ce qu'on vérifie
    ici.
    """
    import importlib.util
    chemin = os.path.normpath(os.path.join(RACINE, "..", "..", "packaging",
                                           "common.py"))
    if not os.path.exists(chemin):
        pytest.skip("packaging/common.py absent de cette copie de travail")
    spec = importlib.util.spec_from_file_location("common", chemin)
    module = importlib.util.module_from_spec(spec)
    #  Inscrire le module AVANT de l'exécuter : `@dataclass` va chercher
    #  `sys.modules[cls.__module__]` pour résoudre les annotations, et
    #  échouerait sur un module encore absent.
    import sys as _sys
    _sys.modules["common"] = module
    spec.loader.exec_module(module)
    return module


def test_les_paquets_annoncent_la_bonne_version():
    """Un paquet estampillé d'une version fausse est pire qu'aucun paquet."""
    c = _construire()
    from phytoscope.version import VERSION
    assert c.Identite.lire().version == VERSION


def test_pyproject_ne_declare_plus_de_version_figee():
    """Elle était restée à 1.0.0 pendant cinq versions : elle est désormais
    lue dans `phytoscope/version.py`, seule source de vérité."""
    with open(os.path.join(RACINE, "pyproject.toml"), encoding="utf-8") as f:
        texte = f.read()
    assert 'dynamic = ["version"]' in texte
    assert re.search(r'^version\s*=\s*"', texte, re.M) is None


def test_les_gabarits_dempaquetage_sont_tous_la():
    c = _construire()
    attendus = [
        ("debian", "control"), ("debian", "postinst"), ("debian", "prerm"),
        ("debian", "lanceur"), ("debian", "phytoscope.desktop"),
        ("fedora", "phytoscope.spec"),
        ("windows", "phytoscope.nsi"), ("windows", "phytoscope.wxs"),
        ("windows", "PhytoScope.cmd"), ("windows", "Diagnostic.cmd"),
        ("macos", "Info.plist"), ("macos", "lanceur"), ("macos", "postinstall"),
        ("linux", "header.sh"), ("linux", "frontend.sh"),
        ("debian", "desktop-icon.sh"), ("debian", "uninstall.sh"),
    ]
    for dossier, nom in attendus:
        chemin = os.path.join(c.GABARITS, dossier, nom)
        assert os.path.exists(chemin), f"gabarit manquant : {dossier}/{nom}"


def test_aucun_jeton_ne_reste_dans_un_gabarit_rempli():
    """Un « @VERSION@ » oublié produirait un paquet à la version littérale."""
    c = _construire()
    id_ = c.Identite.lire()
    #  Le MÊME jeu de jetons que les générateurs : c'est justement ce qu'on
    #  veut éprouver. Le construire à la main ici laisserait passer un jeton
    #  ajouté à un gabarit mais oublié dans `Identite.jetons()`.
    valeurs = dict(id_.jetons(), ARCH="all", TAILLE="1000",
                   DATE_RPM="Thu Jan 01 2026")
    for dossier, nom in (("debian", "control"), ("fedora", "phytoscope.spec"),
                         ("macos", "Info.plist"), ("linux", "header.sh")):
        if nom == "header.sh":
            #  Comme le fait le générateur : la couche d'affichage est un
            #  fragment inséré, dont les propres jetons sont remplis d'abord.
            couche = c.remplir(os.path.join(c.GABARITS, "linux",
                                            "frontend.sh"), valeurs)
            valeurs = dict(valeurs, EMPREINTE="0" * 64, LIGNES="1",
                           COUCHE_INTERFACE=couche)
        rempli = c.remplir(os.path.join(c.GABARITS, dossier, nom), valeurs)
        #  Le motif exact des jetons, celui que `remplir()` remplace. Chercher
        #  un simple « @ » signalerait à tort les adresses de courriel et les
        #  commentaires du gabarit qui décrivent la syntaxe.
        restants = re.findall(r"@[A-Z_]+@", rempli)
        assert not restants, \
            f"jeton non remplacé dans {dossier}/{nom} : {restants}"
        assert id_.version in rempli


def test_le_contenu_empaquete_existe_reellement():
    c = _construire()
    for nom in c.CONTENU:
        assert os.path.exists(os.path.join(c.LOGICIEL, nom)), \
            f"{nom} est annoncé dans le paquet mais absent des sources"


def test_les_essais_ne_partent_pas_dans_le_paquet():
    """Un utilisateur n'a que faire des essais, et ils pèsent."""
    c = _construire()
    assert "tests" not in c.CONTENU
    assert "tools" not in c.CONTENU


def test_la_version_vient_dun_seul_fichier():
    """Le logiciel, les paquets et l'outil de publication lisent le MÊME
    endroit : `phytoscope/VERSION`.

    Tant que le numéro était écrit en Python, `pyproject.toml` en gardait une
    copie qui a dérivé pendant cinq versions — elle annonçait encore 1.0.0.
    """
    from phytoscope.version import (FICHIER_VERSION, RELEASE_DATE,
                                    RELEASE_NAME, VERSION,
                                    lire_le_fichier_version)
    assert os.path.exists(FICHIER_VERSION), \
        "le fichier VERSION doit voyager avec le paquet"
    brut = lire_le_fichier_version()
    assert brut["version"] + brut.get("suffixe", "") == VERSION
    assert brut["nom"] == RELEASE_NAME
    assert brut["date"] == RELEASE_DATE

    #  La fabrique lit la même chose.
    c = _construire()
    assert c.Identite.lire().version == VERSION

    #  Et la déclaration de données du paquet l'emporte avec le logiciel.
    with open(os.path.join(RACINE, "pyproject.toml"), encoding="utf-8") as f:
        assert '"VERSION"' in f.read(), \
            "VERSION doit figurer dans package-data, sinon une roue le perd"


def test_un_fichier_version_absent_narrete_pas_le_logiciel():
    """Un numéro de version illisible est un ennui, pas une panne."""
    from phytoscope.version import lire_le_fichier_version
    assert lire_le_fichier_version("/chemin/qui/nexiste/pas") == {}


def test_lattribution_vient_dun_seul_fichier():
    """L'éditeur, l'auteur et ses coordonnées vivent dans `phytoscope/AUTHORS`.

    Le logiciel, la fabrique de paquets et la génération du certificat lisent
    tous ce fichier. Une copie ailleurs finirait par diverger — c'est
    exactement ce qui était arrivé au numéro de version.
    """
    from phytoscope.version import (AUTHOR, AUTHOR_EMAIL, AUTHOR_NAME,
                                    FICHIER_AUTEURS, lire_le_fichier_auteurs)
    assert os.path.exists(FICHIER_AUTEURS), \
        "le fichier AUTHORS doit voyager avec le paquet"
    brut = lire_le_fichier_auteurs()
    assert brut["editeur"] == AUTHOR
    assert brut["auteur"] == AUTHOR_NAME
    assert brut["courriel"] == AUTHOR_EMAIL

    c = _construire()
    id_ = c.Identite.lire()
    assert id_.editeur == AUTHOR
    assert id_.auteur == AUTHOR_NAME
    assert id_.responsable == f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>"

    with open(os.path.join(RACINE, "pyproject.toml"), encoding="utf-8") as f:
        assert '"AUTHORS"' in f.read(), \
            "AUTHORS doit figurer dans package-data, sinon une roue le perd"


def test_la_cle_privee_nentre_jamais_dans_le_depot():
    """Une clé privée dans un dépôt est une clé publiée."""
    racine = os.path.normpath(os.path.join(RACINE, "..", ".."))
    gitignore = os.path.join(racine, ".gitignore")
    if not os.path.exists(gitignore):
        pytest.skip(".gitignore absent de cette copie de travail")
    with open(gitignore, encoding="utf-8") as f:
        regles = f.read()
    assert "*.key" in regles
    assert "certificate/phytoscope.key" in regles

    #  Et le certificat déposé à la racine ne doit contenir QUE du public.
    public = os.path.join(racine, "phytoscope-certificate.pem")
    if os.path.exists(public):
        with open(public, encoding="utf-8") as f:
            contenu = f.read()
        assert "PRIVATE KEY" not in contenu, \
            "le fichier déposé à la racine contient une clé privée"
        assert "BEGIN CERTIFICATE" in contenu


# ---------------------------------------------------------------------------
#  La nomenclature du projet, et le certificat
# ---------------------------------------------------------------------------
def _charger(chemin_relatif):
    """Charge un script du dépôt par son chemin ; None s'il est absent."""
    import importlib.util
    depot = os.path.dirname(os.path.dirname(RACINE))
    chemin = os.path.join(depot, chemin_relatif)
    if not os.path.exists(chemin):
        return None
    spec = importlib.util.spec_from_file_location(
        os.path.basename(chemin).replace(".py", "") + "_essai", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestNomenclatureDuProjet:
    """`tools/sbom.py` — logiciel ET micrologiciel.

    Ce que ces essais protègent : les versions du micrologiciel sont **lues**
    dans `_make_.sh` et `CMakeLists.txt`, jamais recopiées dans un tableau.
    Une version écrite à la main vieillirait en silence, et un SBOM faux est
    pire qu'aucun SBOM — il sert à répondre « cette faille me concerne-t-elle ? ».
    """

    def _module(self):
        m = _charger(os.path.join("tools", "sbom.py"))
        if m is None:
            pytest.skip("tools/sbom.py absent de cette copie de travail")
        return m

    def test_la_version_du_sdk_est_lue_et_non_ecrite(self):
        m = self._module()
        firmware = {d["nom"]: d for d in m.inventaire_firmware()}
        sdk = firmware.get("pico-sdk")
        assert sdk is not None, "le Pico SDK doit figurer à la nomenclature"
        assert sdk["version"] != "—", (
            "version du Pico SDK non lue — SDK_VERSION a-t-il changé de nom "
            "dans src/firmware/_make_.sh ?")
        #  Elle doit être celle du fichier, et non une constante du script.
        attendue = m._lire_version(
            os.path.join(m.FIRMWARE, "_make_.sh"), "SDK_VERSION")
        assert sdk["version"] == attendue

    def test_tinyusb_suit_la_version_du_sdk(self):
        """Elle est livrée *dans* le SDK : lui donner un numéro à part
        serait l'inventer."""
        m = self._module()
        firmware = {d["nom"]: d for d in m.inventaire_firmware()}
        assert firmware["tinyusb"]["version"] == firmware["pico-sdk"]["version"]

    def test_les_outils_de_construction_ne_sont_pas_embarques(self):
        """Le compilateur ARM construit le produit, il n'y est pas dedans.

        La distinction compte pour qui lit ce document afin de savoir si une
        faille le concerne : `scope: excluded` le dit.
        """
        m = self._module()
        firmware = {d["nom"]: d for d in m.inventaire_firmware()}
        assert firmware["arm-gnu-toolchain"]["scope"] == "excluded"
        assert firmware["picotool"]["scope"] == "excluded"
        assert firmware["pico-sdk"]["scope"] == "required"

    def test_les_bibliotheques_liees_sont_lues_dans_cmake(self):
        m = self._module()
        liees = m.bibliotheques_liees()
        assert liees, "aucune bibliothèque lue dans CMakeLists.txt"
        #  Celles-là sont indispensables au micrologiciel : leur disparition
        #  de la liste signalerait un CMakeLists.txt mal lu.
        for indispensable in ("pico_stdlib", "tinyusb_device"):
            assert indispensable in liees, f"{indispensable} attendue"
        assert "phytosense" not in liees, "le nom de la cible n'est pas une lib"
        assert "PRIVATE" not in liees, "les mots-clés CMake ne sont pas des libs"

    def test_le_document_separe_logiciel_et_micrologiciel(self):
        m = self._module()
        doc = m.en_cyclonedx(m.inventaire_logiciel(), m.inventaire_firmware())
        assert doc["bomFormat"] == "CycloneDX"
        types = {c["type"] for c in doc["components"]}
        assert types == {"application", "firmware"}, (
            "les deux natures de produit doivent rester séparables")

    def test_la_signature_ignore_l_horodatage(self):
        """Sinon il y aurait une révision par jour, sans qu'un composant
        ait bougé."""
        m = self._module()
        a = m.en_cyclonedx(m.inventaire_logiciel(), m.inventaire_firmware())
        b = m.en_cyclonedx(m.inventaire_logiciel(), m.inventaire_firmware())
        assert a["metadata"]["timestamp"] != b["metadata"]["timestamp"] \
            or a["serialNumber"] != b["serialNumber"]
        assert m._signature(a) == m._signature(b)


class TestCertificat:
    """`packaging/certificate.py` — les emplacements et les garde-fous."""

    def _module(self):
        m = _charger(os.path.join("packaging", "certificate.py"))
        if m is None:
            pytest.skip("packaging/certificate.py absent de cette copie")
        return m

    def test_la_cle_de_travail_reste_dans_certificat(self):
        """`C-2R` n'autorise la clé privée qu'à deux endroits."""
        m = self._module()
        assert os.path.basename(os.path.dirname(m.CLE_TRAVAIL)) == "certificate"
        assert m.CLE_TRAVAIL.endswith("phytoscope.key")

    def test_le_certificat_public_va_dans_certificat_et_non_a_la_racine(self):
        """Il était déposé à la racine du dépôt, ce qui en faisait un doublon
        que personne ne savait à jour."""
        m = self._module()
        import importlib.util
        assert os.path.basename(os.path.dirname(m.PUBLIC)) == "certificate"
        signature = _charger(os.path.join("packaging", "signature.py"))
        if signature is not None:
            assert os.path.basename(
                os.path.dirname(signature.CERTIFICAT_PROJET)) == "certificate"

    def test_le_depot_refuse_sans_copie_de_reference(self, monkeypatch):
        """Créer une clé est une décision, pas un effet de bord."""
        m = self._module()
        import packaging  # noqa: F401  (au cas où le nom existe)
        monkeypatch.setattr(m.signature, "certificat_existe", lambda: False)
        assert m.deposer() is False

    def test_proposer_ne_cree_rien_sans_terminal(self, monkeypatch):
        """Sur une machine d'intégration continue, ce serait une clé
        éphémère qu'on croirait permanente."""
        m = self._module()
        monkeypatch.setattr(m.signature, "certificat_existe", lambda: False)
        cree = []
        monkeypatch.setattr(m, "creer", lambda *a, **k: cree.append(1) or True)
        monkeypatch.setattr(m.sys.stdin, "isatty", lambda: False, raising=False)
        assert m.proposer_si_absent() is False
        assert not cree, "aucune clé ne doit être créée sans accord explicite"

    def test_proposer_ne_demande_rien_si_le_certificat_est_la(self, monkeypatch):
        m = self._module()
        monkeypatch.setattr(m.signature, "certificat_existe", lambda: True)
        assert m.proposer_si_absent() is True


class TestScriptsDuMicrologiciel:
    """`_make_.sh` compile, `build.sh` range le livrable.

    Deux scripts et deux rôles : `_make_.sh` pour la mise au point — on
    compile vingt fois d'affilée et ranger un livrable à chaque fois n'a
    aucun sens —, `build.sh` pour la publication. Ces essais protègent la
    séparation, sans compiler quoi que ce soit : la chaîne croisée ARM n'est
    pas une dépendance de la suite de tests.
    """

    def _firmware(self):
        chemin = os.path.normpath(os.path.join(RACINE, "..", "firmware"))
        if not os.path.isdir(chemin):
            pytest.skip("micrologiciel absent de cette copie de travail")
        return chemin

    def test_les_deux_scripts_existent_et_sont_executables(self):
        d = self._firmware()
        for nom in ("_make_.sh", "build.sh"):
            chemin = os.path.join(d, nom)
            assert os.path.exists(chemin), f"{nom} manquant"
            assert os.access(chemin, os.X_OK), f"{nom} n'est pas exécutable"

    def test_make_porte_la_version_du_sdk(self):
        """C'est lui qui la fixe, et `tools/sbom.py` la lit là."""
        source = open(os.path.join(self._firmware(), "_make_.sh"),
                      encoding="utf-8").read()
        assert re.search(r'^\s*SDK_VERSION\s*=', source, re.M), (
            "SDK_VERSION a disparu de _make_.sh — tools/sbom.py ne saura "
            "plus quelle version du Pico SDK est en service")

    def test_build_delegue_la_compilation(self):
        """Il ne réimplémente pas cmake : il appelle `_make_.sh`."""
        source = open(os.path.join(self._firmware(), "build.sh"),
                      encoding="utf-8").read()
        assert "_make_.sh" in source
        assert "cmake --build" not in source, (
            "build.sh ne doit pas compiler lui-même — c'est le travail "
            "de _make_.sh, et deux implémentations divergeraient")

    def test_build_lit_la_version_la_ou_elle_fait_foi(self):
        source = open(os.path.join(self._firmware(), "build.sh"),
                      encoding="utf-8").read()
        assert "phytoscope/VERSION" in source, (
            "la version doit être lue dans VERSION, jamais écrite ici")
        #  Une version en dur serait un mensonge le jour du prochain bump.
        assert not re.search(r'VERSION="\d+\.\d+\.\d+"', source)

    def test_build_suit_la_sortie_de_la_fabrique(self):
        """Lancé par `make all`, le micrologiciel doit se ranger dans la
        MÊME fabrication que les .deb et les .msi."""
        source = open(os.path.join(self._firmware(), "build.sh"),
                      encoding="utf-8").read()
        assert "PHYTOSCOPE_OUTPUT" in source

    def test_make_jette_un_cache_cmake_perime(self):
        """Un cache retient le chemin ABSOLU des sources : déplacer la copie
        de travail le rend périmé, et cmake refuse de continuer. C'est
        arrivé au rangement du 2026-09-18."""
        source = open(os.path.join(self._firmware(), "_make_.sh"),
                      encoding="utf-8").read()
        assert "CMAKE_HOME_DIRECTORY" in source, (
            "la détection du cache périmé a disparu — la compilation "
            "échouera au prochain déplacement du dépôt")

    def test_les_deux_scripts_sont_du_shell_valide(self):
        """Une coquille de syntaxe ne se voit qu'à l'exécution."""
        import subprocess
        d = self._firmware()
        for nom in ("_make_.sh", "build.sh"):
            r = subprocess.run(["sh", "-n", os.path.join(d, nom)],
                               capture_output=True, text=True)
            assert r.returncode == 0, f"{nom} : {r.stderr.strip()}"


class TestLaFabriqueDeSesGenerateurs:
    """`build.py` names its generators as STRINGS, so nothing checks them.

    The rename pass of 2026-09-22 turned `construire_debian.py` into
    `build_debian.py` and could not see the string that names it: `build.py`
    went on calling `__import__("construire_debian")`. Every target then died
    on a `ModuleNotFoundError` that the dispatcher merely **logged** — it
    printed "0 target(s)", wrote its five documents, produced no package, and
    exited 1 with a message nobody reads in a log.

    The Makefile was unaffected, because it calls the scripts by path. So the
    defect only showed up through `build.py`, which is the documented entry
    point. Found on 2026-09-23 while analysing the impact of renaming the
    Makefile targets.

    These tests read the list out of the source and import each module for
    real. Nothing is built.
    """

    def _packaging(self):
        chemin = os.path.normpath(os.path.join(RACINE, "..", "..", "packaging"))
        if not os.path.isdir(chemin):
            pytest.skip("packaging absent de cette copie de travail")
        return chemin

    def _modules_cites(self):
        """The module names `build.py` hands to `__import__`."""
        source = open(os.path.join(self._packaging(), "build.py"),
                      encoding="utf-8").read()
        arbre = ast.parse(source)
        #  The list is a literal of (key, module, options) tuples; we read the
        #  second element of each, which is the module name.
        noms = []
        for n in ast.walk(arbre):
            if not isinstance(n, ast.Tuple) or len(n.elts) != 3:
                continue
            cle, module = n.elts[0], n.elts[1]
            if (isinstance(cle, ast.Constant) and isinstance(cle.value, str)
                    and isinstance(module, ast.Constant)
                    and isinstance(module.value, str)):
                noms.append(module.value)
        return noms

    def test_build_cite_bien_cinq_generateurs(self):
        noms = self._modules_cites()
        assert len(noms) == 5, f"attendu 5 generateurs, trouve {noms}"

    def test_chaque_generateur_cite_existe_sur_le_disque(self):
        """A string that names no file is a target that cannot run."""
        d = self._packaging()
        for nom in self._modules_cites():
            chemin = os.path.join(d, f"{nom}.py")
            assert os.path.isfile(chemin), (
                f"build.py importe « {nom} », absent de packaging/")

    def test_chaque_generateur_cite_offre_un_main(self):
        """`build.py` calls `generateur.main(options)`."""
        d = self._packaging()
        for nom in self._modules_cites():
            source = open(os.path.join(d, f"{nom}.py"), encoding="utf-8").read()
            assert re.search(r"^def main\(", source, re.M), (
                f"{nom}.py n'offre pas de main()")


class TestThePackageFactorysMakefile:
    """`packaging/Makefile` — the three things that broke in it.

    All three were found on 2026-09-23, and all three were silent:

      1. `.DEFAULT_GOAL := aide` survived the rename of 2026-09-22. A bare
         `make` — the first thing a newcomer types — died on "No rule to make
         target 'aide'".
      2. `make verify` on its own **created** an empty timestamped build and
         repointed `latest` at it, because `$(OUTPUT)` carries the current
         invocation's timestamp and `dossier_fabrication()` makes what it is
         asked for. Verifying a build therefore destroyed it.
      3. `make deliverables` produced a build that `make verify` refused:
         `all` writes the documents per system directory, `firmware` then
         creates `Firmware/`, and nothing wrote into it.

    These tests read the Makefile rather than run it — building takes a
    quarter of an hour and needs NSIS — except the one that runs `make -n`,
    which touches nothing.
    """

    def _makefile(self):
        path = os.path.normpath(os.path.join(RACINE, "..", "..", "packaging",
                                             "Makefile"))
        if not os.path.isfile(path):
            pytest.skip("packaging/Makefile is absent from this working copy")
        return path

    def _phony(self, text):
        m = re.search(r"^\.PHONY:(.*?)(?<!\\)$", text, re.M | re.S)
        assert m, "no .PHONY in the Makefile"
        return m.group(1).replace("\\", " ").split()

    def test_the_default_goal_is_a_target_that_exists(self):
        """A bare `make` must work: it is the first thing anybody types."""
        text = open(self._makefile(), encoding="utf-8").read()
        m = re.search(r"^\.DEFAULT_GOAL\s*:=\s*(\S+)", text, re.M)
        assert m, "no .DEFAULT_GOAL declared"
        goal = m.group(1)
        assert re.search(rf"^{re.escape(goal)}:", text, re.M), (
            f".DEFAULT_GOAL is “{goal}”, which is not a target of this "
            "Makefile — a bare `make` would fail")

    def test_every_phony_target_is_defined(self):
        """The CI checks this too; here it costs nothing and runs offline."""
        path = self._makefile()
        text = open(path, encoding="utf-8").read()
        undefined = [t for t in self._phony(text)
                     if not re.search(rf"^{re.escape(t)}:", text, re.M)]
        assert not undefined, (
            f"declared .PHONY but never defined: {undefined}")

    def test_the_after_the_fact_targets_do_not_use_a_fresh_timestamp(self):
        """`documents`, `verify`, `checksums` and `sign` work on an
        EXISTING build.

        The regression to prevent: they used `$(OUTPUT)`, which carries this
        invocation's timestamp, so each one named a directory that did not
        exist — and creating it moved `latest` onto an empty build.
        """
        text = open(self._makefile(), encoding="utf-8").read()
        assert "TARGET_DIR" in text, (
            "the after-the-fact targets no longer resolve their directory")
        for target in ("documents", "verify", "checksums", "sign"):
            m = re.search(rf"^{target}:\n((?:\t.*\n)+)", text, re.M)
            assert m, f"target {target} not found"
            body = m.group(1)
            assert "$(TARGET_DIR)" in body, (
                f"`{target}` does not use $(TARGET_DIR): a bare "
                f"`make {target}` would invent a new build")
            assert "$(OUTPUT)" not in body, (
                f"`{target}` still uses $(OUTPUT), which carries a fresh "
                "timestamp")

    def test_deliverables_writes_the_documents_after_the_firmware(self):
        """Otherwise `Firmware/` has none, and `make verify` refuses."""
        text = open(self._makefile(), encoding="utf-8").read()
        m = re.search(r"^deliverables:(.*)\n((?:\t.*\n)+)", text, re.M)
        assert m, "the deliverables target was not found"
        assert "firmware" in m.group(1), "deliverables no longer builds the firmware"
        assert "documents" in m.group(2), (
            "`deliverables` does not run `documents` after `firmware`: the "
            "Firmware/ directory would carry none, and `make verify` refuses "
            "exactly that")

    def test_the_documents_are_written_into_every_subdirectory(self):
        """`verify.py` walks the directories; the writer must too.

        `verify.py` asks every subdirectory of a build for the four
        documents. `common.ecrire_les_documents` used to write into the three
        names of `SYSTEMES`, so a fourth directory was checked and never
        written.
        """
        path = os.path.normpath(os.path.join(RACINE, "..", "..", "packaging",
                                             "common.py"))
        if not os.path.isfile(path):
            pytest.skip("packaging/common.py is absent from this working copy")
        source = open(path, encoding="utf-8").read()
        body = re.search(r"def ecrire_les_documents\(.*?\n(?=def |\Z)",
                         source, re.S)
        assert body, "ecrire_les_documents was not found"
        assert "os.listdir(base)" in body.group(0), (
            "ecrire_les_documents does not read the build's directories: a "
            "directory verify.py checks would go unwritten")

    def test_make_dry_runs_every_target(self):
        """`make -n` parses the whole file and resolves every prerequisite."""
        import subprocess
        path = self._makefile()
        text = open(path, encoding="utf-8").read()
        broken = []
        for target in self._phony(text):
            done = subprocess.run(["make", "-n", "-C", os.path.dirname(path),
                                   target],
                                  capture_output=True, text=True)
            if done.returncode:
                broken.append((target, done.stderr.strip().splitlines()[:1]))
        assert not broken, f"targets that do not even dry-run: {broken}"


class TestTheReleaseToolLeavesTheChangelogIntact:
    """`release.py bump` writes into CHANGELOG.txt. It must not damage it.

    On 2026-09-23 it did. It looked for a separator of 78 "=" characters;
    the journal's banners are 80 long. So the pattern matched the first 78
    characters of the banner on line 1, split the file in the middle of it,
    inserted the new section **above the journal's own header**, and left two
    orphan "=" twelve lines further down.

    `release.py check` passed throughout: it verifies that a section for the
    version exists and that "(à compléter)" is gone, not that the file it
    wrote still reads. A release tool that quietly mangles the file it
    maintains is the kind of defect that is found by whoever downloads the
    release.

    These tests run the real function on a copy, and read the result.
    """

    def _tool(self):
        import importlib.util
        path = os.path.join(RACINE, "tools", "release.py")
        if not os.path.isfile(path):
            pytest.skip("tools/release.py is absent from this working copy")
        spec = importlib.util.spec_from_file_location("release_under_test",
                                                      path)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        return tool

    def _changelog(self, tmp_path):
        import shutil
        source = os.path.join(RACINE, "CHANGELOG.txt")
        if not os.path.isfile(source):
            pytest.skip("CHANGELOG.txt is absent from this working copy")
        target = str(tmp_path / "CHANGELOG.txt")
        shutil.copy(source, target)
        return target

    def test_the_new_section_goes_after_the_header(self, tmp_path):
        tool = self._tool()
        path = self._changelog(tmp_path)
        tool.CHANGELOG = path
        before = open(path, encoding="utf-8").read().split("\n")
        tool.changelog_open_section("9.9.9", "2026-01-01", "trial")
        after = open(path, encoding="utf-8").read().split("\n")

        #  The header is whatever precedes the first version section.
        head_before = before[:next(i for i, l in enumerate(before)
                                   if tool.HEADER_RE.match(l))]
        head_after = after[:next(i for i, l in enumerate(after)
                                 if tool.HEADER_RE.match(l))]
        assert head_after == head_before, (
            "the header changed; the section was inserted into it")

    def test_no_separator_is_cut_in_half(self, tmp_path):
        """A banner that loses two characters is how the defect showed."""
        tool = self._tool()
        path = self._changelog(tmp_path)
        tool.CHANGELOG = path
        widths_before = {len(l) for l in open(path, encoding="utf-8")
                         .read().split("\n") if l and set(l) == {"="}}
        tool.changelog_open_section("9.9.9", "2026-01-01", "trial")
        widths_after = {len(l) for l in open(path, encoding="utf-8")
                        .read().split("\n") if l and set(l) == {"="}}
        assert widths_after == widths_before, (
            f"the separator widths changed: {sorted(widths_before)} -> "
            f"{sorted(widths_after)}")

    def test_the_previous_sections_are_all_still_there(self, tmp_path):
        tool = self._tool()
        path = self._changelog(tmp_path)
        tool.CHANGELOG = path
        text = open(path, encoding="utf-8").read()
        before = [m.group(1) for m in tool.HEADER_RE.finditer(text)]
        tool.changelog_open_section("9.9.9", "2026-01-01", "trial")
        after = [m.group(1) for m in
                 tool.HEADER_RE.finditer(open(path, encoding="utf-8").read())]
        assert after == ["9.9.9"] + before, (
            "the new section must come first, and lose none of the others")

    def test_the_shipped_changelog_opens_on_the_version_in_VERSION(self):
        """What `release.py check` does not check: they must agree."""
        tool = self._tool()
        version = tool.read_version()["string"] if hasattr(tool, "read_version") \
            else None
        text = open(os.path.join(RACINE, "CHANGELOG.txt"),
                    encoding="utf-8").read()
        first = tool.HEADER_RE.search(text)
        assert first, "no version section in CHANGELOG.txt"
        if version:
            assert first.group(1) == version, (
                f"CHANGELOG.txt opens on {first.group(1)}, VERSION says "
                f"{version}")


class TestEveryAllIsHonest:
    """`__all__` must name only things the module actually has.

    A name in `__all__` that does not exist is not caught by an import of the
    module: it only bites on `from … import *`, which raises `AttributeError`
    naming the first one it cannot find. Nothing in this repository does a
    star import, so three of them sat there unnoticed — `phytoscope.api` and
    `phytoscope.api.contract` each claimed `Analyser`, `Descriptor` and
    `Quantity` while the classes were still called `Analyseur`,
    `Descripteur` and `Grandeur`, and `core/quantities.py` claimed a
    `Quantity` it has never had.

    They were the residue of a rename that stopped halfway, and they were a
    fair warning of it: `__all__` is the module's own statement of its public
    surface, and a statement nothing checks drifts. Found on 2026-09-23 while
    renaming the API to English.
    """

    def _modules(self):
        import importlib
        import pkgutil
        found = []
        pkg = importlib.import_module("phytoscope")
        for info in pkgutil.walk_packages(pkg.__path__, "phytoscope."):
            #  The UI needs a display; the modules directory is loaded by the
            #  registry, not by import. Neither declares `__all__`.
            if ".ui." in info.name or ".modules." in info.name:
                continue
            found.append(info.name)
        assert len(found) > 20, f"only {len(found)} modules walked"
        return found

    def test_no_module_promises_what_it_does_not_have(self):
        import importlib
        liars = []
        for name in self._modules():
            try:
                mod = importlib.import_module(name)
            except Exception:                              # noqa: BLE001
                continue        # an optional dependency, not our business
            for exported in getattr(mod, "__all__", ()):
                if not hasattr(mod, exported):
                    liars.append(f"{name}.__all__ names “{exported}”")
        assert not liars, ("`__all__` names something absent:\n  "
                           + "\n  ".join(liars))

    def test_the_api_exports_the_whole_contract(self):
        """`phytoscope.api` is the only surface a module may import from."""
        import phytoscope.api as api
        for name in ("API_VERSION", "compatible", "parse_version",
                     "Manifest", "Module",
                     "Capability", "Analyser", "Descriptor", "Sonifier",
                     "Exporter", "Source", "Quantity", "Trace",
                     "ProposedNote", "Context", "MeasurementState",
                     "BUS", "EVENTS"):
            assert name in api.__all__, f"{name} is missing from api.__all__"
            assert hasattr(api, name), f"{name} is not importable from api"


class TestTheSdkSkeletonGenerator:
    """`new_module.py` writes the first module anybody will read.

    It has to keep working even when the software is *not* installed, so it
    holds its own copy of what it needs — the capability names, the ones the
    host really calls, and the path to the contract it reads `API_VERSION`
    from. Those are duplicates, and a duplicate drifts.

    It had already drifted: the path said `src/software/phytoscope`, a
    directory that has never existed. `api_version()` caught the `OSError`,
    fell back to "2.0", and said nothing; on a 2.1 host the generated module
    would have claimed 2.0 — loadable, but a version behind, and nobody would
    have known why. Found on 2026-09-23 while finishing the SDK.

    These tests read the generator, run it into a temporary directory, and
    hand what it wrote to the software's own manifest reader. Nothing is
    installed, and the user's configuration is never touched.
    """

    EXPECTED_CAPABILITIES = ("analyser", "descriptor", "sonifier",
                             "exporter")

    def _generator(self):
        path = os.path.normpath(os.path.join(RACINE, "..", "sdk", "tools",
                                             "new_module.py"))
        if not os.path.isfile(path):
            pytest.skip("src/sdk is absent from this working copy")
        import importlib.util
        spec = importlib.util.spec_from_file_location("sdk_new_module", path)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        return tool

    def test_the_contract_it_reads_is_on_the_disk(self):
        """A path that names no file is a silent fallback."""
        path = self._generator().contract_path()
        assert os.path.isfile(path), (
            f"new_module.py reads API_VERSION from \u201c{path}\u201d, which "
            "does not exist: it would fall back without saying so")

    def test_it_writes_the_softwares_own_api_version(self):
        """What it writes into a manifest has to be what the host offers."""
        from phytoscope.api import API_VERSION
        assert self._generator().api_version() == API_VERSION

    def test_every_capability_it_offers_is_one_the_contract_knows(self):
        """A capability the contract ignores is a module never called."""
        from phytoscope.api import Capability
        offered = set(self._generator().CAPABILITIES)
        assert offered == set(self.EXPECTED_CAPABILITIES)
        assert offered <= set(Capability.ALL), (
            "unknown to the contract: "
            f"{sorted(offered - set(Capability.ALL))}")

    def test_it_knows_which_capabilities_the_host_really_calls(self):
        """The SDK must not promise a capability nothing asks for.

        Of the contract's five, the host asks the registry for two:
        `providers(Capability.ANALYSEUR)` in `ui/tabs.py` and
        `providers(Capability.DESCRIPTEUR)` in `ui/features_tab.py`. A
        sonifier, an exporter or a source loads, shows as `actif`, and is
        never called — which costs its author an evening unless it is said
        out loud. `new_module.py` says it, and so do the SDK chapters.

        This test reads what the interface actually calls, and compares. The
        day somebody wires up the exporter, it fails and names what to update.
        """
        called = set()
        ui = os.path.join(PAQUET, "ui")
        for name in sorted(os.listdir(ui)):
            if not name.endswith(".py"):
                continue
            source = open(os.path.join(ui, name), encoding="utf-8").read()
            called |= set(re.findall(
                r"providers\(\s*Capability\.([A-Z_]+)", source))
        assert called, "no call to providers() found — is the read right?"

        from phytoscope.api import Capability
        consumed = {getattr(Capability, name) for name in called}
        announced = set(self._generator().CONSUMED)
        assert announced == consumed, (
            f"the host calls {sorted(consumed)}, new_module.py announces "
            f"{sorted(announced)} — update CONSUMED, "
            "src/sdk/docs/01-getting-started.md, docs/03-capabilities.md, "
            "pdf-src/writing-a-phytoscope-module/06-capabilities.html "
            "and .ai/state.md")

    @pytest.mark.parametrize("capability", EXPECTED_CAPABILITIES)
    def test_the_skeleton_it_writes_is_accepted_by_the_registry(self,
                                                                capability,
                                                                tmp_path):
        """The real reader, on the real file — not a regex of our own."""
        from phytoscope.api import compatible
        from phytoscope.api.registry import Registry

        tool = self._generator()
        name = f"probe-{capability}"
        assert tool.main([name, "--capability", capability,
                          "--in", str(tmp_path)]) == 0

        manifest = Registry(None, None)._read_manifest(
            str(tmp_path / name / "module.py"), name)
        assert manifest is not None, "the manifest was not read at all"
        assert manifest.problems() == [], manifest.problems()
        assert manifest.name == name
        assert compatible(manifest.api), (
            f"the host would refuse a module aiming at {manifest.api}")
        assert manifest.capabilities == (capability,)

    @pytest.mark.parametrize("capability", EXPECTED_CAPABILITIES)
    def test_the_tests_it_writes_parse(self, capability, tmp_path):
        """A skeleton whose tests do not even compile teaches the wrong thing."""
        tool = self._generator()
        name = f"probe-{capability}"
        assert tool.main([name, "--capability", capability,
                          "--in", str(tmp_path)]) == 0
        directory = tmp_path / name
        tests = directory / f"test_{name.replace('-', '_')}.py"
        assert tests.is_file(), f"{tests.name} was not written"
        for f in (directory / "module.py", tests):
            ast.parse(f.read_text(encoding="utf-8"), str(f))


class TestGitignoreProtegeLeDepotPublic:
    """Les règles qui gardent hors du dépôt ce qui n'a rien à y faire.

    Ce que ces essais protègent, et pourquoi ils existent : le 2026-09-18,
    **toute la section du `.gitignore` qui écarte les documents sous droits a
    disparu** au cours d'une réécriture par script. Résultat : 6 449 fichiers
    se sont retrouvés dans l'index, dont les cinq ouvrages sous droits et
    817 Mo d'archives tierces. Le dépôt est **public** ; rien n'avait encore
    été poussé, mais une clé ou un livre publiés ne se dépublient pas.

    Un `.gitignore` est du code : il se teste.
    """

    def _gitignore(self):
        depot = os.path.dirname(os.path.dirname(RACINE))
        chemin = os.path.join(depot, ".gitignore")
        if not os.path.exists(chemin):
            pytest.skip(".gitignore absent de cette copie de travail")
        return open(chemin, encoding="utf-8").read()

    @pytest.mark.parametrize("regle,pourquoi", [
        ("certificate/phytoscope.key", "la clé privée de signature (C-2R)"),
        ("*.key", "toute clé, où qu'elle soit"),
        ("*.pem", "idem — avec deux exceptions nommées plus bas"),
        ("sources/ebooks/", "cinq ouvrages sous droits"),
        ("sources/documents/scientific-articles/*.pdf",
         "articles payants — nos notes .md, elles, se publient"),
        ("sources/datasheets/*.pdf", "notices constructeurs"),
        ("sources/manufacturer-manuals/*.pdf", "manuels constructeurs"),
        ("sources/brevets/*.pdf", "brevets en fac-similé"),
        ("sources/documents/public-domain/*.pdf",
         "258 Mo de numérisations — libres, mais lourdes"),
        ("sources/code/*.zip", "dépôts tiers recopiés"),
        ("sources/software/**/*.zip", "817 Mo de dépôts tiers"),
        (".ecarte/", "doublons et environnements mis à l'écart"),
        ("/phytoscope/", "un clone du dépôt déposé dans le dépôt — "
                         "« git add -A » l'avalait comme sous-module"),
        ("build/", "PDF et paquets produits"),
        ("src/firmware/build/", "le SDK Pico récupéré, et les objets"),
    ])
    def test_la_regle_est_presente(self, regle, pourquoi):
        lignes = [l.strip() for l in self._gitignore().splitlines()]
        assert regle in lignes, (
            f"règle absente du .gitignore : {regle!r} — {pourquoi}")

    @pytest.mark.parametrize("exception,pourquoi", [
        ("!certificate/phytoscope-certificate.pem",
         "le certificat PUBLIC se diffuse : c'est lui qui vérifie une signature"),
        ("!certificate/phytoscope.crt", "idem, en brut"),
        ("!sources/software/MANIFESTE.md", "la provenance des dépôts tiers"),
        ("!src/phytoscope/sbom.cdx.json", "la nomenclature du logiciel"),
        ("!/sbom.cdx.json", "la nomenclature du projet"),
    ])
    def test_l_exception_est_presente(self, exception, pourquoi):
        """Interdire large puis réautoriser nommément : encore faut-il que
        les exceptions survivent aux réécritures."""
        lignes = [l.strip() for l in self._gitignore().splitlines()]
        assert exception in lignes, (
            f"exception absente : {exception!r} — {pourquoi}")

    def test_les_langages_et_systemes_demandes_sont_couverts(self):
        """Le `.gitignore` couvre bash, Python, Go, Rust, C/C++, Windows,
        macOS, Debian et Fedora. Une section perdue ne se voit pas."""
        contenu = self._gitignore()
        for repere in ("__pycache__/", ".venv/",          # Python
                       "*.o", "CMakeCache.txt",           # C/C++
                       "/target/", "*.rlib",              # Rust
                       "go.work", "*.test",               # Go
                       "Thumbs.db", "[Dd]esktop.ini",     # Windows
                       ".DS_Store", ".AppleDouble",       # macOS
                       "*.dsc", "*.changes",              # Debian
                       "*.rpmsave", "BUILDROOT/",         # Fedora
                       ".bash_history"):                  # bash
            assert repere in contenu, (
                f"{repere!r} absent — une section du .gitignore a-t-elle "
                f"disparu ?")


class TestReferencesDesActions:
    """Les `uses:` des workflows : épinglés, et pas des coquilles.

    Ce que ces essais protègent : le 2026-09-19, deux références du dépôt ne
    désignaient rien. `aquasecurity/trivy-action@0.28.0` — il fallait
    `v0.28.0` — a fait échouer « Analyse de l'arborescence (trivy) » dès
    « Set up job », donc **avant** que `continue-on-error: true` ne puisse
    s'appliquer : une action qui ne se résout pas n'est pas une étape qui
    échoue, c'est un travail qui ne démarre pas, et le contrôle de sécurité
    devient silencieux. `ossf/scorecard-action@v2` était morte aussi, mais
    son workflow ne tourne qu'à l'horaire : elle n'avait pas encore eu
    l'occasion de le montrer.

    L'existence d'une référence demande le réseau — c'est le travail de
    `tools/verify_actions.py`, lancé par la CI. Ce qui se vérifie **hors
    ligne**, et que ces essais vérifient, c'est la forme : une action tierce
    épinglée par empreinte de commit, et la version dite en clair à côté.
    """

    #  Publiées par GitHub : suivies par étiquette majeure, comme partout,
    #  parce que la chaîne d'approvisionnement est celle du coureur.
    MAISON = ("actions/", "github/")
    USES = re.compile(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)")
    EMPREINTE = re.compile(r"^[0-9a-f]{40}$")

    def _references(self):
        depot = os.path.dirname(os.path.dirname(RACINE))
        dossier = os.path.join(depot, ".github", "workflows")
        if not os.path.isdir(dossier):
            pytest.skip(".github/workflows absent de cette copie de travail")
        trouvees = []
        for nom in sorted(os.listdir(dossier)):
            if not nom.endswith((".yml", ".yaml")):
                continue
            chemin = os.path.join(dossier, nom)
            with open(chemin, encoding="utf-8") as f:
                for numero, ligne in enumerate(f, 1):
                    trouve = self.USES.match(ligne)
                    if not trouve:
                        continue
                    ref = trouve.group(1)
                    if ref.startswith(("./", "docker://")) or "@" not in ref:
                        continue
                    trouvees.append((ref, ligne.rstrip(), nom, numero))
        assert trouvees, "aucun « uses: » trouvé — la lecture est-elle bonne ?"
        return trouvees

    def test_l_outil_de_controle_existe(self):
        depot = os.path.dirname(os.path.dirname(RACINE))
        chemin = os.path.join(depot, "tools", "verify_actions.py")
        assert os.path.exists(chemin), (
            "tools/verify_actions.py a disparu — c'est lui qui interroge "
            "GitHub sur l'existence des références")

    def test_la_ci_lance_l_outil(self):
        depot = os.path.dirname(os.path.dirname(RACINE))
        chemin = os.path.join(depot, ".github", "workflows", "security.yml")
        if not os.path.exists(chemin):
            pytest.skip("security.yml absent de cette copie de travail")
        contenu = open(chemin, encoding="utf-8").read()
        assert "tools/verify_actions.py" in contenu, (
            "la CI ne lance plus le contrôle des références d'actions")

    def test_les_actions_tierces_sont_epinglees(self):
        """Une étiquette se déplace sous nos pieds ; une empreinte non."""
        flottantes = []
        for ref, _ligne, fichier, numero in self._references():
            chemin, _, version = ref.partition("@")
            if chemin.startswith(self.MAISON):
                continue
            if not self.EMPREINTE.match(version):
                flottantes.append(f"{fichier}:{numero} — {ref}")
        assert not flottantes, (
            "action(s) tierce(s) non épinglée(s) par empreinte de commit :\n  "
            + "\n  ".join(flottantes))

    def test_chaque_empreinte_dit_sa_version_en_clair(self):
        """Une empreinte seule est illisible : le commentaire la traduit.

        Sans « # v0.36.0 » à côté, personne ne sait quelle version tourne, et
        Dependabot n'a rien à mettre à jour de lisible.
        """
        muettes = []
        for ref, ligne, fichier, numero in self._references():
            version = ref.partition("@")[2]
            if not self.EMPREINTE.match(version):
                continue
            if not re.search(r"#\s*v?\d+\.\d+", ligne):
                muettes.append(f"{fichier}:{numero} — {ligne.strip()}")
        assert not muettes, (
            "empreinte(s) sans version en commentaire :\n  "
            + "\n  ".join(muettes))

    def test_aucune_reference_ne_pointe_sur_une_branche_mouvante(self):
        """`@main` ou `@master` : le code exécuté change sans qu'on décide."""
        fautives = []
        for ref, _ligne, fichier, numero in self._references():
            if ref.partition("@")[2] in ("main", "master", "HEAD"):
                fautives.append(f"{fichier}:{numero} — {ref}")
        assert not fautives, (
            "référence(s) sur une branche mouvante :\n  "
            + "\n  ".join(fautives))


class TestEveryPaletteKeyAskedForExists:
    """A colour asked for but not defined stops the software from starting.

    `theme.py` holds three palettes, and every widget reads a colour out of
    them by name. A `KeyError` there is not a wrong colour: it is raised while
    the window is being built, so the user sees a fatal-error dialog with the
    missing key as its whole message and an application that never opens.

    This is what happened on 2026-09-23: eight call sites had been translated
    to `p["alert"]` while the three palettes still spelled it `"alerte"`. The
    391 tests then in the suite all passed, because not one of them built a
    widget. The check below reads the source rather than the screen, which is
    what makes it cheap enough to keep.
    """

    UI = os.path.join(RACINE, "phytoscope", "ui")

    def _palettes(self):
        from phytoscope.ui.theme import PALETTES
        return PALETTES

    def _keys_asked_for(self):
        """Every `p["…"]` / `palette["…"]` in the package, with its place."""
        asked = {}
        for base, _dirs, files in os.walk(os.path.join(RACINE, "phytoscope")):
            for f in files:
                if not f.endswith(".py"):
                    continue
                chemin = os.path.join(base, f)
                with open(chemin, encoding="utf-8") as fh:
                    arbre = ast.parse(fh.read(), chemin)
                for n in ast.walk(arbre):
                    if not (isinstance(n, ast.Subscript)
                            and isinstance(n.slice, ast.Constant)
                            and isinstance(n.slice.value, str)):
                        continue
                    cible = n.value
                    nom = (cible.id if isinstance(cible, ast.Name)
                           else cible.attr if isinstance(cible, ast.Attribute)
                           else None)
                    if nom in ("p", "palette"):
                        asked.setdefault(n.slice.value, []).append(
                            f"{os.path.relpath(chemin, RACINE)}:{n.lineno}")
        return asked

    def test_every_key_a_widget_asks_for_is_in_every_palette(self):
        palettes = self._palettes()
        manquantes = []
        for cle, endroits in sorted(self._keys_asked_for().items()):
            for nom, palette in palettes.items():
                if cle not in palette:
                    manquantes.append(f"{cle!r} absent de « {nom} » "
                                      f"— demandé en {endroits[0]}")
        assert not manquantes, (
            "couleur(s) demandée(s) mais non définie(s) :\n  "
            + "\n  ".join(manquantes))

    def test_the_three_palettes_define_exactly_the_same_colours(self):
        """A colour that exists in one theme only breaks on the other two."""
        palettes = self._palettes()
        reference = None
        ecarts = []
        for nom, palette in palettes.items():
            if reference is None:
                reference = (nom, set(palette))
                continue
            manque = reference[1] - set(palette)
            surplus = set(palette) - reference[1]
            if manque or surplus:
                ecarts.append(f"« {nom} » vs « {reference[0]} » : "
                              f"manque {sorted(manque)}, en trop {sorted(surplus)}")
        assert not ecarts, "palettes désaccordées :\n  " + "\n  ".join(ecarts)

    def test_no_palette_key_is_still_spelled_in_french(self):
        """The vocabulary is US English, the palette included.

        It is also what keeps a half-finished rename visible: a `fond` left in
        one file and a `background` in the next is exactly the state that
        produced the crash.
        """
        FRANCAIS = {"fond", "fond2", "fond3", "trait", "texte", "texte2",
                    "or", "alerte", "couleur", "cadre"}
        fautives = []
        for nom, palette in self._palettes().items():
            for cle in sorted(set(palette) & FRANCAIS):
                fautives.append(f"« {nom} » définit {cle!r}")
        for cle, endroits in sorted(self._keys_asked_for().items()):
            if cle in FRANCAIS:
                fautives.append(f"{endroits[0]} demande {cle!r}")
        assert not fautives, (
            "clé(s) de palette encore en français :\n  " + "\n  ".join(fautives))


class TestEverySettingsFieldNamedExists:
    """`settings.modules.settings` was written where the field is `reglages`.

    Nothing refused it: Python creates the attribute on assignment and raises
    only on the read, inside the shutdown path, where a `try` logged it and
    carried on. The user lost every module setting at each exit and saw
    nothing — and the sibling defect, `modules.disabled = …`, wrote to an
    attribute nobody ever read.

    So the check is not "does it crash" but "is the name a declared field".
    `Settings` says which dataclass hides behind each of its own fields, and
    every `….<that field>.<name>` in the package is measured against it.
    """

    def _dataclasses_by_field(self):
        """`{"modules": ModulesSettings, "music": MusicSettings, …}`."""
        from dataclasses import fields, is_dataclass
        from phytoscope.config import Settings
        return {f.name: f.type if is_dataclass(f.type) else type(getattr(Settings(), f.name))
                for f in fields(Settings)
                if is_dataclass(type(getattr(Settings(), f.name)))}

    def test_no_line_names_a_settings_field_that_does_not_exist(self):
        from dataclasses import fields
        groupes = self._dataclasses_by_field()
        connus = {nom: {f.name for f in fields(cls)}
                  for nom, cls in groupes.items()}
        fautives = []
        for base, _dirs, files in os.walk(os.path.join(RACINE, "phytoscope")):
            for f in sorted(files):
                if not f.endswith(".py"):
                    continue
                chemin = os.path.join(base, f)
                with open(chemin, encoding="utf-8") as fh:
                    arbre = ast.parse(fh.read(), chemin)
                for n in ast.walk(arbre):
                    #  `<anything>.settings.modules.<name>`: the chain has to
                    #  start at a `Settings`, or the name means something else
                    #  — `self.modules` on the registry is a dict, and
                    #  `self.voice` on the engine is the voice itself.
                    if not (isinstance(n, ast.Attribute)
                            and isinstance(n.value, ast.Attribute)
                            and isinstance(n.value.value, ast.Attribute)
                            and n.value.value.attr == "settings"):
                        continue
                    groupe = n.value.attr
                    if groupe not in connus or n.attr in connus[groupe]:
                        continue
                    if n.attr.startswith("__"):
                        continue
                    fautives.append(
                        f"{os.path.relpath(chemin, RACINE)}:{n.lineno} — "
                        f"{groupe}.{n.attr} n'est pas un champ de "
                        f"{groupes[groupe].__name__} "
                        f"({', '.join(sorted(connus[groupe]))})")
        assert not fautives, (
            "réglage(s) nommé(s) mais inexistant(s) :\n  " + "\n  ".join(fautives))
