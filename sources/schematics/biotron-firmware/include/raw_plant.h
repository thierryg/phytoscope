/*
 *  ==========================================================================
 *  PhytoScope — attribution — sources/schematics/biotron-firmware/include/raw_plant.h
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

#ifndef BIOTRON_RAW_PLANT_H
#define BIOTRON_RAW_PLANT_H

#define PLANT_PIN 13
#define TIMER_PLANT_MS 100
#define TIMER_MULTIPLIER (1000 / TIMER_PLANT_MS)

#define MIN_FREQ 60

void init_plant();
bool plant_is_ready();
uint32_t get_real_freq();

#endif //BIOTRON_RAW_PLANT_H
