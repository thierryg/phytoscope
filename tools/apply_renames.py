#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/apply_renames.py
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

"""Rename files and directories, and fix every reference to them.

Why this is a tool and not a `sed` one-liner
--------------------------------------------

Renaming `packaging/commun.py` to `packaging/common.py` is one `git mv`. What
takes care is everything that *named* it: `import commun` in nine sibling
scripts, `$(PY) commun.py` in the Makefile, `packaging/commun.py` in the CI
workflows, and the prose that mentions it in four documents. Miss one and the
build breaks; over-reach and prose gets mangled — `commun` is also an
ordinary French word, and a blind substitution turns « le socle commun » into
« le socle common ».

So substitution here is **syntactic, never lexical**. Three rules, and
nothing else:

  · **full paths.** `packaging/commun.py` -> `packaging/common.py`, anywhere
    in any tracked text file. A path is distinctive; this is safe.

  · **bare basenames.** `commun.py` -> `common.py`, likewise. Also
    distinctive, because of the extension.

  · **module stems**, and only inside Python files that actually import the
    module. `import commun`, `from commun import`, `from .commun import`, and
    then — in those files only — `commun.` attribute access. Prose is never
    touched, because prose does not write `commun.` with a dot.

What this tool deliberately does **not** do is substitute a bare quoted word.
The first version did, for both modules and directories, and it lasted one
stage: renaming `packaging/certificat.py` rewrote

    CERTIFICAT_PROJET = os.path.join(_RACINE, "certificat", ...)

in `signature.py`, where `"certificat"` is the **directory** — renamed in a
later stage, so the code now pointed at a path that did not exist. The test
suite caught it, which is the only reason it is worth recounting here.

A quoted bare word can be a directory, a settings key, a catalog entry, or a
piece of displayed text. There is no way to tell from the outside, and the
rule bought almost nothing: a module named as a string is rare. Those few
cases are edited by hand, deliberately, and the test suite is what proves it.

Reading the plan
----------------

`.ai/rename-plan.json` holds ordered stages, each a list of
`[old path, new path]`. Stages exist so that a mistake costs one stage and
not sixty-three renames: apply one, run the tests, commit, move on.

Every run writes the cumulative `{old path: new path}` map for every tracked
file to `.ai/translation-renames.json`, which is what
`tools/verify_translation.py --renames` needs to follow a file across a
rename instead of reporting it as lost.

Usage
-----

    python3 tools/apply_renames.py --stage stage-1-packaging-modules --dry-run
    python3 tools/apply_renames.py --stage stage-1-packaging-modules
    python3 tools/apply_renames.py --list

`--dry-run` is not optional in practice: run it, read what it says it will
touch, then run it for real. Nothing is written without `git` seeing it, so
`git diff` remains the last word.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, ".ai", "rename-plan.json")
MAP = os.path.join(ROOT, ".ai", "translation-renames.json")

#  Extensions we rewrite references in. Binary and generated files are left
#  alone; the generated ones are rebuilt from their sources anyway (C-45).
TEXT = (".py", ".sh", ".md", ".html", ".css", ".txt", ".yml", ".yaml",
        ".json", ".cfg", ".toml", ".spec", ".nsi", ".cmake", ".c", ".h",
        ".ino", ".in", ".desktop", ".control", ".gitignore", ".cmd")


#  Files left out of reference rewriting, and the only two that are.
#
#    · the baseline is keyed by the paths as they were BEFORE any rename.
#      Rewriting it would erase the very mapping it exists to anchor, and
#      tools/verify_translation.py would then compare each file against
#      itself and pass whatever happened;
#    · the rename map is this tool's own output.
#
#  The journal and the changelog are NOT excluded. They are historical
#  records, and the first version of this list kept them untouched so that a
#  past entry would keep the names of its day. The owner asked for the whole
#  repository, agent memory included: an entry that names a file now carries
#  the name that file has today, because that is the name a reader can act
#  on. The entry still says what happened, and when.
NEVER_REWRITTEN = (
    ".ai/translation-baseline.json",
    ".ai/translation-renames.json",
)


def tracked() -> list[str]:
    issue = subprocess.run(["git", "ls-files"], cwd=ROOT,
                           capture_output=True, text=True, check=True)
    return issue.stdout.split()


def is_text(relative: str) -> bool:
    base = os.path.basename(relative)
    return relative.endswith(TEXT) or base in ("Makefile", "control",
                                               "AUTHORS", "LICENSE",
                                               "VERSION", "AUTEURS",
                                               "CODEOWNERS")


def rules_for(old: str, new: str, a_directory: bool) -> list[tuple[str, str, str]]:
    """(label, pattern, replacement) for one rename."""
    rules = [("full path", re.escape(old), new)]

    old_base, new_base = os.path.basename(old), os.path.basename(new)
    if old_base != old and old_base != new_base:
        if not a_directory:
            rules.append(("basename", re.escape(old_base), new_base))

    if not a_directory and old.endswith(".py"):
        stem, new_stem = old_base[:-3], new_base[:-3]
        if stem != new_stem:
            rules.append(("import",
                          r"(?m)^(\s*(?:from|import)\s+\.*)" +
                          re.escape(stem) + r"\b",
                          r"\g<1>" + new_stem))
            rules.append(("attribute",
                          r"\b" + re.escape(stem) + r"(?=\.)", new_stem))
    return rules


def imports_the_module(text: str, stem: str) -> bool:
    return re.search(r"(?m)^\s*(?:from|import)\s+\.*" + re.escape(stem)
                     + r"\b", text) is not None


def apply_stage(stage: str, dry_run: bool) -> int:
    with open(PLAN, encoding="utf-8") as f:
        plan = json.load(f)
    if stage not in plan:
        print(f"  ! unknown stage: {stage}")
        print("    known stages: "
              + ", ".join(k for k in plan if not k.startswith("_")))
        return 1

    pairs = plan[stage]
    known = set(tracked())
    directories = set()
    for old, new in pairs:
        absolute = os.path.join(ROOT, old)
        if not os.path.exists(absolute):
            print(f"  ! {old} does not exist — plan out of date?")
            return 1
        if os.path.isdir(absolute):
            directories.add(old)
        if os.path.exists(os.path.join(ROOT, new)):
            print(f"  ! {new} already exists — refusing to overwrite")
            return 1

    # ------------------------------------------------- 1. move the paths
    print(f"  {stage} — {len(pairs)} rename(s)")
    for old, new in pairs:
        kind = "dir " if old in directories else "file"
        print(f"    {kind}  {old}")
        print(f"       ->  {new}")
        if not dry_run:
            os.makedirs(os.path.join(ROOT, os.path.dirname(new)) or ROOT,
                        exist_ok=True)
            subprocess.run(["git", "mv", old, new], cwd=ROOT, check=True)

    # ------------------------------------------- 2. fix every reference
    touched: dict[str, int] = {}
    per_rule: dict[str, int] = {}
    for relative in tracked() if not dry_run else known:
        if not is_text(relative) or relative in NEVER_REWRITTEN:
            continue
        absolute = os.path.join(ROOT, relative)
        if not os.path.exists(absolute):
            continue
        try:
            with open(absolute, encoding="utf-8") as f:
                before = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        after = before
        for old, new in pairs:
            a_directory = old in directories
            stem = os.path.basename(old)[:-3] if old.endswith(".py") else None
            for label, pattern, replacement in rules_for(old, new,
                                                         a_directory):
                if label in ("attribute", "quoted stem") and stem:
                    #  Only in files that really import this module: a dot
                    #  after a common word is rare, but « registre.  » at the
                    #  end of a French sentence is not.
                    if not imports_the_module(after, stem) and \
                       not imports_the_module(before, stem):
                        continue
                nouveau, count = re.subn(pattern, replacement, after)
                if count:
                    after = nouveau
                    per_rule[label] = per_rule.get(label, 0) + count
        if after != before:
            touched[relative] = sum(
                1 for a, b in zip(before.splitlines(), after.splitlines())
                if a != b) or 1
            if not dry_run:
                with open(absolute, "w", encoding="utf-8") as f:
                    f.write(after)

    print()
    print(f"  references rewritten in {len(touched)} file(s):")
    for relative in sorted(touched, key=lambda r: -touched[r])[:40]:
        print(f"    {touched[relative]:4d} line(s)  {relative}")
    if len(touched) > 40:
        print(f"    ... and {len(touched) - 40} more")
    print()
    print("  by rule: " + ", ".join(f"{k} {v}" for k, v in
                                    sorted(per_rule.items())))

    # --------------------------------------- 3. keep the cumulative map
    if not dry_run:
        cumulative = {}
        if os.path.exists(MAP):
            with open(MAP, encoding="utf-8") as f:
                cumulative = json.load(f)
        for old, new in pairs:
            if old in directories:
                for former in known:
                    if former.startswith(old + "/"):
                        origin = next((k for k, v in cumulative.items()
                                       if v == former), former)
                        cumulative[origin] = new + former[len(old):]
            else:
                origin = next((k for k, v in cumulative.items()
                               if v == old), old)
                cumulative[origin] = new
        with open(MAP, "w", encoding="utf-8") as f:
            json.dump(cumulative, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"  · {len(cumulative)} entry/entries in {os.path.relpath(MAP, ROOT)}")
    else:
        print("  (dry run — nothing written)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rename paths and fix every reference to them.")
    parser.add_argument("--stage", help="stage name from the plan")
    parser.add_argument("--dry-run", action="store_true",
                        help="say what would change, write nothing")
    parser.add_argument("--list", action="store_true",
                        help="list the stages of the plan")
    args = parser.parse_args(argv)

    if args.list:
        with open(PLAN, encoding="utf-8") as f:
            plan = json.load(f)
        for name, pairs in plan.items():
            if not name.startswith("_"):
                print(f"  {name:38s} {len(pairs):3d} rename(s)")
        return 0
    if args.stage:
        return apply_stage(args.stage, args.dry_run)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
