#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — src/firmware/build.sh
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

# ===========================================================================
#  PhytoScope — micrologiciel PhytoSense : compiler et ranger le livrable
# ===========================================================================
#  La chaîne complète, en une commande : ce script compile par `_make_.sh`,
#  puis **range le résultat dans build/paquets/**, au même endroit et de la
#  même façon que les paquets d'installation.
#
#  Pourquoi deux scripts
#  ---------------------
#
#  `_make_.sh` ne fait qu'une chose : produire `build/phytosense.uf2`. C'est
#  ce qu'on veut pendant la mise au point — on compile vingt fois d'affilée,
#  et ranger un livrable à chaque fois n'a aucun sens.
#
#  Ce script-ci est pour la publication : il nomme le fichier avec sa
#  version — « phytosense.uf2 » tout court, sur le disque de quelqu'un, ne
#  dit pas de quelle version il sort —, calcule ses empreintes, et le dépose
#  là où la fabrique de paquets dépose les siens. Le `.uf2` est un livrable
#  à part entière : sans lui, les paquets installent un logiciel qui n'a
#  rien à écouter.
#
#  Où le livrable est rangé
#  ------------------------
#
#      build/paquets/<version>-<horodatage>/Firmware/
#          phytosense-<version>.uf2      ce qu'on copie sur la carte
#          phytosense-<version>.elf      pour le débogage
#          phytosense-<version>.bin      image brute
#          phytosense-<version>.sha256   les empreintes
#          LISEZ-MOI.txt                 comment programmer la carte
#
#  Trois cas pour choisir ce dossier, dans cet ordre :
#
#    1. `--sortie DOSSIER` — imposé ;
#    2. `PHYTOSCOPE_SORTIE` — la variable que pose la fabrique de paquets.
#       C'est ainsi que le micrologiciel se range dans la MÊME fabrication
#       que les .deb et les .msi, même lancé séparément ;
#    3. sinon, un dossier neuf horodaté, et le lien « dernier » suit.
#
#  Usage :
#      ./build.sh                  compile et range
#      ./build.sh --deps           installe SDK et chaîne ARM, puis compile
#      ./build.sh --propre         repart d'un répertoire de construction vide
#      ./build.sh --sortie DOSSIER range ailleurs
#      ./build.sh --sans-installer compile seulement (comme ./_make_.sh)
#      ./build.sh --help
#
#  Bretagne Namasté — https://bretagne-namaste.com — licence MIT
# ===========================================================================
set -eu

ICI="$(cd "$(dirname "$0")" && pwd)"
#  src/firmware → src → la racine du dépôt.
RACINE="$(cd "$ICI/../.." && pwd)"
VERSION_FICHIER="$RACINE/src/phytoscope/phytoscope/VERSION"
AUTEURS_FICHIER="$RACINE/src/phytoscope/phytoscope/AUTEURS"

#  L'identité vient d'AUTEURS, seule source : le logiciel la lit pour sa
#  fenêtre « À propos », la fabrique de paquets pour estampiller le .deb, et
#  ce script pour la notice. Une quatrième copie finirait par diverger.
lire_cle() {
    sed -n "s/^ *$1 *= *//p" "$2" 2>/dev/null | head -1
}

VERT="$(printf '\033[0;32m')"
JAUNE="$(printf '\033[0;33m')"
ROUGE="$(printf '\033[0;31m')"
GRIS="$(printf '\033[0;90m')"
NEUTRE="$(printf '\033[0m')"

vert()  { printf '%s%s%s\n' "$VERT" "$1" "$NEUTRE"; }
jaune() { printf '%s%s%s\n' "$JAUNE" "$1" "$NEUTRE"; }
rouge() { printf '%s%s%s\n' "$ROUGE" "$1" "$NEUTRE"; }
gris()  { printf '%s%s%s\n' "$GRIS" "$1" "$NEUTRE"; }

aide() {
    sed -n '3,50p' "$0" | sed 's/^#  \{0,1\}//; s/^#$//'
    exit 0
}

# ------------------------------------------------------------------ options
SORTIE=""
INSTALLER=1
ARGS_MAKE=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --sortie)          SORTIE="${2:?--sortie demande un dossier}"; shift 2 ;;
        --sans-installer)  INSTALLER=0; shift ;;
        -h|--help)         aide ;;
        #  Tout le reste va à `_make_.sh` : --deps, --propre, et ce qu'il
        #  apprendra à comprendre plus tard sans qu'on touche ici.
        *)                 ARGS_MAKE="$ARGS_MAKE $1"; shift ;;
    esac
done

# ------------------------------------------------------------ la compilation
if [ ! -x "$ICI/_make_.sh" ]; then
    rouge "  _make_.sh introuvable dans $ICI"
    exit 1
fi

# shellcheck disable=SC2086
"$ICI/_make_.sh" $ARGS_MAKE

UF2="$ICI/build/phytosense.uf2"
if [ ! -f "$UF2" ]; then
    rouge "  la compilation n'a pas produit phytosense.uf2"
    exit 1
fi

if [ "$INSTALLER" -eq 0 ]; then
    gris "  (--sans-installer : le livrable n'est pas rangé)"
    exit 0
fi

# ------------------------------------------------------------- la version
#  Lue dans le fichier qui fait foi, jamais écrite ici. Format « clé =
#  valeur », volontairement pauvre : voir l'en-tête de VERSION.
VERSION="$(sed -n 's/^ *version *= *//p' "$VERSION_FICHIER" 2>/dev/null \
           | head -1 | tr -d ' ')"
if [ -z "$VERSION" ]; then
    jaune "  version indéterminée dans $VERSION_FICHIER — on écrit « inconnue »"
    VERSION="inconnue"
