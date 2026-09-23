#  ==========================================================================
#  PhytoScope — attribution — sources/schematics/biotron-firmware/PLSDK/CMakeLists.txt
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

cmake_minimum_required(VERSION 3.13)
project(PLSDK
        VERSION 2.0.0
        DESCRIPTION "Abstraction library for Playtronica projects"
        LANGUAGES C CXX ASM
)


add_library(PLSDK_lib STATIC
        src/cap_buttons.c
        src/commands.c
        src/PLSDK.c
        src/music.c
        src/usb_descriptors.c
)


target_link_libraries(PLSDK_lib PUBLIC pico_unique_id pico_stdlib tinyusb_device)
target_include_directories(PLSDK_lib PUBLIC include)
