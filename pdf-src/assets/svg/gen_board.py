#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/assets/svg/gen_board.py
#
#  Version  : 1.5.1
#  Date     : 2026-09-18
#  Éditeur  : Bretagne Namasté
#  Auteur   : Thierry GAYET <Thierry.Gayet@gmail.com>
#  Site     : https://bretagne-namaste.com
#  Contact  : contact@bretagne-namaste.com
#  Licence  : MIT — voir LICENCE.txt
#
#  SPDX-License-Identifier: MIT
#  fin de l'attribution
#  ==========================================================================

"""
Générateur des figures du hors-série « La Carte PhytoSense ».

Toutes les planches — schémas électroniques, synoptiques, implantations,
diagrammes logiciels — sont dessinées ici de façon déterministe, afin que
le document soit intégralement reproductible à partir des sources.

Usage : python3 gen_board.py
Sortie : pdf-src/assets/svg/carte-*.svg
"""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Palette (identique à book.css) -----------------------------------------
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

# Les tailles de texte sont exprimées en POINTS TYPOGRAPHIQUES RÉELS à
# l'impression. Chaque planche connaît sa largeur imprimée (print_mm) et en
# déduit le facteur unité→point : une figure pleine page (125 mm) et une
# planche paysage (212 mm) affichent donc le même corps, quelle que soit la
# taille de leur viewBox. Plancher de lisibilité : 5,6 pt.
MM_PAR_POINT = 0.352777
PT_MIN       = 5.6

# ---- Identité portée par toutes les planches --------------------------------
#  Un plan qui circule sans nom d'auteur ni adresse devient anonyme en deux
#  copies. Ces trois chaînes sont donc reprises sur le cartouche de chaque
#  feuille, sur la sérigraphie du circuit imprimé et dans la nomenclature.
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
    """Une planche SVG : liste d'éléments + utilitaires de câblage."""

    def __init__(self, w=980, h=600, bg="#FFFFFF", print_mm=125.0):
        self.w, self.h, self.bg = w, h, bg
        self.print_mm = print_mm
        # unités de viewBox pour 1 point typographique imprimé
        self.tf = MM_PAR_POINT * w / print_mm
        self.body = []

    def add(self, *chunks):
        for c in chunks:
            if c:
                self.body.append(c)
        return self

    # ---- primitives géométriques -------------------------------------------
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
        """Fil orthogonal passant par les points donnés (x, y)."""
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
        """Appose l'auteur et l'adresse en pied de planche."""
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
#  SYMBOLES NORMALISÉS (CEI 60617)
# =============================================================================
def resistor(sh, x, y, ref="", val="", horiz=True, L=92, W=34, lab_above=True,
             color=INK):
    """Résistance CEI (rectangle). (x, y) = extrémité gauche / haute du fil."""
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
    """Condensateur non polarisé."""
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
    """Masses : agnd (analogique), dgnd (numérique), iso (flottante), chassis."""
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
    """Repère d'alimentation."""
    d = -1 if up else 1
    sh.line(x, y, x, y + d * 20, stroke=color)
    sh.line(x - 19, y + d * 20, x + 19, y + d * 20, stroke=color, sw=2.4)
    sh.txt(x, y + d * 20 + (-9 if up else 25), label, size=6.5, fill=color,
           family=MONO, weight="700")
    return (x, y)


def opamp(sh, x, y, w=120, h=104, ref="", part="", inv_top=True, fill="#fff"):
    """Amplificateur opérationnel. Renvoie le dictionnaire des broches."""
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
    """Amplificateur d'instrumentation (triangle avec broches RG)."""
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
    """Connecteur : boîtier + broches."""
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


def barrier(sh, x, y0, y1, label="BARRIÈRE GALVANIQUE", color=CUIVRE):
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
             "Deux îlots d'alimentation, une barrière d'isolement, un seul câble")

    # --- îlots ---------------------------------------------------------------
    sh.rect(20, 96, 648, 616, fill="#F3F8F5", stroke=SEVE, sw=1.4, rx=10, dash="8 5")
    sh.txt(344, 120, "ÎLOT ANALOGIQUE FLOTTANT — masse AGND", size=6.6, fill=SEVE,
           weight="700", spacing="0.8")
    sh.rect(716, 96, 236, 616, fill="#EEF3FA", stroke=BLEU, sw=1.4, rx=10, dash="8 5")
    sh.txt(834, 120, "ÎLOT NUMÉRIQUE (USB)", size=6.6, fill=BLEU,
           weight="700", spacing="0.8")
    barrier(sh, 692, 108, 712)

    # --- chaîne analogique principale ---------------------------------------
    chaine = [
        ("Électrodes et câble", "Ag/AgCl · TRS blindé · garde"),
        ("Protection d'entrée", "10 kΩ · BAV199 · PTC"),
        ("Carte fille FE", "FE-Z électromètre / FE-B pont"),
        ("Gain programmable", "OPA2189 · ×1 à ×200"),
        ("Filtre anti-repliement", "Bessel 3ᵉ ordre · 400 Hz"),
        ("CAN Δ-Σ 24 bits", "ADS131M04 · 4 voies · 32 kSPS"),
    ]
    ys = [146, 232, 318, 404, 490, 576]
    for (t, sub), y in zip(chaine, ys):
        block(sh, 44, y, 300, 56, t, sub, fill="#fff", stroke=SEVE, sw=1.7, tsize=8.0)
    for y in ys[:-1]:
        sh.arrow(194, y + 56, 194, y + 84, color=OR, sw=2.0)

    # --- servitudes ----------------------------------------------------------
    sh.rect(372, 134, 276, 428, fill="#FBF8EF", stroke=OR, sw=1.2, rx=8, dash="6 4")
    sh.txt(510, 154, "SERVITUDES DE PRÉCISION", size=6.4, fill=OR, weight="700",
           spacing="1.2")
    serv = [
        ("Référence 2,5 V", "ADR4525 · 2 ppm/°C"),
        ("Auto-test étalonné", "1 M / 10 M / 100 MΩ à 0,1 %"),
        ("Alimentation ±5 V", "LT3045 · LT3094 · 0,8 µV"),
        ("Base de temps", "TCXO 12,288 MHz · ±1 ppm"),
        ("Pilote de garde", "suiveur ×1 · Cin < 1 pF"),
    ]
    for i, (t, sub) in enumerate(serv):
        block(sh, 386, 170 + i * 78, 248, 58, t, sub, fill="#fff", stroke=OR_CL,
              sw=1.3, tsize=7.4)

    block(sh, 372, 576, 276, 56, "Capteurs d'ambiance",
          "BME688 · TSL2591 · PT1000", fill="#fff", stroke=SEVE_C, sw=1.4, tsize=7.4)

    # --- franchissement de la barrière --------------------------------------
    sh.wire((194, 632), (194, 664), (598, 664), stroke=INK, sw=2.0)
    sh.wire((510, 632), (510, 664), stroke=INK, sw=1.6)
    sh.dot(510, 664)
    block(sh, 598, 636, 188, 56, "Isolateurs", "ADuM4151 · 6 voies",
          fill=CUIV_P, stroke=CUIVRE, sw=1.8, tsize=7.6)

    # --- chaîne numérique ----------------------------------------------------
    num = [
        (232, "Prise USB-C", "CC 5,1 kΩ · ESD · 5 V"),
        (330, "Pile USB TinyUSB", "UAC2 + CDC + DFU"),
        (428, "Microcontrôleur", "RP2350 · 150 MHz"),
        (526, "Sortie MIDI TRS-A", "synthé externe"),
    ]
    for y, t, sub in num:
        block(sh, 738, y, 194, 58, t, sub, fill="#fff", stroke=BLEU, sw=1.7, tsize=7.0)
    sh.wire((786, 664), (942, 664), (942, 457), (930, 457), stroke=INK, sw=2.0)
    sh.arrow(835, 428, 835, 392, color=BLEU, sw=2.0, marker="ahb")
    sh.arrow(835, 330, 835, 294, color=BLEU, sw=2.0, marker="ahb")
    sh.wire((740, 457), (726, 457), (726, 555), (740, 555), stroke=BLEU, sw=1.5, dash="5 4")

    # --- hôte ----------------------------------------------------------------
    block(sh, 96, 748, 440, 56, "Ordinateur hôte — PhytoScope",
          "Linux · Windows · macOS — aucun pilote à installer",
          fill=NUIT, stroke=NUIT, sw=1.6, tcol=OR_CL, tsize=8.6)
    sh.wire((738, 261), (712, 261), (712, 776), (580, 776), stroke=BLEU, sw=2.6)
    sh.arrow(600, 776, 540, 776, color=BLEU, sw=2.4, marker="ahb")
    sh.txt(706, 742, "USB-C · 1 m · blindé", size=6.0, fill=BLEU, anchor="end")

    # --- entrée plante -------------------------------------------------------
    sh.arrow(194, 78, 194, 142, color=SEVE, sw=2.4, marker="ahv")
    sh.txt(150, 74, "PLANTE", size=7.4, fill=SEVE, weight="700", spacing="1.6",
           anchor="end")
    sh.signer()
    sh.save("carte-archi.svg")


