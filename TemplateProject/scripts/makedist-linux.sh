#!/usr/bin/env bash

# Builds the Linux standalone app, VST3 and CLAP with CMake and packages them
# in a .tar.gz archive in build-linux/out
#
# usage: makedist-linux.sh [full/demo]
#
# requires: cmake (3.25+), ninja, python3 and the iPlug2 Linux development
# libraries (see modules/iPlug2/Documentation/cmake.md)

set -euo pipefail

BASEDIR=$(cd "$(dirname "$0")" && pwd)

cd "$BASEDIR/.."

#---------------------------------------------------------------------------------------------------------
#variables

IPLUG2_ROOT=../modules/iPlug2
SCRIPTS=$IPLUG2_ROOT/Scripts
BUILD_DIR=build-linux
PLUGIN_NAME=TemplateProject
ARCH=$(uname -m)

DEMO=0
DEMO_ARG=full
if [ "${1:-full}" == "demo" ]; then
  DEMO=1
  DEMO_ARG=demo
fi

ARCHIVE_NAME=$(python3 "$SCRIPTS/get_archive_name.py" . "linux-$ARCH" $DEMO_ARG)

echo "making $ARCHIVE_NAME ..."

#---------------------------------------------------------------------------------------------------------
#build

if [ -d $BUILD_DIR ]; then
  rm -rf $BUILD_DIR
fi

cmake -S . -B $BUILD_DIR -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_FLAGS="-DDEMO_VERSION=$DEMO" \
  -DIPLUG_DEPLOY_PLUGINS=OFF

cmake --build $BUILD_DIR

#---------------------------------------------------------------------------------------------------------
#package

OUT=$BUILD_DIR/out
STAGE=$BUILD_DIR/$ARCHIVE_NAME

mkdir -p "$STAGE"

# The .resources folders hold the fonts/images each binary loads at runtime,
# and must stay next to the binary they belong to
for item in \
  "$PLUGIN_NAME" \
  "$PLUGIN_NAME.resources" \
  "$PLUGIN_NAME.vst3" \
  "$PLUGIN_NAME.clap" \
  "$PLUGIN_NAME.clap.resources"
do
  if [ -e "$OUT/$item" ]; then
    cp -R "$OUT/$item" "$STAGE/"
  fi
done

for binary in "$PLUGIN_NAME" "$PLUGIN_NAME.vst3" "$PLUGIN_NAME.clap"; do
  if [ ! -e "$STAGE/$binary" ]; then
    echo "error: $OUT/$binary was not built"
    exit 1
  fi
done

cp installer/readme-linux.md "$STAGE/README.md"
cp installer/license.md "$STAGE/LICENSE.md"
cp installer/changelog.txt "$STAGE/changelog.txt"

tar -czf "$OUT/$ARCHIVE_NAME.tar.gz" -C $BUILD_DIR "$ARCHIVE_NAME"

rm -rf "$STAGE"

echo "created $OUT/$ARCHIVE_NAME.tar.gz"
