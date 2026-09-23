# Installing PhytoScope

This file describes **what each installer does, step by step**, for each
system. It does not replace `README.md` (the project from the outside) or
`packaging/README.md` (the package factory): it answers one question —
*what happens on my machine when I install, and where?*

> **Version described**: 1.6.0 — 23 September 2026.
> The sizes are the ones measured on that build.

---

## Contents

- [What is true on every system](#what-is-true-on-every-system)
- [Debian · Ubuntu · Mint — `.deb`](#debian--ubuntu--mint--deb)
- [Fedora · RHEL · Rocky · AlmaLinux — `.rpm`](#fedora--rhel--rocky--almalinux--rpm)
- [Every distribution — `.run`](#every-distribution--run)
- [Windows 10 / 11 — `.exe`, `.msi`, portable archive](#windows-10--11--exe-msi-portable-archive)
- [macOS — `.pkg` and `.zip`](#macos--pkg-and-zip)
- [From source](#from-source)
- [Checking what you downloaded](#checking-what-you-downloaded)
- [Uninstalling](#uninstalling)
- [When it does not start](#when-it-does-not-start)

---

## What is true on every system

### A private Python environment, never the system's

PhytoScope installs **nothing** into your machine's Python. Each installer
creates a virtual environment of its own and puts NumPy, PySide6, pyqtgraph,
sounddevice and pyserial in it. The reason is simple: PySide6 is not in every
distribution's repositories, and overwriting a system version would break
other software.

### The interpreter is supplied when the system has none

| System | Where Python comes from |
|---|---|
| Debian, Ubuntu, Mint | declared as a dependency — `apt` installs it |
| Fedora, RHEL | declared as a dependency — `dnf` installs it |
| Every distribution (`.run`) | the system's if it will do, **otherwise the one the installer carries** |
| Windows | **always bundled** (the official "embeddable" distribution) |
| macOS | **bundled**, failing that python.org, failing that Apple's |

The bundled interpreters are **relocatable binaries**: they work from any
directory, without being installed, without privileges, and without touching
the system.

### Homebrew, Nix and conda are excluded — deliberately

An interpreter installed under `/home/linuxbrew`, `/opt/homebrew`,
`/nix/store` or `/opt/conda` comes with **its own dynamic loader**. It does
not read the distribution's search path: Qt, pyqtgraph and sounddevice
install there without error, then fail at run time on `libGL.so.1` or
`libportaudio.so.2` — libraries that **are in fact present**.

Every installer and every launcher therefore rules them out, and `run.py`
re-launches itself with a suitable interpreter.

### The language is asked at the very start, and remembered

**It is asked, never guessed.** Constraint `C-31` forbids automatic locale
detection, and that is not an affectation: a machine whose environment says
`fr_FR` may be the one in a workshop where the work is done in English, a
shared desk, or a cloned system image.

Eleven languages: **English, French, Spanish, Portuguese, Italian,
Indonesian, Russian, simplified Chinese, Japanese, Korean, Arabic.** Each is
offered **in its own script** — a Korean reader recognises "한국어", not
"Korean".

| Installer | When the question is asked |
|---|---|
| `.run` | **the first question**, before the licence — which is therefore read in the chosen language |
| Windows `.exe` | an NSIS dialogue, before the first page |
| macOS `.pkg` / `.app` | at the **first opening** of the application |
| `.deb`, `.rpm` | `apt` and `dnf` do not ask — the question comes at the **software's first start-up** |
| from source | the same: at first start-up |

The choice is written into `reglages.json`, key `ui.language`, which
PhytoScope reads at every start-up. **The installer and the software
therefore speak the same language without consulting each other**, and the
question never comes back. It is changed afterwards through
"View → Language".

All three installers go through the same utility,
`tools/write_language.py`, which **merges** instead of overwriting: a
reinstallation over an existing one changes nothing but the language.

To impose the language without being asked — an unattended installation, a
system image, a deployment:

```bash
./PhytoScope-1.6.0-Linux.run -y --language ja
```

### A bytecode cache, built once

Without it, Python recompiles at every start-up every module whose directory
is not writable — `/usr/share`, `/Applications`, `Program Files` — and throws
the result away. The wait shows: a few seconds, every time. So each installer
builds the cache during installation, while it still has the right to write.

### No `sudo` where it is not needed

The project will not elevate privileges behind the back of whoever is
installing (constraint `C-55`). The only cases where privileges are required
are the ones where you grant them: `sudo apt install ./phytoscope.deb`,
`sudo dnf install`, or a `.run` started by `root` to install for the whole
machine.

### Your data is never touched by an uninstallation

| What | Where |
|---|---|
| Settings and log | `~/.config/phytoscope/` · `%APPDATA%\PhytoScope` · `~/Library/Application Support/PhytoScope` |
| Recorded sessions | `~/.local/share/phytoscope/seances/` |

No installer deletes them. The commands for doing it yourself are given at
the end of every uninstallation.

---

## Debian · Ubuntu · Mint — `.deb`

**File**: `phytoscope_1.6.0_all.deb` (416 kB)

```bash
sudo apt install ./phytoscope_1.6.0_all.deb
```

`apt` — and not `dpkg -i` — because it resolves the dependencies. With
`dpkg` you then need `sudo apt install -f`.

### What happens, in order

1. **`apt` installs the declared dependencies**: `python3` (≥ 3.9),
   `python3-venv`, `python3-pip`, and **20 system libraries** — `libgl1`,
   `libegl1`, `libglx0`, `libopengl0`, `libxkbcommon-x11-0`, the seven
   `libxcb-*`, `libfontconfig1`, `libfreetype6`, `libdbus-1-3`,
   `libportaudio2`.
   *Recommended*: `python3-numpy`, `espeak-ng` (speech synthesis).
2. **The files are laid down** in `/usr/share/phytoscope/`, the launcher in
   `/usr/bin/phytoscope`, the menu entry in
   `/usr/share/applications/phytoscope.desktop`.
3. **`postinst` creates the virtual environment** in
   `/usr/share/phytoscope/venv`.
4. **The Python libraries are installed** — from the bundled wheels if the
   package carries any (an **offline** installation), otherwise from the
   network. Then the optional ones: `python-rtmidi`, `pyttsx3`. Their failure
   is without consequence, by construction.
5. **The bytecode cache is built** (`compileall`) for the software and for
   the environment.
6. **The menu-entry database is refreshed**.

### If step 3 or 4 fails

The installation **is not rolled back**: the software will say so at
start-up, with the command to type. To resume:

```bash
sudo dpkg-reconfigure phytoscope
phytoscope --check          # what is missing, and the exact remedy
```

---

## Fedora · RHEL · Rocky · AlmaLinux — `.rpm`

**File**: `phytoscope-1.6.0-1.noarch.rpm` (668 kB)

```bash
sudo dnf install ./phytoscope-1.6.0-1.noarch.rpm
```

### What happens, in order

1. **`dnf` installs the dependencies**: `python3` (≥ 3.9), `python3-pip`, and
   **11 system libraries** — `mesa-libGL`, `mesa-libEGL`,
   `libxkbcommon-x11`, `xcb-util-cursor`, `xcb-util-wm`, `xcb-util-keysyms`,
   `xcb-util-image`, `xcb-util-renderutil`, `fontconfig`, `freetype`,
   `dbus-libs`.
   *Recommended*: `portaudio`, `espeak-ng`, `python3-numpy`.
2. **The files go** into `/usr/share/phytoscope/`.
3. **`%post` creates the virtual environment**, installs the libraries
   (offline if the wheels are there), then **builds the bytecode cache**.

> **Up to 1.6.0, this package declared no system library at all.** The
> installation looked successful and the software failed on its first
> attempt to draw. That is fixed.

---

## Every distribution — `.run`

**File**: `PhytoScope-1.6.0-Linux.run` (29 MB)

For Arch, openSUSE, Alpine, NixOS, Slackware — and for **installing with no
privileges whatever**. It is both a script and an archive: the shell reads
the header, stops, and everything after it is a compressed archive. The
principle of NVIDIA's `.run` files, and the free equivalent of
InstallShield.

```bash
chmod +x PhytoScope-1.6.0-Linux.run
./PhytoScope-1.6.0-Linux.run              # a guided installation
```

| Option | Effect |
|---|---|
| *(none)* | a graphical interface if there is a desktop, otherwise text |
| `--gui` / `--tui` / `--text` | force the interface (zenity/kdialog · whiptail/dialog · plain lines) |
| `-y`, `--yes` | ask nothing — an unattended installation |
| `--prefix DIRECTORY` | install elsewhere |
| `--language CODE` | impose the language (`en fr es pt it id ru zh ja ko ar`) instead of asking |
| `--with-system-dependencies` | **also install the missing system libraries** (asks for privileges) |
| `--desktop` / `--no-desktop` | put the icon on the desktop, or not |
| `--launch` / `--no-launch` | start at the end, or not |
| `--check` | verify the archive's integrity, without installing |
| `--extract DIRECTORY` | unpack without installing |
| `--uninstall` | uninstall |

The French spellings of the options — `--texte`, `--langue`,
`--avec-dependances-systeme` — are still accepted: they were the documented
ones until 2026-09-23, and somebody's script may still use them.

### What happens, in order

1. **The language is asked** — the first question, because every following
   one will be put in the language chosen. The catalogues of all eleven
   languages travel inside the archive, and only the one chosen is loaded.
2. **The payload's SHA-256 checksum is verified** — before anything is
   written. `--check` does this step and stops.
3. **The licence is displayed**, extracted without unpacking everything,
   **in the chosen language**.
4. **The installation directory is chosen**: `~/.local/opt/phytoscope` for an
   ordinary account, `/opt/phytoscope` if started by `root`.
5. **A system Python is looked for** — `/usr/bin/python3` and its versioned
   variants, **Homebrew excluded**, and it has to be able to create a virtual
   environment. No error if none will do: the next steps provide.
6. **The payload is unpacked.**
7. **The interpreter is settled**: if no system Python would do, the one the
   archive carries is used (`<prefix>/python/bin/python3`). Otherwise **the
   duplicate is deleted**, so as not to keep 104 MB for nothing.
8. **The system libraries are checked** — the eleven that Qt and the audio
   require. If one is missing:
   - without `--with-system-dependencies`: they are **named precisely**, with
     the exact command for your distribution;
   - with the option: they are installed by your package manager.

   They are not installed in the home directory — `libGL` has to match the
   machine's graphics driver.

   Privileges are asked for through **`pkexec`, `kdesu` or `gksu`** when the
   installer was started from a desktop — an authentication window is then
   the only correct thing — and through **`sudo`** in text mode, where there
   is a terminal in front of you. If none is available, the exact command is
   printed and the installation carries on.
9. **The virtual environment is created**, then the Python libraries
   installed (offline if the wheels are bundled), then the optional ones.
10. **The bytecode cache is built.**
11. **The launcher, the menu entry and the icon are laid down** in
    `~/.local/bin`, `~/.local/share/applications`, `~/.local/share/icons`.
12. **A registry file is written** — it is what `--uninstall` reads back,
    rather than guessing.
13. **An uninstaller** is left behind: `<prefix>/uninstall.sh`.

> If `~/.local/bin` is not in your `PATH`, the installer says so and gives
> the line to add to `~/.profile`.

---

## Windows 10 / 11 — `.exe`, `.msi`, portable archive

All three carry **the Python interpreter, Qt, NumPy and the software**.
Nothing to install, nothing to download, no administrator rights.

| File | Size | For whom |
|---|---|---|
| `PhytoScope-1.6.0-Windows.exe` | 178 MB | the ordinary installer (NSIS) |
| `PhytoScope-1.6.0.msi` | 275 MB | deployment by group policy |
| `PhytoScope-1.6.0-Windows-portable.zip` | 262 MB | a USB stick, no installation |

> **SmartScreen will warn you.** The signing certificate is
> **self-signed**: it proves integrity and continuity of origin, it does not
> silence SmartScreen — and has never claimed to. Click "More info", then
> "Run anyway". The signature itself is verified through the checksum: see
> below.

### `.exe` — what happens, in order

1. **The language is asked** — an NSIS box, before any page. All eleven
   languages are compiled into the executable; the choice is remembered under
   `HKCU\Software\PhytoScope\Langue`, which avoids asking again at the next
   update.
2. **The licence is displayed** and has to be accepted.
3. **The directory is chosen** — by default
   `%LOCALAPPDATA%\Programs\PhytoScope`, which requires no privilege.
4. **The components**: the software (required) and the desktop icon
   (optional, a check box).
5. **The files are copied**: `app\` the software, `python\` the interpreter
   and the libraries, already unpacked.
6. **The registry is filled in** — under `HKCU`, never `HKLM`: "Apps &
   features" finds the name, the version, the publisher and the uninstaller
   there.
7. **The shortcuts are created** in the Start menu: *PhytoScope*,
   *Diagnostics*, *Uninstall*.
8. **The bytecode cache is built** — that is the moment that takes a few
   seconds, and the installer says so.
9. **The language is written into `reglages.json`**, so that the software
   takes it up.

### `.msi` and the portable archive

Neither has an installation step in which to run anything. **The
`PhytoScope.cmd` launcher therefore builds the cache at first start-up**,
once, with a witness file (`python\.bytecode-pret`). If the directory is
read-only, the witness cannot be written and we shall try again: that is not
fatal, the software simply starts more slowly.

For the portable archive: unpack it where you like, run `PhytoScope.cmd`.
`Diagnostic.cmd` opens a console and prints the whole report.

---

## macOS — `.pkg` and `.zip`

| File | Size |
|---|---|
| `PhytoScope-1.6.0.pkg` | 18 MB |
| `PhytoScope-1.6.0-macOS.zip` | 19 MB |

> **Gatekeeper will warn you**, for the same reason as SmartScreen: the
> certificate is self-signed, and the application is not notarised by Apple.
> Use **right-click → Open** the first time, or
> *System Settings → Privacy & Security → Open Anyway*.

### What happens, in order

1. **The `.pkg` copies `PhytoScope.app`** into `/Applications`. The `.zip`
   unpacks wherever you like.
2. **At first opening the language is asked** — a list, in eleven languages,
   before the environment is built. The choice goes into
   `~/Library/Application Support/PhytoScope/reglages.json`.
3. **At first launch** the launcher looks for an interpreter, in this order:
   the one **bundled** in `Contents/Resources/python`, then **python.org's**
   (installed as a framework), then **Apple's**. **Homebrew is excluded.**
4. **The virtual environment is created** in
   `~/Library/Application Support/PhytoScope/venv` — not inside the bundle: a
   `.app` in `/Applications` is not writable, and it has to serve several
   accounts. A window warns that this takes a minute or two, once.
5. **The libraries are installed**, offline if the package carries the
   wheels.
6. **The bytecode cache is built** in the user's environment, and the cache
   for the bundle's own modules goes beside it (`PYTHONPYCACHEPREFIX`), since
   the `.app` is read-only.

### One reservation, said plainly

The bundled interpreter is supplied **for one architecture only** — the one
chosen at build time (`--arch x86_64` or `--arch arm64`), by default the one
of the machine doing the building. There is no "universal2" build of the
relocatable interpreter we use. A package built on Intel will therefore not
bring an interpreter usable on Apple Silicon: the launcher will fall back on
python.org's or Apple's, and will say so if it finds neither.

---

## From source

```bash
git clone https://github.com/thierryg/phytoscope.git
cd phytoscope/src/phytoscope

make install-dev      # a virtual environment + the development tools
make doctor           # what is installed, what is missing
make test             # 385 tests, no hardware and no network
make demo             # start up with a simulated plant
```

The system libraries are still yours to install, through your package
manager. `make system-deps` prints the exact command for your distribution.

Then, to run: `make run`, or `./run.py`. The second will do as well — it
re-launches itself with the environment's interpreter if the one on `PATH`
will not do.

---

## Checking what you downloaded

Every published package comes with three things.

### 1. The checksum — is the file intact?

```bash
sha256sum -c SHA256SUMS.txt --ignore-missing
```

### 2. The provenance — where did it come from? (the strongest)

Every published package carries a Sigstore attestation saying which
repository, which commit and which workflow it came from:

```bash
gh attestation verify phytoscope_1.6.0_all.deb --repo thierryg/phytoscope
```

### 3. The publisher's signature

`AUTHENTICITE.txt`, shipped with the packages, gives the procedure. The
`.exe` and `.msi` carry an Authenticode signature; the others a detached CMS
signature (`.p7s`), verifiable with the public certificate
`phytoscope-certificate.pem`, also shipped.

To check everything again at once, from source:

```bash
cd packaging && make verify
```

---

## Uninstalling

| System | Command |
|---|---|
| Debian, Ubuntu, Mint | `sudo apt remove phytoscope` |
| Fedora, RHEL | `sudo dnf remove phytoscope` |
| `.run` | `~/.local/opt/phytoscope/uninstall.sh` — or `./PhytoScope-*.run --uninstall` |
| Windows | "Apps & features", or the *Uninstall* shortcut |
| macOS | drag `PhytoScope.app` to the Trash |

Each removes the virtual environment and the bytecode cache, which neither
`dpkg` nor `rpm` knows about — they were produced after the installation, and
would otherwise survive it.

**Your settings and your sessions are kept.** To erase those as well:

```bash
# Linux
rm -rf ~/.config/phytoscope ~/.local/share/phytoscope
# macOS
rm -rf ~/Library/Application\ Support/PhytoScope
# Windows
rmdir /s "%APPDATA%\PhytoScope"
```

---

## When it does not start

The first thing to do, always:

```bash
phytoscope --check          # or, on Windows: Diagnostic.cmd
```

It prints the banner, the **checklist** — system, interpreter, dependencies,
board, audio inputs and outputs, where the files go — then the **pre-flight
checks**, dependency by dependency, each with its version. That listing is
what to attach to any report.

### The two commonest cases

**"*libGL.so.1* is installed but the interpreter cannot reach it"**
You are running PhytoScope with a Python from Homebrew, Nix or conda.
**There is no package to install.** Start it through the project's
environment (`make run`), or through an installation package. `./run.py`
re-launches itself in that case anyway.

**"*libGL.so.1* not found"** — without the first sentence. There it really is
missing. The report gives the exact command for your distribution; so does
`make system-deps`.

### The interface refuses to load

You can work without it, and still record:

```bash
phytoscope --headless --record
```

### Reporting

A fault: an issue, with the output of `--check`
(`.github/ISSUE_TEMPLATE/bug.yml` will guide you).
**A security problem: no public issue** — read [`SECURITY.md`](SECURITY.md).
