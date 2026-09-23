# AGENTS.md — how to work in this repository (Claude Code, ChatGPT, Gemini, other)

This repository is worked on by agents and by humans. This file is **the entry
point**: it says what to read and in what order, what not to do, and how to
leave a trace of what you did. It is deliberately short; everything else lives
elsewhere and is referenced from here.

## 1. Read these, in this order

| Order | File | What it holds |
|---|---|---|
| 1 | `constraints.md` | **The requirements**, as numbered constraints `C-1`…`C-64`. Authoritative. |
| 2 | `.ai/state.md` | **Where the work stands**: what is done, what is left, what is in flight. |
| 3 | `.ai/journal.md` | **What was done, when, and why** — the full log of interventions. |
| 4 | `.ai/decisions.md` | The **design decisions** and their reasons (short ADR format). |
| 5 | `packaging/README.md` | **The package factory**: targets, formats, signing, what is verified and what is not. |
| 6 | `.ai/portability.md` | The Windows / macOS / Linux record: what was fixed, what still holds. |
| 7 | `README.md` | The project from the outside: contents, how to rebuild the PDFs. |
| 8 | `src/phytoscope/README.txt` | The software from the user's point of view. |

## 2. Working rules

1. **Technical US English everywhere**: code, comments, docstrings, interface,
   documents, file names, directory names. US spelling (`behavior`,
   `initialize`, `analyze`), US typography (`"quotes"`, no space before
   `: ; ! ?`), ISO dates (`2026-09-22`).

   This rule replaced a French-only rule on 2026-09-22, at the owner's
   request, because a public repository whose code and documentation are in
   French can only be read by a fraction of its possible contributors. It
   covers **the agent memory under `.ai/`** as well — journal, decisions,
   state, portability record — even though the owner writes to us in French.

   What stays French: proper nouns (`Bretagne Namasté`) and the titles of
   French works cited in the bibliographies. Nothing else.

   Past entries in `.ai/journal.md` and `CHANGELOG.md` are translated like
   the rest. Where such an entry names a file that has since been renamed, it
   is written with the name the file carries **today**, because that is the
   name a reader can act on; the entry still says what happened, and when.

2. **Explain the why.** A comment that paraphrases the code should be deleted;
   a comment that says why the code is the way it is should be kept.
3. **Verify, do not assume.** Every number you write down — pages, tests,
   coverage, throughput — is measured by a command first.
4. **Never edit a generated file** (see `C-45`): edit the source and re-run the
   generator.
5. **Test before you conclude**: `cd src/phytoscope && make test`
   (385 tests, no hardware and no network required).
6. **Record it.** After any substantial change, add a dated entry to
   `.ai/journal.md` and bring `.ai/state.md` up to date. That is what lets the
   next agent — or the same one, three weeks later — pick the work back up.

## 3. What we do not do here

- ❌ **Write to the user's settings** (`~/.config/phytoscope/reglages.json`)
  during a test. Point `XDG_CONFIG_HOME` at a temporary directory.
  *(This rule comes from a real incident: see the journal entry for
  2026-09-18.)*
- ❌ Run the software with `--lang`, `--simulation`, or `--theme` against the
  user's real configuration.
- ❌ Add automatic locale detection (`C-31`).
- ❌ Add a mandatory dependency (`C-40`), or SciPy under any pretext.
- ❌ Use the vocabulary of speech without its warning (`C-5`).
- ❌ `sudo`: everything installs under the home directory (`C-55`). That holds
  for the packaging tools too — `make deps` unpacks them into `~/.local/opt`.
- ❌ **Copy the private signing key** anywhere other than
  `~/.local/share/phytoscope-signature/` and `certificate/` (`C-2R`).
- ❌ Imply that a self-signed certificate silences SmartScreen or Gatekeeper
  (`C-2Q`).

## 4. Useful commands

