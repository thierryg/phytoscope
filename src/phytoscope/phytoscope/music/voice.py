# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/voice.py
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

"""Sortie parlée — dire les énoncés à voix haute.

Prononcer du texte est l'une des rares choses pour lesquelles il n'existe aucune
solution portable en Python pur. Chaque système a la sienne, et aucune n'est
garantie présente. Ce module applique donc le motif *Strategy* : plusieurs
stratégies sont essayées dans l'ordre, la première qui répond est retenue, et si
aucune ne répond le logiciel continue sans rien dire — l'énoncé reste visible
dans le journal et dans le fichier de séance.

============  ==================================  ============================
Stratégie     Comment                             Disponibilité
============  ==================================  ============================
pyttsx3       bibliothèque Python, hors ligne     les trois systèmes, si
                                                  installée (facultative)
espeak-ng     programme externe                   Linux, parfois macOS
say           programme du système                macOS uniquement
SAPI          PowerShell, voix du système         Windows uniquement
silencieuse   ne dit rien                         toujours
============  ==================================  ============================

Toutes parlent **hors ligne** : aucun texte ne quitte la machine. C'est une
exigence, pas une préférence — on enregistre des séances chez des gens, et rien
de ce qui s'y dit n'a à partir sur un service distant.

La parole est émise dans un fil séparé, avec une file d'attente bornée. Si la
plante « parle » plus vite que la voix ne prononce, les énoncés en trop sont
abandonnés plutôt qu'accumulés : mieux vaut perdre une phrase que prendre trois
minutes de retard sur la mesure.
"""
from __future__ import annotations

import os
import platform
import queue
import shutil
import subprocess
import sys
import threading
from abc import ABC, abstractmethod
from typing import List, Optional

from ..core.logging_setup import get_logger
from ..i18n import t

log = get_logger(__name__)

__all__ = ["VoiceOutput", "strategies_disponibles"]


# ---------------------------------------------------------------------------
#  Les stratégies
# ---------------------------------------------------------------------------
class _Strategie(ABC):
    nom = "?"
    description = ""

    @classmethod
    @abstractmethod
    def disponible(cls) -> bool: ...

    @abstractmethod
    def dire(self, texte: str, debit: int, volume: float, voix: str) -> None: ...

    def voix_disponibles(self) -> List[str]:
        return []

    def voix_utilisable(self, voix: str) -> str:
        """Ne garder l'identifiant de voix que s'il est de ce moteur.

        Un `reglages.json` voyage : celui d'un utilisateur de Windows contient
        un identifiant SAPI de la forme
        ``HKEY_LOCAL_MACHINE\\…\\TTS_MS_FR-FR_HORTENSE_11.0``. Passé tel
        quel à `espeak -v`, il produit un échec journalisé à chaque énoncé, et
        le mode Parole paraît cassé sans qu'on sache pourquoi. Chaque moteur
        vérifie donc que l'identifiant est bien le sien, et retombe sur sa
        voix par défaut sinon.
        """
        if not voix:
            return ""
        connues = self.voix_disponibles()
        return voix if (not connues or voix in connues) else ""

    def fermer(self) -> None:
        pass


class _Pyttsx3(_Strategie):
    nom = "pyttsx3"
    description = "bibliothèque Python hors ligne, les trois systèmes"

    def __init__(self):
        #  Le moteur n'est PAS créé ici, et c'est délibéré. Sous Windows,
        #  pyttsx3 s'appuie sur SAPI5, c'est-à-dire sur COM, dont les objets
        #  ont une **affinité d'appartement** : créés dans un fil, ils ne
        #  s'utilisent pas depuis un autre. Or cette classe est construite
        #  dans le fil appelant tandis que `dire()` tourne dans le fil
        #  « phytoscope-voix ». On diffère donc la création jusqu'au premier
        #  énoncé, qui a lieu dans le bon fil, et l'on refait le moteur si le
        #  fil change.
        self._moteur = None
        self._fil = None

    @classmethod
    def disponible(cls) -> bool:
        try:
            import pyttsx3                               # noqa: F401,PLC0415
        except Exception:                                # noqa: BLE001
            return False
        return True

    def _obtenir(self):
        """Le moteur du fil courant, créé à la demande."""
        actuel = threading.get_ident()
        if self._moteur is not None and self._fil == actuel:
            return self._moteur
        if self._moteur is not None:
            #  Changement de fil : l'ancien objet COM n'est plus utilisable.
            try:
                self._moteur.stop()
            except Exception:                            # noqa: BLE001
                pass
        if sys.platform.startswith("win"):
            #  Chaque fil qui parle à COM doit d'abord entrer dans un
            #  appartement. pythoncom arrive avec pywin32, que pyttsx3 tire
            #  sous Windows ; son absence n'est pas fatale.
            try:
                import pythoncom                         # noqa: PLC0415
                pythoncom.CoInitialize()
            except Exception:                            # noqa: BLE001
                pass
        import pyttsx3                                   # noqa: PLC0415
        self._moteur = pyttsx3.init()
        self._fil = actuel
        return self._moteur

    def dire(self, texte: str, debit: int, volume: float, voix: str) -> None:
        moteur = self._obtenir()
        moteur.setProperty("rate", int(debit))
        moteur.setProperty("volume", float(max(0.0, min(volume, 1.0))))
        if voix:
            moteur.setProperty("voice", voix)
        moteur.say(texte)
        moteur.runAndWait()

    def voix_disponibles(self) -> List[str]:
        try:
            return [v.id for v in self._obtenir().getProperty("voices")]
        except Exception:                                # noqa: BLE001
            return []

    def fermer(self) -> None:
        try:
            if self._moteur is not None:
                self._moteur.stop()
        except Exception:                                # noqa: BLE001
            pass


