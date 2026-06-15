# Night Mobility Scraper

Scrapes Google Maps place data around Munich transit stations, processes opening hours & popular times, and filters for places open during night-time windows (20:00–06:00).


## Clone
Clone repository (including submodules):

```bash
git clone --recurse-submodules https://github.com/wardstoneX/idp.git
# or, if you've already cloned the repo:
git submodule update --init --recursive
```

## Folder Structure

```
scraper/
├── environment.yml              # Conda environment (night-mobility)
├── README.md
├── .gitignore
├── .env                         # (gitignored) API keys / secrets
├── google-maps-scraper/         # External Go scraper (gitignored, built from source)
├── data/                        # Raw CSV exports from Google Maps scraper
├── output/                      # Processed CSV: distance + time-filtered (currently empty)
├── result/                      # Category-specific scraped results (per location × category)
├── queries/                     # Google Maps search query strings per category
├── misc/
│   └── locations.json           # Station coordinates {name: {lat, lon}}
└── python_scripts/
    ├── utils.py                 # Core library: time parsing, distance, filtering
    ├── test.py                  # Test suite (50–65 cases per function)
    ├── scrape_lokal.py          # Google Maps scraper (calls external Go binary)
    ├── scrape_docker.py         # Google Maps scraper (Docker variant)
    ├── process.py               # Main pipeline: filter raw CSVs → processed CSVs
    ├── analyse.py               # Quick statistics on a data CSV
    └── verify.py                # (planned) Output sanity checks
```

