#!/usr/bin/bash

git submodule init
git submodule update
cd iPlug2/Dependencies/IPlug/
./download-iplug-sdks.sh
cd ../../..