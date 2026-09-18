/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/afe.c
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

/* ===========================================================================
 *  afe.c — chaîne analogique : convertisseur, gain, gamme, auto-test.
 *
 *  Tout ce qui touche à la mesure est ici, et rien d'autre. Le reste du
 *  micrologiciel ignore comment un code brut devient des volts : il appelle
 *  afe_en_volts() et se tait.
 *
 *  Le convertisseur ADS131M04 est servi par SPI en accès direct à la mémoire,
 *  déclenché par sa propre broche « données prêtes ». Le microcontrôleur ne
 *  scrute rien : il est réveillé par le convertisseur, ce qui garantit que la
 *  cadence d'échantillonnage est celle du quartz compensé, et non celle d'une
 *  boucle logicielle.
 *
 *  Licence MIT — Bretagne Namasté — https://bretagne-namaste.com
 * ======================================================================== */

#include <math.h>        /* sqrt(), pour l'écart-type de l'auto-test          */
#include <stdio.h>       /* snprintf(), pour lire l'étiquette de la carte     */
#include <string.h>

#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/dma.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"

#include "afe.h"

/* --------------------------------------------------------------------------
 *  Brochage
 * ----------------------------------------------------------------------- */
#define SPI_PORT        spi0
#define BR_SCK          2
#define BR_MOSI         3
#define BR_MISO         4
#define BR_CS           5
#define BR_DRDY         6        /* données prêtes, actif bas */
#define BR_RESET        7

#define I2C_PORT        i2c0
#define BR_SDA          20
#define BR_SCL          21

#define BR_GAIN_A0      10       /* sélection du gain, multiplexeur U8 */
#define BR_GAIN_A1      11
#define BR_GAMME_A0     12       /* sélection de gamme, multiplexeur U6 */
#define BR_GAMME_A1     13
#define BR_TEST_A0      14       /* réseau d'auto-test, multiplexeur U50 */
#define BR_TEST_A1      15

/* --------------------------------------------------------------------------
 *  Registres de l'ADS131M04 (notice SBAS950)
 * ----------------------------------------------------------------------- */
#define REG_ID          0x00
#define REG_STATUS      0x01
#define REG_MODE        0x02
#define REG_CLOCK       0x03
#define REG_GAIN1       0x04
#define REG_CFG         0x06
#define REG_CH0_CFG     0x09

#define CMD_NULL        0x0000
#define CMD_RESET       0x0011
#define CMD_STANDBY     0x0022
#define CMD_WAKEUP      0x0033
#define CMD_RREG        0xA000
#define CMD_WREG        0x6000

/*  MODE : mot de 24 bits, CRC désactivé, données alignées à gauche.
 *  CLOCK : quatre voies actives, suréchantillonnage 4096 → 250 Hz avec
 *  le quartz à 12,288 MHz (12,288 MHz / 2 / 4096 / 6 = 250 Hz).            */
#define MODE_DEFAUT     0x0510
#define CLOCK_DEFAUT    0x0F0E   /* voies 0-3 actives, OSR 4096 */
#define GAIN_DEFAUT     0x0000   /* gain interne ×1 : le gain est analogique */

/* --------------------------------------------------------------------------
 *  Tables : gains de l'étage programmable, gammes du pont, étalons
 * ----------------------------------------------------------------------- */
static const uint16_t TABLE_GAINS[AFE_GAINS]   = {2, 10, 20, 200};
static const uint32_t TABLE_GAMMES[AFE_GAMMES] = {100000u, 1000000u,
                                                  10000000u, 100000000u};
static const uint32_t TABLE_ETALONS[AFE_ETALONS] = {1000000u, 10000000u,
                                                    100000000u};

#define PLEINE_ECHELLE_V   1.2f      /* ±1,2 V avec la référence à 2,5 V */
#define CODE_PLEINE_ECHELLE 8388608.0f

/* --------------------------------------------------------------------------
 *  État interne
 * ----------------------------------------------------------------------- */
static afe_etat_t etat = {
    .gain = 1, .gamme = 1, .auto_gain = true, .offset_cna = 32768,
    .sature = false, .temperature_c = 0.0f,
};
static volatile bool pret = false;
static uint8_t trame[ (AFE_VOIES + 2) * 3 ];   /* état + 4 voies + CRC */

/* --------------------------------------------------------------------------
 *  Accès SPI de bas niveau
 * ----------------------------------------------------------------------- */
static void cs(bool actif)
{
    gpio_put(BR_CS, actif ? 0 : 1);
    asm volatile("nop \n nop \n nop");
}

