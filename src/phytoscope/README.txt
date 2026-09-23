================================================================================

   PhytoScope 1.4.0 « Le cadran et l'empreinte »
   Listen to, measure and record plant signals

   Bretagne Namasté
   https://bretagne-namaste.com  ·  contact@bretagne-namaste.com
   Licence MIT — voir LICENSE.txt

================================================================================


TABLE DES MATIÈRES
------------------

   1.  Ce que fait ce logiciel, et ce qu'il ne fait pas
   1 bis. La langue de l'interface, et comment en ajouter une
   2.  Installation rapide
   3.  Installation détaillée, par système
   4.  Premier lancement
   5.  Les dix onglets
   6.  L'assistant d'auto-configuration
   7.  Le format des séances enregistrées
   8.  Utilisation sans interface graphique
   9.  Brancher un autre matériel que la carte PhytoSense
  10.  Dépannage
  11.  Développement et publication
  12.  Crédits


1. CE QUE FAIT CE LOGICIEL, ET CE QU'IL NE FAIT PAS
--------------------------------------------------

PhytoScope lit un signal électrique mesuré sur une plante, l'affiche comme le
ferait un oscilloscope, le chiffre comme le ferait un multimètre, l'enregistre
avec un horodatage exact, et propose d'en faire une écoute musicale.

Il ne traduit pas la plante. Il n'interprète pas. Il mesure une grandeur
physique — une tension ou une impédance — et propose une correspondance
sonore dont chaque règle est affichée, réglable et consignée dans le fichier
de séance. Cette distinction est le sujet du document qui accompagne ce
logiciel : « La Carte PhytoSense — conditionnement et interface USB ».


1 BIS. LA LANGUE DE L'INTERFACE, ET COMMENT EN AJOUTER UNE
----------------------------------------------------------

Au premier lancement, l'interface est en FRANÇAIS — quelle que soit la langue
du système. Le logiciel ne consulte pas la locale : l'ouvrage, les planches et
le dictionnaire du mode vocal sont en français, et une interface qui ne
correspondrait pas à sa documentation coûterait plus cher qu'elle ne
rapporterait. Le choix fait ensuite dans les réglages est conservé.

Le logiciel est écrit en français, et traduit en dix autres langues :

   en   English (US)        it   Italiano          ja   日本語
   es   Español             id   Bahasa Indonesia  ko   한국어
   pt   Português           ru   Русский           ar   العربية
                            zh   中文

Le choix se fait dans Réglages → Interface → Langue, ou au lancement :

   python3 run.py --lang ja

Le changement prend effet au redémarrage : le logiciel propose de relancer.
En arabe, toute la mise en page est inversée.

AJOUTER UNE LANGUE — sans écrire une ligne de code :

   1. Réglages → Interface → « Écrire un modèle de traduction… ».
      Le fichier produit contient tous les libellés du logiciel, les
      traductions déjà faites conservées, les autres laissées vides.

   2. Traduisez-le avec un éditeur de texte. Les valeurs laissées vides
      s'afficheront en français : un catalogue à moitié rempli reste
      parfaitement utilisable.

   3. Déposez le fichier dans phytoscope/langues/ sous le nom <code>.json —
      par exemple « nl.json » pour le néerlandais — et complétez son bloc
      « _langue » (nom, nom_fr, direction : ltr ou rtl).

   4. Relancez : la langue apparaît dans la liste.

Les mêmes opérations en ligne de commande :

   python3 tools/i18n.py --couverture      état de chaque traduction
   python3 tools/i18n.py --modele nl       crée ou complète langues/nl.json
   python3 tools/i18n.py --inutiles nl     les clés que le code n'emploie plus

Ce qui est traduit : la totalité de l'interface, les infobulles, les messages
d'état, les noms des timbres, des gammes et des profils, les textes de l'aide.
Ce qui ne l'est pas : le dictionnaire du mode vocal, qui est un fichier à part
et que chacun écrit dans la langue de son atelier (onglet Parole).


