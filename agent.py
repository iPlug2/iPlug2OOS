#!/usr/bin/env python3

import os
import difflib
import requests
import tempfile
import sys

API_KEY = os.getenv("AI_API_KEY")

if not API_KEY:
    print("Error: AI_API_KEY is not set in the environment.")
    sys.exit(1)

CONFIG_FILE = "agent_task_config.txt"
config = {}

with open(CONFIG_FILE, "r") as f:
    exec(f.read(), config)

path = config.get("PATH")
associated_path = config.get("ASSOCIATED")
query = config.get("QUERY")

with open(path, "r") as f:
    main_text = f.read()

associated_text = ""
if associated_path and os.path.isfile(associated_path):
    with open(associated_path, "r") as f:
        associated_text = f.read()

prompt = f"{query}\n\nMAIN FILE:\n{main_text}"
if associated_text:
    prompt += f"\n\nASSOCIATED FILE:\n{associated_text}"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

data = {
    "model": "google/gemma-3-4b",
    "input": prompt,
    "temperature": 0.3,
    "max_tokens": 6000
}

response = requests.post("https://api.aimlapi.com/v1/completions", json=data, headers=headers)

# Handle bad HTTP response
if response.status_code != 200:
    print(f"Error: API returned {response.status_code}")
    print(response.text)
    sys.exit(1)

resp_json = response.json()
new_text = resp_json.get("output_text", "").strip()

# Prevent accidental overwrite with empty or bad output
if not new_text:
    print("Error: No usable output from AI.")
    print("Full response:", resp_json)
    sys.exit(1)

# Show concise diff like git
diff = difflib.unified_diff(
    main_text.splitlines(),
    new_text.splitlines(),
    fromfile="Current",
    tofile="Updated",
    lineterm="",
    n=3  # keep 3 lines of context like git
)

diff_output = "\n".join(diff)
if not diff_output.strip():
    print("No changes detected. File will not be updated.")
    sys.exit(0)

print("\nProposed changes:\n")
print(diff_output)

# Write candidate changes to a temp file
with tempfile.NamedTemporaryFile("w", delete=False) as tmp_file:
    tmp_file.write(new_text)
    tmp_path = tmp_file.name

print(f"\nProposed changes saved to {tmp_path}")

choice = input("Overwrite the original file with these changes? (y/n): ").strip().lower()
if choice == "y":
    os.replace(tmp_path, path)  # safe overwrite
    print(f"File {path} updated!")
else:
    os.remove(tmp_path)
    print("No changes made.")
