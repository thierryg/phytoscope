/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/usb_descriptors.c
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
 *  usb_descriptors.c — the USB identity of the PhytoSense One board.
 *
 *  The board presents itself as a composite device:
 *
 *    - interfaces 0-1: a class 2 audio input (UAC2), four channels of
 *                      24 bits. This is the measurement stream. No driver is
 *                      needed: Windows 10 and later, macOS and Linux can all
 *                      read a standard audio input.
 *    - interfaces 2-3: a virtual serial port (CDC-ACM). This is the control
 *                      dialogue, described in protocol.c.
 *
 *  Choosing UAC2 over a proprietary protocol is not a convenience: it is what
 *  guarantees the board will still be readable in ten years, by any software,
 *  even if the program shipped with it has gone.
 *
 *  The serial number is not invented. It is derived from the unique
 *  identifier burned into the QSPI flash, so it belongs to one board and is
 *  stable for its whole life. It is what PhytoScope writes into the header of
 *  every recording.
 *
 *  These descriptors are documented field by field, with their wire bytes, in
 *  sources/usb/reference.html.
 *
 *  MIT licence — Bretagne Namasté — https://bretagne-namaste.com
 * ------------------------------------------------------------------------ */
#include "tusb.h"
#include "pico/unique_id.h"

#include "afe.h"          /* AFE_RATE_HZ, AFE_CHANNELS — the one source */

#include <string.h>

/* ---------------------------------------------------------------------------
 *  Identifiers
 *
 *  The VID/PID pair below comes from the free pid.codes range, set aside for
 *  open hardware projects. It must NOT be used for a product that is sold:
 *  obtain an identifier of your own from the USB-IF, or a sub-allocation from
 *  a vendor.
 *
 *  It is also the pair PhytoScope's diagnostic routine looks for in order to
 *  recognise the board — see phytoscope/core/usbdiag.py. Anyone forking this
 *  firmware for a different board must change the product identifier: two
 *  boards answering to the same pair are matched by the same rules, and the
 *  first tool to run will report whichever it happened to find first.
 * ------------------------------------------------------------------------ */
#define PHYTO_VID   0x1209      /* pid.codes - open hardware projects        */
#define PHYTO_PID   0x7A01      /* PhytoSense One                            */
#define PHYTO_BCD   0x0100      /* firmware version 1.0.0                    */

/* ---------------------------------------------------------------------------
 *  Endpoints
 *
 *  Numbered by hand so that the address map stays readable in a Wireshark
 *  capture, and identical from one firmware version to the next.
 * ------------------------------------------------------------------------ */
#define EP_AUDIO_IN     0x81    /* measurement stream to host, isochronous   */
#define EP_CDC_NOTIF    0x82    /* serial-state notifications                */
#define EP_CDC_OUT      0x03    /* commands received                         */
#define EP_CDC_IN       0x83    /* replies sent                              */

/* Measurement frame size: 4 channels x 3 bytes, with headroom for the higher
 * rates. Must stay aligned with CFG_TUD_AUDIO_EP_SZ_IN.                     */
#define EP_AUDIO_SZ     CFG_TUD_AUDIO_EP_SZ_IN

/* ---------------------------------------------------------------------------
 *  Device descriptor
 * ------------------------------------------------------------------------ */
static const tusb_desc_device_t desc_device = {
    .bLength            = sizeof(tusb_desc_device_t),
    .bDescriptorType    = TUSB_DESC_DEVICE,
    .bcdUSB             = 0x0200,

    /* Composite: the class is declared per interface, not globally. The
     * Interface Association Descriptor then groups the interfaces that
     * belong together. Without exactly these three values, Windows binds a
     * single driver to the first interface it recognises and never reaches
     * the CDC control port. Linux binds per-interface anyway, which is why
     * this class of bug survives testing on Linux.                          */
    .bDeviceClass       = TUSB_CLASS_MISC,
    .bDeviceSubClass    = MISC_SUBCLASS_COMMON,
    .bDeviceProtocol    = MISC_PROTOCOL_IAD,

    .bMaxPacketSize0    = CFG_TUD_ENDPOINT0_SIZE,

    .idVendor           = PHYTO_VID,
    .idProduct          = PHYTO_PID,
    .bcdDevice          = PHYTO_BCD,

    .iManufacturer      = 0x01,
    .iProduct           = 0x02,
    .iSerialNumber      = 0x03,

    .bNumConfigurations = 0x01
};

