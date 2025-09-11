#!/bin/bash
# setup_latex.sh
# Install LaTeX and all dependencies required to compile svjour project
set -e

echo "Fixing locale for LaTeX installation..."
sudo apt update
sudo apt install -y locales
sudo locale-gen en_US.UTF-8
export LANG=en_US.UTF-8
export LANGUAGE=en_US:en
export LC_ALL=en_US.UTF-8

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/svjour"

if [ ! -d "$SRC_DIR" ]; then
    echo "Error: $SRC_DIR does not exist!"
    exit 1
fi

echo "Installing required LaTeX packages for svjour..."
REQUIRED_PACKAGES=(
    texlive-latex-base
    texlive-latex-extra      
    texlive-latex-recommended
    texlive-fonts-recommended
    texlive-fonts-extra
    texlive-bibtex-extra
    texlive-lang-german
    texlive-lang-english
    texlive-xetex
    texlive-luatex
    texlive-science           
    texlive-pictures        
    texlive-humanities        
    texlive-publishers        
)

sudo apt install -y "${REQUIRED_PACKAGES[@]}"

echo -e "\nLaTeX setup complete. You can now compile $SRC_DIR/README.tex with pdflatex or lualatex."
