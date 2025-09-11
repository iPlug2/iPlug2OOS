#!/bin/bash

# makedist-web.sh builds a Web version of an iPlug2 project using emscripten
# arguments:
# 1st argument : "on", "off" or "ws" (launch emrun/browser or websocket mode)
# 2nd argument : site origin
# 3rd argument : browser ("chrome", "safari", "firefox")

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
IPLUG2_ROOT=$SCRIPT_DIR/../../iPlug2
PROJECT_ROOT=$SCRIPT_DIR/..
FILE_PACKAGER=$EMSDK/upstream/emscripten/tools/file_packager.py
EMRUN="python3 ${IPLUG2_ROOT}/Scripts/emrun/emrun.py"

PROJECT_NAME=TemplateProject
BUILD_DSP=1
BUILD_EDITOR=1
WEBSOCKET_MODE=0
EMRUN_BROWSER=chrome
LAUNCH_EMRUN=1
EMRUN_SERVER=1
EMRUN_SERVER_PORT=6969
EMRUN_CONTAINER=0
SITE_ORIGIN="/"

cd $PROJECT_ROOT

# process arguments
if [ "$1" = "ws" ]; then
  LAUNCH_EMRUN=0
  BUILD_DSP=0
  WEBSOCKET_MODE=1
elif [ "$1" = "off" ]; then
  LAUNCH_EMRUN=0
elif [ "$1" = "container" ]; then
  EMRUN_CONTAINER=1
fi

[ "$#" -ge 2 ] && SITE_ORIGIN=$2
[ "$#" -ge 3 ] && EMRUN_BROWSER=$3

