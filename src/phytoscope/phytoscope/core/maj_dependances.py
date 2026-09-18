#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/maj_dependances.py
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

"""Les bibliothèques Python sont-elles à jour ?

Ce module répond à une question simple — « existe-t-il une version plus
récente de NumPy, de PySide6, de pyserial ? » — et il la pose à PyPI, source
d'autorité pour les paquets Python.

Ce qu'il ne fait pas, et pourquoi
---------------------------------

**Il n'installe rien.** Mettre à jour PySide6 sous les pieds d'une séance
d'enregistrement en cours serait une mauvaise surprise ; et une mise à jour
majeure peut casser la portabilité que `.ai/portabilite.md` tient à jour.
L'installation reste une décision explicite, prise dans la fenêtre, et
confiée à `preflight.installer()` — qui sait déjà choisir entre l'environnement
virtuel, `--user` et le gestionnaire du système.

**Il n'ajoute aucune dépendance** (`C-40`). Interroger PyPI se fait avec
`urllib` de la bibliothèque standard, et comparer deux numéros de version avec
une fonction écrite ici. Tirer `requests` et `packaging` pour cela coûterait
plus qu'il ne rapporte.

**Il ne bloque jamais.** Sans réseau, avec un miroir lent ou derrière un
mandataire qui filtre, la vérification échoue proprement et le dit. Le
logiciel fonctionne sans elle : ce n'est pas un contrôle avant vol, c'est un
renseignement.

**Il ne décide pas à votre place de ce qui est « urgent ».** Il classe les
écarts — correctif, mineur, majeur — et laisse lire. Un écart majeur n'est
pas un défaut : c'est un changement d'interface, qui demande justement qu'on
y regarde.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .logging_setup import get_logger

log = get_logger(__name__)

#  L'adresse officielle de l'index. Paramétrable : une machine derrière un
#  miroir d'entreprise (devpi, Artifactory) doit pouvoir l'interroger, et
#  c'est le même format de réponse.
PYPI_JSON = "https://pypi.org/pypi/{distribution}/json"

#  Court exprès. Cette vérification est un agrément, pas un prérequis : mieux
#  vaut renoncer au bout de quelques secondes que faire attendre.
DELAI_PAR_DEFAUT = 6.0

#  `_normaliser` sert à comparer les noms : PyPI ne distingue ni la casse ni
#  les séparateurs — « python-rtmidi », « python_rtmidi » et « Python.RTMidi »
#  désignent la même distribution (PEP 503).
_SEPARATEURS = re.compile(r"[-_.]+")

#  Une ligne de requirements : nom, extras facultatifs, puis les contraintes.
_EXIGENCE = re.compile(
    r"^\s*(?P<nom>[A-Za-z0-9][A-Za-z0-9._-]*)"
    r"(?:\[(?P<extras>[^\]]*)\])?"
    r"(?P<contraintes>.*)$")


def _normaliser(nom: str) -> str:
    return _SEPARATEURS.sub("-", nom.strip()).lower()


# ---------------------------------------------------------------------------
#  Comparaison de versions
# ---------------------------------------------------------------------------
#  Assez de PEP 440 pour ce que nous avons à faire, et pas plus. Les versions
#  que nous rencontrons sont de la forme « 2.2.6 », « 6.11.2 », « 1.5.8 »,
#  parfois « 2.0.0rc1 » ou « 1.26.0.post1 ». On extrait la suite de nombres,
#  et l'on retient si un suffixe de pré-diffusion suit — une « 3.0.0rc1 » est
#  ANTÉRIEURE à la « 3.0.0 », et la proposer serait une régression.
#  Les suffixes qui ORDONNENT une version, et leur rang relatif.
#
#    alpha < beta < rc < (rien) < post
#
#  Le rang « (rien) » vaut 1 : une pré-diffusion se compare donc AVANT la
#  version qu'elle annonce, et une post-diffusion APRÈS. Le sous-rang
#  distingue les pré-diffusions entre elles, et le numéro final les ordonne
#  (« rc2 » après « rc1 »). PEP 440 en dit davantage ; ceci en couvre ce que
#  nos dépendances publient réellement.
_SUFFIXES = (
    ("alpha", 0, 0), ("a", 0, 0),
    ("beta", 0, 1), ("b", 0, 1),
    ("rc", 0, 2), ("c", 0, 2), ("pre", 0, 2), ("preview", 0, 2),
    ("dev", 0, -1),          # une version de développement précède tout
    ("post", 2, 0), ("rev", 2, 0), ("r", 2, 0),
)

_NOMBRES = re.compile(r"^\s*v?(?P<nombres>\d+(?:\.\d+)*)(?P<suite>.*)$")


def decouper_version(v: str) -> Tuple[Tuple[int, ...], int, int, int]:
    """Rend une clé comparable : (nombres, rang, sous_rang, numéro).

    Attention au piège que ceci referme : ramasser tous les nombres de
    « 3.0.0rc1 » donne (3, 0, 0, 1), qui se compare APRÈS (3, 0, 0) — et
    « 3.0.0rc1 » passait ainsi pour plus récent que « 3.0.0 ». On coupe donc
    la chaîne au premier caractère qui n'est pas un composant numérique, et
    l'on interprète ce qui suit.
    """
    v = (v or "").strip().split("+")[0]        # « 1.2.3+local » → « 1.2.3 »
    m = _NOMBRES.match(v)
    if m is None:
        #  Version non numérique : on ne sait pas l'ordonner, et on le dit en
        #  la plaçant au plus bas plutôt qu'en inventant un rang.
        return (0,), 1, 0, 0
    nombres = tuple(int(x) for x in m.group("nombres").split(".")[:4])
    suite = m.group("suite").lstrip(".-_").lower()
    for nom, rang, sous_rang in _SUFFIXES:
        if suite.startswith(nom):
            chiffres = re.match(r"\d+", suite[len(nom):].lstrip(".-_"))
            return (nombres or (0,), rang, sous_rang,
                    int(chiffres.group()) if chiffres else 0)
    return nombres or (0,), 1, 0, 0


def comparer_versions(a: str, b: str) -> int:
    """-1 si a < b, 0 si égales, 1 si a > b."""
    na, *qa = decouper_version(a)
    nb, *qb = decouper_version(b)
    #  Comparer à égalité de longueur : « 2.2 » et « 2.2.0 » sont la même.
    taille = max(len(na), len(nb))
    na = na + (0,) * (taille - len(na))
    nb = nb + (0,) * (taille - len(nb))
    ca, cb = (na, *qa), (nb, *qb)
    if ca == cb:
        return 0
    return -1 if ca < cb else 1


def ampleur(installee: str, disponible: str) -> str:
    """« majeure », « mineure », « correctif » — ou "" si rien à dire.

    Le mot compte : c'est lui qui dit s'il faut relire les notes de version
    avant de mettre à jour, ou si l'on peut y aller.
    """
    if comparer_versions(installee, disponible) >= 0:
        return ""
    a = decouper_version(installee)[0]
    b = decouper_version(disponible)[0]
    a = a + (0,) * (3 - len(a)) if len(a) < 3 else a
    b = b + (0,) * (3 - len(b)) if len(b) < 3 else b
    if a[0] != b[0]:
        return "majeure"
    if a[1] != b[1]:
        return "mineure"
    return "correctif"


# ---------------------------------------------------------------------------
#  Ce que l'on sait d'une dépendance
# ---------------------------------------------------------------------------
@dataclass
class Dependance:
    """Une bibliothèque, ce qu'on en exige, ce qu'on en a, ce qui existe."""
    distribution: str                  # le nom PyPI : « python-rtmidi »
    module: str = ""                   # le nom d'import : « rtmidi »
    role: str = ""                     # à quoi elle sert, en français
    obligatoire: bool = True
    exigence: str = ""                 # « >=1.24 », tel qu'écrit
    installee: str = ""                # "" si absente
    disponible: str = ""               # "" si l'index n'a pas répondu
    erreur: str = ""                   # pourquoi l'index n'a pas répondu

    @property
    def absente(self) -> bool:
        return not self.installee

    @property
    def inconnue(self) -> bool:
        """L'index n'a rien dit : on ne sait pas, et on ne le cache pas."""
        return not self.disponible

    @property
    def ampleur(self) -> str:
        if self.absente or self.inconnue:
            return ""
        return ampleur(self.installee, self.disponible)

    @property
    def a_jour(self) -> bool:
        return bool(self.installee) and not self.inconnue and not self.ampleur

    @property
    def etat(self) -> str:
        """Un mot, pour l'affichage : le tri et les couleurs s'y appuient."""
        if self.absente:
            return "absente"
        if self.inconnue:
            return "inconnue"
        return self.ampleur or "a_jour"

    def __str__(self) -> str:                          # pragma: no cover
        return f"{self.distribution} {self.installee or '—'} → {self.disponible or '?'}"


@dataclass
class Rapport:
    """Le résultat d'une vérification complète."""
    dependances: List[Dependance] = field(default_factory=list)
    hors_ligne: bool = False
    #  Le message qui explique un échec global — pas de réseau, mandataire
    #  qui refuse, index injoignable.
    erreur: str = ""

    @property
    def a_mettre_a_jour(self) -> List[Dependance]:
        return [d for d in self.dependances if d.ampleur]

    @property
    def absentes(self) -> List[Dependance]:
        return [d for d in self.dependances if d.absente]

    @property
    def inconnues(self) -> List[Dependance]:
        return [d for d in self.dependances if d.inconnue and not d.absente]

    @property
    def resume(self) -> str:
        """Une phrase, celle qu'on lit en premier."""
        if self.erreur:
            return self.erreur
        n = len(self.a_mettre_a_jour)
        if n == 0:
            if self.inconnues:
                return (f"Aucune mise à jour trouvée ; "
                        f"{len(self.inconnues)} non vérifiée(s).")
            return "Toutes les bibliothèques sont à jour."
        majeures = sum(1 for d in self.a_mettre_a_jour if d.ampleur == "majeure")
        phrase = f"{n} mise(s) à jour disponible(s)"
        if majeures:
            phrase += f", dont {majeures} majeure(s)"
        return phrase + "."


