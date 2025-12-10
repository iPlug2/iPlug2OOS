#!/usr/bin/env python3
"""
DSP analysis toolkit for iPlug2 CLI plugins.

Analyze and visualize audio processing: impulse response, frequency response,
THD measurement, spectrograms, step response, and more.

Usage:
    python cli_analyze.py <cli_binary> [options]

Examples:
    # Basic impulse plot
    python cli_analyze.py ./build/out/MyPlugin --set 0 100 -o impulse.png

    # THD analysis with 1kHz sine
    python cli_analyze.py ./build/out/MyPlugin --set 0 75 --thd 1000 100 -o thd.png

    # Spectrogram of chirp through distortion
    python cli_analyze.py ./build/out/MyPlugin --chirp 100 8000 500 --spectrogram -o spec.png

    # Frequency response
    python cli_analyze.py ./build/out/MyPlugin --spectrum -o freq.png

    # Combined 4-panel view
    python cli_analyze.py ./build/out/MyPlugin --combined -o combined.png

    # Parameter sweep comparison
    python cli_analyze.py ./build/out/MyPlugin --sweep 0 0 100 5 -o sweep.png

    # Validation checks
    python cli_analyze.py ./build/out/MyPlugin --set 0 100 --validate unity
"""

import argparse
import subprocess
import tempfile
import os
import sys
import math
import json
from pathlib import Path

# Optional: numpy for FFT
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# Optional: matplotlib for plotting
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False




