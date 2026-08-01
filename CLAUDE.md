# CLAUDE.md

## iPlug2OOS "Out of Source"

This repo keeps plugin projects separate from the iPlug2 framework. Structure:

- @iPlug2 - Framework as git submodule
- TemplateProject - Base template for new plugins (IGraphics UI)
- TemplateProjectWebView - Plugin template with a WebView UI (HTML/CSS/JS), CMake only
- TemplateProjectReaperExtensionWebView - REAPER extension (not a plugin) with a WebView UI, CMake only, macOS/Windows
- duplicate.py - Script to create new projects by duplicating a template

## Workflow

To create a new plugin, duplicate @TemplateProject using the `new-plugin` skill or:

```bash
./duplicate.py TemplateProject [PluginName] [ManufacturerName]
```

Substitute another template for `TemplateProject` to start from a WebView UI or a REAPER
extension. Run `./duplicate.py` with no arguments to be prompted instead.

Pass a fourth argument to create the project outside this repo; the iPlug2 paths in its
`CMakeLists.txt` and xcconfigs are rewritten to suit. By default nothing outside the new
project is modified — pass `--rewrite-root` to also repoint this repo's `bump_version.py`,
`CMakeLists.txt`, `.vscode/` and `.github/` at it, which is what you want when the repo is
becoming your plugin's repo rather than gaining another project alongside the templates.

After duplication, optionally commit:
```bash
git add [PluginName]/* .vscode/* .github/* bump_version.py
git commit -m "created [PluginName] based on TemplateProject"
```

## Additional Context

- iPlug2 framework: @iPlug2/CLAUDE.md
- Project structure: @iPlug2/Documentation/structure.md
