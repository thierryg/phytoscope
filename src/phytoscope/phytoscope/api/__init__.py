# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/__init__.py
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

"""The PhytoScope module API — the public surface, and nothing else.

A module imports **only from here**:

.. code-block:: python

    from phytoscope.api import Module, Manifest, Capability, Analyser, Quantity

What is absent from this file is not part of the API: it may change from one
release to the next without notice. What appears here is held by the version
contract (see `contract.API_VERSION`).

Writing a module
----------------

The shortest one that does anything fits in twenty lines:

.. code-block:: python

    from phytoscope.api import Analyser, Capability, Quantity, Manifest, Module

    class Bonjour(Module, Analyser):
        MANIFEST = Manifest(
            name="hello-world",
            title="Hello, world",
            version="1.0.0",
            api="2.0",
            capabilities=(Capability.ANALYSER,),
        )

        def analyse(self, x, fs, context):
            return [Quantity(
                key="compte", label="Samples received",
                value=float(x.size), text=f"{x.size}",
                meaning="The number of samples in the analyzed window.")]

The SDK, under `src/sdk/`, gives a complete specimen together with its tests,
and a tool that creates a new one in a single command.
"""
from __future__ import annotations

from .context import Context, MeasurementState
from .contract import (API_VERSION, Analyser, Capability, Descriptor,
                      Exporter, Quantity, Manifest, Module, ProposedNote,
                      Sonifier, Source, Trace, compatible, parse_version)
from .events import BUS, EVENTS
from .events import (DISK_ALERT, SAMPLE_CAPTURED, UTTERANCE_PRODUCED,
                         EVENT_DETECTED, MEASUREMENT_STOPPED, MEASUREMENT_STARTED,
                         NOTE_PLAYED, SETTINGS_CHANGED, SESSION_STARTED,
                         SESSION_ENDED, SOURCE_CHANGED)
from .registry import ModuleState, LoadedModule, Registry

__all__ = [
    #  The contract
    "API_VERSION", "compatible", "parse_version", "Manifest", "Module",
    "Capability",
    #  The capabilities
    "Analyser", "Descriptor", "Sonifier", "Exporter", "Source",
    #  What they exchange
    "Quantity", "Trace", "ProposedNote",
    #  What a module receives
    "Context", "MeasurementState",
    #  The events
    "BUS", "EVENTS", "MEASUREMENT_STARTED", "MEASUREMENT_STOPPED", "SOURCE_CHANGED",
    "EVENT_DETECTED", "NOTE_PLAYED", "UTTERANCE_PRODUCED", "SESSION_STARTED",
    "SESSION_ENDED", "SAMPLE_CAPTURED", "SETTINGS_CHANGED",
    "DISK_ALERT",
    #  The host — a module does not need it, the interface does
    "Registry", "LoadedModule", "ModuleState",
]
