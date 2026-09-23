/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/protocol.h
 *
 *  Version   : 1.6.0
 *  Date      : 2026-09-23
 *  Publisher : Bretagne Namasté
 *  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
 *  Website   : https://bretagne-namaste.com
 *  Contact   : contact@bretagne-namaste.com
 *  License   : MIT — see LICENSE.txt
 *
 *  SPDX-License-Identifier: MIT
 *  end of attribution
 *  ==========================================================================
 */

/* ---------------------------------------------------------------------------
 *  protocol.h — the control dialogue on the virtual serial port.
 *
 *  Commands are plain text terminated by CR-LF; replies fit on one line and
 *  open with '+' (success) or '-' (failure) followed by a JSON object. The
 *  choice is deliberately archaic: it means the board can be interrogated and
 *  repaired with any terminal, with no software at all.
 *
 *  Licence MIT — Bretagne Namasté
 * ------------------------------------------------------------------------ */
#ifndef PHYTOSENSE_PROTOCOL_H
#define PHYTOSENSE_PROTOCOL_H

#include <stddef.h>
#include <stdint.h>

#define PROTO_LINE_MAX   256
#define PROTO_REPLY_MAX 512

void protocol_init(void);

/* Absorb received bytes; emits a reply once a complete line has arrived. */
void protocol_receive(const uint8_t *bytes, uint32_t n);

/* Periodic state beacon: sample index, lost count, gain, range, saturation. */
void protocol_beacon(uint64_t index, uint32_t lost);

/* Insert a mark, from the board's button. */
void protocol_mark(const char *label, uint64_t index);

#endif /* PHYTOSENSE_PROTOCOL_H */
