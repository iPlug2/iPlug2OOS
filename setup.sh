#!/bin/bash

if [ "$#" -eq 2 ]; then
    git submodule init
    git submodule update
    cd iPlug2/Dependencies/IPlug/
    ./download-iplug-sdks.sh
    cd ../../..
    python3 duplicate.py TemplateProject $1 $2
    rm -r TemplateProject
    git add $1
    git commit -a -m "Renamed template project"
else
    echo "usage: setup.sh PROJECT_NAME MANUFACTURER_NAME"
fi
