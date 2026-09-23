# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/preflight.py
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

"""Contrôles avant vol — ce qui manque, pourquoi, et comment l'obtenir.

Un logiciel qui refuse de démarrer doit dire **exactement** ce qui lui
manque. Trois causes distinctes sont couramment confondues, et ce module les
sépare soigneusement :

1. **Le paquet Python est absent.**
   Remède : ``pip install``. Le logiciel peut le proposer et le faire.

2. **Le paquet Python est présent, mais son import échoue** parce qu'une
   bibliothèque *système* manque. Cas le plus fréquent sous Linux :
   PySide6 est bien installé, mais ``libGL.so.1`` est introuvable. Aucun
   ``pip install`` ne corrigera cela ; il faut un paquet système.
   Le message d'erreur brut est analysé pour nommer le paquet exact.

3. **L'environnement Python est « géré par le système »** (PEP 668).
   ``pip install`` refuse alors de s'exécuter. Trois issues existent, et le
   module les propose dans l'ordre de sécurité décroissant : environnement
   virtuel, installation utilisateur, dérogation explicite.

Le rapport produit est utilisable en console (avec couleurs) comme dans une
fenêtre graphique : c'est le même objet, rendu de deux façons.

Motifs de conception employés : *Value Object* pour `Requirement` et
`PreflightReport`, *Strategy* pour les stratégies d'installation,
*Facade* pour la fonction `run()`.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from . import console as C
from .logging_setup import get_logger

log = get_logger(__name__)

PYTHON_MINIMUM = (3, 9)


# ---------------------------------------------------------------------------
#  Modèle
# ---------------------------------------------------------------------------
class Statut(Enum):
    """État d'un prérequis, du meilleur au pire."""
    PRESENT = "présent"
    ABSENT = "absent"
    CASSE = "présent mais inutilisable"
    INCONNU = "non vérifié"


@dataclass(frozen=True)
class Requirement:
    """Description d'un prérequis Python (objet-valeur, immuable)."""
    module: str                    # nom d'import
    paquet: str                    # nom pip
    role: str                      # à quoi il sert, en français
    obligatoire: bool = True
    version_min: str = ""

    def __str__(self) -> str:      # pragma: no cover
        return f"{self.module} ({self.paquet})"


@dataclass
class CheckResult:
    """Résultat du contrôle d'un prérequis."""
    requirement: Requirement
    statut: Statut = Statut.INCONNU
    version: str = ""
    erreur: str = ""               # message brut de l'ImportError
    bibliotheque_manquante: str = ""   # ex. « libGL.so.1 »
    paquet_systeme: str = ""       # ex. « libgl1 »
    commande_systeme: str = ""     # ex. « sudo apt install libgl1 »
    #  Vrai quand la bibliothèque EST installée sur le système mais que
    #  l'interpréteur courant ne peut pas l'atteindre. Le remède n'est alors
    #  pas d'installer un paquet — il est déjà là — mais de changer
    #  d'interpréteur. Voir `interpreteur_etranger()`.
    presente_mais_inatteignable: bool = False

    @property
    def ok(self) -> bool:
        return self.statut is Statut.PRESENT

    @property
    def bloquant(self) -> bool:
        return self.requirement.obligatoire and not self.ok


# ---------------------------------------------------------------------------
#  Table des prérequis
# ---------------------------------------------------------------------------
REQUIREMENTS: Tuple[Requirement, ...] = (
    Requirement("numpy", "numpy", "traitement du signal", True, "1.24"),
    Requirement("PySide6", "PySide6", "interface graphique Qt 6", True, "6.5"),
    Requirement("pyqtgraph", "pyqtgraph", "tracés temps réel accélérés", False),
    Requirement("sounddevice", "sounddevice", "entrée et sortie audio", False),
    Requirement("serial", "pyserial", "contrôle de la carte, montages série", False),
    Requirement("rtmidi", "python-rtmidi", "sortie MIDI", False),
    Requirement("pyttsx3", "pyttsx3", "synthèse vocale du mode Parole", False),
    Requirement("usb.core", "pyusb", "descripteurs USB détaillés", False),
)


