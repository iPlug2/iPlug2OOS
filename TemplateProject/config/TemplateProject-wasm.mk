# IPLUG2_ROOT should point to the top level IPLUG2 folder from the project folder
# In the iPlug2OOS layout that is two directories up from TemplateProject/config
IPLUG2_ROOT = ../../iPlug2

include ../../iPlug2/common-wasm.mk

SRC += $(PROJECT_ROOT)/TemplateProject.cpp

# DSP module flags
WASM_DSP_CFLAGS +=

WASM_DSP_LDFLAGS += -O3 -s ASSERTIONS=0

# UI module flags
WASM_UI_CFLAGS += -DIGRAPHICS_NANOVG -DIGRAPHICS_GLES2

WASM_UI_LDFLAGS += -O3 -s ASSERTIONS=0

WASM_UI_LDFLAGS += $(NANOVG_LDFLAGS)
