# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/music/lexicon.py
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

"""Le mode vocal : des mots au lieu des notes.

Ce module remplace le moteur de correspondance musical par un moteur de
correspondance **lexical**. Là où :mod:`mapper` choisit une hauteur dans une
gamme, celui-ci choisit un mot dans un dictionnaire, puis assemble quelques mots
en un énoncé court.

==================  =======================================================
Avertissement       Ce n'est pas une traduction.
==================  =======================================================

Il faut le dire nettement, parce que le dispositif invite à croire le contraire.
La plante n'émet pas de mots, n'a pas de langage, et rien dans son signal
électrique ne correspond à un vocabulaire. Ce que fait ce module est exactement
ce que fait la sonification musicale, avec un matériau différent : il applique
des règles explicites, réglables et consignées, qui associent une **région de
l'espace des descripteurs** à un **mot choisi par l'utilisateur**.

Le mot qui sort est donc dans le dictionnaire de celui qui l'a écrit. Il dit
quelque chose du signal — son intensité, son sens de variation, son rythme, sa
couleur spectrale — et rien du tout de ce que « pense » la plante. Le dialogue
qui s'installe est un dialogue entre l'utilisateur et sa propre grille de
lecture ; il peut être fécond, à condition de savoir cela.

C'est pourquoi chaque énoncé produit est accompagné de sa **justification** :
les valeurs qui l'ont déclenché et la règle appliquée. Le fichier de séance les
conserve, de sorte qu'on puisse, six mois plus tard, refaire le chemin à
l'envers.

Organisation
------------

Le dictionnaire est fait de **registres**, chacun rattaché à un axe mesurable :

===========  ==================================  ============================
Registre     Axe du signal                       Rôle grammatical
===========  ==================================  ============================
sujet        — (fixe, choisi par l'utilisateur)  qui parle
verbe        pente de l'événement, signée        l'action
intensite    amplitude en écarts-types           l'adverbe d'intensité
tempo        temps écoulé depuis le précédent    la circonstance de temps
couleur      centre de gravité spectral          la qualification
liaison      — (fixe)                            l'articulation
===========  ==================================  ============================

Chaque registre est une liste ordonnée de mots ; la position dans la liste
correspond à une position sur l'axe, de 0 à 1. Ajouter un mot, changer de
langue, écrire un dictionnaire poétique ou un dictionnaire clinique : il suffit
d'un fichier JSON.

Un dictionnaire est livré **pour chacune des langues de l'interface**, dans
:file:`phytoscope/lexiques/`. Ce sont des points de départ, pas des références :
le chapitre de déontologie vaut ici aussi, et les mots d'un atelier ne sont
jamais tout à fait ceux d'un autre.

Les dictionnaires des langues dont l'ordre des mots n'est pas le nôtre — le
japonais, le coréen, le chinois, l'arabe — portent en plus leurs **propres
gabarits de phrase**, qui l'emportent sur ceux de la grammaire choisie. Sans
cela, « 私は かすかに ふるえる » sortirait dans l'ordre français et ne voudrait
rien dire.

Motif de conception : *Strategy* pour la grammaire (plusieurs façons d'assembler
les mots), *Value Object* pour l'énoncé produit (immuable, sérialisable).
"""
from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from ..core.dsp import Event
from ..core.logging_setup import get_logger
from ..i18n import t

log = get_logger(__name__)

__all__ = ["Enonce", "Lexique", "VocalMapper", "LEXIQUE_PAR_DEFAUT",
           "GRAMMAIRES", "CSV_HEADER_VOCAL", "DOSSIER_LEXIQUES",
           "lexiques_livres", "lexique_livre"]

#  Les dictionnaires livrés, un par langue de l'interface.
DOSSIER_LEXIQUES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lexicons")


