# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/quantities.py
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

"""Grandeurs scientifiques — ce qu'on peut dire du signal en chiffres.

L'onglet Multimètre affiche six nombres bien visibles : la tension, le bruit, la
crête à crête, la dérive, la ligne de base, le compte d'événements. Ils suffisent
pour conduire une séance. Ils ne suffisent pas pour **qualifier une mesure**, et
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
activité comme du bruit, et le majorant n'aurait plus aucun sens.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .analysis import (allan_deviation, spectre, statistiques_evenements,
                       temps_de_correlation, test_normalite)

__all__ = ["Grandeur", "Grandeurs", "mesurer", "inventaire",
           "BOLTZMANN", "TEMPERATURE_K"]

BOLTZMANN = 1.380649e-23          # J/K, valeur exacte du SI depuis 2019
TEMPERATURE_K = 293.15            # 20 °C — la température d'une pièce, faute de sonde


@dataclass
class Grandeur:
    """Une grandeur mesurée : sa valeur, son unité, et ce qu'elle raconte.

    ``libelle`` et ``sens`` sont des GABARITS, jamais des phrases déjà
    composées : « Écart d'Allan à {tau} s » et non « Écart d'Allan à 1 s ».
    C'est ce qui permet de les traduire — une phrase où le nombre est déjà
    incrusté ne peut pas entrer dans un catalogue. L'affichage compose avec
    ``params`` après traduction.
    """
    cle: str
    libelle: str
    valeur: float
    texte: str                    # la valeur mise en forme, unité comprise
    sens: str                     # ce que ce nombre dit — en une phrase
    alerte: bool = False          # vrai si la valeur mérite qu'on s'y arrête
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Grandeurs:
    """L'ensemble des grandeurs calculées sur une fenêtre de signal."""
    duree_s: float = 0.0
    fs: float = 250.0
    liste: List[Grandeur] = field(default_factory=list)

    def __iter__(self):
        return iter(self.liste)

    def __len__(self) -> int:
        return len(self.liste)

    def get(self, cle: str) -> Optional[Grandeur]:
        for g in self.liste:
            if g.cle == cle:
                return g
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {g.cle: g.valeur for g in self.liste}


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
def mesurer(x: np.ndarray, fs: float, pleine_echelle_v: float = 2.5,
            reseau_hz: float = 50.0, evenements_s: Optional[Sequence[float]] = None,
            seuil_sigma: float = 3.5,
            bande_thermique: Tuple[float, float] = (10.0, 40.0)) -> Grandeurs:
    """Toutes les grandeurs qu'on peut tirer d'une fenêtre de signal.

    :param pleine_echelle_v: pour la marge de saturation et les bits effectifs.
    :param bande_thermique: bande où l'on suppose que la plante ne produit rien,
        et où l'on lit donc le bruit propre de la chaîne.
    """
    g = Grandeurs(fs=float(fs))
    x = np.asarray(x, dtype=np.float64).ravel()
    if x.size < 64 or fs <= 0:
        return g
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    g.duree_s = x.size / fs
    centre = x - float(np.mean(x))
    rms = float(np.sqrt(np.mean(centre ** 2)))
    crete = float(np.max(np.abs(centre)))

    ajouter = g.liste.append
    sp = spectre(centre, fs, nperseg=int(min(8192, max(256, x.size // 4))))

    # --- 1. le plancher de bruit, en densité --------------------------------
    f1, f2 = bande_thermique
    f2 = min(f2, fs / 2.5)
    plancher = sp.plancher(f1, f2) if f2 > f1 else 0.0
    ajouter(Grandeur(
        "plancher", "Densité de bruit", plancher,
        f"{plancher * 1e9:.1f} nV/√Hz" if plancher > 0 else "—",
        "Mesurée entre {f1} et {f2} Hz, où la plante ne produit plus rien. "
        "C'est le bruit propre de la chaîne : électrode, câble, amplificateur.",
        params={"f1": f"{f1:g}", "f2": f"{f2:g}"}))

    # --- 2. la résistance équivalente (majorant) ----------------------------
    r_eq = (plancher ** 2) / (4.0 * BOLTZMANN * TEMPERATURE_K) if plancher > 0 else 0.0
    ajouter(Grandeur(
        "resistance", "Résistance équivalente", r_eq, _ohms(r_eq),
        "Déduite du bruit thermique (Johnson-Nyquist) à 20 °C : R = Sᵥ / 4kT. "
        "C'est un MAJORANT — le bruit de l'amplificateur et ce que le montage "
        "capte s'y ajoutent —, mais il grimpe d'une décade quand un contact "
        "sèche : c'est là qu'il est précieux.",
        alerte=r_eq > 5e6))

    # --- 3. le bruit intégré dans la bande utile ----------------------------
    bruit_bande = sp.bruit_dans_bande(0.01, min(10.0, fs / 3))
    ajouter(Grandeur(
        "bruit_bande", "Bruit dans 0,01–10 Hz", bruit_bande,
        f"{bruit_bande * 1e6:.2f} µV RMS" if bruit_bande > 0 else "—",
        "Le bruit intégré là où vit l'activité végétale. C'est lui qu'il faut "
        "comparer à l'amplitude des événements cherchés, pas le bruit total.",
        alerte=bruit_bande * 1e6 > 30.0))

    # --- 4. le réseau ---------------------------------------------------------
    if reseau_hz and fs > 2.5 * reseau_hz:
        _, amp = sp.pic(reseau_hz, 1.0)
        au_dessus = (20 * math.log10(max(amp, 1e-30) / plancher)
                     if plancher > 0 else 0.0)
        ajouter(Grandeur(
            "reseau", "Résidu à {f} Hz, au-dessus du plancher", au_dessus,
            f"{au_dessus:+.1f} dB",
            "Ce que le montage capte du secteur. Au-delà de 20 dB, c'est le "
            "blindage et la garde qu'il faut revoir — pas le réjecteur, qui "
            "masque le problème sans le résoudre.",
            alerte=au_dessus > 20.0, params={"f": f"{reseau_hz:g}"}))

    # --- 5. facteur de crête -------------------------------------------------
    facteur = crete / rms if rms > 0 else 0.0
    ajouter(Grandeur(
        "crete", "Facteur de crête", facteur, f"{facteur:.1f}",
        "Rapport de la crête à la valeur efficace. Autour de 3 à 4 pour du "
        "bruit gaussien ; bien plus quand des événements francs se détachent, "
        "ce qui est bon signe.",
        alerte=facteur > 12.0))

    # --- 6. pente spectrale ---------------------------------------------------
    garde = (sp.freqs > 0.02) & (sp.freqs < fs / 2.5)
    pente = 0.0
    if garde.sum() > 8:
        lf = np.log10(sp.freqs[garde])
        ld = np.log10(np.maximum(sp.psd_v2_hz[garde], 1e-30))
        pente = float(np.polyfit(lf, ld, 1)[0]) * 10.0
    ajouter(Grandeur(
        "pente", "Pente spectrale", pente, f"{pente:+.1f} dB/dec",
        "−10 dB par décade est la signature d'un bruit en 1/f, celle des "
        "électrodes et des milieux vivants. Une pente plate signale un bruit "
        "blanc dominant — souvent l'électronique, pas la plante."))

    # --- 7. stabilité : écart d'Allan ----------------------------------------
    al = allan_deviation(centre, fs)
    for cible, cle in ((1.0, "allan1"), (10.0, "allan10")):
        if al.taus.size and cible <= al.taus[-1]:
            i = int(np.argmin(np.abs(al.taus - cible)))
            valeur = float(al.deviations[i])
            ajouter(Grandeur(
                cle, "Écart d'Allan à {tau} s", valeur,
                f"{valeur * 1e6:.3f} µV",
                "Stabilité empruntée à la métrologie du temps : contrairement "
                "à l'écart-type, il distingue le bruit — qui s'améliore en "
                "moyennant — de la dérive, qui empire.",
                params={"tau": f"{cible:g}"}))
    if al.tau_optimal > 0:
        ajouter(Grandeur(
            "tau_optimal", "Intégration optimale", al.tau_optimal,
            f"{_secondes(al.tau_optimal)} → {al.minimum * 1e6:.3f} µV",
            "La durée de moyennage la plus favorable. Au-delà, moyenner plus "
            "longtemps DÉGRADE la mesure : la dérive l'emporte sur le bruit. "
            "Régime observé : {regime}.",
            params={"regime": al.regime or "indéterminé"}))

    # --- 8. temps de corrélation ---------------------------------------------
    tau_c = temps_de_correlation(centre, fs)
    ajouter(Grandeur(
        "correlation", "Temps de corrélation", tau_c, _secondes(tau_c),
        "Durée au bout de laquelle le signal ne se ressemble plus. Elle donne "
        "l'inertie du système mesuré, et la durée minimale d'une fenêtre "
        "d'analyse qui ait un sens."))

    # --- 9. normalité ---------------------------------------------------------
    p = test_normalite(centre)
    ajouter(Grandeur(
        "normalite", "Normalité (d'Agostino-Pearson)", p, f"p = {p:.3f}",
        "Au-dessus de 0,05, la distribution est compatible avec une loi "
        "normale et un seuil exprimé en écarts-types a un sens. En dessous, "
        "ce seuil devient discutable — et c'est souvent bon signe : cela veut "
        "dire qu'il se passe quelque chose.",
        alerte=p <= 0.05))

    # --- 10. bits effectifs ---------------------------------------------------
    if rms > 0 and pleine_echelle_v > 0:
        bits = math.log2(pleine_echelle_v * 2.0 / (rms * math.sqrt(12.0)))
        ajouter(Grandeur(
            "bits", "Résolution effective", bits, f"{bits:.1f} bits",
            "Ce que la chaîne offre réellement, bruit compris, sur la pleine "
            "échelle du convertisseur — toujours moins que ses 24 bits "
            "nominaux."))

    # --- 11. marge avant saturation ------------------------------------------
    if pleine_echelle_v > 0:
        marge = 100.0 * (1.0 - min(crete / pleine_echelle_v, 1.0))
        ajouter(Grandeur(
            "marge", "Marge avant saturation", marge, f"{marge:.1f} %",
            "Ce qu'il reste avant que le convertisseur ne bute. En dessous de "
            "10 %, un événement franc sera écrêté, et un écrêtage ne se "
            "rattrape pas après coup.",
            alerte=marge < 10.0))

    # --- 12. statistique des événements --------------------------------------
    if evenements_s:
        st = statistiques_evenements(evenements_s, duree_s=g.duree_s)
        ajouter(Grandeur(
            "evenements", "Taux d'événements", st.taux_par_min,
            f"{st.taux_par_min:.2f} /min",
            "Au seuil de {sigma} σ en vigueur. Le taux dépend autant du seuil "
            "que de la plante : le changer change le taux.",
            params={"sigma": f"{seuil_sigma:g}"}))
        #  En dessous d'une dizaine d'événements, Fano et CV sont du bruit
        #  déguisé en chiffre : on affiche le compte, pas une statistique à
        #  laquelle on n'a pas droit.
        assez = st.n >= 10
        ajouter(Grandeur(
            "fano", "Facteur de Fano", st.fano if assez else 0.0,
            f"{st.fano:.2f}" if assez else f"— (n = {st.n})",
            "Variance divisée par moyenne du comptage. Vaut 1 pour un "
            "processus purement aléatoire ; en dessous, les événements sont "
            "réguliers ; au-dessus, ils arrivent par bouffées. Il en faut une "
            "dizaine pour que ce nombre veuille dire quelque chose."))
        if assez:
            ajouter(Grandeur(
                "cv", "Régularité (CV des intervalles)", st.cv, f"{st.cv:.2f}",
                "Coefficient de variation des intervalles. En dessous de 0,6 "
                "les événements sont trop réguliers pour être végétaux — "
                "cherchez plutôt une pompe, une ventilation ou un arrosage "
                "automatique. Au-delà de 1,4, ils arrivent par bouffées, ce "
                "qui est le comportement attendu d'un tissu vivant.",
                alerte=st.cv < 0.6))
    return g


def inventaire() -> List[str]:
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
        for item in mesurer(x, fs, reseau_hz=hz, evenements_s=evs):
            for texte in (item.libelle, item.sens):
                if texte not in vus:
                    vus.append(texte)
            for valeur in item.params.values():
                if isinstance(valeur, str) and not valeur.replace(".", "").isdigit():
                    if valeur not in vus:
                        vus.append(valeur)
    return vus
