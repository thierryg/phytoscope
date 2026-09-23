#  ==========================================================================
#  PhytoScope — attribution — src/firmware/CMakeLists.txt
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

# ---------------------------------------------------------------------------
#  Micrologiciel PhytoSense One — RP2350
#  Licence MIT — Bretagne Namasté
# ---------------------------------------------------------------------------
cmake_minimum_required(VERSION 3.13)

include(pico_sdk_import.cmake)
project(phytosense C CXX ASM)
set(CMAKE_C_STANDARD 11)
pico_sdk_init()

add_executable(phytosense
    main.c
    afe.c
    protocol.c
    usb_descriptors.c
)

target_include_directories(phytosense PRIVATE ${CMAKE_CURRENT_LIST_DIR})

target_link_libraries(phytosense
    pico_stdlib
    pico_multicore
    pico_unique_id
    hardware_spi
    hardware_dma
    hardware_i2c
    hardware_pwm
    hardware_clocks
    tinyusb_device
    tinyusb_board
)

# The measurement stream goes over USB, so the hardware serial console is
# released.
pico_enable_stdio_usb(phytosense 0)
pico_enable_stdio_uart(phytosense 0)

pico_add_extra_outputs(phytosense)
