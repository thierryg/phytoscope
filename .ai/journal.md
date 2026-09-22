# Journal des interventions

Une entrée par intervention notable, la plus récente en **bas** — on lit ce
fichier comme on lit une histoire, du début. Chaque entrée dit **ce qui a été
fait**, **pourquoi**, et **ce qu'il en reste à vérifier**.

Format : `## AAAA-MM-JJ — titre` puis, au besoin, `**Agent :**`, `**Fait :**`,
`**Pourquoi :**`, `**Vérifié :**`, `**Attention :**`.

---

## 2026-09-15 → 2026-09-17 — L'ouvrage, le hors-série et la première version du logiciel

**Agent :** Claude Code (sessions antérieures) · **Sources :** `CHANGELOG.txt`
du logiciel, horodatage des fichiers, contenu du dépôt.

**Fait :**
- L'ouvrage principal *La Musique des Plantes* — 478 pages, 10 parties,
  40 chapitres, 5 annexes, 28 illustrations vectorielles, 21 planches de brevets
  traduites — produit par `build.py` (WeasyPrint) depuis `src/parts/`.
- Le hors-série *La Carte PhytoSense* et ses trois fascicules détachables
  (schémas, nomenclature, circuit imprimé), produits par `build_board.py`.
- La carte PhytoSense One : schémas, routage quatre couches, nomenclature
  chiffrée, planches générées par `src/assets/svg/gen_board.py`.
- Le micrologiciel RP2350 (`sources/firmware-phytosense/phytosense-fw`) :
  ADS131M04 en SPI/DMA, USB classe audio 2.0, protocole de contrôle.
- **PhytoScope 1.0.0 « Première sève »** : quatre sources d'acquisition,
  oscilloscope, multimètre, analyseur, traceur façon gnuplot, écoute musicale,
  bibliothèque, diagnostic, réglages, mode sans interface, 56 tests.

---

## 2026-09-17 — Descripteurs avancés et mode vocal (PhytoScope 1.1.0)

**Agent :** Claude Code.

**Fait :**
- `core/features.py` : FFT, ondelettes de Morlet, MFCC, prédiction linéaire,
  cepstre — en NumPy pur, constantes transposées d'après la fréquence réelle
  (`C-14`), chacune accompagnée de ce qu'elle ne permet pas de conclure (`C-15`).
- `music/lexicon.py` : le mode vocal — registres, grammaires, énoncés traçables.
- `music/voice.py` : synthèse vocale hors ligne, cinq stratégies, file bornée.
- Onglets **Descripteurs** et **Parole**, `enonces.csv` dans les séances.
- `core/interrupt.py` : **Ctrl+C aboutit même derrière Qt** (`C-23`) —
  chronomètre de réveil, chien de garde, SIGTERM.
- Aide : les 22 raccourcis en 5 groupes, **vérifiés par le programme** à
  l'ouverture contre les actions réellement installées.
- Hors-série : deux planches et deux chapitres neufs (176 → 186 pages).

**Corrigé :** tout réglage reconstruisait la chaîne de traitement et **vidait la
mémoire de signal** ; la reconstruction n'a plus lieu que si un réglage de la
chaîne change réellement (`C-27`). Mesuré : 435 ms → 2–15 ms par changement.

**Vérifié :** 111 tests, capture d'écran de chaque onglet, `kill -INT` en mode
console et en interface graphique.

---

## 2026-09-18 — Onze langues (PhytoScope 1.2.0)

**Agent :** Claude Code.

**Fait :**
- `phytoscope/i18n.py` : catalogues JSON découverts au démarrage, clés =
  phrases françaises (`C-30`, `C-32`), repli silencieux, écriture de droite à
  gauche pour l'arabe (`C-35`).
- **652 libellés** traduits en anglais américain, espagnol, portugais, italien,
  indonésien, russe, chinois, japonais, coréen et arabe.
- `tools/i18n.py` : inventaire par analyse syntaxique du code (`C-34`),
  couverture, modèles, clés périmées.
- Sélecteur de langue dans Réglages → Interface, option `--lang`, proposition de
  redémarrage.

**Attention — incident :** un essai de bout en bout lancé avec
`run.py --lang ko --simulation` a **écrit ces options dans la configuration
réelle de l'utilisateur** en se refermant (l'arrêt propre sauve les réglages).
L'utilisateur a retrouvé son interface en coréen au démarrage suivant.
→ Réglages rétablis (`fr`, `auto`), copie de l'état fautif conservée dans
`~/.config/phytoscope/reglages.json.avant-correction`.
→ **Cause corrigée** : une option de ligne de commande ne s'inscrit plus jamais
dans le fichier de réglages (`C-24`, `Settings.forcer`).
→ **Règle pour la suite** : ne jamais lancer le logiciel sur la configuration
réelle ; passer par `XDG_CONFIG_HOME` vers un dossier temporaire.

**Vérifié :** 142 tests dont un qui échoue si un catalogue livré est incomplet ;
premier lancement en français avec `LANG=ko_KR.UTF-8` sur configuration vierge.

---

## 2026-09-18 — Mode vocal utilisable, micrologiciel compilable, surveillance du disque

**Agent :** Claude Code.

**Fait :**
- **Mode vocal** : la musique se tait pendant la parole (`voice.mute_music`,
  actif par défaut) — une voix et un synthétiseur qui jouent ensemble se
  couvrent l'un l'autre, d'où l'impression que « ça ne marche pas ».
  Un voyant permanent dit l'état, le moteur de synthèse et le dernier énoncé.
- **Onze dictionnaires** livrés, un par langue de l'interface
  (`phytoscope/lexiques/`). Ceux du japonais, du coréen, du chinois et de
  l'arabe portent **leurs propres gabarits de phrase** : l'ordre des mots n'est
  pas le nôtre. Le dictionnaire suit la langue de l'interface, sauf choix
  explicite.
- **Micrologiciel** : `pico_sdk_import.cmake` manquait et le SDK n'était pas
  installé. Installés **sans privilège administrateur** — Pico SDK 2.3.1 dans
  `~/pico/pico-sdk`, chaîne ARM GNU 14.2 dans `~/.local/opt/` — et
  `build.sh [--deps|--propre]` écrit pour rendre la manœuvre reproductible
  (`C-55`). Deux en-têtes manquaient dans `afe.c` (`math.h`, `stdio.h`) :
  corrigés. Produit : `phytosense.uf2`, 80 Ko, cœur ARMv8-M mainline.
- **Espace disque** (`core/disk_space.py`) : mesure pendant l'enregistrement,
  alerte à vingt minutes d'autonomie, clôture propre de la séance avant
  saturation (`C-26`). Le rendu musical écrit 305 Mo par heure — c'est lui qui
  remplit le disque, pas le signal (2,6 Mo/h).

**Vérifié :** énoncés prononcés en 45 s d'essai (2 énoncés, 0 abandon, musique
muette) ; les onze dictionnaires produisent une phrase correcte dans leur
langue ; micrologiciel compilé ; clôture automatique d'un enregistrement avec
réserve impossible à satisfaire.

---

## 2026-09-18 (soir) — Échantillons, relecture, disque, fenêtre (PhytoScope 1.3.0)

**Agent :** Claude Code.

**Fait :**
- **Échantillons** (`core/samples.py`) : `Ctrl+E` écrit la dernière minute
  gardée en mémoire — un WAV plus un JSON compagnon. Pleine échelle choisie par
  échantillon (voir `D-5`), jamais d'écrasement, renommage et suppression qui
  emportent le JSON.
- **Relecture par le moteur** : `Engine.rejouer()` / `arreter_relecture()`
  remplacent le poking des attributs privés que faisait la bibliothèque. La
  cadence d'échantillonnage du fichier est installée pendant la relecture, puis
  rendue au retour en direct.
- **Bibliothèque** refondue en deux pages — Séances et Échantillons — avec
  aperçu, résumé chiffré, capture, renommage, suppression, retour en direct.
- **Espace disque** (`core/disk_space.py`) : mesure toutes les cinq secondes,
  alerte à vingt minutes d'autonomie, clôture propre avant saturation ;
  réserve, seuil et répertoire réglables ; espace restant dans le bandeau.
- **Fenêtre réductible** : hauteur minimale 1094 → 520 px. Les colonnes de
  commandes défilent dans leur onglet au lieu d'imposer leur hauteur ; défaut
  invisible sur grand moniteur, bloquant sur un portable.
- **Zoom d'origine** (`Ctrl+0`) sur tous les tracés de l'onglet courant.
- **Sélecteur de langue dans la barre d'outils**, en plus des réglages.
- **Mode vocal** : musique coupée pendant la parole, voyant permanent, onze
  dictionnaires livrés (gabarits propres pour ja, ko, zh, ar).
- **Micrologiciel** : Pico SDK 2.3.1 et chaîne ARM GNU 14.2 installés sans
  privilège administrateur ; `build.sh [--deps|--propre]` ; deux en-têtes
  manquants corrigés dans `afe.c`. Produit `phytosense.uf2` (80 Ko, ARMv8-M).
- **Documentation** : `constraints.md`, `AGENTS.md`, `CLAUDE.md`,
  `CHANGELOG.md`, et ce journal.

**Corrigé :** la relecture rouvrait la sortie audio déjà ouverte — deux fils
écrivaient dans le même flux PortAudio, d'où un plantage net (SIGSEGV). Un
garde-fou dans `AudioOutput.start()` rend l'appel idempotent.

**Puis, sur demande :**
- **Charger un enregistrement extérieur** : un échantillon, le `signal.wav`
  d'une séance ou tout WAV reçu d'ailleurs se rejoue par un sélecteur de
  fichier.
- **La suspension de l'acquisition est dite** : pendant une relecture, la
  source vivante est réellement arrêtée — elle l'était déjà — et un **bandeau
  permanent** le rappelle, avec la position dans le fichier. Si les deux
  coexistaient, on ne saurait plus ce qu'on écoute (`C-1`, `C-2`).
- **Le bouton de retour au cadrage n'apparaît que si la vue a bougé** : un
  « ⟲ » posé sur la courbe, plus l'action de la barre d'outils qui suit le
  même état. Seuls les gestes de l'utilisateur comptent
  (`sigRangeChangedManually`) — un recadrage automatique dû à l'arrivée de
  données ne doit évidemment pas le faire surgir.

