# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/usbdiag.py
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

"""Diagnostic du lien USB — qui est branché, sous quel VID/PID, et est-ce stable.

Trois questions reviennent en permanence lorsqu'un instrument USB « ne marche
pas » :

1. **Est-il seulement énuméré ?** D'où l'inventaire par identifiant
   constructeur et produit (VID/PID), lu sans aucune dépendance obligatoire.
2. **Est-ce le bon périphérique ?** D'où la comparaison avec les identifiants
   attendus, et la liste des cartes connues du domaine.
3. **Le lien tient-il dans la durée ?** D'où la surveillance périodique, qui
   compte les disparitions et les réénumérations.

Quatre sources d'information sont interrogées, de la plus universelle à la
plus riche : `pyserial` (toujours présent dans nos dépendances), `pyusb` si
installé, le sysfs de Linux, et l'inventaire des périphériques audio de
PortAudio. Aucune n'est obligatoire.

Le mode de mise au point ajoute la **capture des trames** : chaque bloc reçu
est consigné dans un fichier, avec son horodatage, sa taille et son contenu.
C'est volumineux — d'où l'activation explicite et le plafond de trames.
"""
from __future__ import annotations

import os
import platform
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from .logging_setup import get_logger

log = get_logger(__name__)

#  Identifiants de la carte de référence, tels que le micrologiciel les
#  déclare. Voir `protocol.USB_VID` : `0x1209` est la plage libre de pid.codes.
PHYTOSENSE_VID = 0x1209            # pid.codes
PHYTOSENSE_PID = 0x7A01            # PhytoSense One

# Cartes du domaine reconnues, pour aider au diagnostic
CARTES_CONNUES: Dict[Tuple[int, int], str] = {
    (0x1209, 0x7A01): "PhytoSense One (carte de référence)",
    #  Les identifiants Raspberry Pi restent utiles au diagnostic : une carte
    #  restée en mode chargeur se présente ainsi, et c'est la panne la plus
    #  fréquente après une programmation interrompue.
    (0x2E8A, 0x0003): "Raspberry Pi RP2 en mode chargeur (BOOTSEL)",
    (0x2E8A, 0x000A): "Raspberry Pi Pico — CDC série",
    (0x2341, 0x0043): "Arduino Uno",
    (0x2341, 0x8036): "Arduino Leonardo",
    (0x1B4F, 0x8D21): "SparkFun Pro Micro (MIDI Sprout et dérivés)",
    (0x239A, 0x800B): "Adafruit Feather M0",
    (0x0403, 0x6001): "Convertisseur FTDI FT232 (montage maison)",
    (0x10C4, 0xEA60): "Convertisseur Silicon Labs CP2102 (montage maison)",
    (0x1A86, 0x7523): "Convertisseur CH340 (montage maison)",
}

CLASSES_USB = {
    0x01: "audio", 0x02: "communication (CDC)", 0x03: "interface humaine",
    0x08: "stockage", 0x0A: "données CDC", 0x0E: "vidéo", 0xFE: "spécifique",
    0xFF: "propriétaire",
}


# ---------------------------------------------------------------------------
#  Inventaire
# ---------------------------------------------------------------------------
@dataclass
class UsbDevice:
    """Un périphérique USB vu par le système."""
    vid: int = 0
    pid: int = 0
    serial: str = ""
    manufacturer: str = ""
    product: str = ""
    port: str = ""                 # /dev/ttyACM0, COM3…
    location: str = ""             # bus/adresse
    source: str = ""               # d'où vient l'information
    interfaces: List[str] = field(default_factory=list)
    is_phytosense: bool = False
    known_as: str = ""

    @property
    def vid_pid(self) -> str:
        return f"{self.vid:04X}:{self.pid:04X}" if (self.vid or self.pid) else "—"

    def describe(self) -> str:
        nom = self.product or self.known_as or "périphérique inconnu"
        return f"{self.vid_pid}  {nom}" + (f"  [{self.port}]" if self.port else "")

    def to_row(self) -> List[str]:
        return [self.vid_pid, self.manufacturer or "—", self.product or self.known_as
                or "—", self.serial or "—", self.port or "—", self.source]