# =============================================================================
#  2. CHAÎNE DE MESURE : NIVEAUX, GAINS, BRUIT
# =============================================================================
def fig_chaine():
    sh = Sheet(980, 600, print_mm=125)
    sh.title("Budget de la chaîne de mesure",
             "Niveau du signal, gain et bruit ramené à l'entrée, étage par étage")

    etages = [
        ("Source", "plante", "1 µV – 50 mV", "—", "—"),
        ("Électrode", "Ag/AgCl", "×1", "0,15 µV", "bruit 1/f"),
        ("Entrée", "ADA4530-1", "×1", "0,42 µV", "14 nV/√Hz"),
        ("InAmp", "INA828", "×10", "0,21 µV", "7 nV/√Hz"),
        ("PGA", "OPA2189", "×1…200", "0,18 µV", "5,9 nV/√Hz"),
        ("Filtre", "Bessel 3", "×1", "0,09 µV", "R 4,7 kΩ"),
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
    sh.txt(40, 266, "Bruit ramené à l'entrée, bande 0,01 – 10 Hz",
           size=7, fill=GRIS, anchor="start", style="italic")

    # --- histogramme des contributions --------------------------------------
    contrib = [("Électrode", 0.15), ("ADA4530-1", 0.42), ("INA828", 0.21),
               ("OPA2189", 0.18), ("Filtre", 0.09), ("CAN", 0.31)]
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
    sh.txt(bx + bw / 2, by - 8, "Contribution de chaque étage (µV eff.)", size=6.8,
           fill=NUIT, weight="700")

    # quadrature
    sh.rect(706, 300, 234, 190, fill=NUIT, stroke=NUIT, rx=6)
    sh.txt(823, 328, "Somme quadratique", size=7.2, fill=OR_CL, weight="700", family=SERIF)
    sh.mono(823, 356, "√(Σ eₙ²)", size=8, fill="#EAF2EC")
    sh.txt(823, 396, f"{total:.2f}".replace(".", ",") + " µV eff.", size=13,
           fill="#fff", weight="700", family=SERIF)
    sh.txt(823, 424, "sur 0,01 – 10 Hz", size=6.2, fill="#9fb8ab")
    sh.line(736, 440, 910, 440, stroke=SEVE, sw=1)
    sh.txt(823, 462, "soit 1 LSB du CAN à ×100", size=6.4, fill=OR_CL)
    sh.txt(823, 478, "dynamique utile : 126 dB", size=6.4, fill="#9fb8ab")
    sh.signer()
    sh.save("carte-chaine.svg")




# =============================================================================
#  OUTILLAGE DES PLANCHES (format CAO : cadre, zones, cartouche)
# =============================================================================
def frame(sh, marge=26, zones=("A", "B", "C", "D"), ncol=8):
    """Cadre de planche avec repères de zone, à la manière d'un schéma de CAO."""
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


def cartouche(sh, titre, feuille="1/8", rev="B", bloc="", w=402, h=138):
    """Cartouche normalisé, en bas à droite de la planche.

    Trois bandes : le titre ; l'ensemble auquel la feuille appartient, avec le
    nom de l'auteur et l'adresse du site ; les repères de gestion. Un plan qui
    circule sans ces mentions devient anonyme dès la deuxième photocopie —
    c'est la raison d'être d'un cartouche.
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

    # -- bande d'identité ----------------------------------------------------
    sh.txt(x + w * 0.31, y + 58, PROJET, size=7.4, weight="700", fill=SEVE)
    sh.txt(x + w * 0.31, y + 72, AUTEUR, size=6.4, fill=NUIT, family=SERIF)
    sh.txt(x + w * 0.31, y + 85, SITE, size=5.8, fill=GRIS, family=MONO)
    sh.txt(x + w * 0.81, y + 60, bloc or "Carte mère", size=7, fill=INK)
    sh.txt(x + w * 0.81, y + 76, LICENCE, size=5.6, fill=GRIS)
    sh.txt(x + w * 0.81, y + 87, "diffusion libre", size=5.4, fill=GRIS)

    for cx, lab, val in ((x + w * 0.155, "FEUILLE", feuille),
                         (x + w * 0.465, "RÉVISION", rev),
                         (x + w * 0.715, "DATE", "2026-09"),
                         (x + w * 0.905, "ÉCHELLE", "—")):
        sh.txt(cx, y + 110, lab, size=5.4, fill=GRIS, spacing="0.8")
        sh.txt(cx, y + 128, val, size=7, fill=INK, weight="700", family=MONO)
    return (x, y)


def connector(sh, x, y, n, label="", pitch=38, w=52, side="right",
              pinlabels=None, netlabels=None, fill=OR_PL, lead=30):
    """Connecteur générique ; les broches sortent à droite ou à gauche."""
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
    """Diode verticale conduisant vers le HAUT ; (x, y) = extrémité basse."""
    m = y - L / 2
    sh.line(x, y, x, m + 15, stroke=color)
    sh.poly([(x - 16, m + 15), (x + 16, m + 15), (x, m - 4)], fill=color,
            stroke=color, sw=1)
    sh.line(x - 16, m - 4, x + 16, m - 4, stroke=color, sw=2.6)
    sh.line(x, m - 4, x, y - L, stroke=color)
    return (x, y - L)


def ic_box(sh, x, y, w, h, ref, part, sub=None):
    """Boîtier de circuit intégré (rectangle normalisé)."""
    sh.rect(x, y, w, h, fill="#FBFBF7", stroke=INK, sw=1.8, rx=3)
    sh.txt(x + w / 2, y + 22, ref, size=7.6, fill=SEVE, weight="700")
    sh.txt(x + w / 2, y + 40, part, size=7, fill=INK, family=MONO)
    if sub:
        sh.txt(x + w / 2, y + 58, sub, size=6, fill=GRIS)
    return {"l": x, "r": x + w, "t": y, "b": y + h, "cx": x + w / 2, "cy": y + h / 2}


# =============================================================================
#  PLANCHE 1 — ÉTAGE D'ENTRÉE ÉLECTROMÉTRIQUE (carte fille FE-Z)
# =============================================================================
def pl_frontend():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Entrée électrométrique FE-Z", feuille="1/8",
              bloc="Carte fille FE-Z")
    sh.txt(90, 76, "FE-Z · mesure de potentiel de surface — impédance d'entrée 10¹⁵ Ω",
           size=8.4, fill=NUIT, weight="700", anchor="start", family=SERIF)

    # --- J1 : connecteur d'électrodes ---------------------------------------
    pT, pR, pS = connector(sh, 92, 160, 3, "J1 · TRS 3,5 mm", pitch=72, w=54,
                           pinlabels=["T", "R", "S"])
    for i, t in enumerate(("T — électrode de mesure",
                           "R — garde et blindage du câble",
                           "S — électrode de référence")):
        sh.txt(92, 420 + i * 17, t, size=6, fill=GRIS, anchor="start")

    # --- protection d'entrée -------------------------------------------------
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

    # --- U1 : électromètre ---------------------------------------------------
    sh.rect(560, 100, 260, 300, fill="none", stroke=SEVE, sw=1.2, rx=6, dash="7 5")
    sh.txt(690, 122, "U1 · ADA4530-1", size=7.4, fill=SEVE, weight="700")
    sh.txt(690, 138, "Ib < 20 fA · tampon de garde intégré", size=6, fill=GRIS)

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

    # net GARDE : anneau, blindage, J1 broche R, connecteur mezzanine
    sh.wire((176, 252), (240, 252), (240, 440), (760, 440), (760, 332),
            stroke=OR, sw=1.8)
    sh.txt(272, 430, "NET « GARDE » — anneau de garde, blindage du câble, plan de garde",
           size=6.2, fill=OR, weight="700", anchor="start")
    sh.wire((760, 332), (1090, 332), (1090, 272), (1150, 272), stroke=OR, sw=1.8)

    # --- sortie SIG_A --------------------------------------------------------
    sh.wire((790, 207), (1060, 207), (1060, 316), (1150, 316), stroke=INK, sw=1.7)
    sh.txt(940, 196, "SIG_A", size=6.6, fill=BLEU, weight="700", family=MONO)

    # --- J10 : connecteur mezzanine -----------------------------------------
    j10 = connector(sh, 1180, 120, 6, "J10 · mezzanine", pitch=44, w=56,
                    side="left", pinlabels=["1", "2", "3", "4", "5", "6"],
                    netlabels=["+5 VA", "−5 VA", "AGND", "GARDE", "SIG_A", "ID I²C"])
    for pin in j10[:3]:
        sh.line(pin[0], pin[1], pin[0] - 18, pin[1], stroke=INK, sw=1.2)
    sh.wire((1040, 360), j10[5], stroke=BLEU, sw=1.3, dash="5 4")
    sh.txt(1030, 356, "EEPROM 24AA02 (identification)", size=6, fill=BLEU,
           anchor="end")

    # --- contre-réaction de mode commun --------------------------------------
    sh.rect(420, 466, 480, 250, fill="#FBF8EF", stroke=OR_CL, sw=1.1, rx=6)
    sh.txt(432, 706, "CONTRE-RÉACTION DE MODE COMMUN — pilotage de l'électrode S",
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

    # retour vers l'électrode de référence
    sh.wire((780, 552), (860, 552), (860, 748), (392, 748), stroke=INK)
    resistor(sh, 300, 748, "R9", "22 kΩ", L=92)
    sh.wire((300, 748), (200, 748), (200, 324), (176, 324), stroke=INK)
    sh.save("carte-fe-z.svg")


def netflag(sh, x, y, name, side="out", color=BLEU, w=None):
    """Étiquette de net inter-feuilles (pentagone normalisé)."""
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
    """Multiplexeur analogique : boîtier + voies."""
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
#  PLANCHE 2 — PONT DE MESURE ET DÉTECTION SYNCHRONE (carte fille FE-B)
# =============================================================================
def pl_pont():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Pont de mesure et détection synchrone", feuille="2/8",
              bloc="Carte fille FE-B")
    sh.txt(90, 76, "FE-B · mesure d'impédance par pont excité en alternatif et "
           "démodulation synchrone", size=8.4, fill=NUIT, weight="700",
           anchor="start", family=SERIF)

    # --- excitation ----------------------------------------------------------
    netflag(sh, 92, 130, "EXC 1 kHz", side="in")
    sh.wire((168, 130), (340, 130), stroke=INK, sw=1.6)
    sh.dot(340, 130)
    sh.wire((340, 130), (620, 130), stroke=INK, sw=1.6)
    sh.txt(470, 116, "sinus 200 mV crête — CNA du microcontrôleur", size=6, fill=GRIS)

    # --- branche de référence ------------------------------------------------
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
    sh.txt(285, 652, "gammes de référence — commutation automatique", size=6, fill=GRIS)

    # --- branche « plante » --------------------------------------------------
    sh.wire((620, 130), (620, 168), stroke=INK)
    resistor(sh, 620, 168, "R12", "10 kΩ", horiz=False, L=92, lab_above=False)
    sh.wire((620, 260), (620, 292), stroke=INK)
    sh.dot(620, 292)
    sh.wire((620, 292), (620, 400), stroke=INK)
    pT, pS = connector(sh, 660, 380, 2, "J1 · électrodes", pitch=64, w=54,
                       pinlabels=["T", "S"], side="left", lead=40)
    sh.wire((620, 400), pT, stroke=INK)
    sh.wire((620, 464), pS, stroke=INK)
    sh.wire((620, 464), (620, 510), stroke=INK)
    ground(sh, 620, 510, "agnd")
    sh.txt(736, 404, "R(plante)", size=6.4, fill=SEVE, anchor="start", weight="700")
    sh.txt(736, 420, "100 kΩ à 2 GΩ", size=6, fill=GRIS, anchor="start")

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
    sh.txt(986, 556, "broche REF pilotée par le CNA 16 bits — recentrage",
           size=6, fill=CUIVRE, anchor="start")

    # --- démodulation synchrone ----------------------------------------------
    sh.rect(990, 150, 310, 330, fill="#F5F8FB", stroke=BLEU, sw=1.2, rx=6, dash="7 5")
    sh.txt(1145, 172, "DÉTECTION SYNCHRONE", size=6.6, fill=BLEU, weight="700",
           spacing="1")
    ic_box(sh, 1010, 214, 130, 86, "U4", "ADG1419", "commutateur")
    sh.wire(ia["out"], (1010, 260), stroke=INK, sw=1.6)
    netflag(sh, 1012, 356, "REF_CARRÉ", side="in", color=BLEU, w=96)
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
    sh.txt(1145, 424, "f₋₃dB = 1,6 Hz : seule subsiste la composante", size=6, fill=GRIS)
    sh.txt(1145, 440, "en phase avec l'excitation", size=6, fill=GRIS)

    # --- note ----------------------------------------------------------------
    note(sh, 92, 676, 800,
         ["Le pont est excité à 1 kHz et démodulé en phase : le bruit en 1/f de la chaîne, la dérive",
          "thermique et le 50 Hz du réseau tombent hors de la bande utile. Réjection mesurée : 62 dB à 50 Hz."],
         title="POURQUOI EXCITER EN ALTERNATIF ?")
    sh.save("carte-fe-b.svg")


# =============================================================================
#  PLANCHE 3 — CARTE MÈRE : GAIN, FILTRE, CONVERSION
# =============================================================================
def pl_mere():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Gain, filtrage et conversion", feuille="3/8", bloc="Carte mère")
    sh.txt(90, 76, "Chaîne principale — gain programmable, filtre de Bessel, "
           "convertisseur Δ-Σ 24 bits", size=8.4, fill=NUIT, weight="700",
           anchor="start", family=SERIF)

    netflag(sh, 92, 256, "SIG_A", side="in", w=70)
    sh.wire((162, 256), (250, 256), (250, 256), stroke=INK, sw=1.6)

    # --- gain programmable ---------------------------------------------------
    sh.rect(200, 100, 420, 530, fill="none", stroke=SEVE, sw=1.2, rx=6, dash="7 5")
    sh.txt(410, 122, "GAIN PROGRAMMABLE ×1 … ×200", size=6.6, fill=SEVE,
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
    sh.txt(870, 122, "FILTRE DE BESSEL 3ᵉ ORDRE — 400 Hz", size=6.6, fill=OR,
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
    sh.txt(880, 462, "C21 revient sur la sortie : cellule de Sallen-Key", size=6,
           fill=GRIS)

    # --- attaque différentielle et convertisseur -----------------------------
    sh.wire((1058, 210), (1160, 210), (1160, 300), stroke=INK, sw=1.6)
    ic_box(sh, 1100, 300, 120, 96, "U9", "THS4551", "asym. → diff.")
    sh.wire((1220, 330), (1268, 330), (1268, 520), (1230, 520), stroke=INK, sw=1.4)
    sh.wire((1220, 366), (1248, 366), (1248, 556), (1230, 556), stroke=INK, sw=1.4)
    ic_box(sh, 1060, 480, 170, 160, "U10", "ADS131M04", "24 bits · Δ-Σ · 4 voies")
    sh.txt(1145, 596, "32 kSPS · 106 dB", size=6, fill=GRIS)
    sh.txt(1145, 612, "AIN0…AIN3", size=6, fill=GRIS, family=MONO)
    for i, n in enumerate(("SCLK", "MOSI", "MISO", "DRDY")):
        netflag(sh, 896, 500 + i * 36, n, side="out", color=CUIVRE, w=74)
        sh.wire((970, 500 + i * 36), (1060, 500 + i * 36), stroke=CUIVRE, sw=1.2)
    sh.txt(970, 492, "vers les isolateurs (feuille 4)", size=6, fill=CUIVRE,
           anchor="end")

    # --- référence et base de temps ------------------------------------------
    ic_box(sh, 660, 560, 160, 86, "U11", "ADR4525", "2,5 V · 2 ppm/°C")
    sh.wire((820, 603), (860, 603), (860, 468), (1250, 468), (1250, 480),
            stroke=INK, sw=1.4)
    sh.txt(1010, 458, "REFP", size=6.2, fill=INK, family=MONO)
    ic_box(sh, 400, 660, 170, 86, "Y1", "TCXO 12,288 MHz", "±1 ppm")
    netflag(sh, 596, 703, "CLKIN", side="out", color=BLEU, w=74)
    sh.wire((570, 703), (596, 703), stroke=BLEU, sw=1.4)
    note(sh, 92, 660, 280,
         ["Chaque échantillon est daté par",
          "son numéro d'ordre, jamais par",
          "l'horloge de l'ordinateur."],
         title="BASE DE TEMPS", color=SEVE, fill=SEVE_P)
    sh.save("carte-mere.svg")


def transfo(sh, x, y, ref="T1", part="", n=4, h=110):
    """Transformateur d'isolement : deux bobinages et un noyau."""
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
    cartouche(sh, "Alimentations et isolement", feuille="4/8", bloc="Carte mère")
    sh.txt(90, 76, "Deux masses, une seule barrière — production des rails ±5 V "
           "analogiques isolés", size=8.4, fill=NUIT, weight="700", anchor="start",
           family=SERIF)

    sh.rect(60, 100, 620, 560, fill="#F2F6FC", stroke=BLEU, sw=1.1, rx=8, dash="7 5")
    sh.txt(370, 122, "CÔTÉ USB — masse DGND", size=6.6, fill=BLEU, weight="700",
           spacing="1")
    sh.rect(760, 100, 550, 520, fill="#F3F8F5", stroke=SEVE, sw=1.1, rx=8, dash="7 5")
    sh.txt(1035, 122, "CÔTÉ MESURE — masse AGND, flottante", size=6.6, fill=SEVE,
           weight="700", spacing="1")
    barrier(sh, 720, 120, 660)

    # --- entrée VBUS ---------------------------------------------------------
    netflag(sh, 80, 190, "VBUS 5 V", side="in", w=84)
    sh.wire((164, 190), (190, 190), stroke=INK, sw=1.8)
    ferrite(sh, 190, 190, "FB1", "600 Ω @ 100 MHz")
    sh.wire((266, 190), (330, 190), stroke=INK, sw=1.8)
    sh.dot(330, 190)
    capacitor(sh, 330, 210, "C30", "22 µF", horiz=False, L=76, plate=34)
    sh.wire((330, 190), (330, 210), stroke=INK)
    ground(sh, 330, 286, "dgnd", "DGND")

    # --- convertisseur isolé -------------------------------------------------
    sh.wire((330, 190), (400, 190), stroke=INK, sw=1.8)
    ic_box(sh, 400, 150, 150, 96, "U20", "SN6505B", "pilote de transfo.")
    netflag(sh, 400, 300, "SYNC", side="in", color=BLEU, w=66)
    sh.wire((466, 300), (475, 300), (475, 246), stroke=BLEU, sw=1.2, dash="5 4")
    sh.txt(500, 296, "synchronisé sur SYNC : le résidu de découpage", size=5.8,
           fill=GRIS, anchor="start")
    sh.txt(500, 310, "tombe à 410 kHz, hors de la bande de mesure", size=5.8,
           fill=GRIS, anchor="start")
    t1 = transfo(sh, 684, 160, "T1", "WE 750315371 · 1:1,3", h=110)
    sh.wire((550, 178), (684, 178), stroke=INK, sw=1.6)
    sh.wire((550, 218), (620, 218), (620, 270), (684, 270), stroke=INK, sw=1.6)

    # --- redressement et régulation ------------------------------------------
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
    sh.txt(1090, 380, "PSRR 76 dB à 1 MHz — le résidu de", size=5.8, fill=GRIS)
    sh.txt(1090, 394, "découpage est enterré sous le bruit", size=5.8, fill=GRIS)
    ground(sh, 1090, 420, "iso", "AGND (flottante)")

    # --- isolateurs ----------------------------------------------------------
    ic_box(sh, 620, 420, 200, 120, "U24", "ADuM4151", "6 voies · 17 Mb/s")
    for i, n in enumerate(("SCLK", "MOSI", "MISO", "DRDY")):
        netflag(sh, 400, 440 + i * 30, n, side="out", color=CUIVRE, w=72)
        sh.wire((472, 440 + i * 30), (620, 440 + i * 30), stroke=CUIVRE, sw=1.1)
    sh.txt(900, 448, "vers le CAN (feuille 3)", size=6, fill=CUIVRE, anchor="start")
    sh.wire((820, 470), (890, 470), stroke=CUIVRE, sw=1.4)
    ic_box(sh, 620, 570, 200, 84, "U25", "ADuM1251", "I²C isolé")
    netflag(sh, 400, 612, "SDA/SCL", side="out", color=CUIVRE, w=84)
    sh.wire((484, 612), (620, 612), stroke=CUIVRE, sw=1.1)
    sh.wire((820, 612), (890, 612), stroke=CUIVRE, sw=1.4)
    sh.txt(900, 616, "capteurs d'ambiance", size=6, fill=CUIVRE, anchor="start")

    # --- rail numérique ------------------------------------------------------
    ic_box(sh, 120, 380, 150, 90, "U23", "TPS7A2033", "3,3 V numérique")
    sh.wire((330, 190), (330, 340), (195, 340), (195, 380), stroke=INK)
    sh.wire((195, 470), (195, 510), stroke=CUIVRE, sw=1.6)
    rail(sh, 195, 510, "+3V3", up=False)

    note(sh, 60, 690, 840,
         ["Aucun chemin conducteur ne relie la plante à la terre du bâtiment : le seul lien est le champ",
          "magnétique de T1 et les capacités de couplage des isolateurs, soit moins de 3 pF au total."],
         title="CE QUE LA BARRIÈRE GARANTIT", color=CUIVRE, fill=CUIV_P)
    sh.save("carte-alim.svg")


# =============================================================================
#  PLANCHE 5 — PARTIE NUMÉRIQUE ET LIAISON USB
# =============================================================================
def pl_num():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Partie numérique et liaison USB", feuille="5/8", bloc="Carte mère")
    sh.txt(90, 76, "RP2350 · USB-C · classe audio 2.0 sans pilote · sortie MIDI "
           "directe", size=8.4, fill=NUIT, weight="700", anchor="start", family=SERIF)

    # --- prise USB-C ---------------------------------------------------------
    pins = connector(sh, 92, 150, 6, "J20 · USB-C (récept.)", pitch=48, w=58,
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
    ic_box(sh, 100, 560, 180, 80, "U33", "TPD4S014", "réseau ESD · < 0,5 pF")
    sh.wire((190, 470), (190, 560), stroke=INK, sw=1.2, dash="5 4")
    sh.wire((176, 362), (190, 362), (190, 470), stroke=INK, sw=1.2, dash="5 4")


    # --- microcontrôleur -----------------------------------------------------
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

    # --- vers les isolateurs -------------------------------------------------
    for n, y in (("SCLK", 250), ("MOSI", 276), ("MISO", 302), ("DRDY", 328)):
        netflag(sh, 880, y, n, side="out", color=CUIVRE, w=72)
        sh.wire((798, y), (880, y), stroke=CUIVRE, sw=1.2)
    sh.txt(960, 254, "→ feuille 4", size=6, fill=CUIVRE, anchor="start")

    # --- sortie MIDI ---------------------------------------------------------
    sh.wire((798, 370), (830, 370), stroke=INK, sw=1.4)
    resistor(sh, 830, 370, "R34", "33 Ω", L=80)
    midi = connector(sh, 1150, 180, 3, "J21 · MIDI TRS type A", pitch=40, w=54,
                     side="left", pinlabels=["T", "R", "S"],
                     netlabels=["TX", "+3V3", "GND"], lead=36)
    sh.wire((910, 370), (1060, 370), (1060, 200), midi[0], stroke=INK, sw=1.4)
    sh.txt(1204, 352, "norme MIDI-TRS type A (2018)", size=6, fill=GRIS)

    # --- interface homme-machine --------------------------------------------
    ic_box(sh, 880, 420, 170, 62, "DS1", "LED RVB", "état et niveau")
    sh.wire((798, 451), (880, 451), stroke=INK, sw=1.3)
    ic_box(sh, 880, 500, 170, 62, "S1", "bouton", "marquage / auto-config")
    sh.wire((798, 531), (880, 531), stroke=INK, sw=1.3)
    ic_box(sh, 880, 580, 170, 62, "U31", "W25Q128JV", "16 Mo · QSPI")
    sh.wire((798, 611), (880, 611), stroke=INK, sw=1.3)

    note(sh, 92, 660, 620,
         ["Le microcontrôleur n'interprète rien : il horodate, met en trame et pousse sur USB.",
          "Toute la musique — échelles, instruments, seuils — est calculée sur l'ordinateur.",
          "CC1/CC2 déclarent la carte comme consommateur 5 V / 500 mA : aucune négociation PD."],
         title="CE QUE FAIT, ET NE FAIT PAS, LE MICROCONTRÔLEUR", color=SEVE,
         fill=SEVE_P)
    sh.save("carte-num.svg")


def stars(sh, x, y, n, total=5, r=4.2, col=SEVE):
    for i in range(total):
        sh.circle(x + i * (r * 2.6), y, r, fill=col if i < n else "#fff",
                  stroke=col, sw=1.1)


# =============================================================================
#  IMPLANTATION ET EMPILAGE DU CIRCUIT IMPRIMÉ
# =============================================================================
def fig_pcb():
    sh = Sheet(980, 660, print_mm=125)
    sh.title("Implantation et empilage du circuit imprimé",
             "Quatre couches, deux plans de masse, un anneau de garde")

    # --- empilage ------------------------------------------------------------
    couches = [("Couche 1 — signaux analogiques", "#D9C08A", 18),
               ("Couche 2 — plan de masse AGND / DGND (fendu)", "#8FA79A", 26),
               ("Couche 3 — alimentations", "#B9C6BF", 22),
               ("Couche 4 — signaux numériques, blindage", "#D9C08A", 18)]
    y = 108
    sh.txt(60, 96, "EMPILAGE", size=7.4, fill=NUIT, weight="700", anchor="start",
           spacing="1.4")
    for i, (nom, col, h) in enumerate(couches):
        sh.rect(60, y, 360, h, fill=col, stroke=INK, sw=1.1)
        sh.txt(430, y + h / 2 + 4, nom, size=6.4, fill=INK, anchor="start")
        y += h
        if i < 3:
            sh.rect(60, y, 360, 16, fill="#F0EEE4", stroke=TRAIT, sw=0.9)
            sh.txt(430, y + 12, ["prépreg 0,2 mm", "âme FR4 1,0 mm",
                                 "prépreg 0,2 mm"][i], size=5.8, fill=GRIS,
                   anchor="start")
            y += 16
    sh.txt(60, y + 22, "Épaisseur totale 1,6 mm · cuivre 35 µm · FR4 Tg 150",
           size=6.2, fill=GRIS, anchor="start")

    # --- implantation --------------------------------------------------------
    sh.txt(60, 282, "IMPLANTATION (vue de dessus, 100 × 60 mm)", size=7.4,
           fill=NUIT, weight="700", anchor="start", spacing="1.4")
    bx, by, bw, bh = 60, 306, 620, 300
    sh.rect(bx, by, bw, bh, fill="#F7F9F7", stroke=SEVE, sw=2.0, rx=10)
    for cx, cy in ((bx + 16, by + 16), (bx + bw - 16, by + 16),
                   (bx + 16, by + bh - 16), (bx + bw - 16, by + bh - 16)):
        sh.circle(cx, cy, 6, fill="#fff", stroke=GRIS, sw=1.2)
    # zones
    zones = [(76, 330, 150, 130, "Entrées\net garde", "#EDF5F0", SEVE),
             (240, 330, 150, 130, "Carte fille\n(mezzanine)", "#FBF5E6", OR),
             (404, 330, 120, 130, "Gain et\nfiltre", "#EDF5F0", SEVE),
             (538, 330, 126, 130, "CAN et\nréférence", "#EDF5F0", SEVE),
             (76, 480, 250, 110, "Alimentations isolées", "#FBEEE6", CUIVRE),
             (340, 480, 150, 110, "Isolateurs", "#FBEEE6", CUIVRE),
             (504, 480, 160, 110, "RP2350 · USB-C", "#EEF3FA", BLEU)]
    for x, yy, w, h, lab, fill, col in zones:
        sh.rect(x, yy, w, h, fill=fill, stroke=col, sw=1.4, rx=5)
        for k, line in enumerate(lab.split("\n")):
            sh.txt(x + w / 2, yy + h / 2 - 4 + k * 15, line, size=6.6, fill=col,
                   weight="700")
    sh.line(495, 470, 495, 600, stroke=CUIVRE, sw=2.0, dash="10 6")
    sh.txt(495, 612, "fente du plan de masse — la barrière", size=6, fill=CUIVRE)
    # anneau de garde
    sh.rect(68, 322, 166, 146, fill="none", stroke=OR, sw=2.4, dash="6 4")
    sh.txt(330, 302, "anneau de garde sur les 4 couches", size=5.8, fill=OR,
           weight="700", anchor="start")

    # --- détail de la garde --------------------------------------------------
    sh.txt(710, 282, "DÉTAIL DE LA GARDE", size=7.4, fill=NUIT, weight="700",
           anchor="start", spacing="1.4")
    dx, dy = 710, 320
    sh.rect(dx, dy, 220, 170, fill="#FFFFFF", stroke=TRAIT, sw=1.2, rx=6)
    sh.circle(dx + 110, dy + 85, 10, fill=SEVE, stroke=NUIT, sw=1.2)
    sh.txt(dx + 110, dy + 62, "pastille d'entrée", size=5.8, fill=NUIT)
    for r in (34, 44):
        sh.circle(dx + 110, dy + 85, r, fill="none", stroke=OR, sw=2.2)
    sh.txt(dx + 110, dy + 148, "anneau de garde au même", size=5.8, fill=OR)
    sh.txt(dx + 110, dy + 162, "potentiel que l'entrée", size=5.8, fill=OR)
    note(sh, 710, 500, 220,
         ["Le vernis épargné sous",
          "l'entrée : un courant de",
          "fuite de surface de 1 pA",
          "suffit à ruiner la mesure."],
         title="RÈGLE", color=CUIVRE, fill=CUIV_P)
    sh.signer()
    sh.save("carte-pcb.svg")


# =============================================================================
#  CONNECTEUR MEZZANINE
# =============================================================================
def fig_mezzanine():
    sh = Sheet(980, 460, print_mm=125)
    sh.title("Le connecteur mezzanine, 20 points",
             "Une carte fille se déclare seule : le logiciel la reconnaît au branchement")

    gauche = [("1", "+5 VA", "alimentation analogique"),
              ("3", "−5 VA", "alimentation analogique"),
              ("5", "AGND", "masse analogique"),
              ("7", "AGND", "masse analogique"),
              ("9", "GARDE", "sortie du tampon de garde"),
              ("11", "SIG_A", "voie A vers le PGA"),
              ("13", "SIG_B", "voie B vers le PGA"),
              ("15", "EXC", "excitation, CNA du MCU"),
              ("17", "SDA", "I²C isolé — EEPROM"),
              ("19", "SCL", "I²C isolé — EEPROM")]
    droite = [("2", "+3V3", "logique de la carte fille"),
              ("4", "V_OFF", "consigne d'offset (CNA)"),
              ("6", "AGND", "masse analogique"),
              ("8", "REF_C", "référence carrée 1 kHz"),
              ("10", "GARDE", "second point de garde"),
              ("12", "SEL0", "sélection de gamme"),
              ("14", "SEL1", "sélection de gamme"),
              ("16", "TEMP", "sonde de la carte fille"),
              ("18", "PRES", "détection de présence"),
              ("20", "AGND", "masse analogique")]
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
    sh.title("Plan de bande de l'instrument",
             "Ce qui est mesuré, ce qui est rejeté, et où passe la frontière")

    x0, x1, yb = 90, 920, 380
    f0, f1 = -3.0, 4.0          # décades : 1 mHz … 10 kHz

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

    # réseau 50 Hz
    x50 = fx(math.log10(50))
    sh.line(x50, 108, x50, yb, stroke=CUIVRE, sw=2.0, dash="7 5")
    sh.txt(x50, 100, "50 Hz", size=6.6, fill=CUIVRE, weight="700")
    x1k = fx(3)
    sh.line(x1k, 108, x1k, yb, stroke=BLEU, sw=2.0, dash="7 5")
    sh.txt(x1k, 100, "excitation 1 kHz", size=6.6, fill=BLEU, weight="700")

    # réponse du filtre
    pts = []
    for i in range(0, 201):
        lf = f0 + (f1 - f0) * i / 200
        f = 10 ** lf
        g = 1.0 / math.sqrt(1 + (f / 400.0) ** 6)
        pts.append((fx(lf), 366 - 34 * g))
    sh.path("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts), stroke=OR, sw=2.2)
    sh.txt(fx(1.0), 348, "filtre anti-repliement (−3 dB à 400 Hz)", size=6.2,
           fill=OR, anchor="middle")

    sh.txt(x0, 424, "Échantillonnage : 250 Hz par défaut, 1 kHz en oscilloscope, "
           "32 kHz en écoute directe.", size=6.4, fill=NUIT, anchor="start",
           weight="700")
    sh.txt(x0, 444, "Le 50 Hz est retiré numériquement : aucun déphasage ajouté "
           "dans la bande utile.", size=6.2, fill=GRIS, anchor="start")
    sh.txt(x0, 462, "Passe-haut à 1 mHz : la dérive de l'électrode est suivie, "
           "jamais supprimée.", size=6.2, fill=GRIS, anchor="start")
    sh.signer()
    sh.save("carte-bande.svg")


# =============================================================================
#  DÉTECTION SYNCHRONE — CHRONOGRAMME
# =============================================================================
def fig_lockin():
    sh = Sheet(980, 610, print_mm=125)
    sh.title("Le principe de la détection synchrone",
             "Pourquoi multiplier le signal par sa propre référence élimine presque tout le bruit")

    x0, x1 = 90, 900
    rows = [(120, "Excitation appliquée au pont", SEVE),
            (230, "Signal reçu (bruité, noyé dans le 50 Hz)", CUIVRE),
            (340, "Référence carrée (même phase)", BLEU),
            (450, "Produit, puis moyenne glissante", NUIT)]
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
    sh.txt(x1 - 6, 412, "≈ amplitude mesurée", size=6.2, fill=NUIT,
           anchor="end", weight="700")

    note(sh, 90, 490, 810,
         ["Tout ce qui n'est pas exactement à la fréquence d'excitation — le 50 Hz, le bruit en 1/f,",
          "la dérive thermique — voit son produit changer de signe en permanence : la moyenne l'annule."],
         title="CE QUE L'ON GAGNE", color=SEVE, fill=SEVE_P)
    sh.signer()
    sh.save("carte-lockin.svg")


# =============================================================================
#  ARCHITECTURE LOGICIELLE
# =============================================================================
def fig_logiciel_archi():
    sh = Sheet(980, 720, print_mm=125)
    sh.title("Architecture du logiciel PhytoScope",
             "Trois fils d'exécution, deux files, aucune allocation dans le chemin temps réel")

    # --- fil d'acquisition ---------------------------------------------------
    sh.rect(40, 92, 260, 300, fill="#F3F8F5", stroke=SEVE, sw=1.4, rx=8)
    sh.txt(170, 114, "FIL D'ACQUISITION", size=6.8, fill=SEVE, weight="700",
           spacing="1.2")
    for i, (t, sub) in enumerate([("Source", "UAC2 · série · fichier · simulée"),
                                  ("Horodatage", "compteur du CAN → temps UTC"),
                                  ("Anneau", "collections.deque, 60 s")]):
        block(sh, 60, 138 + i * 84, 220, 66, t, sub, fill="#fff", stroke=SEVE,
              sw=1.3, tsize=7.4)
        if i < 2:
            sh.arrow(170, 204 + i * 84, 170, 232 + i * 84, color=OR, sw=1.8)

    # --- fil de traitement ---------------------------------------------------
    sh.rect(340, 92, 300, 480, fill="#FBF8EF", stroke=OR, sw=1.4, rx=8)
    sh.txt(490, 114, "FIL DE TRAITEMENT (NumPy)", size=6.8, fill=OR, weight="700",
           spacing="1.2")
    for i, (t, sub) in enumerate([("Filtrage", "passe-haut, notch 50 Hz, lissage"),
                                  ("Mesures", "eff., crête, pente, écart-type"),
                                  ("Détection", "seuil adaptatif sur la dérivée"),
                                  ("Sonification", "événement → note, durée, nuance"),
                                  ("Synthèse", "table d'ondes + enveloppe ADSR")]):
        block(sh, 360, 138 + i * 84, 260, 66, t, sub, fill="#fff", stroke=OR_CL,
              sw=1.3, tsize=7.4)
        if i < 4:
            sh.arrow(490, 204 + i * 84, 490, 232 + i * 84, color=OR, sw=1.8)
    sh.arrow(300, 240, 356, 240, color=OR, sw=2.0)
    sh.txt(328, 228, "file", size=5.8, fill=GRIS)

    # --- fil d'interface -----------------------------------------------------
    sh.rect(680, 92, 260, 480, fill="#EEF3FA", stroke=BLEU, sw=1.4, rx=8)
    sh.txt(810, 114, "FIL D'INTERFACE (Qt)", size=6.8, fill=BLEU, weight="700",
           spacing="1.2")
    for i, (t, sub) in enumerate([("Oscilloscope", "pyqtgraph · 60 im/s"),
                                  ("Multimètre", "afficheur et statistiques"),
                                  ("Analyseur", "FFT et spectrogramme"),
                                  ("Écoute", "instruments et mixage"),
                                  ("Bibliothèque", "séances, relecture")]):
        block(sh, 700, 138 + i * 84, 220, 66, t, sub, fill="#fff", stroke=BLEU,
              sw=1.3, tsize=7.4)
    sh.arrow(640, 240, 696, 240, color=BLEU, sw=2.0, marker="ahb")
    sh.txt(668, 228, "file", size=5.8, fill=GRIS)

    # --- sorties -------------------------------------------------------------
    for i, (x, t, sub, col) in enumerate([
            (40, "Enregistreur", "WAV 24 bits + CSV + JSON", NUIT),
            (340, "Sortie audio", "sounddevice / PortAudio", NUIT),
            (680, "Sortie MIDI", "python-rtmidi", NUIT)]):
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
             "Une barre d'état qui ne ment jamais : gain réel, dérive, saturation, horloge")

    sh.rect(40, 84, 900, 500, fill="#12201B", stroke=NUIT, sw=1.6, rx=8)
    # barre de titre
    sh.rect(40, 84, 900, 34, fill="#0A1712", stroke="none", rx=8)
    sh.txt(60, 106, "PhytoScope 1.0 — Ficus benjamina — séance 2026-09-17 14:02",
           size=6.6, fill=OR_CL, anchor="start")
    for i, c in enumerate(("#E06C5A", "#E0C073", "#6FA98A")):
        sh.circle(900 - i * 22, 101, 6, fill=c, stroke="none")
    # onglets
    onglets = ["Oscilloscope", "Multimètre", "Analyseur", "Écoute", "Bibliothèque",
               "Réglages"]
    for i, o in enumerate(onglets):
        x = 56 + i * 142
        act = (i == 0)
        sh.rect(x, 128, 132, 30, fill=SEVE if act else "#1B3129",
                stroke=SEVE if act else "#26443A", sw=1.1, rx=5)
        sh.txt(x + 66, 148, o, size=6.2, fill="#fff" if act else "#9fb8ab",
               weight="700" if act else "400")
    # tracé
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
    sh.txt(240, 214, "événement détecté", size=6, fill=OR_CL)
    sh.line(240, 222, 240, 250, stroke=OR_CL, sw=1.2, dash="4 3")

    # panneau latéral
    sh.rect(732, 176, 192, 300, fill="#16281F", stroke="#26443A", sw=1.1, rx=5)
    sh.txt(828, 200, "RÉGLAGES RAPIDES", size=6, fill=OR_CL, weight="700",
           spacing="1")
    champs = [("Base de temps", "5 s / div"), ("Sensibilité", "200 µV / div"),
              ("Couplage", "AC 0,01 Hz"), ("Notch", "50 Hz — actif"),
              ("Gain matériel", "×100 (auto)"), ("Voie", "A — FE-Z")]
    for i, (k, v_) in enumerate(champs):
        yy = 226 + i * 40
        sh.txt(748, yy, k, size=5.8, fill="#9fb8ab", anchor="start")
        sh.rect(748, yy + 6, 160, 22, fill="#0A1712", stroke="#2E5247", sw=1.0, rx=4)
        sh.txt(756, yy + 21, v_, size=6, fill="#EAF2EC", anchor="start", family=MONO)

    # barre d'état
    sh.rect(56, 492, 868, 72, fill="#0A1712", stroke="#26443A", sw=1.1, rx=5)
    etats = [("ÉTAT", "acquisition", "#7FE0A8"), ("HORLOGE", "CAN ±0,4 ppm", "#EAF2EC"),
             ("SATURATION", "non", "#7FE0A8"), ("DÉRIVE", "+12 µV/min", "#E0C073"),
             ("ÉLECTRODES", "142 / 138 kΩ", "#EAF2EC"),
             ("ENREGISTRE", "● 00:14:22", "#E06C5A")]
    for i, (k, v_, col) in enumerate(etats):
        x = 76 + i * 144
        sh.txt(x, 516, k, size=5.4, fill="#6d8a7d", anchor="start", spacing="0.8")
        sh.txt(x, 540, v_, size=6.6, fill=col, anchor="start", weight="700",
               family=MONO)
    sh.txt(490, 604, "Mode sombre par défaut ; thème clair et contraste renforcé "
           "dans les réglages d'accessibilité.", size=6.2, fill=GRIS, style="italic")
    sh.signer()
    sh.save("logiciel-ihm.svg")


# =============================================================================
#  CHAÎNE DE SONIFICATION
# =============================================================================
def fig_mapping():
    sh = Sheet(980, 600, print_mm=125)
    sh.title("De la microvolt à la note",
             "Chaque flèche est un choix esthétique : le document dit lequel, et pourquoi")

    src = [("Amplitude de l'événement", "µV"), ("Pente à l'origine", "µV/s"),
           ("Durée au-dessus du seuil", "s"), ("Variabilité sur 60 s", "µV eff."),
           ("Température, lumière", "capteurs")]
    dst = [("Hauteur de note", "degré dans la gamme"),
           ("Nuance (vélocité)", "1 – 127"),
           ("Durée de la note", "0,2 – 8 s"),
           ("Densité rythmique", "notes / minute"),
           ("Timbre, réverbération", "instrument, envoi")]
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
          ["quantification", "à la gamme", "et anti-répétition"], fill=OR_PL,
          stroke=OR, sw=1.6, tsize=8)
    sh.signer()
    sh.save("logiciel-mapping.svg")


# =============================================================================
#  COMPARATIF DES LANGAGES
# =============================================================================
def fig_langages():
    sh = Sheet(980, 660, print_mm=125)
    sh.title("Quel langage pour ce logiciel ?",
             "Notes attribuées pour CE cahier des charges — pas dans l'absolu")

    langs = ["Python 3", "C++", "Rust", "Go", "TypeScript\n(Electron)"]
    crits = [("Vitesse de développement", [5, 2, 2, 4, 3]),
             ("Écosystème traitement du signal", [5, 4, 2, 1, 2]),
             ("Qualité des graphiques temps réel", [4, 5, 3, 2, 4]),
             ("Facilité d'installation (3 OS)", [3, 2, 4, 5, 3]),
             ("Accès audio et MIDI", [5, 4, 3, 2, 3]),
             ("Contributions d'un amateur", [5, 1, 2, 3, 3]),
             ("Empreinte mémoire", [2, 5, 5, 4, 1])]
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
           "Python 3 pour l'application, un cœur en C dans le microcontrôleur, "
           "et NumPy pour les boucles chaudes.", size=6.6, fill=NUIT, anchor="start")
    sh.txt(60, y0 + len(crits) * rh + 70,
           "Rust devient le bon choix le jour où la carte doit fonctionner sans "
           "ordinateur.", size=6.2, fill=GRIS, anchor="start")
    sh.signer()
    sh.save("logiciel-langages.svg")