# ---------------------------------------------------------------------------
#  Bibliothèques système : diagnostic des imports cassés
# ---------------------------------------------------------------------------
#  Correspondance bibliothèque partagée → paquet, par famille de distribution.
BIBLIOTHEQUES: Dict[str, Dict[str, str]] = {
    "libGL.so.1":            {"apt": "libgl1", "dnf": "mesa-libGL",
                              "pacman": "libglvnd", "brew": "", "zypper": "Mesa-libGL1"},
    "libEGL.so.1":           {"apt": "libegl1", "dnf": "mesa-libEGL",
                              "pacman": "libglvnd", "zypper": "Mesa-libEGL1"},
    "libGLX.so.0":           {"apt": "libglx0", "dnf": "libglvnd-glx",
                              "pacman": "libglvnd", "zypper": "libglvnd"},
    "libGLdispatch.so.0":    {"apt": "libglvnd0", "dnf": "libglvnd",
                              "pacman": "libglvnd", "zypper": "libglvnd"},
    "libGLESv2.so.2":        {"apt": "libglvnd0", "dnf": "libglvnd",
                              "pacman": "libglvnd"},
    "libOpenGL.so.0":        {"apt": "libopengl0", "dnf": "mesa-libGL",
                              "pacman": "libglvnd"},
    "libxkbcommon-x11.so.0": {"apt": "libxkbcommon-x11-0", "dnf": "libxkbcommon-x11",
                              "pacman": "libxkbcommon-x11"},
    "libxkbcommon.so.0":     {"apt": "libxkbcommon0", "dnf": "libxkbcommon",
                              "pacman": "libxkbcommon"},
    "libxcb-cursor.so.0":    {"apt": "libxcb-cursor0", "dnf": "xcb-util-cursor",
                              "pacman": "xcb-util-cursor"},
    "libxcb-xinerama.so.0":  {"apt": "libxcb-xinerama0", "dnf": "libxcb",
                              "pacman": "libxcb"},
    "libxcb-icccm.so.4":     {"apt": "libxcb-icccm4", "dnf": "xcb-util-wm",
                              "pacman": "xcb-util-wm"},
    "libxcb-image.so.0":     {"apt": "libxcb-image0", "dnf": "xcb-util-image",
                              "pacman": "xcb-util-image"},
    "libxcb-keysyms.so.1":   {"apt": "libxcb-keysyms1", "dnf": "xcb-util-keysyms",
                              "pacman": "xcb-util-keysyms"},
    "libxcb-render-util.so.0": {"apt": "libxcb-render-util0", "dnf": "xcb-util-renderutil",
                                "pacman": "xcb-util-renderutil"},
    "libportaudio.so.2":     {"apt": "libportaudio2", "dnf": "portaudio",
                              "pacman": "portaudio", "brew": "portaudio"},
    "libasound.so.2":        {"apt": "libasound2", "dnf": "alsa-lib",
                              "pacman": "alsa-lib"},
    "librtmidi.so":          {"apt": "librtmidi-dev", "dnf": "rtmidi",
                              "pacman": "rtmidi"},
    "libglib-2.0.so.0":      {"apt": "libglib2.0-0", "dnf": "glib2",
                              "pacman": "glib2"},
    "libdbus-1.so.3":        {"apt": "libdbus-1-3", "dnf": "dbus-libs",
                              "pacman": "dbus"},
    "libfontconfig.so.1":    {"apt": "libfontconfig1", "dnf": "fontconfig",
                              "pacman": "fontconfig"},
    "libfreetype.so.6":      {"apt": "libfreetype6", "dnf": "freetype",
                              "pacman": "freetype2"},
}

#  Ensemble minimal qui fait fonctionner Qt 6 sur une installation nue.
QT_PAQUETS = {
    "apt": ["libgl1", "libegl1", "libxkbcommon-x11-0", "libxcb-cursor0",
            "libxcb-icccm4", "libxcb-keysyms1", "libxcb-render-util0",
            "libxcb-shape0", "libdbus-1-3", "libfontconfig1"],
    "dnf": ["mesa-libGL", "mesa-libEGL", "libxkbcommon-x11", "xcb-util-cursor",
            "xcb-util-wm", "xcb-util-keysyms", "xcb-util-renderutil",
            "dbus-libs", "fontconfig"],
    "pacman": ["libglvnd", "libxkbcommon-x11", "xcb-util-cursor", "xcb-util-wm",
               "xcb-util-keysyms", "xcb-util-renderutil", "dbus", "fontconfig"],
}

