#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  ==========================================================================
#  PhytoScope — attribution — tools/fetch-software.py
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

"""
Récupère la chaîne logicielle open source du projet « arbre parlant ».

Télécharge chaque dépôt en ARCHIVE SOURCE (pas de clone git : ni historique,
ni .git, donc 5 à 20 fois plus léger), relève la licence réellement présente
dans l'archive, et écrit un manifeste JSON + Markdown.

Rien n'est inventé : un dépôt qui ne répond pas est marqué ABSENT, et son
absence apparaît dans le manifeste.

Usage : python3 tools/fetch-software.py [catégorie…]
"""
import json
import os
import re
import subprocess
import sys
import time
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, "sources", "software")

# (catégorie, hôte, org/repo, branches à essayer, rôle)
DEPOTS = [
    # ---- bibliothèques microcontrôleur (ESP32 / ATmega328P) -----------------
    ("libs-mcu", "gh", "adafruit/Adafruit_ADS1X15", ["master", "main"],
     "ADS1115/ADS1015 — convertisseur de la planche 2"),
    ("libs-mcu", "gh", "adafruit/Adafruit_BME280_Library", ["master", "main"],
     "BME280 — T/HR/pression, planche 3"),
    ("libs-mcu", "gh", "adafruit/Adafruit_BusIO", ["master", "main"],
     "couche I²C/SPI commune aux bibliothèques Adafruit"),
    ("libs-mcu", "gh", "adafruit/Adafruit_Sensor", ["master", "main"],
     "interface de capteur unifiée Adafruit"),
    ("libs-mcu", "gh", "adafruit/Adafruit_TSL2591_Library", ["master", "main"],
     "TSL2591 — luxmètre à forte dynamique"),
    ("libs-mcu", "gh", "claws/BH1750", ["master", "main"],
     "BH1750 — éclairement, planche 3"),
    ("libs-mcu", "gh", "PaulStoffregen/OneWire", ["master", "main"],
     "bus 1-Wire — planche 3"),
    ("libs-mcu", "gh", "milesburton/Arduino-Temperature-Control-Library",
     ["master", "main"], "DS18B20 — sondes de température"),
    ("libs-mcu", "gh", "Sensirion/arduino-i2c-scd4x", ["main", "master"],
     "SCD40/SCD41 — CO₂"),
    ("libs-mcu", "gh", "Sensirion/arduino-core", ["main", "master"],
     "socle commun des bibliothèques Sensirion"),
    ("libs-mcu", "gh", "Sensirion/arduino-i2c-sht4x", ["main", "master"],
     "SHT4x — T/HR de précision"),
    ("libs-mcu", "gh", "FortySevenEffects/arduino_midi_library",
     ["master", "main"], "MIDI série — sortie DIN-5 de la planche 1"),
    ("libs-mcu", "gh", "lathoub/Arduino-AppleMIDI-Library", ["master", "main"],
     "RTP-MIDI sur Wi-Fi — utilisé par BiodataFeather"),
    ("libs-mcu", "gh", "lathoub/Arduino-BLE-MIDI", ["master", "main"],
     "MIDI sur Bluetooth LE — utilisé par BiodataFeather"),
    ("libs-mcu", "gh", "thomasfredericks/Bounce2", ["master", "main"],
     "anti-rebond logiciel — dépendance du firmware biodata"),
    ("libs-mcu", "gh", "jgillick/arduino-LEDFader", ["master", "main"],
     "gestion des LED sans delay() — dépendance du firmware biodata"),
    ("libs-mcu", "gh", "thijse/Arduino-EEPROMEx", ["master", "main"],
     "EEPROMex — dépendance du firmware MIDI Sprout"),
    ("libs-mcu", "gh", "sparkfun/AD8232_Heart_Rate_Monitor", ["master", "main"],
     "exemples AD8232 — front-end ECG applicable à la planche 2"),
    ("libs-mcu", "gh", "mcci-catena/arduino-lmic", ["master", "main"],
     "pile LoRaWAN de référence pour nœud sur batterie"),
    ("libs-mcu", "gh", "TheThingsNetwork/arduino-device-lib", ["master", "main"],
     "bibliothèque The Things Network"),
    ("libs-mcu", "gh", "jgromes/RadioLib", ["master", "main"],
     "pile radio universelle (LoRa, SX126x/SX127x)"),

    # ---- firmware ----------------------------------------------------------
    ("firmware", "gh", "esphome/esphome", ["dev", "main"],
     "firmware ESP décrit en YAML — listing 4 de l'annexe"),
    ("firmware", "gh", "arendst/Tasmota", ["master", "development"],
     "firmware ESP alternatif"),
    ("firmware", "gh", "meshtastic/firmware", ["master", "main"],
     "maillage LoRa hors couverture"),
    ("firmware", "gh", "kizniche/Mycodo", ["master", "main"],
     "acquisition et régulation sur Raspberry Pi"),
    ("firmware", "gh", "farmOS/farmOS", ["3.x", "2.x", "main"],
     "couche métier agricole (Drupal)"),

    # ---- ingestion et stockage --------------------------------------------
    ("ingest", "gh", "eclipse-mosquitto/mosquitto", ["master", "develop"],
     "courtier MQTT"),
    ("ingest", "gh", "influxdata/telegraf", ["master", "main"],
     "agent de collecte"),
    ("ingest", "gh", "influxdata/influxdb", ["main", "master"],
     "base de séries temporelles (Core : MIT/Apache-2.0)"),
    ("ingest", "gh", "timescale/timescaledb", ["main", "master"],
     "extension PostgreSQL séries temporelles"),
    ("ingest", "gh", "node-red/node-red", ["master", "main"],
     "orchestration par flux"),

    # ---- visualisation -----------------------------------------------------
    ("viz", "gh", "grafana/grafana", ["main", "master"],
     "tableaux de bord — ATTENTION AGPL-3.0"),
    ("viz", "gh", "home-assistant/core", ["dev", "master"],
     "supervision locale"),

    # ---- sonification et audio --------------------------------------------
    ("sonification", "gh", "supercollider/supercollider", ["develop", "main"],
     "moteur de synthèse — listing 9"),
    ("sonification", "gh", "pure-data/pure-data", ["master", "main"],
     "patch temps réel (Pd vanilla)"),
    ("sonification", "gh", "sonic-pi-net/sonic-pi", ["dev", "main", "stable"],
     "live coding pédagogique"),
    ("sonification", "gh", "ccrma/chuck", ["main", "master"],
     "langage audio strongly-timed"),
    ("sonification", "gh", "csound/csound", ["develop", "master"],
     "moteur de synthèse historique"),
    ("sonification", "gh", "attwad/python-osc", ["main", "master"],
     "pont Python → OSC — listing 8"),
    ("sonification", "gh", "mido/mido", ["main", "master"],
     "MIDI en Python"),
    ("sonification", "gh", "FluidSynth/fluidsynth", ["master", "main"],
     "MIDI → audio (SoundFont)"),
    ("sonification", "gh", "BelaPlatform/Bela", ["dev", "master"],
     "capteurs à la fréquence audio, latence ultra-faible"),
    ("sonification", "cb", "uzu/tidal", ["main", "master"],
     "TidalCycles — langage de motifs (migré sur Codeberg)"),

    # ---- synthèse vocale ---------------------------------------------------
    ("tts", "gh", "OHF-Voice/piper1-gpl", ["main", "master"],
     "Piper 1 — synthèse vocale locale, GPLv3"),
    ("tts", "gh", "rhasspy/piper", ["master", "main"],
     "Piper historique — ARCHIVÉ, conservé pour référence"),
    ("tts", "gh", "idiap/coqui-ai-TTS", ["main", "dev"],
     "fork maintenu de Coqui TTS"),
    ("tts", "gh", "espeak-ng/espeak-ng", ["master", "main"],
     "synthèse à formants, très légère"),
    ("tts", "gh", "hexgrad/kokoro", ["main", "master"],
     "Kokoro — Apache-2.0 code et poids"),

    # ---- modèles de langue locaux -----------------------------------------
    ("llm", "gh", "ggml-org/llama.cpp", ["master", "main"],
     "moteur d'inférence sur processeur"),
    ("llm", "gh", "ollama/ollama", ["main", "master"],
     "surcouche de gestion de modèles"),
]

