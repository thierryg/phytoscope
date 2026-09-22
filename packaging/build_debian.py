#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/build_debian.py
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

"""Génère le paquet Debian (.deb) — Debian, Ubuntu, Mint.

Le paquet pose le logiciel dans `/usr/share/phytoscope`, un lanceur dans
`/usr/bin/phytoscope`, une entrée de menu et une icône, puis crée à
l'installation un environnement Python privé — voir `gabarits/debian/postinst`
pour le pourquoi.

Deux variantes : **légère** par défaut (340 ko, l'installation va chercher les
bibliothèques), et **hors ligne** avec `--hors-ligne` (335 Mo, tout est dedans,
pour un atelier sans réseau).

.. code-block:: console

    python3 packaging/build_debian.py [--hors-ligne]

Ce script est autonome : il ne dépend que de `common.py`, et se lance seul ou
par le Makefile du même dossier (`make debian`).
"""
from __future__ import annotations

import argparse
import os
import hashlib
import shutil
import sys
import tarfile
import tempfile
import time
import zipfile
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    GABARITS, GRIS, JAUNE, LOGICIEL, echec, PYTHONS_COUVERTS, RACINE_SORTIE, VERT, Identite,
    appliquer_les_arguments, arguments_communs, bien, copier_le_logiciel,
    dire, dossier_sortie, ecrire, ecrire_les_documents, ecrire_les_empreintes,
    etape, executer, icone_svg, lisible, remplir, souci, taille_ko,
    telecharger_les_roues, PYTHON_AUTONOME, _python_autonome)


def construire_deb(id_: Identite, embarquer: bool) -> Optional[str]:
    """Le paquet Debian, léger par défaut.

    Deux variantes, et le choix n'est pas anodin. Le paquet **léger** (340 ko)
    laisse le script d'après-installation aller chercher les bibliothèques :
    c'est le cas courant, puisqu'on installe un `.deb` par `apt`, donc en
    ligne. Le paquet **hors ligne** (`--hors-ligne`, 335 Mo) les embarque pour
    Python 3.9 à 3.13 : c'est ce qu'il faut pour un atelier ou une salle de
    classe sans réseau, où trente machines doivent s'installer d'une clé USB.
    """
    dire("\nPaquet Debian (.deb) — Debian, Ubuntu, Mint\n", JAUNE)
    if not shutil.which("dpkg-deb"):
        echec("dpkg-deb absent : sudo apt install dpkg-dev")
        return None

    with tempfile.TemporaryDirectory(prefix="phyto-deb-") as bac:
        racine = os.path.join(bac, "paquet")
        partage = os.path.join(racine, "usr", "share", "phytoscope")
        etape("copie du logiciel")
        copier_le_logiciel(partage)

        if embarquer:
            etape("roues Linux (installation hors ligne)")
            telecharger_les_roues("linux", os.path.join(partage, "roues"),
                                  PYTHONS_COUVERTS)

        ecrire(os.path.join(racine, "usr", "bin", "phytoscope"),
               open(os.path.join(GABARITS, "debian", "lanceur"),
                    encoding="utf-8").read(), executable=True)
        #  Deux outils que l'utilisateur appelle quand IL le décide : `apt` et
        #  `dnf` installent sans interaction, souvent sans session graphique.
        #  Poser la question de l'icône à ce moment-là serait la poser à la
        #  mauvaise personne.
        for outil, cible in (("desktop-icon.sh", "phytoscope-icone-bureau"),
                             ("uninstall.sh", "phytoscope-desinstaller")):
            ecrire(os.path.join(racine, "usr", "bin", cible),
                   open(os.path.join(GABARITS, "debian", outil),
                        encoding="utf-8").read(), executable=True)
        applications = os.path.join(racine, "usr", "share", "applications")
        os.makedirs(applications, exist_ok=True)
        shutil.copy2(os.path.join(GABARITS, "debian", "phytoscope.desktop"),
                     os.path.join(applications, "phytoscope.desktop"))
        ecrire(os.path.join(racine, "usr", "share", "icons", "hicolor",
                            "scalable", "apps", "phytoscope.svg"), icone_svg())

        valeurs = dict(id_.jetons(), ARCH="all",
                       TAILLE=str(taille_ko(racine)))
        ecrire(os.path.join(racine, "DEBIAN", "control"),
               remplir(os.path.join(GABARITS, "debian", "control"), valeurs))
        for script in ("postinst", "prerm"):
            ecrire(os.path.join(racine, "DEBIAN", script),
                   open(os.path.join(GABARITS, "debian", script),
                        encoding="utf-8").read(), executable=True)

        #  Le nom dit ce que le paquet contient : deux fichiers de 340 ko et
        #  de 335 Mo qui s'appelleraient pareil seraient une invitation à
        #  diffuser le mauvais.
        marque = "-horsligne" if embarquer else ""
        cible = os.path.join(dossier_sortie(id_, "Linux"),
                             f"phytoscope_{id_.version}{marque}_all.deb")
        etape("assemblage")
        #  fakeroot donne à tous les fichiers le propriétaire root:root sans
        #  exiger de privilèges : sans lui, dpkg-deb inscrirait l'utilisateur
        #  courant, et l'installation poserait des permissions étranges.
        prefixe = ["fakeroot"] if shutil.which("fakeroot") else []
        if not executer(prefixe + ["dpkg-deb", "--build", "--root-owner-group",
                                   racine, cible]):
            return None
    bien(f"{os.path.basename(cible)}  ({lisible(os.path.getsize(cible))})")
    return cible


