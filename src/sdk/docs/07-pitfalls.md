# 7. Pitfalls

What costs you an evening when you do not know about it. Every one of these is
real: each was met while writing the modules shipped with the software.

---

## The manifest is read without running your code

The software parses `module.py` to extract the manifest, **before** importing
it.

```python
#  NO — will not be read, and the default "0.1.0" will apply
MANIFEST = Manifest(name="my-module", version=read_my_version())

#  NO — the same
VERSION = "1.0.0"
MANIFEST = Manifest(name="my-module", version=VERSION)

#  YES
MANIFEST = Manifest(name="my-module", version="1.0.0")
```

Only the `Capability` constants are an exception, because they belong to the
contract:

```python
capabilities=(Capability.ANALYSER,)          # read correctly
capabilities=("analyser",)                 # also read, but less readable
capabilities=my_capabilities()              # NOT read
```

**Why it works this way:** listing the modules present, disabling one, and
refusing the one that aims at an unknown interface all require the manifest.
Obtaining it by running the module would mean trusting it before knowing
whether it deserves to be trusted.

---

## Never raise to say "nothing to report"

```python
#  NO — disables your module for the whole session
def analyse(self, x, fs, context):
    if x.size == 0:
        raise ValueError("no signal")

#  YES
def analyse(self, x, fs, context):
    if x.size == 0:
        return []
```

An exception, wherever it happens, **disables your module until the next
start-up**. That is deliberate: a module that fails once will most likely fail
again, and letting it through would produce the same traceback every two
seconds.

---

## Do nothing lengthy in `__init__`

```python
#  NO — delays the start-up of EVERY module
def __init__(self, context):
    super().__init__(context)
    self._table = load_ten_megabytes()

#  YES
def setup(self):
    self._table = load_ten_megabytes()

#  BETTER — on first use
def analyse(self, x, fs, context):
    if self._table is None:
        self._table = load_ten_megabytes()
```

---

## Labels containing a number must be templates

```python
#  NO — this sentence cannot go into any translation catalogue
Quantity(label=f"Allan deviation at {tau} s", ...)

#  YES
Quantity(label="Allan deviation at {tau} s",
         params={"tau": f"{tau:g}"}, ...)
```

The interface **translates first and fills in afterwards**. A label with the
number already embedded cannot be translated: it will stay in English in all
the other languages.

---

## `text` holds unit symbols only

```python
text="+37.2 dB"                        # YES — symbols are international
text="+37.2 dB above the floor"        # NO — "above the floor" will stay
                                        #      in English everywhere
```

Words belong in `label` or in `meaning`, which are translated. This pitfall is
all the easier to fall into because it is invisible from an English interface.

---

## Filtering before measuring noise

```python
RAW_SIGNAL = False     # NO, if you are measuring noise
```

The processed signal has been through the mains notch and the 40 Hz low-pass.
Measuring noise on it amounts to **measuring your own filter**: the mains
residue has been removed, and so has the band in which thermal noise is read.

```python
RAW_SIGNAL = True      # for any noise measurement
```

---

## Writing anywhere but at home

```python
#  NO — the session directory belongs to the user
path = os.path.join(session, "my-file.txt")

#  YES
path = os.path.join(self.context.directory(), "my-file.txt")
```

Nothing stops you technically. But a module that litters the sessions
directory will be uninstalled, and rightly so.

---

## Event callbacks must be short

```python
#  NO — you are in the interface thread
def _sur_evenement(self, instant_s, amplitude_v):
    self._recompute_the_whole_spectrum()

#  YES — note it down, compute elsewhere
def _sur_evenement(self, instant_s, amplitude_v):
    self._pending.append((instant_s, amplitude_v))
```

Thirty milliseconds at every event, on an active plant, shows on screen.

---

## A callback that raises is unsubscribed, for good

If your module "stops reacting" after a few minutes, look at the log: you will
find the fault there, and the time at which it was disconnected.

This is not a punishment: leaving a faulty subscriber connected would drown
the log under the same traceback — the very log one needs in order to
understand.

---

## Import from `phytoscope.api` and nowhere else

```python
#  NO — will break without notice, and we shall not know
from phytoscope.core.engine import Engine
from phytoscope.core.analysis import spectre

#  YES
from phytoscope.api import Analyser, Quantity, Manifest, Module
```

The engine changes with every version. `phytoscope.api` does not change as
long as the major does not — that is the whole difference, and it is written
into the contract.

If something you need is missing from the interface, **say so**: that is
precisely how it will grow.

---

## Two test files with the same name

```
my-module/test_module.py
other-module/test_module.py     ← pytest refuses to collect both
```

Name them `test_<your-module>.py`. The `new_module.py` tool does it for you.

---

## Forgetting `meaning`

```python
#  Loaded all the same — but the interface will write, on your behalf:
#  "the module “my-module” does not explain this value"
Quantity(key="x", label="X", value=1.0, text="1")
```

A number without its interpretation is an invitation to get it wrong.
"618 kΩ" means nothing unless one knows it is an upper bound derived from
noise, and not a resistance read off an ohmmeter.

---

## Summary

| The pitfall | The symptom | The rule |
|---|---|---|
| a computed manifest | the defaults apply | use literals |
| raising for "nothing" | module disabled | return `[]` |
| a lengthy `__init__` | slow start-up | `setup()` |
| a label that is not a template | untranslatable | `{param}` + `params` |
| words in `text` | English everywhere | symbols only |
| the processed signal for noise | you measure your filter | `RAW_SIGNAL = True` |
| writing elsewhere | module uninstalled | `context.directory()` |
| a lengthy callback | a jerky display | note it down, compute elsewhere |
| importing outside the API | breaks on update | `phytoscope.api` |
| no `meaning` | the interface tells on you | always write it |

---

**Back:** [the SDK README](../README.md)
