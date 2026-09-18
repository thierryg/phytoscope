#!/usr/bin/env bash
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
#  Construction du micrologiciel PhytoSense One — RP2350
#
#    ./build.sh            construit (et dit quoi faire s'il manque quelque chose)
#    ./build.sh --deps     installe SDK et chaîne de compilation dans $HOME,
#                          sans toucher au système ni demander de mot de passe
#    ./build.sh --propre   repart d'un répertoire de construction vide
#
#  Rien n'est installé à l'échelle du système : le SDK va dans ~/pico/pico-sdk
#  et la chaîne ARM dans ~/.local/opt/. Qui préfère les paquets de sa
#  distribution les installe lui-même — le script les trouvera aussi.
#
#  Licence MIT — Bretagne Namasté — https://bretagne-namaste.com
# ===========================================================================
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_VERSION="2.3.1"          # 2.0.0 minimum pour le RP2350
ARM_VERSION="14.2.rel1"
SDK_DEFAUT="$HOME/pico/pico-sdk"
CARTE="${PICO_BOARD:-pico2}"

#  --- Quelle chaîne ARM télécharger ? --------------------------------------
#  ARM publie une archive par couple système/architecture. L'ancienne version
#  de ce script codait « x86_64 » en dur : `--deps` échouait donc sur un Mac
#  Apple Silicon comme sur un Raspberry Pi, avec une erreur 404 peu parlante.
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
                *)             echo "" ;;     # architecture non publiée par ARM
            esac ;;
        *)  echo "" ;;
    esac
}

HOTE_ARM="$(hote_arm)"
ARM_DEFAUT="$HOME/.local/opt/arm-gnu-toolchain-${ARM_VERSION}-${HOTE_ARM}-arm-none-eabi"

vert()  { printf '\033[0;32m%s\033[0m\n' "$*"; }
jaune() { printf '\033[0;33m%s\033[0m\n' "$*"; }
rouge() { printf '\033[0;31m%s\033[0m\n' "$*"; }

# --- 1. où est le SDK ? ----------------------------------------------------
trouver_sdk() {
    for c in "${PICO_SDK_PATH:-}" "$SDK_DEFAUT" /usr/share/pico-sdk \
             /opt/pico-sdk "$HOME/pico-sdk"; do
        [ -n "$c" ] && [ -f "$c/pico_sdk_init.cmake" ] && { echo "$c"; return; }
    done
}

# --- 2. où est la chaîne ARM ? --------------------------------------------
trouver_arm() {
    command -v arm-none-eabi-gcc >/dev/null 2>&1 && { dirname "$(command -v arm-none-eabi-gcc)"; return; }
    for c in "$ARM_DEFAUT/bin" "$HOME"/.local/opt/arm-gnu-toolchain-*/bin; do
        [ -x "$c/arm-none-eabi-gcc" ] && { echo "$c"; return; }
    done
}

installer_deps() {
    if [ -z "$(trouver_sdk)" ]; then
        jaune "· Téléchargement du Pico SDK ${SDK_VERSION} → ${SDK_DEFAUT}"
        mkdir -p "$(dirname "$SDK_DEFAUT")"
        git clone --branch "$SDK_VERSION" --depth 1 \
            https://github.com/raspberrypi/pico-sdk.git "$SDK_DEFAUT"
        #  Sans TinyUSB, la compilation échoue sur « tusb.h: No such file ».
        git -C "$SDK_DEFAUT" submodule update --init --depth 1 lib/tinyusb
        vert "✓ SDK installé"
    else
        vert "✓ SDK déjà présent : $(trouver_sdk)"
    fi

    if [ -z "$(trouver_arm)" ]; then
        if [ -z "$HOTE_ARM" ]; then
            rouge "✗ ARM ne publie pas de chaîne précompilée pour $(uname -s)/$(uname -m)."
            rouge "  Installez « gcc-arm-none-eabi » par votre gestionnaire de paquets,"
            rouge "  ou indiquez une chaîne existante : ARM_TOOLCHAIN_PATH=/chemin ./build.sh"
            exit 2
        fi
        jaune "· Téléchargement de la chaîne ARM ${ARM_VERSION} pour ${HOTE_ARM} (≈ 140 Mo)"
        jaune "  → ${ARM_DEFAUT}"
        mkdir -p "$HOME/.local/opt"
        local url="https://developer.arm.com/-/media/Files/downloads/gnu/${ARM_VERSION}/binrel/arm-gnu-toolchain-${ARM_VERSION}-${HOTE_ARM}-arm-none-eabi.tar.xz"
        local tmp; tmp="$(mktemp -d)"
        curl -L --progress-bar "$url" -o "$tmp/arm.tar.xz"
        tar -xf "$tmp/arm.tar.xz" -C "$HOME/.local/opt"
        rm -rf "$tmp"
        vert "✓ Chaîne ARM installée"
    else
        vert "✓ Chaîne ARM déjà présente : $(trouver_arm)"
    fi
}

