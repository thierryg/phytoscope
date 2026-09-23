# 8. Migrating from 2.0

Every name in the interface changed on 2026-09-23: the surface was French, and
the repository turned to technical US English. `API_VERSION` went from `"2.0"`
to `"3.0"` in the same change, which is exactly what the major number is for.

**Your 2.0 module will not run, and it will not half-run.** The host reads its
manifest without importing it, sees `api="2.0"`, and refuses it at discovery
with one sentence in Diagnostics:

```
incompatible — targets API 2.0, but this software offers 3.0
```

Nothing is aliased. That is deliberate: an alias would let the module load and
then fail on the first field it read, halfway through a session — which is the
failure a major bump exists to prevent. A refusal you can read at start-up is
worth more than a module that works until it does not.

---

## Doing it

Three steps, and the tests will tell you when you are done.

1. **`api="3.0"`** in the manifest.
2. **Rename**, with the table below. Every one is a plain rename: no
   behaviour changed, no argument moved, nothing was added or taken away.
3. **Run your tests.** If they were written against the SDK's fake context,
   rename the names in it too — or copy the current one out of
   `src/sdk/hello-world/test_hello_world.py`, which is shorter than patching.

There is no step four. The interface does the same things it did, under names
somebody who does not read French can follow.

---

## The table


### The contract

| 2.0 | 3.0 |
|---|---|
| `VERSION_API` | `API_VERSION` |
| `Manifeste` | `Manifest` |
| `MANIFESTE` | `MANIFEST` |
| `Capacite` | `Capability` |
| `Capacite.TOUTES` | `Capability.ALL` |
| `Capacite.ANALYSEUR` | `Capability.ANALYSER` |
| `Capacite.DESCRIPTEUR` | `Capability.DESCRIPTOR` |
| `Capacite.SONIFICATEUR` | `Capability.SONIFIER` |
| `Capacite.EXPORTATEUR` | `Capability.EXPORTER` |


### The manifest's fields

| 2.0 | 3.0 |
|---|---|
| `nom` | `name` |
| `titre` | `title` |
| `auteur` | `author` |
| `site` | `website` |
| `capacites` | `capabilities` |
| `depend_de` | `depends_on` |
| `exige` | `requires` |
| `integre` | `built_in` |
| `valide` | `valid` |
| `defauts()` | `problems()` |


### The module's life cycle

| 2.0 | 3.0 |
|---|---|
| `installer()` | `setup()` |
| `arreter()` | `shutdown()` |
| `reglages_par_defaut()` | `default_settings()` |
| `self.contexte` | `self.context` |


### The five capabilities

| 2.0 | 3.0 |
|---|---|
| `Analyseur` | `Analyser` |
| `Descripteur` | `Descriptor` |
| `Sonificateur` | `Sonifier` |
| `Exportateur` | `Exporter` |
| `Source` | Source — unchanged |
| `analyser()` | `analyse()` |
| `decrire()` | `describe()` |
| `sonifier()` | `sonify()` |
| `exporter()` | `export()` |
| `ouvrir()` | `open()` |
| `lire()` | `read()` |
| `fermer()` | `close()` |
| `FENETRE_S` | `WINDOW_S` |
| `SIGNAL_BRUT` | `RAW_SIGNAL` |
| `LIBELLE` | `LABEL` |


### What they exchange

| 2.0 | 3.0 |
|---|---|
| `Grandeur` | `Quantity` |
| `cle` | `key` |
| `libelle` | `label` |
| `valeur` | `value` |
| `texte` | `text` |
| `sens` | `meaning` |
| `alerte` | `alert` |
| `params` | params — unchanged |
| `Trace.titre` | `Trace.title` |
| `Trace.x_libelle` | `Trace.x_label` |
| `Trace.y_libelle` | `Trace.y_label` |
| `Trace.avertissement` | `Trace.warning` |
| `NoteProposee` | `ProposedNote` |
| `hauteur_midi` | `midi_pitch` |
| `velocite` | `velocity` |
| `duree_s` | `duration_s` |
| `canal` | `channel` |
| `origine_v` | `source_v` |


### The context

