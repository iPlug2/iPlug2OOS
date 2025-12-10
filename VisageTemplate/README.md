# VisageTemplate

iPlug2 template project using Visage UI library instead of IGraphics.

## Building

This project supports two build approaches:

### Option 1: CMake (Recommended)

Build everything with CMake - this automatically downloads and builds Visage and its dependencies.

```bash
# Configure
cmake -S . -B build-cmake -G "Visual Studio 17 2022" -A x64  # Windows
cmake -S . -B build-cmake -G Xcode                           # macOS

# Build
cmake --build build-cmake --config Release
```

### Option 2: Visual Studio / Xcode (Traditional iPlug2 workflow)

Use the native IDE projects but requires pre-building Visage static libraries via CMake first.

#### Step 1: Build Visage static libraries

```bash
# Configure CMake
cmake -S . -B build-cmake -G "Visual Studio 17 2022" -A x64  # Windows
cmake -S . -B build-cmake -G Xcode                           # macOS

# Build Visage libraries only
cmake --build build-cmake --target visage-libs --config Release
cmake --build build-cmake --target visage-libs --config Debug
```

This outputs static libraries to:
- `build-cmake/visage-libs/Release/`
- `build-cmake/visage-libs/Debug/`

#### Step 2: Build with IDE

- **Windows**: Open `VisageTemplate.sln` in Visual Studio
- **macOS**: Open `VisageTemplate.xcworkspace` in Xcode

The project configs are already set up to link against the Visage libraries from `build-cmake/visage-libs/`.

## Visage Libraries

The `visage-libs` CMake target builds and collects these static libraries:

| Library | Description |
|---------|-------------|
| `visage.lib` | Main Visage UI library |
| `VisageEmbeddedFonts.lib` | Embedded font resources |
| `VisageEmbeddedIcons.lib` | Embedded icon resources |
| `VisageEmbeddedShaders.lib` | Compiled bgfx shaders |
| `bgfx.lib` | Graphics abstraction layer |
| `bimg.lib` | Image loading/processing |
| `bimg_decode.lib` | Image decoding |
| `bimg_encode.lib` | Image encoding |
| `bx.lib` | Base library utilities |
| `freetype.lib` | Font rendering |

## System Dependencies

### macOS
Required frameworks (automatically linked via xcconfig):
- Metal, MetalKit
- Cocoa, QuartzCore
- IOKit, CoreFoundation

### Windows
Standard Windows libraries (automatically linked via props):
- wininet.lib, comctl32.lib, Shlwapi.lib
