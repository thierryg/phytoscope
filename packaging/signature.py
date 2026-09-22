#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — packaging/signature.py
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

"""Certificat et signature des paquets — ce que cela prouve, et ce que non.

Ce module fabrique un **certificat X.509 auto-signé** au nom de l'auteur et
s'en sert pour signer tout ce que la fabrique produit :

* les installateurs Windows — `.exe` et `.msi` — par **Authenticode**, la
  signature que Windows sait lire nativement (`osslsigncode`) ;
* tout le reste — `.deb`, `.rpm`, `.pkg`, `.zip`, `.tar.gz`, `.run` — par une
  signature **CMS détachée** (`.p7s`), que `openssl cms -verify` contrôle.

Ce que la signature prouve
--------------------------

Que le fichier n'a pas changé depuis qu'il a été signé, et qu'il a été signé
par la clé privée correspondant au certificat livré à côté. Autrement dit :
deux téléchargements faits à six mois d'intervalle viennent bien de la même
personne, et personne n'a modifié l'archive en route.

Ce que la signature NE prouve PAS, et il faut le dire
------------------------------------------------------

**Un certificat auto-signé ne fait pas taire les avertissements de Windows ni
de macOS.** SmartScreen exige un certificat de signature de code délivré par
une autorité reconnue — un produit commercial, facturé chaque année ;
Gatekeeper exige un identifiant de développeur Apple, qui suppose un compte
payant et un Mac. Ni l'un ni l'autre ne se contourne par un certificat qu'on
se délivre à soi-même.

Ce que le certificat auto-signé apporte réellement :

1. **L'intégrité et la continuité d'origine**, vérifiables par qui veut, avec
   `openssl` seul et sans rien acheter.
2. **Un déploiement en parc sans avertissement** : une entreprise qui installe
   le certificat public dans le magasin « Éditeurs approuvés » de ses machines
   ne verra plus l'avertissement — c'est la pratique courante pour un logiciel
   interne, et le MSI s'y prête.
3. **Une empreinte publiable.** Le site annonce l'empreinte SHA-256 du
   certificat ; qui la compare sait à qui il a affaire.

Prétendre davantage serait mentir à l'utilisateur, et un instrument de mesure
qui ment sur ce qu'il garantit n'a plus grand intérêt.

Où vit la clé privée
--------------------

Dans ``~/.local/share/phytoscope-signature/``, en 0600, **hors du dépôt** : une
clé privée n'a rien à faire dans un dossier qu'on recopie et qu'on publie. Elle
est créée sans phrase de passe, pour qu'une fabrication complète se fasse sans
intervention ; sur une machine partagée, ajoutez-en une (la marche à suivre est
dans le fichier ``LISEZ-MOI`` déposé à côté de la clé).

**Sauvegardez cette clé.** La perdre signifie que les versions suivantes ne
pourront plus être rattachées aux précédentes.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from common import (  # noqa: E402
    GRIS, JAUNE, ROUGE, VERT, Identite, bien, dire, dossier_fabrication,
    echec, ecrire, etape, executer, lisible, souci, tous_les_paquets)

#  La clé privée vit hors du dépôt. Un dossier qu'on recopie, qu'on archive et
#  qu'on publie n'est pas un endroit pour une clé privée.
MAGASIN = os.path.expanduser("~/.local/share/phytoscope-signature")
CLE = os.path.join(MAGASIN, "phytoscope.key")
CERTIFICAT = os.path.join(MAGASIN, "phytoscope.crt")

#  Dix ans : assez pour que le certificat survive au logiciel, assez peu pour
#  qu'on le renouvelle un jour. Un certificat expiré invalide les signatures
#  faites après son expiration, pas celles d'avant.
DUREE_JOURS = 3653

OSSLSIGNCODE_MAISON = os.path.expanduser("~/.local/opt/osslsigncode")

#  Une copie du certificat PUBLIC dans le dépôt, pour l'avoir sous la main :
#  c'est lui qu'on publie, qu'on joint à une annonce et que quelqu'un compare.
#  La clé PRIVÉE, elle, ne quitte jamais ~/.local/share — un dépôt se recopie,
#  s'archive et se publie, et une clé privée n'y a pas sa place.
#
#  Dans `certificat/`, et non plus à la racine : le rangement du 2026-09-18 a
#  donné un dossier à tout ce qui touche au certificat, et en laisser une
#  copie à la racine en faisait un doublon que personne ne savait à jour.
#  C'est `packaging/certificate.py` qui remplit ce dossier.
from common import RACINE as _RACINE                      # noqa: E402
CERTIFICAT_PROJET = os.path.join(_RACINE, "certificat",
                                 "phytoscope-certificate.pem")


# ---------------------------------------------------------------------------
#  Outils
# ---------------------------------------------------------------------------
def trouver_osslsigncode() -> str:
    """Le chemin d'osslsigncode, du système ou du dossier personnel."""
    systeme = shutil.which("osslsigncode")
    if systeme:
        return systeme
    maison = os.path.join(OSSLSIGNCODE_MAISON, "usr", "bin", "osslsigncode")
    return maison if os.path.exists(maison) else ""