```bash
# Software
cd src/phytoscope
make test                      # 385 tests
make demo                      # a guided look, no hardware needed
.venv/bin/python tools/i18n.py --couverture     # translation coverage
.venv/bin/python tools/sbom.py --json           # software bill of materials

# Publications (from the repository root) — 10 PDFs, 1,385 pages
python3 pdf-src/assets/svg/gen.py         && python3 pdf-src/build.py         # main book,      478 pp.
python3 pdf-src/assets/svg/gen_tt.py      && python3 pdf-src/build_tree.py   # the series,     573 pp.
python3 pdf-src/assets/svg/gen_sch.py     && python3 pdf-src/build_appendix.py  # the appendix,    65 pp.
python3 pdf-src/assets/svg/gen_board.py   && python3 pdf-src/build_board.py   # the special,    235 pp.
python3 pdf-src/assets/svg/gen_sdk.py     && python3 pdf-src/build_sdk.py     # the SDK guide,   35 pp.
python3 tools/verify_svg.py                    # are the 104 figures well-formed XML?
git diff --name-only | python3 tools/impacted_pdfs.py -   # which PDFs need rebuilding?

# Translation of the repository — see .ai/rename-plan.json
python3 tools/verify_translation.py --remaining   # how much French is left, per area
python3 tools/verify_translation.py --compare .ai/translation-baseline.json \
        --renames .ai/translation-renames.json    # did any code move? (it must not)
python3 tools/apply_renames.py --list             # the rename stages

# Installer packages (from Debian, Ubuntu, or Mint)
cd packaging
make tools        # what is missing in order to package
make deps          # NSIS, msitools, osslsigncode — without sudo
make certificate    # once
make all          # .deb .rpm .run .exe .msi .pkg .zip .tar.gz, all signed
make verify      # reopen and check everything that was produced

# Firmware
cd src/firmware
./_make_.sh --deps             # installs the SDK and the ARM toolchain in $HOME, no sudo
./_make_.sh                    # -> build/phytosense.uf2 — compiles only
./build.sh                     # compiles AND files the deliverable under build/packages/
```

## 5. Where everything lives

The repository was tidied on 2026-09-18: **code** lives under `src/`,
**publishing sources** under `pdf-src/`, and `sources/` holds nothing but
**reference material** — things we did not write.

