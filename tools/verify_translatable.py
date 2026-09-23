#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/verify_translatable.py
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

"""Find user-visible text that does not go through `t()`.

Why this exists
---------------

The software has eleven languages and a user who picks one, at install time
or afterwards. That promise holds only for text that passes through `t()`.
A label written directly into a Qt call —

    bouton.setText("Calculer maintenant")          # wrong
    bouton.setText(t("Calculer maintenant"))       # right

— stays in the source language whatever the user chose. Nothing fails, no
test goes red, and the interface is simply half-translated for everyone who
did not pick French. That is the defect this tool looks for.

`phytoscope/i18n.py` already collects every `t("…")` call by parsing the
source, which answers "what must be translated". This tool answers the
opposite and more useful question: **what reaches the screen without being
translatable at all?**

How it decides
--------------

By parsing, never by regular expression: a call spread over three lines, or a
string concatenated from two literals, defeats a regex and is common in
layout code.

For every call, the callee name is matched against `SINKS` — the Qt setters
and constructors whose argument is displayed. A string literal in one of
those positions is a leak unless it is wrapped: `t("…")`, an f-string built
from `t(…)`, or `t("…").format(…)`.

What is not a leak
------------------

  · anything too short or with no letter in it: `" "`, `":"`, `"—"`, `"%"`,
    `"·"`. These are separators and units, and translating them would be
    noise;
  · stylesheets and object names. `setStyleSheet` and `setObjectName` are not
    displayed, and they are not in `SINKS`;
  · a unit suffix already handled as data, such as `" Hz"` — declared in
    `ALLOWED` with its reason, one line each. An allowlist entry is a claim
    that the string is *not* user-visible prose, and it is reviewed like any
    other line of code.

Usage
-----

    python3 tools/verify_translatable.py            # the whole interface
    python3 tools/verify_translatable.py --verbose  # list what was accepted

Exit status is 1 if a leak is found, and the report names the file, the line
and the string, so the fix is mechanical.
"""
from __future__ import annotations

import argparse
import ast
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOFTWARE = os.path.join(ROOT, "src", "phytoscope")

#  Qt calls whose string argument reaches the screen. Setters first, then the
#  constructors that take their label directly.
SINKS = {
    #  setters
    "setText", "setWindowTitle", "setToolTip", "setStatusTip",
    "setPlaceholderText", "setTitle", "setLabelText", "setSuffix",
    "setPrefix", "setTabText", "setItemText", "setHeaderLabels",
    "setHorizontalHeaderLabels", "setVerticalHeaderLabels", "setWhatsThis",
    "setInformativeText", "setDetailedText",
    #  things that append a visible entry
    "addItem", "addTab", "addAction", "addButton", "insertItem",
    #  the message boxes — see BOITES below: these five names are shared
    #  with the logger, and a receiver check tells them apart.
    "information", "warning", "critical", "question", "about",
    #  constructors
    "QLabel", "QPushButton", "QCheckBox", "QRadioButton", "QGroupBox",
    "QAction", "QToolButton", "QMenu", "QLineEdit", "QTextEdit",
    "QPlainTextEdit", "QCommandLinkButton",
}

#  Which argument actually carries the label. Checking them all was wrong:
#  `addItem(t("automatique"), "auto")` passes the visible text first and a
#  hidden user-data string second, and the tool reported the second one. The
#  default is argument 0; these are the exceptions.
POSITIONS = {
    "addTab": (1,),            # addTab(widget, label)
    "insertItem": (1,),        # insertItem(index, text, userData)
    "addItem": (0,),           # addItem(text, userData)
    "information": (1, 2),     # (parent, title, text)
    "warning": (1, 2),
    "critical": (1, 2),
    "question": (1, 2),
    "about": (1, 2),
    "setLabelText": (0,),
    "addButton": (0,),
}


