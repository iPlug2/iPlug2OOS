#include "MyNewPlugin.h"
#include "IPlug_include_in_plug_src.h"

#if IPLUG_EDITOR
#include "IControls.h"
#endif

#if IPLUG_DSP
#include "MySynthVoice.h"
#endif

MyNewPlugin::MyNewPlugin(const InstanceInfo& info)
: Plugin(info, MakeConfig(kNumParams, kNumPresets))
{
  GetParam(kGain)->InitDouble("Gain", 0., 0., 100.0, 0.01, "%");

#if IPLUG_DSP
  for (int i = 0; i < kNumVoices; i++) {
    mSynth.AddVoice(new MySynthVoice());
  }
#endif
  
#if IPLUG_EDITOR // http://bit.ly/2S64BDd
  mMakeGraphicsFunc = [&]() {
    return MakeGraphics(*this, PLUG_WIDTH, PLUG_HEIGHT, PLUG_FPS, GetScaleForScreen(PLUG_HEIGHT));
  };
  
  mLayoutFunc = [&](IGraphics* pGraphics) {
    pGraphics->AttachCornerResizer(EUIResizerMode::Scale, false);
    pGraphics->AttachPanelBackground(COLOR_GRAY);
    pGraphics->LoadFont("Roboto-Regular", ROBOTO_FN);
    IRECT controlsArea = pGraphics->GetBounds();
    const IRECT keyboardArea = controlsArea.ReduceFromBottom(100);
    pGraphics->AttachControl(new IVKnobControl(controlsArea.GetCentredInside(100), kGain));
    pGraphics->AttachControl(new IVKeyboardControl(keyboardArea));
  };
#endif
}

#if IPLUG_DSP
void MyNewPlugin::ProcessBlock(sample** inputs, sample** outputs, int nFrames)
{
  const double gain = GetParam(kGain)->Value() / 100.;
  const int nChans = NOutChansConnected();

  mSynth.ProcessBlock(inputs, outputs, 0, 2, nFrames);
  
  for (int s = 0; s < nFrames; s++) {
    for (int c = 0; c < nChans; c++) {
      outputs[c][s] *= gain;
    }
  }
}

void MyNewPlugin::ProcessMidiMsg(const IMidiMsg& msg)
{
  mSynth.AddMidiMsgToQueue(msg);
}

void MyNewPlugin::OnReset()
{
  mSynth.SetSampleRateAndBlockSize(GetSampleRate(), GetBlockSize());
}

#endif
