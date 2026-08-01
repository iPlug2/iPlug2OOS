# CLAUDE.md

iPlug2 plugin/app project with a **WebView UI** — the editor is authored in HTML/CSS/JS under `resources/web/`, not in IGraphics/C++.

> This file is duplicated by `../duplicate.py` along with the rest of the project, and the project-name string-rewrite pass runs over it — so `TemplateProjectWebView.cpp` etc. resolve to the new project's filenames after duplication.

## Distributed plugins

iPlug2 has a mechanism to split DSP and UI builds in two, in order that the plugin can run across procees or sandboxed boundaries, e.g. AudioWorklet in the WASM target. Typically this is only used in WASM builds. Code that should be part of the UI build is guarded with IPLUG_EDITOR and code that is part of the DSP build is guarded with IPLUG_DSP. The build system includes graphics related code only in the UI build etc.

IT IS VERY IMPORTANT TO MAKE SURE CODE AND INCLUDES ARE CORRECTLY GUARDED FOR WASM BUILDS - WHICH ARE USED BY HOT RELOADING IDEs - EVEN IF THE USER ULTIMATELY BUILDS A NATIVE PLUGIN/APP.

## UI: WebView, no IGraphics

The plugin derives from `iplug::Plugin` and, is built with `WEBVIEW_EDITOR_DELEGATE` defined in order to swap in the right base class. It hosts a platform webview (WKWebView on macOS, WebView2 on Windows) that renders `resources/web/index.html`. Layout is CSS, controls are HTML custom elements. The webview also functions in the browser via the WASM target.

Key UI pieces in the C++ code (`TemplateProjectWebView.cpp` / `.h`), all gated behind `#ifdef IPLUG_EDITOR`:

- `mEditorInitFunc` runs when the editor opens. It calls `LoadIndexHtml(__FILE__, GetBundleID())` — which loads `resources/web/index.html` **from the source tree in debug builds and from the app bundle in release builds** — then `EnableScroll(false)`.
- `SetEnableDevTools(true)` is enabled in `DEBUG` builds: right-click → Inspect (macOS) opens Web Inspector against the live UI.

## DSP: C++

- `ProcessBlock` is plain DSP and is independent of the UI backend.

## The JS ↔ C++ message bridge

The webview and the plugin talk through a fixed set of bridge functions defined in `resources/web/script.js`. Do not rename them — iPlug2 calls them by name.

**Delegate → UI** (native calls these JS functions; you implement the `On*` handlers in `index.html`):

- `SPVFD(paramIdx, val)` — Set Parameter Value From Delegate → calls `OnParamChange(paramIdx, value)`. This is how host/automation parameter changes reach the UI.
- `SCVFD` / `SCMFD` — control value / control message from delegate.
- `SAMFD(msgTag, dataSize, msg)` — arbitrary message from delegate → calls `OnMessage(msgTag, dataSize, data)` (data is base64). The plugin pushes the parameter list as JSON this way once the page loads.
- `SMMFD` / `SSMFD` — MIDI / sysex from delegate.

**UI → Delegate** (your JS calls these; they marshal to `IPlugSendMsg` and surface on the C++ side):

- `SPVFUI(paramIdx, normValue)` — Set Parameter Value From UI. `normValue` is **normalized 0–1**. Call on every value change.
- `BPCFUI(paramIdx)` / `EPCFUI(paramIdx)` — Begin / End Parameter Change From UI. Wrap a drag gesture so the host records a single automation gesture and can undo it atomically.
- `SAMFUI(msgTag, ctrlTag = -1, data = 0)` — arbitrary message from UI → arrives at C++ `OnMessage(msgTag, ctrlTag, dataSize, pData)`.
- `SMMFUI` / `SSMFUI` — send MIDI / sysex from UI.

On the C++ side, override `OnMessage(int msgTag, int ctrlTag, int dataSize, const void* pData)` to receive `SAMFUI` calls. The template uses it for the editor-size buttons: `EMsgTags` in the header (`kMsgTagButtonSmall/Medium/Large`) maps to `Resize(...)` calls, with matching `kMsgTag*` constants at the top of `index.html` — the two lists must stay in sync, since the wire format is a bare int. Return `true` if you handled the message.

