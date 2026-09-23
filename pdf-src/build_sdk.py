#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — pdf-src/build_sdk.py
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

"""Builds the developer companion volume "Writing a module for PhytoScope".

    build/writing-a-phytoscope-module.pdf

The document describes the modules' programming interface, the SDK, and what a
module is allowed to do. It is built from the fragments in
`pdf-src/writing-a-phytoscope-module/`, by the same mould as the other two
volumes — the same style sheets, the same clickable contents, the same
metadata.

The content is the same as that of `src/sdk/docs/`, laid out for print. Two
forms, one source of truth: the Markdown is read in the repository, the PDF is
printed and carried about.

Usage:
    python3 build_sdk.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

#  We borrow the companion volume's mould: reading the fragments, numbering
#  the figures, the contents, the checks. Copying it would have guaranteed it
#  drifts.
import build_board as mould

mould.PARTS = os.path.join(mould.SRC, "writing-a-phytoscope-module")

ORDER = [
    "00-cover",
    "01-titlepage",
    "02-notice",
    "03-toc",
    "04-first-module",
    "05-anatomy",
    "06-capabilities",
    "07-events",
    "08-pitfalls",
    "09-migrating",
    "10-closing",
]

DOCUMENT = {
    "out": "writing-a-phytoscope-module.pdf",
    "lang": "en",
    "title": "Writing a module for PhytoScope",
    "running": "Writing a module for PhytoScope",
    "description": (
        "The programming interface of PhytoScope's modules, the SDK, and what "
        "a module is allowed to do: the five capabilities, the events, "
        "testing without hardware, and the pitfalls."),
    "keywords": ("PhytoScope, module, SDK, API, Python, extension, plugin, "
                 "biosignal, plant"),
    "order": ORDER,
}


def main(argv):
    #  `build_board.build` reads its fragments from `mould.PARTS`, which we
    #  have just redirected: it therefore produces our document unchanged.
    return 0 if mould.build("sdk", DOCUMENT) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