## Pipeline Overview

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│ scrape_lokal.py  │ ──▶ │   data/*.csv     │ ──▶ │  process.py  │
│ (Google Maps     │     │ (raw scraped)    │     │ (filter +    │
│  scraper)        │     │                  │     │  enrich)     │
└──────────────────┘     └──────────────────┘     └──────┬───────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │ output/*.csv     │
                                                │ (distance+time   │
                                                │  filtered)       │
                                                └────────┬─────────┘
                                                         │
                                                         ▼
                                                ┌──────────────────┐
                                                │  analyse.py      │
                                                │ (statistics)     │
                                                └──────────────────┘
```

## Time Format Handling

All times are internally converted to **decimal hours** (0.0–24.0) for arithmetic and comparison.

### Conversion Rules

| Input format | Example | Decimal | Rule |
|---|---|---|---|
| `H:MMam` / `H:MMpm` | `"10:30am"` | `10.5` | 12h clock → minutes ÷ 60 |
| `H:MMpm` | `"5:30pm"` | `17.5` | PM → +12 hours |
| `H.MMam` / `H.MMpm` | `"5.30 PM"` | `17.5` | Dot accepted as colon |
| `HH:MM` (24h) | `"14:00"` | `14.0` | No am/pm → 24h clock |
| Bare `Hpm` / `Ham` | `"5pm"` | `17.0` | No minutes → `.0` |
| `"Closed"` | — | `[(0, 0)]` | Zero-length interval |

### Midnight Handling

Midnight is the critical edge case. The parser distinguishes between **midnight-as-start** and **midnight-as-end**:

| Time | Role | Value | Reason |
|---|---|---|---|
| `"12:00am"` | Start of interval | `0.0` | Beginning of day |
| `"12:00am"` | End of interval | `24.0` | End of day (closing at midnight) |

**Example:** `"4pm–12am"` → start=`16.0`, end=`0.0` → adjusted to `24.0` → interval `[(16, 24)]`  
A place open 4pm to midnight is open `[16:00–24:00]`, not `[16:00–00:00]`.

### Overnight Intervals

When closing time is before opening time (crosses midnight), the interval is **split into two segments**:

| Input | Parsed | Meaning |
|---|---|---|
| `"10pm–2am"` | `[(22, 24), (0, 2)]` | 10pm–midnight, midnight–2am |
| `"8pm–4am"` | `[(20, 24), (0, 4)]` | 8pm–midnight, midnight–4am |
| `"5pm–4am"` | `[(17, 24), (0, 4)]` | 5pm–midnight, midnight–4am |

### Query Time Window

The night-mobility query window `"20:00-06:00"` is parsed the same way:

```
"20:00-06:00" → [(20, 24), (0, 6)]
```

A place is considered "open during the window" if **any** of its daily opening intervals overlap with **any** segment of the query window. Overlap check: `max(open_start, query_start) < min(open_end, query_end)`.

### Am/Pm Suffix Inheritance

When only one side of an interval has an am/pm suffix, the other side inherits it from the raw string's trailing suffix or from the other side:

| Input | Left gets | Right gets | Result |
|---|---|---|---|
| `"9–11pm"` | inherits `"pm"` | `"pm"` (explicit) | `[(21, 23)]` |
| `"9am–11"` | `"am"` (explicit) | inherits `"am"` | `[(9, 11)]` |
| `"5:30–7:30 pm"` | inherits `"pm"` | `"pm"` (explicit) | `[(17.5, 19.5)]` |

## Python Scripts

### `utils.py` — Core Library

Shared utility functions used across the project:

| Function | Description |
|---|---|
| `normalize_time(t, fallback_suffix)` | Converts time strings (`"5:30pm"`, `"5.30 PM"`, `"5pm"`, `"14:00"`) to float hours (0.0–24.0). Accepts colon or dot separators, optional am/pm with spaces, bare hours like `"5pm"`. |
| `parse_interval(raw)` | Parses an opening-hours interval string (`"9am–5pm"`) into `[(start, end), ...]` tuples. Splits overnight intervals (e.g. `"10pm–2am"` → `[(22,24),(0,2)]`). Returns `[(0,0)]` for `"Closed"`, `[(0,24)]` for `"Open 24 hours"`. |
| `normalize_interval(s, e)` | Splits an interval crossing midnight into two `[0,24]` segments. |
| `parse_time_window(window)` | Parses a query time window (`"20:00-06:00"`) for the night-mobility filter. Accepts optional spaces around dash (`"10:00 - 14:00"`). |
| `extract_global_suffix(raw)` | Extracts trailing "am"/"pm" suffix from a raw time string. |
| `get_suffix(x)` | Finds "am" or "pm" anywhere in a string via regex search. |
| `extract_open_close(open_hours_json)` | Converts Google Maps `open_hours` JSON into structured `{Day_openHours: [(start,end),...]}` per day of week. |
| `extract_popular_times(pop_json)` | Converts Google Maps `popular_times` JSON into `{Day: {hour_int: value}}`. |
| `is_open_during_window(open_features, query_intervals)` | Checks if a place is open during any of the given query time windows. |
| `haversine(lat1, lon1, lat2, lon2)` | Calculates great-circle distance in km between two coordinates. |
| `safe_json_load(x)` | Robust JSON parser handling single-quotes, unicode escapes, NaN, and already-parsed dicts. |
| `normalize_dashes(s)` | Replaces Unicode dash variants (en-dash, em-dash, minus) with ASCII `-`. |
| `load_locations(path)` | Loads station coordinates from `misc/locations.json`. |

### `process.py` — Main Processing Pipeline

Filters raw scraped data by distance and opening hours:

1. Reads each `data/*.csv`
2. For each place, computes distance to the transit station via `haversine()`
3. Skips places farther than **1000 m**
4. Parses `open_hours` JSON and checks if the place is open during **20:00–06:00**
5. Extracts `popular_times` data
6. Writes filtered results to `output/*_processed.csv`

**Configurable globals at top of file:**
- `radius = 1000` — max distance in meters
- `time_window = "20:00-06:00"` — night-time window

**Note:** If output files already exist, `process.py` skips them silently. To force a re-run:
```bash
rm output/*_processed.csv
python python_scripts/process.py
```

### `scrape_lokal.py` — Google Maps Scraper

Calls the external [`google-maps-scraper`](https://github.com/gosom/google-maps-scraper) Go binary for each location in `misc/locations.json`, using all query strings from `queries/all-queries.txt`. Outputs raw CSV files.

Uses these scraper parameters:
- **Radius:** 1000 m
- **Zoom:** 16
- **Depth:** 3
- **Parallelism:** 1

### `scrape_docker.py` — Docker Variant

Alternative scraper script for Docker-based runs.

### `analyse.py` — Quick Statistics

Reads a single CSV (default: `data/marienplatz.csv`) and prints:
- Shortest/longest `open_hours` strings
- Shortest/longest `popular_times` strings  
- Complexity scores for open hours and popular times

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
Raw Google Maps place data scraped by the external Go tool. Columns include: `title`, `place_id`, `latitude`, `longitude`, `open_hours` (JSON string), `popular_times` (JSON string).

### `output/*.csv` (empty until processed)
Filtered output from `process.py` with added columns:
- `name`, `place_id`, `lat`, `lon`, `location`
- `Monday_openHours` through `Sunday_openHours` — parsed interval lists
- `Monday` through `Sunday` — popular times hour→value dicts

### `result/*.csv`
Category-specific scraped results for 7 locations × 5 categories:
- **Locations:** marienplatz, maxWeberPlatz, muenchnerFreiheit, ostbahnhof, pasing, rosenheimerPlatz, sendlingerTor
- **Categories:** entertainment, food, services, shopping, transportation

### `misc/locations.json`
```json
{
  "marienplatz": {"lat": 48.1371, "lon": 11.5754},
  "ostbahnhof": {"lat": 48.1273, "lon": 11.6043},
  ...
}
```

### `queries/*.txt`
Google Maps search queries in German, one per line, organized by category.

## External Dependencies

### Google Maps Scraper

The scraper uses [`gosom/google-maps-scraper`](https://github.com/gosom/google-maps-scraper) — a Go-based tool that uses Playwright to scrape Google Maps.

**Option 1 — Docker (recommended):**
```bash
docker pull gosom/google-maps-scraper
```

**Option 2 — Build from source (requires Go 1.25.6+):**
```bash
git clone https://github.com/gosom/google-maps-scraper.git
cd google-maps-scraper
go mod download
go build
# The binary is then called by scrape_lokal.py:
./google-maps-scraper -input example-queries.txt -results results.csv -exit-on-inactivity 3m
```

Place the `google-maps-scraper` directory (or symlink the binary) at the project root so `scrape_lokal.py` can call `./google-maps-scraper/google-maps-scraper`.

## Setup

```bash
conda env create -f environment.yml
conda activate night-mobility
```

## Usage

```bash
# 1. Scrape Google Maps data (requires the Go scraper)
python python_scripts/scrape_lokal.py

# 2. Process and filter for night-time open places
python python_scripts/process.py

# 3. Analyze results
python python_scripts/analyse.py

# Run tests anytime
python python_scripts/test.py
```
