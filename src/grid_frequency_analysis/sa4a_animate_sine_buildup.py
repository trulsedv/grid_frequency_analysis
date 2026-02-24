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


def main() -> None:  # noqa: PLR0914
    """Build and save the interactive FFT build-up animation HTML."""
    args = parse_args()
    week_path = Path("data/D03_weekly_1hz_csv") / f"{args.week}.csv"
    y = pd.read_csv(week_path)["Value"].to_numpy(dtype=float)

    n = args.duration_seconds
    s = args.start_second
    segment = y[s : s + n]
    if len(segment) != n:
        msg = "Segment shorter than requested duration"
        raise ValueError(msg)

    t = np.arange(n)
    spectrum = np.fft.rfft(segment)
    freqs = np.fft.rfftfreq(n, d=1.0)

    partial = np.zeros(n, dtype=float)
    partial += spectrum[0].real / n

    frames = [("Measured", segment.copy()), ("DC only", partial.copy())]

    max_k = len(spectrum) - 1
    step = max(1, args.component_step)
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

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=t,
            y=segment,
            mode="lines",
            name="Measured",
            line={"color": "black", "width": 2},
        ),
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

    plotly_frames = []
    for name, yhat in frames:
        plotly_frames.append(
            go.Frame(
                name=name,
                data=[go.Scatter(x=t, y=segment), go.Scatter(x=t, y=yhat)],
                layout=go.Layout(title=f"FFT build-up: {name}"),
            ),
        )

    fig.frames = plotly_frames
    fig.update_layout(
        title="FFT build-up",
        xaxis_title="Second in 1h segment",
        yaxis_title="Frequency (Hz)",
        template="plotly_white",
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
