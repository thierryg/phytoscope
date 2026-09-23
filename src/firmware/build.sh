#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — src/firmware/build.sh
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

# ===========================================================================
#  PhytoScope — PhytoSense firmware: build it, and file the deliverable
# ===========================================================================
#  The whole chain in one command: this script compiles through `_make_.sh`,
#  then **files the result under build/packages/**, in the same place and the
#  same way as the installation packages.
#
#  Why two scripts
#  ---------------
#
#  `_make_.sh` does one thing: produce `build/phytosense.uf2`. That is
#  what you want while developing — you build twenty times in a row, and
#  filing a deliverable each time makes no sense.
#
#  This script is for release: it names the file with its version — a bare
#  "phytosense.uf2" on somebody's disk does not say which version it came
#  from — computes its checksums, and
#  puts it where the package factory puts its own. The `.uf2` is a
#  deliverable in its own right: without it, the packages install software
#  that has nothing to listen to.
#
#  Where the deliverable is filed
#  ------------------------------
#
#      build/packages/<version>-<timestamp>/Firmware/
#          phytosense-<version>.uf2      what you copy onto the board
#          phytosense-<version>.elf      for debugging
#          phytosense-<version>.bin      the raw image
#          phytosense-<version>.sha256   the checksums
#          README.txt                    how to flash the board
#
#  Three cases decide that directory, in this order:
#
#    1. `--output DIR` — forced;
#    2. `PHYTOSCOPE_OUTPUT` — the variable the package factory sets. That
#       is how the firmware is filed under the SAME build
#       as the .deb and the .msi, even when run on its own;
#    3. otherwise a fresh timestamped directory, and the "latest" link
#       follows.
#
#  Usage:
#      ./build.sh                  build it and file it
#      ./build.sh --deps           install SDK and ARM toolchain, then build
#      ./build.sh --clean          start again from an empty build directory
#      ./build.sh --sortie DOSSIER range ailleurs
#      ./build.sh --no-install     build only (like ./_make_.sh)
#      ./build.sh --help
#
#  Bretagne Namasté — https://bretagne-namaste.com — MIT licence
# ===========================================================================
set -eu

ICI="$(cd "$(dirname "$0")" && pwd)"
#  src/firmware -> src -> the repository root.
RACINE="$(cd "$ICI/../.." && pwd)"
VERSION_FICHIER="$RACINE/src/phytoscope/phytoscope/VERSION"
AUTHORS_FICHIER="$RACINE/src/phytoscope/phytoscope/AUTHORS"

#  The identity comes from AUTHORS, the single source: the software reads it
#  for its About window, the package factory to stamp the .deb, and this
#  script for the README. A fourth copy would end up diverging.
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
OUTPUT=""
INSTALLER=1
ARGS_MAKE=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --output|--sortie) OUTPUT="${2:?--output needs a directory}"; shift 2 ;;
        --no-install|--sans-installer)  INSTALLER=0; shift ;;
        -h|--help)         aide ;;
        #  Everything else goes to `_make_.sh`: --deps, --clean, and
        #  whatever it learns to understand later without a change here.
        *)                 ARGS_MAKE="$ARGS_MAKE $1"; shift ;;
    esac
done

# ------------------------------------------------------------- the build
if [ ! -x "$ICI/_make_.sh" ]; then
    rouge "  _make_.sh not found in $ICI"
    exit 1
fi

# shellcheck disable=SC2086
"$ICI/_make_.sh" $ARGS_MAKE

UF2="$ICI/build/phytosense.uf2"
if [ ! -f "$UF2" ]; then
    rouge "  the build did not produce phytosense.uf2"
    exit 1
fi

if [ "$INSTALLER" -eq 0 ]; then
    gris "  (--no-install: the deliverable is not filed)"
    exit 0
fi

# ------------------------------------------------------------- the version
#  Read from the file of record, never written here. A deliberately poor
#  "key = value" format: see the header of VERSION.
VERSION="$(sed -n 's/^ *version *= *//p' "$VERSION_FICHIER" 2>/dev/null \
           | head -1 | tr -d ' ')"
if [ -z "$VERSION" ]; then
    jaune "  version undetermined in $VERSION_FICHIER — writing \"unknown\""
    VERSION="inconnue"
fi

EDITEUR="$(lire_cle editeur "$AUTHORS_FICHIER")"
AUTEUR="$(lire_cle auteur "$AUTHORS_FICHIER")"
SITE="$(lire_cle site "$AUTHORS_FICHIER")"
COURRIEL="$(lire_cle contact "$AUTHORS_FICHIER")"
LICENCE="$(lire_cle licence "$AUTHORS_FICHIER")"
[ -n "$EDITEUR" ]  || EDITEUR="Bretagne Namasté"
[ -n "$SITE" ]     || SITE="https://bretagne-namaste.com"
[ -n "$LICENCE" ]  || LICENCE="MIT"

