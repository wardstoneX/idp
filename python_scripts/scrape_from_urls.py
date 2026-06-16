#!/usr/bin/env python3
"""
Scrape Google Maps place pages from all URL files in results/*/url_txt/.

Discovers every url_txt/ folder under results/, then runs the scraper
once per .txt file.  Results land in the sibling urls/ folder as
urls/<name>.csv (url_<name>.txt → urls/<name>.csv).

Usage:
  python scrape_from_urls.py
"""

import subprocess
from pathlib import Path
import shlex
import time
from datetime import datetime
from urllib.parse import quote

# =========================
# CONFIG
# =========================

_SCRIPT_DIR = Path(__file__).resolve().parent  # python_scripts/
_PROJECT_DIR = _SCRIPT_DIR.parent              # idp/

RESULTS_BASE = _PROJECT_DIR / "results"
PROXIES_FILE = _PROJECT_DIR / "proxy-list.txt"
SCRAPER_BIN = _PROJECT_DIR.parent / "scraper" / "google-maps-scraper" / "google-maps-scraper"

PARALLELISM = "10"
BROWSER_POOL_SIZE = "10"
PAGES_PER_BROWSER = "1"
EXIT_ON_INACTIVITY = "3m"

# =========================
# LOGGING
# =========================

_log_file = None


def log_init(log_path: Path):
    global _log_file
    log_path.parent.mkdir(parents=True, exist_ok=True)
    _log_file = open(log_path, "w", encoding="utf-8")
    return log_path


def log(msg: str, level: str = "INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = {
        "INFO": "ℹ️ ", "OK": "✅", "FAIL": "❌", "WARN": "⚠️ ",
        "START": "🚀", "RAW": "",
    }.get(level, "")
    line = f"[{ts}] {prefix}{msg}"
    print(line, flush=True)
    if _log_file:
        _log_file.write(line + "\n")
        _log_file.flush()


def log_close():
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
            if "://" in line:
                proxies.append(line)
                continue

            parts = line.split(":")
            if len(parts) == 4:
                host, port, user, passwd = parts
                user_enc = quote(user, safe="")
                pass_enc = quote(passwd, safe="")
                proxies.append(f"http://{user_enc}:{pass_enc}@{host}:{port}")
            elif len(parts) == 2:
                host, port = parts
                proxies.append(f"http://{host}:{port}")
            else:
                proxies.append(line)
    return proxies


# =========================
# HELPERS
# =========================

def discover_url_files(results_base: Path):
    """Find every url_txt/*.txt file under results_base.

    Returns a list of (url_file, output_file) tuples where *output_file*
    points to ``urls/<name>.csv`` (sibling of url_txt/).
    """
    jobs = []
    for url_txt_dir in sorted(results_base.glob("*/url_txt")):
        urls_dir = url_txt_dir.parent / "urls"
        for txt_file in sorted(url_txt_dir.glob("*.txt")):
            output_file = urls_dir / f"{txt_file.stem}.csv"
            jobs.append((txt_file, output_file))
    return jobs


def run_scrape(url_file: Path, output_file: Path, proxies: list[str]):
    """Run the scraper for a single URL file.  Returns the exit code."""
    output_file.parent.mkdir(parents=True, exist_ok=True)

    command = [
        str(SCRAPER_BIN.resolve()),
        "-input", str(url_file.resolve()),
        "-results", str(output_file.resolve()),
        "-c", PARALLELISM,
        "-browser-pool-size", BROWSER_POOL_SIZE,
        "-pages-per-browser", PAGES_PER_BROWSER,
        "-exit-on-inactivity", EXIT_ON_INACTIVITY,
    ]
    if proxies:
        command.extend(["-proxies", ",".join(proxies)])

    log(f"CMD: {shlex.join(str(x) for x in command)}")
    log(f"Input:  {url_file.name}  →  Output: {output_file.name}")

    t0 = time.time()
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    for raw_line in proc.stdout:
        line = raw_line.rstrip("\n")
        log(line, "RAW")

    proc.wait()
    elapsed = time.time() - t0
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)
    return proc.returncode, mins, secs


# =========================
# MAIN
# =========================

def main():
    # --- init log ---
    log_stem = datetime.now().strftime("scrape_urls_%Y%m%d_%H%M%S")
    log_path = log_init(Path("../logs") / f"{log_stem}.log")
    log(f"Log file: {log_path.resolve()}")

    # --- discover URL files ---
    jobs = discover_url_files(RESULTS_BASE)
    if not jobs:
        log(f"No url_txt/*.txt files found under {RESULTS_BASE.resolve()}", "FAIL")
        log_close()
        return

    log(f"Found {len(jobs)} URL file(s) to process:")
    for url_file, output_file in jobs:
        log(f"  {url_file.relative_to(RESULTS_BASE)}  →  {output_file.relative_to(RESULTS_BASE)}")

    # --- proxies (loaded once) ---
    proxies = load_proxies(PROXIES_FILE)
    if proxies:
        log(f"Loaded {len(proxies)} proxies")
    else:
        log("No proxies loaded", "WARN")

    # --- process each URL file ---
    ok = 0
    fail = 0

    for idx, (url_file, output_file) in enumerate(jobs, start=1):

        # --- load URL count ---
        with open(url_file, "r", encoding="utf-8") as f:
            url_count = sum(1 for line in f if line.strip())
        log(f"\n{'='*60}")
        log(f"[{idx}/{len(jobs)}] SCRAPING: {url_file.name}  ({url_count} URLs)", "START")
        log(f"{'='*60}")

        try:
            rc, mins, secs = run_scrape(url_file, output_file, proxies)
            if rc == 0:
                log(f"[{idx}/{len(jobs)}] DONE in {mins}m {secs}s", "OK")
                ok += 1
            else:
                log(f"[{idx}/{len(jobs)}] FAILED (exit {rc}) in {mins}m {secs}s", "FAIL")
                fail += 1
        except KeyboardInterrupt:
            log(f"[{idx}/{len(jobs)}] Interrupted by user — stopping", "WARN")
            break
        except Exception as e:
            log(f"[{idx}/{len(jobs)}] EXCEPTION: {e}", "FAIL")
            fail += 1

    log(f"\n{'='*60}")
    log(f"ALL DONE — {ok} ok, {fail} failed, {len(jobs)} total")
    log(f"Log saved to: {log_path.resolve()}")
    log_close()


if __name__ == "__main__":
    main()