# =============================================================================
#  COMPARATIF DES BOÎTES À OUTILS GRAPHIQUES
# =============================================================================
def fig_toolkits():
    sh = Sheet(980, 600, print_mm=125)
    sh.title("Quelle boîte à outils graphique ?",
             "Le critère décisif n'est pas la beauté : c'est le tracé de 250 points par seconde")

    kits = [("Qt 6 (PySide6)", 5, 5, 5, 4, "LGPL · 60 im/s via pyqtgraph"),
            ("GTK 4 (PyGObject)", 3, 3, 4, 3, "pénible à installer sous Windows"),
            ("wxWidgets (wxPython)", 3, 3, 3, 3, "natif, mais tracé vieillissant"),
            ("Tkinter", 2, 1, 5, 2, "canevas saturé au-delà de 20 im/s"),
            ("Dear PyGui", 4, 4, 4, 2, "GPU rapide, peu accessible"),
            ("HTML5 + TypeScript", 4, 4, 3, 5, "Electron/Tauri : 180 Mo, passerelle")]
    heads = ["Vitesse\nde tracé", "Richesse\ndes widgets", "Installation\nsimple",
             "Beauté\nnative"]
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
    sh.txt(490, 580, "Retenu : PySide6 + pyqtgraph. Le reste du document explique "
           "comment le remplacer si ce choix vieillit.", size=6.4, fill=OR,
           weight="700")
    sh.signer()
    sh.save("logiciel-toolkits.svg")


