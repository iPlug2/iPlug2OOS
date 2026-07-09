# CLAUDE.md

A **REAPER extension** with a **WebView UI**. This is not an audio plugin: it loads into REAPER
itself, calls the REAPER API, and puts up a dockable window whose UI is authored in HTML/CSS/JS
under `resources/web/`.

> This file is duplicated by `../duplicate.py` along with the rest of the project, and the
> project-name string-rewrite pass runs over it — so `TemplateProjectReaperExtensionWebView.cpp`
> etc. resolve to the new project's filenames after duplication.

## How this differs from a plugin project

Coming from `../TemplateProject` or `../TemplateProjectWebView`, most of the plugin scaffolding is
simply absent, and it is worth knowing what is gone before looking for it:

- **No `iplug::Plugin`.** The class derives from `ReaperExtBase`, via
  `ReaperExt_include_in_plug_hdr.h` / `ReaperExt_include_in_plug_src.h`.
- **No `ProcessBlock`, no realtime thread.** Audio work here is offline: you pull samples out of
  the project with an audio accessor and write a file. Nothing you write runs on the audio thread,
  so the usual realtime-safety rules don't apply.
- **No parameters.** There is no host to expose them to, so there is no `EParams`, no
  `GetParam()`, and no automation. `SPVFD`/`SPVFUI` and the rest of the parameter bridge exist in
  `script.js` but go unused — state lives in plain C++ members and is pushed to the UI by hand
  (see *Talking to the UI* below).
- **No plugin formats, no presets, no `PLUG_CHANNEL_IO`.** `config.h` is correspondingly tiny.
- **macOS and Windows only.** No iOS, no WASM/Emscripten, so there is no `IPLUG_EDITOR` /
  `IPLUG_DSP` split to maintain — `ReaperExt.cmake` defines both to `1` and the whole extension is
  a single binary. The `CMakeLists.txt` bails out early on iOS and Emscripten.
- **No `iplug_add_plugin()`.** The target is a plain `add_library(... MODULE ...)` configured by
  `iplug_configure_reaperext()`, which names the binary `reaper_<project>` (REAPER only loads
  extensions with that prefix), restricts the exported symbols to `ReaperPluginEntry` and
  `SWELL_dllMain`, and deploys to REAPER's `UserPlugins` directory.

On macOS the extension links only SWELL's *module stub* (`swell-modstub.mm`), because REAPER
already provides SWELL. `ReaperExt.cmake` handles this; compiling the full SWELL sources into the
extension would leave every SWELL symbol undefined and the extension would silently fail to load.

## Calling the REAPER API: IMPAPI

REAPER's API is not linked — it is handed to the extension as function pointers at load time. Each
function you want must be imported by name in the constructor:

```cpp
IMPAPI(CountTracks);
IMPAPI(InsertTrackAtIndex);
```

`IMPAPI` declares a global of the right signature (from `reaper_plugin_functions.h`) and binds it.
**A function you forget to `IMPAPI` compiles fine and is a null pointer at runtime**, so a crash on
first use of a new REAPER call is almost always a missing `IMPAPI` line. Add the import next to the
others at the top of the constructor.

## Registering actions

`RegisterAction(name, lambda, addToMenu, toggleStatePtr, contextMenuId, menuLabel)` puts a lambda in
REAPER's action list. The template registers four:

- Two demo actions (a message box, and one that inserts a track).
- Show/Hide UI and Toggle dock, which pass `GetWindowTogglePtr()` / `GetDockTogglePtr()` as the
  toggle-state pointer so REAPER draws a checkmark next to the menu item.
- `Process selected item`, registered into the `"Media item context"` menu rather than the
  Extensions submenu. That menu is shared with every other installed extension, so its label names
  the extension explicitly.

## The UI

`mEditorInitFunc` runs when the window opens and calls `LoadIndexHtml(__FILE__, "")`, which loads
`resources/web/index.html` **from the source tree in debug builds**. Note the empty bundle id:
`ReaperExtBase` doesn't inherit `GetBundleID()` (that lives on `IPluginBase`), and a REAPER
extension is a bare dylib/DLL rather than a bundle. Release builds therefore have no resource
directory to load from — **if you ship this, embed the UI or point `LoadFile` at a real install
path**. `SetEnableDevTools(true)` is on in `_DEBUG`, so right-click → Inspect opens the Web
Inspector.

### Talking to the UI

Because there are no parameters, the two directions are asymmetric:

- **UI → C++**: JS calls `SAMFUI(msgTag, ctrlTag, data)` from `script.js`, which arrives at the
  `SendArbitraryMsgFromUI(int msgTag, int ctrlTag, int dataSize, const void* pData)` override. This
  is *not* the `bool OnMessage(...)` you override on `iplug::Plugin` — different name, no return
  value. `EMsgTags` in the header must stay in sync with the `kMsgTag*` constants at the top of
  `index.html`. The template smuggles the gain percentage through the `ctrlTag` int rather than
  packing a data payload.
