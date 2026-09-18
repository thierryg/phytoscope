# État du travail

**Au 2026-09-18, fin de journée (1.5.1).** Ce fichier dit où en est le chantier : ce qui tient debout,
ce qui est en cours, ce qui attend. Il se met à jour **à chaque intervention**,
en même temps que `.ai/journal.md`.

## Ce qui tient debout

| Ensemble | État | Repère |
|---|---|---|
| Ouvrage principal | 478 p. — construit | `build/La-Musique-des-Plantes.pdf` |
| Hors-série + 3 fascicules | 198 + 12 + 18 + 7 p. — construits | `build/La-Carte-PhytoSense.pdf` |
| Logiciel PhytoScope | **1.5.1**, 260 tests au vert (2 ignorés) | `src/phytoscope/` |
| Traductions | 11 langues, 861 libellés, couverture 100 % | `tools/i18n.py --couverture` |
| Échantillons et relecture | capture `Ctrl+E`, relecture dans le moteur | `core/samples.py` |
| Dictionnaires du mode vocal | 11, un par langue | `phytoscope/lexiques/` |
| Micrologiciel RP2350 | compile — `phytosense.uf2`, 80 Ko | `./build.sh` |
| Surveillance du disque | mesure, alerte, clôture propre | `core/espace.py` |
| Vumètres | quatre cadrans à balistique | `widgets.VuMetre` |
| Empreinte de mesure | huit descripteurs + registre des montages | `core/empreinte.py` |
| Grandeurs scientifiques | quinze, dont la résistance équivalente (majorant) | `core/grandeurs.py` |
| Fenêtre du journal | direct, chemin, copie, `Ctrl+L` | `ui/log_window.py` |
| Portabilité | 13 points relevés, 13 corrigés | `.ai/portabilite.md` |
| Paquets d'installation | .deb, .rpm, .run, .exe, .msi, .pkg, .zip, .tar.gz | `packaging/Makefile` |
| Signature | X.509 auto-signé, Authenticode + CMS | `packaging/signature.py` |
| Attribution | une seule source, lue par tous | `phytoscope/AUTEURS` |
| Version | une seule source, lue par tous ; **sans nom de code** | `phytoscope/VERSION` |
| API des modules | contrat 1.0, cinq capacités, registre isolant | `phytoscope/api/` |
| Modules intégrés | quatre, par la même API que n'importe qui | `phytoscope/modules/` |
| SDK | sept chapitres, un exemple, un générateur de module | `src/sdk/` |
| **Série « L'Arbre qui Parle »** | 3 volumes, 573 p. — fusionnée ce jour | `pdf-src/build_arbre.py` |
| **Annexe technique de la série** | 65 p. — construite | `pdf-src/build_annexe.py` |
| **Guide du SDK imprimé** | 27 p. — construit | `pdf-src/build_sdk.py` |
| **Dix publications** | **1 378 pages**, un dossier de sources par PDF | `pdf-src/` |
| **Dépôt git public** | arborescence rangée, `.gitignore` en 459 lignes | `phytoscope/` |
| **Intégration continue** | 6 workflows — analyse, paquets, PDF, sécurité, CodeQL, diffusion | `.github/workflows/` |
| **Contrôle des illustrations** | 104 SVG, 0 mal formée | `tools/verifier_svg.py` |
| **Reconstruction sélective** | ne refait que les PDF touchés | `tools/pdf_impactes.py` |
| **Cohérence des licences** | MIT + CERN-OHL-P v2, code tiers rendu à sa licence | `LICENSES/README.md` |
| Hors-série développeur | 27 p. — construit | `build/Ecrire-un-module-PhytoScope.pdf` |
| En-têtes d'attribution | 240 fichiers, outil idempotent | `tools/entetes.py` |

## En cours — ne pas repartir de zéro

**Le chantier des modules est à moitié consommé, et c'est le seul.** L'API, le
registre, les quatre modules intégrés, le SDK et son hors-série sont livrés et
éprouvés ; mais sur les cinq capacités du contrat, **l'hôte n'en appelle que
deux** :

