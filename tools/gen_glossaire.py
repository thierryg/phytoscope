#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/gen_glossaire.py
#
#  Version  : 1.5.1
#  Date     : 2026-09-18
#  Éditeur  : Bretagne Namasté
#  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Site     : https://bretagne-namaste.com
#  Contact  : contact@bretagne-namaste.com
#  Licence  : MIT — voir LICENCE.txt
#
#  SPDX-License-Identifier: MIT
#  fin de l'attribution
#  ==========================================================================

"""
Génère l'annexe « Glossaire raisonné » des trois volumes.

Une base unique, partagée : chaque terme porte les volumes où il est pertinent.
Ainsi le vocabulaire reste cohérent d'un ouvrage à l'autre, et un terme corrigé
l'est partout.

Usage : python3 tools/gen_glossaire.py
"""
import os
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "pdf-src", "la-musique-des-plantes")
DIRS = {"v1": "v1-dublin", "v2": "v2-biocommunication", "v3": "v3-atelier"}

# (terme, catégorie, définition, contexte, écueil, volumes)
A = "123"          # présent dans les trois volumes
G = [
# ---------------------------------------------------------------- épistémologie
("Ablation (test d')", "méthode",
 "Procédure consistant à retirer un composant d'un système pour mesurer sa contribution réelle aux performances.",
 "Appliquée à un dispositif de plante parlante : remplacer le signal du capteur par un tirage aléatoire de même distribution, puis faire écouter les deux à l'aveugle.",
 "Un taux de reconnaissance proche de 50 % signifie que le signal n'apportait rien.", A),
("Anthropomorphisme", "épistémologie",
 "Attribution de caractères humains — intentions, émotions, langage — à un être non humain ou à un objet.",
 "Ce n'est pas une erreur de raisonnement mais un mode de perception par défaut, documenté depuis Weizenbaum (1966).",
 "Le combattre entièrement est vain ; l'utile est de savoir quand il opère.", A),
("Attribution", "épistémologie",
 "Opération mentale par laquelle on assigne une origine, une intention ou une auteurité à un énoncé.",
 "Le cœur du problème traité par cette série : l'attribution est déclenchée par la forme grammaticale — la première personne —, indépendamment du mécanisme réel.",
 None, A),
("Biais de citation", "épistémologie",
 "Tendance à citer préférentiellement les travaux qui confirment une hypothèse populaire, au détriment des résultats nuls ou contraires.",
 "Quantifié pour les réseaux mycorhiziens par Karst, Jones &amp; Hoeksema (2023) : les affirmations non étayées ont doublé en vingt-cinq ans.",
 None, A),
("Biais de confirmation", "épistémologie",
 "Tendance à rechercher, retenir et interpréter l'information dans le sens de ses attentes préalables.",
 "En observation de terrain, il opère surtout par <em>sélection</em> : on retient la séance où « ça a marché ».",
 "Le remède n'est pas la vigilance mais le pré-enregistrement du protocole.", A),
("Double aveugle", "méthode",
 "Protocole dans lequel ni le sujet ni l'expérimentateur ne connaissent la condition appliquée.",
 "Dans nos protocoles, une forme allégée suffit : faire juger les enregistrements par une personne ignorant leur provenance.",
 None, A),
("Falsifiabilité", "épistémologie",
 "Propriété d'un énoncé qui spécifie à l'avance ce qui le réfuterait.",
 "Critère de démarcation appliqué dans cette série : un système qui ne dit pas dans quelles conditions il produirait du non-sens n'est pas évaluable.",
 None, A),
("Pré-enregistrement", "méthode",
 "Consignation écrite et datée du protocole avant la collecte des données.",
 "Interdit la sélection rétrospective du passage qui « parle » — mécanisme le plus puissant de l'auto-illusion.",
 None, A),
("Réplication", "méthode",
 "Reproduction indépendante d'une expérience, avec le même protocole, pour vérifier la robustesse d'un résultat.",
 "Le triptyque Markel / Gagliano / Markel dans <em>eLife</em> (2020) est le cas d'école du domaine.",
 None, A),
("Sélection rétrospective", "épistémologie",
 "Choix, après coup, du segment de données qui confirme l'hypothèse.",
 "Sur trois heures d'un signal bruité, il existe toujours deux minutes qui semblent répondre à ce qui s'est passé dans la pièce.",
 "Ce n'est pas une coïncidence remarquable : c'est une propriété ordinaire des séries longues.", A),
("Témoin", "méthode",
 "Condition de référence enregistrée sans intervention, à laquelle toutes les observations ultérieures sont comparées.",
 "Le contrôle « pot de terre sans plante » de Khait et al. (2023) — zéro son sur plus de 500 heures — est le modèle du genre.",
 None, A),
# ---------------------------------------------------------------- sciences cognitives
("CASA (paradigme)", "sciences cognitives",
 "<em>Computers Are Social Actors</em> : les humains appliquent aux machines des règles sociales sans y penser.",
 "Établi par Reeves &amp; Nass (1996) et Nass &amp; Moon (2000).",
 "L'effet persiste chez des sujets qui affirment par ailleurs, sincèrement, que les machines n'ont ni intentions ni émotions.", A),
("Communication facilitée", "psychologie",
 "Méthode où un « facilitateur » soutient la main d'une personne non verbale désignant des lettres sur un clavier.",
 "Wegner, Fuller &amp; Sparrow (2003) ont montré par test croisé que le message provient du facilitateur, par effet idéomoteur, et que celui-ci attribue sincèrement l'auteurité à l'autre.",
 "Structure identique à celle d'un dispositif de plante parlante : le précédent le plus éclairant du domaine.", A),
("Effet ELIZA", "sciences cognitives",
 "Tendance à attribuer compréhension et intention à un programme informatique dont on connaît pourtant le mécanisme.",
 "Nommé d'après le programme de Joseph Weizenbaum (1966), qui simulait un psychothérapeute par simple substitution de motifs.",
 "La connaissance du mécanisme ne protège pas de l'effet : expliquer ne suffit pas, il faut tester.", A),
("Idéomoteur (effet)", "psychologie",
 "Production de micro-mouvements involontaires, sous le seuil de la conscience, dirigés par une attente.",
 "Mécanisme explicatif de la communication facilitée, de la planche Ouija et du pendule de radiesthésie.",
 None, A),
# ---------------------------------------------------------------- biologie végétale
("Acropète", "biologie végétale",
 "Se dit d'une propagation qui va de la base vers le sommet de la plante.",
 "Les potentiels de variation présentent une asymétrie directionnelle : la propagation acropète est plus rapide que la basipète.",
 None, "12"),
("Allélopathie", "biologie végétale",
 "Influence biochimique d'une plante sur une autre, par libération de composés dans le milieu.",
 "Voie d'interaction distincte des composés volatils aériens : elle passe par le sol et les exsudats racinaires.",
 None, "2"),
("Apoplaste", "biologie végétale",
 "Ensemble des espaces extracellulaires d'un tissu végétal : parois, lacunes, vaisseaux.",
 "C'est en grande partie par l'apoplaste que circule le courant lors d'une mesure d'impédance sur feuille.",
 None, A),
("Aubier", "biologie végétale",
 "Partie externe et vivante du bois, assurant la conduction de la sève brute.",
 "C'est la seule zone où une mesure de flux de sève a un sens ; le duramen central est inerte.",
 None, "13"),
("Basipète", "biologie végétale",
 "Se dit d'une propagation qui va du sommet vers la base de la plante.",
 None, None, "12"),
("Bioacoustique végétale", "biologie végétale",
 "Étude des sons émis et perçus par les plantes.",
 "L'émission de sons sous stress est démontrée (Khait et al., <em>Cell</em>, 2023) ; le mécanisme — cavitation xylémique — est compris depuis 1966.",
 "Émission ≠ communication. Aucune preuve ne soutient une communication acoustique de plante à plante.", A),
("Cambium", "biologie végétale",
 "Assise de cellules en division située juste sous l'écorce, responsable de la croissance en diamètre.",
 "Toute perforation du cambium ouvre une porte aux pathogènes : c'est pourquoi visser ou clouer dans un tronc est proscrit.",
 None, A),
("Cavitation", "biophysique",
 "Rupture de la colonne d'eau dans un vaisseau du xylème, sous l'effet d'une tension trop forte.",
 "Le vaisseau se vide — embolie — et la détente élastique produit un clic ultrasonore de 20 à 100 kHz.",
 "Toutes les émissions acoustiques d'un arbre ne sont pas de la cavitation : le bois qui se retire, l'écorce qui sèche et le vent en produisent aussi.", A),
("Composés organiques volatils", "biologie végétale",
 "Molécules émises dans l'air par les tissus végétaux, notamment après blessure : terpènes, aldéhydes en C6, salicylate de méthyle.",
 "Seule voie d'interaction végétale à distance dont le canal soit clairement identifié et le mécanisme documenté.",
 "Rien ne prouve que l'émettrice ait un intérêt à prévenir : la voisine capte peut-être un signal qui ne lui était pas destiné.", "12"),
("Duramen", "biologie végétale",
 "Bois de cœur, imprégné de substances de réserve, mécaniquement résistant mais physiologiquement inerte.",
 None, "Une sonde de flux de sève placée dans le duramen ne mesure rien.", "13"),
("Électrome", "biologie végétale",
 "Ensemble des oscillations électriques d'un organisme considérées comme un système dynamique plutôt que comme du bruit.",
 "Terme forgé par analogie avec génome et protéome ; l'analyse spectrale et fractale de l'électrome permet de classer l'état physiologique d'une plante.",
 "Les mesures d'électrome sont solides ; leur interprétation en termes d'« attention » ou de « cognition » ne fait pas consensus.", A),
("Électrophysiologie végétale", "biologie végétale",
 "Étude des phénomènes électriques des tissus végétaux : potentiels de membrane, potentiels d'action, potentiels de variation.",
 "Discipline centenaire, fondée par Burdon-Sanderson (1873) et Bose (1902).",
 "Ne pas confondre avec la mesure d'impédance des appareils grand public, qui relève d'une physique différente.", A),
("Embolie", "biophysique",
 "État d'un vaisseau conducteur rempli de gaz à la suite d'une cavitation, et devenu non fonctionnel.",
 None, None, A),
("GLR (récepteurs)", "biologie végétale",
 "Canaux ioniques de la famille <em>glutamate receptor-like</em>, apparentés aux récepteurs au glutamate animaux.",
 "GLR3.3 et GLR3.6 sont nécessaires à la propagation du signal de blessure de feuille à feuille (Toyota et al., <em>Science</em>, 2018).",
 "Les potentiels d'action phloémiens sont initiés et propagés <em>indépendamment</em> de ces récepteurs : deux systèmes, pas un.", "12"),
("Jasmonate", "biologie végétale",
 "Famille d'hormones végétales déclenchant les réponses de défense après blessure.",
 "L'accumulation de jasmonoyl-isoleucine à distance de la blessure est le marqueur biochimique de la signalisation systémique.",
 None, "2"),
("Mycorhize", "biologie",
 "Association symbiotique entre les racines d'une plante et un champignon.",
 "Quasi universelle chez les arbres. Le transfert de carbone entre arbres via des réseaux ectomycorhiziens est documenté (Klein et al., 2016).",
 "L'hypothèse de l'« arbre-mère » nourrissant préférentiellement sa descendance n'a aucune preuve publiée et évaluée par les pairs.", A),
("Phloème", "biologie végétale",
 "Tissu conducteur transportant les produits de la photosynthèse.",
 "Décrit comme un « câble vert » : c'est la voie de propagation des potentiels d'action végétaux.",
 None, A),
("Plasmodesme", "biologie végétale",
 "Canal traversant la paroi entre deux cellules végétales voisines, assurant leur continuité cytoplasmique.",
 "Voie de propagation de cellule à cellule des signaux électriques.",
 None, "12"),
("Potentiel d'action (végétal)", "biologie végétale",
 "Dépolarisation transitoire stéréotypée, obéissant à la loi du tout ou rien, avec seuil et période réfractaire.",
 "Vitesse de 1 à 10 cm/s. Mécanisme : efflux de Cl⁻ puis de K⁺, avec désactivation de la pompe à protons.",
 "Code un événement, non une intensité : c'est ce qui le distingue du potentiel de variation.", A),
("Potentiel de variation", "biologie végétale",
 "Dépolarisation de forme irrégulière, graduée selon le stimulus, d'une durée pouvant atteindre des dizaines de minutes.",
 "N'est pas auto-propagée : c'est une réponse locale à une onde hydraulique ou à un agent chimique.",
 "Traverse les zones de tissu nécrosé — ce qu'un signal électrique auto-propagé ne ferait pas.", A),
("Potentiel hydrique", "biophysique",
 "Énergie potentielle de l'eau dans un système, exprimée en mégapascals ; négative dans une plante en transpiration.",
 "Dans le xylème d'un arbre, il descend couramment de −0,5 à −3 MPa : l'eau y est sous tension.",
 None, "123"),
("Potentiel systémique", "biologie végétale",
 "Variation systémique du potentiel de membrane vers l'hyperpolarisation, mécanisme présumé : activation de la pompe à protons.",
 "La moins étudiée des trois classes de signaux électriques longue distance.",
 None, "2"),
("Stomate", "biologie végétale",
 "Pore de l'épiderme foliaire, bordé de deux cellules de garde, régulant les échanges gazeux et la transpiration.",
 "Son ouverture module la teneur en eau du tissu, donc l'impédance mesurée en surface.",
 None, A),
("Transpiration", "biologie végétale",
 "Évaporation de l'eau par les stomates, moteur de la montée de sève.",
 "Un arbre mature peut transpirer plusieurs centaines de litres par jour en été.",
 None, "123"),
("Turgescence", "biologie végétale",
 "État de tension d'une cellule végétale gorgée d'eau, pressant sur sa paroi.",
 "Sa perte se traduit par le flétrissement — et, à l'échelle du tronc, par une contraction mesurable au dendromètre.",
 None, "13"),
("Xylème", "biologie végétale",
 "Tissu conducteur assurant la montée de l'eau et des sels minéraux depuis les racines.",
 "L'eau y circule sous tension — en pression négative — ce qui rend possible la cavitation.",
 None, A),
# ---------------------------------------------------------------- instrumentation
("Agrégation", "instrumentation",
 "Réduction d'un ensemble de mesures à une valeur unique — moyenne, médiane, extrêmes — sur une fenêtre de temps.",
 "Indispensable pour transmettre par radio longue portée, où le débit se compte en dizaines d'octets par message.",
 "Après agrégation, le modèle de langage ne voit jamais le signal, mais un résumé de résumé.", A),
("Amplificateur d'instrumentation", "électronique",
 "Amplificateur différentiel à très haute impédance d'entrée et fort taux de réjection du mode commun.",
 "Indispensable en électrophysiologie végétale, où l'impédance de source atteint plusieurs mégaohms.",
 "Un amplificateur ordinaire charge la source et modifie ce qu'il prétend mesurer.", A),
("Anti-repliement (filtre)", "instrumentation",
 "Filtre passe-bas analogique placé <strong>avant</strong> le convertisseur analogique-numérique.",
 "Il supprime les composantes de fréquence supérieure à la moitié de la fréquence d'échantillonnage.",
 "Un filtrage numérique après conversion ne corrige pas le repliement : l'information est déjà perdue et mélangée.", A),
("Artefact", "instrumentation",
 "Variation enregistrée qui ne provient pas du phénomène étudié mais de la chaîne de mesure ou de l'environnement.",
 "Sept artefacts dominent en extérieur : dérive d'électrode, potentiel d'écoulement, blessure d'insertion, dérive thermique, humidité de surface, mouvement, couplage secteur.",
 "Un artefact rythmé est indiscernable d'un rythme biologique sans voies de contexte.", A),
("Capacitif (capteur)", "instrumentation",
 "Capteur mesurant une grandeur par variation de capacité électrique, sans contact galvanique avec le milieu.",
 "Pour l'humidité du sol, c'est la seule technologie recommandable : les sondes résistives se corrodent en quelques semaines.",
 None, "13"),
("Convertisseur analogique-numérique", "électronique",
 "Circuit transformant une tension continue en valeur numérique, caractérisé par sa résolution et sa fréquence d'échantillonnage.",
 "En électrophysiologie végétale, 16 bits constituent un minimum, 24 bits un confort.",
 None, "13"),
("Couplage capacitif", "électronique",
 "Transfert d'énergie entre deux conducteurs séparés par un isolant, sans contact direct.",
 "Explique qu'un montage haute impédance « réagisse » à l'approche d'une personne : le corps humain est un conducteur couplé au réseau à 50 Hz.",
 None, A),
("Dendromètre", "instrumentation",
 "Capteur mesurant les variations de circonférence ou de diamètre d'un tronc, au micromètre près.",
 "Révèle le cycle journalier de contraction diurne et de regonflement nocturne.",
 "Ne figure dans aucune source décrivant le dispositif de 2025, contrairement à ce qui est souvent affirmé.", A),
("Dérive", "instrumentation",
 "Évolution lente et systématique d'une mesure, sans rapport avec la grandeur mesurée.",
 "Sur une électrode métallique nue, la dérive des premières heures dépasse couramment la totalité du signal utile.",
 "Conséquence : seules les variations rapides sont exploitables, jamais le niveau absolu.", A),
("Descripteur", "traitement du signal",
 "Grandeur calculée résumant une propriété d'un signal : valeur courante, pente, variance, énergie spectrale.",
 "Bloc escamoté par la plupart des dispositifs commerciaux — et pourtant seul moyen de savoir à quoi le système a réagi.",
 None, A),
("Électrode impolarisable", "électronique",
 "Électrode dont l'interface avec le milieu ne développe pas de tension parasite significative.",
 "Types courants : argent/chlorure d'argent (Ag/AgCl), plomb/chlorure de plomb (Pb/PbCl₂).",
 "Une électrode métallique nue se polarise et dérive : c'est l'erreur de montage la plus répandue.", A),
("Flux de sève", "instrumentation",
 "Débit d'eau circulant dans l'aubier, mesuré le plus souvent par dissipation thermique.",
 "Méthode de Granier : deux sondes, l'une chauffée, l'autre de référence ; c'est l'écart de température qui porte l'information.",
 "La sonde de référence est indispensable : sans elle, la dérive thermique ambiante est prise pour du flux.", "13"),
("Impédance", "électronique",
 "Opposition d'un circuit au passage d'un courant alternatif, généralisant la résistance.",
 "Ce que mesurent réellement la plupart des appareils de « musique des plantes » — largement déterminée par la teneur en eau du tissu et par l'état du contact.",
 None, A),
("Mode commun", "électronique",
 "Composante identique présente sur les deux entrées d'un amplificateur différentiel.",
 "Le parasite à 50 Hz est typiquement en mode commun : une mesure différentielle bien conçue l'élimine en grande partie.",
 None, "13"),
("PAR", "instrumentation",
 "<em>Photosynthetically Active Radiation</em> : flux de photons utilisables par la photosynthèse, entre 400 et 700 nm, en µmol·m⁻²·s⁻¹.",
 "Grandeur pertinente pour une plante, contrairement au lux qui est pondéré par la sensibilité de l'œil humain.",
 "Convertir des lux en PAR par un facteur fixe est faux : le rapport dépend du spectre de la source.", "13"),
("Repliement de spectre", "traitement du signal",
 "Apparition de fausses fréquences basses lorsqu'un signal est échantillonné trop lentement.",
 "Un parasite rapide mal filtré produit, après échantillonnage, une oscillation lente parfaitement crédible.",
 "Beaucoup de « rythmes » découverts dans des séries végétales sont des artefacts de repliement.", A),
("Voies parallèles (règle des)", "méthode",
 "Principe selon lequel toute voie bioélectrique doit être accompagnée d'au moins quatre voies de contexte : température, humidité, vent, état hydrique.",
 "Sans elles, aucune distinction n'est possible entre variation physiologique et dérive thermo-hygrométrique.",
 "Un dispositif qui ne mesure que le bioélectrique ne peut pas savoir ce qu'il mesure.", A),
("Wheatstone (pont de)", "électronique",
 "Montage en quatre branches permettant de mesurer finement une résistance inconnue par équilibrage.",
 "Base historique des dispositifs de bio-sonification végétale, dont ceux de Damanhur.",
 None, "13"),
# ---------------------------------------------------------------- informatique & IA
("Hallucination", "intelligence artificielle",
 "Production, par un modèle génératif, d'un contenu plausible mais sans fondement dans ses entrées.",
 "Ce n'est pas un dysfonctionnement mais le régime normal d'un modèle dont la fonction est de maximiser la plausibilité.",
 "Un modèle branché sur un capteur produira de belles phrases même sur du bruit blanc : c'est le premier test à faire.", A),
("Inférence", "intelligence artificielle",
 "Exécution d'un modèle entraîné sur une entrée nouvelle, pour produire une sortie.",
 "Sur une machine de bureau récente, l'inférence d'un modèle de taille moyenne prend moins d'une seconde pour une soixantaine de jetons.",
 None, "13"),
("Invite (système)", "intelligence artificielle",
 "Texte d'instruction fourni à un modèle de langage pour définir son rôle, son registre et ses contraintes.",
 "Véritable lieu de l'auteur dans un dispositif d'arbre parlant. Celle du projet de 2025 n'a jamais été publiée.",
 "Une invite sans bloc de contraintes produit systématiquement des énoncés non traçables.", A),
("Jeton", "intelligence artificielle",
 "Unité élémentaire de texte manipulée par un modèle de langage : un mot court, un fragment de mot long, un signe.",
 "Une phrase française de quinze mots représente environ vingt-cinq jetons.",
 None, "13"),
("Modèle de langage", "intelligence artificielle",
 "Modèle statistique produisant du texte par prédiction du mot suivant, entraîné sur de vastes corpus.",
 "Dans un arbre parlant, il fournit la syntaxe, le ton, les images et le sentiment exprimé — tout, sauf les nombres.",
 "Un modèle produit un texte plausible quelle que soit l'entrée : la plausibilité est une propriété du décodeur, pas une mesure de l'entrée.", A),
("Plongement lexical", "intelligence artificielle",
 "Représentation d'un mot ou d'une phrase par un vecteur numérique dans un espace où la proximité traduit la similarité de sens.",
 "Support théorique de l'idée de « projeter un signal dans un espace de mots ».",
 "La matrice de projection est apprise sur des couples choisis par un humain : le sens ne sort pas du signal, il y a été mis.", "2"),
("Quantification (modèle)", "intelligence artificielle",
 "Réduction de la précision numérique des paramètres d'un modèle, pour diminuer son empreinte mémoire.",
 "Permet d'exécuter localement, sur une machine modeste, des modèles qui exigeraient autrement un serveur.",
 None, "3"),
("Reconnaissance vocale", "intelligence artificielle",
 "Conversion d'un signal audio de parole en texte.",
 "Premier étage de la chaîne conversationnelle d'un arbre parlant ; n'ajoute aucun contenu, il transcrit.",
 None, "13"),
("Synthèse vocale", "intelligence artificielle",
 "Conversion d'un texte en parole audible.",
 "Le choix du timbre — grave, lent, légèrement rauque — construit le personnage autant que le texte.",
 "Aucune propriété physique d'un arbre ne détermine sa voix : c'est un choix de mise en scène.", A),
# ---------------------------------------------------------------- réseaux
("I²C", "électronique",
 "Bus série à deux fils permettant de raccorder plusieurs capteurs numériques à un même microcontrôleur.",
 "Standard de fait pour les capteurs environnementaux ; portée limitée à quelques dizaines de centimètres.",
 None, "3"),
("LoRaWAN", "réseaux",
 "Protocole radio longue portée et basse consommation, en bandes libres (868 MHz en Europe).",
 "Portée de plusieurs kilomètres, consommation d'émission dix à cent fois moindre que le Wi-Fi.",
 "Débit minuscule : impossible d'envoyer un signal brut, il faut extraire les descripteurs sur le nœud.", "3"),
("MQTT", "réseaux",
 "Protocole de messagerie léger, par publication et abonnement, conçu pour les objets connectés.",
 "Colonne vertébrale de la plupart des chaînes d'acquisition libres.",
 None, "3"),
("Veille profonde", "électronique",
 "Mode de fonctionnement où un microcontrôleur coupe l'essentiel de ses circuits, ne conservant qu'une horloge de réveil.",
 "Consommation de quelques dizaines de microampères contre plusieurs dizaines de milliampères en fonctionnement : c'est ce qui rend l'autonomie solaire possible.",
 None, "3"),
# ---------------------------------------------------------------- sonification
("Affichage auditif", "sonification",
 "Terme générique désignant toute présentation d'information par le son (<em>auditory display</em>).",
 "La communauté internationale du domaine (ICAD) organise une conférence annuelle depuis 1992, dont les actes sont en accès libre.",
 None, A),
("Audification", "sonification",
 "Technique consistant à lire directement une série temporelle comme une forme d'onde sonore, généralement après accélération.",
 "La plus fidèle des trois familles de sonification : aucune interprétation n'est ajoutée.",
 "Exige un signal riche et rapide ; inapplicable à une mesure toutes les quinze minutes.", A),
("Biofeedback", "physiologie · technique",
 "Dispositif restituant en temps réel à un sujet une grandeur physiologique habituellement inaccessible à sa conscience.",
 "Le terme est souvent employé abusivement pour les appareils de sonification végétale.",
 "Il n'y a pas de <em>feedback</em> si la plante ne perçoit pas le retour : la boucle n'est jamais démontrée.", A),
("Isomorphe (mapping)", "sonification",
 "Correspondance qui préserve une structure mesurable de l'objet représenté.",
 "Exemple conforme : la sonification des protéines par Buehler, qui conserve les rapports de fréquences des modes de vibration.",
 "Un mapping note → mot n'est pas isomorphe : rien dans le signal ne correspond au mot choisi.", A),
("Mapping paramétrique", "sonification",
 "Technique associant chaque dimension des données à un paramètre sonore : hauteur, timbre, durée, intensité.",
 "La plus répandue des trois familles de sonification.",
 "Le choix du mapping est entièrement arbitraire au regard des données — et détermine pourtant ce qui sera perçu.", A),
("Mapping sémantique", "sonification · linguistique",
 "Substitution de mots ou de phonèmes aux notes dans une sonification.",
 "Mis en œuvre dès 2015 par Alexandre Ferran, avec un échantillonneur chargé d'environ cinquante mots.",
 "N'ajoute aucune information : ajoute de la référence. La charge interprétative migre du système vers l'auditeur.", A),
("MIDI", "audio",
 "Protocole de communication entre instruments de musique électroniques, transmettant des événements (note, vélocité) et non du son.",
 "C'est parce que le MIDI transporte des <em>numéros de note</em> qu'on peut y substituer des mots à des hauteurs.",
 None, "13"),
("Sonification", "sonification",
 "Génération de son dépendante des données, lorsque la transformation est systématique, objective et reproductible.",
 "Définition canonique de Thomas Hermann (ICAD, 2008), assortie de quatre conditions dont la possibilité d'appliquer le système à d'autres jeux de données.",
 "Un dispositif dont on ne peut ni décrire la fonction de transfert, ni la rejouer, n'est pas une sonification : c'est un instrument à contrôleur biologique.", A),
("Sonification modélisée", "sonification",
 "Technique où les données définissent un modèle physique virtuel que l'auditeur excite et écoute vibrer.",
 "Très expressive, elle rend en revanche difficile de démêler la part du modèle de celle des données.",
 None, "2"),
("Spectrogramme", "audio",
 "Représentation temps-fréquence d'un signal, montrant l'évolution de son contenu spectral.",
 "Outil de base pour vérifier qu'un « signal biologique » n'est pas un parasite à 50 Hz et ses harmoniques.",
 None, "23"),
# ---------------------------------------------------------------- traditions
("Animisme", "anthropologie",
 "Ensemble de conceptions attribuant une intériorité aux êtres non humains.",
 "À l'échelle de l'humanité, c'est la position majoritaire ; la réduction du vivant non humain au statut d'objet est une construction récente et localisée.",
 "Le relativisme qui sert à défendre une croyance doit aussi s'appliquer à elle.", "1"),
("Chamanisme", "anthropologie",
 "Ensemble de pratiques fondées sur la modification volontaire de l'état de conscience à des fins de soin, de divination ou de médiation.",
 "Ces traditions comportent généralement une théorie explicite de l'erreur : entité trompeuse, projection, validation par l'efficacité, contrôle par un tiers.",
 "Invoquer la rigueur d'une tradition pour dispenser une pratique de tout contrôle en inverse le sens.", "1"),
("Druidisme", "histoire · religion",
 "Sacerdoce celtique antique ; par extension, les mouvements contemporains s'en réclamant.",
 "Les druides antiques n'écrivaient pas leur enseignement : il n'existe aucun texte druidique.",
 "Le druidisme contemporain est une reconstruction — ce qui ne le disqualifie pas, mais interdit de revendiquer une continuité.", "1"),
("Géobiologie", "pratique",
 "Étude des influences du lieu sur le vivant.",
 "Certains facteurs qu'elle invoque sont physiquement mesurables : radon, champs électromagnétiques, qualité de l'air, résistivité du sous-sol.",
 "D'autres n'ont aucun corrélat physique identifié : leur prêter le vocabulaire de la physique — « fréquences », « vibrations » en hertz — est un abus.", "1"),
("<em>Nemeton</em>", "histoire · religion",
 "Terme celtique désignant un sanctuaire, fréquemment un bosquet consacré.",
 "Attesté par l'épigraphie et la toponymie : Nemetacum, Vernemeton, Drunemeton.",
 None, "1"),
("Ogham", "écriture",
 "Alphabet irlandais des IV<sup>e</sup>-VI<sup>e</sup> siècles, gravé en encoches le long de l'arête d'une pierre.",
 "Environ quatre cents inscriptions lapidaires connues ; les gloses médiévales associent aux lettres des noms souvent empruntés aux arbres.",
 "Le « calendrier celtique des arbres » qu'on lui associe est une reconstruction de Robert Graves (1948), non une tradition transmise.", "1"),
("Radiesthésie", "pratique",
 "Recherche d'informations au moyen d'un pendule ou de baguettes.",
 "Les tentatives de mise à l'épreuve en aveugle n'ont pas produit de résultat reproductible ; le mécanisme idéomoteur en rend compte.",
 None, "1"),
# ---------------------------------------------------------------- histoire
("Backster (effet)", "histoire des sciences",
 "Affirmation, formulée en 1966 par Cleve Backster, que des plantes reliées à un polygraphe réagiraient aux intentions humaines.",
 "Réfuté en conditions contrôlées par Horowitz, Lewis &amp; Gasteiger (1975), <em>Science</em> 189, p. 478-480.",
 "Les tracés observés s'expliquent par l'électricité statique, les mouvements et l'humidité.", A),
("Crescographe", "histoire des sciences",
 "Appareil conçu par Jagadish Chandra Bose pour amplifier optiquement et enregistrer la croissance des plantes.",
 "Emblème de la première électrophysiologie végétale. Exemplaires conservés au Bose Institute de Kolkata.",
 None, A),
("Polygraphe", "histoire des sciences",
 "Appareil enregistrant simultanément plusieurs variables physiologiques, dont la conductance électrodermale.",
 "C'est l'électronique du polygraphe qui a été adaptée aux feuilles pour les premiers appareils de « musique des plantes ».",
 None, A),
]


