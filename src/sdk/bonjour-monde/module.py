# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/sdk/bonjour-monde/module.py
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

"""Bonjour, monde — le plus petit module de PhytoScope qui fasse quelque chose.

Ce fichier est fait pour être lu en entier, puis copié. Il montre les quatre
choses qu'un module fait, et rien de plus :

1. **se présenter** — le manifeste ;
2. **se préparer** — `installer()`, une fois au démarrage ;
3. **travailler** — ici, une capacité `Analyseur` qui rend deux nombres ;
4. **écouter** — un abonnement à un événement du logiciel.

Pour l'essayer
--------------

Copiez ce dossier dans le répertoire des modules de votre installation :

.. code-block:: console

    # Linux
    cp -r sdk/bonjour-monde ~/.config/phytoscope/modules/
    # macOS
    cp -r sdk/bonjour-monde ~/Library/Application\\ Support/PhytoScope/modules/
    # Windows
    xcopy /E sdk\\bonjour-monde %APPDATA%\\PhytoScope\\modules\\bonjour-monde\\

Relancez le logiciel : l'onglet Multimètre, page « Grandeurs scientifiques »,
affiche vos deux lignes. L'onglet Diagnostic montre le module dans la liste.

Si rien n'apparaît, c'est que le module a été refusé — le Diagnostic dit
pourquoi, en une phrase.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

#  Tout ce dont un module a besoin vient d'ici, et de nulle part ailleurs.
#  Ce qui n'est pas dans `phytoscope.api` n'est pas de l'API : cela peut
#  changer d'une version à l'autre sans préavis.
from phytoscope.api import (Analyseur, Capacite, Contexte, EVENEMENT_DETECTE,
                            Grandeur, Manifeste, Module)


class BonjourMonde(Module, Analyseur):
    """Compte les échantillons reçus et les événements depuis le démarrage."""

    #  ── 1. Se présenter ────────────────────────────────────────────────────
    #  Le manifeste est lu SANS exécuter ce fichier : le logiciel sait donc ce
    #  que fait ce module avant de lui faire confiance. Écrivez-le en clair,
    #  avec des valeurs littérales — une valeur calculée serait ignorée.
    MANIFESTE = Manifeste(
        nom="bonjour-monde",            # a-z, 0-9 et tirets ; c'est l'identifiant
        titre="Bonjour, monde",         # ce que l'utilisateur lit
        version="1.0.0",
        api="1.0",                      # la version d'API que ce module vise
        description="Le module d'exemple du SDK. Compte, et c'est tout.",
        auteur="Votre nom",
        licence="MIT",
        site="https://bretagne-namaste.com",
        capacites=(Capacite.ANALYSEUR,),
        #  Si votre module a besoin d'une bibliothèque, dites-le ici : le
        #  logiciel vérifiera AVANT d'importer, et affichera « module désactivé :
        #  scipy absent » plutôt qu'une trace d'importation illisible.
        # exige=("scipy",),
    )

    # ── Les réglages de l'analyseur ──────────────────────────────────────────
    #  Combien de secondes de signal vous voulez, et si vous le voulez brut.
    #  BRUT = avant réjecteur et passe-bas. À employer pour toute mesure de
    #  bruit : filtrer avant de mesurer le bruit revient à mesurer son propre
    #  filtre.
    FENETRE_S = 30.0
    SIGNAL_BRUT = False

    # ── 2. Se préparer ───────────────────────────────────────────────────────
    def installer(self) -> None:
        """Appelé une fois, après le chargement de tous les modules.

        C'est ici qu'on s'abonne et qu'on prépare ses fichiers — **pas** dans
        `__init__`, qui est appelé pour tous les modules au démarrage et doit
        rester instantané.
        """
        self._evenements_vus = 0
        self.contexte.abonner(EVENEMENT_DETECTE, self._sur_evenement)
        self.contexte.journal("bonjour, monde")

    def arreter(self) -> None:
        """Appelé une fois, à la fermeture. Fermer ce qu'on a ouvert.

        Les abonnements sont retirés par l'hôte : inutile de s'en occuper.
        """
        self.contexte.journal(f"au revoir — {self._evenements_vus} événements vus")

    # ── 3. Travailler ────────────────────────────────────────────────────────
    def reglages_par_defaut(self) -> Dict[str, Any]:
        """Vos réglages et leurs valeurs initiales.

        Le logiciel les conserve pour vous, sous le nom de votre module, et
        vous les rend par `contexte.reglages`. N'écrivez jamais vous-même dans
        le fichier de réglages du logiciel.
        """
        return {"saluer": True, "unite_temps": "s"}

    def analyser(self, x: np.ndarray, fs: float,
                 contexte: Contexte) -> List[Grandeur]:
        """Rend les grandeurs à afficher. Une liste vide est acceptable.

        :param x: le signal, **en volts**, dans l'ordre chronologique.
        :param fs: la cadence réelle d'échantillonnage, en hertz.

        Ne levez pas d'exception pour dire « je n'ai rien à dire » : rendez
        une liste vide. Une exception désactive votre module pour la séance.
        """
        if x.size == 0:
            return []

        grandeurs = [
            Grandeur(
                cle="echantillons",
                libelle="Échantillons dans la fenêtre",
                valeur=float(x.size),
                texte=f"{x.size}",
                #  `sens` n'est pas décoratif. Le logiciel impose que toute
                #  valeur affichée dise ce qu'elle signifie ET ce qu'elle ne
                #  permet pas de conclure. Un module qui ne l'explique pas est
                #  chargé quand même, mais l'interface écrit « le module
                #  n'explique pas cette valeur », ce qui se remarque.
                sens=(f"Le nombre d'échantillons reçus sur les "
                      f"{x.size / fs:.0f} dernières secondes, à {fs:.0f} Hz. "
                      "Ne dit rien de la plante : c'est une mesure du logiciel "
                      "sur lui-même."),
            ),
            Grandeur(
                cle="evenements-vus",
                libelle="Événements vus depuis le démarrage",
                valeur=float(self._evenements_vus),
                texte=f"{self._evenements_vus}",
                sens=("Compté par abonnement, non par relecture du signal. "
                      "Dépend du seuil de détection en vigueur : le changer "
                      "change ce nombre."),
                #  Passez `alerte=True` pour que la valeur s'affiche en rouge.
                alerte=self._evenements_vus > 1000,
            ),
        ]

        if contexte.reglages.get("saluer", True):
            grandeurs.append(Grandeur(
                cle="salut",
                #  Un libellé qui contient un nombre doit être un GABARIT, avec
                #  la valeur dans `params` : « à {tau} s » et non « à 1 s ».
                #  Sinon il ne peut pas entrer dans un catalogue de traduction.
                libelle="Bonjour depuis {module}",
                valeur=1.0,
                texte=contexte.traduire("ça fonctionne"),
                sens="Si vous lisez ceci, votre module est chargé et appelé.",
                params={"module": self.MANIFESTE.titre},
            ))
        return grandeurs

    # ── 4. Écouter ───────────────────────────────────────────────────────────
    def _sur_evenement(self, instant_s: float, amplitude_v: float) -> None:
        """Appelé à chaque événement détecté dans le signal.

        **Soyez bref.** Les rappels s'exécutent dans le fil de l'interface :
        trente millisecondes ici ralentissent l'affichage de tout le monde.

        Un rappel qui lève est désabonné sur-le-champ, et l'incident inscrit au
        journal — c'est délibéré : laisser branché un abonné fautif noierait le
        journal sous la même trace, celui-là même dont on a besoin pour
        comprendre la panne.
        """
        self._evenements_vus += 1