**Vérifié :** 162 tests ; traductions à 100 % dans les onze langues (722
libellés) ; capture, zoom, relecture, chargement d'un fichier et retour en
direct essayés depuis l'interface ; suspension de l'entrée vérifiée par test ;
micrologiciel compilé ; hors-série reconstruit (192 pages).

---

## 2026-09-18 (nuit) — Vumètres, empreinte de mesure, barre de menus (PhytoScope 1.4.0)

**Agent :** Claude Code.

**Corrigé d'abord — un défaut que j'avais introduit :** en ajoutant des boutons
à la barre d'outils, celle-ci a débordé la largeur de la fenêtre et Qt a rangé
**l'aide, « À propos » et « Quitter »** derrière un chevron « » », sans
prévenir. L'utilisateur ne les trouvait plus. Réparé par une **barre de menus**
(Séance / Affichage / Aide), qui ne tronque jamais rien ; les mêmes objets
`QAction` servent aux deux, donc un seul raccourci et un seul état.
→ Leçon : une barre d'outils qui grandit escamote ses dernières actions. Tout
ce qui doit rester atteignable va dans un menu.

**Fait :**
- **Quatre vumètres** dans le Multimètre (`widgets.VuMetre`) : balistique de
  150 ms, mémoire de crête, échelle par paliers 1–2–5 inscrite sous le cadran.
  Le nombre donne la valeur, l'aiguille donne le mouvement.
- **Empreinte de mesure** (`core/fingerprint.py`) : huit descripteurs, une
  distance pondérée, un registre JSON des montages connus, et des phrases de
  qualification plutôt qu'un pourcentage nu. Elle caractérise le **montage**,
  jamais la plante — l'avertissement est permanent dans l'interface et occupe
  une section entière du hors-série (`C-1`, `C-5`).
- **Planche « Brancher une feuille et une racine »** et section du hors-série :
  ce qu'on mesure vraiment (le chemin complet, pas la feuille), et **quelle
  électrode planter dans la terre**.

**Corrigé aussi :** le hors-série conseillait une tige de **laiton** dans le
substrat. C'est une faute : laiton et cuivre forment une pile galvanique avec
l'électrode de feuille — des dizaines de millivolts qui dérivent avec
l'humidité — et le cuivre est toxique pour les racines. Remplacé par inox 316L,
graphite, ou pont salin Ag/AgCl, avec la règle qui gouverne tout : **le même
métal aux deux bouts**.

**Vérifié :** 176 tests ; traductions à 100 % dans les onze langues (755
libellés) ; empreinte essayée sur montages synthétiques (95 % entre deux
moments du même montage, nettement moins avec un contact sec) ; hors-série
reconstruit (198 pages).

---

## 2026-09-18 (fin de journée) — Ce que dit le bruit, et où est le journal

**Agent :** Claude Code · **Demandes :** « sur la partie multimètres les données
numériques affiche d'autres indicateurs comme la résistance, ou d'autres données
ou indicateurs scientifiques » ; puis « regarde dans
`~/.config/phytoscope/phytoscope.log` si tu observes des erreurs » ; puis
« ajoute une possibilité d'afficher une fenêtre pour charger le fichier de log
qui s'actualise en temps réel en précisant son emplacement et en permettant d'en
faire une copie dans un path précis ».

**Fait :**
- `phytoscope/core/quantities.py` — quinze grandeurs calculées sur une fenêtre de
  120 s, chacune accompagnée de ce qu'elle dit **et de ce qu'elle ne dit pas**.
- Page « Grandeurs scientifiques » dans le Multimètre (troisième onglet du bas),
  recalculée toutes les deux secondes, et **seulement quand elle est visible**.
- Trois afficheurs de plus sur la façade : RÉSISTANCE ÉQUIV., PLANCHER DE BRUIT,
  RÉSEAU.
- `phytoscope/ui/log_window.py` — fenêtre du journal (`Ctrl+L`, menu Aide) :
  chemin affiché et copiable, contenu en direct par lecture incrémentale,
  filtre, niveau réglable à chaud, « Enregistrer une copie… » avec les archives
  de rotation.
- `tests/conftest.py` — première fixture `qapp` et détournement de
  XDG_CONFIG_HOME / XDG_DATA_HOME / APPDATA.
- 826 libellés traduisibles, 100 % dans les dix langues. Version 1.5.0.

**Pourquoi :**
- La carte ne mesure pas d'impédance pendant une séance : on écoute, on n'excite
  pas. Mais le bruit thermique de Johnson-Nyquist donne `R = Sᵥ / 4kT`. C'est le
  seul chemin honnête vers une résistance — à condition de dire que c'est un
  **majorant** (voir `D-11`).
- Le journal existait mais vivait à un endroit que l'utilisateur devait deviner,
  et il fallait un terminal pour le lire. Trois questions se posent quand quelque
  chose se passe mal : où est-il, que dit-il maintenant, comment l'envoyer. La
  fenêtre répond aux trois.

**Vérifié :**
- La densité de bruit est confrontée au calcul au crayon : 2 µV eff. sur 125 Hz
  de bande donnent 179 nV/√Hz en théorie, le module en lit 174. La résistance
  suit en R² quand le bruit décuple. Onze essais dédiés.
- Rendu hors écran dans quatre écritures (fr, en, ja, ar) : gabarits composés
  après traduction, arabe en `rtl`, aucun mot français résiduel dans la colonne
  « Valeur ».
- Fenêtre du journal : lecture incrémentale confirmée (une ligne ajoutée coûte
  moins de 200 octets relus), rattrapage après vidage, minuterie arrêtée à la
  fermeture. Dix essais dédiés.
- 198 essais au vert.

**Sur le journal de l'utilisateur :** les trois lignes présentes dataient du
2026-09-17 à 17 h 40 (`libGL.so.1` et `libportaudio.so.2` introuvables) et
venaient d'un lancement en bac à sable — le mien, pas le sien. Elles ne se
reproduisent plus ; les deux bibliothèques sont installées et les modules
s'importent. Rien depuis, alors que le logiciel a été relancé le 2026-09-18 à
11 h 13. Réglages intacts (`language: fr`).

**Attention :**
- La colonne « Valeur » des grandeurs ne doit contenir que des symboles d'unité.
  Un essai le vérifie (`test_la_colonne_valeur_ne_contient_aucun_mot_a_traduire`)
  parce que la faute est facile et invisible depuis une interface française.
- Les libellés des grandeurs sont **récoltés** par `grandeurs.inventaire()`, qui
  fait tourner le calcul. Ajouter une grandeur sans traduction fait donc échouer
  la campagne — c'est voulu.

**Suite, même journée — portabilité.** L'utilisateur demande une analyse de
compatibilité Windows 10/11, macOS et Debian/Ubuntu/Mint/Fedora/Red Hat. Relevé
complet dans `.ai/portabilite.md` : treize points, quatre bloquants, **aucune
correction appliquée** — c'était une analyse, pas un chantier.

Le plus grave (`P-1`) a été vérifié à la main et confirmé : le logiciel cherche
la carte sur `0x2E8A:0x10F5` (`protocol.py:38`, `usbdiag.py:38`,
`config.py:255`) alors que le micrologiciel déclare `0x1209:0x7A01`
(`usb_descriptors.c:40-41`). **C'est le logiciel qui a tort** : `0x1209` est la
plage libre de pid.codes, faite pour les projets ouverts, tandis que `0x2E8A`
appartient à Raspberry Pi et ne nous autorise pas à y attribuer un PID. Sous
Linux et macOS un repli par nom de produit sauve la découverte ; sous Windows
`pyserial` ne remplit pas `product`, et le lien de contrôle est donc inutilisable.

La bonne nouvelle, consignée elle aussi : `config_dir()`, `data_dir()`,
`shutil.disk_usage`, les `encoding=` systématiques, `os.path.join` partout et
les gardes Linux-only sont exemplaires. Il n'y a pas de refonte à faire.

---

## 2026-09-18 (nuit) — Windows, macOS, GNU/Linux, et de quoi les installer

**Agent :** Claude Code · **Demandes :** « effectue tous les changements »
(les treize points de `.ai/portabilite.md`), puis « pour chaque OS […] crée des
package/installer pour simplifier l'installation : crée un script bash ou
python3 séparé pour (re)générer la création des packages/installer depuis linux
debian/ubuntu/mint ».

**Fait — portabilité (version 1.5.1) :** les treize points relevés sont
corrigés. Le détail vit dans `CHANGELOG.txt` ; les décisions dans `D-13` et
`D-14`. Deux méritent d'être retenues ici :

- **Le VID/PID était faux dans le logiciel**, pas dans le micrologiciel. Sous
  Windows, cela rendait le lien de contrôle inutilisable ; sous Linux et macOS
  un repli par nom de produit le masquait depuis toujours.
- **L'entrée audio ne pouvait pas s'ouvrir sur Mac ni sous Windows** : on
  demandait 250 Hz à CoreAudio et à WASAPI, qui n'acceptent que le format de
  mixage du périphérique. On se replie désormais sur le débit natif avec
  décimation logicielle, sans perdre un échantillon.

**Fait — empaquetage :** `packaging/build.py` et `packaging/gabarits/`
produisent depuis Debian/Ubuntu/Mint :

| Cible | Fichier | Exige sur la machine cible |
|---|---|---|
| Debian, Ubuntu, Mint | `.deb` | rien |
| Fedora, RHEL, Rocky, Alma | `.rpm` | rien |
| Windows 10 et 11 | `.exe` (NSIS) + `.zip` portable | **rien, pas même Python** |
| macOS Intel + Apple Silicon | `.zip` contenant `PhytoScope.app` | Python 3.9+ |
| Tous | `.tar.gz` source | Python 3.9+ |

**Vérifié :**
- `dpkg-deb -I/-c` et `rpm -qip/-qlp/-qRp` : métadonnées, dépendances et
  contenu conformes.
- L'archive Windows contient bien `pythonw.exe`, `python311.dll`, la
  bibliothèque standard, 1064 fichiers de NumPy, 3830 de Qt et 78 du logiciel ;
  le fichier `._pth` pointe sur `..\app` avec `import site`.
