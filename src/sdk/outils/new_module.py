#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/sdk/outils/new_module.py
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

"""Crée un module PhytoScope : le dossier, le squelette et les essais.

L'intérêt d'un tel outil n'est pas de taper moins. C'est que **le squelette
produit est déjà correct** : le manifeste est valide, les essais passent, et
les pièges décrits dans le manuel sont déjà évités. On part d'un module qui
fonctionne, et l'on remplace ce qu'on veut — plutôt que de partir d'une page
blanche et de découvrir les règles une par une, en les enfreignant.

.. code-block:: console

    python3 src/sdk/outils/new_module.py mon-module
    python3 src/sdk/outils/new_module.py mon-module --capacite descripteur
    python3 src/sdk/outils/new_module.py mon-module --installer

`--installer` le dépose directement dans le dossier des modules de votre
installation, prêt à l'essai au prochain démarrage.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Optional

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
LOGICIEL = os.path.join(RACINE, "software", "phytoscope")

#  Les capacités et ce qu'il faut écrire pour chacune. Le texte vient d'ici et
#  non du contrat : l'outil doit fonctionner même si le logiciel n'est pas
#  installé — on écrit un module avant de l'essayer.
CAPACITES: Dict[str, Dict[str, str]] = {
    "analyseur": {
        "classe": "Analyseur",
        "resume": "calcule des grandeurs sur une fenêtre de signal",
        "corps": '''    #  Combien de secondes de signal vous voulez, et si vous le voulez BRUT
    #  — avant réjecteur et passe-bas. Le brut pour toute mesure de bruit :
    #  filtrer avant de mesurer le bruit revient à mesurer son propre filtre.
    FENETRE_S = 60.0
    SIGNAL_BRUT = False

    def analyser(self, x: np.ndarray, fs: float,
                 contexte: Contexte) -> List[Grandeur]:
        """Rend les grandeurs à afficher. Une liste vide est acceptable.

        :param x: le signal, **en volts**, dans l'ordre chronologique.
        :param fs: la cadence réelle d'échantillonnage, en hertz.
        """
        if x.size < 64:
            return []

        return [Grandeur(
            cle="amplitude-crete",
            libelle="Amplitude crête",
            valeur=float(np.max(np.abs(x - x.mean()))),
            texte=f"{np.max(np.abs(x - x.mean())) * 1e6:.1f} µV",
            #  `sens` n'est pas décoratif : dites ce que ce nombre signifie ET
            #  ce qu'il ne permet pas de conclure. Sans cela, l'interface
            #  écrira « le module n'explique pas cette valeur ».
            sens=("L'écart maximal à la moyenne sur la fenêtre. Sensible à un "
                  "seul artefact : une porte qui claque suffit à la faire "
                  "tripler."),
        )]
''',
    },
    "descripteur": {
        "classe": "Descripteur",
        "resume": "produit une représentation du signal — une courbe",
        "corps": '''    FENETRE_S = 60.0
    SIGNAL_BRUT = False

    def decrire(self, x: np.ndarray, fs: float,
                contexte: Contexte) -> List[Trace]:
        """Rend les courbes à afficher. Une liste vide est acceptable."""
        if x.size < 64:
            return []

        t = np.arange(x.size) / fs
        return [Trace(
            x=t, y=x * 1e6,
            titre=contexte.traduire("Ma représentation"),
            x_libelle=contexte.traduire("temps (s)"),
            y_libelle="µV",
            #  Ce que votre représentation suppose, et ce qu'elle ne permet
            #  pas de conclure. Affiché sous la courbe.
            avertissement=contexte.traduire(
                "Dites ici ce que cette représentation suppose."),
        )]
''',
    },
    "sonificateur": {
        "classe": "Sonificateur",
        "resume": "transforme une valeur mesurée en notes",
        "corps": '''    def sonifier(self, valeur_v: float,
                 contexte: Contexte) -> List[NoteProposee]:
        """Rend les notes proposées. **Soyez rapide** : appelé dans la boucle
        de rendu musical. Une liste vide signifie « pas de note », ce qui est
        une réponse légitime.
        """
        #  Un exemple volontairement simple : plus la tension est forte, plus
        #  la note est haute. Une gamme diatonique, pour que ce soit écoutable.
        gamme = (0, 2, 4, 5, 7, 9, 11)
        rang = int(abs(valeur_v) * 1e6) % len(gamme)
        return [NoteProposee(
            hauteur_midi=60 + gamme[rang],
            velocite=70,
            duree_s=0.4,
            #  La valeur qui a produit la note : conservée dans le rendu, pour
            #  qu'on puisse toujours remonter de la note à la mesure.
            origine_v=valeur_v,
        )]
''',
    },
    "exportateur": {
        "classe": "Exportateur",
        "resume": "écrit une séance dans un autre format",
        "corps": '''    #  Ce qui s'affiche dans la liste des formats, et l'extension produite.
    FORMAT = "Mon format"
    EXTENSION = ".txt"

    def exporter(self, seance: str, cible: str, contexte: Contexte) -> bool:
        """Écrit la séance `seance` dans le fichier `cible`.

        Rend vrai si l'écriture a réussi. N'écrivez QUE dans `cible` : le
        dossier de la séance ne vous appartient pas.
        """
        source = os.path.join(seance, "mesures.csv")
        if not os.path.exists(source):
            contexte.journal(f"« {source} » introuvable", "warning")
            return False
        with open(source, encoding="utf-8") as entree, \\
             open(cible, "w", encoding="utf-8") as sortie:
            for ligne in entree:
                sortie.write(ligne)
        return True
''',
    },
}

GABARIT = '''# -*- coding: utf-8 -*-
"""{titre} — {resume}.

