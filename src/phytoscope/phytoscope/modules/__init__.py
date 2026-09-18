# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/modules/__init__.py
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

"""Les modules livrés avec le logiciel.

Chaque sous-dossier est un module, au même format que ceux qu'on écrit
soi-même : un `module.py`, une classe héritant de `api.Module`, un manifeste.
Aucun privilège, aucun raccourci — ils passent par la même API que tout le
monde, et c'est ce qui garantit que cette API suffit réellement.

Cette règle a une conséquence agréable : pour savoir comment écrire un module,
il suffit d'en lire un.

    descripteurs-avances   les six représentations du signal
    empreinte-montage      les descripteurs du montage et le registre
    export-csv             une séance en CSV, lisible par un tableur
    grandeurs-scientifiques  quinze quantités et ce qu'elles disent
"""
