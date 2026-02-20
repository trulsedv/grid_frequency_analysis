# Final Plot Pipeline (2025 measured vs undamped estimate + decomposition)

This document describes the end-to-end script flow to generate the final decomposition plot:

- `results/counterfactual_2025/counterfactual_2025_cumulative_decomposed_area_with_history.html`
- `results/counterfactual_2025/counterfactual_2025_cumulative_decomposed_area_with_history.png`

The plot shows:
- 2025 measured cumulative minutes outside nominal
- 2025 undamped estimate (both bins adjusted)
- area: dampening of low period oscillations
- area: dampening of high period oscillations
- historical context lines (2015–2024)

---

## Prerequisites

- Python deps installed:

```bash
uv sync
```

---

## 0) Download raw archives

**Script:** `src/grid_frequency_analysis/download_fingrid_data.py`

**Input:**
- configured date range inside script (or CLI if configured in your branch)

**Output:**
- raw archives in `data/raw/`

**Run:**
```bash
uv run python src/grid_frequency_analysis/download_fingrid_data.py
```

---

## 1) Extract raw archives to daily CSV

**Script:** `src/grid_frequency_analysis/extract_fingrid_data.py`

**Input:**
- `data/raw/*`

**Output:**
- `data/extracted_csv/YYYY-MM-DD.csv`

**Run:**
```bash
uv run python src/grid_frequency_analysis/extract_fingrid_data.py
```

---

## 2) Weekly quality-filtered time series

**Script:** `src/grid_frequency_analysis/create_weekly_csv.py`

**Input:**
- `data/extracted_csv/*.csv`

**Output:**
- `data/weekly_csv/<YYYY-Www>.csv`
- `results/weekly_quality_report.csv`

**Run:**
```bash
uv run python src/grid_frequency_analysis/create_weekly_csv.py
```

---

## 3) Measured minutes outside nominal (all years)

**Script:** `src/grid_frequency_analysis/count_min_outside_nominal.py`

**Input:**
- `data/weekly_csv/*.csv`

**Output:**
- `data/minutes_outside_nominal_per_week.csv`

**Run:**
```bash
uv run python src/grid_frequency_analysis/count_min_outside_nominal.py
```

---

## 4) Weekly STFT (complex coefficients)

**Script:** `src/grid_frequency_analysis/weekly_stft.py`

**Input:**
- `data/weekly_csv/*.csv`

**Output:**
- `results/weekly_stft/<YYYY-Www>.csv` (period + frame_XXX complex columns)
- `results/weekly_stft/<YYYY-Www>_meta.csv`

**Run:**
```bash
uv run python src/grid_frequency_analysis/weekly_stft.py --window-size-seconds 14400 --overlap-fraction 0.5
```

---

## 5) Average STFT amplitude per week

**Script:** `src/grid_frequency_analysis/weekly_stft_average_amplitude.py`

**Input:**
- `results/weekly_stft/*.csv`

**Output:**
- `results/weekly_stft_avg/<YYYY-Www>.csv` with columns:
  - `period_s`
  - `amplitude`

**Run:**
```bash
uv run python src/grid_frequency_analysis/weekly_stft_average_amplitude.py
```

---

## 6) Baseline average spectrum (pre-summer-2024)

**Script:** `src/grid_frequency_analysis/baseline_average_spectrum.py`

**Input:**
- `results/weekly_stft_avg/*.csv`

**Output:**
- `results/baseline_average_spectrum_pre_2024_summer.csv`

**Run (current cutoff):**
```bash
uv run python src/grid_frequency_analysis/baseline_average_spectrum.py --cutoff-week 2024-W22
```

(Uses all weeks strictly before cutoff.)

---

## 7) 2025 undamped-estimate runs (weekly minutes)

**Script:** `src/grid_frequency_analysis/counterfactual_2025_analysis.py`

**Inputs:**
- `data/weekly_csv/*.csv`
- `results/weekly_stft/*.csv` + `_meta.csv`
- `results/weekly_stft_avg/*.csv`
- `results/baseline_average_spectrum_pre_2024_summer.csv`

**What it does:**
- For each 2025 week, scales complex STFT coefficients in selected bins using:
  - scale(period) = baseline_amplitude(period) / target_week_amplitude(period)
- Reconstructs weekly undamped estimate from modified STFT
- Computes measured vs undamped minutes outside nominal

**Output:**
- `results/counterfactual_2025/counterfactual_2025_minutes_per_week.csv`
- `results/counterfactual_2025/counterfactual_2025_cumulative_compare.html/.png`

**Run:**
```bash
uv run python src/grid_frequency_analysis/counterfactual_2025_analysis.py
```

---

## 8) By-bin attribution (primary-only, balancing-only, both)

**Generated using inline analysis run** (same method as step 6, split by bin set).

**Outputs:**
- `results/counterfactual_2025/counterfactual_2025_by_bin_minutes_per_week.csv`
- `results/counterfactual_2025/counterfactual_2025_by_bin_summary.csv`
- `results/counterfactual_2025/counterfactual_2025_cumulative_by_bin.html/.png`

This file is used to build the final decomposition areas.

---

## 9) Final decomposition plot with historical context

**Generated using inline plotting run** (reads measured-all-years + by-bin 2025 table).

**Inputs:**
- `data/minutes_outside_nominal_per_week.csv`
- `results/counterfactual_2025/counterfactual_2025_by_bin_minutes_per_week.csv`

**Output (final):**
- `results/counterfactual_2025/counterfactual_2025_cumulative_decomposed_area_with_history.html`
- `results/counterfactual_2025/counterfactual_2025_cumulative_decomposed_area_with_history.png`

**Visual semantics:**
- Line: `2025 measured`
- Line: `2025 undamped estimate`
- Area between measured and primary-only: `Dampening of low period oscillations`
- Area between primary-only and both: `Dampening of high period oscillations`
- Thin context lines for 2015–2024 measured years

---

## Notes

- STFT internals (`results/weekly_stft`, `results/weekly_stft_avg`) are large and treated as generated data.
- Compact outputs for presentation/evaluation are kept under `results/` and committed as needed.
