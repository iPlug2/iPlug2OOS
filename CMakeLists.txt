cmake_minimum_required(VERSION 3.25)
project(iPlug2OOS)

set(IPLUG2_DIR ${CMAKE_SOURCE_DIR}/iPlug2)
include(${IPLUG2_DIR}/iPlug2.cmake)

find_package(iPlug2 REQUIRED)

add_subdirectory(TemplateProject)
