# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/context.py
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

"""The context — everything a module receives from the host, and nothing else.

A module **never receives the `Engine` object**. That is deliberate, and it
is what makes the API sustainable over time: the engine changes with every
release — replay, disk monitoring and quick samples were all added to it —
and a module leaning on it would break every time.

So it receives this object instead, whose shape is frozen by the contract. In
it there is:

* what it needs to **read** the signal and the state of the measurement;
* what it needs to **write** its own settings and its own files, in a place
  that belongs to it;
* what it needs to **say** something — the log, a message to the user;
* what it needs to **translate** its labels;
* what it needs to **subscribe** to what is happening.

What is not in it, and why
--------------------------

**No way to write into the signal.** A module does not alter the
measurement. It observes it, draws numbers from it, proposes notes. Letting a
module change what is about to be recorded would turn every session into data
you can no longer conclude anything from.

**No write access to other modules' settings, or to the software's.** A
module reads the sampling rate; it does not change it.

**No path outside its own.** `directory()` returns a directory that belongs to
it, and that is where it writes. Nothing technically prevents it from writing
elsewhere — this is Python, not a prison — but it would be a fault, and the
SDK documentation says so.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

__all__ = ["Context", "MeasurementState"]


@dataclass
class MeasurementState:
    """A snapshot of the measurement, copied — not shared.

    Copied, rather than a reference to the engine's state: a module holding
    the reference would see its values shift underneath it in the middle of a
    computation.
    """
    running: bool = False
    source: str = ""
    duration_s: float = 0.0
    rate_hz: float = 250.0
    value_v: float = 0.0
    baseline_v: float = 0.0
    rms_v: float = 0.0
    pp_v: float = 0.0
    drift_v_per_min: float = 0.0
    saturated: bool = False
    events: int = 0
    notes: int = 0
    recording: bool = False
    #  True while an existing recording is being replayed: a module that
    #  writes somewhere has to know it is not measuring, it is replaying.
    replaying: bool = False


class Context:
    """What a module receives. Created by the host, one per module.

    A context **belongs to one module**: its log carries that module's name,
    its settings are its own, its directory belongs to it. Two modules do not
    tread on each other.
    """

    def __init__(self, module_name: str, engine: Any, host_settings: Any,
                 modules_directory: str, api_required: str = "") -> None:
        self._name = module_name
        self._engine = engine              # never exposed as such
        self._host_settings = host_settings
        self._modules_directory = modules_directory
        self._settings: Dict[str, Any] = {}
        self._subscriptions: List[tuple] = []
        #  What the module's manifest asked for. Empty when a context is
        #  built outside the registry — a test, say — which is why
        #  `api_required` is documented as "as the host read it".
        self._api_required = api_required

    # -- identity ------------------------------------------------------------
    @property
    def name(self) -> str:
        """The name of the module this context belongs to."""
        return self._name

    # -- the two sides of the version contract -------------------------------
    #
    #  The manifest says the MINIMUM the module needs, and the host refuses it
    #  at discovery if it cannot honour that (`Manifest.api`,
    #  `compatible()`). The three members below are the other direction: once
    #  loaded, a module can ask what it is actually running on, and adapt.
    #
    #  Why a module would want to: a manifest declares one minimum, for the
    #  whole module. A module that needs 3.0 to work at all but would use one
    #  field added in 3.2 should declare `api="3.0"` — the lowest that
    #  suffices — and ask here at run time whether that field is there.
    #  Declaring 3.2 instead would refuse the module on every 3.0 and 3.1
    #  host, to gain one optional field. This is how "aim for the lowest that
    #  will do", in the SDK, is meant to be possible.
    @property
    def api_version(self) -> str:
        """The API version this host offers, "major.minor"."""
        from .contract import API_VERSION
        return API_VERSION

    @property
    def api_required(self) -> str:
        """The minimum this module declared, as the host read it.

        Handed back so a module can check what it asked for against what it
        got — and so that a test can assert the two agree without importing
        the registry.
        """
        return self._api_required

    def api_at_least(self, version: str) -> bool:
        """Is the host's API at least `version`? Same major, minor at least.

        .. code-block:: python

            if self.context.api_at_least("3.2"):
                self._use_the_new_field()
        """
        from .contract import compatible
        return compatible(version, self.api_version)

    # -- reading the signal --------------------------------------------------
    def signal(self, seconds: float = 60.0, raw: bool = False) -> np.ndarray:
        """The last N seconds of signal, **in volts**.

        :param raw: true for the signal before the notch and low-pass
            filters. Use it for any noise measurement: filtering before
            measuring noise amounts to measuring your own filter (`C-1B`).

        Returns an empty array if there is nothing yet — that is not an
        error, it is the situation at startup, and the module must expect it.
        """
        try:
            x = self._engine.recent(max(float(seconds), 0.1), raw=bool(raw))
        except Exception:                                  # noqa: BLE001
            return np.zeros(0, dtype=np.float64)
        return np.asarray(x, dtype=np.float64).ravel()

    @property
    def rate_hz(self) -> float:
        """The actual sampling rate."""
        try:
            return float(self._host_settings.acquisition.sample_rate)
        except Exception:                                  # noqa: BLE001
            return 250.0

    @property
    def full_scale_v(self) -> float:
        """The converter's full scale, in volts."""
        try:
            return float(self._host_settings.acquisition.input_range_v)
        except Exception:                                  # noqa: BLE001
            return 2.5

    @property
    def mains_hz(self) -> float:
        """The mains frequency declared in the settings: 50 or 60."""
        try:
            return float(self._host_settings.processing.notch_hz or 50.0)
        except Exception:                                  # noqa: BLE001
            return 50.0

    def state(self) -> MeasurementState:
        """A snapshot of the measurement. Copied, never shared."""
        e = MeasurementState(rate_hz=self.rate_hz)
        s = getattr(self._engine, "state", None)
        if s is None:
            return e
        e.running = bool(getattr(s, "running", False))
        e.source = str(getattr(s, "source_name", ""))
        e.duration_s = float(getattr(s, "elapsed_s", 0.0))
        e.value_v = float(getattr(s, "value_v", 0.0))
        e.baseline_v = float(getattr(s, "baseline_v", 0.0))
        e.rms_v = float(getattr(s, "rms_v", 0.0))
        e.pp_v = float(getattr(s, "pp_v", 0.0))
        e.drift_v_per_min = float(getattr(s, "drift_v_per_min", 0.0))
        e.saturated = bool(getattr(s, "saturated", False))
        e.events = int(getattr(s, "events_total", 0))
        e.notes = int(getattr(s, "notes_total", 0))
        e.recording = bool(getattr(s, "recording", False))
        e.replaying = bool(getattr(s, "replaying", False))
        return e

    def event_times(self) -> List[float]:
        """The times of recent events, in seconds since the start."""
        try:
            return list(getattr(self._engine, "_evenements_recents", []))
        except Exception:                                  # noqa: BLE001
            return []

    # -- writing somewhere ---------------------------------------------------
    def directory(self) -> str:
        """The module's directory, created as needed. **Write here, only here.**

        ``<configuration>/modules/<module-name>/``

        It survives updates and is never erased by the software. A module
        writing anywhere else — in the sessions directory, say — is meddling
        with what is none of its business.
        """
        path = os.path.join(self._modules_directory, self._name)
        os.makedirs(path, exist_ok=True)
        return path

    # -- settings ------------------------------------------------------------
    @property
    def settings(self) -> Dict[str, Any]:
        """The module's settings, as the user left them.

        Mutable; the host saves them at shutdown. They are the ones declared
        by `default_settings()`, filled in with whatever had been stored.
        """
        return self._settings

    def _set_settings(self, values: Dict[str, Any]) -> None:
        """Host only."""
        self._settings = dict(values)

    # -- saying something ----------------------------------------------------
    def log(self, message: str, level: str = "info") -> None:
        """Writes a line to the software's log, under the module's name."""
        from ..core.logging_setup import get_logger
        log = get_logger(f"module.{self._name}")
        getattr(log, level if level in
                ("debug", "info", "warning", "error") else "info")("%s", message)

    def message(self, text: str) -> None:
        """Passes a message to the user, in the status bar.

        Use sparingly: a module that talks incessantly ends up not being read
        at all.
        """
        try:
            self._engine._message(f"[{self._name}] {text}")
        except Exception:                                  # noqa: BLE001
            self.log(text)

    def translate(self, text: str) -> str:
        """The translation of a label in the current language.

        A module supplies its own catalogs in the `languages/` directory of
        its own folder; failing that, the source text is returned as is,
        which is acceptable behavior and not an error.
        """
        from ..i18n import t
        return t(text)

    # -- subscribing ---------------------------------------------------------
    def subscribe(self, event: str, callback: Callable) -> None:
        """Subscribes to one of the software's events.

        The events are listed in `api.events`. A callback that raises is
        unsubscribed and the incident recorded in the log: a faulty module
        does not drown the session in errors.
        """
        from .events import BUS
        BUS.subscribe(event, callback, module=self._name)
        self._subscriptions.append((event, callback))

    def _unsubscribe_all(self) -> None:
        """Host only, called when the module stops."""
        from .events import BUS
        for event, callback in self._subscriptions:
            BUS.unsubscribe(event, callback)
        self._subscriptions.clear()
