"""S06: Compute baseline average amplitude across weeks before a cutoff."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from utils import parse_week_label


def main() -> None:
    """Write D06 baseline spectrum from pre-cutoff weekly average spectra."""
    args = parse_args()
    in_dir = Path(args.input_dir)
    out = Path(args.output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)

    cutoff_key = parse_week_label(args.cutoff_week)

    rows = []
    for p in sorted(in_dir.glob("*.csv")):
        wk = p.stem
        if parse_week_label(wk) >= cutoff_key:
            continue
        df = pd.read_csv(p)
        rows.append(df[["period_s", "amplitude"]].rename(columns={"amplitude": wk}))

    if not rows:
        msg = "No weeks matched cutoff"
        raise RuntimeError(msg)

    merged = rows[0]
    for r in rows[1:]:
        merged = merged.merge(r, on="period_s", how="inner")

    amp_cols = [c for c in merged.columns if c != "period_s"]
    merged["amplitude"] = merged[amp_cols].mean(axis=1)
    merged[["period_s", "amplitude"]].to_csv(out, index=False)
    print(f"Saved {out}")


def parse_args() -> argparse.Namespace:
    """Parse S06 CLI arguments."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="data/D05_weekly_stft_avg_amplitude")
    p.add_argument("--cutoff-week", default="2024-W22", help="Exclude this week and later")
    p.add_argument("--output-csv", default="data/D06_baseline_pre_cutoff_amplitude/baseline_pre_cutoff.csv")
    return p.parse_args()


if __name__ == "__main__":
    main()
