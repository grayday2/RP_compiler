cmake_minimum_required(VERSION 3.13)

# Keep the tested board behavior; the physical Flash size is still unverified.
set(PICO_BOARD waveshare_rp2040_zero)
set(PICO_FLASH_SIZE_BYTES 4194304 CACHE STRING "Flash size used by the original working build")
set(PICO_NO_PICOTOOL 1)
# This selects the same implementation as the original board/compile_time_choice.
set(PICO_DEFAULT_BOOT_STAGE2 boot2_w25q080)

if(CMAKE_HOST_WIN32)
    set(CMAKE_SYSTEM_NAME Generic)
    set(CMAKE_SYSTEM_PROCESSOR arm)
    set(TOOLCHAIN_PREFIX "${CMAKE_CURRENT_LIST_DIR}/toolchain/bin/arm-none-eabi-")
    set(CMAKE_C_COMPILER "${TOOLCHAIN_PREFIX}gcc.exe")
    set(CMAKE_CXX_COMPILER "${TOOLCHAIN_PREFIX}g++.exe")
    set(CMAKE_ASM_COMPILER "${TOOLCHAIN_PREFIX}gcc.exe")
endif()

include(pico_sdk_import.cmake)
project(my_portable_os C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()

if(NOT EXISTS "${CMAKE_CURRENT_LIST_DIR}/main.cpp")
    message(FATAL_ERROR "Add the current main.cpp before building firmware")
endif()
add_executable(blink_zero main.cpp)
pico_enable_stdio_usb(blink_zero 0)
pico_enable_stdio_uart(blink_zero 0)
target_include_directories(blink_zero PRIVATE
    "${CMAKE_CURRENT_LIST_DIR}"
    "${PICO_SDK_PATH}/lib/tinyusb/src"
    "${PICO_SDK_PATH}/lib/tinyusb/hw"
)

set(LIB_DIR "${CMAKE_CURRENT_LIST_DIR}/libraries")
file(MAKE_DIRECTORY "${LIB_DIR}")
function(add_lib_to_target TARGET LIB_PATH)
    target_include_directories(${TARGET} PRIVATE "${LIB_PATH}")
    foreach(SUBDIR include src)
        if(EXISTS "${LIB_PATH}/${SUBDIR}")
            target_include_directories(${TARGET} PRIVATE "${LIB_PATH}/${SUBDIR}")
        endif()
    endforeach()
    file(GLOB_RECURSE LIB_SRC CONFIGURE_DEPENDS
        "${LIB_PATH}/*.c" "${LIB_PATH}/*.cpp" "${LIB_PATH}/*.S" "${LIB_PATH}/*.s")
    list(FILTER LIB_SRC EXCLUDE REGEX "/(examples|tests|test|docs|build|\\.git)/")
    if(LIB_SRC)
        target_sources(${TARGET} PRIVATE ${LIB_SRC})
    endif()
endfunction()
file(GLOB ALL_LIBS LIST_DIRECTORIES true "${LIB_DIR}/*")
foreach(LIB ${ALL_LIBS})
    if(IS_DIRECTORY "${LIB}")
        add_lib_to_target(blink_zero "${LIB}")
    endif()
endforeach()

target_link_libraries(blink_zero PRIVATE
    pico_stdlib tinyusb_device hardware_gpio hardware_i2c hardware_spi
    hardware_adc hardware_pwm hardware_pio hardware_clocks hardware_uart
    hardware_flash hardware_watchdog
)
