#!/bin/bash
# Quick LaTeX compile script with dependency check
# Usage: ./tex.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/svjour"

# List of required LaTeX packages 
REQUIRED_PKGS=(
    "texlive-latex-base"
    "texlive-latex-extra"
    "texlive-fonts-recommended"
    "texlive-lang-english"
    "texlive-lang-german"
    "texlive-bibtex-extra"
    "texlive-pictures"
    "texlive-science"
)

if ! command -v pdflatex &> /dev/null; then
    echo "pdflatex not found. Installing TeX Live..."
    sudo apt update
    sudo apt install -y "${REQUIRED_PKGS[@]}"
else
    echo "pdflatex found. Checking for missing packages..."
    # This is minimal: assumes packages installed via apt cover everything
    # Could add more advanced checks if needed
fi

echo "Compiling README.tex..."
pdflatex -interaction=nonstopmode -output-directory="$SRC_DIR" "$SRC_DIR/README.tex"

if [ ! -f "$SRC_DIR/README.pdf" ]; then
    echo "Compilation failed. See logs in $SRC_DIR/README.log"
    exit 1
fi

mv "$SRC_DIR/README.pdf" "$SCRIPT_DIR/README.pdf"

echo "Compiled PDF is at: $SCRIPT_DIR/README.pdf"
echo "Auxiliary files are in: $SRC_DIR"
