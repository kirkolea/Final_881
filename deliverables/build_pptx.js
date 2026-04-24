// Build project_presentation.pptx for CSE 881 project.
// Palette: Midnight Executive (1E2761 navy + CADCFC ice blue + FFFFFF white)
// with a coral accent (F96167) for highlights.

const PPTX = require(process.env.APPDATA + "/npm/node_modules/pptxgenjs");
const path = require("path");
const fs = require("fs");

const OUT   = path.resolve(__dirname, "project_presentation.pptx");
const IMG   = path.resolve(__dirname, "images");

const NAVY    = "1E2761";
const ICE     = "CADCFC";
const WHITE   = "FFFFFF";
const CORAL   = "F96167";
const DARK    = "0E1633";
const MUTED   = "6B7694";
const CARD    = "F5F7FC";

const pres = new PPTX();
pres.layout = "LAYOUT_WIDE";           // 13.33" x 7.5"
pres.author = "Atharva + Team";
pres.title  = "Quantifying Health, Fitness, and Progress Using Wearable Devices";

const W = 13.33, H = 7.5;

function bg(slide, color) {
  slide.background = { color };
}

function titleBar(slide, text) {
  slide.addText(text, {
    x: 0.6, y: 0.35, w: W - 1.2, h: 0.7,
    fontFace: "Calibri", fontSize: 28, bold: true, color: NAVY,
    valign: "middle",
  });
  slide.addShape(pres.ShapeType.rect, {
    x: 0.6, y: 1.05, w: 0.5, h: 0.05,
    fill: { color: CORAL }, line: { color: CORAL },
  });
}

function footer(slide, n) {
  slide.addText("Quantifying Health, Fitness & Progress  ·  CSE 881", {
    x: 0.6, y: H - 0.4, w: 8, h: 0.3,
    fontFace: "Calibri", fontSize: 10, color: MUTED,
  });
  slide.addText(String(n), {
    x: W - 0.9, y: H - 0.4, w: 0.4, h: 0.3,
    fontFace: "Calibri", fontSize: 10, color: MUTED, align: "right",
  });
}

// ============================================================
// SLIDE 1 — Title
// ============================================================
{
  const s = pres.addSlide();
  bg(s, NAVY);

  // decorative corner block
  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 0.3, h: H,
    fill: { color: CORAL }, line: { color: CORAL },
  });

  s.addText("CSE 881  ·  Data Mining", {
    x: 0.9, y: 1.4, w: 11, h: 0.4,
    fontFace: "Consolas", fontSize: 14, color: ICE, bold: true, charSpacing: 4,
  });

  s.addText("Quantifying Health, Fitness,\nand Progress Using Wearable Devices", {
    x: 0.9, y: 1.9, w: 11.5, h: 2.0,
    fontFace: "Calibri", fontSize: 44, bold: true, color: WHITE,
    lineSpacingMultiple: 1.05,
  });

  s.addText("An end-to-end prototype: PhysioNet ingestion · EM imputation · ML for VO₂max, body-fat %, activity · Flask dashboard", {
    x: 0.9, y: 4.2, w: 11, h: 0.9,
    fontFace: "Calibri", fontSize: 17, color: ICE, italic: true,
  });

  // team placeholder
  s.addText("Team · Atharva ·  Spring 2026", {
    x: 0.9, y: 6.5, w: 11, h: 0.4,
    fontFace: "Calibri", fontSize: 13, color: ICE,
  });
}

