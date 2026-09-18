/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/usb_descriptors.c
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
 *  usb_descriptors.c — identité USB de la carte PhytoSense One.
 *
 *  La carte se présente comme un périphérique composite :
 *
 *    · interface 0-1 : entrée audio en classe 2 (UAC2), quatre voies 24 bits.
 *                      C'est le flux de mesure. Aucun pilote n'est requis :
 *                      Windows 10, macOS et Linux savent tous lire une entrée
 *                      audio normalisée.
 *    · interface 2-3 : port série virtuel (CDC-ACM). C'est le dialogue de
 *                      contrôle, décrit dans protocol.c.
 *
 *  Le choix d'UAC2 plutôt qu'un protocole propriétaire n'est pas un détail de
 *  confort : il garantit que la carte restera lisible dans dix ans, par
 *  n'importe quel logiciel, même si celui qui l'accompagne a disparu.
 *
 *  Le numéro de série n'est pas inventé : il est dérivé de l'identifiant unique
 *  gravé dans la flash QSPI, donc propre à chaque exemplaire et stable pour
 *  toute sa vie. C'est lui que PhytoScope inscrit dans l'en-tête des
 *  enregistrements.
 *
 *  Licence MIT — Bretagne Namasté — https://bretagne-namaste.com
 * ------------------------------------------------------------------------ */
#include "tusb.h"
#include "pico/unique_id.h"

#include <string.h>

/* ---------------------------------------------------------------------------
 *  Identifiants
 *
 *  Le couple VID/PID ci-dessous appartient à la plage libre de pid.codes,
 *  réservée aux projets matériels ouverts. Il ne doit PAS être utilisé pour un
 *  produit commercialisé : dans ce cas, obtenir un identifiant propre auprès de
 *  l'USB-IF, ou une sous-allocation auprès d'un fournisseur.
 *
 *  Ce couple est également celui que la routine de diagnostic de PhytoScope
 *  recherche pour reconnaître la carte (voir usb/diagnostic.py).
 * ------------------------------------------------------------------------ */
#define PHYTO_VID   0x1209      /* pid.codes — projets ouverts               */
#define PHYTO_PID   0x7A01      /* PhytoSense One                            */
#define PHYTO_BCD   0x0100      /* version 1.0.0 du micrologiciel            */

/* ---------------------------------------------------------------------------
 *  Points de terminaison
 *
 *  Numérotés à la main pour que la carte des adresses reste lisible dans les
 *  captures Wireshark, et identique d'une version à l'autre.
 * ------------------------------------------------------------------------ */
#define EP_AUDIO_IN     0x81    /* flux de mesure vers l'hôte, isochrone     */
#define EP_CDC_NOTIF    0x82    /* notifications du port série               */
#define EP_CDC_OUT      0x03    /* commandes reçues                          */
#define EP_CDC_IN       0x83    /* réponses émises                           */

/* Taille de la trame audio : 4 voies × 3 octets × marge pour les cadences
 * élevées. Doit rester alignée sur CFG_TUD_AUDIO_EP_SZ_IN.                  */
#define EP_AUDIO_SZ     CFG_TUD_AUDIO_EP_SZ_IN

/* ---------------------------------------------------------------------------
 *  Descripteur de périphérique
 * ------------------------------------------------------------------------ */
static const tusb_desc_device_t desc_device = {
    .bLength            = sizeof(tusb_desc_device_t),
    .bDescriptorType    = TUSB_DESC_DEVICE,
    .bcdUSB             = 0x0200,

    /* Composite : la classe est déclarée par interface, pas globalement.
     * IAD (Interface Association Descriptor) regroupe ensuite les interfaces
     * qui vont ensemble. Sans ces trois valeurs exactes, Windows refuse de
     * charger le pilote CDC de la partie contrôle.                          */
    .bDeviceClass       = TUSB_CLASS_MISC,
    .bDeviceSubClass    = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol    = MISC_PROTOCOL_IAD,

    .bMaxPacketSize0    = CFG_TUD_ENDPOINT0_SIZE,

    .idVendor           = PHYTO_VID,
    .idProduct          = PHYTO_PID,
    .bcdDevice          = PHYTO_BCD,

    .iManufacturer      = 0x01,
    .iProduct           = 0x02,
    .iSerialNumber      = 0x03,

    .bNumConfigurations = 0x01
};

const uint8_t *tud_descriptor_device_cb(void)
{
    return (const uint8_t *) &desc_device;
}

/* ---------------------------------------------------------------------------
 *  Descripteur de configuration
 *
 *  L'ordre compte : l'audio d'abord, parce que c'est la fonction principale et
 *  que certains hôtes anciens n'explorent pas au-delà de la première interface
 *  qu'ils savent traiter.
 * ------------------------------------------------------------------------ */
enum {
    ITF_NUM_AUDIO_CONTROL = 0,
    ITF_NUM_AUDIO_STREAM,
    ITF_NUM_CDC_CONTROL,
    ITF_NUM_CDC_DATA,
    ITF_NUM_TOTAL
};

