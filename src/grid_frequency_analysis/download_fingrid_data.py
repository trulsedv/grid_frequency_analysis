"""Download Fingrid frequency data for a specified date range."""

import re
from pathlib import Path

import requests


def main():
    """Download data for the specified date range."""
    from_date = "2015-01"  # Start date in YYYY-MM format
    to_date = "2025-12"    # End date in YYYY-MM format
    urls = generate_fingrid_urls(from_date, to_date)
    download_fingrid_data(urls)


def generate_fingrid_urls(from_date, to_date):
    """Generate Fingrid data URLs for a range of dates in YYYY-MM format."""
    # Multiple URL patterns to try (different formats used over time)
    url_patterns = [
        "https://data.fingrid.fi/files/339/{year}/{year}-{month:02d}.7z",  # With year folder, 7z
        "https://data.fingrid.fi/files/339/{year}-{month:02d}.7z",         # Without year folder, 7z
        "https://data.fingrid.fi/files/339/{year}-{month:02d}.zip",        # Without year folder, zip
        "https://data.fingrid.fi/files/339/xtaajuusraporttitaajuusdata2018csv-tiedostot-nettiin{year}-{month:02d}.zip",
        "https://data.fingrid.fi/files/339/xtaajuusraporttitaajuusdata2017csv-tiedostot-nettiin{year}-{month:02d}.zip",
        "https://data.fingrid.fi/files/339/pohjavarastoanalyysittaajuusraporttitaajuusdata2017-09.zip",
    ]

    urls = []

    from_year, from_month = map(int, from_date.split("-"))
    to_year, to_month = map(int, to_date.split("-"))

    year, month = from_year, from_month
    while (year < to_year) or (year == to_year and month <= to_month):
        # Add all possible URL patterns for this month
        month_urls = [pattern.format(year=year, month=month) for pattern in url_patterns]
        urls.append(month_urls)

        month += 1
        if month > 12:  # noqa: PLR2004
            month = 1
            year += 1

    return urls


def download_fingrid_data(urls, output_dir="data/raw"):
    """Download files from a list of URL groups (trying multiple URLs per month)."""
    output_dir = "data/raw"
    root_path = Path(output_dir)
    root_path.mkdir(exist_ok=True, parents=True)

    for url_group in urls:
        for url in url_group:
            downloaded = download_single_url(url, root_path)
            if downloaded:
                break

        if not downloaded:
            print(f"\n✗ Failed to download data for month in: {url_group[0]}\n")


def download_single_url(url, root_path):
    """Download a single URL and return True if successful."""
    expected_status_code = 200
    print(f"Trying {url}...")
    response = requests.get(url, stream=True, timeout=10)

    if response.status_code != expected_status_code:
        print(f"  → {response.status_code} {url}")
        return False

    filename = get_standardized_filename(url, root_path)
    with Path(filename).open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):  # noqa: FURB122
            f.write(chunk)
    print(f"✓ Downloaded {filename.name}")

    return True


def get_standardized_filename(url, root_path):
    """Extract year-month from URL and create standardized filename."""
    year_month_pattern = r"(\d{4}-\d{2})"
    match = re.search(year_month_pattern, url)

    year_month = match.group(1)
    extension = Path(url).suffix
    return root_path / f"{year_month}{extension}"


if __name__ == "__main__":
    main()
