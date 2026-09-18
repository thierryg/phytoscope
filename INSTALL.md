# Installation de PhytoScope

Ce fichier décrit **ce que fait chaque installateur, étape par étape**, pour
chaque système. Il ne remplace pas `README.md` (le projet vu de l'extérieur)
ni `packaging/README.md` (la fabrique des paquets) : il répond à une seule
question — *qu'est-ce qui se passe sur ma machine quand j'installe, et où ?*

> **Version décrite** : 1.5.1 — 18 septembre 2026.
> Les chiffres de taille sont ceux mesurés à cette fabrication.

---

## Table des matières

- [Ce qui est vrai sur tous les systèmes](#ce-qui-est-vrai-sur-tous-les-systèmes)
- [Debian · Ubuntu · Mint — `.deb`](#debian--ubuntu--mint--deb)
- [Fedora · RHEL · Rocky · AlmaLinux — `.rpm`](#fedora--rhel--rocky--almalinux--rpm)
- [Toutes distributions — `.run`](#toutes-distributions--run)
- [Windows 10 / 11 — `.exe`, `.msi`, archive portable](#windows-10--11--exe-msi-archive-portable)
- [macOS — `.pkg` et `.zip`](#macos--pkg-et-zip)
- [Depuis les sources](#depuis-les-sources)
- [Vérifier ce que vous avez téléchargé](#vérifier-ce-que-vous-avez-téléchargé)
- [Désinstaller](#désinstaller)
- [Quand ça ne démarre pas](#quand-ça-ne-démarre-pas)

---

## Ce qui est vrai sur tous les systèmes

### Un environnement Python privé, jamais celui du système

PhytoScope n'installe **rien** dans le Python de votre machine. Chaque
installateur crée un environnement virtuel qui lui appartient, et y pose
NumPy, PySide6, pyqtgraph, sounddevice et pyserial. La raison est simple :
PySide6 n'est pas dans les dépôts de toutes les distributions, et écraser une
version système casserait d'autres logiciels.

### L'interpréteur est fourni quand le système n'en a pas

| Système | D'où vient Python |
|---|---|
| Debian, Ubuntu, Mint | déclaré en dépendance — `apt` l'installe |
| Fedora, RHEL | déclaré en dépendance — `dnf` l'installe |
| Toutes distributions (`.run`) | celui du système s'il convient, **sinon celui que l'installateur transporte** |
| Windows | **toujours embarqué** (distribution officielle « embeddable ») |
| macOS | **embarqué**, sinon python.org, sinon celui d'Apple |

Les interpréteurs embarqués sont des **binaires relogeables** : ils
fonctionnent depuis n'importe quel dossier, sans être installés, sans
privilèges et sans toucher au système.

### Homebrew, Nix et conda sont écartés — délibérément

Un interpréteur posé sous `/home/linuxbrew`, `/opt/homebrew`, `/nix/store` ou
`/opt/conda` vient avec **son propre chargeur dynamique**. Il ne lit pas le
chemin de recherche de la distribution : Qt, pyqtgraph et sounddevice s'y
installent sans erreur, puis échouent à l'exécution sur `libGL.so.1` ou
`libportaudio.so.2` — des bibliothèques **pourtant présentes**.

Tous les installateurs et tous les lanceurs les écartent donc, et
`run.py` se relance de lui-même avec un interpréteur convenable.

### La langue est demandée au tout début, et retenue

**Elle est demandée, jamais devinée.** La contrainte `C-31` interdit la
détection automatique de la locale, et ce n'est pas une coquetterie : une
machine dont l'environnement dit `fr_FR` peut être celle d'un atelier où l'on
travaille en anglais, celle d'un poste partagé, ou celle d'une image système
clonée.

Onze langues : **français, anglais, espagnol, portugais, italien, indonésien,
russe, chinois simplifié, japonais, coréen, arabe.** Chacune est proposée
**dans sa propre écriture** — un lecteur coréen reconnaît « 한국어 », pas
« coréen ».

| Installateur | Quand la question est posée |
|---|---|
| `.run` | **première question**, avant la licence — qui est donc lue dans la langue retenue |
| `.exe` Windows | boîte de dialogue NSIS, avant la première page |
| `.pkg` / `.app` macOS | à la **première ouverture** de l'application |
| `.deb`, `.rpm` | `apt` et `dnf` n'interrogent pas — la question est posée au **premier démarrage du logiciel** |
| depuis les sources | idem : au premier démarrage |

Le choix est écrit dans `reglages.json`, clé `ui.language`, que PhytoScope
relit à chaque démarrage. **L'installateur et le logiciel parlent donc la même
langue sans se concerter**, et la question ne revient jamais. Elle se modifie
ensuite par « Affichage → Langue ».

Les trois installateurs passent par le même utilitaire,
`tools/ecrire_langue.py`, qui **fusionne** au lieu d'écraser : une
réinstallation par-dessus une installation existante ne change que la langue.

Pour imposer la langue sans être interrogé — installation sans surveillance,
image système, déploiement :

```bash
./PhytoScope-1.5.1-Linux.run -y --langue ja
```

### Un cache de bytecode, construit une fois

Sans lui, Python recompile à chaque démarrage tous les modules dont le dossier
n'est pas inscriptible — `/usr/share`, `/Applications`, `Program Files` — et
jette le résultat. L'attente se voit : quelques secondes, à chaque lancement.
Chaque installateur construit donc le cache pendant l'installation, tant qu'il
a les droits d'écriture.

### Aucun `sudo` là où il n'est pas nécessaire

Le projet s'interdit d'élever les droits à l'insu de qui installe
(contrainte `C-55`). Les seuls cas où des privilèges sont requis sont ceux où
c'est vous qui les donnez : `sudo apt install ./phytoscope.deb`,
`sudo dnf install`, ou un `.run` lancé par `root` pour installer pour toute la
machine.

### Vos données ne sont jamais touchées par une désinstallation

| Quoi | Où |
|---|---|
| Réglages et journal | `~/.config/phytoscope/` · `%APPDATA%\PhytoScope` · `~/Library/Application Support/PhytoScope` |
| Séances enregistrées | `~/.local/share/phytoscope/seances/` |

Aucun installateur ne les supprime. Les commandes pour le faire vous-même sont
données à la fin de chaque désinstallation.

---

## Debian · Ubuntu · Mint — `.deb`

**Fichier** : `phytoscope_1.5.1_all.deb` (369 ko)

```bash
sudo apt install ./phytoscope_1.5.1_all.deb
```

`apt` — et non `dpkg -i` — parce qu'il résout les dépendances. Avec `dpkg`,
il faut ensuite `sudo apt install -f`.

### Ce qui se passe, dans l'ordre

1. **`apt` installe les dépendances déclarées** : `python3` (≥ 3.9),
   `python3-venv`, `python3-pip`, et **20 bibliothèques système** —
   `libgl1`, `libegl1`, `libglx0`, `libopengl0`, `libxkbcommon-x11-0`, les
   sept `libxcb-*`, `libfontconfig1`, `libfreetype6`, `libdbus-1-3`,
   `libportaudio2`.
   *Recommandés* : `python3-numpy`, `espeak-ng` (synthèse vocale).
2. **Les fichiers sont posés** dans `/usr/share/phytoscope/`, le lanceur dans
   `/usr/bin/phytoscope`, l'entrée de menu dans
   `/usr/share/applications/phytoscope.desktop`.
3. **`postinst` crée l'environnement virtuel** dans
   `/usr/share/phytoscope/venv`.
4. **Les bibliothèques Python sont installées** — depuis les roues embarquées
   si le paquet en porte (installation **hors ligne**), sinon depuis le
   réseau. Puis les facultatives : `python-rtmidi`, `pyttsx3`. Leur échec est
   sans conséquence, par construction.
5. **Le cache de bytecode est construit** (`compileall`) pour le logiciel et
   pour l'environnement.
6. **La base des entrées de menu est rafraîchie**.

### Si l'étape 3 ou 4 échoue

L'installation **n'est pas annulée** : le logiciel le dira au démarrage, avec
la commande à taper. Pour reprendre :

```bash
sudo dpkg-reconfigure phytoscope
phytoscope --check          # ce qui manque, et le remède exact
```

---

## Fedora · RHEL · Rocky · AlmaLinux — `.rpm`

**Fichier** : `phytoscope-1.5.1-1.noarch.rpm` (609 ko)

```bash
sudo dnf install ./phytoscope-1.5.1-1.noarch.rpm
```

### Ce qui se passe, dans l'ordre

1. **`dnf` installe les dépendances** : `python3` (≥ 3.9), `python3-pip`, et
   **11 bibliothèques système** — `mesa-libGL`, `mesa-libEGL`,
   `libxkbcommon-x11`, `xcb-util-cursor`, `xcb-util-wm`, `xcb-util-keysyms`,
   `xcb-util-image`, `xcb-util-renderutil`, `fontconfig`, `freetype`,
   `dbus-libs`.
   *Recommandés* : `portaudio`, `espeak-ng`, `python3-numpy`.
2. **Les fichiers vont** dans `/usr/share/phytoscope/`.
3. **`%post` crée l'environnement virtuel**, installe les bibliothèques
   (hors ligne si les roues sont là), puis **construit le cache de bytecode**.

> **Jusqu'à la 1.5.1, ce paquet ne déclarait aucune bibliothèque système.**
> L'installation paraissait réussie et le logiciel échouait au premier
> affichage. C'est corrigé.

---

## Toutes distributions — `.run`

**Fichier** : `PhytoScope-1.5.1-Linux.run` (28,4 Mo)

Pour Arch, openSUSE, Alpine, NixOS, Slackware — et pour **installer sans
aucun privilège**. C'est à la fois un script et une archive : le shell lit
l'en-tête, s'arrête, et tout ce qui suit est une archive compressée. Le
principe des `.run` de NVIDIA, et l'équivalent libre d'InstallShield.

```bash
chmod +x PhytoScope-1.5.1-Linux.run
./PhytoScope-1.5.1-Linux.run              # installation guidée
```

| Option | Effet |
|---|---|
| *(aucune)* | interface graphique s'il y a un bureau, sinon texte |
| `--gui` / `--tui` / `--texte` | imposer l'interface (zenity/kdialog · whiptail/dialog · lignes) |
| `-y`, `--yes` | ne rien demander — installation sans surveillance |
| `--prefix DOSSIER` | installer ailleurs |
| `--langue CODE` | imposer la langue (`fr en es pt it id ru zh ja ko ar`) au lieu de la demander |
| `--avec-dependances-systeme` | **installer aussi les bibliothèques système manquantes** (demande des privilèges) |
| `--desktop` / `--no-desktop` | poser l'icône sur le Bureau, ou non |
| `--launch` / `--no-launch` | lancer à la fin, ou non |
| `--check` | vérifier l'intégrité de l'archive, sans installer |
| `--extract DOSSIER` | décompresser sans installer |
| `--uninstall` | désinstaller |

### Ce qui se passe, dans l'ordre

1. **La langue est demandée** — première question, parce que toutes les
   suivantes seront posées dans la langue choisie. Les catalogues des onze
   langues voyagent dans l'archive, et seul celui retenu est chargé.
2. **L'empreinte SHA-256 de la charge est vérifiée** — avant d'écrire quoi
   que ce soit. `--check` fait cette étape seule.
3. **La licence est affichée**, extraite sans tout déplier, **dans la langue
   retenue**.
4. **Le dossier d'installation est choisi** : `~/.local/opt/phytoscope` pour
   un compte ordinaire, `/opt/phytoscope` si lancé par `root`.
5. **Un Python du système est cherché** — `/usr/bin/python3` et ses variantes
   versionnées, **Homebrew écarté**, et il doit savoir créer un environnement
   virtuel. Aucune erreur si rien ne convient : la suite y pourvoit.
5. **La charge est décompressée.**
6. **L'interpréteur est arbitré** : si aucun Python du système ne convenait,
   celui que l'archive transporte est retenu (`<prefixe>/python/bin/python3`).
   Sinon **le double est effacé**, pour ne pas garder 104 Mo inutiles.
7. **Les bibliothèques système sont contrôlées** — les onze que Qt et l'audio
   réclament. Si l'une manque :
   - sans `--avec-dependances-systeme` : elles sont **nommées précisément**,
     avec la commande exacte pour votre distribution ;
   - avec l'option : elles sont installées par votre gestionnaire de paquets.

   Elles ne s'installent pas dans le dossier personnel — `libGL` doit
   correspondre au pilote graphique de la machine.

   Les droits sont demandés par **`pkexec`, `kdesu` ou `gksu`** quand
   l'installateur a été lancé depuis un bureau — une fenêtre
   d'authentification est alors la seule chose correcte —, et par **`sudo`**
   en mode texte, où il y a un terminal sous les yeux. Si aucun n'est
   disponible, la commande exacte est affichée et l'installation continue.
8. **L'environnement virtuel est créé**, puis les bibliothèques Python
   installées (hors ligne si les roues sont embarquées), puis les
   facultatives.
9. **Le cache de bytecode est construit.**
10. **Le lanceur, l'entrée de menu et l'icône sont posés** dans
    `~/.local/bin`, `~/.local/share/applications`, `~/.local/share/icons`.
11. **Un registre est écrit** — c'est lui que `--uninstall` relit, plutôt que
    de deviner.
12. **Un désinstallateur** est déposé : `<prefixe>/desinstaller.sh`.

> Si `~/.local/bin` n'est pas dans votre `PATH`, l'installateur le dit et
> donne la ligne à ajouter à `~/.profile`.

---

## Windows 10 / 11 — `.exe`, `.msi`, archive portable

Les trois embarquent **l'interpréteur Python, Qt, NumPy et le logiciel**.
Rien à installer, rien à télécharger, aucun droit d'administrateur.

| Fichier | Taille | Pour qui |
|---|---|---|
| `PhytoScope-1.5.1-Windows.exe` | 178 Mo | l'installateur ordinaire (NSIS) |
| `PhytoScope-1.5.1.msi` | 276 Mo | déploiement par stratégie de groupe |
| `PhytoScope-1.5.1-Windows-portable.zip` | 267 Mo | clé USB, aucune installation |

> **SmartScreen vous avertira.** Le certificat de signature est
> **auto-signé** : il prouve l'intégrité et la continuité d'origine, il ne
> fait pas taire SmartScreen — et n'a jamais prétendu le faire. Cliquez sur
> « Informations complémentaires », puis « Exécuter quand même ». La
> signature se vérifie, elle, par l'empreinte : voir plus bas.

### `.exe` — ce qui se passe, dans l'ordre

1. **La langue est demandée** — boîte NSIS, avant toute page. Les onze
   langues sont compilées dans l'exécutable ; le choix est mémorisé sous
   `HKCU\Software\PhytoScope\Langue`, ce qui évite de reposer la question à
   la mise à jour suivante.
2. **La licence est affichée** et doit être acceptée.
3. **Le dossier est choisi** — par défaut `%LOCALAPPDATA%\Programs\PhytoScope`,
   qui ne demande aucun privilège.
4. **Les composants** : le logiciel (obligatoire) et l'icône du Bureau
   (facultative, une case à cocher).
5. **Les fichiers sont copiés** : `app\` le logiciel, `python\` l'interpréteur
   et les bibliothèques déjà dépliées.
6. **La base de registre est renseignée** — sous `HKCU`, jamais `HKLM` :
   « Applications et fonctionnalités » y trouve le nom, la version, l'éditeur
   et le désinstallateur.
7. **Les raccourcis sont créés** dans le menu Démarrer : *PhytoScope*,
   *Diagnostic*, *Désinstaller*.
8. **Le cache de bytecode est construit** — c'est le moment qui prend
   quelques secondes, et l'installateur le dit.
9. **La langue est écrite dans `reglages.json`**, pour que le logiciel la
   reprenne.

### `.msi` et archive portable

Ni l'un ni l'autre n'a d'étape d'installation où exécuter quoi que ce soit.
**Le lanceur `PhytoScope.cmd` construit donc le cache au premier
démarrage**, une seule fois, avec un témoin (`python\.bytecode-pret`). Si le
dossier est en lecture seule, le témoin ne s'écrit pas et l'on retentera : ce
n'est pas bloquant, le logiciel démarre seulement plus lentement.

Pour l'archive portable : décompressez où vous voulez, lancez
`PhytoScope.cmd`. `Diagnostic.cmd` ouvre une console et affiche le bilan
complet.

---

## macOS — `.pkg` et `.zip`

| Fichier | Taille |
|---|---|
| `PhytoScope-1.5.1.pkg` | 17,3 Mo |
| `PhytoScope-1.5.1-macOS.zip` | 18,7 Mo |

> **Gatekeeper vous avertira**, pour la même raison que SmartScreen : le
> certificat est auto-signé, et l'application n'est pas notariée par Apple.
> Faites un **clic droit → Ouvrir** à la première ouverture, ou
> *Réglages Système → Confidentialité et sécurité → Ouvrir quand même*.

### Ce qui se passe, dans l'ordre

1. **Le `.pkg` copie `PhytoScope.app`** dans `/Applications`. Le `.zip` se
   décompresse où vous voulez.
2. **À la première ouverture, la langue est demandée** — une liste, en
   onze langues, avant que l'environnement ne soit bâti. Le choix va dans
   `~/Library/Application Support/PhytoScope/reglages.json`.
3. **Au premier lancement**, le lanceur cherche un interpréteur, dans cet
   ordre : celui **embarqué** dans `Contents/Resources/python`, puis celui de
   **python.org** (installé en « framework »), puis celui **d'Apple**.
   **Homebrew est écarté.**
4. **L'environnement virtuel est créé** dans
   `~/Library/Application Support/PhytoScope/venv` — pas dans le paquet : un
   `.app` posé dans `/Applications` n'est pas inscriptible, et il doit
   pouvoir servir plusieurs comptes. Une fenêtre prévient que cela prend une
   à deux minutes, une seule fois.
5. **Les bibliothèques sont installées**, hors ligne si le paquet porte les
   roues.
6. **Le cache de bytecode est construit** dans l'environnement de
   l'utilisateur, et le cache des modules du paquet va à côté
   (`PYTHONPYCACHEPREFIX`), puisque le `.app` est en lecture seule.

### Une réserve, dite franchement

L'interpréteur embarqué est fourni **pour une seule architecture** — celle
choisie à la fabrication (`--arch x86_64` ou `--arch arm64`), par défaut celle
de la machine qui fabrique. Il n'existe pas de build « universal2 » de
l'interpréteur relogeable que nous utilisons. Un paquet fabriqué sur Intel
n'apportera donc pas d'interpréteur utilisable sur Apple Silicon : le lanceur
retombera sur python.org ou sur celui d'Apple, et le dira s'il n'en trouve
aucun.

---

## Depuis les sources

```bash
git clone https://github.com/thierryg/phytoscope.git
cd phytoscope/src/phytoscope

make install-dev      # environnement virtuel + outils de développement
make doctor           # ce qui est installé, ce qui manque
make test             # 266 tests, sans matériel ni réseau
make demo             # lancement avec une plante simulée
```

Les bibliothèques système, elles, restent à installer par votre gestionnaire
de paquets. `make system-deps` affiche la commande exacte pour votre
distribution.

Puis, pour lancer : `make run`, ou `./run.py`. Le second convient aussi — il
se relance de lui-même avec l'interpréteur de l'environnement si celui du
`PATH` ne convient pas.

---

## Vérifier ce que vous avez téléchargé

Chaque paquet publié est accompagné de trois choses.

### 1. L'empreinte — le fichier est-il intact ?

```bash
sha256sum -c SHA256SUMS.txt --ignore-missing
```

### 2. La provenance — d'où sort-il ? (le plus fort)

Chaque paquet publié porte une attestation Sigstore qui dit de quel dépôt,
quel commit et quel workflow il provient :

```bash
gh attestation verify phytoscope_1.5.1_all.deb --repo thierryg/phytoscope
```

### 3. La signature de l'éditeur

`AUTHENTICITE.txt`, livré avec les paquets, donne la marche à suivre. Les
`.exe` et `.msi` portent une signature Authenticode ; les autres une
signature CMS détachée (`.p7s`), vérifiable avec le certificat public
`phytoscope-certificat.pem`, lui aussi livré.

Pour tout revérifier d'un coup, depuis les sources :

```bash
cd packaging && make verifier
```

---

## Désinstaller

| Système | Commande |
|---|---|
| Debian, Ubuntu, Mint | `sudo apt remove phytoscope` |
| Fedora, RHEL | `sudo dnf remove phytoscope` |
| `.run` | `~/.local/opt/phytoscope/desinstaller.sh` — ou `./PhytoScope-*.run --uninstall` |
| Windows | « Applications et fonctionnalités », ou le raccourci *Désinstaller* |
| macOS | glissez `PhytoScope.app` vers la Corbeille |

Chacun retire l'environnement virtuel et le cache de bytecode, que ni `dpkg`
ni `rpm` ne connaissent — ils ont été produits après l'installation, et
survivraient sans cela.

**Vos réglages et vos séances sont conservés.** Pour les effacer aussi :

```bash
# Linux
rm -rf ~/.config/phytoscope ~/.local/share/phytoscope
# macOS
rm -rf ~/Library/Application\ Support/PhytoScope
# Windows
rmdir /s "%APPDATA%\PhytoScope"
```

---

## Quand ça ne démarre pas

La première chose à faire, toujours :

```bash
phytoscope --check          # ou : Diagnostic.cmd sous Windows
```

Il affiche la bannière, la **checklist** — système, interpréteur,
dépendances, carte, entrées et sorties audio, où vont les fichiers — puis les
**contrôles avant vol**, dépendance par dépendance, avec sa version. C'est ce
relevé qu'il faut joindre à tout signalement.

### Les deux cas les plus fréquents

**« *libGL.so.1* est bien installée mais l'interpréteur ne l'atteint pas »**
Vous exécutez PhytoScope avec un Python de Homebrew, Nix ou conda. **Il n'y a
aucun paquet à installer.** Lancez-le par l'environnement du projet
(`make run`), ou par un paquet d'installation. `./run.py` se relance
d'ailleurs tout seul dans ce cas.

**« *libGL.so.1* est introuvable »** — sans la première phrase. Là, elle
manque vraiment. Le bilan donne la commande exacte pour votre distribution ;
`make system-deps` aussi.

### L'interface refuse de se charger

Vous pouvez travailler sans elle, et enregistrer quand même :

```bash
phytoscope --headless --record
```

### Signaler

Une anomalie : un ticket, avec la sortie de `--check`
(`.github/ISSUE_TEMPLATE/anomalie.yml` vous guidera).
**Une faille de sécurité : pas de ticket public** — lisez
[`SECURITY.md`](SECURITY.md).
