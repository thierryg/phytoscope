# Fabriquer les paquets

Ce fichier dit **comment produire un paquet précis, ou tous**, et ce qu'il
faut avoir avant. Il ne décrit pas ce que fait un installateur une fois entre
les mains de qui l'exécute : cela, c'est [`INSTALL.md`](INSTALL.md).

Tout se passe depuis `packaging/`, et tout passe par `make`.

> **Un seul poste Debian, Ubuntu ou Mint produit les paquets de tous les
> systèmes.** Windows et macOS sont fabriqués par compilation croisée — NSIS,
> msitools et un générateur de `.pkg` écrit de bout en bout. Il n'y a pas de
> machine Windows ni de Mac dans la boucle, et c'est assumé : ce qui est
> vérifié ici, c'est la **structure** des paquets, pas leur installation.

---

## Table des matières

1. [En cinq minutes](#1-en-cinq-minutes)
2. [Ce qu'il faut avoir](#2-ce-quil-faut-avoir)
3. [Le certificat de signature](#3-le-certificat-de-signature)
4. [Fabriquer un paquet précis](#4-fabriquer-un-paquet-précis)
4 bis. [Fabriquer le micrologiciel](#4-bis-fabriquer-le-micrologiciel)
5. [Fabriquer tout](#5-fabriquer-tout)
6. [Imposer la version, la révision, la destination](#6-imposer-la-version-la-révision-la-destination)
7. [Vérifier ce qui a été produit](#7-vérifier-ce-qui-a-été-produit)
8. [La nomenclature logicielle](#8-la-nomenclature-logicielle)
9. [Publier une version](#9-publier-une-version)
10. [Quand ça échoue](#10-quand-ça-échoue)
11. [Toutes les cibles](#11-toutes-les-cibles)

---

## 1. En cinq minutes

```bash
cd packaging

make outils        # ce qui est installé, ce qui manque
make deps          # installe NSIS, msitools, osslsigncode — sans sudo
make certificat    # une seule fois, puis jamais
make tout          # les neuf paquets, signés
make verifier      # rouvre et contrôle tout ce qui a été produit
```

Les paquets arrivent dans
`build/paquets/<version>-<horodatage>/`, et `build/paquets/dernier` pointe sur
la dernière fabrication.

---

## 2. Ce qu'il faut avoir

`make outils` répond, et ne se trompe pas :

```
  ✓ dpkg-deb   paquet Debian (.deb)
  ✓ rpmbuild   paquet Red Hat (.rpm)
  ✓ makensis   installateur Windows (.exe)
  ✓ wixl       paquet Windows (.msi)
  ✓ zip        archives Windows et macOS
  ✓ openssl    certificat et signatures
  ✓ osslsigncode signature Authenticode (.exe, .msi)
```

### Ce qui manque s'installe sans `sudo`

```bash
make deps
```

NSIS, msitools et osslsigncode sont dépliés dans `~/.local/opt`. Le projet
s'interdit d'élever les droits (`C-55`) : aucune de ces commandes n'appelle
`sudo`.

`dpkg-deb` et `rpmbuild`, eux, viennent de votre distribution :

```bash
sudo apt install dpkg-dev fakeroot rpm
```

### L'environnement Python du projet

La fabrique utilise l'interpréteur du projet s'il existe
(`src/phytoscope/.venv/bin/python`), sinon celui du système. Pour le créer :

```bash
cd ../src/phytoscope && make install-dev
```

---

## 3. Le certificat de signature

**Une seule fois dans la vie du projet.** Ensuite, on n'y touche plus.

```bash
make certificat          # crée s'il n'existe pas, puis remplit certificat/
make certificat-etat     # ce qui existe, et où
make certificat-verifier # les deux copies concordent-elles ?
```

### Où vit quoi

| Où | Quoi | Dans le dépôt ? |
|---|---|---|
| `~/.local/share/phytoscope-signature/` | la copie de **référence** : clé privée + certificat | **non**, et jamais |
| `certificat/` | la copie de **travail** : certificat public, `.crt`, clé en 0600, notice | le public **oui**, la clé **jamais** |

La contrainte `C-2R` n'autorise la clé privée qu'à ces deux endroits. Trois
filets l'empêchent d'être publiée : `.gitignore` l'écarte nommément, le
crochet `pre-commit` la refuse **sur son seul nom** — même vide, même
renommée —, et le job « secrets » de l'intégration continue échoue si elle
apparaît. Trois, parce qu'une clé publiée ne se dépublie pas.

### Si le certificat manque au moment de signer

La fabrique **le dit et propose**, elle ne crée rien d'autorité :

```
  ! aucun certificat de signature : les paquets ne seront pas signés.
      La copie de référence est attendue dans
      /home/…/.local/share/phytoscope-signature

  En créer un maintenant ? [o/N]
```

Sans terminal — dans un script, dans l'intégration continue — elle affiche la
commande et s'arrête plutôt que de supposer un accord : fabriquer une clé de
signature à l'improviste produirait une clé éphémère qu'on croirait
permanente.

### SAUVEGARDEZ la clé privée

Sans elle, les versions suivantes ne pourront plus être rattachées aux
précédentes. Qui avait noté l'empreinte verrait soudain une autre.

```bash
make empreinte-certificat     # l'empreinte SHA-256, celle qu'on publie
```

### Refaire le certificat — ce qu'il faut savoir avant

```bash
make certificat-refait
```

Cela **remplace la clé** et **rompt le lien** avec tout ce qui a été signé :
les paquets déjà publiés deviennent invérifiables avec le nouveau certificat.
La commande demande de taper `REMPLACER` en entier, et refuse s'il n'y a pas
de terminal. Ajoutez `--oui` à `certificat.py --refaire` seulement si c'est
vraiment voulu.

### Ce que ce certificat prouve, et ce qu'il ne prouve pas

Il est **auto-signé**. Il prouve l'**intégrité** d'un paquet et la
**continuité d'origine**. Il ne fait **pas** taire SmartScreen ni Gatekeeper,
et n'a jamais prétendu le faire (`C-2Q`).

---

## 4. Fabriquer un paquet précis

| Commande | Produit | Pour |
|---|---|---|
| `make debian` | `phytoscope_<v>_all.deb` **et** `PhytoScope-<v>-Linux.run` | Debian, Ubuntu, Mint — et toutes distributions pour le `.run` |
| `make fedora` | `phytoscope-<v>-1.noarch.rpm` | Fedora, RHEL, Rocky, Alma |
| `make windows` | `PhytoScope-<v>-Windows.exe`, `.msi`, `-portable.zip` | Windows 10 / 11 |
| `make macos` | `PhytoScope-<v>.pkg`, `-macOS.zip` | macOS Intel et Apple Silicon |
| `make source` | `phytoscope-<v>.tar.gz` | tous systèmes |
| `make linux` | `.deb` + `.run` + `.rpm` | les deux familles Linux |

### Par le script, pour les options fines

```bash
python3 packaging/construire_debian.py            # .deb et .run
python3 packaging/construire_fedora.py            # .rpm
python3 packaging/construire_windows.py --msi     # le .msi seulement
python3 packaging/construire_macos.py --pkg       # le .pkg seulement
python3 packaging/construire_macos.py --arch arm64
python3 packaging/construire_source.py
```

### Combien de temps, et combien de place

| Cible | Durée | Taille |
|---|---:|---:|
| `source` | quelques secondes | 640 ko |
| `debian` | ~1 min *(le `.run` embarque un interpréteur)* | 388 ko + 29 Mo |
| `fedora` | quelques secondes | 636 ko |
| `macos` | ~1 min | 18 + 19 Mo |
| `windows` | **~15 min** *(250 Mo de roues à télécharger)* | 178 + 275 + 262 Mo |

`make windows` est de loin le plus long : il récupère l'interpréteur
embarquable et les roues Qt, puis compresse trois fois le même contenu. C'est
pourquoi `make tout` enchaîne les cibles rapides d'abord — une panne d'outil
se voit en dix secondes plutôt qu'au bout du quart d'heure.

### Sans réseau

```bash
make hors-ligne
```

Les roues sont embarquées dans les paquets : l'installation chez qui les
reçoit se fait alors sans connexion. Les paquets grossissent d'autant — Qt
pèse 450 Mo en « universal2 » pour macOS.

---

## 4 bis. Fabriquer le micrologiciel

Le `.uf2` est un **livrable à part entière** : sans lui, les paquets
installent un logiciel qui n'a rien à écouter.

**Deux scripts, deux usages.**

| | Ce qu'il fait | Quand |
|---|---|---|
| `./_make_.sh` | compile, et rien de plus → `build/phytosense.uf2` | pendant la mise au point, quand on compile vingt fois d'affilée |
| `./build.sh` | compile **puis range le livrable** dans `build/paquets/` | pour publier, et dans l'intégration continue |

```bash
cd src/firmware
./build.sh --deps      # Pico SDK et chaîne ARM dans $HOME, sans sudo — une fois
./build.sh             # compile et range le livrable
```

Le livrable arrive **au même endroit que les paquets**, parce que c'en est un :

```
build/paquets/<version>-<horodatage>/Firmware/
    phytosense-<version>.uf2      ce qu'on copie sur la carte
    phytosense-<version>.elf      pour le débogage
    phytosense-<version>.bin      image brute
    phytosense-<version>.sha256   les empreintes
    LISEZ-MOI.txt                 comment programmer la carte
```

Le nom porte la version : « phytosense.uf2 » tout court, sur le disque de
quelqu'un six mois plus tard, ne dit pas de quelle version il sort.

| Option de `build.sh` | Effet |
|---|---|
| `--deps` | installe le Pico SDK et la chaîne ARM dans `$HOME` |
| `--propre` | repart d'un répertoire de construction vide |
| `--sortie DOSSIER` | range ailleurs |
| `--sans-installer` | compile seulement, comme `./_make_.sh` |

Lancé par la fabrique de paquets, il suit la variable `PHYTOSCOPE_SORTIE` :
le micrologiciel se range alors dans **la même fabrication** que les `.deb` et
les `.msi`, même lancé séparément. D'où deux cibles, depuis `packaging/` :

```bash
make micrologiciel     # le .uf2, rangé dans la fabrication en cours
make livrables         # les paquets ET le micrologiciel, ensemble
```

**`micrologiciel` est volontairement hors de `make tout`** : compiler demande
une chaîne croisée ARM que la machine qui empaquette n'a pas forcément, et un
`make tout` qui échouerait faute de `arm-none-eabi-gcc` serait une mauvaise
surprise. `make livrables` est là pour qui veut les deux d'un coup.

### Ce qu'il faut sur la machine

```bash
sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi                  libstdc++-arm-none-eabi-newlib
```

Le Pico SDK (**2.0.0 minimum** — les versions 1.x ne connaissent que le
RP2040 et échouent à la configuration) et la chaîne ARM sont installés par
`--deps` dans `$HOME`, sans privilèges.

### Si la compilation refuse de partir

```
CMake Error: The current CMakeCache.txt directory … is different than
the directory … where CMakeCache.txt was created.
```

Un cache CMake retient le **chemin absolu** des sources : déplacer ou
renommer la copie de travail le rend périmé. `build.sh` le détecte
maintenant et le jette de lui-même — le message ne devrait plus apparaître.
Si cela arrive quand même : `rm -rf src/firmware/build`.

### Dans l'intégration continue

`paquets.yml` compile le micrologiciel à chaque passage — un binaire
fabriqué à la main est un binaire dont personne ne sait de quel commit il
sort — et le joint aux artéfacts avec ses empreintes. `diffusion.yml` le
publie avec la version, sous le nom `phytosense-<version>.uf2`, et **atteste
sa provenance** comme celle des paquets.

---

## 5. Fabriquer tout

```bash
make tout
```

Enchaîne, **dans cet ordre, qui n'est pas indifférent** :

```
source → linux → macos → windows → certificat → signer → documents
```

1. **les cibles rapides d'abord** — une panne d'outil se voit tout de suite ;
2. **`certificat`** avant `signer`, évidemment ;
3. **`signer`** avant `documents` : la signature Authenticode **modifie** le
   `.exe` et le `.msi`, et les empreintes doivent donc être calculées
   **après** elle. `documents` écrit les empreintes ; il vient en dernier.

Puis `make tout` appelle `verifier.py` de lui-même et en affiche le bilan.

### Ce que cela produit

> **Le micrologiciel n'est pas dans `make tout`.** Il se compile par
> `src/firmware/build.sh` ou `make micrologiciel` (voir le
> [§ 4 bis](#4-bis-fabriquer-le-micrologiciel)), et la CI le joint aux
> livrables. Les deux chaînes sont séparées parce que leurs outils le sont :
> `make tout` n'a pas besoin d'un compilateur ARM. `make livrables` fait les
> deux.

**Neuf paquets**, chacun accompagné de :

- son empreinte `.sha256` ;
- sa signature — `.p7s` (CMS détachée) pour tous, **Authenticode** pour le
  `.exe` et le `.msi` ;
- sept documents : `AUTHENTICITE.txt`, `install.txt`, `manuel.txt`,
  `readme.txt`, `licence.txt`, `changelog.txt`,
  `phytoscope-certificat.pem`.

Rangés par système :

```
build/paquets/1.5.1-20260918-2044/
├── phytoscope-1.5.1.tar.gz          + .sha256 .p7s
├── Linux/    .deb  .run  .rpm       + empreintes, signatures, documents
├── Windows/  .exe  .msi  .zip
├── MacOSX/   .pkg  .zip
└── (documents à la racine)
```

---

## 6. Imposer la version, la révision, la destination

La version est lue dans `src/phytoscope/phytoscope/VERSION`, **seule source
de vérité**. Pour la contourner le temps d'un essai :

```bash
make tout VERSION=1.6.0            # une autre version
make tout RELEASE=2                # révision du paquet, pas du logiciel
make tout SORTIE=/tmp/essai        # ailleurs que dans build/paquets/
make debian VERSION=1.6.0 RELEASE=2
```

Pour **changer** la version pour de bon, c'est le logiciel qui décide :

```bash
cd ../src/phytoscope
make bump-patch      # 1.5.1 → 1.5.2
make bump-minor      # 1.5.1 → 1.6.0
make bump-major      # 1.5.1 → 2.0.0
make release-check   # la version est-elle diffusable ?
```

`release-check` refuse une version suffixée (`-dev`, `-rc1`) : elle n'est pas
destinée à être diffusée.

---

## 7. Vérifier ce qui a été produit

```bash
make verifier      # rouvre chaque paquet et contrôle sa cohérence
make empreintes    # recalcule les .sha256
```

`make verifier` contrôle, pour chaque paquet :

- qu'il s'**ouvre** — un `.deb` se relit par `dpkg-deb`, un `.rpm` par
  `rpm -qp`, un `.msi` par `msiinfo`, un `.pkg` par `xar`, une archive par
  son propre format ;
- que la **version annoncée** dedans correspond à celle attendue ;
- que la **nomenclature interne** concorde avec la charge réelle ;
- que les **empreintes SHA-256** correspondent ;
- que les **sept documents** sont présents dans chaque dossier système.

Il termine par un avertissement qu'il faut lire :

```
  ! aucun de ces paquets n'a été INSTALLÉ : il n'y a sur cette machine
    ni Windows, ni macOS, ni Fedora. Ce qui est vérifié ici, c'est leur
    structure et leur cohérence interne.
```

L'installation réelle se teste sur chaque système. L'intégration continue y
aide : `paquets.yml` passe les tests sur Linux, Windows et macOS.

### Vérifier une signature à la main

```bash
cd build/paquets/dernier
openssl cms -verify -binary -inform DER -in Linux/phytoscope_1.5.1_all.deb.p7s \
    -content Linux/phytoscope_1.5.1_all.deb \
    -certfile phytoscope-certificat.pem -noverify -out /dev/null
```

---

## 8. La nomenclature logicielle

Deux nomenclatures, deux portées — et c'est voulu.

| Fichier | Portée | Produit par |
|---|---|---|
| `src/phytoscope/sbom.cdx.json` | **le logiciel** — c'est elle qui est livrée dans les paquets | `src/phytoscope/tools/sbom.py` |
| `sbom.cdx.json` (racine) | **le projet entier** — logiciel *et* micrologiciel RP2350 | `tools/sbom.py` |

```bash
python3 tools/sbom.py                  # le relevé, en texte
python3 tools/sbom.py --ecrire         # écrit sbom.cdx.json (CycloneDX 1.6)
python3 tools/sbom.py --verifier       # est-il à jour ? code 1 sinon
python3 tools/sbom.py --logiciel-seul  # régénère aussi celui du logiciel
```

La partie micrologiciel lit les versions **dans les fichiers qui font foi** —
`src/firmware/_make_.sh` pour le Pico SDK et la chaîne ARM,
`CMakeLists.txt` pour les bibliothèques réellement liées. Rien n'est recopié
à la main : une version écrite dans un tableau vieillirait en silence.

Le compilateur ARM et `picotool` y portent `scope: excluded` : ils
**construisent** le produit, ils n'y sont pas embarqués. La distinction
compte pour qui lit ce document afin de savoir si une faille le concerne.

> **Un SBOM faux est pire qu'aucun SBOM.** Il sert à répondre « cette faille
> me concerne-t-elle ? ». `.github/workflows/sbom.yml` le régénère dès
> qu'une modification touche `src/phytoscope/`, et `securite.yml` refuse
> qu'il dérive.

---

## 9. Publier une version

```bash
# 1. la version, à la source
cd src/phytoscope
make bump-patch && make release-check

# 2. les tests, avant tout
make test                      # 306, sans matériel ni réseau

# 3. les nomenclatures
cd .. && python3 tools/sbom.py --ecrire --logiciel-seul

# 4-5. les paquets ET le micrologiciel, dans la même fabrication
cd packaging && make livrables && make verifier

# 6. les publications, si elles ont changé
cd .. && git diff --name-only | python3 tools/pdf_impactes.py -

# 7. l'étiquette — c'est elle qui déclenche la diffusion
git tag -a v1.5.2 -m "PhytoScope 1.5.2"
git push --tags
```

L'étiquette déclenche `.github/workflows/diffusion.yml`, qui **vérifie que
l'étiquette correspond à `VERSION`** — une étiquette qui ne correspond pas
produirait des paquets estampillés d'un numéro que personne ne retrouverait —,
rejoue les tests, refabrique tout — **paquets, micrologiciel et
publications** —, **atteste la provenance** de chaque livrable auprès de
GitHub (Sigstore), et publie.

Qui télécharge peut alors vérifier d'où sort un fichier :

```bash
gh attestation verify phytoscope_1.5.2_all.deb --repo thierryg/phytoscope
```

La CI signe la **provenance** ; l'éditeur signe l'**origine**. Les deux sont
utiles et ne se remplacent pas.

---

## 10. Quand ça échoue

### « makensis a échoué »

Le plus souvent : **plus de place**. NSIS compresse ~500 Mo d'un coup.

```bash
df -h .
make propre                    # vide build/paquets
```

Sinon, l'erreur exacte se voit en montant la verbosité — `-V2` dans
`construire_windows.py` devient `-V4`.

### « rpmbuild absent »

```bash
sudo apt install rpm
```

### « dépendances non installées » à l'installation du `.deb`

L'installation **n'est pas annulée** : le logiciel le dira au démarrage.

```bash
sudo dpkg-reconfigure phytoscope
phytoscope --check
```

### Le `.deb` ne se produit plus

Regardez `packaging/gabarits/debian/control` : **un fichier `control`
n'admet aucun commentaire.** Une ligne commençant par `#` fait échouer
`dpkg-deb` avec « field name '#' must be followed by colon » — et `make tout`
continue, produisant les huit autres paquets sans broncher. C'est arrivé le
2026-09-18 ; `"control"` est depuis dans les exclusions de
`tools/entetes.py`.

### « aucun certificat de signature »

Voir le [§ 3](#3-le-certificat-de-signature). `make certificat`.

### Les paquets Windows pèsent 275 Mo — est-ce normal ?

Oui. Ils embarquent l'interpréteur Python et Qt, pour n'exiger **rien** de la
machine. Les autres systèmes s'appuient sur leur Python.

---

## 11. Toutes les cibles

```
Préparation
  make outils                 ce qui est installé, ce qui manque
  make deps                   installe NSIS et msitools sans sudo

Un système
  make debian                 .deb et .run
  make fedora                 .rpm
  make windows                .zip .exe .msi
  make macos                  .zip .pkg
  make source                 .tar.gz

Plusieurs
  make tout                   les neuf paquets, signés
  make linux                  .deb .run .rpm
  make hors-ligne             avec les bibliothèques embarquées

Micrologiciel
  make micrologiciel          compile le .uf2 et le range dans la fabrication
  make livrables              les paquets ET le micrologiciel

Signature
  make certificat             crée le certificat et remplit certificat/
  make certificat-etat        ce qui existe, et où
  make certificat-verifier    les deux copies concordent ?
  make certificat-refait      REMPLACE la clé (rompt le lien)
  make signer                 signe les paquets de la fabrication
  make empreinte-certificat   son empreinte SHA-256

Après coup
  make documents              readme, install, licence, changelog, empreintes
  make verifier               relit et contrôle ce qui a été produit
  make empreintes             recalcule les .sha256
  make propre                 vide build/paquets

  make version                affiche la version qui serait utilisée
  make aide                   ce résumé
```

---

## Où vit quoi, dans `packaging/`

```
Makefile               enchaîne les cibles
commun.py              ce qui ne dépend d'aucun système : identité,
                       copie du logiciel, roues, interpréteurs embarqués
construire.py          --outils, --deps
construire_debian.py   le .deb et l'installateur .run
construire_fedora.py   le .rpm
construire_windows.py  le .exe, le .msi, l'archive portable
construire_macos.py    le .app, le .zip, le .pkg
construire_source.py   le .tar.gz
macos_pkg.py           le format .pkg, écrit de bout en bout
signature.py           certificat X.509, Authenticode, CMS
certificat.py          crée, recrée et dépose le certificat
verifier.py            rouvre et contrôle ce qui a été produit
langues.py             les libellés des installateurs, 11 langues
langues/               installateur.json — 51 libellés × 11 langues
gabarits/              control, .spec, .nsi, .wxs, Info.plist, lanceurs
```

---

© 2026 Bretagne Namasté — Thierry GAYET · [bretagne-namaste.com](https://bretagne-namaste.com)
