"""Sa6a: Modify weekly amplitudes and save Da2."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from utils import parse_week_label


def main() -> None:
    """Run Sa6a appendix step."""
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline = pd.read_csv(args.baseline_csv)
    baseline_lookup = dict(
        zip(
            np.round(baseline["period_s"].to_numpy(dtype=float), 9),
            baseline["amplitude"].to_numpy(dtype=float),
            strict=False,
        ),
    )

    processed = 0
    for week_file in sorted(input_dir.glob("*.csv")):
        week_label = week_file.stem
        year, _ = parse_week_label(week_label)
        if year != args.target_year:
            continue

        weekly = pd.read_csv(week_file)
        periods = np.round(weekly["period_s"].to_numpy(dtype=float), 9)
        target_amp = weekly["amplitude"].to_numpy(dtype=float)

        modified_amp = np.array(
            [
                baseline_lookup.get(float(period), float(target))
                for period, target in zip(periods, target_amp, strict=False)
            ],
            dtype=float,
        )

        out = pd.DataFrame(
            {
                "period_s": weekly["period_s"].to_numpy(dtype=float),
                "amplitude_unmodified": target_amp,
                "amplitude_modified": modified_amp,
            },
        )
        out.to_csv(output_dir / f"{week_label}.csv", index=False)
        processed += 1

    print(f"Sa6a summary: processed={processed}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/D05_weekly_stft_avg_amplitude")
    parser.add_argument(
        "--baseline-csv",
        default="data/D06_baseline_pre_cutoff_amplitude/baseline_pre_cutoff.csv",
    )
    parser.add_argument("--target-year", type=int, default=2025)
    parser.add_argument("--output-dir", default="data/Da2_modified_weekly_amplitudes")
    return parser.parse_args()


if __name__ == "__main__":
    main()
