""""Run the full grid frequency analysis pipeline."""
from grid_frequency_analysis.concat_resample import main as concat_resample_main
from grid_frequency_analysis.count_min_outside_nominal import main as count_minutes_main
from grid_frequency_analysis.download_fingrid_data import main as download_data_main
from grid_frequency_analysis.extract_fingrid_data import main as extract_data_main
from grid_frequency_analysis.plot_minutes_per_year import main as plot_minutes_main


def main():
    """Run the full grid frequency analysis pipeline."""
    download_data_main()
    extract_data_main()
    concat_resample_main()
    count_minutes_main()
    plot_minutes_main()


if __name__ == "__main__":
    main()
