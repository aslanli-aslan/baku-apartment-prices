import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from apartmentprices.paths import PROCESSED_DATA


def split_data(df: pd.DataFrame, save_to_file: bool = True):

    df = df.copy()

    price_bin = pd.qcut(df["price"], q=10, labels=False, duplicates="drop")

    train, test = train_test_split(
        df, test_size=0.2, stratify=price_bin, random_state=42
    )

    if save_to_file:
        train.to_parquet(PROCESSED_DATA / "01_train.parquet", index=False)
        test.to_parquet(PROCESSED_DATA / "01_test.parquet", index=False)

    return train, test


# cleaning functions


def filter_physical_anomalies(df):
    mask = (df["floor"] <= df["floors"]) & (df["area"].between(10, 700))
    return df[mask].copy()


def filter_price_anomalies(df):
    unit_price = df["price"] / df["area"]
    mask = (df["price"] >= 25000) & (unit_price.between(400, 15000))
    return df[mask].copy()


def filter_duplicates(df):
    ignore = ["id", "updatedAt"]
    cols = df.columns.difference(ignore)

    df = df.drop_duplicates(subset=cols)
    return df


def fix_dtypes(df):
    df = df.copy()
    for col in ["hasMortgage", "hasBillOfSale", "hasRepair"]:
        if col in df.columns:
            df[col] = df[col].fillna(False).astype(bool)
    if "location" in df.columns:
        df["location"] = df["location"].astype("category")
    return df


def clean_data(df):
    df = filter_physical_anomalies(df)
    df = filter_price_anomalies(df)
    df = filter_duplicates(df)
    df = fix_dtypes(df)
    return df


# engineering functions


def calculate_floor_fields(df):
    df = df.copy()

    df["floor_ratio"] = df["floor"] / df["floors"]
    df["is_first_floor"] = (df["floor"] == 1).astype(bool)
    df["is_last_floor"] = (df["floor"] == df["floors"]).astype(bool)

    return df


def calculate_physical_features(df):
    df = df.copy()

    df["area_to_room_ratio"] = df["area"] / df["rooms"]

    return df


def calculate_metro_features(df):
    METRO_COORDINATES = np.array(
        [
            (40.36621, 49.83162),
            (40.37302, 49.84403),
            (40.38261, 49.84680),
            (40.40067, 49.85152),
            (40.40301, 49.87067),
            (40.41447, 49.87886),
            (40.41505, 49.89152),
            (40.42090, 49.91813),
            (40.41777, 49.93416),
            (40.41039, 49.94329),
            (40.39792, 49.95251),
            (40.38553, 49.95395),
            (40.37288, 49.95345),
            (40.37973, 49.84918),
            (40.38309, 49.87195),
            (40.37990, 49.82981),
            (40.37536, 49.81507),
            (40.39067, 49.80262),
            (40.40443, 49.80775),
            (40.41059, 49.81362),
            (40.42143, 49.79503),
            (40.42443, 49.82514),
            (40.42470, 49.78190),
            (40.40187, 49.82089),
            (40.42587, 49.84171),
            (40.42533, 49.86191),
        ]
    )

    R = 6371

    lat = np.radians(df["lat"].to_numpy())
    lng = np.radians(df["lng"].to_numpy())

    metro_lat = np.radians(METRO_COORDINATES[:, 0])
    metro_lng = np.radians(METRO_COORDINATES[:, 1])

    dlat = metro_lat[None, :] - lat[:, None]
    dlng = metro_lng[None, :] - lng[:, None]

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat[:, None]) * np.cos(metro_lat[None, :]) * np.sin(dlng / 2) ** 2
    )

    distances = 2 * R * np.arcsin(np.sqrt(a))

    result = df.copy()
    result["nearest_metro_distance_km"] = distances.min(axis=1)
    result["nearest_metro_id"] = pd.Series(
        distances.argmin(axis=1), index=df.index, dtype="category"
    )

    return result


def calculate_distance_to_center(df):
    R = 6371

    center_lat = np.radians(40.3667)
    center_lng = np.radians(49.8333)

    lat = np.radians(df["lat"].to_numpy())
    lng = np.radians(df["lng"].to_numpy())

    dlat = center_lat - lat
    dlng = center_lng - lng

    a = np.sin(dlat / 2) ** 2 + np.cos(lat) * np.cos(center_lat) * np.sin(dlng / 2) ** 2
    distance = 2 * R * np.arcsin(np.sqrt(a))

    result = df.copy()
    result["distance_to_center_km"] = distance

    return result


def drop_useless_columns(df):

    df = df.drop(columns=["id", "updatedAt", "hasMortgage"])

    return df


def engineering_pipeline(df):
    df = calculate_floor_fields(df)
    df = calculate_physical_features(df)
    df = calculate_metro_features(df)
    df = calculate_distance_to_center(df)
    df = drop_useless_columns(df)

    return df