def _from_pyserial() -> List[UsbDevice]:
    try:
        from serial.tools import list_ports
    except ImportError:
        return []
    out = []
    try:
        for p in list_ports.comports():
            d = UsbDevice(vid=int(p.vid or 0), pid=int(p.pid or 0),
                          serial=str(p.serial_number or ""),
                          manufacturer=str(p.manufacturer or ""),
                          product=str(p.product or p.description or ""),
                          port=str(p.device or ""),
                          location=str(getattr(p, "location", "") or ""),
                          source="pyserial")
            out.append(d)
    except Exception as exc:                           # pragma: no cover
        log.warning("Inventaire pyserial impossible : %s", exc)
    return out


def _from_pyusb() -> List[UsbDevice]:
    try:
        import usb.core
        import usb.util
    except Exception:
        return []
    out = []
    try:
        for dev in usb.core.find(find_all=True):
            d = UsbDevice(vid=int(dev.idVendor), pid=int(dev.idProduct),
                          location=f"bus {dev.bus} adresse {dev.address}",
                          source="pyusb")
            for attr, champ in (("iManufacturer", "manufacturer"),
                                ("iProduct", "product"),
                                ("iSerialNumber", "serial")):
                try:
                    idx = getattr(dev, attr)
                    if idx:
                        setattr(d, champ, str(usb.util.get_string(dev, idx) or ""))
                except Exception:
                    pass
            try:
                for cfg in dev:
                    for itf in cfg:
                        nom = CLASSES_USB.get(itf.bInterfaceClass,
                                              f"classe 0x{itf.bInterfaceClass:02X}")
                        if nom not in d.interfaces:
                            d.interfaces.append(nom)
            except Exception:
                pass
            out.append(d)
    except Exception as exc:                           # pragma: no cover
        log.debug("Inventaire pyusb impossible : %s", exc)
    return out


def _from_sysfs() -> List[UsbDevice]:
    """Repli universel sous Linux : aucune dépendance, tout est dans /sys."""
    base = "/sys/bus/usb/devices"
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        vid_f = os.path.join(path, "idVendor")
        if not os.path.exists(vid_f):
            continue

        def lire(champ: str) -> str:
            try:
                with open(os.path.join(path, champ), encoding="utf-8") as f:
                    return f.read().strip()
            except OSError:
                return ""
        try:
            d = UsbDevice(vid=int(lire("idVendor") or "0", 16),
                          pid=int(lire("idProduct") or "0", 16),
                          serial=lire("serial"), manufacturer=lire("manufacturer"),
                          product=lire("product"), location=name, source="sysfs")
            out.append(d)
        except ValueError:
            continue
    return out


def _from_audio() -> List[UsbDevice]:
    """Les entrées audio ne donnent pas de VID/PID, mais complètent le tableau."""
    try:
        import sounddevice as sd
    except Exception:
        return []
    out = []
    try:
        for i, dev in enumerate(sd.query_devices()):
            if dev.get("max_input_channels", 0) <= 0:
                continue
            out.append(UsbDevice(product=str(dev["name"]),
                                 location=f"audio #{i}",
                                 source="portaudio",
                                 interfaces=["audio"]))
    except Exception:                                  # pragma: no cover
        pass
    return out


def enumerate_devices(include_audio: bool = True,
                      expected: Tuple[int, int] = (PHYTOSENSE_VID,
                                                   PHYTOSENSE_PID)) -> List[UsbDevice]:
    """Inventaire consolidé, sans doublon, trié carte attendue en tête."""
    devices: List[UsbDevice] = []
    seen = set()
    for source in (_from_pyserial(), _from_pyusb(), _from_sysfs()):
        for d in source:
            cle = (d.vid, d.pid, d.serial, d.port)
            if cle in seen:
                continue
            seen.add(cle)
            devices.append(d)
    if include_audio:
        devices.extend(_from_audio())

    for d in devices:
        d.known_as = CARTES_CONNUES.get((d.vid, d.pid), "")
        d.is_phytosense = (d.vid, d.pid) == tuple(expected)
        if not d.is_phytosense and d.product:
            d.is_phytosense = "phytosense" in d.product.lower()
    devices.sort(key=lambda d: (not d.is_phytosense, not d.known_as, d.vid_pid))
    return devices


