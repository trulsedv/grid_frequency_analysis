"""Sa4a: Animate cumulative FFT reconstruction of a 1-hour signal segment."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def parse_args() -> argparse.Namespace:
    """Parse Sa4a CLI arguments."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--week", default="2025-W15", help="Week file in data/D03_weekly_1hz_csv")
    p.add_argument("--start-second", type=int, default=0, help="Start index in week series")
    p.add_argument("--duration-seconds", type=int, default=3600, help="Segment length (default 1h)")
    p.add_argument("--component-step", type=int, default=20, help="Add every Nth frequency bin")
    p.add_argument("--output", default="results/fft_build_up_animation.html")
    return p.parse_args()


def load_segment(args: argparse.Namespace) -> np.ndarray:
    """Load selected week segment from D03 weekly series."""
    week_path = Path("data/D03_weekly_1hz_csv") / f"{args.week}.csv"
    values = pd.read_csv(week_path)["Value"].to_numpy(dtype=float)
    segment = values[args.start_second : args.start_second + args.duration_seconds]
    if len(segment) != args.duration_seconds:
        msg = "Segment shorter than requested duration"
        raise ValueError(msg)
    return segment


def build_reconstruction_frames(
    segment: np.ndarray,
    component_step: int,
) -> tuple[np.ndarray, list[tuple[str, np.ndarray]]]:
    """Build measured/partial/full reconstruction frames."""
    n = len(segment)
    t = np.arange(n)
    spectrum = np.fft.rfft(segment)
    freqs = np.fft.rfftfreq(n, d=1.0)

    partial = np.zeros(n, dtype=float)
    partial += spectrum[0].real / n
    frames = [("Measured", segment.copy()), ("DC only", partial.copy())]

    max_k = len(spectrum) - 1
    step = max(1, component_step)
    k_values = list(range(1, max_k + 1, step))
    if k_values[-1] != max_k:
        k_values.append(max_k)

    accum = partial.copy()
    included: set[int] = set()
    for k in k_values:
        for j in range(1, k + 1):
            if j in included:
                continue
            phase = np.angle(spectrum[j])
            amp = (2.0 / n) * np.abs(spectrum[j])
            if j == n // 2 and n % 2 == 0:
                amp /= 2.0
            accum += amp * np.cos(2 * np.pi * freqs[j] * t + phase)
            included.add(j)

        period = np.inf if freqs[k] == 0 else 1.0 / freqs[k]
        frames.append((f"DC + periods ≥ {period:.1f}s", accum.copy()))

    frames.append(("Full reconstruction (IFFT)", np.fft.irfft(spectrum, n=n)))
    return t, frames


def build_figure(t: np.ndarray, segment: np.ndarray, frames: list[tuple[str, np.ndarray]]) -> go.Figure:
    """Build animation figure from prepared frames."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(x=t, y=segment, mode="lines", name="Measured", line={"color": "black", "width": 2}),
    )
    fig.add_trace(
        go.Scatter(
            x=t,
            y=frames[1][1],
            mode="lines",
            name="Reconstruction",
            line={"color": "red", "width": 2},
        ),
    )

    fig.frames = [
        go.Frame(
            name=name,
            data=[go.Scatter(x=t, y=segment), go.Scatter(x=t, y=yhat)],
            layout=go.Layout(title=f"FFT build-up: {name}"),
        )
        for name, yhat in frames
    ]
    fig.update_layout(
        title="FFT build-up",
        xaxis_title="Second in 1h segment",
        yaxis_title="Frequency (Hz)",
        template="plotly_white",
    )
    return fig


def main() -> None:
    """Run Sa4a: load segment, build frames, and save animation HTML."""
    args = parse_args()
    segment = load_segment(args)
    t, frames = build_reconstruction_frames(segment, args.component_step)
    fig = build_figure(t, segment, frames)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