// ============================================================
// SLIDE 2 — Motivation / Problem Statement
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Motivation & Problem Statement");

  // Left column — problem framing
  s.addText([
    { text: "The gap.\n",
      options: { bold: true, fontSize: 18, color: NAVY } },
    { text: "Wearable devices continuously log heart rate, EDA, temperature, accelerometry — but users rarely get actionable fitness metrics back.\n\n",
      options: { fontSize: 15, color: DARK } },
    { text: "The challenge.\n",
      options: { bold: true, fontSize: 18, color: NAVY } },
    { text: "Extracting reliable indicators (VO₂max, body-fat %, session intensity) from noisy, missing, multi-rate time series and presenting them in context against clinical baselines.",
      options: { fontSize: 15, color: DARK } },
  ], { x: 0.6, y: 1.4, w: 6.5, h: 5.2, fontFace: "Calibri", paraSpaceAfter: 6 });

  // Right column — 3 stat cards stacked
  const cardY = [1.4, 3.05, 4.7];
  const cards = [
    ["46",  "subjects in the PhysioNet cohort"],
    ["3",   "activity protocols: aerobic · anaerobic · stress"],
    ["21M+", "raw sensor rows ingested into SQLite"],
  ];
  cards.forEach(([big, label], i) => {
    s.addShape(pres.ShapeType.roundRect, {
      x: 7.6, y: cardY[i], w: 5.1, h: 1.45,
      fill: { color: CARD }, line: { color: ICE, width: 1 }, rectRadius: 0.08,
    });
    s.addText(big, {
      x: 7.7, y: cardY[i] + 0.1, w: 1.8, h: 1.25,
      fontFace: "Calibri", fontSize: 40, bold: true, color: CORAL, valign: "middle",
    });
    s.addText(label, {
      x: 9.5, y: cardY[i] + 0.1, w: 3.1, h: 1.25,
      fontFace: "Calibri", fontSize: 13, color: DARK, valign: "middle",
    });
  });

  footer(s, 2);
}

// ============================================================
// SLIDE 3 — Dataset
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Dataset  ·  PhysioNet Wearable Device");

  s.addText("Hongn et al., 2025 — Wearable Device Dataset from Induced Stress and Structured Exercise Sessions.",
    { x: 0.6, y: 1.25, w: W - 1.2, h: 0.4, fontFace: "Calibri", fontSize: 13, italic: true, color: MUTED });

  // two-column table
  const leftX = 0.6, rightX = 7.0;
  const rowY  = 1.9;
  const colW  = 5.9;

  const blocks = [
    { x: leftX, title: "Demographics",
      body: "Subject ID · Age · Gender · Height · Weight · Activity history · Protocol version (V1/V2)" },
    { x: rightX, title: "Sensor streams",
      body: "HR @ 1 Hz · TEMP @ 4 Hz · EDA @ 4 Hz · BVP @ 64 Hz · ACC (x,y,z) @ 32 Hz · IBI (event-based)" },
    { x: leftX, title: "Segments",
      body: "Three sessions per subject: AEROBIC · ANAEROBIC · STRESS — stored hierarchically in CSVs" },
    { x: rightX, title: "Clinical reference (scraped)",
      body: "VO₂max norms by age / sex / sport from fitness-science repositories (inscyd.com)" },
  ];
  blocks.forEach((b, i) => {
    const y = rowY + Math.floor(i / 2) * 2.35;
    s.addShape(pres.ShapeType.roundRect, {
      x: b.x, y, w: colW, h: 2.1,
      fill: { color: CARD }, line: { color: ICE, width: 1 }, rectRadius: 0.08,
    });
    s.addText(b.title, {
      x: b.x + 0.3, y: y + 0.15, w: colW - 0.6, h: 0.45,
      fontFace: "Calibri", fontSize: 16, bold: true, color: NAVY,
    });
    s.addText(b.body, {
      x: b.x + 0.3, y: y + 0.6, w: colW - 0.6, h: 1.4,
      fontFace: "Calibri", fontSize: 13, color: DARK, valign: "top",
    });
  });

  footer(s, 3);
}

