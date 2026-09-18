# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/protocol.py
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

"""Protocole de la carte PhytoSense sur le lien série virtuel (CDC).

Deux flux coexistent sur le même câble USB :

* le **flux de mesure**, transporté par la classe audio (UAC2), que le
  système d'exploitation présente comme une carte son — donc sans pilote ;
* le **flux de contrôle**, en texte sur le port série virtuel, décrit ici.

Le contrôle est volontairement lisible : on peut l'ouvrir avec n'importe
quel terminal, taper `?` et voir la carte répondre. Une carte qu'on ne peut
pas interroger à la main est une carte qu'on ne peut pas dépanner.

    > ?                     → identification complète, en JSON sur une ligne
    > gain 100              → force le gain matériel
    > gain auto             → rend la main à la boucle d'auto-échelle
    > range 2               → gamme du pont (0..3)
    > selftest              → lance l'auto-test et renvoie le rapport
    > mark Ouverture        → insère un marqueur horodaté dans le flux
    > clock                 → renvoie le compteur d'échantillons courant

Chaque réponse tient sur une ligne et commence par `+` (succès) ou `-`
(erreur), suivie d'un objet JSON.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


CRLF = "\r\n"
DEFAULT_BAUD = 115200
DEFAULT_TIMEOUT = 1.0

#  Identifiants USB déclarés par le micrologiciel de référence
#  (`usb_descriptors.c`). `0x1209` est la plage de **pid.codes**, ouverte aux
#  projets libres : un projet comme celui-ci y a droit, alors qu'il n'a aucun
#  titre à attribuer un PID sous `0x2E8A`, qui appartient à Raspberry Pi. Ces
#  deux constantes doivent suivre le micrologiciel, jamais l'inverse.
USB_VID = 0x1209          # pid.codes — plage libre pour les projets ouverts
USB_PID = 0x7A01          # PhytoSense One
PRODUCT_HINTS = ("phytosense", "plantwave", "biodata", "midi sprout", "biotron")


@dataclass
class BoardInfo:
    """Ce que la carte dit d'elle-même."""
    model: str = "inconnu"
    serial: str = ""
    firmware: str = ""
    channels: int = 1
    sample_rate: float = 250.0
    frontend: str = ""            # FE-Z, FE-B, FE-C, FE-AUX
    frontend_serial: str = ""
    gains: List[int] = field(default_factory=lambda: [1, 2, 5, 10, 20, 50, 100, 200])
    ranges: List[str] = field(default_factory=list)
    volts_per_unit: float = 1.0
    calibration_date: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_json(cls, payload: Dict[str, Any]) -> "BoardInfo":
        info = cls(raw=dict(payload))
        for k in ("model", "serial", "firmware", "frontend", "frontend_serial",
                  "calibration_date"):
            if k in payload:
                setattr(info, k, str(payload[k]))
        for k in ("channels",):
            if k in payload:
                info.channels = int(payload[k])
        for k in ("sample_rate", "volts_per_unit"):
            if k in payload:
                setattr(info, k, float(payload[k]))
        if isinstance(payload.get("gains"), list):
            info.gains = [int(g) for g in payload["gains"]]
        if isinstance(payload.get("ranges"), list):
            info.ranges = [str(r) for r in payload["ranges"]]
        return info

    def describe(self) -> str:
        fe = f" · carte fille {self.frontend}" if self.frontend else ""
        return f"{self.model} (série {self.serial or '?'}){fe}"


@dataclass
class SelfTestReport:
    """Rapport d'auto-test : ce que la carte mesure sur ses propres étalons."""
    passed: bool = False
    measurements: Dict[str, float] = field(default_factory=dict)
    errors_percent: Dict[str, float] = field(default_factory=dict)
    noise_floor_v: float = 0.0
    leakage_fa: float = 0.0
    message: str = ""

    def summary_lines(self) -> List[str]:
        out = [("réussi" if self.passed else "ÉCHEC") + " — " + (self.message or "")]
        for k, v in sorted(self.errors_percent.items()):
            out.append(f"  étalon {k} : écart {v:+.2f} %")
        if self.noise_floor_v:
            out.append(f"  plancher de bruit : {self.noise_floor_v * 1e6:.2f} µV eff.")
        if self.leakage_fa:
            out.append(f"  courant de fuite : {self.leakage_fa:.1f} fA")
        return out


