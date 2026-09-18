# Décisions de conception

Format court : **contexte → décision → conséquence**, et ce qui la ferait
changer. Une décision qu'on ne sait pas défendre n'est pas une décision, c'est
une habitude.

---

## D-1 — Python plutôt que C++ ou Rust pour le logiciel

**Contexte :** un logiciel de mesure lent au rendu mais rapide à modifier, que
des non-informaticiens doivent pouvoir amender.
**Décision :** Python 3 + PySide6 + NumPy, sans SciPy.
**Conséquence :** le rappel audio ne calcule rien (tampon rempli à l'avance),
les coefficients de filtre sont écrits à la main. Voir la partie V du hors-série.
**Ce qui la changerait :** une cadence d'échantillonnage au-delà de 10 kHz.

## D-2 — Les clés de traduction sont les phrases françaises

**Contexte :** un catalogue incomplet ne doit jamais dégrader l'interface.
**Décision :** `t("Oscilloscope")` plutôt que `t("tab.scope.title")`.
**Conséquence :** une traduction manquante affiche du français correct ; le code
reste lisible ; renommer une phrase française invalide sa traduction — d'où
l'outil `--inutiles` et le test de couverture.

## D-3 — Le français au premier lancement, sans détection de locale

**Contexte :** l'ouvrage, les planches et les dictionnaires sont en français.
**Décision :** `UISettings.language = "fr"`, aucune lecture de `LANG`.
**Conséquence :** une interface toujours cohérente avec sa documentation ; le
choix de l'utilisateur, lui, est conservé. Verrouillé par sept tests (`C-31`).

## D-4 — Une option de ligne de commande ne s'enregistre pas

**Contexte :** `--simulation` passé une fois laissait le logiciel en simulation
pour toujours ; `--lang ko` laissait l'interface en coréen.
**Décision :** `Settings.forcer()` retient la valeur d'origine et la remet à
l'écriture, sauf si l'utilisateur change lui-même le réglage entre-temps.
**Conséquence :** les essais ne polluent plus la configuration (`C-24`).

## D-5 — L'échantillon choisit sa pleine échelle

**Contexte :** un signal de 150 µV écrit à ±2,5 V n'utilise que neuf bits sur
vingt-quatre, et se quantifie à 0,3 µV — soit un tiers du bruit propre.
**Décision :** pleine échelle arrondie dans la suite 1–2–5 au-dessus de
l'amplitude observée, inscrite dans le JSON compagnon.
**Conséquence :** pas de quantification sous le picovolt ; un WAV privé de son
JSON reste lisible mais son amplitude est *supposée*, et l'interface le dit.

## D-6 — La musique se tait pendant le mode vocal

**Contexte :** une voix et un synthétiseur qui jouent ensemble se couvrent ;
l'utilisateur conclut que le mode vocal est cassé.
**Décision :** `voice.mute_music`, actif par défaut ; la détection continue.
**Conséquence :** le mode vocal s'entend dès qu'on l'active.

## D-7 — Les dictionnaires portent leurs propres gabarits de phrase

**Contexte :** « 私は かすかに ふるえる » n'a pas l'ordre de « je frémis à peine ».
**Décision :** un dictionnaire peut définir ses gabarits par grammaire ; ils
l'emportent sur ceux de `GRAMMAIRES`.
**Conséquence :** le japonais, le coréen, le chinois et l'arabe sortent des
phrases correctes sans que le moteur connaisse la moindre grammaire.

## D-8 — Le SDK et la chaîne ARM s'installent dans le dossier personnel

**Contexte :** compiler le micrologiciel ne doit pas exiger le mot de passe
administrateur de l'utilisateur.
**Décision :** `_make_.sh --deps` installe le Pico SDK dans `~/pico/pico-sdk` et
la chaîne ARM GNU dans `~/.local/opt/`.
**Conséquence :** reproductible sur une machine d'atelier ; qui préfère les
paquets de sa distribution les installe, le script les trouve aussi.

## D-9 — On s'arrête avant le disque plein, pas après

**Contexte :** le rendu musical écrit 305 Mo/h ; une séance de nuit remplit un
disque de démonstration.
**Décision :** mesure toutes les cinq secondes, alerte à vingt minutes
d'autonomie, clôture propre en deçà de la réserve (500 Mo par défaut).
**Conséquence :** une séance close vaut infiniment mieux qu'une séance tronquée
par une erreur d'écriture (`C-26`, `C-29`).

## D-10 — Pas de diagramme de l'œil sur le signal végétal

**Contexte :** la question a été posée ; l'outil est séduisant.
**Décision :** refusé sous ce nom — sans horloge ni alphabet, superposer des
segments à une période arbitraire produit une image qui ne mesure rien.
Réservé au lien numérique et aux montages à période connue (NE555).
**Ce qui la changerait :** une superposition **déclenchée** (stimulus, marqueur,
période détectée par le cepstre) serait légitime sous le nom de « superposition
synchrone » — elle reste à écrire.

## D-11 — La résistance est un majorant, et le dit

**Contexte :** l'utilisateur demande la résistance parmi les indicateurs du
multimètre. Or la carte n'injecte aucun courant pendant une séance : il n'y a
pas d'impédancemètre, et il n'en faut pas — on écoute, on n'excite pas.

**Décision :** la calculer à partir du bruit thermique, `R = Sᵥ / 4kT`, et
l'afficher sous le nom de **résistance équivalente**, avec la mention explicite
qu'il s'agit d'un **majorant**. Le bruit observé contient aussi celui de
l'amplificateur et tout ce que le montage capte ; la source ne peut donc pas
être plus résistive que le nombre affiché, mais elle peut l'être moins.

**Pourquoi c'est utile quand même :** un contact qui sèche fait grimper ce
majorant d'une décade en quelques minutes. C'est sa **variation** qui informe,
pas sa valeur absolue — et l'interface le dit dans la colonne d'à côté.

**Conséquence :** la densité est lue entre 10 et 40 Hz, au-dessus de la bande
biologique, sans quoi on compterait l'activité de la plante comme du bruit
(`C-1A`, `C-15`).

**Ce qui la changerait :** une injection de courant alternatif de faible
amplitude donnerait une vraie impédance — mais elle cesserait d'être une écoute
passive, ce que le projet refuse par ailleurs.

## D-12 — On mesure le bruit avant de le filtrer

**Contexte :** les grandeurs de bruit pouvaient se calculer sur le signal
traité, disponible au même endroit et déjà propre.

**Décision :** `engine.recent(duree, raw=True)`. Le réjecteur effacerait le
résidu de réseau qu'on cherche justement à mesurer ; le passe-bas à 40 Hz
effacerait la bande 10–40 Hz où se lit le bruit thermique.

**Conséquence :** les nombres de la page « Grandeurs scientifiques » peuvent
différer de ceux des autres onglets, et l'en-tête de la page l'annonce en toutes
lettres. Filtrer avant de mesurer le bruit revient à mesurer son propre filtre
(`C-1B`).

## D-13 — Les identifiants USB suivent le micrologiciel, pas l'inverse

**Contexte :** le logiciel cherchait la carte sur `0x2E8A:0x10F5`, le
micrologiciel déclare `0x1209:0x7A01`. Il fallait trancher.

**Décision :** c'est le **micrologiciel** qui a raison, et le logiciel qui a
été corrigé. `0x1209` est la plage de **pid.codes**, ouverte aux projets
libres ; `0x2E8A` appartient à Raspberry Pi, et rien ne nous autorise à y
attribuer un PID de notre choix. Publier un produit sous l'identifiant de
quelqu'un d'autre est une faute, même quand la carte est bâtie sur sa puce.

**Conséquence :** un essai lit `usb_descriptors.c` et compare les trois
déclarations du logiciel. La divergence ne peut plus passer inaperçue — elle
était restée invisible sous Linux et macOS, où un repli par nom de produit la
masquait, et rendait la carte inutilisable sous Windows (`C-2D`).

## D-14 — Une pile de polices, jamais une famille

**Contexte :** « DejaVu Sans Mono » était nommée en dur à vingt et un endroits.
Elle est installée d'office sur presque toutes les distributions GNU/Linux et
sur aucune installation neuve de Windows ou de macOS.

**Décision :** `ui/polices.py` déclare une pile de familles **et le genre**
(`QFont.Monospace`). Le genre importe plus que la pile : même si aucune famille
n'existe, Qt choisit alors une police à chasse fixe, et les colonnes de valeurs
restent alignées. Une substitution proportionnelle rendrait le multimètre
illisible sans qu'aucune erreur ne soit levée.

**Conséquence :** la correction de taille pour macOS (72 ppp contre 96) vit au
même endroit, et un essai interdit qu'une police soit nommée ailleurs (`C-2C`).

## D-15 — Les paquets se fabriquent depuis Linux, sans machine Windows ni Mac

**Contexte :** livrer un logiciel Python à des utilisateurs qui n'ont ni
Python ni terminal.

**Décision :** un script unique, `packaging/construire.py`, lancé depuis
Debian/Ubuntu/Mint, produit les cinq cibles. Trois mécanismes le permettent :
`pip download --platform` récupère les roues d'un autre système ; Python publie
pour Windows une **distribution embarquable** qu'on place dans le paquet ; et
**NSIS existe sous Linux**, si bien qu'un vrai `.exe` d'installation se
fabrique depuis Debian.

**Ce qui est assumé :** rien n'est signé — une signature Windows coûte un
certificat, une signature Apple exige un compte développeur **et** un Mac. Les
deux systèmes avertiront à la première ouverture ; chaque paquet explique
comment passer outre. Mieux vaut le dire que laisser croire à une garantie
qui n'existe pas.

**macOS fait exception :** on n'y embarque pas l'interpréteur. Apple ne fournit
plus de Python utilisable depuis macOS 12.3, et un CPython redistribué depuis
Linux serait non signé — Gatekeeper le refuserait, et l'application ne
s'ouvrirait pas sans dire pourquoi. Le paquet `.app` utilise donc le Python de
l'utilisateur, embarque toutes les bibliothèques, et montre une vraie fenêtre
s'il manque.

## D-16 — Les paquets Linux créent un environnement Python privé

**Contexte :** faut-il dépendre de `python3-pyside6` ou porter ses propres
bibliothèques ?

**Décision :** un environnement privé dans `/usr/share/phytoscope/venv`, créé
à l'installation à partir des roues embarquées dans le paquet.

**Pourquoi :** PySide6 n'est pas empaqueté par toutes les versions de Debian,
d'Ubuntu ni de Fedora, et sa version y va de 6.2 à 6.7 selon les dépôts. Un
environnement dédié garantit la même chose partout sans toucher au Python du
système — donc sans risquer de casser un autre logiciel.

**Conséquence :** les roues sont téléchargées pour **cinq versions de Python**
(3.9 à 3.13), car une roue de NumPy ne vaut que pour une version mineure et
les distributions visées en livrent de 3.9 à 3.13. Qt y échappe : ses roues
sont « abi3 ». Le script d'après-installation retombe sur le réseau si aucune
roue ne convient, et l'échec n'empêche jamais l'installation (`C-2E`).

## D-17 — La version vit dans un fichier de données, pas dans du code

**Contexte :** le numéro était écrit en Python (`VERSION_MAJOR = 1`…), et
`pyproject.toml` en gardait une copie. Elle a dérivé : elle annonçait encore
1.0.0 alors que le logiciel en était à 1.5.0.

**Décision :** `src/phytoscope/phytoscope/VERSION`, au format
« clé = valeur », est la seule source. Le logiciel le lit au démarrage,
`pyproject.toml` le lit par `dynamic = ["version"]`, la fabrique de paquets le
lit pour estampiller, et `tools/release.py` est le seul à l'écrire.

**Pourquoi dans le paquet Python et non à la racine du dépôt :** un logiciel
installé n'emporte pas le dépôt. Placé là, le fichier suit le logiciel partout
où il va, et la version affichée dans « À propos » est forcément celle du code
qui tourne. Il figure donc dans `package-data`, faute de quoi une roue le
laisserait derrière elle (`C-2L`).

## D-18 — Un générateur par système, et un Makefile pour les enchaîner

**Contexte :** un script unique de 1 100 lignes fabriquait les cinq cibles. Il
devenait difficile à lire, et une erreur dans la partie Windows empêchait de
travailler sur la partie Debian.

**Décision :** `commun.py` porte ce qui ne dépend d'aucun système ; chaque
cible a son script, autonome et lançable seul ; `construire.py` n'est plus
qu'un aiguillage, et un `Makefile` offre `make debian`, `make windows`,
`make tout`.

**Conséquence :** chaque générateur reçoit `--version`, `--release` et
`--sortie`. C'est ce qui permet au Makefile de calculer **une fois** le dossier
horodaté et de l'imposer à tous : sans cela, cinq générateurs lancés à la
suite créeraient cinq dossiers, et les paquets d'une même fabrication seraient
éparpillés (`C-2M`, `C-2N`).

## D-19 — Le format .pkg de macOS est écrit de bout en bout

**Contexte :** l'utilisateur demande un `.pkg`. `pkgbuild` n'existe que sur
macOS, et les deux outils libres qui le remplacent — `xar` et `mkbom` — ne
sont plus empaquetés par Debian ni par Ubuntu.

**Décision :** `macos_pkg.py` écrit les trois formats imbriqués en Python pur :
l'archive **XAR**, la charge **cpio** au format « odc », et la **nomenclature
BOM**, cet arbre binaire dont l'absence fait échouer un paquet par ailleurs
correct. Aucune dépendance, rien à compiler, résultat déterministe.

**Comment on s'assure que c'est juste :** tout ce qui est écrit est relu par le
même module — table XAR réextraite, cpio redéplié, arbre du BOM reparcouru —
et l'on vérifie que les trois décrivent le **même ensemble de fichiers**. Une
charge utile et une nomenclature qui divergent sont la panne classique du
paquet fabriqué à la main : l'installateur copie, puis refuse.

**Ce qui reste incertain :** le paquet n'a jamais été soumis à `installer(8)`.
Il n'y a pas de Mac ici, et le script le dit à chaque fabrication.

## D-20 — Un MSI, et pas InstallShield

**Contexte :** la question a été posée. InstallShield est un produit commercial
de Revenera, sous licence payante, qui ne tourne que sur Windows : il est
inutilisable depuis Debian.

**Décision :** produire ce qu'InstallShield produit — un **MSI** — avec `wixl`,
de msitools, qui existe sous Linux. Le MSI complète l'installateur NSIS sans
le remplacer : NSIS s'installe dans le profil de l'utilisateur **sans droits
d'administration**, ce qui compte en salle de classe ; le MSI s'installe pour
toute la machine et se déploie par stratégie de groupe ou par Intune.

**Détail qui a coûté deux essais :** `wixl` refuse les chemins `Source`
absolus et résout tout depuis son répertoire courant. Il faut donc décrire
l'arborescence en relatif et se placer dans la charge avant de l'appeler. Il
ignore par ailleurs `CompressionLevel` et `WixVariable`, que WiX accepte.

## D-21 — Un certificat auto-signé, et l'on dit ce qu'il ne fait pas

**Contexte :** l'utilisateur demande un certificat pour authentifier les
installateurs. La tentation est d'annoncer « paquets signés » et d'en rester là.

**Décision :** produire un vrai certificat X.509 de signature de code, signer
les installateurs Windows en **Authenticode** et tout le reste en **CMS
détachée**, et écrire noir sur blanc, dans `AUTHENTICITE.txt` livré avec les
paquets, que **ce certificat ne fait taire ni SmartScreen ni Gatekeeper**.

**Pourquoi c'est important :** SmartScreen exige un certificat délivré par une
autorité reconnue, facturé chaque année ; Gatekeeper exige un compte
développeur Apple et un Mac. Laisser croire qu'un certificat auto-signé y
change quelque chose, c'est préparer une déception à la première installation.
Ce que la signature apporte réellement est dit aussi : intégrité vérifiable
avec `openssl` seul, continuité d'origine entre deux versions, et déploiement
sans avertissement pour qui installe le certificat dans son parc.

**Où vivent les clés :** la clé privée dans `~/.local/share/`, en 0600, hors du
dépôt ; une copie de travail dans `certificat/`, que `.gitignore` écarte. Et
l'on précise que `.gitignore` protège de Git, pas d'une sauvegarde.

## D-22 — Un installateur Linux à trois interfaces

**Contexte :** l'installateur `.run` parlait en lignes de texte. L'utilisateur
demande « un affichage graphique comme InstallShield », et une version texte
sur `--tui`.

**Décision :** une **couche d'affichage** (`gabarits/linux/interface.sh`) avec
une seule API — `ui_question`, `ui_licence`, `ui_dossier`, `ui_progres` — et
trois implémentations : zenity ou kdialog (graphique), whiptail ou dialog
(boîtes en mode texte), et des lignes brutes. Le choix est automatique, et
`--gui`, `--tui`, `--texte` l'imposent.

**Pourquoi une couche plutôt que trois scripts :** la logique d'installation
est délicate — détection de Python, environnement virtuel, roues embarquées,
désinstallateur, registre. En avoir trois copies, c'est garantir qu'elles
divergeront. Ici, le reste du script ne sait pas s'il parle à une fenêtre ou à
un terminal.

**Détail qui compte :** les questions d'option sont posées **avant** la copie.
Interrompre une barre de progression pour demander « voulez-vous une icône ? »
est exactement ce qu'on reproche aux installateurs.
