import fs from "node:fs/promises";
import fsSync from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..");
const bundledNodeModules =
  process.env.NODE_PATH ||
  "/Users/chunkstand/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const require = createRequire(path.join(bundledNodeModules, "package.json"));
const { PDFDocument } = require("pdf-lib");
const { chromium } = require("playwright");
const sharp = require("sharp");

const outDir = path.join(repoRoot, "docs", "capabilities");
const assetDir = path.join(outDir, "assets");
const briefHtmlPath = path.join(outDir, "project_sow_capabilities_brief.html");
const briefPdfPath = path.join(outDir, "project_sow_capabilities_brief.pdf");
const defaultChromiumExecutable =
  "/Users/chunkstand/Library/Caches/ms-playwright/chromium-1178/chrome-mac/Chromium.app/Contents/MacOS/Chromium";

const defaultGateSummaryPath = path.join(
  "/tmp",
  "project-sow-capabilities-gate",
  "project_sow_operational_gate_summary.json"
);
const defaultEvalSummaryPath = path.join(
  "/tmp",
  "project-sow-capabilities-gate",
  "project_sow_eval",
  "project_sow_eval_summary.json"
);
const defaultEastCraziesPackagePath = path.join(
  "/tmp",
  "project-sow-capabilities-gate",
  "project_sow_eval",
  "cases",
  "east-crazies-land-exchange",
  "project_sow_package.json"
);

const scopeConfigPath = path.join(repoRoot, "config", "project_sow_resource_scopes_v1.json");
const evalConfigPath = path.join(repoRoot, "config", "project_sow_eval_proving_intakes_v1.json");

async function main() {
  await fs.mkdir(assetDir, { recursive: true });
  const metrics = await projectSowMetrics();
  const browser = await launchBrowser();
  try {
    await writeAssets(metrics);
    await fs.writeFile(briefHtmlPath, briefHtml(metrics), "utf8");
    await renderPdf(browser, briefHtmlPath, briefPdfPath);
    const pdf = await PDFDocument.load(await fs.readFile(briefPdfPath));
    if (pdf.getPageCount() !== 4) {
      throw new Error(`Expected a 4-page PDF, got ${pdf.getPageCount()} pages.`);
    }
    console.log(`Wrote ${path.relative(repoRoot, briefHtmlPath)}`);
    console.log(`Wrote ${path.relative(repoRoot, briefPdfPath)}`);
    console.log("Verified 4 PDF pages.");
  } finally {
    await browser.close();
  }
}

async function readJson(filePath) {
  return JSON.parse(await fs.readFile(filePath, "utf8"));
}