| 2.0 | 3.0 |
|---|---|
| `Contexte` | `Context` |
| `EtatMesure` | `MeasurementState` |
| `contexte.signal(secondes, brut)` | `context.signal(seconds, raw)` |
| `contexte.frequence_hz` | `context.rate_hz` |
| `contexte.pleine_echelle_v` | `context.full_scale_v` |
| `contexte.reseau_hz` | `context.mains_hz` |
| `contexte.etat()` | `context.state()` |
| `contexte.instants_evenements()` | `context.event_times()` |
| `contexte.dossier()` | `context.directory()` |
| `contexte.reglages` | `context.settings` |
| `contexte.journal()` | `context.log()` |
| `contexte.traduire()` | `context.translate()` |
| `contexte.abonner()` | `context.subscribe()` |
| `contexte.message()` | context.message() — unchanged |


### The measurement state

| 2.0 | 3.0 |
|---|---|
| `en_marche` | `running` |
| `duree_s` | `elapsed_s` |
| `frequence_hz` | `rate_hz` |
| `tension_v` | `value_v` |
| `ligne_de_base_v` | `baseline_v` |
| `bruit_efficace_v` | `rms_v` |
| `crete_a_crete_v` | `pp_v` |
| `derive_v_par_min` | `drift_v_per_min` |
| `sature` | `saturated` |
| `evenements` | `events` |
| `enregistre` | `recording` |
| `relecture` | `replaying` |


### The events

| 2.0 | 3.0 |
|---|---|
| `EVENEMENTS` | `EVENTS` |
| `the eleven constants` | unchanged — they were renamed in 2.0 |


### The states shown in Diagnostics

| 2.0 | 3.0 |
|---|---|
| `"decouvert"` | `"discovered"` |
| `"charge"` | `"loaded"` |
| `"actif"` | `"active"` |
| `"desactive"` | `"disabled"` |
| `"en_faute"` | `"faulted"` |
| `"incompatible"` | `"incompatible"` |


### The capability values in a manifest

| 2.0 | 3.0 |
|---|---|
| `"analyseur"` | `"analyser"` |
| `"descripteur"` | `"descriptor"` |
| `"sonificateur"` | `"sonifier"` |
| `"exportateur"` | `"exporter"` |
| `"source"` | "source" — unchanged |

---

## What 3.0 added

Renaming was the occasion, not the whole of it. Three members are new, and
they exist so that the version contract can be read from either side rather
than guessed:

| New in 3.0 | Who asks | What it answers |
|---|---|---|
| `context.api_version` | your module | the API version this host offers |
| `context.api_required` | your module | the minimum your own manifest declared |
| `context.api_at_least(v)` | your module | is the host at `v` or later, same major? |
| `manifest.api_required` | the host | your minimum, parsed to `(major, minor)` |
| `manifest.api_satisfied_by` | the host | "API 3.0 or any later 3.x", for Diagnostics |
| `registry.api_requirements()` | the host | the minimum of every module at once |
| `parse_version(v)` | both | `"3.1.4"` → `(3, 1)`; unreadable → `(-1, -1)` |

`Manifest.api` has always been a minimum — that is what `compatible()`
computed — but nothing said so, and nothing handed it back parsed. Now both
sides read the same field through the same parser, and the refusal names both
versions:

```
needs at least API 2.0, but this software offers 3.0 — it wants API 2.0 or any later 2.x
```

**What to do with it:** declare the lowest version that actually suffices, and
use `api_at_least()` for anything newer you would merely like. A module
declaring `api="3.2"` because that is what its author had installed is
refused on every 3.0 and 3.1 host, for nothing.

---

## What did *not* change

* the **event wire names** — `measurement.started`, `signal.event` and the
  nine others. They were renamed in 2.0, and renaming them twice would have
  been its own kind of cruelty;
* **subscribing to an unknown event is still not an error.** The callback is
  simply never called;
* the **session files on disk** — `mesures.csv`, `evenements.csv`,
  `seance.json` and the rest. An exporter reads the same names it always did;
* the **settings file**: your module's settings are still stored under its
  `name`, and the values you had are the values you get back;
* the **guarantees**. A module that raises still never brings the software
  down, load order is still deterministic, and nothing is still called on the
  acquisition thread.

---

## If you maintain a module you cannot rename today

Publish the 2.0 version as it stands and pin it: say in your `README` that it
needs PhytoScope 1.5.1 or earlier. A module that says which version it needs
is a module somebody can still use; one that fails silently on a newer host is
not.

---

**Back:** [the SDK README](../README.md)
