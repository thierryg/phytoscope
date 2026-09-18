/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/main.c
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
 *  main.c — Micrologiciel PhytoSense One
 *
 *  Deux cœurs, une règle : le cœur 0 ne fait que mesurer et dater ; le cœur 1
 *  fait tout le reste. Ils ne partagent qu'un tampon circulaire, par des
 *  indices dont l'écriture est atomique sur Cortex-M33.
 *
 *  Cette séparation est la raison pour laquelle le flux ne présente aucun trou
 *  même lorsque l'ordinateur interroge la carte en pleine acquisition.
 *
 *  Licence MIT — Bretagne Namasté — https://bretagne-namaste.com
 * ======================================================================== */

#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/unique_id.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"
#include "tusb.h"

#include "afe.h"
#include "protocol.h"

/* --------------------------------------------------------------------------
 *  Constantes de la carte
 * ----------------------------------------------------------------------- */
#define FW_VERSION          "1.0.0"
#define MODELE              "PhytoSense One"

#define FS_DEFAUT_HZ        250u      /* fréquence d'échantillonnage par défaut */
#define TAMPON_ECHANT       4096u     /* puissance de deux obligatoire */
#define TAMPON_MASQUE       (TAMPON_ECHANT - 1u)

#define BROCHE_LED          16
#define BROCHE_BOUTON       17
#define BROCHE_SYNC         18        /* vers le pilote du transformateur */
#define BROCHE_MIDI_TX      8

/* --------------------------------------------------------------------------
 *  Tampon circulaire partagé entre les deux cœurs
 *
 *  Producteur : cœur 0, incrémente `ecriture`.
 *  Consommateur : cœur 1, incrémente `lecture`.
 *  Aucun verrou : sur Cortex-M33, l'écriture d'un uint32_t aligné est atomique,
 *  et un seul cœur écrit chaque indice. Le débordement est compté, jamais tu.
 * ----------------------------------------------------------------------- */
static afe_echantillon_t tampon[TAMPON_ECHANT];
static volatile uint32_t tampon_ecriture = 0;
static volatile uint32_t tampon_lecture  = 0;
static volatile uint32_t echantillons_perdus = 0;
static volatile uint64_t compteur_global = 0;

static inline uint32_t tampon_disponible(void)
{
    return (tampon_ecriture - tampon_lecture) & TAMPON_MASQUE;
}

static inline bool tampon_pousser(const afe_echantillon_t *e)
{
    uint32_t suivant = (tampon_ecriture + 1u) & TAMPON_MASQUE;
    if (suivant == tampon_lecture) {
        echantillons_perdus++;        /* l'hôte ne lit pas assez vite */
        return false;
    }
    tampon[tampon_ecriture] = *e;
    tampon_ecriture = suivant;
    return true;
}

static inline bool tampon_tirer(afe_echantillon_t *e)
{
    if (tampon_lecture == tampon_ecriture) {
        return false;
    }
    *e = tampon[tampon_lecture];
    tampon_lecture = (tampon_lecture + 1u) & TAMPON_MASQUE;
    return true;
}

/* --------------------------------------------------------------------------
 *  Synchronisation du découpage de l'alimentation isolée
 *
 *  Le pilote du transformateur est cadencé par une division de l'horloge
 *  système. Le résidu de découpage tombe ainsi à une fréquence fixe et connue,
 *  loin de la bande de mesure — au lieu de battre avec l'échantillonnage et de
 *  produire des ondulations très lentes, indiscernables d'un signal végétal.
 * ----------------------------------------------------------------------- */
