"""S05: Calculate weekly average amplitudes from weekly STFT files."""

from __future__ import annotations

import sys

from grid_frequency_analysis.weekly_stft_average_amplitude import main

if __name__ == "__main__":
    sys.argv = [
        "weekly_stft_average_amplitude",
        "--input-dir",
        "data/D04_weekly_stft",
        "--output-dir",
        "data/D05_weekly_stft_avg_amplitude",
    ]
    main()