2. INSTALLATION RAPIDE
----------------------

   Dans un terminal, depuis le répertoire de ce fichier :

       make install
       make demo

   La première commande crée un environnement virtuel Python et y installe
   les dépendances. La seconde lance le logiciel avec une plante simulée :
   aucun matériel n'est nécessaire pour découvrir l'interface.

   Sous Windows en invite de commandes native, remplacez « make » par
   « make.bat » :

       make.bat install
       make.bat demo

   Si quelque chose ne va pas :

       make doctor

   affiche ce qui est installé, ce qui manque, et la commande à lancer.


3. INSTALLATION DÉTAILLÉE, PAR SYSTÈME
--------------------------------------

Prérequis commun : Python 3.9 ou plus récent.

   GNU/LINUX (Debian, Ubuntu, Mint)

       sudo apt install python3 python3-venv python3-pip \
                        libportaudio2 libasound2-dev librtmidi-dev \
                        libxcb-cursor0 libxkbcommon-x11-0
       make install

       Les trois derniers paquets sont exigés par Qt 6 et par PortAudio.
       Sans « libxcb-cursor0 », Qt refuse de démarrer avec un message peu
       explicite ; c'est la cause la plus fréquente d'échec sous Linux.

   GNU/LINUX (Fedora)

       sudo dnf install python3 python3-pip portaudio alsa-lib-devel \
                        rtmidi-devel xcb-util-cursor
       make install

   MACOS

       brew install python portaudio
       make install

       À la première ouverture du micro ou de l'entrée audio, macOS demande
       une autorisation. Elle est indispensable : l'entrée de la carte est
       vue comme un microphone.

   WINDOWS 10 ET 11

       Installez Python depuis python.org en cochant « Add python.exe to
       PATH », puis :

           make.bat install

       Rien d'autre n'est nécessaire : les roues Python embarquent Qt,
       PortAudio et RtMidi. La carte PhytoSense est reconnue comme
       périphérique audio USB standard, sans pilote.

   SANS MAKE, PARTOUT

       python3 -m venv .venv
       .venv/bin/python -m pip install -r requirements.txt     (Linux, macOS)
       .venv\Scripts\python -m pip install -r requirements.txt (Windows)
       .venv/bin/python run.py


4. PREMIER LANCEMENT
--------------------

   make run

Au démarrage, le logiciel cherche une source dans cet ordre : carte
PhytoSense déclarée en classe audio, carte détectée sur un port série,
entrée audio explicitement demandée, puis générateur interne. Il démarre
donc toujours, même sur une machine nue — c'est la condition pour qu'un
atelier ne commence pas par une séance de dépannage.

Le bandeau du bas ne ment jamais. Il affiche l'état réel de l'acquisition,
la source utilisée, la durée écoulée, l'origine de l'horloge, l'état de
saturation, la dérive en microvolts par minute, le nombre d'événements et
l'état de l'enregistrement.

