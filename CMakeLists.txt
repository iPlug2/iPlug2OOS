cmake_minimum_required(VERSION 3.14)
project(iPlug2OOS)


# Disable deprecated warnings
if(MSVC)
  add_compile_options(/wd4996)
else()
  add_compile_options(-Wno-deprecated-declarations)
endif()

set(IPLUG2_DIR ${CMAKE_SOURCE_DIR}/iPlug2)
include(${IPLUG2_DIR}/iPlug2.cmake)

find_package(iPlug2 REQUIRED)

add_subdirectory(TemplateProject)
