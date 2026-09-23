# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/i18n.py
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

"""Traduction de l'interface — le français pour source, tout le reste en JSON.

Ajouter une langue ne requested **aucune modification du code** : on dépose un
file_path :file:`<code>.json` dans :file:`phytoscope/langues/`, et la langue
apparaît dans les réglages au démarrage suivant. Le logiciel découvre les
catalogues présents plutôt que de connaître une entries ; c'est la seule façon
qu'un utilisateur puisse add la sienne sans nous attendre.

Structure d'un catalogue
------------------------

::

    {
      "_langue": {
        "name": "Bahasa Indonesia",     the language's name, in that language
        "english_name": "Indonesian",   its name in the source language
        "direction": "ltr",             "rtl" for Arabic, Hebrew, Persian
        "author": "who translated it"
      },
      "Oscilloscope": "Osiloskop",
      "Compute now": "Hitung sekarang"
    }

Trois décisions de conception, et leurs raisons
-----------------------------------------------

**Les clés sont les phrases françaises elles-mêmes**, et non des identifiants
abstraits du genre ``menu.file.open``. Le code reste donc lisible —
``t("Oscilloscope")`` se comprend sans consulter un catalogue — et, surtout, une
traduction manquante retombe silencieusement sur un français correct plutôt que
sur un identifiant nu. Un logiciel de mesure à moitié traduit doit rester
usable ; il ne doit jamais afficher ``tab.scope.title``.

**Une entrée vide vaut une entrée absente.** On peut donc livrer un catalogue
complet aux trois quarts, et le compléter phrase par phrase : rien ne casse, et
l'onglet de diagnostic affiche le taux de couverture réel de chaque langue.

**Le changement de langue prend effet au redémarrage.** Retraduire à chaud
supposerait que chaque libellé sache se réécrire ; ce serait beaucoup de code
pour une opération qu'on fait une fois. L'interface propose donc de relancer le
logiciel — ce que font aussi les appareils du commerce.

Usage
-----

::

    from ..i18n import t
    bouton = QPushButton(t("Calculer maintenant"))

Les chaînes composées se traduisent **avant** la substitution, de sorte que
chaque langue puisse déplacer ses variables :

::

    t("{n} énoncés par minute").format(n=6)
"""
from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from .core.logging_setup import get_logger

log = get_logger(__name__)

__all__ = ["t", "definir_langue", "langue_courante", "direction_courante",
           "langues_disponibles", "catalogue", "missing", "meta",
           "chemin_catalogue", "DOSSIER", "LANGUE_SOURCE", "ecrire_modele",
           "couverture", "collecter_cles"]

#  English has been the SOURCE language since 2026-09-22: the code's labels
#  are written in English, and French became a catalogue like any other. That
#  is not a display detail — it is what makes the code readable by somebody
#  who does not speak French, and a source language has, by construction, no
#  catalogue to keep up to date.
#
#  The third field of LIVREES was called `nom_fr` and held the name in the
#  source language, which is to say in English. Renamed `english_name` on
#  2026-09-23, in the table and in the ten catalogues' `_langue` block, which
#  is the only thing that reads it.
LANGUE_SOURCE = "en"