Raccourcis clavier — la même liste figure dans l'aide (F1), où elle est
vérifiée par le programme à chaque ouverture :

   PENDANT LA SÉANCE

      Ctrl+R          démarrer ou arrêter l'enregistrement
      Ctrl+M          poser un marqueur horodaté dans la séance
      Ctrl+K          couper le son sans interrompre la mesure ni
                      l'enregistrement
      Ctrl+E          garder sur le disque le signal qui vient de passer
      Ctrl+0          ramener tous les tracés de l'onglet au cadrage d'origine
      Ctrl+.          silence : coupe immédiatement toutes les notes en cours
      Ctrl+A          ouvrir l'assistant d'auto-configuration

   LA FENÊTRE

      F1              l'aide
      Maj+F1          fenêtre « À propos » : version, composants installés,
                      rapport d'environnement copiable
      Ctrl+Tab        onglet suivant
      Ctrl+Maj+Tab    onglet précédent
      Tab / Maj+Tab   commande suivante, commande précédente
      Espace          cocher, décocher, actionner la commande au focus
      Échap           fermer la fenêtre de dialogue sans rien appliquer
      Ctrl+Q          quitter en refermant proprement la séance en cours

   ONGLET TRACEUR — LIGNE DE COMMANDE

      Entrée          exécuter la commande saisie
      Flèche haut     rappeler la commande précédente
      Flèche bas      revenir à la commande suivante

   CHAMPS DE SAISIE, LISTES ET TABLEAUX

      Ctrl+C, Ctrl+V  copier, coller
      Ctrl+A          tout sélectionner, dans un champ de texte
                      (ailleurs : auto-configuration)
      Flèches         se déplacer dans une liste, un tableau, une valeur
      Page préc./suiv. faire défiler d'un écran

   DEPUIS LE TERMINAL

      Ctrl+C          interrompt le logiciel, interface graphique comprise :
                      la séance en cours est close, les réglages sauvés, puis
                      le programme s'arrête. Un second Ctrl+C n'attend pas.
                      Le logiciel se termine de lui-même au bout de quelques
                      secondes si l'arrêt propre se bloque.
      Ctrl+Z          suspend le processus (Unix). L'acquisition s'arrête
                      aussi : « fg » la reprend, mais le signal de
                      l'intervalle est perdu.


