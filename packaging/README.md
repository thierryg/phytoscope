# Empaquetage de PhytoScope

Tout se fabrique depuis **Debian, Ubuntu ou Mint**. Une cible par système, et
un Makefile pour les enchaîner.

```bash
cd packaging
make tools      # ce qui est installé, ce qui manque
make deps        # installe NSIS et msitools sans mot de passe
make all        # les cinq systèmes
make windows     # un seul
make verify    # rouvre et contrôle ce qui a été produit
```

Les paquets sortent dans `build/packages/`, avec un fichier `.sha256`
vérifiable par `sha256sum -c`.

---

## Ce qui est produit

| Système | Fichier | Ce qu'il faut déjà sur la machine |
|---|---|---|
| Debian, Ubuntu, Mint | `phytoscope_X.Y.Z_all.deb` | rien |
| Fedora, RHEL, Rocky, Alma | `phytoscope-X.Y.Z-1.noarch.rpm` | rien |
| **Toute distribution** | `PhytoScope-X.Y.Z-Linux.run` | Python 3.9+ |
| Windows 10 et 11 | `PhytoScope-X.Y.Z-Windows.exe` | **rien, pas même Python** |
| Windows, déploiement en parc | `PhytoScope-X.Y.Z.msi` | rien |
| Windows, sans installer | `…-Windows-portable.zip` | rien |
| macOS, glisser-déposer | `PhytoScope-X.Y.Z-macOS.zip` | Python 3.9+ |
| macOS, installateur | `PhytoScope-X.Y.Z.pkg` | Python 3.9+ |
| Tous systèmes | `phytoscope-X.Y.Z.tar.gz` | Python 3.9+ |

### L'installateur autonome `.run`

C'est l'équivalent libre de ce que produit InstallShield : un en-tête `sh`
suivi d'une archive compressée, dans un seul fichier exécutable — le principe
des `.run` de NVIDIA ou de VMware.

Il existe parce que le `.deb` et le `.rpm` ne couvrent pas tout : Arch,
openSUSE, Alpine, NixOS et Slackware n'ont ni l'un ni l'autre. Et surtout,
**il s'installe sans privilèges** : lancé par un compte ordinaire il se pose
dans `~/.local/opt` et n'appelle jamais `sudo`.

```bash
./PhytoScope-X.Y.Z-Linux.run                 installation guidée
./PhytoScope-X.Y.Z-Linux.run --prefix ~/opt  ailleurs
./PhytoScope-X.Y.Z-Linux.run --check         vérifier l'intégrité
./PhytoScope-X.Y.Z-Linux.run --extract /tmp  décompresser sans installer
./PhytoScope-X.Y.Z-Linux.run -y --no-desktop --no-launch   sans surveillance
```

Il porte l'empreinte SHA-256 de sa propre charge et la vérifie avant d'écrire
quoi que ce soit.

### Trois formes pour Windows, et pourquoi

**`.exe` (NSIS)** s'installe dans le profil de l'utilisateur
(`%LOCALAPPDATA%`) : **aucun privilège d'administration n'est demandé**, ce qui
compte en salle de classe et dans les ateliers où l'on n'a pas les droits.

**`.msi`** est le format que Windows comprend nativement, celui qu'un service
informatique déploie par stratégie de groupe ou par Intune, et qui s'installe
sans un clic :

```
msiexec /i PhytoScope-X.Y.Z.msi /qn
```

C'est ce que produisent les outils commerciaux du genre InstallShield — lequel
n'est pas utilisé ici : c'est un produit sous licence payante qui ne tourne que
sur Windows. Le MSI s'installe pour toute la machine et demande donc, lui, les
droits d'administration.

**`.zip` portable** ne s'installe pas du tout : on décompresse et on
double-clique. Pour une clé USB, ou un poste verrouillé.

### Deux formes pour macOS

**`.zip`** contient `PhytoScope.app`, qu'on glisse dans Applications — l'usage
le plus répandu, et le plus facile à défaire.

**`.pkg`** est l'installateur d'Apple : un assistant, l'application posée dans
`/Applications` pour tous les comptes, et l'installation sans interface par
`installer -pkg … -target /`.

---

## Ce que chaque installateur demande

Les trois mêmes choses, partout où c'est possible :