- L'installateur est un vrai `PE32 GUI` de 177,6 Mo.
- 215 essais au vert, 828 libellés à 100 % dans les onze langues.

**Attention — pièges découverts à l'essai :**
- `pip download --no-deps` donnait un paquet Windows de 27 Mo **sans Qt** :
  `PySide6` n'est qu'une roue de quelques kilo-octets qui déclare dépendre de
  `PySide6-Essentials`, `PySide6-Addons` et `shiboken6`. Ne jamais mettre
  `--no-deps` sur le téléchargement des roues.
- `pip install` refuse une roue `win_amd64` sur Linux : il faut `--platform`
  **et** `--target` ensemble pour qu'il accepte de remplir un paquet destiné
  à un autre système.
- Une roue de NumPy ne vaut que pour **une** version mineure de Python. Ne
  couvrir que celle de la machine qui empaquette revenait à livrer 450 Mo de
  bibliothèques inutilisables sur une Ubuntu 24.04. On couvre 3.9 à 3.13.
- Qt pour macOS n'existe qu'en `universal2` : deux paquets par architecture
  contenaient 400 Mo identiques. Un seul paquet macOS, donc.
- **NSIS s'installe sans `sudo`** (`apt-get download` puis `dpkg-deb -x` vers
  `~/.local/opt`), comme le SDK du micrologiciel : `build.py --deps`.

---

## 2026-09-18 (nuit, suite) — La fabrique de paquets

**Agent :** Claude Code · **Demandes :** un `.pkg` macOS en plus du zip ;
« pour la version windows as-tu généré un installshield ? » ; un MSI ; un
générateur par OS et un Makefile ; un fichier de version unique ; une
arborescence `<VERSION>-<TIMESTAMP>/<OS>/` ; readme, install, licence,
changelog et une empreinte par paquet ; la version fournie aux générateurs.

**Réponse à la question posée :** non, ce n'est pas InstallShield — c'est
**NSIS**. InstallShield est un produit commercial de Revenera, sous licence
payante, qui ne tourne que sur Windows. Ce qu'il *produit*, en revanche, c'est
un **MSI**, et `wixl` (msitools) sait le faire sous Linux : c'est désormais
livré (voir `D-20`).

**Fait :**
- `packaging/` réorganisé : `common.py` (ce qui ne dépend d'aucun système),
  un générateur autonome par cible, `build.py` réduit à un aiguillage,
  `verify.py`, et un `Makefile` (`make debian`, `make windows`, `make tout`).
- `packaging/macos_pkg.py` — le format `.pkg` écrit de bout en bout : XAR,
  cpio « odc » et nomenclature BOM, en Python pur, avec relecture de tout ce
  qui est écrit (`D-19`).
- Le **MSI** par `wixl`, avec des identifiants de composants déterministes
  (UUID v5 du chemin) pour que la mise à jour d'un parc se passe bien.
- `src/phytoscope/phytoscope/VERSION` — la seule source du numéro de
  version, lue par le logiciel, la fabrique, `pyproject.toml` et
  `tools/release.py` (`D-17`).
- Sortie en `build/paquets/<version>-<horodatage>/<Système>/`, avec un lien
  `dernier`, une empreinte par paquet, et readme/install/licence/changelog à
  la racine **et** dans chaque dossier de système.

**Vérifié :**
- `make tout` produit huit paquets ; `make verifier` les rouvre tous et
  contrôle métadonnées, contenu, droits d'exécution et empreintes.
- Le `.pkg` : les trois formats imbriqués se relisent et décrivent le même
  ensemble de 104 fichiers.
- Le `.msi` : document composé OLE valide, tables `File`, `Component`,
  `Directory`, `Feature`, `Property` présentes, version conforme.
- 223 essais au vert.

**Attention — pièges découverts à l'essai :**
- **`wixl` refuse les chemins `Source` absolus** et résout tout depuis son
  répertoire courant : décrire l'arborescence en relatif, et se placer dans la
  charge. Il ignore aussi `CompressionLevel` et `WixVariable`.
- **Dans une fonction imbriquée, `lignes += [...]` fait de `lignes` une
  variable locale** et lève `UnboundLocalError`. Utiliser `.extend()`.
- Le **BOM** a un en-tête de nœud de **douze** octets (isLeaf, count, forward,
  backward) : les couples d'indices commencent à l'octet 12, pas 8.
- Un paquet fabriqué sous Linux hérite de l'`umask` : normaliser les droits à
  755/644 avant d'écrire la nomenclature, sinon on livre des dossiers
  inscriptibles par le groupe dans `/Applications`.
- Le `v1.0/` trouvé dans `build/paquets` n'était pas de moi ; c'est ce qui a
  motivé le dossier horodaté. `ecrire_les_empreintes` ignore désormais les
  sous-dossiers qu'il ne connaît pas.

---

## 2026-09-18 (soir) — Paquets, signature et installateurs

**Agent :** Claude Code · **Demandes :** un `.pkg` macOS ; « as-tu généré un
installshield ? » ; un MSI ; un générateur par OS et un Makefile ; un fichier
de version ; `<VERSION>-<TIMESTAMP>/<OS>/` ; empreinte par paquet et documents ;
`manuel.txt` par système ; la version fournie aux générateurs ; un `.run` façon
InstallShield pour Linux ; un certificat et la signature de tout ; l'auteur
Thierry GAYET ; icône de bureau, désinstallateur et lancement demandés à
l'installation ; l'attribution dans un fichier mutualisé ; un essai Windows
sous Wine ; une interface graphique pour le `.run` et `--uninstall`.

**Réponse à la question posée :** non, ce n'est pas InstallShield — c'est NSIS,
et pour Linux un script auto-extractible. InstallShield est un produit
commercial qui ne tourne que sur Windows. Ce qu'il *produit*, un **MSI**, est
désormais livré (`D-20`).

**Fait :**
- `packaging/` : `common.py`, un générateur par système, `verify.py`,
  `signature.py`, `macos_pkg.py`, un `Makefile`, et `gabarits/` par système.
- Huit paquets : `.deb`, `.rpm`, `.run`, `.exe`, `.msi`, deux `.zip`, `.pkg`,
  `.tar.gz`, tous signés, tous accompagnés de leur empreinte et de cinq
  documents (readme, install, manuel, licence, changelog).
- `phytoscope/VERSION` et `phytoscope/AUTEURS` : deux fichiers de données lus
  par le logiciel, la fabrique et la génération du certificat (`D-17`).
- Certificat X.509 de signature de code, Authenticode pour Windows, CMS
  détachée pour le reste (`D-21`).
- Installateur `.run` à trois interfaces, avec `--uninstall` (`D-22`).

**Vérifié :**
- **Sous Wine 6.0.3** : l'interpréteur Python 3.11.9 embarqué démarre, PySide6
  6.11.2, pyserial et sounddevice s'importent, et `run.py --version` affiche
  correctement les accents. **NumPy échoue** — Wine 6.0.3 n'implémente pas
  `fetestexcept` dans son runtime MSVC. C'est une lacune de Wine, pas du
  paquet : la fonction existe sur un vrai Windows, et la DLL se charge.
- **L'installateur NSIS n'a pas pu être essayé sous Wine** : c'est un
  exécutable **32 bits** (ce qui est normal pour NSIS et fonctionne sur un
  Windows 64 bits), et cette machine n'a que Wine 64 bits — `wine32` demande
  `sudo`.
- L'utilisateur a installé le `.run` pour de vrai sur sa machine : la séquence
  complète s'est déroulée comme prévu.
- 225 essais au vert, 832 libellés à 100 % dans les onze langues.

**Attention — pièges découverts à l'essai :**
- **Le `.run` choisissait le Python de Homebrew**, que le logiciel déconseille
  lui-même sous Linux (les roues de Qt bâties dessus ne trouvent pas les
  bibliothèques du système). On cherche désormais dans `/usr/bin` d'abord, et
  l'on écarte explicitement les chemins Homebrew.
- **`wixl` refuse les chemins `Source` absolus** et résout tout depuis son
  répertoire courant ; il ignore `CompressionLevel` et `WixVariable`.
- **`openssl cms -sign` est détaché par défaut** : l'option `-detach` n'existe
  pas.
- **`openssl req` sans `-utf8`** écrit « NamastÃ© » dans le certificat.
- Un jeton `@VERSION@` situé dans un fragment inséré **après** la substitution
  survit à celle-ci : remplir le fragment avant de l'insérer.
- Dans une fonction shell imbriquée en Python, `lignes += [...]` lève
  `UnboundLocalError` ; utiliser `.extend()`.

---

## 2026-09-18 (nuit, fin) — Les modules, le SDK, et la fin du nom de code

**Agent :** Claude Code · **Demandes :** « reprend et continue » ; puis
« change "Version  : 1.5.1 « Les trois systèmes »" dans tous les fichiers par
juste "Version  : 1.5.1" » ; puis, à la question de la portée, « partout,
l'histoire comprise ».

### 1. Ce qui était dans le dépôt sans être au journal

La session précédente a livré **l'API des modules et le SDK** sans en écrire
l'entrée. Relevé et vérifié avant d'y toucher, pour que l'agent suivant ne le
redécouvre pas :

- `phytoscope/api/` — le contrat (`VERSION_API` = 1.0, cinq capacités), le
  `Contexte`, le bus d'événements, le registre (1 338 lignes) ;
- quatre **modules intégrés** qui passent par la même API que n'importe qui —
  `grandeurs-scientifiques`, `descripteurs-avances`, `empreinte-montage`,
  `export-csv` ;
- l'hôte câblé dans `core/engine.py` (chargement au démarrage, réglages
  enregistrés à la fermeture, arrêt ordonné), avec une page **Modules** au
  Diagnostic et une autre aux Réglages ;
- `sdk/` — sept chapitres (1 586 lignes), un module d'exemple avec ses essais,
  et `new_module.py` qui en crée un ;
- le hors-série développeur, **27 pages** :
  `build/Ecrire-un-module-PhytoScope.pdf`, par `build_sdk.py` — qui emprunte
  le moule de `build_board.py` au lieu de le recopier.

