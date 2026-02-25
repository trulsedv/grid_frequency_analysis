"""Sa5a: Plot average amplitude spectra for two selected weeks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from utils import plot_period_spectrum_series


def main() -> None:
    """Render and save Sa5a comparison plot as HTML and PNG."""
    args = parse_args()
    input_dir = Path(args.input_dir)

    week_a = pd.read_csv(input_dir / f"{args.week_a}.csv")
    week_b = pd.read_csv(input_dir / f"{args.week_b}.csv")

    plot_period_spectrum_series(
        [
            (week_a["period_s"].to_numpy(), week_a["amplitude"].to_numpy(), args.week_a),
            (week_b["period_s"].to_numpy(), week_b["amplitude"].to_numpy(), args.week_b),
        ],
        title=f"Average STFT amplitude: {args.week_a} vs {args.week_b}",
        output_html=args.output_html,
        output_png=args.output_png,
    )


def parse_args() -> argparse.Namespace:
    """Parse Sa5a CLI arguments."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="data/D05_weekly_stft_avg_amplitude")
    p.add_argument("--week-a", default="2024-W15")
    p.add_argument("--week-b", default="2025-W15")
    p.add_argument("--output-html", default="results/fft_amplitudes_two_weeks.html")
    p.add_argument("--output-png", default="results/fft_amplitudes_two_weeks.png")
    return p.parse_args()


if __name__ == "__main__":
    main()
