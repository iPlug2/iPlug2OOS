# TemplateProjectReaperExtensionWebView readme

A **REAPER extension** with a **WebView UI**, rather than an audio plugin. It loads into REAPER
itself, registers actions, and opens a dockable window whose UI is authored in HTML/CSS/JS under
`resources/web/` (entry point `index.html`).

macOS and Windows only. Build with CMake:

```bash
cmake -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug
cmake --build build
```

`IPLUG_DEPLOY_PLUGINS` defaults to `ON`, so the build copies
`reaper_TemplateProjectReaperExtensionWebView.dylib`/`.dll` into REAPER's `UserPlugins` directory.
Restart REAPER and look under Extensions. Build `Debug` while developing: that is what enables
loading the web UI from the source tree and the devtools inspector.
