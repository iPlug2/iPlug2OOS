#!/bin/bash

# This script initializes the cloned iPlug2OOS repo, downloading dependencies, and tools

echo "Initializing submodule..."
git submodule update --init

echo "Downloading iPlug2 SDKs..."
cd iPlug2/Dependencies/IPlug/
./download-iplug-sdks.sh
cd ../../..

# Not nessecary until we have WASM libs
# echo "Downloading iPlug2 prebuilt libs..."
# cd iPlug2/Dependencies/
# ./download-prebuilt-libs.sh
# cd ../..

echo "Downloading mkcert..."
wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.3/mkcert-v1.4.3-linux-amd64 -O mkcert
chmod +x mkcert
mv mkcert /usr/local/bin
mkcert -install