MOTIFS_LICENCE = re.compile(
    r"/(LICEN[SC]E|COPYING|LICENSE\.txt|LICENSE\.md|COPYRIGHT)[^/]*$", re.I)

# Relevés manuels, faits en ouvrant le fichier : ces dépôts ne déclarent pas
# leur licence là où un automate sait la lire. La provenance est indiquée pour
# que chaque valeur reste vérifiable.
RELEVES_MANUELS = {
    "adafruit/Adafruit_TSL2591_Library":
        ("BSD", "en-tête de Adafruit_TSL2591.cpp (@section LICENSE)"),
    "PaulStoffregen/OneWire":
        ("MIT", "en-tête de OneWire.cpp (« Permission is hereby granted »)"),
    "lathoub/Arduino-AppleMIDI-Library":
        ("CC BY-SA 4.0 ⚠", "LICENSE.md — licence à partage à l'identique, "
                           "inhabituelle pour du code et contaminante"),
    "sparkfun/AD8232_Heart_Rate_Monitor":
        ("matériel CC BY-SA 3.0 · code Beerware", "LICENSE.md"),
}


def url(hote, repo, branche):
    if hote == "gh":
        return f"https://codeload.github.com/{repo}/zip/refs/heads/{branche}"
    if hote == "cb":
        nom = repo.split("/")[-1]
        return f"https://codeberg.org/{repo}/archive/{branche}.zip"
    raise ValueError(hote)