Écrivez ici ce que fait ce module, et surtout **ce qu'il ne fait pas**. Le
logiciel tient à ce que toute représentation dise ce qu'elle suppose et ce
qu'elle ne permet pas de conclure ; cela commence par la documentation.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import numpy as np

#  Tout ce dont un module a besoin vient d'ici, et de nulle part ailleurs.
#  Ce qui n'est pas dans `phytoscope.api` peut changer sans préavis.
from phytoscope.api import ({imports})


class {classe_python}(Module, {classe_capacite}):
    """{titre}."""

    MANIFESTE = Manifeste(
        nom="{nom}",
        titre="{titre}",
        version="0.1.0",
        api="{api}",
        description="{resume}.",
        auteur="{auteur}",
        licence="MIT",
        capacites=(Capacite.{capacite_majuscule},),
        #  Les bibliothèques nécessaires. Le logiciel vérifie AVANT d'importer
        #  et affiche « module désactivé : scipy absent » plutôt qu'une trace.
        # exige=("scipy",),
    )

    # ── Se préparer ──────────────────────────────────────────────────────────
    def installer(self) -> None:
        """Appelé une fois, après le chargement de tous les modules.

        C'est ici qu'on s'abonne et qu'on prépare ses fichiers — **pas** dans
        `__init__`, qui est appelé pour tous les modules au démarrage et doit
        rester instantané.
        """
        self.contexte.journal("{nom} installé")

    def arreter(self) -> None:
        """Appelé une fois à la fermeture. Fermer ce qu'on a ouvert.

        Les abonnements sont retirés par l'hôte : inutile de s'en occuper.
        """

    def reglages_par_defaut(self) -> Dict[str, Any]:
        """Vos réglages et leurs valeurs initiales.

        Le logiciel les conserve sous le nom de votre module et vous les rend
        par `contexte.reglages`. N'écrivez jamais dans les réglages du
        logiciel.
        """
        return {{}}

    # ── Travailler ───────────────────────────────────────────────────────────
{corps}'''

GABARIT_ESSAIS = '''# -*- coding: utf-8 -*-
"""Essais de « {nom} » — sans logiciel lancé, sans matériel.

    python3 -m pytest {chemin_essais} -v
"""
from __future__ import annotations