def find_phytosense(expected: Tuple[int, int] = (PHYTOSENSE_VID,
                                                 PHYTOSENSE_PID)) -> Optional[UsbDevice]:
    for d in enumerate_devices(include_audio=False, expected=expected):
        if d.is_phytosense:
            return d
    return None


# ---------------------------------------------------------------------------
#  Rapport
# ---------------------------------------------------------------------------
@dataclass
class UsbReport:
    """Résultat d'un diagnostic complet du lien USB."""
    when: str = ""
    system: str = ""
    devices: List[UsbDevice] = field(default_factory=list)
    target: Optional[UsbDevice] = None
    expected_vid: int = PHYTOSENSE_VID
    expected_pid: int = PHYTOSENSE_PID
    backends: Dict[str, bool] = field(default_factory=dict)
    verdict: str = ""
    advice: List[str] = field(default_factory=list)

    def as_text(self) -> str:
        lignes = [
            "DIAGNOSTIC DU LIEN USB",
            "======================",
            f"Date        : {self.when}",
            f"Système     : {self.system}",
            f"Attendu     : VID {self.expected_vid:04X} / PID {self.expected_pid:04X}",
            "",
            "Sources d'information :",
        ]
        for nom, dispo in self.backends.items():
            lignes.append(f"   {'[ok]' if dispo else '[--]'} {nom}")
        lignes += ["", f"{len(self.devices)} périphérique(s) énuméré(s) :", ""]
        lignes.append(f"  {'VID:PID':<10} {'FABRICANT':<18} {'PRODUIT':<30} "
                      f"{'PORT':<14} SOURCE")
        lignes.append("  " + "-" * 86)
        for d in self.devices:
            marque = "→ " if d.is_phytosense else "  "
            lignes.append(f"{marque}{d.vid_pid:<10} {(d.manufacturer or '—')[:18]:<18} "
                          f"{(d.product or d.known_as or '—')[:30]:<30} "
                          f"{(d.port or '—')[:14]:<14} {d.source}")
        lignes += ["", "VERDICT", "-------", self.verdict]
        if self.advice:
            lignes += ["", "À FAIRE", "-------"] + ["  · " + a for a in self.advice]
        return "\n".join(lignes)


def diagnose(settings=None) -> UsbReport:
    """Diagnostic complet, avec verdict et conseils concrets."""
    diag = getattr(settings, "diagnostics", None)
    vid = getattr(diag, "expected_vid", PHYTOSENSE_VID)
    pid = getattr(diag, "expected_pid", PHYTOSENSE_PID)

    rep = UsbReport(when=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    system=platform.platform(), expected_vid=vid, expected_pid=pid)
    rep.backends = {
        "pyserial (ports série)": bool(_module_present("serial")),
        "pyusb (descripteurs complets)": bool(_module_present("usb.core")),
        "sysfs Linux": os.path.isdir("/sys/bus/usb/devices"),
        "PortAudio (périphériques audio)": bool(_module_present("sounddevice")),
    }
    rep.devices = enumerate_devices(expected=(vid, pid))
    rep.target = next((d for d in rep.devices if d.is_phytosense), None)

    if rep.target is not None:
        rep.verdict = (f"Carte trouvée : {rep.target.describe()}"
                       + (f" — numéro de série {rep.target.serial}"
                          if rep.target.serial else ""))
        if not rep.target.port:
            rep.advice.append(
                "Le port série virtuel n'est pas visible : le contrôle de la "
                "carte sera indisponible, l'écoute restera possible.")
    else:
        candidats = [d for d in rep.devices if d.known_as]
        if candidats:
            rep.verdict = ("Aucune carte PhytoSense, mais un matériel connu du "
                           "domaine est branché : " +
                           ", ".join(d.known_as for d in candidats[:3]))
            rep.advice.append("Réglez la source sur « Port série » et choisissez "
                              "ce périphérique.")
        elif not any(d.vid for d in rep.devices):
            rep.verdict = ("Aucun périphérique USB identifiable. Le système ne "
                           "fournit ni VID ni PID.")
            rep.advice.append("Installez pyserial : python3 -m pip install pyserial")
        else:
            rep.verdict = ("Aucune carte PhytoSense parmi les périphériques "
                           "énumérés.")
            rep.advice.append("Vérifiez le câble : beaucoup de câbles USB-C ne "
                              "transportent que l'alimentation.")
            rep.advice.append("Essayez un autre port, de préférence à l'arrière "
                              "de la machine, sans concentrateur.")

    if platform.system() == "Linux" and rep.target is not None and rep.target.port:
        rep.advice.append(
            "Sous Linux, l'accès au port exige d'appartenir au groupe « dialout » : "
            "sudo usermod -aG dialout $USER, puis se reconnecter.")
    if not rep.backends["pyusb (descripteurs complets)"]:
        rep.advice.append("Pour les descripteurs complets : pip install pyusb")

    log.info("Diagnostic USB : %s", rep.verdict)
    return rep


