#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/run.py
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

"""Lanceur : `python3 run.py` depuis ce répertoire, sans rien installer."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from phytoscope.__main__ import main            # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
