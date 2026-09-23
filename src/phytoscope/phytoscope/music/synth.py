# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/synth.py
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

"""Synthétiseur interne — polyphonique, additif, sans dépendance.

Le rendu se fait en NumPy par blocs, dans le fil audio de PortAudio. Rien
n'est alloué dans la boucle : les voix sont préallouées et recyclées, ce qui
évite les micro-coupures dues au ramasse-miettes.

Le but n'est pas de rivaliser avec un synthétiseur professionnel — pour cela
il y a la sortie MIDI — mais de garantir qu'un utilisateur entende quelque
chose de beau **sans rien installer d'autre**.
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from ..core.logging_setup import get_logger
from .instruments import Instrument, get as get_instrument
from .scales import DIAPASON_DEFAUT, midi_to_hz

log = get_logger(__name__)

ATTACK, DECAY, SUSTAIN, RELEASE, DEAD = range(5)


@dataclass
class Voice:
    """Une note en cours de jeu."""
    active: bool = False
    midi: int = 60
    freq: float = 261.63
    gain: float = 0.0
    phase: float = 0.0
    stage: int = DEAD
    env: float = 0.0
    t_stage: float = 0.0
    duration: float = 1.0
    elapsed: float = 0.0
    instrument: Optional[Instrument] = None
    phases: Optional[np.ndarray] = None


def _ligne_a_retard(buf: np.ndarray, pos: int, x: np.ndarray,
                    traitement) -> Tuple[np.ndarray, int]:
    """Applique un traitement à une ligne à retard, par tranches vectorisées.

    Le point clé pour la performance : tant que la tranche traitée ne
    dépasse pas la longueur du retard, lecture et écriture ne se recouvrent
    pas — la récurrence disparaît et tout se fait par opérations de tableau.
    Une boucle Python par échantillon coûterait ici cent fois plus cher, et
    provoquerait les coupures audio que l'on cherche précisément à éviter.
    """
    n = buf.shape[0]
    reste = x.shape[0]
    sortie = np.empty_like(x)
    debut = 0
    while reste > 0:
        k = min(reste, n - pos, n)
        vue = buf[pos:pos + k]
        entree = x[debut:debut + k]
        y, nouveau = traitement(vue, entree)
        sortie[debut:debut + k] = y
        buf[pos:pos + k] = nouveau
        pos = (pos + k) % n
        debut += k
        reste -= k
    return sortie, pos


class Reverb:
    """Réverbération de Schroeder — quatre peignes et deux passe-tout.

    Volontairement modeste : juste assez pour que les notes ne sonnent pas
    « collées au haut-parleur », sans noyer la lisibilité des événements.
    Entièrement vectorisée : le coût par bloc est indépendant du contenu.
    """

    RETARDS_PEIGNE = (0.0297, 0.0371, 0.0411, 0.0437)
    REACTIONS = (0.805, 0.827, 0.783, 0.764)
    RETARDS_PASSE_TOUT = (0.0050, 0.0017)
    GAIN_PASSE_TOUT = 0.5

    def __init__(self, fs: float):
        self.fs = fs
        self.comb_buf = [np.zeros(max(int(fs * d), 1)) for d in self.RETARDS_PEIGNE]
        self.comb_pos = [0] * len(self.RETARDS_PEIGNE)
        self.ap_buf = [np.zeros(max(int(fs * d), 1)) for d in self.RETARDS_PASSE_TOUT]
        self.ap_pos = [0] * len(self.RETARDS_PASSE_TOUT)

    def reset(self) -> None:
        for b in self.comb_buf + self.ap_buf:
            b.fill(0.0)

    def process(self, x: np.ndarray, amount: float) -> np.ndarray:
        if amount <= 0.001 or x.size == 0:
            return x
        humide = np.zeros_like(x)
        for i, fb in enumerate(self.REACTIONS):
            def peigne(vue, entree, fb=fb):
                return vue.copy(), entree + vue * fb
            y, self.comb_pos[i] = _ligne_a_retard(
                self.comb_buf[i], self.comb_pos[i], x, peigne)
            humide += y
        humide *= 0.25
        g = self.GAIN_PASSE_TOUT
        for i in range(len(self.ap_buf)):
            def passe_tout(vue, entree, g=g):
                interne = entree + vue * g
                return vue - interne * g, interne
            humide, self.ap_pos[i] = _ligne_a_retard(
                self.ap_buf[i], self.ap_pos[i], humide, passe_tout)
        return x * (1.0 - amount) + humide * amount


class Synth:
    """Synthétiseur polyphonique, thread-safe côté déclenchement."""

    def __init__(self, sample_rate: int = 44100, polyphony: int = 24,
                 diapason_hz: float = DIAPASON_DEFAUT):
        self.fs = sample_rate
        self.diapason = diapason_hz
        self.voices = [Voice() for _ in range(polyphony)]
        self.reverb = Reverb(sample_rate)
        self.reverb_amount = 0.35
        self.master = 0.5
        self.lock = threading.Lock()
        self.drone_voice: Optional[Voice] = None
        self._peak = 0.0
        self.polyphonie_max = polyphony

    # -- déclenchement -------------------------------------------------------
    def note_on(self, midi: int, velocity: int = 100, duration: float = 1.0,
                instrument: str = "kalimba") -> None:
        inst = get_instrument(instrument)
        midi = int(min(max(midi + inst.octave_shift * 12, 0), 127))
        with self.lock:
            v = self._free_voice()
            v.active = True
            v.midi = midi
            v.freq = midi_to_hz(midi, self.diapason)
            v.gain = (velocity / 127.0) ** 1.6
            v.stage = ATTACK
            v.env = 0.0
            v.t_stage = 0.0
            v.elapsed = 0.0
            v.duration = max(duration, 0.05)
            v.instrument = inst
            v.phases = np.zeros(len(inst.partials), dtype=np.float64)

    def all_off(self) -> None:
        with self.lock:
            for v in self.voices:
                if v.active and v.stage != RELEASE:
                    v.stage = RELEASE
                    v.t_stage = 0.0

    def set_drone(self, midi: Optional[int], instrument: str = "bourdon") -> None:
        """Bourdon continu : la tonique tenue sous la séance."""
        with self.lock:
            if self.drone_voice is not None:
                self.drone_voice.stage = RELEASE
                self.drone_voice.t_stage = 0.0
                self.drone_voice = None
        if midi is None:
            return
        self.note_on(midi, velocity=42, duration=1e9, instrument=instrument)
        with self.lock:
            for v in self.voices:
                if v.active and v.midi == midi + get_instrument(instrument).octave_shift * 12:
                    self.drone_voice = v
                    break

    def _free_voice(self) -> Voice:
        """Voix libre, ou la plus éteinte si la polyphonie est saturée.

        La polyphonie utile est plafonnée par `polyphonie_max` : c'est
        l'équivalent du sélecteur « 3 voix / monodique » des appareils du
        commerce. Le bourdon ne compte pas dans ce plafond.
        """
        actives = [v for v in self.voices
                   if v.active and v is not self.drone_voice]
        if len(actives) >= max(self.polyphonie_max, 1):
            return min(actives, key=lambda v: v.env)
        for v in self.voices:
            if not v.active:
                return v
        return min(self.voices, key=lambda v: v.env)

    # -- rendu ---------------------------------------------------------------
    def render(self, frames: int) -> np.ndarray:
        out = np.zeros(frames, dtype=np.float64)
        dt = 1.0 / self.fs
        t = np.arange(frames, dtype=np.float64) * dt
        with self.lock:
            for v in self.voices:
                if not v.active or v.instrument is None:
                    continue
                inst = v.instrument
                env = self._envelope(v, frames, dt)
                sig = np.zeros(frames, dtype=np.float64)
                for k, (ratio, amp) in enumerate(inst.partials):
                    det = 1.0 + (inst.detune_cents / 1200.0) * (k % 2 * 2 - 1) * 0.5
                    f = v.freq * ratio * det
                    ph = float(v.phases[k])
                    sig += amp * np.sin(2 * math.pi * f * t + ph)
                    v.phases[k] = (ph + 2 * math.pi * f * frames * dt) % (2 * math.pi)
                norm = sum(a for _, a in inst.partials) or 1.0
                out += sig * (env * v.gain / norm)
                v.elapsed += frames * dt
                if v.stage == DEAD:
                    v.active = False
        out = self.reverb.process(out, self.reverb_amount)
        out *= self.master
        self._peak = float(np.max(np.abs(out))) if frames else 0.0
        return out

    def _envelope(self, v: Voice, frames: int, dt: float) -> np.ndarray:
        """Enveloppe ADSR du bloc, calculée segment par segment.

        Chaque étape a une forme analytique : rampe linéaire à l'attaque,
        approche exponentielle à la chute, palier au maintien, rampe à
        l'extinction. On remplit donc des tranches de tableau plutôt que de
        boucler sur les échantillons — c'est ce qui permet de tenir
        vingt-quatre voix sans coupure.
        """
        inst = v.instrument
        env = np.empty(frames, dtype=np.float64)
        i = 0
        e, stage, ts = v.env, v.stage, v.t_stage
        elapsed = v.elapsed

        while i < frames:
            reste = frames - i

            if stage == ATTACK:
                pente = dt / max(inst.attack, 1e-4)
                n = min(reste, max(int(math.ceil((1.0 - e) / pente)), 1))
                env[i:i + n] = np.minimum(e + pente * np.arange(1, n + 1), 1.0)
                e = float(env[i + n - 1])
                if e >= 1.0 - 1e-9:
                    e, stage, ts = 1.0, DECAY, 0.0
                i += n

            elif stage == DECAY:
                cible = inst.sustain
                a = dt / max(inst.decay, 1e-4)
                n_total = max(int(inst.decay / dt), 1)
                n = min(reste, max(n_total - int(ts / dt), 1))
                k = np.arange(1, n + 1)
                env[i:i + n] = cible + (e - cible) * np.power(1.0 - a, k)
                e = float(env[i + n - 1])
                ts += n * dt
                if ts >= inst.decay:
                    e, stage, ts = cible, SUSTAIN, 0.0
                i += n

            elif stage == SUSTAIN:
                restant = v.duration - (elapsed + i * dt)
                n = min(reste, max(int(restant / dt), 1)) if restant > 0 else 1
                env[i:i + n] = e
                ts += n * dt
                if restant <= n * dt:
                    stage, ts = RELEASE, 0.0
                i += n

            elif stage == RELEASE:
                pente = dt / max(inst.release, 1e-4)
                n = min(reste, max(int(math.ceil(e / pente)), 1))
                env[i:i + n] = np.maximum(e - pente * np.arange(1, n + 1), 0.0)
                e = float(env[i + n - 1])
                if e <= 1e-9:
                    e, stage = 0.0, DEAD
                i += n

            else:                                      # DEAD
                env[i:] = 0.0
                break

        v.env, v.stage, v.t_stage = e, stage, ts
        return env

    @property
    def peak(self) -> float:
        return self._peak

    @property
    def active_voices(self) -> int:
        return sum(1 for v in self.voices if v.active)


class RingBuffer:
    """Tampon circulaire mono, écrit par un fil, lu par un autre.

    Sans verrou dans le chemin de lecture : les indices sont des entiers
    Python, dont l'affectation est atomique sous le verrou global. La lecture
    ne fait donc que copier de la mémoire — c'est exactement ce qu'il faut
    dans un rappel audio.
    """

    def __init__(self, taille: int):
        self.buf = np.zeros(int(taille), dtype=np.float32)
        self.n = self.buf.shape[0]
        self.w = 0          # position d'écriture
        self.r = 0          # position de lecture

    @property
    def disponible(self) -> int:
        return (self.w - self.r) % self.n

    @property
    def libre(self) -> int:
        return self.n - 1 - self.disponible

    def ecrire(self, x: np.ndarray) -> int:
        k = min(x.shape[0], self.libre)
        if k <= 0:
            return 0
        fin = self.w + k
        if fin <= self.n:
            self.buf[self.w:fin] = x[:k]
        else:
            coupe = self.n - self.w
            self.buf[self.w:] = x[:coupe]
            self.buf[:fin - self.n] = x[coupe:k]
        self.w = fin % self.n
        return k

    def lire(self, frames: int, sortie: np.ndarray) -> int:
        k = min(frames, self.disponible)
        if k <= 0:
            sortie[:frames] = 0.0
            return 0
        fin = self.r + k
        if fin <= self.n:
            sortie[:k] = self.buf[self.r:fin]
        else:
            coupe = self.n - self.r
            sortie[:coupe] = self.buf[self.r:]
            sortie[coupe:k] = self.buf[:fin - self.n]
        if k < frames:
            sortie[k:frames] = 0.0
        self.r = fin % self.n
        return k


class AudioOutput:
    """Sortie audio temps réel — écriture bloquante, ou rappel.

    Le problème que résout cette classe est propre à Python : le rappel audio
    de PortAudio doit acquérir le verrou global de l'interpréteur pour
    exécuter du code Python. Si l'interface graphique tient ce verrou plus
    longtemps que la durée du tampon — ce qu'un rafraîchissement de courbe
    peut faire —, le rappel ne s'exécute pas à temps et la couche ALSA
    signale « underrun occurred ».

    Deux modes sont donc proposés.

    **Écriture bloquante** (défaut). Aucun rappel : un fil dédié synthétise et
    appelle ``stream.write()``, lequel **libère le verrou pendant qu'il
    bloque**. L'interface peut alors monopoliser le verrou sans empêcher le
    fil audio de progresser, et le tampon du périphérique — dimensionné par
    ``latency`` — absorbe les à-coups. C'est la configuration robuste.

    **Rappel** avec tampon circulaire pré-rempli. Le rappel ne fait que copier
    de la mémoire. Utile là où l'écriture bloquante se comporte mal, et sur
    les plateformes où PortAudio préfère ce mode.

    Dans les deux cas, le bloc rendu est transmis à ``tap`` après l'étage de
    sortie, de sorte que le fichier « musique.wav » contienne exactement ce
    qui a été entendu.
    """

    MODES = ("ecriture", "rappel")

    def __init__(self, synth: Synth, device: Optional[str] = None,
                 block: int = 1024, output_stage=None, latency: str = "high",
                 avance_s: float = 0.5, mode: str = "ecriture"):
        self.synth = synth
        self.device = device
        self.block = block or 1024
        self.latency = latency
        self.output_stage = output_stage
        self.mode = mode if mode in self.MODES else "ecriture"
        self._stream = None
        self.last_error = ""
        self.tap = None          # fonction appelée avec chaque bloc rendu
        self.underruns = 0       # anomalies signalées par PortAudio
        self.famines = 0         # tampon vide au moment de lire
        self.avance_s = avance_s
        self._ring = RingBuffer(int(synth.fs * max(avance_s, 0.1) * 3))
        self._fil = None
        self._fil_rendu = None
        self._actif = False
        self._sortie = np.zeros(8192, dtype=np.float32)

    # -- production d'un bloc ------------------------------------------------
    def _produire(self, frames: int) -> np.ndarray:
        """Synthèse, étage de sortie et dérivation vers l'enregistreur."""
        try:
            buf = self.synth.render(frames)
            if self.output_stage is not None:
                buf = self.output_stage.process(buf)
        except Exception:
            # Un défaut de rendu ne doit jamais interrompre le flux : on
            # produit du silence, on le journalise, et la séance continue.
            log.exception("Rendu audio en erreur — silence émis")
            buf = np.zeros(frames, dtype=np.float64)
        if self.tap is not None:
            try:
                self.tap(buf)
            except Exception:
                log.exception("Consommateur audio en erreur")
        return buf

    # -- mode écriture bloquante --------------------------------------------
    def _boucle_ecriture(self) -> None:                # pragma: no cover
        """Écrit, et rien d'autre.

        Ce fil ne calcule RIEN : il recopie ce que le fil de rendu a préparé
        et appelle ``write()``, qui libère le verrou global pendant qu'il
        bloque. C'est la condition pour que la cadence soit tenue — une seule
        milliseconde de calcul intercalée entre deux écritures suffit à faire
        décrocher le flux au démarrage, avant que le tampon du périphérique
        ne soit rempli, et la couche ALSA ne s'en remet plus.
        """
        pas = max(int(self.block), 256)
        mono = np.zeros(pas, dtype=np.float32)
        stereo = np.zeros((pas, 2), dtype=np.float32)
        while self._actif and self._stream is not None:
            # Attendre que le bloc soit complet plutôt que d'écrire du
            # silence : au démarrage, le périphérique se remplit plus vite
            # que le rendu ne produit, et écrire des trous à ce moment-là
            # provoque une cascade de récupérations dans la couche ALSA.
            # Une famine n'est comptée que si l'attente devient anormale.
            limite = time.monotonic() + 0.020
            while (self._ring.disponible < pas and self._actif
                   and time.monotonic() < limite):
                time.sleep(0.001)
            lus = self._ring.lire(pas, mono)
            if lus < pas:
                self.famines += 1
                log.debug("Famine audio : %d échantillons sur %d", lus, pas)
            stereo[:, 0] = mono
            stereo[:, 1] = mono
            try:
                self._stream.write(stereo)
            except Exception as exc:
                if not self._actif:
                    break
                self.underruns += 1
                self.last_error = str(exc)
                log.debug("Écriture audio : %s", exc)
                time.sleep(0.005)

    # -- mode rappel ---------------------------------------------------------
    def _boucle_rendu(self) -> None:                   # pragma: no cover
        """Maintient le tampon d'avance garni, par blocs réguliers.

        On vise soixante-dix pour cent de la capacité plutôt que le strict
        nécessaire : cette réserve est ce qui absorbe les à-coups du verrou
        global quand l'interface graphique redessine une courbe.
        """
        pas = 1024
        cible = int(self._ring.n * 0.70)
        while self._actif:
            if self._ring.disponible >= cible:
                time.sleep(0.002)
                continue
            self._ring.ecrire(self._produire(pas).astype(np.float32))

    # -- cycle de vie --------------------------------------------------------
    def start(self) -> bool:
        #  Deux ouvertures simultanées, c'est deux fils qui écrivent dans le
        #  même flux PortAudio : la bibliothèque C n'y survit pas. Ce garde-fou
        #  existe parce que la relecture rouvrait la sortie déjà ouverte.
        if self._stream is not None:
            return True
        try:
            import sounddevice as sd
        except Exception as exc:
            self.last_error = (f"sounddevice indisponible ({exc}) — "
                               "le rendu sonore est désactivé.")
            return False

        from ..core.audio_quiet import sans_bavardage

        latence = self.latency
        try:
            latence = float(latence)
        except (TypeError, ValueError):
            pass

        def callback(outdata, frames, time_info, status):   # pragma: no cover
            """Ne fait que copier : aucun calcul, aucune allocation."""
            if status:
                self.underruns += 1
            if frames > self._sortie.shape[0]:
                self._sortie = np.zeros(frames, dtype=np.float32)
            lus = self._ring.lire(frames, self._sortie)
            if lus < frames:
                self.famines += 1
            outdata[:, 0] = self._sortie[:frames]
            if outdata.shape[1] > 1:
                outdata[:, 1] = outdata[:, 0]

        try:
            # L'ouverture du flux fait bavarder ALSA, JACK et PortAudio :
            # on étouffe la sortie d'erreur pendant cette phase, et elle seule.
            with sans_bavardage():
                if self.mode == "ecriture":
                    self._stream = sd.OutputStream(
                        device=self.resoudre(self.device), channels=2,
                        samplerate=self.synth.fs, dtype="float32",
                        blocksize=self.block, latency=latence)
                else:
                    self._stream = sd.OutputStream(
                        device=self.resoudre(self.device), channels=2,
                        samplerate=self.synth.fs, dtype="float32",
                        blocksize=self.block, latency=latence,
                        callback=callback)

                self._actif = True

                # Dans les deux modes, le rendu vit dans son propre fil et
                # remplit un tampon d'avance. On ne démarre le flux qu'une
                # fois ce tampon garni : c'est ce qui évite le décrochage
                # initial dont la couche ALSA ne se remet jamais.
                self._fil_rendu = threading.Thread(target=self._boucle_rendu,
                                                   name="audio-rendu",
                                                   daemon=True)
                self._fil_rendu.start()

                # Amorçage : il faut attendre que le tampon d'avance contienne
                # PLUS que le tampon du périphérique. Sinon, au démarrage,
                # « write » ne bloque pas encore — le périphérique se remplit
                # d'un coup — et le fil d'écriture vide l'avance en quelques
                # itérations, ce qui produit une rafale de trous dont ALSA se
                # plaint bruyamment. C'est la cause de la totalité des
                # décrochages observés : ils avaient tous lieu à la seconde
                # zéro, et aucun ensuite.
                attente = time.monotonic() + 3.0
                cible = int(self._ring.n * 0.65)
                while (self._ring.disponible < cible
                       and time.monotonic() < attente):
                    time.sleep(0.005)
                log.debug("Amorçage audio : %.2f s d'avance constituée",
                          self._ring.disponible / self.synth.fs)

                self._stream.start()
                if self.mode == "ecriture":
                    self._fil = threading.Thread(target=self._boucle_ecriture,
                                                 name="audio-ecriture",
                                                 daemon=True)
                    self._fil.start()
        except Exception as exc:
            self.last_error = f"sortie audio impossible : {exc}"
            self._actif = False
            self._stream = None
            log.error("Ouverture de la sortie audio impossible : %s", exc)
            return False

        log.info("Sortie audio ouverte — mode %s, bloc %d, latence %s",
                 self.mode, self.block, self.latency)
        return True

    def stop(self) -> None:
        self._actif = False
        for attribut in ("_fil", "_fil_rendu"):
            fil = getattr(self, attribut, None)
            if fil is not None:
                fil.join(timeout=1.5)
                setattr(self, attribut, None)
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:                          # pragma: no cover
                pass
            finally:
                self._stream = None

    @property
    def remplissage(self) -> float:
        """Taux de remplissage du tampon — 1,0 = plein, 0 = famine imminente."""
        if self.mode == "ecriture":
            return 1.0
        cible = max(int(self.synth.fs * self.avance_s), 1)
        return min(self._ring.disponible / cible, 1.0)

    @property
    def anomalies(self) -> int:
        """Total des incidents de flux, quel que soit le mode."""
        return self.underruns + self.famines

    @staticmethod
    def list_devices() -> List[str]:
        try:
            import sounddevice as sd
            return [d["name"] for d in sd.query_devices()
                    if d.get("max_output_channels", 0) > 0]
        except Exception:
            return []

    @staticmethod
    def resoudre(nom: str):
        """Nom de périphérique → index, en choisissant la bonne interface hôte.

        Même raison que pour l'entrée (`core.sources.AudioSource.resoudre`) :
        sous Windows le même haut-parleur apparaît sous MME, DirectSound,
        WASAPI et WDM-KS, et le nom seul désigne le plus souvent MME.
        """
        if not nom:
            return None
        try:
            import sounddevice as sd
            from ..core.sources import _API_PREFEREES, _nom_api
        except Exception:                              # pragma: no cover
            return nom
        try:
            sorties = [(i, d) for i, d in enumerate(sd.query_devices())
                       if d.get("max_output_channels", 0) > 0]
        except Exception:                              # pragma: no cover
            return nom
        candidats = [(i, d) for i, d in sorties if d["name"] == nom]
        if not candidats:
            candidats = [(i, d) for i, d in sorties
                         if nom[:31] in d["name"] or d["name"] in nom]
        if not candidats:
            return nom
        rang = {api: k for k, api in enumerate(_API_PREFEREES)}
        candidats.sort(key=lambda p: rang.get(_nom_api(sd, p[1].get("hostapi", 0)),
                                              len(rang)))
        return candidats[0][0]
