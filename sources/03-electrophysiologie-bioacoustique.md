# SYNTHÈSE SCIENTIFIQUE — ÉLECTROPHYSIOLOGIE VÉGÉTALE ET BIOACOUSTIQUE DES PLANTES

**Méthode** : toutes les références ci-dessous ont été vérifiées via Europe PMC (API REST), PubMed, ou le texte intégral des articles. Les éditeurs Science, Nature, Cell, Wiley et Oxford bloquent l'accès direct (HTTP 403) ; j'ai donc travaillé sur les notices Europe PMC (auteurs/volume/pages/DOI/résumé verbatim) et, quand c'était possible, sur les PDF en accès libre (Khait et al. 2023 a été extrait intégralement par pdftotext). **Les points non vérifiés sont signalés explicitement en fin de chaque axe et récapitulés en §G.**

---

## A. ÉLECTROPHYSIOLOGIE VÉGÉTALE — FONDAMENTAUX

### A.1 Les trois classes de signaux électriques longue distance

La taxonomie de référence (Mudrilov, Ladeynova, Grinberg, Balalaeva & Vodeneev 2021, *Int. J. Mol. Sci.* 22(19):10715, Box 1 — texte intégral vérifié) distingue :

**Potentiel d'action (AP)** — dépolarisation transitoire à forme d'impulsion caractéristique.
- Amplitude : « de quelques dizaines à une centaine de mV » (verbatim).
- Durée : quelques secondes chez les plantes « locomotrices » (Mimosa, Dionaea), jusqu'à plusieurs dizaines de secondes chez les plantes ordinaires.
- Obéit au **seuil**, à la loi du **tout-ou-rien**, présente une **période réfractaire**.
- Vitesse de propagation : **1–10 cm/s**, via les éléments du phloème et de cellule à cellule par les **plasmodesmes**.
- Mécanisme ionique (séquence établie) : activation de canaux **Ca²⁺ voltage-dépendants** (nature moléculaire encore incertaine) → le Ca²⁺ active les **canaux anioniques** (efflux de **Cl⁻**) et **désactive simultanément la H⁺-ATPase plasmalemmique** → phase de dépolarisation ; puis **efflux de K⁺** + réactivation de la pompe H⁺ → phase de repolarisation.
- Preuve pharmacologique : blocage par les inhibiteurs de canaux anioniques (acide éthacrynique, acide anthracène-9-carboxylique A-9-C, NPPB) et par les inhibiteurs de H⁺-ATPase.

**Potentiel de variation / onde lente (VP / SWP)** — dépolarisation transitoire de forme irrégulière.
- Amplitude : « plusieurs dizaines de mV » ; durée : jusqu'à plusieurs **dizaines de minutes**.
- **N'obéit PAS au tout-ou-rien** : amplitude et durée dépendent du stimulus (c'est le point de distinction décisif avec l'AP).
- **N'est pas un signal auto-propagé** : c'est une réponse électrique *locale* induite par la propagation d'une **onde hydraulique** et/ou d'un **agent chimique** (facteur de Ricca ; les ROS sont candidats). Déclenchement par canaux calciques ligand-dépendants ou mécanosensibles ; **GLR3.1, 3.2, 3.3 et 3.6** sont impliqués.
- Le moteur principal de la dépolarisation est l'**inhibition de la H⁺-ATPase induite par le Ca²⁺**.

**Potentiel systémique (SP, « system potential »)** — variation systémique du potentiel de membrane vers l'**hyperpolarisation** (et non la dépolarisation). Mécanisme présumé : **activation** de la H⁺-ATPase. Le type de signal « le moins étudié », induit dans des conditions très particulières.

### A.2 Données chiffrées récentes, mesurées in planta

Ibacache-Carrión, Bolua-Hernández, Michard & Ramírez (2026), *Physiologia Plantarum* 178(4):e71066, DOI 10.1111/ppl.71066 — **mesures intraphloémiennes par électrographie de pénétration (EPG) avec pucerons *Acyrthosiphon pisum* comme bioélectrodes** (fil d'or 25 µm, colle d'argent conductrice), sur *Vicia faba* :

| Paramètre | AP (induit par section) | VP (induit par flamme 2–5 s) |
|---|---|---|
| Amplitude | **12,43 ± 0,51 mV** | 11,63 ± 0,41 mV |
| Durée | **3,04 ± 0,25 s** | **45,32 ± 5,3 s** |
| Vitesse globale | **2,6 ± 0,2 cm/s** | **0,38 ± 0,03 cm/s** |
| Acropète | 2,71 ± 0,43 cm/s | 0,59 ± 0,08 cm/s |
| Basipète | 2,43 ± 0,56 cm/s | 0,38 ± 0,05 cm/s |
| Asymétrie directionnelle | **non** (p = 0,07–0,70) | **oui**, acropète > basipète (p < 0,05) |
| Hyperpolarisation associée | 2,79 ± 0,3 mV / 2,58 ± 0,3 s (50 % des événements) | 3,8 ± 0,3 mV / 43,0 ± 6,7 s, *précède* le VP (30 %) |

**Point important pour un livre technique** : l'amplitude mesurée *dans le phloème* (~12 mV) est d'un ordre de grandeur inférieure aux « dizaines à centaine de mV » des mesures intracellulaires classiques au microélectrode. La valeur dépend entièrement du site et du mode de mesure (intracellulaire vs extracellulaire de surface vs intraphloémique). Toute amplitude citée sans son protocole est ininterprétable.

Blyth & Morris (2019), *Frontiers in Plant Science* 10:1393, DOI 10.3389/fpls.2019.01393, donnent pour le VP une vitesse de l'ordre de **1 à 2 mm/s**, contre **~10 cm/s** pour l'onde hydraulique elle-même — écart qui motive leur modèle de « dispersion augmentée par cisaillement » d'une substance de blessure dans le xylème (rayon xylémien 12 µm chez la tomate, 30–60 µm chez le frêne ; vitesse de flux 0,1–0,17 cm/s ; diffusivité 10⁻⁶–10⁻⁵ cm²/s). Le VP **traverse les zones de tissu nécrosé**, ce qu'un signal électrique auto-propagé ne ferait pas — argument fort pour l'origine hydraulique/chimique.

### A.3 GLR3.3 / GLR3.6 : la voie glutamate

**Mousavi, Chauvin, Pascaud, Kellenberger & Farmer (2013)**, *Nature* 500(7463):422–426, DOI 10.1038/nature12478, PMID 23969459. Criblage de **34 lignées mutantes** ; identification de **GLR3.2, GLR3.3 et GLR3.6** comme nécessaires à la signalisation de blessure feuille-à-feuille. L'injection de courant suffit à déclencher l'accumulation de **jasmonoyl-isoleucine** et l'expression des gènes de défense ; les doubles mutants montrent une expression distale réduite des gènes de réponse au jasmonate.

**Toyota, Spencer, Sawai-Toyota, Jiaqi, Zhang, Koo, Howe & Gilroy (2018)**, *Science* 361(6407):1112–1115, DOI 10.1126/science.aat7744, PMID 30213912. Résumé verbatim : « *Here we show that glutamate is a wound signal in plants. Ion channels of the GLUTAMATE RECEPTOR-LIKE family act as sensors that convert this signal into an increase in intracellular calcium ion concentration that propagates to distant organs, where defense responses are then induced.* » Éléments confirmés par sources secondaires : la propagation est **totalement abolie chez le double mutant *glr3.3 glr3.6*** et **restaurée à un niveau quasi sauvage** par expression de GLR3.6 dans cette lignée ; l'application de **L-Glu 100 mM** suffit à déclencher des élévations calciques systémiques GLR3.3/GLR3.6-dépendantes. Imagerie par capteur **GCaMP3**.
→ ⚠️ **Je n'ai PAS pu vérifier sur source primaire la vitesse de l'onde calcique** (valeur souvent citée « ~1 mm/s » dans la littérature secondaire). Le texte intégral est derrière paywall (403) et l'article n'est pas dans PMC. **Ne pas citer de chiffre de vitesse pour Toyota 2018 sans accès à l'article.**

### A.4 Phloème, plasmodesmes, cellules compagnes

**Hedrich, Salvador-Recatalà & Dreyer (2016)**, « Electrical Wiring and Long-Distance Plant Communication », *Trends in Plant Science* 21(5):376–387, DOI 10.1016/j.tplants.2016.01.016, PMID 26880317. Le phloème y est décrit comme un « **câble vert** » (*green cable*) permettant la transmission des AP. Point critique et souvent ignoré des vulgarisations, verbatim : « *However, phloem APs are initiated and propagated independently of these glutamate receptors.* » Autrement dit **GLR3.3/3.6 sont nécessaires à la propagation de l'activité électrique de la feuille lésée vers les feuilles saines, mais les AP phloémiens eux-mêmes sont initiés et propagés indépendamment des GLR**. La méthode de référence pour séparer le potentiel phloémien des réponses secondaires des tissus environnants est l'usage de **pucerons vivants comme bioélectrodes**.

**Nguyen, Kurenda, Stolz, Chételat & Farmer (2018)**, *PNAS* 115(40):10178–10183, DOI 10.1073/pnas.1807049115, PMID 30228123. Les protéines de fusion GLR sont localisées dans les **éléments criblés du phloème** ET les **cellules de contact du xylème** ; seuls les doubles mutants privés de GLR dans *les deux* types cellulaires réduisent substantiellement la signalisation feuille-à-feuille. Résultat de séquence temporelle, verbatim : « *wound-induced membrane depolarizations in the wild-type preceded cytosolic Ca²⁺ maxima* » — **la dépolarisation précède le maximum calcique cytosolique**, ce qui contraint les modèles causaux.

**Wu, Li, Chen & Kong (2024)**, *PNAS* 121(24):e2400639121, DOI 10.1073/pnas.2400639121, PMID 38838018. La **cellule compagne** est essentielle : « *GLR3.3 has to be renewed from companion cells to allow its function in sieve elements* ». GLR3.6 opère à la fois dans les cellules compagnes et les cellules de contact xylémiennes, son action phloémienne étant indépendante de GLR3.3.

