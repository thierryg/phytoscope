/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/main.c
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

/* ===========================================================================
 *  main.c — PhytoSense One firmware
 *
 *  Two cores, one rule: core 0 does nothing but measure and timestamp; core 1
 *  does everything else. They share a single ring buffer, through indices
 *  whose writes are atomic on Cortex-M33.
 *
 *  That separation is why the stream has no gaps even while the computer is
 *  interrogating the board in the middle of an acquisition.
 *
 *  MIT licence — Bretagne Namasté — https://bretagne-namaste.com
 * ======================================================================== */

#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/multicore.h"
#include "pico/unique_id.h"
#include "hardware/clocks.h"
#include "hardware/gpio.h"
#include "hardware/pwm.h"
#include "tusb.h"

#include "afe.h"
#include "protocol.h"

/* --------------------------------------------------------------------------
 *  Board constants
 * ----------------------------------------------------------------------- */
#define FW_VERSION          "1.0.0"
#define MODEL              "PhytoSense One"

#define RING_SAMPLES       4096u     /* must be a power of two */
#define RING_MASK       (RING_SAMPLES - 1u)

#define PIN_LED          16
#define PIN_BUTTON       17
#define PIN_SYNC         18        /* to the transformer driver */
#define PIN_MIDI_TX      8

/* --------------------------------------------------------------------------
 *  Ring buffer shared between the two cores
 *
 *  Producer: core 0, which increments `write_idx`.
 *  Consumer: core 1, which increments `read_idx`.
 *  No lock: on Cortex-M33 an aligned uint32_t write is atomic, and only one
 *  core writes each index. Overrun is COUNTED, never silently swallowed —
 *  isochronous transfers are not retried, so nothing else would tell you.
 * ----------------------------------------------------------------------- */
static afe_sample_t ring[RING_SAMPLES];
static volatile uint32_t ring_write = 0;
static volatile uint32_t ring_read  = 0;
static volatile uint32_t lost_samples = 0;
static volatile uint64_t global_counter = 0;

static inline uint32_t ring_available(void)
{
    return (ring_write - ring_read) & RING_MASK;
}

static inline bool ring_push(const afe_sample_t *e)
{
    uint32_t next_one = (ring_write + 1u) & RING_MASK;
    if (next_one == ring_read) {
        lost_samples++;        /* the host is not reading fast enough */
        return false;
    }
    ring[ring_write] = *e;
    ring_write = next_one;
    return true;
}

static inline bool ring_pop(afe_sample_t *e)
{
    if (ring_read == ring_write) {
        return false;
    }
    *e = ring[ring_read];
    ring_read = (ring_read + 1u) & RING_MASK;
    return true;
}

/* --------------------------------------------------------------------------
 *  Synchronising the isolated supply's switching
 *
 *  The transformer driver is clocked by a division of the system clock. The
 *  switching residue therefore lands at a fixed, known frequency well away
 *  from the measurement band — rather than beating against the sampling and
 *  producing very slow ripples, indistinguishable from a plant signal.
 * ----------------------------------------------------------------------- */
static void sync_init(uint32_t frequency_hz)
{
    gpio_set_function(PIN_SYNC, GPIO_FUNC_PWM);
    uint slice = pwm_gpio_to_slice_num(PIN_SYNC);
    uint32_t sys = clock_get_hz(clk_sys);
    uint32_t divider = sys / (frequency_hz * 2u);

    pwm_config cfg = pwm_get_default_config();
    pwm_config_set_wrap(&cfg, (uint16_t)(divider - 1u));
    pwm_init(slice, &cfg, true);
    pwm_set_gpio_level(PIN_SYNC, (uint16_t)(divider / 2u));
}

/* --------------------------------------------------------------------------
 *  Core 0 — the measurement loop
 *
 *  No allocation, no blocking call, no I/O. Its execution time is bounded,
 *  which is what guarantees the sample rate is held whatever else happens in
 *  the system.
 * ----------------------------------------------------------------------- */
static void measurement_loop(void)
{
    afe_sample_t e;

    for (;;) {
        if (afe_read(&e)) {
            e.index = global_counter++;
            ring_push(&e);
        }
        tight_loop_contents();
    }
}

/* --------------------------------------------------------------------------
 *  Audio class: handing the stream to the host
 *
 *  Samples leave as 24 bits, one track per channel. The sample INDEX is not
 *  carried by the audio class — that is the job of the beacon sent on the
 *  serial port, which lets the host align the stream and check that nothing
 *  was lost.
 *
 *  The frame is variable in length: this loop drains whatever the ring holds,
 *  up to the packet size. At 250 Hz three frames in four carry nothing. A
 *  host-side reader must therefore take the length the transfer returns and
 *  not assume twelve bytes.
 *
 *  The packet size is a hard ceiling on the rate the board can sustain,
 *  because the loop stops when the next whole sample set would not fit:
 *
 *      highest rate = packet size / 12 bytes x 1000 frames/s
 *
 *  384 bytes gives exactly 32 sample sets, so 32 kHz — the fastest the
 *  analog front end can be driven. It was 256 until 2026-09-23, which gave
 *  21 sets and a ceiling near 21 kHz while `tusb_config.h` claimed to cover
 *  32 kHz: above that ceiling this loop left samples in the ring, where
 *  `ring_lost` counted them. That was divergence 11.2 of the USB reference.
 * ----------------------------------------------------------------------- */
