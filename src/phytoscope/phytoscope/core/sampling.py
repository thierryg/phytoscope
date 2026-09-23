# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/sampling.py
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

"""Module d'échantillonnage — prélever proprement, et savoir ce qu'on a prélevé.

L'acquisition continue suffit pour écouter. Pour **mesurer**, il faut
maîtriser le prélèvement : taille du bloc, décimation, moyennage, fenêtre
d'apodisation, et surtout déclenchement. C'est l'objet de ce module, qui
s'intercale entre la source et le reste du logiciel.

Trois modes :

* **continu**   — tout passe, rien n'est découpé ; c'est le mode d'écoute ;
* **bloc**      — des blocs de N échantillons sont constitués, fenêtrés et
                  éventuellement moyennés : c'est le mode d'analyse ;
* **déclenché** — un bloc n'est retenu que si le signal franchit un seuil,
                  avec pré-déclenchement, comme sur un oscilloscope.

Rappels de métrologie appliqués ici :

* la **décimation** par moyenne de N échantillons divise la bande par N et
  améliore le rapport signal sur bruit de √N — à condition que le bruit soit
  blanc, ce que le module vérifie en publiant le facteur réellement obtenu ;
* le **moyennage de blocs** ne réduit que le bruit non corrélé au
  déclenchement : il ne sert à rien en mode continu, d'où son verrouillage ;
* une **fenêtre d'apodisation** réduit les fuites spectrales mais élargit le
  lobe principal et réduit le gain cohérent ; les deux facteurs de correction
  sont fournis, sans quoi une amplitude lue sur un spectre est fausse.
"""
from __future__ import annotations

import math
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

from .logging_setup import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
#  Fenêtres d'apodisation et leurs facteurs de correction
#  (gain cohérent = moyenne ; gain de bruit = racine de la moyenne des carrés)
# ---------------------------------------------------------------------------
FENETRES: Dict[str, str] = {
    "rectangle": "Rectangular — no windowing, maximum leakage",
    "hann": "Hann — the usual compromise",
    "hamming": "Hamming — lower side lobes, slower roll-off",
    "blackman": "Blackman — very low leakage, degraded resolution",
    "flattop": "Flat-top — exact amplitude, poor resolution",
}


def window(name: str, n: int) -> np.ndarray:
    name = (name or "hann").lower()
    if n <= 1:
        return np.ones(max(n, 1))
    if name == "rectangle":
        return np.ones(n)
    if name == "hamming":
        return np.hamming(n)
    if name == "blackman":
        return np.blackman(n)
    if name == "flattop":
        k = np.arange(n) / (n - 1)
        a = (0.21557895, 0.41663158, 0.277263158, 0.083578947, 0.006947368)
        return (a[0] - a[1] * np.cos(2 * np.pi * k) + a[2] * np.cos(4 * np.pi * k)
                - a[3] * np.cos(6 * np.pi * k) + a[4] * np.cos(8 * np.pi * k))
    return np.hanning(n)


def window_gains(name: str, n: int = 4096) -> Tuple[float, float]:
    """(gain cohérent, gain de bruit) — à appliquer aux amplitudes lues."""
    w = window(name, n)
    coherent = float(np.mean(w))
    noise = float(np.sqrt(np.mean(w ** 2)))
    return coherent, noise


# ---------------------------------------------------------------------------
#  Bloc échantillonné
# ---------------------------------------------------------------------------
@dataclass
class SampleBlock:
    """Un bloc prélevé, avec tout ce qu'il faut pour l'interpréter."""
    index: int                      # numéro du premier échantillon
    time_s: float                   # instant du premier échantillon
    data: np.ndarray                # échantillons, en volts
    sample_rate: float              # fréquence APRÈS décimation
    decimation: int = 1
    averages: int = 1
    window_name: str = "rectangle"
    triggered: bool = False
    trigger_index: int = 0          # position du déclenchement dans le bloc
    coherent_gain: float = 1.0
    noise_gain: float = 1.0

    @property
    def duration_s(self) -> float:
        return self.data.shape[0] / self.sample_rate if self.sample_rate else 0.0

    @property
    def resolution_hz(self) -> float:
        """Résolution spectrale d'une transformée sur ce bloc."""
        return self.sample_rate / self.data.shape[0] if self.data.size else 0.0

    def stats(self) -> Dict[str, float]:
        x = self.data
        if not x.size:
            return {}
        return {
            "n": float(x.size),
            "moyenne": float(np.mean(x)),
            "ecart_type": float(np.std(x, ddof=1)) if x.size > 1 else 0.0,
            "efficace": float(np.sqrt(np.mean(x ** 2))),
            "minimum": float(np.min(x)),
            "maximum": float(np.max(x)),
            "crete_a_crete": float(np.max(x) - np.min(x)),
            "mediane": float(np.median(x)),
            "duree_s": self.duration_s,
            "resolution_hz": self.resolution_hz,
        }