# =============================================================================
#  LES TROIS NIVEAUX DE MATÉRIEL
# =============================================================================
def fig_tiers():
    sh = Sheet(980, 520, print_mm=125)
    sh.title("Où se situe cette carte",
             "Trois niveaux d'instrument, trois usages, trois budgets")

    tiers = [("NIVEAU 1", "Oscillateur NE555", "25 – 40 €",
              ["mesure : une période", "sortie : MIDI", "aucun étalonnage",
               "idéal pour comprendre"], SEVE, "#EDF5F0",
              "La Musique des Plantes, partie X"),
             ("NIVEAU 2", "INA333 + ADS1115", "60 – 120 €",
              ["mesure : une tension", "16 bits, 860 éch./s", "étalonnage relatif",
               "idéal pour l'atelier"], BLEU, "#EEF3FA",
              "Créer un Arbre Parlant, planche 2"),
             ("NIVEAU 3", "PhytoSense One", "180 – 240 €",
              ["mesure : volts et ohms", "24 bits, isolée, datée", "étalonnage absolu",
               "idéal pour publier"], OR, "#FBF5E6", "Le présent document")]
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
        sh.txt(x + 144, 362, "décrit dans", size=5.8, fill=GRIS)
        for k, line in enumerate(src.split(", ")):
            sh.txt(x + 144, 382 + k * 15, line, size=6.2, fill=NUIT, style="italic")
    sh.txt(490, 470, "Les trois montages partagent les mêmes électrodes et le même "
           "logiciel : on monte d'un niveau sans rien jeter.", size=6.6, fill=NUIT,
           weight="700")
    sh.signer()
    sh.save("carte-tiers.svg")


# =============================================================================
#  HORODATAGE
# =============================================================================
def fig_horodatage():
    sh = Sheet(980, 520, print_mm=125)
    sh.title("L'horodatage : deux horloges, une seule vérité",
             "Le numéro d'échantillon fait foi ; l'heure du système n'est qu'une étiquette")

    sh.rect(40, 96, 420, 180, fill="#F3F8F5", stroke=SEVE, sw=1.4, rx=8)
    sh.txt(250, 120, "HORLOGE DE LA CARTE", size=6.8, fill=SEVE, weight="700",
           spacing="1.2")
    sh.txt(250, 148, "TCXO 12,288 MHz · ±1 ppm", size=7, fill=NUIT, family=MONO)
    sh.txt(250, 172, "n = 0, 1, 2, 3 … compteur 64 bits", size=6.4, fill=INK)
    sh.txt(250, 196, "t = n / 250 Hz, exactement", size=6.4, fill=INK)
    sh.txt(250, 226, "dérive : 86 ms par jour, au pire", size=6.2, fill=GRIS)
    sh.txt(250, 248, "jamais corrigée en cours de séance", size=6.2, fill=CUIVRE,
           weight="700")

    sh.rect(520, 96, 420, 180, fill="#EEF3FA", stroke=BLEU, sw=1.4, rx=8)
    sh.txt(730, 120, "HORLOGE DE L'ORDINATEUR", size=6.8, fill=BLEU, weight="700",
           spacing="1.2")
    sh.txt(730, 148, "CLOCK_MONOTONIC + UTC", size=7, fill=NUIT, family=MONO)
    sh.txt(730, 172, "sauts possibles : NTP, veille,", size=6.4, fill=INK)
    sh.txt(730, 192, "changement d'heure, suspension", size=6.4, fill=INK)
    sh.txt(730, 226, "utilisée uniquement pour nommer", size=6.2, fill=GRIS)
    sh.txt(730, 248, "et pour dater le début de séance", size=6.2, fill=GRIS)

    block(sh, 250, 320, 480, 78, "Ajustement affine au fil de l'eau",
          "t_UTC = a · n + b, réestimé toutes les 10 s",
          fill=OR_PL, stroke=OR, sw=1.6, tsize=7.6)
    sh.arrow(250, 276, 360, 316, color=SEVE, sw=1.8, marker="ahv")
    sh.arrow(730, 276, 620, 316, color=BLEU, sw=1.8, marker="ahb")
    sh.txt(490, 430, "Résultat : deux séances enregistrées sur deux machines "
           "différentes restent superposables à la milliseconde.", size=6.6,
           fill=NUIT, weight="700")
    sh.txt(490, 452, "Chaque fichier porte les deux échelles ; aucune n'est perdue.",
           size=6.2, fill=GRIS)
    sh.signer()
    sh.save("carte-horodatage.svg")


# =============================================================================
#  CIRCUIT IMPRIMÉ — IMPLANTATION ET ROUTAGE QUATRE COUCHES
# =============================================================================
#  Le dessin est décrit en millimètres réels : la carte fait 100 × 60 mm.
#  Une fonction de conversion place ces millimètres dans le viewBox, de sorte
#  que les cotes portées sur les planches sont les vraies.
# -----------------------------------------------------------------------------
CARTE_L, CARTE_H = 100.0, 60.0          # dimensions hors tout, en millimètres

