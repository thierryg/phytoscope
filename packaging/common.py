# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/common.py
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

"""Outillage commun aux générateurs de paquets.

Chaque système a son script — `build_debian.py`, `build_fedora.py`,
`build_windows.py`, `build_macos.py`, `build_source.py` — et
tous s'appuient sur ce module. On y trouve ce qui ne dépend d'aucune cible :

* l'**identité** du logiciel, lue à la source dans `phytoscope/version.py` ;
* le **recensement des outils** (`dpkg-deb`, `rpmbuild`, `makensis`, `wixl`) et
  leur installation dans le dossier personnel, sans `sudo` ;
* le **téléchargement des roues** d'une plateforme quelconque, qui est ce qui
  permet d'empaqueter pour Windows et macOS depuis Debian ;
* la fabrication des **icônes** `.ico` et `.icns`, rendues par Qt puis
  assemblées ici ;
* les petites choses partagées : copier le logiciel, remplir un gabarit,
  compresser en conservant les droits, calculer les empreintes.

Rien ici ne sait ce qu'est un `.deb` ou un `.msi` : cette connaissance vit dans
le script de chaque système, et nulle part ailleurs.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGICIEL = os.path.join(RACINE, "src", "phytoscope")
GABARITS = os.path.join(RACINE, "packaging", "gabarits")
#  Chaque fabrication a son dossier : « build/paquets/1.5.1-20260918-1345 ».
#  Motif : on garde ainsi plusieurs constructions d'une même version côte à
#  côte — celle d'avant un correctif et celle d'après — sans qu'un fichier en
#  écrase un autre, et l'on sait au nom près ce qu'on est en train de diffuser.
APP_TAGLINE = "Écoute, mesure et enregistrement des signaux végétaux"

RACINE_SORTIE = os.path.join(RACINE, "build", "paquets")

#  Le lien « dernier » pointe toujours sur la fabrication la plus récente :
#  c'est ce qu'on met dans un script de publication, plutôt qu'un nom qui
#  change à chaque fois.
LIEN_DERNIER = os.path.join(RACINE_SORTIE, "dernier")

#  Variable d'environnement qui impose le dossier. C'est par elle que
#  `build.py` fait converger toutes les cibles d'une même fabrication
#  vers un seul dossier : sans cela, chaque générateur en créerait un nouveau
#  et les paquets d'une même version se retrouveraient éparpillés.
VARIABLE_SORTIE = "PHYTOSCOPE_SORTIE"

_sortie_courante = ""

#  La version vit dans un fichier de données que le logiciel relit lui-même
#  au démarrage : paquet et fenêtre « À propos » ne peuvent pas diverger.
FICHIER_VERSION = os.path.join(LOGICIEL, "phytoscope", "VERSION")
#  L'attribution vit dans son propre fichier, lu aussi par le logiciel et par
#  la génération du certificat : une seule source, pas de copie à maintenir.
FICHIER_AUTEURS = os.path.join(LOGICIEL, "phytoscope", "AUTEURS")
MODULE_VERSION = os.path.join(LOGICIEL, "phytoscope", "version.py")


def lire_cle_valeur(chemin: str) -> Dict[str, str]:
    """Analyse un fichier « clé = valeur » — le format de VERSION et AUTEURS."""
    valeurs: Dict[str, str] = {}
    try:
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                ligne = ligne.strip()
                if not ligne or ligne.startswith("#") or "=" not in ligne:
                    continue
                cle, _, valeur = ligne.partition("=")
                valeurs[cle.strip().lower()] = valeur.strip()
    except OSError as exc:
        echec(f"{chemin} illisible : {exc}")
    return valeurs

#  Version de Python embarquée pour Windows. On la fixe plutôt que de suivre
#  la dernière parue : les roues de NumPy et de PySide6 arrivent avec quelques
#  mois de retard sur chaque nouvelle version, et un paquet qu'on ne peut pas
#  remplir n'a aucun intérêt.
PYTHON_WINDOWS = "3.11.9"
ABI_WINDOWS = "311"

#  ---------------------------------------------------------------------------
#  Python autonome pour Linux et macOS
#  ---------------------------------------------------------------------------
#  Windows a sa « distribution embarquable » officielle ; Linux et macOS n'ont
#  pas d'équivalent chez python.org. Sans interpréteur livré, l'installateur
#  .run et le .pkg macOS ne pouvaient qu'échouer en disant « installez
#  python3 » — ce qui n'est pas « prêt après l'installation », et ce qui exige
#  des privilèges que le projet s'interdit (C-55).
#
#  On livre donc CPython construit par « python-build-standalone » : des
#  binaires **relogeables**, qui se déplient dans n'importe quel dossier et
#  fonctionnent sans être installés, sans root et sans toucher au système.
#  La variante « install_only » est la plus petite qui contienne un
#  interpréteur complet avec `venv`, `ssl` et `pip`.
PYTHON_AUTONOME = "3.11.9"
PBS_TAG = "20240814"

#  Triplet de la chaîne de construction, par système et architecture.
CIBLES_PBS = {
    ("linux", "x86_64"):  "x86_64-unknown-linux-gnu",
    ("linux", "aarch64"): "aarch64-unknown-linux-gnu",
    ("linux", "arm64"):   "aarch64-unknown-linux-gnu",
    ("macos", "x86_64"):  "x86_64-apple-darwin",
    ("macos", "arm64"):   "aarch64-apple-darwin",
    ("macos", "aarch64"): "aarch64-apple-darwin",
}

#  Étiquettes de plateforme acceptées par pip pour chaque cible. On en donne
#  plusieurs : une roue peut être publiée sous « manylinux_2_28 » ou sous
#  l'ancien « manylinux2014 », et sous macOS la roue universelle cohabite avec
#  les roues par architecture.
PLATEFORMES: Dict[str, List[List[str]]] = {
    #  Une liste d'étiquettes par architecture à couvrir. Pour chacune, on
    #  essaie les étiquettes dans l'ordre et l'on garde la première qui donne
    #  une roue — de la plus précise à la plus large.
    "windows": [["win_amd64"]],
    #  macOS : une seule cible pour les deux architectures. Qt n'est publié
    #  qu'en « universal2 », c'est-à-dire en binaire double : le séparer
    #  donnerait deux paquets de 450 Mo contenant les mêmes 400 Mo de Qt.
    #  « universal2 » figure en REPLI de chaque architecture, et non comme une
    #  troisième passe : en passe séparée, on retéléchargeait les variantes
    #  universelles de NumPy en plus des natives, et le paquet passait de 500
    #  à 900 Mo pour rien.
    "macos": [["macosx_11_0_x86_64", "macosx_10_9_x86_64",
               "macosx_11_0_universal2", "macosx_10_9_universal2"],
              ["macosx_11_0_arm64", "macosx_11_0_universal2"]],
    "linux": [["manylinux_2_28_x86_64", "manylinux2014_x86_64",
               "manylinux_2_17_x86_64"]],
}

#  Versions de Python à couvrir pour les paquets qui utilisent l'interpréteur
#  de la machine cible. Une roue de NumPy vaut pour une seule version mineure ;
#  or Debian 11 livre 3.9, Ubuntu 22.04 livre 3.10, Ubuntu 24.04 livre 3.12 et
#  Fedora 41 livre 3.13. Ne couvrir que celle de la machine qui empaquette
#  reviendrait à livrer 450 Mo de bibliothèques inutilisables.
#  PySide6 échappe à cela : ses roues sont « abi3 », valables de 3.9 à 3.13.
PYTHONS_COUVERTS = ("3.9", "3.10", "3.11", "3.12", "3.13")

#  macOS n'a pas de dépôt de distribution : l'utilisateur installe Python par
#  Homebrew ou depuis python.org, qui livrent tous deux des versions récentes.
#  Couvrir 3.9 et 3.10 y serait du poids pour personne.
PYTHONS_MACOS = ("3.11", "3.12", "3.13")

#  Ce qui part dans le paquet. Les essais et l'outillage restent dehors : ils
#  pèsent, et l'utilisateur d'un paquet ne les lance pas.
CONTENU = ["phytoscope", "run.py", "requirements.txt",
           "requirements-optionnel.txt", "README.txt", "CHANGELOG.txt",
           "LICENCE.txt", "pyproject.toml"]

VERT, JAUNE, ROUGE, GRIS, NEUTRE = (
    "\033[0;32m", "\033[0;33m", "\033[0;31m", "\033[0;90m", "\033[0m")


def dire(texte: str, couleur: str = "") -> None:
    print(f"{couleur}{texte}{NEUTRE}" if couleur else texte)


def etape(texte: str) -> None:
    dire(f"  · {texte}", GRIS)


def bien(texte: str) -> None:
    dire(f"  ✓ {texte}", VERT)


def souci(texte: str) -> None:
    dire(f"  ! {texte}", JAUNE)


def echec(texte: str) -> None:
    dire(f"  ✗ {texte}", ROUGE)


# ---------------------------------------------------------------------------
#  Identité du logiciel — lue à la source, jamais recopiée
# ---------------------------------------------------------------------------
@dataclass
class Identite:
    """Ce qu'un paquet doit savoir du logiciel pour s'estampiller.

    ``version`` est celle du **logiciel** — 1.5.1 —, ``release`` celle de
    l'**empaquetage** : le « -1 » de ``phytoscope-1.5.1-1.noarch.rpm``. Les
    deux sont distinctes parce qu'elles changent pour des raisons
    différentes : corriger un script d'installation sans toucher au logiciel
    incrémente la release, pas la version.
    """
    version: str = "0.0.0"
    release: str = "1"
    nom_de_version: str = ""
    date: str = ""
    #  L'éditeur — l'atelier qui publie — et l'auteur — la personne qui a
    #  écrit. Les paquets portent les deux : le premier dans la description,
    #  le second dans le champ « responsable », qui attend une adresse de
    #  courriel à laquelle quelqu'un répond.
    editeur: str = "Bretagne Namasté"
    site: str = ""
    contact: str = ""
    auteur: str = ""
    courriel: str = ""
    telephone: str = ""
    licence: str = "MIT"
    droits: str = ""
    pays: str = "FR"
    region: str = ""
    ville: str = ""

    @property
    def titre(self) -> str:
        """La version telle qu'elle s'affiche, nom de code compris s'il existe.

        `VERSION` peut ne pas en porter : une paire de guillemets vides dans
        la description d'un `.deb` se voit, et se voit longtemps.
        """
        return (f"{self.version} « {self.nom_de_version} »"
                if self.nom_de_version else self.version)

    @property
    def mention_nom(self) -> str:
        """Le nom de code seul, précédé d'une espace — ou rien du tout."""
        return f" « {self.nom_de_version} »" if self.nom_de_version else ""

    @property
    def responsable(self) -> str:
        """Le champ « Maintainer » des paquets, au format RFC 822."""
        if self.auteur and self.courriel:
            return f"{self.auteur} <{self.courriel}>"
        return f"{self.editeur} <{self.contact}>"

    def jetons(self) -> Dict[str, str]:
        """Les valeurs que tous les gabarits attendent.

        Un seul endroit où l'on décide de ce que vaut `@AUTEUR@` : sans cela,
        chaque générateur en déciderait pour lui, et l'on se retrouverait avec
        un `.deb` au nom de l'atelier et un `.rpm` au nom de la personne.
        """
        return {
            "VERSION": self.version,
            "RELEASE": self.release,
            "NOM_DE_VERSION": self.nom_de_version,
            "TITRE_VERSION": self.titre,
            "DATE": self.date,
            "EDITEUR": self.editeur,
            "AUTEUR": self.auteur or self.editeur,
            "COURRIEL": self.courriel or self.contact,
            "TELEPHONE": self.telephone,
            "CONTACT": self.contact,
            "SITE": self.site,
            "LICENCE": self.licence,
            "DROITS": self.droits,
            "RESPONSABLE": self.responsable,
            "ATTRIBUTION": self.attribution,
        }

    @property
    def attribution(self) -> str:
        """L'attribution lisible : l'atelier et la personne."""
        return f"{self.editeur} — {self.auteur}" if self.auteur else self.editeur

    @classmethod
    def lire(cls, version: str = "", release: str = "") -> "Identite":
        """Lit l'identité du logiciel là où elle vit — et nulle part ailleurs.

        Le **numéro de version** vient de `phytoscope/VERSION`, fichier de
        données au format « clé = valeur » que le logiciel lui-même relit au
        démarrage : le paquet et la fenêtre « À propos » ne peuvent donc pas
        annoncer deux choses différentes.

        Le reste — auteur, site, contact — vient de `phytoscope/version.py`,
        analysé au lieu d'être importé : importer le paquet tirerait NumPy et
        Qt, dont la machine qui empaquette n'a aucun besoin.

        :param version: impose la version au lieu de la lire. C'est ainsi que
            `build.py` garantit que toutes les cibles d'une fabrication
            portent le même numéro, même si le fichier change entre-temps.
        :param release: itération d'empaquetage, « 1 » par défaut.
        """
        valeurs = lire_cle_valeur(FICHIER_VERSION)
        auteurs = lire_cle_valeur(FICHIER_AUTEURS)
        lue = valeurs.get("version", "0.0.0") + valeurs.get("suffixe", "")
        return cls(
            version=version or lue,
            release=release or "1",
            nom_de_version=valeurs.get("nom", ""),
            date=valeurs.get("date", ""),
            editeur=auteurs.get("editeur", "Bretagne Namasté"),
            site=auteurs.get("site", "https://bretagne-namaste.com"),
            contact=auteurs.get("contact", "contact@bretagne-namaste.com"),
            auteur=auteurs.get("auteur", ""),
            courriel=auteurs.get("courriel", ""),
            telephone=auteurs.get("telephone", ""),
            licence=auteurs.get("licence", "MIT"),
            droits=auteurs.get("droits", ""),
            pays=auteurs.get("pays", "FR"),
            region=auteurs.get("region", ""),
            ville=auteurs.get("ville", ""))


