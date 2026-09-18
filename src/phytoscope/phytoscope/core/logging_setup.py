# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/logging_setup.py
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

"""Journalisation : un fichier, un niveau, et rien dans le terminal par défaut.

Principes retenus :

* **Par défaut, seul le niveau ERROR est journalisé.** Un instrument ne doit
  pas remplir le disque pendant une séance de huit heures.
* **La sortie va dans un fichier**, avec rotation : la console reste propre,
  et l'utilisateur qui signale un bogue a un fichier à joindre.
* Le niveau se change à chaud, depuis l'interface ou la ligne de commande,
  sans redémarrer l'acquisition.
* Le niveau DEBUG active en plus la journalisation des trames, qui est
  volumineuse et donc explicitement séparée.

Les messages sont en français, mais les niveaux gardent leurs noms
normalisés : c'est ce que cherchera quiconque lira le fichier.
"""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from typing import Optional

LOGGER_NAME = "phytoscope"
NIVEAUX = ("ERROR", "WARNING", "INFO", "DEBUG")
NIVEAUX_FR = {
    "ERROR": "Erreurs seulement (défaut)",
    "WARNING": "Erreurs et avertissements",
    "INFO": "Déroulement des opérations",
    "DEBUG": "Tout, y compris les trames",
}

FORMAT_FICHIER = "%(asctime)s  %(levelname)-8s  %(name)-28s  %(message)s"
FORMAT_CONSOLE = "%(levelname)-8s %(message)s"

class _RotationTolerante(logging.handlers.RotatingFileHandler):
    """Rotation qui ne fait pas perdre le journal quand elle échoue.

    Windows refuse de renommer un fichier qu'un autre processus tient ouvert.
    Deux instances de PhytoScope — ou une instance et un éditeur de texte
    laissé ouvert sur le journal — font alors échouer la rotation avec
    `PermissionError`, et la gestion d'erreur par défaut de `logging` déverse
    une trace sur `stderr` à **chaque** message suivant.

    Ici, on préfère continuer d'écrire dans le fichier courant, quitte à le
    laisser grossir au-delà de la taille prévue : un journal trop gros se
    supprime, un journal perdu ne se retrouve pas. `delay=True` retarde en
    outre l'ouverture au premier message, ce qui évite de verrouiller le
    fichier pour rien quand aucune erreur ne survient.
    """

    def doRollover(self) -> None:                      # noqa: N802 (API logging)
        try:
            super().doRollover()
        except OSError:
            #  On repart d'un flux ouvert ; sans quoi plus rien ne serait
            #  journalisé du tout.
            if self.stream is None:
                try:
                    self.stream = self._open()
                except OSError:                        # pragma: no cover
                    pass
            #  Et l'on cesse de réessayer à chaque message : la taille limite
            #  est relevée, la journalisation continue.
            self.maxBytes = 0


_configured = False
_file_handler: Optional[logging.Handler] = None
_console_handler: Optional[logging.Handler] = None
_current_path = ""


def get_logger(name: str = "") -> logging.Logger:
    """Journal d'un module : `get_logger(__name__)`."""
    if not name or name.startswith(LOGGER_NAME):
        return logging.getLogger(name or LOGGER_NAME)
    short = name.split(".", 1)[-1] if name.startswith("phytoscope.") else name
    return logging.getLogger(f"{LOGGER_NAME}.{short}")


def setup(settings=None, level: Optional[str] = None,
          path: Optional[str] = None, console: Optional[bool] = None) -> str:
    """Installe la journalisation ; renvoie le chemin du fichier.

    Peut être rappelée à tout moment : les gestionnaires sont remplacés, pas
    empilés.
    """
    global _configured, _file_handler, _console_handler, _current_path

    conf = getattr(settings, "logging", None)
    lvl = (level or getattr(conf, "level", "ERROR") or "ERROR").upper()
    if lvl not in NIVEAUX:
        lvl = "ERROR"
    to_file = getattr(conf, "to_file", True)
    to_console = console if console is not None else getattr(conf, "to_console", False)

    if path:
        log_path = path
    elif settings is not None and hasattr(settings, "log_path"):
        log_path = settings.log_path()
    else:
        from ..config import config_dir
        log_path = os.path.join(config_dir(), "phytoscope.log")

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.DEBUG)          # le filtrage se fait par gestionnaire
    logger.propagate = False

    if _file_handler is not None:
        logger.removeHandler(_file_handler)
        _file_handler.close()
        _file_handler = None
    if _console_handler is not None:
        logger.removeHandler(_console_handler)
        _console_handler = None

    if to_file:
        try:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            _file_handler = _RotationTolerante(
                log_path, maxBytes=getattr(conf, "max_bytes", 2_000_000),
                backupCount=getattr(conf, "backup_count", 3), encoding="utf-8",
                delay=True)
            _file_handler.setFormatter(logging.Formatter(FORMAT_FICHIER))
            _file_handler.setLevel(getattr(logging, lvl))
            logger.addHandler(_file_handler)
            _current_path = log_path
        except OSError:
            _current_path = ""

    if to_console:
        _console_handler = logging.StreamHandler(sys.stderr)
        _console_handler.setFormatter(logging.Formatter(FORMAT_CONSOLE))
        _console_handler.setLevel(getattr(logging, lvl))
        logger.addHandler(_console_handler)

    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    _configured = True
    logger.info("Journalisation installée — niveau %s, fichier %s",
                lvl, _current_path or "(aucun)")
    return _current_path


def set_level(level: str) -> str:
    """Change le niveau à chaud. Renvoie le niveau effectivement appliqué."""
    lvl = (level or "ERROR").upper()
    if lvl not in NIVEAUX:
        lvl = "ERROR"
    for h in (_file_handler, _console_handler):
        if h is not None:
            h.setLevel(getattr(logging, lvl))
    get_logger().log(getattr(logging, lvl), "Niveau de journalisation : %s", lvl)
    return lvl


def current_level() -> str:
    for h in (_file_handler, _console_handler):
        if h is not None:
            return logging.getLevelName(h.level)
    return "ERROR"


def log_path() -> str:
    return _current_path


def tail(lines: int = 200) -> str:
    """Les dernières lignes du journal — pour l'afficher dans l'interface."""
    if not _current_path or not os.path.exists(_current_path):
        return "(aucun fichier de journal)"
    try:
        with open(_current_path, encoding="utf-8", errors="replace") as f:
            content = f.readlines()
        return "".join(content[-lines:])
    except OSError as exc:                             # pragma: no cover
        return f"(lecture impossible : {exc})"


def clear() -> bool:
    """Vide le fichier de journal."""
    if not _current_path:
        return False
    try:
        open(_current_path, "w", encoding="utf-8").close()
        return True
    except OSError:                                    # pragma: no cover
        return False


def install_excepthook() -> None:
    """Toute exception non rattrapée finit dans le journal, pas dans le vide."""
    logger = get_logger()

    def hook(exc_type, exc_value, exc_tb):             # pragma: no cover
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logger.critical("Exception non rattrapée",
                        exc_info=(exc_type, exc_value, exc_tb))
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = hook
