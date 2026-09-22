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
build breaks; over-reach and prose gets mangled — `commun` is also an ordinary
French word, and a blind substitution turns "le socle commun" into "le socle
common".

Substitution here is therefore **syntactic, never lexical**.

Path rules, applied to every tracked text file
----------------------------------------------

  · **full paths.** `packaging/commun.py` -> `packaging/common.py`.
  · **bare basenames.** `commun.py` -> `common.py`. Distinctive thanks to the
    extension.

Module rules, applied to a Python file only when it *binds* the module
----------------------------------------------------------------------

A module is bound by any of these, and all four forms occur in this
repository:

    import commun
    import phytoscope.core.commun
    from commun import quelque_chose
    from phytoscope.core import commun          <- the one that was missed

When a file binds the module, three rewrites apply and nothing else:

  · the **module path** of an `import` / `from ... import` statement, dotted
    component by dotted component, so that a longer name merely containing
    the stem is left alone;
  · the **imported names** of a `from ... import a, b, c` statement, in name
    position only;
  · **module attribute access**, `commun.RACINE` -> `common.RACINE`.

Two mistakes this design exists to prevent, both of which happened
------------------------------------------------------------------

**A quoted bare word is never substituted.** The first version did, and it
lasted one stage: renaming `packaging/certificat.py` rewrote

    CERTIFICAT_PROJET = os.path.join(_RACINE, "certificat", ...)

in `signature.py`, where `"certificat"` is the **directory** — renamed in a
later stage, so the code then pointed at a path that did not exist. A quoted
word can be a directory, a settings key, a catalog entry, or displayed text;
nothing distinguishes them from outside, and a module named as a string is
rare enough to edit by hand.

**Module attribute access requires an identifier after the dot.** The second
version matched `stem` followed by a dot, and broke two things at once:

    module.contexte.reglages   ->  module.context.reglages

where `contexte` is a **field of an object**, not the module — the loaded
module object had no `context` attribute, and Python said so; and, in French
prose, a sentence ending in "... reste d'espace." matches "stem followed by a
dot" perfectly well. The pattern now demands `\\.[A-Za-z_]`, and forbids a
preceding `.` or word character, which excludes both cases.

The test suite caught both. That is the only reason they are worth recounting
here: a rename tool is exactly as trustworthy as what runs after it.

Reading the plan
----------------

`.ai/rename-plan.json` holds ordered stages, each a list of
`[old path, new path]`. Stages exist so that a mistake costs one stage and not
sixty-three renames: apply one, run the tests, commit, move on.

Every run writes the cumulative `{old path: new path}` map for every tracked
file to `.ai/translation-renames.json`, which is what
`tools/verify_translation.py --renames` needs in order to follow a file across
a rename instead of reporting it as lost.

Usage
-----

    python3 tools/apply_renames.py --list
    python3 tools/apply_renames.py --stage stage-1-packaging-modules --dry-run
    python3 tools/apply_renames.py --stage stage-1-packaging-modules
    python3 tools/apply_renames.py --stage stage-1-packaging-modules \\
                                   --references-only

`--dry-run` is not optional in practice: run it, read what it says it will
touch, then run it for real. `--references-only` moves nothing and only
catches up on references — what you need after fixing a rule that had missed
some.
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

#  Extensions in which references are rewritten. Binary and generated files
#  are left alone; the generated ones are rebuilt from their sources (C-45).
TEXT = (".py", ".sh", ".md", ".html", ".css", ".txt", ".yml", ".yaml",
        ".json", ".cfg", ".toml", ".spec", ".nsi", ".cmake", ".c", ".h",
        ".ino", ".in", ".desktop", ".control", ".gitignore", ".cmd")

BY_NAME = ("Makefile", "control", "AUTHORS", "LICENSE", "VERSION", "AUTEURS",
           "CODEOWNERS")