class _Espeak(_Strategie):
    nom = "espeak-ng"
    description = "synthétiseur libre, à installer par le gestionnaire de paquets"

    @classmethod
    def _binaire(cls) -> Optional[str]:
        return shutil.which("espeak-ng") or shutil.which("espeak")

    @classmethod
    def disponible(cls) -> bool:
        return cls._binaire() is not None

    def dire(self, texte: str, debit: int, volume: float, voix: str) -> None:
        cmd = [self._binaire() or "espeak-ng",
               "-s", str(int(debit)),
               "-a", str(int(max(0.0, min(volume, 1.0)) * 200)),
               "-v", self.voix_utilisable(voix) or "fr",
               texte]
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=30)

    def voix_disponibles(self) -> List[str]:
        return ["fr", "fr-be", "fr-ch", "en", "en-gb", "es", "de", "it"]


class _Say(_Strategie):
    nom = "say"
    description = "synthèse intégrée à macOS"

    @classmethod
    def disponible(cls) -> bool:
        return platform.system() == "Darwin" and shutil.which("say") is not None

    def dire(self, texte: str, debit: int, volume: float, voix: str) -> None:
        cmd = ["say", "-r", str(int(debit))]
        retenue = self.voix_utilisable(voix)
        if retenue:
            cmd += ["-v", retenue]
        cmd.append(texte)
        subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=30)

    def voix_disponibles(self) -> List[str]:
        try:
            sortie = subprocess.run(["say", "-v", "?"], capture_output=True,
                                    text=True, timeout=10, check=False).stdout
            return [l.split()[0] for l in sortie.splitlines() if l.strip()]
        except Exception:                                # noqa: BLE001
            return []


class _Sapi(_Strategie):
    nom = "SAPI"
    description = "voix du système Windows, par PowerShell"

    @classmethod
    def disponible(cls) -> bool:
        return platform.system() == "Windows"

    def dire(self, texte: str, debit: int, volume: float, voix: str) -> None:
        # Le débit SAPI va de −10 à +10 ; on transpose depuis les mots/minute.
        taux = int(max(-10, min((int(debit) - 175) / 17, 10)))
        propre = texte.replace("'", "''")
        script = ("Add-Type -AssemblyName System.Speech; "
                  "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                  f"$s.Rate = {taux}; "
                  f"$s.Volume = {int(max(0.0, min(volume, 1.0)) * 100)}; "
                  f"$s.Speak('{propre}')")
        subprocess.run(["powershell", "-NoProfile", "-Command", script],
                       check=False, stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, timeout=30)


class _Silencieuse(_Strategie):
    nom = "silencieuse"
    description = "aucune synthèse : le texte reste écrit"

    @classmethod
    def disponible(cls) -> bool:
        return True

    def dire(self, texte: str, debit: int, volume: float, voix: str) -> None:
        pass


#  Ordre de préférence : la plus intégrée d'abord, la plus universelle ensuite.
_ORDRE = (_Pyttsx3, _Say, _Sapi, _Espeak, _Silencieuse)


