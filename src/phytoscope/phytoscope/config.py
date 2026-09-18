# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/config.py
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

"""Réglages de l'application : modèle, valeurs par défaut, persistance.

Un seul objet `Settings` décrit tout le comportement du logiciel. Il est
sérialisé en JSON dans le répertoire de configuration de l'utilisateur, et
peut être exporté / importé sous forme de « profil » — ce qui permet de
transporter un réglage d'atelier d'une machine à l'autre.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict, fields
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
#  Emplacements
# ---------------------------------------------------------------------------
def config_dir() -> str:
    """Répertoire de configuration, selon les usages de chaque système."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "PhytoScope")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/PhytoScope")
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "phytoscope")


def data_dir() -> str:
    """Répertoire des séances enregistrées."""
    if sys.platform.startswith("win"):
        base = os.environ.get("USERPROFILE") or os.path.expanduser("~")
        return os.path.join(base, "Documents", "PhytoScope")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Documents/PhytoScope")
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return os.path.join(base, "phytoscope", "seances")


# ---------------------------------------------------------------------------
#  Sections de réglages
# ---------------------------------------------------------------------------
@dataclass
class AcquisitionSettings:
    source: str = "auto"              # auto | phytosense | audio | serie | fichier | simulation
    device: str = ""                  # nom du périphérique audio ou port série
    sample_rate: float = 250.0        # Hz
    channels: int = 1
    block_size: int = 64              # échantillons par bloc remonté
    hardware_gain: int = 0            # 0 = automatique ; sinon 1,2,5,…,200
    input_range_v: float = 2.5        # pleine échelle du convertisseur
    volts_per_unit: float = 1.0       # étalonnage : unité source → volt
    invert: bool = False


@dataclass
class ProcessingSettings:
    highpass_hz: float = 0.01         # 0 = désactivé
    lowpass_hz: float = 40.0          # 0 = désactivé
    notch_hz: float = 50.0            # 0 = désactivé ; 50 ou 60
    notch_q: float = 30.0
    detrend_seconds: float = 120.0    # fenêtre de la ligne de base
    smoothing_ms: float = 0.0
    event_threshold_sigma: float = 3.5
    event_refractory_ms: float = 400.0
    event_min_amplitude_uv: float = 8.0


@dataclass
class MusicSettings:
    enabled: bool = True
    scale: str = "pentatonique_majeure"
    root: str = "D"
    diapason_hz: float = 440.0        # 440 | 432 | 426.7 | 415
    profile: str = ""                 # profil préréglé appliqué en dernier
    polyphony_voices: int = 3         # 1 = monodique, 3 = comme le U1 Pro
    chorus: float = 0.0               # 0 à 1
    pan: float = 0.0                  # −1 (gauche) à +1 (droite)
    spatial: float = 0.0              # effet d'espace, 0 à 1
    gm_program: int = -1              # -1 = timbre interne ; 0..127 = General MIDI
    octave_low: int = 3
    octave_span: int = 3
    instrument: str = "kalimba"
    velocity_min: int = 40
    velocity_max: int = 120
    note_len_min_s: float = 0.25
    note_len_max_s: float = 4.0
    density_per_min: float = 24.0
    quantize_ms: float = 0.0          # 0 = temps réel, sinon grille
    reverb: float = 0.35
    master_gain_db: float = -6.0
    midi_enabled: bool = False
    midi_port: str = ""
    midi_channel: int = 1
    drone_enabled: bool = True


