// Build the full presentation deck for the News Sentiment & Market Dynamics project.
// Palette: Ocean Gradient (finance feel). Dark bookend slides + light content.

const pptxgen = require("pptxgenjs");
const path = require("path");
const fs = require("fs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5

// --- paths --------------------------------------------------------------------
const PLOTS_DIR = path.join(__dirname, "artifacts", "plots");

// --- palette -----------------------------------------------------------------
const C = {
  deep:    "065A82",   // primary
  teal:    "1C7293",   // secondary
  mid:     "21295C",   // accent / dark bg
  ice:     "E8F1F7",   // light bg tint
  line:    "9DB4C0",   // subtle rule
  black:   "0B1B26",
  white:   "FFFFFF",
  text:    "1F2A37",
  muted:   "5C6B7A",
  accent:  "F0A202",   // warm gold pop
  pos:     "2E7D32",   // green for positive
  neg:     "C62828",   // red for negative
};

const F = { head: "Georgia", body: "Calibri" };

// ---------------------------------------------------------------------------
// Slide 1 — Title (Intro & Motivation)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.mid };
  s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: C.accent } });

  s.addText("THE RESEARCH", {
    x: 0.9, y: 1.9, w: 8, h: 0.5,
    fontFace: F.body, fontSize: 14, color: C.accent, bold: true, charSpacing: 8,
  });
  s.addText("News Sentiment &\nMarket Dynamics", {
    x: 0.9, y: 2.4, w: 11, h: 2.2,
    fontFace: F.head, fontSize: 54, color: C.white, bold: true,
    paraSpaceAfter: 0,
  });
  s.addText("Predicting Bitcoin and Gold volatility from headline sentiment", {
    x: 0.9, y: 4.7, w: 11, h: 0.6,
    fontFace: F.body, fontSize: 20, color: C.ice, italic: true,
  });

  // Decorative stat callouts at bottom
  const stats = [
    { n: "21,005", l: "news headlines" },
    { n: "3",      l: "aligned datasets" },
    { n: "183",    l: "daily observations" },
  ];
  stats.forEach((st, i) => {
    const x = 0.9 + i * 4.1;
    s.addText(st.n, {
      x, y: 5.8, w: 3.8, h: 0.7,
      fontFace: F.head, fontSize: 36, color: C.accent, bold: true,
    });
    s.addText(st.l, {
      x, y: 6.45, w: 3.8, h: 0.4,
      fontFace: F.body, fontSize: 13, color: C.ice, charSpacing: 2,
    });
  });
}

