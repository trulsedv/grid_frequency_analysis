"""Concatenate daily CSV files into weekly files resampled to 1Hz."""

from datetime import datetime
from pathlib import Path

import pandas as pd


def main():
    """Process all daily CSV files into weekly resampled files."""
    raw_csv_dir = Path("data/extracted_csv")
    weekly_dir = Path("data/weekly_csv")

    weekly_dir.mkdir(parents=True, exist_ok=True)

    csv_files = list(raw_csv_dir.glob("*.csv"))
    weekly_groups = group_files_by_week(csv_files)
    for week_key, files in weekly_groups.items():
        process_weekly_files(files, week_key, weekly_dir)

    print("✓ Weekly processing complete!")


def group_files_by_week(csv_files):
    """Group CSV files by ISO week."""
    weekly_groups = {}

    for csv_file in csv_files:
        date_str = csv_file.stem
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")  # noqa: DTZ007

        iso_year, iso_week, _ = date_obj.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"

        if week_key not in weekly_groups:
            weekly_groups[week_key] = []
        weekly_groups[week_key].append(csv_file)

    return weekly_groups


def process_weekly_files(files, week_key, output_dir):
    """Process a week's worth of files into a single resampled CSV."""
    print(f"Processing week {week_key} ({len(files)} files)...")

    weekly_data = []

    for csv_file in sorted(files):
        df = pd.read_csv(csv_file, parse_dates=True)
        weekly_data.append(df)

    week_df = pd.concat(weekly_data)
    week_df["Time"] = pd.to_datetime(week_df["Time"])
    week_df = week_df.set_index("Time")
    week_df = week_df.sort_index()
    week_df = week_df.resample("1s").mean()

    output_file = output_dir / f"{week_key}.csv"
    week_df.to_csv(output_file)
    print(f"✓ Saved {week_key}.csv")


if __name__ == "__main__":
    main()
