"""Download Fingrid frequency data for a specified date range."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import requests

DEFAULT_FROM_DATE = "2015-01"
DEFAULT_TO_DATE = "2025-12"


def main() -> None:
    """Download data for a date range."""
    args = parse_args()
    urls = generate_fingrid_urls(args.from_date, args.to_date)
    download_fingrid_data(urls, output_dir=args.output_dir, verbose=args.verbose)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", default=DEFAULT_FROM_DATE, help="Start month (YYYY-MM)")
    parser.add_argument("--to-date", default=DEFAULT_TO_DATE, help="End month (YYYY-MM)")
    parser.add_argument("--output-dir", default="data/raw", help="Destination directory")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print every attempted URL (default prints only summary/failures)",
    )
    return parser.parse_args()


def generate_fingrid_urls(from_date: str, to_date: str) -> list[list[str]]:
    """Generate Fingrid candidate URLs for each month in YYYY-MM range."""
    # Multiple URL patterns to try (different formats used over time)
    url_patterns = [
        "https://data.fingrid.fi/files/339/{year}/{year}-{month:02d}.7z",  # with year folder, 7z
        "https://data.fingrid.fi/files/339/{year}-{month:02d}.7z",  # without year folder, 7z
        "https://data.fingrid.fi/files/339/{year}-{month:02d}.zip",  # without year folder, zip
        "https://data.fingrid.fi/files/339/xtaajuusraporttitaajuusdata2018csv-tiedostot-nettiin{year}-{month:02d}.zip",
        "https://data.fingrid.fi/files/339/xtaajuusraporttitaajuusdata2017csv-tiedostot-nettiin{year}-{month:02d}.zip",
        "https://data.fingrid.fi/files/339/pohjavarastoanalyysittaajuusraporttitaajuusdata2017-09.zip",
    ]

    urls: list[list[str]] = []

    from_year, from_month = map(int, from_date.split("-"))
    to_year, to_month = map(int, to_date.split("-"))

    year, month = from_year, from_month
    while (year < to_year) or (year == to_year and month <= to_month):
        month_urls = [pattern.format(year=year, month=month) for pattern in url_patterns]
        urls.append(month_urls)

        month += 1
        if month > 12:  # noqa: PLR2004
            month = 1
            year += 1

    return urls


def download_fingrid_data(urls: list[list[str]], output_dir: str = "data/raw", verbose: bool = False) -> None:
    """Download files from grouped candidate URLs (one group per month)."""
    root_path = Path(output_dir)
    root_path.mkdir(exist_ok=True, parents=True)

    downloaded_months = 0
    skipped_months = 0
    failed_months = 0

    for url_group in urls:
        if not url_group:
            continue

        month_key = extract_year_month(url_group[0])
        if month_key and month_already_downloaded(root_path, month_key):
            skipped_months += 1
            if verbose:
                print(f"↷ Skipping {month_key}, file already exists")
            continue

        downloaded = False
        for url in url_group:
            downloaded = download_single_url(url, root_path, verbose=verbose)
            if downloaded:
                downloaded_months += 1
                break

        if not downloaded:
            failed_months += 1
            print(f"✗ Failed to download month candidate set: {url_group[0]}")

    print(
        "Download summary: "
        f"downloaded={downloaded_months}, skipped={skipped_months}, failed={failed_months}"
    )


def download_single_url(url: str, root_path: Path, verbose: bool = False) -> bool:
    """Download a single URL and return True on success."""
    if verbose:
        print(f"Trying {url}...")

    try:
        response = requests.get(url, stream=True, timeout=10)
    except requests.RequestException as exc:
        if verbose:
            print(f"  → request error for {url}: {exc}")
        return False

    if response.status_code != requests.codes.ok:
        if verbose:
            print(f"  → {response.status_code} {url}")
        return False

    filename = get_standardized_filename(url, root_path)
    with filename.open("wb") as file_obj:
        for chunk in response.iter_content(chunk_size=8192):
            file_obj.write(chunk)
    print(f"✓ Downloaded {filename.name}")
    return True


def month_already_downloaded(root_path: Path, year_month: str) -> bool:
    """Check whether any archive for YYYY-MM already exists."""
    return any(root_path.glob(f"{year_month}.*"))


def get_standardized_filename(url: str, root_path: Path) -> Path:
    """Extract year-month from URL and create standardized output filename."""
    year_month = extract_year_month(url)
    if year_month is None:
        raise ValueError(f"Could not extract YYYY-MM from URL: {url}")

    extension = Path(url).suffix
    return root_path / f"{year_month}{extension}"


def extract_year_month(text: str) -> str | None:
    """Extract YYYY-MM from arbitrary text."""
    match = re.search(r"(\d{4}-\d{2})", text)
    if match is None:
        return None
    return match.group(1)


if __name__ == "__main__":
    main()
