# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/fingerprint.py
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

"""Fingerprint de mesure : reconnaître un montage, pas une âme.

La question posée est séduisante : puisqu'une plante a, dit-on, une « signature
vibratoire », pourrait-on identifier celle qu'on est en train de measure ?

Il faut répondre en deux temps, et le premier temps est un refus.

Ce que ce module **ne fait pas**
--------------------------------

Il ne reconnaît pas une plante. Ni son espèce, ni son individu, ni son état, ni
rien qui lui appartienne en propre. Un signal électrique de surface n'est pas
une fingerprint digitale : il dépend autant de l'électrode, du gel, de l'humidité
du substrat, de la température de la pièce et de la longueur du câble que du
végétal. Deux mesures du même ficus à deux jours d'intervalle diffèrent
davantage que deux mesures de deux ficus voisins le même après-midi. Prétendre
le contraire serait vendre du merveilleux avec des chiffres.

Ce que ce module **fait**
-------------------------

Il calcule l'fingerprint du **montage** : une poignée de descripteurs stables,
mesurables et interprétables, qui caractérisent l'ensemble
`plante + électrodes + substrat + câble + carte` tel qu'il est à cet instant.

============================  ==============================================
Descriptor                   Ce qu'il capture surtout
============================  ==============================================
bruit efficace                la qualité du contact et le blindage
pente spectrale (1/f^α)       la nature du milieu et de l'électrode
centre de gravité spectral    la bande où vit l'activité
temps de corrélation          l'inertie du système mesuré
dérive                        l'électrode qui se stabilise, l'humidité
taux d'événements             l'activité apparente, au seuil choisi
facteur de Fano               le groupement des événements dans le temps
aplatissement                 la forme de la distribution des amplitudes
============================  ==============================================

À quoi cela sert, concrètement :

* **retrouver un montage** — « ceci ressemble à la séance d'hier sur le ficus,
  à 86 % » — et donc s'apercevoir qu'il a changé ;
* **détecter une dégradation** : le contact qui sèche fait chuter la
  resemblance bien avant qu'on ne le voie à l'écran ;
* **comparer honnêtement** deux séances avant de les interpréter.

La resemblance est une **distance**, jamais une identité. Elle se lit comme un
indice de confiance, et le logiciel dit toujours sur quels descripteurs elle se
fonde, avec leurs values. Aucun code d'identification n'est produit : un code
laisserait croire à une exactitude qui n'existe pas.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .analysis import autocorrelation, derive, spectre, statistiques_evenements

__all__ = ["Fingerprint", "compute", "resemble", "qualify", "Registry",
           "DESCRIPTORS", "THRESHOLDS"]

#  Comment read une resemblance. Ces bornes sont des **conventions de
#  lecture**, pas des résultats : elles disent à partir de quand on peut parler,
#  et elles sont écrites ici pour qu'on puisse les contester.
THRESHOLDS = ((0.92, "the same setup, most likely"),
          (0.80, "a close setup — the contact may have changed"),
          (0.65, "a possible kinship, nothing more"),
          (0.00, "a different setup"))

#  (clé, libellé, unité, poids dans la comparaison, échelle logarithmique ?)
DESCRIPTORS: Tuple[Tuple[str, str, str, float, bool], ...] = (
    ("bruit_uv",        "RMS noise",             "µV",      1.4, True),
    ("pente_spectrale", "Spectral slope",            "dB/déc.", 1.0, False),
    ("centroide_hz",    "Spectral centroid", "Hz",      1.0, True),
    ("correlation_s",   "Correlation time",       "s",       0.8, True),
    ("derive_uv_min",   "Drift",                     "µV/min",  0.6, False),
    ("evenements_min",  "Events",                 "/min",    0.8, False),
    ("fano",            "Fano factor",            "",        0.5, False),
    ("aplatissement",   "Kurtosis",              "",        0.5, False),
)


@dataclass
class Fingerprint:
    """Les descripteurs d'un montage, à un instant donné."""
    name: str = ""
    horodatage: str = ""
    duration_s: float = 0.0
    fs: float = 250.0
    bruit_uv: float = 0.0
    pente_spectrale: float = 0.0
    centroide_hz: float = 0.0
    correlation_s: float = 0.0
    derive_uv_min: float = 0.0
    evenements_min: float = 0.0
    fano: float = 0.0
    aplatissement: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def values(self) -> Dict[str, float]:
        return {key: float(getattr(self, key, 0.0)) for key, *_ in DESCRIPTORS}

    def rows(self) -> List[Tuple[str, str]]:
        """(libellé, value formatée) — ce que l'interface affiche."""
        out = []
        for key, label, unite, _, _ in DESCRIPTORS:
            v = float(getattr(self, key, 0.0))
            text = f"{v:.3g}" + (f" {unite}" if unite else "")
            out.append((label, text))
        return out

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Fingerprint":
        connus = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in (d or {}).items() if k in connus})


