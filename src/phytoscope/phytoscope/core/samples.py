# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/samples.py
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

"""Échantillons : garder un morceau de signal d'un seul geste, et le rejouer.

Un enregistrement de séance est un engagement : on le décide avant, il dure, il
produit un répertoire. Or l'essentiel arrive souvent **avant** qu'on ait pensé à
enregistrer — la plante réagit, on comprend une minute trop tard que cela valait
la peine d'être gardé. Le logiciel tient dix minutes de signal en mémoire ; il
serait absurde de les laisser s'effacer.

D'où l'échantillon : un bouton, et la dernière minute écoulée est écrite sur le
disque. Rien à préparer, rien à arrêter.

Le format, volontairement pauvre
--------------------------------

Un échantillon, c'est **un fichier WAV** — 24 bits, la cadence réelle, une piste
par voie — et, à côté, un petit fichier JSON de même nom :

    2026-09-18_101530_ficus.wav     le signal, ouvrable dans Audacity
    2026-09-18_101530_ficus.json    cadence, pleine échelle, plante, réglages

Le JSON est **facultatif** : un WAV seul se recharge très bien, la pleine
échelle étant alors celle des réglages courants. C'est ce qui permet de recevoir
l'échantillon d'un correspondant, ou d'en fabriquer un avec un autre logiciel,
sans rien devoir convertir.

Ce que le JSON ajoute est ce qu'un WAV ne sait pas dire : combien de volts vaut
la pleine échelle — sans quoi le fichier est joli mais inexploitable —, quelle
plante, quel lieu, et les réglages de la chaîne au moment de la capture.

La pleine échelle, et pourquoi elle n'est pas celle du convertisseur
--------------------------------------------------------------------

Le `signal.wav` d'une séance conserve le signal **brut**, qui occupe réellement
la plage du convertisseur : ±2,5 V y est la bonne référence. Un échantillon, lui,
garde le signal **filtré et centré** — celui qu'on voit à l'écran —, dont
l'amplitude se compte en microvolts. L'écrire à ±2,5 V reviendrait à n'utiliser
que neuf bits sur vingt-quatre, et à quantifier à 0,3 µV un signal dont le bruit
propre vaut un microvolt : la relecture serait visiblement plus grossière que
l'original.

La pleine échelle est donc **choisie pour chaque échantillon**, arrondie vers le
haut dans la suite 1–2–5 au-dessus de l'amplitude observée, et inscrite dans le
JSON. Le pas de quantification tombe ainsi sous le picovolt, et la relecture est
exacte à la précision de la mesure près. Un WAV privé de son JSON reste lisible
— la forme est intacte — mais son amplitude est alors *supposée* : l'interface
le signale plutôt que de faire croire à une mesure.
"""
from __future__ import annotations

import json
import math
import os
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from . import noms

__all__ = ["EchantillonRef", "dossier_par_defaut", "ecrire", "lister",
           "charger", "supprimer", "renommer", "echelle_adaptee"]


def dossier_par_defaut(settings) -> str:
    """Les échantillons vivent à côté des séances, dans leur propre dossier."""
    return os.path.join(settings.recording.directory, "echantillons")


# ---------------------------------------------------------------------------
#  Référence
# ---------------------------------------------------------------------------
@dataclass
class EchantillonRef:
    """Ce que la bibliothèque affiche sans avoir à lire tout le signal."""
    path: str                       # le .wav
    name: str = ""
    started: str = ""
    duration_s: float = 0.0
    sample_rate: float = 250.0
    channels: int = 1
    full_scale_v: float = 2.5
    plante: str = ""
    lieu: str = ""
    note: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def json_path(self) -> str:
        return os.path.splitext(self.path)[0] + ".json"

    @property
    def complet(self) -> bool:
        """Vrai si l'échantillon porte ses métadonnées."""
        return os.path.exists(self.json_path)

    def pretty_duration(self) -> str:
        s = self.duration_s
        return f"{s:.1f} s" if s < 60 else f"{int(s) // 60} min {int(s) % 60:02d} s"

    def pretty_date(self) -> str:
        try:
            return datetime.fromisoformat(self.started).astimezone().strftime(
                "%d/%m/%Y %H:%M:%S")
        except (TypeError, ValueError):
            return self.started or "?"


