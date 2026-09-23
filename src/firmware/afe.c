/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/afe.c
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
 *  afe.c — the analog chain: converter, gain, range, self-test.
 *
 *  Everything that touches the measurement is here, and nothing else. The
 *  rest of the firmware does not know how a raw code becomes volts: it calls
 *  afe_to_volts() and keeps quiet.
 *
 *  The ADS131M04 converter is served over SPI by direct memory access,
 *  triggered by its own "data ready" pin. The microcontroller polls nothing:
 *  it is woken by the converter, which is what guarantees the sample rate is
 *  the compensated crystal's and not a software loop's.
 *
 *  MIT licence — Bretagne Namasté — https://bretagne-namaste.com
 * ======================================================================== */

#include <math.h>        /* sqrt(), for the self-test's standard deviation    */
#include <stdio.h>       /* snprintf(), to read the daughter board's label    */
#include <string.h>

#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/dma.h"
#include "hardware/gpio.h"
#include "hardware/i2c.h"

#include "afe.h"

/* --------------------------------------------------------------------------
 *  Pin assignment
 * ----------------------------------------------------------------------- */
#define SPI_PORT        spi0
#define PIN_SCK          2
#define PIN_MOSI         3
#define PIN_MISO         4
#define PIN_CS           5
#define PIN_DRDY         6        /* data ready, active low */
#define PIN_RESET        7

#define I2C_PORT        i2c0
#define PIN_SDA          20
#define PIN_SCL          21

#define PIN_GAIN_A0      10       /* gain selection, multiplexer U8 */
#define PIN_GAIN_A1      11
#define PIN_RANGE_A0     12       /* range selection, multiplexer U6 */
#define PIN_RANGE_A1     13
#define PIN_TEST_A0      14       /* self-test network, multiplexer U50 */
#define PIN_TEST_A1      15

/* --------------------------------------------------------------------------
 *  ADS131M04 registers (datasheet SBAS950)
 * ----------------------------------------------------------------------- */
#define REG_ID          0x00
#define REG_STATUS      0x01
#define REG_MODE        0x02
#define REG_CLOCK       0x03
#define REG_GAIN1       0x04
#define REG_CFG         0x06
#define REG_CH0_CFG     0x09

#define CMD_NULL        0x0000
#define CMD_RESET       0x0011
#define CMD_STANDBY     0x0022
#define CMD_WAKEUP      0x0033
#define CMD_RREG        0xA000
#define CMD_WREG        0x6000

/*  MODE: 24-bit word, CRC disabled, data left-aligned.
 *  CLOCK: four channels active, 4096x oversampling -> 250 Hz with the
 *  12.288 MHz crystal (12.288 MHz / 2 / 4096 / 6 = 250 Hz).                */
#define MODE_DEFAULT     0x0510
#define CLOCK_DEFAULT    0x0F0E   /* channels 0-3 enabled, OSR 4096 */
#define GAIN_DEFAULT     0x0000   /* internal gain x1: the gain is analog */

/* --------------------------------------------------------------------------
 *  Tables: programmable-stage gains, bridge ranges, reference resistors
 * ----------------------------------------------------------------------- */
static const uint16_t GAIN_TABLE[AFE_GAINS]   = {2, 10, 20, 200};
static const uint32_t RANGE_TABLE[AFE_RANGES] = {100000u, 1000000u,
                                                  10000000u, 100000000u};
static const uint32_t REFERENCE_TABLE[AFE_STANDARDS] = {1000000u, 10000000u,
                                                    100000000u};

#define FULL_SCALE_V   1.2f      /* +/-1.2 V with the 2.5 V reference */
#define FULL_SCALE_CODE 8388608.0f

/* --------------------------------------------------------------------------
 *  État interne
 * ----------------------------------------------------------------------- */
static afe_state_t state = {
    .gain = 1, .range = 1, .auto_gain = true, .dac_offset = 32768,
    .saturated = false, .temperature_c = 0.0f,
};
static volatile bool ready = false;
static uint8_t frame[ (AFE_CHANNELS + 2) * 3 ];   /* status + 4 channels + CRC */

