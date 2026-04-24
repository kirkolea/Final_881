
from __future__ import annotations

import warnings
import numpy as np
import pandas as pd
from scipy.stats import zscore


def clean_subjects(df: pd.DataFrame):
    
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    rename = {
        "Info": "subject_id",
        "Gender": "gender",
        "Age": "age",
        "Height (cm)": "height_cm",
        "Weight (kg)": "weight_kg",
        "Does physical activity regularly?": "active",
        "Protocol": "protocol",
        "Stress Inducement": "stress",
        "Aerobic Exercise": "aerobic",
        "Anaerobic Exercise": "anaerobic",
    }
    df = df.rename(columns=rename)

    # Drop reference/footnote rows (they have no subject id or contain "References")
    df = df[df["subject_id"].notna()]
    df = df[~df["subject_id"].astype(str).str.contains("References|:", regex=True, na=False)]

    # Coerce numerics, empty / dash cells -> NaN
    for col in ("age", "height_cm", "weight_kg"):
        df[col] = pd.to_numeric(df[col].replace({"-": np.nan, "": np.nan}), errors="coerce")

    # Strip footnote stars from Yes/No cells
    for col in ("active", "stress", "aerobic", "anaerobic"):
        if col in df.columns:
            df[col] = (df[col].astype(str)
                              .str.replace(r"\*+", "", regex=True)
                              .str.strip()
                              .replace({"-": np.nan, "": np.nan}))

    df["gender"] = df["gender"].astype(str).str.strip().str.lower().replace({"nan": np.nan})
    df = df.reset_index(drop=True)
    return df

def em_impute(df: pd.DataFrame, max_iter: int = 50, tol: float = 1e-4,verbose: bool = False):
  
    numeric = df.select_dtypes(include=[np.number]).copy()
    other = df.drop(columns=numeric.columns)

    if numeric.empty:
        return df.copy()

    X = numeric.to_numpy(dtype=float)
    missing = np.isnan(X)

    col_means = np.nanmean(X, axis=0)
    col_means = np.where(np.isnan(col_means), 0.0, col_means)
    X_filled = np.where(missing, col_means, X)

    mu = X_filled.mean(axis=0)
    sigma = np.cov(X_filled, rowvar=False)
    if sigma.ndim == 0:
        sigma = np.array([[float(sigma)]])

    for it in range(max_iter):
        mu_old, sigma_old = mu.copy(), sigma.copy()
        cov_correction = np.zeros_like(sigma)

        for i in range(X.shape[0]):
            miss = missing[i]
            if not miss.any():
                continue
            obs = ~miss
            s_oo = sigma[np.ix_(obs, obs)]
            s_mo = sigma[np.ix_(miss, obs)]
            s_mm = sigma[np.ix_(miss, miss)]

            try:
                s_oo_inv = np.linalg.pinv(s_oo)
            except np.linalg.LinAlgError:
                s_oo_inv = np.linalg.pinv(s_oo + 1e-6 * np.eye(s_oo.shape[0]))

            diff = X_filled[i, obs] - mu[obs]
            X_filled[i, miss] = mu[miss] + s_mo @ s_oo_inv @ diff

            block = s_mm - s_mo @ s_oo_inv @ s_mo.T
            idx = np.where(miss)[0]
            cov_correction[np.ix_(idx, idx)] += block

        mu = X_filled.mean(axis=0)
        n = X_filled.shape[0]
        centered = X_filled - mu
        sigma = (centered.T @ centered + cov_correction) / n
        sigma += 1e-8 * np.eye(sigma.shape[0])

        delta = np.linalg.norm(mu - mu_old) + np.linalg.norm(sigma - sigma_old)
        if verbose:
            print(f"  EM iter {it+1}: delta={delta:.6f}")
        if delta < tol:
            break

    filled = pd.DataFrame(X_filled, columns=numeric.columns, index=numeric.index)
    return pd.concat([filled, other], axis=1)[df.columns]

def iterative_impute(df: pd.DataFrame, max_iter: int = 20):
  
    from sklearn.experimental import enable_iterative_imputer 
    from sklearn.impute import IterativeImputer

    numeric = df.select_dtypes(include=[np.number]).copy()
    other = df.drop(columns=numeric.columns)
    if numeric.empty:
        return df.copy()
    imp = IterativeImputer(max_iter=max_iter, random_state=0)
    X = imp.fit_transform(numeric)
    filled = pd.DataFrame(X, columns=numeric.columns, index=numeric.index)
    return pd.concat([filled, other], axis=1)[df.columns]

def preprocess_table(df: pd.DataFrame, method: str = "em",normalize: bool = True):
    
    out = df.copy()

    non_num = out.select_dtypes(exclude=[np.number]).columns
    for col in non_num:
        if out[col].isna().any():
            mode = out[col].mode(dropna=True)
            if len(mode):
                out[col] = out[col].fillna(mode.iloc[0])

    if method == "em":
        out = em_impute(out)
    elif method == "iterative":
        out = iterative_impute(out)
    elif method in ("mean", "mode"):
        for col in out.select_dtypes(include=[np.number]).columns:
            out[col] = out[col].fillna(out[col].mean())
    else:
        raise ValueError(f"unknown imputation method: {method}")

    if normalize:
        num_cols = out.select_dtypes(include=[np.number]).columns
        for col in num_cols:
            lo, hi = out[col].min(), out[col].max()
            if hi - lo > 1e-12:
                out[col] = (out[col] - lo) / (hi - lo)

    return out


def scrub_sensor_stream(series: pd.Series, z_thresh: float = 5.0,
                        rolling: int = 5) -> pd.Series:
 
    s = pd.to_numeric(series, errors="coerce")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        z = zscore(s.fillna(s.median()), nan_policy="omit")
    s = s.where(np.abs(z) < z_thresh)
    s = s.ffill().bfill()
    if rolling > 1:
        s = s.rolling(rolling, min_periods=1, center=True).median()
    return s


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    X = rng.multivariate_normal([1, 2, 3], [[1, .3, .2], [.3, 1, .1], [.2, .1, 1]], size=500)
    mask = rng.random(X.shape) < 0.15
    Xm = X.copy()
    Xm[mask] = np.nan
    df = pd.DataFrame(Xm, columns=["a", "b", "c"])
    filled = em_impute(df, verbose=True)
    mae = np.abs(filled.to_numpy() - X)[mask].mean()
    print(f"EM imputation MAE on held-out cells: {mae:.4f}")
