"""Count minutes per week where frequency was outside 49.9-50.1 Hz range."""

from pathlib import Path

import pandas as pd


def main():
    """Execute the frequency analysis."""
    # Define paths
    base_dir = Path(__file__).parent.parent.parent
    weekly_csv_dir = base_dir / "data" / "weekly_csv"
    output_file = base_dir / "data" / "minutes_outside_nominal_per_week.csv"

    print("Grid Frequency Analysis: Minutes Outside Nominal Range (49.9-50.1 Hz)")
    print("=" * 70)
    print(f"Input directory: {weekly_csv_dir}")
    print(f"Output file: {output_file}")
    print()

    results = process_weekly_files(str(weekly_csv_dir))
    save_results(results, str(output_file))

    print(f"\nAnalysis complete! Results saved to {output_file}")


def process_weekly_files(weekly_csv_dir):
    """Process weekly CSV files and count minutes outside 49.9-50.1 Hz range."""
    results = []

    # Get all weekly CSV files and sort them
    csv_files = sorted(Path(weekly_csv_dir).glob("*.csv"))

    print(f"Found {len(csv_files)} weekly CSV files to process")

    nominal_lower = 49.9
    nominal_upper = 50.1
    for csv_file in csv_files:
        # Extract week string from filename (e.g., "2021-W39" from "2021-W39.csv")
        filename = csv_file.name
        week_string = filename.replace(".csv", "")

        # Read the CSV file
        df = pd.read_csv(csv_file)

        # Count rows where frequency is outside 49.9-50.1 range
        outside_nominal = df[
            (df["Value"] < nominal_lower) | (df["Value"] > nominal_upper)
        ]

        # Convert seconds to minutes
        seconds_outside = len(outside_nominal)
        minutes_outside = seconds_outside / 60.0

        year, week = week_string.split("-W")
        results.append((int(year), int(week), minutes_outside))

        print(f"Processed {week_string}: {minutes_outside:5.1f} minutes outside nominal range")

    return results


def save_results(results, output_file):
    """Save results to CSV file with summary statistics."""
    # Create DataFrame from results
    df = pd.DataFrame(results, columns=["year", "week", "minutes_outside_nominal"])

    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