/* --------------------------------------------------------------------------
 *  Low-level SPI access
 * ----------------------------------------------------------------------- */
static void cs(bool active)
{
    gpio_put(PIN_CS, active ? 0 : 1);
    asm volatile("nop \n nop \n nop");
}

static uint16_t spi_word(uint16_t out)
{
    uint8_t tx[3] = { (uint8_t)(out >> 8), (uint8_t)(out & 0xFF), 0 };
    uint8_t rx[3] = {0};
    spi_write_read_blocking(SPI_PORT, tx, rx, 3);
    return (uint16_t)((rx[0] << 8) | rx[1]);
}

static uint16_t reg_read(uint8_t address)
{
    cs(true);
    spi_word(CMD_RREG | ((uint16_t)address << 7));
    uint16_t value = spi_word(CMD_NULL);
    cs(false);
    return value;
}

static void reg_write(uint8_t address, uint16_t value)
{
    cs(true);
    spi_word(CMD_WREG | ((uint16_t)address << 7));
    spi_word(value);
    cs(false);
}

/* --------------------------------------------------------------------------
 *  The "data ready" interrupt
 * ----------------------------------------------------------------------- */
static void on_drdy(uint gpio, uint32_t events)
{
    (void)gpio; (void)events;
    ready = true;
}

/* --------------------------------------------------------------------------
 *  Gain and range selection
 *
 *  Each of the two multiplexers is driven by two pins. We then wait a few
 *  milliseconds: changing the gain makes the output jump,
 *  and the samples taken during the transition are worthless. The firmware
 *  MARKS them rather than dropping them silently — what to do with them is
 *  the computer's decision, not ours.
 * ----------------------------------------------------------------------- */
bool afe_set_gain(int idx)
{
    if (idx < 0) {
        state.auto_gain = true;
        return true;
    }
    if (idx >= AFE_GAINS) {
        return false;
    }
    state.auto_gain = false;
    state.gain = (uint8_t)idx;
    gpio_put(PIN_GAIN_A0, idx & 1);
    gpio_put(PIN_GAIN_A1, (idx >> 1) & 1);
    sleep_ms(2);
    return true;
}

bool afe_set_range(int idx)
{
    if (idx < 0 || idx >= AFE_RANGES) {
        return false;
    }
    state.range = (uint8_t)idx;
    gpio_put(PIN_RANGE_A0, idx & 1);
    gpio_put(PIN_RANGE_A1, (idx >> 1) & 1);
    sleep_ms(2);
    return true;
}

void afe_set_offset(uint16_t code)
{
    state.dac_offset = code;
    /* The re-centring DAC shares the I2C bus. Address 0x4C, two bytes,
     * most significant first. */
    uint8_t message[3] = { 0x00, (uint8_t)(code >> 8), (uint8_t)(code & 0xFF) };
    i2c_write_blocking(I2C_PORT, 0x4C, message, sizeof(message), false);
}

const uint16_t *afe_gain_table(void)   { return GAIN_TABLE; }
const uint32_t *afe_range_table(void)  { return RANGE_TABLE; }

/* --------------------------------------------------------------------------
 *  Auto-ranging loop
 *
 *  The rule: step down as soon as 90 % of full scale is exceeded; step back
 *  up after more than a second below 20 %. The hysteresis is what keeps a
 *  signal oscillating around a threshold from making the range chatter — the
 *  classic failing of a naive auto-range.
 * ----------------------------------------------------------------------- */
static void auto_range(int32_t code)
{
    static uint32_t low_since = 0;
    float fraction = (float)(code < 0 ? -code : code) / FULL_SCALE_CODE;

    if (fraction > 0.90f) {
        state.saturated = true;
        if (state.gain > 0) {
            afe_set_gain(state.gain - 1);
            state.auto_gain = true;
        }
        low_since = 0;
        return;
    }
    state.saturated = false;

    if (fraction < 0.20f) {
        if (++low_since > 250u && state.gain < AFE_GAINS - 1) {
            afe_set_gain(state.gain + 1);
            state.auto_gain = true;
            low_since = 0;
        }
    } else {
        low_since = 0;
    }
}

/* --------------------------------------------------------------------------
 *  Reading one sample set
 * ----------------------------------------------------------------------- */
