#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/build_carte.py
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
Build du hors-série « La Carte PhytoSense » et de ses trois annexes détachables.

Quatre documents sont produits à partir des mêmes fragments :

    build/La-Carte-PhytoSense.pdf          l'ouvrage complet
    build/PhytoSense-schemas.pdf           les six feuilles de schéma seules
    build/PhytoSense-bom-accessoires.pdf   nomenclature et accessoires
    build/PhytoSense-pcb.pdf               circuit imprimé et fabrication

Les trois annexes sont faites pour être imprimées séparément et emportées
à l'établi ; l'ouvrage, lui, se lit.

Usage :
    python3 build_carte.py             les quatre documents
    python3 build_carte.py livre       l'ouvrage seul
    python3 build_carte.py schemas bom pcb
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pdf-src")
#  PARTS est réaffecté pour chaque document : depuis le rangement du
#  2026-09-18, chaque PDF a son propre dossier de fragments. COMMUN tient
#  ceux que plusieurs documents se partagent — les tableaux de nomenclature,
#  produits par tools/gen_bom.py et inclus par <!--INCLURE:…-->.
PARTS = os.path.join(SRC, "la-carte-phytosense")
COMMUN = os.path.join(SRC, "commun")
BUILD = os.path.join(ROOT, "build")

DATE = "2026-09-17"
AUTEUR = "Bretagne Namasté"
SITE = "https://bretagne-namaste.com"


# =============================================================================
#  DÉFINITION DES QUATRE DOCUMENTS
# =============================================================================
DOCUMENTS = {
    "livre": {
        "dir": "la-carte-phytosense",
        "out": "La-Carte-PhytoSense.pdf",
        "title": "La Carte PhytoSense — conditionnement analogique et interface USB",
        "running": "La Carte PhytoSense",
        "description": (
            "Conception complète d'une carte d'acquisition pour l'écoute des "
            "plantes : étage électrométrique, pont à détection synchrone, "
            "convertisseur 24 bits, isolement galvanique, liaison USB-C en "
            "classe audio, circuit imprimé quatre couches et logiciel "
            "d'exploitation multiplateforme."),
        "keywords": (
            "électrophysiologie végétale, carte d'acquisition, ADA4530-1, "
            "INA828, ADS131M04, RP2350, USB audio class 2, isolement "
            "galvanique, détection synchrone, circuit imprimé quatre couches, "
            "sonification, PhytoScope, Python, Qt"),
        "order": [
            "00-cover", "01-titlepage", "01b-epigraph", "02-notice",
            "03-toc", "04-introduction",
            "10-part1", "11-part1-content", "12-part1-content",
            "20-part2", "21-part2-content", "22-part2-content",
            "23-part2-content",
            "30-part3", "31-part3-content", "32-part3-content",
            "33-part3-content",
            "40-part4", "40a-part4-content", "41-part4-content",
            "41a-part4-content", "42-part4-content", "43-part4-content",
            "50-part5", "51-part5-content", "52-part5-content",
            "53-part5-content", "54-part5-content",
            "60-part6", "60a-part6-content", "61-part6-content",
            "62-part6-content",
            "A0-annexes", "A1-schemas", "A2-bom", "A3-pcb", "A4-protocole",
            "A5-glossaire", "A6-biblio", "A7-index", "99-colophon",
        ],
    },
    "schemas": {
        "dir": "phytosense-schemas",
        "out": "PhytoSense-schemas.pdf",
        "title": "PhytoSense One — dossier de schémas",
        "running": "PhytoSense One — schémas",
        "description": ("Les huit feuilles de schéma de la carte PhytoSense One, "
                        "protections, alimentation et signalisation comprises. "
                        "Bretagne Namasté — bretagne-namaste.com"),
        "keywords": "schéma électronique, PhytoSense, électrophysiologie",
        "order": ["S0-cover", "S1-notice", "S2-schemas"],
    },
    "bom": {
        "dir": "phytosense-bom-accessoires",
        "out": "PhytoSense-bom-accessoires.pdf",
        "title": "PhytoSense One — nomenclature et accessoires",
        "running": "PhytoSense One — nomenclature",
        "description": ("Nomenclature chiffrée de la carte PhytoSense One, "
                        "accessoires, outillage, nomenclature logicielle et "
                        "budgets. Bretagne Namasté — bretagne-namaste.com"),
        "keywords": "nomenclature, BOM, accessoires, budget, PhytoSense",
        "order": ["B0-cover", "B1-bom", "B2-accessoires", "B4-sbom",
                  "B3-budget"],
    },
    "pcb": {
        "dir": "phytosense-pcb",
        "out": "PhytoSense-pcb.pdf",
        "title": "PhytoSense One — circuit imprimé",
        "running": "PhytoSense One — circuit imprimé",
        "description": ("Routage quatre couches, implantation, empilage et "
                        "dossier de fabrication de la carte PhytoSense One."),
        "keywords": "circuit imprimé, routage, quatre couches, Gerber, PhytoSense",
        "order": ["P0-cover", "P1-pcb", "P2-fabrication"],
    },
}

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7,
         "VIII": 8, "IX": 9, "X": 10}


