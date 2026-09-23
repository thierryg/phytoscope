# State of the work

**As of 2026-09-23 (1.6.0).** This file says where the work stands: what holds
up, what is under way, what is waiting. It is updated **at every
intervention**, together with `.ai/journal.md`.

Every figure here was measured, not remembered. Where a number could not be
checked, the text says so.

## What holds up

| Part | State | Where |
|---|---|---|
| Main book | 478 p. — built | `build/La-Musique-des-Plantes.pdf` |
| Companion volume + 3 fascicles | 197 + 12 + 18 + 7 p. — built | `build/La-Carte-PhytoSense.pdf` |
| PhytoScope software | **1.6.0**, 391 tests passing | `src/phytoscope/` |
| Translations | 11 languages — English the source, 10 catalogues — 932 labels, 100 % coverage | `src/phytoscope/tools/i18n.py --couverture` |
| Samples and playback | `Ctrl+E` capture, playback in the engine | `core/samples.py` |
| Voice-mode dictionaries | 11, one per language | `phytoscope/lexicons/` |
| RP2350 firmware | builds — `phytosense.uf2`, 80 kB, 44,784 B of code | `src/firmware/build.sh` |
| Disk-space watch | measures, warns, closes cleanly | `core/disk_space.py` |
| VU meters | four dials with proper ballistics | `widgets.VuMetre` |
| Measurement fingerprint | eight descriptors plus a rig registry | `core/fingerprint.py` |
| Scientific quantities | fifteen, including equivalent resistance (an upper bound) | `core/quantities.py` |
| Log window | live, path, copy, `Ctrl+L` | `ui/log_window.py` |
| Portability | 13 points found, 13 fixed | `.ai/portability.md` |
| Installation packages | .deb, .rpm, .run, .exe, .msi, .pkg, .zip, .tar.gz | `packaging/Makefile` |
| Signing | self-signed X.509, Authenticode + CMS | `packaging/signature.py` |
| Attribution | one source, read by everything | `phytoscope/AUTHORS` |
| Version | one source, read by everything; **no code name** | `phytoscope/VERSION` |
| Module API | contract **3.0**, English, five capabilities, an isolating registry | `phytoscope/api/` |
| Built-in modules | four, through the same API as anyone else | `phytoscope/modules/` |
| SDK | eight chapters, one example, a module generator — all in English | `src/sdk/` |
| **"The Talking Tree" series** | 3 volumes, 573 p. | `pdf-src/build_tree.py` |
| **Series technical appendix** | 65 p. — built | `pdf-src/build_appendix.py` |
| **Printed SDK guide** | 35 p. — built | `pdf-src/build_sdk.py` |
| **Ten publications** | **1,385 pages**, one source directory per PDF | `pdf-src/` |
| **Reference documents** | MIDI 22 p., USB 24 p. | `sources/build_references.py` |
| **Public git repository** | tidy tree, `.gitignore` in 485 lines | `phytoscope/` |
| **Continuous integration** | 7 workflows — analysis, packages, PDFs, security, CodeQL, distribution, SBOM | `.github/workflows/` |
| **Illustration check** | 104 SVG, 0 malformed | `tools/verify_svg.py` |
| **Selective rebuild** | rebuilds only the PDFs actually affected | `tools/impacted_pdfs.py` |
| **Licence consistency** | MIT + CERN-OHL-P v2, third-party code left under its own | `LICENSES/README.md` |
| **Library updates** | from the interface, installing nothing by default | `ui/updates_dialog.py` |
| **Language at install time** | 11 languages, asked first, taken up by the software | `packaging/templates/` |
| **Installer labels** | 104 × 11 = 1,144 translations, one source | `packaging/languages/installateur.json` |
| **Bundled interpreter** | `.run` 28 MB, `.pkg` 18 MB — installs on a bare machine | `common._python_autonome` |
| **Bytecode cache** | built at install time on all five targets | `INSTALL.md` |
| **Tests** | **391 passing, 0 skipped** | `make test` |
| Developer companion volume | 35 p. — built | `build/writing-a-phytoscope-module.pdf` |
| Attribution headers | 309 files, idempotent tool | `tools/headers.py` |

## The translation into technical US English

