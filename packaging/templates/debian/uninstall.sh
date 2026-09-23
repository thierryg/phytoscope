#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — packaging/templates/debian/uninstall.sh
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
#  Remove PhytoScope, when it was installed from a package.
#
#  This script only calls the package manager: the package manager is what
#  knows what it put down. It exists so that "how do I uninstall" is found in
#  the same place as everything else, without having to remember whether this
#  machine speaks apt or dnf.
#
#  YOUR SETTINGS AND YOUR SESSIONS ARE NOT TOUCHED:
#      ~/.config/phytoscope           settings and log
#      ~/.local/share/phytoscope      recorded sessions
#  Uninstalling is not a request to be forgotten.
# ===========================================================================
set -e

CIBLE="/usr/share/phytoscope"
if [ -f "$CIBLE/labels.sh" ]; then
    # shellcheck disable=SC1091
    . "$CIBLE/labels.sh"
    charger_libelles "$CIBLE/languages" || true
else
    tl() { _d="$2"; shift 2; while [ "$#" -ge 2 ]; do
               _d="$(printf '%s' "$_d" | sed "s|{$1}|$2|g")"; shift 2; done
           printf '%s' "$_d"; }
fi

phytoscope-desktop-icon --remove 2>/dev/null || true

if command -v apt-get >/dev/null 2>&1; then
    echo "$(tl T_DESINSTALLATION_PAR "Uninstalling with {tool}..." tool "apt")"
    sudo apt-get remove -y phytoscope
elif command -v dnf >/dev/null 2>&1; then
    echo "$(tl T_DESINSTALLATION_PAR "Uninstalling with {tool}..." tool "dnf")"
    sudo dnf remove -y phytoscope
elif command -v yum >/dev/null 2>&1; then
    echo "$(tl T_DESINSTALLATION_PAR "Uninstalling with {tool}..." tool "yum")"
    sudo yum remove -y phytoscope
elif command -v rpm >/dev/null 2>&1; then
    echo "$(tl T_DESINSTALLATION_PAR "Uninstalling with {tool}..." tool "rpm")"
    sudo rpm -e phytoscope
else
    echo "$(tl T_AUCUN_GESTIONNAIRE "No recognised package manager.")" >&2
    exit 1
fi

#  What is kept, and how to erase it. Said in the language the user chose,
#  because this is the one part of the operation they have a decision to make
#  about.
echo ""
echo "$(tl T_RETIRE "PhytoScope has been removed.")"
echo ""
echo "$(tl T_DONNEES_CONSERVEES "YOUR DATA IS KEPT:")"
echo "    ~/.config/phytoscope           $(tl T_DONNEES_REGLAGES "settings and log")"
echo "    ~/.local/share/phytoscope      $(tl T_DONNEES_SEANCES "recorded sessions")"
echo ""
echo "$(tl T_POUR_EFFACER_AUSSI "To erase them as well:")"
echo "    rm -rf ~/.config/phytoscope ~/.local/share/phytoscope"
echo ""