// ============================================================
// SLIDE 4 — Pipeline
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "End-to-End Pipeline");

  const steps = [
    ["1", "PhysioNet\nCSVs", "Raw files\nper subject"],
    ["2", "ETL\nSQLite", "wearable_data.db\n7 tables"],
    ["3", "EM\nImputation", "Multivariate-\nGaussian fill"],
    ["4", "Feature\nEngineering", "HR, HRV, EDA,\nACC stats"],
    ["5", "ML\nModels", "Linear, Ridge,\nRF, LogReg"],
    ["6", "Flask\nDashboard", "Explore · Models\nPredict"],
  ];

  const boxW = 1.85, boxH = 1.85, gap = 0.25;
  const totalW = steps.length * boxW + (steps.length - 1) * gap;
  const startX = (W - totalW) / 2;
  const y = 2.3;

  steps.forEach(([num, title, desc], i) => {
    const x = startX + i * (boxW + gap);

    // box
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: boxW, h: boxH,
      fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.08,
    });

    // number badge
    s.addShape(pres.ShapeType.ellipse, {
      x: x + boxW / 2 - 0.25, y: y - 0.25, w: 0.5, h: 0.5,
      fill: { color: CORAL }, line: { color: CORAL },
    });
    s.addText(num, {
      x: x + boxW / 2 - 0.25, y: y - 0.25, w: 0.5, h: 0.5,
      fontFace: "Calibri", fontSize: 16, bold: true, color: WHITE, align: "center", valign: "middle",
    });

    s.addText(title, {
      x: x + 0.1, y: y + 0.35, w: boxW - 0.2, h: 0.9,
      fontFace: "Calibri", fontSize: 15, bold: true, color: WHITE,
      align: "center", valign: "middle",
    });

    // arrow
    if (i < steps.length - 1) {
      s.addText("›", {
        x: x + boxW, y: y + boxH / 2 - 0.3, w: gap, h: 0.6,
        fontFace: "Calibri", fontSize: 28, color: MUTED, align: "center", valign: "middle",
      });
    }

    // description below
    s.addText(desc, {
      x, y: y + boxH + 0.15, w: boxW, h: 0.8,
      fontFace: "Calibri", fontSize: 11, color: DARK, align: "center",
    });
  });

  // bottom note
  s.addText("Every stage is a standalone Python module — reproducible, testable, re-runnable.", {
    x: 0.6, y: 5.9, w: W - 1.2, h: 0.5,
    fontFace: "Calibri", fontSize: 14, italic: true, color: MUTED, align: "center",
  });

  footer(s, 4);
}

// ============================================================
// SLIDE 5 — EM Imputation
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Preprocessing  ·  EM Imputation");

  // Left: description
  s.addText([
    { text: "Why EM?\n", options: { bold: true, fontSize: 17, color: NAVY }},
    { text: "Mean imputation zeroes out correlations between sensor streams. Dropping rows deletes valid demographics.\n\n",
      options: { fontSize: 14, color: DARK }},
    { text: "How it works\n", options: { bold: true, fontSize: 17, color: NAVY }},
    { text: "• Assume multivariate Gaussian (μ, Σ).\n",
      options: { fontSize: 14, color: DARK }},
    { text: "• E-step: fill missing cells with conditional means given observed cells.\n",
      options: { fontSize: 14, color: DARK }},
    { text: "• M-step: re-estimate (μ, Σ) using filled data plus covariance correction.\n",
      options: { fontSize: 14, color: DARK }},
    { text: "• Iterate until ‖Δμ‖ + ‖ΔΣ‖ < 10⁻⁴.\n",
      options: { fontSize: 14, color: DARK }},
  ], { x: 0.6, y: 1.4, w: 6.5, h: 4.8, paraSpaceAfter: 4, fontFace: "Calibri" });

  // Right: synthetic benchmark card
  s.addShape(pres.ShapeType.roundRect, {
    x: 7.4, y: 1.4, w: 5.3, h: 4.8,
    fill: { color: CARD }, line: { color: ICE, width: 1 }, rectRadius: 0.1,
  });
  s.addText("Synthetic MCAR Benchmark", {
    x: 7.6, y: 1.55, w: 5, h: 0.5,
    fontFace: "Calibri", fontSize: 16, bold: true, color: NAVY,
  });
  s.addText([
    { text: "500 samples · 3-D multivariate normal · 15% MCAR\n\n",
      options: { fontSize: 13, italic: true, color: MUTED }},
    { text: "Convergence in 6 iterations\n\n", options: { fontSize: 14, color: DARK }},
  ], { x: 7.6, y: 2.05, w: 5, h: 1.1, fontFace: "Calibri" });

  // "metric" tile
  s.addShape(pres.ShapeType.roundRect, {
    x: 7.7, y: 3.3, w: 4.9, h: 1.3,
    fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.08,
  });
  s.addText("0.76", {
    x: 7.7, y: 3.35, w: 2.0, h: 1.2,
    fontFace: "Calibri", fontSize: 40, bold: true, color: CORAL, align: "center", valign: "middle",
  });
  s.addText("MAE on held-out cells\n(lower = better)", {
    x: 9.7, y: 3.35, w: 2.8, h: 1.2,
    fontFace: "Calibri", fontSize: 13, color: ICE, valign: "middle",
  });

  s.addText("Also replaces sensor-stream spikes (|z|>5) with forward-filled rolling medians.", {
    x: 7.6, y: 4.8, w: 5, h: 1.1,
    fontFace: "Calibri", fontSize: 12, italic: true, color: MUTED,
  });

  footer(s, 5);
}

