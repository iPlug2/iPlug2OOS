#!/bin/bash
# tex.sh - Compile README.tex in VOID_Docs project

set -e


ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"   # VOID_Docs
SRC_DIR="$ROOT_DIR/svjour"
BUILD_DIR="$ROOT_DIR/build.LaTeX"
OUTPUT_PDF="$BUILD_DIR/README.pdf"
FINAL_PDF="$ROOT_DIR/README.pdf"

mkdir -p "$BUILD_DIR"

echo "Compiling README.tex..."
export TEXINPUTS="$SRC_DIR:"

pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" "$SRC_DIR/README.tex"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$BUILD_DIR" "$SRC_DIR/README.tex"


if [ -f "$OUTPUT_PDF" ]; then
    mv -f "$OUTPUT_PDF" "$FINAL_PDF"
    echo -e "\nCompiled PDF is at: $FINAL_PDF\n"
else
    echo -e "\nCompilation failed. See logs in $BUILD_DIR/README.log\n"
    exit 1
fi

echo -e "Auxiliary files are in: $BUILD_DIR\n"
