# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/session.py
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

"""Bibliothèque des séances : lister, lire, rejouer, exporter.

Le format étant ouvert, cette classe ne fait rien de magique : elle parcourt
un répertoire, lit les `seance.json` et rend les enregistrements utilisables
par le reste du logiciel.
"""
from __future__ import annotations

import csv
import json
import os
import wave
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class SessionRef:
    """Référence légère vers une séance — ce qu'affiche la bibliothèque."""
    path: str
    name: str = ""
    started: str = ""
    duration_s: float = 0.0
    sample_rate: float = 250.0
    channels: int = 1
    full_scale_v: float = 2.5
    plante: str = ""
    lieu: str = ""
    notes: int = 0
    events: int = 0
    marks: int = 0
    meta: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_signal(self) -> bool:
        return os.path.exists(os.path.join(self.path, "signal.wav"))

    @property
    def has_music(self) -> bool:
        return os.path.exists(os.path.join(self.path, "musique.wav"))

    def pretty_duration(self) -> str:
        s = int(self.duration_s)
        return f"{s // 3600:d} h {(s % 3600) // 60:02d} min {s % 60:02d} s" \
            if s >= 3600 else f"{s // 60:d} min {s % 60:02d} s"

    def pretty_date(self) -> str:
        try:
            return datetime.fromisoformat(self.started).astimezone().strftime(
                "%d/%m/%Y %H:%M")
        except (TypeError, ValueError):
            return self.started or "?"


def scan(directory: str) -> List[SessionRef]:
    """Toutes les séances d'un répertoire, de la plus récente à la plus ancienne."""
    out: List[SessionRef] = []
    if not os.path.isdir(directory):
        return out
    for name in sorted(os.listdir(directory), reverse=True):
        path = os.path.join(directory, name)
        meta_path = os.path.join(path, "seance.json")
        if not os.path.isfile(meta_path):
            continue
        try:
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
        except (OSError, ValueError):
            continue
        md = meta.get("metadata") or {}
        counts = meta.get("counts") or {}
        out.append(SessionRef(
            path=path, name=meta.get("name", name),
            started=meta.get("started_utc", ""),
            duration_s=float(meta.get("duration_s", 0.0) or 0.0),
            sample_rate=float(meta.get("sample_rate", 250.0) or 250.0),
            channels=int(meta.get("channels", 1) or 1),
            full_scale_v=float(meta.get("full_scale_v", 2.5) or 2.5),
            plante=str(md.get("plante", "")), lieu=str(md.get("lieu", "")),
            notes=int(counts.get("notes", 0) or 0),
            events=int(counts.get("evenements", 0) or 0),
            marks=int(counts.get("marqueurs", 0) or 0),
            meta=meta))
    return out


def load_signal(ref: SessionRef) -> Tuple[Optional[np.ndarray], float]:
    """Relit `signal.wav` et le reconvertit en volts."""
    path = os.path.join(ref.path, "signal.wav")
    if not os.path.exists(path):
        return None, ref.sample_rate
    with wave.open(path, "rb") as w:
        n = w.getnframes()
        ch = w.getnchannels()
        width = w.getsampwidth()
        fs = float(w.getframerate())
        raw = w.readframes(n)
    if width == 3:
        a = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        vals = a[:, 0] | (a[:, 1] << 8) | (a[:, 2] << 16)
        vals = np.where(vals & 0x800000, vals - 0x1000000, vals)
        data = vals.astype(np.float64) / 8388607.0
    elif width == 2:
        data = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32767.0
    elif width == 4:
        data = np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483647.0
    else:                                              # pragma: no cover
        return None, fs
    data = data.reshape(-1, ch) * ref.full_scale_v
    return data, fs


def load_events(ref: SessionRef) -> List[Dict[str, Any]]:
    return _load_csv(os.path.join(ref.path, "evenements.csv"))


def load_notes(ref: SessionRef) -> List[Dict[str, Any]]:
    return _load_csv(os.path.join(ref.path, "notes.csv"))


def load_marks(ref: SessionRef) -> List[Dict[str, Any]]:
    return _load_csv(os.path.join(ref.path, "marqueurs.csv"))


def _load_csv(path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    except OSError:                                    # pragma: no cover
        return []


def export_summary(ref: SessionRef) -> str:
    """Résumé lisible d'une séance — ce qu'on colle dans un carnet."""
    lines = [
        f"Séance : {ref.name}",
        f"Date : {ref.pretty_date()}   Durée : {ref.pretty_duration()}",
        f"Plante : {ref.plante or '—'}   Lieu : {ref.lieu or '—'}",
        f"Échantillonnage : {ref.sample_rate:g} Hz sur {ref.channels} voie(s)",
        f"Événements : {ref.events}   Notes : {ref.notes}   Marqueurs : {ref.marks}",
    ]
    settings = (ref.meta.get("settings") or {})
    music = settings.get("music") or {}
    if music:
        lines.append(f"Gamme : {music.get('scale', '?')} sur {music.get('root', '?')} "
                     f"— instrument : {music.get('instrument', '?')}")
    proc = settings.get("processing") or {}
    if proc:
        lines.append(f"Filtrage : passe-haut {proc.get('highpass_hz', 0)} Hz, "
                     f"passe-bas {proc.get('lowpass_hz', 0)} Hz, "
                     f"réjecteur {proc.get('notch_hz', 0)} Hz")
        lines.append(f"Seuil de détection : {proc.get('event_threshold_sigma', 0)} σ")
    return "\n".join(lines)
