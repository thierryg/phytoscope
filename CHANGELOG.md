# Changelog — the *Music of Plants* project

This file follows **the whole project**: the book, the companion volume, the
board, the firmware and the software. The detail of the software's versions
lives in `src/phytoscope/CHANGELOG.txt`, which is finer-grained; this one
gives the overall view.

"Keep a Changelog" format. The dates are those on which the documents were
built, verified after rebuilding (`C-64`).

Where an entry below names a file that has since been renamed, it is written
with the name the file carries **today** — that is the name a reader can act
on. The entry still says what happened, and when.

---

## 2026-09-23 — the module interface turns to English (API 3.0)

### Changed — BREAKING
- **`API_VERSION`: 2.0 → 3.0.** The whole public surface of the module
  contract is renamed to English — 195 identifiers, from `Manifeste`→`Manifest`
  to `installer()`→`setup()`. A module written for 2.0 is **refused at
  discovery**, with a readable sentence in Diagnostics, and not loaded
  halfway: nothing is aliased, and that is exactly what a major number is
  for.
- The states displayed (`actif`, `en_faute`, `desactive`) and the capability
  values (`analyseur`…) turn to English with it.
- **Migration**: `src/sdk/docs/08-migrating-from-2.0.md`, and chapter 6 of the
  printed guide. Three steps, and nothing else to do.
- The **version contract can now be read from both sides**: a module asks
  `context.api_version` and `context.api_at_least("3.2")`; the host asks
  `manifest.api_required` and `registry.api_requirements()`. `Manifest.api`
  has always been a **minimum** — now it says so, and both sides go through
  the same parser.

### Added
- **The SDK is finished**: the eight chapters, the complete example, the
  generator and the printed guide (35 pp.) are in technical US English. The
  generator warns when the capability asked for is one nobody calls.
- **The firmware answers the UAC2 clock**: `tud_audio_get_req_entity_cb` and
  its write counterpart report **250 Hz**, the real rate, with a
  single-value range. A host that refuses a rate below 8 kHz refuses plainly —
  which is worth more than a wrong timestamp for months.
- **The audio function is written out by hand**, thirteen descriptors instead
  of TinyUSB's microphone template, so that the feature unit stops declaring a
  mute and a volume the board has not got. The isochronous packet goes from
  256 to **384 bytes** = 32 × 12 exactly, which is the 32 kHz mode the old
  comment claimed and did not deliver. All three divergences recorded in
  section 11 of the USB reference are settled.

### Fixed
- **`make` with no argument was broken** in `packaging/` since 2026-09-22:
  `.DEFAULT_GOAL` named an `aide` target that no longer existed — the one
  invocation a newcomer types first.
- **Four `__all__` lists** named classes that did not exist, residue of a
  rename that stopped halfway. A test now compares them all, module by
  module, and found the fourth one itself.
- `new_module.py` read `VERSION_API` from a directory that has never existed,
  and fell back silently; it also printed a literal `{nom_essais}`.
- `build/paquets/` becomes `build/packages/`, and the `dernier` link becomes
  `latest`. `PHYTOSCOPE_OUTPUT` replaces `PHYTOSCOPE_SORTIE`; `SORTIE=` is
  still honoured.
- `.ecarte/` deleted — 857 MB of an obsolete virtual environment, exact
  duplicates and a dead CMake cache.

---

## 2026-09-22 — the repository turns to technical US English

### Changed
- **English becomes the source language**, and French a catalogue like any
  other. The translation keys are the English sentences themselves;
  `LANGUE_SOURCE = "en"`; `en.json` was deleted, because a source language
  has no catalogue to keep up to date, and `fr.json` was created.
- Comments, docstrings, file names, directory names, Makefile targets,
  package metadata and the `.ai/` agent memory are written natively in
  English. Whatever is **not** exposed to an end user is in English without
  exception; whatever is exposed follows the language the user chose at
  installation.
- The event wire names were renamed from French — `mesure.demarree` →
  `measurement.started`, and nine others — which is what took `API_VERSION`
  from 1.0 to 2.0.