def _famille(texte):
    """Identifie la licence d'après l'EN-TÊTE seulement.

    Analyser le corps entier est piégeux : le texte de la MPL 2.0 cite la GPL
    dans son exhibit B, et celui de la GPL v2 cite la LGPL dans son dernier
    paragraphe. Les deux erreurs ont été observées ici avant correction.
    """
    lignes = [l.strip() for l in texte.splitlines() if l.strip()]
    # On élargit la fenêtre progressivement : le préambule de la GPL v2 cite la
    # LGPL dès sa douzième ligne, ce qui produit un faux positif dès qu'on
    # regarde trop loin. On s'arrête à la première fenêtre qui décide.
    CLES = ("public license", "mit license", "free of charge",
            "redistribution and use", "unencumbered", "permission to use, copy")
    t = "\n".join(lignes[:30]).lower()
    for fenetre in (3, 6, 14, 30):
        essai = "\n".join(lignes[:fenetre]).lower()
        if any(k in essai for k in CLES):
            t = essai
            break
    if "affero" in t:
        return "AGPL-3.0"
    if "lesser general public license" in t or "lgpl" in t:
        return "LGPL-3.0" if ("version 3" in t or "lgpl 3" in t or "lgpl-3" in t) else (
            "LGPL-2.1" if "2.1" in t else "LGPL-?")
    if "general public license" in t:
        return "GPL-3.0" if "version 3" in t else (
            "GPL-2.0" if "version 2" in t else "GPL-?")
    if "mozilla public license" in t:
        return "MPL-2.0"
    if "eclipse public license" in t:
        return "EPL-2.0"
    if "apache license" in t:
        return "Apache-2.0"
    if "timescale license" in t:
        return "TSL (source-available)"
    if "mit license" in t or "permission is hereby granted, free of charge" in t:
        return "MIT"
    if "redistribution and use in source and binary forms" in t:
        return "BSD"
    if "this is free and unencumbered software" in t:
        return "Unlicense"
    if "permission to use, copy, modify, and/or distribute" in t:
        return "ISC"
    return None


def licence_de(chemin):
    """Renvoie (licence, fichier). Signale les doubles licences."""
    try:
        with zipfile.ZipFile(chemin) as z:
            cands = [n for n in z.namelist()
                     if MOTIFS_LICENCE.search("/" + n) and n.count("/") <= 1]
            if not cands:
                cands = [n for n in z.namelist()
                         if MOTIFS_LICENCE.search("/" + n) and n.count("/") <= 2]
            if not cands:
                return "aucun fichier de licence à la racine", None
            trouves = []
            for nom in sorted(cands, key=lambda n: (n.count("/"), len(n)))[:4]:
                t = z.read(nom).decode("utf-8", "replace")[:6000]
                f = _famille(t)
                if f and f not in [x[0] for x in trouves]:
                    trouves.append((f, nom))
    except Exception as e:
        return f"illisible ({e.__class__.__name__})", None
    if not trouves:
        return "indéterminée (fichier présent)", cands[0]
    if len(trouves) > 1:
        return (" ou ".join(x[0] for x in trouves) + " (double licence)",
                ", ".join(x[1] for x in trouves))
    return trouves[0]


