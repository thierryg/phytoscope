#!/bin/sh
#  ==========================================================================
#  PhytoScope — attribution — packaging/gabarits/linux/entete.sh
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
PhytoScope - installateur autonome pour GNU/Linux

  ./PhytoScope-X.Y.Z-Linux.run [options]

Interface
  (aucune)          graphique s'il y a un bureau, sinon texte
  --gui             imposer l'interface graphique (zenity, kdialog)
  --tui             imposer les boites en mode texte (whiptail, dialog)
  --texte           imposer l'affichage en lignes, sans boites

Installation
  --prefix DOSSIER  installer ailleurs que dans le dossier par defaut
  --desktop         poser l'icone sur le Bureau, sans demander
  --no-desktop      ne pas la poser
  --launch          lancer le logiciel a la fin, sans demander
  --langue CODE     imposer la langue (fr en es pt it id ru zh ja ko ar)
                    sans quoi elle est demandee au tout debut
  --avec-dependances-systeme
                    installer aussi les bibliotheques systeme manquantes
                    (libGL, libxcb, portaudio...). EXIGE des privileges :
                    l'installateur appellera votre gestionnaire de paquets.
                    Sans cette option il se contente de les nommer.
  --no-launch       ne pas le lancer
  -y, --yes         ne rien demander (installation sans surveillance)

Autres
  --uninstall       desinstaller PhytoScope
  --check           verifier l'integrite de l'archive, sans installer
  --extract DOSSIER decompresser sans installer
  --version         afficher la version
  -h, --help        cette aide

Sans privileges : lance par un compte ordinaire, l'installateur se pose dans
~/.local/opt/phytoscope et n'appelle jamais sudo. Lance par root, il installe
dans /opt/phytoscope pour toute la machine.
AIDE
    exit 0
}

charge() {
    tail -n +$((LIGNES_ENTETE + 1)) "$MOI"
}

verifier() {
    if ! command -v sha256sum >/dev/null 2>&1; then
        souci "sha256sum absent : impossible de verifier"
        return 0
    fi
    calculee="$(charge | sha256sum | cut -d' ' -f1)"
    if [ "$calculee" = "$EMPREINTE" ]; then
        bien "archive intacte"
        return 0
    fi
    echec "archive ABIMEE"
    dire "      attendue : $EMPREINTE"
    dire "      obtenue  : $calculee"
    dire "      Retelechargez le fichier."
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
        --extract)    EXTRAIRE="${2:?--extract demande un dossier}"; shift 2 ;;
        --prefix)     PREFIXE="${2:?--prefix demande un dossier}"; shift 2 ;;
        --langue|--lang)    LANGUE_IMPOSEE="${2:?--langue demande un code}"; shift 2 ;;
        --avec-dependances-systeme) LIBS_SYSTEME=1; shift ;;
        --uninstall|--desinstaller) DESINSTALLER=1; shift ;;
        --gui|--graphique)  INTERFACE="graphique"; shift ;;
        --tui)              INTERFACE="tui"; shift ;;
        --texte|--text)     INTERFACE="texte"; shift ;;
        -y|--yes)     SANS_QUESTION=1; shift ;;
        --desktop)    ICONE_BUREAU="oui"; shift ;;
        --no-desktop) ICONE_BUREAU="non"; shift ;;
        --launch)     LANCER="oui"; shift ;;
        --no-launch)  LANCER="non"; shift ;;
        *)            echec "option inconnue : $1"; dire "  --help pour la liste."; exit 2 ;;
    esac
done

choisir_interface

