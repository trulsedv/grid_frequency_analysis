"""Sa6b: Plot unmodified/modified/baseline weekly amplitudes (Ra4)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from utils import plot_period_spectrum_series, resolve_week_with_fallback


def main() -> None:
    """Run Sa6b appendix step."""
    args = parse_args()

    week = resolve_week_with_fallback(args.week, Path(args.unmodified_dir), Path(args.modified_dir))
    unmodified = pd.read_csv(Path(args.unmodified_dir) / f"{week}.csv")
    modified = pd.read_csv(Path(args.modified_dir) / f"{week}.csv")
    baseline = pd.read_csv(args.baseline_csv)

    plot_period_spectrum_series(
        [
            (unmodified["period_s"].to_numpy(), unmodified["amplitude"].to_numpy(), f"{week} unmodified"),
            (
                modified["period_s"].to_numpy(),
                modified["amplitude_modified"].to_numpy(),
                f"{week} modified",
            ),
            (baseline["period_s"].to_numpy(), baseline["amplitude"].to_numpy(), "baseline pre-cutoff"),
        ],
        title=f"Weekly amplitude comparison for {week}",
        output_html=args.output_html,
        output_png=args.output_png,
    )


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", default="2025-W22")
    parser.add_argument("--unmodified-dir", default="data/D05_weekly_stft_avg_amplitude")
    parser.add_argument("--modified-dir", default="data/Da2_modified_weekly_amplitudes")
    parser.add_argument(
        "--baseline-csv",
        default="data/D06_baseline_pre_cutoff_amplitude/baseline_pre_cutoff.csv",
    )
    parser.add_argument("--output-html", default="results/weekly_amplitude_compare.html")
    parser.add_argument("--output-png", default="results/weekly_amplitude_compare.png")
    return parser.parse_args()


if __name__ == "__main__":
    main()