5. LES DIX ONGLETS
------------------

   OSCILLOSCOPE   Le signal dans le temps. Fenêtre de 5 s à 1 h, sensibilité
                  de 2 µV à 10 mV par division, affichage au choix du signal
                  filtré ou du signal brut — ce dernier est indispensable
                  pour diagnostiquer un problème de contact. Cinq boutons de
                  marquage rapide posent une annotation horodatée.

   MULTIMÈTRE     Les chiffres ET les aiguilles. Quatre vumètres — tension,
                  bruit efficace, crête à crête, dérive — avec la balistique
                  des appareils à cadre mobile : l'aiguille rejoint la valeur
                  en 150 ms, une mémoire de crête retient les pointes brèves,
                  et l'échelle saute par paliers 1–2–5. Le nombre se recopie
                  dans un carnet ; l'aiguille se lit d'un coup d'œil et montre
                  le mouvement, qui est ce qu'on guette devant une plante.

                  Dessous : le diagnostic de contact, le journal des mesures,
                  et l'EMPREINTE DU MONTAGE — huit descripteurs qui
                  caractérisent l'ensemble plante + électrodes + substrat +
                  câble + carte, et un registre des montages connus pour les
                  reconnaître d'une séance à l'autre.

                  Cette empreinte N'IDENTIFIE PAS UNE PLANTE, et l'interface
                  le dit : deux mesures du même végétal à deux jours
                  d'intervalle diffèrent souvent plus que deux végétaux
                  voisins le même après-midi. Elle sert à retrouver un
                  montage, à voir un contact qui se dégrade, et à comparer
                  deux séances avant de les interpréter.

   ANALYSEUR      Le spectre. C'est ici qu'on voit immédiatement si le
                  montage capte le réseau : un pic à 50 Hz signifie qu'il
                  faut revoir le blindage et la garde, pas activer le
                  réjecteur.

   DESCRIPTEURS   Six façons de regarder le même signal, et ce que chacune
                  vaut ici :

                    · forme d'onde — rien n'y est calculé, donc rien perdu ;
                    · FFT — les périodicités et le réseau, mais le signal est
                      supposé stationnaire, ce qu'il n'est jamais longtemps ;
                    · ondelettes de Morlet — la mieux adaptée : elle situe
                      dans le temps ce que la FFT se contente de moyenner ;
                    · MFCC — compression du spectre, utile pour comparer deux
                      séquences, non pour mesurer quoi que ce soit d'une
                      plante : l'échelle de Mel décrit l'oreille humaine ;
                    · prédiction linéaire — enveloppe spectrale et
                      résonances. Ce ne sont pas des formants : une plante n'a
                      pas de conduit vocal. Ces résonances sont celles de
                      l'électrode, du milieu et de la carte ;
                    · cepstre — les périodicités lentes qu'une dérive masque.

                  Les constantes des outils de la parole sont transposées
                  d'après la fréquence d'échantillonnage réelle, jamais
                  recopiées : une trame de MFCC dure ici huit secondes.

   ÉCOUTE         Le choix musical : timbre, gamme, tonique, étendue,
                  densité, réverbération, bourdon. Le journal des notes
                  jouées indique pour chacune la règle qui l'a produite.

   PAROLE         Le mode vocal : un dictionnaire de mots au lieu d'une
                  gamme. Six registres, chacun rattaché à un axe mesuré —
                  le verbe suit le sens de la pente, l'adverbe l'amplitude en
                  écarts-types, la circonstance le temps écoulé, la
                  qualification le centre de gravité spectral. Quatre
                  grammaires, du mot unique à la phrase complète.

                  Ce n'est pas une traduction, et l'onglet le rappelle en
                  permanence. Les mots sont ceux du dictionnaire choisi : le
                  modifier, le traduire, en écrire un clinique ou un poétique
                  est l'usage normal — c'est un simple fichier JSON, et le
                  bouton « Écrire un modèle… » en produit un à remplir.

                  Les énoncés peuvent être prononcés à voix haute. La
                  synthèse est cherchée dans cet ordre : pyttsx3, la voix du
                  système (macOS, Windows), espeak-ng. Tout se passe hors
                  ligne : aucun texte ne quitte la machine. Si rien n'est
                  installé, les énoncés restent écrits et enregistrés.

   TRACEUR        Un gnuplot intégré. Ligne de commande et panneau de
                  réglages agissent sur le même état. Neuf sources : signal,
                  signal brut, spectre, densité en V/racine de hertz,
                  histogramme, autocorrélation, variance d'Allan, événements,
                  dernier bloc échantillonné. Exportation en PNG, SVG, données
                  ASCII et script gnuplot.

                  Quelques commandes :
                      plot densite with lines
                      set logscale xy
                      set xrange [0.01:100]
                      export png spectre.png
                      help

   BIBLIOTHÈQUE   Deux pages, qui ne gardent pas la même chose.

                  SÉANCES — l'archive : un répertoire complet, décidé,
                  qui dure. Relecture accélérée jusqu'à six cents fois.

                  ÉCHANTILLONS — le carnet de croquis : Ctrl+E, et la
                  dernière minute écoulée est sur le disque. Rien à
                  préparer, rien à arrêter — le logiciel tient dix minutes
                  de signal en mémoire, et l'essentiel arrive souvent avant
                  qu'on ait pensé à enregistrer. Un échantillon est un WAV
                  plus un petit JSON de même nom ; le WAV s'ouvre dans
                  Audacity, le JSON porte la pleine échelle en volts, la
                  plante, le lieu et les réglages.

                  « Charger un enregistrement… » rejoue un fichier pris
                  n'importe où : un échantillon, le signal.wav d'une séance,
                  ou un WAV reçu d'un correspondant.

                  Les deux se rejouent DANS LE MOTEUR : filtres, détection,
                  descripteurs, musique et mode vocal fonctionnent comme
                  devant une plante vivante. On règle ainsi une sonification
                  le soir, sur la séance du matin. Pendant une relecture,
                  L'ACQUISITION EN DIRECT EST SUSPENDUE — la source est
                  réellement arrêtée, et un bandeau le rappelle en
                  permanence. « Revenir en direct » rend la main à la plante
                  branchée.

   DIAGNOSTIC     Quatre pages. Lien USB : inventaire par identifiants
                  constructeur et produit, reconnaissance des cartes connues,
                  surveillance des décrochages, capture des trames dans un
                  fichier. Échantillonnage : modes continu, bloc et déclenché,
                  décimation, moyennage, fenêtres. Sortie sonore :
                  amplification, compression, bips, essai du haut-parleur,
                  et état des synthèses vocales installées.
                  Journal : niveau réglable à chaud, de ERROR à DEBUG.

   RÉGLAGES       Sept pages, de l'assistant à la page « Expert ».