#  (référence, x, y, largeur, hauteur, rotation, description)
COMPOSANTS = [
    ("J1",   6.0,  12.0, 12.0, 12.0, "entrée voie A"),
    ("J2",   6.0,  30.0, 12.0, 12.0, "entrée voie B"),
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

#  Pistes par couche : chaque piste est une polyligne en millimètres.
PISTES = {
    1: [  # signaux analogiques, côté composants
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
    4: [  # signaux numériques et blindage
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
    1: ("Couche 1 — signaux analogiques", "#B03A2E", "côté composants"),
    2: ("Couche 2 — plan de masse (fendu)", "#1E6F50", "référence unique"),
    3: ("Couche 3 — alimentations", "#2F5E86", "±5 V, 3,3 V, 5 V"),
    4: ("Couche 4 — signaux numériques", "#8A6A1F", "côté soudure"),
}


def _pcb_transform(x0: float, y0: float, echelle: float):
    """Renvoie une fonction mm → unités du viewBox."""
    def mm(x: float, y: float):
        return (x0 + x * echelle, y0 + y * echelle)
    return mm


def _dessiner_carte(sh, mm, echelle, couche: int, avec_composants: bool = True,
                    avec_reperes: bool = True):
    """Trace le contour, les fixations, les composants et les pistes."""
    x0, y0 = mm(0, 0)
    x1, y1 = mm(CARTE_L, CARTE_H)
    sh.rect(x0, y0, x1 - x0, y1 - y0, fill="#F7F9F7", stroke=NUIT, sw=2.0, rx=4)

    # fente du plan de masse : la barrière d'isolement
    xa, _ = mm(56, 0)
    sh.line(xa, y0 + 2, xa, y1 - 2, stroke=CUIVRE, sw=2.0, dash="8 5")

    for cx, cy in ((4, 4), (CARTE_L - 4, 4), (4, CARTE_H - 4),
                   (CARTE_L - 4, CARTE_H - 4)):
        px, py = mm(cx, cy)
        sh.circle(px, py, 1.6 * echelle, fill="#fff", stroke=GRIS, sw=1.2)
        sh.circle(px, py, 0.8 * echelle, fill=GRIS, stroke=GRIS, sw=0.8)

    # anneau de garde autour des entrées
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

    # -- sérigraphie : le nom du projet, l'auteur et l'adresse ---------------
    #  Gravés dans le cuivre de la couche de sérigraphie : une carte qui
    #  circule doit dire d'où elle vient, même séparée de sa documentation.
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
        sh.txt(tx, ty + echelle * 1.05, "RÉV. B · CERN-OHL-P v2",
               size=max(3.8, echelle * 0.46), fill=GRIS, anchor="end")

    if avec_reperes:
        sh.txt((x0 + x1) / 2, y1 + 16, f"{CARTE_L:.0f} mm", size=6, fill=GRIS)
        sh.txt(x0 - 14, (y0 + y1) / 2, f"{CARTE_H:.0f} mm", size=6, fill=GRIS,
               rot=-90)


def pl_pcb_couches():
    """Planche : les quatre couches, côte à côte."""
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Routage — quatre couches", feuille="1/3", bloc="Circuit imprimé")
    sh.txt(90, 74, "PhytoSense One — circuit imprimé 100 × 60 mm, FR4 1,6 mm, "
           "cuivre 35 µm", size=8.2, fill=NUIT, weight="700", anchor="start",
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

    # --- légende -----------------------------------------------------------
    lx, ly = 1030, 130
    sh.rect(lx, ly, 260, 380, fill="#FBFBF7", stroke=TRAIT, sw=1.0, rx=5)
    sh.txt(lx + 130, ly + 20, "LÉGENDE", size=6.6, fill=NUIT, weight="700",
           spacing="1.4")
    entrees = [(COUCHES[1][1], "piste couche 1"), (COUCHES[2][1], "piste couche 2"),
               (COUCHES[3][1], "piste couche 3"), (COUCHES[4][1], "piste couche 4"),
               (CUIVRE, "fente du plan de masse"), (OR, "anneau de garde")]
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
            "Échelle 1 : 2,5", "",
            "La fente du plan de masse",
            "sépare la masse analogique",
            "flottante de la masse USB.",
            "Aucune piste ne la franchit :",
            "seuls le transformateur T1 et",
            "les isolateurs U24 la traversent,",
            "et ils la traversent dans l'air."]):
        sh.txt(lx + 14, yy + 56 + i * 15, ligne, size=5.6, fill=GRIS,
               anchor="start")
    sh.txt(500, 770, "Les quatre couches sont représentées vues de dessus "
           "(couche 4 non miroitée) — c'est la convention des fichiers Gerber "
           "fournis.", size=6.0, fill=GRIS)
    sh.save("pcb-couches.svg")


def pl_pcb_implantation():
    """Planche : implantation, sérigraphie et cotes."""
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Implantation et sérigraphie", feuille="2/3",
              bloc="Circuit imprimé")
    sh.txt(90, 74, "Implantation vue de dessus — repères de sérigraphie et zones "
           "fonctionnelles", size=8.2, fill=NUIT, weight="700", anchor="start",
           family=SERIF)

    echelle = 8.2
    mm = _pcb_transform(140, 140, echelle)
    _dessiner_carte(sh, mm, echelle, 1, avec_composants=True)

    # --- étiquettes, réparties sans chevauchement -------------------------
    #  Les composants sont serrés ; on répartit donc les étiquettes sur deux
    #  colonnes, en les espaçant d'au moins une hauteur de ligne, puis on
    #  trace un rappel jusqu'à la pastille.
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

    zones = [("entrées et garde", 3, 8, 31, 36, OR),
             ("conditionnement", 46, 8, 28, 30, SEVE),
             ("alimentation isolée", 14, 42, 42, 16, CUIVRE),
             ("numérique et USB", 74, 12, 24, 40, BLEU)]
    for nom, zx, zy, zw, zh, couleur in zones:
        ax, ay = mm(zx, zy)
        sh.rect(ax, ay, zw * echelle, zh * echelle, fill="none", stroke=couleur,
                sw=1.2, dash="4 3")
        sh.txt(ax + 4, ay + 12, nom, size=5.8, fill=couleur, anchor="start",
               weight="700")
    sh.save("pcb-implantation.svg")


def fig_pcb_empilage():
    """Figure : empilage, impédances et règles de percement."""
    sh = Sheet(980, 640, print_mm=125)
    sh.title("Empilage, impédances et perçages",
             "Quatre couches sur FR4 1,6 mm — ce que le fabricant doit savoir")

    couches = [("Couche 1 — signaux analogiques", "35 µm", "#D9C08A", 20),
               ("Prépreg 7628 ×1", "0,20 mm", "#F0EEE4", 14),
               ("Couche 2 — masse AGND / DGND (fendue)", "35 µm", "#8FA79A", 24),
               ("Âme FR4 Tg150", "1,00 mm", "#E6E2D2", 30),
               ("Couche 3 — alimentations", "35 µm", "#B9C6BF", 22),
               ("Prépreg 7628 ×1", "0,20 mm", "#F0EEE4", 14),
               ("Couche 4 — numérique et blindage", "35 µm", "#D9C08A", 20)]
    y = 100
    for nom, ep, couleur, h in couches:
        sh.rect(60, y, 420, h, fill=couleur, stroke=INK, sw=1.0)
        sh.txt(492, y + h / 2 + 4, nom, size=6.6, fill=INK, anchor="start")
        sh.txt(474, y + h / 2 + 4, ep, size=6, fill=GRIS, anchor="end")
        y += h
    sh.txt(270, y + 22, "épaisseur totale 1,60 mm ± 10 %", size=6.4, fill=NUIT,
           weight="700")

    lignes = [
        ("Largeur de piste minimale", "0,20 mm (8 mil)"),
        ("Isolement minimal", "0,20 mm — 0,60 mm de part et d'autre de la fente"),
        ("Via traversant", "percé 0,30 mm, pastille 0,60 mm"),
        ("Via de masse sous les boîtiers", "matrice de 1,2 mm"),
        ("Impédance différentielle USB", "90 Ω ± 10 % (couche 4 sur couche 3)"),
        ("Impédance de l'horloge du CAN", "50 Ω asymétrique"),
        ("Finition", "ENIG — obligatoire sous les entrées électrométriques"),
        ("Vernis épargné", "sous J1, J2 et l'anneau de garde"),
        ("Classe IPC", "2 (fabrication courante, aucun surcoût)"),
    ]
    y0 = 300
    sh.txt(60, y0 - 12, "RÈGLES DE FABRICATION", size=7.2, fill=NUIT,
           weight="700", anchor="start", spacing="1.2")
    for i, (cle, valeur) in enumerate(lignes):
        yy = y0 + i * 26
        sh.rect(60, yy, 860, 22, fill="#FAFBFA" if i % 2 else "#fff",
                stroke=TRAIT, sw=0.8, rx=3)
        sh.txt(72, yy + 15, cle, size=6.4, fill=INK, anchor="start")
        sh.txt(908, yy + 15, valeur, size=6.4, fill=SEVE, anchor="end",
               weight="700")
    note(sh, 60, y0 + len(lignes) * 26 + 16, 860,
         ["Le vernis épargné sous les entrées n'est pas un détail esthétique : un film",
          "de vernis humide conduit assez pour ruiner une mesure à 10¹⁵ Ω. C'est la",
          "première chose à vérifier quand une voie dérive sans raison apparente."],
         title="LE POINT QUI FAIT ÉCHOUER LES PREMIÈRES SÉRIES", color=CUIVRE,
         fill=CUIV_P)
    sh.signer()
    sh.save("pcb-empilage.svg")


# =============================================================================
#  COUVERTURES
# =============================================================================
def _fond_circuit(sh, w, h, seed=11, densite=40):
    """Trame de pistes de circuit imprimé, façon fond de couverture."""
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
    """Feuille stylisée dont les nervures sont des pistes."""
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
    # trace d'un signal qui sort de la feuille
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
    """Couverture sobre pour les trois annexes détachables."""
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
                       "Dossier\nde schémas",
                       "Six feuilles — révision B", "ANNEXE 1", 17)


def fig_cover_bom():
    _couverture_annexe("carte-cover-bom.svg",
                       "Nomenclature\net accessoires",
                       "47 références · budgets détaillés", "ANNEXE 2", 23)


def fig_cover_pcb():
    _couverture_annexe("carte-cover-pcb.svg",
                       "Circuit\nimprimé",
                       "Quatre couches — dossier de fabrication", "ANNEXE 3", 31)


# =============================================================================
#  PLANCHE 7 — PROTECTIONS ET GESTION DE L'ALIMENTATION
# =============================================================================
def pl_protections():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Protections et gestion d'alimentation", feuille="7/8",
              bloc="Carte mère")
    sh.txt(90, 74, "Deux sources, une priorité, et rien qui casse en cas de "
           "fausse manœuvre", size=8.4, fill=NUIT, weight="700", anchor="start",
           family=SERIF)

    # ---------------- voie « bloc secteur » --------------------------------
    sh.rect(60, 104, 560, 210, fill="#FBF8EF", stroke=OR, sw=1.2, rx=6, dash="7 5")
    sh.txt(340, 124, "ENTRÉE BLOC SECTEUR — 7 à 24 V, polarité indifférente",
           size=6.6, fill=OR, weight="700", spacing="1")

    pJ30 = connector(sh, 82, 150, 3, "J30 · 2,1 mm", pitch=42, w=50,
                     pinlabels=["+", "−", "S"])
    sh.wire(pJ30[0], (210, 170), stroke=INK, sw=1.8)

    # anti-inversion par MOS canal P
    ic_box(sh, 210, 146, 96, 58, "Q30", "DMP3099L", "anti-inversion")
    sh.txt(258, 222, "une inversion bloque,", size=5.8, fill=GRIS)
    sh.txt(258, 236, "elle ne détruit rien", size=5.8, fill=GRIS)

    sh.wire((306, 170), (346, 170), stroke=INK, sw=1.8)
    sh.dot(346, 170)
    diode_up(sh, 346, 240, L=60)
    sh.txt(316, 262, "D30 · SMAJ18A", size=6.2, fill=SEVE, anchor="start",
           weight="700")
    sh.txt(316, 276, "écrête à 18 V, 400 W", size=5.8, fill=GRIS, anchor="start")
    sh.wire((346, 240), (346, 262), stroke=INK)
    ground(sh, 346, 262, "dgnd")

    sh.wire((346, 170), (420, 170), stroke=INK, sw=1.8)
    ic_box(sh, 420, 142, 120, 66, "U60", "TPS62932", "abaisseur 5,2 V")
    sh.txt(480, 222, "2 A · 92 % · protégé en court-circuit", size=5.8, fill=GRIS)
    sh.wire((540, 170), (600, 170), (600, 300), stroke=CUIVRE, sw=2.0)
    sh.txt(572, 156, "5,2 V", size=6.4, fill=CUIVRE, weight="700", family=MONO)

    # ---------------- voie USB ---------------------------------------------
    sh.rect(60, 340, 560, 190, fill="#F2F6FC", stroke=BLEU, sw=1.2, rx=6, dash="7 5")
    sh.txt(340, 360, "ENTRÉE USB — 5 V, 500 mA déclarés", size=6.6, fill=BLEU,
           weight="700", spacing="1")

    netflag(sh, 82, 400, "VBUS", side="in", w=64)
    sh.wire((146, 400), (190, 400), stroke=INK, sw=1.8)
    ferrite(sh, 190, 400, "FB1", "600 Ω")
    sh.wire((266, 400), (300, 400), stroke=INK, sw=1.8)
    ic_box(sh, 300, 372, 130, 66, "U61", "TPS2553", "limite à 500 mA")
    sh.txt(365, 452, "coupe en 2 µs sur court-circuit,", size=5.8, fill=GRIS)
    sh.txt(365, 466, "signale le défaut, se réarme seul", size=5.8, fill=GRIS)
    sh.wire((430, 400), (600, 400), (600, 330), stroke=CUIVRE, sw=2.0)
    sh.txt(500, 390, "5,0 V", size=6.4, fill=CUIVRE, weight="700", family=MONO)
    netflag(sh, 300, 480, "FAULT", side="out", color=CUIVRE, w=70)
    sh.wire((370, 480), (410, 480), (410, 438), stroke=CUIVRE, sw=1.2, dash="4 3")

    # ---------------- aiguilleur -------------------------------------------
    ic_box(sh, 640, 270, 150, 90, "U62", "TPS2116", "aiguilleur à priorité")
    sh.txt(715, 378, "priorité au bloc secteur ;", size=5.8, fill=GRIS)
    sh.txt(715, 392, "bascule sans coupure ;", size=5.8, fill=GRIS)
    sh.txt(715, 406, "blocage inverse des deux côtés", size=5.8, fill=GRIS)
    sh.wire((600, 300), (640, 300), stroke=CUIVRE, sw=2.0)
    sh.wire((600, 330), (640, 330), stroke=CUIVRE, sw=2.0)
    sh.wire((790, 315), (850, 315), stroke=CUIVRE, sw=2.4)
    sh.txt(820, 305, "5 V", size=6.6, fill=CUIVRE, weight="700", family=MONO)

    # ---------------- mesure de consommation --------------------------------
    resistor(sh, 850, 315, "R60", "0,1 Ω", L=80)
    sh.wire((930, 315), (980, 315), stroke=CUIVRE, sw=2.4)
    ic_box(sh, 980, 286, 130, 62, "U63", "INA219", "tension et courant")
    sh.txt(1045, 366, "alimente l'afficheur :", size=5.8, fill=GRIS)
    sh.txt(1045, 380, "5,03 V · 137 mA · 0,69 W", size=5.8, fill=SEVE, weight="700")
    netflag(sh, 980, 410, "I²C", side="out", color=BLEU, w=56)

    sh.wire((1110, 315), (1180, 315), stroke=CUIVRE, sw=2.4)
    ferrite(sh, 1180, 315, "F30", "0,5 A")
    sh.wire((1256, 315), (1284, 315), stroke=CUIVRE, sw=2.4)
    rail(sh, 1284, 315, "5 V carte")

    # ---------------- protections des entrées de mesure ---------------------
    sh.rect(640, 430, 660, 180, fill="#FBEEE6", stroke=CUIVRE, sw=1.2, rx=6,
            dash="7 5")
    sh.txt(970, 450, "PROTECTION DES ENTRÉES DE MESURE", size=6.6, fill=CUIVRE,
           weight="700", spacing="1")

    netflag(sh, 656, 490, "ÉLECTRODE", side="in", color=SEVE, w=98)
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
    sh.txt(1096, 486, "vers U1", size=6.2, fill=SEVE, anchor="start", weight="700")
    sh.txt(1096, 500, "(feuille 1)", size=5.8, fill=GRIS, anchor="start")
    sh.txt(1096, 528, "0,5 pF seulement :", size=5.8, fill=GRIS, anchor="start")
    sh.txt(1096, 542, "ne charge pas l'entrée", size=5.8, fill=GRIS, anchor="start")
    sh.txt(700, 556, "un branchement sur une source active ouvre le fusible",
           size=5.8, fill=GRIS, anchor="start")
    sh.txt(700, 570, "au lieu de détruire l'amplificateur d'entrée",
           size=5.8, fill=GRIS, anchor="start")

    note(sh, 60, 560, 550,
         ["Toute combinaison est admise : bloc secteur seul, USB seul, ou les deux.",
          "Le passage de l'un à l'autre se fait sans coupure ni redémarrage — on peut",
          "débrancher l'ordinateur en pleine séance sans perdre un échantillon."],
         title="DEUX SOURCES, AUCUNE MANIPULATION", color=SEVE, fill=SEVE_P)
    sh.save("carte-protections.svg")


