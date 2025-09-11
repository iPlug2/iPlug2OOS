#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import glob
import fileinput
import semver

IPLUG2_ROOT = "iPlug2"
PROJECT_ROOT = "TemplateProject"
PROJECT_SCRIPTS = os.path.join(PROJECT_ROOT, "scripts")

def replacestrs(filename, s, r):
    files = glob.glob(filename)
    print(f"Replacing '{s}' with '{r}' in {filename}")
    for line in fileinput.input(files, inplace=True):
        line = line.replace(s, r)
        sys.stdout.write(line)

scripts_dir = os.path.join(os.getcwd(), IPLUG2_ROOT, "Scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from parse_config import parse_config 

def main():
    config = parse_config(PROJECT_ROOT)
    versionStr = config['FULL_VER_STR']
    currentVersionInfo = semver.VersionInfo.parse(versionStr)
    print(f"Current version in config.h: v{versionStr}")

    if len(sys.argv) == 2:
        arg = sys.argv[1].lower()
        if arg == 'major':
            newVersionInfo = currentVersionInfo.bump_major()
        elif arg == 'minor':
            newVersionInfo = currentVersionInfo.bump_minor()
        elif arg == 'patch':
            newVersionInfo = currentVersionInfo.bump_patch()
        else:
            print("Unknown argument. Using current version.")
            newVersionInfo = currentVersionInfo
    else:
        print("Please supply an argument: major, minor, or patch")
        sys.exit(1)

    newVersionInt = ((newVersionInfo.major << 16) & 0xFFFF0000) + \
                    ((newVersionInfo.minor << 8) & 0x0000FF00) + \
                    (newVersionInfo.patch & 0x000000FF)

    replacestrs(
        os.path.join(PROJECT_ROOT, "config.h"),
        f'#define PLUG_VERSION_STR "{versionStr}"',
        f'#define PLUG_VERSION_STR "{newVersionInfo}"'
    )
    replacestrs(
        os.path.join(PROJECT_ROOT, "config.h"),
        f'#define PLUG_VERSION_HEX {config["PLUG_VERSION_HEX"]}',
        f'#define PLUG_VERSION_HEX 0x{newVersionInt:08x}'
    )

    subprocess.run(["python3", "update_version-mac.py"], cwd=PROJECT_SCRIPTS)
    subprocess.run(["python3", "update_version-ios.py"], cwd=PROJECT_SCRIPTS)
    subprocess.run(["python3", "update_installer-win.py", "0"], cwd=PROJECT_SCRIPTS)

    print("\nCurrent changelog: \n--------------------")
    subprocess.run(["cat", os.path.join(PROJECT_ROOT, "installer", "changelog.txt")])
    print("\n--------------------")

    edit = input("\nEdit changelog? Y/N: ").strip().lower()
    if edit == 'y':
        subprocess.run(["vim", os.path.join(PROJECT_ROOT, "installer", "changelog.txt")])
        print("\nNew changelog: \n--------------------")
        subprocess.run(["cat", os.path.join(PROJECT_ROOT, "installer", "changelog.txt")])
        print("\n--------------------")

    edit = input("\nTag version and git push to origin (will prompt for commit message)? Y/N: ").strip().lower()
    if edit == 'y':
        subprocess.run(["git", "commit", "-a", "--allow-empty"])
        subprocess.run(["git", "tag", f"v{newVersionInfo}"])
        subprocess.run(["git", "push"])
        subprocess.run(["git", "push", "--tags"])

if __name__ == '__main__':
    main()
