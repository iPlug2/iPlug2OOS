// AudioWorklet polyfill
// Jari Kleimola 2017-20 (jari@webaudiomodules.org)
//
var AWGS = { processors:[] }

// --------------------------------------------------------------------------
//
//
AWGS.AudioWorkletGlobalScope = function () {
  var ctors = {}; // node name to processor definition map

  function registerOnWorker(name, ctor) {
    if (!ctors[name]) {
      ctors[name] = ctor;
      let descriptor = ctor.parameterDescriptors || {}
      postMessage({ type:"register", name:name, descriptor });
    }
    else {
      postMessage({ type:"state", node:nodeID, state:"error" });
      throw new Error("AlreadyRegistered");
    }
  };

  function constructOnWorker (name, port, options) {
    if (ctors[name]) {
      options = options || {}
      options._port = port;
      var processor = new ctors[name](options);
      if (!(processor instanceof AudioWorkletProcessor)) {
        postMessage({ type:"state", node:nodeID, state:"error" });
        throw new Error("InvalidStateError");
      }
      processor.inputChannelCount = options.inputChannelCount[0];
      return processor;
    }
    else {
      postMessage({ type:"state", node:nodeID, state:"error" });
      throw new Error("NotSupportedException");
    }
  }

  class AudioWorkletProcessorPolyfill {
    constructor (options) { this.port = options._port; }
    process (inputs, outputs, params) {}
  }

  return {
    'AudioWorkletProcessor': AudioWorkletProcessorPolyfill,
    'registerProcessor': registerOnWorker,
    '_createProcessor':  constructOnWorker
  }
}


AudioWorkletGlobalScope = AWGS.AudioWorkletGlobalScope();
AudioWorkletProcessor   = AudioWorkletGlobalScope.AudioWorkletProcessor;
registerProcessor = AudioWorkletGlobalScope.registerProcessor;
sampleRate = 44100;
hasSAB = true;
origin = "";

onmessage = function (e) {
  var msg = e.data;
  switch (msg.type) {

    case "init":
      sampleRate = AudioWorkletGlobalScope.sampleRate = msg.sampleRate;
      origin = msg.origin + "/";
      break;

    case "import":
      let url = msg.url.indexOf("http") == 0 ? msg.url : origin + msg.url;
      importScripts(url);
      postMessage({ type:"load", url:msg.url });
      break;

    case "createProcessor":
      // -- slice io to match with SPN bufferlength
      var a = msg.args;
      var slices = [];
      var buflen = a.options.buflenAWP;
      var numSlices = (a.options.buflenSPN / buflen)|0;

      hasSAB = a.hasSAB;
      if (hasSAB) {
        for (var i=0; i<numSlices; i++) {
          var sliceStart = i * buflen;
          var sliceEnd   = sliceStart + buflen;

          // -- create io buses
          function createBus (buffers) {
            var ports = [];
            for (var iport=0; iport<buffers.length; iport++) {
              var port = [];
              for (var channel=0; channel<buffers[iport].length; channel++) {
                var buf = new Float32Array(buffers[iport][channel]);
                port.push(buf.subarray(sliceStart, sliceEnd));
              }
              ports.push(port);
            }
            return ports;
          }
          var inbus  = createBus(a.audio.input);
          var outbus = createBus(a.audio.output);

          slices.push({ inbus:inbus, outbus:outbus });
        }
      }

      // -- create processor
      var processor = AudioWorkletGlobalScope._createProcessor(a.name, e.ports[0], a.options);
      processor.node = a.node;
      processor.id = AWGS.processors.length;
      processor.numSlices = numSlices;
      processor.buflen = buflen;
      AWGS.processors.push({ awp:processor, slices:slices });
      postMessage({ type:"state", node:a.node, processor:processor.id, state:"running" });
      break;

    case "process":
      var processor = AWGS.processors[msg.processor];
      if (processor) {
        if (hasSAB) {
          for (var i=0; i<processor.slices.length; i++) {
            var slice = processor.slices[i];
            processor.awp.process(slice.inbus, slice.outbus, []);
          }
        }
        else if (msg.buf[0].byteLength) {
          let inbufs  = [];
          let outbufs = [];
          let c;
          for (c = 0; c < processor.awp.inputChannelCount; c++)
            inbufs.push(new Float32Array(msg.buf[c]));
          for (; c < msg.buf.length; c++)
            outbufs.push(new Float32Array(msg.buf[c]));

          var n = 0;
          for (var i=0; i<processor.awp.numSlices; i++) {
            let ins  = [];
            let outs = [];
            for (let c = 0; c < inbufs.length; c++)
              ins.push(inbufs[c].subarray(n, n + processor.awp.buflen));
            for (let c = 0; c < outbufs.length; c++)
              outs.push(outbufs[c].subarray(n, n + processor.awp.buflen));
            processor.awp.process([ins], [outs], []);
            n += processor.awp.buflen;
          }
          postMessage({ buf:msg.buf, type:"process", node:processor.awp.node }, msg.buf);
        }
      }
      break;
  }
}