#  Five of the names above belong to `QMessageBox` *and* to `logging.Logger`.
#  The first version treated them all as user-visible and reported thirty-one
#  log lines as leaks — `log.warning("Capture de trames démarrée : %s")` among
#  them. That is the wrong verdict, and the distinction is the one the owner
#  drew on 2026-09-22: what is not exposed to end users is written in English,
#  and **the log is not exposed**. It is a diagnostic artifact, attached to bug
#  reports; translating it would make those reports unreadable to whoever
#  receives them. So the log stays English and is not a catalog entry.
#
#  A call to one of those five names counts as user-visible only when the
#  receiver names a dialog.
BOITES = ("QMessageBox", "QInputDialog", "QFileDialog", "QErrorMessage")
NOMS_PARTAGES = {"information", "warning", "critical", "question", "about"}


def _receiver(node: ast.Call) -> str:
    """The textual receiver of a method call, or "" for a plain function."""
    fonction = node.func
    if not isinstance(fonction, ast.Attribute):
        return ""
    cible = fonction.value
    morceaux = []
    while isinstance(cible, ast.Attribute):
        morceaux.append(cible.attr)
        cible = cible.value
    if isinstance(cible, ast.Name):
        morceaux.append(cible.id)
    elif isinstance(cible, ast.Call):
        nom = getattr(cible.func, "id", None) or \
            getattr(cible.func, "attr", None)
        morceaux.append(str(nom or ""))
    return ".".join(reversed(morceaux))


#  Strings accepted in a sink position, each with the reason. An entry here
#  says "this is not prose": a unit, a symbol, a technical token. Anything
#  else belongs in a catalog.
ALLOWED = {
    " Hz": "unit, appended to a number",
    " s": "unit",
    " ms": "unit",
    " µV": "unit",
    " dB": "unit",
    " %": "unit",
    "PhytoScope": "the product name, never translated",
    "PhytoSense": "the board name, never translated",
    "MIDI": "protocol name",
    "CSV": "format name",
    "WAV": "format name",
    "OK": "kept as is in every language of the catalog",
}

VERT = "\033[0;32m"
ROUGE = "\033[0;31m"
JAUNE = "\033[0;33m"
GRIS = "\033[0;90m"
NEUTRE = "\033[0m"


def is_prose(texte: str) -> bool:
    """Is this string something a reader would read?

    One letter is not enough — `"x"` is an axis name. Two adjacent letters
    are the cheapest test that separates `"Mode"` from `":"`, `"·"` and
    `"{:.1f}"`, and it has no false negative worth the complication.
    """
    if texte in ALLOWED:
        return False
    lettres = [c for c in texte if c.isalpha()]
    if len(lettres) < 2:
        return False
    #  A format-only string carries no prose of its own.
    sans_champs = texte
    for ouvrant in ("{", "<"):
        if texte.strip().startswith(ouvrant):
            sans_champs = ""
    return bool(sans_champs.strip())


def contient_t(node: ast.AST) -> bool:
    """Is there a literal `t(...)` call anywhere in this expression?

    Stricter than `wrapped()`, and used for f-strings. `wrapped()` answers
    "might this be translated somewhere I cannot see", and for a bare name it
    answers yes — which is right for `setText(self._titre)` and wrong for
    `f"{exc}\n\nDétails dans le journal."`, where the prose is in the
    literal part and the name carries an exception. The first version let
    exactly that line through.
    """
    for sous in ast.walk(node):
        if isinstance(sous, ast.Call):
            nom = getattr(sous.func, "id", None) or \
                getattr(sous.func, "attr", None)
            if nom == "t":
                return True
    return False


def wrapped(node: ast.AST) -> bool:
    """Does this argument go through `t()`, in any of the accepted shapes?"""
    #  t("…")
    if isinstance(node, ast.Call):
        nom = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if nom == "t":
            return True
        #  t("…").format(…)  /  "…".format(t(…))
        if nom == "format":
            return wrapped(node.func.value) if hasattr(node.func, "value") \
                else False
        #  Any other call: look inside its arguments. `str(t("…"))` and
        #  `"".join(t(x) for x in …)` are both legitimate.
        return any(wrapped(a) for a in node.args)
    #  f"{t('…')} …"
    if isinstance(node, ast.JoinedStr):
        return any(wrapped(v.value) for v in node.values
                   if isinstance(v, ast.FormattedValue))
    #  t("a") + " " + t("b")
    if isinstance(node, ast.BinOp):
        return wrapped(node.left) or wrapped(node.right)
    #  A name or an attribute: already computed elsewhere, out of reach here.
    return not isinstance(node, ast.Constant)


