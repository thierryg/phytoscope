# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/dsp.py
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

"""Traitement du signal — filtres, statistiques, détection d'événements.

Tout est écrit en NumPy, sans SciPy : les coefficients des biquads sont
calculés à la main (formules du « Audio EQ Cookbook » de Robert Bristow-
Johnson), ce qui évite une dépendance lourde pour cinq filtres.

Convention : les signaux circulent en VOLTS, en float64, et le temps est
compté en numéro d'échantillon depuis le début de la séance.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np


# ---------------------------------------------------------------------------
#  Cellules biquad
# ---------------------------------------------------------------------------
class Biquad:
    """Cellule du second ordre, forme directe II transposée.

    L'état est conservé entre les blocs : le filtrage d'un flux découpé en
    blocs donne exactement le même résultat que le filtrage du flux entier.
    """

    __slots__ = ("b0", "b1", "b2", "a1", "a2", "z1", "z2")

    def __init__(self, b: Tuple[float, float, float], a: Tuple[float, float, float]):
        a0 = a[0]
        self.b0, self.b1, self.b2 = b[0] / a0, b[1] / a0, b[2] / a0
        self.a1, self.a2 = a[1] / a0, a[2] / a0
        self.z1 = self.z2 = 0.0

    def reset(self) -> None:
        self.z1 = self.z2 = 0.0

    def process(self, x: np.ndarray) -> np.ndarray:
        y = np.empty_like(x, dtype=np.float64)
        z1, z2 = self.z1, self.z2
        b0, b1, b2, a1, a2 = self.b0, self.b1, self.b2, self.a1, self.a2
        for i in range(x.shape[0]):
            xi = float(x[i])
            yi = b0 * xi + z1
            z1 = b1 * xi - a1 * yi + z2
            z2 = b2 * xi - a2 * yi
            y[i] = yi
        self.z1, self.z2 = z1, z2
        return y

    # -- gabarits ------------------------------------------------------------
    @classmethod
    def lowpass(cls, fc: float, fs: float, q: float = 0.7071) -> "Biquad":
        w = 2 * math.pi * fc / fs
        c, s = math.cos(w), math.sin(w)
        al = s / (2 * q)
        b = ((1 - c) / 2, 1 - c, (1 - c) / 2)
        a = (1 + al, -2 * c, 1 - al)
        return cls(b, a)

    @classmethod
    def highpass(cls, fc: float, fs: float, q: float = 0.7071) -> "Biquad":
        w = 2 * math.pi * fc / fs
        c, s = math.cos(w), math.sin(w)
        al = s / (2 * q)
        b = ((1 + c) / 2, -(1 + c), (1 + c) / 2)
        a = (1 + al, -2 * c, 1 - al)
        return cls(b, a)

    @classmethod
    def notch(cls, f0: float, fs: float, q: float = 30.0) -> "Biquad":
        w = 2 * math.pi * f0 / fs
        c, s = math.cos(w), math.sin(w)
        al = s / (2 * q)
        b = (1.0, -2 * c, 1.0)
        a = (1 + al, -2 * c, 1 - al)
        return cls(b, a)


class Chain:
    """Suite de cellules appliquées dans l'ordre."""

    def __init__(self, cells: Optional[List[Biquad]] = None):
        self.cells: List[Biquad] = list(cells or [])

    def reset(self) -> None:
        for c in self.cells:
            c.reset()

    def process(self, x: np.ndarray) -> np.ndarray:
        for c in self.cells:
            x = c.process(x)
        return x


def build_chain(fs: float, highpass: float = 0.0, lowpass: float = 0.0,
                notch: float = 0.0, notch_q: float = 30.0) -> Chain:
    """Construit la chaîne décrite par les réglages.

    Le notch est doublé (50 Hz et son premier harmonique) car le résidu de
    150 Hz est souvent plus gênant que le fondamental sur un montage mal
    blindé.
    """
    cells: List[Biquad] = []
    nyq = fs / 2.0
    if highpass and highpass > 0:
        cells.append(Biquad.highpass(max(highpass, 1e-4), fs))
    if notch and 0 < notch < nyq:
        cells.append(Biquad.notch(notch, fs, notch_q))
        if 3 * notch < nyq:
            cells.append(Biquad.notch(3 * notch, fs, notch_q))
    if lowpass and 0 < lowpass < nyq:
        cells.append(Biquad.lowpass(lowpass, fs))
        cells.append(Biquad.lowpass(lowpass, fs))     # 4e ordre, Butterworth
    return Chain(cells)


