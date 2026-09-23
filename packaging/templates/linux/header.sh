#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — packaging/templates/linux/header.sh
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
#  PhytoScope @VERSION@ - installateur autonome pour GNU/Linux
#
#  Ce fichier est a la fois un script et une archive : le shell lit l'en-tete
#  et s'arrete a la derniere ligne connue ; tout ce qui suit est une archive
#  compressee. C'est le principe des installateurs .run de NVIDIA ou de
#  VMware, et l'equivalent libre de ce que produit InstallShield.
#
#  Il fonctionne sur les distributions qui n'ont ni .deb ni .rpm - Arch,
#  openSUSE, Alpine, NixOS, Slackware - et s'installe SANS privileges dans le
#  dossier personnel.
#
#      ./PhytoScope-@VERSION@-Linux.run              installation guidee
#      ./PhytoScope-@VERSION@-Linux.run --tui        en mode texte
#      ./PhytoScope-@VERSION@-Linux.run --uninstall  desinstaller
#      ./PhytoScope-@VERSION@-Linux.run --help       toutes les options
#
#  @EDITEUR@ - @AUTEUR@ - @SITE@ - licence @LICENCE@
# ===========================================================================
set -eu

VERSION="@VERSION@"
RELEASE="@RELEASE@"
EMPREINTE="@EMPREINTE@"
LIGNES_ENTETE=@LIGNES@
MOI="$0"

#  Ou l'on note ce qui a ete installe : c'est ce fichier que --uninstall
#  relit pour savoir quoi retirer, plutot que de deviner.
REGISTRE="$HOME/.local/share/phytoscope/installation.conf"

if [ -t 1 ]; then
    VERT='\033[0;32m'; JAUNE='\033[0;33m'; ROUGE='\033[0;31m'
    GRIS='\033[0;90m'; NEUTRE='\033[0m'
else
    VERT=''; JAUNE=''; ROUGE=''; GRIS=''; NEUTRE=''
fi

dire()  { printf '%b\n' "$*"; }
bien()  { printf "${VERT}  [ok] %s${NEUTRE}\n" "$*"; }
souci() { printf "${JAUNE}  [!] %s${NEUTRE}\n" "$*"; }
echec() { printf "${ROUGE}  [x] %s${NEUTRE}\n" "$*" >&2; }
etape() { printf "${GRIS}   .  %s${NEUTRE}\n" "$*"; }

@COUCHE_INTERFACE@

aide() {
    cat <<'AIDE'
PhytoScope @VERSION@ - standalone installer for GNU/Linux

  ./PhytoScope-@VERSION@-Linux.run [options]

Interface
  (none)            graphical when there is a desktop, text otherwise
  --gui             force the graphical interface (zenity, kdialog)
  --tui             force text-mode boxes (whiptail, dialog)
  --text            force plain lines, with no boxes

Installation
  --prefix DIR      install somewhere other than the default directory
  --desktop         put the icon on the Desktop, without asking
  --no-desktop      do not put it there
  --launch          start the software at the end, without asking
  --no-launch       do not start it
  --language CODE   force the language (en fr es pt it id ru zh ja ko ar)
                    otherwise it is the very first question asked
  --with-system-dependencies
                    also install the missing system libraries (libGL,
                    libxcb, portaudio and so on). REQUIRES privileges:
                    the installer will call your package manager.
                    Without this option it merely names them.
  -y, --yes         ask nothing (unattended installation)

Other
  --uninstall       uninstall PhytoScope
  --check           verify the archive's integrity, without installing
  --extract DIR     unpack without installing
  --version         print the version
  -h, --help        this help

Without privileges: run from an ordinary account, the installer puts itself in
~/.local/opt/phytoscope and never calls sudo. Run as root, it installs into
/opt/phytoscope with a launcher in /usr/local/bin.

@EDITEUR@ - @AUTEUR@ - @SITE@ - licence @LICENCE@
AIDE
    exit 0
}

charge() {
    tail -n +$((LIGNES_ENTETE + 1)) "$MOI"
}

verifier() {
    if ! command -v sha256sum >/dev/null 2>&1; then
        souci "${T_SHA_ABSENT:-sha256sum missing: cannot verify}"
        return 0
    fi
    calculee="$(charge | sha256sum | cut -d' ' -f1)"
    if [ "$calculee" = "$EMPREINTE" ]; then
        bien "${T_ARCHIVE_INTACTE:-archive intact}"
        return 0
    fi
    echec "${T_ARCHIVE_ABIMEE:-archive DAMAGED}"
    dire "      ${T_EMPREINTE_ATTENDUE:-expected} : $EMPREINTE"
    dire "      ${T_EMPREINTE_OBTENUE:-got} : $calculee"
    dire "      ${T_RETELECHARGER:-Download the file again.}"
    return 1
}

extraire() {
    mkdir -p "$1"
    charge | tar xz -C "$1"
}

extraire_un() {
    #  Un seul fichier de l'archive, sans tout deplier : sert a montrer la
    #  licence avant que l'utilisateur ne se soit engage a quoi que ce soit.
    charge | tar xz -C "$2" "$1" 2>/dev/null || true
}

# --------------------------------------------------------------- options
PREFIXE=""
LIBS_SYSTEME=0
LANGUE_IMPOSEE=""
EXTRAIRE=""
SANS_QUESTION=0
ICONE_BUREAU=""
LANCER=""
DESINSTALLER=0