// ============================================================
// SLIDE 6 — Feature Engineering
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Feature Engineering");

  s.addText("One feature row per (subject, activity) · 51 columns · 94 rows total.", {
    x: 0.6, y: 1.25, w: W - 1.2, h: 0.4,
    fontFace: "Calibri", fontSize: 13, italic: true, color: MUTED,
  });

  const cats = [
    { title: "HR statistics",
      body: "mean · std · min · max · P25 · P75 · range · linear slope · HR reserve used" },
    { title: "Thermoregulation",
      body: "temperature mean · std · drift · P25 / P75 over session" },
    { title: "Skin conductance (EDA)",
      body: "mean / std / peaks · captures stress response" },
    { title: "Motion intensity",
      body: "accelerometer magnitude √(x²+y²+z²) — mean · std · range" },
    { title: "Heart-rate variability",
      body: "SDNN · RMSSD · mean IBI — parasympathetic proxies" },
    { title: "Demographics + encoded",
      body: "age · height · weight · gender_m · active_bin · activity one-hots" },
  ];

  const boxW = 4.0, boxH = 1.55, gapX = 0.2, gapY = 0.2;
  cats.forEach((c, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 0.6 + col * (boxW + gapX);
    const y = 2.0 + row * (boxH + gapY);
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: boxW, h: boxH,
      fill: { color: CARD }, line: { color: ICE, width: 1 }, rectRadius: 0.08,
    });
    s.addShape(pres.ShapeType.rect, {
      x, y, w: 0.12, h: boxH, fill: { color: CORAL }, line: { color: CORAL },
    });
    s.addText(c.title, {
      x: x + 0.3, y: y + 0.1, w: boxW - 0.4, h: 0.45,
      fontFace: "Calibri", fontSize: 14, bold: true, color: NAVY,
    });
    s.addText(c.body, {
      x: x + 0.3, y: y + 0.55, w: boxW - 0.4, h: boxH - 0.6,
      fontFace: "Calibri", fontSize: 12, color: DARK, valign: "top",
    });
  });

  footer(s, 6);
}

