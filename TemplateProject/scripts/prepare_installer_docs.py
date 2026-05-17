#!/usr/bin/env python3

import argparse
import os
import re
import shutil
import textwrap


PRODUCT_NAME = "TemplateProject"

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
INSTALLER_DIR = os.path.join(PROJECT_DIR, "installer")
MANUAL_DIR = os.path.join(PROJECT_DIR, "manual")


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


def markdown_inline_to_text(markdown):
  text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", markdown)
  text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
  text = re.sub(r"__([^_]+)__", r"\1", text)
  text = re.sub(r"\*([^*]+)\*", r"\1", text)
  text = re.sub(r"_([^_]+)_", r"\1", text)
  text = re.sub(r"`([^`]+)`", r"\1", text)
  return text.strip()


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


def pdf_text(text):
  text = text.encode("cp1252", "replace").decode("cp1252")
  return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(path, page_streams):
  os.makedirs(os.path.dirname(path), exist_ok=True)

  objects = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    None,
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
  ]

  page_refs = []
  for stream in page_streams:
    stream_bytes = stream.encode("cp1252", "replace")
    page_object_id = len(objects) + 1
    stream_object_id = len(objects) + 2
    page_refs.append(f"{page_object_id} 0 R")
    objects.append(
      (
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
        "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> "
        f"/Contents {stream_object_id} 0 R >>"
      ).encode("ascii")
    )
    objects.append(
      b"<< /Length " + str(len(stream_bytes)).encode("ascii") + b" >>\nstream\n" +
      stream_bytes + b"\nendstream"
    )

  objects[1] = (
    f"<< /Type /Pages /Kids [{' '.join(page_refs)}] /Count {len(page_refs)} >>"
  ).encode("ascii")

  output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
  offsets = [0]

  for index, content in enumerate(objects, start=1):
    offsets.append(len(output))
    output.extend(f"{index} 0 obj\n".encode("ascii"))
    output.extend(content)
    output.extend(b"\nendobj\n")

  xref_offset = len(output)
  output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
  output.extend(b"0000000000 65535 f \n")
  for offset in offsets[1:]:
    output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
  output.extend(
    (
      "trailer\n"
      f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
      "startxref\n"
      f"{xref_offset}\n"
      "%%EOF\n"
    ).encode("ascii")
  )

  with open(path, "wb") as output_file:
    output_file.write(output)


def write_markdown_pdf(markdown_path, pdf_path):
  markdown = read_text(markdown_path)
  page_width = 595
  page_height = 842
  margin = 54
  page_streams = []
  stream_lines = []
  y = page_height - margin

  def new_page():
    nonlocal stream_lines, y
    if stream_lines:
      page_streams.append("\n".join(stream_lines))
    stream_lines = []
    y = page_height - margin

  def add_vertical_space(points):
    nonlocal y
    if y - points < margin:
      new_page()
    else:
      y -= points

  def add_text(text, font="F1", size=11, leading=15, indent=0):
    nonlocal y
    max_chars = max(10, int((page_width - (2 * margin) - indent) / (size * 0.52)))
    wrapped_lines = textwrap.wrap(text, width=max_chars) or [""]

    for line in wrapped_lines:
      if y - leading < margin:
        new_page()
      x = margin + indent
      stream_lines.append(f"BT /{font} {size} Tf {x} {y:.2f} Td ({pdf_text(line)}) Tj ET")
      y -= leading

  paragraph_lines = []
  in_code_block = False

  def flush_paragraph():
    nonlocal paragraph_lines
    if paragraph_lines:
      add_text(markdown_inline_to_text(" ".join(paragraph_lines)))
      add_vertical_space(6)
      paragraph_lines = []

  for raw_line in markdown.splitlines():
    stripped = raw_line.strip()

    if stripped.startswith("```"):
      flush_paragraph()
      in_code_block = not in_code_block
      continue

    if in_code_block:
      add_text(stripped, size=10, leading=13, indent=12)
      continue

    if not stripped:
      flush_paragraph()
      continue

    heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
    bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
    numbered = re.match(r"^(\d+\.)\s+(.+)$", stripped)

    if heading:
      flush_paragraph()
      level = len(heading.group(1))
      size = 22 if level == 1 else 16 if level == 2 else 13
      add_vertical_space(8 if y < page_height - margin else 0)
      add_text(markdown_inline_to_text(heading.group(2)), font="F2", size=size, leading=size + 6)
      add_vertical_space(6)
    elif bullet:
      flush_paragraph()
      add_text("- " + markdown_inline_to_text(bullet.group(1)), indent=12)
    elif numbered:
      flush_paragraph()
      add_text(numbered.group(1) + " " + markdown_inline_to_text(numbered.group(2)), indent=12)
    else:
      paragraph_lines.append(stripped)

  flush_paragraph()
  if not stream_lines:
    add_text(" ")
  page_streams.append("\n".join(stream_lines))
  write_pdf(pdf_path, page_streams)


def build_manual_pdf(build_dir_name):
  source_path = os.path.join(MANUAL_DIR, PRODUCT_NAME + " manual.md")
  target_path = os.path.join(PROJECT_DIR, build_dir_name, "manual", PRODUCT_NAME + " manual.pdf")
  write_markdown_pdf(source_path, target_path)
  print("Prepared manual PDF at " + target_path)


def build_mac_docs():
  target_dir = os.path.join(PROJECT_DIR, "build-mac", "installer", "resources")
  build_manual_pdf("build-mac")

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
  build_manual_pdf("build-win")

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
