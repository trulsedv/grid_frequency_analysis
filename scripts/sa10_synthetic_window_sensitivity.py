"""Sa10: Synthetic sinusoid control for STFT window sensitivity.

Build a one-week synthetic signal from fixed-period sinusoids, vary phases across
multiple draws, and compare average STFT amplitudes from 4h vs 23h51m windows.
Also writes one fixed synthetic week CSV plus full amplitude-vs-period figure.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from utils import starts_for_len

SECONDS_PER_WEEK = 7 * 24 * 60 * 60


def main() -> None:
    """Run synthetic phase sweep and export ratio figures/tables."""
    args = parse_args()
    periods = np.array([10.0, 30.0, 120.0, 600.0, 1800.0, 5400.0], dtype=float)

    rng = np.random.default_rng(args.seed)
    draws = []
    rows = []
    for draw_id in range(args.phase_draws):
        phases = rng.uniform(0.0, 2.0 * np.pi, size=len(periods))
        signal = synthesize_signal(periods, phases, SECONDS_PER_WEEK)

        p4, a4 = average_amplitude(signal, args.short_window_seconds, args.overlap_fraction, args.window_type)
        p24, a24 = average_amplitude(signal, args.long_window_seconds, args.overlap_fraction, args.window_type)

        eval_periods, ratio = ratio_at_target_periods(periods, p4, a4, p24, a24)
        draws.append((eval_periods, ratio, draw_id))

        for period_s, value in zip(eval_periods, ratio, strict=True):
            rows.append({"draw": draw_id, "period_s": float(period_s), "ratio_23h51m_over_4h": float(value)})

    out_csv = Path(args.output_csv)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)

    summary = (
        df.groupby("period_s")["ratio_23h51m_over_4h"]
        .agg(["min", "median", "max"])
        .reset_index()
        .sort_values("period_s")
    )
    summary_csv = Path(args.output_summary_csv)
    summary.to_csv(summary_csv, index=False)

    write_draws_plot(draws, Path(args.output_draws_html), Path(args.output_draws_png))
    write_summary_plot(summary, Path(args.output_summary_html), Path(args.output_summary_png))

    save_fixed_week_and_amplitude_plot(
        periods,
        args.fixed_phases,
        args.short_window_seconds,
        args.long_window_seconds,
        args.overlap_fraction,
        args.window_type,
        Path(args.output_fixed_week_csv),
        Path(args.output_fixed_amp_csv),
        Path(args.output_fixed_amp_html),
        Path(args.output_fixed_amp_png),
    )

    print(f"Saved {out_csv}")
    print(f"Saved {summary_csv}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args for synthetic sensitivity experiment."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--phase-draws", type=int, default=8)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--short-window-seconds", type=int, default=14400)
    p.add_argument("--long-window-seconds", type=int, default=85860)
    p.add_argument("--overlap-fraction", type=float, default=0.5)
    p.add_argument("--window-type", choices=["hann", "rect"], default="hann")
    p.add_argument("--fixed-phases", default="0,0,0,0,0,0")
    p.add_argument("--output-csv", default="results/synthetic_window_phase_draws.csv")
    p.add_argument("--output-summary-csv", default="results/synthetic_window_phase_summary.csv")
    p.add_argument("--output-draws-html", default="results/synthetic_window_phase_draws.html")
    p.add_argument("--output-draws-png", default="results/synthetic_window_phase_draws.png")
    p.add_argument("--output-summary-html", default="results/synthetic_window_phase_summary.html")
    p.add_argument("--output-summary-png", default="results/synthetic_window_phase_summary.png")
    p.add_argument("--output-fixed-week-csv", default="results/synthetic_week_signal.csv")
    p.add_argument("--output-fixed-amp-csv", default="results/synthetic_week_window_compare_amplitudes.csv")
    p.add_argument("--output-fixed-amp-html", default="results/synthetic_week_window_compare_amplitudes.html")
    p.add_argument("--output-fixed-amp-png", default="results/synthetic_week_window_compare_amplitudes.png")
    return p.parse_args()


def synthesize_signal(periods: np.ndarray, phases: np.ndarray, length: int) -> np.ndarray:
    """Build synthetic weekly signal from equal-amplitude sinusoids."""
    t = np.arange(length, dtype=float)
    out = np.zeros(length, dtype=float)
    for period_s, phase in zip(periods, phases, strict=True):
        out += np.sin((2.0 * np.pi * t / period_s) + phase)
    return out


def save_fixed_week_and_amplitude_plot(
    periods: np.ndarray,
    fixed_phases: str,
    short_window_seconds: int,
    long_window_seconds: int,
    overlap_fraction: float,
    window_type: str,
    week_csv: Path,
    amp_csv: Path,
    amp_html: Path,
    amp_png: Path,
) -> None:
    """Save one fixed synthetic week CSV and its 4h vs 23h51m amplitude plot."""
    phase_values = np.array([float(x.strip()) for x in fixed_phases.split(",")], dtype=float)
    if len(phase_values) != len(periods):
        raise ValueError("--fixed-phases must have 6 comma-separated values")

    signal = synthesize_signal(periods, phase_values, SECONDS_PER_WEEK)

    week_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"Value": signal}).to_csv(week_csv, index=False)

    p4, a4 = average_amplitude(signal, short_window_seconds, overlap_fraction, window_type)
    p24, a24 = average_amplitude(signal, long_window_seconds, overlap_fraction, window_type)

    common_min = max(p4.min(), p24.min())
    common_max = min(p4.max(), p24.max())
    m4 = (p4 >= common_min) & (p4 <= common_max)
    m24 = (p24 >= common_min) & (p24 <= common_max)

    amp_rows = []
    amp_rows.extend(to_rows("synthetic_fixed", "4h", p4[m4], a4[m4]))
    amp_rows.extend(to_rows("synthetic_fixed", "23h51m", p24[m24], a24[m24]))

    amp_csv.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(amp_rows).to_csv(amp_csv, index=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=p4[m4], y=a4[m4], mode="lines", name="4h", line={"dash": "solid"}))
    fig.add_trace(go.Scatter(x=p24[m24], y=a24[m24], mode="lines", name="23h51m", line={"dash": "dash"}))
    fig.update_layout(
        title="Synthetic week: average amplitude vs period (4h solid, 23h51m dashed)",
        xaxis_title="Period (s)",
        yaxis_title="Average amplitude",
        xaxis_type="log",
        yaxis_type="log",
        template="plotly_white",
    )

    amp_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(amp_html, include_plotlyjs="cdn")
    fig.write_image(amp_png, width=1600, height=900, scale=2)


def average_amplitude(
    values: np.ndarray,
    window_seconds: int,
    overlap_fraction: float,
    window_type: str,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute period grid and average STFT amplitude for one signal."""
    n = window_seconds
    hop = max(1, round(n * (1.0 - overlap_fraction)))
    pad = n // 2

    x_pad = np.pad(values, (pad, pad), mode="reflect")
    starts = starts_for_len(len(x_pad), n, hop)
    window = np.hanning(n) if window_type == "hann" else np.ones(n, dtype=float)

    spec_cols = []
    for s in starts:
        seg = x_pad[s : s + n] * window
        spec_cols.append(np.fft.rfft(seg))

    spec = np.stack(spec_cols, axis=1)
    avg_amp = np.abs(spec).mean(axis=1)

    freqs = np.fft.rfftfreq(n, d=1.0)
    with np.errstate(divide="ignore"):
        periods = np.where(freqs > 0, 1.0 / freqs, np.inf)

    finite = np.isfinite(periods)
    return periods[finite], avg_amp[finite]


