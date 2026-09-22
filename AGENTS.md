# AGENTS.md — how to work in this repository (Claude Code, ChatGPT, Gemini, other)

This repository is worked on by agents and by humans. This file is **the entry
point**: it says what to read and in what order, what not to do, and how to
leave a trace of what you did. It is deliberately short; everything else lives
elsewhere and is referenced from here.

## 1. Read these, in this order

| Order | File | What it holds |
|---|---|---|
| 1 | `constraints.md` | **The requirements**, as numbered constraints `C-1`…`C-64`. Authoritative. |
| 2 | `.ai/etat.md` | **Where the work stands**: what is done, what is left, what is in flight. |
| 3 | `.ai/journal.md` | **What was done, when, and why** — the full log of interventions. |
| 4 | `.ai/decisions.md` | The **design decisions** and their reasons (short ADR format). |
| 5 | `packaging/README.md` | **The package factory**: targets, formats, signing, what is verified and what is not. |
| 6 | `.ai/portabilite.md` | The Windows / macOS / Linux record: what was fixed, what still holds. |
| 7 | `README.md` | The project from the outside: contents, how to rebuild the PDFs. |
| 8 | `src/phytoscope/README.txt` | The software from the user's point of view. |

## 2. Working rules

1. **Technical US English everywhere**: code, comments, docstrings, interface,
   documents, file names, directory names. US spelling (`behavior`,
   `initialize`, `analyze`), US typography (`"quotes"`, no space before
   `: ; ! ?`), ISO dates (`2026-09-22`).

   This rule replaced a French-only rule on 2026-09-22, at the owner's
   request, because a public repository whose code and documentation are in
   French can only be read by a fraction of its possible contributors. It
   covers **the agent memory under `.ai/`** as well — journal, decisions,
   state, portability record — even though the owner writes to us in French.

   What stays French: proper nouns (`Bretagne Namasté`) and the titles of
   French works cited in the bibliographies. Nothing else.

   Past entries in `.ai/journal.md` and `CHANGELOG.md` are translated like
   the rest. Where such an entry names a file that has since been renamed, it
   is written with the name the file carries **today**, because that is the
   name a reader can act on; the entry still says what happened, and when.

2. **Explain the why.** A comment that paraphrases the code should be deleted;
   a comment that says why the code is the way it is should be kept.
3. **Verify, do not assume.** Every number you write down — pages, tests,
   coverage, throughput — is measured by a command first.
4. **Never edit a generated file** (see `C-45`): edit the source and re-run the
   generator.
5. **Test before you conclude**: `cd src/phytoscope && make test`
   (350 tests, no hardware and no network required).
6. **Record it.** After any substantial change, add a dated entry to
   `.ai/journal.md` and bring `.ai/etat.md` up to date. That is what lets the
   next agent — or the same one, three weeks later — pick the work back up.

## 3. What we do not do here

- ❌ **Write to the user's settings** (`~/.config/phytoscope/reglages.json`)
  during a test. Point `XDG_CONFIG_HOME` at a temporary directory.
  *(This rule comes from a real incident: see the journal entry for
  2026-09-18.)*
- ❌ Run the software with `--lang`, `--simulation`, or `--theme` against the
  user's real configuration.
- ❌ Add automatic locale detection (`C-31`).
- ❌ Add a mandatory dependency (`C-40`), or SciPy under any pretext.
- ❌ Use the vocabulary of speech without its warning (`C-5`).
- ❌ `sudo`: everything installs under the home directory (`C-55`). That holds
  for the packaging tools too — `make deps` unpacks them into `~/.local/opt`.
- ❌ **Copy the private signing key** anywhere other than
  `~/.local/share/phytoscope-signature/` and `certificat/` (`C-2R`).
- ❌ Imply that a self-signed certificate silences SmartScreen or Gatekeeper
  (`C-2Q`).

## 4. Useful commands

