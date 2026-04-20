// Build the data-overview deck for the News Sentiment & Market Dynamics project.
// Palette: Ocean Gradient (finance feel). Dark bookend slides + light content.

const pptxgen = require("pptxgenjs");
const path = require("path");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.33 x 7.5

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
};

const F = { head: "Georgia", body: "Calibri" };

// ---------------------------------------------------------------------------
// Slide 1 — Title
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.mid };
  // Accent vertical bar on left
  s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: C.accent } });

  s.addText("THE DATA", {
    x: 0.9, y: 1.9, w: 8, h: 0.5,
    fontFace: F.body, fontSize: 14, color: C.accent, bold: true, charSpacing: 8,
  });
  s.addText("News Sentiment &\nMarket Dynamics", {
    x: 0.9, y: 2.4, w: 11, h: 2.2,
    fontFace: F.head, fontSize: 54, color: C.white, bold: true,
    paraSpaceAfter: 0,
  });
  s.addText("Bitcoin and Gold, July–December 2024", {
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
// Slide 2 — Three datasets at a glance
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
    // Card
    s.addShape("roundRect", {
      x, y: 1.7, w, h: 4.8,
      fill: { color: C.ice },
      line: { color: C.line, width: 0.5 },
      rectRadius: 0.1,
    });
    // Color stripe top
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

  // Footer rule
  s.addShape("line", {
    x: 0.6, y: 6.9, w: 12.2, h: 0, line: { color: C.line, width: 0.75 },
  });
  s.addText("Source: public APIs (crypto aggregators, yfinance) + curated news corpus",
    { x: 0.6, y: 6.98, w: 12.2, h: 0.35,
      fontFace: F.body, fontSize: 11, color: C.muted });
}

// ---------------------------------------------------------------------------
// Slide 3 — News corpus breakdown
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

  // LEFT: tag breakdown cards
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
    // Horizontal bar proportional
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

  // Callout below tag bars
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

  // RIGHT: top sources
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
// Slide 4 — Bitcoin price data
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Bitcoin price data", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("4-hour OHLCV candles resampled to daily, matched to sentiment calendar",
    { x: 0.6, y: 1.05, w: 12.2, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.muted, italic: true });

  // LEFT: spec table
  const rows = [
    ["Source",      "crypto aggregator API"],
    ["Granularity", "4-hour candles (raw) → daily (modeled)"],
    ["Columns",     "Open, High, Low, Close, Volume"],
    ["Raw rows",    "1,098"],
    ["Daily rows",  "183 (24/7 market, no gaps)"],
    ["Window",      "2024-07-01 → 2024-12-30"],
  ];
  const tblX = 0.6, tblY = 1.8;
  rows.forEach((r, i) => {
    const y = tblY + i * 0.55;
    const bg = i % 2 === 0 ? C.ice : C.white;
    s.addShape("rect", {
      x: tblX, y, w: 6.6, h: 0.55, fill: { color: bg }, line: { width: 0 },
    });
    s.addText(r[0], {
      x: tblX + 0.15, y, w: 2.3, h: 0.55,
      fontFace: F.body, fontSize: 13, color: C.deep, bold: true, valign: "middle",
    });
    s.addText(r[1], {
      x: tblX + 2.55, y, w: 4, h: 0.55,
      fontFace: F.body, fontSize: 13, color: C.text, valign: "middle",
    });
  });

  // RIGHT: resample diagram
  s.addText("Resample pipeline", {
    x: 7.5, y: 1.8, w: 5.3, h: 0.4,
    fontFace: F.body, fontSize: 14, color: C.mid, bold: true, charSpacing: 4,
  });
  const steps = [
    { t: "6 candles per day", s: "4h × 6 = 24h" },
    { t: "Aggregate per date", s: "open=first, close=last\nhigh=max, low=min\nvolume=sum" },
    { t: "Daily return",       s: "(closeₜ − closeₜ₋₁) / closeₜ₋₁" },
    { t: "Spike label",        s: "|return| > 2σ rolling std(30d)" },
  ];
  steps.forEach((st, i) => {
    const y = 2.3 + i * 1.02;
    s.addShape("roundRect", {
      x: 7.5, y, w: 5.3, h: 0.82,
      fill: { color: C.white },
      line: { color: C.teal, width: 1.2 },
      rectRadius: 0.08,
    });
    s.addShape("ellipse", {
      x: 7.65, y: y + 0.17, w: 0.5, h: 0.5,
      fill: { color: C.teal }, line: { width: 0 },
    });
    s.addText(String(i + 1), {
      x: 7.65, y: y + 0.17, w: 0.5, h: 0.5,
      fontFace: F.body, fontSize: 15, color: C.white, bold: true,
      align: "center", valign: "middle",
    });
    s.addText(st.t, {
      x: 8.3, y: y + 0.05, w: 4.4, h: 0.35,
      fontFace: F.body, fontSize: 13, color: C.mid, bold: true,
    });
    s.addText(st.s, {
      x: 8.3, y: y + 0.37, w: 4.4, h: 0.45,
      fontFace: F.body, fontSize: 11, color: C.muted,
    });
  });
}

