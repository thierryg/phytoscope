#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/certificate.py
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

"""Crée, recrée et dépose le certificat qui signe les paquets.

C'est le point d'entrée unique pour tout ce qui touche au certificat. La
cryptographie elle-même vit dans `signature.py`, qui sait déjà fabriquer une
clé et un certificat X.509 auto-signé ; ce script ne la refait pas — il
l'appelle, et s'occupe de ce que `signature.py` ne fait pas : **remplir le
dossier `certificate/` du dépôt**.

Deux endroits, et pourquoi
--------------------------

| Où | Quoi | Dans le dépôt ? |
|---|---|---|
| `~/.local/share/phytoscope-signature/` | la copie de **référence** : clé privée + certificat | non, et jamais |
| `certificate/` | la copie de **travail** : le certificat public, le `.crt`, et la clé en 0600 | le public oui, la clé **jamais** |

La contrainte `C-2R` n'autorise la clé privée qu'à ces deux endroits. Le
`.gitignore` écarte `certificate/phytoscope.key` nommément, le crochet
`pre-commit` la refuse sur son seul nom, et le job « secrets » de
l'intégration continue échoue si elle apparaît. Trois filets, parce qu'une
clé publiée ne se dépublie pas.

Ce que ce script ne fait jamais
-------------------------------

**Il ne refait pas le certificat de lui-même.** Régénérer la clé rompt le
lien avec tout ce qui a déjà été signé : les paquets publiés deviennent
invérifiables avec le nouveau certificat, et qui avait noté l'empreinte en
voit soudain une autre. `--refaire` l'exige explicitement, et demande
confirmation.

**Il n'affiche jamais la clé privée**, ni ne la recopie ailleurs que dans les
deux emplacements ci-dessus.

Usage :
    python3 packaging/certificate.py                 l'état, sans rien changer
    python3 packaging/certificate.py --creer         créer s'il n'existe pas
    python3 packaging/certificate.py --deposer       remplir certificate/
    python3 packaging/certificate.py --refaire       REMPLACER (rompt le lien)
    python3 packaging/certificate.py --verifier      cohérence des deux copies

Ou par le Makefile :
    make certificate        crée s'il n'existe pas, puis remplit certificate/
    make certificate-status   l'état
    make certificate-renew REMPLACE, après confirmation
"""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (GRIS, JAUNE, RACINE, ROUGE, VERT, Identite,  # noqa: E402
                    bien, dire, echec, ecrire, etape, souci)
import signature  # noqa: E402

#  Le dossier du dépôt qui porte la copie de travail.
DOSSIER = os.path.join(RACINE, "certificate")
PUBLIC = os.path.join(DOSSIER, "phytoscope-certificate.pem")
CRT = os.path.join(DOSSIER, "phytoscope.crt")
CLE_TRAVAIL = os.path.join(DOSSIER, "phytoscope.key")
NOTICE = os.path.join(DOSSIER, "README.md")


# ---------------------------------------------------------------------------
#  État
# ---------------------------------------------------------------------------
def etat() -> bool:
    """Affiche ce qui existe et où ; rend True si tout est en place."""
    dire("\nCertificat de signature\n", JAUNE)

    reference = signature.certificat_existe()
    dire("  Copie de référence — ~/.local/share/phytoscope-signature/", GRIS)
    _ligne("clé privée", signature.CLE, secrete=True)
    _ligne("certificat", signature.CERTIFICAT)

    dire("\n  Copie de travail — certificate/", GRIS)
    _ligne("certificat public", PUBLIC)
    _ligne("certificat (.crt)", CRT)
    _ligne("clé privée", CLE_TRAVAIL, secrete=True)
    _ligne("notice", NOTICE)

    if reference:
        empreinte = signature.empreinte_certificat()
        if empreinte:
            dire(f"\n  Empreinte SHA-256 : {empreinte}", GRIS)
            dire("  C'est elle qu'on publie, et qu'on compare.", GRIS)
        sujet = _sujet()
        if sujet:
            dire(f"  Sujet             : {sujet}", GRIS)
        fin = _expiration()
        if fin:
            dire(f"  Valable jusqu'au  : {fin}", GRIS)
    else:
        dire("")
        souci("aucun certificat : les paquets ne pourront pas être signés")
        dire("      python3 packaging/certificate.py --creer", GRIS)

    complet = reference and all(os.path.exists(f) for f in (PUBLIC, CRT))
    dire("")
    return complet


