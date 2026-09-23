#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/assets/svg/gen_board.py
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
Figure generator for the companion volume *The PhytoSense Board*.

Every figure — circuit diagrams, block diagrams, board layouts, software
diagrams — is drawn here deterministically, so that the document is
reproducible in full from its sources.

Usage:  python3 gen_board.py
Output: pdf-src/assets/svg/board-*.svg
"""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Palette (the same one as book.css) -------------------------------------
NUIT   = "#0E2A22"
NUIT2  = "#17392F"
SEVE   = "#3F7D5A"
SEVE_C = "#6FA98A"
SEVE_P = "#E9F2EC"
OR     = "#B08528"
OR_CL  = "#E0C073"
OR_PL  = "#F7F0DC"
IVOIRE = "#FBF9F1"
GRIS   = "#6B7A72"
TRAIT  = "#D9D9C6"
BLEU   = "#2F5E86"
BLEU_P = "#EAF1FB"
CUIVRE = "#A8552E"
CUIV_P = "#FBEEE6"
INK    = "#23302C"

# Text sizes are expressed in REAL TYPOGRAPHIC POINTS as printed. Every figure
# knows its printed width (print_mm) and derives the unit-to-point factor from
# it: a full-page figure (125 mm) and a landscape plate (212 mm) therefore show
# the same body size, whatever the size of their viewBox. Readability floor:
# 5.6 pt.
MM_PAR_POINT = 0.352777
PT_MIN       = 5.6

# ---- The identity every figure carries --------------------------------------
#  A drawing that circulates without an author's name or an address becomes
#  anonymous in two copies. These three strings are therefore repeated on the
#  title block of every
#  sheet, on the board's silkscreen and in the bill of materials.
AUTEUR   = "Bretagne Namasté"
SITE     = "bretagne-namaste.com"
CONTACT  = "contact@bretagne-namaste.com"
PROJET   = "PhytoSense One"
LICENCE  = "CERN-OHL-P v2"

MONO = "DejaVu Sans Mono, monospace"
SANS = "Lato, sans-serif"
SERIF = "Cormorant Garamond, serif"


# =============================================================================
#  SOCLE DE DESSIN
# =============================================================================
class Sheet:
    """An SVG sheet: a list of elements plus wiring helpers."""

    def __init__(self, w=980, h=600, bg="#FFFFFF", print_mm=125.0):
        self.w, self.h, self.bg = w, h, bg
        self.print_mm = print_mm
        # viewBox units per printed typographic point
        self.tf = MM_PAR_POINT * w / print_mm
        self.body = []

    def add(self, *chunks):
        for c in chunks:
            if c:
                self.body.append(c)
        return self

    # ---- geometric primitives ----------------------------------------------
    def rect(self, x, y, w, h, fill="none", stroke=INK, sw=1.4, rx=0, dash=None,
             op=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        o = f' opacity="{op}"' if op else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
                 f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')
        return self

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=1.4, op=None):
        o = f' opacity="{op}"' if op else ""
        self.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" '
                 f'stroke="{stroke}" stroke-width="{sw}"{o}/>')
        return self

    def line(self, x1, y1, x2, y2, stroke=INK, sw=1.4, dash=None, cap="round"):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="{cap}"{d}/>')
        return self

    def path(self, d, stroke=INK, sw=1.4, fill="none", dash=None, cap="round"):
        da = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linecap="{cap}" stroke-linejoin="round"{da}/>')
        return self

    def poly(self, pts, fill="none", stroke=INK, sw=1.4):
        p = " ".join(f"{x},{y}" for x, y in pts)
        self.add(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linejoin="round"/>')
        return self

    # ---- texte --------------------------------------------------------------
    def txt(self, x, y, s, size=6.2, fill=INK, anchor="middle", family=SANS,
            weight="400", style="normal", spacing="0", rot=None, op=None):
        size = round(max(size, PT_MIN) * self.tf, 2)
        o = f' opacity="{op}"' if op else ""
        t = (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
             f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
             f'font-style="{style}" letter-spacing="{spacing}"{o}>{esc(s)}</text>')
        if rot is not None:
            t = f'<g transform="rotate({rot},{x},{y})">{t}</g>'
        self.add(t)
        return self

    def mono(self, x, y, s, size=7, fill=INK, anchor="middle", weight="400", op=None):
        return self.txt(x, y, s, size=size, fill=fill, anchor=anchor,
                        family=MONO, weight=weight, op=op)

    def title(self, s, sub=None, x=None, y=None):
        x = self.w / 2 if x is None else x
        y = 13 * self.tf if y is None else y
        self.txt(x, y, s, size=11, family=SERIF, weight="700", fill=NUIT)
        if sub:
            self.txt(x, y + 11 * self.tf, sub, size=7.4, fill=GRIS, style="italic")
        return self

    # ---- câblage ------------------------------------------------------------
    def wire(self, *pts, stroke=INK, sw=1.35, dash=None):
        """An orthogonal wire through the given (x, y) points."""
        d = "M " + " L ".join(f"{x},{y}" for x, y in pts)
        return self.path(d, stroke=stroke, sw=sw, dash=dash, cap="square")

    def bus(self, *pts, stroke=BLEU, sw=3.0):
        return self.wire(*pts, stroke=stroke, sw=sw)

    def dot(self, x, y, r=3.6, fill=INK):
        self.add(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}"/>')
        return self

    def arrow(self, x1, y1, x2, y2, color=OR, sw=1.8, marker="ah"):
        self.add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
                 f'stroke-width="{sw}" marker-end="url(#{marker})"/>')
        return self

    def arrow_path(self, d, color=OR, sw=1.8, marker="ah"):
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" '
                 f'stroke-linecap="round" stroke-linejoin="round" '
                 f'marker-end="url(#{marker})"/>')
        return self

    # ---- sortie -------------------------------------------------------------
    def signer(self, y=None, discret=True):
        "Stamp the author and the address at the foot of the plate."
        y = (self.h - 8) if y is None else y
        couleur = GRIS if discret else NUIT
        self.txt(28, y, AUTEUR, size=5.6, fill=couleur, anchor="start")
        self.txt(self.w - 28, y, SITE, size=5.6, fill=couleur, anchor="end",
                 family=MONO)
        return self

    def save(self, name):
        bg = f'<rect width="{self.w}" height="{self.h}" fill="{self.bg}"/>' if self.bg else ""
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
               f'width="{self.w}" height="{self.h}">\n{DEFS}\n{bg}\n'
               + "\n".join(self.body) + "\n</svg>\n")
        with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
            f.write(svg)
        print("  ·", name)


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


DEFS = f'''<defs>
 <marker id="ah" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.5"
   markerHeight="5.5" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{OR}"/></marker>
 <marker id="ahb" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.5"
   markerHeight="5.5" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{BLEU}"/></marker>
 <marker id="ahv" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.5"
   markerHeight="5.5" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{SEVE}"/></marker>
 <marker id="ahk" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5"
   markerHeight="5" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{INK}"/></marker>
 <marker id="ahc" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.5"
   markerHeight="5.5" orient="auto-start-reverse">
   <path d="M0,0 L10,5 L0,10 z" fill="{CUIVRE}"/></marker>
 <pattern id="hatch" width="7" height="7" patternTransform="rotate(45)"
   patternUnits="userSpaceOnUse">
   <line x1="0" y1="0" x2="0" y2="7" stroke="{OR_CL}" stroke-width="2.4"/></pattern>
 <pattern id="hatchb" width="7" height="7" patternTransform="rotate(45)"
   patternUnits="userSpaceOnUse">
   <line x1="0" y1="0" x2="0" y2="7" stroke="#cfe0f2" stroke-width="2.8"/></pattern>
</defs>'''


# =============================================================================
#  STANDARD SYMBOLS (IEC 60617)
# =============================================================================
def resistor(sh, x, y, ref="", val="", horiz=True, L=92, W=34, lab_above=True,
             color=INK):
    """IEC resistor (a rectangle). (x, y) = the wire's left or top end."""
    if horiz:
        bx = x + (L - 56) / 2
        sh.line(x, y, bx, y, stroke=color)
        sh.rect(bx, y - W / 2, 56, W, fill="#fff", stroke=color, sw=1.8)
        sh.line(bx + 56, y, x + L, y, stroke=color)
        if ref:
            sh.txt(bx + 28, y - W / 2 - 8 if lab_above else y + W / 2 + 20, ref,
                   size=6.6, fill=SEVE, weight="700")
        if val:
            sh.txt(bx + 28, y + W / 2 + 20 if lab_above else y - W / 2 - 8, val,
                   size=6.6, fill=INK, family=MONO)
        return (x + L, y)
    else:
        by = y + (L - 56) / 2
        sh.line(x, y, x, by, stroke=color)
        sh.rect(x - W / 2, by, W, 56, fill="#fff", stroke=color, sw=1.8)
        sh.line(x, by + 56, x, y + L, stroke=color)
        side = 1 if lab_above else -1
        if ref:
            sh.txt(x + side * (W / 2 + 8), by + 22, ref, size=6.6, fill=SEVE,
                   weight="700", anchor="start" if side > 0 else "end")
        if val:
            sh.txt(x + side * (W / 2 + 8), by + 44, val, size=6.6, fill=INK,
                   family=MONO, anchor="start" if side > 0 else "end")
        return (x, y + L)


def capacitor(sh, x, y, ref="", val="", horiz=True, L=76, plate=40, color=INK):
    """Non-polarised capacitor."""
    if horiz:
        m = x + L / 2
        sh.line(x, y, m - 7, y, stroke=color)
        sh.line(m - 7, y - plate / 2, m - 7, y + plate / 2, stroke=color, sw=2.6)
        sh.line(m + 7, y - plate / 2, m + 7, y + plate / 2, stroke=color, sw=2.6)
        sh.line(m + 7, y, x + L, y, stroke=color)
        if ref:
            sh.txt(m, y - plate / 2 - 8, ref, size=6.6, fill=SEVE, weight="700")
        if val:
            sh.txt(m, y + plate / 2 + 20, val, size=6.6, fill=INK, family=MONO)
        return (x + L, y)
    else:
        m = y + L / 2
        sh.line(x, y, x, m - 7, stroke=color)
        sh.line(x - plate / 2, m - 7, x + plate / 2, m - 7, stroke=color, sw=2.6)
        sh.line(x - plate / 2, m + 7, x + plate / 2, m + 7, stroke=color, sw=2.6)
        sh.line(x, m + 7, x, y + L, stroke=color)
        if ref:
            sh.txt(x + plate / 2 + 8, m - 4, ref, size=6.6, fill=SEVE,
                   weight="700", anchor="start")
        if val:
            sh.txt(x + plate / 2 + 8, m + 18, val, size=6.6, fill=INK,
                   family=MONO, anchor="start")
        return (x, y + L)


def ground(sh, x, y, kind="agnd", label=None, color=INK):
    """Grounds: agnd (analog), dgnd (digital), iso (floating), chassis."""
    sh.line(x, y, x, y + 18, stroke=color)
    if kind == "chassis":
        sh.line(x - 22, y + 18, x + 22, y + 18, stroke=color, sw=2.2)
        for dx in (-15, 0, 15):
            sh.line(x + dx, y + 18, x + dx - 10, y + 33, stroke=color, sw=1.6)
    elif kind == "iso":
        sh.poly([(x - 22, y + 18), (x + 22, y + 18), (x, y + 40)],
                fill="#fff", stroke=color, sw=2.0)
    elif kind == "dgnd":
        sh.line(x - 24, y + 18, x + 24, y + 18, stroke=color, sw=2.8)
        sh.line(x - 15, y + 26, x + 15, y + 26, stroke=color, sw=2.4)
        sh.line(x - 7, y + 34, x + 7, y + 34, stroke=color, sw=2.0)
    else:  # agnd : triangle plein
        sh.poly([(x - 22, y + 18), (x + 22, y + 18), (x, y + 40)],
                fill=color, stroke=color, sw=1.0)
    if label:
        sh.txt(x, y + 58, label, size=6.3, fill=GRIS, family=MONO)
    return (x, y)


def rail(sh, x, y, label, up=True, color=CUIVRE):
    """A supply-rail marker."""
    d = -1 if up else 1
    sh.line(x, y, x, y + d * 20, stroke=color)
    sh.line(x - 19, y + d * 20, x + 19, y + d * 20, stroke=color, sw=2.4)
    sh.txt(x, y + d * 20 + (-9 if up else 25), label, size=6.5, fill=color,
           family=MONO, weight="700")
    return (x, y)


def opamp(sh, x, y, w=120, h=104, ref="", part="", inv_top=True, fill="#fff"):
    """Operational amplifier. Returns the dictionary of its pins."""
    sh.poly([(x, y), (x + w, y + h / 2), (x, y + h)], fill=fill, stroke=INK, sw=1.6)
    ya, yb = y + h * 0.28, y + h * 0.72
    s1, s2 = ("−", "+") if inv_top else ("+", "−")
    sh.txt(x + 20, ya + 9, s1, size=9.5, fill=INK, weight="700")
    sh.txt(x + 20, yb + 9, s2, size=9.5, fill=INK, weight="700")
    if ref:
        sh.txt(x + w * 0.36, y + h / 2 - 5, ref, size=6.5, fill=SEVE,
               weight="700", anchor="start")
    if part:
        sh.txt(x + w * 0.36, y + h / 2 + 15, part, size=7.8, fill=GRIS,
               anchor="start", family=MONO)
    return {"in-": (x, ya) if inv_top else (x, yb),
            "in+": (x, yb) if inv_top else (x, ya),
            "top": (x, ya), "bot": (x, yb),
            "out": (x + w, y + h / 2),
            "vcc": (x + w * 0.33, y + h * 0.16),
            "vee": (x + w * 0.33, y + h * 0.84)}


def inamp(sh, x, y, w=190, h=180, ref="U?", part="INA828", rg=True):
    """Instrumentation amplifier (a triangle with RG pins)."""
    sh.poly([(x, y), (x + w, y + h / 2), (x, y + h)], fill="#fff", stroke=INK, sw=1.7)
    ya, yb = y + h * 0.22, y + h * 0.78
    sh.txt(x + 24, ya + 9, "+", size=9.5, weight="700")
    sh.txt(x + 24, yb + 9, "−", size=9.5, weight="700")
    sh.txt(x + w * 0.30, y + h / 2 - 6, ref, size=7, fill=SEVE, weight="700", anchor="start")
    sh.txt(x + w * 0.30, y + h / 2 + 16, part, size=6.2, fill=GRIS, anchor="start", family=MONO)
    pins = {"in+": (x, ya), "in-": (x, yb), "out": (x + w, y + h / 2),
            "ref": (x + w * 0.52, y + h * 0.80)}
    if rg:
        pins["rg1"] = (x + w * 0.23, y + h * 0.36)
        pins["rg2"] = (x + w * 0.23, y + h * 0.64)
        sh.line(x + 44, y + h * 0.36, x + 66, y + h * 0.36, stroke=INK, sw=1.4)
        sh.line(x + 44, y + h * 0.64, x + 66, y + h * 0.64, stroke=INK, sw=1.4)
    return pins


def block(sh, x, y, w, h, title, sub=None, lines=None, fill="#fff", stroke=SEVE,
          rx=7, sw=1.6, tcol=NUIT, dash=None, tsize=8.2):
    sh.rect(x, y, w, h, fill=fill, stroke=stroke, rx=rx, sw=sw, dash=dash)
    cy = y + (32 if (sub or lines) else h / 2 + 8)
    sh.txt(x + w / 2, cy, title, size=tsize, fill=tcol, weight="700", family=SERIF)
    if sub:
        sh.txt(x + w / 2, cy + 20, sub, size=6.0, fill=GRIS)
    if lines:
        y0 = cy + (46 if sub else 28)
        for i, ln in enumerate(lines):
            sh.txt(x + w / 2, y0 + i * 19, ln, size=6.1, fill=INK)
    return {"l": (x, y + h / 2), "r": (x + w, y + h / 2),
            "t": (x + w / 2, y), "b": (x + w / 2, y + h),
            "x": x, "y": y, "w": w, "h": h}


def conn(sh, x, y, n, label="", pitch=30, w=48, vertical=True, pinlabels=None,
         fill=OR_PL):
    """Connector: body plus pins."""
    h = n * pitch + 18
    sh.rect(x, y, w, h, fill=fill, stroke=OR, sw=1.5, rx=3)
    pts = []
    for i in range(n):
        py = y + 18 + i * pitch
        sh.line(x + w, py, x + w + 26, py, stroke=INK, sw=1.3)
        sh.circle(x + w - 9, py, 4.4, fill=OR, stroke=OR, sw=1)
        pts.append((x + w + 26, py))
        if pinlabels and i < len(pinlabels):
            sh.txt(x - 10, py + 7, pinlabels[i], size=6.2, fill=INK, anchor="end",
                   family=MONO)
    if label:
        sh.txt(x + w / 2, y - 12, label, size=6.6, fill=OR, weight="700")
    return pts


def diode(sh, x, y, horiz=True, L=64, zener=False, color=INK):
    if horiz:
        m = x + L / 2
        sh.line(x, y, m - 15, y, stroke=color)
        sh.poly([(m - 15, y - 16), (m - 15, y + 16), (m + 4, y)], fill=color, stroke=color, sw=1)
        sh.line(m + 4, y - 16, m + 4, y + 16, stroke=color, sw=2.6)
        sh.line(m + 4, y, x + L, y, stroke=color)
        return (x + L, y)
    m = y + L / 2
    sh.line(x, y, x, m - 15, stroke=color)
    sh.poly([(x - 16, m - 15), (x + 16, m - 15), (x, m + 4)], fill=color, stroke=color, sw=1)
    sh.line(x - 16, m + 4, x + 16, m + 4, stroke=color, sw=2.6)
    if zener:
        sh.line(x - 16, m + 4, x - 23, m + 12, stroke=color, sw=2.0)
        sh.line(x + 16, m + 4, x + 23, m - 4, stroke=color, sw=2.0)
    sh.line(x, m + 4, x, y + L, stroke=color)
    return (x, y + L)


def ferrite(sh, x, y, ref="", val="", L=76):
    sh.line(x, y, x + 12, y, stroke=INK)
    sh.rect(x + 12, y - 15, L - 24, 30, fill="#e9eceb", stroke=INK, sw=1.6, rx=5)
    sh.line(x + L - 12, y, x + L, y, stroke=INK)
    if ref:
        sh.txt(x + L / 2, y - 22, ref, size=6.3, fill=SEVE, weight="700")
    if val:
        sh.txt(x + L / 2, y + 34, val, size=6.2, fill=INK, family=MONO)
    return (x + L, y)


def barrier(sh, x, y0, y1, label="GALVANIC BARRIER", color=CUIVRE):
    """Trait mixte vertical d'isolation."""
    sh.line(x, y0, x, y1, stroke=color, sw=2.0, dash="12 6 3 6")
    sh.txt(x, y0 - 16, label, size=6.3, fill=color, weight="700", spacing="1.4")
    return x


def note(sh, x, y, w, lines, color=BLEU, fill=BLEU_P, title=None):
    h = 26 + len(lines) * 22 + (24 if title else 0)
    sh.rect(x, y, w, h, fill=fill, stroke=color, sw=1.1, rx=5)
    yy = y + 28
    if title:
        sh.txt(x + 14, yy, title, size=6.9, fill=color, weight="700", anchor="start")
        yy += 24
    for ln in lines:
        sh.txt(x + 14, yy, ln, size=6.3, fill=INK, anchor="start")
        yy += 22
    return h


# =============================================================================
#  1. ARCHITECTURE D'ENSEMBLE
# =============================================================================
def fig_archi():
    sh = Sheet(980, 820, print_mm=125)
    sh.title("Architecture d'ensemble — PhytoSense One",
             "Two supply islands, one isolation barrier, a single cable")

    # --- islands -------------------------------------------------------------
    sh.rect(20, 96, 648, 616, fill="#F3F8F5", stroke=SEVE, sw=1.4, rx=10, dash="8 5")
    sh.txt(344, 120, "FLOATING ANALOG ISLAND — AGND ground", size=6.6, fill=SEVE,
           weight="700", spacing="0.8")
    sh.rect(716, 96, 236, 616, fill="#EEF3FA", stroke=BLEU, sw=1.4, rx=10, dash="8 5")
    sh.txt(834, 120, "DIGITAL ISLAND (USB)", size=6.6, fill=BLEU,
           weight="700", spacing="0.8")
    barrier(sh, 692, 108, 712)

    # --- main analog chain ---------------------------------------------------
    chaine = [
        ("Electrodes and cable", "Ag/AgCl · shielded TRS · guard"),
        ("Input protection", "10 kΩ · BAV199 · PTC"),
        ("FE daughter board", "FE-Z electrometer / FE-B bridge"),
        ("Gain programmable", "OPA2189 · x1 to x200"),
        ("Anti-aliasing filter", "Bessel 3ᵉ ordre · 400 Hz"),
        ("CAN Δ-Σ 24 bits", "ADS131M04 · 4 channels · 32 kSPS"),
    ]
    ys = [146, 232, 318, 404, 490, 576]
    for (t, sub), y in zip(chaine, ys):
        block(sh, 44, y, 300, 56, t, sub, fill="#fff", stroke=SEVE, sw=1.7, tsize=8.0)
    for y in ys[:-1]:
        sh.arrow(194, y + 56, 194, y + 84, color=OR, sw=2.0)

    # --- servitudes ----------------------------------------------------------
    sh.rect(372, 134, 276, 428, fill="#FBF8EF", stroke=OR, sw=1.2, rx=8, dash="6 4")
    sh.txt(510, 154, "PRECISION SUPPORT", size=6.4, fill=OR, weight="700",
           spacing="1.2")
    serv = [
        ("2.5 V reference", "ADR4525 · 2 ppm/°C"),
        ("Calibrated self-test", "1 M / 10 M / 100 MΩ at 0.1 %"),
        ("Supply ±5 V", "LT3045 · LT3094 · 0,8 µV"),
        ("Base de temps", "TCXO 12,288 MHz · ±1 ppm"),
        ("Guard driver", "suiveur ×1 · Cin < 1 pF"),
    ]
    for i, (t, sub) in enumerate(serv):
        block(sh, 386, 170 + i * 78, 248, 58, t, sub, fill="#fff", stroke=OR_CL,
              sw=1.3, tsize=7.4)

    block(sh, 372, 576, 276, 56, "Capteurs d'ambiance",
          "BME688 · TSL2591 · PT1000", fill="#fff", stroke=SEVE_C, sw=1.4, tsize=7.4)

    # --- crossing the barrier ------------------------------------------------
    sh.wire((194, 632), (194, 664), (598, 664), stroke=INK, sw=2.0)
    sh.wire((510, 632), (510, 664), stroke=INK, sw=1.6)
    sh.dot(510, 664)
    block(sh, 598, 636, 188, 56, "Isolateurs", "ADuM4151 · 6 channels",
          fill=CUIV_P, stroke=CUIVRE, sw=1.8, tsize=7.6)

    # --- digital chain -------------------------------------------------------
    num = [
        (232, "USB-C socket", "CC 5,1 kΩ · ESD · 5 V"),
        (330, "Pile USB TinyUSB", "UAC2 + CDC + DFU"),
        (428, "Microcontroller", "RP2350 · 150 MHz"),
        (526, "MIDI TRS-A output", "external synth"),
    ]
    for y, t, sub in num:
        block(sh, 738, y, 194, 58, t, sub, fill="#fff", stroke=BLEU, sw=1.7, tsize=7.0)
    sh.wire((786, 664), (942, 664), (942, 457), (930, 457), stroke=INK, sw=2.0)
    sh.arrow(835, 428, 835, 392, color=BLEU, sw=2.0, marker="ahb")
    sh.arrow(835, 330, 835, 294, color=BLEU, sw=2.0, marker="ahb")
    sh.wire((740, 457), (726, 457), (726, 555), (740, 555), stroke=BLEU, sw=1.5, dash="5 4")

    # --- host ----------------------------------------------------------------
    block(sh, 96, 748, 440, 56, "Host computer — PhytoScope",
          "Linux · Windows · macOS — no driver to install",
          fill=NUIT, stroke=NUIT, sw=1.6, tcol=OR_CL, tsize=8.6)
    sh.wire((738, 261), (712, 261), (712, 776), (580, 776), stroke=BLEU, sw=2.6)
    sh.arrow(600, 776, 540, 776, color=BLEU, sw=2.4, marker="ahb")
    sh.txt(706, 742, "USB-C · 1 m · shielded", size=6.0, fill=BLEU, anchor="end")

    # --- plant input ---------------------------------------------------------
    sh.arrow(194, 78, 194, 142, color=SEVE, sw=2.4, marker="ahv")
    sh.txt(150, 74, "PLANT", size=7.4, fill=SEVE, weight="700", spacing="1.6",
           anchor="end")
    sh.signer()
    sh.save("carte-archi.svg")


