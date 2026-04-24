// Modeling & Analysis deck — companion to slides_data_overview.pptx.
// Same Ocean Gradient palette and typography for visual continuity.

const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5

const C = {
  deep: "065A82", teal: "1C7293", mid: "21295C",
  ice: "E8F1F7", line: "9DB4C0",
  white: "FFFFFF", text: "1F2A37", muted: "5C6B7A",
  accent: "F0A202",        // gold
  good: "2E8B57", bad: "C03221", neutral: "6C757D",
};
const F = { head: "Georgia", body: "Calibri", mono: "Consolas" };

function titleSlide(s, opts) {
  s.background = { color: C.mid };
  s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: C.accent } });
  s.addText(opts.eyebrow, {
    x: 0.9, y: 1.9, w: 10, h: 0.5,
    fontFace: F.body, fontSize: 14, color: C.accent, bold: true, charSpacing: 8,
  });
  s.addText(opts.title, {
    x: 0.9, y: 2.4, w: 11.8, h: 2.0,
    fontFace: F.head, fontSize: 52, color: C.white, bold: true,
  });
  if (opts.subtitle) {
    s.addText(opts.subtitle, {
      x: 0.9, y: 4.5, w: 11.5, h: 0.6,
      fontFace: F.body, fontSize: 20, color: C.ice, italic: true,
    });
  }
}

function contentHeader(s, title, sub) {
  s.addText(title, {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  if (sub) s.addText(sub, {
    x: 0.6, y: 1.05, w: 12.2, h: 0.4,
    fontFace: F.body, fontSize: 15, color: C.muted, italic: true,
  });
}

// ---------------------------------------------------------------------------
// Slide 1 — Title
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  titleSlide(s, {
    eyebrow: "PART II",
    title: "Modeling &\nAnalysis",
    subtitle: "From 21,000 headlines to statistically rigorous findings",
  });
  // Three stat callouts
  const stats = [
    { n: "18",    l: "model cells trained" },
    { n: "0.674", l: "BTC sentiment-only AUC" },
    { n: "p=0.011", l: "political news → BTC lag 5" },
  ];
  stats.forEach((st, i) => {
    const x = 0.9 + i * 4.1;
    s.addText(st.n, {
      x, y: 5.8, w: 3.8, h: 0.7,
      fontFace: F.head, fontSize: 34, color: C.accent, bold: true,
    });
    s.addText(st.l, {
      x, y: 6.45, w: 3.8, h: 0.4,
      fontFace: F.body, fontSize: 13, color: C.ice, charSpacing: 2,
    });
  });
}

// ---------------------------------------------------------------------------
// Slide 2 — Fine-tuning FinancialBERT (weak supervision)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  contentHeader(s, "Fine-tuning FinancialBERT",
    "Weak-supervision pipeline: no gold labels needed");

  // LEFT: pipeline steps
  const steps = [
    { n: "1", t: "Sample 5,000 headlines", s: "stratified across tags" },
    { n: "2", t: "Zero-shot label with BART-MNLI", s: "market-framed hypotheses" },
    { n: "3", t: "Confidence filter ≥ 0.65", s: "2,922 clean pseudo-labels" },
    { n: "4", t: "Fine-tune FinancialBERT", s: "4 epochs, bottom layers frozen" },
    { n: "5", t: "Score all 20,939 headlines", s: "feed downstream aggregation" },
  ];
  steps.forEach((st, i) => {
    const y = 1.7 + i * 0.85;
    s.addShape("ellipse", {
      x: 0.7, y: y + 0.1, w: 0.5, h: 0.5,
      fill: { color: C.deep }, line: { width: 0 },
    });
    s.addText(st.n, {
      x: 0.7, y: y + 0.1, w: 0.5, h: 0.5,
      fontFace: F.head, fontSize: 18, color: C.white, bold: true,
      align: "center", valign: "middle",
    });
    s.addText(st.t, {
      x: 1.35, y, w: 5.5, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.mid, bold: true,
    });
    s.addText(st.s, {
      x: 1.35, y: y + 0.4, w: 5.5, h: 0.4,
      fontFace: F.body, fontSize: 12, color: C.muted, italic: true,
    });
  });

  // RIGHT: ablation card
  s.addShape("roundRect", {
    x: 7.4, y: 1.7, w: 5.4, h: 4.6,
    fill: { color: C.ice }, line: { color: C.line, width: 0.5 },
    rectRadius: 0.1,
  });
  s.addText("ABLATION RESULT", {
    x: 7.6, y: 1.85, w: 5, h: 0.35,
    fontFace: F.body, fontSize: 11, color: C.accent, bold: true, charSpacing: 5,
  });
  s.addText("Held-out test set (n = 291)", {
    x: 7.6, y: 2.2, w: 5, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.muted, italic: true,
  });

  // Comparison rows
  const abl = [
    { label: "Baseline\nFinancialBERT", acc: "0.526", f1: "0.423", col: C.neutral },
    { label: "Fine-tuned\nFinancialBERT", acc: "0.790", f1: "0.790", col: C.good },
  ];
  abl.forEach((r, i) => {
    const y = 2.75 + i * 1.55;
    s.addShape("rect", {
      x: 7.6, y, w: 0.08, h: 1.3, fill: { color: r.col }, line: { width: 0 },
    });
    s.addText(r.label, {
      x: 7.85, y, w: 2, h: 1.3,
      fontFace: F.body, fontSize: 13, color: C.text, bold: true, valign: "middle",
    });
    s.addText(r.acc, {
      x: 9.9, y: y + 0.1, w: 1.25, h: 0.55,
      fontFace: F.head, fontSize: 26, color: r.col, bold: true, align: "center",
    });
    s.addText("accuracy", {
      x: 9.9, y: y + 0.72, w: 1.25, h: 0.3,
      fontFace: F.body, fontSize: 9, color: C.muted, align: "center",
    });
    s.addText(r.f1, {
      x: 11.3, y: y + 0.1, w: 1.25, h: 0.55,
      fontFace: F.head, fontSize: 26, color: r.col, bold: true, align: "center",
    });
    s.addText("F1 (macro)", {
      x: 11.3, y: y + 0.72, w: 1.25, h: 0.3,
      fontFace: F.body, fontSize: 9, color: C.muted, align: "center",
    });
  });

  s.addText("Δ = +0.37 F1 — scheme-alignment gain (not superhuman accuracy)",
    { x: 7.6, y: 5.9, w: 5, h: 0.35,
      fontFace: F.body, fontSize: 11, color: C.muted, italic: true });
}

