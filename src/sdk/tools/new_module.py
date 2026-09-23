#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/sdk/tools/new_module.py
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

"""Creates a PhytoScope module: the directory, the skeleton and the tests.

The point of such a tool is not to type less. It is that **the skeleton it
produces is already correct**: the manifest is valid, the tests pass, and the
pitfalls described in the manual are already avoided. One starts from a module
that works and replaces what one wants — rather than starting from a blank
page and discovering the rules one at a time, by breaking them.

.. code-block:: console

    python3 src/sdk/tools/new_module.py my-module
    python3 src/sdk/tools/new_module.py my-module --capability descriptor
    python3 src/sdk/tools/new_module.py my-module --install

`--install` drops it straight into your installation's modules directory,
ready to be tried at the next start-up.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
#  `<root>/phytoscope` is the software's source tree, which holds the second
#  `phytoscope/` — the importable package. The path said `software/phytoscope`
#  until 2026-09-23, a directory that has never existed: `api_version()` then
#  fell back silently, and a module created against a 2.1 host would have
#  claimed 2.0. A test reads this path and checks the file is there.
SOFTWARE = os.path.join(ROOT, "phytoscope")

#  The capabilities the host actually asks the registry for, as of
#  PhytoScope 1.5. `ui/tabs.py` calls `providers(Capability.ANALYSER)` and
#  `ui/features_tab.py` calls `providers(Capability.DESCRIPTOR)`; nothing
#  calls it for the other three. A module of one of those other kinds loads
#  and shows as active, and is never called — so the tool says so, rather
#  than letting someone look for the mistake in their own code.
CONSUMED = ("analyser", "descriptor")

#  The capability names as API 2.0 spelled them. A command line written
#  against 2.0 still says `--capacite descripteur`; it is translated rather
#  than refused. The MANIFEST the tool writes always carries the 3.0
#  spelling, because that is the only one the host will accept.
LEGACY_NAMES = {
    "analyseur": "analyser",
    "descripteur": "descriptor",
    "sonificateur": "sonifier",
    "exportateur": "exporter",
}

#  The capabilities, and what has to be written for each. The text comes from
#  here rather than from the contract: the tool has to work even when the
#  software is not installed — one writes a module before trying it.
#
#  The keys are the values of `Capability` in `phytoscope.api`, because that is
#  what goes into the manifest.
CAPABILITIES: Dict[str, Dict[str, str]] = {
    "analyser": {
        "class": "Analyser",
        "summary": "computes quantities over a window of signal",
        "body": '''    #  How many seconds of signal you want, and whether you want it RAW
    #  — before the notch and the low-pass. Raw for any noise measurement:
    #  filtering before measuring noise amounts to measuring your own filter.
    WINDOW_S = 60.0
    RAW_SIGNAL = False

    def analyse(self, x: np.ndarray, fs: float,
                 context: Context) -> List[Quantity]:
        """Returns the quantities to display. An empty list is acceptable.

        :param x: the signal, **in volts**, in chronological order.
        :param fs: the actual sampling rate, in hertz.
        """
        if x.size < 64:
            return []

        return [Quantity(
            key="peak-amplitude",
            label="Peak amplitude",
            value=float(np.max(np.abs(x - x.mean()))),
            text=f"{np.max(np.abs(x - x.mean())) * 1e6:.1f} µV",
            #  `meaning` is not decorative: say what this number means AND what
            #  it does not allow one to conclude. Without it, the interface
            #  will write "the module does not explain this value".
            meaning=("The largest departure from the mean over the window. It is "
                  "sensitive to a single artefact: a slamming door is enough "
                  "to treble it."),
        )]
''',
    },
    "descriptor": {
        "class": "Descriptor",
        "summary": "produces a representation of the signal — a curve",
        "body": '''    WINDOW_S = 60.0
    RAW_SIGNAL = False

    def describe(self, x: np.ndarray, fs: float,
                context: Context) -> List[Trace]:
        """Returns the curves to display. An empty list is acceptable."""
        if x.size < 64:
            return []

        t = np.arange(x.size) / fs
        return [Trace(
            x=t, y=x * 1e6,
            title=context.translate("My representation"),
            x_label=context.translate("time (s)"),
            y_label="µV",
            #  What your representation assumes, and what it does not allow
            #  one to conclude. Displayed under the curve.
            warning=context.translate(
                "Say here what this representation assumes."),
        )]
''',
    },
    "sonifier": {
        "class": "Sonifier",
        "summary": "turns a measured value into notes",
        "body": '''    def sonify(self, value_v: float,
                 context: Context) -> List[ProposedNote]:
        """Returns the notes proposed. **Be quick**: this is called inside the
        musical rendering loop. An empty list means "no note", which is a
        legitimate answer.
        """
        #  A deliberately simple example: the higher the voltage, the higher
        #  the note. A diatonic scale, so that it is listenable.
        gamme = (0, 2, 4, 5, 7, 9, 11)
        rang = int(abs(value_v) * 1e6) % len(gamme)
        return [ProposedNote(
            midi_pitch=60 + gamme[rang],
            velocity=70,
            duration_s=0.4,
            #  The value that produced the note: kept in the rendering, so
            #  that one can always get back from the note to the measurement.
            source_v=value_v,
        )]
''',
    },
    "exporter": {
        "class": "Exporter",
        "summary": "writes a session in another format",
        "body": '''    #  What appears in the list of formats, and the extension produced.
    FORMAT = "My format"
    EXTENSION = ".txt"

    def export(self, session: str, target: str, context: Context) -> bool:
        """Writes the session `session` into the file `target`.

        Returns true if the write succeeded. Write ONLY into `target`: the
        session's directory is not yours.
        """
        source = os.path.join(session, "mesures.csv")
        if not os.path.exists(source):
            context.log(f"“{source}” not found", "warning")
            return False
        with open(source, encoding="utf-8") as entree, \\
             open(target, "w", encoding="utf-8") as sortie:
            for ligne in entree:
                sortie.write(ligne)
        return True
''',
    },
}

MODULE_TEMPLATE = '''# -*- coding: utf-8 -*-
"""{title} — {summary}.

