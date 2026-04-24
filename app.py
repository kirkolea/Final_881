
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

from features import session_features, estimate_targets
from preprocessing import clean_subjects

BASE_DIR = Path(__file__).parent
DB_NAME = BASE_DIR / "wearable_data.db"
MODEL_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "Wearable_Dataset"
FEATURES_CSV = BASE_DIR / "features.csv"
METRICS_JSON = MODEL_DIR / "metrics.json"

app = Flask(__name__)


def cleanSubjects():
    if not DB_NAME.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(DB_NAME)
    data = pd.read_sql("SELECT * FROM subjects", conn)
    conn.close()
    return clean_subjects(data)

@app.route("/")
def dashboard():
    subjects = cleanSubjects()
    metrics = json.loads(METRICS_JSON.read_text())

    demo = {
        "n_subjects": int(subjects["subject_id"].nunique()),
        "n_male": int((subjects["gender"].str.lower() == "m").sum()),
        "n_female": int((subjects["gender"].str.lower() == "f").sum()),
        "age_range": f"{int(subjects['age'].min(skipna=True))}-"
                    f"{int(subjects['age'].max(skipna=True))}",
        "mean_age": round(float(subjects["age"].mean(skipna=True)), 1),
        "mean_weight": round(float(subjects["weight_kg"].mean(skipna=True)), 1),
        "mean_height": round(float(subjects["height_cm"].mean(skipna=True)), 1),
    }

    table_counts = {}
    conn = sqlite3.connect(DB_NAME)
    for t in ("hr", "temp", "eda", "bvp", "acc", "ibi"):
        c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        table_counts[t.upper()] = int(c)
                
    conn.close()

    model_summary = []
    for task, info in metrics.items():
        top = info["leaderboard"][0]
        model_summary.append({
            "task": task,
            "best_model": info["best_model"],
            "score": top.get("rmse") if info.get("primary_metric") == "rmse" else top.get("r2", top.get("f1_macro")),
            "score_name": "RMSE" if info.get("primary_metric") == "rmse" else ("R²" if "r2" in top else "F1"),
            "n": info.get("n_samples", 0),
        })

    return render_template(
        "dashboard.html",
        demo=demo,
        table_counts=table_counts,
        model_summary=model_summary,
    )


@app.route("/explore")
def explore():
    subjects = cleanSubjects()
    subject_ids = sorted(subjects["subject_id"].dropna().tolist())
    return render_template(
        "explore.html",
        subjects=subject_ids,
        activities=["AEROBIC", "ANAEROBIC", "STRESS"],
        metrics=["HR", "TEMP", "EDA", "BVP", "ACC"],
    )


@app.route("/api/chart")
def api_chart():
    subject = request.args.get("subject", "S01")
    activity = request.args.get("activity", "AEROBIC")
    metric = request.args.get("metric", "HR").lower()
    limit = int(request.args.get("limit", 2000))

    if not DB_NAME.exists():
        return jsonify({"error": "database missing"}), 400

    conn = sqlite3.connect(DB_NAME)
    try:
        if metric == "acc":
            q = "SELECT x, y, z FROM acc WHERE subject_id=? AND activity=? LIMIT ?"
            df = pd.read_sql(q, conn, params=(subject, activity, limit))
            if df.empty:
                return jsonify({"labels": [], "datasets": []})
            mag = np.sqrt(df["x"] ** 2 + df["y"] ** 2 + df["z"] ** 2)
            return jsonify({
                "labels": list(range(len(df))),
                "datasets": [{"label": "ACC magnitude", "data": mag.round(3).tolist()}],
            })
        else:
            col = {"hr": "bpm", "temp": "celsius", "eda": "value", "bvp": "value"}[metric]
            q = f"SELECT {col} FROM {metric} WHERE subject_id=? AND activity=? LIMIT ?"
            df = pd.read_sql(q, conn, params=(subject, activity, limit))
            if df.empty:
                return jsonify({"labels": [], "datasets": []})
            return jsonify({
                "labels": list(range(len(df))),
                "datasets": [{
                    "label": f"{metric.upper()} ({col})",
                    "data": df[col].round(3).tolist(),
                }],
            })
    finally:
        conn.close()


@app.route("/api/subject_profile")
def api_subject_profile():
    sid = request.args.get("subject", "S01")
    subjects = cleanSubjects()
    row = subjects[subjects["subject_id"] == sid]
    if row.empty:
        return jsonify({})
    return jsonify(row.iloc[0].fillna("").to_dict())


@app.route("/models")
def models_view():
    metrics = json.loads(METRICS_JSON.read_text())
    return render_template("models.html", metrics=metrics)


