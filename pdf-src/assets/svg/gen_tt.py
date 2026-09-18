#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/assets/svg/gen_tt.py
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
Illustrations vectorielles propres à la série « L'Arbre qui Parle ».

Ce module réutilise les primitives de gen.py (palette, write, txt, box, arrow,
arbres fractals) et y ajoute les schémas spécifiques aux trois volumes :
instrumentation d'arbre, chaînes d'acquisition, architectures logicielles,
conversion signal → langage et diagrammes épistémologiques.

Usage : python3 gen_tt.py
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
#  Briques communes
# ---------------------------------------------------------------------------
def node(x, y, w, h, title, lines=(), fill="#FFFFFF", stroke=SEVE,
         tcol=NUIT, ts=11.5, ls=8.2):
    """Bloc rectangulaire titré, avec lignes de détail centrées."""
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
    """Bandeau de regroupement (couche, étage, zone)."""
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
    """Arbre feuillu large — tronc court, houppier étalé.

    La primitive `fractal_tree` de gen.py part d'un unique segment de la hauteur
    totale, ce qui produit une silhouette en « Y ». Ici le tronc ne fait qu'un
    tiers de la hauteur et se divise en trois charpentières, ce qui donne la
    couronne arrondie d'un chêne ou d'un platane de parc.
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
#  1. L'ARBRE INSTRUMENTÉ — carte des capteurs
# =============================================================================
def tt_sensor_map():
    W, H = 900, 640
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']

    # Sol
    p.append(f'<path d="M0,520 Q220,506 450,514 T900,520 L900,640 L0,640 Z" '
             f'fill="#E6E2D2"/>')
    p.append(f'<line x1="0" y1="518" x2="900" y2="518" stroke="{GRIS}" stroke-width="1.2"/>')

    # Arbre — hauteur volontairement modérée pour dégager le titre
    p.append(canopy_tree(430, 520, 300, seed=23, color="#2F5F47", depth=8,
                         trunk_ratio=0.46, leaf="#6FA98A"))

    # Racines
    for a, l in ((200, 150), (222, 190), (248, 130), (292, 190), (318, 150), (342, 120)):
        ar = math.radians(a)
        p.append(f'<path d="M430,518 q{math.cos(ar)*l*0.5:.0f},{-math.sin(ar)*l*0.5+28:.0f} '
                 f'{math.cos(ar)*l:.0f},{-math.sin(ar)*l+18:.0f}" fill="none" '
                 f'stroke="#6B5A42" stroke-width="3" stroke-linecap="round" opacity="0.85"/>')

    # Étiquettes de capteurs : (x, y, ancre_x, ancre_y, code, libellé, grandeur)
    sensors = [
        (92,  118, 388, 236, "S1", "Capteur climatique",  "T° air · HR · pression"),
        (92,  206, 398, 300, "S2", "Lumière / PAR",       "lux · µmol·m⁻²·s⁻¹"),
        (92,  294, 384, 268, "S3", "Anémomètre",          "vitesse · direction du vent"),
        (92,  382, 413, 420, "S4", "Électrodes tronc",    "ΔV bioélectrique (mV)"),
        (630, 118, 472, 238, "S5", "Capteur acoustique",  "20 Hz – 200 kHz"),
        (630, 206, 447, 396, "S6", "Dendromètre",         "Δ circonférence (µm)"),
        (630, 294, 447, 456, "S7", "Flux de sève",        "densité de flux (cm·h⁻¹)"),
        (630, 382, 528, 512, "S8", "Sonde de sol",        "T° sol · θ volumique · CE"),
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

    # Boîtier d'acquisition
    p += node(352, 556, 196, 56, "Nœud d'acquisition",
              ("MCU · ADC · horloge · radio",), stroke=OR, fill="#FFF8E8", ts=10.5, ls=7.6)
    p.append(arrow(450, 500, 450, 552, OR, 2.4))
    p.append(txt(450, 630, "Alimentation solaire + accumulateur LiFePO₄ · liaison LoRaWAN / Wi-Fi",
                 8, GRIS))

    p.append(f'<rect x="0" y="0" width="{W}" height="72" fill="{IVOIRE}"/>')
    p.append(txt(450, 40, "L'ARBRE INSTRUMENTÉ", 13, NUIT, weight="700", spacing="3.4",
                 family=SERIF))
    p.append(txt(450, 60, "Huit familles de mesures, une seule chaîne d'acquisition",
                 8.4, GRIS, style="italic"))
    write("tt-sensor-map.svg", "\n".join(p), W, H)


# =============================================================================
#  2. ARCHITECTURE SYSTÈME COMPLÈTE
# =============================================================================
def tt_architecture():
    W, H = 920, 560
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(460, 34, "ARCHITECTURE D'UN ARBRE PARLANT", 12.5, NUIT,
                 weight="700", spacing="3", family=SERIF))

    y0 = 72
    layers = [
        (y0,       "1 · CAPTATION", SEVE, [
            ("Capteurs", ("physiques", "biologiques")),
            ("Conditionnement", ("amplification", "filtrage 50 Hz")),
            ("Conversion", ("ADC 16-24 bits", "horodatage")),
        ]),
        (y0 + 108, "2 · TRANSPORT", BLEU, [
            ("Nœud MCU", ("ESP32 / RP2040", "veille profonde")),
            ("Radio", ("LoRaWAN · Wi-Fi", "NB-IoT")),
            ("Passerelle", ("MQTT", "file d'attente")),
        ]),
        (y0 + 216, "3 · TRAITEMENT", OR, [
            ("Base temporelle", ("InfluxDB", "TimescaleDB")),
            ("Prétraitement", ("calibration", "détection d'anomalie")),
            ("Extraction", ("descripteurs", "fenêtres glissantes")),
        ]),
        (y0 + 324, "4 · RESTITUTION", CUIVRE, [
            ("Sonification", ("mapping → MIDI", "synthèse")),
            ("Modèle de langage", ("descripteurs → texte", "gabarit contraint")),
            ("Interface", ("web · audio", "affichage in situ")),
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
                 "Chaque étage peut être remplacé indépendamment : c'est la condition de la reproductibilité.",
                 8.2, GRIS, style="italic"))
    write("tt-architecture.svg", "\n".join(p), W, H)


# =============================================================================
#  3. CHAÎNE D'ACQUISITION ANALOGIQUE (électrophysiologie de terrain)
# =============================================================================
def tt_acquisition_chain():
    W, H = 920, 400
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(460, 34, "CHAÎNE D'ACQUISITION BIOÉLECTRIQUE", 12, NUIT,
                 weight="700", spacing="2.8", family=SERIF))

    stages = [
        ("Électrodes", ("Ag/AgCl", "Z ≈ 1-50 MΩ"), SEVE),
        ("Ampli. d'instr.", ("INA333 · AD8221", "Zin > 10 GΩ")),
        ("Filtre passe-bas", ("fₑ ≈ 10 Hz", "réjection 50 Hz")),
        ("Convertisseur", ("ADS1115 16 bits", "ADS1256 24 bits")),
        ("Microcontrôleur", ("horodatage", "moyennage")),
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

    # Tracés de signal sous chaque étage
    labels = [("bruit + signal", 0.55), ("×1000", 0.9), ("lissé", 0.55),
              ("quantifié", 0.5), ("série datée", 0.4)]
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

    p += band(28, 92, 356, 106, "TERRAIN — sous abri IP65", fill=SEVE)
    p += band(400, 92, 500, 106, "NUMÉRIQUE", fill=BLEU)

    p.append(txt(460, 340,
                 "Le gain est placé au plus près de l'électrode : toute longueur de câble avant l'amplificateur est une antenne.",
                 8.4, CUIVRE, style="italic"))
    p.append(txt(460, 362,
                 "Masse commune obligatoire ; isolation galvanique si une liaison secteur est présente en aval.",
                 8.4, GRIS, style="italic"))
    write("tt-acquisition-chain.svg", "\n".join(p), W, H)


# =============================================================================
#  4. DU SIGNAL AU LANGAGE — les trois conversions possibles
# =============================================================================
def tt_signal_to_language():
    W, H = 900, 560
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "TROIS FAÇONS DE FAIRE « PARLER » UN SIGNAL", 12, NUIT,
                 weight="700", spacing="2.6", family=SERIF))

    # Source commune
    p += node(330, 62, 240, 54, "Série temporelle mesurée",
              ("x(t) — grandeur physique datée",), stroke=SEVE, fill="#EAF3ED", ts=10.5)

    routes = [
        (40, "A · SONIFICATION", SEVE,
         [("Mapping paramétrique", "grandeur → hauteur, timbre, durée"),
          ("Synthèse / MIDI", "règle explicite et réversible")],
         "Le signal détermine entièrement la sortie.",
         "Vérifiable : on peut remonter du son à la donnée."),
        (330, "B · CLASSIFICATION", BLEU,
         [("Descripteurs", "moyenne, pente, variance, spectre"),
          ("Modèle appris", "→ étiquette : « stress hydrique »")],
         "Le signal sélectionne parmi des états connus.",
         "Vérifiable : matrice de confusion, jeu de test."),
        (620, "C · VERBALISATION", CUIVRE,
         [("Descripteurs → invite", "chiffres insérés dans un gabarit"),
          ("Modèle de langage", "→ phrases en langue naturelle")],
         "Le signal conditionne, le modèle rédige.",
         "Non vérifiable mot à mot : la forme vient du modèle."),
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
        p.append(txt(x + 120, 400, "Contrôle :", 7.4, col, weight="700"))
        for j, frag in enumerate(_wrap(check, 34)):
            p.append(txt(x + 120, 416 + j * 12, frag, 7.4, GRIS))
        p.append(arrow(x + 120, 118, x + 120, 146, col, 2.0,
                       "ahv" if col == SEVE else ("ahb" if col == BLEU else "ah")))

    p.append(f'<path d="M160,140 L450,120 L740,140" fill="none" stroke="{TRAIT}" stroke-width="1.2"/>')
    p.append(txt(450, 512,
                 "La part d'information réellement issue de la plante décroît de A vers C. La part de séduction croît.",
                 8.6, CUIVRE, style="italic"))
    p.append(txt(450, 534,
                 "Aucune des trois n'est illégitime — mais elles ne s'annoncent pas de la même façon.",
                 8.4, GRIS, style="italic"))
    write("tt-signal-to-language.svg", "\n".join(p), W, H)


def _wrap(s, n):
    """Découpe une chaîne en lignes d'au plus n caractères, sur les espaces."""
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
#  5. QUI PARLE ? — budget d'information
# =============================================================================
def tt_attribution():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 36, "QUI PARLE ? BUDGET D'INFORMATION D'UNE PHRASE GÉNÉRÉE",
                 11.5, NUIT, weight="700", spacing="2.2", family=SERIF))
    p.append(txt(440, 58,
                 "Répartition qualitative des sources de contenu dans une sortie textuelle",
                 8.2, GRIS, style="italic"))

    rows = [
        ("Mesure de l'arbre", 12, SEVE,
         "Les chiffres : température, humidité, tension. Réellement issus du capteur."),
        ("Choix de l'ingénieur", 23, BLEU,
         "Seuils, fenêtres, quelles grandeurs sont retenues et lesquelles sont ignorées."),
        ("Gabarit d'invite", 25, OR,
         "Le rôle assigné au modèle : « tu es un chêne bicentenaire, parle à la première personne »."),
        ("Modèle de langage", 40, CUIVRE,
         "Syntaxe, ton, métaphores, sentiment exprimé : entièrement produits par le modèle."),
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
                 "Ces proportions sont une illustration pédagogique, non une mesure.",
                 8.6, CUIVRE, weight="700"))
    p.append(txt(440, 445,
                 "Le point démontrable est l'ordre de grandeur : l'essentiel du texte ne vient pas de l'arbre.",
                 8.2, GRIS, style="italic"))
    write("tt-attribution.svg", "\n".join(p), W, H)


