#!/usr/bin/env bash
#  ==========================================================================
#  PhytoScope — attribution — src/firmware/_make_.sh
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
#  Building the PhytoSense One firmware — RP2350
#
#  This script COMPILES, and nothing more. It was called "build.sh" until
#  2026-09-18; it was renamed to free that name for the script that runs the
#  whole chain — compile AND file the deliverable under build/packages/. See
#  ./build.sh, which calls this one.
#
#    ./_make_.sh           build (and say what to do if something is missing)
#    ./_make_.sh --deps    install the SDK and the toolchain under $HOME,
#                          touching nothing system-wide and asking for no
#                          password
#    ./_make_.sh --clean   start again from an empty build directory
#
#  Nothing is installed system-wide: the SDK goes to ~/pico/pico-sdk and the
#  ARM toolchain to ~/.local/opt/. Anyone who prefers their distribution's
#  packages installs them themselves — the script will find those too.
#
#  MIT licence — Bretagne Namasté — https://bretagne-namaste.com
# ===========================================================================
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_VERSION="2.3.1"          # 2.0.0 is the minimum for the RP2350
ARM_VERSION="14.2.rel1"
SDK_DEFAUT="$HOME/pico/pico-sdk"
CARTE="${PICO_BOARD:-pico2}"

#  --- Which ARM toolchain to download? -------------------------------------
#  ARM publishes one archive per system/architecture pair. An earlier version
#  of this script hardcoded "x86_64", so `--deps` failed on an Apple Silicon
#  Mac and on a Raspberry Pi alike, with an unhelpful 404.
hote_arm() {
    local systeme machine
    systeme="$(uname -s)"
    machine="$(uname -m)"
    case "$systeme" in
        Darwin)
            case "$machine" in
                arm64|aarch64) echo "darwin-arm64" ;;
                *)             echo "darwin-x86_64" ;;
            esac ;;
        Linux)
            case "$machine" in
                aarch64|arm64) echo "aarch64" ;;
                x86_64|amd64)  echo "x86_64" ;;
                *)             echo "" ;;     # architecture ARM does not publish
            esac ;;
        *)  echo "" ;;
    esac
}

HOTE_ARM="$(hote_arm)"
ARM_DEFAUT="$HOME/.local/opt/arm-gnu-toolchain-${ARM_VERSION}-${HOTE_ARM}-arm-none-eabi"

vert()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
jaune() { printf '\033[0;33m%s\033[0m\n' "$*"; }
rouge() { printf '\033[0;31m%s\033[0m\n' "$*"; }

# --- 1. where is the SDK? --------------------------------------------------
trouver_sdk() {
    for c in "${PICO_SDK_PATH:-}" "$SDK_DEFAUT" /usr/share/pico-sdk \
             /opt/pico-sdk "$HOME/pico-sdk"; do
        [ -n "$c" ] && [ -f "$c/pico_sdk_init.cmake" ] && { echo "$c"; return; }
    done
}

# --- 2. where is the ARM toolchain? ---------------------------------------
trouver_arm() {
    command -v arm-none-eabi-gcc >/dev/null 2>&1 && { dirname "$(command -v arm-none-eabi-gcc)"; return; }
    for c in "$ARM_DEFAUT/bin" "$HOME"/.local/opt/arm-gnu-toolchain-*/bin; do
        [ -x "$c/arm-none-eabi-gcc" ] && { echo "$c"; return; }
    done
}

installer_deps() {
    if [ -z "$(trouver_sdk)" ]; then
        jaune "· Downloading Pico SDK ${SDK_VERSION} -> ${SDK_DEFAUT}"
        mkdir -p "$(dirname "$SDK_DEFAUT")"
        git clone --branch "$SDK_VERSION" --depth 1 \
            https://github.com/raspberrypi/pico-sdk.git "$SDK_DEFAUT"
        #  Without TinyUSB the build fails on "tusb.h: No such file".
        git -C "$SDK_DEFAUT" submodule update --init --depth 1 lib/tinyusb
        vert "✓ SDK installed"
    else
        vert "✓ SDK already present: $(trouver_sdk)"
    fi

    if [ -z "$(trouver_arm)" ]; then
        if [ -z "$HOTE_ARM" ]; then
            rouge "✗ ARM publishes no prebuilt toolchain for $(uname -s)/$(uname -m)."
            rouge "  Installez « gcc-arm-none-eabi » par votre gestionnaire de paquets,"
            rouge "  or point at an existing one: ARM_TOOLCHAIN_PATH=/path ./_make_.sh"
            exit 2
        fi
        jaune "· Downloading ARM toolchain ${ARM_VERSION} for ${HOTE_ARM} (~140 MB)"
        jaune "  → ${ARM_DEFAUT}"
        mkdir -p "$HOME/.local/opt"
        local url="https://developer.arm.com/-/media/Files/downloads/gnu/${ARM_VERSION}/binrel/arm-gnu-toolchain-${ARM_VERSION}-${HOTE_ARM}-arm-none-eabi.tar.xz"
        local tmp; tmp="$(mktemp -d)"
        curl -L --progress-bar "$url" -o "$tmp/arm.tar.xz"
        tar -xf "$tmp/arm.tar.xz" -C "$HOME/.local/opt"
        rm -rf "$tmp"
        vert "✓ ARM toolchain installed"
    else
        vert "✓ ARM toolchain already present: $(trouver_arm)"
    fi
}

