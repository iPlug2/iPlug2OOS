#pragma once

#include "IPlug_include_in_plug_hdr.h"

#if IPLUG_DSP
#include "MidiSynth.h"
#endif

const int kNumPresets = 1;
const int kNumVoices = 32;

enum EParams
{
  kGain = 0,
  kNumParams
};

using namespace iplug;
using namespace igraphics;

class MyNewPlugin final : public Plugin
{
public:
  MyNewPlugin(const InstanceInfo& info);

#if IPLUG_DSP // http://bit.ly/2S64BDd
  void ProcessBlock(sample** inputs, sample** outputs, int nFrames) override;
  void ProcessMidiMsg(const IMidiMsg& msg) override;
  void OnReset() override;
  MidiSynth mSynth;
#endif
};
