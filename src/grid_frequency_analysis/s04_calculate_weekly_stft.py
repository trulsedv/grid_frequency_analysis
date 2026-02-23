"""S04: Calculate weekly STFT from weekly 1 Hz CSV files."""

from __future__ import annotations

import sys

from grid_frequency_analysis.weekly_stft import main

if __name__ == "__main__":
    sys.argv = [
        "weekly_stft",
        "--input-dir",
        "data/D03_weekly_1hz_csv",
        "--output-dir",
        "data/D04_weekly_stft",
    ]
    main()
