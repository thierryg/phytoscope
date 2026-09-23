# PhytoSense One firmware

Firmware for the acquisition board described in *The PhytoSense Board*.

**Target**: RP2350 (Raspberry Pi) · **SDK**: Pico SDK 2.0 or newer · **USB stack**: TinyUSB
**Licence**: MIT · Bretagne Namasté — https://bretagne-namaste.com

---

## 1. What it does, and what it does not

It does four things, and nothing else:

1. it clocks the ADS131M04 converter and reads its four channels;
2. it **timestamps** every sample with a 64-bit counter driven by the TCXO;
3. it pushes the stream over USB as **audio class 2.0**, with no driver;
4. it answers the control dialogue on the virtual serial port.

It **interprets nothing**: no event detection, no musical rule, no filtering
beyond the converter's own. All of that is computed on the computer, where it
can be changed, checked and replaced.

The one exception is the **direct MIDI output**, which carries a reduced
version of the mapping engine so as to drive a hardware synthesizer without
going through the computer's audio chain. It does not make the board
independent: the computer is still needed to set it up, to receive the stream
and to record.

### How the two cores divide the work

| Core | Task | Constraint |
|---|---|---|
| 0 | USB, control dialogue, environmental sensors, MIDI, display | may block without consequence |
| 1 | Servicing the converter, timestamping, the ring buffer | bounded loop, no allocation, no I/O |

`main()` runs on core 0 by definition, and `multicore_launch_core1()` starts
the measurement loop on core 1. Until 2026-09-23 the function was named
`coeur0_boucle` and this table said the opposite: the code was right and the
names were wrong, so the names were changed. Which core does which does not
matter — that they are separate does.

The two cores share nothing but the ring buffer, through atomic indices. That
is why the stream has no gaps even while the computer is interrogating the
board in the middle of an acquisition.

---

## 2. Where to get the SDK for the RP2350

The RP2350 requires **Pico SDK 2.0.0 as a minimum** — the 1.x versions know
only the RP2040 and will fail at configuration time. 2.1.x or newer is
recommended.

### The SDK

```bash
git clone --branch 2.1.1 https://github.com/raspberrypi/pico-sdk.git
cd pico-sdk
git submodule update --init          # essential: TinyUSB is a submodule
export PICO_SDK_PATH=$PWD            # put this in ~/.bashrc or ~/.zshrc
```

> **Forgetting `git submodule update --init` is mistake number one.** Without
> it, `tinyusb` stays empty and the build fails on `tusb.h: No such file`.

| Item | Address |
|---|---|
| Pico SDK (official repository) | https://github.com/raspberrypi/pico-sdk |
| SDK documentation | https://www.raspberrypi.com/documentation/pico-sdk/ |
| RP2350 datasheet | https://datasheets.raspberrypi.com/rp2350/rp2350-datasheet.pdf |
| RP2350 hardware design guide | https://datasheets.raspberrypi.com/rp2350/hardware-design-with-rp2350.pdf |
| Official examples | https://github.com/raspberrypi/pico-examples |
| TinyUSB (documentation) | https://docs.tinyusb.org/ |

### The cross toolchain

| System | Command |
|---|---|
| Debian, Ubuntu, Mint | `sudo apt install cmake gcc-arm-none-eabi libnewlib-arm-none-eabi libstdc++-arm-none-eabi-newlib git python3` |
| Fedora, RHEL, Rocky | `sudo dnf install cmake arm-none-eabi-gcc-cs arm-none-eabi-newlib git python3` |
| Arch, Manjaro | `sudo pacman -S cmake arm-none-eabi-gcc arm-none-eabi-newlib git python` |
| macOS (Homebrew) | `brew install cmake`, then `brew install --cask gcc-arm-embedded` |
| Windows | The official **Pico SDK for Windows** installer — https://github.com/raspberrypi/pico-setup-windows |

On Debian and Ubuntu, check that `arm-none-eabi-gcc` is at least version 10:
`arm-none-eabi-gcc --version`. Older versions do not know the RP2350's
Cortex-M33 core.

### The `pico_sdk_import.cmake` file

