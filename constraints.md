# Contraintes de développement — cahier des charges

**Projet :** *La Musique des Plantes* — ouvrage, hors-série technique, carte
d'acquisition PhytoSense One, micrologiciel RP2350 et logiciel PhytoScope.
**Auteur :** Bretagne Namasté · https://bretagne-namaste.com
**Dernière révision :** 2026-09-18

Ce fichier est la référence : **toute contrainte qui gouverne le développement y
figure, numérotée**, de sorte qu'un être humain comme un agent puisse la citer
(« C-14 ») plutôt que de la paraphraser. Ce qui n'y est pas n'est pas une règle,
mais un usage — et peut être discuté.

> Ordre de préséance en cas de conflit : **déontologie (C-1 à C-9) › mesure
> (C-10 à C-19) › robustesse (C-20 à C-29) › tout le reste.** Une belle
> fonction qui viole C-3 ne se livre pas.

---

## 1. Déontologie — ce qui prime sur tout

| № | Contrainte |
|---|---|
| **C-1** | Rien de ce que produit le dispositif n'est une **traduction** de la plante. Sonification et mode vocal sont des correspondances réglables, jamais des interprétations. |
| **C-2** | Toute règle de correspondance est **affichée dans l'interface** et **consignée dans le fichier de séance**. Une règle invisible est interdite. |
| **C-3** | Chaque sortie interprétée (note, énoncé) porte sa **justification chiffrée** : les valeurs mesurées qui l'ont déclenchée. |
| **C-4** | Les quatre registres de l'ouvrage restent distincts et balisés : 🔬 point scientifique, 🌿 regard énergétique, ⚠️ limites, ✨ expérience intérieure. Aucune affirmation spirituelle présentée comme un fait scientifique. |
| **C-5** | Le vocabulaire emprunté à d'autres champs est employé **avec son avertissement** : pas de « formants » pour une plante (elle n'a pas de conduit vocal), pas de « décodage », pas de « langage ». |
| **C-6** | Les ambiguïtés des documents d'origine sont **signalées**, jamais lissées. |
| **C-7** | Aucune affiliation commerciale, aucun lien commissionné, aucune marque présentée comme partenaire. |
| **C-8** | Tout ce qui est prononcé ou écrit reste **sur la machine** : aucune synthèse vocale en ligne, aucun envoi de texte ou de signal à un service distant. |
| **C-9** | Les dictionnaires du mode vocal sont des **points de départ**, modifiables par l'utilisateur ; le logiciel ne prétend jamais qu'ils disent la plante. |

## 2. Mesure — ce qui fait la valeur de l'appareil

| № | Contrainte |
|---|---|
| **C-10** | Les grandeurs sont **étalonnées et exprimées en unités physiques** (volts, ohms, hertz, secondes), jamais en unités arbitraires. |
| **C-11** | Le facteur de conversion pleine échelle est **inscrit dans chaque fichier** produit ; un WAV sans son échelle est inexploitable. |
| **C-12** | La ligne de base est **suivie mais jamais supprimée** : on montre la dérive, on ne la cache pas. |
| **C-13** | Le seuil de détection est exprimé en **écarts-types** du signal courant, doublé d'une **amplitude minimale absolue** — sans quoi on sonifie le bruit de fond. |
| **C-14** | Les constantes empruntées au traitement de la parole sont **transposées d'après la fréquence d'échantillonnage réelle**, jamais recopiées. |
| **C-15** | Toute représentation affiche **ce qu'elle suppose** et **ce qu'elle ne permet pas de conclure**. |
| **C-16** | Les pertes sont **comptées et affichées** (blocs jetés, énoncés abandonnés, écrêtages), jamais silencieuses. |
| **C-17** | L'horodatage provient du matériel quand il existe (TCXO, compteur d'échantillons) ; sa provenance est affichée. |
| **C-18** | Aucune donnée mesurée n'est modifiée pour « faire joli » : les filtres sont déclarés, réglables et réversibles. |
| **C-19** | Les fichiers de séance sont **ouverts et relisibles sans le logiciel** : WAV, CSV, JSON. Rien n'est enfermé. |
| **C-1A** | Une grandeur **déduite** est annoncée comme telle, avec sa relation et son hypothèse. La résistance équivalente est un **majorant** tiré de `R = Sᵥ / 4kT` : elle ne se présente jamais comme une mesure d'impédance, que la carte ne fait pas. |
| **C-1B** | Les grandeurs de bruit sont calculées sur le **signal brut**, avant réjecteur et passe-bas. Filtrer avant de mesurer le bruit revient à mesurer son propre filtre. |
| **C-1C** | Une statistique qui n'a pas assez d'échantillons **se tait** plutôt que d'afficher un chiffre. Le facteur de Fano n'apparaît pas en dessous de dix événements. |

