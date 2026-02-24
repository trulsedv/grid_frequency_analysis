"""Sa8a: Reproduce frequency signal for a selected week from STFT (Da3)."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

NORMALIZATION_EPSILON = 1e-12


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", default="2025-W22")
    parser.add_argument("--stft-dir", default="data/D04_weekly_stft")
    parser.add_argument("--output-dir", default="data/Da3_reproduced_weekly_1hz")
    return parser.parse_args()


def starts_for_len(total_len: int, n: int, hop: int) -> list[int]:
    """Compute overlap-add window starts."""
    starts = list(range(0, total_len - n + 1, hop))
    if starts[-1] != total_len - n:
        starts.append(total_len - n)
    return starts


def decode(  # noqa: PLR0913, PLR0917
    stft_frames_bins: np.ndarray,
    n: int,
    hop: int,
    padded_len: int,
    orig_len: int,
    pad: int,
) -> np.ndarray:
    """Decode STFT to time signal."""
    window = np.hanning(n)
    starts = starts_for_len(padded_len, n, hop)

    out = np.zeros(padded_len)
    norm = np.zeros(padded_len)
    for index, start in enumerate(starts):
        segment = np.fft.irfft(stft_frames_bins[index], n=n).real
        out[start : start + n] += segment * window
        norm[start : start + n] += window * window

    valid = norm > NORMALIZATION_EPSILON
    out[valid] /= norm[valid]
    out[~valid] = 0.0
    return out[pad : pad + orig_len]


def resolve_week(requested_week: str, stft_dir: Path) -> str:
    """Resolve week label, with fallback to latest available week."""
    requested = stft_dir / f"{requested_week}.csv"
    if requested.exists():
        return requested_week

    weeks = sorted([path.stem for path in stft_dir.glob("*.csv") if not path.name.endswith("_meta.csv")])
    if not weeks:
        msg = "No STFT week files found"
        raise FileNotFoundError(msg)

    fallback = weeks[-1]
    print(f"Requested week {requested_week} not available; using {fallback}")
    return fallback


def main() -> None:
    """Run Sa8a appendix step."""
    args = parse_args()

    stft_dir = Path(args.stft_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    week = resolve_week(args.week, stft_dir)

    stft_df = pd.read_csv(stft_dir / f"{week}.csv")
    meta = pd.read_csv(stft_dir / f"{week}_meta.csv").iloc[0]

    frame_cols = [column for column in stft_df.columns if column.startswith("frame_")]
    stft = np.column_stack([pd.Series(stft_df[column]).map(complex).to_numpy() for column in frame_cols]).T

    n = int(meta["window_size_seconds"])
    hop = int(meta["hop_seconds"])
    pad = int(meta["pad"])
    orig_len = int(meta["orig_len"])

    reproduced = decode(stft, n, hop, orig_len + 2 * pad, orig_len, pad)
    out_csv = out_dir / f"{week}.csv"
    pd.DataFrame({"Value": reproduced}).to_csv(out_csv, index=False)
    print(f"Saved {out_csv}")


if __name__ == "__main__":
    main()
