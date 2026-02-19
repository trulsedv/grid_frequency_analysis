"""Compute baseline average amplitude across weeks before a cutoff week."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="results/weekly_stft_avg")
    p.add_argument("--cutoff-week", default="2024-W22", help="Exclude this week and later")
    p.add_argument("--output-csv", default="results/baseline_average_spectrum_pre_2024_summer.csv")
    return p.parse_args()


def week_key(name: str) -> tuple[int, int]:
    y, w = name.split("-W")
    return int(y), int(w)


def main() -> None:
    args = parse_args()
    in_dir = Path(args.input_dir)
    out = Path(args.output_csv)
    out.parent.mkdir(parents=True, exist_ok=True)

    cutoff_key = week_key(args.cutoff_week)

    rows = []
    for p in sorted(in_dir.glob("*.csv")):
        wk = p.stem
        if week_key(wk) >= cutoff_key:
            continue
        df = pd.read_csv(p)
        rows.append(df[["period_s", "amplitude"]].rename(columns={"amplitude": wk}))

    if not rows:
        raise RuntimeError("No weeks matched cutoff")

    merged = rows[0]
    for r in rows[1:]:
        merged = merged.merge(r, on="period_s", how="inner")

    amp_cols = [c for c in merged.columns if c != "period_s"]
    merged["amplitude"] = merged[amp_cols].mean(axis=1)
    merged[["period_s", "amplitude"]].to_csv(out, index=False)
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