def fold(s):
    """Replie les accents : « Électrome » doit se classer sous E, pas sous É."""
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")


def render(vol):
    entries = [g for g in G if vol[1] in g[5]]
    rows, cur = [], ""
    for terme, cat, dfn, ctx, ecueil, _ in sorted(
            entries, key=lambda x: fold(x[0]).replace("<em>", "").replace("«", "")
            .replace("</em>", "").strip().lower()):
        plain = fold(terme).replace("<em>", "").replace("</em>", "").lstrip("«").strip()
        if plain[0].upper() != cur:
            cur = plain[0].upper()
            rows.append(f'  <div class="alpha-head">{cur}</div>')
        r = ['  <div class="gloss-item">',
             f'    <div class="gloss-term">{terme}<span class="cat">{cat}</span></div>',
             f'    <div class="gloss-def">{dfn}</div>']
        if ctx:
            r.append(f'    <div class="ctx">{ctx}</div>')
        if ecueil:
            r.append(f'    <div class="ex"><span class="lbl">Écueil — </span>{ecueil}</div>')
        r.append('  </div>')
        rows.append("\n".join(r))

    return f'''<section class="chapter">
  <h2 id="glossaire" data-toc="chapter">Glossaire raisonné</h2>
  <p class="chapo">{len(entries)} entrées. Chaque terme est donné avec sa définition, son contexte d'emploi dans cet ouvrage et, lorsqu'il y a lieu, l'écueil qu'il faut éviter — car dans ce domaine, la plupart des erreurs sont des erreurs de vocabulaire.</p>

  <div class="glossary">
{chr(10).join(rows)}
  </div>
</section>
''', len(entries)


def main():
    print("• Glossaire…")
    for vol, d in DIRS.items():
        out = os.path.join(PARTS, d, "A1-glossaire.html")
        os.makedirs(os.path.dirname(out), exist_ok=True)
        html, n = render(vol)
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  · {vol} : {n} entrées → {os.path.relpath(out, ROOT)}")
    print(f"✓ base commune : {len(G)} termes")


if __name__ == "__main__":
    main()
