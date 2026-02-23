"""Read daily CSV files and create weekly 1 Hz CSV files (Oslo time)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

MAX_FILLED_ROWS = 7_200  # 2 hours at 1 Hz
MAX_LONGEST_SYNTHETIC_STREAK_SECONDS = 1_800  # 30 minutes
MIN_VALID_FREQUENCY_HZ = 45.0
MAX_VALID_FREQUENCY_HZ = 55.0


@dataclass
class WeeklyQuality:
    """Quality metrics for one weekly file."""

    year: int
    week: int
    observed_rows: int
    invalid_rows_replaced: int
    filled_rows: int
    longest_synthetic_streak_seconds: int
    status: str


def main() -> None:
    """Read daily CSV files and create weekly CSV files in Oslo timezone."""
    input_dir = Path("data/D02_extracted_10hz_csv")
    output_dir = Path("data/D03_weekly_1hz_csv")
    report_path = Path("results/quality_report.csv")
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    weekly_data: dict[tuple[int, int], list[pd.DataFrame]] = {}
    prev_week: int | None = None
    prev_year: int | None = None

    report_rows: list[WeeklyQuality] = []
    files_total = 0
    files_skipped = 0
    files_empty = 0

    csv_files = sorted(input_dir.glob("*.csv"))
    for csv_file in csv_files:
        files_total += 1
        if skip_csv_file(csv_file, output_dir):
            files_skipped += 1
            continue

        try:
            df = pd.read_csv(csv_file)
        except pd.errors.EmptyDataError:
            files_empty += 1
            continue

        df["Time"] = pd.to_datetime(df["Time"])

        # Convert Time from Helsinki to Oslo time
        df["Time"] = df["Time"].dt.tz_localize("Europe/Helsinki", ambiguous=False)
        df["Time"] = df["Time"].dt.tz_convert("Europe/Oslo")

        # Resample to 1-second intervals by averaging duplicate timestamps
        df["Time"] = df["Time"].dt.floor("1s", ambiguous=False)
        df = df.groupby(df["Time"]).mean().reset_index()

        df["ISO_Year"] = df["Time"].dt.isocalendar().year
        df["ISO_Week"] = df["Time"].dt.isocalendar().week

        for (year, week), week_data in df.groupby(["ISO_Year", "ISO_Week"]):
            if prev_week is not None and prev_week != week and prev_year is not None:
                quality = write_week_csv(weekly_data, prev_year, prev_week, output_dir)
                if quality is not None:
                    report_rows.append(quality)

            weekly_data.setdefault((year, week), []).append(week_data)
            prev_week = int(week)
            prev_year = int(year)

    if prev_week is not None and prev_year is not None:
        quality = write_week_csv(weekly_data, prev_year, prev_week, output_dir)
        if quality is not None:
            report_rows.append(quality)

    write_quality_report(report_rows, report_path)
    print(
        "create_weekly_csv summary: "
        f"files_total={files_total}, files_skipped={files_skipped}, files_empty={files_empty}, "
        f"weeks_evaluated={len(report_rows)}",
    )


def write_week_csv(
    weekly_data: dict[tuple[int, int], list[pd.DataFrame]],
    year: int,
    week: int,
    output_dir: Path,
) -> WeeklyQuality | None:
    """Write one week's data, skipping if synthetic gaps are too large."""
    key = (year, week)
    if key not in weekly_data:
        return None

    if skip_week(year, week, output_dir):
        del weekly_data[key]
        return WeeklyQuality(
            year=year,
            week=week,
            observed_rows=0,
            invalid_rows_replaced=0,
            filled_rows=0,
            longest_synthetic_streak_seconds=0,
            status="already_exists",
        )

    week_df = pd.concat(weekly_data[key], axis=0).drop(columns=["ISO_Year", "ISO_Week"])

    invalid_mask = (
        (week_df["Value"] <= 0)
        | (week_df["Value"] < MIN_VALID_FREQUENCY_HZ)
        | (week_df["Value"] > MAX_VALID_FREQUENCY_HZ)
    )
    invalid_rows_replaced = int(invalid_mask.sum())
    if invalid_rows_replaced > 0:
        week_df.loc[invalid_mask, "Value"] = pd.NA

    observed_rows = len(week_df)

    expected_week = get_expected_week(year, week)
    merged = expected_week.merge(week_df, on="Time", how="left")

    # Synthetic rows are those missing in source data before fill.
    synthetic_mask = merged["Value"].isna()
    filled_rows = int(synthetic_mask.sum())
    longest_streak = longest_true_streak(synthetic_mask)

    quality = WeeklyQuality(
        year=year,
        week=week,
        observed_rows=observed_rows,
        invalid_rows_replaced=invalid_rows_replaced,
        filled_rows=filled_rows,
        longest_synthetic_streak_seconds=longest_streak,
        status="saved",
    )

    if (
        filled_rows > MAX_FILLED_ROWS
        or longest_streak > MAX_LONGEST_SYNTHETIC_STREAK_SECONDS
    ):
        quality.status = "skipped_quality"
        print(
            f"Skipped {year}-W{week:02d}: invalid_rows_replaced={invalid_rows_replaced}, "
            f"filled_rows={filled_rows}, longest_synthetic_streak_seconds={longest_streak}",
        )
        del weekly_data[key]
        return quality

    merged = merged.ffill().bfill()

    output_file = output_dir / f"{year}-W{week:02d}.csv"
    merged.to_csv(output_file, index=True)
    print(
        f"Saved {output_file.name}: observed_rows={observed_rows}, "
        f"invalid_rows_replaced={invalid_rows_replaced}, filled_rows={filled_rows}, "
        f"longest_synthetic_streak_seconds={longest_streak}",
    )
    del weekly_data[key]
    return quality


