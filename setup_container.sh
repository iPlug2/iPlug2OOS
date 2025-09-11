#!/bin/bash

echo "Initializing submodule..."
git submodule update --init

echo "Downloading iPlug2 SDKs..."
cd iPlug2/Dependencies/IPlug/
chmod +x download-iplug-sdks.sh
./download-iplug-sdks.sh
cd ../../..

echo "Downloading mkcert..."
wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.3/mkcert-v1.4.3-linux-amd64 -O mkcert
chmod +x mkcert
sudo mv -f mkcert /usr/local/bin
mkcert -install

echo -e "\nSetup complete.\n"
