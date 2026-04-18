cmake_minimum_required(VERSION 3.25)
project(iPlug2OOS)

# iPlug2 framework location. Default to the in-tree submodule, but allow an
# external canonical checkout via `-DIPLUG2_DIR=/path` or the IPLUG2_DIR
# environment variable. iPlug2 Agent sets this to a shared per-machine
# checkout so individual plugin projects don't each carry ~2 GB of deps.
set(IPLUG2_DIR "${CMAKE_SOURCE_DIR}/iPlug2" CACHE PATH "Path to the iPlug2 framework root")
include(${IPLUG2_DIR}/iPlug2.cmake)

find_package(iPlug2 REQUIRED)

add_subdirectory(TemplateProject)
