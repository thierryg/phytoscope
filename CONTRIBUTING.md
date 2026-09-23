# Contributing to PhytoScope

Thank you for the interest. This file says how to work here without losing
time — yours or anybody else's.

## Before writing a line: read, in this order

| Order | File | What is in it |
|---|---|---|
| 1 | [`AGENTS.md`](AGENTS.md) | The way in: the reading order, what we do not do here, how to leave a trace. |
| 2 | [`constraints.md`](constraints.md) | **The requirements**, numbered `C-1`…`C-64`. They are authoritative: a contribution that contradicts a constraint is refused, or the constraint changes first. |
| 3 | [`.ai/state.md`](.ai/state.md) | Where the work stands. |
| 4 | [`.ai/decisions.md`](.ai/decisions.md) | The design decisions **and their reasons**. A great many "why not do it like this?" already have their answer there. |

## The five rules that cost dearly when forgotten

1. **Technical US English everywhere** — code, comments, docstrings,
   documents, file names, commit messages. The interface is the exception: it
   follows the language the user chose at installation, through the
   catalogues (`C-42`, `C-31`).

2. **Explain the why.** A comment that paraphrases the code is to be deleted;
   a comment that says *why* the code is as it is, is to be kept. That is the
   rule that makes the difference between this repository and another.

3. **Verify, do not assume.** Every stated figure — a page count, a number of
   tests, of references, a data rate, a price — is **measured by a command**
   before it is written down.

4. **Never edit a generated file** (`C-45`). Edit the source and run the
   generator again. Generated files are recognisable: a name starting with
   `_`, or the `build/` directory, or `pdf-src/assets/svg/*.svg`.

5. **Test before concluding.** `cd src/phytoscope && make test` — no hardware,
   no network.

## What we do not do here

- ❌ **Write into the settings of whoever is running the software**
  (`~/.config/phytoscope/reglages.json`) during a test. Point
  `XDG_CONFIG_HOME` at a temporary directory instead.
  *(That rule comes from a real incident: see the journal for 2026-09-18.)*
- ❌ Add automatic locale detection (`C-31`).
- ❌ Add a mandatory dependency (`C-40`), or SciPy on any pretext.
- ❌ Use the vocabulary of speech without its warning (`C-5`). A plant
  expresses nothing; a signal is transposed. That distinction is the heart of
  the project's honesty.
- ❌ `sudo`: everything installs in the home directory (`C-55`).
- ❌ **Copy the private signing key** anywhere but
  `~/.local/share/phytoscope-signature/` and `certificate/` (`C-2R`).
- ❌ Stamp our attribution header on third-party code. `sources/` is excluded
  from `tools/headers.py` for that reason: writing
  "SPDX-License-Identifier: MIT" on GPL code is a false statement.
- ❌ Declare in a descriptor what the hardware has not got (`C-56`). A
  template is a way to start, not a way to finish.

## Setting up

```bash
git clone https://github.com/thierryg/phytoscope.git
cd phytoscope

# The software
cd src/phytoscope
make install-dev            # a virtual environment + the development tools
make test                   # the whole suite, no hardware and no network
make doctor                 # says what is installed and what is missing
cd ../..

# The pre-commit guards (strongly advised)
python3 -m pip install --user pre-commit
pre-commit install
pre-commit run --all-files  # to see the state of the whole repository
```

The archives of third-party repositories (`sources/code/`,
`sources/software/`) are not version-controlled — they weigh 817 MB. To fetch
them:

```bash
python3 tools/fetch-software.py
```

## The useful commands

```bash
# The software
cd src/phytoscope
make test                                        # the test suite
make lint                                        # ruff
make demo                                        # with no hardware
.venv/bin/python tools/i18n.py --couverture      # the 10 translations' state
.venv/bin/python tools/sbom.py --json            # the bill of materials

# The publications (from the root)
python3 pdf-src/assets/svg/gen.py       && python3 pdf-src/build.py         # the book
python3 pdf-src/assets/svg/gen_board.py && python3 pdf-src/build_board.py   # the companion volume
python3 pdf-src/assets/svg/gen_tt.py    && python3 pdf-src/build_tree.py    # the series
python3 pdf-src/assets/svg/gen_sdk.py   && python3 pdf-src/build_sdk.py     # the SDK guide
python3 tools/verify_svg.py                                   # well-formed XML
python3 tools/headers.py --verifier                           # headers up to date

# The packages (from Debian, Ubuntu or Mint)
cd packaging
make                # the target list — `help` is the default goal
make tools          # what is missing in order to package
make deps           # NSIS, msitools, osslsigncode — without sudo
make all            # .deb .rpm .run .exe .msi .pkg .zip .tar.gz, signed
make deliverables   # the packages AND the firmware, in one build
make verify         # reopens and checks everything produced

# The firmware
cd src/firmware
./_make_.sh --deps  # the SDK + the ARM toolchain in $HOME, without sudo
./build.sh          # builds AND files the deliverable
```

## Proposing a change

1. **Open an issue first** if the change touches a constraint, an interface,
   or more than a few files. That avoids writing code which will be refused
   for a reason already recorded in `.ai/decisions.md`.
2. Make a branch: `git checkout -b short-subject`.
3. Do one thing at a time. One branch, one subject.
4. **Commit messages in English**, in the imperative, with the why:

   ```
   escape & in the generated illustrations

   The generator wrote the text straight into the SVG. A bare "&" makes the
   file malformed; WeasyPrint then drops it and composes an empty frame,
   without a word. timeline.svg was the victim.
   ```

5. Before pushing:

   ```bash
   pre-commit run --all-files
   cd src/phytoscope && make test && make lint
   python3 tools/headers.py --verifier
   ```

6. **Record it**: add a dated entry to [`.ai/journal.md`](.ai/journal.md) and
   bring [`.ai/state.md`](.ai/state.md) up to date. That is what lets the next
   person — or you, three weeks later — pick the work up.
7. Open the pull request. Continuous integration will run the static
   analysis, the tests on Linux, Windows and macOS, the package build and the
   security checks.

## Reporting a fault

Open an issue with what it takes to reproduce it: the version
(`phytoscope --version`), the operating system, the Python version, and the
shortest sequence of actions. A template will help you.

**Unless it is a security problem**: in that case, do not open a public
issue. Read [`SECURITY.md`](SECURITY.md).

## The licences, and what becomes of your contribution

The repository carries two licences (`C-53`):

- **MIT** for the software, the firmware, the SDK and the tools;
- **CERN-OHL-P v2** for the hardware (`hardware/`).

See [`LICENSES/README.md`](LICENSES/README.md). By proposing a contribution
you agree to it being distributed under the licence of the file concerned.
People who contribute are added to [`AUTHORS`](AUTHORS).

## The tone

The project is about plants and electrical signals, a subject where
enthusiasm spills quickly into claims one cannot stand behind. The
repository's editorial rule is therefore simple: **say what is measured, say
what is assumed, and never confuse the two.** A contribution that improves
that honesty is always welcome, even if it does not change a line of code.
