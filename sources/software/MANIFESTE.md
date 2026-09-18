# Manifeste de la chaîne logicielle — « L'Arbre qui Parle »

Archives source (sans historique git) téléchargées par `tools/fetch-software.py`.

| Catégorie | Dépôt | Licence (lue dans l'archive) | Mo | Rôle |
|---|---|---|---|---|
| libs-mcu | [adafruit/Adafruit_ADS1X15](https://github.com/adafruit/Adafruit_ADS1X15) | BSD | 0.02 | ADS1115/ADS1015 — convertisseur de la planche 2 |
| libs-mcu | [adafruit/Adafruit_BME280_Library](https://github.com/adafruit/Adafruit_BME280_Library) | BSD | 0.44 | BME280 — T/HR/pression, planche 3 |
| libs-mcu | [adafruit/Adafruit_BusIO](https://github.com/adafruit/Adafruit_BusIO) | MIT | 0.03 | couche I²C/SPI commune aux bibliothèques Adafruit |
| libs-mcu | [adafruit/Adafruit_Sensor](https://github.com/adafruit/Adafruit_Sensor) | Apache-2.0 | 0.02 | interface de capteur unifiée Adafruit |
| libs-mcu | [adafruit/Adafruit_TSL2591_Library](https://github.com/adafruit/Adafruit_TSL2591_Library) | BSD | 0.02 | TSL2591 — luxmètre à forte dynamique |
| libs-mcu | [claws/BH1750](https://github.com/claws/BH1750) | MIT | 0.28 | BH1750 — éclairement, planche 3 |
| libs-mcu | [PaulStoffregen/OneWire](https://github.com/PaulStoffregen/OneWire) | MIT | 0.02 | bus 1-Wire — planche 3 |
| libs-mcu | [milesburton/Arduino-Temperature-Control-Library](https://github.com/milesburton/Arduino-Temperature-Control-Library) | MIT | 0.06 | DS18B20 — sondes de température |
| libs-mcu | [Sensirion/arduino-i2c-scd4x](https://github.com/Sensirion/arduino-i2c-scd4x) | BSD | 2.62 | SCD40/SCD41 — CO₂ |
| libs-mcu | [Sensirion/arduino-core](https://github.com/Sensirion/arduino-core) | BSD | 0.04 | socle commun des bibliothèques Sensirion |
| libs-mcu | [Sensirion/arduino-i2c-sht4x](https://github.com/Sensirion/arduino-i2c-sht4x) | BSD | 1.96 | SHT4x — T/HR de précision |
| libs-mcu | [FortySevenEffects/arduino_midi_library](https://github.com/FortySevenEffects/arduino_midi_library) | MIT | 0.13 | MIDI série — sortie DIN-5 de la planche 1 |
| libs-mcu | [lathoub/Arduino-AppleMIDI-Library](https://github.com/lathoub/Arduino-AppleMIDI-Library) | CC BY-SA 4.0 ⚠ | 0.24 | RTP-MIDI sur Wi-Fi — utilisé par BiodataFeather |
| libs-mcu | [lathoub/Arduino-BLE-MIDI](https://github.com/lathoub/Arduino-BLE-MIDI) | MIT | 0.04 | MIDI sur Bluetooth LE — utilisé par BiodataFeather |
| libs-mcu | [thomasfredericks/Bounce2](https://github.com/thomasfredericks/Bounce2) | MIT | 0.09 | anti-rebond logiciel — dépendance du firmware biodata |
| libs-mcu | [jgillick/arduino-LEDFader](https://github.com/jgillick/arduino-LEDFader) | MIT | 0.01 | gestion des LED sans delay() — dépendance du firmware biodata |
| libs-mcu | [thijse/Arduino-EEPROMEx](https://github.com/thijse/Arduino-EEPROMEx) | LGPL-2.1 | 0.08 | EEPROMex — dépendance du firmware MIDI Sprout |
| libs-mcu | [sparkfun/AD8232_Heart_Rate_Monitor](https://github.com/sparkfun/AD8232_Heart_Rate_Monitor) | matériel CC BY-SA 3.0 · code Beerware | 0.58 | exemples AD8232 — front-end ECG applicable à la planche 2 |
| libs-mcu | [mcci-catena/arduino-lmic](https://github.com/mcci-catena/arduino-lmic) | MIT | 4.48 | pile LoRaWAN de référence pour nœud sur batterie |
| libs-mcu | [TheThingsNetwork/arduino-device-lib](https://github.com/TheThingsNetwork/arduino-device-lib) | MIT | 3.07 | bibliothèque The Things Network |
| libs-mcu | [jgromes/RadioLib](https://github.com/jgromes/RadioLib) | MIT | 5.27 | pile radio universelle (LoRa, SX126x/SX127x) |
| firmware | [esphome/esphome](https://github.com/esphome/esphome) | GPL-? | 11.37 | firmware ESP décrit en YAML — listing 4 de l'annexe |
| firmware | [arendst/Tasmota](https://github.com/arendst/Tasmota) | GPL-3.0 | 56.54 | firmware ESP alternatif |
| firmware | [meshtastic/firmware](https://github.com/meshtastic/firmware) | GPL-3.0 | 5.11 | maillage LoRa hors couverture |
| firmware | [kizniche/Mycodo](https://github.com/kizniche/Mycodo) | GPL-3.0 | 7.31 | acquisition et régulation sur Raspberry Pi |
| firmware | [farmOS/farmOS](https://github.com/farmOS/farmOS) | GPL-2.0 ou GPL-? (double licence) | 1.25 | couche métier agricole (Drupal) |
| ingest | [eclipse-mosquitto/mosquitto](https://github.com/eclipse-mosquitto/mosquitto) | EPL-2.0 | 3.59 | courtier MQTT |
| ingest | [influxdata/telegraf](https://github.com/influxdata/telegraf) | MIT | 7.9 | agent de collecte |
| ingest | [influxdata/influxdb](https://github.com/influxdata/influxdb) | MIT ou Apache-2.0 (double licence) | 5.59 | base de séries temporelles (Core : MIT/Apache-2.0) |
| ingest | [timescale/timescaledb](https://github.com/timescale/timescaledb) | Apache-2.0 | 10.09 | extension PostgreSQL séries temporelles |
| ingest | [node-red/node-red](https://github.com/node-red/node-red) | Apache-2.0 | 9.56 | orchestration par flux |
| viz | [grafana/grafana](https://github.com/grafana/grafana) | AGPL-3.0 | 60.64 | tableaux de bord — ATTENTION AGPL-3.0 |
| viz | [home-assistant/core](https://github.com/home-assistant/core) | Apache-2.0 | 41.82 | supervision locale |
| sonification | [supercollider/supercollider](https://github.com/supercollider/supercollider) | GPL-3.0 | 20.2 | moteur de synthèse — listing 9 |
| sonification | [pure-data/pure-data](https://github.com/pure-data/pure-data) | BSD | 14.57 | patch temps réel (Pd vanilla) |
| sonification | [sonic-pi-net/sonic-pi](https://github.com/sonic-pi-net/sonic-pi) | MIT | 130.8 | live coding pédagogique |
| sonification | [ccrma/chuck](https://github.com/ccrma/chuck) | GPL-2.0 ou MIT (double licence) | 21.89 | langage audio strongly-timed |
| sonification | [csound/csound](https://github.com/csound/csound) | LGPL-2.1 | 27.54 | moteur de synthèse historique |
| sonification | [attwad/python-osc](https://github.com/attwad/python-osc) | Unlicense | 0.11 | pont Python → OSC — listing 8 |
| sonification | [mido/mido](https://github.com/mido/mido) | MIT | 0.22 | MIDI en Python |
| sonification | [FluidSynth/fluidsynth](https://github.com/FluidSynth/fluidsynth) | LGPL-2.1 | 2.39 | MIDI → audio (SoundFont) |
| sonification | [BelaPlatform/Bela](https://github.com/BelaPlatform/Bela) | LGPL-3.0 | 62.49 | capteurs à la fréquence audio, latence ultra-faible |
| sonification | [uzu/tidal](https://codeberg.org/uzu/tidal) | GPL-3.0 | 1.65 | TidalCycles — langage de motifs (migré sur Codeberg) |
| tts | [OHF-Voice/piper1-gpl](https://github.com/OHF-Voice/piper1-gpl) | GPL-3.0 | 24.25 | Piper 1 — synthèse vocale locale, GPLv3 |
| tts | [rhasspy/piper](https://github.com/rhasspy/piper) | MIT | 24.49 | Piper historique — ARCHIVÉ, conservé pour référence |
| tts | [idiap/coqui-ai-TTS](https://github.com/idiap/coqui-ai-TTS) | MPL-2.0 | 20.77 | fork maintenu de Coqui TTS |
| tts | [espeak-ng/espeak-ng](https://github.com/espeak-ng/espeak-ng) | GPL-3.0 ou MIT ou BSD ou Apache-2.0 (double licence) | 21.05 | synthèse à formants, très légère |
| tts | [hexgrad/kokoro](https://github.com/hexgrad/kokoro) | Apache-2.0 | 25.02 | Kokoro — Apache-2.0 code et poids |
| llm | [ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) | MIT | 37.44 | moteur d'inférence sur processeur |
| llm | [ollama/ollama](https://github.com/ollama/ollama) | MIT | 25.59 | surcouche de gestion de modèles |

**50 dépôts, 701 Mo au total.**
