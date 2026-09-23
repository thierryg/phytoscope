# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/api/registry.py
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

"""The registry — discovers modules, loads them, and keeps them contained.

Three places are searched, in this order:

1. ``phytoscope/modules/`` — the **built-in modules**, shipped with the
   software. They cannot be uninstalled; they can be disabled.
2. ``<configuration>/modules/`` — the ones the user installed themselves.
   That is where the SDK puts what you write.
3. Python packages declaring a ``phytoscope.modules`` entry point — for a
   module distributed on PyPI.

Every module is a **directory** containing at least ``module.py``. That file
declares a class inheriting from `Module`, with its `MANIFEST`.

How containment works
---------------------

The principle fits in one sentence: **a module that misbehaves is disabled,
never tolerated**. Concretely:

* a fault at import, at install time, or inside a capability **disables the
  module for the session** and records it in the log, with its full
  traceback;
* the software carries on, missing that module and that module alone;
* the Diagnostics tab shows what was disabled and why.

This is not a sandbox — it is Python, and a module can write wherever it
likes. It is a **discipline of good neighborliness**, backed by a safety net:
nobody loses an eight-hour session because one module went wrong.

Why there is no hot reloading
-----------------------------

We considered it and ruled it out. Reloading a module whose objects are
already referenced elsewhere — a subscription, a displayed curve — leaves two
versions in memory and produces bugs nobody can read. A restart costs three
seconds; a reload bug costs an evening.
"""
from __future__ import annotations

import importlib.util
import os
import sys
import traceback
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type

from .context import Context
from .contract import API_VERSION, Capability, Manifest, Module, compatible

__all__ = ["Registry", "LoadedModule", "ModuleState"]

#  Sentinel: tells "no value" apart from "a value we cannot evaluate without
#  running the module".
_INEVALUABLE = object()


class ModuleState:
    """Where a module stands."""
    DISCOVERED = "discovered"        # found, not imported yet
    LOADED = "loaded"              # imported and instantiated
    ACTIVE = "active"                # installed, running
    DISABLED = "disabled"        # the user does not want it
    FAULTED = "faulted"          # raised — withdrawn for the session
    INCOMPATIBLE = "incompatible"  # targets an API we cannot honor


@dataclass
class LoadedModule:
    """A module, its manifest, its state, and what happened to it."""
    manifest: Manifest
    path: str = ""
    origin: str = "built_in"       # built_in | utilisateur | package
    state: str = ModuleState.DISCOVERED
    instance: Optional[Module] = None
    context: Optional[Context] = None
    fault: str = ""                # the message, in plain words
    trace: str = ""                # the full traceback, for the log

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def usable(self) -> bool:
        return self.state == ModuleState.ACTIVE and self.instance is not None

    def provides(self, capability: str) -> bool:
        return self.usable and capability in self.manifest.capabilities