It is not shipped here: it belongs to the SDK and must be copied from it, so
that it stays in step with it.

```bash
cp "$PICO_SDK_PATH/external/pico_sdk_import.cmake" .
```

### Installing nothing at all

The **Raspberry Pi Pico** extension for Visual Studio Code downloads the SDK,
the toolchain and the debugging tools by itself:
https://marketplace.visualstudio.com/items?itemName=raspberry-pi.raspberry-pi-pico

---

## 3. Building

**Two scripts, two uses.**

| | What it does | When to use it |
|---|---|---|
| **`./_make_.sh`** | builds, and nothing more → `build/phytosense.uf2` | while developing |
| **`./build.sh`** | builds **and files the deliverable** under `build/packages/`, named with its version | for a release |

```bash
./build.sh --deps     # Pico SDK and ARM toolchain in $HOME, no sudo — once
./build.sh            # build and file the deliverable
```

The first command installs the SDK and the cross toolchain **under the home
directory, without privileges** (`C-55`). The second produces:

```
build/phytosense.uf2                        what the build produces
build/packages/<version>-<timestamp>/Firmware/
    phytosense-<version>.uf2                what you copy onto the board
    phytosense-<version>.elf                for debugging
    phytosense-<version>.bin                the raw image
    phytosense-<version>.sha256             the checksums
    README.txt                              how to flash the board
```

**Why the file carries its version**: a bare "phytosense.uf2" on somebody's
disk six months later does not say which version it came from. And the `.uf2`
is a deliverable in its own right — without it, the packages install software
that has nothing to listen to.

### The options

| Option | Effect |
|---|---|
| `--deps` | installs the Pico SDK and the ARM toolchain under `$HOME` |
| `--clean` | starts again from an empty build directory |
| `--output DIR` | files the deliverable somewhere else |
| `--no-install` | builds only, like `./_make_.sh` |

The older French names — `--propre`, `--sortie`, `--sans-installer` — are all
still accepted, so that a script or a habit built on them keeps working.

`build.sh` hands `_make_.sh` everything it does not recognise, so the build
options remain `_make_.sh`'s own.

### By hand, for anyone who prefers it

```bash
export PICO_SDK_PATH=/path/to/pico-sdk
cp "$PICO_SDK_PATH/external/pico_sdk_import.cmake" .
mkdir -p build && cd build
cmake .. -DPICO_BOARD=pico2 -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
# -> phytosense.uf2, phytosense.elf, phytosense.bin
```

`-DPICO_BOARD=pico2` selects the RP2350. For a bare board with no ready-made
board definition: `-DPICO_PLATFORM=rp2350 -DPICO_BOARD=none`.

### If `cmake` refuses to start

```
CMake Error: The current CMakeCache.txt directory … is different than
the directory … where CMakeCache.txt was created.
```

A CMake cache remembers the **absolute path** of the sources, so moving or
renaming the working copy makes it stale. `_make_.sh` now detects that and
throws the cache away itself — this message should no longer appear. Should it
happen anyway: `rm -rf build`.

---

## 4. Flashing the board

### Route 1 — drag and drop (the simplest)

1. hold **BOOTSEL** down;
2. plug the USB cable in, or press RESET briefly;
3. release BOOTSEL: a volume named `RP2350` appears;
4. copy `phytosense.uf2` onto it;
5. the board restarts by itself and enumerates.

No tool, no driver, no administrative rights. This is the normal route.

### Route 2 — a debug probe (for development)

A second Pico board turned into a probe is enough. It brings single-stepping,
breakpoints and a serial console.

```bash
# upload
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg \
        -c "adapter speed 5000" -c "program phytosense.elf verify reset exit"

# debug
openocd -f interface/cmsis-dap.cfg -f target/rp2350.cfg -c "adapter speed 5000" &
arm-none-eabi-gdb phytosense.elf -ex "target extended-remote localhost:3333"
```

| Item | Address |
|---|---|
| Probe (the `debugprobe` firmware) | https://github.com/raspberrypi/debugprobe |
| OpenOCD, Raspberry Pi branch | https://github.com/raspberrypi/openocd |

