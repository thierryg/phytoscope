# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tests/test_portabilite.py
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
FIRMWARE = os.path.normpath(os.path.join(
    RACINE, "..", "..", "sources", "firmware-phytosense", "phytosense-fw",
    "usb_descriptors.c"))


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
    autorises = {"polices.py", "theme.py"}      # la pile de replis vit là
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

    C'est `commun.py` et non `construire.py` : le second n'est qu'un
    aiguillage vers les générateurs de chaque système, tandis que le premier
    porte l'identité du logiciel et les gabarits, qui sont ce qu'on vérifie
    ici.
    """
    import importlib.util
    chemin = os.path.normpath(os.path.join(RACINE, "..", "..", "packaging",
                                           "commun.py"))
    if not os.path.exists(chemin):
        pytest.skip("packaging/commun.py absent de cette copie de travail")
    spec = importlib.util.spec_from_file_location("commun", chemin)
    module = importlib.util.module_from_spec(spec)
    #  Inscrire le module AVANT de l'exécuter : `@dataclass` va chercher
    #  `sys.modules[cls.__module__]` pour résoudre les annotations, et
    #  échouerait sur un module encore absent.
    import sys as _sys
    _sys.modules["commun"] = module
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
        ("linux", "entete.sh"), ("linux", "interface.sh"),
        ("debian", "icone-bureau.sh"), ("debian", "desinstaller.sh"),
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
                         ("macos", "Info.plist"), ("linux", "entete.sh")):
        if nom == "entete.sh":
            #  Comme le fait le générateur : la couche d'affichage est un
            #  fragment inséré, dont les propres jetons sont remplis d'abord.
            couche = c.remplir(os.path.join(c.GABARITS, "linux",
                                            "interface.sh"), valeurs)
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
    """L'éditeur, l'auteur et ses coordonnées vivent dans `phytoscope/AUTEURS`.

    Le logiciel, la fabrique de paquets et la génération du certificat lisent
    tous ce fichier. Une copie ailleurs finirait par diverger — c'est
    exactement ce qui était arrivé au numéro de version.
    """
    from phytoscope.version import (AUTHOR, AUTHOR_EMAIL, AUTHOR_NAME,
                                    FICHIER_AUTEURS, lire_le_fichier_auteurs)
    assert os.path.exists(FICHIER_AUTEURS), \
        "le fichier AUTEURS doit voyager avec le paquet"
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
        assert '"AUTEURS"' in f.read(), \
            "AUTEURS doit figurer dans package-data, sinon une roue le perd"


def test_la_cle_privee_nentre_jamais_dans_le_depot():
    """Une clé privée dans un dépôt est une clé publiée."""
    racine = os.path.normpath(os.path.join(RACINE, "..", ".."))
    gitignore = os.path.join(racine, ".gitignore")
    if not os.path.exists(gitignore):
        pytest.skip(".gitignore absent de cette copie de travail")
    with open(gitignore, encoding="utf-8") as f:
        regles = f.read()
    assert "*.key" in regles
    assert "certificat/phytoscope.key" in regles

    #  Et le certificat déposé à la racine ne doit contenir QUE du public.
    public = os.path.join(racine, "phytoscope-certificat.pem")
    if os.path.exists(public):
        with open(public, encoding="utf-8") as f:
            contenu = f.read()
        assert "PRIVATE KEY" not in contenu, \
            "le fichier déposé à la racine contient une clé privée"
        assert "BEGIN CERTIFICATE" in contenu