AUDIO_PAQUETS = {"apt": ["libportaudio2", "libasound2"],
                 "dnf": ["portaudio", "alsa-lib"],
                 "pacman": ["portaudio", "alsa-lib"],
                 "brew": ["portaudio"]}


def gestionnaire_paquets() -> str:
    """Gestionnaire de paquets du système, ou chaîne vide si indéterminé."""
    if sys.platform == "darwin":
        return "brew" if shutil.which("brew") else ""
    if sys.platform.startswith("win"):
        return ""
    for outil, cle in (("apt-get", "apt"), ("dnf", "dnf"), ("pacman", "pacman"),
                       ("zypper", "zypper"), ("apk", "apk")):
        if shutil.which(outil):
            return cle
    return ""


def commande_installation(paquets: Sequence[str], gestionnaire: str = "") -> str:
    """Commande d'installation système, prête à copier-coller."""
    g = gestionnaire or gestionnaire_paquets()
    if not paquets:
        return ""
    liste = " ".join(paquets)
    return {
        "apt": f"sudo apt install {liste}",
        "dnf": f"sudo dnf install {liste}",
        "pacman": f"sudo pacman -S {liste}",
        "zypper": f"sudo zypper install {liste}",
        "apk": f"sudo apk add {liste}",
        "brew": f"brew install {liste}",
    }.get(g, f"(installez les paquets suivants : {liste})")


_RE_LIB = re.compile(r"(lib[\w.+-]*\.so[\w.]*)")


def _resoudre_chemin(nom: str) -> str:
    """Chemin absolu d'une bibliothèque, d'après ldconfig puis les répertoires usuels."""
    try:
        sortie = subprocess.run(["ldconfig", "-p"], capture_output=True, text=True,
                                timeout=5).stdout
        for ligne in sortie.splitlines():
            if nom in ligne and "=>" in ligne:
                return ligne.split("=>")[-1].strip()
    except Exception:
        pass
    for base in ("/usr/lib/x86_64-linux-gnu", "/usr/lib64", "/usr/lib",
                 "/lib/x86_64-linux-gnu", "/usr/local/lib"):
        chemin = os.path.join(base, nom)
        if os.path.exists(chemin):
            return chemin
    return ""


def presente_sur_le_systeme(nom: str) -> str:
    """Chemin de la bibliothèque si le SYSTÈME la connaît, sinon "".

    À ne pas confondre avec « on sait la charger ». Un interpréteur installé
    hors du système — Homebrew, Nix, conda, une construction maison — vient
    souvent avec son propre chargeur dynamique et son propre chemin de
    recherche ; il ne voit pas `/lib/x86_64-linux-gnu`. La bibliothèque est
    alors présente et pourtant introuvable, et conseiller
    « sudo apt install libgl1 » envoie réinstaller un paquet déjà là.

    On interroge donc le système par `ldconfig`, qui répond pour le système
    et non pour nous.
    """
    return _resoudre_chemin(nom)


def interpreteur_etranger() -> str:
    """Dit d'où vient l'interpréteur courant s'il n'est pas celui du système.

    Rend une phrase prête à afficher, ou "" si l'interpréteur est celui du
    système ou un environnement virtuel bâti sur lui.
    """
    reel = os.path.realpath(getattr(sys, "_base_executable", None) or sys.executable)
    for prefixe, origine in (
        ("/home/linuxbrew/.linuxbrew", "Homebrew"),
        ("/opt/homebrew", "Homebrew"),
        ("/usr/local/Cellar", "Homebrew"),
        ("/nix/store", "Nix"),
        ("/opt/conda", "conda"),
        ("/opt/miniconda", "conda"),
        ("/opt/anaconda", "conda"),
    ):
        if reel.startswith(prefixe):
            return f"{origine} ({reel})"
    #  conda se signale aussi par une variable d'environnement
    if os.environ.get("CONDA_PREFIX") and reel.startswith(os.environ["CONDA_PREFIX"]):
        return f"conda ({reel})"
    return ""


