from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)

from apartmentprices.paths import LOG_PATH

EXPERIMENT_PATH = LOG_PATH / "experiments.csv"


def evaluate_predictions(y_true_azn, y_pred_azn, model_name="Model"):
    mae = mean_absolute_error(y_true_azn, y_pred_azn)
    mape = mean_absolute_percentage_error(y_true_azn, y_pred_azn) * 100
    r2 = r2_score(y_true_azn, y_pred_azn)
    rmsle = np.sqrt(
        mean_squared_error(np.log1p(y_true_azn), np.log1p(np.clip(y_pred_azn, 1, None)))
    )

    print(f"=== {model_name} ===")
    print(f"MAE:   {mae:,.0f} AZN")
    print(f"MAPE:  {mape:.2f}%")
    print(f"RMSLE: {rmsle:.4f}")
    print(f"R²:    {r2:.4f}\n")

    return {"Model": model_name, "MAE": mae, "MAPE": mape, "RMSLE": rmsle, "R2": r2}


def log_experiment(
    model_name: str,
    dataset_version: str,
    features_used: list,
    metrics: dict,
    notes: str = "",
):

    EXPERIMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "model": model_name,
        "data": dataset_version,
        "n_features": len(features_used),
        "mae": round(metrics["MAE"], 0),
        "mape": round(metrics["MAPE"], 2),
        "rmsle": round(metrics["RMSLE"], 4),
        "r2": round(metrics["R2"], 4),
        "notes": notes,
    }
    df_new = pd.DataFrame([record])
    if EXPERIMENT_PATH.exists():
        df_log = pd.read_csv(EXPERIMENT_PATH)
        df_log = pd.concat([df_log, df_new], ignore_index=True)
    else:
        df_log = df_new
    df_log.to_csv(EXPERIMENT_PATH, index=False)
    print(f"Logged to {EXPERIMENT_PATH}")
    return df_log
