"""
Analyze sentiment <-> market dynamics and build the 2x3 results matrix.

Stages:
  1. Load daily_sentiment.csv + BTC (4h) + GLD (daily). Merge on date.
  2. Compute returns, rolling volatility, spike/surge labels.
  3. Engineer lag features for the all/financial/political sentiment streams.
  4. Correlation heatmap + Granger causality tests.
  5. Train LogReg / RF / XGBoost per {asset x feature-set} with walk-forward CV.
  6. Feature importance (XGBoost).
  7. Plots + results_matrix.csv.

Run:
    pip install xgboost statsmodels matplotlib seaborn
    python analyze_and_model.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

PROJECT_DIR = Path(__file__).parent
ARTIFACTS = PROJECT_DIR / "artifacts"
PLOTS = ARTIFACTS / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

SENT_CSV = ARTIFACTS / "daily_sentiment.csv"
BTC_CSV = PROJECT_DIR / "bitcoin_prices_2024_4h.csv"
GLD_CSV = PROJECT_DIR / "GLD_ETF_Stock_Price_History_Converted.csv"

# --- modeling config ----------------------------------------------------------
SPIKE_SIGMA = 2.0          # volatility spike: |return| > SIGMA * rolling std
ROLL_WINDOW = 30           # rolling stats window (days)
LAGS = [1, 3, 7]           # rolling-mean windows for lag features
WALK_FOLDS = 5             # TimeSeriesSplit folds
RANDOM_STATE = 42


# =============================================================================
# Stage 1 — Load & merge
# =============================================================================
def load_sentiment() -> pd.DataFrame:
    s = pd.read_csv(SENT_CSV, parse_dates=["date"])
    s = s.rename(columns={"date": "date"}).set_index("date").sort_index()
    s.index = s.index.normalize()
    print(f"[sent] {s.shape[0]} days x {s.shape[1]} features")
    return s


def load_btc_daily() -> pd.DataFrame:
    df = pd.read_csv(BTC_CSV, parse_dates=["timestamp"])
    df = df.set_index("timestamp").sort_index()
    daily = pd.DataFrame({
        "btc_open":   df["Open"].resample("D").first(),
        "btc_high":   df["High"].resample("D").max(),
        "btc_low":    df["Low"].resample("D").min(),
        "btc_close":  df["Close"].resample("D").last(),
        "btc_volume": df["Volume"].resample("D").sum(),
    }).dropna(how="all")
    daily.index = daily.index.tz_localize(None).normalize()
    print(f"[btc]  {daily.shape[0]} daily rows")
    return daily


def load_gld_daily() -> pd.DataFrame:
    df = pd.read_csv(GLD_CSV)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Vol."] = df["Vol."].astype(str).str.replace(",", "").astype(float)
    df = df.rename(columns={
        "Date": "date", "Price": "gld_close", "Open": "gld_open",
        "High": "gld_high", "Low": "gld_low", "Vol.": "gld_volume",
    })
    df = df.set_index("date").sort_index()[
        ["gld_open", "gld_high", "gld_low", "gld_close", "gld_volume"]
    ]
    df.index = df.index.normalize()
    print(f"[gld]  {df.shape[0]} daily rows")
    return df


# =============================================================================
# Stage 2 — Target labels
# =============================================================================
def add_targets(df: pd.DataFrame, close_col: str, vol_col: str, prefix: str):
    ret = df[close_col].pct_change()
    abs_ret = ret.abs()
    roll_std = abs_ret.rolling(ROLL_WINDOW, min_periods=10).std()
    roll_mean_vol = df[vol_col].rolling(ROLL_WINDOW, min_periods=10).mean()
    roll_std_vol = df[vol_col].rolling(ROLL_WINDOW, min_periods=10).std()

    df[f"{prefix}_return"] = ret
    df[f"{prefix}_abs_return"] = abs_ret
    df[f"{prefix}_spike"] = (abs_ret > SPIKE_SIGMA * roll_std).astype(int)
    df[f"{prefix}_surge"] = (df[vol_col] > roll_mean_vol + SPIKE_SIGMA * roll_std_vol).astype(int)
    return df


# =============================================================================
# Stage 3 — Lag features
# =============================================================================
SENT_STREAMS = ["all", "fin", "pol"]
SENT_CORE = ["sent_mean", "sent_var", "headline_count", "pos_share", "neg_share"]


def engineer_lags(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag1, rolling means over LAGS, and momentum for every sentiment col."""
    out = df.copy()
    for stream in SENT_STREAMS:
        for feat in SENT_CORE:
            col = f"{stream}_{feat}"
            if col not in out.columns:
                continue
            out[f"{col}_lag1"] = out[col].shift(1)
            for L in LAGS:
                out[f"{col}_rm{L}"] = out[col].shift(1).rolling(L, min_periods=1).mean()
            out[f"{col}_mom"] = out[col].shift(1) - out[col].shift(2)
    return out


