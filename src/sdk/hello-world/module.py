# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/sdk/hello-world/module.py
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

"""Hello, world — the smallest PhytoScope module that does anything at all.

This file is meant to be read from end to end, and then copied. It shows the
four things a module does, and nothing more:

1. **introduce itself** — the manifest;
2. **get ready** — `setup()`, once at start-up;
3. **work** — here, an `Analyser` capability returning two numbers;
4. **listen** — a subscription to one of the software's events.

Trying it out
-------------

Copy this directory into your installation's modules directory:

.. code-block:: console

    # Linux
    cp -r src/sdk/hello-world ~/.config/phytoscope/modules/
    # macOS
    cp -r src/sdk/hello-world ~/Library/Application\\ Support/PhytoScope/modules/
    # Windows
    xcopy /E src\\sdk\\hello-world %APPDATA%\\PhytoScope\\modules\\hello-world\\

Restart the software: the Multimeter tab, "Scientific quantities" page, shows
your two rows. The Diagnostics tab shows the module in the list.

If nothing appears, the module was refused — Diagnostics says why, in one
sentence.
"""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

#  Everything a module needs comes from here, and from nowhere else. What is
#  not in `phytoscope.api` is not part of the interface: it may change from
#  one version to the next without notice.
from phytoscope.api import (Analyser, Capability, Context, EVENT_DETECTED,
                            Quantity, Manifest, Module)


class HelloWorld(Module, Analyser):
    """Counts the samples received, and the events since start-up."""

    #  ── 1. Introduce itself ───────────────────────────────────────────────
    #  The manifest is read WITHOUT running this file: the software therefore
    #  knows what this module does before trusting it. Write it out in plain
    #  sight, with literal values — a computed value would be ignored.
    MANIFEST = Manifest(
        name="hello-world",              # a-z, 0-9 and hyphens; the identifier
        title="Hello, world",           # what the user reads
        version="1.0.0",
        api="3.0",                      # the API version this module aims at
        description="The SDK's example module. It counts, and that is all.",
        author="Your name",
        licence="MIT",
        website="https://bretagne-namaste.com",
        capabilities=(Capability.ANALYSER,),
        #  If your module needs a library, say so here: the software checks
        #  BEFORE importing, and displays "module disabled: scipy missing"
        #  rather than an unreadable import traceback.
        # requires=("scipy",),
    )

    # ── The analyse's parameters ────────────────────────────────────────────
    #  How many seconds of signal you want, and whether you want it raw.
    #  RAW = before the notch and the low-pass. Use it for any noise
    #  measurement: filtering before measuring noise amounts to measuring your
    #  own filter.
    WINDOW_S = 30.0
    RAW_SIGNAL = False

    # ── 2. Get ready ─────────────────────────────────────────────────────────
    def setup(self) -> None:
        """Called once, after every module has been loaded.

        This is where you subscribe and prepare your files — **not** in
        `__init__`, which is called for every module at start-up and must stay
        instantaneous.
        """
        self._events_seen = 0
        self.context.subscribe(EVENT_DETECTED, self._on_event)
        self.context.log("hello, world")

    def shutdown(self) -> None:
        """Called once, at shutdown. Close what you opened.

        Your subscriptions are removed by the host: there is no need to deal
        with them.
        """
        self.context.log(f"goodbye — {self._events_seen} events seen")

    # ── 3. Work ──────────────────────────────────────────────────────────────
    def default_settings(self) -> Dict[str, Any]:
        """Your settings and their initial values.

        The software keeps them for you, under your module's name, and hands
        them back through `context.settings`. Never write into the software's
        own settings file yourself.
        """
        return {"greet": True, "time_unit": "s"}

    def analyse(self, x: np.ndarray, fs: float,
                 context: Context) -> List[Quantity]:
        """Returns the quantities to display. An empty list is acceptable.

        :param x: the signal, **in volts**, in chronological order.
        :param fs: the actual sampling rate, in hertz.

        Do not raise an exception to say "I have nothing to say": return an
        empty list. An exception disables your module for the session.
        """
        if x.size == 0:
            return []

        quantities = [
            Quantity(
                key="samples",
                label="Samples in the window",
                value=float(x.size),
                text=f"{x.size}",
                #  `meaning` is not decorative. The software requires every
                #  displayed value to say what it means AND what it does not
                #  allow one to conclude. A module that does not explain it is
                #  still loaded, but the interface writes "the module does not
                #  explain this value", which gets noticed.
                meaning=("How many samples were received over the last "
                      "{seconds} seconds, at {fs} Hz. It says nothing about "
                      "the plant: it is the software measuring itself."),
                #  A TEMPLATE here too, and not an f-string: `meaning` goes
                #  through the same catalogue as `label`, and a sentence
                #  with the numbers already embedded cannot be translated.
                params={"seconds": f"{x.size / fs:.0f}", "fs": f"{fs:.0f}"},
            ),
            Quantity(
                key="events-seen",
                label="Events seen since start-up",
                value=float(self._events_seen),
                text=f"{self._events_seen}",
                meaning=("Counted through a subscription, not by re-reading the "
                      "signal. It depends on the detection threshold in "
                      "force: changing that changes this number."),
                #  Pass `alert=True` to have the value displayed in red.
                alert=self._events_seen > 1000,
            ),
        ]

        if context.settings.get("greet", True):
            quantities.append(Quantity(
                key="greeting",
                #  A label containing a number must be a TEMPLATE, with the
                #  value in `params`: "at {tau} s" and not "at 1 s". Otherwise
                #  it cannot go into a translation catalogue.
                label="Hello from {module}",
                value=1.0,
                text=context.translate("it works"),
                meaning="If you are reading this, your module is loaded and called.",
                params={"module": self.MANIFEST.title},
            ))
        return quantities

    # ── 4. Listen ────────────────────────────────────────────────────────────
    def _on_event(self, instant_s: float, amplitude_v: float) -> None:
        """Called at every event detected in the signal.

        **Be brief.** Callbacks run in the interface thread: thirty
        milliseconds here slow the display down for everyone.

        A callback that raises is unsubscribed on the spot, and the incident
        written to the log — that is deliberate: leaving a faulty subscriber
        connected would drown the log under the same traceback, the very log
        one needs in order to understand the fault.
        """
        self._events_seen += 1
