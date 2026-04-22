from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from analyze_and_model import (
    ARTIFACTS,
    DEFAULT_SPIKE_SIGMA,
    add_targets,
    build_results_matrix,
    engineer_lags,
    load_btc_daily,
    load_gld_daily,
    load_sentiment,
    plot_correlation,
    pretty_matrix,
    spike_timeline_plot,
)
from deeper_analysis import add_price_lags, build_ablation, granger_with_adf

SECTION_DIR = ARTIFACTS / "correlation_visualization_interpretation"
PLOTS_DIR = SECTION_DIR / "plots"
SECTION_DIR.mkdir(parents=True, exist_ok=True)
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

SENT_STREAMS = ["all", "fin", "pol"]
TARGETS = [
    "btc_return",
    "btc_abs_return",
    "btc_spike",
    "gld_return",
    "gld_abs_return",
    "gld_spike",
]


def build_modeling_table(sigma: float) -> pd.DataFrame:
    try:
        sent = load_sentiment()
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            "Missing artifacts/daily_sentiment.csv. Run finetune_financialbert.py "
            "first to generate the daily sentiment features."
        ) from exc

    btc = load_btc_daily()
    gld = load_gld_daily()
    df = sent.join(btc, how="outer").join(gld, how="outer").sort_index()
    df = add_targets(df, "btc_close", "btc_volume", "btc", sigma)
    df = add_targets(df, "gld_close", "gld_volume", "gld", sigma)
    df = engineer_lags(df)
    df = add_price_lags(df)
    return df


def full_correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    sent_cols = [
        c for c in df.columns
        if c.endswith("_lag1") and any(c.startswith(f"{stream}_") for stream in SENT_STREAMS)
    ]
    for sent_col in sent_cols:
        for target in TARGETS:
            pair = df[[sent_col, target]].dropna()
            if len(pair) < 20:
                continue
            rho = pair[sent_col].corr(pair[target], method="spearman")
            if pd.isna(rho):
                continue
            rows.append({
                "feature": sent_col,
                "target": target,
                "n": len(pair),
                "spearman_rho": round(float(rho), 4),
                "abs_rho": round(abs(float(rho)), 4),
            })
    return pd.DataFrame(rows).sort_values(["abs_rho", "feature"], ascending=[False, True])


def stream_target_correlation_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for stream in SENT_STREAMS:
        sent_col = f"{stream}_sent_mean_lag1"
        if sent_col not in df.columns:
            continue
        for target in TARGETS:
            pair = df[[sent_col, target]].dropna()
            if len(pair) < 20:
                continue
            rho = pair[sent_col].corr(pair[target], method="spearman")
            if pd.isna(rho):
                continue
            rows.append({
                "stream": stream,
                "feature": sent_col,
                "target": target,
                "n": len(pair),
                "spearman_rho": round(float(rho), 4),
                "abs_rho": round(abs(float(rho)), 4),
            })
    return pd.DataFrame(rows).sort_values(["target", "abs_rho"], ascending=[True, False])


