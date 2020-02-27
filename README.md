This is an example of how to set up an iPlug2 project to build "out of source", which might be desirable to keep all your project dependencies synchronised with version control.

Instead of using the common-mac.xcconfig and common-win.xcconfig in the iPlug2 folder, it uses copies which have slight modifications for the different paths. This means the iPlug2 submodule itself does not have to be modified.

https://github.com/iPlug2/iPlug2/wiki/Out-of-source-builds