def write_quality_report(rows: list[WeeklyQuality], report_path: Path) -> None:
    """Write weekly quality metrics to CSV."""
    if not rows:
        return

    report_df = pd.DataFrame(
        [
            {
                "year": r.year,
                "week": r.week,
                "observed_rows": r.observed_rows,
                "invalid_rows_replaced": r.invalid_rows_replaced,
                "filled_rows": r.filled_rows,
                "longest_synthetic_streak_seconds": r.longest_synthetic_streak_seconds,
                "status": r.status,
            }
            for r in rows
        ],
    )
    report_df = report_df.sort_values(["year", "week"])
    report_df.to_csv(report_path, index=False)
    print(f"Saved quality report: {report_path}")


def longest_true_streak(mask: pd.Series) -> int:
    """Return longest consecutive True streak length from a boolean Series."""
    max_streak = 0
    current = 0
    for flag in mask.to_numpy():
        if bool(flag):
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return int(max_streak)


def get_expected_week(year: int, week: int) -> pd.DataFrame:
    """Generate expected 1 Hz timestamps for one ISO week in Oslo timezone."""
    expected_start = pd.Timestamp.fromisocalendar(year, week, 1).tz_localize("Europe/Oslo")
    expected_end = expected_start + pd.Timedelta(weeks=1) - pd.Timedelta(seconds=1)
    expected_range = pd.date_range(start=expected_start, end=expected_end, freq="1s")
    return pd.DataFrame({"Time": expected_range})


def skip_csv_file(csv_file: Path, output_dir: Path) -> bool:
    """Check if weekly CSV already exists for the file's date week."""
    date_obj = pd.to_datetime(csv_file.stem)
    iso_year, iso_week, _ = date_obj.isocalendar()
    output_file = output_dir / f"{iso_year}-W{iso_week:02d}.csv"
    return output_file.exists()


def skip_week(year: int, week: int, output_dir: Path) -> bool:
    """Check if weekly CSV already exists."""
    output_file = output_dir / f"{year}-W{week:02d}.csv"
    return output_file.exists()


if __name__ == "__main__":
    main()
