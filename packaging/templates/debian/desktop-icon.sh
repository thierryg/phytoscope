#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — packaging/templates/debian/desktop-icon.sh
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
#  Put the PhytoScope icon on the Desktop, or take it away.
#
#  Why a script rather than a question during installation: `apt` and `dnf`
#  install without interaction, often with no graphical session, and
#  sometimes for an account other than the one that will use the software.
#  Asking there would be asking the wrong person at the wrong moment. So we
#  ask when the user wants it, and only then.
#
#      phytoscope-desktop-icon            put the icon in place
#      phytoscope-desktop-icon --remove   take it away
# ===========================================================================
set -e
CIBLE="/usr/share/phytoscope"
SOURCE="/usr/share/applications/phytoscope.desktop"
[ -f "$SOURCE" ] || SOURCE="$HOME/.local/share/applications/phytoscope.desktop"

if [ -f "$CIBLE/labels.sh" ]; then
    # shellcheck disable=SC1091
    . "$CIBLE/labels.sh"
    charger_libelles "$CIBLE/languages" || true
else
    tl() { _d="$2"; shift 2; while [ "$#" -ge 2 ]; do
               _d="$(printf '%s' "$_d" | sed "s|{$1}|$2|g")"; shift 2; done
           printf '%s' "$_d"; }
fi

#  The desktop folder is named in the user's own language, which is why we ask
#  xdg-user-dir rather than guessing. The three fallbacks cover machines with
#  no xdg-utils installed.
trouver_le_bureau() {
    if command -v xdg-user-dir >/dev/null 2>&1; then
        d="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
        [ -n "$d" ] && [ -d "$d" ] && { echo "$d"; return; }
    fi
    for essai in "$HOME/Desktop" "$HOME/Bureau" "$HOME/Escritorio"; do
        [ -d "$essai" ] && { echo "$essai"; return; }
    done
    echo ""
}

BUREAU="$(trouver_le_bureau)"
if [ -z "$BUREAU" ]; then
    echo "$(tl T_BUREAU_INTROUVABLE "Desktop folder not found.")" >&2
    exit 1
fi

if [ "${1:-}" = "--remove" ] || [ "${1:-}" = "--retirer" ]; then
    rm -f "$BUREAU/phytoscope.desktop"
    echo "$(tl T_ICONE_RETIREE "Icon removed from the Desktop.")"
    exit 0
fi

if [ ! -f "$SOURCE" ]; then
    echo "$(tl T_MENU_INTROUVABLE "Menu entry not found - is PhytoScope installed?")" >&2
    exit 1
fi
cp "$SOURCE" "$BUREAU/phytoscope.desktop"
chmod +x "$BUREAU/phytoscope.desktop"
#  GNOME additionally requires this attribute, without which it shows
#  "Untrusted application launcher" instead of the icon.
command -v gio >/dev/null 2>&1 && \
    gio set "$BUREAU/phytoscope.desktop" metadata::trusted true 2>/dev/null || true
echo "$(tl T_ICONE_POSEE "Icon placed on the Desktop.")"
