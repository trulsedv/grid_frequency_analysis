# Grid Frequency Analysis

This repo contains scripts used for analysis of the grid frequency in the nordic grid.

## Usage

**Install dependencies:**
   ```bash
   uv sync
   ```

### Download historical grid frequency

1. **Edit dates** in `src/grid_frequency_analysis/download_fingrid_data.py`:
   ```python
   from_date = "2024-01"  # Start date in YYYY-MM format
   to_date = "2024-12"    # End date in YYYY-MM format
   ```

2. **Run the script:**
   ```bash
   python src/grid_frequency_analysis/download_fingrid_data.py
   ```

Data will be downloaded as .7z files to the `data/raw/` directory.

## Data Source

[Fingrid open data](https://data.fingrid.fi/en/datasets/339), Frequency - historical data
