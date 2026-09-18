#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/assets/svg/gen_sch.py
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
Générateur de SCHÉMAS ÉLECTRONIQUES — « L'Arbre qui Parle ».

Symboles à l'européenne (CEI 60617) : résistances rectangulaires, masses en
peigne, sauts de fil (« hops ») aux croisements sans connexion.

Autonome : ne dépend pas de gen.py, afin que les deux générateurs évoluent
séparément sans risque de collision.

PROVENANCE DES SCHÉMAS
  · sch-biodata-555 .......... relevé FIDÈLE du netlist GalvShield_005.sch
                               (Eagle) du dépôt electricityforprogress/
                               BiodataSonificationBreadboardKit — licence MIT.
                               Netlist extraite par analyse du XML Eagle.
  · sch-electrophysio-ina333 . schéma d'application composé d'après les
                               datasheets TI INA333 / ADS1115 et ADI ADuM1251.
  · sch-bus-capteurs-esp32 ... schéma d'application (datasheets BME280,
                               BH1750, SCD41, DS18B20).
  · sch-alim-solaire ......... schéma d'application (CN3791, TPS63020).
  · sch-granier-tdp .......... principe Granier 1985 + ADS1220.

Usage : python3 gen_sch.py
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- Palette (identique à book.css) -----------------------------------------
NUIT   = "#0E2A22"
SEVE   = "#3F7D5A"
SEVE_C = "#6FA98A"
OR     = "#B08528"
OR_CL  = "#E0C073"
GRIS   = "#6B7A72"
TRAIT  = "#D9D9C6"
BLEU   = "#2F5E86"
CUIVRE = "#A8552E"
FIL    = "#23302C"

TEXT_SCALE = 1.30
TEXT_MIN   = 9.6
HEAD       = 56       # hauteur du bandeau de titre d'un boîtier


def esc(s):
    return re.sub(r"&(?!(?:amp|lt|gt|quot|apos|#\d+|#x[0-9a-fA-F]+);)", "&amp;", str(s))


