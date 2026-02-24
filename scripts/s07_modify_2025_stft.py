"""S07: Create modified 2025 weekly STFT datasets."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from utils import DEFAULT_PERIOD_BINS


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--source-stft-dir", default="data/D04_weekly_stft")
    parser.add_argument("--weekly-avg-dir", default="data/D05_weekly_stft_avg_amplitude")
    parser.add_argument("--baseline-csv", default="data/D06_baseline_pre_cutoff_amplitude/baseline_pre_cutoff.csv")
    parser.add_argument("--out-all", default="data/D07_modified_2025_weekly_stft_all_periods")
    parser.add_argument("--out-low-high", default="data/D08_modified_2025_weekly_stft_low_high_periods")
    parser.add_argument("--out-low", default="data/D09_modified_2025_weekly_stft_low_periods")
    return parser.parse_args()


def main() -> None:  # noqa: C901, PLR0914, PLR0915
    """Create three modified STFT datasets for the target year.

    The script scales STFT bins using baseline-vs-target amplitude ratios and
    writes three variants: all-period scaling, low+high-period scaling, and
    low-period-only scaling.
    """
    args = parse_args()

    src_dir = Path(args.source_stft_dir)
    avg_dir = Path(args.weekly_avg_dir)
    baseline = pd.read_csv(args.baseline_csv)

    out_all = Path(args.out_all)
    out_low_high = Path(args.out_low_high)
    out_low = Path(args.out_low)
    out_all.mkdir(parents=True, exist_ok=True)
    out_low_high.mkdir(parents=True, exist_ok=True)
    out_low.mkdir(parents=True, exist_ok=True)

    low_bins = {
        "fast_sub_primary_5s_to_30s",
        "primary_local_control_30s_to_2m",
        "midrange_2m_to_15m",
    }
    high_bin = {"balancing_15m_to_2h"}

    processed = 0
    for stft_csv in sorted(src_dir.glob(f"{args.year}-W*.csv")):
        if stft_csv.name.endswith("_meta.csv"):
            continue

        week = stft_csv.stem
        week_avg_path = avg_dir / f"{week}.csv"
        if not week_avg_path.exists():
            continue

        stft_df = pd.read_csv(stft_csv)
        periods = stft_df["period_s"].to_numpy(dtype=float)

        target_avg = pd.read_csv(week_avg_path)
        merged = target_avg.merge(baseline, on="period_s", suffixes=("_target", "_base"))
        merged["scale"] = merged["amplitude_base"] / merged["amplitude_target"]
        # Round periods so CSV float representation differences do not break lookups.
        rounded_periods = np.round(merged["period_s"].to_numpy(), 9)
        scales = merged["scale"].to_numpy()
        period_to_scale = dict(zip(rounded_periods, scales, strict=False))

        scale_all = np.ones_like(periods)
        scale_low_high = np.ones_like(periods)
        scale_low = np.ones_like(periods)

        for bin_cfg in DEFAULT_PERIOD_BINS:
            mask = (periods >= bin_cfg.period_min_s) & (periods <= bin_cfg.period_max_s)
            idxs = np.where(mask)[0]
            for idx in idxs:
                scale_value = period_to_scale.get(round(float(periods[idx]), 9), 1.0)
                scale_all[idx] = scale_value
                if bin_cfg.name in low_bins:
                    scale_low[idx] = scale_value
                    scale_low_high[idx] = scale_value
                if bin_cfg.name in high_bin:
                    scale_low_high[idx] = scale_value

        frame_cols = [c for c in stft_df.columns if c.startswith("frame_")]
        for column in frame_cols:
            values = pd.Series(stft_df[column]).map(complex).to_numpy()
            stft_df[column] = values * scale_all
        stft_df.to_csv(out_all / f"{week}.csv", index=False)

        stft_df_lh = pd.read_csv(stft_csv)
        for column in frame_cols:
            values = pd.Series(stft_df_lh[column]).map(complex).to_numpy()
            stft_df_lh[column] = values * scale_low_high
        stft_df_lh.to_csv(out_low_high / f"{week}.csv", index=False)

        stft_df_l = pd.read_csv(stft_csv)
        for column in frame_cols:
            values = pd.Series(stft_df_l[column]).map(complex).to_numpy()
            stft_df_l[column] = values * scale_low
        stft_df_l.to_csv(out_low / f"{week}.csv", index=False)

        meta_path = src_dir / f"{week}_meta.csv"
        if meta_path.exists():
            meta_df = pd.read_csv(meta_path)
            meta_df.to_csv(out_all / f"{week}_meta.csv", index=False)
            meta_df.to_csv(out_low_high / f"{week}_meta.csv", index=False)
            meta_df.to_csv(out_low / f"{week}_meta.csv", index=False)

        processed += 1

    print(f"S07 summary: processed={processed}")


if __name__ == "__main__":
    main()
