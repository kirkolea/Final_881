# Pulse · Wearable Health & Fitness Analytics

End-to-end prototype for **CSE 881** that turns PhysioNet wearable-device
streams into VO₂ max, body-fat %, and activity-class predictions, served
through a Flask dashboard.

## Pipeline

```
PhysioNet CSVs  →  ETL (convert_to_db.py)  →  SQLite (wearable_data.db)
               →  EM imputation + feature engineering (preprocessing.py, features.py)
               →  ML training + leaderboard (models.py)
               →  Flask dashboard (app.py + templates/)
```

## Modules

| File | Role |
|------|------|
| `convert_to_db.py` | Bulk-load PhysioNet CSVs into a SQLite database |
| `preprocessing.py` | **EM imputation**, sensor scrubbing, subject-info cleaning |
| `features.py` | Session-level feature extraction + clinical-target estimates |
| `models.py` | Trains & evaluates Linear / Ridge / RandomForest / GradBoost / LogReg |
| `app.py` | Flask app: `/`, `/explore`, `/models`, `/predict`, plus JSON APIs |
| `templates/` | Bootstrap 5 + Chart.js dark-themed dashboard |

## Running it

```bash
# 1. Activate venv and install deps
venv/Scripts/activate
pip install -r requirements.txt

# 2. One-time data prep (skip if wearable_data.db already exists)
python convert_to_db.py
python features.py          # writes features.csv
python models.py            # writes models/*.joblib + models/metrics.json

# 3. Start the dashboard
python app.py               # http://127.0.0.1:5001
```

## Model targets

- **VO₂max** – regression target = Uth-Sorensen estimate
  `15 × HR_max / HR_rest` (mL/kg/min). Used because direct VO₂max
  measurement isn't in the dataset; this is the standard field proxy.
- **Body-fat %** – Deurenberg BMI-based formula
  `1.20 · BMI + 0.23 · age − 10.8 · sex − 5.4`.
- **Activity** – ternary classification of the session protocol
  (`AEROBIC`, `ANAEROBIC`, `STRESS`). `act_*` one-hot columns are
  excluded from this task's feature set to avoid leakage.

## Imputation

`preprocessing.em_impute` runs Expectation-Maximization under a
multivariate-Gaussian assumption: E-step fills missing cells with
conditional means, M-step re-estimates `(μ, Σ)` using the filled data
plus the covariance correction from the imputed blocks. A synthetic
benchmark (MCAR @ 15 %) in `preprocessing.py`'s `__main__` reports MAE
against the ground truth.

## Screens

- `/` Dashboard – cohort summary, dataset scale, top-line model scores
- `/explore` Sensor explorer – pick a (subject, activity, metric), get a live Chart.js line plot + summary stats
- `/models` Leaderboard – full per-task metrics with bar charts
- `/predict` Predict – runs the full pipeline on one session and renders
  VO₂max, body-fat %, activity probabilities, and clinical ratings