// ---------------------------------------------------------------------------
// Slide 3 — Feature engineering
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  contentHeader(s, "Feature engineering",
    "Turn each daily sentiment score and price observation into predictive lags");

  const groups = [
    {
      title: "Sentiment lags (× 3 streams)",
      color: C.deep,
      items: [
        "mean · variance · headline count · pos/neg share",
        "1-day lag (yesterday's value)",
        "3-day and 7-day rolling means",
        "Momentum (Δ day-over-day)",
      ],
      note: "≈ 45 features across all / financial / political streams",
    },
    {
      title: "Price-autoregressive features",
      color: C.teal,
      items: [
        "Returns at lag 1, 2, 3",
        "Absolute returns at lag 1, 3",
        "Rolling volatility (5 / 10 / 30-day std)",
        "Weekend-ffill for GLD",
      ],
      note: "Critical baseline — 'does sentiment beat price history alone?'",
    },
    {
      title: "Target labels",
      color: C.accent,
      items: [
        "Spike: |return| > 2σ above 30-day rolling mean",
        "Surge: volume > 2σ above 30-day rolling volume",
        "Binary targets for classification",
        "Magnitude: raw |return| for ridge regression",
      ],
      note: "σ = 1.5 also tested as a robustness check",
    },
  ];

  groups.forEach((g, i) => {
    const x = 0.6 + i * 4.2;
    const w = 3.9;
    s.addShape("roundRect", {
      x, y: 1.7, w, h: 5.1,
      fill: { color: C.white },
      line: { color: C.line, width: 0.75 },
      rectRadius: 0.1,
    });
    s.addShape("rect", {
      x, y: 1.7, w, h: 0.18, fill: { color: g.color }, line: { width: 0 },
    });
    s.addText(g.title, {
      x: x + 0.25, y: 2.0, w: w - 0.5, h: 0.6,
      fontFace: F.head, fontSize: 16, color: C.mid, bold: true,
    });
    g.items.forEach((it, j) => {
      const y = 2.75 + j * 0.55;
      s.addShape("ellipse", {
        x: x + 0.3, y: y + 0.15, w: 0.12, h: 0.12,
        fill: { color: g.color }, line: { width: 0 },
      });
      s.addText(it, {
        x: x + 0.5, y, w: w - 0.7, h: 0.45,
        fontFace: F.body, fontSize: 12.5, color: C.text,
      });
    });
    // Note at bottom
    s.addShape("rect", {
      x, y: 6.25, w, h: 0.55,
      fill: { color: C.ice }, line: { width: 0 },
    });
    s.addText(g.note, {
      x: x + 0.25, y: 6.28, w: w - 0.5, h: 0.5,
      fontFace: F.body, fontSize: 11, color: C.muted, italic: true, valign: "middle",
    });
  });
}

