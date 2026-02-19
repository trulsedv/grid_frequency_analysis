"""Reconstruct a synthetic signal from weekly FFT amplitudes and compare to measured data.

Note: weekly FFT export stores amplitudes (no phase), so reconstruction uses zero phase.
This gives a shape/frequency-content comparison, not an exact waveform match.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", required=True, help="ISO week, e.g. 2024-W15")
    parser.add_argument("--window-size-seconds", type=int, default=14400, help="FFT window size used for weekly_fft")
    parser.add_argument("--weekly-csv-dir", default="data/weekly_csv", help="Directory with weekly measured CSV files")
    parser.add_argument("--weekly-fft-dir", default="data/weekly_fft", help="Directory with weekly FFT spectra")
    parser.add_argument("--output-dir", default="results/reconstruction", help="Output directory")
    parser.add_argument("--preview-seconds", type=int, default=43200, help="Overlay preview length in seconds")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    weekly_csv = Path(args.weekly_csv_dir) / f"{args.week}.csv"
    weekly_fft = Path(args.weekly_fft_dir) / f"{args.week}.csv"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    measured_df = pd.read_csv(weekly_csv)
    spectrum_df = pd.read_csv(weekly_fft)

    measured = measured_df["Value"].to_numpy(dtype=float)
    measured_mean = float(np.mean(measured))

    recon_window = reconstruct_window_from_amplitude_spectrum(
        spectrum_df=spectrum_df,
        n=args.window_size_seconds,
    )

    recon_window = recon_window + measured_mean
    recon_tiled = tile_to_length(recon_window, len(measured))

    out_csv = out_dir / f"{args.week}_measured_vs_reconstructed.csv"
    save_compare_csv(out_csv, measured, recon_tiled)

    out_html = out_dir / f"{args.week}_measured_vs_reconstructed.html"
    out_png = out_dir / f"{args.week}_measured_vs_reconstructed.png"
    make_overlay_plot(
        measured=measured,
        reconstructed=recon_tiled,
        preview_seconds=args.preview_seconds,
        title=f"Measured vs reconstructed from weekly FFT amplitudes ({args.week})",
        html_path=out_html,
        png_path=out_png,
    )

    print(f"Saved {out_csv}")
    print(f"Saved {out_html}")
    print(f"Saved {out_png}")


def reconstruct_window_from_amplitude_spectrum(spectrum_df: pd.DataFrame, n: int) -> np.ndarray:
    """Reconstruct one N-second window from one-sided amplitude spectrum with zero phase."""
    amp = spectrum_df["amplitude"].to_numpy(dtype=float)

    expected_bins = n // 2 + 1
    if amp.shape[0] != expected_bins:
        raise ValueError(f"Unexpected spectrum size: got {amp.shape[0]}, expected {expected_bins} for n={n}")

    mag = np.zeros_like(amp)
    mag[0] = amp[0] * n
    if n % 2 == 0:
        if amp.shape[0] > 1:
            mag[-1] = amp[-1] * n
        if amp.shape[0] > 2:
            mag[1:-1] = amp[1:-1] * n / 2.0
    else:
        if amp.shape[0] > 1:
            mag[1:] = amp[1:] * n / 2.0

    phase = np.zeros_like(mag)
    one_sided_complex = mag * np.exp(1j * phase)

    recon = np.fft.irfft(one_sided_complex, n=n)
    return recon.real


def tile_to_length(window: np.ndarray, length: int) -> np.ndarray:
    repeats = int(np.ceil(length / len(window)))
    tiled = np.tile(window, repeats)[:length]
    return tiled


def save_compare_csv(path: Path, measured: np.ndarray, reconstructed: np.ndarray) -> None:
    df = pd.DataFrame(
        {
            "idx_s": np.arange(len(measured), dtype=int),
            "measured_value": measured,
            "reconstructed_value": reconstructed,
        }
    )
    df.to_csv(path, index=False)


def make_overlay_plot(
    measured: np.ndarray,
    reconstructed: np.ndarray,
    preview_seconds: int,
    title: str,
    html_path: Path,
    png_path: Path,
) -> None:
    n = min(preview_seconds, len(measured), len(reconstructed))
    x = np.arange(n)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=measured[:n], mode="lines", name="measured", line=dict(width=1.5)))
    fig.add_trace(go.Scatter(x=x, y=reconstructed[:n], mode="lines", name="reconstructed", line=dict(width=1.2)))

    fig.update_layout(
        title=title,
        xaxis_title="Second index",
        yaxis_title="Frequency (Hz)",
    )

    fig.write_html(html_path, include_plotlyjs="cdn")
    try:
        fig.write_image(png_path, width=1800, height=900, scale=2)
    except Exception as exc:  # noqa: BLE001
        print(f"PNG export failed: {exc}")


if __name__ == "__main__":
    main()