# =============================================================================
#  2. MEASUREMENT CHAIN: LEVELS, GAINS, NOISE
# =============================================================================
def fig_chaine():
    sh = Sheet(980, 600, print_mm=125)
    sh.title("Measurement chain budget",
             "Signal level, gain and input-referred noise, stage by stage")

    etages = [
        ("Source", "plante", "1 µV – 50 mV", "—", "—"),
        ("Electrode", "Ag/AgCl", "×1", "0,15 µV", "1/f noise"),
        ("Input", "ADA4530-1", "×1", "0,42 µV", "14 nV/√Hz"),
        ("InAmp", "INA828", "×10", "0,21 µV", "7 nV/√Hz"),
        ("PGA", "OPA2189", "×1…200", "0,18 µV", "5,9 nV/√Hz"),
        ("Filter", "Bessel 3", "×1", "0,09 µV", "R 4,7 kΩ"),
        ("CAN", "ADS131M04", "24 bits", "0,31 µV", "plancher"),
    ]
    x0, w, gap = 40, 118, 15
    for i, (nom, part, gain, bruit, note_) in enumerate(etages):
        x = x0 + i * (w + gap)
        col = SEVE if i else NUIT
        fill = "#fff" if i else NUIT
        sh.rect(x, 110, w, 74, fill=fill, stroke=col, sw=1.7, rx=6)
        sh.txt(x + w / 2, 134, nom, size=7.8, weight="700", family=SERIF,
               fill=OR_CL if not i else NUIT)
        sh.txt(x + w / 2, 152, part, size=6.2, fill=OR_CL if not i else GRIS, family=MONO)
        sh.txt(x + w / 2, 172, gain, size=6.8, fill=OR_CL if not i else BLEU, weight="700")
        if i:
            sh.arrow(x - gap - 1, 147, x - 3, 147, color=OR, sw=1.8)
        # contribution de bruit
        sh.txt(x + w / 2, 214, bruit, size=6.8, fill=CUIVRE, weight="700", family=MONO)
        sh.txt(x + w / 2, 232, note_, size=5.8, fill=GRIS)

    sh.txt(40, 214, "", size=6)
    sh.line(40, 245, 940, 245, stroke=TRAIT, sw=1.2)
    sh.txt(40, 266, "Input-referred noise, 0.01 – 10 Hz band",
           size=7, fill=GRIS, anchor="start", style="italic")

    # --- histogram of contributions ------------------------------------------
    contrib = [("Electrode", 0.15), ("ADA4530-1", 0.42), ("INA828", 0.21),
               ("OPA2189", 0.18), ("Filter", 0.09), ("CAN", 0.31)]
    total = math.sqrt(sum(v * v for _, v in contrib))
    bx, by, bw, bh = 60, 300, 620, 190
    sh.rect(bx, by, bw, bh, fill="#FAFBFA", stroke=TRAIT, sw=1.1, rx=5)
    vmax = 0.5
    for i, (nom, v) in enumerate(contrib):
        x = bx + 34 + i * 96
        h = v / vmax * (bh - 56)
        sh.rect(x, by + bh - 30 - h, 44, h, fill=SEVE_C, stroke=SEVE, sw=1.2, rx=3)
        sh.txt(x + 22, by + bh - 36 - h, f"{v:.2f}".replace(".", ","), size=6.2,
               fill=NUIT, weight="700")
        sh.txt(x + 22, by + bh - 14, nom, size=6.0, fill=GRIS)
    sh.txt(bx + bw / 2, by - 8, "Each stage's contribution (µV rms)", size=6.8,
           fill=NUIT, weight="700")

    # quadrature
    sh.rect(706, 300, 234, 190, fill=NUIT, stroke=NUIT, rx=6)
    sh.txt(823, 328, "Somme quadratique", size=7.2, fill=OR_CL, weight="700", family=SERIF)
    sh.mono(823, 356, "√(Σ eₙ²)", size=8, fill="#EAF2EC")
    sh.txt(823, 396, f"{total:.2f}".replace(".", ",") + " µV eff.", size=13,
           fill="#fff", weight="700", family=SERIF)
    sh.txt(823, 424, "over 0.01 – 10 Hz", size=6.2, fill="#9fb8ab")
    sh.line(736, 440, 910, 440, stroke=SEVE, sw=1)
    sh.txt(823, 462, "that is 1 ADC LSB at x100", size=6.4, fill=OR_CL)
    sh.txt(823, 478, "dynamique utile : 126 dB", size=6.4, fill="#9fb8ab")
    sh.signer()
    sh.save("carte-chaine.svg")




# =============================================================================
#  OUTILLAGE DES PLANCHES (format CAO : cadre, zones, cartouche)
# =============================================================================
def frame(sh, marge=26, zones=("A", "B", "C", "D"), ncol=8):
    """Sheet frame with zone markers, in the manner of a CAD drawing."""
    x0, y0 = marge, marge
    x1, y1 = sh.w - marge, sh.h - marge
    sh.rect(x0, y0, x1 - x0, y1 - y0, fill="none", stroke=INK, sw=1.8)
    sh.rect(x0 + 16, y0 + 16, x1 - x0 - 32, y1 - y0 - 32, fill="none",
            stroke=TRAIT, sw=1.0)
    hcol = (x1 - x0 - 32) / ncol
    hrow = (y1 - y0 - 32) / len(zones)
    for i in range(1, ncol):
        for yy in (y0, y1 - 16):
            sh.line(x0 + 16 + i * hcol, yy, x0 + 16 + i * hcol, yy + 16,
                    stroke=TRAIT, sw=1.0)
    for i in range(ncol):
        for yy in (y0 + 12, y1 - 4):
            sh.txt(x0 + 16 + (i + .5) * hcol, yy, str(i + 1), size=5.6, fill=GRIS)
    for i in range(1, len(zones)):
        for xx in (x0, x1 - 16):
            sh.line(xx, y0 + 16 + i * hrow, xx + 16, y0 + 16 + i * hrow,
                    stroke=TRAIT, sw=1.0)
    for i, z in enumerate(zones):
        for xx in (x0 + 8, x1 - 8):
            sh.txt(xx, y0 + 16 + (i + .5) * hrow + 4, z, size=5.6, fill=GRIS)
    return (x0 + 16, y0 + 16, x1 - 16, y1 - 16)


def cartouche(sh, titre, sheet="1/8", rev="B", bloc="", w=402, h=138):
    """Standard title block, bottom right of the sheet.

    Three bands: the title; the assembly the sheet belongs to, with the
    author's name and the site address; the management markers. A drawing that
    circulates without those becomes anonymous by the second photocopy — which
    is what a title block is for.
    """
    x = sh.w - 26 - 16 - w
    y = sh.h - 26 - 16 - h
    sh.rect(x, y, w, h, fill="#FDFCF7", stroke=INK, sw=1.6)
    sh.line(x, y + 40, x + w, y + 40, stroke=INK, sw=1.2)
    sh.line(x, y + 92, x + w, y + 92, stroke=INK, sw=1.0)
    sh.line(x + w * 0.62, y + 40, x + w * 0.62, y + 92, stroke=INK, sw=1.0)
    sh.line(x + w * 0.31, y + 92, x + w * 0.31, y + h, stroke=INK, sw=1.0)
    sh.line(x + w * 0.81, y + 92, x + w * 0.81, y + h, stroke=INK, sw=1.0)

    sh.txt(x + w / 2, y + 27, titre, size=9, family=SERIF, weight="700", fill=NUIT)

    # -- identity band -------------------------------------------------------
    sh.txt(x + w * 0.31, y + 58, PROJET, size=7.4, weight="700", fill=SEVE)
    sh.txt(x + w * 0.31, y + 72, AUTEUR, size=6.4, fill=NUIT, family=SERIF)
    sh.txt(x + w * 0.31, y + 85, SITE, size=5.8, fill=GRIS, family=MONO)
    sh.txt(x + w * 0.81, y + 60, bloc or "Main board", size=7, fill=INK)
    sh.txt(x + w * 0.81, y + 76, LICENCE, size=5.6, fill=GRIS)
    sh.txt(x + w * 0.81, y + 87, "diffusion libre", size=5.4, fill=GRIS)

    for cx, lab, val in ((x + w * 0.155, "SHEET", sheet),
                         (x + w * 0.465, "REVISION", rev),
                         (x + w * 0.715, "DATE", "2026-09"),
                         (x + w * 0.905, "SCALE", "—")):
        sh.txt(cx, y + 110, lab, size=5.4, fill=GRIS, spacing="0.8")
        sh.txt(cx, y + 128, val, size=7, fill=INK, weight="700", family=MONO)
    return (x, y)


def connector(sh, x, y, n, label="", pitch=38, w=52, side="right",
              pinlabels=None, netlabels=None, fill=OR_PL, lead=30):
    """Generic connector; the pins leave to the right or to the left."""
    h = n * pitch + 20
    sh.rect(x, y, w, h, fill=fill, stroke=OR, sw=1.6, rx=3)
    pts = []
    for i in range(n):
        py = y + 20 + i * pitch
        if side == "right":
            sh.line(x + w, py, x + w + lead, py, stroke=INK, sw=1.3)
            sh.circle(x + w - 10, py, 4.2, fill=OR, stroke=OR, sw=1)
            pts.append((x + w + lead, py))
            tx, anch = x - 8, "end"
        else:
            sh.line(x - lead, py, x, py, stroke=INK, sw=1.3)
            sh.circle(x + 10, py, 4.2, fill=OR, stroke=OR, sw=1)
            pts.append((x - lead, py))
            tx, anch = x + w + 8, "start"
        if pinlabels and i < len(pinlabels):
            sh.txt(x + w / 2, py + 3, pinlabels[i], size=5.8, fill="#fff",
                   weight="700", family=MONO)
        if netlabels and i < len(netlabels):
            sh.txt(tx, py + 3, netlabels[i], size=6.2, fill=INK, anchor=anch,
                   family=MONO)
    if label:
        sh.txt(x + w / 2, y - 10, label, size=6.8, fill=OR, weight="700")
    return pts


def diode_up(sh, x, y, L=64, color=INK, zener=False):
    """Vertical diode conducting UPWARD; (x, y) = the bottom end."""
    m = y - L / 2
    sh.line(x, y, x, m + 15, stroke=color)
    sh.poly([(x - 16, m + 15), (x + 16, m + 15), (x, m - 4)], fill=color,
            stroke=color, sw=1)
    sh.line(x - 16, m - 4, x + 16, m - 4, stroke=color, sw=2.6)
    sh.line(x, m - 4, x, y - L, stroke=color)
    return (x, y - L)


def ic_box(sh, x, y, w, h, ref, part, sub=None):
    """Integrated-circuit body (a standard rectangle)."""
    sh.rect(x, y, w, h, fill="#FBFBF7", stroke=INK, sw=1.8, rx=3)
    sh.txt(x + w / 2, y + 22, ref, size=7.6, fill=SEVE, weight="700")
    sh.txt(x + w / 2, y + 40, part, size=7, fill=INK, family=MONO)
    if sub:
        sh.txt(x + w / 2, y + 58, sub, size=6, fill=GRIS)
    return {"l": x, "r": x + w, "t": y, "b": y + h, "cx": x + w / 2, "cy": y + h / 2}


# =============================================================================
#  SHEET 1 — ELECTROMETER INPUT STAGE (FE-Z daughter board)
# =============================================================================
def pl_frontend():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "FE-Z electrometer input", sheet="1/8",
              bloc="FE-Z daughter board")
    sh.txt(90, 76, "FE-Z · surface-potential measurement — 10¹⁵ Ω input impedance",
           size=8.4, fill=NUIT, weight="700", anchor="start", family=SERIF)

    # --- J1: the electrode connector ----------------------------------------
    pT, pR, pS = connector(sh, 92, 160, 3, "J1 · TRS 3,5 mm", pitch=72, w=54,
                           pinlabels=["T", "R", "S"])
    for i, t in enumerate(("T — measurement electrode",
                           "R — guard and cable shield",
                           "S — reference electrode")):
        sh.txt(92, 420 + i * 17, t, size=6, fill=GRIS, anchor="start")

    # --- input protection ----------------------------------------------------
    sh.wire(pT, (210, 180), stroke=INK)
    resistor(sh, 210, 180, "R1", "10 kΩ 0,1 %", L=92)
    sh.wire((302, 180), (370, 180), stroke=INK)
    sh.dot(370, 180)
    diode_up(sh, 370, 180, L=64)
    rail(sh, 370, 116, "+5 VA")
    diode_up(sh, 370, 244, L=64)
    sh.wire((370, 244), (370, 268), stroke=INK)
    rail(sh, 370, 268, "−5 VA", up=False)
    sh.txt(406, 200, "D1 · BAV199", size=6.2, fill=SEVE, anchor="start", weight="700")
    sh.txt(406, 216, "fuite < 1 pA", size=6, fill=GRIS, anchor="start")
    sh.txt(406, 232, "Cj = 1,5 pF", size=6, fill=GRIS, anchor="start")

    # --- polarisation --------------------------------------------------------
    sh.wire((370, 180), (530, 180), stroke=INK)
    sh.dot(530, 180)
    resistor(sh, 530, 180, "R2", "1 GΩ", horiz=False, L=92, lab_above=False)
    ground(sh, 530, 272, "agnd", "AGND")

    # --- U1: the electrometer ------------------------------------------------
    sh.rect(560, 100, 260, 300, fill="none", stroke=SEVE, sw=1.2, rx=6, dash="7 5")
    sh.txt(690, 122, "U1 · ADA4530-1", size=7.4, fill=SEVE, weight="700")
    sh.txt(690, 138, "Ib < 20 fA · integrated guard buffer", size=6, fill=GRIS)

    a = opamp(sh, 600, 151, w=130, h=112, ref="U1A", part="×1")
    sh.wire((530, 180), (560, 180), (560, 232), a["in+"], stroke=INK)
    sh.wire(a["out"], (790, 207), (790, 140), (582, 140), (582, 182), a["in-"],
            stroke=INK)
    sh.dot(790, 207)

    g = opamp(sh, 600, 290, w=120, h=84, ref="U1B", part="")
    sh.wire((560, 232), (560, 350), g["in+"], stroke=OR, sw=1.4, dash="6 4")
    sh.dot(560, 232)
    sh.wire(g["out"], (760, 332), (760, 384), (582, 384), (582, 314), g["in-"],
            stroke=INK)
    sh.dot(760, 332)

    # GUARD net: ring, shield, J1 pin R, mezzanine connector
    sh.wire((176, 252), (240, 252), (240, 440), (760, 440), (760, 332),
            stroke=OR, sw=1.8)
    sh.txt(272, 430, "“GUARD” NET — guard ring, cable shield, guard plane",
           size=6.2, fill=OR, weight="700", anchor="start")
    sh.wire((760, 332), (1090, 332), (1090, 272), (1150, 272), stroke=OR, sw=1.8)

    # --- sortie SIG_A --------------------------------------------------------
    sh.wire((790, 207), (1060, 207), (1060, 316), (1150, 316), stroke=INK, sw=1.7)
    sh.txt(940, 196, "SIG_A", size=6.6, fill=BLEU, weight="700", family=MONO)

    # --- J10 : connecteur mezzanine -----------------------------------------
    j10 = connector(sh, 1180, 120, 6, "J10 · mezzanine", pitch=44, w=56,
                    side="left", pinlabels=["1", "2", "3", "4", "5", "6"],
                    netlabels=["+5 VA", "−5 VA", "AGND", "GUARD", "SIG_A", "ID I²C"])
    for pin in j10[:3]:
        sh.line(pin[0], pin[1], pin[0] - 18, pin[1], stroke=INK, sw=1.2)
    sh.wire((1040, 360), j10[5], stroke=BLEU, sw=1.3, dash="5 4")
    sh.txt(1030, 356, "EEPROM 24AA02 (identification)", size=6, fill=BLEU,
           anchor="end")

    # --- common-mode feedback ------------------------------------------------
    sh.rect(420, 466, 480, 250, fill="#FBF8EF", stroke=OR_CL, sw=1.1, rx=6)
    sh.txt(432, 706, "COMMON-MODE FEEDBACK — driving the S electrode",
           size=6.4, fill=OR, weight="700", anchor="start")
    sh.wire((830, 207), (830, 496), (452, 496), (452, 532), (464, 532), stroke=INK)
    sh.dot(830, 207)
    resistor(sh, 464, 532, "R7", "1 MΩ", L=92)
    u2 = opamp(sh, 620, 506, w=110, h=92, ref="U2A", part="OPA2189")
    sh.wire((556, 532), u2["in-"], stroke=INK)
    sh.dot(574, 532)
    sh.wire(u2["in+"], (612, 578), (612, 600), stroke=INK)
    ground(sh, 612, 600, "agnd")
    sh.wire(u2["out"], (780, 552), stroke=INK)
    sh.dot(780, 552)
    sh.wire((780, 552), (780, 484), (688, 484), stroke=INK)
    resistor(sh, 596, 484, "R8", "100 kΩ", L=92)
    sh.wire((596, 484), (574, 484), (574, 532), stroke=INK)
    sh.wire((780, 552), (780, 676), (672, 676), stroke=INK)
    capacitor(sh, 596, 676, "C7", "470 nF", L=76, plate=34)
    sh.wire((596, 676), (574, 676), (574, 552), stroke=INK)

    # back to the reference electrode
    sh.wire((780, 552), (860, 552), (860, 748), (392, 748), stroke=INK)
    resistor(sh, 300, 748, "R9", "22 kΩ", L=92)
    sh.wire((300, 748), (200, 748), (200, 324), (176, 324), stroke=INK)
    sh.save("carte-fe-z.svg")


def netflag(sh, x, y, name, side="out", color=BLEU, w=None):
    """Off-sheet net label (the standard pentagon)."""
    w = w or max(56, 5.4 * len(name) + 18)
    h = 26
    if side == "out":
        pts = [(x, y - h / 2), (x + w - 12, y - h / 2), (x + w, y),
               (x + w - 12, y + h / 2), (x, y + h / 2)]
        tx = x + (w - 8) / 2
    else:
        pts = [(x + w, y - h / 2), (x + 12, y - h / 2), (x, y),
               (x + 12, y + h / 2), (x + w, y + h / 2)]
        tx = x + (w + 8) / 2
    sh.poly(pts, fill="#fff", stroke=color, sw=1.4)
    sh.txt(tx, y + 4, name, size=6.2, fill=color, weight="700", family=MONO)
    return (x + w, y) if side == "out" else (x, y)


def mux(sh, x, y, w=120, h=150, ref="U?", part="TMUX1208", n=4):
    """Analog multiplexer: body plus channels."""
    sh.rect(x, y, w, h, fill="#FBFBF7", stroke=INK, sw=1.8, rx=3)
    sh.txt(x + w / 2, y + 20, ref, size=7.2, fill=SEVE, weight="700")
    sh.txt(x + w / 2, y + 36, part, size=6.4, fill=INK, family=MONO)
    ins = []
    for i in range(n):
        py = y + 56 + i * (h - 70) / max(n - 1, 1)
        sh.line(x - 24, py, x, py, stroke=INK, sw=1.2)
        sh.txt(x + 10, py + 3, f"S{i+1}", size=5.6, fill=GRIS, anchor="start")
        ins.append((x - 24, py))
    out = (x + w + 24, y + h / 2)
    sh.line(x + w, y + h / 2, out[0], out[1], stroke=INK, sw=1.2)
    sh.txt(x + w - 12, y + h / 2 + 3, "D", size=5.6, fill=GRIS, anchor="end")
    sh.line(x + w / 2, y + h, x + w / 2, y + h + 18, stroke=BLEU, sw=1.2)
    sh.txt(x + w / 2, y + h + 32, "A0/A1", size=5.6, fill=BLEU, family=MONO)
    return ins, out