# --- 3. the run itself -----------------------------------------------------
[ "${1:-}" = "--deps" ] && { installer_deps; shift || true; }
#  --clean is the English name; --propre stays accepted so that a script
#  or a habit built on the old name keeps working.
case "${1:-}" in
    --clean|--propre) rm -rf "$ICI/build"; shift || true ;;
esac

SDK="$(trouver_sdk || true)"
ARM="$(trouver_arm || true)"

if [ -z "$SDK" ] || [ -z "$ARM" ]; then
    rouge "Il manque de quoi construire :"
    [ -z "$SDK" ] && echo "  · the Pico SDK 2.x (RP2350)"
    [ -z "$ARM" ] && echo "  · the arm-none-eabi toolchain"
    echo
    echo "  Install everything under your home directory, with no password:"
    echo "      ./_make_.sh --deps"
    echo
    echo "  Ou par votre gestionnaire de paquets :"
    echo "      Debian, Ubuntu, Mint :"
    echo "          sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi \\"
    echo "                           libstdc++-arm-none-eabi-newlib build-essential git python3"
    echo "      Fedora, Red Hat, Rocky, Alma :"
    echo "          sudo dnf install cmake arm-none-eabi-gcc-cs arm-none-eabi-newlib \\"
    echo "                           gcc gcc-c++ make git python3"
    echo "      macOS (Homebrew) :"
    echo "          brew install cmake git"
    echo "          brew install --cask gcc-arm-embedded"
    echo
    echo "  Windows: this script needs a POSIX shell. Use WSL 2"
    echo "  (\"wsl --install\", then Ubuntu) and run it again from Linux."
    exit 2
fi

export PICO_SDK_PATH="$SDK"
export PATH="$ARM:$PATH"

#  This file belongs to the SDK and must stay in step with it, so it is
#  copied at every build rather than frozen into the repository.
cp "$SDK/external/pico_sdk_import.cmake" "$ICI/pico_sdk_import.cmake"

vert "· SDK   : $SDK"
vert "· ARM   : $(arm-none-eabi-gcc --version | head -1)"
vert "· Board: $CARTE"

mkdir -p "$ICI/build"

#  A CMake cache remembers the ABSOLUTE path of the sources. Moving or
#  renaming the working copy — which happened on 2026-09-18, when the
#  firmware left sources/ for src/firmware/ — therefore makes it stale,
#  et cmake refuse de continuer :
#
#      The current CMakeCache.txt directory … is different than the
#      directory … where CMakeCache.txt was created.
#
#  The message is accurate but discouraging, and the answer is always the
#  same: throw the cache away. So we do it here, rather than leaving every
#  person who hits it to work that out for themselves.
if [ -f "$ICI/build/CMakeCache.txt" ]; then
    cache_source="$(sed -n 's/^CMAKE_HOME_DIRECTORY:INTERNAL=//p' \
                    "$ICI/build/CMakeCache.txt" | head -1)"
    if [ -n "$cache_source" ] && [ "$cache_source" != "$ICI" ]; then
        jaune "· Stale CMake cache (it points at $cache_source) — discarding it"
        rm -rf "$ICI/build"
        mkdir -p "$ICI/build"
    fi
fi

cd "$ICI/build"
cmake .. -DPICO_BOARD="$CARTE" -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build . -j"$(nproc 2>/dev/null || echo 4)"

echo
vert "✓ Built:"
for f in phytosense.uf2 phytosense.elf phytosense.bin; do
    [ -f "$f" ] && printf '    %-18s %s\n' "$f" "$(du -h "$f" | cut -f1)"
done
arm-none-eabi-size phytosense.elf | tail -1 | awk \
    '{printf "    memory             %d bytes of code, %d of data\n", $1, $3}'
echo
#  The board's mount point differs from system to system: Debian and
#  Ubuntu mount under /media/$USER, Fedora and Red Hat under /run/media/$USER,
#  macOS under /Volumes. We look rather than guess.
monter_ou() {
    local d
    for d in "/media/$USER/RP2350" "/run/media/$USER/RP2350" \
             "/media/$USER/RPI-RP2" "/run/media/$USER/RPI-RP2" \
             "/Volumes/RP2350" "/Volumes/RPI-RP2"; do
        [ -d "$d" ] && { echo "$d"; return; }
    done
    echo ""
}

echo "  To flash: plug the board in while holding BOOTSEL, then"
CIBLE="$(monter_ou)"
if [ -n "$CIBLE" ]; then
    vert "      cp build/phytosense.uf2 $CIBLE/       <- board detected"
else
    echo "      cp build/phytosense.uf2 <mount point>/"
    echo
    echo "      Debian, Ubuntu, Mint  : /media/\$USER/RP2350/"
    echo "      Fedora, Red Hat       : /run/media/\$USER/RP2350/"
    echo "      macOS                 : /Volumes/RP2350/"
    echo "      Windows (WSL)         : /mnt/<letter>/ — the board shows up"
    echo "                              as a removable disk"
fi
