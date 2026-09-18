/* ===========================================================================
   DamanhurBridge — micrologiciel de reconstitution
   ---------------------------------------------------------------------------
   Reconstruction libre de l'architecture décrite par le brevet
   US 6 487 817 B2 (O. Airaudi, Music of Plants Inc., priorité 02/06/1999,
   EXPIRÉ depuis le 13 juin 2019) et son extension US 6 743 164 B2.

   Le code d'origine du Device U1 n'a jamais été publié : le brevet le
   mentionne sous la forme « le code objet de l'ANNEXE I », annexe déposée
   sur microfiche et absente du document numérisé. Ce fichier propose donc
   une IMPLÉMENTATION ORIGINALE des fonctions décrites en clair par le
   brevet, écrite pour du matériel contemporain.

   Publié avec l'ouvrage « La Musique des Plantes » (Bretagne Namasté, 2026)
   sous licence MIT. Aucune affiliation avec Damanhur ni Music of the Plants.

   ---------------------------------------------------------------------------
   ARCHITECTURE RECONSTITUÉE
   ---------------------------------------------------------------------------
     PLANTE (Rp)  →  pont de Wheatstone  →  ampli d'instrumentation INA333
                  →  convertisseur A/N 16 bits ADS1115
                  →  BOUCLE DE NULLIFICATION par convertisseur N/A MCP4725
                     injecté sur la broche REF de l'INA333
                  →  la CONSIGNE du convertisseur N/A est la MESURE
                  →  détection d'événement → quantification → MIDI

   Principe repris du brevet (col. 6-7) : « le microprocesseur et son
   programme suivent les variations de la résistance de l'élément végétal
   puis créent un signal opposé pour annuler ce changement ». L'amplificateur
   travaille ainsi en permanence autour de zéro, dans sa zone la plus
   linéaire, quelle que soit l'amplitude de la dérive d'interface.

   ---------------------------------------------------------------------------
   MATÉRIEL
   ---------------------------------------------------------------------------
     Arduino Nano / Pro Mini 5 V (ATmega328P, 16 MHz)
     ADS1115   convertisseur A/N 16 bits, I²C, adresse 0x48
     MCP4725   convertisseur N/A 12 bits, I²C, adresse 0x60
     INA333    amplificateur d'instrumentation, Rg = 1 kΩ → G ≈ 101
     REF3025   référence de tension 2,5 V pour l'alimentation du pont
     Rb        résistances de référence 1 MΩ / 4,7 MΩ / 10 MΩ,
               commutées par D4 et D5 via un multiplexeur analogique CD4066
     R3 = R4   1 MΩ 0,1 % appariées (bras fixe du pont)

     Face avant, d'après la planche FIG. 3 du brevet :
       A0  SCALE         gamme
       A1  NOTE          tonique
       A2  SAMPLE RATE   fréquence d'échantillonnage
       A3  EVENT FILTER  seuil de déclenchement
       D6  MODE          bouton : majeur / mineur / modal
       D7  AUTO RANGE    interrupteur
       D8  MIDI VELOCITY interrupteur : fixe ou proportionnelle
       D1  TX → sortie MIDI DIN, via 220 Ω

   ALIMENTATION SUR PILES EXCLUSIVEMENT. Voir les règles de sécurité,
   chapitre 36 de l'ouvrage.
   =========================================================================== */

#include <Wire.h>

/* --- Adresses I²C ------------------------------------------------------- */
#define ADS1115_ADDR   0x48
#define MCP4725_ADDR   0x60

/* --- Registres ADS1115 -------------------------------------------------- */
#define ADS_REG_CONV   0x00
#define ADS_REG_CONFIG 0x01