const uint8_t *tud_descriptor_device_cb(void)
{
    return (const uint8_t *) &desc_device;
}

/* ---------------------------------------------------------------------------
 *  Configuration descriptor
 *
 *  The order matters: audio first, because it is the main function and
 *  because some older hosts stop exploring past the first interface they know
 *  how to handle. On such a host the instrument still measures and loses only
 *  the control port, which is the more useful half to keep.
 * ------------------------------------------------------------------------ */
enum {
    ITF_NUM_AUDIO_CONTROL = 0,
    ITF_NUM_AUDIO_STREAM,
    ITF_NUM_CDC_CONTROL,
    ITF_NUM_CDC_DATA,
    ITF_NUM_TOTAL
};

/*  Entity identifiers inside the audio function. A host addresses entities
 *  by these numbers in every class request, and section 5 of
 *  sources/usb/reference.html documents them — so they are kept at the
 *  values TinyUSB's microphone template used, even now that the descriptor
 *  is written out by hand. Renumbering them would break nothing in the
 *  firmware and every capture taken with the old one.                      */
#define ENTITY_INPUT_TERMINAL   0x01
#define ENTITY_FEATURE_UNIT     0x02
#define ENTITY_OUTPUT_TERMINAL  0x03
#define ENTITY_CLOCK_SOURCE     0x04

/* ---------------------------------------------------------------------------
 *  The audio function, written out by hand
 *
 *  TinyUSB ships `TUD_AUDIO_MIC_FOUR_CH_DESCRIPTOR`, and this board used it
 *  until 2026-09-23. A template is the right way to start and the wrong way
 *  to finish: it described a microphone, and one of the things it described
 *  was not true of this board.
 *
 *  The template declares the feature unit's mute and volume as READ/WRITE,
 *  on the master and on all four channels. Nothing on this board is wired to
 *  them — the gain is set through the control port, in decade steps chosen by
 *  a relay tree — so a host offered a volume slider that did nothing, and an
 *  application could set it, read it back unchanged, and draw its own
 *  conclusions. Recorded as divergence 11.3 in the USB reference, and the
 *  only honest fix was to stop declaring what the hardware has not got.
 *
 *  Writing the thirteen descriptors out costs forty lines and buys three
 *  things: `bmControls` says what is true, the reasoning sits next to the
 *  field it explains, and `TU_VERIFY_STATIC` below turns any disagreement
 *  between the bytes and the arithmetic into a compile error rather than a
 *  host that stops enumerating halfway through a configuration descriptor.
 *
 *  The entity graph is unchanged, and deliberately so: entity numbers are
 *  what a host addresses in a class request, and `0x01`, `0x02`, `0x04` are
 *  the numbers section 5 of the reference documents.
 *
 *      clock source 0x04  ─┐
 *      input terminal 0x01 ├─→ feature unit 0x02 ─→ output terminal 0x03
 *                          ┘        (no controls)        (USB streaming)
 * ------------------------------------------------------------------------ */

/*  The class-specific AC interface header carries the total length of the
 *  entity descriptors that follow it — not of itself. Getting this wrong
 *  gives a host that reads past the end of one descriptor into the next.   */
#define PHYTO_AC_ENTITIES_LEN  (TUD_AUDIO_DESC_CLK_SRC_LEN                 \
                              + TUD_AUDIO_DESC_INPUT_TERM_LEN              \
                              + TUD_AUDIO_DESC_OUTPUT_TERM_LEN             \
                              + TUD_AUDIO_DESC_FEATURE_UNIT_FOUR_CHANNEL_LEN)