6. L'ASSISTANT D'AUTO-CONFIGURATION
-----------------------------------

Onglet « Réglages », page « Assistant », ou Ctrl+A.

L'assistant écoute le signal pendant la durée choisie (douze secondes par
défaut), puis mesure :

   · le plancher de bruit efficace, après filtrage ;
   · la présence et la fréquence du réseau, 50 ou 60 Hz ;
   · la dérive continue, en microvolts par minute ;
   · une éventuelle saturation de l'entrée.

Il en déduit un jeu complet de réglages — fréquences de coupure, réjecteur,
seuil de détection, amplitude minimale, densité musicale et gain matériel —
et affiche la justification de chacun. Rien n'est appliqué tant que vous
n'avez pas cliqué sur « Appliquer les réglages proposés ».

Une auto-configuration opaque produit des utilisateurs qui ne comprennent
pas leur instrument. Celle-ci explique tout ce qu'elle fait.


7. LE FORMAT DES SÉANCES ENREGISTRÉES
-------------------------------------

Une séance est un répertoire, pas un fichier :

   2026-09-17_140233_ficus/
   ├── seance.json        métadonnées, réglages complets, étalonnage
   ├── signal.wav         signal brut, 24 bits, une piste par voie
   ├── musique.wav        rendu sonore
   ├── evenements.csv     un événement par ligne
   ├── notes.csv          une note par ligne, avec la règle appliquée
   ├── enonces.csv        un énoncé par ligne, si le mode vocal est actif :
   │                      le texte, les quatre axes mesurés, la grammaire,
   │                      le dictionnaire et la règle appliquée
   └── marqueurs.csv      annotations posées pendant la séance

   echantillons/          les captures rapides (Ctrl+E), à côté des séances
   ├── 2026-09-18_101530_ficus.wav    le signal, ouvrable dans Audacity
   └── 2026-09-18_101530_ficus.json   cadence, pleine échelle, plante, réglages

Ce choix a une raison : dans dix ans, on veut pouvoir ouvrir ce répertoire
et comprendre sans ce logiciel. Le WAV s'ouvre dans Audacity, les CSV dans
un tableur, le JSON dans un éditeur de texte. Rien n'est enfermé.

Le facteur de conversion pleine échelle est consigné dans seance.json :
sans lui, le WAV serait joli mais inexploitable.

Emplacement par défaut :

   Linux    ~/.local/share/phytoscope/seances
   macOS    ~/Documents/PhytoScope
   Windows  %USERPROFILE%\Documents\PhytoScope


7 bis. LE SON : AMPLIFICATION, COMPRESSION, BIPS
------------------------------------------------

Une plante produit des événements rares et peu dynamiques : sur les
haut-parleurs d'un portable, dans une salle, le rendu est inaudible si l'on
se contente d'un gain. L'étage de sortie traite donc le problème comme une
console de sonorisation.

   Gain               −60 à +12 dB, réglable à chaud depuis la barre d'outils
   Amplification      0 à +36 dB supplémentaires
   Présence           0 à +18 dB entre 1 et 4 kHz, là où l'oreille est la plus
                      sensible et où un petit haut-parleur rend le mieux
   Compresseur        seuil et rapport réglables, rattrapage automatique
   Limiteur           garantit qu'aucun échantillon ne dépasse la pleine échelle
   Bips               repère court à chaque événement, et grave en cas de
                      saturation — précieux quand on regarde ailleurs

Le bouton « Essai HP » de la barre d'outils émet un kilohertz pendant une
demi-seconde : c'est la façon la plus rapide de savoir si le son sort.

