cmake_minimum_required(VERSION 3.25)
project(TemplateProjectReaperExtensionWebView VERSION 1.0.0)

# REAPER Extensions are macOS and Windows only (no iOS, no Emscripten)
if(IOS OR CMAKE_SYSTEM_NAME STREQUAL "Emscripten")
  message(STATUS "TemplateProjectReaperExtensionWebView is not supported on ${CMAKE_SYSTEM_NAME}. Skipping.")
  return()
endif()

# The WebView editor delegate uses std::filesystem, which requires macOS 10.15+
# (iPlug2.cmake otherwise defaults to 10.13). Set before including iPlug2.cmake.
if(APPLE AND NOT CMAKE_OSX_DEPLOYMENT_TARGET)
  set(CMAKE_OSX_DEPLOYMENT_TARGET "10.15" CACHE STRING "Minimum macOS version")
endif()

if(NOT DEFINED IPLUG2_DIR)
  set(IPLUG2_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../iPlug2" CACHE PATH "iPlug2 root directory")
endif()

# Include iPlug2 CMake configuration
include(${IPLUG2_DIR}/iPlug2.cmake)
find_package(iPlug2 REQUIRED)

# REAPER extensions are not plugins, so they do not go through iplug_add_plugin()
include(${IPLUG2_CMAKE_DIR}/ReaperExt.cmake)

# WebViewEditorDelegate instead of IGraphics
include(${IPLUG2_CMAKE_DIR}/WebView.cmake)

# Standard plugin setup
set(PROJECT_DIR ${CMAKE_CURRENT_SOURCE_DIR})
set(PLUG_RESOURCES_DIR ${PROJECT_DIR}/resources)

set(SOURCE_FILES
  TemplateProjectReaperExtensionWebView.cpp
  TemplateProjectReaperExtensionWebView.h
  resources/resource.h
  resources/web/index.html
  resources/web/script.js
)

# Add Windows resources
if(WIN32)
  list(APPEND SOURCE_FILES ${PLUG_RESOURCES_DIR}/main.rc)
endif()

# Build as a shared library (MODULE for dynamic loading)
add_library(${PROJECT_NAME} MODULE ${SOURCE_FILES})

# Base configuration - use the WebView UI instead of IGraphics
iplug_add_target(${PROJECT_NAME} PUBLIC
  INCLUDE ${PROJECT_DIR} ${PROJECT_DIR}/resources
  LINK iPlug2::WebView
)

# Names the binary reaper_<project>, restricts exported symbols, and deploys to
# REAPER's UserPlugins directory when IPLUG_DEPLOY_PLUGINS is set.
# WEB_RESOURCES_DIR puts the UI in UserPlugins/${PROJECT_NAME}/, which is where
# release builds load index.html from - see the LoadFile call in the .cpp.
iplug_configure_reaperext(${PROJECT_NAME} ${PROJECT_NAME}
  WEB_RESOURCES_DIR ${PLUG_RESOURCES_DIR}/web
)