### Added
- `tools/verify_translation.py` — an AST fingerprint per file (code shape with
  docstrings stripped and literals blanked, plus the literals themselves), so
  that a prose translation can be **proved** to have moved no code.
- `tools/verify_installer_i18n.py` — the same office for the shell scripts,
  where there is no syntax tree to lean on: it finds leaks, dangerous
  `${T_…:-…}` defaults, missing labels, and fields that disagree across the
  eleven languages.

---

## 2026-09-18 (night) — library updates, and the language in eleven voices

### Added
- **"Help → Library updates…"** — the software compares the installed Python
  libraries with what the package index publishes, sorts the differences into
  *patch*, *minor* and *major*, and **installs nothing without being asked
  explicitly**. The query runs on a separate thread and `pip`'s output
  scrolls line by line. No dependency was added for it (`C-40`).
- **The language is asked at the very start of the installation**, in the
  **software's eleven languages**, each offered in its own script. It is
  written into `reglages.json` and taken up by PhytoScope: the question never
  comes back.
  - `.run`: the first question, before the licence — which is therefore read
    in the chosen language. `--language ja` for an unattended installation;
  - `.exe`: an NSIS box, **eleven languages compiled in** instead of two, the
    choice remembered under `HKCU`;
  - macOS `.pkg`: a list at first opening;
  - `.deb` and `.rpm`: `apt` and `dnf` do not ask — the question comes at the
    **software's first start-up**.
- **51 installer labels × 11 languages = 561 translations**, from a single
  source (`packaging/languages/installateur.json`), from which the `.run`'s
  shell catalogues and NSIS's `LangString`s are generated.
- **Privilege elevation through `pkexec`, `kdesu` or `gksu`** when the
  installer comes from a desktop — an authentication window is the only
  correct thing then — and through `sudo` in text mode.
- **An ASCII banner** and a **checklist** displayed at launch by default,
  with the pre-flight checks dependency by dependency.
- `INSTALL.md` — what each installer does, step by step, system by system.
- Automatic regeneration of the **software bill of materials** as soon as a
  change touches `src/phytoscope/` (`.github/workflows/sbom.yml`).

### Fixed
- **A pre-release passed for newer than its own version.** In the new
  comparator, gathering every number out of "3.0.0rc1" gives `(3, 0, 0, 1)`,
  which compares after `(3, 0, 0)`. The order now covers
  `dev < alpha < beta < rc < (nothing) < post`.
- **Two tests had been checking nothing since the repository was tidied.**
  `test_le_sdk_livre_un_exemple_qui_se_charge` and
  `test_les_identifiants_usb_suivent_le_micrologiciel` were looking for the
  SDK and the firmware at their old locations, and **skipping themselves
  silently**. The paths were fixed; they pass.
- The **banner existed twice** in `__main__.py`, and its first rule had lost
  a character. One source now, `core/console.banniere()`, which also carries
  the version.
- "start-up report" becomes "**checklist**", everywhere.

### Changed
- **`ruff` in continuous integration**: blocking on crashes (`E9`, `F82x`,
  `F811`), informative on the thousand style warnings inherited from code
  written for Python 3.9. The intent is declared in `pyproject.toml`, with
  its reasoning. The previous configuration would have failed the chain on
  the first push.

### Verified
- **306 tests green, 0 skipped**; essential `ruff`: *All checks passed*;
- **11 languages at 100 %** (888 labels) and 561 installer translations, with
  the substitution fields preserved;
- `.run --language ja` prints `[ok] 言語：日本語` — the Japanese catalogue is
  indeed loaded.

---

## 2026-09-18 (end of day) — the "Talking Tree" series, and a public repository

### Added
- **The "Talking Tree" series**, merged into the project: three volumes and a
  technical appendix, **638 pages**, built by `pdf-src/build_tree.py` and
  `pdf-src/build_appendix.py` from their own style sheet
  `pdf-src/tree.css`.
  - *Dublin — a scientific examination* (212 pp.) — the investigation into
    the "talking trees";
  - *Plant biocommunication and artificial intelligence* (163 pp.) — the
    treatise;
  - *Building a talking tree* (198 pp.) — the workshop manual;
  - *Appendix — plates, bill of materials, programs* (65 pp.).
