# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/features.py
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

"""Descripteurs avancés : FFT, ondelettes, MFCC, LPC, cepstre.

Ce module ajoute au logiciel les représentations qu'on emploie couramment en
traitement de la parole. Il faut dire d'emblée pourquoi elles ne s'appliquent
pas telles quelles à un signal végétal, et ce qu'on a fait pour qu'elles aient
malgré tout un sens.

Un signal de parole est échantillonné à 16 000 Hz et occupe la bande 80 Hz –
8 kHz. Le nôtre est échantillonné à 250 Hz et occupe la bande 0,001 Hz – 40 Hz :
**cinq décades plus bas**. Toutes les constantes des outils de la parole —
largeur des fenêtres, bornes du banc de Mel, ordre de prédiction — sont donc
transposées d'après la fréquence d'échantillonnage réelle, jamais recopiées.

Ce qui survit à la transposition, et ce qui n'y survit pas :

=========================  ====================================================
Outil                      Ce qu'il vaut ici
=========================  ====================================================
FFT / spectre              Directement valable. C'est la représentation de
                           référence pour repérer le réseau et les périodicités.
Ondelettes (CWT)           **Le mieux adapté.** Le signal végétal est non
                           stationnaire par nature : une bouffée d'activité dure
                           quelques secondes dans un fond qui dérive sur des
                           heures. La FFT moyenne cela ; l'ondelette le montre.
MFCC                       Transposable, mais l'échelle de Mel modélise
                           l'audition humaine, qui ne dit rien d'une plante. On
                           la conserve comme **compression perceptuelle d'un
                           spectre**, utile pour comparer des séquences entre
                           elles, non comme mesure physiologique.
LPC                        Mathématiquement valable (c'est une prédiction
                           linéaire), mais son interprétation habituelle — le
                           conduit vocal — n'a **aucun sens** ici : une plante
                           n'a pas de résonateur. Reste un bon estimateur
                           d'enveloppe spectrale et un détecteur de résonances.
Cepstre                    Valable. Sépare l'excitation de l'enveloppe, donc
                           détecte les périodicités cachées — utile pour trouver
                           un rythme circadien ou une modulation lente.
=========================  ====================================================

Aucune de ces représentations ne « décode » quoi que ce soit. Elles décrivent la
forme du signal, plus finement qu'une simple courbe. Le chapitre de déontologie
de l'ouvrage s'applique ici mot pour mot.

Tout est en NumPy pur : aucune dépendance supplémentaire n'est requise.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional, Tuple

import numpy as np

__all__ = [
    "SpectreInstantane", "spectre_instantane",
    "Scalogramme", "ondelettes_morlet",
    "MFCC", "mfcc",
    "LPC", "lpc",
    "Cepstre", "cepstre",
    "DESCRIPTEURS",
]


# ---------------------------------------------------------------------------
#  Utilitaires communs
# ---------------------------------------------------------------------------
def _fenetre(n: int, nom: str = "hann") -> np.ndarray:
    """Fenêtre d'apodisation. Hann par défaut : le meilleur compromis entre
    largeur du lobe principal et niveau des lobes secondaires pour un signal
    dont on ne connaît pas la structure à l'avance."""
    if n <= 1:
        return np.ones(max(n, 1))
    k = np.arange(n)
    if nom == "hamming":
        return 0.54 - 0.46 * np.cos(2 * np.pi * k / (n - 1))
    if nom == "blackman":
        return (0.42 - 0.5 * np.cos(2 * np.pi * k / (n - 1))
                + 0.08 * np.cos(4 * np.pi * k / (n - 1)))
    if nom == "rectangulaire":
        return np.ones(n)
    return 0.5 - 0.5 * np.cos(2 * np.pi * k / (n - 1))          # hann