| Capacité | Consommée par l'hôte ? | Où elle devrait paraître |
|---|---|---|
| `analyseur` | oui | Multimètre → Grandeurs scientifiques (`ui/tabs.py`) |
| `descripteur` | oui | onglet Descripteurs (`ui/features_tab.py`) |
| `exportateur` | **non** | Bibliothèque — `ui/library_tab.py` n'interroge pas le registre |
| `sonificateur` | **non** | Écoute — rien dans `music/` ne consulte le registre |
| `source` | **non** | les sources d'acquisition, dans `core/sources.py` |

Conséquence visible : le module intégré `export-csv` est chargé, actif, et ne
sert à rien — aucun écran ne propose son format. Le SDK, lui, promet les cinq
(`src/sdk/docs/01-demarrage.md`, tableau « Où ça s'affiche »). C'est par là qu'il
faut reprendre.

La portabilité est traitée — les treize points de `.ai/portabilite.md` sont
corrigés — et la fabrique des paquets fonctionne pour les cinq cibles.

## Ce qui attend

- ⬜ **Superposition synchrone** (l'« œil » honnête) : voir `D-10`. Non
  commencé, en attente d'un accord — trois formes possibles, seule la première
  relève du logiciel : superposition déclenchée du signal végétal, œil au sens
  propre sur un montage à NE555, planche de méthode pour l'isolateur numérique.
- ⬜ **Relecture des dix traductions** par des locuteurs natifs — surtout russe,
  chinois, japonais, coréen et arabe. Le mécanisme rend la correction triviale
  (un éditeur de texte, aucune recompilation).
- ⬜ **Dictionnaires du mode vocal** : les onze livrés sont des points de départ
  écrits d'un trait ; ils gagneraient à être relus par des praticiens.
- ⬜ **Séances longues** : le découpage automatique (`split_hours`) est déclaré
  dans les réglages mais pas encore appliqué par l'enregistreur.
- ⬜ **Quantification rythmique**, chorus et effet d'espace : présents dans les
  réglages, pas encore appliqués par le rendu.
- ⬜ **Essais sur matériel réel Windows et macOS** : les correctifs de
  portabilité sont vérifiés par lecture du code et par 17 essais automatiques,
  mais **aucun n'a tourné sur une vraie machine Windows ni sur un Mac**. C'est
  la seule dette qui reste sur ce chantier, et elle est réelle.
- ⬜ **Signature des paquets** : ni Windows ni macOS ne sont signés — certificat
  payant d'un côté, compte développeur Apple et Mac de l'autre. Les paquets
  expliquent comment passer outre (`D-15`).
- ⬜ **Le `.pkg` n'a jamais été soumis à `installer(8)`** : le format est écrit
  à la main et relu par nos soins, mais seul un Mac peut confirmer qu'il
  s'installe. Idem pour le `.msi` et `msiexec` (`D-19`, `D-20`).
- ⬜ **L'installateur NSIS n'a pas pu être essayé sous Wine** : c'est un
  exécutable 32 bits — normal pour NSIS —, et cette machine n'a que Wine
  64 bits. `sudo apt install wine32` permettrait l'essai.
- ⬜ **NumPy ne s'importe pas sous Wine 6.0.3** (`fetestexcept` non implémenté
  dans le runtime MSVC de Wine). Lacune de Wine, pas du paquet : le reste de
  la charge — Python 3.11.9, PySide6, pyserial, sounddevice — fonctionne, et
  `run.py --version` s'exécute. Un Wine plus récent lèverait le doute.
- ⬜ **Le `.run` en mode graphique n'a pas été essayé** : cela ouvrirait des
  fenêtres zenity sur l'écran de l'utilisateur. Les modes texte et sans
  surveillance sont, eux, éprouvés de bout en bout (installation, registre,
  `--uninstall`).
- ⬜ **`pdf-src/assets/svg/timeline.svg` n'est pas du XML bien formé** : un `&`
  nu, écrit par `pdf-src/assets/svg/gen.py` (ligne 261). WeasyPrint le tolère, un
  lecteur XML strict non. À corriger dans le générateur (`C-45`), donc en
  régénérant les planches puis en relançant `tools/entetes.py`.
- ⬜ **Le chantier des modules n'a ni entrée de `CHANGELOG.txt`, ni contrainte
  dans `constraints.md`, ni ligne dans `CHANGELOG.md`** : le code et le SDK
  sont là, la trace documentaire manque. Le journal du 2026-09-18 (nuit, fin)
  en dresse l'inventaire.
- ⬜ **Mise à jour du hors-série** : la page « Grandeurs scientifiques », la
  fenêtre du journal et les paquets d'installation ne figurent pas encore dans
  le manuel ; le PDF est donc en retard de deux versions sur le logiciel.

## Pièges connus

- Une barre d'outils qui grandit **escamote ses dernières actions** derrière un
  chevron, sans prévenir : ce qui doit rester atteignable va dans la barre de
  menus (incident du 2026-09-18).
- Ne **jamais** lancer le logiciel sur `~/.config/phytoscope/` pendant un essai
  (incident du 2026-09-18) : `XDG_CONFIG_HOME=/tmp/…` systématiquement.
- La sortie audio ne supporte pas deux ouvertures : `AudioOutput.start()` est
  désormais idempotent, ne pas retirer ce garde-fou (un SIGSEGV en dépend).
- La sortie audio ALSA se plaint bruyamment à l'arrêt en mode hors écran ; sans
  conséquence, c'est le teardown de PortAudio.
- Un libellé qui **incruste un nombre** (« Écart d'Allan à 1 s ») ne peut pas
  entrer dans un catalogue de traduction : écrire un gabarit (« à {tau} s ») et
  composer **après** `t()`, jamais avant.
- La colonne d'une valeur mesurée ne doit porter **que des symboles d'unité** —
  ils sont internationaux. Un « au-dessus du plancher » collé derrière un chiffre
  reste en français dans les dix autres interfaces ; un essai le surveille.
- `tests/conftest.py` détourne XDG_CONFIG_HOME, XDG_DATA_HOME et APPDATA : ne
  pas le contourner, c'est ce qui protège la configuration de l'utilisateur.
- **`pip download --no-deps` vide un paquet de sa substance** : `PySide6` n'est
  qu'une roue de quelques kilo-octets ; les 400 Mo de Qt sont dans ses
  dépendances. Le paquet Windows faisait 27 Mo et n'aurait pas démarré.
- **Une roue de NumPy ne vaut que pour une version mineure de Python.** Les
  paquets Linux et macOS en embarquent donc pour 3.9 à 3.13 ; Qt y échappe,
  ses roues étant « abi3 ».
- Un libellé de l'interface ne doit **jamais dépendre de la plateforme** : la
  liste des clés à traduire varierait d'un système à l'autre, et un même
  catalogue ne pourrait plus les servir tous. Conditionner le texte, pas
  l'existence de l'entrée.
- Un outil qui écrit un texte **transformé** doit le reconnaître sous sa forme
  transformée. `tools/entetes.py` écrit les en-têtes des `.bat` sans accents,
  mais cherchait sa marque **avec** son tiret cadratin : il ne la retrouvait
  jamais et empilait un en-tête par exécution (2026-09-18).
- Une suppression de bloc de commentaire doit emporter ses **délimiteurs**
  (`<!--`, `-->`, `*/`) : sans eux, chaque passage laissait un commentaire vide
  de plus dans les 67 fichiers XML du dépôt.
- Le **nom de code** d'une version est facultatif et vide depuis la 1.5.1. Qui
  veut l'afficher demande `version.TITRE_VERSION` (logiciel) ou
  `Identite.titre` (fabrique) — jamais `f"{VERSION} « {RELEASE_NAME} »"`, qui
  produit une paire de guillemets vides quand le nom manque.


## Ce qui attend une décision

- **`AUTEURS` contient un numéro de téléphone personnel.** Le dépôt est
  public et ce fichier part dans chaque paquet. Le code lit le champ avec un
  défaut vide (`version.py:114`, `packaging/commun.py:290`) : le vider est
  sans conséquence technique. Décision non prise.
- **Le premier `git push`.** Le dépôt local est prêt et la télécommande est
  `git@github.com:thierryg/phytoscope.git`, mais rien n'a été poussé : publier
  est irréversible, et cela se décide.
- **`.ecarte/` pèse 762 Mo** (l'ancien environnement virtuel, surtout).
  Supprimable sans conséquence — laissé en place parce que la consigne était
  de ne rien perdre.
- **2 tests sont ignorés** depuis que l'environnement virtuel a été recréé :
  une dépendance optionnelle manque. `make doctor` le dit.
