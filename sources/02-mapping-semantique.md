# Le mapping sémantique : remplacer les notes par des mots
Consultation : 2026-09-17

## LA VIDÉO IDENTIFIÉE — https://www.youtube.com/watch?v=TYHmBoMEElg
- **Titre** : « Le Chant des Plantes — Grand Rex 2015 »
- **Auteur** : **Alexandre Ferran** (chaîne @LeChantdesPlantes ; aussi connu sous le nom
  **Motokiyo**, au lieu-dit Le Parédé, Bagnères-de-Bigorre)
- **Publiée** le 28/11/2016 ; **événement filmé le 1er novembre 2015**
- **Durée** 21 min 34 s · 71 167 vues · sous-titres **manuels** FR et EN
- **Contexte** : « 24 heures de méditation pour la Terre », Grand Rex (Paris), un mois avant la COP21
- **Tags révélateurs** : `clavier des mots`, `plante qui parle`, `parole de plante`, `damanhur`, `devodama`

### Le dispositif, tel que décrit par l'auteur dans la vidéo
1. **Capteur** : appareil *Music of the Plants* de **Damanhur** (société **Devodama srl**) —
   une pince dans la terre/racines, une pince sur les feuilles.
2. **Mesure** : Ferran dit « différence de potentiel » (00:52) ; la documentation décrit en
   réalité un **pont de Wheatstone mesurant des variations d'impédance**.
3. **Conversion** : signal → messages MIDI → notes.
4. **Aveu décisif de l'auteur (02:20)** : « *l'appareil ne retranscrit pas la musique de la
   plante, ça lui donne la possibilité d'avoir des mains qui vont appuyer sur un clavier* ».
   C'est une définition exacte du *parameter mapping*.
5. **Le mapping sémantique (16:03)** : « *je suis le premier à avoir eu l'idée saugrenue de
   mettre des mots, vu que c'est du MIDI […] on peut mettre un piano… ou des mots* ».
   Premier clavier : les prénoms des habitants de la maison. Au Grand Rex : **≈ 50 mots**
   chargés dans un sampler (EXS24, Logic Pro).
6. **Seuil anti-rebond (19:33)** : « *Il faut qu'elle reste **quatre secondes** appuyée sur la
   note pour déclencher le mot* ». Ce seuil transforme un signal continu bruité en
   événements rares, donc en « énoncés » interprétables.
7. **Sortie effective au Grand Rex — 8 tokens au total** :
   « SOLEIL … AIDE … MALADE … TERRE … SOLEIL » (19:07-19:19), « TERRE » (19:58),
   « CHAUD, AIDE » (20:13). Présentés comme « la parole de sagesse des plantes ».