| | icône sur le Bureau | lancer à la fin | désinstallateur |
|---|---|---|---|
| `.run` | question (ou `--desktop`) | question (ou `--launch`) | `uninstall.sh` |
| `.exe` NSIS | case à cocher | case à cocher | « Applications et fonctionnalités » |
| `.msi` | fonctionnalité `IconeBureau` | — (déploiement sans interface) | `msiexec /x` |
| `.pkg` | fenêtre de l'assistant | fenêtre de l'assistant | `uninstall.sh` dans le `.app` |
| `.deb` `.rpm` | `phytoscope-desktop-icon` | — | `phytoscope-uninstall` |

**Pourquoi `.deb` et `.rpm` ne demandent rien.** `apt` et `dnf` installent sans
interaction, souvent sans session graphique, et parfois pour un autre compte
que celui qui s'en servira. Poser la question là serait la poser à la mauvaise
personne, au mauvais moment. Les deux paquets livrent donc
`phytoscope-desktop-icon`, que l'utilisateur appelle quand il le décide.

**Aucune désinstallation n'efface vos données.** Réglages et séances sont
conservés, et chaque désinstallateur dit où ils sont et comment les effacer si
on le veut vraiment. Une désinstallation n'est pas une demande d'oubli.


## Signature

```bash
make certificate            une seule fois — crée la clé et le certificat
make sign                signe la fabrication en cours
make certificate-fingerprint  l'empreinte SHA-256 à publier
```

Chaque paquet reçoit une signature **CMS détachée** (`.p7s`), et les
installateurs Windows en plus une signature **Authenticode**, celle que
Windows lit nativement. Le certificat public voyage avec les paquets, et
`AUTHENTICITE.txt` explique comment vérifier.

### Ce que la signature prouve, et ce qu'elle ne prouve pas

Elle prouve que le fichier n'a pas changé depuis sa signature et qu'il vient
de la même clé que les versions précédentes.

Elle **ne fait pas taire** l'avertissement de Windows ni celui de macOS : le
certificat est **auto-signé**. SmartScreen exige un certificat délivré par une
autorité reconnue — un produit commercial facturé chaque année ; Gatekeeper
exige un identifiant de développeur Apple, qui suppose un compte payant et un
Mac. Ni l'un ni l'autre ne se contourne par un certificat qu'on se délivre à
soi-même, et prétendre le contraire serait mentir à l'utilisateur.

Ce qu'elle apporte réellement : l'intégrité vérifiable par qui veut avec
`openssl` seul ; un déploiement en parc sans avertissement, pour qui installe
le certificat dans le magasin « Éditeurs approuvés » de ses machines ; et une
empreinte publiable que chacun peut comparer.

### Où vivent les clés

La clé de référence est dans `~/.local/share/phytoscope-signature/`, en 0600,
**hors du dépôt**. Une copie de travail vit dans `certificate/`, où
`.gitignore` écarte la clé privée — mais `.gitignore` protège de Git, pas
d'une sauvegarde ni d'une archive du dossier. Voir `certificate/README.md`.


## Organisation du dossier

```
packaging/
  Makefile                 enchaîne les cibles — « make all », « make macos »
  build.py            aiguillage : appelle les générateurs dans l'ordre
  common.py                ce qui ne dépend d'aucun système
  verify.py              rouvre les paquets produits et les contrôle
  macos_pkg.py             le format .pkg, écrit de bout en bout

  signature.py             certificat X.509, signatures CMS et Authenticode

  build_debian.py     .deb et l'installateur autonome .run
  build_fedora.py     .rpm
  build_windows.py    .zip portable, .exe (NSIS), .msi (wixl)
  build_macos.py      .zip du .app, .pkg
  build_source.py     .tar.gz

  gabarits/
    debian/    control, postinst, prerm, lanceur, .desktop
    fedora/    phytoscope.spec
    linux/     header.sh — l'en-tête du .run
    windows/   phytoscope.nsi, phytoscope.wxs, PhytoScope.cmd, Diagnostic.cmd
    macos/     Info.plist, lanceur, postinstall
```

Chaque générateur est **autonome** : il se lance seul (`python3
packaging/build_windows.py --msi`) et ne dépend que de `common.py`. Une
panne sur l'un n'emporte pas les autres.