- **234 photographs and plates**, with their credits
  (`pdf-src/assets/img/photos/CREDITS.md`), and 44 new illustrations.
- **Four sourced research notes** (`sources/01-…` to `04-…`).
- `tools/verify_svg.py` — checks that the 104 illustrations are well-formed
  XML. A malformed illustration does not break the build: WeasyPrint drops it
  and composes an empty frame, without a word.
- `tools/impacted_pdfs.py` — says which publications to remake given the
  files that changed. Remaking all ten costs a dozen minutes.
- **A public git repository**: `LICENSE` (MIT) and
  `LICENSES/CERN-OHL-P-2.0.txt` with the official SPDX texts, `SECURITY.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `AUTHORS`, `.editorconfig`,
  `.gitattributes`, `.pre-commit-config.yaml`, issue templates, `CODEOWNERS`.
- **Six continuous-integration workflows**: static analysis then a package
  build per system (`packages.yml`), rebuilding only the publications affected
  (`publications.yml`), seven security checks (`security.yml`), CodeQL on
  Python **and** C, OpenSSF Scorecard, and a release chain that **attests the
  provenance** of the packages (Sigstore) after checking that the tag matches
  `VERSION`.

### Fixed
- **The illustrations did not escape the text they were given.**
  `pdf-src/assets/svg/gen.py` had lost its `esc()` function: `timeline.svg`
  contained two bare `&` and was the **only malformed SVG of 104**. The
  corresponding frame was empty in the book, with nothing to say so.
- **A false licence statement on 32 third-party files.** `tools/headers.py`
  had stamped "© Bretagne Namasté" and "SPDX-License-Identifier: MIT" on
  LEDFader (MIT © Jeremy Gillick), MIDI Sprout
  (MIT © electricityforprogress) and the **Biotron firmware, which is
  GPL-3.0**. The headers were removed, the original headers left intact,
  `sources/` excluded from the tool, and a CI job now refuses to let it come
  back. The code appendix also announced Biotron as "MIT": corrected to
  GPL-3.0.
- **The `.deb` had disappeared from the build.** The attribution header had
  been stamped onto `packaging/templates/debian/control`, and **a `control`
  file admits no comment**: `dpkg-deb` refused the package, but `make all`
  carried on and produced the other seven. `"control"` went into
  `tools/headers.py`'s exclusions.
- The figures in `sources/INDEX.md` were stale (76 files announced, 248 real):
  measured again.

### Changed
- **The repository is arranged by what the files are, not by when they
  arrived.** Code under `src/` (`phytoscope/`, `firmware/`, `sdk/`), the
  publishing sources under `pdf-src/` with **one directory per publication**,
  and `sources/` reserved for reference material — things we did not write.
  `hardware/` left `sources/`: it is our hardware, under CERN-OHL-P v2.
- `.gitignore` rewritten — **459 commented lines**, covering bash, Python,
  Go, Rust, C/C++, Windows 10/11, macOS/Darwin, Debian/Ubuntu/Mint and
  Fedora/RHEL, organised into three families: the secrets, what we have no
  right to redistribute, what rebuilds itself.
- The public-domain scans (Bose, Darwin — 258 MB) leave the repository: they
  are free of rights, but a 415 MB clone for books anybody can download again
  in one command makes no sense. The **transcriptions** stay
  version-controlled, and `sources/documents/public-domain/README.md` gives
  the commands.

### Verified
- **1,378 pages across 10 publications**, unchanged after the
  restructuring (0 discrepancy across the ten counts);
- **260 tests** green; **104 illustrations**, 0 malformed; **260 headers** up
  to date;
- `make all`: **8 signed packages**, 0 failure; `make verify`: SHA-256
  checksums correct;
- `git ls-files`: only the **public** certificate is tracked; the private key
  is excluded.

---

## 2026-09-18 (evening) — installers, signing and attribution

### Added
- **A self-contained Linux installer**, `PhytoScope-X.Y.Z-Linux.run` — a
  script and an archive in one file, in the manner of NVIDIA's `.run` files,
  and the free equivalent of what InstallShield produces. It covers the
  distributions with neither `.deb` nor `.rpm` (Arch, openSUSE, Alpine,
  NixOS) and **installs without privileges**. Three interfaces: graphical
  (zenity, kdialog), text-mode boxes (`--tui`), plain lines (`--text`). With
  `--uninstall`, `--check`, `--extract` and an installation registry.
- **A macOS `.pkg` installer** — written end to end in pure Python
  (`macos_pkg.py`): a XAR archive, a cpio "odc" payload, a BOM. Neither
  `pkgbuild`, nor `xar`, nor `mkbom` is needed. Everything written is read
  back and checked again.
- **A Windows `.msi` package** through `wixl` — the format group policy and
  Intune deploy, with deterministic component identifiers so that updating a
  fleet goes well. This is not InstallShield, which is a commercial product
  running only on Windows; it is what InstallShield *produces*.
- **All packages signed**: an X.509 code-signing certificate, Authenticode
  for `.exe` and `.msi`, detached CMS (`.p7s`) for the rest. The certificate
  being **self-signed**, every package says what the signature proves —
  integrity, continuity of origin — and what it does not: it silences neither
  SmartScreen nor Gatekeeper.
- **Every installer asks** about the desktop icon and about launching at the
  end, and **provides an uninstaller**. No uninstallation erases settings or
  sessions.
- `phytoscope/AUTHORS` — the attribution in a single file, read by the
  software, by the package factory and by the certificate's subject.
  Publisher (Bretagne Namasté) and author (Thierry GAYET) are distinguished
  there.
- `manuel.txt` per system, in addition to readme, install, licence and
  changelog.

### Verified
- **Under Wine 6.0.3**: the bundled Python 3.11.9 interpreter starts, PySide6,
  pyserial and sounddevice import, `run.py --version` runs correctly. NumPy
  fails for want of `fetestexcept` in Wine's MSVC runtime — a gap in Wine,
  not in the package. The NSIS installer, being 32-bit, could not be tried:
  this machine has only 64-bit Wine.
- The `.run`: installation, registry and `--uninstall` exercised end to end.
- 225 tests green, 832 labels at 100 % in all eleven languages.

---

## 2026-09-18 (night) — the installation packages

### Added
- **`packaging/`** — a package factory, run from Debian, Ubuntu or Mint,
  which produces the five targets in one command:

  | Target | File | Requires on the receiving machine |
  |---|---|---|
  | Debian, Ubuntu, Mint | `.deb` | nothing |
  | Fedora, RHEL, Rocky, Alma | `.rpm` | nothing |
  | Windows 10 and 11 | `.exe` (NSIS) + a portable `.zip` | **nothing, not even Python** |
  | macOS Intel + Apple Silicon | a `.zip` containing `PhytoScope.app` | Python 3.9+ |
  | Every system | a source `.tar.gz` | Python 3.9+ |

- **The Windows installer requires nothing.** It bundles the Python
  interpreter (the official "embeddable" distribution), Qt, NumPy and the
  software: 177 MB, one double-click, shortcuts, an entry in "Apps &
  features" and an uninstaller. It is built from Linux, NSIS existing for
  that system too.
- **The Linux packages create a private Python environment** in
  `/usr/share/phytoscope/venv` rather than depend on `python3-pyside6`, which
  does not exist in every version of Debian, Ubuntu or Fedora. With
  `--offline` they bundle the libraries for Python 3.9 to 3.13 and install
  with no network — which is what a workshop or a classroom needs.
- **`build.py --deps` installs NSIS without `sudo`**, in `~/.local/opt`, as
  `build.sh --deps` does for the firmware's SDK.
- SHA-256 checksums for every package, verifiable with `sha256sum -c`.

### Owned
- **Nothing is signed**: a Windows signature requires a paid certificate, an
  Apple signature a developer account and a Mac. Both systems will warn at
  first opening; each package's `readme.txt` explains how to get past it.
  Better to say so than to let anybody believe in a guarantee that does not
  exist.
  *(Superseded on 2026-09-18, evening: all packages are now signed with a
  self-signed certificate, and each says what that does and does not prove.)*
- **None of these packages has been tried on a real Windows machine or on a
  Mac.** Their structure is verified (`dpkg-deb`, `rpm -qip`, the archives'
  contents, the executable's type); their execution is not.

---

## 2026-09-18 (night) — portability

### Fixed
- **Software 1.5.1** — a complete review of Windows 10/11, macOS (Intel and
  Apple Silicon) and GNU/Linux (Debian, Ubuntu, Mint, Fedora, Red Hat):
  thirteen points found, thirteen fixed.
- **The board was never recognised by its USB identifiers**: the software was
  looking for `0x2E8A:0x10F5`, the firmware declares `0x1209:0x7A01`. The
  firmware was right — `0x1209` is the free pid.codes range, `0x2E8A` belongs
  to Raspberry Pi. On Windows the control link was unusable. A test now reads
  `usb_descriptors.c` and compares.
- **The audio input refused to open on Mac and on Windows** (250 Hz asked of
  CoreAudio and WASAPI): it now falls back to the device's native rate and
  decimates in software, without losing a sample.
- **An optional dependency made the whole installation fail**:
  `requirements-optionnel.txt` is now installed separately.
- **The fonts** were hard-coded in twenty-one places, with no fallback:
  `ui/fonts.py` declares a stack and the font's genre, and corrects the size
  on macOS (72 dpi against 96).
- The audio device is resolved by host interface on Windows; shortcuts are
  shown as macOS presents them (⌘); the virtual MIDI port is explained; the
  synthesis voice is filtered by engine; the SAPI engine is created on its own
  thread; restart is rebuilt; log rotation is tolerant; file names are
  transliterated to ASCII (APFS's NFD, Windows's reserved names).
- **Firmware**: `build.sh --deps` detects the architecture — it failed on
  Apple Silicon and on Raspberry Pi — and looks for the board's mount point
  instead of assuming it.
- **PDF building**: the page count no longer depends on `pdfinfo`; the Pango /
  HarfBuzz / fontconfig prerequisites are declared.

### Added
- `tests/test_portability.py`: twenty-three tests that check under Linux what
  only shows elsewhere. **221 tests green.**

---

## 2026-09-18 (end of day)

### Added
- **Software 1.5.0 "What the noise says"** — fifteen scientific quantities in
  the Multimeter, foremost among them the **equivalent resistance** derived
  from Johnson-Nyquist thermal noise (`R = Sᵥ / 4kT`), announced for what it
  is: an **upper bound**, not an ohmmeter reading. With it: noise density in
  nV/√Hz, noise integrated over 0.01–10 Hz, mains residue, crest factor,
  spectral slope, Allan deviation at 1 s and 10 s, optimal integration,
  correlation time, normality, effective resolution, saturation margin, event
  rate and Fano factor.
- **The log window (`Ctrl+L`)**: the file live, its location spelled out, and
  "Save a copy…" to wherever you like, rotated archives included.
  Incremental reading, a text filter, the level adjustable on the fly.

### Changed
- The quantities are computed on the **raw** signal: filtering before
  measuring noise would amount to measuring your own filter.
- 826 translatable labels (against 755), 100 % in the ten languages.
- The tests can no longer touch the user's configuration
  (`tests/conftest.py` redirects XDG_CONFIG_HOME and APPDATA).

---

## 2026-09-18 (night)

### Added
- **Software 1.4.0 "The dial and the fingerprint"** — four dials with proper
  ballistics in the Multimeter, a measurement fingerprint of the rig with a
  registry of known rigs, a menu bar (Session / View / Help).
- Companion volume: the plate **"Connecting a leaf and a root"**, a section on
  choosing the substrate electrode, a section on the measurement fingerprint
  and its limits (192 → 198 pages).

### Fixed
- **Help and "About" had become unreachable**: the toolbar had overflowed and
  Qt had tucked them away. They live in the menu bar.
- The advice on the substrate electrode — a brass rod — was bad: a galvanic
  cell, and copper is toxic to roots. It is now 316L stainless steel,
  graphite, or an Ag/AgCl salt bridge.

---

## 2026-09-18 (evening)

### Added
- **Software 1.3.0 "The sketchbook"** — quick sample capture (`Ctrl+E`),
  replay of sessions and samples **inside the engine**, disk-space watching
  with a clean close before saturation, a language selector in the toolbar,
  return to the original zoom (`Ctrl+0`), eleven Speech-mode dictionaries.
- **Firmware**: `build.sh` installs the Pico SDK and the ARM toolchain in the
  home directory — with no administrator privilege — and produces
  `phytosense.uf2` (RP2350, 80 kB).
- **The project's memory**: `AGENTS.md`, `constraints.md` (64 numbered
  constraints), `.ai/journal.md`, `.ai/decisions.md`, `.ai/state.md`.
- Companion volume: chapters on samples, disk space and languages
  (190 → 192 pages).

### Changed
- Speech mode **mutes the music** while it is active, and shows a permanent
  indicator: the silence of a mode that speaks rarely must not pass for a
  fault.
- The **window shrinks** again: minimum height from 1094 to 520 pixels.

### Fixed
- Replay reopened the audio output that was already open — two threads were
  writing into the same PortAudio stream.
- Two headers were missing from `afe.c`: the firmware no longer built.

---

## 2026-09-18 (morning)

### Added
- **Software 1.2.0 "Eleven languages"** — the interface translated into
  French (then the source), American English, Spanish, Portuguese, Italian,
  Indonesian, Russian, Chinese, Japanese, Korean and Arabic; right-to-left
  layout for Arabic; a language added by simply dropping in a JSON file.
- **Eleven Speech-mode dictionaries**, one per language, with sentence
  templates of their own for the languages whose word order differs.
- **Disk-space watching** during recording: a warning at twenty minutes of
  headroom, and a clean close of the session before saturation.
- **The firmware's `build.sh`**: installs the Pico SDK and the ARM toolchain
  in the home directory, with no administrator privilege, then builds
  `phytosense.uf2`.
- **The agent memory**: `AGENTS.md`, `constraints.md`, `.ai/journal.md`,
  `.ai/decisions.md`, `.ai/state.md`.

### Changed
- Speech mode **mutes the music** while it is active, and shows its state and
  its last utterance at all times.
- The firmware builds again: two headers were missing from `afe.c`.

### Fixed
- A command-line option (`--lang`, `--simulation`, `--theme`…) is no longer
  written into the settings file: it holds for the session.

---

## 2026-09-17

### Added
- **Software 1.1.0 "Words and waves"** — the *Descriptors* tab (waveform,
  FFT, Morlet wavelets, MFCC, linear prediction, cepstrum) and the *Speech*
  tab (Speech mode, dictionary, offline synthesis).
- **Ctrl+C interrupts the software**, graphical interface included, with a
  watchdog and SIGTERM handling.
- The keyboard-shortcut help page is **checked by the program** every time it
  opens.
- Companion volume: the chapters "Six looks at the same signal" and "Words
  instead of notes", two original plates (176 → 186 pages).

### Fixed
- A settings change no longer clears the signal memory: the chain is rebuilt
  only when one of its own settings changes.

---

## 2026-09-15 → 2026-09-17

### Added
- **The book** *La Musique des Plantes* — 478 pages, 10 parts, 40 chapters,
  5 appendices, 28 vector illustrations, 21 translated patent plates.
- **The companion volume** *La Carte PhytoSense* and its three detachable
  fascicles.
- **The PhytoSense One board**: schematics, four-layer routing, a costed bill
  of materials, front- and rear-panel templates.
- **The RP2350 firmware**: ADS131M04 over SPI/DMA, USB as audio class 2.0.
- **The PhytoScope 1.0.0 software, "First sap"**: four sources, four
  instruments, documented sonification, a library, diagnostics, a headless
  mode, 56 tests.
