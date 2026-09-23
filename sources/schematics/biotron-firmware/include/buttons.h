/*
 *  ==========================================================================
 *  PhytoScope — attribution — sources/schematics/biotron-firmware/include/buttons.h
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

#ifndef BIOTRON_BUTTONS_H
#define BIOTRON_BUTTONS_H

#include <stdbool.h>

#define BUTTON_FINGER 8
#define BUTTON_BOTTOM 7
#define BUTTON_TOP 6

extern bool button_finger_pressed;
extern bool button_bottom_pressed;
extern bool button_top_pressed;

void init_buttons();
void check_buttons();

#endif //BIOTRON_BUTTONS_H