fi

EDITEUR="$(lire_cle editeur "$AUTEURS_FICHIER")"
AUTEUR="$(lire_cle auteur "$AUTEURS_FICHIER")"
SITE="$(lire_cle site "$AUTEURS_FICHIER")"
COURRIEL="$(lire_cle contact "$AUTEURS_FICHIER")"
LICENCE="$(lire_cle licence "$AUTEURS_FICHIER")"
[ -n "$EDITEUR" ]  || EDITEUR="Bretagne Namasté"
[ -n "$SITE" ]     || SITE="https://bretagne-namaste.com"
[ -n "$LICENCE" ]  || LICENCE="MIT"

# ------------------------------------------------------------- la destination
if [ -z "$SORTIE" ]; then
    if [ -n "${PHYTOSCOPE_SORTIE:-}" ]; then
        #  La fabrique de paquets a déjà choisi : on la suit, pour que tout
        #  se retrouve dans la même fabrication.
        SORTIE="$PHYTOSCOPE_SORTIE"
    else
        SORTIE="$RACINE/build/paquets/$VERSION-$(date +%Y%m%d-%H%M)"
    fi
fi
CIBLE="$SORTIE/Firmware"
mkdir -p "$CIBLE"

# ------------------------------------------------------------- le rangement
echo
vert "· Rangement du livrable"

for ext in uf2 elf bin; do
    src="$ICI/build/phytosense.$ext"
    [ -f "$src" ] || continue
    cp "$src" "$CIBLE/phytosense-$VERSION.$ext"
    gris "    phytosense-$VERSION.$ext  ($(du -h "$src" | cut -f1))"
done

#  Les empreintes, calculées sur les fichiers RANGÉS et non sur ceux du
#  répertoire de construction : c'est ce qui est diffusé qu'on vérifie.
if command -v sha256sum >/dev/null 2>&1; then
    ( cd "$CIBLE" && sha256sum phytosense-"$VERSION".* \
        > "phytosense-$VERSION.sha256" )
    gris "    phytosense-$VERSION.sha256"
else
    jaune "    sha256sum absent : pas d'empreintes"
fi

# ------------------------------------------------------------- la notice
cat > "$CIBLE/LISEZ-MOI.txt" <<NOTICE
PhytoScope $VERSION — micrologiciel de la carte PhytoSense One
================================================================

Ce dossier contient le micrologiciel du RP2350. Il n'a rien à voir avec les
paquets d'installation du logiciel, qui sont dans les dossiers voisins : le
logiciel tourne sur l'ordinateur, celui-ci tourne sur la carte.

  phytosense-$VERSION.uf2      ce qu'on copie sur la carte
  phytosense-$VERSION.elf      pour le débogage (GDB, openocd)
  phytosense-$VERSION.bin      image brute
  phytosense-$VERSION.sha256   les empreintes

PROGRAMMER LA CARTE
-------------------

  1. débrancher la carte ;
  2. la rebrancher EN MAINTENANT le bouton BOOTSEL ;
  3. elle apparaît comme un disque amovible nommé RP2350 ;
  4. y copier phytosense-$VERSION.uf2.

La carte redémarre d'elle-même dès que la copie est finie, et le disque
disparaît. C'est normal, et c'est le signe que cela a fonctionné.

  Debian, Ubuntu, Mint  cp phytosense-$VERSION.uf2 /media/\$USER/RP2350/
  Fedora, Red Hat       cp phytosense-$VERSION.uf2 /run/media/\$USER/RP2350/
  macOS                 cp phytosense-$VERSION.uf2 /Volumes/RP2350/
  Windows               glisser le fichier sur le disque amovible

VÉRIFIER LE FICHIER
-------------------

  sha256sum -c phytosense-$VERSION.sha256

CE QUE CE MICROLOGICIEL FAIT, ET CE QU'IL NE FAIT PAS
----------------------------------------------------

Il mesure et il horodate. Il n'interprète rien : aucune détection
d'événement, aucune règle musicale, aucun filtrage autre que celui du
convertisseur. Tout le raisonnement est calculé sur l'ordinateur, où il est
modifiable, vérifiable et remplaçable.

Seule exception : la sortie MIDI directe, qui embarque une version réduite du
moteur de correspondance pour attaquer un synthétiseur matériel sans passer
par la chaîne audio de l'ordinateur. Elle ne rend pas la carte indépendante —
l'ordinateur reste requis pour la régler et pour enregistrer.

--
$EDITEUR — $AUTEUR
$SITE — $COURRIEL — licence $LICENCE
NOTICE
gris "    LISEZ-MOI.txt"

# --------------------------------------------------- le lien « dernier »
#  La fabrique de paquets pose ce lien ; on fait de même quand on a créé le
#  dossier nous-mêmes, pour que « build/paquets/dernier » désigne toujours la
#  fabrication la plus récente, d'où qu'elle vienne.
#  Seulement si la sortie est BIEN dans build/paquets/ : avec « --sortie
#  /tmp/essai », un lien relatif vers « essai » y pointerait dans le vide.
#  Le défaut a existé, le temps d'un essai.
if [ -z "${PHYTOSCOPE_SORTIE:-}" ] \
   && [ "$(dirname "$SORTIE")" = "$RACINE/build/paquets" ]; then
    ln -sfn "$(basename "$SORTIE")" "$RACINE/build/paquets/dernier"
fi

echo
vert "✓ Livrable rangé"
gris "    $(printf '%s' "$CIBLE" | sed "s|$RACINE/||")"
echo
gris "  Pour programmer la carte : voir LISEZ-MOI.txt à côté du .uf2"
echo
