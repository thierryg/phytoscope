# 3. The five capabilities

A capability is what your module knows how to do. You declare one, several, or
none — a module that acts only at install and shutdown is perfectly
legitimate.

| Capability | Called | Time constraint | Shows up in | Called today? |
|---|---|---|---|---|
| [Analyser](#analyser) | every 2 s, while the page is visible | a few tens of ms | Multimeter | **yes** |
| [Descriptor](#descriptor) | on demand | a second is fine | Descriptors | **yes** |
| [Sonifier](#sonifier) | on every event | **very short** | Listen | not yet |
| [Exporter](#exporter) | on demand | none | Library | not yet |
| [Source](#source) | continuously | **critical** | Settings | not yet |

> **Three of the five are not consumed yet, as of PhytoScope 1.5.** The
> contract declares them, the registry records them, a manifest that announces
> them is accepted — but nothing in the host asks the registry for them. Only
> `providers(Capability.ANALYSER)`, in `ui/tabs.py`, and
> `providers(Capability.DESCRIPTOR)`, in `ui/features_tab.py`, are called.
>
> Concretely: a sonifier, an exporter or a source you write today will load,
> will show as `active` in Diagnostics, and will never be called. The shipped
> `export-csv` module is in exactly that position.
>
> We would rather say so here than let you spend an evening looking for the
> mistake in your own code. The two capabilities above are the ones to write
> against today; the three others are described because the contract already
> honours them, and a module written against them will start working the day
> the host asks for it — without changing.

---

## Analyser

Computes quantities over a window of signal.

```python
from phytoscope.api import Analyser, Capability, Quantity, Manifest, Module

class MyAnalysis(Module, Analyser):
    MANIFEST = Manifest(name="my-analysis", api="3.0",
                        capabilities=(Capability.ANALYSER,))

    WINDOW_S = 60.0        # how many seconds you want
    RAW_SIGNAL = True      # before the notch and the low-pass

    def analyse(self, x, fs, context):
        if x.size < 64:
            return []       # "nothing to say" — never an exception
        return [Quantity(
            key="standard-deviation",
            label="Standard deviation",
            value=float(np.std(x)),
            text=f"{np.std(x) * 1e6:.2f} µV",
            meaning=("The signal's spread about its mean. It grows with noise "
                  "AND with activity: it does not let you tell one from the "
                  "other."),
        )]
```

### `WINDOW_S` and `RAW_SIGNAL`

```python
WINDOW_S = 60.0        # the host gives what it has, never more
RAW_SIGNAL = True
```

**Raw** = before the mains notch and the low-pass. That is what any noise
measurement needs: *filtering before measuring noise amounts to measuring your
own filter*. The notch would erase the mains residue that is precisely what one
wants to see; the 40 Hz low-pass would erase the band in which thermal noise is
read.

**Processed** = what is seen on screen. For analysing *activity* rather than
the measurement chain.

### An example that means something

Estimating the source's resistance from thermal noise:

```python
BOLTZMANN = 1.380649e-23
TEMPERATURE_K = 293.15          # 20 °C

def analyse(self, x, fs, context):
    if x.size < int(10 * fs):
        return []

    #  The noise density is read ABOVE the biological band, where the plant
    #  produces nothing any more. Otherwise its activity would be counted as
    #  noise, and the result would mean nothing at all.
    spectre = np.abs(np.fft.rfft(x - x.mean())) ** 2
    freqs = np.fft.rfftfreq(x.size, 1 / fs)
    bande = (freqs > 10.0) & (freqs < min(40.0, fs / 2.5))
    densite = np.sqrt(np.mean(spectre[bande]) * 2 / (fs * x.size))

    resistance = densite ** 2 / (4 * BOLTZMANN * TEMPERATURE_K)

    return [Quantity(
        key="equivalent-resistance",
        label="Equivalent resistance",
        value=resistance,
        text=f"{resistance / 1e6:.2f} MΩ",
        meaning=("Derived from Johnson-Nyquist thermal noise, R = Sᵥ / 4kT. It "
              "is an UPPER BOUND, not an ohmmeter reading: the amplifier's "
              "own noise adds to it. It is its VARIATION that informs — a "
              "contact drying out pushes it up by a decade."),
        alert=resistance > 5e6,
    )]
```

Notice the `meaning`: it says what the number is worth **and** what it is not.
That is what separates a measurement from an impression.

---

## Descriptor

Produces a representation — a curve, a spectrum, an energy map.

```python
def describe(self, x, fs, context):
    if x.size < 64:
        return []
    spectre = np.abs(np.fft.rfft(x - x.mean()))
    freqs = np.fft.rfftfreq(x.size, 1 / fs)
    return [Trace(
        x=freqs[1:], y=20 * np.log10(np.maximum(spectre[1:], 1e-15)),
        title=context.translate("My spectrum"),
        x_label=context.translate("frequency (Hz)"),
        y_label="dB",
        x_log=True,
        warning=context.translate(
            "Assumes the signal is stationary over the window analysed, "
            "which is rarely true for long on a plant signal."),
    )]
```

This is not a critical path: the user asked for the view and is waiting. A
second of computation is fine.

`Trace` checks that `x` and `y` have the same length, and raises otherwise —
which is better than a curve that is silently wrong.

---

## Sonifier

Turns a measured value into notes.

```python
def sonify(self, value_v, context):
    gamme = (0, 2, 4, 5, 7, 9, 11)          # diatonic major
    rang = int(abs(value_v) * 1e6) % len(gamme)
    octave = min(int(abs(value_v) * 1e5), 3)
    return [ProposedNote(
        midi_pitch=48 + 12 * octave + gamme[rang],
        velocity=min(40 + int(abs(value_v) * 5e5), 110),
        duration_s=0.4,
        source_v=value_v,     # where this note came from
    )]
```

> **Be quick.** You are inside the musical rendering loop. No spectral
> computation here, no disk access, no network request.

Returning an empty list means "no note for this value". That is a legitimate
answer, and often the right one: not every variation deserves to be heard.

---

## Exporter

Writes a session in another format.

```python
FORMAT = "My format (.xyz)"    # what appears in the list
EXTENSION = ".xyz"

def export(self, session, target, context):
    """`session`: the directory to READ. `target`: the file to WRITE."""
    source = os.path.join(session, "mesures.csv")
    if not os.path.exists(source):
        context.log(f"“{source}” not found", "warning")
        return False        # false, not an exception

    with open(source, encoding="utf-8", newline="") as entree, \
         open(target, "w", encoding="utf-8", newline="") as sortie:
        ...
    return True
```

### What a session contains

```
2026-09-18_143000_basil/
    signal.wav          the raw signal, 24 bits, at the actual rate
    mesures.csv         t, voltage, baseline, noise, drift, events
    evenements.csv      instant, amplitude, duration
    notes.csv           instant, MIDI pitch, velocity, originating value
    enonces.csv         voice mode, with the values that triggered it
    seance.json         plant, place, rate, FULL SCALE, settings
    musique.wav         the audio rendering
```

> **`seance.json` contains the full scale.** If your format loses that
> information, it produces a pretty and unusable file. Copy it across.

### Write only into `target`

The session directory belongs to the user. If you need to write several files,
derive them from `target`:

```python
os.path.splitext(target)[0] + "-metadata.json"
```

---

## Source

Supplies a measurement stream. **The most delicate one.**

```python
LABEL = "My board"        # in the list of acquisition sources

def open(self, context):
    self._port = ...
    return True             # false if the open failed

def read(self):
    """A block of samples IN VOLTS, or None when there is nothing."""
    raw = self._port.read(...)
    return np.frombuffer(raw, dtype=np.int32) * self._volts_par_unite

def close(self):
    self._port.close()
```

> **You are on the data path.** The software isolates you from faults, but it
> cannot isolate you from the time you take. A slow source drops samples, and
> that cannot be made up for.
>
> Concretely: no allocation in `read()`, no logging per block, no computation.
> You read and you return.

### Converting to volts

`read()` returns **volts**, not arbitrary units. You are the one who knows your
hardware's calibration; the software cannot guess it, and a signal without a
scale is not a measurement.

---

## Providing several capabilities

```python
class MyModule(Module, Analyser, Descriptor):
    MANIFEST = Manifest(
        name="my-module", api="3.0",
        capabilities=(Capability.ANALYSER, Capability.DESCRIPTOR),
    )

    def analyse(self, x, fs, context): ...
    def describe(self, x, fs, context): ...
```

Careful: `WINDOW_S` and `RAW_SIGNAL` are **shared** by both. If your two
capabilities have different needs, write two modules — they can share code
through a neighbouring file.

---

**Next:** [4. Events](04-events.md)
