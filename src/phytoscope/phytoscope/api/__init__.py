# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/__init__.py
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

"""L'API des modules de PhytoScope — la surface publique, et elle seule.

Un module n'importe **que depuis ici** :

.. code-block:: python

    from phytoscope.api import Module, Manifeste, Capacite, Analyseur, Grandeur

Ce qui est absent de ce fichier n'est pas de l'API : cela peut changer d'une
version à l'autre sans préavis. Ce qui y figure est tenu par le contrat de
version (voir `contract.VERSION_API`).

Pour écrire un module
---------------------

Le plus court qui fasse quelque chose tient en vingt lignes :

.. code-block:: python

    from phytoscope.api import Analyseur, Capacite, Grandeur, Manifeste, Module

    class Bonjour(Module, Analyseur):
        MANIFESTE = Manifeste(
            nom="bonjour-monde",
            titre="Bonjour, monde",
            version="1.0.0",
            api="1.0",
            capacites=(Capacite.ANALYSEUR,),
        )

        def analyser(self, x, fs, contexte):
            return [Grandeur(
                cle="compte", libelle="Échantillons reçus",
                valeur=float(x.size), texte=f"{x.size}",
                sens="Le nombre d'échantillons de la fenêtre analysée.")]

Le SDK, à la racine du projet (`sdk/`), en donne un exemplaire complet avec ses
essais, et un outil qui en crée un nouveau d'une commande.
"""
from __future__ import annotations

from .context import Contexte, EtatMesure
from .contract import (VERSION_API, Analyseur, Capacite, Descripteur,
                      Exportateur, Grandeur, Manifeste, Module, NoteProposee,
                      Sonificateur, Source, Trace, compatible)
from .events import BUS, EVENEMENTS
from .events import (ALERTE_DISQUE, ECHANTILLON_CAPTURE, ENONCE_PRODUIT,
                         EVENEMENT_DETECTE, MESURE_ARRETEE, MESURE_DEMARREE,
                         NOTE_JOUEE, REGLAGES_MODIFIES, SEANCE_COMMENCEE,
                         SEANCE_TERMINEE, SOURCE_CHANGEE)
from .registry import EtatModule, ModuleCharge, Registre

__all__ = [
    #  Le contrat
    "VERSION_API", "compatible", "Manifeste", "Module", "Capacite",
    #  Les capacités
    "Analyseur", "Descripteur", "Sonificateur", "Exportateur", "Source",
    #  Ce qu'elles échangent
    "Grandeur", "Trace", "NoteProposee",
    #  Ce qu'un module reçoit
    "Contexte", "EtatMesure",
    #  Les événements
    "BUS", "EVENEMENTS", "MESURE_DEMARREE", "MESURE_ARRETEE", "SOURCE_CHANGEE",
    "EVENEMENT_DETECTE", "NOTE_JOUEE", "ENONCE_PRODUIT", "SEANCE_COMMENCEE",
    "SEANCE_TERMINEE", "ECHANTILLON_CAPTURE", "REGLAGES_MODIFIES",
    "ALERTE_DISQUE",
    #  L'hôte — un module n'en a pas besoin, l'interface si
    "Registre", "ModuleCharge", "EtatModule",
]
