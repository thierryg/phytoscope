# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/contexte.py
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

"""Le contexte — tout ce qu'un module reçoit de l'hôte, et rien d'autre.

Un module **ne reçoit jamais l'objet `Engine`**. C'est délibéré, et c'est ce
qui rend l'API tenable dans le temps : le moteur change à chaque version — on
y a ajouté la relecture, la surveillance du disque, les échantillons — et un
module qui s'appuierait dessus casserait à chaque fois.

Il reçoit donc cet objet-ci, dont la forme est figée par le contrat. Il y
trouve :

* de quoi **lire** le signal et l'état de la mesure ;
* de quoi **écrire** ses propres réglages et ses propres fichiers, à un endroit
  qui lui appartient ;
* de quoi **dire** quelque chose — journal, message à l'utilisateur ;
* de quoi **traduire** ses libellés ;
* de quoi **s'abonner** à ce qui se passe.

Ce qu'il n'y trouve pas, et pourquoi
------------------------------------

**Aucun moyen d'écrire dans le signal.** Un module ne modifie pas la mesure.
Il l'observe, il en tire des nombres, il propose des notes. Laisser un module
altérer ce qui sera enregistré ferait de chaque séance une donnée dont on ne
pourrait plus rien conclure.

**Aucun accès aux réglages des autres modules ni à ceux du logiciel en
écriture.** Un module lit la fréquence d'échantillonnage ; il ne la change pas.

**Aucun chemin en dehors du sien.** `dossier()` rend un répertoire qui lui
appartient, et c'est là qu'il écrit. Rien ne l'empêche techniquement d'écrire
ailleurs — c'est du Python, pas une prison — mais ce serait une faute, et la
documentation du SDK le dit.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

__all__ = ["Contexte", "EtatMesure"]


@dataclass
class EtatMesure:
    """Un instantané de la mesure, recopié — non partagé.

    Recopié, et non une référence à l'état du moteur : un module qui garderait
    la référence verrait ses valeurs changer sous lui au milieu d'un calcul.
    """
    en_marche: bool = False
    source: str = ""
    duree_s: float = 0.0
    frequence_hz: float = 250.0
    tension_v: float = 0.0
    ligne_de_base_v: float = 0.0
    bruit_efficace_v: float = 0.0
    crete_a_crete_v: float = 0.0
    derive_v_par_min: float = 0.0
    sature: bool = False
    evenements: int = 0
    notes: int = 0
    enregistre: bool = False
    #  Vrai pendant la relecture d'un enregistrement : un module qui écrit
    #  quelque part doit savoir qu'il ne mesure pas, il rejoue.
    relecture: bool = False


class Contexte:
    """Ce qu'un module reçoit. Créé par l'hôte, un par module.

    Un contexte est **propre à un module** : son journal porte son nom, ses
    réglages sont les siens, son dossier lui appartient. Deux modules ne se
    marchent pas dessus.
    """

    def __init__(self, nom_module: str, moteur: Any, reglages_hote: Any,
                 dossier_modules: str) -> None:
        self._nom = nom_module
        self._moteur = moteur              # jamais exposé tel quel
        self._reglages_hote = reglages_hote
        self._dossier_modules = dossier_modules
        self._reglages: Dict[str, Any] = {}
        self._abonnements: List[tuple] = []

    # -- identité ------------------------------------------------------------
    @property
    def nom(self) -> str:
        """Le nom du module à qui appartient ce contexte."""
        return self._nom

    # -- lire le signal ------------------------------------------------------
    def signal(self, secondes: float = 60.0, brut: bool = False) -> np.ndarray:
        """Les N dernières secondes de signal, **en volts**.

        :param brut: vrai pour le signal avant réjecteur et passe-bas. À
            employer pour toute mesure de bruit : filtrer avant de mesurer le
            bruit revient à mesurer son propre filtre (`C-1B`).

        Rend un tableau vide s'il n'y a rien encore — ce n'est pas une erreur,
        c'est le cas au démarrage, et le module doit le prévoir.
        """
        try:
            x = self._moteur.recent(max(float(secondes), 0.1), raw=bool(brut))
        except Exception:                                  # noqa: BLE001
            return np.zeros(0, dtype=np.float64)
        return np.asarray(x, dtype=np.float64).ravel()

    @property
    def frequence_hz(self) -> float:
        """La cadence réelle d'échantillonnage."""
        try:
            return float(self._reglages_hote.acquisition.sample_rate)
        except Exception:                                  # noqa: BLE001
            return 250.0

    @property
    def pleine_echelle_v(self) -> float:
        """La pleine échelle du convertisseur, en volts."""
        try:
            return float(self._reglages_hote.acquisition.input_range_v)
        except Exception:                                  # noqa: BLE001
            return 2.5

    @property
    def reseau_hz(self) -> float:
        """La fréquence du secteur déclarée dans les réglages : 50 ou 60."""
        try:
            return float(self._reglages_hote.processing.notch_hz or 50.0)
        except Exception:                                  # noqa: BLE001
            return 50.0

    def etat(self) -> EtatMesure:
        """Un instantané de la mesure. Recopié, jamais partagé."""
        e = EtatMesure(frequence_hz=self.frequence_hz)
        s = getattr(self._moteur, "state", None)
        if s is None:
            return e
        e.en_marche = bool(getattr(s, "running", False))
        e.source = str(getattr(s, "source_name", ""))
        e.duree_s = float(getattr(s, "elapsed_s", 0.0))
        e.tension_v = float(getattr(s, "value_v", 0.0))
        e.ligne_de_base_v = float(getattr(s, "baseline_v", 0.0))
        e.bruit_efficace_v = float(getattr(s, "rms_v", 0.0))
        e.crete_a_crete_v = float(getattr(s, "pp_v", 0.0))
        e.derive_v_par_min = float(getattr(s, "drift_v_per_min", 0.0))
        e.sature = bool(getattr(s, "saturated", False))
        e.evenements = int(getattr(s, "events_total", 0))
        e.notes = int(getattr(s, "notes_total", 0))
        e.enregistre = bool(getattr(s, "recording", False))
        e.relecture = bool(getattr(s, "replaying", False))
        return e

    def instants_evenements(self) -> List[float]:
        """Les instants des événements récents, en secondes depuis le début."""
        try:
            return list(getattr(self._moteur, "_evenements_recents", []))
        except Exception:                                  # noqa: BLE001
            return []

    # -- écrire quelque part -------------------------------------------------
    def dossier(self) -> str:
        """Le répertoire du module, créé au besoin. **Écrire ici, et ici seul.**

        ``<configuration>/modules/<nom-du-module>/``

        Il survit aux mises à jour et n'est jamais effacé par le logiciel. Un
        module qui écrit ailleurs — dans le dossier des séances, par exemple —
        se mêle de ce qui ne le regarde pas.
        """
        chemin = os.path.join(self._dossier_modules, self._nom)
        os.makedirs(chemin, exist_ok=True)
        return chemin

    # -- réglages ------------------------------------------------------------
    @property
    def reglages(self) -> Dict[str, Any]:
        """Les réglages du module, tels que l'utilisateur les a laissés.

        Modifiables ; l'hôte les conserve à la fermeture. Ce sont ceux
        déclarés par `reglages_par_defaut()`, complétés par ce qui avait été
        enregistré.
        """
        return self._reglages

    def _poser_reglages(self, valeurs: Dict[str, Any]) -> None:
        """Réservé à l'hôte."""
        self._reglages = dict(valeurs)

    # -- dire quelque chose --------------------------------------------------
    def journal(self, message: str, niveau: str = "info") -> None:
        """Inscrit une ligne au journal du logiciel, sous le nom du module."""
        from ..core.logging_setup import get_logger
        log = get_logger(f"module.{self._nom}")
        getattr(log, niveau if niveau in
                ("debug", "info", "warning", "error") else "info")("%s", message)

    def message(self, texte: str) -> None:
        """Fait passer un message à l'utilisateur, dans la barre d'état.

        À employer avec parcimonie : un module qui parle sans cesse finit par
        n'être plus lu.
        """
        try:
            self._moteur._message(f"[{self._nom}] {texte}")
        except Exception:                                  # noqa: BLE001
            self.journal(texte)

    def traduire(self, texte: str) -> str:
        """La traduction d'un libellé dans la langue courante.

        Un module fournit ses propres catalogues dans `langues/` de son
        dossier ; à défaut, le texte source est rendu tel quel, ce qui est un
        comportement acceptable et non une erreur.
        """
        from ..i18n import t
        return t(texte)

    # -- s'abonner -----------------------------------------------------------
    def abonner(self, evenement: str, rappel: Callable) -> None:
        """S'abonne à un événement du logiciel.

        Les événements sont listés dans `api.evenements`. Un rappel qui lève
        est désabonné et l'incident inscrit au journal : un module fautif ne
        noie pas la séance sous les erreurs.
        """
        from .evenements import BUS
        BUS.abonner(evenement, rappel, module=self._nom)
        self._abonnements.append((evenement, rappel))

    def _desabonner_tout(self) -> None:
        """Réservé à l'hôte, appelé à l'arrêt du module."""
        from .evenements import BUS
        for evenement, rappel in self._abonnements:
            BUS.desabonner(evenement, rappel)
        self._abonnements.clear()
