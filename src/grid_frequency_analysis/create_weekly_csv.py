"""Read all daily CSV files (Helsinki time) and create weekly CSV files (Oslo time)."""
from pathlib import Path

import pandas as pd


def main():
    """Read all daily CSV files (Helsinki time) and create weekly CSV files (Oslo time)."""
    input_dir = Path("data/extracted_csv")
    output_dir = Path("data/weekly_csv")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted(input_dir.glob("*.csv"))
    for csv_file in csv_files:
        df = pd.read_csv(csv_file)
        df["Time"] = pd.to_datetime(df["Time"]).dt.tz_localize("Europe/Helsinki").dt.tz_convert("Europe/Oslo")

        df["ISO_Year"] = df["Time"].dt.isocalendar().year
        df["ISO_Week"] = df["Time"].dt.isocalendar().week
        for (year, week), week_data in df.groupby(["ISO_Year", "ISO_Week"]):
            week_key = f"{year}-W{week:02d}"
            output_file = output_dir / f"{week_key}.csv"
            week_data.drop(columns=["ISO_Year", "ISO_Week"]).to_csv(
                output_file,
                mode="a",
                header=not output_file.exists(),
                index=False,
            )
            print(f"{csv_file.name} saved to {output_file.name}")


if __name__ == "__main__":
    main()
