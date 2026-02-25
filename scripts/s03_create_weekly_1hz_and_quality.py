"""S03: Create weekly 1 Hz files and write a weekly quality report."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
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


@dataclass
class S03Context:
    """Shared S03 paths/state used when flushing weekly outputs."""

    weekly_data: dict[tuple[int, int], list[pd.DataFrame]]
    output_dir: Path
    report_path: Path
    overwrite_existing_weeks: bool


@dataclass
class S03Counters:
    """Progress counters printed in S03 summary."""

    weeks_evaluated: int = 0
    files_total: int = 0
    files_skipped: int = 0
    files_empty: int = 0


def parse_args() -> argparse.Namespace:
    """Parse S03 CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/D02_extracted_10hz_csv")
    parser.add_argument("--output-dir", default="data/D03_weekly_1hz_csv")
    parser.add_argument("--report-path", default="results/quality_report.csv")
    parser.add_argument("--from-date", default="", help="Optional YYYY-MM-DD lower bound")
    parser.add_argument("--to-date", default="", help="Optional YYYY-MM-DD upper bound")
    parser.add_argument("--limit-files", type=int, default=0)
    parser.add_argument("--overwrite-existing-weeks", action="store_true")
    return parser.parse_args()


def parse_and_prepare_daily(csv_file: Path) -> pd.DataFrame | None:
    """Read one daily 10 Hz CSV and return timezone-aware 1 Hz rows."""
    try:
        df = pd.read_csv(
            csv_file,
            usecols=["Time", "Value"],
            dtype={"Time": "string", "Value": "float64"},
        )
    except pd.errors.EmptyDataError:
        return None

    if df.empty:
        return None

    df["Time"] = pd.to_datetime(df["Time"], format="%Y-%m-%d %H:%M:%S.%f", errors="coerce")
    df = df.dropna(subset=["Time"])
    df["Time"] = (
        df["Time"]
        .dt.tz_localize("Europe/Helsinki", ambiguous="infer", nonexistent="NaT")
        .dt.tz_convert("Europe/Oslo")
        .dt.floor("1s")
    )
    df = df.dropna(subset=["Time"])
    df = df.groupby("Time", as_index=False, sort=False)["Value"].mean()

    iso = df["Time"].dt.isocalendar()
    df["ISO_Year"] = iso.year
    df["ISO_Week"] = iso.week
    return df


def flush_previous_week(ctx: S03Context, prev_year: int | None, prev_week: int | None) -> int:
    """Write previous week if available and append quality report row."""
    if prev_week is None or prev_year is None:
        return 0
    quality = write_week_csv(
        ctx.weekly_data,
        prev_year,
        prev_week,
        ctx.output_dir,
        overwrite_existing_weeks=ctx.overwrite_existing_weeks,
    )
    if quality is None:
        return 0
    write_quality_report([quality], ctx.report_path)
    return 1


