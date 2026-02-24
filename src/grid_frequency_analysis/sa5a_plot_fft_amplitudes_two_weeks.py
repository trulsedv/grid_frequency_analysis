"""Sa5a: Plot average amplitude spectra for two selected weeks."""

from __future__ import annotations

import argparse
from contextlib import suppress
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def parse_args() -> argparse.Namespace:
    """Parse Sa5a CLI arguments."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="data/D05_weekly_stft_avg_amplitude")
    p.add_argument("--week-a", default="2024-W15")
    p.add_argument("--week-b", default="2025-W15")
    p.add_argument("--output-html", default="results/fft_amplitudes_two_weeks.html")
    p.add_argument("--output-png", default="results/fft_amplitudes_two_weeks.png")
    return p.parse_args()


def main() -> None:
    """Render and save Sa5a comparison plot as HTML and PNG."""
    args = parse_args()
    input_dir = Path(args.input_dir)

    week_a = pd.read_csv(input_dir / f"{args.week_a}.csv")
    week_b = pd.read_csv(input_dir / f"{args.week_b}.csv")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=week_a["period_s"], y=week_a["amplitude"], mode="lines", name=args.week_a))
    fig.add_trace(go.Scatter(x=week_b["period_s"], y=week_b["amplitude"], mode="lines", name=args.week_b))
    fig.update_layout(
        title=f"Average STFT amplitude: {args.week_a} vs {args.week_b}",
        xaxis_title="Period (s)",
        yaxis_title="Amplitude",
        xaxis_type="log",
        yaxis_type="log",
    )

    html = Path(args.output_html)
    png = Path(args.output_png)
    html.parent.mkdir(parents=True, exist_ok=True)

    fig.write_html(html, include_plotlyjs="cdn")
    with suppress(ValueError, RuntimeError):
        fig.write_image(png, width=1600, height=900, scale=2)

    print(f"Saved {html}")
    print(f"Saved {png}")


if __name__ == "__main__":
    main()
