# Design decisions

Short form: **context → decision → consequence**, plus what would change it. A
decision you cannot defend is not a decision, it is a habit.

Numbers are stable: `constraints.md` and `.ai/journal.md` cite them. Where a
decision has been reversed, it is marked and the reversal is recorded rather
than the entry being deleted — how a project changed its mind is part of what
this file is for.

---

## D-1 — Python rather than C++ or Rust for the software

**Context:** a measurement program that is slow to render but quick to change,
and that non-programmers must be able to amend.
**Decision:** Python 3 + PySide6 + NumPy, without SciPy.
**Consequence:** the audio callback computes nothing (the buffer is filled in
advance), and the filter coefficients are written by hand. See part V of the
companion volume.
**What would change it:** a sample rate beyond 10 kHz.

## D-2 — Translation keys are the source-language sentences

**Reversed on 2026-09-22 as to which language.** The mechanism stands; the
source language changed from French to English.

**Context:** an incomplete catalogue must never degrade the interface.
**Decision:** `t("Oscilloscope")` rather than `t("tab.scope.title")`. The keys
are the **English** sentences since 2026-09-22; they were the French ones
before, and French became a catalogue like the other ten.
**Consequence:** a missing translation shows correct English; the code stays
readable; renaming an English sentence invalidates its translation — hence the
`--inutiles` tool and the coverage test.
**What the reversal cost:** 1,162 literals re-keyed across 42 files, with an
AST fingerprint to prove no code moved. `ast`'s `col_offset` is a byte offset,
which the first attempt got wrong; see `.ai/journal.md` for 2026-09-22.

## D-3 — The language is asked at installation, and never guessed

**Replaced on 2026-09-22.** The earlier decision — French at first launch,
without locale detection — is superseded in its choice of language but not in
its refusal to guess.

**Context:** the book, the figures and the dictionaries were in French; they
are becoming English. Either way, guessing from the environment is wrong.
**Decision:** the installer asks the language as its **first question**, before
the licence, and writes the answer to `ui.language` in `reglages.json` — the
same file the software reads at every start. Failing that, the source
language: English. **No reading of `LANG`** anywhere (`C-31`).
**Consequence:** the installer's screens and the software speak the same
language, chosen once by the user. One generic installer, not one per
language. Locked down by tests on all three platforms; on macOS the question
moved from first launch to the post-install script on 2026-09-23, so that the
`.pkg` behaves like the others.

## D-4 — A command-line option does not persist

**Context:** `--simulation` passed once left the software in simulation for
ever; `--lang ko` left the interface in Korean.
**Decision:** `Settings.forcer()` remembers the original value and restores it
on write, unless the user changes that setting themselves in the meantime.
**Consequence:** tests no longer pollute the configuration (`C-24`).

## D-5 — The sample chooses its own full scale

**Context:** a 150 µV signal written at ±2.5 V uses nine bits out of
twenty-four, and quantises at 0.3 µV — a third of its own noise.
**Decision:** full scale rounded up the 1–2–5 sequence above the observed
amplitude, and written into the companion JSON.
**Consequence:** no quantisation below the picovolt; a WAV deprived of its JSON
stays readable but its amplitude is *assumed*, and the interface says so.

## D-6 — The music falls silent during voice mode

**Context:** a voice and a synthesizer playing together mask each other; the
user concludes that voice mode is broken.
**Decision:** `voice.mute_music`, on by default; detection continues.
**Consequence:** voice mode is audible as soon as it is switched on.

## D-7 — Dictionaries carry their own sentence templates

**Context:** "私は かすかに ふるえる" does not follow the word order of "I barely
shiver".
**Decision:** a dictionary may define its templates per grammar; they take
precedence over those in `GRAMMAIRES`.
**Consequence:** Japanese, Korean, Chinese and Arabic produce correct sentences
without the engine knowing any grammar at all.

## D-8 — The SDK and the ARM toolchain install under the home directory

**Context:** building the firmware must not require the user's administrator
password.
**Decision:** `_make_.sh --deps` installs the Pico SDK in `~/pico/pico-sdk`
and the ARM GNU toolchain in `~/.local/opt/`.
**Consequence:** reproducible on a workshop machine; anyone who prefers their
distribution's packages installs those, and the script finds them too.

## D-9 — Stop before the disk is full, not after

**Context:** the musical rendering writes 305 MB/h; an overnight session fills
a demonstration disk.
**Decision:** measure every five seconds, warn at twenty minutes of headroom,
close cleanly below the reserve (500 MB by default).
**Consequence:** a closed session is worth infinitely more than one truncated
by a write error (`C-26`, `C-29`).

## D-10 — No eye diagram on the plant signal

