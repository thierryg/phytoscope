# Development constraints — the requirements

**Project:** *The Music of Plants* — the book, the technical companion volume,
the PhytoSense One acquisition board, the RP2350 firmware and the PhytoScope
software.
**Author:** Bretagne Namasté · https://bretagne-namaste.com
**Last revised:** 2026-09-23

This file is the reference: **every constraint that governs the work is here,
numbered**, so that a human or an agent can cite it ("C-14") rather than
paraphrase it. What is not here is not a rule but a habit — and can be argued
with.

> Order of precedence when two conflict: **ethics (C-1 to C-9) › measurement
> (C-10 to C-19) › robustness (C-20 to C-29) › everything else.** A fine
> feature that violates C-3 does not ship.

---

## 1. Ethics — what comes before everything else

| № | Constraint |
|---|---|
| **C-1** | Nothing the device produces is a **translation** of the plant. Sonification and Speech mode are adjustable correspondences, never interpretations. |
| **C-2** | Every correspondence rule is **shown in the interface** and **recorded in the session file**. An invisible rule is forbidden. |
| **C-3** | Every interpreted output — a note, an utterance — carries its **numerical justification**: the measured values that triggered it. |
| **C-4** | The book's four registers stay distinct and marked: 🔬 a scientific point, 🌿 an energetic reading, ⚠️ limits, ✨ inner experience. No spiritual claim presented as a scientific fact. |
| **C-5** | Vocabulary borrowed from another field is used **with its warning**: no "formants" for a plant (it has no vocal tract), no "decoding", no "language". |
| **C-6** | Ambiguities in the source documents are **flagged**, never smoothed over. |
| **C-7** | No commercial affiliation, no commissioned link, no brand presented as a partner. |
| **C-8** | Everything spoken or written stays **on the machine**: no online speech synthesis, no text or signal sent to a remote service. |
| **C-9** | The Speech-mode dictionaries are **starting points**, editable by the user; the software never claims they say what the plant says. |

## 2. Measurement — what makes the instrument worth having

| № | Constraint |
|---|---|
| **C-10** | Quantities are **calibrated and expressed in physical units** — volts, ohms, hertz, seconds — never in arbitrary ones. |
| **C-11** | The full-scale conversion factor is **written into every file** produced; a WAV without its scale cannot be used. |
| **C-12** | The baseline is **tracked but never removed**: drift is shown, not hidden. |
| **C-13** | The detection threshold is expressed in **standard deviations** of the current signal, together with an **absolute minimum amplitude** — without which one sonifies the noise floor. |
| **C-14** | Constants borrowed from speech processing are **transposed to the actual sampling rate**, never copied across. |
| **C-15** | Every representation states **what it assumes** and **what it does not allow one to conclude**. |
| **C-16** | Losses are **counted and displayed** — dropped blocks, abandoned utterances, clipping — never silent. |
| **C-17** | Timestamps come from the hardware where there is any (TCXO, sample counter); their provenance is displayed. |
| **C-18** | No measured datum is altered to "look better": filters are declared, adjustable and reversible. |
| **C-19** | Session files are **open and readable without the software**: WAV, CSV, JSON. Nothing is locked in. |
| **C-1A** | A **derived** quantity is announced as such, with its relation and its assumption. The equivalent resistance is an **upper bound** from `R = Sᵥ / 4kT`: it is never presented as an impedance measurement, which the board does not make. |
| **C-1B** | Noise quantities are computed on the **raw signal**, before the notch and the low-pass. Filtering before measuring noise amounts to measuring your own filter. |
| **C-1C** | A statistic without enough samples **says nothing** rather than showing a figure. The Fano factor does not appear below ten events. |

## 3. Robustness — what makes an eight-hour session possible