def feature_cols_for(stream_keys: list[str]) -> list[str]:
    """Return lag feature names whose stream prefix is in stream_keys."""
    suffixes = ["_lag1", "_mom"] + [f"_rm{L}" for L in LAGS]
    cols = []
    for s in stream_keys:
        for feat in SENT_CORE:
            for suf in suffixes:
                cols.append(f"{s}_{feat}{suf}")
    return cols


# =============================================================================
# Stage 4 — Stats: correlation + Granger
# =============================================================================
def plot_correlation(df: pd.DataFrame, path: Path):
    import matplotlib.pyplot as plt
    import seaborn as sns

    targets = ["btc_return", "btc_abs_return", "btc_spike",
               "gld_return", "gld_abs_return", "gld_spike"]
    sent_lag_cols = [c for c in df.columns if c.endswith("_lag1")
                     and any(c.startswith(s + "_") for s in SENT_STREAMS)]
    sub = df[sent_lag_cols + targets].dropna()
    corr = sub.corr(method="spearman").loc[sent_lag_cols, targets]

    plt.figure(figsize=(10, max(6, 0.25 * len(sent_lag_cols))))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                cbar_kws={"label": "Spearman ρ"}, annot_kws={"size": 7})
    plt.title("Lagged sentiment vs next-day market outcomes")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()
    print(f"[plot] {path.name}")


def granger_table(df: pd.DataFrame, path: Path):
    from statsmodels.tsa.stattools import grangercausalitytests

    rows = []
    targets = {"BTC_abs_return": "btc_abs_return", "GLD_abs_return": "gld_abs_return"}
    sent_streams = {"all": "all_sent_mean", "fin": "fin_sent_mean", "pol": "pol_sent_mean"}

    for tgt_name, tgt_col in targets.items():
        for sname, scol in sent_streams.items():
            pair = df[[tgt_col, scol]].dropna()
            if len(pair) < 40:
                continue
            try:
                res = grangercausalitytests(pair, maxlag=5, verbose=False)
                for lag in range(1, 6):
                    p = res[lag][0]["ssr_ftest"][1]
                    rows.append({"target": tgt_name, "sentiment": sname,
                                 "lag": lag, "p_value": p,
                                 "significant_5pct": p < 0.05})
            except Exception as e:
                print(f"[granger] skip {tgt_name}<-{sname}: {e}")

    out = pd.DataFrame(rows)
    out.to_csv(path, index=False)
    print(f"[granger] wrote {path.name} ({len(out)} rows)")
    return out


# =============================================================================
# Stage 5 — The 2x3 matrix: models with walk-forward CV
# =============================================================================
def walk_forward_scores(X: np.ndarray, y: np.ndarray, model_factory):
    from sklearn.metrics import f1_score, roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit

    # Guard against tiny classes making TimeSeriesSplit eat all positives
    tscv = TimeSeriesSplit(n_splits=WALK_FOLDS)
    f1s, aucs = [], []
    for train_idx, test_idx in tscv.split(X):
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        if len(np.unique(ytr)) < 2 or len(np.unique(yte)) < 2:
            continue  # fold is degenerate (no positives); skip
        model = model_factory()
        model.fit(Xtr, ytr)
        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(Xte)[:, 1]
            pred = (proba >= 0.5).astype(int)
            try:
                aucs.append(roc_auc_score(yte, proba))
            except ValueError:
                pass
        else:
            pred = model.predict(Xte)
        f1s.append(f1_score(yte, pred, zero_division=0))
    return (np.mean(f1s) if f1s else np.nan,
            np.mean(aucs) if aucs else np.nan)