def environnement_ossl() -> Dict[str, str]:
    env = dict(os.environ)
    if shutil.which("osslsigncode"):
        return env
    lib = os.path.join(OSSLSIGNCODE_MAISON, "usr", "lib", "x86_64-linux-gnu")
    if os.path.isdir(lib):
        ancien = env.get("LD_LIBRARY_PATH", "")
        env["LD_LIBRARY_PATH"] = lib + (":" + ancien if ancien else "")
    return env


def installer_osslsigncode() -> bool:
    """Déplie osslsigncode dans le dossier personnel, sans privilèges."""
    from common import installer_paquets_debian
    return installer_paquets_debian(
        "osslsigncode", OSSLSIGNCODE_MAISON,
        ("osslsigncode", "libcurl4"), trouver_osslsigncode)


# ---------------------------------------------------------------------------
#  Le certificat
# ---------------------------------------------------------------------------
def sujet(id_: Identite) -> str:
    """Le sujet X.509, bâti sur le fichier `AUTEURS` — une seule source.

    L'ordre est celui qu'attend OpenSSL, du plus général au plus précis. Les
    champs vides sont omis : un certificat portant « L= » vide est mal formé.
    """
    morceaux: List[Tuple[str, str]] = [
        ("C", id_.pays), ("ST", id_.region), ("L", id_.ville),
        ("O", id_.editeur), ("OU", "PhytoScope"),
        ("CN", id_.auteur or id_.editeur),
        ("emailAddress", id_.courriel or id_.contact),
    ]
    return "".join(f"/{cle}={valeur}" for cle, valeur in morceaux if valeur)


def certificat_existe() -> bool:
    return os.path.exists(CLE) and os.path.exists(CERTIFICAT)


