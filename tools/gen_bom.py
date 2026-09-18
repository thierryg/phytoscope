#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/gen_bom.py
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

"""Génère les fragments de nomenclature depuis les fichiers CSV de référence.

La nomenclature vit dans `hardware/*.csv`, format
ouvert et modifiable dans un tableur. Ce programme en produit les tableaux
HTML du document, avec les totaux calculés — de sorte qu'un prix corrigé
dans le CSV se répercute partout sans recopie.

Usage : python3 tools/gen_bom.py
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Identité portée par chaque tableau produit : une nomenclature circule seule,
# se photocopie et se colle dans un carnet ; elle doit dire d'où elle vient.
AUTEUR = "Bretagne Namasté"
SITE = "https://bretagne-namaste.com"
CONTACT = "contact@bretagne-namaste.com"
PROJET = "PhytoSense One"
REVISION = "révision B — septembre 2026"
LICENCE = "CERN-OHL-P v2"
DATA = os.path.join(ROOT, "hardware")
OUT = os.path.join(ROOT, "pdf-src", "commun")


def euro(x: float) -> str:
    return f"{x:,.2f}".replace(",", " ").replace(".", ",")


def lire(nom: str):
    with open(os.path.join(DATA, nom), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def entete(titre: str) -> str:
    """Bandeau d'origine, placé au-dessus de chaque tableau."""
    return (f'<div class="origine"><b>{PROJET}</b> — {titre}<br/>'
            f'<span>{AUTEUR} · <a href="{SITE}">{SITE.replace("https://", "")}</a>'
            f' · {CONTACT}</span><br/>'
            f'<span>{REVISION} · licence {LICENCE}</span></div>')