def _ligne(libelle: str, chemin: str, secrete: bool = False) -> None:
    if not os.path.exists(chemin):
        dire(f"    [ ]  {libelle:<18} absent", GRIS)
        return
    #  On ne montre jamais le contenu d'une clé, pas même sa taille exacte —
    #  seulement qu'elle est là et que ses droits sont corrects.
    if secrete:
        mode = stat.S_IMODE(os.stat(chemin).st_mode)
        droits = "0600" if mode == 0o600 else f"{mode:04o}"
        marque = "✓" if mode == 0o600 else "!"
        dire(f"    [{marque}]  {libelle:<18} présente, droits {droits}",
             GRIS if mode == 0o600 else JAUNE)
        return
    taille = os.path.getsize(chemin)
    dire(f"    [✓]  {libelle:<18} {taille} octets", GRIS)


def _openssl(*args: str) -> str:
    try:
        r = subprocess.run(["openssl", *args], capture_output=True, text=True,
                           timeout=15)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _sujet() -> str:
    s = _openssl("x509", "-in", signature.CERTIFICAT, "-noout", "-subject")
    return s.split("=", 1)[-1].strip() if "=" in s else s


def _expiration() -> str:
    s = _openssl("x509", "-in", signature.CERTIFICAT, "-noout", "-enddate")
    return s.split("=", 1)[-1].strip() if "=" in s else s


# ---------------------------------------------------------------------------
#  Dépôt de la copie de travail
# ---------------------------------------------------------------------------
def deposer(id_: Optional[Identite] = None) -> bool:
    """Remplit `certificate/` depuis la copie de référence.

    Rien n'est fabriqué ici : on recopie, et l'on écrit la notice. Si la
    référence manque, on le dit plutôt que de créer une clé à l'improviste —
    créer une clé est une décision, pas un effet de bord.
    """
    if not signature.certificat_existe():
        echec("aucune copie de référence — rien à déposer")
        dire("      python3 packaging/certificate.py --creer", GRIS)
        return False

    id_ = id_ or Identite.lire()
    os.makedirs(DOSSIER, exist_ok=True)

    etape("certificat public (avec son en-tête et son empreinte)")
    #  `signature.deposer_dans_le_projet` écrit le PEM commenté : on le
    #  réutilise plutôt que de réécrire l'en-tête, qui porte l'empreinte et
    #  la commande de vérification.
    if not signature.deposer_dans_le_projet(id_):
        echec("dépôt du certificat public impossible")
        return False

    etape("certificat brut (.crt), pour les outils qui l'exigent")
    shutil.copy2(signature.CERTIFICAT, CRT)

    #  La clé de travail : autorisée ici et seulement ici (C-2R), en 0600,
    #  et écartée du dépôt par trois filets. On la recopie parce que la
    #  fabrique la cherche à cet endroit quand la référence est absente —
    #  sur une machine de secours, par exemple.
    etape("clé privée — copie de travail, en 0600, hors du dépôt")
    shutil.copy2(signature.CLE, CLE_TRAVAIL)
    os.chmod(CLE_TRAVAIL, 0o600)

    etape("notice")
    ecrire(NOTICE, _notice(id_))

    bien(f"certificate/ rempli — {os.path.relpath(DOSSIER, RACINE)}")
    souci("la clé privée qui s'y trouve ne doit JAMAIS être publiée")
    dire("      .gitignore l'écarte, pre-commit la refuse, la CI échoue "
         "si elle apparaît.", GRIS)
    return True


