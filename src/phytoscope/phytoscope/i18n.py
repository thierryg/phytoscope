# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/i18n.py
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

"""Traduction de l'interface — le français pour source, tout le reste en JSON.

Ajouter une langue ne demande **aucune modification du code** : on dépose un
fichier :file:`<code>.json` dans :file:`phytoscope/langues/`, et la langue
apparaît dans les réglages au démarrage suivant. Le logiciel découvre les
catalogues présents plutôt que de connaître une liste ; c'est la seule façon
qu'un utilisateur puisse ajouter la sienne sans nous attendre.

Structure d'un catalogue
------------------------

::

    {
      "_langue": {
        "nom": "Bahasa Indonesia",      nom de la langue, dans la langue
        "nom_fr": "indonésien",         son nom en français
        "direction": "ltr",             "rtl" pour l'arabe, l'hébreu, le persan
        "auteur": "qui l'a traduite"
      },
      "Oscilloscope": "Osiloskop",
      "Calculer maintenant": "Hitung sekarang"
    }

Trois décisions de conception, et leurs raisons
-----------------------------------------------

**Les clés sont les phrases françaises elles-mêmes**, et non des identifiants
abstraits du genre ``menu.file.open``. Le code reste donc lisible —
``t("Oscilloscope")`` se comprend sans consulter un catalogue — et, surtout, une
traduction manquante retombe silencieusement sur un français correct plutôt que
sur un identifiant nu. Un logiciel de mesure à moitié traduit doit rester
utilisable ; il ne doit jamais afficher ``tab.scope.title``.

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
           "langues_disponibles", "catalogue", "manquantes", "meta",
           "chemin_catalogue", "DOSSIER", "LANGUE_SOURCE", "ecrire_modele",
           "couverture", "collecter_cles"]

LANGUE_SOURCE = "fr"

#  Les langues livrées avec le logiciel. Cette table ne sert qu'à deux choses :
#  afficher un nom lisible avant d'avoir ouvert le fichier, et fixer l'ordre du
#  menu. Une langue absente d'ici mais présente dans le dossier apparaît quand
#  même — c'est tout l'intérêt.
LIVREES = (
    ("fr", "Français", "français", "ltr"),
    ("en", "English (US)", "américain", "ltr"),
    ("es", "Español", "espagnol", "ltr"),
    ("pt", "Português", "portugais", "ltr"),
    ("it", "Italiano", "italien", "ltr"),
    ("id", "Bahasa Indonesia", "indonésien", "ltr"),
    ("ru", "Русский", "russe", "ltr"),
    ("zh", "中文", "chinois", "ltr"),
    ("ja", "日本語", "japonais", "ltr"),
    ("ko", "한국어", "coréen", "ltr"),
    ("ar", "العربية", "arabe", "rtl"),
)

DOSSIER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "langues")

_courante = LANGUE_SOURCE
_catalogue: Dict[str, str] = {}
_chargees: Dict[str, Dict[str, str]] = {}
_metas: Dict[str, Dict[str, str]] = {}
#  Tout ce qui a été demandé sans traduction : sert au rapport de couverture.
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
        chemin = chemin_catalogue(code)
        try:
            with open(chemin, encoding="utf-8") as f:
                brut = json.load(f)
            info = dict(brut.get("_langue") or {})
            #  Une traduction vide retombe sur le français : elle ne doit
            #  jamais afficher une étiquette blanche.
            table = {str(k): str(v) for k, v in brut.items()
                     if not k.startswith("_") and isinstance(v, str) and v.strip()}
        except FileNotFoundError:
            log.warning("Catalogue de traduction absent : %s — "
                        "l'interface restera en français.", chemin)
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
    for c, nom, nom_fr, direction in LIVREES:
        if c == code:
            info.setdefault("nom", nom)
            info.setdefault("nom_fr", nom_fr)
            info.setdefault("direction", direction)
    info.setdefault("nom", code)
    info.setdefault("nom_fr", code)
    info.setdefault("direction", "ltr")
    return info


def codes_presents() -> List[str]:
    """Les langues réellement disponibles : le français, plus les catalogues.

    L'ordre est celui de :data:`LIVREES` pour ce qui est connu, alphabétique
    pour ce qui a été ajouté ensuite — une langue déposée par l'utilisateur
    n'est pas reléguée, elle est simplement rangée après celles d'origine.
    """
    trouves = set()
    try:
        for nom in os.listdir(DOSSIER):
            if nom.endswith(".json") and not nom.startswith("_"):
                trouves.add(nom[:-5].lower())
    except OSError:
        pass
    ordre = [c for c, _, _, _ in LIVREES if c == LANGUE_SOURCE or c in trouves]
    ordre += sorted(c for c in trouves
                    if c not in {x for x, _, _, _ in LIVREES})
    return ordre


def langues_disponibles() -> List[tuple]:
    """(code, nom local, nom français, entrées traduites, direction)."""
    out = []
    for code in codes_presents():
        info = meta(code)
        n = -1 if code == LANGUE_SOURCE else len(catalogue(code))
        out.append((code, info["nom"], info["nom_fr"], n, info["direction"]))
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


def t(texte: str) -> str:
    """Le libellé dans la langue courante, ou le français s'il manque.

    C'est volontairement une fonction triviale : elle est appelée des centaines
    de fois à la construction de l'interface, et tout ce qui coûte doit rester
    dans le chargement, pas ici.
    """
    if _courante == LANGUE_SOURCE or not texte:
        return texte
    traduit = _catalogue.get(texte)
    if traduit is None:
        _absentes.setdefault(_courante, set()).add(texte)
        return texte
    return traduit


def manquantes(code: Optional[str] = None) -> List[str]:
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


def ecrire_modele(chemin: str, cles: List[str], code: str = "",
                  garder: bool = True) -> int:
    """Écrit un catalogue à compléter : toutes les clés, valeurs vides.

    Si un catalogue existe déjà pour ``code``, ses traductions sont conservées
    et seules les clés nouvelles arrivent vides — c'est ce qui permet de
    maintenir une traduction au fil des versions sans tout relire.
    """
    existant = catalogue(code) if (code and garder) else {}
    info = meta(code) if code else {"nom": "", "nom_fr": "", "direction": "ltr"}
    sortie: Dict[str, object] = {"_langue": {
        "nom": info.get("nom", ""), "nom_fr": info.get("nom_fr", ""),
        "direction": info.get("direction", "ltr"),
        "auteur": info.get("auteur", ""),
    }}
    for cle in cles:
        sortie[cle] = existant.get(cle, "")
    os.makedirs(os.path.dirname(os.path.abspath(chemin)), exist_ok=True)
    with open(chemin, "w", encoding="utf-8") as f:
        json.dump(sortie, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return sum(1 for c in cles if not existant.get(c))


# ---------------------------------------------------------------------------
#  Inventaire des libellés — la source unique de vérité
# ---------------------------------------------------------------------------
def collecter_cles() -> List[str]:
    """Tous les libellés traduisibles du logiciel, dans l'ordre de rencontre.

    Deux gisements, parce que l'interface en a deux :

    * les appels ``t("…")`` du code, trouvés par **analyse syntaxique** — jamais
      par expression régulière, qui se tromperait sur les chaînes réparties sur
      plusieurs lignes ;
    * les **tables de données** — instruments, gammes, profils, descripteurs,
      grammaires, textes de l'aide — dont le contenu est traduit au moment de
      l'affichage, et qu'il serait absurde de recopier ici.

    Utilisé par l'outil ``tools/i18n.py`` et par le bouton « Écrire un modèle de
    traduction » des réglages : les deux voient exactement la même liste.
    """
    import ast

    racine = os.path.dirname(os.path.abspath(__file__))
    vues, cles = set(), []

    def ajouter(texte):
        texte = str(texte or "")
        if texte and texte not in vues:
            vues.add(texte)
            cles.append(texte)

    class _Collecteur(ast.NodeVisitor):
        def visit_Call(self, node):
            nom = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if nom == "t" and node.args:
                a = node.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    ajouter(a.value)
            self.generic_visit(node)

    for dossier, _, fichiers in os.walk(racine):
        if "__pycache__" in dossier:
            continue
        for nom in sorted(fichiers):
            if not nom.endswith(".py"):
                continue
            chemin = os.path.join(dossier, nom)
            try:
                _Collecteur().visit(ast.parse(open(chemin, encoding="utf-8").read()))
            except (OSError, SyntaxError) as exc:       # pragma: no cover
                log.warning("Inventaire : %s illisible (%s)", chemin, exc)

    #  Les tables de données. Importées tardivement : ce module est chargé très
    #  tôt, et rien de tout cela n'est nécessaire pour traduire.
    try:
        from .core.fingerprint import DESCRIPTEURS as EMPREINTE, SEUILS
        from .core.features import DESCRIPTEURS
        from .core.quantities import inventaire as GRANDEURS
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

    for cle, libelle in instrument_list():
        ajouter(libelle)
        try:
            ajouter(_instr(cle).description)
        except Exception:                               # noqa: BLE001
            pass
    for _, libelle in scale_names():
        ajouter(libelle)
    for _, libelle in profile_list():
        ajouter(libelle)
    for valeur in FENETRES.values():
        ajouter(valeur)
    for triplet in DESCRIPTEURS.values():
        for x in triplet:
            ajouter(x)
    for g in GRAMMAIRES.values():
        ajouter(g["titre"])
        ajouter(g["description"])
    for titre, lignes in RACCOURCIS:
        ajouter(titre)
        for _, role in lignes:
            ajouter(role)
    for nom, texte in ONGLETS:
        ajouter(nom)
        ajouter(texte)
    for _, titre, texte in DEMARRAGE:
        ajouter(titre)
        ajouter(texte)
    for valeur in SOURCES.values():
        ajouter(valeur)
    for valeur in NIVEAUX_FR.values():
        ajouter(valeur)
    ajouter(AVERTISSEMENT)
    #  Les descripteurs de l'empreinte et les phrases de qualification : ils
    #  sont traduits à l'affichage, comme les autres tables de données.
    for _cle, libelle, _unite, _poids, _log in EMPREINTE:
        ajouter(libelle)
    for _borne, phrase in SEUILS:
        ajouter(phrase)
    #  Les grandeurs scientifiques du multimètre : récoltées en faisant
    #  tourner le calcul, jamais recopiées — une grandeur ajoutée sans
    #  traduction doit faire échouer la couverture.
    for phrase in GRANDEURS():
        ajouter(phrase)
    #  Le nom français de chaque langue, affiché dans la liste des réglages.
    for _, _, nom_fr, _ in LIVREES:
        ajouter(nom_fr)
    return cles
