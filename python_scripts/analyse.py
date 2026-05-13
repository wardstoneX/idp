import pandas as pd

INPUT_FILE = "../data/marienplatz.csv"


# =========================================================
# METRIC: OPEN HOURS COMPLEXITY
# =========================================================
def open_hours_complexity(x):

    if pd.isna(x):
        return 0

    s = str(x).lower()

    if s in ["{}", "nan", "none"]:
        return 0

    # count intervals / keywords as complexity proxy
    score = 0

    if "closed" in s:
        return 1

    if "24" in s:
        return 1

    # count time ranges
    score += s.count("–") + s.count("-")

    return score


# =========================================================
# METRIC: POPULAR TIMES COMPLEXITY
# =========================================================
def popular_times_complexity(x):

    if pd.isna(x):
        return 0

    s = str(x).lower()

    if s in ["{}", "nan", "none"]:
        return 0

    try:
        # rough proxy: number of hour entries
        return s.count(":")
    except:
        return 0


# =========================================================
def get_min_max(df, col, metric_fn):

    scores = df[col].apply(metric_fn)

    min_idx = scores.idxmin()
    max_idx = scores.idxmax()

    return min_idx, max_idx, scores


def print_block(df, col, idx, scores, label):

    print("\n====================")
    print(label)
    print("====================")

    print("Title:", df.loc[idx, "title"])
    print("Score:", scores[idx])

    # -------------------------
    # PRINT LINK (auto-detect column)
    # -------------------------
    link_cols = ["link", "url", "place_url", "google_maps_url", "website"]

    link = None
    for c in link_cols:
        if c in df.columns:
            link = df.loc[idx, c]
            break

    print("Link:", link)

    print("\nValue:")
    print(df.loc[idx, col])


# =========================================================
def main():

    df = pd.read_csv(INPUT_FILE, low_memory=False)

    # -------------------------
    # OPEN HOURS
    # -------------------------
    min_i, max_i, open_scores = get_min_max(df, "open_hours", open_hours_complexity)

    print_block(df, "open_hours", min_i, open_scores, "SHORTEST open_hours")
    print_block(df, "open_hours", max_i, open_scores, "LONGEST open_hours")

    # -------------------------
    # POPULAR TIMES
    # -------------------------
    min_i, max_i, pop_scores = get_min_max(df, "popular_times", popular_times_complexity)

    print_block(df, "popular_times", min_i, pop_scores, "SHORTEST popular_times")
    print_block(df, "popular_times", max_i, pop_scores, "LONGEST popular_times")


if __name__ == "__main__":
    main()