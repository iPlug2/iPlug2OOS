#!/bin/bash

# Quick LaTeX compile script
# Usage: ./tex.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_DIR="$SCRIPT_DIR/svjour"

pdflatex -interaction=nonstopmode -output-directory="$SRC_DIR" "$SRC_DIR/README.tex"

mv "$SRC_DIR/README.pdf" "$SCRIPT_DIR/README.pdf"

echo "Compiled PDF is at: $SCRIPT_DIR/README.pdf"
echo "Auxiliary files are in: $SRC_DIR"
