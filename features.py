from __future__ import annotations

import os
import sqlite3
from typing import Dict

import numpy as np
import pandas as pd

from preprocessing import clean_subjects, preprocess_table

DB_NAME = "wearable_data.db"



def load_subjects(db: str = DB_NAME):
    conn = sqlite3.connect(db)
    df = pd.read_sql("SELECT * FROM subjects", conn)
    conn.close()
    return clean_subjects(df)


def load_stream(table: str, subject: str, activity: str,
                db: str = DB_NAME):
    conn = sqlite3.connect(db)
    q = f"SELECT * FROM {table} WHERE subject_id = ? AND activity = ?"
    df = pd.read_sql(q, conn, params=(subject, activity))
    conn.close()
    return df


def stats(series: pd.Series, prefix: str):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {f"{prefix}_{k}": np.nan
                for k in ("mean", "std", "min", "max", "p25", "p75", "range", "slope")}
    arr = s.to_numpy()
    out = {
        f"{prefix}_mean": float(np.mean(arr)),
        f"{prefix}_std":  float(np.std(arr)),
        f"{prefix}_min":  float(np.min(arr)),
        f"{prefix}_max":  float(np.max(arr)),
        f"{prefix}_p25":  float(np.percentile(arr, 25)),
        f"{prefix}_p75":  float(np.percentile(arr, 75)),
        f"{prefix}_range": float(np.max(arr) - np.min(arr)),
    }
    if len(arr) > 1:
        x = np.arange(len(arr))
        slope = float(np.polyfit(x, arr, 1)[0])
    else:
        slope = 0.0
    out[f"{prefix}_slope"] = slope
    return out


def session_features(subject: str, activity: str,
                     db: str = DB_NAME):
    feats = {"subject_id": subject, "activity": activity}

    hr = load_stream("hr", subject, activity, db)
    if not hr.empty:
        feats.update(stats(hr["bpm"], "hr"))
        feats["hr_reserve_used"] = float((hr["bpm"].max() - hr["bpm"].min())
                                         / max(1.0, hr["bpm"].min()))

    temp = load_stream("temp", subject, activity, db)
    if not temp.empty:
        feats.update(stats(temp["celsius"], "temp"))

    eda = load_stream("eda", subject, activity, db)
    if not eda.empty:
        feats.update(stats(eda["value"], "eda"))

    acc = load_stream("acc", subject, activity, db)
    if not acc.empty:
        mag = np.sqrt(acc["x"].astype(float) ** 2
                      + acc["y"].astype(float) ** 2
                      + acc["z"].astype(float) ** 2)
        feats.update(stats(pd.Series(mag), "acc_mag"))

    ibi = load_stream("ibi", subject, activity, db)
    if not ibi.empty and "interval" in ibi.columns:
        iv = pd.to_numeric(ibi["interval"], errors="coerce").dropna().to_numpy()
        if len(iv) > 1:
            feats["hrv_sdnn"] = float(np.std(iv) * 1000)
            feats["hrv_rmssd"] = float(np.sqrt(np.mean(np.diff(iv) ** 2)) * 1000)
            feats["hrv_mean_ibi"] = float(np.mean(iv) * 1000)

    return feats


def estimate_targets(row: pd.Series):
    targets: Dict[str, float] = {}

    age = row.get("age")
    gender = str(row.get("gender", "")).lower()
    h = row.get("height_cm")
    w = row.get("weight_kg")

    if pd.notna(age) and pd.notna(h) and pd.notna(w) and h > 0:
        bmi = w / ((h / 100) ** 2)
        sex = 1.0 if gender.startswith("m") else 0.0
        targets["bmi"] = float(bmi)
        targets["body_fat_pct"] = float(1.20 * bmi + 0.23 * age - 10.8 * sex - 5.4)

    hr_rest = row.get("hr_min")
    hr_max = row.get("hr_max")
    if pd.notna(hr_rest) and pd.notna(hr_max) and hr_rest > 0:
        targets["vo2max"] = float(15.0 * (hr_max / hr_rest))
    elif pd.notna(age):
        predicted_max = 208 - 0.7 * age
        if pd.notna(hr_rest) and hr_rest > 0:
            targets["vo2max"] = float(15.0 * (predicted_max / hr_rest))

    return targets


def featureTables(db: str = DB_NAME, activities=("AEROBIC", "ANAEROBIC", "STRESS"),impute: str = "em"):
    subjects = load_subjects(db)

    rows = []
    for i , subj in subjects.iterrows():
        sid = subj["subject_id"]
        for act in activities:
            feats = session_features(sid, act, db)
            if len(feats) <= 2:
                continue
            for k in ("age", "height_cm", "weight_kg", "gender", "active"):
                feats[k] = subj.get(k)
            rows.append(feats)

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    target_rows = df.apply(estimate_targets, axis=1, result_type="expand")
    df = pd.concat([df, target_rows], axis=1)

    feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in ("vo2max", "body_fat_pct", "bmi")]
    if feature_cols:
        imputed = preprocess_table(df[feature_cols], method=impute, normalize=False)
        df[feature_cols] = imputed

    df["gender_m"] = (df["gender"].astype(str).str.lower().str.startswith("m")).astype(int)
    df["active_bin"] = (df["active"].astype(str).str.lower() == "yes").astype(int)
    act_dummies = pd.get_dummies(df["activity"], prefix="act").astype(int)
    df = pd.concat([df, act_dummies], axis=1)

    return df


if __name__ == "__main__":
    featureTables().to_csv("features.csv", index=False)
