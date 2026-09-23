# 4. Events

A module does not poll the software in a loop: it says what interests it, and
the host calls it. That is the only way to have modules that cost nothing when
nothing is happening.

```python
from phytoscope.api import EVENT_DETECTED

def setup(self):
    self._compte = 0
    self.context.subscribe(EVENT_DETECTED, self._sur_evenement)

def _sur_evenement(self, instant_s, amplitude_v):
    self._compte += 1
```

---

## The complete list

| Constant | String | The callback receives |
|---|---|---|
| `MEASUREMENT_STARTED` | `measurement.started` | `(state: MeasurementState)` |
| `MEASUREMENT_STOPPED` | `measurement.stopped` | `(state: MeasurementState)` |
| `SOURCE_CHANGED` | `measurement.source` | `(name: str)` |
| `EVENT_DETECTED` | `signal.event` | `(instant_s: float, amplitude_v: float)` |
| `NOTE_PLAYED` | `music.note` | `(midi_pitch: int, velocity: int)` |
| `UTTERANCE_PRODUCED` | `speech.utterance` | `(text: str)` |
| `SESSION_STARTED` | `session.started` | `(directory: str)` |
| `SESSION_ENDED` | `session.ended` | `(directory: str)` |
| `SAMPLE_CAPTURED` | `sample.captured` | `(path: str)` |
| `SETTINGS_CHANGED` | `settings.changed` | *(nothing)* |
| `DISK_ALERT` | `disk.alert` | `(megaoctets_restants: float)` |

`EVENTS` is a dictionary from those strings to their description:

```python
from phytoscope.api import EVENTS
for name, description in EVENTS.items():
    print(f"{name:<24} {description}")
```

---

## What the host guarantees

### Callbacks come from the interface thread

**Never from the acquisition thread.** A module that takes thirty milliseconds
to answer slows the display down; it does not drop a sample.

That is not permission to be slow. Thirty milliseconds at every event, on an
active plant, is visible.

### A callback that raises is unsubscribed

Immediately, and the incident is written to the log with your module's name.

That is deliberate. Leaving a faulty subscriber connected would mean writing
the same traceback every second, and making the log unreadable — the very log
one needs in order to understand the fault.

> **Consequence:** if your module "stops reacting" after a while, look at the
> log. You will find the fault there, and the time at which it was
> disconnected.

### The call order is the subscription order

Deterministic, and therefore reproducible.

### Unsubscribing is automatic

When your module shuts down, the host removes your subscriptions. Do not deal
with them in `shutdown()`.

---

## Subscribing to an event that does not exist

That is **not an error**. The callback will simply never be called.

It is intended: a later version can publish new events without older modules
having to change, and a module can subscribe to a recent event while remaining
loadable on an older version.

```python
#  Works on every version; is only called on those that publish this event.
self.context.subscribe("signal.anomalie", self._sur_anomalie)
```

---

## A complete example

A module that keeps a running log of the session:

```python
import json, os, time
from phytoscope.api import (Capability, Manifest, Module, SESSION_STARTED,
                            SESSION_ENDED, EVENT_DETECTED, DISK_ALERT)

class SessionLog(Module):
    MANIFEST = Manifest(
        name="session-log",
        title="Session log",
        version="1.0.0", api="3.0",
        description="Writes a readable record of what happened.",
        #  No capability: this module acts only through its subscriptions.
        #  That is legitimate, and the manifest says so by declaring none.
    )

    def setup(self):
        self._lignes = []
        self._debut = time.time()
        for event, callback in (
            (SESSION_STARTED, self._seance_commencee),
            (SESSION_ENDED, self._seance_terminee),
            (EVENT_DETECTED, self._evenement),
            (DISK_ALERT, self._disque),
        ):
            self.context.subscribe(event, callback)

    def _noter(self, text):
        self._lignes.append(f"{time.time() - self._debut:8.1f} s  {text}")

    def _seance_commencee(self, directory):
        self._noter(f"recording started → {os.path.basename(directory)}")

    def _seance_terminee(self, directory):
        self._noter("recording finished")
        self._ecrire(directory)

    def _evenement(self, instant_s, amplitude_v):
        self._noter(f"event, {amplitude_v * 1e6:+.1f} µV")

    def _disque(self, megaoctets):
        self._noter(f"WARNING: {megaoctets:.0f} MB left")

    def _ecrire(self, directory):
        #  Into OUR directory, not the session's.
        path = os.path.join(self.context.directory(),
                              f"log-{int(self._debut)}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(self._lignes) + "\n")
        self.context.log(f"log written: {path}")

    def shutdown(self):
        if self._lignes:
            self._ecrire("")
```

---

**Next:** [5. Testing your module](05-testing.md)