def write(name, body, w, h, bg="#FFFFFF"):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
           f'width="{w}" height="{h}">\n{rect}\n{body}\n</svg>\n')
    with open(os.path.join(HERE, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"  · {name}  ({w}×{h})")


def txt(x, y, s, size=10, fill=NUIT, anchor="middle", family="Lato, sans-serif",
        weight="400", style="normal", spacing="0"):
    size = round(max(size * TEXT_SCALE, TEXT_MIN), 2)
    return (f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" '
            f'fill="{fill}" text-anchor="{anchor}" font-weight="{weight}" '
            f'font-style="{style}" letter-spacing="{spacing}">{esc(s)}</text>')


def title(x, y, s):
    return txt(x, y, s, size=13, fill=SEVE, weight="700", spacing="1.5")


# =============================================================================
#  PRIMITIVES
# =============================================================================
def w_(pts, color=FIL, sw=1.7, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    p = " ".join(f"{x},{y}" for x, y in pts)
    return (f'<polyline points="{p}" fill="none" stroke="{color}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round"{d}/>')


def dot(x, y, color=FIL, r=3.6):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>'


def hop(x, y, r=7):
    """Saut de fil : croisement SANS connexion, sur un fil horizontal."""
    return (f'<path d="M{x-r},{y} A{r},{r} 0 0 1 {x+r},{y}" fill="none" '
            f'stroke="{FIL}" stroke-width="1.7"/>')


def res_h(x, y, ref="", val="", w=48, h=17):
    """Résistance horizontale ; (x,y) = extrémité gauche du corps."""
    o = [f'<rect x="{x}" y="{y-h/2}" width="{w}" height="{h}" rx="1.5" '
         f'fill="#FFFFFF" stroke="{FIL}" stroke-width="1.7"/>']
    if ref:
        o.append(txt(x + w / 2, y - h / 2 - 7, ref, size=8.4, fill=BLEU, weight="700"))
    if val:
        o.append(txt(x + w / 2, y + h / 2 + 16, val, size=8.4, fill=NUIT))
    return "".join(o)


def res_v(x, y, ref="", val="", h=48, w=17, side=1):
    """Résistance verticale ; (x,y) = extrémité HAUTE du corps.
    side = +1 → étiquettes à droite, −1 → à gauche."""
    o = [f'<rect x="{x-w/2}" y="{y}" width="{w}" height="{h}" rx="1.5" '
         f'fill="#FFFFFF" stroke="{FIL}" stroke-width="1.7"/>']
    dx, a = w / 2 + 8, ("start" if side > 0 else "end")
    if ref:
        o.append(txt(x + side * dx, y + h / 2 - 3, ref, size=8.4, fill=BLEU,
                     weight="700", anchor=a))
    if val:
        o.append(txt(x + side * dx, y + h / 2 + 11, val, size=8.4, fill=NUIT, anchor=a))
    return "".join(o)


def cap_v(x, y, ref="", val="", side=1, pol=False, pw=26):
    """Condensateur vertical ; (x,y) = haut. Hauteur totale = 30."""
    ya, yb = y + 12, y + 20
    o = [w_([(x, y), (x, ya)]),
         f'<line x1="{x-pw/2}" y1="{ya}" x2="{x+pw/2}" y2="{ya}" stroke="{FIL}" '
         f'stroke-width="2.4"/>']
    if pol:
        o.append(f'<path d="M{x-pw/2},{yb+4} Q{x},{yb-5} {x+pw/2},{yb+4}" fill="none" '
                 f'stroke="{FIL}" stroke-width="2.4"/>')
        # le « + » se place à l'OPPOSÉ des étiquettes, sinon il les chevauche
        o.append(txt(x - side * (pw / 2 + 8), ya - 4, "+", size=9.5, fill=FIL))
    else:
        o.append(f'<line x1="{x-pw/2}" y1="{yb}" x2="{x+pw/2}" y2="{yb}" '
                 f'stroke="{FIL}" stroke-width="2.4"/>')
    o.append(w_([(x, yb + 4), (x, y + 30)]))
    dx, a = pw / 2 + 8, ("start" if side > 0 else "end")
    if ref:
        o.append(txt(x + side * dx, ya + 1, ref, size=8.4, fill=BLEU, weight="700", anchor=a))
    if val:
        o.append(txt(x + side * dx, ya + 14, val, size=8.4, fill=NUIT, anchor=a))
    return "".join(o)


def gnd(x, y, label=None):
    o = [w_([(x, y), (x, y + 10)])]
    for i, hw in enumerate((13, 8.5, 4)):
        yy = y + 10 + i * 4.5
        o.append(f'<line x1="{x-hw}" y1="{yy}" x2="{x+hw}" y2="{yy}" '
                 f'stroke="{FIL}" stroke-width="2.2"/>')
    if label:
        o.append(txt(x, y + 40, label, size=7.8, fill=GRIS))
    return "".join(o)


def vcc(x, y, label="+3V3"):
    """Rail d'alimentation ; (x,y) = point de connexion, le symbole monte."""
    return "".join([
        w_([(x, y), (x, y - 13)], CUIVRE),
        f'<line x1="{x-14}" y1="{y-13}" x2="{x+14}" y2="{y-13}" stroke="{CUIVRE}" '
        f'stroke-width="2.4"/>',
        txt(x, y - 20, label, size=8.4, fill=CUIVRE, weight="700"),
    ])


def ic(x, y, w, name, sub="", left=(), right=(), top=(), bottom=(), lead=26,
       fill="#FBFAF4", pad=42):
    """Boîtier. left/right = [(broche, nom, y_absolu)] ; top/bottom = [(br, nom, x)].

    Garde-fou : toute broche latérale placée dans le bandeau de titre lève une
    erreur — c'est la cause n°1 de chevauchement dans les planches.
    Renvoie (svg, pins) ; pins[nom] = (x, y) du BOUT de la patte.
    """
    ys = [p[2] for p in left] + [p[2] for p in right]
    for py in ys:
        if py < y + HEAD:
            raise ValueError(f"{name}: broche à y={py} dans le bandeau "
                             f"(minimum {y + HEAD})")
    h = (max(ys) - y + pad) if ys else 90
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" '
         f'stroke="{NUIT}" stroke-width="2.1"/>',
         txt(x + w / 2, y + 25, name, size=13.5, fill=NUIT, weight="700",
             family="Cormorant Garamond, serif")]
    if sub:
        o.append(txt(x + w / 2, y + 41, sub, size=8, fill=GRIS, style="italic"))
    pins = {}
    for num, nm, py in left:
        o.append(w_([(x - lead, py), (x, py)]))
        o.append(txt(x + 8, py + 3.6, nm, size=8.6, anchor="start"))
        if num:
            o.append(txt(x - 6, py - 6, str(num), size=7.2, fill=GRIS, anchor="end"))
        pins[nm] = (x - lead, py)
    for num, nm, py in right:
        o.append(w_([(x + w, py), (x + w + lead, py)]))
        o.append(txt(x + w - 8, py + 3.6, nm, size=8.6, anchor="end"))
        if num:
            o.append(txt(x + w + 6, py - 6, str(num), size=7.2, fill=GRIS, anchor="start"))
        pins[nm] = (x + w + lead, py)
    for num, nm, px in top:
        o.append(w_([(px, y - lead), (px, y)]))
        if nm:
            o.append(txt(px + 16, y - 10, nm, size=8.2, fill=GRIS, anchor="start"))
        pins[nm] = (px, y - lead)
    for num, nm, px in bottom:
        o.append(w_([(px, y + h), (px, y + h + lead)]))
        if nm:
            o.append(txt(px + 16, y + h + 14, nm, size=8.2, fill=GRIS, anchor="start"))
        pins[nm] = (px, y + h + lead)
    return "".join(o), pins


def pot_v(x, y, ref="", val="", h=52):
    """Potentiomètre : corps vertical (x,y=haut) + curseur à gauche.
    Renvoie (svg, {'haut':…, 'bas':…, 'curseur':…})."""
    o = [f'<rect x="{x-9}" y="{y}" width="18" height="{h}" rx="1.5" fill="#FFFFFF" '
         f'stroke="{FIL}" stroke-width="1.7"/>']
    ym = y + h / 2
    o.append(w_([(x - 34, ym), (x - 16, ym)]))
    o.append(f'<path d="M{x-16},{ym-6} L{x-16},{ym+6} L{x-9},{ym} z" fill="{FIL}"/>')
    if ref:
        o.append(txt(x + 15, ym - 3, ref, size=8.4, fill=BLEU, weight="700", anchor="start"))
    if val:
        o.append(txt(x + 15, ym + 11, val, size=8.4, anchor="start"))
    return "".join(o), {"haut": (x, y), "bas": (x, y + h), "curseur": (x - 34, ym)}


def switch_v(x, y, ref=""):
    """Interrupteur (contact travail) vertical ; (x,y)=haut, hauteur 34."""
    o = [w_([(x, y), (x, y + 6)]),
         f'<circle cx="{x}" cy="{y+8}" r="2.6" fill="{FIL}"/>',
         f'<circle cx="{x}" cy="{y+26}" r="2.6" fill="{FIL}"/>',
         w_([(x, y + 28), (x, y + 34)]),
         w_([(x, y + 26), (x + 13, y + 6)])]
    if ref:
        o.append(txt(x - 10, y + 20, ref, size=8.4, fill=BLEU, weight="700", anchor="end"))
    return "".join(o)


def reed(x, y, ref=""):
    """Contact ILS (reed) horizontal ; (x,y) = borne gauche, longueur 56."""
    o = [w_([(x, y), (x + 12, y)]),
         w_([(x + 44, y), (x + 56, y)]),
         f'<circle cx="{x+14}" cy="{y}" r="2.6" fill="{FIL}"/>',
         f'<circle cx="{x+42}" cy="{y}" r="2.6" fill="{FIL}"/>',
         w_([(x + 14, y), (x + 42, y - 11)]),
         f'<ellipse cx="{x+28}" cy="{y-2}" rx="24" ry="13" fill="none" '
         f'stroke="{GRIS}" stroke-width="1.1"/>']
    if ref:
        o.append(txt(x + 28, y - 22, ref, size=8.2, fill=GRIS))
    return "".join(o)


def diode(x, y, ref=""):
    """Diode horizontale (anode à gauche) ; (x,y) = anode, longueur 34."""
    o = [w_([(x, y), (x + 10, y)]),
         f'<path d="M{x+10},{y-10} L{x+10},{y+10} L{x+26},{y} z" fill="#FFFFFF" '
         f'stroke="{FIL}" stroke-width="1.8"/>',
         f'<line x1="{x+26}" y1="{y-10}" x2="{x+26}" y2="{y+10}" stroke="{FIL}" '
         f'stroke-width="2.4"/>',
         w_([(x + 26, y), (x + 34, y)])]
    if ref:
        o.append(txt(x + 17, y - 17, ref, size=8.4, fill=BLEU, weight="700"))
    return "".join(o)


def led_v(x, y, ref="", color=OR):
    """LED verticale (anode en haut) ; (x,y) = anode, hauteur 36."""
    o = [w_([(x, y), (x, y + 10)]),
         f'<path d="M{x-10},{y+10} L{x+10},{y+10} L{x},{y+26} z" fill="#FFFFFF" '
         f'stroke="{FIL}" stroke-width="1.7"/>',
         f'<line x1="{x-10}" y1="{y+26}" x2="{x+10}" y2="{y+26}" stroke="{FIL}" '
         f'stroke-width="2.4"/>',
         w_([(x, y + 26), (x, y + 36)])]
    for k in (0, 1):
        x0, y0 = x + 13 + k * 8, y + 17 - k * 5
        o.append(f'<line x1="{x0}" y1="{y0}" x2="{x0+9}" y2="{y0-9}" stroke="{color}" '
                 f'stroke-width="1.7"/>')
        o.append(f'<path d="M{x0+9},{y0-9} l-4.4,0.6 l1.9,3.4 z" fill="{color}"/>')
    if ref:
        o.append(txt(x - 14, y + 22, ref, size=8.4, fill=BLEU, weight="700", anchor="end"))
    return "".join(o)


def pad(x, y, label="", side="left"):
    """Pastille d'électrode + étiquette déportée."""
    o = [f'<circle cx="{x}" cy="{y}" r="7.5" fill="{OR_CL}" stroke="{OR}" stroke-width="1.8"/>']
    if label:
        dx, a = (-14, "end") if side == "left" else (14, "start")
        o.append(txt(x + dx, y + 3.4, label, size=8.2, fill=OR, weight="700", anchor=a))
    return "".join(o)


def note(x, y, lines, w=300, kind="info", size=8.2):
    """Cartouche : kind = info (bleu) | warn (cuivre) | ok (vert)."""
    fill, stroke = {"info": ("#F5F8FB", BLEU),
                    "warn": ("#FBF0E8", CUIVRE),
                    "ok":   ("#EAF4ED", SEVE)}[kind]
    h = 14 + 13.6 * len(lines)
    o = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="{fill}" '
         f'stroke="{stroke}" stroke-width="1.2"/>']
    for i, ln in enumerate(lines):
        bold = ln.startswith("*")
        s = ln[1:] if bold else ln
        o.append(txt(x + 10, y + 18 + 13.6 * i, s, size=size,
                     fill=(stroke if bold else NUIT), anchor="start",
                     weight=("700" if bold else "400")))
    return "".join(o)


