"""Extract CSV files from compressed archives downloaded from Fingrid."""
import os
import re
import shutil
import stat
import zipfile
from pathlib import Path

import py7zr


def main():
    """Extract all compressed files from raw folder to CSV files in raw_csv."""
    raw_dir = Path("data/raw")
    raw_csv_dir = Path("data/raw_csv")

    raw_csv_dir.mkdir(parents=True, exist_ok=True)

    # Extract 7z files
    seven_z_files = list(raw_dir.glob("*.7z"))
    for seven_z_file in seven_z_files:
        extract_file(seven_z_file, raw_csv_dir, archive_type="7z")

    # Extract zip files
    zip_files = list(raw_dir.glob("*.zip"))
    for zip_file in zip_files:
        extract_file(zip_file, raw_csv_dir, archive_type="zip")


def extract_file(compressed_file, output_dir, archive_type):
    """Extract a compressed file (7z or zip) to the output directory."""
    temp_dir = output_dir / f"temp_{compressed_file.stem}"
    temp_dir.mkdir(exist_ok=True)

    print(f"Extracting {compressed_file.name}...")
    if archive_type == "7z":
        with py7zr.SevenZipFile(compressed_file, mode="r") as archive:
            archive.extractall(path=temp_dir)
    if archive_type == "zip":
        with zipfile.ZipFile(compressed_file, "r") as archive:
            archive.extractall(path=temp_dir)
    print(f"✓ Extracted to {temp_dir}")

    # Fix permissions on extracted files and directories
    fix_extracted_permissions(temp_dir)

    print("Renaming CSV files...")
    csv_files = list(temp_dir.rglob("*.csv"))
    for csv_file in csv_files:
        new_name = get_standardized_csv_name(csv_file.name)
        target_file = output_dir / new_name
        csv_file.rename(target_file)

    shutil.rmtree(temp_dir)
    print(f"✓ Renamed and moved {len(csv_files)} CSV files to {output_dir}\n")


def get_standardized_csv_name(original_name):
    """Generate a standardized CSV filename by extracting yyyy-mm-dd from the original name."""
    date_pattern = r"(\d{4}-\d{2}-\d{2})"

    match = re.search(date_pattern, original_name)
    if match:
        date_str = match.group(1)
        return f"{date_str}.csv"
    print(f"⚠️  Could not standardize filename: {original_name}")
    return original_name


def fix_extracted_permissions(directory):
    """Fix permissions on extracted files and directories to ensure they're readable/writable."""
    # Walk through all files and directories
    for root, dirs, files in os.walk(directory):
        # Fix directory permissions (readable, writable, executable)
        for dir_name in dirs:
            dir_path = Path(root) / dir_name
            dir_path.chmod(stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

        # Fix file permissions (readable, writable)
        for file_name in files:
            file_path = Path(root) / file_name
            file_path.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


if __name__ == "__main__":
    main()
