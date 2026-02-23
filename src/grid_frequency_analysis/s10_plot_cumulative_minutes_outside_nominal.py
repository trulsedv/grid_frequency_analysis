"""S10: Plot cumulative minutes outside nominal band."""

from __future__ import annotations

import sys

from grid_frequency_analysis.plot_minutes_per_year import main


if __name__ == "__main__":
    sys.argv = [
        "plot_minutes_per_year",
        "--input-csv",
        "data/D13_minutes_outside_unmodified_weeks/minutes_outside_unmodified_weeks.csv",
        "--output-dir",
        "results",
    ]
    main()
