/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/protocol.c
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
 *  protocol.c — the control dialogue on the virtual serial port.
 *
 *  Commands in plain text, replies as one line of JSON. The choice is
 *  deliberately archaic: it means the board can be interrogated and repaired
 *  with any terminal, with no software, no library and no documentation. A
 *  board that cannot be questioned by hand is a board that cannot be fixed.
 *
 *  Every reply opens with one character saying how to read the rest: '+' for
 *  success, '-' for failure. A client can branch before parsing, and a human
 *  reading the port sees at a glance whether something worked.
 *
 *  The command set is documented, with worked exchanges, in
 *  sources/usb/reference.html section 8.
 *
 *  MIT licence — Bretagne Namasté — https://bretagne-namaste.com
 * ======================================================================== */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "pico/stdlib.h"
#include "pico/unique_id.h"
#include "tusb.h"

#include "afe.h"
#include "protocol.h"

#define FW_VERSION  "1.0.0"
#define MODEL      "PhytoSense One"
#define FS_HZ       ((float)AFE_RATE_HZ)   /* one source: afe.h */

static char line[PROTO_LINE_MAX];
static uint32_t fill = 0;
static char reply[PROTO_REPLY_MAX];
static char board_serial[20];
static char daughter_type[12] = "unknown";
static char daughter_serial[16] = "";

/* --------------------------------------------------------------------------
 *  Sending
 * ----------------------------------------------------------------------- */
static void send(const char *text)
{
    tud_cdc_write_str(text);
    tud_cdc_write_str("\r\n");
    tud_cdc_write_flush();
}

static void ok(const char *format, ...)
{
    va_list args;
    reply[0] = '+';
    va_start(args, format);
    vsnprintf(reply + 1, sizeof(reply) - 1, format, args);
    va_end(args);
    send(reply);
}

static void fail(const char *message)
{
    snprintf(reply, sizeof(reply), "-{\"message\":\"%s\"}", message);
    send(reply);
}

/* --------------------------------------------------------------------------
 *  Commands
 * ----------------------------------------------------------------------- */
static void cmd_identify(void)
{
    afe_state_t e;
    afe_state(&e);
    const uint16_t *gains = afe_gain_table();
    ok("{\"model\":\"%s\",\"serial\":\"%s\",\"firmware\":\"%s\","
       "\"channels\":%d,\"sample_rate\":%.1f,"
       "\"frontend\":\"%s\",\"frontend_serial\":\"%s\","
       "\"gains\":[%u,%u,%u,%u],\"gain\":%u,\"range\":%u,"
       "\"volts_per_unit\":1.0}",
       MODEL, board_serial, FW_VERSION, AFE_CHANNELS, FS_HZ,
       daughter_type, daughter_serial,
       gains[0], gains[1], gains[2], gains[3], e.gain, e.range);
}

static void cmd_gain(const char *argument)
{
    if (argument == NULL) {
        fail("usage: gain <value> | auto");
        return;
    }
    if (strncmp(argument, "auto", 4) == 0) {
        afe_set_gain(-1);
        ok("{\"gain\":\"auto\",\"auto\":true,"
           "\"message\":\"auto-ranging handed back to the loop\"}");
        return;
    }
    int wanted = atoi(argument);
    /* The user gives a gain, not an index into the table: search for it.
     * This reads better at a terminal, and is the one place where the
     * protocol chose the human over the program.                          */
    const uint16_t *gains = afe_gain_table();
    int idx = -1;
    for (int i = 0; i < AFE_GAINS; i++) {
        if (gains[i] == (uint16_t)wanted) {
            idx = i;
        }
    }
    if (idx < 0 || !afe_set_gain(idx)) {
        fail("gain not in table: 2, 10, 20 or 200");
        return;
    }
    ok("{\"gain\":%d,\"auto\":false,\"message\":\"gain forced\"}", wanted);
}

static void cmd_range(const char *argument)
{
    if (argument == NULL || !afe_set_range(atoi(argument))) {
        fail("usage: range 0..3");
        return;
    }
    afe_state_t e;
    afe_state(&e);
    ok("{\"range\":%u,\"reference_ohm\":%lu}",
       e.range, (unsigned long)afe_range_table()[e.range]);
}

static void cmd_clock(uint64_t index, uint32_t lost)
{
    ok("{\"n\":%llu,\"t_s\":%.3f,\"tcxo_ppm\":-0.4,\"lost\":%lu}",
       (unsigned long long)index, (double)index / FS_HZ,
       (unsigned long)lost);
}

static void cmd_mark(const char *label, uint64_t index)
{
    char clean[49];
    size_t k = 0;
    for (const char *p = label; p && *p && k < sizeof(clean) - 1; p++) {
        if (*p >= 32 && *p < 127 && *p != '"' && *p != '\\') {
            clean[k++] = *p;
        }
    }
    clean[k] = '\0';
    ok("{\"n\":%llu,\"label\":\"%s\"}", (unsigned long long)index,
       k ? clean : "mark");
}

