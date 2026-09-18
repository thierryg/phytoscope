# État de l'art technique — capteurs, logiciels, projets analogues
Vérifications du 17 septembre 2026

## CORRECTIONS D'INGÉNIERIE MAJEURES

### 1. Le courant de polarisation, et non l'impédance d'entrée
L'erreur de mesure vaut **I_bias × R_source**. Sur une source de 100 MΩ :
| Composant | I_bias | Erreur induite |
|---|---|---|
| INA333 | 200 pA max | 20 mV |
| AD8221-BR | 0,4 nA | 40 mV |
| INA128 (pire cas) | 5 nA | 500 mV |
| INA826 | 65 nA | **saturé** (malgré 20 GΩ annoncés) |

Signal utile : 1 à 50 mV. **Au-delà d'environ 10 MΩ de source, aucun amplificateur
d'instrumentation du commerce ne suffit** : il faut un suiveur électromètre
(LMP7721, ADA4530-1, OPA129) au plus près de l'électrode. Presque toujours absent
des projets amateurs.

### 2. L'ADS1115 seul est disqualifié pour l'électrophysiologie
Impédance d'entrée différentielle **710 kΩ à 22 MΩ selon le gain** (datasheet
SBAS444E §5.5) ; son propre datasheet recommande un tampon. Brancher une électrode
végétale dessus atténue le signal d'un facteur 2,4 à 1400. L'ADS1256 tampon activé
plafonne à 80 MΩ.

### 3. Granier — le facteur 100 et les biais
- `u = 119e-6·K^1,231` → **m/s** · `0,0119·K^1,231` → **cm/s** · `4,284·K^1,231` → dm/h.
  Quatre écritures équivalentes circulent. Exposant exact : **1,231**.
- Biais documentés : **−60 %** sur noisetier (doi:10.3390/s19102419), **−69 %** sur
  *Pinus tabuliformis*, **−37 %** en peuplement de conifères (Peters 2018,
  doi:10.1111/nph.15241), jusqu'à **−50 %** si la sonde déborde de l'aubier
  (Clearwater 1999, doi:10.1093/treephys/19.10.681).
- Méta-analyse de **290 calibrations** (Flo 2019, doi:10.1016/j.agrformet.2019.03.012) :
  la dissipation thermique a la plus faible exactitude et le plus fort biais
  proportionnel, mais une **bonne linéarité → exploitable en flux relatif seulement**.
- ⚠️ La « correction de Lu et al. » **n'existe pas comme formule unique** :
  Lu, Urban & Zhao 2004, *Acta Bot. Sinica* 46(6):631-646, est une **revue, sans DOI**.

### 4. Gradients thermiques naturels du tronc
0,3 à 3,5 °C sur 8-10 cm, induisant des erreurs de flux **> 100 %**
(Do & Rocheteau 2002, doi:10.1093/treephys/22.9.641 et .649).
Parade validée : **chauffage cyclique 45 min ON / 15 min OFF** — qui divise en prime
la consommation par quatre.

### 5. Électrode de référence : deux fonctions distinctes
Sans référence, l'amplificateur ne mesure **rien** (pas de chemin de retour du courant
de polarisation — datasheet INA128 explicite). Le sol est un bon retour de courant mais
une mauvaise référence (la jonction sol/racine dérive avec la pluie).
**Tronc à ≥ 50 cm = meilleur compromis** (même chimie → la jonction se soustrait).
Parade radicale si l'on ne cherche que des événements : **couplage alternatif à 0,05 Hz**
(l'AD8232 l'intègre) — au prix de toute information saisonnière.

### 6. Licences — plusieurs idées reçues à corriger
- **InfluxDB 3 Core est passé à MIT/Apache-2.0** (disponibilité générale avril 2025) ;
  c'est *Enterprise* qui est fermé. Contre-intuitif.
- **Grafana est AGPLv3 depuis le 20 avril 2021.**
- TimescaleDB : Apache-2.0 hors `tsl/`, TSL dedans. Timescale Inc. renommée
  **TigerData** (17/06/2025) — renommage, pas rachat.
- **XTTS v2 est juridiquement hors-jeu** : la *Coqui Public Model License* couvre
  explicitement les fichiers audio produits et exclut toute activité génératrice de
  revenus, « y compris les projets financés par des subventions publiques ».
- **Piper 1 = `OHF-Voice/piper1-gpl`** ; l'ancien `rhasspy/piper` est **archivé**
  depuis le 06/10/2025. Code passé **MIT → GPLv3**, poids en MIT.
- Firmware MIDI Sprout : réellement **MIT**. Mais le dépôt le plus étoilé
  (BreadboardKit, 147 ★) est **sans fichier LICENSE** → « tous droits réservés ».
- Biotron (Playtronica) : **GPL-3.0** — cas rare de produit vendu au firmware ouvert.
- **Un dépôt sans LICENSE est « tous droits réservés » par défaut.**

