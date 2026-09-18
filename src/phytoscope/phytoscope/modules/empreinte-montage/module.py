# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/empreinte-montage/module.py
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

"""L'empreinte du montage — et ce qu'elle n'identifie pas.

Huit descripteurs caractérisent l'installation du moment : la plante, les
électrodes, le substrat, le câble, la carte. Le registre garde les montages
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

from phytoscope.api import (Analyseur, Capacite, Contexte, Grandeur, Manifeste,
                            Module)


class EmpreinteMontage(Module, Analyseur):
    """Les descripteurs du montage, et sa ressemblance avec ce qu'on connaît."""

    MANIFESTE = Manifeste(
        nom="empreinte-montage",
        titre="Empreinte du montage",
        version="1.0.0",
        api="1.0",
        description=(
            "Huit descripteurs de l'installation du moment, et un registre "
            "des montages déjà retenus. N'identifie PAS une plante."),
        auteur="Bretagne Namasté — Thierry GAYET",
        licence="MIT",
        capacites=(Capacite.ANALYSEUR,),
        integre=True,
    )

    FENETRE_S = 120.0
    SIGNAL_BRUT = False

    def installer(self) -> None:
        #  Le registre vit dans le dossier du module, pas dans celui du
        #  logiciel : ce sont les données de ce module, il en est responsable.
        self._chemin_registre = os.path.join(self.contexte.dossier(),
                                             "montages.json")
        self._registre = None

    def reglages_par_defaut(self) -> Dict[str, Any]:
        return {"fenetre_s": 120.0, "comparer_aux_montages_connus": True}

    def analyser(self, x: np.ndarray, fs: float,
                 contexte: Contexte) -> List[Grandeur]:
        from phytoscope.core import empreinte as emp

        if x.size < 64:
            return []

        etat = contexte.etat()
        instants = [ev for ev in contexte.instants_evenements()
                    if etat.duree_s - ev <= x.size / fs]
        courante = emp.calculer(x, fs, instants,
                                metadonnees={"source": etat.source})

        avertissement = contexte.traduire(
            "Descripteur du MONTAGE — plante, électrodes, substrat, câble, "
            "carte — et non de la plante. Deux mesures du même végétal à deux "
            "jours d'intervalle diffèrent souvent davantage que deux végétaux "
            "voisins le même après-midi.")

        grandeurs = [
            Grandeur(cle=cle, libelle=libelle, valeur=self._nombre(valeur),
                     texte=valeur, sens=avertissement)
            for cle, libelle, valeur in self._lignes(courante)
        ]

        if contexte.reglages.get("comparer_aux_montages_connus", True):
            grandeurs += self._ressemblances(courante, contexte)
        return grandeurs

    # -- détails -------------------------------------------------------------
    @staticmethod
    def _lignes(courante) -> List[tuple]:
        """Les descripteurs, sous forme (clé, libellé, valeur affichée)."""
        sorties = []
        for i, (libelle, valeur) in enumerate(courante.lignes()):
            sorties.append((f"descripteur-{i}", libelle, valeur))
        return sorties

    @staticmethod
    def _nombre(texte: str) -> float:
        """La valeur numérique d'un texte formaté, ou zéro.

        L'empreinte affiche des valeurs déjà mises en forme ; l'API veut aussi
        un nombre. On l'extrait plutôt que de dupliquer le calcul.
        """
        import re
        m = re.search(r"[-+]?\d*[.,]?\d+", texte or "")
        if not m:
            return 0.0
        try:
            return float(m.group(0).replace(",", "."))
        except ValueError:                                 # pragma: no cover
            return 0.0

    def _ressemblances(self, courante, contexte: Contexte) -> List[Grandeur]:
        from phytoscope.core import empreinte as emp
        if self._registre is None:
            self._registre = emp.Registre(self._chemin_registre)
        connus = self._registre.reconnaitre(courante)
        if not connus:
            return [Grandeur(
                cle="montages-connus", libelle=contexte.traduire(
                    "Montages retenus"),
                valeur=0.0, texte=contexte.traduire("aucun"),
                sens=contexte.traduire(
                    "Aucun montage n'a encore été retenu. L'onglet Multimètre "
                    "permet d'en garder un sous un nom."))]
        nom, score = connus[0]
        return [Grandeur(
            cle="ressemblance", libelle=contexte.traduire("Montage le plus proche"),
            valeur=float(score), texte=f"{nom.nom} — {score * 100:.1f} %",
            sens=contexte.traduire(
                "Ressemblance avec un montage retenu précédemment. Une forte "
                "ressemblance signale un montage semblable, PAS la même "
                "plante."))]
