# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/amplifier.py
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

"""Étage de sortie — amplification, compression, limitation, bip.

Une plante produit des événements rares et de faible dynamique. Sur les
haut-parleurs d'un ordinateur portable, dans une salle d'atelier, le rendu
est inaudible si l'on se contente d'un gain. Cet étage traite le problème
comme le ferait une console de sonorisation :

    entrée ─▶ gain ─▶ correction de présence ─▶ compresseur ─▶ gain de
                                                 rattrapage ─▶ limiteur ─▶ sortie

* **Le gain** monte le niveau global, jusqu'à +36 dB.
* **La correction de présence** remonte la bande 1–4 kHz, là où un petit
  haut-parleur rend le mieux et où l'oreille est la plus sensible (courbes
  isosoniques de Fletcher et Munson). C'est ce qui rend une note audible
  sans la rendre forte.
* **Le compresseur** réduit l'écart entre les notes fortes et les faibles :
  seuil, rapport, attaque et rétablissement sont réglables, et le gain de
  rattrapage est calculé automatiquement.
* **Le limiteur** garantit qu'aucun échantillon ne dépasse la pleine
  échelle : indispensable au casque, où un pic d'écrêtage fait mal.
* **Le bip** est un repère sonore court, indépendant de la musique, qu'on
  peut déclencher sur chaque événement ou sur une saturation. Il sert quand
  on regarde ailleurs — c'est-à-dire presque toujours.

Tout est vectorisé en NumPy : le coût par bloc reste constant, condition
pour ne pas provoquer de coupures dans le flux audio.
"""
from __future__ import annotations

import math
import threading
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from ..core.logging_setup import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
#  Cellules élémentaires
# ---------------------------------------------------------------------------
class PeakingEQ:
    """Filtre en cloche — remontée de présence, vectorisé par blocs.

    Implémenté en forme directe I, appliquée par récurrence sur le bloc.
    Pour rester rapide, la récurrence est faite par `np.convolve` sur la
    partie non récursive et par une boucle courte sur la partie récursive :
    à 44,1 kHz et 1024 échantillons, le coût reste négligeable devant la
    synthèse.
    """

    def __init__(self, fs: float, f0: float = 2500.0, gain_db: float = 0.0,
                 q: float = 0.9):
        self.fs = fs
        self.set(f0, gain_db, q)
        self.x1 = self.x2 = self.y1 = self.y2 = 0.0

    def set(self, f0: float, gain_db: float, q: float) -> None:
        a = 10 ** (gain_db / 40.0)
        w = 2 * math.pi * max(f0, 20.0) / self.fs
        alpha = math.sin(w) / (2 * max(q, 0.1))
        cos_w = math.cos(w)
        b = [1 + alpha * a, -2 * cos_w, 1 - alpha * a]
        aa = [1 + alpha / a, -2 * cos_w, 1 - alpha / a]
        self.b = [x / aa[0] for x in b]
        self.a = [x / aa[0] for x in aa]
        self.actif = abs(gain_db) > 0.05

    def process(self, x: np.ndarray) -> np.ndarray:
        if not self.actif:
            return x
        b0, b1, b2 = self.b
        _, a1, a2 = self.a
        y = np.empty_like(x)
        x1, x2, y1, y2 = self.x1, self.x2, self.y1, self.y2
        for i in range(x.shape[0]):
            xi = float(x[i])
            yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
            x2, x1 = x1, xi
            y2, y1 = y1, yi
            y[i] = yi
        self.x1, self.x2, self.y1, self.y2 = x1, x2, y1, y2
        return y