### A.5 Le cas Dionaea (référence de calibration)

**Hedrich & Kreuzer (2023)**, « Demystifying the Venus flytrap action potential », *New Phytologist* 239(6):2108–2112, DOI 10.1111/nph.19113, PMID 37424515. L'AP de *Dionaea* suit une séquence en **cinq phases** : transitoire Ca²⁺ cytosolique initial → dépolarisation → repolarisation → hyperpolarisation transitoire (*overshoot*) → retour au potentiel de repos, le tout en **~1 seconde**. La plante **compte** les AP successifs pour réguler son comportement de chasse.

Travaux de Volkov (tous vérifiés via Europe PMC) :
- Volkov, Adesina & Jovanov (2007), *Plant Signaling & Behavior* 2(3):139–145, DOI 10.4161/psb.2.3.4217 : fermeture par stimulation électrique du midrib au lobe en **0,3 s** (vs **0,1 s** en stimulation mécanique) ; charge moyenne requise **13,6 µC** ; durée d'AP ~1,5 ms.
- Volkov, Carrell, Baldwin & Markin (2009), « Electrical memory in Venus flytrap », *Bioelectrochemistry* 75(2):142–147, DOI 10.1016/j.bioelechem.2009.03.005 : seuils de charge **8 µC (petits pièges) / 9 µC (grands pièges)** à température ambiante, **4,1 µC à 28–36 °C** ; caractère **cumulatif** des stimuli sub-liminaires → « mémoire électrique à court terme ».
- Volkov, Carrell & Markin (2009), *Plant Physiology* 149(4):1661–1667, DOI 10.1104/pp.108.134536 : modèle de circuit électrique équivalent (« biologically closed electrical circuits »).
- Volkov et al. (2013), *J. Plant Physiol.* 170(9):838–846, DOI 10.1016/j.jplph.2013.01.009 : seuil en tension **4,4 V**.
- Volkov et al. (2013), *J. Plant Physiol.* 170(1):25–32, DOI 10.1016/j.jplph.2012.08.009 : forces mécaniques — impact moyen **149 mN**, constriction jusqu'à **450 mN** pendant la digestion.
- Volkov (2019), *Bioelectrochemistry* 125:25–32, DOI 10.1016/j.bioelechem.2018.09.001 : AP se propageant « *with speed up to 10 m/s* » dans le piège.

⚠️ **La valeur « 14 µC » couramment reprise dans la presse est une arrondie de 13,6 µC (Volkov 2007). Les seuils publiés ultérieurement par la même équipe sont plus bas (8–9 µC, voire 4,1 µC à chaud). Citer la fourchette, pas un chiffre unique.**

⚠️ **Signalement d'anomalie** : Volkov, Lang & Volkova-Gugeshashvili (2007), *Bioelectrochemistry* 71(2):192–197, DOI 10.1016/j.bioelechem.2007.04.006, rapportent des AP rapides chez *Aloe vera* à **67 m/s** — soit 3 à 4 ordres de grandeur au-dessus des vitesses de propagation phloémienne (1–10 cm/s). Cette valeur, comme les « 10 m/s » chez Dionaea, relève très probablement d'une **propagation électrotonique passive (câble) et non d'un AP régénératif**, ou d'un artefact de couplage entre électrodes. **À citer avec réserve explicite dans un ouvrage technique.**

### A.6 Historique

- **Burdon-Sanderson, J. (1873)**, « Note on the electrical phenomena which accompany irritation of the leaf of *Dionæa muscipula* », *Proceedings of the Royal Society of London* 21:495–496. Premier enregistrement d'un potentiel d'action végétal, à la suite d'une correspondance avec Darwin qui lui avait fourni des plants de dionée. (Vitesse de propagation rapportée de ~200 mm/s chez *Dionaea* — chiffre trouvé en source secondaire, non vérifié sur l'original.)
- **Bose, J. C. (1902)**, *Response in the Living and Non-Living*, Longmans, Green & Co., Londres/New York. **Vérifié** (exemplaires numérisés, Internet Archive).
- **Bose, J. C. (1907)**, *Comparative Electro-Physiology: A Physico-Physiological Study*, Longmans, Green & Co. **Vérifié**.
- **Bose, J. C. (1913)**, *Researches on Irritability of Plants*. **Vérifié**.
- **Bose, J. C. (1926)**, *The Nervous Mechanism of Plants*, Longmans, Green & Co. ⚠️ **Non trouvé dans le catalogue Internet Archive interrogé** ; existence attestée uniquement par sources secondaires (notice Wikipédia, littérature historique). À vérifier en catalogue de bibliothèque avant publication.
- **Darwin, C. & Darwin, F. (1880)**, *The Power of Movement in Plants*, John Murray, Londres. ⚠️ **Non vérifié bibliographiquement dans cette session** (fait bibliographique classique, mais à confirmer).

---

## B. ARBRES : ÉLECTROPHYSIOLOGIE IN SITU ET ÉMISSIONS ACOUSTIQUES

### B.1 Potentiel électrique du tronc — protocoles et amplitudes réelles

**Hao, Li & Hao (2021)**, « Variations of electric potential in the xylem of tree trunks associated with water content rhythms », *Journal of Experimental Botany* 72(4):1321–1335, DOI 10.1093/jxb/eraa492.
- Espèce : *Populus hopeiensis* — 73 jeunes plants en pots (diamètre de tronc moyen 4,17 ± 0,28 cm, hauteur 1,72 ± 0,08 m) + 3 arbres de plein champ.
- Électrodes : acier inoxydable, **30 mm de long × 4 mm de diamètre**, insérées à **50 cm de hauteur**, extrémité enfoncée de **5 mm dans le xylème** ; électrode de masse enterrée à 20–80 cm (40 cm de long).
- Amplitudes : **plusieurs centaines de mV en saison de végétation (avril–octobre), atteignant parfois 1 V** ; **quelques dizaines de mV** en fin d'automne/hiver (typiquement < 700 mV).
- Rythmicité journalière (pic matinal, niveaux hauts nocturnes) et annuelle, synchrone avec le cycle de dormance.
- Mécanisme proposé : variations du **nombre d'ions accumulés à la surface de l'électrode** en fonction de la disponibilité en eau du xylème — **et non le flux de sève seul**.

