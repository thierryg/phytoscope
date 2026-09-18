# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/contrat.py
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

"""Le contrat des modules — ce qu'un module promet, ce que l'hôte garantit.

Ce fichier est la **pièce la plus engageante du logiciel**. Tout le reste peut
changer d'une version à l'autre ; ceci, non : dès qu'un module écrit par
quelqu'un d'autre s'y appuie, le casser casse son travail. On l'a donc écrit
en se demandant, pour chaque ligne, si l'on accepterait de la maintenir dix
ans.

Ce qui en découle, et qui explique les choix ci-dessous :

* **Un numéro de version explicite.** ``VERSION_API`` suit la numérotation
  sémantique. Un module déclare la version qu'il vise ; l'hôte refuse de
  charger ce qu'il ne sait pas honorer, plutôt que de le charger à moitié.
* **Des capacités déclarées, pas devinées.** Un module dit ce qu'il fournit.
  L'hôte ne va pas fouiller ses attributs pour deviner : ce qui n'est pas
  déclaré n'existe pas.
* **Aucun accès au moteur.** Un module reçoit un `Contexte` — une surface
  étroite, documentée, stable. Il ne reçoit jamais l'objet `Engine`, dont la
  forme interne change à chaque version.
* **Rien n'est obligatoire sauf le manifeste.** Un module qui ne fournit
  qu'une seule capacité n'écrit qu'une seule méthode.

Les cinq capacités
------------------

===============  ==========================================================
`Analyseur`      calcule des grandeurs sur une fenêtre de signal
`Descripteur`    produit une représentation du signal (une image, une courbe)
`Sonificateur`   transforme le signal en notes
`Exportateur`    écrit une séance dans un autre format
`Source`         fournit un flux de mesure
===============  ==========================================================

Un module peut en fournir plusieurs, ou aucune — dans ce dernier cas il n'a
d'intérêt que par ce qu'il fait à l'installation et à l'arrêt, ce qui est
légitime (un module de journalisation, par exemple).

Ce que l'hôte garantit
----------------------

1. **Un module qui lève ne fait jamais tomber le logiciel.** Toute méthode est
   appelée sous protection ; une faute désactive le module, l'inscrit au
   journal, et la séance continue.
2. **L'ordre de chargement est déterministe** : les dépendances d'abord, puis
   l'ordre alphabétique. Deux démarrages donnent le même ordre.
3. **Rien n'est appelé pendant l'acquisition sur le fil des données.** Les
   modules travaillent sur des instantanés, jamais sur le flux : un module lent
   ralentit son propre affichage, pas la mesure (`C-20`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "VERSION_API", "Manifeste", "Module", "Capacite",
    "Analyseur", "Descripteur", "Sonificateur", "Exportateur", "Source",
    "Grandeur", "Trace", "NoteProposee", "compatible",
]

#  Version du contrat, en numérotation sémantique.
#
#    majeur  une promesse est rompue — un module ancien cesse de fonctionner ;
#    mineur  une capacité ou un paramètre s'ajoute, sans rien casser ;
#    correctif  une précision de comportement, jamais de forme.
#
#  Un module déclarant « 1.0 » fonctionne avec toute API « 1.x ». Il ne
#  fonctionne pas avec « 2.x », et l'hôte le lui dira plutôt que d'échouer
#  au milieu d'une séance.
VERSION_API = "1.0"


def compatible(demande: str, offerte: str = VERSION_API) -> bool:
    """Le module demandant `demande` peut-il tourner sur l'API `offerte` ?

    Règle : même majeur, et mineur offert au moins égal au mineur demandé.
    Un module qui vise 1.2 ne tourne pas sur une API 1.1, qui ne connaît pas
    encore ce qu'il attend.
    """
    def decouper(v: str) -> Tuple[int, int]:
        m = re.match(r"^\s*(\d+)\.(\d+)", str(v))
        return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)

    dm, dn = decouper(demande)
    om, on = decouper(offerte)
    if dm < 0 or om < 0:
        return False
    return dm == om and dn <= on


# ---------------------------------------------------------------------------
#  Ce qu'un module dit de lui-même
# ---------------------------------------------------------------------------
class Capacite:
    """Les noms des capacités, pour éviter les chaînes en dur."""
    ANALYSEUR = "analyseur"
    DESCRIPTEUR = "descripteur"
    SONIFICATEUR = "sonificateur"
    EXPORTATEUR = "exportateur"
    SOURCE = "source"

    TOUTES = (ANALYSEUR, DESCRIPTEUR, SONIFICATEUR, EXPORTATEUR, SOURCE)


@dataclass
class Manifeste:
    """L'identité d'un module — la seule chose qu'il doit obligatoirement dire.

    Elle est lue **avant** d'importer quoi que ce soit du module : c'est ce qui
    permet de lister les modules présents, d'en désactiver un, et de refuser
    d'importer celui qui vise une API qu'on ne sait pas honorer. Importer pour
    savoir s'il faut importer serait absurde.
    """
    nom: str                        # identifiant technique : a-z, 0-9, tiret
    titre: str = ""                 # ce qui s'affiche ; à défaut, `nom`
    version: str = "0.1.0"
    api: str = VERSION_API          # la version de contrat visée
    description: str = ""
    auteur: str = ""
    licence: str = ""
    site: str = ""
    #  Ce que le module fournit. Déclaratif : ce qui n'est pas là n'est pas
    #  proposé à l'utilisateur, même si la méthode existe.
    capacites: Tuple[str, ...] = ()
    #  Les modules qui doivent être chargés avant celui-ci, par leur `nom`.
    depend_de: Tuple[str, ...] = ()
    #  Les bibliothèques Python nécessaires. Vérifiées avant le chargement :
    #  mieux vaut « module désactivé : scipy absent » qu'une trace d'import.
    exige: Tuple[str, ...] = ()
    #  Un module interne au logiciel, livré avec lui. Il ne se désinstalle pas.
    integre: bool = False

    def __post_init__(self) -> None:
        if not self.titre:
            self.titre = self.nom

    @property
    def valide(self) -> bool:
        return bool(re.match(r"^[a-z][a-z0-9-]{1,48}$", self.nom or ""))

    def defauts(self) -> List[str]:
        """Ce qui empêche ce manifeste d'être accepté, en clair."""
        soucis = []
        if not self.valide:
            soucis.append(
                f"nom « {self.nom} » invalide : lettres minuscules, chiffres "
                "et tirets, 2 à 49 caractères, commençant par une lettre")
        if not compatible(self.api):
            soucis.append(
                f"vise l'API {self.api}, or ce logiciel offre {VERSION_API}")
        inconnues = [c for c in self.capacites if c not in Capacite.TOUTES]
        if inconnues:
            soucis.append(f"capacité(s) inconnue(s) : {', '.join(inconnues)}")
        return soucis

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


