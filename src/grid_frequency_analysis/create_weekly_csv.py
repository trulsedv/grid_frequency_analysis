"""Read all daily CSV files (Helsinki time) and create weekly CSV files (Oslo time)."""
from pathlib import Path

import pandas as pd


def main():
    """Read all daily CSV files (Helsinki time) and create weekly CSV files (Oslo time)."""
    input_dir = Path("data/extracted_csv")
    output_dir = Path("data/weekly_csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    weekly_data = {}
    prev_week = None
    prev_year = None

    csv_files = sorted(input_dir.glob("*.csv"))
    for csv_file in csv_files:
        if skip_csv_file(csv_file, output_dir):
            print(f"Skipping existing file for {csv_file.name} as weekly CSV exists.")
            continue
        try:
            df = pd.read_csv(csv_file)
        except pd.errors.EmptyDataError:
            print(f"Skipping file with no columns: {csv_file.name}")
            continue

        df["Time"] = pd.to_datetime(df["Time"])

        # Convert "Time" column from Helsinki time to Oslo time
        df["Time"] = df["Time"].dt.tz_localize("Europe/Helsinki", ambiguous=False)
        df["Time"] = df["Time"].dt.tz_convert("Europe/Oslo")

        # Resample to 1-second intervals by averaging (no new timestamps)
        df["Time"] = df["Time"].dt.floor("1s", ambiguous=False)
        df = df.groupby(df["Time"]).mean()
        df = df.reset_index()

        df["ISO_Year"] = df["Time"].dt.isocalendar().year
        df["ISO_Week"] = df["Time"].dt.isocalendar().week
        groups = df.groupby(["ISO_Year", "ISO_Week"])
        for (year, week), week_data in groups:
            if prev_week and prev_week != week:
                write_week_csv(weekly_data, prev_year, prev_week, output_dir)

            if (year, week) not in weekly_data:
                weekly_data[year, week] = []
            weekly_data[year, week].append(week_data)
            print(f"Added data for {year}-W{week:02d} from file {csv_file.name}")
            prev_week = week
            prev_year = year

    write_week_csv(weekly_data, prev_year, prev_week, output_dir)


def write_week_csv(weekly_data, prev_year, prev_week, output_dir):
    """Write the previous week's data to a CSV file after filling missing seconds."""
    if skip_week(prev_year, prev_week, output_dir):
        del weekly_data[prev_year, prev_week]
        return
    prev_week_data = pd.concat(weekly_data[prev_year, prev_week], axis=0)
    prev_week_data = prev_week_data.drop(columns=["ISO_Year", "ISO_Week"])
    length_before = len(prev_week_data)

    # Fill missing seconds
    expected_week = get_expected_week(prev_year, prev_week)
    prev_week_data = expected_week.merge(prev_week_data, on="Time", how="left")
    prev_week_data = prev_week_data.ffill().bfill()
    length_after = len(prev_week_data)

    output_file = output_dir / f"{prev_year}-W{prev_week:02d}.csv"
    prev_week_data.to_csv(output_file, index=True)
    print(f"Saved {output_file.name} (filled in {length_after - length_before} rows)", flush=True)
    del weekly_data[prev_year, prev_week]


def get_expected_week(year, week):
    """Generate a DataFrame with expected timestamps for the given ISO week in Oslo timezone."""
    # sample rate
    freq = "1s"
    seconds = 1

    expected_start = pd.Timestamp.fromisocalendar(year, week, 1).tz_localize("Europe/Oslo")
    expected_end = expected_start + pd.Timedelta(weeks=1) - pd.Timedelta(seconds=seconds)
    expected_range = pd.date_range(start=expected_start, end=expected_end, freq=freq)
    df = pd.DataFrame({"Time": expected_range})
    return df


def skip_csv_file(csv_file, output_dir):
    """Check if the weekly CSV file already exists."""
    date_str = csv_file.stem
    date_obj = pd.to_datetime(date_str)
    iso_year, iso_week, _ = date_obj.isocalendar()
    output_file = output_dir / f"{iso_year}-W{iso_week:02d}.csv"
    return output_file.exists()


def skip_week(year, week, output_dir):
    """Check if the weekly CSV file already exists."""
    output_file = output_dir / f"{year}-W{week:02d}.csv"
    return output_file.exists()


if __name__ == "__main__":
    main()