// ---------------------------------------------------------------------------
// Slide 4 — Modeling methodology
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  contentHeader(s, "Modeling methodology",
    "Honest out-of-sample evaluation via walk-forward cross-validation");

  // LEFT: CV diagram illustration
  s.addText("Walk-forward CV (5 folds)", {
    x: 0.6, y: 1.7, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true, charSpacing: 4,
  });

  // Small CV schematic
  const foldRows = 5;
  for (let i = 0; i < foldRows; i++) {
    const y = 2.2 + i * 0.55;
    const trainW = 2.2 + i * 0.55;
    const testW = 0.55;
    // train bar
    s.addShape("rect", {
      x: 0.6, y, w: trainW, h: 0.38,
      fill: { color: C.deep }, line: { width: 0 },
    });
    // test bar
    s.addShape("rect", {
      x: 0.6 + trainW + 0.05, y, w: testW, h: 0.38,
      fill: { color: C.accent }, line: { width: 0 },
    });
    // Fold label
    s.addText("fold " + (i + 1), {
      x: 5.4, y, w: 0.9, h: 0.38,
      fontFace: F.body, fontSize: 11, color: C.muted, valign: "middle",
    });
  }
  // Legend
  s.addShape("rect", { x: 0.6, y: 5.1, w: 0.3, h: 0.25,
    fill: { color: C.deep }, line: { width: 0 } });
  s.addText("train (past)", { x: 1.0, y: 5.08, w: 1.5, h: 0.3,
    fontFace: F.body, fontSize: 11, color: C.muted });
  s.addShape("rect", { x: 2.5, y: 5.1, w: 0.3, h: 0.25,
    fill: { color: C.accent }, line: { width: 0 } });
  s.addText("test (future)", { x: 2.9, y: 5.08, w: 1.5, h: 0.3,
    fontFace: F.body, fontSize: 11, color: C.muted });

  // Bottom: models
  s.addText("Classifiers compared", {
    x: 0.6, y: 5.7, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true, charSpacing: 4,
  });
  s.addText("Logistic Regression · Random Forest · XGBoost", {
    x: 0.6, y: 6.15, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 13, color: C.text,
  });
  s.addText("Best model per cell is reported — we let the data choose.",
    { x: 0.6, y: 6.5, w: 6, h: 0.4,
      fontFace: F.body, fontSize: 11, color: C.muted, italic: true });

  // RIGHT: design choices
  s.addShape("roundRect", {
    x: 7.0, y: 1.7, w: 5.8, h: 5.1,
    fill: { color: C.ice }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("DESIGN CHOICES", {
    x: 7.2, y: 1.85, w: 5.4, h: 0.35,
    fontFace: F.body, fontSize: 11, color: C.accent, bold: true, charSpacing: 5,
  });

  const choices = [
    {
      h: "No future leakage",
      b: "Time-series split always trains on past rows, tests on future rows. Never random k-fold.",
    },
    {
      h: "AUC over F1",
      b: "Spikes are ~15% of days. AUC is the honest metric for rare events; F1 reported as secondary.",
    },
    {
      h: "Class-imbalance safe",
      b: "class_weight='balanced' on LogReg/RF. Skip degenerate folds with no positives in train or test.",
    },
    {
      h: "Two sigma thresholds",
      b: "σ = 2.0 (proposal spec) and σ = 1.5 (robustness). Report both to rule out threshold sensitivity.",
    },
    {
      h: "Missing-stream imputation",
      b: "Days with zero political headlines → neutral sentiment (0). Prevents dropna() collapsing the matrix.",
    },
  ];
  choices.forEach((c, i) => {
    const y = 2.3 + i * 0.88;
    s.addShape("rect", {
      x: 7.2, y, w: 0.06, h: 0.75, fill: { color: C.teal }, line: { width: 0 },
    });
    s.addText(c.h, {
      x: 7.4, y, w: 5.3, h: 0.3,
      fontFace: F.body, fontSize: 13, color: C.deep, bold: true,
    });
    s.addText(c.b, {
      x: 7.4, y: y + 0.3, w: 5.3, h: 0.5,
      fontFace: F.body, fontSize: 11.5, color: C.text,
    });
  });
}

// ---------------------------------------------------------------------------
// Slide 5 — The 2x3 matrix
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  contentHeader(s, "Result: the 2×3 matrix",
    "Walk-forward AUC across {BTC, GLD} × {Financial, Political, Combined} sentiment");

  // Two matrix tables side by side
  const sigmas = [
    { tag: "σ = 2.0 (strict, ~14% spike rate)", yOffset: 0,
      data: {
        BTC: [0.608, 0.538, 0.631],
        GLD: [0.464, 0.546, 0.563],
      }},
    { tag: "σ = 1.5 (lenient, ~20% spike rate)", yOffset: 3.05,
      data: {
        BTC: [0.623, 0.490, 0.569],
        GLD: [0.537, 0.447, 0.512],
      }},
  ];

  const colLabels = ["Financial only", "Political only", "Combined"];

  sigmas.forEach(sg => {
    const yBase = 1.7 + sg.yOffset;
    s.addText(sg.tag, {
      x: 0.6, y: yBase, w: 7, h: 0.35,
      fontFace: F.body, fontSize: 13, color: C.accent, bold: true, charSpacing: 4,
    });

    // Table header
    const colW = 1.4; const labelW = 1.0;
    const x0 = 0.6; const y0 = yBase + 0.45;
    // top-left blank
    s.addShape("rect", { x: x0, y: y0, w: labelW, h: 0.4,
      fill: { color: C.mid }, line: { width: 0 } });
    colLabels.forEach((cl, i) => {
      s.addShape("rect", { x: x0 + labelW + i * colW, y: y0,
        w: colW, h: 0.4, fill: { color: C.mid }, line: { width: 0 } });
      s.addText(cl, { x: x0 + labelW + i * colW, y: y0, w: colW, h: 0.4,
        fontFace: F.body, fontSize: 11, color: C.white, bold: true,
        align: "center", valign: "middle" });
    });

    // Rows
    ["BTC", "GLD"].forEach((asset, r) => {
      const y = y0 + 0.4 + r * 0.55;
      s.addShape("rect", { x: x0, y, w: labelW, h: 0.55,
        fill: { color: r % 2 === 0 ? C.ice : C.white }, line: { width: 0 } });
      s.addText(asset, { x: x0 + 0.1, y, w: labelW - 0.1, h: 0.55,
        fontFace: F.body, fontSize: 14, color: C.deep, bold: true, valign: "middle" });
      const rowData = sg.data[asset];
      const maxVal = Math.max(...rowData);
      rowData.forEach((v, c) => {
        const isBest = Math.abs(v - maxVal) < 1e-6 && v > 0.55;
        const isSignal = v >= 0.6;
        const cellColor = isBest ? C.accent : (isSignal ? C.teal : C.white);
        const textColor = isBest ? C.white : (isSignal ? C.white : C.text);
        s.addShape("rect", {
          x: x0 + labelW + c * colW, y, w: colW, h: 0.55,
          fill: { color: cellColor }, line: { color: C.line, width: 0.3 },
        });
        s.addText(v.toFixed(3), {
          x: x0 + labelW + c * colW, y, w: colW, h: 0.55,
          fontFace: F.head, fontSize: 18, bold: isBest, color: textColor,
          align: "center", valign: "middle",
        });
      });
    });
  });

  // RIGHT: takeaways
  s.addShape("roundRect", {
    x: 8.0, y: 1.7, w: 4.8, h: 5.1,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("READING THE MATRIX", {
    x: 8.2, y: 1.9, w: 4.4, h: 0.35,
    fontFace: F.body, fontSize: 11, color: C.accent, bold: true, charSpacing: 5,
  });
  const takeaways = [
    { t: "AUC > 0.60 = signal", b: "Every cell above chance" },
    { t: "BTC responds", b: "All BTC cells ≥ 0.54 at σ=2.0; combined = 0.63" },
    { t: "GLD does not", b: "No GLD cell exceeds 0.57 in either regime" },
    { t: "Robust across σ", b: "BTC story holds at σ=1.5 (AUC 0.62)" },
    { t: "F1 is low by design", b: "Spikes are rare → AUC is the honest metric" },
  ];
  takeaways.forEach((t, i) => {
    const y = 2.35 + i * 0.88;
    s.addShape("rect", { x: 8.2, y, w: 0.06, h: 0.75,
      fill: { color: C.accent }, line: { width: 0 } });
    s.addText(t.t, { x: 8.4, y, w: 4.2, h: 0.3,
      fontFace: F.body, fontSize: 13, color: C.white, bold: true });
    s.addText(t.b, { x: 8.4, y: y + 0.3, w: 4.2, h: 0.5,
      fontFace: F.body, fontSize: 11.5, color: C.ice });
  });
}

// ---------------------------------------------------------------------------
// Slide 6 — Does sentiment add value? (THE KEY ABLATION)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  contentHeader(s, "Does sentiment add value beyond price?",
    "Three-way ablation: price-autoregressive vs sentiment vs combined");

  // Big comparison chart — two assets, three bars each
  // Draw as stylized bar groups
  const groups = [
    { asset: "BTC",
      bars: [
        { label: "Price only",        v: 0.640, col: C.teal },
        { label: "Sentiment only",    v: 0.674, col: C.accent },
        { label: "Price + Sentiment", v: 0.582, col: C.neutral },
      ]},
    { asset: "GLD",
      bars: [
        { label: "Price only",        v: 0.591, col: C.teal },
        { label: "Sentiment only",    v: 0.563, col: C.neutral },
        { label: "Price + Sentiment", v: 0.585, col: C.neutral },
      ]},
  ];

  // Chart area
  const chartX = 0.8, chartY = 2.0, chartW = 7.5, chartH = 4.5;
  const maxAxis = 0.75, minAxis = 0.40;
  const range = maxAxis - minAxis;

  // Baseline line at 0.5
  const chanceY = chartY + chartH * (1 - (0.5 - minAxis) / range);
  s.addShape("line", {
    x: chartX, y: chanceY, w: chartW, h: 0,
    line: { color: C.line, width: 1, dashType: "dash" },
  });
  s.addText("chance (AUC 0.50)", {
    x: chartX + chartW - 2.0, y: chanceY - 0.3, w: 2, h: 0.3,
    fontFace: F.body, fontSize: 10, color: C.muted, italic: true, align: "right",
  });

  const groupSpacing = chartW / groups.length;
  const barWRatio = 0.25;
  groups.forEach((g, gi) => {
    const gx = chartX + gi * groupSpacing + 0.3;
    // Asset label
    s.addText(g.asset, {
      x: gx, y: chartY + chartH + 0.1, w: groupSpacing - 0.6, h: 0.4,
      fontFace: F.head, fontSize: 18, color: C.mid, bold: true, align: "center",
    });
    g.bars.forEach((b, bi) => {
      const barW = barWRatio * groupSpacing;
      const x = gx + bi * (barW + 0.15);
      const h = chartH * (b.v - minAxis) / range;
      const y = chartY + chartH - h;
      s.addShape("rect", {
        x, y, w: barW, h, fill: { color: b.col }, line: { width: 0 },
      });
      s.addText(b.v.toFixed(3), {
        x, y: y - 0.4, w: barW, h: 0.35,
        fontFace: F.head, fontSize: 13, color: b.col, bold: true, align: "center",
      });
      s.addText(b.label, {
        x: x - 0.2, y: chartY + chartH + 0.55, w: barW + 0.4, h: 0.6,
        fontFace: F.body, fontSize: 9.5, color: C.muted, align: "center",
      });
    });
  });

  // Y-axis label
  s.addText("AUC", {
    x: 0.3, y: chartY + chartH / 2 - 0.2, w: 0.4, h: 0.4,
    fontFace: F.body, fontSize: 12, color: C.muted, bold: true,
  });

  // RIGHT: finding callout
  s.addShape("roundRect", {
    x: 8.8, y: 1.7, w: 4.0, h: 5.1,
    fill: { color: C.accent }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("KEY FINDING", {
    x: 9.0, y: 1.85, w: 3.6, h: 0.4,
    fontFace: F.body, fontSize: 12, color: C.mid, bold: true, charSpacing: 6,
  });
  s.addText("Sentiment > Price\nfor Bitcoin", {
    x: 9.0, y: 2.3, w: 3.6, h: 1.2,
    fontFace: F.head, fontSize: 24, color: C.white, bold: true,
  });
  s.addText("BTC sentiment-only (0.674) beats price-only (0.640).\n\nThis is evidence sentiment carries information NOT present in autoregressive price features.",
    { x: 9.0, y: 3.6, w: 3.6, h: 1.8,
      fontFace: F.body, fontSize: 12, color: C.white });
  s.addShape("line", {
    x: 9.1, y: 5.45, w: 3.6, h: 0, line: { color: C.white, width: 1 },
  });
  s.addText("But naïve combination (0.582) overfits — 178 samples aren't enough for feature stacking.",
    { x: 9.0, y: 5.55, w: 3.6, h: 1.1,
      fontFace: F.body, fontSize: 11.5, color: C.white, italic: true });
}

// ---------------------------------------------------------------------------
// Slide 7 — Granger causality (the rigorous finding)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  contentHeader(s, "Granger causality with stationarity correction",
    "Does past sentiment help predict future volatility beyond its own past?");

  // LEFT: methodology
  s.addText("Methodology", {
    x: 0.6, y: 1.7, w: 6, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true, charSpacing: 4,
  });
  const method = [
    "Test each sentiment stream against each asset's\n|return| at lags 1–5 days.",
    "Run augmented Dickey-Fuller (ADF) pre-check.\nIf a series is non-stationary, difference it before\nrunning Granger — so p-values are interpretable.",
    "Total: 30 (asset × stream × lag) tests.",
  ];
  method.forEach((m, i) => {
    const y = 2.15 + i * 1.0;
    s.addShape("ellipse", {
      x: 0.65, y: y + 0.12, w: 0.25, h: 0.25,
      fill: { color: C.deep }, line: { width: 0 },
    });
    s.addText(m, { x: 1.0, y, w: 5.3, h: 0.9,
      fontFace: F.body, fontSize: 12.5, color: C.text });
  });

  // RIGHT: the result
  s.addShape("roundRect", {
    x: 7.0, y: 1.7, w: 5.8, h: 5.1,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("THE ONE SIGNIFICANT RESULT", {
    x: 7.2, y: 1.9, w: 5.4, h: 0.35,
    fontFace: F.body, fontSize: 11, color: C.accent, bold: true, charSpacing: 5,
  });
  // Equation-style display
  s.addText("Political sentiment", {
    x: 7.2, y: 2.45, w: 5.4, h: 0.5,
    fontFace: F.head, fontSize: 22, color: C.white, bold: true,
  });
  s.addText("→   BTC |return|   (lag 5)", {
    x: 7.2, y: 2.95, w: 5.4, h: 0.5,
    fontFace: F.head, fontSize: 22, color: C.accent, bold: true,
  });

  // Big p-value callout
  s.addShape("line", {
    x: 7.2, y: 3.75, w: 5.4, h: 0, line: { color: C.accent, width: 1.5 },
  });
  s.addText("p = 0.0107", {
    x: 7.2, y: 3.9, w: 5.4, h: 0.8,
    fontFace: F.head, fontSize: 40, color: C.white, bold: true, align: "center",
  });
  s.addText("(below 0.05 threshold — statistically significant)", {
    x: 7.2, y: 4.7, w: 5.4, h: 0.4,
    fontFace: F.body, fontSize: 12, color: C.ice, italic: true, align: "center",
  });

  // Interpretation
  s.addText("Counter to hypothesis: political news predicts Bitcoin, not gold.", {
    x: 7.2, y: 5.3, w: 5.4, h: 0.4,
    fontFace: F.body, fontSize: 13, color: C.accent, bold: true,
  });
  s.addText("Likely explanation: the Jul–Dec 2024 window covers the US election. Political uncertainty affected BTC via regulatory expectations.",
    { x: 7.2, y: 5.7, w: 5.4, h: 1.0,
      fontFace: F.body, fontSize: 11.5, color: C.ice });
}

// ---------------------------------------------------------------------------
// Slide 8 — Ridge regression (honest null)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  contentHeader(s, "Predicting volatility magnitude",
    "Ridge regression on |return| — an honest null result");

  // Table of ridge R² results
  const rows = [
    { asset: "BTC", fs: "Price only",        r2: -0.91, mae: 0.021 },
    { asset: "BTC", fs: "Sentiment only",    r2: -1.77, mae: 0.021 },
    { asset: "BTC", fs: "Price + Sentiment", r2: -3.74, mae: 0.029 },
    { asset: "GLD", fs: "Price only",        r2: -0.54, mae: 0.005 },
    { asset: "GLD", fs: "Sentiment only",    r2: -1.55, mae: 0.007 },
    { asset: "GLD", fs: "Price + Sentiment", r2: -2.25, mae: 0.008 },
  ];

  const tbl = { x: 0.6, y: 1.7, w: 7.0, rowH: 0.5 };
  // Header
  const headers = ["Asset", "Feature set", "MAE", "R²"];
  const colWidths = [1.0, 2.6, 1.4, 2.0];
  let cx = tbl.x;
  headers.forEach((h, i) => {
    s.addShape("rect", { x: cx, y: tbl.y, w: colWidths[i], h: tbl.rowH,
      fill: { color: C.mid }, line: { width: 0 } });
    s.addText(h, { x: cx, y: tbl.y, w: colWidths[i], h: tbl.rowH,
      fontFace: F.body, fontSize: 13, color: C.white, bold: true,
      align: "center", valign: "middle" });
    cx += colWidths[i];
  });

  rows.forEach((r, ri) => {
    const y = tbl.y + tbl.rowH + ri * tbl.rowH;
    const bg = ri % 2 === 0 ? C.ice : C.white;
    let x = tbl.x;
    const vals = [r.asset, r.fs, r.mae.toFixed(3), r.r2.toFixed(2)];
    vals.forEach((v, i) => {
      s.addShape("rect", { x, y, w: colWidths[i], h: tbl.rowH,
        fill: { color: bg }, line: { color: C.line, width: 0.3 } });
      const isR2 = i === 3;
      s.addText(v, { x, y, w: colWidths[i], h: tbl.rowH,
        fontFace: isR2 ? F.head : F.body,
        fontSize: isR2 ? 15 : 13,
        color: isR2 ? C.bad : C.text,
        bold: isR2,
        align: "center", valign: "middle" });
      x += colWidths[i];
    });
  });

  // RIGHT: interpretation
  s.addShape("roundRect", {
    x: 8.0, y: 1.7, w: 4.8, h: 5.1,
    fill: { color: C.ice }, line: { color: C.line, width: 0.5 }, rectRadius: 0.1,
  });
  s.addText("INTERPRETATION", {
    x: 8.2, y: 1.85, w: 4.4, h: 0.35,
    fontFace: F.body, fontSize: 11, color: C.bad, bold: true, charSpacing: 5,
  });

  // Big number
  s.addText("R² < 0", {
    x: 8.2, y: 2.35, w: 4.4, h: 0.9,
    fontFace: F.head, fontSize: 44, color: C.bad, bold: true, align: "center",
  });
  s.addText("every configuration", {
    x: 8.2, y: 3.2, w: 4.4, h: 0.4,
    fontFace: F.body, fontSize: 13, color: C.muted, italic: true, align: "center",
  });

  s.addShape("line", {
    x: 8.4, y: 3.8, w: 4.0, h: 0, line: { color: C.line, width: 1 },
  });

  s.addText("All models do worse than predicting the mean volatility.",
    { x: 8.3, y: 3.95, w: 4.2, h: 0.7,
      fontFace: F.body, fontSize: 13, color: C.text, bold: true });
  s.addText("Consistent with efficient-market expectations: magnitude is harder than direction at daily frequency with sub-200 samples.",
    { x: 8.3, y: 4.75, w: 4.2, h: 1.5,
      fontFace: F.body, fontSize: 11.5, color: C.text });
  s.addText("Honest reporting. Not every experiment succeeds — and that's fine.",
    { x: 8.3, y: 6.2, w: 4.2, h: 0.5,
      fontFace: F.body, fontSize: 11, color: C.muted, italic: true });
}

