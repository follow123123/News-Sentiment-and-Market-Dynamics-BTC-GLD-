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

import argparse
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
DEFAULT_SPIKE_SIGMA = 2.0  # volatility spike: |return| > SIGMA * rolling std
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
def add_targets(df: pd.DataFrame, close_col: str, vol_col: str, prefix: str,
                sigma: float):
    ret = df[close_col].pct_change()
    abs_ret = ret.abs()
    roll_std = abs_ret.rolling(ROLL_WINDOW, min_periods=10).std()
    roll_mean_vol = df[vol_col].rolling(ROLL_WINDOW, min_periods=10).mean()
    roll_std_vol = df[vol_col].rolling(ROLL_WINDOW, min_periods=10).std()

    df[f"{prefix}_return"] = ret
    df[f"{prefix}_abs_return"] = abs_ret
    df[f"{prefix}_spike"] = (abs_ret > sigma * roll_std).astype(int)
    df[f"{prefix}_surge"] = (df[vol_col] > roll_mean_vol + sigma * roll_std_vol).astype(int)
    return df


# =============================================================================
# Stage 3 — Lag features
# =============================================================================
SENT_STREAMS = ["all", "fin", "pol"]
SENT_CORE = ["sent_mean", "sent_var", "headline_count", "pos_share", "neg_share"]


def engineer_lags(df: pd.DataFrame) -> pd.DataFrame:
    """Add lag1, rolling means over LAGS, and momentum for every sentiment col.

    Impute NaN in sentiment columns with neutral defaults BEFORE computing
    lags. Without this, any day with zero political headlines becomes NaN
    for all pol_* features, and downstream dropna() wipes most rows.
    """
    out = df.copy()
    # Impute: sentiment means/variances/shares -> 0 (neutral), counts -> 0
    for stream in SENT_STREAMS:
        for feat in SENT_CORE:
            col = f"{stream}_{feat}"
            if col in out.columns:
                out[col] = out[col].fillna(0.0)
    # Now compute lags/rolls/momentum on the filled series
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
    # Catch both missing package AND missing libomp on macOS (XGBoostError)
    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except Exception as e:
        print(f"[models] XGBoost unavailable ({type(e).__name__}); "
              f"skipping. Install libomp on macOS: brew install libomp")
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
    except Exception as e:
        print(f"[importance] xgboost unavailable ({type(e).__name__}) — skipping")
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


def granger_heatmap(granger_df: pd.DataFrame, path: Path):
    """Heatmap of -log10(p) across (target, sentiment) x lag."""
    import matplotlib.pyplot as plt
    import seaborn as sns

    if granger_df.empty:
        print("[plot] granger heatmap skipped (empty results)")
        return
    g = granger_df.copy()
    g["row"] = g["target"] + " <- " + g["sentiment"]
    pivot = g.pivot(index="row", columns="lag", values="p_value")
    neglog = -np.log10(pivot.clip(lower=1e-6))

    plt.figure(figsize=(8, max(4, 0.4 * len(pivot))))
    sns.heatmap(neglog, annot=pivot.round(3), fmt="", cmap="viridis",
                cbar_kws={"label": "-log10(p)"}, annot_kws={"size": 9})
    plt.title("Granger causality (cell = raw p-value; color = -log10 p)\n"
              "brighter = more significant; p<0.05 threshold = -log10(p) > 1.3")
    plt.xlabel("Lag (days)")
    plt.ylabel("target <- sentiment")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()
    print(f"[plot] {path.name}")


