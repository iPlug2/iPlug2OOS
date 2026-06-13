#pragma once

#include "IPlug_include_in_plug_hdr.h"

const int kNumPresets = 1;

enum EParams
{
  kParamGain = 0,
  kNumParams
};

// Tags for messages sent from the web UI to the plugin (see OnMessage).
enum EMsgTags
{
  kMsgTagTest = 0,
};

class TemplateProjectWebView final : public iplug::Plugin
{
public:
  TemplateProjectWebView(const iplug::InstanceInfo& info);

#if IPLUG_DSP // http://bit.ly/2S64BDd
  void ProcessBlock(iplug::sample** inputs, iplug::sample** outputs, int nFrames) override;
#endif

  // Messages posted from the web UI (IPlugSendMsg / SAMFUI) arrive here.
  bool OnMessage(int msgTag, int ctrlTag, int dataSize, const void* pData) override;
};