# =============================================================================
#  6. ÉCHELLE ÉPISTÉMIQUE
# =============================================================================
def tt_epistemic_ladder():
    W, H = 840, 520
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(420, 36, "L'ÉCHELLE ÉPISTÉMIQUE", 12.5, NUIT, weight="700",
                 spacing="3", family=SERIF))
    p.append(txt(420, 57, "Quatre registres qu'il ne faut jamais faire glisser l'un dans l'autre",
                 8.4, GRIS, style="italic"))

    steps = [
        ("MESURE", "#2F7D5E",
         "« La tension entre deux points du tronc a varié de 7 mV en 40 minutes. »",
         "Reproductible par quiconque dispose du même appareil. Chiffrée, datée, incertitude connue."),
        ("FAIT ÉTABLI", BLEU,
         "« Les plantes propagent des signaux électriques sur de longues distances. »",
         "Publié, répliqué, mécanisme identifié. Révisable, mais solidement adossé."),
        ("HYPOTHÈSE", OR,
         "« Ce signal pourrait coder l'état hydrique de l'arbre. »",
         "Formulée pour être testée. Prédit quelque chose de falsifiable. Pas encore tranchée."),
        ("INTERPRÉTATION", CUIVRE,
         "« L'arbre exprime sa soif. »",
         "Donne du sens à l'expérience. Légitime comme récit, nulle comme preuve. Non falsifiable."),
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
            p.append(txt(438, y + 99, "↓ le glissement commence ici", 7, CUIVRE,
                         anchor="start", style="italic"))
        y += 100

    p.append(txt(420, 500,
                 "Chaque affirmation de cet ouvrage est rattachée explicitement à l'un de ces quatre barreaux.",
                 8.4, NUIT, style="italic"))
    write("tt-epistemic-ladder.svg", "\n".join(p), W, H)


# =============================================================================
#  7. PILE LOGICIELLE OPEN SOURCE
# =============================================================================
def tt_stack():
    W, H = 900, 520
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "PILE LOGICIELLE LIBRE, DE L'ÉLECTRODE À LA VOIX", 12, NUIT,
                 weight="700", spacing="2.4", family=SERIF))

    tiers = [
        ("Firmware du nœud", SEVE, [("ESPHome", "YAML, OTA"), ("Tasmota", "MQTT natif"),
                                    ("MicroPython", "prototypage")]),
        ("Collecte & stockage", BLEU, [("Mosquitto", "courtier MQTT"),
                                       ("Telegraf", "agent d'ingestion"),
                                       ("InfluxDB", "séries temporelles")]),
        ("Analyse", OR, [("Python / NumPy", "descripteurs"), ("scikit-learn", "classification"),
                         ("Grafana", "tableaux de bord")]),
        ("Restitution", CUIVRE, [("SuperCollider", "synthèse temps réel"),
                                 ("Pure Data", "patch graphique"),
                                 ("Piper / Ollama", "voix · texte, en local")]),
    ]
    y = 70
    for name, col, items in tiers:
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
    p.append(txt(450, y + 26, "Tout l'étage est remplaçable et auto-hébergeable.", 9.4, NUIT,
                 weight="700"))
    p.append(txt(450, y + 42,
                 "Aucun maillon ne dépend d'un service propriétaire : c'est ce qui rend l'expérience reproductible et durable.",
                 7.8, GRIS, style="italic"))
    write("tt-stack.svg", "\n".join(p), W, H)


