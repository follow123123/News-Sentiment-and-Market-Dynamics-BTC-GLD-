"""
Fine-tune FinancialBERT using weak supervision (Path A).

Pipeline:
  1. Load the 21K normalized news headlines.
  2. Take a stratified sample (~3000 rows) across tag/source.
  3. Auto-label with a zero-shot model (BART-MNLI) to create pseudo-labels.
  4. Filter low-confidence labels.
  5. Fine-tune FinancialBERT on the pseudo-labeled set.
  6. Evaluate: fine-tuned model vs. off-the-shelf FinancialBERT on a held-out slice.
  7. Score ALL 21K headlines with the best model and save daily aggregates.

Run:
    pip install transformers datasets torch scikit-learn pandas numpy accelerate
    python finetune_financialbert.py

Hardware note:
  - GPU strongly recommended. On CPU, zero-shot labeling of 3K rows takes ~30 min;
    fine-tuning 3 epochs takes ~1-2 hours. On a T4/A100, both finish in minutes.
  - If you have no GPU, reduce SAMPLE_SIZE to 1000 and EPOCHS to 2.
"""

from __future__ import annotations

import os
import random
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from datasets import ClassLabel, Dataset
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, f1_score)
from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                          Trainer, TrainingArguments, pipeline)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).parent
NEWS_CSV = PROJECT_DIR / "normalized_news_july_dec_2024.csv"
OUT_DIR = PROJECT_DIR / "artifacts"
OUT_DIR.mkdir(exist_ok=True)

BASE_MODEL = "ahmedrachid/FinancialBERT-Sentiment-Analysis"
ZERO_SHOT_MODEL = "facebook/bart-large-mnli"

SEED = 42
SAMPLE_SIZE = 5000          # M5 Pro / 48GB can easily handle more pseudo-labels
CONFIDENCE_THRESHOLD = 0.65 # drop weak pseudo-labels below this
EPOCHS = 4                  # small model, plenty of headroom — watch val loss
BATCH_SIZE = 64             # unified memory on M5 Pro: no issue
LR = 2e-5
MAX_LEN = 64                # headlines are short
FREEZE_LOWER_LAYERS = 4     # with more data we can unfreeze more layers

LABELS = ["negative", "neutral", "positive"]
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

# Descriptive hypothesis strings for zero-shot — wording matters a lot
ZERO_SHOT_HYPOTHESES = {
    "positive": "this headline signals positive news for financial markets",
    "neutral":  "this headline is neutral or factual with no market impact",
    "negative": "this headline signals negative news for financial markets",
}

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# Device selection: CUDA > MPS (Apple Silicon) > CPU
# HF pipeline accepts: 0 (cuda), "mps", or -1 (cpu)
if torch.cuda.is_available():
    DEVICE = 0
    DEVICE_NAME = "cuda"
elif torch.backends.mps.is_available():
    DEVICE = "mps"
    DEVICE_NAME = "mps"
    # MPS fallback for ops not yet implemented in Metal
    os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
else:
    DEVICE = -1
    DEVICE_NAME = "cpu"
print(f"[cfg] device: {DEVICE_NAME}")


# ---------------------------------------------------------------------------
# Step 1 — Load news
# ---------------------------------------------------------------------------
def load_news() -> pd.DataFrame:
    df = pd.read_csv(NEWS_CSV)
    df["title"] = df["title"].astype(str).str.strip()
    df = df[df["title"].str.len() > 10].copy()          # drop junk
    df = df.drop_duplicates(subset="title").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"]).dt.tz_localize(None).dt.date
    print(f"[load] {len(df):,} unique headlines")
    print(df["tags"].value_counts().head())
    return df


