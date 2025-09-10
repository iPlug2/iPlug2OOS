#!/bin/bash

# setup.sh PROJECT_NAME MANUFACTURER_NAME
# Fully initializes iPlug2OOS, duplicates template, and commits.

set -e  

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 PROJECT_NAME MANUFACTURER_NAME"
    exit 1
fi

PROJECT_NAME=$1
MANUFACTURER_NAME=$2
TEMPLATE_NAME="Rend"

echo "Duplicating template project..."
python3 duplicate.py "$TEMPLATE_NAME" "$PROJECT_NAME" "$MANUFACTURER_NAME"

echo "Cleaning up template folder..."
rm -rf "$TEMPLATE_NAME"
rm -rf "TestOOS"

git add "$PROJECT_NAME"
git commit -m "Created project $PROJECT_NAME for $MANUFACTURER_NAME"

echo "Setup complete!"
