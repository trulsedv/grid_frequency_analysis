"""Shared utility definitions used across pipeline and appendix scripts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from pathlib import Path

NORMALIZATION_EPSILON = 1e-12


@dataclass(frozen=True)
class PeriodBin:
    """Named period range in seconds."""

    name: str
    period_min_s: float
    period_max_s: float


DEFAULT_PERIOD_BINS: tuple[PeriodBin, ...] = (
    PeriodBin("fast_sub_primary_5s_to_30s", 5.0, 30.0),
    PeriodBin("primary_local_control_30s_to_2m", 30.0, 120.0),
    PeriodBin("midrange_2m_to_15m", 120.0, 900.0),
    PeriodBin("balancing_15m_to_2h", 900.0, 7200.0),
    PeriodBin("slow_over_2h_to_12h", 7200.0, 43200.0),
)


def parse_week_label(week_label: str) -> tuple[int, int]:
    """Parse ISO week label (YYYY-Www) to a sortable tuple."""
    year_txt, week_txt = week_label.split("-W")
    return int(year_txt), int(week_txt)


def starts_for_len(total_len: int, n: int, hop: int) -> list[int]:
    """Return frame start indices and include a tail-aligned final frame."""
    starts = list(range(0, total_len - n + 1, hop))
    if starts[-1] != total_len - n:
        starts.append(total_len - n)
    return starts


def decode_stft_overlap_add(  # noqa: PLR0913, PLR0917
    stft_frames_bins: np.ndarray,
    n: int,
    hop: int,
    padded_len: int,
    orig_len: int,
    pad: int,
    *,
    normalization_epsilon: float = NORMALIZATION_EPSILON,
) -> np.ndarray:
    """Reconstruct a time-domain signal from STFT frames using overlap-add."""
    window = np.hanning(n)
    starts = starts_for_len(padded_len, n, hop)

    out = np.zeros(padded_len)
    norm = np.zeros(padded_len)
    for index, start in enumerate(starts):
        segment = np.fft.irfft(stft_frames_bins[index], n=n).real
        out[start : start + n] += segment * window
        norm[start : start + n] += window * window

    valid = norm > normalization_epsilon
    out[valid] /= norm[valid]
    out[~valid] = 0.0
    return out[pad : pad + orig_len]


def resolve_week_with_fallback(requested_week: str, *directories: Path) -> str:
    """Resolve requested week or fall back to latest week present in all dirs."""
    if all((directory / f"{requested_week}.csv").exists() for directory in directories):
        return requested_week

    candidates: set[str] | None = None
    for directory in directories:
        weeks = {path.stem for path in directory.glob("*.csv") if not path.name.endswith("_meta.csv")}
        candidates = weeks if candidates is None else (candidates & weeks)

    if not candidates:
        msg = "No overlapping week files found across required directories"
        raise FileNotFoundError(msg)

    fallback = max(candidates)
    print(f"Requested week {requested_week} not available; using {fallback}")
    return fallback
