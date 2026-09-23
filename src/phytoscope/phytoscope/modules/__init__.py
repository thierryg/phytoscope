# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/__init__.py
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

"""Les modules livrés avec le logiciel.

Chaque sous-dossier est un module, au même format que ceux qu'on écrit
soi-même : un `module.py`, une classe héritant de `api.Module`, un manifeste.
Aucun privilège, aucun raccourci — ils passent par la même API que tout le
monde, et c'est ce qui garantit que cette API suffit réellement.

Cette règle a une conséquence agréable : pour savoir comment écrire un module,
il suffit d'en lire un.

    advanced-descriptors   les six représentations du signal
    rig-fingerprint      les descripteurs du montage et le registre
    export-csv             une séance en CSV, lisible par un tableur
    scientific-quantities  quinze quantités et ce qu'elles disent
"""