### Nature exacte du mapping
**Mot par note** — un échantillon audio par zone de note dans un sampler. Ce n'est
**pas** phonème par phonème, **pas** de la synthèse vocale paramétrique, **pas** un modèle
de langage. C'est une **table de correspondance**.
Un **clavier de LETTRES** (A-Z sur sol#1 → mi6) est également documenté sur le site de
l'auteur : structurellement identique à une planche Ouija.

### Ce que la vidéo ne fait pas
Aucun protocole de contrôle : pas de plante témoin, pas de condition « pince débranchée
ou sur objet inerte », pas de double aveugle, pas de pré-enregistrement du vocabulaire
attendu. Les ~50 mots du dictionnaire sont **choisis par l'opérateur** : le vocabulaire
disponible contraint entièrement l'énoncé possible. C'est aussi l'opérateur qui décide où
le « message » commence et finit.

## LE POINT ÉPISTÉMOLOGIQUE CENTRAL
Un mapping signal→note et un mapping signal→mot sont **formellement identiques** (une table).
Ils ne sont pas **sémantiquement** identiques : une note n'a pas de référent, un mot en a un.
Passer de l'un à l'autre **n'ajoute aucune information** — cela ajoute de la **référence**
dans la tête de l'auditeur. Le gain est perceptif et rhétorique, jamais informationnel.

## CRITÈRE DE DÉMARCATION : ce qui fait un mapping défendable
(a) **isomorphe** à une structure physique mesurable — (b) **inversible** — (c) **falsifiable**,
avec des conditions d'échec explicitées à l'avance.

### Exemples conformes
- **Buehler (MIT)** : modes normaux de vibration des 20 acides aminés calculés par chimie
  quantique, **transposés** dans l'audible en conservant les rapports de fréquences. Chaque
  acide aminé devient un **accord**. Inversible (musique → séquence → repliement prédit →
  validation par modélisation) et falsifiable.
  - Qin & Buehler (2019), *Extreme Mechanics Letters* 29, 100460 — doi:10.1016/j.eml.2019.100460
  - Yu et al. (2019), *ACS Nano* 13(7) — doi:10.1021/acsnano.9b02180
  - Yu & Buehler (2020), *APL Bioengineering* 4(1), 016108 — doi:10.1063/1.5133026
  - ⚠️ Buehler parle de « langage » au sens des *protein language models*. **Aucun de ses
    travaux ne convertit des données biologiques en mots de langue naturelle prononcés.**
- **Temple** : sonification de l'ADN, mapping motivé par la granularité du codon.
  - Temple (2017), *BMC Bioinformatics* 18:221 — doi:10.1186/s12859-017-1632-x
  - Temple (2021), *BMC Research Notes* 14:273 — doi:10.1186/s13104-021-05685-7
- **Résultat négatif assumé** : aucune sonification ADN → **phonèmes** trouvée dans la
  littérature. Ne rien citer sur ce point.

## SIGNAL CONTINU → ESPACE SÉMANTIQUE → MOTS : le travail de référence
**Tang, LeBel, Jain & Huth (2023)**, *Semantic reconstruction of continuous language from
non-invasive brain recordings*, **Nature Neuroscience 26, 858-866** — doi:10.1038/s41593-023-01304-9
→ Architecture exacte. **Point capital** : ce n'est pas un plus-proche-voisin naïf. Un
**modèle de langage sert de prior génératif** qui propose des continuations ; le signal
cérébral ne fait que **noter et reclasser** ces candidats. **La grammaire et la fluidité
viennent du LM ; seule la sélection vient du signal.** Les auteurs le mesurent par des
baselines et des tests de permutation, et montrent que le décodage exige la **coopération
du sujet** et s'effondre sous contre-mesures mentales.

- **Morris et al. (2023)**, vec2text — arxiv:2310.06816. L'inversion d'un embedding en texte
  est possible **quand l'embedding contient réellement le texte** ; cela ne dit rien du cas
  où l'on projette un signal physiologique arbitraire dans cet espace.
- **Mikolov et al. (2013)** — arxiv:1301.3781 ; **Reimers & Gurevych (2019)**, Sentence-BERT —
  doi:10.18653/v1/D19-1410.

## LLM SUR FLUX DE CAPTEURS — état de la technique
Technique dominante : **injecter la série temporelle en texte dans l'invite**. Fonctionne mal
au-delà de ~200 pas de temps ; sorties fréquemment génériques, inexactes ou mal ancrées.
- Nepal et al. (2024), AWARE Narrator — arxiv:2411.04691
- DailyLLM (2025) — arxiv:2507.13737 · SensorLLM — arxiv:2410.10624
- *Virtual Annotators for Time-series Physical Sensing Data* — arxiv:2403.01133
- *LLMs Memorize Sensor Datasets!* — arxiv:2406.05900
- *Empowering Time Series Analysis with LLMs: A Survey*, IJCAI 2024

## LES CINQ PREUVES QUE LE TEXTE NE VIENT PAS DU SIGNAL
**(a) Ablation — la preuve la plus directe.**
**Tan, Merrill, Gupta, Althoff & Hartvigsen (2024)**, *Are Language Models Actually Useful for
Time Series Forecasting?*, **NeurIPS 2024 (Spotlight)** — arxiv:2406.16964.
Sur trois méthodes LLM-pour-séries-temporelles populaires, **retirer le LLM ou le remplacer
par une simple couche d'attention ne dégrade pas les performances — et souvent les améliore**.
Un baseline trivial (« PAttn ») bat la plupart des forecasters à base de LLM.

**(b) Hallucination du prior génératif.**
**Shirakawa et al. (2024)**, *Spurious reconstruction from brain activity* — arxiv:2405.10078.
Les « reconstructions photoréalistes » d'activité cérébrale relèvent largement de la
classification dans des catégories vues à l'entraînement + hallucination du modèle de
diffusion, et échouent sur un jeu de test sans recouvrement de catégories.

**(c) Forme ≠ sens.**
- Bender & Koller (2020), *Climbing towards NLU*, ACL, Best Theme Paper — aclanthology 2020.acl-main.463
- Bender, Gebru, McMillan-Major & Shmitchell (2021), *Stochastic Parrots*, FAccT — doi:10.1145/3442188.3445922
- Shanahan (2024), *Talking About Large Language Models*, **CACM 67(2), 68-79** — arxiv:2212.03551

**(d) Effet ELIZA et paradigme CASA.**
- Weizenbaum (1966), CACM 9(1), 36-45 — doi:10.1145/365153.365168
- Reeves & Nass (1996), *The Media Equation*, CSLI/CUP
- Nass & Moon (2000), *Machines and Mindlessness*, J. Social Issues 56(1), 81-103 — doi:10.1111/0022-4537.00153

**(e) L'analogie la plus juste : la communication facilitée.**
**Wegner, Fuller & Sparrow (2003)**, *Clever hands: uncontrolled intelligence in facilitated
communication*, **JPSP 85(1), 5-19**. Un « facilitateur » sincèrement convaincu de n'être
qu'un conduit produit lui-même le message, par effet idéomoteur. Les participants répondent
correctement à des questions dont l'autre personne n'a même pas connaissance, tout en
attribuant sincèrement l'auteurité à l'autre. **Un clavier de mots piloté par un signal
bruité + un opérateur qui décide quand le message commence et finit reproduit ce dispositif
à l'identique.**

## LES TROIS TESTS DE CONTRÔLE MINIMAUX (à intégrer dans l'atelier)
1. **Pince débranchée / sur objet inerte / bruit blanc** → le système doit produire du
   non-sens visible. S'il produit de belles phrases, le signal n'y est pour rien.
2. **Ablation** : remplacer le signal par un tirage aléatoire dans le même vocabulaire.
   Un auditeur peut-il distinguer les deux ? Sinon, conclure.
3. **Pré-enregistrement** du vocabulaire, du seuil et de la fenêtre d'écoute **avant** la
   performance, sans édition a posteriori.

## LA PISTE ARTISTIQUE HONNÊTE
Mapper le signal vers un **espace de style prosodique continu** (Global Style Tokens), le
contenu lexical restant explicitement humain. **La plante module le *comment*, jamais le *quoi*.**
Esthétiquement aussi fort, épistémiquement défendable.
- Wang et al. (2018), *Style Tokens* — arxiv:1803.09017
- Stanton et al. (2018) — arxiv:1808.01410

## GARDE-FOUS DE SOURCE
- Citation de **Monica Gagliano** sur les machines de biofeedback végétal : circule via un
  blog de vendeur concurrent, **source primaire non retrouvée** → ne pas citer.
- **Aucune publication à comité de lecture** n'évalue le dispositif Devodama U1.
- L'effet Backster a été réfuté en conditions contrôlées : **Horowitz, Lewis & Gasteiger
  (1975)**, *Science* 189(4201), 478-480 — doi:10.1126/science.189.4201.478.

## CADRE GÉNÉRAL DE LA SONIFICATION
Hermann, Hunt & Neuhoff (eds.), *The Sonification Handbook*, Logos, 2011 —
https://sonification.de/handbook/ (PDF libre).
