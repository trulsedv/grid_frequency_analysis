"""S02: Extract monthly archives into daily 10 Hz CSV files."""

from __future__ import annotations

from pathlib import Path

from grid_frequency_analysis.extract_fingrid_data import extract_file, should_extract_archive


def main() -> None:
    """Run D02 pipeline step."""
    raw_dir = Path("data/D01_raw_archives")
    out_dir = Path("data/D02_extracted_10hz_csv")
    out_dir.mkdir(parents=True, exist_ok=True)

    for zip_file in sorted(raw_dir.glob("*.zip")):
        if should_extract_archive(zip_file, out_dir):
            extract_file(zip_file, out_dir, archive_type="zip")

    for seven_z_file in sorted(raw_dir.glob("*.7z")):
        if should_extract_archive(seven_z_file, out_dir):
            extract_file(seven_z_file, out_dir, archive_type="7z")


if __name__ == "__main__":
    main()
