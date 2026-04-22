# Project Development Log

A compacted record of the design decisions, bugs encountered, fixes applied,
and findings produced while building this project end-to-end. Useful for
reviewers, future maintainers, and writing up the methodology section.

---

## Phase 1 — Scoping and Data Understanding

### Starting materials
- Course project proposal: predict BTC and Gold volatility from news sentiment.
- Three CSVs: `normalized_news_july_dec_2024.csv` (21,005 headlines across
  50+ sources), `bitcoin_prices_2024_4h.csv` (1,098 four-hour candles),
  `GLD_ETF_Stock_Price_History_Converted.csv` (128 daily rows).
- Window: July 1 – December 30, 2024.

### Key design decisions
- **Dual-pipeline sentiment** (financial headlines vs political headlines vs
  combined) to answer "which kind of news matters for which asset?"
- **Binary spike classification** (|return| > 2σ above 30-day rolling mean)
  as the primary target, with ridge-regression magnitude as a secondary
  deliverable from the proposal.
- **Walk-forward cross-validation** (never train on future data) to produce
  credible out-of-sample metrics.

### Planned 2×3 result matrix
{BTC, GLD} × {Financial only, Political only, Combined} — the centrepiece
deliverable called for in the presentation outline.

---

## Phase 2 — Sentiment Model (Fine-tuning FinancialBERT)

### Decision: weak supervision over manual labelling
- No gold labels available; manual labelling ~500 headlines would take a
  weekend per person.
- Chose **Path A (weak supervision)**: zero-shot pseudo-label a stratified
  sample with BART-MNLI using market-framed hypotheses, then fine-tune
  FinancialBERT on the result.

### Pipeline (`finetune_financialbert.py`)
1. Load 21K headlines → 20,939 unique after dedupe.
2. Stratified sample across `tags` (financial / political / both) to 5,000 rows.
3. Zero-shot label with `facebook/bart-large-mnli` using hypotheses like
   *"this headline signals positive news for financial markets"*.
4. Confidence filter at 0.65 → 2,922 clean pseudo-labels.
5. Fine-tune `ahmedrachid/FinancialBERT-Sentiment-Analysis` (embeddings +
   bottom 4 encoder layers frozen) for 4 epochs, batch 64, lr 2e-5.
6. Score all 20,939 headlines; aggregate into daily sentiment features
   (mean, variance, count, positive share, negative share) split by stream.

### Hardware note
Apple Silicon M5 Pro / 48GB ran end-to-end in ~10 min on MPS.

### Ablation result
| Model                         | Accuracy | F1 (macro) |
|-------------------------------|---------:|-----------:|
| FinancialBERT (baseline)      |    0.526 |      0.423 |
| FinancialBERT (fine-tuned)    |    0.790 |      0.790 |