# ---------------------------------------------------------------------------
#  Le dossier de cette fabrication
# ---------------------------------------------------------------------------
#  Les trois familles de systèmes, telles qu'elles apparaissent dans
#  l'arborescence de sortie. Le nom est celui que l'utilisateur reconnaît,
#  pas celui de `sys.platform`.
SYSTEMES = ("Linux", "Windows", "MacOSX")


def dossier_fabrication(id_: Optional["Identite"] = None,
                        nouveau: bool = False) -> str:
    """Le dossier de CETTE fabrication : « build/paquets/1.5.1-20260918-1345 ».

    Trois cas, dans cet ordre :

    1. la variable d'environnement ``PHYTOSCOPE_SORTIE`` est posée — on
       l'utilise telle quelle. C'est ainsi que toutes les cibles d'une même
       fabrication se retrouvent au même endroit, même lancées par des
       processus distincts ;
    2. un dossier a déjà été choisi dans ce processus — on le reprend ;
    3. sinon, on en crée un neuf, horodaté.

    Pourquoi horodater : on garde ainsi plusieurs fabrications d'une même
    version côte à côte — celle d'avant un correctif d'empaquetage et celle
    d'après — sans qu'un fichier en écrase un autre, et l'on sait au nom près
    ce qu'on est en train de diffuser.
    """
    global _sortie_courante
    impose = os.environ.get(VARIABLE_SORTIE, "").strip()
    if impose and not nouveau:
        os.makedirs(impose, exist_ok=True)
        _sortie_courante = impose
        #  Le lien « dernier » se pose aussi quand le dossier est imposé —
        #  c'est le cas courant, puisque le Makefile le calcule une fois et
        #  l'impose à tous les générateurs.
        if os.path.dirname(os.path.abspath(impose)) == RACINE_SORTIE:
            _poser_le_lien(impose)
        return impose
    if _sortie_courante and not nouveau:
        return _sortie_courante

    version = (id_ or Identite.lire()).version
    dossier = os.path.join(RACINE_SORTIE,
                           f"{version}-{time.strftime('%Y%m%d-%H%M')}")
    #  Deux fabrications dans la même minute : on ajoute les secondes plutôt
    #  que d'écrire par-dessus la précédente.
    if os.path.isdir(dossier):
        dossier = os.path.join(RACINE_SORTIE,
                               f"{version}-{time.strftime('%Y%m%d-%H%M%S')}")
    os.makedirs(dossier, exist_ok=True)
    _sortie_courante = dossier
    os.environ[VARIABLE_SORTIE] = dossier
    _poser_le_lien(dossier)
    return dossier


def dossier_sortie(id_: Optional["Identite"] = None,
                   systeme: str = "") -> str:
    """Où déposer un paquet : le dossier de la fabrication, puis le système.

    ``…/1.5.1-20260918-1345/Windows/PhytoScope-1.5.1.msi``

    Un dossier par système parce qu'on ne diffuse pas les huit fichiers à
    tout le monde : celui qui vient chercher la version Windows n'a que faire
    des 340 ko du paquet Debian, et le dossier se recopie tel quel sur un
    serveur.

    ``systeme`` vide désigne la racine de la fabrication : c'est là que vivent
    les documents communs — readme, install, licence, changelog — et l'archive
    source, qui n'appartient à aucun système en particulier.
    """
    base = dossier_fabrication(id_)
    if not systeme:
        return base
    if systeme not in SYSTEMES:
        raise ValueError(f"système inconnu : {systeme!r} "
                         f"(attendu : {', '.join(SYSTEMES)})")
    chemin = os.path.join(base, systeme)
    os.makedirs(chemin, exist_ok=True)
    return chemin


def _poser_le_lien(dossier: str) -> None:
    """« dernier » désigne la fabrication la plus récente.

    Un lien symbolique, refait à chaque fabrication : c'est ce qu'on met dans
    un script de publication, plutôt qu'un nom horodaté qui change à chaque
    fois. Son absence n'est pas une erreur — certains systèmes de fichiers
    n'en veulent pas, et rien n'en dépend.
    """
    try:
        if os.path.islink(LIEN_DERNIER) or os.path.exists(LIEN_DERNIER):
            os.remove(LIEN_DERNIER)
        os.symlink(os.path.basename(dossier), LIEN_DERNIER)
    except OSError:                                    # pragma: no cover
        pass


def tous_les_paquets(id_: Optional["Identite"] = None) -> List[str]:
    """Tous les fichiers de paquet de la fabrication, sous-dossiers compris."""
    base = dossier_fabrication(id_)
    trouves = []
    for dossier, _, fichiers in os.walk(base):
        for nom in sorted(fichiers):
            #  Ni les empreintes, ni les documents, ni le certificat ni les
            #  signatures : ce sont les accompagnements, pas les paquets.
            if nom.endswith((".sha256", ".txt", ".p7s", ".pem", ".crt")):
                continue
            trouves.append(os.path.join(dossier, nom))
    return sorted(trouves)


def derniere_fabrication() -> str:
    """La fabrication la plus récente qui contient quelque chose.

    « Qui contient quelque chose » : un outil qui ne fait que LIRE — signer,
    vérifier — ne doit pas se voir attribuer un dossier vide qu'un appel
    précédent aurait créé au passage. Rend la chaîne vide s'il n'y a rien.
    """
    for dossier in fabrications():
        for _, _, fichiers in os.walk(dossier):
            if any(not f.endswith((".txt", ".pem", ".sha256")) for f in fichiers):
                return dossier
    return ""


def fabrications() -> List[str]:
    """Les dossiers de fabrication, du plus récent au plus ancien."""
    if not os.path.isdir(RACINE_SORTIE):
        return []
    dossiers = [os.path.join(RACINE_SORTIE, n)
                for n in os.listdir(RACINE_SORTIE)
                if os.path.isdir(os.path.join(RACINE_SORTIE, n))
                and not os.path.islink(os.path.join(RACINE_SORTIE, n))]
    return sorted(dossiers, key=os.path.getmtime, reverse=True)


# ---------------------------------------------------------------------------
#  Outils
# ---------------------------------------------------------------------------
@dataclass
class Outil:
    nom: str
    commande: str
    pour: str
    paquet_debian: str
    indispensable: bool = True

    @property
    def present(self) -> bool:
        if self.commande == "makensis":
            return bool(trouver_makensis())
        if self.commande == "wixl":
            return bool(trouver_wixl())
        if self.commande == "osslsigncode":
            try:
                import signature                       # noqa: PLC0415
                return bool(signature.trouver_osslsigncode())
            except Exception:                          # noqa: BLE001
                return False
        return shutil.which(self.commande) is not None


