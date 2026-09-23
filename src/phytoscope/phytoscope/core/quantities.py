# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/quantities.py
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

"""Quantities scientifiques — ce qu'on peut dire du signal en chiffres.

L'onglet Multimètre affiche six nombres bien visibles : la tension, le bruit, la
crête à crête, la dérive, la ligne de base, le compte d'événements. Ils suffisent
pour conduire une séance. Ils ne suffisent pas pour **qualify une mesure**, et
c'est ce que ce module ajoute.

Chaque grandeur est accompagnée de ce qu'elle veut dire et de ce qu'elle ne dit
pas. Un nombre sans son interprétation est une invitation à se tromper : « 618 kΩ »
ne signifie rien si l'on ignore que c'est un majorant déduit du bruit, et non une
résistance mesurée à l'ohmmètre.

La résistance, et pourquoi elle est un majorant
----------------------------------------------

La carte ne mesure pas d'impédance en continu : il n'y a pas d'injection de
courant pendant une séance — on écoute, on n'excite pas. Mais toute résistance
produit d'elle-même un bruit, celui de Johnson et Nyquist :

.. math:: e_n = \\sqrt{4 k T R}

d'où l'on tire ``R = S_v / (4 k T)`` à partir de la densité spectrale mesurée.
Le calcul est exact ; son interprétation ne l'est pas tout à fait, car le bruit
observé contient aussi celui de l'amplificateur, celui de l'électrode et tout ce
que le montage capte. **La résistance ainsi obtenue est donc une borne
supérieure** : la source réelle ne peut pas être plus résistive que cela. C'est
exactement ce qu'on veut savoir pour juger un contact — un contact qui sèche voit
ce majorant grimper d'une décade en quelques minutes.

La densité est prise **au-dessus de la bande biologique** (par défaut 10 à 40 Hz,
hors réseau), là où la plante ne produit plus rien : autrement on compterait son
activité comme du bruit, et le majorant n'aurait plus aucun meaning.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .analysis import (allan_deviation, spectre, statistiques_evenements,
                       temps_de_correlation, test_normalite)

__all__ = ["Quantity", "Quantities", "measure", "inventory",
           "BOLTZMANN", "TEMPERATURE_K"]

BOLTZMANN = 1.380649e-23          # J/K, value exacte du SI depuis 2019
TEMPERATURE_K = 293.15            # 20 °C — la température d'une pièce, fault de sonde


@dataclass
class Quantity:
    """Une grandeur mesurée : sa value, son unité, et ce qu'elle raconte.

    ``label`` et ``meaning`` sont des GABARITS, jamais des phrases déjà
    composées : « Écart d'Allan à {tau} s » et non « Écart d'Allan à 1 s ».
    C'est ce qui permet de les translate — une phrase où le nombre est déjà
    incrusté ne peut pas entrer dans un catalogue. L'affichage compose avec
    ``params`` après traduction.
    """
    key: str
    label: str
    value: float
    text: str                    # la value mise en forme, unité comprise
    meaning: str                     # ce que ce nombre dit — en une phrase
    alert: bool = False          # vrai si la value mérite qu'on s'y arrête
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Quantities:
    """L'ensemble des grandeurs calculées sur une fenêtre de signal."""
    duration_s: float = 0.0
    fs: float = 250.0
    entries: List[Quantity] = field(default_factory=list)

    def __iter__(self):
        return iter(self.entries)

    def __len__(self) -> int:
        return len(self.entries)

    def get(self, key: str) -> Optional[Quantity]:
        for g in self.entries:
            if g.key == key:
                return g
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {g.key: g.value for g in self.entries}


# ---------------------------------------------------------------------------
#  Mise en forme
# ---------------------------------------------------------------------------
def _ohms(r: float) -> str:
    if r <= 0 or not math.isfinite(r):
        return "—"
    for seuil, unite, facteur in ((1e9, "GΩ", 1e9), (1e6, "MΩ", 1e6),
                                  (1e3, "kΩ", 1e3)):
        if r >= seuil:
            return f"{r / facteur:.2f} {unite}"
    return f"{r:.0f} Ω"


def _secondes(s: float) -> str:
    if s <= 0 or not math.isfinite(s):
        return "—"
    if s < 1.0:
        return f"{s * 1000:.0f} ms"
    if s < 90.0:
        return f"{s:.1f} s"
    return f"{s / 60:.1f} min"