while [ $# -gt 0 ]; do
    case "$1" in
        -h|--help)    aide ;;
        --check)      verifier; exit $? ;;
        --version)    echo "$VERSION-$RELEASE"; exit 0 ;;
        --extract)    EXTRAIRE="${2:?--extract needs a directory}"; shift 2 ;;
        --prefix)     PREFIXE="${2:?--prefix needs a directory}"; shift 2 ;;
        --language|--lang|--langue)
                      LANGUE_IMPOSEE="${2:?--language needs a code}"; shift 2 ;;
        --with-system-dependencies|--avec-dependances-systeme)
                      LIBS_SYSTEME=1; shift ;;
        --uninstall|--desinstaller) DESINSTALLER=1; shift ;;
        --gui|--graphique)  INTERFACE="graphique"; shift ;;
        --tui)              INTERFACE="tui"; shift ;;
        --text|--texte)     INTERFACE="texte"; shift ;;
        -y|--yes)     SANS_QUESTION=1; shift ;;
        --desktop)    ICONE_BUREAU="oui"; shift ;;
        --no-desktop) ICONE_BUREAU="non"; shift ;;
        --launch)     LANCER="oui"; shift ;;
        --no-launch)  LANCER="non"; shift ;;
        *)            echec "$(tl T_OPTION_INCONNUE "unknown option: {option}" option "$1")"; dire "  ${T_HELP_POUR_LISTE:---help for the list.}"; exit 2 ;;
    esac
done

choisir_interface

if [ -n "$EXTRAIRE" ]; then
    extraire "$EXTRAIRE"
    bien "$(tl T_DECOMPRESSE_DANS "extracted into {directory}" directory "$EXTRAIRE")"
    exit 0
fi

# ---------------------------------------------------------- desinstaller
if [ "$DESINSTALLER" -eq 1 ]; then
    #  On relit ce qu'on avait note a l'installation ; a defaut, on cherche
    #  aux deux endroits habituels.
    if [ -f "$REGISTRE" ]; then
        . "$REGISTRE"
    else
        for essai in "$HOME/.local/opt/phytoscope" "/opt/phytoscope"; do
            [ -d "$essai" ] && { PREFIXE_INSTALLE="$essai"; break; }
        done
        PREFIXE_INSTALLE="${PREFIXE_INSTALLE:-}"
    fi
    CIBLE="${PREFIXE:-${PREFIXE_INSTALLE:-}}"
    if [ -z "$CIBLE" ] || [ ! -d "$CIBLE" ]; then
        ui_erreur "$(tl T_DESINSTALLATION "Uninstallation")" \
            "$(tl T_PAS_INSTALLE "PhytoScope does not appear to be installed.")\n\n$(tl T_SI_AILLEURS "If you installed it elsewhere:")\n    $MOI --uninstall --prefix /the/folder"
        exit 1
    fi
    if [ -x "$CIBLE/uninstall.sh" ]; then
        if [ "$SANS_QUESTION" -eq 1 ]; then
            "$CIBLE/uninstall.sh" -y
        else
            reponse="$(ui_question "$(tl T_DESINSTALLATION "Uninstallation")" \
                "$(tl T_RETIRER_QUESTION "Remove PhytoScope from")\n    $CIBLE\n\n$(tl T_DONNEES_SERONT_GARDEES "Your settings and your sessions will be KEPT.")" "non")"
            [ "$reponse" = "oui" ] || { dire "  $(tl T_ANNULE "Cancelled.")"; exit 0; }
            "$CIBLE/uninstall.sh" -y
            ui_info "$(tl T_DESINSTALLATION "Uninstallation")" \
                "$(tl T_RETIRE "PhytoScope has been removed.")\n\n$(tl T_DONNEES_CONSERVEES "YOUR DATA IS KEPT:")\n    ~/.config/phytoscope\n    ~/.local/share/phytoscope"
        fi
    else
        echec "$(tl T_DESINST_INTROUVABLE "uninstaller not found in {directory}" \
                     directory "$CIBLE")"
        exit 1
    fi
    exit 0
fi

# ----------------------------------------------------------- installation
dire ""
dire "  PhytoScope @TITRE_VERSION@"
dire "  @EDITEUR@ - @AUTEUR@"
dire "  @SITE@ - @COURRIEL@ - $(tl T_ENTETE_EDITEUR "licence") @LICENCE@"
dire ""

# ---------------------------------------------------------------- la langue
#  AVANT TOUT LE RESTE. C'est la premiere question, parce que toutes les
#  suivantes seront posees dans la langue choisie ici - licence comprise.
#
#  On DEMANDE, on ne devine pas : la contrainte C-31 interdit la detection
#  automatique de la locale, et elle vaut ici aussi. Une machine dont
#  l'environnement dit « fr_FR » peut etre celle d'un atelier ou l'on
#  travaille en anglais.
#
#  Le choix est ensuite ecrit dans les reglages, que PhytoScope relit a
#  chaque demarrage : l'installateur et le logiciel parlent la meme langue
#  sans se concerter.
LANGUE=""
BAC_LANGUES="$(mktemp -d)"
extraire_un "languages" "$BAC_LANGUES" 2>/dev/null || true

