# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/descripteurs-avances/module.py
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

"""Six représentations du même signal — et ce que chacune ne permet pas de dire.

Forme d'onde, FFT, ondelettes de Morlet, MFCC, prédiction linéaire, cepstre.
Les constantes empruntées au traitement de la parole sont transposées d'après
la cadence réelle, cinq décades plus bas que la voix humaine : les recopier
telles quelles n'aurait aucun sens.

Chaque trace porte son avertissement. Ce n'est pas de la prudence de façade :
la MFCC repose sur l'échelle de Mel, qui modélise l'audition humaine et ne dit
rien d'une plante ; la LPC modélise un conduit vocal, dont une plante est
dépourvue. Les deux restent utiles — comme comparateurs, comme estimateurs
d'enveloppe — à condition de savoir ce qu'on regarde (`C-15`).
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from phytoscope.api import (Capacite, Contexte, Descripteur, Manifeste, Module,
                            Trace)


class DescripteursAvances(Module, Descripteur):
    """Les six représentations, à la demande."""

    MANIFESTE = Manifeste(
        nom="descripteurs-avances",
        titre="Descripteurs avancés",
        version="1.0.0",
        api="1.0",
        description=(
            "Forme d'onde, FFT, ondelettes de Morlet, MFCC, prédiction "
            "linéaire et cepstre, avec les constantes transposées à la cadence "
            "réelle."),
        auteur="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capacites=(Capacite.DESCRIPTEUR,),
        integre=True,
    )

    FENETRE_S = 60.0
    #  Traité : ces représentations servent à regarder le SIGNAL, pas la
    #  chaîne de mesure. Le brut est le domaine des grandeurs scientifiques.
    SIGNAL_BRUT = False

    def reglages_par_defaut(self) -> Dict[str, Any]:
        return {
            "fenetre_s": 60.0,
            #  Lesquelles calculer. Les six coûtent une seconde ensemble ;
            #  n'en vouloir que deux est un choix légitime.
            "representations": ["temporel", "frequentiel", "ondelettes",
                                "mfcc", "lpc", "cepstre"],
        }

    def decrire(self, x: np.ndarray, fs: float,
                contexte: Contexte) -> List[Trace]:
        from phytoscope.core import features as f

        if x.size < 64:
            return []

        voulues = contexte.reglages.get("representations", [])
        traces: List[Trace] = []
        for cle in voulues:
            fabrique = getattr(self, f"_{cle}", None)
            if fabrique is None:
                continue
            try:
                trace = fabrique(x, fs, f, contexte)
            except Exception as exc:                       # noqa: BLE001
                #  Une représentation qui échoue ne doit pas emporter les cinq
                #  autres : on la saute et l'on dit pourquoi.
                contexte.journal(
                    f"représentation « {cle} » abandonnée : "
                    f"{type(exc).__name__}: {exc}", "warning")
                continue
            if trace is not None:
                traces.append(trace)
        return traces

    # -- les six représentations --------------------------------------------
    @staticmethod
    def _entete(cle: str, module) -> tuple:
        titre, sous_titre, avertissement = module.DESCRIPTEURS[cle]
        return titre, sous_titre, avertissement

    def _temporel(self, x, fs, f, contexte) -> Trace:
        titre, _, avertissement = self._entete("temporel", f)
        t = np.arange(x.size) / fs
        return Trace(x=t, y=x * 1e6, titre=contexte.traduire(titre),
                     x_libelle=contexte.traduire("temps (s)"),
                     y_libelle="µV",
                     avertissement=contexte.traduire(avertissement))

    def _frequentiel(self, x, fs, f, contexte) -> Trace:
        titre, _, avertissement = self._entete("frequentiel", f)
        sp = f.spectre_instantane(x, fs)
        return Trace(x=sp.frequences_hz, y=sp.amplitude_db,
                     titre=contexte.traduire(titre),
                     x_libelle=contexte.traduire("fréquence (Hz)"),
                     y_libelle="dB", x_log=True,
                     avertissement=contexte.traduire(avertissement))

    def _ondelettes(self, x, fs, f, contexte) -> Trace:
        titre, _, avertissement = self._entete("ondelettes", f)
        sc = f.ondelettes_morlet(x, fs)
        #  Une carte temps-fréquence ne rentre pas dans une courbe : on rend
        #  l'énergie intégrée par échelle, qui dit où l'énergie se trouve.
        energie = np.mean(sc.module, axis=1)
        return Trace(x=sc.frequences_hz, y=energie,
                     titre=contexte.traduire(titre) + " — "
                     + contexte.traduire("énergie par échelle"),
                     x_libelle=contexte.traduire("fréquence (Hz)"),
                     y_libelle=contexte.traduire("énergie"),
                     x_log=True,
                     avertissement=contexte.traduire(avertissement))

    def _mfcc(self, x, fs, f, contexte) -> Trace:
        titre, _, avertissement = self._entete("mfcc", f)
        m = f.mfcc(x, fs)
        #  `coefficients` est (trames, rangs) : on moyenne sur les trames
        #  pour obtenir un coefficient par rang, qui est ce qu'on compare
        #  d'une séance à l'autre.
        coefficients = np.asarray(m.coefficients, dtype=np.float64)
        moyens = (coefficients.mean(axis=0) if coefficients.ndim > 1
                  else coefficients.ravel())
        return Trace(x=np.arange(moyens.size, dtype=float), y=moyens,
                     titre=contexte.traduire(titre),
                     x_libelle=contexte.traduire("rang du coefficient"),
                     y_libelle=contexte.traduire("valeur"),
                     avertissement=contexte.traduire(avertissement))

    def _lpc(self, x, fs, f, contexte) -> Trace:
        titre, _, avertissement = self._entete("lpc", f)
        p = f.lpc(x, fs)
        return Trace(x=p.frequences_hz, y=p.enveloppe_db,
                     titre=contexte.traduire(titre),
                     x_libelle=contexte.traduire("fréquence (Hz)"),
                     y_libelle="dB", x_log=True,
                     avertissement=contexte.traduire(avertissement))

    def _cepstre(self, x, fs, f, contexte) -> Trace:
        titre, _, avertissement = self._entete("cepstre", f)
        c = f.cepstre(x, fs)
        return Trace(x=c.quefrence_s, y=c.cepstre,
                     titre=contexte.traduire(titre),
                     x_libelle=contexte.traduire("quéfrence (s)"),
                     y_libelle=contexte.traduire("amplitude"),
                     avertissement=contexte.traduire(avertissement))
