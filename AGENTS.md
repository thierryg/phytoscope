# AGENTS.md — mode d'emploi pour un agent (Claude Code, ChatGPT, Gemini, autre)

Ce dépôt est travaillé par des agents et par des humains. Ce fichier est **le
point d'entrée** : il dit dans quel ordre lire, ce qu'il ne faut pas faire, et
comment laisser une trace de ce qu'on a fait. Il est court exprès ; tout le reste
est ailleurs et référencé ici.

## 1. Lire, dans cet ordre

| Ordre | Fichier | Ce qu'on y trouve |
|---|---|---|
| 1 | `constraints.md` | **Le cahier des charges**, contraintes numérotées `C-1`…`C-64`. Fait autorité. |
| 2 | `.ai/etat.md` | **Où en est le travail** : ce qui est fait, ce qui reste, ce qui est en cours. |
| 3 | `.ai/journal.md` | **Ce qui a été fait, quand, et pourquoi** — l'historique complet des interventions. |
| 4 | `.ai/decisions.md` | Les **décisions de conception** et leurs raisons (format ADR court). |
| 5 | `packaging/README.md` | **La fabrique de paquets** : cibles, formats, signature, ce qui est vérifié et ce qui ne l'est pas. |
| 6 | `.ai/portabilite.md` | Le relevé Windows / macOS / Linux : ce qui est corrigé, ce qui reste vrai. |
| 7 | `README.md` | Le projet vu de l'extérieur : contenu, reconstruction des PDF. |
| 8 | `src/phytoscope/README.txt` | Le logiciel vu de l'utilisateur. |

## 2. Règles de travail

1. **Le français partout** : code, commentaires, docstrings, interface, documents.
   Typographie française (« guillemets », espaces avant `: ; ! ?`).
2. **Expliquer le pourquoi.** Un commentaire qui paraphrase le code est à
   supprimer ; un commentaire qui dit pourquoi le code est ainsi est à garder.
3. **Vérifier, ne pas supposer.** Toute affirmation chiffrée (pages, tests,
   couverture, débit) se mesure par une commande avant d'être écrite.
4. **Ne jamais modifier un fichier généré** (voir `C-45`) : modifier la source
   et relancer le générateur.
5. **Tester avant de conclure** : `cd src/phytoscope && make test`
   (260 tests, sans matériel ni réseau).
6. **Consigner** : après toute intervention notable, ajouter une entrée datée
   dans `.ai/journal.md` et mettre `.ai/etat.md` à jour. C'est ce qui permet à
   l'agent suivant — ou au même, trois semaines plus tard — de reprendre.

## 3. Ce qu'on ne fait pas ici

- ❌ **Écrire dans les réglages de l'utilisateur** (`~/.config/phytoscope/reglages.json`)
  pendant un essai. Utiliser `XDG_CONFIG_HOME` vers un dossier temporaire.
  *(Cette règle vient d'un incident réel : voir le journal du 2026-09-18.)*
- ❌ Lancer le logiciel avec `--lang`, `--simulation`, `--theme` sur la
  configuration réelle de l'utilisateur.
- ❌ Ajouter une détection automatique de la locale (`C-31`).
- ❌ Ajouter une dépendance obligatoire (`C-40`), ou SciPy sous quelque prétexte.
- ❌ Employer le vocabulaire de la parole sans son avertissement (`C-5`).
- ❌ `sudo` : tout s'installe dans le dossier personnel (`C-55`). Vaut aussi
  pour les outils d'empaquetage — `make deps` les déplie dans `~/.local/opt`.
- ❌ **Copier la clé privée de signature** ailleurs que dans
  `~/.local/share/phytoscope-signature/` et `certificat/` (`C-2R`).
- ❌ Laisser croire qu'un certificat auto-signé fait taire SmartScreen ou
  Gatekeeper (`C-2Q`).

## 4. Commandes utiles

```bash
# Logiciel
cd src/phytoscope
make test                      # 260 tests
make demo                      # découverte, sans matériel
.venv/bin/python tools/i18n.py --couverture     # état des traductions
.venv/bin/python tools/sbom.py --json           # nomenclature logicielle

# Publications (depuis la racine) — 10 PDF, 1 378 pages
python3 pdf-src/assets/svg/gen.py         && python3 pdf-src/build.py         # ouvrage, 478 p.
python3 pdf-src/assets/svg/gen_tt.py      && python3 pdf-src/build_arbre.py   # la série, 573 p.
python3 pdf-src/assets/svg/gen_sch.py     && python3 pdf-src/build_annexe.py  # annexe, 65 p.
python3 pdf-src/assets/svg/gen_carte.py   && python3 pdf-src/build_carte.py   # hors-série, 235 p.
python3 pdf-src/assets/svg/gen_sdk.py     && python3 pdf-src/build_sdk.py     # guide SDK, 27 p.
python3 tools/verifier_svg.py                    # les 104 illustrations sont-elles bien formées ?
git diff --name-only | python3 tools/pdf_impactes.py -   # que faut-il refaire ?

# Paquets d'installation (depuis Debian, Ubuntu ou Mint)
cd packaging
make outils        # ce qui manque pour empaqueter
make deps          # NSIS, msitools, osslsigncode — sans sudo
make certificat    # une seule fois
make tout          # .deb .rpm .run .exe .msi .pkg .zip .tar.gz, signés
make verifier      # rouvre et contrôle tout ce qui a été produit

# Micrologiciel
cd src/firmware
./_make_.sh --deps             # installe SDK + chaîne ARM dans $HOME, sans sudo
./_make_.sh                    # → build/phytosense.uf2 — compile seulement
./build.sh                     # compile ET range le livrable dans build/paquets/
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
  commun.py                 ce qui ne dépend d'aucun système
  construire_<os>.py        un générateur par système, autonome
  signature.py              certificat X.509, Authenticode et CMS
  certificat.py             crée, recrée et dépose le certificat
  langues.py                les libellés des installateurs, 11 langues
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
