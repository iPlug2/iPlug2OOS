#!/usr/bin/python3

# Python shell script for Duplicating IPlug Projects
# Oli Larkin 2012-2019
# License: WTFPL http://sam.zoy.org/wtfpl/COPYING
# Modified from this script by Bibha Tripathi http://code.activestate.com/recipes/435904-sedawk-python-script-to-rename-subdirectories-of-a/
# Author accepts no responsibilty for wiping your hd

# NOTES:
# requires Python3
# not designed to be fool proof- think carefully about what you choose for a project name
# best to stick to standard characters in your project names - avoid spaces, numbers and dots
# windows users need to install python and set it up so you can run it from the command line
# see http://www.voidspace.org.uk/python/articles/command_line.shtml
# this involves adding the python folder e.g. C:\Python27\ to your %PATH% environment variable

# USAGE:
# duplicate.py [inputprojectname] [outputprojectname] [manufacturername] (outputpath)
# Run with no arguments to be prompted for each of them.
#
# By default only the duplicated project is touched. Pass --rewrite-root (or answer yes to
# the prompt) to also point this repo's root files - bump_version.py, CMakeLists.txt,
# .vscode/ and .github/ - at the new project.

# TODO:
# - indentation of directory structure
# - variable manufacturer name


from __future__ import generators

import argparse, fileinput, glob, string, sys, os, re, uuid, pprint, random
from shutil import copy, copytree, ignore_patterns, rmtree
from os.path import join

scriptpath = os.path.dirname(os.path.realpath(__file__))

sys.path.insert(0, scriptpath + '/iPlug2/Scripts/')

from parse_config import parse_config, parse_xcconfig, set_uniqueid

VERSION = "1.0"

# binary files that we don't want to do find and replace inside
FILTERED_FILE_EXTENSIONS = [".ico",".icns", ".pdf", ".png", ".zip", ".exe", ".wav", ".aif", ".data", ".wasm", "mkcert"]
FILTERED_FILE_NAMES = [".DS_Store", "duplicate.py"]
# additionally skipped when rewriting the repo root: these describe the templates, which still
# exist after duplicating. Rewriting them renames the templates the docs are talking about, and
# a substring match turns e.g. TemplateProjectWebView into MyPluginWebView.
ROOT_FILTERED_FILE_NAMES = FILTERED_FILE_NAMES + ["CLAUDE.md", "README.md"]
# the iPlug2 root as spelled in a template's CMakeLists.txt, relative to the project dir
CMAKE_IPLUG2_DIR = "${CMAKE_CURRENT_SOURCE_DIR}/../iPlug2"
# files that we don't want to duplicate
DONT_COPY = (".vs", "*.exe", "*.dmg", "*.pkg", "*.mpkg", "*.svn", "*.ncb", "*.suo", "*sdf", "ipch", "*.layout", "*.depend", ".DS_Store", "xcuserdata", "*.aps")

SUBFOLDERS_TO_SEARCH = [
"projects",
"config",
"resources",
"installer",
"scripts",
"manual",
"xcschemes",
"xcshareddata",
"xcuserdata",
"en-osx.lproj",
"project.xcworkspace",
"Images.xcassets",
"build-web-wasm",
"web"
]

def randomFourChar(chars=string.ascii_letters + string.digits):
  return ''.join(random.choice(chars) for _ in range(4))

def checkdirname(name, searchproject):
  "check if directory name matches with the given pattern"
  print("")
  if name == searchproject:
    return True
  else:
    return False

def replacestrs(filename, s, r):
  files = glob.glob(filename)

  for line in fileinput.input(files,inplace=1):
    line.find(s)
    line = line.replace(s, r)
    sys.stdout.write(line)

def replacestrsChop(filename, s, r):
  files = glob.glob(filename)

  for line in fileinput.input(files,inplace=1):
    if(line.startswith(s)):
      line = r + "\n"
    sys.stdout.write(line)

