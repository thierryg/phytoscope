# Journal des modifications — projet *La Musique des Plantes*

Ce fichier suit **le projet entier** : l'ouvrage, le hors-série, la carte, le
micrologiciel et le logiciel. Le détail des versions du logiciel vit dans
`src/phytoscope/CHANGELOG.txt`, qui est plus fin ; celui-ci donne la vue
d'ensemble.

Format « Keep a Changelog ». Les dates sont celles de la construction des
documents, vérifiées après reconstruction (`C-64`).

---

## 2026-09-18 (nuit) — mises à jour des bibliothèques, et la langue en onze voix

### Ajouté
- **« Aide → Mises à jour des bibliothèques… »** — le logiciel compare les
  bibliothèques Python installées à ce que publie l'index des paquets, classe
  les écarts en *correctif*, *mineure*, *majeure*, et **n'installe rien sans
  demande explicite**. L'interrogation se fait dans un fil séparé et la sortie
  de `pip` défile ligne à ligne. Aucune dépendance ajoutée pour cela (`C-40`).
- **La langue est demandée au tout début de l'installation**, dans les **onze
  langues du logiciel**, chacune proposée dans sa propre écriture. Elle est
  écrite dans `reglages.json` et reprise par PhytoScope : la question ne
  revient jamais.
  - `.run` : première question, avant la licence — qui est donc lue dans la
    langue retenue. `--langue ja` pour une installation sans surveillance ;
  - `.exe` : boîte NSIS, **onze langues compilées** au lieu de deux, choix
    mémorisé sous `HKCU` ;
  - `.pkg` macOS : liste à la première ouverture ;
  - `.deb` et `.rpm` : `apt` et `dnf` n'interrogent pas — la question se pose
    au **premier démarrage du logiciel**.
- **51 libellés d'installateur × 11 langues = 561 traductions**, dans une
  source unique (`packaging/langues/installateur.json`), d'où sont générés les
  catalogues shell du `.run` et les `LangString` de NSIS.
- **Élévation de droits par `pkexec`, `kdesu` ou `gksu`** quand l'installateur
  vient d'un bureau — une fenêtre d'authentification est la seule chose
  correcte alors —, par `sudo` en mode texte.
- **Bannière ASCII** et **checklist** affichées au lancement par défaut, avec
  les contrôles avant vol dépendance par dépendance.
- `INSTALL.md` — ce que fait chaque installateur, étape par étape, par système.
- Régénération automatique de la **nomenclature logicielle** dès qu'une
  modification touche `src/phytoscope/` (`.github/workflows/sbom.yml`).

### Corrigé
- **Une pré-diffusion passait pour plus récente que sa version.** Dans le
  comparateur neuf : ramasser tous les nombres de « 3.0.0rc1 » donne
  `(3, 0, 0, 1)`, qui se compare après `(3, 0, 0)`. L'ordre couvre désormais
  `dev < alpha < beta < rc < (rien) < post`.
- **Deux tests ne vérifiaient plus rien depuis le rangement du dépôt.**
  `test_le_sdk_livre_un_exemple_qui_se_charge` et
  `test_les_identifiants_usb_suivent_le_micrologiciel` cherchaient le SDK et
  le micrologiciel à leurs anciens emplacements, et **s'ignoraient
  silencieusement**. Chemins corrigés ; ils passent.
- La **bannière existait en double** dans `__main__.py`, et son premier trait
  avait perdu un caractère. Une seule source désormais,
  `core/console.banniere()`, qui porte aussi la version.
- « bilan de démarrage » devient « **checklist** », partout.

### Changé
- **`ruff` dans l'intégration continue** : bloquant sur les plantages (`E9`,
  `F82x`, `F811`), informatif sur les mille avertissements de style hérités
  d'un code écrit pour Python 3.9. L'intention est déclarée dans
  `pyproject.toml`, avec son pourquoi. La configuration précédente aurait fait
  échouer la chaîne au premier envoi.

### Vérifié
- **306 tests au vert, 0 ignoré** ; `ruff` essentiel : *All checks passed* ;
- **11 langues à 100 %** (888 libellés) et 561 traductions d'installateur,
  champs de substitution préservés ;
