"""STFT roundtrip and bin-edit experiment for one week.

Goal: reconstruct with high fidelity (complex coefficients + overlap-add), then
modify selected period bins and inspect effect on minutes-outside-nominal.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sys

if __package__ is None or __package__ == "":
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from grid_frequency_analysis.period_bins import DEFAULT_PERIOD_BINS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", required=True, help="ISO week, e.g. 2024-W15")
    parser.add_argument("--weekly-csv-dir", default="data/weekly_csv")
    parser.add_argument("--window-size-seconds", type=int, default=14400)
    parser.add_argument("--overlap-fraction", type=float, default=0.5)
    parser.add_argument("--output-dir", default="results/reconstruction_stft")
    parser.add_argument("--preview-seconds", type=int, default=43200)
    parser.add_argument("--nominal-lower", type=float, default=49.9)
    parser.add_argument("--nominal-upper", type=float, default=50.1)
    parser.add_argument(
        "--bin-scales",
        default="primary_local_control_30s_to_2m=1.0,balancing_15m_to_2h=0.9",
        help="Comma list: bin_name=factor, e.g. balancing_15m_to_2h=0.8",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not (0 <= args.overlap_fraction < 1):
        raise ValueError("--overlap-fraction must be in [0,1)")

    week_path = Path(args.weekly_csv_dir) / f"{args.week}.csv"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    measured = pd.read_csv(week_path)["Value"].to_numpy(dtype=float)

    stft, n, hop, starts, signal_mean, pad, orig_len = stft_encode(
        measured, args.window_size_seconds, args.overlap_fraction
    )
    baseline_full = stft_decode(stft, n, hop, orig_len + 2 * pad, starts) + signal_mean
    baseline = baseline_full[pad : pad + orig_len]

    scales = parse_scales(args.bin_scales)
    edited_stft = apply_bin_scales(stft.copy(), n, scales)
    edited_full = stft_decode(edited_stft, n, hop, orig_len + 2 * pad, starts) + signal_mean
    edited = edited_full[pad : pad + orig_len]

    baseline_stats = minutes_outside_stats("roundtrip", measured, baseline, args.nominal_lower, args.nominal_upper)
    edited_stats = minutes_outside_stats("edited", measured, edited, args.nominal_lower, args.nominal_upper)

    metrics_path = out_dir / f"{args.week}_stft_metrics.csv"
    pd.DataFrame([baseline_stats, edited_stats]).to_csv(metrics_path, index=False)

    compare_path = out_dir / f"{args.week}_stft_compare.csv"
    pd.DataFrame(
        {
            "idx_s": np.arange(len(measured)),
            "measured": measured,
            "roundtrip": baseline,
            "edited": edited,
        }
    ).to_csv(compare_path, index=False)

    html_path = out_dir / f"{args.week}_stft_compare.html"
    png_path = out_dir / f"{args.week}_stft_compare.png"
    plot_compare(measured, baseline, edited, args.preview_seconds, html_path, png_path, args.week)

    print(f"Saved {metrics_path}")
    print(f"Saved {compare_path}")
    print(f"Saved {html_path}")
    print(f"Saved {png_path}")


def stft_encode(x: np.ndarray, n: int, overlap_fraction: float):
    hop = max(1, int(round(n * (1.0 - overlap_fraction))))
    if len(x) < n:
        raise ValueError(f"Signal shorter than window ({len(x)} < {n})")

    # Reflect-pad to reduce boundary artifacts at start/end.
    pad = n // 2
    x_pad = np.pad(x, (pad, pad), mode="reflect")

    starts = list(range(0, len(x_pad) - n + 1, hop))
    if starts[-1] != len(x_pad) - n:
        starts.append(len(x_pad) - n)

    window = np.hanning(n)
    signal_mean = float(x_pad.mean())
    x0 = x_pad - signal_mean

    spec = []
    for s in starts:
        seg = x0[s : s + n] * window
        spec.append(np.fft.rfft(seg))

    return np.stack(spec, axis=0), n, hop, starts, signal_mean, pad, len(x)


def stft_decode(stft: np.ndarray, n: int, hop: int, target_len: int, starts: list[int]) -> np.ndarray:
    window = np.hanning(n)
    out = np.zeros(target_len, dtype=float)
    norm = np.zeros(target_len, dtype=float)

    for i, s in enumerate(starts):
        seg = np.fft.irfft(stft[i], n=n).real
        out[s : s + n] += seg * window
        norm[s : s + n] += window * window

    # Avoid edge blow-ups where overlap normalization is too small.
    valid = norm > 1e-6
    out[valid] /= norm[valid]

    if not np.all(valid):
        valid_idx = np.flatnonzero(valid)
        if valid_idx.size == 0:
            out[:] = 0.0
        else:
            first = int(valid_idx[0])
            last = int(valid_idx[-1])
            out[:first] = out[first]
            out[last + 1 :] = out[last]
    return out


def apply_bin_scales(stft: np.ndarray, n: int, scales: dict[str, float]) -> np.ndarray:
    freqs = np.fft.rfftfreq(n, d=1.0)
    for b in DEFAULT_PERIOD_BINS:
        if b.name not in scales:
            continue
        f_low = 1.0 / b.period_max_s
        f_high = 1.0 / b.period_min_s
        mask = (freqs >= f_low) & (freqs <= f_high)
        stft[:, mask] *= float(scales[b.name])
    return stft


def parse_scales(text: str) -> dict[str, float]:
    out: dict[str, float] = {}
    if not text.strip():
        return out
    for part in text.split(","):
        k, v = part.split("=")
        out[k.strip()] = float(v.strip())
    return out


def minutes_outside_stats(series: str, measured: np.ndarray, candidate: np.ndarray, lo: float, hi: float) -> dict[str, float | str]:
    def minutes(v: np.ndarray) -> float:
        return float(((v < lo) | (v > hi)).sum() / 60.0)

    rmse = float(np.sqrt(np.mean((measured - candidate) ** 2)))
    corr = float(np.corrcoef(measured, candidate)[0, 1])
    return {
        "series": series,
        "minutes_outside": minutes(candidate),
        "rmse": rmse,
        "corr": corr,
    }


def plot_compare(measured: np.ndarray, roundtrip: np.ndarray, edited: np.ndarray, preview_seconds: int, html: Path, png: Path, week: str) -> None:
    n = min(preview_seconds, len(measured))
    x = np.arange(n)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=measured[:n], mode="lines", name="measured", line=dict(width=1.6)))
    fig.add_trace(go.Scatter(x=x, y=roundtrip[:n], mode="lines", name="roundtrip", line=dict(width=1.2)))
    fig.add_trace(go.Scatter(x=x, y=edited[:n], mode="lines", name="edited", line=dict(width=1.2)))
    fig.update_layout(
        title=f"{week}: measured vs STFT roundtrip and edited",
        xaxis_title="Second index",
        yaxis_title="Frequency (Hz)",
    )
    fig.write_html(html, include_plotlyjs="cdn")
    try:
        fig.write_image(png, width=1800, height=900, scale=2)
    except Exception as exc:  # noqa: BLE001
        print(f"PNG export failed: {exc}")


if __name__ == "__main__":
    main()
