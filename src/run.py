"""Run the currently implemented part of the pipeline."""
from grid_frequency_analysis.count_min_outside_nominal import main as count_minutes_main
from grid_frequency_analysis.create_weekly_csv import main as create_weekly_csv_main
from grid_frequency_analysis.download_fingrid_data import main as download_data_main
from grid_frequency_analysis.extract_fingrid_data import main as extract_data_main
from grid_frequency_analysis.plot_minutes_per_year import main as plot_minutes_main


def main():
    """Run data download/extract + weekly aggregation + nominal-band plots."""
    download_data_main()
    extract_data_main()
    create_weekly_csv_main()
    count_minutes_main()
    plot_minutes_main()


if __name__ == "__main__":
    main()
