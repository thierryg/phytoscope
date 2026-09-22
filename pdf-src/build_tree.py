#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/build_tree.py
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
Build de la série « L'Arbre qui Parle » — Ateliers BN.

Trois ouvrages partagent la même charte graphique (pdf-src/arbre.css) et le même
moteur de rendu. Chaque volume possède son propre répertoire de fragments
dans pdf-src/parts/<volume>/ et sa propre liste ORDER.

Usage :
    python3 build.py              # construit les trois volumes
    python3 build.py v1           # construit le volume 1 seulement
    python3 build.py v1 v3        # construit les volumes 1 et 3
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pdf-src")
BUILD = os.path.join(ROOT, "build")

DATE = "2026-09-17"
AUTEUR = "Ateliers BN"

# =============================================================================
#  DÉFINITION DES TROIS VOLUMES
# =============================================================================
BOOKS = {
    "v1": {
        "dir": "arbre-parlant-dublin",
        "out": "arbre-parlant-dublin-analyse-scientifique.pdf",
        "title": "L'Arbre qui Parle — Dublin, anatomie d'un arbre connecté",
        "running": "L'Arbre qui Parle",
        "description": (
            "Analyse scientifique, technique et symbolique du « Talking Tree » de "
            "Dublin : capteurs, électrophysiologie végétale, architecture "
            "d'intelligence artificielle, épistémologie de la traduction et "
            "lectures traditionnelles."
        ),
        "keywords": (
            "Talking Tree, Dublin, arbre parlant, intelligence artificielle, "
            "électrophysiologie végétale, capteurs, biofeedback, sonification, "
            "effet ELIZA, LLM, druidisme, ogham, chamanisme, géobiologie, "
            "communication végétale, Evan Greally"
        ),
        "order": [
            "00-cover", "01-titlepage", "01b-epigraph", "02-notice",
            "03-toc", "04-introduction",
            "10-part1", "11-part1-content", "12-part1-content",
            "20-part2", "21-part2-content", "22-part2-content",
            "30-part3", "31-part3-content", "32-part3-content",
            "40-part4", "41-part4-content", "42-part4-content",
            "50-part5", "51-part5-content", "52-part5-content",
            "60-part6", "61-part6-content", "62-part6-content",
            "70-part7", "71-part7-content",
            "80-part8", "81-part8-content",
            "A0-annexes", "A1-glossaire", "A2-biblio", "A3-index",
            "A4-credits", "99-colophon",
        ],
    },
    "v2": {
        "dir": "biocommunication-vegetale-et-ia",
        "out": "biocommunication-vegetale-et-ia.pdf",
        "title": "Biocommunication Végétale et Intelligence Artificielle",
        "running": "Biocommunication Végétale & IA",
        "description": (
            "Traité avancé de la signalisation végétale et de sa traduction "
            "machine : électrophysiologie, bioacoustique, composés volatils, "
            "réseaux mycorhiziens, sonification et modèles de langage."
        ),
        "keywords": (
            "biocommunication végétale, électrophysiologie, potentiel d'action, "
            "bioacoustique, phytoacoustique, composés organiques volatils, "
            "réseaux mycorhiziens, wood wide web, sonification, apprentissage "
            "automatique, LLM, plant neurobiology, conscience végétale"
        ),
        "order": [
            "00-cover", "01-titlepage", "01b-epigraph", "02-notice",
            "03-toc", "04-introduction",
            "10-part1", "11-part1-content",
            "20-part2", "21-part2-content", "22-part2-content",
            "30-part3", "31-part3-content", "32-part3-content",
            "40-part4", "41-part4-content",
            "50-part5", "51-part5-content", "52-part5-content",
            "60-part6", "61-part6-content", "62-part6-content",
            "70-part7", "71-part7-content",
            "80-part8", "81-part8-content",
            "A0-annexes", "A1-glossaire", "A2-biblio", "A3-index",
            "A4-credits", "99-colophon",
        ],
    },
    "v3": {
        "dir": "atelier-creer-arbre-parlant",
        "out": "atelier-creer-arbre-parlant.pdf",
        "title": "Créer un Arbre Parlant — Manuel d'atelier",
        "running": "Créer un Arbre Parlant",
        "description": (
            "Manuel d'atelier complet : capteurs, acquisition, électrophysiologie "
            "de terrain, chaîne logicielle open source, sonification, couche IA, "
            "protocoles reproductibles et déontologie arboricole."
        ),
        "keywords": (
            "arbre parlant, atelier, DIY, ESP32, Raspberry Pi, LoRaWAN, "
            "électrophysiologie, ADS1115, INA333, sonification, SuperCollider, "
            "Pure Data, MQTT, InfluxDB, Grafana, Piper TTS, Ollama, open source, "
            "arboriculture, protocole"
        ),
        "order": [
            "00-cover", "01-titlepage", "01b-epigraph", "02-notice",
            "03-toc", "04-introduction",
            "10-part1", "11-part1-content",
            "20-part2", "21-part2-content", "22-part2-content",
            "30-part3", "31-part3-content", "32-part3-content",
            "40-part4", "41-part4-content",
            "50-part5", "51-part5-content", "52-part5-content",
            "60-part6", "61-part6-content",
            "70-part7", "71-part7-content",
            "80-part8", "81-part8-content",
            "A0-annexes",
            "A5-planche1", "A6-planche2", "A7-planche3", "A8-planche4",
            "A9-planche5", "B1-bom", "B2-programmes", "B3-inventaire",
            "A1-glossaire", "A2-biblio", "A3-index",
            "A4-credits", "99-colophon",
        ],
    },
}


# =============================================================================
#  ASSEMBLAGE
# =============================================================================

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
         "VIII": 8, "IX": 9, "X": 10}


