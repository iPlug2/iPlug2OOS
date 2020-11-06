# IPLUG2_ROOT should point to the top level IPLUG2 folder from the project folder
# By default, that is three directories up from /Examples/MyNewPlugin/config
IPLUG2_ROOT = ../../iPlug2

include ../../iPlug2/common-web.mk

SRC += $(PROJECT_ROOT)/MyNewPlugin.cpp

WAM_SRC += $(PROJECT_ROOT)/MidiSynth.cpp

# WAM_CFLAGS +=

WEB_CFLAGS += -DIGRAPHICS_NANOVG -DIGRAPHICS_GLES2

WAM_LDFLAGS += -O0 -s EXPORT_NAME="'AudioWorkletGlobalScope.WAM.MyNewPlugin'" -s ASSERTIONS=0

WEB_LDFLAGS += -O0 -s ASSERTIONS=0

WEB_LDFLAGS += $(NANOVG_LDFLAGS)