# =============================================================================
#  SHEET 2 — MEASUREMENT BRIDGE AND SYNCHRONOUS DETECTION (FE-B daughter board)
# =============================================================================
def pl_pont():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Measurement bridge and synchronous detection", sheet="2/8",
              bloc="FE-B daughter board")
    sh.txt(90, 76, "FE-B · impedance measurement by AC-excited bridge and synchronous demodulation", size=8.4, fill=NUIT, weight="700",
           anchor="start", family=SERIF)

    # --- excitation ----------------------------------------------------------
    netflag(sh, 92, 130, "EXC 1 kHz", side="in")
    sh.wire((168, 130), (340, 130), stroke=INK, sw=1.6)
    sh.dot(340, 130)
    sh.wire((340, 130), (620, 130), stroke=INK, sw=1.6)
    sh.txt(470, 116, "200 mV peak sine — microcontroller DAC", size=6, fill=GRIS)

    # --- reference branch ----------------------------------------------------
    sh.wire((340, 130), (340, 168), stroke=INK)
    resistor(sh, 340, 168, "R10", "1 MΩ", horiz=False, L=92, lab_above=False)
    sh.wire((340, 260), (340, 292), stroke=INK)
    sh.dot(340, 292)
    ins, out = mux(sh, 230, 360, w=110, h=240, ref="U6", part="TMUX1208", n=4)
    sh.wire((340, 292), (340, 340), (out[0], 340), (out[0], out[1]), stroke=INK)
    for i, (px, py) in enumerate(ins):
        lab = ["100 kΩ", "1 MΩ", "10 MΩ", "100 MΩ"][i]
        resistor(sh, 96, py, lab, "", L=110)
        sh.wire((206, py), (px, py), stroke=INK)
        sh.wire((96, py), (76, py), stroke=INK)
    sh.wire((76, ins[0][1]), (76, ins[-1][1]), stroke=INK)
    ground(sh, 76, ins[-1][1], "agnd", "AGND")
    sh.txt(285, 652, "reference ranges — switched automatically", size=6, fill=GRIS)

    # --- branche « plante » --------------------------------------------------
    sh.wire((620, 130), (620, 168), stroke=INK)
    resistor(sh, 620, 168, "R12", "10 kΩ", horiz=False, L=92, lab_above=False)
    sh.wire((620, 260), (620, 292), stroke=INK)
    sh.dot(620, 292)
    sh.wire((620, 292), (620, 400), stroke=INK)
    pT, pS = connector(sh, 660, 380, 2, "J1 · electrodes", pitch=64, w=54,
                       pinlabels=["T", "S"], side="left", lead=40)
    sh.wire((620, 400), pT, stroke=INK)
    sh.wire((620, 464), pS, stroke=INK)
    sh.wire((620, 464), (620, 510), stroke=INK)
    ground(sh, 620, 510, "agnd")
    sh.txt(736, 404, "R(plant)", size=6.4, fill=SEVE, anchor="start", weight="700")
    sh.txt(736, 420, "100 kΩ to 2 GΩ", size=6, fill=GRIS, anchor="start")

    # --- amplificateur d'instrumentation -------------------------------------
    ia = inamp(sh, 760, 170, w=190, h=180, ref="U3", part="INA828")
    sh.wire((340, 292), (400, 292), (400, 210), (760, 210), stroke=INK)
    sh.wire((620, 292), (740, 292), (740, 310), (760, 310), stroke=INK)
    sh.wire((760, 224), (700, 224), stroke=INK)
    sh.wire((760, 296), (700, 296), stroke=INK)
    resistor(sh, 700, 224, "R14", "6,19 kΩ", horiz=False, L=72, lab_above=False)
    sh.txt(676, 336, "G = 9,08", size=6.2, fill=BLEU, anchor="end", weight="700")
    sh.wire((859, 314), (859, 560), (880, 560), stroke=INK)
    netflag(sh, 880, 560, "V_OFFSET", side="in", color=CUIVRE, w=92)
    sh.txt(986, 556, "REF pin driven by the 16-bit DAC — re-centring",
           size=6, fill=CUIVRE, anchor="start")

    # --- synchronous demodulation --------------------------------------------
    sh.rect(990, 150, 310, 330, fill="#F5F8FB", stroke=BLEU, sw=1.2, rx=6, dash="7 5")
    sh.txt(1145, 172, "SYNCHRONOUS DETECTION", size=6.6, fill=BLEU, weight="700",
           spacing="1")
    ic_box(sh, 1010, 214, 130, 86, "U4", "ADG1419", "commutateur")
    sh.wire(ia["out"], (1010, 260), stroke=INK, sw=1.6)
    netflag(sh, 1012, 356, "REF_SQUARE", side="in", color=BLEU, w=96)
    sh.wire((1075, 330), (1075, 300), stroke=BLEU, sw=1.3, dash="5 4")
    sh.wire((1140, 240), (1164, 240), stroke=INK, sw=1.6)
    resistor(sh, 1164, 240, "R15", "100 kΩ", L=80)
    sh.dot(1244, 240)
    capacitor(sh, 1244, 250, "C10", "1 µF", horiz=False, L=76, plate=34)
    sh.wire((1244, 240), (1244, 250), stroke=INK)
    ground(sh, 1244, 326, "agnd")
    sh.wire((1244, 240), (1290, 240), stroke=INK, sw=1.6)
    sh.txt(1298, 222, "SIG_B", size=6.4, fill=BLEU, weight="700", family=MONO,
           anchor="end")
    sh.txt(1145, 424, "f₋₃dB = 1.6 Hz: only the component", size=6, fill=GRIS)
    sh.txt(1145, 440, "in phase with the excitation survives", size=6, fill=GRIS)

    # --- note ----------------------------------------------------------------
    note(sh, 92, 676, 800,
         ["The bridge is excited at 1 kHz and demodulated in phase: the chain's 1/f noise, the thermal",
          "drift and the mains hum all fall outside the useful band. Measured rejection: 62 dB at 50 Hz."],
         title="POURQUOI EXCITER EN ALTERNATIF ?")
    sh.save("carte-fe-b.svg")


# =============================================================================
#  SHEET 3 — MAIN BOARD: GAIN, FILTER, CONVERSION
# =============================================================================
def pl_mere():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Gain, filtering and conversion", sheet="3/8", bloc="Main board")
    sh.txt(90, 76, "Main chain — programmable gain, Bessel filter, 24-bit Δ-Σ converter", size=8.4, fill=NUIT, weight="700",
           anchor="start", family=SERIF)

    netflag(sh, 92, 256, "SIG_A", side="in", w=70)
    sh.wire((162, 256), (250, 256), (250, 256), stroke=INK, sw=1.6)

    # --- gain programmable ---------------------------------------------------
    sh.rect(200, 100, 420, 530, fill="none", stroke=SEVE, sw=1.2, rx=6, dash="7 5")
    sh.txt(410, 122, "PROGRAMMABLE GAIN x1 … x200", size=6.6, fill=SEVE,
           weight="700", spacing="1")
    a = opamp(sh, 300, 174, w=130, h=112, ref="U7A", part="OPA2189")
    sh.wire((250, 256), a["in+"], stroke=INK)
    sh.wire(a["out"], (480, 230), (480, 160), (422, 160), stroke=INK)
    resistor(sh, 330, 160, "R26", "20 kΩ", L=92)
    sh.wire((330, 160), (290, 160), (290, 205), a["in-"], stroke=INK)
    sh.dot(290, 205)
    ins, out = mux(sh, 330, 330, w=110, h=240, ref="U8", part="TMUX1208", n=4)
    sh.wire((290, 205), (290, 300), (556, 300), (556, out[1]), (out[0], out[1]),
            stroke=INK)
    for i, (px, py) in enumerate(ins):
        lab = ["20 kΩ", "2,2 kΩ", "1,05 kΩ", "100 Ω"][i]
        resistor(sh, 214, py, lab, "", L=92)
        sh.wire((306, py), (px, py), stroke=INK)
        sh.wire((214, py), (196, py), stroke=INK)
    sh.wire((196, ins[0][1]), (196, ins[-1][1]), stroke=INK)
    ground(sh, 196, ins[-1][1], "agnd", "AGND")

    # --- filtre de Bessel ----------------------------------------------------
    sh.rect(660, 100, 420, 400, fill="none", stroke=OR, sw=1.2, rx=6, dash="7 5")
    sh.txt(870, 122, "THIRD-ORDER BESSEL FILTER — 400 Hz", size=6.6, fill=OR,
           weight="700", spacing="1")
    sh.wire((480, 230), (688, 230), stroke=INK, sw=1.6)
    resistor(sh, 688, 230, "R24", "4,7 kΩ", L=84)
    sh.dot(772, 230)
    resistor(sh, 772, 230, "R25", "4,7 kΩ", L=84)
    b = opamp(sh, 890, 164, w=110, h=92, ref="U7B", part="")
    sh.wire((856, 230), b["in+"], stroke=INK)
    sh.dot(866, 230)
    sh.wire((866, 230), (866, 268), stroke=INK)
    capacitor(sh, 866, 268, "C20", "33 nF", horiz=False, L=76, plate=34)
    ground(sh, 866, 344, "agnd")
    sh.wire(b["out"], (1030, 210), (1030, 148), (872, 148), (872, 190), b["in-"],
            stroke=INK)
    sh.wire((772, 230), (772, 420), (808, 420), stroke=INK)
    capacitor(sh, 808, 420, "C21", "68 nF", L=76, plate=34)
    sh.wire((884, 420), (1058, 420), (1058, 210), stroke=INK)
    sh.dot(1030, 210)
    sh.txt(880, 462, "C21 returns to the output: a Sallen-Key cell", size=6,
           fill=GRIS)

    # --- differential drive and converter ------------------------------------
    sh.wire((1058, 210), (1160, 210), (1160, 300), stroke=INK, sw=1.6)
    ic_box(sh, 1100, 300, 120, 96, "U9", "THS4551", "asym. → diff.")
    sh.wire((1220, 330), (1268, 330), (1268, 520), (1230, 520), stroke=INK, sw=1.4)
    sh.wire((1220, 366), (1248, 366), (1248, 556), (1230, 556), stroke=INK, sw=1.4)
    ic_box(sh, 1060, 480, 170, 160, "U10", "ADS131M04", "24 bits · Δ-Σ · 4 channels")
    sh.txt(1145, 596, "32 kSPS · 106 dB", size=6, fill=GRIS)
    sh.txt(1145, 612, "AIN0…AIN3", size=6, fill=GRIS, family=MONO)
    for i, n in enumerate(("SCLK", "MOSI", "MISO", "DRDY")):
        netflag(sh, 896, 500 + i * 36, n, side="out", color=CUIVRE, w=74)
        sh.wire((970, 500 + i * 36), (1060, 500 + i * 36), stroke=CUIVRE, sw=1.2)
    sh.txt(970, 492, "to the isolators (sheet 4)", size=6, fill=CUIVRE,
           anchor="end")

    # --- reference and time base ---------------------------------------------
    ic_box(sh, 660, 560, 160, 86, "U11", "ADR4525", "2,5 V · 2 ppm/°C")
    sh.wire((820, 603), (860, 603), (860, 468), (1250, 468), (1250, 480),
            stroke=INK, sw=1.4)
    sh.txt(1010, 458, "REFP", size=6.2, fill=INK, family=MONO)
    ic_box(sh, 400, 660, 170, 86, "Y1", "TCXO 12,288 MHz", "±1 ppm")
    netflag(sh, 596, 703, "CLKIN", side="out", color=BLEU, w=74)
    sh.wire((570, 703), (596, 703), stroke=BLEU, sw=1.4)
    note(sh, 92, 660, 280,
         ["Every sample is dated by",
          "its index, never by",
          "l'horloge de l'ordinateur."],
         title="BASE DE TEMPS", color=SEVE, fill=SEVE_P)
    sh.save("carte-mere.svg")


def transfo(sh, x, y, ref="T1", part="", n=4, h=110):
    """Isolation transformer: two windings and a core."""
    for k, xx in enumerate((x, x + 76)):
        d = ["M{},{} ".format(xx, y)]
        for i in range(3):
            yy = y + i * (h / 3)
            sgn = 1 if k == 0 else -1
            d.append(f"A 13,{h/6} 0 0 {1 if k==0 else 0} {xx},{yy + h/3}")
        sh.path(" ".join(d), sw=1.8)
    sh.line(x + 32, y - 8, x + 32, y + h + 8, stroke=INK, sw=1.6)
    sh.line(x + 44, y - 8, x + 44, y + h + 8, stroke=INK, sw=1.6)
    sh.txt(x + 38, y - 20, ref, size=7, fill=SEVE, weight="700")
    if part:
        sh.txt(x + 38, y + h + 26, part, size=6, fill=GRIS)
    return {"p1": (x, y), "p2": (x, y + h), "s1": (x + 76, y), "s2": (x + 76, y + h)}


# =============================================================================
#  PLANCHE 4 — ALIMENTATIONS ET ISOLEMENT GALVANIQUE
# =============================================================================
def pl_alim():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Power supplies and isolation", sheet="4/8", bloc="Main board")
    sh.txt(90, 76, "Two grounds, one barrier — generating the isolated ±5 V analog rails", size=8.4, fill=NUIT, weight="700", anchor="start",
           family=SERIF)

    sh.rect(60, 100, 620, 560, fill="#F2F6FC", stroke=BLEU, sw=1.1, rx=8, dash="7 5")
    sh.txt(370, 122, "USB SIDE — DGND ground", size=6.6, fill=BLEU, weight="700",
           spacing="1")
    sh.rect(760, 100, 550, 520, fill="#F3F8F5", stroke=SEVE, sw=1.1, rx=8, dash="7 5")
    sh.txt(1035, 122, "MEASUREMENT SIDE — AGND ground, floating", size=6.6, fill=SEVE,
           weight="700", spacing="1")
    barrier(sh, 720, 120, 660)

    # --- VBUS input ----------------------------------------------------------
    netflag(sh, 80, 190, "VBUS 5 V", side="in", w=84)
    sh.wire((164, 190), (190, 190), stroke=INK, sw=1.8)
    ferrite(sh, 190, 190, "FB1", "600 Ω @ 100 MHz")
    sh.wire((266, 190), (330, 190), stroke=INK, sw=1.8)
    sh.dot(330, 190)
    capacitor(sh, 330, 210, "C30", "22 µF", horiz=False, L=76, plate=34)
    sh.wire((330, 190), (330, 210), stroke=INK)
    ground(sh, 330, 286, "dgnd", "DGND")

    # --- isolated converter --------------------------------------------------
    sh.wire((330, 190), (400, 190), stroke=INK, sw=1.8)
    ic_box(sh, 400, 150, 150, 96, "U20", "SN6505B", "pilote de transfo.")
    netflag(sh, 400, 300, "SYNC", side="in", color=BLEU, w=66)
    sh.wire((466, 300), (475, 300), (475, 246), stroke=BLEU, sw=1.2, dash="5 4")
    sh.txt(500, 296, "locked to SYNC: the switching residue", size=5.8,
           fill=GRIS, anchor="start")
    sh.txt(500, 310, "lands at 410 kHz, outside the measurement band", size=5.8,
           fill=GRIS, anchor="start")
    t1 = transfo(sh, 684, 160, "T1", "WE 750315371 · 1:1,3", h=110)
    sh.wire((550, 178), (684, 178), stroke=INK, sw=1.6)
    sh.wire((550, 218), (620, 218), (620, 270), (684, 270), stroke=INK, sw=1.6)

    # --- rectification and regulation ----------------------------------------
    sh.wire((760, 160), (820, 160), stroke=INK, sw=1.6)
    sh.wire((760, 270), (800, 270), (800, 300), (820, 300), stroke=INK, sw=1.6)
    ic_box(sh, 820, 150, 150, 170, "D10-D13", "BAT54S ×2", "redressement double")
    sh.wire((970, 190), (1010, 190), stroke=INK, sw=1.6)
    sh.wire((970, 280), (1010, 280), stroke=INK, sw=1.6)
    ic_box(sh, 1010, 150, 160, 90, "U21", "LT3045", "+5 VA · 0,8 µV eff.")
    ic_box(sh, 1010, 260, 160, 90, "U22", "LT3094", "−5 VA · 0,8 µV eff.")
    sh.wire((1170, 195), (1250, 195), stroke=CUIVRE, sw=1.8)
    rail(sh, 1250, 195, "+5 VA")
    sh.wire((1170, 305), (1250, 305), stroke=CUIVRE, sw=1.8)
    rail(sh, 1250, 305, "−5 VA", up=False)
    sh.txt(1090, 380, "PSRR 76 dB at 1 MHz — the switching", size=5.8, fill=GRIS)
    sh.txt(1090, 394, "residue is buried under the noise", size=5.8, fill=GRIS)
    ground(sh, 1090, 420, "iso", "AGND (flottante)")

    # --- isolateurs ----------------------------------------------------------
    ic_box(sh, 620, 420, 200, 120, "U24", "ADuM4151", "6 channels · 17 Mb/s")
    for i, n in enumerate(("SCLK", "MOSI", "MISO", "DRDY")):
        netflag(sh, 400, 440 + i * 30, n, side="out", color=CUIVRE, w=72)
        sh.wire((472, 440 + i * 30), (620, 440 + i * 30), stroke=CUIVRE, sw=1.1)
    sh.txt(900, 448, "to the ADC (sheet 3)", size=6, fill=CUIVRE, anchor="start")
    sh.wire((820, 470), (890, 470), stroke=CUIVRE, sw=1.4)
    ic_box(sh, 620, 570, 200, 84, "U25", "ADuM1251", "isolated I²C")
    netflag(sh, 400, 612, "SDA/SCL", side="out", color=CUIVRE, w=84)
    sh.wire((484, 612), (620, 612), stroke=CUIVRE, sw=1.1)
    sh.wire((820, 612), (890, 612), stroke=CUIVRE, sw=1.4)
    sh.txt(900, 616, "capteurs d'ambiance", size=6, fill=CUIVRE, anchor="start")

    # --- digital rail --------------------------------------------------------
    ic_box(sh, 120, 380, 150, 90, "U23", "TPS7A2033", "3.3 V digital")
    sh.wire((330, 190), (330, 340), (195, 340), (195, 380), stroke=INK)
    sh.wire((195, 470), (195, 510), stroke=CUIVRE, sw=1.6)
    rail(sh, 195, 510, "+3V3", up=False)

    note(sh, 60, 690, 840,
         ["No conductive path links the plant to the building's earth: the only coupling is T1's magnetic",
          "field and the isolators' coupling capacitance, less than 3 pF in total."],
         title="WHAT THE BARRIER GUARANTEES", color=CUIVRE, fill=CUIV_P)
    sh.save("carte-alim.svg")


# =============================================================================
#  SHEET 5 — DIGITAL SECTION AND USB LINK
# =============================================================================
def pl_num():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Digital section and USB link", sheet="5/8", bloc="Main board")
    sh.txt(90, 76, "RP2350 · USB-C · driverless audio class 2.0 · direct MIDI output", size=8.4, fill=NUIT, weight="700", anchor="start", family=SERIF)

    # --- prise USB-C ---------------------------------------------------------
    pins = connector(sh, 92, 150, 6, "J20 · USB-C (receptacle)", pitch=48, w=58,
                     pinlabels=["A4", "A1", "A5", "B5", "A6", "A7"],
                     netlabels=["VBUS", "GND", "CC1", "CC2", "D+", "D−"])
    sh.wire(pins[0], (330, 170), stroke=CUIVRE, sw=1.8)
    netflag(sh, 330, 170, "VBUS 5 V", side="out", color=CUIVRE, w=84)
    ground(sh, 206, 218, "dgnd")
    sh.wire(pins[1], (206, 218), stroke=INK)
    for i, py in enumerate((266, 314)):
        sh.wire((176, py), (220, py), stroke=INK)
        resistor(sh, 220, py, "5,1 kΩ", "", L=80, lab_above=(i == 0))
        sh.wire((300, py), (336, py), stroke=INK)
    sh.wire((336, 266), (336, 314), stroke=INK)
    ground(sh, 336, 314, "dgnd")
    sh.wire(pins[4], (300, 362), (300, 400), (480, 400), stroke=INK, sw=1.5)
    sh.wire(pins[5], (270, 410), (270, 430), (480, 430), stroke=INK, sw=1.5)

    ic_box(sh, 320, 470, 150, 70, "Y2", "12 MHz", "±20 ppm")
    sh.wire((480, 470), (476, 470), (476, 505), (470, 505), stroke=INK, sw=1.3)
    ic_box(sh, 100, 560, 180, 80, "U33", "TPD4S014", "ESD network · < 0.5 pF")
    sh.wire((190, 470), (190, 560), stroke=INK, sw=1.2, dash="5 4")
    sh.wire((176, 362), (190, 362), (190, 470), stroke=INK, sw=1.2, dash="5 4")


    # --- microcontroller -----------------------------------------------------
    sh.rect(480, 140, 300, 500, fill="#FBFBF7", stroke=INK, sw=2.0, rx=4)
    sh.txt(630, 184, "U30", size=9.5, fill=SEVE, weight="700")
    sh.txt(630, 208, "RP2350B", size=8.6, fill=INK, family=MONO)
    sh.txt(630, 228, "2× Cortex-M33 · 150 MHz", size=6, fill=GRIS)
    sh.txt(630, 244, "520 ko SRAM · 12 machines PIO", size=6, fill=GRIS)
    for n, y in (("USB_DP", 400), ("USB_DM", 430), ("XIN", 470), ("BOOTSEL", 510),
                 ("SWCLK", 550), ("SWDIO", 580)):
        sh.line(462, y, 480, y, stroke=INK, sw=1.2)
        sh.txt(490, y + 4, n, size=5.8, fill=GRIS, anchor="start", family=MONO)
    for n, y in (("SCLK", 250), ("MOSI", 276), ("MISO", 302), ("DRDY", 328),
                 ("UART1", 370), ("PWM", 451), ("GPIO", 531), ("QSPI", 611)):
        sh.line(780, y, 798, y, stroke=INK, sw=1.2)
        sh.txt(770, y + 4, n, size=5.8, fill=GRIS, anchor="end", family=MONO)

    # --- to the isolators ----------------------------------------------------
    for n, y in (("SCLK", 250), ("MOSI", 276), ("MISO", 302), ("DRDY", 328)):
        netflag(sh, 880, y, n, side="out", color=CUIVRE, w=72)
        sh.wire((798, y), (880, y), stroke=CUIVRE, sw=1.2)
    sh.txt(960, 254, "→ sheet 4", size=6, fill=CUIVRE, anchor="start")

    # --- sortie MIDI ---------------------------------------------------------
    sh.wire((798, 370), (830, 370), stroke=INK, sw=1.4)
    resistor(sh, 830, 370, "R34", "33 Ω", L=80)
    midi = connector(sh, 1150, 180, 3, "J21 · MIDI TRS type A", pitch=40, w=54,
                     side="left", pinlabels=["T", "R", "S"],
                     netlabels=["TX", "+3V3", "GND"], lead=36)
    sh.wire((910, 370), (1060, 370), (1060, 200), midi[0], stroke=INK, sw=1.4)
    sh.txt(1204, 352, "norme MIDI-TRS type A (2018)", size=6, fill=GRIS)

    # --- interface homme-machine --------------------------------------------
    ic_box(sh, 880, 420, 170, 62, "DS1", "LED RVB", "status and level")
    sh.wire((798, 451), (880, 451), stroke=INK, sw=1.3)
    ic_box(sh, 880, 500, 170, 62, "S1", "bouton", "marquage / auto-config")
    sh.wire((798, 531), (880, 531), stroke=INK, sw=1.3)
    ic_box(sh, 880, 580, 170, 62, "U31", "W25Q128JV", "16 Mo · QSPI")
    sh.wire((798, 611), (880, 611), stroke=INK, sw=1.3)

    note(sh, 92, 660, 620,
         ["The microcontroller interprets nothing: it timestamps, frames and pushes over USB.",
          "All the music — scales, instruments, thresholds — is computed on the computer.",
          "CC1/CC2 declare the board as a 5 V / 500 mA sink: no PD negotiation."],
         title="WHAT THE MICROCONTROLLER DOES, AND DOES NOT DO", color=SEVE,
         fill=SEVE_P)
    sh.save("carte-num.svg")


def stars(sh, x, y, n, total=5, r=4.2, col=SEVE):
    for i in range(total):
        sh.circle(x + i * (r * 2.6), y, r, fill=col if i < n else "#fff",
                  stroke=col, sw=1.1)


