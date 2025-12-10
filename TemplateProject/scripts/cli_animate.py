#!/usr/bin/env python3
"""
Animate the effect of a parameter sweep on plugin output.

Usage:
    python3 cli_animate.py ./build-ninja/out/MyPlugin --param 1 --output sweep.gif
    python3 cli_animate.py ./build-ninja/out/MyPlugin --param 0 --min 0 --max 100 --steps 25
"""

import argparse
import subprocess
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter


def get_waveform(cli_path, param_idx, param_value, freq, duration_ms, sample_rate):
    """Run CLI with given parameter value and return output samples."""
    cmd = [
        cli_path,
        "--set", str(param_idx), str(param_value),
        "--sine", str(freq), str(duration_ms),
        "--sr", str(sample_rate),
        "--output-txt", "/dev/stdout"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running CLI: {result.stderr}")
        return np.array([])
    samples = [float(line.split()[0]) for line in result.stdout.strip().split('\n') if line]
    return np.array(samples)


def compute_harmonics(samples, fundamental_freq, sample_rate, num_harmonics=11):
    """Compute harmonic magnitudes in dB relative to fundamental."""
    n = len(samples)
    if n == 0:
        return [0] * num_harmonics, 0

    fft = np.fft.rfft(samples)
    freqs = np.fft.rfftfreq(n, 1/sample_rate)

    magnitudes = []
    for h in range(1, num_harmonics + 1):
        target_freq = fundamental_freq * h
        idx = np.argmin(np.abs(freqs - target_freq))
        mag = np.abs(fft[idx]) / (n/2)
        magnitudes.append(mag)

    # Convert to dB relative to fundamental
    fund_mag = magnitudes[0] if magnitudes[0] > 0 else 1e-10
    db_values = [20 * np.log10(m / fund_mag + 1e-10) for m in magnitudes]

    # Compute THD
    harmonic_power = sum(m**2 for m in magnitudes[1:])
    thd = 100 * np.sqrt(harmonic_power) / fund_mag if fund_mag > 0 else 0

    return db_values, thd


def main():
    parser = argparse.ArgumentParser(description='Animate parameter sweep effect on audio')
    parser.add_argument('cli_path', help='Path to CLI executable')
    parser.add_argument('--param', '-p', type=int, default=0, help='Parameter index to sweep (default: 0)')
    parser.add_argument('--min', type=float, default=0, help='Minimum parameter value (default: 0)')
    parser.add_argument('--max', type=float, default=100, help='Maximum parameter value (default: 100)')
    parser.add_argument('--steps', type=int, default=51, help='Number of steps (default: 51)')
    parser.add_argument('--freq', '-f', type=float, default=1000, help='Sine frequency in Hz (default: 1000)')
    parser.add_argument('--duration', '-d', type=float, default=4, help='Duration in ms (default: 4)')
    parser.add_argument('--sr', type=int, default=44100, help='Sample rate (default: 44100)')
    parser.add_argument('--output', '-o', default='sweep_animation.gif', help='Output filename (default: sweep_animation.gif)')
    parser.add_argument('--fps', type=int, default=10, help='Animation FPS (default: 10)')
    parser.add_argument('--title', '-t', default='Parameter Sweep', help='Animation title')
    parser.add_argument('--param-name', default='Param', help='Parameter name for display')
    parser.add_argument('--param-unit', default='%', help='Parameter unit for display')

    args = parser.parse_args()

    # Generate reference sine
    num_samples = int(args.sr * args.duration / 1000)
    t = np.arange(num_samples) / args.sr * 1000  # time in ms
    reference = np.sin(2 * np.pi * args.freq * np.arange(num_samples) / args.sr)

    # Pre-compute waveforms for different parameter values
    param_values = np.linspace(args.min, args.max, args.steps)
    waveforms = []
    print(f"Generating waveforms for {args.param_name} {args.min}-{args.max}{args.param_unit}...")
    for i, val in enumerate(param_values):
        waveforms.append(get_waveform(args.cli_path, args.param, val, args.freq, args.duration, args.sr))
        print(f"  {args.param_name}: {val:.1f}{args.param_unit}  ", end='\r')
    print(f"\nCreating animation ({args.steps} frames)...")

    # Set up the figure
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7))
    fig.suptitle(args.title, fontsize=14, fontweight='bold')

    # Waveform plot
    line_out, = ax1.plot([], [], 'b-', linewidth=2, label='Output')
    line_ref, = ax1.plot(t, reference, 'g--', linewidth=1, alpha=0.7, label='Input sine')
    ax1.set_xlim(0, args.duration)
    ax1.set_ylim(-1.2, 1.2)
    ax1.set_xlabel('Time (ms)')
    ax1.set_ylabel('Amplitude')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    title1 = ax1.set_title(f'{args.param_name}: {args.min}{args.param_unit}')

    # Spectrum plot
    ax2.set_xlim(-0.5, 10.5)
    ax2.set_ylim(-80, 5)
    ax2.set_xlabel('Harmonic')
    ax2.set_ylabel('Magnitude (dB rel. fundamental)')
    ax2.set_xticks(range(11))
    ax2.set_xticklabels(['F', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11'])
    ax2.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()

    def animate(frame):
        val = param_values[frame]
        samples = waveforms[frame]

        # Update waveform
        if len(samples) > 0:
            line_out.set_data(t[:len(samples)], samples)
        title1.set_text(f'Waveform ({args.param_name}: {val:.1f}{args.param_unit})')

        # Update spectrum
        db_values, thd = compute_harmonics(samples, args.freq, args.sr)

        ax2.clear()
        ax2.bar(range(len(db_values)), db_values, width=0.6, color='red', alpha=0.8)
        ax2.set_xlim(-0.5, 10.5)
        ax2.set_ylim(-80, 5)
        ax2.set_xlabel('Harmonic')
        ax2.set_ylabel('Magnitude (dB rel. fundamental)')
        ax2.set_xticks(range(11))
        ax2.set_xticklabels(['F', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11'])
        ax2.grid(True, alpha=0.3, axis='y')
        ax2.set_title(f'Harmonic Content (THD: {thd:.1f}%)')

        return [line_out, title1]

    anim = FuncAnimation(fig, animate, frames=len(param_values), interval=1000//args.fps, blit=False)

    # Save animation
    print(f"Saving to {args.output}...")
    if args.output.endswith('.gif'):
        anim.save(args.output, writer=PillowWriter(fps=args.fps))
    elif args.output.endswith('.mp4'):
        anim.save(args.output, writer='ffmpeg', fps=args.fps)
    else:
        # Default to GIF
        anim.save(args.output, writer=PillowWriter(fps=args.fps))

    print(f"Saved to {args.output}")
    plt.close()


if __name__ == '__main__':
    main()