def netlabel(x, y, s, anchor="start"):
    return txt(x, y, s, size=8.2, fill=SEVE, weight="700", anchor=anchor,
               family="DejaVu Sans Mono, monospace")


def frame(w, h, l1, l2):
    cw, ch = 322, 46
    return "".join([
        f'<rect x="10" y="10" width="{w-20}" height="{h-20}" rx="3" fill="none" '
        f'stroke="{TRAIT}" stroke-width="1.4"/>',
        f'<rect x="{w-10-cw}" y="{h-10-ch}" width="{cw}" height="{ch}" fill="#FBFAF4" '
        f'stroke="{TRAIT}" stroke-width="1.4"/>',
        txt(w - cw, h - 10 - ch + 19, l1, size=8.4, fill=NUIT, anchor="start", weight="700"),
        txt(w - cw, h - 10 - ch + 34, l2, size=7.6, fill=GRIS, anchor="start"),
    ])


# =============================================================================
#  PLANCHE 1 — FRONT-END BIODATA À LMC555
# =============================================================================
def sch_biodata_555():
    W, H = 1200, 750
    o = [frame(W, H, "PLANCHE 1 — Front-end biodata à LMC555",
               "relevé du netlist GalvShield_005.sch · licence MIT"),
         title(W / 2, 42, "CAPTEUR DE CONDUCTANCE À OSCILLATEUR ASTABLE")]

    # ---- LMC555 -------------------------------------------------------------
    u1, p = ic(380, 232, 160, "LMC555", "multivibrateur astable",
               left=[(7, "DIS", 290), (6, "THR", 325), (2, "TR", 360)],
               right=[(3, "Q", 290), (8, "V+", 325), (4, "RST", 360)],
               bottom=[(1, "GND", 460)])
    o.append(u1)
    o.append(gnd(460, p["GND"][1]))

    # V+ et RST sur le même rail local
    o.append(w_([(566, 325), (600, 325)]))
    o.append(w_([(566, 360), (600, 360), (600, 325)]))
    o.append(dot(600, 325))
    o.append(vcc(600, 325, "+5 V"))

    # ---- Réseau de temporisation : R2, la plante, C1 ------------------------
    o.append(vcc(300, 150, "+5 V"))
    o.append(res_v(300, 150, "R2", "100 kΩ"))
    o.append(w_([(300, 198), (300, 290)]))
    o.append(w_([(210, 290), (380, 290)]))
    o.append(dot(300, 290))
    o.append(netlabel(318, 282, "PROBE2"))

    o.append(w_([(210, 390), (330, 390)]))
    o.append(w_([(330, 390), (330, 325), (380, 325)]))
    o.append(w_([(330, 360), (380, 360)]))
    o.append(dot(330, 360))
    o.append(netlabel(348, 384, "PROBE1"))
    o.append(dot(268, 390))
    o.append(cap_v(268, 390, "C1", "4,7 nF", side=1))
    o.append(gnd(268, 420))

    # ---- La plante ----------------------------------------------------------
    o.append(f'<rect x="52" y="250" width="158" height="184" rx="8" fill="#EAF4ED" '
             f'stroke="{SEVE}" stroke-width="1.8" stroke-dasharray="6 4"/>')
    o.append(txt(131, 274, "FEUILLE / RAMEAU", size=8.8, fill=SEVE, weight="700", spacing="1"))
    o.append(pad(210, 290, "électrode A", "left"))
    o.append(pad(210, 390, "électrode B", "left"))
    o.append(txt(131, 340, "R", size=17, fill=NUIT, weight="700",
                 family="Cormorant Garamond, serif"))
    o.append(txt(143, 344, "plante", size=8, fill=NUIT, anchor="start"))
    o.append(txt(131, 362, "0,3 – 5 MΩ", size=9.4, fill=NUIT))
    o.append(txt(131, 416, "c\u2019est ELLE la résistance RB", size=7.8, fill=SEVE,
                 style="italic"))

    # ---- Microcontrôleur ----------------------------------------------------
    u2, m = ic(700, 232, 190, "ATmega328P", "carte Arduino Uno",
               left=[("", "D2 / INT0", 290)],
               right=[("", "D1 / TX", 290), ("", "A0", 370), ("", "A1", 420),
                      ("", "D11 (PWM)", 470)],
               top=[("", "", 795)])
    o.append(u2)
    o.append(vcc(795, 206, "+5 V"))

    # Sortie Q → D2, avec LED témoin sur la branche
    o.append(w_([(566, 290), (674, 290)]))
    o.append(netlabel(596, 282, "OUTPUT"))
    o.append(dot(620, 290))
    o.append(w_([(620, 290), (620, 330)]))
    o.append(res_v(620, 330, "R3", "220 Ω", h=42, side=-1))
    o.append(w_([(620, 372), (620, 382)]))
    o.append(led_v(620, 382, "LED6"))
    o.append(gnd(620, 418))

    # ---- Sortie MIDI --------------------------------------------------------
    o.append(w_([(916, 290), (964, 290)]))
    o.append(f'<circle cx="1000" cy="290" r="36" fill="#FBFAF4" stroke="{NUIT}" '
             f'stroke-width="2"/>')
    for a in (-1, 0, 1):
        o.append(f'<circle cx="{1000 + a*13}" cy="{284 + abs(a)*9}" r="2.6" fill="{FIL}"/>')
    o.append(txt(1000, 348, "DIN-5 · MIDI OUT", size=8.2, fill=NUIT, weight="700"))
    o.append(txt(958, 282, "5", size=7.4, fill=GRIS, anchor="end"))
    o.append(w_([(1000, 254), (1000, 244)]))
    o.append(txt(1012, 248, "4", size=7.4, fill=GRIS, anchor="start"))
    o.append(res_v(1000, 196, "R1", "220 Ω", h=48, side=1))
    o.append(vcc(1000, 196, "+5 V"))

    # ---- Potentiomètre de seuil (A0) ---------------------------------------
    o.append(w_([(916, 370), (1090, 370), (1090, 476)]))
    pt, pp = pot_v(1124, 450, "R9", "10 kΩ lin.")
    o.append(pt)
    o.append(w_([(1090, 476), (pp["curseur"][0], 476)]))
    o.append(vcc(1124, 450, "+5 V"))
    o.append(gnd(1124, 502))

    # ---- Bouton de menu (A1) -----------------------------------------------
    o.append(w_([(916, 420), (1000, 420), (1000, 456)]))
    o.append(switch_v(1000, 456, "S1"))
    o.append(gnd(1000, 490))

    # ---- Sortie CV / audio (D11) -------------------------------------------
    o.append(w_([(916, 470), (952, 470), (952, 530)]))
    o.append(netlabel(920, 462, "PWM"))
    o.append(cap_v(952, 530, "C3", "1 µF", side=-1, pol=True))
    o.append(w_([(952, 560), (996, 560)]))
    o.append(res_h(996, 560, "R10  3,9 kΩ", "", w=64))
    o.append(w_([(1060, 560), (1112, 560)]))
    o.append(dot(1086, 560))
    o.append(w_([(1086, 560), (1086, 586)]))
    o.append(res_v(1086, 586, "R11", "1 kΩ", h=42, side=1))
    o.append(gnd(1086, 628))
    o.append(f'<rect x="1112" y="536" width="78" height="48" rx="6" fill="#FBFAF4" '
             f'stroke="{NUIT}" stroke-width="2"/>')
    o.append(txt(1151, 556, "JACK 3,5", size=8.6, fill=NUIT, weight="700"))
    o.append(txt(1151, 571, "CV / audio", size=7.8, fill=GRIS))

    # ---- Cartouches ---------------------------------------------------------
    o.append(note(52, 496, [
        "*PRINCIPE — la plante EST le composant",
        "Le tissu ferme le réseau RC de l\u2019astable :",
        "f ≈ 1,44 / ((R2 + 2·R_plante) · C1)",
        "0,3 MΩ → ≈ 480 Hz        5 MΩ → ≈ 29 Hz",
        "Le firmware mesure la PÉRIODE sur INT0, pas",
        "une tension : voir le listing 1 de l\u2019annexe.",
    ], w=392, kind="info"))

    o.append(note(52, 616, [
        "*CE QUE LE SIGNAL N\u2019EST PAS",
        "Aucune tension n\u2019est « lue » dans la plante : le",
        "montage INJECTE un courant et mesure une impédance",
        "de surface — analogue de la réponse électrodermale.",
        "Humidité de l\u2019air, appui de l\u2019électrode et température",
        "y pèsent autant que l\u2019état physiologique du végétal.",
    ], w=392, kind="warn"))

    write("sch-biodata-555.svg", "\n".join(o), W, H)


