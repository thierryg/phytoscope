# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/interrupt.py
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

"""Ctrl+C : tout arrêter, depuis le terminal, même en interface graphique.

Un programme lancé depuis un terminal doit s'arrêter quand on y tape Ctrl+C.
Cela va de soi en mode console ; cela ne va **pas** de soi derrière Qt, pour une
raison technique qu'il vaut mieux connaître : pendant ``app.exec()``, le fil
principal est bloqué dans la boucle d'événements écrite en C++, et l'interpréteur
Python n'exécute plus une seule instruction. Le signal est bien reçu par le
système, mais le gestionnaire Python ne s'exécute qu'au prochain retour dans du
code Python — c'est-à-dire jamais, tant qu'on ne touche pas à la fenêtre.

Trois mesures, donc :

1. un **chronomètre Qt** de 200 ms, dont la fonction ne fait rien : son seul rôle
   est de rendre la main à l'interpréteur assez souvent pour que le signal soit
   traité, y compris si l'utilisateur ne touche à rien ;
2. un **gestionnaire de signal** qui exécute les fonctions de nettoyage
   enregistrées — clore l'enregistrement, arrêter le moteur, sauver les
   réglages — puis demande à Qt de quitter ;
3. un **chien de garde** : si le nettoyage se bloque (une couche audio qui ne
   rend pas la main, un sous-processus de synthèse vocale qui traîne), le
   processus est terminé sans ménagement après quelques secondes. Un second
   Ctrl+C produit le même effet, immédiatement.

La règle qui gouverne tout cela : **un Ctrl+C doit toujours aboutir.** Un
logiciel qui, une fois interrompu, oblige à chercher son numéro de processus
n'est pas interruptible ; il est seulement poli.

SIGTERM reçoit le même traitement, car c'est ce que le système envoie à
l'extinction et ce qu'envoie ``kill`` sans argument : une séance de six heures
doit se refermer proprement quand la machine s'éteint.
"""
from __future__ import annotations

import os
import signal
import sys
import threading
from typing import Callable, List, Optional

from .logging_setup import get_logger

log = get_logger(__name__)

__all__ = ["installer", "ajouter_nettoyage", "interrompu", "DELAI_CHIEN_DE_GARDE"]

#  Délai laissé au nettoyage avant de terminer le processus de force.
DELAI_CHIEN_DE_GARDE = 6.0

_nettoyages: List[Callable[[], None]] = []
_recu = threading.Event()
_app = None
_code_sortie = 130                       # convention : 128 + SIGINT


def interrompu() -> bool:
    """Vrai dès qu'un Ctrl+C ou un SIGTERM a été reçu."""
    return _recu.is_set()


def ajouter_nettoyage(fonction: Callable[[], None]) -> None:
    """Enregistre une fonction à exécuter avant de quitter.

    Les fonctions sont appelées dans l'ordre d'enregistrement, chacune protégée :
    une qui échoue n'empêche pas les suivantes de s'exécuter. C'est voulu — le
    but est de sauver ce qui peut l'être, pas de réussir parfaitement.
    """
    if fonction is not None and fonction not in _nettoyages:
        _nettoyages.append(fonction)


def _nettoyer() -> None:
    for fonction in list(_nettoyages):
        try:
            fonction()
        except Exception:                              # noqa: BLE001
            log.exception("Nettoyage imparfait pendant l'interruption")


def _forcer() -> None:                                 # pragma: no cover
    """Sortie immédiate, sans passer par les gestionnaires de sortie.

    ``os._exit`` est délibéré : à ce stade, l'arrêt propre a déjà échoué ou a
    déjà eu lieu, et ``sys.exit`` ne ferait que relancer un déroulement de pile
    qui, lui aussi, peut se bloquer.
    """
    try:
        sys.stderr.write("\n  Arrêt forcé.\n")
        sys.stderr.flush()
    except Exception:                                  # noqa: BLE001
        pass
    os._exit(_code_sortie)


def _gestionnaire(signum, _frame):                     # pragma: no cover
    nom = "Ctrl+C" if signum == signal.SIGINT else f"signal {signum}"
    if _recu.is_set():
        # Deuxième demande : l'utilisateur a compris que ça traînait.
        _forcer()
    _recu.set()
    try:
        sys.stderr.write(f"\n  {nom} — arrêt en cours "
                         f"(Ctrl+C de nouveau pour forcer)…\n")
        sys.stderr.flush()
    except Exception:                                  # noqa: BLE001
        pass
    log.info("Interruption reçue (%s) : arrêt demandé.", nom)

    chien = threading.Timer(DELAI_CHIEN_DE_GARDE, _forcer)
    chien.daemon = True
    chien.start()

    _nettoyer()

    if _app is not None:
        try:
            _app.quit()
            return
        except Exception:                              # noqa: BLE001
            log.exception("Qt n'a pas voulu quitter")
            _forcer()
    # Sans interface : on rend l'interruption à la boucle principale, qui sait
    # déjà la traiter.
    raise KeyboardInterrupt


def installer(app=None, nettoyage: Optional[Callable[[], None]] = None,
              code_sortie: int = 130) -> bool:
    """Met en place l'interruption. Retourne False si ce n'est pas possible.

    Ce n'est pas possible dans un fil secondaire — ``signal.signal`` n'y est pas
    autorisé — et ce n'est alors pas grave : le fil principal a déjà installé ce
    qu'il fallait.

    :param app: l'application Qt, si l'on est en interface graphique.
    :param nettoyage: fonction d'arrêt propre, ajoutée aux autres.
    """
    global _app, _code_sortie
    _app = app if app is not None else _app
    _code_sortie = int(code_sortie)
    if nettoyage is not None:
        ajouter_nettoyage(nettoyage)

    try:
        signal.signal(signal.SIGINT, _gestionnaire)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _gestionnaire)
    except (ValueError, OSError, RuntimeError) as exc:
        log.debug("Gestionnaire de signal non installé : %s", exc)
        return False

    if app is not None:
        _reveiller_python(app)
    return True


def _reveiller_python(app) -> None:
    """Le chronomètre qui rend la main à Python pendant la boucle de Qt.

    200 ms : assez court pour qu'un Ctrl+C paraisse instantané, assez long pour
    ne rien coûter — la fonction appelée est vide, et elle l'est exprès.
    """
    try:
        from PySide6.QtCore import QTimer
    except Exception:                                  # noqa: BLE001  pragma: no cover
        log.debug("Qt indisponible : pas de réveil périodique.")
        return
    minuteur = QTimer(app)
    minuteur.setInterval(200)
    minuteur.timeout.connect(lambda: None)
    minuteur.start()
    #  Référence gardée sur l'application : sans cela, le ramasse-miettes
    #  détruirait le chronomètre et l'interruption redeviendrait inopérante.
    app._phytoscope_reveil = minuteur                   # noqa: SLF001