**Context:** the question was asked; the tool is appealing.
**Decision:** refused under that name — with neither a clock nor an alphabet,
overlaying segments at an arbitrary period produces a picture that measures
nothing. Reserved for the digital link and for rigs with a known period
(NE555).
**What would change it:** a **triggered** overlay (a stimulus, a mark, a period
detected by the cepstrum) would be legitimate under the name "synchronous
overlay" — it remains to be written.

## D-11 — Resistance is an upper bound, and says so

**Context:** the user asks for resistance among the multimeter's readings. But
the board injects no current during a session: there is no impedance meter, and
none is wanted — we listen, we do not excite.

**Decision:** compute it from thermal noise, `R = Sᵥ / 4kT`, and show it under
the name **equivalent resistance**, with the explicit note that it is an
**upper bound**. The observed noise also contains the amplifier's and whatever
the rig picks up; the source therefore cannot be more resistive than the figure
shown, but it may be less.

**Why it is useful anyway:** a contact that dries out pushes that bound up by a
decade within minutes. It is its **variation** that informs, not its absolute
value — and the interface says so in the next column.

**Consequence:** the density is read between 10 and 40 Hz, above the biological
band, without which the plant's activity would be counted as noise (`C-1A`,
`C-15`).

**What would change it:** injecting a small alternating current would give a
true impedance — but it would stop being passive listening, which the project
refuses elsewhere.

## D-12 — Measure the noise before filtering it

**Context:** the noise figures could be computed on the processed signal,
available in the same place and already clean.

**Decision:** `engine.recent(duree, raw=True)`. The notch filter would erase
the mains residue that is precisely what we want to measure; the 40 Hz
low-pass would erase the 10–40 Hz band where thermal noise is read.

**Consequence:** the numbers on the "Scientific quantities" page may differ
from those on the other tabs, and the page's header says so in plain words.
Filtering before measuring noise amounts to measuring your own filter
(`C-1B`).

## D-13 — The USB identifiers follow the firmware, not the other way round

**Context:** the software looked for the board at `0x2E8A:0x10F5`; the firmware
declares `0x1209:0x7A01`. A choice had to be made.

**Decision:** the **firmware** is right, and the software was corrected.
`0x1209` is the **pid.codes** range, open to free projects; `0x2E8A` belongs to
Raspberry Pi, and nothing entitles us to assign a PID of our choosing inside
it. Shipping a product under someone else's identifier is a fault, even when
the board is built on their chip.

**Consequence:** a test reads `usb_descriptors.c` and compares the software's
three declarations against it. The divergence can no longer go unnoticed — it
had stayed invisible on Linux and macOS, where a fallback on product name
masked it, and made the board unusable on Windows (`C-2D`).

## D-14 — A font stack, never a single family

**Context:** "DejaVu Sans Mono" was named in twenty-one places. It is
installed by default on almost every GNU/Linux distribution and on no fresh
install of Windows or macOS.

**Decision:** `ui/fonts.py` declares a stack of families **and the style hint**
(`QFont.Monospace`). The hint matters more than the stack: even if no family
exists, Qt then picks a fixed-pitch face and the value columns stay aligned. A
proportional substitution would make the multimeter unreadable without raising
any error at all.

**Consequence:** the size correction for macOS (72 dpi against 96) lives in the
same place, and a test forbids naming a font anywhere else (`C-2C`).

## D-15 — Packages are built from Linux, with no Windows machine and no Mac

**Context:** delivering Python software to users who have neither Python nor a
terminal.

**Decision:** a single script, `packaging/build.py`, run from
Debian/Ubuntu/Mint, produces all five targets. Three mechanisms make that
possible: `pip download --platform` fetches another system's wheels; Python
publishes an **embeddable distribution** for Windows that can be placed inside
the package; and **NSIS exists on Linux**, so a real installer `.exe` can be
built from Debian.

**What is accepted:** nothing is signed by a recognised authority — a Windows
signature costs a certificate, an Apple signature demands a developer account
**and** a Mac. Both systems will warn on first opening; every package explains
how to get past it. Better to say so than to let a guarantee be assumed that
does not exist.

**macOS is the exception:** the interpreter is not bundled there. Apple has
shipped no usable Python since macOS 12.3, and a CPython redistributed from
Linux would be unsigned — Gatekeeper would refuse it, and the application would
not open without saying why. The `.app` package therefore uses the user's
Python, bundles every library, and shows a real window if it is missing.

## D-16 — The Linux packages create a private Python environment

**Context:** should we depend on `python3-pyside6` or carry our own libraries?

**Decision:** a private environment in `/usr/share/phytoscope/venv`, created at
install time from the wheels bundled in the package.

**Why:** PySide6 is not packaged by every version of Debian, Ubuntu or Fedora,
and where it is, the version ranges from 6.2 to 6.7 depending on the
repository. A dedicated environment guarantees the same thing everywhere
without touching the system Python — and therefore without risking breaking
some other program.