---

## La version et l'attribution

Deux fichiers, dans le paquet Python, et nulle part ailleurs :
**`phytoscope/VERSION`** et **`phytoscope/AUTHORS`**.

```
version = 1.5.1
nom =
date = 2026-09-18
suffixe =
```

```
editeur = Bretagne Namasté
auteur = Thierry GAYET
courriel = Thierry.Gayet@gmail.com
telephone = +33 (0)6 63 84 95 89
```

Le logiciel les lit au démarrage pour « À propos », la fabrique pour
estampiller chaque paquet, `signature.py` pour remplir le sujet du certificat,
`pyproject.toml` pour la roue Python, et `tools/release.py` est le seul à
écrire la version. Ils sont **dans le paquet Python** et non à la racine du
dépôt, pour une raison simple : un logiciel installé n'emporte pas le dépôt.
Placés là, ils le suivent partout, et ce qui s'affiche est forcément ce qui
tourne.

---

## Pourquoi tout se construit depuis Linux

Trois mécanismes le permettent :

**`pip download --platform` télécharge les roues d'un autre système.** On
récupère donc depuis Debian les paquets Windows et macOS de NumPy, de Qt et du
reste, sans jamais démarrer ces systèmes. C'est ce qui rend les paquets
installables hors ligne.

**Python publie pour Windows une distribution « embarquable »** : une archive
contenant l'interpréteur complet, sans installateur ni base de registre. On la
place dans le paquet, et le logiciel n'exige alors rien de la machine Windows.
C'est pour cela que les paquets Windows pèsent entre 180 et 270 Mo : ils
contiennent Python, Qt, NumPy et le logiciel.

**Les outils existent sous Linux.** `makensis` (paquet `nsis`) produit le
`.exe`, `wixl` (paquet `wixl`, de msitools) produit le `.msi`. Tous deux
s'installent dans `~/.local/opt` par `make deps`, sans `sudo` — comme le SDK
du micrologiciel (`C-55`).

### Le `.pkg` de macOS est écrit de bout en bout

Apple fournit `pkgbuild`, qui n'existe que sur macOS. Les deux outils libres
qui le remplacent — `xar` et `mkbom` — ne sont plus empaquetés par Debian.
`macos_pkg.py` écrit donc les trois formats imbriqués lui-même, en Python pur :

* **XAR**, l'archive : en-tête, table des matières XML compressée, tas, et une
  somme SHA-1 par membre ;
* **cpio** au format « odc » : en-têtes en octal ASCII, déterministe ;
* **BOM**, la nomenclature binaire : un arbre listant chaque chemin avec son
  mode, sa taille et sa somme CRC. C'est l'absence de ce fichier qui fait
  échouer un paquet autrement correct.

Tout ce qui est écrit est **relu et recontrôlé** : la table XAR est
réextraite, le cpio redéplié, l'arbre du BOM reparcouru, et l'on vérifie que
les trois décrivent le même ensemble de fichiers. Une charge utile et une
nomenclature qui divergent sont la panne classique du paquet fabriqué à la
main — l'installateur copie, puis refuse.

### macOS n'embarque pas l'interpréteur

Apple ne fournit plus de Python utilisable depuis macOS 12.3, et un CPython
redistribué depuis Linux serait non signé : Gatekeeper le refuserait, ce qui
donnerait une application qui ne s'ouvre pas — le pire des résultats, puisque
l'utilisateur n'en saurait pas la raison. Le paquet utilise donc le Python de
l'utilisateur et affiche une vraie fenêtre d'explication s'il manque.

---

## Ce que la fabrique ne fait pas

**Elle ne signe rien.** Une signature Windows exige un certificat payant ; une
signature macOS exige un compte développeur Apple **et** un Mac. Les deux
systèmes afficheront donc un avertissement à la première ouverture :

* **Windows** — « Windows a protégé votre ordinateur » : « Informations
  complémentaires », puis « Exécuter quand même ».
* **macOS** — clic droit sur l'icône, « Ouvrir », puis confirmer. Une seule
  fois suffit. En dernier recours :
  `xattr -dr com.apple.quarantine /Applications/PhytoScope.app`

Le `LISEZ-MOI.txt` de chaque paquet l'explique à l'utilisateur. C'est honnête,
et cela vaut mieux qu'un faux sentiment de sécurité.