def sonder_bibliotheque(nom: str, profondeur: int = 4) -> str:
    """Trouve la bibliothèque RÉELLEMENT manquante derrière une erreur de chargement.

    Le message du chargeur dynamique est trompeur : quand ``libGL.so.1`` est
    présent mais qu'il lui manque ``libGLdispatch.so.0``, Linux annonce
    « libGL.so.1: cannot open shared object file ». L'utilisateur réinstalle
    alors en boucle un paquet déjà présent.

    Cette fonction charge la bibliothèque avec ctypes, et suit la chaîne des
    dépendances jusqu'à nommer celle qui manque vraiment.
    """
    if not sys.platform.startswith("linux") or not nom:
        return nom
    try:
        import ctypes
    except ImportError:                                # pragma: no cover
        return nom
    courant = nom
    for _ in range(max(profondeur, 1)):
        chemin = _resoudre_chemin(courant)
        cible = chemin or courant
        try:
            ctypes.CDLL(cible)
            return ""                       # tout se charge : plus rien ne manque
        except OSError as exc:
            suivant = _RE_LIB.search(str(exc))
            nom_suivant = suivant.group(1) if suivant else ""
            if not nom_suivant:
                return courant
            if nom_suivant == courant:
                # le chargeur nomme la bibliothèque elle-même : soit elle est
                # absente, soit le chemin résolu n'existe pas
                return courant if not chemin else courant
            courant = nom_suivant
        except Exception:                              # pragma: no cover
            return courant
    return courant


def analyser_import_casse(message: str) -> Tuple[str, str, str, bool]:
    """D'un message d'ImportError, tire (bibliothèque, paquet, commande, présente).

    La bibliothèque nommée par le chargeur n'est pas toujours celle qui
    manque : on sonde la chaîne de dépendances pour nommer la bonne.

    Le quatrième élément vaut ``True`` quand la bibliothèque est **installée
    sur le système** et que c'est l'interpréteur courant qui ne l'atteint pas.
    Il n'y a alors rien à installer, et le dire évite d'envoyer quelqu'un
    réinstaller en boucle un paquet déjà présent.
    """
    m = _RE_LIB.search(message or "")
    if not m:
        return "", "", "", False
    lib = m.group(1)
    reelle = sonder_bibliotheque(lib)
    if reelle and reelle != lib:
        log.info("Bibliothèque annoncée %s, réellement manquante : %s", lib, reelle)
        lib = reelle

    #  Avant de conseiller un paquet : le système l'a-t-il déjà ? Si oui, le
    #  défaut est chez nous — un interpréteur venu d'ailleurs (Homebrew, Nix,
    #  conda) ne lit pas le chemin de recherche du système.
    chemin = presente_sur_le_systeme(lib)
    if chemin:
        log.info("%s est présente (%s) mais illisible depuis %s",
                 lib, chemin, sys.executable)
        return lib, "", "", True

    table = BIBLIOTHEQUES.get(lib)
    if table is None:
        # tolérance aux suffixes de version : libGL.so.1.7.0 → libGL.so.1
        for connue in BIBLIOTHEQUES:
            if lib.startswith(connue.rsplit(".", 1)[0]):
                table = BIBLIOTHEQUES[connue]
                lib = connue
                break
    if table is None:
        return lib, "", "", False
    g = gestionnaire_paquets()
    paquet = table.get(g, "")
    commande = commande_installation([paquet], g) if paquet else ""
    return lib, paquet, commande, False


# ---------------------------------------------------------------------------
#  Contrôles
# ---------------------------------------------------------------------------
def verifier(requirement: Requirement) -> CheckResult:
    """Contrôle un prérequis en séparant absence et import cassé."""
    res = CheckResult(requirement=requirement)
    racine = requirement.module.split(".")[0]
    try:
        spec = importlib.util.find_spec(racine)
    except (ImportError, ValueError):
        spec = None
    if spec is None:
        res.statut = Statut.ABSENT
        log.debug("Prérequis absent : %s", requirement.module)
        return res
    try:
        module = importlib.import_module(requirement.module)
        res.version = str(getattr(module, "__version__", "") or
                          getattr(sys.modules.get(racine), "__version__", "") or
                          "présent")
        res.statut = Statut.PRESENT
    except BaseException as exc:                       # noqa: BLE001
        # Un import cassé lève parfois autre chose qu'ImportError.
        res.statut = Statut.CASSE
        res.erreur = f"{type(exc).__name__}: {exc}"
        (res.bibliotheque_manquante, res.paquet_systeme,
         res.commande_systeme,
         res.presente_mais_inatteignable) = analyser_import_casse(str(exc))
        log.error("Import de %s impossible : %s", requirement.module, res.erreur)
    return res