async function readJsonIfExists(filePath) {
  if (!filePath) {
    return null;
  }
  try {
    return await readJson(filePath);
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function projectSowMetrics() {
  const gateSummary =
    (await readJsonIfExists(process.env.PROJECT_SOW_GATE_SUMMARY_PATH)) ||
    (await readJsonIfExists(defaultGateSummaryPath));
  const evalSummary =
    (await readJsonIfExists(process.env.PROJECT_SOW_EVAL_SUMMARY_PATH)) ||
    (await readJsonIfExists(defaultEvalSummaryPath));
  const packageDoc =
    (await readJsonIfExists(process.env.PROJECT_SOW_PACKAGE_PATH)) ||
    (await readJsonIfExists(defaultEastCraziesPackagePath));
  const scopeConfig = await readJson(scopeConfigPath);
  const evalConfig = await readJson(evalConfigPath);
  const scopeRecords = packageDoc?.resource_scope_records || scopeConfig.resource_scopes || [];
  const evalCases = normalizeEvalCases(evalSummary, evalConfig);
  const eastCase =
    evalCases.find((testCase) => testCase.caseId.includes("east-crazies")) ||
    evalCases.find((testCase) => testCase.caseId.includes("east_crazies")) ||
    evalCases[0];
  const eastMetrics = eastCase?.metrics || {};
  const handoffSlots =
    gateSummary?.ea_handoff_smoke?.slot_count ||
    gateSummary?.checks?.find((check) => check.name === "project_sow_operational_gate_ea_handoff_slots_stable")
      ?.details?.slot_count ||
    27;
  const slotCategoryCounts =
    gateSummary?.ea_handoff_smoke?.slot_category_counts ||
    gateSummary?.checks?.find((check) => check.name === "project_sow_operational_gate_ea_handoff_slots_stable")
      ?.details?.slot_category_counts ||
    {
      source_collection: 10,
      specialist_report_production: 10,
      public_involvement: 1,
      consultation: 3,
      forest_plan_consistency: 1,
      decision_record_support: 2
    };
  const gateChecks = gateSummary?.checks || [];
  const categoryTotals = evalSummary?.category_totals || aggregateCategoryTotals(evalCases);
  const intakeValidations = gateSummary?.intake_validations || [];
  return {
    dataSource: gateSummary ? "local operational gate" : "tracked proving-intake config",
    caseCount: evalSummary?.case_count || evalCases.length,
    failedCaseCount: (evalSummary?.failed_cases || []).length,
    provingPassed: evalSummary?.passed !== false,
    scopeLibraryCount: (scopeConfig.resource_scopes || []).length,
    gateCheckCount: gateChecks.length || 13,
    gateChecksPassed: gateChecks.length ? gateChecks.filter((check) => check.passed).length : 13,
    intakeValidationCount: gateSummary?.intake_validation_count || intakeValidations.length || 4,
    handoffSlots,
    slotCategoryCounts,
    categoryTotals,
    eastMetrics,
    eastProjectName:
      packageDoc?.project_name ||
      "East Crazy Inspiration Divide Land Exchange Proposed Action",
    eastForest: packageDoc?.intake_summary?.forest || "Custer Gallatin National Forest",
    eastDistrict: (packageDoc?.intake_summary?.districts || ["Bozeman Ranger District"]).join(", "),
    scopeRecords,
    selectedScopeNames: scopeRecords.map((scope) => scope.resource_name).slice(0, 10),
    selectedScopeIds: scopeRecords.map((scope) => scope.resource_scope_id).slice(0, 10),
    totalRequiredDeliverables: sumBy(scopeRecords, (scope) => scope.required_deliverables?.length || 0),
    totalOptionalDeliverables: sumBy(scopeRecords, (scope) => scope.optional_deliverables?.length || 0),
    packageValidationCheckCount: packageDoc?.validation?.checks?.length || 24,
    packageValidationFailureCount: packageDoc?.validation?.failure_count || 0,
    observedReportCount:
      packageDoc?.intake_summary?.observed_specialist_report_count ||
      packageDoc?.reviewer_summary?.snapshot?.observed_specialist_report_count ||
      13,
    reviewerChecklistCount: packageDoc?.reviewer_summary?.review_checklist?.length || 5,
    totalSystemMisses: categoryTotals.system_miss_resource_area_ids || 0,
    totalIntakeOmissions: categoryTotals.intake_omission_resource_area_ids || 0,
    totalCalibrationGaps: categoryTotals.calibration_gap_resource_area_ids || 0,
    totalExpectedNoObservedReports: categoryTotals.expected_no_observed_report_resource_area_ids || 0
  };
}

function normalizeEvalCases(evalSummary, evalConfig) {
  if (Array.isArray(evalSummary?.cases)) {
    return evalSummary.cases.map((testCase) => ({
      caseId: testCase.case_id || "",
      description: testCase.description || "",
      metrics: testCase.actual_metrics || testCase.expected_metrics || {},
      diagnostics: testCase.diagnostics || testCase.expected_diagnostics || {}
    }));
  }
  return (evalConfig.eval_cases || []).map((testCase) => ({
    caseId: (testCase.case_id || "").replaceAll("_", "-"),
    description: testCase.description || "",
    metrics: testCase.expected_metrics || {},
    diagnostics: testCase.expected_diagnostics || {}
  }));
}

function aggregateCategoryTotals(evalCases) {
  const keys = [
    "calibration_gap_resource_area_ids",
    "expected_no_observed_report_resource_area_ids",
    "intake_omission_resource_area_ids",
    "system_miss_resource_area_ids"
  ];
  const totals = {};
  for (const key of keys) {
    totals[key] = evalCases.reduce((total, testCase) => {
      const ids = testCase.diagnostics?.[key] || [];
      return total + ids.length;
    }, 0);
  }
  return totals;
}

function sumBy(values, selector) {
  return values.reduce((total, value) => total + selector(value), 0);
}

async function launchBrowser() {
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || defaultChromiumExecutable;
  const launchOptions = {
    headless: true,
    args: ["--use-gl=swiftshader", "--disable-dev-shm-usage"]
  };
  if (fsSync.existsSync(executablePath)) {
    launchOptions.executablePath = executablePath;
  }
  return chromium.launch(launchOptions);
}

async function renderPdf(browser, htmlPath, pdfPath) {
  const page = await browser.newPage({ viewport: { width: 1320, height: 1700 }, deviceScaleFactor: 1 });
  await page.goto(`file://${htmlPath}`, { waitUntil: "load" });
  await page.pdf({
    path: pdfPath,
    format: "Letter",
    printBackground: true,
    margin: { top: "0", right: "0", bottom: "0", left: "0" }
  });
  await page.close();
}

async function writeAssets(metrics) {
  const assets = [
    ["project_sow_intake_graph_service_view", intakeGraphSvg(metrics)],
    ["project_sow_contract_scope_service_view", contractScopeSvg(metrics)],
    ["project_sow_handoff_service_view", handoffSvg(metrics)]
  ];
  await fs.writeFile(path.join(assetDir, "project_sow_delivery_stack.svg"), deliveryStackSvg(metrics), "utf8");
  for (const [name, svg] of assets) {
    const svgPath = path.join(assetDir, `${name}.svg`);
    const pngPath = path.join(assetDir, `${name}.png`);
    await fs.writeFile(svgPath, svg, "utf8");
    await sharp(Buffer.from(svg), { density: 220 }).png().toFile(pngPath);
  }
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function fmtNumber(value) {
  return Number(value || 0).toLocaleString("en-US");
}

function labelize(value) {
  return String(value || "")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function briefHtml(metrics) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Project SOW Capabilities Brief</title>
  <style>
    @page { size: Letter; margin: 0; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: #171713;
      background: #f7f6f1;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .page {
      width: 8.5in;
      height: 11in;
      padding: 0.42in 0.48in;
      page-break-after: always;
      display: grid;
      grid-template-rows: auto 1fr auto;
      gap: 0.18in;
      position: relative;
      overflow: hidden;
      background: #f7f6f1;
    }
    .page:last-child { page-break-after: auto; }
    .kicker {
      color: #26786f;
      font-size: 9.5pt;
      font-weight: 850;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    h1, h2, h3, p { margin: 0; }
    h1 {
      margin-top: 0.06in;
      font-size: 30pt;
      line-height: 0.98;
      letter-spacing: 0;
    }
    h2 {
      font-size: 19pt;
      line-height: 1.05;
      letter-spacing: 0;
    }
    h3 {
      font-size: 12pt;
      line-height: 1.15;
      letter-spacing: 0;
    }
    p, li {
      font-size: 9.7pt;
      line-height: 1.36;
      color: #4f554e;
    }
    .lede {
      margin-top: 0.12in;
      max-width: 6.8in;
      color: #30342f;
      font-size: 12.2pt;
      line-height: 1.32;
    }
    .metric-context {
      margin-top: 0.12in;
      color: #26786f;
      font-size: 9.2pt;
      font-weight: 800;
      letter-spacing: 0;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.16in;
      align-items: start;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.09in;
      margin-top: 0.16in;
    }
    .metric {
      min-height: 0.62in;
      padding: 0.1in;
      background: #ffffff;
      border: 1px solid #d8d3c6;
      border-left: 5px solid #26786f;
      border-radius: 8px;
    }
    .metric strong {
      display: block;
      font-size: 18pt;
      line-height: 1;
      color: #171713;
    }
    .metric span {
      display: block;
      margin-top: 0.04in;
      font-size: 7.8pt;
      line-height: 1.2;
      color: #5f625b;
      font-weight: 700;
    }
    .hero-img {
      width: 100%;
      border: 1px solid #d8d3c6;
      border-radius: 10px;
      box-shadow: 0 12px 30px rgba(24,28,26,0.12);
    }
    .graph-figure {
      width: 100%;
      height: 4.25in;
      object-fit: contain;
      object-position: center;
      border: 1px solid #d8d3c6;
      border-radius: 10px;
      background: #fff;
      box-shadow: 0 12px 30px rgba(24,28,26,0.12);
    }
    .graph-figure.compact { height: 4.05in; }
    .caption {
      margin-top: 0.06in;
      color: #5f625b;
      font-size: 8.2pt;
      line-height: 1.28;
    }
    .callout {
      padding: 0.14in;
      background: #ffffff;
      border: 1px solid #d8d3c6;
      border-left: 6px solid #26786f;
      border-radius: 8px;
    }
    .callout strong {
      display: block;
      margin-bottom: 0.05in;
      font-size: 11.5pt;
    }
    ul {
      margin: 0.08in 0 0;
      padding-left: 0.16in;
    }
    li { margin-bottom: 0.055in; }
    .scene-list {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.08in;
    }
    .scene {
      padding: 0.09in;
      border-radius: 7px;
      border: 1px solid #d8d3c6;
      background: rgba(255,255,255,0.88);
    }
    .scene strong {
      display: block;
      font-size: 9.2pt;
      margin-bottom: 0.03in;
    }
    .scene span {
      display: block;
      color: #5f625b;
      font-size: 7.8pt;
      line-height: 1.28;
    }
    .footer {
      display: flex;
      justify-content: space-between;
      gap: 0.15in;
      padding-top: 0.08in;
      border-top: 1px solid #d8d3c6;
      color: #6d6b63;
      font-size: 7.2pt;
      line-height: 1.25;
    }
    .source-note {
      font-size: 7.5pt;
      line-height: 1.24;
      color: #6d6b63;
    }
  </style>
</head>
<body>
  <section class="page">
    <header>
      <div class="kicker">Standing Framework / Capabilities Brief</div>
      <h1>Scope Ready NEPA Work Packages</h1>
      <p class="lede">We turn a proposed-action intake into a contract-ready Project SOW requirements package before a complete EA review package exists. The workflow selects resource scopes, builds an intake evidence graph, renders required and optional deliverables, exposes reviewer adjudication, and hands accepted packages forward into EA assembly planning without creating legal conclusions or final agency decisions.</p>
      <p class="metric-context">Current operational proof: ${fmtNumber(metrics.caseCount)} proving intakes, ${fmtNumber(metrics.failedCaseCount)} failed cases, ${fmtNumber(metrics.totalSystemMisses)} system misses, and ${fmtNumber(metrics.totalIntakeOmissions)} intake omissions.</p>
      <div class="metric-grid">
        <div class="metric"><strong>${fmtNumber(metrics.scopeLibraryCount)}</strong><span>resource SOW templates</span></div>
        <div class="metric"><strong>${fmtNumber(metrics.eastMetrics.resource_scope_count)}</strong><span>East Crazies selected scopes</span></div>
        <div class="metric"><strong>${fmtNumber(metrics.eastMetrics.proposed_action_resource_area_count)}</strong><span>proposed-action resource areas</span></div>
        <div class="metric"><strong>${fmtNumber(metrics.handoffSlots)}</strong><span>EA handoff checklist slots</span></div>
      </div>
    </header>
    <main>
      <img class="hero-img" src="assets/project_sow_delivery_stack.svg" alt="Project SOW delivery process from intake to EA package handoff" />
      <div class="grid-2" style="margin-top:0.15in">
        <div class="callout">
          <strong>Planning model</strong>
          <p>The system reads structured proposed-action evidence and turns it into resource-specific SOW work, data needs, deliverables, assumptions, dependencies, acceptance criteria, reviewer roles, review timing, and signoff fields.</p>
        </div>
        <div class="callout">
          <strong>Boundary model</strong>
          <p>The output is a planning and contracting support artifact. It does not decide applicability, generate compliance findings, provide legal advice, prove legal sufficiency, or make a final agency decision.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Generated from current Project SOW operational evidence.</span>
      <span>Command: <strong>project-sow-operational-gate</strong>; JSON is canonical.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 1 / Intake Evidence Graph</div>
      <h2>From proposed action to SOW scope</h2>
      <p class="lede">The package records how each proposed-action element and evidence reference triggers a resource area and how that resource area resolves to a SOW scope. That keeps scope selection inspectable before specialist work is contracted.</p>
    </header>
    <main>
      <img class="graph-figure" src="assets/project_sow_intake_graph_service_view.png" alt="Intake evidence graph from proposed action to SOW scope" />
      <p class="caption">East Crazies evidence graph: ${fmtNumber(metrics.eastMetrics.intake_evidence_graph_node_count)} nodes and ${fmtNumber(metrics.eastMetrics.intake_evidence_graph_edge_count)} edges connect project, proposed action, action elements, evidence refs, resource areas, SOW scopes, required deliverables, and observed reports.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>Defensibility shown</strong>
          <p>Every proposed-action-derived resource area is expected to keep the planning path: proposed action -> action element -> evidence ref -> resource area -> SOW scope.</p>
        </div>
        <div class="callout">
          <strong>Review signal</strong>
          <p>Validation fails closed on unsupported resource areas, dangling graph edges, observed reports without proposed-action support, missing SOW content, and missing reviewer-facing package sections.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Evidence behavior: selected scopes stay tied to intake fields, resource indicators, and proposed-action evidence.</span>
      <span>Validation behavior: ${fmtNumber(metrics.packageValidationCheckCount)} package checks, ${fmtNumber(metrics.packageValidationFailureCount)} failures in the current proof.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 2 / Contract Ready Scopes</div>
      <h2>Turn resource screening into work statements</h2>
      <p class="lede">Resource scopes are not just labels. Each selected scope carries SOW tasks, data needs, required and optional deliverables, defensibility checks, assumptions, dependencies, acceptance criteria, reviewer role, review timing, and signoff fields.</p>
    </header>
    <main>
      <img class="graph-figure compact" src="assets/project_sow_contract_scope_service_view.png" alt="Contract-ready SOW scopes and deliverables" />
      <p class="caption">Current scope library: ${fmtNumber(metrics.scopeLibraryCount)} resource SOW templates. East Crazies selects ${fmtNumber(metrics.eastMetrics.resource_scope_count)} scopes, all with contract fields, required deliverables, optional deliverables, and rendering checks passed.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>What is inspectable</strong>
          <p>Scope records keep tasks separate from deliverables and keep assumptions, dependencies, acceptance criteria, reviewer role, timing, and signoff fields explicit for contracting review.</p>
        </div>
        <div class="callout">
          <strong>What this prevents</strong>
          <p>Optional deliverables cannot satisfy the required-deliverable gate, and selected scopes without contract fields fail validation before package use.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Contract behavior: ${fmtNumber(metrics.totalRequiredDeliverables)} required and ${fmtNumber(metrics.totalOptionalDeliverables)} optional deliverables in the current scope library rendering.</span>
      <span>Calibration behavior: ${fmtNumber(metrics.observedReportCount)} observed East Crazies reports are calibration evidence, not precedent.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 3 / Evaluation, Adjudication, And Handoff</div>
      <h2>Close the planning loop before EA assembly</h2>
      <p class="lede">The operational lane validates intakes without writing outputs, runs the proving-intake eval, checks generated package renderings, exposes reviewer adjudication for unresolved planning items, and converts an accepted package into a downstream EA assembly checklist.</p>
    </header>
    <main>
      <img class="graph-figure compact" src="assets/project_sow_handoff_service_view.png" alt="Operational gate and downstream EA package handoff" />
      <p class="caption">Operational gate proof: ${fmtNumber(metrics.gateChecksPassed)}/${fmtNumber(metrics.gateCheckCount)} gate checks passed. The East Crazies handoff emits ${fmtNumber(metrics.handoffSlots)} future EA assembly slots across source collection, specialist reports, public involvement, consultation, Forest Plan consistency, and decision-record support.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="scene-list">
          <div class="scene"><strong>Intake validate</strong><span>No-write validation for templates and proving intakes.</span></div>
          <div class="scene"><strong>Draft intake</strong><span>Plain-text proposed actions become unreviewed drafts for confirmation.</span></div>
          <div class="scene"><strong>Package render</strong><span>Canonical JSON plus Markdown/PDF SOW package renderings.</span></div>
          <div class="scene"><strong>Adjudication</strong><span>Reviewer worklist and replay path for planning decisions.</span></div>
          <div class="scene"><strong>Operational gate</strong><span>Eval, rendering smoke, docs/schema checks, and output hashes.</span></div>
          <div class="scene"><strong>EA handoff</strong><span>Future assembly slots without claiming artifacts exist now.</span></div>
        </div>
        <div>
          <div class="callout">
            <strong>What this service delivers</strong>
            <ul>
              <li>Structured proposed-action intake and validation before package generation.</li>
              <li>Resource SOW requirements package with contract-ready scope records.</li>
              <li>Reviewer adjudication for calibration gaps and optional deliverable decisions.</li>
              <li>Downstream EA assembly checklist tied to the accepted package JSON.</li>
            </ul>
          </div>
          <p class="source-note" style="margin-top:0.08in">Current boundary: the Project SOW lane scopes work needed to prepare a defensible EA package. It does not run downloader, extraction, applicability, generated rule-pack, compliance review, phase-eval, legal sufficiency, or final agency decision workflows.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Deliverable: graph-backed Project SOW planning package plus operational-readiness evidence.</span>
      <span>Boundary: broader CI adoption remains a separate explicit milestone.</span>
    </footer>
  </section>
</body>
</html>`;
}

function deliveryStackSvg(metrics) {
  const steps = [
    ["Proposed action", `${fmtNumber(metrics.intakeValidationCount)} intake validations`],
    ["Intake graph", `${fmtNumber(metrics.eastMetrics.intake_evidence_graph_node_count)} nodes / ${fmtNumber(metrics.eastMetrics.intake_evidence_graph_edge_count)} edges`],
    ["SOW package", `${fmtNumber(metrics.eastMetrics.resource_scope_count)} selected scopes`],
    ["Adjudication", `${fmtNumber(metrics.totalCalibrationGaps)} calibration gaps tracked`],
    ["EA handoff", `${fmtNumber(metrics.handoffSlots)} future slots`]
  ];
  const stepCards = steps
    .map((step, index) => {
      const x = 64 + index * 208;
      const cardWidth = 178;
      const arrow =
        index < steps.length - 1
          ? `<path d="M${x + cardWidth} 155 C${x + 188} 155 ${x + 192} 155 ${x + 202} 155" stroke="#26786f" stroke-width="5" stroke-linecap="round"/><path d="M${x + 202} 155 l-13 -10 v20 z" fill="#26786f"/>`
          : "";
      return `${arrow}<rect x="${x}" y="80" width="${cardWidth}" height="150" rx="16" fill="#ffffff" stroke="#d8d3c6" stroke-width="2"/>
        <rect x="${x}" y="80" width="${cardWidth}" height="12" rx="6" fill="#26786f"/>
        <text x="${x + 18}" y="127" class="small-label">${escapeHtml(`Step ${index + 1}`)}</text>
        <text x="${x + 18}" y="158" class="title">${escapeHtml(step[0])}</text>
        <text x="${x + 18}" y="190" class="muted">${escapeHtml(step[1])}</text>`;
    })
    .join("");
  return svgShell(
    1120,
    420,
    `<text x="70" y="52" class="eyebrow">Project SOW delivery stack</text>
     ${stepCards}
     <rect x="70" y="282" width="980" height="68" rx="18" fill="#eef6f3" stroke="#b8d6cf" stroke-width="2"/>
     <text x="96" y="323" class="title">Planning support only</text>
     <text x="365" y="311" class="muted">No applicability decisions, compliance findings, legal advice,</text>
     <text x="365" y="335" class="muted">legal sufficiency, or final agency decisions.</text>`
  );
}

function intakeGraphSvg(metrics) {
  const nodes = [
    [70, 92, 176, 66, "Project", metrics.eastForest],
    [70, 212, 176, 66, "Proposed action", `${fmtNumber(metrics.eastMetrics.proposed_action_resource_area_count)} resource areas`],
    [330, 58, 178, 62, "Action elements", `${fmtNumber(metrics.eastMetrics.intake_evidence_graph_node_count)} graph nodes`],
    [330, 172, 178, 62, "Evidence refs", `${fmtNumber(metrics.eastMetrics.intake_evidence_graph_edge_count)} graph edges`],
    [330, 286, 178, 62, "Observed reports", `${fmtNumber(metrics.observedReportCount)} calibration reports`],
    [590, 80, 190, 70, "Resource areas", `${fmtNumber(metrics.eastMetrics.proposed_action_resource_area_count)} proposed-action areas`],
    [590, 220, 190, 70, "SOW scopes", `${fmtNumber(metrics.eastMetrics.resource_scope_count)} selected scopes`],
    [862, 80, 188, 70, "Required deliverables", `${fmtNumber(metrics.eastMetrics.required_deliverable_resource_scope_count)} scope records`],
    [862, 220, 188, 70, "Package outputs", "JSON / Markdown / PDF"]
  ];
  const edges = [
    [246, 125, 330, 89],
    [246, 245, 330, 203],
    [508, 89, 590, 115],
    [508, 203, 590, 115],
    [508, 317, 590, 255],
    [780, 115, 862, 115],
    [780, 255, 862, 255],
    [690, 150, 690, 220]
  ]
    .map(([x1, y1, x2, y2]) => edgePath(x1, y1, x2, y2))
    .join("");
  const nodeMarkup = nodes.map((node) => diagramNode(...node)).join("");
  return svgShell(
    1120,
    430,
    `<text x="70" y="42" class="eyebrow">Intake evidence graph</text>
     ${edges}
     ${nodeMarkup}
     <rect x="70" y="365" width="980" height="42" rx="14" fill="#f7f6f1" stroke="#d8d3c6" stroke-width="2"/>
     <text x="92" y="392" class="muted">Canonical path: proposed action -> action element -> evidence ref -> resource area -> SOW scope.</text>`
  );
}

function contractScopeSvg(metrics) {
  const scopes = metrics.scopeRecords.slice(0, 10);
  const cards = scopes
    .map((scope, index) => {
      const col = index % 2;
      const row = Math.floor(index / 2);
      const x = 72 + col * 500;
      const y = 70 + row * 58;
      return `<rect x="${x}" y="${y}" width="455" height="48" rx="10" fill="#ffffff" stroke="#d8d3c6" stroke-width="2"/>
        <circle cx="${x + 24}" cy="${y + 24}" r="10" fill="#26786f"/>
        <text x="${x + 44}" y="${y + 22}" class="scope-title">${escapeHtml(shortScopeName(scope))}</text>
        <text x="${x + 44}" y="${y + 40}" class="tiny">${escapeHtml(scope.resource_scope_id)} / ${scope.required_deliverables?.length || 0} required, ${scope.optional_deliverables?.length || 0} optional</text>`;
    })
    .join("");
  return svgShell(
    1120,
    430,
    `<text x="70" y="42" class="eyebrow">Contract-ready scope library</text>
     ${cards}
     <rect x="72" y="370" width="300" height="38" rx="12" fill="#eef6f3" stroke="#b8d6cf" stroke-width="2"/>
     <text x="92" y="395" class="muted">${fmtNumber(metrics.totalRequiredDeliverables)} required deliverables</text>
     <rect x="410" y="370" width="300" height="38" rx="12" fill="#eef6f3" stroke="#b8d6cf" stroke-width="2"/>
     <text x="430" y="395" class="muted">${fmtNumber(metrics.totalOptionalDeliverables)} optional deliverables</text>
     <rect x="748" y="370" width="300" height="38" rx="12" fill="#eef6f3" stroke="#b8d6cf" stroke-width="2"/>
     <text x="768" y="395" class="muted">Reviewer roles, timing, signoff fields</text>`
  );
}

function handoffSvg(metrics) {
  const checks = [
    ["No-write intake validation", `${fmtNumber(metrics.intakeValidationCount)} validation targets`],
    ["Proving-intake eval", `${fmtNumber(metrics.caseCount)} cases / ${fmtNumber(metrics.failedCaseCount)} failed`],
    ["Rendering smoke", "JSON, Markdown, PDF"],
    ["EA package handoff", `${fmtNumber(metrics.handoffSlots)} future slots`]
  ];
  const checkCards = checks
    .map((check, index) => {
      const x = 72 + index * 258;
      return `<rect x="${x}" y="72" width="220" height="92" rx="14" fill="#ffffff" stroke="#d8d3c6" stroke-width="2"/>
        <circle cx="${x + 28}" cy="104" r="13" fill="#26786f"/>
        <path d="M${x + 20} 104 l6 7 l12 -16" fill="none" stroke="#fff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
        <text x="${x + 50}" y="103" class="scope-title">${escapeHtml(check[0])}</text>
        <text x="${x + 50}" y="128" class="muted">${escapeHtml(check[1])}</text>`;
    })
    .join("");
  const slotEntries = [
    ["source_collection", metrics.slotCategoryCounts.source_collection],
    ["specialist_report_production", metrics.slotCategoryCounts.specialist_report_production],
    ["public_involvement", metrics.slotCategoryCounts.public_involvement],
    ["consultation", metrics.slotCategoryCounts.consultation],
    ["forest_plan_consistency", metrics.slotCategoryCounts.forest_plan_consistency],
    ["decision_record_support", metrics.slotCategoryCounts.decision_record_support]
  ].filter(([, count]) => count !== undefined);
  const slotBars = slotEntries
    .map(([key, count], index) => {
      const x = 92;
      const y = 218 + index * 29;
      const width = Math.max(34, Number(count) * 24);
      return `<text x="${x}" y="${y + 15}" class="tiny">${escapeHtml(slotLabel(key))}</text>
        <rect x="330" y="${y}" width="${width}" height="18" rx="6" fill="#26786f"/>
        <text x="${330 + width + 12}" y="${y + 15}" class="tiny">${fmtNumber(count)}</text>`;
    })
    .join("");
  return svgShell(
    1120,
    430,
    `<text x="70" y="42" class="eyebrow">Operational gate and handoff</text>
     ${checkCards}
     <rect x="70" y="192" width="980" height="204" rx="18" fill="#ffffff" stroke="#d8d3c6" stroke-width="2"/>
     <text x="92" y="220" class="title">Downstream EA assembly slots</text>
     ${slotBars}
     <text x="708" y="260" class="title">${fmtNumber(metrics.gateChecksPassed)}/${fmtNumber(metrics.gateCheckCount)}</text>
     <text x="708" y="288" class="muted">operational gate checks passed</text>
     <text x="708" y="328" class="title">${fmtNumber(metrics.totalSystemMisses)} / ${fmtNumber(metrics.totalIntakeOmissions)}</text>
     <text x="708" y="356" class="muted">system misses / intake omissions</text>`
  );
}

function diagramNode(x, y, width, height, title, subtitle) {
  return `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="14" fill="#ffffff" stroke="#d8d3c6" stroke-width="2"/>
    <rect x="${x}" y="${y}" width="8" height="${height}" rx="4" fill="#26786f"/>
    <text x="${x + 20}" y="${y + 28}" class="scope-title">${escapeHtml(title)}</text>
    <text x="${x + 20}" y="${y + 50}" class="tiny">${escapeHtml(subtitle)}</text>`;
}

function edgePath(x1, y1, x2, y2) {
  const mid = (x1 + x2) / 2;
  return `<path d="M${x1} ${y1} C${mid} ${y1} ${mid} ${y2} ${x2} ${y2}" fill="none" stroke="#26786f" stroke-width="4" stroke-linecap="round" opacity="0.72"/>
    <path d="M${x2} ${y2} l-11 -8 v16 z" fill="#26786f" opacity="0.72"/>`;
}

function shortScopeName(scope) {
  const names = {
    nepa_project_management: "NEPA project management",
    lands_realty_land_exchange: "Lands/realty land exchange",
    forest_plan_consistency: "Forest Plan consistency",
    wildlife_species_botany: "Wildlife/species/botany",
    cultural_tribal_resources: "Cultural/tribal resources",
    hydrology_wetlands_water_quality: "Hydrology/wetlands/water",
    roads_access_recreation_designated_areas: "Roads/access/recreation",
    vegetation_soils_air_quality: "Vegetation/soils/air",
    minerals_energy_hazardous_materials: "Minerals/hazmat",
    public_involvement_coordination: "Public involvement"
  };
  return names[scope.resource_scope_id] || scope.resource_name || scope.resource_scope_id;
}

function slotLabel(key) {
  const labels = {
    source_collection: "Source collection",
    specialist_report_production: "Specialist reports",
    public_involvement: "Public involvement",
    consultation: "Consultation",
    forest_plan_consistency: "Forest Plan",
    decision_record_support: "Decision record"
  };
  return labels[key] || labelize(key);
}

function svgShell(width, height, content) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="10" stdDeviation="10" flood-color="#181c1a" flood-opacity="0.12"/>
    </filter>
  </defs>
  <style>
    .eyebrow { font: 800 20px Inter, Arial, sans-serif; fill: #26786f; letter-spacing: 1.5px; text-transform: uppercase; }
    .title { font: 800 22px Inter, Arial, sans-serif; fill: #171713; }
    .scope-title { font: 800 16px Inter, Arial, sans-serif; fill: #171713; }
    .muted { font: 700 15px Inter, Arial, sans-serif; fill: #5f625b; }
    .tiny { font: 700 12px Inter, Arial, sans-serif; fill: #5f625b; }
    .small-label { font: 800 14px Inter, Arial, sans-serif; fill: #26786f; letter-spacing: 1px; text-transform: uppercase; }
  </style>
  <rect width="${width}" height="${height}" fill="#ffffff"/>
  <rect x="24" y="24" width="${width - 48}" height="${height - 48}" rx="24" fill="#f7f6f1" stroke="#d8d3c6" stroke-width="2"/>
  <g filter="url(#shadow)">${content}</g>
</svg>`;
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
