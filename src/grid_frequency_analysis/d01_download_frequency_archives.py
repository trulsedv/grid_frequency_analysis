"""D01: Download monthly frequency archives from Fingrid."""

from __future__ import annotations

import argparse

from grid_frequency_analysis.download_fingrid_data import download_fingrid_data, generate_fingrid_urls


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from-date", default="2015-01")
    parser.add_argument("--to-date", default="2025-12")
    parser.add_argument("--output-dir", default="data/D01_raw_archives")
    parser.add_argument("--verbose", action="store_true")
    return parser.parse_args()


def main() -> None:
    """Run D01 pipeline step."""
    args = parse_args()
    urls = generate_fingrid_urls(args.from_date, args.to_date)
    download_fingrid_data(urls, output_dir=args.output_dir, verbose=args.verbose)


if __name__ == "__main__":
    main()