## 3. Robustesse — ce qui permet une séance de huit heures

| № | Contrainte |
|---|---|
| **C-20** | **Aucun composant lent sur le chemin des données.** L'interface lit un instantané publié par le moteur ; elle ne calcule rien. |
| **C-21** | Le logiciel **démarre toujours**, même sans matériel : repli automatique sur le générateur interne. |
| **C-22** | Une dépendance facultative absente **limite** le logiciel, elle ne l'empêche pas de démarrer. Les contrôles avant vol distinguent paquet absent, paquet cassé et environnement verrouillé. |
| **C-23** | **Ctrl+C doit toujours aboutir**, interface graphique comprise : séance close, réglages sauvés, chien de garde si l'arrêt se bloque, second Ctrl+C immédiat. SIGTERM de même. |
| **C-24** | Une **option de ligne de commande vaut pour la séance**, jamais pour toujours : elle n'est pas écrite dans le fichier de réglages. |
| **C-25** | Un fichier de réglages **absent, incomplet ou corrompu** ne doit jamais empêcher le démarrage. |
| **C-26** | L'espace disque est **surveillé pendant l'enregistrement** ; la séance est close proprement avant saturation, avec alerte préalable. |
| **C-27** | Un changement de réglage ne détruit que ce qu'il doit : la mémoire de signal n'est vidée que si la chaîne de traitement change réellement. |
| **C-28** | Les fils secondaires ne touchent **jamais** directement à l'interface graphique : signaux Qt uniquement. |
| **C-29** | Toute écriture de fichier est **atomique ou refermable** : un enregistrement interrompu reste exploitable. |
| **C-2A** | Le journal est **consultable depuis le logiciel** (`Ctrl+L`) : son emplacement est écrit en toutes lettres, son contenu se complète en direct, et une copie peut être enregistrée où l'on veut — archives de rotation comprises. Aucun terminal n'est nécessaire pour signaler un incident. |
| **C-2B** | La surveillance d'un fichier est **incrémentale** et s'arrête quand la fenêtre se ferme : on ne relit jamais tout, on ne réveille jamais le disque pour une fenêtre invisible. |
| **C-2C** | **Rien ne se nomme en dur quand le système peut en décider autrement** : ni police (pile de replis et genre, `ui/polices.py`), ni chemin (`os.path.join`), ni séparateur, ni encodage (`open()` porte toujours `encoding=`). Des essais le vérifient. |
| **C-2D** | Les **identifiants USB du logiciel suivent le micrologiciel**, jamais l'inverse. Le couple appartient à la plage libre de pid.codes (`0x1209`) ; un essai lit `usb_descriptors.c` et compare. |
| **C-2E** | Une **dépendance facultative qui échoue n'empêche pas l'installation du reste** : elle vit dans `requirements-optionnel.txt`, installé séparément. |
| **C-2F** | Un **nom de fichier est translittéré en ASCII** avant d'atteindre le disque : APFS normalise en NFD, Windows réserve `CON`, `NUL`, `COM1`… et supprime les points finaux. Le nom lisible reste en Unicode dans les métadonnées. |
| **C-2G** | Le logiciel **ouvre l'entrée audio au débit que le périphérique accepte** et décime en logiciel : CoreAudio et WASAPI refusent 250 Hz. Le rééchantillonnage ne perd aucun échantillon. |
| **C-2H** | Les **paquets d'installation se fabriquent depuis Debian/Ubuntu/Mint**, d'une seule commande (`packaging/construire.py`), pour les cinq cibles. Aucune machine Windows ni Mac n'est nécessaire. |
| **C-2I** | **L'installateur Windows n'exige rien de la machine cible**, Python compris. Les paquets Linux n'exigent que ce que la distribution fournit d'office. |
| **C-2J** | Aucun paquet n'est signé, et **chacun le dit** : le `LISEZ-MOI` explique l'avertissement du système et comment passer outre. On n'entretient pas l'illusion d'une garantie qu'on ne donne pas. |
| **C-2K** | Une désinstallation **ne touche jamais aux réglages ni aux séances** de l'utilisateur. Elle retire ce que l'installation a posé, rien de plus. |
| **C-2L** | **La version vit dans un seul fichier de données**, `phytoscope/VERSION`, à l'intérieur du paquet Python. Le logiciel, la fabrique de paquets, `pyproject.toml` et `tools/release.py` le lisent tous ; seul ce dernier l'écrit. Aucune copie nulle part. |
| **C-2M** | **Un générateur de paquets par système**, autonome et lançable seul, plus un `Makefile` qui les enchaîne. Une panne sur l'un n'emporte pas les autres. |
| **C-2N** | Chaque fabrication a **son dossier horodaté** `build/paquets/<version>-<AAAAMMJJ-HHMM>/<Système>/`, et reçoit sa version en argument : deux fabrications d'une même version ne peuvent pas s'écraser, et l'on sait au nom près ce qu'on diffuse. |
| **C-2O** | Chaque paquet est accompagné de **son empreinte SHA-256** et, dans son dossier, de `readme.txt`, `install.txt`, `manuel.txt`, `licence.txt` et `changelog.txt`. Un dossier recopié seul sur un serveur reste compréhensible. |
| **C-2P** | **L'attribution vit dans un seul fichier**, `phytoscope/AUTEURS` : le logiciel, la fabrique de paquets et le sujet du certificat le lisent tous. Éditeur et auteur sont distingués — l'atelier qui publie n'est pas la personne qui a écrit. |
| **C-2Q** | Tous les paquets sont **signés** : Authenticode pour Windows, CMS détachée ailleurs. Le certificat étant **auto-signé**, chaque paquet dit explicitement que la signature prouve l'intégrité et la continuité d'origine, et qu'elle **ne fait taire ni SmartScreen ni Gatekeeper**. |
| **C-2R** | La **clé privée ne quitte jamais** `~/.local/share/` ; sa copie de travail est écartée par `.gitignore`, et la documentation précise que `.gitignore` protège de Git, pas d'une sauvegarde. |
| **C-2S** | Chaque installateur **demande** ce qui engage l'utilisateur — icône sur le Bureau, lancement en fin d'installation — et **fournit un désinstallateur**. Les questions sont posées avant la copie, jamais au milieu d'une barre de progression. |
| **C-2T** | Aucune désinstallation n'efface **réglages ni séances** : elle retire ce que l'installation a posé, dit où sont les données, et laisse l'utilisateur décider. |
| **C-2U** | L'installateur Linux offre **trois interfaces** — graphique, boîtes en mode texte, lignes brutes — derrière **une seule** implémentation de la logique d'installation. Trois copies de cette logique divergeraient. |