# ---------------------------------------------------------------------------
#  Environnement Python
# ---------------------------------------------------------------------------
@dataclass
class EnvInfo:
    """Ce qu'il faut savoir de l'interpréteur avant d'installer quoi que ce soit."""
    version: str = ""
    executable: str = ""
    in_venv: bool = False
    venv_path: str = ""
    externally_managed: bool = False       # PEP 668
    pip_present: bool = False
    writable: bool = False
    base_prefix: str = ""
    homebrew_linux: bool = False           # piège connu : voir plus bas
    python_systeme: str = ""               # interpréteur de la distribution

    def resume(self) -> str:
        base = ""
        if self.in_venv:
            base = f"environnement virtuel ({self.venv_path})"
        elif self.externally_managed:
            base = "interpréteur système, géré par la distribution (PEP 668)"
        else:
            base = "interpréteur système"
        if self.homebrew_linux:
            base += " — construit sur le Python Homebrew"
        return base


def _python_systeme() -> str:
    """Interpréteur fourni par la distribution, hors Homebrew et hors pyenv."""
    for chemin in ("/usr/bin/python3", "/usr/local/bin/python3", "/bin/python3"):
        if os.path.exists(chemin) and "linuxbrew" not in os.path.realpath(chemin):
            try:
                sortie = subprocess.run([chemin, "-c",
                                         "import sys;print('%d.%d' % sys.version_info[:2])"],
                                        capture_output=True, text=True, timeout=5)
                majeur, _, mineur = sortie.stdout.strip().partition(".")
                if (int(majeur), int(mineur or 0)) >= PYTHON_MINIMUM:
                    return chemin
            except Exception:
                continue
    return ""


def inspecter_environnement() -> EnvInfo:
    info = EnvInfo(version=platform.python_version(), executable=sys.executable)
    info.in_venv = (hasattr(sys, "real_prefix") or
                    (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix))
    info.venv_path = sys.prefix if info.in_venv else ""
    info.base_prefix = getattr(sys, "base_prefix", sys.prefix)
    # Piège classique : sous GNU/Linux, le Python de Homebrew embarque sa
    # propre glibc et son propre chargeur dynamique. Il ne sait pas résoudre
    # les bibliothèques du système (libGL, libportaudio…), et les mélanger
    # fait parfois planter le processus. Il faut alors bâtir l'environnement
    # virtuel sur l'interpréteur de la distribution.
    if sys.platform.startswith("linux"):
        chemins = (sys.executable or "") + " " + (info.base_prefix or "")
        info.homebrew_linux = "linuxbrew" in chemins or "/home/linuxbrew" in chemins
        if info.homebrew_linux:
            info.python_systeme = _python_systeme()
    try:
        import sysconfig
        stdlib = sysconfig.get_path("stdlib")
        info.externally_managed = os.path.exists(
            os.path.join(stdlib or "", "EXTERNALLY-MANAGED"))
    except Exception:                                  # pragma: no cover
        info.externally_managed = False
    info.pip_present = importlib.util.find_spec("pip") is not None
    try:
        import site
        chemins = site.getsitepackages() if hasattr(site, "getsitepackages") else []
        info.writable = any(os.access(p, os.W_OK) for p in chemins) if chemins else False
    except Exception:                                  # pragma: no cover
        info.writable = False
    return info


