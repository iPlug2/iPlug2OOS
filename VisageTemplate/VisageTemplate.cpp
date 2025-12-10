#include "VisageTemplate.h"
#include "IPlug_include_in_plug_src.h"
#include <cmath>

#ifndef CLI_API
static constexpr float kPi = 3.14159265358979323846f;
static constexpr float kTwoPi = 2.f * kPi;
#endif

using namespace iplug;

VisageTemplate::VisageTemplate(const InstanceInfo& info)
: iplug::Plugin(info, MakeConfig(kNumParams, kNumPresets))
{
  GetParam(kParamGain)->InitDouble("Gain", 50., 0., 100.0, 0.01, "%");
}

#ifndef CLI_API
void VisageTemplate::OnDraw(visage::Canvas& canvas)
{
  auto* editor = GetEditor();
  if (!editor)
    return;

  float w = editor->width();
  float h = editor->height();
  double time = canvas.time();
  float gain = GetParam(kParamGain)->Value() / 100.f;

  // Animated gradient background
  float hueShift = std::fmod(time * 0.1f, 1.f);
  visage::Gradient bgGradient = visage::Gradient::fromSampleFunction(64, [hueShift](float t) {
    float hue = std::fmod(t * 0.5f + hueShift, 1.f);
    // HSV to RGB (S=0.3, V=0.15 for subtle dark gradient)
    float c = 0.15f * 0.3f;
    float x = c * (1.f - std::abs(std::fmod(hue * 6.f, 2.f) - 1.f));
    float m = 0.15f - c;
    float r, g, b;
    int hi = static_cast<int>(hue * 6.f) % 6;
    switch (hi) {
      case 0: r = c; g = x; b = 0; break;
      case 1: r = x; g = c; b = 0; break;
      case 2: r = 0; g = c; b = x; break;
      case 3: r = 0; g = x; b = c; break;
      case 4: r = x; g = 0; b = c; break;
      default: r = c; g = 0; b = x; break;
    }
    return visage::Color(1.f, r + m, g + m, b + m);
  });

  visage::Brush bgBrush = visage::Brush::linear(bgGradient, {0, 0}, {w, h});
  canvas.setColor(bgBrush);
  canvas.fill(0, 0, w, h);

  // Draw animated waveform
  float waveY = h * 0.3f;
  float waveH = h * 0.15f;
  int numPoints = 120;

  // Rainbow gradient for waveform
  visage::Gradient waveGradient(0xffff6666, 0xffffff66, 0xff66ff66, 0xff66ffff, 0xff6666ff, 0xffff66ff, 0xffff6666);
  visage::Brush waveBrush = visage::Brush::linear(waveGradient, {0, 0}, {w, 0});

  canvas.setColor(waveBrush);

  visage::Path wavePath;
  for (int i = 0; i <= numPoints; ++i) {
    float t = static_cast<float>(i) / numPoints;
    float x = t * w;
    float phase = t * kTwoPi * 4.f + time * 3.f;
    float envelope = std::sin(t * kPi); // Fade edges
    float y = waveY + std::sin(phase) * waveH * gain * envelope;

    if (i == 0)
      wavePath.moveTo({x, y});
    else
      wavePath.lineTo({x, y});
  }
  canvas.fill(wavePath.stroke(2.5f));

  // Draw circular gain knob
  float knobX = w * 0.5f;
  float knobY = h * 0.65f;
  float knobRadius = std::min(w, h) * 0.18f;
  float knobInner = knobRadius * 0.7f;

  // Outer ring gradient
  visage::Gradient ringGradient(0xff333344, 0xff444455);
  visage::Brush ringBrush = visage::Brush::radial(ringGradient, {knobX, knobY}, knobRadius);
  canvas.setColor(ringBrush);
  canvas.circle(knobX - knobRadius, knobY - knobRadius, knobRadius * 2.f);

  // Inner knob
  visage::Gradient knobGradient(0xff556677, 0xff334455);
  visage::Brush knobBrush = visage::Brush::radial(knobGradient, {knobX, knobY - knobInner * 0.3f}, knobInner * 1.5f);
  canvas.setColor(knobBrush);
  canvas.circle(knobX - knobInner, knobY - knobInner, knobInner * 2.f);

  // Arc indicator showing gain level
  float arcRadius = knobRadius * 0.88f;
  float arcWidth = 4.f;
  float startAngle = kPi * 0.75f;
  float endAngle = kPi * 2.25f;
  float gainAngle = startAngle + (endAngle - startAngle) * gain;

  // Background arc
  canvas.setColor(0x44ffffff);
  visage::Path bgArc;
  for (int i = 0; i <= 50; ++i) {
    float t = static_cast<float>(i) / 50.f;
    float angle = startAngle + t * (endAngle - startAngle);
    float x = knobX + std::cos(angle) * arcRadius;
    float y = knobY + std::sin(angle) * arcRadius;
    if (i == 0)
      bgArc.moveTo({x, y});
    else
      bgArc.lineTo({x, y});
  }
  canvas.fill(bgArc.stroke(arcWidth));

  // Active arc with gradient
  if (gain > 0.01f) {
    visage::Gradient arcGradient(0xff00ffaa, 0xff00aaff, 0xffaa00ff);
    int activePoints = static_cast<int>(50 * gain);
    visage::Path activeArc;
    for (int i = 0; i <= activePoints; ++i) {
      float t = static_cast<float>(i) / 50.f;
      float angle = startAngle + t * (endAngle - startAngle);
      float x = knobX + std::cos(angle) * arcRadius;
      float y = knobY + std::sin(angle) * arcRadius;
      if (i == 0)
        activeArc.moveTo({x, y});
      else
        activeArc.lineTo({x, y});
    }
    visage::Brush arcBrush = visage::Brush::linear(arcGradient,
      {knobX - arcRadius, knobY}, {knobX + arcRadius, knobY});
    canvas.setColor(arcBrush);
    canvas.fill(activeArc.stroke(arcWidth));
  }

  // Knob pointer
  float pointerLength = knobInner * 0.6f;
  float pointerAngle = startAngle + (endAngle - startAngle) * gain;
  float px = knobX + std::cos(pointerAngle) * pointerLength;
  float py = knobY + std::sin(pointerAngle) * pointerLength;
  canvas.setColor(0xffffffff);
  visage::Path pointer;
  pointer.moveTo({knobX, knobY});
  pointer.lineTo({px, py});
  canvas.fill(pointer.stroke(3.f));

  // Gain percentage text
  canvas.setColor(0xccffffff);
  char gainText[16];
  snprintf(gainText, sizeof(gainText), "%.0f%%", gain * 100.f);

  // Draw centered below knob (simple centered text approximation)
  float textY = knobY + knobRadius + 20.f;
  float textW = 60.f;
  canvas.setColor(0xaaffffff);
  canvas.fill(knobX - 3.f, textY - 8.f, 6.f, 16.f); // Simple indicator

  // Title
  canvas.setColor(0x88ffffff);
  canvas.fill(w * 0.5f - 40.f, 15.f, 80.f, 3.f);

  // Request continuous redraw for animation
  editor->redraw();
}

