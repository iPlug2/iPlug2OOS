#!/usr/bin/env python3

import os
import shutil
import re

BACKUP_DIR = "agent_backups"
RESTORE_ROOT = "TemplateProject"

if not os.path.isdir(BACKUP_DIR):
    print(f"Backup directory '{BACKUP_DIR}' does not exist.")
    exit(1)

for backup_file in sorted(os.listdir(BACKUP_DIR)):
    backup_path = os.path.join(BACKUP_DIR, backup_file)

    if not os.path.isfile(backup_path):
        continue

    # Strip timestamp / .bak suffix
    # Example: TemplateProject.cpp.20250911_042530.bak -> TemplateProject.cpp
    original_filename_match = re.match(r"^(.*?)(?:\.\d{8}_\d{6}\.bak)?$", backup_file)
    if not original_filename_match:
        print(f"Skipping {backup_file}: unable to determine original filename")
        continue

    original_filename = original_filename_match.group(1)
    restore_path = os.path.join(RESTORE_ROOT, original_filename)

    # Ensure the parent directories exist
    os.makedirs(os.path.dirname(restore_path), exist_ok=True)

    # Copy the backup over
    shutil.copy2(backup_path, restore_path)
    print(f"Restored {backup_file} -> {restore_path}")

print("All backups restored.")