def make_models():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except ImportError:
        has_xgb = False

    models = {
        "LogReg": lambda: Pipeline([
            ("sc", StandardScaler()),
            ("lr", LogisticRegression(max_iter=1000, class_weight="balanced",
                                      random_state=RANDOM_STATE)),
        ]),
        "RandomForest": lambda: RandomForestClassifier(
            n_estimators=300, max_depth=6, class_weight="balanced",
            random_state=RANDOM_STATE, n_jobs=-1),
    }
    if has_xgb:
        models["XGBoost"] = lambda: XGBClassifier(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.9, colsample_bytree=0.9,
            eval_metric="logloss", random_state=RANDOM_STATE,
            n_jobs=-1, verbosity=0)
    return models


FEATURE_SETS = {
    "Financial only":  ["fin"],
    "Political only":  ["pol"],
    "Combined":        ["fin", "pol", "all"],
}


def build_results_matrix(df: pd.DataFrame) -> pd.DataFrame:
    models = make_models()
    rows = []

    for asset, spike_col in [("BTC", "btc_spike"), ("GLD", "gld_spike")]:
        work = df.dropna(subset=[spike_col]).copy()
        # For GLD, inner-join on trading days (the column already has gaps filled with NaN)
        for fs_name, streams in FEATURE_SETS.items():
            cols = feature_cols_for(streams)
            cols = [c for c in cols if c in work.columns]
            data = work[cols + [spike_col]].dropna()
            X = data[cols].values
            y = data[spike_col].values.astype(int)
            pos_rate = y.mean() if len(y) else 0.0
            for mname, mfac in models.items():
                f1, auc = walk_forward_scores(X, y, mfac)
                rows.append({
                    "asset": asset,
                    "feature_set": fs_name,
                    "model": mname,
                    "n_samples": len(y),
                    "pos_rate": round(pos_rate, 3),
                    "f1": round(f1, 3) if not np.isnan(f1) else np.nan,
                    "auc": round(auc, 3) if not np.isnan(auc) else np.nan,
                })
                print(f"[model] {asset:3s} | {fs_name:15s} | {mname:12s} "
                      f"f1={f1:.3f} auc={auc:.3f} (n={len(y)}, pos={pos_rate:.2%})")

    return pd.DataFrame(rows)


def pretty_matrix(results: pd.DataFrame, metric: str) -> pd.DataFrame:
    """Return the 2x3 matrix for a given metric, using best model per cell."""
    best = (results.sort_values(metric, ascending=False)
                   .groupby(["asset", "feature_set"], as_index=False)
                   .first())
    piv = best.pivot(index="asset", columns="feature_set", values=metric)
    # Preserve column order
    piv = piv[list(FEATURE_SETS.keys())]
    return piv


# =============================================================================
# Stage 6 — Feature importance (XGBoost, best-cell per asset)
# =============================================================================
def feature_importance_plots(df: pd.DataFrame):
    import matplotlib.pyplot as plt
    try:
        from xgboost import XGBClassifier
    except ImportError:
        print("[importance] xgboost not installed — skipping")
        return

    for asset, spike_col in [("BTC", "btc_spike"), ("GLD", "gld_spike")]:
        cols = feature_cols_for(["fin", "pol", "all"])
        cols = [c for c in cols if c in df.columns]
        data = df.dropna(subset=[spike_col])[cols + [spike_col]].dropna()
        if len(data) < 40:
            continue
        X = data[cols].values
        y = data[spike_col].values.astype(int)
        if len(np.unique(y)) < 2:
            continue
        model = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                              eval_metric="logloss", random_state=RANDOM_STATE,
                              n_jobs=-1, verbosity=0)
        model.fit(X, y)
        imp = pd.Series(model.feature_importances_, index=cols).sort_values().tail(15)

        plt.figure(figsize=(8, 6))
        imp.plot(kind="barh")
        plt.title(f"{asset} spike — top 15 XGBoost feature importances")
        plt.xlabel("Importance")
        plt.tight_layout()
        out = PLOTS / f"feature_importance_{asset.lower()}.png"
        plt.savefig(out, dpi=130)
        plt.close()
        print(f"[plot] {out.name}")


