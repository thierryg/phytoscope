# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/theme.py
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

"""Thèmes graphiques — sombre, clair, contraste renforcé.

Les couleurs reprennent la charte de l'ouvrage : vert forêt, vert sève, or.
Un instrument de mesure se regarde longtemps ; le thème sombre est donc le
défaut, mais l'accessibilité impose de fournir un contraste renforcé.
"""
from __future__ import annotations

from typing import Dict

from . import polices

PALETTES: Dict[str, Dict[str, str]] = {
    "sombre": {
        "fond": "#12201B", "fond2": "#16281F", "fond3": "#0A1712",
        "trait": "#26443A", "texte": "#EAF2EC", "texte2": "#9FB8AB",
        "accent": "#3F7D5A", "accent2": "#6FA98A", "or": "#E0C073",
        "alerte": "#E06C5A", "trace": "#7FE0A8", "trace2": "#E0C073",
        "grille": "#1B3129",
    },
    "clair": {
        "fond": "#FBF9F1", "fond2": "#F2EFE2", "fond3": "#FFFFFF",
        "trait": "#D9D9C6", "texte": "#23302C", "texte2": "#6B7A72",
        "accent": "#3F7D5A", "accent2": "#2F7D5E", "or": "#B08528",
        "alerte": "#A8552E", "trace": "#2F7D5E", "trace2": "#B08528",
        "grille": "#E6E6D8",
    },
    "contraste": {
        "fond": "#000000", "fond2": "#0A0A0A", "fond3": "#000000",
        "trait": "#FFFFFF", "texte": "#FFFFFF", "texte2": "#E0E0E0",
        "accent": "#00D06A", "accent2": "#00FF88", "or": "#FFD000",
        "alerte": "#FF4040", "trace": "#00FF88", "trace2": "#FFD000",
        "grille": "#303030",
    },
}


def palette(name: str) -> Dict[str, str]:
    return PALETTES.get(name, PALETTES["sombre"])


def stylesheet(name: str, font_scale: float = 1.0) -> str:
    p = palette(name)
    #  La pile de familles vit dans `polices` : un seul endroit à
    #  corriger le jour où une police manque sur un système.
    mono = polices.css_mono()
    s = max(0.8, min(font_scale, 2.0))
    #  Sur macOS le point vaut 1/72 pouce logique contre 1/96 ailleurs :
    #  sans cette correction toute l'interface y serait un tiers plus
    #  petite. Voir `polices.facteur()`.
    f = polices.facteur()
    base = round(10 * s * f)
    big = round(13 * s * f)
    return f"""
    QWidget {{ background: {p['fond']}; color: {p['texte']};
               font-size: {base}pt; }}
    QMainWindow, QDialog {{ background: {p['fond']}; }}
    QTabWidget::pane {{ border: 1px solid {p['trait']}; border-radius: 6px;
                        background: {p['fond2']}; }}
    QTabBar::tab {{ background: {p['fond2']}; color: {p['texte2']};
                    padding: 8px 18px; margin-right: 3px;
                    border: 1px solid {p['trait']};
                    border-top-left-radius: 6px; border-top-right-radius: 6px; }}
    QTabBar::tab:selected {{ background: {p['accent']}; color: #FFFFFF;
                             font-weight: bold; }}
    QGroupBox {{ border: 1px solid {p['trait']}; border-radius: 6px;
                 margin-top: {round(14 * s)}px; padding-top: 8px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px;
                        color: {p['or']}; font-weight: bold; }}
    QPushButton {{ background: {p['fond3']}; border: 1px solid {p['trait']};
                   border-radius: 5px; padding: 6px 14px; }}
    QPushButton:hover {{ border-color: {p['accent2']}; }}
    QPushButton:pressed {{ background: {p['accent']}; color: #fff; }}
    QPushButton:checked {{ background: {p['accent']}; color: #fff;
                           border-color: {p['accent2']}; }}
    QPushButton:disabled {{ color: {p['texte2']}; border-color: {p['trait']}; }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
        background: {p['fond3']}; border: 1px solid {p['trait']};
        border-radius: 4px; padding: 4px 6px; selection-background-color: {p['accent']}; }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QSlider::groove:horizontal {{ height: 4px; background: {p['trait']};
                                  border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {p['or']}; width: 14px;
                                  margin: -6px 0; border-radius: 7px; }}
    QProgressBar {{ border: 1px solid {p['trait']}; border-radius: 4px;
                    text-align: center; background: {p['fond3']}; }}
    QProgressBar::chunk {{ background: {p['accent']}; border-radius: 3px; }}
    QHeaderView::section {{ background: {p['fond3']}; color: {p['texte2']};
                            border: none; border-bottom: 1px solid {p['trait']};
                            padding: 5px; }}
    QTableWidget, QListWidget, QTreeWidget {{ background: {p['fond3']};
        border: 1px solid {p['trait']}; border-radius: 5px;
        gridline-color: {p['grille']}; alternate-background-color: {p['fond2']}; }}
    QCheckBox::indicator, QRadioButton::indicator {{ width: 15px; height: 15px; }}
    QToolTip {{ background: {p['fond3']}; color: {p['texte']};
                border: 1px solid {p['or']}; padding: 4px; }}
    QStatusBar {{ background: {p['fond3']}; border-top: 1px solid {p['trait']}; }}
    QLabel#titre {{ font-size: {big}pt; font-weight: bold; color: {p['or']}; }}
    QLabel#valeur {{ {mono} font-size: {round(28 * s * polices.facteur())}pt;
                     color: {p['trace']}; }}
    QLabel#unite {{ color: {p['texte2']}; }}
    QLabel#alerte {{ color: {p['alerte']}; font-weight: bold; }}
    """