Write here what this module does, and above all **what it does not do**. The
software insists that every representation say what it assumes and what it
does not allow one to conclude; that starts with the documentation.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import numpy as np

#  Everything a module needs comes from here, and from nowhere else. What is
#  not in `phytoscope.api` may change without notice.
from phytoscope.api import ({imports})


class {python_class}(Module, {capability_class}):
    """{title}."""

    MANIFEST = Manifest(
        name="{name}",
        title="{title}",
        version="0.1.0",
        api="{api}",
        description="{summary}.",
        author="{author}",
        licence="MIT",
        capabilities=(Capability.{capability_upper},),
        #  The libraries you need. The software checks BEFORE importing and
        #  displays "module disabled: scipy missing" rather than a traceback.
        # requires=("scipy",),
    )

    # ── Getting ready ────────────────────────────────────────────────────────
    def setup(self) -> None:
        """Called once, after every module has been loaded.

        This is where you subscribe and prepare your files — **not** in
        `__init__`, which is called for every module at start-up and must stay
        instantaneous.
        """
        self.context.log("{name} installed")

    def shutdown(self) -> None:
        """Called once, at shutdown. Close what you opened.

        Your subscriptions are removed by the host: there is no need to deal
        with them.
        """

    def default_settings(self) -> Dict[str, Any]:
        """Your settings and their initial values.

        The software keeps them under your module's name and hands them back
        through `context.settings`. Never write into the software's own
        settings.
        """
        return {{}}

    # ── Working ──────────────────────────────────────────────────────────────
{body}'''

TEST_TEMPLATE = '''# -*- coding: utf-8 -*-
"""Tests for "{name}" — no running software, no hardware.

    python3 -m pytest {test_path} -v
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Dict, List

import numpy as np
import pytest


class FakeContext:
    """A fake context: the same surface, with nothing behind it."""

    def __init__(self, settings: Dict[str, Any] | None = None) -> None:
        self.settings: Dict[str, Any] = dict(settings or {{}})
        self.subscriptions: Dict[str, List] = {{}}
        self.logged: List[str] = []
        self.rate_hz = 250.0
        self.full_scale_v = 2.5
        self.mains_hz = 50.0

    def subscribe(self, event, callback):
        self.subscriptions.setdefault(event, []).append(callback)

    def log(self, message, level="info"):
        self.logged.append(f"{{level}}: {{message}}")

    def message(self, text):
        self.logged.append(f"message: {{text}}")

    def translate(self, text):
        return text

    def directory(self):
        import tempfile
        return tempfile.mkdtemp(prefix="test-{name}-")

    def signal(self, seconds=60.0, raw=False):
        return fake_signal(seconds)

    def event_times(self):
        return []

    def state(self):
        from types import SimpleNamespace
        return SimpleNamespace(duration_s=120.0, source="test", running=True,
                               replaying=False)


def fake_signal(seconds=30.0, fs=250.0):
    """A plausible signal: noise, a drift, and a few bursts."""
    n = int(seconds * fs)
    t = np.arange(n) / fs
    r = np.random.default_rng(42)
    x = r.normal(0.0, 3e-6, n)
    x += 4e-5 * np.sin(2 * np.pi * t / 400.0)
    for t0 in np.arange(5.0, seconds, 7.0):
        x += 1.2e-4 * np.exp(-((t - t0) / 1.5) ** 2)
    return x


@pytest.fixture()
def instance():
    from phytoscope.api import Module
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "{internal_name}", os.path.join(here, "module.py"))
    package = importlib.util.module_from_spec(spec)
    #  Registered BEFORE execution: `@dataclass` looks up
    #  `sys.modules[cls.__module__]` and would fail otherwise. The name is
    #  specific to this module, so that two modules can coexist in one
    #  pytest session.
    sys.modules["{internal_name}"] = package
    spec.loader.exec_module(package)
    module_cls = next(o for o in vars(package).values()
                      if isinstance(o, type) and issubclass(o, Module)
                      and o is not Module)
    context = FakeContext(
        settings=module_cls(FakeContext()).default_settings())
    obj = module_cls(context)
    obj.setup()
    return obj


def test_the_manifest_is_valid(instance):
    """A rejected manifest, and the module is never loaded."""
    assert instance.MANIFEST.problems() == [], instance.MANIFEST.problems()


def test_the_manifest_targets_a_known_api(instance):
    from phytoscope.api import compatible
    assert compatible(instance.MANIFEST.api)


{capability_tests}

def test_shutdown_does_not_raise(instance):
    instance.shutdown()
'''

TESTS_BY_CAPABILITY = {
    "analyser": '''def test_analyse_returns_complete_quantities(instance):
    """Every quantity has to say what it means."""
    quantities = instance.analyse(fake_signal(30.0), 250.0, instance.context)
    assert quantities, "the module returned nothing on a valid signal"
    for g in quantities:
        assert g.key and g.label
        assert g.text
        assert len(g.meaning) > 20, (
            f"“{g.key}” does not explain what it means")
        assert np.isfinite(g.value)


def test_an_empty_signal_does_not_raise(instance):
    """“Nothing to say” is said with an empty list, never with an exception."""
    assert instance.analyse(np.zeros(0), 250.0, instance.context) == []
''',
    "descriptor": '''def test_describe_returns_consistent_traces(instance):
    traces = instance.describe(fake_signal(30.0), 250.0, instance.context)
    assert traces, "the module returned no trace at all"
    for tr in traces:
        assert tr.x.size == tr.y.size
        assert tr.title
        assert tr.warning, (
            "say what this representation does not allow one to conclude")


def test_an_empty_signal_does_not_raise(instance):
    assert instance.describe(np.zeros(0), 250.0, instance.context) == []
''',
    "sonifier": '''def test_sonify_returns_playable_notes(instance):
    notes = instance.sonify(1.2e-4, instance.context)
    for n in notes:
        assert 0 <= n.midi_pitch <= 127, "MIDI pitch out of bounds"
        assert 0 <= n.velocity <= 127
        assert n.duration_s > 0
        assert n.source_v == 1.2e-4, "the originating measurement is kept"


def test_a_zero_value_does_not_raise(instance):
    instance.sonify(0.0, instance.context)
''',
    "exporter": '''def test_export_writes_the_file(instance, tmp_path):
    session = tmp_path / "session"
    session.mkdir()
    (session / "mesures.csv").write_text("t;v\\n0;1e-6\\n", encoding="utf-8")
    target = tmp_path / ("output" + instance.EXTENSION)
    assert instance.export(str(session), str(target), instance.context)
    assert target.exists() and target.stat().st_size > 0


def test_a_missing_session_returns_false_without_raising(instance, tmp_path):
    target = tmp_path / ("output" + instance.EXTENSION)
    assert instance.export(str(tmp_path / "nothing"), str(target),
                             instance.context) is False
''',
}


def modules_directory() -> str:
    """The installation's modules directory, according to the system."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "PhytoScope", "modules")
    if sys.platform == "darwin":
        return os.path.expanduser(
            "~/Library/Application Support/PhytoScope/modules")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "phytoscope", "modules")