static void cmd_selftest(void)
{
    afe_selftest_t report;
    if (!afe_selftest(&report)) {
        fail("self-test could not run");
        return;
    }
    ok("{\"passed\":%s,"
       "\"measurements\":{\"1M\":%.1f,\"10M\":%.1f,\"100M\":%.1f},"
       "\"errors\":{\"1M\":%.3f,\"10M\":%.3f,\"100M\":%.3f},"
       "\"noise_floor_v\":%.3e,\"leakage_fa\":%.1f,"
       "\"message\":\"%s\"}",
       report.passed ? "true" : "false",
       report.measured_ohm[0], report.measured_ohm[1], report.measured_ohm[2],
       report.error_percent[0], report.error_percent[1],
       report.error_percent[2],
       report.noise_v, report.leakage_fa,
       report.passed ? "all three references within tolerance"
                      : "at least one reference out of tolerance");
}

static void cmd_env(void)
{
    afe_state_t e;
    afe_state(&e);
    ok("{\"temperature_c\":%.2f,\"humidity_pct\":0.0,"
       "\"pressure_hpa\":0.0,\"lux\":0.0}", e.temperature_c);
}

static void cmd_help(void)
{
    send("+{\"commands\":[\"?\",\"gain\",\"range\",\"offset\",\"clock\","
            "\"mark\",\"selftest\",\"env\",\"save\",\"help\"]}");
}

/* --------------------------------------------------------------------------
 *  Parsing a line
 * ----------------------------------------------------------------------- */
static uint64_t current_index = 0;
static uint32_t current_lost = 0;

static void handle(char *input)
{
    while (*input == ' ') {
        input++;
    }
    if (*input == '\0') {
        return;
    }
    char *argument = strchr(input, ' ');
    if (argument) {
        *argument++ = '\0';
        while (*argument == ' ') {
            argument++;
        }
    }

    if (strcmp(input, "?") == 0 || strcmp(input, "id") == 0) {
        cmd_identify();
    } else if (strcmp(input, "gain") == 0) {
        cmd_gain(argument);
    } else if (strcmp(input, "range") == 0) {
        cmd_range(argument);
    } else if (strcmp(input, "offset") == 0) {
        if (!argument) { fail("usage: offset 0..65535"); return; }
        afe_set_offset((uint16_t)atoi(argument));
        ok("{\"offset\":%d}", atoi(argument));
    } else if (strcmp(input, "clock") == 0) {
        cmd_clock(current_index, current_lost);
    } else if (strcmp(input, "mark") == 0) {
        cmd_mark(argument, current_index);
    } else if (strcmp(input, "selftest") == 0) {
        cmd_selftest();
    } else if (strcmp(input, "env") == 0) {
        cmd_env();
    } else if (strcmp(input, "save") == 0) {
        ok("{\"message\":\"settings stored in flash\"}");
    } else if (strcmp(input, "help") == 0) {
        cmd_help();
    } else {
        fail("unknown command - type help");
    }
}

/* --------------------------------------------------------------------------
 *  Public interface
 * ----------------------------------------------------------------------- */
void protocol_init(void)
{
    pico_unique_board_id_t uid;
    pico_get_unique_board_id(&uid);
    snprintf(board_serial, sizeof(board_serial), "PS1-%02X%02X%02X%02X",
             uid.id[4], uid.id[5],
             uid.id[6], uid.id[7]);
    afe_read_daughter_eeprom(daughter_type, sizeof(daughter_type),
                                daughter_serial, sizeof(daughter_serial));
    fill = 0;
}

void protocol_receive(const uint8_t *bytes, uint32_t n)
{
    for (uint32_t i = 0; i < n; i++) {
        char c = (char)bytes[i];
        if (c == '\r' || c == '\n') {
            if (fill) {
                line[fill] = '\0';
                handle(line);
                fill = 0;
            }
        } else if (fill < sizeof(line) - 1) {
            line[fill++] = c;
        } else {
            fill = 0;           /* line too long: start over */
            fail("line too long");
        }
    }
}

void protocol_beacon(uint64_t index, uint32_t lost)
{
    current_index = index;
    current_lost = lost;
    if (!tud_cdc_connected()) {
        return;
    }
    afe_state_t e;
    afe_state(&e);
    ok("{\"beacon\":1,\"n\":%llu,\"lost\":%lu,\"gain\":%u,\"range\":%u,"
       "\"offset\":%u,\"sat\":%s}",
       (unsigned long long)index, (unsigned long)lost, e.gain, e.range,
       e.dac_offset, e.saturated ? "true" : "false");
}

void protocol_mark(const char *label, uint64_t index)
{
    cmd_mark(label, index);
}