/* --- Broches ------------------------------------------------------------ */
const uint8_t PIN_SCALE      = A0;
const uint8_t PIN_NOTE       = A1;
const uint8_t PIN_RATE       = A2;
const uint8_t PIN_FILTER     = A3;
const uint8_t PIN_MODE       = 6;
const uint8_t PIN_AUTORANGE  = 7;
const uint8_t PIN_VELOCITY   = 8;
const uint8_t PIN_RANGE_A    = 4;   /* commande Rb, bit 0 */
const uint8_t PIN_RANGE_B    = 5;   /* commande Rb, bit 1 */
const uint8_t PIN_LED_EVENT  = 9;   /* témoin d'événement (PWM)            */
const uint8_t PIN_LED_LOCK   = 10;  /* témoin de boucle verrouillée (PWM)  */

/* ===========================================================================
   GAMMES — les dix-sept gammes annoncées par Music of the Plants.
   Format : { nombre de degrés, degrés en demi-tons depuis la tonique }
   =========================================================================== */
const uint8_t SC_MAJEUR[]        = { 7, 0, 2, 4, 5, 7, 9, 11 };
const uint8_t SC_MINEUR_NAT[]    = { 7, 0, 2, 3, 5, 7, 8, 10 };
const uint8_t SC_MINEUR_HARM[]   = { 7, 0, 2, 3, 5, 7, 8, 11 };
const uint8_t SC_PENTA_MAJ[]     = { 5, 0, 2, 4, 7, 9 };
const uint8_t SC_PENTA_MIN[]     = { 5, 0, 3, 5, 7, 10 };
const uint8_t SC_BLUES[]         = { 6, 0, 3, 5, 6, 7, 10 };
const uint8_t SC_DORIEN[]        = { 7, 0, 2, 3, 5, 7, 9, 10 };
const uint8_t SC_PHRYGIEN[]      = { 7, 0, 1, 3, 5, 7, 8, 10 };
const uint8_t SC_LYDIEN[]        = { 7, 0, 2, 4, 6, 7, 9, 11 };
const uint8_t SC_MIXOLYDIEN[]    = { 7, 0, 2, 4, 5, 7, 9, 10 };
const uint8_t SC_HEALING[]       = { 6, 0, 2, 5, 7, 9, 11 };   /* Lydien pentatonisé */
const uint8_t SC_JAPON_HIRA[]    = { 5, 0, 2, 3, 7, 8 };       /* Hirajōshi */
const uint8_t SC_CHINOIS[]       = { 5, 0, 4, 6, 7, 11 };
const uint8_t SC_AMERINDIEN[]    = { 5, 0, 3, 5, 7, 10 };
const uint8_t SC_INDIEN_BHAIR[]  = { 7, 0, 1, 4, 5, 7, 8, 11 };
const uint8_t SC_ARABE_HIJAZ[]   = { 7, 0, 1, 4, 5, 7, 8, 10 };
const uint8_t SC_CHROMATIQUE[]   = { 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11 };

const uint8_t* const GAMMES[] = {
  SC_CHROMATIQUE,   /* 0 — par défaut : le mode HONNÊTE (voir chap. 11) */
  SC_MAJEUR, SC_MINEUR_NAT, SC_MINEUR_HARM,
  SC_PENTA_MAJ, SC_PENTA_MIN, SC_BLUES,
  SC_DORIEN, SC_PHRYGIEN, SC_LYDIEN, SC_MIXOLYDIEN,
  SC_HEALING, SC_JAPON_HIRA, SC_CHINOIS, SC_AMERINDIEN,
  SC_INDIEN_BHAIR, SC_ARABE_HIJAZ
};
const uint8_t NB_GAMMES = sizeof(GAMMES) / sizeof(GAMMES[0]);

/* ===========================================================================
   PARAMÈTRES DE LA BOUCLE DE NULLIFICATION
   =========================================================================== */
const int16_t  ADC_CENTRE     = 0;      /* consigne : sortie d'ampli nulle   */
const int16_t  ADC_BANDE_MORTE= 12;     /* ≈ 0,75 mV au gain 16 — anti-pompage */
const uint16_t DAC_MILIEU     = 2048;   /* mi-course du convertisseur N/A     */
const uint16_t DAC_MIN        = 200;    /* butées : au-delà, il faut changer  */
const uint16_t DAC_MAX        = 3896;   /* de calibre de résistance Rb        */
const float    GAIN_INTEGRAL  = 0.06;   /* gain de la boucle. Trop haut = elle
                                           oscille ; trop bas = elle décroche */