# =============================================================================
#  BOARD LAYOUT AND STACK-UP
# =============================================================================
def fig_pcb():
    sh = Sheet(980, 660, print_mm=125)
    sh.title("Board layout and stack-up",
             "Four layers, two ground planes, one guard ring")

    # --- empilage ------------------------------------------------------------
    couches = [("Layer 1 — analog signals", "#D9C08A", 18),
               ("Layer 2 — AGND / DGND ground plane (slotted)", "#8FA79A", 26),
               ("Layer 3 — supplies", "#B9C6BF", 22),
               ("Layer 4 — digital signals, shielding", "#D9C08A", 18)]
    y = 108
    sh.txt(60, 96, "EMPILAGE", size=7.4, fill=NUIT, weight="700", anchor="start",
           spacing="1.4")
    for i, (nom, col, h) in enumerate(couches):
        sh.rect(60, y, 360, h, fill=col, stroke=INK, sw=1.1)
        sh.txt(430, y + h / 2 + 4, nom, size=6.4, fill=INK, anchor="start")
        y += h
        if i < 3:
            sh.rect(60, y, 360, 16, fill="#F0EEE4", stroke=TRAIT, sw=0.9)
            sh.txt(430, y + 12, ["0.2 mm prepreg", "FR4 core 1.0 mm",
                                 "0.2 mm prepreg"][i], size=5.8, fill=GRIS,
                   anchor="start")
            y += 16
    sh.txt(60, y + 22, "Total thickness 1.6 mm · 35 µm copper · FR4 Tg 150",
           size=6.2, fill=GRIS, anchor="start")

    # --- implantation --------------------------------------------------------
    sh.txt(60, 282, "PLACEMENT (seen from above, 100 × 60 mm)", size=7.4,
           fill=NUIT, weight="700", anchor="start", spacing="1.4")
    bx, by, bw, bh = 60, 306, 620, 300
    sh.rect(bx, by, bw, bh, fill="#F7F9F7", stroke=SEVE, sw=2.0, rx=10)
    for cx, cy in ((bx + 16, by + 16), (bx + bw - 16, by + 16),
                   (bx + 16, by + bh - 16), (bx + bw - 16, by + bh - 16)):
        sh.circle(cx, cy, 6, fill="#fff", stroke=GRIS, sw=1.2)
    # zones
    zones = [(76, 330, 150, 130, "Inputs\nand guard", "#EDF5F0", SEVE),
             (240, 330, 150, 130, "Daughter board\n(mezzanine)", "#FBF5E6", OR),
             (404, 330, 120, 130, "Gain and\nfilter", "#EDF5F0", SEVE),
             (538, 330, 126, 130, "ADC and\nreference", "#EDF5F0", SEVE),
             (76, 480, 250, 110, "Isolated supplies", "#FBEEE6", CUIVRE),
             (340, 480, 150, 110, "Isolateurs", "#FBEEE6", CUIVRE),
             (504, 480, 160, 110, "RP2350 · USB-C", "#EEF3FA", BLEU)]
    for x, yy, w, h, lab, fill, col in zones:
        sh.rect(x, yy, w, h, fill=fill, stroke=col, sw=1.4, rx=5)
        for k, line in enumerate(lab.split("\n")):
            sh.txt(x + w / 2, yy + h / 2 - 4 + k * 15, line, size=6.6, fill=col,
                   weight="700")
    sh.line(495, 470, 495, 600, stroke=CUIVRE, sw=2.0, dash="10 6")
    sh.txt(495, 612, "slot in the ground plane — the barrier", size=6, fill=CUIVRE)
    # guard ring
    sh.rect(68, 322, 166, 146, fill="none", stroke=OR, sw=2.4, dash="6 4")
    sh.txt(330, 302, "guard ring on all 4 layers", size=5.8, fill=OR,
           weight="700", anchor="start")

    # --- guard detail --------------------------------------------------------
    sh.txt(710, 282, "GUARD DETAIL", size=7.4, fill=NUIT, weight="700",
           anchor="start", spacing="1.4")
    dx, dy = 710, 320
    sh.rect(dx, dy, 220, 170, fill="#FFFFFF", stroke=TRAIT, sw=1.2, rx=6)
    sh.circle(dx + 110, dy + 85, 10, fill=SEVE, stroke=NUIT, sw=1.2)
    sh.txt(dx + 110, dy + 62, "input pad", size=5.8, fill=NUIT)
    for r in (34, 44):
        sh.circle(dx + 110, dy + 85, r, fill="none", stroke=OR, sw=2.2)
    sh.txt(dx + 110, dy + 148, "guard ring at the same", size=5.8, fill=OR)
    sh.txt(dx + 110, dy + 162, "potential as the input", size=5.8, fill=OR)
    note(sh, 710, 500, 220,
         ["The solder mask is kept clear under",
          "the input: a leakage current of",
          "fuite de surface de 1 pA",
          "is enough to ruin the measurement."],
         title="RULE", color=CUIVRE, fill=CUIV_P)
    sh.signer()
    sh.save("carte-pcb.svg")


# =============================================================================
#  CONNECTEUR MEZZANINE
# =============================================================================
def fig_mezzanine():
    sh = Sheet(980, 460, print_mm=125)
    sh.title("The 20-pin mezzanine connector",
             "A daughter board declares itself: the software recognises it when plugged in")

    gauche = [("1", "+5 VA", "analog supply"),
              ("3", "−5 VA", "analog supply"),
              ("5", "AGND", "analog ground"),
              ("7", "AGND", "analog ground"),
              ("9", "GUARD", "guard buffer output"),
              ("11", "SIG_A", "channel A to the PGA"),
              ("13", "SIG_B", "channel B to the PGA"),
              ("15", "EXC", "excitation, MCU DAC"),
              ("17", "SDA", "isolated I²C — EEPROM"),
              ("19", "SCL", "isolated I²C — EEPROM")]
    droite = [("2", "+3V3", "daughter-board logic"),
              ("4", "V_OFF", "consigne d'offset (CNA)"),
              ("6", "AGND", "analog ground"),
              ("8", "REF_C", "1 kHz square reference"),
              ("10", "GUARD", "second guard point"),
              ("12", "SEL0", "range selection"),
              ("14", "SEL1", "range selection"),
              ("16", "TEMP", "daughter-board sensor"),
              ("18", "PRES", "presence detection"),
              ("20", "AGND", "analog ground")]
    y0, dy = 100, 32
    for col, items, x in ((0, gauche, 60), (1, droite, 520)):
        for i, (n, net, desc) in enumerate(items):
            yy = y0 + i * dy
            fill = SEVE_P if net.startswith(("+", "−", "AG", "+3")) else "#fff"
            sh.rect(x, yy, 40, 24, fill=OR_PL, stroke=OR, sw=1.1, rx=3)
            sh.txt(x + 20, yy + 17, n, size=6.4, fill=INK, family=MONO, weight="700")
            sh.rect(x + 44, yy, 78, 24, fill=fill, stroke=TRAIT, sw=1.0, rx=3)
            sh.txt(x + 83, yy + 17, net, size=6.4, fill=NUIT, family=MONO)
            sh.txt(x + 130, yy + 17, desc, size=6.2, fill=GRIS, anchor="start")

    sh.signer()
    sh.save("carte-mezzanine.svg")


