

import subprocess
from pathlib import Path
import shlex
import json
import argparse
import sys
from urllib.parse import quote
from datetime import datetime
import math
import time
import threading

from utils import point_to_bbox



# =========================
# CONFIG
# =========================

ALL_QUERIES_FILE = Path("queries/all-queries.txt")
PROXIES_FILE = Path("proxy-list.txt")


RADIUS = "1000"
ZOOM = "16"
DEPTH = "5"
PARALLELISM = "8"
BROWSER_POOL_SIZE = "8"
PAGES_PER_BROWSER = "1"
EXIT_ON_INACTIVITY = "1m"

# ---- grid-bbox mode ----
GRID_CELL_KM = "0.5"   # 500mo radi per grid cell
BBOX_SIZE_KM = 2.0      # 2km × 2km box centered on location

# =========================
# LOGGING
# =========================x

_log_file = None  # set once results_folder is known

def log_init(log_path: Path):
    """Open the log file for writing."""
    global _log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _log_file = open(log_path, "w", encoding="utf-8")
    return log_path

def log(msg: str, level: str = "INFO"):
    """Timestamped log output — prints to stdout and writes to log file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {"INFO": "ℹ️ ", "OK": "✅", "FAIL": "❌", "WARN": "⚠️ ", "START": "🚀", "GROUP": "📦", "RAW": ""}.get(level, "")
    line = f"[{ts}] {prefix}{msg}"
    print(line, flush=True)
    if _log_file:
        _log_file.write(line + "\n")
        _log_file.flush()

def log_close():
    """Close the log file."""
    global _log_file
    if _log_file:
        _log_file.close()
        _log_file = None

# =========================
# LOAD PROXIES 
# =========================


def load_proxies(path: Path):
    if not path.exists():
        return []

    proxies = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # If proxy already contains a scheme, use as-is
            if "://" in line:
                proxies.append(line)
                continue

            parts = line.split(":")

            # host:port:user:pass  -> http://user:pass@host:port
            if len(parts) == 4:
                host, port, user, passwd = parts
                user_enc = quote(user, safe="")
                pass_enc = quote(passwd, safe="")
                proxies.append(f"http://{user_enc}:{pass_enc}@{host}:{port}")
                continue

            # host:port -> default to http://host:port
            if len(parts) == 2:
                host, port = parts
                proxies.append(f"http://{host}:{port}")
                continue

            # Fallback: include raw line
            proxies.append(line)

    return proxies

# =========================
# LOAD LOCATIONS
# =========================

def load_locations(path: Path):
    """Return {city: (lat, lon)} from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {
        city: (coords["lat"], coords["lon"])
        for city, coords in data.items()
    }

# =========================
# MAIN SCRAPER
# =========================