/* ===========================================================================
   ÉTAT
   =========================================================================== */
uint16_t dacValeur   = DAC_MILIEU;  /* LA MESURE : consigne d'annulation      */
uint8_t  calibre     = 1;           /* 0 = 1 MΩ, 1 = 4,7 MΩ, 2 = 10 MΩ        */
bool     boucleOK    = false;       /* vrai quand l'erreur reste dans la bande */

const uint8_t FENETRE = 12;         /* taille de la fenêtre d'analyse         */
uint16_t fen[FENETRE];
uint8_t  fenIdx = 0;

uint32_t tPrec = 0;
uint16_t periodeMs = 100;           /* fixée par SAMPLE RATE                  */

/* Notes MIDI en cours — polyphonie 5, comme le MIDI Sprout */
const uint8_t POLY = 5;
struct Note { uint8_t hauteur; uint32_t fin; bool active; };
Note notes[POLY];

uint8_t canalMidi = 1;
uint8_t ccNumero  = 80;    /* même n° que Plants Play, par commodité */
uint8_t ccDernier = 64;
uint8_t niveauLed = 0;      /* luminosité courante du témoin d'événement */

/* ===========================================================================
   COUCHE MATÉRIELLE — I²C brut, sans bibliothèque externe
   =========================================================================== */

/* ADS1115 : configuration en mesure unique, différentielle AIN0-AIN1.
   pga : 0 = ±6,144 V … 5 = ±0,256 V. On travaille au gain 16 (pga = 5)
   pour résoudre 7,8 µV par bit. */
void adsDemarrerMesure(uint8_t pga) {
  uint16_t config = 0;
  config |= 0x8000;              /* OS = 1 : lance une conversion             */
  config |= 0x0000;              /* MUX = 000 : différentiel AIN0 − AIN1      */
  config |= ((uint16_t)pga) << 9;
  config |= 0x0100;              /* MODE = 1 : mesure unique                  */
  config |= 0x0080;              /* DR = 100 : 128 échantillons par seconde   */
  config |= 0x0003;              /* comparateur désactivé                     */

  Wire.beginTransmission(ADS1115_ADDR);
  Wire.write(ADS_REG_CONFIG);
  Wire.write(config >> 8);
  Wire.write(config & 0xFF);
  Wire.endTransmission();
}

int16_t adsLire() {
  Wire.beginTransmission(ADS1115_ADDR);
  Wire.write(ADS_REG_CONV);
  Wire.endTransmission();
  Wire.requestFrom((uint8_t)ADS1115_ADDR, (uint8_t)2);
  if (Wire.available() < 2) return 0;
  int16_t v = ((int16_t)Wire.read() << 8);
  v |= Wire.read();
  return v;
}

/* MCP4725 : écriture rapide, 12 bits */
void dacEcrire(uint16_t valeur) {
  if (valeur > 4095) valeur = 4095;
  Wire.beginTransmission(MCP4725_ADDR);
  Wire.write(0x40);                       /* commande d'écriture du registre */
  Wire.write(valeur >> 4);
  Wire.write((valeur & 0x0F) << 4);
  Wire.endTransmission();
}

/* Commutation de la résistance de référence Rb — fonction AUTO RANGE */
void choisirCalibre(uint8_t c) {
  calibre = c;
  digitalWrite(PIN_RANGE_A, c & 0x01);
  digitalWrite(PIN_RANGE_B, (c >> 1) & 0x01);
  /* Après un changement de calibre, le pont est fortement déséquilibré :
     on recentre le convertisseur N/A et on laisse la boucle rattraper. */
  dacValeur = DAC_MILIEU;
  dacEcrire(dacValeur);
  boucleOK = false;
}

