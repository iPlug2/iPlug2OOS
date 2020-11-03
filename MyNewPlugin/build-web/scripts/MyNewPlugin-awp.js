/* Declares the MyNewPlugin Audio Worklet Processor */

class MyNewPlugin_AWP extends AudioWorkletGlobalScope.WAMProcessor
{
  constructor(options) {
    options = options || {}
    options.mod = AudioWorkletGlobalScope.WAM.MyNewPlugin;
    super(options);
  }
}

registerProcessor("MyNewPlugin", MyNewPlugin_AWP);
