#!/bin/bash

# setup.sh PROJECT_NAME MANUFACTURER_NAME

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 PROJECT_NAME MANUFACTURER_NAME"
    exit 1
fi

PROJECT_NAME=$1
MANUFACTURER_NAME=$2

echo "Initializing submodules..."
git submodule update --init

echo "Downloading iPlug2 SDKs..."
cd iPlug2/Dependencies/IPlug/ || exit 1
chmod +x download-iplug-sdks.sh
./download-iplug-sdks.sh
cd ../../..

echo "Duplicating template project..."
python3 duplicate.py Rend "$PROJECT_NAME" "$MANUFACTURER_NAME"

echo "Cleaning up old templates..."
rm -rf TestOOS
rm -rf Rend

git add "$PROJECT_NAME"
git commit -m "Created project $PROJECT_NAME for $MANUFACTURER_NAME"

echo "Setup complete!"
