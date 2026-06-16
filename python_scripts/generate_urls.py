#!/usr/bin/env python3
"""
Read all CSV files from results_berlin_munich/ and generate a single text file
with Google Maps URLs for every location.

URL construction priority:
  1. Use existing 'link' field if present
  2. Use 'data_id' (Google ftid) → https://www.google.com/maps/place/data=!4m2!3m1!1s{DATA_ID}
  3. Use 'plus_code' → https://www.google.com/maps/place/{PLUS_CODE}
  4. Use title + address search → https://www.google.com/maps/search/TITLE+ADDRESS
  5. Fall back to lat/lng → https://www.google.com/maps?q={LAT},{LNG}
"""

import csv
import os
import urllib.parse
from pathlib import Path

RESULTS_DIR = Path("../results/results_berlin_munich")
OUTPUT_FILE = Path("../queries/all_google_maps_urls.txt")


def build_google_maps_url(row: dict) -> str:
    """Construct a Google Maps URL from a CSV row."""
    title = row.get("title", "").strip()
    address = row.get("address", "").strip()
    link = row.get("link", "").strip()
    data_id = row.get("data_id", "").strip()
    plus_code = row.get("plus_code", "").strip()
    lat = row.get("latitude", "").strip()
    lng = row.get("longitude", "").strip()

    # 1. Use existing link if non-empty
    if link:
        return ("link", link)

    # 2. Use data_id (Google feature ID / ftid)
    if data_id:
        # data_id format: 0xHEX1:0xHEX2
        return ("data_id", f"https://www.google.com/maps/place/data=!4m2!3m1!1s{data_id}")

    # 3. Use plus code (Open Location Code)
    if plus_code:
        return ("plus_code", f"https://www.google.com/maps/place/{urllib.parse.quote(plus_code, safe='+')}")

    # 4. Title + Address search (Google Maps search query)
    if title and address:
        query = f"{title} {address}"
        return ("title_address", f"https://www.google.com/maps/search/{urllib.parse.quote(query)}")

    # 5. Fall back to latitude/longitude
    if lat and lng:
        try:
            lat_f = float(lat)
            lng_f = float(lng)
            if lat_f != 0.0 or lng_f != 0.0:
                return ("latlng", f"https://www.google.com/maps?q={lat_f},{lng_f}")
        except (ValueError, TypeError):
            pass

    # 6. Last resort: search by title only
    if title:
        return ("search", f"https://www.google.com/maps/search/{urllib.parse.quote(title)}")

    return ("empty", "")  # No usable data


def main():
    csv_files = sorted(RESULTS_DIR.glob("*.csv"))
    if not csv_files:
        print(f"No CSV files found in {RESULTS_DIR.resolve()}")
        return

    print(f"Found {len(csv_files)} CSV files:")
    for f in csv_files:
        print(f"  - {f.name}")

    urls = []
    total_rows = 0
    skipped = 0
    methods = {"link": 0, "data_id": 0, "plus_code": 0, "title_address": 0, "latlng": 0, "search": 0, "empty": 0}

    for csv_path in csv_files:
        with open(csv_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                total_rows += 1
                method, url = build_google_maps_url(row)
                title = row.get("title", "").strip()

                methods[method] += 1

                if url:
                    urls.append(url)
                else:
                    skipped += 1

    # Write output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
        for url_line in urls:
            fh.write(url_line + "\n")

    # Summary
    print(f"\n{'='*60}")
    print(f"Total rows processed:  {total_rows}")
    print(f"URLs generated:        {len(urls)}")
    print(f"Skipped (no data):     {skipped}")
    print(f"\nURL construction methods used:")
    for method, count in methods.items():
        print(f"  {method:12s}: {count}")
    print(f"\nOutput written to: {OUTPUT_FILE.resolve()}")
    print(f"{'='*60}")

    # Print first 5 sample URLs for verification
    print("\nSample URLs (first 5):")
    for u in urls[:5]:
        print(f"  {u}")


if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    main()
