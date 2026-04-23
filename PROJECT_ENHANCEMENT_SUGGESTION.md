# Project Enhancement Suggestions

Based on the updated prompt and project analysis, here are comprehensive suggestions for your 10-minute presentation.

---

## Presentation Essentials (Address These Directly)

### 1. What are you interested in and why?

**Key Points:**
- Investigate whether news sentiment predicts crypto/commodity volatility
- Bitcoin trades 24/7, Gold only weekdays — different market dynamics
- FinancialBERT exists but was never fine-tuned on market-framed sentiment hypotheses
- Hypothesis: Sentiment from financial news should predict BTC better than GLD (corpus is crypto-heavy)

---

### 2. How do you collect data and ensure data is suitable?

**Key Points:**
- 21,005 headlines from 50+ sources (July–December 2024)
- Tags: financial (82.8%), political (7.9%), both (9.0%)
- BTC: 4-hour OHLCV → resampled to 183 daily rows
- GLD: 128 daily rows (weekends excluded)
- Alignment: inner-join on date — ensures valid comparison

**Visualization:** Dataset overview card (slide 2 in existing deck)

---

### 3. What methods applied, and interesting findings?

**Methods:**
- Pseudo-labeling with BART-MNLI (zero-shot)
- Fine-tune FinancialBERT (bottom 4 layers frozen)
- Walk-forward cross-validation
- Granger causality with ADF correction

**Key Findings:**
- Fine-tuned model: **79% accuracy** (vs. 52.6% baseline)
- Best BTC prediction: **AUC 0.631** (Combined sentiment, σ=2.0)
- Best GLD prediction: **AUC 0.563** — near chance
- Sentiment-only for BTC: **AUC 0.674** > price-only (0.640)
- Political sentiment → BTC volatility at lag 5 (Granger, p=0.0107)

---

### 4. How have you leveraged foundation models?

**Key Points:**
- BART-MNLI: Zero-shot labeling for pseudo-labels (no human annotations needed)
- FinancialBERT: Pre-trained on finance corpus, fine-tuned for sentiment
- Foundation models enable weak supervision at scale

---

## Timing Allocation (10 Minutes Total)

| Section | Time | Slides |
|---|---|---|
| 1. Intro & Motivation | 1 min | 1 |
| 2. Data Collection & Preprocessing | 1.5 min | 2–3 |
| 3. Sentiment Analysis & Modeling | 2.5 min | 4–6 |
| 4. Correlation & Visualization | 2 min | 7–8 |
| 5. Findings & Conclusions | 1 min | 9 |
| **Total Presentation** | **8 min** | |
| Q&A | 2 min | — |

---

## Section-by-Section Suggestions

### Section 1: Intro & Motivation (~1 min)

**Add:**
- Research question slide
- Why this matters: Sentiment as a leading indicator

**Visual:**
- Icon-based motivation (💡 → 📰 → 📈)

---

### Section 2: Data Collection & Preprocessing (~1.5 min)

**Already Complete:** Slides 1–3 in existing deck

**Enhance:**
- Add slide showing data pipeline flow
- Highlight: 21K → 20.9K (deduped) → 2.9K (filtered)

---

### Section 3: Sentiment Analysis & Modeling (~2.5 min)

**Add:**

- **Model Comparison Table**
  | Model | Accuracy | F1 (macro) |
  |---|---|---|
  | FinancialBERT (off-the-shelf) | 52.6% | 0.423 |
  | **FinancialBERT (fine-tuned)** | **79.0%** | **0.790** |

- **Confusion Matrix Heatmap**
  - Show prediction vs. ground truth
  - Annotate with counts

- **Pipeline Visualization**
  - Step 1: Zero-shot labeling
  - Step 2: Filtering (≥0.65 confidence)
  - Step 3: Fine-tuning
  - Step 4: Scoring all 21K
  - Step 5: Daily aggregation

**Timing Note:** Spend adequate time here — this is where foundation models were leveraged

---

### Section 4: Correlation & Visualization (~2 min)

**Add:**

- **AUC Matrix Heatmap (2×3)**
  | Asset | Financial | Political | Combined |
  |---|---|---|---|
  | BTC | 0.608 | 0.538 | **0.631** |
  | GLD | 0.464 | 0.546 | 0.563 |

- **Correlation Heatmap**
  - Key rho-values annotated

- **Ablation Results**
  | Feature Set | BTC AUC |
  |---|---|
  | Price-only | 0.640 |
  | Sentiment-only | **0.674** |
  | Price + Sentiment | 0.582 |

- **Granger Causality Highlight**
  - `BTC_abs_return ← political sentiment` (lag 5, p = 0.0107)

---

### Section 5: Findings & Conclusions (~1 min)

**Key Takeaways:**

1. Modest but real sentiment signal for BTC (AUC > 0.6)
2. Political news predicts crypto volatility (unique finding)
3. Gold doesn't respond to headline sentiment
4. Sentiment carries unique information beyond price alone

**Visual:**
- Impactful closing slide with key numbers

---

## Visualization Ideas Summary

| Visualization | Section | Timing |
|---|---|---|
| Dataset overview cards | 2 | 30 sec |
| Model comparison table | 3 | 30 sec |
| Confusion matrix heatmap | 3 | 20 sec |
| Pipeline flow diagram | 3 | 30 sec |
| AUC matrix heatmap | 4 | 30 sec |
| Correlation heatmap | 4 | 30 sec |
| Ablation bar chart | 4 | 30 sec |
| Granger results table | 4 | 30 sec |
| Closing summary slide | 5 | 1 min |

---

## Presentation Polish Tips

### Color Coding (Consistent with Existing Deck)

| Element | Hex |
|---|---|
| Primary (BTC/Financial) | #065A82 |
| Secondary (GLD/Political) | #1C7293 |
| Accent (gold pop) | #F0A202 |
| Dark background | #21295C |
| Light tint | #E8F1F7 |

### Icons to Use

- 📰 News/Headlines
- 📈 Bitcoin
- 🪙 Gold (GLD)
- 🧠 Model/Foundation Model
- 🔗 Correlation/Relationship
- ✅ Positive finding
- ⚠️ Limitation

### Layout Cues

- Dark bookend slides (first/last) with vertical accent bar
- Light content slides with consistent headers
- Footer with section tag + slide number

---

## Summary Checklist

- [ ] Add research question slide (Section 1)
- [ ] Add data pipeline flow (Section 2)
- [ ] Model comparison table with metrics (Section 3)
- [ ] Confusion matrix heatmap (Section 3)
- [ ] Pipeline visualization (Section 3)
- [ ] AUC matrix heatmap (2×3) (Section 4)
- [ ] Correlation heatmap (Section 4)
- [ ] Ablation results bar chart (Section 4)
- [ ] Granger causality table (Section 4)
- [ ] Closing slide with key takeaways (Section 5)
- [ ] Timing: 8 min presentation + 2 min Q&A