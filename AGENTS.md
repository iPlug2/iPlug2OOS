# AGENTS.md

## iPlug2OOS "Out of Source"

This repo keeps plugin projects separate from the iPlug2 framework. Structure:

- @modules/iPlug2 - Framework as git submodule
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

- iPlug2 framework: @modules/iPlug2/AGENTS.md
- Project structure: @modules/iPlug2/Documentation/structure.md
