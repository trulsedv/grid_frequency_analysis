"""Run counterfactual reconstruction for all available 2025 weeks and plot cumulative minutes.

Uses STFT complex coefficients for each target week and scales selected period bins
using baseline average amplitudes.
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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--year", type=int, default=2025)
    p.add_argument("--weekly-csv-dir", default="data/weekly_csv")
    p.add_argument("--weekly-stft-dir", default="results/weekly_stft")
    p.add_argument("--weekly-stft-avg-dir", default="results/weekly_stft_avg")
    p.add_argument("--baseline-spectrum", default="results/baseline_average_spectrum_pre_2024_summer.csv")
    p.add_argument("--bins", default="primary_local_control_30s_to_2m,balancing_15m_to_2h")
    p.add_argument("--output-dir", default="results/counterfactual_2025")
    return p.parse_args()


def week_key(name: str) -> tuple[int, int]:
    y, w = name.split("-W")
    return int(y), int(w)


def starts_for_len(total_len: int, n: int, hop: int) -> list[int]:
    starts = list(range(0, total_len - n + 1, hop))
    if starts[-1] != total_len - n:
        starts.append(total_len - n)
    return starts


def decode(stft_frames_bins: np.ndarray, n: int, hop: int, padded_len: int, orig_len: int, pad: int) -> np.ndarray:
    window = np.hanning(n)
    starts = starts_for_len(padded_len, n, hop)

    out = np.zeros(padded_len)
    norm = np.zeros(padded_len)
    for i, s in enumerate(starts):
        seg = np.fft.irfft(stft_frames_bins[i], n=n).real
        out[s : s + n] += seg * window
        norm[s : s + n] += window * window

    valid = norm > 1e-12
    out[valid] /= norm[valid]
    out[~valid] = 0.0
    return out[pad : pad + orig_len]


def minutes_outside(v: np.ndarray, lo: float = 49.9, hi: float = 50.1) -> float:
    return float(((v < lo) | (v > hi)).sum() / 60.0)


def main() -> None:
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    weekly_csv_dir = Path(args.weekly_csv_dir)
    weeks = sorted([p.stem for p in weekly_csv_dir.glob(f"{args.year}-W*.csv")], key=week_key)

    base_avg = pd.read_csv(args.baseline_spectrum)
    chosen_bins = {b.strip() for b in args.bins.split(",") if b.strip()}

    rows = []
    for week in weeks:
        stft_path = Path(args.weekly_stft_dir) / f"{week}.csv"
        meta_path = Path(args.weekly_stft_dir) / f"{week}_meta.csv"
        avg_path = Path(args.weekly_stft_avg_dir) / f"{week}.csv"
        meas_path = weekly_csv_dir / f"{week}.csv"
        if not (stft_path.exists() and meta_path.exists() and avg_path.exists() and meas_path.exists()):
            continue

        measured = pd.read_csv(meas_path)["Value"].to_numpy(dtype=float)

        stft_df = pd.read_csv(stft_path)
        frame_cols = [c for c in stft_df.columns if c.startswith("frame_")]
        stft = np.column_stack([pd.Series(stft_df[c]).map(complex).to_numpy() for c in frame_cols]).T
        periods = stft_df["period_s"].to_numpy(dtype=float)

        meta = pd.read_csv(meta_path).iloc[0]
        n = int(meta["window_size_seconds"])
        hop = int(meta["hop_seconds"])
        pad = int(meta["pad"])
        orig_len = int(meta["orig_len"])

        target_avg = pd.read_csv(avg_path)
        merged = target_avg.merge(base_avg, on="period_s", suffixes=("_target", "_base"))
        period_to_scale = dict(
            zip(
                np.round(merged["period_s"].to_numpy(), 9),
                (merged["amplitude_base"].to_numpy() / merged["amplitude_target"].to_numpy()),
            )
        )

        scale = np.ones_like(periods)
        for b in DEFAULT_PERIOD_BINS:
            if b.name not in chosen_bins:
                continue
            mask = (periods >= b.period_min_s) & (periods <= b.period_max_s)
            idxs = np.where(mask)[0]
            for idx in idxs:
                scale[idx] = period_to_scale.get(round(float(periods[idx]), 9), 1.0)

        stft_cf = stft * scale[np.newaxis, :]
        counterfactual = decode(stft_cf, n, hop, orig_len + 2 * pad, orig_len, pad)

        y, w = week_key(week)
        rows.append(
            {
                "year": y,
                "week": w,
                "week_label": week,
                "minutes_measured": minutes_outside(measured[:orig_len]),
                "minutes_counterfactual": minutes_outside(counterfactual),
            }
        )

    df = pd.DataFrame(rows).sort_values(["year", "week"])
    df["cum_measured"] = df["minutes_measured"].cumsum()
    df["cum_counterfactual"] = df["minutes_counterfactual"].cumsum()
    df["cum_delta_cf_minus_measured"] = df["cum_counterfactual"] - df["cum_measured"]

    out_csv = out_dir / "counterfactual_2025_minutes_per_week.csv"
    df.to_csv(out_csv, index=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["week"], y=df["cum_measured"], mode="lines+markers", name="2025 measured"))
    fig.add_trace(go.Scatter(x=df["week"], y=df["cum_counterfactual"], mode="lines+markers", name="2025 counterfactual"))
    fig.update_layout(
        title="2025 cumulative minutes outside nominal: measured vs counterfactual",
        xaxis_title="Week",
        yaxis_title="Cumulative minutes outside 49.9-50.1 Hz",
    )
    html = out_dir / "counterfactual_2025_cumulative_compare.html"
    png = out_dir / "counterfactual_2025_cumulative_compare.png"
    fig.write_html(html, include_plotlyjs="cdn")
    try:
        fig.write_image(png, width=1600, height=900, scale=2)
    except Exception:
        pass

    print(f"Saved {out_csv}")
    print(f"Saved {html}")
    print(f"Saved {png}")


if __name__ == "__main__":
    main()