# ---------------------------------------------------------------------------
#  Écriture
# ---------------------------------------------------------------------------
def echelle_adaptee(signal: np.ndarray, plancher_v: float = 1e-5) -> float:
    """Pleine échelle d'un échantillon : 1–2–5 juste au-dessus de l'amplitude.

    Un nombre rond plutôt que l'amplitude exacte, pour deux raisons : il se lit
    dans le JSON sans calculette, et deux échantillons voisins tombent sur la
    même échelle, ce qui rend leurs tracés directement comparables.
    """
    x = np.asarray(signal, dtype=np.float64)
    crete = float(np.max(np.abs(x))) if x.size else 0.0
    besoin = max(crete * 1.2, plancher_v)
    decade = 10.0 ** math.floor(math.log10(besoin))
    for facteur in (1.0, 2.0, 5.0, 10.0):
        if besoin <= facteur * decade:
            return facteur * decade
    return 10.0 * decade                               # pragma: no cover


def ecrire(signal: np.ndarray, fs: float, dossier: str,
           full_scale_v: float = 0.0, etiquette: str = "",
           metadonnees: Optional[Dict[str, Any]] = None) -> str:
    """Écrit un échantillon et retourne le chemin du WAV.

    Le signal est attendu **en volts**. `full_scale_v` à zéro — le cas normal —
    laisse la pleine échelle être choisie d'après le signal lui-même ; on ne la
    force que pour recopier un échantillon dans l'échelle d'un autre.
    """
    x = np.asarray(signal, dtype=np.float64)
    if x.ndim == 1:
        x = x[:, None]
    if x.size == 0:
        raise ValueError("échantillon vide")
    fs = float(fs) if fs > 0 else 250.0
    pleine = float(full_scale_v) if full_scale_v > 0 else echelle_adaptee(x)

    os.makedirs(dossier, exist_ok=True)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    #  Une étiquette entièrement non latine — « 中文 » — ne laisse rien après
    #  translittération : on garde alors le seul horodatage plutôt qu'un nom
    #  terminé par un tiret bas orphelin.
    marque = _slug(etiquette) if etiquette else ""
    base = f"{horodatage}_{marque}" if marque else horodatage
    chemin = os.path.join(dossier, base + ".wav")
    n = 1
    while os.path.exists(chemin):                      # jamais écraser
        n += 1
        chemin = os.path.join(dossier, f"{base}-{n}.wav")

    ints = (np.clip(x / pleine, -1.0, 1.0 - 1e-9) * 8388607.0).astype(np.int32)
    plat = ints.reshape(-1)
    brut = bytearray(plat.size * 3)
    for i, v in enumerate(plat.tolist()):
        v &= 0xFFFFFF
        brut[3 * i] = v & 0xFF
        brut[3 * i + 1] = (v >> 8) & 0xFF
        brut[3 * i + 2] = (v >> 16) & 0xFF
    with wave.open(chemin, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(3)
        w.setframerate(int(round(fs)))
        w.writeframes(bytes(brut))

    infos: Dict[str, Any] = {
        "type": "echantillon-phytoscope",
        "version": 1,
        "nom": base,
        "horodatage_utc": datetime.now(timezone.utc).isoformat(),
        "duree_s": x.shape[0] / fs,
        "frequence_echantillonnage_hz": fs,
        "voies": x.shape[1],
        "pleine_echelle_v": pleine,
        "signal": "filtré et centré, en volts",
        "pas_de_quantification_v": pleine / 8388607.0,
    }
    infos.update(metadonnees or {})
    try:
        with open(os.path.splitext(chemin)[0] + ".json", "w",
                  encoding="utf-8") as f:
            json.dump(infos, f, ensure_ascii=False, indent=2)
    except OSError:                                    # pragma: no cover
        pass                                           # le WAV suffit à relire
    return chemin


# ---------------------------------------------------------------------------
#  Lecture
# ---------------------------------------------------------------------------
def lister(dossier: str) -> List[EchantillonRef]:
    """Les échantillons d'un dossier, du plus récent au plus ancien."""
    out: List[EchantillonRef] = []
    if not os.path.isdir(dossier):
        return out
    for nom in sorted(os.listdir(dossier), reverse=True):
        if not nom.lower().endswith(".wav"):
            continue
        chemin = os.path.join(dossier, nom)
        ref = EchantillonRef(path=chemin, name=os.path.splitext(nom)[0])
        _entete_wav(ref)
        _relire_json(ref)
        out.append(ref)
    return out


def _entete_wav(ref: EchantillonRef) -> None:
    """Ce que le WAV dit de lui-même — il dit presque tout, sauf les volts."""
    try:
        with wave.open(ref.path, "rb") as w:
            ref.channels = w.getnchannels()
            ref.sample_rate = float(w.getframerate())
            ref.duration_s = w.getnframes() / max(ref.sample_rate, 1e-9)
    except (OSError, wave.Error):                      # pragma: no cover
        pass
    try:
        horo = datetime.fromtimestamp(os.path.getmtime(ref.path))
        ref.started = horo.isoformat()
    except OSError:                                    # pragma: no cover
        pass


def _relire_json(ref: EchantillonRef) -> None:
    if not os.path.exists(ref.json_path):
        return
    try:
        with open(ref.json_path, encoding="utf-8") as f:
            infos = json.load(f)
    except (OSError, ValueError):
        return
    ref.meta = infos
    ref.full_scale_v = float(infos.get("pleine_echelle_v", ref.full_scale_v) or 2.5)
    ref.plante = str(infos.get("plante", "") or "")
    ref.lieu = str(infos.get("lieu", "") or "")
    ref.note = str(infos.get("note", "") or "")
    ref.started = str(infos.get("horodatage_utc", ref.started) or ref.started)
    if infos.get("frequence_echantillonnage_hz"):
        ref.sample_rate = float(infos["frequence_echantillonnage_hz"])


def charger(ref: EchantillonRef,
            pleine_echelle_defaut: float = 2.5) -> Tuple[Optional[np.ndarray], float]:
    """Relit le signal, en volts. Le WAV seul suffit."""
    if not os.path.exists(ref.path):
        return None, ref.sample_rate
    try:
        with wave.open(ref.path, "rb") as w:
            n, ch, largeur = w.getnframes(), w.getnchannels(), w.getsampwidth()
            fs = float(w.getframerate())
            brut = w.readframes(n)
    except (OSError, wave.Error):                      # pragma: no cover
        return None, ref.sample_rate
    if largeur == 3:
        a = np.frombuffer(brut, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        v = a[:, 0] | (a[:, 1] << 8) | (a[:, 2] << 16)
        v = np.where(v & 0x800000, v - 0x1000000, v)
        data = v.astype(np.float64) / 8388607.0
    elif largeur == 2:
        data = np.frombuffer(brut, dtype="<i2").astype(np.float64) / 32767.0
    elif largeur == 4:
        data = np.frombuffer(brut, dtype="<i4").astype(np.float64) / 2147483647.0
    elif largeur == 1:                                 # PCM non signé
        data = (np.frombuffer(brut, dtype=np.uint8).astype(np.float64) - 128.0) / 127.0
    else:                                              # pragma: no cover
        return None, fs
    pleine = ref.full_scale_v if ref.complet else float(pleine_echelle_defaut)
    return data.reshape(-1, ch) * pleine, fs


# ---------------------------------------------------------------------------
#  Gestion
# ---------------------------------------------------------------------------
def supprimer(ref: EchantillonRef) -> None:
    """Efface le WAV et son JSON. Rien d'autre ne dépend d'eux."""
    for chemin in (ref.path, ref.json_path):
        try:
            os.remove(chemin)
        except OSError:
            pass


def renommer(ref: EchantillonRef, nouveau: str) -> str:
    """Renomme le couple WAV + JSON, en gardant l'horodatage en tête."""
    nouveau = _slug(nouveau) or ref.name
    dossier = os.path.dirname(ref.path)
    cible = os.path.join(dossier, nouveau + ".wav")
    if os.path.exists(cible):
        return ref.path
    os.rename(ref.path, cible)
    if os.path.exists(ref.json_path):
        os.rename(ref.json_path, os.path.splitext(cible)[0] + ".json")
    return cible


def _slug(texte: str) -> str:
    """Nom de fichier d'échantillon — voir `core.noms` pour le pourquoi.

    Rend la chaîne vide quand il ne reste rien : les appelants s'en servent
    pour décider s'il y a une étiquette (`ecrire`) ou pour garder l'ancien nom
    (`renommer`).
    """
    return noms.assainir(texte, defaut="", longueur=48)
