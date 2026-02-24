"""S09: Calculate minutes outside nominal band for all required variants."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

NOMINAL_LOW_HZ = 49.9
NOMINAL_HIGH_HZ = 50.1


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--unmodified-dir", default="data/D03_weekly_1hz_csv")
    parser.add_argument("--modified-all-dir", default="data/D10_modified_2025_weekly_1hz_all_periods")
    parser.add_argument("--modified-low-high-dir", default="data/D11_modified_2025_weekly_1hz_low_high_periods")
    parser.add_argument("--modified-low-dir", default="data/D12_modified_2025_weekly_1hz_low_periods")
    parser.add_argument(
        "--output-d13",
        default="data/D13_minutes_outside_unmodified_weeks/minutes_outside_unmodified_weeks.csv",
    )
    parser.add_argument(
        "--output-d14",
        default="data/D14_minutes_outside_modified_2025_all_periods/"
        "minutes_outside_modified_2025_all_periods.csv",
    )
    parser.add_argument(
        "--output-d15",
        default="data/D15_minutes_outside_modified_2025_low_high_periods/"
        "minutes_outside_modified_2025_low_high_periods.csv",
    )
    parser.add_argument(
        "--output-d16",
        default="data/D16_minutes_outside_modified_2025_low_periods/"
        "minutes_outside_modified_2025_low_periods.csv",
    )
    return parser.parse_args()


def calculate_minutes_for_dir(input_dir: Path) -> pd.DataFrame:
    """Calculate minutes outside nominal range for all weekly CSV files in a directory."""
    rows: list[dict[str, float | int]] = []

    for csv_file in sorted(input_dir.glob("*.csv")):
        week_label = csv_file.stem
        year_str, week_str = week_label.split("-W")

        df = pd.read_csv(csv_file)
        outside_mask = (df["Value"] < NOMINAL_LOW_HZ) | (df["Value"] > NOMINAL_HIGH_HZ)
        minutes_outside = float(outside_mask.sum() / 60.0)

        rows.append(
            {
                "year": int(year_str),
                "week": int(week_str),
                "minutes_outside_nominal": minutes_outside,
            },
        )

    out_df = pd.DataFrame(rows)
    return out_df.sort_values(["year", "week"]).reset_index(drop=True)


def save_dataset(df: pd.DataFrame, output_csv: Path) -> None:
    """Save one minutes-outside dataset to CSV."""
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")


def main() -> None:
    """Run S09 pipeline step."""
    args = parse_args()

    d13 = calculate_minutes_for_dir(Path(args.unmodified_dir))
    d14 = calculate_minutes_for_dir(Path(args.modified_all_dir))
    d15 = calculate_minutes_for_dir(Path(args.modified_low_high_dir))
    d16 = calculate_minutes_for_dir(Path(args.modified_low_dir))

    save_dataset(d13, Path(args.output_d13))
    save_dataset(d14, Path(args.output_d14))
    save_dataset(d15, Path(args.output_d15))
    save_dataset(d16, Path(args.output_d16))


if __name__ == "__main__":
    main()
