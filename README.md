# Grid frequency analysis (Fingrid, 2015–2025)

## Purpose
This project tests why 2025 has fewer minutes outside the 49.9–50.1 Hz band.

Method summary:
1. Build weekly 1 Hz signals from daily 10 Hz data.
2. Compute weekly STFT spectra.
3. Build a pre-cutoff baseline spectrum.
4. Replace 2025 spectral amplitudes with baseline amplitudes in selected period ranges.
5. Reconstruct modified 2025 signals and compare minutes outside band.

## Method details (for technical review)
### Data conditioning (S03)
- Source is daily 10 Hz frequency CSV files.
- Data is downsampled to 1 Hz by second-level averaging.
- Invalid values are replaced (`<=0`, `<45 Hz`, `>55 Hz`), then filled with forward/backward fill.
- Week quality gates:
  - `filled_rows <= 7200` (max 2 hours synthetic fill)
  - `longest_synthetic_streak_seconds <= 1800` (max 30 min consecutive synthetic)
- Weeks failing gates are excluded from downstream analysis and logged in `results/quality_report.csv`.

### Spectral model (S04–S06)
- STFT is computed per week with Hann windowing and overlap (`window_size_seconds=14400`, overlap `0.5` by default).
- Output STFT stores complex FFT values per frame and period bin.
- Weekly amplitudes (S05) are `mean(abs(STFT), axis=frames)`.
- Baseline (S06) is the period-wise mean amplitude across pre-cutoff weeks (`< 2024-W22` by default).

### Counterfactual construction (S07–S08)
- For each 2025 week, period-wise scale factors are derived from `baseline_amplitude / 2025_amplitude`.
- Three modified STFT variants are created:
  - all periods,
  - low+high periods,
  - low periods only.
- Modified STFT is inverted via overlap-add iSTFT to 1 Hz weekly signals.

### Outcome metric and attribution (S09–S10)
- Outcome is weekly minutes outside [49.9, 50.1] Hz.
- Cumulative yearly curves compare measured and counterfactual variants.
- Area decomposition attributes parts of the 2025 reduction to different period-range interventions.

### Period bins used
- fast_sub_primary_5s_to_30s (5–30 s)
- primary_local_control_30s_to_2m (30–120 s)
- midrange_2m_to_15m (120–900 s)
- balancing_15m_to_2h (900–7200 s)
- slow_over_2h_to_12h (7200–43200 s)

### Key assumptions and limitations
- This is an attribution-style counterfactual, not causal identification.
- Amplitude replacement keeps observed phase structure; phase dynamics are not independently modeled.
- Fixed STFT window/overlap choices affect low-frequency resolution and attribution sensitivity.
- Quality filtering can remove difficult weeks and may bias representativeness.
- Fill strategy (ffill/bfill) is simple and may smooth extremes in missing intervals.
- Results depend on chosen cutoff week and period-bin definitions.

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