# ---------------------------------------------------------------------------
#  Les objets que les capacités échangent
# ---------------------------------------------------------------------------
@dataclass
class Grandeur:
    """Une quantité mesurée, avec ce qu'elle dit et ce qu'elle ne dit pas.

    Le champ `sens` n'est pas décoratif : `C-15` impose que toute
    représentation affiche ce qu'elle suppose et ce qu'elle ne permet pas de
    conclure. Un module qui rend une grandeur sans l'expliquer sera chargé,
    mais l'interface écrira « (le module n'explique pas cette valeur) », ce
    qui se remarque.
    """
    cle: str
    libelle: str
    valeur: float
    texte: str = ""                 # la valeur mise en forme, unité comprise
    sens: str = ""                  # ce que ce nombre dit — en une phrase
    alerte: bool = False
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.texte:
            self.texte = f"{self.valeur:.3g}"


@dataclass
class Trace:
    """Une courbe à afficher : des abscisses, des ordonnées, des légendes."""
    x: np.ndarray
    y: np.ndarray
    titre: str = ""
    x_libelle: str = ""
    y_libelle: str = ""
    x_log: bool = False
    y_log: bool = False
    #  Ce que la représentation suppose, et ce qu'elle ne permet pas de
    #  conclure. Affiché sous la courbe (`C-15`).
    avertissement: str = ""

    def __post_init__(self) -> None:
        self.x = np.asarray(self.x, dtype=np.float64).ravel()
        self.y = np.asarray(self.y, dtype=np.float64).ravel()
        if self.x.size != self.y.size:
            raise ValueError(
                f"trace « {self.titre} » : {self.x.size} abscisses pour "
                f"{self.y.size} ordonnées")


@dataclass
class NoteProposee:
    """Une note qu'un sonificateur propose. L'hôte décide de la jouer."""
    hauteur_midi: int
    velocite: int = 80
    duree_s: float = 0.4
    canal: int = 0
    #  La valeur mesurée qui a produit cette note. Conservée dans le rendu :
    #  une sonification dont on ne peut pas remonter à la mesure n'est plus
    #  une mesure (`C-15`).
    origine_v: float = 0.0