charger_langue() {
    #  $1 = code. Charge le catalogue, ou ne fait rien s'il manque : les
    #  libellés gardent alors leur valeur de repli, en francais.
    if [ -f "$BAC_LANGUES/languages/$1.sh" ]; then
        # shellcheck disable=SC1090
        . "$BAC_LANGUES/languages/$1.sh"
        LANGUE="$1"
        return 0
    fi
    return 1
}

#  `t` remplit les champs nommes d'un libelle : t "$T_INSTALLATION_DANS" \
#  directory "$PREFIXE". Un sed par champ, ce qui suffit pour des libelles qui
#  n'en portent jamais plus de deux.
#  Resolve a label BY NAME, fall back if the catalogue is missing, then
#  substitute its {fields}.
#
#  Why this exists rather than "${T_NAME:-default}". A default value that
#  itself contains braces closes the parameter expansion early:
#
#      ${T_OPTION_INCONNUE:-unknown option: {option}}
#                                          ^ this } ends the expansion
#
#  bash then chokes on the stray brace, and the script does not even parse.
#  Found the hard way: the first version of this patch broke `sh -n`.
tl() {
    _nom="$1"; shift
    _defaut="$1"; shift
    eval "_valeur=\${$_nom}"
    [ -n "$_valeur" ] || _valeur="$_defaut"
    t "$_valeur" "$@"
}

#  Pad a label to a width counted in CHARACTERS.
#
#  `printf "%-18s"` counts BYTES, so "Désinstaller" — thirteen characters,
#  fourteen bytes — comes out one column short, and the colons in a summary
#  no longer line up. `wc -m` counts characters when the locale is UTF-8 and
#  falls back to bytes when it is not, which is the old behaviour rather than
#  a failure.
#
#  Not perfect for Chinese, Japanese or Korean, whose glyphs occupy two
#  columns each; no POSIX tool knows display width. Those three languages get
#  a column that is too narrow rather than one that is too wide, which reads
#  better than the reverse.
colonne() {
    _texte="$1"
    _large="$2"
    _n="$(printf '%s' "$_texte" | wc -m 2>/dev/null)" || _n=""
    [ -n "$_n" ] || _n="$(printf '%s' "$_texte" | wc -c)"
    printf '%s' "$_texte"
    _reste=$((_large - _n))
    while [ "$_reste" -gt 0 ]; do
        printf ' '
        _reste=$((_reste - 1))
    done
}

t() {
    _texte="$1"; shift
    while [ "$#" -ge 2 ]; do
        _texte="$(printf '%s' "$_texte" | sed "s|{$1}|$(printf '%s' "$2" | sed 's|[&|\\]|\\&|g')|g")"
        shift 2
    done
    printf '%s' "$_texte"
}

if [ -f "$BAC_LANGUES/languages/index.sh" ]; then
    # shellcheck disable=SC1091
    . "$BAC_LANGUES/languages/index.sh"

    if [ -n "$LANGUE_IMPOSEE" ]; then
        #  A code that has no catalogue is not a reason to stop: English is
        #  the source language, and every call site carries its English text.
        charger_langue "$LANGUE_IMPOSEE" || charger_langue en
    elif [ "$SANS_QUESTION" -eq 1 ]; then
        #  Unattended: English, unless --language said otherwise. Nobody is
        #  there to be asked, and guessing from the locale is forbidden (C-31).
        charger_langue en
    else
        charger_langue en          # so that the question can be asked at all
        CHOIX=""
        if [ "$INTERFACE" != "texte" ]; then
            CHOIX="$(ui_langue "$T_LANGUE_TITRE" "$T_LANGUE_INVITE")"
        fi
        if [ -z "$CHOIX" ]; then
            #  En mode texte, un menu numerote : aucun outil a installer, et
            #  cela fonctionne au travers d'un ssh.
            dire "  $T_LANGUE_TITRE"
            dire "  $T_LANGUE_INVITE"
            dire ""
            _i=0
            for _c in $LANGUES_CODES; do
                _i=$((_i + 1))
                eval "_nom=\$LANGUE_NOM_$_c"
                printf '    %2d) %s\n' "$_i" "$_nom"
            done
            dire ""
            printf '  %s' "$(t "$T_LANGUE_CHOIX" n "$_i")"
            read -r _rep || _rep=""
            _i=0
            for _c in $LANGUES_CODES; do
                _i=$((_i + 1))
                [ "$_rep" = "$_i" ] && CHOIX="$_c"
            done
        fi
        [ -n "$CHOIX" ] && charger_langue "$CHOIX"
    fi
    eval "_nom=\$LANGUE_NOM_$LANGUE"
    bien "$(t "$T_LANGUE_RETENUE" language "${_nom:-$LANGUE}")"
fi

verifier || {
    ui_erreur "$(tl T_INSTALLATION "Installation")" \
              "$(tl T_ARCHIVE_ABIMEE "The archive is damaged.")\n$(tl T_RETELECHARGER "Download the file again.")"
    exit 1
}

#  La licence, avant tout engagement. En mode graphique et en mode tui, la
#  case a cocher est la : c'est ce qu'on attend d'un installateur.
if [ "$SANS_QUESTION" -eq 0 ] && [ "$INTERFACE" != "texte" ]; then
    BAC_LICENCE="$(mktemp -d)"
    extraire_un "LICENSE.txt" "$BAC_LICENCE"
    if [ "$(ui_licence "$BAC_LICENCE/LICENSE.txt")" != "accepte" ]; then
        rm -rf "$BAC_LICENCE"
        dire "  ${T_LICENCE_REFUSEE:-Licence refusee - installation annulee.}"
        exit 0
    fi
    rm -rf "$BAC_LICENCE"