La touche Ctrl+K coupe le son sans rien interrompre : la mesure et
l'enregistrement continuent.


7 ter. LE JOURNAL ET LA MISE AU POINT
--------------------------------------

Par défaut, seules les erreurs sont journalisées, dans un fichier :

   Linux    ~/.config/phytoscope/phytoscope.log
   macOS    ~/Library/Application Support/PhytoScope/phytoscope.log
   Windows  %APPDATA%\PhytoScope\phytoscope.log

Le niveau se change à chaud dans l'onglet Diagnostic, ou au lancement :

   python3 run.py --log-level debug --log-console
   python3 run.py --debug              (équivaut à debug + outils bas niveau)
   python3 run.py --debug-usb          (diagnostic USB au démarrage)
   python3 run.py --capture-frames     (enregistre les trames reçues)

La capture des trames écrit un fichier horodaté dans le répertoire des
captures, en texte par défaut — donc lisible immédiatement.


8. UTILISATION SANS INTERFACE GRAPHIQUE
---------------------------------------

Pour une séance longue, sur une machine sans écran, ou dans un script :

   python3 run.py --headless --record --duration 7200

Options utiles :

   --simulation          force le générateur interne
   --device NOM          choisit l'entrée audio ou le port série
   --rate 250            fréquence d'échantillonnage en hertz
   --theme contraste     thème à contraste renforcé
   --lang ja             langue de l'interface (fr, en, es, pt, it, id, ru,
                         zh, ja, ko, ar, ou toute autre présente dans
                         phytoscope/langues/)

Ces options valent POUR LA SÉANCE EN COURS seulement : elles ne sont jamais
écrites dans le fichier de réglages. Lancer une fois « --simulation » pour une
démonstration ne laisse donc pas le logiciel en simulation pour toujours. Pour
qu'un choix soit permanent, faites-le dans l'onglet Réglages.
   --settings FICHIER    charge un fichier de réglages précis
   --version             affiche la version et quitte
   --check               contrôles avant vol, puis sortie
   --install-missing     installe les paquets Python manquants
   --log-level NIVEAU    error (défaut), warning, info, debug


9. BRANCHER UN AUTRE MATÉRIEL QUE LA CARTE PHYTOSENSE
-----------------------------------------------------

Le logiciel n'exige pas la carte décrite dans le document compagnon.

   MONTAGE À NE555 (MIDI Sprout, Biotron, montages publiés sur GitHub)
   Réglez la source sur « Port série » et indiquez le port. Le logiciel
   accepte le format texte : une valeur décimale par ligne, ce que produit
   la quasi-totalité des croquis Arduino publiés.

   CARTE DU COMMERCE À SORTIE AUDIO
   Réglez la source sur « Entrée audio quelconque » et choisissez le
   périphérique. Renseignez le facteur « volts par unité source » dans la
   page Acquisition, sinon les valeurs affichées seront relatives.

   AUCUN MATÉRIEL
   Réglez la source sur « Générateur interne ». Le signal produit est
   statistiquement crédible : dérive lente, bruit en 1/f, potentiels
   d'action occasionnels, ronflette du réseau. Il sert à préparer un
   atelier, à tester l'enregistrement et à régler la sonification.


