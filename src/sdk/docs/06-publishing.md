# 6. Publishing your module

Three ways to distribute one, from the simplest to the most formal.

---

## 1. A directory

The simplest, and often enough. Compress the directory and publish it.

```bash
tar czf my-module-1.0.0.tar.gz my-module/
```

The user unpacks it into their modules directory:

| System | Directory |
|---|---|
| Linux | `~/.config/phytoscope/modules/` |
| macOS | `~/Library/Application Support/PhytoScope/modules/` |
| Windows | `%APPDATA%\PhytoScope\modules\` |

**Publish the checksum alongside it** — this is code that will run on someone
else's machine:

```bash
sha256sum my-module-1.0.0.tar.gz > my-module-1.0.0.tar.gz.sha256
```

---

## 2. A Git repository

```
my-module/
    module.py
    test_my_module.py
    README.md
    LICENSE.txt
    CHANGELOG.md
```

The user clones straight into their modules directory:

```bash
git clone https://… ~/.config/phytoscope/modules/my-module
```

What a module's `README.md` has to say, in this order:

1. **what the module does, in one sentence**;
2. **what it does not do** — the question everyone will ask;
3. how to install it;
4. the settings, with their default values;
5. the interface version aimed at, and the compatible PhytoScope versions;
6. the licence.

---

## 3. A Python package

For distributing on PyPI. Declare an entry point:

```toml
# pyproject.toml
[project]
name = "phytoscope-my-module"
version = "1.0.0"
dependencies = ["numpy>=1.24"]

[project.entry-points."phytoscope.modules"]
my-module = "phytoscope_my_module:MyModule"
```

```bash
pip install phytoscope-my-module
```

The software discovers entry points at start-up, as well as the directories.

> **The package name** is better off starting with `phytoscope-`: it makes it
> findable, and says at once what it is for.

---

## Versioning

### Your version

Semantic numbering, as everywhere:

| | |
|---|---|
| **major** | a setting disappears, a behaviour changes |
| **minor** | a quantity is added, a setting appears |
| **patch** | a fix, with nothing visible changing |

### The interface version aimed at

```python
api="3.0"
```

**Aim for the lowest that will do.** A module declaring `api="3.0"` runs on
every `3.x` version; a module declaring `api="3.3"` refuses to run on a 3.2,
even though it uses nothing new.

Only raise that number the day you actually *need* something added in that
version — and if you merely want it, ask at run time instead:

```python
if context.api_at_least("3.2"):
    ...                      # use it
else:
    ...                      # do without, and still load on a 3.0 host
```

`api` is a **minimum**, and the host reads it as one: it accepts your module
on any later minor of the same major, and refuses it on any other major with
a sentence naming both versions. See
[the version contract](02-api.md#the-version-contract-goes-both-ways).

---

## The compatibility contract

What we promise, as long as the major of `API_VERSION` does not change:

* the existing classes, methods and fields **stay**;
* their behaviour **does not change**;
* we may **add** capabilities, fields and events.

What we do not promise:

* that anything outside `phytoscope.api` will stay. If your module imports
  `phytoscope.core.something`, it will break, and we will not even know.

The day a break becomes necessary — and it will — the major will change, the
software will refuse to load the older modules **while saying so clearly**,
and the documentation will explain the migration.

---

## A checklist before publishing

- [ ] `MANIFEST.problems()` returns an empty list
- [ ] the tests pass: `python3 -m pytest my-module/ -v`
- [ ] the module comes through the edge cases without raising: empty, dead and railed signals
- [ ] every `Quantity` has a `meaning` saying what it does not allow one to conclude
- [ ] labels containing a number are **templates**, with `params`
- [ ] `text` holds unit symbols only, no words
- [ ] the module writes nowhere but in `context.directory()`
- [ ] the event callbacks are short
- [ ] `author` and `licence` are filled in, in the manifest
- [ ] the `README` says what the module **does not** do
- [ ] the SHA-256 checksum accompanies the archive

---

**Next:** [7. Pitfalls](07-pitfalls.md)
