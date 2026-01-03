"""Read all daily CSV files (Helsinki time) and create weekly CSV files (Oslo time)."""
from pathlib import Path

import pandas as pd


def main():
    """Read all daily CSV files (Helsinki time) and create weekly CSV files (Oslo time)."""
    input_dir = Path("data/extracted_csv")
    output_dir = Path("data/weekly_csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    weekly_data = {}
    prev_week_key = None

    csv_files = sorted(input_dir.glob("*.csv"))
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)

        # Convert "Time" column from Helsinki time to Oslo time
        df["Time"] = pd.to_datetime(df["Time"]).dt.tz_localize("Europe/Helsinki").dt.tz_convert("Europe/Oslo")
        df = df.set_index("Time")

        # Resample to 1-second intervals by averaging, but do not add new timestamps
        df = df.groupby(df.index.floor("1s")).mean()

        df["ISO_Year"] = df["Time"].dt.isocalendar().year
        df["ISO_Week"] = df["Time"].dt.isocalendar().week
        for (year, week), week_data in df.groupby(["ISO_Year", "ISO_Week"]):
            week_key = f"{year}-W{week:02d}"

            if prev_week_key and prev_week_key != week_key:
                prev_week_data = pd.concat(weekly_data[prev_week_key], axis=0)
                output_file = output_dir / f"{prev_week_key}.csv"
                prev_week_data.drop(columns=["ISO_Year", "ISO_Week"]).to_csv(output_file, index=False)
                print(f"Saved {output_file.name}", flush=True)
                del weekly_data[prev_week_key]

            if week_key not in weekly_data:
                weekly_data[week_key] = []
            weekly_data[week_key].append(week_data)
            print(f"Added data for {week_key} from {csv_file.name}", flush=True)
            prev_week_key = week_key

    if prev_week_key and prev_week_key in weekly_data:
        last_week_data = pd.concat(weekly_data[prev_week_key], axis=0)
        output_file = output_dir / f"{prev_week_key}.csv"
        last_week_data.drop(columns=["ISO_Year", "ISO_Week"]).to_csv(output_file, index=False)
        print(f"Saved {prev_week_key} to {output_file.name}")
        del weekly_data[prev_week_key]


if __name__ == "__main__":
    main()
