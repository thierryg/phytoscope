#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/run.py
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

"""Lanceur : `./run.py` ou `python3 run.py` depuis ce répertoire.

Avant toute chose, ce fichier s'assure d'être exécuté par un interpréteur
**utilisable**, et se relance avec un autre si ce n'est pas le cas. C'est la
première chose qu'il fait, et il n'importe rien du projet avant de l'avoir
fait — sans quoi l'import échouerait justement à cause du mauvais
interpréteur.
"""
import os
import sys

# ---------------------------------------------------------------------------
#  Choisir l'interpréteur avant d'importer quoi que ce soit
# ---------------------------------------------------------------------------
#  Le shebang dit « python3 », et `env` prend le premier du PATH. Sur une
#  machine où Homebrew est installé, c'est le sien : un interpréteur posé sous
#  /home/linuxbrew (ou /opt/homebrew) avec son propre chargeur dynamique, qui
#  ne lit pas le chemin de recherche de la distribution. Les roues de Qt,
#  pyqtgraph et sounddevice s'installent bien dedans, puis échouent à
#  l'exécution sur `libGL.so.1` ou `libportaudio.so.2` — des bibliothèques
#  pourtant présentes, mais que cet interpréteur n'atteint pas.
#
#  Le diagnostic le dit désormais clairement (`core/preflight.py`), mais dire
#  n'est pas réparer : on se relance donc avec un interpréteur convenable.
#  Même raisonnement pour Nix et conda, qui ont le même isolement.

ICI = os.path.dirname(os.path.abspath(__file__))

#  Préfixes d'interpréteurs à ne jamais utiliser, et pourquoi.
PREFIXES_ECARTES = (
    ("/home/linuxbrew", "Homebrew"),
    ("/opt/homebrew", "Homebrew"),
    ("/usr/local/Cellar", "Homebrew"),
    ("/nix/store", "Nix"),
    ("/opt/conda", "conda"),
    ("/opt/miniconda", "conda"),
    ("/opt/anaconda", "conda"),
)

#  Le jeton qui empêche la boucle : si le second interpréteur ne convient pas
#  non plus, on continue avec lui plutôt que de se relancer indéfiniment.
JETON = "PHYTOSCOPE_INTERPRETEUR_CHOISI"

#  La trace laissée au bilan de démarrage : « origine|écarté|retenu ».
#  Elle remplace ce que ce fichier écrivait autrefois sur la sortie d'erreur.
TRACE = "PHYTOSCOPE_INTERPRETEUR_ECARTE"


def _origine_ecartee(executable: str, courant: bool = False) -> str:
    """Nom de la distribution à écarter, ou "" si l'interpréteur convient.

    `courant` vaut True pour juger l'interpréteur qui nous exécute. On
    consulte alors `sys._base_executable`, qui désigne l'interpréteur SOUS
    l'environnement virtuel : un venv bâti sur le Python de Homebrew en
    hérite le défaut, et son propre chemin ne le dirait pas.

    Il ne faut PAS le consulter pour juger un candidat : cet attribut décrit
    notre interpréteur, pas le sien, et tous les candidats seraient écartés.
    """
    chemins = [os.path.realpath(executable or "")]
    if courant:
        base = getattr(sys, "_base_executable", None)
        if base:
            chemins.append(os.path.realpath(base))
    for chemin in chemins:
        for prefixe, origine in PREFIXES_ECARTES:
            if chemin.startswith(prefixe):
                return origine
        conda = os.environ.get("CONDA_PREFIX")
        if courant and conda and chemin.startswith(conda):
            return "conda"
    return ""


def _candidats():
    """Interpréteurs de rechange, du plus souhaitable au moins souhaitable."""
    #  L'environnement du projet d'abord : c'est lui qui porte les versions
    #  avec lesquelles le logiciel est testé.
    yield os.path.join(ICI, ".venv", "bin", "python")
    yield os.path.join(ICI, ".venv", "Scripts", "python.exe")
    #  Puis celui de la distribution, jamais celui du PATH — le PATH est
    #  précisément ce qui nous a menés ici.
    for nom in ("python3", "python3.13", "python3.12", "python3.11",
                "python3.10", "python3.9"):
        yield os.path.join("/usr/bin", nom)
        yield os.path.join("/bin", nom)


def _convient(chemin: str) -> bool:
    """L'interpréteur existe, il est assez récent, et il n'est pas écarté."""
    if not chemin or not os.path.isfile(chemin) or not os.access(chemin, os.X_OK):
        return False
    if _origine_ecartee(chemin):
        return False
    import subprocess
    try:
        r = subprocess.run(
            [chemin, "-c", "import sys; print(sys.version_info[:2] >= (3, 9))"],
            capture_output=True, text=True, timeout=15)
    except Exception:                                  # noqa: BLE001
        return False
    return r.returncode == 0 and r.stdout.strip() == "True"


def _se_relancer_si_besoin() -> None:
    """Réexécute ce script avec un interpréteur convenable, une seule fois."""
    if os.environ.get(JETON):
        return                          # déjà relancé : on ne boucle pas
    origine = _origine_ecartee(sys.executable, courant=True)
    if not origine:
        return                          # l'interpréteur courant convient

    for candidat in _candidats():
        if not _convient(candidat):
            continue
        #  Rien n'est écrit ici. Un lanceur qui explique sa plomberie avant
        #  même que le logiciel ne démarre encombre chaque lancement d'un
        #  pavé que personne ne relit. L'information est utile — elle est
        #  donc transmise au bilan de démarrage, qui est fait pour ça, et
        #  au journal. Voir `core/preflight.py`, `INTERPRETEUR_ECARTE`.
        os.environ[JETON] = candidat
        os.environ[TRACE] = f"{origine}|{sys.executable}|{candidat}"
        try:
            os.execv(candidat, [candidat, os.path.abspath(__file__)] + sys.argv[1:])
        except OSError as exc:
            os.environ[TRACE] = f"{origine}|{sys.executable}|échec : {exc}"
            break

    #  Aucun interpréteur de rechange : on continue avec celui-ci plutôt que
    #  de refuser de démarrer — le mode sans interface fonctionnera
    #  peut-être. Le bilan dira ce qui manque, et pourquoi.
    os.environ.setdefault(TRACE, f"{origine}|{sys.executable}|")


_se_relancer_si_besoin()

sys.path.insert(0, ICI)

from phytoscope.__main__ import main            # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
