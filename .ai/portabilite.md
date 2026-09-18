# Portabilité — relevé du 2026-09-18

Analyse demandée le 2026-09-18 : Windows 10/11, macOS (Darwin, Intel et Apple
Silicon), GNU/Linux (Debian, Ubuntu, Mint, Fedora, Red Hat). Périmètre : le
paquet `phytoscope/`, `tools/`, `run.py`, `Makefile`, `make.bat`. Le
micrologiciel et la fabrication des PDF sont traités à part, ce sont des outils
de développement.

**Tout a été corrigé le 2026-09-18 (version 1.5.1).** Ce fichier reste comme
relevé d'origine : il dit ce qui était cassé, pourquoi, et ce qu'il ne faut pas
refaire. L'état des correctifs figure dans la colonne « Corrigé ».

Ce qui n'est **pas** vérifié : aucun de ces correctifs n'a tourné sur une vraie
machine Windows ni sur un Mac. Ils le sont par lecture du code et par les
vingt-trois essais de `tests/test_portabilite.py`, qui vérifient sous Linux ce qui
ne se voit qu'ailleurs.

## Ce qui est déjà bon — et qu'il ne faut pas casser

- `config.py:21-29` `config_dir()` et `:32-40` `data_dir()` respectent les trois
  usages : `%APPDATA%\PhytoScope`, `~/Library/Application Support/PhytoScope`,
  `$XDG_CONFIG_HOME`.
- `espace.py:73` utilise `shutil.disk_usage`, portable. **Aucun `os.statvfs`**
  dans le projet.
- Aucun `open()` texte sans `encoding=`. Les CSV portent `newline=""`, ce qui
  est indispensable sous Windows.
- Aucune concaténation de chemin par `+ "/"`. Tout passe par `os.path.join`.
- Aucun `fcntl`, `termios`, `pwd`, `grp`, `resource`, `posix`, `os.uname`,
  `os.system`. Seuls `SIGINT` et `SIGTERM` sont posés, et `SIGTERM` est gardé
  par `hasattr` (`interrupt.py:145-147`).
- Les ports série sont découverts par `serial.tools.list_ports.comports()` :
  aucun motif `/dev/ttyACM*` ni `COM*` codé en dur.
- Le code réservé à Linux est correctement gardé (`audio_quiet.py`,
  `preflight.py`, `usbdiag._from_sysfs`).
- `platform_info.py` couvre apt et dnf/yum, y compris la bascule `dnf`→`yum`
  pour les RHEL anciens.

## Bloquants

| № (✔ = corrigé) | Fichier | Plateformes | Constat |
|---|---|---|---|
| **P-1** ✔ | `core/protocol.py:38-39`, `core/usbdiag.py:38-39,43`, `config.py:255-256` | les trois, aggravé sous Windows | Le logiciel cherche `0x2E8A:0x10F5` ; **le micrologiciel déclare `0x1209:0x7A01`** (`usb_descriptors.c:40-41`). La carte n'est donc jamais reconnue par VID/PID. Le repli par nom de produit (`protocol.py:132-134`) sauve Linux et macOS ; sous Windows `pyserial` ne remplit pas `product` et `description` vaut `"USB Serial Device (COMx)"` — **le lien de contrôle est inutilisable**. Le micrologiciel a raison : `0x1209` est la plage libre de pid.codes, `0x2E8A` appartient à Raspberry Pi. **C'est le logiciel qu'il faut corriger.** |
| **P-2** ✔ | `core/sources.py:258-261`, `config.py:50` | Windows, macOS | `sd.InputStream(samplerate=250.0)` : CoreAudio et WASAPI refusent, ALSA rééchantillonne. Le repli sur le générateur interne fonctionne, donc le logiciel démarre — mais la source « Entrée audio » est inutilisable. Correction : ouvrir à la `default_samplerate` du périphérique (déjà lue en `sources.py:225`) et décimer en logiciel. |
| **P-3** ✔ | `requirements.txt:14-20` | les trois | `python-rtmidi` et `pyttsx3` sont sur des lignes dures. `python-rtmidi` est du C++ sans roue pour les Python récents : un échec sur cette ligne fait échouer `make install` **en entier**, et l'utilisateur se retrouve sans NumPy ni PySide6. `pyproject.toml:33-35` les classe pourtant correctement en extra `complet`. |
| **P-4** ✔ | `core/console.py:95,130-132,155`, `__main__.py:268,534`, `usbdiag.py:265` | Windows | Aucun `sys.stdout.reconfigure(encoding="utf-8")`. En console réelle Python passe par l'API UTF-16 et cela s'affiche ; **dès que la sortie est redirigée** (`run.py --check > rapport.txt`), cp1252 reprend et `print()` lève `UnicodeEncodeError` — précisément quand on cherche à diagnostiquer. |

## Dégradés

