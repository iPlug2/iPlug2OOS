cmake_minimum_required(VERSION 3.14)
project(VisageTemplate VERSION 1.0.0)

# Use static runtime on Windows to match iPlug2 (must be set before any targets)
if(MSVC)
  set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>" CACHE STRING "" FORCE)
endif()

# Set up iPlug2 paths
set(IPLUG2_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../iPlug2 CACHE PATH "iPlug2 root directory")
include(${IPLUG2_DIR}/iPlug2.cmake)
find_package(iPlug2 REQUIRED)

# Include Visage support from iPlug2
include(${IPLUG2_DIR}/Scripts/cmake/Visage.cmake)

# Visage UI Library via FetchContent
include(FetchContent)
FetchContent_Declare(visage
  GIT_REPOSITORY https://github.com/iPlug2/visage.git
  GIT_TAG claude/compile-with-mt-flag-01GA2wfzj1g7Ki8NgB2SLGWA
  EXCLUDE_FROM_ALL
)
set(VISAGE_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(VISAGE_BUILD_TESTS OFF CACHE BOOL "" FORCE)
set(VISAGE_ENABLE_WIDGETS ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(visage)

# Link visage to iPlug2::Visage so the delegate can find it
target_link_libraries(iPlug2_Visage PUBLIC visage)

# ============================================================================
# Visage Libraries Target - builds only static libraries for non-CMake linking
# ============================================================================
# Output directory for collected static libraries
set(VISAGE_LIB_OUTPUT_DIR ${CMAKE_BINARY_DIR}/visage-libs/$<CONFIG>)

# Custom target to build all visage static libraries
add_custom_target(visage-libs
  COMMENT "Building Visage static libraries for external linking"
)

# Depend on all visage and dependency targets (only actual STATIC library targets)
add_dependencies(visage-libs
  visage
  VisageEmbeddedFonts
  VisageEmbeddedIcons
  VisageEmbeddedShaders
  bgfx
  bimg
  bimg_decode
  bimg_encode
  bx
  freetype
)

# Copy all static libraries to output directory after build
add_custom_command(TARGET visage-libs POST_BUILD
  COMMAND ${CMAKE_COMMAND} -E make_directory "${VISAGE_LIB_OUTPUT_DIR}"
  # Visage main library (contains all object libraries)
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:visage> "${VISAGE_LIB_OUTPUT_DIR}/"
  # Visage embedded resources
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:VisageEmbeddedFonts> "${VISAGE_LIB_OUTPUT_DIR}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:VisageEmbeddedIcons> "${VISAGE_LIB_OUTPUT_DIR}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:VisageEmbeddedShaders> "${VISAGE_LIB_OUTPUT_DIR}/"
  # bgfx/bx/bimg dependencies
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:bgfx> "${VISAGE_LIB_OUTPUT_DIR}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:bimg> "${VISAGE_LIB_OUTPUT_DIR}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:bimg_decode> "${VISAGE_LIB_OUTPUT_DIR}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:bimg_encode> "${VISAGE_LIB_OUTPUT_DIR}/"
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:bx> "${VISAGE_LIB_OUTPUT_DIR}/"
  # freetype (rename to freetype.lib regardless of config since freetype adds 'd' suffix for debug)
  COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_FILE:freetype> "${VISAGE_LIB_OUTPUT_DIR}/freetype.lib"
  COMMENT "Copying Visage libraries to ${VISAGE_LIB_OUTPUT_DIR}"
)

set(PROJECT_DIR ${CMAKE_CURRENT_SOURCE_DIR})
set(PLUG_RESOURCES_DIR ${PROJECT_DIR}/resources)

set(SOURCE_FILES
  VisageTemplate.cpp
  VisageTemplate.h
  resources/resource.h
)

# create a private library target called "__${PROJECT_NAME}-base" for shared code
add_library(_${PROJECT_NAME}-base INTERFACE)
iplug_add_target(_${PROJECT_NAME}-base INTERFACE
  INCLUDE ${PROJECT_DIR} ${PROJECT_DIR}/resources
  LINK iPlug2::Visage
)

# ============================================================================
# macOS/Windows targets (not iOS, not Emscripten)
# ============================================================================
if(NOT IOS AND NOT CMAKE_SYSTEM_NAME STREQUAL "Emscripten")
  # ============================================================================
  # APP Target (Standalone Application) - with Visage UI
  # ============================================================================
  set(APP_SOURCES ${SOURCE_FILES})

  # Add Windows resource file for dialog/menu resources
  if(WIN32)
    list(APPEND APP_SOURCES ${PLUG_RESOURCES_DIR}/main.rc)
  endif()

  add_executable(${PROJECT_NAME}-app ${APP_SOURCES})
  iplug_add_target(${PROJECT_NAME}-app PUBLIC
    LINK iPlug2::APP _${PROJECT_NAME}-base
    RESOURCE ${RESOURCES}
  )
  iplug_configure_target(${PROJECT_NAME}-app APP ${PROJECT_NAME})

  # ============================================================================
  # VST3 Target - with Visage UI
  # ============================================================================
  add_library(${PROJECT_NAME}-vst3 MODULE ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}-vst3 PUBLIC
    LINK iPlug2::VST3 _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}-vst3 VST3 ${PROJECT_NAME})

  # ============================================================================
  # CLAP Target - with Visage UI
  # ============================================================================
  add_library(${PROJECT_NAME}-clap MODULE ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}-clap PUBLIC
    LINK iPlug2::CLAP _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}-clap CLAP ${PROJECT_NAME})

  # ============================================================================
  # CLI Target (Command Line Interface) - NO UI, for offline processing
  # ============================================================================
  add_executable(${PROJECT_NAME}-cli
    VisageTemplate.cpp
    VisageTemplate.h
    resources/resource.h
  )
  iplug_add_target(${PROJECT_NAME}-cli PUBLIC
    INCLUDE ${PROJECT_DIR} ${PROJECT_DIR}/resources
    LINK iPlug2::CLI
  )
  iplug_configure_cli(${PROJECT_NAME}-cli ${PROJECT_NAME})