#  NSIS installé dans le dossier personnel, à la manière de `_make_.sh --deps`
#  du micrologiciel : le projet s'interdit `sudo` (`C-55`), et un outil de
#  fabrication n'a aucune raison de faire exception.
NSIS_MAISON = os.path.expanduser("~/.local/opt/nsis")


def trouver_makensis() -> str:
    """Le chemin de makensis, du système ou du dossier personnel."""
    systeme = shutil.which("makensis")
    if systeme:
        return systeme
    maison = os.path.join(NSIS_MAISON, "usr", "bin", "makensis")
    return maison if os.path.exists(maison) else ""


def environnement_nsis() -> Dict[str, str]:
    """Les variables dont makensis a besoin s'il vient du dossier personnel.

    Installé hors de /usr, il ne trouve plus ses en-têtes ni ses talons : la
    variable NSISDIR les lui désigne.
    """
    env = dict(os.environ)
    partage = os.path.join(NSIS_MAISON, "usr", "share", "nsis")
    if os.path.isdir(partage) and not shutil.which("makensis"):
        env["NSISDIR"] = partage
    return env


def installer_nsis() -> bool:
    return installer_paquets_debian("NSIS", NSIS_MAISON, ("nsis", "nsis-common"),
                                    trouver_makensis)


#  msitools (wixl) installé de la même façon que NSIS : `apt-get download`
#  puis `dpkg-deb -x` vers ~/.local/opt. Aucun mot de passe.
MSITOOLS_MAISON = os.path.expanduser("~/.local/opt/msitools")
#  Les paquets Debian dont wixl a besoin. libmsi et libgcab portent le format
#  MSI lui-même ; libgsf lit les documents composés OLE sur lesquels il repose.
MSITOOLS_PAQUETS = ("wixl", "msitools", "libmsi0", "libgcab-1.0-0",
                    "libgsf-1-114", "libgsf-1-common")


def trouver_wixl() -> str:
    """Le chemin de wixl, du système ou du dossier personnel."""
    systeme = shutil.which("wixl")
    if systeme:
        return systeme
    maison = os.path.join(MSITOOLS_MAISON, "usr", "bin", "wixl")
    return maison if os.path.exists(maison) else ""


def environnement_wixl() -> Dict[str, str]:
    """Les variables dont wixl a besoin s'il vient du dossier personnel."""
    env = dict(os.environ)
    if shutil.which("wixl"):
        return env
    bibliotheques = os.path.join(MSITOOLS_MAISON, "usr", "lib",
                                 "x86_64-linux-gnu")
    if os.path.isdir(bibliotheques):
        ancien = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = (bibliotheques + (":" + ancien if ancien else ""))
    return env


def installer_paquets_debian(nom_lisible: str, destination: str,
                             paquets: Sequence[str], temoin) -> bool:
    """Déplie des paquets Debian dans le dossier personnel, sans privilèges.

    `apt-get download` récupère un paquet sans l'installer et `dpkg-deb -x` le
    déplie où l'on veut : ni l'un ni l'autre ne demande de mot de passe. C'est
    exactement ce que fait `_make_.sh --deps` du micrologiciel pour le SDK et la
    chaîne ARM (`C-55`).
    """
    if temoin():
        bien(f"{nom_lisible} est déjà là")
        return True
    if not shutil.which("apt-get") or not shutil.which("dpkg-deb"):
        echec("apt-get et dpkg-deb sont nécessaires (Debian, Ubuntu, Mint)")
        return False
    etape(f"téléchargement de {nom_lisible}")
    os.makedirs(destination, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="paquets-") as bac:
        if not executer(["apt-get", "download", *paquets], cwd=bac):
            echec("téléchargement impossible — dépôt « universe » activé ?")
            return False
        for nom in sorted(os.listdir(bac)):
            if nom.endswith(".deb"):
                if not executer(["dpkg-deb", "-x", os.path.join(bac, nom),
                                 destination]):
                    return False
    if not temoin():
        echec(f"{nom_lisible} déplié mais son exécutable reste introuvable")
        return False
    bien(f"{nom_lisible} installé dans {destination} (aucun privilège demandé)")
    return True


def installer_wixl() -> bool:
    return installer_paquets_debian("msitools (wixl)", MSITOOLS_MAISON,
                                    MSITOOLS_PAQUETS, trouver_wixl)


OUTILS = [
    Outil("dpkg-deb", "dpkg-deb", "paquet Debian (.deb)", "dpkg-dev"),
    Outil("rpmbuild", "rpmbuild", "paquet Red Hat (.rpm)", "rpm"),
    Outil("makensis", "makensis", "installateur Windows (.exe)", "nsis",
          indispensable=False),
    Outil("wixl", "wixl", "paquet Windows (.msi)", "wixl",
          indispensable=False),
    Outil("zip", "zip", "archives Windows et macOS", "zip"),
    Outil("openssl", "openssl", "certificat et signatures", "openssl"),
    Outil("osslsigncode", "osslsigncode", "signature Authenticode (.exe, .msi)",
          "osslsigncode", indispensable=False),
]


def installer_les_outils() -> bool:
    """Tout ce qui s'installe sans privilèges : NSIS, msitools, osslsigncode."""
    dire("\nInstallation des outils manquants\n", JAUNE)
    ok = installer_nsis()
    ok = installer_wixl() and ok
    try:
        import signature                               # noqa: PLC0415
        ok = signature.installer_osslsigncode() and ok
    except Exception as exc:                           # noqa: BLE001
        souci(f"osslsigncode : {exc}")
    return ok


def etat_des_outils() -> None:
    """Dit ce qui est présent, ce qui manque, et comment l'obtenir."""
    dire("\nOutils d'empaquetage\n")
    manquants = []
    for o in OUTILS:
        if o.present:
            bien(f"{o.nom:<10} {o.pour}")
        else:
            (souci if not o.indispensable else echec)(
                f"{o.nom:<10} {o.pour} — absent")
            manquants.append(o)
    if manquants:
        dire("\n  Pour les installer :", GRIS)
        paquets = " ".join(sorted({o.paquet_debian for o in manquants}))
        dire(f"      sudo apt install {paquets}\n")
    else:
        dire("\n  Tout est là.\n", VERT)
    #  makensis à part : son absence dégrade sans bloquer, et l'on sait
    #  l'installer sans mot de passe.
    if any(o.nom in ("makensis", "wixl", "osslsigncode") for o in manquants):
        dire("  Sans privilèges et sans toucher au système :", GRIS)
        dire("      python3 packaging/build.py --deps\n")
        dire("  Sans lui, la cible Windows produit tout de même une archive",
             GRIS)
        dire("  portable (.zip) : elle s'utilise en décompressant, sans "
             "installation.\n", GRIS)


def arguments_communs(p: "argparse.ArgumentParser") -> None:
    """Les options que TOUS les générateurs partagent.

    Elles existent pour que `build.py` puisse imposer la même version et
    le même dossier à toutes les cibles d'une fabrication : sans cela, deux
    générateurs lancés à une minute d'intervalle produiraient des paquets dans
    deux dossiers différents, et un changement du fichier VERSION entre les
    deux passerait inaperçu.
    """
    p.add_argument("--version", default="", metavar="X.Y.Z",
                   help="imposer la version au lieu de la lire dans "
                        "phytoscope/VERSION")
    p.add_argument("--release", default="", metavar="N",
                   help="itération d'empaquetage (défaut : 1). Elle change "
                        "quand l'empaquetage change sans que le logiciel "
                        "bouge.")
    p.add_argument("--sortie", default="", metavar="DOSSIER",
                   help="imposer le dossier de fabrication au lieu d'en "
                        "créer un horodaté")


def appliquer_les_arguments(args) -> "Identite":
    """Lit l'identité en tenant compte des options communes."""
    if getattr(args, "sortie", ""):
        os.environ[VARIABLE_SORTIE] = os.path.abspath(args.sortie)
    return Identite.lire(getattr(args, "version", ""),
                         getattr(args, "release", ""))


# ---------------------------------------------------------------------------
#  Outillage commun
# ---------------------------------------------------------------------------
def executer(commande: Sequence[str], cwd: Optional[str] = None,
             muet: bool = True, env: Optional[Dict[str, str]] = None,
             tentative: bool = False) -> bool:
    """Lance une commande ; rend vrai si elle a réussi.

    `tentative=True` pour les essais dont l'échec est **attendu** — chercher
    une roue pour une version de Python qui n'en a pas, par exemple. Sans
    cela, la fabrication affichait une dizaine de croix rouges parfaitement
    normales, et l'on ne voyait plus les vraies erreurs au milieu.
    """
    try:
        subprocess.run(list(commande), cwd=cwd, check=True, env=env,
                       stdout=subprocess.DEVNULL if muet else None,
                       stderr=subprocess.PIPE if muet else None)
        return True
    except FileNotFoundError:
        if not tentative:
            echec(f"commande introuvable : {commande[0]}")
        return False
    except subprocess.CalledProcessError as exc:
        if tentative:
            return False
        echec(f"{commande[0]} a échoué")
        if exc.stderr:
            for ligne in exc.stderr.decode("utf-8", "replace").splitlines()[-8:]:
                dire(f"      {ligne}", GRIS)
        return False


def copier_le_logiciel(vers: str) -> None:
    """Recopie ce qui compose l'application, sans les scories."""
    os.makedirs(vers, exist_ok=True)
    for nom in CONTENU:
        source = os.path.join(LOGICIEL, nom)
        cible = os.path.join(vers, nom)
        if os.path.isdir(source):
            shutil.copytree(source, cible,
                            ignore=shutil.ignore_patterns(
                                "__pycache__", "*.pyc", "*.pyo", ".pytest_cache"))
        elif os.path.exists(source):
            shutil.copy2(source, cible)

    #  `tools/` reste dehors — c'est de l'outillage de développement —, mais
    #  `ecrire_langue.py` n'en est pas : c'est lui qui inscrit dans les
    #  réglages la langue choisie à l'installation, et les trois
    #  installateurs l'appellent. On le pose à la racine de la charge, au même
    #  endroit pour tous, plutôt que de laisser chacun deviner un chemin.
    langue = os.path.join(LOGICIEL, "tools", "ecrire_langue.py")
    if os.path.exists(langue):
        shutil.copy2(langue, os.path.join(vers, "ecrire_langue.py"))