def dirwalk(dir, searchproject, replaceproject, searchman, replaceman, oldroot= "", newroot="", filterednames=FILTERED_FILE_NAMES):
  for f in os.listdir(dir):
    fullpath = os.path.join(dir, f)

    if os.path.isdir(fullpath) and not os.path.islink(fullpath):
      if checkdirname(f, searchproject + "-macOS.xcodeproj"):
        os.rename(fullpath, os.path.join(dir, replaceproject + "-macOS.xcodeproj"))
        fullpath = os.path.join(dir, replaceproject + "-macOS.xcodeproj")

        print("recursing in macOS xcode project directory: ")
        for x in dirwalk(fullpath, searchproject, replaceproject, searchman, replaceman, oldroot, newroot, filterednames):
          yield x
      elif checkdirname(f, searchproject + "-iOS.xcodeproj"):
        os.rename(fullpath, os.path.join(dir, replaceproject + "-iOS.xcodeproj"))
        fullpath = os.path.join(dir, replaceproject + "-iOS.xcodeproj")

        print("recursing in iOS xcode project directory: ")
        for x in dirwalk(fullpath, searchproject, replaceproject, searchman, replaceman, oldroot, newroot, filterednames):
          yield x
      elif checkdirname(f, searchproject + ".xcworkspace"):
        os.rename(fullpath, os.path.join(dir, replaceproject + ".xcworkspace"))
        fullpath = os.path.join(dir, replaceproject + ".xcworkspace")

        print("recursing in main xcode workspace directory: ")
        for x in dirwalk(fullpath, searchproject, replaceproject, searchman, replaceman, oldroot, newroot, filterednames):
          yield x
      elif checkdirname(f, searchproject + "-iOS.appiconset"):
        os.rename(fullpath, os.path.join(dir, replaceproject + "-iOS.appiconset"))
        fullpath = os.path.join(dir, replaceproject + "-iOS.appiconset")

        print("recursing in -iOS.appiconset directory: ")
      elif checkdirname(f, searchproject + "-macOS.appiconset"):
        os.rename(fullpath, os.path.join(dir, replaceproject + "-macOS.appiconset"))
        fullpath = os.path.join(dir, replaceproject + "-macOS.appiconset")

        print("recursing in -macOS.appiconset directory: ")
        for x in dirwalk(fullpath, searchproject, replaceproject, searchman, replaceman, oldroot, newroot, filterednames):
          yield x
      elif (f in SUBFOLDERS_TO_SEARCH):
        print('recursing in ' + f + ' directory: ')
        for x in dirwalk(fullpath, searchproject, replaceproject, searchman, replaceman, oldroot, newroot, filterednames):
          yield x

    if os.path.isfile(fullpath):
      filename = os.path.basename(fullpath)
      newfilename = filename.replace(searchproject, replaceproject)
      base, extension = os.path.splitext(filename)

      if (not(extension in FILTERED_FILE_EXTENSIONS) and not(filename in filterednames)):

        print("Replacing project name strings in file " + filename)
        replacestrs(fullpath, searchproject, replaceproject)

        print("Replacing captitalized project name strings in file " + filename)
        replacestrs(fullpath, searchproject.upper(), replaceproject.upper())

        print("Replacing manufacturer name strings in file " + filename)
        replacestrs(fullpath, searchman, replaceman)

        if (oldroot and newroot):
          print ("Replacing iPlug2 root folder in file  " + filename)
          replacestrs(fullpath, oldroot, newroot)
          replacestrs(fullpath, oldroot.replace('/', '\\'), newroot.replace('/', '\\'))

      else:
        print("NOT replacing name strings in file " + filename)

      if filename != newfilename:
        print("Renaming file " + filename + " to " + newfilename)
        os.rename(fullpath, os.path.join(dir, newfilename))

      yield f, fullpath
    else:
      yield f, fullpath

def find_projects():
  """Directories next to this script that look like an iPlug2 project. Any of them can be
  duplicated, not just the templates, so projects you have already made show up too."""
  projects = []

  for f in sorted(os.listdir(scriptpath)):
    if os.path.isdir(os.path.join(scriptpath, f)) and os.path.isfile(os.path.join(scriptpath, f, "config.h")):
      projects.append(f)

  return projects

