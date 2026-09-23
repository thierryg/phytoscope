# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/ui/theme.py
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

"""Thèmes graphiques — sombre, clair, contraste renforcé.

Les couleurs reprennent la charte de l'ouvrage : vert forêt, vert sève, or.
Un instrument de mesure se regarde longtemps ; le thème sombre est donc le
défaut, mais l'accessibilité impose de fournir un contraste renforcé.
"""
from __future__ import annotations

from typing import Dict

from . import fonts

PALETTES: Dict[str, Dict[str, str]] = {
    "sombre": {
        "background": "#12201B", "background2": "#16281F", "background3": "#0A1712",
        "line": "#26443A", "text": "#EAF2EC", "text2": "#9FB8AB",
        "accent": "#3F7D5A", "accent2": "#6FA98A", "gold": "#E0C073",
        "alert": "#E06C5A", "trace": "#7FE0A8", "trace2": "#E0C073",
        "grid": "#1B3129",
    },
    "clair": {
        "background": "#FBF9F1", "background2": "#F2EFE2", "background3": "#FFFFFF",
        "line": "#D9D9C6", "text": "#23302C", "text2": "#6B7A72",
        "accent": "#3F7D5A", "accent2": "#2F7D5E", "gold": "#B08528",
        "alert": "#A8552E", "trace": "#2F7D5E", "trace2": "#B08528",
        "grid": "#E6E6D8",
    },
    "contraste": {
        "background": "#000000", "background2": "#0A0A0A", "background3": "#000000",
        "line": "#FFFFFF", "text": "#FFFFFF", "text2": "#E0E0E0",
        "accent": "#00D06A", "accent2": "#00FF88", "gold": "#FFD000",
        "alert": "#FF4040", "trace": "#00FF88", "trace2": "#FFD000",
        "grid": "#303030",
    },
}


def palette(name: str) -> Dict[str, str]:
    return PALETTES.get(name, PALETTES["sombre"])


def stylesheet(name: str, font_scale: float = 1.0) -> str:
    p = palette(name)
    #  La pile de familles vit dans `polices` : un seul endroit à
    #  corriger le jour où une police manque sur un système.
    mono = fonts.css_mono()
    s = max(0.8, min(font_scale, 2.0))
    #  Sur macOS le point vaut 1/72 pouce logique contre 1/96 ailleurs :
    #  sans cette correction toute l'interface y serait un tiers plus
    #  petite. Voir `fonts.facteur()`.
    f = fonts.facteur()
    base = round(10 * s * f)
    big = round(13 * s * f)
    return f"""
    QWidget {{ background: {p['background']}; color: {p['text']};
               font-size: {base}pt; }}
    QMainWindow, QDialog {{ background: {p['background']}; }}
    QTabWidget::pane {{ border: 1px solid {p['line']}; border-radius: 6px;
                        background: {p['background2']}; }}
    QTabBar::tab {{ background: {p['background2']}; color: {p['text2']};
                    padding: 8px 18px; margin-right: 3px;
                    border: 1px solid {p['line']};
                    border-top-left-radius: 6px; border-top-right-radius: 6px; }}
    QTabBar::tab:selected {{ background: {p['accent']}; color: #FFFFFF;
                             font-weight: bold; }}
    QGroupBox {{ border: 1px solid {p['line']}; border-radius: 6px;
                 margin-top: {round(14 * s)}px; padding-top: 8px; }}
    QGroupBox::title {{ subcontrol-origin: margin; left: 10px;
                        color: {p['gold']}; font-weight: bold; }}
    QPushButton {{ background: {p['background3']}; border: 1px solid {p['line']};
                   border-radius: 5px; padding: 6px 14px; }}
    QPushButton:hover {{ border-color: {p['accent2']}; }}
    QPushButton:pressed {{ background: {p['accent']}; color: #fff; }}
    QPushButton:checked {{ background: {p['accent']}; color: #fff;
                           border-color: {p['accent2']}; }}
    QPushButton:disabled {{ color: {p['text2']}; border-color: {p['line']}; }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QPlainTextEdit, QTextEdit {{
        background: {p['background3']}; border: 1px solid {p['line']};
        border-radius: 4px; padding: 4px 6px; selection-background-color: {p['accent']}; }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QSlider::groove:horizontal {{ height: 4px; background: {p['line']};
                                  border-radius: 2px; }}
    QSlider::handle:horizontal {{ background: {p['gold']}; width: 14px;
                                  margin: -6px 0; border-radius: 7px; }}
    QProgressBar {{ border: 1px solid {p['line']}; border-radius: 4px;
                    text-align: center; background: {p['background3']}; }}
    QProgressBar::chunk {{ background: {p['accent']}; border-radius: 3px; }}
    QHeaderView::section {{ background: {p['background3']}; color: {p['text2']};
                            border: none; border-bottom: 1px solid {p['line']};
                            padding: 5px; }}
    QTableWidget, QListWidget, QTreeWidget {{ background: {p['background3']};
        border: 1px solid {p['line']}; border-radius: 5px;
        gridline-color: {p['grid']}; alternate-background-color: {p['background2']}; }}
    QCheckBox::indicator, QRadioButton::indicator {{ width: 15px; height: 15px; }}
    QToolTip {{ background: {p['background3']}; color: {p['text']};
                border: 1px solid {p['gold']}; padding: 4px; }}
    QStatusBar {{ background: {p['background3']}; border-top: 1px solid {p['line']}; }}
    QLabel#titre {{ font-size: {big}pt; font-weight: bold; color: {p['gold']}; }}
    QLabel#valeur {{ {mono} font-size: {round(28 * s * fonts.facteur())}pt;
                     color: {p['trace']}; }}
    QLabel#unite {{ color: {p['text2']}; }}
    QLabel#alerte {{ color: {p['alert']}; font-weight: bold; }}
    """