# =============================================================================
#  8. ARTEFACTS DE TERRAIN
# =============================================================================
def tt_noise():
    W, H = 900, 520
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "CE QUI CONTAMINE UNE MESURE EN EXTÉRIEUR", 12, NUIT,
                 weight="700", spacing="2.4", family=SERIF))

    # Tracé composite
    x0, y0, wid, hei = 70, 250, 760, 150
    p += axes(x0, y0, wid, hei, "temps (24 h)", "amplitude")
    base = []
    for k in range(0, wid, 3):
        t = k / wid * 24
        v = (math.sin((t - 6) / 24 * 2 * math.pi) * 38          # circadien
             + math.sin(t * 2.1) * 9                             # thermique
             + (18 if 9 < t < 11 else 0)                         # arrosage
             + math.sin(k * 1.7) * 5)                            # 50 Hz replié
        base.append(f"{x0+k},{y0 - 20 - v:.1f}")
    p.append(f'<polyline points="{" ".join(base)}" fill="none" stroke="{BLEU}" stroke-width="1.8"/>')
    clean = " ".join(f"{x0+k},{y0 - 20 - math.sin((k/wid*24 - 6)/24*2*math.pi)*38:.1f}"
                     for k in range(0, wid, 3))
    p.append(f'<polyline points="{clean}" fill="none" stroke="{SEVE}" stroke-width="2.2" '
             f'stroke-dasharray="7 4"/>')
    p.append(txt(x0 + wid, y0 - 130, "— signal physiologique supposé", 8, SEVE, anchor="end"))
    p.append(txt(x0 + wid, y0 - 116, "— signal réellement enregistré", 8, BLEU, anchor="end"))

    causes = [
        ("Dérive d'électrode", "Polarisation et oxydation du contact : 10 à 40 % dans la première demi-heure, puis lente dérive sur des jours.", CUIVRE),
        ("Température", "Le gain de l'amplificateur et la résistance du tissu varient avec T°. Un cycle jour/nuit se lit comme un « rythme ».", OR),
        ("Humidité de surface", "Rosée, pluie, brouillard : le film d'eau court-circuite le trajet à travers le tissu.", BLEU),
        ("Mouvement", "Vent, passage d'un promeneur, vibration : micro-déplacement de l'électrode = artefact de grande amplitude.", SEVE),
        ("Couplage secteur", "50 Hz rayonné par le réseau et les lampadaires. Sans filtre, il se replie dans la bande utile.", GRIS),
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
                 "Un signal propre en laboratoire devient, en extérieur, une somme dont la part biologique est minoritaire.",
                 8.4, CUIVRE, style="italic"))
    write("tt-noise.svg", "\n".join(p), W, H)


# =============================================================================
#  9. RYTHME CIRCADIEN DU SIGNAL
# =============================================================================
def tt_circadian():
    W, H = 860, 420
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(430, 34, "CE QUE L'ARBRE FAIT PENDANT QUE PERSONNE NE REGARDE",
                 11.5, NUIT, weight="700", spacing="2.2", family=SERIF))
    p.append(txt(430, 55, "Grandeurs physiologiques mesurables sur 24 heures",
                 8.2, GRIS, style="italic"))

    x0, y0, wid = 78, 340, 720
    # Bandes jour / nuit
    p.append(f'<rect x="{x0}" y="90" width="{wid*0.25:.0f}" height="250" fill="#E8E6DB"/>')
    p.append(f'<rect x="{x0+wid*0.79:.0f}" y="90" width="{wid*0.21:.0f}" height="250" fill="#E8E6DB"/>')
    p.append(txt(x0 + wid * 0.12, 106, "NUIT", 7.6, GRIS, spacing="1.6"))
    p.append(txt(x0 + wid * 0.52, 106, "JOUR", 7.6, OR, spacing="1.6"))
    p.append(txt(x0 + wid * 0.90, 106, "NUIT", 7.6, GRIS, spacing="1.6"))

    p += axes(x0, y0, wid, 250, "heure solaire", "")
    for h in range(0, 25, 4):
        xx = x0 + wid * h / 24
        p.append(f'<line x1="{xx}" y1="{y0}" x2="{xx}" y2="{y0+5}" stroke="{GRIS}" stroke-width="1.2"/>')
        p.append(txt(xx, y0 + 18, f"{h:02d}h", 7.4, GRIS))

    curves = [
        ("Transpiration / flux de sève", SEVE,
         lambda t: max(0, math.sin((t - 6) / 12 * math.pi)) ** 0.8 * 88),
        ("Diamètre du tronc", BLEU,
         lambda t: 44 + math.cos((t - 5) / 24 * 2 * math.pi) * 34),
        ("Potentiel bioélectrique", CUIVRE,
         lambda t: 120 + math.sin((t - 9) / 24 * 2 * math.pi) * 42),
        ("Émissions ultrasonores", OR,
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
                 "Ces rythmes sont mesurés et publiés. Ils suffisent à produire une « conversation » convaincante sans qu'aucune intention n'entre en jeu.",
                 8.2, GRIS, style="italic"))
    write("tt-circadian.svg", "\n".join(p), W, H)


# =============================================================================
# 10. FRISE DES ARBRES ET PLANTES « PARLANTS »
# =============================================================================
def tt_timeline():
    W, H = 1000, 366
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(500, 34, "CENT CINQUANTE ANS DE PLANTES QUI « RÉPONDENT »", 12, NUIT,
                 weight="700", spacing="2.4", family=SERIF))

    y = 196
    p.append(f'<line x1="56" y1="{y}" x2="950" y2="{y}" stroke="{OR}" stroke-width="2.6"/>')

    events = [
        ("1873", "Burdon-Sanderson", "Potentiel électrique mesuré chez la dionée.", SEVE, 1),
        ("1880", "Charles Darwin", "« The Power of Movement in Plants ».", SEVE, -1),
        ("1902", "J. C. Bose", "Crescographe ; réponses électriques du végétal.", SEVE, 1),
        ("1966", "Cleve Backster", "Polygraphe sur dracaena : l'« effet Backster ».", CUIVRE, -1),
        ("1973", "Tompkins & Bird", "« La Vie secrète des plantes » : diffusion mondiale.", CUIVRE, 1),
        ("1975", "Horowitz et al.", "Réfutation de l'effet Backster (Science).", BLEU, -1),
        ("1976", "Damanhur", "Premiers dispositifs de sonification végétale.", OR, 1),
        ("1997", "Suzanne Simard", "Transferts de carbone entre arbres (Nature).", BLEU, -1),
        ("2010", "Happiness Brussels", "« Talking Tree » : un arbre bruxellois sur les réseaux.", CUIVRE, 1),
        ("2015", "Alexandre Ferran", "Clavier de mots : la plante déclenche du langage.", OR, -1),
        ("2018", "Toyota & Gilroy", "Vagues calciques à longue distance (Science).", BLEU, 1),
        ("2023", "Khait et al.", "Sons aériens émis sous stress (Cell).", BLEU, -1),
        ("2023", "Karst et al.", "Critique du « wood wide web » (Nat. Ecol. Evol.).", BLEU, 1),
        ("2025", "Droga5 / Agency for Nature", "« The Talking Tree » : capteurs + LLM local.", CUIVRE, -1),
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

    p.append(txt(210, 344, "■ physiologie mesurée", 7.6, SEVE, anchor="start"))
    p.append(txt(390, 344, "■ écologie & signalisation", 7.6, BLEU, anchor="start"))
    p.append(txt(590, 344, "■ dispositifs artistiques et médiatiques", 7.6, CUIVRE, anchor="start"))
    write("tt-timeline.svg", "\n".join(p), W, H)


# =============================================================================
# 11. FLUX DE SÈVE — méthode de dissipation thermique
# =============================================================================
def tt_sap_flow():
    W, H = 820, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(410, 34, "MESURER LE FLUX DE SÈVE — MÉTHODE DE DISSIPATION THERMIQUE",
                 11, NUIT, weight="700", spacing="2", family=SERIF))
    p.append(txt(410, 55, "Principe de Granier (1985)", 8.2, GRIS, style="italic"))

    # Coupe de tronc
    cx, cy = 250, 250
    p.append(f'<circle cx="{cx}" cy="{cy}" r="132" fill="#D9CDB4" stroke="#6B5A42" stroke-width="3"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="120" fill="#E8DFC8"/>')
    for r, col, lab in ((118, "#7A6B4E", "écorce"), (106, "#9BAF7E", "cambium"),
                        (86, "#C9D9B4", "aubier (conducteur)"), (46, "#B39A6E", "duramen")):
        p.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{col}" opacity="0.9"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="#A88E62"/>')
    for r, lab, ly in ((124, "écorce", -124), (96, "aubier — c'est ici que l'eau monte", -96),
                       (30, "duramen (inerte)", -20)):
        p.append(dashline(cx, cy + ly, cx + 190, cy + ly, GRIS, 1, "3 3"))
        p.append(txt(cx + 196, cy + ly + 3.5, lab, 7.6, GRIS, anchor="start"))

    # Sondes
    for dy, lab, col in ((-34, "sonde chauffée", CUIVRE), (34, "sonde de référence", BLEU)):
        p.append(f'<rect x="{cx-6}" y="{cy+dy-4}" width="96" height="8" rx="4" fill="{col}"/>')
        p.append(f'<circle cx="{cx+90}" cy="{cy+dy}" r="6" fill="{col}"/>')
        p.append(txt(cx + 104, cy + dy + 3.5, lab, 7.6, col, anchor="start", weight="700"))
    p.append(txt(cx, cy + 6, "Δ 10 cm", 7.4, NUIT))
    p.append(f'<line x1="{cx+70}" y1="{cy-30}" x2="{cx+70}" y2="{cy+30}" stroke="{NUIT}" '
             f'stroke-width="1.2" stroke-dasharray="3 3"/>')

    # Relation
    p.append(box(520, 118, 268, 250, fill="#FFFFFF", stroke=OR))
    p.append(txt(654, 142, "Ce que l'on calcule", 10.4, OR, weight="700"))
    p.append(dashline(538, 154, 770, 154))
    formulas = [
        ("ΔT", "écart de température entre les deux sondes"),
        ("ΔTₘ", "écart maximal, mesuré de nuit à flux nul"),
        ("K = (ΔTₘ − ΔT) / ΔT", "indice de flux, sans dimension"),
        ("u = 119 × K^1,231", "densité de flux, en cm·h⁻¹"),
    ]
    yy = 176
    for f, d in formulas:
        p.append(txt(538, yy, f, 9.2, NUIT, anchor="start", weight="700", family=MONO))
        for j, frag in enumerate(_wrap(d, 40)):
            p.append(txt(538, yy + 14 + j * 10.5, frag, 7.2, GRIS, anchor="start"))
        yy += 48
    p.append(txt(654, 356, "Plus la sève monte, plus elle refroidit la sonde chauffée.",
                 7.6, SEVE, style="italic"))

    p.append(txt(410, 412,
                 "La sonde de référence annule la dérive thermique ambiante : c'est l'écart, jamais la valeur absolue, qui porte l'information.",
                 8, GRIS, style="italic"))
    write("tt-sap-flow.svg", "\n".join(p), W, H)