def generer_certificat(id_: Optional[Identite] = None,
                       refaire: bool = False) -> bool:
    """Crée le certificat auto-signé, s'il n'existe pas déjà.

    On ne le refait JAMAIS tout seul : régénérer la clé romprait le lien avec
    tout ce qui a été signé auparavant, et les utilisateurs qui ont noté
    l'empreinte verraient soudain une autre. `--refaire` l'exige explicitement.
    """
    id_ = id_ or Identite.lire()
    if certificat_existe() and not refaire:
        bien(f"certificat déjà présent : {CERTIFICAT}")
        return True
    if refaire and certificat_existe():
        souci("l'ancien certificat est remplacé — les signatures déjà "
              "publiées ne seront plus rattachables à la nouvelle clé")

    if not shutil.which("openssl"):
        echec("openssl est nécessaire : sudo apt install openssl")
        return False

    os.makedirs(MAGASIN, exist_ok=True)
    os.chmod(MAGASIN, 0o700)
    etape(f"génération de la clé et du certificat ({DUREE_JOURS} jours)")

    #  Les extensions font de ce certificat un certificat de SIGNATURE DE
    #  CODE, et non un certificat de serveur : c'est ce que vérifie Windows,
    #  et ce que `openssl verify -purpose codesign` contrôle.
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False,
                                     encoding="utf-8") as f:
        f.write("""[req]
distinguished_name = dn
x509_extensions = ext
prompt = no

[dn]

[ext]
basicConstraints = critical, CA:FALSE
keyUsage = critical, digitalSignature
extendedKeyUsage = critical, codeSigning
subjectKeyIdentifier = hash
nsComment = "PhytoScope — certificat auto-signe, voir AUTHENTICITE.txt"
""")
        config = f.name

    #  `-utf8` : sans lui, OpenSSL lit le sujet en Latin-1 et « Namasté »
    #  devient « NamastÃ© » dans le certificat — donc dans tout ce qui
    #  l'affiche, y compris les propriétés du fichier sous Windows.
    ok = executer(["openssl", "req", "-x509", "-utf8", "-newkey", "rsa:4096",
                   "-keyout", CLE, "-out", CERTIFICAT,
                   "-days", str(DUREE_JOURS), "-nodes", "-sha256",
                   "-subj", sujet(id_), "-config", config, "-extensions", "ext"])
    os.unlink(config)
    if not ok:
        return False

    os.chmod(CLE, 0o600)
    os.chmod(CERTIFICAT, 0o644)
    ecrire(os.path.join(MAGASIN, "LISEZ-MOI.txt"), _lisez_moi_cle(id_))
    deposer_dans_le_projet(id_)
    bien(f"certificat créé : {CERTIFICAT}")
    souci("SAUVEGARDEZ phytoscope.key — sans elle, les versions suivantes "
          "ne\n    pourront plus être rattachées aux précédentes.")
    return True


def deposer_dans_le_projet(id_: Optional[Identite] = None) -> str:
    """Recopie le certificat PUBLIC à la racine du projet.

    Seulement le certificate. La clé privée reste dans ~/.local/share, et le
    fichier déposé ici porte en clair, dans son en-tête, l'empreinte à
    comparer — pour qu'on puisse l'annoncer sans avoir à la recalculer.
    """
    if not os.path.exists(CERTIFICAT):
        return ""
    id_ = id_ or Identite.lire()
    with open(CERTIFICAT, encoding="utf-8") as f:
        pem = f.read()
    entete = (
        f"# PhytoScope — certificat public de signature\n"
        f"#\n"
        f"# {id_.editeur} — {id_.auteur} <{id_.courriel}>\n"
        f"# {id_.site}\n"
        f"#\n"
        f"# Empreinte SHA-256 :\n"
        f"#     {empreinte_certificat()}\n"
        f"#\n"
        f"# Ce fichier est PUBLIC : il sert à vérifier les paquets, jamais à\n"
        f"# en signer. La clé privée vit dans ~/.local/share/phytoscope-signature\n"
        f"# et ne doit JAMAIS être recopiée ici.\n"
        f"#\n"
        f"# Vérifier un paquet :\n"
        f"#     openssl cms -verify -binary -inform DER -in <paquet>.p7s \\\n"
        f"#         -content <paquet> -certfile phytoscope-certificate.pem \\\n"
        f"#         -noverify -out /dev/null\n"
        f"#\n"
        f"# Ce certificat est AUTO-SIGNÉ : il prouve l'intégrité et la\n"
        f"# continuité d'origine, il ne fait taire ni SmartScreen ni Gatekeeper.\n"
        f"# Voir AUTHENTICITE.txt auprès des paquets.\n\n")
    ecrire(CERTIFICAT_PROJET, entete + pem)
    return CERTIFICAT_PROJET


def empreinte_certificat() -> str:
    """L'empreinte SHA-256 du certificat, celle qu'on publie sur le site."""
    if not os.path.exists(CERTIFICAT):
        return ""
    try:
        r = subprocess.run(["openssl", "x509", "-in", CERTIFICAT, "-noout",
                            "-fingerprint", "-sha256"],
                           capture_output=True, timeout=60)
        return r.stdout.decode("utf-8", "replace").strip().split("=", 1)[-1]
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return ""