def _preparer(x: np.ndarray, retirer_moyenne: bool = True) -> np.ndarray:
    """Met le signal en flottant, retire les valeurs non finies et, par défaut,
    la composante continue — qui écrase tout le reste sur un signal végétal où
    l'offset d'électrode vaut mille fois le signal."""
    x = np.asarray(x, dtype=float).ravel()
    if x.size == 0:
        return x
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    if retirer_moyenne:
        x = x - x.mean()
    return x


# ---------------------------------------------------------------------------
#  1. Domaine fréquentiel — spectre instantané par FFT
# ---------------------------------------------------------------------------
@dataclass
class SpectreInstantane:
    """Amplitude en fonction de la fréquence, sur une seule fenêtre."""
    frequences_hz: np.ndarray
    amplitude: np.ndarray                 # unité d'entrée (V), pas de densité
    amplitude_db: np.ndarray
    pic_hz: float
    pic_amplitude: float
    fenetre: str
    duree_s: float

    @property
    def resolution_hz(self) -> float:
        """Écart entre deux points du spectre : 1 / durée analysée."""
        return 1.0 / self.duree_s if self.duree_s > 0 else float("nan")


def spectre_instantane(x: np.ndarray, fs: float, fenetre: str = "hann",
                       zero_padding: int = 1) -> SpectreInstantane:
    """Spectre d'amplitude d'une fenêtre unique — le « domaine fréquentiel ».

    À distinguer de la densité spectrale de puissance calculée par la méthode de
    Welch dans :mod:`analysis` : celle-ci moyenne plusieurs fenêtres et lisse le
    bruit, celle-là montre l'instant présent, avec sa variance. Pour observer un
    phénomène qui change, c'est cette dernière qu'il faut.

    :param zero_padding: facteur d'allongement par des zéros. Il n'ajoute
        aucune information — la résolution reste 1/durée — mais interpole le
        tracé et rend la lecture d'un pic plus confortable.
    """
    x = _preparer(x)
    n = x.size
    if n < 8 or fs <= 0:
        vide = np.zeros(0)
        return SpectreInstantane(vide, vide, vide, float("nan"), 0.0, fenetre, 0.0)

    w = _fenetre(n, fenetre)
    xw = x * w
    # correction de gain cohérent : une fenêtre de Hann divise l'amplitude par 2
    gain = w.sum() / n
    nfft = int(2 ** math.ceil(math.log2(n * max(zero_padding, 1))))
    spec = np.fft.rfft(xw, n=nfft)
    freqs = np.fft.rfftfreq(nfft, d=1.0 / fs)

    amp = np.abs(spec) * 2.0 / (n * max(gain, 1e-12))
    if amp.size:
        amp[0] /= 2.0                      # la composante continue n'est pas doublée
    db = 20.0 * np.log10(np.maximum(amp, 1e-18))

    if amp.size > 1:
        i = int(np.argmax(amp[1:]) + 1)    # on ignore le continu pour le pic
        pic_hz, pic_amp = float(freqs[i]), float(amp[i])
    else:
        pic_hz, pic_amp = float("nan"), 0.0

    return SpectreInstantane(freqs, amp, db, pic_hz, pic_amp, fenetre, n / fs)


# ---------------------------------------------------------------------------
#  2. Ondelettes — transformée continue de Morlet
# ---------------------------------------------------------------------------
@dataclass
class Scalogramme:
    """Énergie en fonction du temps ET de la fréquence."""
    temps_s: np.ndarray
    frequences_hz: np.ndarray
    module: np.ndarray                    # (n_freq, n_temps)
    module_db: np.ndarray
    omega0: float
    cone_influence_s: np.ndarray          # durée aveugle à chaque échelle

    def ridge(self) -> np.ndarray:
        """Fréquence dominante à chaque instant — la « crête » du scalogramme."""
        if self.module.size == 0:
            return np.zeros(0)
        return self.frequences_hz[np.argmax(self.module, axis=0)]


