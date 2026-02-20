"""Create an animation showing cumulative FFT reconstruction of 1 hour signal.

Frames:
1) measured signal
2) DC offset only
3+) DC + increasingly shorter-period sine components (with phase)
Final frame: full reconstruction (all components)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--week", default="2025-W15", help="Week file in data/weekly_csv")
    p.add_argument("--start-second", type=int, default=0, help="Start index in week series")
    p.add_argument("--duration-seconds", type=int, default=3600, help="Segment length (default 1h)")
    p.add_argument("--component-step", type=int, default=20, help="Add every Nth frequency bin for intermediate frames")
    p.add_argument("--output", default="results/animations/fft_build_up_1h.html")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    week_path = Path("data/weekly_csv") / f"{args.week}.csv"
    y = pd.read_csv(week_path)["Value"].to_numpy(dtype=float)

    n = args.duration_seconds
    s = args.start_second
    segment = y[s : s + n]
    if len(segment) != n:
        raise ValueError("Segment shorter than requested duration")

    t = np.arange(n)
    Y = np.fft.rfft(segment)
    freqs = np.fft.rfftfreq(n, d=1.0)

    # Build partial reconstructions.
    partial = np.zeros(n, dtype=float)
    partial += (Y[0].real / n)  # DC component

    frames = []
    frames.append(("Measured", segment.copy()))
    frames.append(("DC only", partial.copy()))

    # Add components from longest period to shorter period => from low freq to high freq.
    # Skip k=0 (DC).
    max_k = len(Y) - 1
    k_values = list(range(1, max_k + 1, max(1, args.component_step)))
    if k_values[-1] != max_k:
        k_values.append(max_k)

    accum = partial.copy()
    included = set()
    for k in k_values:
        # Add missing bins up to k, preserving full phase information.
        for j in range(1, k + 1):
            if j in included:
                continue
            phi = np.angle(Y[j])
            amp = (2.0 / n) * np.abs(Y[j])
            if j == n // 2 and n % 2 == 0:
                amp = amp / 2.0
            accum += amp * np.cos(2 * np.pi * freqs[j] * t + phi)
            included.add(j)

        period = np.inf if freqs[k] == 0 else 1.0 / freqs[k]
        frames.append((f"DC + periods ≥ {period:.1f}s", accum.copy()))

    # Final exact inverse frame
    final = np.fft.irfft(Y, n=n)
    frames.append(("Full reconstruction (IFFT)", final))

    # Build plotly animation
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=t, y=segment, mode="lines", name="Measured", line=dict(color="black", width=2)))
    fig.add_trace(go.Scatter(x=t, y=frames[1][1], mode="lines", name="Reconstruction", line=dict(color="red", width=2)))

    plotly_frames = []
    for name, yhat in frames:
        plotly_frames.append(
            go.Frame(
                name=name,
                data=[
                    go.Scatter(x=t, y=segment),
                    go.Scatter(x=t, y=yhat),
                ],
                layout=go.Layout(title=f"FFT build-up: {name}")
            )
        )

    fig.frames = plotly_frames
    sliders = [{
        "steps": [
            {
                "method": "animate",
                "label": fr.name,
                "args": [[fr.name], {"mode": "immediate", "frame": {"duration": 0, "redraw": True}, "transition": {"duration": 0}}],
            }
            for fr in plotly_frames
        ],
        "x": 0.1,
        "len": 0.88,
    }]

    fig.update_layout(
        title="FFT build-up",
        xaxis_title="Second in 1h segment",
        yaxis_title="Frequency (Hz)",
        updatemenus=[{
            "type": "buttons",
            "buttons": [
                {"label": "Play", "method": "animate", "args": [None, {"frame": {"duration": 200, "redraw": True}, "fromcurrent": True}]},
                {"label": "Pause", "method": "animate", "args": [[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]},
            ],
            "x": 0.0,
            "y": 1.15,
        }],
        sliders=sliders,
        template="plotly_white",
    )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
