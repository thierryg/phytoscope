#  ==========================================================================
#  PhytoScope — attribution — packaging/templates/common/labels.sh
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
#  PhytoScope — label lookup for the scripts an end user runs
#
#  Three scripts outlive the installation and still talk to the user: the
#  launcher on the PATH, the one that puts an icon on the desktop, and the
#  macOS wrapper. They must speak the language the user picked, exactly as
#  the software does, and they must say so without needing Python — the
#  launcher's whole reason for printing anything is that Python is missing.
#
#  Sourced, not executed. It defines `tl` and nothing else runs.
#
#  Where the language comes from, in order:
#
#    1. $PHYTOSCOPE_LANGUAGE, so a script can be tested in any language
#       without touching the user's settings;
#    2. `ui.language` in the settings file the software itself reads, which
#       is where the installer wrote the answer to its first question;
#    3. English, the source language, whose text is compiled into the call
#       sites as the fallback argument.
#
#  Deliberately no locale detection (C-31): the language is a choice the user
#  made, not a guess from the environment.
# ===========================================================================

#  A newline in a variable, for composing a multi-line AppleScript without a
#  here-document: `osascript -e` takes the script as one argument.
_NL='
'

#  Read one string value out of a flat-ish JSON object without a JSON parser.
#  This is not a general reader and does not pretend to be: it finds
#  "<key>" : "<value>" anywhere in the file and returns the value. The file it
#  reads is written by the software itself, one key per line, so the shape is
#  known. Anything unexpected yields nothing, and the caller falls back.
_valeur_json() {
    #  $1 = file, $2 = key
    [ -f "$1" ] || return 1
    sed -n 's/.*"'"$2"'"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$1" \
        2>/dev/null | head -n 1
}

#  The settings file for this platform, which is where the installer put the
#  language and where the software reads it at every start.
_fichier_des_reglages() {
    case "$(uname -s 2>/dev/null)" in
        Darwin) echo "$HOME/Library/Application Support/PhytoScope/reglages.json" ;;
        *)      echo "${XDG_CONFIG_HOME:-$HOME/.config}/phytoscope/reglages.json" ;;
    esac
}

#  $1 = the directory holding the generated `<code>.sh` catalogues.
#  Sets T_* in the current shell. Silent, and harmless, when there is no
#  catalogue to load: every call site carries its English default.
charger_libelles() {
    _dossier="$1"
    _code="${PHYTOSCOPE_LANGUAGE:-}"
    if [ -z "$_code" ]; then
        _code="$(_valeur_json "$(_fichier_des_reglages)" language)"
    fi
    [ -n "$_code" ] || _code="en"
    T_LANGUE_CODE="$_code"
    if [ -f "$_dossier/$_code.sh" ]; then
        # shellcheck disable=SC1090
        . "$_dossier/$_code.sh"
        return 0
    fi
    return 1
}

#  Resolve a label BY NAME, fall back if the catalogue is missing, then
#  substitute its {fields}.
#
#  Why this exists rather than "${T_NAME:-default}". A default value that
#  contains a brace closes the parameter expansion early, and one that
#  contains an apostrophe opens a single-quoted string that swallows the rest
#  of the file. Neither is reported by `dash -n`, and `bash -n` blames a
#  perfectly sound line dozens of lines further down. Taking the label name as
#  a plain word keeps the default out of the expansion entirely.
#
#      tl T_INSTALLED_IN "Installed in {directory}" directory "$PREFIX"
tl() {
    _nom="$1"; shift
    _defaut="$1"; shift
    eval "_valeur=\${$_nom}"
    [ -n "$_valeur" ] || _valeur="$_defaut"
    while [ "$#" -ge 2 ]; do
        _valeur="$(printf '%s' "$_valeur" | sed "s|{$1}|$2|g")"
        shift 2
    done
    printf '%s' "$_valeur"
}

#  --------------------------------------------------------------------------
#  macOS: asking for the language, and recording the answer
#
#  A .pkg installs without asking anything — that is what one expects of it —
#  so the question is put by the post-install script, in the installing user's
#  session, and the answer is written where the software will read it. The
#  launcher then has nothing to ask.
#
#  The list of languages is built from the generated `index.sh`, never written
#  out here: one list, in packaging/languages/installateur.json, and every
#  screen follows it. Adding a language must not mean editing a shell script.
#  --------------------------------------------------------------------------

#  $1 = the directory holding the catalogues (it must contain index.sh).
#  $2 = optional: a uid to ask in another user's session, for a script that
#       runs as root during a .pkg install.
#  Echoes the chosen code, or nothing when the user cancelled or there is no
#  way to ask.
demander_la_langue() {
    _dossier="$1"
    _uid="${2:-}"
    [ -f "$_dossier/index.sh" ] || return 1
    #  The absolute path is what a macOS script should use. The override
    #  exists so that this function can be exercised on a machine that has no
    #  osascript at all, which is where it gets written.
    _osascript="${PHYTOSCOPE_OSASCRIPT:-/usr/bin/osascript}"
    command -v "$_osascript" >/dev/null 2>&1 || return 1
    # shellcheck disable=SC1091
    . "$_dossier/index.sh"

    #  AppleScript wants {"a", "b", "c"}; the names come from the catalogue.
    _liste=""
    _premier=""
    for _c in $LANGUES_CODES; do
        eval "_nom=\$LANGUE_NOM_$_c"
        [ -n "$_premier" ] || _premier="$_nom"
        if [ -z "$_liste" ]
        then _liste="\"$_nom\""
        else _liste="$_liste, \"$_nom\""
        fi
    done

    #  The prompt is asked BEFORE a language is known, so it is asked in the
    #  source language. Its title is the product name, which needs none.
    _script="set retenue to choose from list {$_liste} with title \"PhytoScope\""
    _script="$_script with prompt \"Choose your language - it will be used by PhytoScope.\""
    _script="$_script default items {\"$_premier\"} without multiple selections allowed"
    _script="$_script${_NL}if retenue is false then${_NL}return \"\"${_NL}else"
    _script="$_script${_NL}return item 1 of retenue${_NL}end if"

    if [ -n "$_uid" ]; then
        _choix="$(launchctl asuser "$_uid" "$_osascript" -e "$_script" 2>/dev/null)"
    else
        _choix="$("$_osascript" -e "$_script" 2>/dev/null)"
    fi
    [ -n "$_choix" ] || return 1

    #  Back from the display name to the code. A reverse lookup, so that the
    #  catalogue stays the only place a name is written.
    for _c in $LANGUES_CODES; do
        eval "_nom=\$LANGUE_NOM_$_c"
        if [ "$_choix" = "$_nom" ]; then
            printf '%s' "$_c"
            return 0
        fi
    done
    return 1
}

#  $1 = language code, $2 = the settings file to write.
#  Only ever called when the file does not exist yet, so a minimal document is
#  enough and nothing can be lost. When the file IS there, the software's own
#  tool must be used instead: it knows how to merge.
ecrire_la_langue() {
    [ -n "$1" ] || return 1
    [ -e "$2" ] && return 1
    mkdir -p "$(dirname "$2")" || return 1
    printf '{\n  "ui": {\n    "language": "%s"\n  }\n}\n' "$1" > "$2"
}
