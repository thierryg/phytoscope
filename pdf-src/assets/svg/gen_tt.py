#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/assets/svg/gen_tt.py
#
#  Version   : 1.6.0
#  Date      : 2026-09-23
#  Publisher : Bretagne Namasté
#  Author    : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Website   : https://bretagne-namaste.com
#  Contact   : contact@bretagne-namaste.com
#  License   : MIT — see LICENSE.txt
#
#  SPDX-License-Identifier: MIT
#  end of attribution
#  ==========================================================================

"""
The illustrations that belong to the "Talking Tree" series.

This module reuses the primitives of gen.py (the palette, write, txt, box,
arrow, the fractal trees) and adds to them the figures specific to the three
volumes: instrumenting a tree, acquisition chains, software architectures,
turning a signal into language, and the epistemological diagrams.

Usage: python3 gen_tt.py
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gen import (  # noqa: E402
    NUIT, NUIT2, SEVE, SEVE_C, OR, OR_CL, IVOIRE, GRIS, TRAIT, BLEU, CUIVRE,
    write, txt, box, arrow, ARROWDEFS, fractal_tree,
)

MONO = "DejaVu Sans Mono, monospace"
SERIF = "Cormorant Garamond, serif"


# ---------------------------------------------------------------------------
#  Shared building blocks
# ---------------------------------------------------------------------------
def node(x, y, w, h, title, lines=(), fill="#FFFFFF", stroke=SEVE,
         tcol=NUIT, ts=11.5, ls=8.2):
    "A titled rectangular block, with centred detail lines."
    p = [box(x, y, w, h, fill=fill, stroke=stroke)]
    cx = x + w / 2
    if lines:
        p.append(txt(cx, y + 17, title, ts, tcol, weight="700"))
        for i, l in enumerate(lines):
            p.append(txt(cx, y + 32 + i * 12.5, l, ls, GRIS))
    else:
        p.append(txt(cx, y + h / 2 + 4, title, ts, tcol, weight="700"))
    return p


def band(x, y, w, h, label, fill=NUIT, tcol=OR_CL, ts=8.0):
    "A grouping band (a layer, a stage, a zone)."
    return [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="none" '
        f'stroke="{fill}" stroke-width="1.2" stroke-dasharray="5 4" opacity="0.55"/>',
        f'<rect x="{x+10}" y="{y-9}" width="{len(label)*5.6+16}" height="18" rx="9" '
        f'fill="{fill}"/>',
        txt(x + 18 + len(label) * 2.8, y + 3.5, label, ts, tcol,
            weight="700", spacing="1.2"),
    ]


def canopy_tree(cx, base_y, height, seed=7, color="#2C5D45", depth=9,
                trunk_ratio=0.34, spread=1.05, leaf=SEVE_C, leaves=True):
    """A broad deciduous tree — a short trunk, a spreading crown.

    The `fractal_tree` primitive of gen.py starts from a single segment as tall
    as the whole tree, which produces a “Y” silhouette. Here the trunk is only
    a third of the height and divides into three scaffold limbs, which gives
    the rounded crown of an oak or of a park plane tree.
    """
    import random as _r
    rng = _r.Random(seed)
    parts = []

    def rec(x, y, ang, ln, d, w):
        if d == 0 or ln < 3.5:
            return
        x2 = x + math.cos(ang) * ln
        y2 = y + math.sin(ang) * ln
        parts.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="{color}" stroke-width="{w:.2f}" stroke-linecap="round"/>')
        if leaves and d <= 4:
            for _ in range(rng.randint(1, 3)):
                rr = rng.uniform(2.0, 5.2)
                ox, oy = rng.uniform(-9, 9), rng.uniform(-9, 9)
                parts.append(f'<circle cx="{x2+ox:.1f}" cy="{y2+oy:.1f}" r="{rr:.1f}" '
                             f'fill="{leaf}" opacity="{rng.uniform(.30,.72):.2f}"/>')
        n = 3 if d > 5 else (2 if d > 2 else rng.choice([1, 2, 2]))
        for i in range(n):
            off = (i - (n - 1) / 2.0) * rng.uniform(.34, .52) * spread
            na = ang + off + rng.uniform(-.14, .14)
            rec(x2, y2, na, ln * rng.uniform(.66, .80), d - 1, w * .66)

    tl = height * trunk_ratio
    ty = base_y - tl
    parts.append(f'<line x1="{cx}" y1="{base_y}" x2="{cx}" y2="{ty:.1f}" '
                 f'stroke="{color}" stroke-width="{height*0.085:.1f}" stroke-linecap="round"/>')
    for i in range(3):
        a = -math.pi / 2 + (i - 1) * rng.uniform(.40, .56)
        rec(cx, ty, a, (height - tl) * rng.uniform(.50, .62), depth,
            height * 0.085 * 0.66)
    return "\n".join(parts)


def dashline(x1, y1, x2, y2, color=TRAIT, sw=1.3, dash="5 4"):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{sw}" stroke-dasharray="{dash}"/>')


def axes(x0, y0, w, h, xlab="", ylab=""):
    p = [f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y0-h}" stroke="{GRIS}" stroke-width="1.5"/>',
         f'<line x1="{x0}" y1="{y0}" x2="{x0+w}" y2="{y0}" stroke="{GRIS}" stroke-width="1.5"/>']
    if xlab:
        p.append(txt(x0 + w, y0 + 18, xlab, 8, GRIS, anchor="end"))
    if ylab:
        p.append(txt(x0 - 6, y0 - h - 6, ylab, 8, GRIS, anchor="start"))
    return p


# =============================================================================
#  1. THE INSTRUMENTED TREE — the sensor map
# =============================================================================
def tt_sensor_map():
    W, H = 900, 640
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']

    # Sol
    p.append(f'<path d="M0,520 Q220,506 450,514 T900,520 L900,640 L0,640 Z" '
             f'fill="#E6E2D2"/>')
    p.append(f'<line x1="0" y1="518" x2="900" y2="518" stroke="{GRIS}" stroke-width="1.2"/>')

    # The tree — deliberately kept short, to clear the title
    p.append(canopy_tree(430, 520, 300, seed=23, color="#2F5F47", depth=8,
                         trunk_ratio=0.46, leaf="#6FA98A"))

    # Racines
    for a, l in ((200, 150), (222, 190), (248, 130), (292, 190), (318, 150), (342, 120)):
        ar = math.radians(a)
        p.append(f'<path d="M430,518 q{math.cos(ar)*l*0.5:.0f},{-math.sin(ar)*l*0.5+28:.0f} '
                 f'{math.cos(ar)*l:.0f},{-math.sin(ar)*l+18:.0f}" fill="none" '
                 f'stroke="#6B5A42" stroke-width="3" stroke-linecap="round" opacity="0.85"/>')

    # The sensor labels: (x, y, anchor_x, anchor_y, code, label, quantity)
    sensors = [
        (92,  118, 388, 236, "S1", "Climate sensor",  "air T° · RH · pressure"),
        (92,  206, 398, 300, "S2", "Light / PAR",       "lux · µmol·m⁻²·s⁻¹"),
        (92,  294, 384, 268, "S3", "Anemometer",          "wind speed · direction"),
        (92,  382, 413, 420, "S4", "Trunk electrodes",    "bioelectric ΔV (mV)"),
        (630, 118, 472, 238, "S5", "Acoustic sensor",  "20 Hz – 200 kHz"),
        (630, 206, 447, 396, "S6", "Dendrometer",         "Δ circumference (µm)"),
        (630, 294, 447, 456, "S7", "Sap flow",        "flux density (cm·h⁻¹)"),
        (630, 382, 528, 512, "S8", "Soil probe",        "soil T° · volumetric θ · EC"),
    ]
    for x, y, ax_, ay, code, name, unit in sensors:
        p += node(x, y, 178, 62, name, (unit,), stroke=BLEU, ts=10.2, ls=7.6)
        p.append(f'<circle cx="{x+178 if x < 400 else x}" cy="{y+31}" r="11" fill="{BLEU}"/>')
        p.append(txt(x + 178 if x < 400 else x, y + 34.5, code, 7.6, "#FFFFFF", weight="700"))
        sx = x + 189 if x < 400 else x - 11
        p.append(f'<path d="M{sx},{y+31} Q{(sx+ax_)/2},{(y+31+ay)/2} {ax_},{ay}" '
                 f'fill="none" stroke="{BLEU}" stroke-width="1.5" '
                 f'stroke-dasharray="4 3" opacity="0.8"/>')
        p.append(f'<circle cx="{ax_}" cy="{ay}" r="4.5" fill="{OR}" stroke="#FFF" stroke-width="1.4"/>')

    # The acquisition enclosure
    p += node(352, 556, 196, 56, "Acquisition node",
              ("MCU · ADC · clock · radio",), stroke=OR, fill="#FFF8E8", ts=10.5, ls=7.6)
    p.append(arrow(450, 500, 450, 552, OR, 2.4))
    p.append(txt(450, 630, "Solar supply + LiFePO₄ battery · LoRaWAN / Wi-Fi link",
                 8, GRIS))

    p.append(f'<rect x="0" y="0" width="{W}" height="72" fill="{IVOIRE}"/>')
    p.append(txt(450, 40, "THE INSTRUMENTED TREE", 13, NUIT, weight="700", spacing="3.4",
                 family=SERIF))
    p.append(txt(450, 60, "Eight families of measurement, one acquisition chain",
                 8.4, GRIS, style="italic"))
    write("tt-sensor-map.svg", "\n".join(p), W, H)


# =============================================================================
#  2. THE COMPLETE SYSTEM ARCHITECTURE
# =============================================================================
def tt_architecture():
    W, H = 920, 560
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(460, 34, "THE ARCHITECTURE OF A TALKING TREE", 12.5, NUIT,
                 weight="700", spacing="3", family=SERIF))

    y0 = 72
    layers = [
        (y0,       "1 · SENSING", SEVE, [
            ("Sensors", ("physical", "biological")),
            ("Conditioning", ("amplification", "50 Hz filtering")),
            ("Conversion", ("16–24-bit ADC", "timestamping")),
        ]),
        (y0 + 108, "2 · TRANSPORT", BLEU, [
            ("MCU node", ("ESP32 / RP2040", "deep sleep")),
            ("Radio", ("LoRaWAN · Wi-Fi", "NB-IoT")),
            ("Gateway", ("MQTT", "queue")),
        ]),
        (y0 + 216, "3 · PROCESSING", OR, [
            ("Time-series store", ("InfluxDB", "TimescaleDB")),
            ("Pre-processing", ("calibration", "anomaly detection")),
            ("Extraction", ("descriptors", "sliding windows")),
        ]),
        (y0 + 324, "4 · OUTPUT", CUIVRE, [
            ("Sonification", ("mapping → MIDI", "synthesis")),
            ("The language model", ("descriptors → text", "a constrained template")),
            ("Interface", ("web · audio", "on-site display")),
        ]),
    ]
    for ly, label, col, blocks in layers:
        p += band(44, ly, 832, 84, label, fill=col)
        for i, (t, sub) in enumerate(blocks):
            bx = 70 + i * 268
            p += node(bx, ly + 14, 224, 56, t, sub, stroke=col, ts=10.5, ls=7.4)
            if i < 2:
                p.append(arrow(bx + 226, ly + 42, bx + 264, ly + 42, col, 2.0,
                               "ahb" if col == BLEU else ("ahv" if col == SEVE else "ah")))
        if ly < y0 + 324:
            p.append(arrow(460, ly + 74, 460, ly + 104, GRIS, 2.2))

    p.append(txt(460, 540,
                 "Every stage can be replaced on its own: that is what makes the work reproducible.",
                 8.2, GRIS, style="italic"))
    write("tt-architecture.svg", "\n".join(p), W, H)


# =============================================================================
#  3. THE ANALOG ACQUISITION CHAIN (field electrophysiology)
# =============================================================================
def tt_acquisition_chain():
    W, H = 920, 400
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(460, 34, "THE BIOELECTRIC ACQUISITION CHAIN", 12, NUIT,
                 weight="700", spacing="2.8", family=SERIF))

    stages = [
        ("Electrodes", ("Ag/AgCl", "Z ≈ 1-50 MΩ"), SEVE),
        ("Instr. amp.", ("INA333 · AD8221", "Zin > 10 GΩ")),
        ("Low-pass filter", ("fₑ ≈ 10 Hz", "50 Hz rejection")),
        ("Converter", ("ADS1115 16-bit", "ADS1256 24-bit")),
        ("Microcontroller", ("timestamping", "averaging")),
    ]
    x = 40
    for i, st in enumerate(stages):
        t, sub = st[0], st[1]
        col = SEVE if i == 0 else (BLEU if i < 4 else OR)
        p += node(x, 110, 152, 74, t, sub, stroke=col, ts=10, ls=7.4)
        if i < len(stages) - 1:
            p.append(arrow(x + 154, 147, x + 186, 147, col, 2.2,
                           "ahv" if i == 0 else "ahb"))
        x += 186

    # A signal trace under each stage
    labels = [("noise + signal", 0.55), ("×1000", 0.9), ("smoothed", 0.55),
              ("quantized", 0.5), ("a dated series", 0.4)]
    x = 40
    for i, (lab, amp) in enumerate(labels):
        cx, cy = x + 76, 250
        pts = []
        for k in range(0, 130, 2):
            v = math.sin(k / 9.0) * 14 * amp
            if i == 0:
                v += math.sin(k * 2.7) * 9 + math.cos(k * 1.3) * 6
            if i == 3:
                v = round(v / 5) * 5
            pts.append(f"{cx-64+k},{cy - v:.1f}")
        p.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{BLEU}" '
                 f'stroke-width="1.5"/>')
        p.append(dashline(cx - 64, cy, cx + 66, cy))
        p.append(txt(cx, 286, lab, 7.6, GRIS, style="italic"))
        x += 186

    p += band(28, 92, 356, 106, "IN THE FIELD — inside an IP65 enclosure", fill=SEVE)
    p += band(400, 92, 500, 106, "DIGITAL", fill=BLEU)

    p.append(txt(460, 340,
                 "The gain sits as close to the electrode as it can: every length of cable before the amplifier is an aerial.",
                 8.4, CUIVRE, style="italic"))
    p.append(txt(460, 362,
                 "A common ground is mandatory; galvanic isolation if anything downstream touches the mains.",
                 8.4, GRIS, style="italic"))
    write("tt-acquisition-chain.svg", "\n".join(p), W, H)


# =============================================================================
#  4. FROM SIGNAL TO LANGUAGE — the three possible conversions
# =============================================================================
def tt_signal_to_language():
    W, H = 900, 560
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "THREE WAYS OF MAKING A SIGNAL “SPEAK”", 12, NUIT,
                 weight="700", spacing="2.6", family=SERIF))

    # Source commune
    p += node(330, 62, 240, 54, "A measured time series",
              ("x(t) — a dated physical quantity",), stroke=SEVE, fill="#EAF3ED", ts=10.5)

    routes = [
        (40, "A · SONIFICATION", SEVE,
         [("Parametric mapping", "quantity → pitch, timbre, duration"),
          ("Synthesis / MIDI", "an explicit, reversible rule")],
         "The signal determines the output entirely.",
         "Verifiable: one can work back from the sound to the data."),
        (330, "B · CLASSIFICATION", BLEU,
         [("Descriptors", "mean, slope, variance, spectrum"),
          ("A trained model", "→ a label: “water stress”")],
         "The signal selects among known states.",
         "Verifiable: a confusion matrix, a test set."),
        (620, "C · VERBALIZATION", CUIVRE,
         [("Descriptors → prompt", "numbers dropped into a template"),
          ("The language model", "→ sentences in natural language")],
         "The signal conditions, the model writes.",
         "Not verifiable word by word: the wording comes from the model."),
    ]
    for x, title, col, steps, claim, check in routes:
        p.append(f'<rect x="{x}" y="150" width="240" height="330" rx="9" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.8"/>')
        p.append(f'<rect x="{x}" y="150" width="240" height="26" rx="9" fill="{col}"/>')
        p.append(f'<rect x="{x}" y="167" width="240" height="9" fill="{col}"/>')
        p.append(txt(x + 120, 168, title, 8.4, "#FFFFFF", weight="700", spacing="1.6"))
        for i, (a, b) in enumerate(steps):
            yy = 196 + i * 76
            p.append(box(x + 14, yy, 212, 58, fill="#FBFAF4", stroke=TRAIT, sw=1.1))
            p.append(txt(x + 120, yy + 21, a, 9.6, NUIT, weight="700"))
            p.append(txt(x + 120, yy + 38, b, 7.4, GRIS))
            if i == 0:
                p.append(arrow(x + 120, yy + 60, x + 120, yy + 72, col, 1.8,
                               "ahv" if col == SEVE else ("ahb" if col == BLEU else "ah")))
        p.append(dashline(x + 14, 356, x + 226, 356))
        p.append(txt(x + 120, 378, claim, 8.2, NUIT, weight="700"))
        p.append(txt(x + 120, 400, "Control:", 7.4, col, weight="700"))
        for j, frag in enumerate(_wrap(check, 34)):
            p.append(txt(x + 120, 416 + j * 12, frag, 7.4, GRIS))
        p.append(arrow(x + 120, 118, x + 120, 146, col, 2.0,
                       "ahv" if col == SEVE else ("ahb" if col == BLEU else "ah")))

    p.append(f'<path d="M160,140 L450,120 L740,140" fill="none" stroke="{TRAIT}" stroke-width="1.2"/>')
    p.append(txt(450, 512,
                 "The share of information that really comes from the plant falls from A to C. The share of seduction rises.",
                 8.6, CUIVRE, style="italic"))
    p.append(txt(450, 534,
                 "None of the three is illegitimate — but they do not announce themselves the same way.",
                 8.4, GRIS, style="italic"))
    write("tt-signal-to-language.svg", "\n".join(p), W, H)


def _wrap(s, n):
    "Break a string into lines of at most n characters, on the spaces."
    out, cur = [], ""
    for w in s.split():
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        out.append(cur)
    return out


# =============================================================================
#  5. WHO IS SPEAKING? — the information budget
# =============================================================================
def tt_attribution():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 36, "WHO IS SPEAKING? THE INFORMATION BUDGET OF A GENERATED SENTENCE",
                 11.5, NUIT, weight="700", spacing="2.2", family=SERIF))
    p.append(txt(440, 58,
                 "A qualitative breakdown of where the content of a text output comes from",
                 8.2, GRIS, style="italic"))

    rows = [
        ("The tree's measurement", 12, SEVE,
         "The numbers: temperature, humidity, voltage. Really out of the sensor."),
        ("The engineer's choices", 23, BLEU,
         "Thresholds, windows, which quantities are kept and which are ignored."),
        ("The prompt template", 25, OR,
         "The role assigned to the model: “you are a two-hundred-year-old oak, speak in the first person”."),
        ("The language model", 40, CUIVRE,
         "Syntax, tone, metaphor, the feeling expressed: produced entirely by the model."),
    ]
    y = 92
    x0, bw = 280, 520
    for name, pct, col, note in rows:
        p.append(txt(x0 - 16, y + 21, name, 10, NUIT, anchor="end", weight="700"))
        p.append(f'<rect x="{x0}" y="{y}" width="{bw}" height="30" rx="5" fill="#EFEDE2"/>')
        p.append(f'<rect x="{x0}" y="{y}" width="{bw*pct/100:.0f}" height="30" rx="5" fill="{col}"/>')
        p.append(txt(x0 + bw * pct / 100 + 12, y + 21, f"{pct} %", 9.6, col, weight="700",
                     anchor="start"))
        for j, frag in enumerate(_wrap(note, 72)):
            p.append(txt(x0, y + 46 + j * 11.5, frag, 7.4, GRIS, anchor="start"))
        y += 84
    p.append(f'<rect x="{x0}" y="78" width="{bw}" height="{y-86}" rx="6" fill="none" '
             f'stroke="{TRAIT}" stroke-width="1"/>')

    p.append(f'<rect x="60" y="410" width="760" height="44" rx="6" fill="#FBF0E8" '
             f'stroke="#F0DCC9" stroke-width="1.2"/>')
    p.append(txt(440, 429,
                 "These proportions are a teaching illustration, not a measurement.",
                 8.6, CUIVRE, weight="700"))
    p.append(txt(440, 445,
                 "What can be shown is the order of magnitude: most of the text does not come from the tree.",
                 8.2, GRIS, style="italic"))
    write("tt-attribution.svg", "\n".join(p), W, H)


# =============================================================================
#  6. THE EPISTEMIC LADDER
# =============================================================================
def tt_epistemic_ladder():
    W, H = 840, 520
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(420, 36, "THE EPISTEMIC LADDER", 12.5, NUIT, weight="700",
                 spacing="3", family=SERIF))
    p.append(txt(420, 57, "Four registers that must never be allowed to slide into one another",
                 8.4, GRIS, style="italic"))

    steps = [
        ("MEASUREMENT", "#2F7D5E",
         "“The voltage between two points on the trunk varied by 7 mV in 40 minutes.”",
         "Reproducible by anyone with the same instrument. Numbered, dated, with a known uncertainty."),
        ("ESTABLISHED FACT", BLEU,
         "“Plants propagate electrical signals over long distances.”",
         "Published, replicated, the mechanism identified. Revisable, but solidly founded."),
        ("HYPOTHESIS", OR,
         "“This signal might encode the water status of the tree.”",
         "Framed to be tested. It predicts something falsifiable. Not yet settled."),
        ("INTERPRETATION", CUIVRE,
         "“The tree is expressing its thirst.”",
         "It gives the experience meaning. Legitimate as a story, worthless as proof. Not falsifiable."),
    ]
    y = 92
    for i, (name, col, ex, note) in enumerate(steps):
        wid = 700 - i * 0
        p.append(f'<rect x="70" y="{y}" width="{wid}" height="84" rx="7" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.8"/>')
        p.append(f'<rect x="70" y="{y}" width="8" height="84" rx="4" fill="{col}"/>')
        p.append(txt(96, y + 24, name, 10.6, col, anchor="start", weight="700", spacing="2"))
        p.append(txt(96, y + 45, ex, 9.2, NUIT, anchor="start", style="italic"))
        for j, frag in enumerate(_wrap(note, 92)):
            p.append(txt(96, y + 63 + j * 11.5, frag, 7.5, GRIS, anchor="start"))
        if i < 3:
            p.append(f'<path d="M420,{y+86} l0,14" stroke="{TRAIT}" stroke-width="1.6"/>')
            p.append(txt(438, y + 99, "↓ the slide starts here", 7, CUIVRE,
                         anchor="start", style="italic"))
        y += 100

    p.append(txt(420, 500,
                 "Every claim in this book is tied explicitly to one of these four rungs.",
                 8.4, NUIT, style="italic"))
    write("tt-epistemic-ladder.svg", "\n".join(p), W, H)


# =============================================================================
#  7. THE OPEN-SOURCE SOFTWARE STACK
# =============================================================================
def tt_stack():
    W, H = 900, 520
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "A FREE SOFTWARE STACK, FROM THE ELECTRODE TO THE VOICE", 12, NUIT,
                 weight="700", spacing="2.4", family=SERIF))

    layers = [
        ("Node firmware", SEVE, [("ESPHome", "YAML, OTA"), ("Tasmota", "native MQTT"),
                                    ("MicroPython", "prototyping")]),
        ("Collection & storage", BLEU, [("Mosquitto", "MQTT broker"),
                                       ("Telegraf", "ingestion agent"),
                                       ("InfluxDB", "time series")]),
        ("Analysis", OR, [("Python / NumPy", "descriptors"), ("scikit-learn", "classification"),
                         ("Grafana", "dashboards")]),
        ("Output", CUIVRE, [("SuperCollider", "real-time synthesis"),
                                 ("Pure Data", "a graphical patch"),
                                 ("Piper / Ollama", "voice · text, locally")]),
    ]
    y = 70
    for name, col, items in layers:
        p.append(f'<rect x="46" y="{y}" width="150" height="90" rx="7" fill="{col}"/>')
        for j, frag in enumerate(_wrap(name, 16)):
            p.append(txt(121, y + 42 + j * 15, frag, 10, "#FFFFFF", weight="700"))
        for i, (t, sub) in enumerate(items):
            bx = 224 + i * 216
            p += node(bx, y + 14, 196, 62, t, (sub,), stroke=col, ts=10.4, ls=7.6)
        p.append(f'<line x1="200" y1="{y+45}" x2="220" y2="{y+45}" stroke="{col}" stroke-width="2"/>')
        if y < 340:
            p.append(arrow(450, y + 92, 450, y + 106, GRIS, 2.0))
        y += 108

    p.append(f'<rect x="46" y="{y+6}" width="808" height="46" rx="7" fill="#F7F0DC" '
             f'stroke="#ECDCB0" stroke-width="1.2"/>')
    p.append(txt(450, y + 26, "The whole stage can be swapped out and self-hosted.", 9.4, NUIT,
                 weight="700"))
    p.append(txt(450, y + 42,
                 "No link depends on a proprietary service: that is what makes the experiment reproducible, and lasting.",
                 7.8, GRIS, style="italic"))
    write("tt-stack.svg", "\n".join(p), W, H)


# =============================================================================
#  8. ARTEFACTS IN THE FIELD
# =============================================================================
def tt_noise():
    W, H = 900, 520
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "WHAT CONTAMINATES A MEASUREMENT OUT OF DOORS", 12, NUIT,
                 weight="700", spacing="2.4", family=SERIF))

    # The composite trace
    x0, y0, wid, hei = 70, 250, 760, 150
    p += axes(x0, y0, wid, hei, "time (24 h)", "amplitude")
    base = []
    for k in range(0, wid, 3):
        t = k / wid * 24
        v = (math.sin((t - 6) / 24 * 2 * math.pi) * 38          # circadien
             + math.sin(t * 2.1) * 9                             # thermique
             + (18 if 9 < t < 11 else 0)                         # arrosage
             + math.sin(k * 1.7) * 5)                            # aliased 50 Hz
        base.append(f"{x0+k},{y0 - 20 - v:.1f}")
    p.append(f'<polyline points="{" ".join(base)}" fill="none" stroke="{BLEU}" stroke-width="1.8"/>')
    clean = " ".join(f"{x0+k},{y0 - 20 - math.sin((k/wid*24 - 6)/24*2*math.pi)*38:.1f}"
                     for k in range(0, wid, 3))
    p.append(f'<polyline points="{clean}" fill="none" stroke="{SEVE}" stroke-width="2.2" '
             f'stroke-dasharray="7 4"/>')
    p.append(txt(x0 + wid, y0 - 130, "— the presumed physiological signal", 8, SEVE, anchor="end"))
    p.append(txt(x0 + wid, y0 - 116, "— the signal actually recorded", 8, BLEU, anchor="end"))

    causes = [
        ("Electrode drift", "Polarization and oxidation of the contact: 10 to 40 % in the first half hour, then a slow drift over days.", CUIVRE),
        ("Temperature", "The amplifier gain and the tissue resistance both vary with T°. A day/night cycle reads as a “rhythm”.", OR),
        ("Surface moisture", "Dew, rain, fog: the film of water short-circuits the path through the tissue.", BLEU),
        ("Movement", "Wind, a passing walker, vibration: a micro-movement of the electrode = a large-amplitude artefact.", SEVE),
        ("Mains coupling", "50 Hz radiated by the grid and by street lamps. Unfiltered, it aliases into the useful band.", GRIS),
    ]
    y = 296
    for i, (t, d, col) in enumerate(causes):
        cx = 70 + (i % 2) * 400
        cy = y + (i // 2) * 62
        p.append(f'<rect x="{cx}" y="{cy}" width="376" height="54" rx="5" fill="#FFFFFF" '
                 f'stroke="{TRAIT}" stroke-width="1"/>')
        p.append(f'<rect x="{cx}" y="{cy}" width="5" height="54" rx="2.5" fill="{col}"/>')
        p.append(txt(cx + 16, cy + 17, t, 9.4, NUIT, anchor="start", weight="700"))
        for j, frag in enumerate(_wrap(d, 62)):
            p.append(txt(cx + 16, cy + 32 + j * 10.5, frag, 7.2, GRIS, anchor="start"))
        y_last = cy
    p.append(txt(450, 500,
                 "A signal that is clean in the laboratory becomes, outdoors, a sum in which the biological share is the smallest.",
                 8.4, CUIVRE, style="italic"))
    write("tt-noise.svg", "\n".join(p), W, H)


# =============================================================================
#  9. THE CIRCADIAN RHYTHM OF THE SIGNAL
# =============================================================================
def tt_circadian():
    W, H = 860, 420
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(430, 34, "WHAT THE TREE DOES WHILE NOBODY IS WATCHING",
                 11.5, NUIT, weight="700", spacing="2.2", family=SERIF))
    p.append(txt(430, 55, "Physiological quantities that can be measured over 24 hours",
                 8.2, GRIS, style="italic"))

    x0, y0, wid = 78, 340, 720
    # Bandes jour / nuit
    p.append(f'<rect x="{x0}" y="90" width="{wid*0.25:.0f}" height="250" fill="#E8E6DB"/>')
    p.append(f'<rect x="{x0+wid*0.79:.0f}" y="90" width="{wid*0.21:.0f}" height="250" fill="#E8E6DB"/>')
    p.append(txt(x0 + wid * 0.12, 106, "NIGHT", 7.6, GRIS, spacing="1.6"))
    p.append(txt(x0 + wid * 0.52, 106, "DAY", 7.6, OR, spacing="1.6"))
    p.append(txt(x0 + wid * 0.90, 106, "NIGHT", 7.6, GRIS, spacing="1.6"))

    p += axes(x0, y0, wid, 250, "solar time", "")
    for h in range(0, 25, 4):
        xx = x0 + wid * h / 24
        p.append(f'<line x1="{xx}" y1="{y0}" x2="{xx}" y2="{y0+5}" stroke="{GRIS}" stroke-width="1.2"/>')
        p.append(txt(xx, y0 + 18, f"{h:02d}h", 7.4, GRIS))

    curves = [
        ("Transpiration / sap flow", SEVE,
         lambda t: max(0, math.sin((t - 6) / 12 * math.pi)) ** 0.8 * 88),
        ("Trunk diameter", BLEU,
         lambda t: 44 + math.cos((t - 5) / 24 * 2 * math.pi) * 34),
        ("Bioelectric potential", CUIVRE,
         lambda t: 120 + math.sin((t - 9) / 24 * 2 * math.pi) * 42),
        ("Ultrasonic emissions", OR,
         lambda t: 170 + (26 if 12 < t < 17 else 4) + math.sin(t * 3) * 5),
    ]
    for i, (name, col, fn) in enumerate(curves):
        pts = " ".join(f"{x0 + wid*t/24:.1f},{y0 - fn(t):.1f}" for t in
                       [k / 6 for k in range(0, 145)])
        p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.1" '
                 f'opacity="0.92"/>')
        p.append(f'<circle cx="{x0+8}" cy="{y0 - fn(0.2):.1f}" r="3.4" fill="{col}"/>')
        p.append(txt(x0 + wid + 8, 132 + i * 18, "—", 9, col, anchor="start"))
        p.append(txt(x0 + wid + 22, 132 + i * 18, name, 7.6, GRIS, anchor="start"))

    p.append(txt(430, 388,
                 "These rhythms are measured and published. They are enough to produce a convincing “conversation” with no intention involved at all.",
                 8.2, GRIS, style="italic"))
    write("tt-circadian.svg", "\n".join(p), W, H)


# =============================================================================
# 10. A TIMELINE OF “TALKING” TREES AND PLANTS
# =============================================================================
def tt_timeline():
    W, H = 1000, 366
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(500, 34, "A HUNDRED AND FIFTY YEARS OF PLANTS THAT “ANSWER”", 12, NUIT,
                 weight="700", spacing="2.4", family=SERIF))

    y = 196
    p.append(f'<line x1="56" y1="{y}" x2="950" y2="{y}" stroke="{OR}" stroke-width="2.6"/>')

    events = [
        ("1873", "Burdon-Sanderson", "Electrical potential measured in the Venus flytrap.", SEVE, 1),
        ("1880", "Charles Darwin", "« The Power of Movement in Plants ».", SEVE, -1),
        ("1902", "J. C. Bose", "The crescograph; electrical responses of plants.", SEVE, 1),
        ("1966", "Cleve Backster", "A polygraph on a dracaena: the “Backster effect”.", CUIVRE, -1),
        ("1973", "Tompkins & Bird", "“The Secret Life of Plants”: a worldwide readership.", CUIVRE, 1),
        ("1975", "Horowitz et al.", "The Backster effect refuted (Science).", BLEU, -1),
        ("1976", "Damanhur", "The first plant sonification devices.", OR, 1),
        ("1997", "Suzanne Simard", "Carbon transfers between trees (Nature).", BLEU, -1),
        ("2010", "Happiness Brussels", "“Talking Tree”: a Brussels tree on social media.", CUIVRE, 1),
        ("2015", "Alexandre Ferran", "A word keyboard: the plant triggers language.", OR, -1),
        ("2018", "Toyota & Gilroy", "Long-distance calcium waves (Science).", BLEU, 1),
        ("2023", "Khait et al.", "Airborne sounds emitted under stress (Cell).", BLEU, -1),
        ("2023", "Karst et al.", "A critique of the “wood wide web” (Nat. Ecol. Evol.).", BLEU, 1),
        ("2025", "Droga5 / Agency for Nature", "“The Talking Tree”: sensors + a local LLM.", CUIVRE, -1),
    ]
    n = len(events)
    for i, (yr, who, what, col, side) in enumerate(events):
        x = 74 + i * (860 / (n - 1))
        p.append(f'<circle cx="{x:.0f}" cy="{y}" r="6.5" fill="{col}" stroke="{IVOIRE}" stroke-width="2"/>')
        ty = y - 24 if side > 0 else y + 24
        p.append(f'<line x1="{x:.0f}" y1="{y + (-7 if side>0 else 7)}" x2="{x:.0f}" '
                 f'y2="{ty + (8 if side>0 else -8)}" stroke="{col}" stroke-width="1.3"/>')
        by = ty - 74 if side > 0 else ty + 4
        p.append(f'<rect x="{x-62:.0f}" y="{by}" width="124" height="70" rx="5" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.2"/>')
        p.append(txt(x, by + 15, yr, 10, col, weight="700", family=SERIF))
        wl = _wrap(who, 21)[:2]
        for j, frag in enumerate(wl):
            p.append(txt(x, by + 27 + j * 9, frag, 6.9, NUIT, weight="700"))
        for j, frag in enumerate(_wrap(what, 26)[:3]):
            p.append(txt(x, by + 30 + len(wl) * 9 + j * 9, frag, 6.2, GRIS))

    p.append(txt(210, 344, "■ measured physiology", 7.6, SEVE, anchor="start"))
    p.append(txt(390, 344, "■ ecology & signalling", 7.6, BLEU, anchor="start"))
    p.append(txt(590, 344, "■ artistic and media installations", 7.6, CUIVRE, anchor="start"))
    write("tt-timeline.svg", "\n".join(p), W, H)


# =============================================================================
# 11. SAP FLOW — the thermal dissipation method
# =============================================================================
def tt_sap_flow():
    W, H = 820, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(410, 34, "MEASURING SAP FLOW — THE THERMAL DISSIPATION METHOD",
                 11, NUIT, weight="700", spacing="2", family=SERIF))
    p.append(txt(410, 55, "The Granier principle (1985)", 8.2, GRIS, style="italic"))

    # A cross-section of the trunk
    cx, cy = 250, 250
    p.append(f'<circle cx="{cx}" cy="{cy}" r="132" fill="#D9CDB4" stroke="#6B5A42" stroke-width="3"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="120" fill="#E8DFC8"/>')
    for r, col, lab in ((118, "#7A6B4E", "bark"), (106, "#9BAF7E", "cambium"),
                        (86, "#C9D9B4", "sapwood (conducting)"), (46, "#B39A6E", "heartwood")):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" opacity="0.9"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="#A88E62"/>')
    for r, lab, ly in ((124, "bark", -124), (96, "sapwood — this is where the water rises", -96),
                       (30, "heartwood (inert)", -20)):
        p.append(dashline(cx, cy + ly, cx + 190, cy + ly, GRIS, 1, "3 3"))
        p.append(txt(cx + 196, cy + ly + 3.5, lab, 7.6, GRIS, anchor="start"))

    # Sondes
    for dy, lab, col in ((-34, "heated probe", CUIVRE), (34, "reference probe", BLEU)):
        p.append(f'<rect x="{cx-6}" y="{cy+dy-4}" width="96" height="8" rx="4" fill="{col}"/>')
        p.append(f'<circle cx="{cx+90}" cy="{cy+dy}" r="6" fill="{col}"/>')
        p.append(txt(cx + 104, cy + dy + 3.5, lab, 7.6, col, anchor="start", weight="700"))
    p.append(txt(cx, cy + 6, "Δ 10 cm", 7.4, NUIT))
    p.append(f'<line x1="{cx+70}" y1="{cy-30}" x2="{cx+70}" y2="{cy+30}" stroke="{NUIT}" '
             f'stroke-width="1.2" stroke-dasharray="3 3"/>')

    # Relation
    p.append(box(520, 118, 268, 250, fill="#FFFFFF", stroke=OR))
    p.append(txt(654, 142, "What is computed", 10.4, OR, weight="700"))
    p.append(dashline(538, 154, 770, 154))
    formulas = [
        ("ΔT", "the temperature gap between the two probes"),
        ("ΔTₘ", "the maximum gap, measured at night at zero flow"),
        ("K = (ΔTₘ − ΔT) / ΔT", "the flow index, dimensionless"),
        ("u = 119 × K^1,231", "the flux density, in cm·h⁻¹"),
    ]
    yy = 176
    for f, d in formulas:
        p.append(txt(538, yy, f, 9.2, NUIT, anchor="start", weight="700", family=MONO))
        for j, frag in enumerate(_wrap(d, 40)):
            p.append(txt(538, yy + 14 + j * 10.5, frag, 7.2, GRIS, anchor="start"))
        yy += 48
    p.append(txt(654, 356, "The faster the sap rises, the more it cools the heated probe.",
                 7.6, SEVE, style="italic"))

    p.append(txt(410, 412,
                 "The reference probe cancels the ambient thermal drift: it is the gap, never the absolute value, that carries the information.",
                 8, GRIS, style="italic"))
    write("tt-sap-flow.svg", "\n".join(p), W, H)


# =============================================================================
# 12. CAVITATION AND ULTRASONIC EMISSIONS
# =============================================================================
def tt_cavitation():
    W, H = 880, 420
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "THE TREE THAT CRACKS: CAVITATION IN THE XYLEM", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    # Trois vaisseaux
    stages = [
        (90, "An unbroken column", "#9FC4DE", "The water is under tension (a negative pressure: −0.5 to −3 MPa). The column holds by cohesion."),
        (350, "Rupture", "#E2B9A0", "Water stress raises the tension. A bubble of air is drawn in through a pore: the column breaks."),
        (610, "Embolism + click", "#DED9CC", "The vessel empties. The release sends out an elastic wave: an ultrasonic click of 20 to 100 kHz."),
    ]
    for x, t, col, d in stages:
        p.append(f'<rect x="{x}" y="86" width="180" height="176" rx="14" fill="#F4F1E6" '
                 f'stroke="#6B5A42" stroke-width="2.4"/>')
        p.append(f'<rect x="{x+12}" y="98" width="156" height="152" rx="8" fill="{col}"/>')
        p.append(txt(x + 90, 76, t, 10, NUIT, weight="700"))
        for j, frag in enumerate(_wrap(d, 34)):
            p.append(txt(x + 90, 284 + j * 12, frag, 7.4, GRIS))
    # Bulle
    p.append(f'<circle cx="440" cy="168" r="30" fill="#FFFFFF" stroke="{CUIVRE}" stroke-width="2"/>')
    p.append(txt(440, 172, "air", 8.4, CUIVRE, weight="700"))
    p.append(f'<circle cx="700" cy="174" r="54" fill="#FFFFFF" stroke="{CUIVRE}" stroke-width="2"/>')
    for k in range(3):
        p.append(f'<circle cx="700" cy="174" r="{62+k*16}" fill="none" stroke="{CUIVRE}" '
                 f'stroke-width="1.6" opacity="{0.55-k*0.15:.2f}"/>')
    p.append(arrow(270, 174, 344, 174, GRIS, 2.2))
    p.append(arrow(530, 174, 604, 174, GRIS, 2.2))

    p.append(f'<rect x="90" y="332" width="700" height="58" rx="6" fill="#EAF0F7" '
             f'stroke="#D2E0EF" stroke-width="1.2"/>')
    p.append(txt(440, 352, "What this allows — and what it does not", 9.4, BLEU, weight="700"))
    p.append(txt(440, 369,
                 "The click rate is a reproducible indicator of water stress. It is mechanical, not intentional:",
                 7.8, GRIS))
    p.append(txt(440, 382,
                 "the tree is not “screaming”, it is fracturing hydraulically — which is measurable, and remarkable enough.",
                 7.8, GRIS))
    write("tt-cavitation.svg", "\n".join(p), W, H)


# =============================================================================
# 13. COMMUNICATION BY VOLATILE COMPOUNDS
# =============================================================================
def tt_voc():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "THE CHEMICAL ROUTE: VOLATILE ORGANIC COMPOUNDS", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(440, 55, "The only plant “communication” at a distance whose channel is clearly identified",
                 8, GRIS, style="italic"))

    p.append(f'<path d="M0,400 Q440,388 880,400 L880,470 L0,470 Z" fill="#E6E2D2"/>')
    p.append(canopy_tree(180, 402, 230, seed=11, color="#3C6B50", depth=7))
    p.append(canopy_tree(660, 402, 220, seed=29, color="#3C6B50", depth=7))

    # Herbivore
    p.append(f'<ellipse cx="196" cy="268" rx="17" ry="11" fill="{CUIVRE}"/>')
    p.append(txt(196, 296, "herbivore", 7.4, CUIVRE, weight="700"))

    # The cloud of VOCs
    for k in range(26):
        a = k * 0.62
        rx_ = 210 + math.cos(a) * (60 + k * 8)
        ry_ = 236 + math.sin(a) * (26 + k * 2.4)
        p.append(f'<circle cx="{rx_:.0f}" cy="{ry_:.0f}" r="{4.4 - k*0.07:.1f}" '
                 f'fill="{SEVE_C}" opacity="{0.75 - k*0.02:.2f}"/>')
    p.append(txt(430, 196, "terpenes · C6 aldehydes · methyl salicylate", 8.2, SEVE,
                 weight="700"))
    p.append(txt(430, 212, "emitted within minutes, carrying a few metres",
                 7.4, GRIS, style="italic"))

    boxes = [
        (60, 92, "Emission", "The wounded leaf releases a bouquet of volatiles whose composition depends on the kind of attack.", SEVE),
        (330, 92, "Reception", "Neighbouring tissues detect these molecules and prime their defences before they are touched.", BLEU),
        (600, 92, "A third beneficiary", "Parasitoids are drawn by the same bouquet: the information serves the predators too.", OR),
    ]
    for x, y, t, d, col in boxes:
        p.append(f'<rect x="{x}" y="{y}" width="222" height="72" rx="6" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.5"/>')
        p.append(txt(x + 111, y + 20, t, 10, col, weight="700"))
        for j, frag in enumerate(_wrap(d, 40)):
            p.append(txt(x + 111, y + 36 + j * 10.5, frag, 7.2, GRIS))

    p.append(f'<rect x="60" y="412" width="762" height="46" rx="6" fill="#FBF0E8" '
             f'stroke="#F0DCC9" stroke-width="1.2"/>')
    p.append(txt(440, 431, "“Communication”, or eavesdropping?", 9, CUIVRE, weight="700"))
    p.append(txt(440, 448,
                 "Nothing proves the emitter has any interest in warning: the neighbour may simply be picking up a signal that was never meant for it.",
                 7.6, GRIS, style="italic"))
    write("tt-voc.svg", "\n".join(p), W, H)


# =============================================================================
# 14. ANATOMY OF A SENSORS → TEXT PROMPT
# =============================================================================
def tt_prompt():
    W, H = 880, 560
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "ANATOMY OF A “SENSORS → SPEECH” PROMPT", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    blocks = [
        ("ROLE", CUIVRE,
         ["You are a two-hundred-year-old pedunculate oak.",
          "You speak in the first person, plainly."],
         "Written entirely by the human. This is where the character is born."),
        ("DATA", SEVE,
         ["air T° 14.2 °C (−1.8 in 3 h) · RH 81 %",
          "soil θ 0.19 m³/m³ (low threshold: 0.22) · PAR 340",
          "Δ trunk −41 µm over 6 h · wind 18 km/h"],
         "The only part that really comes from the tree."),
        ("CONSTRAINTS", BLEU,
         ["Three sentences at most. No invented emotion.",
          "Mention only the quantities you are given.",
          "If a datum is missing, say so instead of filling the gap."],
         "The guard rail: this is what separates honesty from fable."),
        ("OUTPUT", OR,
         ["“The soil around my roots is drying out:",
          "  0.19, below my comfort threshold. The air has",
          "  lost two degrees since noon.”"],
         "Traceable word by word to the numbers — and to nothing else."),
    ]
    y = 66
    for name, col, lines, note in blocks:
        h = 34 + len(lines) * 16 + 24
        p.append(f'<rect x="60" y="{y}" width="600" height="{h}" rx="6" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.6"/>')
        p.append(f'<rect x="60" y="{y}" width="600" height="22" rx="6" fill="{col}"/>')
        p.append(f'<rect x="60" y="{y+14}" width="600" height="8" fill="{col}"/>')
        p.append(txt(76, y + 15, name, 8, "#FFFFFF", anchor="start", weight="700", spacing="1.8"))
        for i, l in enumerate(lines):
            p.append(txt(78, y + 40 + i * 16, l, 8.2, NUIT, anchor="start", family=MONO))
        p.append(f'<path d="M672,{y+h/2} l-8,-6 v12 z" fill="{col}"/>')
        for j, frag in enumerate(_wrap(note, 30)):
            p.append(txt(684, y + h / 2 - 4 + j * 11, frag, 7.2, GRIS, anchor="start"))
        if y < 400:
            p.append(arrow(360, y + h + 2, 360, y + h + 14, col, 1.8,
                           "ahv" if col == SEVE else ("ahb" if col == BLEU else "ah")))
        y += h + 16

    p.append(f'<rect x="60" y="{y+4}" width="762" height="44" rx="6" fill="#F7F0DC" '
             f'stroke="#ECDCB0" stroke-width="1.2"/>')
    p.append(txt(440, y + 24, "The golden rule of the workshop", 9.2, OR, weight="700"))
    p.append(txt(440, y + 40,
                 "Every sentence produced must be traceable to a measured number. Whatever is not is decoration — and must be announced as such.",
                 7.6, GRIS, style="italic"))
    write("tt-prompt.svg", "\n".join(p), W, H)


# =============================================================================
# 15. FITTING ELECTRODES WITHOUT WOUNDING THE TREE
# =============================================================================
def tt_electrode_tree():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "FITTING SENSORS WITHOUT WOUNDING THE TREE", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    # The trunk in vertical section
    p.append(f'<rect x="150" y="80" width="130" height="330" rx="10" fill="#8A7455"/>')
    p.append(f'<rect x="162" y="80" width="106" height="330" fill="#A08A66"/>')
    for k in range(9):
        p.append(f'<path d="M162,{92+k*38} q26,10 52,0 t52,0" fill="none" stroke="#6B5A42" '
                 f'stroke-width="1.2" opacity="0.5"/>')
    p.append(txt(215, 432, "trunk", 8.4, GRIS))

    good = [
        (300, 104, "YES", "The electrode held under a wide elastic collar, never a tight one.", SEVE),
        (300, 186, "YES", "A loose loop of cable: the tree thickens, the cable must follow.", SEVE),
        (300, 268, "YES", "Check and loosen at every growing season.", SEVE),
    ]
    bad = [
        (590, 104, "NO", "A screw or a nail in the cambium: a way in for pathogens.", CUIVRE),
        (590, 186, "NO", "A strap tightened around the trunk: strangulation in the end.", CUIVRE),
        (590, 268, "NO", "A cable fixed permanently into the bark: it will end up inside the wood.", CUIVRE),
    ]
    for x, y, tag, d, col in good + bad:
        p.append(f'<rect x="{x}" y="{y}" width="248" height="66" rx="6" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.5"/>')
        p.append(f'<circle cx="{x+22}" cy="{y+22}" r="12" fill="{col}"/>')
        p.append(txt(x + 22, y + 25.5, "✓" if col == SEVE else "✗", 11, "#FFFFFF", weight="700"))
        p.append(txt(x + 42, y + 26, tag, 9, col, anchor="start", weight="700", spacing="1.4"))
        for j, frag in enumerate(_wrap(d, 42)):
            p.append(txt(x + 42, y + 42 + j * 10.5, frag, 7.3, GRIS, anchor="start"))

    # The correct electrode, on the drawing
    p.append(f'<rect x="146" y="150" width="138" height="14" rx="7" fill="none" '
             f'stroke="{SEVE}" stroke-width="2.6"/>')
    p.append(f'<rect x="258" y="146" width="22" height="22" rx="4" fill="{SEVE}"/>')
    p.append(f'<path d="M280,157 q30,26 18,60" fill="none" stroke="{SEVE}" stroke-width="2"/>')

    p.append(f'<rect x="150" y="352" width="698" height="72" rx="6" fill="#EAF3ED" '
             f'stroke="#CFE6DC" stroke-width="1.2"/>')
    p.append(txt(499, 372, "The principle that outranks every other", 9.4, "#2F7D5E", weight="700"))
    for j, frag in enumerate(_wrap(
            "The tree is a living being several centuries old, not a mounting bracket. Any measurement "
            "that shortens its life is a failed measurement, however good the signal obtained. "
            "When in doubt: a non-invasive sensor, or no sensor at all.", 104)):
        p.append(txt(499, 390 + j * 11.5, frag, 7.6, GRIS))
    write("tt-electrode-tree.svg", "\n".join(p), W, H)


# =============================================================================
# 16. NETWORK TOPOLOGY & THE ENERGY BUDGET
# =============================================================================
def tt_network_power():
    W, H = 900, 480
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "SELF-SUFFICIENCY AND THE RADIO LINK", 12, NUIT, weight="700",
                 spacing="3", family=SERIF))

    # --- The topology
    p += band(40, 70, 420, 200, "TOPOLOGY", fill=BLEU)
    p.append(canopy_tree(120, 232, 140, seed=5, color="#3C6B50", depth=6))
    p.append(canopy_tree(210, 234, 116, seed=17, color="#3C6B50", depth=6))
    for x, lbl in ((120, "node A"), (210, "node B")):
        p.append(f'<rect x="{x-14}" y="236" width="28" height="18" rx="3" fill="{OR}"/>')
        p.append(txt(x, 264, lbl, 7, GRIS))
    p += node(316, 158, 120, 54, "Gateway", ("LoRaWAN", "→ the Internet"), stroke=BLEU, ts=9.4, ls=7)
    for x in (120, 210):
        for k in range(3):
            p.append(f'<path d="M{x+16},{230-k*7} q28,{-14-k*6} {186-x+8},{-44-k*6}" '
                     f'fill="none" stroke="{BLEU}" stroke-width="1.2" opacity="{0.6-k*0.16:.2f}"/>')
    p.append(txt(250, 128, "868 MHz · SF9 · one message / 15 min", 7.4, BLEU, style="italic"))

    # --- The budget
    p += band(486, 70, 380, 200, "THE DAILY ENERGY BUDGET", fill=OR)
    rows = [
        ("Deep sleep (23 h 50)", 0.3, 7.2, SEVE),
        ("Measurements (96 wake-ups × 4 s)", 2.1, 50.4, BLEU),
        ("Radio transmissions (96 frames)", 4.0, 12.8, CUIVRE),
        ("Total consumed", None, 70.4, NUIT),
        ("Solar input 2 W (winter, 1.5 h equivalent)", None, 300.0, OR),
    ]
    y = 102
    maxv = 300.0
    for lab, cur, mah, col in rows:
        p.append(txt(500, y + 10, lab, 7.4, NUIT if col != OR else OR, anchor="start",
                     weight="700" if cur is None else "400"))
        p.append(f'<rect x="500" y="{y+14}" width="{340*mah/maxv:.0f}" height="11" rx="3" fill="{col}" '
                 f'opacity="{0.95 if cur is None else 0.75}"/>')
        p.append(txt(500 + 340 * mah / maxv + 8, y + 23, f"{mah:.0f} mAh", 7, col,
                     anchor="start", weight="700"))
        y += 33

    p.append(f'<rect x="40" y="298" width="826" height="66" rx="6" fill="#FFFFFF" '
             f'stroke="{TRAIT}" stroke-width="1.2"/>')
    p.append(txt(453, 318, "The sizing rule", 9.4, NUIT, weight="700"))
    for j, frag in enumerate(_wrap(
            "Size the battery for ten days without sun, and the panel to recharge in one overcast "
            "winter day. A 6 Ah LiFePO₄ and a 5 W panel hold this budget comfortably; it is the margin, "
            "not the average, that carries the installation through December.", 116)):
        p.append(txt(453, 336 + j * 11.5, frag, 7.6, GRIS))

    p.append(txt(450, 398, "Why LoRaWAN rather than Wi-Fi", 9.4, BLEU, weight="700"))
    for j, frag in enumerate(_wrap(
            "A range of several kilometres in open ground, a transmit power ten to a hundred times lower, "
            "and no dependence on an access point near the tree. The price: a tiny throughput "
            "(a few tens of bytes per message) — which rules out sending a raw signal and forces the "
            "descriptors to be extracted on the node itself.", 122)):
        p.append(txt(450, 416 + j * 11.5, frag, 7.6, GRIS))
    write("tt-network-power.svg", "\n".join(p), W, H)


# =============================================================================
# 17. OGHAM AND TREES
# =============================================================================
def tt_ogham():
    W, H = 880, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "OGHAM: A SCRIPT LEANING ON TREES", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(440, 55, "An Irish alphabet of the 4th–6th centuries, carved on the edge of standing stones",
                 8, GRIS, style="italic"))

    # The vertical edge + the notches
    x = 140
    p.append(f'<line x1="{x}" y1="86" x2="{x}" y2="386" stroke="{NUIT}" stroke-width="3"/>')
    letters = [
        ("B", "beith", "birch", 1, "right"),
        ("L", "luis", "rowan", 2, "right"),
        ("F", "fearn", "alder", 3, "right"),
        ("S", "sail", "willow", 4, "right"),
        ("N", "nion", "ash", 5, "right"),
        ("H", "uath", "hawthorn", 1, "left"),
        ("D", "dair", "oak", 2, "left"),
        ("T", "tinne", "holly", 3, "left"),
        ("C", "coll", "hazel", 4, "left"),
        ("Q", "ceirt", "apple", 5, "left"),
    ]
    yy = 108
    for lt, name, tree, n, side in letters:
        for k in range(n):
            if side == "right":
                p.append(f'<line x1="{x}" y1="{yy+k*4.6}" x2="{x+30}" y2="{yy+k*4.6}" '
                         f'stroke="{OR}" stroke-width="2.4"/>')
            else:
                p.append(f'<line x1="{x-30}" y1="{yy+k*4.6}" x2="{x}" y2="{yy+k*4.6}" '
                         f'stroke="{SEVE}" stroke-width="2.4"/>')
        p.append(txt(x + 48, yy + 8, lt, 10.4, NUIT, anchor="start", weight="700", family=SERIF))
        p.append(txt(x + 68, yy + 8, f"{name} — {tree}", 8, GRIS, anchor="start", style="italic"))
        yy += 28

    p.append(f'<rect x="470" y="92" width="366" height="132" rx="7" fill="#FFFFFF" '
             f'stroke="{SEVE}" stroke-width="1.5"/>')
    p.append(txt(653, 114, "What is attested", 10, SEVE, weight="700"))
    for j, frag in enumerate(_wrap(
            "Ogham is a real script, documented by some 400 stone inscriptions in Ireland and Wales. "
            "The medieval glosses tie each letter to a name, often a tree. The order and the value of "
            "the letters are established.", 58)):
        p.append(txt(490, 136 + j * 12, frag, 7.6, GRIS, anchor="start"))

    p.append(f'<rect x="470" y="242" width="366" height="144" rx="7" fill="#FBF0E8" '
             f'stroke="#F0DCC9" stroke-width="1.5"/>')
    p.append(txt(653, 264, "What is not", 10, CUIVRE, weight="700"))
    for j, frag in enumerate(_wrap(
            "The “tree calendar” and the divinatory system attached to it are a 20th-century "
            "reconstruction, owed largely to Robert Graves (“The White Goddess”, 1948). It is a modern "
            "poetic creation, not a Celtic tradition handed down. To call it ancient is an error; to "
            "practise it knowingly is a choice.", 58)):
        p.append(txt(490, 286 + j * 12, frag, 7.6, GRIS, anchor="start"))
    write("tt-ogham.svg", "\n".join(p), W, H)


# =============================================================================
# 18. THE THREE READINGS OF ONE EVENT
# =============================================================================
def tt_three_readings():
    W, H = 880, 450
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "ONE EVENT, THREE LEGITIMATE READINGS", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    p.append(f'<rect x="230" y="62" width="420" height="52" rx="7" fill="{NUIT}"/>')
    p.append(txt(440, 82, "THE EVENT", 8, OR_CL, weight="700", spacing="2"))
    p.append(txt(440, 100, "At 15:20 the trace bends sharply by 9 mV for 4 minutes.",
                 8.6, "#FFFFFF"))

    cols = [
        (48, "THE INSTRUMENTAL READING", BLEU,
         ["Check the artefact first: wind,",
          "a passing walker, dew,",
          "an electrode contact.",
          "",
          "If nothing explains it: record",
          "the event, and look for a",
          "correlation with the other channels."],
         "The question: what moved in the measuring chain?"),
        (318, "THE PHYSIOLOGICAL READING", SEVE,
         ["A variation of this order is",
          "consistent with a variation",
          "potential of hydraulic origin.",
          "",
          "A testable hypothesis: correlate it",
          "with the sap flow and the vapour",
          "pressure deficit of the air."],
         "The question: what known mechanism would produce this?"),
        (588, "THE FELT READING", OR,
         ["The practitioner notes what they",
          "perceived at that same moment,",
          "without reading it off the instrument.",
          "",
          "The note is taken blind,",
          "timestamped, before looking at",
          "the traces."],
         "The question: what was happening for me at that moment?"),
    ]
    for x, t, col, lines, q in cols:
        p.append(f'<rect x="{x}" y="152" width="244" height="228" rx="8" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.8"/>')
        p.append(f'<rect x="{x}" y="152" width="244" height="26" rx="8" fill="{col}"/>')
        p.append(f'<rect x="{x}" y="168" width="244" height="10" fill="{col}"/>')
        p.append(txt(x + 122, 170, t, 7.6, "#FFFFFF", weight="700", spacing="1.2"))
        for i, l in enumerate(lines):
            p.append(txt(x + 16, 200 + i * 15, l, 7.8, NUIT, anchor="start"))
        p.append(dashline(x + 16, 318, x + 228, 318))
        for j, frag in enumerate(_wrap(q, 36)):
            p.append(txt(x + 122, 336 + j * 11.5, frag, 7.4, col, style="italic"))
        p.append(arrow(x + 122, 118, x + 122, 148, col, 1.8,
                       "ahb" if col == BLEU else ("ahv" if col == SEVE else "ah")))

    p.append(f'<rect x="48" y="396" width="784" height="42" rx="6" fill="#F7F0DC" '
             f'stroke="#ECDCB0" stroke-width="1.2"/>')
    p.append(txt(440, 414, "The three columns do not contradict one another — they do not answer the same question.",
                 8.6, NUIT, weight="700"))
    p.append(txt(440, 430,
                 "The fault is not in holding all three. It is in presenting the third with the authority of the first.",
                 7.8, CUIVRE, style="italic"))
    write("tt-three-readings.svg", "\n".join(p), W, H)


# =============================================================================
# 19. THE TWO “TALKING TREES” COMPARED
# =============================================================================
def tt_comparison():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "TWO “TALKING TREES”, FIFTEEN YEARS APART", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    heads = [(80, "BRUSSELS · 2010", CUIVRE, "Happiness Brussels, for EOS magazine"),
             (470, "LONDON · AUSTIN · DUBLIN · 2025", BLEU, "Droga5, for Agency for Nature")]
    for x, t, col, sub in heads:
        p.append(f'<rect x="{x}" y="66" width="330" height="46" rx="7" fill="{col}"/>')
        p.append(txt(x + 165, 86, t, 9.4, "#FFFFFF", weight="700", spacing="1.4"))
        p.append(txt(x + 165, 102, sub, 7.4, "#FFFFFF", style="italic"))

    rows = [
        ("Tree", "One hundred-year-old tree, in Brussels.",
         "Three trees in turn: 150, 50 and 200 years old."),
        ("Sensors", "Ozone, fine particles, a lux meter, a weather station, a webcam, a microphone.",
         "About ten: bioelectric, soil, air, light, wind."),
        ("Processing", "Bespoke software: fixed rules produce a message.",
         "A language model running offline on a Mac Mini."),
        ("Voice", "Delayed posts on Facebook, Twitter, Flickr, SoundCloud.",
         "Live spoken dialogue: the visitor sits down and talks."),
        ("What comes from the human", "Every sentence, written in advance.",
         "The role, the constraints, and all of the style."),
        ("Verifiability", "Total: the rule set is finite and open to inspection.",
         "Nil from the outside: neither code, nor data, nor model published."),
    ]
    y = 130
    for i, (lab, a, b) in enumerate(rows):
        bg = "#F6F2E8" if i % 2 else "#FFFFFF"
        p.append(f'<rect x="80" y="{y}" width="720" height="48" fill="{bg}"/>')
        p.append(txt(88, y + 20, lab, 8.4, NUIT, anchor="start", weight="700"))
        for j, frag in enumerate(_wrap(a, 44)):
            p.append(txt(236, y + 18 + j * 11, frag, 7.4, GRIS, anchor="start"))
        for j, frag in enumerate(_wrap(b, 44)):
            p.append(txt(560, y + 18 + j * 11, frag, 7.4, GRIS, anchor="start"))
        p.append(f'<line x1="80" y1="{y+48}" x2="800" y2="{y+48}" stroke="{TRAIT}" stroke-width="1"/>')
        y += 48
    p.append(f'<line x1="470" y1="124" x2="470" y2="{y}" stroke="{TRAIT}" stroke-width="1.2"/>')
    p.append(f'<line x1="228" y1="124" x2="228" y2="{y}" stroke="{TRAIT}" stroke-width="1.2"/>')

    p.append(txt(440, y + 26,
                 "The technical progress is real. It bears on the fluency of the language, not on how much information comes from the tree.",
                 8.2, CUIVRE, style="italic"))
    p.append(txt(440, y + 44,
                 "The 2010 installation was the more honest on this point: nobody could believe the oak was writing its own messages.",
                 8, GRIS, style="italic"))
    write("tt-comparison.svg", "\n".join(p), W, H)


# =============================================================================
# 20. MODES OF SONIFICATION
# =============================================================================
def tt_sonification_modes():
    W, H = 880, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "THREE MODES OF SONIFICATION", 12, NUIT, weight="700",
                 spacing="3", family=SERIF))

    modes = [
        (50, "AUDIFICATION", SEVE,
         "The signal IS the sound: it is sped up until it can be heard.",
         "Faithful, with no interpretation. It demands a rich, fast signal.",
         lambda k: math.sin(k / 3.0) * 22 + math.sin(k / 1.1) * 9),
        (330, "PARAMETRIC MAPPING", BLEU,
         "Each quantity drives a parameter: pitch, duration, timbre, loudness.",
         "Supple and legible. The choice of mapping is entirely arbitrary.",
         lambda k: (round(math.sin(k / 12.0) * 3) * 7)),
        (610, "MODEL-BASED SONIFICATION", OR,
         "The data drive a virtual physical model, and one listens to it vibrate.",
         "Very expressive. The model's share becomes hard to disentangle.",
         lambda k: math.sin(k / 9.0) * 20 * math.exp(-((k % 60) / 40.0))),
    ]
    for x, t, col, d1, d2, fn in modes:
        p.append(f'<rect x="{x}" y="76" width="240" height="286" rx="8" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.8"/>')
        p.append(f'<rect x="{x}" y="76" width="240" height="26" rx="8" fill="{col}"/>')
        p.append(f'<rect x="{x}" y="92" width="240" height="10" fill="{col}"/>')
        p.append(txt(x + 120, 94, t, 7.8, "#FFFFFF", weight="700", spacing="1.4"))
        # the trace
        cy = 160
        pts = " ".join(f"{x+18+k*1.7:.1f},{cy - fn(k):.1f}" for k in range(0, 120))
        p.append(f'<rect x="{x+14}" y="{cy-42}" width="212" height="84" rx="4" fill="#FBFAF4" '
                 f'stroke="{TRAIT}" stroke-width="1"/>')
        p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.7"/>')
        p.append(dashline(x + 14, cy, x + 226, cy))
        yy = 226
        for d in (d1, d2):
            for j, frag in enumerate(_wrap(d, 36)):
                p.append(txt(x + 120, yy + j * 12, frag, 7.4,
                             NUIT if d is d1 else GRIS,
                             weight="700" if d is d1 else "400"))
            yy += 12 * len(_wrap(d, 36)) + 14

    p.append(txt(440, 394,
                 "In all three, a human rule decides what is heard. Publishing the rule is what separates an honest work from a conjuring trick.",
                 8.2, GRIS, style="italic"))
    write("tt-sonification-modes.svg", "\n".join(p), W, H)


# =============================================================================
# 21. THE OBSERVATION PROTOCOL (the wheel of seven sittings)
# =============================================================================
def tt_protocol_wheel():
    W, H = 760, 620
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(380, 36, "AN OBSERVATION PROTOCOL IN SEVEN SITTINGS", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(380, 57, "The same hour, the same tree, seven times", 8.2, GRIS, style="italic"))

    cx, cy, R = 380, 330, 190
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{TRAIT}" stroke-width="1.6"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="72" fill="{NUIT}"/>')
    p.append(txt(cx, cy - 8, "TREE", 10, OR_CL, weight="700", spacing="2.4", family=SERIF))
    p.append(txt(cx, cy + 10, "CONTROL", 10, OR_CL, weight="700", spacing="2.4", family=SERIF))
    p.append(txt(cx, cy + 30, "the same one, always", 6.8, "#9FB8AB", style="italic"))

    sittings = [
        ("1", "Reconnaissance", "No instrument. Describe the place, the tree, the light, the soil."),
        ("2", "Calibration", "Fit the sensors, let them settle for 2 h, interpret nothing."),
        ("3", "Reference", "Record a whole day without intervening. This is the control."),
        ("4", "A gentle disturbance", "A measured watering. Note the exact time before looking."),
        ("5", "Presence", "Stay 40 min near the tree. Record your perceptions blind."),
        ("6", "Counter-test", "The same protocol, with the sensor on an inert support."),
        ("7", "Confrontation", "Lay the three journals over one another. Look for what does not fit."),
    ]
    for i, (n, t, d) in enumerate(sittings):
        a = -math.pi / 2 + i * 2 * math.pi / 7
        x = cx + math.cos(a) * R
        y = cy + math.sin(a) * R
        p.append(f'<line x1="{cx+math.cos(a)*74:.0f}" y1="{cy+math.sin(a)*74:.0f}" '
                 f'x2="{x-math.cos(a)*24:.0f}" y2="{y-math.sin(a)*24:.0f}" '
                 f'stroke="{TRAIT}" stroke-width="1.3"/>')
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="23" fill="{OR}" stroke="{IVOIRE}" stroke-width="2.4"/>')
        p.append(txt(x, y + 6, n, 13, "#FFFFFF", weight="700", family=SERIF))
        lx = x + math.cos(a) * 46
        ly = y + math.sin(a) * 46
        anch = "middle"
        if math.cos(a) > 0.4:
            anch, lx = "start", x + 30
        elif math.cos(a) < -0.4:
            anch, lx = "end", x - 30
        p.append(txt(lx, ly - 2, t, 9.2, NUIT, anchor=anch, weight="700"))
        for j, frag in enumerate(_wrap(d, 34)):
            p.append(txt(lx, ly + 12 + j * 10.5, frag, 6.9, GRIS, anchor=anch))

    p.append(txt(380, 598,
                 "Sitting 6 is the one everybody skips. It is the only one that can prove you wrong.",
                 8.2, CUIVRE, style="italic"))
    write("tt-protocol-wheel.svg", "\n".join(p), W, H)


# =============================================================================
# 22. THE EMBEDDING SPACE
# =============================================================================
def tt_embedding():
    W, H = 860, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(430, 34, "PROJECTING A SIGNAL INTO A SPACE OF WORDS", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(430, 55, "The seductive idea — and what it quietly assumes", 8.2, GRIS,
                 style="italic"))

    # Espace 2D
    p.append(f'<rect x="440" y="86" width="330" height="270" rx="8" fill="#FFFFFF" '
             f'stroke="{TRAIT}" stroke-width="1.4"/>')
    p.append(txt(605, 106, "the vector space of language", 8, GRIS, style="italic"))
    words = [("thirst", 540, 180, CUIVRE), ("drought", 636, 156, CUIVRE),
             ("aridity", 700, 196, CUIVRE), ("coolness", 520, 300, BLEU),
             ("rain", 604, 320, BLEU), ("damp", 686, 288, BLEU),
             ("wind", 720, 250, SEVE), ("light", 500, 240, OR)]
    for w, x, y, col in words:
        p.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{col}" opacity="0.85"/>')
        p.append(txt(x + 8, y + 3.5, w, 7.6, col, anchor="start"))
    p.append(f'<circle cx="596" cy="196" r="9" fill="none" stroke="{NUIT}" stroke-width="2.2"/>')
    p.append(f'<circle cx="596" cy="196" r="3" fill="{NUIT}"/>')
    p.append(txt(596, 176, "the projected point", 7.4, NUIT, weight="700"))
    for w, x, y, col in words[:3]:
        p.append(dashline(596, 196, x, y, NUIT, 1, "3 3"))

    # The chain
    steps = [("Descriptors", "θ, T°, Δtrunk, PAR"),
             ("Projection", "a learned matrix W"),
             ("Neighbours", "the nearest words"),
             ("Writing", "a constrained sentence")]
    y = 108
    for i, (t, sub) in enumerate(steps):
        p += node(70, y, 250, 52, t, (sub,), stroke=BLEU, ts=10, ls=7.4)
        if i < 3:
            p.append(arrow(195, y + 54, 195, y + 68, BLEU, 1.8, "ahb"))
        y += 68
    p.append(arrow(324, 200, 434, 200, BLEU, 2, "ahb"))

    p.append(f'<rect x="70" y="378" width="720" height="48" rx="6" fill="#FBF0E8" '
             f'stroke="#F0DCC9" stroke-width="1.2"/>')
    p.append(txt(430, 396, "The hidden assumption", 9, CUIVRE, weight="700"))
    p.append(txt(430, 412,
                 "The matrix W is learned on (measurement, word) pairs chosen by a human. The meaning does not come out of the signal: it was put there, then found again.",
                 7.6, GRIS, style="italic"))
    write("tt-embedding.svg", "\n".join(p), W, H)


# =============================================================================
# 23. THE SITE PLAN IN THE FIELD
# =============================================================================
def tt_site_plan():
    W, H = 840, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(420, 34, "THE SITE PLAN", 12, NUIT, weight="700", spacing="3",
                 family=SERIF))
    p.append(txt(420, 55, "Seen from above — a tree, its sensors and its protection zone",
                 8.2, GRIS, style="italic"))

    cx, cy = 330, 262
    # Zone racinaire
    p.append(f'<circle cx="{cx}" cy="{cy}" r="170" fill="#EDEADB" stroke="{SEVE_C}" '
             f'stroke-width="1.6" stroke-dasharray="7 5"/>')
    p.append(txt(cx, cy - 152, "protected root zone — no machinery, no compaction",
                 7.4, SEVE, style="italic"))
    # Houppier
    p.append(f'<circle cx="{cx}" cy="{cy}" r="118" fill="#D7E3D2" opacity="0.75"/>')
    p.append(txt(cx + 84, cy - 92, "the crown projection", 7.2, GRIS, anchor="start"))
    # Tronc
    p.append(f'<circle cx="{cx}" cy="{cy}" r="26" fill="#8A7455" stroke="#5C4B34" stroke-width="2"/>')

    pts = [
        (cx, cy - 26, "E1", "north electrodes", CUIVRE, 0, -44),
        (cx + 26, cy, "E2", "south electrodes", CUIVRE, 44, 6),
        (cx - 92, cy + 40, "P1", "soil probe 20 cm", SEVE, -60, 24),
        (cx + 96, cy + 62, "P2", "soil probe 60 cm", SEVE, 44, 18),
        (cx - 8, cy - 118, "M1", "weather shelter 2 m", BLEU, -30, -24),
        (cx + 62, cy - 84, "A1", "acoustic sensor", OR, 52, -14),
        (cx + 150, cy - 140, "S1", "solar panel facing due south", OR, 16, -18),
    ]
    for x, y, code, lab, col, dx, dy in pts:
        p.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{col}" stroke="#FFF" stroke-width="1.8"/>')
        p.append(txt(x, y + 3.2, code, 6.6, "#FFFFFF", weight="700"))
        p.append(txt(x + dx, y + dy, lab, 7.2, col,
                     anchor="start" if dx >= 0 else "end", weight="700"))

    # The key / the distances
    p.append(f'<rect x="580" y="96" width="242" height="304" rx="7" fill="#FFFFFF" '
             f'stroke="{TRAIT}" stroke-width="1.2"/>')
    p.append(txt(701, 118, "Siting rules", 9.6, NUIT, weight="700"))
    p.append(dashline(596, 130, 806, 130))
    rules = [
        ("Electrodes", "Two opposed pairs: the differential cancels the common mode."),
        ("Soil probes", "Two depths at least, away from the footpath."),
        ("Weather shelter", "At 2 m, ventilated, never against the trunk nor in full sun."),
        ("Enclosure", "North of the trunk, on a wide collar, 1.80 m above the ground."),
        ("Cables", "In flexible trunking, with an expansion loop at each end."),
        ("Signage", "A sign explains the installation: it is what prevents vandalism."),
    ]
    yy = 146
    for t, d in rules:
        p.append(txt(596, yy, t, 8, SEVE, anchor="start", weight="700"))
        for j, frag in enumerate(_wrap(d, 40)):
            p.append(txt(596, yy + 12 + j * 10.5, frag, 7, GRIS, anchor="start"))
        yy += 44

    p.append(txt(420, 440,
                 "The plan is dated, photographed and archived: without it, no measurement will be re-readable in five years.",
                 8, GRIS, style="italic"))
    write("tt-site-plan.svg", "\n".join(p), W, H)


# =============================================================================
# 24. THE WORD KEYBOARD (Alexandre Ferran, 2015)
# =============================================================================
def tt_word_keyboard():
    W, H = 900, 500
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "THE WORD KEYBOARD", 12.5, NUIT, weight="700", spacing="3",
                 family=SERIF))
    p.append(txt(450, 55, "Replacing notes with words: the gesture, and what it shifts",
                 8.2, GRIS, style="italic"))

    # The chain
    chain = [
        ("Plant + clips", "impedance variation", SEVE),
        ("Wheatstone bridge", "→ voltage", SEVE),
        ("MIDI conversion", "→ a note number", BLEU),
        ("A 4 s threshold", "a debounce filter", OR),
        ("Sampler", "note → sound file", CUIVRE),
    ]
    x = 26
    for i, (t, sub, col) in enumerate(chain):
        p += node(x, 92, 150, 62, t, (sub,), stroke=col, ts=9.4, ls=7.0)
        if i < 4:
            p.append(arrow(x + 152, 123, x + 176, 123, col, 2.0,
                           "ahv" if col == SEVE else ("ahb" if col == BLEU else "ah")))
        x += 178

    # Clavier
    kx, ky = 120, 214
    keys = ["SUN", "HELP", "ILL", "EARTH", "HOT", "THANK YOU", "YES", "NO"]
    for i in range(14):
        p.append(f'<rect x="{kx+i*44}" y="{ky}" width="42" height="94" rx="3" fill="#FFFFFF" '
                 f'stroke="{GRIS}" stroke-width="1.2"/>')
    for i, w in enumerate(keys):
        xx = kx + i * 44
        p.append(f'<rect x="{xx}" y="{ky}" width="42" height="94" rx="3" fill="#FBF3DF" '
                 f'stroke="{OR}" stroke-width="1.6"/>')
        p.append(f'<text x="{xx+21}" y="{ky+74}" font-family="Lato, sans-serif" font-size="9.6" '
                 f'fill="{NUIT}" text-anchor="middle" font-weight="700" '
                 f'transform="rotate(-90 {xx+21} {ky+74})">{w}</text>')
    p.append(txt(450, 330, "≈ 50 words, chosen by the operator, one per key", 8.4, GRIS,
                 style="italic"))
    p.append(f'<path d="M779,156 v26 H450" fill="none" stroke="{CUIVRE}" stroke-width="2.2"/>')
    p.append(arrow(450, 182, 450, 208, CUIVRE, 2.2))

    # Two columns to read
    cols = [
        (60, "WHAT THIS CHANGES", SEVE,
         ["The signal is unchanged: the same",
          "variations, the same instrument, the",
          "same threshold. Only the sound bank",
          "has been swapped.",
          "",
          "No new information enters",
          "the system at all."]),
        (470, "WHAT THIS SHIFTS", CUIVRE,
         ["A note has no referent;",
          "a word has one. The listener now",
          "supplies the meaning.",
          "",
          "The interpretive load migrates",
          "from the instrument to the human —",
          "and becomes invisible."]),
    ]
    for x, t, col, lines in cols:
        p.append(f'<rect x="{x}" y="348" width="370" height="132" rx="7" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.6"/>')
        p.append(txt(x + 185, 370, t, 9.2, col, weight="700", spacing="1.6"))
        for i, l in enumerate(lines):
            p.append(txt(x + 20, 390 + i * 13, l, 7.6, NUIT, anchor="start"))
    write("tt-word-keyboard.svg", "\n".join(p), W, H)


# =============================================================================
# 25. THE THREE CONTROL TESTS
# =============================================================================
def tt_control_tests():
    W, H = 900, 480
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "THE THREE TESTS THAT DECIDE EVERYTHING", 12.5, NUIT,
                 weight="700", spacing="2.6", family=SERIF))
    p.append(txt(450, 55, "To be run before any public showing — and published with the result",
                 8.2, GRIS, style="italic"))

    tests = [
        (40, "1", "THE EMPTY TEST", CUIVRE,
         ["Unclip the electrode. Put it on",
          "a bottle of water. Feed white",
          "noise in where the signal",
          "used to be."],
         "The system must produce visible nonsense.",
         "If it still produces fine sentences, they were never coming from the plant."),
        (320, "2", "THE ABLATION", BLEU,
         ["Replace the signal with a random",
          "draw from the same vocabulary.",
          "Play both versions to a listener,",
          "blind."],
         "A listener has to be able to tell them apart.",
         "Otherwise the signal adds nothing: that is the result of Tan et al., NeurIPS 2024."),
        (600, "3", "PRE-REGISTRATION", SEVE,
         ["Write down, before the sitting:",
          "the vocabulary, the threshold, the",
          "listening window, the duration. Timestamp it.",
          "No editing afterwards."],
         "The protocol comes before the data.",
         "This is what forbids picking, after the fact, the passage that “speaks”."),
    ]
    for x, n, t, col, steps, verdict, why in tests:
        p.append(f'<rect x="{x}" y="86" width="260" height="322" rx="9" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.8"/>')
        p.append(f'<circle cx="{x+34}" cy="{118}" r="19" fill="{col}"/>')
        p.append(txt(x + 34, 125, n, 16, "#FFFFFF", weight="700", family=SERIF))
        p.append(txt(x + 62, 124, t, 9.6, col, anchor="start", weight="700", spacing="1.2"))
        p.append(dashline(x + 18, 148, x + 242, 148))
        for i, l in enumerate(steps):
            p.append(txt(x + 18, 170 + i * 15, l, 7.8, NUIT, anchor="start"))
        p.append(f'<rect x="{x+18}" y="{244}" width="224" height="44" rx="4" fill="#FBFAF4" '
                 f'stroke="{col}" stroke-width="1.1"/>')
        for j, frag in enumerate(_wrap(verdict, 32)):
            p.append(txt(x + 130, 262 + j * 12, frag, 8, col, weight="700"))
        for j, frag in enumerate(_wrap(why, 36)):
            p.append(txt(x + 130, 306 + j * 12, frag, 7.2, GRIS))

    p.append(f'<rect x="40" y="424" width="820" height="42" rx="6" fill="#0E2A22"/>')
    p.append(txt(450, 442, "An installation that does not publish its failure conditions publishes nothing.",
                 9.4, OR_CL, weight="700"))
    p.append(txt(450, 458,
                 "These three tests do not destroy the work: they make it defensible.",
                 7.8, "#9FB8AB", style="italic"))
    write("tt-control-tests.svg", "\n".join(p), W, H)


# =============================================================================
# 26. EXTRA OPENING FIGURES
# =============================================================================
def tt_cover_art():
    "The cover of volume I: a tree at night, crossed by flows of data."
    W, H = 680, 960
    p = [f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="#071A14"/><stop offset="0.55" stop-color="{NUIT}"/>'
         f'<stop offset="1" stop-color="#11291F"/></linearGradient>'
         f'<radialGradient id="glow" cx="0.5" cy="0.62" r="0.5">'
         f'<stop offset="0" stop-color="{SEVE_C}" stop-opacity="0.38"/>'
         f'<stop offset="1" stop-color="{NUIT}" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#glow)"/>']

    # The stars
    import random as _r
    rng = _r.Random(2026)
    for _ in range(90):
        x, y = rng.uniform(0, W), rng.uniform(0, 460)
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(0.6,1.8):.1f}" '
                 f'fill="{OR_CL}" opacity="{rng.uniform(0.2,0.8):.2f}"/>')

    # Colline
    p.append(f'<path d="M0,760 Q170,726 340,748 T680,760 L680,960 L0,960 Z" fill="#0A2018"/>')

    # Arbre
    p.append(canopy_tree(340, 764, 470, seed=2026, color="#24503A", depth=9,
                         leaf="#3E7F5E"))

    # Data flowing up along the trunk
    for k in range(7):
        off = k * 7 - 21
        pts = " ".join(
            f"{340 + off + math.sin(t / 26.0 + k) * (16 + k * 2):.1f},{760 - t:.0f}"
            for t in range(0, 460, 6))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{OR_CL}" stroke-width="1.1" '
                 f'opacity="{0.5 - k*0.05:.2f}"/>')

    # Bits
    for k in range(46):
        x = 340 + rng.uniform(-150, 150)
        y = rng.uniform(300, 750)
        p.append(f'<text x="{x:.0f}" y="{y:.0f}" font-family="{MONO}" font-size="9" '
                 f'fill="{SEVE_C}" opacity="{rng.uniform(0.15,0.55):.2f}">'
                 f'{rng.choice(["0","1","01","10","110"])}</text>')

    # A dark veil behind the title area, to lift the type off the image
    p.append('<defs><linearGradient id="veil" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#071A14" stop-opacity="0"/>'
             '<stop offset="0.22" stop-color="#071A14" stop-opacity="0.62"/>'
             '<stop offset="0.72" stop-color="#071A14" stop-opacity="0.62"/>'
             '<stop offset="1" stop-color="#071A14" stop-opacity="0"/>'
             '</linearGradient></defs>')
    p.append(f'<rect x="0" y="56" width="{W}" height="300" fill="url(#veil)"/>')

    # A sound wave at the bottom
    for k in range(4):
        amp = 26 - k * 5
        pts = " ".join(f"{x},{880 + math.sin(x / (22.0 - k * 3)) * amp:.1f}"
                       for x in range(40, W - 40, 4))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{OR if k % 2 else SEVE_C}" '
                 f'stroke-width="{1.8-k*0.32:.1f}" opacity="{0.55-k*0.1:.2f}"/>')

    # Points of light on the trunk
    for y in (600, 664, 728):
        p.append(f'<circle cx="340" cy="{y}" r="5.5" fill="{OR_CL}" opacity="0.9"/>')
        p.append(f'<circle cx="340" cy="{y}" r="12" fill="none" stroke="{OR_CL}" '
                 f'stroke-width="1" opacity="0.4"/>')
    write("tt-cover-art.svg", "\n".join(p), W, H)


def tt_part_bg(n, seed):
    "A part-opening background, the “connected tree” variant."
    import random as _r
    W, H = 680, 960
    rng = _r.Random(seed)
    p = [f'<defs><linearGradient id="g{n}" x1="0" y1="0" x2="0.6" y2="1">'
         f'<stop offset="0" stop-color="#081C15"/><stop offset="1" stop-color="{NUIT2}"/>'
         f'</linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#g{n})"/>']
    # A network of points (a constellation of sensors)
    nodes = [(rng.uniform(40, W - 40), rng.uniform(60, H - 60)) for _ in range(26)]
    for i, (x, y) in enumerate(nodes):
        for x2, y2 in nodes[i + 1:]:
            d = math.hypot(x - x2, y - y2)
            if d < 190:
                p.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                         f'stroke="{SEVE_C}" stroke-width="0.7" opacity="{0.24*(1-d/190):.2f}"/>')
    for x, y in nodes:
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(1.4,3.2):.1f}" '
                 f'fill="{OR_CL}" opacity="{rng.uniform(0.25,0.7):.2f}"/>')
    # A tree silhouette, as a watermark
    p.append(f'<g opacity="0.28">{canopy_tree(rng.choice([170, 340, 510]), 906, 460, seed=seed, color="#2A5741", depth=8, leaf="#3E7F5E")}</g>')
    # A gold rule
    p.append(f'<rect x="28" y="28" width="{W-56}" height="{H-56}" fill="none" '
             f'stroke="{OR}" stroke-width="0.8" opacity="0.32"/>')
    write(f"tt-part-bg-{n}.svg", "\n".join(p), W, H)


# =============================================================================
def main():
    print("• “The Talking Tree” illustrations…")
    tt_cover_art()
    for i, s in enumerate((211, 223, 227, 229, 233, 239, 241, 251), start=1):
        tt_part_bg(i, s)
    tt_sensor_map()
    tt_architecture()
    tt_acquisition_chain()
    tt_signal_to_language()
    tt_attribution()
    tt_epistemic_ladder()
    tt_stack()
    tt_noise()
    tt_circadian()
    tt_timeline()
    tt_sap_flow()
    tt_cavitation()
    tt_voc()
    tt_prompt()
    tt_electrode_tree()
    tt_network_power()
    tt_ogham()
    tt_three_readings()
    tt_comparison()
    tt_sonification_modes()
    tt_protocol_wheel()
    tt_embedding()
    tt_site_plan()
    tt_word_keyboard()
    tt_control_tests()
    n = len([f for f in os.listdir(HERE) if f.startswith("tt-") and f.endswith(".svg")])
    print(f"✓ {n} “tt-” illustrations generated in {HERE}")


if __name__ == "__main__":
    main()