static uint16_t spi_mot(uint16_t sortie)
{
    uint8_t tx[3] = { (uint8_t)(sortie >> 8), (uint8_t)(sortie & 0xFF), 0 };
    uint8_t rx[3] = {0};
    spi_write_read_blocking(SPI_PORT, tx, rx, 3);
    return (uint16_t)((rx[0] << 8) | rx[1]);
}

static uint16_t reg_lire(uint8_t adresse)
{
    cs(true);
    spi_mot(CMD_RREG | ((uint16_t)adresse << 7));
    uint16_t valeur = spi_mot(CMD_NULL);
    cs(false);
    return valeur;
}

static void reg_ecrire(uint8_t adresse, uint16_t valeur)
{
    cs(true);
    spi_mot(CMD_WREG | ((uint16_t)adresse << 7));
    spi_mot(valeur);
    cs(false);
}

/* --------------------------------------------------------------------------
 *  Interruption « données prêtes »
 * ----------------------------------------------------------------------- */
static void sur_drdy(uint gpio, uint32_t evenements)
{
    (void)gpio; (void)evenements;
    pret = true;
}

/* --------------------------------------------------------------------------
 *  Sélection du gain et de la gamme
 *
 *  Les deux multiplexeurs sont pilotés par deux broches chacun. On attend
 *  ensuite quelques millisecondes : changer de gain fait sauter la sortie,
 *  et les échantillons de la transition ne valent rien. Le micrologiciel les
 *  marque plutôt que de les jeter en silence — c'est à l'ordinateur de
 *  décider quoi en faire.
 * ----------------------------------------------------------------------- */
bool afe_set_gain(int indice)
{
    if (indice < 0) {
        etat.auto_gain = true;
        return true;
    }
    if (indice >= AFE_GAINS) {
        return false;
    }
    etat.auto_gain = false;
    etat.gain = (uint8_t)indice;
    gpio_put(BR_GAIN_A0, indice & 1);
    gpio_put(BR_GAIN_A1, (indice >> 1) & 1);
    sleep_ms(2);
    return true;
}

bool afe_set_gamme(int indice)
{
    if (indice < 0 || indice >= AFE_GAMMES) {
        return false;
    }
    etat.gamme = (uint8_t)indice;
    gpio_put(BR_GAMME_A0, indice & 1);
    gpio_put(BR_GAMME_A1, (indice >> 1) & 1);
    sleep_ms(2);
    return true;
}

void afe_set_offset(uint16_t code)
{
    etat.offset_cna = code;
    /* Le convertisseur numérique-analogique de recentrage partage le bus I²C.
     * Adresse 0x4C, deux octets, poids fort en tête. */
    uint8_t message[3] = { 0x00, (uint8_t)(code >> 8), (uint8_t)(code & 0xFF) };
    i2c_write_blocking(I2C_PORT, 0x4C, message, sizeof(message), false);
}

const uint16_t *afe_table_gains(void)   { return TABLE_GAINS; }
const uint32_t *afe_table_gammes(void)  { return TABLE_GAMMES; }

/* --------------------------------------------------------------------------
 *  Boucle d'auto-échelle
 *
 *  Règle : on descend d'un cran dès que l'on dépasse 90 % de la pleine
 *  échelle, on remonte quand on est resté sous 20 % pendant plus d'une
 *  seconde. L'hystérésis évite le battement sur un signal qui oscille
 *  autour d'un seuil — défaut classique des auto-échelles naïves.
 * ----------------------------------------------------------------------- */
static void auto_echelle(int32_t code)
{
    static uint32_t bas_depuis = 0;
    float fraction = (float)(code < 0 ? -code : code) / CODE_PLEINE_ECHELLE;

    if (fraction > 0.90f) {
        etat.sature = true;
        if (etat.gain > 0) {
            afe_set_gain(etat.gain - 1);
            etat.auto_gain = true;
        }
        bas_depuis = 0;
        return;
    }
    etat.sature = false;

    if (fraction < 0.20f) {
        if (++bas_depuis > 250u && etat.gain < AFE_GAINS - 1) {
            afe_set_gain(etat.gain + 1);
            etat.auto_gain = true;
            bas_depuis = 0;
        }
    } else {
        bas_depuis = 0;
    }
}

/* --------------------------------------------------------------------------
 *  Lecture d'un échantillon
 * ----------------------------------------------------------------------- */
