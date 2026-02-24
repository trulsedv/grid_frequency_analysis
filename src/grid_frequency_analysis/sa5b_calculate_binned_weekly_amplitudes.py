"""Sa5b: Calculate average amplitude per week for each defined bin (Da1)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from grid_frequency_analysis.period_bins import DEFAULT_PERIOD_BINS


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/D05_weekly_stft_avg_amplitude")
    parser.add_argument(
        "--output-csv",
        default="data/Da1_binned_weekly_amplitudes/binned_weekly_amplitudes.csv",
    )
    return parser.parse_args()


def parse_week(week_label: str) -> tuple[int, int]:
    """Parse week label YYYY-Www."""
    year_txt, week_txt = week_label.split("-W")
    return int(year_txt), int(week_txt)


def main() -> None:
    """Run Sa5b appendix step."""
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, float | int | str]] = []
    for week_file in sorted(input_dir.glob("*.csv")):
        week_label = week_file.stem
        year, week = parse_week(week_label)
        df = pd.read_csv(week_file)

        row: dict[str, float | int | str] = {
            "week": week_label,
            "year": year,
            "iso_week": week,
        }
        for period_bin in DEFAULT_PERIOD_BINS:
            mask = (df["period_s"] >= period_bin.period_min_s) & (df["period_s"] <= period_bin.period_max_s)
            row[period_bin.name] = float(df.loc[mask, "amplitude"].mean()) if mask.any() else float("nan")

        rows.append(row)

    out = pd.DataFrame(rows).sort_values(["year", "iso_week"]).reset_index(drop=True)
    out.to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")


if __name__ == "__main__":
    main()
