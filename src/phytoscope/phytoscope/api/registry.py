# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/registry.py
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

"""Le registre — découvre les modules, les charge, et les isole.

Trois endroits sont fouillés, dans cet ordre :

1. ``phytoscope/modules/`` — les **modules intégrés**, livrés avec le logiciel.
   Ils ne se désinstallent pas ; ils se désactivent.
2. ``<configuration>/modules/`` — ceux que l'utilisateur a posés lui-même.
   C'est là que le SDK dépose ce qu'on écrit.
3. les paquets Python déclarant un point d'entrée ``phytoscope.modules`` —
   pour un module diffusé sur PyPI.

Chaque module est un **dossier** contenant au minimum ``module.py``. Le fichier
y déclare une classe héritant de `Module`, avec son `MANIFESTE`.

Comment l'isolement fonctionne
------------------------------

Le principe tient en une phrase : **un module qui se comporte mal est
désactivé, jamais toléré**. Concrètement :

* une faute à l'import, à l'installation ou dans une capacité **désactive le
  module pour la séance** et l'inscrit au journal, avec sa trace complète ;
* le logiciel continue, amputé de ce module et de lui seul ;
* l'onglet Diagnostic montre ce qui a été désactivé et pourquoi.

Ce n'est pas un bac à sable — c'est du Python, un module peut écrire où il
veut. C'est une **discipline de bon voisinage**, doublée d'un filet : personne
ne perd une séance de huit heures parce qu'un module a mal tourné.

Pourquoi pas de rechargement à chaud
------------------------------------

On y a pensé, et on l'a écarté. Recharger un module dont des objets sont déjà
référencés ailleurs — un abonnement, une trace affichée — laisse deux versions
en mémoire et produit des bogues qu'on ne sait pas lire. Un redémarrage coûte
trois secondes ; un bogue de rechargement coûte une soirée.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Type

from .context import Contexte
from .contract import VERSION_API, Capacite, Manifeste, Module, compatible

__all__ = ["Registre", "ModuleCharge", "EtatModule"]

#  Marqueur : distingue « valeur absente » de « valeur qu'on ne
#  sait pas évaluer sans exécuter le module ».
_INEVALUABLE = object()


class EtatModule:
    """Où en est un module."""
    DECOUVERT = "decouvert"        # trouvé, pas encore importé
    CHARGE = "charge"              # importé et instancié
    ACTIF = "actif"                # installé, en fonction
    DESACTIVE = "desactive"        # l'utilisateur n'en veut pas
    EN_FAUTE = "en_faute"          # a levé — retiré pour la séance
    INCOMPATIBLE = "incompatible"  # vise une API qu'on ne sait pas honorer


@dataclass
class ModuleCharge:
    """Un module, son manifeste, son état, et ce qui lui est arrivé."""
    manifeste: Manifeste
    chemin: str = ""
    origine: str = "integre"       # integre | utilisateur | paquet
    etat: str = EtatModule.DECOUVERT
    instance: Optional[Module] = None
    contexte: Optional[Contexte] = None
    faute: str = ""                # le message, en clair
    trace: str = ""                # la trace complète, pour le journal

    @property
    def nom(self) -> str:
        return self.manifeste.nom

    @property
    def utilisable(self) -> bool:
        return self.etat == EtatModule.ACTIF and self.instance is not None

    def fournit(self, capacite: str) -> bool:
        return self.utilisable and capacite in self.manifeste.capacites


class Registre:
    """Découvre, charge et tient les modules. Un par session."""

    FICHIER_MODULE = "module.py"

    def __init__(self, moteur: Any, reglages: Any) -> None:
        self._moteur = moteur
        self._reglages = reglages
        self.modules: Dict[str, ModuleCharge] = {}
        self._ordre: List[str] = []

    # -- les chemins ---------------------------------------------------------
    @staticmethod
    def dossier_integres() -> str:
        return os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "modules")

    @staticmethod
    def dossier_utilisateur() -> str:
        from ..config import config_dir
        return os.path.join(config_dir(), "modules")

    # -- découverte ----------------------------------------------------------
    def decouvrir(self) -> List[ModuleCharge]:
        """Trouve les modules sans en importer un seul.

        Sans en importer un seul : c'est ce qui permet de lister ce qui est
        présent, d'en désactiver un, et de refuser celui qui vise une API
        inconnue — sans avoir à exécuter son code pour le savoir.
        """
        trouves: List[ModuleCharge] = []
        for dossier, origine in ((self.dossier_integres(), "integre"),
                                 (self.dossier_utilisateur(), "utilisateur")):
            if not os.path.isdir(dossier):
                continue
            for nom in sorted(os.listdir(dossier)):
                chemin = os.path.join(dossier, nom)
                fichier = os.path.join(chemin, self.FICHIER_MODULE)
                if not os.path.isfile(fichier):
                    continue
                manifeste = self._lire_manifeste(fichier, nom)
                if manifeste is None:
                    continue
                trouves.append(ModuleCharge(manifeste=manifeste, chemin=chemin,
                                            origine=origine))
        trouves += self._decouvrir_paquets()

        for m in trouves:
            defauts = m.manifeste.defauts()
            if defauts:
                m.etat = EtatModule.INCOMPATIBLE
                m.faute = " ; ".join(defauts)
            elif not self._active(m.nom, m.manifeste):
                m.etat = EtatModule.DESACTIVE
            manquantes = [p for p in m.manifeste.exige
                          if importlib.util.find_spec(p) is None]
            if manquantes and m.etat != EtatModule.INCOMPATIBLE:
                m.etat = EtatModule.INCOMPATIBLE
                m.faute = (f"bibliothèque(s) absente(s) : {', '.join(manquantes)}"
                           f" — pip install {' '.join(manquantes)}")
            self.modules[m.nom] = m
        return trouves

    def _decouvrir_paquets(self) -> List[ModuleCharge]:
        """Les modules installés comme paquets Python.

        Facultatif et sans conséquence s'il n'y en a pas : `importlib.metadata`
        est dans la bibliothèque standard depuis 3.8, mais l'énumération peut
        échouer sur une installation abîmée — ce n'est pas une raison de ne pas
        démarrer.
        """
        trouves: List[ModuleCharge] = []
        try:
            from importlib.metadata import entry_points
            points = entry_points()
            groupe = (points.select(group="phytoscope.modules")
                      if hasattr(points, "select")
                      else points.get("phytoscope.modules", ()))
        except Exception:                                  # noqa: BLE001
            return trouves
        for point in groupe:
            try:
                fabrique = point.load()
                manifeste = getattr(fabrique, "MANIFESTE", None)
                if isinstance(manifeste, Manifeste):
                    m = ModuleCharge(manifeste=manifeste, origine="paquet")
                    m.instance = None
                    m._classe = fabrique                   # type: ignore[attr-defined]
                    trouves.append(m)
            except Exception as exc:                       # noqa: BLE001
                from ..core.logging_setup import get_logger
                get_logger("modules").warning(
                    "Point d'entrée « %s » ignoré : %s", point.name, exc)
        return trouves

    def _lire_manifeste(self, fichier: str, dossier: str) -> Optional[Manifeste]:
        """Extrait le manifeste par analyse syntaxique, sans exécuter le code.

        On lit l'arbre du fichier et l'on cherche l'appel `Manifeste(...)`.
        Exécuter le module pour connaître son manifeste reviendrait à lui faire
        confiance avant de savoir s'il le mérite.
        """
        import ast
        try:
            with open(fichier, encoding="utf-8") as f:
                arbre = ast.parse(f.read(), fichier)
        except (OSError, SyntaxError) as exc:
            from ..core.logging_setup import get_logger
            get_logger("modules").error("« %s » illisible : %s", dossier, exc)
            return None

        for noeud in ast.walk(arbre):
            if not (isinstance(noeud, ast.Call)
                    and getattr(noeud.func, "id", "") == "Manifeste"):
                continue
            valeurs: Dict[str, Any] = {}
            for mc in noeud.keywords:
                valeur = self._evaluer(mc.value)
                if valeur is not _INEVALUABLE:
                    valeurs[mc.arg] = valeur
            if "nom" not in valeurs:
                valeurs["nom"] = dossier
            for champ in ("capacites", "depend_de", "exige"):
                if champ in valeurs and not isinstance(valeurs[champ], tuple):
                    valeurs[champ] = tuple(valeurs[champ] or ())
            try:
                return Manifeste(**valeurs)
            except TypeError as exc:
                from ..core.logging_setup import get_logger
                get_logger("modules").error(
                    "Manifeste de « %s » invalide : %s", dossier, exc)
                return None
        return None

    @staticmethod
    def _evaluer(noeud: Any) -> Any:
        """Évalue une valeur de manifeste sans exécuter le module.

        `ast.literal_eval` ne connaît que les littéraux. Or on écrit
        `capacites=(Capacite.ANALYSEUR,)`, qui est plus lisible qu'une chaîne
        nue et moins sujet aux fautes de frappe. On résout donc aussi les
        attributs de `Capacite`, qui sont des constantes du contrat — et rien
        d'autre : évaluer une expression quelconque reviendrait à exécuter le
        module, ce qu'on veut précisément éviter.
        """
        import ast as _ast
        if isinstance(noeud, _ast.Attribute):
            proprietaire = getattr(noeud.value, "id", "")
            if proprietaire == "Capacite":
                valeur = getattr(Capacite, noeud.attr, _INEVALUABLE)
                return valeur if isinstance(valeur, str) else _INEVALUABLE
            return _INEVALUABLE
        if isinstance(noeud, (_ast.Tuple, _ast.List)):
            elements = [Registre._evaluer(e) for e in noeud.elts]
            if any(e is _INEVALUABLE for e in elements):
                return _INEVALUABLE
            return tuple(elements)
        try:
            return _ast.literal_eval(noeud)
        except (ValueError, SyntaxError, TypeError):
            return _INEVALUABLE

    def _active(self, nom: str, manifeste: Manifeste) -> bool:
        """L'utilisateur veut-il de ce module ?

        Par défaut oui pour les modules intégrés, oui aussi pour ceux qu'il a
        posés lui-même — les poser est déjà un choix. Le fichier de réglages
        ne contient que les exceptions.
        """
        try:
            desactives = set(getattr(self._reglages.modules, "desactives", ()))
        except Exception:                                  # noqa: BLE001
            desactives = set()
        return nom not in desactives

    # -- chargement ----------------------------------------------------------
    def charger_tout(self) -> int:
        """Charge et installe tout ce qui est utilisable. Rend le compte."""
        if not self.modules:
            self.decouvrir()
        for nom in self._ordonner():
            self.charger(nom)
        actifs = 0
        for nom in self._ordre:
            if self._installer(nom):
                actifs += 1
        return actifs

    def _ordonner(self) -> List[str]:
        """Les dépendances d'abord, puis l'ordre alphabétique.

        Déterministe : deux démarrages donnent le même ordre. Un cycle de
        dépendances est signalé et rompu — on charge quand même, dans l'ordre
        alphabétique, plutôt que de ne rien charger du tout.
        """
        restants = {n: set(m.manifeste.depend_de) & set(self.modules)
                    for n, m in self.modules.items()}
        ordre: List[str] = []
        while restants:
            prets = sorted(n for n, d in restants.items() if not (d - set(ordre)))
            if not prets:
                cycle = ", ".join(sorted(restants))
                from ..core.logging_setup import get_logger
                get_logger("modules").error(
                    "Cycle de dépendances entre modules : %s — chargés dans "
                    "l'ordre alphabétique", cycle)
                ordre += sorted(restants)
                break
            ordre += prets
            for n in prets:
                restants.pop(n, None)
        self._ordre = ordre
        return ordre

    def charger(self, nom: str) -> bool:
        """Importe et instancie un module. Rend vrai si c'est fait."""
        m = self.modules.get(nom)
        if m is None or m.etat in (EtatModule.DESACTIVE,
                                   EtatModule.INCOMPATIBLE,
                                   EtatModule.EN_FAUTE):
            return False
        try:
            classe = self._classe_du_module(m)
            if classe is None:
                raise ImportError(
                    f"aucune classe héritant de Module dans « {nom} »")
            m.contexte = Contexte(nom, self._moteur, self._reglages,
                                  self.dossier_utilisateur())
            instance = classe(m.contexte)
            defauts = {}
            try:
                defauts = dict(instance.reglages_par_defaut() or {})
            except Exception:                              # noqa: BLE001
                pass
            defauts.update(self._reglages_enregistres(nom))
            m.contexte._poser_reglages(defauts)
            m.instance = instance
            m.etat = EtatModule.CHARGE
            return True
        except Exception as exc:                           # noqa: BLE001
            self._mettre_en_faute(m, "chargement", exc)
            return False

    def _classe_du_module(self, m: ModuleCharge) -> Optional[Type[Module]]:
        classe = getattr(m, "_classe", None)
        if classe is not None:
            return classe
        fichier = os.path.join(m.chemin, self.FICHIER_MODULE)
        nom_interne = f"phytoscope_module_{m.nom.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(nom_interne, fichier)
        if spec is None or spec.loader is None:
            raise ImportError(f"« {fichier} » n'est pas importable")
        paquet = importlib.util.module_from_spec(spec)
        #  Inscrit avant l'exécution : les `@dataclass` du module iraient
        #  chercher `sys.modules[cls.__module__]` et échoueraient sinon.
        sys.modules[nom_interne] = paquet
        spec.loader.exec_module(paquet)
        for objet in vars(paquet).values():
            if (isinstance(objet, type) and issubclass(objet, Module)
                    and objet is not Module):
                return objet
        return None

    def _installer(self, nom: str) -> bool:
        m = self.modules.get(nom)
        if m is None or m.etat != EtatModule.CHARGE or m.instance is None:
            return False
        try:
            m.instance.installer()
            m.etat = EtatModule.ACTIF
            return True
        except Exception as exc:                           # noqa: BLE001
            self._mettre_en_faute(m, "installation", exc)
            return False

    def _mettre_en_faute(self, m: ModuleCharge, etape: str,
                         exc: BaseException) -> None:
        """Désactive un module fautif, et dit pourquoi — une seule fois."""
        m.etat = EtatModule.EN_FAUTE
        m.faute = f"{type(exc).__name__} à l'{etape} : {exc}"
        m.trace = traceback.format_exc()
        from .events import BUS
        BUS.desabonner_module(m.nom)
        from ..core.logging_setup import get_logger
        log = get_logger("modules")
        log.error("Module « %s » désactivé — %s", m.nom, m.faute)
        log.debug("Trace du module « %s » :\n%s", m.nom, m.trace)

    # -- réglages ------------------------------------------------------------
    def _reglages_enregistres(self, nom: str) -> Dict[str, Any]:
        try:
            return dict(getattr(self._reglages.modules, "reglages", {}).get(nom, {}))
        except Exception:                                  # noqa: BLE001
            return {}

    def collecter_reglages(self) -> Dict[str, Dict[str, Any]]:
        """Ce qu'il faut enregistrer à la fermeture."""
        return {n: dict(m.contexte.reglages)
                for n, m in self.modules.items()
                if m.contexte is not None and m.contexte.reglages}

    # -- usage ---------------------------------------------------------------
    def actifs(self) -> List[ModuleCharge]:
        return [self.modules[n] for n in self._ordre
                if n in self.modules and self.modules[n].utilisable]

    def fournisseurs(self, capacite: str) -> List[ModuleCharge]:
        """Les modules actifs qui fournissent une capacité, dans l'ordre."""
        return [m for m in self.actifs() if m.fournit(capacite)]

    def appeler(self, m: ModuleCharge, methode: str, *args: Any,
                defaut: Any = None, **kwargs: Any) -> Any:
        """Appelle une méthode d'un module **sous protection**.

        C'est le seul chemin par lequel l'hôte touche à un module. Une faute
        désactive le module et rend `defaut` : l'appelant n'a pas à s'en
        soucier, et la séance continue.
        """
        if m.instance is None:
            return defaut
        try:
            return getattr(m.instance, methode)(*args, **kwargs)
        except Exception as exc:                           # noqa: BLE001
            self._mettre_en_faute(m, f"appel de « {methode} »", exc)
            return defaut

    def arreter_tout(self) -> None:
        """Arrête les modules, dans l'ordre inverse du chargement."""
        for nom in reversed(self._ordre):
            m = self.modules.get(nom)
            if m is None or m.instance is None:
                continue
            if m.etat == EtatModule.ACTIF:
                self.appeler(m, "arreter")
            if m.contexte is not None:
                m.contexte._desabonner_tout()
        from .events import BUS
        BUS.vider()

    # -- pour le diagnostic --------------------------------------------------
    def rapport(self) -> List[Dict[str, Any]]:
        """L'état de chaque module, pour l'onglet Diagnostic."""
        lignes = []
        for nom in (self._ordre or sorted(self.modules)):
            m = self.modules.get(nom)
            if m is None:
                continue
            lignes.append({
                "nom": nom,
                "titre": m.manifeste.titre,
                "version": m.manifeste.version,
                "api": m.manifeste.api,
                "origine": m.origine,
                "etat": m.etat,
                "capacites": ", ".join(m.manifeste.capacites),
                "faute": m.faute,
            })
        return lignes