**Ce qui n'est pas terminé, et que le SDK promet pourtant :** seules deux des
cinq capacités sont réellement consommées par l'hôte — `analyseur`
(Multimètre → Grandeurs scientifiques) et `descripteur` (onglet Descripteurs).
`exportateur`, `sonificateur` et `source` sont au contrat, documentés, mais
**aucun code de l'hôte ne les appelle** : le module `export-csv` ne s'affiche
donc nulle part dans la Bibliothèque. C'est la dette de ce chantier.

### 2. Le nom de code retiré

**Fait :**
- `tools/headers.py` ne compose plus « 1.5.1 « … » » : un en-tête identifie une
  révision, et un nom de code ne l'identifie pas. Les **240 en-têtes** du dépôt
  portent `Version  : 1.5.1`.
- `phytoscope/VERSION` : `nom =` est vide. Le champ reste — le remplir ferait
  réapparaître le nom partout, sans toucher au code.
- `version.py` : `TITRE_VERSION` et `FULL_TITLE`, **le seul endroit** qui décide
  si un nom paraît. Sept endroits composaient cette ligne eux-mêmes (fenêtre
  « À propos », écran d'accueil, `--version`, SBOM, rapport d'environnement,
  readme des paquets, installateur `.run`) ; ils la demandent désormais.
- `packaging/common.py` : `Identite.titre` et `Identite.mention_nom`, plus le
  jeton `@TITRE_VERSION@` pour les gabarits.
- Le journal des versions, `CHANGELOG.md`, `packaging/README.md` et le titre de
  l'entrée du 2026-09-18 (nuit) ne le mentionnent plus.

**Corrigé — deux défauts de `tools/headers.py` découverts en chemin :**
- **L'outil n'était pas idempotent sur les `.bat` et les `.cmd`.** Il y écrit
  l'en-tête sans accents (une console en cp850 les rendrait illisibles) ; sa
  marque de reconnaissance, elle, gardait son tiret cadratin. Elle n'était donc
  jamais retrouvée, et **chaque exécution empilait un en-tête de plus** : trois
  fichiers en portaient deux. La comparaison se fait désormais sur la forme
  réduite à l'ASCII, et la suppression boucle — elle répare l'empilement au
  lieu de s'y ajouter.
- **Il ne reconnaissait pas les délimiteurs de bloc `<!--` et `-->`.** Il
  retirait le contenu de l'en-tête et laissait les délimiteurs : un commentaire
  vide de plus par exécution dans les 67 fichiers XML (SVG, `Info.plist`,
  `.wxs`). Ils sont ramassés au passage.

**Vérifié :**
- `python3 tools/headers.py` : deuxième passe vide — « 240 fichiers examinés,
  tous déjà à jour ». C'est ce qui manquait pour que l'outil soit sûr.
- Plus aucune occurrence du nom de code dans le dépôt, hors PDF et paquets
  déjà fabriqués.
- **262 essais** au vert ; 861 libellés à 100 % dans les onze langues.
- `run.py --version` → « PhytoScope 1.5.1 — 2026-09-18 » ; la nomenclature
  logicielle et `Identite.titre` rendent « 1.5.1 » sans guillemets vides.
- 66 des 67 fichiers XML se relisent (voir ci-dessous).

**Attention :**
- **`src/assets/svg/timeline.svg` n'est pas du XML bien formé** : un `&` nu,
  ligne 53 (« polygraphe & « perception primaire » »), écrit par
  `src/assets/svg/gen.py` ligne 261 — il faudrait `&amp;`. Le défaut est
  antérieur à cette intervention et WeasyPrint le tolère, mais tout lecteur
  XML strict refuse le fichier. À corriger **dans le générateur**, pas dans la
  planche (`C-45`), ce qui impose de régénérer les planches puis de relancer
  `tools/headers.py`.

---

## 2026-09-18 (fin de journée) — Fusion de « L'Arbre qui Parle », rangement du dépôt, dépôt git public

**Agent :** Claude Code (Opus 5) · **Demande :** fusionner
`musique-of-the-plants-2/` sans perdre un fichier, puis ranger tout le projet
dans un dépôt git public conforme aux attentes de l'open source et du
DevSecOps.

### Fait — la fusion

- **565 fichiers** repris de `musique-of-the-plants-2/` : la série
  « L'Arbre qui Parle » (3 volumes + annexe technique, 573 + 65 pages), ses
  notes de recherche, 234 photographies, 39 illustrations `tt-*`, 5 planches
  `sch-*`, et 817 Mo de dépôts tiers.
- **522** fichiers étaient nouveaux : copiés et vérifiés bit à bit.
- **10** étaient identiques. **33** entraient en collision, dont **27** ne
  différaient que par l'en-tête d'attribution (le parent gagnait).
- **6 collisions réelles**, arbitrées une par une :
  - `book.css` — le sous-répertoire avait **83 lignes de plus** (photographies,
    planches paysage, tableaux de nomenclature). Les fusionner aurait changé
    les PDF du parent : plusieurs sélecteurs sont génériques (`td`,
    `table.tight`). La feuille a donc été gardée entière sous
    `pdf-src/arbre.css`, et la série utilise `arbre.css` quand l'ouvrage
    principal garde `book.css`.
  - `build.py` de la série → `pdf-src/build_tree.py`, deux lignes ajustées.
  - `README.md` de la série → `sources/README-arbre-qui-parle.md`.
  - `fonts.css` — identique hors en-tête.
  - **`gen.py` et `timeline.svg` — le parent avait RÉGRESSÉ.** Le générateur
    du sous-répertoire portait une fonction `esc()` que le parent avait
    perdue, et `timeline.svg` du parent contenait deux `&` nus : **le seul
    SVG mal formé des 65**. Le correctif a été reporté, l'illustration
    régénérée.
- Audit final : **565/565 fichiers retrouvés**, 0 perdu.

### Fait — le rangement

Tout a été déplacé dans `phytoscope/`, qui est désormais le seul répertoire
du dossier parent. La règle de rangement :

| Avant | Après | Pourquoi |
|---|---|---|
| `src/` (les ouvrages) | `pdf-src/`, un **dossier par publication** | `src/` à côté de `software/` laissait croire à du code ; il n'y avait pas une ligne de code dedans |
| `software/phytoscope/` | `src/phytoscope/` | `src/` = le code, et rien d'autre |
| `sources/firmware-phytosense/` | `src/firmware/` | c'est notre développement, pas de la matière de référence |
| `sources/hardware/phytosense-one/` | `hardware/` | idem |
| `sources/firmware-damanhur/` | `sources/reverse/damanhur-bridge/` | reconstitution d'un brevet expiré, pas un produit |
| `sdk/` | `src/sdk/` | du code |
| `research/`, `docs/` | `sources/` | de la matière de référence |
| 5 PDF sous droits à la racine | `sources/ebooks/`, hors dépôt | on n'a pas le droit de les rediffuser |
| `tools/build-annexe.py` | `pdf-src/build_appendix.py` | c'est une fabrique de PDF |
| `paquets/`, `__pycache__`, `.venv` | `.ecarte/` | doublons et régénérables, hors dépôt |

Les `pdf-src/parts*/` ont été éclatés en **un dossier par PDF** (10 dossiers
+ `commun/` pour les tableaux partagés). `build_board.py` réaffecte `PARTS`
par document et son `inject_includes()` se replie sur `commun/`.

### Fait — le dépôt public

- `.gitignore` de **459 lignes**, commenté, couvrant bash, Python, Go, Rust,
  C/C++, Windows 10/11, macOS/Darwin, Debian/Ubuntu/Mint et Fedora/RHEL —
  organisé en trois familles : les secrets, ce qu'on n'a pas le droit de
  rediffuser, ce qui se reconstruit.
- Licences officielles SPDX installées : `LICENSE` (MIT), `LICENSES/MIT.txt`,
  `LICENSES/CERN-OHL-P-2.0.txt`, plus `LICENSES/README.md` qui dit laquelle
  s'applique où.
