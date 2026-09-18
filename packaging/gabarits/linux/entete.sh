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

verifier || { ui_erreur "Installation" "L'archive est abimee.\nRetelechargez le fichier."; exit 1; }

#  La licence, avant tout engagement. En mode graphique et en mode tui, la
#  case a cocher est la : c'est ce qu'on attend d'un installateur.
if [ "$SANS_QUESTION" -eq 0 ] && [ "$INTERFACE" != "texte" ]; then
    BAC_LICENCE="$(mktemp -d)"
    extraire_un "LICENCE.txt" "$BAC_LICENCE"
    if [ "$(ui_licence "$BAC_LICENCE/LICENCE.txt")" != "accepte" ]; then
        rm -rf "$BAC_LICENCE"
        dire "  Licence refusee - installation annulee."
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
if [ -z "$PY" ]; then
    ui_erreur "Installation" "Python 3.9 (avec le module « venv ») est introuvable.\n\nDebian, Ubuntu, Mint :\n    sudo apt install python3 python3-venv\n\nFedora, Red Hat :\n    sudo dnf install python3\n\nArch :\n    sudo pacman -S python"
    exit 1
fi
bien "Python : $PY"

# -- 2. la copie, sous une barre de progression ----------------------------
ui_progres_debut
ui_progres 10 "Decompression du logiciel..."

if [ -d "$PREFIXE" ]; then
    rm -rf "$PREFIXE/phytoscope" "$PREFIXE/run.py" "$PREFIXE/roues"
fi
mkdir -p "$PREFIXE"
extraire "$PREFIXE"
ui_progres 30 "Logiciel installe."

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