# ---------------------------------------------------------------------------
#  Le module lui-même
# ---------------------------------------------------------------------------
class Module:
    """Ce dont hérite tout module de PhytoScope.

    Le seul élément obligatoire est `MANIFESTE`. Tout le reste a un
    comportement par défaut qui ne fait rien, de sorte qu'un module minimal
    tient en quinze lignes — voir le SDK, module « bonjour-monde ».

    Cycle de vie, dans cet ordre :

    1. ``__init__(contexte)`` — on reçoit le contexte. **Ne rien faire de
       long ici** : c'est appelé au démarrage du logiciel, et tous les
       modules passent par là.
    2. ``installer()`` — une fois, après le chargement de tous les modules.
       C'est ici qu'on s'abonne aux événements et qu'on prépare ses fichiers.
    3. les capacités sont appelées à la demande, pendant la séance.
    4. ``arreter()`` — une fois, à la fermeture. Fermer ce qu'on a ouvert.

    Une exception levée dans n'importe laquelle de ces étapes désactive le
    module et l'inscrit au journal. Elle ne fait jamais tomber le logiciel.
    """

    #: Obligatoire. Redéfini par chaque module.
    MANIFESTE: Manifeste = Manifeste(nom="module-sans-nom")

    def __init__(self, contexte: "Contexte") -> None:   # noqa: F821
        self.contexte = contexte

    # -- cycle de vie --------------------------------------------------------
    def installer(self) -> None:
        """Appelé une fois, après le chargement de tous les modules."""

    def arreter(self) -> None:
        """Appelé une fois, à la fermeture. Fermer ce qu'on a ouvert."""

    # -- réglages ------------------------------------------------------------
    def reglages_par_defaut(self) -> Dict[str, Any]:
        """Les réglages du module et leurs valeurs initiales.

        L'hôte les conserve dans son propre fichier, sous le nom du module, et
        les rend par `contexte.reglages`. Un module n'écrit jamais dans le
        fichier de réglages du logiciel.
        """
        return {}


# ---------------------------------------------------------------------------
#  Les cinq capacités
# ---------------------------------------------------------------------------
class Analyseur:
    """Calcule des grandeurs sur une fenêtre de signal.

    Appelé par l'onglet Multimètre, à cadence réduite et seulement quand la
    page est visible. Le signal reçu est **en volts** et, sauf demande
    contraire, **brut** — avant réjecteur et passe-bas : filtrer avant de
    mesurer le bruit revient à mesurer son propre filtre (`C-1B`).
    """

    #: Durée de signal souhaitée, en secondes. L'hôte donne ce qu'il a.
    FENETRE_S: float = 120.0
    #: Faux pour recevoir le signal traité plutôt que le signal brut.
    SIGNAL_BRUT: bool = True

    def analyser(self, x: np.ndarray, fs: float,
                 contexte: "Contexte") -> Sequence[Grandeur]:  # noqa: F821
        """Rend les grandeurs calculées. Une liste vide est acceptable."""
        raise NotImplementedError


class Descripteur:
    """Produit une représentation du signal — une courbe, un spectre, une carte.

    Appelé par l'onglet Descripteurs, à la demande de l'utilisateur. Ce n'est
    donc pas un chemin critique : un calcul d'une seconde est acceptable.
    """

    FENETRE_S: float = 60.0
    SIGNAL_BRUT: bool = False

    def decrire(self, x: np.ndarray, fs: float,
                contexte: "Contexte") -> Sequence[Trace]:      # noqa: F821
        raise NotImplementedError


class Sonificateur:
    """Transforme une valeur mesurée en notes.

    Appelé pour chaque événement détecté. **Doit être rapide** : il s'exécute
    dans la boucle de rendu musical. Rendre une liste vide signifie « pas de
    note pour cette valeur », ce qui est une réponse légitime.
    """

    def sonifier(self, valeur_v: float, contexte: "Contexte"  # noqa: F821
                 ) -> Sequence[NoteProposee]:
        raise NotImplementedError


class Exportateur:
    """Écrit une séance dans un autre format.

    Proposé dans la bibliothèque, à côté des formats livrés. Le module reçoit
    le répertoire de la séance et écrit où on le lui dit — jamais ailleurs.
    """

    #: Ce qui s'affiche dans la liste des formats.
    FORMAT: str = ""
    #: L'extension du fichier produit, point compris.
    EXTENSION: str = ""

    def exporter(self, seance: str, cible: str,
                 contexte: "Contexte") -> bool:                # noqa: F821
        """Rend vrai si l'écriture a réussi."""
        raise NotImplementedError


class Source:
    """Fournit un flux de mesure — une carte, un fichier, un générateur.

    La capacité la plus délicate : elle s'exécute sur le chemin des données.
    Un module de source doit être **irréprochable** sur ce point, et l'hôte
    l'isole autant qu'il peut — mais il ne peut pas l'isoler du temps qu'il
    prend.
    """

    #: Ce qui s'affiche dans la liste des sources d'acquisition.
    LIBELLE: str = ""

    def ouvrir(self, contexte: "Contexte") -> bool:            # noqa: F821
        raise NotImplementedError

    def lire(self) -> Optional[np.ndarray]:
        """Rend le bloc d'échantillons disponible, en volts, ou None."""
        raise NotImplementedError

    def fermer(self) -> None:
        """Referme ce qui a été ouvert."""