```bash
# Software
cd src/phytoscope
make test                      # 350 tests
make demo                      # a guided look, no hardware needed
.venv/bin/python tools/i18n.py --couverture     # translation coverage
.venv/bin/python tools/sbom.py --json           # software bill of materials

# Publications (from the repository root) — 10 PDFs, 1,378 pages
python3 pdf-src/assets/svg/gen.py         && python3 pdf-src/build.py         # main book,      478 pp.
python3 pdf-src/assets/svg/gen_tt.py      && python3 pdf-src/build_arbre.py   # the series,     573 pp.
python3 pdf-src/assets/svg/gen_sch.py     && python3 pdf-src/build_annexe.py  # the appendix,    65 pp.
python3 pdf-src/assets/svg/gen_carte.py   && python3 pdf-src/build_carte.py   # the special,    235 pp.
python3 pdf-src/assets/svg/gen_sdk.py     && python3 pdf-src/build_sdk.py     # the SDK guide,   27 pp.
python3 tools/verifier_svg.py                    # are the 104 figures well-formed XML?
git diff --name-only | python3 tools/pdf_impactes.py -   # which PDFs need rebuilding?

# Translation of the repository — see .ai/rename-plan.json
python3 tools/verify_translation.py --remaining   # how much French is left, per area
python3 tools/verify_translation.py --compare .ai/translation-baseline.json \
        --renames .ai/translation-renames.json    # did any code move? (it must not)
python3 tools/apply_renames.py --list             # the seven rename stages

# Installer packages (from Debian, Ubuntu, or Mint)
cd packaging
make outils        # what is missing in order to package
make deps          # NSIS, msitools, osslsigncode — without sudo
make certificat    # once
make tout          # .deb .rpm .run .exe .msi .pkg .zip .tar.gz, all signed
make verifier      # reopen and check everything that was produced

# Firmware
cd src/firmware
./_make_.sh --deps             # installs the SDK and the ARM toolchain in $HOME, no sudo
./_make_.sh                    # -> build/phytosense.uf2 — compiles only
./build.sh                     # compiles AND files the deliverable under build/paquets/
```

## 5. Où vit quoi

Le dépôt a été rangé le 2026-09-18 : le **code** vit sous `src/`, les
**sources d'édition** sous `pdf-src/`, et `sources/` ne contient plus que de
la **matière de référence** — ce que nous n'avons pas écrit.