class Registry:
    """Discovers, loads and holds the modules. One per session."""

    MODULE_FILE = "module.py"

    def __init__(self, engine: Any, settings: Any) -> None:
        self._engine = engine
        self._settings = settings
        self.modules: Dict[str, LoadedModule] = {}
        self._order: List[str] = []

    # -- the paths -----------------------------------------------------------
    @staticmethod
    def builtin_directory() -> str:
        return os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "modules")

    @staticmethod
    def user_directory() -> str:
        from ..config import config_dir
        return os.path.join(config_dir(), "modules")

    # -- discovery -----------------------------------------------------------
    def discover(self) -> List[LoadedModule]:
        """Finds the modules without importing a single one.

        Without importing a single one: that is what makes it possible to
        list what is present, to disable one, and to refuse the one targeting
        an unknown API — without having to run its code to find out.
        """
        found: List[LoadedModule] = []
        for directory, origin in ((self.builtin_directory(), "built_in"),
                                 (self.user_directory(), "user")):
            if not os.path.isdir(directory):
                continue
            for name in sorted(os.listdir(directory)):
                path = os.path.join(directory, name)
                file_path = os.path.join(path, self.MODULE_FILE)
                if not os.path.isfile(file_path):
                    continue
                manifest = self._read_manifest(file_path, name)
                if manifest is None:
                    continue
                found.append(LoadedModule(manifest=manifest, path=path,
                                            origin=origin))
        found += self._discover_packages()

        for m in found:
            problems = m.manifest.problems()
            if problems:
                m.state = ModuleState.INCOMPATIBLE
                m.fault = " ; ".join(problems)
            elif not self._enabled(m.name, m.manifest):
                m.state = ModuleState.DISABLED
            missing = [p for p in m.manifest.requires
                          if importlib.util.find_spec(p) is None]
            if missing and m.state != ModuleState.INCOMPATIBLE:
                m.state = ModuleState.INCOMPATIBLE
                m.fault = (f"missing library/libraries: "
                           f"{', '.join(missing)}"
                           f" — pip install {' '.join(missing)}")
            self.modules[m.name] = m
        return found

    def _discover_packages(self) -> List[LoadedModule]:
        """The modules installed as Python packages.

        Optional, and harmless if there are none: `importlib.metadata` has
        been in the standard library since 3.8, but the enumeration can fail
        on a damaged installation — which is no reason not to start up.
        """
        found: List[LoadedModule] = []
        try:
            from importlib.metadata import entry_points
            points = entry_points()
            group = (points.select(group="phytoscope.modules")
                      if hasattr(points, "select")
                      else points.get("phytoscope.modules", ()))
        except Exception:                                  # noqa: BLE001
            return found
        for point in group:
            try:
                factory = point.load()
                manifest = getattr(factory, "MANIFEST", None)
                if isinstance(manifest, Manifest):
                    m = LoadedModule(manifest=manifest, origin="package")
                    m.instance = None
                    m._cls = factory                   # type: ignore[attr-defined]
                    found.append(m)
            except Exception as exc:                       # noqa: BLE001
                from ..core.logging_setup import get_logger
                get_logger("modules").warning(
                    "Entry point \u201c%s\u201d ignored: %s", point.name, exc)
        return found

    def _read_manifest(self, file_path: str, directory: str) -> Optional[Manifest]:
        """Extracts the manifest by parsing, without running the code.

        We read the file's syntax tree and look for the `Manifest(...)`
        call. Running the module in order to learn its manifest would amount
        to trusting it before knowing whether it deserves that.
        """
        import ast
        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), file_path)
        except (OSError, SyntaxError) as exc:
            from ..core.logging_setup import get_logger
            get_logger("modules").error(
                "\u201c%s\u201d cannot be read: %s", directory, exc)
            return None

        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and getattr(node.func, "id", "") == "Manifest"):
                continue
            values: Dict[str, Any] = {}
            for mc in node.keywords:
                value = self._evaluate(mc.value)
                if value is not _INEVALUABLE:
                    values[mc.arg] = value
            if "name" not in values:
                values["name"] = directory
            for field_name in ("capabilities", "depends_on", "requires"):
                if field_name in values and not isinstance(values[field_name], tuple):
                    values[field_name] = tuple(values[field_name] or ())
            try:
                return Manifest(**values)
            except TypeError as exc:
                from ..core.logging_setup import get_logger
                get_logger("modules").error(
                    "Manifest of \u201c%s\u201d is invalid: %s", directory, exc)
                return None
        return None

    @staticmethod
    def _evaluate(node: Any) -> Any:
        """Evaluates a manifest value without running the module.

        `ast.literal_eval` only knows literals. But we write
        `capabilities=(Capability.ANALYSER,)`, which reads better than a bare
        string and is less prone to typos. So attributes of `Capability` are
        resolved as well, since those are constants of the contract — and
        nothing else: evaluating an arbitrary expression would amount to
        running the module, which is precisely what we are avoiding.
        """
        import ast as _ast
        if isinstance(node, _ast.Attribute):
            owner = getattr(node.value, "id", "")
            if owner == "Capability":
                value = getattr(Capability, node.attr, _INEVALUABLE)
                return value if isinstance(value, str) else _INEVALUABLE
            return _INEVALUABLE
        if isinstance(node, (_ast.Tuple, _ast.List)):
            elements = [Registry._evaluate(e) for e in node.elts]
            if any(e is _INEVALUABLE for e in elements):
                return _INEVALUABLE
            return tuple(elements)
        try:
            return _ast.literal_eval(node)
        except (ValueError, SyntaxError, TypeError):
            return _INEVALUABLE

    def _enabled(self, name: str, manifest: Manifest) -> bool:
        """Does the user want this module?

        Yes by default for built-in modules, and yes as well for the ones the
        user installed themselves — installing one is already a choice. The
        settings file holds nothing but the exceptions.
        """
        try:
            disabled = set(getattr(self._settings.modules, "disabled", ()))
        except Exception:                                  # noqa: BLE001
            disabled = set()
        return name not in disabled

    # -- loading -------------------------------------------------------------
    def load_all(self) -> int:
        """Loads and installs everything usable. Returns the count."""
        if not self.modules:
            self.discover()
        for name in self._order_them():
            self.load(name)
        active = 0
        for name in self._order:
            if self._setup(name):
                active += 1
        return active

    def _order_them(self) -> List[str]:
        """Dependencies first, then alphabetical order.

        Deterministic: two launches give the same order. A dependency cycle
        is reported and broken — we load anyway, in alphabetical order,
        rather than loading nothing at all.
        """
        remaining = {n: set(m.manifest.depends_on) & set(self.modules)
                    for n, m in self.modules.items()}
        order: List[str] = []
        while remaining:
            ready = sorted(n for n, d in remaining.items() if not (d - set(order)))
            if not ready:
                cycle = ", ".join(sorted(remaining))
                from ..core.logging_setup import get_logger
                get_logger("modules").error(
                    "Dependency cycle between modules: %s — loaded in "
                    "alphabetical order", cycle)
                order += sorted(remaining)
                break
            order += ready
            for n in ready:
                remaining.pop(n, None)
        self._order = order
        return order

    def load(self, name: str) -> bool:
        """Imports and instantiates a module. Returns true if it worked."""
        m = self.modules.get(name)
        if m is None or m.state in (ModuleState.DISABLED,
                                   ModuleState.INCOMPATIBLE,
                                   ModuleState.FAULTED):
            return False
        try:
            cls = self._module_class(m)
            if cls is None:
                raise ImportError(
                    f"no class inheriting from Module in \u201c{name}\u201d")
            m.context = Context(name, self._engine, self._settings,
                                self.user_directory(),
                                api_required=m.manifest.api)
            instance = cls(m.context)
            problems = {}
            try:
                problems = dict(instance.default_settings() or {})
            except Exception:                              # noqa: BLE001
                pass
            problems.update(self._stored_settings(name))
            m.context._set_settings(problems)
            m.instance = instance
            m.state = ModuleState.LOADED
            return True
        except Exception as exc:                           # noqa: BLE001
            self._mark_faulted(m, "loading", exc)
            return False

    def _module_class(self, m: LoadedModule) -> Optional[Type[Module]]:
        cls = getattr(m, "_cls", None)
        if cls is not None:
            return cls
        file_path = os.path.join(m.path, self.MODULE_FILE)
        internal_name = f"phytoscope_module_{m.name.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(internal_name, file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"\u201c{file_path}\u201d is not importable")
        package = importlib.util.module_from_spec(spec)
        #  Registered before execution: the module's `@dataclass` decorators
        #  would otherwise look up `sys.modules[cls.__module__]` and fail.
        sys.modules[internal_name] = package
        spec.loader.exec_module(package)
        for obj in vars(package).values():
            if (isinstance(obj, type) and issubclass(obj, Module)
                    and obj is not Module):
                return obj
        return None

    def _setup(self, name: str) -> bool:
        m = self.modules.get(name)
        if m is None or m.state != ModuleState.LOADED or m.instance is None:
            return False
        try:
            m.instance.setup()
            m.state = ModuleState.ACTIVE
            return True
        except Exception as exc:                           # noqa: BLE001
            self._mark_faulted(m, "installation", exc)
            return False

    def _mark_faulted(self, m: LoadedModule, stage: str,
                         exc: BaseException) -> None:
        """Disables a faulty module, and says why — once."""
        m.state = ModuleState.FAULTED
        m.fault = f"{type(exc).__name__} during {stage}: {exc}"
        m.trace = traceback.format_exc()
        from .events import BUS
        BUS.unsubscribe_module(m.name)
        from ..core.logging_setup import get_logger
        log = get_logger("modules")
        log.error("Module \u201c%s\u201d disabled — %s", m.name, m.fault)
        log.debug("Traceback of module \u201c%s\u201d:\n%s", m.name, m.trace)

    # -- settings ------------------------------------------------------------
    def _stored_settings(self, name: str) -> Dict[str, Any]:
        try:
            return dict(getattr(self._settings.modules, "settings", {}).get(name, {}))
        except Exception:                                  # noqa: BLE001
            return {}

    def collect_settings(self) -> Dict[str, Dict[str, Any]]:
        """What has to be saved at shutdown."""
        return {n: dict(m.context.settings)
                for n, m in self.modules.items()
                if m.context is not None and m.context.settings}

    # -- use -----------------------------------------------------------------
    def active(self) -> List[LoadedModule]:
        return [self.modules[n] for n in self._order
                if n in self.modules and self.modules[n].usable]

    def api_requirements(self) -> Dict[str, Tuple[int, int]]:
        """What each module needs, as (major, minor) — the minimum it stated.

        The reciprocal of `Context.api_version`: a module can ask what it is
        running on, and the host can ask what each module needs. Both go
        through `parse_version`, so the two answers cannot drift apart.
        """
        return {name: m.manifest.api_required
                for name, m in self.modules.items()}

    def providers(self, capability: str) -> List[LoadedModule]:
        """The active modules providing a capability, in order."""
        return [m for m in self.active() if m.provides(capability)]

    def call(self, m: LoadedModule, method: str, *args: Any,
                fallback: Any = None, **kwargs: Any) -> Any:
        """Calls a module method **under protection**.

        This is the only path by which the host touches a module. A fault
        disables the module and returns `fallback`: the caller does not have to
        worry about it, and the session carries on.
        """
        if m.instance is None:
            return fallback
        try:
            return getattr(m.instance, method)(*args, **kwargs)
        except Exception as exc:                           # noqa: BLE001
            self._mark_faulted(m, f"the call to \u201c{method}\u201d", exc)
            return fallback

    def shutdown_all(self) -> None:
        """Stops the modules, in the reverse of their loading order."""
        for name in reversed(self._order):
            m = self.modules.get(name)
            if m is None or m.instance is None:
                continue
            if m.state == ModuleState.ACTIVE:
                self.call(m, "shutdown")
            if m.context is not None:
                m.context._unsubscribe_all()
        from .events import BUS
        BUS.clear()

    # -- for the diagnostics -------------------------------------------------
    def report(self) -> List[Dict[str, Any]]:
        """The state of every module, for the Diagnostics tab."""
        rows = []
        for name in (self._order or sorted(self.modules)):
            m = self.modules.get(name)
            if m is None:
                continue
            rows.append({
                "name": name,
                "title": m.manifest.title,
                "version": m.manifest.version,
                "api": m.manifest.api,
                "origin": m.origin,
                "state": m.state,
                "capabilities": ", ".join(m.manifest.capabilities),
                "fault": m.fault,
            })
        return rows