# =============================================================================
# 12. CAVITATION ET ÉMISSIONS ULTRASONORES
# =============================================================================
def tt_cavitation():
    W, H = 880, 420
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "L'ARBRE QUI CRAQUE : CAVITATION DANS LE XYLÈME", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    # Trois vaisseaux
    stages = [
        (90, "Colonne continue", "#9FC4DE", "L'eau est sous tension (pression négative : −0,5 à −3 MPa). La colonne tient par cohésion."),
        (350, "Rupture", "#E2B9A0", "Le stress hydrique augmente la tension. Une bulle d'air est aspirée par un pore : la colonne casse."),
        (610, "Embolie + clic", "#DED9CC", "Le vaisseau se vide. La détente libère une onde élastique : un clic ultrasonore de 20 à 100 kHz."),
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
    p.append(txt(440, 352, "Ce que cela permet — et ne permet pas", 9.4, BLEU, weight="700"))
    p.append(txt(440, 369,
                 "Le taux de clics est un indicateur reproductible du stress hydrique. Il est mécanique, non intentionnel :",
                 7.8, GRIS))
    p.append(txt(440, 382,
                 "l'arbre ne « crie » pas, il se fissure hydrauliquement — ce qui est mesurable, et déjà remarquable.",
                 7.8, GRIS))
    write("tt-cavitation.svg", "\n".join(p), W, H)


# =============================================================================
# 13. COMMUNICATION PAR COMPOSÉS VOLATILS
# =============================================================================
def tt_voc():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "LA VOIE CHIMIQUE : COMPOSÉS ORGANIQUES VOLATILS", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(440, 55, "La seule « communication » végétale à distance dont le canal soit clairement identifié",
                 8, GRIS, style="italic"))

    p.append(f'<path d="M0,400 Q440,388 880,400 L880,470 L0,470 Z" fill="#E6E2D2"/>')
    p.append(canopy_tree(180, 402, 230, seed=11, color="#3C6B50", depth=7))
    p.append(canopy_tree(660, 402, 220, seed=29, color="#3C6B50", depth=7))

    # Herbivore
    p.append(f'<ellipse cx="196" cy="268" rx="17" ry="11" fill="{CUIVRE}"/>')
    p.append(txt(196, 296, "herbivore", 7.4, CUIVRE, weight="700"))

    # Nuage de COV
    for k in range(26):
        a = k * 0.62
        rx_ = 210 + math.cos(a) * (60 + k * 8)
        ry_ = 236 + math.sin(a) * (26 + k * 2.4)
        p.append(f'<circle cx="{rx_:.0f}" cy="{ry_:.0f}" r="{4.4 - k*0.07:.1f}" '
                 f'fill="{SEVE_C}" opacity="{0.75 - k*0.02:.2f}"/>')
    p.append(txt(430, 196, "terpènes · aldéhydes en C6 · salicylate de méthyle", 8.2, SEVE,
                 weight="700"))
    p.append(txt(430, 212, "émission en quelques minutes, portée de quelques mètres",
                 7.4, GRIS, style="italic"))

    boxes = [
        (60, 92, "Émission", "La feuille blessée libère un bouquet de volatils dont la composition dépend du type d'attaque.", SEVE),
        (330, 92, "Réception", "Les tissus voisins détectent ces molécules et amorcent leurs défenses avant d'être touchés.", BLEU),
        (600, 92, "Tiers bénéficiaire", "Des parasitoïdes sont attirés par le même bouquet : l'information profite aussi aux prédateurs.", OR),
    ]
    for x, y, t, d, col in boxes:
        p.append(f'<rect x="{x}" y="{y}" width="222" height="72" rx="6" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.5"/>')
        p.append(txt(x + 111, y + 20, t, 10, col, weight="700"))
        for j, frag in enumerate(_wrap(d, 40)):
            p.append(txt(x + 111, y + 36 + j * 10.5, frag, 7.2, GRIS))

    p.append(f'<rect x="60" y="412" width="762" height="46" rx="6" fill="#FBF0E8" '
             f'stroke="#F0DCC9" stroke-width="1.2"/>')
    p.append(txt(440, 431, "« Communication » ou écoute indiscrète ?", 9, CUIVRE, weight="700"))
    p.append(txt(440, 448,
                 "Rien ne prouve que l'émettrice ait un intérêt à prévenir : la voisine capte peut-être un signal qui ne lui était pas destiné.",
                 7.6, GRIS, style="italic"))
    write("tt-voc.svg", "\n".join(p), W, H)


