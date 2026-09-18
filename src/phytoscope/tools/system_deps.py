#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/system_deps.py
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

"""Affiche les paquets système à installer, pour CE système précisément.

Aucune dépendance : cet outil s'exécute avec le Python du système, avant
toute installation. Il reconnaît Debian, Ubuntu, Mint, Fedora, RHEL, CentOS,
Rocky, AlmaLinux, Arch, Manjaro, openSUSE, Alpine, macOS et Windows.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from phytoscope.core.platform_info import resume     # noqa: E402

if __name__ == "__main__":
    print()
    print(resume())
    print()