# ---------------------------------------------------------------------------
#  Ce qui est exigé, et ce qui est installé
# ---------------------------------------------------------------------------
def lire_exigences(chemin: str) -> Dict[str, str]:
    """Les contraintes d'un fichier requirements, par distribution normalisée.

    On ignore les commentaires, les lignes vides, les options (`-r`, `--index`)
    et les marqueurs d'environnement : ce qui nous intéresse ici est le nom et
    la contrainte de version, rien d'autre.
    """
    exigences: Dict[str, str] = {}
    try:
        with open(chemin, encoding="utf-8") as f:
            lignes = f.readlines()
    except OSError as exc:
        log.info("Fichier d'exigences illisible (%s) : %s", chemin, exc)
        return exigences

    for ligne in lignes:
        ligne = ligne.split("#", 1)[0].strip()
        if not ligne or ligne.startswith("-"):
            continue
        ligne = ligne.split(";", 1)[0].strip()      # marqueur d'environnement
        m = _EXIGENCE.match(ligne)
        if not m:
            continue
        exigences[_normaliser(m.group("nom"))] = m.group("contraintes").strip()
    return exigences


def version_installee(distribution: str) -> str:
    """La version présente, ou "" si la distribution est absente."""
    try:
        from importlib.metadata import PackageNotFoundError, version
    except ImportError:                                # pragma: no cover
        return ""
    for candidat in (distribution, _SEPARATEURS.sub("_", distribution),
                     _SEPARATEURS.sub("-", distribution)):
        try:
            return version(candidat)
        except PackageNotFoundError:
            continue
        except Exception as exc:                       # noqa: BLE001
            log.info("Version de %s indéterminée : %s", distribution, exc)
            return ""
    return ""


