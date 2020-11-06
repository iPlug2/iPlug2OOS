#include "MyNewPlugin.h"
#include "IPlug_include_in_plug_src.h"

#if IPLUG_EDITOR
#include "IControls.h"
#endif

MyNewPlugin::MyNewPlugin(const InstanceInfo& info)
: Plugin(info, MakeConfig(kNumParams, kNumPresets))
{
  GetParam(kParamGain)->InitDouble("Gain", 0., 0., 100.0, 0.01, "%");
  GetParam(kParamAttack)->InitDouble("Attack", 10., 1., 1000., 0.1, "ms", IParam::kFlagsNone, "ADSR", IParam::ShapePowCurve(3.));
  GetParam(kParamDecay)->InitDouble("Decay", 10., 1., 1000., 0.1, "ms", IParam::kFlagsNone, "ADSR", IParam::ShapePowCurve(3.));
  GetParam(kParamSustain)->InitDouble("Sustain", 50., 0., 100., 1, "%", IParam::kFlagsNone, "ADSR");
  GetParam(kParamRelease)->InitDouble("Release", 10., 2., 1000., 0.1, "ms", IParam::kFlagsNone, "ADSR");

#if IPLUG_DSP
  for (int i = 0; i < kNumVoices; i++) {
    auto* newVoice = new MySynthVoice();
    mVoices.push_back(newVoice);
    mSynth.AddVoice(newVoice); // takes ownership
  }
#endif
  
#if IPLUG_EDITOR // http://bit.ly/2S64BDd
  mMakeGraphicsFunc = [&]() {
    return MakeGraphics(*this, PLUG_WIDTH, PLUG_HEIGHT, PLUG_FPS, GetScaleForScreen(PLUG_HEIGHT));
  };
  
  mLayoutFunc = [&](IGraphics* pGraphics) {
    pGraphics->AttachCornerResizer(EUIResizerMode::Scale, false);
    pGraphics->AttachTextEntryControl();
    pGraphics->LoadFont("Roboto-Regular", ROBOTO_FN);
    const IRECT bounds = pGraphics->GetBounds();
    const IRECT keyboardArea = bounds.GetFromBottom(100);
    IRECT controlsArea = bounds.GetReducedFromBottom(100).GetPadded(-10);
    
    pGraphics->AttachPanelBackground(COLOR_LIGHT_GRAY);
    pGraphics->AttachControl(new IVGroupControl(controlsArea, "Controls"));
    // pGraphics->AttachControl(new IVKnobControl(controlsArea.GetGridCell(0,4,4), kParamGain));
    // pGraphics->AttachControl(new IVMultiSliderControl<4>(controlsArea.GetGridCell(1,4,4), "Env", DEFAULT_STYLE, kParamAttack, 0, EDirection::Vertical));
    pGraphics->AttachControl(new IVKeyboardControl(keyboardArea, 36, 64), kCtrlTagKeyboard);

    WDL_String versionStr;
    GetPluginVersionStr(versionStr);
    WDL_String buildDateStr;
    buildDateStr.SetFormatted(100, "Version %s %s %s, built on %s at %.5s ", versionStr.Get(), GetArchStr(), GetAPIStr(), __DATE__, __TIME__);
    pGraphics->AttachControl(new ITextControl(bounds.GetFromTRHC(300, 12), buildDateStr.Get()));

    pGraphics->SetQwertyMidiKeyHandlerFunc([pGraphics](const IMidiMsg& msg) { pGraphics->GetControlWithTag(kCtrlTagKeyboard)->As<IVKeyboardControl>()->SetNoteFromMidi(msg.NoteNumber(), msg.StatusMsg() == IMidiMsg::kNoteOn); });
  };
#endif
}

#if IPLUG_DSP
void MyNewPlugin::ProcessBlock(sample** inputs, sample** outputs, int nFrames)
{
  mSynth.ProcessBlock(inputs, outputs, 0, 1, nFrames);

  /*
  const double gain = GetParam(kParamGain)->Value() / 100.;
 
  for (int s = 0; s < nFrames; s++)
  {
    outputs[0][s] *= gain;
  }
  */

  // copy left hand channel audio to right hand channel
  memcpy(outputs[1], outputs[0], nFrames * sizeof(sample));
}

void MyNewPlugin::ProcessMidiMsg(const IMidiMsg& msg)
{
  mSynth.AddMidiMsgToQueue(msg);
}

void MyNewPlugin::OnReset()
{
  mSynth.SetSampleRateAndBlockSize(GetSampleRate(), GetBlockSize());
}

void MyNewPlugin::OnParamChange(int paramIdx)
{
  auto value = GetParam(paramIdx)->Value();
  switch (paramIdx) {
  case kParamAttack:  for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kAttack,  value) ; } break;
  case kParamDecay:   for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kDecay,   value); } break;
  case kParamSustain: for(auto* voice : mVoices) { voice->mSustainLevel = value / 100.0; } break;
  case kParamRelease: for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kRelease, value); } break;
  default:
    break;
  }
}

#endif
