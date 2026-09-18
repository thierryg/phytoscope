# Micrologiciel PhytoSense One

Micrologiciel de la carte d'acquisition décrite dans *La Carte PhytoSense*.

**Cible** : RP2350 (Raspberry Pi) · **SDK** : Pico SDK 2.0 ou plus récent · **Pile USB** : TinyUSB
**Licence** : MIT · Bretagne Namasté — https://bretagne-namaste.com

---

## 1. Ce qu'il fait, et ce qu'il ne fait pas

Il fait quatre choses, et rien d'autre :

1. il cadence le convertisseur ADS131M04 et lit ses quatre voies ;
2. il **horodate** chaque échantillon par un compteur 64 bits issu du TCXO ;
3. il pousse le flux sur USB en **classe audio 2.0**, sans pilote ;
4. il répond au dialogue de contrôle sur le port série virtuel.

Il **n'interprète rien** : aucune détection d'événement, aucune règle musicale,
aucun filtrage autre que celui du convertisseur. Tout cela est calculé sur
l'ordinateur, où c'est modifiable, vérifiable et remplaçable.

Seule exception : la **sortie MIDI directe**, qui embarque une version réduite du
moteur de correspondance pour attaquer un synthétiseur matériel sans passer par la
chaîne audio de l'ordinateur. Elle ne rend pas la carte indépendante : l'ordinateur
reste requis pour la régler, recevoir le flux et enregistrer.

### Répartition des deux cœurs

| Cœur | Tâche | Contrainte |
|---|---|---|
| 0 | Service du convertisseur, horodatage, tampon circulaire | boucle bornée, aucune allocation, aucune attente |
| 1 | USB, dialogue de contrôle, capteurs d'ambiance, MIDI, afficheur | peut bloquer sans conséquence pour la mesure |

Les deux cœurs ne partagent que le tampon circulaire, par des indices atomiques.
C'est la raison pour laquelle le flux ne présente aucun trou même lorsque
l'ordinateur interroge la carte en pleine acquisition.

---

## 2. Où télécharger le SDK pour le RP2350

Le RP2350 exige le **Pico SDK version 2.0.0 au minimum** — les versions 1.x ne
connaissent que le RP2040 et échoueront à la configuration. La version 2.1.x est
recommandée.

### Le SDK

```bash
git clone --branch 2.1.1 https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init          # indispensable : TinyUSB est un sous-module
export PICO_SDK_PATH=$PWD            # à mettre dans ~/.bashrc ou ~/.zshrc
```

> **L'oubli de `git submodule update --init` est l'erreur numéro un.** Sans lui,
> `tinyusb` reste vide, et la compilation échoue sur `tusb.h: No such file`.

| Élément | Adresse |
|---|---|
| Pico SDK (dépôt officiel) | https://github.com/raspberrypi/pico-sdk |
| Documentation du SDK | https://www.raspberrypi.com/documentation/pico-sdk/ |
| Fiche technique RP2350 | https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf |
| Guide matériel RP2350 | https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf |
| Exemples officiels | https://github.com/raspberrypi/pico-examples |
| TinyUSB (documentation) | https://docs.tinyusb.org/ |

### La chaîne de compilation croisée

| Système | Commande |
|---|---|
| Debian, Ubuntu, Mint | `sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib build-essential git python3` |
| Fedora, RHEL, Rocky | `sudo dnf install cmake arm-none-eabi-gcc-cs arm-none-eabi-newlib git python3` |
| Arch, Manjaro | `sudo pacman -S cmake arm-none-eabi-gcc arm-none-eabi-newlib git python` |
| macOS (Homebrew) | `brew install cmake` puis `brew install --cask gcc-arm-embedded` |
| Windows | Installateur officiel **Pico SDK for Windows** — https://github.com/raspberrypi/pico-setup-windows/releases |

Sous Debian et Ubuntu, vérifiez que la version d'`arm-none-eabi-gcc` est au moins
la 10 : `arm-none-eabi-gcc --version`. Les versions plus anciennes ne connaissent
pas le cœur Cortex-M33 du RP2350.

### Le fichier `pico_sdk_import.cmake`

Il n'est pas fourni ici : il appartient au SDK et doit en être copié, afin de
rester synchronisé avec lui.

```bash
cp "$PICO_SDK_PATH/external/pico_sdk_import.cmake" .
```

### Solution sans rien installer

L'extension **Raspberry Pi Pico** de Visual Studio Code télécharge le SDK, la
chaîne de compilation et l'outillage de mise au point toute seule :
https://marketplace.visualstudio.com/items?itemName=raspberry-pi.raspberry-pi-pico

---

## 3. Construire

**Deux scripts, deux usages.**