| № | Constraint |
|---|---|
| **C-20** | **Nothing slow on the data path.** The interface reads a snapshot published by the engine; it computes nothing. |
| **C-21** | The software **always starts**, with or without hardware: automatic fallback to the internal generator. |
| **C-22** | A missing optional dependency **limits** the software; it does not stop it starting. The pre-flight checks tell a missing package from a broken one and from a locked-down environment. |
| **C-23** | **Ctrl+C must always get through**, graphical interface included: session closed, settings saved, a watchdog if shutdown hangs, an immediate second Ctrl+C. SIGTERM likewise. |
| **C-24** | A **command-line option holds for the session**, never for ever: it is not written into the settings file. |
| **C-25** | A settings file that is **missing, incomplete or corrupt** must never prevent start-up. |
| **C-26** | Disk space is **watched while recording**; the session is closed cleanly before saturation, with a warning beforehand. |
| **C-27** | A settings change destroys only what it must: the signal memory is cleared only when the processing chain really changes. |
| **C-28** | Secondary threads **never** touch the graphical interface directly: Qt signals only. |
| **C-29** | Every file write is **atomic or re-closable**: an interrupted recording remains usable. |
| **C-2A** | The log is **readable from inside the software** (`Ctrl+L`): its location is spelled out, its contents fill in live, and a copy can be saved anywhere — rotated archives included. No terminal is needed in order to report an incident. |
| **C-2B** | Watching a file is **incremental** and stops when the window closes: never re-read the whole of it, never wake the disk for a window nobody is looking at. |
| **C-2C** | **Nothing is hard-coded that the system may decide otherwise**: not a font (a fallback stack and a genre, `ui/fonts.py`), not a path (`os.path.join`), not a separator, not an encoding (`open()` always carries `encoding=`). Tests check it. |
| **C-2D** | The **software's USB identifiers follow the firmware**, never the other way round. The pair belongs to the free pid.codes range (`0x1209`); a test reads `usb_descriptors.c` and compares. |
| **C-2E** | An **optional dependency that fails does not prevent the rest from installing**: it lives in `requirements-optionnel.txt`, installed separately. |
| **C-2F** | A **file name is transliterated to ASCII** before it reaches the disk: APFS normalises to NFD, Windows reserves `CON`, `NUL`, `COM1`… and strips trailing dots. The readable name stays in Unicode, in the metadata. |
| **C-2G** | The software **opens the audio input at a rate the device accepts** and decimates in software: CoreAudio and WASAPI refuse 250 Hz. The resampling loses no sample. |
| **C-2H** | **Installation packages are built from Debian/Ubuntu/Mint**, in one command (`packaging/build.py`), for all five targets. No Windows machine and no Mac is needed. |
| **C-2I** | **The Windows installer requires nothing of the target machine**, Python included. The Linux packages require only what the distribution ships by default. |
| **C-2J** | Every package **says what its signature does and does not prove**. The certificate is self-signed, so `readme.txt` explains the operating system's warning and how to get past it. We do not maintain the illusion of a guarantee we are not giving. |
| **C-2K** | Uninstalling **never touches the user's settings or sessions**. It removes what installing put down, and nothing more. |
| **C-2L** | **The version lives in one data file**, `phytoscope/VERSION`, inside the Python package. The software, the package factory, `pyproject.toml` and `tools/release.py` all read it; only the last writes it. No copy anywhere. |
| **C-2M** | **One package generator per system**, self-contained and runnable on its own, plus a `Makefile` that chains them. A failure in one does not take the others with it. |
| **C-2N** | Every build has **its own timestamped directory** `build/packages/<version>-<YYYYMMDD-HHMM>/<System>/`, and receives its version as an argument: two builds of one version cannot overwrite each other, and one knows to the name what is being distributed. |
| **C-2O** | Every package comes with **its SHA-256 checksum** and, in its directory, `readme.txt`, `install.txt`, `manuel.txt`, `licence.txt`, `changelog.txt` and `AUTHENTICITE.txt`. A directory copied on its own to a server still makes sense. |
| **C-2P** | **Attribution lives in one file**, `phytoscope/AUTHORS`: the software, the package factory and the certificate's subject all read it. Publisher and author are distinguished — the workshop that publishes is not the person who wrote. |
| **C-2Q** | All packages are **signed**: Authenticode for Windows, detached CMS elsewhere. The certificate being **self-signed**, each package says explicitly that the signature proves integrity and continuity of origin, and that it **silences neither SmartScreen nor Gatekeeper**. |
| **C-2R** | The **private key never leaves** `~/.local/share/`; its working copy is excluded by `.gitignore`, and the documentation is clear that `.gitignore` protects against Git, not against a backup. |
| **C-2S** | Every installer **asks** about what commits the user — a desktop icon, launching at the end of installation — and **provides an uninstaller**. The questions come before the copying, never in the middle of a progress bar. |
| **C-2T** | No uninstallation erases **settings or sessions**: it removes what installing put down, says where the data is, and leaves the user to decide. |
| **C-2U** | The Linux installer offers **three interfaces** — graphical, text-mode boxes, bare lines — behind **one** implementation of the installation logic. Three copies of that logic would diverge. |

## 4. Language and accessibility