- `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `AUTHORS`,
  `.editorconfig`, `.gitattributes`, `.pre-commit-config.yaml`,
  `.yamllint.yml`, `.github/CODEOWNERS`, gabarits de tickets et de demandes
  de fusion.
- **6 workflows** : `paquets.yml` (analyse statique puis fabrication par
  système, puis chaîne signée, puis tests sur 3 systèmes × 2 Python),
  `publications.yml` (ne refait **que les PDF touchés**),
  `securite.yml` (7 contrôles), `codeql.yml` (Python et C),
  `scorecard.yml`, `diffusion.yml` (attestation de provenance Sigstore).
- Deux outils nouveaux : `tools/verify_svg.py` et
  `tools/impacted_pdfs.py`.

### Pourquoi — deux défauts trouvés en chemin, et corrigés

1. **Fausse déclaration de licence sur 32 fichiers tiers.**
   `tools/headers.py` avait apposé « © Bretagne Namasté » et
   « SPDX-License-Identifier: MIT » sur LEDFader (MIT © Jeremy Gillick),
   MIDI Sprout (MIT © electricityforprogress) et surtout le micrologiciel
   **Biotron, qui est en GPL-3.0**. Les en-têtes ont été retirés, les
   en-têtes d'origine sont intacts, `sources/schemas`, `sources/code` et
   `sources/software` sont entrés dans `EXCLUS`, et le job `licences` de
   `securite.yml` refuse que cela revienne. L'annexe de codes annonçait aussi
   Biotron en « MIT (code) » : corrigé en GPL-3.0.

2. **Le `.deb` avait disparu de la fabrication.** En passant
   `tools/headers.py --ecrire` sur tout le dépôt, l'en-tête s'est posé sur
   `packaging/gabarits/debian/control` — **un fichier `control` n'admet aucun
   commentaire**, et `dpkg-deb` refusait le paquet avec
   « field name '#' must be followed by colon ». Rien d'autre ne le signalait :
   `make tout` continuait et produisait les sept autres paquets. En-tête
   retiré, `"control"` ajouté à `NOMS_EXCLUS`.

### Vérifié

| Contrôle | Résultat |
|---|---|
| Fichiers de la fusion retrouvés | **565 / 565** |
| `cd src/phytoscope && make test` | **260 passés**, 2 ignorés |
| Les 5 fabriques de PDF | **5 / 5** |
| Pages produites | **1 378 p. sur 10 PDF — 0 écart** après restructuration |
| `tools/verify_svg.py` | **104 illustrations, 0 mal formée** |
| `tools/headers.py --verifier` | **260 fichiers, tous à jour** |
| `cd packaging && make tout` | **8 paquets signés, 0 échec** |
| `cd packaging && make verifier` | empreintes SHA-256 conformes |
| YAML des 6 workflows | tous analysables |
| `git ls-files` et les clés | seul le certificat **public** est suivi |

### Attention

- **Le venv a été recréé à neuf** : `make install-dev` a réinstallé les
  dépendances, et 2 tests sont désormais *ignorés* au lieu d'être exécutés
  (dépendance optionnelle absente). À regarder : `make doctor`.
- **`AUTEURS` contient un numéro de téléphone personnel**
  (`telephone = +33 …`). Le dépôt est public, et ce fichier part dans chaque
  paquet. Le code lit ce champ avec un défaut vide
  (`version.py:114`, `common.py:290`) : le vider est sans conséquence
  technique. **C'est une décision à prendre, elle n'a pas été prise ici.**
- `.ecarte/` pèse 762 Mo (l'ancien venv, surtout). Supprimable sans
  conséquence ; laissé en place parce que rien ne devait être détruit.
- Les paquets Windows pèsent 178 à 275 Mo : ils embarquent l'interpréteur et
  Qt. Ce n'est pas une régression, c'est le mode portable.
- Le journal n'a pas été réécrit pour les nouveaux chemins : il consigne ce
  qui était vrai au moment de chaque entrée.

---

## 2026-09-18 (soirée) — Interpréteurs, installateurs, bytecode, bannière

**Agent :** Claude Code (Opus 5) · **Déclencheur :** `./run.py` échouait sur
`libGL.so.1` alors que `libgl1` était installé.

### Le défaut, et ce qu'il cachait

`./run.py` porte `#!/usr/bin/env python3`. Sur cette machine, le `PATH` donne
d'abord **Homebrew** : un interpréteur sous `/home/linuxbrew` avec son propre
chargeur dynamique, qui ne lit pas `/lib/x86_64-linux-gnu`. Qt, pyqtgraph et
sounddevice s'y installent puis échouent à l'exécution sur des bibliothèques
**présentes**.

Le bilan de démarrage aggravait les choses : il concluait « `libGL.so.1` est
introuvable » et conseillait `sudo apt install libgl1` — un paquet déjà
installé. `sonder_bibliotheque()` savait démêler « présente mais sa
dépendance manque », mais pas « présente et illisible par cet interpréteur ».

**Fait :**
- `core/preflight.py` : `presente_sur_le_systeme()` interroge `ldconfig`, qui
  répond pour le système et non pour nous ; `interpreteur_etranger()` nomme
  Homebrew, Nix ou conda. `analyser_import_casse()` rend un quatrième
  élément et **ne propose plus aucun paquet** quand la bibliothèque est là.
- `run.py` : se relance avec un interpréteur convenable — le venv du projet,
  puis `/usr/bin/python3` —, **jamais** Homebrew, Nix ni conda. Un jeton
  d'environnement empêche la boucle.
- La relance est **silencieuse**. Elle écrivait trois lignes sur la sortie
  d'erreur à chaque lancement ; elle laisse maintenant une trace que la
  checklist rapporte, une fois, au bon endroit.
- `core/console.py` : `banniere()` — ASCII pur, rendue à l'identique par un
  terminal Windows en cp850, un `ssh`, un journal redirigé. Elle donne la
  version sans qu'on la cherche, premier renseignement de tout signalement.
- « bilan de démarrage » devient « **checklist** », partout.

### Installateurs : prêts après l'installation, sur les trois systèmes

Windows embarquait déjà l'interpréteur. Les autres non : le `.run` s'arrêtait
en disant « installez python3 », et le lanceur macOS conseillait
`brew install python` — précisément ce qu'il faut éviter.

**Fait :**
- `packaging/common.py` : `_python_autonome()` récupère CPython **relogeable**
  (python-build-standalone, les binaires qu'utilise `uv`), pendant de
  `_python_embarquable()` pour Windows. Il se déplie dans n'importe quel
  dossier, sans root et sans toucher au système (`C-55`).
- `.run` : 590 ko → **28,4 Mo**. Il cherche d'abord un Python du système —
  Homebrew écarté —, déplie le sien s'il n'en trouve pas, et **efface le
  double** dans le cas contraire.
- macOS : l'interpréteur voyage dans `Resources/python`. Le `.zip` passe de
  700 ko à 18,7 Mo, le `.pkg` de 624 ko à 17,3 Mo. Réserve dite franchement :
  python-build-standalone ne publie pas d'`universal2`, on livre donc
  l'architecture demandée (`--arch`), celle de la machine par défaut.
- **Sous-dépendances système** : le `.deb` déclarait 8 bibliothèques, il en
  déclare 20 (les `libxcb-*` et `libdbus` que le logiciel réclamait lui-même
  manquaient) ; le `.rpm` n'en déclarait **aucune** et en déclare 11. Le
  `.run` ne peut pas les installer sans privilèges — `libGL` doit
  correspondre au pilote graphique : il les **détecte et les nomme
  précisément**, et `--avec-dependances-systeme` les installe sur demande
  explicite.

### Cache de bytecode, après installation

Sans lui, Python recompile à chaque démarrage les modules dont le dossier
n'est pas inscriptible — `/usr/share`, `/Applications`, `Program Files` — et
jette le résultat.

- `.deb` (`postinst`), `.rpm` (`%post`), `.run` : `compileall` du logiciel et
  du venv ; `prerm` et `%postun` emportent le cache, que ni dpkg ni rpm ne
  connaissent.
- Windows : l'installateur `.exe` le construit ; le `.msi` et l'archive
  portable n'ont pas cette occasion, le lanceur s'en charge au premier
  démarrage, avec un témoin.
- macOS : dans l'environnement de l'utilisateur, avec `PYTHONPYCACHEPREFIX`
  puisque le `.app` est en lecture seule.

### Deux plantages latents, trouvés par ruff et corrigés

1. **`core/usbdiag.py:415`** — `if mode != "wb"` testait un nom disparu d'une
   refonte : démarrer une capture de trames levait `NameError`, dans les
   trois formats. Le mode mise au point était cassé, et **aucun test ne
   démarrait de capture**. Quatre tests l'ont fermé.
2. **`packaging/build_fedora.py:59`** — `echec` n'était pas importé : la
   fabrique du `.rpm` plantait au lieu de diagnostiquer proprement, sur le
   chemin exact qu'emprunte qui n'a pas `rpmbuild`.

### Vérifié

| Contrôle | Résultat |
|---|---|
| `make test` | **266 passés** (4 nouveaux), 2 ignorés |
| `ruff --select E9,F821,F822,F823,F811` sur tout le dépôt | **All checks passed** |
| `./run.py` sur un PATH Homebrew | se relance sur le venv, interface chargée |
| `.run` installé pour de vrai (`HOME` jetable) | venv créé, **67 + 1515 `.pyc`**, logiciel démarré |
| Python embarqué du `.run` | 3.11.9, `venv`/`ssl`/`sqlite3`, crée un venv |
| `make debian` / `fedora` / `macos` | `.deb` 369 ko, `.rpm` 609 ko, `.pkg` 17,3 Mo |
| `tools/headers.py --verifier` | 260 fichiers, tous à jour |

### Attention

- **La CI que j'avais écrite aurait échoué au premier `push`** : elle lançait
  `ruff check` en bloquant sur un dépôt qui compte **1050 avertissements de
  style** hérités d'un code écrit pour Python 3.9. Le `Makefile` du projet,
  lui, préfixe `-` : ruff y est consultatif. La CI suit désormais cette
  posture — bloquante sur les plantages (`E9`, `F82x`, `F811`), informative
  sur le reste, avec le compte affiché à chaque passage. L'intention est
  écrite dans `pyproject.toml`.
- Les paquets Windows pèsent 178 à 275 Mo : ils embarquent l'interpréteur et
  Qt. Ce n'est pas une régression.
- **Rien n'est commité** depuis le dépôt initial : ces modifications sont dans
  l'arbre de travail.

---

## 2026-09-18 (nuit) — Mises à jour des bibliothèques, et la langue aux onze voix

**Agent :** Claude Code (Opus 5) · **Demande :** deux choses, dans cet ordre —
vérifier les mises à jour des dépendances Python depuis l'interface Qt ; puis
faire choisir la langue au tout début de l'installation, l'enregistrer, et la
faire reprendre par PhytoScope.

### 1. « Aide → Mises à jour des bibliothèques… »

**Fait :**
- `core/dependency_updates.py` — interroge PyPI, compare, classe les écarts en
  *correctif*, *mineure*, *majeure*. **Aucune dépendance ajoutée** (`C-40`) :
  `urllib` de la bibliothèque standard, et un comparateur de versions écrit
  ici plutôt que `packaging`.
- `ui/updates_dialog.py` — l'interrogation dans un fil séparé (huit requêtes à
  six secondes feraient quarante-huit secondes de fenêtre figée), rien coché
  d'avance, et la sortie de `pip` qui défile ligne à ligne. L'installation
  passe par `preflight.installer()`, qui sait déjà choisir entre le venv,
  `--user` et le gestionnaire du système.
- La liste des dépendances vient de `preflight.REQUIREMENTS`, **seule
  source** : la redire l'aurait fait diverger au prochain ajout. Un test le
  vérifie.

**Un défaut, dans mon propre comparateur, trouvé par ses tests :**
ramasser tous les nombres de « 3.0.0rc1 » donne `(3, 0, 0, 1)`, qui se
compare **après** `(3, 0, 0)` — et une pré-diffusion passait pour plus
récente que la version qu'elle annonce. La chaîne est maintenant coupée au
premier caractère non numérique, et l'ordre couvre
`dev < alpha < beta < rc < (rien) < post`. Quinze cas en test.

### 2. La langue, demandée au tout début