# =============================================================================
# 14. ANATOMIE D'UNE INVITE CAPTEURS → TEXTE
# =============================================================================
def tt_prompt():
    W, H = 880, 560
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "ANATOMIE D'UNE INVITE « CAPTEURS → PAROLE »", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    blocks = [
        ("RÔLE", CUIVRE,
         ["Tu es un chêne pédonculé de deux cents ans.",
          "Tu t'exprimes à la première personne, sobrement."],
         "Entièrement écrit par l'humain. C'est ici que naît le personnage."),
        ("DONNÉES", SEVE,
         ["T° air 14,2 °C (−1,8 en 3 h) · HR 81 %",
          "θ sol 0,19 m³/m³ (seuil bas : 0,22) · PAR 340",
          "Δ tronc −41 µm sur 6 h · vent 18 km/h"],
         "La seule partie qui vient réellement de l'arbre."),
        ("CONTRAINTES", BLEU,
         ["Trois phrases au plus. Aucune émotion inventée.",
          "Ne mentionne que les grandeurs fournies.",
          "Si une donnée manque, dis-le au lieu de combler."],
         "Le garde-fou : c'est lui qui sépare l'honnêteté de la fable."),
        ("SORTIE", OR,
         ["« Le sol autour de mes racines s'assèche :",
          "  0,19, sous mon seuil de confort. L'air a",
          "  perdu deux degrés depuis midi. »"],
         "Traçable mot à mot vers les chiffres — et seulement vers eux."),
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
    p.append(txt(440, y + 24, "La règle d'or de l'atelier", 9.2, OR, weight="700"))
    p.append(txt(440, y + 40,
                 "Toute phrase produite doit pouvoir être reliée à un nombre mesuré. Ce qui ne l'est pas est de la décoration — et doit être annoncé comme tel.",
                 7.6, GRIS, style="italic"))
    write("tt-prompt.svg", "\n".join(p), W, H)


# =============================================================================
# 15. POSE D'ÉLECTRODES SANS BLESSER L'ARBRE
# =============================================================================
def tt_electrode_tree():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "POSER DES CAPTEURS SANS BLESSER L'ARBRE", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    # Tronc en coupe verticale
    p.append(f'<rect x="150" y="80" width="130" height="330" rx="10" fill="#8A7455"/>')
    p.append(f'<rect x="162" y="80" width="106" height="330" fill="#A08A66"/>')
    for k in range(9):
        p.append(f'<path d="M162,{92+k*38} q26,10 52,0 t52,0" fill="none" stroke="#6B5A42" '
                 f'stroke-width="1.2" opacity="0.5"/>')
    p.append(txt(215, 432, "tronc", 8.4, GRIS))

    good = [
        (300, 104, "OUI", "Électrode plaquée sous un collier élastique large, jamais serré.", SEVE),
        (300, 186, "OUI", "Câble en boucle lâche : l'arbre grossit, le câble doit suivre.", SEVE),
        (300, 268, "OUI", "Contrôle et desserrage à chaque saison de croissance.", SEVE),
    ]
    bad = [
        (590, 104, "NON", "Vis ou clou dans le cambium : porte d'entrée pour les pathogènes.", CUIVRE),
        (590, 186, "NON", "Sangle serrée autour du tronc : strangulation à terme.", CUIVRE),
        (590, 268, "NON", "Câble fixé à demeure dans l'écorce : il entrera dans le bois.", CUIVRE),
    ]
    for x, y, tag, d, col in good + bad:
        p.append(f'<rect x="{x}" y="{y}" width="248" height="66" rx="6" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.5"/>')
        p.append(f'<circle cx="{x+22}" cy="{y+22}" r="12" fill="{col}"/>')
        p.append(txt(x + 22, y + 25.5, "✓" if col == SEVE else "✗", 11, "#FFFFFF", weight="700"))
        p.append(txt(x + 42, y + 26, tag, 9, col, anchor="start", weight="700", spacing="1.4"))
        for j, frag in enumerate(_wrap(d, 42)):
            p.append(txt(x + 42, y + 42 + j * 10.5, frag, 7.3, GRIS, anchor="start"))

    # Électrode correcte sur le dessin
    p.append(f'<rect x="146" y="150" width="138" height="14" rx="7" fill="none" '
             f'stroke="{SEVE}" stroke-width="2.6"/>')
    p.append(f'<rect x="258" y="146" width="22" height="22" rx="4" fill="{SEVE}"/>')
    p.append(f'<path d="M280,157 q30,26 18,60" fill="none" stroke="{SEVE}" stroke-width="2"/>')

    p.append(f'<rect x="150" y="352" width="698" height="72" rx="6" fill="#EAF3ED" '
             f'stroke="#CFE6DC" stroke-width="1.2"/>')
    p.append(txt(499, 372, "Le principe qui prime sur tous les autres", 9.4, "#2F7D5E", weight="700"))
    for j, frag in enumerate(_wrap(
            "L'arbre est un être vivant de plusieurs siècles, pas un support de montage. Toute mesure qui "
            "réduit son espérance de vie est une mesure ratée, quelle que soit la qualité du signal obtenue. "
            "En cas de doute : capteur non invasif, ou pas de capteur.", 104)):
        p.append(txt(499, 390 + j * 11.5, frag, 7.6, GRIS))
    write("tt-electrode-tree.svg", "\n".join(p), W, H)


# =============================================================================
# 16. TOPOLOGIE RÉSEAU & BUDGET ÉNERGÉTIQUE
# =============================================================================
def tt_network_power():
    W, H = 900, 480
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "AUTONOMIE ET LIAISON RADIO", 12, NUIT, weight="700",
                 spacing="3", family=SERIF))

    # --- Topologie
    p += band(40, 70, 420, 200, "TOPOLOGIE", fill=BLEU)
    p.append(canopy_tree(120, 232, 140, seed=5, color="#3C6B50", depth=6))
    p.append(canopy_tree(210, 234, 116, seed=17, color="#3C6B50", depth=6))
    for x, lbl in ((120, "nœud A"), (210, "nœud B")):
        p.append(f'<rect x="{x-14}" y="236" width="28" height="18" rx="3" fill="{OR}"/>')
        p.append(txt(x, 264, lbl, 7, GRIS))
    p += node(316, 158, 120, 54, "Passerelle", ("LoRaWAN", "→ Internet"), stroke=BLEU, ts=9.4, ls=7)
    for x in (120, 210):
        for k in range(3):
            p.append(f'<path d="M{x+16},{230-k*7} q28,{-14-k*6} {186-x+8},{-44-k*6}" '
                     f'fill="none" stroke="{BLEU}" stroke-width="1.2" opacity="{0.6-k*0.16:.2f}"/>')
    p.append(txt(250, 128, "868 MHz · SF9 · 1 message / 15 min", 7.4, BLEU, style="italic"))

    # --- Budget
    p += band(486, 70, 380, 200, "BUDGET ÉNERGÉTIQUE JOURNALIER", fill=OR)
    rows = [
        ("Veille profonde (23 h 50)", 0.3, 7.2, SEVE),
        ("Mesures (96 réveils × 4 s)", 2.1, 50.4, BLEU),
        ("Émissions radio (96 trames)", 4.0, 12.8, CUIVRE),
        ("Total consommé", None, 70.4, NUIT),
        ("Apport solaire 2 W (hiver, 1,5 h éq.)", None, 300.0, OR),
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
    p.append(txt(453, 318, "Règle de dimensionnement", 9.4, NUIT, weight="700"))
    for j, frag in enumerate(_wrap(
            "Dimensionner l'accumulateur pour dix jours sans soleil, et le panneau pour recharger en un jour "
            "d'hiver couvert. Un LiFePO₄ de 6 Ah et un panneau de 5 W tiennent confortablement ce budget ; "
            "c'est la marge, non la moyenne, qui fait survivre l'installation à décembre.", 116)):
        p.append(txt(453, 336 + j * 11.5, frag, 7.6, GRIS))

    p.append(txt(450, 398, "Pourquoi LoRaWAN plutôt que Wi-Fi", 9.4, BLEU, weight="700"))
    for j, frag in enumerate(_wrap(
            "Portée de plusieurs kilomètres en zone dégagée, consommation d'émission dix à cent fois moindre, "
            "et aucune dépendance à une borne à proximité de l'arbre. Le prix à payer : un débit minuscule "
            "(quelques dizaines d'octets par message) — ce qui interdit d'envoyer un signal brut et oblige à "
            "extraire les descripteurs sur le nœud lui-même.", 122)):
        p.append(txt(450, 416 + j * 11.5, frag, 7.6, GRIS))
    write("tt-network-power.svg", "\n".join(p), W, H)


# =============================================================================
# 17. OGHAM ET ARBRES
# =============================================================================
def tt_ogham():
    W, H = 880, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "L'OGHAM : UNE ÉCRITURE ADOSSÉE AUX ARBRES", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(440, 55, "Alphabet irlandais des IVᵉ–VIᵉ siècles, gravé sur l'arête des pierres dressées",
                 8, GRIS, style="italic"))

    # Arête verticale + encoches
    x = 140
    p.append(f'<line x1="{x}" y1="86" x2="{x}" y2="386" stroke="{NUIT}" stroke-width="3"/>')
    letters = [
        ("B", "beith", "bouleau", 1, "right"),
        ("L", "luis", "sorbier", 2, "right"),
        ("F", "fearn", "aulne", 3, "right"),
        ("S", "sail", "saule", 4, "right"),
        ("N", "nion", "frêne", 5, "right"),
        ("H", "uath", "aubépine", 1, "left"),
        ("D", "dair", "chêne", 2, "left"),
        ("T", "tinne", "houx", 3, "left"),
        ("C", "coll", "noisetier", 4, "left"),
        ("Q", "ceirt", "pommier", 5, "left"),
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
    p.append(txt(653, 114, "Ce qui est attesté", 10, SEVE, weight="700"))
    for j, frag in enumerate(_wrap(
            "L'ogham est une écriture réelle, documentée par environ 400 inscriptions lapidaires en Irlande et "
            "au pays de Galles. Les gloses médiévales associent chaque lettre à un nom, souvent d'arbre. "
            "L'ordre et la valeur des lettres sont établis.", 58)):
        p.append(txt(490, 136 + j * 12, frag, 7.6, GRIS, anchor="start"))

    p.append(f'<rect x="470" y="242" width="366" height="144" rx="7" fill="#FBF0E8" '
             f'stroke="#F0DCC9" stroke-width="1.5"/>')
    p.append(txt(653, 264, "Ce qui ne l'est pas", 10, CUIVRE, weight="700"))
    for j, frag in enumerate(_wrap(
            "Le « calendrier des arbres » et le système divinatoire qu'on lui associe sont une reconstruction "
            "du XXᵉ siècle, largement due à Robert Graves (« The White Goddess », 1948). C'est une création "
            "poétique moderne, non une tradition celtique transmise. La dire ancienne est une erreur ; la "
            "pratiquer en le sachant est un choix.", 58)):
        p.append(txt(490, 286 + j * 12, frag, 7.6, GRIS, anchor="start"))
    write("tt-ogham.svg", "\n".join(p), W, H)


# =============================================================================
# 18. LES TROIS LECTURES D'UN MÊME ÉVÉNEMENT
# =============================================================================
def tt_three_readings():
    W, H = 880, 450
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "UN MÊME ÉVÉNEMENT, TROIS LECTURES LÉGITIMES", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    p.append(f'<rect x="230" y="62" width="420" height="52" rx="7" fill="{NUIT}"/>')
    p.append(txt(440, 82, "L'ÉVÉNEMENT", 8, OR_CL, weight="700", spacing="2"))
    p.append(txt(440, 100, "À 15 h 20, le tracé s'infléchit brusquement de 9 mV pendant 4 minutes.",
                 8.6, "#FFFFFF"))

    cols = [
        (48, "LECTURE INSTRUMENTALE", BLEU,
         ["Vérifier d'abord l'artefact : vent,",
          "passage d'un promeneur, rosée,",
          "contact d'électrode.",
          "",
          "Si rien n'explique : consigner",
          "l'événement, chercher la",
          "corrélation avec les autres voies."],
         "Question : qu'est-ce qui a bougé dans la chaîne de mesure ?"),
        (318, "LECTURE PHYSIOLOGIQUE", SEVE,
         ["Une variation de cet ordre est",
          "compatible avec un potentiel de",
          "variation d'origine hydraulique.",
          "",
          "Hypothèse testable : corréler",
          "avec le flux de sève et le",
          "déficit de saturation de l'air."],
         "Question : quel mécanisme connu produirait cela ?"),
        (588, "LECTURE SENSIBLE", OR,
         ["Le praticien note ce qu'il",
          "percevait au même instant,",
          "sans le lire dans l'appareil.",
          "",
          "La note se fait à l'aveugle,",
          "horodatée, avant consultation",
          "des tracés."],
         "Question : que se passait-il pour moi à cet instant ?"),
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
    p.append(txt(440, 414, "Les trois colonnes ne se contredisent pas — elles ne répondent pas à la même question.",
                 8.6, NUIT, weight="700"))
    p.append(txt(440, 430,
                 "La faute n'est pas de tenir les trois. Elle est de présenter la troisième avec l'autorité de la première.",
                 7.8, CUIVRE, style="italic"))
    write("tt-three-readings.svg", "\n".join(p), W, H)


# =============================================================================
# 19. COMPARATIF DES DEUX « TALKING TREES »
# =============================================================================
def tt_comparison():
    W, H = 880, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "DEUX « TALKING TREES », QUINZE ANS D'ÉCART", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))

    heads = [(80, "BRUXELLES · 2010", CUIVRE, "Happiness Brussels, pour le magazine EOS"),
             (470, "LONDRES · AUSTIN · DUBLIN · 2025", BLEU, "Droga5, pour Agency for Nature")]
    for x, t, col, sub in heads:
        p.append(f'<rect x="{x}" y="66" width="330" height="46" rx="7" fill="{col}"/>')
        p.append(txt(x + 165, 86, t, 9.4, "#FFFFFF", weight="700", spacing="1.4"))
        p.append(txt(x + 165, 102, sub, 7.4, "#FFFFFF", style="italic"))

    rows = [
        ("Arbre", "Un arbre centenaire, à Bruxelles.",
         "Trois arbres successifs : 150, 50 et 200 ans."),
        ("Capteurs", "Ozone, particules fines, luxmètre, station météo, webcam, microphone.",
         "Une dizaine : bioélectrique, sol, air, lumière, vent."),
        ("Traitement", "Logiciel sur mesure : des règles fixes produisent un message.",
         "Modèle de langage exécuté hors ligne sur un Mac Mini."),
        ("Voix", "Publications différées sur Facebook, Twitter, Flickr, SoundCloud.",
         "Dialogue vocal en direct : le visiteur s'assoit et parle."),
        ("Ce qui vient de l'humain", "Chaque phrase, écrite à l'avance.",
         "Le rôle, les contraintes, et tout le style."),
        ("Vérifiabilité", "Totale : le jeu de règles est fini et inspectable.",
         "Nulle de l'extérieur : ni code, ni données, ni modèle publiés."),
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
                 "Le progrès technique est réel. Il porte sur la fluidité de la langue, non sur la quantité d'information venue de l'arbre.",
                 8.2, CUIVRE, style="italic"))
    p.append(txt(440, y + 44,
                 "Le dispositif de 2010 était plus honnête sur ce point : nul ne pouvait croire que le chêne rédigeait ses messages.",
                 8, GRIS, style="italic"))
    write("tt-comparison.svg", "\n".join(p), W, H)


