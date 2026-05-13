import pandas as pd
import numpy as np
from pathlib import Path

from utils import (
    load_locations,
    haversine,
    safe_json_load,
    extract_open_close,
    extract_popular_times,
    is_open_during_window,
    parse_time_window
)

data_folder = Path("../data")
output_folder = Path("../output")
radius = 1000  # in meters
time_window = "20:00-06:00"  # in HH:MM-HH:MM
locations = load_locations()



# -------------------------
# PROCESS SINGLE FILE
# -------------------------
def process_file(input_path, output_path, location):

    # -------------------------
    # VALIDATE GLOBALS
    # -------------------------
    if "locations" not in globals():
        raise RuntimeError("Missing global: locations")

    if "radius" not in globals():
        raise RuntimeError("Missing global: radius")

    if "time_window" not in globals():
        raise RuntimeError("Missing global: time_window")

    df = pd.read_csv(input_path)
    rows = []

    center = locations.get(location)

    query_intervals = parse_time_window(time_window) if time_window else None

    for _, row in df.iterrows():

        lat = row.get("latitude")
        lon = row.get("longitude")

        # -------------------------
        # DISTANCE FILTER
        # -------------------------
        if (
            pd.notna(lat)
            and pd.notna(lon)
            and center
            and radius is not None
        ):
            dist = haversine(
                center["lat"],
                center["lon"],
                float(lat),
                float(lon)
            )

            if dist * 1000 > float(radius):
                continue

        open_hours = safe_json_load(row.get("open_hours"))
        pop_times = safe_json_load(row.get("popular_times"))

        open_features = extract_open_close(open_hours)

        # -------------------------
        # TIME FILTER
        # -------------------------
        if query_intervals:
            if not is_open_during_window(open_features, query_intervals):
                continue

        pop_features = extract_popular_times(pop_times)

        rows.append({
            "name": row.get("title"),
            "place_id": row.get("place_id"),
            "lat": lat,
            "lon": lon,
            "location": location,
            **open_features,
            **pop_features
        })

    pd.DataFrame(rows).to_csv(output_path, index=False)

    print("Saved →", output_path)

# -------------------------
# PROCESS ALL FILES
# -------------------------
def process_all():
    output_folder.mkdir(exist_ok=True)

    for file in data_folder.glob("*.csv"):

        location = file.stem

        if location not in locations:
            print(f"Skipping {file.name}")
            continue

        out_file = output_folder / f"{location}_processed.csv"
        
        if out_file.exists():
            print(f"Already processed → {out_file.name}")
            continue

        process_file(
            input_path=file,
            output_path=out_file,
            location=location
        )

if __name__ == "__main__":
    process_all()