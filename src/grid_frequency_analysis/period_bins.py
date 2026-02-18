"""Period-bin configuration for spectral analysis and attribution."""

from dataclasses import dataclass


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


def period_to_frequency_hz(period_s: float) -> float:
    """Convert period in seconds to frequency in Hz (cycles per second)."""
    if period_s <= 0:
        raise ValueError("period_s must be positive")
    return 1.0 / period_s


def bin_to_frequency_range_hz(bin_cfg: PeriodBin) -> tuple[float, float]:
    """Return (f_min, f_max) Hz for a period bin.

    Longer periods map to lower frequencies.
    """
    f_low = period_to_frequency_hz(bin_cfg.period_max_s)
    f_high = period_to_frequency_hz(bin_cfg.period_min_s)
    return (f_low, f_high)