def ondelettes_morlet(x: np.ndarray, fs: float,
                      f_min: Optional[float] = None,
                      f_max: Optional[float] = None,
                      n_echelles: int = 48,
                      omega0: float = 6.0,
                      decimation: int = 1) -> Scalogramme:
    """Transformée en ondelettes continue, ondelette de Morlet.

    C'est la représentation la mieux adaptée à un signal végétal, pour une
    raison de fond : **l'analyse de Fourier suppose la stationnarité**, que ce
    signal n'a jamais. Une bouffée d'activité de trois secondes dans une heure
    d'enregistrement disparaît dans une FFT globale ; l'ondelette la situe dans
    le temps et en donne l'étendue fréquentielle.

    L'ondelette de Morlet est une sinusoïde enveloppée d'une gaussienne. Son
    paramètre ``omega0`` règle le compromis temps/fréquence : 6 est la valeur
    usuelle, qui satisfait presque exactement la condition d'admissibilité tout
    en gardant une bonne localisation temporelle. L'augmenter affine la
    fréquence et brouille le temps ; le diminuer fait l'inverse.

    Le calcul se fait par produit dans le domaine de Fourier — O(N log N) par
    échelle —, seule méthode praticable sur des dizaines de milliers de points.

    :param decimation: sous-échantillonne le résultat en temps. Un scalogramme
        de 48 × 60 000 points ne s'affiche pas ; 48 × 1 200 se lit très bien.
    """
    x = _preparer(x)
    n = x.size
    if n < 32 or fs <= 0:
        v = np.zeros(0)
        return Scalogramme(v, v, np.zeros((0, 0)), np.zeros((0, 0)), omega0, v)

    duree = n / fs
    # Bornes par défaut : du plus lent qu'on peut voir (2 périodes dans la
    # fenêtre) au plus rapide que l'échantillonnage autorise (Nyquist / 2,5).
    f_min = float(f_min) if f_min else max(2.0 / duree, 1e-4)
    f_max = float(f_max) if f_max else fs / 2.5
    if f_max <= f_min:
        f_max = f_min * 8.0

    freqs = np.geomspace(f_min, f_max, max(int(n_echelles), 4))

    # Relation échelle ↔ fréquence pour Morlet.
    echelles = (omega0 + math.sqrt(2.0 + omega0 ** 2)) / (4.0 * np.pi * freqs)

    nfft = int(2 ** math.ceil(math.log2(n * 2)))       # bourrage : évite le repli circulaire
    X = np.fft.fft(x, n=nfft)
    omega = 2.0 * np.pi * np.fft.fftfreq(nfft, d=1.0 / fs)

    module = np.empty((freqs.size, n), dtype=float)
    for i, s in enumerate(echelles):
        # Ondelette mère dans le domaine de Fourier, normalisée en énergie.
        arg = s * omega - omega0
        psi = (np.pi ** -0.25) * np.sqrt(s * fs) * np.exp(-0.5 * arg ** 2)
        psi[omega <= 0] = 0.0                          # ondelette analytique
        module[i] = np.abs(np.fft.ifft(X * psi)[:n])

    # Cône d'influence : zone où le résultat est contaminé par les bords.
    coi = math.sqrt(2.0) * echelles

    if decimation > 1:
        module = module[:, ::int(decimation)]
        temps = np.arange(module.shape[1]) * (int(decimation) / fs)
    else:
        temps = np.arange(n) / fs

    db = 20.0 * np.log10(np.maximum(module, 1e-18))
    return Scalogramme(temps, freqs, module, db, omega0, coi)


# ---------------------------------------------------------------------------
#  3. MFCC — coefficients cepstraux sur échelle de Mel
# ---------------------------------------------------------------------------
def _hz_vers_mel(f: np.ndarray | float) -> np.ndarray | float:
    return 2595.0 * np.log10(1.0 + np.asarray(f, dtype=float) / 700.0)


def _mel_vers_hz(m: np.ndarray | float) -> np.ndarray | float:
    return 700.0 * (10.0 ** (np.asarray(m, dtype=float) / 2595.0) - 1.0)


