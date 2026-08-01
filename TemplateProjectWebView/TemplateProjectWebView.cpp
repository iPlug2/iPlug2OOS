#include "TemplateProjectWebView.h"
#include "IPlug_include_in_plug_src.h"

using namespace iplug;

TemplateProjectWebView::TemplateProjectWebView(const InstanceInfo& info)
: iplug::Plugin(info, MakeConfig(kNumParams, kNumPresets))
{
  GetParam(kParamGain)->InitDouble("Gain", 100., 0., 100.0, 0.01, "%");

#ifdef IPLUG_EDITOR
#ifdef DEBUG
  SetEnableDevTools(true);
#endif

  // The web UI lives in resources/web/. LoadIndexHtml() loads index.html from
  // the source tree in debug builds and from the bundle in release builds.
  mEditorInitFunc = [&]() {
    LoadIndexHtml(__FILE__, GetBundleID());
    EnableScroll(false);
  };
#endif
}

#if IPLUG_DSP
void TemplateProjectWebView::ProcessBlock(sample** inputs, sample** outputs, int nFrames)
{
  const int nChans = NOutChansConnected();
  const double gain = GetParam(kParamGain)->Value() / 100.;

  for (int s = 0; s < nFrames; s++) {
    for (int c = 0; c < nChans; c++) {
      outputs[c][s] = inputs[c][s] * gain;
    }
  }
}
#endif

bool TemplateProjectWebView::OnMessage(int msgTag, int ctrlTag, int dataSize, const void* pData)
{
// Resize() lives on the WebView editor delegate, so this is guarded more tightly than
// IPLUG_EDITOR. The sizes stay within PLUG_MIN_/PLUG_MAX_ in config.h and keep the 4:3
// aspect of the default editor size.
#ifdef WEBVIEW_EDITOR_DELEGATE
  switch (msgTag) {
    case kMsgTagButtonSmall:   Resize(512, 384);   return true;
    case kMsgTagButtonMedium:  Resize(1024, 768);  return true;
    case kMsgTagButtonLarge:   Resize(1536, 1152); return true;
    default: break;
  }
#endif
  return false;
}
