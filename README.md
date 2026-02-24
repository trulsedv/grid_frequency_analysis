# Grid frequency analysis (Fingrid, 2015–2025)

## Purpose
This project tests why 2025 has fewer minutes outside the 49.9–50.1 Hz band.

Method summary:
1. Build weekly 1 Hz signals from daily 10 Hz data.
2. Compute weekly STFT spectra.
3. Build a pre-cutoff baseline spectrum.
4. Replace 2025 spectral amplitudes with baseline amplitudes in selected period ranges.
5. Reconstruct modified 2025 signals and compare minutes outside band.

Main interpretation from the final decomposition plot:
- Most reduction is explained by damping in **high-period (balancing)** oscillations.
- A significant part is also explained by damping in **low-period (frequency-control)** oscillations.

## Project structure
- `scripts/` contains all numbered pipeline scripts (`s01..s10`) and appendix scripts (`sa4a..sa8b`) plus `utils.py`.
- `data/` uses numbered datasets (`D01..D16`, `Da1..Da3`).
- `results/` contains report outputs (`R1`, `R2`, `Ra1..Ra5`).
- `docs/overview.md` is the canonical workflow specification.

## Quick run
Install deps:

```bash
uv sync
```

Run full pipeline:

```bash
uv run python scripts/s01_download_frequency_archives.py
uv run python scripts/s02_extract_frequency_archives.py
uv run python scripts/s03_create_weekly_1hz_and_quality.py
uv run python scripts/s04_calculate_weekly_stft.py
uv run python scripts/s05_calculate_weekly_average_amplitudes.py
uv run python scripts/s06_calculate_baseline_pre_cutoff.py
uv run python scripts/s07_modify_2025_stft.py
uv run python scripts/s08_reconstruct_modified_2025_signal.py
uv run python scripts/s09_calculate_minutes_outside_nominal.py
uv run python scripts/s10_plot_cumulative_minutes_outside_nominal.py
```

Appendix outputs:

```bash
uv run python scripts/sa4a_animate_sine_buildup.py
uv run python scripts/sa5a_plot_fft_amplitudes_two_weeks.py
uv run python scripts/sa5b_calculate_binned_weekly_amplitudes.py
uv run python scripts/sa5c_plot_binned_amplitudes_over_time.py
uv run python scripts/sa6a_modify_weekly_amplitudes.py
uv run python scripts/sa6b_plot_modified_unmodified_baseline_amplitudes.py
uv run python scripts/sa8a_reproduce_week_from_stft.py
uv run python scripts/sa8b_plot_measured_reproduced_modified.py
```

## Reproducibility notes
- Datasets are generated locally and should not be committed.
- Quality filtering in S03 skips low-quality weeks and writes `results/quality_report.csv`.
- Validation runs can start from `s04` when `D03` already exists.

## Data source
- Fingrid open data: https://data.fingrid.fi/en/datasets/339