# =============================================================================
#  PLANCHE 2 — ÉLECTROPHYSIOLOGIE HAUTE IMPÉDANCE
# =============================================================================
def sch_electrophysio():
    W, H = 1160, 720
    o = [frame(W, H, "PLANCHE 2 — Voie d'électrophysiologie extracellulaire",
               "schéma d'application · datasheets TI INA333 / ADS1115, ADI ADuM1251"),
         title(W / 2, 42, "ÉLECTRODES → INA333 → ADS1115 → LIAISON I²C ISOLÉE")]

    # ---- Tronc et électrodes ------------------------------------------------
    o.append(f'<rect x="36" y="212" width="120" height="300" rx="10" fill="#EAF4ED" '
             f'stroke="{SEVE}" stroke-width="1.8" stroke-dasharray="6 4"/>')
    o.append(txt(96, 236, "TRONC", size=9.4, fill=SEVE, weight="700", spacing="1.4"))
    o.append(pad(156, 290, "E1", "left"))
    o.append(pad(156, 390, "E2", "left"))
    o.append(pad(156, 470, "REF", "left"))
    o.append(txt(96, 496, "Pb/PbCl₂, −80 cm", size=7.6, fill=GRIS))
    o.append(txt(96, 312, "aubier", size=7.6, fill=GRIS))
    o.append(txt(96, 412, "aubier", size=7.6, fill=GRIS))

    # Résistances de limitation + filtrage RF
    o.append(w_([(164, 290), (200, 290)]))
    o.append(res_h(200, 290, "R1", "10 kΩ"))
    o.append(w_([(248, 290), (314, 290)]))
    o.append(w_([(164, 390), (200, 390)]))
    o.append(res_h(200, 390, "R2", "10 kΩ"))
    o.append(w_([(248, 390), (314, 390)]))
    o.append(dot(292, 290))
    o.append(cap_v(292, 290, "C1", "1 nF", side=-1))
    o.append(gnd(292, 320))
    o.append(dot(292, 390))
    o.append(cap_v(292, 390, "C2", "1 nF", side=-1))
    o.append(gnd(292, 420))

    # ---- INA333 -------------------------------------------------------------
    u1, p = ic(340, 228, 170, "INA333", "ampli d'instrumentation",
               left=[(2, "IN−", 290), (3, "IN+", 390)],
               right=[(6, "OUT", 290), (5, "REF", 390)],
               top=[(7, "V+", 465)], bottom=[(4, "V−", 425)])
    o.append(u1)
    o.append(vcc(465, 202, "+3V3"))
    o.append(gnd(425, p["V−"][1]))
    o.append(txt(425, 330, "R_G = 1 kΩ  →  G = 101", size=8.6, fill=BLEU, weight="700"))
    o.append(txt(425, 346, "G = 1 + 100 kΩ / R_G", size=8, fill=GRIS))

    # Référence à mi-alimentation
    o.append(w_([(536, 390), (536, 470), (596, 470)]))
    o.append(dot(596, 470))
    o.append(res_v(596, 428, "R4", "100 kΩ", h=42, side=1))
    o.append(vcc(596, 428, "+3V3"))
    o.append(res_v(596, 470, "R5", "100 kΩ", h=42, side=1))
    o.append(gnd(596, 512))
    o.append(txt(556, 466, "V/2", size=8.2, fill=GRIS, anchor="end"))

    # ---- Filtre anti-repliement --------------------------------------------
    o.append(w_([(536, 290), (560, 290)]))
    o.append(res_h(560, 290, "R3  16 kΩ", "", w=62))
    o.append(w_([(622, 290), (664, 290)]))
    o.append(dot(646, 290))
    o.append(cap_v(646, 290, "C3", "100 nF", side=-1))
    o.append(gnd(646, 320))
    o.append(txt(596, 246, "passe-bas 1ᵉʳ ordre, f_c ≈ 100 Hz", size=8, fill=GRIS))

    # ---- ADS1115 ------------------------------------------------------------
    u2, a = ic(690, 232, 170, "ADS1115", "ΔΣ 16 bits · PGA · I²C",
               left=[(4, "AIN0", 290), (5, "AIN1", 330)],
               right=[(10, "SCL", 290), (9, "SDA", 330), (11, "ADDR", 370)])
    o.append(u2)
    o.append(w_([(664, 330), (664, 470)]))
    o.append(gnd(664, 470))
    o.append(w_([(886, 370), (906, 370), (906, 430)]))
    o.append(gnd(906, 430, "0x48"))

    # ---- Isolation galvanique ----------------------------------------------
    o.append(f'<line x1="1000" y1="150" x2="1000" y2="600" stroke="{CUIVRE}" '
             f'stroke-width="1.6" stroke-dasharray="9 6"/>')
    o.append(txt(1000, 142, "BARRIÈRE D'ISOLATION", size=8, fill=CUIVRE,
                 weight="700", spacing="0.8"))
    u3, s = ic(940, 232, 120, "ADuM1251", "isolateur I²C",
               left=[("", "SCL1", 290), ("", "SDA1", 330)],
               right=[("", "SCL2", 290), ("", "SDA2", 330)])
    o.append(u3)
    o.append(w_([(886, 290), (914, 290)]))
    o.append(w_([(886, 330), (914, 330)]))
    o.append(txt(1092, 296, "vers ESP32", size=8.4, fill=GRIS, anchor="start"))
    o.append(txt(1092, 310, "(côté réseau)", size=7.6, fill=GRIS, anchor="start"))

    # Blindage
    o.append(f'<rect x="180" y="250" width="350" height="202" rx="8" fill="none" '
             f'stroke="{BLEU}" stroke-width="1.3" stroke-dasharray="3 4"/>')
    o.append(txt(188, 466, "blindage relié à REF (garde active)", size=7.6, fill=BLEU,
                 anchor="start", style="italic"))

    # ---- Cartouches ---------------------------------------------------------
    o.append(note(46, 540, [
        "*POURQUOI UN INA333 (et pas un AD620)",
        "I_bias ≈ 200 pA. Sur une source de 10 MΩ cela",
        "ne fait que 2 mV d'erreur. L'AD620 (1 nA typ.)",
        "en ferait 10 mV, un ampli bipolaire bien plus.",
        "Le tissu végétal est une source à très haute",
        "impédance : le courant d'entrée est LE critère.",
    ], w=352, kind="info"))

    o.append(note(414, 540, [
        "*POURQUOI PAS L'ADC TOUT SEUL",
        "L'ADS1115 présente 6 MΩ en mode commun (PGA ×1)",
        "et seulement 710 kΩ à PGA ×16 : brancher",
        "l'électrode dessus forme un pont diviseur avec",
        "le tissu. La mesure devient une fonction de",
        "l'impédance de contact, pas du potentiel.",
    ], w=352, kind="warn"))

    o.append(note(782, 540, [
        "*RÉJECTION DU 50 Hz",
        "Échantillonner à un multiple entier de 20 ms",
        "(ex. 8 SPS) annule le secteur par intégration,",
        "puis notch IIR numérique en secours.",
        "L'isolateur coupe la boucle de masse : sans lui,",
        "le secteur revient par la terre du réseau.",
    ], w=332, kind="ok"))

    write("sch-electrophysio-ina333.svg", "\n".join(o), W, H)