# =============================================================================
#  PLAN DE BANDE
# =============================================================================
def fig_bande():
    sh = Sheet(980, 520, print_mm=125)
    sh.title("The instrument's band plan",
             "What is measured, what is rejected, and where the line falls")

    x0, x1, yb = 90, 920, 380
    f0, f1 = -3.0, 4.0          # decades: 1 mHz … 10 kHz

    def fx(logf):
        return x0 + (logf - f0) / (f1 - f0) * (x1 - x0)

    sh.line(x0, yb, x1, yb, stroke=INK, sw=1.6)
    for d in range(int(f0), int(f1) + 1):
        x = fx(d)
        sh.line(x, yb, x, yb + 8, stroke=INK, sw=1.2)
        lab = {-3: "1 mHz", -2: "10 mHz", -1: "0,1 Hz", 0: "1 Hz", 1: "10 Hz",
               2: "100 Hz", 3: "1 kHz", 4: "10 kHz"}[d]
        sh.txt(x, yb + 26, lab, size=6.2, fill=GRIS)
        for k in range(2, 10):
            sh.line(fx(d + math.log10(k)), yb, fx(d + math.log10(k)), yb + 4,
                    stroke=TRAIT, sw=0.9)

    bandes = [(-2.7, -1.0, 118, "Variations lentes, circadiennes", SEVE, "#E7F1EA"),
              (-2.0, 0.3, 176, "Potentiels de variation", SEVE, "#E7F1EA"),
              (-1.0, 1.0, 234, "Potentiels d'action", SEVE, "#DCEBE2"),
              (0.7, 1.9, 292, "Artefacts de contact", CUIVRE, "#FBEEE6")]
    for a, b, yy, lab, col, fill in bandes:
        sh.rect(fx(a), yy, fx(b) - fx(a), 22, fill=fill, stroke=col, sw=1.3, rx=4)
        sh.txt(fx(a) + 4, yy - 6, lab, size=6.4, fill=col, weight="700",
               anchor="start")

    # mains hum
    x50 = fx(math.log10(50))
    sh.line(x50, 108, x50, yb, stroke=CUIVRE, sw=2.0, dash="7 5")
    sh.txt(x50, 100, "50 Hz", size=6.6, fill=CUIVRE, weight="700")
    x1k = fx(3)
    sh.line(x1k, 108, x1k, yb, stroke=BLEU, sw=2.0, dash="7 5")
    sh.txt(x1k, 100, "1 kHz excitation", size=6.6, fill=BLEU, weight="700")

    # the filter's response
    pts = []
    for i in range(0, 201):
        lf = f0 + (f1 - f0) * i / 200
        f = 10 ** lf
        g = 1.0 / math.sqrt(1 + (f / 400.0) ** 6)
        pts.append((fx(lf), 366 - 34 * g))
    sh.path("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts), stroke=OR, sw=2.2)
    sh.txt(fx(1.0), 348, "anti-aliasing filter (−3 dB at 400 Hz)", size=6.2,
           fill=OR, anchor="middle")

    sh.txt(x0, 424, "Sampling: 250 Hz by default, 1 kHz in oscilloscope mode, 32 kHz for direct listening.", size=6.4, fill=NUIT, anchor="start",
           weight="700")
    sh.txt(x0, 444, "Mains hum is removed digitally: no phase shift is added in the useful band.", size=6.2, fill=GRIS, anchor="start")
    sh.txt(x0, 462, "1 mHz high-pass: the electrode's drift is tracked, never removed.", size=6.2, fill=GRIS, anchor="start")
    sh.signer()
    sh.save("carte-bande.svg")


# =============================================================================
#  SYNCHRONOUS DETECTION — TIMING DIAGRAM
# =============================================================================
def fig_lockin():
    sh = Sheet(980, 610, print_mm=125)
    sh.title("How synchronous detection works",
             "Why multiplying the signal by its own reference removes almost all the noise")

    x0, x1 = 90, 900
    rows = [(120, "Excitation applied to the bridge", SEVE),
            (230, "Received signal (noisy, buried in mains hum)", CUIVRE),
            (340, "Square reference (same phase)", BLEU),
            (450, "Product, then a moving average", NUIT)]
    for yy, lab, col in rows:
        sh.line(x0, yy, x1, yy, stroke=TRAIT, sw=1.0, dash="4 4")
        sh.txt(x0 - 4, yy - 34, lab, size=6.4, fill=col, weight="700", anchor="start")

    n = 400
    import random as _r
    rng = _r.Random(11)
    bruit = [rng.gauss(0, 1) for _ in range(n + 1)]
    p1, p2, p3, p4 = [], [], [], []
    moy = 0.0
    for i in range(n + 1):
        t = i / n
        x = x0 + t * (x1 - x0)
        s = math.sin(2 * math.pi * 6 * t)
        carre = 1.0 if math.sin(2 * math.pi * 6 * t) >= 0 else -1.0
        recu = 0.45 * s + 0.75 * math.sin(2 * math.pi * 0.85 * t + 1.1) + 0.28 * bruit[i]
        prod = recu * carre
        moy = moy + 0.035 * (prod - moy)
        p1.append((x, 120 - 30 * s))
        p2.append((x, 230 - 24 * recu))
        p3.append((x, 340 - 26 * carre))
        p4.append((x, 450 - 60 * moy))

    def poly(pts, col, sw=1.8):
        sh.path("M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in pts), stroke=col, sw=sw)

    poly(p1, SEVE)
    poly(p2, CUIVRE, 1.3)
    poly(p3, BLEU)
    poly(p4, NUIT, 2.4)
    sh.txt(x1 - 6, 412, "≈ measured amplitude", size=6.2, fill=NUIT,
           anchor="end", weight="700")

    note(sh, 90, 490, 810,
         ["Anything not exactly at the excitation frequency — mains hum, 1/f noise,",
          "thermal drift — has its product change sign constantly: the average cancels it."],
         title="WHAT IS GAINED", color=SEVE, fill=SEVE_P)
    sh.signer()
    sh.save("carte-lockin.svg")


# =============================================================================
#  ARCHITECTURE LOGICIELLE
# =============================================================================
def fig_logiciel_archi():
    sh = Sheet(980, 720, print_mm=125)
    sh.title("The PhytoScope software architecture",
             "Three threads, two queues, no allocation in the real-time path")

    # --- fil d'acquisition ---------------------------------------------------
    sh.rect(40, 92, 260, 300, fill="#F3F8F5", stroke=SEVE, sw=1.4, rx=8)
    sh.txt(170, 114, "THE ACQUISITION THREAD", size=6.8, fill=SEVE, weight="700",
           spacing="1.2")
    for i, (t, sub) in enumerate([("Source", "UAC2 · serial · file · simulated"),
                                  ("Horodatage", "ADC counter → UTC time"),
                                  ("Anneau", "collections.deque, 60 s")]):
        block(sh, 60, 138 + i * 84, 220, 66, t, sub, fill="#fff", stroke=SEVE,
              sw=1.3, tsize=7.4)
        if i < 2:
            sh.arrow(170, 204 + i * 84, 170, 232 + i * 84, color=OR, sw=1.8)

    # --- fil de traitement ---------------------------------------------------
    sh.rect(340, 92, 300, 480, fill="#FBF8EF", stroke=OR, sw=1.4, rx=8)
    sh.txt(490, 114, "THE PROCESSING THREAD (NumPy)", size=6.8, fill=OR, weight="700",
           spacing="1.2")
    for i, (t, sub) in enumerate([("Filtering", "high-pass, 50 Hz notch, smoothing"),
                                  ("Measurements", "rms, peak, slope, standard deviation"),
                                  ("Detection", "adaptive threshold on the derivative"),
                                  ("Sonification", "event → note, length, dynamics"),
                                  ("Synthesis", "table d'ondes + enveloppe ADSR")]):
        block(sh, 360, 138 + i * 84, 260, 66, t, sub, fill="#fff", stroke=OR_CL,
              sw=1.3, tsize=7.4)
        if i < 4:
            sh.arrow(490, 204 + i * 84, 490, 232 + i * 84, color=OR, sw=1.8)
    sh.arrow(300, 240, 356, 240, color=OR, sw=2.0)
    sh.txt(328, 228, "file", size=5.8, fill=GRIS)

    # --- fil d'interface -----------------------------------------------------
    sh.rect(680, 92, 260, 480, fill="#EEF3FA", stroke=BLEU, sw=1.4, rx=8)
    sh.txt(810, 114, "THE INTERFACE THREAD (Qt)", size=6.8, fill=BLEU, weight="700",
           spacing="1.2")
    for i, (t, sub) in enumerate([("Oscilloscope", "pyqtgraph · 60 im/s"),
                                  ("Multimeter", "display and statistics"),
                                  ("Analyser", "FFT and spectrogram"),
                                  ("Listen", "instruments and mixing"),
                                  ("Library", "sessions, playback")]):
        block(sh, 700, 138 + i * 84, 220, 66, t, sub, fill="#fff", stroke=BLEU,
              sw=1.3, tsize=7.4)
    sh.arrow(640, 240, 696, 240, color=BLEU, sw=2.0, marker="ahb")
    sh.txt(668, 228, "file", size=5.8, fill=GRIS)

    # --- sorties -------------------------------------------------------------
    for i, (x, t, sub, col) in enumerate([
            (40, "Enregistreur", "WAV 24 bits + CSV + JSON", NUIT),
            (340, "Audio output", "sounddevice / PortAudio", NUIT),
            (680, "MIDI output", "python-rtmidi", NUIT)]):
        w = 260 if i != 1 else 300
        block(sh, x, 606, w, 62, t, sub, fill=NUIT, stroke=NUIT, tcol=OR_CL,
              sw=1.4, tsize=7.8)
    sh.arrow(170, 392, 170, 602, color=OR, sw=1.8)
    sh.arrow(490, 572, 490, 602, color=OR, sw=1.8)
    sh.arrow(810, 572, 810, 602, color=OR, sw=1.8)
    sh.signer()
    sh.save("logiciel-archi.svg")


# =============================================================================
#  MAQUETTE DE L'INTERFACE
# =============================================================================
def fig_logiciel_ihm():
    sh = Sheet(980, 640, print_mm=125)
    sh.title("Maquette de l'interface — onglet « Oscilloscope »",
             "A status bar that never lies: real gain, drift, saturation, clock")

    sh.rect(40, 84, 900, 500, fill="#12201B", stroke=NUIT, sw=1.6, rx=8)
    # barre de titre
    sh.rect(40, 84, 900, 34, fill="#0A1712", stroke="none", rx=8)
    sh.txt(60, 106, "PhytoScope 1.0 — Ficus benjamina — session 2026-09-17 14:02",
           size=6.6, fill=OR_CL, anchor="start")
    for i, c in enumerate(("#E06C5A", "#E0C073", "#6FA98A")):
        sh.circle(900 - i * 22, 101, 6, fill=c, stroke="none")
    # onglets
    onglets = ["Oscilloscope", "Multimeter", "Analyser", "Listen", "Library",
               "Settings"]
    for i, o in enumerate(onglets):
        x = 56 + i * 142
        act = (i == 0)
        sh.rect(x, 128, 132, 30, fill=SEVE if act else "#1B3129",
                stroke=SEVE if act else "#26443A", sw=1.1, rx=5)
        sh.txt(x + 66, 148, o, size=6.2, fill="#fff" if act else "#9fb8ab",
               weight="700" if act else "400")
    # the trace
    sh.rect(56, 176, 660, 300, fill="#0A1712", stroke="#26443A", sw=1.1, rx=5)
    for i in range(1, 8):
        sh.line(56 + i * 82.5, 176, 56 + i * 82.5, 476, stroke="#1B3129", sw=0.9)
    for i in range(1, 6):
        sh.line(56, 176 + i * 50, 716, 176 + i * 50, stroke="#1B3129", sw=0.9)
    import random as _r
    rng = _r.Random(5)
    pts, v = [], 0.0
    for i in range(331):
        v += rng.gauss(0, 0.06)
        v *= 0.985
        if i in (90, 91, 92):
            v += 1.1
        pts.append((56 + i * 2, 326 - v * 52))
    sh.path("M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in pts), stroke="#7FE0A8",
            sw=1.8)
    sh.txt(240, 214, "event detected", size=6, fill=OR_CL)
    sh.line(240, 222, 240, 250, stroke=OR_CL, sw=1.2, dash="4 3")

    # side panel
    sh.rect(732, 176, 192, 300, fill="#16281F", stroke="#26443A", sw=1.1, rx=5)
    sh.txt(828, 200, "QUICK SETTINGS", size=6, fill=OR_CL, weight="700",
           spacing="1")
    champs = [("Base de temps", "5 s / div"), ("Sensitivity", "200 µV / div"),
              ("Couplage", "AC 0,01 Hz"), ("Notch", "50 Hz — live"),
              ("Hardware gain", "×100 (auto)"), ("Channel", "A — FE-Z")]
    for i, (k, v_) in enumerate(champs):
        yy = 226 + i * 40
        sh.txt(748, yy, k, size=5.8, fill="#9fb8ab", anchor="start")
        sh.rect(748, yy + 6, 160, 22, fill="#0A1712", stroke="#2E5247", sw=1.0, rx=4)
        sh.txt(756, yy + 21, v_, size=6, fill="#EAF2EC", anchor="start", family=MONO)

    # status bar
    sh.rect(56, 492, 868, 72, fill="#0A1712", stroke="#26443A", sw=1.1, rx=5)
    etats = [("STATUS", "acquisition", "#7FE0A8"), ("HORLOGE", "CAN ±0,4 ppm", "#EAF2EC"),
             ("SATURATION", "non", "#7FE0A8"), ("DRIFT", "+12 µV/min", "#E0C073"),
             ("ELECTRODES", "142 / 138 kΩ", "#EAF2EC"),
             ("ENREGISTRE", "● 00:14:22", "#E06C5A")]
    for i, (k, v_, col) in enumerate(etats):
        x = 76 + i * 144
        sh.txt(x, 516, k, size=5.4, fill="#6d8a7d", anchor="start", spacing="0.8")
        sh.txt(x, 540, v_, size=6.6, fill=col, anchor="start", weight="700",
               family=MONO)
    sh.txt(490, 604, "Dark mode by default; a light theme and higher contrast in the accessibility settings.", size=6.2, fill=GRIS, style="italic")
    sh.signer()
    sh.save("logiciel-ihm.svg")


# =============================================================================
#  SONIFICATION CHAIN
# =============================================================================
def fig_mapping():
    sh = Sheet(980, 600, print_mm=125)
    sh.title("From the microvolt to the note",
             "Every arrow is an aesthetic choice: the document says which, and why")

    src = [("Event amplitude", "µV"), ("Initial slope", "µV/s"),
           ("Time above threshold", "s"), ("Variability over 60 s", "µV eff."),
           ("Temperature, light", "capteurs")]
    dst = [("Note pitch", "degree in the scale"),
           ("Dynamics (velocity)", "1 – 127"),
           ("Note length", "0,2 – 8 s"),
           ("Rhythmic density", "notes / minute"),
           ("Timbre, reverberation", "instrument, send level")]
    for i, (t, u) in enumerate(src):
        block(sh, 40, 110 + i * 88, 300, 66, t, u, fill="#fff", stroke=SEVE,
              sw=1.4, tsize=7.4)
    for i, (t, u) in enumerate(dst):
        block(sh, 640, 110 + i * 88, 300, 66, t, u, fill="#fff", stroke=BLEU,
              sw=1.4, tsize=7.4)
    liens = [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (0, 1), (3, 0)]
    for a, b in liens:
        y1 = 143 + a * 88
        y2 = 143 + b * 88
        sh.arrow_path(f"M340,{y1} C480,{y1} 500,{y2} 636,{y2}", color=OR, sw=1.5)
    block(sh, 392, 254, 196, 120, "Moteur de", "correspondance",
          ["quantification", "to the scale", "and anti-repetition"], fill=OR_PL,
          stroke=OR, sw=1.6, tsize=8)
    sh.signer()
    sh.save("logiciel-mapping.svg")


# =============================================================================
#  COMPARATIF DES LANGAGES
# =============================================================================
def fig_langages():
    sh = Sheet(980, 660, print_mm=125)
    sh.title("Which language for this software?",
             "Scores given for THESE requirements — not in the abstract")

    langs = ["Python 3", "C++", "Rust", "Go", "TypeScript\n(Electron)"]
    crits = [("Development speed", [5, 2, 2, 4, 3]),
             ("Signal-processing ecosystem", [5, 4, 2, 1, 2]),
             ("Quality of real-time graphics", [4, 5, 3, 2, 4]),
             ("Ease of installation (3 OSes)", [3, 2, 4, 5, 3]),
             ("Audio and MIDI access", [5, 4, 3, 2, 3]),
             ("Contributions from an amateur", [5, 1, 2, 3, 3]),
             ("Memory footprint", [2, 5, 5, 4, 1])]
    x0, y0, cw, rh = 330, 146, 122, 58
    for j, l in enumerate(langs):
        for k, line in enumerate(l.split("\n")):
            sh.txt(x0 + j * cw + cw / 2, 106 + k * 14, line, size=6.6, fill=NUIT,
                   weight="700")
    for i, (c, notes) in enumerate(crits):
        yy = y0 + i * rh
        sh.rect(40, yy, 900, rh - 8, fill="#FAFBFA" if i % 2 else "#fff",
                stroke=TRAIT, sw=0.9, rx=3)
        sh.txt(56, yy + 30, c, size=6.6, fill=INK, anchor="start")
        for j, n in enumerate(notes):
            stars(sh, x0 + j * cw + 24, yy + 26, n)
    sh.rect(40, y0 + len(crits) * rh + 6, 900, 76, fill=OR_PL, stroke=OR, sw=1.4,
            rx=6)
    sh.txt(60, y0 + len(crits) * rh + 32, "VERDICT", size=7, fill=OR, weight="700",
           anchor="start", spacing="1.2")
    sh.txt(60, y0 + len(crits) * rh + 54,
           "Python 3 for the application, a C core in the microcontroller, and NumPy for the hot loops.", size=6.6, fill=NUIT, anchor="start")
    sh.txt(60, y0 + len(crits) * rh + 70,
           "Rust becomes the right choice the day the board has to work without a computer.", size=6.2, fill=GRIS, anchor="start")
    sh.signer()
    sh.save("logiciel-langages.svg")


# =============================================================================
#  GRAPHICAL TOOLKITS COMPARED
# =============================================================================
def fig_toolkits():
    sh = Sheet(980, 600, print_mm=125)
    sh.title("Which graphical toolkit?",
             "The deciding criterion is not beauty: it is plotting 250 points per second")

    kits = [("Qt 6 (PySide6)", 5, 5, 5, 4, "LGPL · 60 im/s via pyqtgraph"),
            ("GTK 4 (PyGObject)", 3, 3, 4, 3, "painful to install on Windows"),
            ("wxWidgets (wxPython)", 3, 3, 3, 3, "native, but the plotting is dated"),
            ("Tkinter", 2, 1, 5, 2, "the canvas saturates beyond 20 fps"),
            ("Dear PyGui", 4, 4, 4, 2, "GPU rapide, peu accessible"),
            ("HTML5 + TypeScript", 4, 4, 3, 5, "Electron/Tauri : 180 Mo, passerelle")]
    heads = ["Plotting\nspeed", "Widget\ncoverage", "Easy to\ninstall",
             "Native\nlook"]
    x0, cw = 470, 110
    for j, h in enumerate(heads):
        for k, line in enumerate(h.split("\n")):
            sh.txt(x0 + j * cw + cw / 2, 104 + k * 13, line, size=6, fill=GRIS)
    for i, (nom, a, b, c, d, com) in enumerate(kits):
        yy = 132 + i * 72
        sh.rect(40, yy, 900, 64, fill="#FAFBFA" if i % 2 else "#fff",
                stroke=TRAIT, sw=0.9, rx=4)
        sh.txt(56, yy + 26, nom, size=7.2, fill=NUIT, anchor="start", weight="700",
               family=SERIF)
        sh.txt(56, yy + 46, com, size=6, fill=GRIS, anchor="start")
        for j, n in enumerate((a, b, c, d)):
            stars(sh, x0 + j * cw + 26, yy + 30, n)
    sh.txt(490, 580, "Chosen: PySide6 + pyqtgraph. The rest of the document explains how to replace it should the choice age.", size=6.4, fill=OR,
           weight="700")
    sh.signer()
    sh.save("logiciel-toolkits.svg")


# =============================================================================
#  THE THREE HARDWARE LEVELS
# =============================================================================
def fig_tiers():
    sh = Sheet(980, 520, print_mm=125)
    sh.title("Where this board sits",
             "Three levels of instrument, three uses, three budgets")

    tiers = [("NIVEAU 1", "Oscillateur NE555", "25 – 40 €",
              ["measures: a period", "output: MIDI", "no calibration",
               "ideal for understanding"], SEVE, "#EDF5F0",
              "The Music of Plants, part X"),
             ("NIVEAU 2", "INA333 + ADS1115", "60 – 120 €",
              ["measures: a voltage", "16 bits, 860 samples/s", "relative calibration",
               "ideal for a workshop"], BLEU, "#EEF3FA",
              "Build a Talking Tree, figure 2"),
             ("NIVEAU 3", "PhytoSense One", "180 – 240 €",
              ["measures: volts and ohms", "24 bits, isolated, timestamped", "absolute calibration",
               "ideal for publishing"], OR, "#FBF5E6", "This document")]
    for i, (n, t, prix, pts, col, fill, src) in enumerate(tiers):
        x = 40 + i * 306
        sh.rect(x, 96, 288, 340, fill=fill, stroke=col, sw=1.8, rx=8)
        sh.rect(x, 96, 288, 34, fill=col, stroke=col, sw=1.8, rx=8)
        sh.txt(x + 144, 118, n, size=6.8, fill="#fff", weight="700", spacing="1.6")
        sh.txt(x + 144, 158, t, size=9, fill=NUIT, weight="700", family=SERIF)
        sh.txt(x + 144, 182, prix, size=7.6, fill=col, weight="700", family=MONO)
        for k, p in enumerate(pts):
            sh.txt(x + 24, 216 + k * 26, "·", size=8, fill=col, anchor="start")
            sh.txt(x + 40, 216 + k * 26, p, size=6.4, fill=INK, anchor="start")
        sh.line(x + 24, 340, x + 264, 340, stroke=col, sw=1.0)
        sh.txt(x + 144, 362, "described in", size=5.8, fill=GRIS)
        for k, line in enumerate(src.split(", ")):
            sh.txt(x + 144, 382 + k * 15, line, size=6.2, fill=NUIT, style="italic")
    sh.txt(490, 470, "The three builds share the same electrodes and the same software: you move up a level without throwing anything away.", size=6.6, fill=NUIT,
           weight="700")
    sh.signer()
    sh.save("carte-tiers.svg")


# =============================================================================
#  HORODATAGE
# =============================================================================
def fig_horodatage():
    sh = Sheet(980, 520, print_mm=125)
    sh.title("Timestamping: two clocks, one truth",
             "The sample index is authoritative; the system clock is only a label")

    sh.rect(40, 96, 420, 180, fill="#F3F8F5", stroke=SEVE, sw=1.4, rx=8)
    sh.txt(250, 120, "THE BOARD'S CLOCK", size=6.8, fill=SEVE, weight="700",
           spacing="1.2")
    sh.txt(250, 148, "TCXO 12,288 MHz · ±1 ppm", size=7, fill=NUIT, family=MONO)
    sh.txt(250, 172, "n = 0, 1, 2, 3 … compteur 64 bits", size=6.4, fill=INK)
    sh.txt(250, 196, "t = n / 250 Hz, exactement", size=6.4, fill=INK)
    sh.txt(250, 226, "drift: 86 ms a day, at worst", size=6.2, fill=GRIS)
    sh.txt(250, 248, "never corrected during a session", size=6.2, fill=CUIVRE,
           weight="700")

    sh.rect(520, 96, 420, 180, fill="#EEF3FA", stroke=BLEU, sw=1.4, rx=8)
    sh.txt(730, 120, "HORLOGE DE L'ORDINATEUR", size=6.8, fill=BLEU, weight="700",
           spacing="1.2")
    sh.txt(730, 148, "CLOCK_MONOTONIC + UTC", size=7, fill=NUIT, family=MONO)
    sh.txt(730, 172, "sauts possibles : NTP, veille,", size=6.4, fill=INK)
    sh.txt(730, 192, "changement d'heure, suspension", size=6.4, fill=INK)
    sh.txt(730, 226, "used only to name files", size=6.2, fill=GRIS)
    sh.txt(730, 248, "and to date the session's start", size=6.2, fill=GRIS)

    block(sh, 250, 320, 480, 78, "An affine fit, as it goes",
          "t_UTC = a · n + b, re-estimated every 10 s",
          fill=OR_PL, stroke=OR, sw=1.6, tsize=7.6)
    sh.arrow(250, 276, 360, 316, color=SEVE, sw=1.8, marker="ahv")
    sh.arrow(730, 276, 620, 316, color=BLEU, sw=1.8, marker="ahb")
    sh.txt(490, 430, "Result: two sessions recorded on two different machines "
           "stay superimposable to the millisecond.", size=6.6,
           fill=NUIT, weight="700")
    sh.txt(490, 452, "Every file carries both scales; neither is lost.",
           size=6.2, fill=GRIS)
    sh.signer()
    sh.save("carte-horodatage.svg")


# =============================================================================
#  PRINTED CIRCUIT BOARD — PLACEMENT AND FOUR-LAYER ROUTING
# =============================================================================
#  The drawing is described in real millimetres: the board is 100 x 60 mm.
#  A conversion function places those millimetres inside the viewBox, so
#  that the dimensions marked on the figures are the true ones.
# -----------------------------------------------------------------------------
CARTE_L, CARTE_H = 100.0, 60.0          # overall dimensions, in millimetres

#  (reference, x, y, width, height, rotation, description)
COMPOSANTS = [
    ("J1",   6.0,  12.0, 12.0, 12.0, "channel A input"),
    ("J2",   6.0,  30.0, 12.0, 12.0, "channel B input"),
    ("U1",  26.0,  14.0,  6.0,  6.0, "ADA4530-1"),
    ("R1",  22.0,  24.0,  3.2,  1.6, "10 kΩ"),
    ("R2",  27.0,  24.0,  3.2,  1.6, "1 GΩ"),
    ("D1",  22.0,  27.5,  2.0,  1.3, "BAV199"),
    ("J10", 38.0,  27.0,  4.0, 34.0, "mezzanine"),
    ("U3",  50.0,  14.0,  5.0,  4.4, "INA828"),
    ("U7",  50.0,  24.0,  5.0,  4.4, "OPA2189"),
    ("U8",  50.0,  32.0,  5.0,  4.4, "TMUX1208"),
    ("U9",  62.0,  14.0,  4.0,  4.0, "THS4551"),
    ("U10", 62.0,  22.0,  6.0,  6.0, "ADS131M04"),
    ("U11", 62.0,  32.0,  4.0,  3.0, "ADR4525"),
    ("Y1",  71.0,  32.0,  5.0,  3.2, "TCXO"),
    ("T1",  30.0,  46.0, 14.0, 10.0, "transformateur"),
    ("U20", 20.0,  47.0,  5.0,  4.0, "SN6505B"),
    ("U21", 48.0,  46.0,  4.0,  3.0, "LT3045"),
    ("U22", 48.0,  52.0,  4.0,  3.0, "LT3094"),
    ("U24", 62.0,  46.0,  8.0,  7.6, "ADuM4151"),
    ("U30", 80.0,  18.0, 10.0, 10.0, "RP2350B"),
    ("U31", 80.0,  32.0,  5.0,  4.0, "flash"),
    ("Y2",  92.0,  32.0,  3.2,  2.5, "12 MHz"),
    ("J20", 93.0,  20.0,  9.0,  7.4, "USB-C"),
    ("J21", 93.0,  44.0,  6.0,  6.0, "MIDI TRS"),
    ("U33", 88.0,  44.0,  3.0,  2.0, "ESD"),
]

#  Tracks per layer: each track is a polyline in millimetres.
PISTES = {
    1: [  # analog signals, component side
        [(12, 12), (22, 12), (22, 14), (26, 14)],
        [(12, 30), (20, 30), (20, 20), (26, 17)],
        [(32, 14), (36, 14), (36, 12), (38, 12)],
        [(32, 17), (36, 17), (36, 20), (38, 20)],
        [(42, 14), (46, 14), (46, 16), (50, 16)],
        [(42, 24), (46, 24), (46, 26), (50, 26)],
        [(55, 16), (58, 16), (58, 15), (62, 15)],
        [(55, 26), (58, 26), (58, 24), (62, 24)],
        [(66, 15), (68, 15), (68, 22), (68, 24)],
        [(66, 34), (69, 34), (69, 33), (71, 33)],
        [(22, 25), (27, 25)],
        [(24, 27), (24, 24)],
    ],
    2: [  # plan de masse fendu : seules quelques liaisons de garde
        [(20, 8), (20, 40)],
        [(34, 8), (34, 40)],
        [(52, 40), (52, 44)],
    ],
    3: [  # alimentations
        [(52, 47), (58, 47), (58, 20), (60, 20)],
        [(52, 53), (56, 53), (56, 30), (60, 30)],
        [(25, 48), (28, 48)],
        [(25, 51), (28, 51)],
        [(44, 47), (48, 47)],
        [(44, 51), (48, 51)],
        [(70, 48), (76, 48), (76, 28), (80, 28)],
        [(96, 24), (96, 16), (86, 16), (86, 18)],
    ],
    4: [  # digital signals and shielding
        [(70, 46), (76, 46), (76, 22), (80, 22)],
        [(70, 49), (74, 49), (74, 24), (80, 24)],
        [(70, 52), (73, 52), (73, 26), (80, 26)],
        [(85, 22), (90, 22), (90, 21), (93, 21)],
        [(85, 24), (89, 24), (89, 24), (93, 24)],
        [(85, 30), (88, 30), (88, 33), (80, 33)],
        [(85, 34), (90, 34), (90, 33), (92, 33)],
        [(85, 36), (88, 36), (88, 45), (93, 45)],
        [(66, 50), (68, 50)],
    ],
}

VIAS = [(36, 12), (36, 20), (46, 16), (58, 15), (68, 24), (76, 28), (76, 22),
        (88, 33), (52, 44), (58, 20), (56, 30), (73, 26), (90, 22), (20, 20),
        (34, 24), (69, 33)]

COUCHES = {
    1: ("Layer 1 — analog signals", "#B03A2E", "component side"),
    2: ("Layer 2 — ground plane (slotted)", "#1E6F50", "single reference"),
    3: ("Layer 3 — supplies", "#2F5E86", "±5 V, 3.3 V, 5 V"),
    4: ("Layer 4 — digital signals", "#8A6A1F", "solder side"),
}


def _pcb_transform(x0: float, y0: float, echelle: float):
    """Return a function mapping millimetres to viewBox units."""
    def mm(x: float, y: float):
        return (x0 + x * echelle, y0 + y * echelle)
    return mm


def _dessiner_carte(sh, mm, echelle, couche: int, avec_composants: bool = True,
                    avec_reperes: bool = True):
    """Draw the outline, the mounting holes, the parts and the tracks."""
    x0, y0 = mm(0, 0)
    x1, y1 = mm(CARTE_L, CARTE_H)
    sh.rect(x0, y0, x1 - x0, y1 - y0, fill="#F7F9F7", stroke=NUIT, sw=2.0, rx=4)

    # slot in the ground plane: the isolation barrier
    xa, _ = mm(56, 0)
    sh.line(xa, y0 + 2, xa, y1 - 2, stroke=CUIVRE, sw=2.0, dash="8 5")

    for cx, cy in ((4, 4), (CARTE_L - 4, 4), (4, CARTE_H - 4),
                   (CARTE_L - 4, CARTE_H - 4)):
        px, py = mm(cx, cy)
        sh.circle(px, py, 1.6 * echelle, fill="#fff", stroke=GRIS, sw=1.2)
        sh.circle(px, py, 0.8 * echelle, fill=GRIS, stroke=GRIS, sw=0.8)

    # guard ring around the inputs
    gx, gy = mm(3, 8)
    gx2, gy2 = mm(34, 44)
    sh.rect(gx, gy, gx2 - gx, gy2 - gy, fill="none", stroke=OR, sw=1.8, dash="5 3")

    if avec_composants:
        for ref, cx, cy, w, h, _desc in COMPOSANTS:
            px, py = mm(cx - w / 2, cy - h / 2)
            sh.rect(px, py, w * echelle, h * echelle, fill="#E8EDEA",
                    stroke=GRIS, sw=1.0, rx=1.5)
            if w * echelle > 22:
                sh.txt(px + w * echelle / 2, py + h * echelle / 2 + 4, ref,
                       size=5.4, fill=NUIT, weight="700")

    couleur = COUCHES[couche][1]
    for piste in PISTES.get(couche, []):
        pts = [mm(x, y) for x, y in piste]
        sh.wire(*pts, stroke=couleur, sw=2.2)

    for vx, vy in VIAS:
        px, py = mm(vx, vy)
        sh.circle(px, py, 0.55 * echelle, fill="#fff", stroke=NUIT, sw=1.0)

    # -- silkscreen: the project name, the author and the address ------------
    #  Etched into the silkscreen layer: a board that circulates must say
    #  where it came from, even when separated from its documentation.
    if echelle >= 3.0:
        sx, sy = mm(10, 57.2)
        sh.txt(sx, sy, PROJET.upper(), size=max(4.4, echelle * 0.62),
               fill=NUIT, weight="700", anchor="start", spacing="0.6")
        sh.txt(sx, sy + echelle * 1.05, AUTEUR.upper(),
               size=max(4.0, echelle * 0.52), fill=GRIS, anchor="start",
               spacing="0.5")
        tx, ty = mm(90, 57.2)
        sh.txt(tx, ty, SITE, size=max(4.0, echelle * 0.52), fill=GRIS,
               anchor="end")
        sh.txt(tx, ty + echelle * 1.05, "REV. B · CERN-OHL-P v2",
               size=max(3.8, echelle * 0.46), fill=GRIS, anchor="end")

    if avec_reperes:
        sh.txt((x0 + x1) / 2, y1 + 16, f"{CARTE_L:.0f} mm", size=6, fill=GRIS)
        sh.txt(x0 - 14, (y0 + y1) / 2, f"{CARTE_H:.0f} mm", size=6, fill=GRIS,
               rot=-90)


def pl_pcb_couches():
    """Plate: the four layers, side by side."""
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Routing — four layers", sheet="1/3", bloc="Printed circuit board")
    sh.txt(90, 74, "PhytoSense One — 100 × 60 mm board, FR4 1.6 mm, 35 µm copper", size=8.2, fill=NUIT, weight="700", anchor="start",
           family=SERIF)

    echelle = 4.0
    positions = ((70, 130), (600, 130), (70, 410), (600, 410))
    for (px, py), couche in zip(positions, (1, 2, 3, 4)):
        titre, couleur, sous = COUCHES[couche]
        sh.txt(px, py - 14, titre, size=7.0, fill=couleur, weight="700",
               anchor="start")
        sh.txt(px + 400, py - 14, sous, size=5.8, fill=GRIS, anchor="end")
        mm = _pcb_transform(px, py, echelle)
        _dessiner_carte(sh, mm, echelle, couche,
                        avec_composants=(couche in (1, 4)), avec_reperes=False)

    # --- key ---------------------------------------------------------------
    lx, ly = 1030, 130
    sh.rect(lx, ly, 260, 380, fill="#FBFBF7", stroke=TRAIT, sw=1.0, rx=5)
    sh.txt(lx + 130, ly + 20, "KEY", size=6.6, fill=NUIT, weight="700",
           spacing="1.4")
    entrees = [(COUCHES[1][1], "layer 1 track"), (COUCHES[2][1], "layer 2 track"),
               (COUCHES[3][1], "layer 3 track"), (COUCHES[4][1], "layer 4 track"),
               (CUIVRE, "slot in the ground plane"), (OR, "guard ring")]
    for i, (couleur, libelle) in enumerate(entrees):
        yy = ly + 44 + i * 22
        sh.line(lx + 14, yy, lx + 44, yy, stroke=couleur, sw=2.4,
                dash="8 5" if i >= 4 else None)
        sh.txt(lx + 52, yy + 4, libelle, size=5.8, fill=INK, anchor="start")
    yy = ly + 44 + len(entrees) * 22 + 10
    sh.circle(lx + 29, yy, 5, fill="#fff", stroke=NUIT, sw=1.0)
    sh.txt(lx + 52, yy + 4, "via traversant 0,3 mm", size=5.8, fill=INK,
           anchor="start")
    sh.circle(lx + 29, yy + 22, 6, fill="#fff", stroke=GRIS, sw=1.2)
    sh.txt(lx + 52, yy + 26, "fixation M3", size=5.8, fill=INK, anchor="start")
    for i, ligne in enumerate([
            "Scale 1 : 2.5", "",
            "The slot in the ground plane",
            "separates the analog ground",
            "analog ground from the USB ground.",
            "No track crosses it:",
            "only transformer T1 and",
            "the U24 isolators span it,",
            "and they span it through air."]):
        sh.txt(lx + 14, yy + 56 + i * 15, ligne, size=5.6, fill=GRIS,
               anchor="start")
    sh.txt(500, 770, "All four layers are shown from above (layer 4 not mirrored) — the convention of the supplied Gerber files.", size=6.0, fill=GRIS)
    sh.save("pcb-couches.svg")


def pl_pcb_implantation():
    """Plate: placement, silkscreen and dimensions."""
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Placement and silkscreen", sheet="2/3",
              bloc="Printed circuit board")
    sh.txt(90, 74, "Placement seen from above — silkscreen markings and functional zones", size=8.2, fill=NUIT, weight="700", anchor="start",
           family=SERIF)

    echelle = 8.2
    mm = _pcb_transform(140, 140, echelle)
    _dessiner_carte(sh, mm, echelle, 1, avec_composants=True)

    # --- labels, spread out so they do not overlap ------------------------
    #  The parts are packed close together, so the labels are spread over two
    #  columns, at least one line-height apart, with a leader drawn back to
    #  the pad.
    def _placer(elements, tx, anchor):
        elements = sorted(elements, key=lambda e: e[1])
        pas = 17.0
        haut = 150.0
        precedent = -1e9
        for ref, py, desc, px in elements:
            y = max(py, precedent + pas, haut)
            precedent = y
            sh.line(px, py, tx + (10 if anchor == "start" else -10), y,
                    stroke=TRAIT, sw=0.7)
            sh.txt(tx, y + 3, f"{ref} — {desc}", size=5.6, fill=INK,
                   anchor=anchor)

    gauche, droite = [], []
    for ref, cx, cy, w, h, desc in COMPOSANTS:
        px, py = mm(cx, cy)
        (gauche if cx < 50 else droite).append((ref, py, desc, px))
    _placer(gauche, 118, "end")
    _placer(droite, 140 + CARTE_L * echelle + 24, "start")

    zones = [("inputs and guard", 3, 8, 31, 36, OR),
             ("conditionnement", 46, 8, 28, 30, SEVE),
             ("isolated supply", 14, 42, 42, 16, CUIVRE),
             ("digital and USB", 74, 12, 24, 40, BLEU)]
    for nom, zx, zy, zw, zh, couleur in zones:
        ax, ay = mm(zx, zy)
        sh.rect(ax, ay, zw * echelle, zh * echelle, fill="none", stroke=couleur,
                sw=1.2, dash="4 3")
        sh.txt(ax + 4, ay + 12, nom, size=5.8, fill=couleur, anchor="start",
               weight="700")
    sh.save("pcb-implantation.svg")


def fig_pcb_empilage():
    """Figure: the stack-up, impedances and drilling rules."""
    sh = Sheet(980, 640, print_mm=125)
    sh.title("Stack-up, impedances and drilling",
             "Four layers on 1.6 mm FR4 — what the fabricator needs to know")

    couches = [("Layer 1 — analog signals", "35 µm", "#D9C08A", 20),
               ("Prepreg 7628 x1", "0,20 mm", "#F0EEE4", 14),
               ("Layer 2 — AGND / DGND ground (slotted)", "35 µm", "#8FA79A", 24),
               ("FR4 core Tg150", "1,00 mm", "#E6E2D2", 30),
               ("Layer 3 — supplies", "35 µm", "#B9C6BF", 22),
               ("Prepreg 7628 x1", "0,20 mm", "#F0EEE4", 14),
               ("Layer 4 — digital and shielding", "35 µm", "#D9C08A", 20)]
    y = 100
    for nom, ep, couleur, h in couches:
        sh.rect(60, y, 420, h, fill=couleur, stroke=INK, sw=1.0)
        sh.txt(492, y + h / 2 + 4, nom, size=6.6, fill=INK, anchor="start")
        sh.txt(474, y + h / 2 + 4, ep, size=6, fill=GRIS, anchor="end")
        y += h
    sh.txt(270, y + 22, "total thickness 1.60 mm ± 10 %", size=6.4, fill=NUIT,
           weight="700")

    lignes = [
        ("Minimum track width", "0.20 mm (8 mil)"),
        ("Minimum clearance", "0.20 mm — 0.60 mm either side of the slot"),
        ("Through via", "0.30 mm drill, 0.60 mm pad"),
        ("Ground via under the packages", "on a 1.2 mm grid"),
        ("USB differential impedance", "90 Ω ± 10 % (layer 4 over layer 3)"),
        ("ADC clock impedance", "50 Ω single-ended"),
        ("Finish", "ENIG — mandatory under the electrometer inputs"),
        ("Mask keep-out", "under J1, J2 and the guard ring"),
        ("IPC class", "2 (standard fabrication, no extra cost)"),
    ]
    y0 = 300
    sh.txt(60, y0 - 12, "FABRICATION RULES", size=7.2, fill=NUIT,
           weight="700", anchor="start", spacing="1.2")
    for i, (cle, valeur) in enumerate(lignes):
        yy = y0 + i * 26
        sh.rect(60, yy, 860, 22, fill="#FAFBFA" if i % 2 else "#fff",
                stroke=TRAIT, sw=0.8, rx=3)
        sh.txt(72, yy + 15, cle, size=6.4, fill=INK, anchor="start")
        sh.txt(908, yy + 15, valeur, size=6.4, fill=SEVE, anchor="end",
               weight="700")
    note(sh, 60, y0 + len(lignes) * 26 + 16, 860,
         ["The mask keep-out under the inputs is not a cosmetic detail: a film of",
          "damp solder mask conducts quite enough to ruin a 10¹⁵ Ω measurement. It is the",
          "first thing to check when a channel drifts for no apparent reason."],
         title="THE POINT THAT SINKS A FIRST PRODUCTION RUN", color=CUIVRE,
         fill=CUIV_P)
    sh.signer()
    sh.save("pcb-empilage.svg")


# =============================================================================
#  COUVERTURES
# =============================================================================
def _fond_circuit(sh, w, h, seed=11, densite=40):
    """A weave of PCB tracks, as a cover background."""
    import random as _r
    rng = _r.Random(seed)
    sh.rect(0, 0, w, h, fill=NUIT)
    for i in range(densite):
        x = rng.uniform(0, w)
        y = rng.uniform(0, h)
        pts = [(x, y)]
        for _ in range(rng.randint(2, 5)):
            horizontal = rng.random() < 0.5
            d = rng.uniform(40, 180) * rng.choice((-1, 1))
            x, y = (x + d, y) if horizontal else (x, y + d)
            pts.append((x, y))
        couleur = rng.choice((SEVE, SEVE_C, OR, "#1E4A3A"))
        sh.wire(*pts, stroke=couleur, sw=rng.uniform(1.0, 2.6))
        sh.circle(pts[-1][0], pts[-1][1], rng.uniform(2.5, 5),
                  fill=NUIT, stroke=couleur, sw=1.4)
    for _ in range(90):
        sh.circle(rng.uniform(0, w), rng.uniform(0, h), rng.uniform(1.2, 2.6),
                  fill=OR, stroke=OR, sw=0.6, op=rng.uniform(0.15, 0.5))


def _feuille_nervures(sh, cx, cy, hauteur, couleur=SEVE_C, op=0.9):
    """A stylised leaf whose veins are copper tracks."""
    w = hauteur * 0.46
    sh.path(f"M {cx},{cy - hauteur / 2} "
            f"C {cx + w},{cy - hauteur * 0.18} {cx + w},{cy + hauteur * 0.18} "
            f"{cx},{cy + hauteur / 2} "
            f"C {cx - w},{cy + hauteur * 0.18} {cx - w},{cy - hauteur * 0.18} "
            f"{cx},{cy - hauteur / 2} Z",
            stroke=couleur, sw=2.4, fill="#123227")
    sh.line(cx, cy - hauteur / 2 + 6, cx, cy + hauteur / 2 - 6, stroke=couleur,
            sw=2.0)
    n = 7
    for i in range(1, n):
        t = i / n
        y = cy - hauteur / 2 + t * hauteur
        etendue = w * 0.82 * math.sin(math.pi * t)
        for signe in (-1, 1):
            sh.wire((cx, y), (cx + signe * etendue * 0.6, y - hauteur * 0.05),
                    (cx + signe * etendue, y - hauteur * 0.09),
                    stroke=couleur, sw=1.3)
            sh.circle(cx + signe * etendue, y - hauteur * 0.09, 2.6, fill=OR,
                      stroke=OR, sw=0.8, op=0.8)


def fig_cover():
    """Couverture de l'ouvrage principal."""
    sh = Sheet(1000, 1412, print_mm=170, bg=None)
    _fond_circuit(sh, 1000, 1412, seed=5, densite=46)
    # halo central
    sh.add(f'<defs><radialGradient id="halo"><stop offset="0%" '
           f'stop-color="#1E4A3A" stop-opacity="0.95"/><stop offset="100%" '
           f'stop-color="{NUIT}" stop-opacity="0"/></radialGradient></defs>')
    sh.add('<ellipse cx="500" cy="720" rx="460" ry="420" fill="url(#halo)"/>')
    _feuille_nervures(sh, 500, 720, 520)
    # the trace of a signal leaving the leaf
    pts = []
    import random as _r
    rng = _r.Random(3)
    v = 0.0
    for i in range(240):
        v += rng.gauss(0, 0.5)
        v *= 0.93
        if i in (110, 111, 112):
            v += 7
        pts.append((250 + i * 2.1, 1080 - v * 9))
    sh.path("M " + " L ".join(f"{a:.1f},{b:.1f}" for a, b in pts),
            stroke="#7FE0A8", sw=2.6)
    sh.save("carte-cover.svg")


def _couverture_annexe(nom, titre, sous_titre, feuille, seed):
    """A plain cover for the three detachable fascicles."""
    sh = Sheet(1000, 1412, print_mm=170, bg=None)
    _fond_circuit(sh, 1000, 1412, seed=seed, densite=30)
    sh.rect(70, 70, 860, 1272, fill="none", stroke=OR, sw=2.0, op=0.55)
    sh.rect(84, 84, 832, 1244, fill="none", stroke=OR, sw=1.0, op=0.3)
    sh.txt(500, 430, "PHYTOSENSE ONE", size=12, fill=OR_CL, weight="700",
           spacing="7", family=SANS)
    sh.line(330, 470, 670, 470, stroke=OR, sw=1.2)
    for i, ligne in enumerate(titre.split("\n")):
        sh.txt(500, 560 + i * 74, ligne, size=30, fill="#FFFFFF", weight="700",
               family=SERIF)
    sh.txt(500, 700, sous_titre, size=12, fill=SEVE_C, style="italic",
           family=SERIF)
    sh.txt(500, 1180, feuille, size=10, fill=OR_CL, spacing="3")
    sh.txt(500, 1230, "Bretagne Namasté · 2026", size=9, fill="#9fb8ab")
    sh.save(nom)


def fig_cover_schemas():
    _couverture_annexe("carte-cover-schemas.svg",
                       "Schematic\nset",
                       "Six sheets — revision B", "ANNEXE 1", 17)


def fig_cover_bom():
    _couverture_annexe("carte-cover-bom.svg",
                       "Bill of materials\nand accessories",
                       "47 part numbers · itemized budgets", "ANNEXE 2", 23)


def fig_cover_pcb():
    _couverture_annexe("carte-cover-pcb.svg",
                       "Printed\ncircuit",
                       "Four layers — the fabrication package", "ANNEXE 3", 31)


# =============================================================================
#  PLANCHE 7 — PROTECTIONS ET GESTION DE L'ALIMENTATION
# =============================================================================
def pl_protections():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Protections and power management", sheet="7/8",
              bloc="Main board")
    sh.txt(90, 74, "Two sources, one priority, and nothing that breaks if you get it wrong", size=8.4, fill=NUIT, weight="700", anchor="start",
           family=SERIF)

    # ---------------- voie « bloc secteur » --------------------------------
    sh.rect(60, 104, 560, 210, fill="#FBF8EF", stroke=OR, sw=1.2, rx=6, dash="7 5")
    sh.txt(340, 124, "MAINS ADAPTER INPUT — 7 to 24 V, either polarity",
           size=6.6, fill=OR, weight="700", spacing="1")

    pJ30 = connector(sh, 82, 150, 3, "J30 · 2,1 mm", pitch=42, w=50,
                     pinlabels=["+", "−", "S"])
    sh.wire(pJ30[0], (210, 170), stroke=INK, sw=1.8)

    # reverse-polarity protection by a P-channel MOSFET
    ic_box(sh, 210, 146, 96, 58, "Q30", "DMP3099L", "anti-inversion")
    sh.txt(258, 222, "a reversal blocks,", size=5.8, fill=GRIS)
    sh.txt(258, 236, "it destroys nothing", size=5.8, fill=GRIS)

    sh.wire((306, 170), (346, 170), stroke=INK, sw=1.8)
    sh.dot(346, 170)
    diode_up(sh, 346, 240, L=60)
    sh.txt(316, 262, "D30 · SMAJ18A", size=6.2, fill=SEVE, anchor="start",
           weight="700")
    sh.txt(316, 276, "clamps at 18 V, 400 W", size=5.8, fill=GRIS, anchor="start")
    sh.wire((346, 240), (346, 262), stroke=INK)
    ground(sh, 346, 262, "dgnd")

    sh.wire((346, 170), (420, 170), stroke=INK, sw=1.8)
    ic_box(sh, 420, 142, 120, 66, "U60", "TPS62932", "abaisseur 5,2 V")
    sh.txt(480, 222, "2 A · 92 % · short-circuit protected", size=5.8, fill=GRIS)
    sh.wire((540, 170), (600, 170), (600, 300), stroke=CUIVRE, sw=2.0)
    sh.txt(572, 156, "5,2 V", size=6.4, fill=CUIVRE, weight="700", family=MONO)

    # ---------------- voie USB ---------------------------------------------
    sh.rect(60, 340, 560, 190, fill="#F2F6FC", stroke=BLEU, sw=1.2, rx=6, dash="7 5")
    sh.txt(340, 360, "USB INPUT — 5 V, 500 mA declared", size=6.6, fill=BLEU,
           weight="700", spacing="1")

    netflag(sh, 82, 400, "VBUS", side="in", w=64)
    sh.wire((146, 400), (190, 400), stroke=INK, sw=1.8)
    ferrite(sh, 190, 400, "FB1", "600 Ω")
    sh.wire((266, 400), (300, 400), stroke=INK, sw=1.8)
    ic_box(sh, 300, 372, 130, 66, "U61", "TPS2553", "limits to 500 mA")
    sh.txt(365, 452, "opens in 2 µs on a short,", size=5.8, fill=GRIS)
    sh.txt(365, 466, "flags the fault, resets itself", size=5.8, fill=GRIS)
    sh.wire((430, 400), (600, 400), (600, 330), stroke=CUIVRE, sw=2.0)
    sh.txt(500, 390, "5,0 V", size=6.4, fill=CUIVRE, weight="700", family=MONO)
    netflag(sh, 300, 480, "FAULT", side="out", color=CUIVRE, w=70)
    sh.wire((370, 480), (410, 480), (410, 438), stroke=CUIVRE, sw=1.2, dash="4 3")

    # ---------------- aiguilleur -------------------------------------------
    ic_box(sh, 640, 270, 150, 90, "U62", "TPS2116", "priority selector")
    sh.txt(715, 378, "the mains adapter wins;", size=5.8, fill=GRIS)
    sh.txt(715, 392, "switches without a break;", size=5.8, fill=GRIS)
    sh.txt(715, 406, "reverse blocking on both sides", size=5.8, fill=GRIS)
    sh.wire((600, 300), (640, 300), stroke=CUIVRE, sw=2.0)
    sh.wire((600, 330), (640, 330), stroke=CUIVRE, sw=2.0)
    sh.wire((790, 315), (850, 315), stroke=CUIVRE, sw=2.4)
    sh.txt(820, 305, "5 V", size=6.6, fill=CUIVRE, weight="700", family=MONO)

    # ---------------- mesure de consommation --------------------------------
    resistor(sh, 850, 315, "R60", "0,1 Ω", L=80)
    sh.wire((930, 315), (980, 315), stroke=CUIVRE, sw=2.4)
    ic_box(sh, 980, 286, 130, 62, "U63", "INA219", "voltage and current")
    sh.txt(1045, 366, "feeds the display:", size=5.8, fill=GRIS)
    sh.txt(1045, 380, "5,03 V · 137 mA · 0,69 W", size=5.8, fill=SEVE, weight="700")
    netflag(sh, 980, 410, "I²C", side="out", color=BLEU, w=56)

    sh.wire((1110, 315), (1180, 315), stroke=CUIVRE, sw=2.4)
    ferrite(sh, 1180, 315, "F30", "0,5 A")
    sh.wire((1256, 315), (1284, 315), stroke=CUIVRE, sw=2.4)
    rail(sh, 1284, 315, "5 V board")

    # ---------------- protection of the measurement inputs ------------------
    sh.rect(640, 430, 660, 180, fill="#FBEEE6", stroke=CUIVRE, sw=1.2, rx=6,
            dash="7 5")
    sh.txt(970, 450, "MEASUREMENT INPUT PROTECTION", size=6.6, fill=CUIVRE,
           weight="700", spacing="1")

    netflag(sh, 656, 490, "ELECTRODE", side="in", color=SEVE, w=98)
    sh.wire((754, 490), (786, 490), stroke=INK, sw=1.6)
    ferrite(sh, 786, 490, "F1", "50 mA")
    sh.wire((862, 490), (896, 490), stroke=INK, sw=1.6)
    resistor(sh, 896, 490, "R1", "10 kΩ", L=80)
    sh.wire((976, 490), (1010, 490), stroke=INK, sw=1.6)
    sh.dot(1010, 490)
    sh.wire((1010, 490), (1010, 528), stroke=INK)
    ic_box(sh, 962, 528, 96, 44, "D3", "PESD5V0", "")
    sh.wire((1010, 572), (1010, 584), stroke=INK)
    ground(sh, 1010, 584, "agnd")
    sh.wire((1010, 490), (1080, 490), stroke=INK, sw=1.6)
    sh.txt(1096, 486, "to U1", size=6.2, fill=SEVE, anchor="start", weight="700")
    sh.txt(1096, 500, "(sheet 1)", size=5.8, fill=GRIS, anchor="start")
    sh.txt(1096, 528, "0,5 pF seulement :", size=5.8, fill=GRIS, anchor="start")
    sh.txt(1096, 542, "does not load the input", size=5.8, fill=GRIS, anchor="start")
    sh.txt(700, 556, "connecting to a live source opens the fuse",
           size=5.8, fill=GRIS, anchor="start")
    sh.txt(700, 570, "instead of destroying the input amplifier",
           size=5.8, fill=GRIS, anchor="start")

    note(sh, 60, 560, 550,
         ["Any combination is allowed: mains adapter alone, USB alone, or both.",
          "Changing from one to the other happens without a break or a restart — you can",
          "unplug the computer mid-session without losing a sample."],
         title="TWO SOURCES, NO HANDLING", color=SEVE, fill=SEVE_P)
    sh.save("carte-protections.svg")


