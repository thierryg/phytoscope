<!-- PhytoScope — the main README -->

# PhytoScope

**Listening to plants without telling stories.**

PhytoScope measures electrical and physiological quantities on a living
plant, transposes them into music, and **says at every step what is measured
and what is interpreted**. It is a complete project: a piece of software, an
acquisition board, a firmware, a module kit, a signed-package factory — and
ten publications that document the lot, down to the limits of what can
honestly be claimed.

> **A plant expresses nothing.** A signal is transposed. The project holds
> that distinction to be its heart, not a formality: constraint `C-5` of the
> requirements forbids using the vocabulary of speech without its warning,
> and code review watches for it.

| | |
|---|---|
| **Version** | 1.6.0 — 23 September 2026 |
| **Publisher** | Bretagne Namasté — [bretagne-namaste.com](https://bretagne-namaste.com) |
| **Licences** | **MIT** (software, firmware, tools) · **CERN-OHL-P v2** (hardware) — see [`LICENSES/README.md`](LICENSES/README.md) |
| **Language** | The whole repository is in technical US English, code and comments included. The software and the installers speak **11 languages** |
| **Systems** | Debian · Ubuntu · Mint · Fedora · RHEL · Windows 10/11 · macOS |
| **Python** | ≥ 3.9 (tested on 3.10 and 3.12) |

---

## Contents

1. [What the project does](#1-what-the-project-does)
2. [Installing](#2-installing)
3. [The repository tree](#3-the-repository-tree)
4. [The software](#4-the-software--srcphytoscope)
5. [The firmware](#5-the-firmware--srcfirmware)
6. [The module kit](#6-the-module-kit--srcsdk)
7. [The hardware](#7-the-hardware--hardware)
8. [The ten publications](#8-the-ten-publications--pdf-src)
9. [Building the packages](#9-building-the-packages--packaging)
10. [Continuous integration and DevSecOps](#10-continuous-integration-and-devsecops)
11. [Security and secrets](#11-security-and-secrets)
12. [What the repository does not contain](#12-what-the-repository-does-not-contain-and-why)
13. [Contributing](#13-contributing)
14. [The project in figures](#14-the-project-in-figures)

---

## 1. What the project does

### The chain, from plant to sound

```
   PLANT              PhytoSense One BOARD              COMPUTER
   ┌──────┐   electrodes ┌────────────────────┐   USB   ┌───────────────────┐
   │      │──────────────▶│ electrometric      │────────▶│ acquisition       │
   │ Rp   │   Ag/AgCl     │ stage (1 GΩ)       │  CDC    │ descriptors       │
   │      │               │ synchronous-       │         │ correspondence    │
   └──────┘               │ detection bridge   │         │ synthesis / MIDI  │
      ▲                   │ 24-bit ADC         │         │ voice (11 lexicons)│
      │                   │ RP2350, two cores  │         └───────────────────┘
   ambient:               └────────────────────┘                  │
   light, CO₂,                      │                             ▼
   temperature,              ambient sensors           sound · MIDI · CSV
   soil moisture             (I²C / 1-Wire)            a replayable session
```

The board **interprets nothing**: no event detection, no musical rule, no
filtering beyond the converter's own. All the reasoning is computed on the
computer, **where it can be changed, checked and replaced**. One exception:
the direct MIDI output, which carries a reduced version of the correspondence
engine so that a hardware synthesiser can be driven without going through the
audio chain.

### Three readings of one signal

The project refuses to choose between measurement and felt experience, and
refuses to confuse them. Every phenomenon is presented on three registers,
always kept apart:

| Register | What is claimed | Where it is documented |
|---|---|---|
| **Measured** | What an instrument gives, with its uncertainty | *The PhytoSense Board*, `core/quantities.py` |
| **Plausible** | What the literature establishes, with its reference | *The Music of Plants*, `sources/INDEX.md` |
| **Not measurable** | What belongs to experience, and is said as such | *The Talking Tree*, the epistemic scale |

---

## 2. Installing

The installation packages carry **everything they need**: the Python
interpreter, Qt, the libraries. Nothing to install beforehand, and no
administrator rights for the `.run`, the `.exe` or the portable archive.

| System | File |
|---|---|
| Debian, Ubuntu, Mint | `sudo apt install ./phytoscope_1.6.0_all.deb` |
| Fedora, RHEL, Rocky | `sudo dnf install ./phytoscope-1.6.0-1.noarch.rpm` |
| Every distribution | `./PhytoScope-1.6.0-Linux.run` — **no privileges** |
| Windows 10 / 11 | `PhytoScope-1.6.0-Windows.exe`, `.msi`, or the portable archive |
| macOS | `PhytoScope-1.6.0.pkg` |
| The board | `phytosense-1.6.0.uf2` — copy onto the board in BOOTSEL |

**The language is asked at the very start of the installation**, from the
eleven, each offered in its own script. The answer goes into the settings and
PhytoScope takes it up: the question never comes back.

> **What each installer does, step by step and system by system**, is
> described in [`INSTALL.md`](INSTALL.md).
> **How these packages are built**: [`PACKAGING.md`](PACKAGING.md).

### From source

```bash
git clone https://github.com/thierryg/phytoscope.git
cd phytoscope/src/phytoscope
make doctor           # what the SYSTEM Python has, before installing anything
make install-dev      # a virtual environment + the development tools
make test             # 385 tests, no hardware and no network
make demo             # start up with a simulated plant
```

`make doctor` runs with the **system** Python, deliberately: it is the first
thing to reach for when nothing starts, and it depends on nothing. It prints
which interpreter it inspected. For the state of the project's own
environment, `phytoscope --check` is the answer.

`make system-deps` prints the exact command for installing your
distribution's system libraries.

---

## 3. The repository tree

One simple rule: **code under `src/`, publishing sources under `pdf-src/`,
and `sources/` holds nothing but reference material — things we did not
write.**

```
phytoscope/
├── src/                            ALL THE CODE
│   ├── phytoscope/                 the software (Python 3 + Qt 6) — 70 modules
│   ├── firmware/                   the RP2350 firmware (C, Pico SDK)
│   └── sdk/                        the kit for writing a third-party module
│
├── pdf-src/                        THE SOURCES OF THE TEN PUBLICATIONS
│   ├── build.py  build_tree.py     ┐
│   ├── build_appendix.py           │ the five factories
│   ├── build_board.py  build_sdk.py┘
│   ├── book.css board.css          the house styles (paged media)
│   ├── tree.css fonts.css
│   ├── assets/svg/                 104 illustrations + their 5 generators
│   ├── assets/img/                 234 photographs and plates
│   ├── assets/fonts/               Cinzel, Cormorant Garamond (SIL OFL 1.1)
│   ├── common/                     shared fragments (bills of materials)
│   │                               ONE DIRECTORY PER PUBLICATION:
│   ├── the-music-of-plants/            478 pp. — the main book
│   ├── talking-tree-dublin/            212 pp. — the investigation
│   ├── plant-biocommunication-and-ai/  163 pp. — the treatise
│   ├── workshop-build-a-talking-tree/  198 pp. — the workshop manual
│   ├── talking-tree-appendix/           65 pp. — plates, BOM, programs
│   ├── the-phytosense-board/           197 pp. — the technical companion
│   ├── phytosense-schematics/           12 pp. ┐
│   ├── phytosense-bom-accessories/      18 pp. │ detachable fascicles
│   ├── phytosense-pcb/                   7 pp. ┘
│   └── writing-a-phytoscope-module/     35 pp. — the SDK guide
│
├── hardware/                       bill of materials and accessories (CSV)
│                                   → CERN-OHL-P v2, not MIT
├── packaging/                      the signed-package factory
├── tools/                          the repository's tools
├── certificate/                    the PUBLIC certificate (the key is excluded)
│
├── sources/                        REFERENCE MATERIAL
│   ├── brevets/ datasheets/        facsimiles — out of tree (rights)
│   ├── manufacturer-manuals/
│   ├── documents/                  articles; public domain (transcriptions)
│   ├── ebooks/                     books under copyright — out of tree
│   ├── schematics/                 3 third-party projects, WITH their licence
│   ├── code/ software/             69 third-party repositories — out of tree (817 MB)
│   ├── reverse/damanhur-bridge/    our reconstruction of an expired patent
│   ├── midi/ usb/                  our two reference documents (22 and 24 pp.)
│   ├── 01-…04-….md                 sourced research notes
│   └── INDEX.md                    the index of the corpus
│
├── build/                          the PDFs, the packages and the .uf2 produced
│                                   — NEVER edited by hand (C-45)
├── .ai/                            the project's memory: journal, decisions,
│                                   state, portability record
├── .github/workflows/              7 continuous-integration workflows
├── constraints.md                  THE REQUIREMENTS — authoritative
├── AGENTS.md                       the way in, for an agent or a human
├── INSTALL.md                      what each installer does, per OS
├── PACKAGING.md                    how to build one package, or all of them
├── sbom.cdx.json                   the whole project's bill of materials
├── CONTRIBUTING.md  SECURITY.md  CODE_OF_CONDUCT.md
└── LICENSE  LICENSES/              MIT and CERN-OHL-P v2
```

### Why `sources/` is not `src/`

They are opposites, and confusing them has real consequences:

- `src/` is **our code**. `tools/headers.py` stamps our attribution header
  and its `SPDX-License-Identifier` there.
- `sources/` is **what other people wrote**. It is **excluded** from
  `tools/headers.py`. The reason is concrete: the tool had put
  "© Bretagne Namasté" and "MIT" on 32 files there, among them the **Biotron
  firmware, which is GPL-3.0**. That was a false statement of licence and of
  authorship; it was corrected, and the CI's `licences` job refuses to let it
  come back.

---

## 4. The software — `src/phytoscope/`

70 Python modules, 23,984 lines, **385 tests** that pass **with no hardware
and no network**.

```bash
cd src/phytoscope
make install-dev      # a virtual environment + the development tools
make doctor           # what the SYSTEM Python has — before the venv
make demo             # start the software with a simulated plant
make test             # 385 tests, ~6 s
make lint             # ruff
```

`make doctor` inspects the system Python and says so ("Executable: …"); it
does not look at the project's environment, and that is deliberate — it is
for when that environment does not exist yet. For the state of the
environment, `phytoscope --check`.

### How it is organised

| Directory | What is in it |
|---|---|
| `phytoscope/core/` | acquisition, timestamping, DSP, session, descriptors, physical quantities, rig fingerprint, pre-flight, **library updates** |
| `phytoscope/music/` | signal → music correspondence, scales, instruments, synthesis, MIDI output, Speech mode |
| `phytoscope/ui/` | the Qt 6 interface — tabs, real-time plots, log, settings, diagnostics |
| `phytoscope/api/` | the third-party module contract — API **3.0**: context, events, registry |
| `phytoscope/languages/` | 10 translation catalogues (ar, es, fr, id, it, ja, ko, pt, ru, zh) |
| `phytoscope/lexicons/` | 11 Speech-mode dictionaries (the 10 above + en) |
| `phytoscope/modules/` | 4 shipped modules: advanced descriptors, rig fingerprint, CSV export, scientific quantities |

### At start-up: the banner, the checklist, the pre-flight checks

```
   ____  _           _        ____
  |  _ \| |__  _   _| |_ ___ / ___|  ___ ___  _ __   ___
  | |_) | '_ \| | | | __/ _ \\___ \ / __/ _ \| '_ \ / _ \
  |  __/| | | | |_| | || (_) |___) | (_| (_) | |_) |  __/
  |_|   |_| |_|\__, |\__\___/|____/ \___\___/| .__/ \___|
               |___/                         |_|
                                   v1.6.0   Bretagne Namasté

  PhytoScope 1.6.0 — checklist
  ──────────────────────────────────────────────────────────────────────────
  [·] System               Ubuntu 22.04.5 LTS 22.04 (x86_64)
  [·] Python               3.10.12  (virtual environment)
  [✓] Dependencies         all present
  [!] PhytoSense board     absent — falling back to the internal generator
  [✓] Audio inputs         11 — HDA Intel PCH: ALC3204 Analog (hw:0,0)
  …
```

Then the **pre-flight checks**, dependency by dependency, each with its
version. That listing is what to attach to any report. `--no-diagnostic`
suppresses it.

### "Help → Library updates…"

The software compares the installed Python libraries with what the package
index publishes, sorts the differences into *patch*, *minor* and *major*, and
**installs nothing without being asked explicitly**. The query runs on a
separate thread, nothing is ticked in advance, and `pip`'s output scrolls
line by line.

### Dependencies

**Five runtime dependencies, and not one more** — constraint `C-40` forbids
adding one lightly, and rules out SciPy without exception:

```
numpy>=1.24        all the signal processing
PySide6>=6.5       the Qt 6 graphical interface (LGPL)
pyqtgraph>=0.13    accelerated real-time plots (otherwise a slower in-house one)
sounddevice>=0.4.6 audio input and output (PortAudio)
pyserial>=3.5      the PhytoSense board and serial rigs (Arduino, NE555)
```

Optional, and the software works without them: `python-rtmidi` (MIDI ports),
`pyttsx3` (the system's speech synthesis).

### Two files are authoritative

`src/phytoscope/phytoscope/VERSION` and `.../AUTHORS` are the **only**
sources of truth for the version and the attribution. The software reads them
for its "About" window, the package factory in order to stamp the `.deb`,
`tools/headers.py` for the headers, `packaging/signature.py` for the X.509
certificate's subject, and `src/firmware/build.sh` for the firmware's notice.
They live **inside the Python package** rather than at the root, for a simple
reason: installed software does not carry the repository with it.

### Homebrew, Nix and conda are excluded — deliberately

An interpreter installed under `/home/linuxbrew`, `/opt/homebrew`,
`/nix/store` or `/opt/conda` comes with **its own dynamic loader**. It does
not read the distribution's search path: Qt, pyqtgraph and sounddevice
install there without error, then fail at run time on `libGL.so.1` — a
library that **is in fact present**.

So `./run.py` re-launches itself with a suitable interpreter, and the
diagnostic tells the truth instead of advising you to install a package that
is already there.

---

## 5. The firmware — `src/firmware/`

7 C files, 1,906 lines, for an **RP2350** (Pico SDK ≥ 2.0.0; the 1.x versions
know only the RP2040 and fail at configuration).

**Two scripts, two uses.**

| | What it does |
|---|---|
| `./_make_.sh` | builds, and nothing else → `build/phytosense.uf2` (84 kB) |
| `./build.sh` | builds **and then files the deliverable** under `build/packages/…/Firmware/`, named with its version, with its checksums and a notice |

```bash
cd src/firmware
./_make_.sh --deps    # Pico SDK and ARM toolchain in $HOME, no sudo — once
./build.sh            # build and file the deliverable
```

The `.uf2` is **a deliverable in its own right**: without it, the packages
install software that has nothing to listen to. The CI builds it on every
run — a binary made by hand is a binary nobody can tie to a commit.

### How the two cores divide the work

| Core | Task | Constraint |
|---|---|---|
| 0 | USB, the control dialogue, ambient sensors, MIDI, the display | may block without consequence for the measurement |
| 1 | servicing the converter, timestamping, the ring buffer | a bounded loop, no allocation, no waiting |

`main()` is core 0 by definition, and that is where USB is handled;
`multicore_launch_core1()` starts the measurement loop. The two cores share
nothing but the ring buffer, through atomic indices. That is what makes the
stream **free of holes** even while the computer is questioning the board in
the middle of an acquisition.

### The control dialogue

Deliberately archaic: text commands terminated by CR-LF, answers on one line
beginning with `+` (success) or `-` (error) followed by a JSON object. So the
board **can be questioned and diagnosed with any terminal**, without
installing anything.

The USB side — the descriptors, the two data paths, the byte layout, and what
three operating systems do with the device — is documented field by field in
`sources/usb/reference.html` (24 pp.). Section 11 of it records three places
where the device's behaviour did not match its own descriptors; all three
were settled on 2026-09-23.

> **This firmware builds, but no board has ever been plugged in.** What
> compiles is not what works: the pinout and the response times need the
> hardware. `src/firmware/README.md` says precisely what is left to try.

---

## 6. The module kit — `src/sdk/`

A third-party module adds a descriptor, a sonification mode or an exporter,
**without touching the software**.

```bash
python3 src/sdk/tools/new_module.py my-module --capability descriptor
python3 src/sdk/tools/new_module.py my-module --install
```

- `src/sdk/docs/` — the documentation, in eight parts;
- `src/sdk/hello-world/` — the example module, **with its tests**;
- the same material, laid out for print:
  `build/writing-a-phytoscope-module.pdf` (35 pp.).

The contract carries its own version, **API 3.0** (`C-49`). A module declares
the **minimum** it needs; the host refuses at discovery what it cannot
honour, naming both versions, rather than loading it halfway. Chapter 8 of
the SDK is the migration from 2.0.

---

## 7. The hardware — `hardware/`

| File | Contents |
|---|---|
| `bom.csv` | **68 references**, €244.35 — the costed bill of materials for the PhytoSense One board |
| `accessories.csv` | €103.90 of accessories, plus €304.30 recommended |

Those two files are the **source** of the printed tables:
`tools/gen_bom.py` produces the HTML fragments from them, and nothing is
copied by hand.

> `hardware/` is under **CERN-OHL-P v2**, not MIT (`C-53`). Writing "MIT" on
> a circuit drawing would be false, and one day somebody would act on it.
> `tools/headers.py` knows the rule and stamps the right licence according to
> the path.

---

## 8. The ten publications — `pdf-src/`

**1,385 pages**, produced by WeasyPrint from 227 HTML fragments and four CSS
house styles in *paged media*: a clickable table of contents, bookmarks,
running heads, pagination, a paginated index, metadata.

| Publication | Pages | Factory |
|---|---:|---|
| **La Musique des Plantes** | 478 | `build.py` |
| **L'Arbre qui Parle — Dublin** | 212 | `build_tree.py v1` |
| **Biocommunication végétale et IA** | 163 | `build_tree.py v2` |
| **Créer un arbre parlant** | 198 | `build_tree.py v3` |
| **Annexe — planches, BOM, programmes** | 65 | `build_appendix.py` |
| **La Carte PhytoSense** | 197 | `build_board.py` |
| **PhytoSense — schematics** | 12 | `build_board.py` |
| **PhytoSense — bill of materials** | 18 | `build_board.py` |
| **PhytoSense — printed circuit** | 7 | `build_board.py` |
| **Writing a module for PhytoScope** | 35 | `build_sdk.py` |

The titles above are the ones each volume carries today. Six of the ten are
still written in French; translating their editorial prose is the largest
piece of work left in the repository, and `.ai/state.md` measures it.

### Rebuilding

```bash
# The illustrations first: they are generated, never drawn (C-45)
python3 pdf-src/assets/svg/gen.py          # the book and the series
python3 pdf-src/assets/svg/gen_board.py    # the companion volume
python3 pdf-src/assets/svg/gen_sch.py      # the schematic plates
python3 pdf-src/assets/svg/gen_sdk.py      # the SDK guide
python3 pdf-src/assets/svg/gen_tt.py       # the "Talking Tree" series
python3 tools/verify_svg.py                # are they well-formed XML?

# The fragments produced from sources of truth
python3 tools/gen_bom.py                   # from hardware/*.csv
python3 tools/gen_code_annex.py            # from the real code files

# The publications
python3 pdf-src/build.py
python3 pdf-src/build_tree.py              # or "v1", "v2 v3"…
python3 pdf-src/build_appendix.py
python3 pdf-src/build_board.py
python3 pdf-src/build_sdk.py
```

### Rebuilding only what was touched

Remaking all ten publications takes a dozen minutes. Fixing a typo in the
companion volume has no reason to rebuild the 478-page book:

```bash
git diff --name-only | python3 tools/impacted_pdfs.py -
# → the commands to run, and nothing else
```

The tool is **deliberately cautious**: a path it cannot attribute triggers
everything. Being wrong by rebuilding too much costs minutes; being wrong by
rebuilding too little publishes a stale PDF, **and that does not show**. It
is what the CI uses.

### The defect that justified `tools/verify_svg.py`

An illustration that is not well-formed XML **does not break the build**:
WeasyPrint drops it, composes an empty frame, and the PDF comes out with the
right number of pages. Nobody notices before it is printed. It happened —
`timeline.svg` carried a bare `&` because its generator did not escape the
text. The generator was fixed, and all 104 illustrations are checked on every
CI run.

---

## 9. Building the packages — `packaging/`

**One Debian, Ubuntu or Mint machine produces the packages for every
system**, signed, with their checksums and their documentation.

```bash
cd packaging
make                # the target list — `help` is the default goal
make tools          # what is missing in order to package
make deps           # NSIS, msitools, osslsigncode — in ~/.local/opt, no sudo
make certificate    # once; idempotent thereafter
make all            # the nine packages, signed
make deliverables   # the packages AND the firmware, in one build
make verify         # reopens and checks everything produced
```

| System | Packages | Size |
|---|---|---|
| Debian / Ubuntu / Mint | `.deb` | 416 kB |
| Every distribution | `.run` *(interpreter bundled)* | 29 MB |
| Fedora / RHEL / Rocky | `.rpm` | 668 kB |
| Windows 10/11 | `.exe` · `.msi` · `-portable.zip` | 178 / 275 / 262 MB |
| macOS | `.pkg` · `-macOS.zip` | 18 / 19 MB |
| Source | `.tar.gz` | 656 kB |
| The board | `phytosense-1.6.0.uf2` | 84 kB |

The Windows packages carry the interpreter and Qt, hence their size; the
others rely on the system's Python, **except the `.run` and the `.pkg`, which
carry one** (a relocatable CPython) so as to be installable on a bare machine
without privileges.

Every package comes with its `.sha256` checksum, its signature (`.p7s`,
detached CMS; Authenticode for `.exe` and `.msi`), and six documents.

> **The full detail** — timings, sizes, options, troubleshooting — is in
> [`PACKAGING.md`](PACKAGING.md).

### Two warnings the project owns

1. **The certificate is self-signed.** It proves integrity and continuity of
   origin. It **silences neither SmartScreen nor Gatekeeper**, and has never
   claimed to (`C-2Q`).
2. **`make verify` does not *install* any package**: the machine that builds
   has no Windows, no macOS and no Fedora. What is verified is their
   structure and their internal consistency. The CI runs the tests on all
   three systems.

### No `sudo`, ever

Everything installs in the home directory (`C-55`) — including the packaging
tools, which `make deps` unpacks into `~/.local/opt`. Where rights really are
needed — the `.run`'s system libraries — they are asked for through `pkexec`,
`kdesu` or `gksu` on a desktop, through `sudo` in text mode, and **never
without saying so**.

---

## 10. Continuous integration and DevSecOps

Seven workflows, in `.github/workflows/`:

| Workflow | Trigger | What it does |
|---|---|---|
| **`packages.yml`** | `src/**`, `packaging/**` | static analysis of everything executable (ruff, shellcheck, Makefile, yamllint), then **one build per target system, in parallel**, the full signed chain, **the firmware**, and the tests on Linux, Windows and macOS × Python 3.10 and 3.12 |
| **`publications.yml`** | `pdf-src/**`, `hardware/**`, `tools/**` | remakes **only the PDFs affected**, checks that the illustrations are well-formed XML and that no publication has collapsed |
| **`security.yml`** | every push + weekly | gitleaks, our own guard on the private key, bandit (SARIF), pip-audit, trivy, a review of added dependencies, **licence consistency**, zizmor on the workflows themselves |
| **`codeql.yml`** | every push + weekly | semantic analysis of Python **and C** — it follows where a value goes, where bandit recognises patterns |
| **`sbom.yml`** | `src/phytoscope/**`, `src/firmware/**` | regenerates **both** bills of materials and commits them back on `main` |
| **`scorecard.yml`** | branch protection + weekly | an OpenSSF Scorecard reading of the repository's practices |
| **`release.yml`** | a `v*.*.*` tag | checks the tag **matches `VERSION`**, replays the tests, builds everything — packages, firmware, publications — **attests the provenance** (Sigstore), and publishes |

### What sets this CI apart from an ordinary one

- **Analysis comes before building.** A package built on a faulty script is a
  package that will have to be republished.
- **The provenance is attested.** Every published deliverable carries a
  Sigstore signature saying which repository, which commit and which workflow
  it came from:

  ```bash
  gh attestation verify phytoscope_1.6.0_all.deb --repo thierryg/phytoscope
  ```

  That complements the publisher's signature: the CI signs the
  **provenance**, the publisher signs the **origin**.
- **Two software bills of materials**, version-controlled and kept up to date
  automatically: the software's (shipped inside the packages) and the whole
  project's, **firmware included** — Pico SDK, TinyUSB, ARM toolchain. A
  false SBOM is worse than none.
- **The workflows are themselves analysed** (`zizmor`): a workflow asking for
  `contents: write` where `read` would do is an open door.
- **Third-party actions are pinned by commit fingerprint**, and their
  existence is checked on every push (`tools/verify_actions.py`). A tag
  moves; a fingerprint does not. And a dead reference does not make a step
  fail: it stops the job from starting, so a security check goes silent
  without a word — which happened with `trivy-action@0.28.0`, which is
  spelled `v0.28.0`. The check also verifies that **the version comment tells
  the truth**: `@abc123… # v2.6.2` could name anything, and a false comment
  is worse than none.
- **Licence consistency is a test.** The CI refuses to let our header
  reappear on third-party code, and checks that every copied project keeps
  its licence file.
- **`ruff` blocks on crashes, informs on style.** `E9`, `F82x` and `F811`
  fail the chain; the thousand style warnings inherited from code written for
  Python 3.9 are counted without blocking. The intent is declared in
  `pyproject.toml`, with its reasoning.

### Local guards

```bash
python3 -m pip install --user pre-commit && pre-commit install
pre-commit run --all-files

# Do the CI's actions exist, and are the third-party ones pinned?
# Through `git ls-remote`: no API quota, no token. With no network, the tool
# says so and does not fail.
python3 tools/verify_actions.py --epingle
```

`.pre-commit-config.yaml` adds three project-specific checks to the usual
hooks: **the private key refused on its name alone** (even empty, even
renamed), the **attribution headers up to date**, and the **illustrations
well formed**.

---

## 11. Security and secrets

The full policy is in [`SECURITY.md`](SECURITY.md) — **do not open a public
issue for a vulnerability.**

The secret that matters here is the **private key that signs the packages**:

- its reference copy lives in `~/.local/share/phytoscope-signature/`;
- `certificate/phytoscope.key` is a working copy, **excluded by
  `.gitignore`** (`C-2R`);
- the **public** certificate (`certificate/phytoscope-certificate.pem`,
  `certificate/phytoscope.crt`) **is** version-controlled: it is what lets
  anyone verify a signature, and it is meant to be distributed.

**Three nets**, because a published key cannot be unpublished: `.gitignore`
excludes it by name and then broadly, the `pre-commit` hook refuses it **on
its name alone**, and the CI's "secrets" job fails if it appears.

```bash
# What git tracks that looks like a key — only the public one should appear
git ls-files | grep -Ei '\.(key|pem|p12|pfx|jks|keystore)$'

# The certificate's state, and whether the two copies agree
cd packaging && make certificate-status && make certificate-verify
```

> `.gitignore` protects against `git`, **not against a backup or an archive of
> the directory**. See `certificate/README.md`.

**The `.gitignore` is tested.** Twenty-one tests check each of its rules and
each of its exceptions. The reason is a real incident: the whole section that
excludes the copyrighted documents disappeared during a rewrite, and 6,449
files ended up in the index. Nothing had been pushed, but a `.gitignore` is
code: it is tested.

---

## 12. What the repository does not contain, and why

The repository is **public**. Some files stay on the disk but are kept out by
`.gitignore` (490 commented lines):

| What | Why |
|---|---|
| `certificate/phytoscope.key` | The private signing key (`C-2R`). |
| `sources/ebooks/`, `sources/brevets/*.pdf`, `sources/datasheets/*.pdf`, `sources/manufacturer-manuals/*.pdf`, `sources/documents/scientific-articles/*.pdf` | **We have no right to redistribute them.** Their bibliographic references are in `sources/INDEX.md`, and our reading notes (`.md`) are version-controlled. |
| `sources/documents/public-domain/*.pdf` | Here it is **not** a question of rights — Bose and Darwin are free. It is the weight: 258 MB of scans, in a repository that weighs 162 MB without them. The **transcriptions** stay version-controlled, and a `README.md` gives the command for downloading them again from archive.org. |
| `sources/code/*.zip`, `sources/software/**/*.zip` | 817 MB of third-party repositories. `python3 tools/fetch-software.py` fetches them from source; `sources/software/MANIFESTE.md` keeps provenance and licences. |
| `build/` | The PDFs, packages and `.uf2` produced — they rebuild themselves. |
| `.venv/`, `__pycache__/` | Regenerable. |

The `.gitignore` covers **bash, Python, Go, Rust, C/C++, Windows 10/11,
macOS/Darwin, Debian/Ubuntu/Mint and Fedora/RHEL**.

---

## 13. Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md), then, **in this order**:

1. [`AGENTS.md`](AGENTS.md) — the way in;
2. [`constraints.md`](constraints.md) — **82 numbered constraints**,
   `C-1`…`C-64`. They are authoritative: a contribution that contradicts one
   is refused, or the constraint changes first;
3. [`.ai/state.md`](.ai/state.md) — where the work stands;
4. [`.ai/decisions.md`](.ai/decisions.md) — the design decisions **and their
   reasons**. A great many "why not do it like this?" already have their
   answer there.

### The five rules that cost dearly when forgotten

1. **Technical US English everywhere** — code, comments, docstrings,
   documents, commit messages. The interface is the exception: it follows the
   language the user chose.
2. **Explain the why.** A comment that paraphrases the code is to be deleted;
   a comment that says *why* the code is as it is, is to be kept.
3. **Verify, do not assume.** Every figure — pages, tests, references,
   prices, throughput — **is measured by a command** before being written.
4. **Never edit a generated file** (`C-45`). Edit the source and run the
   generator again.
5. **Test before concluding**: `cd src/phytoscope && make test`.

See also [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

## 14. The project in figures

All measured on 2026-09-23, by the repository's own commands.

| | |
|---|---:|
| Python modules in the software | 70 |
| Lines of Python (software) | 23,984 |
| **Tests, no hardware and no network** | **385** |
| C files in the firmware | 7 (1,906 lines) |
| Module contract | API **3.0** |
| Interface **and installer** languages | 11 |
| Speech-mode lexicons | 11 |
| Installer translations | 1,144 (104 × 11) |
| Modules shipped with the software | 4 |
| PDF publications | 10 (**1,385 pages**) |
| Reference documents | 2 (MIDI 22 pp., USB 24 pp.) |
| Publishing HTML fragments | 227 |
| Generated illustrations | 104 (0 malformed) |
| Photographs and plates | 234 |
| Bill-of-materials references | 68 (€244.35) |
| Constraints in the requirements | 82 |
| Packages produced by `make all` | 9, all signed; 10 with the firmware |
| Continuous-integration workflows | 7 |

---

## Licences

| What is covered | Licence | SPDX |
|---|---|---|
| Software, firmware, kit, tools, factories | **MIT** | `MIT` |
| Hardware — boards, schematics, bills of materials (`hardware/`) | **CERN-OHL-P v2** | `CERN-OHL-P-2.0` |

The detail, the exceptions and the third-party work:
[`LICENSES/README.md`](LICENSES/README.md).

The `Cinzel` and `Cormorant Garamond` fonts are under the SIL Open Font
Licence 1.1. The origin and licence of every photograph are in
`pdf-src/assets/img/photos/CREDITS.md`.

---

© 2026 Bretagne Namasté — Thierry GAYET
[bretagne-namaste.com](https://bretagne-namaste.com) ·
contact@bretagne-namaste.com