def _lisez_moi_cle(id_: Identite) -> str:
    return f"""Clé de signature de PhytoScope — {id_.attribution}
{'=' * 74}

  phytoscope.key    LA CLÉ PRIVÉE. Ne la partagez jamais. Sauvegardez-la.
  phytoscope.crt    le certificat public, à diffuser avec les paquets.

  Sujet   : {sujet(id_)}
  Validité: {DUREE_JOURS} jours à compter de sa création.

AJOUTER UNE PHRASE DE PASSE
{'-' * 74}

  La clé est créée sans phrase de passe, pour qu'une fabrication complète se
  fasse sans intervention. Sur une machine partagée, protégez-la :

      openssl rsa -aes256 -in phytoscope.key -out phytoscope.key.chiffree
      mv phytoscope.key.chiffree phytoscope.key

  La fabrique demandera alors la phrase à chaque signature.

SI VOUS PERDEZ CETTE CLÉ
{'-' * 74}

  Les paquets déjà publiés restent vérifiables — leur certificat est diffusé
  avec eux. Mais les versions suivantes seront signées par une AUTRE clé, et
  rien ne les rattachera aux précédentes. C'est le seul dommage, et il est
  irréversible : sauvegardez.
"""


# ---------------------------------------------------------------------------
#  Signer
# ---------------------------------------------------------------------------
def signer_authenticode(fichier: str, id_: Identite) -> bool:
    """Signature Authenticode d'un .exe ou d'un .msi.

    C'est la signature que Windows lit nativement : elle apparaît dans les
    propriétés du fichier, onglet « Signatures numériques ». Elle n'empêchera
    pas l'avertissement SmartScreen — voir l'en-tête de ce module — mais elle
    rend le fichier vérifiable et permet à un parc de le reconnaître.
    """
    outil = trouver_osslsigncode()
    if not outil:
        souci(f"osslsigncode absent — {os.path.basename(fichier)} non signé")
        return False
    sortie = fichier + ".signe"
    ok = executer([outil, "sign",
                   "-certs", CERTIFICAT, "-key", CLE,
                   "-n", f"PhytoScope {id_.version}",
                   "-i", id_.site,
                   "-h", "sha256",
                   "-in", fichier, "-out", sortie],
                  env=environnement_ossl())
    if not ok or not os.path.exists(sortie):
        return False
    os.replace(sortie, fichier)
    return True


def signer_cms(fichier: str) -> bool:
    """Signature CMS détachée : un fichier `.p7s` à côté du paquet.

    Détachée, et non incorporée : le paquet reste utilisable tel quel par qui
    n'a que faire de la signature, et `apt`, `dnf` ou l'installateur de macOS
    ne voient aucune différence.
    """
    cible = fichier + ".p7s"
    #  Détachée par défaut : `openssl cms -sign` n'incorpore le contenu que si
    #  on le lui demande par `-nodetach`. Il n'existe pas d'option `-detach`.
    return executer(["openssl", "cms", "-sign", "-binary",
                     "-in", fichier, "-out", cible, "-outform", "DER",
                     "-signer", CERTIFICAT, "-inkey", CLE, "-md", "sha256"])


def signer_tout(id_: Optional[Identite] = None) -> Tuple[int, int]:
    """Signe tous les paquets de la fabrication en cours.

    Rend (signés, en échec). L'échec d'une signature n'est jamais fatal : un
    paquet non signé reste un paquet utilisable, et mieux vaut une fabrication
    incomplètement signée qu'une fabrication perdue.
    """
    id_ = id_ or Identite.lire()
    if not certificat_existe():
        echec("aucun certificat — lancez d'abord : make certificat")
        return (0, 0)

    dire(f"\nSignature des paquets — {id_.attribution}\n", JAUNE)
    signes, rates = 0, 0
    for chemin in tous_les_paquets(id_):
        nom = os.path.basename(chemin)
        if nom.endswith((".p7s", ".pem", ".crt")):
            continue
        #  Windows d'abord : la signature Authenticode modifie le fichier, il
        #  faut donc la poser AVANT de calculer la signature détachée.
        if nom.endswith((".exe", ".msi")):
            if signer_authenticode(chemin, id_):
                bien(f"{nom} — Authenticode")
            else:
                rates += 1
                continue
        if signer_cms(chemin):
            signes += 1
            if not nom.endswith((".exe", ".msi")):
                bien(f"{nom} — CMS détachée")
        else:
            echec(f"{nom} — signature impossible")
            rates += 1

    #  Le certificat public voyage avec les paquets : sans lui, la signature
    #  n'est vérifiable par personne. Et dans CHAQUE dossier de système, car
    #  un dossier recopié seul sur un serveur doit rester vérifiable seul.
    from common import SYSTEMES
    base = dossier_fabrication(id_)
    texte = _authenticite(id_)
    dossiers = [base] + [os.path.join(base, sys_) for sys_ in SYSTEMES
                         if os.path.isdir(os.path.join(base, sys_))]
    for dossier in dossiers:
        shutil.copy2(CERTIFICAT,
                     os.path.join(dossier, "phytoscope-certificate.pem"))
        ecrire(os.path.join(dossier, "AUTHENTICITE.txt"), texte)
    return (signes, rates)


