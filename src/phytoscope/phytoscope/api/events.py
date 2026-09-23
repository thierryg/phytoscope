# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/events.py
#
#  Version   : 1.6.0
#  Date      : 2026-09-23
#  Publisher : Bretagne Namasté
#  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Website   : https://bretagne-namaste.com
#  Contact   : contact@bretagne-namaste.com
#  License   : MIT — see LICENSE.txt
#
#  SPDX-License-Identifier: MIT
#  end of attribution
#  ==========================================================================

"""The event bus — what a module can subscribe to.

A module does not poll the software in a loop: it states what interests it,
and the host calls it back. That is the only way to have modules that cost
nothing while nothing is happening.

Events are **strings**, listed below and nowhere else. A string rather than
an enumeration, for one specific reason: a later release can publish new ones
without older modules having to be recompiled or even re-read. Subscribing to
an event that does not exist yet is not an error — the callback will simply
never be called.

What the host guarantees
-----------------------

**Callbacks are called from the interface thread**, never from the
acquisition thread. A module taking thirty milliseconds to answer slows the
display down; it does not drop a sample (`C-20`, `C-28`).

**A callback that raises is unsubscribed.** Immediately, and the incident is
recorded in the log with the module's name. A faulty module does not drown
the session in tracebacks, and it is not left half-wired.

**Call order is subscription order.** Deterministic, therefore reproducible.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Dict, List, Tuple

__all__ = ["BUS", "Bus", "EVENTS",
           "MEASUREMENT_STARTED", "MEASUREMENT_STOPPED", "EVENT_DETECTED",
           "NOTE_PLAYED", "UTTERANCE_PRODUCED", "SESSION_STARTED",
           "SESSION_ENDED", "SAMPLE_CAPTURED", "SETTINGS_CHANGED",
           "SOURCE_CHANGED", "DISK_ALERT"]

#  --- The published events, with what the callback receives ----------------
#
#  These wire names were renamed from French on 2026-09-22, which **breaks**
#  every module that subscribed to the old ones. That is why `API_VERSION`
#  went from 1.0 to 2.0 in the same change.
#
#  The version bump is not bureaucracy. Subscribing to an event that does not
#  exist is deliberately not an error — see the docstring above — so a module
#  still asking for "mesure.demarree" would simply never be called again, and
#  nothing would say why. A major bump makes the host refuse that module up
#  front, with a sentence naming the version it targets. Refusing loudly
#  beats running silently wrong.
MEASUREMENT_STARTED = "measurement.started"  # (state: MeasurementState)
MEASUREMENT_STOPPED = "measurement.stopped"  # (state: MeasurementState)
SOURCE_CHANGED = "measurement.source"        # (name: str)
EVENT_DETECTED = "signal.event"              # (instant_s, amplitude_v: float)
NOTE_PLAYED = "music.note"                   # (midi_pitch, velocity: int)
UTTERANCE_PRODUCED = "speech.utterance"      # (text: str)
SESSION_STARTED = "session.started"          # (directory: str)
SESSION_ENDED = "session.ended"              # (directory: str)
SAMPLE_CAPTURED = "sample.captured"          # (path: str)
SETTINGS_CHANGED = "settings.changed"        # ()
DISK_ALERT = "disk.alert"                    # (megaoctets_restants: float)

#: The complete list, with what the callback receives. Used by the
#: documentation and by the SDK tool, which reads it to offer the events that
#: actually exist.
EVENTS: Dict[str, str] = {
    MEASUREMENT_STARTED: "acquisition starts — receives the measurement state",
    MEASUREMENT_STOPPED: "acquisition stops — receives the measurement state",
    SOURCE_CHANGED: "the acquisition source changed — receives its name",
    EVENT_DETECTED: "an event crosses the threshold — receives "
                       "(instant_s, amplitude_v)",
    NOTE_PLAYED: "a note is played — receives (midi_pitch, velocity)",
    UTTERANCE_PRODUCED: "Speech mode produced an utterance — receives the text",
    SESSION_STARTED: "a recording starts — receives the directory",
    SESSION_ENDED: "a recording ends — receives the directory",
    SAMPLE_CAPTURED: "a quick sample is written — receives its path",
    SETTINGS_CHANGED: "the settings changed — no argument",
    DISK_ALERT: "disk space is becoming critical — receives the MB left",
}


class Bus:
    """The event dispatcher. One per process: `BUS`."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Tuple[Callable, str]]] = {}
        #  A lock, because `subscribe` can be called while a module is being
        #  installed and an event is already being dispatched.
        self._lock = threading.RLock()
        self.published = 0
        self.unsubscribed_on_fault = 0

    def subscribe(self, event: str, callback: Callable,
                module: str = "") -> None:
        with self._lock:
            self._subscribers.setdefault(event, []).append((callback, module))

    def unsubscribe(self, event: str, callback: Callable) -> None:
        with self._lock:
            entries = self._subscribers.get(event)
            if not entries:
                return
            self._subscribers[event] = [(r, m) for r, m in entries if r is not callback]

    def unsubscribe_module(self, module: str) -> int:
        """Removes every subscription held by a module. Returns how many."""
        removed = 0
        with self._lock:
            for event, entries in list(self._subscribers.items()):
                kept = [(r, m) for r, m in entries if m != module]
                removed += len(entries) - len(kept)
                self._subscribers[event] = kept
        return removed

    def publish(self, event: str, *args: Any, **kwargs: Any) -> int:
        """Calls the subscribers. Returns the number of successful calls.

        A callback that raises is **unsubscribed on the spot**: leaving a
        failing module wired up would mean writing the same traceback to the
        log every second, and making the log unusable — the very log you need
        in order to understand the failure.
        """
        with self._lock:
            subscribers = list(self._subscribers.get(event, ()))
        if not subscribers:
            return 0

        self.published += 1
        succeeded = 0
        for callback, module in subscribers:
            try:
                callback(*args, **kwargs)
                succeeded += 1
            except Exception as exc:                       # noqa: BLE001
                self.unsubscribe(event, callback)
                self.unsubscribed_on_fault += 1
                from ..core.logging_setup import get_logger
                get_logger(f"module.{module or '?'}").error(
                    "Subscription to “%s” removed after a fault: "
                    "%s: %s", event, type(exc).__name__, exc)
        return succeeded

    def subscribers(self, event: str = "") -> int:
        with self._lock:
            if event:
                return len(self._subscribers.get(event, ()))
            return sum(len(v) for v in self._subscribers.values())

    def clear(self) -> None:
        """Removes everything. Used by the tests, and at shutdown."""
        with self._lock:
            self._subscribers.clear()


#: The one bus of the process.
BUS = Bus()
