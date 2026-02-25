# Grid frequency analysis (2015–2025)

## Summary
In 2025, the grid has noticeably fewer minutes outside the 49.9–50.1 Hz band than in earlier years, and this project investigates how much is linked to dampening of oscillations with certain periods. The method builds counterfactual 2025 signals by replacing selected spectral amplitudes with pre-cutoff baseline amplitudes, then computes minutes outside band and compares cumulative curves. The results indicate that most of the reduction is associated with damping in high-period (balancing) oscillations, with a meaningful additional contribution from low-period (frequency-control) oscillations.

## Method (pipeline scripts S01–S10)
1. **S01 – Download frequency archives**
   - Downloads monthly `.7z/.zip` archives from Fingrid.
   - Output: `data/D01_raw_archives`.

2. **S02 – Extract frequency archives**
   - Extracts daily 10 Hz CSV files from D01.
   - Output: `data/D02_extracted_10hz_csv`.

3. **S03 – Create weekly 1 Hz logs + quality report**
   - Downsamples daily 10 Hz to 1 Hz (second-level average).
   - Invalid values removed (`<45 Hz`, `>55 Hz`)
   - Fill in missing values (`ffill/bfill`).
   - Week-level quality gates:
     - `filled_rows <= 7200`
     - `longest_synthetic_streak_seconds <= 1800`
   - Low-quality weeks are skipped from D03 and logged.
   - Outputs:
     - `data/D03_weekly_1hz_csv`
     - `results/quality_report.csv` (R1)

4. **S04 – Calculate weekly STFT**
   - Splits each week into windows (Hann window, overlap) and calculate FFT for each.
   - Default: `window_size_seconds=14400`, `overlap_fraction=0.5`.
   - Output: `data/D04_weekly_stft`.

5. **S05 – Calculate weekly average amplitudes**
   - Output: `data/D05_weekly_stft_avg_amplitude`.

6. **S06 – Calculate pre-cutoff baseline spectrum**
   - Period-wise mean amplitude across all weeks before cutoff (`2024-W22` default).
   - Output: `data/D06_baseline_pre_cutoff_amplitude/baseline_pre_cutoff.csv`.

7. **S07 – Modify 2025 STFT amplitudes**
   - Builds period-wise scale factors from `baseline_amplitude / observed_2025_amplitude`.
   - Applies those factors to STFT amplitudes while preserving the observed phase in each frame.
   - Produces 3 modified 2025 STFT variants:
     - modify all periods (D07)
     - modify low+high periods (D08)
     - modify low periods (D09)

8. **S08 – Reconstruct modified 2025 weekly 1 Hz signals**
   - Inverse STFT with overlap-add reconstruction.
   - Produces 3 modified 2025 signal datasets:
     - D10 (all periods)
     - D11 (low+high)
     - D12 (low only)

9. **S09 – Calculate minutes outside nominal band**
   - Metric: minutes outside [49.9, 50.1] Hz.
   - Produces:
     - D13 unmodified
     - D14 modified all periods
     - D15 modified low+high
     - D16 modified low only

10. **S10 – Plot cumulative minutes outside nominal**
    - Builds cumulative yearly curves and decomposition areas.
    - Output: `results/cumulative_minutes_outside_nominal.html/.png` (R2).

Period bins used in spectral attribution:
- fast_sub_primary_5s_to_30s (5–30 s)
- primary_local_control_30s_to_2m (30–120 s)
- midrange_2m_to_15m (120–900 s)
- balancing_15m_to_2h (900–7200 s)
- slow_over_2h_to_12h (7200–43200 s)

## Key assumptions and limitations
- Attribution-style counterfactual, not causal identification.
- Amplitude replacement keeps observed phase structure.
- STFT window/overlap choices affect low-frequency attribution.
- Quality filtering may remove difficult weeks and affect representativeness.
- Results depend on cutoff week and period-bin definitions.

## Disclaimer
This method is a structured "what-if" test. It asks: if we change selected oscillation ranges in 2025 to look more like pre-cutoff years, how much does the out-of-band metric change? That helps estimate which ranges are important in the data and model used here. But it does not, by itself, prove the real-world root cause. To make a stronger causal claim, you would need extra evidence (for example operational records, market/control changes, and robustness checks across multiple alternative model choices).

## Run
Install dependencies:

```bash
uv sync
```

Run full pipeline (note the three first will takr time to finish):

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

## Data source
- Fingrid open data: https://data.fingrid.fi/en/datasets/339