# ---------------------------------------------------------------------------
#  Vérifier
# ---------------------------------------------------------------------------
def verifier_tout(id_: Optional[Identite] = None) -> Tuple[int, int]:
    """Recontrôle chaque signature — on ne publie pas ce qu'on n'a pas relu."""
    id_ = id_ or Identite.lire()
    base = dossier_fabrication(id_)
    cert = os.path.join(base, "phytoscope-certificate.pem")
    if not os.path.exists(cert):
        souci("aucun certificat dans cette fabrication — rien à vérifier")
        return (0, 0)

    dire("\nVérification des signatures\n", JAUNE)
    bons, mauvais = 0, 0
    for chemin in tous_les_paquets(id_):
        nom = os.path.basename(chemin)
        if nom.endswith((".p7s", ".pem", ".crt")):
            continue
        p7s = chemin + ".p7s"
        if not os.path.exists(p7s):
            souci(f"{nom} — non signé")
            continue
        #  `-noverify` : on contrôle la SIGNATURE, pas la chaîne de confiance.
        #  Un certificat auto-signé n'a pas de chaîne, et c'est assumé.
        ok = executer(["openssl", "cms", "-verify", "-binary",
                       "-in", p7s, "-inform", "DER", "-content", chemin,
                       "-certfile", cert, "-noverify", "-out", os.devnull])
        if ok:
            bien(f"{nom}")
            bons += 1
        else:
            echec(f"{nom} — SIGNATURE INVALIDE")
            mauvais += 1
    return (bons, mauvais)


def _authenticite(id_: Identite) -> str:
    return f"""PhytoScope {id_.version} — authenticité des paquets
{'=' * 74}

  Publié par {id_.editeur} — {id_.site}
  Écrit par  {id_.auteur} — {id_.courriel}
             {id_.telephone}

  Tous les paquets de ce dossier sont signés avec le certificat
  « phytoscope-certificate.pem », livré ici même.

  Empreinte SHA-256 du certificat :
      {empreinte_certificat() or '(indisponible)'}

  Comparez-la avec celle publiée sur {id_.site}.


CE QUE LA SIGNATURE PROUVE
{'-' * 74}

  Que le fichier n'a pas changé depuis qu'il a été signé, et qu'il l'a été par
  la clé correspondant à ce certificate. Deux téléchargements faits à six mois
  d'intervalle viennent donc bien de la même personne, et personne n'a modifié
  l'archive en route.


CE QU'ELLE NE PROUVE PAS
{'-' * 74}

  Ce certificat est AUTO-SIGNÉ. Il ne fait taire ni l'avertissement de Windows
  (SmartScreen), ni celui de macOS (Gatekeeper) : le premier exige un
  certificat délivré par une autorité reconnue — un produit commercial facturé
  chaque année —, le second un identifiant de développeur Apple, qui suppose
  un compte payant et un Mac.

  Nous préférons le dire. Un instrument de mesure qui exagère ce qu'il
  garantit n'a plus grand intérêt.

  En revanche, un service informatique qui installe ce certificat dans le
  magasin « Éditeurs approuvés » de ses machines n'aura plus d'avertissement :
  c'est la pratique courante pour un logiciel interne, et le MSI s'y prête.


VÉRIFIER UNE SIGNATURE
{'-' * 74}

  Sur n'importe quel système avec OpenSSL :

      openssl cms -verify -binary -inform DER \\
          -in <paquet>.p7s -content <paquet> \\
          -certfile phytoscope-certificate.pem -noverify -out /dev/null

  « Verification successful » signifie que le fichier est intact et signé par
  cette clé. L'option -noverify écarte la chaîne de confiance, qu'un
  certificat auto-signé n'a pas — c'est attendu, pas un défaut de vérification.

  Sous Windows, pour les .exe et .msi, la signature Authenticode est visible
  dans les propriétés du fichier, onglet « Signatures numériques ». En ligne
  de commande :

      Get-AuthenticodeSignature .\\PhytoScope-{id_.version}-Windows.exe

  Voir aussi le certificat lui-même :

      openssl x509 -in phytoscope-certificate.pem -noout -text


  {id_.attribution} — licence {id_.licence}
"""


