# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/evenements.py
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

"""Le bus d'événements — ce à quoi un module peut s'abonner.

Un module n'interroge pas le logiciel en boucle : il dit ce qui l'intéresse, et
l'hôte l'appelle. C'est le seul moyen d'avoir des modules qui ne coûtent rien
quand il ne se passe rien.

Les événements sont des **chaînes**, listées ci-dessous et nulle part ailleurs.
Une chaîne plutôt qu'une énumération pour une raison précise : une version
ultérieure peut en publier de nouveaux sans que les modules anciens aient à
être recompilés ni même relus. S'abonner à un événement qui n'existe pas encore
n'est pas une erreur — le rappel ne sera simplement jamais appelé.

Ce que l'hôte garantit
----------------------

**Les rappels sont appelés depuis le fil de l'interface**, jamais depuis le fil
d'acquisition. Un module qui met trente millisecondes à répondre ralentit
l'affichage ; il ne fait pas tomber un échantillon (`C-20`, `C-28`).

**Un rappel qui lève est désabonné.** Immédiatement, et l'incident est inscrit
au journal avec le nom du module. Un module fautif ne noie pas la séance sous
les traces, et il ne reste pas à moitié branché.

**L'ordre d'appel est celui de l'abonnement.** Déterministe, donc reproductible.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Tuple

__all__ = ["BUS", "Bus", "EVENEMENTS",
           "MESURE_DEMARREE", "MESURE_ARRETEE", "EVENEMENT_DETECTE",
           "NOTE_JOUEE", "ENONCE_PRODUIT", "SEANCE_COMMENCEE",
           "SEANCE_TERMINEE", "ECHANTILLON_CAPTURE", "REGLAGES_MODIFIES",
           "SOURCE_CHANGEE", "ALERTE_DISQUE"]

#  --- Les événements publiés, avec ce que reçoit le rappel -----------------
MESURE_DEMARREE = "mesure.demarree"          # (etat: EtatMesure)
MESURE_ARRETEE = "mesure.arretee"            # (etat: EtatMesure)
SOURCE_CHANGEE = "mesure.source"             # (nom: str)
EVENEMENT_DETECTE = "signal.evenement"       # (instant_s: float, amplitude_v: float)
NOTE_JOUEE = "musique.note"                  # (hauteur_midi: int, velocite: int)
ENONCE_PRODUIT = "parole.enonce"             # (texte: str)
SEANCE_COMMENCEE = "seance.commencee"        # (dossier: str)
SEANCE_TERMINEE = "seance.terminee"          # (dossier: str)
ECHANTILLON_CAPTURE = "echantillon.capture"  # (chemin: str)
REGLAGES_MODIFIES = "reglages.modifies"      # ()
ALERTE_DISQUE = "disque.alerte"              # (megaoctets_restants: float)

#: La liste complète, avec ce que le rappel reçoit. Sert à la documentation et
#: à l'outil du SDK, qui la lit pour proposer les événements existants.
EVENEMENTS: Dict[str, str] = {
    MESURE_DEMARREE: "l'acquisition commence — reçoit l'état de la mesure",
    MESURE_ARRETEE: "l'acquisition s'arrête — reçoit l'état de la mesure",
    SOURCE_CHANGEE: "la source d'acquisition a changé — reçoit son nom",
    EVENEMENT_DETECTE: "un événement franchit le seuil — reçoit (instant_s, amplitude_v)",
    NOTE_JOUEE: "une note est jouée — reçoit (hauteur_midi, velocite)",
    ENONCE_PRODUIT: "le mode Parole produit un énoncé — reçoit le texte",
    SEANCE_COMMENCEE: "un enregistrement démarre — reçoit le dossier",
    SEANCE_TERMINEE: "un enregistrement se termine — reçoit le dossier",
    ECHANTILLON_CAPTURE: "un échantillon rapide est écrit — reçoit son chemin",
    REGLAGES_MODIFIES: "les réglages ont changé — aucun argument",
    ALERTE_DISQUE: "l'espace disque devient critique — reçoit les Mo restants",
}


class Bus:
    """Le distributeur d'événements. Un seul par processus : `BUS`."""

    def __init__(self) -> None:
        self._abonnes: Dict[str, List[Tuple[Callable, str]]] = {}
        #  Un verrou, car `abonner` peut être appelé depuis l'installation
        #  d'un module tandis qu'un événement est en cours de distribution.
        self._verrou = threading.RLock()
        self.publies = 0
        self.desabonnements_sur_faute = 0

    def abonner(self, evenement: str, rappel: Callable,
                module: str = "") -> None:
        with self._verrou:
            self._abonnes.setdefault(evenement, []).append((rappel, module))

    def desabonner(self, evenement: str, rappel: Callable) -> None:
        with self._verrou:
            liste = self._abonnes.get(evenement)
            if not liste:
                return
            self._abonnes[evenement] = [(r, m) for r, m in liste if r is not rappel]

    def desabonner_module(self, module: str) -> int:
        """Retire tous les abonnements d'un module. Rend leur nombre."""
        retires = 0
        with self._verrou:
            for evenement, liste in list(self._abonnes.items()):
                garde = [(r, m) for r, m in liste if m != module]
                retires += len(liste) - len(garde)
                self._abonnes[evenement] = garde
        return retires

    def publier(self, evenement: str, *args: Any, **kwargs: Any) -> int:
        """Appelle les abonnés. Rend le nombre d'appels réussis.

        Un rappel qui lève est **désabonné sur-le-champ** : laisser branché un
        module qui échoue reviendrait à inscrire la même trace au journal
        toutes les secondes, et à rendre le journal inutilisable — celui-là
        même dont on a besoin pour comprendre la panne.
        """
        with self._verrou:
            abonnes = list(self._abonnes.get(evenement, ()))
        if not abonnes:
            return 0

        self.publies += 1
        reussis = 0
        for rappel, module in abonnes:
            try:
                rappel(*args, **kwargs)
                reussis += 1
            except Exception as exc:                       # noqa: BLE001
                self.desabonner(evenement, rappel)
                self.desabonnements_sur_faute += 1
                from ..core.logging_setup import get_logger
                get_logger(f"module.{module or '?'}").error(
                    "Abonnement à « %s » retiré après une faute : %s: %s",
                    evenement, type(exc).__name__, exc)
        return reussis

    def abonnes(self, evenement: str = "") -> int:
        with self._verrou:
            if evenement:
                return len(self._abonnes.get(evenement, ()))
            return sum(len(v) for v in self._abonnes.values())

    def vider(self) -> None:
        """Retire tout. Employé par les essais, et à la fermeture."""
        with self._verrou:
            self._abonnes.clear()


#: L'unique bus du processus.
BUS = Bus()
