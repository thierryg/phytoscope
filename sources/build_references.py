#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — sources/build_references.py
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

"""Render the reference documents of `sources/` to PDF.

What these documents are
------------------------

`sources/` holds reference material, and almost all of it is material we did
not write — datasheets, patents, third-party projects, each with its own
licence. These few are the exception: **we wrote them**, for this project,
because we needed the reference and could not redistribute the normative one.

Each lives in its own directory as `reference.html` plus a stylesheet, and is
rendered here with WeasyPrint — the same engine the ten publications use, so
there is one paged-media toolchain in this repository and not two.

    sources/midi/reference.html   ->  sources/midi/MIDI-Protocol-Reference.pdf
    sources/usb/reference.html    ->  sources/usb/USB-Device-Reference.pdf

Why the PDF is committed
------------------------

Unlike `build/`, which is regenerable and ignored, these PDFs are tracked.
The point of a reference document is that it is *there* when you need it —
on a machine with no WeasyPrint, in a clone made from a phone, next to the
datasheets it complements. They are small, they are ours, and they are MIT
licensed.

The HTML remains the source. Never edit the PDF (`C-45`).

Usage
-----

    python3 sources/build_references.py            # everything
    python3 sources/build_references.py midi       # one directory

Exit status is 1 if a document fails to render, or if a declared directory
holds no `reference.html`.
"""
from __future__ import annotations

import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))

#  (directory, output file name, document title for the PDF metadata)
DOCUMENTS = [
    ("midi", "MIDI-Protocol-Reference.pdf",
     "MIDI Protocol Reference — PhytoScope"),
    ("usb", "USB-Device-Reference.pdf",
     "USB Device and Frame Reference — PhytoScope"),
]

VERT = "\033[0;32m"
ROUGE = "\033[0;31m"
GRIS = "\033[0;90m"
NEUTRE = "\033[0m"


def rendre(dossier: str, sortie: str, titre: str) -> bool:
    """Render one document. Returns True on success."""
    source = os.path.join(ICI, dossier, "reference.html")
    if not os.path.exists(source):
        print(f"{ROUGE}  ✗ {dossier}/reference.html not found{NEUTRE}")
        return False

    try:
        from weasyprint import HTML
    except ImportError:
        print(f"{ROUGE}  ✗ WeasyPrint is missing — "
              f"pip install weasyprint{NEUTRE}")
        return False

    cible = os.path.join(ICI, dossier, sortie)
    print(f"{GRIS}  · {dossier}/reference.html → {sortie}{NEUTRE}")
    #  The document title comes from the HTML <title>; WeasyPrint puts it
    #  in the PDF metadata by itself. `titre` is kept in DOCUMENTS so that
    #  this script can report what it is building without opening the file.
    HTML(filename=source).write_pdf(cible)

    taille = os.path.getsize(cible)
    pages = _compter_les_pages(cible)
    print(f"{VERT}  ✓ {sortie}  ({taille / 1024:.0f} kB, "
          f"{pages if pages else '?'} pages){NEUTRE}")
    return True


def _compter_les_pages(chemin: str) -> int:
    """Page count, read from the PDF itself.

    `pdfinfo` first, because it is right. Scanning the raw file for `/Count`
    was the first attempt and it reported nothing: WeasyPrint compresses the
    page tree into an object stream, so the string is not in the file. The
    fallback is kept for a machine without poppler, where an uncompressed
    PDF may still be readable that way.

    pypdf would settle it, but it is not a dependency of this project
    (`C-40`) and this is one report line. A failure here is not a failure of
    the render.
    """
    try:
        import subprocess
        issue = subprocess.run(["pdfinfo", chemin], capture_output=True,
                               text=True, timeout=30)
        for ligne in issue.stdout.splitlines():
            if ligne.startswith("Pages:"):
                return int(ligne.split()[1])
    except Exception:                                      # noqa: BLE001
        pass
    try:
        import re
        with open(chemin, "rb") as f:
            brut = f.read()
        comptes = [int(m.group(1))
                   for m in re.finditer(rb"/Count\s+(\d+)", brut)]
        return max(comptes) if comptes else 0
    except Exception:                                      # noqa: BLE001
        return 0


def main(argv: list[str]) -> int:
    demandes = argv[1:]
    a_faire = [d for d in DOCUMENTS if not demandes or d[0] in demandes]
    if not a_faire:
        print(f"{ROUGE}  ✗ nothing to do — known directories: "
              f"{', '.join(d[0] for d in DOCUMENTS)}{NEUTRE}")
        return 1

    print()
    print("  Reference documents under sources/")
    print()
    echecs = 0
    for dossier, sortie, titre in a_faire:
        if not rendre(dossier, sortie, titre):
            echecs += 1
    print()
    if echecs:
        print(f"{ROUGE}  {echecs} document(s) failed{NEUTRE}")
        return 1
    print(f"{VERT}  {len(a_faire)} document(s) produced{NEUTRE}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
