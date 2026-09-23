# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/audio_quiet.py
#
#  Version   : 1.6.0
#  Date      : 2026-09-23
#  Publisher : Bretagne Namasté
#  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Website   : https://bretagne-namaste.com
#  Contact   : contact@bretagne-namaste.com
#  License   : MIT — see LICENSE.txt
#
#  SPDX-License-Identifier: MIT
#  end of attribution
#  ==========================================================================

"""Faire taire le bavardage des couches audio bas niveau.

Sous GNU/Linux, ALSA, JACK et PortAudio écrivent directement sur la sortie
d'erreur du processus, en C, sans passer par Python. Un message comme

    ALSA lib pcm.c:8568:(snd_pcm_recover) underrun occurred

n'est donc pas journalisable par les moyens ordinaires : au moment où il
s'affiche, aucun code Python n'est en cours d'exécution. Deux mécanismes sont
nécessaires, et ils sont complémentaires.

**Le gestionnaire d'erreurs d'ALSA.** La bibliothèque expose
``snd_lib_error_set_handler``, qui permet de lui fournir sa propre fonction
d'affichage. On lui en donne une qui, au lieu d'écrire sur le terminal,
transmet au journal de l'application. Rien n'est perdu : les messages
deviennent consultables au niveau DEBUG, et invisibles au niveau par défaut.

**La redirection du descripteur 2.** PortAudio et JACK écrivent, eux,
directement sur le descripteur de fichier. On le redirige donc vers le néant
pendant l'ouverture du flux — et pendant elle seule, afin de ne jamais perdre
une erreur qui viendrait d'ailleurs.

Sous Windows et macOS, ces couches sont silencieuses : le module ne fait alors
rien du tout, et c'est voulu.
"""
from __future__ import annotations

import contextlib
import ctypes
import os
import sys
from typing import Optional

from .logging_setup import get_logger

log = get_logger(__name__)

# La fonction de rappel doit survivre aussi longtemps qu'ALSA l'utilise :
# si le ramasse-miettes la reprend, le processus se termine brutalement.
_handler_ref = None
_installe = False
_messages = 0


def _installer_gestionnaire_alsa() -> bool:
    """Détourne les messages d'ALSA vers le journal. Renvoie True si posé."""
    global _handler_ref, _installe

    if _installe or not sys.platform.startswith("linux"):
        return _installe

    # int snd_lib_error_set_handler(snd_lib_error_handler_t handler)
    # void handler(const char *file, int line, const char *function,
    #              int err, const char *fmt, ...)
    prototype = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int,
                                 ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)

    def _vers_le_journal(fichier, ligne, fonction, err, fmt):
        global _messages
        _messages += 1
        try:
            log.debug("ALSA %s:%s(%s) err=%s : %s",
                      (fichier or b"?").decode("utf-8", "replace"), ligne,
                      (fonction or b"?").decode("utf-8", "replace"), err,
                      (fmt or b"").decode("utf-8", "replace"))
        except Exception:                              # pragma: no cover
            pass

    try:
        asound = ctypes.cdll.LoadLibrary("libasound.so.2")
        _handler_ref = prototype(_vers_le_journal)
        asound.snd_lib_error_set_handler(_handler_ref)
        _installe = True
        log.info("Messages ALSA détournés vers le journal (niveau DEBUG).")
    except OSError as exc:
        log.debug("libasound introuvable, rien à faire : %s", exc)
    except Exception as exc:                           # pragma: no cover
        log.warning("Gestionnaire ALSA non installé : %s", exc)
    return _installe


def installer() -> bool:
    """À appeler une fois au démarrage, avant d'ouvrir le moindre flux."""
    return _installer_gestionnaire_alsa()


def messages_captes() -> int:
    """Nombre de messages ALSA détournés depuis le démarrage.

    C'est un indicateur utile : un chiffre qui grimpe pendant une séance
    signale que la sortie sonore peine, même si plus rien ne s'affiche.
    """
    return _messages


@contextlib.contextmanager
def sans_bavardage(actif: bool = True):
    """Étouffe le descripteur d'erreur du processus, le temps d'un bloc.

    Réservé à l'ouverture des flux : PortAudio et JACK y écrivent des pages
    d'avertissements sans conséquence. Les erreurs Python, elles, ne passent
    pas par ce descripteur et restent donc visibles.
    """
    if not actif or not sys.platform.startswith("linux"):
        yield
        return

    copie: Optional[int] = None
    devnull: Optional[int] = None
    try:
        sys.stderr.flush()
        copie = os.dup(2)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, 2)
        yield
    except Exception:
        raise
    finally:
        try:
            if copie is not None:
                os.dup2(copie, 2)
                os.close(copie)
            if devnull is not None:
                os.close(devnull)
        except OSError:                                # pragma: no cover
            pass
