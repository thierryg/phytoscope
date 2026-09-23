/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/afe.h
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
 *  afe.h — the analog chain: converter, gain, range, self-test.
 *
 *  Licence MIT — Bretagne Namasté
 * ------------------------------------------------------------------------ */
#ifndef PHYTOSENSE_AFE_H
#define PHYTOSENSE_AFE_H

#include <stdbool.h>
#include <stdint.h>

#define AFE_CHANNELS     4
#define AFE_GAINS        4           /* ×2, ×10, ×20, ×200 */
#define AFE_RANGES       4           /* 100 k, 1 M, 10 M, 100 MΩ */
#define AFE_STANDARDS    3           /* 1 M, 10 M, 100 MΩ */

/*  The rate the board runs at, in hertz.
 *
 *  It lives here because the analog chain fixes it: four channels active and
 *  4096x oversampling off the 12.288 MHz crystal give
 *  12.288 MHz / 2 / 4096 / 6 = 250 Hz exactly. Nothing changes it at run
 *  time — there is no command for it in the control port, and the clock
 *  source descriptor says so with AUDIO_CLOCK_SOURCE_ATT_INT_FIX_CLK.
 *
 *  Three other files have to agree with it: `main.c` starts the converter
 *  with it, `protocol.c` reports it in the reply to `identify`, and
 *  `usb_descriptors.c` answers the host's clock-source request with it. It
 *  was written down three times, independently, until 2026-09-23.           */
#define AFE_RATE_HZ      250u

/* One sample set, as it comes out of the converter. */
typedef struct {
    uint64_t index;                  /* index of the first sample */
    int32_t  channel[AFE_CHANNELS];        /* signed 24-bit samples */
} afe_sample_t;

/* Current state of the chain, sent to the host on every change. */
typedef struct {
    uint8_t  gain;                   /* index into the gain table */
    uint8_t  range;                  /* index into the range table */
    bool     auto_gain;              /* auto-ranging loop is running */
    uint16_t dac_offset;             /* applied re-centring, 16 bits */
    bool     saturated;                 /* at least one channel is railed */
    float    temperature_c;          /* the board's own sensor */
} afe_state_t;

/* Self-test report against the internal reference resistors. */
typedef struct {
    bool  passed;
    float measured_ohm[AFE_STANDARDS];
    float error_percent[AFE_STANDARDS];
    float noise_v;
    float leakage_fa;
} afe_selftest_t;

bool  afe_init(void);
void  afe_start(uint32_t frequency_hz);
void  afe_stop(void);

bool  afe_read(afe_sample_t *out);   /* non-blocking */
void  afe_state(afe_state_t *out);

bool  afe_set_gain(int idx);              /* -1 = automatique */
bool  afe_set_range(int idx);
void  afe_set_offset(uint16_t code);

const uint16_t *afe_gain_table(void);
const uint32_t *afe_range_table(void);

bool  afe_selftest(afe_selftest_t *report);
bool  afe_read_daughter_eeprom(char *type, size_t type_max,
                                  char *serial, size_t serial_max);

/* Convert a raw code to volts, given the current state. */
float afe_to_volts(int32_t code, const afe_state_t *state);

#endif /* PHYTOSENSE_AFE_H */
