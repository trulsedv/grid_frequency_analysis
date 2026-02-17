"""Plot cumulative minutes outside nominal frequency range by year."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def main() -> None:
    """Generate cumulative minutes plots and save as HTML/PNG."""
    args = parse_args()
    data_file = Path(args.input_csv)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(data_file)
    years_data = calculate_cumulative_by_year(df)
    fig = create_plot(years_data)

    html_path = output_dir / "cumulative_minutes_by_year.html"
    fig.write_html(html_path, include_plotlyjs="cdn")
    print(f"Saved {html_path}")

    png_path = output_dir / "cumulative_minutes_by_year.png"
    try:
        fig.write_image(png_path, width=1600, height=900, scale=2)
        print(f"Saved {png_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"PNG export failed: {exc}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        default="data/minutes_outside_nominal_per_week.csv",
        help="Path to minutes-per-week CSV",
    )
    parser.add_argument(
        "--output-dir",
        default="results/plots",
        help="Directory for generated plot files",
    )
    return parser.parse_args()


def calculate_cumulative_by_year(df: pd.DataFrame) -> dict[int, pd.DataFrame]:
    """Calculate cumulative minutes for each year."""
    years_data: dict[int, pd.DataFrame] = {}
    for year in sorted(df["year"].unique()):
        year_df = df[df["year"] == year].copy()
        year_df = year_df.sort_values("week")
        year_df["cumulative_minutes"] = year_df["minutes_outside_nominal"].cumsum()
        years_data[int(year)] = year_df
    return years_data


def create_plot(years_data: dict[int, pd.DataFrame]) -> go.Figure:
    """Create plot for cumulative minutes by year."""
    fig = go.Figure()

    for year, data in years_data.items():
        fig.add_trace(
            go.Scatter(
                x=data["week"],
                y=data["cumulative_minutes"],
                name=str(year),
                mode="lines+markers",
            )
        )

    fig.update_layout(
        title="Cumulative Minutes Outside Nominal Frequency Range by Year",
        xaxis_title="Week Number",
        yaxis_title="Cumulative Minutes",
        xaxis={"range": [1, 53]},
    )
    return fig


if __name__ == "__main__":
    main()