#define PHYTO_AUDIO_DESC_LEN   (TUD_AUDIO_DESC_IAD_LEN                     \
                              + TUD_AUDIO_DESC_STD_AC_LEN                  \
                              + TUD_AUDIO_DESC_CS_AC_LEN                   \
                              + PHYTO_AC_ENTITIES_LEN                      \
                              + TUD_AUDIO_DESC_STD_AS_INT_LEN * 2          \
                              + TUD_AUDIO_DESC_CS_AS_INT_LEN               \
                              + TUD_AUDIO_DESC_TYPE_I_FORMAT_LEN           \
                              + TUD_AUDIO_DESC_STD_AS_ISO_EP_LEN           \
                              + TUD_AUDIO_DESC_CS_AS_ISO_EP_LEN)

#define CONFIG_TOTAL_LEN  (TUD_CONFIG_DESC_LEN                \
                         + PHYTO_AUDIO_DESC_LEN               \
                         + TUD_CDC_DESC_LEN)

static const uint8_t desc_configuration[] = {
    /* Configuration: 4 interfaces, bus-powered, 500 mA. The board typically
     * draws 180 mA; the margin covers the inrush as the isolated supplies
     * come up. A hub that granted only 100 mA would cut the port during it,
     * giving an enumeration that succeeds and then drops.                   */
    TUD_CONFIG_DESCRIPTOR(1, ITF_NUM_TOTAL, 0, CONFIG_TOTAL_LEN,
                          TUSB_DESC_CONFIG_ATT_REMOTE_WAKEUP, 500),

    /* -- the audio function, interfaces 0 and 1 --------------------------- */

    /* Interface association: the two audio interfaces belong together. This
     * is what stops Windows binding one driver to interface 0 and leaving
     * the CDC port unclaimed.                                              */
    TUD_AUDIO_DESC_IAD(/*_firstitf*/ ITF_NUM_AUDIO_CONTROL, /*_nitfs*/ 2,
                       /*_stridx*/ 0x00),

    /* Standard AC interface: no endpoint of its own — control requests go
     * through endpoint 0.                                                  */
    TUD_AUDIO_DESC_STD_AC(/*_itfnum*/ ITF_NUM_AUDIO_CONTROL, /*_nEPs*/ 0x00,
                          /*_stridx*/ 4),

    /* Class-specific AC interface header. UAC 2.0, category "microphone" —
     * the category a host uses to decide which icon and which default
     * routing to offer, and an input of four channels is the nearest true
     * thing in the list.                                                   */
    TUD_AUDIO_DESC_CS_AC(/*_bcdADC*/ 0x0200,
                         /*_category*/ AUDIO_FUNC_MICROPHONE,
                         /*_totallen*/ PHYTO_AC_ENTITIES_LEN,
                         /*_ctrl*/ AUDIO_CS_AS_INTERFACE_CTRL_LATENCY_POS),

    /* Clock source 0x04: internal, FIXED. The rate is set by the analog
     * chain — 12.288 MHz / 2 / 4096 / 6 = 250 Hz — and nothing on the board
     * can change it, which is exactly what INT_FIX_CLK says. The frequency
     * is declared READABLE, and `tud_audio_get_req_entity_cb` below answers
     * it; declaring a control and then stalling it was divergence 11.1.    */
    TUD_AUDIO_DESC_CLK_SRC(/*_clkid*/ ENTITY_CLOCK_SOURCE,
                           /*_attr*/ AUDIO_CLOCK_SOURCE_ATT_INT_FIX_CLK,
                           /*_ctrl*/ (AUDIO_CTRL_R
                                      << AUDIO_CLOCK_SOURCE_CTRL_CLK_FRQ_POS),
                           /*_assocTerm*/ ENTITY_INPUT_TERMINAL,
                           /*_stridx*/ 0x00),

    /* Input terminal 0x01: four logical channels, no predefined spatial
     * position — these are electrodes on a plant, not a surround rig, and
     * claiming FRONT_LEFT for channel 1 would invite a host to mix them.   */
    TUD_AUDIO_DESC_INPUT_TERM(/*_termid*/ ENTITY_INPUT_TERMINAL,
                              /*_termtype*/ AUDIO_TERM_TYPE_IN_GENERIC_MIC,
                              /*_assocTerm*/ ENTITY_OUTPUT_TERMINAL,
                              /*_clkid*/ ENTITY_CLOCK_SOURCE,
                              /*_nchannelslogical*/ AFE_CHANNELS,
                              /*_channelcfg*/ AUDIO_CHANNEL_CONFIG_NON_PREDEFINED,
                              /*_idxchannelnames*/ 0x00,
                              /*_ctrl*/ (AUDIO_CTRL_R
                                         << AUDIO_IN_TERM_CTRL_CONNECTOR_POS),
                              /*_stridx*/ 0x00),

    /* Feature unit 0x02: present, and declaring NO control.
     *
     * It stays in the graph because the output terminal names it as its
     * source and because a UAC2 input function is conventionally read
     * through one; it declares nothing because the board has no mute and no
     * host-settable volume. AUDIO_CTRL_NONE on the master and on all four
     * channels means a host shows no slider at all, rather than a slider
     * that does nothing (divergence 11.3, settled 2026-09-23).
     *
     * Gain IS adjustable — x2, x10, x20, x200 — through the control port's
     * `gain` command, in decade steps chosen by a relay tree. That is not a
     * volume control: it changes the measurement's full scale, and a host
     * that moved it without recording the change would invalidate every
     * sample that followed.                                                */
    TUD_AUDIO_DESC_FEATURE_UNIT_FOUR_CHANNEL(
        /*_unitid*/ ENTITY_FEATURE_UNIT, /*_srcid*/ ENTITY_INPUT_TERMINAL,
        /*_ctrlch0master*/ AUDIO_CTRL_NONE, /*_ctrlch1*/ AUDIO_CTRL_NONE,
        /*_ctrlch2*/ AUDIO_CTRL_NONE, /*_ctrlch3*/ AUDIO_CTRL_NONE,
        /*_ctrlch4*/ AUDIO_CTRL_NONE, /*_stridx*/ 0x00),

    /* Output terminal 0x03: where the stream leaves for the host.          */
    TUD_AUDIO_DESC_OUTPUT_TERM(/*_termid*/ ENTITY_OUTPUT_TERMINAL,
                               /*_termtype*/ AUDIO_TERM_TYPE_USB_STREAMING,
                               /*_assocTerm*/ ENTITY_INPUT_TERMINAL,
                               /*_srcid*/ ENTITY_FEATURE_UNIT,
                               /*_clkid*/ ENTITY_CLOCK_SOURCE,
                               /*_ctrl*/ 0x0000, /*_stridx*/ 0x00),

    /* Alternate 0: no endpoint, no bandwidth. A host selects this when it is
     * not capturing, and it is what lets the board be plugged in all day
     * without reserving a slice of every frame.                            */
    TUD_AUDIO_DESC_STD_AS_INT(/*_itfnum*/ ITF_NUM_AUDIO_STREAM,
                              /*_altset*/ 0x00, /*_nEPs*/ 0x00,
                              /*_stridx*/ 0x00),

    /* Alternate 1: the streaming setting, with the isochronous endpoint.   */
    TUD_AUDIO_DESC_STD_AS_INT(/*_itfnum*/ ITF_NUM_AUDIO_STREAM,
                              /*_altset*/ 0x01, /*_nEPs*/ 0x01,
                              /*_stridx*/ 0x00),

    /* Class-specific AS interface: PCM, four physical channels.            */
    TUD_AUDIO_DESC_CS_AS_INT(/*_termid*/ ENTITY_OUTPUT_TERMINAL,
                             /*_ctrl*/ AUDIO_CTRL_NONE,
                             /*_formattype*/ AUDIO_FORMAT_TYPE_I,
                             /*_formats*/ AUDIO_DATA_FORMAT_TYPE_I_PCM,
                             /*_nchannelsphysical*/ AFE_CHANNELS,
                             /*_channelcfg*/ AUDIO_CHANNEL_CONFIG_NON_PREDEFINED,
                             /*_stridx*/ 0x00),

    /* Type I format: 3 bytes per sample, 24 bits of them significant. The
     * converter is a 24-bit sigma-delta; there is no padding to declare.   */
    TUD_AUDIO_DESC_TYPE_I_FORMAT(/*_subslotsize*/ 3, /*_bitresolution*/ 24),

    /* The isochronous IN endpoint. ASYNCHRONOUS: the board sets the cadence,
     * the host follows. Interval 1 — one frame, one opportunity.           */
    TUD_AUDIO_DESC_STD_AS_ISO_EP(
        /*_ep*/ EP_AUDIO_IN,
        /*_attr*/ (uint8_t) ((uint8_t) TUSB_XFER_ISOCHRONOUS
                             | (uint8_t) TUSB_ISO_EP_ATT_ASYNCHRONOUS
                             | (uint8_t) TUSB_ISO_EP_ATT_DATA),
        /*_maxEPsize*/ EP_AUDIO_SZ, /*_interval*/ 0x01),

    /* Class-specific AS ISO endpoint. NON_MAX_PACKETS_OK is not decoration:
     * the frame is variable in length, because at 250 Hz three frames in
     * four carry nothing at all.                                           */
    TUD_AUDIO_DESC_CS_AS_ISO_EP(
        /*_attr*/ AUDIO_CS_AS_ISO_DATA_EP_ATT_NON_MAX_PACKETS_OK,
        /*_ctrl*/ AUDIO_CTRL_NONE,
        /*_lockdelayunit*/ AUDIO_CS_AS_ISO_DATA_EP_LOCK_DELAY_UNIT_UNDEFINED,
        /*_lockdelay*/ 0x0000),

    /* -- the virtual serial port used for control, interfaces 2 and 3 ----- */
    TUD_CDC_DESCRIPTOR(ITF_NUM_CDC_CONTROL, /* str */ 5,
                       EP_CDC_NOTIF, 8, EP_CDC_OUT, EP_CDC_IN, 64),
};