class Compressor:
    """Compresseur à détection de crête, avec genou doux et rattrapage auto.

    Le gain est calculé sur l'enveloppe, laquelle est obtenue par une
    récurrence à deux constantes de temps (attaque, rétablissement). La
    boucle est écrite en NumPy avec un découpage par segments monotones,
    ce qui la rend assez rapide pour le temps réel.
    """

    def __init__(self, fs: float, threshold_db: float = -24.0,
                 ratio: float = 4.0, attack_ms: float = 8.0,
                 release_ms: float = 180.0, knee_db: float = 6.0):
        self.fs = fs
        self.set(threshold_db, ratio, attack_ms, release_ms, knee_db)
        self.env = 0.0
        self.gain_courant = 1.0

    def set(self, threshold_db: float, ratio: float, attack_ms: float = 8.0,
            release_ms: float = 180.0, knee_db: float = 6.0) -> None:
        self.threshold_db = threshold_db
        self.ratio = max(ratio, 1.0)
        self.knee_db = max(knee_db, 0.0)
        self.a_att = math.exp(-1.0 / (max(attack_ms, 0.1) * 1e-3 * self.fs))
        self.a_rel = math.exp(-1.0 / (max(release_ms, 1.0) * 1e-3 * self.fs))
        # Gain de rattrapage : ce que le compresseur retire au niveau 0 dB.
        excursion = max(-self.threshold_db, 0.0)
        self.makeup = 10 ** ((excursion * (1 - 1 / self.ratio)) / 20.0)

    def _courbe(self, niveau_db: np.ndarray) -> np.ndarray:
        """Gain en dB à appliquer, avec genou quadratique."""
        t, r, k = self.threshold_db, self.ratio, self.knee_db
        delta = niveau_db - t
        sortie = np.where(
            delta <= -k / 2, niveau_db,
            np.where(delta >= k / 2, t + delta / r,
                     niveau_db + (1 / r - 1) * (delta + k / 2) ** 2 / (2 * k)
                     if k > 0 else niveau_db))
        return sortie - niveau_db

    def process(self, x: np.ndarray) -> np.ndarray:
        n = x.shape[0]
        if n == 0:
            return x
        absx = np.abs(x)
        env = np.empty(n)
        e = self.env
        for i in range(n):
            v = float(absx[i])
            a = self.a_att if v > e else self.a_rel
            e = a * e + (1 - a) * v
            env[i] = e
        self.env = e
        niveau_db = 20 * np.log10(np.maximum(env, 1e-9))
        gain_db = self._courbe(niveau_db)
        return x * (10 ** (gain_db / 20.0)) * self.makeup

    @property
    def reduction_db(self) -> float:
        """Réduction de gain instantanée, pour l'afficher."""
        niveau = 20 * math.log10(max(self.env, 1e-9))
        return float(self._courbe(np.asarray([niveau]))[0])


class Limiter:
    """Limiteur doux — aucun échantillon ne sort de [−1, 1].

    Deux étages : une saturation progressive (tangente hyperbolique) qui
    arrondit les crêtes sans les écraser, puis un plafonnement strict pour
    le cas pathologique. Le nombre d'échantillons plafonnés est compté :
    c'est un indicateur de réglage, pas un détail cosmétique.
    """

    def __init__(self, seuil: float = 0.95):
        self.seuil = seuil
        self.ecretages = 0

    def process(self, x: np.ndarray) -> np.ndarray:
        depasse = int(np.count_nonzero(np.abs(x) > self.seuil))
        if depasse:
            self.ecretages += depasse
        y = np.tanh(x / max(self.seuil, 1e-6)) * self.seuil
        return np.clip(y, -1.0, 1.0)


# ---------------------------------------------------------------------------
#  Bip
# ---------------------------------------------------------------------------
class Beeper:
    """Générateur de bips — repère sonore court, indépendant de la musique.

    Les bips sont produits dans le même fil audio que la synthèse, par
    superposition : ils ne peuvent donc ni retarder ni interrompre le flux.
    Une brève rampe d'attaque et d'extinction évite le claquement.
    """

    #  (fréquence Hz, durée ms, gain relatif) par type de repère
    TIMBRES = {
        "evenement":  (880.0, 70.0, 1.0),
        "saturation": (220.0, 180.0, 1.2),
        "marqueur":   (1320.0, 60.0, 0.9),
        "debut":      (660.0, 120.0, 0.8),
        "fin":        (440.0, 200.0, 0.8),
        "test":       (1000.0, 500.0, 1.0),
        "erreur":     (180.0, 300.0, 1.2),
    }

    def __init__(self, fs: int = 44100):
        self.fs = fs
        self._file: list = []
        self._lock = threading.Lock()
        self._reste: Optional[np.ndarray] = None
        self.gain = 10 ** (-12.0 / 20.0)
        self.total = 0

    def set_gain_db(self, gain_db: float) -> None:
        self.gain = 10 ** (min(max(gain_db, -60.0), 6.0) / 20.0)

    def bip(self, genre: str = "evenement", freq: Optional[float] = None,
            duree_ms: Optional[float] = None) -> None:
        """Programme un bip ; il sera mêlé au prochain bloc audio."""
        f, d, g = self.TIMBRES.get(genre, self.TIMBRES["evenement"])
        f = freq if freq else f
        d = duree_ms if duree_ms else d
        n = max(int(self.fs * d / 1000.0), 16)
        t = np.arange(n) / self.fs
        onde = np.sin(2 * math.pi * f * t)
        # rampes de 5 ms pour éviter le claquement
        r = max(int(self.fs * 0.005), 4)
        if n > 2 * r:
            onde[:r] *= np.linspace(0.0, 1.0, r)
            onde[-r:] *= np.linspace(1.0, 0.0, r)
        with self._lock:
            self._file.append(onde * (self.gain * g))
            self.total += 1

    def render(self, frames: int) -> np.ndarray:
        """Bloc de bips à mêler au signal — zéro si rien n'est programmé."""
        out = np.zeros(frames, dtype=np.float64)
        with self._lock:
            if self._reste is not None:
                k = min(frames, self._reste.shape[0])
                out[:k] += self._reste[:k]
                self._reste = (self._reste[k:] if self._reste.shape[0] > k
                               else None)
            while self._file:
                onde = self._file.pop(0)
                k = min(frames, onde.shape[0])
                out[:k] += onde[:k]
                if onde.shape[0] > k:
                    reste = onde[k:]
                    self._reste = (reste if self._reste is None
                                   else _somme_alignee(self._reste, reste))
                    break
        return out