@app.route("/predict")
def predict_view():
    subjects = cleanSubjects()
    sids = sorted(subjects["subject_id"].dropna().tolist())
    return render_template("predict.html", subjects=sids, activities=["AEROBIC", "ANAEROBIC", "STRESS"])


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(force=True, silent=True) or {}
    subject = data.get("subject", "S01")
    activity = data.get("activity", "AEROBIC")

    feats = session_features(subject, activity, str(DB_NAME))
    subjects = cleanSubjects()
    row = subjects[subjects["subject_id"] == subject]
    if not row.empty:
        r = row.iloc[0]
        for k in ("age", "height_cm", "weight_kg", "gender", "active"):
            feats[k] = r.get(k)

    feats_series = pd.Series(feats)
    targets = estimate_targets(feats_series)

    df = pd.DataFrame([feats])
    df["gender_m"] = (df["gender"].astype(str).str.lower().str.startswith("m")).astype(int)
    df["active_bin"] = (df["active"].astype(str).str.lower() == "yes").astype(int)
    for a in ["AEROBIC", "ANAEROBIC", "STRESS"]:
        df[f"act_{a}"] = int(activity == a)

    feature_cols = json.loads((MODEL_DIR / "feature_cols.json").read_text())

    def _predict(model_name):
        mdl = joblib.load(MODEL_DIR / f"{model_name}.joblib")
        if mdl is None:
            return None
        cols = feature_cols.get(model_name, [])
        X = df.reindex(columns=cols, fill_value=0).fillna(0)
        try:
            return float(mdl.predict(X)[0])
        except Exception as exc:
            return {"error": str(exc)}

    vo2 = _predict("vo2max")
    bf = _predict("body_fat_pct")

    act_mdl = joblib.load(MODEL_DIR / f"activity.joblib")
    act_pred = None
    act_probs = {}
    if act_mdl is not None:
        cols = feature_cols.get("activity", [])
        X = df.reindex(columns=cols, fill_value=0).fillna(0)
        try:
            le = joblib.load(MODEL_DIR / "activity_labels.joblib")
            proba = act_mdl.predict_proba(X)[0]
            labels = le.classes_
            act_probs = {str(l): float(p) for l, p in zip(labels, proba)}
            act_pred = str(labels[int(np.argmax(proba))])
        except Exception as exc:
            act_pred = None
            act_probs = {"error": str(exc)}

    def _rating_vo2(value, age, gender):
        if value is None or pd.isna(age):
            return "—"
        tbl = VO2_NORMS_M if str(gender).lower().startswith("m") else VO2_NORMS_F
        band = next((row for row in tbl if row["min_age"] <= age <= row["max_age"]), None)
        if band is None:
            return "—"
        for level, lo in band["levels"]:
            if value >= lo:
                return level
        return "Very Poor"

    def _rating_bf(value, gender):
        if value is None:
            return "—"
        table = BF_NORMS_M if str(gender).lower().startswith("m") else BF_NORMS_F
        for level, lo, hi in table:
            if lo <= value < hi:
                return level
        return "—"

    age = feats.get("age")
    gender = feats.get("gender", "")

    return jsonify({
        "subject": subject,
        "activity": activity,
        "predictions": {
            "vo2max": vo2,
            "body_fat_pct": bf,
            "activity": act_pred,
            "activity_probs": act_probs,
        },
        "clinical_estimates": targets,
        "ratings": {
            "vo2max":       _rating_vo2(vo2, age, gender),
            "body_fat_pct": _rating_bf(bf, gender),
        },
        "inputs": {
            "age": feats.get("age"),
            "gender": feats.get("gender"),
            "height_cm": feats.get("height_cm"),
            "weight_kg": feats.get("weight_kg"),
            "hr_mean": feats.get("hr_mean"),
            "hr_max":  feats.get("hr_max"),
            "hr_min":  feats.get("hr_min"),
        },
    })


VO2_NORMS_M = [
    {"min_age": 0,  "max_age": 29, "levels": [("Elite", 55), ("Excellent", 51),
                                              ("Good", 45), ("Fair", 38),
                                              ("Poor", 32)]},
    {"min_age": 30, "max_age": 39, "levels": [("Elite", 52), ("Excellent", 47),
                                              ("Good", 41), ("Fair", 35),
                                              ("Poor", 30)]},
    {"min_age": 40, "max_age": 49, "levels": [("Elite", 48), ("Excellent", 43),
                                              ("Good", 37), ("Fair", 32),
                                              ("Poor", 27)]},
    {"min_age": 50, "max_age": 200, "levels": [("Elite", 44), ("Excellent", 39),
                                               ("Good", 33), ("Fair", 28),
                                               ("Poor", 24)]},
]
VO2_NORMS_F = [
    {"min_age": 0,  "max_age": 29, "levels": [("Elite", 49), ("Excellent", 44),
                                              ("Good", 38), ("Fair", 32),
                                              ("Poor", 28)]},
    {"min_age": 30, "max_age": 39, "levels": [("Elite", 45), ("Excellent", 40),
                                              ("Good", 34), ("Fair", 29),
                                              ("Poor", 25)]},
    {"min_age": 40, "max_age": 49, "levels": [("Elite", 42), ("Excellent", 36),
                                              ("Good", 30), ("Fair", 26),
                                              ("Poor", 22)]},
    {"min_age": 50, "max_age": 200, "levels": [("Elite", 38), ("Excellent", 32),
                                               ("Good", 27), ("Fair", 23),
                                               ("Poor", 20)]},
]
BF_NORMS_M = [
    ("Essential", 2, 6),
    ("Athlete",   6, 14),
    ("Fit",       14, 18),
    ("Average",   18, 25),
    ("High",      25, 100),
]
BF_NORMS_F = [
    ("Essential", 10, 14),
    ("Athlete",   14, 21),
    ("Fit",       21, 25),
    ("Average",   25, 32),
    ("High",      32, 100),
]


@app.route("/api/norms")
def api_norms():
    return jsonify({
        "vo2_male": VO2_NORMS_M,
        "vo2_female": VO2_NORMS_F,
        "bf_male": BF_NORMS_M,
        "bf_female": BF_NORMS_F,
    })


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port)