## 4. Langue et accessibilité

| № | Contrainte |
|---|---|
| **C-30** | La langue source est le **français** ; les clés de traduction sont les phrases françaises elles-mêmes. |
| **C-31** | **Au premier lancement, l'interface est en français**, quelle que soit la locale du système. Aucune détection automatique. |
| **C-32** | Une traduction manquante retombe sur le français ; jamais d'identifiant nu à l'écran. |
| **C-33** | Ajouter une langue ne demande **aucune modification du code** : un fichier JSON déposé dans `phytoscope/langues/`. |
| **C-34** | L'inventaire des libellés est produit **par analyse du code**, pas tenu à la main ; un test échoue si un catalogue livré est incomplet. |
| **C-35** | Les langues à écriture de droite à gauche inversent toute la mise en page. |
| **C-36** | Thème à contraste renforcé de niveau AAA et échelle de texte de 0,8 à 2,0 disponibles en permanence. |

## 5. Technique logicielle

| № | Contrainte |
|---|---|
| **C-40** | **Python 3 + PySide6 + NumPy**. Aucune dépendance obligatoire au-delà. Pas de SciPy : les coefficients de filtre sont calculés à la main. |
| **C-41** | Le logiciel fonctionne sur **GNU/Linux, Windows et macOS**, sans code spécifique à une distribution. |
| **C-42** | Tout le code, les commentaires et les docstrings sont **en français**, avec la typographie française (espaces insécables, guillemets « »). |
| **C-43** | Chaque module explique **pourquoi** il est écrit ainsi, pas seulement ce qu'il fait. Un commentaire qui paraphrase le code est à supprimer. |
| **C-44** | Les motifs de conception employés sont **nommés** (stratégie, observateur, commande, objet-valeur). |
| **C-45** | Les fichiers générés (`A0b-codes.html`, `_bom-table.html`, `_sbom-table.html`, `pdf-src/_book.html`, `pdf-src/_carte-*.html`) **ne se modifient jamais à la main**. |
| **C-46** | La nomenclature logicielle (SBOM, CycloneDX 1.5) est produite **par introspection des modules réellement importables**, jamais recopiée du fichier de dépendances. |
| **C-47** | Les tests sont exécutables sans matériel et sans réseau : `make test`. Aucun test ne doit dépendre d'une carte son. |
| **C-48** | Une vérification visuelle (capture d'écran hors écran) accompagne toute modification d'interface notable. |

## 6. Matériel et micrologiciel

| № | Contrainte |
|---|---|
| **C-50** | Cible : **RP2350**, Pico SDK ≥ 2.0, TinyUSB. Le flux de mesure passe par l'USB en **classe audio 2.0**, sans pilote. |
| **C-51** | Alimentation **sur pile ou batterie exclusivement**. Jamais de raccordement au secteur, jamais de trajet thoracique chez un porteur d'implant. |
| **C-52** | Isolement galvanique entre l'étage de mesure et l'hôte ; la garde et le blindage sont documentés. |
| **C-53** | Le matériel est publié sous **CERN-OHL-P v2**, le logiciel et le micrologiciel sous **MIT**. |
| **C-54** | Chaque document, chaque planche et la carte elle-même portent **l'auteur et l'adresse du site** — un plan anonyme dès la deuxième photocopie est un plan perdu. |
| **C-55** | La construction du micrologiciel ne demande **aucun privilège administrateur** : `_make_.sh --deps` installe SDK et chaîne ARM dans le dossier personnel. |

## 7. Documents

| № | Contrainte |
|---|---|
| **C-60** | Les PDF sont **intégralement reproductibles** depuis les sources : fragments HTML + CSS + planches générées par script déterministe. |
| **C-61** | Les planches sont **dessinées par programme** (`gen.py`, `gen_carte.py`), jamais importées d'un éditeur graphique. |
| **C-62** | Sommaire cliquable, signets, en-têtes, pagination et métadonnées PDF complètes (auteur, éditeur, contact, licence). |
| **C-63** | Toute affirmation technique est **sourcée** : brevet, article à comité de lecture, fiche technique ou code public. |
| **C-64** | Les compteurs annoncés (pages, chapitres, planches, tests) sont **vérifiés après reconstruction**, jamais estimés. |

## 8. Hors périmètre — ce qu'on ne fera pas

- Aucune **reconnaissance d'émotion** ou d'« intention » végétale, sous quelque nom que ce soit.
- Aucun **apprentissage automatique** qui produirait une sortie inexplicable : tout ce qui sort doit pouvoir être justifié ligne à ligne.
- Aucune **synthèse vocale en ligne**, aucun service distant, aucune télémétrie.
- Aucune **boutique**, aucun lien affilié, aucune capture d'adresse de courriel.
- Aucun **diagramme de l'œil** sur le signal végétal : sans horloge ni alphabet, ce serait une image sans mesure (le nom reste réservé au lien numérique et aux montages à période connue).
