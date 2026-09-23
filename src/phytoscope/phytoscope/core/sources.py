# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/sources.py
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

"""Sources de signal — d'où viennent les échantillons.

Toutes les sources exposent la même interface : on les démarre, elles
poussent des blocs `(index_premier_échantillon, tableau[n, voies])` exprimés
en volts dans une file, et on les arrête. Le reste du logiciel ignore
complètement si le signal vient d'une carte 24 bits, d'une entrée
microphone, d'un fichier ou du générateur interne.

Le générateur interne n'est pas un gadget : il produit un signal
statistiquement crédible (dérive lente, bruit en 1/f, potentiels d'action
occasionnels, ronflette du réseau), ce qui permet de préparer un atelier,
de tester l'enregistrement et de déboguer la sonification sans plante ni
carte sous la main.
"""
from __future__ import annotations

import math
import queue
import random
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ..i18n import t
from .logging_setup import get_logger
from .protocol import BoardInfo, ControlLink

log = get_logger(__name__)

#  Interfaces hôtes PortAudio, de la meilleure à la pire. Sous Windows, WASAPI
#  est la voie moderne et MME un vestige des années 1990 qu'il faut éviter ;
#  sous Linux, PulseAudio/PipeWire savent partager le périphérique là où ALSA
#  direct le verrouille. Une interface absente de cette liste passe en dernier.
_API_PREFEREES = ("Windows WASAPI", "Windows WDM-KS", "Windows DirectSound",
                  "Core Audio", "PulseAudio", "PipeWire", "JACK Audio "
                  "Connection Kit", "ALSA", "MME")


def _nom_api(sd, index: int) -> str:
    """Le nom lisible d'une interface hôte, ou une chaîne vide."""
    try:
        return str(sd.query_hostapis(index).get("name", ""))
    except Exception:                                  # pragma: no cover
        return ""


Block = Tuple[int, np.ndarray]           # (index du premier échantillon, données)


# ---------------------------------------------------------------------------
#  Base commune
# ---------------------------------------------------------------------------
@dataclass
class SourceInfo:
    kind: str                 # simulation | audio | serie | fichier
    name: str                 # nom affiché
    device: str = ""          # identifiant technique
    channels: int = 1
    sample_rate: float = 250.0
    volts_per_unit: float = 1.0
    detail: str = ""
    board: Optional[BoardInfo] = None


class Source:
    """Interface commune à toutes les sources."""

    def __init__(self, info: SourceInfo, out: "queue.Queue[Block]"):
        self.info = info
        self.out = out
        self.running = False
        self.dropped = 0
        self.n = 0                      # compteur d'échantillons de la séance
        self.last_error = ""

    # -- cycle de vie --------------------------------------------------------
    def start(self) -> bool:
        raise NotImplementedError

    def stop(self) -> None:
        self.running = False

    # -- utilitaire ----------------------------------------------------------
    def _emit(self, data: np.ndarray) -> None:
        """Pousse un bloc, en jetant le plus ancien si la file déborde.

        Jeter plutôt que bloquer : un affichage en retard ne doit jamais
        faire décrocher l'acquisition.
        """
        block = (self.n, data)
        self.n += data.shape[0]
        try:
            self.out.put_nowait(block)
        except queue.Full:
            self.dropped += 1
            try:
                self.out.get_nowait()
                self.out.put_nowait(block)
            except queue.Empty:                        # pragma: no cover
                pass