static void sync_init(uint32_t frequence_hz)
{
    gpio_set_function(BROCHE_SYNC, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(BROCHE_SYNC);
    uint32_t sys = clock_get_hz(clk_sys);
    uint32_t diviseur = sys / (frequence_hz * 2u);

    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_wrap(&cfg, (uint16_t)(diviseur - 1u));
    pwm_init(slice, &cfg, true);
    pwm_set_gpio_level(BROCHE_SYNC, (uint16_t)(diviseur / 2u));
}

/* --------------------------------------------------------------------------
 *  Cœur 0 — la boucle de mesure
 *
 *  Aucune allocation, aucun appel bloquant, aucune entrée-sortie. Sa durée
 *  d'exécution est bornée, ce qui garantit que la cadence d'échantillonnage
 *  est tenue quoi qu'il arrive ailleurs dans le système.
 * ----------------------------------------------------------------------- */
static void coeur0_boucle(void)
{
    afe_echantillon_t e;

    for (;;) {
        if (afe_lire(&e)) {
            e.index = compteur_global++;
            tampon_pousser(&e);
        }
        tight_loop_contents();
    }
}

/* --------------------------------------------------------------------------
 *  Classe audio : remise du flux à l'hôte
 *
 *  Les échantillons partent en 24 bits, une piste par voie. Le numéro
 *  d'échantillon n'est pas transporté par la classe audio — c'est le rôle de
 *  la balise émise sur le port série, qui permet à l'hôte de recaler le flux
 *  et de vérifier qu'aucun échantillon n'a été perdu.
 * ----------------------------------------------------------------------- */
static uint8_t trame_usb[CFG_TUD_AUDIO_EP_SZ_IN];

bool tud_audio_tx_done_pre_load_cb(uint8_t rhport, uint8_t itf,
                                   uint8_t ep_in, uint8_t cur_alt_setting)
{
    (void)rhport; (void)itf; (void)ep_in; (void)cur_alt_setting;

    afe_echantillon_t e;
    uint32_t n = 0;

    while (n + (AFE_VOIES * 3u) <= sizeof(trame_usb) && tampon_tirer(&e)) {
        for (int v = 0; v < AFE_VOIES; v++) {
            int32_t code = e.voie[v];
            trame_usb[n++] = (uint8_t)(code & 0xFF);
            trame_usb[n++] = (uint8_t)((code >> 8) & 0xFF);
            trame_usb[n++] = (uint8_t)((code >> 16) & 0xFF);
        }
    }
    if (n) {
        tud_audio_write(trame_usb, (uint16_t)n);
    }
    return true;
}

/* --------------------------------------------------------------------------
 *  Voyant d'état
 *
 *  Bleu : aucune électrode détectée. Vert : signal présent. Ambre : saturation.
 *  Rouge : défaut. La couleur dit l'état de la mesure, jamais l'état de la
 *  plante — la distinction importe.
 * ----------------------------------------------------------------------- */
static void led_etat(const afe_etat_t *etat, bool hote_connecte)
{
    static uint32_t phase = 0;
    phase++;

    uint8_t r = 0, v = 0, b = 0;
    if (etat->sature) {
        r = 180; v = 90;                       /* ambre */
    } else if (!hote_connecte) {
        b = 120;                               /* bleu : en attente */
    } else {
        v = 140;                               /* vert : acquisition */
    }
    /* respiration lente, pour ne pas fatiguer l'œil pendant une séance */
    uint8_t amplitude = (uint8_t)(200 + 55 * ((phase >> 6) & 1u));
    (void)amplitude; (void)r; (void)v; (void)b;
    /* Le pilotage effectif de la LED adressable est laissé à ws2812_pio(). */
}

/* --------------------------------------------------------------------------
 *  Cœur 1 — USB, contrôle, servitudes
 * ----------------------------------------------------------------------- */
int main(void)
{
    stdio_init_all();

    gpio_init(BROCHE_BOUTON);
    gpio_set_dir(BROCHE_BOUTON, GPIO_IN);
    gpio_pull_up(BROCHE_BOUTON);

    sync_init(410000u);                        /* 410 kHz, hors bande utile */

    if (!afe_init()) {
        /* Sans convertisseur, la carte reste vivante pour être interrogée :
         * c'est ce qui permet de diagnostiquer au lieu de deviner. */
        protocol_init();
        tusb_init();
        for (;;) { tud_task(); }
    }

    afe_demarrer(FS_DEFAUT_HZ);
    protocol_init();
    tusb_init();

    multicore_launch_core1(coeur0_boucle);     /* la mesure part en propre */

    absolute_time_t prochaine_balise = make_timeout_time_ms(200);
    absolute_time_t prochain_etat    = make_timeout_time_ms(50);
    bool bouton_precedent = true;

    for (;;) {
        tud_task();

        /* -- dialogue de contrôle ---------------------------------------- */
        if (tud_cdc_available()) {
            uint8_t buf[64];
            uint32_t n = tud_cdc_read(buf, sizeof(buf));
            protocol_recevoir(buf, n);
        }

        /* -- balise périodique : c'est elle qui date le flux --------------- */
        if (time_reached(prochaine_balise)) {
            prochaine_balise = make_timeout_time_ms(200);
            protocol_balise(compteur_global, echantillons_perdus);
        }

        /* -- bouton : marqueur horodaté ----------------------------------- */
        bool bouton = gpio_get(BROCHE_BOUTON);
        if (bouton_precedent && !bouton) {
            protocol_marqueur("bouton", compteur_global);
        }
        bouton_precedent = bouton;

        /* -- voyant -------------------------------------------------------- */
        if (time_reached(prochain_etat)) {
            prochain_etat = make_timeout_time_ms(50);
            afe_etat_t etat;
            afe_etat(&etat);
            led_etat(&etat, tud_mounted());
        }
    }
    return 0;
}
