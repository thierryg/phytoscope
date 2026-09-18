#  ==========================================================================
#  PhytoScope — attribution — packaging/gabarits/linux/interface.sh
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
#  Couche d'affichage de l'installateur — trois interfaces, une seule API.
#
#  Le reste du script ne sait pas s'il parle a une fenetre ou a un terminal :
#  il appelle ui_question, ui_info, ui_progres... et cette couche traduit.
#  C'est ce qui permet d'ajouter une interface sans toucher a la logique
#  d'installation, et surtout de n'avoir qu'UNE version de cette logique.
#
#      graphique   zenity (GTK) ou kdialog (KDE) — comme un InstallShield
#      tui         whiptail ou dialog — des boites en mode texte (ncurses)
#      texte       des lignes, sans fioritures — pour un journal ou un script
#
#  Le choix est automatique : graphique s'il y a un serveur d'affichage et
#  l'outil qui va avec, sinon tui, sinon texte. --gui, --tui et --texte
#  l'imposent.
# ===========================================================================

INTERFACE=""          # graphique | tui | texte — vide = on choisit
OUTIL_GUI=""          # zenity | kdialog
OUTIL_TUI=""          # whiptail | dialog
TITRE="PhytoScope @VERSION@"

choisir_interface() {
    #  Un serveur d'affichage ET un outil : sans les deux, une fenetre ne
    #  s'ouvrirait pas, et l'installation paraitrait bloquee.
    if command -v zenity >/dev/null 2>&1; then OUTIL_GUI="zenity"
    elif command -v kdialog >/dev/null 2>&1; then OUTIL_GUI="kdialog"
    elif command -v yad >/dev/null 2>&1; then OUTIL_GUI="yad"
    fi
    if command -v whiptail >/dev/null 2>&1; then OUTIL_TUI="whiptail"
    elif command -v dialog >/dev/null 2>&1; then OUTIL_TUI="dialog"
    fi

    if [ -n "$INTERFACE" ]; then
        #  Impose : on verifie quand meme que c'est possible.
        case "$INTERFACE" in
            graphique)
                if [ -z "$OUTIL_GUI" ] || { [ -z "${DISPLAY:-}" ] && [ -z "${WAYLAND_DISPLAY:-}" ]; }; then
                    INTERFACE="texte"
                fi ;;
            tui) [ -z "$OUTIL_TUI" ] && INTERFACE="texte" ;;
        esac
        return
    fi

    if [ -n "$OUTIL_GUI" ] && { [ -n "${DISPLAY:-}" ] || [ -n "${WAYLAND_DISPLAY:-}" ]; }; then
        INTERFACE="graphique"
    elif [ -n "$OUTIL_TUI" ] && [ -t 0 ]; then
        INTERFACE="tui"
    else
        INTERFACE="texte"
    fi
}

# --- question fermee : rend « oui » ou « non » -----------------------------
ui_question() {
    titre="$1"; texte="$2"; defaut="${3:-oui}"
    case "$INTERFACE" in
        graphique)
            case "$OUTIL_GUI" in
                zenity)
                    if zenity --question --title="$TITRE" --text="$texte" \
                        --ok-label="Oui" --cancel-label="Non" \
                        --width=460 2>/dev/null; then echo "oui"; else echo "non"; fi ;;
                kdialog)
                    if kdialog --title "$TITRE" --yesno "$texte" 2>/dev/null
                    then echo "oui"; else echo "non"; fi ;;
                *)  if yad --question --title="$TITRE" --text="$texte" 2>/dev/null
                    then echo "oui"; else echo "non"; fi ;;
            esac ;;
        tui)
            if $OUTIL_TUI --title "$titre" --yesno "$texte" 14 72 3>&1 1>&2 2>&3
            then echo "oui"; else echo "non"; fi ;;
        *)
            #  En mode texte, la lettre par defaut est en majuscule.
            if [ "$defaut" = "oui" ]; then invite="[O/n]"; else invite="[o/N]"; fi
            printf "  %s %s " "$texte" "$invite" >&2
            read -r r </dev/tty 2>/dev/null || r=""
            case "${r:-$([ "$defaut" = "oui" ] && echo o || echo n)}" in
                [oOyY]*) echo "oui" ;; *) echo "non" ;;
            esac ;;
    esac
}

# --- message ---------------------------------------------------------------
ui_info() {
    titre="$1"; texte="$2"
    case "$INTERFACE" in
        graphique)
            case "$OUTIL_GUI" in
                zenity) zenity --info --title="$TITRE" --text="$texte" \
                            --width=480 2>/dev/null || true ;;
                kdialog) kdialog --title "$TITRE" --msgbox "$texte" 2>/dev/null || true ;;
                *) yad --info --title="$TITRE" --text="$texte" 2>/dev/null || true ;;
            esac ;;
        tui) $OUTIL_TUI --title "$titre" --msgbox "$texte" 18 74 2>/dev/null || true ;;
        *)  printf '%b\n' "$texte" ;;
    esac
}