import importlib.util
import os
import sys
from typing import Any, Dict, List

import numpy as np
import pytest


class ContexteDEssai:
    """Un faux contexte : la même surface, sans rien derrière."""

    def __init__(self, reglages: Dict[str, Any] | None = None) -> None:
        self.reglages: Dict[str, Any] = dict(reglages or {{}})
        self.abonnements: Dict[str, List] = {{}}
        self.journal_ecrit: List[str] = []
        self.frequence_hz = 250.0
        self.pleine_echelle_v = 2.5
        self.reseau_hz = 50.0

    def abonner(self, evenement, rappel):
        self.abonnements.setdefault(evenement, []).append(rappel)

    def journal(self, message, niveau="info"):
        self.journal_ecrit.append(f"{{niveau}}: {{message}}")

    def message(self, texte):
        self.journal_ecrit.append(f"message: {{texte}}")

    def traduire(self, texte):
        return texte

    def dossier(self):
        import tempfile
        return tempfile.mkdtemp(prefix="essai-{nom}-")

    def signal(self, secondes=60.0, brut=False):
        return signal_dessai(secondes)

    def instants_evenements(self):
        return []

    def etat(self):
        from types import SimpleNamespace
        return SimpleNamespace(duree_s=120.0, source="essai", en_marche=True,
                               relecture=False)


def signal_dessai(secondes=30.0, fs=250.0):
    """Un signal plausible : du bruit, une dérive, quelques bouffées."""
    n = int(secondes * fs)
    t = np.arange(n) / fs
    r = np.random.default_rng(42)
    x = r.normal(0.0, 3e-6, n)
    x += 4e-5 * np.sin(2 * np.pi * t / 400.0)
    for t0 in np.arange(5.0, secondes, 7.0):
        x += 1.2e-4 * np.exp(-((t - t0) / 1.5) ** 2)
    return x


@pytest.fixture()
def instance():
    from phytoscope.api import Module
    ici = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location(
        "{nom_interne}", os.path.join(ici, "module.py"))
    paquet = importlib.util.module_from_spec(spec)
    #  Inscrit AVANT l'exécution : `@dataclass` va chercher
    #  `sys.modules[cls.__module__]` et échouerait sinon. Le nom est propre à
    #  ce module, pour que deux modules cohabitent dans la même session.
    sys.modules["{nom_interne}"] = paquet
    spec.loader.exec_module(paquet)
    classe = next(o for o in vars(paquet).values()
                  if isinstance(o, type) and issubclass(o, Module)
                  and o is not Module)
    contexte = ContexteDEssai(
        reglages=classe(ContexteDEssai()).reglages_par_defaut())
    obj = classe(contexte)
    obj.installer()
    return obj


def test_le_manifeste_est_valide(instance):
    """Un manifeste refusé, et le module n'est jamais chargé."""
    assert instance.MANIFESTE.defauts() == [], instance.MANIFESTE.defauts()


def test_le_manifeste_vise_une_api_connue(instance):
    from phytoscope.api import compatible
    assert compatible(instance.MANIFESTE.api)


{essai_capacite}

def test_arreter_ne_leve_pas(instance):
    instance.arreter()
'''

ESSAIS_PAR_CAPACITE = {
    "analyseur": '''def test_analyser_rend_des_grandeurs_completes(instance):
    """Chaque grandeur doit dire ce qu'elle signifie."""
    grandeurs = instance.analyser(signal_dessai(30.0), 250.0, instance.contexte)
    assert grandeurs, "le module n'a rien rendu sur un signal valide"
    for g in grandeurs:
        assert g.cle and g.libelle
        assert g.texte
        assert len(g.sens) > 20, (
            f"« {g.cle} » n'explique pas ce qu'elle signifie")
        assert np.isfinite(g.valeur)


