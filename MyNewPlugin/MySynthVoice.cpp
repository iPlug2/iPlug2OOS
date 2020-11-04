  #include "MySynthVoice.h"
  
  void MySynthVoice::ProcessSamples(sample** inputs, 
                                    sample** outputs, 
                                    int nInputs, 
                                    int nOutputs, 
                                    int startIdx, 
                                    int nFrames, 
                                    double pitchBend)
  {
    for (auto s = startIdx; s < startIdx + nFrames; s++)
    {
      sample y = mEnv.Process(mSustainLevel) * mOsc.Process(midi2CPS(mBasePitch + pitchBend));
      
      outputs[0][s] += y; // accumulate the output of this voice 
    }
  }