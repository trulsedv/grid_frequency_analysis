"""Sa8b: Plot measured/reproduced/modified signals for a selected week (Ra5)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from utils import resolve_week_with_fallback


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", default="2025-W22")
    parser.add_argument("--measured-dir", default="data/D03_weekly_1hz_csv")
    parser.add_argument("--reproduced-dir", default="data/Da3_reproduced_weekly_1hz")
    parser.add_argument("--modified-dir", default="data/D11_modified_2025_weekly_1hz_low_high_periods")
    parser.add_argument("--output-html", default="results/week_signal_compare.html")
    parser.add_argument("--output-png", default="results/week_signal_compare.png")
    return parser.parse_args()


def main() -> None:
    """Run Sa8b appendix step."""
    args = parse_args()

    measured_dir = Path(args.measured_dir)
    reproduced_dir = Path(args.reproduced_dir)
    modified_dir = Path(args.modified_dir)

    week = resolve_week_with_fallback(args.week, measured_dir, reproduced_dir, modified_dir)

    measured = pd.read_csv(measured_dir / f"{week}.csv")["Value"].to_numpy(dtype=float)
    reproduced = pd.read_csv(reproduced_dir / f"{week}.csv")["Value"].to_numpy(dtype=float)
    modified = pd.read_csv(modified_dir / f"{week}.csv")["Value"].to_numpy(dtype=float)

    n = min(len(measured), len(reproduced), len(modified))
    x = list(range(n))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x,
            y=measured[:n],
            mode="lines",
            line={"color": "rgba(0,0,0,0.45)", "width": 1.2},
            name="Measured",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=reproduced[:n],
            mode="lines",
            line={"color": "rgba(0,100,255,0.45)", "width": 1.2},
            name="Reproduced from STFT",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=x,
            y=modified[:n],
            mode="lines",
            line={"color": "rgba(255,0,0,0.45)", "width": 1.2},
            name="Reproduced from modified STFT",
        ),
    )

    fig.update_layout(
        title=f"Week signal comparison ({week})",
        xaxis_title="Second index",
        yaxis_title="Frequency (Hz)",
        template="plotly_white",
    )

    output_html = Path(args.output_html)
    output_png = Path(args.output_png)
    output_html.parent.mkdir(parents=True, exist_ok=True)

    fig.write_html(output_html, include_plotlyjs="cdn")
    try:
        fig.write_image(output_png, width=1600, height=900, scale=2)
    except Exception as exc:
        print(f"PNG export failed: {exc}")

    print(f"Saved {output_html}")
    print(f"Saved {output_png}")


if __name__ == "__main__":
    main()