def test_un_signal_vide_ne_fait_pas_lever(instance):
    """« Rien à dire » se dit par une liste vide, jamais par une exception."""
    assert instance.analyser(np.zeros(0), 250.0, instance.contexte) == []
''',
    "descripteur": '''def test_decrire_rend_des_traces_coherentes(instance):
    traces = instance.decrire(signal_dessai(30.0), 250.0, instance.contexte)
    assert traces, "le module n'a rendu aucune trace"
    for tr in traces:
        assert tr.x.size == tr.y.size
        assert tr.titre
        assert tr.avertissement, (
            "dites ce que cette représentation ne permet pas de conclure")


def test_un_signal_vide_ne_fait_pas_lever(instance):
    assert instance.decrire(np.zeros(0), 250.0, instance.contexte) == []
''',
    "sonificateur": '''def test_sonifier_rend_des_notes_jouables(instance):
    notes = instance.sonifier(1.2e-4, instance.contexte)
    for n in notes:
        assert 0 <= n.hauteur_midi <= 127, "hauteur MIDI hors bornes"
        assert 0 <= n.velocite <= 127
        assert n.duree_s > 0
        assert n.origine_v != 0.0 or True   # la mesure d'origine est conservée


def test_une_valeur_nulle_ne_fait_pas_lever(instance):
    instance.sonifier(0.0, instance.contexte)
''',
    "exportateur": '''def test_exporter_ecrit_le_fichier(instance, tmp_path):
    seance = tmp_path / "seance"
    seance.mkdir()
    (seance / "mesures.csv").write_text("t;v\\n0;1e-6\\n", encoding="utf-8")
    cible = tmp_path / ("sortie" + instance.EXTENSION)
    assert instance.exporter(str(seance), str(cible), instance.contexte)
    assert cible.exists() and cible.stat().st_size > 0


def test_une_seance_absente_rend_faux_sans_lever(instance, tmp_path):
    cible = tmp_path / ("sortie" + instance.EXTENSION)
    assert instance.exporter(str(tmp_path / "rien"), str(cible),
                             instance.contexte) is False