def banc_de_mel(n_filtres: int, nfft: int, fs: float,
                f_min: float = 0.0, f_max: Optional[float] = None) -> np.ndarray:
    """Banc de filtres triangulaires régulièrement espacés en échelle de Mel.

    L'échelle de Mel est une courbe psychoacoustique : elle serre les filtres
    aux basses fréquences, où l'oreille discrimine bien, et les espace aux
    hautes. Transposée à notre bande, elle serre donc les filtres sous le hertz
    — ce qui, par un hasard heureux, est exactement là où se passe l'essentiel
    de l'activité végétale. Le résultat reste une compression arbitraire, mais
    une compression arbitraire bien placée.
    """
    f_max = float(f_max) if f_max else fs / 2.0
    n_filtres = max(int(n_filtres), 2)

    m = np.linspace(_hz_vers_mel(f_min), _hz_vers_mel(f_max), n_filtres + 2)
    hz = np.asarray(_mel_vers_hz(m), dtype=float)
    bins = np.floor((nfft + 1) * hz / fs).astype(int)
    bins = np.clip(bins, 0, nfft // 2)

    banc = np.zeros((n_filtres, nfft // 2 + 1))
    for i in range(n_filtres):
        g, c, d = bins[i], bins[i + 1], bins[i + 2]
        if c == g:
            c = min(g + 1, nfft // 2)
        if d == c:
            d = min(c + 1, nfft // 2)
        if c > g:
            banc[i, g:c] = (np.arange(g, c) - g) / (c - g)
        if d > c:
            banc[i, c:d] = (d - np.arange(c, d)) / (d - c)
    return banc


@dataclass
class MFCC:
    """Coefficients, plus le spectre de Mel dont ils sont issus."""
    coefficients: np.ndarray              # (n_trames, n_coef)
    temps_s: np.ndarray
    spectre_mel_db: np.ndarray            # (n_filtres, n_trames)
    frequences_mel_hz: np.ndarray
    delta: np.ndarray = field(default_factory=lambda: np.zeros((0, 0)))

    def moyenne(self) -> np.ndarray:
        if self.coefficients.size == 0:
            return np.zeros(0)
        return self.coefficients.mean(axis=0)


def mfcc(x: np.ndarray, fs: float, n_coef: int = 13, n_filtres: int = 26,
         fenetre_s: float = 8.0, recouvrement: float = 0.5,
         f_min: float = 0.0, f_max: Optional[float] = None,
         avec_delta: bool = True) -> MFCC:
    """Coefficients cepstraux sur échelle de Mel.

    La chaîne est la chaîne canonique : découpage en trames, fenêtre de Hamming,
    spectre de puissance, banc de Mel, logarithme, transformée en cosinus
    discrète. Seules les constantes changent — la trame vaut ici **huit
    secondes** au lieu de vingt-cinq millisecondes, parce que la stationnarité
    locale d'un signal végétal se mesure en secondes, non en millisecondes.

    Les coefficients d'ordre élevé décrivent les détails de l'enveloppe
    spectrale, les premiers sa forme générale. Le coefficient 0, qui n'est que
    l'énergie totale, est conservé : sur un signal végétal il porte une
    information réelle, contrairement à la parole où on le jette.

    À quoi cela sert ici : à **comparer des séquences**. Deux minutes
    d'enregistrement se résument en une poignée de vecteurs qu'on peut mettre en
    correspondance, regrouper ou classer. C'est le fondement du mode vocal, qui
    associe un mot à chaque région de cet espace.
    """
    x = _preparer(x)
    if x.size < 32 or fs <= 0:
        v = np.zeros(0)
        return MFCC(np.zeros((0, 0)), v, np.zeros((0, 0)), v)

    n_trame = max(int(fenetre_s * fs), 16)
    pas = max(int(n_trame * (1.0 - min(max(recouvrement, 0.0), 0.95))), 1)
    if x.size < n_trame:                                # trop court : une trame unique
        n_trame, pas = x.size, x.size

    nfft = int(2 ** math.ceil(math.log2(n_trame)))
    banc = banc_de_mel(n_filtres, nfft, fs, f_min, f_max)
    w = _fenetre(n_trame, "hamming")

    debuts = range(0, x.size - n_trame + 1, pas)
    coefs, mels, temps = [], [], []
    for d in debuts:
        trame = x[d:d + n_trame] * w
        puissance = (np.abs(np.fft.rfft(trame, n=nfft)) ** 2) / nfft
        energie_mel = banc @ puissance
        log_mel = np.log(np.maximum(energie_mel, 1e-20))
        coefs.append(_dct2(log_mel)[:n_coef])
        mels.append(10.0 * np.log10(np.maximum(energie_mel, 1e-20)))
        temps.append((d + n_trame / 2) / fs)

    C = np.array(coefs) if coefs else np.zeros((0, n_coef))
    M = np.array(mels).T if mels else np.zeros((n_filtres, 0))

    D = np.zeros((0, 0))
    if avec_delta and C.shape[0] >= 3:
        D = np.gradient(C, axis=0)                      # variation d'une trame à l'autre

    m_centres = np.linspace(_hz_vers_mel(f_min),
                            _hz_vers_mel(f_max if f_max else fs / 2.0),
                            n_filtres + 2)[1:-1]
    return MFCC(C, np.array(temps), M, np.asarray(_mel_vers_hz(m_centres)), D)


def _dct2(v: np.ndarray) -> np.ndarray:
    """Transformée en cosinus discrète de type II, normalisée en orthogonalité.

    Implémentée par une FFT sur le signal réfléchi : c'est exact, et cela évite
    d'exiger SciPy pour huit lignes de code.
    """
    n = v.size
    if n == 0:
        return v
    miroir = np.concatenate([v, v[::-1]])
    spec = np.fft.rfft(miroir)[:n]
    phase = np.exp(-1j * np.pi * np.arange(n) / (2 * n))
    out = np.real(spec * phase)
    out[0] *= 1.0 / math.sqrt(4 * n)
    if n > 1:
        out[1:] *= 1.0 / math.sqrt(2 * n)
    return out


# ---------------------------------------------------------------------------
#  4. LPC — codage prédictif linéaire
# ---------------------------------------------------------------------------
@dataclass
class LPC:
    """Coefficients de prédiction, enveloppe spectrale et résonances."""
    coefficients: np.ndarray              # a[1..p], convention x[n] ≈ −Σ a[k]·x[n−k]
    erreur_residuelle: float
    gain: float
    frequences_hz: np.ndarray
    enveloppe_db: np.ndarray
    formants_hz: np.ndarray               # résonances : pôles proches du cercle
    formants_largeur_hz: np.ndarray
    ordre: int

    @property
    def gain_prediction_db(self) -> float:
        """De combien la prédiction réduit l'énergie. Un signal parfaitement
        imprévisible donne 0 dB ; un signal très résonant, 20 dB et plus."""
        if self.erreur_residuelle <= 0:
            return float("inf")
        return 10.0 * math.log10(max(self.gain, 1e-30) / self.erreur_residuelle)


def lpc(x: np.ndarray, fs: float, ordre: Optional[int] = None,
        n_points: int = 512) -> LPC:
    """Prédiction linéaire par l'algorithme de Levinson-Durbin.

    Le principe : chercher les ``p`` coefficients qui prédisent le mieux chaque
    échantillon à partir des précédents. Ce qui reste — l'erreur de prédiction —
    est ce que le modèle n'explique pas.

    **Avertissement sur l'interprétation.** En traitement de la parole, les
    pôles du filtre obtenu s'interprètent comme les résonances du conduit vocal,
    et on les appelle formants. Ici, *il n'y a pas de conduit vocal* : une plante
    n'a aucun résonateur acoustique, et parler de formants végétaux serait une
    faute. Ce que les pôles décrivent réellement, ce sont les **résonances du
    système de mesure et du milieu** : la constante de temps de l'électrode, le
    filtrage de la carte, les oscillations lentes du potentiel. C'est utile — et
    c'est autre chose que ce que le nom suggère. Le mot « résonance » est donc
    employé ici de préférence à « formant ».

    L'ordre par défaut suit la règle usuelle ``2 + fs/1000`` transposée : deux
    pôles par résonance attendue, plus deux pour la pente générale.
    """
    x = _preparer(x)
    n = x.size
    if fs <= 0 or n < 16:
        v = np.zeros(0)
        return LPC(v, 0.0, 0.0, v, v, v, v, 0)

    p = int(ordre) if ordre else max(4, min(int(2 + fs / 25.0), 24))
    p = min(p, n - 2)

    w = _fenetre(n, "hamming")
    xw = x * w

    # autocorrélation par FFT (bien plus rapide qu'une double boucle)
    nfft = int(2 ** math.ceil(math.log2(2 * n)))
    S = np.abs(np.fft.rfft(xw, n=nfft)) ** 2
    r = np.fft.irfft(S)[:p + 1]
    if r[0] <= 0:
        v = np.zeros(0)
        return LPC(v, 0.0, 0.0, v, v, v, v, p)

    # --- Levinson-Durbin ---------------------------------------------------
    a = np.zeros(p + 1)
    a[0] = 1.0
    e = float(r[0])
    for i in range(1, p + 1):
        acc = r[i] + np.dot(a[1:i], r[i - 1:0:-1]) if i > 1 else r[i]
        k = -acc / e
        a_prec = a[1:i].copy()
        a[i] = k
        if i > 1:
            a[1:i] = a_prec + k * a_prec[::-1]
        e *= (1.0 - k * k)
        if e <= 0:                                   # instabilité numérique
            e = 1e-30
            break

    # --- enveloppe spectrale ------------------------------------------------
    freqs = np.linspace(0.0, fs / 2.0, max(int(n_points), 16))
    z = np.exp(-2j * np.pi * np.outer(freqs / fs, np.arange(p + 1)))
    H = math.sqrt(max(e, 1e-30)) / np.maximum(np.abs(z @ a), 1e-18)
    env_db = 20.0 * np.log10(np.maximum(H, 1e-18))

    # --- résonances : racines du polynôme, converties en fréquence ----------
    res_f, res_bw = [], []
    if p >= 2:
        racines = np.roots(a)
        racines = racines[np.imag(racines) > 0]
        for rac in racines:
            module = abs(rac)
            if not (0.0 < module < 1.0):
                continue
            f = float(np.angle(rac) * fs / (2 * np.pi))
            bw = float(-fs * math.log(max(module, 1e-12)) / np.pi)
            if 0.0 < f < fs / 2.0:
                res_f.append(f)
                res_bw.append(bw)
        ordre_tri = np.argsort(res_f)
        res_f = list(np.asarray(res_f)[ordre_tri])
        res_bw = list(np.asarray(res_bw)[ordre_tri])

    return LPC(a[1:], float(e), float(r[0]), freqs, env_db,
               np.asarray(res_f), np.asarray(res_bw), p)


# ---------------------------------------------------------------------------
#  5. Cepstre
# ---------------------------------------------------------------------------
@dataclass
class Cepstre:
    """Le spectre du logarithme du spectre — en « quéfrence », des secondes."""
    quefrence_s: np.ndarray
    cepstre: np.ndarray
    pic_quefrence_s: float
    pic_valeur: float
    periode_detectee_s: float
    frequence_detectee_hz: float


def cepstre(x: np.ndarray, fs: float, q_min_s: Optional[float] = None,
            q_max_s: Optional[float] = None) -> Cepstre:
    """Cepstre réel — l'outil qui sépare l'excitation de l'enveloppe.

    L'idée est un joli détour : le spectre d'un signal périodique est lui-même
    périodique, avec ses harmoniques régulièrement espacées. En prenant le
    logarithme du spectre puis sa transformée inverse, cette régularité devient
    un **pic unique**, situé à la période du signal. La variable obtenue n'est
    ni un temps ni une fréquence ; on l'appelle quéfrence, et elle se mesure en
    secondes.

    Sur un signal végétal, c'est ce qui permet de détecter une périodicité lente
    — un cycle jour/nuit, une modulation d'arrosage, un rythme d'une dizaine de
    minutes — que ni la FFT ni l'autocorrélation ne font ressortir aussi
    nettement lorsque le fond dérive.

    La plage de quéfrences explorée est bornée par défaut entre deux
    échantillons et le tiers de la durée : en deçà on lit du bruit, au-delà on
    n'a pas assez de répétitions pour conclure quoi que ce soit.
    """
    x = _preparer(x)
    n = x.size
    if n < 32 or fs <= 0:
        v = np.zeros(0)
        return Cepstre(v, v, float("nan"), 0.0, float("nan"), float("nan"))

    w = _fenetre(n, "hann")
    nfft = int(2 ** math.ceil(math.log2(2 * n)))
    spec = np.fft.rfft(x * w, n=nfft)
    log_spec = np.log(np.maximum(np.abs(spec), 1e-20))
    c = np.fft.irfft(log_spec)[: nfft // 2]
    q = np.arange(c.size) / fs

    q_min = float(q_min_s) if q_min_s else 2.0 / fs
    q_max = float(q_max_s) if q_max_s else (n / fs) / 3.0
    masque = (q >= q_min) & (q <= q_max)

    if not masque.any():
        return Cepstre(q, c, float("nan"), 0.0, float("nan"), float("nan"))

    idx = np.flatnonzero(masque)
    i = int(idx[np.argmax(c[idx])])
    pic_q = float(q[i])
    return Cepstre(q, c, pic_q, float(c[i]), pic_q,
                   (1.0 / pic_q) if pic_q > 0 else float("nan"))


# ---------------------------------------------------------------------------
#  Table des descripteurs — pour l'interface et la documentation
# ---------------------------------------------------------------------------
DESCRIPTEURS = {
    "temporel": (
        "Domaine temporel",
        "amplitude en fonction du temps — la forme d'onde brute",
        "La représentation de référence : rien n'y est calculé, donc rien n'y "
        "est perdu. Tout diagnostic commence ici."),
    "frequentiel": (
        "Domaine fréquentiel (FFT)",
        "amplitude en fonction de la fréquence — spectre instantané",
        "Montre les périodicités et le réseau à 50 Hz. Suppose le signal "
        "stationnaire sur la fenêtre analysée, ce qui est rarement vrai "
        "longtemps."),
    "ondelettes": (
        "Ondelettes (scalogramme)",
        "énergie en fonction du temps ET de la fréquence",
        "La mieux adaptée aux signaux non stationnaires : situe dans le temps "
        "ce que la FFT se contente de moyenner. Résolution multi-échelle."),
    "mfcc": (
        "MFCC",
        "coefficients cepstraux sur échelle de Mel",
        "Compresse le spectre en une poignée de nombres comparables entre eux. "
        "L'échelle de Mel modélise l'audition humaine, pas la plante : c'est un "
        "outil de comparaison, non une mesure physiologique."),
    "lpc": (
        "LPC (prédiction linéaire)",
        "enveloppe spectrale et résonances du système",
        "Modélise le signal comme la sortie d'un filtre. Les résonances "
        "trouvées sont celles de l'électrode et du milieu — une plante n'a pas "
        "de conduit vocal."),
    "cepstre": (
        "Cepstre",
        "spectre du logarithme du spectre — l'abscisse est une quéfrence, "
        "anagramme de « fréquence », qui se mesure en secondes",
        "Sépare l'excitation de l'enveloppe et révèle les périodicités lentes "
        "qu'une dérive de fond masque."),
}
