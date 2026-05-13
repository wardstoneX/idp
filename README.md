# Night Mobility Scraper

Scrapes Google Maps place data around Munich transit stations, processes opening hours & popular times, and filters for places open during night-time windows (20:00–06:00).

## Folder Structure

```
scraper/
├── environment.yml          # Conda environment (night-mobility)
├── README.md
├── data/                    # Raw CSV exports from Google Maps scraper
│   ├── frankfurterring.csv
│   ├── marienplatz.csv
│   ├── munchenhauptbahnhof.csv
│   ├── ostbahnhof.csv
│   ├── pasing.csv
│   └── sendlingertor.csv
├── output/                  # Processed CSV: distance + time-filtered results
│   ├── frankfurterring_processed.csv
│   ├── marienplatz_processed.csv
│   ├── munchenhauptbahnhof_processed.csv
│   ├── ostbahnhof_processed.csv
│   ├── pasing_processed.csv
│   └── sendlingertor_processed.csv
├── result/                  # Category-specific scraped results (per location × category)
│   ├── marienplatz_entertainment.csv
│   ├── marienplatz_food.csv
│   ├── ...
│   └── sendlingerTor_transportation.csv
├── queries/                 # Google Maps search query strings per category
│   ├── all-queries.txt
│   ├── entertainment.txt
│   ├── food.txt
│   ├── services.txt
│   ├── shopping.txt
│   └── transportation.txt
├── misc/
│   └── locations.json       # Station coordinates {name: {lat, lon}}
└── python_scripts/
    ├── utils.py             # Core library: time parsing, distance, filtering
    ├── test.py              # Test suite for all utils.py functions
    ├── process_lokal.py     # Main pipeline: filter raw CSVs → processed CSVs
    ├── scrape.py            # Google Maps scraper (local run)
    ├── scrape_docker.py     # Google Maps scraper (Dockerized)
    ├── analyse.py           # Analysis/statistics on processed data
    └── verify.py            # (planned) Output sanity checks
```

## Pipeline Overview

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  scrape.py   │ ──▶ │   data/*.csv     │ ──▶ │ process_lokal.py │
│ (Google Maps)│     │ (raw scraped)    │     │ (filter + enrich) │
└──────────────┘     └──────────────────┘     └────────┬─────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │ output/*.csv     │
                                              │ (distance+time   │
                                              │  filtered)       │
                                              └──────────────────┘
                                                       │
                                                       ▼
                                              ┌──────────────────┐
                                              │  analyse.py      │
                                              │ (statistics)     │
                                              └──────────────────┘
```

## Python Scripts

### `utils.py` — Core Library

Shared utility functions used across the project:

| Function | Description |
|---|---|
| `normalize_time(t, fallback_suffix)` | Converts time strings (`"5:30pm"`, `"5.30 PM"`, `"5pm"`, `"14:00"`) to float hours (0.0–24.0). Accepts colon or dot separators, optional am/pm with spaces. |
| `parse_interval(raw)` | Parses an opening-hours interval string (`"9am–5pm"`) into `[(start, end), ...]` tuples. Splits overnight intervals (e.g. `"10pm–2am"` → `[(22,24),(0,2)]`). Returns `[(0,0)]` for `"Closed"`, `[(0,24)]` for `"Open 24 hours"`. |
| `normalize_interval(s, e)` | Splits an interval crossing midnight into two `[0,24]` segments. |
| `parse_time_window(window)` | Parses a query time window (`"20:00-06:00"`) for the night-mobility filter. Accepts optional spaces around dash. |
| `extract_global_suffix(raw)` | Extracts trailing "am"/"pm" suffix from a raw time string. |
| `get_suffix(x)` | Finds "am" or "pm" anywhere in a string via regex search. |
| `extract_open_close(open_hours_json)` | Converts Google Maps `open_hours` JSON into structured `{Day_openHours: [(start,end),...]}` per day of week. |
| `extract_popular_times(pop_json)` | Converts Google Maps `popular_times` JSON into `{Day: {hour_int: value}}`. |
| `is_open_during_window(open_features, query_intervals)` | Checks if a place is open during any of the given query time windows. |
| `haversine(lat1, lon1, lat2, lon2)` | Calculates great-circle distance in km between two coordinates. |
| `safe_json_load(x)` | Robust JSON parser handling single-quotes, unicode escapes, NaN, and already-parsed dicts. |
| `normalize_dashes(s)` | Replaces Unicode dash variants (en-dash, em-dash, minus) with ASCII `-`. |
| `load_locations(path)` | Loads station coordinates from `locations.json`. |

### `process_lokal.py` — Main Processing Pipeline

Filters raw scraped data by distance and opening hours:

1. Reads each `data/*.csv`
2. For each place, computes distance to the transit station via `haversine()`
3. Skips places farther than 1000 m
4. Parses `open_hours` JSON and checks if the place is open during `20:00–06:00`
5. Extracts `popular_times` data
6. Writes filtered results to `output/*_processed.csv`

**Configurable globals:**
- `radius = 1000` — max distance in meters
- `time_window = "20:00-06:00"` — night-time window

**Skips already-processed files** — delete `output/*.csv` to force re-run.

### `scrape.py` / `scrape_docker.py` — Google Maps Scraper

Scrapes Google Maps for places around each Munich transit station using query strings from `queries/`. Outputs raw CSV files to `data/`.

### `analyse.py` — Analysis & Statistics

Analyzes the processed data, showing statistics like:
- Shortest/longest `open_hours` strings
- Shortest/longest `popular_times` strings
- Complexity metrics for open hours and popular times

### `test.py` — Test Suite

Tests all functions in `utils.py` with 50–65 test cases per function. Run with:

```bash
cd python_scripts
conda activate night-mobility
python test.py
```

### `verify.py` — (Planned)

Will verify the correctness of processed output files.

## Data Files

### `data/*.csv`
Raw Google Maps place data with columns including: `title`, `place_id`, `latitude`, `longitude`, `open_hours` (JSON string), `popular_times` (JSON string).

### `output/*_processed.csv`
Filtered output with added columns:
- `name`, `place_id`, `lat`, `lon`, `location`
- `Monday_openHours` through `Sunday_openHours` — parsed interval lists
- `Monday` through `Sunday` — popular times hour→value dicts

### `result/*.csv`
Category-specific scraped results (e.g. `marienplatz_food.csv`, `ostbahnhof_entertainment.csv`).

### `misc/locations.json`
```json
{
  "marienplatz": {"lat": 48.1371, "lon": 11.5754},
  "ostbahnhof": {"lat": 48.1273, "lon": 11.6043},
  ...
}
```

### `queries/*.txt`
Google Maps search queries, one per line, organized by category.

## Setup

```bash
conda env create -f environment.yml
conda activate night-mobility
```

## Usage

```bash
# Scrape Google Maps data
python python_scripts/scrape.py

# Process and filter for night-time open places
python python_scripts/process_lokal.py

# Analyze results
python python_scripts/analyse.py

# Run tests
python python_scripts/test.py
```
