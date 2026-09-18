# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/__init__.py
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

"""PhytoScope — écoute, mesure et enregistrement des signaux végétaux.

Logiciel compagnon de la carte PhytoSense One, mais utilisable avec
n'importe quelle source : carte du commerce, entrée microphone, fichier
déjà enregistré, ou générateur interne pour découvrir sans matériel.

    Bretagne Namasté — https://bretagne-namaste.com
    contact@bretagne-namaste.com — licence MIT
"""

from .version import (APP_NAME, APP_TAGLINE, AUTHOR, CONTACT, COPYRIGHT,
                      FULL_NAME, FULL_TITLE, LICENSE, RELEASE_DATE,
                      RELEASE_NAME, TITRE_VERSION, VERSION, VERSION_TUPLE,
                      WEBSITE, dependencies, environment_report, release_info)

__version__ = VERSION
__author__ = AUTHOR
__license__ = LICENSE
__contact__ = CONTACT
__url__ = WEBSITE

__all__ = ["APP_NAME", "APP_TAGLINE", "AUTHOR", "CONTACT", "COPYRIGHT",
           "FULL_NAME", "FULL_TITLE", "LICENSE", "RELEASE_DATE",
           "RELEASE_NAME", "TITRE_VERSION", "VERSION", "VERSION_TUPLE",
           "WEBSITE", "dependencies", "environment_report", "release_info",
           "__version__"]