### 7. Le « Talking Tree » belge — rectifications
Domaine réel **`talking-tree.com`** (pas `.be`) ; compte **@eostalkingtree** ;
**shortlist** Cannes Lions 2011 mais **aucun Lion** ; **Wood Pencil D&AD 2011** confirmé.
Le site archivé est **100 % Flash** → contenu perdu. Vilvoorde est le siège de Happiness
Brussels, **pas** l'emplacement de l'arbre. Capteurs convergents sur quatre sources :
particules fines, ozone, lumière, station météo, webcam, micro.

### 8. Deux « Nature 4.0 » sans lien entre elles
- LOEWE *Nature 4.0 – Sensing Biodiversity* (Marburg, financement du Land de Hesse,
  **pas H2020** ; doi:10.1111/gcb.17056)
- **Nature 4.0 Società Benefit Srl** (Viterbe, R. Valentini), qui fabrique le TreeTalker.
  Celui-ci utilise **HPV, pas Granier** (impulsion 6 s/heure), spectro 28 canaux
  AS7265x+AS7341, dendromètre ~0,4 µm, accéléromètre — **pas d'humidité du tronc**.
  **Non open-hardware**, mais **données brutes ouvertes** (endpoints HTTP documentés)
  et paquets R tiers (`ttprocessing`, `ttalkR`).
  Tarif 2026 : TT Cyber **420 € LoRa / 510 € NB-IoT**, passerelle **1 100 €**
  → ≈ 1 600 € pour le premier arbre.
- **TreeWatch.net est vivant** : 55 arbres, 19 sites, 8 pays (Gand, Steppe ;
  doi:10.3389/fpls.2016.00993). Sapflow+ maison + dendromètre Natkon ZN11-T-WP.

### 9. Bibliothèques Python de sonification
- **`strauss`** = la seule réellement maintenue (JOSS doi:10.21105/joss.07875).
  ⚠️ auteur à **Portsmouth**, pas Newcastle. **Divergence de licence non résolue** :
  Apache-2.0 dans le dépôt, MIT sur PyPI.
- `astronify` (STScI, BSD-3) : maintenu lentement.
- **`sonipy` : abandonné** (aucune publication depuis 2020).

## SYNTHÈSES CHIFFRÉES

### Capteurs d'ambiance
DS18B20 ±0,5 °C (1-Wire) · BME280 ±1,0 °C / ±3 %HR / ±1 hPa · SHT31 ±0,2 °C / ±2 % ·
**SHT85 ±0,1 °C / ±1,5 %** · BH1750 1-65 535 lx · TSL2591 188 µlx-88 klx ·
SCD30 ±(30 ppm+3 %) vs **SCD41 ±(40 ppm+5 %)** — le SCD30 est plus juste malgré son
ancienneté · BME680 : **indice COV inutilisable sans BSEC et calibration multi-jours**.

**Lux ≠ PPFD** : le facteur 0,0185 n'est valable **que sous soleil**
(108 klx ≈ 2 000 µmol·m⁻²·s⁻¹) ; sous LED horticole l'erreur dépasse un facteur 3.
Apogee SQ-500 : 389-692 nm ±5 nm, erreur directionnelle ≤ ±5 % à 75°.

### Humidité du sol
Résistif = électrolyse par courant continu, destruction en semaines + sensibilité à la
salinité → **à proscrire**. Capacitif = pas de corrosion mais **non étalonné** ; la v1.2
n'a pas de régulateur (la lecture dépend de Vcc) → préférer la **v2.0**.
Watermark 200SS : 0-200 kPa, calibration Shock 1998 valide de 10 à 100 kPa.
TEROS 12 : ±0,03 m³/m³, SDI-12. Acclima TDR-315N : vrai TDR, base de temps 5 ps.

### Plateformes
ESP32-S3 ≈ **13,4 µA** / ESP32-C6 ≈ **16,9 µA** en veille **au niveau carte**
(7 µA au niveau puce) — *le régulateur et la puce USB-série dominent, pas le SoC*.
Pico 2 W (RP2350). **Pycom/LoPy : discontinué** (dernières commandes juillet 2022).
MKR WAN 1310 ≈ 104 µA.

### LoRaWAN / TTN
Rapport cyclique 1 % en EU868 + **politique d'usage équitable : 30 s d'émission par jour
et 10 messages descendants** → ≈ **100 messages courts par jour**, soit exactement un
relevé au quart d'heure. **Aucune marge pour une forme d'onde : le traitement doit être
dans le nœud.**

### Budget d'énergie type (relevé au quart d'heure)
61,5 mA·s par cycle → **1,64 mA·h/jour** → une cellule de 6 000 mA·h tiendrait environ
dix ans sans soleil. **La capacité n'est jamais la contrainte.** Ce qui tue les stations :
la consommation résiduelle des cartes de développement, et la **charge sous 0 °C**
(dépôt de lithium métallique irréversible).

### Synthèse vocale
**Piper 1** (`OHF-Voice/piper1-gpl`) : **6 voix françaises réelles**, aucune en qualité
`high`. `siwis-medium` (CC-BY 4.0) recommandée ; `tom-medium` en 44,1 kHz mais corpus
AGPLv3 ; `mls-medium` 125 locuteurs. **Kokoro : une seule voix FR** (`ff_siwis`, note B−,
< 11 h) issue du **même corpus SIWIS** — donc pas une alternative de timbre.
Coqui : seuls `css10/vits` (BSD-3) et `mai/tacotron2-DDC` (MPL-2.0) sont exploitables
commercialement.

