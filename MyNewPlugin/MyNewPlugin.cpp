#include "MyNewPlugin.h"
#include "IPlug_include_in_plug_src.h"

#if IPLUG_EDITOR
#include "IControls.h"
#endif

MyNewPlugin::MyNewPlugin(const InstanceInfo& info)
: Plugin(info, MakeConfig(kNumParams, kNumPresets))
{
  GetParam(kParamGain)->InitDouble("Gain", 0., 0., 100.0, 0.01, "%"); // TASK_04
  GetParam(kParamAmpAttack)->InitDouble("Attack", 10., 1., 1000., 0.1, "ms", IParam::kFlagsNone, "ADSR", IParam::ShapePowCurve(3.));
  GetParam(kParamAmpDecay)->InitDouble("Decay", 10., 1., 1000., 0.1, "ms", IParam::kFlagsNone, "ADSR", IParam::ShapePowCurve(3.));
  GetParam(kParamAmpSustain)->InitDouble("Sustain", 50., 0., 100., 1, "%", IParam::kFlagsNone, "ADSR");
  GetParam(kParamAmpRelease)->InitDouble("Release", 10., 2., 1000., 0.1, "ms", IParam::kFlagsNone, "ADSR");

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
    
    /* SETUP */
    
    pGraphics->AttachCornerResizer(EUIResizerMode::Scale, false);
    pGraphics->AttachTextEntryControl();
    
    /* RESOURCE LOADING */
    
    pGraphics->LoadFont("Roboto-Regular", ROBOTO_FN);
    pGraphics->LoadFont("Logo", LOGO_FONT_FN);
//    auto knobSVG = pGraphics->LoadSVG(BEFACO_TINYKNOB_FN); /* TASK_02 */
    auto sliderPotSVG = pGraphics->LoadSVG(BEFACO_SLIDEPOT_FN);
    auto sliderHandleSVG = pGraphics->LoadSVG(BEFACO_SLIDEPOTHANDLE_FN);

    /* DIVIDE UP BOUNDS FOR LAYOUT */

    const IRECT bounds = pGraphics->GetBounds();
    const IRECT keyboardArea = bounds.GetFromBottom(100);
    const IRECT controlsArea = bounds.GetReducedFromBottom(100).GetPadded(-10);
    const IRECT column1 = controlsArea.GetGridCell(0, 1, 3).GetPadded(-10);
    const IRECT column2 = controlsArea.GetGridCell(1, 1, 3).GetPadded(-10);
    const IRECT column3 = controlsArea.GetGridCell(2, 1, 3).GetPadded(-10);
    const IRECT masterArea = column3.FracRectVertical(0.75, true);
    const IRECT logoArea = column3.FracRectVertical(0.25, false);
    const IRECT ampEG = column2.FracRectVertical(0.5, true);
    const IRECT ampEGLabelsArea = ampEG.GetGridCell(0, 3, 1);
    const IRECT ampEGSlidersArea = ampEG.GetGridCell(1, 3, 1);
    const IRECT ampEGValuesArea = ampEG.GetGridCell(2, 3, 1);
    
    /* ADD CONTROLS */
    
    // Background control, either a fixed color, gradient, svg or bitmap
    pGraphics->AttachPanelBackground(COLOR_LIGHT_GRAY); /* TASK_01 */
//    pGraphics->AttachPanelBackground(IPattern::CreateLinearGradient(bounds, EDirection::Vertical, {{COLOR_LIGHT_GRAY, 0.}, {COLOR_DARK_GRAY, 1.}}));
     
    // Group controls (background labels)
    pGraphics->AttachControl(new IVGroupControl(controlsArea, " ", 0.f));
    pGraphics->AttachControl(new IVGroupControl(column1.GetPadded(0, 0., 5., 0.), "OSCILLATORS"));
    pGraphics->AttachControl(new IVGroupControl(column2.GetPadded(5., 0., 5., 0.), "ENVELOPES"));
    pGraphics->AttachControl(new IVGroupControl(masterArea.GetPadded(5., 0., 0., 0.), "MASTER"));
    WDL_String versionStr, buildDateStr;
    GetPluginVersionStr(versionStr);
    buildDateStr.SetFormatted(100, "%s %s %s, built on %s at %.5s ", versionStr.Get(), GetArchStr(), GetAPIStr(), __DATE__, __TIME__);
    pGraphics->AttachControl(new ITextControl(bounds.GetFromTRHC(300, 20), buildDateStr.Get()));

    // Oscillator controls
    
    // Envelope controls
    pGraphics->AttachControl(new ITextControl(ampEGLabelsArea.GetGridCell(0, 1, 4).GetFromBottom(20.f), "Attack"));
    pGraphics->AttachControl(new ITextControl(ampEGLabelsArea.GetGridCell(1, 1, 4).GetFromBottom(20.f), "Decay"));
    pGraphics->AttachControl(new ITextControl(ampEGLabelsArea.GetGridCell(2, 1, 4).GetFromBottom(20.f), "Sustain"));
    pGraphics->AttachControl(new ITextControl(ampEGLabelsArea.GetGridCell(3, 1, 4).GetFromBottom(20.f), "Release"));
    
    pGraphics->AttachControl(new ISVGSliderControl(ampEGSlidersArea.GetGridCell(0, 1, 4), sliderHandleSVG, sliderPotSVG, kParamAmpAttack));
    pGraphics->AttachControl(new ISVGSliderControl(ampEGSlidersArea.GetGridCell(1, 1, 4), sliderHandleSVG, sliderPotSVG, kParamAmpDecay));
    pGraphics->AttachControl(new ISVGSliderControl(ampEGSlidersArea.GetGridCell(2, 1, 4), sliderHandleSVG, sliderPotSVG, kParamAmpSustain));
    pGraphics->AttachControl(new ISVGSliderControl(ampEGSlidersArea.GetGridCell(3, 1, 4), sliderHandleSVG, sliderPotSVG, kParamAmpRelease));
    
    pGraphics->AttachControl(new ICaptionControl(ampEGValuesArea.GetGridCell(0, 1, 4).GetFromTop(20.f), kParamAmpAttack));
    pGraphics->AttachControl(new ICaptionControl(ampEGValuesArea.GetGridCell(1, 1, 4).GetFromTop(20.f), kParamAmpDecay));
    pGraphics->AttachControl(new ICaptionControl(ampEGValuesArea.GetGridCell(2, 1, 4).GetFromTop(20.f), kParamAmpSustain));
    pGraphics->AttachControl(new ICaptionControl(ampEGValuesArea.GetGridCell(3, 1, 4).GetFromTop(20.f), kParamAmpRelease));
    
    // Master controls

    /* TASK_03 -- insert some code here! */
    
//    pGraphics->AttachControl(new ISVGKnobControl(masterArea.GetCentredInside(100), knobSVG, kParamGain)); /* TASK_02 */
    
    // Keyboard
    pGraphics->AttachControl(new IVKeyboardControl(keyboardArea, 36, 64), kCtrlTagKeyboard);

    pGraphics->AttachControl(new IVLabelControl(logoArea, "MyNewPlugin", DEFAULT_STYLE.WithDrawFrame(false).WithValueText(IText(50., "Logo"))));
    
    pGraphics->SetQwertyMidiKeyHandlerFunc([pGraphics](const IMidiMsg& msg) { pGraphics->GetControlWithTag(kCtrlTagKeyboard)->As<IVKeyboardControl>()->SetNoteFromMidi(msg.NoteNumber(), msg.StatusMsg() == IMidiMsg::kNoteOn); });
  };
#endif
}

#if IPLUG_DSP
void MyNewPlugin::ProcessBlock(sample** inputs, sample** outputs, int nFrames)
{
  mSynth.ProcessBlock(inputs, outputs, 0, 1, nFrames);

  /* TASK_02 */
  /*
  const double gain = GetParam(kParamGain)->Value() / 100.; // TASK_04
 
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
  case kParamAmpAttack:  for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kAttack,  value) ; } break;
  case kParamAmpDecay:   for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kDecay,   value); } break;
  case kParamAmpSustain: for(auto* voice : mVoices) { voice->mSustainLevel = value / 100.0; } break;
  case kParamAmpRelease: for(auto* voice : mVoices) { voice->mEnv.SetStageTime(ADSREnvelope<sample>::EStage::kRelease, value); } break;
  default:
    break;
  }
}

#endif