# --- 3. déroulement --------------------------------------------------------
[ "${1:-}" = "--deps" ] && { installer_deps; shift || true; }
[ "${1:-}" = "--propre" ] && { rm -rf "$ICI/build"; shift || true; }

SDK="$(trouver_sdk || true)"
ARM="$(trouver_arm || true)"

if [ -z "$SDK" ] || [ -z "$ARM" ]; then
    rouge "Il manque de quoi construire :"
    [ -z "$SDK" ] && echo "  · le Pico SDK 2.x (RP2350)"
    [ -z "$ARM" ] && echo "  · la chaîne de compilation arm-none-eabi"
    echo
    echo "  Tout installer dans votre dossier personnel, sans mot de passe :"
    echo "      ./build.sh --deps"
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
    echo "  Windows : ce script demande un shell POSIX. Passez par WSL 2"
    echo "  (« wsl --install », puis Ubuntu) et relancez-le depuis Linux."
    exit 2
fi

export PICO_SDK_PATH="$SDK"
export PATH="$ARM:$PATH"

#  Ce fichier appartient au SDK et doit rester synchronisé avec lui : on le
#  recopie à chaque construction plutôt que de le figer dans le dépôt.
cp "$SDK/external/pico_sdk_import.cmake" "$ICI/pico_sdk_import.cmake"

vert "· SDK   : $SDK"
vert "· ARM   : $(arm-none-eabi-gcc --version | head -1)"
vert "· Carte : $CARTE"

mkdir -p "$ICI/build"
cd "$ICI/build"
cmake .. -DPICO_BOARD="$CARTE" -DCMAKE_BUILD_TYPE=Release >/dev/null
cmake --build . -j"$(nproc 2>/dev/null || echo 4)"

echo
vert "✓ Construit :"
for f in phytosense.uf2 phytosense.elf phytosense.bin; do
    [ -f "$f" ] && printf '    %-18s %s\n' "$f" "$(du -h "$f" | cut -f1)"
done
arm-none-eabi-size phytosense.elf | tail -1 | awk \
    '{printf "    mémoire            %d octets de code, %d de données\n", $1, $3}'
echo
#  Le point de montage de la carte diffère d'un système à l'autre : Debian et
#  Ubuntu montent sous /media/$USER, Fedora et Red Hat sous /run/media/$USER,
#  macOS sous /Volumes. On cherche plutôt que de deviner.
monter_ou() {
    local d
    for d in "/media/$USER/RP2350" "/run/media/$USER/RP2350" \
             "/media/$USER/RPI-RP2" "/run/media/$USER/RPI-RP2" \
             "/Volumes/RP2350" "/Volumes/RPI-RP2"; do
        [ -d "$d" ] && { echo "$d"; return; }
    done
    echo ""
}

echo "  Programmer : brancher la carte en maintenant BOOTSEL, puis"
CIBLE="$(monter_ou)"
if [ -n "$CIBLE" ]; then
    vert "      cp build/phytosense.uf2 $CIBLE/       ← carte détectée"
else
    echo "      cp build/phytosense.uf2 <point de montage>/"
    echo
    echo "      Debian, Ubuntu, Mint  : /media/\$USER/RP2350/"
    echo "      Fedora, Red Hat       : /run/media/\$USER/RP2350/"
    echo "      macOS                 : /Volumes/RP2350/"
    echo "      Windows (WSL)         : /mnt/<lettre>/ — la carte apparaît"
    echo "                              comme un disque amovible"
fi
