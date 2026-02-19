"""Plot average spectrum comparison for two weeks."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="results/weekly_stft_avg")
    p.add_argument("--week-a", required=True)
    p.add_argument("--week-b", required=True)
    p.add_argument("--output-dir", default="results/plots")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    d = Path(args.input_dir)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    a = pd.read_csv(d / f"{args.week_a}.csv")
    b = pd.read_csv(d / f"{args.week_b}.csv")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=a["period_s"], y=a["amplitude"], mode="lines", name=args.week_a))
    fig.add_trace(go.Scatter(x=b["period_s"], y=b["amplitude"], mode="lines", name=args.week_b))
    fig.update_layout(
        title=f"Average STFT amplitude: {args.week_a} vs {args.week_b}",
        xaxis_title="Period (s)",
        yaxis_title="Amplitude",
        xaxis_type="log",
        yaxis_type="log",
    )

    html = out / f"avg_spectrum_{args.week_a}_vs_{args.week_b}.html"
    png = out / f"avg_spectrum_{args.week_a}_vs_{args.week_b}.png"
    fig.write_html(html, include_plotlyjs="cdn")
    try:
        fig.write_image(png, width=1600, height=900, scale=2)
    except Exception:
        pass
    print(f"Saved {html}")
    print(f"Saved {png}")


if __name__ == "__main__":
    main()