- `.run --langue ja` affiche `[ok] 言語：日本語` — le catalogue japonais est
  bien chargé.

---

## 2026-09-18 (fin de journée) — la série « L'Arbre qui Parle », et un dépôt public

### Ajouté
- **La série « L'Arbre qui Parle »**, fusionnée dans le projet : trois volumes
  et une annexe technique, **638 pages**, construits par
  `pdf-src/build_arbre.py` et `pdf-src/build_annexe.py` depuis leur propre
  charte `pdf-src/arbre.css`.
  - *Dublin — analyse scientifique* (212 p.) — l'enquête sur les « arbres
    parlants » ;
  - *Biocommunication végétale et intelligence artificielle* (163 p.) — le
    traité ;
  - *Créer un arbre parlant* (198 p.) — le manuel d'atelier ;
  - *Annexe — planches, nomenclature, programmes* (65 p.).
- **234 photographies et planches**, avec leurs crédits
  (`pdf-src/assets/img/photos/CREDITS.md`), et 44 illustrations nouvelles.
- **Quatre notes de recherche sourcées** (`sources/01-…` à `04-…`).
- `tools/verifier_svg.py` — contrôle que les 104 illustrations sont du XML
  bien formé. Une illustration mal formée ne casse pas la fabrication :
  WeasyPrint la laisse tomber et compose un cadre vide, sans rien signaler.
- `tools/pdf_impactes.py` — dit quelles publications refaire au vu des
  fichiers modifiés. Refaire les dix coûte une douzaine de minutes.