// ============================================================
// SLIDE 7 — ML Models & Targets
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Models & Target Construction");

  // Three target cards
  const targets = [
    { title: "VO₂max", formula: "15 · HR_max / HR_rest",
      detail: "Uth-Sorensen field estimate (mL/kg/min).",
      models: "Linear · Ridge · RandomForest" },
    { title: "Body-fat %", formula: "1.20·BMI + 0.23·age − 10.8·sex − 5.4",
      detail: "Deurenberg BMI-based equation.",
      models: "Linear · Ridge · RandomForest" },
    { title: "Activity class", formula: "AEROBIC / ANAEROBIC / STRESS",
      detail: "Protocol label from the dataset.",
      models: "LogReg · RandomForest" },
  ];

  const boxW = 4.0, boxH = 4.5;
  targets.forEach((t, i) => {
    const x = 0.6 + i * (boxW + 0.2);
    const y = 1.5;
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w: boxW, h: boxH,
      fill: { color: NAVY }, line: { color: NAVY }, rectRadius: 0.1,
    });
    s.addText(t.title, {
      x: x + 0.25, y: y + 0.25, w: boxW - 0.5, h: 0.6,
      fontFace: "Calibri", fontSize: 22, bold: true, color: WHITE,
    });

    s.addShape(pres.ShapeType.rect, {
      x: x + 0.25, y: y + 0.9, w: 0.8, h: 0.04,
      fill: { color: CORAL }, line: { color: CORAL },
    });

    s.addText("Target formula", {
      x: x + 0.25, y: y + 1.05, w: boxW - 0.5, h: 0.3,
      fontFace: "Consolas", fontSize: 10, bold: true, color: ICE, charSpacing: 2,
    });
    s.addText(t.formula, {
      x: x + 0.25, y: y + 1.35, w: boxW - 0.5, h: 0.8,
      fontFace: "Consolas", fontSize: 13, color: WHITE,
    });

    s.addText("Source", {
      x: x + 0.25, y: y + 2.25, w: boxW - 0.5, h: 0.3,
      fontFace: "Consolas", fontSize: 10, bold: true, color: ICE, charSpacing: 2,
    });
    s.addText(t.detail, {
      x: x + 0.25, y: y + 2.55, w: boxW - 0.5, h: 0.7,
      fontFace: "Calibri", fontSize: 13, color: WHITE,
    });

    s.addText("Models evaluated", {
      x: x + 0.25, y: y + 3.35, w: boxW - 0.5, h: 0.3,
      fontFace: "Consolas", fontSize: 10, bold: true, color: ICE, charSpacing: 2,
    });
    s.addText(t.models, {
      x: x + 0.25, y: y + 3.65, w: boxW - 0.5, h: 0.6,
      fontFace: "Calibri", fontSize: 13, color: CORAL, bold: true,
    });
  });

  s.addText("75/25 train/test split · scikit-learn · StandardScaler for linear models.", {
    x: 0.6, y: 6.2, w: W - 1.2, h: 0.4,
    fontFace: "Calibri", fontSize: 13, italic: true, color: MUTED, align: "center",
  });

  footer(s, 7);
}

// ============================================================
// SLIDE 8 — Results: Regression
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Results  ·  Regression Tasks");

  // Left — VO2max
  s.addText("VO₂max", {
    x: 0.6, y: 1.4, w: 6, h: 0.45,
    fontFace: "Calibri", fontSize: 20, bold: true, color: NAVY,
  });
  s.addText("sorted by RMSE (lower is better)", {
    x: 0.6, y: 1.85, w: 6, h: 0.3,
    fontFace: "Calibri", fontSize: 11, italic: true, color: MUTED,
  });

  // Chart
  const vo2Data = [
    { name: "VO₂max RMSE",
      labels: ["RandomForest", "Ridge", "Linear"],
      values: [1.13, 8.85, 9.61] },
  ];
  s.addChart(pres.ChartType.bar, vo2Data, {
    x: 0.6, y: 2.2, w: 6, h: 3.8,
    barDir: "bar", showValue: true,
    dataLabelColor: NAVY, dataLabelFontSize: 11, dataLabelFontBold: true,
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    chartColors: [NAVY, ICE, ICE], chartColorsOpacity: 100,
    showLegend: false,
  });

  // Right — Body Fat
  s.addText("Body-fat %", {
    x: 6.9, y: 1.4, w: 6, h: 0.45,
    fontFace: "Calibri", fontSize: 20, bold: true, color: NAVY,
  });
  s.addText("sorted by R² (higher is better)", {
    x: 6.9, y: 1.85, w: 6, h: 0.3,
    fontFace: "Calibri", fontSize: 11, italic: true, color: MUTED,
  });

  const bfData = [
    { name: "Body-fat R²",
      labels: ["RandomForest", "Linear", "Ridge"],
      values: [0.874, 0.872, 0.743] },
  ];
  s.addChart(pres.ChartType.bar, bfData, {
    x: 6.9, y: 2.2, w: 6, h: 3.8,
    barDir: "bar", showValue: true,
    dataLabelColor: NAVY, dataLabelFontSize: 11, dataLabelFontBold: true,
    catAxisLabelFontSize: 11, valAxisLabelFontSize: 10,
    chartColors: [NAVY, ICE, ICE], chartColorsOpacity: 100,
    showLegend: false,
  });

  // callout
  s.addShape(pres.ShapeType.roundRect, {
    x: 0.6, y: 6.15, w: 12.1, h: 0.7,
    fill: { color: CARD }, line: { color: ICE }, rectRadius: 0.06,
  });
  s.addText("RandomForest wins both — captures non-linear HR-rest/HR-max and demographic interactions that linear models miss.", {
    x: 0.8, y: 6.15, w: 11.9, h: 0.7,
    fontFace: "Calibri", fontSize: 13, color: DARK, valign: "middle",
  });

  footer(s, 8);
}