def number_figures(body):
    """Numérote les figures automatiquement, par partie.

    Les fragments écrivent `<span class="fig-n">Fig. ##.</span>` ; la
    numérotation « P.k » est calculée ici, à l'assemblage. Cela évite de
    renuméroter tout un volume à la main dès qu'une figure est insérée.
    """
    part_re = re.compile(r'<span class="rom">([IVX]+)</span>')
    fig_re = re.compile(r'(<span class="fig-n">Fig\.\s*)##(\.</span>)')
    marks = [(m.start(), "part", ROMAN.get(m.group(1), 0))
             for m in part_re.finditer(body)]
    marks += [(m.start(), "fig", m) for m in fig_re.finditer(body)]
    marks.sort(key=lambda x: x[0])

    part, k, out, last = 0, 0, [], 0
    n_fig = 0
    for pos, kind, val in marks:
        if kind == "part":
            part, k = val, 0
            continue
        k += 1
        n_fig += 1
        out.append(body[last:val.start()])
        label = f"{part}.{k}" if part else f"0.{k}"
        out.append(f"{val.group(1)}{label}{val.group(2)}")
        last = val.end()
    out.append(body[last:])
    print(f"    · {n_fig} figures numérotées")
    return "".join(out)


def read_fragment(parts_dir, name):
    path = os.path.join(parts_dir, name + ".html")
    if not os.path.exists(path):
        print(f"    · manquant : {name}.html  (ignoré)")
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
    """Signale les identifiants dupliqués (ils cassent les renvois de pages)."""
    ids = re.findall(r'\bid="([^"]+)"', body)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"    ! identifiants dupliqués ({len(dup)}) : {', '.join(dup[:12])}"
              f"{' …' if len(dup) > 12 else ''}")
    return dup


def check_links(body):
    """Signale les ancres internes pointant vers un id inexistant."""
    ids = set(re.findall(r'\bid="([^"]+)"', body))
    refs = set(re.findall(r'href="#([^"]+)"', body))
    manquants = sorted(refs - ids)
    if manquants:
        print(f"    ! ancres mortes ({len(manquants)}) : {', '.join(manquants[:12])}"
              f"{' …' if len(manquants) > 12 else ''}")
    return manquants


def check_assets(body):
    """Signale les images référencées mais absentes du disque."""
    srcs = set(re.findall(r'<img[^>]*\bsrc="([^"]+)"', body))
    manquants = sorted(s for s in srcs
                       if not s.startswith(("http:", "https:", "data:"))
                       and not os.path.exists(os.path.join(SRC, s)))
    if manquants:
        print(f"    ! images manquantes ({len(manquants)}) : "
              f"{', '.join(manquants[:8])}{' …' if len(manquants) > 8 else ''}")
    return manquants


def build_one(key):
    book = BOOKS[key]
    parts_dir = os.path.join(SRC, book["dir"])
    out_path = os.path.join(BUILD, book["out"])

    print(f"\n━━━ {key.upper()} · {book['title']}")
    print("  • Assemblage des fragments…")
    body = "\n".join(
        bp for bp in (read_fragment(parts_dir, n) for n in book["order"]) if bp.strip()
    )
    if not body.strip():
        print(f"  ! aucun fragment trouvé dans {parts_dir} — volume ignoré")
        return None

    print("  • Génération des sommaires (target-counter)…")
    items = collect_toc_items(body)
    print(f"    · {len(items)} entrées repérées")
    if "<!--TOC_HERE-->" in body:
        body = body.replace("<!--TOC_HERE-->", render_toc(items, with_sub=False))
    else:
        print("    ! marqueur <!--TOC_HERE--> introuvable — sommaire non inséré")
    if "<!--TOC_FULL-->" in body:
        body = body.replace("<!--TOC_FULL-->", render_toc(items, with_sub=True))

    print("  • Numérotation des figures…")
    body = number_figures(body)

    print("  • Vérifications…")
    check_ids(body)
    check_links(body)
    check_assets(body)

    # Le titre courant de l'en-tête vient de string-set sur <body>.
    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<title>{book['title']}</title>
<meta name="author" content="{AUTEUR}"/>
<meta name="description" content="{book['description']}"/>
<meta name="keywords" content="{book['keywords']}"/>
<meta name="dcterms.created" content="{DATE}"/>
<meta name="generator" content="WeasyPrint"/>
<link rel="stylesheet" href="fonts.css"/>
<link rel="stylesheet" href="arbre.css"/>
<style>body{{ string-set: booktitle "{book['running']}"; }}</style>
</head>
<body>
{body}
</body>
</html>"""

    assembled = os.path.join(SRC, f"_book-{key}.html")
    with open(assembled, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  • HTML assemblé : {os.path.relpath(assembled, ROOT)}  ({len(html)//1024} Ko)")

    print("  • Rendu PDF avec WeasyPrint…")
    from weasyprint import HTML
    os.makedirs(BUILD, exist_ok=True)
    HTML(filename=assembled, base_url=SRC).write_pdf(out_path, uncompressed_pdf=False)
    size = os.path.getsize(out_path) / (1024 * 1024)
    print(f"  ✓ {os.path.relpath(out_path, ROOT)}  ({size:.1f} Mo)")
    return out_path


def main():
    keys = [a for a in sys.argv[1:] if a in BOOKS] or list(BOOKS)
    inconnus = [a for a in sys.argv[1:] if a not in BOOKS]
    if inconnus:
        print(f"! volume(s) inconnu(s) : {', '.join(inconnus)} "
              f"(attendu : {', '.join(BOOKS)})")
    produced = [p for p in (build_one(k) for k in keys) if p]
    print(f"\n✓ {len(produced)} volume(s) produit(s) dans {os.path.relpath(BUILD, ROOT)}/")


if __name__ == "__main__":
    main()