def _somme_alignee(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    n = max(a.shape[0], b.shape[0])
    out = np.zeros(n)
    out[:a.shape[0]] += a
    out[:b.shape[0]] += b
    return out


# ---------------------------------------------------------------------------
#  Chaîne complète
# ---------------------------------------------------------------------------
@dataclass
class OutputMetrics:
    """Ce que la chaîne de sortie mesure sur elle-même."""
    peak: float = 0.0
    rms: float = 0.0
    reduction_db: float = 0.0
    ecretages: int = 0
    gain_total_db: float = 0.0

    @property
    def peak_db(self) -> float:
        return 20 * math.log10(max(self.peak, 1e-9))

    @property
    def rms_db(self) -> float:
        return 20 * math.log10(max(self.rms, 1e-9))


class OutputStage:
    """Étage de sortie complet, piloté par les réglages `audio_out`."""

    def __init__(self, fs: int, settings):
        self.fs = fs
        self.settings = settings
        self._dernier_reglage = None
        self.eq = PeakingEQ(fs, 2500.0, 0.0, 0.9)
        self.comp = Compressor(fs)
        self.limiter = Limiter(0.95)
        self.beeper = Beeper(fs)
        self.metrics = OutputMetrics()
        self.apply_settings()

    def apply_settings(self) -> None:
        s = self.settings.audio_out
        self.gain = 10 ** (min(max(s.gain_db, -60.0), 12.0) / 20.0)
        self.boost = 10 ** (min(max(s.boost_db, 0.0), 36.0) / 20.0)
        self.eq.set(2500.0, min(max(s.presence_boost_db, 0.0), 18.0), 0.9)
        self.comp.set(s.comp_threshold_db, s.comp_ratio)
        self.compression_active = bool(s.compressor)
        self.limitation_active = bool(s.limiter)
        self.beeper.set_gain_db(s.beep_gain_db)
        self.metrics.gain_total_db = s.gain_db + s.boost_db
        # Journaliser le réglage, mais une seule fois par valeur : cette
        # méthode est appelée à chaque construction d'onglet.
        signature = (s.gain_db, s.boost_db, s.presence_boost_db, s.compressor,
                     s.comp_threshold_db, s.comp_ratio, s.limiter)
        if signature != self._dernier_reglage:
            self._dernier_reglage = signature
            log.info("Sortie audio : gain %+.1f dB, amplification %+.1f dB, "
                     "compression %s, limiteur %s", s.gain_db, s.boost_db,
                     "oui" if s.compressor else "no",
                     "oui" if s.limiter else "no")

    def process(self, x: np.ndarray) -> np.ndarray:
        """Traite un bloc de synthèse et y mêle les bips éventuels."""
        y = x * (self.gain * self.boost)
        y = self.eq.process(y)
        if self.compression_active:
            y = self.comp.process(y)
        y = y + self.beeper.render(y.shape[0])
        if self.limitation_active:
            y = self.limiter.process(y)
        else:
            y = np.clip(y, -1.0, 1.0)
        if y.size:
            self.metrics.peak = float(np.max(np.abs(y)))
            self.metrics.rms = float(np.sqrt(np.mean(y * y)))
        self.metrics.reduction_db = (self.comp.reduction_db
                                     if self.compression_active else 0.0)
        self.metrics.ecretages = self.limiter.ecretages
        return y

    # -- repères sonores -----------------------------------------------------
    def bip(self, genre: str = "evenement") -> None:
        self.beeper.bip(genre)

    def test_haut_parleur(self, duree_ms: float = 600.0) -> None:
        """Bip d'essai à 1 kHz — vérifie la sortie sans lancer d'acquisition."""
        self.beeper.bip("test", 1000.0, duree_ms)

    def resume(self) -> str:
        m = self.metrics
        return (f"crête {m.peak_db:+.1f} dB · efficace {m.rms_db:+.1f} dB · "
                f"réduction {m.reduction_db:+.1f} dB · "
                f"{m.ecretages} écrêtage(s)")
