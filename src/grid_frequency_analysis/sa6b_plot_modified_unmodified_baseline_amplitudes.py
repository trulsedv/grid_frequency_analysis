"""Sa6b: Plot unmodified/modified/baseline weekly amplitudes (Ra4)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--week", default="2025-W22")
    parser.add_argument("--unmodified-dir", default="data/D05_weekly_stft_avg_amplitude")
    parser.add_argument("--modified-dir", default="data/Da2_modified_weekly_amplitudes")
    parser.add_argument(
        "--baseline-csv",
        default="data/D06_baseline_pre_cutoff_amplitude/baseline_pre_cutoff.csv",
    )
    parser.add_argument("--output-html", default="results/weekly_amplitude_compare.html")
    parser.add_argument("--output-png", default="results/weekly_amplitude_compare.png")
    return parser.parse_args()


def resolve_week(requested_week: str, unmodified_dir: Path, modified_dir: Path) -> str:
    """Resolve week label, with fallback to latest available intersection."""
    requested_path = unmodified_dir / f"{requested_week}.csv"
    requested_modified = modified_dir / f"{requested_week}.csv"
    if requested_path.exists() and requested_modified.exists():
        return requested_week

    unmodified_weeks = {p.stem for p in unmodified_dir.glob("*.csv")}
    modified_weeks = {p.stem for p in modified_dir.glob("*.csv")}
    candidates = sorted(unmodified_weeks & modified_weeks)
    if not candidates:
        msg = "No overlapping week files found between unmodified and modified directories"
        raise FileNotFoundError(msg)

    fallback = candidates[-1]
    print(f"Requested week {requested_week} not available; using {fallback}")
    return fallback


def main() -> None:
    """Run Sa6b appendix step."""
    args = parse_args()

    week = resolve_week(args.week, Path(args.unmodified_dir), Path(args.modified_dir))
    unmodified = pd.read_csv(Path(args.unmodified_dir) / f"{week}.csv")
    modified = pd.read_csv(Path(args.modified_dir) / f"{week}.csv")
    baseline = pd.read_csv(args.baseline_csv)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=unmodified["period_s"],
            y=unmodified["amplitude"],
            mode="lines",
            name=f"{week} unmodified",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=modified["period_s"],
            y=modified["amplitude_modified"],
            mode="lines",
            name=f"{week} modified",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=baseline["period_s"],
            y=baseline["amplitude"],
            mode="lines",
            name="baseline pre-cutoff",
        ),
    )

    fig.update_layout(
        title=f"Weekly amplitude comparison for {week}",
        xaxis_title="Period (s)",
        yaxis_title="Amplitude",
        xaxis_type="log",
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
