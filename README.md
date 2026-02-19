# Grid Frequency Analysis

This repo analyzes Nordic grid frequency and investigates whether the 2025
improvement (fewer minutes outside 49.9–50.1 Hz) can be explained by damping in
specific oscillation period ranges.

## Project status

- ✅ Data download/extraction and weekly 1 Hz CSV generation
- ✅ Weekly minutes outside nominal band + cumulative yearly plotting
- ✅ Weekly FFT export (`period_s`, `amplitude`) per week
- 🚧 Spectral tracking, reconstruction, and counterfactual attribution (planned)

See:
- `docs/analysis_plan.md`
- `docs/pr_roadmap.md`

## Usage

Install dependencies:

```bash
uv sync
```

Run implemented pipeline:

```bash
python src/run.py
```

Generate weekly FFT CSVs (full spectrum for each week):

```bash
uv run python src/grid_frequency_analysis/weekly_fft.py --window-size-seconds 14400
```

Outputs are written to `data/weekly_fft/<YYYY-WW>.csv` with columns:
- `frequency_hz`
- `period_s`
- `amplitude`

Aggregate FFT amplitudes by period bin (week rows, bin columns) and plot:

```bash
uv run python src/grid_frequency_analysis/weekly_fft_bin_means.py
```

Outputs:
- `results/weekly_fft_bin_means.csv`
- `results/plots/weekly_fft_bin_means.html`
- `results/plots/weekly_fft_bin_means.png`

Reconstruct a 4h signal from weekly FFT amplitudes, tile to week length, and compare:

```bash
uv run python src/grid_frequency_analysis/reconstruct_from_weekly_fft.py --week 2024-W15 --window-size-seconds 14400
```

Outputs:
- `results/reconstruction/<week>_measured_vs_reconstructed.csv`
- `results/reconstruction/<week>_measured_vs_reconstructed.html`
- `results/reconstruction/<week>_measured_vs_reconstructed.png`

### Download historical grid frequency only

1. Edit dates in `src/grid_frequency_analysis/download_fingrid_data.py`
2. Run:

```bash
python src/grid_frequency_analysis/download_fingrid_data.py
```

Data is downloaded as `.7z` files to `data/raw/`.

## Data source

[Fingrid open data](https://data.fingrid.fi/en/datasets/339), Frequency - historical data
