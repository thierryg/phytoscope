#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — packaging/gabarits/debian/icone-bureau.sh
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
#  Pose ou retire l'icône PhytoScope sur le Bureau.
#
#  Pourquoi un script plutôt qu'une question à l'installation : `apt` et `dnf`
#  installent sans interaction, souvent sans session graphique et parfois pour
#  un autre compte que celui qui s'en servira. Poser la question là serait la
#  poser à la mauvaise personne, au mauvais moment. On la pose donc quand
#  l'utilisateur la veut, et lui seul.
#
#      phytoscope-icone-bureau            pose l'icône
#      phytoscope-icone-bureau --retirer  la retire
# ===========================================================================
set -e
SOURCE="/usr/share/applications/phytoscope.desktop"
[ -f "$SOURCE" ] || SOURCE="$HOME/.local/share/applications/phytoscope.desktop"

trouver_le_bureau() {
    if command -v xdg-user-dir >/dev/null 2>&1; then
        d="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
        [ -n "$d" ] && [ -d "$d" ] && { echo "$d"; return; }
    fi
    for essai in "$HOME/Bureau" "$HOME/Desktop" "$HOME/Escritorio"; do
        [ -d "$essai" ] && { echo "$essai"; return; }
    done
    echo ""
}

BUREAU="$(trouver_le_bureau)"
if [ -z "$BUREAU" ]; then
    echo "Dossier du Bureau introuvable." >&2
    exit 1
fi

if [ "${1:-}" = "--retirer" ]; then
    rm -f "$BUREAU/phytoscope.desktop"
    echo "Icône retirée du Bureau."
    exit 0
fi

if [ ! -f "$SOURCE" ]; then
    echo "Entrée de menu introuvable — PhytoScope est-il installé ?" >&2
    exit 1
fi
cp "$SOURCE" "$BUREAU/phytoscope.desktop"
chmod +x "$BUREAU/phytoscope.desktop"
#  GNOME exige en plus cet attribut, sans quoi il affiche « Lancement
#  d'application non fiable » au lieu de l'icône.
command -v gio >/dev/null 2>&1 && \
    gio set "$BUREAU/phytoscope.desktop" metadata::trusted true 2>/dev/null || true
echo "Icône posée sur le Bureau."
