/* Declares the TemplateProject Audio Worklet Processor */

class TemplateProject_AWP extends AudioWorkletGlobalScope.WAMProcessor
{
  constructor(options) {
    options = options || {}
    options.mod = AudioWorkletGlobalScope.WAM.TemplateProject;
    super(options);
  }
}

registerProcessor("TemplateProject", TemplateProject_AWP);
