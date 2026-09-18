/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/afe.h
 *
 *  Version  : 1.5.1
 *  Date     : 2026-09-18
 *  Éditeur  : Bretagne Namasté
 *  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
 *  Site     : https://bretagne-namaste.com
 *  Contact  : contact@bretagne-namaste.com
 *  Licence  : MIT — voir LICENCE.txt
 *
 *  SPDX-License-Identifier: MIT
 *  fin de l'attribution
 *  ==========================================================================
 */

/* ---------------------------------------------------------------------------
 *  afe.h — chaîne analogique : convertisseur, gain, gamme, auto-test.
 *
 *  Licence MIT — Bretagne Namasté
 * ------------------------------------------------------------------------ */
#ifndef PHYTOSENSE_AFE_H
#define PHYTOSENSE_AFE_H

#include <stdbool.h>
#include <stdint.h>

#define AFE_VOIES        4
#define AFE_GAINS        4           /* ×2, ×10, ×20, ×200 */
#define AFE_GAMMES       4           /* 100 k, 1 M, 10 M, 100 MΩ */
#define AFE_ETALONS      3           /* 1 M, 10 M, 100 MΩ */

/* Un bloc d'échantillons tel qu'il sort du convertisseur. */
typedef struct {
    uint64_t index;                  /* numéro du premier échantillon */
    int32_t  voie[AFE_VOIES];        /* échantillons signés sur 24 bits */
} afe_echantillon_t;

/* État courant de la chaîne, transmis à l'hôte à chaque changement. */
typedef struct {
    uint8_t  gain;                   /* indice dans la table des gains */
    uint8_t  gamme;                  /* indice dans la table des gammes */
    bool     auto_gain;              /* boucle d'auto-échelle active */
    uint16_t offset_cna;             /* recentrage appliqué, 16 bits */
    bool     sature;                 /* au moins une voie en butée */
    float    temperature_c;          /* sonde de la carte */
} afe_etat_t;

/* Rapport d'auto-test sur les étalons internes. */
typedef struct {
    bool  reussi;
    float mesure_ohm[AFE_ETALONS];
    float ecart_pourcent[AFE_ETALONS];
    float bruit_v;
    float fuite_fa;
} afe_autotest_t;

bool  afe_init(void);
void  afe_demarrer(uint32_t frequence_hz);
void  afe_arreter(void);

bool  afe_lire(afe_echantillon_t *sortie);   /* non bloquant */
void  afe_etat(afe_etat_t *sortie);

bool  afe_set_gain(int indice);              /* -1 = automatique */
bool  afe_set_gamme(int indice);
void  afe_set_offset(uint16_t code);

const uint16_t *afe_table_gains(void);
const uint32_t *afe_table_gammes(void);

bool  afe_autotest(afe_autotest_t *rapport);
bool  afe_lire_eeprom_carte_fille(char *type, size_t type_max,
                                  char *serie, size_t serie_max);

/* Conversion d'un code brut en volts, d'après l'état courant. */
float afe_en_volts(int32_t code, const afe_etat_t *etat);

#endif /* PHYTOSENSE_AFE_H */
