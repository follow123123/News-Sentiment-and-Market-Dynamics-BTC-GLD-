"""
Generate Ablation Results Bar Chart for News Sentiment & Market Dynamics project.
Shows Price-only vs Sentiment-only vs Combined AUC for BTC and GLD.

Run:
    python generate_ablation_chart.py
"""

import warnings
warnings.filterwarnings("ignore")

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_DIR = Path(__file__).parent
ARTIFACTS = PROJECT_DIR / "artifacts"
PLOTS = ARTIFACTS / "plots"
PLOTS.mkdir(parents=True, exist_ok=True)

plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"
sns.set_style("whitegrid")

COLORS = {
    "deep": "#065A82",
    "teal": "#1C7293",
    "accent": "#F0A202",
    "pos": "#2E7D32",
}


def plot_ablation_bar_chart():
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Data from ablation study
    feature_sets = ["Price only", "Sentiment only", "Price + Sentiment"]
    btc_auc = [0.640, 0.674, 0.582]
    gld_auc = [0.591, 0.563, 0.585]
    
    x = np.arange(len(feature_sets))
    width = 0.35
    
    # BTC bar chart
    ax1 = axes[0]
    bars1 = ax1.bar(x, btc_auc, width, color=COLORS["deep"], edgecolor="white", linewidth=1.5)
    
    # Highlight best BTC result
    best_idx = btc_auc.index(max(btc_auc))
    bars1[best_idx].set_color(COLORS["pos"])
    
    ax1.set_xlabel("Feature Set", fontsize=11)
    ax1.set_ylabel("AUC Score", fontsize=11)
    ax1.set_title("Bitcoin (BTC) — Ablation Study\nBest: Sentiment-only (0.674)", 
                   fontsize=12, fontweight="bold", color=COLORS["deep"])
    ax1.set_xticks(x)
    ax1.set_xticklabels(feature_sets, fontsize=10)
    ax1.set_ylim([0.5, 0.75])
    ax1.axhline(y=0.5, color="gray", linestyle="--", linewidth=1, alpha=0.5, label="Chance level")
    ax1.set_yticks([0.5, 0.55, 0.6, 0.65, 0.7, 0.75])
    
    # Add value labels on bars
    for bar, val in zip(bars1, btc_auc):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    
    ax1.legend(loc="upper right", fontsize=9)
    ax1.grid(axis="y", alpha=0.3)
    
    # GLD bar chart
    ax2 = axes[1]
    bars2 = ax2.bar(x, gld_auc, width, color=COLORS["accent"], edgecolor="white", linewidth=1.5)
    
    ax2.set_xlabel("Feature Set", fontsize=11)
    ax2.set_ylabel("AUC Score", fontsize=11)
    ax2.set_title("Gold (GLD) — Ablation Study\nAll results near chance (0.5)", 
                   fontsize=12, fontweight="bold", color=COLORS["accent"])
    ax2.set_xticks(x)
    ax2.set_xticklabels(feature_sets, fontsize=10)
    ax2.set_ylim([0.5, 0.75])
    ax2.axhline(y=0.5, color="gray", linestyle="--", linewidth=1, alpha=0.5, label="Chance level")
    ax2.set_yticks([0.5, 0.55, 0.6, 0.65, 0.7, 0.75])
    
    # Add value labels on bars
    for bar, val in zip(bars2, gld_auc):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                f"{val:.3f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(axis="y", alpha=0.3)
    
    plt.tight_layout()
    out = PLOTS / "ablation_bar_chart.png"
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[plot] {out.name}")
    return out


if __name__ == "__main__":
    plot_ablation_bar_chart()
    print(f"Saved to: {PLOTS / 'ablation_bar_chart.png'}")