10. DÉPANNAGE
-------------

   « Le logiciel ne démarre pas »
      make doctor  — puis suivez la ligne indiquée.

   « qt.qpa.plugin: could not load the Qt platform plugin xcb »
      Sous Linux : sudo apt install libxcb-cursor0 libxkbcommon-x11-0

   « Aucun son »
      Vérifiez que sounddevice est installé (make doctor) et que l'onglet
      Écoute n'est pas en mode « couper le son ». Sous Linux, vérifiez que
      PortAudio voit bien une sortie : la page Expert des réglages en donne
      la liste.

   « Des lignes ALSA lib ... underrun occurred défilent dans le terminal »
      Elles ne devraient plus apparaître : ces messages viennent de la
      bibliothèque C d'ALSA, et le logiciel les détourne vers son journal, où
      ils sont consultables au niveau DEBUG. Pour les revoir dans le terminal :
      run.py --verbose-audio

      S'ils signalent un vrai décrochage du son — craquements audibles —,
      l'onglet Diagnostic / Sortie sonore en donne le compte et permet
      d'augmenter la taille de bloc et la latence. Les valeurs recommandées
      sont 4096 échantillons et 0,5 s ; sur une machine très chargée, passez
      à 8192 et 1,0 s. Le retard ajouté est sans conséquence : la plante
      n'attend pas de réponse.

   « Le tracé est saccadé »
      Installez pyqtgraph (il est dans requirements.txt), ou baissez le
      rafraîchissement à 10 images par seconde dans les réglages
      d'interface. L'acquisition et l'enregistrement ne sont jamais
      affectés par la cadence d'affichage.

   « Un pic énorme à 50 Hz »
      Ce n'est pas un défaut du logiciel. Vérifiez le blindage du câble, la
      garde, et l'absence de boucle de masse. Le chapitre correspondant du
      document compagnon détaille la marche à suivre.

   « La valeur dérive sans arrêt »
      Une électrode fraîchement posée met de dix à trente minutes à se
      stabiliser. C'est normal, et c'est mesurable : l'onglet Multimètre
      affiche la dérive en microvolts par minute.

   « Rien n'est détecté »
      Baissez le seuil et l'amplitude minimale dans la page Traitement, ou
      relancez l'assistant d'auto-configuration.


11. DÉVELOPPEMENT ET PUBLICATION
--------------------------------

   make install-dev     installe aussi pytest et ruff
   make test            exécute les tests
   make check           vérifie la syntaxe, sans rien installer
   make lint            analyse statique

   Nomenclature logicielle :

       python3 tools/sbom.py            lisible
       python3 tools/sbom.py --json     CycloneDX 1.5, pour les outils
                                        d'analyse de conformité
       python3 tools/sbom.py --html     fragment du fascicule imprimé

   Elle décrit ce qui est réellement installé sur la machine, et non ce que
   le fichier des dépendances prétend exiger — c'est tout l'intérêt.

   Publication d'une version :

       python3 tools/release.py show          version courante
       python3 tools/release.py bump minor --name "Sève d'automne"
       (compléter la section ouverte dans CHANGELOG.txt)
       python3 tools/release.py check         vérifications avant diffusion
       python3 tools/release.py dist          archives .tar.gz et .zip
       python3 tools/release.py tag           étiquette git

   Le numéro de version vit dans un seul fichier, phytoscope/version.py, et
   seul l'outil de publication y écrit.

   Organisation du code :

       phytoscope/core/      sources, traitement, moteur, enregistrement
       phytoscope/music/     gammes, instruments, synthèse, correspondance
       phytoscope/ui/        interface Qt
       tools/                diagnostic, vérification, publication
       tests/                tests unitaires


12. CRÉDITS
-----------

   Conception, électronique, logiciel et rédaction : Bretagne Namasté.

   Ce logiciel accompagne le document « La Carte PhytoSense — conditionnement
   analogique et interface USB pour l'écoute des plantes », lui-même
   hors-série de l'ouvrage « La Musique des Plantes — dialogue vibratoire
   avec le monde végétal ».

   Bibliothèques utilisées : NumPy, PySide6 (Qt 6), pyqtgraph, sounddevice
   (PortAudio), pyserial, python-rtmidi. Voir LICENSE.txt pour le détail des
   licences.

   Les marques Music of the Plants, PlantWave, Plants Play, Scion et Biotron
   appartiennent à leurs détenteurs. Ce logiciel n'est ni sponsorisé, ni
   affilié, ni rémunéré par aucun fabricant.

================================================================================