def _notice(id_: Identite) -> str:
    empreinte = signature.empreinte_certificat() or "(indéterminée)"
    return f"""# Le certificat de signature

Ce dossier porte la **copie de travail** du certificat qui signe les paquets
de PhytoScope. La copie de référence, elle, vit dans
`~/.local/share/phytoscope-signature/` et n'entre jamais dans le dépôt.

> **FICHIER GÉNÉRÉ** par `packaging/certificate.py`. Le modifier à la main
> serait perdu à la prochaine exécution (`C-45`).

## Ce qu'il y a ici

| Fichier | Nature | Dans le dépôt ? |
|---|---|---|
| `phytoscope-certificate.pem` | certificat **public**, commenté | **oui** — c'est lui qu'on diffuse |
| `phytoscope.crt` | le même, brut | **oui** |
| `phytoscope.key` | **la clé privée** | **non, jamais** |
| `README.md` | ce fichier | oui |

Le certificat public **doit** se diffuser : c'est lui qui permet de vérifier
une signature. Le taire rendrait les signatures invérifiables.

## Empreinte SHA-256

```
{empreinte}
```

C'est ce qu'on publie sur {id_.site} et ce que compare qui veut s'assurer
qu'un paquet vient bien de nous.

## Trois filets contre la publication de la clé

1. `.gitignore` écarte `certificate/phytoscope.key` nommément, puis `*.key`
   et `*.pem` partout, avec deux exceptions nommées pour les fichiers
   publics ;
2. le crochet `pre-commit` « detect-signing-key » la refuse **sur son seul
   nom** — même vide, même renommée ;
3. le job « secrets » de l'intégration continue échoue si un fichier de ce
   genre est suivi.

Trois filets parce qu'une clé publiée ne se dépublie pas.

> `.gitignore` protège de `git`, **pas d'une sauvegarde ni d'une archive du
> dossier**. Si vous archivez ce dépôt, excluez `certificate/phytoscope.key`.

## Recréer, déposer, vérifier

```bash
python3 packaging/certificate.py              # l'état, sans rien changer
python3 packaging/certificate.py --creer      # créer s'il n'existe pas
python3 packaging/certificate.py --deposer    # re-remplir ce dossier
python3 packaging/certificate.py --verifier   # les deux copies concordent ?
```

**Ne refaites pas le certificat sans raison.** `--refaire` remplace la clé, et
rompt le lien avec tout ce qui a déjà été signé : les paquets publiés
deviennent invérifiables avec le nouveau certificat, et qui avait noté
l'empreinte en voit soudain une autre.

## Ce que ce certificat prouve, et ce qu'il ne prouve pas

Il est **auto-signé**. Il prouve l'**intégrité** d'un paquet et la
**continuité d'origine** : deux paquets signés par la même clé viennent bien
du même endroit.

Il ne fait **pas** taire SmartScreen sous Windows ni Gatekeeper sous macOS,
et n'a jamais prétendu le faire (`C-2Q`). Cela demanderait un certificat
d'une autorité reconnue, payant et nominatif.

---

{id_.editeur} — {id_.auteur} — {id_.site}
"""


# ---------------------------------------------------------------------------
#  Création
# ---------------------------------------------------------------------------
def creer(id_: Optional[Identite] = None, refaire: bool = False,
          sans_question: bool = False) -> bool:
    """Crée le certificat s'il manque, puis remplit `certificate/`."""
    id_ = id_ or Identite.lire()

    if refaire and signature.certificat_existe():
        dire("")
        souci("REMPLACER le certificat rompt le lien avec tout ce qui a été "
              "signé auparavant.")
        dire("      Les paquets déjà publiés ne seront plus vérifiables avec",
             GRIS)
        dire("      le nouveau certificat, et qui avait noté l'empreinte", GRIS)
        dire(f"      {signature.empreinte_certificat()}", GRIS)
        dire("      en verra soudain une autre.", GRIS)
        dire("")
        if not sans_question and not _confirmer():
            dire("  Annulé — le certificat existant est conservé.\n")
            return False

    if not signature.generer_certificat(id_, refaire=refaire):
        return False
    return deposer(id_)


def _confirmer() -> bool:
    """Demande une confirmation explicite ; refuse si l'on n'est pas devant.

    Sans terminal — dans un script, dans l'intégration continue —, on refuse
    plutôt que de supposer un accord : remplacer une clé de signature n'est
    pas une chose qu'on fait par défaut.
    """
    if not sys.stdin.isatty():
        souci("pas de terminal : refusé. Ajoutez --oui si c'est bien voulu.")
        return False
    try:
        reponse = input("  Taper « REMPLACER » pour confirmer : ")
    except (EOFError, KeyboardInterrupt):
        return False
    return reponse.strip() == "REMPLACER"


