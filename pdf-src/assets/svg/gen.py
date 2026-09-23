#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/assets/svg/gen.py
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
Vector illustration generator — "The Music of the Plants".

Every image is created here, deterministically (the seed is fixed), so that
the book is reproducible from end to end.

Usage: python3 gen.py
"""
import os, math, random, re

HERE = os.path.dirname(os.path.abspath(__file__))


def esc(s):
    "Escape raw & without touching entities already formed (&amp;, &#8594;…)."
    return re.sub(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", "&amp;", str(s))

# ---- Palette (the same one as book.css) -------------------------------------
NUIT   = "#0E2A22"   # deep forest green
NUIT2  = "#17392F"
SEVE   = "#3F7D5A"   # sap green
SEVE_C = "#6FA98A"
OR     = "#B08528"
OR_CL  = "#E0C073"
IVOIRE = "#FBF9F1"
GRIS   = "#6B7A72"
TRAIT  = "#D9D9C6"
BLEU   = "#2F5E86"
CUIVRE = "#A8552E"


def write(name, body, w=800, h=500, bg=None):
    "Write out a complete SVG file."
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
           f'width="{w}" height="{h}">\n{rect}\n{body}\n</svg>\n')
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("  ·", name)


# The figures are shown about 125 mm wide: a body size of 8 units inside a
# viewBox of 760 would print at 4 pt. Every text size is therefore raised by
# a constant factor, with a floor below which nothing is legible.
TEXT_SCALE = 1.45
TEXT_MIN   = 9.6


def txt(x, y, s, size=13, fill=NUIT, anchor="middle", family="Lato, sans-serif",
        weight="400", style="normal", spacing="0"):
    size = round(max(size * TEXT_SCALE, TEXT_MIN), 2)
    s = esc(s)
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'font-style="{style}" letter-spacing="{spacing}">{s}</text>')


def box(x, y, w, h, fill="#FFFFFF", stroke=SEVE, rx=8, sw=1.6, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def arrow(x1, y1, x2, y2, color=OR, sw=2.2, marker="ah"):
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="{sw}" marker-end="url(#{marker})"/>')


ARROWDEFS = f'''<defs>
 <marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6"
   markerHeight="6" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{OR}"/></marker>
 <marker id="ahb" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6"
   markerHeight="6" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{BLEU}"/></marker>
 <marker id="ahv" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6"
   markerHeight="6" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{SEVE}"/></marker>
</defs>'''


# =============================================================================
#  TREES & FOLIAGE (reusable building blocks)
# =============================================================================
def branch(x, y, angle, length, depth, width, rng, color, parts):
    "Recursive fractal tree."
    if depth == 0 or length < 3:
        return
    x2 = x + math.cos(angle) * length
    y2 = y + math.sin(angle) * length
    parts.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{color}" stroke-width="{width:.2f}" stroke-linecap="round"/>')
    if depth <= 3:
        r = rng.uniform(1.6, 3.4)
        parts.append(f'<circle cx="{x2:.1f}" cy="{y2:.1f}" r="{r:.1f}" '
                     f'fill="{SEVE_C}" opacity="{rng.uniform(.35,.8):.2f}"/>')
    n = 2 if depth > 2 else rng.choice([1, 2])
    for i in range(n):
        spread = rng.uniform(.28, .54)
        na = angle + (spread if i == 0 else -spread) + rng.uniform(-.12, .12)
        branch(x2, y2, na, length * rng.uniform(.68, .80), depth - 1,
               width * .68, rng, color, parts)


def fractal_tree(cx, base_y, height, depth=9, color="#2C5D45", seed=7):
    rng = random.Random(seed)
    parts = []
    branch(cx, base_y, -math.pi / 2, height, depth, height * .11, rng, color, parts)
    return "\n".join(parts)


def leaf_path(cx, cy, w, h, rot=0):
    "Lance-shaped leaf (two arcs)."
    return (f'<g transform="translate({cx},{cy}) rotate({rot})">'
            f'<path d="M0,{-h/2} C{w/2},{-h/6} {w/2},{h/6} 0,{h/2} '
            f'C{-w/2},{h/6} {-w/2},{-h/6} 0,{-h/2} Z" '
            f'fill="{SEVE}" opacity=".9"/>'
            f'<line x1="0" y1="{-h/2}" x2="0" y2="{h/2}" stroke="{NUIT}" '
            f'stroke-width="1.1" opacity=".55"/></g>')


# =============================================================================
#  1. COVER
# =============================================================================
def cover_art():
    W, H = 680, 960
    p = [f'<defs>'
         f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="#05120F"/>'
         f'<stop offset="40%" stop-color="#0B231C"/>'
         f'<stop offset="100%" stop-color="#16382D"/></linearGradient>'
         f'<radialGradient id="halo" cx="50%" cy="74%" r="46%">'
         f'<stop offset="0%" stop-color="{SEVE_C}" stop-opacity=".34"/>'
         f'<stop offset="60%" stop-color="{SEVE}" stop-opacity=".09"/>'
         f'<stop offset="100%" stop-color="{NUIT}" stop-opacity="0"/></radialGradient>'
         f'<linearGradient id="scrim" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="#05120F" stop-opacity=".88"/>'
         f'<stop offset="52%" stop-color="#05120F" stop-opacity=".62"/>'
         f'<stop offset="78%" stop-color="#05120F" stop-opacity="0"/></linearGradient>'
         f'<linearGradient id="scrimb" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="#05120F" stop-opacity="0"/>'
         f'<stop offset="46%" stop-color="#05120F" stop-opacity=".58"/>'
         f'<stop offset="100%" stop-color="#05120F" stop-opacity=".90"/></linearGradient>'
         f'<radialGradient id="glow" cx="50%" cy="50%" r="50%">'
         f'<stop offset="0%" stop-color="{OR_CL}" stop-opacity=".8"/>'
         f'<stop offset="100%" stop-color="{OR_CL}" stop-opacity="0"/></radialGradient>'
         f'</defs>',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#halo)"/>']

    rng = random.Random(21)
    # Distant stand of trees, low and unobtrusive
    for i in range(22):
        x = rng.uniform(-20, W + 20)
        hh = rng.uniform(70, 150)
        p.append(f'<g opacity="{rng.uniform(.05,.13):.2f}">'
                 + fractal_tree(x, H - 60, hh, depth=6, color="#8FBFA6",
                                seed=100 + i) + '</g>')

    # The ancient tree: confined to the lower third
    p.append('<g opacity=".92">' + fractal_tree(W / 2, H - 70, 132, depth=9,
                                                color="#CFE2D6", seed=3) + '</g>')
    p.append(f'<path d="M{W/2-15},{H-58} C{W/2-10},{H-108} {W/2-7},{H-150} '
             f'{W/2-4},{H-192} L{W/2+4},{H-192} C{W/2+7},{H-150} {W/2+10},{H-108} '
             f'{W/2+15},{H-58} Z" fill="#CFE2D6" opacity=".9"/>')
    for a in (-1, 1):
        for k in (1, 2, 3):
            p.append(f'<path d="M{W/2},{H-60} Q{W/2+a*k*26},{H-48} '
                     f'{W/2+a*k*50},{H-28}" stroke="#B9D3C3" stroke-width="{3.4-k*0.8:.1f}" '
                     f'fill="none" stroke-linecap="round" opacity=".7"/>')

    # Energy flow: concentric waves rising from the crown
    for i in range(8):
        r = 46 + i * 44
        p.append(f'<circle cx="{W/2}" cy="{H-196}" r="{r}" fill="none" '
                 f'stroke="{OR_CL}" stroke-width="{1.3-i*0.10:.2f}" '
                 f'opacity="{0.34-i*0.036:.2f}"/>')

    # Rising staves of sound
    for k, amp in enumerate((20, 14, 9)):
        y0 = H - 250 - k * 30
        pts = " ".join(f"{x},{y0 + math.sin(x/40.0+k*1.3)*amp:.1f}"
                       for x in range(34, W - 24, 10))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{OR_CL}" '
                 f'stroke-width="{1.4-k*0.28:.1f}" opacity="{0.44-k*0.11:.2f}"/>')

    # Particles of light, kept clear of the title area
    for i in range(18):
        x = rng.uniform(40, W - 40)
        y = rng.choice([rng.uniform(70, 150), rng.uniform(H - 430, H - 250)])
        r = rng.uniform(1.8, 3.8)
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r*5:.0f}" fill="url(#glow)" '
                 f'opacity=".26"/>')
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{OR_CL}" '
                 f'opacity="{rng.uniform(.55,.95):.2f}"/>')

    # The ground and the mycorrhizal network
    p.append(f'<path d="M0,{H-54} Q{W/2},{H-76} {W},{H-54} L{W},{H} L0,{H} Z" '
             f'fill="#05120F" opacity=".94"/>')
    for i in range(26):
        x1 = rng.uniform(0, W); y1 = rng.uniform(H - 50, H - 8)
        x2 = x1 + rng.uniform(-80, 80); y2 = y1 + rng.uniform(-16, 16)
        p.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" '
                 f'stroke="{SEVE_C}" stroke-width=".8" opacity="{rng.uniform(.10,.28):.2f}"/>')

    # A dark veil over the upper half: it is what makes the title legible
    p.append(f'<rect width="{W}" height="{H*0.66:.0f}" fill="url(#scrim)"/>')
    p.append(f'<rect y="{H-268}" width="{W}" height="268" fill="url(#scrimb)"/>')
    write("cover-art.svg", "\n".join(p), W, H)


# =============================================================================
#  2. PART-OPENING BACKGROUNDS
# =============================================================================
def part_bg(n, seed):
    W, H = 680, 960
    p = [f'<defs><linearGradient id="g{n}" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="#071A15"/>'
         f'<stop offset="100%" stop-color="#16382D"/></linearGradient>'
         f'<radialGradient id="h{n}" cx="50%" cy="38%" r="60%">'
         f'<stop offset="0%" stop-color="{SEVE_C}" stop-opacity=".22"/>'
         f'<stop offset="100%" stop-color="{NUIT}" stop-opacity="0"/>'
         f'</radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#g{n})"/>',
         f'<rect width="{W}" height="{H}" fill="url(#h{n})"/>']
    rng = random.Random(seed)
    for i in range(14):
        x = rng.uniform(-30, W + 30)
        p.append(f'<g opacity="{rng.uniform(.05,.13):.2f}">'
                 + fractal_tree(x, H + 30, rng.uniform(150, 330), depth=7,
                                color="#9FCBB4", seed=seed * 10 + i) + '</g>')
    for i in range(3):
        r = 150 + i * 110
        p.append(f'<circle cx="{W/2}" cy="{H/2}" r="{r}" fill="none" '
                 f'stroke="{OR_CL}" stroke-width=".9" opacity="{.16-i*.04:.2f}"/>')
    for i in range(26):
        x = rng.uniform(20, W - 20); y = rng.uniform(40, H - 40)
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(.9,2.4):.1f}" '
                 f'fill="{OR_CL}" opacity="{rng.uniform(.2,.6):.2f}"/>')
    write(f"part-bg-{n}.svg", "\n".join(p), W, H)


# =============================================================================
#  3. HISTORICAL TIMELINE
# =============================================================================
def timeline():
    W, H = 880, 470
    milestones = [
        ("1770", "Percival Baxter /", "first measurements of irritability"),
        ("1901", "J. C. Bose", "crescograph, electrical response"),
        ("1966", "Cleve Backster", "polygraph & “primary perception”"),
        ("1973", "Tompkins & Bird", "The Secret Life of Plants"),
        ("1976", "Damanhur", "first plant → sound converter"),
        ("2014", "MIDI Sprout", "bio-sonification open source"),
        ("2017", "Plants Play", "portable Bluetooth enclosure"),
        ("2021", "US 10 909 956", "PlantWave patent"),
    ]
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    y0 = 235
    p.append(f'<line x1="40" y1="{y0}" x2="{W-40}" y2="{y0}" stroke="{TRAIT}" '
             f'stroke-width="3"/>')
    p.append(arrow(W - 60, y0, W - 34, y0))
    step = (W - 120) / (len(milestones) - 1)
    for i, (year, who, what) in enumerate(milestones):
        x = 60 + i * step
        upper = (i % 2 == 0)
        ty = y0 - 26 if upper else y0 + 26
        p.append(f'<line x1="{x:.0f}" y1="{y0}" x2="{x:.0f}" y2="{ty:.0f}" '
                 f'stroke="{SEVE_C}" stroke-width="1.4"/>')
        p.append(f'<circle cx="{x:.0f}" cy="{y0}" r="6.5" fill="{OR}" '
                 f'stroke="#FFF" stroke-width="2"/>')
        by = (ty - 74) if upper else ty
        p.append(box(x - 52, by, 104, 74, fill="#F7F5EC", stroke=TRAIT, rx=6, sw=1))
        p.append(txt(x, by + 20, year, 15, OR, weight="700",
                     family="Cormorant Garamond, serif"))
        p.append(txt(x, by + 38, who, 8.6, NUIT, weight="700"))
        # the description broken over two lines
        words = what.split()
        l1, l2 = [], []
        cur = l1
        for m in words:
            if len(" ".join(cur + [m])) > 20 and cur is l1:
                cur = l2
            cur.append(m)
        p.append(txt(x, by + 52, " ".join(l1), 7.4, GRIS))
        p.append(txt(x, by + 63, " ".join(l2), 7.4, GRIS))
    p.append(txt(W / 2, 40, "FROM PLANT IRRITABILITY TO BIO-SONIFICATION", 12,
                 SEVE, weight="700", spacing="2"))
    p.append(txt(W / 2, H - 22, "Two centuries of measuring living plants", 10, GRIS,
                 family="Cormorant Garamond, serif", style="italic"))
    write("timeline.svg", "\n".join(p), W, H)


# =============================================================================
#  4. THE PROCESSING CHAIN: SIGNAL → MUSIC
# =============================================================================
def pipeline():
    W, H = 980, 400
    stages = [
        ("PLANT", "living organism", SEVE),
        ("ELECTRODES", "leaf · root", SEVE),
        ("MEASURING BRIDGE", "variable R", BLEU),
        ("AMPLIFICATION", "gain × 25", BLEU),
        ("FILTERING", "anti-noise", BLEU),
        ("A/D CONVERSION", "8 to 12 bits", BLEU),
        ("ANALYSIS", "threshold · standard deviation", OR),
        ("MIDI MAPPING", "note · CC", OR),
        ("SYNTHESIS", "instrument · effects", NUIT),
        ("SOUND", "loudspeaker", NUIT),
    ]
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 36, "FROM ELECTRICAL POTENTIAL TO NOTE", 12, SEVE,
                 weight="700", spacing="2"))
    bw, bh = 154, 76
    gap = (W - 56 - bw * 5) / 4
    for i, (t, sub, c) in enumerate(stages):
        row, col = divmod(i, 5)
        x = 28 + col * (bw + gap)
        y = 90 + row * 146
        p.append(box(x, y, bw, bh, fill="#FBFAF4", stroke=c, rx=8, sw=1.8))
        p.append(f'<rect x="{x}" y="{y}" width="{bw}" height="5" rx="2" fill="{c}"/>')
        p.append(txt(x + bw / 2, y + 34, t, 8.4, NUIT, weight="700"))
        p.append(txt(x + bw / 2, y + 54, sub, 6.8, GRIS))
        p.append(f'<circle cx="{x+bw-14}" cy="{y+bh-14}" r="11" fill="{c}" opacity=".14"/>')
        p.append(txt(x + bw - 14, y + bh - 9, str(i + 1), 7.6, c, weight="700"))
        if col < 4:
            p.append(arrow(x + bw + 4, y + bh / 2, x + bw + gap - 4, y + bh / 2))
    p.append(f'<path d="M{28+4*(bw+gap)+bw/2},{90+bh+8} v38 H{28+bw/2} v18" '
             f'fill="none" stroke="{OR}" stroke-width="2.4" marker-end="url(#ah)"/>')
    for x, sub in [(28 + bw / 2, "µV — analog"),
                   (28 + 2 * (bw + gap) + bw / 2, "mV — amplified"),
                   (28 + 4 * (bw + gap) + bw / 2, "bytes — digital")]:
        p.append(txt(x, 182, sub, 7, BLEU, style="italic"))
    for x, sub in [(28 + bw / 2, "0–127 — MIDI"),
                   (28 + 3 * (bw + gap) + bw / 2, "44.1 kHz — audio")]:
        p.append(txt(x, 330, sub, 7, OR, style="italic"))
    p.append(txt(W / 2, H - 16,
                 "The canonical chain, common to every bio-sonification device", 8.6,
                 GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("pipeline.svg", "\n".join(p), W, H)


# =============================================================================
#  5. ELECTRODE SETUP
# =============================================================================
def electrodes():
    W, H = 820, 486
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 34, "PLACING THE ELECTRODES: THE CIRCUIT RUNS THROUGH THE PLANT", 12,
                 SEVE, weight="700", spacing="1.6"))
    cx = 380
    # Pot
    p.append(f'<path d="M{cx-110},388 L{cx-78},438 L{cx+78},438 L{cx+110},388 Z" '
             f'fill="#C8A98A" stroke="{CUIVRE}" stroke-width="1.6"/>')
    p.append(f'<rect x="{cx-118}" y="374" width="236" height="16" rx="4" fill="#B9977A" '
             f'stroke="{CUIVRE}" stroke-width="1.4"/>')
    p.append(f'<path d="M{cx-100},390 L{cx+100},390 L{cx+92},398 L{cx-92},398 Z" fill="#5A4433"/>')
    # Tige + feuilles
    p.append(f'<path d="M{cx},390 C{cx-4},320 {cx+2},270 {cx},200" stroke="#2C5D45" '
             f'stroke-width="7" fill="none" stroke-linecap="round"/>')
    for (fx, fy, w, h, r) in [(cx-58, 292, 60, 114, -58), (cx+58, 266, 60, 114, 58),
                              (cx-50, 224, 50, 96, -40), (cx+50, 206, 50, 96, 40),
                              (cx, 164, 52, 100, 0)]:
        p.append(leaf_path(fx, fy, w, h, r))
    for a in (-1, 1):
        for k in (1, 2):
            p.append(f'<path d="M{cx},394 Q{cx+a*k*28},420 {cx+a*k*48},440" '
                     f'stroke="#8B6F4E" stroke-width="{3.2-k*0.8:.1f}" fill="none"/>')
    # The leaf electrode
    p.append(f'<rect x="{cx-30}" y="152" width="28" height="13" rx="3" fill="#D8D8D0" '
             f'stroke="{GRIS}" stroke-width="1.2"/>')
    p.append(f'<circle cx="{cx-16}" cy="158" r="3" fill="{CUIVRE}"/>')
    p.append(f'<path d="M{cx-30},158 C{cx-120},142 {cx-190},162 {cx-230},192" '
             f'stroke="#B03A2E" stroke-width="2.6" fill="none"/>')
    # The soil electrode
    p.append(f'<rect x="{cx-86}" y="382" width="8" height="32" rx="2" fill="#9AA0A6" '
             f'stroke="{GRIS}" stroke-width="1"/>')
    p.append(f'<path d="M{cx-82},388 C{cx-160},360 {cx-210},318 {cx-232},250" '
             f'stroke="{NUIT}" stroke-width="2.6" fill="none"/>')
    # The enclosure
    p.append(box(58, 188, 110, 84, fill="#F3F0E4", stroke=NUIT, rx=8, sw=2))
    p.append(txt(113, 220, "ENCLOSURE", 9, NUIT, weight="700"))
    p.append(txt(113, 238, "for measuring", 7.2, GRIS))
    for i, c in enumerate((OR, SEVE_C, BLEU)):
        p.append(f'<circle cx="{88+i*25}" cy="256" r="5" fill="{c}"/>')
    p.append(f'<rect x="97" y="180" width="32" height="8" rx="3" fill="{NUIT}"/>')
    p.append(txt(113, 172, "MIDI OUT", 6.4, SEVE, weight="700"))
    p.append(arrow(113, 166, 113, 138, marker="ahv"))
    p.append(txt(113, 126, "to synthesizer / DAW", 7.2, SEVE))
    # Captions, all of them on the right
    p.append(f'<circle cx="530" cy="150" r="10" fill="{OR}"/>')
    p.append(txt(530, 155, "1", 8, "#FFF", weight="700"))
    p.append(txt(548, 148, "Upper electrode", 8.8, NUIT, anchor="start", weight="700"))
    p.append(txt(548, 168, "underside of a mature leaf,", 7.4, GRIS, anchor="start"))
    p.append(txt(548, 184, "healthy and well watered — basal third", 7.4, GRIS, anchor="start"))
    p.append(f'<path d="M524,150 L{cx-4},152" stroke="{GRIS}" stroke-width="1" '
             f'stroke-dasharray="3 3"/>')
    p.append(f'<circle cx="530" cy="244" r="10" fill="{OR}"/>')
    p.append(txt(530, 249, "2", 8, "#FFF", weight="700"))
    p.append(txt(548, 242, "Lower electrode", 8.8, NUIT, anchor="start", weight="700"))
    p.append(txt(548, 262, "moist soil at the foot of the stem,", 7.4, GRIS, anchor="start"))
    p.append(txt(548, 278, "or a second point on the same blade", 7.4, GRIS, anchor="start"))
    p.append(f'<path d="M524,252 C480,300 440,360 {cx-78},392" stroke="{GRIS}" '
             f'stroke-width="1" stroke-dasharray="3 3" fill="none"/>')
    p.append(txt(W / 2, H - 14,
                 "The circuit closes through the plant: the plant IS the resistance being measured.",
                 8.6, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("electrodes.svg", "\n".join(p), W, H)


# =============================================================================
#  6. THE WHEATSTONE BRIDGE
# =============================================================================
def wheatstone():
    W, H = 800, 480
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 34, "THE WHEATSTONE BRIDGE — HOW DEVICE U1 WORKS", 12,
                 SEVE, weight="700", spacing="1.6"))
    BX, BY = 350, 268          # the centre of the diamond
    A, B, C, D = (BX, 148), (BX + 190, BY), (BX, 388), (BX - 190, BY)
    for (x1, y1), (x2, y2) in [(A, B), (B, C), (C, D), (D, A)]:
        p.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{NUIT}" '
                 f'stroke-width="2.2"/>')

    def resistor(pa, pb, label, sub, color):
        (x1, y1), (x2, y2) = pa, pb
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ang = math.degrees(math.atan2(y2 - y1, x2 - x1))
        out = (f'<g transform="translate({mx},{my}) rotate({ang})">'
               f'<rect x="-28" y="-12" width="56" height="24" rx="3" fill="#FFF" '
               f'stroke="{color}" stroke-width="2"/></g>')
        # the label offset at right angles, outward from the diamond
        dx, dy = mx - BX, my - BY
        n = math.hypot(dx, dy) or 1
        lx, ly = mx + dx / n * 56, my + dy / n * 56
        out += txt(lx, ly - 2, label, 11, color, weight="700",
                   family="Cormorant Garamond, serif")
        out += txt(lx, ly + 16, sub, 7.4, GRIS)
        return out

    p.append(resistor(A, B, "R1", "10.1 MΩ", BLEU))
    p.append(resistor(B, C, "R2", "4 MΩ", BLEU))
    p.append(resistor(D, C, "Rp", "THE PLANT", SEVE))
    p.append(resistor(A, D, "R3", "reference", BLEU))

    for pt, color in [(A, NUIT), (C, NUIT), (B, OR), (D, OR)]:
        p.append(f'<circle cx="{pt[0]}" cy="{pt[1]}" r="5" fill="{color}"/>')
    # Alimentation
    p.append(f'<line x1="{A[0]}" y1="{A[1]}" x2="{A[0]}" y2="94" stroke="{NUIT}" stroke-width="2.2"/>')
    p.append(txt(A[0], 84, "+4 V — midpoint of the diode string", 8, NUIT))
    # Masse
    p.append(f'<line x1="{C[0]}" y1="{C[1]}" x2="{C[0]}" y2="424" stroke="{NUIT}" stroke-width="2.2"/>')
    for i, hw in enumerate((17, 11, 5)):
        p.append(f'<line x1="{C[0]-hw}" y1="{424+i*7}" x2="{C[0]+hw}" y2="{424+i*7}" '
                 f'stroke="{NUIT}" stroke-width="{2.6-i*0.5:.1f}"/>')
    p.append(txt(C[0], 458, "ground", 8, GRIS))
    # The measuring diagonal
    p.append(f'<line x1="{D[0]}" y1="{D[1]}" x2="{B[0]}" y2="{B[1]}" stroke="{OR}" '
             f'stroke-width="2.4" stroke-dasharray="7 4"/>')
    p.append(box(BX - 70, BY - 26, 140, 52, fill="#FDF7E6", stroke=OR, rx=8, sw=1.8))
    p.append(txt(BX, BY - 4, "Vb − Vc", 12, OR, weight="700",
                 family="Cormorant Garamond, serif"))
    p.append(txt(BX, BY + 16, "imbalance voltage", 7.4, GRIS))
    # Sortie
    p.append(arrow(B[0], BY, B[0] + 76, BY))
    p.append(box(B[0] + 44, BY + 40, 148, 66, fill="#F2F7FB", stroke=BLEU, rx=7, sw=1.6))
    p.append(txt(B[0] + 118, BY + 64, "AMP", 9.4, BLEU, weight="700"))
    p.append(txt(B[0] + 118, BY + 82, "instrumentation", 7.2, GRIS))
    p.append(txt(B[0] + 118, BY + 98, "total gain × 25", 7.2, GRIS))
    p.append(f'<path d="M{B[0]+76},{BY} L{B[0]+118},{BY+40}" stroke="{OR}" stroke-width="2"/>')
    write("wheatstone.svg", "\n".join(p), W, H)


# =============================================================================
#  7. NE555 OSCILLATOR (the MIDI Sprout approach)
# =============================================================================
def ne555():
    W, H = 860, 456
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 34, "THE NE555 ASTABLE OSCILLATOR — THE OPEN-SOURCE APPROACH", 12,
                 SEVE, weight="700", spacing="1.8"))

    # --- the microcontroller, top left ---
    p.append(box(40, 66, 240, 84, fill="#F2F7FB", stroke=BLEU, rx=8, sw=1.8))
    p.append(txt(160, 94, "ATmega328P", 10, BLEU, weight="700"))
    p.append(txt(160, 114, "INT0 — period measurement", 7, GRIS))
    p.append(txt(160, 130, "MIDI 31,250 baud on TX", 7, GRIS))

    # --- the 555 package, in the middle ---
    p.append(box(330, 130, 170, 170, fill="#FBFAF4", stroke=NUIT, rx=6, sw=2))
    p.append(txt(415, 164, "NE555", 14, NUIT, weight="700",
                 family="Cormorant Garamond, serif"))
    p.append(txt(415, 184, "astable", 7.6, GRIS, style="italic"))
    for pin, num, y, side in [("TR", 2, 212, "l"), ("R", 4, 246, "l"), ("CV", 5, 280, "l"),
                              ("Q", 3, 212, "r"), ("DIS", 7, 246, "r"), ("THR", 6, 280, "r")]:
        if side == "l":
            p.append(f'<line x1="296" y1="{y}" x2="330" y2="{y}" stroke="{NUIT}" stroke-width="1.6"/>')
            p.append(txt(348, y + 5, pin, 8, NUIT, anchor="start"))
            p.append(txt(292, y - 7, str(num), 6.2, GRIS, anchor="end"))
        else:
            p.append(f'<line x1="500" y1="{y}" x2="534" y2="{y}" stroke="{NUIT}" stroke-width="1.6"/>')
            p.append(txt(482, y + 5, pin, 8, NUIT, anchor="end"))
            p.append(txt(538, y - 7, str(num), 6.2, GRIS, anchor="start"))

    # --- Q to the microcontroller ---
    p.append(f'<path d="M534,212 H566 V108 H286" fill="none" stroke="{BLEU}" '
             f'stroke-width="2.2" marker-end="url(#ahb)"/>')

    # --- the plant: an RC network ---
    p.append(box(614, 226, 218, 104, fill="#EDF6F0", stroke=SEVE, rx=8, sw=1.8))
    p.append(txt(723, 256, "PLANT", 11, SEVE, weight="700",
                 family="Cormorant Garamond, serif"))
    p.append(txt(723, 278, "R varies between P1 and P2", 7, GRIS))
    p.append(txt(723, 300, "≈ 0.5 – 50 MΩ", 8.4, NUIT, weight="700"))
    p.append(txt(723, 320, "(resistance of the leaf blade)", 6.6, GRIS))
    p.append(f'<line x1="534" y1="246" x2="614" y2="262" stroke="{SEVE}" stroke-width="2"/>')
    p.append(f'<line x1="534" y1="280" x2="614" y2="296" stroke="{SEVE}" stroke-width="2"/>')

    # --- R2 to VCC, above the plant ---
    p.append(f'<path d="M566,280 V176 H700" fill="none" stroke="{NUIT}" stroke-width="1.6"/>')
    p.append(f'<rect x="700" y="166" width="54" height="20" rx="3" fill="#FFF" '
             f'stroke="{BLEU}" stroke-width="1.6"/>')
    p.append(txt(727, 156, "R2  100 kΩ", 7.4, BLEU))
    p.append(f'<line x1="754" y1="176" x2="800" y2="176" stroke="{NUIT}" stroke-width="1.6"/>')
    p.append(f'<line x1="800" y1="176" x2="800" y2="162" stroke="{NUIT}" stroke-width="1.6"/>')
    p.append(txt(800, 152, "+5 V", 7.4, NUIT))

    # --- C1 ---
    p.append(f'<line x1="264" y1="200" x2="264" y2="256" stroke="{NUIT}" stroke-width="1.6"/>')
    p.append(f'<line x1="248" y1="222" x2="280" y2="222" stroke="{NUIT}" stroke-width="2.6"/>')
    p.append(f'<line x1="248" y1="232" x2="280" y2="232" stroke="{NUIT}" stroke-width="2.6"/>')
    p.append(f'<path d="M264,212 H296" fill="none" stroke="{NUIT}" stroke-width="1.6"/>')
    p.append(txt(232, 224, "C1", 8.4, NUIT, anchor="end"))
    p.append(txt(232, 242, "4.2 nF", 7, GRIS, anchor="end"))

    # --- chronogramme ---
    p.append(txt(60, 344, "A pulse train whose PERIOD follows the conductance:",
                 8.2, NUIT, anchor="start"))
    y, xs = 376, 74
    cur = xs
    d = [f"M{cur},{y+22}"]
    for w in [20, 20, 20, 32, 32, 16, 16, 16, 28, 28, 24, 24]:
        d.append(f"V{y} H{cur+w/2:.0f} V{y+22} H{cur+w:.0f}")
        cur += w
    p.append(f'<path d="{" ".join(d)}" fill="none" stroke="{OR}" stroke-width="2"/>')
    p.append(f'<line x1="{xs-6}" y1="{y+22}" x2="{cur+14}" y2="{y+22}" stroke="{TRAIT}" stroke-width="1"/>')
    p.append(txt(xs - 14, y + 5, "5 V", 7, GRIS, anchor="end"))
    p.append(txt(xs - 14, y + 26, "0 V", 7, GRIS, anchor="end"))
    p.append(f'<line x1="{xs+60}" y1="{y-10}" x2="{xs+124}" y2="{y-10}" stroke="{SEVE}" '
             f'stroke-width="1.2" marker-end="url(#ahv)"/>')
    p.append(txt(xs + 250, y - 6, "longer period = falling conductance", 7.2, SEVE,
                 anchor="start"))
    p.append(txt(W / 2, H - 14,
                 "Here the plant is not measured: it SETS the oscillator's frequency.",
                 8.6, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("ne555.svg", "\n".join(p), W, H)


# =============================================================================
#  8. PLANT ACTION POTENTIAL
# =============================================================================
def action_potential():
    W, H = 760, 400
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 30, "THREE ELECTRICAL SIGNALS OF A PLANT", 11.5, SEVE,
                 weight="700", spacing="1.6"))
    ox, oy = 90, 300
    p.append(f'<line x1="{ox}" y1="60" x2="{ox}" y2="{oy}" stroke="{GRIS}" '
             f'stroke-width="1.4"/>')
    p.append(f'<line x1="{ox}" y1="{oy}" x2="{W-40}" y2="{oy}" stroke="{GRIS}" '
             f'stroke-width="1.4"/>')
    p.append(txt(ox - 12, 72, "mV", 8, GRIS, anchor="end"))
    p.append(txt(W - 40, oy + 20, "time", 8, GRIS, anchor="end"))
    for v, lab in [(0, "−160"), (60, "−120"), (120, "−80"), (180, "−40"), (240, "0")]:
        p.append(f'<line x1="{ox-4}" y1="{oy-v}" x2="{ox}" y2="{oy-v}" stroke="{GRIS}" '
                 f'stroke-width="1"/>')
        p.append(txt(ox - 10, oy - v + 4, lab, 6.6, GRIS, anchor="end"))
    # The resting potential
    p.append(f'<line x1="{ox}" y1="{oy-90}" x2="{W-50}" y2="{oy-90}" stroke="{TRAIT}" '
             f'stroke-width="1.2" stroke-dasharray="5 4"/>')
    p.append(txt(ox + 236, oy - 98, "resting potential ≈ −120 mV", 7, GRIS))
    # AP : pointe rapide
    ap = f"M{ox+40},{oy-90} L{ox+96},{oy-90} C{ox+104},{oy-90} {ox+108},{oy-232} " \
         f"{ox+118},{oy-232} C{ox+130},{oy-232} {ox+134},{oy-60} {ox+152},{oy-70} " \
         f"C{ox+172},{oy-80} {ox+186},{oy-90} {ox+216},{oy-90}"
    p.append(f'<path d="{ap}" fill="none" stroke="{BLEU}" stroke-width="2.4"/>')
    p.append(txt(ox + 118, oy - 244, "Action potential (AP)", 8.4, BLEU, weight="700"))
    p.append(txt(ox + 118, oy - 232 + 0, "", 7))
    p.append(txt(ox + 118, 282, "1–5 s · all or nothing", 7, GRIS))
    # The VP: slow, with a decaying amplitude
    vp = f"M{ox+250},{oy-90} C{ox+268},{oy-92} {ox+276},{oy-198} {ox+300},{oy-192} " \
         f"C{ox+330},{oy-184} {ox+356},{oy-126} {ox+400},{oy-104} " \
         f"C{ox+430},{oy-92} {ox+444},{oy-90} {ox+466},{oy-90}"
    p.append(f'<path d="{vp}" fill="none" stroke="{CUIVRE}" stroke-width="2.4"/>')
    p.append(txt(ox + 330, oy - 214, "Variation potential (VP)", 8.4, CUIVRE,
                 weight="700"))
    p.append(txt(ox + 330, 282, "10 s – several minutes · graded", 7, GRIS))
    # SWP / micro-fluctuations
    pts = " ".join(f"{ox+500+i*4},{oy-90+math.sin(i/2.4)*7+math.sin(i/7.0)*11:.1f}"
                   for i in range(0, 38))
    p.append(f'<polyline points="{pts}" fill="none" stroke="{SEVE}" stroke-width="2.2"/>')
    p.append(txt(ox + 574, oy - 134, "Micro-fluctuations", 8.4, SEVE, weight="700"))
    p.append(txt(ox + 574, oy - 122, "in conductance", 8.4, SEVE, weight="700"))
    p.append(txt(ox + 574, 282, "continuous · what the devices “read”", 7, GRIS))
    p.append(txt(W / 2, H - 14,
                 "Only the third family feeds the consumer music of the plants.",
                 9, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("action-potential.svg", "\n".join(p), W, H)


# =============================================================================
#  9. THE MIDI → DAW CHAIN
# =============================================================================
def midi_flow():
    W, H = 820, 220
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 34, "INTEGRATION INTO A DIGITAL AUDIO WORKSTATION", 12, SEVE,
                 weight="700", spacing="2"))
    blocks = [
        (28, 80, "ENCLOSURE", "MIDI out", SEVE),
        (232, 80, "INTERFACE", "DIN · TRS-A · USB · BLE", BLEU),
        (436, 80, "DAW", "Ableton · Ardour · Reaper", NUIT),
        (640, 80, "INSTRUMENT", "synth · sampler", OR),
    ]
    for x, y, t, sub, c in blocks:
        p.append(box(x, y, 152, 78, fill="#FBFAF4", stroke=c, rx=8, sw=1.8))
        p.append(f'<rect x="{x}" y="{y}" width="152" height="5" rx="2" fill="{c}"/>')
        p.append(txt(x + 76, y + 36, t, 9.4, NUIT, weight="700"))
        p.append(txt(x + 76, y + 58, sub, 6.6, GRIS))
        if x < 640:
            p.append(arrow(x + 156, y + 39, x + 200, y + 39))
    p.append(txt(W / 2, H - 14,
                 "MIDI is a score, not a recording.",
                 8.6, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("midi-flow.svg", "\n".join(p), W, H)


# =============================================================================
# 10. THE MYCORRHIZAL NETWORK
# =============================================================================
def wood_wide_web():
    W, H = 800, 500
    p = [f'<rect width="{W}" height="{H}" fill="#FBFAF4"/>', ARROWDEFS]
    rng = random.Random(11)
    ground = 268
    p.append(f'<rect x="0" y="{ground}" width="{W}" height="{H-ground}" fill="#EFE7DA"/>')
    p.append(f'<line x1="0" y1="{ground}" x2="{W}" y2="{ground}" stroke="{CUIVRE}" '
             f'stroke-width="1.6" opacity=".6"/>')
    trees = [(130, 52, 4), (310, 64, 6), (500, 48, 3), (680, 60, 8)]
    nodes = []
    for cx, hh, sd in trees:
        p.append(fractal_tree(cx, ground, hh, depth=7, color="#2C5D45", seed=sd))
        for k in range(3):
            nx = cx + rng.uniform(-44, 44)
            ny = ground + rng.uniform(28, 150)
            nodes.append((nx, ny))
            p.append(f'<path d="M{cx},{ground} Q{(cx+nx)/2},{(ground+ny)/2+12} {nx:.0f},{ny:.0f}" '
                     f'stroke="#8B6F4E" stroke-width="1.8" fill="none"/>')
    for i, (x1, y1) in enumerate(nodes):
        for j, (x2, y2) in enumerate(nodes):
            if j <= i:
                continue
            if math.hypot(x2 - x1, y2 - y1) < 215:
                p.append(f'<path d="M{x1:.0f},{y1:.0f} Q{(x1+x2)/2:.0f},'
                         f'{(y1+y2)/2+rng.uniform(-18,18):.0f} {x2:.0f},{y2:.0f}" '
                         f'stroke="{SEVE_C}" stroke-width="1" fill="none" '
                         f'opacity="{rng.uniform(.3,.7):.2f}"/>')
    for x, y in nodes:
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.6" fill="{OR}" opacity=".9"/>')
    for i, (lab, c) in enumerate([("carbon", OR), ("nitrogen, phosphorus", SEVE),
                                  ("alarm signals", CUIVRE)]):
        y = 434 + i * 18
        p.append(f'<line x1="40" y1="{y-4}" x2="68" y2="{y-4}" stroke="{c}" stroke-width="2.6"/>')
        p.append(txt(76, y, lab, 7.6, NUIT, anchor="start"))
    p.append(txt(W - 40, ground - 14, "canopy", 7.6, GRIS, style="italic", anchor="end"))
    p.append(txt(W - 40, ground + 22, "rhizosphere", 7.6, GRIS, style="italic", anchor="end"))
    # the title sits above the drawing, on a light band
    p.append(f'<rect x="0" y="0" width="{W}" height="54" fill="#FBFAF4" opacity=".93"/>')
    p.append(txt(W / 2, 34, "THE MYCORRHIZAL NETWORK — THE “WOOD WIDE WEB”", 12, SEVE,
                 weight="700", spacing="1.6"))
    p.append(txt(W / 2, H - 12,
                 "The electrodes listen to a single individual; the tree is already networked.",
                 8.6, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("wood-wide-web.svg", "\n".join(p), W, H)


# =============================================================================
# 11. NOTE MAPPING: FROM THE DELTA TO THE SCALE
# =============================================================================
def mapping():
    W, H = 800, 250
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 34, "FROM NUMBER TO NOTE: THE MAPPING", 12, SEVE,
                 weight="700", spacing="2"))
    p.append(box(24, 64, 226, 150, fill="#F2F7FB", stroke=BLEU, rx=8, sw=1.6))
    p.append(txt(137, 90, "① ANALYSIS WINDOW", 8.2, BLEU, weight="700", spacing="1"))
    vals = [412, 418, 409, 431, 522, 508, 415, 410, 421]
    for i, v in enumerate(vals):
        x = 42 + i * 23
        h = (v - 390) * 0.70
        p.append(f'<rect x="{x}" y="{188-h:.0f}" width="15" height="{h:.0f}" rx="2" '
                 f'fill="{BLEU}" opacity="{0.42 if v<480 else 0.95}"/>')
    p.append(f'<line x1="38" y1="188" x2="240" y2="188" stroke="{GRIS}" stroke-width="1"/>')
    p.append(txt(137, 206, "9 successive periods (µs)", 7, GRIS))

    p.append(box(288, 64, 224, 150, fill="#FDF7E6", stroke=OR, rx=8, sw=1.6))
    p.append(txt(400, 90, "② DETECTION", 8.2, OR, weight="700", spacing="1"))
    for i, line in enumerate(["μ = 438 µs", "σ = 41 µs", "delta = 113 µs",
                               "threshold = σ × 2.3 = 94", "113 > 94 → EVENT"]):
        p.append(txt(400, 114 + i * 20, line, 7.6,
                     NUIT if i < 4 else SEVE, weight="700" if i == 4 else "400",
                     family="DejaVu Sans Mono, monospace"))

    p.append(box(550, 64, 226, 150, fill="#EDF6F0", stroke=SEVE, rx=8, sw=1.6))
    p.append(txt(663, 90, "③ QUANTIZATION", 8.2, SEVE, weight="700", spacing="1"))
    for i, n in enumerate(["C", "D", "E", "F", "G", "A", "B"]):
        x = 570 + i * 29
        fill = "#F2E2B8" if n == "G" else "#FFF"
        p.append(f'<rect x="{x}" y="{116}" width="23" height="48" rx="3" fill="{fill}" '
                 f'stroke="{SEVE}" stroke-width="1.2"/>')
        p.append(txt(x + 11, 146, n, 7.6, NUIT))
    p.append(txt(663, 186, "raw note 63 → G", 7, GRIS))
    for x1, x2 in [(252, 288), (514, 550)]:
        p.append(arrow(x1, 139, x2 - 4, 139))
    p.append(txt(W / 2, H - 12,
                 "The mapping is a human CHOICE: it decides what will be heard.",
                 8.6, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("mapping.svg", "\n".join(p), W, H)


# =============================================================================
# 12. THREE READINGS: SCIENCE / SYMBOL / EXPERIENCE
# =============================================================================
def three_reads():
    W, H = 720, 470
    p = [f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 32, "THREE READINGS OF ONE PHENOMENON", 11.5, SEVE,
                 weight="700", spacing="1.6"))
    circles = [(270, 210, BLEU, "MEASUREMENT", "what the instrument records"),
               (450, 210, SEVE, "SYMBOL", "what culture projects onto it"),
               (360, 300, OR, "EXPERIENCE", "what you feel")]
    for cx, cy, c, t, s in circles:
        p.append(f'<circle cx="{cx}" cy="{cy}" r="110" fill="{c}" opacity=".13" '
                 f'stroke="{c}" stroke-width="1.6"/>')
    p.append(txt(210, 150, "MEASUREMENT", 12, BLEU, weight="700",
                 family="Cormorant Garamond, serif"))
    p.append(txt(210, 166, "µV, MΩ, ms", 7.6, GRIS))
    p.append(txt(512, 150, "SYMBOL", 12, SEVE, weight="700",
                 family="Cormorant Garamond, serif"))
    p.append(txt(512, 166, "story, tradition", 7.6, GRIS))
    p.append(txt(360, 420, "EXPERIENCE", 12, OR, weight="700",
                 family="Cormorant Garamond, serif"))
    p.append(txt(360, 438, "feeling, presence", 7.6, GRIS))
    p.append(txt(360, 236, "MUSIC", 13, NUIT, weight="700",
                 family="Cormorant Garamond, serif"))
    p.append(txt(360, 252, "of the plants", 9, NUIT, style="italic",
                 family="Cormorant Garamond, serif"))
    p.append(txt(W / 2, H - 10,
                 "Confusing the three circles produces confusion; separating them produces clarity.",
                 8.6, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("three-reads.svg", "\n".join(p), W, H)


# =============================================================================
# 13. HEART COHERENCE
# =============================================================================
def heart():
    W, H = 700, 300
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 32, "THE HEART AS A TUNER", 12, SEVE, weight="700",
                 spacing="2"))
    rng = random.Random(5)
    pts = [f"{60+i*3.0:.1f},{112+math.sin(i/3.1)*16+rng.uniform(-14,14):.1f}"
           for i in range(190)]
    p.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{CUIVRE}" '
             f'stroke-width="1.8"/>')
    p.append(txt(60, 76, "BEFORE — disordered variability", 9, CUIVRE, anchor="start",
                 weight="700"))
    p.append(txt(60, 158, "irregular breathing, busy mind", 7.6, GRIS,
                 anchor="start"))
    pts = [f"{60+i*3.0:.1f},{242+math.sin(i/9.55)*26:.1f}" for i in range(190)]
    p.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{SEVE}" '
             f'stroke-width="2.4"/>')
    p.append(txt(60, 200, "AFTER — 5 / 5 coherence", 9, SEVE, anchor="start",
                 weight="700"))
    p.append(txt(60, 290, "5 s breathing in · 5 s breathing out · 6 cycles per minute",
                 7.6, GRIS, anchor="start"))
    write("heart.svg", "\n".join(p), W, H)


# =============================================================================
# 14. TRISKELE / OGHAM — A DRUIDIC MOTIF
# =============================================================================
def triskell():
    W, H = 420, 420
    cx, cy, R = 210, 200, 130
    p = [f'<rect width="{W}" height="{H}" fill="none"/>']
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{R+22}" fill="none" stroke="{OR}" '
             f'stroke-width="1.2" opacity=".55"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{R+14}" fill="none" stroke="{OR}" '
             f'stroke-width="2.4"/>')
    for k in range(3):
        a = math.radians(90 + k * 120)
        d = []
        for t in range(0, 210, 6):
            tt = math.radians(t)
            r = R * (1 - t / 260.0)
            x = cx + math.cos(a + tt) * r
            y = cy - math.sin(a + tt) * r
            d.append(f"{'M' if t == 0 else 'L'}{x:.1f},{y:.1f}")
        p.append(f'<path d="{" ".join(d)}" fill="none" stroke="{SEVE}" '
                 f'stroke-width="7" stroke-linecap="round"/>')
        p.append(f'<path d="{" ".join(d)}" fill="none" stroke="{OR_CL}" '
                 f'stroke-width="2" stroke-linecap="round" opacity=".8"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="9" fill="{OR}"/>')
    # A stylised ogham at the bottom
    y = 372
    p.append(f'<line x1="120" y1="{y}" x2="300" y2="{y}" stroke="{NUIT}" '
             f'stroke-width="2"/>')
    groups = [1, 3, 2, 4, 2]
    x = 134
    for g in groups:
        for i in range(g):
            p.append(f'<line x1="{x+i*5}" y1="{y-14}" x2="{x+i*5}" y2="{y}" '
                     f'stroke="{NUIT}" stroke-width="1.8"/>')
        x += g * 5 + 16
    write("triskell.svg", "\n".join(p), W, H)


# =============================================================================
# 15. LEAF ANATOMY (the measurement site)
# =============================================================================
def leaf_anatomy():
    W, H = 720, 300
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 32, "ANATOMY OF THE MEASUREMENT SITE", 12, SEVE, weight="700",
                 spacing="2"))
    x0, y0, w, h = 40, 90, 330, 110
    p.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="20" fill="#3E7F5C"/>')
    p.append(f'<rect x="{x0}" y="{y0+20}" width="{w}" height="38" fill="#63A882"/>')
    p.append(f'<rect x="{x0}" y="{y0+58}" width="{w}" height="32" fill="#8FC6A8"/>')
    p.append(f'<rect x="{x0}" y="{y0+90}" width="{w}" height="20" fill="#4B8A68"/>')
    p.append(f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" '
             f'stroke="{NUIT}" stroke-width="1.4"/>')
    for s2, y in [("cuticle + upper epidermis", 104),
                  ("palisade mesophyll", 143),
                  ("spongy mesophyll", 178),
                  ("lower epidermis + stomata", 200)]:
        p.append(f'<line x1="{x0+w}" y1="{y}" x2="{x0+w+18}" y2="{y}" stroke="{GRIS}" '
                 f'stroke-width="1"/>')
        p.append(txt(x0 + w + 24, y + 4, s2, 8.6, NUIT, anchor="start"))
    for i in range(5):
        x = x0 + 36 + i * 66
        p.append(f'<ellipse cx="{x}" cy="{y0+h}" rx="11" ry="5" fill="#FFF" '
                 f'stroke="{NUIT}" stroke-width="1.2"/>')
        p.append(f'<ellipse cx="{x}" cy="{y0+h}" rx="3.4" ry="2" fill="{NUIT}"/>')
    p.append(f'<rect x="150" y="{y0+h+8}" width="46" height="15" rx="3" fill="#D8D8D0" '
             f'stroke="{GRIS}" stroke-width="1.2"/>')
    p.append(txt(173, y0 + h + 46, "electrode", 8.2, CUIVRE))
    p.append(f'<path d="M173,{y0+h+8} L173,{y0+h}" stroke="{CUIVRE}" stroke-width="2"/>')
    for i in range(4):
        x = x0 + 52 + i * 80
        p.append(f'<path d="M{x},{y0+104} C{x+6},{y0+76} {x-6},{y0+50} {x},{y0+26}" '
                 f'stroke="{BLEU}" stroke-width="1.6" fill="none" opacity=".7" '
                 f'marker-end="url(#ahb)"/>')
    p.append(txt(205, y0 - 12, "upward water flow (transpiration)", 7.6, BLEU))
    p.append(txt(W / 2, H - 14,
                 "The electrode goes on the underside: the moistest point of the blade.",
                 8.6, GRIS, family="Cormorant Garamond, serif", style="italic"))
    write("leaf-anatomy.svg", "\n".join(p), W, H)


# =============================================================================
# 16. THE LISTENING PROTOCOL — THE SEVEN STEPS
# =============================================================================
def protocol_seven():
    W, H = 800, 500
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 30, "THE SEVEN-STEP LISTENING PROTOCOL", 11.5, SEVE,
                 weight="700", spacing="1.6"))
    steps = [("Choose", "the plant and the hour"),
             ("Prepare", "the place, the silence"),
             ("Attune", "coherence, 3 minutes"),
             ("Ask", "inner consent"),
             ("Place", "the electrodes, unhurried"),
             ("Listen", "20 minutes without touching"),
             ("Record", "the journal, then give thanks")]
    cx, cy, R = 400, 272, 136
    for i, (t, s) in enumerate(steps):
        a = math.radians(-90 + i * (360 / 7))
        x = cx + math.cos(a) * R
        y = cy + math.sin(a) * R
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="34" fill="#FBFAF4" '
                 f'stroke="{SEVE}" stroke-width="1.8"/>')
        p.append(f'<circle cx="{x:.0f}" cy="{y-24:.0f}" r="11" fill="{OR}"/>')
        p.append(txt(x, y - 19, str(i + 1), 8.4, "#FFF", weight="700"))
        p.append(txt(x, y + 8, t, 8.2, NUIT, weight="700"))
        # the caption on the outside
        lx = cx + math.cos(a) * (R + 74)
        ly = cy + math.sin(a) * (R + 74)
        anc = "middle"
        if lx > cx + 30: anc = "start"
        elif lx < cx - 30: anc = "end"
        p.append(txt(lx, ly, s, 7.2, GRIS, anchor=anc))
        # the arc to the next one
        a2 = math.radians(-90 + (i + 1) * (360 / 7))
        x2 = cx + math.cos(a2) * R
        y2 = cy + math.sin(a2) * R
        p.append(f'<path d="M{x:.0f},{y:.0f} A{R},{R} 0 0 1 {x2:.0f},{y2:.0f}" '
                 f'fill="none" stroke="{TRAIT}" stroke-width="1.4"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="50" fill="{NUIT}"/>')
    p.append(txt(cx, cy - 4, "LISTENING", 10, OR_CL, weight="700", spacing="1.2"))
    p.append(txt(cx, cy + 12, "45 – 60 min", 8, IVOIRE))
    write("protocole-sept.svg", "\n".join(p), W, H)


# =============================================================================
# 17. THE COMPLETE DIY DIAGRAM
# =============================================================================
def diy():
    W, H = 860, 350
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="#FFFFFF"/>']
    p.append(txt(W / 2, 34, "DIY DEVICE — WIRING OVERVIEW", 12, SEVE,
                 weight="700", spacing="2"))
    blocks = [
        (28, 80, 178, 92, "PROBES", "2 crocodile clips|+ stainless-steel electrodes", SEVE),
        (246, 80, 178, 92, "NE555", "astable|C1 4.2 nF · R2 100 kΩ", BLEU),
        (464, 80, 178, 92, "ARDUINO", "Nano / Pro Mini|16 MHz · INT0", BLEU),
        (682, 80, 150, 92, "MIDI OUT", "5-pin DIN or|TRS-A · 220 Ω", OR),
        (246, 232, 178, 84, "POWER", "3 × AA or|LiPo + regulator", NUIT),
        (464, 232, 178, 84, "INDICATORS", "6 LEDs + R 220 Ω|note indication", NUIT),
        (682, 232, 150, 84, "SYNTH / DAW", "MIDI instrument|or computer", OR),
    ]
    for x, y, w, h, t, sub, c in blocks:
        p.append(box(x, y, w, h, fill="#FBFAF4", stroke=c, rx=8, sw=1.8))
        p.append(f'<rect x="{x}" y="{y}" width="{w}" height="5" rx="2" fill="{c}"/>')
        p.append(txt(x + w / 2, y + 34, t, 9.2, NUIT, weight="700"))
        for k, line in enumerate(sub.split("|")):
            p.append(txt(x + w / 2, y + 56 + k * 17, line, 6.8, GRIS))
    for x1, x2 in [(206, 246), (424, 464), (642, 682)]:
        p.append(arrow(x1, 126, x2 - 4, 126))
    p.append(arrow(335, 232, 335, 176))
    p.append(f'<path d="M553,172 v56" stroke="{OR}" stroke-width="2.2" '
             f'marker-end="url(#ah)"/>')
    p.append(f'<path d="M832,126 v148 h-40" stroke="{OR}" stroke-width="2.2" '
             f'fill="none" marker-end="url(#ah)"/>')
    p.append(txt(310, 210, "5 V", 7.4, NUIT, anchor="end"))
    p.append(txt(566, 208, "PWM", 7.4, OR, anchor="start"))
    write("diy.svg", "\n".join(p), W, H)


# =============================================================================
# 18. DECORATIVE MOTIFS
# =============================================================================
def seed_of_life():
    W = H = 320
    cx, cy, r = 160, 160, 52
    p = [f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{OR_CL}" '
         f'stroke-width="1.6"/>']
    for k in range(6):
        a = math.radians(k * 60)
        p.append(f'<circle cx="{cx+math.cos(a)*r:.1f}" cy="{cy+math.sin(a)*r:.1f}" '
                 f'r="{r}" fill="none" stroke="{OR_CL}" stroke-width="1.6"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{r*2}" fill="none" stroke="{OR}" '
             f'stroke-width="2"/>')
    write("seed-of-life.svg", "\n".join(p), W, H)


def sound_waves():
    W, H = 600, 200
    p = [f'<rect width="{W}" height="{H}" fill="none"/>']
    for k in range(4):
        amp = 46 - k * 10
        pts = " ".join(f"{x},{100+math.sin(x/(26.0-k*3))*amp:.1f}"
                       for x in range(10, W - 10, 5))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{SEVE if k%2 else OR}" '
                 f'stroke-width="{2.2-k*0.4:.1f}" opacity="{0.9-k*0.18:.2f}"/>')
    write("sound-waves.svg", "\n".join(p), W, H)


# =============================================================================
def main():
    print("• Generating the illustrations…")
    cover_art()
    for i, s in enumerate((31, 47, 59, 73, 89, 101, 113, 127, 139, 151), start=1):
        part_bg(i, s)
    timeline()
    pipeline()
    electrodes()
    wheatstone()
    ne555()
    action_potential()
    midi_flow()
    wood_wide_web()
    mapping()
    three_reads()
    heart()
    triskell()
    leaf_anatomy()
    protocol_seven()
    diy()
    seed_of_life()
    sound_waves()
    n = len([f for f in os.listdir(HERE) if f.endswith(".svg")])
    print(f"✓ {n} illustrations generated in {HERE}")


if __name__ == "__main__":
    main()