# ---------------------------------------------------------------------------
#  Rapport
# ---------------------------------------------------------------------------
@dataclass
class PreflightReport:
    """Synthèse des contrôles : le même objet sert à la console et à Qt."""
    python_ok: bool = True
    python_version: str = ""
    env: EnvInfo = field(default_factory=EnvInfo)
    resultats: List[CheckResult] = field(default_factory=list)
    repertoires: List[Tuple[str, str, bool]] = field(default_factory=list)
    avertissements: List[str] = field(default_factory=list)

    # -- synthèses -----------------------------------------------------------
    @property
    def bloquants(self) -> List[CheckResult]:
        return [r for r in self.resultats if r.bloquant]

    @property
    def absents(self) -> List[CheckResult]:
        return [r for r in self.resultats if r.statut is Statut.ABSENT]

    @property
    def casses(self) -> List[CheckResult]:
        return [r for r in self.resultats if r.statut is Statut.CASSE]

    @property
    def peut_demarrer(self) -> bool:
        return self.python_ok and not self.bloquants

    @property
    def peut_demarrer_sans_interface(self) -> bool:
        bloquants = [r for r in self.bloquants if r.requirement.module != "PySide6"]
        return self.python_ok and not bloquants

    def paquets_a_installer(self, tous: bool = False) -> List[str]:
        return [r.requirement.paquet for r in self.absents
                if tous or r.requirement.obligatoire]

    def paquets_systeme_manquants(self) -> List[str]:
        return sorted({r.paquet_systeme for r in self.casses if r.paquet_systeme})

    def commande_systeme(self) -> str:
        paquets = self.paquets_systeme_manquants()
        if not paquets:
            return ""
        g = gestionnaire_paquets()
        # Qt casse rarement seul : on propose l'ensemble minimal cohérent.
        if any(p in QT_PAQUETS.get(g, []) for p in paquets):
            paquets = sorted(set(paquets) | set(QT_PAQUETS.get(g, [])))
        return commande_installation(paquets, g)

    # -- rendus --------------------------------------------------------------
    def to_console(self) -> str:
        lignes: List[str] = []
        lignes.append(C.titre("Pre-flight checks"))
        lignes.append("")
        etat = "ok" if self.python_ok else "err"
        lignes.append(C.ligne_statut(etat, f"Python {self.python_version}",
                                     self.env.resume(), 26))
        for r in self.resultats:
            req = r.requirement
            if r.statut is Statut.PRESENT:
                lignes.append(C.ligne_statut("ok", req.module, f"{r.version}  {req.role}", 26))
            elif r.statut is Statut.ABSENT:
                lignes.append(C.ligne_statut("err" if req.obligatoire else "warn",
                                             req.module,
                                             f"absent — {req.role}", 26))
            else:
                detail = (f"installé mais inutilisable : "
                          f"{r.bibliotheque_manquante or r.erreur}")
                lignes.append(C.ligne_statut("err" if req.obligatoire else "warn",
                                             req.module, detail, 26))
        for chemin, role, ok in self.repertoires:
            lignes.append(C.ligne_statut("ok" if ok else "warn", role,
                                         chemin, 26))
        for a in self.avertissements:
            lignes.append("  " + C.alerte("! " + a))
        return "\n".join(lignes)

    def to_html(self) -> str:
        """Rendu pour la fenêtre de démarrage."""
        lignes = ["<table cellspacing='6'>"]
        def ligne(couleur, nom, detail):
            return (f"<tr><td style='color:{couleur}'>&#9679;</td>"
                    f"<td><b>{nom}</b></td><td>{detail}</td></tr>")
        lignes.append(ligne("#7FE0A8" if self.python_ok else "#E06C5A",
                            f"Python {self.python_version}", self.env.resume()))
        for r in self.resultats:
            if r.statut is Statut.PRESENT:
                lignes.append(ligne("#7FE0A8", r.requirement.module,
                                    f"{r.version} — {r.requirement.role}"))
            elif r.statut is Statut.ABSENT:
                couleur = "#E06C5A" if r.requirement.obligatoire else "#E0C073"
                lignes.append(ligne(couleur, r.requirement.module,
                                    f"absent — {r.requirement.role}"))
            else:
                couleur = "#E06C5A" if r.requirement.obligatoire else "#E0C073"
                detail = (f"installé mais inutilisable — bibliothèque système "
                          f"<code>{r.bibliotheque_manquante}</code> introuvable"
                          if r.bibliotheque_manquante else
                          f"installé mais inutilisable — {r.erreur}")
                lignes.append(ligne(couleur, r.requirement.module, detail))
        lignes.append("</table>")
        return "".join(lignes)

    def conseils(self) -> List[str]:
        """Les actions concrètes à proposer, dans l'ordre."""
        out: List[str] = []
        # Le piège Homebrew passe avant tout le reste : tant qu'il n'est pas
        # levé, aucune installation de paquet ne corrigera quoi que ce soit.
        if self.env.homebrew_linux and self.casses:
            cible = self.env.python_systeme or "/usr/bin/python3"
            out.append(
                "L'interpréteur vient de Homebrew et ne peut pas charger les "
                "bibliothèques du système. Reconstruisez l'environnement sur le "
                f"Python de la distribution :  make distclean && make install PYTHON={cible}")
            return out
        if not self.python_ok:
            out.append(f"Installez Python {PYTHON_MINIMUM[0]}.{PYTHON_MINIMUM[1]} "
                       "ou plus récent.")
        paquets = self.paquets_a_installer(tous=True)
        if paquets:
            out.append("Installer les paquets Python manquants : " +
                       " ".join(paquets))
        cmd = self.commande_systeme()
        if cmd:
            out.append("Installer les bibliothèques système : " + cmd)
        if self.env.externally_managed and not self.env.in_venv and paquets:
            out.append("Cet interpréteur est géré par le système : préférez "
                       "« make install », qui crée un environnement virtuel.")
        return out