// ============================================================
// SLIDE 9 — Results: Classification
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Results  ·  Activity Classification");

  s.addText("3-way classification — AEROBIC · ANAEROBIC · STRESS  (94 sessions)", {
    x: 0.6, y: 1.25, w: W - 1.2, h: 0.4,
    fontFace: "Calibri", fontSize: 13, italic: true, color: MUTED,
  });

  const clsData = [
    { name: "Accuracy", labels: ["LogReg", "RandomForest"], values: [0.750, 0.708] },
    { name: "F1 macro", labels: ["LogReg", "RandomForest"], values: [0.718, 0.683] },
    { name: "ROC-AUC",  labels: ["LogReg", "RandomForest"], values: [0.819, 0.863] },
  ];
  s.addChart(pres.ChartType.bar, clsData, {
    x: 0.6, y: 1.9, w: 8.0, h: 4.7,
    barDir: "col", showValue: false, barGrouping: "clustered",
    catAxisLabelFontSize: 13, valAxisLabelFontSize: 11, valAxisMinVal: 0, valAxisMaxVal: 1,
    chartColors: [NAVY, CORAL, ICE], chartColorsOpacity: 100,
    showLegend: true, legendPos: "b", legendFontSize: 12,
  });

  // Right-side stat cards
  const cards = [
    ["0.750", "Best accuracy",    NAVY],
    ["0.718", "Best F1 (macro)",  NAVY],
    ["0.863", "Best ROC-AUC",     NAVY],
  ];
  cards.forEach(([big, lbl, c], i) => {
    const y = 1.9 + i * 1.6;
    s.addShape(pres.ShapeType.roundRect, {
      x: 8.9, y, w: 3.8, h: 1.4,
      fill: { color: c }, line: { color: c }, rectRadius: 0.08,
    });
    s.addText(big, {
      x: 9.0, y: y + 0.05, w: 1.7, h: 1.3,
      fontFace: "Calibri", fontSize: 32, bold: true, color: CORAL, align: "center", valign: "middle",
    });
    s.addText(lbl, {
      x: 10.7, y: y + 0.05, w: 2.0, h: 1.3,
      fontFace: "Calibri", fontSize: 13, color: WHITE, valign: "middle",
    });
  });

  footer(s, 9);
}

// ============================================================
// SLIDE 10 — Dataset Explorer (full screenshot)
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Prototype  ·  Dataset Explorer");

  const imgPath = path.join(IMG, "explore.png");
  const x = 0.6, y = 1.3, w = W - 1.2, h = 5.4;
  if (fs.existsSync(imgPath)) {
    s.addImage({ path: imgPath, x, y, w, h, sizing: { type: "contain", w, h } });
  } else {
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w, h,
      fill: { color: CARD }, line: { color: ICE, width: 2, dashType: "dash" }, rectRadius: 0.1,
    });
    s.addText("[ screenshot — deliverables/images/explore.png ]", {
      x, y: y + h / 2 - 0.2, w, h: 0.5,
      fontFace: "Consolas", fontSize: 14, color: MUTED, align: "center",
    });
  }

  s.addText("Live per-subject, per-activity sensor stream viewer — HR, EDA, TEMP, BVP, ACC channels, with summary statistics (mean, std, min, max) computed on the fly.", {
    x: 0.6, y: 6.75, w: W - 1.2, h: 0.45,
    fontFace: "Calibri", fontSize: 12, italic: true, color: MUTED, align: "center",
  });

  footer(s, 10);
}

