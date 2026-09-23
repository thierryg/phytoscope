# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/sdk/hello-world/test_hello_world.py
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

"""Tests for the "hello-world" module — no running software, no hardware.

This is the most useful thing about this file: a module is tested **without
starting anything**. A fake context, a manufactured signal, and the methods
are called. Writing a module therefore needs neither a plant on the desk, nor
a board plugged in, nor even PhytoScope running.

Copy this file along with `module.py`: your own tests will look like these.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Dict, List

import numpy as np
import pytest


# ---------------------------------------------------------------------------
#  What it takes to run a module without the software
# ---------------------------------------------------------------------------
class FakeContext:
    """A fake context: the same surface, with nothing behind it.

    Only what the module uses is implemented, and nothing else. If a test
    fails because a method is missing here, that is a sign the module uses a
    part of the API which will also have to be tested.
    """

    def __init__(self, settings: Dict[str, Any] | None = None) -> None:
        self.settings: Dict[str, Any] = dict(settings or {})
        self.subscriptions: Dict[str, List] = {}
        self.logged: List[str] = []
        self.rate_hz = 250.0
        self.full_scale_v = 2.5
        self.mains_hz = 50.0

    def subscribe(self, event: str, callback) -> None:
        self.subscriptions.setdefault(event, []).append(callback)

    def log(self, message: str, level: str = "info") -> None:
        self.logged.append(f"{level}: {message}")

    def message(self, text: str) -> None:
        self.logged.append(f"message: {text}")

    def translate(self, text: str) -> str:
        return text                 # in a test, the source language is enough

    def directory(self) -> str:
        import tempfile
        return tempfile.mkdtemp(prefix="test-module-")

    def signal(self, seconds: float = 60.0, raw: bool = False) -> np.ndarray:
        return fake_signal(seconds)

    def event_times(self) -> List[float]:
        return []

    def state(self):
        from types import SimpleNamespace
        return SimpleNamespace(duration_s=120.0, source="test", running=True,
                               replaying=False)


def fake_signal(seconds: float = 30.0, fs: float = 250.0) -> np.ndarray:
    """A plausible signal: noise, a slow drift, and a few bursts."""
    n = int(seconds * fs)
    t = np.arange(n) / fs
    r = np.random.default_rng(42)
    x = r.normal(0.0, 3e-6, n)                    # background noise, 3 µV
    x += 4e-5 * np.sin(2 * np.pi * t / 400.0)     # slow drift
    for t0 in np.arange(5.0, seconds, 7.0):       # bursts of activity
        x += 1.2e-4 * np.exp(-((t - t0) / 1.5) ** 2)
    return x


@pytest.fixture()
def module():
    """Loads the `module.py` sitting next to this file, without installing it."""
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(here, "module.py")
    spec = importlib.util.spec_from_file_location("module_hello_world", path)
    package = importlib.util.module_from_spec(spec)
    #  Registered BEFORE execution: `@dataclass` looks up
    #  `sys.modules[cls.__module__]` and would fail on a missing module.
    sys.modules["module_hello_world"] = package
    spec.loader.exec_module(package)
    return package


def module_class(package):
    """The one class of `package` that is a module."""
    from phytoscope.api import Module
    return next(o for o in vars(package).values()
                if isinstance(o, type) and issubclass(o, Module)
                and o is not Module)


@pytest.fixture()
def instance(module):
    """The module, built and installed, with a test context."""
    module_cls = module_class(module)
    context = FakeContext(settings=module_cls(FakeContext())
                           .default_settings())
    obj = module_cls(context)
    obj.setup()
    return obj


# ---------------------------------------------------------------------------
#  The manifest
# ---------------------------------------------------------------------------
def test_the_manifest_is_valid(module):
    """A rejected manifest, and the module is never loaded."""
    manifest = module_class(module).MANIFEST
    assert manifest.problems() == [], manifest.problems()
    assert manifest.name == "hello-world"
    assert manifest.capabilities, "a module with no capability is of no use"


def test_the_manifest_targets_a_known_api(module):
    from phytoscope.api import API_VERSION, compatible
    assert compatible(module_class(module).MANIFEST.api, API_VERSION)


# ---------------------------------------------------------------------------
#  The work
# ---------------------------------------------------------------------------
def test_analyse_returns_complete_quantities(instance):
    """Every quantity has to say what it means."""
    context = instance.context
    quantities = instance.analyse(fake_signal(30.0), 250.0, context)
    assert quantities, "the module returned nothing on a valid signal"
    for g in quantities:
        assert g.key and g.label, "a key and a label are required"
        assert g.text, "the displayed value must not be empty"
        assert len(g.meaning) > 20, (
            f"“{g.key}” does not explain what it means — the interface will "
            "write that in your place, and it will show")
        assert np.isfinite(g.value)


def test_an_empty_signal_does_not_raise(instance):
    """“Nothing to say” is said with an empty list, never with an exception."""
    assert instance.analyse(np.zeros(0), 250.0, instance.context) == []


def test_the_settings_are_honoured(module):
    """A setting turned off has to show in the result."""
    module_cls = module_class(module)
    context = FakeContext(settings={"greet": False})
    obj = module_cls(context)
    obj.setup()
    keys = {g.key for g in obj.analyse(fake_signal(20.0), 250.0, context)}
    assert "greeting" not in keys
    assert "samples" in keys


def test_every_hole_in_a_template_has_a_value(instance):
    """The interface translates first and fills in afterwards.

    A `{hole}` left without a value in `params` raises a `KeyError` at display
    time, which shows as an empty row rather than as a fault. Checking it here
    costs nothing.
    """
    import string
    for g in instance.analyse(fake_signal(20.0), 250.0, instance.context):
        for template in (g.label, g.meaning):
            holes = {name for _, name, _, _ in string.Formatter().parse(template)
                     if name}
            missing = holes - set(g.params or {})
            assert not missing, (
                f"“{g.key}”: {sorted(missing)} has no value in `params`")


# ---------------------------------------------------------------------------
#  The subscriptions
# ---------------------------------------------------------------------------
def test_the_module_subscribes_to_what_it_announces(instance):
    from phytoscope.api import EVENT_DETECTED
    assert EVENT_DETECTED in instance.context.subscriptions


def test_the_callback_counts_the_events(instance):
    from phytoscope.api import EVENT_DETECTED
    callbacks = instance.context.subscriptions[EVENT_DETECTED]
    for i in range(5):
        for callback in callbacks:
            callback(float(i), 1e-4)
    quantities = {g.key: g for g in
                  instance.analyse(fake_signal(20.0), 250.0,
                                    instance.context)}
    assert quantities["events-seen"].value == 5.0


def test_shutdown_does_not_raise(instance):
    """Closing has to be quiet, even if nothing happened."""
    instance.shutdown()
    assert any("goodbye" in m for m in instance.context.logged)
