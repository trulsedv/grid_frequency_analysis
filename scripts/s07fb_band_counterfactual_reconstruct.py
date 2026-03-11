"""S07fb: Band-level FFT counterfactual reconstruction for 2025 weeks.

This alternative method decomposes each weekly signal into fixed period bands using
full-week FFT masks, calibrates per-band scaling from a pre-cutoff baseline, and
reconstructs three modified 2025 variants (all, low+high, low).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from utils import DEFAULT_PERIOD_BINS, parse_week_label

RMS_EPSILON = 1e-12


@dataclass(frozen=True)
class BandParts:
    """Band decomposition pieces for one week."""

    mean: float
    parts: dict[str, np.ndarray]
    residual: np.ndarray


@dataclass(frozen=True)
class FBContext:
    """Prepared context for S07fb run."""

    weekly_files: list[Path]
    target_year: int
    cutoff_week: str
    weekly_band_rms_csv: Path
    baseline_csv: Path
    scales_csv: Path
    out_all: Path
    out_low_high: Path
    out_low: Path


def main() -> None:
    """Run band-level counterfactual reconstruction for 2025."""
    ctx = build_context(parse_args())

    weekly_band_rms = compute_weekly_band_rms(ctx.weekly_files)
    write_weekly_band_rms_csv(weekly_band_rms, ctx.weekly_band_rms_csv)

    baseline = compute_baseline_band_rms(weekly_band_rms, ctx.cutoff_week)
    write_baseline_csv(baseline, ctx.baseline_csv)

    processed, scales_rows = process_target_year_weeks(ctx, baseline)
    write_scales_csv(scales_rows, ctx.scales_csv)
    print(f"S07fb summary: processed={processed}")


def parse_args() -> argparse.Namespace:
    """Parse CLI args."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", default="data/D03_weekly_1hz_csv")
    parser.add_argument("--target-year", type=int, default=2025)
    parser.add_argument("--cutoff-week", default="2024-W22")
    parser.add_argument("--weekly-band-rms-csv", default="data/Db1_weekly_band_rms.csv")
    parser.add_argument("--baseline-csv", default="data/Db2_band_baseline_pre_cutoff.csv")
    parser.add_argument("--scales-csv", default="data/Db7_2025_band_scales.csv")
    parser.add_argument("--out-all", default="data/D10fb_modified_2025_weekly_1hz_all_periods")
    parser.add_argument("--out-low-high", default="data/D11fb_modified_2025_weekly_1hz_low_high_periods")
    parser.add_argument("--out-low", default="data/D12fb_modified_2025_weekly_1hz_low_periods")
    return parser.parse_args()


def build_context(args: argparse.Namespace) -> FBContext:
    """Build resolved path context and create output directories."""
    out_all = Path(args.out_all)
    out_low_high = Path(args.out_low_high)
    out_low = Path(args.out_low)
    out_all.mkdir(parents=True, exist_ok=True)
    out_low_high.mkdir(parents=True, exist_ok=True)
    out_low.mkdir(parents=True, exist_ok=True)

    return FBContext(
        weekly_files=sorted(Path(args.input_dir).glob("*.csv")),
        target_year=args.target_year,
        cutoff_week=args.cutoff_week,
        weekly_band_rms_csv=Path(args.weekly_band_rms_csv),
        baseline_csv=Path(args.baseline_csv),
        scales_csv=Path(args.scales_csv),
        out_all=out_all,
        out_low_high=out_low_high,
        out_low=out_low,
    )