/*  The bytes and the arithmetic must agree. A configuration descriptor whose
 *  wTotalLength is short leaves a host reading garbage after the last
 *  descriptor it believed in; one that is long leaves it waiting for bytes
 *  that never come. Neither failure names itself, and both are a compile
 *  error here instead.                                                     */
TU_VERIFY_STATIC(sizeof(desc_configuration) == CONFIG_TOTAL_LEN,
                 "the configuration descriptor is not the length it claims");

const uint8_t *tud_descriptor_configuration_cb(uint8_t index)
{
    (void) index;   /* only one configuration */
    return desc_configuration;
}

/* ---------------------------------------------------------------------------
 *  String descriptors
 *
 *  The serial number is built once, on the first request, from the flash's
 *  64-bit identifier. It takes the form PS1-XXXXXXXX, where the eight hex
 *  digits are the low 32 bits of that identifier — enough to be unique across
 *  any plausible production run, short enough to be copied onto a lab
 *  notebook by hand. Both halves matter: a serial nobody transcribes is a
 *  serial that never appears in the record of an experiment.
 * ------------------------------------------------------------------------ */
static char serial_str[13];     /* "PS1-4A17C302" plus the terminator       */

static void build_serial(void)
{
    if (serial_str[0] != '\0') {
        return;                 /* already built */
    }

    pico_unique_board_id_t uid;
    pico_get_unique_board_id(&uid);

    /* The last four bytes, in uppercase hexadecimal. */
    static const char hex[] = "0123456789ABCDEF";
    serial_str[0] = 'P';
    serial_str[1] = 'S';
    serial_str[2] = '1';
    serial_str[3] = '-';
    for (int i = 0; i < 4; i++) {
        uint8_t byte = uid.id[PICO_UNIQUE_BOARD_ID_SIZE_BYTES - 4 + i];
        serial_str[4 + i * 2]     = hex[(byte >> 4) & 0x0F];
        serial_str[4 + i * 2 + 1] = hex[byte & 0x0F];
    }
    serial_str[12] = '\0';
}