# ---------------------------------------------------------------------------
#  Entrée
# ---------------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    import argparse
    p = argparse.ArgumentParser(
        prog="signature.py",
        description="Certificat et signature des paquets de PhytoScope.")
    p.add_argument("--certificat", action="store_true",
                   help="créer le certificat s'il n'existe pas")
    p.add_argument("--refaire", action="store_true",
                   help="REMPLACER le certificat existant (rompt le lien avec "
                        "tout ce qui a déjà été signé)")
    p.add_argument("--signer", action="store_true",
                   help="signer les paquets de la fabrication en cours")
    p.add_argument("--verifier", action="store_true",
                   help="recontrôler les signatures")
    p.add_argument("--deps", action="store_true",
                   help="installer osslsigncode dans ~/.local/opt, sans sudo")
    p.add_argument("--empreinte", action="store_true",
                   help="afficher l'empreinte SHA-256 du certificat")
    p.add_argument("--deposer", action="store_true",
                   help="recopier le certificat public à la racine du projet")
    p.add_argument("--sortie", default="", help=argparse.SUPPRESS)
    args = p.parse_args(argv)

    from common import VARIABLE_SORTIE, derniere_fabrication
    if args.sortie:
        os.environ[VARIABLE_SORTIE] = os.path.abspath(args.sortie)
    elif not os.environ.get(VARIABLE_SORTIE):
        #  Sans indication, on travaille sur la fabrication la plus récente
        #  QUI CONTIENT QUELQUE CHOSE — et surtout pas sur un dossier neuf,
        #  qu'on créerait au passage et qui serait vide.
        recente = derniere_fabrication()
        if recente:
            os.environ[VARIABLE_SORTIE] = recente
        elif args.signer or args.verifier:
            echec("aucune fabrication à signer — lancez d'abord « make tout »")
            return 1

    id_ = Identite.lire()

    if args.deps:
        return 0 if installer_osslsigncode() else 1
    if args.empreinte:
        print(empreinte_certificat() or "(aucun certificat)")
        return 0
    if args.deposer:
        chemin = deposer_dans_le_projet(id_)
        if chemin:
            bien(f"certificat public déposé : {os.path.relpath(chemin, _RACINE)}")
            return 0
        echec("aucun certificat à déposer")
        return 1
    if args.certificat or args.refaire:
        return 0 if generer_certificat(id_, args.refaire) else 1
    if args.verifier:
        bons, mauvais = verifier_tout(id_)
        dire(f"\n  {bons} signature(s) valide(s), {mauvais} invalide(s)\n",
             VERT if not mauvais else ROUGE)
        return 0 if not mauvais else 1
    if args.signer:
        #  On PROPOSE, on ne crée pas d'autorité. Fabriquer une clé de
        #  signature dans le dos de qui lance un « make » est le genre de
        #  surprise qu'on ne veut pas : sur une machine d'intégration
        #  continue, ce serait une clé éphémère qu'on croirait permanente,
        #  et les paquets porteraient une signature invérifiable ailleurs.
        import certificate as _certificat
        if not _certificat.proposer_si_absent():
            echec("rien n'a été signé — aucun certificat")
            return 1
        signes, rates = signer_tout(id_)
        dire(f"\n  {signes} paquet(s) signé(s), {rates} en échec\n",
             VERT if not rates else JAUNE)
        return 0 if signes else 1

    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
