#include "TemplateProjectWebView.h"
#include "IPlug_include_in_plug_src.h"
#include <iostream>

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
#ifdef IPLUG_EDITOR
  auto DoTest = []() {
    std::cout << "Test message received from web UI!" << std::endl;
  };

  switch (msgTag) {
    case kMsgTagTest:  DoTest();  return true;
    default: break;
  }
#endif
  return false;
}