def table_bom(lignes):
    """Nomenclature détaillée, groupée par fonction."""
    out = [entete("nomenclature de la carte"),
           '<table class="bom tight"><thead><tr>'
           '<th>Repère</th><th>Qté</th><th>Désignation</th>'
           '<th>Boîtier<br/><span class="small">L × l × h (mm)</span></th>'
           '<th>Fabricant · référence</th><th>PU €</th><th>Total €</th>'
           '</tr></thead><tbody>']
    groupe = None
    total = 0.0
    for r in lignes:
        if r["groupe"] != groupe:
            groupe = r["groupe"]
            out.append(f'<tr class="groupe"><td colspan="7">{esc(groupe)}</td></tr>')
        qte = int(r["qte"])
        pu = float(r["pu_eur"].replace(",", "."))
        sous = qte * pu
        total += sous
        out.append(
            f'<tr><td>{esc(r["ref"])}</td><td class="num">{qte}</td>'
            f'<td>{esc(r["designation"])}'
            + (f'<br/><span class="small">{esc(r["note"])}</span>'
               if r.get("note") else "")
            + f'</td><td>{esc(r["boitier"])}'
            + (f'<br/><span class="small">{esc(r["dimensions"])}</span>'
               if r.get("dimensions") and r["dimensions"] != "—" else "")
            + f'</td><td>{esc(r["fabricant"])}<br/><span class="small">'
            f'{esc(r["reference"])}</span></td>'
            f'<td class="num">{euro(pu)}</td>'
            f'<td class="num">{euro(sous)}</td></tr>')
    out.append(f'<tr class="tot"><td colspan="6">Total des composants, '
               f'un exemplaire</td><td class="num">{euro(total)}</td></tr>')
    out.append('<tr class="origine-pied"><td colspan="7">'
               f'{PROJET} · {AUTEUR} · {SITE.replace("https://", "")} · '
               f'{REVISION} · licence {LICENCE}</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out), total


def table_accessoires(lignes):
    """Accessoires, classés par nécessité."""
    ordre = {"nécessaire": 0, "recommandé": 1, "alternative": 2, "facultatif": 3}
    libelle = {"nécessaire": "Indispensables", "recommandé": "Recommandés",
               "alternative": "Variantes possibles", "facultatif": "Confort"}
    out = [entete("accessoires, outillage et consommables"),
           '<table class="bom tight"><thead><tr>'
           '<th>Désignation</th><th>Référence indicative</th>'
           '<th>Où</th><th>≈ €</th></tr></thead><tbody>']
    totaux = {}
    for cle in sorted(ordre, key=lambda k: ordre[k]):
        groupe = [r for r in lignes if r["necessaire"] == cle]
        if not groupe:
            continue
        out.append(f'<tr class="groupe"><td colspan="4">{libelle[cle]}</td></tr>')
        somme = 0.0
        for r in groupe:
            pu = float(r["pu_eur"].replace(",", "."))
            somme += pu
            out.append(
                f'<td>{esc(r["designation"])}'
                + (f'<br/><span class="small">{esc(r["note"])}</span>'
                   if r.get("note") else "")
                + f'</td><td>{esc(r["reference"])}</td>'
                f'<td>{esc(r["distributeur"])}</td>'
                f'<td class="num">{euro(pu)}</td></tr>')
            out[-1] = "<tr>" + out[-1]
        totaux[cle] = somme
        out.append(f'<tr class="tot"><td colspan="3">Sous-total — '
                   f'{libelle[cle].lower()}</td>'
                   f'<td class="num">{euro(somme)}</td></tr>')
    out.append('<tr class="origine-pied"><td colspan="4">'
               f'{PROJET} · {AUTEUR} · {SITE.replace("https://", "")} · '
               f'{REVISION}</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out), totaux


def main() -> int:
    bom = lire("bom.csv")
    acc = lire("accessoires.csv")
    t_bom, total_bom = table_bom(bom)
    t_acc, totaux_acc = table_accessoires(acc)
    os.makedirs(OUT, exist_ok=True)

    with open(os.path.join(OUT, "_bom-table.html"), "w", encoding="utf-8") as f:
        f.write(t_bom)
    with open(os.path.join(OUT, "_accessoires-table.html"), "w",
              encoding="utf-8") as f:
        f.write(t_acc)

    necessaire = totaux_acc.get("nécessaire", 0.0)
    recommande = totaux_acc.get("recommandé", 0.0)
    resume = {
        "composants": total_bom,
        "accessoires_necessaires": necessaire,
        "accessoires_recommandes": recommande,
        "minimum": total_bom + necessaire,
        "confortable": total_bom + necessaire + recommande,
        "n_composants": sum(int(r["qte"]) for r in bom),
        "n_references": len(bom),
    }
    with open(os.path.join(OUT, "_budget.html"), "w", encoding="utf-8") as f:
        f.write(
            entete("budgets") +
            '<table class="tight"><thead><tr><th>Poste</th><th>Montant</th>'
            '<th>Ce que cela recouvre</th></tr></thead><tbody>\n'
            f'<tr><td>Composants de la carte</td><td class="num">'
            f'{euro(total_bom)} €</td><td>{resume["n_references"]} références, '
            f'{resume["n_composants"]} composants, circuit imprimé compris</td></tr>\n'
            f'<tr><td>Accessoires indispensables</td><td class="num">'
            f'{euro(necessaire)} €</td><td>câble, électrodes, gel, outillage '
            f'de soudure</td></tr>\n'
            f'<tr><td>Accessoires recommandés</td><td class="num">'
            f'{euro(recommande)} €</td><td>boîtier, batterie, instruments de '
            f'contrôle</td></tr>\n'
            f'<tr class="tot"><td>Budget minimal</td><td class="num">'
            f'{euro(resume["minimum"])} €</td><td>une carte qui fonctionne</td></tr>\n'
            f'<tr class="tot"><td>Budget confortable</td><td class="num">'
            f'{euro(resume["confortable"])} €</td><td>une carte qu\'on peut '
            f'défendre devant un physicien</td></tr>\n'
            '</tbody></table>')
    print(f"✓ nomenclature : {resume['n_references']} références, "
          f"{euro(total_bom)} € ; accessoires : {euro(necessaire)} € "
          f"(+ {euro(recommande)} € recommandés)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
