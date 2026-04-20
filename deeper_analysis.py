"""
Deeper modeling + analysis beyond the baseline 2x3 matrix.

Key questions this answers:
  1. Does sentiment add predictive value *beyond* price-autoregressive features?
     (Price-only vs Sentiment-only vs Combined ablation.)
  2. Can we predict volatility *magnitude* (not just binary spikes) via ridge?
  3. Are Granger results statistically valid? (ADF stationarity pre-check.)
  4. Which features drive the best model? (SHAP on the top XGBoost cell.)
  5. Are predicted probabilities well-calibrated? (Reliability diagrams.)

Run:
    pip install shap statsmodels
    python deeper_analysis.py
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

from analyze_and_model import (ARTIFACTS, PLOTS, SENT_STREAMS, FEATURE_SETS,
                                ROLL_WINDOW, RANDOM_STATE, WALK_FOLDS,
                                DEFAULT_SPIKE_SIGMA,
                                load_sentiment, load_btc_daily, load_gld_daily,
                                add_targets, engineer_lags, feature_cols_for)

SIGMA = DEFAULT_SPIKE_SIGMA  # use 2.0 (proposal spec)


# =============================================================================
# 1. Price-autoregressive features — the critical missing baseline
# =============================================================================
def add_price_lags(df: pd.DataFrame) -> pd.DataFrame:
    """Add past-return and past-volatility features for each asset.

    GLD doesn't trade on weekends, so its return series has NaN gaps. We
    forward-fill those gaps before computing rolling stats (weekend state
    == last Friday state) to avoid wiping rolling windows. BTC trades
    24/7 and doesn't need this treatment.
    """
    out = df.copy()
    for asset in ["btc", "gld"]:
        r_raw = out[f"{asset}_return"]
        ar_raw = out[f"{asset}_abs_return"]
        if asset == "gld":
            r = r_raw.ffill()
            ar = ar_raw.ffill()
        else:
            r, ar = r_raw, ar_raw
        out[f"{asset}_ret_lag1"] = r.shift(1)
        out[f"{asset}_ret_lag2"] = r.shift(2)
        out[f"{asset}_ret_lag3"] = r.shift(3)
        out[f"{asset}_absret_lag1"] = ar.shift(1)
        out[f"{asset}_absret_lag3"] = ar.shift(3)
        out[f"{asset}_vol_rm5"]  = ar.shift(1).rolling(5,  min_periods=1).std()
        out[f"{asset}_vol_rm10"] = ar.shift(1).rolling(10, min_periods=1).std()
        out[f"{asset}_vol_rm30"] = ar.shift(1).rolling(30, min_periods=5).std()
    return out


def price_cols(asset: str) -> list[str]:
    a = asset.lower()
    return [f"{a}_ret_lag1", f"{a}_ret_lag2", f"{a}_ret_lag3",
            f"{a}_absret_lag1", f"{a}_absret_lag3",
            f"{a}_vol_rm5", f"{a}_vol_rm10", f"{a}_vol_rm30"]


# =============================================================================
# 2. Full ablation: price-only vs sentiment-only vs combined
# =============================================================================
def build_ablation(df: pd.DataFrame) -> pd.DataFrame:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import f1_score, roc_auc_score
    from sklearn.model_selection import TimeSeriesSplit
    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except Exception:
        has_xgb = False

    def make():
        m = {
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
            m["XGBoost"] = lambda: XGBClassifier(
                n_estimators=300, max_depth=4, learning_rate=0.05,
                eval_metric="logloss", random_state=RANDOM_STATE,
                n_jobs=-1, verbosity=0)
        return m

    def score(X, y, mfac):
        tscv = TimeSeriesSplit(n_splits=WALK_FOLDS)
        f1s, aucs = [], []
        for tr, te in tscv.split(X):
            if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2:
                continue
            mdl = mfac()
            mdl.fit(X[tr], y[tr])
            p = mdl.predict_proba(X[te])[:, 1]
            f1s.append(f1_score(y[te], (p >= 0.5).astype(int), zero_division=0))
            try: aucs.append(roc_auc_score(y[te], p))
            except ValueError: pass
        return (np.mean(f1s) if f1s else np.nan,
                np.mean(aucs) if aucs else np.nan)

    rows = []
    models = make()

    # Sentiment combined = all three streams; for this ablation, collapse to single bucket
    def sent_all_cols():
        return feature_cols_for(["fin", "pol", "all"])

    for asset, spike_col in [("BTC", "btc_spike"), ("GLD", "gld_spike")]:
        sub = df.dropna(subset=[spike_col]).copy()
        pcols = [c for c in price_cols(asset) if c in sub.columns]
        scols = [c for c in sent_all_cols() if c in sub.columns]

        feature_sets = {
            "Price only":            pcols,
            "Sentiment only":        scols,
            "Price + Sentiment":     pcols + scols,
        }

        for fs_name, cols in feature_sets.items():
            if not cols:
                continue
            data = sub[cols + [spike_col]].dropna()
            X = data[cols].values
            y = data[spike_col].values.astype(int)
            if len(np.unique(y)) < 2:
                continue
            for mname, mfac in models.items():
                f1, auc = score(X, y, mfac)
                rows.append({"asset": asset, "feature_set": fs_name,
                             "model": mname, "n": len(y),
                             "pos_rate": round(y.mean(), 3),
                             "f1": round(f1, 3), "auc": round(auc, 3)})
                print(f"[ablation] {asset:3s} | {fs_name:20s} | {mname:12s} "
                      f"AUC={auc:.3f} F1={f1:.3f} n={len(y)}")

    return pd.DataFrame(rows)


# =============================================================================
# 3. Ridge regression: predict volatility MAGNITUDE (not just binary spike)
# =============================================================================
def ridge_magnitude(df: pd.DataFrame) -> pd.DataFrame:
    from sklearn.linear_model import Ridge
    from sklearn.metrics import mean_absolute_error, r2_score
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    rows = []
    for asset, tgt_col in [("BTC", "btc_abs_return"), ("GLD", "gld_abs_return")]:
        sub = df.dropna(subset=[tgt_col]).copy()
        pcols = [c for c in price_cols(asset) if c in sub.columns]
        scols = [c for c in feature_cols_for(["fin", "pol", "all"]) if c in sub.columns]

        feature_sets = {
            "Price only":        pcols,
            "Sentiment only":    scols,
            "Price + Sentiment": pcols + scols,
        }
        for fs_name, cols in feature_sets.items():
            if not cols: continue
            data = sub[cols + [tgt_col]].dropna()
            if len(data) < 40:
                continue
            X = data[cols].values
            y = data[tgt_col].values

            tscv = TimeSeriesSplit(n_splits=WALK_FOLDS)
            maes, r2s = [], []
            for tr, te in tscv.split(X):
                pipe = Pipeline([
                    ("sc", StandardScaler()),
                    ("rg", Ridge(alpha=1.0, random_state=RANDOM_STATE)),
                ])
                pipe.fit(X[tr], y[tr])
                pred = pipe.predict(X[te])
                maes.append(mean_absolute_error(y[te], pred))
                r2s.append(r2_score(y[te], pred))

            rows.append({"asset": asset, "feature_set": fs_name,
                         "n": len(y),
                         "mae": round(np.mean(maes), 5),
                         "r2":  round(np.mean(r2s),  3)})
            print(f"[ridge]   {asset:3s} | {fs_name:20s}  MAE={np.mean(maes):.5f}  R2={np.mean(r2s):+.3f}  n={len(y)}")
    return pd.DataFrame(rows)


# =============================================================================
# 4. Granger with ADF stationarity pre-check
# =============================================================================
def granger_with_adf(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    from statsmodels.tsa.stattools import adfuller, grangercausalitytests

    def adf_p(series):
        s = series.dropna()
        if len(s) < 20:
            return np.nan
        try: return adfuller(s, autolag="AIC")[1]
        except Exception: return np.nan

    targets = {"BTC_abs_return": "btc_abs_return",
               "GLD_abs_return": "gld_abs_return"}
    sents   = {"all": "all_sent_mean", "fin": "fin_sent_mean",
               "pol": "pol_sent_mean"}

    rows = []
    for tname, tcol in targets.items():
        for sname, scol in sents.items():
            pair = df[[tcol, scol]].dropna()
            if len(pair) < 40: continue

            tgt_adf = adf_p(pair[tcol])
            sent_adf = adf_p(pair[scol])
            tgt_stationary = (tgt_adf is not np.nan) and (tgt_adf < 0.05)
            sent_stationary = (sent_adf is not np.nan) and (sent_adf < 0.05)

            # If non-stationary, difference before running Granger
            series = pair.copy()
            if not tgt_stationary:
                series[tcol] = series[tcol].diff()
            if not sent_stationary:
                series[scol] = series[scol].diff()
            series = series.dropna()

            try:
                res = grangercausalitytests(series[[tcol, scol]], maxlag=5,
                                            verbose=False)
                for lag in range(1, 6):
                    p = res[lag][0]["ssr_ftest"][1]
                    rows.append({
                        "target": tname, "sentiment": sname, "lag": lag,
                        "p_value": round(p, 4),
                        "significant_5pct": p < 0.05,
                        "tgt_adf_p": round(tgt_adf, 4) if tgt_adf is not np.nan else None,
                        "sent_adf_p": round(sent_adf, 4) if sent_adf is not np.nan else None,
                        "tgt_stationary": tgt_stationary,
                        "sent_stationary": sent_stationary,
                    })
            except Exception as e:
                print(f"[granger-adf] skip {tname}<-{sname}: {e}")

    out = pd.DataFrame(rows)
    out.to_csv(path, index=False)
    print(f"[granger-adf] wrote {path.name} ({len(out)} rows)")
    return out


# =============================================================================
# 5. SHAP on best XGBoost cell (for interpretability)
# =============================================================================
def shap_best_cell(df: pd.DataFrame, asset: str, streams: list[str]):
    try:
        import shap
        from xgboost import XGBClassifier
    except Exception as e:
        print(f"[shap] unavailable ({type(e).__name__}) — run "
              f"`pip install shap`")
        return

    import matplotlib.pyplot as plt

    spike_col = f"{asset.lower()}_spike"
    pcols = [c for c in price_cols(asset) if c in df.columns]
    scols = [c for c in feature_cols_for(streams) if c in df.columns]
    cols = pcols + scols
    data = df.dropna(subset=[spike_col])[cols + [spike_col]].dropna()
    if len(data) < 50:
        print(f"[shap] not enough samples for {asset}")
        return
    X = data[cols]
    y = data[spike_col].astype(int)

    mdl = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                        eval_metric="logloss", random_state=RANDOM_STATE,
                        n_jobs=-1, verbosity=0)
    mdl.fit(X, y)

    explainer = shap.TreeExplainer(mdl)
    sv = explainer.shap_values(X)

    plt.figure()
    shap.summary_plot(sv, X, show=False, max_display=15, plot_size=(9, 6))
    plt.title(f"{asset} — SHAP feature contributions (XGBoost, price+sentiment)")
    plt.tight_layout()
    out = PLOTS / f"shap_{asset.lower()}.png"
    plt.savefig(out, dpi=130, bbox_inches="tight")
    plt.close()
    print(f"[plot] {out.name}")


# =============================================================================
# 6. Calibration curves
# =============================================================================
def calibration_plot(df: pd.DataFrame, path: Path):
    import matplotlib.pyplot as plt
    from sklearn.calibration import calibration_curve
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import TimeSeriesSplit

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    for ax, (asset, spike_col) in zip(axes, [("BTC", "btc_spike"),
                                              ("GLD", "gld_spike")]):
        sub = df.dropna(subset=[spike_col])
        pcols = [c for c in price_cols(asset) if c in sub.columns]
        scols = [c for c in feature_cols_for(["fin", "pol", "all"])
                 if c in sub.columns]
        for fs_name, cols in [("Price only",        pcols),
                              ("Price + Sentiment", pcols + scols)]:
            data = sub[cols + [spike_col]].dropna()
            X, y = data[cols].values, data[spike_col].values.astype(int)
            if len(np.unique(y)) < 2:
                continue
            tscv = TimeSeriesSplit(n_splits=WALK_FOLDS)
            oof_y, oof_p = [], []
            for tr, te in tscv.split(X):
                if len(np.unique(y[tr])) < 2: continue
                mdl = RandomForestClassifier(
                    n_estimators=300, max_depth=6,
                    class_weight="balanced",
                    random_state=RANDOM_STATE, n_jobs=-1)
                mdl.fit(X[tr], y[tr])
                oof_y.extend(y[te])
                oof_p.extend(mdl.predict_proba(X[te])[:, 1])
            if len(set(oof_y)) < 2: continue
            try:
                frac_pos, mean_pred = calibration_curve(oof_y, oof_p,
                                                        n_bins=8, strategy="quantile")
                ax.plot(mean_pred, frac_pos, marker="o", label=fs_name)
            except Exception:
                pass
        ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="perfect")
        ax.set_xlabel("Predicted probability")
        ax.set_ylabel("Observed spike frequency")
        ax.set_title(f"{asset} — calibration (walk-forward OOF, RF)")
        ax.legend(loc="upper left", fontsize=9)
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()
    print(f"[plot] {path.name}")


# =============================================================================
# Main
# =============================================================================
def main():
    # Load and build the modeling table with price lags in addition to sentiment lags.
    sent = load_sentiment()
    btc  = load_btc_daily()
    gld  = load_gld_daily()
    df = sent.join(btc, how="outer").join(gld, how="outer").sort_index()
    df = add_targets(df, "btc_close", "btc_volume", "btc", SIGMA)
    df = add_targets(df, "gld_close", "gld_volume", "gld", SIGMA)
    df = engineer_lags(df)
    df = add_price_lags(df)

    df.to_csv(ARTIFACTS / "merged_daily_with_price_lags.csv")
    print(f"[save] merged_daily_with_price_lags.csv "
          f"({df.shape[0]} rows x {df.shape[1]} cols)\n")

    # 1 & 2 — Price vs sentiment ablation (CLASSIFICATION)
    print("===== ablation: price-only vs sentiment-only vs combined (classification) =====")
    abl = build_ablation(df)
    abl.to_csv(ARTIFACTS / "ablation_price_vs_sentiment.csv", index=False)

    # Best AUC per (asset, feature_set)
    best = (abl.sort_values("auc", ascending=False)
               .groupby(["asset", "feature_set"], as_index=False).first())
    piv_auc = best.pivot(index="asset", columns="feature_set", values="auc")
    print("\n===== AUC (best model per cell) — the 'does sentiment add value?' test =====")
    print(piv_auc.round(3).to_string())

    # 3 — Ridge regression on magnitude
    print("\n===== ridge regression: predicting |return| =====")
    ridge_df = ridge_magnitude(df)
    ridge_df.to_csv(ARTIFACTS / "ridge_magnitude.csv", index=False)

    # 4 — Granger with stationarity pre-check
    print("\n===== Granger with ADF stationarity pre-check =====")
    gadf = granger_with_adf(df, ARTIFACTS / "granger_with_adf.csv")
    sig = gadf[gadf.significant_5pct]
    if not sig.empty:
        print("Statistically significant at p<0.05:")
        print(sig[["target", "sentiment", "lag", "p_value"]].to_string(index=False))
    else:
        print("No (sentiment -> volatility) lag reached p<0.05 after stationarity correction.")

    # 5 — SHAP on best asset+streams combo
    print("\n===== SHAP on XGBoost (price + all sentiment) =====")
    shap_best_cell(df, "BTC", ["fin", "pol", "all"])
    shap_best_cell(df, "GLD", ["fin", "pol", "all"])

    # 6 — Calibration
    print("\n===== Calibration =====")
    calibration_plot(df, PLOTS / "calibration.png")

    print(f"\n[done] outputs in {ARTIFACTS}/ and {PLOTS}/")


if __name__ == "__main__":
    main()