#  Files left out of reference rewriting, and the only three that are.
#
#    · the baseline is keyed by the paths as they were BEFORE any rename.
#      Rewriting it would erase the very mapping it exists to anchor, and
#      tools/verify_translation.py would then compare each file against
#      itself and pass whatever happened;
#    · the rename map is this tool's own output;
#    · the plan holds the OLD paths by construction. Stage 2 rewrote its own
#      entries into "tools/headers.py -> tools/headers.py" before this
#      exclusion existed; stage 1 escaped only because the plan was still
#      untracked, so `git ls-files` did not list it. Restored by hand, and
#      excluded here so the record keeps saying what was renamed.
NEVER_REWRITTEN = (
    ".ai/translation-baseline.json",
    ".ai/translation-renames.json",
    ".ai/rename-plan.json",
)


def tracked() -> list[str]:
    issue = subprocess.run(["git", "ls-files"], cwd=ROOT,
                           capture_output=True, text=True, check=True)
    return issue.stdout.split()


def is_text(relative: str) -> bool:
    return relative.endswith(TEXT) or os.path.basename(relative) in BY_NAME


# --------------------------------------------------------------- module rules
def binds_module(text: str, stem: str) -> bool:
    """Does this file bind `stem` as a module name?

    All four forms that occur in this repository, including
    `from phytoscope.core import commun`, whose omission broke stage 3.
    """
    s = re.escape(stem)
    return re.search(
        r"(?m)^\s*(?:"
        #  import commun  /  import phytoscope.core.commun
        r"import\s+(?:[\w.]+\.)?" + s + r"\b"
        #  from commun import X  /  from phytoscope.core.commun import X
        r"|from\s+\.*(?:[\w.]+\.)?" + s + r"\b\s*import\b"
        #  from phytoscope.core import commun  /  from . import commun
        r"|from\s+[\w.]*\s*import\s+[^#\n]*?(?<![\w.])" + s + r"\b"
        r")", text) is not None


def _rewrite_components(path: str, stem: str, new_stem: str) -> str:
    """Rewrite `stem` as a whole dotted component of a module path."""
    return ".".join(new_stem if part == stem else part
                    for part in path.split("."))


def _rewrite_names(names: str, stem: str, new_stem: str) -> str:
    """Rewrite `stem` in name position among imported names."""
    return re.sub(r"(?<![\w.])" + re.escape(stem) + r"\b", new_stem, names)


def module_rewrites(text: str, stem: str, new_stem: str) -> str:
    """Apply the three module rewrites to one Python source text."""
    if not binds_module(text, stem):
        return text

    def _from(trouve):
        return (trouve.group(1)
                + _rewrite_components(trouve.group(2), stem, new_stem)
                + trouve.group(3)
                + _rewrite_names(trouve.group(4), stem, new_stem))

    text = re.sub(r"(?m)^(\s*from\s+)([\w.]*)(\s+import\s+)([^#\n]*)",
                  _from, text)

    def _import(trouve):
        return trouve.group(1) + ",".join(
            _rewrite_components(part.strip(), stem, new_stem)
            for part in trouve.group(2).split(","))

    text = re.sub(r"(?m)^(\s*import\s+)([\w.,\s]+?)(?=\s*(?:#|$))",
                  _import, text)

    #  Module attribute access. The dot must be followed by an identifier —
    #  otherwise a French sentence ending in "... d'espace." would match — and
    #  must not be preceded by a dot or a word character, which is what tells
    #  a module apart from a field of the same name (`module.contexte.x`).
    text = re.sub(r"(?<![\w.])" + re.escape(stem) + r"(?=\.[A-Za-z_])",
                  new_stem, text)
    return text


def path_rules(old: str, new: str, a_directory: bool) -> list[tuple[str, str]]:
    """(pattern, replacement) for the textual path references of one rename."""
    rules = [(re.escape(old), new)]
    old_base, new_base = os.path.basename(old), os.path.basename(new)
    if not a_directory and old_base != old and old_base != new_base:
        rules.append((re.escape(old_base), new_base))
    return rules


