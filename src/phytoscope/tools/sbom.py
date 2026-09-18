#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/sbom.py
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

"""Nomenclature logicielle (SBOM) de PhytoScope.

Une carte a sa nomenclature de composants ; un logiciel a la sienne. Elle
répond aux mêmes questions : qu'est-ce qui entre dans le produit, d'où cela
vient, sous quelle licence, et dans quelle version exacte.

Deux formats sont produits :

* **CycloneDX 1.5**, en JSON — c'est le format que lisent les outils d'analyse
  de vulnérabilités et de conformité ;
* **texte**, lisible par un être humain, destiné au fascicule imprimé.

Aucune dépendance : l'inventaire est établi par introspection des modules
réellement importables, complété par la table de référence ci-dessous. Cela
signifie que le SBOM décrit **ce qui est installé sur cette machine**, et non
ce que le fichier des dépendances prétend — ce qui est précisément l'intérêt
de l'exercice.

Usage :
    python3 tools/sbom.py            texte sur la sortie standard
    python3 tools/sbom.py --json     CycloneDX
    python3 tools/sbom.py --html     fragment pour le fascicule
"""
from __future__ import annotations

import argparse
import datetime
import importlib
import json
import os
import platform
import sys
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from phytoscope import version as V                   # noqa: E402

# (module importable, nom du paquet, licence, éditeur, rôle, obligatoire)
COMPOSANTS = [
    ("numpy", "numpy", "BSD-3-Clause", "NumPy Developers",
     "calcul numérique et traitement du signal", True),
    ("PySide6", "PySide6", "LGPL-3.0-only", "The Qt Company",
     "interface graphique Qt 6", True),
    ("shiboken6", "shiboken6", "LGPL-3.0-only", "The Qt Company",
     "liaison C++/Python de Qt", True),
    ("pyqtgraph", "pyqtgraph", "MIT", "Luke Campagnola et contributeurs",
     "tracés scientifiques temps réel", False),
    ("sounddevice", "sounddevice", "MIT", "Matthias Geier",
     "entrée et sortie audio (liaison PortAudio)", False),
    ("serial", "pyserial", "BSD-3-Clause", "Chris Liechti",
     "port série : contrôle de la carte", False),
    ("rtmidi", "python-rtmidi", "MIT", "Christopher Arndt",
     "sortie MIDI (liaison RtMidi)", False),
    ("usb.core", "pyusb", "BSD-3-Clause", "PyUSB Developers",
     "descripteurs USB détaillés", False),
    ("cffi", "cffi", "MIT", "Armin Rigo, Maciej Fijalkowski",
     "interface C, requise par sounddevice", False),
]

# Bibliothèques natives atteintes à travers ces paquets : elles font partie du
# produit livré à l'utilisateur, et doivent donc figurer à l'inventaire.
NATIVES = [
    ("PortAudio", "MIT", "portaudio.com", "couche audio multiplateforme"),
    ("RtMidi", "MIT modifiée", "rtmidi (McGill)", "couche MIDI multiplateforme"),
    ("Qt", "LGPL-3.0", "The Qt Company", "boîte à outils graphique"),
    ("libasound (ALSA)", "LGPL-2.1", "alsa-project.org",
     "couche audio du noyau Linux — système, non redistribuée"),
]


def inventaire():
    """Relève la version réellement installée de chaque composant."""
    lignes = []
    for module, paquet, licence, editeur, role, obligatoire in COMPOSANTS:
        try:
            m = importlib.import_module(module)
            version = str(getattr(m, "__version__", "") or "présent")
            etat = "installé"
        except Exception:
            version, etat = "—", "absent"
        lignes.append({
            "module": module, "paquet": paquet, "version": version,
            "licence": licence, "editeur": editeur, "role": role,
            "obligatoire": obligatoire, "etat": etat,
        })
    return lignes


# ---------------------------------------------------------------------------
#  Rendus
# ---------------------------------------------------------------------------
def en_texte(lignes) -> str:
    out = [
        "NOMENCLATURE LOGICIELLE — SBOM",
        "=" * 74,
        f"Produit    : {V.APP_NAME} {V.TITRE_VERSION}",
        f"Auteur     : {V.AUTHOR}",
        f"Site       : {V.WEBSITE}",
        f"Contact    : {V.CONTACT}",
        f"Licence    : {V.LICENSE}",
        f"Établie le : {datetime.date.today().isoformat()}",
        f"Machine    : Python {platform.python_version()} — {platform.system()}",
        "",
        "COMPOSANTS TIERS",
        "-" * 74,
        f"  {'PAQUET':<16} {'VERSION':<12} {'LICENCE':<16} RÔLE",
        "  " + "-" * 70,
    ]
    for d in lignes:
        marque = "!" if d["obligatoire"] and d["etat"] == "absent" else " "
        out.append(f" {marque}{d['paquet']:<16} {d['version']:<12} "
                   f"{d['licence']:<16} {d['role']}")
    out += ["", "BIBLIOTHÈQUES NATIVES ATTEINTES", "-" * 74]
    for nom, licence, editeur, role in NATIVES:
        out.append(f"  {nom:<18} {licence:<16} {role}")
    out += [
        "", "PORTÉE", "-" * 74,
        "  PhytoScope n'incorpore aucun code tiers : il s'appuie sur ces",
        "  bibliothèques à l'exécution. Distribué sous forme de sources, il",
        "  satisfait de fait l'obligation de substituabilité de la LGPL.",
        "",
        f"  {V.AUTHOR} — {V.WEBSITE} — {V.CONTACT}",
    ]
    return "\n".join(out)


