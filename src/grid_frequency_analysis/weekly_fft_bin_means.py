"""Aggregate weekly FFT spectra into mean amplitude per period bin and plot them."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

if __package__ is None or __package__ == "":
    # Allow running as `python src/grid_frequency_analysis/weekly_fft_bin_means.py`
    sys.path.append(str(Path(__file__).resolve().parents[1]))

from grid_frequency_analysis.period_bins import DEFAULT_PERIOD_BINS, PeriodBin


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/weekly_fft", help="Directory with weekly FFT CSV files")
    parser.add_argument(
        "--output-csv",
        default="data/weekly_fft_bin_means.csv",
        help="Output CSV path (week rows, bin columns)",
    )
    parser.add_argument(
        "--plot-output-dir",
        default="data/plots",
        help="Directory for plot outputs (HTML and PNG)",
    )
    parser.add_argument(
        "--min-period-s",
        type=float,
        default=0.0,
        help="Optional lower period cutoff before binning",
    )
    parser.add_argument(
        "--max-period-s",
        type=float,
        default=0.0,
        help="Optional upper period cutoff before binning (0 = no cutoff)",
    )
    return parser.parse_args()


def main() -> None:
    """Run weekly FFT bin aggregation and plot generation."""
    args = parse_args()

    input_dir = Path(args.input_dir)
    output_csv = Path(args.output_csv)
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    plot_dir = Path(args.plot_output_dir)
    plot_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for fft_file in sorted(input_dir.glob("*.csv")):
        week_name = fft_file.stem
        try:
            spectrum = pd.read_csv(fft_file)
        except pd.errors.EmptyDataError:
            continue

        if not {"period_s", "amplitude"}.issubset(spectrum.columns):
            continue

        spectrum = filter_period_range(spectrum, args.min_period_s, args.max_period_s)
        if spectrum.empty:
            continue

        year, week = parse_week_name(week_name)
        row = {"week": week_name, "year": year, "iso_week": week}

        for bin_cfg in DEFAULT_PERIOD_BINS:
            mask = (
                (spectrum["period_s"] >= bin_cfg.period_min_s)
                & (spectrum["period_s"] <= bin_cfg.period_max_s)
            )
            row[bin_cfg.name] = float(spectrum.loc[mask, "amplitude"].mean()) if mask.any() else float("nan")

        rows.append(row)

    if not rows:
        raise RuntimeError("No FFT weekly files could be aggregated into bins")

    out_df = pd.DataFrame(rows).sort_values(["year", "iso_week"])
    out_df.to_csv(output_csv, index=False)
    print(f"Saved {output_csv}")

    make_plot(out_df, DEFAULT_PERIOD_BINS, plot_dir)


def filter_period_range(df: pd.DataFrame, min_period_s: float, max_period_s: float) -> pd.DataFrame:
    """Apply optional period filters before bin aggregation."""
    out = df.copy()
    if min_period_s > 0:
        out = out[out["period_s"] >= min_period_s]
    if max_period_s > 0:
        out = out[out["period_s"] <= max_period_s]
    return out


def parse_week_name(week_name: str) -> tuple[int, int]:
    """Parse `YYYY-Www` into integers."""
    year_txt, week_txt = week_name.split("-W")
    return int(year_txt), int(week_txt)


def make_plot(df: pd.DataFrame, bins: tuple[PeriodBin, ...], plot_dir: Path) -> None:
    """Create line plot for per-bin weekly mean amplitudes."""
    fig = go.Figure()

    x = df["week"]
    for bin_cfg in bins:
        fig.add_trace(
            go.Scatter(
                x=x,
                y=df[bin_cfg.name],
                mode="lines+markers",
                name=bin_cfg.name,
            )
        )

    fig.update_layout(
        title="Weekly mean FFT amplitude by period bin",
        xaxis_title="ISO Week",
        yaxis_title="Mean amplitude",
        legend_title="Period bin",
    )

    html_path = plot_dir / "weekly_fft_bin_means.html"
    png_path = plot_dir / "weekly_fft_bin_means.png"

    fig.write_html(html_path, include_plotlyjs="cdn")
    print(f"Saved {html_path}")

    try:
        fig.write_image(png_path, width=1600, height=900, scale=2)
        print(f"Saved {png_path}")
    except Exception as exc:  # noqa: BLE001
        print(f"PNG export failed: {exc}")


if __name__ == "__main__":
    main()
