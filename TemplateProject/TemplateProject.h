#pragma once

#include "IPlug_include_in_plug_hdr.h"

const int kNumPresets = 1;

enum EParams
{
  kParamGain = 0,
  kNumParams
};

using namespace iplug;

class TemplateProject final : public Plugin
{
public:
  TemplateProject(const InstanceInfo& info);

  bool OnHostRequestingSupportedViewConfiguration(int width, int height) override { return true; }
  
  void ProcessBlock(sample** inputs, sample** outputs, int nFrames) override;
  
  bool OnMessage(int msgTag, int ctrlTag, int dataSize, const void* pData) override;
};
