"""Sa8a: Reproduce frequency signal for a selected week from STFT (Da3)."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from utils import decode_stft_overlap_add, resolve_week_with_fallback


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", default="2025-W22")
    parser.add_argument("--stft-dir", default="data/D04_weekly_stft")
    parser.add_argument("--output-dir", default="data/Da3_reproduced_weekly_1hz")
    return parser.parse_args()


def main() -> None:
    """Run Sa8a appendix step."""
    args = parse_args()

    stft_dir = Path(args.stft_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    week = resolve_week_with_fallback(args.week, stft_dir)

    stft_df = pd.read_csv(stft_dir / f"{week}.csv")
    meta = pd.read_csv(stft_dir / f"{week}_meta.csv").iloc[0]

    frame_cols = [column for column in stft_df.columns if column.startswith("frame_")]
    stft = np.column_stack([pd.Series(stft_df[column]).map(complex).to_numpy() for column in frame_cols]).T

    n = int(meta["window_size_seconds"])
    hop = int(meta["hop_seconds"])
    pad = int(meta["pad"])
    orig_len = int(meta["orig_len"])

    reproduced = decode_stft_overlap_add(stft, n, hop, orig_len + 2 * pad, orig_len, pad)
    out_csv = out_dir / f"{week}.csv"
    pd.DataFrame({"Value": reproduced}).to_csv(out_csv, index=False)
    print(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
