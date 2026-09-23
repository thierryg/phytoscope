# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/filenames.py
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

"""Fabriquer un nom de fichier qui passe partout.

Trois systèmes, trois façons de s'y prendre mal.

**macOS normalise les noms.** APFS et HFS+ enregistrent les noms de fichiers
en forme **NFD** — « é » y devient « e » suivi d'un accent combinant. Un nom
mémorisé en NFC dans un fichier JSON ne sera donc pas égal, caractère pour
caractère, à celui que renvoie `os.listdir()`, et une comparaison exacte
échoue. Un échantillon nommé « Basilic — mardi » deviendrait introuvable.

**Windows réserve des noms.** `CON`, `PRN`, `AUX`, `NUL`, `COM1` à `COM9`,
`LPT1` à `LPT9` désignent des périphériques depuis MS-DOS : aucun fichier ne
peut porter ces noms, même suivis d'une extension. Windows refuse par ailleurs
`< > : " / \\ | ? *`, et supprime silencieusement les points et espaces finaux
— si bien qu'un nom peut désigner un autre fichier que celui qu'on croit.

**Les trois refusent la chaîne vide.**

La parade est simple et se prend en amont : on translittère en ASCII. Un nom
de fichier n'est pas un titre — le titre lisible vit dans les métadonnées de
la séance, en Unicode et intact. Le nom sur le disque, lui, n'a qu'à être
stable, comparable et acceptable partout.
"""
from __future__ import annotations

import unicodedata

__all__ = ["assainir", "RESERVES_WINDOWS"]

#  Noms de périphériques hérités de MS-DOS, interdits même avec une extension.
RESERVES_WINDOWS = frozenset(
    ["con", "prn", "aux", "nul"]
    + [f"com{i}" for i in range(1, 10)]
    + [f"lpt{i}" for i in range(1, 10)]
)


def assainir(texte: str, defaut: str = "seance", longueur: int = 48) -> str:
    """Un nom de fichier sûr, en ASCII, identique sur les trois systèmes.

    :param defaut: ce qu'on rend quand il ne reste rien d'utilisable.
    :param longueur: coupe au-delà — les chemins ont eux aussi des limites,
        et 260 caractères restent la valeur par défaut sous Windows.
    """
    #  NFKD sépare la lettre de son accent ; on jette ensuite les accents.
    #  C'est ce qui rend le nom insensible à la normalisation d'APFS.
    decompose = unicodedata.normalize("NFKD", str(texte))
    sans_accent = "".join(c for c in decompose
                          if not unicodedata.combining(c))

    garde = []
    for c in sans_accent.strip().lower():
        if c.isascii() and c.isalnum():
            garde.append(c)
        elif c in " -_.":
            garde.append("-")
        #  Tout le reste — idéogrammes, cyrillique, ponctuation — disparaît
        #  plutôt que de produire un nom que le système d'accueil réécrira.

    sortie = "".join(garde).strip("-")
    while "--" in sortie:
        sortie = sortie.replace("--", "-")
    #  Windows ôte les points et espaces de fin sans prévenir : on le fait
    #  nous-mêmes, pour que le nom écrit soit le nom relu.
    sortie = sortie[:longueur].strip("-. ")

    if not sortie or sortie.split(".")[0] in RESERVES_WINDOWS:
        #  « nul.wav » n'existerait pas sous Windows ; on le désamorce.
        sortie = f"{sortie}-x" if sortie else defaut
    return sortie
