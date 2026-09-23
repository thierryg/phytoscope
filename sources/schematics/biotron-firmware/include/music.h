/*
 *  ==========================================================================
 *  PhytoScope — attribution — sources/schematics/biotron-firmware/include/music.h
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

#ifndef BIOTRON_MUSIC_H
#define BIOTRON_MUSIC_H


#define LOWEST_NOTE_RANGE 24
#define HIGHEST_NOTE_RANGE 37
#define MIDDLE_NOTE 60
#define LIGHT_DIFFERENCE 24
extern uint8_t last_note_plant;


#define MAX_OF_LIGHT 3200
extern uint8_t last_note_light;

void reset_plant_note_off();
void midi_plant(int64_t to_the_next_beat_us);

void midi_light();
void midi_light_pitch();

void stop_midi();

void play_music(int64_t to_the_next_beat_us);
void play_music_bpm_clock();

#endif //BIOTRON_MUSIC_H
