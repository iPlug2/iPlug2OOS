#include "MyNewPlugin.h"
#include "IPlug_include_in_plug_src.h"

#if IPLUG_EDITOR
#include "IControls.h"
#endif

MyNewPlugin::MyNewPlugin(const InstanceInfo& info)
: Plugin(info, MakeConfig(kNumParams, kNumPresets))
{
  GetParam(kGain)->InitDouble("Gain", 0., 0., 100.0, 0.01, "%");
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
    pGraphics->AttachPanelBackground(COLOR_ORANGE);
    auto smileyBitmap = pGraphics->LoadBitmap(SMILEY_FN);
    pGraphics->LoadFont("Roboto-Regular", ROBOTO_FN);
    IRECT controlsArea = pGraphics->GetBounds();
    const IRECT keyboardArea = controlsArea.ReduceFromBottom(100);
    pGraphics->AttachControl(new IBitmapControl(controlsArea.GetFromTRHC(50,50), smileyBitmap));
    pGraphics->AttachControl(new IVKnobControl(controlsArea.GetGridCell(0,4,4), kGain));
    pGraphics->AttachControl(new IVMultiSliderControl<4>(controlsArea.GetGridCell(1,4,4), "Env", DEFAULT_STYLE, kParamAttack, 0, EDirection::Horizontal));
    pGraphics->AttachControl(new IVKeyboardControl(keyboardArea), kCtrlTagKeyboard);
    pGraphics->AttachTextEntryControl();
    pGraphics->AttachControl(new IVScopeControl<1>(controlsArea.GetGridCell(2,4,4)), kCtrlTagScope);
    pGraphics->SetQwertyMidiKeyHandlerFunc([pGraphics](const IMidiMsg& msg) { pGraphics->GetControlWithTag(kCtrlTagKeyboard)->As<IVKeyboardControl>()->SetNoteFromMidi(msg.NoteNumber(), msg.StatusMsg() == IMidiMsg::kNoteOn); });
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

  mScopeSender.ProcessBlock(outputs, nFrames, kCtrlTagScope);
}

void MyNewPlugin::ProcessMidiMsg(const IMidiMsg& msg)
{
  mSynth.AddMidiMsgToQueue(msg);
}

void MyNewPlugin::OnReset()
{
  mSynth.SetSampleRateAndBlockSize(GetSampleRate(), GetBlockSize());
}

void MyNewPlugin::OnIdle()
{
  mScopeSender.TransmitData(*this);
}

void MyNewPlugin::OnParamChange(int paramIdx)
{
  auto value = GetParam(paramIdx)->Value();
  switch (paramIdx)
  {
  case kParamAttack:  for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kAttack,  value) ; } break;
  case kParamDecay:   for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kDecay,   value); } break;
  case kParamSustain: for(auto* voice : mVoices) { voice->mSustainLevel = value / 100.0; } break;
  case kParamRelease: for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kRelease, value); } break;

  default:
    break;
  }
}

#endif
