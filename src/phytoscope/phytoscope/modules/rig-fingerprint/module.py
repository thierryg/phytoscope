# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/rig-fingerprint/module.py
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

"""L'fingerprint du montage — et ce qu'elle n'identifie pas.

Huit descripteurs caractérisent l'installation du moment : la plante, les
électrodes, le substrat, le câble, la carte. Le registre kept les montages
qu'on a retenus et dit lequel ressemble le plus à celui-ci.

**Ceci n'identifie pas une plante**, et le module le répète partout où il
s'affiche. Deux mesures du même végétal à deux jours d'intervalle diffèrent
souvent davantage que deux végétaux voisins le même après-midi. Un module qui
laisserait croire le contraire aurait plus d'inconvénients que d'utilité, et
`C-15` l'interdit.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import numpy as np

from phytoscope.api import (Analyser, Capability, Context, Quantity, Manifest,
                            Module)


class EmpreinteMontage(Module, Analyser):
    """Les descripteurs du montage, et sa resemblance avec ce qu'on connaît."""

    MANIFEST = Manifest(
        name="rig-fingerprint",
        title="Setup fingerprint",
        version="1.0.0",
        api="3.0",
        description=(
            "Huit descripteurs de l'installation du moment, et un registre "
            "des montages déjà retenus. N'identifie PAS une plante."),
        author="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capabilities=(Capability.ANALYSER,),
        built_in=True,
    )

    WINDOW_S = 120.0
    RAW_SIGNAL = False

    def setup(self) -> None:
        #  Le registre vit dans le directory du module, pas dans celui du
        #  logiciel : ce sont les données de ce module, il en est responsable.
        self._chemin_registre = os.path.join(self.context.directory(),
                                             "montages.json")
        self._registre = None

    def default_settings(self) -> Dict[str, Any]:
        return {"fenetre_s": 120.0, "comparer_aux_montages_connus": True}

    def analyse(self, x: np.ndarray, fs: float,
                 context: Context) -> List[Quantity]:
        from phytoscope.core import fingerprint as emp

        if x.size < 64:
            return []

        state = context.state()
        instants = [ev for ev in context.event_times()
                    if state.duration_s - ev <= x.size / fs]
        current = emp.compute(x, fs, instants,
                                metadata={"source": state.source})

        warning = context.translate(
            "Descriptor du MONTAGE — plante, électrodes, substrat, câble, "
            "carte — et non de la plante. Deux mesures du même végétal à deux "
            "jours d'intervalle diffèrent souvent davantage que deux végétaux "
            "voisins le même après-midi.")

        grandeurs = [
            Quantity(key=key, label=label, value=self._nombre(value),
                     text=value, meaning=warning)
            for key, label, value in self._lignes(current)
        ]

        if context.settings.get("comparer_aux_montages_connus", True):
            grandeurs += self._ressemblances(current, context)
        return grandeurs

    # -- détails -------------------------------------------------------------
    @staticmethod
    def _lignes(current) -> List[tuple]:
        """Les descripteurs, sous forme (clé, libellé, value affichée)."""
        outputs = []
        for i, (label, value) in enumerate(current.rows()):
            outputs.append((f"descripteur-{i}", label, value))
        return outputs

    @staticmethod
    def _nombre(text: str) -> float:
        """La value numérique d'un text formaté, ou zéro.

        L'fingerprint affiche des values déjà mises en forme ; l'API veut aussi
        un nombre. On l'extrait plutôt que de dupliquer le calcul.
        """
        import re
        m = re.search(r"[-+]?\d*[.,]?\d+", text or "")
        if not m:
            return 0.0
        try:
            return float(m.group(0).replace(",", "."))
        except ValueError:                                 # pragma: no cover
            return 0.0

    def _ressemblances(self, current, context: Context) -> List[Quantity]:
        from phytoscope.core import fingerprint as emp
        if self._registre is None:
            self._registre = emp.Registry(self._chemin_registre)
        connus = self._registre.recognise(current)
        if not connus:
            return [Quantity(
                key="montages-connus", label=context.translate(
                    "Montages retenus"),
                value=0.0, text=context.translate("aucun"),
                meaning=context.translate(
                    "Aucun montage n'a encore été retenu. L'onglet Multimètre "
                    "permet d'en garder un sous un name."))]
        name, score = connus[0]
        return [Quantity(
            key="resemblance", label=context.translate("Montage le plus proche"),
            value=float(score), text=f"{name.name} — {score * 100:.1f} %",
            meaning=context.translate(
                "Ressemblance avec un montage retenu précédemment. Une forte "
                "resemblance signale un montage semblable, PAS la même "
                "plante."))]