class ControlLink:
    """Dialogue avec la carte sur le port série virtuel.

    L'objet reste utilisable si `pyserial` n'est pas installé : toutes les
    méthodes renvoient alors `None`, et le logiciel continue de fonctionner
    en lecture seule. C'est volontaire — on ne bloque jamais l'écoute parce
    qu'une dépendance facultative manque.
    """

    def __init__(self, port: str = "", baud: int = DEFAULT_BAUD):
        self.port = port
        self.baud = baud
        self._ser = None
        self.last_error = ""

    # -- découverte ----------------------------------------------------------
    @staticmethod
    def discover() -> List[str]:
        """Ports série qui ressemblent à une carte de bio-signal."""
        try:
            from serial.tools import list_ports
        except ImportError:
            return []
        found = []
        for p in list_ports.comports():
            if p.vid == USB_VID and p.pid == USB_PID:
                found.insert(0, p.device)
                continue
            text = f"{p.description} {p.manufacturer or ''} {p.product or ''}".lower()
            if any(h in text for h in PRODUCT_HINTS):
                found.append(p.device)
        return found

    # -- connexion -----------------------------------------------------------
    def open(self) -> bool:
        try:
            import serial
        except ImportError:
            self.last_error = ("pyserial n'est pas installé : le contrôle de la "
                               "carte est désactivé (l'écoute reste possible).")
            return False
        if not self.port:
            ports = self.discover()
            if not ports:
                self.last_error = "aucune carte détectée sur les ports série."
                return False
            self.port = ports[0]
        try:
            self._ser = serial.Serial(self.port, self.baud, timeout=DEFAULT_TIMEOUT)
            time.sleep(0.15)
            self._ser.reset_input_buffer()
            return True
        except Exception as exc:                      # pragma: no cover
            self.last_error = f"ouverture de {self.port} impossible : {exc}"
            self._ser = None
            return False

    def close(self) -> None:
        if self._ser is not None:
            try:
                self._ser.close()
            finally:
                self._ser = None

    @property
    def is_open(self) -> bool:
        return self._ser is not None and getattr(self._ser, "is_open", False)

    # -- échanges ------------------------------------------------------------
    def command(self, line: str) -> Optional[Dict[str, Any]]:
        """Envoie une commande et renvoie l'objet JSON de la réponse."""
        if not self.is_open:
            return None
        try:
            self._ser.write((line.strip() + CRLF).encode("ascii", "replace"))
            self._ser.flush()
            raw = self._ser.readline().decode("ascii", "replace").strip()
        except Exception as exc:                      # pragma: no cover
            self.last_error = str(exc)
            return None
        if not raw:
            self.last_error = "pas de réponse de la carte."
            return None
        ok = raw.startswith("+")
        body = raw[1:].strip() if raw[:1] in "+-" else raw
        try:
            payload = json.loads(body) if body.startswith("{") else {"message": body}
        except ValueError:
            payload = {"message": body}
        if not ok:
            self.last_error = str(payload.get("message", body))
            return None
        return payload

    # -- commandes de haut niveau -------------------------------------------
    def identify(self) -> Optional[BoardInfo]:
        payload = self.command("?")
        return BoardInfo.from_json(payload) if payload else None

    def set_gain(self, gain: int | str) -> bool:
        return self.command(f"gain {gain}") is not None

    def set_range(self, index: int) -> bool:
        return self.command(f"range {int(index)}") is not None

    def mark(self, label: str) -> bool:
        clean = "".join(ch for ch in label if ch.isprintable())[:48] or "marqueur"
        return self.command(f"mark {clean}") is not None

    def clock(self) -> Optional[int]:
        payload = self.command("clock")
        if not payload:
            return None
        try:
            return int(payload.get("n", 0))
        except (TypeError, ValueError):
            return None

    def self_test(self) -> Optional[SelfTestReport]:
        payload = self.command("selftest")
        if payload is None:
            return None
        rep = SelfTestReport(
            passed=bool(payload.get("passed", False)),
            measurements={str(k): float(v)
                          for k, v in (payload.get("measurements") or {}).items()},
            errors_percent={str(k): float(v)
                            for k, v in (payload.get("errors") or {}).items()},
            noise_floor_v=float(payload.get("noise_floor_v", 0.0) or 0.0),
            leakage_fa=float(payload.get("leakage_fa", 0.0) or 0.0),
            message=str(payload.get("message", "")))
        return rep
