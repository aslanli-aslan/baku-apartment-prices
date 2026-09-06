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