def roc_curves_plot(df: pd.DataFrame, results: pd.DataFrame, path_prefix: Path):
    """One plot per asset, with ROC curves for all three feature sets overlaid."""
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    def best_model_factory(asset, fs_name):
        sub = results[(results.asset == asset) & (results.feature_set == fs_name)]
        if sub.empty:
            return None
        # Pick the model with highest AUC for this cell
        mname = sub.sort_values("auc", ascending=False).iloc[0]["model"]
        return mname

    for asset, spike_col in [("BTC", "btc_spike"), ("GLD", "gld_spike")]:
        plt.figure(figsize=(7, 6))
        plt.plot([0, 1], [0, 1], "k--", alpha=0.4, label="chance")
        any_plotted = False
        for fs_name, streams in FEATURE_SETS.items():
            cols = [c for c in feature_cols_for(streams) if c in df.columns]
            data = df.dropna(subset=[spike_col])[cols + [spike_col]].dropna()
            if len(data) < 40:
                continue
            X = data[cols].values
            y = data[spike_col].values.astype(int)
            if len(np.unique(y)) < 2:
                continue
            # Aggregate OOF predictions across walk-forward folds
            tscv = TimeSeriesSplit(n_splits=WALK_FOLDS)
            oof_y, oof_p = [], []
            for tr, te in tscv.split(X):
                if len(np.unique(y[tr])) < 2:
                    continue
                mdl = Pipeline([
                    ("sc", StandardScaler()),
                    ("lr", LogisticRegression(max_iter=1000, class_weight="balanced",
                                              random_state=RANDOM_STATE)),
                ])
                mdl.fit(X[tr], y[tr])
                oof_y.extend(y[te])
                oof_p.extend(mdl.predict_proba(X[te])[:, 1])
            if not oof_y or len(set(oof_y)) < 2:
                continue
            fpr, tpr, _ = roc_curve(oof_y, oof_p)
            from sklearn.metrics import roc_auc_score
            auc = roc_auc_score(oof_y, oof_p)
            plt.plot(fpr, tpr, label=f"{fs_name} (AUC={auc:.2f})")
            any_plotted = True
        if not any_plotted:
            plt.close()
            continue
        plt.xlabel("False positive rate")
        plt.ylabel("True positive rate")
        plt.title(f"{asset} spike prediction — ROC (walk-forward OOF, LogReg)")
        plt.legend(loc="lower right")
        plt.tight_layout()
        out = Path(f"{path_prefix}_{asset.lower()}.png")
        plt.savefig(out, dpi=130)
        plt.close()
        print(f"[plot] {out.name}")