if [ -n "$EXTRAIRE" ]; then
    extraire "$EXTRAIRE"
    bien "decompresse dans $EXTRAIRE"
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
        ui_erreur "Desinstallation" "PhytoScope ne semble pas installe.\n\nSi vous l'avez installe ailleurs :\n    $MOI --uninstall --prefix /le/dossier"
        exit 1
    fi
    if [ -x "$CIBLE/desinstaller.sh" ]; then
        if [ "$SANS_QUESTION" -eq 1 ]; then
            "$CIBLE/desinstaller.sh" -y
        else
            reponse="$(ui_question "Desinstallation" \
                "Retirer PhytoScope de\n    $CIBLE\n\nVos reglages et vos seances seront CONSERVES." "non")"
            [ "$reponse" = "oui" ] || { dire "  Annule."; exit 0; }
            "$CIBLE/desinstaller.sh" -y
            ui_info "Desinstallation" \
                "PhytoScope est retire.\n\nVos donnees sont conservees :\n    ~/.config/phytoscope\n    ~/.local/share/phytoscope"
        fi
    else
        echec "desinstallateur introuvable dans $CIBLE"
        exit 1
    fi
    exit 0
fi

# ----------------------------------------------------------- installation
dire ""
dire "  PhytoScope @TITRE_VERSION@"
dire "  @EDITEUR@ - @AUTEUR@"
dire "  @SITE@ - @COURRIEL@ - licence @LICENCE@"
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
extraire_un "langues" "$BAC_LANGUES" 2>/dev/null || true

charger_langue() {
    #  $1 = code. Charge le catalogue, ou ne fait rien s'il manque : les
    #  libellés gardent alors leur valeur de repli, en francais.
    if [ -f "$BAC_LANGUES/langues/$1.sh" ]; then
        # shellcheck disable=SC1090
        . "$BAC_LANGUES/langues/$1.sh"
        LANGUE="$1"
        return 0
    fi
    return 1
}

#  `t` remplit les champs nommes d'un libelle : t "$T_INSTALLATION_DANS" \
#  dossier "$PREFIXE". Un sed par champ, ce qui suffit pour des libelles qui
#  n'en portent jamais plus de deux.
t() {
    _texte="$1"; shift
    while [ "$#" -ge 2 ]; do
        _texte="$(printf '%s' "$_texte" | sed "s|{$1}|$(printf '%s' "$2" | sed 's|[&|\\]|\\&|g')|g")"
        shift 2
    done
    printf '%s' "$_texte"
}

if [ -f "$BAC_LANGUES/langues/index.sh" ]; then
    # shellcheck disable=SC1091
    . "$BAC_LANGUES/langues/index.sh"

    if [ -n "$LANGUE_IMPOSEE" ]; then
        charger_langue "$LANGUE_IMPOSEE" || charger_langue fr
    elif [ "$SANS_QUESTION" -eq 1 ]; then
        #  Installation sans surveillance : le francais, sauf --langue.
        charger_langue fr
    else
        charger_langue fr          # pour pouvoir poser la question
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
    bien "$(t "$T_LANGUE_RETENUE" langue "${_nom:-$LANGUE}")"
fi

verifier || { ui_erreur "${T_INSTALLATION:-Installation}" "${T_ARCHIVE_ABIMEE:-L'archive est abimee.}\n${T_RETELECHARGER:-Retelechargez le fichier.}"; exit 1; }

#  La licence, avant tout engagement. En mode graphique et en mode tui, la
#  case a cocher est la : c'est ce qu'on attend d'un installateur.
if [ "$SANS_QUESTION" -eq 0 ] && [ "$INTERFACE" != "texte" ]; then
    BAC_LICENCE="$(mktemp -d)"
    extraire_un "LICENCE.txt" "$BAC_LICENCE"
    if [ "$(ui_licence "$BAC_LICENCE/LICENCE.txt")" != "accepte" ]; then
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
        [ -n "$PREFIXE" ] || { dire "  Annule."; exit 0; }
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

dire "  Installation dans : $PREFIXE"
dire "  Lanceur           : $BINAIRE/phytoscope"
[ "$(id -u)" -ne 0 ] && dire "  ${GRIS}(compte ordinaire - aucun privilege demande)${NEUTRE}"
dire ""

