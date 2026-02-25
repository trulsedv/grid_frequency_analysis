"""S10: Plot cumulative minutes outside nominal band with 2025 counterfactual variants."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
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


@dataclass
class S10Data:
    """Prepared cumulative frames used by S10 plotting helpers."""

    year_frames: dict[int, pd.DataFrame]
    d14: pd.DataFrame
    d15: pd.DataFrame
    d16: pd.DataFrame


def load_cumulative_inputs(args: argparse.Namespace) -> S10Data:
    """Load D13..D16 and return cumulative frames."""
    d13 = pd.read_csv(args.d13_csv)
    d14 = cumulative(pd.read_csv(args.d14_csv))
    d15 = cumulative(pd.read_csv(args.d15_csv))
    d16 = cumulative(pd.read_csv(args.d16_csv))

    year_frames: dict[int, pd.DataFrame] = {}
    for year in sorted(d13["year"].unique()):
        year_frames[int(year)] = cumulative(d13[d13["year"] == year].copy())

    return S10Data(year_frames=year_frames, d14=d14, d15=d15, d16=d16)


def add_historical_traces(fig: go.Figure, year_frames: dict[int, pd.DataFrame], target_year: int) -> None:
    """Add gray historical year traces."""
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


def add_counterfactual_traces(fig: go.Figure, measured: pd.DataFrame, data: S10Data, target_year: int) -> None:
    """Add measured/counterfactual lines and decomposition area fills."""
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
            x=data.d14["week"],
            y=data.d14["cumulative_minutes"],
            mode="lines",
            line={"color": "red", "width": 2},
            name=f"{target_year} modified (all periods)",
        ),
    )

    for x1, y1, x2, y2, fill_color, label in [
        (
            data.d16["week"],
            data.d16["cumulative_minutes"],
            measured["week"],
            measured["cumulative_minutes"],
            "rgba(30, 144, 255, 0.25)",
            "Area: measured vs modified (low periods)",
        ),
        (
            data.d16["week"],
            data.d16["cumulative_minutes"],
            data.d15["week"],
            data.d15["cumulative_minutes"],
            "rgba(255, 0, 0, 0.2)",
            "Area: modified (low) vs modified (low+high)",
        ),
        (
            data.d15["week"],
            data.d15["cumulative_minutes"],
            data.d14["week"],
            data.d14["cumulative_minutes"],
            "rgba(120, 120, 120, 0.25)",
            "Area: modified (low+high) vs modified (all)",
        ),
    ]:
        fig.add_trace(
            go.Scatter(x=x1, y=y1, mode="lines", line={"color": "rgba(0,0,0,0)"}, showlegend=False, hoverinfo="skip"),
        )
        fig.add_trace(
            go.Scatter(
                x=x2,
                y=y2,
                mode="lines",
                fill="tonexty",
                fillcolor=fill_color,
                line={"color": "rgba(0,0,0,0)"},
                name=label,
            ),
        )


def save_figure(fig: go.Figure, output_html: Path, output_png: Path) -> None:
    """Save HTML and PNG outputs."""
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_png.parent.mkdir(parents=True, exist_ok=True)

    fig.write_html(output_html, include_plotlyjs="cdn")
    try:
        fig.write_image(output_png, width=1600, height=900, scale=2)
    except (RuntimeError, ValueError) as exc:
        print(f"PNG export failed: {exc}")

    print(f"Saved {output_html}")
    print(f"Saved {output_png}")


def main() -> None:
    """Run S10: load metrics, build figure, and save outputs."""
    args = parse_args()
    data = load_cumulative_inputs(args)
    measured = data.year_frames[args.year]

    fig = go.Figure()
    add_historical_traces(fig, data.year_frames, args.year)
    add_counterfactual_traces(fig, measured, data, args.year)

    fig.update_layout(
        title="Cumulative minutes outside nominal by year and 2025 counterfactual variants",
        xaxis_title="ISO week",
        yaxis_title="Cumulative minutes outside nominal",
        template="plotly_white",
    )

    save_figure(fig, Path(args.output_html), Path(args.output_png))


if __name__ == "__main__":
    main()