**On demande, on ne devine pas** : `C-31` interdit la détection automatique de
la locale, et l'interdiction vaut pour les installateurs. Une machine dont
l'environnement dit `fr_FR` peut être celle d'un atelier où l'on travaille en
anglais.

**Fait :**
- `packaging/langues/installateur.json` — **51 libellés × 11 langues = 561
  traductions**, une seule source.
- `packaging/languages.py` — deux sorties depuis cette source, parce que les
  deux installateurs ne parlent pas le même langage : des **variables shell**
  pour le `.run` (un `/bin/sh` n'a pas d'analyseur JSON, et en bricoler un à
  coups de `sed` casserait sur la première apostrophe), un bloc
  **`LangString`** pour NSIS. `--verifier` contrôle que chaque `{champ}`
  survit à la traduction.
- `.run` : la langue est la **première question**, avant la licence — qui est
  donc lue dans la langue retenue. Menu numéroté en mode texte (aucun outil à
  installer, fonctionne à travers un `ssh`), liste `zenity`/`kdialog`/
  `whiptail` sinon. `--langue ja` pour une installation sans surveillance.
- NSIS : **onze langues** compilées au lieu de deux, boîte
  `MUI_LANGDLL_DISPLAY` avant la première page, choix mémorisé sous `HKCU`.
- macOS : liste `osascript` à la **première ouverture** — un `.pkg` s'installe
  sans rien demander, c'est ce qu'on attend de lui.
- `.deb` et `.rpm` : `apt` et `dnf` n'interrogent pas. La question se pose donc
  au **premier démarrage du logiciel**, par `ui/language_dialog.py`. Chaque
  langue y est écrite **dans sa propre écriture** — un lecteur coréen
  reconnaît « 한국어 », pas « coréen ».
- `tools/write_language.py` — le maillon commun aux trois installateurs. Il
  **fusionne** : une réinstallation ne change que la langue. Écriture atomique
  par fichier provisoire puis `os.replace`.
- `config.py` : `Settings.premier_lancement`, vrai quand aucun fichier de
  réglages n'existait. Il **n'est pas écrit** dans le fichier — c'est une
  observation du démarrage, pas un réglage —, sans quoi la question
  reviendrait sans fin. Un test le vérifie.

### Aussi, dans le même passage

- **Élévation de droits** : `pkexec`, `kdesu` ou `gksu` quand l'installateur
  vient d'un bureau — une fenêtre d'authentification est alors la seule chose
  correcte, un `sudo` attendrait un mot de passe sur un terminal que personne
  ne regarde —, `sudo` en mode texte. Aucun disponible : la commande exacte
  est affichée.
- **`.github/workflows/sbom.yml`** : la nomenclature logicielle se régénère
  dès qu'une modification touche `src/phytoscope/`, et se reverse sur `main`.
  La comparaison **ignore l'horodatage**, sans quoi il y aurait une révision
  par jour. Sur une demande de fusion, elle signale sans écrire.
- **`ruff` dans la CI** : bloquant sur `E9`, `F82x`, `F811` — les plantages —,
  informatif sur les mille avertissements de style hérités de Python 3.9.
  L'intention est écrite dans `pyproject.toml` avec son pourquoi.
- **Bannière ASCII** et **checklist** affichées au lancement par défaut, avec
  les contrôles avant vol. Le doublon de bannière qui dormait dans
  `__main__.py` — et dont le premier trait avait perdu un caractère — est
  remplacé par `core/console.banniere()`, seule source.
- **`INSTALL.md`** (494 lignes) décrit chaque installateur étape par étape.

### Deux tests que mon rangement avait rendus muets

`test_le_sdk_livre_un_exemple_qui_se_charge` et
`test_les_identifiants_usb_suivent_le_micrologiciel` cherchaient le SDK et le
micrologiciel à leurs anciens emplacements (`sdk/`, `sources/firmware-…/`).
Ils **s'ignoraient silencieusement** depuis le déplacement vers `src/sdk/` et
`src/firmware/` — c'est-à-dire qu'ils ne vérifiaient plus rien, sans le dire.
Chemins corrigés ; ils passent, donc les identifiants USB correspondent
toujours au micrologiciel et l'exemple du SDK se charge toujours.

### Vérifié

| Contrôle | Résultat |
|---|---|
| `make test` | **306 passés, 0 ignoré** (+40 depuis ce matin) |
| `ruff --select E9,F821,F822,F823,F811` | *All checks passed* |
| Couverture des traductions du logiciel | **11 langues à 100 %** (888 libellés) |
| Catalogue des installateurs | 51 × 11 = **561 traductions**, champs préservés |
| `packaging/languages.py --verifier` | toutes présentes et cohérentes |
| Fenêtre des mises à jour | 8 lignes, numpy 2.2.6 → 2.5.3 détecté et coché |
| Fenêtre de langue au premier démarrage | 11 langues, chacune dans son écriture |
| `.run --langue ja` | `[ok] 言語：日本語` — catalogue japonais chargé |
| `tools/write_language.py` | écrit, fusionne, refuse un code inconnu, survit à un JSON cassé |
| `tools/headers.py --verifier` | 265 fichiers, tous à jour |

### Attention

- **Le disque a été saturé pendant la séance** : l'installation d'essai du
  `.run` en japonais a échoué sur `No space left on device` après avoir
  affiché la langue — le mécanisme est donc prouvé, la fin de la chaîne (venv,
  bibliothèques, écriture des réglages) reste à voir sur une installation
  complète. Mes fabrications répétées en sont la cause ; `build/paquets/`
  compte neuf fabrications empilées.
- *(Réserve levée le même soir.)* `make tout` a finalement abouti : **9
  paquets signés, 0 échec**, empreintes SHA-256 conformes. `makensis` compile
  bien les onze langues — la trace le montre : `+ LangDLL::LangDialog`,
  `MUI_LANGDLL_REGISTRY_VALUENAME = Langue`, `!insertmacro: CodeLangue`,
  `ExecToLog … write_language.py "$R0"`, puis
  « Generating language tables... Done! ». Ce qui reste non vu, faute de
  machine Windows ici, c'est la boîte **à l'écran** : la fabrication est
  vérifiée, l'affichage ne peut pas l'être.
- Rien n'est commité depuis le dépôt initial.

---

## 2026-09-18 (nuit, suite) — Le certificat, PACKAGING.md, la nomenclature du projet, le micrologiciel en livrable

**Agent :** Claude Code (Opus 5) · **Demandes :** un script pour (re)créer les
certificats dans `certificat/` ; un `PACKAGING.md` ; proposer de recréer les
certificats s'ils manquent à l'empaquetage ; un script de nomenclature
couvrant `src/phytoscope/` **et** `src/firmware/` ; le micrologiciel dans les
livrables de la CI.

### Une découverte d'abord : rien ne remplissait `certificat/`

Ce dossier avait été rempli **à la main**. `signature.py --deposer` déposait,
lui, une copie à la **racine du dépôt** — précisément le doublon que le
rangement du matin avait écarté. Personne ne savait donc laquelle était à
jour.

**Fait :**
- `packaging/certificate.py` — point d'entrée unique. La cryptographie reste
  dans `signature.py` (aucune recopie) ; ce script s'occupe de ce qu'elle ne
  faisait pas : remplir `certificat/` — certificat public commenté, `.crt`,
  clé en 0600, et une notice **générée** qui porte l'empreinte.
  `--etat`, `--creer`, `--deposer`, `--refaire`, `--verifier`.
- `signature.py` : `CERTIFICAT_PROJET` vise `certificat/`, plus la racine.
- `--verifier` compare **ce qu'openssl lit**, et non les fichiers octet par
  octet : le `.pem` porte un en-tête commenté que le `.crt` n'a pas, et
  comparer les octets signalerait un écart qui n'existe pas.
- Quatre cibles : `make certificat`, `certificat-etat`,
  `certificat-verifier`, `certificat-refait`.

**`--refaire` demande de taper `REMPLACER` en entier, et refuse sans
terminal.** Remplacer une clé de signature n'est pas une chose qu'on fait par
défaut : cela rompt le lien avec tout ce qui a été signé.

### La proposition quand le certificat manque

`signature.py --signer` **créait la clé d'autorité**. Il **propose**
désormais, par `certificat.proposer_si_absent()` : sur une machine
d'intégration continue, une clé créée en silence serait une clé éphémère
qu'on croirait permanente, et les paquets porteraient une signature
invérifiable ailleurs. Sans terminal, il affiche la commande et s'arrête.

### `PACKAGING.md` (560 lignes)

Comment produire un paquet précis ou tous, ce qu'il faut avoir, le
certificat, les durées et les tailles réelles, la vérification, les deux
nomenclatures, la publication, et ce qu'il faut faire quand ça échoue — y
compris le piège du fichier `control` Debian, qui n'admet aucun commentaire.

### `tools/sbom.py` — la nomenclature du **projet**

Il existait `src/phytoscope/tools/sbom.py`, qui recense les bibliothèques
Python et qui est livré dans les paquets. Il reste. Le nouveau répond à une
autre question — « de quoi est fait le projet ? » — et couvre donc le
micrologiciel : Pico SDK, TinyUSB, chaîne ARM, picotool.

- La partie logiciel est **demandée** à l'outil existant ; la redire l'aurait
  fait diverger.
- Les versions du micrologiciel sont **lues** dans `src/firmware/build.sh` et
  `CMakeLists.txt`. Écrites à la main dans un tableau, elles auraient
  vieilli en silence — six tests le protègent.
- Le compilateur ARM et `picotool` portent `scope: excluded` : ils
  **construisent** le produit, ils n'y sont pas embarqués. La distinction
  compte pour qui lit ce document afin de savoir si une faille le concerne.
- `--verifier` ignore l'horodatage et le numéro de série, sinon il y aurait
  une révision par jour sans qu'un composant ait bougé.

### Le micrologiciel devient un livrable

**Il ne se compilait plus.** Le rangement du matin avait laissé dans
`src/firmware/build/` un cache CMake qui retient le **chemin absolu** des
sources et pointait encore sur `sources/firmware-phytosense/phytosense-fw/`.
`cmake` refusait de continuer.

