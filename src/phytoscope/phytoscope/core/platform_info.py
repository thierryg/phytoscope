# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/platform_info.py
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

"""Identification du système — et commandes exactes pour chaque famille.

Le logiciel vise trois mondes, et sept façons d'installer un paquet :

* **Windows 10 et 11** — rien à installer : les roues Python embarquent Qt,
  PortAudio et RtMidi. Le seul écueil connu est l'absence du redistribuable
  Visual C++ sur les machines très anciennes.
* **macOS (Darwin)**, Intel et Apple Silicon — Homebrew pour PortAudio ;
  Qt vient avec la roue PySide6. Une autorisation microphone est demandée
  au premier accès à l'entrée audio.
* **GNU/Linux** — Debian, Ubuntu, Mint et dérivés (apt) ; Fedora, RHEL,
  CentOS, Rocky, AlmaLinux (dnf ou yum) ; Arch et Manjaro (pacman) ;
  openSUSE (zypper) ; Alpine (apk).

La détection lit `/etc/os-release` (norme freedesktop), et retombe sur la
présence des exécutables si le fichier est absent.
"""
from __future__ import annotations

import os
import platform
import shutil
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

# ---------------------------------------------------------------------------
#  Familles de distributions
# ---------------------------------------------------------------------------
FAMILLES: Dict[str, Dict[str, str]] = {
    "debian": {"gestionnaire": "apt", "installer": "sudo apt install -y",
               "rafraichir": "sudo apt update",
               "libelle": "Debian, Ubuntu, Mint, Pop!_OS, Raspberry Pi OS"},
    "fedora": {"gestionnaire": "dnf", "installer": "sudo dnf install -y",
               "rafraichir": "sudo dnf check-update",
               "libelle": "Fedora, RHEL, CentOS Stream, Rocky, AlmaLinux"},
    "arch":   {"gestionnaire": "pacman", "installer": "sudo pacman -S --noconfirm",
               "rafraichir": "sudo pacman -Sy",
               "libelle": "Arch, Manjaro, EndeavourOS"},
    "suse":   {"gestionnaire": "zypper", "installer": "sudo zypper install -y",
               "rafraichir": "sudo zypper refresh", "libelle": "openSUSE, SLE"},
    "alpine": {"gestionnaire": "apk", "installer": "sudo apk add",
               "rafraichir": "sudo apk update", "libelle": "Alpine"},
    "macos":  {"gestionnaire": "brew", "installer": "brew install",
               "rafraichir": "brew update", "libelle": "macOS avec Homebrew"},
    "windows": {"gestionnaire": "", "installer": "", "rafraichir": "",
                "libelle": "Windows 10 et 11"},
}

#  Identifiants ID_LIKE de /etc/os-release → famille
ALIAS = {
    "debian": "debian", "ubuntu": "debian", "linuxmint": "debian",
    "pop": "debian", "elementary": "debian", "raspbian": "debian",
    "kali": "debian", "devuan": "debian", "zorin": "debian",
    "fedora": "fedora", "rhel": "fedora", "centos": "fedora",
    "rocky": "fedora", "almalinux": "fedora", "ol": "fedora",
    "arch": "arch", "manjaro": "arch", "endeavouros": "arch", "garuda": "arch",
    "opensuse": "suse", "opensuse-leap": "suse", "opensuse-tumbleweed": "suse",
    "sles": "suse", "suse": "suse",
    "alpine": "alpine",
}

