
from __future__ import annotations

import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (accuracy_score, f1_score, mean_absolute_error,
                             r2_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

warnings.filterwarnings("ignore")

DROP = {
    "subject_id", "activity", "gender", "active",
    "vo2max", "body_fat_pct", "bmi",
}

def regress(df: pd.DataFrame, target: str, primary: str = "r2"):
    data = df.dropna(subset=[target]).copy()
    X = data[[c for c in df.columns if c not in DROP and pd.api.types.is_numeric_dtype(df[c])]]
    y = data[target].astype(float)

    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)

    models = {
        "Linear":       Pipeline([("sc", StandardScaler()), ("m", LinearRegression())]),
        "Ridge":        Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))]),
        "RandomForest": RandomForestRegressor(n_estimators=200, random_state=42),
    }

    leaderboard = []
    fitted = {}
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
        leaderboard.append({
            "model": name,
            "r2":  float(r2_score(y_te, pred)),
            "mae": float(mean_absolute_error(y_te, pred)),
            "rmse": float(np.sqrt(((y_te - pred) ** 2).mean())),
        })
        fitted[name] = model

    if primary == "rmse":
        leaderboard.sort(key=lambda r: r["rmse"])       
    else:
        leaderboard.sort(key=lambda r: r["r2"], reverse=True)

    best_name = leaderboard[0]["model"]
    joblib.dump(fitted[best_name], MODEL_DIR / f"{target}.joblib")

    return {
        "target": target,
        "n_samples": int(len(data)),
        "best_model": best_name,
        "primary_metric": primary,
        "leaderboard": leaderboard,
        "feature_cols": list(X.columns),
    }

def classify(df: pd.DataFrame, target: str = "activity"):
    data = df.dropna(subset=[target]).copy()
    le = LabelEncoder()
    y = le.fit_transform(data[target].astype(str))

    extra_drop = [c for c in data.columns if c.startswith("act_")]
    feats = data.drop(columns=extra_drop, errors="ignore")[[c for c in df.columns if c not in DROP and pd.api.types.is_numeric_dtype(df[c])]]
    X = feats

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    models = {
        "LogReg":Pipeline([("sc", StandardScaler()),("m", LogisticRegression(max_iter=1000,multi_class="ovr"))]),
        "RandomForest": RandomForestClassifier(n_estimators=300, random_state=42),
    }

    leaderboard = []
    fitted = {}
    for name, model in models.items():
        model.fit(X_tr, y_tr)
        pred = model.predict(X_te)
       
        leaderboard.append({
            "model": name,
            "accuracy": float(accuracy_score(y_te, pred)),
            "f1_macro": float(f1_score(y_te, pred, average="macro")),
        })
        fitted[name] = model

    leaderboard.sort(key=lambda r: r["f1_macro"], reverse=True)
    best_name = leaderboard[0]["model"]
    joblib.dump(fitted[best_name], MODEL_DIR / f"{target}.joblib")
    joblib.dump(le, MODEL_DIR / f"{target}_labels.joblib")

    return {
        "target": target,
        "n_samples": int(len(data)),
        "classes": list(le.classes_),
        "best_model": best_name,
        "leaderboard": leaderboard,
        "feature_cols": list(X.columns),
    }

def train_all(feature_csv: str = "features.csv"):
    df = pd.read_csv(feature_csv)

    report = {
        "vo2max":       regress(df, "vo2max", primary="rmse"),
        "body_fat_pct": regress(df, "body_fat_pct"),
        "activity":     classify(df, "activity"),
    }

    with open(MODEL_DIR / "metrics.json", "w") as fh:
        json.dump(report, fh, indent=2)

    with open(MODEL_DIR / "feature_cols.json", "w") as fh:
        json.dump({k: v["feature_cols"] for k, v in report.items()}, fh, indent=2)

    return report

if __name__ == "__main__":
    rpt = train_all()
