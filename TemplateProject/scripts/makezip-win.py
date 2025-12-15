import zipfile, os, fileinput, string, sys, shutil

scriptpath = os.path.dirname(os.path.realpath(__file__))
projectpath = os.path.abspath(os.path.join(scriptpath, os.pardir))

IPLUG2_ROOT = "..\..\iPlug2"

sys.path.insert(0, os.path.join(scriptpath, IPLUG2_ROOT + '\Scripts'))

from get_archive_name import get_archive_name

def add_folder_to_zip(zf, folder_path, archive_base):
  """Add a folder and its contents to a zip file, preserving structure."""
  for root, dirs, files in os.walk(folder_path):
    for file in files:
      file_path = os.path.join(root, file)
      arcname = os.path.join(archive_base, os.path.relpath(file_path, folder_path))
      print("adding " + file_path + " as " + arcname)
      zf.write(file_path, arcname, zipfile.ZIP_DEFLATED)

def main():
  if len(sys.argv) != 3:
    print("Usage: make_zip.py demo[0/1] zip[0/1]")
    sys.exit(1)
  else:
    demo=int(sys.argv[1])
    zip=int(sys.argv[2])

  dir = projectpath + "\\build-win\\out"

  if os.path.exists(dir):
    shutil.rmtree(dir)

  os.makedirs(dir)

  zipname = get_archive_name(projectpath, "win", "demo" if demo == 1 else "full" )
  zf = zipfile.ZipFile(projectpath + "\\build-win\\out\\" + zipname + ".zip", mode="w")

  if not zip:
    installer = "\\build-win\\installer\\TemplateProject Installer.exe"

    if demo:
      installer = "\\build-win\\installer\\TemplateProject Demo Installer.exe"

    files = [
      projectpath + installer,
      projectpath + "\\installer\\changelog.txt",
      projectpath + "\\installer\\known-issues.txt",
      projectpath + "\\manual\\TemplateProject manual.pdf"
    ]

    for f in files:
      print("adding " + f)
      zf.write(f, os.path.basename(f), zipfile.ZIP_DEFLATED)
  else:
    # Add VST3 bundle with folder structure preserved
    vst3_bundle = projectpath + "\\build-win\\TemplateProject.vst3"
    if os.path.exists(vst3_bundle):
      add_folder_to_zip(zf, vst3_bundle, "TemplateProject.vst3")

    # Add standalone executables
    files = [
      projectpath + "\\build-win\\TemplateProject_x64.exe",
      projectpath + "\\build-win\\TemplateProject_ARM64EC.exe",
      projectpath + "\\build-win\\TemplateProject.clap"
    ]

    for f in files:
      if os.path.exists(f):
        print("adding " + f)
        zf.write(f, os.path.basename(f), zipfile.ZIP_DEFLATED)

  zf.close()
  print("wrote " + zipname)

  # Create PDB archive
  zf = zipfile.ZipFile(projectpath + "\\build-win\\out\\" + zipname + "-pdbs.zip", mode="w")

  files = [
    projectpath + "\\build-win\\pdbs\\TemplateProject-vst3_x64.pdb",
    projectpath + "\\build-win\\pdbs\\TemplateProject-vst3_ARM64EC.pdb",
    projectpath + "\\build-win\\pdbs\\TemplateProject-app_x64.pdb",
    projectpath + "\\build-win\\pdbs\\TemplateProject-app_ARM64EC.pdb",
    projectpath + "\\build-win\\pdbs\\TemplateProject-clap_x64.pdb",
    projectpath + "\\build-win\\pdbs\\TemplateProject-clap_ARM64EC.pdb"
  ]

  for f in files:
    if os.path.exists(f):
      print("adding " + f)
      zf.write(f, os.path.basename(f), zipfile.ZIP_DEFLATED)

  zf.close()
  print("wrote " + zipname)

if __name__ == '__main__':
  main()