#  Paquets système, par rôle et par famille
PAQUETS: Dict[str, Dict[str, List[str]]] = {
    "qt": {
        "debian": ["libgl1", "libegl1", "libxkbcommon-x11-0", "libxcb-cursor0",
                   "libxcb-icccm4", "libxcb-keysyms1", "libxcb-render-util0",
                   "libxcb-shape0", "libxcb-xinerama0", "libdbus-1-3",
                   "libfontconfig1"],
        "fedora": ["mesa-libGL", "mesa-libEGL", "libxkbcommon-x11",
                   "xcb-util-cursor", "xcb-util-wm", "xcb-util-keysyms",
                   "xcb-util-renderutil", "dbus-libs", "fontconfig"],
        "arch": ["libglvnd", "libxkbcommon-x11", "xcb-util-cursor",
                 "xcb-util-wm", "xcb-util-keysyms", "xcb-util-renderutil",
                 "dbus", "fontconfig"],
        "suse": ["Mesa-libGL1", "Mesa-libEGL1", "libxkbcommon-x11-0",
                 "xcb-util-cursor0", "libdbus-1-3", "fontconfig"],
        "alpine": ["mesa-gl", "mesa-egl", "libxkbcommon-x11", "xcb-util-cursor",
                   "dbus-libs", "fontconfig"],
        "macos": [], "windows": [],
    },
    "audio": {
        "debian": ["libportaudio2", "libasound2"],
        "fedora": ["portaudio", "alsa-lib"],
        "arch": ["portaudio", "alsa-lib"],
        "suse": ["portaudio", "alsa"],
        "alpine": ["portaudio", "alsa-lib"],
        "macos": ["portaudio"], "windows": [],
    },
    "midi": {
        "debian": ["librtmidi-dev"], "fedora": ["rtmidi"],
        "arch": ["rtmidi"], "suse": ["rtmidi-devel"], "alpine": ["rtmidi-dev"],
        "macos": [], "windows": [],
    },
    #  Chaîne de fabrication des PDF (`build.py`, `build_board.py`). Elle ne
    #  concerne pas l'utilisateur du logiciel : seulement qui reconstruit
    #  l'ouvrage. WeasyPrint embarque son moteur de rendu depuis la version 53
    #  mais reste lié à Pango, HarfBuzz et fontconfig, qu'aucune roue Python
    #  ne fournit — d'où cette entrée, sans laquelle l'échec à la première
    #  construction est illisible.
    "documents": {
        "debian": ["libpango-1.0-0", "libpangoft2-1.0-0", "libharfbuzz0b",
                   "libfontconfig1", "libffi-dev"],
        "fedora": ["pango", "harfbuzz", "fontconfig", "libffi-devel"],
        "arch": ["pango", "harfbuzz", "fontconfig", "libffi"],
        "suse": ["pango", "harfbuzz", "fontconfig", "libffi-devel"],
        "alpine": ["pango", "harfbuzz", "fontconfig", "libffi-dev"],
        #  Sur Apple Silicon, Homebrew installe dans /opt/homebrew : il faut
        #  en outre DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib pour que
        #  WeasyPrint trouve Pango.
        "macos": ["pango", "libffi"],
        #  Sous Windows, ces bibliothèques viennent du runtime GTK3, qui
        #  s'installe séparément — voir README.md.
        "windows": [],
    },
    "python": {
        "debian": ["python3", "python3-venv", "python3-pip"],
        "fedora": ["python3", "python3-pip"],
        "arch": ["python", "python-pip"],
        "suse": ["python3", "python3-pip"],
        "alpine": ["python3", "py3-pip"],
        "macos": ["python"], "windows": [],
    },
}


@dataclass
class SystemInfo:
    """Description du système hôte, telle qu'elle sert à installer."""
    systeme: str = ""           # Linux | Darwin | Windows
    famille: str = ""           # debian | fedora | arch | suse | alpine | macos | windows
    distribution: str = ""      # nom affiché
    version: str = ""
    architecture: str = ""
    gestionnaire: str = ""
    installer_cmd: str = ""
    wayland: bool = False
    headless: bool = False
    notes: List[str] = field(default_factory=list)

    def libelle(self) -> str:
        base = self.distribution or self.systeme
        return f"{base} {self.version}".strip() + f" ({self.architecture})"

    def commande(self, *roles: str) -> str:
        """Commande d'installation pour un ou plusieurs rôles."""
        paquets: List[str] = []
        for role in roles:
            paquets += PAQUETS.get(role, {}).get(self.famille, [])
        paquets = sorted(dict.fromkeys(paquets))
        if not paquets:
            return ""
        if not self.installer_cmd:
            return f"(aucun paquet système requis pour : {', '.join(roles)})"
        return f"{self.installer_cmd} {' '.join(paquets)}"

    def instructions(self) -> List[str]:
        """Marche à suivre complète, adaptée au système détecté."""
        if self.famille == "windows":
            return [
                "Installez Python depuis python.org en cochant "
                "« Add python.exe to PATH ».",
                "Puis, dans l'invite de commandes :  make.bat install",
                "Aucune bibliothèque système supplémentaire n'est nécessaire.",
            ]
        if self.famille == "macos":
            return [
                "Installez Homebrew si besoin : "
                "/bin/bash -c \"$(curl -fsSL "
                "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"",
                self.commande("audio"),
                "Puis :  make install",
                "macOS demandera l'autorisation d'accès au microphone au "
                "premier démarrage de l'acquisition : elle est indispensable.",
            ]
        lignes = []
        if self.famille in FAMILLES:
            lignes.append(FAMILLES[self.famille]["rafraichir"])
        cmd = self.commande("python", "qt", "audio", "midi")
        if cmd:
            lignes.append(cmd)
        lignes.append("Puis :  make install")
        if self.wayland:
            lignes.append("Session Wayland détectée : Qt bascule automatiquement "
                          "sur le greffon adéquat ; en cas de souci, forcez "
                          "QT_QPA_PLATFORM=xcb.")
        return [x for x in lignes if x]