# =============================================================================
#  ASSEMBLAGE
# =============================================================================
def read_fragment(name):
    path = os.path.join(PARTS, name + ".html")
    if not os.path.exists(path):
        print(f"    · manquant : {name}.html  (ignoré)")
        return ""
    with open(path, encoding="utf-8") as f:
        return f.read()


def inject_includes(body):
    """Remplace <!--INCLURE:fichier--> par le contenu du fragment généré."""
    def remplacer(m):
        nom = m.group(1).strip()
        #  D'abord dans le dossier du document, puis dans le commun : un
        #  tableau de nomenclature sert au hors-série ET au fascicule.
        for base in (PARTS, COMMUN):
            chemin = os.path.join(base, nom)
            if os.path.exists(chemin):
                with open(chemin, encoding="utf-8") as f:
                    return f.read()
        print(f"    ! inclusion introuvable : {nom}")
        return f"<p class='small'>[{nom} manquant — lancez tools/gen_bom.py]</p>"
    return re.sub(r"<!--INCLURE:([^>]+?)-->", remplacer, body)


def number_figures(body):
    """Numérote les figures par partie : « Fig. ## » devient « Fig. 2.3 »."""
    part_re = re.compile(r'<span class="rom">([IVX]+)</span>')
    fig_re = re.compile(r'(<span class="fig-n">(?:Fig\.|PLANCHE|FIGURE)\s*)##')
    marks = [(m.start(), "part", ROMAN.get(m.group(1), 0))
             for m in part_re.finditer(body)]
    marks += [(m.start(), "fig", m) for m in fig_re.finditer(body)]
    marks.sort(key=lambda x: x[0])
    part, k, out, last, total = 0, 0, [], 0, 0
    for pos, kind, val in marks:
        if kind == "part":
            part, k = val, 0
            continue
        k += 1
        total += 1
        out.append(body[last:val.start()])
        out.append(f"{val.group(1)}{part}.{k}" if part else f"{val.group(1)}{k}")
        last = val.end()
    out.append(body[last:])
    if total:
        print(f"    · {total} figures numérotées")
    return "".join(out)


def strip_tags(s):
    s = re.sub(r"<sup.*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def collect_toc_items(body_html):
    items, seen = [], set()
    for pat in (re.compile(r'<(h1|h2|h3)[^>]*\bdata-toc="(part|chapter|sub)"'
                           r'[^>]*\bid="([^"]+)"[^>]*>(.*?)</\1>', re.S),
                re.compile(r'<(h1|h2|h3)[^>]*\bid="([^"]+)"[^>]*'
                           r'\bdata-toc="(part|chapter|sub)"[^>]*>(.*?)</\1>', re.S)):
        for m in pat.finditer(body_html):
            if pat.pattern.startswith(r'<(h1|h2|h3)[^>]*\bdata-toc'):
                niveau, hid, texte = m.group(2), m.group(3), m.group(4)
            else:
                niveau, hid, texte = m.group(3), m.group(2), m.group(4)
            if hid in seen:
                continue
            seen.add(hid)
            items.append((m.start(), niveau, hid, strip_tags(texte)))
    items.sort(key=lambda x: x[0])
    return items


def render_toc(items, with_sub=True):
    out = []
    for _, lvl, hid, text in items:
        if lvl == "part":
            out.append(f'<li class="toc-part"><a class="tl-part" href="#{hid}">'
                       f'<span class="t">{text}</span>'
                       f'<span class="leader"></span></a></li>')
        elif lvl == "chapter":
            out.append(f'<li><a class="tl" href="#{hid}">'
                       f'<span class="t">{text}</span>'
                       f'<span class="leader"></span></a></li>')
        elif with_sub:
            out.append(f'<li><a class="tl sub" href="#{hid}">'
                       f'<span class="t">{text}</span>'
                       f'<span class="leader"></span></a></li>')
    return "<ul>\n" + "\n".join(out) + "\n</ul>"


def check(body):
    ids = re.findall(r'\bid="([^"]+)"', body)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"    ! identifiants dupliqués : {', '.join(dup[:10])}")
    refs = set(re.findall(r'href="#([^"]+)"', body))
    manquants = sorted(refs - set(ids))
    if manquants:
        print(f"    ! ancres mortes ({len(manquants)}) : "
              f"{', '.join(manquants[:10])}")
    images = set(re.findall(r'<img[^>]+src="([^"]+)"', body))
    absentes = [i for i in images
                if not os.path.exists(os.path.join(SRC, i))]
    if absentes:
        print(f"    ! images absentes ({len(absentes)}) : "
              f"{', '.join(absentes[:6])}")


