/*
 *  ==========================================================================
 *  PhytoScope — attribution — sources/schematics/biotron-firmware/PLSDK/src/PLSDK.c
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

#include "tusb.h"
#include <stdarg.h>
#include "PLSDK.h"

bool LOGGER_FLAG = false;


void init_midi() {
    tusb_init();
}


void remind_midi() {
    tud_task();
}

void plsdk_printf(const char *__restrict format, ...) {
    if (!LOGGER_FLAG) return;
    va_list args;
    va_start(args, format);
    vprintf(format, args);
    va_end(args);
}