# =============================================================================
# Stage 7 — Overlay + model comparison plots
# =============================================================================
def overlay_plots(df: pd.DataFrame):
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    for ax, (asset, close) in zip(axes, [("BTC", "btc_close"), ("GLD", "gld_close")]):
        sub = df[[close, "all_sent_mean"]].dropna()
        if sub.empty:
            continue
        ax2 = ax.twinx()
        ax.plot(sub.index, sub[close], color="black", label=f"{asset} close")
        ax2.plot(sub.index, sub["all_sent_mean"].rolling(7).mean(),
                 color="tab:blue", alpha=0.7, label="sentiment (7d MA)")
        ax.set_ylabel(f"{asset} price", color="black")
        ax2.set_ylabel("sentiment", color="tab:blue")
        ax.set_title(f"{asset} price vs rolling mean sentiment")
    plt.tight_layout()
    path = PLOTS / "price_vs_sentiment.png"
    plt.savefig(path, dpi=130)
    plt.close()
    print(f"[plot] {path.name}")


def model_comparison_plot(results: pd.DataFrame):
    import matplotlib.pyplot as plt

    for asset in ["BTC", "GLD"]:
        sub = results[results["asset"] == asset]
        if sub.empty:
            continue
        piv = sub.pivot(index="feature_set", columns="model", values="f1")
        piv = piv.loc[list(FEATURE_SETS.keys())]
        ax = piv.plot(kind="bar", figsize=(8, 5))
        ax.set_title(f"{asset} spike prediction — F1 by model x feature set")
        ax.set_ylabel("F1 (walk-forward mean)")
        ax.axhline(0, color="gray", linewidth=0.5)
        plt.xticks(rotation=0)
        plt.tight_layout()
        path = PLOTS / f"model_comparison_{asset.lower()}.png"
        plt.savefig(path, dpi=130)
        plt.close()
        print(f"[plot] {path.name}")


# =============================================================================
# Main
# =============================================================================
def main():
    sent = load_sentiment()
    btc = load_btc_daily()
    gld = load_gld_daily()

    # Outer-join sentiment + BTC (daily, 24/7), then left-join GLD (weekdays only).
    df = sent.join(btc, how="outer").join(gld, how="outer").sort_index()

    # Targets
    df = add_targets(df, "btc_close", "btc_volume", "btc")
    df = add_targets(df, "gld_close", "gld_volume", "gld")

    # Lag features
    df = engineer_lags(df)

    # Save merged dataset for inspection
    merged_path = ARTIFACTS / "merged_daily.csv"
    df.to_csv(merged_path)
    print(f"[save] {merged_path.name} ({df.shape[0]} rows x {df.shape[1]} cols)")

    # Stats
    plot_correlation(df, PLOTS / "correlation_heatmap.png")
    granger_table(df, ARTIFACTS / "granger_results.csv")

    # Models — the 2x3 matrix
    print("\n[models] training walk-forward CV across 2 assets x 3 feature sets x 3 models")
    results = build_results_matrix(df)
    results.to_csv(ARTIFACTS / "results_full.csv", index=False)

    f1_mat = pretty_matrix(results, "f1")
    auc_mat = pretty_matrix(results, "auc")
    f1_mat.to_csv(ARTIFACTS / "results_matrix_f1.csv")
    auc_mat.to_csv(ARTIFACTS / "results_matrix_auc.csv")

    print("\n===== 2x3 matrix — F1 (best model per cell) =====")
    print(f1_mat.round(3).to_string())
    print("\n===== 2x3 matrix — AUC (best model per cell) =====")
    print(auc_mat.round(3).to_string())

    # Plots
    overlay_plots(df)
    feature_importance_plots(df)
    model_comparison_plot(results)

    print(f"\n[done] all outputs in {ARTIFACTS}/ and {PLOTS}/")


if __name__ == "__main__":
    main()
