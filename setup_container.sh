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

echo "Checking for pdflatex..."
if ! command -v pdflatex &> /dev/null; then
    echo "pdflatex not found, installing TeX Live..."
    sudo apt update
    sudo apt install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended
else
    echo "pdflatex already installed."
fi


echo -e "\nSetup complete.\n"

