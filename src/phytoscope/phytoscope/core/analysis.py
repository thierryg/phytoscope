# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/analysis.py
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

"""Mesures scientifiques — ce qu'on peut affirmer d'un enregistrement.

Ce module rassemble les grandeurs qu'un opérateur sérieux veut pouvoir citer
dans un compte rendu, avec leurs définitions et leurs limites. Chaque
fonction renvoie une valeur **et** de quoi la relativiser : incertitude,
nombre de points, hypothèses.

Contenu :

* **Densité spectrale** en V/√Hz — l'unité dans laquelle se lisent les
  spécifications de bruit des amplificateurs, et la seule qui permette de
  comparer deux montages échantillonnés différemment.
* **Variance d'Allan** — l'outil des métrologues du temps, transposé ici à
  la dérive d'une électrode : elle sépare le bruit blanc (pente −1/2), la
  marche aléatoire (pente +1/2) et la dérive linéaire (pente +1).
* **Autocorrélation** et temps de corrélation — pour savoir si deux
  échantillons successifs sont indépendants, condition de tout test
  statistique ultérieur.
* **Statistique des événements** — intervalle moyen, facteur de Fano,
  coefficient de variation : un processus de Poisson a un Fano de 1 ; une
  plante « qui réagit » devrait s'en écarter, et c'est mesurable.
* **Régression de dérive** avec incertitude sur la pente et coefficient de
  détermination — parce qu'une dérive annoncée sans R² ne veut rien dire.
* **Rapport signal sur bruit**, distorsion harmonique et plancher de bruit,
  pour qualifier la chaîne elle-même à l'aide d'un signal étalon.
* **Test de normalité** de d'Agostino-Pearson, qui conditionne l'emploi d'un
  seuil exprimé en écarts-types.

Aucune de ces mesures ne dit ce que « ressent » la plante. Elles disent ce
que vaut la mesure — ce qui est la seule chose qu'un instrument puisse dire.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

from .dsp import welch_psd
from .logging_setup import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
#  Densité spectrale
# ---------------------------------------------------------------------------
@dataclass
class SpectralResult:
    """Densité spectrale, avec tout ce qu'il faut pour la lire."""
    freqs: np.ndarray
    psd_v2_hz: np.ndarray           # V²/Hz
    fs: float = 0.0
    nperseg: int = 0
    n_segments: int = 0
    window: str = "hann"

    @property
    def asd_v_rthz(self) -> np.ndarray:
        """Densité d'amplitude, en V/√Hz — l'unité des notices techniques."""
        return np.sqrt(np.maximum(self.psd_v2_hz, 0.0))

    def bruit_dans_bande(self, f1: float, f2: float) -> float:
        """Bruit efficace intégré entre deux fréquences, en volts."""
        m = (self.freqs >= f1) & (self.freqs <= f2)
        if not m.any() or self.freqs.size < 2:
            return 0.0
        df = float(self.freqs[1] - self.freqs[0])
        return float(np.sqrt(np.sum(self.psd_v2_hz[m]) * df))

    def plancher(self, f1: float = 1.0, f2: float = 10.0) -> float:
        """Plancher de bruit médian dans une bande, en V/√Hz."""
        m = (self.freqs >= f1) & (self.freqs <= f2)
        return float(np.median(self.asd_v_rthz[m])) if m.any() else 0.0

    def pic(self, autour: float, largeur: float = 1.0) -> Tuple[float, float]:
        """(fréquence, amplitude V/√Hz) du maximum autour d'une fréquence."""
        m = (self.freqs > autour - largeur) & (self.freqs < autour + largeur)
        if not m.any():
            return (0.0, 0.0)
        idx = int(np.argmax(self.psd_v2_hz[m]))
        f = float(self.freqs[m][idx])
        return (f, float(self.asd_v_rthz[m][idx]))

    def incertitude_db(self) -> float:
        """Écart-type de l'estimation, en décibels (Welch, segments moyennés)."""
        n = max(self.n_segments, 1)
        return 10 * math.log10(1 + 1 / math.sqrt(n))


