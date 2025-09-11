#!/bin/bash

# init.sh
# Reads a config file, sets variables, then calls setup_container.sh and setup.sh

CONFIG_FILE="config.txt"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Config file '$CONFIG_FILE' not found!"
    exit 1
fi


while IFS='=' read -r key value; do

    [[ -z "$key" || "$key" =~ ^# ]] && continue
    key=$(echo "$key" | xargs)
    value=$(echo "$value" | xargs)
    export "$key"="$value"

done < "$CONFIG_FILE"


echo "PROJECT_NAME=$PROJECT_NAME"
echo "MANUFACTURER_NAME=$MANUFACTURER_NAME"


./setup.sh "$PROJECT_NAME" "$MANUFACTURER_NAME" && \

echo -e "\nConfigured $MANUFACTURER_NAME $PROJECT_NAME...get to work\n"