The board's SWD connector is a three-pin 1.27 mm header, marked `SWD` in the
silkscreen: SWCLK, SWDIO, ground.

### Route 3 — an update by the end user

The PhytoScope software detects a firmware version older than the one it
carries and offers to update it. The update goes through the same UF2
interface: the board restarts in bootloader mode, the file is copied, the board
comes back. The user sees nothing but a progress bar.

---

## 5. The other programmable parts

| Part | What is written to it | How |
|---|---|---|
| **U30** RP2350 | the firmware | UF2 or SWD, see above |
| **U31** W25Q128 (QSPI flash) | the firmware and the stored settings | through the RP2350 |
| **24AA02 EEPROM** on the daughter boards | type, serial number, date and calibration coefficients | once, in manufacturing |
| **DS5** SSD1306 display | nothing — an initialisation sequence only | sent by the firmware at every start |
| **U10** ADS131M04 | the MODE, CLOCK and GAIN registers | written by `afe_init()` at every start |
| **U63** INA219 | the configuration register and the shunt calibration | written by the firmware |

The daughter board's memory is the only part to be programmed **once, in
manufacturing**. Everything else is rebuilt at every power-up: a board that
loses its configuration does not exist.

### Flash memory map

| Address | Size | Content |
|---|---|---|
| `0x10000000` | 1 MB | firmware |
| `0x10100000` | 4 kB | stored settings (gain, range, MIDI profile) |
| `0x10101000` | 4 kB | factory calibration — written at acceptance, never erased |
| `0x10102000` | the rest | a ring log of events |

---

## 6. Files

| File | Role | Lines |
|---|---|---|
| `main.c` | the two cores' loops, timestamping, ring buffer, USB hand-off | 274 |
| `afe.c` / `afe.h` | converter, gain, range, self-test, daughter-board memory | 462 + 80 |
| `protocol.c` / `protocol.h` | the control dialogue, JSON replies | 301 + 48 |
| `usb_descriptors.c` | descriptors for the composite UAC2 + CDC device | 254 |
| `tusb_config.h` | TinyUSB configuration | 88 |
| `CMakeLists.txt` | the build | 54 |
| `_make_.sh` | builds — SDK, ARM toolchain, cmake | — |
| `build.sh` | builds **and files the deliverable** under `build/packages/` | — |

The USB side of all this — every descriptor with its wire bytes, the frame
layout, the control protocol, and what each host makes of the device — is
documented in **`sources/usb/reference.html`**, which renders to a 21-page
`USB-Device-Reference.pdf`.

---

## 7. Checking that the firmware works

With nothing installed but a terminal:

```bash
# Linux or macOS
screen /dev/ttyACM0 115200        # or: picocom -b 115200 /dev/ttyACM0
# Windows: PuTTY, serial connection, 115200 baud
```

On macOS use `/dev/cu.usbmodem*` and not `/dev/tty.*`: the `tty` node waits for
carrier detect, which a CDC device never asserts, so opening it blocks.

Type `?` and Enter. The board must answer in one line:

```
+{"model":"PhytoSense One","serial":"PS1-4A17C302","firmware":"1.0.0",
  "channels":4,"sample_rate":250.0,"frontend":"FE-Z", ... }
```

If that line appears, the microcontroller, the USB stack, the converter and the
daughter board's memory are all four working. If it does not, chapter 10 of the
board document says what to look for, and in what order. The baud rate is a
fiction — CDC-ACM carries one because it emulates a UART, and the board ignores
it; any setting works.

---

## 8. The state of this publication

**These sources build.** They produce `phytosense.uf2` (80 kB),
`phytosense.elf` (764 kB) and `phytosense.bin` (40 kB), for 44,784 bytes of
code and 106,508 of data. Continuous integration builds them on every push —
`.github/workflows/packages.yml`, the `firmware` job — and attaches the
deliverable to the artefacts with its checksums.

> Until 2026-09-18 this section said the sources "had not been built here".
> That was true when it was written, and it is what constraint `C-3` exists to
> correct: **verify before asserting.** The build is now automatic, and the
> figures above come from `arm-none-eabi-size`.