def en_cyclonedx(lignes) -> dict:
    """Document CycloneDX 1.5, format d'échange des nomenclatures logicielles."""
    composants = []
    for d in lignes:
        if d["etat"] == "absent":
            continue
        composants.append({
            "type": "library",
            "name": d["paquet"],
            "version": d["version"],
            "purl": f"pkg:pypi/{d['paquet']}@{d['version']}",
            "publisher": d["editeur"],
            "description": d["role"],
            "licenses": [{"license": {"id": d["licence"]}}],
            "scope": "required" if d["obligatoire"] else "optional",
        })
    for nom, licence, editeur, role in NATIVES:
        composants.append({
            "type": "library", "name": nom, "version": "système",
            "publisher": editeur, "description": role,
            "licenses": [{"license": {"name": licence}}], "scope": "optional",
        })
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.datetime.now(
                datetime.timezone.utc).isoformat(),
            "tools": [{"vendor": V.AUTHOR, "name": "phytoscope-sbom",
                       "version": V.VERSION}],
            "authors": [{"name": V.AUTHOR, "email": V.CONTACT}],
            "component": {
                "type": "application", "name": V.APP_NAME,
                "version": V.VERSION, "publisher": V.AUTHOR,
                "description": V.APP_TAGLINE,
                "licenses": [{"license": {"id": V.LICENSE}}],
                "externalReferences": [{"type": "website", "url": V.WEBSITE}],
            },
        },
        "components": composants,
    }


def en_html(lignes) -> str:
    """Fragment pour le fascicule de nomenclature."""
    out = [f'<div class="origine"><b>{V.APP_NAME} {V.VERSION}</b> — '
           f'nomenclature logicielle (SBOM)<br/>'
           f'<span>{V.AUTHOR} · <a href="{V.WEBSITE}">'
           f'{V.WEBSITE.replace("https://", "")}</a> · {V.CONTACT}</span><br/>'
           f'<span>licence {V.LICENSE} · établie le '
           f'{datetime.date.today().isoformat()}</span></div>',
           '<table class="bom tight"><thead><tr><th>Composant</th>'
           '<th>Version</th><th>Licence</th><th>Éditeur</th><th>Rôle</th>'
           '</tr></thead><tbody>',
           '<tr class="groupe"><td colspan="5">Bibliothèques Python</td></tr>']
    for d in lignes:
        version = d["version"] if d["etat"] == "installé" else "non installé"
        out.append(f'<tr><td>{d["paquet"]}</td><td class="num">{version}</td>'
                   f'<td>{d["licence"]}</td><td>{d["editeur"]}</td>'
                   f'<td>{d["role"]}'
                   + ('' if d["obligatoire"] else
                      '<br/><span class="small">facultatif</span>')
                   + '</td></tr>')
    out.append('<tr class="groupe"><td colspan="5">Bibliothèques natives '
               'atteintes</td></tr>')
    for nom, licence, editeur, role in NATIVES:
        out.append(f'<tr><td>{nom}</td><td class="num">système</td>'
                   f'<td>{licence}</td><td>{editeur}</td><td>{role}</td></tr>')
    out.append(f'<tr class="origine-pied"><td colspan="5">'
               f'{V.APP_NAME} {V.VERSION} · {V.AUTHOR} · '
               f'{V.WEBSITE.replace("https://", "")} · licence {V.LICENSE}'
               f'</td></tr>')
    out.append("</tbody></table>")
    return "\n".join(out)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Nomenclature logicielle de PhytoScope.")
    ap.add_argument("--json", action="store_true", help="format CycloneDX 1.5")
    ap.add_argument("--html", action="store_true", help="fragment pour le fascicule")
    ap.add_argument("-o", "--output", default=None, help="fichier de sortie")
    args = ap.parse_args(argv)

    lignes = inventaire()
    if args.json:
        texte = json.dumps(en_cyclonedx(lignes), ensure_ascii=False, indent=2)
    elif args.html:
        texte = en_html(lignes)
    else:
        texte = en_texte(lignes)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(texte + "\n")
        print(f"✓ écrit : {args.output}")
    else:
        print(texte)
    return 0


if __name__ == "__main__":
    sys.exit(main())