| | Ce qu'il fait | Quand s'en servir |
|---|---|---|
| **`./_make_.sh`** | compile, et rien de plus → `build/phytosense.uf2` | pendant la mise au point, quand on compile vingt fois d'affilée |
| **`./build.sh`** | compile **puis range le livrable** dans `build/paquets/`, nommé avec sa version, avec ses empreintes et une notice | pour publier, et dans l'intégration continue |

```bash
./build.sh --deps     # Pico SDK et chaîne ARM dans $HOME, sans sudo — une fois
./build.sh            # compile et range le livrable
```

La première commande installe le SDK et la chaîne croisée **dans le dossier
personnel, sans privilèges** (`C-55`). La seconde produit :

```
build/phytosense.uf2                        ce que produit la compilation
build/paquets/<version>-<horodatage>/Firmware/
    phytosense-<version>.uf2                ce qu'on copie sur la carte
    phytosense-<version>.elf                pour le débogage
    phytosense-<version>.bin                image brute
    phytosense-<version>.sha256             les empreintes
    LISEZ-MOI.txt                           comment programmer la carte
```

**Pourquoi nommer le fichier avec sa version** : « phytosense.uf2 » tout court,
sur le disque de quelqu'un six mois plus tard, ne dit pas de quelle version il
sort. Et le `.uf2` est un livrable à part entière — sans lui, les paquets
installent un logiciel qui n'a rien à écouter.

### Les options

| Option | Effet |
|---|---|
| `--deps` | installe le Pico SDK et la chaîne ARM dans `$HOME` |
| `--propre` | repart d'un répertoire de construction vide |
| `--sortie DOSSIER` | range le livrable ailleurs |
| `--sans-installer` | compile seulement, comme `./_make_.sh` |

`build.sh` passe à `_make_.sh` tout ce qu'il ne reconnaît pas : les options de
compilation restent donc celles de `_make_.sh`.

### À la main, si l'on préfère

```bash
export PICO_SDK_PATH=/chemin/vers/pico-sdk
cp "$PICO_SDK_PATH/external/pico_sdk_import.cmake" .
mkdir -p build && cd build
cmake .. -DPICO_BOARD=pico2 -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
# → phytosense.uf2, phytosense.elf, phytosense.bin
```

`-DPICO_BOARD=pico2` sélectionne le RP2350. Pour une carte nue, sans définition de
carte toute faite : `-DPICO_PLATFORM=rp2350 -DPICO_BOARD=none`.

### Si `cmake` refuse de partir

```
CMake Error: The current CMakeCache.txt directory … is different than
the directory … where CMakeCache.txt was created.
```

Un cache CMake retient le **chemin absolu** des sources : déplacer ou renommer
la copie de travail le rend périmé. `_make_.sh` le détecte maintenant et le
jette de lui-même — ce message ne devrait plus apparaître. Si cela arrive
quand même : `rm -rf build`.

---

## 4. Programmer la carte

### Voie 1 — glisser-déposer (la plus simple)

1. Maintenir **BOOTSEL** enfoncé ;
2. brancher le câble USB, ou appuyer brièvement sur RESET ;
3. relâcher BOOTSEL : un volume `RP2350` apparaît ;
4. y copier `phytosense.uf2` ;
5. la carte redémarre seule et s'énumère.

Aucun outil, aucun pilote, aucun droit d'administration. C'est la voie normale.

### Voie 2 — sonde de mise au point (pour développer)

Une seconde carte Pico transformée en sonde suffit. Elle apporte l'exécution pas
à pas, les points d'arrêt et la console série.

```bash
# téléverser
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg \
        -c "adapter speed 5000" -c "program phytosense.elf verify reset exit"

# déboguer
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000" &
arm-none-eabi-gdb phytosense.elf -ex "target extended-remote localhost:3333"
```

| Élément | Adresse |
|---|---|
| Sonde (micrologiciel `debugprobe`) | https://github.com/raspberrypi/debugprobe |
| OpenOCD, branche Raspberry Pi | https://github.com/raspberrypi/openocd |

Le connecteur SWD de la carte est un embase à trois points au pas de 1,27 mm,
repérée `SWD` sur la sérigraphie : SWCLK, SWDIO, masse.

### Voie 3 — mise à jour par l'utilisateur final

Le logiciel PhytoScope détecte une version de micrologiciel plus ancienne que
celle qu'il embarque et propose la mise à jour. Elle passe par la même interface
UF2 : la carte redémarre en mode chargeur, le fichier est copié, la carte revient.
L'utilisateur ne voit qu'une barre de progression.

---

## 5. Les autres composants programmables