fi

#  Ou installer : /opt si l'on est administrateur, le dossier personnel
#  sinon. Aucun sudo n'est appele - on n'eleve jamais les privileges a
#  l'insu de l'utilisateur.
if [ -z "$PREFIXE" ]; then
    if [ "$(id -u)" -eq 0 ]; then
        DEFAUT="/opt/phytoscope"
    else
        DEFAUT="$HOME/.local/opt/phytoscope"
    fi
    if [ "$SANS_QUESTION" -eq 0 ] && [ "$INTERFACE" != "texte" ]; then
        PREFIXE="$(ui_dossier "$DEFAUT")"
        [ -n "$PREFIXE" ] || { dire "  $(tl T_ANNULE "Cancelled.")"; exit 0; }
    else
        PREFIXE="$DEFAUT"
    fi
fi

case "$PREFIXE" in
    /opt/*|/usr/*) BINAIRE="/usr/local/bin"
                   BUREAU="/usr/share/applications"
                   ICONES="/usr/share/icons/hicolor/scalable/apps" ;;
    "$HOME/.local/opt/"*) BINAIRE="$HOME/.local/bin"
                   BUREAU="$HOME/.local/share/applications"
                   ICONES="$HOME/.local/share/icons/hicolor/scalable/apps" ;;
    *)             BINAIRE="$PREFIXE/bin"
                   BUREAU="$PREFIXE/share/applications"
                   ICONES="$PREFIXE/share/icons" ;;
esac

dire "  $(tl T_INSTALLATION_DANS "Installing into: {directory}" directory "$PREFIXE")"
dire "  $(tl T_LANCEUR "Launcher") : $BINAIRE/phytoscope"
[ "$(id -u)" -ne 0 ] && dire "  ${GRIS}$(tl T_COMPTE_ORDINAIRE "(ordinary account - no privileges requested)")${NEUTRE}"
dire ""

if [ "$SANS_QUESTION" -eq 0 ] && [ "$INTERFACE" = "texte" ]; then
    [ "$(ui_question "$(tl T_INSTALLATION "Installation")" \
                     "$(tl T_CONTINUER "Continue?")" "oui")" = "oui" ] || {
        dire "  $(tl T_ANNULE "Cancelled.")"; exit 0; }
    dire ""
fi

#  Les questions d'option AVANT la copie : on ne veut pas interrompre une
#  barre de progression pour poser une question.
if [ -z "$ICONE_BUREAU" ]; then
    if [ "$SANS_QUESTION" -eq 1 ]; then
        ICONE_BUREAU="non"
    else
        ICONE_BUREAU="$(ui_question "$(tl T_OPTIONS "Options")" \
            "$(tl T_ICONE_QUESTION "Add a PhytoScope icon to the Desktop?")" "oui")"
    fi
fi

# -- 1. Python --------------------------------------------------------------
#  Celui de la DISTRIBUTION d'abord. Sur une machine ou Homebrew est
#  installe, le PATH donne d'abord son Python ; or les roues de Qt batties
#  dessus ne trouvent pas les bibliotheques graphiques du systeme.
convient() {
    [ -x "$1" ] || return 1
    case "$1" in */linuxbrew/*|*/Homebrew/*) return 1 ;; esac
    "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)' \
        2>/dev/null || return 1
    "$1" -c 'import venv' 2>/dev/null || return 1
    return 0
}

PY=""
for candidat in /usr/bin/python3 /usr/bin/python3.13 /usr/bin/python3.12 \
                /usr/bin/python3.11 /usr/bin/python3.10 /usr/bin/python3.9; do
    if convient "$candidat"; then PY="$candidat"; break; fi
done
if [ -z "$PY" ]; then
    for nom in python3 python3.13 python3.12 python3.11 python3.10 python3.9; do
        chemin="$(command -v "$nom" 2>/dev/null || true)"
        if [ -n "$chemin" ] && convient "$chemin"; then PY="$chemin"; break; fi
    done
fi
#  Rien n'echoue ici si aucun Python ne convient : la charge peut en
#  transporter un. Le verdict est rendu apres la decompression.
PY_EMBARQUE=""
if [ -n "$PY" ]; then
    bien "$(tl T_PY_SYSTEME "Python: {py} (from the system)" py "$PY")"
else
    souci "$(tl T_PY_AUCUN_SYSTEME "no system Python is suitable - the bundled one will be used")"
fi

# -- 2. la copie, sous une barre de progression ----------------------------
ui_progres_debut
ui_progres 10 "$(tl T_ETAPE_DECOMPRESSION "Extracting the software...")"

if [ -d "$PREFIXE" ]; then
    rm -rf "$PREFIXE/phytoscope" "$PREFIXE/run.py" "$PREFIXE/roues" \
           "$PREFIXE/python"
fi
mkdir -p "$PREFIXE"
extraire "$PREFIXE"
ui_progres 30 "$(tl T_ETAPE_INSTALLE "Software installed.")"

#  L'archive transporte un CPython RELOGEABLE (python-build-standalone) :
#  il fonctionne depuis n'importe quel dossier, sans etre installe, sans
#  privileges et sans toucher au systeme - ce que le projet exige (C-55).
#  C'est ce qui rend cet installateur utilisable sur une machine nue.
if [ -z "$PY" ] && [ -x "$PREFIXE/python/bin/python3" ]; then
    PY="$PREFIXE/python/bin/python3"
    PY_EMBARQUE="oui"
    bien "$(tl T_PY_EMBARQUE "Python: {py} (bundled)" py "$PY")"
elif [ -n "$PY" ] && [ -d "$PREFIXE/python" ]; then
    #  Le systeme en a un qui convient : on n'emporte pas le double.
    rm -rf "$PREFIXE/python"
fi

if [ -z "$PY" ]; then
    ui_progres_fin
    ui_erreur "$(tl T_INSTALLATION "Installation")" \
        "$(tl T_PY_INTROUVABLE "Python 3.9 (with the “venv” module) cannot be found, and this installer does not carry one.")\n\n$(tl T_PY_AIDE_DISTRIBUTIONS "Install it with your package manager:")\n\nDebian, Ubuntu, Mint :\n    sudo apt install python3 python3-venv\n\nFedora, Red Hat :\n    sudo dnf install python3\n\nArch :\n    sudo pacman -S python"
    exit 1
fi

# -- 2 bis. les bibliotheques du systeme -----------------------------------
#  Les roues de Qt, pyqtgraph et sounddevice apportent leurs propres binaires,
#  mais ceux-ci s'appuient sur des bibliotheques du SYSTEME : libGL pour le
#  rendu, libxcb-* pour X11, libportaudio pour le son. Elles ne sont pas
#  installables dans le dossier personnel - libGL, en particulier, doit
#  correspondre au pilote graphique de la machine.
#
#  On les nomme donc precisement plutot que de laisser le logiciel echouer au
#  premier affichage avec un message du chargeur dynamique qui, lui, ne nomme
#  presque jamais la bonne. Les installer exige des privileges, ce que cet
#  installateur ne prend pas de lui-meme (C-55) : il faut --avec-dependances-systeme.
BIBLIOTHEQUES="libGL.so.1 libEGL.so.1 libxkbcommon-x11.so.0 libxcb-cursor.so.0
libxcb-icccm.so.4 libxcb-keysyms.so.1 libxcb-render-util.so.0
libxcb-shape.so.0 libfontconfig.so.1 libdbus-1.so.3 libportaudio.so.2"

PAQUETS_APT="libgl1 libegl1 libxkbcommon-x11-0 libxcb-cursor0 libxcb-icccm4 \
libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 libfontconfig1 libdbus-1-3 \
libportaudio2"
PAQUETS_DNF="mesa-libGL mesa-libEGL libxkbcommon-x11 xcb-util-cursor \
xcb-util-wm xcb-util-keysyms xcb-util-renderutil fontconfig dbus-libs portaudio"
PAQUETS_PACMAN="libglvnd libxkbcommon-x11 xcb-util-cursor xcb-util-wm \
xcb-util-keysyms xcb-util-renderutil fontconfig dbus portaudio"
PAQUETS_ZYPPER="Mesa-libGL1 Mesa-libEGL1 libxkbcommon-x11-0 libxcb-cursor0 \
libxcb-icccm4 libxcb-keysyms1 libxcb-render-util0 libxcb-shape0 fontconfig \
libdbus-1-3 libportaudio2"

manquantes=""
for lib in $BIBLIOTHEQUES; do
    if command -v ldconfig >/dev/null 2>&1; then
        ldconfig -p 2>/dev/null | grep -q "$lib" || manquantes="$manquantes $lib"
    fi
done

if [ -n "$manquantes" ]; then
    #  Quel gestionnaire, et donc quels noms de paquets ?
    GEST=""; PAQUETS=""; INSTALLE=""
    if command -v apt-get >/dev/null 2>&1; then
        GEST="apt"; PAQUETS="$PAQUETS_APT"; INSTALLE="apt-get install -y"
    elif command -v dnf >/dev/null 2>&1; then
        GEST="dnf"; PAQUETS="$PAQUETS_DNF"; INSTALLE="dnf install -y"
    elif command -v pacman >/dev/null 2>&1; then
        GEST="pacman"; PAQUETS="$PAQUETS_PACMAN"; INSTALLE="pacman -S --noconfirm"
    elif command -v zypper >/dev/null 2>&1; then
        GEST="zypper"; PAQUETS="$PAQUETS_ZYPPER"; INSTALLE="zypper install -y"
    fi

    souci "$(tl T_LIBS_MANQUANTES "missing system libraries:{libs}" libs "$manquantes")"

    if [ "$LIBS_SYSTEME" -eq 1 ] && [ -n "$GEST" ]; then
        ui_progres 34 "$(tl T_ETAPE_LIBS_SYSTEME "Installing the system libraries...")"
        #  Comment demander les droits, et dans quel ordre.
        #
        #  L'ordre suit le contexte, non la preference : sur un bureau,
        #  pkexec, kdesu ou gksu ouvrent une FENETRE d'authentification, ce
        #  qui est la seule chose correcte quand l'installateur a lui-meme
        #  ete lance depuis un bureau - un `sudo` y attendrait un mot de
        #  passe sur un terminal que personne ne regarde, et l'installation
        #  paraitrait figee. En mode texte, c'est l'inverse : `sudo` parle au
        #  terminal qu'on a sous les yeux.
        #
        #  pkexec d'abord parmi les graphiques : il est le mecanisme de
        #  polkit, present sur toutes les distributions modernes, alors que
        #  gksu est abandonne depuis des annees et kdesu propre a KDE.
        ELEVATEUR=""
        if [ "$(id -u)" = "0" ]; then
            ELEVATEUR="direct"
        elif [ "$INTERFACE" = "texte" ] && command -v sudo >/dev/null 2>&1; then
            ELEVATEUR="sudo"
        else
            for outil in pkexec kdesu gksu sudo; do
                if command -v "$outil" >/dev/null 2>&1; then
                    #  pkexec et gksu n'ont de sens qu'avec un serveur
                    #  d'affichage : sans lui, ils echouent sans rien dire.
                    case "$outil" in
                        pkexec|kdesu|gksu)
                            [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ] || continue ;;
                    esac
                    ELEVATEUR="$outil"; break
                fi
            done
        fi

        case "$ELEVATEUR" in
            direct)
                # shellcheck disable=SC2086
                $INSTALLE $PAQUETS || souci "$(tl T_INSTALLATION_INCOMPLETE "installation incomplete")" ;;
            pkexec)
                dire "      pkexec $INSTALLE ... ($(tl T_MOT_DE_PASSE "a window will ask for your password"))"
                # shellcheck disable=SC2086
                pkexec $INSTALLE $PAQUETS || souci "$(tl T_INSTALLATION_REFUSEE "installation incomplete or declined")" ;;
            kdesu)
                dire "      kdesu $INSTALLE ..."
                # shellcheck disable=SC2086
                kdesu -c "$INSTALLE $PAQUETS" || souci "$(tl T_INSTALLATION_REFUSEE "installation incomplete or declined")" ;;
            gksu)
                dire "      gksu $INSTALLE ..."
                # shellcheck disable=SC2086
                gksu "$INSTALLE $PAQUETS" || souci "$(tl T_INSTALLATION_REFUSEE "installation incomplete or declined")" ;;
            sudo)
                dire "      sudo $INSTALLE ..."
                # shellcheck disable=SC2086
                sudo $INSTALLE $PAQUETS || souci "$(tl T_INSTALLATION_INCOMPLETE "installation incomplete")" ;;
            *)
                souci "$(tl T_DROITS_IMPOSSIBLES "no way to obtain privileges (neither root, pkexec, kdesu, gksu nor sudo)")"
                dire ""
                dire "      $(tl T_LIBS_A_TAPER_VOUS "To be typed yourself, as administrator:")"
                dire "          $INSTALLE $PAQUETS"
                dire "" ;;
        esac
    elif [ -n "$GEST" ]; then
        dire ""
        dire "      $(tl T_LIBS_EXPLICATION "These libraries cannot be installed in the home folder: libGL must match the graphics driver.")"
        dire "      $(tl T_LIBS_A_TAPER "To be typed once, as administrator:")"
        dire ""
        dire "          sudo $INSTALLE $PAQUETS"
        dire ""
        dire "      $(tl T_LIBS_OU_RELANCER "Or run this installer again with:")"
        dire "          --with-system-dependencies"
        dire ""
    fi
fi

VENV="$PREFIXE/venv"
if [ ! -x "$VENV/bin/python" ]; then
    ui_progres 40 "$(tl T_ETAPE_ENV "Creating the Python environment...")"
    if ! "$PY" -m venv "$VENV" 2>/dev/null; then
        ui_progres_fin
        ui_erreur "$(tl T_INSTALLATION "Installation")" \
            "$(tl T_ENV_IMPOSSIBLE "Cannot create the environment: the “venv” module is missing.")\n\n$(tl T_PY_AIDE_DISTRIBUTIONS "Install it with your package manager:")\n\nDebian, Ubuntu, Mint :\n    sudo apt install python3-venv"
        exit 1
    fi
fi

ui_progres 55 "$(tl T_ETAPE_LIBS "Installing the libraries (this may take a minute)...")"
if [ -d "$PREFIXE/roues" ] && [ -n "$(ls -A "$PREFIXE/roues" 2>/dev/null)" ]; then
    "$VENV/bin/pip" install --quiet --no-index --find-links "$PREFIXE/roues" \
        -r "$PREFIXE/requirements.txt" 2>/dev/null \
    || "$VENV/bin/pip" install --quiet -r "$PREFIXE/requirements.txt" \
    || { ui_progres_fin
         ui_erreur "$(tl T_INSTALLATION "Installation")" \
                   "$(tl T_LIBS_IMPOSSIBLE "Cannot install the libraries.")"
         exit 1; }
else
    "$VENV/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1 || true
    "$VENV/bin/pip" install --quiet -r "$PREFIXE/requirements.txt" \
    || { ui_progres_fin
         ui_erreur "$(tl T_INSTALLATION "Installation")" \
                   "$(tl T_INSTALLATION_IMPOSSIBLE "Cannot install.")\n$(tl T_VERIFIEZ_RESEAU "Check your connection.")"
         exit 1; }
fi
ui_progres 85 "$(tl T_ETAPE_LIBS_FAC "Optional libraries (MIDI, speech)...")"
"$VENV/bin/pip" install --quiet -r "$PREFIXE/requirements-optionnel.txt" \
    >/dev/null 2>&1 || true

#  Cache de bytecode. Sans lui, Python recompile a chaque demarrage tous les
#  modules dont le dossier n'est pas inscriptible - et l'attente se voit au
#  premier lancement. On le construit maintenant, une fois, pendant qu'on a
#  encore les droits d'ecriture.
#
#  « -q » pour ne pas deverser des milliers de lignes, « || true » parce
#  qu'un module illisible ne doit pas faire echouer une installation reussie.
ui_progres 92 "${T_ETAPE_BYTECODE:-Cache de bytecode (demarrages plus rapides)...}"
"$VENV/bin/python" -m compileall -q "$PREFIXE/phytoscope" >/dev/null 2>&1 || true
"$VENV/bin/python" -m compileall -q "$PREFIXE/run.py" >/dev/null 2>&1 || true
"$VENV/bin/python" -m compileall -q "$VENV/lib" >/dev/null 2>&1 || true

# -- la langue choisie devient celle de PhytoScope --------------------------
#  Le logiciel lit « ui.language » dans reglages.json a chaque demarrage. On
#  l'y ecrit donc une fois, plutot que de laisser refaire dans le logiciel le
#  choix qu'on vient de faire ici.
#
#  Par l'outil du logiciel, et non par du sed : lui sait FUSIONNER - une
#  reinstallation par-dessus une installation existante ne doit changer que
#  la langue - et il ecrit de facon atomique. Les trois installateurs
#  l'appellent, ce qui evite trois versions de la meme prudence.
if [ -n "$LANGUE" ] && [ -x "$VENV/bin/python" ] \
   && [ -f "$PREFIXE/write_language.py" ]; then
    if "$VENV/bin/python" "$PREFIXE/write_language.py" "$LANGUE" >/dev/null 2>&1; then
        REGLAGES="${XDG_CONFIG_HOME:-$HOME/.config}/phytoscope/reglages.json"
        bien "$(tl T_LANGUE_ENREGISTREE "Language recorded in {file}" \
                   file "$REGLAGES")"
    else
        souci "$(tl T_LANGUE_NON_ENREGISTREE "settings not written: the language can be chosen in the software")"
    fi
fi

# -- 3. lanceur, menu, icone ------------------------------------------------
ui_progres 92 "$(tl T_ETAPE_LANCEUR "Launcher and menu entry...")"
mkdir -p "$BINAIRE" "$BUREAU" "$ICONES"
cat > "$BINAIRE/phytoscope" <<LANCEUR
#!/bin/sh
#  Lanceur de PhytoScope - ecrit par l'installateur.
exec "$VENV/bin/python" "$PREFIXE/run.py" "\$@"
LANCEUR
chmod +x "$BINAIRE/phytoscope"

[ -f "$PREFIXE/phytoscope.svg" ] && cp "$PREFIXE/phytoscope.svg" "$ICONES/phytoscope.svg"
cat > "$BUREAU/phytoscope.desktop" <<BUREAUFIN
[Desktop Entry]
Type=Application
Version=1.0
Name=PhytoScope
GenericName=Plant signal monitor
Comment=Measure, listen to and record a plant's electrical signals
Exec=$BINAIRE/phytoscope %f
TryExec=$BINAIRE/phytoscope
Icon=phytoscope
Terminal=false
Categories=Science;Education;AudioVideo;Audio;
Keywords=plante;plant;biosignal;sonification;oscilloscope;MIDI;
StartupNotify=true
StartupWMClass=phytoscope
BUREAUFIN

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

if [ "$ICONE_BUREAU" = "oui" ]; then
    DOSSIER_BUREAU="$(trouver_le_bureau)"
    if [ -n "$DOSSIER_BUREAU" ]; then
        cp "$BUREAU/phytoscope.desktop" "$DOSSIER_BUREAU/phytoscope.desktop"
        chmod +x "$DOSSIER_BUREAU/phytoscope.desktop"
        #  GNOME exige en plus cet attribut, sans quoi il affiche
        #  « Lancement d'application non fiable » au lieu de l'icone.
        command -v gio >/dev/null 2>&1 && \
            gio set "$DOSSIER_BUREAU/phytoscope.desktop" metadata::trusted true \
                2>/dev/null || true
    fi
fi

# -- 4. desinstallateur et registre ----------------------------------------
ui_progres 96 "$(tl T_ETAPE_DESINSTALLATEUR "Uninstaller...")"
cat > "$PREFIXE/uninstall.sh" <<DESINSTALL
#!/bin/sh
# ===========================================================================
#  Retire PhytoScope $VERSION.
#
#  NE TOUCHE PAS a vos reglages ni a vos seances : une desinstallation n'est
#  pas une demande d'oubli. Ils restent dans
#      ~/.config/phytoscope           reglages et journal
#      ~/.local/share/phytoscope      seances enregistrees
#
#      ./uninstall.sh        avec confirmation
#      ./uninstall.sh -y     sans question
# ===========================================================================
set -e
SANS_QUESTION=0
[ "\${1:-}" = "-y" ] && SANS_QUESTION=1

echo ""
echo "  $(tl T_RETRAIT_DE "PhytoScope {version} will be removed from:" version "$VERSION")"
echo "      $PREFIXE"
echo "      $BINAIRE/phytoscope"
echo "      $BUREAU/phytoscope.desktop"
echo ""
if [ "\$SANS_QUESTION" -eq 0 ]; then
    printf '  %s %s ' "$(tl T_CONTINUER "Continue?")" "${T_INVITE_NON_DEFAUT:-[y/N]}"
    read -r r
    _oui=non
    for _l in ${T_LETTRES_OUI:-yY}; do
        case "\$r" in [\$_l]*) _oui=oui ;; esac
    done
    [ "\$_oui" = oui ] || { echo "  $(tl T_ANNULE "Cancelled.")"; exit 0; }
fi

rm -f "$BINAIRE/phytoscope" "$BUREAU/phytoscope.desktop" "$ICONES/phytoscope.svg"
for d in "\$(command -v xdg-user-dir >/dev/null 2>&1 && xdg-user-dir DESKTOP || true)" \\
         "\$HOME/Bureau" "\$HOME/Desktop" "\$HOME/Escritorio"; do
    [ -n "\$d" ] && rm -f "\$d/phytoscope.desktop" 2>/dev/null || true
done
rm -f "$REGISTRE"
rm -rf "$PREFIXE"

echo ""
echo "  $(tl T_RETIRE "PhytoScope has been removed.")"
echo ""
echo "  $(tl T_DONNEES_CONSERVEES "YOUR DATA IS KEPT:")"
echo "      ~/.config/phytoscope           $(tl T_DONNEES_REGLAGES "settings and log")"
echo "      ~/.local/share/phytoscope      $(tl T_DONNEES_SEANCES "recorded sessions")"
echo ""
echo "  $(tl T_POUR_EFFACER_AUSSI "To erase them as well:")"
echo "      rm -rf ~/.config/phytoscope ~/.local/share/phytoscope"
echo ""
DESINSTALL
chmod +x "$PREFIXE/uninstall.sh"

#  Le registre : c'est lui que « --uninstall » relit, plutot que de deviner.
mkdir -p "$(dirname "$REGISTRE")"
cat > "$REGISTRE" <<REGISTREFIN
#  Ecrit par l'installateur de PhytoScope $VERSION - ne pas modifier a la main.
PREFIXE_INSTALLE="$PREFIXE"
BINAIRE_INSTALLE="$BINAIRE"
VERSION_INSTALLEE="$VERSION-$RELEASE"
DATE_INSTALLATION="$(date -Iseconds 2>/dev/null || date)"
REGISTREFIN

ui_progres 100 "$(tl T_TERMINE "Done.")"
ui_progres_fin

# -- 5. voila ---------------------------------------------------------------
RESUME="$(tl T_TERMINE_MESSAGE "PhytoScope {version} is installed." version "$VERSION")

$(colonne "$(tl T_LANCER "Launch")" 18) :  phytoscope
$(colonne "$(tl T_OU_PAR_LE_MENU "Or from the menu")" 18) :  Science -> PhytoScope
$(colonne "$(tl T_DIAGNOSTIC "Diagnostics")" 18) :  phytoscope --check
$(colonne "$(tl T_DESINSTALLER "Uninstall")" 18) :  $MOI --uninstall

$(tl T_DEMARRE_SANS_MATERIEL "The software starts with NO hardware: an internal generator takes over.")
$(tl T_MANUEL_ET_AIDE "The manual is in manual.txt; online help is on F1.")"

dire ""
bien "$(tl T_TERMINE_MESSAGE "PhytoScope {version} is installed." version "$VERSION")"
dire ""
#  Padded at RUN time, not written out with spaces: the labels are different
#  lengths in every language, and a column that lines up in English does not
#  line up in Italian. `%-18s` is not perfect for scripts whose glyphs are
#  double-width, but it is right for every Latin and Cyrillic language and it
#  degrades gracefully for the others.
dire "  $(colonne "$(tl T_LANCER "Launch")" 18) :  phytoscope"
dire "  $(colonne "$(tl T_OU_PAR_LE_MENU "Or from the menu")" 18) :  Science -> PhytoScope"
dire "  $(colonne "$(tl T_DIAGNOSTIC "Diagnostics")" 18) :  phytoscope --check"
dire "  $(colonne "$(tl T_DESINSTALLER "Uninstall")" 18) :  $MOI --uninstall"
dire ""
case ":$PATH:" in
    *":$BINAIRE:"*) ;;
    *) souci "$(tl T_PATH_ABSENT "{directory} is not in your PATH." directory "$BINAIRE")"
       dire "      $(tl T_PATH_AJOUTEZ "Add to ~/.profile:")  export PATH=\"\$PATH:$BINAIRE\"" ;;
esac

#  Lancer maintenant ? Seulement s'il y a un serveur graphique : demarrer une
#  interface Qt sans ecran produirait une erreur incomprehensible juste apres
#  une installation reussie.
if [ -z "$LANCER" ]; then
    if [ "$SANS_QUESTION" -eq 1 ]; then
        LANCER="non"
    elif [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
        LANCER="non"
        souci "$(tl T_PAS_DE_SERVEUR_GRAPHIQUE "no display server: run “phytoscope” from a desktop session")"
    else
        LANCER="$(ui_question "$(tl T_TERMINE_TITRE "Installation finished")" \
            "$RESUME

$(tl T_LANCER_MAINTENANT "Start PhytoScope now?")" "oui")"
    fi
elif [ "$INTERFACE" != "texte" ] && [ "$SANS_QUESTION" -eq 0 ]; then
    ui_info "$(tl T_TERMINE_TITRE "Installation finished")" "$RESUME"
fi

if [ "$LANCER" = "oui" ]; then
    dire ""
    etape "$(tl T_DEMARRAGE "starting...")"
    setsid "$BINAIRE/phytoscope" >/dev/null 2>&1 &
    sleep 1
fi
dire ""
exit 0