def construire_run(id_: Identite, embarquer: bool = False) -> Optional[str]:
    """L'installateur autonome : un script et une archive dans un seul fichier.

    Le principe est celui des `.run` de NVIDIA ou de VMware, et c'est
    l'équivalent libre de ce que produit InstallShield : un en-tête `sh` suivi
    d'une archive compressée. Le shell lit l'en-tête, s'arrête à la dernière
    ligne connue, et le reste du fichier est déplié par `tar`.

    Pourquoi ce format en plus du `.deb` et du `.rpm` : il fonctionne sur les
    distributions qui n'ont ni l'un ni l'autre — Arch, openSUSE, Alpine,
    NixOS, Slackware — et surtout **il s'installe sans privilèges**. Lancé par
    un compte ordinaire, il se pose dans `~/.local/opt` et n'appelle jamais
    `sudo` : on n'élève pas les droits à l'insu de qui installe.

    Il porte l'empreinte SHA-256 de sa propre charge utile, qu'il vérifie
    avant d'écrire quoi que ce soit (`--check` la contrôle sans installer).
    """
    dire("\nInstallateur autonome (.run) — toutes distributions\n", JAUNE)

    with tempfile.TemporaryDirectory(prefix="phyto-run-") as bac:
        contenu = os.path.join(bac, "contenu")
        etape("copie du logiciel")
        copier_le_logiciel(contenu)
        ecrire(os.path.join(contenu, "phytoscope.svg"), icone_svg())

        #  L'interpréteur voyage avec l'installateur. Sans lui, le .run ne
        #  pouvait qu'échouer sur une machine nue en disant « installez
        #  python3 » — ce qui n'est pas « prêt après l'installation », et ce
        #  qui exige des privilèges que le projet s'interdit (C-55).
        #
        #  Ce sont des binaires RELOGEABLES : ils se déplient dans
        #  ~/.local/opt et fonctionnent sans être installés. L'installateur ne
        #  s'en sert QUE si aucun Python du système ne convient, et efface le
        #  double dans le cas contraire.
        etape(f"Python autonome {PYTHON_AUTONOME} (installation sur machine nue)")
        if not _python_autonome(os.path.join(contenu, "python"), "linux"):
            souci("l'installateur exigera un Python déjà présent")

        #  Les libellés de l'installateur, dans les onze languages. Ils sont
        #  extraits AVANT la décompression complète (`extraire_un langues`),
        #  parce que la langue est la première question posée — avant la
        #  licence, qui sera lue dans la langue choisie.
        etape("libellés de l'installateur (11 langues)")
        import languages as _langues
        _fichiers = _langues.ecrire_shell(os.path.join(contenu, "languages"))
        dire(f"      {len(_fichiers)} catalogues", GRIS)

        if embarquer:
            etape("roues Linux (installation hors ligne)")
            telecharger_les_roues("linux", os.path.join(contenu, "roues"),
                                  PYTHONS_COUVERTS)

        etape("archive")
        archive = os.path.join(bac, "charge.tar.gz")
        with tarfile.open(archive, "w:gz", compresslevel=9) as tar:
            for nom in sorted(os.listdir(contenu)):
                tar.add(os.path.join(contenu, nom), arcname=nom)

        with open(archive, "rb") as f:
            charge = f.read()
        somme = hashlib.sha256(charge).hexdigest()

        #  L'en-tête doit annoncer sa propre longueur en lignes, puisque c'est
        #  ainsi que le script retrouve le début de l'archive. On le remplit
        #  donc en deux temps : une première fois pour compter, une seconde
        #  avec le compte exact. Le jeton et sa valeur ayant la même longueur
        #  en lignes, le compte ne change pas entre les deux passes.
        #  La couche d'affichage vit dans son propre fichier : elle ne dépend
        #  pas de PhytoScope, et la garder à part rend les deux lisibles.
        #  La couche porte elle aussi des jetons (@VERSION@ dans son titre) :
        #  on les remplit AVANT de l'insérer, sans quoi ils survivraient à la
        #  substitution de l'en-tête, qui a déjà eu lieu à ce moment-là.
        couche = remplir(os.path.join(GABARITS, "linux", "frontend.sh"),
                         id_.jetons())

        valeurs = dict(id_.jetons(), EMPREINTE=somme, LIGNES="0",
                       COUCHE_INTERFACE=couche)
        entete = remplir(os.path.join(GABARITS, "linux", "header.sh"), valeurs)
        #  L'en-tête doit annoncer sa propre longueur en lignes : c'est ainsi
        #  que le script retrouve le début de l'archive. On le remplit donc
        #  deux fois — une première pour compter, une seconde avec le compte.
        #  Le jeton et sa valeur tenant sur une ligne, le compte ne bouge pas.
        valeurs["LIGNES"] = str(entete.count("\n"))
        entete = remplir(os.path.join(GABARITS, "linux", "header.sh"), valeurs)
        assert entete.count("\n") == int(valeurs["LIGNES"]), \
            "le remplissage a changé le nombre de lignes de l'en-tête"

        marque = "-horsligne" if embarquer else ""
        cible = os.path.join(dossier_sortie(id_, "Linux"),
                             f"PhytoScope-{id_.version}{marque}-Linux.run")
        with open(cible, "wb") as f:
            f.write(entete.encode("utf-8"))
            f.write(charge)
        os.chmod(cible, 0o755)

    #  Relire ce qu'on vient d'écrire : c'est le script lui-même qui sait
    #  vérifier son intégrité, autant le lui demander tout de suite.
    if not executer(["sh", cible, "--check"]):
        echec("l'installateur ne se relit pas lui-même")
        return None
    bien(f"{os.path.basename(cible)}  ({lisible(os.path.getsize(cible))})")
    return cible


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="build_debian.py",
        description="Fabrique le paquet Debian de PhytoScope.")
    arguments_communs(p)
    p.add_argument("--hors-ligne", action="store_true",
                   help="embarquer les bibliothèques (Python 3.9 à 3.13) pour "
                        "une installation sans connexion")
    p.add_argument("--sans-run", action="store_true",
                   help="ne pas produire l'installateur autonome .run")
    args = p.parse_args(argv)

    id_ = appliquer_les_arguments(args)
    dire(f"\n  PhytoScope {id_.version}-{id_.release} — Debian, Ubuntu, Mint", VERT)
    produits = [x for x in (construire_deb(id_, args.hors_ligne),
                            None if args.sans_run
                            else construire_run(id_, args.hors_ligne))
                if x]
    if produits:
        ecrire_les_empreintes(id_)
        ecrire_les_documents(id_)
    for f in produits:
        dire(f"    {os.path.relpath(f, RACINE_SORTIE)}", GRIS)
    return 0 if produits else 1


if __name__ == "__main__":
    sys.exit(main())
