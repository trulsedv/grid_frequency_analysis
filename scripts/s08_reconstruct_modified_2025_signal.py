"""S08: Reconstruct modified 2025 weekly 1 Hz signals from modified STFT."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from utils import decode_stft_overlap_add


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--stft-all", default="data/D07_modified_2025_weekly_stft_all_periods")
    parser.add_argument("--stft-low-high", default="data/D08_modified_2025_weekly_stft_low_high_periods")
    parser.add_argument("--stft-low", default="data/D09_modified_2025_weekly_stft_low_periods")
    parser.add_argument("--out-all", default="data/D10_modified_2025_weekly_1hz_all_periods")
    parser.add_argument("--out-low-high", default="data/D11_modified_2025_weekly_1hz_low_high_periods")
    parser.add_argument("--out-low", default="data/D12_modified_2025_weekly_1hz_low_periods")
    return parser.parse_args()


def reconstruct_one_week(stft_path: Path, out_path: Path) -> None:
    """Reconstruct one week and save CSV."""
    week = stft_path.stem
    meta = pd.read_csv(stft_path.with_name(f"{week}_meta.csv")).iloc[0]

    n = int(meta["window_size_seconds"])
    hop = int(meta["hop_seconds"])
    pad = int(meta["pad"])
    orig_len = int(meta["orig_len"])

    df = pd.read_csv(stft_path)
    frame_cols = [c for c in df.columns if c.startswith("frame_")]
    stft = np.column_stack([pd.Series(df[c]).map(complex).to_numpy() for c in frame_cols]).T

    signal = decode_stft_overlap_add(stft, n, hop, orig_len + 2 * pad, orig_len, pad)
    out_df = pd.DataFrame({"Value": signal})
    out_df.to_csv(out_path / f"{week}.csv", index=False)


def process_variant(stft_dir: Path, out_dir: Path, year: int) -> int:
    """Process all weeks for one STFT variant."""
    out_dir.mkdir(parents=True, exist_ok=True)
    processed = 0
    for stft_path in sorted(stft_dir.glob(f"{year}-W*.csv")):
        if stft_path.name.endswith("_meta.csv"):
            continue
        reconstruct_one_week(stft_path, out_dir)
        processed += 1
    return processed


def main() -> None:
    """Run S08 pipeline step."""
    args = parse_args()

    count_all = process_variant(Path(args.stft_all), Path(args.out_all), args.year)
    count_lh = process_variant(Path(args.stft_low_high), Path(args.out_low_high), args.year)
    count_low = process_variant(Path(args.stft_low), Path(args.out_low), args.year)

    print(f"S08 summary: all={count_all}, low_high={count_lh}, low={count_low}")


if __name__ == "__main__":
    main()
