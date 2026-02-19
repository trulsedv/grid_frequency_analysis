"""Compute complex STFT for each weekly CSV and save as n x (m+1) CSV.

Output format per week:
- rows: frequency bins (n_fft/2 + 1)
- columns: period_s, frame_000, frame_001, ... (complex values as strings)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="data/weekly_csv")
    p.add_argument("--output-dir", default="results/weekly_stft")
    p.add_argument("--window-size-seconds", type=int, default=14400)
    p.add_argument("--overlap-fraction", type=float, default=0.5)
    p.add_argument("--limit-weeks", type=int, default=0)
    return p.parse_args()


def starts_for_len(total_len: int, n: int, hop: int) -> list[int]:
    starts = list(range(0, total_len - n + 1, hop))
    if starts[-1] != total_len - n:
        starts.append(total_len - n)
    return starts


def main() -> None:
    args = parse_args()
    n = args.window_size_seconds
    hop = max(1, int(round(n * (1.0 - args.overlap_fraction))))
    pad = n // 2

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    weeks = sorted(in_dir.glob("*.csv"))
    if args.limit_weeks > 0:
        weeks = weeks[: args.limit_weeks]

    processed = 0
    skipped = 0
    for week_file in weeks:
        week = week_file.stem
        out_csv = out_dir / f"{week}.csv"
        if out_csv.exists():
            skipped += 1
            continue

        df = pd.read_csv(week_file)
        if "Value" not in df.columns:
            skipped += 1
            continue

        x = df["Value"].to_numpy(dtype=float)
        if len(x) < n:
            skipped += 1
            continue

        x_pad = np.pad(x, (pad, pad), mode="reflect")
        starts = starts_for_len(len(x_pad), n, hop)
        window = np.hanning(n)

        spec_cols: list[np.ndarray] = []
        for s in starts:
            seg = x_pad[s : s + n] * window
            spec_cols.append(np.fft.rfft(seg))

        spec = np.stack(spec_cols, axis=1)  # bins x frames
        freqs = np.fft.rfftfreq(n, d=1.0)
        with np.errstate(divide="ignore"):
            periods = np.where(freqs > 0, 1.0 / freqs, np.inf)

        out_df = pd.DataFrame({"period_s": periods})
        for i in range(spec.shape[1]):
            out_df[f"frame_{i:03d}"] = spec[:, i]
        out_df.to_csv(out_csv, index=False)

        meta = pd.DataFrame(
            [{"week": week, "window_size_seconds": n, "hop_seconds": hop, "pad": pad, "orig_len": len(x), "frames": spec.shape[1]}]
        )
        meta.to_csv(out_dir / f"{week}_meta.csv", index=False)

        processed += 1
        if processed % 25 == 0:
            print(f"Processed {processed} weeks...")

    print(f"weekly_stft summary: processed={processed}, skipped={skipped}")


if __name__ == "__main__":
    main()
