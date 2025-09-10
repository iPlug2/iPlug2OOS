#!/bin/bash

# undo_setup.sh
# Fully reverts setup.sh actions and restores Rend using config.txt,
# but preserves setup scripts and config.txt

set -e

CONFIG_FILE="config.txt"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found!"
    exit 1
fi

PROJECT_NAME=$(grep -E "^PROJECT_NAME" "$CONFIG_FILE" | awk -F '=' '{gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2}')
if [ -z "$PROJECT_NAME" ]; then
    echo "Error: PROJECT_NAME not found in $CONFIG_FILE"
    exit 1
fi

TEMPLATE_NAME="Rend"

echo "Using PROJECT_NAME='$PROJECT_NAME' from $CONFIG_FILE"

if [ -d "$PROJECT_NAME" ]; then
    echo "Removing project folder '$PROJECT_NAME'..."
    sudo rm -rf "$PROJECT_NAME"
else
    echo "Project folder '$PROJECT_NAME' does not exist. Skipping."

fi

if [ ! -d "$TEMPLATE_NAME" ]; then
    echo "Restoring template folder '$TEMPLATE_NAME' from git..."
    git checkout HEAD -- "$TEMPLATE_NAME" || echo "Warning: $TEMPLATE_NAME could not be restored from git."
else
    echo "Template folder '$TEMPLATE_NAME' already exists. Skipping restore."
fi

if [ -f .gitmodules ]; then
    echo "Resetting submodules..."
    git submodule update --init --recursive
fi

LAST_COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || echo "")
if [[ "$LAST_COMMIT_MSG" == "Created project $PROJECT_NAME for"* ]]; then
    echo "Undoing last commit..."
    git reset --soft HEAD~1
else
    echo "No matching setup commit found. Skipping git reset."
fi

EXCLUDE_FILES=("setup.sh" "undo_setup.sh" "setup_container.sh" "$CONFIG_FILE")
echo "Unstaging remaining changes (excluding critical scripts)..."

for file in "${EXCLUDE_FILES[@]}"; do
    git reset HEAD -- "$file" 2>/dev/null || true
done

git reset

echo -e "\nUndo complete! Repository is restored to initial state.\n"
