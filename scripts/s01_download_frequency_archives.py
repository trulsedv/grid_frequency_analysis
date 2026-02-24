"""S01: Download monthly frequency archives from Fingrid."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    """Parse S01 CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", default="2015-01")
    parser.add_argument("--to-date", default="2025-12")
    parser.add_argument("--output-dir", default="data/D01_raw_archives")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def generate_fingrid_urls(from_date: str, to_date: str) -> list[list[str]]:
    """Generate candidate Fingrid URLs for each month in a YYYY-MM range."""
    url_patterns = [
        "https://data.fingrid.fi/files/339/{year}/{year}-{month:02d}.7z",
        "https://data.fingrid.fi/files/339/{year}-{month:02d}.7z",
        "https://data.fingrid.fi/files/339/{year}-{month:02d}.zip",
        "https://data.fingrid.fi/files/339/xtaajuusraporttitaajuusdata2018csv-tiedostot-nettiin{year}-{month:02d}.zip",
        "https://data.fingrid.fi/files/339/xtaajuusraporttitaajuusdata2017csv-tiedostot-nettiin{year}-{month:02d}.zip",
        "https://data.fingrid.fi/files/339/pohjavarastoanalyysittaajuusraporttitaajuusdata2017-09.zip",
    ]

    urls: list[list[str]] = []
    from_year, from_month = map(int, from_date.split("-"))
    to_year, to_month = map(int, to_date.split("-"))

    year, month = from_year, from_month
    while (year < to_year) or (year == to_year and month <= to_month):
        urls.append([pattern.format(year=year, month=month) for pattern in url_patterns])
        month += 1
        if month > 12:  # noqa: PLR2004
            month = 1
            year += 1

    return urls


def extract_year_month(text: str) -> str | None:
    """Extract YYYY-MM from arbitrary text."""
    match = re.search(r"(\d{4}-\d{2})", text)
    if match is None:
        return None
    return match.group(1)


def month_already_downloaded(root_path: Path, year_month: str) -> bool:
    """Return True when an archive for this month already exists."""
    return any(root_path.glob(f"{year_month}.*"))


def get_standardized_filename(url: str, root_path: Path) -> Path:
    """Build standardized local filename using extracted YYYY-MM and source extension."""
    year_month = extract_year_month(url)
    if year_month is None:
        msg = f"Could not extract YYYY-MM from URL: {url}"
        raise ValueError(msg)

    extension = Path(url).suffix
    return root_path / f"{year_month}{extension}"


def download_single_url(url: str, root_path: Path, *, verbose: bool = False) -> bool:
    """Download one URL and return True on success."""
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


def download_fingrid_data(urls: list[list[str]], output_dir: str, *, verbose: bool = False) -> None:
    """Download one archive per month by trying each candidate URL group."""
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
        f"downloaded={downloaded_months}, skipped={skipped_months}, failed={failed_months}",
    )


def main() -> None:
    """Run S01 and download archives into D01."""
    args = parse_args()
    urls = generate_fingrid_urls(args.from_date, args.to_date)
    download_fingrid_data(urls, output_dir=args.output_dir, verbose=args.verbose)


if __name__ == "__main__":
    main()