### Modèles de langage locaux (Q4_K_M, mesures `geerlingguy/ai-benchmarks`)
| Machine | Modèle | Débit |
|---|---|---|
| Pi 5 8 Go | llama3.2:3b | **4,61 t/s** (13,9 W) |
| Pi 5 8 Go | llama3.1:8b | 1,99 t/s |
| Pi 5 8 Go | 13b | échec |
| Pi 5 16 Go | deepseek-r1:14b | 1,20 t/s |
| Pi 400 (≈ Pi 4) | 3b | 1,60 t/s → **hors sujet** |
| Mini-PC N150 | 3b / 8b | 9,06 / 3,91 t/s |

Tailles vérifiées : Qwen3-0.6B 0,48 Go · Llama-3.2-1B 0,81 · Qwen3-1.7B 1,28 ·
Llama-3.2-3B 2,02 · Qwen3-4B 2,50 · Llama-3.1-8B 4,92.
**Zone confortable : 0,6 à 4 milliards de paramètres → 5 à 12 jetons/s.**
⚠️ **Qwen2.5-3B n'est PAS Apache-2.0** (licence `qwen-research`) ; **Qwen3 l'est
intégralement** → famille la plus propre juridiquement. Ministral 3 (2512) est en
Apache-2.0, contrairement à Ministral 8B (2410, licence non commerciale).

## LIMITES DE TERRAIN
Le problème dominant en longue durée **n'est pas le bruit : c'est la dérive du potentiel
de demi-pile** des électrodes, qui apparaît en différentiel et se confond avec un signal
biologique lent. S'y ajoutent : potentiel de jonction (mV à dizaines de mV,
**≈ 0,2 mV/°C**, du même ordre que le signal) ; impédance de contact variant avec
l'humidité du rhytidome (hygroscopique) ; micromouvements sous le vent ; couplage 50 Hz
(l'arbre est une antenne de plusieurs mètres) ; absence de cage de Faraday.
Parade documentée : **alimentation sur batterie, enregistreurs séparés** pour
l'environnement et l'électrophysiologie, afin d'éviter la diaphonie.
La littérature de terrain admet que « les signaux n'étaient pas détectables pendant les
perturbations » (pluie, champs électriques anormaux).

### Le problème fondamental, formulé nettement
Le front-end biodata classique **ne mesure pas un signal émis par la plante** : il
**injecte un courant et mesure une impédance de surface**, analogue exact de la réponse
électrodermale. Dans le firmware, le **seuil de détection détermine à lui seul la densité
de notes** : tourné d'un côté la plante « joue » sans arrêt, de l'autre elle se tait.
Aucune position n'est plus vraie que l'autre. **L'expressivité perçue est un réglage
humain.** La quantification sur gamme achève le travail : le résultat est agréable
exactement dans la mesure où l'information a été écrasée.
Aucune publication évaluée par les pairs ne montre que le rendu sonore de ces appareils
encode une information physiologique interprétable.
*Music of the Plants* / Damanhur est à classer à part : **zéro publication**, et un
partenariat affiché avec la « Bosnian Pyramid Foundation ».

### Projets artistiques de référence
**Pulsu(m) Plantae** de Leslie García (`github.com/Lessnullvoid/Pulsum-Plantae`, PCB
Fritzing, ampli LM324) — le meilleur candidat pour un atelier ouvert.
Sommerer & Mignonneau, *Interactive Plant Growing* (1992, collection ZKM).
Scenocosme, *Akousmaflore* — qui détecte en réalité **le visiteur** par couplage
capacitif, la plante servant d'électrode. Distinction à ne pas gommer.

## NON VÉRIFIÉ — à assumer explicitement
- **Facteur temps réel de Piper sur Raspberry Pi** : aucune source primaire. Les valeurs
  qui circulent viennent de blogs non reproductibles. À mesurer sur cible.
- **Prix distributeur des circuits intégrés** : Mouser, Digi-Key, Farnell, RS, Octopart,
  LCSC systématiquement inaccessibles. Les prix cités sont des ordres de grandeur.
- **Textes intégraux de Granier 1985/1987** non lus ; coefficient attesté par quatre
  sources secondaires concordantes.
- **Impédance de source publiée pour un enregistrement sur tronc** : introuvable. La
  fourchette MΩ-GΩ est cohérente physiquement mais non sourcée.
- **Aucun article HardwareX sur un capteur de flux de sève open source** : les
  équivalents réels sont OPEnS Lab et Baseliner/SoftwareX.
- Licences à vérifier : Pulsum-Plantae, SapFlowMeterOld, SDK Plants Play.
- **Les planches 2 à 5 sont des schémas d'application composés d'après datasheets —
  non prototypés.** Seule la planche 1 est un relevé de netlist réel.