| Composant | Ce qu'on y écrit | Comment |
|---|---|---|
| **U30** RP2350 | le micrologiciel | UF2 ou SWD, voir ci-dessus |
| **U31** W25Q128 (flash QSPI) | le micrologiciel et les réglages mémorisés | à travers le RP2350, jamais directement |
| **EEPROM 24AA02** des cartes filles | type, numéro de série, date et coefficients d'étalonnage | `../outils/provision_eeprom.py`, par le bus I²C de la carte mère |
| **DS5** afficheur SSD1306 | rien — séquence d'initialisation seulement | envoyée par le micrologiciel au démarrage |
| **U10** ADS131M04 | registres MODE, CLOCK, GAIN | écrits par `afe_init()` à chaque démarrage |
| **U63** INA219 | registre de configuration et étalonnage du shunt | écrit par le micrologiciel |

La mémoire de la carte fille est le seul élément à programmer **une fois, en
fabrication**. Tout le reste est reconstruit à chaque mise sous tension : une
carte qui perd sa configuration n'existe pas.

### Carte des zones de la mémoire flash

| Adresse | Taille | Contenu |
|---|---|---|
| `0x10000000` | 1 Mo | micrologiciel |
| `0x10100000` | 4 ko | réglages mémorisés (gain, gamme, profil MIDI) |
| `0x10101000` | 4 ko | étalonnage d'usine — écrit en recette, jamais effacé |
| `0x10102000` | reste | journal d'événements en anneau |

---

## 6. Fichiers

| Fichier | Rôle | Lignes |
|---|---|---|
| `main.c` | boucles des deux cœurs, horodatage, tampon circulaire, remise USB | 246 |
| `afe.c` / `afe.h` | convertisseur, gain, gamme, auto-test, mémoire de carte fille | 443 + 63 |
| `protocol.c` / `protocol.h` | dialogue de contrôle, réponses JSON | 276 + 31 |
| `usb_descriptors.c` | descripteurs du périphérique composite UAC2 + CDC | 221 |
| `tusb_config.h` | configuration de TinyUSB | 62 |
| `CMakeLists.txt` | construction | 38 |
| `_make_.sh` | compile — SDK, chaîne ARM, cmake | — |
| `build.sh` | compile **et range le livrable** dans `build/paquets/` | — |

---

## 7. Vérifier que le micrologiciel fonctionne

Sans rien installer d'autre qu'un terminal :

```bash
# Linux ou macOS
screen /dev/ttyACM0 115200        # ou : picocom -b 115200 /dev/ttyACM0
# Windows : PuTTY, connexion série, 115200 bauds
```

Taper `?` puis Entrée. La carte doit répondre en une ligne :

```
+{"model":"PhytoSense One","serial":"PS1-4A17C302","firmware":"1.0.0",
  "channels":4,"sample_rate":250.0,"frontend":"FE-Z", ... }
```

Si cette ligne apparaît, le microcontrôleur, l'USB, le convertisseur et la mémoire
de la carte fille fonctionnent tous les quatre. Sinon, le chapitre 10 du document
indique quoi chercher, dans quel ordre.

---

## 8. État de cette publication

**Ces sources compilent.** Elles produisent `phytosense.uf2` (80 ko),
`phytosense.elf` (764 ko) et `phytosense.bin` (40 ko), pour 44 776 octets de
code et 106 508 de données. L'intégration continue les compile à chaque
passage — `.github/workflows/paquets.yml`, job « micrologiciel » — et joint le
livrable aux artéfacts avec ses empreintes.

> Cette section disait jusqu'au 2026-09-18 que les sources « n'avaient pas été
> compilées ici ». C'était vrai quand elle a été écrite, et c'est ce que
> corrige la contrainte `C-3` : **vérifier avant d'affirmer.** La compilation
> est désormais automatique, et le décompte ci-dessus vient de
> `arm-none-eabi-size`.

### Ce qui reste à éprouver, et qui ne peut pas l'être ici

**Aucune carte n'a été branchée.** Ce qui compile n'est pas ce qui fonctionne :
la configuration du convertisseur, le brochage et les temps de réponse
demandent le matériel. Attendez-vous donc à ajuster :

- une broche, selon le brochage définitif de votre carte ;
- les constantes de gain de l'étage d'entrée ;
- les délais du dialogue avec le convertisseur.

Ce qui est juste, en revanche, et ce qui a demandé le travail : la discipline
d'horodatage, la séparation des deux cœurs, et le dialogue de contrôle — que
l'on peut éprouver sans carte, par un terminal série (voir le § 7).

### Une dépendance à surveiller

`usb_descriptors.c` dépend de la macro `TUD_AUDIO_MIC_FOUR_CH_DESCRIPTOR`,
présente dans TinyUSB depuis la version fournie avec le SDK 2.0. Le SDK utilisé
est figé dans `_make_.sh` (`SDK_VERSION`), et `tools/sbom.py` le lit là :
la nomenclature du projet dit donc toujours quelle version est en service.