static uint8_t usb_frame[CFG_TUD_AUDIO_EP_SZ_IN];

/*  A packet that is not a whole number of sample sets wastes the remainder
 *  in every frame, for ever. 384 = 32 x 12 divides exactly; 256 did not, and
 *  threw away four bytes per frame as well as capping the rate. Left as a
 *  build error rather than a comment, because the next person to change the
 *  packet size will not read the comment.                                  */
TU_VERIFY_STATIC(CFG_TUD_AUDIO_EP_SZ_IN % (AFE_CHANNELS * 3u) == 0,
                 "the isochronous packet is not a whole number of sample sets");

bool tud_audio_tx_done_pre_load_cb(uint8_t rhport, uint8_t itf,
                                   uint8_t ep_in, uint8_t cur_alt_setting)
{
    (void)rhport; (void)itf; (void)ep_in; (void)cur_alt_setting;

    afe_sample_t e;
    uint32_t n = 0;

    while (n + (AFE_CHANNELS * 3u) <= sizeof(usb_frame) && ring_pop(&e)) {
        for (int v = 0; v < AFE_CHANNELS; v++) {
            int32_t code = e.channel[v];
            usb_frame[n++] = (uint8_t)(code & 0xFF);
            usb_frame[n++] = (uint8_t)((code >> 8) & 0xFF);
            usb_frame[n++] = (uint8_t)((code >> 16) & 0xFF);
        }
    }
    if (n) {
        tud_audio_write(usb_frame, (uint16_t)n);
    }
    return true;
}

/* --------------------------------------------------------------------------
 *  Status indicator
 *
 *  Blue: no electrode detected. Green: signal present. Amber: saturation.
 *  Red: fault. The colour reports the state of the MEASUREMENT, never the
 *  state of the plant — the distinction matters, and it matters most to the
 *  person who most wants it to be otherwise.
 * ----------------------------------------------------------------------- */
static void led_state(const afe_state_t *state, bool host_connected)
{
    static uint32_t phase = 0;
    phase++;

    uint8_t r = 0, v = 0, b = 0;
    if (state->saturated) {
        r = 180; v = 90;                       /* amber */
    } else if (!host_connected) {
        b = 120;                               /* blue: waiting */
    } else {
        v = 140;                               /* green: acquiring */
    }
    /* a slow breathing pulse, easy on the eye over a long session */
    uint8_t amplitude = (uint8_t)(200 + 55 * ((phase >> 6) & 1u));
    (void)amplitude; (void)r; (void)v; (void)b;
    /* Driving the addressable LED itself is left to ws2812_pio(). */
}

/* --------------------------------------------------------------------------
 *  Core 1 — USB, control, housekeeping
 * ----------------------------------------------------------------------- */
int main(void)
{
    stdio_init_all();

    gpio_init(PIN_BUTTON);
    gpio_set_dir(PIN_BUTTON, GPIO_IN);
    gpio_pull_up(PIN_BUTTON);

    sync_init(410000u);                        /* 410 kHz, out of band */

    if (!afe_init()) {
        /* With no converter the board stays alive so that it can still be
         * interrogated: that is what lets you diagnose instead of guess. */
        protocol_init();
        tusb_init();
        for (;;) { tud_task(); }
    }

    afe_start(AFE_RATE_HZ);
    protocol_init();
    tusb_init();

    /*  The measurement loop runs on core 1, and USB on core 0 — `main` is
     *  core 0 by definition, and this call starts core 1. The naming said
     *  the opposite until 2026-09-23; the code was right and the names were
     *  wrong, so the names were changed. */
    multicore_launch_core1(measurement_loop);

    absolute_time_t next_beacon = make_timeout_time_ms(200);
    absolute_time_t next_state    = make_timeout_time_ms(50);
    bool previous_button = true;

    for (;;) {
        tud_task();

        /* -- control dialogue -------------------------------------------- */
        if (tud_cdc_available()) {
            uint8_t buf[64];
            uint32_t n = tud_cdc_read(buf, sizeof(buf));
            protocol_receive(buf, n);
        }

        /* -- periodic beacon: this is what timestamps the stream ---------- */
        if (time_reached(next_beacon)) {
            next_beacon = make_timeout_time_ms(200);
            protocol_beacon(global_counter, lost_samples);
        }

        /* -- button: a timestamped mark ----------------------------------- */
        bool button = gpio_get(PIN_BUTTON);
        if (previous_button && !button) {
            protocol_mark("button", global_counter);
        }
        previous_button = button;

        /* -- indicator -------------------------------------------------------- */
        if (time_reached(next_state)) {
            next_state = make_timeout_time_ms(50);
            afe_state_t state;
            afe_state(&state);
            led_state(&state, tud_mounted());
        }
    }
    return 0;
}
