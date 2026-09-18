# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/errors.py
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

"""Gestion des erreurs — une hiérarchie, des décorateurs, et aucune exception muette.

Règles suivies dans tout le logiciel :

1. **Une exception ne disparaît jamais.** Elle est soit traitée, soit
   journalisée, soit remontée ; jamais avalée par un `except: pass`.
2. **Le fil d'acquisition ne meurt pas.** Une erreur dans un consommateur
   (affichage, MIDI, disque) ne doit pas interrompre la mesure : ces appels
   sont protégés par `@resilient`.
3. **Les messages sont destinés à l'utilisateur.** Chaque exception porte un
   message en français, une cause technique, et si possible un remède.
4. **Les codes de sortie sont normalisés** : le mode sans interface est
   scriptable, donc ses codes doivent être stables.

Le type `Result` évite les exceptions dans les chemins où l'échec est un
résultat normal (périphérique absent, fichier illisible) plutôt qu'un bogue.
"""
from __future__ import annotations

import functools
import traceback
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Callable, Generic, Optional, TypeVar

from .logging_setup import get_logger

log = get_logger(__name__)

T = TypeVar("T")


# ---------------------------------------------------------------------------
#  Codes de sortie
# ---------------------------------------------------------------------------
class ExitCode(IntEnum):
    """Codes de retour du programme — stables, documentés, scriptables."""
    OK = 0
    ERREUR_GENERALE = 1
    DEPENDANCE_MANQUANTE = 2
    MATERIEL_ABSENT = 3
    CONFIGURATION_INVALIDE = 4
    ECRITURE_IMPOSSIBLE = 5
    INTERROMPU = 130


# ---------------------------------------------------------------------------
#  Hiérarchie d'exceptions
# ---------------------------------------------------------------------------
class PhytoScopeError(Exception):
    """Exception de base : message utilisateur + cause technique + remède."""

    exit_code = ExitCode.ERREUR_GENERALE

    def __init__(self, message: str, cause: str = "", remede: str = ""):
        super().__init__(message)
        self.message = message
        self.cause = cause
        self.remede = remede

    def __str__(self) -> str:
        parties = [self.message]
        if self.cause:
            parties.append(f"Cause : {self.cause}")
        if self.remede:
            parties.append(f"Remède : {self.remede}")
        return "\n".join(parties)

    def as_dict(self) -> dict:
        return {"type": type(self).__name__, "message": self.message,
                "cause": self.cause, "remede": self.remede,
                "code": int(self.exit_code)}


class DependanceManquante(PhytoScopeError):
    """Une bibliothèque nécessaire n'est pas installée."""
    exit_code = ExitCode.DEPENDANCE_MANQUANTE

    def __init__(self, module: str, role: str = "", paquet: str = ""):
        paquet = paquet or module
        super().__init__(
            f"La bibliothèque « {module} » est nécessaire" +
            (f" pour {role}" if role else "") + ".",
            cause=f"module Python « {module} » introuvable",
            remede=f"python3 -m pip install {paquet}   (ou : make install)")
        self.module = module
        self.paquet = paquet


class SourceIndisponible(PhytoScopeError):
    """La source de signal demandée ne peut pas être ouverte."""
    exit_code = ExitCode.MATERIEL_ABSENT


class ConfigurationInvalide(PhytoScopeError):
    """Un réglage est hors des bornes admissibles."""
    exit_code = ExitCode.CONFIGURATION_INVALIDE


class EcritureImpossible(PhytoScopeError):
    """Un fichier ou un répertoire n'a pas pu être écrit."""
    exit_code = ExitCode.ECRITURE_IMPOSSIBLE


class ProtocoleInvalide(PhytoScopeError):
    """La carte a répondu quelque chose d'inattendu."""


# ---------------------------------------------------------------------------
#  Résultat explicite
# ---------------------------------------------------------------------------
@dataclass
class Result(Generic[T]):
    """Succès ou échec, sans exception — pour les échecs « normaux ».

        r = ouvrir_port("/dev/ttyACM0")
        if r:
            utiliser(r.value)
        else:
            afficher(r.error)
    """
    value: Optional[T] = None
    error: str = ""
    detail: str = ""
    remede: str = ""

    def __bool__(self) -> bool:
        return not self.error

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        return cls(value=value)

    @classmethod
    def fail(cls, error: str, detail: str = "", remede: str = "") -> "Result[T]":
        log.debug("Échec : %s (%s)", error, detail)
        return cls(error=error, detail=detail, remede=remede)

    def unwrap(self) -> T:
        if self.error:
            raise PhytoScopeError(self.error, self.detail, self.remede)
        return self.value               # type: ignore[return-value]

    def or_else(self, default: T) -> T:
        return self.value if not self.error else default   # type: ignore[return-value]


# ---------------------------------------------------------------------------
#  Décorateurs
# ---------------------------------------------------------------------------
def resilient(default: Any = None, message: str = "",
              reraise: bool = False) -> Callable:
    """Protège un appel dont l'échec ne doit pas arrêter la mesure.

    Toute exception est journalisée avec sa pile, puis `default` est renvoyé.
    À réserver aux consommateurs (affichage, MIDI, disque) : jamais au cœur
    du traitement, où une erreur doit être visible.
    """
    def decorateur(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def enveloppe(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as exc:                   # noqa: BLE001
                log.error("%s%s : %s", message or fn.__qualname__,
                          " (ignoré)" if not reraise else "", exc)
                log.debug("Pile :\n%s", traceback.format_exc())
                if reraise:
                    raise
                return default
        return enveloppe
    return decorateur


def require(module: str, role: str = "", paquet: str = "") -> Callable:
    """Vérifie une dépendance avant d'entrer dans la fonction."""
    def decorateur(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def enveloppe(*args, **kwargs):
            import importlib
            try:
                importlib.import_module(module)
            except ImportError as exc:
                raise DependanceManquante(module, role, paquet) from exc
            return fn(*args, **kwargs)
        return enveloppe
    return decorateur


def validate_range(nom: str, valeur: float, mini: float, maxi: float) -> float:
    """Borne une valeur en journalisant toute correction — jamais silencieuse."""
    if valeur < mini or valeur > maxi:
        borne = min(max(valeur, mini), maxi)
        log.warning("Réglage « %s » hors bornes (%.6g) : ramené à %.6g "
                    "[%.6g … %.6g]", nom, valeur, borne, mini, maxi)
        return borne
    return valeur


class ErrorCollector:
    """Accumule les erreurs d'une opération longue sans l'interrompre.

    Utilisé au démarrage et pendant les diagnostics : on veut la liste
    complète des problèmes, pas seulement le premier.
    """

    def __init__(self, titre: str = ""):
        self.titre = titre
        self.erreurs: list[str] = []
        self.avertissements: list[str] = []

    def erreur(self, texte: str) -> None:
        self.erreurs.append(texte)
        log.error("%s%s", f"[{self.titre}] " if self.titre else "", texte)

    def avertir(self, texte: str) -> None:
        self.avertissements.append(texte)
        log.warning("%s%s", f"[{self.titre}] " if self.titre else "", texte)

    @property
    def ok(self) -> bool:
        return not self.erreurs

    def resume(self) -> str:
        if self.ok and not self.avertissements:
            return "Aucun problème."
        lignes = []
        for e in self.erreurs:
            lignes.append(f"  ✗ {e}")
        for a in self.avertissements:
            lignes.append(f"  ! {a}")
        return "\n".join(lignes)
