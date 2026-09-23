# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/contract.py
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

"""The plug-in contract — what a module promises, what the host guarantees.

This file is **the most binding piece of the software**. Everything else may
change from one release to the next; this may not. The moment a module written
by somebody else relies on it, breaking it breaks their work. So it was
written by asking, line by line, whether we would be willing to maintain that
line for ten years.

What follows from that, and what explains the choices below:

* **An explicit version number.** ``API_VERSION`` follows semantic
  versioning. A module declares the version it targets; the host refuses to
  load what it cannot honor, rather than loading it halfway.
* **Declared capabilities, not guessed ones.** A module states what it
  provides. The host does not rummage through its attributes to find out:
  what is not declared does not exist.
* **No access to the engine.** A module receives a `Context` — a narrow,
  documented, stable surface. It never receives the `Engine` object, whose
  internal shape changes with every release.
* **Nothing is mandatory except the manifest.** A module that provides a
  single capability writes a single method.

The five capabilities
---------------------

===============  ==========================================================
`Analyser`      computes quantities over a window of signal
`Descriptor`    produces a representation of the signal (an image, a curve)
`Sonifier`   turns the signal into notes
`Exporter`    writes a session out in another format
`Source`         supplies a stream of measurements
===============  ==========================================================

A module may provide several of them, or none — in that last case it is only
useful for what it does at install and shutdown time, which is a legitimate
thing to be (a logging module, for instance).

What the host guarantees
------------------------

1. **A module that raises never brings the software down.** Every method is
   called under protection; a fault disables the module, records it in the
   log, and the session carries on.
2. **Load order is deterministic**: dependencies first, then alphabetical
   order. Two launches give the same order.
3. **Nothing is called on the data thread during acquisition.** Modules work
   on snapshots, never on the live stream: a slow module slows down its own
   display, not the measurement (`C-20`).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

__all__ = [
    "API_VERSION", "parse_version", "Manifest", "Module", "Capability",
    "Analyser", "Descriptor", "Sonifier", "Exporter", "Source",
    "Quantity", "Trace", "ProposedNote", "compatible",
]

#  The contract version, in semantic versioning.
#
#    major  a promise is broken — an older module stops working;
#    minor  a capability or a parameter is added, breaking nothing;
#    patch  a clarification of behavior, never of shape.
#
#  A module declaring "3.0" works with any "3.x" API. It does not work with
#  "4.x", and the host will say so rather than failing in the middle of a
#  session.
#
#  1.0 -> 2.0 on 2026-09-22: the event wire names were renamed from French
#  (`mesure.demarree` -> `measurement.started`, and nine others). That breaks
#  any module subscribing to the old names, and because subscribing to an
#  unknown event is deliberately not an error, such a module would have gone
#  quiet instead of failing. The major bump is what turns that silence into a
#  refusal the author can read.
#
#  2.0 -> 3.0 on 2026-09-23: the whole surface was renamed from French to
#  English, on request. `Manifeste` is `Manifest`, `installer()` is `setup()`,
#  `Grandeur.libelle` is `Quantity.label`, and a hundred and seventy other
#  names besides — the full table is in the SDK, "Migrating from 2.0".
#
#  This is exactly the break the contract was written to handle, and it is
#  handled the way this file promised it would be: the major changes, so a
#  module declaring "2.0" is refused **at discovery**, with a sentence naming
#  the version it asked for and the version on offer. It is not loaded and
#  then found wanting halfway through a method call; it never runs at all.
#  Nothing is aliased, because an alias would let a 2.0 module load and then
#  fail on the first field it reads — which is the failure mode a major bump
#  exists to prevent.
API_VERSION = "3.0"


def parse_version(v: Any) -> Tuple[int, int]:
    """"3.1" -> (3, 1). An unreadable version gives (-1, -1).

    Public, because both sides of the contract need it and neither should be
    writing its own regular expression: a module that adapts its behaviour to
    the host's version asks this, and the host asks it of every manifest it
    reads. Two parsers would disagree on "3.1.4" or " 3.0 " sooner or later.

    The patch number is deliberately ignored. A patch clarifies behaviour,
    never shape (see API_VERSION above), so it cannot make a module
    compatible or incompatible — and letting it into the comparison would
    invite modules to require one.
    """
    m = re.match(r"^\s*(\d+)\.(\d+)", str(v))
    return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)


def compatible(requested: str, offered: str = API_VERSION) -> bool:
    """Can a module needing **at least** `requested` run on `offered`?

    The rule: same major, and the offered minor at least equal to the one
    required. A module needing 3.2 does not run on a 3.1 API, which does not
    yet know what it expects; it does run on 3.3, which knows more.

    `requested` is therefore a **minimum**, not an exact match — which is why
    `Manifest.api` is documented as the lowest version the module needs, and
    why `Manifest.api_required` returns it parsed.
    """
    rm, rn = parse_version(requested)
    om, on = parse_version(offered)
    if rm < 0 or om < 0:
        return False
    return rm == om and rn <= on


# ---------------------------------------------------------------------------
#  What a module says about itself
# ---------------------------------------------------------------------------
class Capability:
    """The capability names, so that they are not hard-coded as strings."""
    ANALYSER = "analyser"
    DESCRIPTOR = "descriptor"
    SONIFIER = "sonifier"
    EXPORTER = "exporter"
    SOURCE = "source"

    ALL = (ANALYSER, DESCRIPTOR, SONIFIER, EXPORTER, SOURCE)


@dataclass
class Manifest:
    """A module's identity — the one thing it is required to state.

    It is read **before** importing anything from the module: that is what
    makes it possible to list the modules present, to disable one, and to
    refuse to import one targeting an API we cannot honor. Importing in order
    to find out whether to import would be absurd.
    """
    name: str                        # technical identifier: a-z, 0-9, hyphen
    title: str = ""                 # what is displayed; falls back to `name`
    version: str = "0.1.0"
    #  The **minimum** API version this module needs, "major.minor". The host
    #  accepts it on any later minor of the same major, and refuses it on any
    #  other major — see `compatible()`. Declare the lowest version that
    #  actually suffices: a module claiming 3.4 because that is what its
    #  author had installed is a module refused on a 3.2 host for no reason.
    api: str = API_VERSION
    description: str = ""
    author: str = ""
    licence: str = ""
    website: str = ""
    #  What the module provides. Declarative: what is not listed here is not
    #  offered to the user, even if the method exists.
    capabilities: Tuple[str, ...] = ()
    #  The modules that must be loaded before this one, by their `name`.
    depends_on: Tuple[str, ...] = ()
    #  The Python libraries required. Checked before loading: "module
    #  disabled: scipy missing" beats an import traceback.
    requires: Tuple[str, ...] = ()
    #  A module internal to the software, shipped with it. It cannot be
    #  uninstalled.
    built_in: bool = False

    def __post_init__(self) -> None:
        if not self.title:
            self.title = self.name

    @property
    def valid(self) -> bool:
        return bool(re.match(r"^[a-z][a-z0-9-]{1,48}$", self.name or ""))

    def problems(self) -> List[str]:
        """What keeps this manifest from being accepted, in plain words."""
        problems_found = []
        if not self.valid:
            problems_found.append(
                f"invalid name “{self.name}”: lowercase letters, "
                "digits and hyphens, 2 to 49 characters, starting with a "
                "letter")
        if not compatible(self.api):
            problems_found.append(
                f"needs at least API {self.api}, but this software offers "
                f"{API_VERSION} — it wants {self.api_satisfied_by}")
        unknown = [c for c in self.capabilities if c not in Capability.ALL]
        if unknown:
            problems_found.append(f"unknown capability/capabilities: "
                          f"{', '.join(unknown)}")
        return problems_found

    @property
    def api_required(self) -> Tuple[int, int]:
        """The minimum API version this module needs, as (major, minor).

        The host reads this rather than parsing `api` itself; `(-1, -1)` means
        the field could not be read at all, which `problems()` reports.
        """
        return parse_version(self.api)

    @property
    def api_satisfied_by(self) -> str:
        """In plain words, what would satisfy this module.

        Displayed in Diagnostics next to a refusal, so that the sentence says
        what to install rather than only what is wrong.
        """
        major, minor = self.api_required
        if major < 0:
            return f"an unreadable API version: “{self.api}”"
        return f"API {major}.{minor} or any later {major}.x"

    def to_dict(self) -> Dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)


# ---------------------------------------------------------------------------
#  The objects the capabilities exchange
# ---------------------------------------------------------------------------
@dataclass
class Quantity:
    """A measured quantity, with what it says and what it does not.

    The `meaning` field is not decoration: `C-15` requires every representation
    to state what it assumes and what it does not allow you to conclude. A
    module that returns a quantity without explaining it will still be
    loaded, but the interface will print "(the module does not explain this
    value)", which is hard to miss.
    """
    key: str
    label: str
    value: float
    text: str = ""                 # the formatted value, unit included
    meaning: str = ""                  # what this number says — in one sentence
    alert: bool = False
    params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.text:
            self.text = f"{self.value:.3g}"


@dataclass
class Trace:
    """A curve to display: abscissas, ordinates, and labels."""
    x: np.ndarray
    y: np.ndarray
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    x_log: bool = False
    y_log: bool = False
    #  What the representation assumes, and what it does not allow you to
    #  conclude. Displayed beneath the curve (`C-15`).
    warning: str = ""

    def __post_init__(self) -> None:
        self.x = np.asarray(self.x, dtype=np.float64).ravel()
        self.y = np.asarray(self.y, dtype=np.float64).ravel()
        if self.x.size != self.y.size:
            raise ValueError(
                f"trace “{self.title}”: {self.x.size} abscissas "
                f"for {self.y.size} ordinates")


@dataclass
class ProposedNote:
    """A note a sonify proposes. The host decides whether to play it."""
    midi_pitch: int
    velocity: int = 80
    duration_s: float = 0.4
    channel: int = 0
    #  The measured value that produced this note. Kept in the rendering: a
    #  sonification you cannot trace back to the measurement is no longer a
    #  measurement (`C-15`).
    source_v: float = 0.0


# ---------------------------------------------------------------------------
#  The module itself
# ---------------------------------------------------------------------------
class Module:
    """What every PhytoScope module inherits from.

    The only required element is `MANIFEST`. Everything else has a default
    behavior that does nothing, so a minimal module fits in fifteen lines —
    see the SDK, module "hello-world".

    Life cycle, in this order:

    1. ``__init__(context)`` — the context is handed over. **Do nothing
       lengthy here**: this runs at startup, and every module goes through
       it.
    2. ``setup()`` — once, after all modules have been loaded. This is
       where you subscribe to events and prepare your files.
    3. the capabilities are called on demand, during the session.
    4. ``shutdown()`` — once, at shutdown. Close what you opened.

    An exception raised in any of these steps disables the module and records
    it in the log. It never brings the software down.
    """

    #: Required. Redefined by every module.
    MANIFEST: Manifest = Manifest(name="module-with-no-name")

    def __init__(self, context: "Context") -> None:   # noqa: F821
        self.context = context

    # -- life cycle ----------------------------------------------------------
    def setup(self) -> None:
        """Called once, after all modules have been loaded."""

    def shutdown(self) -> None:
        """Called once, at shutdown. Close what you opened."""

    # -- settings ------------------------------------------------------------
    def default_settings(self) -> Dict[str, Any]:
        """The module's settings and their initial values.

        The host keeps them in its own file, under the module's name, and
        hands them back through `context.settings`. A module never writes to
        the software's settings file.
        """
        return {}


# ---------------------------------------------------------------------------
#  The five capabilities
# ---------------------------------------------------------------------------
class Analyser:
    """Computes quantities over a window of signal.

    Called by the Multimeter tab, at a reduced rate and only while the page
    is visible. The signal received is **in volts** and, unless asked
    otherwise, **raw** — before the notch and low-pass filters: filtering
    before measuring noise amounts to measuring your own filter (`C-1B`).
    """

    #: Length of signal wanted, in seconds. The host gives what it has.
    WINDOW_S: float = 120.0
    #: False to receive the processed signal rather than the raw one.
    RAW_SIGNAL: bool = True

    def analyse(self, x: np.ndarray, fs: float,
                 context: "Context") -> Sequence[Quantity]:  # noqa: F821
        """Returns the computed quantities. An empty list is acceptable."""
        raise NotImplementedError


class Descriptor:
    """Produces a representation of the signal — a curve, a spectrum, a map.

    Called by the Descriptors tab, at the user's request. It is therefore not
    a critical path: a computation taking a second is acceptable.
    """

    WINDOW_S: float = 60.0
    RAW_SIGNAL: bool = False

    def describe(self, x: np.ndarray, fs: float,
                context: "Context") -> Sequence[Trace]:      # noqa: F821
        raise NotImplementedError


class Sonifier:
    """Turns a measured value into notes.

    Called for every detected event. **Must be fast**: it runs inside the
    music rendering loop. Returning an empty list means "no note for this
    value", which is a legitimate answer.
    """

    def sonify(self, value_v: float, context: "Context"  # noqa: F821
                 ) -> Sequence[ProposedNote]:
        raise NotImplementedError


class Exporter:
    """Writes a session out in another format.

    Offered in the library, alongside the formats that ship with the
    software. The module receives the session directory and writes where it
    is told to — never anywhere else.
    """

    #: What appears in the list of formats.
    FORMAT: str = ""
    #: The extension of the file produced, dot included.
    EXTENSION: str = ""

    def export(self, session: str, target: str,
                 context: "Context") -> bool:                # noqa: F821
        """Returns true if the write succeeded."""
        raise NotImplementedError


class Source:
    """Supplies a stream of measurements — a board, a file, a generator.

    The most delicate capability: it runs on the data path. A source module
    has to be **beyond reproach** on that point, and the host isolates it as
    far as it can — but it cannot isolate it from the time it takes.
    """

    #: What appears in the list of acquisition sources.
    LABEL: str = ""

    def open(self, context: "Context") -> bool:            # noqa: F821
        raise NotImplementedError

    def read(self) -> Optional[np.ndarray]:
        """Returns the available block of samples, in volts, or None."""
        raise NotImplementedError

    def close(self) -> None:
        """Closes what was opened."""
