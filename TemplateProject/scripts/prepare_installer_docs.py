#!/usr/bin/env python3

import argparse
import os
import shutil
import subprocess


SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
INSTALLER_DIR = os.path.join(PROJECT_DIR, "installer")
MANUAL_DIR = os.path.join(PROJECT_DIR, "manual")
PRODUCT_NAME = os.path.basename(PROJECT_DIR)


def read_text(path):
  with open(path, "r", encoding="utf-8") as input_file:
    return input_file.read()


def write_text(path, text, newline="\n"):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, "w", encoding="utf-8", newline=newline) as output_file:
    output_file.write(text)


def require_tool(name):
  if shutil.which(name) is None:
    raise RuntimeError(name + " is required to prepare installer documents")


def run_pandoc(args):
  require_tool("pandoc")
  subprocess.run(["pandoc"] + args, check=True)


def pandoc_convert(source_path, target_path, output_format, extra_args=None):
  os.makedirs(os.path.dirname(target_path), exist_ok=True)
  run_pandoc([
    "--from", "markdown",
    "--to", output_format,
    "--output", target_path,
    source_path,
  ] + (extra_args or []))


def pandoc_plain_text(source_path, target_path, newline="\n"):
  temp_path = target_path + ".tmp"
  pandoc_convert(source_path, temp_path, "plain", ["--wrap=none"])
  try:
    text = read_text(temp_path).strip() + "\n"
    write_text(target_path, text, newline=newline)
  finally:
    if os.path.exists(temp_path):
      os.remove(temp_path)


def build_manual_pdf(build_dir_name):
  require_tool("typst")
  source_path = os.path.join(MANUAL_DIR, PRODUCT_NAME + " manual.md")
  target_path = os.path.join(PROJECT_DIR, build_dir_name, "manual", PRODUCT_NAME + " manual.pdf")
  os.makedirs(os.path.dirname(target_path), exist_ok=True)
  run_pandoc([
    "--from", "markdown",
    "--output", target_path,
    "--pdf-engine=typst",
    source_path,
  ])
  print("Prepared manual PDF at " + target_path)


def build_mac_docs():
  target_dir = os.path.join(PROJECT_DIR, "build-mac", "installer", "resources")
  build_manual_pdf("build-mac")

  for name in ("license", "readme-mac", "intro"):
    pandoc_convert(
      os.path.join(INSTALLER_DIR, name + ".md"),
      os.path.join(target_dir, name + ".rtf"),
      "rtf",
      ["--standalone"],
    )

  background = os.path.join(INSTALLER_DIR, PRODUCT_NAME + "-installer-bg.png")
  if os.path.exists(background):
    shutil.copy2(background, os.path.join(target_dir, os.path.basename(background)))

  print("Prepared macOS installer documents in " + target_dir)


def build_win_docs():
  target_dir = os.path.join(PROJECT_DIR, "build-win", "installer-docs")
  build_manual_pdf("build-win")

  for name in ("license", "readme-win", "readme-win-demo"):
    pandoc_plain_text(
      os.path.join(INSTALLER_DIR, name + ".md"),
      os.path.join(target_dir, name + ".txt"),
      newline="\r\n",
    )

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
