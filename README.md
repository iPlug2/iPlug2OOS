![Build WAM](https://github.com/iPlug2/iPlug2OOS/workflows/Build%20WAM/badge.svg)

This repo contains an "out of source" iPlug2 template project, which is desirable when you need to keep all your project dependencies synchronised with version control and build it using CI/CD in the cloud. It set up for "containerized development" using [VSCode](https://code.visualstudio.com/docs/devcontainers/containers) and [github codespaces](https://github.com/features/codespaces).

Instead of using the common-mac.xcconfig and common-win.xcconfig in the iPlug2 folder, it uses copies of them at the top level of the iPlug2OOS repo. This means the iPlug2 submodule itself does not have to be modified.

https://github.com/iPlug2/iPlug2/wiki/Out-of-source-builds

Containerized development is documented [here](https://docs.google.com/document/d/e/2PACX-1vT6lYZ3vtYKWAty2g6DL994IO0_pfyGctDdKfPxF6MZwOgFWENfLuVtBW9J0-KzLsfPSKKN055UnAmj/pub)
