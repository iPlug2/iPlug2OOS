---
name: build-cmake
description: Build an iPlug2 plugin project using CMake (Ninja or Xcode generator)
---

# Build iPlug2 Plugin with CMake

Use this skill when the user wants to build their plugin project using CMake.

## Workflow

1. **Identify the project:**
   - Look for `CMakeLists.txt` in project directories

2. **Choose a preset** based on platform and build requirements

## Using CMake Presets

The project uses CMake presets for standardized builds. Prefer `--preset` instead of manual `-G` flags. `CMakePresets.json` lives at the repository root, so run these commands from there; each project is selected by its build target (`[ProjectName]-app` etc.).

### List Available Presets

```bash
cmake --list-presets
```

### macOS Builds

```bash
# Configure with Ninja (fast builds)
cmake --preset macos-ninja

# Build
cmake --build build/macos-ninja --target [ProjectName]-app

# Or with Xcode (for debugging)
cmake --preset macos-xcode
cmake --build build/macos-xcode --config Release --target [ProjectName]-app

# Universal binary (arm64 + x86_64)
cmake --preset macos-xcode-universal
cmake --build build/macos-xcode-universal --config Release
```

### iOS Builds

```bash
# iOS Device
cmake --preset ios-xcode
cmake --build build/ios-xcode --config Release

# iOS Simulator
cmake --preset ios-sim-xcode
cmake --build build/ios-sim-xcode --config Release
```

For running in Simulator, use the `run-ios-simulator` skill.

### visionOS Builds

```bash
# visionOS Device
cmake --preset visionos-xcode
cmake --build build/visionos-xcode --config Release

# visionOS Simulator
cmake --preset visionos-sim-xcode
cmake --build build/visionos-sim-xcode --config Release
```

### Windows Builds

```bash
# Visual Studio 2022 (x64)
cmake --preset windows-vs2022
cmake --build build/windows-vs2022 --config Release

# ARM64EC
cmake --preset windows-vs2022-arm64ec
cmake --build build/windows-vs2022-arm64ec --config Release
```

### Linux Builds

Builds APP, VST3 and CLAP (X11, NanoVG/GL3, ALSA/JACK/PulseAudio). Install the development libraries first (Ubuntu/Debian):

```bash
sudo apt-get install -y \
  build-essential cmake ninja-build pkg-config \
  libfreetype-dev libfontconfig-dev \
  libx11-dev libx11-xcb-dev libxcb1-dev libxi-dev libxext-dev libxrender-dev \
  libxrandr-dev libxfixes-dev libxcursor-dev \
  libgl-dev libgtk-3-dev \
  libasound2-dev libjack-jackd2-dev libpulse-dev
```

```bash
# Configure with Ninja
cmake --preset linux-ninja

# Build
cmake --build build/linux-ninja --target [ProjectName]-app

# Or with Make
cmake --preset linux-make
cmake --build build/linux-make -- -j$(nproc)
```

Output in `build/linux-ninja/out/`: `[ProjectName]` (standalone executable), `[ProjectName].vst3/` and `[ProjectName].clap`. Resources (fonts, images) are staged next to the binaries in `[ProjectName].resources/` (APP), `[ProjectName].clap.resources/` (CLAP) and `Contents/Resources/` (VST3), and must be shipped with them.

### Web/Wasm Build (Emscripten)

```bash
# Configure (requires the Emscripten SDK environment: source emsdk_env.sh)
cmake --preset web

# Build the full web distribution (DSP + UI modules, HTML and scripts)
cmake --build build/web --target [ProjectName]-wasm-dist
```

Output in `build/web/out/[ProjectName]/` (`index.html`, `scripts/`, `styles/`). See `modules/iPlug2/Documentation/wasm.md` for serving it locally.

## Available Configure Presets

| Preset | Platform | Generator | Description |
|--------|----------|-----------|-------------|
| `macos-ninja` | macOS | Ninja | Fast command-line builds (NanoVG/Metal) |
| `macos-make` | macOS | Make | Unix Makefiles (NanoVG/Metal) |
| `macos-xcode` | macOS | Xcode | IDE builds with debugging |
| `macos-xcode-universal` | macOS | Xcode | Universal binary (arm64+x86_64) |
| `ios-xcode` | iOS | Xcode | iOS device builds |
| `ios-sim-xcode` | iOS | Xcode | iOS Simulator builds |
| `visionos-xcode` | visionOS | Xcode | visionOS device builds |
| `visionos-sim-xcode` | visionOS | Xcode | visionOS Simulator builds |
| `windows-ninja` | Windows | Ninja | Fast Windows command-line builds |
| `windows-vs2022` | Windows | VS2022 | Windows x64 builds |
| `windows-vs2022-arm64ec` | Windows | VS2022 | Windows ARM64EC builds |
| `linux-ninja` | Linux | Ninja | Fast Linux command-line builds (NanoVG/GL3) |
| `linux-make` | Linux | Make | Unix Makefiles (NanoVG/GL3) |
| `web` | Web | Ninja | Emscripten/WebAssembly builds |

## Available Targets

- `[ProjectName]-app` - Standalone application
- `[ProjectName]-vst3` - VST3 plugin
- `[ProjectName]-au` - Audio Unit (AUv2)
- `[ProjectName]-clap` - CLAP plugin
- `[ProjectName]AU-framework` - AUv3 framework
- `[ProjectName]AUv3-appex` - AUv3 app extension
- `[ProjectName]-ios-app` - iOS standalone app
- `[ProjectName]-wasm-dist` - Web distribution (Wasm DSP + UI, `web` preset only)

## Graphics Backend and Renderer

Default configuration uses NanoVG with Metal (macOS/iOS), GL2 (Windows) or GL3 (Linux).

To use Skia backend, add cache variables:

```bash
cmake --preset macos-ninja \
  -DIGRAPHICS_BACKEND=SKIA \
  -DIGRAPHICS_RENDERER=METAL
```

Valid combinations:
- **NanoVG**: GL2, GL3, METAL
- **Skia**: GL3, METAL, CPU
- **Linux**: NanoVG/GL3, Skia/GL3 or Skia/CPU only (Skia must be built locally with `modules/iPlug2/Dependencies/IGraphics/build-skia-linux.sh`)

**Note:** Skia requires prebuilt libraries:
```bash
./modules/iPlug2/Dependencies/download-prebuilt-libs.sh mac
```

## Build Locations (symlinked on macOS)

- APP: `~/Applications/[ProjectName].app`
- VST3: `~/Library/Audio/Plug-Ins/VST3/`
- AU: `~/Library/Audio/Plug-Ins/Components/`
- CLAP: `~/Library/Audio/Plug-Ins/CLAP/`

## Build Locations (symlinked on Linux)

- APP: stays in `build/linux-ninja/out/`
- VST3: `~/.vst3/`
- CLAP: `~/.clap/`

Pass `-DIPLUG_DEPLOY_PLUGINS=OFF` at configure time to skip deployment (any platform).

## Clean Build

```bash
# Remove build directory and reconfigure
rm -rf build/macos-ninja
cmake --preset macos-ninja
```

## Example

```bash
# Quick build of standalone app
cmake --preset macos-ninja
cmake --build build/macos-ninja --target MySynth-app

# Open the built app
open ~/Applications/MySynth.app

# Build for iOS Simulator
cmake --preset ios-sim-xcode
cmake --build build/ios-sim-xcode --config Release
```