@dataclass
class VoiceSettings:
    """Mode vocal : des mots au lieu des notes.

    Le moteur lexical produit un énoncé court à partir des mêmes événements
    que le moteur musical. Ce n'est pas une traduction — voir l'avertissement
    en tête de :mod:`phytoscope.music.lexicon` — et chaque réglage d'ici
    modifie la grille de lecture, jamais le signal.
    """
    enabled: bool = False
    lexicon_path: str = ""            # vide = le dictionnaire livré
    grammar: str = "contemplative"    # minimale | telegraphique | contemplative | descriptive
    subject_position: float = 0.0     # quel sujet, dans son registre : 0 à 1
    density_per_min: float = 6.0      # énoncés par minute, au plus
    tempo_scale_s: float = 120.0      # durée qui sature le registre « tempo »
    spoken: bool = True               # prononcer à voix haute
    muted: bool = False               # couper la voix sans couper les énoncés
    #  Une voix et un synthétiseur qui jouent ensemble ne s'entendent ni l'un
    #  ni l'autre : la musique se tait pendant le mode vocal, sauf demande
    #  contraire. C'est le réglage qui fait la différence entre « ça ne marche
    #  pas » et « ça parle ».
    mute_music: bool = True           # couper la musique tant que la parole est active
    lexicon_auto: bool = True         # suivre la langue de l'interface
    lexicon_code: str = ""            # dictionnaire livré imposé ; vide = suivre
    backend: str = "auto"             # auto | pyttsx3 | say | SAPI | espeak-ng | silencieuse
    voice_id: str = ""                # identifiant de voix propre au moteur
    rate_wpm: int = 150               # débit, en mots par minute
    volume: float = 0.9               # 0 à 1
    write_csv: bool = True            # enonces.csv dans la séance


@dataclass
class FeaturesSettings:
    """Descripteurs avancés : FFT, ondelettes, MFCC, LPC, cepstre.

    Les constantes sont exprimées en secondes et en hertz, jamais en nombre
    d'échantillons : elles restent donc valables si la fréquence
    d'échantillonnage change.
    """
    representation: str = "ondelettes"   # temporel | frequentiel | ondelettes | mfcc | lpc | cepstre
    window_s: float = 120.0              # durée de signal analysée
    auto_refresh_s: float = 2.0          # 0 = calcul à la demande seulement
    fft_window: str = "hann"             # hann | hamming | blackman | rectangulaire
    fft_zero_padding: int = 2
    wavelet_scales: int = 48
    wavelet_omega0: float = 6.0
    wavelet_f_min_hz: float = 0.0        # 0 = automatique (2 périodes / fenêtre)
    wavelet_f_max_hz: float = 0.0        # 0 = automatique (Nyquist / 2,5)
    wavelet_decimation: int = 0          # 0 = choisi pour tenir à l'écran
    mfcc_count: int = 13
    mfcc_filters: int = 26
    mfcc_frame_s: float = 8.0
    mfcc_overlap: float = 0.5
    lpc_order: int = 0                   # 0 = automatique (2 + fs/25)
    cepstrum_q_min_s: float = 0.0        # 0 = automatique
    cepstrum_q_max_s: float = 0.0        # 0 = automatique


@dataclass
class RecordingSettings:
    directory: str = field(default_factory=data_dir)
    auto_start: bool = False
    write_wav: bool = True            # signal brut, 24 bits
    write_audio: bool = True          # rendu musical
    write_csv: bool = True            # événements
    write_raw_csv: bool = False       # toutes les valeurs (gros fichiers)
    split_hours: float = 6.0
    note_template: str = "{plante} — {lieu}"
    #  Surveillance du disque. La réserve n'est pas pour le logiciel mais pour
    #  le système : un disque réellement plein empêche d'écrire les réglages et
    #  le journal, et parfois d'ouvrir une session. On s'arrête avant.
    #  Durée gardée par un « échantillon » : la mémoire de signal en contient
    #  dix minutes, et l'essentiel arrive souvent avant qu'on ait pensé à
    #  enregistrer.
    sample_seconds: float = 60.0
    watch_disk: bool = True           # surveiller l'espace pendant l'enregistrement
    reserve_mb: float = 500.0         # on clôt la séance en deçà
    warn_minutes: float = 20.0        # on prévient quand il reste moins que cela


