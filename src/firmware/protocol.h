/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/protocol.h
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
 *  protocol.h — dialogue de contrôle sur le port série virtuel.
 *
 *  Les commandes sont en texte, terminées par CR-LF ; les réponses tiennent
 *  sur une ligne et commencent par '+' (succès) ou '-' (erreur), suivi d'un
 *  objet JSON. Ce choix délibérément archaïque permet d'interroger et de
 *  dépanner la carte avec n'importe quel terminal, sans logiciel.
 *
 *  Licence MIT — Bretagne Namasté
 * ------------------------------------------------------------------------ */
#ifndef PHYTOSENSE_PROTOCOL_H
#define PHYTOSENSE_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#define PROTO_LIGNE_MAX   256
#define PROTO_REPONSE_MAX 512

void protocol_init(void);

/* Absorbe les octets reçus ; appelle protocol_emettre() sur ligne complète. */
void protocol_recevoir(const uint8_t *octets, uint32_t n);

/* Émission périodique de la balise d'état (numéro d'échantillon, gain…). */
void protocol_balise(uint64_t index, uint32_t perdus);

/* Insère un marqueur, depuis le bouton de la carte. */
void protocol_marqueur(const char *etiquette, uint64_t index);

#endif /* PHYTOSENSE_PROTOCOL_H */