# =============================================================================
# 20. MODES DE SONIFICATION
# =============================================================================
def tt_sonification_modes():
    W, H = 880, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(440, 34, "TROIS MODES DE SONIFICATION", 12, NUIT, weight="700",
                 spacing="3", family=SERIF))

    modes = [
        (50, "AUDIFICATION", SEVE,
         "Le signal EST le son : on l'accélère jusqu'à le rendre audible.",
         "Fidèle, sans interprétation. Exige un signal riche et rapide.",
         lambda k: math.sin(k / 3.0) * 22 + math.sin(k / 1.1) * 9),
        (330, "MAPPING PARAMÉTRIQUE", BLEU,
         "Chaque grandeur pilote un paramètre : hauteur, durée, timbre, intensité.",
         "Souple et lisible. Le choix du mapping est entièrement arbitraire.",
         lambda k: (round(math.sin(k / 12.0) * 3) * 7)),
        (610, "SONIFICATION MODÉLISÉE", OR,
         "Les données pilotent un modèle physique virtuel que l'on écoute vibrer.",
         "Très expressif. La part du modèle devient difficile à démêler.",
         lambda k: math.sin(k / 9.0) * 20 * math.exp(-((k % 60) / 40.0))),
    ]
    for x, t, col, d1, d2, fn in modes:
        p.append(f'<rect x="{x}" y="76" width="240" height="286" rx="8" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.8"/>')
        p.append(f'<rect x="{x}" y="76" width="240" height="26" rx="8" fill="{col}"/>')
        p.append(f'<rect x="{x}" y="92" width="240" height="10" fill="{col}"/>')
        p.append(txt(x + 120, 94, t, 7.8, "#FFFFFF", weight="700", spacing="1.4"))
        # tracé
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
                 "Dans les trois cas, c'est une règle humaine qui décide de ce que l'on entend. Publier la règle est ce qui distingue une œuvre honnête d'un tour de passe-passe.",
                 8.2, GRIS, style="italic"))
    write("tt-sonification-modes.svg", "\n".join(p), W, H)