Started on 2026-09-22, when the French-only rule was repealed. What is
**finished**, and verified rather than asserted:

| Part | Proof |
|---|---|
| RP2350 firmware — code, scripts, README | `arm-none-eabi-size` gives 44,792 / 106,508 bytes **before and after** the 550 identifier renames: byte for byte identical |
| Installer templates — 9 shell scripts | 94 hardcoded strings → 0; `.deb` unpacked and the launcher exercised in 6 languages; `.run` installed end to end in Italian, Russian and French |
| Installer label catalogue | 104 labels × 11 languages, 0 leak, 0 dead label (`tools/verify_installer_i18n.py`) |
| Hardware bill of materials | `hardware/*.csv`: English column names, 184 texts, decimal points; totals unchanged at 244.35 € / 103.90 € / 304.30 € |
| `gen_board.py` — 36 figures | 700 literals and 88 comments; pagination unchanged |
| Three PhytoSense fascicles | `pdftotext` finds **zero** French in all three |
| MIDI and USB reference documents | written natively in English |
| 106 photographs | renamed in both directories, 198 references updated, 491 image references resolve |
| SDK — 8 chapters, the example, the generator, the printed guide | 0 French left but 5 argparse aliases; 385 tests, of which 26 read the generator or the `__all__` lists; `writing-a-phytoscope-module.pdf` 35 p. |
| **The public module API, renamed to English — `API_VERSION` 2.0 → 3.0** | 195 identifiers, 3,000 occurrences over 35 files; 932 translatable labels migrated in the ten catalogues; 385 tests pass, and a 2.0 manifest is refused at discovery (`D-24`). The version contract is now readable from both sides: `context.api_version` / `api_at_least()` for the module, `manifest.api_required` / `registry.api_requirements()` for the host |
| `build/packages/` and its `latest` link | was `build/paquets/` and `dernier`; `PHYTOSCOPE_OUTPUT` replaces `PHYTOSCOPE_SORTIE`, `SORTIE=` still honoured |
| **The root documents** | 5,464 markers → 41, and those 41 are the French titles of the six untranslated volumes. Five constraints were false and are corrected; every figure measured again |
| **`.github/` — all seven workflows and every template** | 1,616 markers → 26; `paquets.yml` → `packages.yml`, `securite.yml` → `security.yml`, `diffusion.yml` → `release.yml`, `anomalie.yml` → `bug.yml`, `evolution.yml` → `enhancement.yml`, and every reference with them. `CODEOWNERS` had a rule on a directory that has never existed |
| **The CI built nothing at all since 2026-09-22** | `packages.yml`'s lint job checked for thirteen Makefile targets by name; six had been renamed. It failed on the first, and `lint` gates every other job. The list is now read from the Makefile's own `.PHONY` |
| **Three defects in `packaging/Makefile`** | a bare `make` died on a target that no longer existed; `make verify` **created** an empty build and repointed `latest` at it; `make deliverables` produced a build `make verify` refused. Six tests, each mutation-checked |
| **`release.py` mangled the changelog it maintains** | it split the 80-character banner at 78, inserted the new section above the file's own header and left two orphan `=`. Four tests |
| Version **1.6.0** | bumped with the project's own tool, 309 attribution headers restamped, and one complete fabrication rebuilt at that version — 10 deliverables, 9 signatures, 11 checksums, `make verify` clean |
| **The three USB divergences** | all closed. §11.1 the clock answers 250 Hz; §11.2 the packet is 384 = 32 × 12, with a static assert on divisibility; §11.3 the audio function is written out by hand and the feature unit declares `AUDIO_CTRL_NONE` — verified on the compiled bytes: 219 o, `wMaxPacketSize = 384`, `bmaControls` all zero |
| Makefile targets | the 16 French ones renamed; all 48 targets dry-run, `packaging/build.py` repaired |
| `.ai/` — state, journal, decisions, portability | translated and brought up to date |

### What remains, measured on 2026-09-23

A "marker" is one occurrence of an unambiguously French stopword or of an
accented letter French uses and English does not. It over-counts a little
(a code identifier counts once per use) and it is the same measure from one
day to the next, which is what makes it useful.

