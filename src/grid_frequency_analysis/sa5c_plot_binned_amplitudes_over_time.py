"""Sa5c: Plot binned amplitudes over time (Ra3)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

from grid_frequency_analysis.utils import DEFAULT_PERIOD_BINS


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-csv",
        default="data/Da1_binned_weekly_amplitudes/binned_weekly_amplitudes.csv",
    )
    parser.add_argument("--output-html", default="results/binned_amplitudes_over_time.html")
    parser.add_argument("--output-png", default="results/binned_amplitudes_over_time.png")
    return parser.parse_args()


def main() -> None:
    """Run Sa5c appendix step."""
    args = parse_args()

    df = pd.read_csv(args.input_csv)
    fig = go.Figure()

    for period_bin in DEFAULT_PERIOD_BINS:
        fig.add_trace(
            go.Scatter(
                x=df["week"],
                y=df[period_bin.name],
                mode="lines+markers",
                name=period_bin.name,
            ),
        )

    fig.update_layout(
        title="Binned weekly amplitudes over time",
        xaxis_title="ISO week",
        yaxis_title="Mean amplitude (log scale)",
        yaxis_type="log",
        template="plotly_white",
    )

    output_html = Path(args.output_html)
    output_png = Path(args.output_png)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    fig.write_html(output_html, include_plotlyjs="cdn")
    try:
        fig.write_image(output_png, width=1600, height=900, scale=2)
    except Exception as exc:  # noqa: BLE001
        print(f"PNG export failed: {exc}")

    print(f"Saved {output_html}")
    print(f"Saved {output_png}")


if __name__ == "__main__":
    main()