/* ===========================================================================
   SORTIE MIDI — trame série à 31 250 bauds, conforme à la norme
   =========================================================================== */
void midiEnvoyer(uint8_t statut, uint8_t canal, uint8_t d1, uint8_t d2) {
  noInterrupts();
    d1 &= 0x7F;
    d2 &= 0x7F;
    Serial.write((uint8_t)(statut | ((canal - 1) & 0x0F)));
    Serial.write(d1);
    Serial.write(d2);
  interrupts();
}

void noteOn(uint8_t hauteur, uint8_t velocite, uint32_t duree) {
  for (uint8_t i = 0; i < POLY; i++) {
    if (!notes[i].active) {
      notes[i].hauteur = hauteur;
      notes[i].fin     = millis() + duree;
      notes[i].active  = true;
      midiEnvoyer(0x90, canalMidi, hauteur, velocite);
      niveauLed = 255;
      analogWrite(PIN_LED_EVENT, niveauLed);
      return;
    }
  }
  /* Polyphonie saturée : on vole la note la plus ancienne */
  uint8_t plusVieille = 0;
  for (uint8_t i = 1; i < POLY; i++)
    if (notes[i].fin < notes[plusVieille].fin) plusVieille = i;
  midiEnvoyer(0x90, canalMidi, notes[plusVieille].hauteur, 0);
  notes[plusVieille].hauteur = hauteur;
  notes[plusVieille].fin     = millis() + duree;
  midiEnvoyer(0x90, canalMidi, hauteur, velocite);
}

void verifierNotes() {
  uint32_t t = millis();
  for (uint8_t i = 0; i < POLY; i++) {
    if (notes[i].active && t >= notes[i].fin) {
      midiEnvoyer(0x90, canalMidi, notes[i].hauteur, 0);   /* Note Off */
      notes[i].active = false;
    }
  }
}

void toutesNotesOff() {
  for (uint8_t i = 0; i < POLY; i++)
    if (notes[i].active) {
      midiEnvoyer(0x90, canalMidi, notes[i].hauteur, 0);
      notes[i].active = false;
    }
}

/* ===========================================================================
   QUANTIFICATION SUR LA GAMME
   Contrairement au MIDI Sprout, on ne fait PAS de « note % 127 » : la
   correspondance mesure → hauteur reste monotone, donc physiquement
   interprétable (voir chapitre 37 de l'ouvrage).
   =========================================================================== */
uint8_t quantifier(uint8_t note, const uint8_t* gamme, uint8_t tonique) {
  uint8_t nbDegres = gamme[0];
  int8_t  classe   = (int8_t)((note - tonique + 120) % 12);
  uint8_t octave   = (note - tonique + 120) / 12;

  uint8_t meilleur = gamme[1];
  uint8_t ecartMin = 12;
  for (uint8_t i = 1; i <= nbDegres; i++) {
    uint8_t e = abs((int8_t)gamme[i] - classe);
    if (e < ecartMin) { ecartMin = e; meilleur = gamme[i]; }
  }
  int16_t res = (int16_t)meilleur + 12 * (int16_t)octave + tonique - 120;
  if (res < 24)  res = 24;
  if (res > 100) res = 100;
  return (uint8_t)res;
}

/* ===========================================================================
   LECTURE DE LA FACE AVANT
   =========================================================================== */
const uint8_t* gammeActive = SC_CHROMATIQUE;
uint8_t tonique   = 0;       /* do */
float   seuilMult = 2.3;     /* EVENT FILTER */
bool    veloProp  = true;    /* MIDI VELOCITY */
bool    autoRange = true;

