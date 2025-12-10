#pragma once

#include "IPlug_include_in_plug_hdr.h"

const int kNumPresets = 1;

enum EParams
{
  kParamGain = 0,
  kNumParams
};

class VisageTemplate final : public iplug::Plugin
{
public:
  VisageTemplate(const iplug::InstanceInfo& info);

  void ProcessBlock(iplug::sample** inputs, iplug::sample** outputs, int nFrames) override;

#ifndef CLI_API
protected:
  // VisageEditorDelegate overrides
  void OnDraw(visage::Canvas& canvas) override;
  void OnMouseDown(const visage::MouseEvent& e) override;
  void OnMouseDrag(const visage::MouseEvent& e) override;
  void OnMouseUp(const visage::MouseEvent& e) override;
  void OnParamChangeUI(int paramIdx, iplug::EParamSource source) override;

private:
  bool mDragging = false;
  float mLastY = 0.f;
#endif
};
