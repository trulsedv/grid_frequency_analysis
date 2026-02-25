"""S07: Create modified 2025 weekly STFT datasets."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from utils import DEFAULT_PERIOD_BINS


@dataclass
class S07Context:
    """Shared inputs/outputs used for weekly S07 processing."""

    avg_dir: Path
    baseline: pd.DataFrame
    out_all: Path
    out_low_high: Path
    out_low: Path
    src_dir: Path


def main() -> None:
    """Run S07: compute scale maps and write three modified STFT variants."""
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

    ctx = S07Context(
        avg_dir=avg_dir,
        baseline=baseline,
        out_all=out_all,
        out_low_high=out_low_high,
        out_low=out_low,
        src_dir=src_dir,
    )

    processed = 0
    for stft_csv in sorted(src_dir.glob(f"{args.year}-W*.csv")):
        if stft_csv.name.endswith("_meta.csv"):
            continue
        if process_week(stft_csv, ctx):
            processed += 1

    print(f"S07 summary: processed={processed}")


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


def build_scale_map(target_avg: pd.DataFrame, baseline: pd.DataFrame) -> dict[float, float]:
    """Build period->scale map from baseline/target amplitudes."""
    merged = target_avg.merge(baseline, on="period_s", suffixes=("_target", "_base"))
    merged["scale"] = merged["amplitude_base"] / merged["amplitude_target"]
    rounded_periods = np.round(merged["period_s"].to_numpy(), 9)
    scales = merged["scale"].to_numpy()
    return dict(zip(rounded_periods, scales, strict=False))


def build_variant_scales(
    periods: np.ndarray,
    period_to_scale: dict[float, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build scale vectors for all-period, low+high, and low-only variants."""
    low_bins = {
        "fast_sub_primary_5s_to_30s",
        "primary_local_control_30s_to_2m",
        "midrange_2m_to_15m",
    }
    high_bin = {"balancing_15m_to_2h"}

    scale_all = np.ones_like(periods)
    scale_low_high = np.ones_like(periods)
    scale_low = np.ones_like(periods)

    for bin_cfg in DEFAULT_PERIOD_BINS:
        mask = (periods >= bin_cfg.period_min_s) & (periods <= bin_cfg.period_max_s)
        for idx in np.where(mask)[0]:
            scale_value = period_to_scale.get(round(float(periods[idx]), 9), 1.0)
            scale_all[idx] = scale_value
            if bin_cfg.name in low_bins:
                scale_low[idx] = scale_value
                scale_low_high[idx] = scale_value
            if bin_cfg.name in high_bin:
                scale_low_high[idx] = scale_value

    return scale_all, scale_low_high, scale_low


def write_scaled_stft(stft_csv: Path, out_path: Path, scales: np.ndarray) -> None:
    """Apply per-period scaling to all frame columns and write CSV."""
    df = pd.read_csv(stft_csv)
    frame_cols = [c for c in df.columns if c.startswith("frame_")]
    for column in frame_cols:
        values = pd.Series(df[column]).map(complex).to_numpy()
        df[column] = values * scales
    df.to_csv(out_path, index=False)


def copy_meta_if_present(src_dir: Path, week: str, out_dirs: list[Path]) -> None:
    """Copy week meta CSV to all output variant directories when present."""
    meta_path = src_dir / f"{week}_meta.csv"
    if not meta_path.exists():
        return
    meta_df = pd.read_csv(meta_path)
    for out_dir in out_dirs:
        meta_df.to_csv(out_dir / f"{week}_meta.csv", index=False)


def process_week(stft_csv: Path, ctx: S07Context) -> bool:
    """Process one week; return True when all outputs were written."""
    week = stft_csv.stem
    week_avg_path = ctx.avg_dir / f"{week}.csv"
    if not week_avg_path.exists():
        return False

    stft_df = pd.read_csv(stft_csv, usecols=["period_s"])
    periods = stft_df["period_s"].to_numpy(dtype=float)
    target_avg = pd.read_csv(week_avg_path)
    period_to_scale = build_scale_map(target_avg, ctx.baseline)
    scale_all, scale_low_high, scale_low = build_variant_scales(periods, period_to_scale)

    write_scaled_stft(stft_csv, ctx.out_all / f"{week}.csv", scale_all)
    write_scaled_stft(stft_csv, ctx.out_low_high / f"{week}.csv", scale_low_high)
    write_scaled_stft(stft_csv, ctx.out_low / f"{week}.csv", scale_low)
    copy_meta_if_present(ctx.src_dir, week, [ctx.out_all, ctx.out_low_high, ctx.out_low])
    return True


if __name__ == "__main__":
    main()
