# INDEX des sources — Communication végétale / « langage » des plantes

Constitution du fonds : **17 septembre 2026**
Répertoire racine : `sources/`
Règle appliquée : **accès ouvert et sources officielles uniquement** (PubMed Central / Europe PMC, bioRxiv, arXiv, MDPI, Frontiers, PLOS, Nature Portfolio, Science Advances, Royal Society, HAL, Internet Archive, Project Gutenberg, sites constructeurs). Aucun site pirate n'a été utilisé.

| Dossier | Fichiers | Volume |
|---|---|---|
| `documents/articles-scientifiques/` | 45 | ~69 Mo |
| `documents/domaine-public/` | 11 | ~258 Mo |
| `documents/presse/` | 12 | ~152 Ko |
| `brevets/` | 13 | ~17 Mo |
| `datasheets/` | 9 | ~9,8 Mo |
| `manufacturer-manuals/` | 11 | ~20 Mo |
| `schemas/` | 66 | ~3,0 Mo |
| `code/` | 17 | ~116 Mo |
| `software/` | 52 | ~701 Mo |
| `reverse/` | 1 | ~28 Ko |
| **Total** | **248** | **~1,2 Go** |

> **Chiffres relevés le 2026-09-18** par `find sources/<dossier> -type f | wc -l`
> et `du -sh`. L'essentiel de ce corpus **n'est pas versionné** : les
> fac-similés sous droits, les numérisations du domaine public et les 69
> dépôts tiers sont écartés par `.gitignore`. Ce qui est versionné, ce sont
> les **références** que voici, nos **notes de lecture** (`.md`), les
> **transcriptions** en texte, et les projets tiers de `schemas/` — ceux-là
> avec leur fichier de licence. Voir `../README.md`, § 11.

Deux fichiers sont au format `.md` et non `.pdf` : le PDF éditeur était bloqué par une protection anti-robot, mais le **texte intégral** (licence ouverte) a été récupéré en XML JATS via l'API Europe PMC puis converti en Markdown. Ils sont signalés par la mention *(texte intégral .md)*.

---

## 1. Articles scientifiques — `documents/articles-scientifiques/`

### 1.1 Bioacoustique végétale (sons émis / sons perçus)