def _module_present(name: str) -> bool:
    import importlib
    try:
        importlib.import_module(name)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
#  Capture de trames
# ---------------------------------------------------------------------------
class FrameCapture:
    """Enregistre les trames reçues dans un fichier — mode mise au point.

    « Trame » désigne ici un bloc d'échantillons tel qu'il est remonté par la
    source, avec son horodatage et son index. Pour une source audio, c'est le
    bloc de PortAudio ; pour une source série, le paquet lu sur le port.

    Le fichier est en texte par défaut, donc lisible immédiatement ; les
    formats hexadécimal et binaire existent pour l'analyse fine.
    """

    def __init__(self, settings):
        self.settings = settings
        self.path = ""
        self.active = False
        self.count = 0
        self.bytes = 0
        self.dropped = 0
        self._f = None
        self._lock = threading.Lock()
        self._t0 = 0.0
        self.last_error = ""

    # -- cycle de vie --------------------------------------------------------
    def start(self, label: str = "") -> Optional[str]:
        diag = self.settings.diagnostics
        if self.active:
            return self.path
        directory = self.settings.capture_dir()
        try:
            os.makedirs(directory, exist_ok=True)
        except OSError as exc:
            self.last_error = str(exc)
            log.error("Capture impossible : %s", exc)
            return None
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        ext = {"binaire": "bin", "hexa": "hex"}.get(diag.capture_format, "txt")
        self.path = os.path.join(directory, f"trames_{stamp}{('_' + label) if label else ''}.{ext}")
        #  Deux ouvertures franches plutôt qu'un mode calculé : le binaire n'a
        #  pas d'encodage, le texte en exige un — sous Windows, un `open()`
        #  sans `encoding=` lit en cp1252 et rend les accents illisibles.
        try:
            if diag.capture_format == "binaire":
                self._f = open(self.path, "wb")
            else:
                self._f = open(self.path, "w", encoding="utf-8")
        except OSError as exc:
            self.last_error = str(exc)
            log.error("Ouverture du fichier de capture impossible : %s", exc)
            return None
        self.active = True
        self.count = self.bytes = self.dropped = 0
        self._t0 = time.time()
        #  L'en-tête est du texte : il n'a de sens que dans un fichier texte.
        #  Cette ligne testait autrefois un `mode` calculé, remplacé plus haut
        #  par deux ouvertures franches — le nom n'existait plus, et démarrer
        #  une capture levait NameError. Défaut trouvé par ruff (F821) le
        #  2026-09-18, jamais rencontré parce qu'aucun test ne démarrait de
        #  capture. Il y en a un maintenant.
        if diag.capture_format != "binaire":
            self._f.write(self._header())
        log.warning("Capture de trames démarrée : %s", self.path)
        return self.path

    def _header(self) -> str:
        from .. import FULL_NAME
        a = self.settings.acquisition
        return (f"# {FULL_NAME} — capture de trames\n"
                f"# début      : {datetime.now().isoformat()}\n"
                f"# source     : {a.source} / {a.device or 'défaut'}\n"
                f"# échantill. : {a.sample_rate} Hz, {a.channels} voie(s)\n"
                f"# format     : temps_s  index  n_ech  min  max  moyenne\n"
                f"# {'-' * 72}\n")

    def stop(self) -> Optional[str]:
        with self._lock:
            if not self.active:
                return None
            self.active = False
            if self._f is not None:
                try:
                    if self.settings.diagnostics.capture_format != "binaire":
                        self._f.write(f"# fin : {self.count} trames, "
                                      f"{self.bytes} octets, "
                                      f"{time.time() - self._t0:.1f} s\n")
                    self._f.close()
                except OSError:                        # pragma: no cover
                    pass
                self._f = None
        log.warning("Capture de trames arrêtée : %d trames dans %s",
                    self.count, self.path)
        return self.path

    # -- écriture ------------------------------------------------------------
    def write(self, index: int, data) -> None:
        """Consigne une trame. Appelé depuis le fil de traitement."""
        if not self.active or self._f is None:
            return
        diag = self.settings.diagnostics
        if self.count >= diag.capture_max_frames:
            if self.active:
                log.warning("Plafond de %d trames atteint : capture arrêtée.",
                            diag.capture_max_frames)
                self.stop()
            return
        with self._lock:
            if self._f is None:
                return
            try:
                t = time.time() - self._t0
                if diag.capture_format == "binaire":
                    raw = data.astype("<f4").tobytes()
                    self._f.write(raw)
                    self.bytes += len(raw)
                elif diag.capture_format == "hexa":
                    raw = data.astype("<f4").tobytes()
                    self._f.write(f"{t:10.4f} {index:10d} {len(raw):6d} "
                                  f"{raw.hex()}\n")
                    self.bytes += len(raw)
                else:
                    flat = data.reshape(-1)
                    self._f.write(f"{t:10.4f} {index:10d} {flat.size:6d} "
                                  f"{float(flat.min()):+.9e} "
                                  f"{float(flat.max()):+.9e} "
                                  f"{float(flat.mean()):+.9e}\n")
                    self.bytes += flat.size * 4
                self.count += 1
                if self.count % 200 == 0:
                    self._f.flush()
            except Exception as exc:                   # pragma: no cover
                self.dropped += 1
                self.last_error = str(exc)

    def status(self) -> str:
        if not self.active:
            return "inactive"
        return (f"{self.count} trames · {self.bytes / 1024:.0f} ko · "
                f"{os.path.basename(self.path)}")