def contract_path() -> str:
    """Where `API_VERSION` is written, when the source tree is at hand."""
    return os.path.join(SOFTWARE, "phytoscope", "api", "contract.py")


def api_version() -> str:
    """The software's API version if it is there, otherwise a safe value."""
    try:
        with open(contract_path(), encoding="utf-8") as f:
            m = re.search(r'^API_VERSION\s*=\s*"([^"]+)"', f.read(), re.M)
        if m:
            return m.group(1)
    except OSError:
        pass
    #  The fallback follows API_VERSION: frozen at "1.0", it would have
    #  produced a module the host refuses ever since the event names changed.
    return "2.0"


def python_class(name: str) -> str:
    """“my-module” → “MyModule”."""
    return "".join(p.capitalize() for p in re.split(r"[-_]", name) if p)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="new_module.py",
        description="Creates a PhytoScope module, ready to be tried.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Capabilities: " + " · ".join(
            f"{c} ({d['summary']})" for c, d in CAPABILITIES.items()))
    p.add_argument("name", help="the module's identifier: a-z, 0-9 and hyphens")
    #  The French spellings are kept as aliases, for the option names and
    #  for the capability values alike: they were the only ones until
    #  2026-09-23, and someone's script may still use them.
    p.add_argument("--capability", "--capacite", default="analyser",
                   choices=sorted(CAPABILITIES) + sorted(LEGACY_NAMES),
                   metavar="NAME", dest="capability",
                   help="what the module provides (default: analyser) — "
                        + ", ".join(sorted(CAPABILITIES)))
    p.add_argument("--title", "--titre", default="", dest="title",
                   help="what the user will read")
    p.add_argument("--author", "--auteur", default="Your name", dest="author")
    p.add_argument("--in", "--dans", default="", dest="where",
                   metavar="DIRECTORY",
                   help="where to create the module (default: here)")
    p.add_argument("--install", "--installer", action="store_true",
                   dest="install",
                   help="create it straight in your installation's modules "
                        "directory")
    args = p.parse_args(argv)
    if args.capability in LEGACY_NAMES:
        was = args.capability
        args.capability = LEGACY_NAMES[was]
        print(f"  · “{was}” is the API 2.0 name for this capability; "
              f"writing “{args.capability}”.")

    if not re.match(r"^[a-z][a-z0-9-]{1,48}$", args.name):
        print(f"✗ “{args.name}” is not a valid name: lowercase letters, "
              "digits and hyphens, 2 to 49 characters, starting with a "
              "letter.", file=sys.stderr)
        return 2

    base = (modules_directory() if args.install
            else (args.where or os.getcwd()))
    target = os.path.join(base, args.name)
    if os.path.exists(target):
        print(f"✗ “{target}” already exists.", file=sys.stderr)
        return 1
    os.makedirs(target, exist_ok=True)

    capability = CAPABILITIES[args.capability]
    title = args.title or args.name.replace("-", " ").capitalize()

    #  The imports: only what the skeleton actually uses. An unused import in
    #  an example is an invitation to add more without thinking.
    needed = ["Capability", "Context", "Manifest", "Module",
              capability["class"]]
    needed += {"analyser": ["Quantity"], "descriptor": ["Trace"],
               "sonifier": ["ProposedNote"],
               "exporter": []}[args.capability]
    imports = ", ".join(sorted(set(needed)))
    if len(imports) > 62:
        imports = ",\n                            ".join(sorted(set(needed)))

    with open(os.path.join(target, "module.py"), "w", encoding="utf-8") as f:
        f.write(MODULE_TEMPLATE.format(
            title=title, summary=capability["summary"], imports=imports,
            python_class=python_class(args.name),
            capability_class=capability["class"], name=args.name,
            api=api_version(), author=args.author,
            capability_upper=args.capability.upper(), body=capability["body"]))

    #  "test_<name>.py" and not "test_module.py": two test files with the same
    #  name, in two directories without an `__init__.py`, cannot be collected
    #  in the same pytest session. A module that cannot be tested alongside
    #  the others is a module that will be tested less.
    test_name = "test_" + args.name.replace("-", "_") + ".py"
    with open(os.path.join(target, test_name), "w", encoding="utf-8") as f:
        f.write(TEST_TEMPLATE.format(
            name=args.name,
            internal_name="module_" + args.name.replace("-", "_"),
            test_path=os.path.join(args.name, test_name),
            capability_tests=TESTS_BY_CAPABILITY[args.capability]))

    with open(os.path.join(target, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"""# {title}

{capability['summary'].capitalize()}.

## Testing

```bash
python3 -m pytest {args.name}/{test_name} -v
```

The tests need neither the software running nor any hardware.

## Installing

```bash
cp -r {args.name} "{modules_directory()}"
```

Then restart PhytoScope. The Diagnostics tab shows the module and, if it was
refused, says why in one sentence.

## To do

- [ ] write what this module does, and what it does not do
- [ ] fill in `meaning` for every value produced
- [ ] replace the manifest's author and licence
- [ ] add your own tests
""")

    print()
    print(f"  ✓ Module “{args.name}” created in {target}")
    print()
    #  The gutter is computed rather than fixed: the name of the test file
    #  follows the module's, and a long name would otherwise run into its
    #  own description.
    rows = (("module.py", f"the skeleton, with {args.capability}"),
            (test_name, "tests that already pass"),
            ("README.md", ""))
    gutter = max(len(n) for n, _ in rows) + 2
    for filename, note in rows:
        print(f"      {filename.ljust(gutter)}{note}".rstrip())
    if args.capability not in CONSUMED:
        print()
        print(f"  ! PhytoScope 1.5 does not call the “{args.capability}”")
        print("    capability yet: the module will load and show as active,")
        print("    and will never be called. Only “analyseur” and")
        print("    “descripteur” are consumed.")
    print()
    print("  Test it:")
    print(f"      python3 -m pytest {os.path.join(target, test_name)} -v")
    print()
    if args.install:
        print("  It is already in place: restart PhytoScope.")
    else:
        print("  Then install it:")
        print(f"      cp -r {target} '{modules_directory()}'")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