- **Un dépôt git public** : `LICENSE` (MIT) et `LICENSES/CERN-OHL-P-2.0.txt`
  aux textes officiels SPDX, `SECURITY.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `AUTHORS`, `.editorconfig`, `.gitattributes`,
  `.pre-commit-config.yaml`, gabarits de tickets, `CODEOWNERS`.
- **Six workflows d'intégration continue** : analyse statique puis
  fabrication des paquets par système (`paquets.yml`), reconstruction des
  seules publications touchées (`publications.yml`), sept contrôles de
  sécurité (`securite.yml`), CodeQL sur Python **et** C, OpenSSF Scorecard,
  et une chaîne de diffusion qui **atteste la provenance** des paquets
  (Sigstore) après avoir vérifié que l'étiquette correspond à `VERSION`.

### Corrigé
- **Les illustrations n'échappaient pas le texte qu'on leur donnait.**
  `pdf-src/assets/svg/gen.py` avait perdu sa fonction `esc()` : `timeline.svg`
  contenait deux `&` nus et était le **seul SVG mal formé sur 104**. Le
  cadre correspondant était vide dans l'ouvrage, sans que rien ne l'indique.
- **Fausse déclaration de licence sur 32 fichiers tiers.** `tools/entetes.py`
  avait apposé « © Bretagne Namasté » et « SPDX-License-Identifier: MIT » sur
  LEDFader (MIT © Jeremy Gillick), MIDI Sprout (MIT © electricityforprogress)
  et le micrologiciel **Biotron, qui est en GPL-3.0**. En-têtes retirés,
  en-têtes d'origine intacts, `sources/` exclu de l'outil, et un job de CI
  refuse désormais que cela revienne. L'annexe de codes annonçait aussi
  Biotron en « MIT » : corrigé en GPL-3.0.
- **Le `.deb` avait disparu de la fabrication.** L'en-tête d'attribution
  s'était posé sur `packaging/gabarits/debian/control`, et **un fichier
  `control` n'admet aucun commentaire** : `dpkg-deb` refusait le paquet, mais
  `make tout` continuait et produisait les sept autres. `"control"` est
  entré dans les exclusions de `tools/entetes.py`.
- Les chiffres de `sources/INDEX.md` étaient périmés (76 fichiers annoncés,
  248 réels) : remesurés.

### Changé
- **Le dépôt est rangé selon ce que les fichiers sont, non selon leur
  ancienneté.** Le code sous `src/` (`phytoscope/`, `firmware/`, `sdk/`), les
  sources d'édition sous `pdf-src/` avec **un dossier par publication**, et
  `sources/` réservé à la matière de référence — ce que nous n'avons pas
  écrit. `hardware/` a quitté `sources/` : c'est notre matériel, sous
  CERN-OHL-P v2.
- `.gitignore` réécrit — **459 lignes commentées**, couvrant bash, Python, Go,
  Rust, C/C++, Windows 10/11, macOS/Darwin, Debian/Ubuntu/Mint et
  Fedora/RHEL, organisées en trois familles : les secrets, ce que nous
  n'avons pas le droit de rediffuser, ce qui se reconstruit.
- Les numérisations du domaine public (Bose, Darwin — 258 Mo) sortent du
  dépôt : elles sont libres de droits, mais un clone de 415 Mo pour des
  livres retéléchargeables en une commande n'a pas de sens. Les
  **transcriptions** restent versionnées, et
  `sources/documents/domaine-public/LISEZ-MOI.md` donne les commandes.

### Vérifié
- **1 378 pages sur 10 publications**, inchangées après restructuration
  (0 écart sur les dix décomptes) ;
- **260 tests** au vert ; **104 illustrations**, 0 mal formée ;
  **260 en-têtes** à jour ;
- `make tout` : **8 paquets signés**, 0 échec ; `make verifier` : empreintes
  SHA-256 conformes ;
- `git ls-files` : seul le certificat **public** est suivi ; la clé privée est
  écartée.

---

## 2026-09-18 (soir) — installateurs, signature et attribution

### Ajouté
- **Installateur autonome Linux** `PhytoScope-X.Y.Z-Linux.run` — un script et
  une archive dans un seul fichier, à la manière des `.run` de NVIDIA, et
  l'équivalent libre de ce que produit InstallShield. Il couvre les
  distributions sans `.deb` ni `.rpm` (Arch, openSUSE, Alpine, NixOS) et
  **s'installe sans privilèges**. Trois interfaces : graphique (zenity,
  kdialog), boîtes en mode texte (`--tui`), lignes brutes (`--texte`). Avec
  `--uninstall`, `--check`, `--extract` et un registre d'installation.
- **Installateur macOS `.pkg`** — écrit de bout en bout en Python pur
  (`macos_pkg.py`) : archive XAR, charge cpio « odc », nomenclature BOM. Ni
  `pkgbuild`, ni `xar`, ni `mkbom` ne sont nécessaires. Tout ce qui est écrit
  est relu et recontrôlé.
- **Paquet Windows `.msi`** par `wixl` — le format que déploient les stratégies
  de groupe et Intune, avec des identifiants de composants déterministes pour
  que la mise à jour d'un parc se passe bien. Ce n'est pas InstallShield, qui
  est un produit commercial ne tournant que sur Windows ; c'est ce
  qu'InstallShield *produit*.
- **Signature de tous les paquets** : certificat X.509 de signature de code,
  Authenticode pour `.exe` et `.msi`, CMS détachée (`.p7s`) pour le reste.
  Le certificat étant **auto-signé**, chaque paquet dit ce que la signature
  prouve — intégrité, continuité d'origine — et ce qu'elle ne prouve pas :
  elle ne fait taire ni SmartScreen ni Gatekeeper.
- **Chaque installateur demande** l'icône sur le Bureau et le lancement en fin
  d'installation, et **fournit un désinstallateur**. Aucune désinstallation
  n'efface réglages ni séances.
- `phytoscope/AUTEURS` — l'attribution en un seul fichier, lue par le logiciel,
  par la fabrique de paquets et par le sujet du certificat. Éditeur
  (Bretagne Namasté) et auteur (Thierry GAYET) y sont distingués.
- `manuel.txt` par système, en plus de readme, install, licence et changelog.

### Vérifié
- **Sous Wine 6.0.3** : l'interpréteur Python 3.11.9 embarqué démarre, PySide6,
  pyserial et sounddevice s'importent, `run.py --version` s'exécute
  correctement. NumPy échoue faute de `fetestexcept` dans le runtime MSVC de
  Wine — lacune de Wine, pas du paquet. L'installateur NSIS, étant 32 bits,
  n'a pas pu être essayé : cette machine n'a que Wine 64 bits.
- Le `.run` : installation, registre et `--uninstall` éprouvés de bout en bout.
- 225 essais au vert, 832 libellés à 100 % dans les onze langues.

---

## 2026-09-18 (nuit) — les paquets d'installation

### Ajouté
- **`packaging/`** — une fabrique de paquets, lancée depuis Debian, Ubuntu ou
  Mint, qui produit les cinq cibles d'une seule commande :

  | Cible | Fichier | Exige sur la machine qui reçoit |
  |---|---|---|
  | Debian, Ubuntu, Mint | `.deb` | rien |
  | Fedora, RHEL, Rocky, Alma | `.rpm` | rien |
  | Windows 10 et 11 | `.exe` (NSIS) + `.zip` portable | **rien, pas même Python** |
  | macOS Intel + Apple Silicon | `.zip` contenant `PhytoScope.app` | Python 3.9+ |
  | Tous systèmes | `.tar.gz` source | Python 3.9+ |

- **L'installateur Windows n'exige rien.** Il embarque l'interpréteur Python
  (distribution « embarquable » officielle), Qt, NumPy et le logiciel :
  177 Mo, un double-clic, des raccourcis, une entrée dans « Applications et
  fonctionnalités » et un désinstallateur. Il est fabriqué depuis Linux, NSIS
  existant aussi pour ce système.
- **Les paquets Linux créent un environnement Python privé** dans
  `/usr/share/phytoscope/venv` plutôt que de dépendre de `python3-pyside6`,
  qui n'existe pas dans toutes les versions de Debian, d'Ubuntu ni de Fedora.
  Avec `--hors-ligne`, ils embarquent les bibliothèques pour Python 3.9 à 3.13
  et s'installent sans réseau — ce qu'il faut pour un atelier ou une salle de
  classe.
- **`build.py --deps` installe NSIS sans `sudo`**, dans `~/.local/opt`,
  comme `build.sh --deps` le fait pour le SDK du micrologiciel.
- Empreintes SHA-256 de chaque paquet, vérifiables par `sha256sum -c`.

### Assumé
- **Rien n'est signé** : une signature Windows exige un certificat payant, une
  signature Apple un compte développeur et un Mac. Les deux systèmes
  avertiront à la première ouverture ; le `LISEZ-MOI.txt` de chaque paquet
  explique comment passer outre. Mieux vaut le dire que laisser croire à une
  garantie qui n'existe pas.
- **Aucun de ces paquets n'a été essayé sur une vraie machine Windows ni sur
  un Mac.** Leur structure est vérifiée (`dpkg-deb`, `rpm -qip`, contenu des
  archives, type de l'exécutable) ; leur exécution ne l'est pas.

---

## 2026-09-18 (nuit) — portabilité

### Corrigé
- **Logiciel 1.5.1** — revue complète Windows 10/11,
  macOS (Intel et Apple Silicon) et GNU/Linux (Debian, Ubuntu, Mint, Fedora,
  Red Hat) : treize points relevés, treize corrigés.
- **La carte n'était jamais reconnue par ses identifiants USB** : le logiciel
  cherchait `0x2E8A:0x10F5`, le micrologiciel déclare `0x1209:0x7A01`. Le
  micrologiciel avait raison — `0x1209` est la plage libre de pid.codes,
  `0x2E8A` appartient à Raspberry Pi. Sous Windows, le lien de contrôle était
  inutilisable. Un essai lit désormais `usb_descriptors.c` et compare.
- **L'entrée audio refusait de s'ouvrir sur Mac et sous Windows** (250 Hz
  demandés à CoreAudio et WASAPI) : repli sur le débit natif du périphérique
  et décimation logicielle, sans perdre un échantillon.
- **Une dépendance facultative faisait échouer toute l'installation** :
  `requirements-optionnel.txt` est désormais installé à part.
- **Les polices** étaient nommées en dur à vingt et un endroits, sans repli :
  `ui/polices.py` déclare une pile et le genre de la police, et corrige la
  taille sur macOS (72 ppp contre 96).
- Périphérique audio résolu par interface hôte sous Windows ; raccourcis
  affichés comme macOS les présente (⌘) ; port MIDI virtuel expliqué ; voix
  de synthèse filtrée par moteur ; moteur SAPI créé dans son propre fil ;
  redémarrage reconstruit ; rotation du journal tolérante ; noms de fichiers
  translittérés en ASCII (NFD d'APFS, noms réservés de Windows).
- **Micrologiciel** : `build.sh --deps` détecte l'architecture — il échouait
  sur Apple Silicon et sur Raspberry Pi — et cherche le point de montage de
  la carte au lieu de le supposer.
- **Fabrication des PDF** : le compte de pages ne dépend plus de `pdfinfo` ;
  les prérequis Pango / HarfBuzz / fontconfig sont déclarés.

### Ajouté
- `tests/test_portabilite.py` : vingt-trois essais qui vérifient sous Linux ce
  qui ne se voit qu'ailleurs. **221 essais au vert.**

---

## 2026-09-18 (fin de journée)

### Ajouté
- **Logiciel 1.5.0 « Ce que dit le bruit »** — quinze grandeurs scientifiques
  dans le Multimètre, au premier rang desquelles la **résistance équivalente**
  déduite du bruit thermique de Johnson-Nyquist (`R = Sᵥ / 4kT`), annoncée pour
  ce qu'elle est : un **majorant**, pas une mesure à l'ohmmètre. Avec elle :
  densité de bruit en nV/√Hz, bruit intégré dans 0,01–10 Hz, résidu de réseau,
  facteur de crête, pente spectrale, écart d'Allan à 1 s et 10 s, intégration
  optimale, temps de corrélation, normalité, résolution effective, marge de
  saturation, taux d'événements et facteur de Fano.
- **Fenêtre du journal (`Ctrl+L`)** : le fichier en direct, son emplacement en
  toutes lettres, et « Enregistrer une copie… » vers l'endroit de son choix,
  archives de rotation comprises. Lecture incrémentale, filtre par texte,
  niveau réglable à chaud.

### Modifié
- Les grandeurs sont calculées sur le signal **brut** : filtrer avant de
  mesurer le bruit reviendrait à mesurer son propre filtre.
- 826 libellés traduisibles (contre 755), 100 % dans les dix langues.
- Les essais ne peuvent plus toucher la configuration de l'utilisateur
  (`tests/conftest.py` détourne XDG_CONFIG_HOME et APPDATA).

---

## 2026-09-18 (nuit)

### Ajouté
- **Logiciel 1.4.0 « Le cadran et l'empreinte »** — quatre vumètres à
  balistique dans le Multimètre, empreinte de mesure du montage avec registre
  des montages connus, barre de menus (Séance / Affichage / Aide).
- Hors-série : planche **« Brancher une feuille et une racine »**, section sur
  le choix de l'électrode de substrat, section sur l'empreinte de mesure et sa
  limite (192 → 198 pages).

### Corrigé
- **L'aide et « À propos » étaient devenus inaccessibles** : la barre d'outils
  avait débordé et Qt les avait escamotées. Elles vivent dans la barre de menus.
- Le conseil d'électrode de substrat — une tige de laiton — était mauvais :
  pile galvanique et cuivre toxique pour les racines. C'est désormais inox
  316L, graphite ou pont salin Ag/AgCl.

---

## 2026-09-18 (soir)

### Ajouté
- **Logiciel 1.3.0 « Le carnet de croquis »** — capture rapide d'échantillons
  (`Ctrl+E`), relecture des séances et des échantillons **dans le moteur**,
  surveillance de l'espace disque avec clôture propre avant saturation,
  sélecteur de langue dans la barre d'outils, retour au zoom d'origine
  (`Ctrl+0`), onze dictionnaires du mode vocal.
- **Micrologiciel** : `build.sh` installe le Pico SDK et la chaîne ARM dans le
  dossier personnel — sans privilège administrateur — et produit
  `phytosense.uf2` (RP2350, 80 Ko).
- **Mémoire du projet** : `AGENTS.md`, `constraints.md` (64 contraintes
  numérotées), `.ai/journal.md`, `.ai/decisions.md`, `.ai/etat.md`.
- Hors-série : chapitres sur les échantillons, l'espace disque et les langues
  (190 → 192 pages).

### Modifié
- Le mode vocal **coupe la musique** tant qu'il est actif, et affiche un voyant
  permanent : le silence d'un mode qui parle rarement ne doit pas passer pour
  une panne.
- La **fenêtre se réduit** de nouveau : hauteur minimale de 1094 à 520 pixels.

### Corrigé
- La relecture rouvrait la sortie audio déjà ouverte — deux fils écrivaient
  dans le même flux PortAudio.
- Deux en-têtes manquaient dans `afe.c` : le micrologiciel ne compilait plus.

---

## 2026-09-18 (matin)

### Ajouté
- **Logiciel 1.2.0 « Onze langues »** — interface traduite en français (source),
  anglais américain, espagnol, portugais, italien, indonésien, russe, chinois,
  japonais, coréen et arabe ; écriture de droite à gauche pour l'arabe ;
  ajout d'une langue par simple dépôt d'un fichier JSON.
- **Onze dictionnaires du mode vocal**, un par langue, avec gabarits de phrase
  propres aux langues dont l'ordre des mots diffère du français.
- **Surveillance de l'espace disque** pendant l'enregistrement : alerte à vingt
  minutes d'autonomie, clôture propre de la séance avant saturation.
- **`build.sh` du micrologiciel** : installe Pico SDK et chaîne ARM dans le
  dossier personnel, sans privilège administrateur, puis construit
  `phytosense.uf2`.
- **Mémoire des agents** : `AGENTS.md`, `constraints.md`, `.ai/journal.md`,
  `.ai/decisions.md`, `.ai/etat.md`.

### Modifié
- Le mode vocal **coupe la musique** tant qu'il est actif, et affiche en
  permanence son état et son dernier énoncé.
- Le micrologiciel compile de nouveau : deux en-têtes manquaient dans `afe.c`.

### Corrigé
- Une option de ligne de commande (`--lang`, `--simulation`, `--theme`…) ne
  s'inscrit plus dans le fichier de réglages : elle vaut pour la séance.

---

## 2026-09-17

### Ajouté
- **Logiciel 1.1.0 « Les mots et les ondes »** — onglet *Descripteurs* (forme
  d'onde, FFT, ondelettes de Morlet, MFCC, prédiction linéaire, cepstre) et
  onglet *Parole* (mode vocal, dictionnaire, synthèse hors ligne).
- **Ctrl+C interrompt le logiciel**, interface graphique comprise, avec chien
  de garde et prise en charge de SIGTERM.
- Page d'aide des raccourcis **vérifiée par le programme** à chaque ouverture.
- Hors-série : chapitres « Six regards sur le même signal » et « Des mots au
  lieu des notes », deux planches originales (176 → 186 pages).

### Corrigé
- Un changement de réglage ne vide plus la mémoire de signal : la chaîne n'est
  reconstruite que si l'un de ses propres réglages change.

---

## 2026-09-15 → 2026-09-17

### Ajouté
- **L'ouvrage** *La Musique des Plantes* — 478 pages, 10 parties, 40 chapitres,
  5 annexes, 28 illustrations vectorielles, 21 planches de brevets traduites.
- **Le hors-série** *La Carte PhytoSense* et ses trois fascicules détachables.
- **La carte PhytoSense One** : schémas, routage quatre couches, nomenclature
  chiffrée, gabarits de face avant et arrière.
- **Le micrologiciel RP2350** : ADS131M04 en SPI/DMA, USB en classe audio 2.0.
- **Le logiciel PhytoScope 1.0.0 « Première sève »** : quatre sources, quatre
  instruments, sonification documentée, bibliothèque, diagnostic, mode sans
  interface, 56 tests.
