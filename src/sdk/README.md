# PhytoScope SDK

What you need in order to write a module: the documentation, a complete
example, and a tool that creates a skeleton which already works.

```
sdk/
  README.md            this file
  docs/                the documentation, step by step
  hello-world/         the complete example, with its tests
  tools/
    new_module.py      creates a module ready to be tested
```

## In three commands

```bash
python3 src/sdk/tools/new_module.py my-module      # create
python3 -m pytest my-module/ -v                    # test
cp -r my-module ~/.config/phytoscope/modules/      # install
```

Restart PhytoScope: your values appear in the **Multimeter → Scientific
quantities** tab, and the module shows up in **Diagnostics → Modules**.

## The documentation

| | |
|---|---|
| [1. Getting started, step by step](docs/01-getting-started.md) | from nothing to an installed module |
| [2. The interface, in detail](docs/02-api.md) | every class, every field, every method |
| [3. The five capabilities](docs/03-capabilities.md) | analyse, describe, sonify, export, measure |
| [4. Events](docs/04-events.md) | subscribing to what happens |
| [5. Testing your module](docs/05-testing.md) | with no software and no hardware |
| [6. Publishing](docs/06-publishing.md) | distributing, versioning, packaging |
| [7. Pitfalls](docs/07-pitfalls.md) | what costs you an evening when you do not know it |
| [8. Migrating from 2.0](docs/08-migrating-from-2.0.md) | every name that changed, and why nothing is aliased |

The same content, laid out for print, is in
`build/writing-a-phytoscope-module.pdf` (`python3 pdf-src/build_sdk.py`).

## What to remember

| | |
|---|---|
| Import | only from `phytoscope.api` |
| Write | only inside `context.directory()` |
| Raise | never to say "nothing to report" — return an empty list |
| `meaning` | always filled in: what the number says, and what it does not |
| Callbacks | short: they run in the interface thread |
| Labels | templates (`"at {tau} s"`), never composed sentences |
| Manifest | literal values: it is read without running your code |
| API | `3.0` since 2026-09-23 — a 2.0 module is refused, not half-loaded |
| `api=` | a **minimum**: declare the lowest that suffices, then ask `context.api_at_least()` |

---

*Bretagne Namasté — Thierry GAYET — https://bretagne-namaste.com — MIT licence*