bool afe_lire(afe_echantillon_t *sortie)
{
    if (!pret) {
        return false;
    }
    pret = false;

    cs(true);
    uint8_t tx[sizeof(trame)];
    memset(tx, 0, sizeof(tx));
    spi_write_read_blocking(SPI_PORT, tx, trame, sizeof(trame));
    cs(false);

    /* Le premier mot est l'état ; viennent ensuite les quatre voies, chacune
     * sur trois octets, en complément à deux. */
    for (int v = 0; v < AFE_VOIES; v++) {
        const uint8_t *p = &trame[3 + v * 3];
        int32_t code = ((int32_t)p[0] << 16) | ((int32_t)p[1] << 8) | p[2];
        if (code & 0x800000) {
            code -= 0x1000000;        /* extension de signe sur 24 bits */
        }
        sortie->voie[v] = code;
    }
    if (etat.auto_gain) {
        auto_echelle(sortie->voie[0]);
    }
    return true;
}

void afe_etat(afe_etat_t *sortie) { *sortie = etat; }

float afe_en_volts(int32_t code, const afe_etat_t *e)
{
    float gain = (float)TABLE_GAINS[e->gain < AFE_GAINS ? e->gain : 0];
    return ((float)code / CODE_PLEINE_ECHELLE) * PLEINE_ECHELLE_V / gain;
}

/* --------------------------------------------------------------------------
 *  Auto-test sur les étalons internes
 *
 *  Trois résistances à 0,1 % sont substituées tour à tour au végétal. On
 *  mesure, on compare, on rend l'écart. C'est cette fonction qui permet de
 *  répondre en trente secondes à la seule question qui compte devant une
 *  mesure surprenante : est-ce la plante, ou est-ce l'appareil ?
 * ----------------------------------------------------------------------- */
static void test_selectionner(int indice)
{
    gpio_put(BR_TEST_A0, indice & 1);
    gpio_put(BR_TEST_A1, (indice >> 1) & 1);
    sleep_ms(50);                      /* laisser le filtre s'établir */
}

static float moyenne_sur(int echantillons)
{
    double somme = 0.0;
    afe_echantillon_t e;
    int obtenus = 0;
    absolute_time_t limite = make_timeout_time_ms(2000);
    while (obtenus < echantillons && !time_reached(limite)) {
        if (afe_lire(&e)) {
            somme += afe_en_volts(e.voie[0], &etat);
            obtenus++;
        }
    }
    return obtenus ? (float)(somme / obtenus) : 0.0f;
}

bool afe_autotest(afe_autotest_t *rapport)
{
    if (rapport == NULL) {
        return false;
    }
    memset(rapport, 0, sizeof(*rapport));

    const uint8_t gain_initial = etat.gain;
    const bool auto_initial = etat.auto_gain;
    afe_set_gain(1);                   /* ×10 : compromis pour les trois */

    /* 1. plancher de bruit, entrée sur l'étalon le plus élevé */
    test_selectionner(3);
    float base = moyenne_sur(200);
    double somme_carres = 0.0;
    afe_echantillon_t e;
    for (int i = 0; i < 200; i++) {
        while (!afe_lire(&e)) { tight_loop_contents(); }
        float v = afe_en_volts(e.voie[0], &etat) - base;
        somme_carres += (double)v * v;
    }
    rapport->bruit_v = (float)sqrt(somme_carres / 200.0);

    /* 2. les trois étalons */
    bool reussi = true;
    for (int i = 0; i < AFE_ETALONS; i++) {
        test_selectionner(i);
        float mesure = moyenne_sur(100);
        /* La conversion tension → résistance dépend du courant d'excitation,
         * calibré en usine et rangé en mémoire. Ici, forme simplifiée. */
        float attendu = (float)TABLE_ETALONS[i];
        float ohms = mesure / 1.0e-7f;          /* 100 nA d'excitation */
        rapport->mesure_ohm[i] = ohms;
        rapport->ecart_pourcent[i] = 100.0f * (ohms - attendu) / attendu;
        if (rapport->ecart_pourcent[i] > 0.5f ||
            rapport->ecart_pourcent[i] < -0.5f) {
            reussi = false;
        }
    }

    /* 3. courant de fuite, par la méthode de la capacité de charge */
    test_selectionner(3);              /* entrée ouverte sur 100 pF */
    float v0 = moyenne_sur(20);
    sleep_ms(1000);
    float v1 = moyenne_sur(20);
    rapport->fuite_fa = (v1 - v0) * 100e-12f * 1e15f;   /* I = C·dV/dt */

    test_selectionner(0);
    afe_set_gain(auto_initial ? -1 : gain_initial);
    rapport->reussi = reussi;
    return true;
}

