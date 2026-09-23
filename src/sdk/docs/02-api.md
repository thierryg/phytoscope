# 2. The interface, in detail

Everything a module imports comes from `phytoscope.api`, and from nowhere
else. **What is not in that file is not part of the interface**: it may change
from one version to the next without notice.

```python
from phytoscope.api import (
    # the contract
    API_VERSION, compatible, Manifest, Module, Capability,
    # the capabilities
    Analyser, Descriptor, Sonifier, Exporter, Source,
    # what they exchange
    Quantity, Trace, ProposedNote,
    # what you are given
    Context, MeasurementState,
    # the events
    BUS, EVENTS, MEASUREMENT_STARTED, EVENT_DETECTED, ...,
)
```

---

## `API_VERSION` and the compatibility promise

```python
API_VERSION = "3.0"
```

Semantic numbering:

| | |
|---|---|
| **major** | a promise is broken — an older module stops working |
| **minor** | a capability or a parameter is added, breaking nothing |
| **patch** | a clarification of behaviour, never of shape |

What `compatible()` actually answers on a 3.0 host:

```python
compatible("3.0")      # True  — same major, and the host knows this minor
compatible("3.1")      # False — the host does not know 3.1 yet
compatible("2.0")      # False — different major
compatible("4.0")      # False — different major
```

**The promise:** as long as the major does not change, a module written today
will go on working. Things can be added; nothing can be taken away.

A module declaring `api="3.0"` runs on any host whose API is `3.0` or a later
`3.x`. It does not run on `4.x`, and the software will say so rather than
failing in the middle of a session.

> **Coming from 2.0?** Every name on this page changed on 2026-09-23, and a
> module written against 2.0 is refused at discovery rather than half-loaded.
> The table is in [Migrating from 2.0](08-migrating-from-2.0.md).

### The version contract goes both ways

`api` in your manifest is a **minimum**, and the host reads it as one. The
question can be asked from either side, and both sides go through the same
parser — so the two answers cannot drift apart.

**You, asking what you are running on:**

```python
context.api_version          # "3.0" — the host's API version
context.api_required         # "3.0" — what YOUR manifest asked for
context.api_at_least("3.2")  # bool — same major, minor at least
```

**The host, asking what you need:**

```python
manifest.api                 # "3.0" — the minimum, as you wrote it
manifest.api_required        # (3, 0) — the same, parsed
manifest.api_satisfied_by    # "API 3.0 or any later 3.x" — for Diagnostics
registry.api_requirements()  # {"my-module": (3, 0), …} for every module
```

And the parser itself, because neither side should write its own:

```python
from phytoscope.api import parse_version
parse_version("3.1")     # (3, 1)
parse_version("3.1.4")   # (3, 1) — the patch never decides
parse_version("three")   # (-1, -1) — and `compatible()` then refuses
```

> **Why `api_at_least()` matters.** Declare the **lowest** version that
> actually suffices, and ask at run time for anything newer you would merely
> *like*:
>
> ```python
> def analyse(self, x, fs, context):
>     if context.api_at_least("3.2"):
>         return self._with_the_field_added_in_3_2(x, fs, context)
>     return self._the_way_that_works_on_3_0(x, fs, context)
> ```
>
> A module that declares `api="3.2"` because that is what its author had
> installed is a module refused on every 3.0 and 3.1 host, for nothing. The
> manifest states what you *need*; the context tells you what you *got*.

---

## `Manifest`