# =============================================================================
#  PLANCHE 8 — SIGNALISATION ET AFFICHEUR
# =============================================================================
def pl_ihm():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Indicators and display", sheet="8/8", bloc="Main board")
    sh.txt(90, 74, "What the instrument shows without opening any software",
           size=8.4, fill=NUIT, weight="700", anchor="start", family=SERIF)

    # ---- voyants -----------------------------------------------------------
    sh.rect(60, 104, 520, 400, fill="#FBFBF7", stroke=SEVE, sw=1.2, rx=6, dash="7 5")
    sh.txt(320, 124, "VOYANTS", size=6.8, fill=SEVE, weight="700", spacing="1.4")

    voyants = [
        ("DS2", "bi-colour", "POWER", SEVE,
         ["steady green: mains adapter", "steady amber: powered from USB",
          "blinking amber: limiting"]),
        ("DS3", "bleue", "LIEN USB", BLEU,
         ["off: not enumerated", "steady: enumerated, idle",
          "blinking: the measurement stream is live"]),
        ("DS4", "rouge", "FAULT", CUIVRE,
         ["overcurrent or short circuit", "saturation persistante",
          "self-test failed"]),
        ("DS1", "RVB", "MEASURE", OR,
         ["vert : acquisition normale", "ambre : saturation",
          "blue: no electrode", "brightness = signal level"]),
    ]
    for i, (ref, genre, titre, couleur, lignes) in enumerate(voyants):
        y = 150 + i * 84
        sh.circle(104, y + 22, 11, fill=couleur, stroke=INK, sw=1.4, op=0.85)
        sh.txt(104, y + 52, ref, size=6.2, fill=INK, family=MONO)
        sh.txt(140, y + 14, titre, size=7.2, fill=couleur, weight="700",
               anchor="start", spacing="0.8")
        sh.txt(140, y + 28, f"LED {genre}", size=5.8, fill=GRIS, anchor="start")
        for k, ligne in enumerate(lignes):
            sh.txt(290, y + 12 + k * 15, ligne, size=6, fill=INK, anchor="start")

    sh.txt(320, 486, "each indicator sits behind 1 kΩ (R70 to R73): 2 mA, readable without dazzling in the dark", size=6, fill=GRIS)

    # ---- afficheur ---------------------------------------------------------
    sh.rect(620, 104, 690, 380, fill="#F2F6FC", stroke=BLEU, sw=1.2, rx=6,
            dash="7 5")
    sh.txt(965, 124, "OLED DISPLAY 128 × 64 — I²C BUS", size=6.8, fill=BLEU,
           weight="700", spacing="1")

    ic_box(sh, 650, 150, 150, 70, "DS5", "SSD1306", "0,96 pouce")
    netflag(sh, 650, 250, "SDA", side="out", color=BLEU, w=60)
    netflag(sh, 650, 285, "SCL", side="out", color=BLEU, w=60)
    sh.wire((710, 250), (760, 250), (760, 220), stroke=BLEU, sw=1.2)
    sh.wire((710, 285), (780, 285), (780, 220), stroke=BLEU, sw=1.2)
    sh.txt(725, 330, "adresse 0x3C · 3,3 V", size=6, fill=GRIS)

    # a mock-up of the screen
    ex, ey, ew, eh = 840, 160, 420, 210
    sh.rect(ex, ey, ew, eh, fill="#0A1712", stroke=INK, sw=2.0, rx=5)
    lignes_ecran = [
        ("PhytoSense One", "#E0C073", 9.4, 30),
        ("source   mains adapter", "#EAF2EC", 7.6, 58),
        ("gain     ×100  range 10 MΩ", "#EAF2EC", 7.6, 80),
        ("measure  +412.7 µV", "#7FE0A8", 9.0, 106),
        ("noise    0.63 µV rms", "#EAF2EC", 7.6, 130),
        ("power    5.03 V · 137 mA", "#9fb8ab", 7.2, 152),
        ("USB      stream live · 0 lost", "#7FE0A8", 7.2, 174),
        ("events  37 · 12.4 /min", "#EAF2EC", 7.2, 196),
    ]
    for texte, couleur, taille, dy in lignes_ecran:
        sh.txt(ex + 14, ey + dy, texte, size=taille, fill=couleur, anchor="start",
               family=MONO)
    sh.txt(ex + ew / 2, ey + eh + 20, "readable on the spot, with the computer's screen out of reach",
           size=6.2, fill=GRIS)

    sh.txt(965, 430, "A short press on the button cycles four pages:",
           size=6.4, fill=NUIT, weight="700")
    sh.txt(965, 448, "measurement · power · USB link · self-test", size=6.2,
           fill=GRIS)
    sh.txt(965, 466, "A long press places a timestamped mark.", size=6.2,
           fill=GRIS)

    # ---- bouton ------------------------------------------------------------
    ic_box(sh, 60, 520, 150, 62, "S1", "bouton", "appui bref / long")
    sh.wire((210, 551), (280, 551), stroke=INK, sw=1.4)
    netflag(sh, 280, 551, "GPIO", side="out", color=CUIVRE, w=64)

    note(sh, 360, 512, 620,
         ["The board always works attached to a computer, but that computer is sitting",
          "three metres away. The four indicators answer, on the spot, the four questions",
          "you ask kneeling in front of the tree: is it powered, is it",
          "connected, is it measuring, and is anything wrong."],
         title="WHY LOCAL INDICATORS AT ALL", color=SEVE, fill=SEVE_P)
    sh.save("carte-ihm.svg")


# =============================================================================
#  POWER TREE AND PROTECTIONS (a summary figure)
# =============================================================================
def fig_alim_arbre():
    sh = Sheet(980, 700, print_mm=125)
    sh.title("Power tree and protections",
             "Two sources, one priority, five protective barriers")

    # sources
    block(sh, 40, 110, 200, 66, "Mains adapter", "7 to 24 V · 1 A",
          fill=OR_PL, stroke=OR, sw=1.6, tsize=8)
    block(sh, 40, 230, 200, 66, "Port USB", "5 V · 500 mA",
          fill=BLEU_P, stroke=BLEU, sw=1.6, tsize=8)

    # protections voie secteur
    etapes_sec = [("Anti-inversion", "Q30 · MOS canal P"),
                  ("18 V clamp", "D30 · transil 400 W"),
                  ("Abaisseur 5,2 V", "U60 · protected")]
    for i, (t, sub) in enumerate(etapes_sec):
        block(sh, 280 + i * 190, 110, 170, 66, t, sub, fill="#fff", stroke=OR,
              sw=1.3, tsize=7.2)
        if i:
            sh.arrow(270 + i * 190, 143, 276 + i * 190, 143, color=OR, sw=1.6)
    sh.arrow(240, 143, 276, 143, color=OR, sw=1.8)

    # protections voie USB
    etapes_usb = [("Ferrite", "FB1 · 600 Ω"),
                  ("Limiteur 500 mA", "U61 · coupe en 2 µs"),
                  ("Fault signal", "to the red indicator")]
    for i, (t, sub) in enumerate(etapes_usb):
        block(sh, 280 + i * 190, 230, 170, 66, t, sub, fill="#fff", stroke=BLEU,
              sw=1.3, tsize=7.2)
        if i:
            sh.arrow(270 + i * 190, 263, 276 + i * 190, 263, color=BLEU, sw=1.6)
    sh.arrow(240, 263, 276, 263, color=BLEU, sw=1.8)

    # aiguilleur
    block(sh, 380, 350, 220, 76, "Priority selector",
          "U62 · TPS2116 · break-free", fill=SEVE_P, stroke=SEVE, sw=1.8,
          tsize=8)
    sh.arrow(470, 176, 470, 346, color=OR, sw=1.8)
    sh.arrow(520, 296, 520, 346, color=BLEU, sw=1.8)
    sh.txt(620, 372, "the mains adapter wins whenever it is present",
           size=6.2, fill=GRIS, anchor="start")
    sh.txt(620, 388, "the changeover is painless: no sample is lost",
           size=6.2, fill=GRIS, anchor="start")

    # mesure et distribution
    block(sh, 380, 450, 220, 66, "Current measurement", "U63 · INA219",
          fill="#fff", stroke=SEVE, sw=1.4, tsize=7.6)
    sh.arrow(490, 426, 490, 446, color=SEVE, sw=1.8)
    block(sh, 380, 546, 220, 62, "Resettable fuse", "F30 · 0,5 A",
          fill=CUIV_P, stroke=CUIVRE, sw=1.4, tsize=7.6)
    sh.arrow(490, 516, 490, 542, color=SEVE, sw=1.8)

    sorties = [("+3V3 digital", "U23"), ("isolated ±5 V analog", "T1, U21, U22"),
               ("Display and indicators", "2 mA chacun")]
    for i, (t, sub) in enumerate(sorties):
        block(sh, 660, 450 + i * 74, 280, 60, t, sub, fill="#fff", stroke=GRIS,
              sw=1.2, tsize=7.4)
        sh.arrow(604, 577, 656, 480 + i * 74, color=SEVE, sw=1.4)

    note(sh, 40, 620, 900,
         ["Reverse polarity, short circuit, overvoltage, overcurrent, electrostatic",
          "discharge: each of these five accidents meets a barrier before it",
          "reaches an expensive part. No fuse to replace: everything resets itself."],
         title="THE FIVE ACCIDENTS COVERED", color=CUIVRE, fill=CUIV_P)
    sh.signer()
    sh.save("carte-alim-arbre.svg")


# =============================================================================
#  DRILLING TEMPLATES — 1:1 SCALE
#
#  The absolute rule of these figures: one viewBox unit is exactly one
#  tenth of a real millimetre. The sheet is 1800 x 900 units and prints
#  180 mm wide, so any dimension measured with a ruler on the paper is the
#  true one. A 100 mm check ruler appears on every template: if it does not
#  measure 100 mm, the print was rescaled and the template is unusable.
#
# =============================================================================
UPMM = 10.0          # viewBox units per millimetre

#  Chosen enclosure: extruded aluminium 120 x 80 x 30 mm, removable panels.
FACE_L, FACE_H = 116.0, 26.0          # front and rear panels, in millimetres