**Consequence:** the wheels are downloaded for **five versions of Python** (3.9
to 3.13), because a NumPy wheel is good for one minor version only and the
targeted distributions ship 3.9 through 3.13. Qt escapes this: its wheels are
`abi3`. The post-install script falls back to the network when no wheel fits,
and that failure never prevents the installation (`C-2E`).

## D-17 — The version lives in a data file, not in code

**Context:** the number was written in Python (`VERSION_MAJOR = 1`…), and
`pyproject.toml` kept a copy. It drifted: it still announced 1.0.0 when the
software was at 1.5.0.

**Decision:** `src/phytoscope/phytoscope/VERSION`, in "key = value" form, is
the only source. The software reads it at start-up, `pyproject.toml` reads it
through `dynamic = ["version"]`, the package factory reads it to stamp the
artefacts, and `tools/release.py` is the only thing that writes it.

**Why inside the Python package and not at the repository root:** installed
software does not carry the repository. Placed there, the file follows the
software wherever it goes, and the version shown in "About" is necessarily the
version of the code that is running. It is therefore listed in
`package-data`, failing which a wheel would leave it behind (`C-2L`).

## D-18 — One generator per system, and a Makefile to chain them

**Context:** a single 1,100-line script built all five targets. It was becoming
hard to read, and an error in the Windows part prevented work on the Debian
part.

**Decision:** `common.py` holds what depends on no system; each target has its
own script, self-contained and runnable alone; `build.py` is now only a
dispatcher, and a `Makefile` offers `make debian`, `make windows`, `make all`.

**Consequence:** each generator takes `--version`, `--release` and `--sortie`.
That is what lets the Makefile compute the timestamped directory **once** and
impose it on all of them: without it, five generators run in sequence would
create five directories, and the packages of one build would be scattered
(`C-2M`, `C-2N`).

## D-19 — macOS's .pkg format is written from end to end

**Context:** the user asks for a `.pkg`. `pkgbuild` exists only on macOS, and
the two free tools that replace it — `xar` and `mkbom` — are no longer packaged
by Debian or Ubuntu.

**Decision:** `macos_pkg.py` writes the three nested formats in pure Python:
the **XAR** archive, the **cpio** payload in "odc" format, and the **BOM**
manifest, that binary tree whose absence makes an otherwise correct package
fail. No dependency, nothing to compile, a deterministic result.

**How we make sure it is right:** everything written is read back by the same
module — the XAR table re-extracted, the cpio re-expanded, the BOM tree
re-walked — and we check that all three describe the **same set of files**. A
payload and a manifest that diverge are the classic failure of a hand-built
package: the installer copies, then refuses.

**What remains uncertain:** the package has never been given to
`installer(8)`. There is no Mac here, and the script says so at every build.

## D-20 — An MSI, and not InstallShield

**Context:** the question was asked. InstallShield is a commercial Revenera
product under a paid licence that runs only on Windows: it is unusable from
Debian.

**Decision:** produce what InstallShield produces — an **MSI** — with `wixl`,
from msitools, which exists on Linux. The MSI complements the NSIS installer
without replacing it: NSIS installs into the user's profile **without
administrative rights**, which matters in a classroom; the MSI installs for the
whole machine and deploys by group policy or Intune.

**The detail that cost two attempts:** `wixl` refuses absolute `Source` paths
and resolves everything from its current directory. The tree must therefore be
described relatively, and one must `cd` into the payload before calling it. It
also ignores `CompressionLevel` and `WixVariable`, which WiX accepts.

## D-21 — A self-signed certificate, and we say what it does not do

**Context:** the user asks for a certificate to authenticate the installers.
The temptation is to announce "signed packages" and leave it there.

**Decision:** produce a real X.509 code-signing certificate, sign the Windows
installers with **Authenticode** and everything else with a **detached CMS**
signature, and write in plain words, in the `AUTHENTICITE.txt` shipped with the
packages, that **this certificate silences neither SmartScreen nor
Gatekeeper**.

**Why that matters:** SmartScreen demands a certificate issued by a recognised
authority, billed annually; Gatekeeper demands an Apple developer account and a
Mac. Letting anyone believe a self-signed certificate changes that is preparing
a disappointment for the first installation. What the signature really brings
is said too: integrity verifiable with `openssl` alone, continuity of origin
between two versions, and deployment without a warning for anyone who installs
the certificate across their estate.

**Where the keys live:** the private key in `~/.local/share/`, mode 0600,
outside the repository; a working copy in `certificate/`, which `.gitignore`
excludes. And we point out that `.gitignore` protects you from Git, not from a
backup.

## D-22 — A Linux installer with three interfaces