# ---------------------------------------------------------------------------
#  Ligne de base et statistiques glissantes
# ---------------------------------------------------------------------------
class Baseline:
    """Ligne de base exponentielle : suit la dérive sans la supprimer.

    `tau` est exprimé en secondes. La valeur retournée est le signal moins
    sa ligne de base ; la ligne elle-même reste consultable, car c'est elle
    qui porte l'information circadienne.
    """

    def __init__(self, fs: float, tau_s: float = 120.0):
        self.fs = fs
        self.set_tau(tau_s)
        self.value = 0.0
        self._primed = False

    def set_tau(self, tau_s: float) -> None:
        tau_s = max(tau_s, 1e-3)
        self.alpha = 1.0 - math.exp(-1.0 / (tau_s * self.fs))

    def process(self, x: np.ndarray) -> np.ndarray:
        if not self._primed and x.size:
            self.value = float(x[0])
            self._primed = True
        out = np.empty_like(x, dtype=np.float64)
        v, a = self.value, self.alpha
        for i in range(x.shape[0]):
            v += a * (float(x[i]) - v)
            out[i] = float(x[i]) - v
        self.value = v
        return out


class RunningStats:
    """Moyenne, écart-type et extrêmes sur une fenêtre glissante."""

    def __init__(self, fs: float, window_s: float = 30.0):
        self.n = max(int(fs * window_s), 8)
        self.buf = np.zeros(self.n, dtype=np.float64)
        self.filled = 0
        self.pos = 0

    def push(self, x: np.ndarray) -> None:
        for chunk in (x,):
            k = chunk.shape[0]
            if k >= self.n:
                self.buf[:] = chunk[-self.n:]
                self.pos = 0
                self.filled = self.n
                return
            end = self.pos + k
            if end <= self.n:
                self.buf[self.pos:end] = chunk
            else:
                cut = self.n - self.pos
                self.buf[self.pos:] = chunk[:cut]
                self.buf[:end - self.n] = chunk[cut:]
            self.pos = end % self.n
            self.filled = min(self.filled + k, self.n)

    def view(self) -> np.ndarray:
        if self.filled < self.n:
            return self.buf[:self.filled]
        return self.buf

    @property
    def mean(self) -> float:
        v = self.view()
        return float(v.mean()) if v.size else 0.0

    @property
    def std(self) -> float:
        v = self.view()
        return float(v.std()) if v.size > 1 else 0.0

    @property
    def rms(self) -> float:
        v = self.view()
        return float(np.sqrt(np.mean(v * v))) if v.size else 0.0

    @property
    def peak_to_peak(self) -> float:
        v = self.view()
        return float(v.max() - v.min()) if v.size else 0.0


# ---------------------------------------------------------------------------
#  Détection d'événements
# ---------------------------------------------------------------------------
@dataclass
class Event:
    """Un événement détecté dans le signal."""
    index: int             # numéro d'échantillon du déclenchement
    time_s: float          # temps depuis le début de la séance
    amplitude_v: float     # amplitude signée par rapport à la ligne de base
    slope_v_s: float       # pente instantanée au déclenchement
    sigma: float           # amplitude en écarts-types
    channel: int = 0

    def to_row(self) -> List[str]:
        return [str(self.index), f"{self.time_s:.4f}", f"{self.amplitude_v:.9f}",
                f"{self.slope_v_s:.9f}", f"{self.sigma:.3f}", str(self.channel)]


