"""Sensitivity scan for filter-bank counterfactual attribution outputs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from utils import DEFAULT_PERIOD_BINS, parse_week_label

NOMINAL_LOW_HZ = 49.9
NOMINAL_HIGH_HZ = 50.1
RMS_EPSILON = 1e-12


@dataclass(frozen=True)
class BandParts:
    mean: float
    parts: dict[str, np.ndarray]
    residual: np.ndarray


@dataclass(frozen=True)
class Scenario:
    name: str
    cutoff_week: str
    baseline_stat: str = "mean"  # mean | median
    clip_min: float | None = None
    clip_max: float | None = None


def main() -> None:
    weekly_dir = Path("data/D03_weekly_1hz_csv")
    weekly_band_rms = pd.read_csv("data/Db1_weekly_band_rms.csv")

    week_files_2025 = sorted([p for p in weekly_dir.glob("2025-W*.csv")])
    decomposed_2025 = {p.stem: decompose_week(pd.read_csv(p)["Value"].to_numpy(dtype=float)) for p in week_files_2025}

    unmodified_total = total_minutes_outside({k: pd.read_csv(weekly_dir / f"{k}.csv")["Value"].to_numpy(dtype=float) for k in decomposed_2025})

    scenarios = [
        Scenario("base_mean_cutoff_2024W22", "2024-W22", "mean", None, None),
        Scenario("cutoff_early_2024W18", "2024-W18", "mean", None, None),
        Scenario("cutoff_late_2024W26", "2024-W26", "mean", None, None),
        Scenario("median_cutoff_2024W22", "2024-W22", "median", None, None),
        Scenario("clip_0.8_1.2", "2024-W22", "mean", 0.8, 1.2),
        Scenario("clip_0.6_1.4", "2024-W22", "mean", 0.6, 1.4),
        Scenario("median_clip_0.8_1.2", "2024-W22", "median", 0.8, 1.2),
    ]

    rows: list[dict[str, float | str]] = []
    for s in scenarios:
        baseline = compute_baseline(weekly_band_rms, s.cutoff_week, s.baseline_stat)
        all_signals, lowhigh_signals, low_signals = reconstruct_for_scenario(decomposed_2025, baseline, s)

        all_total = total_minutes_outside(all_signals)
        lowhigh_total = total_minutes_outside(lowhigh_signals)
        low_total = total_minutes_outside(low_signals)

        rows.append(
            {
                "scenario": s.name,
                "cutoff_week": s.cutoff_week,
                "baseline_stat": s.baseline_stat,
                "clip_min": np.nan if s.clip_min is None else s.clip_min,
                "clip_max": np.nan if s.clip_max is None else s.clip_max,
                "minutes_2025_unmodified": unmodified_total,
                "minutes_2025_modified_all": all_total,
                "minutes_2025_modified_low_high": lowhigh_total,
                "minutes_2025_modified_low": low_total,
                "delta_all_vs_unmodified": all_total - unmodified_total,
                "delta_low_high_vs_unmodified": lowhigh_total - unmodified_total,
                "delta_low_vs_unmodified": low_total - unmodified_total,
                "component_low": low_total - unmodified_total,
                "component_high": lowhigh_total - low_total,
                "component_remaining": all_total - lowhigh_total,
            },
        )

    out = pd.DataFrame(rows)
    out_path = Path("data/Db8_filterbank_sensitivity_scan.csv")
    out.to_csv(out_path, index=False)
    print(out.to_string(index=False))
    print(f"Saved {out_path}")


def compute_baseline(weekly_band_rms: pd.DataFrame, cutoff_week: str, stat: str) -> dict[str, float]:
    cutoff_y, cutoff_w = parse_week_label(cutoff_week)
    mask = (weekly_band_rms["year"] < cutoff_y) | ((weekly_band_rms["year"] == cutoff_y) & (weekly_band_rms["iso_week"] < cutoff_w))
    pre = weekly_band_rms.loc[mask]

    baseline: dict[str, float] = {}
    for b in DEFAULT_PERIOD_BINS:
        if stat == "median":
            baseline[b.name] = float(pre[b.name].median())
        else:
            baseline[b.name] = float(pre[b.name].mean())
    return baseline


def decompose_week(values: np.ndarray) -> BandParts:
    n = len(values)
    mean = float(values.mean())
    centered = values - mean

    spectrum = np.fft.rfft(centered)
    freqs = np.fft.rfftfreq(n, d=1.0)
    parts: dict[str, np.ndarray] = {}
    used_mask = np.zeros_like(freqs, dtype=bool)

    for band in DEFAULT_PERIOD_BINS:
        f_min = 1.0 / band.period_max_s
        f_max = 1.0 / band.period_min_s
        mask = (freqs >= f_min) & (freqs < f_max)
        used_mask |= mask

        band_spec = np.zeros_like(spectrum)
        band_spec[mask] = spectrum[mask]
        parts[band.name] = np.fft.irfft(band_spec, n=n)

    residual_spec = np.zeros_like(spectrum)
    residual_spec[~used_mask] = spectrum[~used_mask]
    residual = np.fft.irfft(residual_spec, n=n)

    return BandParts(mean=mean, parts=parts, residual=residual)


def reconstruct_for_scenario(
    decomposed_2025: dict[str, BandParts],
    baseline: dict[str, float],
    scenario: Scenario,
) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray]]:
    low_band_names = {
        "fast_sub_primary_5s_to_30s",
        "primary_local_control_30s_to_2m",
        "midrange_2m_to_15m",
    }
    high_band_names = {"balancing_15m_to_2h"}

    all_signals: dict[str, np.ndarray] = {}
    lowhigh_signals: dict[str, np.ndarray] = {}
    low_signals: dict[str, np.ndarray] = {}

    for week, decomp in decomposed_2025.items():
        current_rms = {name: rms(v) for name, v in decomp.parts.items()}
        scales = {}
        for name, cur in current_rms.items():
            raw = 1.0 if cur <= RMS_EPSILON else baseline[name] / cur
            if scenario.clip_min is not None:
                raw = max(scenario.clip_min, raw)
            if scenario.clip_max is not None:
                raw = min(scenario.clip_max, raw)
            scales[name] = float(raw)

        all_signals[week] = reconstruct_variant(decomp, scales, selected=set(scales))
        lowhigh_signals[week] = reconstruct_variant(decomp, scales, selected=low_band_names | high_band_names)
        low_signals[week] = reconstruct_variant(decomp, scales, selected=low_band_names)

    return all_signals, lowhigh_signals, low_signals


def reconstruct_variant(decomp: BandParts, scales: dict[str, float], selected: set[str]) -> np.ndarray:
    out = np.full_like(decomp.residual, decomp.mean)
    out += decomp.residual
    for name, values in decomp.parts.items():
        factor = scales[name] if name in selected else 1.0
        out += factor * values
    return out


def total_minutes_outside(weekly_signals: dict[str, np.ndarray]) -> float:
    total = 0.0
    for values in weekly_signals.values():
        mask = (values < NOMINAL_LOW_HZ) | (values > NOMINAL_HIGH_HZ)
        total += float(mask.sum() / 60.0)
    return total


def rms(values: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(values))))


if __name__ == "__main__":
    main()