def ratio_at_target_periods(
    target_periods: np.ndarray,
    periods_short: np.ndarray,
    amps_short: np.ndarray,
    periods_long: np.ndarray,
    amps_long: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Interpolate both spectra to target periods and compute ratio."""
    log_short = np.log(periods_short)
    log_long = np.log(periods_long)
    log_target = np.log(target_periods)

    a4 = np.interp(log_target, log_short, amps_short)
    a24 = np.interp(log_target, log_long, amps_long)
    ratio = np.divide(a24, a4, out=np.full_like(a24, np.nan), where=a4 > 0)
    return target_periods, ratio


def write_draws_plot(draws: list[tuple[np.ndarray, np.ndarray, int]], out_html: Path, out_png: Path) -> None:
    """Plot phase-draw ratio curves by target period."""
    fig = go.Figure()
    for periods, ratio, draw_id in draws:
        fig.add_trace(
            go.Scatter(x=periods, y=ratio, mode="lines+markers", name=f"draw_{draw_id}"),
        )

    fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Synthetic control: ratio 23h51m/4h across phase draws",
        xaxis_title="Target period (s)",
        yaxis_title="Amplitude ratio",
        xaxis_type="log",
        template="plotly_white",
    )

    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_html, include_plotlyjs="cdn")
    fig.write_image(out_png, width=1400, height=900, scale=2)


def write_summary_plot(summary: pd.DataFrame, out_html: Path, out_png: Path) -> None:
    """Plot min/median/max ratio envelope per target period."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=summary["period_s"],
            y=summary["median"],
            mode="lines+markers",
            name="median",
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=summary["period_s"],
            y=summary["min"],
            mode="lines+markers",
            name="min",
            line={"dash": "dot"},
        ),
    )
    fig.add_trace(
        go.Scatter(
            x=summary["period_s"],
            y=summary["max"],
            mode="lines+markers",
            name="max",
            line={"dash": "dot"},
        ),
    )

    fig.add_hline(y=1.0, line_dash="dash", line_color="gray")
    fig.update_layout(
        title="Synthetic control summary: ratio 23h51m/4h by period",
        xaxis_title="Target period (s)",
        yaxis_title="Amplitude ratio",
        xaxis_type="log",
        template="plotly_white",
    )

    out_html.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out_html, include_plotlyjs="cdn")
    fig.write_image(out_png, width=1400, height=900, scale=2)


def to_rows(week: str, variant: str, periods: np.ndarray, values: np.ndarray) -> list[dict[str, float | str]]:
    """Convert one period series into long-form rows for CSV output."""
    return [
        {"week": week, "variant": variant, "period_s": float(p), "value": float(v)}
        for p, v in zip(periods, values, strict=True)
    ]


if __name__ == "__main__":
    main()