# ---------------------------------------------------------------------------
# Step 2 — Stratified sample across tag/source
# ---------------------------------------------------------------------------
def stratified_sample(df: pd.DataFrame, n: int) -> pd.DataFrame:
    # Group by tag so both "financial" and "political" are represented.
    # Use groupby().sample() — works across pandas versions and preserves columns.
    tag_counts = df["tags"].value_counts()
    per_group = max(1, n // max(1, len(tag_counts)))
    parts = []
    for tag, count in tag_counts.items():
        take = min(count, per_group)
        parts.append(df[df["tags"] == tag].sample(take, random_state=SEED))
    sampled = pd.concat(parts, ignore_index=True)
    if len(sampled) > n:
        sampled = sampled.sample(n, random_state=SEED).reset_index(drop=True)
    print(f"[sample] {len(sampled)} rows; tag distribution:")
    print(sampled["tags"].value_counts())
    return sampled


# ---------------------------------------------------------------------------
# Step 3 — Zero-shot pseudo-labeling
# ---------------------------------------------------------------------------
def pseudo_label(texts: list[str]) -> tuple[list[str], list[float]]:
    clf = pipeline(
        "zero-shot-classification",
        model=ZERO_SHOT_MODEL,
        device=DEVICE,
    )
    hyp_list = [ZERO_SHOT_HYPOTHESES[l] for l in LABELS]
    hyp_to_label = {ZERO_SHOT_HYPOTHESES[l]: l for l in LABELS}

    labels_out, confs_out = [], []
    BATCH = 32
    for i in range(0, len(texts), BATCH):
        batch = texts[i : i + BATCH]
        outputs = clf(batch, candidate_labels=hyp_list, multi_label=False)
        if isinstance(outputs, dict):      # single-item edge case
            outputs = [outputs]
        for out in outputs:
            top_hyp = out["labels"][0]
            labels_out.append(hyp_to_label[top_hyp])
            confs_out.append(float(out["scores"][0]))
        if (i // BATCH) % 10 == 0:
            print(f"[zsl] {i + len(batch):>5}/{len(texts)}")
    return labels_out, confs_out


# ---------------------------------------------------------------------------
# Step 4 — Tokenize and build train/val/test splits
# ---------------------------------------------------------------------------
def build_datasets(df_labeled: pd.DataFrame, tokenizer):
    def tok(batch):
        return tokenizer(
            batch["title"],
            padding="max_length",
            truncation=True,
            max_length=MAX_LEN,
        )

    df_labeled = df_labeled.copy()

    # If a class has too few samples to stratify across 3 splits, drop it
    # and warn. (Zero-shot often underpredicts "neutral" on news headlines.)
    MIN_PER_CLASS = 20
    counts = df_labeled["pseudo_label"].value_counts()
    tiny = counts[counts < MIN_PER_CLASS].index.tolist()
    if tiny:
        print(f"[build] dropping classes with <{MIN_PER_CLASS} samples: {tiny}")
        df_labeled = df_labeled[~df_labeled["pseudo_label"].isin(tiny)].copy()

    active_labels = [l for l in LABELS if l not in tiny]
    active_l2i = {l: i for i, l in enumerate(active_labels)}
    df_labeled["label"] = df_labeled["pseudo_label"].map(active_l2i)

    ds = Dataset.from_pandas(df_labeled[["title", "label"]], preserve_index=False)
    # Cast label → ClassLabel so HF datasets can stratify on it
    ds = ds.cast_column("label", ClassLabel(names=active_labels))
    ds = ds.map(tok, batched=True)

    split = ds.train_test_split(test_size=0.2, seed=SEED,
                                stratify_by_column="label")
    val_test = split["test"].train_test_split(test_size=0.5, seed=SEED,
                                              stratify_by_column="label")
    print(f"[build] active classes: {active_labels}")
    return split["train"], val_test["train"], val_test["test"], active_labels


# ---------------------------------------------------------------------------
# Step 5 — Fine-tune
# ---------------------------------------------------------------------------
def freeze_lower_layers(model, n: int):
    if n <= 0:
        return
    frozen = 0
    for name, p in model.named_parameters():
        if "encoder.layer." in name:
            layer_idx = int(name.split("encoder.layer.")[1].split(".")[0])
            if layer_idx < n:
                p.requires_grad = False
                frozen += 1
        if "embeddings" in name:
            p.requires_grad = False
            frozen += 1
    print(f"[freeze] froze {frozen} tensors (layers < {n} + embeddings)")


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = logits.argmax(axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
    }


def fine_tune(train_ds, val_ds, active_labels):
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    id2label = {i: l for i, l in enumerate(active_labels)}
    label2id = {l: i for i, l in id2label.items()}
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=len(active_labels),
        id2label=id2label,
        label2id=label2id,
        ignore_mismatched_sizes=True,
    )
    freeze_lower_layers(model, FREEZE_LOWER_LAYERS)

    args = TrainingArguments(
        output_dir=str(OUT_DIR / "finbert-ft"),
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE * 2,
        learning_rate=LR,
        warmup_ratio=0.1,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        logging_steps=25,
        save_total_limit=1,
        seed=SEED,
        report_to="none",
        # Mac-friendly: fp16 is CUDA-only. MPS uses fp32 reliably.
        fp16=torch.cuda.is_available(),
        # Avoid spawning workers on Mac (fork issues with MPS)
        dataloader_num_workers=0,
        # Note: HF Trainer auto-detects MPS on Apple Silicon (>= transformers 4.30)
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        compute_metrics=compute_metrics,
    )
    trainer.train()
    trainer.save_model(str(OUT_DIR / "finbert-ft-best"))
    tokenizer.save_pretrained(str(OUT_DIR / "finbert-ft-best"))
    return trainer, tokenizer


# ---------------------------------------------------------------------------
# Step 6 — Evaluate vs. off-the-shelf FinancialBERT
# ---------------------------------------------------------------------------
def evaluate_baseline(test_df: pd.DataFrame, active_labels):
    """Score the test set with out-of-the-box FinancialBERT."""
    clf = pipeline(
        "sentiment-analysis",
        model=BASE_MODEL,
        tokenizer=BASE_MODEL,
        device=DEVICE,
        truncation=True,
        max_length=MAX_LEN,
    )
    l2i = {l: i for i, l in enumerate(active_labels)}
    # Pick a fallback class for labels the baseline returns that we dropped
    fallback = l2i.get("neutral", 0)
    preds_raw = clf(test_df["title"].tolist(), batch_size=32)
    preds = [p["label"].lower() for p in preds_raw]
    preds_id = [l2i.get(p, fallback) for p in preds]
    true_id = test_df["pseudo_label"].map(l2i).tolist()
    return np.array(true_id), np.array(preds_id)


def report_block(name, y_true, y_pred, active_labels):
    print(f"\n===== {name} =====")
    print(classification_report(
        y_true, y_pred,
        labels=list(range(len(active_labels))),
        target_names=active_labels,
        digits=3, zero_division=0,
    ))
    print("confusion matrix (rows=true, cols=pred):")
    print(pd.DataFrame(
        confusion_matrix(y_true, y_pred, labels=list(range(len(active_labels)))),
        index=active_labels, columns=active_labels,
    ))


# ---------------------------------------------------------------------------
# Step 7 — Score all 21K headlines + daily aggregates
# ---------------------------------------------------------------------------
def score_all(df_all: pd.DataFrame, model_dir: str) -> pd.DataFrame:
    clf = pipeline(
        "sentiment-analysis",
        model=model_dir,
        tokenizer=model_dir,
        device=DEVICE,
        truncation=True,
        max_length=MAX_LEN,
        top_k=None,                 # return full prob distribution
    )
    titles = df_all["title"].tolist()
    out = clf(titles, batch_size=64)

    # Convert each prediction into a signed score in [-1, 1]
    scores = []
    best_labels = []
    for dist in out:
        probs = {d["label"].lower(): d["score"] for d in dist}
        s = probs.get("positive", 0.0) - probs.get("negative", 0.0)
        scores.append(s)
        best_labels.append(max(probs, key=probs.get))

    df_all = df_all.copy()
    df_all["sent_score"] = scores
    df_all["sent_label"] = best_labels
    return df_all


def daily_aggregate(df_scored: pd.DataFrame) -> pd.DataFrame:
    df_scored = df_scored.copy()
    df_scored["is_fin"] = df_scored["tags"].astype(str).str.contains("financial")
    df_scored["is_pol"] = df_scored["tags"].astype(str).str.contains("political")
    df_scored["is_pos"] = (df_scored["sent_label"] == "positive").astype(int)
    df_scored["is_neg"] = (df_scored["sent_label"] == "negative").astype(int)

    def _agg(subset: pd.DataFrame, prefix: str) -> pd.DataFrame:
        g = subset.groupby("date")
        out = pd.DataFrame({
            f"{prefix}sent_mean": g["sent_score"].mean(),
            f"{prefix}sent_var":  g["sent_score"].var(ddof=0),
            f"{prefix}headline_count": g.size(),
            f"{prefix}pos_share": g["is_pos"].mean(),
            f"{prefix}neg_share": g["is_neg"].mean(),
        })
        return out

    all_daily = _agg(df_scored,                       "all_")
    fin_daily = _agg(df_scored[df_scored.is_fin],     "fin_")
    pol_daily = _agg(df_scored[df_scored.is_pol],     "pol_")

    daily = all_daily.join(fin_daily, how="outer").join(pol_daily, how="outer")
    daily.index = pd.to_datetime(daily.index)
    daily = daily.sort_index()
    return daily


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    # --- 1. Load ---
    news = load_news()

    # --- 2. Sample + 3. Pseudo-label ---
    sample = stratified_sample(news, SAMPLE_SIZE)
    labels, confs = pseudo_label(sample["title"].tolist())
    sample["pseudo_label"] = labels
    sample["pseudo_conf"] = confs

    print("\n[pseudo] label distribution (all):")
    print(sample["pseudo_label"].value_counts())

    # Filter low-confidence pseudo-labels (noise reduction)
    clean = sample[sample["pseudo_conf"] >= CONFIDENCE_THRESHOLD].copy()
    print(f"\n[filter] kept {len(clean)}/{len(sample)} "
          f"with conf ≥ {CONFIDENCE_THRESHOLD}")
    print(clean["pseudo_label"].value_counts())

    clean.to_csv(OUT_DIR / "pseudo_labeled_sample.csv", index=False)

    # --- 4. Datasets ---
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    train_ds, val_ds, test_ds, active_labels = build_datasets(clean, tokenizer)
    print(f"[split] train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")

    # --- 5. Fine-tune ---
    trainer, _ = fine_tune(train_ds, val_ds, active_labels)

    # --- 6. Evaluate on held-out test set ---
    test_df = pd.DataFrame({
        "title": test_ds["title"],
        "pseudo_label": [active_labels[i] for i in test_ds["label"]],
    })

    # Fine-tuned predictions
    ft_preds = trainer.predict(test_ds)
    y_true_ft = ft_preds.label_ids
    y_pred_ft = ft_preds.predictions.argmax(axis=-1)
    report_block("Fine-tuned FinancialBERT", y_true_ft, y_pred_ft, active_labels)

    # Baseline predictions
    y_true_b, y_pred_b = evaluate_baseline(test_df, active_labels)
    report_block("Baseline (off-the-shelf FinancialBERT)", y_true_b, y_pred_b,
                 active_labels)

    # Ablation summary
    ablation = pd.DataFrame({
        "model": ["FinancialBERT (baseline)", "FinancialBERT (fine-tuned)"],
        "accuracy": [accuracy_score(y_true_b, y_pred_b),
                     accuracy_score(y_true_ft, y_pred_ft)],
        "f1_macro": [f1_score(y_true_b, y_pred_b, average="macro"),
                     f1_score(y_true_ft, y_pred_ft, average="macro")],
    })
    print("\n===== ABLATION =====")
    print(ablation.to_string(index=False))
    ablation.to_csv(OUT_DIR / "ablation_results.csv", index=False)

    # --- 7. Score full corpus + daily aggregates ---
    print("\n[score] running fine-tuned model on all headlines...")
    best_model_dir = str(OUT_DIR / "finbert-ft-best")
    news_scored = score_all(news, best_model_dir)
    news_scored.to_csv(OUT_DIR / "news_scored.csv", index=False)

    daily = daily_aggregate(news_scored)
    daily.to_csv(OUT_DIR / "daily_sentiment.csv")
    print(f"[done] wrote {OUT_DIR/'daily_sentiment.csv'} "
          f"({len(daily)} days × {daily.shape[1]} features)")

    print("\nNext: merge daily_sentiment.csv with BTC/GLD daily OHLCV, "
          "engineer lag features, and train LogReg/RF/XGBoost per the proposal.")


if __name__ == "__main__":
    main()
