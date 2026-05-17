# CLAUDE.md

iPlug2 plugin project. This document describes choices in this project's structure that are not obvious from the iPlug2 framework docs.

> This file is duplicated by `../duplicate.py` along with the rest of the project, and the project-name string-rewrite pass runs over it — so `TemplateProject.cpp` etc. resolve to the new project's filenames after duplication.

## UI: responsive IGraphics layout

The UI in `TemplateProject.cpp` is a **resizable / responsive IGraphics** example. The pattern is the important thing to preserve when extending it.

Key pieces:

- `config.h` enables host resize and sets bounds: `PLUG_HOST_RESIZE 1`, `PLUG_MIN_WIDTH/HEIGHT`, `PLUG_MAX_WIDTH/HEIGHT`.
- `OnHostRequestingSupportedViewConfiguration` returns `true` so hosts know any size in range is acceptable.
- `mLayoutFunc` runs on both first attach AND every resize: in the initial-attach branch it calls `pGraphics->SetLayoutOnResize(true)` and `AttachCornerResizer(...)`, which together cause it to re-run on every resize.

### How `mLayoutFunc` is structured

The function computes every IRECT once at the top from the current `pGraphics->GetBounds()`, then splits:

1. **Resize branch (appears first in the code):** `if (pGraphics->NControls()) { ... return; }` — re-applies each tagged control's new rect via `SetTargetAndDrawRECTs(...)` (background uses `GetBackgroundControl()`), then returns early so the attach code below doesn't run again.
2. **Initial-attach branch (fall-through below the `if`):** one-time setup — `SetLayoutOnResize(true)`, `AttachCornerResizer`, `LoadFont`, `AttachPanelBackground`, then `AttachControl(...)` for each control with its tag.

The early `return` in the resize branch is load-bearing — without it, controls would be re-attached on every resize.

Because the IRECTs are computed once at the top, the same layout math feeds both branches.

## Adding a new control — checklist

To keep the responsive layout working, every new control needs all of these:

1. Add a tag to `ECtrlTags` in the plugin header.
2. In `mLayoutFunc`, compute its `IRECT` at the top from `innerBounds` (or `bounds`) using IRECT helpers like `GetFromLeft`, `GetMidVPadded`, `GetCentredInside`, `GetGridCell`, etc. — never hard-code pixel coordinates that don't derive from the current bounds.
3. In the **resize branch** (inside `if (pGraphics->NControls())`, before the `return`), add `pGraphics->GetControlWithTag(kYourTag)->SetTargetAndDrawRECTs(yourRect);`.
4. In the **initial-attach branch** (the fall-through below the `if`), `AttachControl(new IVWhatever(rect, ...), kYourTag);`.

Forgetting step 3 is the common mistake: the control will appear correctly at startup but stay frozen at its original rect when the window is resized.

Controls that are not tagged (e.g. the panel background, corner resizer) are handled via their dedicated accessors or don't need repositioning.

## Files of interest

- `TemplateProject.cpp` / `.h` — plugin class, parameters (`EParams`), control tags (`ECtrlTags`), `ProcessBlock`, `mLayoutFunc`.
- `config.h` — plugin metadata, channel I/O, size constraints, format-specific IDs (`PLUG_UNIQUE_ID`, `PLUG_MFR_ID`, `AAX_TYPE_IDS`, etc.).
- `projects/` — per-format IDE projects (Xcode, VS, WAM makefiles).
- `resources/` — Info.plists, icons, fonts, images. Fonts referenced via `*_FN` macros in `config.h` (e.g. `ROBOTO_FN`).
- `CMakeLists.txt` — alternative CMake build (see `build-cmake` skill).
- `build-mac/`, `build-win/`, `installer/`, `manual/`, `scripts/` — build, packaging, and docs tooling.