# ---------------------------------------------------------------------------
#  Surveillance
# ---------------------------------------------------------------------------
class LinkMonitor:
    """Surveille la présence du périphérique et compte les décrochages.

    Un lien USB qui se réénumère en cours de séance produit un trou dans les
    données. Mieux vaut le savoir et le consigner que de découvrir l'anomalie
    six mois plus tard en dépouillant les fichiers.
    """

    def __init__(self, settings):
        self.settings = settings
        self.present = False
        self.disconnections = 0
        self.reconnections = 0
        self.last_seen = 0.0
        self.last_change = 0.0
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self.on_change = None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name="usb-monitor",
                                        daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def _run(self) -> None:
        diag = self.settings.diagnostics
        period = max(float(getattr(diag, "usb_poll_seconds", 5.0)), 1.0)
        while self._running:
            found = find_phytosense((diag.expected_vid, diag.expected_pid)) is not None
            if found != self.present:
                self.last_change = time.time()
                if found:
                    self.reconnections += 1
                    log.warning("Carte réapparue sur le bus USB.")
                else:
                    self.disconnections += 1
                    log.error("Carte disparue du bus USB.")
                self.present = found
                if self.on_change:
                    try:
                        self.on_change(found)
                    except Exception:                  # pragma: no cover
                        pass
            if found:
                self.last_seen = time.time()
            time.sleep(period)

    def summary(self) -> str:
        if self.present:
            return f"lien stable — {self.disconnections} décrochage(s) depuis le début"
        if self.last_seen:
            return (f"carte absente depuis "
                    f"{time.time() - self.last_seen:.0f} s "
                    f"({self.disconnections} décrochage(s))")
        return "carte jamais vue sur le bus"