`OnMessage`'s resize block is guarded by `WEBVIEW_EDITOR_DELEGATE` rather than `IPLUG_EDITOR`, because `Resize()` comes from the webview delegate.

## Parameters

- Parameters are declared the usual iPlug2 way: add to `EParams` in the header and `GetParam(...)->InitDouble(...)` (etc.) in the constructor.
- The UI does **not** hard-code parameter ranges. After the page loads, the plugin sends the full parameter list as JSON via `SAMFD` (msgTag `-1`); `OnMessage` in `index.html` parses it and configures each `knob-control` (`min`, `max`, `label`, `default-value`) by matching its `param-id` attribute. So adding/retitling a parameter in C++ flows to the UI automatically — you only bind a control to a `param-id`.

## Web controls — custom elements

Controls are HTML Custom Elements (Web Components), each in its own module:

- `resources/web/knob-control.js` — `<knob-control param-id="0" label="Gain" units="%">`. On drag it calls `BPCFUI` (start), `SPVFUI` (each move, normalized), `EPCFUI` (end). Host-driven changes arrive via `updateValueFromHost(normalizedValue)`, dispatched from `OnParamChange`. `observedAttributes` includes `param-id`, `min`, `max`, `label`, `default-value`.
- `resources/web/button-control.js` — `<button-control>`, a styled shadow-DOM button. The template wires `onclick="SAMFUI(kMsgTagButton*)"` directly in `index.html` to trigger the resize messages.

### Don't echo host values back to the host

`updateValue()` in `knob-control.js` takes a `notifyHost` flag. Drag and wheel leave it at
its default of `true`; `updateValueFromHost()` passes `false`, so a host-originated change
redraws the knob without calling `SPVFUI`. Without that split, automation, preset recall and
initialisation all bounce back to the host as UI edits — and outside any `BPCFUI`/`EPCFUI`
gesture, so the host records parameter writes nobody asked for. Any new control needs the
same separation between "the user did this" and "the host told us this".

### Adding a new control — checklist

1. **C++:** add the parameter to `EParams` and `Init*` it in the constructor (for a parameter-bound control). For a non-parameter action, define a tag in `EMsgTags` and handle it in `OnMessage`.
2. **HTML:** add the element in `index.html` with its `param-id` (for a knob) or an `onclick`/event wiring (for a button/action).
3. **Bind to the host:** a parameter control must call `BPCFUI`→`SPVFUI`(normalized)→`EPCFUI` on user input, and implement an update path from `OnParamChange` (e.g. `updateValueFromHost`) so host automation moves it.
4. **Styling:** layout via CSS in the `index.html` `<style>` block / the component's shadow DOM. CSS custom properties on `:root` (`--accent`, `--surface`, `--knob-size`, …) are the theming surface — components read them with `var(..., fallback)`.

The common mistake mirrors the IGraphics one: wiring UI→host (`SPVFUI`) but forgetting the host→UI path (`OnParamChange` / `updateValueFromHost`), so the control moves the parameter but doesn't follow automation or preset recall.

## Files of interest

- `TemplateProjectWebView.cpp` / `.h` — plugin class, parameters (`EParams`), UI message tags (`EMsgTags`), `ProcessBlock`, `OnMessage`, and the `mEditorInitFunc` that loads the web UI.
- `resources/web/index.html` — the UI: markup, CSS, and the `OnParamChange` / `OnMessage` handlers the delegate calls.
- `resources/web/script.js` — the bridge function definitions (`S*FD` from delegate, `*FUI` to delegate). Treat as framework glue; extend rather than rename.
- `resources/web/knob-control.js`, `button-control.js` — example custom-element controls.
- `config.h` — plugin metadata, channel I/O, size constraints, format-specific IDs (`PLUG_UNIQUE_ID`, `PLUG_MFR_ID`, `AAX_TYPE_IDS`, etc.).
- `CMakeLists.txt` — the build. `WEB_RESOURCES` lists the files copied into the bundle (and watched for the WASM/JIT preview); `UI WEBVIEW` selects the webview editor delegate.
- `resources/` — Info.plists, icons, and the `web/` UI tree.
- `installer/`, `manual/` — packaging and docs tooling.
