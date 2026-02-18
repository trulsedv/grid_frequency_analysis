"""Compute weekly FFT spectra (period + amplitude) for each weekly CSV.

This uses a Welch-style approach: split the weekly signal into overlapping windows,
compute a one-sided FFT amplitude spectrum per window, and average amplitudes.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import jax.numpy as jnp
import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/weekly_csv", help="Input weekly CSV directory")
    parser.add_argument("--output-dir", default="data/weekly_fft", help="Output FFT CSV directory")
    parser.add_argument(
        "--window-size-seconds",
        type=int,
        default=14400,
        help="FFT window size in seconds (samples at 1 Hz), minimum 4 hours",
    )
    parser.add_argument(
        "--overlap-fraction",
        type=float,
        default=0.5,
        help="Window overlap fraction in [0, 1)",
    )
    parser.add_argument(
        "--limit-weeks",
        type=int,
        default=0,
        help="Optional limit for quick test runs (0 = all weeks)",
    )
    return parser.parse_args()


def main() -> None:
    """Run weekly FFT pipeline."""
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not (0 <= args.overlap_fraction < 1):
        raise ValueError("--overlap-fraction must be in [0, 1)")
    if args.window_size_seconds < 14400:
        raise ValueError("--window-size-seconds must be >= 14400 (4 hours)")

    weekly_files = sorted(input_dir.glob("*.csv"))
    if args.limit_weeks > 0:
        weekly_files = weekly_files[: args.limit_weeks]

    print(f"Computing FFT for {len(weekly_files)} weekly files...")

    processed = 0
    skipped = 0
    for weekly_file in weekly_files:
        week_name = weekly_file.stem
        output_file = output_dir / f"{week_name}.csv"
        if output_file.exists():
            skipped += 1
            continue

        try:
            df = pd.read_csv(weekly_file)
        except pd.errors.EmptyDataError:
            print(f"Skipping empty file: {weekly_file.name}")
            skipped += 1
            continue

        if "Value" not in df.columns:
            print(f"Skipping invalid file (missing Value): {weekly_file.name}")
            skipped += 1
            continue

        values = df["Value"].to_numpy(dtype=np.float64)
        spectrum = compute_weekly_amplitude_spectrum(
            values,
            window_size=args.window_size_seconds,
            overlap_fraction=args.overlap_fraction,
        )
        spectrum.to_csv(output_file, index=False)
        processed += 1

        if processed % 25 == 0:
            print(f"Processed {processed} weeks...")

    print(f"weekly_fft summary: processed={processed}, skipped={skipped}")


def compute_weekly_amplitude_spectrum(
    values: np.ndarray,
    window_size: int,
    overlap_fraction: float,
) -> pd.DataFrame:
    """Compute Welch-style averaged one-sided FFT amplitude spectrum."""
    n = len(values)
    if n < window_size:
        raise ValueError(f"Signal shorter than window size ({n} < {window_size})")

    step = max(1, int(round(window_size * (1.0 - overlap_fraction))))

    # Demean to reduce DC dominance.
    signal = values - values.mean()

    window = np.hanning(window_size).astype(np.float64)
    window_j = jnp.asarray(window)

    amplitudes: list[np.ndarray] = []
    for start in range(0, n - window_size + 1, step):
        segment = signal[start : start + window_size]
        segment_j = jnp.asarray(segment)
        windowed = segment_j * window_j

        fft_vals = jnp.fft.rfft(windowed)
        amp = (2.0 / window_size) * jnp.abs(fft_vals)

        # Correct DC and Nyquist bins for one-sided scaling.
        amp = amp.at[0].set(amp[0] / 2.0)
        if window_size % 2 == 0 and amp.shape[0] > 1:
            amp = amp.at[-1].set(amp[-1] / 2.0)

        amplitudes.append(np.asarray(amp))

    amp_avg = np.mean(np.stack(amplitudes, axis=0), axis=0)
    freqs = np.fft.rfftfreq(window_size, d=1.0)

    with np.errstate(divide="ignore"):
        periods = np.where(freqs > 0, 1.0 / freqs, np.inf)

    return pd.DataFrame(
        {
            "frequency_hz": freqs,
            "period_s": periods,
            "amplitude": amp_avg,
        }
    )


if __name__ == "__main__":
    main()
