#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/pick_python.sh
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

# ---------------------------------------------------------------------------
#  Choisit l'interpréteur Python à utiliser pour construire l'environnement.
#
#  Sous GNU/Linux, le Python de Homebrew embarque sa propre glibc et son
#  propre chargeur dynamique : il ne sait pas résoudre les bibliothèques du
#  système (libGL.so.1, libportaudio.so.2…). Un environnement virtuel bâti
#  dessus produit une interface graphique qui refuse de démarrer, avec un
#  message trompeur. On lui préfère donc l'interpréteur de la distribution.
#
#  Écrit le chemin retenu sur la sortie standard. Toujours un résultat.
# ---------------------------------------------------------------------------
set -eu

candidat=$(command -v python3 2>/dev/null || echo python3)

# Sous macOS et Windows, Homebrew ne pose pas ce problème : on garde le défaut.
case "$(uname -s 2>/dev/null || echo inconnu)" in
  Linux) ;;
  *) echo "$candidat"; exit 0 ;;
esac

reel=$(readlink -f "$candidat" 2>/dev/null || echo "$candidat")

case "$reel" in
  *linuxbrew*)
    for autre in /usr/bin/python3 /usr/local/bin/python3 /bin/python3; do
      if [ -x "$autre" ]; then
        version=$("$autre" -c 'import sys;print("%d%02d" % sys.version_info[:2])' 2>/dev/null || echo 0)
        if [ "$version" -ge 309 ] 2>/dev/null; then
          echo "$autre"
          exit 0
        fi
      fi
    done
    ;;
esac

echo "$candidat"