# ------------------------------------------------------------- where it goes
if [ -z "$OUTPUT" ]; then
    if [ -n "${PHYTOSCOPE_OUTPUT:-}" ]; then
        #  The package factory has already chosen: follow it, so that
        #  everything lands in the same build.
        OUTPUT="$PHYTOSCOPE_OUTPUT"
    else
        OUTPUT="$RACINE/build/packages/$VERSION-$(date +%Y%m%d-%H%M)"
    fi
fi
CIBLE="$OUTPUT/Firmware"
mkdir -p "$CIBLE"

# ------------------------------------------------------------- filing it
echo
vert "· Filing the deliverable"

for ext in uf2 elf bin; do
    src="$ICI/build/phytosense.$ext"
    [ -f "$src" ] || continue
    cp "$src" "$CIBLE/phytosense-$VERSION.$ext"
    gris "    phytosense-$VERSION.$ext  ($(du -h "$src" | cut -f1))"
done

#  The checksums, computed over the FILED files and not those in the build
#  directory: what gets verified must be what gets distributed.
if command -v sha256sum >/dev/null 2>&1; then
    ( cd "$CIBLE" && sha256sum phytosense-"$VERSION".* \
        > "phytosense-$VERSION.sha256" )
    gris "    phytosense-$VERSION.sha256"
else
    jaune "    sha256sum missing: no checksums"
fi

# ------------------------------------------------------------- the README
cat > "$CIBLE/README.txt" <<NOTICE
PhytoScope $VERSION — firmware for the PhytoSense One board
============================================================

This directory holds the RP2350's firmware. It has nothing to do with the
software's installation packages, which sit in the neighbouring directories:
the software runs on the computer, this runs on the board.

  phytosense-$VERSION.uf2      what you copy onto the board
  phytosense-$VERSION.elf      for debugging (GDB, openocd)
  phytosense-$VERSION.bin      the raw image
  phytosense-$VERSION.sha256   the checksums

FLASHING THE BOARD
------------------

  1. unplug the board;
  2. plug it back in WHILE HOLDING the BOOTSEL button;
  3. it appears as a removable disk named RP2350;
  4. copy phytosense-$VERSION.uf2 onto it.

The board restarts by itself as soon as the copy finishes, and the disk
disappears. That is normal, and it is the sign that it worked.

  Debian, Ubuntu, Mint  cp phytosense-$VERSION.uf2 /media/\$USER/RP2350/
  Fedora, Red Hat       cp phytosense-$VERSION.uf2 /run/media/\$USER/RP2350/
  macOS                 cp phytosense-$VERSION.uf2 /Volumes/RP2350/
  Windows               drag the file onto the removable disk

VERIFYING THE FILE
------------------

  sha256sum -c phytosense-$VERSION.sha256

WHAT THIS FIRMWARE DOES, AND WHAT IT DOES NOT
---------------------------------------------

It measures and it timestamps. It interprets nothing: no event detection, no
musical rule, no filtering beyond the converter's own. All the reasoning is
computed on the computer, where it can be changed, checked and replaced.

The one exception is the direct MIDI output, which carries a reduced version
of the mapping engine so as to drive a hardware synthesizer without going
through the computer's audio chain. It does not make the board independent —
the computer is still needed to set it up and to record.

The USB side of the board — its descriptors, the frames it sends and the
control protocol — is documented in sources/usb/reference.html.

--
$EDITEUR — $AUTEUR
$SITE — $COURRIEL — licence $LICENCE
NOTICE
gris "    README.txt"

# ------------------------------------------------- the "latest" symlink
#  The package factory lays this link down; we do the same when we created
#  the directory ourselves, so that "build/packages/latest" always names the
#  most recent build, wherever it came from.
#  Only when the output really is under build/packages/: with
#  "--output /tmp/trial", a relative link to "trial" would point nowhere.
#  The defect did happen, for the length of one trial.
if [ -z "${PHYTOSCOPE_OUTPUT:-}" ] \
   && [ "$(dirname "$OUTPUT")" = "$RACINE/build/packages" ]; then
    ln -sfn "$(basename "$OUTPUT")" "$RACINE/build/packages/latest"
fi

echo
vert "✓ Deliverable filed"
gris "    $(printf '%s' "$CIBLE" | sed "s|$RACINE/||")"
echo
gris "  To flash the board: see README.txt next to the .uf2"
echo