def derniere_version(distribution: str, delai: float = DELAI_PAR_DEFAUT,
                     index: str = PYPI_JSON) -> Tuple[str, str]:
    """Interroge l'index ; rend (version, erreur).

    On lit `info.version`, qui est la dernière version **stable** publiée :
    PyPI y écarte de lui-même les pré-diffusions, ce qui est exactement ce
    qu'il faut proposer.
    """
    url = index.format(distribution=urllib.request.quote(distribution))
    requete = urllib.request.Request(
        url, headers={"Accept": "application/json",
                      #  Un agent explicite : un index d'entreprise journalise
                      #  ce qui l'interroge, et une ligne anonyme s'y lit mal.
                      "User-Agent": "PhytoScope (verification des mises a jour)"})
    try:
        with urllib.request.urlopen(requete, timeout=delai) as reponse:
            charge = json.loads(reponse.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return "", "inconnue de l'index"
        return "", f"index : HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return "", f"réseau : {exc.reason}"
    except (TimeoutError, OSError) as exc:
        return "", f"réseau : {exc}"
    except (ValueError, KeyError) as exc:
        return "", f"réponse illisible : {exc}"

    version = str((charge.get("info") or {}).get("version") or "")
    return (version, "") if version else ("", "l'index n'annonce aucune version")


# ---------------------------------------------------------------------------
#  La vérification
# ---------------------------------------------------------------------------
#  Les bibliothèques du logiciel, avec leur nom d'import et leur rôle. La
#  liste vient de `preflight.REQUIREMENTS`, seule source : la redire ici la
#  ferait diverger le jour où l'on ajoute une dépendance.
def _dependances_du_logiciel() -> List[Dependance]:
    from . import preflight
    return [
        Dependance(distribution=r.paquet, module=r.module, role=r.role,
                   obligatoire=r.obligatoire)
        for r in preflight.REQUIREMENTS
    ]


def verifier(delai: float = DELAI_PAR_DEFAUT,
             index: str = PYPI_JSON,
             racine_exigences: str = "",
             avancement: Optional[Callable[[int, int, str], None]] = None,
             arret: Optional[Callable[[], bool]] = None,
             distributions: Optional[Sequence[str]] = None) -> Rapport:
    """Compare l'installé au publié, et rend un rapport.

    `avancement(fait, total, nom)` est appelé avant chaque interrogation, ce
    qui permet à une barre de progression d'avancer et à un bouton
    « Annuler » d'avoir un sens. `arret()` est consulté au même moment : s'il
    rend True, la vérification s'arrête là et rend ce qu'elle a.
    """
    rapport = Rapport()
    dependances = _dependances_du_logiciel()

    if distributions is not None:
        voulues = {_normaliser(d) for d in distributions}
        dependances = [d for d in dependances
                       if _normaliser(d.distribution) in voulues]

    #  Les contraintes déclarées, pour dire « >=1.24 » à côté de la version.
    if racine_exigences:
        import os
        exigences: Dict[str, str] = {}
        for nom in ("requirements.txt", "requirements-optionnel.txt"):
            exigences.update(lire_exigences(os.path.join(racine_exigences, nom)))
        for d in dependances:
            d.exigence = exigences.get(_normaliser(d.distribution), "")

    total = len(dependances)
    for i, d in enumerate(dependances):
        if arret is not None and arret():
            log.info("Vérification des mises à jour interrompue.")
            break
        if avancement is not None:
            avancement(i, total, d.distribution)

        d.installee = version_installee(d.distribution)
        #  Une distribution absente n'a pas à être interrogée : ce n'est pas
        #  une mise à jour qu'il lui faut, c'est une installation, et
        #  `preflight` s'en occupe déjà.
        if d.absente:
            continue
        d.disponible, d.erreur = derniere_version(d.distribution, delai, index)

    if avancement is not None:
        avancement(total, total, "")

    #  Un échec unanime ne se dit pas dépendance par dépendance : c'est le
    #  réseau qui manque, et une seule phrase le dit mieux que huit.
    interrogees = [d for d in dependances if not d.absente]
    if interrogees and all(d.inconnue for d in interrogees):
        rapport.hors_ligne = True
        raison = next((d.erreur for d in interrogees if d.erreur), "")
        rapport.erreur = ("Index des paquets injoignable — vérification "
                          "impossible" + (f" ({raison})." if raison else "."))

    rapport.dependances = dependances
    return rapport
