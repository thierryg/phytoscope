# 1. Getting started, step by step

From nothing at all to an installed module showing your own values. Allow ten
minutes.

---

## Step 0 — What you need

* **Python 3.9 or newer** — the one that runs PhytoScope will do.
* **PhytoScope installed**, or its source code. If you have the source, you
  already have everything.
* Something to run `pytest` with: `pip install pytest`.

You need **neither hardware nor a plant**. The software starts on its internal
generator, and a module's tests do not even require it to be running.

---

## Step 1 — Create the skeleton

```bash
python3 src/sdk/tools/new_module.py my-first-module
```

The tool creates a directory of three files:

```
my-first-module/
    module.py                    the skeleton — it already works
    test_my_first_module.py      five tests, which pass
    README.md                    how to install it, what is left to do
```

### Choosing the capability

By default the tool creates an **analyser**: the simplest, and the one whose
result shows up immediately. The others:

```bash
python3 src/sdk/tools/new_module.py my-module --capability descripteur
python3 src/sdk/tools/new_module.py my-module --capability sonificateur
python3 src/sdk/tools/new_module.py my-module --capability exportateur
```

| Capability | What it does | Where it shows up |
|---|---|---|
| `analyseur` | computes numbers | Multimeter → Scientific quantities |
| `descripteur` | produces a curve | Descriptors |
| `sonificateur` | makes notes | Listen — *not called yet* |
| `exportateur` | writes a format | Library — *not called yet* |

> **Start with `analyseur` or `descripteur`.** Those are the two the host
> actually asks the registry for, as of PhytoScope 1.5. A sonifier or an
> exporter loads and shows as active, but is never called — see
> [the five capabilities](03-capabilities.md).

### The other options

```bash
--title "My fine module"     what the user will read
--author "Your name"
--in /some/path              where to create the directory
--install                    create it directly in the modules directory
```

---

## Step 2 — Read what was created

Open `module.py`. It is short, and every part is commented. Three things to
look for:

### The manifest

```python
MANIFEST = Manifest(
    name="my-first-module",
    title="My first module",
    version="0.1.0",
    api="3.0",
    capabilities=(Capability.ANALYSER,),
)
```

This is the identity card. **It is read without running your code**: the
software extracts it by parsing the file. That is what lets it refuse a module
aimed at an unknown interface without having to run it to find out.

> **Consequence**: write literal values. `version="1.0.0"` is read;
> `version=read_my_version()` is not, and the default will apply.

> **`api` is a minimum.** `api="3.0"` means "I need 3.0 or later, same
> major" — the host accepts you on 3.1 and 3.7, and refuses you on 4.0 with a
> sentence naming both versions. Once loaded, `self.context.api_version` tells
> you what you actually got.

### The life cycle

```python
def setup(self):    # once, at start-up
def shutdown(self):      # once, at shutdown
```

`setup()` and not `__init__`: `__init__` is called for every module, one
after another, when the software launches. It must stay instantaneous.

### The capability

```python
def analyse(self, x, fs, context):
    ...
    return [Quantity(...)]
```

This is the work. `x` is the signal **in volts**, `fs` the actual rate.

---

## Step 3 — Test it

```bash
python3 -m pytest my-first-module/ -v
```

```
test_the_manifest_is_valid PASSED
test_the_manifest_targets_a_known_api PASSED
test_analyse_returns_complete_quantities PASSED
test_an_empty_signal_does_not_raise PASSED
test_shutdown_does_not_raise PASSED
```

Notice what these tests do **not** require: no running software, no board, no
plant. They build a plausible signal and a fake context, then call your code.

That is the most useful thing about the SDK: you can develop a module on a
train.

---

## Step 4 — Write something of your own

Replace the body of `analyse`. An example that means something: count how
often the signal crosses its own mean, which gives a rough idea of how agitated
it is.

```python
def analyse(self, x, fs, context):
    if x.size < 64:
        return []

    centre = x - x.mean()
    #  A zero crossing: two consecutive samples of opposite sign.
    passages = int(np.sum(np.diff(np.sign(centre)) != 0))
    par_minute = passages / (x.size / fs) * 60.0

    return [Quantity(
        key="mean-crossings",
        label="Crossings of the mean",
        value=par_minute,
        text=f"{par_minute:.0f} /min",
        meaning=("How many times a minute the signal crosses its own mean. It "
              "rises with high-frequency noise and falls when a slow drift "
              "dominates. It says nothing about the plant's activity in "
              "itself: a cable that moves produces the same effect."),
    )]
```

Run the tests again. They still pass — they check the **shape** of what you
return, not its value. Add one of your own:

```python
def test_the_count_rises_with_noise(instance):
    quiet = np.zeros(7500) + 1e-6
    lively = np.random.default_rng(0).normal(0, 3e-6, 7500)
    a = instance.analyse(quiet, 250.0, instance.context)[0].value
    b = instance.analyse(lively, 250.0, instance.context)[0].value
    assert b > a * 10
```

---

## Step 5 — Install it

```bash
# Linux
cp -r my-first-module ~/.config/phytoscope/modules/

# macOS
cp -r my-first-module ~/Library/Application\ Support/PhytoScope/modules/

# Windows
xcopy /E my-first-module %APPDATA%\PhytoScope\modules\my-first-module\
```

Or, right at creation:
`python3 src/sdk/tools/new_module.py my-module --install`

---

## Step 6 — See the result

Restart PhytoScope.

1. **Diagnostics → Modules tab.** Your module should be there, as `active`.
2. **Multimeter → Scientific quantities tab.** Your row appears among those of
   the shipped modules. Hover over it: your `meaning` appears.

---

## If nothing appears

Go to **Diagnostics → Modules**. It says in one sentence what happened. That
is the page to look at first, before doubting yourself.

| What it shows | What it means | What to do |
|---|---|---|
| absent from the list | the directory is in the wrong place, or there is no `module.py` | check the path |
| `incompatible` — needs at least API 2.0… | a module written for the old interface — see [migrating](08-migrating-from-2.0.md) | rename, and `api="3.0"` |
| `incompatible` — needs at least API 3.4 | your `api=` asks for a minor this host does not have | declare the lowest that suffices, and use `context.api_at_least()` for the rest |
| `incompatible` — library missing | your `requires=` demands something absent | the command is given on the spot |
| `incompatible` — invalid name | lowercase, digits and hyphens only | fix `name=` |
| `faulted` | your code raised | the traceback is in the log (<kbd>Ctrl+L</kbd>) |
| `disabled` | the user does not want it | Settings |

---

**Next:** [2. The interface, in detail](02-api.md)