// ---------------------------------------------------------------------------
// Slide 5 — Gold ETF data
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("Gold ETF (GLD) data", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("Daily OHLCV for a safe-haven asset — contrast with Bitcoin's 24/7 market",
    { x: 0.6, y: 1.05, w: 12.2, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.muted, italic: true });

  // LEFT: big number callout
  s.addShape("roundRect", {
    x: 0.6, y: 1.8, w: 5.5, h: 4.9,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.12,
  });
  s.addText("128", {
    x: 0.6, y: 2.2, w: 5.5, h: 1.8,
    fontFace: F.head, fontSize: 130, color: C.accent, bold: true, align: "center",
  });
  s.addText("trading days", {
    x: 0.6, y: 4.1, w: 5.5, h: 0.5,
    fontFace: F.body, fontSize: 20, color: C.ice, align: "center", italic: true,
  });
  s.addShape("line", {
    x: 2.1, y: 4.8, w: 2.5, h: 0, line: { color: C.accent, width: 1.5 },
  });
  s.addText("55 days fewer than Bitcoin\nbecause markets close on weekends.",
    { x: 0.9, y: 5.0, w: 4.9, h: 1.0,
      fontFace: F.body, fontSize: 14, color: C.white, align: "center" });

  // RIGHT: characteristics
  const info = [
    { h: "Source",      b: "Yahoo Finance historical CSV" },
    { h: "Columns",     b: "Date, Price (close), Open, High, Low, Vol., Change %" },
    { h: "Price range", b: "$218 – $253 across Jul–Dec 2024" },
    { h: "Alignment",   b: "Inner-joined with daily sentiment → 128 modeling rows for GLD" },
    { h: "Why gold?",   b: "Safe-haven asset. Hypothesis: responds to political news, unlike BTC." },
  ];
  info.forEach((row, i) => {
    const y = 1.85 + i * 1.0;
    s.addShape("ellipse", {
      x: 6.4, y: y + 0.1, w: 0.3, h: 0.3,
      fill: { color: C.accent }, line: { width: 0 },
    });
    s.addText(row.h, {
      x: 6.8, y, w: 6, h: 0.35,
      fontFace: F.body, fontSize: 13, color: C.deep, bold: true, charSpacing: 4,
    });
    s.addText(row.b, {
      x: 6.8, y: y + 0.36, w: 6, h: 0.6,
      fontFace: F.body, fontSize: 13, color: C.text,
    });
  });
}

// ---------------------------------------------------------------------------
// Slide 6 — Sentiment pipeline (how raw headlines become features)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.white };
  s.addText("From headlines to daily features", {
    x: 0.6, y: 0.35, w: 12.2, h: 0.7,
    fontFace: F.head, fontSize: 32, color: C.mid, bold: true,
  });
  s.addText("Fine-tuned FinancialBERT scores every headline; we aggregate into three parallel daily streams",
    { x: 0.6, y: 1.05, w: 12.2, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.muted, italic: true });

  // 5-step horizontal flow
  const steps = [
    { n: "1", t: "Clean & dedupe",   s: "21,005 →\n20,939 unique" },
    { n: "2", t: "Fine-tune BERT",   s: "Weak-supervision\nwith BART-MNLI" },
    { n: "3", t: "Score all",        s: "pos / neg prob\nper headline" },
    { n: "4", t: "Daily aggregate",  s: "Mean · var ·\ncount · shares" },
    { n: "5", t: "Split by tag",     s: "all / financial /\npolitical streams" },
  ];
  const startX = 0.6, boxW = 2.45, gap = 0.08, top = 2.1;
  steps.forEach((st, i) => {
    const x = startX + i * (boxW + gap);
    s.addShape("roundRect", {
      x, y: top, w: boxW, h: 2.3,
      fill: { color: C.ice },
      line: { color: C.line, width: 0.5 },
      rectRadius: 0.1,
    });
    s.addShape("ellipse", {
      x: x + (boxW - 0.6) / 2, y: top + 0.25, w: 0.6, h: 0.6,
      fill: { color: C.deep }, line: { width: 0 },
    });
    s.addText(st.n, {
      x: x + (boxW - 0.6) / 2, y: top + 0.25, w: 0.6, h: 0.6,
      fontFace: F.head, fontSize: 22, color: C.white, bold: true,
      align: "center", valign: "middle",
    });
    s.addText(st.t, {
      x: x + 0.15, y: top + 1.0, w: boxW - 0.3, h: 0.45,
      fontFace: F.body, fontSize: 15, color: C.mid, bold: true, align: "center",
    });
    s.addText(st.s, {
      x: x + 0.15, y: top + 1.48, w: boxW - 0.3, h: 0.75,
      fontFace: F.body, fontSize: 12, color: C.muted, align: "center",
    });
    // Arrow
    if (i < steps.length - 1) {
      const ax = x + boxW + 0.005;
      s.addShape("triangle", {
        x: ax, y: top + 1.05, w: 0.07, h: 0.2,
        fill: { color: C.teal }, line: { width: 0 },
        rotate: 90,
      });
    }
  });

  // Feature vector summary
  s.addShape("roundRect", {
    x: 0.6, y: 4.7, w: 12.2, h: 2.0,
    fill: { color: C.mid }, line: { width: 0 }, rectRadius: 0.1,
  });
  s.addText("Output: 183 days × 15 sentiment features", {
    x: 0.9, y: 4.85, w: 11.5, h: 0.5,
    fontFace: F.head, fontSize: 22, color: C.white, bold: true,
  });
  const cols = [
    { t: "all_*",      s: "All headlines\ncombined" },
    { t: "fin_*",      s: "Only financial-\ntagged headlines" },
    { t: "pol_*",      s: "Only political-\ntagged headlines" },
  ];
  cols.forEach((c, i) => {
    const x = 0.9 + i * 4.0;
    s.addText(c.t, {
      x, y: 5.45, w: 3.8, h: 0.4,
      fontFace: "Consolas", fontSize: 16, color: C.accent, bold: true,
    });
    s.addText(c.s, {
      x, y: 5.85, w: 3.8, h: 0.7,
      fontFace: F.body, fontSize: 13, color: C.ice,
    });
  });
  s.addText("Each stream provides: mean · variance · headline count · positive share · negative share",
    { x: 0.9, y: 6.35, w: 11.5, h: 0.35,
      fontFace: F.body, fontSize: 12, color: C.ice, italic: true });
}