// ---------------------------------------------------------------------------
// Slide 2 — Research Question (NEW - Section 1)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Research Question", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("Can news sentiment predict cryptocurrency and commodity volatility?", {
    x: 0.6, y: 1.05, w: 12.2, h: 0.5,
    fontFace: F.body, fontSize: 18, color: C.text, italic: true,
  });

  // Three cards for motivation
  const cards = [
    { t: "Why Bitcoin?",       b: "24/7 market, high volatility, sentiment-driven community" },
    { t: "Why Gold?",         b: "Safe-haven asset, responds to macro/political events" },
    { t: "Foundation Models", b: "FinancialBERT + BART-MNLI for weak supervision at scale" },
  ];
  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.2;
    s.addShape("roundRect", {
      x, y: 1.9, w: 3.9, h: 3.2,
      fill: { color: C.ice },
      line: { color: C.line, width: 0.5 },
      rectRadius: 0.1,
    });
    s.addShape("rect", {
      x, y: 1.9, w: 3.9, h: 0.12,
      fill: { color: i === 0 ? C.deep : i === 1 ? C.accent : C.teal },
    });
    s.addText(c.t, {
      x: x + 0.25, y: 2.15, w: 3.4, h: 0.4,
      fontFace: F.body, fontSize: 16, color: C.mid, bold: true,
    });
    s.addText(c.b, {
      x: x + 0.25, y: 2.6, w: 3.4, h: 2.2,
      fontFace: F.body, fontSize: 13, color: C.text,
    });
  });

  // Hypothesis callout
  s.addShape("roundRect", {
    x: 0.6, y: 5.4, w: 12.2, h: 1.4,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("HYPOTHESIS", {
    x: 0.8, y: 5.55, w: 3, h: 0.3,
    fontFace: F.body, fontSize: 11, color: C.accent, bold: true, charSpacing: 5,
  });
  s.addText("Sentiment from financial news should predict BTC better than GLD\n(because our corpus is heavily crypto-native)", {
    x: 0.8, y: 5.9, w: 11.5, h: 0.8,
    fontFace: F.body, fontSize: 15, color: C.white,
  });
}

// ---------------------------------------------------------------------------
// Slide 3 — Three datasets at a glance
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Three datasets, one aligned window", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("All three cover July 1 – December 30, 2024 and merge on daily date.", {
    x: 0.6, y: 1.05, w: 12.2, h: 0.4,
    fontFace: F.body, fontSize: 15, color: C.muted, italic: true,
  });

  const cards = [
    {
      title: "News headlines",
      big: "21,005",
      unit: "headlines",
      body: "50+ sources.\nCrypto, financial,\npolitical coverage.",
      accent: C.deep,
    },
    {
      title: "Bitcoin prices",
      big: "1,098",
      unit: "4-hour candles",
      body: "OHLCV resampled\nto 183 daily rows.\n24/7 market.",
      accent: C.teal,
    },
    {
      title: "Gold (GLD ETF)",
      big: "128",
      unit: "trading days",
      body: "Daily OHLCV.\nWeekdays only —\nmarket closed weekends.",
      accent: C.accent,
    },
  ];

  cards.forEach((c, i) => {
    const x = 0.6 + i * 4.2;
    const w = 3.9;
    s.addShape("roundRect", {
      x, y: 1.7, w, h: 4.8,
      fill: { color: C.ice },
      line: { color: C.line, width: 0.5 },
      rectRadius: 0.1,
    });
    s.addShape("rect", {
      x, y: 1.7, w, h: 0.18,
      fill: { color: c.accent }, line: { width: 0 },
    });
    s.addText(c.title.toUpperCase(), {
      x: x + 0.3, y: 2.05, w: w - 0.6, h: 0.4,
      fontFace: F.body, fontSize: 12, color: c.accent,
      bold: true, charSpacing: 6,
    });
    s.addText(c.big, {
      x: x + 0.3, y: 2.5, w: w - 0.6, h: 1.1,
      fontFace: F.head, fontSize: 54, color: C.mid, bold: true,
    });
    s.addText(c.unit, {
      x: x + 0.3, y: 3.6, w: w - 0.6, h: 0.4,
      fontFace: F.body, fontSize: 14, color: C.muted, italic: true,
    });
    s.addText(c.body, {
      x: x + 0.3, y: 4.15, w: w - 0.6, h: 2.2,
      fontFace: F.body, fontSize: 14, color: C.text,
      paraSpaceAfter: 4,
    });
  });

  s.addShape("line", {
    x: 0.6, y: 6.9, w: 12.2, h: 0, line: { color: C.line, width: 0.75 },
  });
  s.addText("Source: public APIs (crypto aggregators, yfinance) + curated news corpus",
    { x: 0.6, y: 6.98, w: 12.2, h: 0.35,
      fontFace: F.body, fontSize: 11, color: C.muted });
}