class EventDetector:
    """Seuil adaptatif sur la dérivée, avec période réfractaire.

    Le seuil n'est pas fixé en volts mais en multiples de l'écart-type
    courant : un montage bruyant déclenche donc autant qu'un montage propre,
    ce qui est exactement ce qu'on veut pour de la musique, et ce qu'il faut
    corriger pour de la mesure (d'où le champ `sigma` conservé).
    """

    def __init__(self, fs: float, sigma: float = 3.5, refractory_ms: float = 400.0,
                 min_amplitude_v: float = 8e-6, window_s: float = 30.0):
        self.fs = fs
        self.k = sigma
        self.refractory = int(fs * refractory_ms / 1000.0)
        self.min_amplitude = min_amplitude_v
        self.stats = RunningStats(fs, window_s)
        self.last_index = -10 ** 9
        self._prev = 0.0

    def process(self, x: np.ndarray, start_index: int, channel: int = 0) -> List[Event]:
        self.stats.push(x)
        sd = self.stats.std
        events: List[Event] = []
        if sd <= 0:
            self._prev = float(x[-1]) if x.size else self._prev
            return events
        thr = max(self.k * sd, self.min_amplitude)
        prev = self._prev
        for i in range(x.shape[0]):
            v = float(x[i])
            n = start_index + i
            if abs(v) >= thr and (n - self.last_index) >= self.refractory:
                self.last_index = n
                events.append(Event(index=n, time_s=n / self.fs, amplitude_v=v,
                                    slope_v_s=(v - prev) * self.fs,
                                    sigma=abs(v) / sd, channel=channel))
            prev = v
        self._prev = prev
        return events


# ---------------------------------------------------------------------------
#  Analyse spectrale
# ---------------------------------------------------------------------------
def welch_psd(x: np.ndarray, fs: float, nperseg: int = 1024,
              overlap: float = 0.5) -> Tuple[np.ndarray, np.ndarray]:
    """Densité spectrale de puissance par la méthode de Welch.

    Renvoie (fréquences, densité en V²/Hz). Fenêtre de Hann, segments
    recouverts, moyenne arithmétique — assez pour lire un plancher de bruit
    et repérer le réseau.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.size < 16:
        return np.zeros(1), np.zeros(1)
    nperseg = int(min(nperseg, x.size))
    step = max(int(nperseg * (1.0 - overlap)), 1)
    win = np.hanning(nperseg)
    scale = 1.0 / (fs * np.sum(win ** 2))
    acc = None
    count = 0
    for start in range(0, x.size - nperseg + 1, step):
        seg = x[start:start + nperseg] * win
        spec = np.abs(np.fft.rfft(seg)) ** 2 * scale
        spec[1:-1] *= 2.0
        acc = spec if acc is None else acc + spec
        count += 1
    if acc is None:
        seg = np.zeros(nperseg)
        seg[:x.size] = x
        acc = np.abs(np.fft.rfft(seg * win)) ** 2 * scale
        count = 1
    freqs = np.fft.rfftfreq(nperseg, 1.0 / fs)
    return freqs, acc / count


def dominant_mains(x: np.ndarray, fs: float) -> Optional[float]:
    """Devine la fréquence du réseau (50 ou 60 Hz) présente dans le signal."""
    if fs < 140 or x.size < int(fs * 4):
        return None
    f, p = welch_psd(x, fs, nperseg=int(min(4096, x.size)))
    best, val = None, 0.0
    for f0 in (50.0, 60.0):
        band = (f > f0 - 1.5) & (f < f0 + 1.5)
        if not band.any():
            continue
        v = float(p[band].max())
        if v > val:
            best, val = f0, v
    if best is None:
        return None
    band = (f > 5) & (f < min(fs / 2 - 5, 100.0))
    ref = p[band]
    floor = float(np.median(ref)) if ref.size else 1e-30
    return best if val > 8 * max(floor, 1e-30) else None


def decimate(x: np.ndarray, factor: int) -> np.ndarray:
    """Décimation avec moyenne de bloc — suffisante pour l'affichage."""
    factor = max(int(factor), 1)
    if factor == 1 or x.size < factor:
        return x
    n = (x.size // factor) * factor
    return x[:n].reshape(-1, factor).mean(axis=1)