ui_erreur() {
    titre="$1"; texte="$2"
    case "$INTERFACE" in
        graphique)
            case "$OUTIL_GUI" in
                zenity) zenity --error --title="$TITRE" --text="$texte" \
                            --width=480 2>/dev/null || true ;;
                kdialog) kdialog --title "$TITRE" --error "$texte" 2>/dev/null || true ;;
                *) yad --error --title="$TITRE" --text="$texte" 2>/dev/null || true ;;
            esac ;;
        tui) $OUTIL_TUI --title "$titre" --msgbox "$texte" 16 74 2>/dev/null || true ;;
        *)  printf '%b\n' "$texte" >&2 ;;
    esac
}

# --- licence : rend « accepte » ou « refuse » ------------------------------
ui_licence() {
    fichier="$1"
    [ -f "$fichier" ] || { echo "accepte"; return; }
    case "$INTERFACE" in
        graphique)
            case "$OUTIL_GUI" in
                zenity)
                    if zenity --text-info --title="$TITRE — licence" \
                        --filename="$fichier" --width=680 --height=480 \
                        --checkbox="J'ai lu et j'accepte la licence MIT" \
                        2>/dev/null; then echo "accepte"; else echo "refuse"; fi ;;
                kdialog)
                    kdialog --title "$TITRE — licence" --textbox "$fichier" \
                        680 480 2>/dev/null || true
                    if kdialog --title "$TITRE" --yesno \
                        "Acceptez-vous la licence MIT ?" 2>/dev/null
                    then echo "accepte"; else echo "refuse"; fi ;;
                *) echo "accepte" ;;
            esac ;;
        tui)
            $OUTIL_TUI --title "Licence MIT" --textbox "$fichier" 22 76 \
                2>/dev/null || true
            if $OUTIL_TUI --title "Licence" --yesno \
                "Acceptez-vous la licence MIT ?" 8 60 3>&1 1>&2 2>&3
            then echo "accepte"; else echo "refuse"; fi ;;
        *)
            #  En mode texte on n'impose pas la lecture de vingt lignes : la
            #  licence est dans le paquet, et MIT tient en une phrase.
            echo "accepte" ;;
    esac
}

# --- dossier de destination ------------------------------------------------
ui_dossier() {
    defaut="$1"
    case "$INTERFACE" in
        graphique)
            case "$OUTIL_GUI" in
                zenity) zenity --entry --title="$TITRE" \
                            --text="Installer dans :" --entry-text="$defaut" \
                            --width=560 2>/dev/null || echo "" ;;
                kdialog) kdialog --title "$TITRE" \
                            --inputbox "Installer dans :" "$defaut" 2>/dev/null \
                            || echo "" ;;
                *) echo "$defaut" ;;
            esac ;;
        tui)
            $OUTIL_TUI --title "Destination" --inputbox "Installer dans :" \
                10 70 "$defaut" 3>&1 1>&2 2>&3 || echo "" ;;
        *)  echo "$defaut" ;;
    esac
}

# --- barre de progression --------------------------------------------------
#  Le tube de progression est le meme pour zenity et pour whiptail : on leur
#  envoie un pourcentage par ligne, et du texte precede de « # ».
TUBE_PROGRES=""
ui_progres_debut() {
    case "$INTERFACE" in
        graphique|tui)
            TUBE_PROGRES="$(mktemp -u)"
            mkfifo "$TUBE_PROGRES" 2>/dev/null || { TUBE_PROGRES=""; return; }
            if [ "$INTERFACE" = "graphique" ] && [ "$OUTIL_GUI" = "zenity" ]; then
                zenity --progress --title="$TITRE" --text="Préparation…" \
                    --percentage=0 --auto-close --no-cancel --width=460 \
                    < "$TUBE_PROGRES" 2>/dev/null &
            elif [ "$INTERFACE" = "tui" ]; then
                $OUTIL_TUI --gauge "Installation…" 8 70 0 < "$TUBE_PROGRES" &
            else
                rm -f "$TUBE_PROGRES"; TUBE_PROGRES=""; return
            fi
            exec 9>"$TUBE_PROGRES"
            ;;
    esac
}

ui_progres() {
    pourcentage="$1"; texte="$2"
    if [ -n "$TUBE_PROGRES" ]; then
        printf '%s\n#%s\n' "$pourcentage" "$texte" >&9 2>/dev/null || true
    else
        etape "$texte"
    fi
}

ui_progres_fin() {
    if [ -n "$TUBE_PROGRES" ]; then
        printf '100\n' >&9 2>/dev/null || true
        exec 9>&-
        rm -f "$TUBE_PROGRES"
        TUBE_PROGRES=""
        wait 2>/dev/null || true
    fi
}