#  Les langues connues du logiciel : leur name lisible, leur name français
#  et leur meaning de lecture. La table ne fait que cela — afficher un name
#  avant d'avoir ouvert le file_path, et fixer l'order du menu.
#
#  Une langue déclarée ici SANS son catalogue n'apparaît pas : voir
#  codes_presents(), qui ne retient que ce qui existe sur le disque. La
#  table peut donc annoncer une ambition — les 48 langues demandées le
#  2026-09-22 — sans prétendre que le travail est fait. « couverture »
#  dit la vérité, langue par langue.
#
#  Et une langue PRÉSENTE mais absente d'ici apparaît quand même, rangée
#  après les autres : c'est ce qui permet d'en déposer une soi-même.
LIVREES = (
    #  --- livrées et complètes ---
    ("en", "English (US)", "American English", "ltr"),
    ("fr", "Français", "French", "ltr"),
    ("es", "Español", "Spanish", "ltr"),
    ("pt", "Português", "Portuguese", "ltr"),
    ("it", "Italiano", "Italian", "ltr"),
    ("id", "Bahasa Indonesia", "Indonesian", "ltr"),
    ("ru", "Русский", "Russian", "ltr"),
    ("zh", "中文", "Chinese", "ltr"),
    ("ja", "日本語", "Japanese", "ltr"),
    ("ko", "한국어", "Korean", "ltr"),
    ("ar", "العربية", "Arabic", "rtl"),
    #  --- demandées, catalogue à écrire ---
    ("de", "Deutsch", "German", "ltr"),
    ("nl", "Nederlands", "Dutch", "ltr"),
    ("pl", "Polski", "Polish", "ltr"),
    ("el", "Ελληνικά", "Greek", "ltr"),
    ("tr", "Türkçe", "Turkish", "ltr"),
    ("fi", "Suomi", "Finnish", "ltr"),
    ("hu", "Magyar", "Hungarian", "ltr"),
    ("et", "Eesti", "Estonian", "ltr"),
    ("he", "עברית", "Hebrew", "rtl"),
    ("fa", "فارسی", "Persian", "rtl"),
    ("hi", "हिन्दी", "Hindi", "ltr"),
    ("bn", "বাংলা", "Bengali", "ltr"),
    ("ta", "தமிழ்", "Tamil", "ltr"),
    ("te", "తెలుగు", "Telugu", "ltr"),
    ("kn", "ಕನ್ನಡ", "Kannada", "ltr"),
    ("yue", "粵語", "Cantonese", "ltr"),
    ("th", "ไทย", "Thai", "ltr"),
    ("vi", "Tiếng Việt", "Vietnamese", "ltr"),
    ("ms", "Bahasa Melayu", "Malay", "ltr"),
    ("tl", "Tagalog", "Tagalog", "ltr"),
    ("mg", "Malagasy", "Malagasy", "ltr"),
    ("mi", "Te Reo Māori", "Māori", "ltr"),
    ("sw", "Kiswahili", "Swahili", "ltr"),
    ("yo", "Yorùbá", "Yoruba", "ltr"),
    ("zu", "isiZulu", "Zulu", "ltr"),
    ("ig", "Igbo", "Igbo", "ltr"),
    ("am", "አማርኛ", "Amharic", "ltr"),
    ("ha", "Hausa", "Hausa", "ltr"),
    ("kk", "Қазақ тілі", "Kazakh", "ltr"),
    ("uz", "Oʻzbekcha", "Uzbek", "ltr"),
)

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "languages")

_courante = LANGUE_SOURCE
_catalogue: Dict[str, str] = {}
_chargees: Dict[str, Dict[str, str]] = {}
_metas: Dict[str, Dict[str, str]] = {}
#  Tout ce qui a été demandé sans traduction : sert au report de couverture.
_absentes: Dict[str, set] = {}


# ---------------------------------------------------------------------------
#  Chargement
# ---------------------------------------------------------------------------
def chemin_catalogue(code: str) -> str:
    return os.path.join(DOSSIER, f"{code}.json")


def catalogue(code: str) -> Dict[str, str]:
    """Le catalogue d'une langue, chargé une fois et gardé en mémoire."""
    code = (code or LANGUE_SOURCE).lower()
    if code in _chargees:
        return _chargees[code]
    table: Dict[str, str] = {}
    info: Dict[str, str] = {}
    if code != LANGUE_SOURCE:
        path = chemin_catalogue(code)
        try:
            with open(path, encoding="utf-8") as f:
                raw = json.load(f)
            info = dict(raw.get("_langue") or {})
            #  Une traduction vide retombe sur le français : elle ne doit
            #  jamais afficher une étiquette blanche.
            table = {str(k): str(v) for k, v in raw.items()
                     if not k.startswith("_") and isinstance(v, str) and v.strip()}
        except FileNotFoundError:
            log.warning("Catalogue de traduction absent : %s — "
                        "l'interface restera en français.", path)
        except (OSError, ValueError) as exc:
            log.error("Catalogue « %s » illisible (%s) — repli sur le français.",
                      code, exc)
    _chargees[code] = table
    _metas[code] = info
    return table


def meta(code: str) -> Dict[str, str]:
    """Le bloc ``_langue`` d'un catalogue, complété par la table des livrées."""
    code = (code or LANGUE_SOURCE).lower()
    catalogue(code)
    info = dict(_metas.get(code) or {})
    for c, name, english_name, direction in LIVREES:
        if c == code:
            info.setdefault("name", name)
            info.setdefault("english_name", english_name)
            info.setdefault("direction", direction)
    info.setdefault("name", code)
    info.setdefault("english_name", code)
    info.setdefault("direction", "ltr")
    return info


