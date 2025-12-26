"""Plot cumulative minutes outside nominal frequency range by year."""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def main():
    """Execute the plotting analysis."""
    filepath = "data/minutes_outside_nominal_per_week.csv"
    data_file = Path(filepath)

    df = pd.read_csv(data_file)
    years_data = calculate_cumulative_by_year(df)
    create_plots(years_data)


def calculate_cumulative_by_year(df):
    """Calculate cumulative minutes for each year."""
    years_data = {}
    for year in df["year"].unique():
        year_df = df[df["year"] == year].copy()
        year_df = year_df.sort_values("week")
        year_df["cumulative_minutes"] = year_df["minutes_outside_nominal"].cumsum()
        years_data[year] = year_df
    return years_data


def create_plots(years_data):
    """Create plots for cumulative minutes by year."""
    fig = go.Figure()

    for year, data in years_data.items():
        fig.add_trace(go.Scatter(
            x=data["week"],
            y=data["cumulative_minutes"],
            name=str(year),
            mode="lines+markers",
        ))

    fig.update_layout(
        title="Cumulative Minutes Outside Nominal Frequency Range by Year",
        xaxis_title="Week Number",
        yaxis_title="Cumulative Minutes",
        xaxis={"range": [1, 53]},
    )

    fig.show()


if __name__ == "__main__":
    main()
