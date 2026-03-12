"""Sa9: Compare weekly STFT average amplitudes for two window sizes on 3 weeks."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from utils import starts_for_len


def main() -> None:
    """Run 3-week STFT window comparison and write plots/CSVs."""
    args = parse_args()

    weeks = [w.strip() for w in args.weeks.split(",") if w.strip()]
    short_window = args.short_window_seconds
    long_window = args.long_window_seconds

    amplitudes_rows: list[dict[str, float | str]] = []
    ratio_rows: list[dict[str, float | str]] = []
    amplitude_series: list[tuple[np.ndarray, np.ndarray, str, str]] = []
    ratio_series: list[tuple[np.ndarray, np.ndarray, str]] = []

    for week in weeks:
        path = Path(args.input_dir) / f"{week}.csv"
        values = pd.read_csv(path)["Value"].to_numpy(dtype=float)

        short_periods, short_amp = average_amplitude(values, short_window, args.overlap_fraction)
        long_periods, long_amp = average_amplitude(values, long_window, args.overlap_fraction)

        amplitude_series.append((short_periods, short_amp, week, "solid"))
        amplitude_series.append((long_periods, long_amp, week, "dash"))

        common_periods, ratio = ratio_on_short_grid(short_periods, short_amp, long_periods, long_amp)
        ratio_series.append((common_periods, ratio, week))

        amplitudes_rows.extend(to_rows(week, "4h", short_periods, short_amp))
        amplitudes_rows.extend(to_rows(week, "23h51m", long_periods, long_amp))
        ratio_rows.extend(to_rows(week, "23h51m_over_4h", common_periods, ratio))

    amp_csv = Path(args.output_amplitude_csv)
    ratio_csv = Path(args.output_ratio_csv)
    amp_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(amplitudes_rows).to_csv(amp_csv, index=False)
    pd.DataFrame(ratio_rows).to_csv(ratio_csv, index=False)

    write_amplitude_plot(amplitude_series, short_window, long_window, Path(args.output_amplitude_html), Path(args.output_amplitude_png))
    write_ratio_plot(ratio_series, Path(args.output_ratio_html), Path(args.output_ratio_png))

    print(f"Saved {amp_csv}")
    print(f"Saved {ratio_csv}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for window comparison."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", default="data/D03_weekly_1hz_csv")
    p.add_argument("--weeks", default="2024-W05,2024-W23,2024-W45")
    p.add_argument("--short-window-seconds", type=int, default=14400)
    p.add_argument("--long-window-seconds", type=int, default=85860)
    p.add_argument("--overlap-fraction", type=float, default=0.5)
    p.add_argument("--output-amplitude-csv", default="results/window_compare_amplitudes.csv")
    p.add_argument("--output-ratio-csv", default="results/window_compare_ratio.csv")
    p.add_argument("--output-amplitude-html", default="results/window_compare_amplitudes.html")
    p.add_argument("--output-amplitude-png", default="results/window_compare_amplitudes.png")
    p.add_argument("--output-ratio-html", default="results/window_compare_ratio.html")
    p.add_argument("--output-ratio-png", default="results/window_compare_ratio.png")
    return p.parse_args()


def average_amplitude(values: np.ndarray, window_seconds: int, overlap_fraction: float) -> tuple[np.ndarray, np.ndarray]:
    """Compute period grid and average STFT amplitude for one weekly signal."""
    n = window_seconds
    hop = max(1, round(n * (1.0 - overlap_fraction)))
    pad = n // 2

    x_pad = np.pad(values, (pad, pad), mode="reflect")
    starts = starts_for_len(len(x_pad), n, hop)
    window = np.hanning(n)

    spec_cols: list[np.ndarray] = []
    for s in starts:
        seg = x_pad[s : s + n] * window
        spec_cols.append(np.fft.rfft(seg))

    spec = np.stack(spec_cols, axis=1)
    amps = np.abs(spec)
    avg_amp = amps.mean(axis=1)

    freqs = np.fft.rfftfreq(n, d=1.0)
    with np.errstate(divide="ignore"):
        periods = np.where(freqs > 0, 1.0 / freqs, np.inf)

    finite = np.isfinite(periods)
    return periods[finite], avg_amp[finite]


def ratio_on_short_grid(
    short_periods: np.ndarray,
    short_amp: np.ndarray,
    long_periods: np.ndarray,
    long_amp: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Interpolate long-window amplitudes to short-window period grid and form ratio."""
    min_p = max(short_periods.min(), long_periods.min())
    max_p = min(short_periods.max(), long_periods.max())
    mask = (short_periods >= min_p) & (short_periods <= max_p)

    ref_p = short_periods[mask]
    ref_amp = short_amp[mask]

    # Ignore near-zero denominator bins where tiny absolute amplitudes create unstable ratios.
    amp_floor = np.quantile(ref_amp, 0.01)
    stable = ref_amp > amp_floor

    log_long_p = np.log(long_periods)
    log_ref_p = np.log(ref_p)
    interp_long_amp = np.interp(log_ref_p, log_long_p, long_amp)
    ratio = np.divide(interp_long_amp, ref_amp, out=np.full_like(ref_amp, np.nan), where=stable)

    return ref_p[stable], ratio[stable]


def write_amplitude_plot(
    series: list[tuple[np.ndarray, np.ndarray, str, str]],
    short_window: int,
    long_window: int,
    out_html: Path,
    out_png: Path,
) -> None:
    """Write log-log amplitude comparison figure for the selected weeks."""
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
    week_colors: dict[str, str] = {}

    for periods, amplitudes, week, dash in series:
        if week not in week_colors:
            week_colors[week] = colors[len(week_colors) % len(colors)]
        label = f"{week} {'4h' if dash == 'solid' else '23h51m'}"
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=amplitudes,
                mode="lines",
                name=label,
                line={"dash": dash, "color": week_colors[week]},
            ),
        )

    fig.update_layout(
        title=(
            f"Weekly STFT average amplitude by period: {short_window}s (solid) vs {long_window}s (dashed)"
        ),
        xaxis_title="Period (s)",
        yaxis_title="Average amplitude",
        xaxis_type="log",
        yaxis_type="log",
        template="plotly_white",
    )

    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_html, include_plotlyjs="cdn")
    fig.write_image(out_png, width=1600, height=900, scale=2)


def write_ratio_plot(
    series: list[tuple[np.ndarray, np.ndarray, str]],
    out_html: Path,
    out_png: Path,
) -> None:
    """Write ratio-vs-period figure (23h51m/4h) for selected weeks."""
    fig = go.Figure()
    colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]

    for idx, (periods, ratio, week) in enumerate(series):
        fig.add_trace(
            go.Scatter(
                x=periods,
                y=ratio,
                mode="lines",
                name=week,
                line={"color": colors[idx % len(colors)]},
            ),
        )

    fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Amplitude ratio by period: 23h51m window / 4h window",
        xaxis_title="Period (s)",
        yaxis_title="Amplitude ratio",
        xaxis_type="log",
        yaxis_type="log",
        template="plotly_white",
    )

    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_html, include_plotlyjs="cdn")
    fig.write_image(out_png, width=1600, height=900, scale=2)


def to_rows(week: str, variant: str, periods: np.ndarray, values: np.ndarray) -> list[dict[str, float | str]]:
    """Convert one period series into long-form rows for CSV output."""
    return [
        {"week": week, "variant": variant, "period_s": float(p), "value": float(v)}
        for p, v in zip(periods, values, strict=True)
    ]


if __name__ == "__main__":
    main()