def main() -> None:
    """Run S03: iterate daily files, write weekly outputs, and update quality report."""
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    report_path = Path(args.report_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    from_date = pd.Timestamp(args.from_date).date() if args.from_date else None
    to_date = pd.Timestamp(args.to_date).date() if args.to_date else None
    csv_files = sorted(input_dir.glob("*.csv"))
    if args.limit_files > 0:
        csv_files = csv_files[: args.limit_files]

    weekly_data: dict[tuple[int, int], list[pd.DataFrame]] = {}
    ctx = S03Context(weekly_data, output_dir, report_path, args.overwrite_existing_weeks)
    prev_year: int | None = None
    prev_week: int | None = None
    counters = S03Counters()

    for csv_file in csv_files:
        file_day = pd.Timestamp(csv_file.stem).date()
        if (from_date and file_day < from_date) or (to_date and file_day > to_date):
            continue

        counters.files_total += 1
        if (not args.overwrite_existing_weeks) and skip_csv_file(csv_file, output_dir):
            counters.files_skipped += 1
            continue

        df = parse_and_prepare_daily(csv_file)
        if df is None:
            counters.files_empty += 1
            continue

        for (year, week), week_data in df.groupby(["ISO_Year", "ISO_Week"], sort=False):
            if prev_week is not None and prev_week != week:
                counters.weeks_evaluated += flush_previous_week(ctx, prev_year, prev_week)
            weekly_data.setdefault((int(year), int(week)), []).append(week_data)
            prev_year, prev_week = int(year), int(week)

    counters.weeks_evaluated += flush_previous_week(ctx, prev_year, prev_week)

    if counters.weeks_evaluated == 0 and report_path.exists():
        print(f"Quality report unchanged: {report_path}")
    print(
        "s03 summary: "
        f"files_total={counters.files_total}, files_skipped={counters.files_skipped}, "
        f"files_empty={counters.files_empty}, weeks_evaluated={counters.weeks_evaluated}",
    )


def write_week_csv(
    weekly_data: dict[tuple[int, int], list[pd.DataFrame]],
    year: int,
    week: int,
    output_dir: Path,
    *,
    overwrite_existing_weeks: bool,
) -> WeeklyQuality | None:
    """Write one week file unless quality thresholds require skipping it."""
    key = (year, week)
    if key not in weekly_data:
        return None

    if (not overwrite_existing_weeks) and skip_week(year, week, output_dir):
        del weekly_data[key]
        return None

    week_df = pd.concat(weekly_data[key], axis=0).drop(columns=["ISO_Year", "ISO_Week"])

    invalid_mask = (
        (week_df["Value"] <= 0)
        | (week_df["Value"] < MIN_VALID_FREQUENCY_HZ)
        | (week_df["Value"] > MAX_VALID_FREQUENCY_HZ)
    )
    invalid_rows_replaced = int(invalid_mask.sum())
    if invalid_rows_replaced > 0:
        week_df.loc[invalid_mask, "Value"] = np.nan

    observed_rows = len(week_df)
    expected_index = get_expected_week_index(year, week)
    week_series = week_df.set_index("Time")["Value"].sort_index()
    aligned = week_series.reindex(expected_index)

    synthetic_mask = aligned.isna()
    filled_rows = int(synthetic_mask.sum())
    longest_streak = longest_true_streak(synthetic_mask.to_numpy())

    quality = WeeklyQuality(
        year=year,
        week=week,
        observed_rows=observed_rows,
        invalid_rows_replaced=invalid_rows_replaced,
        filled_rows=filled_rows,
        longest_synthetic_streak_seconds=longest_streak,
        status="saved",
    )

    if filled_rows > MAX_FILLED_ROWS or longest_streak > MAX_LONGEST_SYNTHETIC_STREAK_SECONDS:
        quality.status = "skipped_quality"
        print(
            f"Skipped {year}-W{week:02d}: invalid_rows_replaced={invalid_rows_replaced}, "
            f"filled_rows={filled_rows}, longest_synthetic_streak_seconds={longest_streak}",
        )
        del weekly_data[key]
        return quality

    aligned = aligned.ffill().bfill()

    output_file = output_dir / f"{year}-W{week:02d}.csv"
    pd.DataFrame({"Time": expected_index, "Value": aligned.to_numpy()}).to_csv(output_file, index=True)
    print(
        f"Saved {output_file.name}: observed_rows={observed_rows}, "
        f"invalid_rows_replaced={invalid_rows_replaced}, filled_rows={filled_rows}, "
        f"longest_synthetic_streak_seconds={longest_streak}",
    )
    del weekly_data[key]
    return quality


def write_quality_report(rows: list[WeeklyQuality], report_path: Path) -> None:
    """Write/merge weekly quality summary without rewriting existing-week status."""
    if not rows and report_path.exists():
        print(f"Quality report unchanged: {report_path}")
        return

    new_df = pd.DataFrame(
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

    if report_path.exists():
        existing_df = pd.read_csv(report_path)
        if new_df.empty:
            report_df = existing_df
        else:
            report_df = pd.concat([existing_df, new_df], axis=0)
            report_df = report_df.drop_duplicates(subset=["year", "week"], keep="last")
    else:
        report_df = new_df

    report_df = report_df.sort_values(["year", "week"])
    report_df.to_csv(report_path, index=False)
    print(f"Saved quality report: {report_path}")


def longest_true_streak(mask: np.ndarray) -> int:
    """Return the longest consecutive True streak length."""
    max_streak = 0
    current = 0
    for flag in mask:
        if bool(flag):
            current += 1
            max_streak = max(max_streak, current)
        else:
            current = 0
    return int(max_streak)


def get_expected_week_index(year: int, week: int) -> pd.DatetimeIndex:
    """Generate expected 1 Hz timestamps for one ISO week in Oslo timezone."""
    expected_start = pd.Timestamp.fromisocalendar(year, week, 1).tz_localize("Europe/Oslo")
    expected_end_exclusive = expected_start + pd.DateOffset(weeks=1)
    return pd.date_range(start=expected_start, end=expected_end_exclusive, freq="1s", inclusive="left")


def skip_csv_file(csv_file: Path, output_dir: Path) -> bool:
    """Return True when this daily file belongs to a week that already exists."""
    date_obj = pd.Timestamp(csv_file.stem)
    iso_year, iso_week, _ = date_obj.isocalendar()
    output_file = output_dir / f"{iso_year}-W{iso_week:02d}.csv"
    return output_file.exists()


def skip_week(year: int, week: int, output_dir: Path) -> bool:
    """Return True when this week output already exists."""
    output_file = output_dir / f"{year}-W{week:02d}.csv"
    return output_file.exists()


if __name__ == "__main__":
    main()
