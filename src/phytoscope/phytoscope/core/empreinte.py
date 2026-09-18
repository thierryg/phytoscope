# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/empreinte.py
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

"""Empreinte de mesure : reconnaître un montage, pas une âme.

La question posée est séduisante : puisqu'une plante a, dit-on, une « signature
vibratoire », pourrait-on identifier celle qu'on est en train de mesurer ?

Il faut répondre en deux temps, et le premier temps est un refus.

Ce que ce module **ne fait pas**
--------------------------------

Il ne reconnaît pas une plante. Ni son espèce, ni son individu, ni son état, ni
rien qui lui appartienne en propre. Un signal électrique de surface n'est pas
une empreinte digitale : il dépend autant de l'électrode, du gel, de l'humidité
du substrat, de la température de la pièce et de la longueur du câble que du
végétal. Deux mesures du même ficus à deux jours d'intervalle diffèrent
davantage que deux mesures de deux ficus voisins le même après-midi. Prétendre
le contraire serait vendre du merveilleux avec des chiffres.

Ce que ce module **fait**
-------------------------

Il calcule l'empreinte du **montage** : une poignée de descripteurs stables,
mesurables et interprétables, qui caractérisent l'ensemble
`plante + électrodes + substrat + câble + carte` tel qu'il est à cet instant.

============================  ==============================================
Descripteur                   Ce qu'il capture surtout
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
  ressemblance bien avant qu'on ne le voie à l'écran ;
* **comparer honnêtement** deux séances avant de les interpréter.

La ressemblance est une **distance**, jamais une identité. Elle se lit comme un
indice de confiance, et le logiciel dit toujours sur quels descripteurs elle se
fonde, avec leurs valeurs. Aucun code d'identification n'est produit : un code
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

__all__ = ["Empreinte", "calculer", "ressembler", "qualifier", "Registre",
           "DESCRIPTEURS", "SEUILS"]

#  Comment lire une ressemblance. Ces bornes sont des **conventions de
#  lecture**, pas des résultats : elles disent à partir de quand on peut parler,
#  et elles sont écrites ici pour qu'on puisse les contester.
SEUILS = ((0.92, "le même montage, vraisemblablement"),
          (0.80, "un montage proche — le contact a pu changer"),
          (0.65, "une parenté possible, rien de plus"),
          (0.00, "un autre montage"))

#  (clé, libellé, unité, poids dans la comparaison, échelle logarithmique ?)
DESCRIPTEURS: Tuple[Tuple[str, str, str, float, bool], ...] = (
    ("bruit_uv",        "Bruit efficace",             "µV",      1.4, True),
    ("pente_spectrale", "Pente spectrale",            "dB/déc.", 1.0, False),
    ("centroide_hz",    "Centre de gravité spectral", "Hz",      1.0, True),
    ("correlation_s",   "Temps de corrélation",       "s",       0.8, True),
    ("derive_uv_min",   "Dérive",                     "µV/min",  0.6, False),
    ("evenements_min",  "Événements",                 "/min",    0.8, False),
    ("fano",            "Facteur de Fano",            "",        0.5, False),
    ("aplatissement",   "Aplatissement",              "",        0.5, False),
)


@dataclass
class Empreinte:
    """Les descripteurs d'un montage, à un instant donné."""
    nom: str = ""
    horodatage: str = ""
    duree_s: float = 0.0
    fs: float = 250.0
    bruit_uv: float = 0.0
    pente_spectrale: float = 0.0
    centroide_hz: float = 0.0
    correlation_s: float = 0.0
    derive_uv_min: float = 0.0
    evenements_min: float = 0.0
    fano: float = 0.0
    aplatissement: float = 0.0
    metadonnees: Dict[str, Any] = field(default_factory=dict)

    def valeurs(self) -> Dict[str, float]:
        return {cle: float(getattr(self, cle, 0.0)) for cle, *_ in DESCRIPTEURS}

    def lignes(self) -> List[Tuple[str, str]]:
        """(libellé, valeur formatée) — ce que l'interface affiche."""
        out = []
        for cle, libelle, unite, _, _ in DESCRIPTEURS:
            v = float(getattr(self, cle, 0.0))
            texte = f"{v:.3g}" + (f" {unite}" if unite else "")
            out.append((libelle, texte))
        return out

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Empreinte":
        connus = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in (d or {}).items() if k in connus})