def codes_presents() -> List[str]:
    """Les langues réellement disponibles : le français, plus les catalogues.

    L'order est celui de :data:`LIVREES` pour ce qui est connu, alphabétique
    pour ce qui a été ajouté ensuite — une langue déposée par l'utilisateur
    n'est pas reléguée, elle est simplement rangée après celles d'origin.
    """
    found = set()
    try:
        for name in os.listdir(DOSSIER):
            if name.endswith(".json") and not name.startswith("_"):
                found.add(name[:-5].lower())
    except OSError:
        pass
    order = [c for c, _, _, _ in LIVREES if c == LANGUE_SOURCE or c in found]
    order += sorted(c for c in found
                    if c not in {x for x, _, _, _ in LIVREES})
    return order


def langues_disponibles() -> List[tuple]:
    """(code, name local, name français, entrées traduites, direction)."""
    out = []
    for code in codes_presents():
        info = meta(code)
        n = -1 if code == LANGUE_SOURCE else len(catalogue(code))
        out.append((code, info["name"], info["english_name"], n,
                    info["direction"]))
    return out


# ---------------------------------------------------------------------------
#  Traduction
# ---------------------------------------------------------------------------
def definir_langue(code: str) -> str:
    """Choisit la langue de l'interface. Retourne le code réellement retenu."""
    global _courante, _catalogue
    code = (code or LANGUE_SOURCE).lower()
    if code != LANGUE_SOURCE and code not in codes_presents():
        log.warning("Langue « %s » sans catalogue : repli sur le français.", code)
        code = LANGUE_SOURCE
    _courante = code
    _catalogue = catalogue(code)
    if code != LANGUE_SOURCE:
        log.info("Interface en %s — %d libellés traduits.", code, len(_catalogue))
    return code


def langue_courante() -> str:
    return _courante


def direction_courante() -> str:
    """« ltr » ou « rtl » — l'arabe impose d'inverser toute la mise en page."""
    return meta(_courante)["direction"]


def t(text: str) -> str:
    """Le libellé dans la langue current, ou le français s'il manque.

    C'est volontairement une fonction triviale : elle est appelée des centaines
    de fois à la construction de l'interface, et tout ce qui coûte doit rester
    dans le chargement, pas ici.
    """
    if _courante == LANGUE_SOURCE or not text:
        return text
    traduit = _catalogue.get(text)
    if traduit is None:
        _absentes.setdefault(_courante, set()).add(text)
        return text
    return traduit


def missing(code: Optional[str] = None) -> List[str]:
    """Les libellés demandés pendant cette session et non traduits.

    Une traduction incomplète doit être visible par celui qui l'entretient,
    pas découverte par l'utilisateur : l'onglet de diagnostic affiche ce compte.
    """
    return sorted(_absentes.get(code or _courante, set()))


def couverture(code: str, cles: Optional[List[str]] = None) -> float:
    """Part des libellés traduits, entre 0 et 1."""
    if code == LANGUE_SOURCE:
        return 1.0
    table = catalogue(code)
    if cles:
        return sum(1 for c in cles if table.get(c)) / max(len(cles), 1)
    return 1.0 if table else 0.0


def ecrire_modele(path: str, cles: List[str], code: str = "",
                  garder: bool = True) -> int:
    """Écrit un catalogue à compléter : toutes les clés, values vides.

    Si un catalogue existe déjà pour ``code``, ses traductions sont conservées
    et seules les clés nouvelles arrivent vides — c'est ce qui permet de
    maintenir une traduction au fil des versions sans tout relire.
    """
    existant = catalogue(code) if (code and garder) else {}
    info = meta(code) if code else {"name": "", "english_name": "", "direction": "ltr"}
    sortie: Dict[str, object] = {"_langue": {
        "name": info.get("name", ""), "english_name": info.get("english_name", ""),
        "direction": info.get("direction", "ltr"),
        "author": info.get("author", ""),
    }}
    for key in cles:
        sortie[key] = existant.get(key, "")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return sum(1 for c in cles if not existant.get(c))


