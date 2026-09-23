#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/tools/doctor.py
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

"""Diagnostic d'installation : ce qui est présent, ce qui manque, quoi faire.

Cet outil ne dépend de rien : il s'exécute avec le Python du système, avant
même que l'environnement virtuel n'existe. C'est le premier réflexe quand
quelque chose ne démarre pas.
"""
import importlib
import platform
import sys

MODULES = [
    ("numpy", True, "traitement du signal"),
    ("PySide6", True, "interface graphique"),
    ("pyqtgraph", False, "tracés temps réel accélérés"),
    ("sounddevice", False, "entrée et sortie audio"),
    ("serial", False, "contrôle de la carte, montages série"),
    ("rtmidi", False, "sortie MIDI"),
]


def main() -> int:
    print()
    print("  PhytoScope — diagnostic d'installation")
    print("  " + "-" * 38)
    print(f"  Python {sys.version.split()[0]}  ({platform.platform()})")
    print(f"  Exécutable : {sys.executable}")
    print()
    manquants, optionnels = [], []
    for nom, obligatoire, role in MODULES:
        try:
            mod = importlib.import_module(nom)
            version = getattr(mod, "__version__", "présent")
            print(f"  [ok]  {nom:<12} {version:<10} {role}")
        except Exception:
            marque = "!!" if obligatoire else "--"
            print(f"  [{marque}]  {nom:<12} {'absent':<10} {role}")
            (manquants if obligatoire else optionnels).append(nom)

    print()
    if manquants:
        print("  Dépendances obligatoires manquantes :", ", ".join(manquants))
        print("  →  make install     (ou : pip install -r requirements.txt)")
    elif optionnels:
        print("  Le logiciel fonctionnera, sans :", ", ".join(optionnels))
        print("  →  make install     pour tout installer")
    else:
        print("  Tout est en place.  →  make run")

    # Périphériques, si possible
    try:
        import sounddevice as sd
        ins = [d["name"] for d in sd.query_devices()
               if d.get("max_input_channels", 0) > 0]
        print()
        print(f"  Entrées audio détectées ({len(ins)}) :")
        for n in ins[:10]:
            print(f"    · {n}")
    except Exception:
        pass
    try:
        from serial.tools import list_ports
        ports = list(list_ports.comports())
        print()
        print(f"  Ports série détectés ({len(ports)}) :")
        for p in ports[:10]:
            print(f"    · {p.device}  {p.description}")
    except Exception:
        pass
    print()
    return 1 if manquants else 0


if __name__ == "__main__":
    sys.exit(main())