# =============================================================================
#  PLANCHE 3 — NŒUD ENVIRONNEMENTAL ESP32
# =============================================================================
def sch_bus_capteurs():
    W, H = 1140, 740
    o = [frame(W, H, "PLANCHE 3 — Nœud environnemental ESP32",
               "bus I²C · 1-Wire · entrée analogique · comptage d'impulsions"),
         title(W / 2, 42, "BUS DE CAPTEURS : I²C, 1-WIRE, ANALOGIQUE, COMPTAGE")]

    # ---- ESP32 --------------------------------------------------------------
    u1, p = ic(560, 180, 210, "ESP32-S3", "Wi-Fi / BLE · deep sleep ≈ 13 µA",
               left=[("", "GPIO9  SCL", 240), ("", "GPIO8  SDA", 280),
                     ("", "GPIO5  ADC1", 440)],
               right=[("", "3V3", 240), ("", "GPIO4  1-Wire", 340),
                      ("", "GPIO6  CNT", 470), ("", "GND", 540)])
    o.append(u1)
    o.append(vcc(796, 240, "+3V3"))
    o.append(gnd(796, 540))

    # ---- Bus I²C (SCL en haut, SDA en dessous) ------------------------------
    o.append(w_([(80, 240), (534, 240)]))
    o.append(w_([(80, 280), (534, 280)]))
    o.append(netlabel(90, 232, "SCL"))
    o.append(netlabel(90, 272, "SDA"))

    # Résistances de tirage, à l'extrémité du bus
    o.append(hop(140, 240))                       # SDA franchit SCL sans contact
    o.append(w_([(140, 280), (140, 248)]))
    o.append(w_([(140, 232), (140, 198)]))
    o.append(res_v(140, 150, "R2", "4,7 kΩ", h=48, side=1))
    o.append(dot(140, 280))
    o.append(w_([(110, 240), (110, 198)]))
    o.append(res_v(110, 150, "R1", "4,7 kΩ", h=48, side=-1))
    o.append(dot(110, 240))
    o.append(w_([(110, 150), (140, 150)]))
    o.append(vcc(125, 150, "+3V3"))

    # ---- Périphériques I²C --------------------------------------------------
    for cx, nm, adr, rol in ((190, "BME280", "0x76", "T · HR · pression"),
                             (330, "BH1750", "0x23", "éclairement (lux)"),
                             (470, "SCD41",  "0x62", "CO₂ · T · HR")):
        o.append(f'<rect x="{cx-65}" y="350" width="130" height="80" rx="5" '
                 f'fill="#FBFAF4" stroke="{NUIT}" stroke-width="2"/>')
        o.append(txt(cx, 378, nm, size=12, fill=NUIT, weight="700",
                     family="Cormorant Garamond, serif"))
        o.append(txt(cx, 396, adr + " · I²C", size=7.8, fill=SEVE, weight="700"))
        o.append(txt(cx, 412, rol, size=7.6, fill=GRIS))
        # SCL : monte jusqu'au bus du haut, saute le bus SDA
        o.append(w_([(cx - 26, 350), (cx - 26, 288)]))
        o.append(hop(cx - 26, 280))
        o.append(w_([(cx - 26, 272), (cx - 26, 240)]))
        o.append(dot(cx - 26, 240))
        # SDA : se raccorde au bus du bas
        o.append(w_([(cx + 26, 350), (cx + 26, 280)]))
        o.append(dot(cx + 26, 280))

    # ---- Sonde capacitive d'humidité du sol --------------------------------
    o.append(w_([(534, 440), (534, 470), (250, 470), (250, 510)]))
    o.append(f'<rect x="170" y="510" width="160" height="74" rx="5" fill="#FBFAF4" '
             f'stroke="{NUIT}" stroke-width="2"/>')
    o.append(txt(250, 536, "Sonde capacitive", size=11, fill=NUIT, weight="700",
                 family="Cormorant Garamond, serif"))
    o.append(txt(250, 552, "v2.0 · sortie 0–3 V", size=7.8, fill=GRIS))
    o.append(txt(250, 568, "alimentée en 3,3 V", size=7.6, fill=SEVE))
    o.append(dot(400, 470))
    o.append(cap_v(400, 470, "C1", "100 nF", side=1))
    o.append(gnd(400, 500))

    # ---- 1-Wire -------------------------------------------------------------
    o.append(w_([(796, 340), (900, 340)]))
    o.append(dot(852, 340))
    o.append(w_([(852, 340), (852, 306)]))
    o.append(res_v(852, 258, "R3", "4,7 kΩ", h=48, side=-1))
    o.append(vcc(852, 258, "+3V3"))
    o.append(f'<rect x="900" y="308" width="180" height="76" rx="5" fill="#FBFAF4" '
             f'stroke="{NUIT}" stroke-width="2"/>')
    o.append(txt(990, 334, "DS18B20 ×3", size=12, fill=NUIT, weight="700",
                 family="Cormorant Garamond, serif"))
    o.append(txt(990, 351, "air · sol −10 cm · tronc", size=7.8, fill=GRIS))
    o.append(txt(990, 368, "1-Wire, adresse 64 bits", size=7.6, fill=SEVE))

    # ---- Entrée à impulsions (anémomètre / pluviomètre) ---------------------
    o.append(w_([(796, 470), (960, 470)]))
    o.append(dot(840, 470))
    o.append(w_([(840, 470), (840, 436)]))
    o.append(res_v(840, 388, "R4", "10 kΩ", h=48, side=-1))
    o.append(vcc(840, 388, "+3V3"))
    o.append(dot(900, 470))
    o.append(cap_v(900, 470, "C2", "100 nF", side=1))
    o.append(gnd(900, 500))
    o.append(reed(960, 470, "ILS — augets / coupelles"))
    o.append(w_([(1016, 470), (1040, 470)]))
    o.append(gnd(1040, 470))

    # ---- Cartouches ---------------------------------------------------------
    o.append(note(788, 556, [
        "*ANTI-REBOND MATÉRIEL, PAS LOGICIEL",
        "Un contact ILS rebondit 1 à 5 ms. Sans le RC,",
        "une bascule de pluviomètre est comptée 3 fois",
        "et la pluie est surestimée d'un facteur 3.",
        "R4·C2 = 10 kΩ × 100 nF = 1 ms de constante.",
    ], w=334, kind="warn"))

    o.append(note(56, 596, [
        "*UN SEUL JEU DE RÉSISTANCES DE TIRAGE",
        "Beaucoup de cartes capteurs embarquent déjà",
        "leurs 10 kΩ. Trois modules en parallèle →",
        "tirage résultant trop fort, fronts déformés,",
        "bus instable. Dessouder les tirages des",
        "modules esclaves, n'en garder qu'un seul.",
    ], w=340, kind="info"))

    o.append(note(424, 596, [
        "*CONVENTION DE LECTURE",
        "L\u2019arceau signale un croisement SANS connexion ;",
        "le point plein signale une connexion.",
    ], w=330, kind="ok"))

    write("sch-bus-capteurs-esp32.svg", "\n".join(o), W, H)


