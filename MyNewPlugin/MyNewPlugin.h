#pragma once

#include "IPlug_include_in_plug_hdr.h"

#if IPLUG_DSP
#include "MidiSynth.h"
#include "ISender.h"
#include "MySynthVoice.h"
#endif

const int kNumPresets = 1;
const int kNumVoices = 32;

enum EParams
{
  kParamGain = 0,
  kParamAmpAttack,
  kParamAmpDecay,
  kParamAmpSustain,
  kParamAmpRelease,
//  kParamFilterAttack,
//  kParamFilterDecay,
//  kParamFilterSustain,
//  kParamFilterRelease,
  kNumParams
};

enum ECtrlTags
{
  kCtrlTagKeyboard = 0,
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
  void OnParamChange(int paramIdx) override;
  MidiSynth mSynth;
  std::vector<MySynthVoice*> mVoices;
#endif
};