void lireFaceAvant() {
  uint8_t g = map(analogRead(PIN_SCALE), 0, 1023, 0, NB_GAMMES - 1);
  gammeActive = GAMMES[g];

  tonique = map(analogRead(PIN_NOTE), 0, 1023, 0, 11);

  /* SAMPLE RATE : de 20 ms (rapide, nerveux) à 500 ms (lent, contemplatif) */
  periodeMs = map(analogRead(PIN_RATE), 0, 1023, 20, 500);

  /* EVENT FILTER : multiplicateur d'écart-type, de 1,5 à 4,0 */
  seuilMult = 1.5 + (analogRead(PIN_FILTER) / 1023.0) * 2.5;

  veloProp  = (digitalRead(PIN_VELOCITY) == LOW);
  autoRange = (digitalRead(PIN_AUTORANGE) == LOW);
}

/* ===========================================================================
   BOUCLE DE NULLIFICATION — le cœur de l'architecture Damanhur
   =========================================================================== */
void asservir() {
  adsDemarrerMesure(5);              /* gain 16 : ±0,256 V, 7,8 µV par bit  */
  delayMicroseconds(9000);           /* 128 éch./s → ≈ 8 ms de conversion   */
  int16_t brut = adsLire();

  int16_t erreur = brut - ADC_CENTRE;

  if (abs(erreur) <= ADC_BANDE_MORTE) {
    boucleOK = true;
    analogWrite(PIN_LED_LOCK, 60);
    return;                          /* dans la bande morte : on ne bouge pas */
  }
  boucleOK = false;
  analogWrite(PIN_LED_LOCK, 255);

  /* Correction intégrale : on déplace la consigne du convertisseur N/A
     jusqu'à ramener la sortie de l'amplificateur à zéro.
     C'est l'équivalent numérique de la boucle convertisseur
     fréquence/tension du brevet (intégrateur de 220 ms). */
  int32_t correction = (int32_t)(erreur * GAIN_INTEGRAL);
  if (correction == 0) correction = (erreur > 0) ? 1 : -1;

  int32_t nouveau = (int32_t)dacValeur - correction;

  /* Butées : si la boucle sature, il faut changer de calibre de Rb */
  if (nouveau < DAC_MIN) {
    if (autoRange && calibre < 2) { choisirCalibre(calibre + 1); return; }
    nouveau = DAC_MIN;
  }
  if (nouveau > DAC_MAX) {
    if (autoRange && calibre > 0) { choisirCalibre(calibre - 1); return; }
    nouveau = DAC_MAX;
  }

  dacValeur = (uint16_t)nouveau;
  dacEcrire(dacValeur);
}

/* ===========================================================================
   ANALYSE — détection d'événement sur la série des consignes d'annulation
   Même principe statistique que le MIDI Sprout, mais appliqué à une
   grandeur physiquement interprétable : la consigne d'annulation est
   proportionnelle au déséquilibre du pont, donc à la variation de Rp.
   =========================================================================== */
void analyser() {
  uint32_t somme = 0, sommeCarres = 0;
  uint16_t mini = 0xFFFF, maxi = 0;

  for (uint8_t i = 0; i < FENETRE; i++) {
    uint16_t v = fen[i];
    somme       += v;
    sommeCarres += (uint32_t)v * v;
    if (v < mini) mini = v;
    if (v > maxi) maxi = v;
  }

  float moyenne = (float)somme / FENETRE;
  float variance = ((float)sommeCarres / FENETRE) - (moyenne * moyenne);
  if (variance < 0) variance = 0;
  float ecartType = sqrt(variance);
  if (ecartType < 1.0) ecartType = 1.0;

  uint16_t delta = maxi - mini;

  /* ------ Détection --------------------------------------------------- */
  if ((float)delta > ecartType * seuilMult) {

    /* Hauteur : correspondance MONOTONE sur toute la plage utile du
       convertisseur N/A, sans repliement modulo. */
    uint8_t brute = map(constrain((int)moyenne, DAC_MIN, DAC_MAX),
                        DAC_MIN, DAC_MAX, 36, 96);
    uint8_t note  = quantifier(brute, gammeActive, tonique);

    /* Durée proportionnelle à l'amplitude, comme dans le brevet PlantWave */
    uint32_t duree = map(constrain(delta, 0, 400), 0, 400, 250, 2500);

    /* Vélocité : proportionnelle si MIDI VELOCITY est sur « variable »,
       sinon fixe à 100 — les deux modes de la planche FIG. 3 du brevet. */
    uint8_t velo = veloProp
                 ? (uint8_t)map(constrain(delta, 0, 400), 0, 400, 45, 127)
                 : 100;

    noteOn(note, velo, duree);

    /* Message de contrôle continu, dérivé de l'amplitude */
    uint8_t cc = (uint8_t)map(constrain(delta, 0, 400), 0, 400, 0, 127);
    if (cc != ccDernier) {
      midiEnvoyer(0xB0, canalMidi, ccNumero, cc);
      ccDernier = cc;
    }
  }

  fenIdx = 0;
}

