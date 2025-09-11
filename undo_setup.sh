#!/bin/bash

# undo_setup.sh
# Reverts setup.sh actions, restoring the project to Rend,
# preserving setup scripts and config.txt

set -e

CONFIG_FILE="config.txt"
TEMPLATE_NAME="TemplateProject"

# Check config file
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found!"
    exit 1
fi

# Extract project name from config
PROJECT_NAME=$(grep -E "^PROJECT_NAME" "$CONFIG_FILE" | awk -F '=' '{gsub(/^[ \t]+|[ \t]+$/, "", $2); print $2}')
if [ -z "$PROJECT_NAME" ]; then
    echo "Error: PROJECT_NAME not found in $CONFIG_FILE"
    exit 1
fi

echo "Using PROJECT_NAME='$PROJECT_NAME' from $CONFIG_FILE"

# Remove existing project folder
if [ -d "$PROJECT_NAME" ]; then
    echo "Removing project folder '$PROJECT_NAME'..."
    sudo rm -rf "$PROJECT_NAME"
else
    echo "Project folder '$PROJECT_NAME' does not exist. Skipping removal."
fi

# Restore template folder
if [ -d "$TEMPLATE_NAME" ]; then
    echo "Template folder '$TEMPLATE_NAME' exists. Resetting to git version..."
    git restore "$TEMPLATE_NAME" || echo "Warning: Could not restore $TEMPLATE_NAME from git."
else
    echo "Template folder '$TEMPLATE_NAME' missing. Restoring from git..."
    git restore "$TEMPLATE_NAME" || echo "Warning: Could not restore $TEMPLATE_NAME from git."
fi

# Reset submodules if any
if [ -f .gitmodules ]; then
    echo "Resetting submodules..."
    git submodule update --init --recursive
fi

# Undo last setup commit if it matches naming pattern
LAST_COMMIT_MSG=$(git log -1 --pretty=%B 2>/dev/null || echo "")
if [[ "$LAST_COMMIT_MSG" == "Created project $PROJECT_NAME for"* ]]; then
    echo "Undoing last commit..."
    git reset --soft HEAD~1
else
    echo "No matching setup commit found. Skipping git reset."
fi

# Unstage changes except critical scripts
EXCLUDE_FILES=("setup.sh" "undo_setup.sh" "setup_container.sh" "$CONFIG_FILE")
echo "Unstaging remaining changes (excluding critical scripts)..."
for file in "${EXCLUDE_FILES[@]}"; do
    git reset HEAD -- "$file" 2>/dev/null || true
done

git reset

echo -e "\nUndo complete! Project restored to Rend.\n"
