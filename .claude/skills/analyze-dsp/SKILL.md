---
name: analyze-dsp
description: DSP analysis toolkit for iPlug2 CLI plugins - impulse response, THD, noise floor, validation
---

# DSP Analysis Toolkit

Use this skill to analyze and visualize audio processing from iPlug2 plugins using the CLI target.

## Requirements

- Plugin built with CLI target (`-cli` suffix)
- Python 3 with matplotlib and numpy (`pip install matplotlib numpy`)

## Quick Start

```bash
# Build the CLI target
ninja -C build-ninja MyPlugin-cli

# Basic impulse response
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --set 0 100 -o plot.png

# THD analysis (distortion measurement)
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --thd 1000 100 -o thd.png

# Validation checks
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --validate unity
```

**Important:** Always use the Read tool to show generated plots to the user.

## CLI Test Signals

The CLI binary supports these test signals:

```bash
--impulse <samples>           Unit impulse response (default: 4096)
--sine <freq> <ms>            Sine wave at frequency for duration
--noise <ms>                  White noise for duration
--step <ms>                   Unit step response
--chirp <start> <end> <ms>    Log frequency sweep
```

## Python Script Options

### Basic Options

| Option | Description |
|--------|-------------|
| `--set <idx> <val>` | Set parameter by index |
| `--length <n>`, `-l` | Impulse length in samples |
| `--sr <rate>` | Sample rate (default: 44100) |
| `--output <file>`, `-o` | Save plot to PNG |
| `--no-plot` | Print numeric data only |

### Plot Types

| Option | Description |
|--------|-------------|
| `--spectrum`, `-s` | Frequency response (magnitude dB) |
| `--phase` | Phase response |
| `--combined`, `-c` | 4-panel view |
| `--group-delay` | Group delay vs frequency |

### Analysis Modes

| Option | Description |
|--------|-------------|
| `--thd <freq> <ms>` | THD analysis with sine input |
| `--noise-floor <ms>` | Noise floor from silence |
| `--step-response <ms>` | Step response metrics |
| `--validate <type>` | Sanity checks (effect/unity/lowpass/highpass) |
| `--metrics <file>` | Export metrics as JSON |

### Instrument/Synth Mode

| Option | Description |
|--------|-------------|
| `--note <midi>` | Render MIDI note |
| `--velocity <vel>` | Note velocity (default: 100) |
| `--duration <ms>` | Note duration (default: 500) |
| `--release <ms>` | Release time (default: 500) |

## Examples

### THD Analysis

Measure harmonic distortion with a 1kHz sine wave:

```bash
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --set 0 100 --thd 1000 100 -o thd.png
```

Output shows THD percentage and harmonic levels relative to fundamental.

### Validation Checks

Run sanity checks on impulse response:

```bash
# Basic checks (NaN, peak, DC, energy decay)
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --validate effect

# Unity gain validation (for gain/bypass plugins)
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --set 0 100 --validate unity

# Lowpass filter validation
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --validate lowpass
```

### Noise Floor Analysis

Measure output noise from silence input:

```bash
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --noise-floor 1000
```

Reports RMS, peak, crest factor, and estimated bit resolution.

### Step Response

Analyze transient behavior:

```bash
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --step-response 100 -o step.png
```

Reports rise time, overshoot, and settling time.

### JSON Metrics Export

Export comprehensive metrics for automation:

```bash
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --no-plot --metrics output.json
```

### Instrument/Synth Analysis

Render and analyze MIDI notes:

```bash
# Render middle C (note 60)
python3 scripts/cli_analyze.py ./build-ninja/out/MySynth --note 60 --combined -o note60.png

# With custom envelope
python3 scripts/cli_analyze.py ./build-ninja/out/MySynth --note 60 --duration 200 --release 800 -o note.png
```

### Parameter Sweep

Compare different parameter values:

```bash
# Time domain comparison
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --sweep 0 0 100 4 -o sweep.png

# Frequency domain comparison
python3 scripts/cli_analyze.py ./build-ninja/out/MyPlugin --sweep 0 0 100 4 --spectrum -o freq_sweep.png
```

## DSP Iteration Workflow

1. Make changes to plugin DSP code
2. Rebuild: `ninja -C build-ninja MyPlugin-cli`
3. Run analysis:
   - `--thd 1000 100` for distortion
   - `--validate unity` for sanity checks
   - `--combined` for full visualization
4. Read plot images to show user
5. Iterate based on results

## Direct CLI Usage

The analysis script wraps the CLI binary. Direct usage:

```bash
# Impulse response as text
./build-ninja/out/MyPlugin --set 0 100 --impulse 1024 --output-txt ir.txt

# Sine wave response
./build-ninja/out/MyPlugin --set 0 100 --sine 1000 100 --output-txt sine.txt

# MIDI note render
./build-ninja/out/MyPlugin --midi 60 100 0 500 --render 1000 --output render.wav
```