// ---------------------------------------------------------------------------
// Slide 4 — Data Pipeline Flow (ENHANCED - Section 2)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Data Pipeline", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("From raw data to modeling-ready daily features", {
    x: 0.6, y: 1.05, w: 12.2, h: 0.4,
    fontFace: F.body, fontSize: 15, color: C.muted, italic: true,
  });

  // Pipeline steps
  const steps = [
    { n: "1", t: "Raw News",     s: "21,005 headlines\nfrom 50+ sources" },
    { n: "2", t: "Dedupe & Clean", s: "20,939 unique\nheadlines" },
    { n: "3", t: "Zero-shot Label", s: "BART-MNLI\npseudo-labels" },
    { n: "4", t: "Filter",        s: "2,917 high-conf\n(≥0.65 threshold)" },
    { n: "5", t: "Fine-tune",    s: "FinancialBERT\n4 epochs" },
    { n: "6", t: "Score & Aggregate", s: "Daily sentiment\nfeatures" },
  ];
  const startX = 0.5, boxW = 2.0, gap = 0.15, top = 1.9;
  steps.forEach((st, i) => {
    const x = startX + i * (boxW + gap);
    s.addShape("roundRect", {
      x, y: top, w: boxW, h: 2.5,
      fill: { color: C.ice },
      line: { color: C.line, width: 0.5 },
      rectRadius: 0.1,
    });
    s.addShape("ellipse", {
      x: x + (boxW - 0.5) / 2, y: top + 0.2, w: 0.5, h: 0.5,
      fill: { color: C.deep }, line: { width: 0 },
    });
    s.addText(st.n, {
      x: x + (boxW - 0.5) / 2, y: top + 0.2, w: 0.5, h: 0.5,
      fontFace: F.head, fontSize: 18, color: C.white, bold: true,
      align: "center", valign: "middle",
    });
    s.addText(st.t, {
      x: x + 0.1, y: top + 0.8, w: boxW - 0.2, h: 0.4,
      fontFace: F.body, fontSize: 12, color: C.mid, bold: true, align: "center",
    });
    s.addText(st.s, {
      x: x + 0.1, y: top + 1.25, w: boxW - 0.2, h: 1.0,
      fontFace: F.body, fontSize: 11, color: C.muted, align: "center",
    });
    // Arrow
    if (i < steps.length - 1) {
      const ax = x + boxW + 0.02;
      s.addShape("triangle", {
        x: ax, y: top + 1.1, w: 0.1, h: 0.2,
        fill: { color: C.teal }, line: { width: 0 },
        rotate: 90,
      });
    }
  });

  // Output summary
  s.addShape("roundRect", {
    x: 0.6, y: 4.7, w: 12.2, h: 1.8,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("Output: 183 days × 15 sentiment features per stream", {
    x: 0.9, y: 4.85, w: 11.5, h: 0.5,
    fontFace: F.head, fontSize: 18, color: C.white, bold: true,
  });
  s.addText("Three parallel streams: all_* (all headlines), fin_* (financial-tagged), pol_* (political-tagged)", {
    x: 0.9, y: 5.4, w: 11.5, h: 0.8,
    fontFace: F.body, fontSize: 13, color: C.ice,
  });
}

// ---------------------------------------------------------------------------
// Slide 5 — News corpus breakdown
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("News corpus", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("21,005 headlines across 50+ sources, each tagged financial, political, or both",
    { x: 0.6, y: 1.05, w: 12.2, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.muted, italic: true });

  const tags = [
    { label: "Financial",            n: "17,397", pct: "82.8%", col: C.deep },
    { label: "Both fin + political", n: "1,881",  pct: "9.0%",  col: C.teal },
    { label: "Political only",       n: "1,661",  pct: "7.9%",  col: C.accent },
  ];
  s.addText("Tag distribution", {
    x: 0.6, y: 1.7, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true, charSpacing: 4,
  });
  tags.forEach((t, i) => {
    const y = 2.15 + i * 1.05;
    s.addShape("rect", {
      x: 0.6, y, w: 0.12, h: 0.8,
      fill: { color: t.col }, line: { width: 0 },
    });
    s.addText(t.label, {
      x: 0.9, y, w: 3, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.text, bold: true,
    });
    s.addText(t.n + "  •  " + t.pct, {
      x: 0.9, y: y + 0.4, w: 3, h: 0.4,
      fontFace: F.body, fontSize: 13, color: C.muted,
    });
    const barW = (parseFloat(t.pct) / 100) * 4.5;
    s.addShape("rect", {
      x: 3.9, y: y + 0.25, w: 4.5, h: 0.3,
      fill: { color: C.ice }, line: { width: 0 },
    });
    s.addShape("rect", {
      x: 3.9, y: y + 0.25, w: barW, h: 0.3,
      fill: { color: t.col }, line: { width: 0 },
    });
  });

  s.addShape("roundRect", {
    x: 0.6, y: 5.55, w: 5.5, h: 1.3,
    fill: { color: C.ice }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("NOTE", {
    x: 0.8, y: 5.65, w: 2, h: 0.3,
    fontFace: F.body, fontSize: 10, color: C.accent, bold: true, charSpacing: 5,
  });
  s.addText("Financial-tagged sources skew crypto-native.\nDownstream 'financial sentiment' primarily reflects\ncrypto-community sentiment, not broad capital markets.",
    { x: 0.8, y: 5.9, w: 5.2, h: 1.0,
      fontFace: F.body, fontSize: 12, color: C.text });

  s.addText("Top sources (headlines)", {
    x: 6.8, y: 1.7, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true, charSpacing: 4,
  });
  const sources = [
    ["coinotag",       1495],
    ["bitcoinsistemi", 1258],
    ["msnbc",          1125],
    ["coinpedia",      1103],
    ["cointelegraph",   987],
    ["coingape",        974],
    ["cointurken",      923],
    ["utoday",          882],
  ];
  const maxCount = sources[0][1];
  sources.forEach((row, i) => {
    const y = 2.15 + i * 0.55;
    const [name, n] = row;
    const isPolitical = name === "msnbc";
    s.addText(name, {
      x: 6.8, y, w: 2.1, h: 0.4,
      fontFace: F.body, fontSize: 13, color: C.text,
    });
    const barMax = 3.3;
    const barW = (n / maxCount) * barMax;
    s.addShape("rect", {
      x: 8.95, y: y + 0.07, w: barMax, h: 0.28,
      fill: { color: C.ice }, line: { width: 0 },
    });
    s.addShape("rect", {
      x: 8.95, y: y + 0.07, w: barW, h: 0.28,
      fill: { color: isPolitical ? C.accent : C.deep }, line: { width: 0 },
    });
    s.addText(String(n), {
      x: 12.35, y, w: 0.95, h: 0.4,
      fontFace: F.body, fontSize: 12, color: C.muted, align: "right",
    });
  });

  s.addShape("line", {
    x: 0.6, y: 6.9, w: 12.2, h: 0, line: { color: C.line, width: 0.75 },
  });
  s.addText("Gold bar = political-leaning outlet; blue = crypto/financial.",
    { x: 0.6, y: 6.98, w: 12.2, h: 0.35,
      fontFace: F.body, fontSize: 11, color: C.muted, italic: true });
}

// ---------------------------------------------------------------------------
// Slide 6 — Model Comparison with Graphs (Lecture 2: ROC + Confusion Matrix)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Sentiment Model Evaluation", {
    x: 0.6, y: 0.3, w: 12.2, h: 0.6,
    fontFace: F.head, fontSize: 28, color: C.mid, bold: true,
  });
  s.addText("Lecture 2: Model Evaluation Techniques — ROC Curve & Confusion Matrix", {
    x: 0.6, y: 0.85, w: 12.2, h: 0.35,
    fontFace: F.body, fontSize: 12, color: C.teal, italic: true,
  });

  // Embed ROC Curve (left) 
  const rocPath = path.join(PLOTS_DIR, "roc_curve.png");
  if (fs.existsSync(rocPath)) {
    s.addImage({
      x: 0.5, y: 1.4, w: 5.8, h: 4.5,
      path: rocPath,
    });
  } else {
    s.addText("ROC Curve ( Lecture 2 )", {
      x: 0.5, y: 2.5, w: 5.8, h: 2.0,
      fontFace: F.body, fontSize: 14, color: C.muted, align: "center",
    });
  }

  // Embed Confusion Matrix (right)
  const cmPath = path.join(PLOTS_DIR, "confusion_matrix.png");
  if (fs.existsSync(cmPath)) {
    s.addImage({
      x: 6.5, y: 1.4, w: 5.8, h: 4.5,
      path: cmPath,
    });
  } else {
    s.addText("Confusion Matrix ( Lecture 2 )", {
      x: 6.5, y: 2.5, w: 5.8, h: 2.0,
      fontFace: F.body, fontSize: 14, color: C.muted, align: "center",
    });
  }

  // Key metrics footer
  s.addShape("roundRect", {
    x: 0.5, y: 6.1, w: 12.2, h: 0.8,
    fill: { color: C.ice }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("Baseline AUC: 0.526  →  Fine-tuned AUC: 0.790  |  Accuracy: 52.6%  →  79.0%  |  F1: 0.423  →  0.790",
    { x: 0.7, y: 6.1, w: 11.8, h: 0.8,
      fontFace: F.body, fontSize: 13, color: C.text, valign: "middle", align: "center" });
}

// ---------------------------------------------------------------------------
// Slide 7 — Methods Summary (Section 3)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Methods Applied", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("Foundation models + statistical testing pipeline", {
    x: 0.6, y: 1.05, w: 12.2, h: 0.4,
    fontFace: F.body, fontSize: 15, color: C.muted, italic: true,
  });

  // Methods cards
  const methods = [
    { t: "Weak Supervision",     b: "BART-MNLI zero-shot labeling → pseudo-labels" },
    { t: "Fine-tuning",          b: "FinancialBERT (bottom 4 layers frozen, 4 epochs)" },
    { t: "Walk-Forward CV",      b: "Time-series split, 5 folds, same dates across cells" },
    { t: "Granger Causality",    b: "ADF stationarity pre-check, lag 1-5 days" },
  ];
  methods.forEach((m, i) => {
    const x = 0.6 + (i % 2) * 6.4;
    const y = 1.7 + Math.floor(i / 2) * 2.0;
    s.addShape("roundRect", {
      x, y, w: 6.0, h: 1.7,
      fill: { color: C.white },
      line: { color: C.deep, width: 1.2 },
      rectRadius: 0.1,
    });
    s.addShape("ellipse", {
      x: x + 0.2, y: y + 0.2, w: 0.4, h: 0.4,
      fill: { color: C.deep }, line: { width: 0 },
    });
    s.addText(String(i + 1), {
      x: x + 0.2, y: y + 0.2, w: 0.4, h: 0.4,
      fontFace: F.body, fontSize: 14, color: C.white, bold: true,
      align: "center", valign: "middle",
    });
    s.addText(m.t, {
      x: x + 0.75, y: y + 0.2, w: 5, h: 0.4,
      fontFace: F.body, fontSize: 14, color: C.mid, bold: true,
    });
    s.addText(m.b, {
      x: x + 0.75, y: y + 0.65, w: 5, h: 0.9,
      fontFace: F.body, fontSize: 12, color: C.text,
    });
  });

  // Foundation models callout
  s.addShape("roundRect", {
    x: 0.6, y: 5.8, w: 12.2, h: 1.2,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("Foundation Models Leveraged", {
    x: 0.8, y: 5.95, w: 5, h: 0.3,
    fontFace: F.body, fontSize: 12, color: C.accent, bold: true, charSpacing: 4,
  });
  s.addText("BART-MNLI: Zero-shot pseudo-labeling (no human annotations needed)  |  FinancialBERT: Pre-trained on finance corpus, fine-tuned for market sentiment",
    { x: 0.8, y: 6.3, w: 11.5, h: 0.6,
      fontFace: F.body, fontSize: 12, color: C.ice });
}

// ---------------------------------------------------------------------------
// Slide 8 — Correlation Analysis with Heatmap (Lecture 1: Variable Relationships)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Correlation Analysis", {
    x: 0.6, y: 0.3, w: 12.2, h: 0.6,
    fontFace: F.head, fontSize: 28, color: C.mid, bold: true,
  });
  s.addText("Lecture 1: Variable Relationships — Spearman Correlation Heatmap", {
    x: 0.6, y: 0.85, w: 12.2, h: 0.35,
    fontFace: F.body, fontSize: 12, color: C.teal, italic: true,
  });

  // Embed Correlation Heatmap (left side - full width since it's large)
  const corrPath = path.join(PLOTS_DIR, "correlation_heatmap.png");
  if (fs.existsSync(corrPath)) {
    s.addImage({
      x: 0.5, y: 1.35, w: 12.2, h: 4.5,
      path: corrPath,
    });
  } else {
    s.addText("Correlation Heatmap ( Lecture 1 )", {
      x: 0.5, y: 2.5, w: 12.2, h: 2.0,
      fontFace: F.body, fontSize: 14, color: C.muted, align: "center",
    });
  }

  // Key correlations callout
  s.addShape("roundRect", {
    x: 0.5, y: 6.0, w: 12.2, h: 0.9,
    fill: { color: C.ice }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("Key Correlations: fin_sent_mean_lag1 → btc_abs_return (ρ = -0.167)  |  pol_sent_mean_lag1 → gld_return (ρ = -0.170)  |  all_sent_mean_lag1 → btc_spike (ρ = -0.111)",
    { x: 0.7, y: 6.0, w: 11.8, h: 0.9,
      fontFace: F.body, fontSize: 12, color: C.text, valign: "middle" });
}

// ---------------------------------------------------------------------------
// Slide 9 — Results: AUC Matrix with Ablation (Section 4)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Results: AUC Matrix (σ = 2.0)", {
    x: 0.6, y: 0.3, w: 12.2, h: 0.6,
    fontFace: F.head, fontSize: 28, color: C.mid, bold: true,
  });
  s.addText("Walk-forward cross-validation, best model per cell (LogReg / RF / XGBoost)", {
    x: 0.6, y: 0.85, w: 12.2, h: 0.35,
    fontFace: F.body, fontSize: 12, color: C.muted, italic: true,
  });

  // 2x3 AUC Matrix visualization
  const matrixData = [
    ["", "Financial", "Political", "Combined"],
    ["BTC", "0.608", "0.538", "0.631"],
    ["GLD", "0.464", "0.546", "0.563"],
  ];
  const matX = 2.5, matY = 1.8, matW = 8.0, matH = 2.2;
  
  // Draw matrix cells
  const cellW = matW / 4, cellH = matH / 3;
  const aucValues = {
    "BTC-Fin": 0.608, "BTC-Pol": 0.538, "BTC-Comb": 0.631,
    "GLD-Fin": 0.464, "GLD-Pol": 0.546, "GLD-Comb": 0.563,
  };
  
  for (let i = 0; i < 3; i++) {
    for (let j = 0; j < 4; j++) {
      const x = matX + j * cellW;
      const y = matY + i * cellH;
      const bg = i === 0 ? C.mid : C.ice;
      s.addShape("rect", {
        x, y, w: cellW, h: cellH,
        fill: { color: bg },
        line: { color: C.line, width: 0.5 },
      });
      if (i === 0 || j === 0) {
        const txt = matrixData[i][j];
        s.addText(txt, {
          x: x + 0.1, y: y, w: cellW - 0.2, h: cellH,
          fontFace: F.body, fontSize: 14, color: i === 0 ? C.white : C.mid,
          bold: true, align: "center", valign: "middle",
        });
      } else {
        const key = (i === 1 ? "BTC" : "GLD") + (j === 1 ? "-Fin" : j === 2 ? "-Pol" : "-Comb");
        const val = aucValues[key];
        const isHighlight = (i === 1 && j === 3); // BTC Combined = best
        s.addText(val.toString(), {
          x: x + 0.1, y: y, w: cellW - 0.2, h: cellH,
          fontFace: F.head, fontSize: 22, color: isHighlight ? C.pos : C.text,
          bold: isHighlight, align: "center", valign: "middle",
        });
      }
    }
  }

  // Key findings boxes
  s.addText("Key Findings", {
    x: 0.6, y: 4.3, w: 4, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true,
  });
  
  const findings = [
    { t: "Best BTC result", v: "AUC 0.631", c: C.pos, b: "Combined sentiment, σ=2.0" },
    { t: "Best GLD result", v: "AUC 0.563", c: C.muted, b: "Near chance level" },
  ];
  findings.forEach((f, i) => {
    const x = 0.6 + i * 5.5;
    s.addShape("roundRect", {
      x, y: 4.75, w: 5.0, h: 1.4,
      fill: { color: C.ice }, line: { width: 0 }, rectRadius: 0.08,
    });
    s.addText(f.t, {
      x: x + 0.2, y: 4.85, w: 4.6, h: 0.35,
      fontFace: F.body, fontSize: 12, color: C.muted, bold: true,
    });
    s.addText(f.v, {
      x: x + 0.2, y: 5.15, w: 4.6, h: 0.5,
      fontFace: F.head, fontSize: 24, color: f.c, bold: true,
    });
    s.addText(f.b, {
      x: x + 0.2, y: 5.65, w: 4.6, h: 0.35,
      fontFace: F.body, fontSize: 11, color: C.text,
    });
  });

  s.addShape("line", {
    x: 0.6, y: 6.5, w: 12.2, h: 0, line: { color: C.line, width: 0.75 },
  });
  s.addText("BTC shows modest but consistent sentiment signal; GLD remains near chance",
    { x: 0.6, y: 6.6, w: 12.2, h: 0.35,
      fontFace: F.body, fontSize: 12, color: C.muted, italic: true });
}