def remplir(gabarit: str, valeurs: Dict[str, str]) -> str:
    """Remplace les jetons @NOM@ d'un gabarit."""
    with open(gabarit, encoding="utf-8") as f:
        texte = f.read()
    for cle, valeur in valeurs.items():
        texte = texte.replace(f"@{cle}@", valeur)
    restants = re.findall(r"@([A-Z_]+)@", texte)
    if restants:
        souci(f"jetons non remplis dans {os.path.basename(gabarit)} : "
              f"{', '.join(sorted(set(restants)))}")
    return texte


def ecrire(chemin: str, contenu: str, executable: bool = False) -> None:
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenu)
    if executable:
        os.chmod(chemin, os.stat(chemin).st_mode | stat.S_IXUSR
                 | stat.S_IXGRP | stat.S_IXOTH)


def taille_ko(chemin: str) -> int:
    total = 0
    for dossier, _, fichiers in os.walk(chemin):
        for nom in fichiers:
            try:
                total += os.path.getsize(os.path.join(dossier, nom))
            except OSError:                            # pragma: no cover
                pass
    return max(total // 1024, 1)


def lisible(octets: int) -> str:
    for seuil, unite in ((1 << 30, "Go"), (1 << 20, "Mo"), (1 << 10, "ko")):
        if octets >= seuil:
            return f"{octets / seuil:.1f} {unite}"
    return f"{octets} o"


def empreinte(chemin: str) -> str:
    h = hashlib.sha256()
    with open(chemin, "rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


# ---------------------------------------------------------------------------
#  Les roues : ce qui rend un paquet installable hors ligne
# ---------------------------------------------------------------------------
def telecharger_les_roues(cible: str, vers: str,
                          versions_python: Sequence[str],
                          optionnelles: bool = True) -> bool:
    """Récupère les roues d'une plateforme dans `vers`, pour plusieurs Python.

    On impose `--only-binary=:all:` : la machine ne peut rien compiler pour un
    autre système, et une roue absente doit se voir tout de suite plutôt que
    d'échouer chez l'utilisateur.

    Les roues déjà présentes ne sont pas retéléchargées — pip les reconnaît
    par leur nom —, si bien que couvrir cinq versions de Python ne multiplie
    pas la taille par cinq : seules les bibliothèques compilées par version
    (NumPy, cffi) se dupliquent, et Qt, publié en « abi3 », ne l'est pas.
    """
    os.makedirs(vers, exist_ok=True)
    obligatoires = _lire_requirements(os.path.join(LOGICIEL, "requirements.txt"))
    facultatives = _lire_requirements(
        os.path.join(LOGICIEL, "requirements-optionnel.txt")) if optionnelles else []

    architectures = PLATEFORMES[cible]
    for paquet in obligatoires:
        obtenu = False
        for etiquettes in architectures:
            for version in versions_python:
                if _une_roue(paquet, etiquettes, version, vers):
                    obtenu = True
        if not obtenu:
            echec(f"roue introuvable pour {paquet} ({cible}) — paquet incomplet")
            return False
    for paquet in facultatives:
        #  Leur échec est sans conséquence : c'est toute leur définition.
        trouve = False
        for etiquettes in architectures:
            for version in versions_python:
                trouve |= _une_roue(paquet, etiquettes, version, vers)
        if not trouve:
            souci(f"{paquet} indisponible pour {cible} — le paquet s'en passera")
    roues = [r for r in os.listdir(vers) if r.endswith(".whl")]
    bien(f"{len(roues)} roues, {lisible(taille_ko(vers) * 1024)} "
         f"(Python {', '.join(versions_python)})")
    return True


def deplier_les_roues(roues: str, vers: str, etiquette: str,
                      version_python: str) -> bool:
    """Installe des roues d'une AUTRE plateforme dans un dossier.

    `pip install` refuse par défaut une roue `win_amd64` sur une machine
    Linux — à juste titre, puisqu'elle n'y fonctionnerait pas. Mais ici on
    n'installe pas pour exécuter : on remplit un paquet destiné à Windows. Les
    options `--platform` et `--target` disent précisément cela à pip, qui
    accepte alors et pose correctement les fichiers de données et les
    métadonnées.

    Si pip refuse malgré tout — cas d'une roue dont l'étiquette est plus
    précise que la nôtre —, on déplie l'archive à la main : une roue n'est
    qu'un zip dont le contenu va tel quel dans `site-packages`.
    """
    os.makedirs(vers, exist_ok=True)
    fichiers = sorted(os.path.join(roues, r) for r in os.listdir(roues)
                      if r.endswith(".whl"))
    if not fichiers:
        return False
    if executer([sys.executable, "-m", "pip", "install", "--no-deps",
                 "--no-compile", "--only-binary=:all:",
                 "--platform", etiquette, "--python-version", version_python,
                 "--target", vers, *fichiers]):
        return True

    souci("pip a refusé ces roues — dépliage direct")
    for roue in fichiers:
        try:
            with zipfile.ZipFile(roue) as z:
                z.extractall(vers)
        except (OSError, zipfile.BadZipFile) as exc:
            echec(f"{os.path.basename(roue)} : {exc}")
            return False
    return True


def _lire_requirements(chemin: str) -> List[str]:
    paquets = []
    with open(chemin, encoding="utf-8") as f:
        for ligne in f:
            ligne = ligne.split("#")[0].strip()
            if ligne:
                paquets.append(ligne)
    return paquets


def _une_roue(specification: str, etiquettes: List[str], version_python: str,
              vers: str) -> bool:
    """Récupère une bibliothèque **et ce dont elle dépend**.

    Le piège, découvert à l'essai : `PySide6` n'est qu'une roue de quelques
    kilo-octets qui déclare dépendre de `PySide6-Essentials`, de
    `PySide6-Addons` et de `shiboken6` — lesquels portent les 150 Mo de Qt.
    Avec `--no-deps`, on obtenait donc un paquet Windows de 27 Mo sans la
    moindre bibliothèque graphique, qui n'aurait pas démarré. On laisse pip
    résoudre, en lui interdisant toute compilation (`--only-binary`) puisque
    la machine ne peut rien compiler pour un autre système.
    """
    for etiquette in etiquettes:
        if executer([sys.executable, "-m", "pip", "download",
                     "--only-binary=:all:",
                     "--platform", etiquette,
                     "--python-version", version_python,
                     "--dest", vers, specification], tentative=True):
            return True
    #  Dernier recours : une roue « any », valable partout (paquets en Python
    #  pur, comme pyserial).
    return executer([sys.executable, "-m", "pip", "download",
                     "--only-binary=:all:", "--dest", vers, specification],
                    tentative=True)


# ---------------------------------------------------------------------------
#  Icônes
# ---------------------------------------------------------------------------
def icone_svg() -> str:
    """L'icône du logiciel, dessinée par programme comme toutes les planches."""
    return '''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256" width="256" height="256">
  <rect width="256" height="256" rx="48" fill="#12201B"/>
  <path d="M128 208 C128 150 128 110 128 78" stroke="#3F7D5A" stroke-width="10"
        stroke-linecap="round" fill="none"/>
  <path d="M128 120 C96 116 74 96 70 62 C106 62 126 84 128 120 Z" fill="#7FE0A8"/>
  <path d="M128 148 C160 144 182 124 186 90 C150 90 130 112 128 148 Z" fill="#3F7D5A"/>
  <path d="M40 176 L64 176 L80 148 L96 196 L112 168 L128 176 L216 176"
        stroke="#E0C073" stroke-width="7" fill="none"
        stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="128" cy="176" r="7" fill="#E0C073"/>
</svg>
'''


def python_du_logiciel() -> str:
    """L'interpréteur qui a PySide6 — celui de l'environnement du logiciel.

    Ce script s'exécute avec n'importe quel Python 3 ; il n'a besoin que de la
    bibliothèque standard et de pip. Mais la fabrication de l'icône demande un
    moteur de rendu SVG, et le seul disponible ici est celui de Qt, installé
    dans `src/phytoscope/.venv`. On ne peut pas l'importer — une
    extension compilée pour Python 3.10 ne se charge pas dans Python 3.14 —,
    on l'appelle donc en sous-processus.
    """
    for candidat in (os.path.join(LOGICIEL, ".venv", "bin", "python"),
                     os.path.join(LOGICIEL, ".venv", "Scripts", "python.exe")):
        if os.path.exists(candidat):
            return candidat
    return sys.executable


#  Programme de rendu, exécuté par l'interpréteur du logiciel. Il lit le SVG
#  sur son entrée standard et écrit une icône au format demandé.
#
#  Les deux formats sont des conteneurs de PNG : une fois les PNG obtenus,
#  l'assemblage tient en quelques lignes et n'exige aucune dépendance. Seul le
#  rendu vectoriel demande Qt.
_RENDU_ICONE = r"""
import os, struct, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QBuffer, QByteArray, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

format_, cible = sys.argv[1], sys.argv[2]
svg = sys.stdin.buffer.read()
app = QApplication([])
rendu = QSvgRenderer(QByteArray(svg))


def png(taille):
    img = QImage(taille, taille, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img); rendu.render(p); p.end()
    tampon = QBuffer(); tampon.open(QBuffer.WriteOnly)
    img.save(tampon, "PNG")
    return bytes(tampon.data())


if format_ == "ico":
    #  Windows : en-tête, puis un descripteur par image, puis les PNG.
    images = [(t, png(t)) for t in (16, 32, 48, 64, 128, 256)]
    entetes, corps, decalage = b"", b"", 6 + 16 * len(images)
    for taille, donnees in images:
        octet = 0 if taille >= 256 else taille   # 256 se note 0
        entetes += struct.pack("<BBBBHHII", octet, octet, 0, 0, 1, 32,
                               len(donnees), decalage)
        corps += donnees
        decalage += len(donnees)
    charge = struct.pack("<HHH", 0, 1, len(images)) + entetes + corps
else:
    #  macOS : la signature « icns », la longueur totale, puis des blocs
    #  typés. Les types icp4/icp5/ic07…ic10 acceptent directement du PNG.
    types = ((b"icp4", 16), (b"icp5", 32), (b"ic07", 128),
             (b"ic08", 256), (b"ic09", 512), (b"ic10", 1024))
    blocs = b""
    for type_, taille in types:
        donnees = png(taille)
        blocs += type_ + struct.pack(">I", len(donnees) + 8) + donnees
    charge = b"icns" + struct.pack(">I", len(blocs) + 8) + blocs

with open(cible, "wb") as f:
    f.write(charge)
"""


def fabriquer_icone(vers: str, format_: str) -> bool:
    """Une icône multi-résolutions, rendue par Qt puis assemblée ici.

    `format_` vaut « ico » (Windows) ou « icns » (macOS). Les deux systèmes
    choisissent la taille qui convient au contexte : 16 px dans la barre des
    tâches, 1024 px dans l'aperçu du Finder.
    """
    python = python_du_logiciel()
    try:
        resultat = subprocess.run([python, "-c", _RENDU_ICONE, format_, vers],
                                  input=icone_svg().encode("utf-8"),
                                  capture_output=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired):
        return False
    if resultat.returncode != 0 or not os.path.exists(vers):
        return False
    return os.path.getsize(vers) > 0


# ---------------------------------------------------------------------------
#  Cible : Debian, Ubuntu, Mint
# ---------------------------------------------------------------------------


def ecrire_les_empreintes(id_: Optional["Identite"] = None) -> Optional[str]:
    """Une empreinte SHA-256 par paquet, plus un récapitulatif à la racine.

    Deux formes, parce qu'elles servent à deux choses :

    * ``<paquet>.sha256``, **à côté du paquet** — c'est ce qu'on télécharge en
      même temps que lui, et ce que la plupart des gens vérifient :
      ``sha256sum -c PhytoScope-….exe.sha256`` ;
    * ``phytoscope-X.Y.Z.sha256`` à la racine de la fabrication, avec les
      chemins relatifs — pour contrôler l'ensemble en une commande.

    Ce n'est pas une signature : cela prouve l'**intégrité**, que le fichier
    n'a pas été abîmé en route, et non son origine.
    """
    id_ = id_ or Identite.lire()
    base = dossier_fabrication(id_)
    paquets = tous_les_paquets(id_)
    if not paquets:
        return None

    lignes = []
    for chemin in paquets:
        somme = empreinte(chemin)
        relatif = os.path.relpath(chemin, base).replace(os.sep, "/")
        lignes.append(f"{somme}  {relatif}")
        #  L'empreinte individuelle, au format que `sha256sum -c` relit
        #  depuis le dossier du paquet.
        with open(chemin + ".sha256", "w", encoding="utf-8",
                  newline="\n") as sortie:
            sortie.write(f"{somme}  {os.path.basename(chemin)}\n")

    cible = os.path.join(base, f"phytoscope-{id_.version}.sha256")
    ecrire(cible, "\n".join(lignes) + "\n")
    return cible


# ---------------------------------------------------------------------------
#  Les documents qui accompagnent les paquets
# ---------------------------------------------------------------------------
def ecrire_les_documents(id_: Optional["Identite"] = None) -> List[str]:
    """Dépose readme, install, licence et changelog auprès des paquets.

    Cinq textes, à la racine de la fabrication **et** dans chaque dossier de
    système : un dossier `Windows/` recopié tel quel sur un serveur doit rester
    compréhensible tout seul.

    * `readme.txt`    — ce qu'il y a là, lequel prendre ;
    * `install.txt`   — comment l'installer ;
    * `manuel.txt`    — comment le logiciel fonctionne ;
    * `licence.txt`   — la licence MIT ;
    * `changelog.txt` — ce qui a changé.
    """
    id_ = id_ or Identite.lire()
    base = dossier_fabrication(id_)
    ecrits = []

    for nom, contenu in (("readme.txt", _readme(id_, base, "")),
                         ("install.txt", _install(id_, "")),
                         ("manuel.txt", _manuel(id_, "")),
                         ("licence.txt", _licence(id_)),
                         ("changelog.txt", _changelog(id_))):
        chemin = os.path.join(base, nom)
        ecrire(chemin, contenu)
        ecrits.append(chemin)

    for systeme in SYSTEMES:
        dossier = os.path.join(base, systeme)
        if not os.path.isdir(dossier) or not os.listdir(dossier):
            continue
        for nom, contenu in (("readme.txt", _readme(id_, dossier, systeme)),
                             ("install.txt", _install(id_, systeme)),
                             ("manuel.txt", _manuel(id_, systeme)),
                             ("licence.txt", _licence(id_)),
                             ("changelog.txt", _changelog(id_))):
            chemin = os.path.join(dossier, nom)
            ecrire(chemin, contenu)
            ecrits.append(chemin)
    return ecrits


def _tableau_des_paquets(dossier: str, recursif: bool = False) -> str:
    """La liste de ce qui est réellement là, avec sa taille.

    À la racine d'une fabrication, on descend dans les dossiers de système :
    un readme qui n'annoncerait que l'archive source alors que huit paquets
    sont là serait pire qu'inutile.
    """
    lignes = []
    if recursif:
        for racine, sous, fichiers in os.walk(dossier):
            sous.sort()
            prefixe = os.path.relpath(racine, dossier).replace(os.sep, "/")
            prefixe = "" if prefixe == "." else prefixe + "/"
            for nom in sorted(fichiers):
                if nom.endswith((".sha256", ".txt")):
                    continue
                chemin = os.path.join(racine, nom)
                taille = lisible(os.path.getsize(chemin))
                lignes.append(f"    {prefixe + nom:<52} {taille:>10}")
    else:
        for nom in sorted(os.listdir(dossier)):
            chemin = os.path.join(dossier, nom)
            if not os.path.isfile(chemin) or nom.endswith((".sha256", ".txt")):
                continue
            taille = lisible(os.path.getsize(chemin))
            lignes.append(f"    {nom:<52} {taille:>10}")
    return "\n".join(lignes) or "    (aucun paquet dans ce dossier)"


def _readme(id_: "Identite", dossier: str, systeme: str = "") -> str:
    """Ce que contient le dossier, et lequel prendre.

    Deux variantes : à la racine, il présente les trois systèmes ; dans
    `Windows/`, il ne parle que de Windows. Un dossier recopié seul sur un
    serveur doit rester compréhensible sans le reste.
    """
    portee = f" — {systeme}" if systeme else ""
    choix = _quoi_prendre(id_, systeme)
    return f"""PhytoScope {id_.titre}{portee}
{'=' * 74}

  {APP_TAGLINE}

  Publié par {id_.editeur} — {id_.site}
  Écrit par  {id_.auteur} — {id_.courriel}
             {id_.telephone}

  Version {id_.version}-{id_.release}, publiée le {id_.date}.
  Licence {id_.licence} — voir licence.txt.


CE QUE CONTIENT CE DOSSIER
{'-' * 74}

{_tableau_des_paquets(dossier, recursif=not systeme)}

  Chaque paquet est accompagné de son empreinte « .sha256 » et de sa signature
  « .p7s ».


LES AUTRES FICHIERS DE CE DOSSIER
{'-' * 74}

    install.txt          comment installer, pas à pas
    manuel.txt           comment le logiciel fonctionne
    licence.txt          la licence MIT
    changelog.txt        ce qui a changé, version par version
    AUTHENTICITE.txt     ce que la signature prouve — et ce qu'elle ne prouve pas
    phytoscope-certificat.pem   le certificat public, pour vérifier


LEQUEL PRENDRE
{'-' * 74}

{choix}
  Les instructions détaillées sont dans install.txt.


CE QU'IL FAUT SAVOIR AVANT D'INSTALLER
{'-' * 74}

  LES PAQUETS SONT SIGNÉS, mais par un certificat AUTO-SIGNÉ. La signature
  prouve que le fichier n'a pas changé depuis qu'il a été signé, et qu'il
  vient de la même clé que les versions précédentes. Elle NE FAIT PAS TAIRE
  l'avertissement de Windows ni celui de macOS : le premier exige un
  certificat délivré par une autorité reconnue — un produit commercial facturé
  chaque année —, le second un compte développeur Apple, qui suppose un
  abonnement payant et un Mac.

  Nous préférons le dire. install.txt explique comment passer outre l'avertis-
  sement, et AUTHENTICITE.txt comment vérifier la signature.

  CHAQUE INSTALLATEUR VOUS DEMANDE s'il faut poser une icône sur le Bureau et
  lancer le logiciel à la fin, et chacun fournit un désinstallateur.

  AUCUNE DÉSINSTALLATION N'EFFACE VOS DONNÉES. Réglages et séances sont
  conservés, et le désinstallateur vous dit où ils sont. Une désinstallation
  n'est pas une demande d'oubli.

  Le logiciel ne se connecte à rien : aucune télémétrie, aucun compte, aucune
  vérification de licence. Vos mesures restent chez vous.

  Le logiciel démarre SANS MATÉRIEL : un générateur interne prend le relais,
  ce qui permet de tout découvrir avant d'acheter quoi que ce soit.


CE QUE LE LOGICIEL NE PRÉTEND PAS FAIRE
{'-' * 74}

  Il ne traduit pas une plante et ne l'identifie pas. Il mesure des variations
  de potentiel électrique, les affiche, les enregistre et les rend audibles.
  Chaque représentation indique ce qu'elle suppose et ce qu'elle ne permet pas
  de conclure. C'est un instrument de mesure, pas un oracle.
"""


def _quoi_prendre(id_: "Identite", systeme: str) -> str:
    """Le paragraphe « lequel prendre », limité au système concerné."""
    v = id_.version
    r = id_.release
    blocs = {
        "Windows": f"""  Windows 10 ou 11, pour vous              PhytoScope-{v}-Windows.exe
      L'installateur habituel : un assistant, des raccourcis, une entrée dans
      « Applications et fonctionnalités ». AUCUN privilège d'administration
      n'est demandé — il s'installe dans votre profil. Rien d'autre à
      installer : Python, Qt et NumPy sont dedans.

  Windows, parc de machines                PhytoScope-{v}.msi
      Le format que déploient les stratégies de groupe et Intune :
          msiexec /i PhytoScope-{v}.msi /qn
      S'installe pour toute la machine, et demande donc les droits
      d'administration.

  Windows, sans rien installer             PhytoScope-{v}-Windows-portable.zip
      On décompresse, on double-clique sur PhytoScope.cmd. Rien n'est inscrit
      dans la base de registre. Pour une clé USB, ou un poste verrouillé.
""",
        "MacOSX": f"""  macOS, installateur                      PhytoScope-{v}.pkg
      Un assistant, l'application posée dans /Applications pour tous les
      comptes. Il demande s'il faut ajouter une icône sur le Bureau et lancer
      le logiciel à la fin, et dépose un désinstallateur.

  macOS, glisser-déposer                   PhytoScope-{v}-macOS.zip
      Contient PhytoScope.app, à glisser dans Applications. La manière la plus
      répandue, et la plus facile à défaire.

  Les deux valent pour Intel ET Apple Silicon : Qt n'est publié pour macOS
  qu'en binaire double, il n'y a donc rien à choisir.
""",
        "Linux": f"""  Debian, Ubuntu, Mint                     phytoscope_{v}_all.deb
      sudo apt install ./phytoscope_{v}_all.deb

  Fedora, Red Hat, Rocky, Alma             phytoscope-{v}-{r}.noarch.rpm
      sudo dnf install ./phytoscope-{v}-{r}.noarch.rpm

  TOUTE AUTRE DISTRIBUTION                 PhytoScope-{v}-Linux.run
      Arch, openSUSE, Alpine, NixOS, Slackware… et tous les cas où l'on n'a
      pas les droits d'administration : cet installateur autonome se pose dans
      votre dossier personnel et n'appelle jamais sudo.
          chmod +x PhytoScope-{v}-Linux.run
          ./PhytoScope-{v}-Linux.run
""",
    }
    if systeme:
        return blocs.get(systeme, "")
    return ("\n".join(blocs[s] for s in ("Windows", "MacOSX", "Linux"))
            + f"\n  Autre système, ou depuis les sources     phytoscope-{v}.tar.gz\n"
              "      À la racine de cette fabrication.\n")


def _install(id_: "Identite", systeme: str = "") -> str:
    """Comment installer — seulement le système concerné, s'il est précisé."""
    v = id_.version
    r = id_.release
    portee = f" — {systeme}" if systeme else ""
    sections = []

    if systeme in ("", "Windows"):
        sections.append(f"""WINDOWS 10 ET 11
{'-' * 74}

  AVEC L'INSTALLATEUR  (le plus simple)

      1. Double-cliquez sur PhytoScope-{v}-Windows.exe

      2. Windows affiche « Windows a protégé votre ordinateur ».
         Cliquez sur « Informations complémentaires », puis
         « Exécuter quand même ».

         Ce message apparaît parce que le fichier n'est pas signé par un
         certificat commercial. Il l'est en revanche par le nôtre : voir
         AUTHENTICITE.txt, qui explique ce que cela prouve et ce que cela
         ne prouve pas.

      3. L'assistant vous propose :
             · le dossier d'installation (par défaut %LOCALAPPDATA%) ;
             · une CASE « Icône sur le Bureau », que vous pouvez décocher ;
             · à la fin, « Lancer PhytoScope maintenant » et « Lire le
               manuel », que vous pouvez décocher aussi.

         L'installation se fait dans votre profil : AUCUN privilège
         d'administration n'est demandé.

      DÉSINSTALLER  Paramètres → Applications → PhytoScope → Désinstaller.
                    Ou le raccourci « Désinstaller » du menu Démarrer.

  AVEC LE PAQUET MSI  (parc de machines)

      msiexec /i PhytoScope-{v}.msi                installation guidée
      msiexec /i PhytoScope-{v}.msi /qn            sans interface
      msiexec /i PhytoScope-{v}.msi /qn ADDLOCAL=Complet,IconeBureau
                                                     avec l'icône du Bureau
      msiexec /x PhytoScope-{v}.msi /qn            désinstallation

      S'installe pour toute la machine dans « Program Files » et demande donc
      les droits d'administration. Déployable par stratégie de groupe ou par
      Intune. Une nouvelle version remplace l'ancienne au lieu de s'installer
      à côté.

      Un service informatique qui installe notre certificat dans le magasin
      « Éditeurs approuvés » de ses machines n'aura plus d'avertissement.

  SANS RIEN INSTALLER

      Décompressez PhytoScope-{v}-Windows-portable.zip où vous voulez, puis
      double-cliquez sur PhytoScope.cmd. Rien n'est inscrit dans la base de
      registre ; pour « désinstaller », effacez le dossier.

  EN CAS DE PROBLÈME

      Double-cliquez sur Diagnostic.cmd : il écrit un rapport à joindre à un
      signalement. Dans le logiciel, Ctrl+L ouvre le journal.

  VOS FICHIERS
      Réglages : %APPDATA%\\PhytoScope
      Séances  : %USERPROFILE%\\Documents\\PhytoScope
      Ils ne sont JAMAIS effacés par une désinstallation.
""")

    if systeme in ("", "MacOSX"):
        sections.append(f"""macOS  (INTEL ET APPLE SILICON)
{'-' * 74}

  PRÉALABLE

      PhytoScope a besoin de Python 3.9 ou plus récent. S'il manque :
          brew install python
      ou téléchargez-le sur python.org. L'application vous le dira, dans une
      vraie fenêtre, si nécessaire.

  AVEC L'INSTALLATEUR

      1. Double-cliquez sur PhytoScope-{v}.pkg

      2. macOS refusera de l'ouvrir. Faites un CLIC DROIT sur le fichier,
         choisissez « Ouvrir », puis confirmez. Une seule fois suffit.

         Ce détour existe parce que l'application n'est pas signée par un
         compte développeur Apple. Le clic droit « Ouvrir » est la manière
         prévue par Apple de passer outre en connaissance de cause.

      3. L'assistant installe dans /Applications, puis demande :
             · « Ajouter une icône PhytoScope sur le Bureau ? »
             · « Lancer PhytoScope maintenant ? »

      DÉSINSTALLER
          /Applications/PhytoScope.app/Contents/Resources/desinstaller.sh

  PAR GLISSER-DÉPOSER

      1. Décompressez PhytoScope-{v}-macOS.zip
      2. Glissez PhytoScope.app dans votre dossier Applications
      3. CLIC DROIT sur l'icône → « Ouvrir » → confirmer

      Pour désinstaller : jetez l'icône à la corbeille.

  SI macOS BLOQUE MALGRÉ TOUT

      xattr -dr com.apple.quarantine /Applications/PhytoScope.app

  À LA PREMIÈRE OUVERTURE

      PhytoScope prépare son environnement Python : une à deux minutes, une
      seule fois. macOS demandera ensuite l'autorisation d'accéder au
      MICROPHONE — c'est par l'entrée audio que le signal de la plante
      arrive. Sans cette autorisation, la mesure reste muette.

  VOS FICHIERS
      Réglages : ~/Library/Application Support/PhytoScope
      Séances  : ~/Documents/PhytoScope
      Ils ne sont JAMAIS effacés par une désinstallation.
""")

    if systeme in ("", "Linux"):
        sections.append(f"""DEBIAN, UBUNTU, MINT
{'-' * 74}

      sudo apt install ./phytoscope_{v}_all.deb

  « apt » et non « dpkg » : il installe aussi les dépendances. Le logiciel
  apparaît ensuite dans le menu, ou se lance par « phytoscope ».

  Deux outils sont posés avec lui :
      phytoscope-icone-bureau              pose l'icône sur le Bureau
      phytoscope-icone-bureau --retirer    la retire
      phytoscope-desinstaller              désinstalle

  Pourquoi l'icône n'est pas proposée à l'installation : « apt » installe sans
  interaction, souvent sans session graphique, et parfois pour un autre compte
  que celui qui s'en servira. La question serait posée à la mauvaise personne.

  DÉSINSTALLER   sudo apt remove phytoscope


FEDORA, RED HAT, ROCKY, ALMALINUX, CENTOS
{'-' * 74}

      sudo dnf install ./phytoscope-{v}-{r}.noarch.rpm

  Sur les versions anciennes de Red Hat, « yum » à la place de « dnf ».
  Les mêmes outils que ci-dessus sont posés.

  DÉSINSTALLER   sudo dnf remove phytoscope


TOUTE AUTRE DISTRIBUTION  (installateur autonome)
{'-' * 74}

  Arch, openSUSE, Alpine, NixOS, Slackware… et tous les cas où l'on n'a pas
  les droits d'administration.

      chmod +x PhytoScope-{v}-Linux.run
      ./PhytoScope-{v}-Linux.run

  L'installateur ouvre une fenêtre s'il y a un bureau, sinon il parle dans le
  terminal. Il affiche la licence, demande où installer, puis :
      · « Ajouter une icône PhytoScope sur le Bureau ? »
      · « Lancer PhytoScope maintenant ? »

  Lancé par un compte ordinaire, il s'installe dans ~/.local/opt/phytoscope et
  N'APPELLE JAMAIS SUDO. Lancé par root, il installe dans /opt pour toute la
  machine.

  OPTIONS

      --gui              imposer l'interface graphique
      --tui              imposer les boîtes en mode texte
      --texte            imposer l'affichage en lignes, sans boîtes
      --prefix DOSSIER   installer ailleurs
      --desktop          poser l'icône sans demander
      --no-desktop       ne pas la poser
      --launch           lancer à la fin sans demander
      --no-launch        ne pas lancer
      -y                 ne rien demander du tout
      --check            vérifier l'intégrité sans installer
      --extract DOSSIER  décompresser sans installer
      --uninstall        désinstaller
      --help             la liste complète

  Installation sans surveillance, pour une salle de classe :

      ./PhytoScope-{v}-Linux.run -y --no-desktop --no-launch

  DÉSINSTALLER   ./PhytoScope-{v}-Linux.run --uninstall
                 ou ~/.local/opt/phytoscope/desinstaller.sh

  VOS FICHIERS
      Réglages : ~/.config/phytoscope
      Séances  : ~/.local/share/phytoscope/seances
      Ils ne sont JAMAIS effacés par une désinstallation.
""")

    if not systeme:
        sections.append(f"""TOUT SYSTÈME, DEPUIS LES SOURCES
{'-' * 74}

      tar xzf phytoscope-{v}.tar.gz
      cd phytoscope-{v}
      make install          environnement virtuel et dépendances
      make demo             découverte, sans matériel
      make doctor           diagnostic d'installation

  Il faut Python 3.9 ou plus récent. « make system-deps » indique les paquets
  système à installer selon votre distribution.
""")

    sections.append(f"""VÉRIFIER CE QUE VOUS AVEZ TÉLÉCHARGÉ
{'-' * 74}

  L'EMPREINTE  — que le fichier n'a pas été abîmé en route

      Un seul fichier, depuis son dossier :
          sha256sum -c <nom du paquet>.sha256

      Toute la fabrication, depuis sa racine :
          sha256sum -c phytoscope-{v}.sha256

      Sous Windows :
          certutil -hashfile <nom du paquet> SHA256
      puis comparez avec le contenu du fichier .sha256.

  LA SIGNATURE  — qu'il vient bien de nous

      openssl cms -verify -binary -inform DER \\
          -in <paquet>.p7s -content <paquet> \\
          -certfile phytoscope-certificat.pem -noverify -out /dev/null

      Sous Windows, pour les .exe et .msi, la signature est visible dans les
      propriétés du fichier, onglet « Signatures numériques ».

      Le certificat est AUTO-SIGNÉ : il prouve l'intégrité et la continuité
      d'origine, il ne fait taire ni SmartScreen ni Gatekeeper. AUTHENTICITE.txt
      l'explique en détail.


APRÈS L'INSTALLATION
{'-' * 74}

  Le logiciel démarre SANS matériel : un générateur interne prend le relais,
  ce qui permet de tout découvrir avant d'acheter quoi que ce soit.

  Lisez manuel.txt : il décrit les dix onglets, comment brancher une plante,
  et surtout quelles électrodes NE PAS employer.

  Dans le logiciel : F1 pour l'aide et les raccourcis, Ctrl+L pour le journal.

  {id_.editeur} — {id_.auteur}
  {id_.site} — {id_.courriel}
""")

    return (f"PhytoScope {v} — installation{portee}\n{'=' * 74}\n\n\n"
            + "\n\n".join(sections))


def _manuel(id_: "Identite", systeme: str = "") -> str:
    """Le mode d'emploi : ce que fait le logiciel, et comment s'en servir.

    Adapté au système, car trois choses en dépendent : la touche de commande
    (⌘ sur macOS, Ctrl ailleurs), l'endroit où vivent les fichiers de
    l'utilisateur, et la façon d'atteindre le matériel.
    """
    cmd = "⌘" if systeme == "MacOSX" else "Ctrl+"
    sep = "" if systeme == "MacOSX" else ""
    portee = f" — {systeme}" if systeme else ""

    if systeme == "Windows":
        emplacements = """  Réglages   %APPDATA%\\PhytoScope\\reglages.json
  Journal    %APPDATA%\\PhytoScope\\phytoscope.log
  Séances    %USERPROFILE%\\Documents\\PhytoScope"""
        materiel = """  La carte PhytoSense One apparaît comme un périphérique audio ET comme un
  port série (COMx). Windows n'a besoin d'aucun pilote : la carte se déclare
  en classe audio 2.0 et en port série standard. Si le lien de contrôle ne
  s'établit pas, l'onglet Diagnostic énumère le bus USB et dit ce qu'il voit."""
    elif systeme == "MacOSX":
        emplacements = """  Réglages   ~/Library/Application Support/PhytoScope/reglages.json
  Journal    ~/Library/Application Support/PhytoScope/phytoscope.log
  Séances    ~/Documents/PhytoScope"""
        materiel = """  La carte PhytoSense One apparaît comme un périphérique audio ET comme un
  port série (/dev/cu.usbmodem…). Aucun pilote n'est nécessaire.

  macOS demandera l'autorisation d'accéder au MICROPHONE : c'est par l'entrée
  audio que le signal arrive. Sans elle, la mesure reste muette. Si vous avez
  refusé, Réglages système -> Confidentialité et sécurité -> Microphone."""
    else:
        emplacements = """  Réglages   ~/.config/phytoscope/reglages.json
  Journal    ~/.config/phytoscope/phytoscope.log
  Séances    ~/.local/share/phytoscope/seances"""
        materiel = """  La carte PhytoSense One apparaît comme un périphérique audio ET comme un
  port série (/dev/ttyACM0). Aucun pilote n'est nécessaire.

  Si le port série est inaccessible, votre compte n'est probablement pas dans
  le groupe « dialout » :

      sudo usermod -aG dialout $USER

  puis refermez la session. L'onglet Diagnostic le signale explicitement."""

    return f"""PhytoScope {id_.version} — manuel{portee}
{'=' * 74}

  {APP_TAGLINE}
  {id_.auteur} — {id_.site}


CE QUE FAIT CE LOGICIEL
{'-' * 74}

  Une plante, comme tout tissu vivant, présente entre deux de ses points une
  différence de potentiel électrique qui varie — de quelques microvolts à
  quelques millivolts, sur des durées allant de la seconde à l'heure.
  PhytoScope mesure cette tension, l'affiche, l'enregistre, et la rend
  audible.

  C'est un INSTRUMENT DE MESURE. Il ne traduit pas la plante et ne l'identifie
  pas. Chaque représentation qu'il affiche indique ce qu'elle suppose et ce
  qu'elle ne permet pas de conclure. Quand un nombre est déduit plutôt que
  mesuré, il le dit.


PREMIÈRE SÉANCE, SANS MATÉRIEL
{'-' * 74}

  Lancez le logiciel. S'il ne trouve aucune carte, il bascule sur son
  générateur interne et le signale dans la barre d'état. Tout fonctionne :
  les courbes, l'analyse, la musique, l'enregistrement. C'est fait pour qu'on
  puisse tout découvrir avant d'acheter quoi que ce soit.

  Passez ensuite en revue les onglets ci-dessous. Appuyez sur F1 à tout
  moment : l'aide liste les raccourcis et décrit chaque onglet.


BRANCHER UNE PLANTE
{'-' * 74}

  Deux points de mesure : une FEUILLE et la TERRE du pot (la racine).

  Sur la feuille — une pince-électrode à contact souple, ou deux petites
  plaques d'acier inoxydable séparées par un tissu humidifié à l'eau
  déminéralisée. Jamais d'aiguille : on blesse la plante et l'on mesure la
  cicatrisation plutôt que la plante.

  Dans la terre — une tige d'ACIER INOXYDABLE 316L, une mine de GRAPHITE, ou
  mieux, une électrode Ag/AgCl reliée par un pont salin.

  N'UTILISEZ NI CUIVRE NI LAITON. Deux métaux différents dans un substrat
  humide forment une pile galvanique : vous mesureriez votre propre montage,
  qui dérive de plusieurs millivolts par heure. Le cuivre est en outre
  toxique pour les racines.

  Après branchement, laissez la mesure se stabiliser dix à vingt minutes. La
  dérive initiale est celle de l'électrode, pas celle de la plante — c'est
  l'onglet Multimètre qui vous dira quand elle s'est calmée.

  ALIMENTATION SUR PILE OU BATTERIE EXCLUSIVEMENT. Jamais de raccordement au
  secteur du côté de la plante.


LES DIX ONGLETS
{'-' * 74}

  Oscilloscope    Le signal dans le temps. C'est l'onglet qu'on regarde le
                  plus. Fenêtre réglable de 5 secondes à 1 heure, sensibilité
                  de 2 µV à 10 mV. Les courbes sont zoomables ; {cmd}0 revient
                  au cadrage d'origine.

  Multimètre      Six grands nombres, quatre aiguilles, et deux pages :
                  « Grandeurs scientifiques » donne quinze quantités calculées
                  sur le signal brut — densité de bruit en nV/√Hz, résistance
                  équivalente, résidu de réseau, écart d'Allan, normalité…
                  chacune accompagnée de ce qu'elle dit et de ce qu'elle ne
                  dit pas. « Empreinte du montage » caractérise l'installation
                  du jour — et rappelle qu'elle n'identifie pas la plante.

  Analyseur      Le spectre. On y voit tout de suite si le secteur parasite
                  la mesure.

  Descripteurs   Six représentations du même signal : forme d'onde, FFT,
                  ondelettes de Morlet, MFCC, prédiction linéaire, cepstre.
                  Les constantes empruntées au traitement de la parole y sont
                  transposées d'après la cadence réelle, cinq décades plus bas
                  que la voix humaine.

  Traceur        Une ligne de commande à la façon de gnuplot, pour tracer ce
                  qu'on veut et exporter.

  Écoute         La sonification : gammes, instruments, tempo, et la façon
                  dont une variation de tension devient une note. Rien n'est
                  caché — les règles de correspondance sont affichées.

  Parole         Des mots au lieu de notes : un dictionnaire modifiable,
                  quatre grammaires, une synthèse vocale hors ligne. CE N'EST
                  PAS UNE TRADUCTION, et l'onglet le rappelle en permanence :
                  chaque énoncé est accompagné des valeurs mesurées qui l'ont
                  déclenché.

  Bibliothèque   Les séances enregistrées et les échantillons. Les deux se
                  rejouent DANS LE MOTEUR : on règle une sonification le soir,
                  sur le signal du matin.

  Diagnostic     Le bus USB, le journal, l'échantillonnage, la sortie sonore.
                  C'est là qu'on va quand quelque chose ne marche pas.

  Réglages       Source d'acquisition, filtrage, seuils, répertoire des
                  enregistrements, thème, langue.


ENREGISTRER
{'-' * 74}

  {cmd}R          démarre ou arrête l'enregistrement d'une séance. Elle
                  produit un répertoire complet : signal brut en WAV, mesures
                  en CSV, métadonnées en JSON, rendu musical. Tout est
                  relisible sans le logiciel.

  {cmd}E          garde la dernière minute écoulée sur le disque, sans rien
                  démarrer ni arrêter. C'est le carnet de croquis : quand on
                  comprend une minute trop tard que cela valait la peine.

  {cmd}M          pose un marqueur horodaté — « j'ai touché la feuille »,
                  « la porte a claqué ».

  L'espace disque est surveillé pendant l'enregistrement : alerte à vingt
  minutes d'autonomie, puis clôture propre avant saturation. Une séance close
  vaut infiniment mieux qu'une séance tronquée par une erreur d'écriture.


LES RACCOURCIS
{'-' * 74}

  {cmd}R    enregistrement          F1          aide
  {cmd}E    échantillon rapide      Maj+F1      à propos
  {cmd}M    marqueur                {cmd}L       journal du logiciel
  {cmd}K    couper le son           {cmd}0       revenir au cadrage d'origine
  {cmd}A    auto-configuration      {cmd}Q       quitter proprement
  {cmd}.    silence immédiat

  Dans un terminal, Ctrl+C interrompt toujours : la séance est close, les
  réglages sauvés, puis le programme s'arrête. Un second Ctrl+C termine sans
  attendre.


LE MATÉRIEL
{'-' * 74}

{materiel}

  Trois autres sources fonctionnent aussi : une carte son ordinaire (par une
  entrée microphone), un montage série maison (Arduino, NE555), et le
  générateur interne.


ONZE LANGUES
{'-' * 74}

  Français, anglais, espagnol, portugais, italien, indonésien, russe,
  chinois, japonais, coréen et arabe — avec inversion de la mise en page pour
  ce dernier. Le choix se fait dans Réglages, ou dans le menu Affichage.

  Le français est le défaut au premier lancement, quelle que soit la langue
  du système : c'est un choix, pas un oubli.


OÙ SONT VOS FICHIERS
{'-' * 74}

{emplacements}

  Ils ne sont JAMAIS effacés par une désinstallation ni par une mise à jour.


QUAND QUELQUE CHOSE NE VA PAS
{'-' * 74}

  {cmd}L ouvre le journal : son emplacement en toutes lettres, son contenu
  qui se complète en direct, un filtre, et « Enregistrer une copie… » vers
  l'endroit de votre choix. C'est ce fichier qu'il faut joindre à un
  signalement — en pensant aux archives de rotation, car un incident d'il y a
  une heure s'y trouve souvent plutôt que dans le fichier courant.

  L'onglet Diagnostic complète : énumération du bus USB, auto-test de la
  carte, capture des trames, test de la sortie sonore.

  Le bruit est élevé, la dérive forte ?  Regardez d'abord la page
  « Grandeurs scientifiques » du Multimètre. Une résistance équivalente qui
  grimpe d'une décade en quelques minutes signale un contact qui sèche. Un
  résidu de réseau au-delà de 20 dB au-dessus du plancher signale un problème
  de blindage — et non un réjecteur à activer, qui masquerait le symptôme
  sans traiter la cause.


CE QUE CE LOGICIEL NE PRÉTEND PAS FAIRE
{'-' * 74}

  Il ne traduit pas une plante. Les mots de l'onglet Parole sont produits par
  des règles que vous pouvez lire et modifier ; ils ne viennent pas de la
  plante.

  Il ne l'identifie pas. L'empreinte du Multimètre caractérise un MONTAGE —
  plante, électrodes, substrat, câble, carte — tel qu'il est à cet instant.
  Deux mesures du même végétal à deux jours d'intervalle diffèrent souvent
  davantage que deux végétaux voisins le même après-midi.

  Il ne diagnostique rien et ne soigne rien.

  Ce qu'il fait, il le fait honnêtement : il mesure, il montre, il enregistre,
  et il dit ce qu'il ne sait pas.


  {id_.auteur} — {id_.site}
  Licence MIT. Aucune télémétrie, aucun compte, aucun réseau.
"""


def _licence(id_: "Identite") -> str:
    """La licence du logiciel, recopiée depuis sa source."""
    chemin = os.path.join(LOGICIEL, "LICENCE.txt")
    try:
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    except OSError:                                    # pragma: no cover
        return (f"PhytoScope {id_.version} — licence MIT\n"
                f"{id_.auteur} — {id_.site}\n")


def _changelog(id_: "Identite") -> str:
    """Le journal des versions, recopié depuis sa source."""
    chemin = os.path.join(LOGICIEL, "CHANGELOG.txt")
    try:
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    except OSError:                                    # pragma: no cover
        return f"PhytoScope {id_.version} — journal indisponible.\n"


# ---------------------------------------------------------------------------
#  Archives et interpréteur embarqué
# ---------------------------------------------------------------------------
def cible_pbs(systeme: str, arch: str = "") -> str:
    """Triplet « python-build-standalone » pour un système et une machine."""
    if not arch:
        arch = platform.machine().lower()
    return CIBLES_PBS.get((systeme, arch), "")


def _python_autonome(vers: str, systeme: str, arch: str = "") -> bool:
    """Récupère et déplie un CPython relogeable pour Linux ou macOS.

    Pendant de `_python_embarquable()`, qui fait la même chose pour Windows
    avec la distribution officielle. Ici la source est
    « python-build-standalone » : mêmes binaires que ceux qu'utilise `uv`.

    L'archive se déplie en un dossier `python/` contenant `bin/`, `lib/` et
    `include/`. On le range donc *dans* ``vers``, et l'appelant trouvera
    l'interpréteur à ``<vers>/bin/python3``.

    Rend False sans rien casser si le téléchargement échoue : l'installateur
    retombe alors sur le Python du système, comme avant.
    """
    import urllib.request

    cible = cible_pbs(systeme, arch)
    if not cible:
        souci(f"aucun Python autonome connu pour {systeme}/{arch or platform.machine()}")
        return False

    url = (f"https://github.com/astral-sh/python-build-standalone/releases/"
           f"download/{PBS_TAG}/cpython-{PYTHON_AUTONOME}+{PBS_TAG}-"
           f"{cible}-install_only.tar.gz")
    parent = os.path.dirname(os.path.abspath(vers)) or "."
    os.makedirs(parent, exist_ok=True)
    archive = os.path.join(parent, "_python-autonome.tar.gz")
    try:
        urllib.request.urlretrieve(url, archive)
    except Exception as exc:                           # noqa: BLE001
        echec(f"téléchargement du Python autonome impossible : {exc}")
        return False

    try:
        #  L'archive contient un unique dossier « python/ » : on le déplie
        #  dans le parent, puis on le renomme vers la destination demandée.
        with tarfile.open(archive) as tar:
            tar.extractall(parent)
    except Exception as exc:                           # noqa: BLE001
        echec(f"archive du Python autonome illisible : {exc}")
        return False
    finally:
        if os.path.exists(archive):
            os.remove(archive)

    deplie = os.path.join(parent, "python")
    if not os.path.isdir(deplie):
        echec("l'archive du Python autonome n'a pas la forme attendue")
        return False
    if os.path.abspath(deplie) != os.path.abspath(vers):
        if os.path.isdir(vers):
            shutil.rmtree(vers)
        shutil.move(deplie, vers)

    interp = os.path.join(vers, "bin", "python3")
    if not os.path.exists(interp):
        echec(f"interpréteur absent de {vers}")
        return False

    #  Ces binaires sont relogeables mais volumineux : les tests, la
    #  documentation et les fichiers de compilation ne servent à rien dans un
    #  paquet d'installation, et pèsent plusieurs dizaines de mégaoctets.
    for inutile in ("lib/python%s/test" % PYTHON_AUTONOME[:4],
                    "lib/python%s/idlelib" % PYTHON_AUTONOME[:4],
                    "lib/python%s/tkinter" % PYTHON_AUTONOME[:4],
                    "share/man", "share/doc"):
        chemin = os.path.join(vers, inutile)
        if os.path.isdir(chemin):
            shutil.rmtree(chemin, ignore_errors=True)

    return True


def _python_embarquable(vers: str) -> bool:
    """Récupère et déplie la distribution Windows embarquable de Python.

    C'est elle qui permet de livrer un logiciel Python sans rien exiger de la
    machine : l'archive contient l'interpréteur, sa bibliothèque standard et
    ses DLL, et ne s'inscrit ni dans la base de registre ni dans le PATH.
    """
    import urllib.request
    url = (f"https://www.python.org/ftp/python/{PYTHON_WINDOWS}/"
           f"python-{PYTHON_WINDOWS}-embed-amd64.zip")
    os.makedirs(vers, exist_ok=True)
    archive = os.path.join(vers, "_python.zip")
    try:
        urllib.request.urlretrieve(url, archive)
    except Exception as exc:                           # noqa: BLE001
        echec(f"téléchargement impossible : {exc}")
        return False
    with zipfile.ZipFile(archive) as z:
        z.extractall(vers)
    os.remove(archive)

    #  Le fichier « ._pth » d'une distribution embarquable verrouille le chemin
    #  d'import : sans « import site » ni le dossier site-packages, aucune
    #  bibliothèque installée ne serait visible. On le réécrit.
    for nom in os.listdir(vers):
        if nom.endswith("._pth"):
            with open(os.path.join(vers, nom), "w", encoding="utf-8",
                      newline="\n") as f:
                f.write(f"python{ABI_WINDOWS}.zip\n.\nLib\\site-packages\n"
                        "..\\app\n\nimport site\n")
    os.makedirs(os.path.join(vers, "Lib", "site-packages"), exist_ok=True)
    return True


def _zipper(source: str, cible: str, racine_interne: str = "") -> None:
    """Compresse un dossier en conservant les droits d'exécution.

    `zipfile` n'écrit pas les permissions par défaut ; or macOS en dépend pour
    le lanceur d'un paquet `.app`. Sans le bit d'exécution, l'application ne
    s'ouvre pas — et n'explique pas pourquoi.
    """
    with zipfile.ZipFile(cible, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=6) as z:
        for dossier, _, fichiers in os.walk(source):
            for nom in fichiers:
                complet = os.path.join(dossier, nom)
                relatif = os.path.relpath(complet, source)
                interne = os.path.join(racine_interne, relatif) \
                    if racine_interne else relatif
                info = zipfile.ZipInfo.from_file(complet, interne)
                info.compress_type = zipfile.ZIP_DEFLATED
                mode = os.stat(complet).st_mode
                info.external_attr = (mode & 0xFFFF) << 16
                with open(complet, "rb") as f:
                    z.writestr(info, f.read())
