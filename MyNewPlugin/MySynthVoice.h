#pragma once

#include "MidiSynth.h"
#include "Oscillator.h"
#include "ADSREnvelope.h"

inline double midi2CPS(double pitch)
{
  return 440. * pow(2., (pitch - 69.) / 12.);
}

class MySynthVoice : public MidiSynth::Voice
{
public:
  void ProcessSamples(sample** inputs, sample** outputs, int nInputs, int nOutputs, int startIdx, int nFrames, double pitchBend) override
  {
    for (auto s = startIdx; s < startIdx + nFrames; s++)
    {
      outputs[0][s] += mEnv.Process(mSustainLevel) * mOsc.Process(midi2CPS(mKey + pitchBend));
      outputs[1][s] = outputs[0][s];
    }
  }
  
  void Trigger(double level, bool isRetrigger) override
  {
    mEnv.Start(level);
  }

  void Release() override
  {
    mEnv.Release();
  }
  
  bool GetBusy() const override
  {
    return mEnv.GetBusy();
  }
  
  bool GetReleased() const override
  {
    return mEnv.GetReleased();
  }
  
public:
  FastSinOscillator<sample> mOsc;
  ADSREnvelope<sample> mEnv;
  sample mSustainLevel = 0.;
};