static const char *const strings[] = {
    (const char[]) { 0x09, 0x04 },      /* 0: English (en-US)               */
    "Bretagne Namaste",                 /* 1: manufacturer                  */
    "PhytoSense One",                   /* 2: product                       */
    serial_str,                         /* 3: serial number, built below    */
    "PhytoSense Measurement Input",     /* 4: the measurement stream        */
    "PhytoSense Control",               /* 5: the control port              */
};

/* Conversion buffer for the UTF-16 that USB expects. The first word carries
 * the length and the descriptor type; the characters follow.
 *
 * Widening one byte into one word is correct for ASCII and WRONG for any
 * multi-byte UTF-8 sequence, which is why the manufacturer string above is
 * written without its acute accent. That is a consequence of a cheap
 * conversion, not an oversight.                                            */
static uint16_t desc_str[32];

const uint16_t *tud_descriptor_string_cb(uint8_t index, uint16_t langid)
{
    (void) langid;

    size_t n;

    if (index == 0) {
        /* Language table: two raw bytes, no conversion. */
        memcpy(&desc_str[1], strings[0], 2);
        n = 1;
    } else {
        if (index >= TU_ARRAY_SIZE(strings)) {
            return NULL;
        }

        if (index == 3) {
            build_serial();
        }

        const char *src = strings[index];
        n = strlen(src);

        /* Truncate rather than overflow: a clipped name beats a smashed
         * stack. None of the strings above comes near the 31-character
         * limit, but the guard is there for whoever adds one.              */
        if (n > TU_ARRAY_SIZE(desc_str) - 1) {
            n = TU_ARRAY_SIZE(desc_str) - 1;
        }

        for (size_t i = 0; i < n; i++) {
            desc_str[1 + i] = (uint16_t) src[i];
        }
    }

    /* Total length in bytes, then the descriptor type. */
    desc_str[0] = (uint16_t) ((TUSB_DESC_STRING << 8) | (2 * n + 2));

    return desc_str;
}