- **C++ → UI**: there is no delegate push for non-parameter state, so the template calls
  `EvaluateJavaScript("OnTrackCount(3)")` and friends, and `index.html` defines matching global
  functions (`OnTrackCount`, `OnSetGain`, `OnDockState`).

`OnUIOpen()` is the hook for pushing current state into a freshly-loaded page. Call it for anything
the UI needs to render correctly on open — the window is destroyed and recreated when docked, so
this runs again after `ToggleDocking()`.

`index.html` also defines empty `OnParamChange` / `OnControlChange` / `OnMessage` stubs. Don't
delete them: `OnWebContentLoaded` sends a parameter-list message regardless, and `script.js`
dispatches into them unconditionally.

## Reacting to project changes

Two hooks, and the template uses both deliberately:

- `OnActionRun(commandId, flag)` — REAPER's `hookpostcommand`, fired after any main-section action.
  This catches user edits (insert track, undo) with no polling lag.
- `OnIdle()` — a safety net for changes that no action caused, such as our own *Add Track* button
  calling `InsertTrackAtIndex()` directly.

`PushTrackCount(force)` only calls into the webview when the count actually changed, so the idle
tick is cheap.

## Per-project state

An extension has no plugin state chunk. To persist per-project data, REAPER offers `projectconfig`,
wired up here as three overrides:

- `SaveProjectState(ctx)` — write lines into the `.RPP`. Prefix keys with the extension name so they
  can't collide with another extension's.
- `LoadProjectStateLine(line)` — REAPER offers every unrecognised line to every extension; parse the
  ones that are yours and **return `true` only for those**, `false` otherwise.
- `OnBeginLoadProjectState(isUndo)` — reset to defaults before the lines arrive, since a project
  without your key must not inherit the previous project's value.

This also gives you undo for free: REAPER replays project state on undo, so the same three hooks
restore the value.

## Offline processing a media item

`ProcessSelectedItem(gain)` is a worked example of the read-modify-write cycle: it reads the
selected item through a take audio accessor, applies gain, writes a new `.wav` and inserts it into
the project. Most of its length is the awkward parts, which are commented in place. The ones worth
knowing before writing your own:

- Output goes to the project's media directory (`GetProjectPathEx`), not next to the source file,
  which may be on read-only or shared storage. It falls back to the source directory for an unsaved
  project.
- The filename is uniquified (`-001`, `-002`, …) rather than overwritten — the existing file is
  usually already open in the project.
- **Section sources** (reversed, looped or trimmed takes) report an empty filename but wrap a real
  source; resolve the name through `GetMediaSourceParent()`. Takes with no media file at all
  (in-project MIDI) must be rejected.
- WDL's `WaveWriter` writes mono or stereo only, so the channel count is clamped for the writer, the
  accessor and the interleaved buffer alike. Feeding it the source count produces a header that
  disagrees with the data.
- The accessor leaves gaps untouched, so each block must be zeroed before `GetAudioAccessorSamples`.
- `WaveWriter` finalises the header in its destructor — scope it so the file is complete before
  `InsertMedia()` reads it.
- `InsertMedia()` drops the file at the edit cursor, so move the cursor to the source item's
  position and restore it afterwards.

## Adding a new UI control — checklist

1. **C++:** add a tag to `EMsgTags` and handle it in `SendArbitraryMsgFromUI`. `IMPAPI` any new
   REAPER function you call.
2. **JS:** mirror the tag as a `const kMsgTag* = n` at the top of `index.html` and call
   `SAMFUI(kMsgTagYours)` from the element.
3. **State back to the UI:** if C++ owns the value, add a `Push*()` that calls
   `EvaluateJavaScript("OnYourThing(...)")`, define the matching global in `index.html`, and call it
   from `OnUIOpen()` so the control is correct when the window (re)opens.

The common mistake is step 3: the button works, but the UI shows stale state after a dock toggle,
project load or undo.

## Files of interest

- `TemplateProjectReaperExtensionWebView.cpp` / `.h` — the extension class: `IMPAPI` imports, action
  registration, message tags, the project-state hooks, and the offline process.
- `resources/web/index.html` — the UI: markup, CSS, the `kMsgTag*` constants, and the global
  functions C++ calls via `EvaluateJavaScript`.
- `resources/web/script.js` — the bridge function definitions. Framework glue; extend, don't rename.
- `config.h` — just a class name, window size and FPS. No formats, no channel I/O.
- `CMakeLists.txt` — `ReaperExt.cmake` + `WebView.cmake`, a `MODULE` library, and
  `iplug_configure_reaperext()`.
- `resources/main.rc`, `resource.h`, `main.rc_mac_dlg` — the empty host dialog the webview is
  parented into. Windows uses `main.rc`; macOS uses the SWELL-generated `main.rc_mac_dlg`.
- `TemplateProjectReaperExtensionWebView.RPP` — a scratch REAPER project for testing. It has no
  media directory configured, so processed audio and REAPER's peak caches land in this directory;
  both are gitignored.
