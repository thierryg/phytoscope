#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/build_annexe.py
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
Construction de l'ANNEXE TECHNIQUE — « L'Arbre qui Parle ».

Volume autonome : schémas électroniques commentés, nomenclatures (BOM) et
listings de programmes. Il réutilise la charte pdf-src/book.css mais possède son
propre assemblage, afin de ne pas interférer avec build.py ni avec les
fragments des volumes v1/v2/v3.

Les listings de code sont EXTRAITS À LA CONSTRUCTION depuis les archives de
sources/code/ : le PDF ne peut donc pas diverger du code réellement téléchargé.

Usage : python3 tools/build-annexe.py
"""
import html
import io
import os
import re
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "pdf-src")
PARTS = os.path.join(SRC, "arbre-parlant-annexe")
CODE = os.path.join(ROOT, "sources", "code")
BUILD = os.path.join(ROOT, "build")

DATE = "2026-09-17"
AUTEUR = "Ateliers BN"
TITRE = "L'Arbre qui Parle — Annexe technique"
RUNNING = "Annexe technique"
OUT = "arbre-parlant-annexe-schemas-bom-programmes.pdf"

ORDER = [
    "00-cover", "01-titlepage", "02-notice", "03-toc",
    "10-planche1", "11-planche2", "12-planche3", "13-planche4", "14-planche5",
    "20-bom-globale",
    "30-programmes",
    "40-inventaire",
    "99-colophon",
]


# =============================================================================
#  EXTRACTION DE CODE DEPUIS LES ARCHIVES
# =============================================================================
def lire_membre(archive, motif):
    """Renvoie le contenu texte du premier membre dont le nom matche `motif`."""
    chemin = os.path.join(CODE, archive)
    if not os.path.exists(chemin):
        raise FileNotFoundError(f"archive absente : {chemin}")
    with zipfile.ZipFile(chemin) as z:
        noms = [n for n in z.namelist() if re.search(motif, n)]
        if not noms:
            raise KeyError(f"{archive} : aucun membre ne matche {motif!r}")
        with z.open(sorted(noms, key=len)[0]) as f:
            return io.TextIOWrapper(f, encoding="utf-8", errors="replace").read()


def extrait(archive, motif, debut=None, fin=None, entete=None):
    """Extrait un bloc de lignes, délimité par des expressions régulières.

    debut/fin sont des regex cherchées dans le texte ; à défaut, tout le
    fichier est pris. Renvoie du HTML prêt à insérer dans un bloc .code.
    """
    txt = lire_membre(archive, motif)
    lignes = txt.splitlines()
    i0 = 0
    if debut:
        for i, l in enumerate(lignes):
            if re.search(debut, l):
                i0 = i
                break
        else:
            raise KeyError(f"{archive}:{motif} — début {debut!r} introuvable")
    i1 = len(lignes)
    if fin:
        for i in range(i0 + 1, len(lignes)):
            if re.search(fin, lignes[i]):
                i1 = i
                break
    bloc = "\n".join(lignes[i0:i1]).rstrip()
    src = entete or f"{archive} › {motif}"
    return bloc, src


def bloc_code(titre, corps, source=None):
    s = (f'<div class="code-h">{html.escape(titre)}</div>' if titre else "")
    src = (f'<p class="small" style="margin:.4em 0 0">Source : {source}</p>'
           if source else "")
    return (f'<div class="code listing">{s}<pre>{html.escape(corps)}</pre></div>{src}')


# =============================================================================
#  ASSEMBLAGE
# =============================================================================
def lire_fragment(nom):
    p = os.path.join(PARTS, nom + ".html")
    if not os.path.exists(p):
        print(f"    · manquant : {nom}.html (ignoré)")
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()


def strip_tags(s):
    s = re.sub(r"<sup.*?</sup>", "", s, flags=re.S)
    s = re.sub(r"<[^>]+>", "", s)
    return re.sub(r"\s+", " ", s).strip()


def collect_toc(body):
    items, seen = [], set()
    pat = re.compile(
        r'<(h1|h2|h3)[^>]*\bdata-toc="(part|chapter|sub)"[^>]*\bid="([^"]+)"[^>]*>(.*?)</\1>',
        re.S)
    pat2 = re.compile(
        r'<(h1|h2|h3)[^>]*\bid="([^"]+)"[^>]*\bdata-toc="(part|chapter|sub)"[^>]*>(.*?)</\1>',
        re.S)
    for m in pat.finditer(body):
        items.append((m.start(), m.group(2), m.group(3), strip_tags(m.group(4))))
        seen.add(m.group(3))
    for m in pat2.finditer(body):
        if m.group(2) not in seen:
            items.append((m.start(), m.group(3), m.group(2), strip_tags(m.group(4))))
    items.sort(key=lambda x: x[0])
    return items


def render_toc(items):
    out = []
    for _, lvl, hid, text in items:
        cls = {"part": "toc-part", "chapter": "", "sub": ""}[lvl]
        a = "tl-part" if lvl == "part" else ("tl sub" if lvl == "sub" else "tl")
        li = f' class="{cls}"' if cls else ""
        out.append(f'<li{li}><a class="{a}" href="#{hid}">'
                   f'<span class="t">{text}</span><span class="leader"></span></a></li>')
    return "<ul>\n" + "\n".join(out) + "\n</ul>"


def verifier(body):
    ids = re.findall(r'\bid="([^"]+)"', body)
    dup = sorted({i for i in ids if ids.count(i) > 1})
    if dup:
        print(f"    ! identifiants dupliqués : {', '.join(dup[:10])}")
    refs = set(re.findall(r'href="#([^"]+)"', body))
    morts = sorted(refs - set(ids))
    if morts:
        print(f"    ! ancres mortes : {', '.join(morts[:10])}")
    srcs = set(re.findall(r'<img[^>]*\bsrc="([^"]+)"', body))
    abs_ = sorted(s for s in srcs
                  if not s.startswith(("http:", "https:", "data:"))
                  and not os.path.exists(os.path.join(SRC, s)))
    if abs_:
        print(f"    ! images manquantes : {', '.join(abs_[:10])}")
    return not (dup or morts or abs_)


def main():
    print(f"━━━ {TITRE}")
    print("  • Assemblage des fragments…")
    body = "\n".join(b for b in (lire_fragment(n) for n in ORDER) if b.strip())
    if not body.strip():
        print(f"  ! aucun fragment dans {PARTS}")
        return 1

    print("  • Sommaire…")
    items = collect_toc(body)
    print(f"    · {len(items)} entrées")
    if "<!--TOC_HERE-->" in body:
        body = body.replace("<!--TOC_HERE-->", render_toc(items))
    else:
        print("    ! marqueur <!--TOC_HERE--> absent")

    print("  • Vérifications…")
    verifier(body)

    doc = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8"/>
<title>{TITRE}</title>
<meta name="author" content="{AUTEUR}"/>
<meta name="description" content="Schémas électroniques commentés, nomenclatures et listings de programmes pour la construction d'un arbre instrumenté."/>
<meta name="dcterms.created" content="{DATE}"/>
<link rel="stylesheet" href="fonts.css"/>
<link rel="stylesheet" href="book.css"/>
<style>
body{{ string-set: booktitle "{RUNNING}"; }}
/* Les planches sont larges : chacune occupe une page paysage entière, sinon
   les annotations tombent sous le seuil de lisibilité à l'impression. */
@page planche{{
  size: 240mm 170mm;
  margin: 13mm 14mm 12mm 14mm;
  @top-left{{ content:none; }} @top-right{{ content:none; }}
  @bottom-left{{ content:none; }} @bottom-right{{ content:none; }}
  @bottom-center{{ content: counter(page);
    font-family:"Cormorant Garamond", serif; font-size:10pt;
    color: var(--nuit); padding-bottom:4mm; }}
}}
section.planche-page{{ page: planche; break-before:page; }}
section.planche-page + *{{ break-before:page; }}
figure.planche{{ margin:0; }}
figure.planche{{ text-align:center; }}
/* la hauteur est la contrainte : 145 mm utiles moins la légende, sinon la
   figure déborde et WeasyPrint ajoute une page paysage vide */
figure.planche img{{ max-width:100%; max-height:130mm; width:auto; height:auto;
  border:1px solid var(--trait); border-radius:2mm; }}
figure.planche figcaption{{ margin-top:3mm; font-size:9pt; text-align:left; }}
table.bom{{ font-size:7.8pt; }}
table.bom th{{ font-size:6.6pt; padding:1.6mm 1.6mm; }}
table.bom td{{ padding:1.5mm 1.6mm; }}
table.bom td:nth-child(2){{ font-size:7.6pt; }}
.tot td{{ background:var(--or-pl) !important; font-weight:700; }}
/* book.css met break-inside:avoid sur TOUS les tableaux : pour les longues
   nomenclatures c'est intenable (une table de 21 lignes laisse une page vide).
   On autorise la coupure, ligne par ligne, avec répétition de l'en-tête. */
table.tight-xs, table.tight, table.bom{{ break-inside:auto; }}
table.tight-xs thead, table.tight thead, table.bom thead{{
  display:table-header-group; }}
table.tight-xs tr, table.tight tr, table.bom tr{{ break-inside:avoid; }}
h4{{ break-after:avoid; }}
</style>
</head>
<body>
{body}
</body>
</html>"""

    assemble = os.path.join(SRC, "_annexe-tech.html")
    with open(assemble, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"  • HTML : {os.path.relpath(assemble, ROOT)} ({len(doc)//1024} Ko)")

    print("  • Rendu WeasyPrint…")
    from weasyprint import HTML
    os.makedirs(BUILD, exist_ok=True)
    out = os.path.join(BUILD, OUT)
    HTML(filename=assemble, base_url=SRC).write_pdf(out)
    print(f"  ✓ {os.path.relpath(out, ROOT)} ({os.path.getsize(out)/1048576:.1f} Mo)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