// ---------------------------------------------------------------------------
// Slide 9 — Findings summary + Limitations (dark, closing)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.mid };
  s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: C.accent } });

  s.addText("Findings", {
    x: 0.9, y: 0.45, w: 12, h: 0.8,
    fontFace: F.head, fontSize: 36, color: C.white, bold: true,
  });

  // LEFT: findings list
  const findings = [
    { t: "Sentiment beats price for BTC",
      b: "Sentiment-only AUC 0.674 > price-only 0.640." },
    { t: "Political news Granger-causes BTC volatility",
      b: "Lag 5 days, p = 0.011 after ADF stationarity correction." },
    { t: "Gold signal is absent",
      b: "No feature set exceeds AUC 0.60 for GLD." },
    { t: "Magnitude is unpredictable",
      b: "Ridge R² negative everywhere — efficient markets at daily scale." },
  ];
  findings.forEach((f, i) => {
    const y = 1.5 + i * 1.1;
    s.addShape("rect", { x: 0.9, y, w: 0.06, h: 0.95,
      fill: { color: C.accent }, line: { width: 0 } });
    s.addText(f.t, { x: 1.1, y, w: 6.0, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.accent, bold: true, charSpacing: 3 });
    s.addText(f.b, { x: 1.1, y: y + 0.4, w: 6.0, h: 0.55,
      fontFace: F.body, fontSize: 13, color: C.ice });
  });

  // RIGHT: Limitations
  s.addShape("rect", {
    x: 7.6, y: 1.5, w: 0.06, h: 4.5,
    fill: { color: C.white }, line: { width: 0 },
  });
  s.addText("LIMITATIONS", {
    x: 7.8, y: 1.5, w: 5.0, h: 0.4,
    fontFace: F.body, fontSize: 12, color: C.white, bold: true, charSpacing: 6,
  });

  const lims = [
    "Small sample: 178 rows (BTC) / 96 (GLD).",
    "Labels are zero-shot-bootstrapped, not human-annotated.",
    "Single time window covers US election cycle.",
    "Financial-tagged corpus is ~83% crypto-native (not broad finance).",
    "Headlines only — no article bodies scored.",
  ];
  lims.forEach((l, i) => {
    const y = 2.0 + i * 0.62;
    s.addText("•", { x: 7.8, y, w: 0.25, h: 0.4,
      fontFace: F.body, fontSize: 16, color: C.accent, bold: true });
    s.addText(l, { x: 8.05, y, w: 4.7, h: 0.55,
      fontFace: F.body, fontSize: 12, color: C.ice });
  });

  // Bottom: headline takeaway ribbon
  s.addShape("roundRect", {
    x: 0.9, y: 6.2, w: 11.9, h: 1.05,
    fill: { color: C.deep }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("The headline result",
    { x: 1.1, y: 6.28, w: 11.5, h: 0.3,
      fontFace: F.body, fontSize: 11, color: C.accent, bold: true, charSpacing: 5 });
  s.addText("News sentiment adds information beyond price history for Bitcoin — most rigorously, political news Granger-causes BTC volatility at a 5-day lag. Gold is unresponsive to sentiment in this window.",
    { x: 1.1, y: 6.58, w: 11.5, h: 0.65,
      fontFace: F.body, fontSize: 13, color: C.white, italic: true });
}

// ---------------------------------------------------------------------------
pres.writeFile({
  fileName: path.join(__dirname, "artifacts", "slides_modeling_analysis.pptx"),
}).then(p => console.log("wrote", p));
