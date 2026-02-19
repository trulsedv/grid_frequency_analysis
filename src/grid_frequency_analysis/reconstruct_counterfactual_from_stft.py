"""Reconstruct target week from STFT and a bin-scaled counterfactual using baseline spectrum."""

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
    p.add_argument("--week", required=True)
    p.add_argument("--weekly-csv-dir", default="data/weekly_csv")
    p.add_argument("--weekly-stft-dir", default="results/weekly_stft")
    p.add_argument("--weekly-stft-avg-dir", default="results/weekly_stft_avg")
    p.add_argument("--baseline-spectrum", default="results/baseline_average_spectrum_pre_2024_summer.csv")
    p.add_argument("--bins", default="primary_local_control_30s_to_2m,balancing_15m_to_2h")
    p.add_argument("--output-dir", default="results/reconstruction_counterfactual")
    return p.parse_args()


def starts_for_len(total_len: int, n: int, hop: int) -> list[int]:
    starts = list(range(0, total_len - n + 1, hop))
    if starts[-1] != total_len - n:
        starts.append(total_len - n)
    return starts


def main() -> None:
    args = parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    measured = pd.read_csv(Path(args.weekly_csv_dir) / f"{args.week}.csv")["Value"].to_numpy(dtype=float)

    stft_df = pd.read_csv(Path(args.weekly_stft_dir) / f"{args.week}.csv")
    frame_cols = [c for c in stft_df.columns if c.startswith("frame_")]
    stft = np.column_stack([pd.Series(stft_df[c]).map(complex).to_numpy() for c in frame_cols]).T  # frames x bins
    periods = stft_df["period_s"].to_numpy(dtype=float)

    meta = pd.read_csv(Path(args.weekly_stft_dir) / f"{args.week}_meta.csv").iloc[0]
    n = int(meta["window_size_seconds"])
    hop = int(meta["hop_seconds"])
    pad = int(meta["pad"])
    orig_len = int(meta["orig_len"])

    # Baseline and target average amplitudes (step 9 and step 5)
    target_avg = pd.read_csv(Path(args.weekly_stft_avg_dir) / f"{args.week}.csv")
    base_avg = pd.read_csv(Path(args.baseline_spectrum))
    merged = target_avg.merge(base_avg, on="period_s", suffixes=("_target", "_base"))

    scale = np.ones_like(periods)
    scale_by_period = (merged["amplitude_base"].to_numpy() / merged["amplitude_target"].to_numpy())
    # aligned by period rows from same STFT config
    period_to_scale = dict(zip(np.round(merged["period_s"].to_numpy(), 9), scale_by_period))

    chosen_bins = {b.strip() for b in args.bins.split(",") if b.strip()}
    for b in DEFAULT_PERIOD_BINS:
        if b.name not in chosen_bins:
            continue
        mask = (periods >= b.period_min_s) & (periods <= b.period_max_s)
        idxs = np.where(mask)[0]
        for idx in idxs:
            scale[idx] = period_to_scale.get(round(float(periods[idx]), 9), 1.0)

    stft_cf = stft * scale[np.newaxis, :]

    roundtrip = decode(stft, n, hop, orig_len + 2 * pad, orig_len, pad)
    counterfactual = decode(stft_cf, n, hop, orig_len + 2 * pad, orig_len, pad)

    cmp = pd.DataFrame({"idx_s": np.arange(orig_len), "measured": measured[:orig_len], "roundtrip": roundtrip, "counterfactual": counterfactual})
    cmp_csv = out / f"{args.week}_counterfactual_compare.csv"
    cmp.to_csv(cmp_csv, index=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cmp["idx_s"], y=cmp["measured"], mode="lines", name="measured"))
    fig.add_trace(go.Scatter(x=cmp["idx_s"], y=cmp["roundtrip"], mode="lines", name="roundtrip"))
    fig.add_trace(go.Scatter(x=cmp["idx_s"], y=cmp["counterfactual"], mode="lines", name="counterfactual"))
    fig.update_layout(title=f"{args.week}: measured vs roundtrip vs counterfactual", xaxis_title="Second", yaxis_title="Hz")

    html = out / f"{args.week}_counterfactual_compare.html"
    png = out / f"{args.week}_counterfactual_compare.png"
    fig.write_html(html, include_plotlyjs="cdn")
    try:
        fig.write_image(png, width=1800, height=900, scale=2)
    except Exception:
        pass

    print(f"Saved {cmp_csv}")
    print(f"Saved {html}")
    print(f"Saved {png}")


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


if __name__ == "__main__":
    main()