bool afe_read(afe_sample_t *out)
{
    if (!ready) {
        return false;
    }
    ready = false;

    cs(true);
    uint8_t tx[sizeof(frame)];
    memset(tx, 0, sizeof(tx));
    spi_write_read_blocking(SPI_PORT, tx, frame, sizeof(frame));
    cs(false);

    /* The first word is the status; then the four channels, three bytes
     * each, in two's complement. */
    for (int v = 0; v < AFE_CHANNELS; v++) {
        const uint8_t *p = &frame[3 + v * 3];
        int32_t code = ((int32_t)p[0] << 16) | ((int32_t)p[1] << 8) | p[2];
        if (code & 0x800000) {
            code -= 0x1000000;        /* sign-extend from 24 bits */
        }
        out->channel[v] = code;
    }
    if (state.auto_gain) {
        auto_range(out->channel[0]);
    }
    return true;
}

void afe_state(afe_state_t *out) { *out = state; }

float afe_to_volts(int32_t code, const afe_state_t *e)
{
    float gain = (float)GAIN_TABLE[e->gain < AFE_GAINS ? e->gain : 0];
    return ((float)code / FULL_SCALE_CODE) * FULL_SCALE_V / gain;
}

/* --------------------------------------------------------------------------
 *  Self-test against the internal reference resistors
 *
 *  Three 0.1 % resistors are substituted for the plant in turn. Measure,
 *  compare, report the error. This is the function that answers, in thirty
 *  seconds, the only question that matters in front of a surprising
 *  measurement: is it the plant, or is it the instrument?
 * ----------------------------------------------------------------------- */
static void test_select(int idx)
{
    gpio_put(PIN_TEST_A0, idx & 1);
    gpio_put(PIN_TEST_A1, (idx >> 1) & 1);
    sleep_ms(50);                      /* let the filter settle */
}

static float average_over(int samples)
{
    double sum = 0.0;
    afe_sample_t e;
    int got = 0;
    absolute_time_t deadline = make_timeout_time_ms(2000);
    while (got < samples && !time_reached(deadline)) {
        if (afe_read(&e)) {
            sum += afe_to_volts(e.channel[0], &state);
            got++;
        }
    }
    return got ? (float)(sum / got) : 0.0f;
}

bool afe_selftest(afe_selftest_t *report)
{
    if (report == NULL) {
        return false;
    }
    memset(report, 0, sizeof(*report));

    const uint8_t initial_gain = state.gain;
    const bool initial_auto = state.auto_gain;
    afe_set_gain(1);                   /* x10: a compromise for all three */

    /* 1. noise floor, input on the highest reference */
    test_select(3);
    float base = average_over(200);
    double sum_of_squares = 0.0;
    afe_sample_t e;
    for (int i = 0; i < 200; i++) {
        while (!afe_read(&e)) { tight_loop_contents(); }
        float v = afe_to_volts(e.channel[0], &state) - base;
        sum_of_squares += (double)v * v;
    }
    report->noise_v = (float)sqrt(sum_of_squares / 200.0);

    /* 2. the three references */
    bool passed = true;
    for (int i = 0; i < AFE_STANDARDS; i++) {
        test_select(i);
        float measurement = average_over(100);
        /* Converting voltage to resistance depends on the excitation
         * current, calibrated in the factory and stored in memory. A
         * simplified form is used here. */
        float expected = (float)REFERENCE_TABLE[i];
        float ohms = measurement / 1.0e-7f;          /* 100 nA d'excitation */
        report->measured_ohm[i] = ohms;
        report->error_percent[i] = 100.0f * (ohms - expected) / expected;
        if (report->error_percent[i] > 0.5f ||
            report->error_percent[i] < -0.5f) {
            passed = false;
        }
    }

    /* 3. leakage current, by the charge-capacitance method */
    test_select(3);              /* open input onto 100 pF */
    float v0 = average_over(20);
    sleep_ms(1000);
    float v1 = average_over(20);
    report->leakage_fa = (v1 - v0) * 100e-12f * 1e15f;   /* I = C·dV/dt */

    test_select(0);
    afe_set_gain(initial_auto ? -1 : initial_gain);
    report->passed = passed;
    return true;
}