| markers | files | area |
|---:|---:|---|
| 62,429 | 206 | **the 6 untranslated publications** (below) |
| 15,604 | 93 | `src/phytoscope/` — comments, docstrings, `CHANGELOG.txt`, `README.txt` |
| 6,947 | 33 | `sources/` — **our own notes only**; the quoted sources are not to be touched |
| 6,000 | 16 | `tools/` — `gen-appendix-parts.py` and `gen_glossary.py` are two thirds of it |
| 5,698 | 18 | `packaging/` — `common.py`, `signature.py`, `certificate.py`, `README.md` |
| 5,464 | 12 | the root documents — `README.md`, `INSTALL.md`, `CHANGELOG.md`, `PACKAGING.md`, `constraints.md`… |
| 2,902 | 66 | `pdf-src/assets/` — 1,606 in `gen_tt.py` (988), `gen_sch.py` (311) and `gen.py` (261); 1,270 in the figures they draw |
| 1,616 | 12 | `.github/` — 5 workflows and 2 issue templates |
| 626 | 8 | `pdf-src/` builders and style sheets |
| 278 | 14 | the last pockets: `certificate/README.md`, `LICENSES/README.md`, `.ai/` residue, firmware |
| **107,567** | **479** | **total** |

The total did not move on 2026-09-23 evening, and that is expected: the API
rename replaced French **identifiers**, which this measure barely sees, while
the two `CHANGELOG` entries written the same evening are in French because
both changelogs still are. The identifier count below is where that work
shows.

The six publications, in the order their size suggests:

| markers | fragments | volume |
|---:|---:|---|
| 23,540 | 46 | `the-music-of-plants/` — the main book, 478 p. |
| 10,735 | 34 | `talking-tree-dublin/` |
| 9,812 | 41 | `the-phytosense-board/` |
| 8,475 | 39 | `workshop-build-a-talking-tree/` |
| 7,284 | 32 | `plant-biocommunication-and-ai/` |
| 2,580 | 13 | `talking-tree-appendix/` |

The three PhytoSense fascicles and the SDK guide are done: `pdftotext` finds
no French in them.

Not counted, because it is not work: **59,522** markers in the generated
documents (`pdf-src/_book*.html`, `_carte-*.html` — `C-45`: they are rebuilt
from the fragments) and **2,755** in the translation catalogues, whose whole
job is to hold another language.

Separately, the **French Python identifiers**, which the marker count barely
sees:

| occurrences | distinct names | area |
|---:|---:|---|
| 1,100 | 377 | `src/phytoscope/` — was 1,544 before the API pass |
| 399 | 144 | `packaging/` |
| 239 | 71 | `tools/` |
| 80 | 37 | `pdf-src/` |
| 0 | 0 | `src/sdk/` and `phytoscope/api/` — **done** (`D-24`) |

`phytoscope/api/` is now entirely English, and so are `core/quantities.py`,
`core/fingerprint.py`, `core/features.py`, the four built-in modules and the
five UI files that consume the contract: those had to move with it, because
the unit of a rename is a vocabulary, not a file.

And **40 French file or directory names**, of which 30 are the board figures
(`pdf-src/assets/svg/carte-*.svg`, renamed by `gen_board.py`), 5 are
`.github/` workflows and templates, and the rest are
`packaging/languages/installateur.json`, `packaging/signature.py`,
`src/phytoscope/requirements-optionnel.txt`, `sources/brevets/` and four
`sources/0*.md` notes.

See `.ai/journal.md` for the day-by-day record.

## Under way — do not start over

**The module work is half consumed, and it is the only one in that state.**
The API, the registry, the four built-in modules, the SDK and its companion
volume are delivered and exercised; but of the contract's five capabilities,
**the host calls only two**:

| Capability | Consumed by the host? | Where it should appear |
|---|---|---|
| `analyseur` | yes | Multimeter → Scientific quantities (`ui/tabs.py`) |
| `descripteur` | yes | Descriptors tab (`ui/features_tab.py`) |
| `exportateur` | **no** | Library — `ui/library_tab.py` does not query the registry |
| `sonificateur` | **no** | Listen — nothing in `music/` consults the registry |
| `source` | **no** | the acquisition sources, in `core/sources.py` |

