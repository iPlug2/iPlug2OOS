#!/bin/bash

# This script initializes the cloned iPlug2OOS repo, downloading dependencies and renaming the template

if [ "$#" -eq 2 ]; then
    echo "Initializing submodule..."
    git submodule init
    git submodule update
    
    echo "Downloading iPlug2 SDKs..."
    cd iPlug2/Dependencies/IPlug/
    ./download-iplug-sdks.sh
    cd ../../..

    echo "Duplicating template project..."
    python3 duplicate.py TemplateProject $1 $2
    rm -r TemplateProject
    git add $1
    git commit -a -m "Renamed template project"
    
    echo "Downloading mkcert..."
    wget https://github.com/FiloSottile/mkcert/releases/download/v1.4.2/mkcert-v1.4.2-linux-amd64 -o mkcert
    ./mkcert install
    ./mkcert localhost    
else
    echo "usage: setup.sh PROJECT_NAME MANUFACTURER_NAME"
fi
