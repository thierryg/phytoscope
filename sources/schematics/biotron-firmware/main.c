/*
 *  ==========================================================================
 *  PhytoScope — attribution — sources/schematics/biotron-firmware/main.c
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

#include <hardware/adc.h>
#include <pico/printf.h>
#include "pico/stdlib.h"
#include "PLSDK.h"
#include "global.h"
#include "buttons.h"
#include "leds.h"
#include "raw_plant.h"
#include "params.h"



void setup() {
    stdio_init_all();
    init_midi();

    adc_init();
    adc_gpio_init(LIGHT_PIN);
    adc_select_input(0);

    init_leds();
    init_buttons();
    init_plant();

    intro_leds();
    read_settings();
    setup_commands();
}


int main(void)
{
    setup();
    while (true)
    {
        status_loop();
        led_loop();
        check_buttons();
        remind_midi();
        get_sys_ex_and_behave();
        sleep_ms(1);
    }
}

