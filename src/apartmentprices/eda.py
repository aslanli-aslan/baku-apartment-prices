import pandas as pd


def check_near_duplicates(df: pd.DataFrame, diff_cols: list) -> pd.DataFrame:

    df = df.copy()

    # must haves
    KEYS = ["id", "updatedAt"]
    diff_cols.extend(KEYS)

    matching_cols = df.columns.difference(diff_cols)
    base_cols = df.columns.difference(KEYS)

    duplicates = df.duplicated(matching_cols, keep=False)
    base_duplicates = df.duplicated(base_cols, keep=False)

    # to investigate rows that have different "diff_cols"
    diff_duplicates = duplicates & ~base_duplicates

    return df[diff_duplicates].sort_values(list(matching_cols))


def check_location_of_coordinates(df, lat, lng):
    df = df.copy()

    filtered = df[(df["lat"] == lat) & (df["lng"] == lng)]

    return filtered["location"].value_counts()