# =============================================================================
#  PLANCHE 8 — SIGNALISATION ET AFFICHEUR
# =============================================================================
def pl_ihm():
    sh = Sheet(1360, 830, print_mm=212)
    frame(sh)
    cartouche(sh, "Signalisation et afficheur", feuille="8/8", bloc="Carte mère")
    sh.txt(90, 74, "Ce que l'appareil montre sans qu'on ait à ouvrir un logiciel",
           size=8.4, fill=NUIT, weight="700", anchor="start", family=SERIF)

    # ---- voyants -----------------------------------------------------------
    sh.rect(60, 104, 520, 400, fill="#FBFBF7", stroke=SEVE, sw=1.2, rx=6, dash="7 5")
    sh.txt(320, 124, "VOYANTS", size=6.8, fill=SEVE, weight="700", spacing="1.4")

    voyants = [
        ("DS2", "bicolore", "ALIMENTATION", SEVE,
         ["vert fixe : bloc secteur", "ambre fixe : alimenté par l'USB",
          "ambre clignotant : limitation en cours"]),
        ("DS3", "bleue", "LIEN USB", BLEU,
         ["éteint : non énuméré", "fixe : énuméré, au repos",
          "clignotant : flux de mesure actif"]),
        ("DS4", "rouge", "DÉFAUT", CUIVRE,
         ["surintensité ou court-circuit", "saturation persistante",
          "auto-test en échec"]),
        ("DS1", "RVB", "MESURE", OR,
         ["vert : acquisition normale", "ambre : saturation",
          "bleu : aucune électrode", "luminosité = niveau du signal"]),
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

    sh.txt(320, 486, "chaque voyant est en série avec 1 kΩ (R70 à R73) : 2 mA, "
           "lisible sans éblouir dans le noir", size=6, fill=GRIS)

    # ---- afficheur ---------------------------------------------------------
    sh.rect(620, 104, 690, 380, fill="#F2F6FC", stroke=BLEU, sw=1.2, rx=6,
            dash="7 5")
    sh.txt(965, 124, "AFFICHEUR OLED 128 × 64 — BUS I²C", size=6.8, fill=BLEU,
           weight="700", spacing="1")

    ic_box(sh, 650, 150, 150, 70, "DS5", "SSD1306", "0,96 pouce")
    netflag(sh, 650, 250, "SDA", side="out", color=BLEU, w=60)
    netflag(sh, 650, 285, "SCL", side="out", color=BLEU, w=60)
    sh.wire((710, 250), (760, 250), (760, 220), stroke=BLEU, sw=1.2)
    sh.wire((710, 285), (780, 285), (780, 220), stroke=BLEU, sw=1.2)
    sh.txt(725, 330, "adresse 0x3C · 3,3 V", size=6, fill=GRIS)

    # maquette de l'écran
    ex, ey, ew, eh = 840, 160, 420, 210
    sh.rect(ex, ey, ew, eh, fill="#0A1712", stroke=INK, sw=2.0, rx=5)
    lignes_ecran = [
        ("PhytoSense One", "#E0C073", 9.4, 30),
        ("source   bloc secteur", "#EAF2EC", 7.6, 58),
        ("gain     ×100  gamme 10 MΩ", "#EAF2EC", 7.6, 80),
        ("mesure   +412,7 µV", "#7FE0A8", 9.0, 106),
        ("bruit    0,63 µV eff.", "#EAF2EC", 7.6, 130),
        ("conso.   5,03 V · 137 mA", "#9fb8ab", 7.2, 152),
        ("USB      flux actif · 0 perdu", "#7FE0A8", 7.2, 174),
        ("événem.  37 · 12,4 /min", "#EAF2EC", 7.2, 196),
    ]
    for texte, couleur, taille, dy in lignes_ecran:
        sh.txt(ex + 14, ey + dy, texte, size=taille, fill=couleur, anchor="start",
               family=MONO)
    sh.txt(ex + ew / 2, ey + eh + 20, "lisible sur place, écran de l'ordinateur hors de portée",
           size=6.2, fill=GRIS)

    sh.txt(965, 430, "Quatre pages font défiler par appui bref sur le bouton :",
           size=6.4, fill=NUIT, weight="700")
    sh.txt(965, 448, "mesure · alimentation · lien USB · auto-test", size=6.2,
           fill=GRIS)
    sh.txt(965, 466, "Un appui long pose un marqueur horodaté.", size=6.2,
           fill=GRIS)

    # ---- bouton ------------------------------------------------------------
    ic_box(sh, 60, 520, 150, 62, "S1", "bouton", "appui bref / long")
    sh.wire((210, 551), (280, 551), stroke=INK, sw=1.4)
    netflag(sh, 280, 551, "GPIO", side="out", color=CUIVRE, w=64)

    note(sh, 360, 512, 620,
         ["La carte travaille toujours reliée à un ordinateur, mais celui-ci est posé",
          "trois mètres plus loin. Les quatre voyants répondent sur place aux quatre",
          "questions qu'on se pose à genoux devant l'arbre : est-ce alimenté, est-ce",
          "relié, est-ce que ça mesure, et est-ce qu'il y a un problème."],
         title="POURQUOI DE LA SIGNALISATION LOCALE", color=SEVE, fill=SEVE_P)
    sh.save("carte-ihm.svg")


# =============================================================================
#  ARBRE D'ALIMENTATION ET PROTECTIONS (figure de synthèse)
# =============================================================================
def fig_alim_arbre():
    sh = Sheet(980, 700, print_mm=125)
    sh.title("Arbre d'alimentation et protections",
             "Deux sources, une priorité, cinq barrières de protection")

    # sources
    block(sh, 40, 110, 200, 66, "Bloc secteur", "7 à 24 V · 1 A",
          fill=OR_PL, stroke=OR, sw=1.6, tsize=8)
    block(sh, 40, 230, 200, 66, "Port USB", "5 V · 500 mA",
          fill=BLEU_P, stroke=BLEU, sw=1.6, tsize=8)

    # protections voie secteur
    etapes_sec = [("Anti-inversion", "Q30 · MOS canal P"),
                  ("Écrêtage 18 V", "D30 · transil 400 W"),
                  ("Abaisseur 5,2 V", "U60 · protégé")]
    for i, (t, sub) in enumerate(etapes_sec):
        block(sh, 280 + i * 190, 110, 170, 66, t, sub, fill="#fff", stroke=OR,
              sw=1.3, tsize=7.2)
        if i:
            sh.arrow(270 + i * 190, 143, 276 + i * 190, 143, color=OR, sw=1.6)
    sh.arrow(240, 143, 276, 143, color=OR, sw=1.8)

    # protections voie USB
    etapes_usb = [("Ferrite", "FB1 · 600 Ω"),
                  ("Limiteur 500 mA", "U61 · coupe en 2 µs"),
                  ("Signal de défaut", "vers le voyant rouge")]
    for i, (t, sub) in enumerate(etapes_usb):
        block(sh, 280 + i * 190, 230, 170, 66, t, sub, fill="#fff", stroke=BLEU,
              sw=1.3, tsize=7.2)
        if i:
            sh.arrow(270 + i * 190, 263, 276 + i * 190, 263, color=BLEU, sw=1.6)
    sh.arrow(240, 263, 276, 263, color=BLEU, sw=1.8)

    # aiguilleur
    block(sh, 380, 350, 220, 76, "Aiguilleur à priorité",
          "U62 · TPS2116 · sans coupure", fill=SEVE_P, stroke=SEVE, sw=1.8,
          tsize=8)
    sh.arrow(470, 176, 470, 346, color=OR, sw=1.8)
    sh.arrow(520, 296, 520, 346, color=BLEU, sw=1.8)
    sh.txt(620, 372, "le bloc secteur l'emporte quand il est présent",
           size=6.2, fill=GRIS, anchor="start")
    sh.txt(620, 388, "la bascule est indolore : aucun échantillon perdu",
           size=6.2, fill=GRIS, anchor="start")

    # mesure et distribution
    block(sh, 380, 450, 220, 66, "Mesure de consommation", "U63 · INA219",
          fill="#fff", stroke=SEVE, sw=1.4, tsize=7.6)
    sh.arrow(490, 426, 490, 446, color=SEVE, sw=1.8)
    block(sh, 380, 546, 220, 62, "Fusible réarmable", "F30 · 0,5 A",
          fill=CUIV_P, stroke=CUIVRE, sw=1.4, tsize=7.6)
    sh.arrow(490, 516, 490, 542, color=SEVE, sw=1.8)

    sorties = [("+3V3 numérique", "U23"), ("±5 V analogiques isolés", "T1, U21, U22"),
               ("Afficheur et voyants", "2 mA chacun")]
    for i, (t, sub) in enumerate(sorties):
        block(sh, 660, 450 + i * 74, 280, 60, t, sub, fill="#fff", stroke=GRIS,
              sw=1.2, tsize=7.4)
        sh.arrow(604, 577, 656, 480 + i * 74, color=SEVE, sw=1.4)

    note(sh, 40, 620, 900,
         ["Inversion de polarité, court-circuit, surtension, surintensité, décharge",
          "électrostatique : chacun de ces cinq accidents rencontre une barrière avant",
          "d'atteindre un composant coûteux. Aucun fusible à remplacer : tout se réarme."],
         title="LES CINQ ACCIDENTS COUVERTS", color=CUIVRE, fill=CUIV_P)
    sh.signer()
    sh.save("carte-alim-arbre.svg")


# =============================================================================
#  GABARITS DE PERÇAGE — ÉCHELLE 1:1
#
#  Règle absolue de ces planches : une unité du viewBox vaut exactement un
#  dixième de millimètre réel. La feuille fait 1800 × 900 unités et s'imprime
#  sur 180 mm de large ; toute cote lue à la règle sur le papier est donc la
#  vraie. Une réglette de contrôle de 100 mm figure sur chaque gabarit : si
#  elle ne mesure pas 100 mm, l'impression a été remise à l'échelle et le
#  gabarit est inutilisable.
# =============================================================================
UPMM = 10.0          # unités de viewBox par millimètre

#  Boîtier retenu : aluminium extrudé 120 × 80 × 30 mm, faces amovibles.
FACE_L, FACE_H = 116.0, 26.0          # face avant et arrière, en millimètres


def _gab(x_mm, y_mm, ox, oy):
    """Millimètres de la face → unités du viewBox."""
    return (ox + x_mm * UPMM, oy + y_mm * UPMM)


def _percage(sh, ox, oy, x, y, diametre, repere, legende="", dessous=True):
    """Trou rond : cercle au diamètre réel, croix de centrage, cote.

    `dessous` place les cotes sous le trou ; à faux, elles passent au-dessus,
    ce qui évite les chevauchements quand deux perçages sont proches.
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
    """Ouverture rectangulaire : contour réel, croix de centrage, cotes."""
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
    """Réglette de contrôle : si elle ne mesure pas sa cote, ne pas percer."""
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
           f"RÉGLETTE DE CONTRÔLE — CETTE BARRE DOIT MESURER {longueur_mm:g} mm",
           size=6.4, fill=CUIVRE, weight="700", spacing="0.8")


def _avertissement_impression(sh, x, y, w=700):
    note(sh, x, y, w,
         ["Imprimer à 100 %, sans « ajuster à la page ».",
          "Vérifier la réglette à la règle AVANT de percer :",
          "4 % d'erreur décalent le dernier trou de 4 mm.",
          "Coller le gabarit à la face au ruban adhésif,",
          "pointer au pointeau, puis percer en deux passes :",
          "avant-trou de 3 mm, puis cote finale."],
         title="AVANT DE PERCER — À LIRE", color=CUIVRE, fill=CUIV_P)


def _cadre_face(sh, ox, oy, titre, sous_titre):
    """Contour de la face, avec ses cotes d'encombrement."""
    w, h = FACE_L * UPMM, FACE_H * UPMM
    sh.rect(ox, oy, w, h, fill="#FBFBF7", stroke=NUIT, sw=2.2, rx=8)
    # axes de référence
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


def _tableau_percages(sh, x, y, lignes, titre="COORDONNÉES DES PERÇAGES"):
    """Table des cotes, mesurées depuis le coin inférieur gauche de la face."""
    sh.txt(x, y, titre, size=6.8, fill=NUIT, weight="700", anchor="start",
           spacing="1.2")
    sh.txt(x, y + 16, "origine : coin supérieur gauche · X vers la droite, "
           "Y vers le bas", size=5.6, fill=GRIS, anchor="start")
    entetes = ("REPÈRE", "X (mm)", "Y (mm)", "COTE", "DESTINATION")
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
    """Gabarit 1:1 de la face avant."""
    sh = Sheet(1800, 900, print_mm=180)
    ox, oy = 180, 150
    _cadre_face(sh, ox, oy, "Face avant — gabarit 1:1",
                "boîtier aluminium 120 × 80 × 30 mm")

    _percage(sh, ox, oy, 14.0, 13.0, 6.5, "J1", "électrode A")
    _percage(sh, ox, oy, 30.0, 13.0, 6.5, "J2", "électrode B")
    _fenetre(sh, ox, oy, 58.0, 13.0, 25.0, 14.0, "DS5", "afficheur OLED")
    _percage(sh, ox, oy, 78.0, 6.5, 3.2, "DS2", "alim.", dessous=False)
    _percage(sh, ox, oy, 86.0, 6.5, 3.2, "DS3", "USB", dessous=False)
    _percage(sh, ox, oy, 94.0, 6.5, 3.2, "DS4", "défaut", dessous=False)
    _percage(sh, ox, oy, 86.0, 18.5, 7.0, "S1", "bouton")
    _percage(sh, ox, oy, 108.0, 13.0, 3.2, "M1", "fixation")

    _reglette(sh, ox, oy + FACE_H * UPMM + 90)
    _tableau_percages(sh, ox, oy + FACE_H * UPMM + 200, [
        ("J1", 14, 13, "Ø 6,5", "embase jack 3,5 mm — électrode A"),
        ("J2", 30, 13, "Ø 6,5", "embase jack 3,5 mm — électrode B"),
        ("DS5", 58, 13, "25 × 14", "fenêtre de l'afficheur OLED"),
        ("DS2", 78, 6.5, "Ø 3,2", "voyant d'alimentation, bicolore"),
        ("DS3", 86, 6.5, "Ø 3,2", "voyant de lien USB, bleu"),
        ("DS4", 94, 6.5, "Ø 3,2", "voyant de défaut, rouge"),
        ("S1", 86, 18.5, "Ø 7,0", "bouton-poussoir"),
        ("M1", 108, 13, "Ø 3,2", "vis de maintien de la face"),
    ])
    _avertissement_impression(sh, 1010, 560)
    sh.txt(1310, 852, f"{AUTEUR} · {SITE} · révision B", size=5.8, fill=GRIS)
    sh.save("gabarit-face-avant.svg")


def gab_face_arriere():
    """Gabarit 1:1 de la face arrière."""
    sh = Sheet(1800, 900, print_mm=180)
    ox, oy = 180, 150
    _cadre_face(sh, ox, oy, "Face arrière — gabarit 1:1",
                "boîtier aluminium 120 × 80 × 30 mm")

    _fenetre(sh, ox, oy, 20.0, 13.0, 10.0, 5.0, "J20", "USB-C")
    _percage(sh, ox, oy, 44.0, 13.0, 8.0, "J30", "bloc secteur")
    _percage(sh, ox, oy, 66.0, 13.0, 6.5, "J21", "MIDI TRS")
    _percage(sh, ox, oy, 88.0, 13.0, 4.2, "GND", "masse châssis")
    _percage(sh, ox, oy, 108.0, 13.0, 3.2, "M2", "fixation")

    _reglette(sh, ox, oy + FACE_H * UPMM + 90)
    _tableau_percages(sh, ox, oy + FACE_H * UPMM + 200, [
        ("J20", 20, 13, "10 × 5", "prise USB-C — ouverture rectangulaire"),
        ("J30", 44, 13, "Ø 8,0", "embase d'alimentation 2,1 mm"),
        ("J21", 66, 13, "Ø 6,5", "sortie MIDI TRS type A"),
        ("GND", 88, 13, "Ø 4,2", "plot de masse châssis, vis M4"),
        ("M2", 108, 13, "Ø 3,2", "vis de maintien de la face"),
    ])
    note(sh, 1010, 420, 700,
         ["Le plot de masse relie le boîtier à la masse analogique flottante,",
          "et à elle seule. Le relier à la masse USB rétablirait la boucle que",
          "toute la conception cherche à supprimer : c'est l'erreur de montage",
          "la plus fréquente, et elle ne se voit pas — elle s'entend, à 50 Hz."],
         title="LE PLOT DE MASSE", color=CUIVRE, fill=CUIV_P)
    _avertissement_impression(sh, 1010, 640)
    sh.txt(1310, 868, f"{AUTEUR} · {SITE} · révision B", size=5.8, fill=GRIS)
    sh.save("gabarit-face-arriere.svg")


def gab_carte():
    """Gabarit 1:1 du perçage du fond et de l'implantation mécanique."""
    sh = Sheet(1800, 1340, print_mm=180)
    ox, oy = 180, 150
    w, h = CARTE_L * UPMM, CARTE_H * UPMM
    sh.rect(ox, oy, w, h, fill="#F7F9F7", stroke=SEVE, sw=2.2, rx=6, dash="10 6")
    sh.txt(ox, oy - 52, "Fond du boîtier — gabarit 1:1", size=10, fill=NUIT,
           weight="700", anchor="start", family=SERIF)
    sh.txt(ox + w, oy - 52, "contour de la carte, 100 × 60 mm", size=6.4,
           fill=GRIS, anchor="end")

    # empreinte des connecteurs, tracée d'abord pour rester sous les perçages
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
           "les rectangles grisés sont les empreintes des connecteurs et des "
           "pièces hautes : vérifier leur dégagement avant de percer",
           size=6, fill=GRIS)

    _reglette(sh, ox, oy + h + 140)

    _tableau_percages(sh, ox, oy + h + 250, [
        ("F1", 4, 4, "Ø 3,2", "entretoise M3, hauteur 6 mm, PTFE — côté analogique"),
        ("F2", 96, 4, "Ø 3,2", "entretoise M3, hauteur 6 mm, PTFE — isolée"),
        ("F3", 4, 56, "Ø 3,2", "entretoise M3, hauteur 6 mm, PTFE — côté analogique"),
        ("F4", 96, 56, "Ø 3,2", "entretoise M3, hauteur 6 mm, PTFE — isolée"),
    ], titre="PERÇAGES DU FOND — origine : coin supérieur gauche de la carte")

    note(sh, 180, 1140, 760,
         ["Entretoises en PTFE, jamais en nylon : le nylon absorbe l'humidité et",
          "conduit assez, en surface, pour dégrader une mesure à 10¹⁵ ohms.",
          "Seules F1 et F3, du côté analogique, touchent un plan de masse ; F2 et F4",
          "restent isolées, sous peine de refermer la boucle ouverte par la fente."],
         title="LES ENTRETOISES NE SONT PAS NEUTRES", color=CUIVRE, fill=CUIV_P)
    _avertissement_impression(sh, 1000, 1140, 740)
    sh.txt(900, 1320, f"{AUTEUR} · {SITE} · révision B", size=5.8, fill=GRIS)
    sh.save("gabarit-carte.svg")