/* --------------------------------------------------------------------------
 *  The daughter board's identification memory
 *
 *  Every daughter board carries a 24AA02 on the isolated I2C bus. The first
 *  sixteen bytes are enough: type, serial number, calibration date. The
 *  microcontroller reads them at start-up and passes them to the computer,
 *  which then adapts its units without the user having to declare anything.
 * ----------------------------------------------------------------------- */
bool afe_read_daughter_eeprom(char *type, size_t type_max,
                                 char *serial, size_t serial_max)
{
    uint8_t address = 0x00;
    uint8_t donnees[32] = {0};

    if (i2c_write_blocking(I2C_PORT, 0x50, &address, 1, true) < 0) {
        return false;
    }
    if (i2c_read_blocking(I2C_PORT, 0x50, donnees, sizeof(donnees), false) < 0) {
        return false;
    }
    /*  Layout: 'P','S','1',version | type[8] | serial[12] | date[8] | sum */
    if (donnees[0] != 'P' || donnees[1] != 'S' || donnees[2] != '1') {
        return false;
    }
    snprintf(type, type_max, "%.8s", (const char *)&donnees[4]);
    snprintf(serial, serial_max, "%.12s", (const char *)&donnees[12]);
    return true;
}

/* --------------------------------------------------------------------------
 *  Initialisation
 * ----------------------------------------------------------------------- */
bool afe_init(void)
{
    /* SPI at 8 MHz: the converter accepts 25 MHz, but there is no reason to
     * fast, and slower edges radiate less. */
    spi_init(SPI_PORT, 8 * 1000 * 1000);
    spi_set_format(SPI_PORT, 8, SPI_CPOL_0, SPI_CPHA_1, SPI_MSB_FIRST);
    gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);

    gpio_init(PIN_CS);   gpio_set_dir(PIN_CS, GPIO_OUT);   gpio_put(PIN_CS, 1);
    gpio_init(PIN_RESET); gpio_set_dir(PIN_RESET, GPIO_OUT); gpio_put(PIN_RESET, 1);

    for (int b = 0; b < 6; b++) {
        const uint broches[] = { PIN_GAIN_A0, PIN_GAIN_A1, PIN_RANGE_A0,
                                 PIN_RANGE_A1, PIN_TEST_A0, PIN_TEST_A1 };
        gpio_init(broches[b]);
        gpio_set_dir(broches[b], GPIO_OUT);
        gpio_put(broches[b], 0);
    }

    i2c_init(I2C_PORT, 400 * 1000);
    gpio_set_function(PIN_SDA, GPIO_FUNC_I2C);
    gpio_set_function(PIN_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(PIN_SDA);
    gpio_pull_up(PIN_SCL);

    /* Hardware reset, then software reset */
    gpio_put(PIN_RESET, 0);
    sleep_ms(2);
    gpio_put(PIN_RESET, 1);
    sleep_ms(10);
    cs(true); spi_word(CMD_RESET); cs(false);
    sleep_ms(10);

    if ((reg_read(REG_ID) & 0xFF00) == 0) {
        return false;                  /* no converter on the bus */
    }

    reg_write(REG_MODE, MODE_DEFAULT);
    reg_write(REG_CLOCK, CLOCK_DEFAULT);
    reg_write(REG_GAIN1, GAIN_DEFAULT);

    gpio_init(PIN_DRDY);
    gpio_set_dir(PIN_DRDY, GPIO_IN);
    gpio_pull_up(PIN_DRDY);
    gpio_set_irq_enabled_with_callback(PIN_DRDY, GPIO_IRQ_EDGE_FALL, true,
                                       &on_drdy);

    afe_set_gain(1);
    afe_set_range(1);
    afe_set_offset(32768);
    return true;
}

void afe_start(uint32_t frequency_hz)
{
    (void)frequency_hz;                /* set by CLOCK_DEFAULT and the TCXO */
    cs(true); spi_word(CMD_WAKEUP); cs(false);
}

void afe_stop(void)
{
    cs(true); spi_word(CMD_STANDBY); cs(false);
}