| Fichier | Référence complète | DOI / URL | Taille | Thème |
|---|---|---|---|---|
| `2023-Khait-sounds-emitted-by-plants-under-stress-cell.pdf` | Khait I., Lewin-Epstein O., Sharon R., *et al.* (2023). *Sounds emitted by plants under stress are airborne and informative.* **Cell** 186(7), 1328-1336.e10 | [10.1016/j.cell.2023.03.009](https://doi.org/10.1016/j.cell.2023.03.009) | 6,1 Mo | Émissions ultrasonores, ML, cavitation |
| `2019-Khait-plants-emit-informative-airborne-sounds-biorxiv.pdf` | Khait I., Lewin-Epstein O., Sharon R., *et al.* (2019). *Plants emit informative airborne sounds under stress.* **bioRxiv** 507590 v4 (préimpression de l'article Cell 2023) | [10.1101/507590](https://doi.org/10.1101/507590) | 1,1 Mo | Préimpression bioacoustique |
| `2019-Veits-flowers-respond-to-pollinator-sound-biorxiv.pdf` | Veits M., Khait I., Obolski U., *et al.* (2018). *Flowers respond to pollinator sound within minutes by increasing nectar sugar concentration.* **bioRxiv** 507319 v1 (publié : Ecology Letters 22:1483-1492, 2019) | [10.1101/507319](https://doi.org/10.1101/507319) — version publiée [10.1111/ele.13331](https://doi.org/10.1111/ele.13331) | 846 Ko | Audition florale, phonotropisme |
| `2012-Gagliano-green-symphonies-acoustic-communication-plants.md` | Gagliano M. (2013). *Green symphonies: a call for studies on acoustic communication in plants.* **Behavioral Ecology** 24(4), 789-796 *(texte intégral .md — Europe PMC)* | [10.1093/beheco/ars206](https://doi.org/10.1093/beheco/ars206) | 49 Ko | Manifeste bioacoustique |
| `2014-Appel-Cocroft-plants-respond-to-leaf-vibrations-herbivore-chewing.md` | Appel H. M., Cocroft R. B. (2014). *Plants respond to leaf vibrations caused by insect herbivore chewing.* **Oecologia** 175(4), 1257-1266 *(texte intégral .md — Europe PMC)* | [10.1007/s00442-014-2995-6](https://doi.org/10.1007/s00442-014-2995-6) | 50 Ko | Vibrations, défense induite |
| `2016-Ghosh-sound-vibrations-transcriptomic-proteomic-hormonal-arabidopsis.pdf` | Ghosh R., Mishra R. C., Choi B., *et al.* (2016). *Exposure to Sound Vibrations Lead to Transcriptomic, Proteomic and Hormonal Changes in Arabidopsis.* **Scientific Reports** 6, 33370 | [10.1038/srep33370](https://doi.org/10.1038/srep33370) | 7,6 Mo | Perception sonore, transcriptome |
| `2017-Ghosh-sound-vibration-regulated-genes-touch-treatment-arabidopsis.pdf` | Ghosh R., Gururani M. A., Ponpandian L. N., *et al.* (2017). *Expression Analysis of Sound Vibration-Regulated Genes by Touch Treatment in Arabidopsis.* **Frontiers in Plant Science** 8, 100 | [10.3389/fpls.2017.00100](https://doi.org/10.3389/fpls.2017.00100) | 4,6 Mo | Son vs toucher, mécanoperception |
| `2017-Choi-sound-vibration-treatment-arabidopsis-botrytis-resistance.pdf` | Choi B., Ghosh R., Gururani M. A., *et al.* (2017). *Positive regulatory role of sound vibration treatment in Arabidopsis thaliana against Botrytis cinerea infection.* **Scientific Reports** 7, 2527 | [10.1038/s41598-017-02556-9](https://doi.org/10.1038/s41598-017-02556-9) | 2,6 Mo | Son et immunité végétale |
| `2018-Jung-beyond-chemical-triggers-sound-evoked-physiological-reactions-plants.pdf` | Jung J., Kim S.-K., Kim J. Y., Jeong M.-J., Ryu C.-M. (2018). *Beyond Chemical Triggers: Evidence for Sound-Evoked Physiological Reactions in Plants.* **Frontiers in Plant Science** 9, 25 | [10.3389/fpls.2018.00025](https://doi.org/10.3389/fpls.2018.00025) | 1,8 Mo | Revue — réactions au son |
| `2016-DeRoo-acoustic-emissions-drought-induced-cavitation-plants.pdf` | De Roo L., Vergeynst L. L., De Baerdemaeker N. J. F., Steppe K. (2016). *Acoustic Emissions to Measure Drought-Induced Cavitation in Plants.* **Applied Sciences** 6(3), 71 | [10.3390/app6030071](https://doi.org/10.3390/app6030071) | 1,4 Mo | Émissions ultrasonores par cavitation (méthodes, capteurs) |

### 1.2 Électrophysiologie végétale

| Fichier | Référence complète | DOI / URL | Taille | Thème |
|---|---|---|---|---|
| `2021-Mudrilov-electrical-signaling-plants-abiotic-stressors-stimulus-specific-information.pdf` | Mudrilov M., Ladeynova M., Grinberg M., *et al.* (2021). *Electrical Signaling of Plants under Abiotic Stressors: Transmission of Stimulus-Specific Information.* **Int. J. Molecular Sciences** 22(19), 10715 | [10.3390/ijms221910715](https://doi.org/10.3390/ijms221910715) | 2,8 Mo | Revue — potentiels d'action / potentiels de variation |
| `2017-Szechynska-Hebda-electrical-signaling-photosynthesis-systemic-acclimation.pdf` | Szechyńska-Hebda M., Lewandowska M., Karpiński S. (2017). *Electrical Signaling, Photosynthesis and Systemic Acquired Acclimation.* **Frontiers in Physiology** 8, 684 | [10.3389/fphys.2017.00684](https://doi.org/10.3389/fphys.2017.00684) | 2,8 Mo | Signaux électriques systémiques |
| `2023-ArmadaMoreira-plant-electrophysiology-organic-electronics-venus-flytrap.pdf` | Armada-Moreira A., Dar A. M., Zhao Z., *et al.* (2023). *Plant electrophysiology with conformable organic electronics: Deciphering the propagation of Venus flytrap action potentials.* **Science Advances** 9(30), eadh4443 | [10.1126/sciadv.adh4443](https://doi.org/10.1126/sciadv.adh4443) | 1,4 Mo | Électrodes conformables, mesure in vivo |
| `2015-Chatterjee-classification-external-stimuli-plant-electrophysiological-signals.pdf` | Chatterjee S. K., Das S., Maharatna K., Masi E., Santopolo L., Mancuso S., Vitaletti A. (2015). *Exploring strategies for classification of external stimuli using statistical features of the plant electrical response.* **J. R. Soc. Interface** 12(104), 20141225 | [10.1098/rsif.2014.1225](https://doi.org/10.1098/rsif.2014.1225) | 1,2 Mo | Traitement du signal, classification |
| `2019-Tran-electrophysiological-assessment-plant-status-outside-faraday-cage-machine-learning.pdf` | Tran D., Dutoit F., Najdenovska E., *et al.* (2019). *Electrophysiological assessment of plant status outside a Faraday cage using supervised machine learning.* **Scientific Reports** 9, 17073 | [10.1038/s41598-019-53675-4](https://doi.org/10.1038/s41598-019-53675-4) | 1,4 Mo | **Mesure hors cage de Faraday** (très utile pour un montage DIY) |
| `2021-Najdenovska-classification-plant-electrophysiology-spider-mites-tomato.pdf` | Najdenovska E., Dutoit F., Tran D., *et al.* (2021). *Classification of Plant Electrophysiology Signals for Detection of Spider Mites Infestation in Tomatoes.* **Applied Sciences** 11(4), 1414 | [10.3390/app11041414](https://doi.org/10.3390/app11041414) | 2,8 Mo | Électrophysiologie + apprentissage automatique |
| `2014-Savatin-wounding-in-the-plant-tissue-defense-dangerous-passage.pdf` | Savatin D. V., Gramegna G., Modesti V., Cervone F. (2014). *Wounding in the plant tissue: the defense of a dangerous passage.* **Frontiers in Plant Science** 5, 470 | [10.3389/fpls.2014.00470](https://doi.org/10.3389/fpls.2014.00470) | 1,1 Mo | Signalisation de blessure (contexte Toyota 2018) |

### 1.3 Signalisation chimique, VOC, allélopathie

| Fichier | Référence complète | DOI / URL | Taille | Thème |
|---|---|---|---|---|
| `2022-Midzi-stress-induced-volatile-emissions-interplant-communication.pdf` | Midzi J., Jeffery D. W., Baumann U., *et al.* (2022). *Stress-Induced Volatile Emissions and Signalling in Inter-Plant Communication.* **Plants** 11(19), 2566 | [10.3390/plants11192566](https://doi.org/10.3390/plants11192566) | 5,3 Mo | Revue — COV et communication inter-plantes |
| `2013-Holopainen-where-do-herbivore-induced-plant-volatiles-go.pdf` | Holopainen J. K., Blande J. D. (2013). *Where do herbivore-induced plant volatiles go?* **Frontiers in Plant Science** 4, 185 | [10.3389/fpls.2013.00185](https://doi.org/10.3389/fpls.2013.00185) | 2,0 Mo | Dispersion des COV, « écoute » des voisins |
| `2015-Erb-indole-essential-herbivore-induced-volatile-priming-signal-maize.pdf` | Erb M., Veyrat N., Robert C. A. M., *et al.* (2015). *Indole is an essential herbivore-induced volatile priming signal in maize.* **Nature Communications** 6, 6273 | [10.1038/ncomms7273](https://doi.org/10.1038/ncomms7273) | 783 Ko | Signal volatil identifié (priming) |
| `2013-Furstenberg-Hagg-plant-defense-against-insect-herbivores.pdf` | Fürstenberg-Hägg J., Zagrobelny M., Bak S. (2013). *Plant Defense against Insect Herbivores.* **Int. J. Molecular Sciences** 14(5), 10242-10297 | [10.3390/ijms140510242](https://doi.org/10.3390/ijms140510242) | 1,0 Mo | Revue générale défense / signalisation |
| `2019-Kong-allelochemicals-and-signaling-chemicals-in-plants.pdf` | Kong C.-H., Xuan T. D., Khanh T. D., *et al.* (2019). *Allelochemicals and Signaling Chemicals in Plants.* **Molecules** 24(15), 2737 | [10.3390/molecules24152737](https://doi.org/10.3390/molecules24152737) | 392 Ko | Allélopathie |
| `2024-Kong-chemically-mediated-plant-plant-interactions-allelopathy-allelobiosis.pdf` | Kong C.-H., Li Z., Li F.-L., *et al.* (2024). *Chemically Mediated Plant–Plant Interactions: Allelopathy and Allelobiosis.* **Plants** 13(5), 626 | [10.3390/plants13050626](https://doi.org/10.3390/plants13050626) | 1,6 Mo | Allélopathie / allélobiose (état de l'art) |
| `2015-Cheng-plant-allelopathy-agriculture-physiological-ecological-mechanisms.pdf` | Cheng F., Cheng Z. (2015). *Research Progress on the use of Plant Allelopathy in Agriculture and the Physiological and Ecological Mechanisms of Allelopathy.* **Frontiers in Plant Science** 6, 1020 | [10.3389/fpls.2015.01020](https://doi.org/10.3389/fpls.2015.01020) | 1,3 Mo | Allélopathie appliquée |

### 1.4 Réseaux mycorhiziens (« wood-wide web »)

| Fichier | Référence complète | DOI / URL | Taille | Thème |
|---|---|---|---|---|
| `2010-Song-interplant-communication-tomato-mycorrhizal-networks.pdf` | Song Y. Y., Zeng R. S., Xu J. F., *et al.* (2010). *Interplant Communication of Tomato Plants through Underground Common Mycorrhizal Networks.* **PLoS ONE** 5(10), e13324 | [10.1371/journal.pone.0013324](https://doi.org/10.1371/journal.pone.0013324) | 2,6 Mo | Expérience clé de signalisation par réseau mycorhizien |
| `2015-Gorzelak-interplant-communication-mycorrhizal-networks-adaptive-behaviour.pdf` | Gorzelak M. A., Asay A. K., Pickles B. J., Simard S. W. (2015). *Inter-plant communication through mycorrhizal networks mediates complex adaptive behaviour in plant communities.* **AoB Plants** 7, plv050 | [10.1093/aobpla/plv050](https://doi.org/10.1093/aobpla/plv050) | 343 Ko | Revue (école Simard) — à lire avec la critique Karst 2023 |

> ⚠️ La critique **Karst, Jones & Hoeksema (2023)**, essentielle pour équilibrer cette section, est sous paywall — voir § « Références non téléchargeables ». La page Wikipédia `documents/presse/wikipedia-en-mycorrhizal-network.md` en résume le contenu et la controverse.

### 1.5 Cognition, « neurobiologie végétale », conscience

| Fichier | Référence complète | DOI / URL | Taille | Thème |
|---|---|---|---|---|
| `2021-Mallatt-debunking-a-myth-plant-consciousness.md` | Mallatt J., Blatt M. R., Draguhn A., Robinson D. G., Taiz L. (2021). *Debunking a myth: plant consciousness.* **Protoplasma** 258(3), 459-476 *(texte intégral .md — Europe PMC)* | [10.1007/s00709-020-01579-w](https://doi.org/10.1007/s00709-020-01579-w) | 81 Ko | **Position sceptique** (suite de Taiz *et al.* 2019) |
| `2016-Baluska-Levin-on-having-no-head-cognition-throughout-biological-systems.pdf` | Baluška F., Levin M. (2016). *On Having No Head: Cognition throughout Biological Systems.* **Frontiers in Psychology** 7, 902 | [10.3389/fpsyg.2016.00902](https://doi.org/10.3389/fpsyg.2016.00902) | 1,5 Mo | **Position « cognition basale »** (camp opposé) |
| `2019-Levin-computational-boundary-of-a-self-bioelectricity.pdf` | Levin M. (2019). *The Computational Boundary of a « Self »: Developmental Bioelectricity Drives Multicellularity and Scale-Free Cognition.* **Frontiers in Psychology** 10, 2688 | [10.3389/fpsyg.2019.02688](https://doi.org/10.3389/fpsyg.2019.02688) | 2,3 Mo | Bioélectricité et cognition sans système nerveux |

### 1.6 Sonification

| Fichier | Référence complète | DOI / URL | Taille | Thème |
|---|---|---|---|---|
| `2013-Dubus-Bresin-systematic-review-mapping-strategies-sonification.pdf` | Dubus G., Bresin R. (2013). *A Systematic Review of Mapping Strategies for the Sonification of Physical Quantities.* **PLoS ONE** 8(12), e82491 | [10.1371/journal.pone.0082491](https://doi.org/10.1371/journal.pone.0082491) | 766 Ko | **Référence méthodologique** : stratégies de mapping donnée→son |
| `2024-Enge-integration-of-sonification-and-visualization-state-of-the-art.pdf` | Enge K., Elmquist E., Caiola V., *et al.* (2024). *Open Your Ears and Take a Look: A State-of-the-Art Report on the Integration of Sonification and Visualization.* **Computer Graphics Forum** 43(3) *(version arXiv:2402.16558)* | [10.1111/cgf.15114](https://doi.org/10.1111/cgf.15114) | 4,5 Mo | État de l'art sonification + visualisation |
| `2020-Minciacchi-sonification-perceptualizing-biological-information-editorial.pdf` | Minciacchi D., Rosenboom D., Bravi R., Cohen E. J. (2020). *Editorial: Sonification, Perceptualizing Biological Information.* **Frontiers in Neuroscience** 14, 550 | [10.3389/fnins.2020.00550](https://doi.org/10.3389/fnins.2020.00550) | 163 Ko | Sonification de données biologiques |
| `2009-Wu-scale-free-music-of-the-brain-sonification-eeg.pdf` | Wu D., Li C.-Y., Yao D.-Z. (2009). *Scale-Free Music of the Brain.* **PLoS ONE** 4(6), e5915 | [10.1371/journal.pone.0005915](https://doi.org/10.1371/journal.pone.0005915) | 445 Ko | Sonification EEG — modèle transposable au signal végétal |
| `2020-Buehler-nanomechanical-sonification-ncov-spike-protein-materiomusic.pdf` | Buehler M. J. (2020). *Nanomechanical sonification of the 2019-nCoV coronavirus spike protein through a materiomusical approach.* **arXiv** 2003.14258 | [arXiv:2003.14258](https://arxiv.org/abs/2003.14258) | 1,5 Mo | Sonification de protéines (MIT) |
| `2020-Buehler-liquified-protein-vibrations-classification-de-novo-image-generation.pdf` | Yu C. H., Qin Z., Martin-Martinez F. J., Buehler M. J. (2020). *Liquified protein vibrations, classification and cross-paradigm de novo image generation using deep neural networks.* **arXiv** 2004.07603 | [arXiv:2004.07603](https://arxiv.org/abs/2004.07603) | 2,5 Mo | Sonification + IA (MIT) |

---

## 2. Domaine public — `documents/domaine-public/`

| Fichier | Référence complète | Source | Taille | Thème |
|---|---|---|---|---|
| `1902-Bose-response-in-the-living-and-non-living.pdf` | Bose J. C. (1902). *Response in the Living and Non-Living.* Longmans, Green & Co., London | [archive.org/details/responseinliving00boseuoft](https://archive.org/details/responseinliving00boseuoft) | 21 Mo | Fondateur de l'électrophysiologie végétale |
| `1906-Bose-plant-response-as-a-means-of-physiological-investigation.pdf` | Bose J. C. (1906). *Plant Response as a Means of Physiological Investigation.* Longmans, Green & Co., London | [archive.org/details/plantresponseasm00boseuoft](https://archive.org/details/plantresponseasm00boseuoft) | 50 Mo | Réponses électriques des plantes |
| `1907-Bose-comparative-electro-physiology.pdf` | Bose J. C. (1907). *Comparative Electro-Physiology: A Physico-Physiological Study.* Longmans, Green & Co., London | [archive.org/details/comparativeelect00boseuoft](https://archive.org/details/comparativeelect00boseuoft) | 71 Mo | Électrophysiologie comparée plante/animal |
| `1880-Darwin-the-power-of-movement-in-plants.pdf` | Darwin C., Darwin F. (1880). *The Power of Movement in Plants.* John Murray, London *(fac-similé numérisé)* | [archive.org/details/powerofmovementi00darwiala](https://archive.org/details/powerofmovementi00darwiala) | 35 Mo | Mouvement, sensibilité, « root-brain » |
| `1880-Darwin-power-of-movement-in-plants-gutenberg.txt` | Darwin C., Darwin F. (1880). *The Power of Movement in Plants.* — texte intégral recherchable | [gutenberg.org/ebooks/5605](https://www.gutenberg.org/ebooks/5605) | 1,1 Mo | Version texte (citations / recherche plein texte) |

---

## 3. Presse et pages web archivées — `documents/presse/`

Chaque fichier `.md` porte en tête l'URL source et la date de consultation (2026-09-17).

| Fichier | Référence | URL source | Taille | Thème |
|---|---|---|---|---|
| `2023-03-30-physorg-stressed-plants-emit-airborne-sounds.md` | Phys.org / Cell Press (30 mars 2023), *Stressed plants emit airborne sounds that can be detected from more than a meter away* | https://phys.org/news/2023-03-stressed-emit-airborne-meter.html | 2,4 Ko | Presse — Khait 2023 |
| `2023-03-30-eurekalert-cellpress-stressed-plants-airborne-sounds.md` | EurekAlert! — communiqué Cell Press (30 mars 2023) | https://www.eurekalert.org/news-releases/983739 | 2,0 Ko | Communiqué officiel |
| `2023-03-31-scinews-plants-emit-ultrasonic-sounds-when-stressed.md` | Sci.News (31 mars 2023), *Plants Emit Ultrasonic Sounds When Stressed* | https://www.sci.news/biology/plant-ultrasonic-sounds-11794.html | 2,2 Ko | Presse — détails 40-80 kHz |
| `2019-MIT-News-translating-proteins-into-music-Buehler.md` | Chandler D. L., MIT News (26 juin 2019), *Translating Proteins Into Music, and Back* | https://news.mit.edu/2019/translating-proteins-music-0626 | 2,4 Ko | Sonification — Buehler / MIT |
| `2026-plantwave-how-it-works-sonification-biodata.md` | PlantWave, *How it works* (page projet, consultée 2026-09-17) | https://www.plantwave.com/pages/how-it-works | 1,9 Ko | Dispositif commercial : électrodes, conductance, MIDI |
| `wikipedia-en-plant-bioacoustics.md` | Wikipedia EN, *Plant bioacoustics* (CC BY-SA) | https://en.wikipedia.org/wiki/Plant_bioacoustics | 6,6 Ko | Synthèse bioacoustique |
| `wikipedia-en-plant-communication.md` | Wikipedia EN, *Plant communication* (CC BY-SA) | https://en.wikipedia.org/wiki/Plant_communication | 19 Ko | Synthèse + bibliographie |
| `wikipedia-en-plant-perception-physiology.md` | Wikipedia EN, *Plant perception (physiology)* (CC BY-SA) | https://en.wikipedia.org/wiki/Plant_perception_(physiology) | 9,3 Ko | Perception, sens des plantes |
| `wikipedia-en-plant-neurobiology.md` | Wikipedia EN, *Plant neurobiology* (CC BY-SA) | https://en.wikipedia.org/wiki/Plant_neurobiology | 24 Ko | Débat Brenner / Alpi / Taiz résumé |
| `wikipedia-en-mycorrhizal-network.md` | Wikipedia EN, *Mycorrhizal network* (CC BY-SA) | https://en.wikipedia.org/wiki/Mycorrhizal_network | 33 Ko | Wood-wide web + controverse Karst 2023 |
| `wikipedia-en-sonification.md` | Wikipedia EN, *Sonification* (CC BY-SA) | https://en.wikipedia.org/wiki/Sonification | 12 Ko | Techniques, ICAD, historique |
| `wikipedia-fr-communication-vegetale.md` | Wikipédia FR, *Communication végétale* (CC BY-SA) | https://fr.wikipedia.org/wiki/Communication_végétale | 9,9 Ko | Synthèse francophone |

---

## 4. Code open source — `code/`

Archives ZIP des dépôts (branche par défaut), téléchargées via `codeload.github.com`.

| Fichier | Dépôt | URL | Taille | Thème |
|---|---|---|---|---|
| `electricityforprogress_MIDIsprout.zip` | MIDI Sprout — sonification de biodonnées (référence historique du domaine) | https://github.com/electricityforprogress/MIDIsprout | 2,5 Mo | Firmware Arduino, mesure de conductance → MIDI |
| `electricityforprogress_BiodataSonificationBreadboardKit.zip` | Kit breadboard de sonification de biodonnées | https://github.com/electricityforprogress/BiodataSonificationBreadboardKit | 21 Mo | Schémas + guide de montage |
| `electricityforprogress_BiodataFeather.zip` | Portage Adafruit Feather du capteur biodata | https://github.com/electricityforprogress/BiodataFeather | 1,9 Mo | Variante matérielle |
| `electricityforprogress_Organon.zip` | Organon — instrument biodata | https://github.com/electricityforprogress/Organon | 2,3 Mo | Synthèse / instrument |
| `Lessnullvoid_Pulsum-Plantae.zip` | Pulsum Plantae — lectures bioélectriques de plantes (projet artistique) | https://github.com/Lessnullvoid/Pulsum-Plantae | 4,6 Mo | Capteurs + traitement + art sonore |
| `leetronics_midi-biodata.zip` | midi-biodata | https://github.com/leetronics/midi-biodata | 5,8 Mo | Biodata → MIDI |
| `Playtronica_biotron-firmware.zip` | Biotron (Playtronica) — firmware | https://github.com/Playtronica/biotron-firmware | 64 Ko | Firmware d'un instrument végétal commercial |
| `ettorhake_BioDataToMidiToDigitakt.zip` | BioDataToMidiToDigitakt (documentation en français) | https://github.com/ettorhake/BioDataToMidiToDigitakt | 23 Ko | Chaîne biodata → MIDI → sampler |
| `RominaSR_SonicPlants.zip` | SonicPlants — visualisation et sonification temps réel | https://github.com/RominaSR/SonicPlants | 3,7 Ko | Arduino / Raspberry Pi |
| `klaemsch_plant-sonification.zip` | plant-sonification (Pico 2 / CircuitPython) | https://github.com/klaemsch/plant-sonification | 8,7 Ko | Montage minimal moderne |
| `ChubbyLobsters_Electrophysiology-and-Biorobotics.zip` | Computational Electrophysiology in Plants: A Low-Cost Arduino Approach | https://github.com/ChubbyLobsters/Electrophysiology-and-Biorobotics | 4,9 Ko | Électrophysiologie low-cost |
| `OPEnSLab-OSU_SapFlowMeterOld.zip` | Sap Flow Meter (OPEnS Lab, Oregon State University) | https://github.com/OPEnSLab-OSU/SapFlowMeterOld | 16 Mo | Capteur de flux de sève (open hardware) |
| `james-trayford_strauss.zip` | STRAUSS — *Sonification Tools & Resources for Analysis Using Sound Synthesis* | https://github.com/james-trayford/strauss | 53 Mo | Bibliothèque Python de sonification scientifique |
| `spacetelescope_astronify.zip` | Astronify (STScI) — sonification de séries temporelles | https://github.com/spacetelescope/astronify | 3,0 Mo | Sonification de séries temporelles (méthode réutilisable) |
| `lockepatton_sonipy.zip` | sonipy — sonification de nuages de points | https://github.com/lockepatton/sonipy | 6,5 Mo | Mapping données → hauteur/temps |

---

## 5. Datasheets composants — `datasheets/`

| Fichier | Composant / référence | Source officielle | Taille |
|---|---|---|---|
| `INA333-TexasInstruments-instrumentation-amplifier.pdf` | Texas Instruments INA333 — amplificateur d'instrumentation micro-puissance, zéro-dérive | https://www.ti.com/lit/ds/symlink/ina333.pdf | 1,5 Mo |
| `AD8232-AnalogDevices-ECG-AFE.pdf` | Analog Devices AD8232 — front-end analogique ECG monodérivation | Analog Devices (miroir SparkFun, `www.analog.com` inaccessible depuis ce réseau) | 661 Ko |
| `ADS1115-TexasInstruments-16bit-ADC-I2C.pdf` | Texas Instruments ADS1115 — CAN 16 bits, I²C, PGA | https://www.ti.com/lit/ds/symlink/ads1115.pdf | 2,7 Mo |
| `ADS1256-TexasInstruments-24bit-ADC.pdf` | Texas Instruments ADS1256 — CAN 24 bits, 30 kSPS, 8 voies | https://www.ti.com/lit/ds/symlink/ads1256.pdf | 811 Ko |
| `DS18B20-Maxim-1wire-digital-thermometer.pdf` | Maxim / Analog Devices DS18B20 — thermomètre numérique 1-Wire | Maxim Integrated (miroir SparkFun) | 399 Ko |
| `BME280-BoschSensortec-humidity-pressure-temperature.pdf` | Bosch Sensortec BME280 — humidité / pression / température | https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf | 1,7 Mo |
| `SHT31-Sensirion-humidity-temperature.pdf` | Sensirion SHT3x-DIS (SHT31) — humidité / température | https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf | 810 Ko |
| `BH1750FVI-ROHM-ambient-light-sensor.pdf` | ROHM BH1750FVI — capteur de lumière ambiante numérique I²C | ROHM (miroir ; `fscdn.rohm.com` renvoie une page de redirection) | 396 Ko |
| `SCD41-Sensirion-CO2-sensor.pdf` | Sensirion SCD4x (SCD41) — capteur CO₂ photoacoustique | https://sensirion.com/resource/datasheet/scd4x | 1,3 Mo |

---

## 6. Références non téléchargeables (paywall / non-OA)

Ces travaux sont cités dans la mission mais **ne sont pas librement accessibles**. Référence complète et DOI donnés pour consultation en bibliothèque ou via un accès institutionnel.

### Bioacoustique
| Référence | DOI |
|---|---|
| Gagliano M., Mancuso S., Robert D. (2012). *Towards understanding plant bioacoustics.* **Trends in Plant Science** 17(6), 323-325 | [10.1016/j.tplants.2012.03.002](https://doi.org/10.1016/j.tplants.2012.03.002) |
| Gagliano M. (2013). *The flowering of plant bioacoustics: how and why.* **Behavioral Ecology** 24(4), 800-801 *(bronze OA mais PDF OUP bloqué aux robots)* | [10.1093/beheco/art021](https://doi.org/10.1093/beheco/art021) |
| Gagliano M., Mancuso S., Robert D. (2012). *Acoustic and magnetic communication in plants.* **Plant Signaling & Behavior** 7(10), 1346-1348 *(PDF Taylor & Francis bloqué)* | [10.4161/psb.21517](https://doi.org/10.4161/psb.21517) |
| Mishra R. C., Ghosh R., Bae H. (2016). *Plant acoustics: in the search of a sound mechanism for sound signaling in plants.* **Journal of Experimental Botany** 67(15), 4483-4494 | [10.1093/jxb/erw235](https://doi.org/10.1093/jxb/erw235) |
| Ponomarenko A., Vincent O., Pietriga A., *et al.* (2014). *Ultrasonic emissions reveal individual cavitation bubbles in water-stressed wood.* **J. R. Soc. Interface** 11(99), 20140480 | [10.1098/rsif.2014.0480](https://doi.org/10.1098/rsif.2014.0480) |
| Vergeynst L. L., Sause M. G. R., Steppe K. (2015). *Clustering reveals cavitation-related acoustic emission signals from dehydrating branches.* **Tree Physiology** 36(5), 786-796 | [10.1093/treephys/tpv125](https://doi.org/10.1093/treephys/tpv125) |

### Électrophysiologie
| Référence | DOI |
|---|---|
| Toyota M., Spencer D., Sawai-Toyota S., *et al.* (2018). *Glutamate triggers long-distance, calcium-based plant defense signaling.* **Science** 361(6407), 1112-1115 | [10.1126/science.aat7744](https://doi.org/10.1126/science.aat7744) |
| Fromm J., Lautner S. (2007). *Electrical signals and their physiological significance in plants.* **Plant, Cell & Environment** 30(3), 249-257 *(bronze OA, PDF Wiley bloqué)* | [10.1111/j.1365-3040.2006.01614.x](https://doi.org/10.1111/j.1365-3040.2006.01614.x) |
| Volkov A. G., Foster J. C., Ashby T. A., *et al.* (2010). *Mimosa pudica: electrical and mechanical stimulation of plant movements.* **Plant, Cell & Environment** 33(2), 163-173 | [10.1111/j.1365-3040.2009.02066.x](https://doi.org/10.1111/j.1365-3040.2009.02066.x) |
| Volkov A. G., Ranatunga D. R. A. (2006). *Plants as Environmental Biosensors.* **Plant Signaling & Behavior** 1(3), 105-115 *(PDF T&F bloqué)* | [10.4161/psb.1.3.3000](https://doi.org/10.4161/psb.1.3.3000) |
| Hedrich R., Salvador-Recatalà V., Dreyer I. (2016). *Electrical Wiring and Long-Distance Plant Communication.* **Trends in Plant Science** 21(5), 376-387 | [10.1016/j.tplants.2016.01.016](https://doi.org/10.1016/j.tplants.2016.01.016) |
| Sukhov V., Sukhova E., Vodeneev V. (2019). *Long-distance electrical signals as a link between the local action of stressors and the systemic physiological responses in higher plants.* **Progress in Biophysics and Molecular Biology** 146, 63-84 | [10.1016/j.pbiomolbio.2018.11.009](https://doi.org/10.1016/j.pbiomolbio.2018.11.009) |
| Choi W.-G., Hilleary R., Swanson S. J., Kim S.-H., Gilroy S. (2016). *Rapid, Long-Distance Electrical and Calcium Signaling in Plants.* **Annual Review of Plant Biology** 67, 287-307 | [10.1146/annurev-arplant-043015-112130](https://doi.org/10.1146/annurev-arplant-043015-112130) |
| Ehosioke S., Nguyen F., Rao S., *et al.* (2020). *Sensing the electrical properties of roots: A review.* **Vadose Zone Journal** 19(1), e20082 *(gold OA, mais PDF Wiley et HAL inaccessibles depuis ce réseau)* | [10.1002/vzj2.20082](https://doi.org/10.1002/vzj2.20082) |

### Réseaux mycorhiziens
| Référence | DOI |
|---|---|
| **Karst J., Jones M. D., Hoeksema J. D. (2023).** *Positive citation bias and overinterpreted results lead to misinformation on common mycorrhizal networks in forests.* **Nature Ecology & Evolution** 7, 501-511 — *critique majeure du « wood-wide web »* | [10.1038/s41559-023-01986-1](https://doi.org/10.1038/s41559-023-01986-1) |
| Simard S. W., Perry D. A., Jones M. D., *et al.* (1997). *Net transfer of carbon between ectomycorrhizal tree species in the field.* **Nature** 388, 579-582 | [10.1038/41557](https://doi.org/10.1038/41557) |

### Débat cognition / conscience végétale
| Référence | DOI |
|---|---|
| Brenner E. D., Stahlberg R., Mancuso S., *et al.* (2006). *Plant neurobiology: an integrated view of plant signaling.* **Trends in Plant Science** 11(8), 413-419 | [10.1016/j.tplants.2006.06.009](https://doi.org/10.1016/j.tplants.2006.06.009) |
| Alpi A., Amrhein N., Bertl A., *et al.* (2007). *Plant neurobiology: no brain, no gain?* **Trends in Plant Science** 12(4), 135-136 | [10.1016/j.tplants.2007.03.002](https://doi.org/10.1016/j.tplants.2007.03.002) |
| Taiz L., Alkon D., Draguhn A., *et al.* (2019). *Plants Neither Possess nor Require Consciousness.* **Trends in Plant Science** 24(8), 677-687 | [10.1016/j.tplants.2019.05.008](https://doi.org/10.1016/j.tplants.2019.05.008) |
| Calvo P., Gagliano M., Souza G. M., Trewavas A. (2020). *Plants are intelligent, here's how.* **Annals of Botany** 125(1), 11-28 *(bronze OA, PDF OUP bloqué)* | [10.1093/aob/mcz155](https://doi.org/10.1093/aob/mcz155) |
| Segundo-Ortin M., Calvo P. (2022). *Consciousness and cognition in plants.* **WIREs Cognitive Science** 13(2), e1578 | [10.1002/wcs.1578](https://doi.org/10.1002/wcs.1578) |
| Lyon P. (2021). *Reframing cognition: getting down to biological basics.* **Phil. Trans. R. Soc. B** 376(1820), 20190750 *(hybride OA, PDF Royal Society bloqué)* | [10.1098/rstb.2019.0750](https://doi.org/10.1098/rstb.2019.0750) |

### Sonification
| Référence | DOI |
|---|---|
| Yu C. H., Qin Z., Martin-Martinez F. J., Buehler M. J. (2019). *A Self-Consistent Sonification Method to Translate Amino Acid Sequences into Musical Compositions and Application in Protein Design Using Artificial Intelligence.* **ACS Nano** 13(7), 7471-7482 — *(les deux préimpressions arXiv de Buehler archivées en § 1.6 couvrent la même méthode)* | [10.1021/acsnano.9b02180](https://doi.org/10.1021/acsnano.9b02180) |

### Ouvrages non libres de droits
| Référence | Note |
|---|---|
| Karban R. (2015). *Plant Sensing and Communication.* University of Chicago Press | Monographie sous droits — non téléchargeable |
| Bose J. C. (1926). *The Nervous Mechanism of Plants.* Longmans, Green & Co. | Présent sur Internet Archive (item Wellcome `b29818722`) mais le fichier PDF n'est pas servi en téléchargement direct ; consultable en ligne : https://archive.org/details/b29818722 |

---

## 7. Cibles recherchées mais non trouvées

| Cible | Résultat |
|---|---|
| **« Talking Tree » belge (2010, Happiness Brussels)** | Le site du projet, `talking-tree.com`, existe dans la Wayback Machine (snapshot 2010 : http://web.archive.org/web/20100901000000/http://www.talking-tree.com/) mais était **entièrement en Flash** — aucun texte exploitable n'a pu être archivé. Le domaine `talkingtree.be` correspond à une agence d'écriture néerlandophone sans rapport. |
| **« Talking Tree » de Dublin** | Aucune source fiable identifiée. Le budget de recherche web de la session (200 requêtes) a été épuisé et les moteurs alternatifs (DuckDuckGo, Mojeek) renvoient des CAPTCHA ou des 403 — à reprendre manuellement. |
| Actes ICAD en accès libre | Zenodo renvoie 403 aux clients non-navigateurs depuis ce réseau ; les articles de sonification retenus (§ 1.6) couvrent le même terrain méthodologique. |

---

## 8. Notes techniques d'archivage

- **Éditeurs inaccessibles depuis ce réseau** (HTTP 403 / blocage anti-robot systématique) : Oxford University Press (`academic.oup.com`), Wiley (`onlinelibrary.wiley.com`), Taylor & Francis, Springer (`link.springer.com`), Annual Reviews, PNAS, Royal Society (`royalsocietypublishing.org` — seul `rsif` a répondu), Zenodo, PubMed Central (`pmc.ncbi.nlm.nih.gov`), `analog.com`, `www.mdpi.com`.
- **Contournements légitimes utilisés** : `res.mdpi.com` (CDN officiel MDPI), API REST Europe PMC (`fullTextXML`, licence ouverte) convertie en Markdown, miroirs officiels de datasheets (SparkFun héberge les PDF constructeur d'origine), préimpressions bioRxiv/arXiv déposées par les auteurs.
- **Vérification** : chaque PDF a été contrôlé (signature `%PDF`, taille > 20 Ko) ; les pages HTML d'erreur et de paywall téléchargées par erreur ont été supprimées.
- **Résolution des accès ouverts** : APIs OpenAlex + Europe PMC (aucune clé ni adresse e-mail transmise).