| № | Constraint |
|---|---|
| **C-30** | The source language is **technical US English**: the translation keys are the English sentences themselves. This reverses the French-only rule, dropped on 2026-09-22; a source language has, by construction, no catalogue to keep up to date. |
| **C-31** | The interface language is **asked once, at installation**, in all the shipped languages, each offered in its own script — and the software takes up that answer. **No automatic detection**, and the question never comes back. Failing an answer, the source language. |
| **C-32** | A missing translation falls back to **English**; never a bare identifier on screen. |
| **C-33** | Adding a language requires **no change to the code**: a JSON file dropped into `phytoscope/languages/`. |
| **C-34** | The inventory of labels is produced **by reading the code**, not kept by hand; a test fails if a shipped catalogue is incomplete. |
| **C-35** | Right-to-left languages mirror the whole layout. |
| **C-36** | A AAA high-contrast theme and a text scale from 0.8 to 2.0, available at all times. |

## 5. Software engineering

| № | Constraint |
|---|---|
| **C-40** | **Python 3 + PySide6 + NumPy**. No mandatory dependency beyond those. No SciPy: filter coefficients are worked out by hand. |
| **C-41** | The software runs on **GNU/Linux, Windows and macOS**, with no distribution-specific code. |
| **C-42** | All code, comments and docstrings are in **technical US English** — file names and directory names too. Whatever is not exposed to an end user is in English without exception: build scripts, tools, CI, firmware, agent memory. Whatever **is** exposed follows the language the user chose at installation. |
| **C-43** | Every module explains **why** it is written the way it is, not only what it does. A comment that paraphrases the code is to be deleted. |
| **C-44** | The design patterns in use are **named** (strategy, observer, command, value object). |
| **C-45** | Generated files (`A0b-codes.html`, `_bom-table.html`, `_sbom-table.html`, `pdf-src/_book.html`, `pdf-src/_carte-*.html`) are **never edited by hand**. |
| **C-46** | The software bill of materials (SBOM, CycloneDX 1.5) is produced **by introspecting the modules that are really importable**, never copied from the requirements file. |
| **C-47** | The tests run without hardware and without network: `make test`. No test may depend on a sound card. |
| **C-48** | A visual check (an off-screen capture) accompanies any notable interface change. |
| **C-49** | The **module contract carries its own version number**, `API_VERSION` in `phytoscope/api/contract.py`, in semantic numbering, and it is the only surface a third-party module may import from. A module declares the **minimum** it needs; the host refuses at discovery what it cannot honour, naming both versions, rather than loading it halfway. Breaking the contract means changing the major and documenting the migration — done once for the event names (1.0 → 2.0) and once for the English rename (2.0 → 3.0). |

## 6. Hardware and firmware

| № | Constraint |
|---|---|
| **C-50** | Target: **RP2350**, Pico SDK ≥ 2.0, TinyUSB. The measurement stream goes over USB as **audio class 2.0**, with no driver. |
| **C-51** | Power **from a battery or cells only**. Never a mains connection, never a path across the chest of somebody with an implant. |
| **C-52** | Galvanic isolation between the measuring stage and the host; the guard and the shield are documented. |
| **C-53** | The hardware is published under **CERN-OHL-P v2**, the software and firmware under **MIT**. |
| **C-54** | Every document, every plate and the board itself carry **the author and the website** — an anonymous drawing is a lost drawing by its second photocopy. |
| **C-55** | Building the firmware requires **no administrator privilege**: `_make_.sh --deps` installs the SDK and the ARM toolchain in the home directory. |
| **C-56** | A **descriptor states what the hardware has**, and nothing else. A template is a way to start, not a way to finish: a control declared and not wired is a control an application will set, read back, and believe. Where the device cannot honour what it advertises, the divergence is recorded in the reference rather than glossed over — and then fixed. |

## 7. Documents

| № | Constraint |
|---|---|
| **C-60** | The PDFs are **entirely reproducible** from the sources: HTML fragments + CSS + plates generated by a deterministic script. |
| **C-61** | Plates are **drawn by program** (`gen.py`, `gen_board.py`), never imported from a drawing application. |
| **C-62** | A clickable table of contents, bookmarks, running heads, pagination, and complete PDF metadata (author, publisher, contact, licence). |
| **C-63** | Every technical claim is **sourced**: a patent, a peer-reviewed article, a datasheet or public code. |
| **C-64** | The counts stated — pages, chapters, plates, tests — are **verified after rebuilding**, never estimated. |

## 8. Out of scope — what we shall not do

- No **emotion recognition**, and no plant "intention", under any name.
- No **machine learning** that would produce an output nobody can explain:
  everything that comes out must be justifiable line by line.
- No **online speech synthesis**, no remote service, no telemetry.
- No **shop**, no affiliate link, no email capture.
- No **eye diagram** on the plant signal: with neither clock nor alphabet it
  would be a picture without a measurement (the name stays reserved for the
  digital link and for rigs of known period).