@dataclass
class SamplingSettings:
    """Module d'échantillonnage — ce qui est prélevé, et comment."""
    mode: str = "continu"             # continu | bloc | declenche
    block_samples: int = 2048         # taille d'un bloc en mode « bloc »
    decimation: int = 1               # moyenne de N échantillons consécutifs
    averaging: int = 1                # moyennage de N blocs successifs
    window: str = "hann"              # rectangle | hann | hamming | blackman | flattop
    trigger_source: str = "signal"    # signal | manuel | externe
    trigger_mode: str = "auto"        # auto | normal | unique
    trigger_level_uv: float = 50.0
    trigger_edge: str = "montant"     # montant | descendant | les_deux
    pretrigger_percent: float = 20.0
    holdoff_ms: float = 250.0
    accumulate: bool = False          # empiler les blocs (persistance)
    max_blocks: int = 64


@dataclass
class AudioOutSettings:
    """Sortie sonore : amplification, compression, bip de repérage."""
    device: str = ""
    gain_db: float = 0.0              # gain de sortie, avant limiteur
    boost_db: float = 0.0             # amplification supplémentaire (0 à +36 dB)
    compressor: bool = True           # indispensable sur haut-parleur de portable
    comp_threshold_db: float = -24.0
    comp_ratio: float = 4.0
    presence_boost_db: float = 0.0    # remontée 1–4 kHz pour petits haut-parleurs
    limiter: bool = True
    beep_enabled: bool = False        # bip à chaque événement détecté
    beep_freq_hz: float = 880.0
    beep_ms: float = 70.0
    beep_gain_db: float = -12.0
    beep_on_saturation: bool = True
    beep_on_event: bool = True
    # Taille de bloc et latence de la sortie audio. Un bloc plus grand coûte
    # moins cher en interruptions et supprime les coupures sur les machines
    # chargées ; il ajoute en contrepartie quelques millisecondes de retard,
    # sans conséquence ici puisque la plante n'attend pas de réponse.
    # Valeurs déterminées par mesure : un bloc de 4096 échantillons et une
    # demi-seconde de latence suppriment les décrochages de la couche ALSA,
    # sans conséquence pour l'usage — une plante n'attend pas de réponse.
    block_size: int = 4096
    latency: str = "0.5"           # low | high | valeur en secondes
    # « ecriture » : un fil dédié appelle stream.write(), qui libère le verrou
    # global pendant qu'il bloque — l'interface graphique ne peut donc plus
    # affamer la sortie. « rappel » : tampon circulaire pré-rempli, utile là
    # où l'écriture bloquante se comporte mal.
    mode: str = "ecriture"         # ecriture | rappel
    quiet: bool = True             # étouffer le bavardage d'ALSA et de JACK


@dataclass
class LoggingSettings:
    """Journalisation : fichier, niveau, rotation."""
    level: str = "ERROR"              # ERROR | WARNING | INFO | DEBUG
    to_file: bool = True
    to_console: bool = False
    directory: str = ""               # vide = répertoire de configuration
    filename: str = "phytoscope.log"
    max_bytes: int = 2_000_000
    backup_count: int = 3
    log_frames: bool = False          # journalise chaque bloc reçu (très verbeux)


@dataclass
class DiagnosticsSettings:
    """Diagnostic bas niveau : USB, trames, mode de mise au point."""
    debug_mode: bool = False          # active les fonctions de mise au point
    capture_usb_frames: bool = False  # enregistre les trames dans un fichier
    capture_directory: str = ""       # vide = répertoire de configuration
    capture_max_frames: int = 200000
    capture_format: str = "texte"     # texte | binaire | hexa
    usb_poll_seconds: float = 5.0     # période de surveillance du lien USB
    #  Doivent rester alignés sur `core.protocol.USB_VID` / `USB_PID`, que le
    #  micrologiciel fixe. Un essai le vérifie.
    expected_vid: int = 0x1209        # pid.codes
    expected_pid: int = 0x7A01        # PhytoSense One