- Cache écarté ; le micrologiciel se recompile — `phytosense.uf2`, 80 ko.
- **`build.sh` détecte désormais un cache périmé et le jette**, plutôt que de
  laisser chacun retrouver que la réponse est toujours la même. Vérifié en
  falsifiant `CMAKE_HOME_DIRECTORY`.
- `paquets.yml` : un job `micrologiciel` compile le `.uf2` à chaque passage,
  contrôle qu'il ne s'est pas effondré (seuil à 32 ko), calcule ses
  empreintes et le joint aux artéfacts. Le Pico SDK est mis en cache d'un
  passage à l'autre.
- `diffusion.yml` : le `.uf2` est publié avec la version sous
  `phytosense-<version>.uf2`, et sa **provenance est attestée** comme celle
  des paquets — un binaire de micrologiciel trouvé quelque part ne dit pas
  d'où il vient.
- `sbom.yml` se déclenche aussi sur `src/firmware/**` et régénère les deux
  nomenclatures.

### Vérifié

| Contrôle | Résultat |
|---|---|
| `make test` | **317 passés, 0 ignoré** |
| `ruff --select E9,F821,F822,F823,F811` | *All checks passed* |
| `tools/sbom.py --verifier` | à jour, 15 composants |
| `certificate.py --verifier` | les deux copies concordent |
| `languages.py --verifier` | 561 traductions cohérentes |
| `tools/headers.py --verifier` | 267 fichiers |
| `src/firmware/build.sh` | `phytosense.uf2` 80 ko, `.elf` 764 ko |
| Cache CMake falsifié | détecté et jeté |
| YAML des 7 workflows | tous analysables |

### Attention — une faute de ma part, réparée

En éprouvant la création du certificat, **j'ai cru que `--creer`
interrogeait** — c'est `--refaire` qui interroge. Il a donc créé deux
nouvelles paires de clés, et mon `mv` de restauration a échoué parce que la
destination existait désormais.

**La clé d'origine était intacte** et a été remise en place. Vérifié à trois
niveaux : empreinte identique
(`57:3D:90:32:…:31:F0`), correspondance clé privée / certificat par
`openssl`, et **les neuf signatures de la fabrication de 20h44 valident
contre le certificat restauré**. Rien n'est perdu.

Restent deux magasins parasites, à supprimer :

```bash
rm -rf ~/.local/share/phytoscope-signature.parasite-a-supprimer \
       ~/.local/share/phytoscope-signature.essai2
```

Et `.ecarte/firmware-build-cache-perime` (27 Mo), le cache CMake écarté.

---

## 2026-09-18 (nuit, fin) — Le micrologiciel a sa chaîne complète

**Agent :** Claude Code (Opus 5) · **Demandes :** renommer
`src/firmware/build.sh` en `_make_.sh` ; écrire un nouveau `build.sh` qui
automatise la construction et range le livrable dans `build/paquets/` ; mettre
le README à jour ; nettoyer les anciennes fabrications.

**Fait :**
- `src/firmware/_make_.sh` — l'ancien script, inchangé dans son travail :
  il **compile**, et rien de plus. C'est ce qu'on veut pendant la mise au
  point, quand on compile vingt fois d'affilée.
- `src/firmware/build.sh` — l'enveloppe : elle appelle `_make_.sh`, puis
  **range le livrable** dans `build/paquets/<version>-<horodatage>/Firmware/`,
  nommé avec sa version, avec ses empreintes et une notice de programmation.
  Options : `--deps`, `--propre`, `--sortie`, `--sans-installer` ; tout ce
  qu'elle ne reconnaît pas est passé à `_make_.sh`.
- Elle suit `PHYTOSCOPE_SORTIE` : lancée par la fabrique de paquets, le
  micrologiciel se range dans **la même fabrication** que les `.deb` et les
  `.msi`, même lancé séparément.
- L'identité de la notice est lue dans `AUTEURS`, seule source — les jetons
  `@EDITEUR@` d'un gabarit n'auraient pas été substitués, ce script n'en
  étant pas un.
- `src/firmware/README.md` : la section 3 documente les deux scripts et le
  piège du cache CMake ; la section 6 les liste.

### Une affirmation périmée, corrigée

Le README affirmait, section 8, que ces sources « **n'ont pas été compilées
ici** ». C'était vrai quand la phrase a été écrite ; ce n'est plus vrai — le
micrologiciel compile, produit 80 ko de `.uf2` pour 44 776 octets de code, et
l'intégration continue le compile à chaque passage. La contrainte `C-3` dit
de vérifier avant d'affirmer ; la section dit maintenant ce qui est vrai, et
distingue **ce qui compile** de **ce qui est éprouvé** : aucune carte n'a été
branchée, et cela reste écrit noir sur blanc.

### Attention — deux fautes de ma part dans cette séance

**1. Le lien « dernier » pointait dans le vide.** Mon `build.sh` posait le
lien même avec `--sortie /tmp/essai`, où `basename` donne un nom relatif qui
n'existe pas dans `build/paquets/`. Corrigé : le lien n'est posé que si la
sortie est bien dans `build/paquets/`. Vérifié.

**2. J'ai supprimé plus que je n'avais annoncé.** En nettoyant
`build/paquets/`, j'avais annoncé conserver `1.5.1-20260918-2044` — la seule
fabrication complète et signée. **Elle a été supprimée avec les autres.** La
logique shell, rejouée isolément, se comporte correctement ; je n'ai pas
d'explication vérifiée de l'écart, et je ne lui en invente pas.

Ce qui est perdu : **les paquets et leurs signatures**, tous régénérables par
`make tout` en une vingtaine de minutes — relancé aussitôt.

Ce qui est intact, vérifié : les **10 PDF** de `build/` (105 Mo), la **clé de
signature** (empreinte `57:3D:90:32:…`), `certificat/`, le micrologiciel
compilé, et **toutes les sources**.

La leçon, pour la prochaine fois : ne pas enchaîner un relevé et une
suppression dans deux commandes séparées en se fiant au relevé de la
première. Lister, puis **supprimer nommément** ce qui a été listé.

### Vérifié

| Contrôle | Résultat |
|---|---|
| `make test` | **317 passés, 0 ignoré** |
| `./build.sh` | livrable rangé, 5 fichiers, notice comprise |
| `./build.sh --sortie /tmp/…` | ne touche pas au lien « dernier » |
| Cache CMake falsifié | détecté et jeté par `_make_.sh` |
| `tools/sbom.py` | lit `SDK_VERSION` dans `_make_.sh` — 2.3.1 |
| YAML des 7 workflows | tous analysables |
| `tools/headers.py --verifier` | à jour |

### Un défaut grave, trouvé juste avant de conclure

En relevant l'état de l'index, **6 449 fichiers y étaient** qui n'avaient rien
à y faire : les cinq ouvrages sous droits de `sources/ebooks/`, les articles
payants, les notices constructeurs, les brevets, 817 Mo d'archives tierces, et
tout `.ecarte/`.

**Cause :** la section 2 du `.gitignore` — celle qui écarte « ce que nous
n'avons pas le droit de rediffuser » — **avait entièrement disparu**, onze
règles, au cours d'une de mes réécritures par script. Le fichier était passé
de 472 à 429 lignes sans que rien ne le signale : `.gitignore` ne désindexe
pas ce qui l'est déjà, et `git add -A` avait fait le reste.

Le dépôt est **public**. Rien n'avait été poussé — le seul commit est
antérieur —, mais un livre ou une clé publiés ne se dépublient pas.

**Fait :**
- `.gitignore` restauré depuis le commit (472 lignes), après avoir vérifié par
  `diff` qu'il n'y avait **que des pertes** depuis, aucun ajout à sauver ;
- une exception ajoutée pour `/sbom.cdx.json`, que ma règle `/sbom*.json`
  — écrite pour les rapports de CI — excluait par ricochet ;
- les 6 449 fichiers désindexés (`git rm --cached`), tous restés sur le
  disque ;
- index vérifié fichier par fichier : **0 fichier ignoré n'est suivi**,
  et les neuf fichiers publics qui *doivent* l'être le sont.

**Et surtout : 20 tests neufs**, `TestGitignoreProtegeLeDepotPublic`, qui
vérifient chacune des quatorze règles et chacune des cinq exceptions, plus la
présence des sections par langage et par système. **Un `.gitignore` est du
code : il se teste.** Le défaut ne peut plus revenir en silence.

| Contrôle | Résultat |
|---|---|
| `make test` | **344 passés, 0 ignoré** |
| Fichiers ignorés mais suivis | **0** |
| Index | 942 fichiers, 162 Mo |
| Ouvrages sous droits, clé privée, `.ecarte/` | tous exclus, vérifiés un par un |

---

## 2026-09-19 — README principal remis à jour

**Agent :** Claude Code (Opus 5) · **Demande :** mettre à jour le `README.md`
principal.

Il datait d'avant la moitié du travail de la veille : il annonçait 260 tests,
ignorait `INSTALL.md`, `PACKAGING.md`, les deux nomenclatures, le choix de la
langue à l'installation, la fenêtre des mises à jour, les interpréteurs
embarqués, le cache de bytecode, le septième workflow, et les deux scripts du
micrologiciel.

**Fait :** réécriture complète — 711 lignes, quatorze sections. Chaque chiffre
a été **mesuré par une commande** avant d'être écrit (`C-3`), et chaque chemin
cité a été vérifié : 0 renvoi cassé sur les 29 fichiers et dossiers
mentionnés, 11 dossiers de publication, 12 générateurs et fabriques.

Ajouté, parce qu'un lecteur les cherche en premier : un § « Installer » en
tête, avec la ligne de commande par système et la mention que la langue est
demandée au début ; la bannière et la checklist telles qu'elles s'affichent ;
les deux scripts du micrologiciel et leur partage de rôle.

### Deux choses trouvées en vérifiant

**1. Le test du `.gitignore` a servi dès le premier jour.** Il a échoué :
l'exception `!/sbom.cdx.json` avait **de nouveau** disparu du fichier. Je
l'ai remise, et les 344 tests repassent. C'est exactement ce pour quoi ces
vingt tests ont été écrits la veille — le défaut se reproduit, et il ne passe
plus inaperçu.

