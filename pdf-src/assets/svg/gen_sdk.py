#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/assets/svg/gen_sdk.py
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

"""Figures for the developer guide — drawn by program.

`C-61`: figures are produced by a deterministic script, never imported from a
graphics editor. Two runs give the same file byte for byte, and a correction is
made in the code rather than with the mouse.

    python3 pdf-src/assets/svg/gen_sdk.py
"""
from __future__ import annotations

import os

ICI = os.path.dirname(os.path.abspath(__file__))

#  The book's palette.
VERT = "#3F7D5A"
VERT_CLAIR = "#7FE0A8"
OR = "#B08528"
ENCRE = "#23302C"
GRIS = "#6B7A72"
PAPIER = "#FBF9F1"
ALERTE = "#A8552E"


def cycle_de_vie() -> str:
    """A module's four moments, and where a fault ends up."""
    L, H = 900, 380
    etapes = [
        ("1", "__init__", "the context arrives", "nothing lengthy here"),
        ("2", "installer()", "once, at start-up", "subscribe, prepare"),
        ("3", "the capabilities", "during the session", "analyse, describe…"),
        ("4", "arreter()", "at shutdown", "close what you opened"),
    ]
    largeur, ecart = 178, 22
    x0 = (L - (len(etapes) * largeur + (len(etapes) - 1) * ecart)) / 2
    y = 92

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L} {H}" '
         f'width="{L}" height="{H}" font-family="DejaVu Sans, sans-serif">',
         f'<rect width="{L}" height="{H}" fill="{PAPIER}"/>',
         f'<text x="{L/2}" y="38" text-anchor="middle" font-size="17" '
         f'font-weight="bold" fill="{ENCRE}">A module\'s life cycle</text>',
         f'<text x="{L/2}" y="60" text-anchor="middle" font-size="12" '
         f'fill="{GRIS}">A fault, at any one of these moments, disables '
         f'the module — and nothing else.</text>']

    for i, (rang, titre, quand, conseil) in enumerate(etapes):
        x = x0 + i * (largeur + ecart)
        p += [
            f'<rect x="{x}" y="{y}" width="{largeur}" height="96" rx="7" '
            f'fill="#fff" stroke="{VERT}" stroke-width="1.6"/>',
            f'<circle cx="{x+20}" cy="{y+20}" r="12" fill="{VERT}"/>',
            f'<text x="{x+20}" y="{y+25}" text-anchor="middle" font-size="13" '
            f'font-weight="bold" fill="#fff">{rang}</text>',
            f'<text x="{x+40}" y="{y+25}" font-size="13.5" font-weight="bold" '
            f'font-family="DejaVu Sans Mono, monospace" fill="{ENCRE}">{titre}</text>',
            f'<text x="{x+14}" y="{y+52}" font-size="11" fill="{GRIS}">{quand}</text>',
            f'<text x="{x+14}" y="{y+74}" font-size="11" fill="{VERT}">{conseil}</text>',
        ]
        if i < len(etapes) - 1:
            xf = x + largeur
            p.append(f'<path d="M {xf+3} {y+48} L {xf+ecart-5} {y+48}" '
                     f'stroke="{VERT}" stroke-width="1.6" fill="none" '
                     f'marker-end="url(#fleche)"/>')

    #  The fault's path: it always leads to the same place.
    yf = y + 150
    p += [
        f'<rect x="{x0}" y="{yf}" width="{L - 2*x0}" height="62" rx="7" '
        f'fill="#fff" stroke="{ALERTE}" stroke-width="1.6" '
        f'stroke-dasharray="5 3"/>',
        f'<text x="{L/2}" y="{yf+25}" text-anchor="middle" font-size="13" '
        f'font-weight="bold" fill="{ALERTE}">An exception, wherever it happens</text>',
        f'<text x="{L/2}" y="{yf+46}" text-anchor="middle" font-size="11.5" '
        f'fill="{ENCRE}">the module is disabled and logged · '
        f'the others carry on · the session is not lost</text>',
    ]
    for i in range(len(etapes)):
        x = x0 + i * (largeur + ecart) + largeur / 2
        p.append(f'<path d="M {x} {y+96} L {x} {yf}" stroke="{ALERTE}" '
                 f'stroke-width="1" stroke-dasharray="3 3" fill="none" '
                 f'opacity="0.55"/>')

    p.insert(1, f'''<defs><marker id="fleche" viewBox="0 0 10 10" refX="9"
      refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="{VERT}"/></marker></defs>''')
    p.append("</svg>")
    return "\n".join(p) + "\n"


PLANCHES = {"sdk-cycle.svg": cycle_de_vie}


def main() -> int:
    for nom, fabrique in PLANCHES.items():
        chemin = os.path.join(ICI, nom)
        with open(chemin, "w", encoding="utf-8") as f:
            f.write(fabrique())
        print(f"  ✓ {nom}  ({os.path.getsize(chemin)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