# =============================================================================
# 21. PROTOCOLE D'OBSERVATION (roue des sept séances)
# =============================================================================
def tt_protocol_wheel():
    W, H = 760, 620
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(380, 36, "PROTOCOLE D'OBSERVATION EN SEPT SÉANCES", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(380, 57, "Une même heure, un même arbre, sept fois", 8.2, GRIS, style="italic"))

    cx, cy, R = 380, 330, 190
    p.append(f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{TRAIT}" stroke-width="1.6"/>')
    p.append(f'<circle cx="{cx}" cy="{cy}" r="72" fill="{NUIT}"/>')
    p.append(txt(cx, cy - 8, "ARBRE", 10, OR_CL, weight="700", spacing="2.4", family=SERIF))
    p.append(txt(cx, cy + 10, "TÉMOIN", 10, OR_CL, weight="700", spacing="2.4", family=SERIF))
    p.append(txt(cx, cy + 30, "le même, toujours", 6.8, "#9FB8AB", style="italic"))

    seances = [
        ("1", "Reconnaissance", "Aucun appareil. Décrire le lieu, l'arbre, la lumière, le sol."),
        ("2", "Étalonnage", "Poser les capteurs, laisser stabiliser 2 h, ne rien interpréter."),
        ("3", "Référence", "Enregistrer une journée entière sans intervenir. C'est le témoin."),
        ("4", "Perturbation douce", "Arrosage mesuré. Noter l'heure exacte avant de regarder."),
        ("5", "Présence", "Rester 40 min près de l'arbre. Consigner à l'aveugle ses perceptions."),
        ("6", "Contre-épreuve", "Même protocole, capteur posé sur un support inerte."),
        ("7", "Confrontation", "Superposer les trois journaux. Chercher ce qui ne colle pas."),
    ]
    for i, (n, t, d) in enumerate(seances):
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
                 "La séance 6 est celle que tout le monde saute. C'est la seule qui puisse vous détromper.",
                 8.2, CUIVRE, style="italic"))
    write("tt-protocol-wheel.svg", "\n".join(p), W, H)


# =============================================================================
# 22. ESPACE D'EMBEDDINGS
# =============================================================================
def tt_embedding():
    W, H = 860, 440
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(430, 34, "PROJETER UN SIGNAL DANS UN ESPACE DE MOTS", 11.5, NUIT,
                 weight="700", spacing="2.2", family=SERIF))
    p.append(txt(430, 55, "L'idée séduisante — et ce qu'elle suppose en silence", 8.2, GRIS,
                 style="italic"))

    # Espace 2D
    p.append(f'<rect x="440" y="86" width="330" height="270" rx="8" fill="#FFFFFF" '
             f'stroke="{TRAIT}" stroke-width="1.4"/>')
    p.append(txt(605, 106, "espace vectoriel de la langue", 8, GRIS, style="italic"))
    words = [("soif", 540, 180, CUIVRE), ("sécheresse", 636, 156, CUIVRE),
             ("aridité", 700, 196, CUIVRE), ("fraîcheur", 520, 300, BLEU),
             ("pluie", 604, 320, BLEU), ("humide", 686, 288, BLEU),
             ("vent", 720, 250, SEVE), ("lumière", 500, 240, OR)]
    for w, x, y, col in words:
        p.append(f'<circle cx="{x}" cy="{y}" r="4.5" fill="{col}" opacity="0.85"/>')
        p.append(txt(x + 8, y + 3.5, w, 7.6, col, anchor="start"))
    p.append(f'<circle cx="596" cy="196" r="9" fill="none" stroke="{NUIT}" stroke-width="2.2"/>')
    p.append(f'<circle cx="596" cy="196" r="3" fill="{NUIT}"/>')
    p.append(txt(596, 176, "point projeté", 7.4, NUIT, weight="700"))
    for w, x, y, col in words[:3]:
        p.append(dashline(596, 196, x, y, NUIT, 1, "3 3"))

    # Chaîne
    steps = [("Descripteurs", "θ, T°, Δtronc, PAR"),
             ("Projection", "matrice apprise W"),
             ("Voisins", "mots les plus proches"),
             ("Rédaction", "phrase contrainte")]
    y = 108
    for i, (t, sub) in enumerate(steps):
        p += node(70, y, 250, 52, t, (sub,), stroke=BLEU, ts=10, ls=7.4)
        if i < 3:
            p.append(arrow(195, y + 54, 195, y + 68, BLEU, 1.8, "ahb"))
        y += 68
    p.append(arrow(324, 200, 434, 200, BLEU, 2, "ahb"))

    p.append(f'<rect x="70" y="378" width="720" height="48" rx="6" fill="#FBF0E8" '
             f'stroke="#F0DCC9" stroke-width="1.2"/>')
    p.append(txt(430, 396, "Le présupposé caché", 9, CUIVRE, weight="700"))
    p.append(txt(430, 412,
                 "La matrice W est apprise sur des couples (mesure, mot) choisis par un humain. Le sens ne sort pas du signal : il y a été mis, puis retrouvé.",
                 7.6, GRIS, style="italic"))
    write("tt-embedding.svg", "\n".join(p), W, H)


# =============================================================================
# 23. PLAN D'IMPLANTATION SUR LE TERRAIN
# =============================================================================
def tt_site_plan():
    W, H = 840, 470
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(420, 34, "PLAN D'IMPLANTATION", 12, NUIT, weight="700", spacing="3",
                 family=SERIF))
    p.append(txt(420, 55, "Vue de dessus — un arbre, ses capteurs et sa zone de protection",
                 8.2, GRIS, style="italic"))

    cx, cy = 330, 262
    # Zone racinaire
    p.append(f'<circle cx="{cx}" cy="{cy}" r="170" fill="#EDEADB" stroke="{SEVE_C}" '
             f'stroke-width="1.6" stroke-dasharray="7 5"/>')
    p.append(txt(cx, cy - 152, "zone racinaire protégée — aucun engin, aucun tassement",
                 7.4, SEVE, style="italic"))
    # Houppier
    p.append(f'<circle cx="{cx}" cy="{cy}" r="118" fill="#D7E3D2" opacity="0.75"/>')
    p.append(txt(cx + 84, cy - 92, "projection du houppier", 7.2, GRIS, anchor="start"))
    # Tronc
    p.append(f'<circle cx="{cx}" cy="{cy}" r="26" fill="#8A7455" stroke="#5C4B34" stroke-width="2"/>')

    pts = [
        (cx, cy - 26, "E1", "électrodes nord", CUIVRE, 0, -44),
        (cx + 26, cy, "E2", "électrodes sud", CUIVRE, 44, 6),
        (cx - 92, cy + 40, "P1", "sonde de sol 20 cm", SEVE, -60, 24),
        (cx + 96, cy + 62, "P2", "sonde de sol 60 cm", SEVE, 44, 18),
        (cx - 8, cy - 118, "M1", "abri météo 2 m", BLEU, -30, -24),
        (cx + 62, cy - 84, "A1", "capteur acoustique", OR, 52, -14),
        (cx + 150, cy - 140, "S1", "panneau solaire plein sud", OR, 16, -18),
    ]
    for x, y, code, lab, col, dx, dy in pts:
        p.append(f'<circle cx="{x}" cy="{y}" r="9" fill="{col}" stroke="#FFF" stroke-width="1.8"/>')
        p.append(txt(x, y + 3.2, code, 6.6, "#FFFFFF", weight="700"))
        p.append(txt(x + dx, y + dy, lab, 7.2, col,
                     anchor="start" if dx >= 0 else "end", weight="700"))

    # Légende / distances
    p.append(f'<rect x="580" y="96" width="242" height="304" rx="7" fill="#FFFFFF" '
             f'stroke="{TRAIT}" stroke-width="1.2"/>')
    p.append(txt(701, 118, "Règles d'implantation", 9.6, NUIT, weight="700"))
    p.append(dashline(596, 130, 806, 130))
    rules = [
        ("Électrodes", "Deux paires opposées : le différentiel annule le mode commun."),
        ("Sondes de sol", "Deux profondeurs au moins, hors du cheminement piéton."),
        ("Abri météo", "À 2 m, ventilé, jamais contre le tronc ni en plein soleil."),
        ("Coffret", "Au nord du tronc, sur collier large, à 1,80 m du sol."),
        ("Câbles", "En goulotte souple, boucle de dilatation à chaque extrémité."),
        ("Signalétique", "Un panneau explique l'installation : il évite le vandalisme."),
    ]
    yy = 146
    for t, d in rules:
        p.append(txt(596, yy, t, 8, SEVE, anchor="start", weight="700"))
        for j, frag in enumerate(_wrap(d, 40)):
            p.append(txt(596, yy + 12 + j * 10.5, frag, 7, GRIS, anchor="start"))
        yy += 44

    p.append(txt(420, 440,
                 "Le plan est daté, photographié et archivé : sans lui, aucune mesure ne sera réinterprétable dans cinq ans.",
                 8, GRIS, style="italic"))
    write("tt-site-plan.svg", "\n".join(p), W, H)


