# Portability — survey of 2026-09-18

Analysis requested on 2026-09-18: Windows 10/11, macOS (Darwin, Intel and
Apple Silicon), GNU/Linux (Debian, Ubuntu, Mint, Fedora, Red Hat). Scope: the
`phytoscope/` package, `tools/`, `run.py`, `Makefile`, `make.bat`. The
firmware and the PDF build are treated separately; those are development
tools.

**Everything was fixed on 2026-09-18 (version 1.5.1).** This file remains as
the original survey: it says what was broken, why, and what not to do again.
The state of each fix is in the "✔" column.

What is **not** verified: none of these fixes has run on a real Windows
machine or on a Mac. They are verified by reading the code and by the 42 tests
in `tests/test_portability.py`, which check under Linux what only shows up
elsewhere.

## What is already right — and must not be broken

- `config.py:21-29` `config_dir()` and `:32-40` `data_dir()` honour all three
  conventions: `%APPDATA%\PhytoScope`,
  `~/Library/Application Support/PhytoScope`, `$XDG_CONFIG_HOME`.
- `disk_space.py:73` uses `shutil.disk_usage`, which is portable. There is
  **no `os.statvfs`** anywhere in the project.
- No text `open()` without `encoding=`. The CSV files carry `newline=""`,
  which is essential on Windows.
- No path built by concatenating `+ "/"`. Everything goes through
  `os.path.join`.
- No `fcntl`, `termios`, `pwd`, `grp`, `resource`, `posix` or `os.uname`, and
  no `os.system`. Only `SIGINT` and `SIGTERM` are installed, and `SIGTERM` is
  guarded by `hasattr` (`interrupt.py:145-147`).
- Serial ports are discovered through `serial.tools.list_ports.comports()`: no
  hardcoded `/dev/ttyACM*` or `COM*` pattern.
- Linux-only code is properly guarded (`audio_quiet.py`, `preflight.py`,
  `usbdiag._from_sysfs`).
- `platform_info.py` covers apt and dnf/yum, including the `dnf`→`yum`
  fallback for older RHEL.

## Blocking

| № (✔ = fixed) | File | Platforms | Finding |
|---|---|---|---|
| **P-1** ✔ | `core/protocol.py:38-39`, `core/usbdiag.py:38-39,43`, `config.py:255-256` | all three, worse on Windows | The software looked for `0x2E8A:0x10F5`; **the firmware declares `0x1209:0x7A01`** (`usb_descriptors.c:40-41`). The board was therefore never recognised by VID/PID. The fallback on product name (`protocol.py:132-134`) saves Linux and macOS; on Windows `pyserial` does not fill in `product` and `description` reads `"USB Serial Device (COMx)"` — **the control link is unusable**. The firmware is right: `0x1209` is the free pid.codes range, `0x2E8A` belongs to Raspberry Pi. **It is the software that had to be corrected.** |
| **P-2** ✔ | `core/sources.py:258-261`, `config.py:50` | Windows, macOS | `sd.InputStream(samplerate=250.0)`: CoreAudio and WASAPI refuse it, ALSA resamples. The fallback to the internal generator works, so the software starts — but the "audio input" source is unusable. Fix: open at the device's `default_samplerate` (already read at `sources.py:225`) and decimate in software. |
| **P-3** ✔ | `requirements.txt:14-20` | all three | `python-rtmidi` and `pyttsx3` were on hard lines. `python-rtmidi` is C++ with no wheel for recent Pythons: a failure on that line makes `make install` fail **entirely**, and the user ends up without NumPy or PySide6. `pyproject.toml:33-35` classes them correctly as a `complet` extra. |
| **P-4** ✔ | `core/console.py:95,130-132,155`, `__main__.py:268,534`, `usbdiag.py:265` | Windows | No `sys.stdout.reconfigure(encoding="utf-8")`. In a real console Python goes through the UTF-16 API and the text appears; **as soon as the output is redirected** (`run.py --check > report.txt`), cp1252 takes over and `print()` raises `UnicodeEncodeError` — precisely when you are trying to diagnose something. |

## Degraded

