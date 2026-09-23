# Building the packages

This file says **how to produce one particular package, or all of them**, and
what you need beforehand. It does not describe what an installer does once it
is in the hands of whoever runs it: that is [`INSTALL.md`](INSTALL.md).

Everything happens from `packaging/`, and everything goes through `make`.

> **One Debian, Ubuntu or Mint machine produces the packages for every
> system.** Windows and macOS are cross-built — NSIS, msitools and a `.pkg`
> generator written end to end. There is no Windows machine and no Mac in the
> loop, and that is owned: what is verified here is the packages'
> **structure**, not their installation.

---

## Contents

1. [In five minutes](#1-in-five-minutes)
2. [What you need](#2-what-you-need)
3. [The signing certificate](#3-the-signing-certificate)
4. [Building one package](#4-building-one-package)
4 bis. [Building the firmware](#4-bis-building-the-firmware)
5. [Building everything](#5-building-everything)
6. [Forcing the version, the release, the destination](#6-forcing-the-version-the-release-the-destination)
7. [Checking what was produced](#7-checking-what-was-produced)
8. [The software bill of materials](#8-the-software-bill-of-materials)
9. [Publishing a version](#9-publishing-a-version)
10. [When it fails](#10-when-it-fails)
11. [Every target](#11-every-target)

---

## 1. In five minutes

```bash
cd packaging

make                # the target list — `help` is the default goal
make tools          # what is installed, what is missing
make deps           # installs NSIS, msitools, osslsigncode — without sudo
make certificate    # once, and then never again
make all            # the nine packages, signed
make verify         # reopens and checks everything produced
```

The packages arrive in `build/packages/<version>-<timestamp>/`, and
`build/packages/latest` points at the most recent build.

---

## 2. What you need

`make tools` answers, and does not get it wrong:

```
  ✓ dpkg-deb   Debian package (.deb)
  ✓ rpmbuild   Red Hat package (.rpm)
  ✓ makensis   Windows installer (.exe)
  ✓ wixl       Windows package (.msi)
  ✓ zip        Windows and macOS archives
  ✓ openssl    certificate and signatures
  ✓ osslsigncode Authenticode signing (.exe, .msi)
```

### What is missing installs without `sudo`

```bash
make deps
```

NSIS, msitools and osslsigncode are unpacked into `~/.local/opt`. The project
will not elevate privileges (`C-55`): none of these commands calls `sudo`.

`dpkg-deb` and `rpmbuild` come from your distribution:

```bash
sudo apt install dpkg-dev fakeroot rpm
```

### The project's Python environment

The factory uses the project's interpreter if it exists
(`src/phytoscope/.venv/bin/python`), otherwise the system's. To create it:

```bash
cd ../src/phytoscope && make install-dev
```

---

## 3. The signing certificate

**Once in the project's life.** After that, it is left alone.

```bash
make certificate          # creates it if absent, then fills certificate/
make certificate-status   # what exists, and where
make certificate-verify   # do the two copies agree?
```

### Where everything lives

| Where | What | In the repository? |
|---|---|---|
| `~/.local/share/phytoscope-signature/` | the **reference** copy: private key + certificate | **no**, and never |
| `certificate/` | the **working** copy: public certificate, `.crt`, the key at 0600, a notice | the public part **yes**, the key **never** |

Constraint `C-2R` allows the private key in those two places only. Three nets
stop it being published: `.gitignore` excludes it by name, the `pre-commit`
hook refuses it **on its name alone** — even empty, even renamed — and
continuous integration's "secrets" job fails if it appears. Three, because a
published key cannot be unpublished.

### If the certificate is missing when it is time to sign

The factory **says so and offers**; it creates nothing on its own authority:

```
  ! no signing certificate: the packages will not be signed.
      The reference copy is expected in
      /home/…/.local/share/phytoscope-signature

  Create one now? [y/N]
```

With no terminal — in a script, in continuous integration — it prints the
command and stops rather than assume agreement: making a signing key on the
spur of the moment would produce an ephemeral key that somebody would believe
permanent.

### BACK UP the private key

Without it, later versions can no longer be tied to earlier ones. Anybody who
had noted the fingerprint would suddenly see a different one.

```bash
make certificate-fingerprint     # the SHA-256 fingerprint, the published one
```

### Remaking the certificate — what to know first

```bash
make certificate-renew
```

That **replaces the key** and **breaks the link** with everything already
signed: the packages already published become unverifiable with the new
certificate. The command asks you to type `REPLACE` in full, and refuses if
there is no terminal. Add `--oui` to `certificate.py --refaire` only if that
is really what you mean.

### What this certificate proves, and what it does not

It is **self-signed**. It proves a package's **integrity** and its
**continuity of origin**. It does **not** silence SmartScreen or Gatekeeper,
and has never claimed to (`C-2Q`).

---

## 4. Building one package

| Command | Produces | For |
|---|---|---|
| `make debian` | `phytoscope_<v>_all.deb` **and** `PhytoScope-<v>-Linux.run` | Debian, Ubuntu, Mint — and every distribution for the `.run` |
| `make fedora` | `phytoscope-<v>-1.noarch.rpm` | Fedora, RHEL, Rocky, Alma |
| `make windows` | `PhytoScope-<v>-Windows.exe`, `.msi`, `-portable.zip` | Windows 10 / 11 |
| `make macos` | `PhytoScope-<v>.pkg`, `-macOS.zip` | macOS Intel and Apple Silicon |
| `make source` | `phytoscope-<v>.tar.gz` | every system |
| `make linux` | `.deb` + `.run` + `.rpm` | both Linux families |

### Through the script, for the finer options

```bash
python3 packaging/build_debian.py            # the .deb and the .run
python3 packaging/build_fedora.py            # the .rpm
python3 packaging/build_windows.py --msi     # the .msi only
python3 packaging/build_macos.py --pkg       # the .pkg only
python3 packaging/build_macos.py --arch arm64
python3 packaging/build_source.py
```

### How long, and how much room

| Target | Time | Size |
|---|---:|---:|
| `source` | a few seconds | 656 kB |
| `debian` | ~1 min *(the `.run` bundles an interpreter)* | 416 kB + 29 MB |
| `fedora` | a few seconds | 668 kB |
| `macos` | ~1 min | 18 + 19 MB |
| `windows` | **~15 min** *(250 MB of wheels to download)* | 178 + 275 + 262 MB |

`make windows` is by far the longest: it fetches the embeddable interpreter
and the Qt wheels, then compresses the same content three times. That is why
`make all` runs the quick targets first — a missing tool then shows in ten
seconds rather than after a quarter of an hour.

### Without a network

```bash
make offline
```

The wheels are bundled inside the packages: the installation on the receiving
machine then needs no connection. The packages grow accordingly — Qt weighs
450 MB as "universal2" for macOS.

---

## 4 bis. Building the firmware

The `.uf2` is **a deliverable in its own right**: without it, the packages
install software that has nothing to listen to.

**Two scripts, two uses.**

| | What it does | When |
|---|---|---|
| `./_make_.sh` | builds, and nothing else → `build/phytosense.uf2` | while developing, when you build twenty times in a row |
| `./build.sh` | builds **and then files the deliverable** in `build/packages/` | to publish, and in continuous integration |

```bash
cd src/firmware
./build.sh --deps      # Pico SDK and ARM toolchain in $HOME, no sudo — once
./build.sh             # build and file the deliverable
```

The deliverable arrives **in the same place as the packages**, because that
is what it is:

```
build/packages/<version>-<timestamp>/Firmware/
    phytosense-<version>.uf2      what you copy onto the board
    phytosense-<version>.elf      for debugging
    phytosense-<version>.bin      the raw image
    phytosense-<version>.sha256   the checksums
    README.txt                    how to flash the board
```

The name carries the version: a bare "phytosense.uf2", on somebody's disk six
months later, does not say which version it came from.

| `build.sh` option | Effect |
|---|---|
| `--deps` | installs the Pico SDK and the ARM toolchain in `$HOME` |
| `--clean` | start again from an empty build directory |
| `--output DIRECTORY` | file it elsewhere |
| `--no-install` | build only, like `./_make_.sh` |

The French spellings — `--sortie`, `--sans-installer` — are still accepted.

Started by the package factory, it follows the `PHYTOSCOPE_OUTPUT` variable:
the firmware is then filed in **the same build** as the `.deb` and the
`.msi`, even when run on its own. Hence two targets, from `packaging/`:

```bash
make firmware       # the .uf2, filed in the build in progress
make deliverables   # the packages AND the firmware, together
```

**`firmware` is deliberately outside `make all`**: building it needs an ARM
cross-toolchain that the packaging machine may not have, and a `make all`
that failed for want of `arm-none-eabi-gcc` would be an unpleasant surprise.
`make deliverables` is there for whoever wants both at once.

### What the machine needs

```bash
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi \
                 libstdc++-arm-none-eabi-newlib
```

The Pico SDK (**2.0.0 minimum** — the 1.x versions know only the RP2040 and
fail at configuration) and the ARM toolchain are installed by `--deps` in
`$HOME`, without privileges.

### If the build refuses to start

```
CMake Error: The current CMakeCache.txt directory … is different than
the directory … where CMakeCache.txt was created.
```

A CMake cache remembers the **absolute path** of the sources: moving or
renaming the working copy makes it stale. `build.sh` now detects that and
throws it away itself — the message should no longer appear. If it does
anyway: `rm -rf src/firmware/build`.

### In continuous integration

`packages.yml` builds the firmware on every run — a binary made by hand is a
binary nobody can tie to a commit — and attaches it to the artefacts with its
checksums. `release.yml` publishes it with the version, under the name
`phytosense-<version>.uf2`, and **attests its provenance** as it does the
packages'.

---

## 5. Building everything

```bash
make all
```

It chains, **in this order, which is not arbitrary**:

```
source → linux → macos → windows → certificate → sign → documents
```

1. **the quick targets first** — a missing tool shows at once;
2. **`certificate`** before `sign`, obviously;
3. **`sign`** before `documents`: the Authenticode signature **modifies** the
   `.exe` and the `.msi`, so the checksums have to be computed **after** it.
   `documents` writes the checksums; it comes last.

Then `make all` calls `verify.py` itself and prints its report.

### What that produces

> **The firmware is not in `make all`.** It builds through
> `src/firmware/build.sh` or `make firmware` (see
> [§ 4 bis](#4-bis-building-the-firmware)), and the CI attaches it to the
> deliverables. The two chains are separate because their tools are:
> `make all` needs no ARM compiler. `make deliverables` does both.

**Nine packages**, each accompanied by:

- its `.sha256` checksum;
- its signature — `.p7s` (detached CMS) for all of them, **Authenticode** for
  the `.exe` and the `.msi`;
- seven documents: `AUTHENTICITE.txt`, `install.txt`, `manuel.txt`,
  `readme.txt`, `licence.txt`, `changelog.txt`,
  `phytoscope-certificate.pem`.

Filed by system:

```
build/packages/1.6.0-20260923-1445/
├── phytoscope-1.6.0.tar.gz          + .sha256 .p7s
├── Linux/    .deb  .run  .rpm       + checksums, signatures, documents
├── Windows/  .exe  .msi  .zip
├── MacOSX/   .pkg  .zip
├── Firmware/ .uf2  (with `make deliverables`)
└── (the documents at the root)
```

---

## 6. Forcing the version, the release, the destination

The version is read from `src/phytoscope/phytoscope/VERSION`, **the only
source of truth**. To work around it for one trial:

```bash
make all VERSION=1.6.0            # another version
make all RELEASE=2                # the package's release, not the software's
make all OUTPUT=/tmp/trial        # somewhere other than build/packages/
make debian VERSION=1.6.0 RELEASE=2
```

`SORTIE=` is still honoured: it was the documented name until 2026-09-23.

To **change** the version for good, the software decides:

```bash
cd ../src/phytoscope
make bump-patch      # 1.6.0 → 1.5.2
make bump-minor      # 1.6.0 → 1.6.0
make bump-major      # 1.6.0 → 2.0.0
make release-check   # is this version fit to publish?
```

`release-check` refuses a suffixed version (`-dev`, `-rc1`): it is not meant
to be distributed.

---

## 7. Checking what was produced

```bash
make verify      # reopens each package and checks its consistency
make checksums   # recomputes the .sha256 files
```

`make verify` checks, for each package:

- that it **opens** — a `.deb` is read back by `dpkg-deb`, an `.rpm` by
  `rpm -qp`, an `.msi` by `msiinfo`, a `.pkg` by `xar`, an archive by its own
  format;
- that the **version declared** inside matches the one expected;
- that the **internal manifest** agrees with the real payload;
- that the **SHA-256 checksums** match;
- that the **seven documents** are present in each system directory.

It ends with a warning that needs reading:

```
  ! none of these packages has been INSTALLED: this machine has no
    Windows, no macOS and no Fedora. What is verified here is their
    structure and their internal consistency.
```

Real installation is tested on each system. Continuous integration helps:
`packages.yml` runs the tests on Linux, Windows and macOS.

### Verifying a signature by hand

```bash
cd build/packages/latest
openssl cms -verify -binary -inform DER -in Linux/phytoscope_1.6.0_all.deb.p7s \
    -content Linux/phytoscope_1.6.0_all.deb \
    -certfile phytoscope-certificate.pem -noverify -out /dev/null
```

---

## 8. The software bill of materials

Two bills of materials, two scopes — and that is intentional.

| File | Scope | Produced by |
|---|---|---|
| `src/phytoscope/sbom.cdx.json` | **the software** — this is the one shipped inside the packages | `src/phytoscope/tools/sbom.py` |
| `sbom.cdx.json` (at the root) | **the whole project** — software *and* RP2350 firmware | `tools/sbom.py` |

```bash
python3 tools/sbom.py                  # the reading, as text
python3 tools/sbom.py --ecrire         # writes sbom.cdx.json (CycloneDX 1.6)
python3 tools/sbom.py --verifier       # is it up to date? exit 1 if not
python3 tools/sbom.py --logiciel-seul  # also regenerates the software's
```

The firmware part reads its versions **from the files that are
authoritative** — `src/firmware/_make_.sh` for the Pico SDK and the ARM
toolchain, `CMakeLists.txt` for the libraries actually linked. Nothing is
copied by hand: a version written into a table would go stale in silence.

The ARM compiler and `picotool` carry `scope: excluded` there: they **build**
the product, they are not embedded in it. The distinction matters to whoever
reads this document in order to know whether a vulnerability concerns them.

> **A false SBOM is worse than no SBOM.** Its purpose is to answer "does this
> vulnerability concern me?". `.github/workflows/sbom.yml` regenerates it as
> soon as a change touches `src/phytoscope/`, and `security.yml` refuses to
> let it drift.

---

## 9. Publishing a version

```bash
# 1. the version, at the source
cd src/phytoscope
make bump-patch && make release-check

# 2. the tests, before anything else
make test                      # 385, no hardware and no network

# 3. the bills of materials
cd .. && python3 tools/sbom.py --ecrire --logiciel-seul

# 4-5. the packages AND the firmware, in the same build
cd packaging && make deliverables && make verify

# 6. the publications, if they changed
cd .. && git diff --name-only | python3 tools/impacted_pdfs.py -

# 7. the tag — it is what triggers the release
git tag -a v1.5.2 -m "PhytoScope 1.5.2"
git push --tags
```

The tag triggers `.github/workflows/release.yml`, which **checks that the
tag matches `VERSION`** — a tag that did not match would produce packages
stamped with a number nobody could find again — replays the tests, rebuilds
everything — **packages, firmware and publications** — **attests the
provenance** of every deliverable to GitHub (Sigstore), and publishes.

Whoever downloads can then check where a file came from:

```bash
gh attestation verify phytoscope_1.5.2_all.deb --repo thierryg/phytoscope
```

The CI signs the **provenance**; the publisher signs the **origin**. Both are
useful and neither replaces the other.

---

## 10. When it fails

### "makensis failed"

Most often: **out of disk space**. NSIS compresses ~500 MB in one go.

```bash
df -h .
make clean                    # empties build/packages
```

Otherwise the exact error shows if you raise the verbosity — `-V2` in
`build_windows.py` becomes `-V4`.

### "rpmbuild missing"

```bash
sudo apt install rpm
```

### "dependencies not installed" when installing the `.deb`

The installation **is not rolled back**: the software will say so at
start-up.

```bash
sudo dpkg-reconfigure phytoscope
phytoscope --check
```

### The `.deb` stops being produced

Look at `packaging/templates/debian/control`: **a `control` file admits no
comment.** A line beginning with `#` makes `dpkg-deb` fail with "field name
'#' must be followed by colon" — and `make all` carries on, producing the
other eight packages without a murmur. It happened on 2026-09-18;
`"control"` has been in `tools/headers.py`'s exclusions ever since.

### "no signing certificate"

See [§ 3](#3-the-signing-certificate). `make certificate`.

### The Windows packages weigh 275 MB — is that normal?

Yes. They bundle the Python interpreter and Qt, so as to require **nothing**
of the machine. The other systems rely on their own Python.

---

## 11. Every target

```
Preparation
  make tools                     what is installed, what is missing
  make deps                      install NSIS and msitools without sudo

One system
  make debian                    .deb and .run
  make fedora                    .rpm
  make windows                   .zip .exe .msi
  make macos                     .zip .pkg
  make source                    .tar.gz

Several
  make all                       the nine packages, signed
  make linux                     .deb .run .rpm
  make offline                   with the libraries bundled

Firmware
  make firmware                  build the .uf2 and file it with the rest
  make deliverables              the packages AND the firmware

Signing
  make certificate               create it, and fill certificate/
  make certificate-status        what exists, and where
  make certificate-verify        do both copies agree?
  make certificate-renew         REPLACE the key (breaks the link)
  make sign                      sign this build's packages
  make certificate-fingerprint   its SHA-256 fingerprint

Afterwards
  make documents                 readme, install, licence, changelog, checksums
  make verify                    reread and check what was produced
  make checksums                 recompute the .sha256 files
  make clean                     empty build/packages

  make version                   print the version that would be used
  make help                      this summary — and the default goal
```

---

## Where everything lives, in `packaging/`

```
Makefile               chains the targets
common.py              what depends on no particular system: identity,
                       copying the software, wheels, bundled interpreters
build.py               --outils, --deps, and the five generators below
build_debian.py        the .deb and the .run installer
build_fedora.py        the .rpm
build_windows.py       the .exe, the .msi, the portable archive
build_macos.py         the .app, the .zip, the .pkg
build_source.py        the .tar.gz
macos_pkg.py           the .pkg format, written end to end
signature.py           X.509 certificate, Authenticode, CMS
certificate.py         creates, recreates and installs the certificate
verify.py              reopens and checks what was produced
languages.py           the installers' labels, 11 languages
languages/             installateur.json — 104 labels × 11 languages
templates/             control, .spec, .nsi, .wxs, Info.plist, launchers
```

---

© 2026 Bretagne Namasté — Thierry GAYET · [bretagne-namaste.com](https://bretagne-namaste.com)