def strategies_disponibles() -> List[tuple]:
    """Ce qui est utilisable sur cette machine — pour l'onglet de diagnostic."""
    out = []
    for cls in _ORDRE:
        try:
            ok = cls.disponible()
        except Exception:                                # noqa: BLE001
            ok = False
        out.append((cls.nom, cls.description, ok))
    return out


# ---------------------------------------------------------------------------
#  La sortie parlée
# ---------------------------------------------------------------------------
class VoiceOutput:
    """File d'attente bornée et fil de prononciation."""

    def __init__(self, settings, profondeur: int = 4):
        self.settings = settings
        self._file: "queue.Queue[Optional[str]]" = queue.Queue(maxsize=profondeur)
        self._fil: Optional[threading.Thread] = None
        self._actif = False
        self._strategie: Optional[_Strategie] = None
        self.abandons = 0
        self.prononces = 0

    # -- cycle de vie -------------------------------------------------------
    def demarrer(self) -> bool:
        """Choisit une stratégie et lance le fil. Retourne False si muet."""
        if self._actif:
            return self._strategie is not None and self._strategie.nom != "silencieuse"

        voulue = getattr(getattr(self.settings, "voice", None), "backend", "auto")
        candidats = _ORDRE
        if voulue and voulue != "auto":
            nommes = [c for c in _ORDRE if c.nom == voulue]
            candidats = nommes + [c for c in _ORDRE if c not in nommes]

        for cls in candidats:
            try:
                if not cls.disponible():
                    continue
                self._strategie = cls()
            except Exception as exc:                     # noqa: BLE001
                log.warning("Synthèse vocale « %s » indisponible : %s", cls.nom, exc)
                continue
            break

        if self._strategie is None:
            self._strategie = _Silencieuse()

        if self._strategie.nom == "silencieuse":
            log.warning("Aucune synthèse vocale trouvée. Les énoncés seront "
                        "écrits mais non prononcés. Sous Linux : "
                        "« sudo apt install espeak-ng » ou « pip install pyttsx3 ».")
        else:
            log.info("Synthèse vocale : %s", self._strategie.nom)

        self._actif = True
        self._fil = threading.Thread(target=self._boucle, name="phytoscope-voix",
                                     daemon=True)
        self._fil.start()
        return self._strategie.nom != "silencieuse"

    def arreter(self) -> None:
        if not self._actif:
            return
        self._actif = False
        try:
            self._file.put_nowait(None)
        except queue.Full:
            pass
        if self._fil is not None:
            self._fil.join(timeout=2.0)
        if self._strategie is not None:
            self._strategie.fermer()
        self._fil = None

    # -- émission -----------------------------------------------------------
    def dire(self, texte: str) -> bool:
        """Met un énoncé dans la file. False s'il a été abandonné."""
        if not (self._actif and texte):
            return False
        try:
            self._file.put_nowait(texte)
            return True
        except queue.Full:
            self.abandons += 1
            log.debug("Énoncé abandonné (file pleine) : %s", texte)
            return False

    def vider(self) -> None:
        """Abandonne ce qui attend — au changement de réglage, ou à l'arrêt."""
        while True:
            try:
                self._file.get_nowait()
            except queue.Empty:
                return

    # -- interne ------------------------------------------------------------
    def _boucle(self) -> None:
        while self._actif:
            try:
                texte = self._file.get(timeout=0.4)
            except queue.Empty:
                continue
            if texte is None:
                return
            v = getattr(self.settings, "voice", None)
            if v is None or not v.enabled or getattr(v, "muted", False):
                continue
            try:
                assert self._strategie is not None
                self._strategie.dire(
                    texte, int(v.rate_wpm), float(v.volume),
                    self._strategie.voix_utilisable(str(v.voice_id)))
                self.prononces += 1
            except Exception as exc:                     # noqa: BLE001
                log.error("Échec de la prononciation : %s", exc)

    # -- état ---------------------------------------------------------------
    @property
    def actif(self) -> bool:
        """Vrai dès que le fil tourne — même si la stratégie est silencieuse."""
        return self._actif

    @property
    def backend(self) -> str:
        return self._strategie.nom if self._strategie else "—"

    def voix_disponibles(self) -> List[str]:
        return self._strategie.voix_disponibles() if self._strategie else []

    def etat(self) -> str:
        if not self._actif:
            return t("stopped")
        if self.backend == "silencieuse":
            return t("no synthesis installed")
        return t("{moteur} · {dits} spoken, {perdus} dropped").format(
            moteur=self.backend, dits=self.prononces, perdus=self.abandons)