| № (✔ = corrigé) | Fichier | Plateformes | Constat |
|---|---|---|---|
| **P-5** ✔ | ~20 emplacements (`widgets.py:448`, `tabs.py:332`, `log_window.py:88,107`, `help_dialog.py:207`…) | Windows, macOS | « DejaVu Sans Mono » codé en dur **sans repli**. Seul `theme.py:91` déclare `, monospace`. DejaVu n'existe ni sous Windows ni sous macOS : Qt substitue souvent une police **proportionnelle**, et l'alignement des tableaux de valeurs se casse. Correction : une fonction `police_mono()` unique posant `setStyleHint(QFont.Monospace)` et `setFamilies(["DejaVu Sans Mono","Menlo","Consolas","Courier New"])`. |
| **P-6** ✔ | `ui/help_dialog.py:33-77` | macOS | Les raccourcis sont réaffichés **en dur** (« Ctrl+R ») alors que Qt les traduit en ⌘R. La fonction `_normaliser()` (`:309-322`) fait déjà le bon travail mais ne sert qu'à comparer. |
| **P-7** ✔ | `ui/main_window.py:275` | macOS | `Ctrl+.` : ⌘. est historiquement « annuler » sur macOS ; conflit possible avec le silence MIDI. |
| **P-8** ✔ | `core/sources.py:232-238,225,258`, `ui/settings_tab.py:213-222,657` | Windows | Le périphérique audio est choisi **par son nom**. Windows expose le même matériel sur MME, DirectSound, WASAPI et WDM-KS avec des noms quasi identiques, et **MME tronque à 31 caractères** : la résolution retient souvent MME, la pire API. `hostapi` est pourtant lu (`sources.py:226`) mais jamais utilisé. |
| **P-9** ✔ | `music/midi_out.py:63` | Windows | `open_virtual_port()` n'existe pas sur l'API Windows MM. L'exception est bien attrapée, mais l'utilisateur n'apprend pas qu'il lui faut loopMIDI. |
| **P-10** ✔ | `music/voice.py:124` | portabilité des réglages | `espeak -v <voix>` reçoit un identifiant SAPI/pyttsx3 si le `reglages.json` vient de Windows → échec journalisé à chaque énoncé. |
| **P-11** ✔ | `music/voice.py:77,239,310,256-258` | Windows | Affinité d'apartment COM : l'objet SAPI5 est créé dans un thread et utilisé dans le thread `phytoscope-voix`. **Risque identifié, non vérifié par exécution.** Le repli SAPI-par-PowerShell (`:175`) n'a pas ce problème. |
| **P-12** ✔ | `ui/settings_tab.py:745` | les trois | `QProcess.startDetached(sys.executable, sys.argv)` : si le logiciel a été lancé par `python -m phytoscope`, relancer `__main__.py` casse les imports relatifs. C'est le chemin nominal du changement de langue. |
| **P-13** ✔ | `core/logging_setup.py:91-93` | Windows | Windows ne renomme pas un fichier ouvert ailleurs : deux instances font échouer la rotation avec `PermissionError`. |

## Cosmétiques

- `__main__.py:352` `sys.stdout.flush()` : avec le point d'entrée `gui-scripts`,
  Windows produit un `.exe` sans console, `sys.stdout` vaut `None`.
- `config.py:358` : `--settings reglages.json` (chemin relatif nu) →
  `os.makedirs("")` lève `FileNotFoundError`. Les trois plateformes.
- `core/console.py:49-56` : `SetConsoleMode(…, 7)` écrase les bits existants au
  lieu d'un OU avec le mode courant.
- `recorder.py:341` et `samples.py:349` `_slug()` : `ch.isalnum()` laisse passer
  les accents. Sur macOS, APFS normalise en NFD tandis que le chemin mémorisé
  est en NFC → une comparaison exacte peut échouer. Aucun filtre contre `CON`,
  `AUX`, `NUL` sous Windows.
- `widgets.py:458` (6,2 pt) et `features_tab.py:111` (7,5 pt) : le point Qt vaut
  1/72 pouce à 72 dpi logiques sous macOS contre 96 ailleurs → ~25 % plus petit.
- Aucun réglage High-DPI explicite : **c'est le bon choix** avec Qt 6.

## Micrologiciel (outil de développement)

`src/src/firmware/build.sh` est **bash strict, Linux
x86-64 seulement** : URL de la chaîne ARM codée en `x86_64` (`:22,61`) — échoue
sur Apple Silicon et sur Raspberry Pi ; chemin de programmation
`/media/$USER/RP2350/` (`:118`) propre à Debian/Ubuntu (Fedora monte sous
`/run/media/`, macOS sous `/Volumes/`). Sous Windows, WSL est obligatoire.

## Fabrication des PDF (chaîne séparée)

WeasyPrint reste lié à Pango, HarfBuzz et fontconfig, non fournis par la roue :
`apt`/`dnf` sous Linux, `brew install pango libffi` sous macOS (plus
`DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` sur Apple Silicon), runtime GTK3
sous Windows — le cas le plus fragile. `build_carte.py:271` appelle `pdfinfo`,
absent par défaut partout. **Ces prérequis ne sont documentés nulle part** :
`platform_info.py:192-231` ne connaît que `qt`, `audio`, `midi`, `python`.