The gain is a **scheme-alignment gain** (fine-tuned model matches
BART-MNLI's market-framed labelling scheme) rather than proof of superhuman
accuracy, because we lack gold labels to compare against.

### Notable runtime issues resolved
- Pandas 2.x `groupby(..., group_keys=False).apply()` drops the grouping
  column → replaced with columnar groupby and per-tag filter+sample.
- HF `datasets` requires `ClassLabel` dtype for stratification → explicit
  `ds.cast_column("label", ClassLabel(...))`.
- Zero-shot under-predicts "neutral" on financial headlines (only ~14 rows
  cleared the confidence filter) → automatically drop any class with
  fewer than 20 samples, so the problem effectively became binary
  positive vs negative.
- Transformers 5.x removed `use_mps_device` and renamed `tokenizer` →
  `processing_class` on `Trainer` → added graceful try/except fallbacks.

---

## Phase 3 — Baseline 2×3 Matrix (`analyze_and_model.py`)

### Stages in the script
1. Load `daily_sentiment.csv` + BTC (resampled 4h → daily) + GLD daily OHLCV.
2. Merge on calendar date (outer-join BTC on 24/7 calendar, GLD on weekdays).
3. Compute returns, rolling volatility, binary spike labels (|return| > σ × rolling_std).
4. Engineer lag features (1-day lag, rolling means 1/3/7, momentum) per stream.
5. Correlation heatmap and Granger causality (p-values).
6. Walk-forward CV with LogReg, Random Forest, XGBoost for every cell of
   the 2×3 matrix.
7. Feature importance (XGBoost), ROC curves, spike-event timelines.

### Critical bug discovered and fixed
Political headlines are sparse — many calendar days have zero political
tags. The initial implementation left `pol_*` columns as NaN on those
days, so `dropna()` collapsed the Political-only and Combined cells to
**29 rows**. Earlier apparent findings (e.g. `GLD Political AUC = 0.71`)
were sample-size artefacts, not real signal.

**Fix:** impute missing-stream days as neutral sentiment (0) *before*
computing lag features. Every cell now trains on 182 aligned rows.

### Post-fix 2×3 matrices (AUC, best model per cell)

**σ = 2.0 (proposal spec, ~14% spike rate):**

| AUC | Financial only | Political only | Combined |
|-----|---------------:|---------------:|---------:|
| BTC |          0.608 |          0.538 |    0.631 |
| GLD |          0.464 |          0.546 |    0.563 |

**σ = 1.5 (robustness check, ~20% spike rate):**

| AUC | Financial only | Political only | Combined |
|-----|---------------:|---------------:|---------:|
| BTC |          0.623 |          0.490 |    0.569 |
| GLD |          0.537 |          0.447 |    0.512 |

### macOS-specific fixes
- XGBoost needs `libomp` on macOS → `brew install libomp` + force
  reinstall to link against it.
- Broadened `except ImportError` to `except Exception` so missing libomp
  degrades XGBoost gracefully instead of crashing the whole script.

---

## Phase 4 — Deeper Analysis (`deeper_analysis.py`)

Addresses the four questions reviewers ask once they've seen the 2×3 matrix.

### Question 1: Does sentiment add value beyond autoregressive price features?
Added **price-lag features** (past returns at lags 1/2/3, rolling volatility
at 5/10/30 days) and ran a three-way ablation: price-only, sentiment-only,
price+sentiment.

```
AUC (best model per cell)     Price+Sent   Price only   Sentiment only
BTC                              0.582        0.640         0.674
GLD                              0.585        0.591         0.563
```

**Finding:** For BTC, sentiment-only (0.674) beats price-only (0.640). But
combining them makes things worse (0.582) — a classic small-data overfit.
For GLD, no feature set exceeds 0.60.

**Side fix:** GLD weekend NaN gaps were collapsing the price-only cell to
~45 rows. Forward-filling GLD returns across weekends (weekend "state" ==
last Friday state) restored full 178-sample support.

### Question 2: Can we predict volatility *magnitude*?
Ridge regression on `|return|` produced **negative R² for every
configuration** (BTC: −0.91 to −3.74, GLD: −0.54 to −2.25). All models
do worse than predicting the mean.

**Finding:** Magnitude is not forecastable from these features at daily
frequency with 178 samples — consistent with efficient-market expectations.
Reported as an honest null result.

### Question 3: Are the Granger results statistically valid?
Baseline Granger tests assume stationarity; we didn't check. Added an
ADF (augmented Dickey-Fuller) pre-check with automatic differencing of
non-stationary series.

**Finding:** After stationarity correction, exactly one cell clears
significance:

```
BTC_abs_return  <-  political sentiment,  lag 5,  p = 0.0107
```

Political sentiment Granger-causes BTC volatility at a 5-day lag — the
single most rigorous statistical finding in the project. Counter to the
original hypothesis (we expected political → GLD). Likely explained by
the 2024 US-election cycle driving both political news and crypto
volatility via regulatory uncertainty.

### Question 4: Which features drive the predictions?
SHAP summary plots on the best XGBoost cell per asset. Outputs:
`artifacts/plots/shap_btc.png`, `artifacts/plots/shap_gld.png`.

Also added calibration curves (`calibration.png`) to check that predicted
probabilities track observed spike frequencies.

---

## Phase 5 — Consolidated Findings

### The headline result (one paragraph)

> News sentiment predicts Bitcoin volatility spikes with out-of-sample
> AUC 0.67, exceeding a price-autoregressive baseline of 0.64.
> Political-news sentiment Granger-causes Bitcoin volatility at a 5-day
> lag (p = 0.011). Gold volatility is not predicted by sentiment in any
> configuration. Volatility magnitude remains unpredictable via ridge
> regression (R² < 0), consistent with efficient-market expectations at
> daily frequency.

### Limitations worth stating up-front
1. **Small sample** — 178 rows (BTC) / 96 rows (GLD). Directionally
   informative, not conclusive.
2. **Labels are bootstrapped**, not human-annotated. Fine-tuned model
   learns the zero-shot labelling scheme, not ground truth sentiment.
3. **Single time window** covers an election cycle → findings may be
   regime-specific. Replication on Jan–Jun 2024 would strengthen claims.
4. **Headlines only** — full articles might add nuance, but scope was
   deliberately limited.
5. **"Financial" sentiment is really crypto sentiment** — 82.8% of
   financial-tagged headlines are from crypto-native sources (CoinDesk,
   CoinTelegraph, etc.). This partly explains why it predicts BTC but
   not GLD.

---

## Artifacts and Deliverables

### Repository layout
```
finetune_financialbert.py    # Phase 2 — sentiment pipeline
analyze_and_model.py         # Phase 3 — baseline 2x3 matrix + sweep
deeper_analysis.py           # Phase 4 — ablation, ridge, SHAP, ADF-Granger
build_slides.js              # Phase 3 — data-overview slide generator
README.md                    # Overview, results, how to run
PROJECT_LOG.md               # This file
```

### GitHub releases
- **v0.2.0-finbert** — current release. Fine-tuned model + all analysis
  artefacts and plots (392 MB zip).
- v0.1.0-finbert (deprecated, deleted) — initial model-only release.

### Key artefacts (gitignored, regenerate locally or download release)
```
artifacts/
├── finbert-ft-best/                       # fine-tuned model
├── daily_sentiment.csv                    # 183 days × 15 features
├── merged_daily_sig{2p0,1p5}.csv          # merged dataset
├── results_matrix_{auc,f1}_sig*.csv       # the 2x3 matrices
├── ablation_price_vs_sentiment.csv        # Phase 4 key result
├── ridge_magnitude.csv
├── granger_with_adf.csv                   # stationarity-aware Granger
├── slides_data_overview.pptx              # 7-slide data deck
└── plots/                                 # ~15 PNG figures
```

### Plot inventory
Data overview: `price_vs_sentiment.png`
Per-σ: `correlation_heatmap_sig*.png`, `granger_heatmap_sig*.png`,
`spike_timeline_sig*.png`, `feature_importance_{btc,gld}_sig*.png`,
`model_comparison_{btc,gld}_sig*.png`, `roc_sig*_{btc,gld}.png`.
Deeper analysis: `shap_{btc,gld}.png`, `calibration.png`.

---

## Commit Timeline (Highlights)

| Commit | Summary |
|---|---|
| `ecf0a37` | Initial dataset upload |
| `71149e4` | Add FinancialBERT weak-supervision fine-tuning pipeline |
| `baa0458` | Add Apple Silicon (MPS) support and tune for M5 Pro / 48GB |
| `1660fca` | Fix pandas 2.x groupby().apply() column loss |
| `4923623` | Handle dropped classes and HF datasets stratification |
| `bfe6323` | Drop removed `use_mps_device` arg from TrainingArguments |
| `6e3b5fb` | Support transformers 5.x Trainer `processing_class` rename |
| `4b10c6d` | Document fine-tuning ablation results and add .gitignore |
| `5c236fe` | Add analyze_and_model.py — merging, tests, and the 2x3 matrix |
| `905e0c0` | Make XGBoost failure non-fatal |
| `12a3b1a` | Fix sparse-stream NaN trap and sweep spike sigmas |
| `d7a34a7` | Add Granger heatmap, ROC curves, and spike timeline plots |
| `0856ea8` | Add data-overview slide deck generator |
| `999c206` | Add deeper_analysis.py: ablation, ridge, SHAP, ADF-Granger |

---

## What Would Be Next (Out of Scope for This Project)

- Replicate on Jan–Jun 2024 to test regime-specificity.
- Collect full article bodies (not just titles) and re-score sentiment.
- Longer time window (2+ years) to unlock proper feature-combining
  without overfitting the 178-sample constraint.
- SHAP-guided feature selection: keep only the top-k SHAP-ranked
  features from sentiment + price, then re-test combined model.
- Trading simulation: convert spike predictions into position sizing
  and evaluate whether signal survives transaction costs.
