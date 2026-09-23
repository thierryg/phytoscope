## What this request does

<!-- In a sentence or two, and above all: why. -->

## Why

<!--
The repository's rule: a comment that paraphrases the code is to be deleted,
a comment that says why the code is as it is, is to be kept. The same here.
If there is an issue, point at it: "fixes #12".
-->

## What I checked

<!-- Tick what you actually ran. An unticked box is not a reproach: it tells
     the reviewer where to look. -->

- [ ] `cd src/phytoscope && make test` — the suite passes
- [ ] `cd src/phytoscope && make lint`
- [ ] `pre-commit run --all-files`
- [ ] `python3 tools/headers.py --verifier` — the headers are up to date
- [ ] `python3 tools/verify_svg.py` — if I touched the illustrations
- [ ] The publications rebuild — if I touched `pdf-src/` or the `build_*.py`
- [ ] `cd packaging && make all && make verify` — if I touched the packaging

## Figures

<!--
The repository requires measuring before asserting. If your text states a
number — of pages, of tests, of references, a price, a data rate — give the
command that produces it.
-->

## What I recorded

- [ ] A dated entry in `.ai/journal.md`
- [ ] `.ai/state.md` brought up to date
- [ ] `.ai/decisions.md` — if this settles a design question
- [ ] `CHANGELOG.md` — if it shows from the outside
- [ ] `constraints.md` — if a constraint changes (and then say which)

## The repository's checks

- [ ] Everything is in technical US English (`C-42`) — the interface excepted,
      which follows the catalogues
- [ ] No mandatory dependency added (`C-40`)
- [ ] No `sudo` (`C-55`)
- [ ] No generated file edited by hand (`C-45`)
- [ ] **No private key, no secret** (`C-2R`)
- [ ] No attribution header stamped on third-party code (`sources/`)
- [ ] If the module contract changed: the major bumped and the migration
      documented (`C-49`)
