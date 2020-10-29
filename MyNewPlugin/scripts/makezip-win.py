import zipfile, os, fileinput, string, sys, shutil

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = os.path.abspath(os.path.join(scriptpath, os.pardir))

IPLUG2_ROOT = "../../iPlug2"

sys.path.insert(0, os.path.join(scriptpath, IPLUG2_ROOT + '\Scripts'))

from parse_config import parse_config

MajorStr = ""
MinorStr = "" 
BugfixStr = ""
BUNDLE_NAME = ""

def main():
  if len(sys.argv) != 3:
    print("Usage: make_zip.py demo[0/1] zip[0/1]")
    sys.exit(1)
  else:
    demo=int(sys.argv[1])
    zip=int(sys.argv[2])
 
  config = parse_config(projectpath)
  
  dir = projectpath + "\\build-win\\out"
  
  if os.path.exists(dir):
    shutil.rmtree(dir)
  
  os.makedirs(dir)
  
  files = []

  if not zip:
    installer = "\\build-win\\installer\\MyNewPlugin Installer.exe"
    
    if demo:
      installer = "\\build-win\\installer\\MyNewPlugin Demo Installer.exe"
    
    files = [
      projectpath + installer,
      projectpath + "\installer\changelog.txt",
      projectpath + "\installer\known-issues.txt",
      projectpath + "\manual\MyNewPlugin manual.pdf" 
    ]
  else:
    files = [
      projectpath + "\\build-win\MyNewPlugin.vst3\Contents\\x86_64-win\MyNewPlugin.vst3",
      projectpath + "\\build-win\MyNewPlugin_x64.exe"  
    ]

  zipname = "MyNewPlugin-v" + config['FULL_VER_STR']
  
  if demo:
    zipname = zipname + "-win-demo"
  else:
    zipname = zipname + "-win"

  zf = zipfile.ZipFile(projectpath + "\\build-win\\out\\" + zipname + ".zip", mode="w")

  for f in files:
    print("adding " + f)
    zf.write(f, os.path.basename(f), zipfile.ZIP_DEFLATED)

  zf.close()
  print("wrote " + zipname)

  zf = zipfile.ZipFile(projectpath + "\\build-win\\out\\" + zipname + "-pdbs.zip", mode="w")

  files = [
    projectpath + "\\build-win\\pdbs\\MyNewPlugin-vst3_x64.pdb",
    projectpath + "\\build-win\\pdbs\\MyNewPlugin-app_x64.pdb"  
  ]

  for f in files:
    print("adding " + f)
    zf.write(f, os.path.basename(f), zipfile.ZIP_DEFLATED)

  zf.close()
  print (zipname)
  # print("wrote " + zipname)



if __name__ == '__main__':
  main()