/* ===========================================================================
   SETUP / LOOP
   =========================================================================== */
void setup() {
  pinMode(PIN_MODE,      INPUT_PULLUP);
  pinMode(PIN_AUTORANGE, INPUT_PULLUP);
  pinMode(PIN_VELOCITY,  INPUT_PULLUP);
  pinMode(PIN_RANGE_A,   OUTPUT);
  pinMode(PIN_RANGE_B,   OUTPUT);
  pinMode(PIN_LED_EVENT, OUTPUT);
  pinMode(PIN_LED_LOCK,  OUTPUT);

  Serial.begin(31250);          /* débit MIDI normalisé */
  Wire.begin();
  Wire.setClock(400000);        /* I²C rapide : la boucle doit être vive */

  for (uint8_t i = 0; i < POLY; i++) notes[i].active = false;

  choisirCalibre(1);            /* on démarre sur 4,7 MΩ, le cas courant */
  delay(50);

  /* Amorçage de la boucle : on la laisse converger avant de produire
     la moindre note. C'est l'équivalent logiciel des 30 minutes de
     stabilisation décrites au chapitre 23. */
  uint32_t t0 = millis();
  while (millis() - t0 < 5000) { asservir(); delay(5); }

  tPrec = millis();
}

void loop() {
  lireFaceAvant();

  /* 1. Asservissement — en permanence, au rythme le plus rapide possible */
  asservir();

  /* 2. Échantillonnage à la cadence fixée par SAMPLE RATE */
  if (millis() - tPrec >= periodeMs) {
    tPrec = millis();
    if (boucleOK) {                 /* on n'échantillonne que verrouillé */
      fen[fenIdx++] = dacValeur;
      if (fenIdx >= FENETRE) analyser();
    }
  }

  /* 3. Extinction des notes échues */
  verifierNotes();

  /* 4. Extinction douce du témoin d'événement, sans delay() */
  static uint32_t tLed = 0;
  if (millis() - tLed > 30) {
    tLed = millis();
    if (niveauLed > 8) niveauLed -= 8; else niveauLed = 0;
    analogWrite(PIN_LED_EVENT, niveauLed);
  }
}

/* ===========================================================================
   NOTES DE MISE AU POINT
   ---------------------------------------------------------------------------
   · GAIN_INTEGRAL trop élevé → la boucle oscille : le témoin LOCK clignote
     en permanence et les notes deviennent erratiques. Divisez-le par deux.
   · GAIN_INTEGRAL trop faible → la boucle décroche dès que la plante bouge :
     le convertisseur N/A tape dans ses butées. Multipliez-le par deux.
   · ADC_BANDE_MORTE trop étroite → pompage. Trop large → on perd les
     micro-variations, qui sont précisément l'objet de la mesure.
   · Pour convertir la consigne du convertisseur N/A en ohms, il faut
     étalonner : remplacez la plante par des résistances connues et relevez
     dacValeur. La relation est affine sur la plage utile.
   · Pour journaliser la mesure physique, ajoutez un port série logiciel
     (SoftwareSerial) sur deux broches libres — le port matériel est occupé
     par le MIDI. N'utilisez jamais Serial.print() : cela injecterait du
     texte dans la trame MIDI.
   =========================================================================== */