# ---------------------------------------------------------------------------
#  Calcul
# ---------------------------------------------------------------------------
def compute(signal: np.ndarray, fs: float, event_times_s: Optional[List[float]] = None,
             name: str = "", metadata: Optional[Dict[str, Any]] = None) -> Fingerprint:
    """Fingerprint d'une fenêtre de signal — au moins trente seconds.

    Moins de trente seconds ne permet ni de voir une dérive, ni d'avoir assez
    d'événements pour que leur statistique veuille dire quelque chose : la
    fonction calcule quand même, mais l'fingerprint obtenue ne se compare à rien.
    """
    x = np.asarray(signal, dtype=np.float64).ravel()
    e = Fingerprint(name=name, fs=float(fs),
                  horodatage=datetime.now(timezone.utc).isoformat(),
                  metadata=dict(metadata or {}))
    if x.size < 64 or fs <= 0:
        return e
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    e.duration_s = x.size / fs

    centre = x - x.mean()
    e.bruit_uv = float(np.std(centre)) * 1e6

    #  Spectre : pente en 1/f^α et centre de gravité, hors continu et réseau.
    sp = spectre(centre, fs, nperseg=min(2048, max(256, x.size // 4)))
    f, d = sp.freqs, sp.psd_v2_hz
    kept = (f > 0.02) & (f < fs / 2.5)
    if kept.sum() > 8:
        lf, ld = np.log10(f[kept]), np.log10(np.maximum(d[kept], 1e-30))
        pente = np.polyfit(lf, ld, 1)[0]
        e.pente_spectrale = float(pente * 10.0)        # dB par décade
        poids = d[kept]
        somme = float(poids.sum())
        if somme > 0:
            e.centroide_hz = float((f[kept] * poids).sum() / somme)

    #  Inertie : temps au bout duquel l'autocorrélation tombe sous 1/e.
    retards, correl = autocorrelation(centre, fs, max_lag_s=min(30.0, e.duration_s / 3))
    sous = np.flatnonzero(correl < math.exp(-1.0))
    e.correlation_s = float(retards[sous[0]]) if sous.size else float(retards[-1])

    d_res = derive(centre, fs)
    e.derive_uv_min = float(d_res.pente_uv_par_min)

    if event_times_s:
        st = statistiques_evenements(event_times_s,
                                     duree_s=e.duration_s)
        e.evenements_min = float(st.taux_par_min)
        e.fano = float(st.fano)
    ecart = float(np.std(centre))
    if ecart > 0:
        e.aplatissement = float(np.mean(((centre) / ecart) ** 4) - 3.0)
    return e


# ---------------------------------------------------------------------------
#  Comparaison
# ---------------------------------------------------------------------------
def resemble(a: Fingerprint, b: Fingerprint) -> Tuple[float, List[Tuple[str, float, float, float]]]:
    """Ressemblance de deux empreintes, entre 0 et 1, avec son détail.

    La distance est une moyenne pondérée d'écarts **relatifs** — un bruit de
    2 µV contre 3 µV compte autant qu'une dérive de 20 µV/min contre 30 : ce
    sont des ordres de grandeur qu'on compare, pas des values absolues. Les
    grandeurs qui s'étalent sur des décades sont comparées en logarithme.

    Retourne (resemblance, détail), où chaque ligne du détail donne
    (libellé, value A, value B, écart relatif).
    """
    total, poids_total = 0.0, 0.0
    detail: List[Tuple[str, float, float, float]] = []
    for key, label, _unite, poids, log in DESCRIPTORS:
        va, vb = float(getattr(a, key, 0.0)), float(getattr(b, key, 0.0))
        if log:
            ea = math.log10(max(abs(va), 1e-9))
            eb = math.log10(max(abs(vb), 1e-9))
            ecart = abs(ea - eb) / 2.0             # deux décades = écart total
        else:
            echelle = max(abs(va), abs(vb), 1e-9)
            ecart = abs(va - vb) / (2.0 * echelle)
        ecart = min(max(ecart, 0.0), 1.0)
        detail.append((label, va, vb, ecart))
        total += ecart * poids
        poids_total += poids
    distance = total / poids_total if poids_total else 1.0
    return max(0.0, 1.0 - distance), detail


def qualify(resemblance: float) -> str:
    """Traduit une resemblance en une phrase qu'on a le droit de prononcer.

    Un pourcentage seul invite à conclure ; une phrase qui dit « vraisemblable »
    rappelle qu'on lit un indice, pas une identité.
    """
    for borne, phrase in THRESHOLDS:
        if resemblance >= borne:
            return phrase
    return THRESHOLDS[-1][1]


# ---------------------------------------------------------------------------
#  Registry : les montages connus
# ---------------------------------------------------------------------------
class Registry:
    """Les empreintes enregistrées, dans un simple file_path JSON.

    On y range les montages qu'on veut pouvoir reconnaître — « ficus du salon,
    pastille sous la troisième feuille, inox à cinq centimètres ». Le file_path
    est lisible et modifiable : il n'y a rien à cacher dans une entries de
    mesures.
    """

    def __init__(self, path: str):
        self.path = path
        self.empreintes: List[Fingerprint] = []
        self.load()

    def load(self) -> None:
        self.empreintes = []
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                donnees = json.load(f)
        except (OSError, ValueError):
            return
        for d in donnees.get("empreintes", []):
            self.empreintes.append(Fingerprint.from_dict(d))

    def save(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump({"type": "registre-empreintes-phytoscope", "version": 1,
                       "empreintes": [e.to_dict() for e in self.empreintes]},
                      f, ensure_ascii=False, indent=2)

    def add(self, fingerprint: Fingerprint) -> None:
        self.empreintes = [e for e in self.empreintes if e.name != fingerprint.name]
        self.empreintes.append(fingerprint)
        self.save()

    def remove(self, name: str) -> None:
        self.empreintes = [e for e in self.empreintes if e.name != name]
        self.save()

    def recognise(self, fingerprint: Fingerprint) -> List[Tuple[Fingerprint, float]]:
        """Les montages connus, du plus ressemblant au moins ressemblant."""
        sortie = [(e, resemble(fingerprint, e)[0]) for e in self.empreintes]
        sortie.sort(key=lambda c: c[1], reverse=True)
        return sortie
