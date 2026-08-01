// A REAPER extension needs far fewer of these than a plugin does: there is no host to
// declare formats, channel I/O or parameters to. PLUG_CLASS_NAME names the class and the
// reaper_<name> binary; PLUG_WIDTH/HEIGHT size the extension window.

#define PLUG_NAME "TemplateProjectReaperExtensionWebView"
#define PLUG_MFR "AcmeInc"
#define PLUG_VERSION_HEX 0x00000000
#define PLUG_VERSION_STR "0.0.0"
#define PLUG_COPYRIGHT_STR "Copyright 2026 Acme Inc"
#define PLUG_CLASS_NAME TemplateProjectReaperExtensionWebView

#define PLUG_WIDTH 300
#define PLUG_HEIGHT 300
#define PLUG_FPS 60
#define PLUG_SHARED_RESOURCES 0

#define SHARED_RESOURCES_SUBPATH "TemplateProjectReaperExtensionWebView"
