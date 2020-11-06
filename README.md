This is an example of how to set up an iPlug2 project to build "out of source", which might be desirable to keep all your project dependencies synchronised with version control. It is also set up for "containerized development" using VSCode and github codespaces.

Instead of using the common-mac.xcconfig and common-win.xcconfig in the iPlug2 folder, it uses copies. This means the iPlug2 submodule itself does not have to be modified.

https://github.com/iPlug2/iPlug2/wiki/Out-of-source-builds

Containerized development is documented [here](https://docs.google.com/document/d/e/2PACX-1vT6lYZ3vtYKWAty2g6DL994IO0_pfyGctDdKfPxF6MZwOgFWENfLuVtBW9J0-KzLsfPSKKN055UnAmj/pub).

In order to set up this repo, you need to initialize the submodule, and download the plug-in SDKs... 

```
cd iPlug2OOS
git submodule init
git submodule update
cd iPlug2/Dependencies/IPlug
./download-iplug-sdks.sh
```
