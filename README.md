<!-- PhytoScope — README principal -->

# PhytoScope

**Écouter les plantes sans raconter d'histoires.**

PhytoScope mesure des grandeurs électriques et physiologiques sur une plante
vivante, les transpose en musique, et **dit à chaque étape ce qui est mesuré
et ce qui est interprété**. C'est un projet complet : un logiciel, une carte
d'acquisition, un micrologiciel, une trousse de modules, une fabrique de
paquets signés — et dix publications qui documentent le tout, jusqu'aux
limites de ce qu'on peut honnêtement affirmer.

> **Une plante n'exprime rien.** Un signal est transposé. Le projet tient
> cette nuance pour son cœur, pas pour une précaution de forme : la
> contrainte `C-5` du cahier des charges interdit d'employer le vocabulaire
> de la parole sans son avertissement, et `tools/entetes.py` comme la revue
> de code y veillent.

| | |
|---|---|
| **Version** | 1.5.1 — 18 septembre 2026 |
| **Éditeur** | Bretagne Namasté — [bretagne-namaste.com](https://bretagne-namaste.com) |
| **Licences** | **MIT** (logiciel, micrologiciel, outils) · **CERN-OHL-P v2** (matériel) — voir [`LICENSES/README.md`](LICENSES/README.md) |
| **Langue** | Tout le dépôt est en français, code et commentaires compris |
| **Systèmes** | Debian · Ubuntu · Mint · Fedora · RHEL · Windows 10/11 · macOS |
| **Python** | ≥ 3.9 (testé sur 3.10 et 3.12) |

---

## Table des matières

1. [Ce que fait le projet](#1-ce-que-fait-le-projet)
2. [Arborescence du dépôt](#2-arborescence-du-dépôt)
3. [Le logiciel](#3-le-logiciel--srcphytoscope)
4. [Le micrologiciel](#4-le-micrologiciel--srcfirmware)
5. [La trousse de modules](#5-la-trousse-de-modules--srcsdk)
6. [Le matériel](#6-le-matériel--hardware)
7. [Les dix publications](#7-les-dix-publications--pdf-src)
8. [La fabrique de paquets](#8-la-fabrique-de-paquets--packaging)
9. [Intégration continue et DevSecOps](#9-intégration-continue-et-devsecops)
10. [Sécurité et secrets](#10-sécurité-et-secrets)
11. [Ce que le dépôt ne contient pas](#11-ce-que-le-dépôt-ne-contient-pas-et-pourquoi)
12. [Contribuer](#12-contribuer)
13. [Chiffres du projet](#13-chiffres-du-projet)

---

## 1. Ce que fait le projet

### La chaîne, de la plante au son

```
   PLANTE                CARTE PhytoSense One            ORDINATEUR
   ┌──────┐   électrodes  ┌────────────────────┐   USB   ┌──────────────────┐
   │      │──────────────▶│ étage électro-     │────────▶│ acquisition      │
   │ Rp   │   Ag/AgCl     │ métrique (1 GΩ)    │  CDC    │ descripteurs     │
   │      │               │ pont à détection   │         │ correspondance   │
   └──────┘               │ synchrone          │         │ synthèse / MIDI  │
      ▲                   │ ADC 24 bits        │         │ voix (11 lexiques)│
      │                   │ RP2350, 2 cœurs    │         └──────────────────┘
   ambiance :             └────────────────────┘                  │
   lumière, CO₂,                    │                             ▼
   température,              capteurs d'ambiance          son · MIDI · CSV
   humidité du sol           (I²C / 1-Wire)               séance rejouable
```

La carte **n'interprète rien** : aucune détection d'événement, aucune règle
musicale, aucun filtrage autre que celui du convertisseur. Tout le
raisonnement est calculé sur l'ordinateur, **où il est modifiable,
vérifiable et remplaçable**. Seule exception : la sortie MIDI directe, qui
embarque une version réduite du moteur de correspondance pour attaquer un
synthétiseur matériel sans passer par la chaîne audio.

### Les trois lectures d'un même signal

Le projet refuse de choisir entre la mesure et le sensible, et refuse de les
confondre. Chaque phénomène est présenté sur trois registres, toujours
distingués :

| Registre | Ce qu'on affirme | Où c'est documenté |
|---|---|---|
| **Mesuré** | Ce qu'un instrument donne, avec son incertitude | *La Carte PhytoSense*, `src/phytoscope/phytoscope/core/grandeurs.py` |
| **Plausible** | Ce que la littérature établit, avec sa référence | *La Musique des Plantes*, `sources/INDEX.md` |
| **Non mesurable** | Ce qui relève du vécu et se dit comme tel | *L'Arbre qui Parle*, échelle épistémique |

---

## 2. Arborescence du dépôt

Le dépôt a été rangé le 2026-09-18 selon une règle simple : **le code sous
`src/`, les sources d'édition sous `pdf-src/`, et `sources/` ne contient plus
que de la matière de référence — ce que nous n'avons pas écrit.**

```
phytoscope/
├── src/                            TOUT LE CODE
│   ├── phytoscope/                 le logiciel (Python 3 + Qt 6) — 67 modules
│   ├── firmware/                   le micrologiciel RP2350 (C, Pico SDK)
│   └── sdk/                        la trousse pour écrire un module tiers
│
├── pdf-src/                        LES SOURCES DES DIX PUBLICATIONS
│   ├── build.py                    ┐
│   ├── build_arbre.py              │ les cinq fabriques
│   ├── build_annexe.py             │
│   ├── build_carte.py              │
│   ├── build_sdk.py                ┘
│   ├── book.css carte.css          les chartes graphiques (paged media)
│   ├── arbre.css fonts.css
│   ├── assets/svg/                 104 illustrations + leurs 5 générateurs
│   ├── assets/img/                 234 photographies et planches
│   ├── assets/fonts/               Cinzel, Cormorant Garamond (SIL OFL 1.1)
│   ├── commun/                     fragments partagés entre publications
│   │                               UN DOSSIER PAR PUBLICATION :
│   ├── la-musique-des-plantes/     478 p. — l'ouvrage principal
│   ├── arbre-parlant-dublin/       212 p. — l'enquête
│   ├── biocommunication-vegetale-et-ia/  163 p. — le traité
│   ├── atelier-creer-arbre-parlant/      198 p. — le manuel d'atelier
│   ├── arbre-parlant-annexe/        65 p. — planches, BOM, programmes
│   ├── la-carte-phytosense/        198 p. — le hors-série technique
│   ├── phytosense-schemas/          12 p. — fascicule détachable
│   ├── phytosense-bom-accessoires/  18 p. — fascicule détachable
│   ├── phytosense-pcb/               7 p. — fascicule détachable
│   └── ecrire-un-module-phytoscope/ 27 p. — le guide du SDK
│
├── hardware/                       nomenclature et accessoires (CSV)
│                                   → CERN-OHL-P v2, pas MIT
├── packaging/                      la fabrique des paquets signés
├── tools/                          les outils du dépôt
├── certificat/                     le certificat PUBLIC (la clé privée est écartée)
│
├── sources/                        MATIÈRE DE RÉFÉRENCE
│   ├── brevets/ datasheets/        fac-similés — hors dépôt (droits)
│   ├── manuels-constructeurs/
│   ├── documents/                  articles ; domaine public (transcriptions)
│   ├── ebooks/                     ouvrages sous droits — hors dépôt
│   ├── schemas/                    3 projets tiers, AVEC leur licence
│   ├── code/ software/             69 dépôts tiers — hors dépôt (817 Mo)
│   ├── reverse/damanhur-bridge/    notre reconstitution d'un brevet expiré
│   ├── 01-…04-….md                 notes de recherche sourcées
│   └── INDEX.md                    l'index du corpus
│
├── build/                          les PDF et les paquets produits
│                                   — JAMAIS édités à la main (C-45)
├── .ai/                            la mémoire du projet : journal, décisions,
│                                   état, relevé de portabilité
├── .github/workflows/              6 workflows d'intégration continue
├── constraints.md                  LE CAHIER DES CHARGES — fait autorité
├── AGENTS.md                       le point d'entrée pour un agent ou un humain
├── CONTRIBUTING.md  SECURITY.md  CODE_OF_CONDUCT.md
└── LICENSE  LICENSES/              MIT et CERN-OHL-P v2
```

### Pourquoi `sources/` n'est pas `src/`

Ce sont deux choses opposées, et les confondre a des conséquences réelles :

- `src/` est **notre code**. `tools/entetes.py` y pose notre en-tête
  d'attribution et son `SPDX-License-Identifier`.
- `sources/` est **ce que d'autres ont écrit**, réuni pour documenter
  l'ouvrage. Il est **exclu** de `tools/entetes.py`. La raison est concrète :
  l'outil y avait apposé « © Bretagne Namasté » et « MIT » sur 32 fichiers,
  dont le micrologiciel **Biotron, qui est en GPL-3.0**. C'était une fausse
  déclaration de licence et de paternité ; corrigé le 2026-09-18, et le
  workflow `securite.yml` refuse désormais qu'elle revienne.

---

## 3. Le logiciel — `src/phytoscope/`

67 modules Python, 22 783 lignes, 260 tests qui passent **sans matériel ni
réseau**.

```bash
cd src/phytoscope
make install-dev      # environnement virtuel + outils de développement
make doctor           # dit ce qui est installé et ce qui manque
make demo             # lance le logiciel avec une plante simulée
make test             # 260 tests, ~7 s
make lint             # ruff
```

### Organisation

| Dossier | Ce qu'on y trouve |
|---|---|
| `phytoscope/core/` | acquisition, horodatage, DSP, session, descripteurs, grandeurs physiques, empreinte de montage, pré-vol |
| `phytoscope/music/` | correspondance signal → musique, gammes, instruments, synthèse, sortie MIDI, mode vocal |
| `phytoscope/ui/` | l'interface Qt 6 — onglets, tracés temps réel, journal, réglages, diagnostic |
| `phytoscope/api/` | le contrat des modules tiers : contexte, événements, registre |
| `phytoscope/langues/` | 10 catalogues de traduction (ar, en, es, id, it, ja, ko, pt, ru, zh) |
| `phytoscope/lexiques/` | 11 dictionnaires du mode vocal (les 10 ci-dessus + fr) |
| `phytoscope/modules/` | 4 modules livrés : descripteurs avancés, empreinte de montage, export CSV, grandeurs scientifiques |

### Dépendances

**Cinq dépendances d'exécution, et pas une de plus** — la contrainte `C-40`
interdit d'en ajouter une à la légère, et proscrit SciPy sans exception :

```
numpy>=1.24        tout le traitement du signal
PySide6>=6.5       interface graphique Qt 6 (LGPL)
pyqtgraph>=0.13    tracés temps réel accélérés (sinon tracé maison, plus lent)
sounddevice>=0.4.6 entrée et sortie audio (PortAudio)
pyserial>=3.5      carte PhytoSense et montages série (Arduino, NE555)
```

Optionnelles, et le logiciel fonctionne sans : `python-rtmidi` (ports MIDI),
`pyttsx3` (synthèse vocale système).

### Deux fichiers font autorité

`src/phytoscope/phytoscope/VERSION` et `.../AUTEURS` sont les **seules**
sources de vérité pour la version et l'attribution. Le logiciel les lit pour
sa fenêtre « À propos », la fabrique de paquets pour estampiller le `.deb`,
le `.rpm`, le `.msi` et le `.pkg`, `tools/entetes.py` pour les en-têtes, et
`packaging/signature.py` pour le sujet du certificat X.509. Ils vivent **dans
le paquet Python** et non à la racine, pour une raison simple : un logiciel
installé n'emporte pas le dépôt.

---

## 4. Le micrologiciel — `src/firmware/`

7 fichiers C, 1 460 lignes, pour un **RP2350** (Pico SDK ≥ 2.0.0 ; les
versions 1.x ne connaissent que le RP2040 et échouent à la configuration).

```bash
cd src/firmware
./build.sh --deps     # installe le SDK et la chaîne ARM dans $HOME, sans sudo
./build.sh            # → phytosense.uf2
```

### Répartition des deux cœurs

| Cœur | Tâche | Contrainte |
|---|---|---|
| 0 | service du convertisseur, horodatage, tampon circulaire | boucle bornée, aucune allocation, aucune attente |
| 1 | USB, dialogue de contrôle, capteurs d'ambiance, MIDI, afficheur | peut bloquer sans conséquence pour la mesure |

Les deux cœurs ne partagent que le tampon circulaire, par des indices
atomiques. C'est ce qui fait que le flux ne présente **aucun trou** même
lorsque l'ordinateur interroge la carte en pleine acquisition.

### Le dialogue de contrôle

Délibérément archaïque : commandes en texte terminées par CR-LF, réponses sur
une ligne commençant par `+` (succès) ou `-` (erreur) suivi d'un objet JSON.
On peut donc **interroger et dépanner la carte avec n'importe quel
terminal**, sans installer quoi que ce soit.

---

## 5. La trousse de modules — `src/sdk/`

Un module tiers ajoute un descripteur, un mode de sonification ou un
exportateur, **sans toucher au logiciel**.

```bash
python3 src/sdk/outils/nouveau_module.py mon-module --capacite descripteur
python3 src/sdk/outils/nouveau_module.py mon-module --installer
```

- `src/sdk/docs/` — la documentation en sept parties, de `01-demarrage.md`
  à `07-pieges.md` ;
- `src/sdk/bonjour-monde/` — le module d'exemple, **avec son test** ;
- la même matière, mise en page pour l'impression :
  `build/Ecrire-un-module-PhytoScope.pdf` (27 p.).

---

## 6. Le matériel — `hardware/`

| Fichier | Contenu |
|---|---|
| `bom.csv` | **68 références**, 244,35 € — nomenclature chiffrée de la carte PhytoSense One |
| `accessoires.csv` | 103,90 € d'accessoires, plus 304,30 € recommandés |

Ces deux fichiers sont la **source** des tableaux imprimés :
`tools/gen_bom.py` en produit les fragments HTML, et rien n'est recopié à la
main.

> `hardware/` est sous **CERN-OHL-P v2**, pas MIT (`C-53`). Écrire « MIT » sur
> un plan de circuit serait faux, et un jour quelqu'un s'en servirait en le
> croyant. `tools/entetes.py` connaît la règle et pose la bonne licence selon
> le chemin.

---

## 7. Les dix publications — `pdf-src/`

**1 378 pages**, produites par WeasyPrint depuis des fragments HTML et quatre
chartes CSS en *paged media* : sommaire cliquable, signets, en-têtes courants,
pagination, index paginé, métadonnées.

| Publication | Pages | Fabrique | Sources |
|---|---:|---|---|
| **La Musique des Plantes** | 478 | `build.py` | `la-musique-des-plantes/` |
| **L'Arbre qui Parle — Dublin** | 212 | `build_arbre.py v1` | `arbre-parlant-dublin/` |
| **Biocommunication végétale et IA** | 163 | `build_arbre.py v2` | `biocommunication-vegetale-et-ia/` |
| **Créer un arbre parlant** | 198 | `build_arbre.py v3` | `atelier-creer-arbre-parlant/` |
| **Annexe — planches, BOM, programmes** | 65 | `build_annexe.py` | `arbre-parlant-annexe/` |
| **La Carte PhytoSense** | 198 | `build_carte.py` | `la-carte-phytosense/` |
| **PhytoSense — schémas** | 12 | `build_carte.py` | `phytosense-schemas/` |
| **PhytoSense — nomenclature** | 18 | `build_carte.py` | `phytosense-bom-accessoires/` |
| **PhytoSense — circuit imprimé** | 7 | `build_carte.py` | `phytosense-pcb/` |
| **Écrire un module PhytoScope** | 27 | `build_sdk.py` | `ecrire-un-module-phytoscope/` |

### Reconstruire

```bash
# Les illustrations d'abord : elles sont générées, jamais dessinées (C-45)
python3 pdf-src/assets/svg/gen.py          # l'ouvrage et la série
python3 pdf-src/assets/svg/gen_carte.py    # le hors-série
python3 pdf-src/assets/svg/gen_sch.py      # les planches de schémas
python3 pdf-src/assets/svg/gen_sdk.py      # le guide du SDK
python3 pdf-src/assets/svg/gen_tt.py       # la série « L'Arbre qui Parle »
python3 tools/verifier_svg.py              # sont-elles du XML bien formé ?

# Les fragments produits à partir de sources de vérité
python3 tools/gen_bom.py                   # depuis hardware/*.csv
python3 tools/gen_code_annex.py            # depuis les fichiers de code réels

# Les publications
python3 pdf-src/build.py
python3 pdf-src/build_arbre.py             # ou « v1 », « v2 v3 »…
python3 pdf-src/build_annexe.py
python3 pdf-src/build_carte.py
python3 pdf-src/build_sdk.py
```

### Ne reconstruire que ce qui est touché

Refaire les dix publications prend une douzaine de minutes. Corriger une
coquille dans le hors-série n'a aucune raison de reconstruire l'ouvrage de
478 pages :

```bash
git diff --name-only | python3 tools/pdf_impactes.py -
# → les commandes à lancer, et rien d'autre
```

L'outil est **volontairement prudent** : un chemin qu'il ne sait pas
rattacher déclenche tout. Se tromper en refaisant trop coûte des minutes ;
se tromper en refaisant trop peu publie un PDF périmé, **et cela ne se voit
pas**. C'est lui que la CI utilise (`.github/workflows/publications.yml`).

### Le défaut qui a justifié `tools/verifier_svg.py`

Une illustration qui n'est pas du XML bien formé **ne casse pas la
fabrication** : WeasyPrint la laisse tomber, compose un cadre vide, et le PDF
sort avec le bon nombre de pages. Personne ne s'en aperçoit avant
l'impression. C'est arrivé — `timeline.svg` portait un `&` nu parce que son
générateur n'échappait pas le texte. Le générateur a été corrigé, et les 104
illustrations sont désormais contrôlées à chaque passage de la CI.

---

## 8. La fabrique de paquets — `packaging/`

**Un seul poste Debian, Ubuntu ou Mint produit les paquets de tous les
systèmes**, signés, avec leurs empreintes et leur documentation.

```bash
cd packaging
make outils        # ce qui manque pour empaqueter
make deps          # NSIS, msitools, osslsigncode — dans ~/.local/opt, sans sudo
make certificat    # une seule fois ; idempotent ensuite
make tout          # tous les paquets, signés
make verifier      # rouvre et contrôle tout ce qui a été produit
```

### Ce que `make tout` produit

| Système | Paquets | Taille |
|---|---|---|
| Debian / Ubuntu / Mint | `phytoscope_1.5.1_all.deb` | 368 ko |
| Toutes distributions | `PhytoScope-1.5.1-Linux.run` | 590 ko |
| Fedora / RHEL / Rocky | `phytoscope-1.5.1-1.noarch.rpm` | 604 ko |
| Windows 10/11 | `PhytoScope-1.5.1-Windows.exe` · `.msi` · `-portable.zip` | 178 / 275 / 262 Mo |
| macOS | `PhytoScope-1.5.1.pkg` · `-macOS.zip` | 624 / 700 ko |
| Source | `phytoscope-1.5.1.tar.gz` | 604 ko |

Les paquets Windows embarquent l'interpréteur et Qt, d'où leur taille ; les
autres s'appuient sur le Python du système.

Chaque paquet est accompagné de son empreinte `.sha256`, de sa signature
(`.p7s` en CMS détachée, Authenticode pour `.exe` et `.msi`), et de sept
documents : `AUTHENTICITE.txt`, `install.txt`, `manuel.txt`, `readme.txt`,
`licence.txt`, `changelog.txt`, `phytoscope-certificat.pem`.

### Deux avertissements que le projet assume

1. **Le certificat est auto-signé.** Il prouve l'intégrité et la continuité
   d'origine. Il **ne fait taire ni SmartScreen ni Gatekeeper**, et n'a jamais
   prétendu le faire (`C-2Q`). Un signalement qui reproche cela est déclaré
   hors portée dans [`SECURITY.md`](SECURITY.md).
2. **Aucun paquet n'est *installé* par `make verifier`** : la machine qui
   fabrique n'a ni Windows, ni macOS, ni Fedora. Ce qui est vérifié, c'est
   leur structure et leur cohérence interne. L'installation réelle se teste
   sur chaque système, et la CI y aide (`paquets.yml`, matrice
   Linux / Windows / macOS).

### Aucun `sudo`, jamais

Tout s'installe dans le dossier personnel (`C-55`) — y compris les outils
d'empaquetage, que `make deps` déplie dans `~/.local/opt`.

---

## 9. Intégration continue et DevSecOps

Six workflows, dans `.github/workflows/` :

| Workflow | Déclencheur | Ce qu'il fait |
|---|---|---|
| **`paquets.yml`** | `src/**`, `packaging/**` | analyse statique de tout l'exécutable (ruff, shellcheck, Makefile, yamllint), puis **une fabrication par système cible en parallèle**, puis la chaîne complète signée et vérifiée ; enfin les tests sur Linux, Windows et macOS × Python 3.10 et 3.12 |
| **`publications.yml`** | `pdf-src/**`, `hardware/**`, `tools/**` | refait **seulement les PDF touchés** (`tools/pdf_impactes.py`), contrôle que les illustrations sont du XML bien formé, et qu'aucune publication ne s'est effondrée |
| **`securite.yml`** | chaque poussée + hebdomadaire | gitleaks, garde-fou maison sur la clé privée, bandit (SARIF), pip-audit, trivy, revue des dépendances ajoutées, **cohérence des licences**, zizmor sur les workflows eux-mêmes |
| **`codeql.yml`** | chaque poussée + hebdomadaire | analyse sémantique Python **et C** — suit le chemin d'une donnée, là où bandit reconnaît des motifs |
| **`scorecard.yml`** | protection de branche + hebdomadaire | relevé OpenSSF Scorecard des pratiques du dépôt |
| **`diffusion.yml`** | étiquette `v*.*.*` | vérifie que l'étiquette **correspond à `VERSION`**, rejoue les tests, fabrique tous les paquets, produit le SBOM, **atteste la provenance** (Sigstore), et publie |

### Ce qui distingue cette CI d'une CI ordinaire

- **L'analyse précède la fabrication.** Un paquet bâti sur un script fautif
  est un paquet qu'il faudra republier.
- **La provenance est attestée.** Chaque paquet publié porte une signature
  Sigstore qui dit de quel dépôt, quel commit et quel workflow il sort :

  ```bash
  gh attestation verify phytoscope_1.5.1_all.deb --repo thierryg/phytoscope
  ```

  C'est complémentaire de la signature de l'éditeur, pas un remplacement :
  la CI signe la **provenance**, l'éditeur signe l'**origine**.
- **Une nomenclature logicielle (SBOM, CycloneDX)** est versionnée dans
  `src/phytoscope/sbom.cdx.json`, et la CI refuse qu'elle dérive des
  dépendances déclarées — un SBOM faux est pire qu'aucun SBOM.
- **Les workflows sont eux-mêmes analysés** (`zizmor`) : un workflow qui
  demande `contents: write` là où `read` suffit est une porte ouverte.
- **La cohérence des licences est un test.** La CI refuse que notre en-tête
  réapparaisse sur du code tiers, et vérifie que chaque projet recopié garde
  son fichier de licence.

### Garde-fous locaux

```bash
python3 -m pip install --user pre-commit && pre-commit install
pre-commit run --all-files
```

`.pre-commit-config.yaml` ajoute aux crochets usuels trois contrôles propres
au projet : **la clé privée refusée sur son seul nom** (même vide, même
renommée), les **en-têtes d'attribution à jour**, et les **illustrations bien
formées**.

---

## 10. Sécurité et secrets

La politique complète est dans [`SECURITY.md`](SECURITY.md) — **n'ouvrez pas
de ticket public pour une faille.**

Le secret qui compte ici est la **clé privée de signature des paquets** :

- sa copie de référence vit dans `~/.local/share/phytoscope-signature/` ;
- `certificat/phytoscope.key` est une copie de travail, **écartée par
  `.gitignore`** (`C-2R`) ;
- le certificat **public** (`certificat/phytoscope-certificat.pem`,
  `certificat/phytoscope.crt`) **est** versionné : c'est lui qui permet de
  vérifier une signature, il est fait pour être diffusé.

```bash
# Ce que git suit et qui ressemble à une clé — doit ne montrer que le public
git ls-files | grep -Ei '\.(key|pem|p12|pfx|jks|keystore)$'
```

> `.gitignore` protège de `git`, **pas d'une sauvegarde ni d'une archive du
> dossier**. Voir `certificat/LISEZ-MOI.md`.

---

## 11. Ce que le dépôt ne contient pas, et pourquoi

Le dépôt est **public**. Certains fichiers restent sur le disque mais sont
écartés par `.gitignore` :

| Quoi | Pourquoi |
|---|---|
| `certificat/phytoscope.key` | La clé privée de signature (`C-2R`). |
| `sources/ebooks/`, `sources/brevets/*.pdf`, `sources/datasheets/*.pdf`, `sources/manuels-constructeurs/*.pdf`, `sources/documents/articles-scientifiques/*.pdf` | **Nous n'avons pas le droit de les rediffuser.** Leurs références bibliographiques sont dans `sources/INDEX.md`, et nos notes de lecture (`.md`) sont versionnées. |
| `sources/documents/domaine-public/*.pdf` | Ici ce n'est **pas** une question de droits — Bose et Darwin sont dans le domaine public. C'est le poids : 260 Mo de numérisations, pour un dépôt qui pèse 162 Mo sans elles. Les **transcriptions** (`.txt`, `.html`, `.epub`) restent versionnées, et `sources/documents/domaine-public/LISEZ-MOI.md` donne la commande pour retélécharger les fac-similés depuis archive.org. |
| `sources/code/*.zip`, `sources/software/**/*.zip` | 817 Mo de dépôts tiers. `python3 tools/fetch-software.py` les récupère à la source ; `sources/software/MANIFESTE.md` garde provenance et licences. |
| `build/` | PDF et paquets produits — ils se reconstruisent. |
| `.venv/`, `__pycache__/`, `.ecarte/` | Régénérables. `.ecarte/` contient des doublons mis de côté ; il est supprimable sans conséquence. |

Le `.gitignore` couvre **bash, Python, Go, Rust, C/C++, Windows 10/11,
macOS/Darwin, Debian/Ubuntu/Mint et Fedora/RHEL**, et il est commenté ligne
à ligne.

---

## 12. Contribuer

Lisez [`CONTRIBUTING.md`](CONTRIBUTING.md), puis, **dans cet ordre** :

1. [`AGENTS.md`](AGENTS.md) — le point d'entrée ;
2. [`constraints.md`](constraints.md) — **80 contraintes numérotées**
   `C-1`…`C-64`. Elles font autorité : une contribution qui en contredit une
   est refusée, ou la contrainte change d'abord ;
3. [`.ai/etat.md`](.ai/etat.md) — où en est le travail ;
4. [`.ai/decisions.md`](.ai/decisions.md) — les décisions de conception **et
   leurs raisons**. Beaucoup de « pourquoi pas comme ça ? » y ont déjà leur
   réponse.

### Les cinq règles qui coûtent cher quand on les oublie

1. **Le français partout** — code, commentaires, docstrings, interface,
   messages de commit ; typographie française comprise.
2. **Expliquer le pourquoi.** Un commentaire qui paraphrase le code est à
   supprimer ; un commentaire qui dit *pourquoi* le code est ainsi est à
   garder.
3. **Vérifier, ne pas supposer.** Tout chiffre — pages, tests, références,
   prix, débit — **se mesure par une commande** avant d'être écrit.
4. **Ne jamais modifier un fichier généré** (`C-45`). On modifie la source et
   on relance le générateur.
5. **Tester avant de conclure** : `cd src/phytoscope && make test`.

Voir aussi [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md).

---

## 13. Chiffres du projet

Tous mesurés le 2026-09-18, par les commandes du dépôt.

| | |
|---|---:|
| Modules Python du logiciel | 67 |
| Lignes de Python (logiciel) | 22 783 |
| Tests, sans matériel ni réseau | 260 |
| Fichiers C du micrologiciel | 7 (1 460 lignes) |
| Langues de l'interface | 10 |
| Lexiques du mode vocal | 11 |
| Modules livrés avec le logiciel | 4 |
| Publications PDF | 10 (**1 378 pages**) |
| Fragments HTML d'édition | 227 |
| Illustrations générées | 104 (0 mal formée) |
| Photographies et planches | 234 |
| Références de nomenclature | 68 (244,35 €) |
| Contraintes au cahier des charges | 80 |
| Paquets produits par `make tout` | 8, tous signés |
| Workflows d'intégration continue | 6 |

---

## Licences

| Ce qui est couvert | Licence | SPDX |
|---|---|---|
| Logiciel, micrologiciel, trousse, outils, fabriques | **MIT** | `MIT` |
| Matériel — cartes, schémas, nomenclatures (`hardware/`) | **CERN-OHL-P v2** | `CERN-OHL-P-2.0` |

Le détail, les exceptions et les travaux tiers :
[`LICENSES/README.md`](LICENSES/README.md).

Les polices `Cinzel` et `Cormorant Garamond` sont sous SIL Open Font License
1.1. L'origine et la licence de chaque photographie sont dans
`pdf-src/assets/img/photos/CREDITS.md`.

---

© 2026 Bretagne Namasté — Thierry GAYET
[bretagne-namaste.com](https://bretagne-namaste.com) ·
contact@bretagne-namaste.com
