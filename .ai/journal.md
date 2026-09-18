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
  (schémas, nomenclature, circuit imprimé), produits par `build_carte.py`.
- La carte PhytoSense One : schémas, routage quatre couches, nomenclature
  chiffrée, planches générées par `src/assets/svg/gen_carte.py`.
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
- **Espace disque** (`core/espace.py`) : mesure pendant l'enregistrement,
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
- **Espace disque** (`core/espace.py`) : mesure toutes les cinq secondes,
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
- **Empreinte de mesure** (`core/empreinte.py`) : huit descripteurs, une
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
- `phytoscope/core/grandeurs.py` — quinze grandeurs calculées sur une fenêtre de
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

**Fait — empaquetage :** `packaging/construire.py` et `packaging/gabarits/`
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
  `~/.local/opt`), comme le SDK du micrologiciel : `construire.py --deps`.

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
- `packaging/` réorganisé : `commun.py` (ce qui ne dépend d'aucun système),
  un générateur autonome par cible, `construire.py` réduit à un aiguillage,
  `verifier.py`, et un `Makefile` (`make debian`, `make windows`, `make tout`).
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
- `packaging/` : `commun.py`, un générateur par système, `verifier.py`,
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
  et `nouveau_module.py` qui en crée un ;
- le hors-série développeur, **27 pages** :
  `build/Ecrire-un-module-PhytoScope.pdf`, par `build_sdk.py` — qui emprunte
  le moule de `build_carte.py` au lieu de le recopier.

**Ce qui n'est pas terminé, et que le SDK promet pourtant :** seules deux des
cinq capacités sont réellement consommées par l'hôte — `analyseur`
(Multimètre → Grandeurs scientifiques) et `descripteur` (onglet Descripteurs).
`exportateur`, `sonificateur` et `source` sont au contrat, documentés, mais
**aucun code de l'hôte ne les appelle** : le module `export-csv` ne s'affiche
donc nulle part dans la Bibliothèque. C'est la dette de ce chantier.

### 2. Le nom de code retiré

**Fait :**
- `tools/entetes.py` ne compose plus « 1.5.1 « … » » : un en-tête identifie une
  révision, et un nom de code ne l'identifie pas. Les **240 en-têtes** du dépôt
  portent `Version  : 1.5.1`.
- `phytoscope/VERSION` : `nom =` est vide. Le champ reste — le remplir ferait
  réapparaître le nom partout, sans toucher au code.
- `version.py` : `TITRE_VERSION` et `FULL_TITLE`, **le seul endroit** qui décide
  si un nom paraît. Sept endroits composaient cette ligne eux-mêmes (fenêtre
  « À propos », écran d'accueil, `--version`, SBOM, rapport d'environnement,
  readme des paquets, installateur `.run`) ; ils la demandent désormais.
- `packaging/commun.py` : `Identite.titre` et `Identite.mention_nom`, plus le
  jeton `@TITRE_VERSION@` pour les gabarits.
- Le journal des versions, `CHANGELOG.md`, `packaging/README.md` et le titre de
  l'entrée du 2026-09-18 (nuit) ne le mentionnent plus.

**Corrigé — deux défauts de `tools/entetes.py` découverts en chemin :**
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
- `python3 tools/entetes.py` : deuxième passe vide — « 240 fichiers examinés,
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
  `tools/entetes.py`.

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
  - `build.py` de la série → `pdf-src/build_arbre.py`, deux lignes ajustées.
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
| `tools/build-annexe.py` | `pdf-src/build_annexe.py` | c'est une fabrique de PDF |
| `paquets/`, `__pycache__`, `.venv` | `.ecarte/` | doublons et régénérables, hors dépôt |

Les `pdf-src/parts*/` ont été éclatés en **un dossier par PDF** (10 dossiers
+ `commun/` pour les tableaux partagés). `build_carte.py` réaffecte `PARTS`
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
- Deux outils nouveaux : `tools/verifier_svg.py` et
  `tools/pdf_impactes.py`.

### Pourquoi — deux défauts trouvés en chemin, et corrigés

1. **Fausse déclaration de licence sur 32 fichiers tiers.**
   `tools/entetes.py` avait apposé « © Bretagne Namasté » et
   « SPDX-License-Identifier: MIT » sur LEDFader (MIT © Jeremy Gillick),
   MIDI Sprout (MIT © electricityforprogress) et surtout le micrologiciel
   **Biotron, qui est en GPL-3.0**. Les en-têtes ont été retirés, les
   en-têtes d'origine sont intacts, `sources/schemas`, `sources/code` et
   `sources/software` sont entrés dans `EXCLUS`, et le job `licences` de
   `securite.yml` refuse que cela revienne. L'annexe de codes annonçait aussi
   Biotron en « MIT (code) » : corrigé en GPL-3.0.

2. **Le `.deb` avait disparu de la fabrication.** En passant
   `tools/entetes.py --ecrire` sur tout le dépôt, l'en-tête s'est posé sur
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
| `tools/verifier_svg.py` | **104 illustrations, 0 mal formée** |
| `tools/entetes.py --verifier` | **260 fichiers, tous à jour** |
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
  (`version.py:114`, `commun.py:290`) : le vider est sans conséquence
  technique. **C'est une décision à prendre, elle n'a pas été prise ici.**
- `.ecarte/` pèse 762 Mo (l'ancien venv, surtout). Supprimable sans
  conséquence ; laissé en place parce que rien ne devait être détruit.
- Les paquets Windows pèsent 178 à 275 Mo : ils embarquent l'interpréteur et
  Qt. Ce n'est pas une régression, c'est le mode portable.
- Le journal n'a pas été réécrit pour les nouveaux chemins : il consigne ce
  qui était vrai au moment de chaque entrée.