# =============================================================================
#  PLANCHE 4 — ALIMENTATION SOLAIRE
# =============================================================================
def sch_alimentation():
    W, H = 1080, 640
    o = [frame(W, H, "PLANCHE 4 — Alimentation solaire LiFePO₄",
               "chaîne MPPT · protections · budget d'énergie"),
         title(W / 2, 42, "AUTONOMIE : PANNEAU → MPPT → LiFePO₄ → 3,3 V")]

    # ---- Panneau ------------------------------------------------------------
    o.append(f'<rect x="50" y="160" width="130" height="92" rx="4" fill="#EAF0F7" '
             f'stroke="{BLEU}" stroke-width="2"/>')
    for i in range(1, 5):
        o.append(f'<line x1="{50+26*i}" y1="160" x2="{50+26*i}" y2="252" '
                 f'stroke="{BLEU}" stroke-width="1"/>')
    o.append(txt(115, 274, "Panneau PV 6 V / 5 W", size=9, fill=NUIT, weight="700"))
    o.append(txt(115, 289, "orienté sud, hors couvert", size=7.8, fill=GRIS))
    o.append(w_([(180, 186), (212, 186)]))
    o.append(w_([(180, 226), (240, 226), (240, 330)]))
    o.append(gnd(240, 330))

    # Diode anti-retour
    o.append(diode(212, 186, "D1  SS34"))
    o.append(w_([(246, 186), (300, 186)]))

    # ---- Contrôleur de charge MPPT -----------------------------------------
    u1, p = ic(300, 130, 170, "CN3791", "chargeur MPPT 1 cellule",
               left=[("", "VIN", 186)],
               right=[("", "BAT", 186), ("", "STAT", 226)])
    o.append(u1)
    o.append(txt(385, 268, "point MPP fixé par pont résistif", size=7.8, fill=GRIS))
    o.append(txt(385, 283, "→ régler sur 0,76 × Voc du panneau", size=7.8, fill=GRIS))

    # ---- Batterie -----------------------------------------------------------
    o.append(w_([(496, 186), (570, 186)]))
    for i, (dx, hh, sw) in enumerate(((0, 24, 2.6), (14, 13, 5), (28, 24, 2.6), (42, 13, 5))):
        o.append(f'<line x1="{570+dx}" y1="{186-hh}" x2="{570+dx}" y2="{186+hh}" '
                 f'stroke="{FIL}" stroke-width="{sw}"/>')
    o.append(txt(591, 140, "LiFePO₄ 3,2 V", size=9.4, fill=NUIT, weight="700"))
    o.append(txt(591, 155, "6 000 mA·h", size=8.4, fill=GRIS))
    o.append(w_([(612, 186), (680, 186)]))
    o.append(w_([(570, 210), (570, 330)]))
    o.append(gnd(570, 330))

    # ---- Régulateur ---------------------------------------------------------
    u2, r = ic(680, 130, 170, "TPS63020", "buck-boost 3,3 V",
               left=[("", "VIN", 186)],
               right=[("", "VOUT", 186), ("", "EN", 226)])
    o.append(u2)
    o.append(w_([(876, 186), (940, 186)]))
    o.append(vcc(940, 186, "+3V3"))
    o.append(w_([(876, 226), (920, 226)]))
    o.append(txt(926, 222, "commandé par le MCU :", size=7.8, fill=GRIS, anchor="start"))
    o.append(txt(926, 236, "coupe les capteurs", size=7.8, fill=GRIS, anchor="start"))
    o.append(txt(926, 250, "pendant le deep sleep", size=7.8, fill=GRIS, anchor="start"))

    # ---- Cartouches ---------------------------------------------------------
    o.append(note(50, 350, [
        "*BUDGET D'ÉNERGIE — 1 relevé toutes les 15 min",
        "veille .............. 15 µA × 899 s  =  13,5 mA·s",
        "réveil + mesures .... 40 mA × 0,9 s  =  36,0 mA·s",
        "émission LoRa ....... 120 mA × 0,1 s =  12,0 mA·s",
        "total par cycle ..................... ≈ 61,5 mA·s",
        "soit 0,0171 mA·h × 96 cycles ≈ 1,64 mA·h / jour",
        "",
        "Une cellule de 6 000 mA·h tiendrait ≈ 3 600 jours",
        "SANS aucun apport solaire. La vraie limite n'est",
        "donc pas la capacité mais le vieillissement",
        "calendaire et l'autodécharge.",
    ], w=470, kind="ok"))

    o.append(note(560, 350, [
        "*POURQUOI LiFePO₄ PLUTÔT QUE Li-ion",
        "· 3,2 V nominal : alimente le 3,3 V sur presque",
        "  toute la décharge, sans élévateur",
        "· −20 … +60 °C en décharge",
        "· chimie LFP : pas d'emballement thermique",
        "",
        "*⚠ INTERDICTION DE CHARGE SOUS 0 °C",
        "Sous 0 °C la charge dépose du lithium métallique",
        "de façon irréversible. Placer un DS18B20 CONTRE",
        "la cellule et verrouiller la charge par logiciel :",
        "c'est l'erreur n°1 des stations hivernales.",
    ], w=470, kind="warn"))

    write("sch-alim-solaire.svg", "\n".join(o), W, H)