def plot_stream_target_heatmap(corr_df: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt
    import seaborn as sns

    if corr_df.empty:
        return

    pivot = corr_df.pivot(index="stream", columns="target", values="spearman_rho")
    pivot = pivot.reindex(SENT_STREAMS)

    plt.figure(figsize=(8, 3.6))
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".2f",
        cmap="RdBu_r",
        center=0,
        cbar_kws={"label": "Spearman rho"},
    )
    plt.title("Lag-1 sentiment mean vs market outcomes")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def plot_auc_heatmap(auc_matrix: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt
    import seaborn as sns

    if auc_matrix.empty:
        return

    plt.figure(figsize=(6.8, 3.6))
    sns.heatmap(
        auc_matrix,
        annot=True,
        fmt=".3f",
        cmap="Blues",
        vmin=0.4,
        vmax=0.7,
        cbar_kws={"label": "AUC"},
    )
    plt.title("Best walk-forward AUC by asset and sentiment stream")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def plot_price_sentiment_overlay(df: pd.DataFrame, path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    for ax, (asset, close_col, sent_col) in zip(
        axes,
        [("BTC", "btc_close", "all_sent_mean"), ("GLD", "gld_close", "all_sent_mean")],
    ):
        sub = df[[close_col, sent_col]].dropna()
        if sub.empty:
            continue
        ax2 = ax.twinx()
        ax.plot(sub.index, sub[close_col], color="black", label=f"{asset} close")
        ax2.plot(
            sub.index,
            sub[sent_col].rolling(7).mean(),
            color="tab:blue",
            alpha=0.75,
            label="all_sent_mean (7d MA)",
        )
        ax.set_ylabel(f"{asset} price", color="black")
        ax2.set_ylabel("sentiment", color="tab:blue")
        ax.set_title(f"{asset} price vs all-news sentiment")
    plt.tight_layout()
    plt.savefig(path, dpi=130)
    plt.close()


def save_interpretation_snapshot(
    sigma: float,
    corr_df: pd.DataFrame,
    auc_matrix: pd.DataFrame,
    ablation_df: pd.DataFrame,
    granger_df: pd.DataFrame,
    path: Path,
) -> None:
    lines = [f"sigma={sigma:.1f}", ""]

    if not corr_df.empty:
        btc_corr = corr_df[corr_df["target"].str.startswith("btc_")].sort_values(
            "abs_rho", ascending=False
        ).head(3)
        gld_corr = corr_df[corr_df["target"].str.startswith("gld_")].sort_values(
            "abs_rho", ascending=False
        ).head(3)
        lines.append("Top BTC stream-level correlations:")
        for _, row in btc_corr.iterrows():
            lines.append(
                f"- {row['feature']} vs {row['target']}: rho={row['spearman_rho']:.3f} (n={int(row['n'])})"
            )
        lines.append("")
        lines.append("Top GLD stream-level correlations:")
        for _, row in gld_corr.iterrows():
            lines.append(
                f"- {row['feature']} vs {row['target']}: rho={row['spearman_rho']:.3f} (n={int(row['n'])})"
            )
        lines.append("")

    if not auc_matrix.empty:
        best_cell = (
            auc_matrix.stack()
            .rename("auc")
            .reset_index()
            .sort_values("auc", ascending=False)
            .iloc[0]
        )
        lines.append(
            f"Best 2x3 AUC cell: {best_cell['asset']} / {best_cell['feature_set']} = {best_cell['auc']:.3f}"
        )
        lines.append("")

    if not ablation_df.empty:
        best_ablation = (
            ablation_df.sort_values("auc", ascending=False)
            .groupby(["asset", "feature_set"], as_index=False)
            .first()
        )
        lines.append("Best ablation AUC by feature set:")
        for _, row in best_ablation.iterrows():
            lines.append(
                f"- {row['asset']} / {row['feature_set']}: AUC={row['auc']:.3f} ({row['model']})"
            )
        lines.append("")

    sig = granger_df[granger_df["significant_5pct"]]
    if sig.empty:
        lines.append("No Granger relationship reached p < 0.05 after ADF correction.")
    else:
        lines.append("ADF-corrected significant Granger results:")
        for _, row in sig.sort_values("p_value").iterrows():
            lines.append(
                f"- {row['target']} <- {row['sentiment']} at lag {int(row['lag'])}: p={row['p_value']:.4f}"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sigma",
        type=float,
        default=DEFAULT_SPIKE_SIGMA,
        help="Spike threshold in rolling standard deviations",
    )
    args = parser.parse_args()

    sigma = args.sigma
    tag = f"sig{sigma:.1f}".replace(".", "p")

    df = build_modeling_table(sigma)
    merged_path = SECTION_DIR / f"merged_daily_{tag}.csv"
    df.to_csv(merged_path)
    print(f"[save] {merged_path.name} ({df.shape[0]} rows x {df.shape[1]} cols)")

    corr_full = full_correlation_table(df)
    corr_stream = stream_target_correlation_table(df)
    corr_full.to_csv(SECTION_DIR / f"lagged_correlations_full_{tag}.csv", index=False)
    corr_stream.to_csv(SECTION_DIR / f"stream_target_correlations_{tag}.csv", index=False)
    corr_full.head(20).to_csv(SECTION_DIR / f"top20_correlations_{tag}.csv", index=False)

    plot_correlation(df, PLOTS_DIR / f"correlation_heatmap_{tag}.png")
    plot_stream_target_heatmap(corr_stream, PLOTS_DIR / f"stream_target_heatmap_{tag}.png")
    plot_price_sentiment_overlay(df, PLOTS_DIR / f"price_vs_sentiment_{tag}.png")
    spike_timeline_plot(df, PLOTS_DIR / f"spike_timeline_{tag}.png")

    results = build_results_matrix(df)
    results.to_csv(SECTION_DIR / f"results_full_{tag}.csv", index=False)
    auc_matrix = pretty_matrix(results, "auc")
    f1_matrix = pretty_matrix(results, "f1")
    auc_matrix.to_csv(SECTION_DIR / f"results_matrix_auc_{tag}.csv")
    f1_matrix.to_csv(SECTION_DIR / f"results_matrix_f1_{tag}.csv")
    plot_auc_heatmap(auc_matrix, PLOTS_DIR / f"results_matrix_auc_{tag}.png")

    ablation = build_ablation(df)
    ablation.to_csv(SECTION_DIR / f"price_vs_sentiment_ablation_{tag}.csv", index=False)

    granger = granger_with_adf(df, SECTION_DIR / f"granger_with_adf_{tag}.csv")

    save_interpretation_snapshot(
        sigma=sigma,
        corr_df=corr_stream,
        auc_matrix=auc_matrix,
        ablation_df=ablation,
        granger_df=granger,
        path=SECTION_DIR / f"interpretation_snapshot_{tag}.txt",
    )

    print(f"[done] dedicated outputs in {SECTION_DIR}/ and {PLOTS_DIR}/")


if __name__ == "__main__":
    main()