# =============================================================================
#  ENTRÉE  (doit rester en fin de fichier : insérer les figures AU-DESSUS)
# =============================================================================

# =============================================================================
#  RACCORDEMENT D'ENSEMBLE — PLANTE, BOÎTIER, ORDINATEUR, ÉNERGIE
# =============================================================================
def fig_raccordement():
    """Vue d'ensemble : ce qu'on relie à quoi, et d'où vient le courant."""
    sh = Sheet(980, 976, print_mm=125)
    sh.title("Raccordement d'ensemble",
             "L'ordinateur portable est toujours requis ; seule l'énergie a deux provenances")

    # ---- les trois éléments de la chaîne -----------------------------------
    py = 128
    bp = block(sh, 30, py, 250, 132, "LA PLANTE", "arbre, arbuste ou plante en pot",
               ["2 électrodes de mesure", "1 électrode de terre", "dans le substrat"],
               fill=SEVE_P, stroke=SEVE, sw=1.8)
    bb = block(sh, 366, py, 250, 132, "LE BOÎTIER", "PhytoSense One",
               ["conditionnement analogique", "conversion 24 bits", "horodatage"],
               fill="#fff", stroke=NUIT, sw=2.0)
    bo = block(sh, 700, py, 250, 132, "L'ORDINATEUR", "portable — indispensable",
               ["réglage de la carte", "enregistrement", "analyse et écoute"],
               fill=BLEU_P, stroke=BLEU, sw=1.8)

    # ---- liaisons : flèches entre les blocs, légendes AU-DESSOUS ------------
    sh.arrow(bp["r"][0] + 4, bp["r"][1], bb["l"][0] - 6, bb["l"][1], color=SEVE, sw=2.4)
    sh.arrow(bb["r"][0] + 4, bb["r"][1], bo["l"][0] - 6, bo["l"][1], color=BLEU, sw=2.4)

    ly = py + 158
    for x, col, titre, l1, l2 in (
            (200, SEVE, "LIAISON DE MESURE", "câble blindé RG-174 · 2 m au plus",
             "jack TRS 3,5 mm sur J1 — voir figure suivante"),
            (760, BLEU, "LIAISON DE COMMANDE", "un seul câble USB-C",
             "données de mesure et 5 V dans le même cordon")):
        sh.txt(x, ly, titre, size=6.4, fill=col, weight="700", spacing="0.8")
        sh.txt(x, ly + 18, l1, size=6.0, fill=INK)
        sh.txt(x, ly + 34, l2, size=5.9, fill=GRIS)

    # ---- bandeau : les provenances de l'énergie -----------------------------
    ey = 378
    sh.rect(30, ey, 920, 266, fill=OR_PL, stroke=OR, sw=1.4, rx=10, dash="8 5")
    sh.txt(490, ey + 26, "D'OÙ VIENT L'ÉNERGIE — AU CHOIX, ET SANS COUPURE AU PASSAGE",
           size=6.6, fill=OR, weight="700", spacing="1.2")

    opts = [
        ("A · PAR L'USB", "le plus simple",
         ["Un seul câble pour tout.", "500 mA disponibles,", "137 mA consommés.",
          "Vide la batterie du", "portable en séance longue."], SEVE),
        ("B · BLOC EXTERNE", "prioritaire",
         ["Bloc secteur 7 à 24 V", "sur la prise J30.", "Soulage le portable et",
          "écarte son 5 V bruyant", "de la chaîne de mesure."], CUIVRE),
        ("C · ACCUMULATEUR", "loin de toute prise",
         ["Li-Po 3,7 V 2 000 mAh", "et son module de charge.", "Ne tire rien du portable",
          "ni du secteur — utile", "pour une séance en forêt."], BLEU),
    ]
    for i, (titre, sous, lignes, col) in enumerate(opts):
        x = 58 + i * 300
        block(sh, x, ey + 46, 264, 192, titre, sous, lignes, fill="#fff",
              stroke=col, sw=1.7, tsize=7.6)

    # convergence vers le boîtier : une seule flèche, dans le couloir libre
    sh.arrow(490, ey - 6, 490, py + 142, color=OR, sw=2.6, marker="ahv")

    note(sh, 30, 674, 920,
         ["Les trois provenances peuvent être présentes en même temps. L'aiguilleur U62 donne la",
          "priorité au bloc externe, puis à l'USB, et bascule de l'une à l'autre en moins de vingt",
          "microsecondes : on débranche l'ordinateur du secteur en pleine séance sans perdre un",
          "échantillon. Aucune des trois ne dispense de l'ordinateur, qui reste le seul",
          "destinataire du flux de mesure."],
         title="RÈGLE — L'ÉNERGIE EST DOUBLE, LA LIAISON NE L'EST PAS",
         color=OR, fill=OR_PL)

    note(sh, 30, 842, 920,
         ["Ne jamais relier au secteur autre chose qu'un bloc d'alimentation marqué CE, à double",
          "isolation et à très basse tension de sécurité. Aucune partie de la carte n'est prévue",
          "pour la tension du réseau, et aucune ne doit l'être."],
         title="SÉCURITÉ", color=CUIVRE, fill=CUIV_P)

    sh.signer()
    sh.save("raccordement-ensemble.svg")


# =============================================================================
#  RACCORDEMENT DÉTAILLÉ — PLANTE / ARBRE VERS LE BOÎTIER
# =============================================================================
def fig_electrodes():
    """Le détail du raccordement : où poser, avec quoi, avec quel câble."""
    sh = Sheet(980, 1060, print_mm=125)
    sh.title("Raccordement des électrodes",
             "Où poser, avec quoi, et avec quel câble")

    # =====================================================================
    #  PANNEAU A — côté plante
    # =====================================================================
    sh.rect(30, 110, 440, 510, fill=SEVE_P, stroke=SEVE, sw=1.4, rx=10, dash="8 5")
    sh.txt(250, 136, "CÔTÉ PLANTE", size=6.6, fill=SEVE, weight="700", spacing="1.2")

    # tronc, ramure, feuillage
    sh.rect(226, 300, 44, 190, fill="#D8CBB4", stroke="#9C8A6E", sw=1.4, rx=4)
    sh.path("M248 302 C 248 250, 186 248, 186 214", stroke="#9C8A6E", sw=3.0)
    sh.path("M248 302 C 248 254, 316 252, 316 220", stroke="#9C8A6E", sw=3.0)
    sh.circle(186, 200, 28, fill=SEVE_C, stroke=SEVE, sw=1.4)
    sh.circle(316, 206, 28, fill=SEVE_C, stroke=SEVE, sw=1.4)
    sh.rect(126, 490, 244, 30, fill="#C7B79A", stroke="#9C8A6E", sw=1.2, rx=3)

    # points de contact, repérés par une pastille courte
    def contact(cx, cy, ref, col, tx, ty, anchor="middle"):
        sh.circle(cx, cy, 8.5, fill=col, stroke="#fff", sw=1.8)
        sh.line(cx, cy, tx, ty + 6, stroke=col, sw=1.0, dash="4 3")
        sh.txt(tx, ty, ref, size=6.8, fill=col, weight="700", anchor=anchor)

    contact(186, 200, "E1", CUIVRE, 186, 158)
    contact(248, 396, "E2", BLEU, 306, 388, "start")
    contact(248, 505, "E3", NUIT, 306, 497, "start")

    # légende des trois contacts, dans le bas du panneau
    leg = [(CUIVRE, "E1", "mesure — sous une feuille"),
           (BLEU,   "E2", "référence — tronc, 10 à 30 cm plus bas"),
           (NUIT,   "E3", "terre — tige inox 316L dans le substrat")]
    for i, (col, ref, txt) in enumerate(leg):
        y = 552 + i * 24
        sh.circle(58, y - 4, 6, fill=col, stroke="none", sw=0)
        sh.txt(74, y, ref, size=6.2, fill=col, weight="700", anchor="start")
        sh.txt(104, y, txt, size=5.8, fill=INK, anchor="start")

    # =====================================================================
    #  PANNEAU B — le câble, vu dénudé
    # =====================================================================
    sh.rect(500, 110, 450, 250, fill="#fff", stroke=NUIT, sw=1.6, rx=10)
    sh.txt(725, 136, "LE CÂBLE", size=6.6, fill=NUIT, weight="700", spacing="1.2")

    yc = 262
    sh.rect(522, yc - 19, 160, 38, fill="#D7D7C6", stroke=INK, sw=1.3, rx=4)
    sh.rect(682, yc - 13, 68, 26, fill=SEVE_C, stroke=SEVE, sw=1.3, rx=3)
    sh.rect(750, yc - 8, 52, 16, fill=IVOIRE, stroke=INK, sw=1.1, rx=2)
    sh.line(802, yc, 862, yc, stroke=CUIVRE, sw=4.0)

    # repères : deux au-dessus, deux au-dessous, jamais sur la même ligne
    for x, ylab, lab, col, sens in ((602, yc + 52, "gaine extérieure", GRIS, 1),
                                    (716, yc - 38, "tresse → BAGUE (garde)", SEVE, -1),
                                    (776, yc + 52, "diélectrique", GRIS, 1),
                                    (832, yc - 62, "âme → POINTE (mesure)", CUIVRE, -1)):
        sh.line(x, yc + sens * 22, x, ylab - sens * 12, stroke=col, sw=0.9, dash="3 3")
        sh.txt(x, ylab, lab, size=6.0, fill=col, weight="700")

    sh.txt(725, 336, "RG-174 · Belden 8216 · 2 m au plus", size=6.0, fill=INK,
           family=MONO)

    # =====================================================================
    #  PANNEAU C — le connecteur
    # =====================================================================
    sh.rect(500, 384, 450, 236, fill="#fff", stroke=OR, sw=1.6, rx=10)
    sh.txt(725, 410, "LE CONNECTEUR — J1 · JACK TRS 3,5 mm", size=6.6, fill=OR,
           weight="700", spacing="1.0")

    jx, jy = 548, 442
    sh.rect(jx, jy, 300, 30, fill="#E8E4D6", stroke=INK, sw=1.4, rx=4)
    for x0, x1, col in ((jx + 4, jx + 60, CUIVRE), (jx + 68, jx + 146, SEVE),
                        (jx + 154, jx + 296, BLEU)):
        sh.rect(x0, jy + 4, x1 - x0, 22, fill=col, stroke="none", sw=0, rx=2)
    sh.circle(jx + 300, jy + 15, 15, fill="#E8E4D6", stroke=INK, sw=1.4)

    broches = [(CUIVRE, "T · pointe", "E1 — électrode de mesure"),
               (SEVE,   "R · bague",  "garde et tresse du câble"),
               (BLEU,   "S · corps",  "E2 — électrode de référence")]
    for i, (col, nom, role) in enumerate(broches):
        y = 510 + i * 26
        sh.rect(jx, y - 11, 16, 14, fill=col, stroke="none", sw=0, rx=2)
        sh.txt(jx + 26, y, nom, size=6.2, fill=col, weight="700", anchor="start")
        sh.txt(jx + 128, y, role, size=6.0, fill=INK, anchor="start")

    sh.txt(725, 600, "La tresse va sur la bague, jamais sur le corps.",
           size=6.2, fill=CUIVRE, weight="700")

    # =====================================================================
    #  CONSEILS
    # =====================================================================
    note(sh, 30, 652, 920,
         ["Électrodes Ag/AgCl adhésives d'électrocardiographie : le contact le plus stable, plusieurs",
          "heures sans dérive. Une noisette de gel conducteur sans chlorure prolonge encore la tenue.",
          "Sur feuille épaisse ou sur écorce, pince crocodile à mors cuivre garnie d'une éponge humide.",
          "Deux électrodes espacées de 10 à 30 cm sur le même individu ; jamais sur deux plantes.",
          "Câble de deux mètres au plus, fixé par un serre-câble à vingt centimètres du contact."],
         title="CE QU'IL FAUT FAIRE", color=SEVE, fill=SEVE_P)

    note(sh, 30, 832, 920,
         ["Pas d'aluminium ménager : il s'oxyde en quelques heures et fabrique une pile parasite.",
          "Pas d'aiguille plantée dans le tronc : blessure inutile, et le signal n'y gagne rien.",
          "Pas de câble non blindé ni de rallonge : chaque mètre nu ajoute le réseau à cinquante hertz.",
          "Pas de tresse reliée à la masse du boîtier : c'est la faute la plus fréquente, et elle fait",
          "perdre d'un seul coup tout le bénéfice de l'étage électrométrique."],
         title="CE QU'IL NE FAUT PAS FAIRE", color=CUIVRE, fill=CUIV_P)

    sh.signer()
    sh.save("raccordement-electrodes.svg")



