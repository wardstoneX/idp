import subprocess
from pathlib import Path
import json

# =========================
# CONFIG
# =========================

RESULTS_FOLDER = Path("results_new")
LOCATIONS_FILE = Path("locations.json")
ALL_QUERIES_FILE = Path("queries/all-queries.txt")

RADIUS = "1000"
ZOOM = "16"
DEPTH = "3"
PARALLELISM = "1"

# =========================
# LOAD LOCATIONS
# =========================

def load_locations(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        city: f"{coords['lat']},{coords['lon']}"
        for city, coords in data.items()
    }

# =========================
# MAIN SCRAPER
# =========================

def run_scraper():

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    locations = load_locations(LOCATIONS_FILE)

    if not locations:
        print("No locations found in locations.json")
        return

    if not ALL_QUERIES_FILE.exists():
        print("all-queries.txt not found")
        return

    # =========================
    # ITERATE LOCATIONS
    # =========================

    for city, geo in locations.items():

        print(f"\n========== Processing location: {city} ==========\n")

        output_file = RESULTS_FOLDER / f"{city}.csv"

        print(f"Running scraper for: {city}")
        print(f"Output: {output_file}")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.touch(exist_ok=True)

        command = [
            "./google-maps-scraper/google-maps-scraper",
            "-input", str(ALL_QUERIES_FILE.resolve()),
            "-results", str(output_file.resolve()),
            "-geo", geo,
            "-radius", RADIUS,
            "-zoom", ZOOM,
            "-depth", DEPTH,
            "-c", PARALLELISM,
            "-exit-on-inactivity", "10m"
        ]

        result = subprocess.run(
            command,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ FAILED: {city}\n")
            continue

        print(f"✅ SUCCESS: {city}\n")


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run_scraper()