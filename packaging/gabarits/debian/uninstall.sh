#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — packaging/gabarits/debian/uninstall.sh
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
#  Retire PhytoScope, installé par paquet.
#
#  Ce script ne fait qu'appeler le gestionnaire de paquets : c'est lui qui
#  sait ce qu'il a posé. Il existe pour qu'on trouve « comment désinstaller »
#  au même endroit que le reste, sans avoir à se rappeler si la machine parle
#  apt ou dnf.
#
#  VOS RÉGLAGES ET VOS SÉANCES NE SONT PAS TOUCHÉS :
#      ~/.config/phytoscope           réglages et journal
#      ~/.local/share/phytoscope      séances enregistrées
#  Une désinstallation n'est pas une demande d'oubli.
# ===========================================================================
set -e

phytoscope-icone-bureau --retirer 2>/dev/null || true

if command -v apt-get >/dev/null 2>&1; then
    echo "Désinstallation par apt…"
    sudo apt-get remove -y phytoscope
elif command -v dnf >/dev/null 2>&1; then
    echo "Désinstallation par dnf…"
    sudo dnf remove -y phytoscope
elif command -v yum >/dev/null 2>&1; then
    sudo yum remove -y phytoscope
elif command -v rpm >/dev/null 2>&1; then
    sudo rpm -e phytoscope
else
    echo "Aucun gestionnaire de paquets reconnu." >&2
    exit 1
fi

cat <<'FIN'

PhytoScope est retiré.

VOS DONNÉES SONT CONSERVÉES :
    ~/.config/phytoscope           réglages et journal
    ~/.local/share/phytoscope      séances enregistrées

Pour les effacer aussi :
    rm -rf ~/.config/phytoscope ~/.local/share/phytoscope

FIN