# =============================================================================
#  PLANCHE 5 — SONDE DE FLUX DE SÈVE (GRANIER / TDP)
# =============================================================================
def sch_granier():
    W, H = 1080, 700
    o = [frame(W, H, "PLANCHE 5 — Sonde de flux de sève (Granier / TDP)",
               "chauffage constant · couple thermoélectrique différentiel"),
         title(W / 2, 42, "DISSIPATION THERMIQUE : SONDE CHAUFFÉE ET SONDE DE RÉFÉRENCE")]

    cx, cy = 200, 330
    o.append(f'<circle cx="{cx}" cy="{cy}" r="122" fill="#F2EFE2" stroke="{NUIT}" '
             f'stroke-width="2"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="96" fill="#EAF4ED" stroke="{SEVE}" '
             f'stroke-width="1.6"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="54" fill="#E4DFCB" stroke="{GRIS}" '
             f'stroke-width="1.4"/>')

    # Aiguilles implantées dans l\u2019aubier
    o.append(f'<rect x="{cx-5}" y="{cy-92}" width="10" height="44" rx="3" '
             f'fill="{CUIVRE}" stroke="{FIL}" stroke-width="1.4"/>')
    o.append(f'<rect x="{cx-5}" y="{cy+48}" width="10" height="44" rx="3" '
             f'fill="{BLEU}" stroke="{FIL}" stroke-width="1.4"/>')

    # Étiquettes des aiguilles, posées hors du disque
    o.append(txt(cx, 150, "aiguille CHAUFFÉE — amont", size=8.4, fill=CUIVRE, weight="700"))
    o.append(txt(cx, 490, "aiguille de RÉFÉRENCE — aval, non chauffée", size=8.4,
                 fill=BLEU, weight="700"))
    o.append(txt(cx, 512, "coupe transversale · les deux aiguilles sur la même",
                 size=7.6, fill=GRIS, style="italic"))
    o.append(txt(cx, 526, "verticale, 40 mm d\u2019écart, insertion 20 mm", size=7.6,
                 fill=GRIS, style="italic"))

    # Légende des cernes
    o.append(f'<rect x="40" y="556" width="320" height="86" rx="4" fill="#FBFAF4" '
             f'stroke="{TRAIT}" stroke-width="1.2"/>')
    for i, (col, lbl) in enumerate((("#F2EFE2", "écorce + liber"),
                                    ("#EAF4ED", "aubier — seul tissu conducteur"),
                                    ("#E4DFCB", "duramen — hydrauliquement mort"))):
        yy = 580 + i * 22
        o.append(f'<rect x="56" y="{yy-9}" width="16" height="14" rx="2" fill="{col}" '
                 f'stroke="{GRIS}" stroke-width="1"/>')
        o.append(txt(82, yy + 2, lbl, size=8.2, fill=NUIT, anchor="start"))

    # ---- Chauffage constant -------------------------------------------------
    o.append(w_([(cx, cy - 92), (cx, 172), (470, 172)]))
    o.append(res_h(470, 172, "R_ch", "≈ 25 Ω · 0,2 W constant", w=92))
    o.append(w_([(562, 172), (650, 172)]))
    o.append(vcc(650, 172, "+5 V régulé"))
    o.append(txt(516, 134, "cartouche chauffante", size=7.8, fill=GRIS))

    # ---- Couple thermoélectrique différentiel ------------------------------
    o.append(w_([(cx + 5, cy - 70), (372, cy - 70), (372, 300), (494, 300)]))
    o.append(w_([(cx + 5, cy + 70), (420, cy + 70), (420, 340), (494, 340)]))
    o.append(txt(384, 232, "constantan / cuivre —", size=7.6, fill=GRIS, anchor="start"))
    o.append(txt(384, 246, "soudure différentielle", size=7.6, fill=GRIS, anchor="start"))

    # ---- Numérisation -------------------------------------------------------
    u1, p = ic(520, 242, 170, "ADS1220", "ΔΣ 24 bits · PGA ×128",
               left=[("", "AIN0", 300), ("", "AIN1", 340)],
               right=[("", "SPI", 320)])
    o.append(u1)
    o.append(w_([(716, 320), (778, 320)]))
    o.append(f'<rect x="778" y="288" width="146" height="64" rx="5" fill="#F2F7FB" '
             f'stroke="{BLEU}" stroke-width="2"/>')
    o.append(txt(851, 316, "ESP32", size=12, fill=BLEU, weight="700",
                 family="Cormorant Garamond, serif"))
    o.append(txt(851, 334, "1 relevé / 10 min", size=7.8, fill=GRIS))

    # ---- Cartouches ---------------------------------------------------------
    o.append(note(400, 416, [
        "*ÉQUATION DE GRANIER (1985)",
        "K = (ΔT_max − ΔT) / ΔT",
        "u = 118,99·10⁻⁶ · K^1,231       [m³ m⁻² s⁻¹]",
        "ΔT_max = écart relevé à flux nul, en fin de nuit.",
    ], w=400, kind="info"))

    o.append(note(400, 500, [
        "*⚠ LA CALIBRATION D\u2019ORIGINE EST BIAISÉE",
        "La littérature documente une sous-estimation de 30 à",
        "60 % du flux réel selon l\u2019espèce et la profondeur",
        "d\u2019insertion. Sans recalibration par espèce, ce montage",
        "ne donne PAS un débit absolu : il donne un INDICE",
        "relatif, à n\u2019interpréter que dans sa propre dynamique",
        "jour / nuit, sur un même arbre et une même saison.",
    ], w=400, kind="warn"))

    o.append(note(824, 416, [
        "*CONTRAINTE MÉTROLOGIQUE",
        "Le gradient utile va de 0 à 10 K.",
        "Il faut résoudre 0,01 K, soit",
        "environ 0,4 µV sur un couple",
        "cuivre-constantan (≈ 40 µV/K).",
        "D\u2019où 24 bits ET un PGA ×128 :",
        "un ADC 12 bits intégré au MCU",
        "est ici totalement hors-jeu.",
    ], w=228, kind="ok"))

    write("sch-granier-tdp.svg", "\n".join(o), W, H)


def main():
    print("Génération des planches de schémas :")
    for f in (sch_biodata_555, sch_electrophysio, sch_bus_capteurs,
              sch_alimentation, sch_granier):
        f()
    print("Terminé.")


if __name__ == "__main__":
    main()