# ---------------------------------------------------------------------------
#  Installation (Strategy)
# ---------------------------------------------------------------------------
class InstallStrategy:
    """Stratégie d'installation de paquets Python."""
    nom = "générique"
    description = ""

    def disponible(self, env: EnvInfo) -> bool:        # pragma: no cover
        return env.pip_present

    def commande(self, paquets: Sequence[str]) -> List[str]:   # pragma: no cover
        raise NotImplementedError


class PipVenv(InstallStrategy):
    nom = "environnement virtuel"
    description = "installe dans l'environnement virtuel courant (le plus sûr)"

    def disponible(self, env: EnvInfo) -> bool:
        return env.pip_present and env.in_venv

    def commande(self, paquets):
        return [sys.executable, "-m", "pip", "install", *paquets]


class PipUser(InstallStrategy):
    nom = "installation utilisateur"
    description = "installe dans votre répertoire personnel (--user)"

    def disponible(self, env: EnvInfo) -> bool:
        return env.pip_present and not env.in_venv

    def commande(self, paquets):
        return [sys.executable, "-m", "pip", "install", "--user", *paquets]


class PipBreakSystem(InstallStrategy):
    nom = "dérogation système"
    description = ("passe outre la protection de la distribution "
                   "(--break-system-packages) — à éviter")

    def disponible(self, env: EnvInfo) -> bool:
        return env.pip_present and env.externally_managed and not env.in_venv

    def commande(self, paquets):
        return [sys.executable, "-m", "pip", "install",
                "--break-system-packages", "--user", *paquets]


def strategies(env: EnvInfo) -> List[InstallStrategy]:
    """Stratégies applicables, de la plus sûre à la moins sûre."""
    return [s for s in (PipVenv(), PipUser(), PipBreakSystem()) if s.disponible(env)]


def installer(paquets: Sequence[str], strategie: Optional[InstallStrategy] = None,
              env: Optional[EnvInfo] = None,
              sortie: Optional[Callable[[str], None]] = None) -> bool:
    """Installe des paquets ; renvoie True si la commande a réussi.

    La sortie de pip est transmise ligne par ligne à `sortie`, ce qui permet
    de l'afficher aussi bien en console que dans une fenêtre.
    """
    if not paquets:
        return True
    env = env or inspecter_environnement()
    strategie = strategie or (strategies(env)[0] if strategies(env) else None)
    if strategie is None:
        log.error("Aucune stratégie d'installation disponible (pip absent ?).")
        return False
    cmd = strategie.commande(paquets)
    log.warning("Installation (%s) : %s", strategie.nom, " ".join(cmd))
    if sortie:
        sortie("$ " + " ".join(cmd))
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace")
        for ligne in proc.stdout or []:
            ligne = ligne.rstrip()
            if sortie:
                sortie(ligne)
            else:
                print("   " + ligne)
        code = proc.wait()
    except Exception as exc:                           # noqa: BLE001
        log.error("Installation impossible : %s", exc)
        if sortie:
            sortie(f"ERREUR : {exc}")
        return False
    if code != 0:
        log.error("pip a échoué avec le code %d", code)
    return code == 0


# ---------------------------------------------------------------------------
#  Façade
# ---------------------------------------------------------------------------
#  Le lanceur `run.py` écarte les interpréteurs qui ne voient pas les
#  bibliothèques du système — Homebrew, Nix, conda — et se relance avec un
#  autre. Il le faisait en écrivant trois lignes sur la sortie d'erreur à
#  chaque lancement ; c'était du bruit. Il laisse maintenant cette trace,
#  et c'est le bilan de démarrage qui la rapporte, une fois, au bon endroit.
#
#  Format : « origine|interpréteur écarté|interpréteur retenu ». Le dernier
#  champ est vide si aucun ne convenait, ou porte le message d'échec.
INTERPRETEUR_ECARTE = "PHYTOSCOPE_INTERPRETEUR_ECARTE"


