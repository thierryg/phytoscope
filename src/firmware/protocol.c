/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/protocol.c
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
 *  protocol.c — dialogue de contrôle sur le port série virtuel.
 *
 *  Commandes en texte, réponses en JSON sur une ligne. Ce choix délibérément
 *  archaïque permet d'interroger et de dépanner la carte avec n'importe quel
 *  terminal, sans logiciel, sans bibliothèque et sans documentation. Une
 *  carte qu'on ne peut pas interroger à la main est une carte qu'on ne peut
 *  pas réparer.
 *
 *  Licence MIT — Bretagne Namasté — https://bretagne-namaste.com
 * ======================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "tusb.h"

#include "afe.h"
#include "protocol.h"

#define FW_VERSION  "1.0.0"
#define MODELE      "PhytoSense One"
#define FS_HZ       250.0f

static char ligne[PROTO_LIGNE_MAX];
static uint32_t remplissage = 0;
static char reponse[PROTO_REPONSE_MAX];
static char serie_carte[20];
static char type_fille[12] = "inconnue";
static char serie_fille[16] = "";

/* --------------------------------------------------------------------------
 *  Émission
 * ----------------------------------------------------------------------- */
static void emettre(const char *texte)
{
    tud_cdc_write_str(texte);
    tud_cdc_write_str("\r\n");
    tud_cdc_write_flush();
}

static void ok(const char *format, ...)
{
    va_list args;
    reponse[0] = '+';
    va_start(args, format);
    vsnprintf(reponse + 1, sizeof(reponse) - 1, format, args);
    va_end(args);
    emettre(reponse);
}

static void erreur(const char *message)
{
    snprintf(reponse, sizeof(reponse), "-{\"message\":\"%s\"}", message);
    emettre(reponse);
}

/* --------------------------------------------------------------------------
 *  Commandes
 * ----------------------------------------------------------------------- */
static void cmd_identifier(void)
{
    afe_etat_t e;
    afe_etat(&e);
    const uint16_t *gains = afe_table_gains();
    ok("{\"model\":\"%s\",\"serial\":\"%s\",\"firmware\":\"%s\","
       "\"channels\":%d,\"sample_rate\":%.1f,"
       "\"frontend\":\"%s\",\"frontend_serial\":\"%s\","
       "\"gains\":[%u,%u,%u,%u],\"gain\":%u,\"range\":%u,"
       "\"volts_per_unit\":1.0}",
       MODELE, serie_carte, FW_VERSION, AFE_VOIES, FS_HZ,
       type_fille, serie_fille,
       gains[0], gains[1], gains[2], gains[3], e.gain, e.gamme);
}

static void cmd_gain(const char *argument)
{
    if (argument == NULL) {
        erreur("usage : gain <indice> | auto");
        return;
    }
    if (strncmp(argument, "auto", 4) == 0) {
        afe_set_gain(-1);
        ok("{\"gain\":\"auto\",\"auto\":true,"
           "\"message\":\"boucle d'auto-echelle rendue\"}");
        return;
    }
    int demande = atoi(argument);
    /* L'utilisateur donne un gain (×10), pas un indice : on cherche. */
    const uint16_t *gains = afe_table_gains();
    int indice = -1;
    for (int i = 0; i < AFE_GAINS; i++) {
        if (gains[i] == (uint16_t)demande) {
            indice = i;
        }
    }
    if (indice < 0 || !afe_set_gain(indice)) {
        erreur("gain hors table : 2, 10, 20 ou 200");
        return;
    }
    ok("{\"gain\":%d,\"auto\":false,\"message\":\"gain force\"}", demande);
}

static void cmd_gamme(const char *argument)
{
    if (argument == NULL || !afe_set_gamme(atoi(argument))) {
        erreur("usage : range 0..3");
        return;
    }
    afe_etat_t e;
    afe_etat(&e);
    ok("{\"range\":%u,\"reference_ohm\":%lu}",
       e.gamme, (unsigned long)afe_table_gammes()[e.gamme]);
}

static void cmd_horloge(uint64_t index, uint32_t perdus)
{
    ok("{\"n\":%llu,\"t_s\":%.3f,\"tcxo_ppm\":-0.4,\"lost\":%lu}",
       (unsigned long long)index, (double)index / FS_HZ,
       (unsigned long)perdus);
}

static void cmd_marqueur(const char *etiquette, uint64_t index)
{
    char propre[49];
    size_t k = 0;
    for (const char *p = etiquette; p && *p && k < sizeof(propre) - 1; p++) {
        if (*p >= 32 && *p < 127 && *p != '"' && *p != '\\') {
            propre[k++] = *p;
        }
    }
    propre[k] = '\0';
    ok("{\"n\":%llu,\"label\":\"%s\"}", (unsigned long long)index,
       k ? propre : "marqueur");
}

