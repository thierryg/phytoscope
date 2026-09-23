#!/usr/bin/env python3
#  ==========================================================================
#  PhytoScope — attribution — tools/verify_installer_i18n.py
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

"""Audit the localisation of the installer scripts.

The graphical application routes every user-visible string through ``t()`` and
a JSON catalogue; ``tools/verify_translatable.py`` guards that. The installer
scripts are shell, so they need a guard of their own. This is it.

Four things are checked:

1. **Leaks.** A literal handed to an output function without passing through a
   label. Such a string reaches the user in English whatever language was
   picked, which defeats the point of asking.

2. **Expansions that do not parse.** ``${T_NAME:-default}`` is the obvious way
   to write a label with a fallback, and it is a trap: a default value that
   contains a brace closes the expansion early, and one that contains an
   apostrophe opens a single-quoted string that swallows the rest of the file.
   Neither is caught by ``dash -n``; ``bash -n`` reports them dozens of lines
   further down, on whichever later line first contains a parenthesis. Use
   ``tl NAME "default" [field value ...]`` instead, which takes the label name
   as a plain word.

3. **Missing labels.** A script that resolves ``T_FOO`` when the catalogue has
   no ``FOO`` silently falls back to its default for every language.

4. **Field disagreement.** ``{directory}`` in one language and ``{dossier}`` in
   another means the substitution quietly does nothing in the second. Every
   translation of a label must carry exactly the fields its default carries,
   and the call site must pass exactly those.

Exit status is 0 when nothing is reported, 1 otherwise, so the CI can gate on
it.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GABARITS = os.path.join(RACINE, "packaging", "templates")
CATALOGUE = os.path.join(RACINE, "packaging", "languages", "installateur.json")

#  Every shell function that puts text in front of the user. `dire` and the
#  four severity helpers print to the terminal; the `ui_*` family routes to
#  zenity, kdialog or the terminal depending on what the machine has. The
#  maintainer scripts have no helpers of their own and call `echo` directly.
SORTIES = (
    "echo",
    "printf",
    "dire",
    "bien",
    "souci",
    "echec",
    "etape",
    "ui_erreur",
    "ui_info",
    "ui_question",
    "ui_progres",
    "ui_progres_debut",
    "ui_licence",
    "ui_dossier",
    "ui_langue",
)

#  Scripts whose output goes to a package manager's log rather than to a
#  person choosing something. `apt` and `dnf` install without interaction, so
#  there is no language to have asked for, and whoever reads the log ran the
#  command as an administrator. These stay in technical English, by the same
#  rule that keeps the build scripts in English. The scripts an end user runs
#  — the launcher, the desktop icon, the uninstall wrapper — are not on this
#  list and must go through the catalogue.
ADMINISTRATEUR = frozenset({"postinst", "prerm", "postrm", "preinst"})

#  A segment made only of these is not prose: it is punctuation, a path, a
#  version number or a shell placeholder, and translating it would be wrong.
#  A literal is checked segment by segment, because the messages that offer a
#  command to copy are a run of shell lines joined by ``\n`` and none of them
#  should be handed to a translator.
PAS_DE_LA_PROSE = re.compile(
    r"""^(?:
          \s*                              # blank
        | [-=*_.:/|+#$\s]+                 # rules, separators, a lone $
        | \$\{?[A-Za-z_][\w:.\-/]*\}?      # a bare expansion
        | \$\([^)]*\)                      # a bare command substitution
        | (?:%[-\d.*]*[bsdifxo]|\s)+       # a printf format and nothing else
        | [\d.]+                           # a number or a version
        | [A-Za-z0-9_.~-]*/[A-Za-z0-9_./~-]*  # a path: it carries a slash
        | [A-Za-z0-9_.~-]+(?<!\.)         # one word or flag, with no full
                                           # stop: "Cancelled." is a sentence
        )$""",
    re.VERBOSE,
)

#  `tl NAME "default" field "value" ...`, allowing a backslash continuation
#  between the arguments.
APPEL_TL = re.compile(
    r'\btl\s+T_([A-Z][A-Z0-9_]*)\s+"((?:[^"\\]|\\.)*)"'
    r'((?:\s*\\?\s*[a-z_]+\s+"(?:[^"\\]|\\.)*")*)'
)
#  Both `${T_NAME:-default}` and the bare `$T_NAME`; only the braced form
#  can carry a default, and only that form can be written dangerously.
EXPANSION_T = re.compile(
    r"\$\{(T_[A-Z][A-Z0-9_]*)(?::-((?:[^}]|\\})*))?\}"
    r"|\$(T_[A-Z][A-Z0-9_]*)()"
)
CHAMP = re.compile(r"\{(\w+)\}")


#  A placeholder the build substitutes, or a shell variable: what it stands
#  for is a version number, a URL or an e-mail address, never prose.
SUBSTITUE = re.compile(r"@[A-Z_]+@|\$\{?[A-Za-z_]\w*\}?|\$\([^)]*\)")

#  The first word of a command the user is invited to copy and run. Naming
#  them is more honest than guessing from shape: "Debian, Ubuntu, Mint:" and
#  "sudo apt install python3" are both a handful of words and a colon, and
#  only the first one is a sentence.
COMMANDES = frozenset(
    """
    sudo su pkexec kdesu gksu doas
    apt apt-get dnf yum pacman zypper apk emerge brew port
    python python3 pip pip3 sh bash dash zsh make cmake
    rm mkdir cp mv ln chmod chown tar unzip curl wget
    export echo printf cat systemctl launchctl defaults open
    phytoscope xdg-mime xdg-desktop-menu update-desktop-database
    """.split()
)


def est_une_commande(segment: str) -> bool:
    """Does this line invite the user to run something, rather than read it?"""
    mots = segment.split()
    if not mots:
        return False
    tete = mots[0].lstrip("$./").split("/")[-1]
    if tete not in COMMANDES:
        return False
    #  A sentence can start with a verb that is also a command name, so refuse
    #  anything carrying sentence punctuation.
    return not any(c in segment for c in ",;?!\u2019'\u00ab\u00bb\u201c\u201d")


def est_de_la_prose(litteral: str) -> bool:
    """Is this literal addressed to a reader, rather than to a shell?

    A literal is prose when at least one of its lines still reads as a
    sentence once the placeholders are removed. Splitting first matters: the
    message that tells the user which command to run is a paragraph of prose
    followed by two indented shell lines, and only the paragraph is ours to
    translate.
    """
    for segment in re.split(r"\\n|\n", litteral):
        nu = SUBSTITUE.sub("", segment).strip()
        if PAS_DE_LA_PROSE.match(nu) or est_une_commande(nu):
            continue
        return True
    return False


def literaux_visibles(ligne: str) -> list[str]:
    """Return the double-quoted literals this line hands to an output function.

    Only the first argument matters for the severity helpers, but the ``ui_*``
    family takes a title and a body, so every literal on the line is returned
    and the caller decides. Lines whose command is not an output function
    yield nothing.
    """
    nu = ligne.lstrip()
    if nu.startswith("#"):
        return []
    #  `echo` and `printf` also serve to build files and feed pipes. Text that
    #  goes anywhere but a terminal is not addressed to the user. `>&2` is a
    #  terminal, so it stays in, and `||` and `&&` are control operators
    #  rather than pipes.
    hors_chaines = re.sub(r'"(?:[^"\\]|\\.)*"', '""', nu)
    if re.search(r"(?<!>)>(?!&2)|(?<!\|)\|(?!\|)", hors_chaines):
        return []
    #  The definition of a helper is its implementation, not a call site.
    if re.match(r"(?:" + "|".join(SORTIES) + r")\(\)", nu):
        return []
    #  The command may be preceded by `if`, `[`, a pipe or a `&&`; look for the
    #  output function as a word anywhere, but require it to start a command.
    #  A `$(...)` is a nested command with its own arguments. Its literals
    #  belong to that command, not to this one: `ui_licence "$BAC/LICENSE.txt"`
    #  inside a test is passing a path, not printing a message. Blank the
    #  substitutions, innermost first, before reading the literals.
    #  Innermost first, and any parenthesised group, not just `$(...)`: the
    #  macOS launcher calls python with a `-c` snippet whose own parentheses
    #  would otherwise keep the substitution from ever matching.
    plat = nu
    for _ in range(12):
        reduit = re.sub(r"\([^()]*\)", "", plat)
        if reduit == plat:
            break
        plat = reduit
    if not re.search(r"(?:^|[;&|({]|\$\()\s*(?:" + "|".join(SORTIES) + r")\s", " " + plat):
        return []
    return re.findall(r'"((?:[^"\\]|\\.)*)"', plat)


def charger_catalogue() -> dict[str, dict[str, str]]:
    with open(CATALOGUE, encoding="utf-8") as f:
        return json.load(f)["libelles"]


def fichiers() -> list[str]:
    trouves = []
    for dossier, _, noms in os.walk(GABARITS):
        for nom in sorted(noms):
            chemin = os.path.join(dossier, nom)
            try:
                with open(chemin, encoding="utf-8") as f:
                    debut = f.read(2048)
            except (OSError, UnicodeDecodeError):
                continue
            #  Shell only: the .desktop, .plist, .wxs and .nsi files carry
            #  their own localisation mechanisms.
            if nom.endswith(".sh") or debut.startswith("#!") and "sh" in debut[:40]:
                trouves.append(chemin)
    return trouves


def verifier(bavard: bool) -> int:
    libelles = charger_catalogue()
    langues = sorted({l for trads in libelles.values() for l in trads})
    soucis: list[str] = []
    fuites_par_fichier: dict[str, int] = {}

    for chemin in fichiers():
        court = os.path.relpath(chemin, RACINE)
        with open(chemin, encoding="utf-8") as f:
            texte = f.read()
        lignes = texte.split("\n")

        #  1. leaks
        fuites = 0
        for n, ligne in enumerate(
            [] if os.path.basename(chemin) in ADMINISTRATEUR else lignes, 1
        ):
            if "$T_" in ligne or "${T_" in ligne or re.search(r"\btl\s+T_", ligne):
                continue
            for litteral in literaux_visibles(ligne):
                if not est_de_la_prose(litteral):
                    continue
                fuites += 1
                if bavard:
                    soucis.append(f"{court}:{n}: not translatable: {litteral[:64]!r}")
        if fuites:
            fuites_par_fichier[court] = fuites

        #  2. expansions that do not parse
        for n, ligne in enumerate(lignes, 1):
            if ligne.lstrip().startswith("#"):
                continue
            for m in EXPANSION_T.finditer(ligne):
                if m.group(1) is None:
                    continue          # the bare form carries no default
                defaut = m.group(2) or ""
                if "'" in defaut:
                    soucis.append(
                        f"{court}:{n}: ${{{m.group(1)}:-...}} default contains an "
                        f"apostrophe, which bash reads as an open quote — use tl"
                    )
                if "{" in defaut:
                    soucis.append(
                        f"{court}:{n}: ${{{m.group(1)}:-...}} default contains a "
                        f"brace, which closes the expansion early — use tl"
                    )

        #  3 and 4. labels and their fields
        for m in APPEL_TL.finditer(texte):
            cle, defaut, suite = m.group(1), m.group(2), m.group(3)
            n = texte[: m.start()].count("\n") + 1
            #  A `tl` shown in a comment is documentation, not a call site:
            #  the example in the helper's own header would otherwise be
            #  reported as a label nobody translated.
            if lignes[n - 1].lstrip().startswith("#"):
                continue
            attendus = set(CHAMP.findall(defaut))
            passes = set(re.findall(r'(?:^|\s)([a-z_]+)\s+"', suite))
            if cle not in libelles:
                soucis.append(f"{court}:{n}: T_{cle} is not in the catalogue")
                continue
            if passes != attendus:
                soucis.append(
                    f"{court}:{n}: T_{cle} is passed {sorted(passes)} but its "
                    f"default declares {sorted(attendus)}"
                )
            for langue in langues:
                if langue not in libelles[cle]:
                    soucis.append(f"{court}:{n}: T_{cle} has no {langue} translation")
                    continue
                champs = set(CHAMP.findall(libelles[cle][langue]))
                if champs != attendus:
                    soucis.append(
                        f"{court}:{n}: T_{cle} [{langue}] carries {sorted(champs)} "
                        f"but the default declares {sorted(attendus)}"
                    )

    #  A label every language translates but no script reads is dead weight.
    lus = set()
    for chemin in fichiers():
        with open(chemin, encoding="utf-8") as f:
            texte = f.read()
        lus |= {m.group(1) for m in APPEL_TL.finditer(texte)}
        lus |= {(m.group(1) or m.group(3))[2:] for m in EXPANSION_T.finditer(texte)}
    inutilises = sorted(set(libelles) - lus)

    for s in soucis:
        print(f"  ✗ {s}")
    total_fuites = sum(fuites_par_fichier.values())
    if fuites_par_fichier:
        print(f"\n  {total_fuites} string(s) not routed through the catalogue:")
        for court, n in sorted(fuites_par_fichier.items(), key=lambda kv: -kv[1]):
            print(f"      {n:4d}  {court}")
    print(
        f"\n  {len(libelles)} labels x {len(langues)} languages, "
        f"{len(lus & set(libelles))} read by a script, {len(inutilises)} unused"
    )
    if inutilises and bavard:
        print(f"      unused: {', '.join(inutilises)}")
    if soucis or total_fuites:
        return 1
    print("  ✓ every user-visible string is translatable")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="list every leaking string and every unused label",
    )
    a = p.parse_args()
    return verifier(a.verbose)


if __name__ == "__main__":
    sys.exit(main())
