/*
 *  ==========================================================================
 *  PhytoScope — attribution — sources/schematics/biotron-firmware/PLSDK/include/PLSDK.h
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

#ifndef PLSDK_PLSDK_H
#define PLSDK_PLSDK_H

extern bool LOGGER_FLAG;


/** @brief Initialize main functionality
 *
 *  @Note Must be put in start of code
 *  @return   Returns nothing
 * */
void init_midi();

/** @brief Remind device about midi
 *
 *  @Note Must be put in main loop, and places where code can be stack for some time
 *  @return   Nothing
 * */
void remind_midi();


void plsdk_printf(const char * format, ...);

#endif //PLSDK_PLSDK_H