if [ "$SANS_QUESTION" -eq 0 ] && [ "$INTERFACE" = "texte" ]; then
    [ "$(ui_question "Installation" "Continuer ?" "oui")" = "oui" ] || {
        dire "  Annule."; exit 0; }
    dire ""
fi

#  Les questions d'option AVANT la copie : on ne veut pas interrompre une
#  barre de progression pour poser une question.
if [ -z "$ICONE_BUREAU" ]; then
    if [ "$SANS_QUESTION" -eq 1 ]; then
        ICONE_BUREAU="non"
    else
        ICONE_BUREAU="$(ui_question "Options" \
            "Ajouter une icone PhytoScope sur le Bureau ?" "oui")"
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
    bien "Python : $PY (du systeme)"
else
    souci "aucun Python du systeme ne convient - on cherchera celui de l'archive"
fi

# -- 2. la copie, sous une barre de progression ----------------------------
ui_progres_debut
ui_progres 10 "Decompression du logiciel..."

if [ -d "$PREFIXE" ]; then
    rm -rf "$PREFIXE/phytoscope" "$PREFIXE/run.py" "$PREFIXE/roues" \
           "$PREFIXE/python"
fi
mkdir -p "$PREFIXE"
extraire "$PREFIXE"
ui_progres 30 "Logiciel installe."

#  L'archive transporte un CPython RELOGEABLE (python-build-standalone) :
#  il fonctionne depuis n'importe quel dossier, sans etre installe, sans
#  privileges et sans toucher au systeme - ce que le projet exige (C-55).
#  C'est ce qui rend cet installateur utilisable sur une machine nue.
if [ -z "$PY" ] && [ -x "$PREFIXE/python/bin/python3" ]; then
    PY="$PREFIXE/python/bin/python3"
    PY_EMBARQUE="oui"
    bien "Python : $PY (embarque)"
elif [ -n "$PY" ] && [ -d "$PREFIXE/python" ]; then
    #  Le systeme en a un qui convient : on n'emporte pas le double.
    rm -rf "$PREFIXE/python"
fi

if [ -z "$PY" ]; then
    ui_progres_fin
    ui_erreur "Installation" "Python 3.9 (avec le module « venv ») est introuvable, et cet installateur n'en transporte pas.\n\nDebian, Ubuntu, Mint :\n    sudo apt install python3 python3-venv\n\nFedora, Red Hat :\n    sudo dnf install python3\n\nArch :\n    sudo pacman -S python"
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

    souci "bibliotheques du systeme manquantes :$manquantes"

    if [ "$LIBS_SYSTEME" -eq 1 ] && [ -n "$GEST" ]; then
        ui_progres 34 "Installation des bibliotheques du systeme..."
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
                $INSTALLE $PAQUETS || souci "installation incomplete" ;;
            pkexec)
                dire "      pkexec $INSTALLE ... (une fenetre va demander votre mot de passe)"
                # shellcheck disable=SC2086
                pkexec $INSTALLE $PAQUETS || souci "installation incomplete ou refusee" ;;
            kdesu)
                dire "      kdesu $INSTALLE ..."
                # shellcheck disable=SC2086
                kdesu -c "$INSTALLE $PAQUETS" || souci "installation incomplete ou refusee" ;;
            gksu)
                dire "      gksu $INSTALLE ..."
                # shellcheck disable=SC2086
                gksu "$INSTALLE $PAQUETS" || souci "installation incomplete ou refusee" ;;
            sudo)
                dire "      sudo $INSTALLE ..."
                # shellcheck disable=SC2086
                sudo $INSTALLE $PAQUETS || souci "installation incomplete" ;;
            *)
                souci "aucun moyen d'obtenir les droits (ni root, ni pkexec, ni kdesu, ni gksu, ni sudo)"
                dire ""
                dire "      A taper vous-meme, en administrateur :"
                dire "          $INSTALLE $PAQUETS"
                dire "" ;;
        esac
    elif [ -n "$GEST" ]; then
        dire ""
        dire "      Ces bibliotheques ne s'installent pas dans le dossier"
        dire "      personnel : libGL doit correspondre au pilote graphique."
        dire "      A taper une fois, en tant qu'administrateur :"
        dire ""
        dire "          sudo $INSTALLE $PAQUETS"
        dire ""
        dire "      Ou relancez cet installateur avec :"
        dire "          --avec-dependances-systeme"
        dire ""
    fi