@dataclass
class UISettings:
    theme: str = "sombre"             # sombre | clair | contraste
    #  Le français au premier lancement, **quelle que soit la locale du
    #  système**. C'est délibéré et il ne faut pas l'« améliorer » en ajoutant
    #  une détection automatique : l'ouvrage, les planches, le dictionnaire du
    #  mode vocal et les messages de l'auteur sont en français, et un logiciel
    #  de mesure dont l'interface ne correspond pas à sa documentation coûte
    #  plus cher qu'il ne rapporte. Chacun choisit ensuite sa langue dans les
    #  réglages, ou par « --lang » ; ce choix, lui, est conservé.
    language: str = "fr"
    refresh_hz: int = 30
    scope_window_s: float = 60.0
    scope_volts_per_div: float = 200e-6
    show_expert: bool = False
    accessible_font_scale: float = 1.0


@dataclass
class ModulesSettings:
    """Ce que l'utilisateur a décidé des modules.

    Le fichier ne contient que les **exceptions** : les modules qu'on a
    désactivés, et les réglages qu'on a changés. Un module posé dans le
    dossier des modules est actif par défaut — l'y poser est déjà un choix, et
    demander deux fois la même chose est une manière de ne pas être cru.
    """
    desactives: List[str] = field(default_factory=list)
    #  Les réglages de chaque module, par son nom. L'hôte ne les interprète
    #  pas : il les conserve et les rend au module.
    reglages: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    #  Charger les modules au démarrage. Le mettre à faux permet de démarrer
    #  sans eux quand l'un d'eux empêche le logiciel de s'ouvrir — c'est le
    #  « mode sans échec » des modules.
    charger_au_demarrage: bool = True


