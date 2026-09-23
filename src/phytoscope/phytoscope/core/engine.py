# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — src/phytoscope/phytoscope/core/engine.py
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

"""Le engine : ce qui relie la source, le traitement, la musique et le disque.

Trois fils d'exécution, deux files, aucune dépendance à l'interface :

    source ──▶ file brute ──▶ fil de traitement ──▶ état partagé ──▶ interface
                                    │
                                    ├──▶ synthétiseur (fil audio de PortAudio)
                                    ├──▶ sortie MIDI
                                    ├──▶ engine lexical ──▶ synthèse vocale
                                    └──▶ enregistreur (disque)

Le engine lexical est le jumeau du engine musical : mêmes événements en
entrée, mêmes kept-fous de densité, une phrase au lieu d'une note en sortie.
Les deux peuvent tourner ensemble ou séparément.

L'interface graphique ne fait que **read** l'état partagé à sa propre
cadence (30 im/s). Elle ne peut donc jamais ralentir l'acquisition : c'est
la règle qui rend l'application usable sur une machine modeste pendant
une séance de plusieurs heures.
"""
from __future__ import annotations

import os
import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from ..i18n import t
from ..music.amplifier import OutputStage
from ..music.lexicon import Enonce, VocalMapper
from ..music.mapper import Mapper, Note
from ..music.midi_out import MidiOut
from ..music.synth import AudioOutput, Synth
from ..music.voice import VoiceOutput
from .dsp import (Baseline, Chain, Event, EventDetector, RunningStats,
                  build_chain, welch_psd)
from . import disk_space, samples
from .errors import resilient
from .logging_setup import get_logger
from .protocol import BoardInfo, ControlLink
from .recorder import Recorder
from .sampling import SampleBlock, Sampler
from .sources import Block, Source, autodetect
from .usbdiag import FrameCapture, LinkMonitor

log = get_logger(__name__)


def asdict_leger(section) -> Dict[str, Any]:
    """Les champs simples d'une section de réglages — pour les métadonnées."""
    return {k: v for k, v in vars(section).items()
            if isinstance(v, (int, float, str, bool))}


@dataclass
class EngineState:
    """Instantané de l'état du engine, lu par l'interface."""
    running: bool = False
    source_name: str = ""
    source_kind: str = ""
    samples: int = 0
    elapsed_s: float = 0.0
    value_v: float = 0.0
    baseline_v: float = 0.0
    rms_v: float = 0.0
    pp_v: float = 0.0
    sigma_v: float = 0.0
    drift_v_per_min: float = 0.0
    saturated: bool = False
    events_total: int = 0
    notes_total: int = 0
    enonces_total: int = 0
    last_event: Optional[Event] = None
    last_note: Optional[Note] = None
    last_enonce: Optional[Enonce] = None
    recording: bool = False
    record_dir: str = ""
    record_elapsed: float = 0.0
    # -- espace disque ------------------------------------------------------
    disk_free_mb: float = 0.0
    disk_total_mb: float = 0.0
    disk_hours_left: float = 0.0     # au débit d'écriture courant
    disk_alert: bool = False         # il reste moins que le seuil d'alert
    dropped_blocks: int = 0
    cpu_load: float = 0.0
    board: Optional[BoardInfo] = None
    messages: List[str] = field(default_factory=list)
    # -- sortie audio et diagnostic ----------------------------------------
    audio_peak_db: float = -99.0
    audio_reduction_db: float = 0.0
    audio_clips: int = 0
    usb_present: bool = False
    usb_disconnections: int = 0
    capture_active: bool = False
    capture_frames: int = 0
    blocks_sampled: int = 0
    # -- mode vocal ---------------------------------------------------------
    voice_backend: str = ""
    voice_spoken: int = 0
    voice_dropped: int = 0
    centroid_hz: float = 0.0
    # -- replaying ----------------------------------------------------------
    replaying: bool = False          # le signal vient d'un file_path, pas d'une plante
    replay_name: str = ""
    replay_position: float = 0.0     # seconds écoulées dans l'enregistrement
    replay_length: float = 0.0
    # -- échantillons -------------------------------------------------------
    samples_total: int = 0
    last_sample: str = ""


