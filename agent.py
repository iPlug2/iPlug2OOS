#!/usr/bin/env python3

import os
import difflib
import tempfile
import sys
import shutil
from datetime import datetime
from openai import OpenAI
import re

HF_TOKEN = os.getenv("AI_API_KEY")
if not HF_TOKEN:
    print("Error: AI_API_KEY is not set in the environment.")
    sys.exit(1)

AGENT_TASKS_DIR = "agent_tasks"
BACKUP_DIR = "agent_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=HF_TOKEN)

while True:
    mode = input("Apply changes manually (y), abort (n), or force all (f)? [y/n/f]: ").strip().lower()
    if mode in ("y", "n", "f"):
        break
    print("Invalid input. Correct commands are: y = manual, n = abort, f = force all")

if mode == "n":
    print("Aborted by user.")
    sys.exit(0)

force_all = mode == "f"
manual_mode = mode == "y"

def custom_unified_diff(old_text, new_text):
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    diff_lines = []
    sm = difflib.SequenceMatcher(a=old_lines, b=new_lines)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        header = (
            "-----------------------------------------------------------------------------------\n"
            f"lines ({i1+1}-{i2}) of Current updated by merge of lines ({j1+1}-{j2}) of Updated\n"
            "-----------------------------------------------------------------------------------\n"
        )
        diff_lines.append(header)
        for line in old_lines[i1:i2]:
            diff_lines.append(f"-{line}")
        for line in new_lines[j1:j2]:
            diff_lines.append(f"+{line}")
    return "\n".join(diff_lines)

for config_file in sorted(os.listdir(AGENT_TASKS_DIR)):
    if not config_file.endswith("_config.txt"):
        continue

    config_path = os.path.join(AGENT_TASKS_DIR, config_file)
    print(f"\n=== Processing {config_file} ===")

    config = {}
    with open(config_path, "r") as f:
        exec(f.read(), config)

    path = config.get("PATH")
    associated_path = config.get("ASSOCIATED")
    query = config.get("QUERY")

    if not path or not os.path.isfile(path):
        print(f"Skipping {config_file}: PATH invalid -> {path}")
        continue

    with open(path, "r") as f:
        main_text = f.read()

    associated_text = ""
    if associated_path and os.path.isfile(associated_path):
        with open(associated_path, "r") as f:
            associated_text = f.read()

    prompt = f"{query}\n\nMAIN FILE:\n{main_text}"
    if associated_text:
        prompt += f"\n\nASSOCIATED FILE:\n{associated_text}"

    try:
        completion = client.chat.completions.create(
            model="moonshotai/Kimi-K2-Instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=6000
        )
    except Exception as e:
        print(f"Error calling Hugging Face API for {config_file}: {e}")
        continue

    raw_text = completion.choices[0].message.content.strip()

    match = re.search(r"```cpp\s*(.*?)\s*```", raw_text, re.DOTALL)
    if match:
        new_text = match.group(1).strip()
    else:
        new_text = raw_text  

    if not new_text:
        print(f"No usable output for {config_file}")
        continue

    diff_output = custom_unified_diff(main_text, new_text)
    if not diff_output.strip():
        print("No changes detected.")
        continue

    print("\nProposed changes:\n")
    print(diff_output)

    with tempfile.NamedTemporaryFile("w", delete=False) as tmp_file:
        tmp_file.write(new_text)
        tmp_path = tmp_file.name

    print(f"\nProposed changes saved to {tmp_path}")

    if force_all:
        overwrite = "y"
    elif manual_mode:
        while True:
            choice = input(f"Overwrite {path}? [y/n]: ").strip().lower()
            if choice in ("y", "n"):
                overwrite = choice
                break
            print("Invalid input. Correct commands are: y = yes, n = no")

    if overwrite == "y":
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{os.path.basename(path)}.{timestamp}.bak"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.copy2(path, backup_path)
        print(f"Original file backed up to {backup_path}")

        shutil.move(tmp_path, path)
        print(f"File {path} updated!")
    else:
        os.remove(tmp_path)
        print("No changes made.")
