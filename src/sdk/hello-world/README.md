# Hello, world — the example module

The smallest PhytoScope module that does anything at all. Read
[`module.py`](module.py): it is written to be read from end to end, and then
copied.

## Trying it

```bash
# Linux
cp -r src/sdk/hello-world ~/.config/phytoscope/modules/
# macOS
cp -r src/sdk/hello-world ~/Library/Application\ Support/PhytoScope/modules/
# Windows
xcopy /E src\sdk\hello-world %APPDATA%\PhytoScope\modules\hello-world\
```

Restart PhytoScope. **Multimeter → Scientific quantities** tab: three more
rows. **Diagnostics → Modules** tab: your module in the list.

If nothing appears, Diagnostics says why in one sentence — an invalid
manifest, an unknown API version aimed at, a missing library, or a fault while
loading.

## The tests

```bash
python3 -m pytest src/sdk/hello-world/test_hello_world.py -v
```

The tests need **neither the software running nor any hardware**: they call
the module with a manufactured signal and a fake context. That is what makes
it possible to develop a module with no plant on the desk.

## Creating a new one

```bash
python3 src/sdk/tools/new_module.py my-module --capability analyseur
```

The tool creates the directory, the manifest, the skeleton and the tests.

## What to remember

| | |
|---|---|
| Import | only from `phytoscope.api` |
| Write | only inside `context.directory()` |
| Raise | never to say "nothing to report" — return an empty list |
| `meaning` | always filled in: what the number says, and what it does not |
| Callbacks | short: they run in the interface thread |
| Labels | templates (`"at {tau} s"`), never composed sentences |

---

*Bretagne Namasté — Thierry GAYET — https://bretagne-namaste.com — MIT licence*