// ============================================================
// SLIDE 11 — Health Estimator (full screenshot)
// ============================================================
{
  const s = pres.addSlide();
  bg(s, WHITE);
  titleBar(s, "Prototype  ·  Health Estimator");

  const imgPath = path.join(IMG, "predict.png");
  const x = 0.6, y = 1.3, w = W - 1.2, h = 5.4;
  if (fs.existsSync(imgPath)) {
    s.addImage({ path: imgPath, x, y, w, h, sizing: { type: "contain", w, h } });
  } else {
    s.addShape(pres.ShapeType.roundRect, {
      x, y, w, h,
      fill: { color: CARD }, line: { color: ICE, width: 2, dashType: "dash" }, rectRadius: 0.1,
    });
    s.addText("[ screenshot — deliverables/images/predict.png ]", {
      x, y: y + h / 2 - 0.2, w, h: 0.5,
      fontFace: "Consolas", fontSize: 14, color: MUTED, align: "center",
    });
  }

  s.addText("Runs the full trained pipeline on user-entered demographics + HR inputs and returns VO₂max, body-fat %, BMI, and activity-class probabilities.", {
    x: 0.6, y: 6.75, w: W - 1.2, h: 0.45,
    fontFace: "Calibri", fontSize: 12, italic: true, color: MUTED, align: "center",
  });

  footer(s, 11);
}

// ============================================================
// SLIDE 12 — Conclusion & Future Work
// ============================================================
{
  const s = pres.addSlide();
  bg(s, NAVY);

  s.addShape(pres.ShapeType.rect, {
    x: 0, y: 0, w: 0.3, h: H, fill: { color: CORAL }, line: { color: CORAL },
  });

  s.addText("Conclusion & Future Work", {
    x: 0.9, y: 0.7, w: 11, h: 0.8,
    fontFace: "Calibri", fontSize: 34, bold: true, color: WHITE,
  });
  s.addShape(pres.ShapeType.rect, {
    x: 0.9, y: 1.5, w: 0.6, h: 0.06, fill: { color: CORAL }, line: { color: CORAL },
  });

  // two columns
  const col = [
    { title: "What we delivered", items: [
      "Reproducible ETL into SQLite (21M+ rows).",
      "Hand-rolled multivariate-Gaussian EM imputer + sklearn sanity check.",
      "51-feature session table driving 3 ML tasks.",
      "Best: VO₂max RMSE 1.13 · Body-fat R² 0.87 · Activity F1 0.72.",
      "Flask dashboard with explore / models / predict views.",
    ]},
    { title: "Limitations & next steps", items: [
      "Only 46 subjects — small N limits generalisation.",
      "Targets are physiology proxies, not gold-standard lab values.",
      "Add subject-level cross-validation and calibration curves.",
      "Bring in external clinical datasets for real VO₂max labels.",
      "Deploy as a lightweight PWA with live wearable sync.",
    ]},
  ];
  col.forEach((c, i) => {
    const x = 0.9 + i * 6.2;
    s.addText(c.title, {
      x, y: 2.0, w: 6.0, h: 0.5,
      fontFace: "Calibri", fontSize: 18, bold: true, color: ICE,
    });
    const lines = c.items.map(t => ({ text: "·  " + t, options: { fontSize: 14, color: WHITE, paraSpaceAfter: 6 } }));
    s.addText(lines, { x, y: 2.55, w: 6.0, h: 4.2, fontFace: "Calibri" });
  });

  s.addText("Thank you — questions?", {
    x: 0.9, y: 6.7, w: 11.5, h: 0.5,
    fontFace: "Calibri", fontSize: 18, italic: true, color: CORAL,
  });
}

// ============================================================
pres.writeFile({ fileName: OUT }).then(f => {
  console.log("Wrote " + f);
}).catch(err => {
  console.error(err);
  process.exit(1);
});