fi

VENV="$PREFIXE/venv"
if [ ! -x "$VENV/bin/python" ]; then
    ui_progres 40 "Creation de l'environnement Python..."
    if ! "$PY" -m venv "$VENV" 2>/dev/null; then
        ui_progres_fin
        ui_erreur "Installation" "Creation de l'environnement impossible : le module « venv » manque.\n\nDebian, Ubuntu, Mint :\n    sudo apt install python3-venv"
        exit 1
    fi
fi

ui_progres 55 "Installation des bibliotheques (cela peut prendre une minute)..."
if [ -d "$PREFIXE/roues" ] && [ -n "$(ls -A "$PREFIXE/roues" 2>/dev/null)" ]; then
    "$VENV/bin/pip" install --quiet --no-index --find-links "$PREFIXE/roues" \
        -r "$PREFIXE/requirements.txt" 2>/dev/null \
    || "$VENV/bin/pip" install --quiet -r "$PREFIXE/requirements.txt" \
    || { ui_progres_fin; ui_erreur "Installation" "Installation des bibliotheques impossible."; exit 1; }
else
    "$VENV/bin/pip" install --quiet --upgrade pip >/dev/null 2>&1 || true
    "$VENV/bin/pip" install --quiet -r "$PREFIXE/requirements.txt" \
    || { ui_progres_fin; ui_erreur "Installation" "Installation impossible.\nVerifiez votre connexion."; exit 1; }
fi
ui_progres 85 "Bibliotheques facultatives (MIDI, parole)..."
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
   && [ -f "$PREFIXE/ecrire_langue.py" ]; then
    if "$VENV/bin/python" "$PREFIXE/ecrire_langue.py" "$LANGUE" >/dev/null 2>&1; then
        REGLAGES="${XDG_CONFIG_HOME:-$HOME/.config}/phytoscope/reglages.json"
        bien "$(t "${T_LANGUE_ENREGISTREE:-Langue enregistree dans {fichier}}" \
                 fichier "$REGLAGES")"
    else
        souci "reglages non ecrits : la langue se choisira dans le logiciel"
    fi
fi

# -- 3. lanceur, menu, icone ------------------------------------------------
ui_progres 92 "Lanceur et entree de menu..."
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
GenericName=Ecoute des signaux vegetaux
Comment=Mesurer, ecouter et enregistrer les signaux electriques d'une plante
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
ui_progres 96 "Desinstallateur..."
cat > "$PREFIXE/desinstaller.sh" <<DESINSTALL
#!/bin/sh
# ===========================================================================
#  Retire PhytoScope $VERSION.
#
#  NE TOUCHE PAS a vos reglages ni a vos seances : une desinstallation n'est
#  pas une demande d'oubli. Ils restent dans
#      ~/.config/phytoscope           reglages et journal
#      ~/.local/share/phytoscope      seances enregistrees
#
#      ./desinstaller.sh        avec confirmation
#      ./desinstaller.sh -y     sans question
# ===========================================================================
set -e
SANS_QUESTION=0
[ "\${1:-}" = "-y" ] && SANS_QUESTION=1

echo ""
echo "  PhytoScope $VERSION sera retire de :"
echo "      $PREFIXE"
echo "      $BINAIRE/phytoscope"
echo "      $BUREAU/phytoscope.desktop"
echo ""
if [ "\$SANS_QUESTION" -eq 0 ]; then
    printf '  Continuer ? [o/N] '
    read -r r
    case "\$r" in [oO]*) ;; *) echo "  Annule."; exit 0 ;; esac