# --------------------------------------------------------------------- actions
def apply_stage(stage: str, dry_run: bool, references_only: bool) -> int:
    with open(PLAN, encoding="utf-8") as f:
        plan = json.load(f)
    if stage not in plan:
        print(f"  ! unknown stage: {stage}")
        print("    known stages: "
              + ", ".join(k for k in plan if not k.startswith("_")))
        return 1

    pairs = [(o, n) for o, n in plan[stage]]
    known = set(tracked())
    directories = set()
    for old, new in pairs:
        if references_only:
            if os.path.isdir(os.path.join(ROOT, new)):
                directories.add(old)
            continue
        if not os.path.exists(os.path.join(ROOT, old)):
            print(f"  ! {old} does not exist — plan out of date?")
            return 1
        if os.path.isdir(os.path.join(ROOT, old)):
            directories.add(old)
        if os.path.exists(os.path.join(ROOT, new)):
            print(f"  ! {new} already exists — refusing to overwrite")
            return 1

    # -------------------------------------------------- 1. move the paths
    print(f"  {stage} — {len(pairs)} rename(s)"
          + ("  (references only)" if references_only else ""))
    for old, new in pairs:
        kind = "dir " if old in directories else "file"
        print(f"    {kind}  {old}")
        print(f"       ->  {new}")
        if not dry_run and not references_only:
            parent = os.path.join(ROOT, os.path.dirname(new))
            os.makedirs(parent or ROOT, exist_ok=True)
            subprocess.run(["git", "mv", old, new], cwd=ROOT, check=True)

    # -------------------------------------------- 2. fix every reference
    stems = [(os.path.basename(o)[:-3], os.path.basename(n)[:-3])
             for o, n in pairs
             if o not in directories and o.endswith(".py")
             and os.path.basename(o) != os.path.basename(n)]

    touched: dict[str, int] = {}
    counts = {"path": 0, "basename": 0, "module": 0}
    for relative in (known if dry_run else tracked()):
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
            for index, (pattern, replacement) in enumerate(
                    path_rules(old, new, old in directories)):
                nouveau, n = re.subn(pattern, replacement, after)
                if n:
                    counts["path" if index == 0 else "basename"] += n
                    after = nouveau
        if relative.endswith(".py"):
            for stem, new_stem in stems:
                nouveau = module_rewrites(after, stem, new_stem)
                if nouveau != after:
                    counts["module"] += 1
                    after = nouveau

        if after != before:
            touched[relative] = sum(
                1 for a, b in zip(before.splitlines(), after.splitlines())
                if a != b) or 1
            if not dry_run:
                with open(absolute, "w", encoding="utf-8") as f:
                    f.write(after)

    print()
    print(f"  references rewritten in {len(touched)} file(s):")
    for relative in sorted(touched, key=lambda r: (-touched[r], r))[:40]:
        print(f"    {touched[relative]:4d} line(s)  {relative}")
    if len(touched) > 40:
        print(f"    ... and {len(touched) - 40} more")
    print()
    print("  paths {path}, basenames {basename}, "
          "files whose module references moved {module}".format(**counts))

    # ----------------------------------------- 3. keep the cumulative map
    if not dry_run and not references_only:
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
                origin = next((k for k, v in cumulative.items() if v == old),
                              old)
                cumulative[origin] = new
        with open(MAP, "w", encoding="utf-8") as f:
            json.dump(cumulative, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"  · {len(cumulative)} entry/entries in "
              f"{os.path.relpath(MAP, ROOT)}")
    elif dry_run:
        print("  (dry run — nothing written)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rename paths and fix every reference to them.")
    parser.add_argument("--stage", help="stage name from the plan")
    parser.add_argument("--dry-run", action="store_true",
                        help="say what would change, write nothing")
    parser.add_argument("--references-only", action="store_true",
                        help="move nothing; only catch up on the references "
                             "of a stage already applied")
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
        return apply_stage(args.stage, args.dry_run, args.references_only)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