# ---------------------------------------------------------------------------
#  Vérification
# ---------------------------------------------------------------------------
def verifier() -> bool:
    """Les deux copies portent-elles bien le même certificat ?"""
    dire("\nCohérence des deux copies\n", JAUNE)
    fautes = 0

    if not signature.certificat_existe():
        echec("copie de référence absente")
        return False

    reference = _empreinte_fichier(signature.CERTIFICAT)
    bien(f"référence : {reference}")

    for libelle, chemin in (("certificat public", PUBLIC), ("certificat .crt", CRT)):
        if not os.path.exists(chemin):
            souci(f"{libelle} absent de certificate/")
            fautes += 1
            continue
        empreinte = _empreinte_fichier(chemin)
        if empreinte == reference:
            bien(f"{libelle} : concorde")
        else:
            echec(f"{libelle} : NE CONCORDE PAS ({empreinte})")
            fautes += 1

    #  Les droits de la clé de travail : une clé lisible par tous n'est plus
    #  une clé.
    if os.path.exists(CLE_TRAVAIL):
        mode = stat.S_IMODE(os.stat(CLE_TRAVAIL).st_mode)
        if mode == 0o600:
            bien("clé de travail : droits 0600")
        else:
            echec(f"clé de travail : droits {mode:04o} — attendu 0600")
            dire(f"      chmod 600 {os.path.relpath(CLE_TRAVAIL, RACINE)}", GRIS)
            fautes += 1

    dire("")
    if fautes:
        dire(f"  {fautes} écart(s) — « --deposer » les corrige.\n", ROUGE)
    else:
        dire("  Les deux copies concordent.\n", VERT)
    return not fautes


def _empreinte_fichier(chemin: str) -> str:
    """L'empreinte du certificat contenu, et non celle du fichier.

    Le `.pem` du dépôt porte un en-tête commenté que le `.crt` n'a pas :
    comparer les fichiers octet par octet signalerait un écart qui n'existe
    pas. On compare donc ce qu'openssl en lit.
    """
    s = _openssl("x509", "-in", chemin, "-noout", "-fingerprint", "-sha256")
    return s.split("=", 1)[-1].strip() if "=" in s else "(illisible)"


# ---------------------------------------------------------------------------
#  Ce que la fabrique appelle quand le certificat manque
# ---------------------------------------------------------------------------
def proposer_si_absent(sans_question: bool = False) -> bool:
    """Propose de créer le certificat s'il manque ; rend True s'il est là.

    Appelée par la fabrique avant de signer. Elle **propose** au lieu de
    créer d'autorité : fabriquer une clé de signature dans le dos de qui
    lance un `make` est le genre de surprise qu'on ne veut pas — et sur une
    machine d'intégration continue, c'est une clé éphémère qu'on croirait
    permanente.
    """
    if signature.certificat_existe():
        return True

    dire("")
    souci("aucun certificat de signature : les paquets ne seront pas signés.")
    dire("      La copie de référence est attendue dans", GRIS)
    dire(f"      {signature.MAGASIN}", GRIS)
    dire("")

    if sans_question or not sys.stdin.isatty():
        dire("      Pour en créer un :", GRIS)
        dire("          make certificate", GRIS)
        dire("      ou  python3 packaging/certificate.py --creer", GRIS)
        dire("")
        return False

    try:
        reponse = input("  En créer un maintenant ? [o/N] ")
    except (EOFError, KeyboardInterrupt):
        dire("")
        return False
    if reponse.strip().lower() not in ("o", "oui", "y", "yes"):
        dire("      Sans certificat, « make all » produira des paquets non "
             "signés.", GRIS)
        dire("      Pour en créer un plus tard : make certificate", GRIS)
        dire("")
        return False

    return creer()


# ---------------------------------------------------------------------------
#  Ligne de commande
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="certificate.py",
        description="Crée, recrée et dépose le certificat de signature.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Sans option : affiche l'état, sans rien changer.")
    p.add_argument("--creer", action="store_true",
                   help="créer le certificat s'il n'existe pas, "
                        "puis remplir certificate/")
    p.add_argument("--deposer", action="store_true",
                   help="remplir certificate/ depuis la copie de référence")
    p.add_argument("--refaire", action="store_true",
                   help="REMPLACER le certificat existant — rompt le lien "
                        "avec tout ce qui a déjà été signé")
    p.add_argument("--verifier", action="store_true",
                   help="les deux copies portent-elles le même certificat ?")
    p.add_argument("--oui", action="store_true",
                   help="ne pas demander confirmation (pour --refaire)")
    args = p.parse_args(argv)

    if args.refaire:
        return 0 if creer(refaire=True, sans_question=args.oui) else 1
    if args.creer:
        return 0 if creer() else 1
    if args.deposer:
        return 0 if deposer() else 1
    if args.verifier:
        return 0 if verifier() else 1
    return 0 if etat() else 1


if __name__ == "__main__":
    sys.exit(main())
