#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/verify_translation.py
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

"""Prove that translating prose did not change any code.

Why this tool exists
--------------------

Translating this repository touches roughly 290,000 words spread over some
250 files, and most of that prose sits *inside* source files as comments and
docstrings. Editing a comment cannot break anything; editing the line above
it by accident can break everything, and a reviewer reading a 700-line diff
in a second language will not notice.

So we do not rely on reading. Before the first translation commit we record,
for every tracked Python file, two fingerprints:

  · the **code shape** — the abstract syntax tree with every docstring
    removed and every string literal replaced by a placeholder. Comments are
    absent from the tree to begin with, so translating a comment or a
    docstring cannot change this fingerprint. Anything else does.

  · the **literals** — the same tree with string contents kept. User-facing
    text lives here, so this fingerprint is *expected* to change when the
    interface strings are re-keyed to English, and it must change on purpose,
    file by file, never by accident.

Afterwards, `--compare` replays the two fingerprints. A file whose code shape
moved is reported as an error, whatever its diff looks like.

Renamed files
-------------

File names are being translated too, so a path is not a stable key. Pass a
rename map (`--renames`, a JSON object of `{"old/path.py": "new/path.py"}`)
and the comparison follows the file to its new name. A file that is missing
and unaccounted for is reported rather than skipped: silence is how a lost
file stops being noticed.

Usage
-----

    python3 tools/verify_translation.py --baseline .ai/translation-baseline.json
    python3 tools/verify_translation.py --compare  .ai/translation-baseline.json \
                                        --renames .ai/translation-renames.json
    python3 tools/verify_translation.py --remaining

`--remaining` needs no baseline: it reports how much French is left, per
area, and is the progress meter for the whole effort.

Exit status is 1 when a code shape moved, when a file went missing, or when
a baseline is requested over an existing one without `--force`.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#  Placeholder substituted for every string literal when computing the code
#  shape. Its own value is irrelevant; it only has to be constant.
PLACEHOLDER = "\x00literal\x00"

#  Areas reported separately by --remaining, in the order they are worked on.
AREAS = (
    ("governance", ("AGENTS.md", "CLAUDE.md", "constraints.md")),
    ("tooling", ("tools/",)),
    ("software", ("src/phytoscope/phytoscope/",)),
    ("software tools", ("src/phytoscope/tools/",)),
    ("tests", ("src/phytoscope/tests/",)),
    ("firmware", ("src/firmware/",)),
    ("sdk", ("src/sdk/",)),
    ("packaging", ("packaging/",)),
    ("publications", ("pdf-src/",)),
    ("hardware", ("hardware/",)),
    ("working notes", (".ai/",)),
    ("workflows", (".github/",)),
    ("top-level docs", ("README.md", "INSTALL.md", "PACKAGING.md",
                        "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md",
                        "CODE_OF_CONDUCT.md")),
)

#  Words that occur in French prose and essentially never in English
#  technical writing. Accented characters alone are not enough: proper nouns
#  such as « Bretagne Namasté » stay as they are, and so do quoted French
#  titles in the bibliographies.
FRENCH_WORDS = re.compile(
    r"\b(?:le|la|les|un|une|des|du|de|et|ou|mais|donc|car|ni|que|qui|quoi"
    r"|dont|où|ce|cet|cette|ces|son|sa|ses|leur|leurs|nos|notre|votre|vos"
    r"|est|sont|était|étaient|sera|seront|a|ont|avait|avaient|fait|faire"
    r"|peut|peuvent|doit|doivent|faut|il|elle|ils|elles|on|nous|vous|je"
    r"|pas|plus|moins|très|bien|alors|ainsi|aussi|encore|déjà|jamais"
    r"|toujours|sans|sous|sur|avec|dans|pour|par|vers|chez|entre|depuis"
    r"|pendant|avant|après|quand|comme|si|non|oui|tout|tous|toute|toutes"
    r"|même|autre|autres|chaque|aucun|aucune|quelque|quelques|celui|celle"
    r"|ceux|celles|lorsque|puisque|parce|afin|lequel|laquelle)\b",
    re.IGNORECASE)


# ---------------------------------------------------------------- fingerprints
class _StripDocstrings(ast.NodeTransformer):
    """Remove docstrings; they are prose and may be translated freely."""

    def _strip(self, node):
        self.generic_visit(node)
        corps = node.body
        if (corps and isinstance(corps[0], ast.Expr)
                and isinstance(corps[0].value, ast.Constant)
                and isinstance(corps[0].value.value, str)):
            node.body = corps[1:] or [ast.Pass()]
        return node

    visit_Module = _strip
    visit_FunctionDef = _strip
    visit_AsyncFunctionDef = _strip
    visit_ClassDef = _strip


class _BlankStrings(ast.NodeTransformer):
    """Replace every string literal by a placeholder."""

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            return ast.copy_location(ast.Constant(value=PLACEHOLDER), node)
        return node


def _digest(tree) -> str:
    return hashlib.sha256(
        ast.dump(tree, include_attributes=False).encode("utf-8")
    ).hexdigest()[:16]


def fingerprints(source: str) -> tuple[str, str]:
    """(code shape, literals) for one Python source text."""
    tree = ast.parse(source)
    without_docs = _StripDocstrings().visit(ast.parse(source))
    ast.fix_missing_locations(without_docs)
    literals = _digest(without_docs)
    shape = _digest(_BlankStrings().visit(without_docs))
    del tree
    return shape, literals


def python_files() -> list[str]:
    issue = subprocess.run(["git", "ls-files", "*.py"], cwd=ROOT,
                           capture_output=True, text=True, check=True)
    return sorted(issue.stdout.split())


# --------------------------------------------------------------------- actions
def write_baseline(path: str, force: bool) -> int:
    if os.path.exists(path) and not force:
        print(f"  ! {path} already exists.")
        print("    A baseline records the state *before* translation; "
              "overwriting it")
        print("    silently would destroy the only reference we have. "
              "Pass --force")
        print("    if that is really what you want.")
        return 1

    recorded, unparsable = {}, []
    for relative in python_files():
        absolute = os.path.join(ROOT, relative)
        try:
            with open(absolute, encoding="utf-8") as f:
                shape, literals = fingerprints(f.read())
        except SyntaxError as error:
            unparsable.append(f"{relative}: {error}")
            continue
        recorded[relative] = {"shape": shape, "literals": literals}

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"files": recorded}, f, indent=2, sort_keys=True)
        f.write("\n")

    print(f"  · {len(recorded)} file(s) fingerprinted -> {path}")
    if unparsable:
        print(f"  ! {len(unparsable)} file(s) could not be parsed:")
        for quoi in unparsable:
            print(f"      {quoi}")
        return 1
    return 0


def compare(path: str, renames_path: str | None) -> int:
    with open(path, encoding="utf-8") as f:
        recorded = json.load(f)["files"]

    renames = {}
    if renames_path and os.path.exists(renames_path):
        with open(renames_path, encoding="utf-8") as f:
            renames = json.load(f)

    present = set(python_files())
    moved_code, changed_text, missing = [], [], []

    for old, reference in sorted(recorded.items()):
        new = renames.get(old, old)
        if new not in present:
            missing.append(f"{old}" + (f" -> {new} (absent)" if new != old
                                       else " (absent)"))
            continue
        with open(os.path.join(ROOT, new), encoding="utf-8") as f:
            shape, literals = fingerprints(f.read())
        if shape != reference["shape"]:
            moved_code.append(f"{new}" + (f"  (was {old})" if new != old
                                          else ""))
        elif literals != reference["literals"]:
            changed_text.append(f"{new}" + (f"  (was {old})" if new != old
                                            else ""))

    added = sorted(present - {renames.get(o, o) for o in recorded})

    print(f"  · {len(recorded)} file(s) compared against the baseline")
    if added:
        print(f"  · {len(added)} file(s) created since:")
        for quoi in added:
            print(f"      {quoi}")
    if changed_text:
        print(f"  · {len(changed_text)} file(s) whose string literals moved "
              f"— expected while re-keying the interface, to be reviewed:")
        for quoi in changed_text:
            print(f"      {quoi}")
    if missing:
        print(f"  ! {len(missing)} file(s) missing and unaccounted for:")
        for quoi in missing:
            print(f"      {quoi}")
        print("    Add them to the rename map, or explain the deletion.")
    if moved_code:
        print(f"  ! {len(moved_code)} file(s) whose CODE SHAPE changed:")
        for quoi in moved_code:
            print(f"      {quoi}")
        print("    Translating a comment or a docstring cannot do that.")
        print("    Something else was edited — review these before pushing.")

    if moved_code or missing:
        return 1
    print("  ✓ no code shape moved")
    return 0


def _french_score(text: str) -> int:
    return len(FRENCH_WORDS.findall(text))


def remaining() -> int:
    issue = subprocess.run(["git", "ls-files"], cwd=ROOT,
                           capture_output=True, text=True, check=True)
    tracked = issue.stdout.split()
    readable = (".py", ".sh", ".md", ".html", ".css", ".txt", ".yml", ".yaml",
                ".c", ".h", ".json", ".cmake", ".spec", ".nsi", ".ino")

    per_area: dict[str, tuple[int, int]] = {}
    for label, prefixes in AREAS:
        words = files = 0
        for relative in tracked:
            if not relative.startswith(prefixes):
                continue
            if not relative.endswith(readable) and "Makefile" not in relative:
                continue
            try:
                with open(os.path.join(ROOT, relative),
                          encoding="utf-8") as f:
                    score = _french_score(f.read())
            except (OSError, UnicodeDecodeError):
                continue
            if score:
                words += score
                files += 1
        per_area[label] = (files, words)

    total_files = sum(f for f, _ in per_area.values())
    total_words = sum(w for _, w in per_area.values())
    print("  French still present, by area")
    print("  " + "-" * 52)
    for label, _ in AREAS:
        files, words = per_area[label]
        if files:
            print(f"    {label:20s} {files:5d} file(s)  {words:8d} marker(s)")
    print("  " + "-" * 52)
    print(f"    {'total':20s} {total_files:5d} file(s)  "
          f"{total_words:8d} marker(s)")
    print()
    print("  A marker is a French function word (le, une, qui, sans, ...).")
    print("  It counts occurrences, not words to translate, and it is meant")
    print("  to be watched going down — not to reach zero: proper nouns and")
    print("  quoted French titles stay.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prove that translating prose did not change any code.")
    parser.add_argument("--baseline", metavar="FILE",
                        help="record the fingerprints of every Python file")
    parser.add_argument("--compare", metavar="FILE",
                        help="compare the working tree against a baseline")
    parser.add_argument("--renames", metavar="FILE",
                        help="JSON map {old path: new path} for renamed files")
    parser.add_argument("--remaining", action="store_true",
                        help="report how much French is left, per area")
    parser.add_argument("--force", action="store_true",
                        help="allow overwriting an existing baseline")
    args = parser.parse_args(argv)

    if args.baseline:
        return write_baseline(args.baseline, args.force)
    if args.compare:
        return compare(args.compare, args.renames)
    if args.remaining:
        return remaining()
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
