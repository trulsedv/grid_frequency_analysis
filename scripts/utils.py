"""Shared utility definitions used across pipeline and appendix scripts."""

from __future__ import annotations

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
