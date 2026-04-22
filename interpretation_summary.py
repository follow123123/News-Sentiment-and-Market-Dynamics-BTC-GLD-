from __future__ import annotations

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).parent / "artifacts" / "correlation_visualization_interpretation"


def latest_file(pattern: str) -> Path:
    matches = sorted(BASE_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No files matched {pattern!r} in {BASE_DIR}")
    return matches[-1]


def best_auc_line(auc_df: pd.DataFrame) -> str:
    stacked = auc_df.stack().rename("auc").reset_index()
    feature_col = next(col for col in stacked.columns if col not in {"asset", "auc"})
    best = stacked.sort_values("auc", ascending=False).iloc[0]
    return f"Best 2x3 AUC cell: {best['asset']} / {best[feature_col]} = {best['auc']:.3f}"


def best_ablation_lines(ablation_df: pd.DataFrame) -> list[str]:
    best = (
        ablation_df.sort_values("auc", ascending=False)
        .groupby(["asset", "feature_set"], as_index=False)
        .first()
        .sort_values(["asset", "auc"], ascending=[True, False])
    )
    return [
        f"{row['asset']}: {row['feature_set']} gives AUC {row['auc']:.3f} with {row['model']}"
        for _, row in best.iterrows()
    ]


def strongest_corr_lines(corr_df: pd.DataFrame, asset_prefix: str) -> list[str]:
    sub = corr_df[corr_df["target"].str.startswith(asset_prefix)].sort_values(
        "abs_rho", ascending=False
    ).head(3)
    return [
        f"{row['feature']} vs {row['target']}: rho {row['spearman_rho']:.3f}"
        for _, row in sub.iterrows()
    ]


def granger_lines(granger_df: pd.DataFrame) -> list[str]:
    sig = granger_df[granger_df["significant_5pct"]].sort_values("p_value")
    if sig.empty:
        return ["No ADF-corrected Granger result reached p < 0.05."]
    return [
        f"{row['target']} <- {row['sentiment']} lag {int(row['lag'])}: p={row['p_value']:.4f}"
        for _, row in sig.iterrows()
    ]


def main() -> None:
    corr_path = latest_file("stream_target_correlations_*.csv")
    auc_path = latest_file("results_matrix_auc_*.csv")
    ablation_path = latest_file("price_vs_sentiment_ablation_*.csv")
    granger_path = latest_file("granger_with_adf_*.csv")

    corr_df = pd.read_csv(corr_path)
    auc_df = pd.read_csv(auc_path, index_col=0)
    ablation_df = pd.read_csv(ablation_path)
    granger_df = pd.read_csv(granger_path)

    lines = [
        "Correlation / Visualization / Interpretation Summary",
        "",
        best_auc_line(auc_df),
        "",
        "Strongest BTC stream-level correlations:",
        *[f"- {line}" for line in strongest_corr_lines(corr_df, "btc_")],
        "",
        "Strongest GLD stream-level correlations:",
        *[f"- {line}" for line in strongest_corr_lines(corr_df, "gld_")],
        "",
        "Price-vs-sentiment ablation:",
        *[f"- {line}" for line in best_ablation_lines(ablation_df)],
        "",
        "ADF-corrected Granger results:",
        *[f"- {line}" for line in granger_lines(granger_df)],
        "",
        "Key plot files in artifacts/correlation_visualization_interpretation/plots:",
        "- correlation_heatmap_*.png",
        "- stream_target_heatmap_*.png",
        "- price_vs_sentiment_*.png",
        "- spike_timeline_*.png",
        "- results_matrix_auc_*.png",
    ]

    out_path = BASE_DIR / "interpretation_summary.txt"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"\n[save] {out_path}")


if __name__ == "__main__":
    main()
