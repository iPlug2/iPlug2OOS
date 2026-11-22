[![Build Wasm](https://github.com/iPlug2/iPlug2OOS/actions/workflows/build-wasm.yml/badge.svg)](https://github.com/iPlug2/iPlug2OOS/actions/workflows/build-wasm.yml)

This repo contains an "out of source" iPlug2 template project, which is desirable when you need to keep all your project dependencies synchronised with version control and build it using CI/CD in the cloud. It set up for "containerized development" using [VSCode](https://code.visualstudio.com/docs/devcontainers/containers) and [github codespaces](https://github.com/features/codespaces).

Instead of using the common-mac.xcconfig and common-win.xcconfig in the iPlug2 folder, it uses copies of them at the top level of the iPlug2OOS repo. This means the iPlug2 submodule itself does not have to be modified.

https://github.com/iPlug2/iPlug2/wiki/Out-of-source-builds

The iPlug2 submodule lives at `modules/iPlug2`. If you cloned the repo before it moved there from `iPlug2/`, run this after pulling:

```bash
git submodule sync && git submodule update --init
```

You can then delete the old top-level `iPlug2/` folder.

Containerized development is documented [here](https://docs.google.com/document/d/e/2PACX-1vT6lYZ3vtYKWAty2g6DL994IO0_pfyGctDdKfPxF6MZwOgFWENfLuVtBW9J0-KzLsfPSKKN055UnAmj/pub)

## CMake

The template can also be built with CMake on macOS, Windows, Linux and the web, using the presets in `CMakePresets.json` (`cmake --list-presets`).

### Linux

Linux builds (standalone app, VST3 and CLAP) are CMake-only. On Ubuntu/Debian:

```bash
sudo apt-get install -y \
  build-essential cmake ninja-build pkg-config \
  libfreetype-dev libfontconfig-dev \
  libx11-dev libx11-xcb-dev libxcb1-dev libxi-dev libxext-dev libxrender-dev \
  libxrandr-dev libxfixes-dev libxcursor-dev \
  libgl-dev libgtk-3-dev \
  libasound2-dev libjack-jackd2-dev libpulse-dev

(cd modules/iPlug2/Dependencies/IPlug && ./download-iplug-sdks.sh)

cmake --preset linux-ninja
cmake --build --preset linux-ninja
```

Binaries are written to `build/linux-ninja/out/`; the VST3 and CLAP are symlinked into `~/.vst3` and `~/.clap` (disable with `-DIPLUG_DEPLOY_PLUGINS=OFF`). CMake 3.25 or later is required.

`TemplateProject/scripts/makedist-linux.sh` builds a release and packages it as a `.tar.gz` in `TemplateProject/build-linux/out/`; the Release Native workflow runs it and attaches the archive to the GitHub release.