endif()

# ============================================================================
# AUv2 Target (macOS only) - with Visage UI
# ============================================================================
if(APPLE AND NOT IOS)
  add_library(${PROJECT_NAME}-au MODULE ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}-au PUBLIC
    LINK iPlug2::AUv2 _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}-au AUv2 ${PROJECT_NAME})
endif()

# ============================================================================
# AUv3 Targets (macOS only) - Framework + Appex embedded in APP
# ============================================================================
if(APPLE AND NOT IOS)
  # Framework containing AUv3 plugin code
  add_library(${PROJECT_NAME}AU-framework SHARED ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}AU-framework PUBLIC
    LINK iPlug2::AUv3 _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}AU-framework AUv3Framework ${PROJECT_NAME})

  # App Extension (appex) - executable using NSExtensionMain entry point
  add_executable(${PROJECT_NAME}AUv3-appex
    ${PLUG_RESOURCES_DIR}/${PROJECT_NAME}AUv3Appex.m
  )
  iplug_configure_target(${PROJECT_NAME}AUv3-appex AUv3Appex ${PROJECT_NAME})

  # Embed AUv3 appex in the existing APP target
  iplug_embed_auv3_in_app(${PROJECT_NAME}-app ${PROJECT_NAME})
endif()

# ============================================================================
# iOS Targets - AUv3 Framework + Appex + Standalone App (Visage UI)
# ============================================================================
if(IOS)
  # iOS AUv3 Framework containing plugin code
  add_library(${PROJECT_NAME}AU-ios-framework SHARED ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}AU-ios-framework PUBLIC
    LINK iPlug2::AUv3iOS _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}AU-ios-framework AUv3iOSFramework ${PROJECT_NAME})

  # iOS AUv3 App Extension (appex)
  add_executable(${PROJECT_NAME}AUv3-ios-appex
    ${PLUG_RESOURCES_DIR}/${PROJECT_NAME}AUv3Appex.m
  )
  iplug_configure_target(${PROJECT_NAME}AUv3-ios-appex AUv3iOSAppex ${PROJECT_NAME})

  # iOS Standalone App that hosts the AUv3 for testing
  add_executable(${PROJECT_NAME}-ios-app ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}-ios-app PUBLIC
    LINK iPlug2::AUv3iOS _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}-ios-app IOSApp ${PROJECT_NAME})

  # Embed AUv3 appex and framework in the iOS app
  iplug_embed_auv3ios_in_app(${PROJECT_NAME}-ios-app ${PROJECT_NAME})
endif()

# ============================================================================
# WAM/Web Targets (Emscripten only)
# ============================================================================
if(CMAKE_SYSTEM_NAME STREQUAL "Emscripten")
  # WAM Processor target (DSP/audio worklet)
  add_executable(${PROJECT_NAME}-wam ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}-wam PUBLIC
    LINK iPlug2::WAM _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}-wam WAM ${PROJECT_NAME})

  # Web Controller target (UI/graphics)
  add_executable(${PROJECT_NAME}-web ${SOURCE_FILES})
  iplug_add_target(${PROJECT_NAME}-web PUBLIC
    LINK iPlug2::Web _${PROJECT_NAME}-base
  )
  iplug_configure_target(${PROJECT_NAME}-web Web ${PROJECT_NAME})

  # Combined WAM distribution target (bundles resources, templates, etc.)
  iplug_build_wam_dist(${PROJECT_NAME}
    WAM_TARGET ${PROJECT_NAME}-wam
    WEB_TARGET ${PROJECT_NAME}-web
    SITE_ORIGIN "/"
  )
endif()