#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/gen_credits.py
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
Génère l'annexe « Crédits iconographiques » de chaque volume.

Le tableau ne liste QUE les photographies réellement employées dans le volume :
il est construit en scannant les fragments à la recherche des images, puis en
retrouvant chaque ligne de crédit dans CREDITS.md. Une image sans crédit
retrouvé fait échouer la génération — un livre ne doit pas publier une
photographie dont l'attribution manque.

Usage : python3 tools/gen_credits.py [v1 v2 v3]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "pdf-src", "the-music-of-plants")
CREDITS = os.path.join(ROOT, "pdf-src", "assets", "img", "photos", "CREDITS.md")
DIRS = {"v1": "v1-dublin", "v2": "v2-biocommunication", "v3": "v3-atelier"}


def load_credits():
    """Lit CREDITS.md → {base_du_fichier: (titre, auteur, licence, url)}."""
    table = {}
    for line in open(CREDITS, encoding="utf-8"):
        m = re.match(r"\|\s*`([^`]+)`\s*\|(.*)", line)
        if not m:
            continue
        cells = [c.strip() for c in line.split("|")]
        base = os.path.splitext(m.group(1))[0]
        titre, auteur, lic = cells[2], cells[3], cells[4]
        url = ""
        mu = re.search(r"\((https?://[^)]+)\)", cells[5])
        if mu:
            url = mu.group(1)
        table[base] = (titre, auteur, lic, url)
    return table


def used_photos(vol):
    d = os.path.join(PARTS, DIRS[vol])
    found = []
    if not os.path.isdir(d):
        return found
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".html"):
            continue
        txt = open(os.path.join(d, fn), encoding="utf-8").read()
        for m in re.finditer(r'src="assets/img/p/([^".]+)\.jpg"', txt):
            if m.group(1) not in found:
                found.append(m.group(1))
    return sorted(found)


def render(vol, table):
    photos = used_photos(vol)
    if not photos:
        return None, 0
    missing = [p for p in photos if p not in table]
    if missing:
        print(f"  ! crédits manquants ({len(missing)}) — annexe NON écrite : "
              f"{', '.join(missing[:6])}")
        return None, 0

    rows = []
    for p in photos:
        titre, auteur, lic, url = table[p]
        lien = f'<br/><span class="small">{url}</span>' if url else ""
        rows.append(f"      <tr><td>{p}</td><td>{titre}{lien}</td>"
                    f"<td>{auteur}</td><td>{lic}</td></tr>")

    html = f'''<section class="chapter">
  <h2 id="credits" data-toc="chapter">Crédits iconographiques</h2>
  <p class="chapo">Les {len(photos)} photographies de ce volume proviennent toutes de Wikimedia Commons et sont sous licence libre : domaine public, CC0, CC BY ou CC BY-SA. Les schémas, diagrammes et illustrations vectorielles sont des créations originales réalisées pour cette série.</p>

  <div class="callout info">
    <div class="callout-title">Obligations d'attribution</div>
    <p>Pour toute réutilisation d'une de ces photographies, mentionner au minimum le titre, l'auteur et la licence, tels qu'ils figurent ci-dessous. Les images sous licence <strong>CC BY-SA</strong> imposent en outre le partage de l'œuvre dérivée dans les mêmes conditions, lorsque celle-ci constitue une adaptation de l'image. Les images en domaine public ou CC0 n'imposent pas d'attribution&nbsp;; la mention est conservée ici par honnêteté intellectuelle.</p>
  </div>

  <table class="credits-table">
    <thead><tr><th>Fichier</th><th>Titre</th><th>Auteur</th><th>Licence</th></tr></thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
    <caption>Toutes les pages Commons correspondantes ont été consultées le 17 septembre 2026.</caption>
  </table>

  <h3 id="credits-svg" data-toc="sub">Illustrations vectorielles</h3>
  <p class="noindent">L'ensemble des schémas, diagrammes, frises, plans et fonds de partie de cette série est généré de façon déterministe par un programme écrit pour l'occasion. Ils sont donc reproductibles à l'identique et librement réutilisables, comme le texte de l'ouvrage.</p>
</section>
'''
    return html, len(photos)


def main():
    table = load_credits()
    print(f"• Crédits ({len(table)} photographies référencées)…")
    for vol in ([a for a in sys.argv[1:] if a in DIRS] or list(DIRS)):
        html, n = render(vol, table)
        if html is None:
            continue
        out = os.path.join(PARTS, DIRS[vol], "A4-credits.html")
        with open(out, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  · {vol} : {n} photographies → {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
