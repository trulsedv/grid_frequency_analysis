"""S06: Calculate baseline average amplitudes before cutoff."""

from __future__ import annotations

import sys

from grid_frequency_analysis.baseline_average_spectrum import main

if __name__ == "__main__":
    sys.argv = [
        "baseline_average_spectrum",
        "--input-dir",
        "data/D05_weekly_stft_avg_amplitude",
        "--output-csv",
        "data/D06_baseline_pre_cutoff_amplitude/baseline_pre_cutoff.csv",
    ]
    main()