# =============================================================================
#  RACCORDEMENT FEUILLE / RACINE — et l'électrode de substrat
# =============================================================================
def fig_feuille_racine():
    sh = Sheet(980, 1310, print_mm=125)
    sh.title("Brancher une feuille et une racine",
             "Le montage le plus courant — et le choix de l'électrode de substrat")

    # =====================================================================
    #  A — LE MONTAGE, EN COUPE
    # =====================================================================
    sh.rect(30, 108, 470, 560, fill=SEVE_P, stroke=SEVE, sw=1.4, rx=10, dash="8 5")
    sh.txt(265, 134, "LE MONTAGE, EN COUPE", size=6.6, fill=SEVE, weight="700",
           spacing="1.2")

    #  le pot, coupé
    sh.path("M150 430 L 178 620 L 352 620 L 380 430 Z", fill="#E4D9C4",
            stroke="#9C8A6E", sw=1.6)
    sh.path("M150 430 L 380 430", stroke="#9C8A6E", sw=1.6)
    #  le substrat
    sh.path("M158 448 L 182 606 L 348 606 L 372 448 Z", fill="#C2A882",
            stroke="none", sw=0)
    #  la tige et les feuilles
    sh.path("M265 430 L 265 250", stroke=SEVE, sw=4.0)
    sh.path("M265 300 C 225 286, 205 262, 202 236", stroke=SEVE, sw=2.6)
    sh.path("M265 336 C 305 322, 326 300, 330 274", stroke=SEVE, sw=2.6)
    for cx, cy, rot in ((196, 228, -28), (336, 266, 26)):
        sh.add(f'<g transform="rotate({rot},{cx},{cy})">'
               f'<ellipse cx="{cx}" cy="{cy}" rx="34" ry="17" fill="{SEVE_C}" '
               f'stroke="{SEVE}" stroke-width="1.4"/></g>')
    #  les racines
    for dx in (-60, -26, 0, 26, 60):
        sh.path(f"M265 432 C {265+dx*0.4} 470, {265+dx} 520, {265+dx*1.1} 588",
                stroke="#A58A5E", sw=1.6)

    #  E1 — sur la feuille
    sh.circle(196, 228, 9, fill=CUIVRE, stroke="#fff", sw=2.0)
    sh.line(196, 228, 120, 192, stroke=CUIVRE, sw=1.0, dash="4 3")
    sh.txt(52, 182, "E1", size=7.0, fill=CUIVRE, weight="700", anchor="start")
    sh.txt(52, 196, "pastille Ag/AgCl", size=5.6, fill=INK, anchor="start")
    sh.txt(52, 208, "sous la feuille", size=5.6, fill=GRIS, anchor="start")

    #  E2 — dans le substrat
    sh.rect(316, 452, 7, 118, fill="#BFC4C8", stroke=INK, sw=1.2, rx=2)
    sh.circle(319, 452, 8, fill=NUIT, stroke="#fff", sw=2.0)
    sh.line(319, 452, 416, 396, stroke=NUIT, sw=1.0, dash="4 3")
    sh.txt(484, 384, "E2", size=7.0, fill=NUIT, weight="700", anchor="end")
    sh.txt(484, 398, "tige inox 316L", size=5.6, fill=INK, anchor="end")
    sh.txt(484, 410, "3 à 5 cm de profondeur", size=5.6, fill=GRIS, anchor="end")

    #  les cotes
    sh.line(265, 640, 319, 640, stroke=BLEU, sw=1.0)
    sh.txt(292, 656, "≥ 5 cm de la tige", size=5.8, fill=BLEU)
    sh.line(330, 452, 330, 570, stroke=BLEU, sw=1.0, dash="3 3")
    sh.txt(352, 516, "3–5 cm", size=5.8, fill=BLEU, anchor="start")

    #  ce que l'on mesure
    note(sh, 30, 690, 920,
         ["La tension mesurée est celle du chemin feuille → tige → racines → substrat → électrode.",
          "Elle ne dit donc pas « la feuille » : elle dit l'ensemble plante + substrat + contacts.",
          "Un arrosage la déplace autant qu'un changement de la plante — c'est la limite du montage,",
          "et elle doit être écrite dans le carnet de séance."],
         title="CE QUE MESURE CE MONTAGE", color=BLEU, fill=BLEU_P)

    # =====================================================================
    #  B — L'ÉLECTRODE DE SUBSTRAT : QUOI PLANTER DANS LA TERRE
    # =====================================================================
    sh.rect(516, 108, 434, 560, fill="#fff", stroke=NUIT, sw=1.6, rx=10)
    sh.txt(733, 134, "QUE PLANTER DANS LA TERRE", size=6.6, fill=NUIT,
           weight="700", spacing="1.2")

    lignes = [
        (SEVE,   "Inox 316L", "tige ø 4–6 mm, 60–100 mm",
         "Le choix par défaut : stable, inerte, increvable.", True),
        (SEVE,   "Graphite", "mine ø 5 mm ou charbon",
         "Peu polarisable, aucun ion métallique. Fragile.", True),
        (OR,     "Ag/AgCl + pont salin", "agar 3 % + KCl 3 mol/L",
         "La référence de laboratoire : dérive minimale.", True),
        (CUIVRE, "Laiton, cuivre", "—",
         "Pile galvanique avec E1, et toxique pour les racines.", False),
        (CUIVRE, "Acier galvanisé", "—",
         "Le zinc se dissout : décalage énorme et croissant.", False),
        (CUIVRE, "Aluminium", "—",
         "S'oxyde en quelques heures ; mesure instable.", False),
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

    #  le détail du pont salin
    sh.rect(540, 548, 386, 104, fill=OR_PL, stroke=OR, sw=1.3, rx=6)
    sh.txt(733, 570, "LE PONT SALIN, EN DEUX MOTS", size=6.0, fill=OR,
           weight="700", spacing="0.8")
    sh.rect(566, 584, 16, 54, fill="#EDE7D4", stroke=INK, sw=1.2, rx=3)
    sh.rect(568, 592, 12, 44, fill=BLEU_P, stroke="none", sw=0)
    sh.line(574, 584, 574, 566, stroke="#BFC4C8", sw=3.0)
    sh.txt(596, 596, "tube rempli d'agar-agar salé,", size=5.6, fill=INK, anchor="start")
    sh.txt(596, 610, "fil d'argent chloruré à l'intérieur,", size=5.6, fill=INK, anchor="start")
    sh.txt(596, 624, "l'extrémité seule touche la terre.", size=5.6, fill=INK, anchor="start")
    sh.txt(596, 640, "Aucun métal ne touche les racines.", size=5.6, fill=SEVE,
           anchor="start", weight="700")

    # =====================================================================
    #  C — LA RÈGLE QUI COMPTE
    # =====================================================================
    note(sh, 30, 852, 920,
         ["LE MÊME MÉTAL AUX DEUX BOUTS. Deux métaux différents dans un milieu humide font une pile :",
          "on mesure alors sa tension — quelques dizaines de millivolts — et sa dérive avec l'humidité,",
          "bien plus que la plante. Si E1 est une pastille Ag/AgCl, la meilleure E2 est un pont salin ;",
          "à défaut, inox des deux côtés. La ligne de base retire le décalage constant, jamais sa dérive.",
          "",
          "SUBSTRAT HUMIDE, jamais détrempé ni sec : sec, l'impédance monte et le bruit avec elle.",
          "Quelques gouttes d'eau avant la séance suffisent — pas d'eau salée, qui brûle les racines.",
          "",
          "MÊME PLACE D'UNE SÉANCE À L'AUTRE si l'on veut comparer : noter la profondeur, la distance",
          "à la tige et la feuille choisie. Sans cela, deux séances ne se comparent pas."],
         title="TROIS RÈGLES, ET RIEN DE PLUS", color=SEVE, fill=SEVE_P)

    note(sh, 30, 1146, 920,
         ["Ne jamais planter l'électrode dans le tronc ou dans une racine : la blessure ne se referme",
          "pas et le signal n'y gagne rien. Ne jamais relier l'électrode de substrat à la terre du",
          "secteur — ni à la masse du boîtier. Ne jamais employer d'engrais liquide juste avant une",
          "séance : la conductivité change pendant des heures et masque tout le reste."],
         title="CE QU'IL NE FAUT PAS FAIRE", color=CUIVRE, fill=CUIV_P)

    sh.signer()
    sh.save("raccordement-feuille-racine.svg")


# =============================================================================
#  LES SIX DESCRIPTEURS — ce que chaque représentation montre
# =============================================================================
def _bruit(i, graine=7):
    """Pseudo-aléa déterministe : la planche doit être reproductible au bit."""
    x = math.sin((i + 1) * 12.9898 + graine * 78.233) * 43758.5453
    return (x - math.floor(x)) * 2.0 - 1.0


def _mini_cadre(sh, x, y, w, h, titre, verdict, couleur=SEVE):
    sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="#fff" '
           f'stroke="{TRAIT}" stroke-width="1.2"/>')
    sh.add(f'<rect x="{x}" y="{y}" width="{w}" height="21" rx="5" '
           f'fill="{couleur}" opacity="0.14"/>')
    sh.txt(x + 10, y + 15, titre, size=7.0, fill=couleur, anchor="start",
           weight="700")
    #  Trente-deux caractères tiennent dans la largeur d'une vignette : au-delà
    #  la ligne dépasse le cadre, ce qui ne se voit qu'à l'impression.
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
    sh.title("Six regards sur le même signal",
             "La même minute d'enregistrement, vue par six outils — et ce que "
             "chacun permet de dire")

    L, H = 296, 188
    X = [30, 342, 654]
    Y = [72, 292]

    # --- 1. domaine temporel ------------------------------------------------
    aire = _mini_cadre(sh, X[0], Y[0], L, H, "Forme d'onde",
                       ["Rien n'y est calculé,",
                        "donc rien n'y est perdu."], SEVE)
    temporel = [0.6 * math.sin(i / 34.0) + 0.12 * _bruit(i)
                + (1.6 * math.exp(-((i - 108) / 9.0) ** 2))
                for i in range(160)]
    _courbe(sh, aire, temporel, SEVE, 1.4)

    # --- 2. domaine fréquentiel ---------------------------------------------
    aire = _mini_cadre(sh, X[1], Y[0], L, H, "Spectre (FFT)",
                       ["Les périodicités, et le réseau.",
                        "Suppose le signal stationnaire :",
                        "il ne l'est jamais longtemps."], BLEU)
    spectre = []
    for i in range(160):
        f = 0.02 * (i + 1)
        v = 1.0 / (f ** 0.8) + 0.25 * abs(_bruit(i, 3))
        if 96 <= i <= 100:                              # la raie du réseau
            v += 9.0 * math.exp(-((i - 98) / 1.1) ** 2)
        spectre.append(math.log10(v + 0.05))
    _courbe(sh, aire, spectre, BLEU, 1.3)
    sh.txt(aire[0] + aire[2] * 0.62, aire[1] + 10, "50 Hz", size=5.6,
           fill=CUIVRE, anchor="start")

    # --- 3. ondelettes ------------------------------------------------------
    aire = _mini_cadre(sh, X[2], Y[0], L, H, "Ondelettes (scalogramme)",
                       ["Situe dans le temps ce que",
                        "la FFT se contente de moyenner.",
                        "La mieux adaptée à ce signal."], OR)
    x0, y0, w, h = aire
    x0 += 26                                          # gouttière des repères
    w -= 26
    nc, nl = 26, 10
    for c in range(nc):
        for l in range(nl):
            #  Une bouffée brève en haute fréquence, un fond lent en bas.
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
                       ["Compresse le spectre en",
                        "quelques nombres comparables.",
                        "Compare ; ne mesure rien."], SEVE)
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
    aire = _mini_cadre(sh, X[1], Y[1], L, H, "Prédiction linéaire (LPC)",
                       ["Enveloppe et résonances du",
                        "système de mesure. Pas des",
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
                       ["Révèle les périodicités lentes",
                        "qu'une dérive de fond masque.",
                        "L'abscisse est une quéfrence."], BLEU)
    cep = [0.12 * _bruit(i, 23) + 1.5 * math.exp(-((i - 104) / 2.6) ** 2)
           + 0.55 * math.exp(-((i - 52) / 2.2) ** 2) for i in range(160)]
    _courbe(sh, aire, cep, BLEU, 1.3)
    x0, y0, w, h = aire
    sh.txt(x0 + w * 104 / 160, y0 + 8, "période détectée", size=5.6,
           fill=BLEU, anchor="middle")

    note(sh, 30, 508, 920,
         ["Aucune de ces représentations ne décode quoi que ce soit : elles décrivent la forme du",
          "signal, plus finement qu'une courbe. Les constantes des outils de la parole — largeur des",
          "fenêtres, bornes du banc de Mel, ordre de prédiction — sont transposées d'après la",
          "fréquence d'échantillonnage réelle, cinq décades plus bas que la voix humaine : une trame",
          "de MFCC dure ici huit secondes, non vingt-cinq millisecondes."],
         title="CE QUE CES OUTILS FONT, ET CE QU'ILS NE FONT PAS",
         color=SEVE, fill=SEVE_P)
    sh.signer()
    sh.save("logiciel-descripteurs.svg")


# =============================================================================
#  LE MODE VOCAL — des mots au lieu des notes
# =============================================================================
def fig_lexique():
    sh = Sheet(980, 836, print_mm=125)
    sh.title("Du microvolt au mot",
             "Le mode vocal, axe par axe — et ce que l'utilisateur apporte "
             "lui-même")

    mesures = [("Sens de la pente", "montée ou descente"),
               ("Amplitude", "en écarts-types"),
               ("Temps écoulé", "depuis l'énoncé précédent"),
               ("Gravité du spectre", "centre de gravité, en hertz")]
    registres = [("verbe", "cinq mots, du faible au fort"),
                 ("intensité", "l'adverbe"),
                 ("tempo", "la circonstance de temps"),
                 ("couleur", "la qualification")]

    for i, (t, u) in enumerate(mesures):
        block(sh, 30, 104 + i * 84, 250, 62, t, u, fill="#fff", stroke=SEVE,
              sw=1.4, tsize=7.0)
    for i, (t, u) in enumerate(registres):
        block(sh, 360, 104 + i * 84, 250, 62, t, u, fill=OR_PL, stroke=OR,
              sw=1.4, tsize=7.0)
        sh.arrow(284, 135 + i * 84, 356, 135 + i * 84, color=OR, sw=1.5)
        sh.arrow(614, 135 + i * 84, 686, 306, color=OR, sw=1.1)

    #  Le sujet ne vient d'aucune mesure : c'est le point à ne pas cacher.
    block(sh, 30, 452, 250, 62, "Sujet", "choisi par l'utilisateur",
          fill=CUIV_P, stroke=CUIVRE, sw=1.6, tsize=7.0)
    sh.arrow(284, 483, 356, 483, color=CUIVRE, sw=1.5)
    block(sh, 360, 452, 250, 62, "sujet", "qui parle — rien ne le mesure",
          fill=CUIV_P, stroke=CUIVRE, sw=1.6, tsize=7.0)
    sh.arrow(614, 483, 686, 372, color=CUIVRE, sw=1.1)

    block(sh, 690, 276, 260, 122, "Grammaire", "un gabarit tiré au sort",
          ["minimale · télégraphique", "contemplative · descriptive"],
          fill=SEVE_P, stroke=SEVE, sw=1.6, tsize=7.6)
    sh.arrow(820, 402, 820, 446, color=SEVE, sw=1.6)

    sh.add(f'<rect x="690" y="450" width="260" height="96" rx="6" fill="#fff" '
           f'stroke="{NUIT}" stroke-width="1.6"/>')
    sh.txt(820, 478, "« La feuille frémit", size=8.2, fill=NUIT,
           family=SERIF, style="italic")
    sh.txt(820, 498, "doucement, sourd »", size=8.2, fill=NUIT,
           family=SERIF, style="italic")
    sh.txt(820, 520, "σ=4,1 · pente +2e−5", size=5.2, fill=GRIS, family=MONO)
    sh.txt(820, 534, "Δt=38 s · f=0,21 Hz", size=5.2, fill=GRIS, family=MONO)
    sh.txt(820, 560, "chaque énoncé porte les valeurs", size=5.6, fill=GRIS)
    sh.txt(820, 574, "qui l'ont déclenché", size=5.6, fill=GRIS)

    note(sh, 30, 600, 920,
         ["La plante n'émet pas de mots et n'a pas de langage : rien dans son signal électrique ne",
          "correspond à un vocabulaire. Ce dispositif applique des règles explicites, réglables et",
          "consignées, qui associent une région de l'espace des descripteurs à un mot choisi par",
          "l'utilisateur. Le mot qui sort est donc dans le dictionnaire de celui qui l'a écrit : il dit",
          "quelque chose du signal — intensité, sens de variation, rythme, couleur spectrale — et",
          "rien de ce que « pense » la plante. Le dialogue qui s'installe est un dialogue entre",
          "l'utilisateur et sa propre grille de lecture ; il peut être fécond, à condition de le savoir."],
         title="CE N'EST PAS UNE TRADUCTION", color=CUIVRE, fill=CUIV_P)
    sh.signer()
    sh.save("logiciel-lexique.svg")



def main():
    print("• Génération des planches de la carte PhytoSense…")
    n = 0
    for nom, fn in sorted(globals().items()):
        if callable(fn) and nom.split("_")[0] in ("fig", "pl", "gab"):
            fn()
            n += 1
    print(f"✓ {n} planches générées")


if __name__ == "__main__":
    main()
