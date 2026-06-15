import subprocess
from pathlib import Path
import json
import argparse
import sys


# =========================
# CONFIG
# =========================

QUERIES_FOLDER = Path("../queries")
ALL_QUERIES_FILE = Path("queries/all-queries.txt")

DOCKER_IMAGE = "gosom/google-maps-scraper"

RADIUS = "1000"
ZOOM = "16"
DEPTH = "10"

# =========================
# LOAD LOCATIONS
# =========================

def load_locations(path: Path):
    with open(path, "r") as f:
        data = json.load(f)

    # convert to "lat,lon" format required by scraper
    return {
        city: f"{coords['lat']},{coords['lon']}"
        for city, coords in data.items()
    }


# =========================
# MAIN SCRAPER
# =========================

def run_scraper(results_folder: Path, locations_file: Path):

    results_folder.mkdir(parents=True, exist_ok=True)

    locations = load_locations(locations_file)
    query_files = list(QUERIES_FOLDER.glob("*.txt"))

    if not query_files:
        print("No query files found in /queries folder")
        return

    if not locations:
        print("No locations found in locations.json")
        return

    # =========================
    # ITERATE LOCATIONS FIRST
    # =========================

    for city, geo in locations.items():
        print(f"\n========== Processing location: {city} ==========\n")

        for query_file in query_files:

            category = query_file.stem
            output_file = results_folder / f"{city}_{category}.csv"

            print(f"Running: {city} + {category}")
            print(f"Output: {output_file}")

            # =========================
            # IMPORTANT FIX:
            # prevent docker treating file as directory
            # =========================

            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.touch(exist_ok=True)

            command = [
                "docker", "run",
                "-v", f"{query_file.resolve()}:/queries.txt",
                "-v", f"{output_file.resolve()}:/results.csv",
                DOCKER_IMAGE,
                "-input", "/queries.txt",
                "-results", "/results.csv",
                "-geo", geo,
                "-radius", RADIUS,
                "-zoom", ZOOM,
                "-depth", DEPTH,
                "-c", "4",
                "-exit-on-inactivity", "10m"
            ]

            result = subprocess.run(
                command,
                text=True
            )

            if result.returncode != 0:
                print(f"❌ FAILED: {city} + {category}\n")
                continue

            print(f"✅ SUCCESS: {city} + {category}\n")


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Google Maps data using Docker")
    parser.add_argument(
        "--results-folder",
        type=Path,
        default=Path("../results"),
        help="Output folder for results (default: ../results)"
    )
    parser.add_argument(
        "--locations-file",
        type=Path,
        default=Path("../misc/locations.json"),
        help="JSON file with location coordinates (default: ../misc/locations.json)"
    )
    
    args = parser.parse_args()
    run_scraper(args.results_folder, args.locations_file)