| № (✔ = fixed) | File | Platforms | Finding |
|---|---|---|---|
| **P-5** ✔ | ~20 places (`widgets.py:448`, `tabs.py:332`, `log_window.py:88,107`, `help_dialog.py:207`…) | Windows, macOS | "DejaVu Sans Mono" hardcoded **with no fallback**. Only `theme.py:91` declares `, monospace`. DejaVu exists on neither Windows nor macOS: Qt often substitutes a **proportional** face, and the alignment of value tables breaks. Fix: a single `police_mono()` function setting `setStyleHint(QFont.Monospace)` and `setFamilies(["DejaVu Sans Mono","Menlo","Consolas","Courier New"])`. |
| **P-6** ✔ | `ui/help_dialog.py:33-77` | macOS | The shortcuts were re-displayed **hardcoded** ("Ctrl+R") while Qt renders them as ⌘R. The `_normaliser()` function (`:309-322`) already does the right thing but was only used for comparison. |
| **P-7** ✔ | `ui/main_window.py:275` | macOS | `Ctrl+.`: ⌘. is historically "cancel" on macOS; a possible conflict with the MIDI panic. |
| **P-8** ✔ | `core/sources.py:232-238,225,258`, `ui/settings_tab.py:213-222,657` | Windows | The audio device was chosen **by name**. Windows exposes the same hardware over MME, DirectSound, WASAPI and WDM-KS under near-identical names, and **MME truncates at 31 characters**: the resolution often landed on MME, the worst API. `hostapi` was read (`sources.py:226`) and never used. |
| **P-9** ✔ | `music/midi_out.py:63` | Windows | `open_virtual_port()` does not exist in the Windows MM API. The exception was caught, but the user was not told they need loopMIDI. |
| **P-10** ✔ | `music/voice.py:124` | settings portability | `espeak -v <voice>` receives a SAPI/pyttsx3 identifier when `reglages.json` came from Windows → a logged failure at every utterance. |
| **P-11** ✔ | `music/voice.py:77,239,310,256-258` | Windows | COM apartment affinity: the SAPI5 object is created in one thread and used in the `phytoscope-voix` thread. **A risk identified, not verified by running it.** The SAPI-through-PowerShell fallback (`:175`) does not have this problem. |
| **P-12** ✔ | `ui/settings_tab.py:745` | all three | `QProcess.startDetached(sys.executable, sys.argv)`: if the software was started with `python -m phytoscope`, restarting `__main__.py` breaks the relative imports. That is the nominal path for a language change. |
| **P-13** ✔ | `core/logging_setup.py:91-93` | Windows | Windows will not rename a file another process holds open: two instances make the rotation fail with `PermissionError`. |

## Cosmetic

- `__main__.py:352` `sys.stdout.flush()`: with the `gui-scripts` entry point,
  Windows produces an `.exe` with no console and `sys.stdout` is `None`.
- `config.py:358`: `--settings reglages.json` (a bare relative path) →
  `os.makedirs("")` raises `FileNotFoundError`. All three platforms.
- `core/console.py:49-56`: `SetConsoleMode(…, 7)` overwrites the existing bits
  instead of OR-ing with the current mode.
- `recorder.py:341` and `samples.py:349` `_slug()`: `ch.isalnum()` lets accents
  through. On macOS, APFS normalises to NFD while the remembered path is NFC →
  an exact comparison can fail. No filter against `CON`, `AUX` or `NUL` on
  Windows.
- `widgets.py:458` (6.2 pt) and `features_tab.py:111` (7.5 pt): the Qt point is
  1/72 inch at 72 logical dpi on macOS against 96 elsewhere → about 25 %
  smaller.
- No explicit High-DPI setting: **that is the right choice** with Qt 6.

## Firmware (a development tool)

The two findings below **were fixed on 2026-09-22**; the text is kept because
the reasoning still applies to anyone forking the script.

`src/firmware/_make_.sh` was **strict bash, Linux x86-64 only**: the ARM
toolchain URL hardcoded `x86_64` (`:22,61`) — which failed on Apple Silicon and
on a Raspberry Pi alike — and the flashing path `/media/$USER/RP2350/` (`:118`)
was Debian/Ubuntu-specific (Fedora mounts under `/run/media/`, macOS under
`/Volumes/`). It now derives the host triple from `uname -s`/`uname -m` and
searches for the mount point rather than assuming one. On Windows, WSL remains
mandatory.

## PDF build (a separate chain)

WeasyPrint is still bound to Pango, HarfBuzz and fontconfig, which its wheel
does not supply: `apt`/`dnf` on Linux, `brew install pango libffi` on macOS
(plus `DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib` on Apple Silicon), the
GTK3 runtime on Windows — the most fragile case. `build_board.py:271` calls
`pdfinfo`, which is absent by default everywhere. **None of these
prerequisites is documented anywhere**: `platform_info.py:192-231` knows only
`qt`, `audio`, `midi` and `python`.
