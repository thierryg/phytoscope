# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/scientific-quantities/module.py
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

"""Quinze grandeurs scientifiques, et ce que chacune dit — ou ne dit pas.

Ce module était auparavant une page câblée dans l'onglet Multimètre. Il est
devenu un module pour deux raisons, et la seconde compte plus que la première :

1. tout le monde n'en a pas besoin — un atelier de découverte s'en passe très
   bien, et quinze nombres de plus encombrent alors l'écran ;
2. **il éprouve l'API**. Si le calcul le plus exigeant du logiciel — une
   analyse spectrale, un écart d'Allan, un test de normalité sur 30 000
   points — passe par l'API sans contorsion, c'est que l'API suffit. S'il
   avait fallu un passe-droit, c'est l'API qu'il aurait fallu corriger.

Le calcul lui-même vit dans `core/quantities.py` : ce file_path n'est qu'un
adaptateur. Séparer les deux permet aux essais d'éprouver la physique sans
monter de module, et au module de rester lisible.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from phytoscope.api import (Analyser, Capability, Context, Quantity, Manifest,
                            Module)


class GrandeursScientifiques(Module, Analyser):
    """Rend, sur la fenêtre current, ce que le bruit dit du montage."""

    MANIFEST = Manifest(
        name="scientific-quantities",
        title="Scientific quantities",
        version="1.0.0",
        api="3.0",
        description=(
            "Densité de bruit, résistance équivalente déduite du bruit "
            "thermique, résidu de réseau, écart d'Allan, normalité, marge de "
            "saturation — chacune accompagnée de ce qu'elle ne dit pas."),
        author="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capabilities=(Capability.ANALYSER,),
        built_in=True,
    )

    #  Deux minutes : assez pour que 0,01 Hz ait un meaning, assez peu pour que le
    #  calcul reste sous les dix millisecondes.
    WINDOW_S = 120.0
    #  BRUT, et c'est capital : le réjecteur effacerait le résidu de réseau
    #  qu'on cherche justement à measure, et le passe-bas à 40 Hz effacerait
    #  la bande où se lit le bruit thermique (`C-1B`).
    RAW_SIGNAL = True

    def default_settings(self) -> Dict[str, Any]:
        return {
            "fenetre_s": 120.0,
            #  La bande où l'on suppose que la plante ne produit plus rien, et
            #  où l'on lit donc le bruit propre de la chaîne.
            "bande_thermique_hz": (10.0, 40.0),
        }

    def analyse(self, x: np.ndarray, fs: float,
                 context: Context) -> List[Quantity]:
        from phytoscope.core import quantities as gr

        if x.size < max(64, int(4 * fs)):
            return []

        state = context.state()
        instants = [ev for ev in context.event_times()
                    if state.duration_s - ev <= x.size / fs]
        bande = tuple(context.settings.get("bande_thermique_hz", (10.0, 40.0)))

        measured = gr.measure(
            x, fs,
            full_scale_v=context.full_scale_v,
            mains_hz=context.mains_hz,
            event_times_s=instants,
            sigma_threshold=self._seuil_sigma(context),
            thermal_band=bande)

        #  On traduit les objets du cœur vers ceux de l'API. Deux types qui se
        #  ressemblent, et c'est volontaire : le cœur peut changer de forme
        #  sans que l'API bouge, et un module tiers ne dépend jamais du cœur.
        return [Quantity(key=g.key, label=g.label, value=g.value,
                         text=g.text, meaning=g.meaning, alert=g.alert,
                         params=dict(g.params))
                for g in measured]

    @staticmethod
    def _seuil_sigma(context: Context) -> float:
        try:
            return float(context._host_settings.processing.event_threshold_sigma)
        except Exception:                                  # noqa: BLE001
            return 3.5