def _gab(x_mm, y_mm, ox, oy):
    """Panel millimetres to viewBox units."""
    return (ox + x_mm * UPMM, oy + y_mm * UPMM)


def _percage(sh, ox, oy, x, y, diametre, repere, legende="", dessous=True):
    """Round hole: a circle at true diameter, a centre cross, a dimension.

    `dessous` puts the dimensions under the hole; when false they go above,
    which avoids overlaps where two holes sit close together.
    """
    cx, cy = _gab(x, y, ox, oy)
    r = diametre / 2.0 * UPMM
    sh.circle(cx, cy, r, fill="none", stroke=INK, sw=1.6)
    sh.line(cx - r - 22, cy, cx + r + 22, cy, stroke=CUIVRE, sw=0.9)
    sh.line(cx, cy - r - 22, cx, cy + r + 22, stroke=CUIVRE, sw=0.9)
    sh.circle(cx, cy, 1.6, fill=CUIVRE, stroke=CUIVRE, sw=0.6)
    cote = f"Ø {diametre:g}".replace(".", ",")
    if dessous:
        sh.txt(cx, cy - r - 32, repere, size=6.2, fill=SEVE, weight="700")
        sh.txt(cx, cy + r + 44, cote, size=5.8, fill=INK, family=MONO)
        if legende:
            sh.txt(cx, cy + r + 58, legende, size=5.4, fill=GRIS)
    else:
        sh.txt(cx, cy - r - 60, repere, size=6.2, fill=SEVE, weight="700")
        sh.txt(cx, cy - r - 46, cote, size=5.8, fill=INK, family=MONO)
        if legende:
            sh.txt(cx, cy - r - 32, legende, size=5.4, fill=GRIS)


def _fenetre(sh, ox, oy, x, y, larg, haut, repere, legende=""):
    """Rectangular cut-out: true outline, centre cross, dimensions."""
    cx, cy = _gab(x, y, ox, oy)
    w, h = larg * UPMM, haut * UPMM
    sh.rect(cx - w / 2, cy - h / 2, w, h, fill="none", stroke=INK, sw=1.6, rx=3)
    sh.line(cx - w / 2 - 22, cy, cx + w / 2 + 22, cy, stroke=CUIVRE, sw=0.9)
    sh.line(cx, cy - h / 2 - 22, cx, cy + h / 2 + 22, stroke=CUIVRE, sw=0.9)
    sh.txt(cx, cy - h / 2 - 32, repere, size=6.2, fill=SEVE, weight="700")
    sh.txt(cx, cy + h / 2 + 44,
           f"{larg:g} × {haut:g}".replace(".", ","), size=5.8, fill=INK,
           family=MONO)
    if legende:
        sh.txt(cx, cy + h / 2 + 58, legende, size=5.4, fill=GRIS)


def _reglette(sh, x, y, longueur_mm=100.0):
    """A check ruler: if it does not measure its stated length, do not drill."""
    L = longueur_mm * UPMM
    sh.rect(x, y, L, 26, fill="none", stroke=INK, sw=1.4)
    for i in range(int(longueur_mm) + 1):
        px = x + i * UPMM
        if i % 10 == 0:
            sh.line(px, y, px, y + 26, stroke=INK, sw=1.2)
            sh.txt(px, y + 42, str(i), size=5.4, fill=GRIS)
        elif i % 5 == 0:
            sh.line(px, y + 8, px, y + 26, stroke=INK, sw=0.9)
        else:
            sh.line(px, y + 16, px, y + 26, stroke=TRAIT, sw=0.7)
    sh.txt(x + L / 2, y - 10,
           f"CHECK RULER — THIS BAR MUST MEASURE {longueur_mm:g} mm",
           size=6.4, fill=CUIVRE, weight="700", spacing="0.8")


def _avertissement_impression(sh, x, y, w=700):
    note(sh, x, y, w,
         ["Print at 100 %, with no “fit to page”.",
          "Check the ruler with a ruler BEFORE drilling:",
          "a 4 % error shifts the last hole by 4 mm.",
          "Tape the template to the panel,",
          "mark with a centre punch, then drill in two passes:",
          "a 3 mm pilot hole, then the final size."],
         title="BEFORE YOU DRILL — READ THIS", color=CUIVRE, fill=CUIV_P)


def _cadre_face(sh, ox, oy, titre, sous_titre):
    """The panel outline, with its overall dimensions."""
    w, h = FACE_L * UPMM, FACE_H * UPMM
    sh.rect(ox, oy, w, h, fill="#FBFBF7", stroke=NUIT, sw=2.2, rx=8)
    # reference axes
    sh.line(ox, oy + h / 2, ox + w, oy + h / 2, stroke=TRAIT, sw=0.8, dash="12 6")
    sh.line(ox + w / 2, oy, ox + w / 2, oy + h, stroke=TRAIT, sw=0.8, dash="12 6")
    # cotes
    sh.line(ox, oy - 34, ox + w, oy - 34, stroke=GRIS, sw=1.0)
    sh.line(ox, oy - 40, ox, oy - 28, stroke=GRIS, sw=1.0)
    sh.line(ox + w, oy - 40, ox + w, oy - 28, stroke=GRIS, sw=1.0)
    sh.txt(ox + w / 2, oy - 42, f"{FACE_L:g} mm".replace(".", ","), size=6.2,
           fill=GRIS)
    sh.line(ox - 34, oy, ox - 34, oy + h, stroke=GRIS, sw=1.0)
    sh.txt(ox - 44, oy + h / 2 + 4, f"{FACE_H:g} mm".replace(".", ","), size=6.2,
           fill=GRIS, rot=-90)
    sh.txt(ox, oy - 62, titre, size=10, fill=NUIT, weight="700", anchor="start",
           family=SERIF)
    sh.txt(ox + w, oy - 62, sous_titre, size=6.4, fill=GRIS, anchor="end")


def _tableau_percages(sh, x, y, lignes, titre="HOLE COORDINATES"):
    """Table of dimensions, measured from the panel's bottom-left corner."""
    sh.txt(x, y, titre, size=6.8, fill=NUIT, weight="700", anchor="start",
           spacing="1.2")
    sh.txt(x, y + 16, "origin: top-left corner · X to the right, Y downward", size=5.6, fill=GRIS, anchor="start")
    entetes = ("DATUM", "X (mm)", "Y (mm)", "COTE", "DESTINATION")
    colonnes = (0, 110, 200, 290, 420)
    yy = y + 40
    for i, e in enumerate(entetes):
        sh.txt(x + colonnes[i], yy, e, size=5.6, fill=GRIS, anchor="start",
               spacing="0.6")
    sh.line(x, yy + 8, x + 900, yy + 8, stroke=TRAIT, sw=1.0)
    for k, (repere, px, py, cote, dest) in enumerate(lignes):
        ly = yy + 28 + k * 22
        if k % 2:
            sh.rect(x - 8, ly - 15, 916, 21, fill="#FAFBFA", stroke="none")
        sh.txt(x + colonnes[0], ly, repere, size=6.2, fill=SEVE, anchor="start",
               weight="700", family=MONO)
        sh.txt(x + colonnes[1], ly, f"{px:g}".replace(".", ","), size=6.2,
               fill=INK, anchor="start", family=MONO)
        sh.txt(x + colonnes[2], ly, f"{py:g}".replace(".", ","), size=6.2,
               fill=INK, anchor="start", family=MONO)
        sh.txt(x + colonnes[3], ly, cote, size=6.2, fill=INK, anchor="start",
               family=MONO)
        sh.txt(x + colonnes[4], ly, dest, size=6.2, fill=GRIS, anchor="start")


# -----------------------------------------------------------------------------
def gab_face_avant():
    """1:1 drilling template for the front panel."""
    sh = Sheet(1800, 900, print_mm=180)
    ox, oy = 180, 150
    _cadre_face(sh, ox, oy, "Front panel — a 1:1 template",
                "aluminium enclosure 120 × 80 × 30 mm")

    _percage(sh, ox, oy, 14.0, 13.0, 6.5, "J1", "electrode A")
    _percage(sh, ox, oy, 30.0, 13.0, 6.5, "J2", "electrode B")
    _fenetre(sh, ox, oy, 58.0, 13.0, 25.0, 14.0, "DS5", "OLED display")
    _percage(sh, ox, oy, 78.0, 6.5, 3.2, "DS2", "power", dessous=False)
    _percage(sh, ox, oy, 86.0, 6.5, 3.2, "DS3", "USB", dessous=False)
    _percage(sh, ox, oy, 94.0, 6.5, 3.2, "DS4", "fault", dessous=False)
    _percage(sh, ox, oy, 86.0, 18.5, 7.0, "S1", "bouton")
    _percage(sh, ox, oy, 108.0, 13.0, 3.2, "M1", "fixation")

    _reglette(sh, ox, oy + FACE_H * UPMM + 90)
    _tableau_percages(sh, ox, oy + FACE_H * UPMM + 200, [
        ("J1", 14, 13, "Ø 6,5", "3.5 mm jack socket — electrode A"),
        ("J2", 30, 13, "Ø 6,5", "3.5 mm jack socket — electrode B"),
        ("DS5", 58, 13, "25 × 14", "window for the OLED display"),
        ("DS2", 78, 6.5, "Ø 3,2", "power indicator, two-color"),
        ("DS3", 86, 6.5, "Ø 3,2", "voyant de lien USB, bleu"),
        ("DS4", 94, 6.5, "Ø 3,2", "fault indicator, red"),
        ("S1", 86, 18.5, "Ø 7,0", "bouton-poussoir"),
        ("M1", 108, 13, "Ø 3,2", "panel retaining screw"),
    ])
    _avertissement_impression(sh, 1010, 560)
    sh.txt(1310, 852, f"{AUTEUR} · {SITE} · revision B", size=5.8, fill=GRIS)
    sh.save("gabarit-face-avant.svg")


def gab_face_arriere():
    """1:1 drilling template for the rear panel."""
    sh = Sheet(1800, 900, print_mm=180)
    ox, oy = 180, 150
    _cadre_face(sh, ox, oy, "Rear panel — 1:1 template",
                "aluminium enclosure 120 × 80 × 30 mm")

    _fenetre(sh, ox, oy, 20.0, 13.0, 10.0, 5.0, "J20", "USB-C")
    _percage(sh, ox, oy, 44.0, 13.0, 8.0, "J30", "mains adapter")
    _percage(sh, ox, oy, 66.0, 13.0, 6.5, "J21", "MIDI TRS")
    _percage(sh, ox, oy, 88.0, 13.0, 4.2, "GND", "chassis ground")
    _percage(sh, ox, oy, 108.0, 13.0, 3.2, "M2", "fixation")

    _reglette(sh, ox, oy + FACE_H * UPMM + 90)
    _tableau_percages(sh, ox, oy + FACE_H * UPMM + 200, [
        ("J20", 20, 13, "10 × 5", "USB-C socket — a rectangular cut-out"),
        ("J30", 44, 13, "Ø 8,0", "2.1 mm power jack"),
        ("J21", 66, 13, "Ø 6,5", "MIDI TRS type A output"),
        ("GND", 88, 13, "Ø 4,2", "chassis ground stud, M4 screw"),
        ("M2", 108, 13, "Ø 3,2", "panel retaining screw"),
    ])
    note(sh, 1010, 420, 700,
         ["The ground stud connects the enclosure to the floating analog ground,",
          "and to that alone. Connecting it to the USB ground would restore the loop",
          "the whole design exists to remove: it is the commonest assembly",
          "mistake, and it cannot be seen — it is heard, at 50 Hz."],
         title="THE GROUND STUD", color=CUIVRE, fill=CUIV_P)
    _avertissement_impression(sh, 1010, 640)
    sh.txt(1310, 868, f"{AUTEUR} · {SITE} · revision B", size=5.8, fill=GRIS)
    sh.save("gabarit-face-arriere.svg")


def gab_carte():
    """1:1 template for drilling the base, and the mechanical layout."""
    sh = Sheet(1800, 1340, print_mm=180)
    ox, oy = 180, 150
    w, h = CARTE_L * UPMM, CARTE_H * UPMM
    sh.rect(ox, oy, w, h, fill="#F7F9F7", stroke=SEVE, sw=2.2, rx=6, dash="10 6")
    sh.txt(ox, oy - 52, "Enclosure base — 1:1 template", size=10, fill=NUIT,
           weight="700", anchor="start", family=SERIF)
    sh.txt(ox + w, oy - 52, "board outline, 100 × 60 mm", size=6.4,
           fill=GRIS, anchor="end")

    # connector footprints, drawn first so they stay under the holes
    for x, y, lw, lh, nom in ((6, 12, 12, 12, "J1"), (6, 30, 12, 12, "J2"),
                              (93, 20, 9, 7.4, "J20"), (93, 44, 6, 6, "J21"),
                              (38, 27, 4, 34, "J10"), (30, 46, 14, 10, "T1")):
        cx, cy = _gab(x, y, ox, oy)
        sh.rect(cx - lw * UPMM / 2, cy - lh * UPMM / 2, lw * UPMM, lh * UPMM,
                fill="#EEF2F0", stroke=GRIS, sw=1.0, dash="4 3")
        sh.txt(cx, cy + 4, nom, size=5.6, fill=GRIS)

    _percage(sh, ox, oy, 4, 4, 3.2, "F1", "entretoise", dessous=False)
    _percage(sh, ox, oy, 96, 4, 3.2, "F2", "entretoise", dessous=False)
    _percage(sh, ox, oy, 4, 56, 3.2, "F3", "entretoise")
    _percage(sh, ox, oy, 96, 56, 3.2, "F4", "entretoise")

    sh.txt(ox + w / 2, oy + h + 96,
           "the grey rectangles are the footprints of the connectors and the tall parts: check their clearance before drilling",
           size=6, fill=GRIS)

    _reglette(sh, ox, oy + h + 140)

    _tableau_percages(sh, ox, oy + h + 250, [
        ("F1", 4, 4, "Ø 3,2", "M3 spacer, 6 mm tall, PTFE — analog side"),
        ("F2", 96, 4, "Ø 3,2", "M3 spacer, 6 mm tall, PTFE — isolated"),
        ("F3", 4, 56, "Ø 3,2", "M3 spacer, 6 mm tall, PTFE — analog side"),
        ("F4", 96, 56, "Ø 3,2", "M3 spacer, 6 mm tall, PTFE — isolated"),
    ], titre="HOLES IN THE BASE — origin: the board's top-left corner")

    note(sh, 180, 1140, 760,
         ["PTFE spacers, never nylon: nylon takes up moisture and conducts",
          "quite enough, across its surface, to degrade a 10¹⁵ ohm measurement.",
          "Only F1 and F3, on the analog side, touch a ground plane; F2 and F4 stay",
          "isolated, on pain of closing the loop that the slot opened."],
         title="THE SPACERS ARE NOT NEUTRAL", color=CUIVRE, fill=CUIV_P)
    _avertissement_impression(sh, 1000, 1140, 740)
    sh.txt(900, 1320, f"{AUTEUR} · {SITE} · revision B", size=5.8, fill=GRIS)
    sh.save("gabarit-carte.svg")


# =============================================================================
#  ENTRY POINT  (must stay at the end of the file: insert figures ABOVE)
# =============================================================================

# =============================================================================
#  OVERALL WIRING — PLANT, ENCLOSURE, COMPUTER, POWER
# =============================================================================
def fig_raccordement():
    """Overview: what connects to what, and where the current comes from."""
    sh = Sheet(980, 976, print_mm=125)
    sh.title("Raccordement d'ensemble",
             "The laptop is always required; only the power has two sources")

    # ---- the three elements of the chain -----------------------------------
    py = 128
    bp = block(sh, 30, py, 250, 132, "THE PLANT", "a tree, a shrub or a potted plant",
               ["2 measurement electrodes", "1 earth electrode", "in the substrate"],
               fill=SEVE_P, stroke=SEVE, sw=1.8)
    bb = block(sh, 366, py, 250, 132, "THE ENCLOSURE", "PhytoSense One",
               ["conditionnement analogique", "conversion 24 bits", "horodatage"],
               fill="#fff", stroke=NUIT, sw=2.0)
    bo = block(sh, 700, py, 250, 132, "L'ORDINATEUR", "portable — indispensable",
               ["board settings", "enregistrement", "analysis and listening"],
               fill=BLEU_P, stroke=BLEU, sw=1.8)

    # ---- links: arrows between the blocks, captions BELOW ------------------
    sh.arrow(bp["r"][0] + 4, bp["r"][1], bb["l"][0] - 6, bb["l"][1], color=SEVE, sw=2.4)
    sh.arrow(bb["r"][0] + 4, bb["r"][1], bo["l"][0] - 6, bo["l"][1], color=BLEU, sw=2.4)

    ly = py + 158
    for x, col, titre, l1, l2 in (
            (200, SEVE, "THE MEASUREMENT LINK", "shielded RG-174 cable · 2 m at most",
             "3.5 mm TRS jack on J1 — see the next figure"),
            (760, BLEU, "LIAISON DE COMMANDE", "a single USB-C cable",
             "measurement data and 5 V in the same lead")):
        sh.txt(x, ly, titre, size=6.4, fill=col, weight="700", spacing="0.8")
        sh.txt(x, ly + 18, l1, size=6.0, fill=INK)
        sh.txt(x, ly + 34, l2, size=5.9, fill=GRIS)

    # ---- banner: where the power comes from --------------------------------
    ey = 378
    sh.rect(30, ey, 920, 266, fill=OR_PL, stroke=OR, sw=1.4, rx=10, dash="8 5")
    sh.txt(490, ey + 26, "WHERE THE POWER COMES FROM — YOUR CHOICE, AND NO BREAK ON CHANGEOVER",
           size=6.6, fill=OR, weight="700", spacing="1.2")

    opts = [
        ("A · OVER USB", "the simplest",
         ["A single cable for everything.", "500 mA available,", "137 mA drawn.",
          "It drains the laptop battery", "over a long session."], SEVE),
        ("B · BLOC EXTERNE", "it takes priority",
         ["Mains adapter 7 to 24 V", "on socket J30.", "Relieves the laptop and",
          "keeps its noisy 5 V away", "from the measurement chain."], CUIVRE),
        ("C · ACCUMULATEUR", "far from any socket",
         ["Li-Po 3,7 V 2 000 mAh", "and its charging module.", "Draws nothing from the laptop",
          "nor from the mains — useful", "for a session in the forest."], BLEU),
    ]
    for i, (titre, sous, lignes, col) in enumerate(opts):
        x = 58 + i * 300
        block(sh, x, ey + 46, 264, 192, titre, sous, lignes, fill="#fff",
              stroke=col, sw=1.7, tsize=7.6)

    # converging on the enclosure: a single arrow, in the free corridor
    sh.arrow(490, ey - 6, 490, py + 142, color=OR, sw=2.6, marker="ahv")

    note(sh, 30, 674, 920,
         ["All three sources may be present at once. The U62 selector gives priority",
          "to the external adapter, then to USB, and switches between them in under twenty",
          "microseconds: you can unplug the computer from the mains mid-session without losing a",
          "sample. None of the three does away with the computer, which remains the only",
          "recipient of the measurement stream."],
         title="RULE — THE POWER IS DOUBLE, THE LINK IS NOT",
         color=OR, fill=OR_PL)

    note(sh, 30, 842, 920,
         ["Never connect anything to the mains but a CE-marked power supply, double-insulated",
          "and at safety extra-low voltage. No part of the board is designed for mains",
          "voltage, and none should be."],
         title="SAFETY", color=CUIVRE, fill=CUIV_P)

    sh.signer()
    sh.save("raccordement-ensemble.svg")


# =============================================================================
#  DETAILED WIRING — PLANT / TREE TO THE ENCLOSURE
# =============================================================================
def fig_electrodes():
    """Wiring in detail: where to place, with what, and with which cable."""
    sh = Sheet(980, 1060, print_mm=125)
    sh.title("Wiring the electrodes",
             "Where to place them, with what, and with which cable")

    # =====================================================================
    #  PANEL A — plant side
    # =====================================================================
    sh.rect(30, 110, 440, 510, fill=SEVE_P, stroke=SEVE, sw=1.4, rx=10, dash="8 5")
    sh.txt(250, 136, "PLANT SIDE", size=6.6, fill=SEVE, weight="700", spacing="1.2")

    # tronc, ramure, feuillage
    sh.rect(226, 300, 44, 190, fill="#D8CBB4", stroke="#9C8A6E", sw=1.4, rx=4)
    sh.path("M248 302 C 248 250, 186 248, 186 214", stroke="#9C8A6E", sw=3.0)
    sh.path("M248 302 C 248 254, 316 252, 316 220", stroke="#9C8A6E", sw=3.0)
    sh.circle(186, 200, 28, fill=SEVE_C, stroke=SEVE, sw=1.4)
    sh.circle(316, 206, 28, fill=SEVE_C, stroke=SEVE, sw=1.4)
    sh.rect(126, 490, 244, 30, fill="#C7B79A", stroke="#9C8A6E", sw=1.2, rx=3)

    # contact points, marked with a short pad
    def contact(cx, cy, ref, col, tx, ty, anchor="middle"):
        sh.circle(cx, cy, 8.5, fill=col, stroke="#fff", sw=1.8)
        sh.line(cx, cy, tx, ty + 6, stroke=col, sw=1.0, dash="4 3")
        sh.txt(tx, ty, ref, size=6.8, fill=col, weight="700", anchor=anchor)

    contact(186, 200, "E1", CUIVRE, 186, 158)
    contact(248, 396, "E2", BLEU, 306, 388, "start")
    contact(248, 505, "E3", NUIT, 306, 497, "start")

    # key to the three contacts, at the foot of the panel
    leg = [(CUIVRE, "E1", "measurement — under a leaf"),
           (BLEU,   "E2", "reference — trunk, 10 to 30 cm lower"),
           (NUIT,   "E3", "earth — 316L stainless rod in the substrate")]
    for i, (col, ref, txt) in enumerate(leg):
        y = 552 + i * 24
        sh.circle(58, y - 4, 6, fill=col, stroke="none", sw=0)
        sh.txt(74, y, ref, size=6.2, fill=col, weight="700", anchor="start")
        sh.txt(104, y, txt, size=5.8, fill=INK, anchor="start")

    # =====================================================================
    #  PANEL B — the cable, stripped
    # =====================================================================
    sh.rect(500, 110, 450, 250, fill="#fff", stroke=NUIT, sw=1.6, rx=10)
    sh.txt(725, 136, "THE CABLE", size=6.6, fill=NUIT, weight="700", spacing="1.2")

    yc = 262
    sh.rect(522, yc - 19, 160, 38, fill="#D7D7C6", stroke=INK, sw=1.3, rx=4)
    sh.rect(682, yc - 13, 68, 26, fill=SEVE_C, stroke=SEVE, sw=1.3, rx=3)
    sh.rect(750, yc - 8, 52, 16, fill=IVOIRE, stroke=INK, sw=1.1, rx=2)
    sh.line(802, yc, 862, yc, stroke=CUIVRE, sw=4.0)

    # markers: two above, two below, never on the same line
    for x, ylab, lab, col, sens in ((602, yc + 52, "outer jacket", GRIS, 1),
                                    (716, yc - 38, "braid → RING (guard)", SEVE, -1),
                                    (776, yc + 52, "dielectric", GRIS, 1),
                                    (832, yc - 62, "core → TIP (measurement)", CUIVRE, -1)):
        sh.line(x, yc + sens * 22, x, ylab - sens * 12, stroke=col, sw=0.9, dash="3 3")
        sh.txt(x, ylab, lab, size=6.0, fill=col, weight="700")

    sh.txt(725, 336, "RG-174 · Belden 8216 · 2 m at most", size=6.0, fill=INK,
           family=MONO)

    # =====================================================================
    #  PANEL C — the connector
    # =====================================================================
    sh.rect(500, 384, 450, 236, fill="#fff", stroke=OR, sw=1.6, rx=10)
    sh.txt(725, 410, "THE CONNECTOR — J1 · 3.5 mm TRS JACK", size=6.6, fill=OR,
           weight="700", spacing="1.0")

    jx, jy = 548, 442
    sh.rect(jx, jy, 300, 30, fill="#E8E4D6", stroke=INK, sw=1.4, rx=4)
    for x0, x1, col in ((jx + 4, jx + 60, CUIVRE), (jx + 68, jx + 146, SEVE),
                        (jx + 154, jx + 296, BLEU)):
        sh.rect(x0, jy + 4, x1 - x0, 22, fill=col, stroke="none", sw=0, rx=2)
    sh.circle(jx + 300, jy + 15, 15, fill="#E8E4D6", stroke=INK, sw=1.4)

    broches = [(CUIVRE, "T · tip", "E1 — measurement electrode"),
               (SEVE,   "R · ring",  "guard and cable braid"),
               (BLEU,   "S · corps",  "E2 — reference electrode")]
    for i, (col, nom, role) in enumerate(broches):
        y = 510 + i * 26
        sh.rect(jx, y - 11, 16, 14, fill=col, stroke="none", sw=0, rx=2)
        sh.txt(jx + 26, y, nom, size=6.2, fill=col, weight="700", anchor="start")
        sh.txt(jx + 128, y, role, size=6.0, fill=INK, anchor="start")

    sh.txt(725, 600, "The braid goes to the ring, never to the sleeve.",
           size=6.2, fill=CUIVRE, weight="700")

    # =====================================================================
    #  CONSEILS
    # =====================================================================
    note(sh, 30, 652, 920,
         ["Adhesive Ag/AgCl ECG electrodes: the most stable contact there is, good for several",
          "hours without drift. A dab of chloride-free conductive gel extends it further.",
          "On a thick leaf or on bark, a copper-jawed crocodile clip lined with a damp sponge.",
          "Two electrodes 10 to 30 cm apart on the same individual; never across two plants.",
          "A cable of two metres at most, strain-relieved twenty centimetres from the contact."],
         title="WHAT TO DO", color=SEVE, fill=SEVE_P)

    note(sh, 30, 832, 920,
         ["No kitchen foil: it oxidises within hours and makes a parasitic cell.",
          "No needle driven into the trunk: a pointless wound, and the signal gains nothing.",
          "No unshielded cable and no extension: every bare metre adds mains hum.",
          "No braid tied to the enclosure ground: it is the commonest mistake, and it throws",
          "away the whole benefit of the electrometer stage at a stroke."],
         title="WHAT NOT TO DO", color=CUIVRE, fill=CUIV_P)

    sh.signer()
    sh.save("raccordement-electrodes.svg")