@dataclass
class Settings:
    acquisition: AcquisitionSettings = field(default_factory=AcquisitionSettings)
    sampling: SamplingSettings = field(default_factory=SamplingSettings)
    processing: ProcessingSettings = field(default_factory=ProcessingSettings)
    music: MusicSettings = field(default_factory=MusicSettings)
    voice: VoiceSettings = field(default_factory=VoiceSettings)
    features: FeaturesSettings = field(default_factory=FeaturesSettings)
    audio_out: AudioOutSettings = field(default_factory=AudioOutSettings)
    recording: RecordingSettings = field(default_factory=RecordingSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    diagnostics: DiagnosticsSettings = field(default_factory=DiagnosticsSettings)
    modules: ModulesSettings = field(default_factory=ModulesSettings)
    ui: UISettings = field(default_factory=UISettings)
    metadata: Dict[str, str] = field(default_factory=lambda: {
        "plante": "", "lieu": "", "operateur": "", "notes": ""})

    #  Vrai quand aucun fichier de réglages n'existait au démarrage. Sert à
    #  une chose : demander la langue, une fois. Il n'est PAS écrit dans le
    #  fichier — c'est une observation du démarrage, pas un réglage —, d'où
    #  son exclusion dans `to_dict`.
    premier_lancement: bool = False

    # -- valeurs imposées en ligne de commande -------------------------------
    #  Une option passée au lancement — « --lang ja », « --simulation »,
    #  « --theme contraste » — vaut **pour cette séance seulement**. La rendre
    #  permanente serait un piège : on lance une fois le logiciel en simulation
    #  pour montrer quelque chose, et six mois plus tard il n'a jamais ouvert la
    #  carte sans qu'on sache pourquoi. Les valeurs d'origine sont donc retenues
    #  et remises au moment d'écrire le fichier de réglages.
    #
    #  Sauf si l'utilisateur change le réglage lui-même pendant la séance : dans
    #  ce cas c'est bien son choix qui est écrit, puisque la valeur courante ne
    #  correspond plus à celle qui avait été imposée.
    def __post_init__(self) -> None:
        self._imposes: Dict[Any, Any] = {}

    def forcer(self, section: str, champ: str, valeur) -> None:
        """Impose une valeur pour cette séance, sans l'inscrire dans le fichier."""
        cible = getattr(self, section, None)
        if cible is None or not hasattr(cible, champ):
            return
        if not hasattr(self, "_imposes"):
            self._imposes = {}
        origine = self._imposes.get((section, champ), (getattr(cible, champ),))[0]
        self._imposes[(section, champ)] = (origine, valeur)
        setattr(cible, champ, valeur)

    def _rendre_les_valeurs_dorigine(self, donnees: Dict[str, Any]) -> Dict[str, Any]:
        for (section, champ), (origine, impose) in getattr(self, "_imposes", {}).items():
            courant = getattr(getattr(self, section), champ, None)
            if courant == impose and section in donnees:
                donnees[section][champ] = origine
        return donnees

    # -- (dé)sérialisation ---------------------------------------------------
    def to_dict(self, persistant: bool = False) -> Dict[str, Any]:
        """Les réglages en dictionnaire.

        `persistant` retire ce qui n'a été imposé que pour la séance en cours :
        c'est la forme qu'on écrit sur le disque, et elle seule.
        """
        donnees = asdict(self)
        #  `premier_lancement` observe le démarrage, il ne se règle pas :
        #  l'écrire ferait croire, au lancement suivant, que c'est encore le
        #  premier.
        donnees.pop("premier_lancement", None)
        return self._rendre_les_valeurs_dorigine(donnees) if persistant else donnees

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Settings":
        s = cls()
        for f in fields(cls):
            if f.name not in d:
                continue
            cur = getattr(s, f.name)
            val = d[f.name]
            if hasattr(cur, "__dataclass_fields__") and isinstance(val, dict):
                for sub in fields(cur):
                    if sub.name in val:
                        setattr(cur, sub.name, val[sub.name])
            elif isinstance(cur, dict) and isinstance(val, dict):
                cur.update(val)
        return s

    # -- fichiers ------------------------------------------------------------
    @staticmethod
    def default_path() -> str:
        return os.path.join(config_dir(), "reglages.json")

    def save(self, path: str | None = None) -> str:
        path = path or self.default_path()
        #  `--settings reglages.json` donne un chemin relatif nu, dont le
        #  répertoire est la chaîne vide : `makedirs("")` lève.
        dossier = os.path.dirname(path)
        if dossier:
            os.makedirs(dossier, exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(persistant=True), f, ensure_ascii=False,
                      indent=2)
        os.replace(tmp, path)
        return path

    @classmethod
    def load(cls, path: str | None = None) -> "Settings":
        path = path or cls.default_path()
        if not os.path.exists(path):
            #  Aucun fichier : c'est le premier lancement. L'interface s'en
            #  sert pour demander la langue — une fois, et jamais ensuite.
            #  On ne DEVINE pas la locale (`C-31`) : on pose la question.
            reglages = cls()
            reglages.premier_lancement = True
            return reglages
        try:
            with open(path, encoding="utf-8") as f:
                return cls.from_dict(json.load(f))
        except (OSError, ValueError):
            # Un fichier corrompu ne doit jamais empêcher le logiciel de démarrer.
            return cls()

    def log_path(self) -> str:
        d = self.logging.directory or config_dir()
        return os.path.join(d, self.logging.filename)

    def capture_dir(self) -> str:
        return self.diagnostics.capture_directory or os.path.join(config_dir(),
                                                                  "captures")

    def profiles_dir(self) -> str:
        return os.path.join(config_dir(), "profils")

    def list_profiles(self) -> List[str]:
        d = self.profiles_dir()
        if not os.path.isdir(d):
            return []
        return sorted(n[:-5] for n in os.listdir(d) if n.endswith(".json"))

    def export_profile(self, name: str) -> str:
        d = self.profiles_dir()
        os.makedirs(d, exist_ok=True)
        return self.save(os.path.join(d, f"{name}.json"))
