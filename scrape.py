import subprocess
from pathlib import Path
import sys
import argparse

# =========================
# CONFIG
# =========================

RESULTS_FOLDER = Path("results/results_berlin")
LOCATIONS_FILE = Path("misc/locations_berlin.json")

SCRAPE_LOKAL_SCRIPT = Path("python_scripts/scrape_lokal.py")
SCRAPE_DOCKER_SCRIPT = Path("python_scripts/scrape_docker.py")

SCRAPER_TYPE = "local"


# =========================
# MAIN SCRAPER
# =========================

def run_scraper(scraper_type="local", results_folder=None, locations_file=None):

    if results_folder is None:
        results_folder = RESULTS_FOLDER
    if locations_file is None:
        locations_file = LOCATIONS_FILE

    scraper_type = scraper_type.lower()

    if scraper_type == "local":
        script = SCRAPE_LOKAL_SCRIPT
    elif scraper_type == "docker":
        script = SCRAPE_DOCKER_SCRIPT
    else:
        print(f"Error: Unknown scraper type '{scraper_type}'")
        return 1

    if not script.exists():
        print(f"Error: script not found at {script.resolve()}")
        return 1

    command = [
        sys.executable,
        str(script.resolve()),
        "--results-folder", str(results_folder.resolve()),
        "--locations-file", str(locations_file.resolve())
    ]

    print(f"Using scraper: {scraper_type}")
    print(f"Running: {' '.join(command)}\n")

    return_code = subprocess.call(command)

    print(f"\nFinished with exit code: {return_code}")
    return return_code


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--scraper",
        choices=["local", "docker"],
        default=SCRAPER_TYPE
    )

    parser.add_argument(
        "--results-folder",
        type=Path,
        default=RESULTS_FOLDER
    )

    parser.add_argument(
        "--locations-file",
        type=Path,
        default=LOCATIONS_FILE
    )

    args = parser.parse_args()

    exit_code = run_scraper(
        args.scraper,
        args.results_folder,
        args.locations_file
    )

    sys.exit(exit_code)