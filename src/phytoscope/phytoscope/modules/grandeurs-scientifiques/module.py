# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/grandeurs-scientifiques/module.py
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

"""Quinze grandeurs scientifiques, et ce que chacune dit — ou ne dit pas.

Ce module était auparavant une page câblée dans l'onglet Multimètre. Il est
devenu un module pour deux raisons, et la seconde compte plus que la première :

1. tout le monde n'en a pas besoin — un atelier de découverte s'en passe très
   bien, et quinze nombres de plus encombrent alors l'écran ;
2. **il éprouve l'API**. Si le calcul le plus exigeant du logiciel — une
   analyse spectrale, un écart d'Allan, un test de normalité sur 30 000
   points — passe par l'API sans contorsion, c'est que l'API suffit. S'il
   avait fallu un passe-droit, c'est l'API qu'il aurait fallu corriger.

Le calcul lui-même vit dans `core/grandeurs.py` : ce fichier n'est qu'un
adaptateur. Séparer les deux permet aux essais d'éprouver la physique sans
monter de module, et au module de rester lisible.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from phytoscope.api import (Analyseur, Capacite, Contexte, Grandeur, Manifeste,
                            Module)


class GrandeursScientifiques(Module, Analyseur):
    """Rend, sur la fenêtre courante, ce que le bruit dit du montage."""

    MANIFESTE = Manifeste(
        nom="grandeurs-scientifiques",
        titre="Grandeurs scientifiques",
        version="1.0.0",
        api="1.0",
        description=(
            "Densité de bruit, résistance équivalente déduite du bruit "
            "thermique, résidu de réseau, écart d'Allan, normalité, marge de "
            "saturation — chacune accompagnée de ce qu'elle ne dit pas."),
        auteur="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capacites=(Capacite.ANALYSEUR,),
        integre=True,
    )

    #  Deux minutes : assez pour que 0,01 Hz ait un sens, assez peu pour que le
    #  calcul reste sous les dix millisecondes.
    FENETRE_S = 120.0
    #  BRUT, et c'est capital : le réjecteur effacerait le résidu de réseau
    #  qu'on cherche justement à mesurer, et le passe-bas à 40 Hz effacerait
    #  la bande où se lit le bruit thermique (`C-1B`).
    SIGNAL_BRUT = True

    def reglages_par_defaut(self) -> Dict[str, Any]:
        return {
            "fenetre_s": 120.0,
            #  La bande où l'on suppose que la plante ne produit plus rien, et
            #  où l'on lit donc le bruit propre de la chaîne.
            "bande_thermique_hz": (10.0, 40.0),
        }

    def analyser(self, x: np.ndarray, fs: float,
                 contexte: Contexte) -> List[Grandeur]:
        from phytoscope.core import grandeurs as gr

        if x.size < max(64, int(4 * fs)):
            return []

        etat = contexte.etat()
        instants = [ev for ev in contexte.instants_evenements()
                    if etat.duree_s - ev <= x.size / fs]
        bande = tuple(contexte.reglages.get("bande_thermique_hz", (10.0, 40.0)))

        mesurees = gr.mesurer(
            x, fs,
            pleine_echelle_v=contexte.pleine_echelle_v,
            reseau_hz=contexte.reseau_hz,
            evenements_s=instants,
            seuil_sigma=self._seuil_sigma(contexte),
            bande_thermique=bande)

        #  On traduit les objets du cœur vers ceux de l'API. Deux types qui se
        #  ressemblent, et c'est volontaire : le cœur peut changer de forme
        #  sans que l'API bouge, et un module tiers ne dépend jamais du cœur.
        return [Grandeur(cle=g.cle, libelle=g.libelle, valeur=g.valeur,
                         texte=g.texte, sens=g.sens, alerte=g.alerte,
                         params=dict(g.params))
                for g in mesurees]

    @staticmethod
    def _seuil_sigma(contexte: Contexte) -> float:
        try:
            return float(contexte._reglages_hote.processing.event_threshold_sigma)
        except Exception:                                  # noqa: BLE001
            return 3.5
