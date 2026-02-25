"""S02: Extract monthly archives into daily 10 Hz CSV files."""

from __future__ import annotations

import os
import re
import shutil
import stat
import zipfile
from pathlib import Path

import py7zr
from py7zr.exceptions import Bad7zFile


def main() -> None:
    """Run S02 and extract D01 archives into D02 CSVs."""
    raw_dir = Path("data/D01_raw_archives")
    out_dir = Path("data/D02_extracted_10hz_csv")
    out_dir.mkdir(parents=True, exist_ok=True)

    for zip_file in sorted(raw_dir.glob("*.zip")):
        if should_extract_archive(zip_file, out_dir):
            extract_file(zip_file, out_dir, archive_type="zip")

    for seven_z_file in sorted(raw_dir.glob("*.7z")):
        if should_extract_archive(seven_z_file, out_dir):
            extract_file(seven_z_file, out_dir, archive_type="7z")


def should_extract_archive(compressed_file: Path, csv_dir: Path) -> bool:
    """Return True if no extracted CSVs exist yet for this archive month."""
    match = re.search(r"(\d{4}-\d{2})", compressed_file.name)
    if not match:
        return True

    year_month = match.group(1)
    existing_csvs = list(csv_dir.glob(f"{year_month}-*.csv"))
    return len(existing_csvs) == 0


def get_standardized_csv_name(original_name: str) -> str:
    """Map extracted CSV names to YYYY-MM-DD.csv when possible."""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", original_name)
    if match:
        return f"{match.group(1)}.csv"
    print(f"⚠️  Could not standardize filename: {original_name}")
    return original_name


def fix_extracted_permissions(directory: Path) -> None:
    """Make extracted files/directories readable and writable."""
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            dir_path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

        for file_name in files:
            file_path = Path(root) / file_name
            file_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def extract_file(compressed_file: Path, output_dir: Path, archive_type: str) -> None:
    """Extract one .zip or .7z archive to output_dir."""
    temp_dir = output_dir / f"temp_{compressed_file.stem}"
    temp_dir.mkdir(exist_ok=True)

    print(f"Extracting {compressed_file.name}...")
    try:
        if archive_type == "7z":
            with py7zr.SevenZipFile(compressed_file, mode="r") as archive:
                archive.extractall(path=temp_dir)
        elif archive_type == "zip":
            with zipfile.ZipFile(compressed_file, "r") as archive:
                archive.extractall(path=temp_dir)
        else:
            msg = f"Unsupported archive type: {archive_type}"
            raise ValueError(msg)
    except (zipfile.BadZipFile, Bad7zFile, OSError) as exc:
        print(f"⚠️  Skipping unreadable archive {compressed_file.name}: {exc}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    fix_extracted_permissions(temp_dir)

    csv_files = list(temp_dir.rglob("*.csv"))
    for csv_file in csv_files:
        target_file = output_dir / get_standardized_csv_name(csv_file.name)
        csv_file.rename(target_file)

    shutil.rmtree(temp_dir)
    print(f"✓ Renamed and moved {len(csv_files)} CSV files to {output_dir}\n")


if __name__ == "__main__":
    main()
