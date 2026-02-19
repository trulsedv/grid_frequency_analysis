"""Average STFT amplitudes over frames per week and save period/amplitude CSVs."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="results/weekly_stft")
    p.add_argument("--output-dir", default="results/weekly_stft_avg")
    p.add_argument("--limit-weeks", type=int, default=0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = sorted([p for p in in_dir.glob("*.csv") if not p.name.endswith("_meta.csv")])
    if args.limit_weeks > 0:
        files = files[: args.limit_weeks]

    processed = 0
    for path in files:
        week = path.stem
        out = out_dir / f"{week}.csv"
        df = pd.read_csv(path)
        frame_cols = [c for c in df.columns if c.startswith("frame_")]
        if not frame_cols:
            continue

        spec = np.column_stack([pd.Series(df[c]).map(complex).to_numpy() for c in frame_cols])
        amps = np.abs(spec)
        avg_amp = amps.mean(axis=1)

        out_df = pd.DataFrame({"period_s": df["period_s"].to_numpy(dtype=float), "amplitude": avg_amp})
        out_df.to_csv(out, index=False)
        processed += 1

    print(f"weekly_stft_average_amplitude summary: processed={processed}")


if __name__ == "__main__":
    main()