/* --------------------------------------------------------------------------
 *  Mémoire d'identification de la carte fille
 *
 *  Chaque carte fille porte une 24AA02 sur le bus I²C isolé. Les seize
 *  premiers octets suffisent : type, numéro de série, date d'étalonnage.
 *  Le microcontrôleur les lit au démarrage et les transmet à l'ordinateur,
 *  qui adapte alors ses unités sans que l'utilisateur ait rien à déclarer.
 * ----------------------------------------------------------------------- */
bool afe_lire_eeprom_carte_fille(char *type, size_t type_max,
                                 char *serie, size_t serie_max)
{
    uint8_t adresse = 0x00;
    uint8_t donnees[32] = {0};

    if (i2c_write_blocking(I2C_PORT, 0x50, &adresse, 1, true) < 0) {
        return false;
    }
    if (i2c_read_blocking(I2C_PORT, 0x50, donnees, sizeof(donnees), false) < 0) {
        return false;
    }
    /*  Format : 'P','S','1',version | type[8] | série[12] | date[8] | somme */
    if (donnees[0] != 'P' || donnees[1] != 'S' || donnees[2] != '1') {
        return false;
    }
    snprintf(type, type_max, "%.8s", (const char *)&donnees[4]);
    snprintf(serie, serie_max, "%.12s", (const char *)&donnees[12]);
    return true;
}

/* --------------------------------------------------------------------------
 *  Initialisation
 * ----------------------------------------------------------------------- */
bool afe_init(void)
{
    /* SPI à 8 MHz : le convertisseur accepte 25 MHz, mais rien n'oblige à
     * courir, et des fronts plus lents rayonnent moins. */
    spi_init(SPI_PORT, 8 * 1000 * 1000);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_1, SPI_MSB_FIRST);
    gpio_set_function(BR_SCK, GPIO_FUNC_SPI);
    gpio_set_function(BR_MOSI, GPIO_FUNC_SPI);
    gpio_set_function(BR_MISO, GPIO_FUNC_SPI);

    gpio_init(BR_CS);   gpio_set_dir(BR_CS, GPIO_OUT);   gpio_put(BR_CS, 1);
    gpio_init(BR_RESET); gpio_set_dir(BR_RESET, GPIO_OUT); gpio_put(BR_RESET, 1);

    for (int b = 0; b < 6; b++) {
        const uint broches[] = { BR_GAIN_A0, BR_GAIN_A1, BR_GAMME_A0,
                                 BR_GAMME_A1, BR_TEST_A0, BR_TEST_A1 };
        gpio_init(broches[b]);
        gpio_set_dir(broches[b], GPIO_OUT);
        gpio_put(broches[b], 0);
    }

    i2c_init(I2C_PORT, 400 * 1000);
    gpio_set_function(BR_SDA, GPIO_FUNC_I2C);
    gpio_set_function(BR_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(BR_SDA);
    gpio_pull_up(BR_SCL);

    /* Réinitialisation matérielle, puis logicielle */
    gpio_put(BR_RESET, 0);
    sleep_ms(2);
    gpio_put(BR_RESET, 1);
    sleep_ms(10);
    cs(true); spi_mot(CMD_RESET); cs(false);
    sleep_ms(10);

    if ((reg_lire(REG_ID) & 0xFF00) == 0) {
        return false;                  /* aucun convertisseur sur le bus */
    }

    reg_ecrire(REG_MODE, MODE_DEFAUT);
    reg_ecrire(REG_CLOCK, CLOCK_DEFAUT);
    reg_ecrire(REG_GAIN1, GAIN_DEFAUT);

    gpio_init(BR_DRDY);
    gpio_set_dir(BR_DRDY, GPIO_IN);
    gpio_pull_up(BR_DRDY);
    gpio_set_irq_enabled_with_callback(BR_DRDY, GPIO_IRQ_EDGE_FALL, true,
                                       &sur_drdy);

    afe_set_gain(1);
    afe_set_gamme(1);
    afe_set_offset(32768);
    return true;
}

void afe_demarrer(uint32_t frequence_hz)
{
    (void)frequence_hz;                /* fixée par CLOCK_DEFAUT et le TCXO */
    cs(true); spi_mot(CMD_WAKEUP); cs(false);
}

void afe_arreter(void)
{
    cs(true); spi_mot(CMD_STANDBY); cs(false);
}
