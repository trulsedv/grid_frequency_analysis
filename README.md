# Grid Frequency Analysis

This repo analyzes Nordic grid frequency and investigates whether the 2025
improvement (fewer minutes outside 49.9–50.1 Hz) can be explained by damping in
specific oscillation period ranges.

## Project status

- ✅ Data download/extraction and weekly 1 Hz CSV generation
- ✅ Weekly minutes outside nominal band + cumulative yearly plotting
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

### Download historical grid frequency only

1. Edit dates in `src/grid_frequency_analysis/download_fingrid_data.py`
2. Run:

```bash
python src/grid_frequency_analysis/download_fingrid_data.py
```

Data is downloaded as `.7z` files to `data/raw/`.

## Data source

[Fingrid open data](https://data.fingrid.fi/en/datasets/339), Frequency - historical data