The visible consequence: the built-in `export-csv` module is loaded, active,
and useless — no screen offers its format.

Since 2026-09-23 the SDK **says so** rather than promising five: the table in
`src/sdk/docs/03-capabilities.md` carries a "Called today?" column, the note in
`01-getting-started.md` sends the reader to the two that work, the printed
guide repeats it, and `new_module.py` prints a warning when the capability
asked for is one of the three nothing calls. `CONSUMED`, in that tool, is the
one place the list is written down, and
`test_it_knows_which_capabilities_the_host_really_calls` reads the `ui/` calls
and fails the day the two lists disagree — naming every file to update.

Wiring up the other three is still the work to be done; the documentation no
longer costs anybody an evening in the meantime.

Portability is settled — the thirteen points in `.ai/portability.md` are fixed
— and the package factory works for all five targets.

## Waiting

- ⬜ **The seven languages asked for on 2026-09-22 are not shipped.** `i18n`
  declares 41 languages and **11 have a catalogue**; `de`, `hi`, `nl`, `pl`,
  `tr`, `vi` and `el` have none. That is 932 × 7 = 6,524 software translations
  plus 104 × 7 = 728 installer ones. German was reportedly at 394/932 at some
  point; that work was not found and is probably to be redone.
- ⬜ **The Python identifiers of `packaging/` and `src/phytoscope/` are still
  French** (`dire`, `etape`, `Identite`, `dossier_sortie`…).
  `.ai/rename-plan.json` keeps a `_deferred-to-the-publications-pass` entry.
- ⬜ **Synchronous overlay** (the honest "eye"): see `D-10`. Not started,
  awaiting a decision — three possible forms, only the first of which is
  software: a triggered overlay of the plant signal, an eye in the proper sense
  on an NE555 rig, a method plate for the digital isolator.
- ⬜ **Review of the ten translations by native speakers** — Russian, Chinese,
  Japanese, Korean and Arabic above all. The mechanism makes a correction
  trivial: a text editor, no recompilation.
- ⬜ **Voice-mode dictionaries**: the eleven shipped are starting points
  written in one pass; they would gain from a practitioner's reading.
- ⬜ **Long sessions**: automatic splitting (`split_hours`) is declared in the
  settings but not yet applied by the recorder.
- ⬜ **Rhythmic quantisation**, chorus and spatial effect: present in the
  settings, not yet applied by the renderer.
- ⬜ **Trials on real Windows and macOS hardware**: the portability fixes are
  verified by reading the code and by 17 automated tests, but **none has run on
  a real Windows machine or a Mac**. This is the one debt left on that front,
  and it is real.
- ⬜ **Package signing**: neither Windows nor macOS is signed — a paid
  certificate on one side, an Apple developer account and a Mac on the other.
  The packages explain how to get past it (`D-15`).
- ⬜ **The `.pkg` has never been given to `installer(8)`**: the format is
  written by hand and reviewed by us, but only a Mac can confirm it installs.
  Likewise the `.msi` and `msiexec` (`D-19`, `D-20`).
- ⬜ **The NSIS installer could not be tried under Wine**: it is a 32-bit
  executable — normal for NSIS — and this machine has only 64-bit Wine.
  `sudo apt install wine32` would allow the trial.
