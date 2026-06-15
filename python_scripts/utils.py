import json
import re
import math

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# =========================================================
# LOAD LOCATIONS
# =========================================================
def load_locations(path="../misc/locations.json"):
    with open(path, "r") as f:
        return json.load(f)


# =========================================================
# BBOX FROM CENTER POINT
# =========================================================
def point_to_bbox(lat: float, lon: float, size_km: float) -> str:
    """
    Return a bounding-box string for a square of size_km × size_km
    centered on (lat, lon). Format: "minLat,minLon,maxLat,maxLon".
    """
    half = size_km / 2.0
    delta_lat = half / 111.32
    delta_lon = half / (111.32 * math.cos(math.radians(lat)))
    return f"{lat - delta_lat:.6f},{lon - delta_lon:.6f},{lat + delta_lat:.6f},{lon + delta_lon:.6f}"


# =========================================================
# HAVERSINE DISTANCE
# =========================================================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # km

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.asin(math.sqrt(a))


# =========================================================
# SAFE JSON LOADER
# =========================================================
def safe_json_load(x):
    if x is None or (isinstance(x, float) and x != x):
        return None

    if isinstance(x, dict):
        return x

    if not isinstance(x, str):
        return None

    try:
        return json.loads(x)
    except:
        pass

    try:
        return json.loads(x.encode().decode("unicode_escape"))
    except:
        pass

    try:
        return json.loads(x.replace("'", '"'))
    except:
        return None


# =========================================================
# SPLIT OVERNIGHT INTERVALS
# =========================================================
def normalize_interval(s, e):
    # only split if crossing midnight
    if s <= e:
        return [(s, e)]
    return [(s, 24), (0, e)]


# =========================================================
# TIME WINDOW PARSER (QUERY)
# =========================================================
def parse_time_window(window):
    match = re.match(r"^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$", window.strip())
    if not match:
        return None

    h1, m1, h2, m2 = map(int, match.groups())

    start = h1 + m1 / 60
    end = h2 + m2 / 60

    return normalize_interval(start, end)


# =========================================================
# GLOBAL SUFFIX DETECTION
# =========================================================
def extract_global_suffix(raw):
    raw = raw.strip().lower()

    if raw.endswith("am"):
        return raw[:-2].strip(), "am"

    if raw.endswith("pm"):
        return raw[:-2].strip(), "pm"

    return raw, None


# =========================================================
# TIME NORMALIZER
# =========================================================
def normalize_time(t, fallback_suffix=None):
    t = t.strip().lower()

    # Pattern 1: HH:MM or HH.MM + optional am/pm (e.g. "5:30am", "5.30 pm")
    match = re.match(r"(\d{1,2})[:.](\d{2})\s*(am|pm)?", t)
    if match:
        h = int(match.group(1))
        m = int(match.group(2))
        ampm = match.group(3)
    else:
        # Pattern 2: bare HH + optional am/pm (e.g. "5pm", "11", "14")
        match = re.match(r"(\d{1,2})\s*(am|pm)?$", t)
        if not match:
            return None
        h = int(match.group(1))
        m = 0
        ampm = match.group(2)

    # -------------------------
    # CASE 1: 24h format (NO am/pm, NO fallback)
    # -------------------------
    if ampm is None:
        if fallback_suffix is None:
            return h + m / 60
        ampm = fallback_suffix

    # -------------------------
    # CASE 2: 12h format
    # -------------------------
    if ampm == "am":
        h = 0 if h == 12 else h
    else:
        h = 12 if h == 12 else h + 12

    return h + m / 60


# =========================================================
# PARSE SINGLE OPEN INTERVAL
# =========================================================
def parse_interval(raw):
    raw = normalize_dashes(raw.replace("\u202f", " ").strip().lower())

    if "invalid" in raw:
        return None
    if "closed" in raw:
        return [(0.0, 0.0)]
    if "open 24" in raw or raw.strip() == "24h":
        return [(0.0, 24.0)]

    if "-" not in raw:
        return None

    left, right = raw.split("-", 1)
    left = left.strip()
    right = right.strip()

    # clean suffix extraction (STRINGS ONLY)
    left_suffix = get_suffix(left)
    right_suffix = get_suffix(right)
    global_suffix = get_suffix(raw)

    # inheritance rules
    if not right_suffix:
        right_suffix = left_suffix or global_suffix

    if not left_suffix:
        left_suffix = global_suffix

    s = normalize_time(left, left_suffix)
    e = normalize_time(right, right_suffix)

    if s is None or e is None:
        return None

    # midnight as end-of-day → 24.0, not 0.0
    if e == 0.0:
        e = 24.0

    return normalize_interval(s, e)

def normalize_dashes(s):
    return (
        s.replace("–", "-")
         .replace("—", "-")
         .replace("-", "-")
         .replace("−", "-")
    )
    
def get_suffix(x):
    """Return 'am' or 'pm' if only one suffix type is present.
    If BOTH 'am' and 'pm' appear (different suffixes on each side), return None."""
    has_am = "am" in x
    has_pm = "pm" in x
    if has_am and has_pm:
        return None
    if has_am:
        return "am"
    if has_pm:
        return "pm"
    return None
    
# =========================================================
# OPEN HOURS EXTRACTION
# =========================================================
def extract_open_close(open_hours_json):
    result = {}

    if not isinstance(open_hours_json, dict):
        return {f"{d}_openHours": [] for d in DAYS}

    for day in DAYS:
        values = open_hours_json.get(day)

        if not values:
            result[f"{day}_openHours"] = []
            continue

        if not isinstance(values, list):
            values = [values]

        intervals = []

        for raw in values:
            parsed = parse_interval(str(raw))

            if parsed is None:
                continue

            if isinstance(parsed, tuple):
                intervals.append(parsed)
            elif isinstance(parsed, list):
                intervals.extend(parsed)

        result[f"{day}_openHours"] = intervals

    return result


# =========================================================
# OPEN WINDOW CHECK
# =========================================================
def is_open_during_window(open_features, query_intervals):

    def overlap(a1, a2, b1, b2):
        return max(a1, b1) < min(a2, b2)

    for day in DAYS:
        intervals = open_features.get(f"{day}_openHours", [])

        for qs, qe in query_intervals:

            query_parts = normalize_interval(qs, qe)

            for s, e in intervals:

                shop_parts = normalize_interval(s, e)

                for qs2, qe2 in query_parts:
                    for ss, se in shop_parts:
                        if overlap(qs2, qe2, ss, se):
                            return True

    return False


# =========================================================
# POPULAR TIMES EXTRACTION
# =========================================================
def extract_popular_times(pop_json):
    result = {}

    if not isinstance(pop_json, dict):
        return result

    for day in DAYS:
        hours = pop_json.get(day)

        if not isinstance(hours, dict):
            continue

        result[day] = {}

        for hour, value in hours.items():
            try:
                result[day][int(hour)] = value
            except:
                continue

    return result