**Context:** the `.run` installer spoke in lines of text. The user asked for "a
graphical display like InstallShield", and a text version on `--tui`.

**Decision:** a **display layer** (`packaging/templates/linux/frontend.sh`)
with a single API — `ui_question`, `ui_licence`, `ui_dossier`, `ui_progres` —
and three implementations: zenity or kdialog (graphical), whiptail or dialog
(text-mode boxes), and raw lines. The choice is automatic, and `--gui`,
`--tui`, `--text` force it.

**Why a layer rather than three scripts:** the installation logic is delicate —
detecting Python, the virtual environment, the bundled wheels, the
uninstaller, the registry. Having three copies of it is a guarantee that they
will diverge. Here, the rest of the script does not know whether it is talking
to a window or to a terminal.

**The detail that counts:** the optional questions are asked **before** the
copy. Interrupting a progress bar to ask "would you like an icon?" is exactly
what one reproaches installers for.

## D-23 — English is the source language, and French becomes a catalogue

**Context:** the whole repository was written in French — code, comments, file
names, publications, interface keys and this memory. On 2026-09-22 the
instruction reversed: everything in technical US English.

**Decision:** English is the **source** language, not a translation. The keys in
`t()` are English sentences; `LANGUE_SOURCE = "en"`; `en.json` was deleted
because a source language needs no catalogue, and `fr.json` was created with
938 labels. Comments, docstrings, file names, directory names, Makefile
targets, package metadata and this `.ai/` directory are written natively in
English, including when the conversation that produces them is in French.

**Where the line falls:** whatever is not exposed to an end user is in English
without exception — build scripts, tools, CI, firmware, agent memory. Whatever
**is** exposed follows the language the user chose at installation, which is
what the catalogues are for. A control port read by a developer counts as
English: the firmware's protocol messages were translated on 2026-09-23.

**What it cost, and what protected it:** two purpose-built guards.
`tools/verify_translation.py` records an AST fingerprint per file — code shape
with docstrings stripped and literals blanked, plus the literals themselves —
so that a prose translation can be proved to have moved no code.
`tools/verify_installer_i18n.py` does the same office for the shell scripts,
where there is no AST to lean on. Both caught real mistakes; see the journal.

**What is not done:** the Python identifiers of `packaging/` and the rest of
`src/phytoscope/`. The 16 Makefile targets were renamed on 2026-09-23, and so
was the public module contract — see `D-24`.


---

## D-24 — The module contract turns to English, and the major goes to 3.0

**Context:** `D-23` left the public module contract in French and called it a
decision rather than an oversight: renaming `Manifeste`, `installer()` or
`Grandeur.libelle` breaks every third-party module written against API 2.0.
On 2026-09-23 the instruction was to do it.

**Decision:** the whole surface is renamed — 195 identifiers, from
`VERSION_API` to `EtatModule.EN_FAUTE` — and `API_VERSION` goes from `"2.0"`
to `"3.0"` in the same change. Nothing is aliased.

**Why no aliases.** An alias is the tempting half-measure: keep `Manifeste`
as a name for `Manifest`, and a 2.0 module goes on loading. It goes on loading
and then fails on the first field it reads — `g.libelle` on a `Quantity` that
now has `label` — halfway through a session, with a traceback that names our
file and not theirs. A major bump exists precisely to turn that into a refusal
at discovery, before a single line of their code has run:

    incompatible — targets API 2.0, but this software offers 3.0

That sentence names the version asked for and the version on offer, appears in
Diagnostics next to the module, and is something its author can act on. It is
the behaviour `contract.py` promised in writing since 1.0, and this is the
second time it has been honoured (the first was the event names, 1.0 → 2.0).

**What the break does not touch**, and this is what makes it affordable: the
event wire names (renamed at 2.0, not again), the session files on disk, the
settings file — a module's settings are still stored under its `name` and come
back unchanged — and every guarantee the host makes.

**What it cost:** 3,000 identifier occurrences over 35 files, and four
boundary defects the test suite caught within minutes — a call into
`core/analysis.py`, one into `music/voice.py`, one into `core/disk_space.py`
and a dict key belonging to `music/lexicon.py`. Each was a place where the
rename crossed out of its own vocabulary, and each was a two-line fix once
named. The 932 translatable labels were migrated in the ten catalogues in the
same pass, placeholder by placeholder, because a `{chemin}` left in a
translation raises `KeyError` at display time.

**What it revealed:** four `__all__` lists naming classes that did not exist —
residue of a rename that had stopped halfway on 2026-09-22 and that nothing
checked, because nothing in the repository does `import *`.
`TestEveryAllIsHonest` now walks every module and compares.

**Migration:** `src/sdk/docs/08-migrating-from-2.0.md`, and chapter 6 of the
printed guide. Three steps: `api="3.0"`, rename with the table, run the tests.