class Engine:
    """Orchestrateur. Utilisable sans interface (scripts, mesures en lot)."""

    RING_SECONDS = 600.0            # dix minutes de signal gardées en mémoire

    def __init__(self, settings):
        self.settings = settings
        self.state = EngineState()
        self.lock = threading.RLock()

        self.raw_q: "queue.Queue[Block]" = queue.Queue(maxsize=256)
        self.source: Optional[Source] = None
        self.control = ControlLink()
        self.recorder: Optional[Recorder] = None

        self.synth = Synth(44100)
        self.output = OutputStage(44100, settings)
        self.audio = AudioOutput(self.synth, settings.audio_out.device or None,
                                 settings.audio_out.block_size, self.output,
                                 settings.audio_out.latency,
                                 mode=settings.audio_out.mode)
        self.midi = MidiOut()
        self.mapper = Mapper(settings)
        self.vocal = VocalMapper(settings)

        #  Le registre des modules. Créé ici, chargé au démarrage : un module
        #  doit pouvoir s'subscribe avant que la première mesure n'arrive.
        #  `charger_au_demarrage = False` permet d'open le logiciel sans eux
        #  quand l'un d'eux empêche de démarrer — le mode sans échec.
        from ..api import Registry
        self.modules = Registry(self, settings)
        self.voice = VoiceOutput(settings)
        self.sampler = Sampler(settings)
        self.capture = FrameCapture(settings)
        self.monitor = LinkMonitor(settings)

        self._chain: Optional[Chain] = None
        self._baseline: Optional[Baseline] = None
        self._detector: Optional[EventDetector] = None
        self._stats: Optional[RunningStats] = None

        self._ring: Optional[np.ndarray] = None
        self._ring_raw: Optional[np.ndarray] = None
        self._ring_pos = 0
        self._ring_filled = 0

        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._drift_t0 = 0.0
        self._drift_v0 = 0.0
        self._centroid_t = 0.0
        self._disque_t = 0.0
        self._disque_prevenu = False
        self._fs_avant_relecture: Optional[float] = None
        self._evenements_recents: List[float] = []
        self._signature: tuple = ()

        self.on_event: Optional[Callable[[Event], None]] = None
        self.on_note: Optional[Callable[[Note], None]] = None
        self.on_enonce: Optional[Callable[[Enonce], None]] = None
        self.on_message: Optional[Callable[[str], None]] = None

    # ------------------------------------------------------------------ setup
    def _message(self, text: str) -> None:
        with self.lock:
            self.state.messages.append(text)
            self.state.messages = self.state.messages[-50:]
        if self.on_message:
            try:
                self.on_message(text)
            except Exception:                          # pragma: no cover
                pass

    def _signature_traitement(self) -> tuple:
        """Les seuls réglages dont dépend la chaîne de traitement."""
        a, p = self.settings.acquisition, self.settings.processing
        return (a.sample_rate, p.highpass_hz, p.lowpass_hz, p.notch_hz,
                p.notch_q, p.detrend_seconds, p.event_threshold_sigma,
                p.event_refractory_ms, p.event_min_amplitude_uv)

    def _rebuild_processing(self, force: bool = False) -> None:
        """Reconstruit filtres, détecteur et mémoire de signal — si besoin.

        Reconstruire coûte la **mémoire de signal** : les dix minutes gardées
        pour l'oscilloscope, l'analyseur et les descripteurs sont remises à
        zéro, et les filtres repartent de leur état initial. Le faire à chaque
        mouvement d'un curseur de volume — ce qui arrivait, tous les réglages
        passant par le même callback — effaçait donc ce qu'on était en train de
        regarder. On ne reconstruit plus que si un réglage de la chaîne a
        réellement changé ; le reste ne fait que se resynchroniser.
        """
        signature = self._signature_traitement()
        if not force and self._chain is not None and signature == self._signature:
            self.mapper.refresh()
            self.vocal.refresh()
            return
        self._signature = signature
        fs = self.settings.acquisition.sample_rate
        p = self.settings.processing
        self._chain = build_chain(fs, p.highpass_hz, p.lowpass_hz, p.notch_hz,
                                  p.notch_q)
        self._baseline = Baseline(fs, p.detrend_seconds)
        self._detector = EventDetector(fs, p.event_threshold_sigma,
                                       p.event_refractory_ms,
                                       p.event_min_amplitude_uv * 1e-6)
        self._stats = RunningStats(fs, 30.0)
        n = int(fs * self.RING_SECONDS)
        self._ring = np.zeros(n, dtype=np.float64)
        self._ring_raw = np.zeros(n, dtype=np.float64)
        self._ring_pos = 0
        self._ring_filled = 0
        self._centroid_t = 0.0
        self.mapper.refresh()
        self.vocal.refresh()

    def apply_settings(self) -> None:
        """À call après toute modification des réglages."""
        self._rebuild_processing()
        m = self.settings.music
        self.synth.reverb_amount = m.reverb
        self.synth.master = 10 ** (m.master_gain_db / 20.0)
        drone = self.mapper.drone_note()
        self.synth.set_drone(drone if (m.drone_enabled and not self.musique_coupee())
                             else None)
        self.output.apply_settings()
        self.sampler.reconfigure()
        self.synth.diapason = m.diapason_hz
        # La polyphonie demandée limite le nombre de voix simultanées, comme
        # le sélecteur « Note 3/1 » du U1 Pro.
        self.synth.polyphonie_max = max(int(m.polyphony_voices), 1)
        self.appliquer_voix()

    def musique_coupee(self) -> bool:
        """Vrai quand le mode vocal impose le silence au synthétiseur.

        Une voix et un instrument qui jouent en même temps se couvrent l'un
        l'autre : on entend une bouillie, et l'on conclut que la parole ne
        fonctionne pas. Le mode vocal fait donc taire la musique par défaut —
        la détection, elle, continue exactement comme avant.
        """
        v = getattr(self.settings, "voice", None)
        return bool(v is not None and v.enabled and v.mute_music)

    def appliquer_voix(self) -> None:
        """Ouvre la synthèse vocale si elle est demandée, la ferme sinon.

        La règle est la même que pour le MIDI : rien n'est ouvert tant que
        l'utilisateur n'en a pas besoin, et une absence de synthétiseur n'est
        jamais une erreur — les énoncés restent écrits.
        """
        v = self.settings.voice
        veut_parler = bool(v.enabled and v.spoken)
        if veut_parler and not self.voice.actif:
            if self.voice.demarrer():
                self._message(t("Speech synthesis: {engine}").format(
                    engine=self.voice.backend))
            else:
                self._message(t("No speech synthesis installed: utterances will be written but not spoken."))
        elif not veut_parler and self.voice.actif:
            self.voice.arreter()
        with self.lock:
            self.state.voice_backend = self.voice.backend if self.voice.actif else ""

    # ------------------------------------------------------------------ start
    def start(self) -> bool:
        if self._running:
            return True
        self._rebuild_processing(force=True)
        self._charger_les_modules()

        self.source = autodetect(self.raw_q, self.settings)
        if not self.source.start():
            self._message(self.source.last_error or t("source unavailable"))
            from .sources import SimulatedSource
            self.source = SimulatedSource(self.raw_q,
                                          self.settings.acquisition.sample_rate,
                                          max(self.settings.acquisition.channels, 1))
            self.source.start()
            self._message(t("Falling back to the internal generator: you can work with no hardware."))

        # contrôle de la carte, facultatif
        if self.source.info.kind in ("audio", "serie"):
            if self.control.open():
                info = self.control.identify()
                if info is not None:
                    with self.lock:
                        self.state.board = info
                    self.source.info.board = info
                    self._message(t("Board detected: {carte}").format(
                        carte=info.describe()))
            elif self.control.last_error:
                self._message(self.control.last_error)

        if not self.audio.start():
            self._message(self.audio.last_error or t("audio output unavailable"))
        else:
            self.audio.tap = self._audio_tap

        if self.settings.music.midi_enabled:
            if self.midi.open(self.settings.music.midi_port):
                self.midi.program(self.mapper.gm_program(),
                                  self.settings.music.midi_channel)
                self._message(t("MIDI output: {port}").format(port=self.midi.port_name))
            else:
                self._message(self.midi.last_error)

        self.apply_settings()

        if self.settings.diagnostics.capture_usb_frames:
            path = self.capture.start()
            if path:
                self._message(t("Frame capture: {path}").format(path=path))
        if self.settings.diagnostics.debug_mode:
            self.monitor.on_change = self._usb_change
            self.monitor.start()

        self._demarrer_traitement()

        with self.lock:
            self.state.running = True
            self.state.source_name = self.source.info.name
            self.state.source_kind = self.source.info.kind
        if self.settings.recording.auto_start:
            self.start_recording()
        return True

    def _demarrer_traitement(self, name: str = "traitement") -> None:
        """Lance le fil qui filtre, mesure et sonifie. Idempotent."""
        if self._running and self._thread is not None:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()

    def _arreter_traitement(self) -> None:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def stop(self) -> None:
        self.stop_recording()
        #  Les modules d'abord : l'un d'eux peut vouloir écrire quelque chose
        #  en se refermant, et il lui faut un engine encore debout pour cela.
        self._arreter_les_modules()
        self._arreter_traitement()
        if self.source is not None:
            self.source.stop()
        self.synth.all_off()
        self.voice.arreter()
        self.audio.stop()
        if self.midi.is_open:
            self.midi.panic()
            self.midi.close()
        self.control.close()
        self.monitor.stop()
        self.capture.stop()
        with self.lock:
            self.state.running = False
            self.state.replaying = False

    # ---------------------------------------------------------------- modules
    def _charger_les_modules(self) -> None:
        """Découvre et installe les modules. Jamais fatal.

        Un module qui échoue est désactivé et inscrit au log ; le logiciel
        continue. Une panne du registre lui-même — ce qui ne devrait pas
        arriver — n'empêche pas non plus la mesure de commencer : measure est
        la raison d'être du logiciel, les modules en sont l'agrément.
        """
        if not getattr(self.settings.modules, "charger_au_demarrage", True):
            log.info("Modules non chargés : désactivés dans les réglages.")
            return
        try:
            self.modules.discover()
            active = self.modules.load_all()
            total = len(self.modules.modules)
            log.info("Modules : %d actif(s) sur %d découvert(s).", active, total)
            en_faute = [m for m in self.modules.modules.values()
                        if m.fault]
            for m in en_faute:
                self._message(t("Module « {name} » disabled: {raison}").format(
                    name=m.name, raison=m.fault))
        except Exception as exc:                           # noqa: BLE001
            log.error("Chargement des modules impossible : %s: %s",
                      type(exc).__name__, exc)

    def _arreter_les_modules(self) -> None:
        try:
            self.settings.modules.reglages.update(
                self.modules.collect_settings())
            self.modules.shutdown_all()
        except Exception as exc:                           # noqa: BLE001
            log.error("Arrêt des modules : %s: %s", type(exc).__name__, exc)

    def publish(self, event: str, *args, **kwargs) -> None:
        """Annonce un événement aux modules abonnés.

        Appelé depuis le fil de l'interface, jamais depuis celui des données :
        un module lent ralentit l'affichage, il ne fait pas tomber un
        échantillon (`C-20`, `C-28`).
        """
        try:
            from ..api.events import BUS
            BUS.publish(event, *args, **kwargs)
        except Exception as exc:                           # noqa: BLE001
            log.error("Publication de « %s » : %s", event, exc)

    # ------------------------------------------------------------- traitement
    def _run(self) -> None:
        fs = self.settings.acquisition.sample_rate
        invert = -1.0 if self.settings.acquisition.invert else 1.0
        full_scale = self.settings.acquisition.input_range_v
        while self._running:
            try:
                start_index, block = self.raw_q.get(timeout=0.2)
            except queue.Empty:
                continue
            t_begin = time.perf_counter()
            x = np.asarray(block, dtype=np.float64)
            if x.ndim == 2:
                x = x[:, 0]
            x = x * invert

            if self.capture.active:
                self.capture.write(start_index, x)
            if self.recorder is not None and self.recorder.active:
                self.recorder.write_signal(block)
            self.sampler.feed(start_index, x)

            filtered = self._chain.process(x) if self._chain else x
            centred = self._baseline.process(filtered) if self._baseline else filtered
            self._push_ring(centred, x)
            if self._stats is not None:
                self._stats.push(centred)

            events: List[Event] = []
            if self._detector is not None:
                events = self._detector.process(centred, start_index)

            for ev in events:
                self._handle_event(ev)

            self._maj_centroide()
            self._surveiller_disque()

            self._update_state(x, centred, start_index, fs, full_scale,
                               time.perf_counter() - t_begin,
                               block.shape[0] / fs if fs else 0.0)

    def _handle_event(self, ev: Event) -> None:
        with self.lock:
            self.state.events_total += 1
            self.state.last_event = ev
            #  Gardés pour dire combien d'événements contient un échantillon.
            self._evenements_recents.append(ev.time_s)
            if len(self._evenements_recents) > 4000:
                del self._evenements_recents[:2000]
        if self.recorder is not None:
            self.recorder.write_event(ev)
        if self.on_event:
            try:
                self.on_event(ev)
            except Exception:                          # pragma: no cover
                pass
        if self.settings.audio_out.beep_enabled and \
                self.settings.audio_out.beep_on_event:
            self.output.bip("event")

        self._handle_enonce(ev)

        if self.musique_coupee():
            return                     # la parole a la place ; rien n'est joué

        note = self.mapper.map_event(ev)
        if note is None:
            return
        self.synth.note_on(note.midi, note.velocity, note.duration,
                           note.instrument)
        if self.midi.is_open:
            self.midi.note(note.midi, note.velocity, note.duration,
                           self.settings.music.midi_channel)
        with self.lock:
            self.state.notes_total += 1
            self.state.last_note = note
        if self.recorder is not None:
            self.recorder.write_note(note)
        if self.on_note:
            try:
                self.on_note(note)
            except Exception:                          # pragma: no cover
                pass

    def _handle_enonce(self, ev: Event) -> None:
        """Le versant lexical de l'événement : une phrase, peut-être.

        Peut-être seulement : le engine lexical a sa propre limite de densité,
        volontairement plus basse que celle de la musique. Une plante qui
        « parlerait » vingt fois par minute ne serait pas écoutée.
        """
        if not self.settings.voice.enabled:
            return
        enonce = self.vocal.map_event(ev)
        if enonce is None:
            return
        with self.lock:
            self.state.enonces_total += 1
            self.state.last_enonce = enonce
        if self.recorder is not None:
            self.recorder.write_enonce(enonce)
        if self.settings.voice.spoken and not self.settings.voice.muted:
            self.voice.dire(enonce.text)
        if self.on_enonce:
            try:
                self.on_enonce(enonce)
            except Exception:                          # pragma: no cover
                pass

    def _surveiller_disque(self) -> None:
        """Mesure l'espace restant et clôt la séance avant la saturation.

        Toutes les cinq seconds : l'appel système est court, mais le faire à
        chaque bloc serait trois cents fois trop souvent. Deux seuils — un pour
        prévenir tant qu'on peut encore faire de la place, un pour s'arrêter —
        parce qu'une alert qui arrive en même temps que la coupure ne sert à
        personne.
        """
        r = self.settings.recording
        if not r.watch_disk:
            return
        maintenant = time.monotonic()
        if maintenant - self._disque_t < 5.0:
            return
        self._disque_t = maintenant

        recording = self.recorder is not None and self.recorder.active
        path = self.recorder.dir if recording else r.directory
        state = disk_space.mesurer(path)
        if not state.mesure:
            return
        debit = disk_space.debit_mo_par_heure(self.settings)
        reste = disk_space.autonomie_heures(state.libre_mo, r.reserve_mb, debit)
        alert = recording and reste * 60.0 <= max(r.warn_minutes, 1.0)

        with self.lock:
            self.state.disk_free_mb = state.libre_mo
            self.state.disk_total_mb = state.total_mo
            self.state.disk_hours_left = reste
            self.state.disk_alert = alert

        if not recording:
            self._disque_prevenu = False
            return

        if state.libre_mo <= r.reserve_mb:
            chemin_clos = self.stop_recording()
            self._message(t("Disk full: recording closed with {reste} free. The session is complete and properly closed: {path}").format(
                                reste=disk_space.formater_mo(state.libre_mo),
                                path=chemin_clos or "—"))
            self._disque_prevenu = False
            return

        if alert and not self._disque_prevenu:
            self._disque_prevenu = True
            self._message(t("Disk space: {reste} free, about {duree} of recording. Recording will be closed automatically at {reserve}.").format(
                                reste=disk_space.formater_mo(state.libre_mo),
                                duree=disk_space.formater_duree(reste),
                                reserve=disk_space.formater_mo(r.reserve_mb)))

    def _maj_centroide(self) -> None:
        """Centre de gravité spectral du signal récent, en hertz.

        C'est l'axe « couleur » du engine lexical. Il est calculé ici, une
        fois toutes les deux seconds et pour tout le monde, plutôt que dans
        le engine lexical : recalculer un spectre à chaque événement coûterait
        cher et donnerait le même résultat.
        """
        maintenant = time.monotonic()
        if maintenant - self._centroid_t < 2.0:
            return
        self._centroid_t = maintenant
        x = self.recent(60.0)
        if x.size < 256:
            return
        fs = self.settings.acquisition.sample_rate
        freqs, psd = welch_psd(x, fs, nperseg=min(1024, x.size))
        # On écarte le continu et ce qui dépasse la bande utile : sans cela le
        # centroïde ne mesurerait que la dérive de la ligne de base.
        kept = (freqs > 0.01) & (freqs < fs / 2.5)
        if not kept.any():
            return
        poids = psd[kept]
        somme = float(poids.sum())
        if somme <= 0:
            return
        centroide = float((freqs[kept] * poids).sum() / somme)
        self.vocal.set_couleur_hz(centroide)
        with self.lock:
            self.state.centroid_hz = centroide

    def _update_state(self, raw: np.ndarray, centred: np.ndarray, index: int,
                      fs: float, full_scale: float, cost: float,
                      audio_time: float) -> None:
        st = self._stats
        now = time.monotonic()
        if self._drift_t0 == 0.0:
            self._drift_t0 = now
            self._drift_v0 = float(self._baseline.value) if self._baseline else 0.0
        drift = 0.0
        if self._baseline is not None and now - self._drift_t0 > 5.0:
            drift = (self._baseline.value - self._drift_v0) / (now - self._drift_t0) * 60.0
            self._drift_t0, self._drift_v0 = now, self._baseline.value
        with self.lock:
            s = self.state
            s.samples = index + centred.shape[0]
            s.elapsed_s = s.samples / fs if fs else 0.0
            s.value_v = float(centred[-1]) if centred.size else 0.0
            s.baseline_v = float(self._baseline.value) if self._baseline else 0.0
            if st is not None:
                s.rms_v, s.pp_v, s.sigma_v = st.rms, st.peak_to_peak, st.std
            if drift:
                s.drift_v_per_min = drift
            saturated = bool(np.max(np.abs(raw)) > 0.95 * full_scale) if raw.size else False
            if saturated and not s.saturated and \
                    self.settings.audio_out.beep_on_saturation and \
                    self.settings.audio_out.beep_enabled:
                self.output.bip("saturation")
            s.saturated = saturated
            m = self.output.metrics
            s.audio_peak_db = m.peak_db
            s.audio_reduction_db = m.reduction_db
            s.audio_clips = m.ecretages
            s.capture_active = self.capture.active
            s.capture_frames = self.capture.count
            s.blocks_sampled = self.sampler.blocks_kept
            s.usb_present = self.monitor.present
            s.usb_disconnections = self.monitor.disconnections
            s.dropped_blocks = self.source.dropped if self.source else 0
            if s.replaying and self.source is not None:
                position = getattr(self.source, "position", 0)
                s.replay_position = position / fs if fs else 0.0
            s.voice_backend = self.voice.backend if self.voice.actif else ""
            s.voice_spoken = self.voice.prononces
            s.voice_dropped = self.voice.abandons
            s.cpu_load = min(cost / audio_time, 9.99) if audio_time > 0 else 0.0
            if self.recorder is not None and self.recorder.active:
                s.recording = True
                s.record_dir = self.recorder.dir
                s.record_elapsed = self.recorder.elapsed
            else:
                s.recording = False

    # --------------------------------------------------------------- mémoire
    def _push_ring(self, centred: np.ndarray, raw: np.ndarray) -> None:
        if self._ring is None:
            return
        n = self._ring.shape[0]
        k = centred.shape[0]
        if k >= n:
            self._ring[:] = centred[-n:]
            self._ring_raw[:] = raw[-n:]
            self._ring_pos, self._ring_filled = 0, n
            return
        end = self._ring_pos + k
        if end <= n:
            self._ring[self._ring_pos:end] = centred
            self._ring_raw[self._ring_pos:end] = raw
        else:
            cut = n - self._ring_pos
            self._ring[self._ring_pos:] = centred[:cut]
            self._ring_raw[self._ring_pos:] = raw[:cut]
            self._ring[:end - n] = centred[cut:]
            self._ring_raw[:end - n] = raw[cut:]
        self._ring_pos = end % n
        self._ring_filled = min(self._ring_filled + k, n)

    def recent(self, seconds: float, raw: bool = False) -> np.ndarray:
        """Les N dernières seconds de signal, dans l'order chronologique."""
        if self._ring is None or self._ring_filled == 0:
            return np.zeros(0)
        src = self._ring_raw if raw else self._ring
        fs = self.settings.acquisition.sample_rate
        want = int(min(max(seconds, 0.1) * fs, self._ring_filled))
        if self._ring_filled < src.shape[0]:
            return src[max(self._ring_filled - want, 0):self._ring_filled].copy()
        idx = (np.arange(self._ring_pos - want, self._ring_pos) % src.shape[0])
        return src[idx].copy()

    # ------------------------------------------------------------- audio tap
    def _audio_tap(self, buf: np.ndarray) -> None:
        if self.recorder is not None and self.recorder.active:
            self.recorder.write_audio(buf)

    # ------------------------------------------------------- enregistrement
    def start_recording(self, label: str = "") -> Optional[str]:
        if self.recorder is not None and self.recorder.active:
            return self.recorder.dir
        self.recorder = Recorder(self.settings.recording.directory, self.settings,
                                 self.source.info if self.source else None,
                                 self.state.board, self.synth.fs)
        path = self.recorder.start(label)
        if path is None:
            self._message(self.recorder.last_error or t("recording impossible"))
            self.recorder = None
            return None
        self._message(t("Recording started: {path}").format(path=path))
        return path

    def stop_recording(self) -> Optional[str]:
        if self.recorder is None:
            return None
        path = self.recorder.stop()
        self.recorder = None
        if path:
            self._message(t("Session recorded: {path}").format(path=path))
        with self.lock:
            self.state.recording = False
        return path

    def mark(self, label: str) -> None:
        instant = self.state.elapsed_s
        if self.recorder is not None:
            self.recorder.write_mark(label, instant)
        if self.control.is_open:
            self.control.mark(label)
        self._message(t("Marker “{etiquette}” at {temps:.1f} s").format(
            etiquette=label, temps=instant))

    # ------------------------------------------------------- échantillons
    def capturer_echantillon(self, seconds: float = 0.0, etiquette: str = "",
                             raw: bool = False) -> Optional[str]:
        """Écrit sur le disque le signal qui vient de passer. Retourne le path.

        Le logiciel kept dix minutes de signal en mémoire ; l'essentiel arrive
        souvent **avant** qu'on ait pensé à save. Un geste, et la minute
        écoulée est sauvée — sans rien démarrer, sans rien arrêter.

        :param seconds: durée à garder ; 0 prend la value des réglages.
        :param raw: le signal avant filtrage plutôt que le signal affiché.
        """
        r = self.settings.recording
        duree = float(seconds) if seconds > 0 else float(r.sample_seconds)
        x = self.recent(duree, raw=raw)
        if x.size < 16:
            self._message(t("Not enough signal yet for a sample."))
            return None
        fs = float(self.settings.acquisition.sample_rate)
        meta = {
            "plante": self.settings.metadata.get("plante", ""),
            "lieu": self.settings.metadata.get("lieu", ""),
            "operateur": self.settings.metadata.get("operateur", ""),
            "source": self.state.source_name,
            "signal_brut": bool(raw),
            "evenements_dans_la_fenetre": sum(
                1 for t_ev in self._evenements_recents
                if self.state.elapsed_s - t_ev <= duree),
            "settings": {
                "acquiring": asdict_leger(self.settings.acquisition),
                "processing": asdict_leger(self.settings.processing),
            },
        }
        try:
            path = samples.ecrire(
                x, fs, samples.dossier_par_defaut(self.settings),
                etiquette=etiquette or self.settings.metadata.get("plante", ""),
                metadata=meta)
        except (OSError, ValueError) as exc:
            self._message(t("Sample failed: {erreur}").format(erreur=exc))
            return None
        with self.lock:
            self.state.last_sample = path
            self.state.samples_total += 1
        self._message(t("Sample kept: {duree:.0f} s in {file_path}").format(
            duree=x.size / fs, file_path=os.path.basename(path)))
        return path

    # ---------------------------------------------------------- replaying
    def rejouer(self, data, fs: float, vitesse: float = 1.0, name: str = "",
                boucle: bool = False) -> bool:
        """Remplace la source vivante par un enregistrement.

        Tout le reste du logiciel continue de fonctionner comme si la plante
        était là : filtres, détection, descripteurs, musique, mode vocal. C'est
        l'intérêt de rejouer dans le engine plutôt que de tracer une courbe.
        """
        from .sources import FileSource
        import numpy as _np

        x = _np.asarray(data, dtype=_np.float64)
        if x.ndim == 1:
            x = x[:, None]
        if x.size == 0 or fs <= 0:
            return False

        self.stop_recording()
        self._arreter_traitement()
        if self.source is not None:
            self.source.stop()

        #  La chaîne doit tourner à la cadence du file_path, pas à celle réglée
        #  pour la carte. On retient la value pour la rendre au retour.
        if self._fs_avant_relecture is None:
            self._fs_avant_relecture = float(self.settings.acquisition.sample_rate)
        self.settings.acquisition.sample_rate = float(fs)
        self._rebuild_processing(force=True)

        self.source = FileSource(self.raw_q, x, float(fs), max(vitesse, 0.01),
                                 loop=boucle, name=name or t("recording"))
        self._demarrer_traitement("replay")
        self.audio.start()          # sans effet si la sortie est déjà ouverte
        self.source.start()
        with self.lock:
            self.state.running = True
            self.state.replaying = True
            self.state.replay_name = name
            self.state.replay_length = x.shape[0] / fs
            self.state.replay_position = 0.0
            self.state.source_name = name or t("recording")
            self.state.source_kind = "file_path"
        self._message(t("Replay: {name} — {duree:.0f} s at ×{vitesse:g}").format(
            name=name or "—", duree=x.shape[0] / fs, vitesse=vitesse))
        return True

    def arreter_relecture(self, revenir_en_direct: bool = True) -> None:
        """Ferme la replaying et, si on le requested, rend la main à la plante."""
        if not self.state.replaying:
            return
        self._arreter_traitement()
        if self.source is not None:
            self.source.stop()
        self.synth.all_off()
        if self._fs_avant_relecture is not None:
            self.settings.acquisition.sample_rate = self._fs_avant_relecture
            self._fs_avant_relecture = None
        with self.lock:
            self.state.replaying = False
            self.state.replay_name = ""
            self.state.replay_position = 0.0
            self.state.replay_length = 0.0
            self.state.running = False
        if revenir_en_direct:
            self.start()

    # ----------------------------------------------------------------- divers
    def snapshot(self) -> EngineState:
        with self.lock:
            st = EngineState(**{k: getattr(self.state, k)
                                for k in self.state.__dataclass_fields__})
        return st

    @resilient(message="Changement d'état USB")
    def _usb_change(self, present: bool) -> None:
        self._message(t("USB board reconnected.") if present
                      else t("WARNING: USB board has vanished from the bus."))
        if not present and self.settings.audio_out.beep_enabled:
            self.output.bip("erreur")

    # ------------------------------------------------------- mise au point
    def start_capture(self, label: str = "") -> Optional[str]:
        """Démarre la capture des trames (mode de mise au point)."""
        path = self.capture.start(label)
        if path:
            self._message(t("Frame capture: {path}").format(path=path))
        else:
            self._message(self.capture.last_error or t("capture impossible"))
        return path

    def stop_capture(self) -> Optional[str]:
        path = self.capture.stop()
        if path:
            self._message(t("Capture stopped: {n} frames").format(n=self.capture.count))
        return path

    def test_haut_parleur(self) -> None:
        """Émet un bip d'essai — vérifie la sortie sans lancer d'acquisition."""
        self.output.test_haut_parleur()

    def set_hardware_gain(self, gain) -> bool:
        if not self.control.is_open:
            return False
        return self.control.set_gain(gain)
