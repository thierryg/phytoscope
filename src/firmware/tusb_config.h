/*
 *  ==========================================================================
 *  PhytoScope — attribution — src/firmware/tusb_config.h
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
 *  tusb_config.h — TinyUSB device stack configuration.
 *
 *  The board presents itself as a composite device: a class 2 audio input
 *  (the measurement stream) and a virtual serial port (the control port).
 *  No driver is needed on any current system — Windows 10 and later, macOS,
 *  and any recent Linux kernel.
 *
 *  See sources/usb/reference.html for what these settings produce on the
 *  wire, descriptor by descriptor.
 *
 *  MIT licence — Bretagne Namasté
 * ------------------------------------------------------------------------ */
#ifndef _TUSB_CONFIG_H_
#define _TUSB_CONFIG_H_

/* RP2350: TinyUSB handles it through the "rp2040" port, which is shared by
 * both chips. This constant does not name the silicon but the family of USB
 * controllers, which is the same on RP2040 and RP2350.                     */
#define CFG_TUSB_MCU                OPT_MCU_RP2040
#define CFG_TUSB_OS                 OPT_OS_PICO
#define CFG_TUSB_RHPORT0_MODE       OPT_MODE_DEVICE

#define CFG_TUD_ENDPOINT0_SIZE      64

/* --- enabled interfaces -------------------------------------------------- */
#define CFG_TUD_AUDIO               1
#define CFG_TUD_CDC                 1
#define CFG_TUD_MSC                 0
#define CFG_TUD_HID                 0
#define CFG_TUD_MIDI                0
#define CFG_TUD_VENDOR              0

/* --- virtual serial port ------------------------------------------------- */
#define CFG_TUD_CDC_RX_BUFSIZE      256
#define CFG_TUD_CDC_TX_BUFSIZE      512

/* --- measurement stream --------------------------------------------------
 *  Four channels of 24 bits at 250 Hz come to 3 kB/s. A sample set is
 *  4 x 3 = 12 bytes, and at 250 Hz one becomes available every 4 ms: in the
 *  steady state three frames out of four carry nothing and the fourth
 *  carries twelve bytes. The frame is therefore VARIABLE in length — see the
 *  drain loop in main.c — and a host-side reader must not assume otherwise.
 *
 *  THE PACKET SIZE
 *
 *  The drain loop fills a frame with whole sample sets and stops when the
 *  next one would not fit, so the endpoint size is a hard ceiling on the
 *  rate the board can sustain:
 *
 *      rate x 12 bytes <= packet size x 1000 frames/s
 *
 *  256 bytes gives 21 sample sets — 252 bytes used, 4 wasted — and therefore
 *  a ceiling near 21 kHz. It was chosen with a comment claiming it absorbed
 *  "the 1 kHz and 32 kHz modes without reconfiguring the stack", and it did
 *  not: above 21 kHz the loop left samples in the ring, where they were
 *  counted as lost. That was divergence 11.2 of the USB reference, and it
 *  was a claim about a mode nobody could select, which is how it went
 *  unnoticed.
 *
 *  384 = 32 x 12 exactly: the 32 kHz mode, with nothing wasted. Full speed
 *  allows a single isochronous endpoint up to 1023 bytes per frame, so this
 *  reserves 37 % of what one endpoint may ask for and leaves the control
 *  port comfortable beside it.
 *
 *  What it costs: a host reserves 384 bytes of every frame from the moment
 *  it selects alternate setting 1, whether or not they are used — 384 kB/s
 *  of the bus held for a stream that currently carries 3. That is the price
 *  of a descriptor that does not lie, and it is payable on a bus running at
 *  three parts in a thousand of its capacity. Alternate setting 0 reserves
 *  nothing, which is what the board sits in when nobody is capturing.
 * ------------------------------------------------------------------------ */

/*  The audio function is written out by hand in usb_descriptors.c rather
 *  than taken from TinyUSB's microphone template: the template declared a
 *  mute and a volume this board has not got. The length below is the sum of
 *  the thirteen descriptors it writes, and a TU_VERIFY_STATIC there checks
 *  the bytes against it.                                                   */
#define CFG_TUD_AUDIO_FUNC_1_DESC_LEN                                        \
    (TUD_AUDIO_DESC_IAD_LEN + TUD_AUDIO_DESC_STD_AC_LEN                      \
     + TUD_AUDIO_DESC_CS_AC_LEN + TUD_AUDIO_DESC_CLK_SRC_LEN                 \
     + TUD_AUDIO_DESC_INPUT_TERM_LEN + TUD_AUDIO_DESC_OUTPUT_TERM_LEN        \
     + TUD_AUDIO_DESC_FEATURE_UNIT_FOUR_CHANNEL_LEN                          \
     + TUD_AUDIO_DESC_STD_AS_INT_LEN * 2 + TUD_AUDIO_DESC_CS_AS_INT_LEN      \
     + TUD_AUDIO_DESC_TYPE_I_FORMAT_LEN + TUD_AUDIO_DESC_STD_AS_ISO_EP_LEN   \
     + TUD_AUDIO_DESC_CS_AS_ISO_EP_LEN)
#define CFG_TUD_AUDIO_FUNC_1_N_AS_INT               1
#define CFG_TUD_AUDIO_FUNC_1_CTRL_BUF_SZ            64

#define CFG_TUD_AUDIO_ENABLE_EP_IN                  1
#define CFG_TUD_AUDIO_FUNC_1_N_BYTES_PER_SAMPLE_TX  3
#define CFG_TUD_AUDIO_FUNC_1_N_CHANNELS_TX          4
#define CFG_TUD_AUDIO_EP_SZ_IN                      384   /* 32 x 12 */
#define CFG_TUD_AUDIO_FUNC_1_EP_IN_SZ_MAX           CFG_TUD_AUDIO_EP_SZ_IN
#define CFG_TUD_AUDIO_FUNC_1_EP_IN_SW_BUF_SZ        (CFG_TUD_AUDIO_EP_SZ_IN * 4)

/*  Asynchronous clock: the board sets the cadence, not the host. Without it
 *  the operating system would resample the stream, and the time base of the
 *  whole instrument would stop meaning anything — a timestamp would be the
 *  host scheduler's opinion rather than a crystal's.
 *
 *  No feedback endpoint follows from that: feedback exists so that a host can
 *  be told to adjust its delivery rate, which only applies to output.       */
#define CFG_TUD_AUDIO_ENABLE_FEEDBACK_EP            0
#define CFG_TUD_AUDIO_FUNC_1_CLK_SRC_ASYNC          1

#endif /* _TUSB_CONFIG_H_ */