# ---------------------------------------------------------------------------
#  Calcul
# ---------------------------------------------------------------------------
def calculer(signal: np.ndarray, fs: float, evenements_s: Optional[List[float]] = None,
             nom: str = "", metadonnees: Optional[Dict[str, Any]] = None) -> Empreinte:
    """Empreinte d'une fenêtre de signal — au moins trente secondes.

    Moins de trente secondes ne permet ni de voir une dérive, ni d'avoir assez
    d'événements pour que leur statistique veuille dire quelque chose : la
    fonction calcule quand même, mais l'empreinte obtenue ne se compare à rien.
    """
    x = np.asarray(signal, dtype=np.float64).ravel()
    e = Empreinte(nom=nom, fs=float(fs),
                  horodatage=datetime.now(timezone.utc).isoformat(),
                  metadonnees=dict(metadonnees or {}))
    if x.size < 64 or fs <= 0:
        return e
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    e.duree_s = x.size / fs

    centre = x - x.mean()
    e.bruit_uv = float(np.std(centre)) * 1e6

    #  Spectre : pente en 1/f^α et centre de gravité, hors continu et réseau.
    sp = spectre(centre, fs, nperseg=min(2048, max(256, x.size // 4)))
    f, d = sp.freqs, sp.psd_v2_hz
    garde = (f > 0.02) & (f < fs / 2.5)
    if garde.sum() > 8:
        lf, ld = np.log10(f[garde]), np.log10(np.maximum(d[garde], 1e-30))
        pente = np.polyfit(lf, ld, 1)[0]
        e.pente_spectrale = float(pente * 10.0)        # dB par décade
        poids = d[garde]
        somme = float(poids.sum())
        if somme > 0:
            e.centroide_hz = float((f[garde] * poids).sum() / somme)

    #  Inertie : temps au bout duquel l'autocorrélation tombe sous 1/e.
    retards, correl = autocorrelation(centre, fs, max_lag_s=min(30.0, e.duree_s / 3))
    sous = np.flatnonzero(correl < math.exp(-1.0))
    e.correlation_s = float(retards[sous[0]]) if sous.size else float(retards[-1])

    d_res = derive(centre, fs)
    e.derive_uv_min = float(d_res.pente_uv_par_min)

    if evenements_s:
        st = statistiques_evenements(evenements_s, duree_s=e.duree_s)
        e.evenements_min = float(st.taux_par_min)
        e.fano = float(st.fano)
    ecart = float(np.std(centre))
    if ecart > 0:
        e.aplatissement = float(np.mean(((centre) / ecart) ** 4) - 3.0)
    return e


# ---------------------------------------------------------------------------
#  Comparaison
# ---------------------------------------------------------------------------
def ressembler(a: Empreinte, b: Empreinte) -> Tuple[float, List[Tuple[str, float, float, float]]]:
    """Ressemblance de deux empreintes, entre 0 et 1, avec son détail.

    La distance est une moyenne pondérée d'écarts **relatifs** — un bruit de
    2 µV contre 3 µV compte autant qu'une dérive de 20 µV/min contre 30 : ce
    sont des ordres de grandeur qu'on compare, pas des valeurs absolues. Les
    grandeurs qui s'étalent sur des décades sont comparées en logarithme.

    Retourne (ressemblance, détail), où chaque ligne du détail donne
    (libellé, valeur A, valeur B, écart relatif).
    """
    total, poids_total = 0.0, 0.0
    detail: List[Tuple[str, float, float, float]] = []
    for cle, libelle, _unite, poids, log in DESCRIPTEURS:
        va, vb = float(getattr(a, cle, 0.0)), float(getattr(b, cle, 0.0))
        if log:
            ea = math.log10(max(abs(va), 1e-9))
            eb = math.log10(max(abs(vb), 1e-9))
            ecart = abs(ea - eb) / 2.0             # deux décades = écart total
        else:
            echelle = max(abs(va), abs(vb), 1e-9)
            ecart = abs(va - vb) / (2.0 * echelle)
        ecart = min(max(ecart, 0.0), 1.0)
        detail.append((libelle, va, vb, ecart))
        total += ecart * poids
        poids_total += poids
    distance = total / poids_total if poids_total else 1.0
    return max(0.0, 1.0 - distance), detail


def qualifier(ressemblance: float) -> str:
    """Traduit une ressemblance en une phrase qu'on a le droit de prononcer.

    Un pourcentage seul invite à conclure ; une phrase qui dit « vraisemblable »
    rappelle qu'on lit un indice, pas une identité.
    """
    for borne, phrase in SEUILS:
        if ressemblance >= borne:
            return phrase
    return SEUILS[-1][1]


# ---------------------------------------------------------------------------
#  Registre : les montages connus
# ---------------------------------------------------------------------------
class Registre:
    """Les empreintes enregistrées, dans un simple fichier JSON.

    On y range les montages qu'on veut pouvoir reconnaître — « ficus du salon,
    pastille sous la troisième feuille, inox à cinq centimètres ». Le fichier
    est lisible et modifiable : il n'y a rien à cacher dans une liste de
    mesures.
    """

    def __init__(self, chemin: str):
        self.chemin = chemin
        self.empreintes: List[Empreinte] = []
        self.charger()

    def charger(self) -> None:
        self.empreintes = []
        if not os.path.exists(self.chemin):
            return
        try:
            with open(self.chemin, encoding="utf-8") as f:
                donnees = json.load(f)
        except (OSError, ValueError):
            return
        for d in donnees.get("empreintes", []):
            self.empreintes.append(Empreinte.from_dict(d))

    def enregistrer(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.chemin)), exist_ok=True)
        with open(self.chemin, "w", encoding="utf-8") as f:
            json.dump({"type": "registre-empreintes-phytoscope", "version": 1,
                       "empreintes": [e.to_dict() for e in self.empreintes]},
                      f, ensure_ascii=False, indent=2)

    def ajouter(self, empreinte: Empreinte) -> None:
        self.empreintes = [e for e in self.empreintes if e.nom != empreinte.nom]
        self.empreintes.append(empreinte)
        self.enregistrer()

    def retirer(self, nom: str) -> None:
        self.empreintes = [e for e in self.empreintes if e.nom != nom]
        self.enregistrer()

    def reconnaitre(self, empreinte: Empreinte) -> List[Tuple[Empreinte, float]]:
        """Les montages connus, du plus ressemblant au moins ressemblant."""
        sortie = [(e, ressembler(empreinte, e)[0]) for e in self.empreintes]
        sortie.sort(key=lambda c: c[1], reverse=True)
        return sortie
