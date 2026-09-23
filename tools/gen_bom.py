#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/gen_bom.py
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

"""Generate the bill-of-materials fragments from the reference CSV files.

The bill of materials lives in `hardware/*.csv`, an open format that opens in
any spreadsheet. This program produces from it the tables
HTML of the document, with the totals computed — so that a price corrected in
the CSV propagates everywhere without being copied by hand.

Usage : python3 tools/gen_bom.py
"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The identity carried by every table produced: a bill of materials travels on
# its own, gets photocopied and pasted into a notebook; it must say where it
# came from.
AUTEUR = "Bretagne Namasté"
SITE = "https://bretagne-namaste.com"
CONTACT = "contact@bretagne-namaste.com"
PROJET = "PhytoSense One"
REVISION = "revision B — September 2026"
LICENCE = "CERN-OHL-P v2"
DATA = os.path.join(ROOT, "hardware")
OUT = os.path.join(ROOT, "pdf-src", "common")


def euro(x: float) -> str:
    #  English convention: a comma groups the thousands and a period marks the
    #  decimals. The document is in English, so the figures follow it.
    return f"{x:,.2f}"


def lire(nom: str):
    with open(os.path.join(DATA, nom), encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def entete(titre: str) -> str:
    """The provenance band placed above every table."""
    return (f'<div class="origine"><b>{PROJET}</b> — {titre}<br/>'
            f'<span>{AUTEUR} · <a href="{SITE}">{SITE.replace("https://", "")}</a>'
            f' · {CONTACT}</span><br/>'
            f'<span>{REVISION} · licence {LICENCE}</span></div>')


def table_bom(lignes):
    """The detailed bill of materials, grouped by function."""
    out = [entete("board bill of materials"),
           '<table class="bom tight"><thead><tr>'
           '<th>Ref.</th><th>Qty</th><th>Description</th>'
           '<th>Package<br/><span class="small">L × W × H (mm)</span></th>'
           '<th>Manufacturer · part</th><th>Unit €</th><th>Total €</th>'
           '</tr></thead><tbody>']
    groupe = None
    total = 0.0
    for r in lignes:
        if r["group"] != groupe:
            groupe = r["group"]
            out.append(f'<tr class="groupe"><td colspan="7">{esc(groupe)}</td></tr>')
        qte = int(r["qty"])
        pu = float(r["unit_eur"].replace(",", "."))
        sous = qte * pu
        total += sous
        out.append(
            f'<tr><td>{esc(r["ref"])}</td><td class="num">{qte}</td>'
            f'<td>{esc(r["description"])}'
            + (f'<br/><span class="small">{esc(r["note"])}</span>'
               if r.get("note") else "")
            + f'</td><td>{esc(r["package"])}'
            + (f'<br/><span class="small">{esc(r["dimensions"])}</span>'
               if r.get("dimensions") and r["dimensions"] != "—" else "")
            + f'</td><td>{esc(r["manufacturer"])}<br/><span class="small">'
            f'{esc(r["part"])}</span></td>'
            f'<td class="num">{euro(pu)}</td>'
            f'<td class="num">{euro(sous)}</td></tr>')
    out.append(f'<tr class="tot"><td colspan="6">Total for the components, '
               f'one unit</td><td class="num">{euro(total)}</td></tr>')
    out.append('<tr class="origine-pied"><td colspan="7">'
               f'{PROJET} · {AUTEUR} · {SITE.replace("https://", "")} · '
               f'{REVISION} · licence {LICENCE}</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out), total


def table_accessoires(lignes):
    """Accessories, sorted by how badly they are needed."""
    ordre = {"required": 0, "recommended": 1, "alternative": 2, "optional": 3}
    libelle = {"required": "Essential", "recommended": "Recommended",
               "alternative": "Variantes possibles", "optional": "Confort"}
    out = [entete("accessoires, outillage et consommables"),
           '<table class="bom tight"><thead><tr>'
           '<th>Description</th><th>Indicative part</th>'
           '<th>Where</th><th>≈ €</th></tr></thead><tbody>']
    totaux = {}
    for cle in sorted(ordre, key=lambda k: ordre[k]):
        groupe = [r for r in lignes if r["need"] == cle]
        if not groupe:
            continue
        out.append(f'<tr class="groupe"><td colspan="4">{libelle[cle]}</td></tr>')
        somme = 0.0
        for r in groupe:
            pu = float(r["unit_eur"].replace(",", "."))
            somme += pu
            out.append(
                f'<td>{esc(r["description"])}'
                + (f'<br/><span class="small">{esc(r["note"])}</span>'
                   if r.get("note") else "")
                + f'</td><td>{esc(r["part"])}</td>'
                f'<td>{esc(r["distributor"])}</td>'
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


def _ecrire_sbom() -> None:
    """Write _sbom-table.html from src/phytoscope/tools/sbom.py."""
    import importlib.util
    outil = os.path.join(ROOT, "src", "phytoscope", "tools", "sbom.py")
    if not os.path.exists(outil):
        print("  ! sbom.py introuvable : _sbom-table.html laisse en place")
        return
    spec = importlib.util.spec_from_file_location("_sbom_logiciel", outil)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        fragment = module.en_html(module.inventaire())
    except Exception as exc:                       # noqa: BLE001
        print(f"  ! SBOM logiciel indisponible : {exc}")
        return
    with open(os.path.join(OUT, "_sbom-table.html"), "w",
              encoding="utf-8") as f:
        f.write(fragment)


def main() -> int:
    bom = lire("bom.csv")
    acc = lire("accessories.csv")
    t_bom, total_bom = table_bom(bom)
    t_acc, totaux_acc = table_accessoires(acc)
    os.makedirs(OUT, exist_ok=True)

    with open(os.path.join(OUT, "_bom-table.html"), "w", encoding="utf-8") as f:
        f.write(t_bom)
    with open(os.path.join(OUT, "_accessoires-table.html"), "w",
              encoding="utf-8") as f:
        f.write(t_acc)

    #  The software bill of materials, from the software's own tool.
    #
    #  It used to be produced by hand — `python3 tools/sbom.py --html` piped
    #  into the fragment — which meant it could go stale in silence: nothing
    #  rebuilt it, and nothing noticed. Since the other three fragments are
    #  written here, this one is too. The tool is loaded by path rather than
    #  imported, because it lives in the software's tree and is not an
    #  installable module.
    _ecrire_sbom()

    necessaire = totaux_acc.get("required", 0.0)
    recommande = totaux_acc.get("recommended", 0.0)
    resume = {
        "composants": total_bom,
        "accessoires_necessaires": necessaire,
        "accessoires_recommandes": recommande,
        "minimum": total_bom + necessaire,
        "confortable": total_bom + necessaire + recommande,
        "n_composants": sum(int(r["qty"]) for r in bom),
        "n_references": len(bom),
    }
    with open(os.path.join(OUT, "_budget.html"), "w", encoding="utf-8") as f:
        f.write(
            entete("budgets") +
            '<table class="tight"><thead><tr><th>Poste</th><th>Montant</th>'
            '<th>What it covers</th></tr></thead><tbody>\n'
            f'<tr><td>Board components</td><td class="num">'
            f'{euro(total_bom)} €</td><td>{resume["n_references"]} part numbers, '
            f'{resume["n_composants"]} components, board included</td></tr>\n'
            f'<tr><td>Accessoires indispensables</td><td class="num">'
            f'{euro(necessaire)} €</td><td>cable, electrodes, gel, minimum '
            f'de soudure</td></tr>\n'
            f'<tr><td>Recommended accessories</td><td class="num">'
            f'{euro(recommande)} €</td><td>enclosure, battery, test '
            f'instruments</td></tr>\n'
            f'<tr class="tot"><td>Budget minimal</td><td class="num">'
            f'{euro(resume["minimum"])} €</td><td>a board that works</td></tr>\n'
            f'<tr class="tot"><td>Budget confortable</td><td class="num">'
            f'{euro(resume["confortable"])} €</td><td>a board you can defend '
            f'to a physicist</td></tr>\n'
            '</tbody></table>')
    print(f"✓ bill of materials: {resume['n_references']} part numbers, "
          f"{euro(total_bom)} €; accessories: {euro(necessaire)} € "
          f"(+ {euro(recommande)} € recommended)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