/* ---------------------------------------------------------------------------
 *  Answering the class-specific requests the descriptors invite
 *
 *  A UAC2 device that declares a control has to be able to answer a request
 *  about it. TinyUSB ships a weak `tud_audio_get_req_entity_cb` whose whole
 *  body is a log line and `return false` — a stall. Until 2026-09-23 this
 *  firmware left that default in place, which meant the board stalled
 *  requests it had itself invited:
 *
 *    - clock source 0x04 declares its sample frequency READABLE;
 *    - input terminal 0x01 declares its connector cluster READABLE.
 *
 *  It also declared a mute and a volume on feature unit 0x02, because the
 *  template did; the descriptor no longer does, so there is nothing here to
 *  answer for them.
 *
 *  A permissive host carried on with the format it had read from the
 *  descriptors; a strict one refused to open the stream. The symptom was a
 *  device that enumerated perfectly, appeared as a four-channel capture
 *  device, and produced silence — with nothing in any log to point at a
 *  control transfer.
 *
 *  What we answer, and why
 *  -----------------------
 *
 *  **The truth, including where the truth is awkward.** The sample frequency
 *  answered is `AFE_RATE_HZ` — 250 Hz, the rate the converter actually runs
 *  at. Most host audio stacks will not accept a rate below 8 kHz, so a host
 *  may well refuse the stream on reading it. That refusal is the correct
 *  outcome: the alternative is to report a rate the board does not use, and
 *  then every timestamp the host computes from it is wrong, silently, for as
 *  long as the recording lasts. A host that refuses tells you at once; a host
 *  misled by a convenient lie tells you months later, if ever.
 *
 *  The RANGE reply carries a single sub-range with min = max = the rate and
 *  res = 0, which is how UAC2 says "this is fixed" — consistent with
 *  AUDIO_CLOCK_SOURCE_ATT_INT_FIX_CLK in the descriptor. A SET CUR asking
 *  for that same rate succeeds; any other value is refused rather than
 *  accepted and ignored.
 *
 *  Mute and volume are answered with fixed values — not muted, 0 dB, and a
 *  range that allows nothing else. They are declared read/write because
 *  TinyUSB's four-channel microphone template declares them so, and they are
 *  not wired to the analog chain: gain is set through the control port
 *  (`gain`, `range`). Answering a fixed value is better than stalling — a
 *  host that asks gets a coherent reply — and the single-value range is how
 *  the device says the slider cannot move. Declaring them read-only in the
 *  descriptor would be better still, and means writing the audio descriptor
 *  out by hand instead of using the template: recorded, not done here.
 * ------------------------------------------------------------------------ */