# ---------------------------------------------------------------------------
#  Inventaire des libellés — la source unique de vérité
# ---------------------------------------------------------------------------
def collecter_cles() -> List[str]:
    """Tous les libellés traduisibles du logiciel, dans l'order de rencontre.

    Deux gisements, parce que l'interface en a deux :

    * les appels ``t("…")`` du code, trouvés par **analyse syntaxique** — jamais
      par expression régulière, qui se tromperait sur les chaînes réparties sur
      plusieurs rows ;
    * les **tables de données** — instruments, gammes, profils, descripteurs,
      grammaires, textes de l'aide — dont le contenu est traduit au moment de
      l'affichage, et qu'il serait absurde de recopier ici.

    Utilisé par l'outil ``tools/i18n.py`` et par le bouton « Écrire un modèle de
    traduction » des réglages : les deux voient exactement la même entries.
    """
    import ast

    racine = os.path.dirname(os.path.abspath(__file__))
    vues, cles = set(), []

    def add(text):
        text = str(text or "")
        if text and text not in vues:
            vues.add(text)
            cles.append(text)

    class _Collecteur(ast.NodeVisitor):
        def visit_Call(self, node):
            name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if name == "t" and node.args:
                a = node.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    add(a.value)
            self.generic_visit(node)

    for directory, _, fichiers in os.walk(racine):
        if "__pycache__" in directory:
            continue
        for name in sorted(fichiers):
            if not name.endswith(".py"):
                continue
            path = os.path.join(directory, name)
            try:
                _Collecteur().visit(ast.parse(open(path, encoding="utf-8").read()))
            except (OSError, SyntaxError) as exc:       # pragma: no cover
                log.warning("Inventaire : %s illisible (%s)", path, exc)

    #  Les tables de données. Importées tardivement : ce module est chargé très
    #  tôt, et rien de tout cela n'est nécessaire pour translate.
    try:
        from .core.fingerprint import DESCRIPTORS as EMPREINTE, THRESHOLDS
        from .core.features import DESCRIPTORS
        from .core.quantities import inventory as GRANDEURS
        from .core.logging_setup import NIVEAUX_FR
        from .core.sampling import FENETRES
        from .music.instruments import get as _instr, instrument_list
        from .music.lexicon import GRAMMAIRES
        from .music.profiles import profile_list
        from .music.scales import scale_names
        from .ui.help_dialog import DEMARRAGE, ONGLETS, RACCOURCIS
        from .ui.plot_tab import SOURCES
        from .ui.voice_tab import AVERTISSEMENT
    except Exception as exc:                            # noqa: BLE001
        log.warning("Inventaire des tables impossible : %s", exc)
        return cles

    for key, label in instrument_list():
        add(label)
        try:
            add(_instr(key).description)
        except Exception:                               # noqa: BLE001
            pass
    for _, label in scale_names():
        add(label)
    for _, label in profile_list():
        add(label)
    for value in FENETRES.values():
        add(value)
    for triplet in DESCRIPTORS.values():
        for x in triplet:
            add(x)
    for g in GRAMMAIRES.values():
        #  GRAMMAIRES lives in `music/lexicon.py`, whose keys are still
        #  French: this one is its key, not ours.
        add(g["titre"])
        add(g["description"])
    for title, rows in RACCOURCIS:
        add(title)
        for _, role in rows:
            add(role)
    for name, text in ONGLETS:
        add(name)
        add(text)
    for _, title, text in DEMARRAGE:
        add(title)
        add(text)
    for value in SOURCES.values():
        add(value)
    for value in NIVEAUX_FR.values():
        add(value)
    add(AVERTISSEMENT)
    #  Les descripteurs de l'fingerprint et les phrases de qualification : ils
    #  sont traduits à l'affichage, comme les autres tables de données.
    for _cle, label, _unite, _poids, _log in EMPREINTE:
        add(label)
    for _borne, phrase in THRESHOLDS:
        add(phrase)
    #  Les grandeurs scientifiques du multimètre : récoltées en faisant
    #  tourner le calcul, jamais recopiées — une grandeur ajoutée sans
    #  traduction doit faire échouer la couverture.
    for phrase in GRANDEURS():
        add(phrase)
    #  Le name français de chaque langue, affiché dans la entries des réglages.
    for _, _, english_name, _ in LIVREES:
        add(english_name)
    return cles