# ---------------------------------------------------------------------------
#  Le calcul
# ---------------------------------------------------------------------------
def measure(x: np.ndarray, fs: float, full_scale_v: float = 2.5,
            mains_hz: float = 50.0, event_times_s: Optional[Sequence[float]] = None,
            sigma_threshold: float = 3.5,
            thermal_band: Tuple[float, float] = (10.0, 40.0)) -> Quantities:
    """Toutes les grandeurs qu'on peut tirer d'une fenêtre de signal.

    :param full_scale_v: pour la marge de saturation et les bits effectifs.
    :param thermal_band: bande où l'on suppose que la plante ne produit rien,
        et où l'on lit donc le bruit propre de la chaîne.
    """
    g = Quantities(fs=float(fs))
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.size < 64 or fs <= 0:
        return g
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    g.duration_s = x.size / fs
    centre = x - float(np.mean(x))
    rms = float(np.sqrt(np.mean(centre ** 2)))
    crete = float(np.max(np.abs(centre)))

    add = g.entries.append
    sp = spectre(centre, fs, nperseg=int(min(8192, max(256, x.size // 4))))

    # --- 1. le plancher de bruit, en densité --------------------------------
    f1, f2 = thermal_band
    f2 = min(f2, fs / 2.5)
    plancher = sp.plancher(f1, f2) if f2 > f1 else 0.0
    add(Quantity(
        "plancher", "Noise density", plancher,
        f"{plancher * 1e9:.1f} nV/√Hz" if plancher > 0 else "—",
        "Measured between {f1} and {f2} Hz, where the plant produces nothing any more. This is the chain's own noise: electrode, cable, amplifier.",
        params={"f1": f"{f1:g}", "f2": f"{f2:g}"}))

    # --- 2. la résistance équivalente (majorant) ----------------------------
    r_eq = (plancher ** 2) / (4.0 * BOLTZMANN * TEMPERATURE_K) if plancher > 0 else 0.0
    add(Quantity(
        "resistance", "Equivalent resistance", r_eq, _ohms(r_eq),
        "Derived from thermal (Johnson-Nyquist) noise at 20 °C: R = Sᵥ / 4kT. It is an UPPER BOUND — the amplifier's noise and whatever the rig picks up are added in — but it climbs by a decade when a contact dries out, and that is where it earns its keep.",
        alert=r_eq > 5e6))

    # --- 3. le bruit intégré dans la bande utile ----------------------------
    bruit_bande = sp.bruit_dans_bande(0.01, min(10.0, fs / 3))
    add(Quantity(
        "bruit_bande", "Noise in 0.01–10 Hz", bruit_bande,
        f"{bruit_bande * 1e6:.2f} µV RMS" if bruit_bande > 0 else "—",
        "Noise integrated where plant activity actually lives. This, and not the total noise, is what the sought events' amplitude must be compared against.",
        alert=bruit_bande * 1e6 > 30.0))

    # --- 4. le réseau ---------------------------------------------------------
    if mains_hz and fs > 2.5 * mains_hz:
        _, amp = sp.pic(mains_hz, 1.0)
        au_dessus = (20 * math.log10(max(amp, 1e-30) / plancher)
                     if plancher > 0 else 0.0)
        add(Quantity(
            "reseau", "Residue at {f} Hz, above the noise floor", au_dessus,
            f"{au_dessus:+.1f} dB",
            "What the rig picks up from the mains. Past 20 dB it is the shielding and the guard that need revisiting — not the notch filter, which hides the problem without solving it.",
            alert=au_dessus > 20.0, params={"f": f"{mains_hz:g}"}))

    # --- 5. facteur de crête -------------------------------------------------
    facteur = crete / rms if rms > 0 else 0.0
    add(Quantity(
        "crete", "Crest factor", facteur, f"{facteur:.1f}",
        "Ratio of peak to RMS. Around 3 to 4 for Gaussian noise; much higher when clear-cut events stand out, which is a good sign.",
        alert=facteur > 12.0))

    # --- 6. pente spectrale ---------------------------------------------------
    kept = (sp.freqs > 0.02) & (sp.freqs < fs / 2.5)
    pente = 0.0
    if kept.sum() > 8:
        lf = np.log10(sp.freqs[kept])
        ld = np.log10(np.maximum(sp.psd_v2_hz[kept], 1e-30))
        pente = float(np.polyfit(lf, ld, 1)[0]) * 10.0
    add(Quantity(
        "pente", "Spectral slope", pente, f"{pente:+.1f} dB/dec",
        "−10 dB per decade is the signature of 1/f noise, that of electrodes and living media. A flat slope signals dominant white noise — often the electronics, not the plant."))

    # --- 7. stabilité : écart d'Allan ----------------------------------------
    al = allan_deviation(centre, fs)
    for target, key in ((1.0, "allan1"), (10.0, "allan10")):
        if al.taus.size and target <= al.taus[-1]:
            i = int(np.argmin(np.abs(al.taus - target)))
            value = float(al.deviations[i])
            add(Quantity(
                key, "Allan deviation at {tau} s", value,
                f"{value * 1e6:.3f} µV",
                "Stability borrowed from time metrology: unlike the standard deviation, it tells noise — which improves with averaging — apart from drift, which worsens.",
                params={"tau": f"{target:g}"}))
    if al.tau_optimal > 0:
        add(Quantity(
            "tau_optimal", "Optimal integration", al.tau_optimal,
            f"{_secondes(al.tau_optimal)} → {al.minimum * 1e6:.3f} µV",
            "The most favourable averaging time. Beyond it, averaging longer DEGRADES the measurement: drift outweighs noise. Observed regime: {regime}.",
            params={"regime": al.regime or "indéterminé"}))

    # --- 8. temps de corrélation ---------------------------------------------
    tau_c = temps_de_correlation(centre, fs)
    add(Quantity(
        "correlation", "Correlation time", tau_c, _secondes(tau_c),
        "The time after which the signal no longer resembles itself. It gives the inertia of the system being measured, and the shortest analysis window that still means something."))

    # --- 9. normalité ---------------------------------------------------------
    p = test_normalite(centre)
    add(Quantity(
        "normalite", "Normality (d'Agostino-Pearson)", p, f"p = {p:.3f}",
        "Above 0.05 the distribution is consistent with a normal law and a threshold in standard deviations means something. Below, that threshold becomes questionable — and that is often a good sign: it means something is happening.",
        alert=p <= 0.05))

    # --- 10. bits effectifs ---------------------------------------------------
    if rms > 0 and full_scale_v > 0:
        bits = math.log2(full_scale_v * 2.0 / (rms * math.sqrt(12.0)))
        add(Quantity(
            "bits", "Effective resolution", bits, f"{bits:.1f} bits",
            "What the chain really delivers, noise included, over the converter's full scale — always less than its nominal 24 bits."))

    # --- 11. marge avant saturation ------------------------------------------
    if full_scale_v > 0:
        marge = 100.0 * (1.0 - min(crete / full_scale_v, 1.0))
        add(Quantity(
            "marge", "Headroom before saturation", marge, f"{marge:.1f} %",
            "What is left before the converter hits its limit. Below 10 %, a clear-cut event will be clipped, and clipping cannot be undone afterwards.",
            alert=marge < 10.0))

    # --- 12. statistique des événements --------------------------------------
    if event_times_s:
        st = statistiques_evenements(event_times_s, duree_s=g.duration_s)
        add(Quantity(
            "events", "Event rate", st.taux_par_min,
            f"{st.taux_par_min:.2f} /min",
            "At the {sigma} σ threshold currently in force. The rate depends as much on the threshold as on the plant: change it and you change the rate.",
            params={"sigma": f"{sigma_threshold:g}"}))
        #  En dessous d'une dizaine d'événements, Fano et CV sont du bruit
        #  déguisé en chiffre : on affiche le compte, pas une statistique à
        #  laquelle on n'a pas droit.
        assez = st.n >= 10
        add(Quantity(
            "fano", "Fano factor", st.fano if assez else 0.0,
            f"{st.fano:.2f}" if assez else f"— (n = {st.n})",
            "Variance divided by mean of the count. It equals 1 for a purely random process; below, the events are regular; above, they come in bursts. About ten events are needed before this number means anything."))
        if assez:
            add(Quantity(
                "cv", "Regularity (CV of intervals)", st.cv, f"{st.cv:.2f}",
                "Coefficient of variation of the intervals. Below 0.6 the events are too regular to be botanical — look instead for a pump, a ventilation system or automatic watering. Above 1.4 they come in bursts, which is the expected behaviour of living tissue.",
                alert=st.cv < 0.6))
    return g


def inventory() -> List[str]:
    """Tous les libellés et toutes les explications, pour le catalogue.

    Plutôt que de recopier les chaînes dans une table — qui dériverait au
    premier ajout —, on fait tourner le calcul une fois sur un signal
    synthétique et l'on récolte ce qu'il produit. Une grandeur ajoutée sans
    traduction fait donc échouer l'essai de couverture, ce qui est exactement
    le comportement voulu.
    """
    fs = 250.0
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 2e-6, int(120 * fs))
    evs = list(np.arange(1.0, 119.0, 4.0))
    vus: List[str] = []
    for hz in (50.0, 60.0):
        for item in measure(x, fs, mains_hz=hz, event_times_s=evs):
            for text in (item.label, item.meaning):
                if text not in vus:
                    vus.append(text)
            for value in item.params.values():
                if isinstance(value, str) and not value.replace(".", "").isdigit():
                    if value not in vus:
                        vus.append(value)
    return vus
