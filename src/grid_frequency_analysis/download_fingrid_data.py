"""Download Fingrid frequency data for a specified date range."""

from pathlib import Path

import requests

# Configuration - Edit these dates as needed


def main():
    """Download data for the specified date range."""
    from_date = "2025-09"  # Start date in YYYY-MM format
    to_date = "2025-10"    # End date in YYYY-MM format
    urls = generate_fingrid_urls(from_date, to_date)
    download_fingrid_data(urls)


def generate_fingrid_urls(from_date, to_date):
    """Generate Fingrid data URLs for a range of dates in YYYY-MM format."""
    base_url = "https://data.fingrid.fi/files/339/{year}/{year}-{month:02d}.7z"
    urls = []

    from_year, from_month = map(int, from_date.split("-"))
    to_year, to_month = map(int, to_date.split("-"))

    year, month = from_year, from_month
    while (year < to_year) or (year == to_year and month <= to_month):
        urls.append(base_url.format(year=year, month=month))

        month += 1
        if month > 12:  # noqa: PLR2004
            month = 1
            year += 1

    return urls


def download_fingrid_data(urls, output_dir="data/raw"):
    """Download 7z files from a list of URLs."""
    output_dir = "data/raw"
    root_path = Path(output_dir)
    root_path.mkdir(exist_ok=True, parents=True)

    for url in urls:
        try:
            print(f"Downloading {url}...")
            filename = root_path / Path(url).name
            with requests.get(url, stream=True, timeout=10) as r, Path(filename).open("wb") as f:
                for chunk in r.iter_content(chunk_size=8192):  # noqa: FURB122
                    f.write(chunk)
            print(f"Saved to {filename}")
        except (requests.RequestException, OSError) as e:
            print(f"Failed to download {url}: {e}")


if __name__ == "__main__":
    main()
