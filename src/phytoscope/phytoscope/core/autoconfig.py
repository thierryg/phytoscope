# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/autoconfig.py
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

"""Auto-configuration : le logiciel se règle tout seul, et dit ce qu'il a fait.

L'assistant écoute quelques secondes, mesure, puis propose un jeu de
réglages. Il ne les applique qu'après accord — et il affiche systématiquement
**pourquoi** il propose ce qu'il propose. Une auto-configuration opaque
produit des utilisateurs qui ne comprennent pas leur instrument.

Mesures effectuées :

* plancher de bruit efficace, dans la bande utile ;
* présence et fréquence du réseau (50 ou 60 Hz) ;
* dérive continue (µV/min) ;
* saturation éventuelle de l'entrée ;
* amplitude typique des événements, d'où le seuil et la densité musicale.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .dsp import Biquad, build_chain, dominant_mains, welch_psd


@dataclass
class AutoConfigResult:
    """Ce que l'assistant a mesuré, ce qu'il propose, et pourquoi."""
    ok: bool = False
    duration_s: float = 0.0
    noise_rms_v: float = 0.0
    noise_pp_v: float = 0.0
    mains_hz: Optional[float] = None
    mains_ratio_db: float = 0.0
    drift_v_per_min: float = 0.0
    saturated: bool = False
    suggested: Dict[str, Any] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> List[str]:
        out = [f"Durée analysée : {self.duration_s:.1f} s",
               f"Bruit : {self.noise_rms_v * 1e6:.2f} µV eff. "
               f"({self.noise_pp_v * 1e6:.1f} µV crête à crête)"]
        if self.mains_hz:
            out.append(f"Réseau détecté : {self.mains_hz:g} Hz "
                       f"({self.mains_ratio_db:+.0f} dB au-dessus du plancher)")
        else:
            out.append("Réseau : non détecté — inutile d'activer le réjecteur")
        out.append(f"Dérive : {self.drift_v_per_min * 1e6:+.1f} µV/min")
        if self.saturated:
            out.append("⚠ Saturation détectée : baissez le gain matériel")
        return out


def analyse(signal: np.ndarray, fs: float, full_scale_v: float = 2.5,
            settings=None) -> AutoConfigResult:
    """Analyse un extrait de signal et propose des réglages."""
    res = AutoConfigResult()
    x = np.asarray(signal, dtype=np.float64).reshape(-1)
    if x.size < int(fs * 2):
        res.warnings.append("Extrait trop court : il faut au moins deux secondes.")
        return res
    res.duration_s = x.size / fs

    # 1. saturation
    if np.max(np.abs(x)) > 0.95 * full_scale_v:
        res.saturated = True
        res.warnings.append(
            "Le signal touche la pleine échelle : le gain matériel est trop élevé, "
            "ou une électrode est débranchée.")

    # 2. dérive : régression linéaire sur l'ensemble
    t = np.arange(x.size) / fs
    if x.size > 2:
        slope, _ = np.polyfit(t, x, 1)
        res.drift_v_per_min = float(slope) * 60.0

    # 3. réseau
    mains = dominant_mains(x, fs)
    res.mains_hz = mains
    if mains:
        f, p = welch_psd(x, fs, nperseg=int(min(4096, x.size)))
        band = (f > mains - 1.5) & (f < mains + 1.5)
        ref = p[(f > 5) & (f < min(fs / 2 - 5, 100.0))]
        floor = float(np.median(ref)) if ref.size else 1e-30
        peak = float(p[band].max()) if band.any() else floor
        res.mains_ratio_db = 10 * math.log10(max(peak, 1e-30) / max(floor, 1e-30))

    # 4. bruit, mesuré APRÈS filtrage : c'est ce que verra la détection
    chain = build_chain(fs, highpass=0.05, lowpass=min(40.0, fs / 3),
                        notch=mains or 0.0)
    y = chain.process(x - float(np.mean(x)))
    tail = y[int(fs):] if y.size > int(fs) * 2 else y      # on jette le transitoire
    res.noise_rms_v = float(np.sqrt(np.mean(tail ** 2)))
    res.noise_pp_v = float(np.percentile(tail, 99.5) - np.percentile(tail, 0.5))

    # 5. propositions
    sug: Dict[str, Any] = {}
    reasons: List[str] = []

    sug["notch_hz"] = mains or 0.0
    reasons.append(f"Réjecteur : {mains:g} Hz" if mains else
                   "Réjecteur désactivé : aucun résidu de réseau mesurable")

    sug["highpass_hz"] = 0.01 if abs(res.drift_v_per_min) < 2e-4 else 0.05
    reasons.append(f"Passe-haut à {sug['highpass_hz']:g} Hz "
                   f"(dérive mesurée : {res.drift_v_per_min * 1e6:+.0f} µV/min)")

    sug["lowpass_hz"] = 40.0 if fs > 100 else max(fs / 4, 2.0)
    reasons.append(f"Passe-bas à {sug['lowpass_hz']:g} Hz : "
                   "au-delà, il n'y a plus de physiologie, seulement du bruit")

    # seuil : on vise environ une douzaine d'événements par minute
    sigma = 3.5
    if res.noise_rms_v > 0:
        sigma = 3.0 if res.noise_rms_v < 3e-6 else (4.0 if res.noise_rms_v < 2e-5 else 5.0)
    sug["event_threshold_sigma"] = sigma
    reasons.append(f"Seuil à {sigma:g} σ, choisi d'après le bruit mesuré "
                   f"({res.noise_rms_v * 1e6:.1f} µV eff.)")

    sug["event_min_amplitude_uv"] = max(4.0, res.noise_rms_v * 1e6 * 2.0)
    reasons.append(f"Amplitude minimale : {sug['event_min_amplitude_uv']:.0f} µV, "
                   "pour ne pas sonifier le bruit de fond")

    sug["density_per_min"] = 24.0 if res.noise_rms_v < 2e-5 else 12.0
    reasons.append(f"Densité musicale : {sug['density_per_min']:g} notes par minute")

    # gain matériel : viser 30 % de la pleine échelle
    if not res.saturated and res.noise_pp_v > 0:
        target = 0.30 * full_scale_v
        span = max(res.noise_pp_v, 1e-9)
        factor = target / span
        gains = [1, 2, 5, 10, 20, 50, 100, 200]
        cur = getattr(getattr(settings, "acquisition", None), "hardware_gain", 0) or 1
        want = cur * factor
        best = min(gains, key=lambda g: abs(math.log(max(g, 1) / max(want, 1e-6))))
        sug["hardware_gain"] = best
        reasons.append(f"Gain matériel ×{best} : le signal occupera environ "
                       f"{100 * span * best / max(cur, 1) / full_scale_v:.0f} % "
                       "de la plage de conversion")

    res.suggested = sug
    res.reasons = reasons
    res.ok = True
    return res


def apply(result: AutoConfigResult, settings) -> List[str]:
    """Applique les réglages proposés ; renvoie la liste des changements."""
    changed: List[str] = []
    s = result.suggested
    p, a, m = settings.processing, settings.acquisition, settings.music
    mapping = [
        (p, "highpass_hz", "passe-haut"), (p, "lowpass_hz", "passe-bas"),
        (p, "notch_hz", "réjecteur"),
        (p, "event_threshold_sigma", "seuil de détection"),
        (p, "event_min_amplitude_uv", "amplitude minimale"),
        (m, "density_per_min", "densité musicale"),
        (a, "hardware_gain", "gain matériel"),
    ]
    for obj, key, label in mapping:
        if key in s and getattr(obj, key, None) != s[key]:
            old = getattr(obj, key)
            setattr(obj, key, s[key])
            changed.append(f"{label} : {old} → {s[key]}")
    return changed
