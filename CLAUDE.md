# CLAUDE.md

## iPlug2OOS "Out of Source"

This repo keeps plugin projects separate from the iPlug2 framework. Structure:

- @iPlug2 - Framework as git submodule
- TemplateProject - Base template for new plugins
- duplicate.py - Script to create new projects by duplicating a template

## Workflow

To create a new plugin, duplicate @TemplateProject using the `new-plugin` skill or:

```bash
./duplicate.py TemplateProject [PluginName] [ManufacturerName]
```

After duplication, optionally commit:
```bash
git add [PluginName]/* .vscode/* .github/* bump_version.py
git commit -m "created [PluginName] based on TemplateProject"
```

## Additional Context

- iPlug2 framework: @iPlug2/CLAUDE.md
- Project structure: @iPlug2/Documentation/structure.md
