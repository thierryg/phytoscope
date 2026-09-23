#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/sbom.py
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

"""PhytoScope's software bill of materials (SBOM).

A board has its bill of materials; software has one too. It answers the same
questions: what goes into the product, where it comes from, under which
licence, and in exactly which version.

Two formats are produced:

* **CycloneDX 1.5**, as JSON — the format that vulnerability and compliance
  tooling reads;
* **text**, readable by a human, intended for the printed fascicle.

No dependencies: the inventory is established by introspecting the modules
that are actually importable, completed by the reference table below. That
means the SBOM describes **what is installed on this machine**, not what the
requirements file claims — which is precisely the point of the exercise.

Usage:
    python3 tools/sbom.py            text on standard output
    python3 tools/sbom.py --json     CycloneDX
    python3 tools/sbom.py --html     a fragment for the fascicle
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

# (importable module, package name, licence, publisher, role, required)
COMPOSANTS = [
    ("numpy", "numpy", "BSD-3-Clause", "NumPy Developers",
     "numerical computation and signal processing", True),
    ("PySide6", "PySide6", "LGPL-3.0-only", "The Qt Company",
     "the Qt 6 graphical interface", True),
    ("shiboken6", "shiboken6", "LGPL-3.0-only", "The Qt Company",
     "Qt's C++/Python binding", True),
    ("pyqtgraph", "pyqtgraph", "MIT", "Luke Campagnola and contributors",
     "real-time scientific plotting", False),
    ("sounddevice", "sounddevice", "MIT", "Matthias Geier",
     "audio input and output (PortAudio binding)", False),
    ("serial", "pyserial", "BSD-3-Clause", "Chris Liechti",
     "serial port: controlling the board", False),
    ("rtmidi", "python-rtmidi", "MIT", "Christopher Arndt",
     "MIDI output (RtMidi binding)", False),
    ("usb.core", "pyusb", "BSD-3-Clause", "PyUSB Developers",
     "detailed USB descriptors", False),
    ("cffi", "cffi", "MIT", "Armin Rigo, Maciej Fijalkowski",
     "C interface, required by sounddevice", False),
]

# Native libraries reached through those packages: they are part of the product
# delivered to the user, and so they belong in the inventory.
NATIVES = [
    ("PortAudio", "MIT", "portaudio.com", "cross-platform audio layer"),
    ("RtMidi", "modified MIT", "rtmidi (McGill)", "cross-platform MIDI layer"),
    ("Qt", "LGPL-3.0", "The Qt Company", "graphical toolkit"),
    ("libasound (ALSA)", "LGPL-2.1", "alsa-project.org",
     "the Linux kernel's audio layer — system, not redistributed"),
]


def inventaire():
    """Record the version of each component as actually installed."""
    lignes = []
    for module, paquet, licence, editeur, role, obligatoire in COMPOSANTS:
        try:
            m = importlib.import_module(module)
            version = str(getattr(m, "__version__", "") or "present")
            etat = "installed"
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
        "  libraries at run time. Distributed as sources, it satisfies in",
        "  practice the substitutability obligation that the LGPL imposes.",
        "",
        f"  {V.AUTHOR} — {V.WEBSITE} — {V.CONTACT}",
    ]
    return "\n".join(out)


def en_cyclonedx(lignes) -> dict:
    """A CycloneDX 1.5 document, the interchange format for software BOMs."""
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
            "type": "library", "name": nom, "version": "system",
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
           f'software bill of materials (SBOM)<br/>'
           f'<span>{V.AUTHOR} · <a href="{V.WEBSITE}">'
           f'{V.WEBSITE.replace("https://", "")}</a> · {V.CONTACT}</span><br/>'
           f'<span>{V.LICENSE} licence · established on '
           f'{datetime.date.today().isoformat()}</span></div>',
           '<table class="bom tight"><thead><tr><th>Component</th>'
           '<th>Version</th><th>Licence</th><th>Publisher</th><th>Role</th>'
           '</tr></thead><tbody>',
           '<tr class="groupe"><td colspan="5">Python libraries</td></tr>']
    for d in lignes:
        version = d["version"] if d["etat"] == "installed" else "not installed"
        out.append(f'<tr><td>{d["paquet"]}</td><td class="num">{version}</td>'
                   f'<td>{d["licence"]}</td><td>{d["editeur"]}</td>'
                   f'<td>{d["role"]}'
                   + ('' if d["obligatoire"] else
                      '<br/><span class="small">facultatif</span>')
                   + '</td></tr>')
    out.append('<tr class="groupe"><td colspan="5">Native libraries '
               'atteintes</td></tr>')
    for nom, licence, editeur, role in NATIVES:
        out.append(f'<tr><td>{nom}</td><td class="num">system</td>'
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
        print(f"✓ written: {args.output}")
    else:
        print(texte)
    return 0


if __name__ == "__main__":
    sys.exit(main())