def telecharger(hote, repo, branches, cible):
    for br in branches:
        tmp = cible + ".part"
        r = subprocess.run(
            ["curl", "-sSL", "--max-time", "900", "-w", "%{http_code}",
             "-o", tmp, url(hote, repo, br)],
            capture_output=True, text=True)
        code = (r.stdout or "").strip()[-3:]
        if code == "200" and os.path.exists(tmp) and os.path.getsize(tmp) > 1024:
            if zipfile.is_zipfile(tmp):
                os.replace(tmp, cible)
                return br
        if os.path.exists(tmp):
            os.remove(tmp)
    return None


def main():
    filtres = set(sys.argv[1:])
    manifeste = []
    for cat, hote, repo, branches, role in DEPOTS:
        if filtres and cat not in filtres:
            continue
        dossier = os.path.join(DEST, cat)
        os.makedirs(dossier, exist_ok=True)
        nom = repo.replace("/", "_") + ".zip"
        cible = os.path.join(dossier, nom)

        if os.path.exists(cible) and zipfile.is_zipfile(cible):
            br = "(déjà présent)"
        else:
            t0 = time.time()
            br = telecharger(hote, repo, branches, cible)
            if br is None:
                print(f"  ABSENT   {repo}")
                manifeste.append({"categorie": cat, "depot": repo, "role": role,
                                  "statut": "ABSENT", "licence": None,
                                  "taille_Mo": None, "branche": None})
                continue
            print(f"  ok  {repo:52s} {br:12s} "
                  f"{os.path.getsize(cible)/1048576:7.1f} Mo  "
                  f"{time.time()-t0:5.1f} s")
        if repo in RELEVES_MANUELS:
            lic, fichier = RELEVES_MANUELS[repo]
        else:
            lic, fichier = licence_de(cible)
        manifeste.append({
            "categorie": cat, "depot": repo, "role": role, "statut": "présent",
            "licence": lic, "fichier_licence": fichier, "branche": br,
            "taille_Mo": round(os.path.getsize(cible) / 1048576, 2),
            "archive": os.path.relpath(cible, ROOT),
            "url": f"https://github.com/{repo}" if hote == "gh"
                   else f"https://codeberg.org/{repo}",
        })

    os.makedirs(DEST, exist_ok=True)
    with open(os.path.join(DEST, "MANIFESTE.json"), "w", encoding="utf-8") as f:
        json.dump(manifeste, f, indent=2, ensure_ascii=False)

    lignes = ["# Manifeste de la chaîne logicielle — « L'Arbre qui Parle »", "",
              "Archives source (sans historique git) téléchargées par "
              "`tools/fetch-software.py`.", "",
              "| Catégorie | Dépôt | Licence (lue dans l'archive) | Mo | Rôle |",
              "|---|---|---|---|---|"]
    total = 0.0
    for m in manifeste:
        if m["statut"] == "ABSENT":
            lignes.append(f"| {m['categorie']} | {m['depot']} | **ABSENT** | — | "
                          f"{m['role']} |")
            continue
        total += m["taille_Mo"] or 0
        lignes.append(f"| {m['categorie']} | [{m['depot']}]({m['url']}) | "
                      f"{m['licence']} | {m['taille_Mo']} | {m['role']} |")
    lignes += ["", f"**{len([m for m in manifeste if m['statut']=='présent'])} "
                   f"dépôts, {total:.0f} Mo au total.**"]
    with open(os.path.join(DEST, "MANIFESTE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lignes) + "\n")
    print(f"\nManifeste : {os.path.relpath(DEST, ROOT)}/MANIFESTE.{{json,md}}  "
          f"— {total:.0f} Mo")


if __name__ == "__main__":
    main()
