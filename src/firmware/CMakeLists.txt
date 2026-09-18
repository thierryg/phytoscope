#  ==========================================================================
#  PhytoScope — attribution — src/firmware/CMakeLists.txt
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

# Le flux de mesure passe par l'USB : on libère la console série matérielle.
pico_enable_stdio_usb(phytosense 0)
pico_enable_stdio_uart(phytosense 0)

pico_add_extra_outputs(phytosense)