// ---------------------------------------------------------------------------
// Slide 10 — Time Series: Price vs Sentiment (Lecture 3: Time Series Analysis)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Time Series: Price vs Sentiment", {
    x: 0.6, y: 0.3, w: 12.2, h: 0.6,
    fontFace: F.head, fontSize: 28, color: C.mid, bold: true,
  });
  s.addText("Lecture 3: Time Series Analysis — Dual-axis Price/Sentiment Overlay", {
    x: 0.6, y: 0.85, w: 12.2, h: 0.35,
    fontFace: F.body, fontSize: 12, color: C.teal, italic: true,
  });

  // Embed Time Series plot (full width)
  const tsPath = path.join(PLOTS_DIR, "price_vs_sentiment_timeseries.png");
  if (fs.existsSync(tsPath)) {
    s.addImage({
      x: 0.5, y: 1.35, w: 12.2, h: 5.0,
      path: tsPath,
    });
  } else {
    s.addText("Time Series: Price vs Sentiment ( Lecture 3 )", {
      x: 0.5, y: 2.5, w: 12.2, h: 2.0,
      fontFace: F.body, fontSize: 14, color: C.muted, align: "center",
    });
  }

  // Insight callout
  s.addShape("roundRect", {
    x: 0.5, y: 6.5, w: 12.2, h: 0.7,
    fill: { color: C.ice }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("BTC trades 24/7 (no weekend gaps) vs GLD (weekdays only) — GLD shows more volatility spikes on Monday openings",
    { x: 0.7, y: 6.5, w: 11.8, h: 0.7,
      fontFace: F.body, fontSize: 12, color: C.text, valign: "middle" });
}

// ---------------------------------------------------------------------------
// Slide 11 — Ablation Results (Section 4)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Ablation: Does Sentiment Add Value?", {
    x: 0.6, y: 0.3, w: 12.2, h: 0.6,
    fontFace: F.head, fontSize: 28, color: C.mid, bold: true,
  });
  s.addText("Price-only vs Sentiment-only vs Combined (XGBoost, best AUC)", {
    x: 0.6, y: 0.85, w: 12.2, h: 0.35,
    fontFace: F.body, fontSize: 14, color: C.muted, italic: true,
  });

  // Embed Ablation Bar Chart image
  const abPath = path.join(PLOTS_DIR, "ablation_bar_chart.png");
  if (fs.existsSync(abPath)) {
    s.addImage({
      x: 0.5, y: 1.35, w: 12.2, h: 4.5,
      path: abPath,
    });
  } else {
    s.addText("Ablation Bar Chart", {
      x: 0.5, y: 2.5, w: 12.2, h: 2.0,
      fontFace: F.body, fontSize: 14, color: C.muted, align: "center",
    });
  }

  // Key insight
  s.addShape("roundRect", {
    x: 0.5, y: 6.0, w: 12.2, h: 1.0,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("KEY FINDING: Sentiment-only (AUC 0.674) outperforms Price-only (AUC 0.640) for BTC", {
    x: 0.7, y: 6.0, w: 11.8, h: 0.5,
    fontFace: F.body, fontSize: 13, color: C.white, bold: true, valign: "middle",
  });
  s.addText("GLD shows no sentiment benefit — all configurations hover near chance level (0.5)", {
    x: 0.7, y: 6.5, w: 11.8, h: 0.4,
    fontFace: F.body, fontSize: 12, color: C.ice, valign: "middle",
  });
}

// ---------------------------------------------------------------------------
// Slide 12 — Granger Causality Results (Section 4)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Granger Causality Results", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("Testing if lagged sentiment predicts next-day volatility (ADF stationarity corrected)", {
    x: 0.6, y: 1.05, w: 12.2, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.muted, italic: true,
  });

  // Significant result highlight
  s.addShape("roundRect", {
    x: 0.6, y: 1.7, w: 12.2, h: 1.8,
    fill: { color: C.deep }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("STATISTICALLY SIGNIFICANT RESULT", {
    x: 0.8, y: 1.85, w: 6, h: 0.3,
    fontFace: F.body, fontSize: 11, color: C.accent, bold: true, charSpacing: 5,
  });
  s.addText("BTC_abs_return ← Political sentiment", {
    x: 0.8, y: 2.2, w: 11, h: 0.5,
    fontFace: F.head, fontSize: 20, color: C.white, bold: true,
  });
  s.addText("Lag: 5 days  |  p-value: 0.0107  |  Significant at p < 0.05", {
    x: 0.8, y: 2.75, w: 11, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.ice,
  });
  s.addText("After ADF stationarity correction, this is the only significant Granger result in the entire matrix.", {
    x: 0.8, y: 3.2, w: 11, h: 0.3,
    fontFace: F.body, fontSize: 12, color: C.muted,
  });

  // Interpretation
  s.addText("Interpretation", {
    x: 0.6, y: 3.8, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true,
  });
  s.addText("Political news from the 2024 election cycle appears to have\npredictive value for Bitcoin volatility at approximately a 5-day lag.", {
    x: 0.6, y: 4.25, w: 8, h: 0.8,
    fontFace: F.body, fontSize: 14, color: C.text,
  });

  // Other results summary
  s.addShape("roundRect", {
    x: 0.6, y: 5.2, w: 12.2, h: 1.6,
    fill: { color: C.ice }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("OTHER RESULTS", {
    x: 0.8, y: 5.35, w: 4, h: 0.3,
    fontFace: F.body, fontSize: 10, color: C.muted, bold: true, charSpacing: 5,
  });
  const others = [
    "No significant Granger results for GLD (all p > 0.05)",
    "Financial and all-stream sentiment did not reach significance",
    "BTC response to political news likely reflects 2024 election uncertainty",
  ];
  others.forEach((txt, i) => {
    s.addText("• " + txt, {
      x: 0.8, y: 5.7 + i * 0.4, w: 11.5, h: 0.4,
      fontFace: F.body, fontSize: 12, color: C.text,
    });
  });
}

// ---------------------------------------------------------------------------
// Slide 13 — Key Takeaways (Section 5 - Closing)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.mid };
  s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: C.accent } });

  s.addText("Key Takeaways", {
    x: 0.9, y: 0.5, w: 12, h: 0.8,
    fontFace: F.head, fontSize: 36, color: C.white, bold: true,
  });

  const takeaways = [
    { n: "1", t: "Bitcoin has a modest but real sentiment signal", d: "Best AUC 0.631, above chance across multiple configurations" },
    { n: "2", t: "Sentiment carries unique information", d: "Sentiment-only (0.674) outperforms price-only (0.640) for BTC" },
    { n: "3", t: "Political news predicts crypto volatility", d: "Granger: political sentiment → BTC volatility at lag 5 (p=0.0107)" },
    { n: "4", t: "Gold doesn't respond to headline sentiment", d: "All GLD results near chance (best AUC 0.563), corpus is crypto-heavy" },
  ];

  takeaways.forEach((t, i) => {
    const y = 1.5 + i * 1.35;
    s.addShape("ellipse", {
      x: 0.9, y: y + 0.1, w: 0.45, h: 0.45,
      fill: { color: C.accent }, line: { width: 0 },
    });
    s.addText(t.n, {
      x: 0.9, y: y + 0.1, w: 0.45, h: 0.45,
      fontFace: F.head, fontSize: 16, color: C.mid, bold: true,
      align: "center", valign: "middle",
    });
    s.addText(t.t, {
      x: 1.5, y: y, w: 10.5, h: 0.45,
      fontFace: F.body, fontSize: 15, color: C.white, bold: true,
    });
    s.addText(t.d, {
      x: 1.5, y: y + 0.45, w: 10.5, h: 0.6,
      fontFace: F.body, fontSize: 12, color: C.ice,
    });
  });

  // Limitations
  s.addShape("roundRect", {
    x: 0.9, y: 6.5, w: 11.5, h: 0.7,
    fill: { color: C.deep }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("Limitations: 6-month window, crypto-heavy corpus, small sample size",
    { x: 1.1, y: 6.5, w: 11.1, h: 0.7,
      fontFace: F.body, fontSize: 12, color: C.white, valign: "middle" });
}

// ---------------------------------------------------------------------------
// Slide 14 — Q&A (Closing)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.mid };
  s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: C.accent } });

  s.addText("Q&A", {
    x: 0.9, y: 2.8, w: 11, h: 1.5,
    fontFace: F.head, fontSize: 72, color: C.white, bold: true, align: "center",
  });
  s.addText("Questions?", {
    x: 0.9, y: 4.4, w: 11, h: 0.8,
    fontFace: F.body, fontSize: 24, color: C.ice, align: "center", italic: true,
  });

  // Contact/info
  s.addText("News Sentiment & Market Dynamics — Bitcoin and Gold, July–December 2024",
    { x: 0.9, y: 6.0, w: 11, h: 0.4,
      fontFace: F.body, fontSize: 12, color: C.muted, align: "center" });
}

// ---------------------------------------------------------------------------
pres.writeFile({
  fileName: path.join(__dirname, "artifacts", "slides_full_presentation.pptx"),
}).then(p => console.log("wrote", p));
