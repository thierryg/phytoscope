#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/build.py
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
Build « La Musique des Plantes — Dialogue Vibratoire avec le Monde Végétal »

Assemble les fragments HTML de pdf-src/parts/, génère un sommaire cliquable
(numéros de page via target-counter de WeasyPrint), puis rend le PDF final
avec métadonnées, signets et pagination.

Usage : python3 build.py
"""
import os, re, sys

ROOT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC   = os.path.join(ROOT, "pdf-src")
PARTS = os.path.join(SRC, "la-musique-des-plantes")
OUT   = os.path.join(ROOT, "build", "La-Musique-des-Plantes.pdf")

# --- Ordre canonique des fragments (sans extension) --------------------------
ORDER = [
    "00-cover",
    "01-titlepage",
    "01b-epigraph",
    "02-notice",
    "03-toc",              # contient le marqueur <!--TOC_HERE-->
    "04-introduction",

    "10-part1",  "11-part1-content",    # I.   Histoire
    "20-part2",  "21-part2-content",    # II.  Fondements scientifiques
                 "22-part2-content",    #      Chimie du signal & électrochimie
                 "23-part2-content",    #      Le polygraphe
    "30-part3",  "31-part3-content",    # III. Principe de fonctionnement
    "40-part4",  "41-part4-content",    # IV.  Analyse technique (brevets)
                 "42-part4-content",    #      Brevets PlantWave & autres
                 "43-part4-content",    #      Corpus complet des brevets
    "50-part5",  "51-part5-content",    # V.   Comparatif des solutions
    "60-part6",  "61-part6-content",    # VI.  Utilisation pratique
                 "62-part6-content",    #      Manuels opérationnels FR
                 "63-part6-content",    #      MIDI & intégration audio
    "70-part7",  "71-part7-content",    # VII. Approche énergétique
    "80-part8",  "81-part8-content",    # VIII.Exercices & rituels
    "90-part9",  "91-part9-content",    # IX.  Protocoles reproductibles
                 "92-part9-content",    #      Humain & animal
    "95-part10", "96-part10-content",   # X.   Dispositif DIY
                 "97-part10-content",   #      Montage, code, calibration
                 "98-part10-content",   #      Variantes & mise au point

    "A0-annexes",
    "A0b-codes",
    "A1-glossaire",
    "A2-biblio",
    "A2b-sites",
    "A3-index",
    "A4-toc-fin",
    "99-colophon",
]


def read_fragment(name):
    path = os.path.join(PARTS, name + ".html")
    if not os.path.exists(path):
        print(f"  · manquant : {name}.html  (ignoré)")
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def strip_tags(s):
    s = re.sub(r"<sup.*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def collect_toc_items(body_html):
    """Repère les éléments porteurs de data-toc pour construire le sommaire."""
    items = []
    pat = re.compile(
        r'<(h1|h2|h3)[^>]*\bdata-toc="(part|chapter|sub)"[^>]*\bid="([^"]+)"[^>]*>(.*?)</\1>',
        re.S)
    pat2 = re.compile(
        r'<(h1|h2|h3)[^>]*\bid="([^"]+)"[^>]*\bdata-toc="(part|chapter|sub)"[^>]*>(.*?)</\1>',
        re.S)
    seen = set()
    for m in pat.finditer(body_html):
        items.append((m.start(), m.group(2), m.group(3), strip_tags(m.group(4))))
        seen.add(m.group(3))
    for m in pat2.finditer(body_html):
        if m.group(2) in seen:
            continue
        items.append((m.start(), m.group(3), m.group(2), strip_tags(m.group(4))))
    items.sort(key=lambda x: x[0])
    return items


def render_toc(items, with_sub=True):
    out = []
    for _, lvl, hid, text in items:
        if lvl == "part":
            out.append(
                f'<li class="toc-part"><a class="tl-part" href="#{hid}">'
                f'<span class="t">{text}</span><span class="leader"></span></a></li>')
        elif lvl == "chapter":
            out.append(
                f'<li><a class="tl" href="#{hid}">'
                f'<span class="t">{text}</span><span class="leader"></span></a></li>')
        elif with_sub:
            out.append(
                f'<li><a class="tl sub" href="#{hid}">'
                f'<span class="t">{text}</span><span class="leader"></span></a></li>')
    return "<ul>\n" + "\n".join(out) + "\n</ul>"


def check_ids(body):
    """Signale les identifiants dupliqués (cassent les renvois de pages)."""
    ids = re.findall(r'\bid="([^"]+)"', body)
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        print(f"  ! identifiants dupliqués : {', '.join(sorted(dup))}")
    return dup


def check_links(body):
    """Signale les ancres internes pointant vers un id inexistant."""
    ids = set(re.findall(r'\bid="([^"]+)"', body))
    refs = set(re.findall(r'href="#([^"]+)"', body))
    manquants = refs - ids
    if manquants:
        print(f"  ! ancres mortes ({len(manquants)}) : "
              f"{', '.join(sorted(manquants)[:12])}"
              f"{' …' if len(manquants) > 12 else ''}")
    return manquants


def main():
    print("• Assemblage des fragments…")
    body_parts = [read_fragment(n) for n in ORDER]
    body = "\n".join(bp for bp in body_parts if bp.strip())

    print("• Génération des sommaires (target-counter)…")
    items = collect_toc_items(body)
    print(f"  · {len(items)} entrées repérées")
    if "<!--TOC_HERE-->" in body:
        body = body.replace("<!--TOC_HERE-->", render_toc(items, with_sub=False))
    else:
        print("  ! marqueur <!--TOC_HERE--> introuvable — sommaire non inséré")
    if "<!--TOC_FULL-->" in body:
        body = body.replace("<!--TOC_FULL-->", render_toc(items, with_sub=True))

    print("• Vérifications…")
    check_ids(body)
    check_links(body)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<title>La Musique des Plantes — Dialogue Vibratoire avec le Monde Végétal</title>
<meta name="author" content="Bretagne Namasté"/>
<meta name="publisher" content="Bretagne Namasté"/>
<meta name="copyright" content="© 2026 Bretagne Namasté — https://bretagne-namaste.com"/>
<meta name="contact" content="contact@bretagne-namaste.com"/>
<meta name="source" content="https://bretagne-namaste.com"/>
<meta name="description" content="Approche énergétique, scientifique et spirituelle de la conscience végétale et des dispositifs de bio-sonification : électrophysiologie, MIDI, protocoles d'écoute, comparatif des appareils et fabrication DIY."/>
<meta name="keywords" content="musique des plantes, bio-sonification, électrophysiologie végétale, biofeedback, MIDI, Damanhur, PlantWave, Plants Play, conscience végétale, druidisme, géobiologie, énergétique, arbre, communication végétale, DIY, NE555, pont de Wheatstone"/>
<meta name="dcterms.created" content="2026-09-16"/>
<meta name="generator" content="WeasyPrint"/>
<link rel="stylesheet" href="fonts.css"/>
<link rel="stylesheet" href="book.css"/>
</head>
<body>
{body}
</body>
</html>"""

    assembled = os.path.join(SRC, "_book.html")
    with open(assembled, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"• HTML assemblé : {assembled}  ({len(html)//1024} Ko)")

    print("• Rendu PDF avec WeasyPrint…")
    from weasyprint import HTML
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    HTML(filename=assembled, base_url=SRC).write_pdf(OUT, uncompressed_pdf=False)
    size = os.path.getsize(OUT) / (1024 * 1024)
    print(f"✓ PDF généré : {OUT}  ({size:.1f} Mo)")


if __name__ == "__main__":
    main()