# prepare build-web folder
if [ -d build-web/.git ]; then
  [ "$BUILD_DSP" -eq 1 ] && rm -f build-web/scripts/*-wam.js
  [ "$BUILD_EDITOR" -eq 1 ] && rm -f build-web/scripts/*-web.*
else
  [ -d build-web ] && rm -rf build-web
  mkdir -p build-web/scripts
fi
mkdir -p build-web/scripts

echo "BUNDLING RESOURCES -----------------------------"

# clean old JS files
rm -f build-web/imgs.js build-web/imgs@2x.js build-web/svgs.js build-web/fonts.js

# package fonts
FOUND_FONTS=0
if [ -d ./resources/fonts ] && compgen -G "./resources/fonts/*.ttf" > /dev/null; then
  FOUND_FONTS=1
  python3 $FILE_PACKAGER fonts.data --preload ./resources/fonts/ --exclude *DS_Store --js-output=./fonts.js
fi

# package svgs
FOUND_SVGS=0
if [ -d ./resources/img ] && compgen -G "./resources/img/*.svg" > /dev/null; then
  FOUND_SVGS=1
  python3 $FILE_PACKAGER svgs.data --preload ./resources/img/ --exclude *.png --exclude *DS_Store --js-output=./svgs.js
fi

# package @1x PNGs
FOUND_PNGS=0
if [ -d ./resources/img ] && compgen -G "./resources/img/*.png" > /dev/null; then
  FOUND_PNGS=1
  python3 $FILE_PACKAGER imgs.data --use-preload-plugins --preload ./resources/img/ --use-preload-cache --indexedDB-name="/$PROJECT_NAME_pkg" --exclude *DS_Store --exclude *@2x.png --exclude *.svg >> ./imgs.js
fi

# package @2x PNGs
FOUND_2XPNGS=0
if [ -d ./resources/img ] && compgen -G "./resources/img/*@2x*.png" > /dev/null; then
  FOUND_2XPNGS=1
  mkdir ./build-web/2x/
  cp ./resources/img/*@2x* ./build-web/2x/
  python3 $FILE_PACKAGER imgs@2x.data --use-preload-plugins --preload ./2x@/resources/img/ --use-preload-cache --indexedDB-name="/$PROJECT_NAME_pkg" --exclude *DS_Store >> ./imgs@2x.js
  rm -rf ./build-web/2x
fi

# move generated files
mv -f imgs.js build-web/imgs.js 2>/dev/null
mv -f imgs@2x.js build-web/imgs@2x.js 2>/dev/null
mv -f svgs.js build-web/svgs.js 2>/dev/null
mv -f fonts.js build-web/fonts.js 2>/dev/null
mv -f imgs.data build-web/imgs.data 2>/dev/null
mv -f imgs@2x.data build-web/imgs@2x.data 2>/dev/null
mv -f svgs.data build-web/svgs.data 2>/dev/null
mv -f fonts.data build-web/fonts.data 2>/dev/null

# --- WAM DSP build ---
if [ "$BUILD_DSP" -eq 1 ]; then
  echo "MAKING - WAM WASM MODULE -----------------------------"
  cd $PROJECT_ROOT/projects
  emmake make --makefile $PROJECT_NAME-wam-processor.mk || { echo "IPlugWAM WASM compilation failed"; exit 1; }

  cd $PROJECT_ROOT/build-web/scripts
  # prefix -wam.js with AudioWorkletGlobalScope scope
  echo "AudioWorkletGlobalScope.WAM = AudioWorkletGlobalScope.WAM || {}; AudioWorkletGlobalScope.WAM.$PROJECT_NAME = { ENVIRONMENT: 'WEB' }; const ModuleFactory = AudioWorkletGlobalScope.WAM.$PROJECT_NAME;" > $PROJECT_NAME-wam.tmp.js
  cat $PROJECT_NAME-wam.js >> $PROJECT_NAME-wam.tmp.js
  mv $PROJECT_NAME-wam.tmp.js $PROJECT_NAME-wam.js

  # copy WAM SDK and AW polyfill
  cp $IPLUG2_ROOT/Dependencies/IPlug/WAM_SDK/wamsdk/*.js .
  cp $IPLUG2_ROOT/Dependencies/IPlug/WAM_AWP/*.js .

  # copy template scripts
  cp $IPLUG2_ROOT/IPlug/WEB/Template/scripts/IPlugWAM-awn.js $PROJECT_NAME-awn.js
  cp $IPLUG2_ROOT/IPlug/WEB/Template/scripts/IPlugWAM-awp.js $PROJECT_NAME-awp.js

  sed -i.bak "s/NAME_PLACEHOLDER/$PROJECT_NAME/g" $PROJECT_NAME-awn.js
  sed -i.bak "s/NAME_PLACEHOLDER/$PROJECT_NAME/g" $PROJECT_NAME-awp.js
  sed -i.bak "s,ORIGIN_PLACEHOLDER,$SITE_ORIGIN,g" $PROJECT_NAME-awn.js
  rm *.bak
else
  echo "WAM not being built, BUILD_DSP=0"
fi

cd $PROJECT_ROOT/build-web

# copy template HTML and update placeholders
cp $IPLUG2_ROOT/IPlug/WEB/Template/index.html index.html
sed -i.bak "s/NAME_PLACEHOLDER/$PROJECT_NAME/g" index.html
[ $FOUND_FONTS -eq 0 ] && sed -i.bak 's#<script async src="fonts.js"></script>#<!--<script async src="fonts.js"></script>-->#g' index.html
[ $FOUND_SVGS -eq 0 ] && sed -i.bak 's#<script async src="svgs.js"></script>#<!--<script async src="svgs.js"></script>-->#g' index.html
[ $FOUND_PNGS -eq 0 ] && sed -i.bak 's#<script async src="imgs.js"></script>#<!--<script async src="imgs.js"></script>-->#g' index.html
[ $FOUND_2XPNGS -eq 0 ] && sed -i.bak 's#<script async src="imgs@2x.js"></script>#<!--<script async src="imgs@2x.js"></script>-->#g' index.html

if [ $WEBSOCKET_MODE -eq 1 ]; then
  cp $IPLUG2_ROOT/Dependencies/IPlug/WAM_SDK/wamsdk/wam-controller.js scripts/wam-controller.js
  cp $IPLUG2_ROOT/IPlug/WEB/Template/scripts/websocket.js scripts/websocket.js
  sed -i.bak 's#<script src="scripts/audioworklet.js"></script>#<!--<script src="scripts/audioworklet.js"></script>-->#g' index.html
  sed -i.bak 's/let WEBSOCKET_MODE=false;/let WEBSOCKET_MODE=true;/g' index.html
else
  sed -i.bak 's#<script src="scripts/websocket.js"></script>#<!--<script src="scripts/websocket.js"></script>-->#g'
  MAXNINPUTS=$(python3 $IPLUG2_ROOT/Scripts/parse_iostr.py "$PROJECT_ROOT" inputs)
  MAXNOUTPUTS=$(python3 $IPLUG2_ROOT/Scripts/parse_iostr.py "$PROJECT_ROOT" outputs)
  [ "$MAXNINPUTS" -eq 0 ] && { MAXNINPUTS=""; sed -i.bak '181,203d' index.html; }
  sed -i.bak "s/MAXNINPUTS_PLACEHOLDER/$MAXNINPUTS/g" index.html
  sed -i.bak "s/MAXNOUTPUTS_PLACEHOLDER/$MAXNOUTPUTS/g" index.html
fi
rm *.bak

# copy styles and favicon
mkdir -p styles
cp $IPLUG2_ROOT/IPlug/WEB/Template/styles/style.css styles/style.css
cp $IPLUG2_ROOT/IPlug/WEB/Template/favicon.ico favicon.ico

# WEB WASM MODULE
cd $PROJECT_ROOT/projects
emmake make --makefile $PROJECT_NAME-wam-controller.mk EXTRA_CFLAGS=-DWEBSOCKET_CLIENT=$WEBSOCKET_MODE || { echo "IPlugWEB WASM compilation failed"; exit 1; }

cd $PROJECT_ROOT/build-web
echo "payload:"
find . -maxdepth 2 -mindepth 1 -name .git -type d \! -prune -o \! -name .DS_Store -type f -exec du -hs {} \;

# launch emrun on port 6969
if [ "$LAUNCH_EMRUN" -eq 1 ]; then
  mkcert 127.0.0.1 localhost
  if [ "$EMRUN_CONTAINER" -eq 1 ]; then
    $EMRUN --no_browser --serve_after_close --serve_after_exit --port=$EMRUN_SERVER_PORT --hostname=0.0.0.0 .
  elif [ "$EMRUN_SERVER" -eq 0 ]; then
    $EMRUN --browser $EMRUN_BROWSER --no_server --port=$EMRUN_SERVER_PORT index.html
  else
    $EMRUN --browser $EMRUN_BROWSER --no_emrun_detect index.html
  fi
else
  echo "Not running emrun"
fi