def default_project(projects):
  "a template makes a better default than whatever project happens to sort first"
  for p in projects:
    if p.startswith("TemplateProject"):
      return p

  return projects[0] if projects else ""

def prompt(question, default=""):
  suffix = " [" + default + "]: " if default else ": "

  try:
    answer = input(question + suffix).strip()
  except EOFError:
    answer = ""

  return answer if answer else default

def prompt_yes_no(question, default=False):
  answer = prompt(question + (" [y/N]" if not default else " [Y/n]"))

  if not answer:
    return default

  return answer[0].lower() == "y"

def find_iplug2_root(inputprojectname):
  """Where iPlug2 lives, as an absolute path. Prefer the template's own xcconfig, since a
  template may point somewhere other than the submodule, and fall back to the submodule for
  CMake-only templates, which have no config/ directory."""
  xcconfigpath = os.path.join(scriptpath, inputprojectname, "config", inputprojectname + "-mac.xcconfig")

  if os.path.isfile(xcconfigpath):
    oldroot = parse_xcconfig(xcconfigpath)["IPLUG2_ROOT"]
    return oldroot, os.path.abspath(os.path.join(scriptpath, inputprojectname, "config", oldroot))

  return "", os.path.join(scriptpath, "iPlug2")

def fix_cmake_iplug2_dir(outputpath, iplug2folder):
  """Point the duplicated CMakeLists.txt at iPlug2. Its default is a sibling ../iPlug2, which is
  only true for a project sitting in this repo, so an out-of-source duplicate needs rewriting.
  The xcconfig equivalent is handled by the oldroot/newroot pass in dirwalk()."""
  cmakelists = os.path.join(outputpath, "CMakeLists.txt")

  if not os.path.isfile(cmakelists):
    return

  newdir = os.path.relpath(iplug2folder, outputpath).replace(os.sep, "/")

  print("Pointing CMakeLists.txt at iPlug2 via " + newdir)
  replacestrs(cmakelists, CMAKE_IPLUG2_DIR, "${CMAKE_CURRENT_SOURCE_DIR}/" + newdir)