def process_target_year_weeks(
    ctx: FBContext,
    baseline: dict[str, float],
) -> tuple[int, list[dict[str, float | int | str]]]:
    """Create 2025 counterfactual variants and collect scale diagnostics."""
    low_band_names = {
        "fast_sub_primary_5s_to_30s",
        "primary_local_control_30s_to_2m",
        "midrange_2m_to_15m",
    }
    high_band_names = {"balancing_15m_to_2h"}

    scales_rows: list[dict[str, float | int | str]] = []
    processed = 0
    for path in ctx.weekly_files:
        year, week = parse_week_label(path.stem)
        if year != ctx.target_year:
            continue

        values = pd.read_csv(path)["Value"].to_numpy(dtype=float)
        decomposition = decompose_week(values)
        current_rms = {name: rms(values_band) for name, values_band in decomposition.parts.items()}
        scales = {
            name: 1.0 if current <= RMS_EPSILON else float(baseline.get(name, current) / current)
            for name, current in current_rms.items()
        }

        row: dict[str, float | int | str] = {"week": path.stem, "year": year, "iso_week": week}
        for name in sorted(scales):
            row[f"{name}__current_rms"] = float(current_rms[name])
            row[f"{name}__baseline_rms"] = float(baseline[name])
            row[f"{name}__scale"] = float(scales[name])
        scales_rows.append(row)

        write_variant(decomposition, scales, selected=set(scales), out_csv=ctx.out_all / path.name)
        write_variant(
            decomposition,
            scales,
            selected=low_band_names | high_band_names,
            out_csv=ctx.out_low_high / path.name,
        )
        write_variant(decomposition, scales, selected=low_band_names, out_csv=ctx.out_low / path.name)
        processed += 1

    return processed, scales_rows


def compute_weekly_band_rms(weekly_files: list[Path]) -> pd.DataFrame:
    """Compute RMS per band for each available weekly signal."""
    rows: list[dict[str, float | int | str]] = []
    for path in weekly_files:
        year, week = parse_week_label(path.stem)
        values = pd.read_csv(path)["Value"].to_numpy(dtype=float)
        decomposition = decompose_week(values)

        row: dict[str, float | int | str] = {
            "week": path.stem,
            "year": year,
            "iso_week": week,
        }
        for name, part in decomposition.parts.items():
            row[name] = rms(part)
        rows.append(row)

    return pd.DataFrame(rows).sort_values(["year", "iso_week"]).reset_index(drop=True)


def compute_baseline_band_rms(weekly_band_rms: pd.DataFrame, cutoff_week: str) -> dict[str, float]:
    """Compute pre-cutoff mean RMS per band from weekly RMS table."""
    cutoff_key = parse_week_label(cutoff_week)
    mask = (weekly_band_rms["year"] < cutoff_key[0]) | (
        (weekly_band_rms["year"] == cutoff_key[0]) & (weekly_band_rms["iso_week"] < cutoff_key[1])
    )
    pre = weekly_band_rms.loc[mask]

    return {
        band.name: float(pre[band.name].mean())
        for band in DEFAULT_PERIOD_BINS
    }


def decompose_week(values: np.ndarray) -> BandParts:
    """Decompose one week into fixed period bands + residual via FFT masks."""
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


def write_variant(
    decomposition: BandParts,
    scales: dict[str, float],
    selected: set[str],
    out_csv: Path,
) -> None:
    """Write one reconstructed variant using selected scaled bands."""
    out = np.full_like(decomposition.residual, decomposition.mean)
    out += decomposition.residual
    for name, values in decomposition.parts.items():
        factor = scales[name] if name in selected else 1.0
        out += factor * values

    pd.DataFrame({"Value": out}).to_csv(out_csv, index=False)


def write_weekly_band_rms_csv(df: pd.DataFrame, path: Path) -> None:
    """Persist per-week per-band RMS table for diagnostics and tests."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def write_baseline_csv(baseline: dict[str, float], path: Path) -> None:
    """Persist baseline band RMS values for traceability."""
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [{"band": name, "baseline_rms": value} for name, value in baseline.items()]
    pd.DataFrame(rows).to_csv(path, index=False)


def write_scales_csv(rows: list[dict[str, float | int | str]], path: Path) -> None:
    """Persist per-week 2025 scaling factors and source RMS values."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).sort_values(["year", "iso_week"]).to_csv(path, index=False)


def rms(values: np.ndarray) -> float:
    """Root-mean-square helper."""
    return float(np.sqrt(np.mean(np.square(values))))


if __name__ == "__main__":
    main()