bool tud_audio_get_req_entity_cb(uint8_t rhport,
                                 tusb_control_request_t const *p_request)
{
    const uint8_t entity   = TU_U16_HIGH(p_request->wIndex);
    const uint8_t selector = TU_U16_HIGH(p_request->wValue);

    if (entity == ENTITY_CLOCK_SOURCE) {
        if (selector == AUDIO_CS_CTRL_SAM_FREQ) {
            if (p_request->bRequest == AUDIO_CS_REQ_CUR) {
                audio_control_cur_4_t reply = {
                    .bCur = (int32_t) AFE_RATE_HZ
                };
                return tud_audio_buffer_and_schedule_control_xfer(
                    rhport, p_request, &reply, sizeof(reply));
            }
            if (p_request->bRequest == AUDIO_CS_REQ_RANGE) {
                /* One sub-range, min = max, res = 0: a fixed rate. */
                audio_control_range_4_n_t(1) reply = {
                    .wNumSubRanges = 1,
                    .subrange[0] = {
                        .bMin = (int32_t) AFE_RATE_HZ,
                        .bMax = (int32_t) AFE_RATE_HZ,
                        .bRes = 0
                    }
                };
                return tud_audio_buffer_and_schedule_control_xfer(
                    rhport, p_request, &reply, sizeof(reply));
            }
        }
        /*  Not advertised as readable in the descriptor, but some hosts ask
         *  anyway. The clock is a crystal: it is valid whenever the board is
         *  powered, and there is nothing that could make it otherwise.     */
        if (selector == AUDIO_CS_CTRL_CLK_VALID
                && p_request->bRequest == AUDIO_CS_REQ_CUR) {
            audio_control_cur_1_t reply = { .bCur = 1 };
            return tud_audio_buffer_and_schedule_control_xfer(
                rhport, p_request, &reply, sizeof(reply));
        }
        return false;
    }

    /*  The feature unit declares no control (see the descriptor above), so
     *  there is nothing here to answer. A host that asks anyway gets a
     *  stall, which is the correct answer to a request about a control the
     *  device never offered — and it will not ask, because bmControls told
     *  it not to. Answering a polite fiction was the half-measure we tried
     *  first, on 2026-09-23 morning; removing the control from the
     *  descriptor is the whole one.                                        */

    if (entity == ENTITY_INPUT_TERMINAL
            && selector == AUDIO_TE_CTRL_CONNECTOR
            && p_request->bRequest == AUDIO_CS_REQ_CUR) {
        /*  Four channels, no predefined spatial position: these are
         *  electrodes on a plant, not a surround rig.                      */
        audio_desc_channel_cluster_t reply = {
            .bNrChannels = AFE_CHANNELS,
            .bmChannelConfig = 0,
            .iChannelNames = 0
        };
        return tud_audio_buffer_and_schedule_control_xfer(
            rhport, p_request, &reply, sizeof(reply));
    }

    return false;   /* stall: a control we never advertised */
}

bool tud_audio_set_req_entity_cb(uint8_t rhport,
                                 tusb_control_request_t const *p_request,
                                 uint8_t *pBuff)
{
    (void) rhport;

    const uint8_t entity   = TU_U16_HIGH(p_request->wIndex);
    const uint8_t selector = TU_U16_HIGH(p_request->wValue);

    /*  The only write we honour: setting the sample rate to the one rate the
     *  board has. Accepting any other value would be a lie with a delay
     *  fuse — the host would timestamp from a rate the converter never ran
     *  at. Refusing is the answer a host can act on.                       */
    if (entity == ENTITY_CLOCK_SOURCE
            && selector == AUDIO_CS_CTRL_SAM_FREQ
            && p_request->bRequest == AUDIO_CS_REQ_CUR
            && p_request->wLength == 4) {
        const int32_t asked = (int32_t) tu_unaligned_read32(pBuff);
        return asked == (int32_t) AFE_RATE_HZ;
    }

    /*  Nothing else is writable. The feature unit declares no control, so a
     *  write to it is refused rather than accepted and ignored: accepting it
     *  would let an application set a volume, read it back, and believe it.
     *  The gain IS adjustable — through the control port's `gain` command,
     *  which records the change in the session metadata, because it moves
     *  the measurement's full scale.                                       */
    return false;   /* stall */
}
