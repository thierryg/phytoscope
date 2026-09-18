/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/tusb_config.h
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
 *  tusb_config.h — configuration de la pile USB TinyUSB.
 *
 *  La carte se présente comme un périphérique composite : une entrée audio
 *  en classe 2 (le flux de mesure), un port série virtuel (le contrôle) et
 *  l'interface de mise à jour. Aucun pilote n'est nécessaire sur les systèmes
 *  courants depuis Windows 10, macOS 10.6 et n'importe quel noyau Linux
 *  récent.
 *
 *  Licence MIT — Bretagne Namasté
 * ------------------------------------------------------------------------ */
#ifndef _TUSB_CONFIG_H_
#define _TUSB_CONFIG_H_

/* RP2350 : TinyUSB le traite par le portage « rp2040 », commun aux deux
 * puces. Cette constante ne désigne pas le silicium mais la famille de
 * contrôleurs USB, identique sur RP2040 et RP2350.                        */
#define CFG_TUSB_MCU                OPT_MCU_RP2040
#define CFG_TUSB_OS                 OPT_OS_PICO
#define CFG_TUSB_RHPORT0_MODE       OPT_MODE_DEVICE

#define CFG_TUD_ENDPOINT0_SIZE      64

/* --- interfaces activées ------------------------------------------------- */
#define CFG_TUD_AUDIO               1
#define CFG_TUD_CDC                 1
#define CFG_TUD_MSC                 0
#define CFG_TUD_HID                 0
#define CFG_TUD_MIDI                0
#define CFG_TUD_VENDOR              0

/* --- port série virtuel -------------------------------------------------- */
#define CFG_TUD_CDC_RX_BUFSIZE      256
#define CFG_TUD_CDC_TX_BUFSIZE      512

/* --- flux audio ----------------------------------------------------------
 *  Quatre voies en 24 bits à 250 Hz font 3 ko/s : une trame d'une
 *  milliseconde transporte donc 1 échantillon par voie, soit 12 octets. On
 *  dimensionne large (256 octets) pour absorber les modes à 1 kHz et 32 kHz
 *  sans reconfigurer la pile.
 * ------------------------------------------------------------------------ */
#define CFG_TUD_AUDIO_FUNC_1_DESC_LEN               TUD_AUDIO_MIC_FOUR_CH_DESC_LEN
#define CFG_TUD_AUDIO_FUNC_1_N_AS_INT               1
#define CFG_TUD_AUDIO_FUNC_1_CTRL_BUF_SZ            64

#define CFG_TUD_AUDIO_ENABLE_EP_IN                  1
#define CFG_TUD_AUDIO_FUNC_1_N_BYTES_PER_SAMPLE_TX  3
#define CFG_TUD_AUDIO_FUNC_1_N_CHANNELS_TX          4
#define CFG_TUD_AUDIO_EP_SZ_IN                      256
#define CFG_TUD_AUDIO_FUNC_1_EP_IN_SZ_MAX           CFG_TUD_AUDIO_EP_SZ_IN
#define CFG_TUD_AUDIO_FUNC_1_EP_IN_SW_BUF_SZ        (CFG_TUD_AUDIO_EP_SZ_IN * 4)

/*  Horloge asynchrone : c'est la carte qui impose sa cadence, pas l'hôte.
 *  Sans cela, le système d'exploitation rééchantillonnerait le flux, et la
 *  base de temps de tout l'instrument perdrait son sens.                    */
#define CFG_TUD_AUDIO_ENABLE_FEEDBACK_EP            0
#define CFG_TUD_AUDIO_FUNC_1_CLK_SRC_ASYNC          1

#endif /* _TUSB_CONFIG_H_ */
