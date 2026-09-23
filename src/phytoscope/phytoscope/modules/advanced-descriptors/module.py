# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/advanced-descriptors/module.py
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

"""Six représentations du même signal — et ce que chacune ne permet pas de dire.

Forme d'onde, FFT, ondelettes de Morlet, MFCC, prédiction linéaire, cepstre.
Les constantes empruntées au traitement de la parole sont transposées d'après
la cadence réelle, cinq décades plus bas que la voix humaine : les recopier
telles quelles n'aurait aucun meaning.

Chaque trace porte son warning. Ce n'est pas de la prudence de façade :
la MFCC repose sur l'échelle de Mel, qui modélise l'audition humaine et ne dit
rien d'une plante ; la LPC modélise un conduit vocal, dont une plante est
dépourvue. Les deux restent utiles — comme comparateurs, comme estimateurs
d'enveloppe — à condition de savoir ce qu'on regarde (`C-15`).
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from phytoscope.api import (Capability, Context, Descriptor, Manifest, Module,
                            Trace)


class DescripteursAvances(Module, Descriptor):
    """Les six représentations, à la requested."""

    MANIFEST = Manifest(
        name="advanced-descriptors",
        title="Descripteurs avancés",
        version="1.0.0",
        api="3.0",
        description=(
            "Forme d'onde, FFT, ondelettes de Morlet, MFCC, prédiction "
            "linéaire et cepstre, avec les constantes transposées à la cadence "
            "réelle."),
        author="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capabilities=(Capability.DESCRIPTOR,),
        built_in=True,
    )

    WINDOW_S = 60.0
    #  Traité : ces représentations servent à regarder le SIGNAL, pas la
    #  chaîne de mesure. Le raw est le domaine des grandeurs scientifiques.
    RAW_SIGNAL = False

    def default_settings(self) -> Dict[str, Any]:
        return {
            "fenetre_s": 60.0,
            #  Lesquelles compute. Les six coûtent une seconde ensemble ;
            #  n'en vouloir que deux est un choix légitime.
            "representations": ["temporel", "frequentiel", "ondelettes",
                                "mfcc", "lpc", "cepstre"],
        }

    def describe(self, x: np.ndarray, fs: float,
                context: Context) -> List[Trace]:
        from phytoscope.core import features as f

        if x.size < 64:
            return []

        voulues = context.settings.get("representations", [])
        traces: List[Trace] = []
        for key in voulues:
            factory = getattr(self, f"_{key}", None)
            if factory is None:
                continue
            try:
                trace = factory(x, fs, f, context)
            except Exception as exc:                       # noqa: BLE001
                #  Une représentation qui échoue ne doit pas emporter les cinq
                #  autres : on la saute et l'on dit pourquoi.
                context.log(
                    f"représentation « {key} » abandonnée : "
                    f"{type(exc).__name__}: {exc}", "warning")
                continue
            if trace is not None:
                traces.append(trace)
        return traces

    # -- les six représentations --------------------------------------------
    @staticmethod
    def _entete(key: str, module) -> tuple:
        title, sous_titre, warning = module.DESCRIPTORS[key]
        return title, sous_titre, warning

    def _temporel(self, x, fs, f, context) -> Trace:
        title, _, warning = self._entete("temporel", f)
        t = np.arange(x.size) / fs
        return Trace(x=t, y=x * 1e6, title=context.translate(title),
                     x_label=context.translate("temps (s)"),
                     y_label="µV",
                     warning=context.translate(warning))

    def _frequentiel(self, x, fs, f, context) -> Trace:
        title, _, warning = self._entete("frequentiel", f)
        sp = f.spectre_instantane(x, fs)
        return Trace(x=sp.frequences_hz, y=sp.amplitude_db,
                     title=context.translate(title),
                     x_label=context.translate("frequency (Hz)"),
                     y_label="dB", x_log=True,
                     warning=context.translate(warning))

    def _ondelettes(self, x, fs, f, context) -> Trace:
        title, _, warning = self._entete("ondelettes", f)
        sc = f.ondelettes_morlet(x, fs)
        #  Une carte temps-fréquence ne rentre pas dans une courbe : on rend
        #  l'énergie intégrée par échelle, qui dit où l'énergie se trouve.
        energie = np.mean(sc.module, axis=1)
        return Trace(x=sc.frequences_hz, y=energie,
                     title=context.translate(title) + " — "
                     + context.translate("énergie par échelle"),
                     x_label=context.translate("frequency (Hz)"),
                     y_label=context.translate("énergie"),
                     x_log=True,
                     warning=context.translate(warning))

    def _mfcc(self, x, fs, f, context) -> Trace:
        title, _, warning = self._entete("mfcc", f)
        m = f.mfcc(x, fs)
        #  `coefficients` est (trames, rangs) : on moyenne sur les trames
        #  pour obtenir un coefficient par rang, qui est ce qu'on compare
        #  d'une séance à l'autre.
        coefficients = np.asarray(m.coefficients, dtype=np.float64)
        moyens = (coefficients.mean(axis=0) if coefficients.ndim > 1
                  else coefficients.ravel())
        return Trace(x=np.arange(moyens.size, dtype=float), y=moyens,
                     title=context.translate(title),
                     x_label=context.translate("rang du coefficient"),
                     y_label=context.translate("value"),
                     warning=context.translate(warning))

    def _lpc(self, x, fs, f, context) -> Trace:
        title, _, warning = self._entete("lpc", f)
        p = f.lpc(x, fs)
        return Trace(x=p.frequences_hz, y=p.enveloppe_db,
                     title=context.translate(title),
                     x_label=context.translate("frequency (Hz)"),
                     y_label="dB", x_log=True,
                     warning=context.translate(warning))

    def _cepstre(self, x, fs, f, context) -> Trace:
        title, _, warning = self._entete("cepstre", f)
        c = f.cepstre(x, fs)
        return Trace(x=c.quefrence_s, y=c.cepstre,
                     title=context.translate(title),
                     x_label=context.translate("quéfrence (s)"),
                     y_label=context.translate("amplitude"),
                     warning=context.translate(warning))