void VisageTemplate::OnMouseDown(const visage::MouseEvent& e)
{
  auto* editor = GetEditor();
  if (!editor)
    return;

  float knobX = editor->width() * 0.5f;
  float knobY = editor->height() * 0.65f;
  float knobRadius = std::min(editor->width(), editor->height()) * 0.18f;

  float dx = e.position.x - knobX;
  float dy = e.position.y - knobY;
  if (dx * dx + dy * dy < knobRadius * knobRadius * 1.5f) {
    BeginInformHostOfParamChangeFromUI(kParamGain);
    mDragging = true;
    mLastY = e.position.y;
  }
}

void VisageTemplate::OnMouseDrag(const visage::MouseEvent& e)
{
  if (mDragging)
  {
    auto* editor = GetEditor();
    if (!editor)
      return;

    float delta = (mLastY - e.position.y) / editor->height() * 2.f;
    double norm = GetParam(kParamGain)->GetNormalized();
    double newNorm = std::clamp(norm + delta, 0.0, 1.0);
    SendParameterValueFromUI(kParamGain, newNorm);
    mLastY = e.position.y;
  }
}

void VisageTemplate::OnMouseUp(const visage::MouseEvent& e)
{
  if (mDragging)
  {
    EndInformHostOfParamChangeFromUI(kParamGain);
    mDragging = false;
  }
}

void VisageTemplate::OnParamChangeUI(int paramIdx, EParamSource source)
{
  if (source != EParamSource::kUI)
    Redraw();
}
#endif // CLI_API

void VisageTemplate::ProcessBlock(sample** inputs, sample** outputs, int nFrames)
{
  const int nChans = NOutChansConnected();
  const double gain = GetParam(kParamGain)->Value() / 100.;
  for (int s = 0; s < nFrames; s++)
    for (int c = 0; c < nChans; c++)
      outputs[c][s] = inputs[c][s] * gain;
}