// ---------------------------------------------------------------------------
// Slide 7 — Merged daily dataset (closing, dark)
// ---------------------------------------------------------------------------
{
  const s = pres.addSlide();
  s.background = { color: C.mid };
  s.addShape("rect", { x: 0, y: 0, w: 0.35, h: 7.5, fill: { color: C.accent } });

  s.addText("What enters the model", {
    x: 0.9, y: 0.5, w: 12, h: 0.8,
    fontFace: F.head, fontSize: 36, color: C.white, bold: true,
  });
  s.addText("Single daily table, one row per date, joined on July–December 2024 calendar",
    { x: 0.9, y: 1.3, w: 12, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.ice, italic: true });

  // Feature columns visualisation
  const groups = [
    { t: "Sentiment (x3 streams)",
      items: ["all_sent_mean, all_sent_var, all_headline_count,",
              "all_pos_share, all_neg_share  (same for fin_, pol_)",
              "+ lag1, rolling 3d/7d means, momentum"] },
    { t: "BTC market",
      items: ["btc_open, btc_high, btc_low, btc_close, btc_volume",
              "btc_return, btc_abs_return",
              "btc_spike (target), btc_surge"] },
    { t: "GLD market",
      items: ["gld_open, gld_high, gld_low, gld_close, gld_volume",
              "gld_return, gld_abs_return",
              "gld_spike (target), gld_surge"] },
  ];

  groups.forEach((g, i) => {
    const y = 2.0 + i * 1.55;
    s.addShape("rect", {
      x: 0.9, y, w: 0.06, h: 1.3, fill: { color: C.accent }, line: { width: 0 },
    });
    s.addText(g.t, {
      x: 1.1, y, w: 6, h: 0.4,
      fontFace: F.body, fontSize: 15, color: C.accent, bold: true, charSpacing: 4,
    });
    s.addText(g.items.join("\n"), {
      x: 1.1, y: y + 0.45, w: 11.5, h: 0.9,
      fontFace: "Consolas", fontSize: 12, color: C.ice,
      paraSpaceAfter: 2,
    });
  });

  // Final stat callout
  s.addShape("roundRect", {
    x: 0.9, y: 6.7, w: 11.5, h: 0.6,
    fill: { color: C.deep }, line: { width: 0 }, rectRadius: 0.08,
  });
  s.addText("→  Final shape: 183 rows (BTC) / 128 rows (GLD) × ~108 engineered columns",
    { x: 1.1, y: 6.7, w: 11.3, h: 0.6,
      fontFace: F.body, fontSize: 15, color: C.white, bold: true, valign: "middle" });
}

// ---------------------------------------------------------------------------
pres.writeFile({
  fileName: path.join(__dirname, "artifacts", "slides_data_overview.pptx"),
}).then(p => console.log("wrote", p));
