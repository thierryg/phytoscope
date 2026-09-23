# 5. Testing your module

No running software, no hardware, no plant. This is the most useful thing the
SDK gives you.

```bash
python3 -m pytest my-module/ -v
```

---

## The principle

A module depends on nothing but `phytoscope.api`. It can therefore be
instantiated with a **fake context** — an object offering the same surface,
with nothing behind it — and a **manufactured signal**.

```python
instance = MyModule(FakeContext())
instance.setup()
quantities = instance.analyse(fake_signal(30.0), 250.0, instance.context)
```

---

## The fake context

Shipped with the generated tests. Copy it.

```python
class FakeContext:
    """The same surface as `Context`, with nothing behind it."""

    def __init__(self, settings=None):
        self.settings = dict(settings or {})
        self.subscriptions = {}
        self.logged = []
        self.rate_hz = 250.0
        self.full_scale_v = 2.5
        self.mains_hz = 50.0

    def subscribe(self, event, callback):
        self.subscriptions.setdefault(event, []).append(callback)

    def log(self, message, level="info"):
        self.logged.append(f"{level}: {message}")

    def message(self, text):
        self.logged.append(f"message: {text}")

    def translate(self, text):
        return text                  # the source language is enough in a test

    def directory(self):
        import tempfile
        return tempfile.mkdtemp(prefix="test-")

    def signal(self, seconds=60.0, raw=False):
        return fake_signal(seconds)

    def event_times(self):
        return []

    def state(self):
        from types import SimpleNamespace
        return SimpleNamespace(duration_s=120.0, source="test",
                               running=True, replaying=False)
```

> **If a test fails because a method is missing here**, that is a sign you are
> using a part of the interface which will also have to be tested. That is
> good news, not a nuisance.

---

## The test signal

```python
def fake_signal(seconds=30.0, fs=250.0):
    """Noise, a slow drift, and a few bursts of activity."""
    n = int(seconds * fs)
    t = np.arange(n) / fs
    r = np.random.default_rng(42)          # fixed seed: reproducible tests
    x = r.normal(0.0, 3e-6, n)             # background noise, 3 µV
    x += 4e-5 * np.sin(2 * np.pi * t / 400.0)      # slow drift
    for t0 in np.arange(5.0, seconds, 7.0):        # bursts
        x += 1.2e-4 * np.exp(-((t - t0) / 1.5) ** 2)
    return x
```

**Fixed seed.** A test that fails one time in ten is worse than no test at
all: it ends up being disabled, and the nine times it would have earned its
keep are lost with it.

### Signals for the edge cases

```python
np.zeros(0)                              # nothing received yet
np.zeros(1000)                           # a dead signal
np.full(1000, 2.5)                       # railed
np.random.default_rng(0).normal(0, 1, n) # an absurd amplitude
```

Your module must come through all four **without raising**.

---

## What to test

### The manifest

```python
def test_the_manifest_is_valid(instance):
    assert instance.MANIFEST.problems() == [], instance.MANIFEST.problems()

def test_the_manifest_targets_a_known_api(instance):
    from phytoscope.api import compatible
    assert compatible(instance.MANIFEST.api)
```

A rejected manifest, and your module is never loaded. This is the first test
to write, and the one that will save you an hour of looking in the wrong
place.

### The shape of what you return

```python
def test_every_quantity_explains_what_it_means(instance):
    for g in instance.analyse(fake_signal(), 250.0, instance.context):
        assert g.key and g.label
        assert g.text
        assert len(g.meaning) > 20, f"“{g.key}” explains nothing"
        assert np.isfinite(g.value)
```

### The edge cases

```python
def test_an_empty_signal_does_not_raise(instance):
    assert instance.analyse(np.zeros(0), 250.0, instance.context) == []

def test_a_railed_signal_does_not_raise(instance):
    instance.analyse(np.full(2000, 2.5), 250.0, instance.context)
```

### The settings

```python
def test_a_setting_turned_off_is_visible(module_class):
    context = FakeContext(settings={"show_detail": False})
    obj = module_class(context); obj.setup()
    keys = {g.key for g in obj.analyse(fake_signal(), 250.0, context)}
    assert "detail" not in keys
```

### The subscriptions

```python
def test_the_callback_counts_correctly(instance):
    from phytoscope.api import EVENT_DETECTED
    for callback in instance.context.subscriptions[EVENT_DETECTED]:
        callback(1.0, 1e-4)
        callback(2.0, 2e-4)
    ...
```

### The physics, where there is any

This is the most important part, and the most often left out. If your module
computes something, **check it against the pencil-and-paper result**:

```python
def test_the_noise_density_is_right(instance):
    """2 µV rms over a 125 Hz band gives 179 nV/√Hz."""
    fs = 250.0
    x = np.random.default_rng(0).normal(0, 2e-6, int(120 * fs))
    expected = 2e-6 / np.sqrt(fs / 2)
    obtained = next(g for g in instance.analyse(x, fs, instance.context)
                    if g.key == "density").value
    assert obtained == pytest.approx(expected, rel=0.10)
```

A test checking that a function "returns a number" checks nothing. A test
checking that the number is the right one checks everything.

---

## Testing several modules together

Name your test file **`test_<your-module>.py`**, not `test_module.py`. Two
files with the same name, in two directories without an `__init__.py`, cannot
be collected in the same pytest session.

The `new_module.py` tool does this for you.

---

## The module inside the real software

Once the tests pass, it remains to check that it really does load:

```bash
cp -r my-module ~/.config/phytoscope/modules/
phytoscope --check          # the pre-flight checks
phytoscope                  # Diagnostics tab → Modules
```

And to see your log lines:

```bash
tail -f ~/.config/phytoscope/phytoscope.log | grep my-module
```

---

**Next:** [6. Publishing](06-publishing.md)