class _Hunter(ast.NodeVisitor):
    def __init__(self, relative: str) -> None:
        self.relative = relative
        self.leaks: list[tuple[int, str, str]] = []

    def visit_Call(self, node: ast.Call) -> None:
        nom = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        interessant = nom in SINKS
        if nom in NOMS_PARTAGES:
            #  A logger, or a dialog? The receiver decides.
            interessant = any(b in _receiver(node) for b in BOITES)
        if interessant:
            positions = POSITIONS.get(nom, (0,))
            for indice in positions:
                if indice >= len(node.args):
                    continue
                argument = node.args[indice]
                if isinstance(argument, ast.Constant) and \
                        isinstance(argument.value, str) and \
                        is_prose(argument.value):
                    self.leaks.append((argument.lineno, nom, argument.value))
                #  An f-string: its literal parts are prose too, and the
                #  first version walked straight past them —
                #  `f"{exc}\n\nDétails dans le journal."` went unreported.
                elif isinstance(argument, ast.JoinedStr) and \
                        not contient_t(argument):
                    litteral = "".join(
                        v.value for v in argument.values
                        if isinstance(v, ast.Constant)
                        and isinstance(v.value, str))
                    if is_prose(litteral):
                        self.leaks.append(
                            (argument.lineno, nom, litteral.strip()))
                #  A list of labels: setHeaderLabels(["A", "B"]).
                elif isinstance(argument, (ast.List, ast.Tuple)):
                    for element in argument.elts:
                        if isinstance(element, ast.Constant) and \
                                isinstance(element.value, str) and \
                                is_prose(element.value):
                            self.leaks.append(
                                (element.lineno, nom, element.value))
        self.generic_visit(node)


def interface_files() -> list[str]:
    issue = subprocess.run(
        ["git", "ls-files", "src/phytoscope/phytoscope"],
        cwd=ROOT, capture_output=True, text=True, check=True)
    return [f for f in issue.stdout.split() if f.endswith(".py")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Find user-visible text that bypasses t().")
    parser.add_argument("--verbose", action="store_true",
                        help="also list the files that were checked")
    args = parser.parse_args(argv)

    total = 0
    par_fichier: dict[str, list[tuple[int, str, str]]] = {}
    for relative in interface_files():
        chemin = os.path.join(ROOT, relative)
        try:
            with open(chemin, encoding="utf-8") as f:
                arbre = ast.parse(f.read(), relative)
        except (OSError, SyntaxError) as erreur:
            print(f"{ROUGE}  ! {relative}: {erreur}{NEUTRE}")
            return 1
        total += 1
        chasseur = _Hunter(relative)
        chasseur.visit(arbre)
        if chasseur.leaks:
            par_fichier[relative] = chasseur.leaks
        elif args.verbose:
            print(f"{GRIS}  · {relative}{NEUTRE}")

    fuites = sum(len(v) for v in par_fichier.values())
    print()
    if not fuites:
        print(f"{VERT}  ✓ {total} file(s) checked, no user-visible text "
              f"bypasses t(){NEUTRE}")
        print(f"{GRIS}    Every label reaching the screen can follow the "
              f"language the user picked.{NEUTRE}")
        print()
        return 0

    print(f"{ROUGE}  ✗ {fuites} string(s) reach the screen without t(), "
          f"in {len(par_fichier)} file(s){NEUTRE}")
    print(f"{GRIS}    These stay in the source language whatever the user "
          f"chose.{NEUTRE}")
    print()
    for relative in sorted(par_fichier):
        print(f"  {relative}")
        for ligne, sink, texte in sorted(par_fichier[relative]):
            court = texte if len(texte) <= 58 else texte[:55] + "…"
            print(f"{JAUNE}      {ligne:5d}  {sink}({court!r}){NEUTRE}")
    print()
    print(f"{GRIS}    Wrap each one: {sink}(t(\"…\")). If a string is not "
          f"prose —{NEUTRE}")
    print(f"{GRIS}    a unit, a symbol, a product name — add it to ALLOWED "
          f"with its reason.{NEUTRE}")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(main())