def run_impulse(cli_path, length=4096, params=None, sample_rate=44100):
    """
    Run the CLI to generate an impulse response.

    Args:
        cli_path: Path to the CLI binary
        length: Impulse response length in samples
        params: List of (index, value) tuples to set parameters
        sample_rate: Sample rate in Hz

    Returns:
        List of float samples
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_path = f.name

    try:
        cmd = [cli_path, "--sr", str(sample_rate)]

        # Add parameter settings
        if params:
            for idx, val in params:
                cmd.extend(["--set", str(idx), str(val)])

        cmd.extend(["--impulse", str(length), "--output-txt", output_path])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"CLI error: {result.stderr}", file=sys.stderr)
            return None

        # Read samples from output file
        samples = []
        with open(output_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(float(line))

        return samples

    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def run_signal(cli_path, signal_type, params=None, sample_rate=44100, **kwargs):
    """
    Run the CLI to generate a test signal response.

    Args:
        cli_path: Path to the CLI binary
        signal_type: 'sine', 'noise', 'step', 'chirp', or 'silence'
        params: List of (index, value) tuples to set parameters
        sample_rate: Sample rate in Hz
        **kwargs: Signal-specific arguments (freq, duration_ms, start_freq, end_freq)

    Returns:
        List of float samples
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_path = f.name

    try:
        cmd = [cli_path, "--sr", str(sample_rate)]

        # Add parameter settings
        if params:
            for idx, val in params:
                cmd.extend(["--set", str(idx), str(val)])

        # Add signal-specific arguments
        duration_ms = kwargs.get('duration_ms', 100)

        if signal_type == 'sine':
            freq = kwargs.get('freq', 1000)
            cmd.extend(["--sine", str(freq), str(duration_ms)])
        elif signal_type == 'noise':
            cmd.extend(["--noise", str(duration_ms)])
        elif signal_type == 'step':
            cmd.extend(["--step", str(duration_ms)])
        elif signal_type == 'chirp':
            start_freq = kwargs.get('start_freq', 20)
            end_freq = kwargs.get('end_freq', 20000)
            cmd.extend(["--chirp", str(start_freq), str(end_freq), str(duration_ms)])
        elif signal_type == 'silence':
            nframes = int(duration_ms * sample_rate / 1000)
            cmd.extend(["--process", str(nframes)])
        else:
            raise ValueError(f"Unknown signal type: {signal_type}")

        cmd.extend(["--output-txt", output_path])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"CLI error: {result.stderr}", file=sys.stderr)
            return None

        # Read samples from output file
        samples = []
        with open(output_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(float(line))

        return samples

    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def render_note(cli_path, note=60, velocity=100, duration_ms=500, release_ms=500,
                params=None, sample_rate=44100):
    """
    Render a MIDI note and capture output (for instruments/synths).

    Args:
        cli_path: Path to the CLI binary
        note: MIDI note number (60 = C4)
        velocity: Note velocity (0-127)
        duration_ms: Note duration in ms
        release_ms: Time after note-off to capture
        params: List of (index, value) tuples to set parameters
        sample_rate: Sample rate in Hz

    Returns:
        List of float samples
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        output_path = f.name

    try:
        cmd = [cli_path, "--sr", str(sample_rate)]

        # Add parameter settings
        if params:
            for idx, val in params:
                cmd.extend(["--set", str(idx), str(val)])

        # Queue MIDI note
        cmd.extend(["--midi", str(note), str(velocity), "0", str(duration_ms)])

        # Render for note duration + release
        total_ms = duration_ms + release_ms
        cmd.extend(["--render", str(total_ms)])
        cmd.extend(["--output-txt", output_path])

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"CLI error: {result.stderr}", file=sys.stderr)
            return None

        # Read samples from output file
        samples = []
        with open(output_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    samples.append(float(line))

        return samples

    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def analyze_thd(samples, fundamental_freq, sample_rate=44100, n_harmonics=10):
    """
    Calculate Total Harmonic Distortion from a sine wave response.

    Args:
        samples: Output samples from sine wave input
        fundamental_freq: Input sine wave frequency
        sample_rate: Sample rate in Hz
        n_harmonics: Number of harmonics to include

    Returns:
        dict with THD percentage and harmonic levels
    """
    if not HAS_NUMPY:
        return None

    samples = np.array(samples)
    n = len(samples)

    # Apply window to reduce spectral leakage
    window = np.hanning(n)
    windowed = samples * window

    # Compute FFT
    fft = np.fft.rfft(windowed)
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)
    magnitude = np.abs(fft)

    # Find fundamental bin (closest to expected frequency)
    fundamental_idx = np.argmin(np.abs(freqs - fundamental_freq))
    fundamental_mag = magnitude[fundamental_idx]

    # Find harmonics
    harmonics = {}
    harmonic_power = 0.0

    for h in range(2, n_harmonics + 1):
        h_freq = fundamental_freq * h
        if h_freq >= sample_rate / 2:
            break
        h_idx = np.argmin(np.abs(freqs - h_freq))
        h_mag = magnitude[h_idx]
        harmonics[f"H{h}"] = {
            'freq': float(freqs[h_idx]),
            'magnitude': float(h_mag),
            'db_relative': float(20 * np.log10(h_mag / fundamental_mag + 1e-10))
        }
        harmonic_power += h_mag ** 2

    # Calculate THD
    if fundamental_mag > 0:
        thd = np.sqrt(harmonic_power) / fundamental_mag * 100
    else:
        thd = 0.0

    return {
        'thd_percent': float(thd),
        'fundamental_freq': float(freqs[fundamental_idx]),
        'fundamental_magnitude': float(fundamental_mag),
        'harmonics': harmonics
    }


def analyze_noise_floor(samples, sample_rate=44100):
    """
    Measure noise floor from silence or very quiet signal.

    Args:
        samples: Output samples from silence input
        sample_rate: Sample rate in Hz

    Returns:
        dict with noise floor metrics
    """
    if not HAS_NUMPY:
        return None

    samples = np.array(samples)

    rms = np.sqrt(np.mean(samples ** 2))
    peak = np.max(np.abs(samples))
    crest = peak / rms if rms > 0 else 0

    # Estimate bits of resolution (assuming 0dBFS = 1.0)
    if rms > 0:
        # For uniform noise, theoretical bits = -log2(rms * sqrt(12))
        bits_resolution = -np.log2(rms) - np.log2(np.sqrt(12))
    else:
        bits_resolution = float('inf')

    # Frequency domain analysis
    fft = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
    magnitude_db = 20 * np.log10(np.abs(fft) + 1e-10)

    return {
        'rms': float(rms),
        'rms_db': float(20 * np.log10(rms + 1e-10)),
        'peak': float(peak),
        'peak_db': float(20 * np.log10(peak + 1e-10)),
        'crest_factor': float(crest),
        'estimated_bits': float(bits_resolution),
        'mean_spectrum_db': float(np.mean(magnitude_db[1:]))  # Exclude DC
    }


def compute_group_delay(samples, sample_rate=44100):
    """
    Compute group delay (derivative of phase).

    Args:
        samples: Impulse response samples
        sample_rate: Sample rate in Hz

    Returns:
        freqs: Frequency bins in Hz
        group_delay_ms: Group delay in milliseconds
    """
    if not HAS_NUMPY:
        return None, None

    samples = np.array(samples)
    n = len(samples)

    # Compute FFT
    fft = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)

    # Unwrapped phase
    phase_rad = np.unwrap(np.angle(fft))

    # Group delay = -d(phase)/d(omega)
    # Using central differences for derivative
    omega = 2 * np.pi * freqs
    d_omega = omega[1] - omega[0]  # Frequency bin spacing in rad/s

    group_delay_samples = -np.gradient(phase_rad, d_omega)
    group_delay_ms = group_delay_samples * 1000.0 / sample_rate

    return freqs, group_delay_ms


def analyze_step_response(samples, sample_rate=44100):
    """
    Analyze step response for transient characteristics.

    Args:
        samples: Output samples from step input
        sample_rate: Sample rate in Hz

    Returns:
        dict with step response metrics
    """
    if not HAS_NUMPY:
        return None

    samples = np.array(samples)
    n = len(samples)

    # Estimate final value from last 10%
    final_value = np.mean(samples[-n // 10:])

    if abs(final_value) < 1e-10:
        return {
            'final_value': float(final_value),
            'rise_time_ms': None,
            'overshoot_percent': None,
            'settling_time_ms': None,
            'note': 'Signal too small to analyze'
        }

    # Find 10% and 90% of final value for rise time
    threshold_10 = 0.1 * final_value
    threshold_90 = 0.9 * final_value

    t10_idx = np.argmax(samples >= threshold_10) if final_value > 0 else np.argmax(samples <= threshold_10)
    t90_idx = np.argmax(samples >= threshold_90) if final_value > 0 else np.argmax(samples <= threshold_90)

    rise_time_ms = (t90_idx - t10_idx) * 1000.0 / sample_rate

    # Overshoot
    if final_value > 0:
        peak = np.max(samples)
        overshoot = (peak - final_value) / final_value * 100 if final_value > 0 else 0
    else:
        peak = np.min(samples)
        overshoot = (final_value - peak) / abs(final_value) * 100

    # Settling time (2% band)
    settling_band = 0.02 * abs(final_value)
    settled = np.abs(samples - final_value) < settling_band

    # Find last unsettled sample
    unsettled_indices = np.where(~settled)[0]
    if len(unsettled_indices) > 0:
        settling_idx = unsettled_indices[-1]
        settling_time_ms = settling_idx * 1000.0 / sample_rate
    else:
        settling_time_ms = 0.0

    return {
        'final_value': float(final_value),
        'rise_time_ms': float(rise_time_ms),
        'overshoot_percent': float(overshoot),
        'settling_time_ms': float(settling_time_ms),
        'peak': float(peak)
    }


def validate_response(samples, expected_behavior=None, sample_rate=44100):
    """
    Run sanity checks on an impulse response.

    Args:
        samples: Impulse response samples
        expected_behavior: Optional hint ('unity', 'lowpass', 'highpass')
        sample_rate: Sample rate in Hz

    Returns:
        list of (check_name, passed, message) tuples
    """
    if not HAS_NUMPY:
        return [('numpy', False, 'numpy required for validation')]

    samples = np.array(samples)
    checks = []

    # Check 1: No NaN or Inf
    has_nan = np.any(np.isnan(samples))
    has_inf = np.any(np.isinf(samples))
    checks.append(('no_nan_inf', not (has_nan or has_inf),
                   f'NaN: {has_nan}, Inf: {has_inf}'))

    # Check 2: Peak within reasonable range
    peak = np.max(np.abs(samples))
    checks.append(('peak_reasonable', peak < 100,
                   f'Peak: {peak:.4f}'))

    # Check 3: DC response reasonable
    dc_sum = np.sum(samples)
    checks.append(('dc_reasonable', -100 < dc_sum < 100,
                   f'DC sum: {dc_sum:.4f}'))

    # Check 4: Energy decay (IR should generally decay, not grow)
    n = len(samples)
    first_half_energy = np.sum(samples[:n // 2] ** 2)
    second_half_energy = np.sum(samples[n // 2:] ** 2)
    decaying = second_half_energy <= first_half_energy * 1.5  # Allow some tolerance
    checks.append(('energy_decay', decaying,
                   f'First half energy: {first_half_energy:.4f}, Second half: {second_half_energy:.4f}'))

    # Expected behavior checks
    if expected_behavior == 'unity':
        # Unity gain should pass signal unchanged (DC sum ~ 1.0 for impulse)
        checks.append(('unity_gain', 0.9 < dc_sum < 1.1,
                       f'Expected DC ~1.0, got {dc_sum:.4f}'))

    elif expected_behavior == 'lowpass':
        # Lowpass should attenuate high frequencies
        freqs, mag_db, _ = compute_spectrum(samples, sample_rate)
        if freqs is not None:
            low_mask = freqs < 1000
            high_mask = freqs > 10000
            low_avg = np.mean(mag_db[low_mask]) if np.any(low_mask) else 0
            high_avg = np.mean(mag_db[high_mask]) if np.any(high_mask) else 0
            checks.append(('lowpass_shape', high_avg < low_avg - 6,
                           f'Low freq: {low_avg:.1f}dB, High freq: {high_avg:.1f}dB'))

    elif expected_behavior == 'highpass':
        # Highpass should attenuate low frequencies
        freqs, mag_db, _ = compute_spectrum(samples, sample_rate)
        if freqs is not None:
            low_mask = freqs < 500
            high_mask = freqs > 5000
            low_avg = np.mean(mag_db[low_mask]) if np.any(low_mask) else 0
            high_avg = np.mean(mag_db[high_mask]) if np.any(high_mask) else 0
            checks.append(('highpass_shape', low_avg < high_avg - 6,
                           f'Low freq: {low_avg:.1f}dB, High freq: {high_avg:.1f}dB'))

    return checks


def generate_metrics_json(samples, sample_rate=44100):
    """
    Generate comprehensive metrics as a dictionary.

    Args:
        samples: Audio samples
        sample_rate: Sample rate in Hz

    Returns:
        dict with all metrics
    """
    if not HAS_NUMPY:
        return {'error': 'numpy required for metrics'}

    samples = np.array(samples)

    metrics = {
        'sample_rate': sample_rate,
        'length_samples': len(samples),
        'length_ms': len(samples) * 1000.0 / sample_rate,
        'time_domain': {
            'peak': float(np.max(np.abs(samples))),
            'peak_db': float(20 * np.log10(np.max(np.abs(samples)) + 1e-10)),
            'rms': float(np.sqrt(np.mean(samples ** 2))),
            'rms_db': float(20 * np.log10(np.sqrt(np.mean(samples ** 2)) + 1e-10)),
            'dc_offset': float(np.mean(samples)),
            'crest_factor': float(np.max(np.abs(samples)) / (np.sqrt(np.mean(samples ** 2)) + 1e-10))
        }
    }

    # Frequency domain
    freqs, mag_db, phase_deg = compute_spectrum(samples, sample_rate)
    if freqs is not None:
        peak_idx = np.argmax(mag_db[1:]) + 1  # Exclude DC
        metrics['frequency_domain'] = {
            'peak_freq_hz': float(freqs[peak_idx]),
            'peak_magnitude_db': float(mag_db[peak_idx]),
            'dc_magnitude_db': float(mag_db[0])
        }

    # Validation checks
    validation = validate_response(samples, sample_rate=sample_rate)
    metrics['validation'] = {
        check[0]: {'passed': bool(check[1]), 'message': check[2]}
        for check in validation
    }

    return metrics


def plot_group_delay(samples, title="Group Delay", sample_rate=44100, output_path=None):
    """Plot group delay vs frequency."""
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        print("matplotlib and numpy required for group delay plot")
        return None

    freqs, group_delay_ms = compute_group_delay(samples, sample_rate)
    if freqs is None:
        return None

    fig, ax = plt.subplots(figsize=(10, 4))

    # Skip DC and very low frequencies where group delay can be noisy
    mask = freqs > 20
    ax.semilogx(freqs[mask], group_delay_ms[mask], 'b-', linewidth=0.8)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Group Delay (ms)')
    ax.set_title(title)
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim(20, sample_rate / 2)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def plot_thd(thd_result, title="THD Analysis", output_path=None, samples=None, sample_rate=44100):
    """Plot THD analysis results with waveform and spectrum display."""
    if not HAS_MATPLOTLIB:
        print("matplotlib required for THD plot")
        return None

    harmonics = thd_result.get('harmonics', {})
    if not harmonics:
        print("No harmonic data to plot")
        return None

    fund_freq = thd_result['fundamental_freq']
    fund_mag = thd_result['fundamental_magnitude']

    # Create 3-panel layout if we have samples, otherwise single plot
    if samples is not None and HAS_NUMPY:
        fig, (ax_wave, ax_spec, ax_harm) = plt.subplots(3, 1, figsize=(12, 10))

        # Plot waveform - show first few cycles
        samples = np.array(samples)
        samples_per_cycle = sample_rate / fund_freq
        n_cycles = min(4, len(samples) / samples_per_cycle)
        n_show = int(n_cycles * samples_per_cycle)

        time_ms = np.arange(n_show) / sample_rate * 1000
        ax_wave.plot(time_ms, samples[:n_show], 'b-', linewidth=1.5, label='Distorted output')
        ax_wave.set_xlabel('Time (ms)')
        ax_wave.set_ylabel('Amplitude')
        ax_wave.set_title(f'Waveform Comparison ({n_cycles:.1f} cycles at {fund_freq:.0f} Hz)')
        ax_wave.grid(True, alpha=0.3)
        ax_wave.axhline(y=0, color='gray', linewidth=0.5)

        # Show reference sine wave as dashed line
        ref_sine = np.sin(2 * np.pi * fund_freq * np.arange(n_show) / sample_rate)
        ref_sine *= np.max(np.abs(samples[:n_show]))  # Scale to match output
        ax_wave.plot(time_ms, ref_sine, 'g--', alpha=0.7, linewidth=1.5, label='Reference sine')
        ax_wave.legend(loc='upper right')

        # Plot full spectrum (dB scale)
        window = np.hanning(len(samples))
        windowed = samples * window
        fft = np.fft.rfft(windowed)
        freqs_fft = np.fft.rfftfreq(len(samples), 1.0 / sample_rate)
        magnitude_db = 20 * np.log10(np.abs(fft) + 1e-10)
        magnitude_db -= np.max(magnitude_db)  # Normalize to 0 dB peak

        # Limit to ~5x fundamental for clarity
        max_freq = fund_freq * 12
        freq_mask = freqs_fft <= max_freq
        ax_spec.plot(freqs_fft[freq_mask], magnitude_db[freq_mask], 'b-', linewidth=1)
        ax_spec.set_xlabel('Frequency (Hz)')
        ax_spec.set_ylabel('Magnitude (dB)')
        ax_spec.set_title('Output Spectrum')
        ax_spec.grid(True, alpha=0.3)
        ax_spec.set_ylim(-80, 5)

        # Mark harmonics on spectrum
        for h in range(1, 11):
            h_freq = fund_freq * h
            if h_freq <= max_freq:
                ax_spec.axvline(x=h_freq, color='red' if h > 1 else 'blue', alpha=0.3, linestyle='--')
                ax_spec.annotate(f'H{h}' if h > 1 else 'F', (h_freq, 2),
                                ha='center', fontsize=8, color='red' if h > 1 else 'blue')
    else:
        fig, ax_harm = plt.subplots(figsize=(10, 5))

    # Plot harmonic levels bar chart
    h_freqs = [fund_freq]
    h_mags = [0]  # Fundamental at 0dB reference
    h_labels = ['F']

    for h_name, h_data in harmonics.items():
        h_freqs.append(h_data['freq'])
        h_mags.append(h_data['db_relative'])
        h_labels.append(h_name)

    ax_harm.bar(range(len(h_freqs)), h_mags, color=['blue'] + ['red'] * (len(h_freqs) - 1))
    ax_harm.set_xticks(range(len(h_freqs)))
    ax_harm.set_xticklabels(h_labels)
    ax_harm.set_ylabel('Magnitude (dB relative to fundamental)')
    ax_harm.set_title(f"Harmonic Levels - THD: {thd_result['thd_percent']:.3f}%")
    ax_harm.grid(True, alpha=0.3, axis='y')

    # Add frequency labels
    for i, (f, m) in enumerate(zip(h_freqs, h_mags)):
        ax_harm.annotate(f'{f:.0f}Hz', (i, m), textcoords="offset points",
                    xytext=(0, 5), ha='center', fontsize=8, color='red' if i > 0 else 'blue')

    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def plot_impulse(samples, title="Impulse Response", sample_rate=44100, output_path=None):
    """Plot an impulse response."""
    if not HAS_MATPLOTLIB:
        print("matplotlib not installed. Install with: pip install matplotlib")
        print("\nSample data (first 32 samples):")
        for i, s in enumerate(samples[:32]):
            print(f"  [{i:4d}] {s:+.6f}")
        return None

    n = len(samples)
    time_ms = [i * 1000.0 / sample_rate for i in range(n)]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(time_ms, samples, 'b-', linewidth=0.8)
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def plot_comparison(results, sample_rate=44100, output_path=None):
    """Plot multiple impulse responses for comparison."""
    if not HAS_MATPLOTLIB:
        print("matplotlib not installed for comparison plot")
        return None

    fig, ax = plt.subplots(figsize=(10, 5))

    for label, samples in results.items():
        n = len(samples)
        time_ms = [i * 1000.0 / sample_rate for i in range(n)]
        ax.plot(time_ms, samples, label=label, linewidth=0.8)

    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('Amplitude')
    ax.set_title('Impulse Response Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def compute_spectrum(samples, sample_rate=44100):
    """
    Compute frequency spectrum from impulse response.

    Returns:
        freqs: Frequency bins in Hz
        magnitude_db: Magnitude in dB
        phase_deg: Phase in degrees
    """
    if not HAS_NUMPY:
        return None, None, None

    samples = np.array(samples)
    n = len(samples)

    # Compute FFT
    fft = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(n, 1.0 / sample_rate)

    # Magnitude in dB (with floor to avoid log(0))
    magnitude = np.abs(fft)
    magnitude_db = 20 * np.log10(np.maximum(magnitude, 1e-10))

    # Phase in degrees (unwrapped for continuity)
    phase_rad = np.angle(fft)
    phase_deg = np.degrees(np.unwrap(phase_rad))

    return freqs, magnitude_db, phase_deg


def plot_spectrum(samples, title="Frequency Response", sample_rate=44100, output_path=None):
    """Plot frequency response (magnitude in dB)."""
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        print("matplotlib and numpy required for spectrum plot")
        print("Install with: pip install matplotlib numpy")
        return None

    freqs, magnitude_db, _ = compute_spectrum(samples, sample_rate)
    if freqs is None:
        return None

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.semilogx(freqs[1:], magnitude_db[1:], 'b-', linewidth=0.8)  # Skip DC
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Magnitude (dB)')
    ax.set_title(title)
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim(20, sample_rate / 2)

    # Set reasonable y-axis limits
    max_db = np.max(magnitude_db[1:])
    ax.set_ylim(max_db - 60, max_db + 6)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def plot_phase(samples, title="Phase Response", sample_rate=44100, output_path=None):
    """Plot phase response."""
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        print("matplotlib and numpy required for phase plot")
        return None

    freqs, _, phase_deg = compute_spectrum(samples, sample_rate)
    if freqs is None:
        return None

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.semilogx(freqs[1:], phase_deg[1:], 'g-', linewidth=0.8)
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Phase (degrees)')
    ax.set_title(title)
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim(20, sample_rate / 2)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def plot_combined(samples, title="Impulse & Frequency Response", sample_rate=44100, output_path=None):
    """Plot combined time-domain and frequency-domain view."""
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        print("matplotlib and numpy required for combined plot")
        return None

    freqs, magnitude_db, phase_deg = compute_spectrum(samples, sample_rate)
    if freqs is None:
        return None

    n = len(samples)
    time_ms = [i * 1000.0 / sample_rate for i in range(n)]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle(title, fontsize=12)

    # Time domain (top-left)
    ax1 = axes[0, 0]
    ax1.plot(time_ms, samples, 'b-', linewidth=0.8)
    ax1.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Amplitude')
    ax1.set_title('Impulse Response')
    ax1.grid(True, alpha=0.3)

    # Magnitude spectrum (top-right)
    ax2 = axes[0, 1]
    ax2.semilogx(freqs[1:], magnitude_db[1:], 'b-', linewidth=0.8)
    ax2.set_xlabel('Frequency (Hz)')
    ax2.set_ylabel('Magnitude (dB)')
    ax2.set_title('Magnitude Response')
    ax2.grid(True, alpha=0.3, which='both')
    ax2.set_xlim(20, sample_rate / 2)
    max_db = np.max(magnitude_db[1:])
    ax2.set_ylim(max_db - 60, max_db + 6)

    # Phase spectrum (bottom-left)
    ax3 = axes[1, 0]
    ax3.semilogx(freqs[1:], phase_deg[1:], 'g-', linewidth=0.8)
    ax3.set_xlabel('Frequency (Hz)')
    ax3.set_ylabel('Phase (degrees)')
    ax3.set_title('Phase Response')
    ax3.grid(True, alpha=0.3, which='both')
    ax3.set_xlim(20, sample_rate / 2)

    # Zoomed time domain (bottom-right) - first 5ms or 10% whichever is smaller
    ax4 = axes[1, 1]
    zoom_samples = min(int(0.005 * sample_rate), n // 10, 256)
    zoom_time = time_ms[:zoom_samples]
    zoom_data = samples[:zoom_samples]
    ax4.plot(zoom_time, zoom_data, 'b-', linewidth=0.8)
    ax4.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
    ax4.set_xlabel('Time (ms)')
    ax4.set_ylabel('Amplitude')
    ax4.set_title('Impulse (zoomed)')
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def plot_spectrogram(samples, title="Spectrogram", sample_rate=44100, output_path=None,
                     max_freq=None, dynamic_range=80):
    """
    Plot spectrogram showing time-frequency content.

    Args:
        samples: Audio samples
        title: Plot title
        sample_rate: Sample rate in Hz
        output_path: Save to file if specified
        max_freq: Maximum frequency to display (default: Nyquist/2)
        dynamic_range: dB range to display (default: 80)
    """
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        print("matplotlib and numpy required for spectrogram")
        return None

    samples = np.array(samples)
    duration_ms = len(samples) / sample_rate * 1000

    # Choose NFFT based on signal length for good resolution
    nfft = min(2048, len(samples) // 4)
    nfft = max(256, nfft)
    # Make it a power of 2
    nfft = 2 ** int(np.log2(nfft))

    noverlap = nfft * 3 // 4  # 75% overlap for smooth display

    fig, (ax_wave, ax_spec) = plt.subplots(2, 1, figsize=(12, 8),
                                            gridspec_kw={'height_ratios': [1, 3]})
    fig.suptitle(title, fontsize=14, fontweight='bold')

    # Waveform on top
    time_ms = np.arange(len(samples)) / sample_rate * 1000
    ax_wave.plot(time_ms, samples, 'b-', linewidth=0.5)
    ax_wave.set_ylabel('Amplitude')
    ax_wave.set_xlim(0, duration_ms)
    ax_wave.set_title('Waveform')
    ax_wave.grid(True, alpha=0.3)
    ax_wave.axhline(y=0, color='gray', linewidth=0.5)

    # Spectrogram
    if max_freq is None:
        max_freq = sample_rate / 4  # Show up to Nyquist/2 by default

    Pxx, freqs, bins, im = ax_spec.specgram(samples, NFFT=nfft, Fs=sample_rate,
                                             noverlap=noverlap, cmap='magma',
                                             scale='dB')

    # Set frequency range
    ax_spec.set_ylim(0, max_freq)
    ax_spec.set_xlabel('Time (ms)')
    ax_spec.set_ylabel('Frequency (Hz)')
    ax_spec.set_title('Spectrogram')

    # Convert x-axis to ms
    ax_spec.set_xlim(0, duration_ms / 1000)
    # Fix x-axis labels to show ms
    ax_spec.set_xlabel('Time (s)')

    # Add colorbar
    cbar = fig.colorbar(im, ax=ax_spec, label='Power (dB)')

    # Adjust dynamic range
    vmax = im.get_clim()[1]
    im.set_clim(vmax - dynamic_range, vmax)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def plot_spectrum_comparison(results, sample_rate=44100, output_path=None):
    """Plot frequency response comparison for multiple parameter settings."""
    if not HAS_MATPLOTLIB or not HAS_NUMPY:
        print("matplotlib and numpy required for spectrum comparison")
        return None

    fig, ax = plt.subplots(figsize=(10, 5))

    for label, samples in results.items():
        freqs, magnitude_db, _ = compute_spectrum(samples, sample_rate)
        if freqs is not None:
            ax.semilogx(freqs[1:], magnitude_db[1:], label=label, linewidth=0.8)

    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Magnitude (dB)')
    ax.set_title('Frequency Response Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3, which='both')
    ax.set_xlim(20, sample_rate / 2)

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return output_path
    else:
        plt.show()
        return None


def main():
    parser = argparse.ArgumentParser(
        description='DSP analysis toolkit for iPlug2 CLI plugins',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('cli', type=str, help='Path to CLI binary')
    parser.add_argument('--length', '-l', type=int, default=4096,
                        help='Impulse response length in samples (default: 4096)')
    parser.add_argument('--sr', type=int, default=44100,
                        help='Sample rate in Hz (default: 44100)')
    parser.add_argument('--set', nargs=2, action='append', metavar=('IDX', 'VAL'),
                        help='Set parameter IDX to VAL (can be repeated)')
    parser.add_argument('--sweep', nargs=4, type=float, metavar=('IDX', 'START', 'END', 'STEPS'),
                        help='Sweep parameter IDX from START to END in STEPS')
    parser.add_argument('--output', '-o', type=str,
                        help='Save plot to PNG file instead of displaying')
    parser.add_argument('--no-plot', action='store_true',
                        help='Print samples instead of plotting')

    # Plot type options (mutually exclusive)
    plot_group = parser.add_mutually_exclusive_group()
    plot_group.add_argument('--spectrum', '-s', action='store_true',
                            help='Plot frequency response (magnitude in dB)')
    plot_group.add_argument('--phase', action='store_true',
                            help='Plot phase response')
    plot_group.add_argument('--combined', '-c', action='store_true',
                            help='Plot combined time + frequency view (4 panels)')
    plot_group.add_argument('--spectrogram', action='store_true',
                            help='Plot spectrogram (time-frequency view)')
    plot_group.add_argument('--group-delay', action='store_true',
                            help='Plot group delay vs frequency')

    # Spectrogram options (not mutually exclusive)
    parser.add_argument('--max-freq', type=float, default=None,
                        help='Maximum frequency for spectrogram (default: sr/4)')

    # Signal generation modes (alternative to impulse)
    signal_group = parser.add_mutually_exclusive_group()
    signal_group.add_argument('--sine', nargs=2, type=float, metavar=('FREQ', 'MS'),
                              help='Generate sine wave at FREQ Hz for MS milliseconds')
    signal_group.add_argument('--chirp', nargs=3, type=float, metavar=('START', 'END', 'MS'),
                              help='Generate log chirp from START to END Hz over MS milliseconds')

    # Analysis modes
    parser.add_argument('--thd', nargs=2, type=float, metavar=('FREQ', 'MS'),
                        help='THD analysis: generate sine at FREQ Hz for MS milliseconds')
    parser.add_argument('--noise-floor', type=int, metavar='MS',
                        help='Noise floor analysis: process MS milliseconds of silence')
    parser.add_argument('--step-response', type=int, metavar='MS',
                        help='Step response analysis for MS milliseconds')
    parser.add_argument('--validate', type=str, metavar='TYPE', nargs='?', const='effect',
                        help='Run validation checks (effect, unity, lowpass, highpass)')
    parser.add_argument('--metrics', type=str, metavar='FILE',
                        help='Export metrics to JSON file')

    # Instrument/synth mode
    parser.add_argument('--note', type=int, metavar='MIDI',
                        help='Render MIDI note (for instruments/synths)')
    parser.add_argument('--velocity', type=int, default=100,
                        help='Note velocity (default: 100)')
    parser.add_argument('--duration', type=int, default=500,
                        help='Note duration in ms (default: 500)')
    parser.add_argument('--release', type=int, default=500,
                        help='Release time after note-off in ms (default: 500)')

    args = parser.parse_args()

    cli_path = args.cli
    print(f"Using CLI: {cli_path}")

    # Parse parameters
    params = []
    if args.set:
        for idx, val in args.set:
            params.append((int(idx), float(val)))

    # Handle special analysis modes first
    if args.thd:
        # THD analysis mode
        freq, duration_ms = args.thd
        print(f"Running THD analysis at {freq} Hz for {duration_ms} ms...")
        samples = run_signal(cli_path, 'sine', params=params, sample_rate=args.sr,
                             freq=freq, duration_ms=int(duration_ms))
        if samples:
            thd_result = analyze_thd(samples, freq, args.sr)
            if thd_result:
                print(f"\nTHD Analysis Results:")
                print(f"  Fundamental: {thd_result['fundamental_freq']:.1f} Hz")
                print(f"  THD: {thd_result['thd_percent']:.4f}%")
                print(f"\n  Harmonics:")
                for h_name, h_data in thd_result['harmonics'].items():
                    print(f"    {h_name}: {h_data['freq']:.0f} Hz, {h_data['db_relative']:.1f} dB")

                if args.output:
                    plot_thd(thd_result, f"THD Analysis ({freq} Hz)", args.output, samples=samples, sample_rate=args.sr)
                    print(f"\nSaved plot to: {args.output}")
                elif not args.no_plot:
                    plot_thd(thd_result, f"THD Analysis ({freq} Hz)", samples=samples, sample_rate=args.sr)

                if args.metrics:
                    with open(args.metrics, 'w') as f:
                        json.dump(thd_result, f, indent=2)
                    print(f"Saved metrics to: {args.metrics}")
        return

    if args.noise_floor:
        # Noise floor analysis mode
        print(f"Running noise floor analysis for {args.noise_floor} ms...")
        samples = run_signal(cli_path, 'silence', params=params, sample_rate=args.sr,
                             duration_ms=args.noise_floor)
        if samples:
            result = analyze_noise_floor(samples, args.sr)
            if result:
                print(f"\nNoise Floor Analysis:")
                print(f"  RMS: {result['rms_db']:.1f} dB ({result['rms']:.2e})")
                print(f"  Peak: {result['peak_db']:.1f} dB ({result['peak']:.2e})")
                print(f"  Crest Factor: {result['crest_factor']:.2f}")
                print(f"  Estimated Resolution: {result['estimated_bits']:.1f} bits")

                if args.metrics:
                    with open(args.metrics, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"Saved metrics to: {args.metrics}")
        return

    if args.step_response:
        # Step response analysis mode
        print(f"Running step response analysis for {args.step_response} ms...")
        samples = run_signal(cli_path, 'step', params=params, sample_rate=args.sr,
                             duration_ms=args.step_response)
        if samples:
            result = analyze_step_response(samples, args.sr)
            if result:
                print(f"\nStep Response Analysis:")
                print(f"  Final Value: {result['final_value']:.4f}")
                if result.get('rise_time_ms') is not None:
                    print(f"  Rise Time (10-90%): {result['rise_time_ms']:.3f} ms")
                    print(f"  Overshoot: {result['overshoot_percent']:.2f}%")
                    print(f"  Settling Time (2%): {result['settling_time_ms']:.3f} ms")
                else:
                    print(f"  Note: {result.get('note', 'Unable to analyze')}")

                if args.output and not args.no_plot:
                    plot_impulse(samples, "Step Response", args.sr, args.output)
                    print(f"Saved plot to: {args.output}")

                if args.metrics:
                    with open(args.metrics, 'w') as f:
                        json.dump(result, f, indent=2)
                    print(f"Saved metrics to: {args.metrics}")
        return

    if args.note is not None:
        # Instrument/synth note rendering mode
        print(f"Rendering MIDI note {args.note} (vel={args.velocity}, dur={args.duration}ms, rel={args.release}ms)...")
        samples = render_note(cli_path, note=args.note, velocity=args.velocity,
                              duration_ms=args.duration, release_ms=args.release,
                              params=params, sample_rate=args.sr)
        if samples:
            # Calculate expected frequency for the note
            expected_freq = 440.0 * (2 ** ((args.note - 69) / 12.0))
            print(f"Expected fundamental: {expected_freq:.1f} Hz")

            if args.no_plot:
                metrics = generate_metrics_json(samples, args.sr)
                print(f"\nMetrics: {json.dumps(metrics, indent=2)}")
            elif args.combined:
                title = f"Note {args.note} (vel={args.velocity})"
                out = plot_combined(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
            elif args.spectrogram:
                title = f"Spectrogram - Note {args.note} (vel={args.velocity})"
                out = plot_spectrogram(samples, title, args.sr, args.output, args.max_freq)
                if out:
                    print(f"Saved plot to: {out}")
            elif args.spectrum:
                title = f"Spectrum - Note {args.note}"
                out = plot_spectrum(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
            else:
                title = f"Note {args.note} (vel={args.velocity}, {args.duration}ms)"
                out = plot_impulse(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")

            if args.metrics:
                metrics = generate_metrics_json(samples, args.sr)
                with open(args.metrics, 'w') as f:
                    json.dump(metrics, f, indent=2)
                print(f"Saved metrics to: {args.metrics}")
        return

    if args.sweep:
        # Parameter sweep mode
        param_idx = int(args.sweep[0])
        start, end, steps = args.sweep[1], args.sweep[2], int(args.sweep[3])

        results = {}
        for i in range(steps + 1):
            val = start + (end - start) * i / steps
            sweep_params = params + [(param_idx, val)]
            samples = run_impulse(cli_path, args.length, sweep_params, args.sr)
            if samples:
                results[f"P{param_idx}={val:.1f}"] = samples

        if results:
            if args.no_plot or not HAS_MATPLOTLIB:
                for label, samples in results.items():
                    print(f"\n{label}:")
                    print(f"  Peak: {max(abs(s) for s in samples):.6f}")
                    print(f"  Sum: {sum(samples):.6f}")
            elif args.spectrum:
                out = plot_spectrum_comparison(results, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
            else:
                out = plot_comparison(results, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
    else:
        # Single signal mode - impulse, sine, or chirp
        signal_type = "Impulse"
        if args.sine:
            freq, duration_ms = args.sine
            print(f"Generating {freq} Hz sine wave for {duration_ms} ms...")
            samples = run_signal(cli_path, 'sine', params=params, sample_rate=args.sr,
                                freq=freq, duration_ms=int(duration_ms))
            signal_type = f"Sine {freq:.0f}Hz"
        elif args.chirp:
            start_freq, end_freq, duration_ms = args.chirp
            print(f"Generating chirp {start_freq}-{end_freq} Hz for {duration_ms} ms...")
            samples = run_signal(cli_path, 'chirp', params=params, sample_rate=args.sr,
                                start_freq=start_freq, end_freq=end_freq, duration_ms=int(duration_ms))
            signal_type = f"Chirp {start_freq:.0f}-{end_freq:.0f}Hz"
        else:
            samples = run_impulse(cli_path, args.length, params, args.sr)

        if samples:
            # Build title with parameters
            title_suffix = ""
            if params:
                param_str = ', '.join(f"P{i}={v}" for i, v in params)
                title_suffix = f" ({param_str})"

            if args.no_plot or not HAS_MATPLOTLIB:
                print(f"\n{signal_type} Response ({len(samples)} samples):")
                print(f"  Peak amplitude: {max(abs(s) for s in samples):.6f}")
                print(f"  DC sum: {sum(samples):.6f}")
                print("\nFirst 32 samples:")
                for i, s in enumerate(samples[:32]):
                    bar = '#' * int(abs(s) * 50) if abs(s) > 0.001 else ''
                    print(f"  [{i:4d}] {s:+.6f} {bar}")
            elif args.spectrum:
                title = f"{signal_type} - Frequency Response" + title_suffix
                out = plot_spectrum(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
            elif args.phase:
                title = f"{signal_type} - Phase Response" + title_suffix
                out = plot_phase(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
            elif args.combined:
                title = f"{signal_type} - Combined View" + title_suffix
                out = plot_combined(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
            elif args.spectrogram:
                title = f"{signal_type} - Spectrogram" + title_suffix
                out = plot_spectrogram(samples, title, args.sr, args.output, args.max_freq)
                if out:
                    print(f"Saved plot to: {out}")
            elif args.group_delay:
                title = f"{signal_type} - Group Delay" + title_suffix
                out = plot_group_delay(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
            else:
                title = f"{signal_type} Response" + title_suffix
                out = plot_impulse(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")

            # Run validation if requested
            if args.validate:
                checks = validate_response(samples, args.validate, args.sr)
                print(f"\nValidation ({args.validate}):")
                all_passed = True
                for name, passed, msg in checks:
                    status = "PASS" if passed else "FAIL"
                    print(f"  [{status}] {name}: {msg}")
                    if not passed:
                        all_passed = False
                if all_passed:
                    print("\nAll checks passed!")

            # Export metrics if requested
            if args.metrics:
                metrics = generate_metrics_json(samples, args.sr)
                with open(args.metrics, 'w') as f:
                    json.dump(metrics, f, indent=2)
                print(f"Saved metrics to: {args.metrics}")


if __name__ == '__main__':
    main()