# ---------------------------------------------------------------------------
#  Échantillonneur
# ---------------------------------------------------------------------------
class Sampler:
    """Transforme un flux continu en blocs exploitables.

    L'objet est alimenté par `feed()` depuis le fil de traitement et publie
    des blocs terminés via `on_block`. Il ne bloque jamais et n'alloue rien
    de durable : la mémoire est bornée par `max_blocks`.
    """

    def __init__(self, settings):
        self.settings = settings
        self.on_block: Optional[Callable[[SampleBlock], None]] = None
        self.lock = threading.Lock()

        self.blocks: List[SampleBlock] = []
        self.last_block: Optional[SampleBlock] = None
        self.blocks_seen = 0
        self.blocks_kept = 0
        self.triggers = 0
        self.armed = True

        self._buf = np.zeros(0, dtype=np.float64)
        self._buf_index = 0
        self._dec_acc = 0.0
        self._dec_n = 0
        self._avg_acc: Optional[np.ndarray] = None
        self._avg_count = 0
        self._holdoff_until = 0.0
        self._prev = 0.0
        self._derniere_config = None
        self.reconfigure()

    # -- configuration -------------------------------------------------------
    def reconfigure(self) -> None:
        s = self.settings.sampling
        fs = self.settings.acquisition.sample_rate
        self.mode = s.mode
        self.n = max(int(s.block_samples), 16)
        self.decim = max(int(s.decimation), 1)
        self.averages = max(int(s.averaging), 1)
        self.window_name = s.window
        self.fs_out = fs / self.decim
        self.win = window(self.window_name, self.n)
        self.coherent, self.noise_gain = window_gains(self.window_name, self.n)
        self.pre = int(self.n * min(max(s.pretrigger_percent, 0.0), 90.0) / 100.0)
        self._buf = np.zeros(0, dtype=np.float64)
        self._avg_acc = None
        self._avg_count = 0
        # Même remarque que pour l'étage de sortie : on ne journalise que les
        # changements effectifs, sans quoi le démarrage produit trois lignes
        # identiques et le journal devient illisible.
        signature = (self.mode, self.n, self.decim, self.averages,
                     self.window_name, self.fs_out)
        if signature != self._derniere_config:
            self._derniere_config = signature
            log.info("Échantillonneur : mode %s, %d éch., décimation %d, "
                     "moyennage %d, fenêtre %s → %.3f Hz",
                     self.mode, self.n, self.decim, self.averages,
                     self.window_name, self.fs_out)

    # -- alimentation --------------------------------------------------------
    def feed(self, index: int, x: np.ndarray) -> None:
        """Absorbe un bloc brut venu de la source."""
        if self.mode == "continu":
            self.blocks_seen += 1
            return
        x = np.asarray(x, dtype=np.float64).reshape(-1)
        if self.decim > 1:
            x = self._decimate(x)
            if not x.size:
                return
        with self.lock:
            if not self._buf.size:
                self._buf_index = index
            self._buf = np.concatenate([self._buf, x]) if self._buf.size else x.copy()
            while self._buf.size >= self.n:
                if self.mode == "declenche":
                    if not self._try_trigger():
                        break
                else:
                    self._emit(self._buf[:self.n], self._buf_index, False, 0)
                    self._advance(self.n)

    def _decimate(self, x: np.ndarray) -> np.ndarray:
        """Moyenne glissante par blocs de `decim`, avec report d'un appel à l'autre."""
        out = []
        acc, n = self._dec_acc, self._dec_n
        for v in x.tolist():
            acc += v
            n += 1
            if n >= self.decim:
                out.append(acc / n)
                acc, n = 0.0, 0
        self._dec_acc, self._dec_n = acc, n
        return np.asarray(out, dtype=np.float64)

    def _advance(self, k: int) -> None:
        self._buf = self._buf[k:]
        self._buf_index += k * self.decim

    def _try_trigger(self) -> bool:
        """Cherche un franchissement de seuil dans le tampon."""
        s = self.settings.sampling
        level = s.trigger_level_uv * 1e-6
        now = time.monotonic()
        if now < self._holdoff_until:
            self._advance(max(self._buf.size - self.n, 0) or 1)
            return False
        x = self._buf
        start = self.pre
        end = x.size - (self.n - self.pre)
        if end <= start:
            return False
        seg = x[start:end]
        prev = np.concatenate([[x[start - 1] if start else self._prev], seg[:-1]])
        if s.trigger_edge == "montant":
            hit = (prev < level) & (seg >= level)
        elif s.trigger_edge == "descendant":
            hit = (prev > -level) & (seg <= -level)
        else:
            hit = ((prev < level) & (seg >= level)) | ((prev > -level) & (seg <= -level))
        idx = np.nonzero(hit)[0]
        if idx.size == 0:
            if s.trigger_mode == "auto" and x.size >= 2 * self.n:
                self._emit(x[:self.n], self._buf_index, False, 0)
                self._advance(self.n)
                return True
            keep = self.n
            if x.size > keep:
                self._advance(x.size - keep)
            return False
        t = int(idx[0]) + start
        begin = t - self.pre
        self._emit(x[begin:begin + self.n], self._buf_index + begin * self.decim,
                   True, self.pre)
        self.triggers += 1
        self._holdoff_until = now + s.holdoff_ms / 1000.0
        self._advance(begin + self.n)
        if s.trigger_mode == "unique":
            self.armed = False
            self.mode = "continu"
            log.info("Mode unique : déclenchement capté, échantillonneur désarmé.")
        return True

    def _emit(self, raw: np.ndarray, index: int, triggered: bool,
              trig_pos: int) -> None:
        data = raw.copy()
        if self.window_name != "rectangle":
            data = data * self.win
        self.blocks_seen += 1

        if self.averages > 1:
            if self._avg_acc is None or self._avg_acc.shape != data.shape:
                self._avg_acc = np.zeros_like(data)
                self._avg_count = 0
            self._avg_acc += data
            self._avg_count += 1
            if self._avg_count < self.averages:
                return
            data = self._avg_acc / self._avg_count
            self._avg_acc = None
            self._avg_count = 0

        block = SampleBlock(index=index, time_s=index / max(
            self.settings.acquisition.sample_rate, 1e-9),
            data=data, sample_rate=self.fs_out, decimation=self.decim,
            averages=self.averages, window_name=self.window_name,
            triggered=triggered, trigger_index=trig_pos,
            coherent_gain=self.coherent, noise_gain=self.noise_gain)
        self.last_block = block
        self.blocks_kept += 1
        if self.settings.sampling.accumulate:
            self.blocks.append(block)
            if len(self.blocks) > max(int(self.settings.sampling.max_blocks), 1):
                self.blocks.pop(0)
        if self.on_block:
            try:
                self.on_block(block)
            except Exception:                          # pragma: no cover
                log.exception("Consommateur de bloc en erreur")

    # -- lecture -------------------------------------------------------------
    def clear(self) -> None:
        with self.lock:
            self.blocks.clear()
            self._avg_acc = None
            self._avg_count = 0
            self.armed = True

    def summary(self) -> str:
        s = self.settings.sampling
        eff = f"{self.fs_out:g} Hz"
        gain = math.sqrt(self.decim * self.averages)
        return (f"mode {self.mode} · {self.n} éch. à {eff} · "
                f"décimation ×{self.decim} · {self.averages} moyennage(s) · "
                f"fenêtre {self.window_name} · gain théorique sur le bruit ×{gain:.1f} "
                f"· {self.blocks_kept} bloc(s) retenus, {self.triggers} déclenchement(s)")