**2. `make doctor` annonçait « PySide6 absent » alors que le logiciel
tourne.** Ce n'est pas un défaut : `tools/doctor.py` s'exécute **avec le
Python du système**, volontairement — « c'est le premier réflexe quand
quelque chose ne démarre pas », dit sa docstring —, et il affiche
l'interpréteur inspecté. Le défaut était dans mon README, qui le plaçait
après `make install-dev` comme s'il rendait compte de l'environnement du
projet. Formulation corrigée aux deux endroits, et renvoi vers
`phytoscope --check` pour l'état du venv.

### Vérifié

| Contrôle | Annoncé | Mesuré |
|---|---:|---:|
| tests | 344 | **344** |
| modules Python | 70 | 70 |
| fragments HTML | 223 | 223 |
| illustrations | 104 | 104 |
| workflows | 7 | 7 |
| fichiers versionnés | 942 | 942 |
| lignes de `.gitignore` | 475 | 475 |
| contraintes | 80 | 80 |

Les commandes citées ont été exécutées : `make certificat-etat`,
`make certificat-verifier`, `tools/verify_svg.py`, `tools/impacted_pdfs.py`,
`tools/sbom.py --verifier` — toutes passent.

---

## 2026-09-19 — deux travaux rouges dans la CI : références d'actions et contrôle de licences

Signalé depuis l'onglet Actions de la publication #4 : « Analyse de
l'arborescence (trivy) » et « Cohérence des licences » en échec. Deux causes
sans rapport l'une avec l'autre, toutes deux des défauts que j'avais
introduits.

### 1. `trivy-action@0.28.0` — une étiquette qui n'existe pas

    Error: Unable to resolve action `aquasecurity/trivy-action@0.28.0`,
    unable to find version `0.28.0`

Les étiquettes de cette action portent toutes un `v` : il fallait `v0.28.0`.

Ce que ce défaut apprend, et qui vaut plus que la coquille : le travail est
devenu rouge dès **« Set up job »**, c'est-à-dire **avant** que le
`continue-on-error: true` de l'étape ne puisse s'appliquer. Une action qui ne
se résout pas n'est pas une étape qui échoue — c'est un travail qui ne
démarre pas. Un contrôle de sécurité devient donc silencieux sans que rien ne
le dise, et la tolérance qu'on croyait avoir posée ne protège de rien.

En vérifiant **les seize** références du dépôt une par une contre l'API
GitHub, une seconde était morte : `ossf/scorecard-action@v2` — cette action
n'a pas d'étiquette majeure flottante. Elle n'avait pas encore échoué parce
que son workflow ne tourne qu'à l'horaire ; elle aurait échoué la nuit
suivante, sans que personne regarde.

Les quatre actions **tierces** sont désormais épinglées par empreinte de
commit, la version dite en clair à côté pour que Dependabot et un lecteur
humain s'y retrouvent :

| Action | Avant | Après |
|---|---|---|
| `aquasecurity/trivy-action` | `@0.28.0` — mort | `@ed142fd…` (v0.36.0) |
| `ossf/scorecard-action` | `@v2` — mort | `@2d11466…` (v2.4.4) |
| `gitleaks/gitleaks-action` | `@v2` | `@ff98106…` (v2.3.9) |
| `softprops/action-gh-release` | `@v2` | `@3bb1273…` (v2.6.2) |

Les actions publiées par GitHub (`actions/*`, `github/codeql-action/*`)
restent suivies par étiquette majeure : leur chaîne d'approvisionnement est
celle du coureur lui-même.

Les huit paramètres que nous passons à trivy ont été vérifiés dans le
`action.yaml` **du commit épinglé**, et non supposés : tous présents. Un de
plus a été ajouté, `limit-severities-for-sarif: true` — sans lui, le
`severity: CRITICAL,HIGH,MEDIUM` que nous déclarons ne s'applique **pas** au
rapport SARIF, où l'action verse toutes les gravités. Le filtre annoncé était
faux.

### 2. Le contrôle de licences accusait à tort

    ! sources/schemas/LEDFader/ — aucun fichier de licence
    ! sources/schemas/biotron-firmware/ — aucun fichier de licence
    ! sources/schemas/midisprout/ — aucun fichier de licence

Les trois projets ont bien leur `LICENSE`, et il est versionné. Le contrôle
était faux :

    ls "$d"LICENSE* "$d"LICENCE* "$d"COPYING*

`ls` rend un code non nul dès qu'**un** des motifs ne trouve rien, même si
les autres trouvent. `LICENCE*` et `COPYING*` n'existant nulle part, le
contrôle déclarait les trois manquants — c'est-à-dire qu'il n'a **jamais**
fonctionné depuis son écriture le 2026-09-18. Réécrit avec `find`, qui ne se
trompe pas là-dessus et ignore la casse d'un seul coup.

Reproduit avant correction, puis contrôlé dans les deux sens : le cas nominal
passe (code 0, trois licences nommées), et un projet sans licence est bien
refusé (code 1) — y compris les variantes `COPYING` et `licence.txt` en
minuscules, qui sont acceptées.

### Le garde-fou, parce que la coquille ne se voit pas

Ni la relecture, ni `yamllint`, ni `zizmor` ne posent la question : tous trois
lisent le fichier, aucun ne demande à GitHub si la cible existe. D'où
`tools/verify_actions.py`, ajouté au travail « Analyse des workflows » —
**sans** `continue-on-error`, seule étape de ce travail à pouvoir refuser une
fusion, puisqu'une référence morte rend un contrôle muet.

Sans réseau, l'outil le dit et sort en 0 : une coupure ne doit pas devenir un
échec de fabrication. Comportement vérifié à travers un mandataire mort.

Cinq essais complètent l'outil dans la suite (349 au total), sur ce qui se
vérifie **hors ligne** : action tierce épinglée, version dite en clair à côté
de l'empreinte, aucune référence sur `main`/`master`/`HEAD`, outil présent et
lancé par la CI. Les quatre essais qui peuvent échouer ont été éprouvés par
mutation — désépinglage, empreinte muette, `@main`, retrait de l'étape : les
quatre échouent comme prévu, et `securite.yml` a été restauré à l'identique.

### Vérifié

| Contrôle | Résultat |
|---|---|
| `make test` | **349 passent** (344 + 5) |
| `tools/headers.py --verifier` | 269 fichiers, tous à jour |
| `ruff` (jeu bloquant de la CI) | aucun avertissement |
| YAML des 7 workflows | tous valides |
| les 16 références d'actions | toutes résolues |
| contrôle de licences, cas nominal | code 0 |
| contrôle de licences, licence absente | code 1 |
| coupure réseau | code 0, message clair |

`pyyaml`, installé dans le venv le temps de valider les workflows, en a été
retiré : `requirements.txt` ne le déclare pas.

### Ce qui reste hors de portée

Le rapport de trivy lui-même n'a pas pu être exécuté ici — il faut le coureur
de la CI. Ce qui est vérifié, c'est que l'action se résout et que ses
paramètres existent à la version épinglée ; ce qu'elle trouvera dans l'arbre
se lira dans l'onglet Security à la prochaine poussée.

---

## 2026-09-19 (suite) — l'outil de contrôle avait le défaut qu'il devait empêcher

Après la poussée de `bceebaf`, j'ai voulu suivre le retour des six workflows
par l'API GitHub. Elle m'a répondu :

    HTTP Error 403: rate limit exceeded

Soixante appels par heure sans jeton, et `tools/verify_actions.py` en avait
déjà consommé seize. Ce mur a révélé un défaut sérieux **dans ce que je
venais de pousser** :

  · l'outil ne rattrapait que `URLError` et `TimeoutError`. Un `HTTPError
    403` remontait en trace et faisait sortir en 1 ;
  · or cette étape est délibérément **non tolérante** — la seule du travail
    à pouvoir refuser une fusion. Une limite de quota aurait donc bloqué une
    fusion pour une raison entièrement étrangère aux workflows ;
  · et en local, seize appels épuisaient le quart du quota horaire de la
    machine, partagé avec tout le reste.

### Corrigé en supprimant la cause, non en rattrapant l'erreur

Rattraper le 403 aurait rendu le contrôle muet précisément quand on
travaille beaucoup — le pire moment. `git ls-remote` répond à la même
question **sans quota, sans jeton et sans compte** : le protocole d'annonce
des références est public. Un appel par dépôt, quatorze au lieu de seize, et
rien à réarmer. Le jeton a été retiré de l'étape de CI : il n'a plus d'objet.

### Ce que le changement a fait gagner

`ls-remote` donne toutes les étiquettes d'un coup, là où l'API répondait
étiquette par étiquette. D'où un contrôle que l'API ne permettait pas : **que
l'empreinte épinglée soit bien celle de la version annoncée en commentaire.**
Sans lui, `@abc123… # v2.6.2` peut désigner n'importe quoi.

Éprouvé : en remplaçant `# v0.36.0` par `# v0.28.0` sur une empreinte
inchangée, l'outil répond

    le commentaire annonce v0.28.0, qui est 915b19bbe73b… et non ed142fd0673e…

— et `915b19bb` est bien le commit de v0.28.0, celui qu'il aurait fallu
écrire hier. Le contrôle ne se contente pas de refuser : il dit quoi.

Une étiquette annotée s'annonce en deux lignes, la seconde suffixée `^{}` et
portant l'empreinte du commit : c'est celle qu'on épingle, et celle que
l'outil compare. Le compte rendu nomme désormais l'étiquette la **plus
précise** quand plusieurs désignent le même commit — il disait « v2 » pour
une empreinte épinglée sur v2.3.9, ce qui laissait croire à un flottement.

### Vérifié

| Contrôle | Résultat |
|---|---|
| état courant, `--epingle` | code 0 — 16 références sur 14 dépôts |
| commentaire de version faux | code 1, et l'empreinte attendue est dite |
| `trivy-action@0.28.0` remise | code 1, introuvable |
| réseau coupé (mandataire mort) | code 0, message clair |
| `make test` | 349 passent |
| `tools/headers.py --verifier` | 269 fichiers à jour |
| `ruff` (jeu bloquant) | aucun avertissement |
| YAML des 7 workflows | valides |

Le retour des workflows de `bceebaf` n'a pas pu être relevé : le quota ne se
réarme qu'à l'heure suivante. Il se lira dans l'onglet Actions.