def run_scraper(results_folder: Path, locations_file: Path):

    results_folder.mkdir(parents=True, exist_ok=True)

    # ---- init log file ----
    log_stem = datetime.now().strftime("scrape_%Y%m%d_%H%M%S")
    log_path = log_init(Path("logs") / f"{log_stem}.log")
    log(f"Log file: {log_path.resolve()}")

    locations = load_locations(locations_file)
    proxies = load_proxies(PROXIES_FILE)

    if not locations:
        log("No locations found in locations file", "FAIL")
        return

    if not ALL_QUERIES_FILE.exists():
        log(f"Query file not found: {ALL_QUERIES_FILE}", "FAIL")
        return

    # ---- load & deduplicate queries ----
    with open(ALL_QUERIES_FILE, "r", encoding="utf-8") as f:
        raw = [line.strip() for line in f if line.strip()]

    before = len(raw)
    queries = list(dict.fromkeys(raw))  # preserves order, removes duplicates
    after = len(queries)
    log(f"Queries loaded: {before} lines -> {after} unique ({before - after} duplicates removed)")

    total_locations = len(locations)
    total_runs = total_locations
    run_counter = 0
    failed_runs = 0

    log(f"{'='*60}")
    log(f"STARTING BATCH: {total_locations} location(s) x {after} queries = {total_runs} total runs")
    log(f"{'='*60}")

    # =========================
    # ITERATE LOCATIONS
    # =========================

    for city_idx, (city, (lat, lon)) in enumerate(locations.items(), start=1):
        bbox = point_to_bbox(lat, lon, BBOX_SIZE_KM)
        run_counter += 1

        output_file = results_folder / f"{city}.csv"
        failed_file = results_folder / f"{city}_failed.jsonl"
        skipped_file = results_folder / f"{city}_skipped.jsonl"

        log(f"\n📍 LOCATION {city_idx}/{total_locations}: {city} ({lat:.4f}, {lon:.4f})")
        log(f"   🗺️  BBox: {bbox} ({BBOX_SIZE_KM}km x {BBOX_SIZE_KM}km, cells: {GRID_CELL_KM}km)")
        log(
            f"  📦 run {run_counter}/{total_runs} | "
            f"{after} queries -> {output_file.name}",
            "GROUP",
        )

        output_file.parent.mkdir(parents=True, exist_ok=True)

        command = [
            "./google-maps-scraper/google-maps-scraper",
            "-input", str(ALL_QUERIES_FILE.resolve()),
            "-results", str(output_file.resolve()),
            "-failed-file", str(failed_file.resolve()),
            "-skipped-file", str(skipped_file.resolve()),
            "-grid-bbox", bbox,
            "-grid-cell", GRID_CELL_KM,
            "-radius", RADIUS,
            "-zoom", ZOOM,
            "-depth", DEPTH,
            "-c", PARALLELISM,
            "-browser-pool-size", BROWSER_POOL_SIZE,
            "-pages-per-browser", PAGES_PER_BROWSER,
            "-exit-on-inactivity", EXIT_ON_INACTIVITY,
        ]

        if proxies:
            command.extend(["-proxies", ",".join(proxies)])

        log(f"      CMD: {shlex.join(str(x) for x in command)}")

        proc = None
        exited_seen_at = None  # timestamp when "scrapemate exited" first seen
        stats_jobs_completed = 0
        stats_jobs_failed = 0
        had_errors = False
        EXIT_GRACE = 30        # seconds to wait after exited message before force-kill

        def _read_stdout():
            nonlocal exited_seen_at, stats_jobs_completed, stats_jobs_failed, had_errors
            for raw_line in proc.stdout:
                line = raw_line.rstrip("\n")
                log(line, "RAW")
                if "scrapemate exited" in line and exited_seen_at is None:
                    exited_seen_at = time.time()
                # Capture scrapemate stats
                if '"message":"scrapemate stats"' in line:
                    try:
                        stats = json.loads(line)
                        stats_jobs_completed = stats.get("numOfJobsCompleted", 0)
                        stats_jobs_failed = stats.get("numOfJobsFailed", 0)
                    except Exception:
                        pass
                # Detect errors
                if '"level":"error"' in line:
                    had_errors = True

        try:
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            reader = threading.Thread(target=_read_stdout, daemon=True)
            reader.start()

            # Wait for process to exit, but check for "scrapemate exited"
            while True:
                try:
                    proc.wait(timeout=2)
                    break  # exited naturally
                except subprocess.TimeoutExpired:
                    if exited_seen_at and (time.time() - exited_seen_at) > EXIT_GRACE:
                        log(
                            f"      'scrapemate exited' seen {EXIT_GRACE}s ago -- force-killing hung process",
                            "WARN",
                        )
                        break

        except Exception as e:
            log(f"      EXCEPTION: {e}", "FAIL")
            failed_runs += 1
            continue
        finally:
            # Ensure scraper is dead before next run
            if proc is not None:
                try:
                    proc.kill()
                    proc.wait(timeout=5)
                except Exception:
                    pass

        # Drain any remaining buffered output from the reader thread
        reader.join(timeout=5)

        # Success = scraper printed "scrapemate exited" before we killed it
        if exited_seen_at is not None:
            log(f"      OK", "OK")
        else:
            log(f"      FAILED (no 'scrapemate exited' seen)", "FAIL")
            failed_runs += 1

        time.sleep(10)  # cooldown between runs

    # =========================
    # FINAL SUMMARY
    # =========================
    log(f"{'='*60}")
    log(f"ALL DONE -- {run_counter} runs, {failed_runs} failed, {run_counter - failed_runs} succeeded")
    log(f"Results folder: {results_folder.resolve()}")
    log(f"{'='*60}")

    # ---- close log ----
    log(f"Log saved to: {log_path.resolve()}")
    log_close()


# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape Google Maps data for locations")
    parser.add_argument(
        "--results-folder",
        type=Path,
        default=Path("results_new"),
        help="Output folder for results (default: results_new)"
    )
    parser.add_argument(
        "--locations-file",
        type=Path,
        default=Path("locations.json"),
        help="JSON file with location coordinates (default: locations.json)"
    )
    
    args = parser.parse_args()
    run_scraper(args.results_folder, args.locations_file)