fi

rm -f "$BINAIRE/phytoscope" "$BUREAU/phytoscope.desktop" "$ICONES/phytoscope.svg"
for d in "\$(command -v xdg-user-dir >/dev/null 2>&1 && xdg-user-dir DESKTOP || true)" \\
         "\$HOME/Bureau" "\$HOME/Desktop" "\$HOME/Escritorio"; do
    [ -n "\$d" ] && rm -f "\$d/phytoscope.desktop" 2>/dev/null || true
done
rm -f "$REGISTRE"
rm -rf "$PREFIXE"

echo ""
echo "  PhytoScope est retire."
echo ""
echo "  VOS DONNEES SONT CONSERVEES :"
echo "      ~/.config/phytoscope           reglages et journal"
echo "      ~/.local/share/phytoscope      seances enregistrees"
echo ""
echo "  Pour les effacer aussi :"
echo "      rm -rf ~/.config/phytoscope ~/.local/share/phytoscope"
echo ""
DESINSTALL
chmod +x "$PREFIXE/desinstaller.sh"

#  Le registre : c'est lui que « --uninstall » relit, plutot que de deviner.
mkdir -p "$(dirname "$REGISTRE")"
cat > "$REGISTRE" <<REGISTREFIN
#  Ecrit par l'installateur de PhytoScope $VERSION - ne pas modifier a la main.
PREFIXE_INSTALLE="$PREFIXE"
BINAIRE_INSTALLE="$BINAIRE"
VERSION_INSTALLEE="$VERSION-$RELEASE"
DATE_INSTALLATION="$(date -Iseconds 2>/dev/null || date)"
REGISTREFIN

ui_progres 100 "Termine."
ui_progres_fin

# -- 5. voila ---------------------------------------------------------------
RESUME="PhytoScope $VERSION est installe.

Lancer       :  phytoscope
Ou par le menu  :  Science -> PhytoScope
Diagnostic   :  phytoscope --check
Desinstaller :  $MOI --uninstall

Le logiciel demarre SANS materiel : un generateur interne prend le relais.
Le manuel est dans manuel.txt ; l'aide en ligne, touche F1."

dire ""
bien "PhytoScope $VERSION est installe."
dire ""
dire "  Lancer           :  phytoscope"
dire "  Ou par le menu   :  Science -> PhytoScope"
dire "  Diagnostic       :  phytoscope --check"
dire "  Desinstaller     :  $MOI --uninstall"
dire ""
case ":$PATH:" in
    *":$BINAIRE:"*) ;;
    *) souci "$BINAIRE n'est pas dans votre PATH."
       dire "      Ajoutez a ~/.profile :  export PATH=\"\$PATH:$BINAIRE\"" ;;
esac

#  Lancer maintenant ? Seulement s'il y a un serveur graphique : demarrer une
#  interface Qt sans ecran produirait une erreur incomprehensible juste apres
#  une installation reussie.
if [ -z "$LANCER" ]; then
    if [ "$SANS_QUESTION" -eq 1 ]; then
        LANCER="non"
    elif [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; then
        LANCER="non"
        souci "aucun serveur graphique : lancez « phytoscope » depuis une session de bureau"
    else
        LANCER="$(ui_question "Installation terminee" \
            "$RESUME

Lancer PhytoScope maintenant ?" "oui")"
    fi
elif [ "$INTERFACE" != "texte" ] && [ "$SANS_QUESTION" -eq 0 ]; then
    ui_info "Installation terminee" "$RESUME"
fi

if [ "$LANCER" = "oui" ]; then
    dire ""
    etape "demarrage..."
    setsid "$BINAIRE/phytoscope" >/dev/null 2>&1 &
    sleep 1
fi
dire ""
exit 0
