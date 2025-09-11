#!/usr/bin/env python3

import os
import difflib
import tempfile
import sys
import shutil
from openai import OpenAI

HF_TOKEN = os.getenv("AI_API_KEY")
if not HF_TOKEN:
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

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

try:
    completion = client.chat.completions.create(
        model="moonshotai/Kimi-K2-Instruct",  
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=6000
    )
except Exception as e:
    print("Error calling Hugging Face API:", e)
    sys.exit(1)

new_text = completion.choices[0].message.content.strip()

if not new_text:
    print("Error: No usable output from AI.")
    print("Full response:", completion)
    sys.exit(1)


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

    return diff_lines


diff_output = "\n".join(custom_unified_diff(main_text, new_text))
if not diff_output.strip():
    print("No changes detected. File will not be updated.")
    sys.exit(0)

print("\nProposed changes:\n")
print(diff_output)

with tempfile.NamedTemporaryFile("w", delete=False) as tmp_file:
    tmp_file.write(new_text)
    tmp_path = tmp_file.name

print(f"\nProposed changes saved to {tmp_path}")


choice = input("Overwrite the original file with these changes? (y/n): ").strip().lower()
if choice == "y":
    shutil.move(tmp_path, path)
    print(f"File {path} updated!")
else:
    os.remove(tmp_path)
    print("No changes made.")