def run(settings=None, verifier_repertoires: bool = True) -> PreflightReport:
    """Exécute tous les contrôles et renvoie le rapport."""
    rep = PreflightReport(python_version=platform.python_version())
    rep.python_ok = sys.version_info[:2] >= PYTHON_MINIMUM
    rep.env = inspecter_environnement()
    rep.resultats = [verifier(r) for r in REQUIREMENTS]

    if verifier_repertoires and settings is not None:
        from ..config import config_dir
        for chemin, role in ((config_dir(), "répertoire de configuration"),
                             (settings.recording.directory, "répertoire des séances")):
            ok = True
            try:
                os.makedirs(chemin, exist_ok=True)
                ok = os.access(chemin, os.W_OK)
            except OSError as exc:
                ok = False
                rep.avertissements.append(f"{role} inaccessible : {exc}")
            rep.repertoires.append((chemin, role, ok))

    if rep.env.homebrew_linux and (rep.casses or not rep.peut_demarrer):
        rep.avertissements.append(
            "Cet interpréteur vient de Homebrew : il embarque sa propre glibc "
            "et ne sait pas charger les bibliothèques du système.")

    #  Ce que le lanceur a fait de l'interpréteur, dit ici plutôt qu'écrit sur
    #  la sortie d'erreur à chaque lancement.
    trace = os.environ.get(INTERPRETEUR_ECARTE, "")
    if trace:
        origine, ecarte, retenu = (trace.split("|") + ["", "", ""])[:3]
        if retenu.startswith("échec"):
            rep.avertissements.append(
                f"Interpréteur {origine} écarté ({ecarte}) mais la relance a "
                f"échoué — {retenu}")
        elif retenu:
            rep.avertissements.append(
                f"Interpréteur {origine} écarté ({ecarte}) : il ne voit pas "
                f"les bibliothèques du système. PhytoScope s'est relancé avec "
                f"{retenu}.")
        else:
            rep.avertissements.append(
                f"Interpréteur {origine} ({ecarte}) : aucun interpréteur de "
                f"rechange n'a été trouvé. Préparez l'environnement du "
                f"projet — « make install-dev ».")
        log.info("Interpréteur : %s", trace)

    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY") \
            and not os.environ.get("WAYLAND_DISPLAY"):
        rep.avertissements.append(
            "Aucun serveur graphique détecté : utilisez --headless, ou "
            "définissez DISPLAY.")

    log.info("Contrôles avant vol : %s",
             "tout est en place" if rep.peut_demarrer else "des éléments manquent")
    return rep


def resoudre_en_console(rep: PreflightReport, interactif: bool = True) -> bool:
    """Affiche le rapport et propose d'installer ce qui manque.

    Renvoie True si le logiciel peut démarrer après cette étape.
    """
    print()
    print(rep.to_console())
    print()

    cmd_sys = rep.commande_systeme()
    if cmd_sys:
        print(C.encadre("Bibliothèques système manquantes", [
            "Des paquets Python sont installés mais ne peuvent pas être chargés :",
            "il leur manque une bibliothèque du système.",
            "",
            "  " + C.info(cmd_sys),
            "",
            "Cette étape demande les droits d'administration : le logiciel ne",
            "peut pas la faire à votre place.",
        ]))
        print()

    paquets = rep.paquets_a_installer(tous=True)
    if paquets:
        options = strategies(rep.env)
        print(C.encadre("Paquets Python manquants", [
            "  " + C.alerte(" ".join(paquets)),
            "",
            f"Environnement : {rep.env.resume()}",
        ] + ([f"Méthode proposée : {options[0].nom} — {options[0].description}"]
             if options else ["Aucune méthode d'installation disponible."])))
        print()
        if options and interactif and C.demander_oui_non(
                "Installer ces paquets maintenant ?", True):
            if installer(paquets, options[0], rep.env):
                print(C.succes("\n  Installation terminée.\n"))
                nouveau = run()
                return nouveau.peut_demarrer
            print(C.erreur("\n  L'installation a échoué. "
                           "Essayez : make install\n"))
        elif options:
            print(C.discret("  Installation refusée. Commande équivalente :"))
            print("    " + " ".join(options[0].commande(paquets)))
            print()

    return rep.peut_demarrer
