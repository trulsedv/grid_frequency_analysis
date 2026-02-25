"""S10: Plot cumulative minutes outside nominal band with 2025 counterfactual variants."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--d13-csv",
        default="data/D13_minutes_outside_unmodified_weeks/minutes_outside_unmodified_weeks.csv",
    )
    parser.add_argument(
        "--d14-csv",
        default="data/D14_minutes_outside_modified_2025_all_periods/minutes_outside_modified_2025_all_periods.csv",
    )
    parser.add_argument(
        "--d15-csv",
        default=(
            "data/D15_minutes_outside_modified_2025_low_high_periods/"
            "minutes_outside_modified_2025_low_high_periods.csv"
        ),
    )
    parser.add_argument(
        "--d16-csv",
        default="data/D16_minutes_outside_modified_2025_low_periods/minutes_outside_modified_2025_low_periods.csv",
    )
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--output-html", default="results/cumulative_minutes_outside_nominal.html")
    parser.add_argument("--output-png", default="results/cumulative_minutes_outside_nominal.png")
    return parser.parse_args()


def cumulative(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by week and add cumulative minutes column."""
    out = df.sort_values("week").copy()
    out["cumulative_minutes"] = out["minutes_outside_nominal"].cumsum()
    return out


def main() -> None:
    """Run S10 pipeline step."""
    args = parse_args()

    d13 = pd.read_csv(args.d13_csv)
    d14 = cumulative(pd.read_csv(args.d14_csv))
    d15 = cumulative(pd.read_csv(args.d15_csv))
    d16 = cumulative(pd.read_csv(args.d16_csv))

    years = sorted(d13["year"].unique())
    year_frames: dict[int, pd.DataFrame] = {}
    for year in years:
        year_df = d13[d13["year"] == year].copy()
        year_frames[int(year)] = cumulative(year_df)

    target_year = args.year
    measured = year_frames[target_year]

    fig = go.Figure()

    for year, frame in year_frames.items():
        if year == target_year:
            continue
        fig.add_trace(
            go.Scatter(
                x=frame["week"],
                y=frame["cumulative_minutes"],
                mode="lines",
                line={"color": "rgba(120,120,120,0.35)", "width": 1},
                name=f"{year}",
                showlegend=False,
            ),
        )

    fig.add_trace(
        go.Scatter(
            x=measured["week"],
            y=measured["cumulative_minutes"],
            mode="lines",
            line={"color": "black", "width": 2},
            name=f"{target_year} measured",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=d14["week"],
            y=d14["cumulative_minutes"],
            mode="lines",
            line={"color": "red", "width": 2},
            name=f"{target_year} modified (all periods)",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=d16["week"],
            y=d16["cumulative_minutes"],
            mode="lines",
            line={"color": "rgba(0,0,0,0)"},
            showlegend=False,
            hoverinfo="skip",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=measured["week"],
            y=measured["cumulative_minutes"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(30, 144, 255, 0.25)",
            line={"color": "rgba(0,0,0,0)"},
            name="Area: measured vs modified (low periods)",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=d16["week"],
            y=d16["cumulative_minutes"],
            mode="lines",
            line={"color": "rgba(0,0,0,0)"},
            showlegend=False,
            hoverinfo="skip",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=d15["week"],
            y=d15["cumulative_minutes"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(255, 0, 0, 0.2)",
            line={"color": "rgba(0,0,0,0)"},
            name="Area: modified (low) vs modified (low+high)",
        ),
    )

    fig.add_trace(
        go.Scatter(
            x=d15["week"],
            y=d15["cumulative_minutes"],
            mode="lines",
            line={"color": "rgba(0,0,0,0)"},
            showlegend=False,
            hoverinfo="skip",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=d14["week"],
            y=d14["cumulative_minutes"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(120, 120, 120, 0.25)",
            line={"color": "rgba(0,0,0,0)"},
            name="Area: modified (low+high) vs modified (all)",
        ),
    )

    fig.update_layout(
        title="Cumulative minutes outside nominal by year and 2025 counterfactual variants",
        xaxis_title="ISO week",
        yaxis_title="Cumulative minutes outside nominal",
        template="plotly_white",
    )

    output_html = Path(args.output_html)
    output_png = Path(args.output_png)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    fig.write_html(output_html, include_plotlyjs="cdn")
    try:
        fig.write_image(output_png, width=1600, height=900, scale=2)
    except Exception as exc:
        print(f"PNG export failed: {exc}")

    print(f"Saved {output_html}")
    print(f"Saved {output_png}")


if __name__ == "__main__":
    main()