def main():
  global VERSION
  print("\nIPlug Project Duplicator v" + VERSION + " by Oli Larkin ------------------------------\n")

  projects = find_projects()

  parser = argparse.ArgumentParser(description="Duplicate an iPlug2 project. Omit any argument to be prompted for it.")
  parser.add_argument("inputprojectname", nargs="?", help="project to copy, one of: " + ", ".join(projects))
  parser.add_argument("outputprojectname", nargs="?", help="name of the new project")
  parser.add_argument("manufacturername", nargs="?", help="your company name, replaces AcmeInc")
  parser.add_argument("outputprojectpath", nargs="?", help="where to put it (default: this repo)")

  rootgroup = parser.add_mutually_exclusive_group()
  rootgroup.add_argument("--rewrite-root", dest="rewriteroot", action="store_true", default=None,
                         help="also point this repo's bump_version.py, CMakeLists.txt, .vscode/ and .github/ at the new project")
  rootgroup.add_argument("--no-rewrite-root", dest="rewriteroot", action="store_false",
                         help="leave this repo's own files alone (default when not a terminal)")

  args = parser.parse_args()

  interactive = sys.stdin.isatty()

  inputprojectname = args.inputprojectname
  outputprojectname = args.outputprojectname
  manufacturer = args.manufacturername

  if not inputprojectname:
    if not interactive:
      parser.error("inputprojectname is required when not running interactively")

    print("Projects you can duplicate: " + ", ".join(projects) + "\n")
    inputprojectname = prompt("Project to duplicate", default_project(projects))

  if not outputprojectname:
    if not interactive:
      parser.error("outputprojectname is required when not running interactively")

    outputprojectname = prompt("Name of the new project")

  if not manufacturer:
    if not interactive:
      parser.error("manufacturername is required when not running interactively")

    manufacturer = prompt("Manufacturer name", "AcmeInc")

  # remove a trailing slash if it exists
  if inputprojectname[-1:] == "/":
    inputprojectname = inputprojectname[0:-1]

  if outputprojectname[-1:] == "/":
    outputprojectname = outputprojectname[0:-1]

  if not outputprojectname:
    print("error: output project name is empty")
    sys.exit(1)

  if ' ' in inputprojectname:
    print("error: input project name has spaces")
    sys.exit(1)

  if ' ' in outputprojectname:
    print("error: output project name has spaces")
    sys.exit(1)

  if ' ' in manufacturer:
    print("error: manufacturer name has spaces")
    sys.exit(1)

  #check that the folders are OK
  if not os.path.isdir(os.path.join(scriptpath, inputprojectname)):
    print("error: input project " +  inputprojectname + " doesn't exist, check spelling/case?")
    sys.exit(1)

  outofsource = args.outputprojectpath is not None

  if outofsource:
    outputbasepath = os.path.abspath(args.outputprojectpath)
  else:
    outputbasepath = scriptpath

  if not (os.path.isdir(outputbasepath)):
    print("error: Output path does not exist")
    sys.exit(1)

  outputpath = os.path.join(outputbasepath, outputprojectname)

  if os.path.isdir(outputpath):
    print("error: output project allready exists")
    sys.exit(1)
  # rmtree(output)

  # Rewriting this repo's own files is destructive and usually unwanted, so it is opt-in.
  rewriteroot = args.rewriteroot

  if rewriteroot is None:
    if interactive:
      print("\nThe repo's own bump_version.py, CMakeLists.txt, .vscode/ and .github/ still refer")
      print("to " + inputprojectname + ". They can be repointed at " + outputprojectname + ", which is what you want if")
      print("this repo is becoming your plugin's repo, and not what you want if you are just")
      print("adding another project alongside the templates.")
      rewriteroot = prompt_yes_no("Repoint them at " + outputprojectname + "?", False)
    else:
      rewriteroot = False

  oldroot, iplug2folder = find_iplug2_root(inputprojectname)
  newroot = ""

  # the xcconfig spells the iPlug2 root relative to the project's config/ dir, so it only needs
  # rewriting when the project moves out of this repo
  if outofsource and oldroot:
    newroot = os.path.relpath(iplug2folder, os.path.join(outputpath, "config"))

  print("copying " + inputprojectname + " folder to " + outputpath)
  copytree(os.path.join(scriptpath, inputprojectname), outputpath, ignore=ignore_patterns(*DONT_COPY))

  #replace manufacturer name strings
  for dir in dirwalk(outputpath, inputprojectname, outputprojectname, "AcmeInc", manufacturer, oldroot, newroot):
    pass

  if outofsource:
    fix_cmake_iplug2_dir(outputpath, iplug2folder)

  if rewriteroot:
    #replace project name in root, but not in the docs describing the templates
    for dir in dirwalk(scriptpath, inputprojectname, outputprojectname, "AcmeInc", manufacturer, "", "", ROOT_FILTERED_FILE_NAMES):
      pass

    #replace project name in github
    if os.path.isdir(scriptpath + "/.github/workflows"):
      for dir in dirwalk(scriptpath + "/.github/workflows", inputprojectname, outputprojectname, "AcmeInc", manufacturer):
        pass

    #replace project name in vscode
    if os.path.isdir(scriptpath + "/.vscode"):
      for dir in dirwalk(scriptpath + "/.vscode", inputprojectname, outputprojectname, "AcmeInc", manufacturer):
        pass
  else:
    print("\nleaving this repo's root files alone (pass --rewrite-root to change that)")

  # print("\ncopying gitignore template into project folder\n")

  # copy('gitignore_template', outputpath + "/.gitignore")

  config = parse_config(outputpath)

  # a REAPER extension has no plugin id to randomise
  if config["PLUG_UNIQUE_ID"]:
    config["PLUG_UNIQUE_ID"] = randomFourChar()
    set_uniqueid(outputpath, config["PLUG_UNIQUE_ID"])

  pp = pprint.PrettyPrinter(indent=4)
  pp.pprint(config)

  print("\ndone - don't forget to change PLUG_MFR_ID in config.h")

if __name__ == '__main__':
  main()
