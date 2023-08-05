#include "TemplateProject.h"
#include "IPlug_include_in_plug_src.h"


TemplateProject::TemplateProject(const InstanceInfo& info)
: iplug::Plugin(info, MakeConfig(kNumParams, kNumPresets))
{
  GetParam(kParamGain)->InitDouble("Gain", 0., 0., 100.0, 0.01, "%");
  
#ifdef _DEBUG
  SetEnableDevTools(true);
#endif
  
  mEditorInitFunc = [&]() {
    LoadIndexHtml(__FILE__, GetBundleID());
    EnableScroll(false);
  };
}

void TemplateProject::ProcessBlock(sample** inputs, sample** outputs, int nFrames)
{ 
  const int nChans = NOutChansConnected();
  const double gain = GetParam(kParamGain)->Value() / 100.;
  
  for (int s = 0; s < nFrames; s++) {
    for (int c = 0; c < nChans; c++) {
      outputs[c][s] = inputs[c][s] * gain;
    }
  }
}

// This fires when the Web side sends a message
bool TemplateProject::OnMessage(int msgTag, int ctrlTag, int dataSize, const void* pData)
{
  DBGMSG("Msg received\n");
  return false;
}