# ---------------------------------------------------------------------------
#  Le dictionnaire livré par défaut
# ---------------------------------------------------------------------------
#  Les listes sont ordonnées du plus faible au plus fort sur l'axe concerné.
#  Elles sont volontairement courtes : un dictionnaire trop riche produit du
#  bavardage, et le bavardage donne l'illusion du sens.
LEXIQUE_PAR_DEFAUT: Dict[str, object] = {
    "nom": "Français — registre contemplatif",
    "langue": "fr",
    "auteur": "Bretagne Namasté",
    "note": "Dictionnaire d'exemple. Le modifier est l'usage normal, pas une "
            "entorse : les mots doivent être ceux de celui qui écoute.",
    "registres": {
        "sujet": ["je", "quelque chose", "la sève", "le tronc", "la feuille"],
        "verbe_montee": ["frémis", "m'éveille", "monte", "m'élance", "jaillis"],
        "verbe_descente": ["m'apaise", "redescends", "me retire", "me repose",
                           "m'efface"],
        "intensite": ["à peine", "doucement", "nettement", "fortement",
                      "de tout mon bois"],
        "tempo": ["encore", "de nouveau", "après un temps", "après un long temps",
                  "après un très long silence"],
        "couleur": ["sourd", "grave", "ample", "clair", "aigu"],
        "liaison": ["et", "puis", "alors", "tandis que", "—"],
    },
    "grammaire": "contemplative",
}


# ---------------------------------------------------------------------------
#  L'énoncé produit
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Enonce:
    """Un énoncé décidé par le moteur — immuable, traçable, sérialisable."""
    texte: str
    mots: Tuple[str, ...]
    time_s: float
    intensite01: float
    direction: int                        # +1 montée, −1 descente, 0 indécis
    tempo01: float
    couleur01: float
    couleur_hz: float
    grammaire: str
    lexique: str
    reason: str = ""
    source_event: Optional[Event] = None

    def to_row(self) -> List[str]:
        e = self.source_event
        return [f"{self.time_s:.4f}", self.texte,
                f"{self.intensite01:.3f}", str(self.direction),
                f"{self.tempo01:.3f}", f"{self.couleur01:.3f}",
                f"{self.couleur_hz:.4f}", self.grammaire, self.lexique,
                f"{(e.amplitude_v if e else 0.0):.9f}",
                f"{(e.sigma if e else 0.0):.2f}", self.reason]


CSV_HEADER_VOCAL = ["temps_s", "enonce", "intensite", "direction", "tempo",
                    "couleur", "couleur_hz", "grammaire", "lexique",
                    "amplitude_v", "sigma", "regle"]


# ---------------------------------------------------------------------------
#  Le dictionnaire
# ---------------------------------------------------------------------------
class Lexique:
    """Un dictionnaire de mots, chargeable et enregistrable en JSON."""

    def __init__(self, donnees: Optional[Dict[str, object]] = None):
        d = dict(donnees or LEXIQUE_PAR_DEFAUT)
        self.nom: str = str(d.get("nom", "sans nom"))
        self.langue: str = str(d.get("langue", "fr"))
        self.auteur: str = str(d.get("auteur", ""))
        self.note: str = str(d.get("note", ""))
        self.grammaire: str = str(d.get("grammaire", "contemplative"))
        #  Gabarits propres au dictionnaire, par grammaire. Ils l'emportent sur
        #  ceux de GRAMMAIRES : c'est ce qui permet à une langue de placer le
        #  verbe là où sa syntaxe le demande.
        self.gabarits: Dict[str, List[str]] = {
            str(k): [str(g) for g in v]
            for k, v in dict(d.get("gabarits") or {}).items() if v}
        reg = d.get("registres") or {}
        self.registres: Dict[str, List[str]] = {
            k: [str(m) for m in v] for k, v in dict(reg).items() if v}
        self._valider()

    # -- validation ---------------------------------------------------------
    REQUIS = ("sujet", "verbe_montee", "verbe_descente", "intensite", "tempo",
              "couleur", "liaison")

    def _valider(self) -> None:
        """Complète silencieusement les registres manquants plutôt que
        d'échouer : un dictionnaire incomplet doit rester utilisable."""
        defaut = LEXIQUE_PAR_DEFAUT["registres"]              # type: ignore[index]
        for cle in self.REQUIS:
            if not self.registres.get(cle):
                self.registres[cle] = list(defaut[cle])       # type: ignore[index]
                log.warning("Lexique « %s » : registre « %s » absent, "
                            "remplacé par celui d'origine.", self.nom, cle)

    # -- accès --------------------------------------------------------------
    def choisir(self, registre: str, position01: float) -> str:
        """Le mot du registre correspondant à une position sur l'axe [0, 1]."""
        mots = self.registres.get(registre) or ["…"]
        if len(mots) == 1:
            return mots[0]
        p = min(max(float(position01), 0.0), 1.0)
        i = int(round(p * (len(mots) - 1)))
        return mots[i]

    def taille(self) -> int:
        return sum(len(v) for v in self.registres.values())

    # -- entrées/sorties ----------------------------------------------------
    @classmethod
    def charger(cls, chemin: str) -> "Lexique":
        with open(chemin, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    @classmethod
    def livre(cls, code: str) -> "Lexique":
        """Le dictionnaire livré pour une langue, le français à défaut."""
        for essai in (str(code or "").lower(), LANGUE_DEFAUT):
            chemin = os.path.join(DOSSIER_LEXIQUES, f"{essai}.json")
            if os.path.isfile(chemin):
                try:
                    return cls.charger(chemin)
                except (OSError, ValueError) as exc:
                    log.error("Dictionnaire livré « %s » illisible : %s", essai, exc)
        return cls()

    def enregistrer(self, chemin: str) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(chemin)), exist_ok=True)
        donnees: Dict[str, object] = {
            "nom": self.nom, "langue": self.langue, "auteur": self.auteur,
            "note": self.note, "grammaire": self.grammaire,
            "registres": self.registres}
        if self.gabarits:
            donnees["gabarits"] = self.gabarits
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(donnees, f, ensure_ascii=False, indent=2)

    def describe(self) -> List[str]:
        return [f"Dictionnaire : {self.nom} ({self.langue})",
                f"Registres : {', '.join(sorted(self.registres))}",
                f"Mots disponibles : {self.taille()}"]


