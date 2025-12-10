#!/usr/bin/env python3
"""
Python harness for plotting impulse responses from iPlug2 CLI plugins.

Usage:
    python plot_impulse.py <cli_binary> [options]

Examples:
    # Basic impulse plot with default settings
    python plot_impulse.py ./build/out/MyPlugin

    # Set gain to 50% and plot 1024 samples
    python plot_impulse.py ./build/out/MyPlugin --set 0 50 --length 1024

    # Compare multiple gain settings
    python plot_impulse.py ./build/out/MyPlugin --sweep 0 0 100 5

    # Save to PNG
    python plot_impulse.py ./build/out/MyPlugin --set 0 75 -o impulse.png
"""

import argparse
import subprocess
import tempfile
import os
import sys
from pathlib import Path

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


def main():
    parser = argparse.ArgumentParser(
        description='Plot impulse responses from iPlug2 CLI plugins',
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

    args = parser.parse_args()

    cli_path = args.cli
    print(f"Using CLI: {cli_path}")

    # Parse parameters
    params = []
    if args.set:
        for idx, val in args.set:
            params.append((int(idx), float(val)))

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
                results[f"Param {param_idx}={val:.1f}"] = samples

        if results:
            if args.no_plot or not HAS_MATPLOTLIB:
                for label, samples in results.items():
                    print(f"\n{label}:")
                    print(f"  Peak: {max(abs(s) for s in samples):.6f}")
                    print(f"  Sum: {sum(samples):.6f}")
            else:
                out = plot_comparison(results, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")
    else:
        # Single impulse mode
        samples = run_impulse(cli_path, args.length, params, args.sr)

        if samples:
            if args.no_plot or not HAS_MATPLOTLIB:
                print(f"\nImpulse Response ({len(samples)} samples):")
                print(f"  Peak amplitude: {max(abs(s) for s in samples):.6f}")
                print(f"  DC sum: {sum(samples):.6f}")
                print("\nFirst 32 samples:")
                for i, s in enumerate(samples[:32]):
                    bar = '#' * int(abs(s) * 50) if abs(s) > 0.001 else ''
                    print(f"  [{i:4d}] {s:+.6f} {bar}")
            else:
                title = "Impulse Response"
                if params:
                    param_str = ', '.join(f"P{i}={v}" for i, v in params)
                    title += f" ({param_str})"
                out = plot_impulse(samples, title, args.sr, args.output)
                if out:
                    print(f"Saved plot to: {out}")


if __name__ == '__main__':
    main()
