#!/usr/bin/env python3

# this script will update the version and text in the innosetup installer files, based on config.h and demo 1/0

import plistlib, os, datetime, fileinput, glob, sys, string, re
scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = os.path.abspath(os.path.join(scriptpath, os.pardir))

IPLUG2_ROOT = "../../iPlug2"

sys.path.insert(0, os.path.join(os.getcwd(), IPLUG2_ROOT + '/Scripts'))

from parse_config import parse_config

README_SOURCE_RE = re.compile(r'^\s*Source:\s*"', re.IGNORECASE)
README_DEST_RE = re.compile(r'\bDestName:\s*"readme\.txt"', re.IGNORECASE)

def is_readme_entry(line):
  return README_SOURCE_RE.search(line) and README_DEST_RE.search(line)

def readme_entry(demo):
  readme = "readme-win-demo.txt" if demo else "readme-win.txt"
  return f'Source: "..\\build-win\\installer-docs\\{readme}"; DestDir: "{{app}}"; DestName: "readme.txt"; Flags: isreadme\n'

def replacestrs(filename, s, r):
  files = glob.glob(filename)
  
  for line in fileinput.input(files,inplace=1):
    string.find(line, s)
    line = line.replace(s, r)
    sys.stdout.write(line)

def main():
  demo = 0
  
  if len(sys.argv) != 2:
    print("Usage: update_installer_version.py demo(0 or 1)")
    sys.exit(1)
  else:
    demo=int(sys.argv[1])

  config = parse_config(projectpath)

# WIN INSTALLER
  print("Updating Windows Installer version info...")
  
  for line in fileinput.input(projectpath + "/installer/" + config['BUNDLE_NAME'] + ".iss",inplace=1):
    if "AppVersion" in line:
      line="AppVersion=" + config['FULL_VER_STR'] + "\n"
    if "OutputBaseFilename" in line:
      if demo:
        line="OutputBaseFilename=TemplateProject Demo Installer\n"
      else:
        line="OutputBaseFilename=TemplateProject Installer\n"
        
    if is_readme_entry(line):
      line=readme_entry(demo)
    
    if "WelcomeLabel1" in line:
     if demo:
       line="WelcomeLabel1=Welcome to the TemplateProject Demo installer\n"
     else:
       line="WelcomeLabel1=Welcome to the TemplateProject installer\n"
       
    if "SetupWindowTitle" in line:
     if demo:
       line="SetupWindowTitle=TemplateProject Demo installer\n"
     else:
       line="SetupWindowTitle=TemplateProject installer\n"
       
    sys.stdout.write(line) 
    
    
if __name__ == '__main__':
  main()