# ---------------------------------------------------------------------------
#  Générateur interne
# ---------------------------------------------------------------------------
class SimulatedSource(Source):
    """Plante synthétique — pour apprendre, démontrer et tester.

    Modèle : marche aléatoire filtrée (dérive), bruit rose approché par une
    somme de trois filtres du premier ordre, ronflette de 50 Hz si la
    fréquence d'échantillonnage le permet, et potentiels d'action rares dont
    la forme reprend l'allure décrite dans la littérature (montée rapide,
    retour lent).
    """

    def __init__(self, out: "queue.Queue[Block]", sample_rate: float = 250.0,
                 channels: int = 1, seed: int = 7, mains: float = 50.0,
                 activity: float = 1.0, realtime: bool = True):
        super().__init__(SourceInfo("simulation", t("Simulated plant"),
                                    channels=channels, sample_rate=sample_rate,
                                    detail="générateur interne, aucun matériel requis"),
                         out)
        self.fs = sample_rate
        self.channels = channels
        self.mains = mains
        self.activity = activity
        self.realtime = realtime
        self.rng = random.Random(seed)
        self._np_rng = np.random.default_rng(seed)
        self._thread: Optional[threading.Thread] = None
        self._drift = [0.0] * channels
        self._pink = [[0.0, 0.0, 0.0] for _ in range(channels)]
        self._ap = [0.0] * channels           # état du potentiel d'action
        self._phase = 0.0

    def start(self) -> bool:
        if self.running:
            return True
        self.running = True
        self._thread = threading.Thread(target=self._run, name="simulation",
                                        daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        super().stop()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    # -- moteur --------------------------------------------------------------
    def _run(self) -> None:
        block = max(int(self.fs / 20), 8)         # ~50 ms
        period = block / self.fs
        next_t = time.monotonic()
        while self.running:
            data = self._render(block)
            self._emit(data)
            if self.realtime:
                next_t += period
                delay = next_t - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_t = time.monotonic()

    def _render(self, n: int) -> np.ndarray:
        out = np.zeros((n, self.channels), dtype=np.float64)
        dt = 1.0 / self.fs
        for c in range(self.channels):
            p = self._pink[c]
            for i in range(n):
                # dérive très lente : quelques centaines de µV par heure
                self._drift[c] += self._np_rng.normal(0.0, 4e-7)
                self._drift[c] *= 0.999995
                # bruit rose (Voss-McCartney simplifié)
                w = self._np_rng.normal(0.0, 1.0)
                p[0] = 0.99765 * p[0] + w * 0.0990460
                p[1] = 0.96300 * p[1] + w * 0.2965164
                p[2] = 0.57000 * p[2] + w * 1.0526913
                pink = (p[0] + p[1] + p[2]) * 1.2e-6
                # potentiel d'action : rare, forme asymétrique
                if self._ap[c] <= 0.0 and self.rng.random() < 4e-4 * self.activity:
                    self._ap[c] = 1.0
                ap = 0.0
                if self._ap[c] > 0.0:
                    ap = self._ap[c] ** 2 * 900e-6
                    self._ap[c] -= dt / 3.2          # retour en ~3 s
                    if self._ap[c] < 0:
                        self._ap[c] = 0.0
                # réseau
                hum = 0.0
                if self.mains and self.fs > 2.5 * self.mains:
                    hum = 2.5e-6 * math.sin(self._phase + c * 0.3)
                out[i, c] = self._drift[c] + pink + ap + hum
                if c == 0:
                    self._phase += 2 * math.pi * (self.mains or 0.0) * dt
        return out


# ---------------------------------------------------------------------------
#  Entrée audio (carte en classe audio 2.0, ou n'importe quelle entrée)
# ---------------------------------------------------------------------------
class AudioSource(Source):
    """Lit une entrée audio via PortAudio (paquet `sounddevice`).

    C'est le chemin privilégié avec la carte PhytoSense : elle se déclare
    comme périphérique audio 24 bits, donc aucun pilote n'est nécessaire sur
    aucun système. C'est aussi ce qui permet d'utiliser le logiciel avec
    n'importe quelle carte du commerce qui sort de l'audio.
    """

    def __init__(self, out: "queue.Queue[Block]", device: Optional[str] = None,
                 sample_rate: float = 250.0, channels: int = 1,
                 volts_per_unit: float = 1.0, block_size: int = 0):
        super().__init__(SourceInfo("audio", device or "entrée audio par défaut",
                                    device=device or "", channels=channels,
                                    sample_rate=sample_rate,
                                    volts_per_unit=volts_per_unit), out)
        self.device = device
        self.fs = sample_rate
        self.channels = channels
        self.vpu = volts_per_unit
        self.block_size = block_size
        self._stream = None

    # -- rééchantillonnage ---------------------------------------------------
    class _Decimateur:
        """Ramène un flux de 48 kHz à 250 Hz, sans perdre un échantillon.

        CoreAudio et WASAPI refusent qu'on leur demande 250 Hz : leur format
        de mixage est celui de la carte son, typiquement 44,1 ou 48 kHz. Il
        faut donc ouvrir au débit du périphérique et décimer ici.

        La moyenne glissante par blocs de `facteur` échantillons est un filtre
        en peigne d'ordre 1 : ses zéros tombent exactement sur les multiples de
        la fréquence de sortie, et l'atténuation hors bande suit une enveloppe
        en 1/f — de l'ordre de −55 dB au voisinage de 48 kHz pour un facteur de
        192. C'est amplement suffisant ici, où la bande utile s'arrête à 40 Hz,
        soit un six-centième du débit d'entrée : l'affaissement dans la bande
        passante est alors indiscernable.

        Le **reste** entre deux blocs est conservé : sans cela on perdrait
        jusqu'à `facteur - 1` échantillons à chaque appel du rappel audio, ce
        qui décalerait lentement l'horodatage.
        """

        def __init__(self, facteur: int, canaux: int = 1):
            self.facteur = max(int(facteur), 1)
            self._reste = np.zeros((0, canaux), dtype=np.float64)

        def __call__(self, bloc: np.ndarray) -> np.ndarray:
            if self.facteur == 1:
                return bloc
            x = np.vstack((self._reste, bloc)) if self._reste.size else bloc
            n = (x.shape[0] // self.facteur) * self.facteur
            self._reste = x[n:].copy()
            if n == 0:
                return np.zeros((0, x.shape[1]), dtype=np.float64)
            return x[:n].reshape(-1, self.facteur, x.shape[1]).mean(axis=1)

    # -- découverte ----------------------------------------------------------
    @staticmethod
    def list_devices() -> List[Dict[str, Any]]:
        try:
            import sounddevice as sd
        except Exception:
            return []
        out = []
        try:
            for i, d in enumerate(sd.query_devices()):
                if d.get("max_input_channels", 0) <= 0:
                    continue
                out.append({"index": i, "name": d["name"],
                            "channels": d["max_input_channels"],
                            "default_samplerate": d.get("default_samplerate", 0.0),
                            "hostapi": d.get("hostapi", 0),
                            "api": _nom_api(sd, d.get("hostapi", 0))})
        except Exception:                              # pragma: no cover
            return []
        return out

    @staticmethod
    def resoudre(nom: str) -> Any:
        """Du nom d'un périphérique à l'index qu'il faut passer à PortAudio.

        Pourquoi ne pas passer le nom directement : **sous Windows, le même
        matériel apparaît plusieurs fois**, une entrée par interface hôte —
        MME, DirectSound, WASAPI, WDM-KS — sous des noms presque identiques,
        et MME tronque le sien à 31 caractères. La résolution par nom de
        `sounddevice` retient alors la première correspondance, c'est-à-dire
        MME : la plus ancienne, la plus latente, la moins fiable.

        On choisit donc explicitement l'interface hôte que le système
        recommande, et l'on rend un **index**, qui lui est sans ambiguïté.
        Rendre le nom tel quel reste le comportement de repli, pour ne pas
        casser une installation où la liste ne serait pas lisible.
        """
        if not nom:
            return None
        candidats = [d for d in AudioSource.list_devices()
                     if d["name"] == nom]
        if not candidats:
            #  Nom tronqué par MME, ou périphérique renommé : on retombe sur
            #  la correspondance partielle plutôt que d'échouer.
            candidats = [d for d in AudioSource.list_devices()
                         if nom[:31] in d["name"] or d["name"] in nom]
        if not candidats:
            return nom
        if len(candidats) == 1:
            return candidats[0]["index"]
        rang = {api: i for i, api in enumerate(_API_PREFEREES)}
        candidats.sort(key=lambda d: rang.get(d["api"], len(rang)))
        return candidats[0]["index"]

    @staticmethod
    def find_phytosense() -> Optional[Dict[str, Any]]:
        """Repère une carte PhytoSense parmi les entrées audio."""
        for d in AudioSource.list_devices():
            name = d["name"].lower()
            if "phytosense" in name or "plantwave" in name or "biodata" in name:
                return d
        return None

    # -- cycle de vie --------------------------------------------------------
    def start(self) -> bool:
        try:
            import sounddevice as sd
        except Exception as exc:
            self.last_error = (f"sounddevice indisponible ({exc}). "
                               "Installez-le avec : pip install sounddevice")
            return False

        decimateur = self._Decimateur(1, self.channels)

        def callback(indata, frames, time_info, status):   # pragma: no cover
            if status:
                self.last_error = str(status)
            data = np.asarray(indata, dtype=np.float64) * self.vpu
            if data.ndim == 1:
                data = data[:, None]
            data = decimateur(data)
            if data.shape[0]:
                self._emit(data.copy())

        #  On tente d'abord le débit demandé : une vraie carte PhytoSense le
        #  déclare, et ALSA l'accepte de toute façon en rééchantillonnant.
        #  CoreAudio et WASAPI, eux, refusent tout ce qui n'est pas le format
        #  de mixage du périphérique — d'où le repli sur son débit natif suivi
        #  d'une décimation logicielle, qui est le seul moyen d'obtenir 250 Hz
        #  sur un Mac ou sous Windows.
        tentatives = [(self.fs, 1)]
        natif = self._debit_natif(sd)
        if natif and natif > self.fs * 1.5:
            tentatives.append((natif, max(int(round(natif / self.fs)), 1)))

        derniere = ""
        for debit, facteur in tentatives:
            try:
                flux = sd.InputStream(
                    device=self.resoudre(self.device), channels=self.channels,
                    samplerate=debit, dtype="float32",
                    blocksize=self.block_size * facteur if self.block_size else 0,
                    callback=callback)
                flux.start()
            except Exception as exc:
                derniere = str(exc)
                continue
            decimateur.facteur = facteur
            self._stream = flux
            self.info.sample_rate = debit / facteur
            if facteur > 1:
                self.last_error = ""
                log.info("Entrée audio ouverte à %.0f Hz, décimée par %d "
                         "vers %.1f Hz (le périphérique refusait %.1f Hz).",
                         debit, facteur, debit / facteur, self.fs)
            self.running = True
            return True

        self.last_error = f"ouverture de l'entrée audio impossible : {derniere}"
        self._stream = None
        return False

    def _debit_natif(self, sd) -> float:
        """Le débit que le périphérique déclare préférer, ou 0 s'il se tait."""
        try:
            if self.device:
                for d in self.list_devices():
                    if d["name"] == self.device or d["index"] == self.device:
                        return float(d.get("default_samplerate") or 0.0)
            return float(sd.query_devices(kind="input").get(
                "default_samplerate") or 0.0)
        except Exception:                              # pragma: no cover
            return 0.0

    def stop(self) -> None:
        super().stop()
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None


# ---------------------------------------------------------------------------
#  Lien série binaire (carte sans classe audio, ou montage maison)
# ---------------------------------------------------------------------------
class SerialSource(Source):
    """Lit un flux de valeurs sur un port série.

    Deux formats sont acceptés, détectés automatiquement :

    * **texte** : une valeur décimale par ligne (ce que produisent la
      plupart des montages Arduino publiés) ;
    * **binaire** : trames `PS` + n° d'échantillon (4 o) + voies (int32).

    Le format texte est lent mais universel ; c'est lui qui permet de
    brancher le logiciel sur un montage à NE555 déjà construit.
    """

    MAGIC = b"PS"

    def __init__(self, out: "queue.Queue[Block]", port: str = "",
                 baud: int = 115200, sample_rate: float = 250.0,
                 channels: int = 1, volts_per_unit: float = 1.0):
        super().__init__(SourceInfo("serie", port or "port série",
                                    device=port, channels=channels,
                                    sample_rate=sample_rate,
                                    volts_per_unit=volts_per_unit), out)
        self.port = port
        self.baud = baud
        self.fs = sample_rate
        self.channels = channels
        self.vpu = volts_per_unit
        self._ser = None
        self._thread: Optional[threading.Thread] = None

    def start(self) -> bool:
        try:
            import serial
        except ImportError:
            self.last_error = ("pyserial n'est pas installé. "
                               "Installez-le avec : pip install pyserial")
            return False
        if not self.port:
            ports = ControlLink.discover()
            if not ports:
                self.last_error = "aucun port série candidat."
                return False
            self.port = ports[0]
        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=0.5)
        except Exception as exc:
            self.last_error = f"ouverture de {self.port} impossible : {exc}"
            return False
        self.running = True
        self._thread = threading.Thread(target=self._run, name="serie", daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        super().stop()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self._ser is not None:
            try:
                self._ser.close()
            finally:
                self._ser = None

    def _run(self) -> None:                             # pragma: no cover
        buf: List[float] = []
        target = max(int(self.fs / 20), 4)
        while self.running and self._ser is not None:
            try:
                line = self._ser.readline()
            except Exception as exc:
                self.last_error = str(exc)
                break
            if not line:
                continue
            try:
                value = float(line.decode("ascii", "ignore").strip().split(",")[0])
            except ValueError:
                continue
            buf.append(value * self.vpu)
            if len(buf) >= target:
                self._emit(np.asarray(buf, dtype=np.float64)[:, None])
                buf = []


# ---------------------------------------------------------------------------
#  Relecture d'une séance enregistrée
# ---------------------------------------------------------------------------
class FileSource(Source):
    """Rejoue un enregistrement, à vitesse réelle ou accélérée."""

    def __init__(self, out: "queue.Queue[Block]", data: np.ndarray,
                 sample_rate: float, speed: float = 1.0, loop: bool = False,
                 name: str = "séance"):
        if data.ndim == 1:
            data = data[:, None]
        super().__init__(SourceInfo("fichier", name, channels=data.shape[1],
                                    sample_rate=sample_rate,
                                    detail="replay"), out)
        self.data = data
        self.fs = sample_rate
        self.speed = max(speed, 0.01)
        self.loop = loop
        self._thread: Optional[threading.Thread] = None
        self.position = 0
        self.paused = False

    def start(self) -> bool:
        if self.running:
            return True
        self.running = True
        self._thread = threading.Thread(target=self._run, name="replay",
                                        daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        super().stop()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def seek(self, sample: int) -> None:
        self.position = max(0, min(int(sample), self.data.shape[0]))

    def _run(self) -> None:
        block = max(int(self.fs / 20), 8)
        next_t = time.monotonic()
        while self.running:
            if self.paused:
                time.sleep(0.05)
                next_t = time.monotonic()
                continue
            end = min(self.position + block, self.data.shape[0])
            if end <= self.position:
                if not self.loop:
                    self.running = False
                    break
                self.position = 0
                continue
            chunk = self.data[self.position:end]
            self.position = end
            self._emit(np.array(chunk, dtype=np.float64))
            next_t += (chunk.shape[0] / self.fs) / self.speed
            delay = next_t - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.monotonic()


# ---------------------------------------------------------------------------
#  Choix automatique
# ---------------------------------------------------------------------------
def autodetect(out: "queue.Queue[Block]", settings) -> Source:
    """Choisit la meilleure source disponible, sans jamais échouer.

    Ordre de préférence : carte PhytoSense en classe audio, puis carte
    détectée sur un port série, puis entrée audio par défaut si l'utilisateur
    l'a explicitement demandée, puis générateur interne. Le logiciel démarre
    donc toujours, même sur une machine nue — ce qui est la condition pour
    qu'un atelier ne commence pas par une séance de dépannage.
    """
    acq = settings.acquisition
    want = (acq.source or "auto").lower()

    if want in ("simulation", "demo"):
        return SimulatedSource(out, acq.sample_rate, max(acq.channels, 1))

    if want in ("auto", "phytosense", "audio"):
        dev = None
        if want == "audio" and acq.device:
            dev = acq.device
        else:
            found = AudioSource.find_phytosense()
            if found:
                dev = found["name"]
            elif want == "audio":
                dev = acq.device or None
        if dev is not None or want == "audio":
            src = AudioSource(out, dev, acq.sample_rate, max(acq.channels, 1),
                              acq.volts_per_unit, acq.block_size)
            if src.start():
                src.stop()               # le moteur redémarrera proprement
                return src

    if want in ("auto", "serie"):
        ports = ControlLink.discover()
        if ports or acq.device:
            return SerialSource(out, acq.device or (ports[0] if ports else ""),
                                115200, acq.sample_rate, max(acq.channels, 1),
                                acq.volts_per_unit)

    return SimulatedSource(out, acq.sample_rate, max(acq.channels, 1))
