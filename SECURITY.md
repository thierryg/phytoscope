# Security policy

## Reporting a vulnerability

**Do not open a public issue for a security problem.** An issue is visible to
everybody, including whoever would like to use it before the fix exists.

Write to **contact@bretagne-namaste.com**, with `[security]` in the subject.
If you can, use GitHub's private advisory instead: the *Security* tab →
*Report a vulnerability*.

Please state:

- what the flaw does, and what it lets someone obtain;
- the version affected (`phytoscope --version`, or the contents of
  `src/phytoscope/phytoscope/VERSION`);
- the operating system and the Python version;
- enough to reproduce it — the shortest sequence of actions, an example file;
- whether it is already known elsewhere (a CVE, an upstream advisory).

### What you can expect

| Step | Target |
|---|---|
| Acknowledgement | 5 working days |
| First assessment (is it in scope? how serious?) | 15 days |
| A fix, or an announced schedule | 60 days |
| Coordinated publication of the advisory | after the fix, with your agreement |

This project is carried by a small outfit: those are a commitment of effort,
not a service contract. You will be credited in the advisory and in
`CHANGELOG.md` if you wish.

## Versions supported

Only the **latest published version** receives security fixes. The current
one is in `src/phytoscope/phytoscope/VERSION`.

## Scope

### In scope

- the software, `src/phytoscope/` (Python, Qt);
- the firmware, `src/firmware/` (RP2350, C);
- the package factory, `packaging/` — in particular the **signing** chain
  (`packaging/signature.py`) and the package verification;
- the tools in `tools/` and the scripts that build the books.

### Out of scope

- the fact that a **self-signed certificate silences neither SmartScreen nor
  Gatekeeper**. That is not a flaw, it is the expected behaviour, and it is
  written out in `packaging/README.md` (constraint `C-2Q`);
- third-party repositories copied under `sources/`: report the flaw
  **upstream**, to the project concerned, then tell us so that we can update;
- the documents and books (`pdf-src/`, `build/`): a mistake in the content is
  not a vulnerability — open an ordinary issue.

## The one secret that matters in this repository: the signing key

The private key that signs the packages **is not in the repository and must
never enter it**.

- its reference copy lives in `~/.local/share/phytoscope-signature/`;
- `certificate/phytoscope.key` is a working copy, **excluded by
  `.gitignore`** (constraint `C-2R`);
- the **public** X.509 certificate (`certificate/phytoscope-certificate.pem`,
  `certificate/phytoscope.crt`) is version-controlled: it is what lets anyone
  verify a signature, and it is meant to be distributed.

`.gitignore` protects against `git`, **not against a backup or an archive of
the directory**. See `certificate/README.md`.

If you believe the key has leaked: write to the address above, urgently. The
course of action is to revoke, regenerate, and republish the packages with
new checksums.

### Checking that no secret has entered the repository

```bash
# What git tracks that looks like a key
git ls-files | grep -Ei '\.(key|pem|p12|pfx|jks|keystore|asc|gpg)$'
# → only certificate/phytoscope-certificate.pem and certificate/phytoscope.crt
#   (both public) should appear.

# The local guard, installed by pre-commit
pre-commit run --all-files detect-signing-key
```

## Checking a package is authentic

Every published package comes with its checksum (`.sha256`) and its detached
CMS signature (`.p7s`). The procedure is in the `AUTHENTICITE.txt` file
shipped alongside them, and the whole verification runs again with:

```bash
cd packaging && make verify
```

## What the project does for its own security

- **no mandatory dependency** added lightly (constraint `C-40`);
- **no `sudo`**: everything installs in the home directory (`C-55`);
- a **software bill of materials** (SBOM, CycloneDX) version-controlled in
  `src/phytoscope/sbom.cdx.json`, regenerated with
  `.venv/bin/python tools/sbom.py --json`;
- continuous integration runs `ruff`, `bandit`, `pip-audit`, `gitleaks` and
  the test suite on every push (see `.github/workflows/`);
- dependency updates arrive through Dependabot
  (`.github/dependabot.yml`).