#define CONFIG_TOTAL_LEN  (TUD_CONFIG_DESC_LEN                \
                         + TUD_AUDIO_MIC_FOUR_CH_DESC_LEN     \
                         + TUD_CDC_DESC_LEN)

static const uint8_t desc_configuration[] = {
    /* Configuration : 4 interfaces, alimentée par le bus, 500 mA.
     * La carte consomme typiquement 180 mA ; la marge couvre l'appel de
     * courant à l'établissement des alimentations isolées.                  */
    TUD_CONFIG_DESCRIPTOR(1, ITF_NUM_TOTAL, 0, CONFIG_TOTAL_LEN,
                          TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP, 500),

    /* Entrée audio quatre voies, 24 bits utiles sur 3 octets.              */
    TUD_AUDIO_MIC_FOUR_CH_DESCRIPTOR(ITF_NUM_AUDIO_CONTROL, /* str */ 4,
                                     /* nBytesPerSample     */ 3,
                                     /* nBitsUsedPerSample  */ 24,
                                     EP_AUDIO_IN, EP_AUDIO_SZ),

    /* Port série virtuel de contrôle.                                       */
    TUD_CDC_DESCRIPTOR(ITF_NUM_CDC_CONTROL, /* str */ 5,
                       EP_CDC_NOTIF, 8, EP_CDC_OUT, EP_CDC_IN, 64),
};

const uint8_t *tud_descriptor_configuration_cb(uint8_t index)
{
    (void) index;   /* une seule configuration */
    return desc_configuration;
}

/* ---------------------------------------------------------------------------
 *  Chaînes de caractères
 *
 *  Le numéro de série est construit une seule fois, au premier appel, à partir
 *  de l'identifiant 64 bits de la flash. Il prend la forme PS1-XXXXXXXX, où
 *  les huit chiffres hexadécimaux sont les 32 bits de poids faible de cet
 *  identifiant — assez pour être unique dans toute série raisonnable, assez
 *  court pour être recopié à la main sur un cahier de laboratoire.
 * ------------------------------------------------------------------------ */
static char serial_str[13];     /* "PS1-4A17C302" + terminateur             */

static void construire_serial(void)
{
    if (serial_str[0] != '\0') {
        return;                 /* déjà fait */
    }

    pico_unique_board_id_t uid;
    pico_get_unique_board_id(&uid);

    /* Les quatre derniers octets, en hexadécimal majuscule. */
    static const char hex[] = "0123456789ABCDEF";
    serial_str[0] = 'P';
    serial_str[1] = 'S';
    serial_str[2] = '1';
    serial_str[3] = '-';
    for (int i = 0; i < 4; i++) {
        uint8_t octet = uid.id[PICO_UNIQUE_BOARD_ID_SIZE_BYTES - 4 + i];
        serial_str[4 + i * 2]     = hex[(octet >> 4) & 0x0F];
        serial_str[4 + i * 2 + 1] = hex[octet & 0x0F];
    }
    serial_str[12] = '\0';
}

static const char *const chaines[] = {
    (const char[]) { 0x09, 0x04 },      /* 0 : anglais (en-US)              */
    "Bretagne Namaste",                 /* 1 : fabricant                    */
    "PhytoSense One",                   /* 2 : produit                      */
    serial_str,                         /* 3 : numéro de série (construit)  */
    "PhytoSense Measurement Input",     /* 4 : flux audio                   */
    "PhytoSense Control",               /* 5 : port de contrôle             */
};

/* Tampon de conversion vers l'UTF-16 attendu par USB. Le premier mot porte la
 * longueur et le type ; viennent ensuite les caractères.                    */
static uint16_t desc_str[32];

const uint16_t *tud_descriptor_string_cb(uint8_t index, uint16_t langid)
{
    (void) langid;

    size_t n;

    if (index == 0) {
        /* Table des langues : deux octets bruts, pas de conversion. */
        memcpy(&desc_str[1], chaines[0], 2);
        n = 1;
    } else {
        if (index >= TU_ARRAY_SIZE(chaines)) {
            return NULL;
        }

        if (index == 3) {
            construire_serial();
        }

        const char *src = chaines[index];
        n = strlen(src);

        /* On tronque plutôt que de déborder : un nom coupé vaut mieux qu'une
         * pile écrasée. La limite de 31 caractères n'a jamais été atteinte
         * par les chaînes ci-dessus, mais elle protège des ajouts futurs.  */
        if (n > TU_ARRAY_SIZE(desc_str) - 1) {
            n = TU_ARRAY_SIZE(desc_str) - 1;
        }

        for (size_t i = 0; i < n; i++) {
            desc_str[1 + i] = (uint16_t) src[i];
        }
    }

    /* Longueur totale en octets, puis type de descripteur. */
    desc_str[0] = (uint16_t) ((TUSB_DESC_STRING << 8) | (2 * n + 2));

    return desc_str;
}