def spectre(x: np.ndarray, fs: float, nperseg: int = 4096,
            overlap: float = 0.5, window: str = "hann") -> SpectralResult:
    """Densité spectrale de puissance par la méthode de Welch."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    nperseg = int(min(max(nperseg, 16), max(x.size, 16)))
    f, p = welch_psd(x, fs, nperseg=nperseg, overlap=overlap)
    step = max(int(nperseg * (1 - overlap)), 1)
    segments = max(1 + (x.size - nperseg) // step, 1) if x.size >= nperseg else 1
    return SpectralResult(freqs=f, psd_v2_hz=p, fs=fs, nperseg=nperseg,
                          n_segments=segments, window=window)


# ---------------------------------------------------------------------------
#  Variance d'Allan
# ---------------------------------------------------------------------------
@dataclass
class AllanResult:
    taus: np.ndarray                # durées d'intégration, en secondes
    deviations: np.ndarray          # écart-type d'Allan, en volts
    pente: float = 0.0              # pente en log-log
    regime: str = ""                # interprétation de la pente
    tau_optimal: float = 0.0        # durée d'intégration la plus favorable
    minimum: float = 0.0

    def interpretation(self) -> List[str]:
        return [
            f"Pente moyenne : {self.pente:+.2f} — {self.regime}",
            f"Meilleure intégration : {self.tau_optimal:.1f} s "
            f"({self.minimum * 1e6:.3f} µV)",
            "Au-delà de cette durée, moyenner plus longtemps DÉGRADE la mesure : "
            "la dérive l'emporte sur le bruit.",
        ]


def allan_deviation(x: np.ndarray, fs: float,
                    n_points: int = 24) -> AllanResult:
    """Écart-type d'Allan superposé — la bonne mesure de la stabilité.

    L'écart-type classique d'un signal qui dérive n'a pas de sens : il croît
    indéfiniment avec la durée. L'écart-type d'Allan, lui, distingue le
    bruit (qui s'améliore en moyennant) de la dérive (qui empire).
    """
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    n = x.size
    if n < 32 or fs <= 0:
        return AllanResult(np.zeros(0), np.zeros(0))
    m_max = n // 4
    ms = np.unique(np.logspace(0, math.log10(max(m_max, 2)),
                               n_points).astype(int))
    taus, devs = [], []
    for m in ms:
        if m < 1 or m > m_max:
            continue
        k = n // m
        if k < 3:
            continue
        moyennes = x[:k * m].reshape(k, m).mean(axis=1)
        diff = np.diff(moyennes)
        av = float(np.mean(diff ** 2) / 2.0)
        taus.append(m / fs)
        devs.append(math.sqrt(max(av, 0.0)))
    if len(taus) < 3:
        return AllanResult(np.asarray(taus), np.asarray(devs))
    taus_a = np.asarray(taus)
    devs_a = np.asarray(devs)
    ok = devs_a > 0
    pente = 0.0
    if ok.sum() >= 3:
        pente = float(np.polyfit(np.log10(taus_a[ok]), np.log10(devs_a[ok]), 1)[0])
    if pente < -0.35:
        regime = "bruit blanc dominant (moyenner améliore la mesure)"
    elif pente < 0.15:
        regime = "palier de scintillation (moyenner n'améliore plus rien)"
    elif pente < 0.75:
        regime = "marche aléatoire (l'électrode vagabonde)"
    else:
        regime = "dérive déterministe (température, séchage du gel)"
    i = int(np.argmin(devs_a))
    return AllanResult(taus_a, devs_a, pente, regime,
                       float(taus_a[i]), float(devs_a[i]))


# ---------------------------------------------------------------------------
#  Corrélation
# ---------------------------------------------------------------------------
def autocorrelation(x: np.ndarray, fs: float,
                    max_lag_s: float = 60.0) -> Tuple[np.ndarray, np.ndarray]:
    """Autocorrélation normalisée, et les décalages correspondants."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    if x.size < 8:
        return np.zeros(0), np.zeros(0)
    x = x - x.mean()
    n = x.size
    max_lag = int(min(max_lag_s * fs, n - 1))
    fft_size = 1 << int(math.ceil(math.log2(2 * n)))
    spec = np.fft.rfft(x, fft_size)
    corr = np.fft.irfft(spec * np.conj(spec), fft_size)[:max_lag + 1]
    if corr[0] <= 0:
        return np.zeros(0), np.zeros(0)
    corr = corr / corr[0]
    return np.arange(max_lag + 1) / fs, corr


def temps_de_correlation(x: np.ndarray, fs: float) -> float:
    """Décalage auquel l'autocorrélation tombe sous 1/e."""
    lags, corr = autocorrelation(x, fs)
    if corr.size == 0:
        return 0.0
    seuil = 1.0 / math.e
    sous = np.nonzero(corr < seuil)[0]
    return float(lags[sous[0]]) if sous.size else float(lags[-1])


# ---------------------------------------------------------------------------
#  Dérive
# ---------------------------------------------------------------------------
@dataclass
class DriftResult:
    pente_v_par_s: float = 0.0
    incertitude_v_par_s: float = 0.0
    ordonnee_v: float = 0.0
    r2: float = 0.0
    n: int = 0
    duree_s: float = 0.0

    @property
    def pente_uv_par_min(self) -> float:
        return self.pente_v_par_s * 60.0 * 1e6

    def significative(self, seuil: float = 3.0) -> bool:
        """Vrai si la pente dépasse `seuil` fois son incertitude."""
        return (abs(self.pente_v_par_s) >
                seuil * max(self.incertitude_v_par_s, 1e-30))

    def resume(self) -> str:
        if self.n < 3:
            return "dérive non mesurable (trop peu de points)"
        signe = "significative" if self.significative() else "non significative"
        return (f"{self.pente_uv_par_min:+.2f} µV/min "
                f"± {self.incertitude_v_par_s * 60e6:.2f} — R² = {self.r2:.3f} "
                f"({signe})")


def derive(x: np.ndarray, fs: float) -> DriftResult:
    """Régression linéaire, avec incertitude sur la pente et R²."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    n = x.size
    if n < 3 or fs <= 0:
        return DriftResult(n=n)
    t = np.arange(n) / fs
    a, b = np.polyfit(t, x, 1)
    residus = x - (a * t + b)
    ss_res = float(np.sum(residus ** 2))
    ss_tot = float(np.sum((x - x.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    s_xx = float(np.sum((t - t.mean()) ** 2))
    sigma = math.sqrt(ss_res / (n - 2)) if n > 2 else 0.0
    inc = sigma / math.sqrt(s_xx) if s_xx > 0 else 0.0
    return DriftResult(float(a), inc, float(b), r2, n, n / fs)


# ---------------------------------------------------------------------------
#  Statistique des événements
# ---------------------------------------------------------------------------
@dataclass
class EventStats:
    n: int = 0
    duree_s: float = 0.0
    taux_par_min: float = 0.0
    intervalle_moyen_s: float = 0.0
    intervalle_median_s: float = 0.0
    cv: float = 0.0                 # coefficient de variation des intervalles
    fano: float = 0.0               # variance / moyenne du comptage
    amplitude_moyenne_v: float = 0.0
    amplitude_max_v: float = 0.0

    def interpretation(self) -> List[str]:
        out = [f"{self.n} événements en {self.duree_s / 60:.1f} min "
               f"({self.taux_par_min:.2f} par minute)"]
        if self.n < 10:
            out.append("Trop peu d'événements pour conclure quoi que ce soit.")
            return out
        out.append(f"Intervalle moyen {self.intervalle_moyen_s:.1f} s, "
                   f"médian {self.intervalle_median_s:.1f} s")
        if self.cv < 0.6:
            out.append(f"CV = {self.cv:.2f} : les événements sont RÉGULIERS — "
                       "méfiance, cela ressemble à une source périodique "
                       "(réseau, ventilation, arrosage automatique).")
        elif self.cv > 1.4:
            out.append(f"CV = {self.cv:.2f} : les événements arrivent par "
                       "bouffées, ce qui est le comportement attendu d'un "
                       "tissu vivant sollicité.")
        else:
            out.append(f"CV = {self.cv:.2f} : compatible avec un processus de "
                       "Poisson, c'est-à-dire avec le hasard.")
        out.append(f"Facteur de Fano = {self.fano:.2f} "
                   "(1,00 pour un processus purement aléatoire)")
        return out


def statistiques_evenements(temps_s: Sequence[float],
                            amplitudes_v: Optional[Sequence[float]] = None,
                            duree_s: float = 0.0,
                            fenetre_s: float = 60.0) -> EventStats:
    """Caractérise une série d'événements — régularité, groupement, intensité."""
    t = np.asarray(list(temps_s), dtype=np.float64)
    st = EventStats(n=int(t.size), duree_s=duree_s or (float(t[-1]) if t.size else 0.0))
    if st.duree_s > 0:
        st.taux_par_min = st.n / (st.duree_s / 60.0)
    if t.size >= 2:
        intervalles = np.diff(np.sort(t))
        st.intervalle_moyen_s = float(np.mean(intervalles))
        st.intervalle_median_s = float(np.median(intervalles))
        if st.intervalle_moyen_s > 0:
            st.cv = float(np.std(intervalles) / st.intervalle_moyen_s)
    if t.size >= 4 and st.duree_s > fenetre_s:
        bords = np.arange(0.0, st.duree_s + fenetre_s, fenetre_s)
        comptes, _ = np.histogram(t, bins=bords)
        moyenne = float(np.mean(comptes))
        st.fano = float(np.var(comptes) / moyenne) if moyenne > 0 else 0.0
    if amplitudes_v is not None and len(amplitudes_v):
        a = np.abs(np.asarray(list(amplitudes_v), dtype=np.float64))
        st.amplitude_moyenne_v = float(np.mean(a))
        st.amplitude_max_v = float(np.max(a))
    return st


# ---------------------------------------------------------------------------
#  Qualification de la chaîne
# ---------------------------------------------------------------------------
@dataclass
class ChainQuality:
    bruit_rms_v: float = 0.0
    bruit_pp_v: float = 0.0
    plancher_v_rthz: float = 0.0
    snr_db: float = 0.0
    thd_percent: float = 0.0
    enob: float = 0.0               # nombre effectif de bits
    reseau_db: float = 0.0          # réjection du réseau
    normalite_p: float = 0.0

    def resume(self) -> List[str]:
        out = [f"Bruit : {self.bruit_rms_v * 1e6:.3f} µV eff., "
               f"{self.bruit_pp_v * 1e6:.1f} µV crête à crête",
               f"Plancher : {self.plancher_v_rthz * 1e9:.1f} nV/√Hz"]
        if self.snr_db:
            out.append(f"Rapport signal sur bruit : {self.snr_db:.1f} dB "
                       f"(soit {self.enob:.1f} bits effectifs)")
        if self.thd_percent:
            out.append(f"Distorsion harmonique : {self.thd_percent:.3f} %")
        if self.reseau_db:
            out.append(f"Résidu de réseau : {self.reseau_db:+.1f} dB "
                       "au-dessus du plancher")
        if self.normalite_p:
            verdict = ("compatible avec une loi normale"
                       if self.normalite_p > 0.05 else
                       "NON normal : un seuil en σ est discutable")
            out.append(f"Normalité : p = {self.normalite_p:.3f} — {verdict}")
        return out


def qualifier_chaine(x: np.ndarray, fs: float,
                     f_signal: Optional[float] = None,
                     mains: float = 50.0) -> ChainQuality:
    """Qualifie la chaîne de mesure à partir d'un enregistrement.

    Si `f_signal` est donnée (essai avec un générateur étalon), le rapport
    signal sur bruit et la distorsion sont calculés ; sinon, seules les
    grandeurs de bruit le sont.
    """
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    q = ChainQuality()
    if x.size < 32:
        return q
    centre = x - float(np.mean(x))
    q.bruit_rms_v = float(np.sqrt(np.mean(centre ** 2)))
    q.bruit_pp_v = float(np.percentile(centre, 99.9) - np.percentile(centre, 0.1))

    sp = spectre(centre, fs, nperseg=min(8192, x.size))
    q.plancher_v_rthz = sp.plancher(max(fs / 100, 0.5), min(fs / 3, 100.0))

    if mains and fs > 2.5 * mains:
        _, amp = sp.pic(mains, 1.0)
        if q.plancher_v_rthz > 0:
            q.reseau_db = 20 * math.log10(max(amp, 1e-30) / q.plancher_v_rthz)

    if f_signal and fs > 2.5 * f_signal:
        f, p = sp.freqs, sp.psd_v2_hz
        df = float(f[1] - f[0]) if f.size > 1 else 1.0
        bande = lambda f0: (f > f0 - 2 * df) & (f < f0 + 2 * df)   # noqa: E731
        p_sig = float(np.sum(p[bande(f_signal)]) * df)
        harmoniques = 0.0
        for k in range(2, 6):
            fk = k * f_signal
            if fk < fs / 2:
                harmoniques += float(np.sum(p[bande(fk)]) * df)
        masque = np.ones_like(p, dtype=bool)
        for k in range(1, 6):
            masque &= ~bande(k * f_signal)
        p_bruit = float(np.sum(p[masque]) * df)
        if p_bruit > 0 and p_sig > 0:
            q.snr_db = 10 * math.log10(p_sig / p_bruit)
            q.enob = (q.snr_db - 1.76) / 6.02
        if p_sig > 0:
            q.thd_percent = 100.0 * math.sqrt(max(harmoniques, 0.0) / p_sig)

    q.normalite_p = test_normalite(centre)
    return q


def test_normalite(x: np.ndarray) -> float:
    """Test de d'Agostino-Pearson — renvoie une valeur p approchée.

    Implémenté sans SciPy : asymétrie et aplatissement sont combinés en une
    statistique K², approximativement distribuée en χ² à deux degrés de
    liberté, dont la fonction de survie est explicite : exp(−K²/2).
    """
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    n = x.size
    if n < 20:
        return 0.0
    m = float(np.mean(x))
    s = float(np.std(x))
    if s <= 0:
        return 0.0
    z = (x - m) / s
    g1 = float(np.mean(z ** 3))
    g2 = float(np.mean(z ** 4)) - 3.0

    # Transformation de l'asymétrie (D'Agostino 1970)
    y = g1 * math.sqrt((n + 1) * (n + 3) / (6.0 * (n - 2)))
    b2 = (3.0 * (n * n + 27 * n - 70) * (n + 1) * (n + 3) /
          ((n - 2) * (n + 5) * (n + 7) * (n + 9)))
    w2 = -1 + math.sqrt(2 * (b2 - 1))
    if w2 <= 1:
        return 0.0
    delta = 1.0 / math.sqrt(0.5 * math.log(w2))
    alpha = math.sqrt(2.0 / (w2 - 1))
    z1 = delta * math.asinh(y / alpha) if alpha > 0 else 0.0

    # Transformation de l'aplatissement (Anscombe-Glynn 1983)
    e = 24.0 * n * (n - 2) * (n - 3) / ((n + 1) ** 2 * (n + 3) * (n + 5))
    if e <= 0:
        return 0.0
    xx = (g2 - 0.0) / math.sqrt(e)
    b = (6.0 * (n * n - 5 * n + 2) / ((n + 7) * (n + 9)) *
         math.sqrt(6.0 * (n + 3) * (n + 5) / (n * (n - 2) * (n - 3))))
    a = 6.0 + 8.0 / b * (2.0 / b + math.sqrt(1 + 4.0 / (b * b))) if b > 0 else 6.0
    terme = (1 - 2.0 / a) / (1 + xx * math.sqrt(2.0 / (a - 4)))
    if terme <= 0:
        return 0.0
    z2 = ((1 - 2.0 / (9 * a)) - terme ** (1 / 3)) / math.sqrt(2.0 / (9 * a))

    k2 = z1 * z1 + z2 * z2
    return float(math.exp(-k2 / 2.0))          # survie du χ² à 2 ddl


# ---------------------------------------------------------------------------
#  Histogramme
# ---------------------------------------------------------------------------
def histogramme(x: np.ndarray, bins: int = 64) -> Tuple[np.ndarray, np.ndarray]:
    """Histogramme normalisé en densité, avec les centres de classe."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    if x.size < 4:
        return np.zeros(0), np.zeros(0)
    compte, bords = np.histogram(x, bins=max(int(bins), 4), density=True)
    centres = 0.5 * (bords[:-1] + bords[1:])
    return centres, compte


def gaussienne_equivalente(x: np.ndarray, centres: np.ndarray) -> np.ndarray:
    """Loi normale de mêmes moyenne et écart-type, pour comparaison visuelle."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    if x.size < 2 or centres.size == 0:
        return np.zeros_like(centres)
    m, s = float(np.mean(x)), float(np.std(x))
    if s <= 0:
        return np.zeros_like(centres)
    return np.exp(-0.5 * ((centres - m) / s) ** 2) / (s * math.sqrt(2 * math.pi))


# ---------------------------------------------------------------------------
#  Rapport complet
# ---------------------------------------------------------------------------
def rapport_complet(x: np.ndarray, fs: float,
                    evenements_s: Optional[Sequence[float]] = None,
                    amplitudes_v: Optional[Sequence[float]] = None,
                    mains: float = 50.0) -> str:
    """Rapport de mesure prêt à être collé dans un carnet de laboratoire."""
    x = np.asarray(x, dtype=np.float64).reshape(-1)
    lignes = ["RAPPORT DE MESURE", "=" * 60, ""]
    lignes.append(f"Durée analysée : {x.size / fs:.1f} s à {fs:g} Hz "
                  f"({x.size} échantillons)")
    lignes.append("")

    q = qualifier_chaine(x, fs, mains=mains)
    lignes += ["QUALITÉ DE LA CHAÎNE", "-" * 60] + \
        ["  " + l for l in q.resume()] + [""]

    d = derive(x, fs)
    lignes += ["DÉRIVE", "-" * 60, "  " + d.resume(), ""]

    a = allan_deviation(x, fs)
    if a.taus.size:
        lignes += ["STABILITÉ (VARIANCE D'ALLAN)", "-" * 60] + \
            ["  " + l for l in a.interpretation()] + [""]

    tc = temps_de_correlation(x, fs)
    lignes += ["CORRÉLATION", "-" * 60,
               f"  Temps de corrélation : {tc:.2f} s",
               f"  Échantillons indépendants : environ {x.size / max(tc * fs, 1):.0f}",
               ""]

    if evenements_s:
        st = statistiques_evenements(evenements_s, amplitudes_v, x.size / fs)
        lignes += ["ÉVÉNEMENTS", "-" * 60] + \
            ["  " + l for l in st.interpretation()] + [""]

    lignes += ["AVERTISSEMENT", "-" * 60,
               "  Ces grandeurs qualifient la MESURE, non la plante. Aucune",
               "  d'entre elles ne permet d'affirmer qu'un signal traduit un",
               "  état physiologique : il y faut un protocole avec témoin."]
    return "\n".join(lignes)