- ⬜ **NumPy does not import under Wine 6.0.3** (`fetestexcept` unimplemented
  in Wine's MSVC runtime). A gap in Wine, not in the package: the rest of the
  payload — Python 3.11.9, PySide6, pyserial, sounddevice — works, and
  `run.py --version` runs. A newer Wine would settle it.
- ⬜ **The `.run` in graphical mode has not been tried**: it would open zenity
  windows on the user's screen. Text and unattended modes, on the other hand,
  are exercised end to end (installation, registry, `--uninstall`).
- ⬜ **The module work has no `CHANGELOG.txt` entry, no constraint in
  `constraints.md`, and no line in `CHANGELOG.md`**: the code and the SDK are
  there, the documentary trace is missing. The journal entry of 2026-09-18
  (night, end) inventories it.
- ⬜ **Companion-volume update**: the "Scientific quantities" page, the log
  window and the installation packages are not yet in the manual; the PDF is
  therefore two versions behind the software.

## Known traps

- A toolbar that grows **hides its last actions** behind a chevron, without
  warning: whatever must stay reachable goes in the menu bar (incident of
  2026-09-18).
- **Never** run the software against `~/.config/phytoscope/` during a test
  (incident of 2026-09-18): `XDG_CONFIG_HOME=/tmp/…`, always.
- The audio output does not tolerate being opened twice:
  `AudioOutput.start()` is now idempotent — do not remove that guard, a
  SIGSEGV depends on it.
- The ALSA output complains loudly when stopped in off-screen mode; harmless,
  it is PortAudio's teardown.
- A label that **embeds a number** ("Allan deviation at 1 s") cannot go into a
  translation catalogue: write a template ("at {tau} s") and compose **after**
  `t()`, never before.
- A measured value's column must carry **unit symbols only** — those are
  international. An "above the floor" stuck behind a figure stays in one
  language across the other ten interfaces; a test watches for it.
- `tests/conftest.py` redirects XDG_CONFIG_HOME, XDG_DATA_HOME and APPDATA: do
  not work around it, that is what protects the user's configuration.
- **`pip download --no-deps` empties a package of its substance**: `PySide6` is
  a wheel of a few kilobytes; Qt's 400 MB are in its dependencies. The Windows
  package came to 27 MB and would not have started.
- **A NumPy wheel is good for one minor version of Python only.** The Linux
  and macOS packages therefore carry wheels for 3.9 to 3.13; Qt escapes this,
  its wheels being `abi3`.
- An interface label must **never** depend on the platform: the set of keys to
  translate would vary from one system to another, and a single catalogue could
  no longer serve them all. Make the text conditional, not the entry's
  existence.
- A tool that writes a **transformed** text must recognise it in its
  transformed form. `tools/headers.py` writes `.bat` headers without accents
  but looked for its marker **with** its em dash: it never found it and stacked
  one header per run (2026-09-18).
- Removing a comment block must take its **delimiters** with it (`<!--`,
  `-->`, `*/`): without them, every pass left one more empty comment in the
  repository's 67 XML files.
- A version's **code name** is optional and empty since 1.6.0. Whoever wants to
  display it asks for `version.TITRE_VERSION` (software) or `Identite.titre`
  (factory) — never `f"{VERSION} « {RELEASE_NAME} »"`, which yields an empty
  pair of quotes when the name is missing.
- **`${VAR:-default}` in shell is a trap for a default that carries an
  apostrophe or a brace.** The apostrophe opens a single-quoted string that
  swallows the rest of the file; the brace closes the expansion early. Neither
  is reported by `dash -n`, and `bash -n` blames a sound line dozens of lines
  further down. Use `tl NAME "default" [field value …]`, which takes the name
  as a plain word (found 2026-09-23 in `header.sh`, where it had been latent).
- **`printf "%-18s"` counts bytes, not characters.** A column that lines up in
  English is one short per accent in French. `colonne()` in `header.sh` pads by
  character count instead.
- **`ast`'s `col_offset` is a UTF-8 byte offset.** Any tool that rewrites
  literals by position must work on bytes; treating them as characters drifts
  on exactly the accented lines a translation pass is aimed at.

## Waiting for a decision

- **`AUTHORS` contains a personal telephone number.** The repository is public
  and that file goes into every package. The code reads the field with an empty
  default (`version.py:114`, `packaging/common.py:290`): clearing it has no
  technical consequence. Still not decided.
- **The first `git push`.** The local repository is ready and the remote is
  `git@github.com:thierryg/phytoscope.git`, but nothing has been pushed:
  publishing is irreversible, and that is a decision.
- **Commit signing.** `commit.gpgsign` is true and the only secret key carries
  the UID `tgayet@tixeo.com`, while the repository is configured to commit as
  `thierry.gayet@gmail.com` (set 2026-09-23). Commits will be signed and shown
  as **Unverified** by GitHub. Three ways out: add a UID to the key and
  re-upload it, disable signing for this repository, or accept the label.
- **`.ecarte/` weighs 857 MB** (the old virtual environment, mostly, plus
  duplicates and a stale firmware CMake cache). Removable without consequence
  — left in place because the instruction was to lose nothing.