```
constraints.md              the requirements (authoritative)
CHANGELOG.md                the history of the whole project
README.md                   the project from the outside
INSTALL.md                  what each installer does, system by system
PACKAGING.md                how to build one package, or all of them
CONTRIBUTING.md             how to contribute; SECURITY.md: how to report
LICENSE, LICENSES/          MIT (software) and CERN-OHL-P v2 (hardware) — C-53
.ai/                        the agent memory (journal, decisions, state)
.github/                    continuous integration, issue templates

src/                        ALL THE CODE
  phytoscope/               the PhytoScope software (Python + Qt) — 70 modules
    Makefile                `make test`, `make demo`, `make doctor`
    phytoscope/VERSION      THE version — the only source of truth
    phytoscope/AUTHORS      publisher, author, website — the only source
    phytoscope/core/        acquisition, DSP, session, quantities
    phytoscope/music/       signal → music, MIDI, voice
    phytoscope/ui/          the Qt interface
    phytoscope/api/         the third-party module contract — API 3.0
    phytoscope/languages/   the 10 translation catalogues (JSON)
    phytoscope/lexicons/    the 11 Speech-mode dictionaries (JSON)
    tests/                  13 files, 385 tests — no hardware, no network
  firmware/                 the RP2350 firmware (C, Pico SDK) — 7 files
    _make_.sh               builds — `--deps` installs the SDK and toolchain
    build.sh                builds AND files the deliverable in build/packages/
  sdk/                      the kit for writing a third-party module
    docs/                   the documentation, in eight parts
    hello-world/            the example module, with its tests
    tools/new_module.py

pdf-src/                    THE SOURCES OF THE TEN PUBLICATIONS
  build.py                  the main book                            478 pp.
  build_tree.py             the "Talking Tree" series (v1 v2 v3)
  build_appendix.py         the series' technical appendix            65 pp.
  build_board.py            the companion volume and its 3 fascicles
  build_sdk.py              the SDK guide                             35 pp.
  book.css board.css        the house styles (paged media)
  tree.css fonts.css
  assets/svg/               104 illustrations + their 5 generators
  assets/img/               239 photographs and plates
  assets/fonts/             Cinzel, Cormorant Garamond (SIL OFL 1.1)
  common/                   shared fragments — the bill-of-materials tables
                            ONE DIRECTORY PER PUBLICATION:
  the-music-of-plants/            478 pp.  the main book
  talking-tree-dublin/            212 pp.  the investigation
  plant-biocommunication-and-ai/  163 pp.  the treatise
  workshop-build-a-talking-tree/  198 pp.  the workshop manual
  talking-tree-appendix/           65 pp.  plates, BOM, programs
  the-phytosense-board/           197 pp.  the technical companion volume
  phytosense-schematics/           12 pp.  a detachable fascicle
  phytosense-bom-accessories/      18 pp.  a detachable fascicle
  phytosense-pcb/                   7 pp.  a detachable fascicle
  writing-a-phytoscope-module/     35 pp.  the SDK guide

hardware/                   bill of materials and accessories (CSV) — CERN-OHL-P v2
packaging/                  the installation-package factory
  Makefile                  chains the targets — `make all`, `make macos`
  common.py                 what depends on no particular system
  build_<os>.py             one generator per system, self-contained
  signature.py              X.509 certificate, Authenticode and CMS
  certificate.py            creates, recreates and installs the certificate
  languages.py              the installers' labels, 11 languages
  macos_pkg.py              the .pkg format, written end to end
  templates/                control, .spec, .nsi, .wxs, Info.plist, launchers
tools/                      the repository's tools
  headers.py                writes and checks the attribution headers
  verify_svg.py             are the illustrations well-formed XML?
  impacted_pdfs.py          which publications to rebuild, given what changed
  sbom.py                   the PROJECT's bill of materials — software AND firmware
  gen_bom.py gen_index.py   generated fragments — never edit them (C-45)
  gen_glossary.py gen_credits.py gen_code_annex.py
  fetch-software.py         fetches the third-party repositories (817 MB, out of tree)
certificate/                the PUBLIC certificate; the private key is excluded

sources/                    REFERENCE MATERIAL — nothing we wrote, except
                            sources/reverse/. Excluded from tools/headers.py.
  brevets/                  13 patents (PDFs out of tree)
  datasheets/               9 component datasheets (out of tree)
  manufacturer-manuals/     11 manuals (out of tree)
  documents/                articles; public domain (transcriptions)
  ebooks/                    5 books under copyright (out of tree)
  schematics/                3 third-party projects, WITH their licence —
                            including biotron-firmware, which is GPL-3.0
  code/ software/           69 third-party repositories, archived (out of tree)
  reverse/damanhur-bridge/  our reconstruction of US patent 6,487,817 (MIT)
  midi/ usb/                our two reference documents (22 and 24 pp.)
  01-…-04-….md              sourced research notes
  INDEX.md                  the index of the corpus

build/                      the PDFs produced — never edited by hand
build/packages/             the packages produced — never edited by hand
```

## 6. What the repository does not contain, and why

The repository is **public**. Three families of file stay on the disk but are
kept out by `.gitignore`:

| What | Why |
|---|---|
| `certificate/phytoscope.key` | The private signing key (`C-2R`). Its reference copy lives in `~/.local/share/phytoscope-signature/`. |
| `sources/ebooks/`, `sources/brevets/*.pdf`, `sources/datasheets/*.pdf`, `sources/manufacturer-manuals/*.pdf`, `sources/documents/scientific-articles/*.pdf` | We have no right to redistribute them. Their bibliographic references are in `sources/INDEX.md`. |
| `sources/documents/public-domain/*.pdf` | Not for the rights — Bose and Darwin are free — but for the weight: 260 MB of scans. The transcriptions stay version-controlled; see the directory's own `README.md`. |
| `sources/code/*.zip`, `sources/software/**/*.zip` | 817 MB of third-party repositories. `python3 tools/fetch-software.py` fetches them from source; `sources/software/MANIFESTE.md` keeps the provenance and the licences. |
| `build/`, `.venv/`, `__pycache__/` | They rebuild themselves. |

> `.ecarte/` used to be listed here — a place to set things aside rather than
> delete them. It was emptied and removed on 2026-09-23 (857 MB). The
> `.gitignore` rule stays, because the habit is a good one.
