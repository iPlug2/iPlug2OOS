---
name: new-plugin
description: Create a new iPlug2 plugin project by duplicating TemplateProject in the iPlug2OOS repository
---

# Create New Plugin (iPlug2OOS)

Use this skill when the user wants to create a new plugin project in this out-of-source repository.

## Workflow

1. **Gather project details:**
   - **Plugin name** (required): No spaces or special characters
   - **Manufacturer name** (required): No spaces

2. **Check for existing projects:**
   - If other project folders exist besides TemplateProject, ask if user wants to continue with existing work or create new

3. **Choose a template and run the duplicate script:**

   | Template | Use for |
   |---|---|
   | `TemplateProject` | A plugin with an IGraphics (C++) UI |
   | `TemplateProjectWebView` | A plugin with a WebView (HTML/CSS/JS) UI |
   | `TemplateProjectReaperExtensionWebView` | A REAPER extension with a WebView UI |

   ```bash
   ./duplicate.py [Template] [PluginName] [ManufacturerName]
   ```

   This touches only the new project. Add `--rewrite-root` to also repoint the repo's
   `bump_version.py`, `CMakeLists.txt`, `.vscode/` and `.github/` at it — appropriate when
   this repo is becoming the plugin's own repo. Add a fourth positional argument to create
   the project outside this repo.

4. **Offer config.h customization:**
   - `PLUG_UNIQUE_ID` - Verify the auto-generated 4-char ID (not present for a REAPER extension)
   - `PLUG_MFR_ID` - Set manufacturer's 4-char ID
   - Copyright, URLs - allow skipping for later

5. **Ask about committing:**
   ```bash
   git add [PluginName]/*
   git commit -m "created [PluginName] based on [Template]"
   ```
   Also stage `.vscode/*`, `.github/*` and `bump_version.py` if `--rewrite-root` was used;
   otherwise those files are unchanged.

6. **Next steps:**
   - Open in Xcode: `open [PluginName]/[PluginName].xcworkspace` (IGraphics template only —
     the CMake-only templates have no xcworkspace; configure with CMake instead)
   - Build: Use the `build` skill, or `build-cmake` for the CMake-only templates
   - Setup SDKs: Use the `setup-deps` skill if needed

## Example

```bash
./duplicate.py TemplateProject MySynth MyBrand
```

Creates `MySynth/` with all project files configured and ready to build. Run `./duplicate.py`
with no arguments to be prompted for the template, name and manufacturer instead.