''',
}


def dossier_des_modules() -> str:
    """Le dossier des modules de l'installation, selon le système."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "PhytoScope", "modules")
    if sys.platform == "darwin":
        return os.path.expanduser(
            "~/Library/Application Support/PhytoScope/modules")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "phytoscope", "modules")


def version_api() -> str:
    """La version d'API du logiciel s'il est là, sinon une valeur sûre."""
    chemin = os.path.join(LOGICIEL, "phytoscope", "api", "contract.py")
    try:
        with open(chemin, encoding="utf-8") as f:
            m = re.search(r'^VERSION_API\s*=\s*"([^"]+)"', f.read(), re.M)
        if m:
            return m.group(1)
    except OSError:
        pass
    return "1.0"


def classe_python(nom: str) -> str:
    """« mon-module » → « MonModule »."""
    return "".join(p.capitalize() for p in re.split(r"[-_]", nom) if p)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        prog="new_module.py",
        description="Crée un module PhytoScope, prêt à essayer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Capacités : " + " · ".join(
            f"{c} ({d['resume']})" for c, d in CAPACITES.items()))
    p.add_argument("nom", help="l'identifiant du module : a-z, 0-9 et tirets")
    p.add_argument("--capacite", default="analyseur", choices=sorted(CAPACITES),
                   help="ce que le module fournit (défaut : analyseur)")
    p.add_argument("--titre", default="", help="ce que l'utilisateur lira")
    p.add_argument("--auteur", default="Votre nom")
    p.add_argument("--dans", default="", metavar="DOSSIER",
                   help="où créer le module (défaut : le dossier courant)")
    p.add_argument("--installer", action="store_true",
                   help="créer directement dans le dossier des modules de "
                        "votre installation")
    args = p.parse_args(argv)

    if not re.match(r"^[a-z][a-z0-9-]{1,48}$", args.nom):
        print(f"✗ « {args.nom} » n'est pas un nom valide : lettres minuscules, "
              "chiffres et tirets, 2 à 49 caractères, commençant par une "
              "lettre.", file=sys.stderr)
        return 2

    base = (dossier_des_modules() if args.installer
            else (args.dans or os.getcwd()))
    cible = os.path.join(base, args.nom)
    if os.path.exists(cible):
        print(f"✗ « {cible} » existe déjà.", file=sys.stderr)
        return 1
    os.makedirs(cible, exist_ok=True)

    capacite = CAPACITES[args.capacite]
    titre = args.titre or args.nom.replace("-", " ").capitalize()

    #  Les imports : seulement ce que le squelette emploie réellement. Un
    #  import inutilisé dans un exemple est une invitation à en ajouter
    #  d'autres sans y penser.
    besoins = ["Capacite", "Contexte", "Manifeste", "Module",
               capacite["classe"]]
    besoins += {"analyseur": ["Grandeur"], "descripteur": ["Trace"],
                "sonificateur": ["NoteProposee"],
                "exportateur": []}[args.capacite]
    imports = ", ".join(sorted(set(besoins)))
    if len(imports) > 62:
        imports = ",\n                            ".join(sorted(set(besoins)))

    with open(os.path.join(cible, "module.py"), "w", encoding="utf-8") as f:
        f.write(GABARIT.format(
            titre=titre, resume=capacite["resume"], imports=imports,
            classe_python=classe_python(args.nom),
            classe_capacite=capacite["classe"], nom=args.nom,
            api=version_api(), auteur=args.auteur,
            capacite_majuscule=args.capacite.upper(), corps=capacite["corps"]))

    #  « test_<nom>.py » et non « test_module.py » : deux fichiers d'essai de
    #  même nom, dans deux dossiers sans `__init__.py`, ne peuvent pas être
    #  collectés dans la même session pytest. Un module qu'on ne peut pas
    #  éprouver en même temps que les autres est un module qu'on éprouvera
    #  moins.
    nom_essais = "test_" + args.nom.replace("-", "_") + ".py"
    with open(os.path.join(cible, nom_essais), "w", encoding="utf-8") as f:
        f.write(GABARIT_ESSAIS.format(
            nom=args.nom,
            nom_interne="module_" + args.nom.replace("-", "_"),
            chemin_essais=os.path.join(args.nom, nom_essais),
            essai_capacite=ESSAIS_PAR_CAPACITE[args.capacite]))

    with open(os.path.join(cible, "README.md"), "w", encoding="utf-8") as f:
        f.write(f"""# {titre}

{capacite['resume'].capitalize()}.

## Essayer

```bash
python3 -m pytest {args.nom}/{nom_essais} -v
```

Les essais n'ont besoin ni du logiciel lancé, ni de matériel.

## Installer

```bash
cp -r {args.nom} "{dossier_des_modules()}"
```

Puis relancez PhytoScope. L'onglet Diagnostic montre le module et, s'il a été
refusé, dit pourquoi en une phrase.

## À faire

- [ ] écrire ce que ce module fait, et ce qu'il ne fait pas
- [ ] renseigner `sens` pour chaque valeur produite
- [ ] remplacer l'auteur et la licence du manifeste
- [ ] ajouter vos essais
""")

    dossier = dossier_des_modules()
    print()
    print(f"  ✓ Module « {args.nom} » créé dans {cible}")
    print()
    print(f"      module.py        le squelette, avec {args.capacite}")
    print("      {nom_essais}   des essais qui passent déjà")
    print("      README.md")
    print()
    print("  Éprouvez-le :")
    print(f"      python3 -m pytest {os.path.join(cible, nom_essais)} -v")
    print()
    if args.installer:
        print("  Il est déjà en place : relancez PhytoScope.")
    else:
        print("  Puis installez-le :")
        print(f"      cp -r {cible} '{dossier}'")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