# ---------------------------------------------------------------------------
#  Les grammaires — comment les mots s'assemblent
# ---------------------------------------------------------------------------
#  Chaque grammaire est une liste de gabarits. Les jetons entre accolades sont
#  remplacés par le mot choisi dans le registre du même nom ; « verbe » est
#  résolu selon la direction. Un gabarit tiré au sort évite la litanie.
GRAMMAIRES: Dict[str, Dict[str, object]] = {
    "minimale": {
        "titre": "Minimal — one word",
        "description": "One word per event. The most honest setting: nothing is added that has not been measured.",
        "gabarits": ["{verbe}"],
    },
    "telegraphique": {
        "titre": "Telegraphic — two words",
        "description": "The verb and its intensity. Short, legible, with no syntax that would suggest a thought.",
        "gabarits": ["{verbe} {intensite}"],
    },
    "contemplative": {
        "titre": "Contemplative — a short sentence",
        "description": "Subject, verb, intensity, sometimes a circumstance. This is the setting shipped by default.",
        "gabarits": [
            "{sujet} {verbe} {intensite}",
            "{tempo}, {sujet} {verbe} {intensite}",
            "{sujet} {verbe} {intensite}, {couleur}",
        ],
    },
    "descriptive": {
        "titre": "Descriptive — every dimension",
        "description": "Every measured axis gives a word. Verbose, but nothing is left implicit.",
        "gabarits": [
            "{tempo}, {sujet} {verbe} {intensite}, {couleur}",
            "{sujet} {verbe} {intensite} {liaison} {couleur}",
        ],
    },
}


# ---------------------------------------------------------------------------
#  Les dictionnaires livrés
# ---------------------------------------------------------------------------
LANGUE_DEFAUT = "fr"


def lexiques_livres() -> List[Tuple[str, str]]:
    """(code de langue, nom du dictionnaire) — pour la liste de l'interface.

    Le dossier est parcouru plutôt que décrit : un dictionnaire ajouté par
    l'utilisateur y apparaît sans qu'on touche au code, exactement comme pour
    les catalogues de traduction.
    """
    out: List[Tuple[str, str]] = []
    try:
        fichiers = sorted(os.listdir(DOSSIER_LEXIQUES))
    except OSError:
        return out
    for nom in fichiers:
        if not nom.endswith(".json"):
            continue
        code = nom[:-5]
        try:
            with open(os.path.join(DOSSIER_LEXIQUES, nom), encoding="utf-8") as f:
                titre = str(json.load(f).get("nom", code))
        except (OSError, ValueError):
            continue
        out.append((code, titre))
    #  Le français d'abord : c'est la langue source du projet.
    out.sort(key=lambda c: (c[0] != LANGUE_DEFAUT, c[0]))
    return out