def spike_timeline_plot(df: pd.DataFrame, path: Path):
    """Price time series with spike days marked and sentiment overlay."""
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True)

    # Known event to annotate
    events = {"2024-11-05": "US Election"}

    for ax, (asset, close, spike, sent_col) in zip(axes, [
        ("BTC", "btc_close", "btc_spike", "fin_sent_mean"),
        ("GLD", "gld_close", "gld_spike", "pol_sent_mean"),
    ]):
        sub = df[[close, spike, sent_col]].dropna(subset=[close])
        if sub.empty:
            continue
        ax.plot(sub.index, sub[close], color="black", lw=1.2, label=f"{asset} close")
        # Mark spike days
        spike_days = sub[sub[spike] == 1].index
        for d in spike_days:
            ax.axvline(d, color="red", alpha=0.25, lw=0.9)
        # Sentiment overlay on second y-axis
        ax2 = ax.twinx()
        ax2.plot(sub.index, sub[sent_col].rolling(7).mean(),
                 color="tab:blue", alpha=0.7, lw=1.1,
                 label=f"{sent_col} (7d MA)")
        ax2.set_ylabel("sentiment", color="tab:blue")
        ax.set_ylabel(f"{asset} price")
        ax.set_title(f"{asset} — price (black), sentiment 7d MA (blue), "
                     f"spike days (red verticals)  |  "
                     f"{int(sub[spike].sum())} spikes")
        # Annotate known events
        for date_str, label in events.items():
            d = pd.to_datetime(date_str)
            if sub.index.min() <= d <= sub.index.max():
                ax.axvline(d, color="green", lw=1.5, ls="--", alpha=0.6)
                ax.text(d, ax.get_ylim()[1] * 0.98, f" {label}",
                        color="green", fontsize=9, va="top")
    plt.tight_layout()
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
def run_once(sigma: float, tag: str):
    """Run the full pipeline at a given spike sigma. Outputs get `tag` suffix."""
    sent = load_sentiment()
    btc = load_btc_daily()
    gld = load_gld_daily()

    df = sent.join(btc, how="outer").join(gld, how="outer").sort_index()
    df = add_targets(df, "btc_close", "btc_volume", "btc", sigma)
    df = add_targets(df, "gld_close", "gld_volume", "gld", sigma)
    df = engineer_lags(df)

    btc_rate = df["btc_spike"].mean()
    gld_rate = df["gld_spike"].mean()
    print(f"\n[{tag}] spike rate: BTC={btc_rate:.1%}  GLD={gld_rate:.1%}")

    merged_path = ARTIFACTS / f"merged_daily_{tag}.csv"
    df.to_csv(merged_path)
    print(f"[save] {merged_path.name} ({df.shape[0]} rows x {df.shape[1]} cols)")

    plot_correlation(df, PLOTS / f"correlation_heatmap_{tag}.png")
    g_df = granger_table(df, ARTIFACTS / f"granger_results_{tag}.csv")
    granger_heatmap(g_df, PLOTS / f"granger_heatmap_{tag}.png")
    spike_timeline_plot(df, PLOTS / f"spike_timeline_{tag}.png")

    print(f"\n[{tag}] training walk-forward CV (2 assets x 3 feature sets x 3 models)")
    results = build_results_matrix(df)
    results.to_csv(ARTIFACTS / f"results_full_{tag}.csv", index=False)

    f1_mat = pretty_matrix(results, "f1")
    auc_mat = pretty_matrix(results, "auc")
    f1_mat.to_csv(ARTIFACTS / f"results_matrix_f1_{tag}.csv")
    auc_mat.to_csv(ARTIFACTS / f"results_matrix_auc_{tag}.csv")

    print(f"\n===== [{tag}] 2x3 matrix — F1 (best model per cell) =====")
    print(f1_mat.round(3).to_string())
    print(f"\n===== [{tag}] 2x3 matrix — AUC (best model per cell) =====")
    print(auc_mat.round(3).to_string())

    overlay_plots(df)  # asset-level plot, same regardless of sigma
    feature_importance_plots(df)
    model_comparison_plot(results)
    roc_curves_plot(df, results, PLOTS / f"roc_{tag}")
    # Re-tag the plots that depend on sigma
    for name in ["feature_importance_btc", "feature_importance_gld",
                 "model_comparison_btc", "model_comparison_gld"]:
        src = PLOTS / f"{name}.png"
        if src.exists():
            src.rename(PLOTS / f"{name}_{tag}.png")

    return {"sigma": sigma, "tag": tag,
            "btc_spike_rate": btc_rate, "gld_spike_rate": gld_rate,
            "f1_matrix": f1_mat, "auc_matrix": auc_mat}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sigmas", nargs="+", type=float,
                        default=[DEFAULT_SPIKE_SIGMA, 1.5],
                        help="Spike thresholds to sweep (in rolling-std units)")
    args = parser.parse_args()

    summaries = []
    for sigma in args.sigmas:
        tag = f"sig{sigma:.1f}".replace(".", "p")  # e.g. sig1p5, sig2p0
        summaries.append(run_once(sigma, tag))

    print("\n" + "=" * 60)
    print("SWEEP SUMMARY")
    print("=" * 60)
    for s in summaries:
        print(f"\nsigma = {s['sigma']:.1f}  "
              f"(BTC spike rate {s['btc_spike_rate']:.1%}, "
              f"GLD spike rate {s['gld_spike_rate']:.1%})")
        print("AUC:")
        print(s["auc_matrix"].round(3).to_string())

    print(f"\n[done] all outputs in {ARTIFACTS}/ and {PLOTS}/")


if __name__ == "__main__":
    main()