def _lire_os_release() -> Dict[str, str]:
    for chemin in ("/etc/os-release", "/usr/lib/os-release"):
        if not os.path.exists(chemin):
            continue
        data: Dict[str, str] = {}
        try:
            with open(chemin, encoding="utf-8") as f:
                for ligne in f:
                    if "=" not in ligne:
                        continue
                    cle, _, valeur = ligne.partition("=")
                    data[cle.strip()] = valeur.strip().strip('"').strip("'")
            return data
        except OSError:
            continue
    return {}


def detect() -> SystemInfo:
    """Identifie le système, sa famille et son gestionnaire de paquets."""
    info = SystemInfo(systeme=platform.system(),
                      architecture=platform.machine(),
                      version=platform.release())

    if sys.platform.startswith("win"):
        info.famille = "windows"
        info.distribution = f"Windows {platform.win32_ver()[0]}"
        info.version = platform.win32_ver()[0]
    elif sys.platform == "darwin":
        info.famille = "macos"
        info.distribution = "macOS"
        info.version = platform.mac_ver()[0]
        if not shutil.which("brew"):
            info.notes.append("Homebrew n'est pas installé : les bibliothèques "
                              "système ne pourront pas être installées "
                              "automatiquement.")
    else:
        osr = _lire_os_release()
        ident = (osr.get("ID") or "").lower()
        like = (osr.get("ID_LIKE") or "").lower().split()
        info.distribution = osr.get("PRETTY_NAME") or osr.get("NAME") or "GNU/Linux"
        info.version = osr.get("VERSION_ID", "") or platform.release()
        info.famille = ALIAS.get(ident, "")
        if not info.famille:
            for cle in like:
                if cle in ALIAS:
                    info.famille = ALIAS[cle]
                    break
        if not info.famille:            # repli : on regarde les exécutables
            for outil, famille in (("apt-get", "debian"), ("dnf", "fedora"),
                                   ("yum", "fedora"), ("pacman", "arch"),
                                   ("zypper", "suse"), ("apk", "alpine")):
                if shutil.which(outil):
                    info.famille = famille
                    break
        info.wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        info.headless = not (os.environ.get("DISPLAY") or info.wayland)
        if info.headless:
            info.notes.append("Aucun serveur graphique : seul le mode "
                              "--headless fonctionnera.")

    famille = FAMILLES.get(info.famille, {})
    info.gestionnaire = famille.get("gestionnaire", "")
    info.installer_cmd = famille.get("installer", "")
    # yum reste courant sur les RHEL anciens
    if info.gestionnaire == "dnf" and not shutil.which("dnf") and shutil.which("yum"):
        info.gestionnaire = "yum"
        info.installer_cmd = "sudo yum install -y"
    return info


def resume() -> str:
    """Rapport système lisible — utilisé par `make system-deps` et le diagnostic."""
    info = detect()
    lignes = [
        f"Système        : {info.libelle()}",
        f"Famille        : {info.famille or 'indéterminée'}"
        + (f" — {FAMILLES[info.famille]['libelle']}" if info.famille in FAMILLES else ""),
        f"Gestionnaire   : {info.gestionnaire or 'aucun'}",
        f"Python         : {platform.python_version()} ({sys.executable})",
    ]
    if info.notes:
        lignes += [""] + ["Note : " + n for n in info.notes]
    lignes += ["", "Paquets système recommandés :", ""]
    for role, titre in (("python", "Python et environnements virtuels"),
                        ("qt", "Interface graphique Qt 6"),
                        ("audio", "Entrée et sortie audio"),
                        ("midi", "Sortie MIDI")):
        cmd = info.commande(role)
        lignes.append(f"  {titre} :")
        lignes.append(f"    {cmd or 'rien à installer'}")
    lignes += ["", "Marche à suivre :", ""]
    lignes += ["  " + i for i in info.instructions()]
    return "\n".join(lignes)


if __name__ == "__main__":                             # pragma: no cover
    print(resume())