def lexique_livre(code: str) -> "Lexique":
    return Lexique.livre(code)


# ---------------------------------------------------------------------------
#  Le moteur
# ---------------------------------------------------------------------------
class VocalMapper:
    """Transforme un flux d'événements en un flux d'énoncés.

    Le parallèle avec :class:`~phytoscope.music.mapper.Mapper` est voulu : mêmes
    entrées, mêmes garde-fous de densité et d'anti-répétition, même traçabilité.
    Seule la sortie change de nature.
    """

    def __init__(self, settings, lexique: Optional[Lexique] = None):
        self.settings = settings
        self.lexique = lexique or Lexique()
        self.last_time = -1e9
        self.last_texte: Optional[str] = None
        self.repeat_count = 0
        self.recent: List[float] = []
        self._rng = random.Random(20260917)      # tirage reproductible
        self._couleur_hz = 0.0
        self._suivi = False                      # le dictionnaire suit-il la langue ?
        self.refresh()

    # -- configuration ------------------------------------------------------
    def refresh(self) -> None:
        """Choisit le dictionnaire : celui de l'utilisateur, ou celui de la langue.

        Sans fichier désigné, le dictionnaire suit la langue de l'interface —
        une interface en japonais qui ferait parler la plante en français
        n'aurait aucun sens. Ce suivi se débraye d'une case à cocher, pour qui
        veut écouter dans une langue et lire dans une autre.
        """
        v = getattr(self.settings, "voice", None)
        chemin = getattr(v, "lexicon_path", "") if v else ""
        if chemin and os.path.isfile(chemin):
            try:
                self.lexique = Lexique.charger(chemin)
                log.info("Dictionnaire chargé : %s (%d mots)",
                         self.lexique.nom, self.lexique.taille())
            except (OSError, ValueError, TypeError) as exc:
                log.error("Dictionnaire illisible (%s) : %s — "
                          "celui d'origine est conservé.", chemin, exc)
            return
        impose = str(getattr(v, "lexicon_code", "") or "") if v else ""
        if impose:
            if self.lexique.langue != impose or not self._suivi:
                self.lexique = Lexique.livre(impose)
                self._suivi = True
                log.info("Dictionnaire « %s » : %s (%d mots)", impose,
                         self.lexique.nom, self.lexique.taille())
            return
        if v is not None and getattr(v, "lexicon_auto", True):
            from ..i18n import langue_courante
            code = langue_courante()
            if self.lexique.langue != code or not self._suivi:
                self.lexique = Lexique.livre(code)
                self._suivi = True
                log.info("Dictionnaire de la langue « %s » : %s (%d mots)",
                         code, self.lexique.nom, self.lexique.taille())

    def set_couleur_hz(self, f: float) -> None:
        """Renseigne le centre de gravité spectral courant, calculé ailleurs.

        Le moteur ne recalcule pas de spectre : ce serait le faire deux fois. Il
        reçoit la valeur de l'analyseur, et s'en passe si elle manque.
        """
        if f and f > 0:
            self._couleur_hz = float(f)

    # -- cœur ---------------------------------------------------------------
    def map_event(self, ev: Event, now: Optional[float] = None) -> Optional[Enonce]:
        v = getattr(self.settings, "voice", None)
        if v is None or not v.enabled:
            return None
        now = ev.time_s if now is None else now

        # 1. densité — on ne parle pas plus vite qu'on ne peut écouter
        min_gap = 60.0 / max(float(v.density_per_min), 1.0)
        self.recent = [t for t in self.recent if now - t < 60.0]
        if now - self.last_time < min_gap:
            return None

        # 2. les quatre axes mesurés
        intensite01 = _compress(max(ev.sigma, 0.0),
                                knee=self.settings.processing.event_threshold_sigma)
        direction = 1 if ev.slope_v_s >= 0 else -1
        gap = min(now - self.last_time, 300.0)
        tempo01 = min(gap / max(float(v.tempo_scale_s), 1.0), 1.0)
        f_max = max(self.settings.acquisition.sample_rate / 2.5, 1e-6)
        couleur01 = min(self._couleur_hz / f_max, 1.0) if self._couleur_hz else 0.5

        # 3. les mots
        registre_verbe = "verbe_montee" if direction > 0 else "verbe_descente"
        mots = {
            "sujet": self.lexique.choisir("sujet", float(v.subject_position)),
            "verbe": self.lexique.choisir(registre_verbe, intensite01),
            "intensite": self.lexique.choisir("intensite", intensite01),
            "tempo": self.lexique.choisir("tempo", tempo01),
            "couleur": self.lexique.choisir("couleur", couleur01),
            "liaison": self.lexique.choisir("liaison", tempo01),
        }

        # 4. la phrase
        nom_gram = v.grammar if v.grammar in GRAMMAIRES else "contemplative"
        #  Les gabarits du dictionnaire l'emportent : une langue dont l'ordre
        #  des mots diffère du français les porte avec elle.
        gabarits: Sequence[str] = (self.lexique.gabarits.get(nom_gram)
                                   or GRAMMAIRES[nom_gram]["gabarits"])   # type: ignore[assignment]
        gabarit = gabarits[self._rng.randrange(len(gabarits))]
        texte = gabarit.format(**mots).strip()
        texte = texte[0].upper() + texte[1:] if texte else texte

        # 5. anti-répétition — deux fois la même phrase, on change de gabarit
        if texte == self.last_texte:
            self.repeat_count += 1
            if self.repeat_count >= 2 and len(gabarits) > 1:
                autre = [g for g in gabarits if g != gabarit]
                texte = autre[self._rng.randrange(len(autre))].format(**mots).strip()
                texte = texte[0].upper() + texte[1:] if texte else texte
                self.repeat_count = 0
        else:
            self.repeat_count = 0

        reason = (f"σ={ev.sigma:.1f}→i{intensite01:.2f} · "
                  f"pente={ev.slope_v_s:+.2e}→{'montée' if direction > 0 else 'descente'} · "
                  f"Δt={gap:.1f}s→t{tempo01:.2f} · "
                  f"f={self._couleur_hz:.3f}Hz→c{couleur01:.2f}")

        self.last_time = now
        self.last_texte = texte
        self.recent.append(now)
        return Enonce(texte=texte, mots=tuple(mots.values()), time_s=now,
                      intensite01=intensite01, direction=direction,
                      tempo01=tempo01, couleur01=couleur01,
                      couleur_hz=self._couleur_hz, grammaire=nom_gram,
                      lexique=self.lexique.nom, reason=reason,
                      source_event=ev)

    # -- explication --------------------------------------------------------
    def describe_rules(self) -> List[str]:
        v = getattr(self.settings, "voice", None)
        if v is None:
            return [t("Speech mode unavailable.")]
        g = GRAMMAIRES.get(v.grammar, GRAMMAIRES["contemplative"])
        return [
            t("Dictionary: {nom} — {n} words").format(
                nom=self.lexique.nom, n=self.lexique.taille()),
            t("Grammar: {nom}").format(nom=t(str(g["titre"]))),
            t("Verb ← direction of the slope (rise or fall)"),
            t("Intensity ← amplitude of the event, in standard deviations"),
            t("Circumstance ← time elapsed since the previous utterance"),
            t("Qualifier ← spectral centroid of the signal"),
            t("Maximum density: {n:g} utterances per minute").format(
                n=v.density_per_min),
            t("None of these rules translates anything: they describe the signal with the words of the chosen dictionary."),
        ]


def _compress(x: float, knee: float = 3.5) -> float:
    """Même compression que le moteur musical — pour que les deux modes
    réagissent identiquement au même événement."""
    if x <= 0:
        return 0.0
    return min(1.0, (x / knee) / (1.0 + x / (knee * 2.2)))