# =============================================================================
#  LEAF / ROOT WIRING — and the substrate electrode
# =============================================================================
def fig_feuille_racine():
    sh = Sheet(980, 1310, print_mm=125)
    sh.title("Connecting a leaf and a root",
             "The commonest arrangement — and the choice of substrate electrode")

    # =====================================================================
    #  A — LE MONTAGE, EN COUPE
    # =====================================================================
    sh.rect(30, 108, 470, 560, fill=SEVE_P, stroke=SEVE, sw=1.4, rx=10, dash="8 5")
    sh.txt(265, 134, "THE ARRANGEMENT, IN SECTION", size=6.6, fill=SEVE, weight="700",
           spacing="1.2")

    #  the pot, in section
    sh.path("M150 430 L 178 620 L 352 620 L 380 430 Z", fill="#E4D9C4",
            stroke="#9C8A6E", sw=1.6)
    sh.path("M150 430 L 380 430", stroke="#9C8A6E", sw=1.6)
    #  the substrate
    sh.path("M158 448 L 182 606 L 348 606 L 372 448 Z", fill="#C2A882",
            stroke="none", sw=0)
    #  the stem and the leaves
    sh.path("M265 430 L 265 250", stroke=SEVE, sw=4.0)
    sh.path("M265 300 C 225 286, 205 262, 202 236", stroke=SEVE, sw=2.6)
    sh.path("M265 336 C 305 322, 326 300, 330 274", stroke=SEVE, sw=2.6)
    for cx, cy, rot in ((196, 228, -28), (336, 266, 26)):
        sh.add(f'<g transform="rotate({rot},{cx},{cy})">'
               f'<ellipse cx="{cx}" cy="{cy}" rx="34" ry="17" fill="{SEVE_C}" '
               f'stroke="{SEVE}" stroke-width="1.4"/></g>')
    #  the roots
    for dx in (-60, -26, 0, 26, 60):
        sh.path(f"M265 432 C {265+dx*0.4} 470, {265+dx} 520, {265+dx*1.1} 588",
                stroke="#A58A5E", sw=1.6)

    #  E1 — on the leaf
    sh.circle(196, 228, 9, fill=CUIVRE, stroke="#fff", sw=2.0)
    sh.line(196, 228, 120, 192, stroke=CUIVRE, sw=1.0, dash="4 3")
    sh.txt(52, 182, "E1", size=7.0, fill=CUIVRE, weight="700", anchor="start")
    sh.txt(52, 196, "pastille Ag/AgCl", size=5.6, fill=INK, anchor="start")
    sh.txt(52, 208, "under the leaf", size=5.6, fill=GRIS, anchor="start")

    #  E2 — in the substrate
    sh.rect(316, 452, 7, 118, fill="#BFC4C8", stroke=INK, sw=1.2, rx=2)
    sh.circle(319, 452, 8, fill=NUIT, stroke="#fff", sw=2.0)
    sh.line(319, 452, 416, 396, stroke=NUIT, sw=1.0, dash="4 3")
    sh.txt(484, 384, "E2", size=7.0, fill=NUIT, weight="700", anchor="end")
    sh.txt(484, 398, "tige inox 316L", size=5.6, fill=INK, anchor="end")
    sh.txt(484, 410, "3 to 5 cm deep", size=5.6, fill=GRIS, anchor="end")

    #  the dimensions
    sh.line(265, 640, 319, 640, stroke=BLEU, sw=1.0)
    sh.txt(292, 656, "≥ 5 cm from the stem", size=5.8, fill=BLEU)
    sh.line(330, 452, 330, 570, stroke=BLEU, sw=1.0, dash="3 3")
    sh.txt(352, 516, "3–5 cm", size=5.8, fill=BLEU, anchor="start")

    #  what is being measured
    note(sh, 30, 690, 920,
         ["The measured voltage is that of the path leaf → stem → roots → substrate → electrode.",
          "So it does not say “the leaf”: it says plant + substrate + contacts, as a whole.",
          "Watering shifts it as much as a change in the plant does — that is the arrangement's limit,",
          "and it belongs in the session notebook."],
         title="WHAT THIS CIRCUIT MEASURES", color=BLEU, fill=BLEU_P)

    # =====================================================================
#  B — THE SUBSTRATE ELECTRODE: WHAT TO PUT IN THE SOIL
    # =====================================================================
    sh.rect(516, 108, 434, 560, fill="#fff", stroke=NUIT, sw=1.6, rx=10)
    sh.txt(733, 134, "WHAT TO PUT IN THE SOIL", size=6.6, fill=NUIT,
           weight="700", spacing="1.2")

    lignes = [
        (SEVE,   "Inox 316L", "tige ø 4–6 mm, 60–100 mm",
         "The default choice: stable, inert, indestructible.", True),
        (SEVE,   "Graphite", "a ø 5 mm lead, or charcoal",
         "Barely polarisable, no metal ions. Fragile.", True),
        (OR,     "Ag/AgCl + pont salin", "agar 3 % + KCl 3 mol/L",
         "The laboratory reference: minimal drift.", True),
        (CUIVRE, "Laiton, cuivre", "—",
         "A galvanic cell with E1, and toxic to the roots.", False),
        (CUIVRE, "Galvanised steel", "—",
         "The zinc dissolves: a huge and growing offset.", False),
        (CUIVRE, "Aluminium", "—",
         "It oxidizes within hours; the measurement is unstable.", False),
    ]
    y = 170
    for col, nom, format_, texte, bon in lignes:
        sh.circle(546, y - 4, 7, fill=(SEVE if bon else CUIVRE), stroke="none", sw=0)
        sh.txt(546, y - 1, "✓" if bon else "✗", size=6.4, fill="#fff", weight="700")
        sh.txt(566, y - 6, nom, size=6.6, fill=col, weight="700", anchor="start")
        if format_ != "—":
            sh.txt(566, y + 6, format_, size=5.6, fill=GRIS, anchor="start",
                   family=MONO)
        sh.txt(566, y + (18 if format_ != "—" else 8), texte, size=5.8, fill=INK,
               anchor="start")
        y += 62

    #  the salt bridge in detail
    sh.rect(540, 548, 386, 104, fill=OR_PL, stroke=OR, sw=1.3, rx=6)
    sh.txt(733, 570, "THE SALT BRIDGE, IN TWO LINES", size=6.0, fill=OR,
           weight="700", spacing="0.8")
    sh.rect(566, 584, 16, 54, fill="#EDE7D4", stroke=INK, sw=1.2, rx=3)
    sh.rect(568, 592, 12, 44, fill=BLEU_P, stroke="none", sw=0)
    sh.line(574, 584, 574, 566, stroke="#BFC4C8", sw=3.0)
    sh.txt(596, 596, "a tube filled with salted agar,", size=5.6, fill=INK, anchor="start")
    sh.txt(596, 610, "a chlorided silver wire inside,", size=5.6, fill=INK, anchor="start")
    sh.txt(596, 624, "only its end touches the soil.", size=5.6, fill=INK, anchor="start")
    sh.txt(596, 640, "No metal touches the roots.", size=5.6, fill=SEVE,
           anchor="start", weight="700")

    # =====================================================================
#  C — THE RULE THAT MATTERS
    # =====================================================================
    note(sh, 30, 852, 920,
         ["THE SAME METAL AT BOTH ENDS. Two different metals in a damp medium make a cell:",
          "you then measure its voltage — a few tens of millivolts — and its drift with humidity,",
          "far more than the plant does. If E1 is an Ag/AgCl pad, the best E2 is a salt bridge;",
          "failing that, stainless steel at both ends. The baseline removes the constant offset, never its drift.",
          "",
          "DAMP SUBSTRATE, never waterlogged and never dry: dry, the impedance rises and the noise with it.",
          "A few drops of water before the session are enough — no salt water, which burns the roots.",
          "",
          "THE SAME SPOT FROM ONE SESSION TO THE NEXT if you mean to compare: note the depth, the distance",
          "from the stem and which leaf was chosen. Without that, two sessions do not compare."],
         title="THREE RULES, AND NOTHING MORE", color=SEVE, fill=SEVE_P)

    note(sh, 30, 1146, 920,
         ["Never drive the electrode into the trunk or into a root: the wound does not close",
          "and the signal gains nothing. Never connect the substrate electrode to mains earth",
          "— nor to the enclosure ground. Never use liquid fertiliser just before a",
          "session: the conductivity changes for hours and masks everything else."],
         title="WHAT NOT TO DO", color=CUIVRE, fill=CUIV_P)

    sh.signer()
    sh.save("raccordement-feuille-racine.svg")


# =============================================================================
#  THE SIX DESCRIPTORS — what each view shows
# =============================================================================
def _bruit(i, graine=7):
    """Deterministic pseudo-randomness: the figure must be bit-reproducible."""
    x = math.sin((i + 1) * 12.9898 + graine * 78.233) * 43758.5453
    return (x - math.floor(x)) * 2.0 - 1.0


def _mini_cadre(sh, x, y, w, h, titre, verdict, couleur=SEVE):
    sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#fff" '
           f'stroke="{TRAIT}" stroke-width="1.2"/>')
    sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="21" rx="5" '
           f'fill="{couleur}" opacity="0.14"/>')
    sh.txt(x + 10, y + 15, titre, size=7.0, fill=couleur, anchor="start",
           weight="700")
    #  Thirty-two characters fit across a thumbnail: beyond that the line
    #  overruns the frame, which only shows up in print.
    for k, ligne in enumerate(verdict):
        sh.txt(x + 10, y + h - 14 - (len(verdict) - 1 - k) * 12, ligne,
               size=5.6, fill=GRIS, anchor="start")
    return (x + 12, y + 30, w - 24, h - 48 - 12 * len(verdict))


def _courbe(sh, aire, valeurs, couleur=SEVE, sw=1.5, remplir=False):
    x0, y0, w, h = aire
    n = len(valeurs)
    lo, hi = min(valeurs), max(valeurs)
    if hi - lo < 1e-9:
        hi = lo + 1e-9
    pts = [(x0 + w * i / (n - 1), y0 + h * (1.0 - (v - lo) / (hi - lo)))
           for i, v in enumerate(valeurs)]
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    if remplir:
        sh.path(d + f" L {x0 + w:.1f},{y0 + h:.1f} L {x0:.1f},{y0 + h:.1f} Z",
                fill=couleur, stroke="none")
        sh.add(f'<path d="{d}" fill="none" stroke="{couleur}" '
               f'stroke-width="{sw}" opacity="0.9"/>')
    else:
        sh.path(d, stroke=couleur, sw=sw)


def fig_descripteurs():
    sh = Sheet(980, 706, print_mm=125)
    sh.title("Six views of the same signal",
             "The same minute of recording, seen through six tools — and what each one lets you say")

    L, H = 296, 188
    X = [30, 342, 654]
    Y = [72, 292]

    # --- 1. domaine temporel ------------------------------------------------
    aire = _mini_cadre(sh, X[0], Y[0], L, H, "Forme d'onde",
                       ["Nothing is computed here,",
                        "so nothing is lost there."], SEVE)
    temporel = [0.6 * math.sin(i / 34.0) + 0.12 * _bruit(i)
                + (1.6 * math.exp(-((i - 108) / 9.0) ** 2))
                for i in range(160)]
    _courbe(sh, aire, temporel, SEVE, 1.4)

    # --- 2. frequency domain -------------------------------------------------
    aire = _mini_cadre(sh, X[1], Y[0], L, H, "Spectre (FFT)",
                       ["The periodicities, and the mains.",
                        "Assumes the signal is stationary:",
                        "it never is for long."], BLEU)
    spectre = []
    for i in range(160):
        f = 0.02 * (i + 1)
        v = 1.0 / (f ** 0.8) + 0.25 * abs(_bruit(i, 3))
        if 96 <= i <= 100:                              # the mains line
            v += 9.0 * math.exp(-((i - 98) / 1.1) ** 2)
        spectre.append(math.log10(v + 0.05))
    _courbe(sh, aire, spectre, BLEU, 1.3)
    sh.txt(aire[0] + aire[2] * 0.62, aire[1] + 10, "50 Hz", size=5.6,
           fill=CUIVRE, anchor="start")

    # --- 3. ondelettes ------------------------------------------------------
    aire = _mini_cadre(sh, X[2], Y[0], L, H, "Ondelettes (scalogramme)",
                       ["Locates in time what the",
                        "FFT merely averages.",
                        "The best suited to this signal."], OR)
    x0, y0, w, h = aire
    x0 += 26                                          # gutter for the markers
    w -= 26
    nc, nl = 26, 10
    for c in range(nc):
        for l in range(nl):
            #  A brief burst high up, a slow floor below.
            e = (1.15 * math.exp(-(((c - 17) / 2.4) ** 2 + ((l - 2.5) / 1.7) ** 2))
                 + 0.75 * math.exp(-(((l - 7.5) / 2.2) ** 2)) * (0.5 + 0.4 * math.sin(c / 3.0))
                 + 0.08 * abs(_bruit(c * nl + l, 5)))
            o = max(0.0, min(e, 1.0))
            couleur = OR if o > 0.45 else SEVE
            sh.add(f'<rect x="{x0 + w * c / nc:.1f}" y="{y0 + h * l / nl:.1f}" '
                   f'width="{w / nc + 0.6:.1f}" height="{h / nl + 0.6:.1f}" '
                   f'fill="{couleur}" opacity="{o:.2f}"/>')
    sh.txt(x0 - 5, y0 + 8, "aigu", size=5.6, fill=GRIS, anchor="end")
    sh.txt(x0 - 5, y0 + h, "grave", size=5.6, fill=GRIS, anchor="end")

    # --- 4. MFCC ------------------------------------------------------------
    aire = _mini_cadre(sh, X[0], Y[1], L, H, "MFCC",
                       ["Compresses the spectrum into",
                        "quelques nombres comparables.",
                        "It compares; it measures nothing."], SEVE)
    x0, y0, w, h = aire
    for i in range(13):
        v = (1.0 / (i + 1.4)) * math.cos(i * 1.7) + 0.25 * _bruit(i, 11)
        hb = abs(v) * h * 0.46
        bx = x0 + w * i / 13 + 2
        by = y0 + h / 2 - (hb if v > 0 else 0)
        sh.add(f'<rect x="{bx:.1f}" y="{by:.1f}" width="{w / 13 - 5:.1f}" '
               f'height="{max(hb, 1.2):.1f}" fill="{SEVE if v > 0 else OR}" '
               f'opacity="0.85"/>')
    sh.wire((x0, y0 + h / 2), (x0 + w, y0 + h / 2), stroke=TRAIT, sw=1.0)
    sh.txt(x0 + w, y0 + 10, "c0 … c12", size=5.6, fill=GRIS, anchor="end")

    # --- 5. LPC -------------------------------------------------------------
    aire = _mini_cadre(sh, X[1], Y[1], L, H, "Linear prediction (LPC)",
                       ["Envelope and resonances of the",
                        "measurement system. Not of the",
                        "formants : aucun conduit vocal."], CUIVRE)
    brut, env = [], []
    for i in range(160):
        e = (1.4 * math.exp(-((i - 38) / 16.0) ** 2)
             + 1.0 * math.exp(-((i - 96) / 22.0) ** 2) + 0.25)
        env.append(e)
        brut.append(e + 0.22 * _bruit(i, 17))
    _courbe(sh, aire, brut, TRAIT, 1.0)
    _courbe(sh, aire, env, CUIVRE, 1.8)
    x0, y0, w, h = aire
    for i in (38, 96):
        sh.add(f'<line x1="{x0 + w * i / 160:.1f}" y1="{y0}" '
               f'x2="{x0 + w * i / 160:.1f}" y2="{y0 + h}" stroke="{CUIVRE}" '
               f'stroke-width="0.9" stroke-dasharray="3,3" opacity="0.6"/>')

    # --- 6. cepstre ---------------------------------------------------------
    aire = _mini_cadre(sh, X[2], Y[1], L, H, "Cepstre",
                       ["Reveals the slow periodicities",
                        "that a background drift hides.",
                        "The abscissa is a quefrency."], BLEU)
    cep = [0.12 * _bruit(i, 23) + 1.5 * math.exp(-((i - 104) / 2.6) ** 2)
           + 0.55 * math.exp(-((i - 52) / 2.2) ** 2) for i in range(160)]
    _courbe(sh, aire, cep, BLEU, 1.3)
    x0, y0, w, h = aire
    sh.txt(x0 + w * 104 / 160, y0 + 8, "detected period", size=5.6,
           fill=BLEU, anchor="middle")

    note(sh, 30, 508, 920,
         ["None of these views decodes anything: they describe the shape of the",
          "signal, more finely than a curve does. The constants of the speech tools — the width of the",
          "windows, Mel bank edges, prediction order — are transposed from the actual",
          "sample rate, five decades below the human voice: one frame",
          "of MFCCs lasts eight seconds here, not twenty-five milliseconds."],
         title="WHAT THESE TOOLS DO, AND WHAT THEY DO NOT",
         color=SEVE, fill=SEVE_P)
    sh.signer()
    sh.save("logiciel-descripteurs.svg")


# =============================================================================
#  VOICE MODE — words instead of notes
# =============================================================================
def fig_lexique():
    sh = Sheet(980, 836, print_mm=125)
    sh.title("From the microvolt to the word",
             "Voice mode, axis by axis — and what the user brings themselves")

    mesures = [("Direction of slope", "rise or fall"),
               ("Amplitude", "in standard deviations"),
               ("Time elapsed", "since the previous statement"),
               ("Spectral centroid", "centre of gravity, in hertz")]
    registres = [("verbe", "five words, from weak to strong"),
                 ("intensity", "l'adverbe"),
                 ("tempo", "the temporal circumstance"),
                 ("couleur", "the qualifier")]

    for i, (t, u) in enumerate(mesures):
        block(sh, 30, 104 + i * 84, 250, 62, t, u, fill="#fff", stroke=SEVE,
              sw=1.4, tsize=7.0)
    for i, (t, u) in enumerate(registres):
        block(sh, 360, 104 + i * 84, 250, 62, t, u, fill=OR_PL, stroke=OR,
              sw=1.4, tsize=7.0)
        sh.arrow(284, 135 + i * 84, 356, 135 + i * 84, color=OR, sw=1.5)
        sh.arrow(614, 135 + i * 84, 686, 306, color=OR, sw=1.1)

    #  The subject comes from no measurement: that is the point not to hide.
    block(sh, 30, 452, 250, 62, "Sujet", "chosen by the user",
          fill=CUIV_P, stroke=CUIVRE, sw=1.6, tsize=7.0)
    sh.arrow(284, 483, 356, 483, color=CUIVRE, sw=1.5)
    block(sh, 360, 452, 250, 62, "sujet", "who speaks — nothing measures it",
          fill=CUIV_P, stroke=CUIVRE, sw=1.6, tsize=7.0)
    sh.arrow(614, 483, 686, 372, color=CUIVRE, sw=1.1)

    block(sh, 690, 276, 260, 122, "Grammaire", "a template drawn at random",
          ["minimal · telegraphic", "contemplative · descriptive"],
          fill=SEVE_P, stroke=SEVE, sw=1.6, tsize=7.6)
    sh.arrow(820, 402, 820, 446, color=SEVE, sw=1.6)

    sh.add(f'<rect x="690" y="450" width="260" height="96" rx="6" fill="#fff" '
           f'stroke="{NUIT}" stroke-width="1.6"/>')
    sh.txt(820, 478, "“The leaf shivers", size=8.2, fill=NUIT,
           family=SERIF, style="italic")
    sh.txt(820, 498, "doucement, sourd »", size=8.2, fill=NUIT,
           family=SERIF, style="italic")
    sh.txt(820, 520, "σ=4,1 · pente +2e−5", size=5.2, fill=GRIS, family=MONO)
    sh.txt(820, 534, "Δt=38 s · f=0,21 Hz", size=5.2, fill=GRIS, family=MONO)
    sh.txt(820, 560, "every statement carries the values", size=5.6, fill=GRIS)
    sh.txt(820, 574, "that triggered it", size=5.6, fill=GRIS)

    note(sh, 30, 600, 920,
         ["The plant emits no words and has no language: nothing in its electrical signal",
          "corresponds to a vocabulary. This arrangement applies explicit, adjustable and",
          "recorded rules, which map a region of the descriptor space to a word chosen by",
          "the user. The word that comes out is therefore from the dictionary of whoever wrote it: it says",
          "something about the signal — intensity, direction of change, rhythm, spectral colour — and",
          "nothing of what the plant “thinks”. The dialogue that sets in is a dialogue between",
          "the user and their own reading grid; it can be fruitful, provided one knows it."],
         title="THIS IS NOT A TRANSLATION", color=CUIVRE, fill=CUIV_P)
    sh.signer()
    sh.save("logiciel-lexique.svg")



def main():
    print("• Generating the PhytoSense board figures…")
    n = 0
    for nom, fn in sorted(globals().items()):
        if callable(fn) and nom.split("_")[0] in ("fig", "pl", "gab"):
            fn()
            n += 1
    print(f"✓ {n} figures generated")


if __name__ == "__main__":
    main()