**Elle n'installe rien pour vérifier.** `make verify` rouvre chaque paquet et
contrôle sa structure — métadonnées, contenu, cohérence interne, droits
d'exécution, empreintes. Mais **aucun paquet n'a été installé** : il n'y a sur
cette machine ni Windows, ni macOS, ni Fedora. Le script le dit à chaque
exécution plutôt que de le laisser croire.

---

## Ce que font les paquets Linux à l'installation

Ils posent le logiciel dans `/usr/share/phytoscope`, un lanceur dans
`/usr/bin/phytoscope`, une entrée de menu et une icône. Puis leur script
d'après-installation crée un **environnement Python privé** dans
`/usr/share/phytoscope/venv`.

Pourquoi un environnement privé plutôt que les paquets de la distribution :
PySide6 n'est pas empaqueté par toutes les versions de Debian, d'Ubuntu ni de
Fedora, et sa version y va de 6.2 à 6.7 selon les dépôts. Un environnement
dédié garantit la même chose partout **sans toucher au Python du système**, et
sans risquer de casser un autre logiciel installé.

Par défaut le paquet est **léger** (340 ko) et l'installation va chercher les
bibliothèques — c'est le cas courant, puisqu'on installe un `.deb` par `apt`,
donc en ligne. Avec `make offline`, elles sont **embarquées** et le paquet
passe à 335 Mo : ce qu'il faut pour un atelier sans réseau, où trente machines
s'installent depuis une clé USB. Le paquet couvre alors Python 3.9 à 3.13 —
une roue de NumPy ne valant que pour une version mineure — et son nom porte la
marque `-horsligne`, pour qu'on ne diffuse pas l'un en croyant diffuser
l'autre.

À la désinstallation, l'environnement est effacé : ni `dpkg` ni `rpm` ne le
connaissent, puisqu'il est créé après coup. Les **réglages et les séances de
l'utilisateur ne sont jamais touchés** — une désinstallation n'est pas une
demande d'oubli.

---

## Les cibles du Makefile

| Cible | Effet |
|---|---|
| `make tools` | dit ce qui est installé et ce qui manque |
| `make deps` | installe NSIS et msitools dans `~/.local/opt`, sans `sudo` |
| `make debian` `fedora` `windows` `macos` `source` | un système |
| `make linux` | `.deb` et `.rpm` |
| `make all` | les cinq, du plus rapide au plus long |
| `make offline` | les paquets qui embarquent leurs bibliothèques |
| `make verify` | rouvre et contrôle ce qui a été produit |
| `make checksums` | recalcule le fichier `.sha256` |
| `make clean` | vide `build/packages` |
| `make version` | affiche le numéro de version |

Chaque générateur accepte en outre ses propres options :

```bash
python3 build_windows.py --msi         # seulement le MSI
python3 build_macos.py   --pkg         # seulement l'installateur
python3 build_debian.py  --offline  # avec les bibliothèques
```

---

## Vérifier un paquet à la main

```bash
dpkg-deb -I build/packages/phytoscope_*.deb        # métadonnées Debian
rpm -qip  build/packages/phytoscope-*.rpm          # métadonnées Red Hat
msiinfo tables build/packages/PhytoScope-*.msi     # tables du MSI
unzip -l build/packages/PhytoScope-*.zip | head
cd build/packages && sha256sum -c phytoscope-*.sha256
```

---

## Ce qu'il faut sur la machine qui empaquette

| Outil | Paquet Debian | Sert à |
|---|---|---|
| `dpkg-deb` | `dpkg-dev` | le `.deb` |
| `rpmbuild` | `rpm` | le `.rpm` |
| `makensis` | `nsis` — ou `make deps` | l'installateur `.exe` |
| `wixl` | `wixl` — ou `make deps` | le paquet `.msi` |
| `zip` | `zip` | les archives |
| une connexion | — | les roues et Python embarquable |

```bash
sudo apt install dpkg-dev rpm zip
make deps                      # NSIS et msitools, sans mot de passe
```

Le `.pkg` de macOS ne demande **rien** : il est écrit en Python pur.

---

*Bretagne Namasté — https://bretagne-namaste.com — licence MIT*