The identity card. **Read without running your code** — see
[the pitfalls](07-pitfalls.md#the-manifest-is-read-without-running-your-code).

```python
Manifest(
    name="my-module",
    title="My module",
    version="1.0.0",
    api="3.0",
    description="",
    author="",
    licence="",
    website="",
    capabilities=(),
    depends_on=(),
    requires=(),
)
```

### The fields

| Field | Type | Default | Role |
|---|---|---|---|
| `name` | `str` | *required* | the identifier: `^[a-z][a-z0-9-]{1,48}$`. Used as the key for settings |
| `title` | `str` | the name | what the user reads |
| `version` | `str` | `"0.1.0"` | yours, semantic |
| `api` | `str` | the current one | the **minimum** interface version you need. Accepted on any later minor of the same major |
| `description` | `str` | `""` | one sentence, shown in Diagnostics |
| `author` | `str` | `""` | |
| `licence` | `str` | `""` | |
| `website` | `str` | `""` | |
| `capabilities` | `tuple[str]` | `()` | **declarative**: what is not listed is not offered, even if the method exists |
| `depends_on` | `tuple[str]` | `()` | the modules loaded before yours, by their `name` |
| `requires` | `tuple[str]` | `()` | the Python libraries. Checked **before** the import |

### The methods

```python
manifest.valid              # bool — does the name match the required shape?
manifest.problems()         # list[str] — what prevents acceptance, in words
manifest.api_required       # (major, minor) — the minimum, parsed
manifest.api_satisfied_by   # str — "API 3.0 or any later 3.x"
manifest.to_dict()          # dict
```

`problems()` is what Diagnostics displays. Call it in your tests:

```python
def test_the_manifest_is_valid(instance):
    assert instance.MANIFEST.problems() == [], instance.MANIFEST.problems()
```

### `Capability`

Constants, to avoid hardcoded strings:

```python
Capability.ANALYSER      # "analyser"
Capability.DESCRIPTOR    # "descriptor"
Capability.SONIFIER   # "sonifier"
Capability.EXPORTER    # "exporter"
Capability.SOURCE         # "source"
Capability.ALL         # the tuple of all five
```

---

## `Module`

What every module inherits from. **Only `MANIFEST` is required**; everything
else has a default behaviour that does nothing.

```python
class Module:
    MANIFEST: Manifest

    def __init__(self, context: Context) -> None
    def setup(self) -> None
    def shutdown(self) -> None
    def default_settings(self) -> dict
```

### `__init__(context)`

Called at load time. `self.context` is set for you.

> **Do nothing lengthy here.** This is called for every module, one after
> another, as the software starts. A second here is a second more before the
> user sees anything at all.

### `setup()`

Once, **after** every module has been loaded. This is where you subscribe and
prepare your files.

Why after all the others: if your module depends on another (`depends_on`), that
one is already loaded when you are called.

### `shutdown()`

Once, at shutdown. Close what you opened. **Your subscriptions are removed for
you**: there is no need to deal with them.

### `default_settings()`

```python
def default_settings(self):
    return {"seuil_uv": 8.0, "montrer_le_detail": True}
```

The software keeps them under your module's name and hands them back through
`context.settings`. **Never write into the software's own settings file**: it
is not yours, and its shape may change.

---

## `Context`

What your module is given. **You are never given the engine object**: that is
deliberate, and it is what makes the interface sustainable over time.

### Which API you are running on

```python
context.api_version            # str — the host's API version
context.api_required           # str — the minimum your manifest declared
context.api_at_least("3.2")    # bool
```

See [the version contract](#the-version-contract-goes-both-ways) above. The
short of it: declare the lowest you need, and ask here for anything newer you
would only like to have.

### Reading the signal

```python
context.signal(seconds=60.0, raw=False) -> np.ndarray
```

The last N seconds, **in volts**, in chronological order. Returns an empty
array when there is nothing yet — that is not an error, it is the situation at
start-up, and your module must expect it.

`raw=True` gives the signal **before** the notch filter and the low-pass.

> **When to use the raw signal:** for any noise measurement. Filtering before
> measuring noise amounts to measuring your own filter — the notch would erase
> the mains residue, and the 40 Hz low-pass would erase the band in which
> thermal noise is read.
>
> **When to use the processed signal:** to analyse the plant's *activity*
> rather than the measurement chain.

### The measurement's parameters

```python
context.rate_hz       # float — the actual rate
context.full_scale_v   # float — the converter's full scale
context.mains_hz          # float — 50 or 60, per the settings
```

### The state

```python
state = context.state()      # MeasurementState — a copy, never a reference
```

| Field | Type | |
|---|---|---|
| `running` | `bool` | the acquisition is running |
| `source` | `str` | the source's name |
| `duration_s` | `float` | since the session began |
| `rate_hz` | `float` | |
| `value_v` | `float` | the instantaneous value |
| `baseline_v` | `float` | |
| `rms_v` | `float` | |
| `pp_v` | `float` | |
| `drift_v_per_min` | `float` | |
| `saturated` | `bool` | the converter is railed |
| `events` | `int` | since the beginning |
| `notes` | `int` | |
| `recording` | `bool` | a session is being written |
| `replaying` | `bool` | **a recording is being replayed; nothing is being measured** |

> `replaying` deserves attention: a module that writes anywhere must know when
> it is not measuring.

```python
context.event_times()   # list[float] — seconds since the beginning
```

### Writing

```python
context.directory()    # str — your directory, created if needed
```

`<configuration>/modules/<your-name>/`. It survives updates and is never
erased by the software.

> **Write here, and only here.** Nothing stops you technically — this is
> Python, not a prison. But the sessions directory belongs to the user, and the
> software's own belongs to the software.

### Saying something

```python
context.log("what happened", level="info")   # debug|info|warning|error
context.message("visible in the status bar")
context.translate("a label")
```

`log()` writes under your module's name: your lines are found by searching
for `module.<your-name>`.

`message()` **sparingly**: a module that talks constantly ends up not being
read at all.

### Subscribing

```python
context.subscribe(EVENT_DETECTED, self._sur_evenement)
```

See [4. Events](04-events.md).

---

## `Quantity`

What an analyser returns.

```python
Quantity(
    key="my-indicator",         # identifier, stable across versions
    label="My indicator",     # a TEMPLATE if a number appears in it
    value=3.14,                # the number, always finite
    text="3.14 µV",            # the formatted value, unit included
    meaning="What this number says, and what it does not say.",
    alert=False,               # True → shown in red
    params={},                  # the template's values
)
```

### `meaning` is not decorative

The software requires every displayed value to say what it means **and what it
does not allow one to conclude**. A module that does not explain it is still
loaded, but the interface writes *"this module does not explain this value"* —
which gets noticed.

### `label` and `params`: the templates

A label containing a number must be a **template**:

```python
#  NO — this sentence cannot go into a translation catalogue
Quantity(label=f"Allan deviation at {tau} s", ...)

#  YES
Quantity(label="Allan deviation at {tau} s", params={"tau": f"{tau:g}"}, ...)
```

The interface translates **and then** fills the holes. A sentence with the
number already embedded cannot be translated.

### `text`: symbols, not words

```python
text="+37.2 dB"                       # YES
text="+37.2 dB above the floor"       # NO — stays in one language everywhere
```

Unit symbols are international; words belong in `label` or `meaning`, which are
translated.

---

## `Trace`

What a descriptor returns.

```python
Trace(
    x=np.ndarray, y=np.ndarray,   # the same length, or ValueError
    title="",
    x_label="", y_label="",
    x_log=False, y_log=False,
    warning="",             # shown under the curve
)
```

`warning` plays the part of `meaning`: what the view assumes, and what it
does not allow one to conclude.

---

## `ProposedNote`

What a sonifier returns. **The host decides whether to play it.**

```python
ProposedNote(
    midi_pitch=60,    # 0–127
    velocity=80,        # 0–127
    duration_s=0.4,
    channel=0,
    source_v=0.0,      # the measured value that produced this note
)
```

`source_v` is kept in the rendering. A sonification from which one can no
longer get back to the measurement is no longer a measurement.

---

**Next:** [3. The five capabilities](03-capabilities.md)