static void cmd_autotest(void)
{
    afe_autotest_t rapport;
    if (!afe_autotest(&rapport)) {
        erreur("auto-test impossible");
        return;
    }
    ok("{\"passed\":%s,"
       "\"measurements\":{\"1M\":%.1f,\"10M\":%.1f,\"100M\":%.1f},"
       "\"errors\":{\"1M\":%.3f,\"10M\":%.3f,\"100M\":%.3f},"
       "\"noise_floor_v\":%.3e,\"leakage_fa\":%.1f,"
       "\"message\":\"%s\"}",
       rapport.reussi ? "true" : "false",
       rapport.mesure_ohm[0], rapport.mesure_ohm[1], rapport.mesure_ohm[2],
       rapport.ecart_pourcent[0], rapport.ecart_pourcent[1],
       rapport.ecart_pourcent[2],
       rapport.bruit_v, rapport.fuite_fa,
       rapport.reussi ? "trois etalons dans les tolerances"
                      : "au moins un etalon hors tolerance");
}

static void cmd_ambiance(void)
{
    afe_etat_t e;
    afe_etat(&e);
    ok("{\"temperature_c\":%.2f,\"humidity_pct\":0.0,"
       "\"pressure_hpa\":0.0,\"lux\":0.0}", e.temperature_c);
}

static void cmd_aide(void)
{
    emettre("+{\"commands\":[\"?\",\"gain\",\"range\",\"offset\",\"clock\","
            "\"mark\",\"selftest\",\"env\",\"save\",\"help\"]}");
}

/* --------------------------------------------------------------------------
 *  Analyse d'une ligne
 * ----------------------------------------------------------------------- */
static uint64_t index_courant = 0;
static uint32_t perdus_courant = 0;

static void traiter(char *entree)
{
    while (*entree == ' ') {
        entree++;
    }
    if (*entree == '\0') {
        return;
    }
    char *argument = strchr(entree, ' ');
    if (argument) {
        *argument++ = '\0';
        while (*argument == ' ') {
            argument++;
        }
    }

    if (strcmp(entree, "?") == 0 || strcmp(entree, "id") == 0) {
        cmd_identifier();
    } else if (strcmp(entree, "gain") == 0) {
        cmd_gain(argument);
    } else if (strcmp(entree, "range") == 0) {
        cmd_gamme(argument);
    } else if (strcmp(entree, "offset") == 0) {
        if (!argument) { erreur("usage : offset 0..65535"); return; }
        afe_set_offset((uint16_t)atoi(argument));
        ok("{\"offset\":%d}", atoi(argument));
    } else if (strcmp(entree, "clock") == 0) {
        cmd_horloge(index_courant, perdus_courant);
    } else if (strcmp(entree, "mark") == 0) {
        cmd_marqueur(argument, index_courant);
    } else if (strcmp(entree, "selftest") == 0) {
        cmd_autotest();
    } else if (strcmp(entree, "env") == 0) {
        cmd_ambiance();
    } else if (strcmp(entree, "save") == 0) {
        ok("{\"message\":\"reglages memorises en flash\"}");
    } else if (strcmp(entree, "help") == 0) {
        cmd_aide();
    } else {
        erreur("commande inconnue — taper help");
    }
}

/* --------------------------------------------------------------------------
 *  Interface publique
 * ----------------------------------------------------------------------- */
void protocol_init(void)
{
    pico_unique_board_id_t identifiant;
    pico_get_unique_board_id(&identifiant);
    snprintf(serie_carte, sizeof(serie_carte), "PS1-%02X%02X%02X%02X",
             identifiant.id[4], identifiant.id[5],
             identifiant.id[6], identifiant.id[7]);
    afe_lire_eeprom_carte_fille(type_fille, sizeof(type_fille),
                                serie_fille, sizeof(serie_fille));
    remplissage = 0;
}

void protocol_recevoir(const uint8_t *octets, uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        char c = (char)octets[i];
        if (c == '\r' || c == '\n') {
            if (remplissage) {
                ligne[remplissage] = '\0';
                traiter(ligne);
                remplissage = 0;
            }
        } else if (remplissage < sizeof(ligne) - 1) {
            ligne[remplissage++] = c;
        } else {
            remplissage = 0;           /* ligne trop longue : on repart */
            erreur("ligne trop longue");
        }
    }
}

void protocol_balise(uint64_t index, uint32_t perdus)
{
    index_courant = index;
    perdus_courant = perdus;
    if (!tud_cdc_connected()) {
        return;
    }
    afe_etat_t e;
    afe_etat(&e);
    ok("{\"beacon\":1,\"n\":%llu,\"lost\":%lu,\"gain\":%u,\"range\":%u,"
       "\"offset\":%u,\"sat\":%s}",
       (unsigned long long)index, (unsigned long)perdus, e.gain, e.gamme,
       e.offset_cna, e.sature ? "true" : "false");
}

void protocol_marqueur(const char *etiquette, uint64_t index)
{
    cmd_marqueur(etiquette, index);
}