def build(key, spec):
    global PARTS
    print(f"\n▸ {spec['out']}")
    #  Chaque document lit ses fragments chez lui. build_sdk.py, qui emprunte
    #  ce moule, impose son dossier en écrivant moule.PARTS : on ne l'écrase
    #  donc que si le document en déclare un.
    if spec.get("dir"):
        PARTS = os.path.join(SRC, spec["dir"])
    body = "\n".join(read_fragment(n) for n in spec["order"])
    if not body.strip():
        print("    ! aucun fragment : document ignoré")
        return False
    body = inject_includes(body)
    body = number_figures(body)

    items = collect_toc_items(body)
    print(f"    · {len(items)} entrées de sommaire")
    if "<!--TOC_HERE-->" in body:
        body = body.replace("<!--TOC_HERE-->", render_toc(items, with_sub=False))
    if "<!--TOC_FULL-->" in body:
        body = body.replace("<!--TOC_FULL-->", render_toc(items, with_sub=True))
    check(body)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<title>{spec['title']}</title>
<meta name="author" content="{AUTEUR}"/>
<meta name="publisher" content="{AUTEUR}"/>
<meta name="copyright" content="© 2026 {AUTEUR} — {SITE}"/>
<meta name="contact" content="contact@bretagne-namaste.com"/>
<meta name="source" content="{SITE}"/>
<meta name="description" content="{spec['description']}"/>
<meta name="keywords" content="{spec['keywords']}"/>
<meta name="dcterms.created" content="{DATE}"/>
<meta name="generator" content="WeasyPrint"/>
<link rel="stylesheet" href="fonts.css"/>
<link rel="stylesheet" href="book.css"/>
<link rel="stylesheet" href="carte.css"/>
<style>body{{ string-set: booktitle "{spec['running']}"; }}</style>
</head>
<body>
{body}
</body>
</html>"""

    assemble = os.path.join(SRC, f"_carte-{key}.html")
    with open(assemble, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"    · HTML assemblé ({len(html) // 1024} Ko)")

    from weasyprint import HTML
    os.makedirs(BUILD, exist_ok=True)
    sortie = os.path.join(BUILD, spec["out"])
    HTML(filename=assemble, base_url=SRC).write_pdf(sortie)
    taille = os.path.getsize(sortie) / (1024 * 1024)
    pages = _compter_les_pages(sortie)
    pages = f", {pages} pages" if pages else ""
    print(f"    ✓ {sortie}  ({taille:.1f} Mo{pages})")
    return True


def _compter_les_pages(chemin: str) -> str:
    """Le nombre de pages du PDF produit, sans rien exiger du système.

    On appelait `pdfinfo`, qui vient de poppler-utils : absent par défaut des
    trois systèmes, et rarement installé sous Windows. Le compte disparaissait
    donc silencieusement, alors que c'est justement le chiffre que la
    contrainte `C-64` demande de vérifier après chaque reconstruction.

    Le PDF le dit pourtant lui-même : il suffit de compter les objets
    `/Type /Page`. On lit donc le fichier, et l'on ne retombe sur `pdfinfo`
    que si ce décompte échoue — pour un document à flux compressés, par
    exemple.
    """
    try:
        with open(chemin, "rb") as f:
            brut = f.read()
        #  `/Count n` dans le nœud racine de l'arbre des pages est la réponse
        #  autorisée ; on prend la plus grande valeur, qui est la racine.
        comptes = [int(m) for m in re.findall(rb"/Type\s*/Pages[^>]*?/Count\s+(\d+)", brut)]
        comptes += [int(m) for m in re.findall(rb"/Count\s+(\d+)[^>]*?/Type\s*/Pages", brut)]
        if comptes:
            return str(max(comptes))
        #  À défaut, on dénombre les pages une à une.
        n = len(re.findall(rb"/Type\s*/Page[^s]", brut))
        if n:
            return str(n)
    except OSError:
        pass
    try:
        import shutil
        import subprocess
        if shutil.which("pdfinfo"):
            info = subprocess.run(["pdfinfo", chemin], capture_output=True,
                                  text=True, timeout=20).stdout
            m = re.search(r"Pages:\s+(\d+)", info)
            if m:
                return m.group(1)
    except Exception:                                  # noqa: BLE001
        pass
    return ""


def main(argv):
    cibles = [a for a in argv[1:] if not a.startswith("-")] or list(DOCUMENTS)
    inconnues = [c for c in cibles if c not in DOCUMENTS]
    if inconnues:
        print(f"Document inconnu : {', '.join(inconnues)}")
        print(f"Disponibles : {', '.join(DOCUMENTS)}")
        return 2
    print("• Construction des documents « La Carte PhytoSense »")
    ok = 0
    for cle in cibles:
        if build(cle, DOCUMENTS[cle]):
            ok += 1
    print(f"\n✓ {ok} document(s) produit(s) dans {BUILD}/")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