# =============================================================================
# 24. LE CLAVIER DE MOTS (Alexandre Ferran, 2015)
# =============================================================================
def tt_word_keyboard():
    W, H = 900, 500
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "LE CLAVIER DE MOTS", 12.5, NUIT, weight="700", spacing="3",
                 family=SERIF))
    p.append(txt(450, 55, "Remplacer les notes par des mots : le geste, et ce qu'il déplace",
                 8.2, GRIS, style="italic"))

    # Chaîne
    chain = [
        ("Plante + pinces", "variation d'impédance", SEVE),
        ("Pont de Wheatstone", "→ tension", SEVE),
        ("Conversion MIDI", "→ numéro de note", BLEU),
        ("Seuil de 4 s", "filtre anti-rebond", OR),
        ("Échantillonneur", "note → fichier son", CUIVRE),
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
    keys = ["SOLEIL", "AIDE", "MALADE", "TERRE", "CHAUD", "MERCI", "OUI", "NON"]
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
    p.append(txt(450, 330, "≈ 50 mots, choisis par l'opérateur, un par touche", 8.4, GRIS,
                 style="italic"))
    p.append(f'<path d="M779,156 v26 H450" fill="none" stroke="{CUIVRE}" stroke-width="2.2"/>')
    p.append(arrow(450, 182, 450, 208, CUIVRE, 2.2))

    # Deux colonnes de lecture
    cols = [
        (60, "CE QUE CELA CHANGE", SEVE,
         ["Le signal est inchangé : mêmes",
          "variations, même appareil, même",
          "seuil. Seule la banque de sons",
          "a été remplacée.",
          "",
          "Aucune information nouvelle",
          "n'entre dans le système."]),
        (470, "CE QUE CELA DÉPLACE", CUIVRE,
         ["Une note n'a pas de référent ;",
          "un mot en a un. L'auditeur",
          "fournit désormais le sens.",
          "",
          "La charge interprétative migre",
          "de l'appareil vers l'humain —",
          "et devient invisible."]),
    ]
    for x, t, col, lines in cols:
        p.append(f'<rect x="{x}" y="348" width="370" height="132" rx="7" fill="#FFFFFF" '
                 f'stroke="{col}" stroke-width="1.6"/>')
        p.append(txt(x + 185, 370, t, 9.2, col, weight="700", spacing="1.6"))
        for i, l in enumerate(lines):
            p.append(txt(x + 20, 390 + i * 13, l, 7.6, NUIT, anchor="start"))
    write("tt-word-keyboard.svg", "\n".join(p), W, H)


# =============================================================================
# 25. LES TROIS TESTS DE CONTRÔLE
# =============================================================================
def tt_control_tests():
    W, H = 900, 480
    p = [ARROWDEFS, f'<rect width="{W}" height="{H}" fill="{IVOIRE}"/>']
    p.append(txt(450, 34, "LES TROIS TESTS QUI DÉCIDENT DE TOUT", 12.5, NUIT,
                 weight="700", spacing="2.6", family=SERIF))
    p.append(txt(450, 55, "À faire avant toute présentation publique — et à publier avec le résultat",
                 8.2, GRIS, style="italic"))

    tests = [
        (40, "1", "L'ÉPREUVE DU VIDE", CUIVRE,
         ["Débrancher la pince. La poser",
          "sur une bouteille d'eau. Injecter",
          "du bruit blanc à la place du",
          "signal."],
         "Le système doit produire du non-sens visible.",
         "S'il produit encore de belles phrases, elles ne venaient pas de la plante."),
        (320, "2", "L'ABLATION", BLEU,
         ["Remplacer le signal par un tirage",
          "au hasard dans le même",
          "vocabulaire. Faire écouter les",
          "deux versions à l'aveugle."],
         "Un auditeur doit pouvoir les distinguer.",
         "Sinon, le signal n'apporte rien : c'est le résultat de Tan et al., NeurIPS 2024."),
        (600, "3", "LE PRÉ-ENREGISTREMENT", SEVE,
         ["Fixer par écrit, avant la séance :",
          "le vocabulaire, le seuil, la fenêtre",
          "d'écoute, la durée. Horodater.",
          "Aucune édition ensuite."],
         "Le protocole précède la donnée.",
         "C'est ce qui interdit de choisir après coup le passage qui « parle »."),
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
    p.append(txt(450, 442, "Un dispositif qui ne publie pas ses conditions d'échec ne publie rien.",
                 9.4, OR_CL, weight="700"))
    p.append(txt(450, 458,
                 "Ces trois tests ne détruisent pas l'œuvre : ils la rendent défendable.",
                 7.8, "#9FB8AB", style="italic"))
    write("tt-control-tests.svg", "\n".join(p), W, H)


# =============================================================================
# 26. FIGURES D'OUVERTURE SUPPLÉMENTAIRES
# =============================================================================
def tt_cover_art():
    """Couverture du volume I : un arbre nocturne traversé de flux de données."""
    W, H = 680, 960
    p = [f'<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0" stop-color="#071A14"/><stop offset="0.55" stop-color="{NUIT}"/>'
         f'<stop offset="1" stop-color="#11291F"/></linearGradient>'
         f'<radialGradient id="glow" cx="0.5" cy="0.62" r="0.5">'
         f'<stop offset="0" stop-color="{SEVE_C}" stop-opacity="0.38"/>'
         f'<stop offset="1" stop-color="{NUIT}" stop-opacity="0"/></radialGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#sky)"/>',
         f'<rect width="{W}" height="{H}" fill="url(#glow)"/>']

    # Étoiles
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

    # Flux de données montant le long du tronc
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

    # Voile sombre derrière la zone de titre, pour détacher la typographie
    p.append('<defs><linearGradient id="veil" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#071A14" stop-opacity="0"/>'
             '<stop offset="0.22" stop-color="#071A14" stop-opacity="0.62"/>'
             '<stop offset="0.72" stop-color="#071A14" stop-opacity="0.62"/>'
             '<stop offset="1" stop-color="#071A14" stop-opacity="0"/>'
             '</linearGradient></defs>')
    p.append(f'<rect x="0" y="56" width="{W}" height="300" fill="url(#veil)"/>')

    # Onde sonore en bas
    for k in range(4):
        amp = 26 - k * 5
        pts = " ".join(f"{x},{880 + math.sin(x / (22.0 - k * 3)) * amp:.1f}"
                       for x in range(40, W - 40, 4))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{OR if k % 2 else SEVE_C}" '
                 f'stroke-width="{1.8-k*0.32:.1f}" opacity="{0.55-k*0.1:.2f}"/>')

    # Capteurs lumineux sur le tronc
    for y in (600, 664, 728):
        p.append(f'<circle cx="340" cy="{y}" r="5.5" fill="{OR_CL}" opacity="0.9"/>')
        p.append(f'<circle cx="340" cy="{y}" r="12" fill="none" stroke="{OR_CL}" '
                 f'stroke-width="1" opacity="0.4"/>')
    write("tt-cover-art.svg", "\n".join(p), W, H)


def tt_part_bg(n, seed):
    """Fond d'ouverture de partie, variante « arbre connecté »."""
    import random as _r
    W, H = 680, 960
    rng = _r.Random(seed)
    p = [f'<defs><linearGradient id="g{n}" x1="0" y1="0" x2="0.6" y2="1">'
         f'<stop offset="0" stop-color="#081C15"/><stop offset="1" stop-color="{NUIT2}"/>'
         f'</linearGradient></defs>',
         f'<rect width="{W}" height="{H}" fill="url(#g{n})"/>']
    # Réseau de points (constellation de capteurs)
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
    # Silhouette d'arbre en filigrane
    p.append(f'<g opacity="0.28">{canopy_tree(rng.choice([170, 340, 510]), 906, 460, seed=seed, color="#2A5741", depth=8, leaf="#3E7F5E")}</g>')
    # Filet doré
    p.append(f'<rect x="28" y="28" width="{W-56}" height="{H-56}" fill="none" '
             f'stroke="{OR}" stroke-width="0.8" opacity="0.32"/>')
    write(f"tt-part-bg-{n}.svg", "\n".join(p), W, H)


# =============================================================================
def main():
    print("• Illustrations « L'Arbre qui Parle »…")
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
    print(f"✓ {n} illustrations « tt- » générées dans {HERE}")


if __name__ == "__main__":
    main()