**Gibert, Le Mouël, Lambs, Nicollin & Perrier (2006)**, « Sap flow and daily electric potential variations in a tree trunk », *Plant Science* 171(5):572–584, DOI 10.1016/j.plantsci.2006.06.012. Sur *Populus nigra* : tiges d'acier inoxydable de 6 mm de diamètre enfoncées de 5 mm dans l'aubier, référencées à une **électrode impolarisable Pb/PbCl₂**. Variations journalières nettes en été (minimum l'après-midi pour les électrodes hautes vs basses), **disparaissant après la chute des feuilles** — argument fort pour un couplage au flux de sève/transpiration. Organisation stable et cohérente établie au printemps, amplitudes maximales en été ; en hiver, amplitudes variables et parfois **anti-corrélations entre électrodes**. La variation de potentiel accompagne le rythme de transpiration **en opposition de phase**.
⚠️ Résumé non récupéré verbatim (notice Europe PMC sans abstract) ; les détails ci-dessus proviennent de sources secondaires citant l'article. Détails méthodologiques à revérifier sur le PDF.

**Gurovich & Hermosilla (2009)**, « Electric signalling in fruit trees in response to water applications and light–darkness conditions », *Journal of Plant Physiology* 166(3):290–300, DOI 10.1016/j.jplph.2008.06.004. Mesure de ΔEP par microélectrodes dans le tronc d'arbres fruitiers, motifs systématiques selon cycle jour/nuit et disponibilité en eau du sol.

**Oyarce & Gurovich (2010)**, « Electrical signals in avocado trees: Responses to light and water availability conditions », *Plant Signaling & Behavior* 5(1):34–41, DOI 10.4161/psb.5.1.10157, PMID 20592805.

**Ríos-Rojas, Tapia & Gurovich (2014)**, *Journal of Plant Physiology* 171(10):799–806, DOI 10.1016/j.jplph.2014.02.005 — capteur de stress hydrique en temps réel sur *Persea americana* et *Prunus domestica*.
**Ríos-Rojas, Morales-Moraga, Alcalde & Gurovich (2015)**, *Plant Signaling & Behavior* 10(2):e976487, DOI 10.4161/15592324.2014.976487 — télémétrie sans fil ; les arbres stressés montrent des **changements progressifs de pente**, les arbres bien irrigués des **cycles journaliers à pente nulle**.

### B.2 Artefacts : ce qui mine les mesures sur arbre sur pied

Synthèse des éléments méthodologiques relevés dans les sources ci-dessus :
1. **Polarisation d'électrode** — des tiges métalliques nues dérivent ; d'où l'usage d'électrodes impolarisables (Pb/PbCl₂ chez Gibert 2006, Ag/AgCl ailleurs). Hao et al. 2021 attribuent explicitement une partie du signal à l'accumulation ionique **à la surface de l'électrode**, c'est-à-dire à l'interface, pas au tissu.
2. **Potentiel d'écoulement (streaming potential) / self-potential** — le mouvement de sève à travers une matrice chargée génère un potentiel électrocinétique. C'est la raison pour laquelle le signal **disparaît après la chute des feuilles**. Ce n'est pas de la signalisation.
3. **Blessure d'insertion** — toute électrode enfoncée dans le xylème provoque elle-même une réponse électrique et une réponse de cicatrisation ; les premières heures/jours de série sont inexploitables.
4. **Dérive thermique et hygrométrique** de l'interface électrode/bois.
5. **Captation électromagnétique** — problème central hors cage de Faraday. **Tran, Dutoit, Najdenovska, Wallbridge, Plummer, Mazza, Raileanu & Camps (2019)**, « Electrophysiological assessment of plant status outside a Faraday cage using supervised machine learning », *Scientific Reports* 9:17073, DOI 10.1038/s41598-019-53675-4, PMID 31745185, est la référence à citer : capteur conçu pour la production sous serre **sans cage de Faraday**, détectant modification de l'activité bioélectrique sous stress hydrique et rythme nycthéméral, avec classification automatique supervisée du statut physiologique.
6. **Confusion signal/corrélat** — les corrélats mesurables (flux de sève par méthode thermique, dendrométrie, potentiel hydrique foliaire par chambre à pression, conductance stomatique) doivent être enregistrés en parallèle, sans quoi rien ne distingue un « signal » d'une dérive hydro-thermique.

⚠️ **Non vérifié en texte intégral** : un article *Hydrology and Earth System Sciences* 29:2997 (2025), « Self-potential signals related to tree transpiration in a Mediterranean climate », existe (URL hess.copernicus.org/articles/29/2997/2025/) et traite du couplage potentiel spontané/transpiration ; je n'ai pas pu en extraire les chiffres.

### B.3 Émissions acoustiques par cavitation/embolie xylémique

**Milburn, J. A. & Johnson, R. P. C. (1966)**, « The conduction of sap. II. Detection of vibrations produced by sap cavitation in *Ricinus* xylem », *Planta* 69:43–52, **DOI 10.1007/BF00380209** (DOI confirmé via l'hommage publié dans *Journal of Plant Hydraulics*). Dispositif : **tête de lecture de tourne-disque** connectée à un amplificateur et un haut-parleur ; des « clics » **audibles** (< 20 kHz) produits par des feuilles en déshydratation. C'est l'acte de naissance de la bioacoustique végétale expérimentale.

**Ritman, K. T. & Milburn, J. A. (1988)**, « Acoustic emissions from plants: ultrasonic and audible compared », *Journal of Experimental Botany* 39:1237–1248, DOI 10.1093/jxb/39.9.1237.

**Tyree, M. T. & Sperry, J. S. (1989)**, « Vulnerability of xylem to cavitation and embolism », *Annual Review of Plant Physiology and Plant Molecular Biology* 40:19–38. ⚠️ Volume/pages confirmés par l'en-tête du PDF hébergé par le laboratoire Sperry ; texte non extractible (PDF scanné sans couche texte). Le passage à l'**ultrasonore** est attribué à Tyree et al. (1984) et le *drought stress monitor* modèle 4615 DSM (Physical Acoustics Corp., Princeton NJ) à Tyree & Sperry 1989 — **références secondaires, à vérifier**.

**Gammes de fréquences et protocoles actuels** (protocole PROMETHEUS, réseau COST de physiologie des plantes ligneuses — source vérifiée) :
- Détection au-dessus de **20 kHz** pour s'affranchir du bruit de fond.
- Capteur **R15** : bande **50–200 kHz** (le plus utilisé historiquement) ; capteur **WD** : **100–1000 kHz** ; capteur large bande **KRNBB-PC** pour l'analyse spectrale complète.
- Seuils d'amplitude : **35 dB en laboratoire**, **45 dB au champ** (pour filtrer les artefacts dus au vent).
- **Sources d'AE qui ne sont PAS de la cavitation** (point critique) : retrait du bois en déshydratation, rupture mécanique du bois, émissions de l'écorce en dessiccation, mouvements d'organes sous le vent, interférences radiofréquence des éclairages fluorescents.

**Nolf, Beikircher, Rosner, Nolf & Mayr (2015)**, « Xylem cavitation resistance can be estimated based on time-dependent rate of acoustic emissions », *New Phytologist* 208(2):625–632, DOI 10.1111/nph.13476, PMID 26010417. **16 espèces et 3 cultivars** ; corrélation linéaire entre le potentiel hydrique à 50 % de perte de conductivité hydraulique (Ψ₅₀) et l'**activité acoustique maximale** : **p < 0,001, R² = 0,76**. L'usage du **taux temporel** d'AE plutôt que du cumul améliore l'estimation de P50 et atténue les signaux parasites aux stades avancés de déshydratation.

**Fernández, Fernández & Bilmes (2012)**, « Natural and laser-induced cavitation in corn stems: On the mechanisms of acoustic emissions », *Papers in Physics* 4:040003, DOI 10.4279/PIP.040003. Mécanisme proposé : l'émission provient d'une **oscillation transitoire de la cavité** au moment de l'inception de la cavitation, et non d'un collapsus unique ; absorption et **filtrage fréquentiel** du signal lors de sa propagation dans le tissu (conséquence majeure : le spectre enregistré en surface n'est pas le spectre émis).

### B.4 Bioacoustique racinaire (Gagliano)

**Gagliano, Mancuso & Robert (2012)**, « Towards understanding plant bioacoustics », *Trends in Plant Science* 17(6):323–325, DOI 10.1016/j.tplants.2012.03.002. Article d'opinion posant le cadre : rationnel évolutif pour une perception des sons/vibrations chez les plantes, mécanismes mécanosensoriels « jusqu'ici insoupçonnés ».

**Gagliano, Renton, Duvdevani, Timmins & Mancuso (2012)**, « Out of sight but not out of mind: Alternative means of communication in plants », *PLoS ONE* 7(5):e37382, DOI 10.1371/journal.pone.0037382. Voisinage détecté chez le piment malgré blocage des voies chimiques, tactiles et lumineuses connues.

**Gagliano, Grimonprez, Depczynski & Renton (2017)**, « Tuned in: plant roots use sound to locate water », *Oecologia*, DOI 10.1007/s00442-017-3862-z, PMID 28382479. ⚠️ Volume et pagination non vérifiés.

⚠️ **Le chiffre de « clics à 220 Hz émis par les racines de maïs »** et « meilleure réponse entre 200 et 300 Hz » circule largement ; il apparaît dans la revue TiPS 2012 de Gagliano et al. **Je n'ai pas pu remonter à un article primaire avec données et statistiques publiées pour l'émission acoustique racinaire.** À traiter comme **non établi**.

⚠️ **« Carol Gibson-Wood » : aucune trace de cette chercheuse en bioacoustique végétale n'a été trouvée** dans les bases interrogées. Il s'agit probablement d'une confusion (à supprimer du manuscrit ou à documenter autrement).

---

## C. BIOACOUSTIQUE : ÉMISSION ET PERCEPTION

### C.1 Khait et al. 2023 — protocole et chiffres exacts

**Khait, I., Lewin-Epstein, O., Sharon, R., Saban, K., Goldstein, R., Anikster, Y., Zeron, Y., Agassy, C., Nizan, S., Sharabi, G., Perelman, R., Boonman, A., Sade, N., Yovel, Y. & Hadany, L. (2023)**, « Sounds emitted by plants under stress are airborne and informative », *Cell* 186(7):1328–1336.e10, DOI 10.1016/j.cell.2023.03.009, PMID 37001499. **Texte intégral extrait et vérifié.**

**Dispositif** : boîte acoustique **50 × 100 × 150 cm³**, dans le sous-sol de la faculté des sciences de la vie de TAU, parois atténuant les bruits extérieurs d'au moins **100 dB SPL** dans la bande utile. **Deux microphones directionnels** par plante (pour éliminer les fausses détections dues au bruit électronique et aux interférences entre plantes). Microphone à condensateur **CM16 (Avisoft Bioacoustics)**, convertisseur **UltraSoundGate 1216H**, **échantillonnage 500 kHz/canal**, **filtre passe-haut 20 kHz**. Enregistrement de 1,5 s déclenché quand le signal dépasse 2 % de la dynamique max. Bande étudiée : **20–150 kHz**.

**Espèces** : tomate (*Solanum lycopersicum*) et tabac (*Nicotiana tabacum*) en conditions contrôlées. Sons également enregistrés chez **blé (*Triticum aestivum*), maïs (*Zea mays*), vigne Cabernet Sauvignon (*Vitis vinifera*), cactus *Mammillaria spinosissima*, lamier *Lamium amplexicaule*** — **mais PAS depuis les parties ligneuses d'amandier et de vigne**.

**Trois contrôles** : même plante avant traitement (auto-contrôle), plante voisine non traitée de la même espèce, pot avec terre sans plante.

**Taux d'émission (nombre de sons/heure, moyenne ± SE)** :
| Condition | Tomate | Tabac |
|---|---|---|
| Sécheresse (Dry) | **35,4 ± 6,1** | **11,0 ± 1,4** |
| Section (Cut) | **25,2 ± 3,2** | **15,2 ± 2,6** |
| Tous contrôles | **< 1** | **< 1** |
| Pot seul | **0 son sur > 500 h d'enregistrement** | — |
Significativité : p < e⁻⁶ (test de Wilcoxon, correction de Holm-Bonferroni sur 12 comparaisons).

**Intensité et fréquence de pic** (à **10,0 cm**, réf. 20 µPa ; **borne inférieure** en raison de la directivité du micro) :
| | Intensité de pic | Fréquence de pic |
|---|---|---|
| Tomate sécheresse | **61,6 ± 0,1 dB SPL** | **49,6 ± 0,4 kHz** |
| Tabac sécheresse | **65,6 ± 0,4 dB SPL** | **54,8 ± 1,1 kHz** |
| Tomate section | **65,6 ± 0,2 dB SPL** | **57,3 ± 0,7 kHz** |
| Tabac section | **63,3 ± 0,2 dB SPL** | **57,8 ± 0,7 kHz** |

**Classification (boîte acoustique)** : SVM avec extraction de traits par **réseau de diffusion (scattering network)** → **70 % d'exactitude** pour chacune des 4 paires (Tomate-Dry vs Tomate-Cut ; Tabac-Dry vs Tabac-Cut ; Tomate-Dry vs Tabac-Dry ; Tomate-Cut vs Tabac-Cut), p < e⁻¹² par paire. MFCC : significatif mais inférieur (p < e⁻⁴). Traits « basiques » (4 traits) : significatif pour 5 des 6 paires. **Sons de plante vs bruit électrique du système : > 98 %**. Résultats reproduits par CNN.

**En serre** : 23 plants de tomate enregistrés **9 jours consécutifs** après arrosage, avec suivi du **contenu volumétrique en eau du sol (VWC)**. Classifieur CNN son-de-tomate vs bruits de serre : **99,7 % d'exactitude équilibrée**. Classification irrigué/sec fondée sur le **taux** de sons : **84 % d'exactitude équilibrée** (p < e⁻⁵, test exact de Fisher). Classification par le signal : **81 %**. Classification VWC < 0,05 vs > 0,05 : **> 72 %**. Sans pré-classification en « sons de tomate » : **> 75 %**. Augmentation significative du nombre de sons entre J1→J2 et J2→J3 (p < 0,01 et p < 0,001, Wilcoxon apparié, correction Holm-Bonferroni sur 8 comparaisons).

**Affirmation de portée** : les auteurs écrivent que les émissions « dans la gamme ultrasonore de **20–100 kHz**, pourraient être détectées à une distance de **3–5 m** par de nombreux organismes ». ⚠️ **C'est une extrapolation des auteurs, pas une mesure de détection à cette distance.**

**Données publiques** : jeu de sons sur Dryad DOI 10.5061/dryad.jwstqjqf7 ; code du classifieur CNN sur Zenodo DOI 10.5281/zenodo.7612742.

### C.2 Les deux critiques majeures (indispensables pour l'équilibre du livre)

**Nardini, A., Cochard, H. & Mayr, S. (2024)**, « Talk is cheap: rediscovering sounds made by plants », *Trends in Plant Science* 29(6):662–667, DOI 10.1016/j.tplants.2023.11.023, PMID 38218649. Résumé verbatim : « *While recent technological advancements have allowed the demonstration that these sounds can propagate in the air surrounding plants, we remind readers here that research on sound production by plants is more than 100 years old. The mechanisms and patterns of sound emission from plants subjected to different stress factors are also reasonably understood, thanks to the pioneering work of John Milburn and others. By contrast, experimental evidence for a role of these sounds in plant-animal or plant-plant communication remains lacking and, at present, these ideas remain highly speculative.* »
→ Le mécanisme physique est **connu depuis 1966** (cavitation xylémique), l'apport de 2023 est la **propagation aérienne et la classification**, pas la découverte du phénomène ; et le rôle **communicationnel** est spéculatif.

**Son, J. S., Jang, S., Mathevon, N. & Ryu, C.-M. (2024)**, « Is plant acoustic communication fact or fiction? », *New Phytologist* 242(5):1876–1880, DOI 10.1111/nph.19648, PMID 38424727. Résumé verbatim : « *While plants do emit sounds under stress, these sounds are high-pitched, low intensity, and propagate only short distances. Most studies on plant sound sensitivity actually concern **substrate vibrations rather than airborne sound**. Low-frequency, high-intensity sounds from loudspeakers near plants may affect growth processes, but plants likely cannot perceive their own sounds over long distances. **No evidence supports plant-to-plant acoustic communication.*** »
→ **La distinction vibration de substrat / son aérien est LA distinction que la vulgarisation efface systématiquement.**

### C.3 Perception acoustique

**Veits, M., Khait, I., Obolski, U., Zinger, E., Boonman, A., Goldshtein, A., Saban, K., Seltzer, R., Ben-Dor, U., Estlein, P., Kabat, A., Peretz, D., Ratzersdorfer, I., Krylov, S., Chamovitz, D., Sapir, Y., Yovel, Y. & Hadany, L. (2019)**, « Flowers respond to pollinator sound within minutes by increasing nectar sugar concentration », *Ecology Letters* 22(9):1483–1492, DOI 10.1111/ele.13331, PMID 31286633.
Résumé vérifié : *Oenothera drummondii* exposée à la diffusion du son d'une abeille en vol ou à des signaux synthétiques de fréquence similaire produit un nectar plus sucré **en 3 minutes** ; les fleurs **vibrent mécaniquement** en réponse, la fleur jouant le rôle d'**organe sensoriel auditif** ; réponse **spécifique en fréquence** (réponse aux sons de pollinisateur, pas aux hautes fréquences).
Chiffres issus de la **préversion bioRxiv** (⚠️ à revérifier sur la version publiée) : abeille = pic **200–500 Hz** ; son synthétique bas = balayage **1000 → 50 Hz** ; contrôles sans réponse = **35–34 kHz** et **160–158 kHz** (p > 0,6 et p > 0,9 pour la vibration). Concentration en sucre : **19,8 ± 0,6 %** (Low) et **19,1 ± 0,7 %** (Bee) contre **16,3 ± 0,5 %** et **16,0 ± 0,4 %** en contrôle, soit **~+20 % relatif**. Effectifs : 257 + 298 + 112 fleurs, > 650 au total. Amplitude de vibration des pétales : **~0,1 mm** ; vibration très réduite après ablation des pétales (p < 0,0005).

⚠️ **Réplique critique** : Pyke, G. H., et al. (2020), « Changes in floral nectar are unlikely adaptive responses to pollinator flight sound », *Ecology Letters*, DOI 10.1111/ele.13403 — existence confirmée, **volume/pages non vérifiés**. À citer comme contrepoint.

**Mishra, R. C., Ghosh, R. & Bae, H. (2016)**, « Plant acoustics: in the search of a sound mechanism for sound signaling in plants », *Journal of Experimental Botany* 67(15):4483–4494, DOI 10.1093/jxb/erw235, PMID 27342223. Revue de référence sur la mécanotransduction acoustique. Effets cellulaires documentés des vibrations sonores : modification de la structure secondaire de protéines membranaires, réarrangement des microfilaments, **signatures Ca²⁺**, augmentation de protéines kinases, peroxydases, enzymes antioxydantes, amylase, activités **H⁺-ATPase / canaux K⁺**, élévation des polyamines, sucres solubles et auxine. Les auteurs proposent un modèle de signalisation — en soulignant qu'il reste hypothétique.

⚠️ À noter pour la prudence éditoriale : El-Sappah et al. (2024), « The plant is neither dumb nor deaf; it talks and hears », *The Plant Journal*, DOI 10.1111/tpj.16650, est **RÉTRACTÉ**. Ne pas citer.

---

## D. RÉSEAUX MYCORHIZIENS : LE « WOOD WIDE WEB » ET SA CRITIQUE

### D.1 Les travaux fondateurs

**Simard, S. W., Perry, D. A., Jones, M. D., Myrold, D. D., Durall, D. M. & Molina, R. (1997)**, « Net transfer of carbon between ectomycorrhizal tree species in the field », *Nature* 388:579–582, DOI 10.1038/41557.

**Klein, T., Siegwolf, R. T. W. & Körner, C. (2016)**, « Belowground carbon trade among tall trees in a temperate forest », *Science* 352(6283):342–344, DOI 10.1126/science.aad6188, PMID 27081070. Marquage isotopique ¹³C à l'échelle de la canopée sur épicéas de **40 m** : transfert interspécifique bidirectionnel vers hêtre, mélèze et pin via sphères racinaires chevauchantes, représentant **40 % du carbone des racines fines**, soit **~280 kg ha⁻¹ an⁻¹** d'échange arbre-à-arbre.

**Kiers, E. T., Duhamel, M., Beesetty, Y., Mensah, J. A., Franken, O., Verbruggen, E., Fellbaum, C. R., Kowalchuk, G. A., Hart, M. M., Bago, A., Palmer, T. M., West, S. A., Vandenkoornhuyse, P., Jansa, J. & Bücking, H. (2011)**, « Reciprocal rewards stabilize cooperation in the mycorrhizal symbiosis », *Science* 333(6044):880–882, DOI 10.1126/science.1208473, PMID 21836016. Les plantes détectent, discriminent et récompensent les meilleurs partenaires fongiques par plus de glucides ; réciproquement les champignons n'augmentent le transfert de nutriments que vers les racines les plus généreuses. Conclusion des auteurs : le symbiote **ne peut pas être « asservi »** ; le mutualisme est stable parce que le **contrôle est bidirectionnel**. (À noter : c'est un mécanisme de **marché biologique**, pas d'altruisme.)

### D.2 La critique de Karst, Jones & Hoeksema 2023 — ce qu'elle établit exactement

**Karst, J., Jones, M. D. & Hoeksema, J. D. (2023)**, « Positive citation bias and overinterpreted results lead to misinformation on common mycorrhizal networks in forests », *Nature Ecology & Evolution* 7(4):501–511, DOI 10.1038/s41559-023-01986-1, PMID 36782032. **Correctif éditorial** : *Author Correction*, *Nat. Ecol. Evol.* 7:623, DOI 10.1038/s41559-023-02035-7.

⚠️ **Le titre exact n'est PAS celui donné dans la commande** : c'est « …lead to **misinformation on common mycorrhizal networks in forests** », et non « …lead to misinformed conclusions about wood-wide webs ». À corriger dans le manuscrit.

Résumé verbatim, et voici précisément les **trois affirmations** évaluées et leur verdict :
1. **« Les CMN sont répandus dans les forêts »** → « *insufficiently supported because results from field studies vary too widely, have alternative explanations or are too limited to support generalizations* ». **Insuffisamment étayé.**
2. **« Des ressources sont transférées via les CMN et améliorent les performances des semis »** → même verdict : **insuffisamment étayé** (variabilité excessive entre études de terrain, explications alternatives, portée trop limitée pour généraliser).
3. **« Les arbres matures envoient préférentiellement ressources et signaux de défense à leur descendance via les CMN »** → verbatim : « *has **no peer-reviewed, published evidence***. » **Aucune preuve publiée et évaluée par les pairs.** C'est le point le plus dur de l'article : l'affirmation la plus populaire (« arbres-mères ») est celle qui n'a **aucun** support publié.

**Sur le biais de citation** : les auteurs ont examiné comment les résultats des recherches sur les CMN sont cités et ont trouvé que **les affirmations non étayées ont doublé au cours des 25 dernières années** ; un biais en faveur de la citation des effets positifs « *may obscure our understanding of the structure and function of CMNs in forests* ».
**Conclusion finale verbatim** : « *We conclude that knowledge on CMNs is presently too sparse and unsettled to inform forest management.* »
Les auteurs reconnaissent par ailleurs que **certaines des citations non étayées provenaient de leurs propres publications antérieures**, et appellent à concevoir de nouvelles expériences, exiger de meilleures preuves, penser aux explications alternatives et être plus sélectifs dans la diffusion des affirmations.

### D.3 Le reste du dossier critique

**Henriksson, N., et al. (2023)**, « Re-examining the evidence for the mother tree hypothesis – resource sharing among trees via ectomycorrhizal networks », *New Phytologist* 239:19–28, DOI 10.1111/nph.18935.

**Robinson, D., et al. (2023)**, « Mother trees, altruistic fungi, and the perils of plant personification », *Trends in Plant Science*. ⚠️ Volume/pages/DOI non vérifiés (article identifié via son identifiant ScienceDirect S1360138523002728).

**Réponse de Simard** : Simard, S. W., Ryan, M. & Perry, D. (2025), « Opinion: Response to questions about common mycorrhizal networks », *Frontiers in Forests and Global Change*, DOI 10.3389/ffgc.2024.1512518. Argument central : même s'il existe un biais de citation, cela n'annule pas le fait que toutes les espèces d'arbres sont mycorhizo-dépendantes et que la facilitation et le transfert CMN-dépendants ont été démontrés.
⚠️ **Aucune réplique dans *Nature Ecology & Evolution* de 2024 n'a été trouvée** ; la réponse formelle est celle de 2025 dans *Frontiers*.

**Position défendable pour un ouvrage technique** : le transfert de carbone entre arbres via des réseaux ectomycorhiziens est **documenté** (Klein 2016) ; sa **généralité en forêt**, son **bénéfice net pour les receveurs**, et surtout la **direction préférentielle vers la descendance** ne le sont **pas**. Le « Wood Wide Web » est une métaphore journalistique qui a rétroagi sur la littérature scientifique via le biais de citation — c'est précisément ce que Karst et al. quantifient.

---

## E. SONIFICATION DE DONNÉES BIOLOGIQUES

### E.1 Cadre théorique

**Hermann, T. (2008)**, « Taxonomy and definitions for sonification and auditory display », *Proceedings of the 14th International Conference on Auditory Display (ICAD 2008)*, Paris. Disponible : https://www.icad.org/Proceedings/2008/Hermann2008.pdf
Définition canonique : la sonification est « *the data-dependent generation of sound, if the transformation is systematic, objective and reproducible* ». Quatre conditions : (1) le son reflète des propriétés ou relations **objectives** des données d'entrée ; (2) la transformation est **systématique** ; (3) la sonification est **reproductible** ; (4) le système est utilisable avec **d'autres jeux de données**.

**C'est le critère opératoire pour trancher.** Un dispositif dont on ne peut pas décrire la fonction de transfert données→son, ni la rejouer à l'identique, ni l'appliquer à un autre jeu de données, n'est pas une sonification au sens ICAD : c'est un instrument de musique à contrôleur biologique.

**Hermann, T., Hunt, A. & Neuhoff, J. G. (éds.) (2011)**, *The Sonification Handbook*, Logos Verlag, Berlin, 586 p., ISBN 978-3-8325-2819-5. **Ouvrage en accès libre intégral** : https://sonification.de/handbook/ (PDF du livre entier et par chapitre). Couvre les trois familles techniques attendues : **audification** (lecture directe d'une série temporelle comme forme d'onde), **parameter mapping sonification** (mappage de dimensions de données sur des paramètres sonores — hauteur, timbre, durée, spatialisation), et **model-based sonification** (les données définissent un système physique virtuel que l'utilisateur excite ; le chapitre discute explicitement ses avantages et différences vis-à-vis du parameter mapping). Chapitres également sur la sonification interactive.

**Communauté** : International Community for Auditory Display (ICAD), icad.org, conférence annuelle depuis 1992, actes en accès libre.

### E.2 Les dispositifs de « musique des plantes » : ce qui est réellement mesuré

**PlantWave / MIDI Sprout (Data Garden, Joe Patitucci ; circuiterie de Sam Cusumano).**
Description technique de l'éditeur, verbatim depuis la page officielle « How it works » : « *PlantWave measures **microfluctuations in conductivity** between two points on a plant.* » et « *The amount of conductivity between these two points is **largely related to how much water there is between them**. That changes as plants photosynthesize and move chloroplasts around.* » Le circuit est celui d'un **psychogalvanomètre**, c'est-à-dire l'électronique d'un polygraphe / capteur de réponse électrodermale (GSR) humaine, adapté aux feuilles. La chaîne de traitement : variation électrique → tracé d'une onde dans le temps → conversion en messages de **hauteur** (notes) → les caractéristiques de l'onde contrôlent tempo et effets. L'éditeur reconnaît publiquement **n'avoir conduit aucune étude évaluée par les pairs**, s'appuyant sur un sondage d'utilisateurs de MIDI Sprout (relaxation, connexion, inspiration ressenties).
Filiation revendiquée : les expériences de **Cleve Backster** dans les années 1970 (plantes connectées à des capteurs GSR) — lignée scientifiquement disqualifiée.

**Damanhur / Music of the Plants** (fédération Damanhur, Piémont, Italie ; Oberto Airaudi dit « Falco Tarassaco »). Communauté fondée en 1975, premières expérimentations de communication végétale à partir de **1976**, explicitement inspirées de **Tompkins & Bird, *The Secret Life of Plants* (1973)**. Le dispositif mesure la **résistance** entre une électrode foliaire et une électrode au niveau des racines/du sol, et mappe chaque variation sur une valeur de note transmise par **interface MIDI**.
⚠️ **Aucune publication évaluée par les pairs sur ce dispositif n'a été trouvée.** Les seules sources disponibles sont la fondation elle-même, ses revendeurs et la presse non spécialisée.

### E.3 Critique méthodologique — ce que ces appareils mesurent vs ce qui est revendiqué

Formulation défendable scientifiquement :

1. **Grandeur mesurée** : une **impédance / conductance** entre deux électrodes de surface, mesurée par injection d'un courant faible. Ce n'est **pas** un potentiel d'action, **pas** un potentiel de variation, **pas** un potentiel systémique. Les AP/VP sont des **variations du potentiel transmembranaire mesurées en potentiométrie haute impédance** (idéalement Ag/AgCl, contre électrode de référence impolarisable), pas des variations d'impédance en amperométrie.
2. **Ce qui domine physiquement le signal** : l'**impédance de contact** électrode/cuticule (dépendante de la pression, du gel conducteur, du séchage), l'**état d'hydratation** du tissu — l'éditeur de PlantWave le dit lui-même —, la **polarisation d'électrode**, la température, l'humidité relative ambiante, et le **couplage électromagnétique du corps de l'opérateur et du secteur 50/60 Hz** (cf. Tran et al. 2019 sur la difficulté réelle de mesurer hors cage de Faraday).
3. **Absence de contrôles** : aucun de ces dispositifs commerciaux ne publie de contrôle « plante morte », « pot sans plante », « résistance équivalente », ni de test de reproductibilité inter-appareils. C'est exactement le type de contrôles que Khait et al. 2023 ont dû mettre en œuvre (pot sans plante : **0 son sur plus de 500 h**) pour que leur résultat soit publiable.
4. **Le mappage n'est pas neutre** : quantification en gamme (souvent pentatonique), lissage, quantification rythmique, réverbération et choix de timbre produisent l'essentiel de l'impression musicale « organique ». Autrement dit, **une part majeure de l'esthétique perçue est dans le mappage, pas dans la plante**. Un test décisif et honnête, à proposer : sonifier avec la même chaîne un bruit blanc filtré d'amplitude comparable — si l'auditeur ne distingue pas, la plante n'est pas la source de l'information musicale.
5. **Critère ICAD** (Hermann 2008) : ces dispositifs sont partiellement systématiques et reproductibles, mais ne visent pas l'**objectivité informationnelle** — ce ne sont pas des affichages auditifs de données, ce sont des instruments. **Les qualifier d'« instruments bio-contrôlés » est exact et défendable ; les qualifier de « traduction du langage des plantes » ne l'est pas.**

### E.4 Le versant scientifique légitime : l'« électrome »

Une littérature évaluée par les pairs mesure et analyse les signaux électriques de basse tension des plantes comme **séries temporelles** (concept d'« électrome », par analogie avec le génome/protéome) :

- **Souza, G. M., Ferreira, A. S., Saraiva, G. F. & Toledo, G. R. (2017)**, « Plant "electrome" can be pushed toward a self-organized critical state by external cues: evidences from a study with soybean seedlings subject to different environmental conditions », *Plant Signaling & Behavior* 12(3):e1290040, DOI 10.1080/15592324.2017.1290040, PMID 28277967. ⚠️ **Attention** : cet article est en *Plant Signaling & Behavior*, **pas** en *Theoretical and Experimental Plant Physiology* comme on le lit parfois. Chiffres rapportés (⚠️ issus d'une source secondaire, à revérifier sur le texte) : ligne de base des signaux **9,6 ± 1,2 mV**, avec des pics allant jusqu'à **500 mV** sous faible lumière et stress osmotique.
- **Debono, M.-W. & Souza, G. M. (2019)**, « Plants as electromic plastic interfaces: A mesological approach », *Progress in Biophysics and Molecular Biology* 146:123–133, DOI 10.1016/j.pbiomolbio.2019.02.007, PMID 30826433.
- **Simmi, F. Z., Dallagnol, L. J., Ferreira, A. S., Pereira, D. R. & Souza, G. M. (2020)**, *Bioelectrochemistry* 133:107493, DOI 10.1016/j.bioelechem.2020.107493 — détection d'infection fongique **avant symptômes visibles** par entropie approchée (ApEn) de l'électrome.
- **de Toledo, G. R. A., Reissig, G. N., Senko, L. G. S., Pereira, D. R., da Silva, A. F. & Souza, G. M. (2024)**, *Plant Signaling & Behavior* 19(1):2333144, DOI 10.1080/15592324.2024.2333144 — classification par apprentissage automatique, jusqu'à **100 % d'exactitude** (SVM) pour la détection du stress salin ; les changements électriques **précèdent** les altérations visibles de turgescence.

⚠️ **Réserve à formuler** : une partie de ce corpus (Parise, Debono, Souza, Gagliano, Marder) glisse vers un vocabulaire d'« attention » et de « cognition » végétales (ex. Parise et al. 2022, *Prog. Biophys. Mol. Biol.* 173:11–23, DOI 10.1016/j.pbiomolbio.2022.05.008 ; Parise et al. 2021, *Front. Plant Sci.* 12:594195, revendiquant « probablement la première preuve empirique d'attention chez les plantes »). **Les mesures d'électrome sont solides ; leur interprétation cognitive ne fait pas consensus.** C'est la même faille épistémique que celle décrite en §F.

---

## F. CE QUE LA SCIENCE NE DIT PAS

### F.1 Les trois confusions à démonter

1. **Signalisation électrique ≠ langage.** Un AP phloémien transporte un événement (« il s'est passé quelque chose de dommageable quelque part »), à vitesse ~1–10 cm/s, avec une information dont la richesse n'a jamais été mesurée en bits. Il n'y a ni syntaxe, ni lexique, ni intentionnalité d'émission, ni destinataire. Hedrich et al. 2016 emploient l'image du « câble » — une infrastructure de transmission, pas une langue.
2. **Réponse ≠ intention.** Le nectar d'*Oenothera* devient plus sucré en 3 min après un son de pollinisateur (Veits 2019) : c'est une chaîne mécanotransduction → réponse physiologique, sélectionnée parce qu'elle augmente le succès de pollinisation. Aucune donnée n'engage un état interne représentationnel.
3. **Complexité ≠ conscience.** L'électrome est complexe, non-linéaire, sensible aux stimuli, et classifiable par apprentissage automatique. La météorologie aussi.

**Et une quatrième, spécifique à la bioacoustique** : **émission ≠ communication.** Khait et al. 2023 démontrent l'**émission** aérienne et son **caractère informatif pour un observateur muni de microphones et d'un classifieur**. Ils écrivent que ces sons « *may also be detectable by other organisms* » — modal. Nardini et al. 2024 et Son et al. 2024 tranchent : la preuve expérimentale d'un rôle dans la communication plante-animal ou plante-plante **fait défaut** ; « *No evidence supports plant-to-plant acoustic communication.* » Le son est très probablement un **sous-produit physique de la cavitation**, comme un craquement de parquet qui sèche — informatif pour qui l'écoute, non émis pour être écouté.

### F.2 Le débat « plant neurobiology », chronologie et pièces vérifiées

**Brenner, E. D., Stahlberg, R., Mancuso, S., Vivanco, J., Baluška, F. & Van Volkenburgh, E. (2006)**, « Plant neurobiology: an integrated view of plant signaling », *Trends in Plant Science* 11(8):413–419, DOI 10.1016/j.tplants.2006.06.009. Programme fondateur : les plantes intègrent l'information environnementale via signaux électriques longue distance, transport d'auxine et molécules « neuronales ».

**Alpi, A., Amrhein, N., Bertl, A., Blatt, M. R., Blumwald, E., Cervone, F., Dainty, J., De Michelis, M. I., Epstein, E., Galston, A. W., Goldsmith, M. H. M., Hawes, C., Hell, R., Hetherington, A., Hofte, H., Juergens, G., Leaver, C. J., Moroni, A., Murphy, A., Oparka, K., Perata, P., Quader, H., Rausch, T., Ritzenthaler, C., Rivetta, A., Robinson, D. G., Sanders, D., Scheres, B., Schumacher, K., Sentenac, H., Slayman, C. L., Soave, C., Somerville, C., Taiz, L., Thiel, G. & Wagner, R. (2007)**, « Plant neurobiology: no brain, no gain? », *Trends in Plant Science* 12(4):135–136, DOI 10.1016/j.tplants.2007.03.002, PMID 17368081. **36 signataires** (liste complète ci-dessus, vérifiée). Argument : le préfixe « neuro- » a toujours désigné en biologie l'appareil physiologique et anatomique qui permet aux animaux de se comporter — cerveaux et systèmes nerveux — et les plantes n'en possèdent pas ; les analogies revendiquées (synapses, neurotransmetteurs) ne sont pas étayées par des structures homologues.

**Réplique** : Trewavas et al. (2007), « Plant neurobiology – all metaphors have value », *Trends in Plant Science*. ⚠️ **Auteurs, volume et pages non vérifiés** (identifiant ScienceDirect S1360138507000101X). À confirmer.

**Taiz, L., Alkon, D., Draguhn, A., Murphy, A., Blatt, M., Hawes, C., Thiel, G. & Robinson, D. G. (2019)**, « Plants Neither Possess nor Require Consciousness », *Trends in Plant Science* 24(8):677–687, DOI 10.1016/j.tplants.2019.05.008, PMID 31279732. Position : les plantes, dépourvues de neurones et a fortiori de cerveau, n'ont pas de conscience ; les structures invoquées par les tenants de la neurobiologie végétale n'ont pas les propriétés fonctionnelles requises.

**Suite du débat** (références vérifiées par PMID mais dont volume/pages restent à confirmer) :
- Calvo, P. & Trewavas, A. (2020), « Consciousness Facilitates Plant Behavior », *Trends in Plant Science*, PMID 31902571 — réponse à Taiz.
- Mallatt, J., Blatt, M. R., Draguhn, A., Robinson, D. G. & Taiz, L. (2020/2021), « Debunking a myth: plant consciousness », *Protoplasma*, PMID 33196907.

### F.3 La leçon de reproductibilité (Gagliano / Markel)

**Markel, K. (2020)**, « Lack of evidence for associative learning in pea plants », *eLife* 9:e57614, DOI 10.7554/eLife.57614, PMID 32573434. Tentative de réplication de Gagliano et al. (2016, conditionnement associatif de type pavlovien chez le pois en labyrinthe en Y), avec **effectif plus grand** et **analyse entièrement en aveugle** : échec de réplication.
**Gagliano, M., Vyazovskiy, V. V., Borbély, A. A., Depczynski, M. & Radford, B. (2020)**, « Comment on "Lack of evidence for associative learning in pea plants" », *eLife* 9:e61141, DOI 10.7554/eLife.61141, PMID 32909941 — protocole de Markel jugé inadapté.
**Markel, K. (2020)**, « Response to comment… », *eLife* 9:e61689, DOI 10.7554/eLife.61689, PMID 32909944 — les différences de dispositif n'expliquent pas l'échec.

→ Ce triptyque est **le cas d'école** à citer : il montre comment une revendication à fort retentissement médiatique dans le domaine « cognition végétale » se comporte sous réplication en aveugle. Il justifie la prudence à l'égard de l'ensemble du corpus de la même équipe, y compris les affirmations de bioacoustique racinaire (§B.4).

---

## G. RÉCAPITULATIF DE CE QUE JE N'AI PAS PU VÉRIFIER

À traiter comme **non consolidé** dans le manuscrit :

1. **Vitesse de l'onde calcique de Toyota et al. 2018** (souvent citée « ~1 mm/s ») — article inaccessible (403, hors PMC). **Ne pas chiffrer.**
2. **Bose, *The Nervous Mechanism of Plants* (1926)** — absent du catalogue Internet Archive interrogé ; attesté seulement en source secondaire.
3. **Darwin & Darwin, *The Power of Movement in Plants* (1880), John Murray** — non vérifié dans cette session.
4. **Vitesse de 200 mm/s chez *Dionaea* attribuée à Burdon-Sanderson 1873** — source secondaire uniquement.
5. **Tyree & Sperry 1989** — volume/pages (Annu. Rev. Plant Physiol. Plant Mol. Biol. 40:19–38) confirmés par l'en-tête du PDF, mais texte non extractible (scan sans OCR) ; les références Tyree & Dixon 1983, Tyree et al. 1984 et le moniteur 4615 DSM proviennent de sources secondaires.
6. **Gibert et al. 2006** — résumé non récupéré ; détails d'électrodes issus de sources secondaires.
7. **Gagliano et al. 2017 *Oecologia*** — volume/pages non vérifiés (DOI et PMID confirmés).
8. **Pyke et al. 2020 *Ecology Letters*** (critique de Veits) — volume/pages non vérifiés.
9. **Robinson et al. 2023 *Trends in Plant Science*** (« Mother trees, altruistic fungi… ») — volume/pages/DOI non vérifiés.
10. **Trewavas et al. 2007** (réponse à Alpi) — auteurs/volume/pages non vérifiés.
11. **Chiffres de Veits et al. 2019** — issus de la **préversion bioRxiv**, à recouper avec la version *Ecology Letters* publiée.
12. **Chiffres de Souza et al. 2017** (9,6 ± 1,2 mV ; pics 500 mV) — source secondaire.
13. **« Clics à 220 Hz » émis par les racines de maïs** — aucun article primaire avec données trouvé. **Traiter comme non établi.**
14. **« Carol Gibson-Wood »** — **aucune trace** de cette personne en bioacoustique végétale. Vraisemblablement une erreur à retirer.
15. **Damanhur / Music of the Plants** — aucune publication évaluée par les pairs ; uniquement sources de l'éditeur.
16. Article HESS 2025 sur le self-potential et la transpiration des arbres — existence confirmée (hess.copernicus.org/articles/29/2997/2025/), contenu non extrait.
17. **Contrainte de session** : le budget de recherche web (200 requêtes WebSearch) a été épuisé avant la fin ; les dernières vérifications ont été menées uniquement par appels directs à l'API Europe PMC. Quelques compléments (Jung et al. 2018 sur les réactions physiologiques évoquées par le son ; travaux de Zimmermann/Felle/Hafke sur les *system potentials*) n'ont pas pu être retrouvés et **manquent au dossier**.

---

## BIBLIOGRAPHIE

**A. Électrophysiologie — fondamentaux**

Blyth, M. G. & Morris, R. J. (2019). Shear-enhanced dispersion of a wound substance as a candidate mechanism for variation potential transmission. *Frontiers in Plant Science*, 10, 1393. DOI 10.3389/fpls.2019.01393

Bose, J. C. (1902). *Response in the Living and Non-Living*. Londres/New York : Longmans, Green & Co.

Bose, J. C. (1907). *Comparative Electro-Physiology: A Physico-Physiological Study*. Londres/New York : Longmans, Green & Co.

Bose, J. C. (1913). *Researches on Irritability of Plants*. Londres : Longmans, Green & Co.

Bose, J. C. (1926). *The Nervous Mechanism of Plants*. Londres : Longmans, Green & Co. [référence non vérifiée en catalogue]

Burdon-Sanderson, J. (1873). Note on the electrical phenomena which accompany irritation of the leaf of *Dionæa muscipula*. *Proceedings of the Royal Society of London*, 21, 495–496.

Darwin, C. & Darwin, F. (1880). *The Power of Movement in Plants*. Londres : John Murray. [non vérifié dans cette session]

Fromm, J. & Lautner, S. (2007). Electrical signals and their physiological significance in plants. *Plant, Cell & Environment*, 30(3), 249–257. DOI 10.1111/j.1365-3040.2006.01614.x — PMID 17263772

Hedrich, R. & Kreuzer, I. (2023). Demystifying the Venus flytrap action potential. *New Phytologist*, 239(6), 2108–2112. DOI 10.1111/nph.19113 — PMID 37424515

Hedrich, R., Salvador-Recatalà, V. & Dreyer, I. (2016). Electrical Wiring and Long-Distance Plant Communication. *Trends in Plant Science*, 21(5), 376–387. DOI 10.1016/j.tplants.2016.01.016 — PMID 26880317

Ibacache-Carrión, F., Bolua-Hernández, Y., Michard, E. & Ramírez, C. C. (2026). Action Potentials and Slow Wave Potentials Exhibit Distinct Phloem Propagation Velocities in *Vicia faba*. *Physiologia Plantarum*, 178(4), e71066. DOI 10.1111/ppl.71066 — PMID 42596572

Mousavi, S. A. R., Chauvin, A., Pascaud, F., Kellenberger, S. & Farmer, E. E. (2013). GLUTAMATE RECEPTOR-LIKE genes mediate leaf-to-leaf wound signalling. *Nature*, 500(7463), 422–426. DOI 10.1038/nature12478 — PMID 23969459

Mudrilov, M., Ladeynova, M., Grinberg, M., Balalaeva, I. & Vodeneev, V. (2021). Electrical Signaling of Plants under Abiotic Stressors: Transmission of Stimulus-Specific Information. *International Journal of Molecular Sciences*, 22(19), 10715. DOI 10.3390/ijms221910715

Nguyen, C. T., Kurenda, A., Stolz, S., Chételat, A. & Farmer, E. E. (2018). Identification of cell populations necessary for leaf-to-leaf electrical signaling in a wounded plant. *PNAS*, 115(40), 10178–10183. DOI 10.1073/pnas.1807049115 — PMID 30228123

Toyota, M., Spencer, D., Sawai-Toyota, S., Jiaqi, W., Zhang, T., Koo, A. J., Howe, G. A. & Gilroy, S. (2018). Glutamate triggers long-distance, calcium-based plant defense signaling. *Science*, 361(6407), 1112–1115. DOI 10.1126/science.aat7744 — PMID 30213912

Vodeneev, V., Akinchits, E. & Sukhov, V. (2015). Variation potential in higher plants: Mechanisms of generation and propagation. *Plant Signaling & Behavior*, 10(9), e1057365. DOI 10.1080/15592324.2015.1057365 — PMID 26313506

Volkov, A. G., Adesina, T. & Jovanov, E. (2007). Closing of Venus flytrap by electrical stimulation of motor cells. *Plant Signaling & Behavior*, 2(3), 139–145. DOI 10.4161/psb.2.3.4217

Volkov, A. G., Lang, R. D. & Volkova-Gugeshashvili, M. I. (2007). Electrical signaling in *Aloe vera* induced by localized thermal stress. *Bioelectrochemistry*, 71(2), 192–197. DOI 10.1016/j.bioelechem.2007.04.006 — PMID 17544342

Volkov, A. G., Carrell, H., Baldwin, A. & Markin, V. S. (2009). Electrical memory in Venus flytrap. *Bioelectrochemistry*, 75(2), 142–147. DOI 10.1016/j.bioelechem.2009.03.005

Volkov, A. G., Carrell, H. & Markin, V. S. (2009). Biologically closed electrical circuits in Venus flytrap. *Plant Physiology*, 149(4), 1661–1667. DOI 10.1104/pp.108.134536

Volkov, A. G., Baker, K., Foster, J. C., Clemmons, J., Jovanov, E. & Markin, V. S. (2011). Circadian variations in biologically closed electrochemical circuits in *Aloe vera* and *Mimosa pudica*. *Bioelectrochemistry*, 81(1), 39–45. DOI 10.1016/j.bioelechem.2011.01.004

Volkov, A. G., Harris, S. L., Vilfranc, C. L., Murphy, V. A., Wooten, J. D., Paulicin, H., Volkova, M. I. & Markin, V. S. (2013). Venus flytrap biomechanics: forces in the *Dionaea muscipula* trap. *Journal of Plant Physiology*, 170(1), 25–32. DOI 10.1016/j.jplph.2012.08.009

Volkov, A. G., Vilfranc, C. L., Murphy, V. A., Mitchell, C. M., Volkova, M. I., O'Neal, L. & Markin, V. S. (2013). Electrotonic and action potentials in the Venus flytrap. *Journal of Plant Physiology*, 170(9), 838–846. DOI 10.1016/j.jplph.2013.01.009

Volkov, A. G. (2019). Signaling in electrical networks of the Venus flytrap (*Dionaea muscipula* Ellis). *Bioelectrochemistry*, 125, 25–32. DOI 10.1016/j.bioelechem.2018.09.001

Wu, Q., Li, Y., Chen, M. & Kong, X. (2024). Companion cell mediates wound-stimulated leaf-to-leaf electrical signaling. *PNAS*, 121(24), e2400639121. DOI 10.1073/pnas.2400639121 — PMID 38838018

**B. Arbres : électrophysiologie in situ, flux de sève, émissions acoustiques**

Fernández, E., Fernández, R. J. & Bilmes, G. M. (2012). Natural and laser-induced cavitation in corn stems: On the mechanisms of acoustic emissions. *Papers in Physics*, 4, 040003. DOI 10.4279/PIP.040003

Gagliano, M., Mancuso, S. & Robert, D. (2012). Towards understanding plant bioacoustics. *Trends in Plant Science*, 17(6), 323–325. DOI 10.1016/j.tplants.2012.03.002

Gagliano, M., Renton, M., Duvdevani, N., Timmins, M. & Mancuso, S. (2012). Out of sight but not out of mind: Alternative means of communication in plants. *PLoS ONE*, 7(5), e37382. DOI 10.1371/journal.pone.0037382

Gagliano, M., Grimonprez, M., Depczynski, M. & Renton, M. (2017). Tuned in: plant roots use sound to locate water. *Oecologia*. DOI 10.1007/s00442-017-3862-z — PMID 28382479

Gibert, D., Le Mouël, J.-L., Lambs, L., Nicollin, F. & Perrier, F. (2006). Sap flow and daily electric potential variations in a tree trunk. *Plant Science*, 171(5), 572–584. DOI 10.1016/j.plantsci.2006.06.012

Gurovich, L. A. & Hermosilla, P. (2009). Electric signalling in fruit trees in response to water applications and light–darkness conditions. *Journal of Plant Physiology*, 166(3), 290–300. DOI 10.1016/j.jplph.2008.06.004

Hao, Z., Li, W. & Hao, X. (2021). Variations of electric potential in the xylem of tree trunks associated with water content rhythms. *Journal of Experimental Botany*, 72(4), 1321–1335. DOI 10.1093/jxb/eraa492

Milburn, J. A. & Johnson, R. P. C. (1966). The conduction of sap. II. Detection of vibrations produced by sap cavitation in *Ricinus* xylem. *Planta*, 69, 43–52. DOI 10.1007/BF00380209

Nolf, M., Beikircher, B., Rosner, S., Nolf, A. & Mayr, S. (2015). Xylem cavitation resistance can be estimated based on time-dependent rate of acoustic emissions. *New Phytologist*, 208(2), 625–632. DOI 10.1111/nph.13476 — PMID 26010417

Oyarce, P. & Gurovich, L. (2010). Electrical signals in avocado trees: Responses to light and water availability conditions. *Plant Signaling & Behavior*, 5(1), 34–41. DOI 10.4161/psb.5.1.10157 — PMID 20592805

Ríos-Rojas, L., Tapia, F. & Gurovich, L. A. (2014). Electrophysiological assessment of water stress in fruit-bearing woody plants. *Journal of Plant Physiology*, 171(10), 799–806. DOI 10.1016/j.jplph.2014.02.005

Ríos-Rojas, L., Morales-Moraga, D., Alcalde, J. A. & Gurovich, L. A. (2015). Use of plant woody species electrical potential for irrigation scheduling. *Plant Signaling & Behavior*, 10(2), e976487. DOI 10.4161/15592324.2014.976487

Ritman, K. T. & Milburn, J. A. (1988). Acoustic emissions from plants: ultrasonic and audible compared. *Journal of Experimental Botany*, 39, 1237–1248. DOI 10.1093/jxb/39.9.1237

Tran, D., Dutoit, F., Najdenovska, E., Wallbridge, N., Plummer, C., Mazza, M., Raileanu, L. E. & Camps, C. (2019). Electrophysiological assessment of plant status outside a Faraday cage using supervised machine learning. *Scientific Reports*, 9, 17073. DOI 10.1038/s41598-019-53675-4 — PMID 31745185

Tyree, M. T. & Sperry, J. S. (1989). Vulnerability of xylem to cavitation and embolism. *Annual Review of Plant Physiology and Plant Molecular Biology*, 40, 19–38.

**C. Bioacoustique**

Khait, I., Lewin-Epstein, O., Sharon, R., Saban, K., Goldstein, R., Anikster, Y., Zeron, Y., Agassy, C., Nizan, S., Sharabi, G., Perelman, R., Boonman, A., Sade, N., Yovel, Y. & Hadany, L. (2023). Sounds emitted by plants under stress are airborne and informative. *Cell*, 186(7), 1328–1336.e10. DOI 10.1016/j.cell.2023.03.009 — PMID 37001499. Données : Dryad DOI 10.5061/dryad.jwstqjqf7 ; code : Zenodo DOI 10.5281/zenodo.7612742

Mishra, R. C., Ghosh, R. & Bae, H. (2016). Plant acoustics: in the search of a sound mechanism for sound signaling in plants. *Journal of Experimental Botany*, 67(15), 4483–4494. DOI 10.1093/jxb/erw235 — PMID 27342223

Nardini, A., Cochard, H. & Mayr, S. (2024). Talk is cheap: rediscovering sounds made by plants. *Trends in Plant Science*, 29(6), 662–667. DOI 10.1016/j.tplants.2023.11.023 — PMID 38218649

Pyke, G. H., et al. (2020). Changes in floral nectar are unlikely adaptive responses to pollinator flight sound. *Ecology Letters*. DOI 10.1111/ele.13403 [volume/pages non vérifiés]

Son, J. S., Jang, S., Mathevon, N. & Ryu, C.-M. (2024). Is plant acoustic communication fact or fiction? *New Phytologist*, 242(5), 1876–1880. DOI 10.1111/nph.19648 — PMID 38424727

Veits, M., Khait, I., Obolski, U., Zinger, E., Boonman, A., Goldshtein, A., Saban, K., Seltzer, R., Ben-Dor, U., Estlein, P., Kabat, A., Peretz, D., Ratzersdorfer, I., Krylov, S., Chamovitz, D., Sapir, Y., Yovel, Y. & Hadany, L. (2019). Flowers respond to pollinator sound within minutes by increasing nectar sugar concentration. *Ecology Letters*, 22(9), 1483–1492. DOI 10.1111/ele.13331 — PMID 31286633. Données : Dryad DOI 10.5061/dryad.6n5h0pb

**D. Réseaux mycorhiziens**

Henriksson, N., et al. (2023). Re-examining the evidence for the mother tree hypothesis – resource sharing among trees via ectomycorrhizal networks. *New Phytologist*, 239, 19–28. DOI 10.1111/nph.18935

Karst, J., Jones, M. D. & Hoeksema, J. D. (2023). Positive citation bias and overinterpreted results lead to misinformation on common mycorrhizal networks in forests. *Nature Ecology & Evolution*, 7(4), 501–511. DOI 10.1038/s41559-023-01986-1 — PMID 36782032. [Author Correction : *Nat. Ecol. Evol.*, 7, 623. DOI 10.1038/s41559-023-02035-7]

Kiers, E. T., Duhamel, M., Beesetty, Y., Mensah, J. A., Franken, O., Verbruggen, E., Fellbaum, C. R., Kowalchuk, G. A., Hart, M. M., Bago, A., Palmer, T. M., West, S. A., Vandenkoornhuyse, P., Jansa, J. & Bücking, H. (2011). Reciprocal rewards stabilize cooperation in the mycorrhizal symbiosis. *Science*, 333(6044), 880–882. DOI 10.1126/science.1208473 — PMID 21836016

Klein, T., Siegwolf, R. T. W. & Körner, C. (2016). Belowground carbon trade among tall trees in a temperate forest. *Science*, 352(6283), 342–344. DOI 10.1126/science.aad6188 — PMID 27081070

Robinson, D., et al. (2023). Mother trees, altruistic fungi, and the perils of plant personification. *Trends in Plant Science*. [DOI/volume/pages non vérifiés]

Simard, S. W., Perry, D. A., Jones, M. D., Myrold, D. D., Durall, D. M. & Molina, R. (1997). Net transfer of carbon between ectomycorrhizal tree species in the field. *Nature*, 388, 579–582. DOI 10.1038/41557

Simard, S. W., Ryan, M. & Perry, D. (2025). Opinion: Response to questions about common mycorrhizal networks. *Frontiers in Forests and Global Change*. DOI 10.3389/ffgc.2024.1512518

**E. Sonification**

Debono, M.-W. & Souza, G. M. (2019). Plants as electromic plastic interfaces: A mesological approach. *Progress in Biophysics and Molecular Biology*, 146, 123–133. DOI 10.1016/j.pbiomolbio.2019.02.007 — PMID 30826433

Hermann, T. (2008). Taxonomy and definitions for sonification and auditory display. *Proceedings of the 14th International Conference on Auditory Display (ICAD 2008)*, Paris. https://www.icad.org/Proceedings/2008/Hermann2008.pdf

Hermann, T., Hunt, A. & Neuhoff, J. G. (éds.) (2011). *The Sonification Handbook*. Berlin : Logos Verlag, 586 p. ISBN 978-3-8325-2819-5. Accès libre : https://sonification.de/handbook/

Simmi, F. Z., Dallagnol, L. J., Ferreira, A. S., Pereira, D. R. & Souza, G. M. (2020). Electrome alterations in a plant-pathogen system: Toward early diagnosis. *Bioelectrochemistry*, 133, 107493. DOI 10.1016/j.bioelechem.2020.107493 — PMID 32145516

Souza, G. M., Ferreira, A. S., Saraiva, G. F. & Toledo, G. R. (2017). Plant "electrome" can be pushed toward a self-organized critical state by external cues: evidences from a study with soybean seedlings subject to different environmental conditions. *Plant Signaling & Behavior*, 12(3), e1290040. DOI 10.1080/15592324.2017.1290040 — PMID 28277967

de Toledo, G. R. A., Reissig, G. N., Senko, L. G. S., Pereira, D. R., da Silva, A. F. & Souza, G. M. (2024). Bean plants' electrome under different water availabilities. *Plant Signaling & Behavior*, 19(1), 2333144. DOI 10.1080/15592324.2024.2333144 — PMID 38545860

Tompkins, P. & Bird, C. (1973). *The Secret Life of Plants*. New York : Harper & Row. [source historique du courant Damanhur/Backster ; ouvrage non scientifique]

PlantWave / Data Garden. « How It Works ». https://plantwave.com/pages/how-it-works [source commerciale]

Damanhur Foundation. « The Music of the Plants ». https://www.damanhur.foundation/project/the-music-of-the-plants/ ; https://www.musicoftheplants.com/history/ [sources non scientifiques]

**F. Débat épistémologique**

Alpi, A., Amrhein, N., Bertl, A., Blatt, M. R., Blumwald, E., Cervone, F., Dainty, J., De Michelis, M. I., Epstein, E., Galston, A. W., Goldsmith, M. H. M., Hawes, C., Hell, R., Hetherington, A., Hofte, H., Juergens, G., Leaver, C. J., Moroni, A., Murphy, A., Oparka, K., Perata, P., Quader, H., Rausch, T., Ritzenthaler, C., Rivetta, A., Robinson, D. G., Sanders, D., Scheres, B., Schumacher, K., Sentenac, H., Slayman, C. L., Soave, C., Somerville, C., Taiz, L., Thiel, G. & Wagner, R. (2007). Plant neurobiology: no brain, no gain? *Trends in Plant Science*, 12(4), 135–136. DOI 10.1016/j.tplants.2007.03.002 — PMID 17368081

Brenner, E. D., Stahlberg, R., Mancuso, S., Vivanco, J., Baluška, F. & Van Volkenburgh, E. (2006). Plant neurobiology: an integrated view of plant signaling. *Trends in Plant Science*, 11(8), 413–419. DOI 10.1016/j.tplants.2006.06.009

Calvo, P. & Trewavas, A. (2020). Consciousness Facilitates Plant Behavior. *Trends in Plant Science*. PMID 31902571 [volume/pages non vérifiés]

Gagliano, M., Vyazovskiy, V. V., Borbély, A. A., Depczynski, M. & Radford, B. (2020). Comment on "Lack of evidence for associative learning in pea plants". *eLife*, 9, e61141. DOI 10.7554/eLife.61141 — PMID 32909941

Mallatt, J., Blatt, M. R., Draguhn, A., Robinson, D. G. & Taiz, L. (2021). Debunking a myth: plant consciousness. *Protoplasma*. PMID 33196907 [volume/pages non vérifiés]

Markel, K. (2020). Lack of evidence for associative learning in pea plants. *eLife*, 9, e57614. DOI 10.7554/eLife.57614 — PMID 32573434

Markel, K. (2020). Response to comment on "Lack of evidence for associative learning in pea plants". *eLife*, 9, e61689. DOI 10.7554/eLife.61689 — PMID 32909944

Parise, A. G., de Toledo, G. R. A., Oliveira, T. F. C., Souza, G. M., Castiello, U., Gagliano, M. & Marder, M. (2022). Do plants pay attention? A possible phenomenological-empirical approach. *Progress in Biophysics and Molecular Biology*, 173, 11–23. DOI 10.1016/j.pbiomolbio.2022.05.008 — PMID 35636584

Taiz, L., Alkon, D., Draguhn, A., Murphy, A., Blatt, M., Hawes, C., Thiel, G. & Robinson, D. G. (2019). Plants Neither Possess nor Require Consciousness. *Trends in Plant Science*, 24(8), 677–687. DOI 10.1016/j.tplants.2019.05.008 — PMID 31279732

Trewavas, A., et al. (2007). Response to Alpi et al.: Plant neurobiology – all metaphors have value. *Trends in Plant Science*. [auteurs/volume/pages non vérifiés]

---

**Fichiers de travail conservés** (extractions texte, réutilisables) :
- `/tmp/claude-1000/-home-tgayet-Documents-PERSO-ateliers-bn-musique-of-the-plants-2/58c7695f-7bcb-4c6f-a97c-e38a491bf3e7/scratchpad/khait.txt` — texte intégral de Khait et al. 2023 (*Cell*), 983 lignes, incluant les STAR Methods.
- `/tmp/claude-1000/-home-tgayet-Documents-PERSO-ateliers-bn-musique-of-the-plants-2/58c7695f-7bcb-4c6f-a97c-e38a491bf3e7/scratchpad/ijms.txt` — texte intégral de Mudrilov et al. 2021 (*IJMS* 22:10715), revue de 38 pages sur la signalisation électrique sous stress abiotiques (Box 1 = définitions AP/VP/SP).