```
constraints.md              le cahier des charges (fait autorité)
CHANGELOG.md                l'historique du projet entier
README.md                   le projet vu de l'extérieur
INSTALL.md                  ce que fait chaque installateur, par système
PACKAGING.md                comment (re)fabriquer un paquet, ou tous
CONTRIBUTING.md             comment contribuer ; SECURITY.md : comment signaler
LICENSE, LICENSES/          MIT (logiciel) et CERN-OHL-P v2 (matériel) — C-53
.ai/                        la mémoire des agents (journal, décisions, état)
.github/                    intégration continue, gabarits de tickets

src/                        TOUT LE CODE
  phytoscope/               le logiciel PhytoScope (Python + Qt) — 67 modules
    Makefile                « make test », « make demo », « make doctor »
    phytoscope/VERSION      LA version — seule source de vérité
    phytoscope/AUTEURS      éditeur, auteur, site — seule source de vérité
    phytoscope/core/        acquisition, DSP, session, grandeurs
    phytoscope/music/       correspondance signal → musique, MIDI, voix
    phytoscope/ui/          l'interface Qt
    phytoscope/api/         le contrat des modules tiers
    phytoscope/langues/     les 10 catalogues de traduction (JSON)
    phytoscope/lexiques/    les 11 dictionnaires du mode vocal (JSON)
    tests/                  12 fichiers de tests, sans matériel ni réseau
  firmware/                 le micrologiciel RP2350 (C, Pico SDK) — 7 fichiers
    _make_.sh               compile — « --deps » installe SDK et chaîne ARM
    build.sh                compile ET range le livrable dans build/paquets/
  sdk/                      la trousse pour écrire un module tiers
    docs/                   les sept parties de la documentation
    bonjour-monde/          le module d'exemple, avec son test
    outils/nouveau_module.py

pdf-src/                    LES SOURCES DES DIX PUBLICATIONS
  build.py                  l'ouvrage principal                      478 p.
  build_arbre.py            la série « L'Arbre qui Parle » (v1 v2 v3)
  build_annexe.py           l'annexe technique de la série            65 p.
  build_carte.py            le hors-série et ses 3 fascicules
  build_sdk.py              le guide du SDK                           27 p.
  book.css carte.css        les chartes graphiques (paged media)
  arbre.css fonts.css
  assets/svg/               104 illustrations + leurs 5 générateurs
  assets/img/               234 photographies et planches
  assets/fonts/             Cinzel, Cormorant Garamond (SIL OFL 1.1)
  commun/                   fragments partagés — tableaux de nomenclature
                            UN DOSSIER PAR PUBLICATION :
  la-musique-des-plantes/           478 p.  l'ouvrage principal
  arbre-parlant-dublin/             212 p.  l'enquête
  biocommunication-vegetale-et-ia/  163 p.  le traité
  atelier-creer-arbre-parlant/      198 p.  le manuel d'atelier
  arbre-parlant-annexe/              65 p.  planches, BOM, programmes
  la-carte-phytosense/              198 p.  le hors-série technique
  phytosense-schemas/                12 p.  fascicule détachable
  phytosense-bom-accessoires/        18 p.  fascicule détachable
  phytosense-pcb/                     7 p.  fascicule détachable
  ecrire-un-module-phytoscope/       27 p.  le guide du SDK

hardware/                   nomenclature et accessoires (CSV) — CERN-OHL-P v2
packaging/                  la fabrique des paquets d'installation
  Makefile                  enchaîne les cibles — « make tout », « make macos »
  common.py                 ce qui ne dépend d'aucun système
  construire_<os>.py        un générateur par système, autonome
  signature.py              certificat X.509, Authenticode et CMS
  certificate.py             crée, recrée et dépose le certificat
  languages.py                les libellés des installateurs, 11 langues
  macos_pkg.py              le format .pkg, écrit de bout en bout
  gabarits/                 control, .spec, .nsi, .wxs, Info.plist, lanceurs
tools/                      les outils du dépôt
  entetes.py                pose et vérifie les en-têtes d'attribution
  verifier_svg.py           les illustrations sont-elles du XML bien formé ?
  pdf_impactes.py           quelles publications refaire, vu ce qui a changé
  sbom.py                   la nomenclature du PROJET — logiciel ET micrologiciel
  gen_bom.py gen_index.py   fragments générés — ne jamais les éditer (C-45)
  gen_glossaire.py gen_credits.py gen_code_annex.py
  fetch-software.py         récupère les dépôts tiers (817 Mo, hors dépôt)
certificat/                 le certificat PUBLIC ; la clé privée est écartée

sources/                    MATIÈRE DE RÉFÉRENCE — rien que nous ayons écrit,
                            sauf sources/reverse/. Exclu de tools/entetes.py.
  brevets/                  13 brevets (PDF hors dépôt)
  datasheets/               9 notices de composants (hors dépôt)
  manuels-constructeurs/    11 manuels (hors dépôt)
  documents/                articles ; domaine public (transcriptions)
  ebooks/                    5 ouvrages sous droits (hors dépôt)
  schemas/                  3 projets tiers, AVEC leur licence — dont
                            biotron-firmware, qui est en GPL-3.0
  code/ software/           69 dépôts tiers en archives (hors dépôt)
  reverse/damanhur-bridge/  notre reconstitution du brevet US 6 487 817 (MIT)
  01-…-04-….md              notes de recherche sourcées
  INDEX.md                  l'index du corpus

build/                      les PDF produits — jamais édités à la main
build/paquets/              les paquets produits — jamais édités à la main
.ecarte/                    doublons et environnements mis à l'écart, hors
                            dépôt ; supprimable sans conséquence
```

## 6. Ce que le dépôt ne contient pas, et pourquoi

Le dépôt est **public**. Trois familles de fichiers restent sur le disque mais
sont écartées par `.gitignore` :

| Quoi | Pourquoi |
|---|---|
| `certificat/phytoscope.key` | La clé privée de signature (`C-2R`). Sa copie de référence vit dans `~/.local/share/phytoscope-signature/`. |
| `sources/ebooks/`, `sources/brevets/*.pdf`, `sources/datasheets/*.pdf`, `sources/manuels-constructeurs/*.pdf`, `sources/documents/articles-scientifiques/*.pdf` | Nous n'avons pas le droit de les rediffuser. Leurs références bibliographiques, elles, sont dans `sources/INDEX.md`. |
| `sources/documents/domaine-public/*.pdf` | Non pour les droits — Bose et Darwin sont libres — mais pour le poids : 260 Mo de numérisations. Les transcriptions restent versionnées ; voir le `LISEZ-MOI.md` du dossier. |
| `sources/code/*.zip`, `sources/software/**/*.zip` | 817 Mo de dépôts tiers. `python3 tools/fetch-software.py` les récupère à la source ; `sources/software/MANIFESTE.md` garde la provenance et les licences. |
| `build/`, `.venv/`, `__pycache__/`, `.ecarte/` | Se reconstruisent. |
