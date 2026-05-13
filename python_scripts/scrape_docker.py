import subprocess
from pathlib import Path
import json


# =========================
# CONFIG
# =========================

QUERIES_FOLDER = Path("../queries")
RESULTS_FOLDER = Path("../results")
LOCATIONS_FILE = Path("../misc/locations.json")

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

def run_scraper():

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    locations = load_locations(LOCATIONS_FILE)
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
            output_file = RESULTS_FOLDER / f"{city}_{category}.csv"

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
    run_scraper()