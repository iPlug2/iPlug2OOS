#!/usr/bin/env python3

import argparse
import os
import re
import shutil


PRODUCT_NAME = "TemplateProject"

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
INSTALLER_DIR = os.path.join(PROJECT_DIR, "installer")


def read_text(path):
  with open(path, "r", encoding="utf-8") as input_file:
    return input_file.read()


def write_text(path, text):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "w", encoding="utf-8", newline="\n") as output_file:
    output_file.write(text)


def markdown_to_plain_text(markdown):
  lines = []
  in_code_block = False

  for line in markdown.splitlines():
    stripped = line.strip()

    if stripped.startswith("```"):
      in_code_block = not in_code_block
      continue

    if not in_code_block:
      line = re.sub(r"^\s{0,3}#{1,6}\s*", "", line)
      line = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", line)
      line = re.sub(r"\*\*([^*]+)\*\*", r"\1", line)
      line = re.sub(r"__([^_]+)__", r"\1", line)
      line = re.sub(r"\*([^*]+)\*", r"\1", line)
      line = re.sub(r"_([^_]+)_", r"\1", line)
      line = re.sub(r"`([^`]+)`", r"\1", line)
      line = re.sub(r"^\s*[-*+]\s+", "- ", line)

    lines.append(line.rstrip())

  return "\n".join(lines).strip() + "\n"


def rtf_escape(text):
  escaped = []

  for char in text:
    codepoint = ord(char)

    if char == "\\":
      escaped.append(r"\\")
    elif char == "{":
      escaped.append(r"\{")
    elif char == "}":
      escaped.append(r"\}")
    elif char == "\t":
      escaped.append(r"\tab ")
    elif codepoint <= 0x7f:
      escaped.append(char)
    else:
      signed_codepoint = codepoint if codepoint < 32768 else codepoint - 65536
      escaped.append(r"\u" + str(signed_codepoint) + "?")

  return "".join(escaped)


def plain_text_to_rtf(text):
  lines = [
    r"{\rtf1\ansi\deff0",
    r"{\fonttbl{\f0 Helvetica;}}",
    r"\fs24",
  ]

  for line in text.splitlines():
    if line:
      lines.append(rtf_escape(line) + r"\par")
    else:
      lines.append(r"\par")

  lines.append("}")

  return "\n".join(lines) + "\n"


def markdown_file_to_plain_text(name):
  return markdown_to_plain_text(read_text(os.path.join(INSTALLER_DIR, name + ".md")))


def build_mac_docs():
  target_dir = os.path.join(PROJECT_DIR, "build-mac", "installer", "resources")

  for name in ("license", "readme-mac", "intro"):
    source_text = markdown_file_to_plain_text(name)
    write_text(os.path.join(target_dir, name + ".rtf"), plain_text_to_rtf(source_text))

  background = os.path.join(INSTALLER_DIR, PRODUCT_NAME + "-installer-bg.png")
  if os.path.exists(background):
    os.makedirs(target_dir, exist_ok=True)
    shutil.copy2(background, os.path.join(target_dir, os.path.basename(background)))

  print("Prepared macOS installer documents in " + target_dir)


def build_win_docs():
  target_dir = os.path.join(PROJECT_DIR, "build-win", "installer-docs")

  for name in ("license", "readme-win", "readme-win-demo"):
    write_text(os.path.join(target_dir, name + ".txt"), markdown_file_to_plain_text(name))

  print("Prepared Windows installer documents in " + target_dir)


def main():
  parser = argparse.ArgumentParser(description="Prepare installer-compatible documents from Markdown sources.")
  parser.add_argument("platform", choices=("mac", "win", "all"), help="Target installer platform.")
  args = parser.parse_args()

  if args.platform in ("mac", "all"):
    build_mac_docs()

  if args.platform in ("win", "all"):
    build_win_docs()


if __name__ == "__main__":
  main()