### What remains to be proven, and cannot be proven here

**No board has been plugged in.** What builds is not what works: the
converter's configuration, the pin assignment and the response times all need
the hardware. So expect to adjust:

- a pin, depending on your board's final assignment;
- the input stage's gain constants;
- the timings of the dialogue with the converter.

What is sound, on the other hand, and what took the work: the timestamping
discipline, the separation of the two cores, and the control dialogue — all of
which can be exercised without a board, through a serial terminal (see § 7).

### Divergences between the descriptors and the behaviour

Found on 2026-09-23 while writing the USB reference, recorded in its section
11, and **all three settled the same day**. They are kept here because a board
flashed with an earlier firmware still shows them.

1. **The UAC2 clock source: settled.** The descriptor advertises a readable
   sample frequency, and until 2026-09-23 the board stalled the request —
   `tud_audio_get_req_entity_cb` was not defined, and TinyUSB's weak default
   logs a line and returns `false`. `usb_descriptors.c` now defines both
   entity callbacks and answers **250 Hz**, the rate the converter really
   runs at, with a `RANGE` of one sub-range (`bMin = bMax = 250`, `bRes = 0`)
   — which is how UAC2 says a value is fixed, and agrees with
   `AUDIO_CLOCK_SOURCE_ATT_INT_FIX_CLK` in the descriptor.

   A host whose audio stack refuses rates below 8 kHz may still refuse the
   stream. **That refusal is the correct outcome**: reporting a rate the board
   does not use would make every timestamp the host derives silently wrong,
   for as long as the recording lasts. A host that refuses says so at plug-in.
   The control port (CDC) describes the same stream and owes nothing to the
   audio class's rate conventions.

   The rate now has **one** home, `AFE_RATE_HZ` in `afe.h`: `main.c` starts
   the converter with it, `protocol.c` reports it to `identify`, and
   `usb_descriptors.c` answers the host with it. It had been written down
   three times, independently.

2. **The isochronous packet: settled.** It was 256 bytes, with a comment
   claiming it covered the 32 kHz mode. It did not: the drain loop fills a
   frame with *whole* sample sets, so 256 bytes gave 21 sets — 252 used, four
   wasted every frame — and a ceiling near 21 kHz, above which samples stayed
   in the ring and were counted as lost.

   `CFG_TUD_AUDIO_EP_SZ_IN` is now **384**, which is 32 × 12 exactly. A
   `TU_VERIFY_STATIC` in `main.c` makes a packet that is not a whole number of
   sample sets a build error. The cost: a host reserves 384 bytes of every
   frame once it selects alternate setting 1, used or not — 37 % of what one
   isochronous endpoint may claim at full speed, on a bus running at three
   parts in a thousand. Alternate setting 0 reserves nothing.

3. **The phantom mute and volume: settled.** The feature unit declared mute
   and volume read/write on the master and all four channels, because
   TinyUSB's microphone template declares them, and nothing was wired to
   them — a host offered a slider that did nothing, and an application could
   set it, read it back unchanged, and believe it.

   **The audio function is now written out by hand** in `usb_descriptors.c`,
   thirteen descriptors instead of `TUD_AUDIO_MIC_FOUR_CH_DESCRIPTOR`, and the
   feature unit declares `AUDIO_CTRL_NONE` everywhere. A host shows no slider,
   and a request about a control that was never advertised is stalled — which
   is the right answer to it. The entity graph and the 219-byte length are
   unchanged: entity numbers are what a host addresses, and the USB reference
   documents them.

   Gain is *not* a volume control. It changes the measurement's **full
   scale**, and the control port's `gain` command exists because the change
   has to be recorded in the session metadata next to the samples it applies
   to. A mixer slider has nowhere to write that.

### A dependency worth watching

`usb_descriptors.c` relies on the `TUD_AUDIO_MIC_FOUR_CH_DESCRIPTOR` macro,
present in TinyUSB since the version shipped with SDK 2.0. The SDK in use is
pinned in `_make_.sh` (`SDK_VERSION`), and `tools/sbom.py` reads it from there:
the project's bill of materials therefore always says which version is in
service.
