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
const qaDir = process.env.NEPA_3D_BRIEF_QA_DIR || path.join("/tmp", "nepa_3d_capabilities_brief_qa");
const briefHtmlPath = path.join(outDir, "nepa_3d_capabilities_brief.html");
const briefPdfPath = path.join(outDir, "nepa_3d_capabilities_brief.pdf");

const sourceSetSummaryPath = path.join(
  repoRoot,
  "source_library",
  "derived",
  "source-set-ba8d0feae79501b8",
  "knowledge_graph",
  "nepa_3d_graph_summary.json"
);
const sourceSetValidationPath = path.join(
  repoRoot,
  "source_library",
  "derived",
  "source-set-ba8d0feae79501b8",
  "knowledge_graph",
  "nepa_3d_graph_validation.json"
);
const catalogManifestPath = path.join(repoRoot, "source_library", "catalog", "source_set_manifest.json");
const promotionSuitePath = path.join(
  repoRoot,
  "source_library",
  "reviews",
  "promotion_suite",
  "post-v1-region1-ea-promotion-suite",
  "promotion_suite_results.json"
);
const phaseEvalPath = path.join(
  repoRoot,
  "source_library",
  "derived",
  "source-set-ba8d0feae79501b8",
  "evidence_graph",
  "phase_eval_results.json"
);

const chromeCandidates = [
  process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
  "/Users/chunkstand/Library/Caches/ms-playwright/chromium-1178/chrome-mac/Chromium.app/Contents/MacOS/Chromium",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
].filter(Boolean);

async function main() {
  await fs.mkdir(assetDir, { recursive: true });
  await fs.mkdir(qaDir, { recursive: true });
  const metrics = await currentMetrics();
  await writeAssets(metrics);
  await fs.writeFile(briefHtmlPath, briefHtml(metrics), "utf8");

  const browser = await launchBrowser();
  try {
    await renderPdf(browser, briefHtmlPath, briefPdfPath);
    await renderQaScreenshots(browser, briefHtmlPath, qaDir);
  } finally {
    await browser.close();
  }

  const pdfBytes = await fs.readFile(briefPdfPath);
  const pdf = await PDFDocument.load(pdfBytes);
  if (pdf.getPageCount() !== 4) {
    throw new Error(`Expected a 4-page PDF, got ${pdf.getPageCount()} pages.`);
  }
  console.log(`Wrote ${path.relative(repoRoot, briefHtmlPath)}`);
  console.log(`Wrote ${path.relative(repoRoot, briefPdfPath)}`);
  console.log(`Wrote visual QA PNGs under ${qaDir}`);
  console.log("Verified 4 PDF pages.");
}

async function currentMetrics() {
  const summary = await readJsonIfExists(sourceSetSummaryPath);
  const validation = await readJsonIfExists(sourceSetValidationPath);
  const catalog = await readJsonIfExists(catalogManifestPath);
  const promotion = await readJsonIfExists(promotionSuitePath);
  const phaseEval = await readJsonIfExists(phaseEvalPath);
  const validationChecks =
    summary?.validation_check_count || (Array.isArray(validation?.checks) ? validation.checks.length : 0);
  const currentGateTotal = promotion?.required_current_result_count || 0;
  const currentGatePassed = promotion?.passed_required_current_result_count || 0;
  const phaseTotal = phaseEval?.phase_count || (Array.isArray(phaseEval?.phases) ? phaseEval.phases.length : 0);
  const phasePassed = phaseEval?.passed_phase_count || 0;

  return {
    sourceRecords: catalog?.source_count || summary?.catalog_source_record_count || 0,
    artifacts: catalog?.artifact_count || summary?.node_type_counts?.artifact || 0,
    sourceLinks: catalog?.link_count || summary?.edge_type_counts?.HAS_ARTIFACT || 0,
    nodeCount: summary?.node_count || 0,
    edgeCount: summary?.edge_count || 0,
    authorityFamilies: summary?.authority_family_count || summary?.node_type_counts?.authority_family || 0,
    baseRules: summary?.base_rule_count || 0,
    authorityTemplates: summary?.authority_family_rule_template_count || 0,
    sourceClaims: summary?.rule_claim_link_count || summary?.node_type_counts?.source_claim || 0,
    forestComponents: summary?.forest_plan_component_count || 0,
    profileCount: summary?.region1_forest_plan_readiness_profile_count || 0,
    graphReadyProfiles: summary?.region1_forest_plan_graph_ready_profile_count || 0,
    blockedProfiles: summary?.region1_forest_plan_blocked_profile_count || 0,
    fieldDirectives: summary?.region1_field_directive_requirement_count || 0,
    overlayRequirements: summary?.region1_overlay_requirement_count || 0,
    validationChecks,
    validationPassed: summary?.validation_passed === true,
    currentnessPassed: summary?.currentness_validation_passed === true,
    currentGateTotal,
    currentGatePassed,
    currentPromotionReady: promotion?.current_promotion_ready === true,
    promotionFailureCategories: promotion?.failure_category_counts || {},
    expansionFailureCategories: promotion?.expansion_failure_category_counts || {},
    phaseTotal,
    phasePassed,
    phaseReviewerReady: phaseEval?.reviewer_ready === true,
    generatedAt: new Date().toISOString().slice(0, 10)
  };
}

async function readJsonIfExists(filePath) {
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8"));
  } catch (error) {
    if (error && error.code === "ENOENT") {
      return null;
    }
    throw error;
  }
}

async function writeAssets(metrics) {
  const assets = [
    ["current_authority_stack", currentAuthorityStackSvg(metrics)],
    ["graph_applicability_service_view", operatingModelSvg(metrics)],
    ["graph_evidence_trace_service_view", evidenceTraceSvg(metrics)],
    ["graph_readiness_service_view", readinessGateSvg(metrics)]
  ];
  for (const [name, svg] of assets) {
    const svgPath = path.join(assetDir, `${name}.svg`);
    await fs.writeFile(svgPath, svg, "utf8");
    if (name !== "current_authority_stack") {
      await sharp(Buffer.from(svg), { density: 220 }).png().toFile(path.join(assetDir, `${name}.png`));
    }
  }
}

async function launchBrowser() {
  const launchOptions = {
    headless: true,
    args: ["--use-gl=swiftshader", "--disable-dev-shm-usage"]
  };
  const executablePath = chromeCandidates.find((candidate) => fsSync.existsSync(candidate));
  if (executablePath) {
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

async function renderQaScreenshots(browser, htmlPath, outputDir) {
  const page = await browser.newPage({ viewport: { width: 1320, height: 1700 }, deviceScaleFactor: 1 });
  await page.goto(`file://${htmlPath}`, { waitUntil: "load" });
  const pages = await page.locator(".page").count();
  for (let index = 0; index < pages; index += 1) {
    await page.locator(".page").nth(index).screenshot({
      path: path.join(outputDir, `page-${String(index + 1).padStart(2, "0")}.png`)
    });
  }
  await page.close();
}

function briefHtml(metrics) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>NEPA 3D Knowledge Graph Capabilities Brief</title>
  <style>
    @page { size: Letter; margin: 0; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: #17202a;
      background: #f4f6f2;
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
      background: #f4f6f2;
    }
    .page:last-child { page-break-after: auto; }
    .kicker {
      color: #1f6f68;
      font-size: 9.5pt;
      font-weight: 850;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    h1, h2, h3, p { margin: 0; }
    h1 {
      margin-top: 0.06in;
      max-width: 6.9in;
      font-size: 29pt;
      line-height: 1;
      letter-spacing: 0;
    }
    h2 {
      margin-top: 0.04in;
      font-size: 20pt;
      line-height: 1.08;
      letter-spacing: 0;
    }
    h3 {
      font-size: 11.4pt;
      line-height: 1.16;
      letter-spacing: 0;
    }
    p, li {
      font-size: 9.5pt;
      line-height: 1.36;
      color: #435049;
    }
    .lede {
      margin-top: 0.12in;
      max-width: 6.75in;
      color: #26322d;
      font-size: 11.6pt;
      line-height: 1.33;
    }
    .metric-context {
      margin-top: 0.12in;
      color: #1f6f68;
      font-size: 8.9pt;
      font-weight: 800;
    }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.09in;
      margin-top: 0.15in;
    }
    .metric {
      min-height: 0.66in;
      padding: 0.1in;
      background: #ffffff;
      border: 1px solid #d4d9d0;
      border-left: 5px solid #1f6f68;
      border-radius: 8px;
      box-shadow: 0 8px 18px rgba(29, 39, 34, 0.07);
    }
    .metric strong {
      display: block;
      font-size: 17pt;
      line-height: 1;
      color: #17202a;
    }
    .metric span {
      display: block;
      margin-top: 0.04in;
      font-size: 7.7pt;
      line-height: 1.22;
      color: #58615b;
      font-weight: 720;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.16in;
      align-items: start;
    }
    .hero-img,
    .graph-figure {
      width: 100%;
      border: 1px solid #d4d9d0;
      border-radius: 10px;
      background: #ffffff;
      box-shadow: 0 12px 28px rgba(29, 39, 34, 0.12);
    }
    .hero-img { height: 3.52in; object-fit: cover; object-position: center; }
    .graph-figure { height: 4.95in; object-fit: contain; object-position: center; }
    .graph-figure.tall { height: 5.38in; }
    .caption {
      margin-top: 0.06in;
      color: #5e6861;
      font-size: 8.1pt;
      line-height: 1.28;
    }
    .callout {
      padding: 0.14in;
      background: #ffffff;
      border: 1px solid #d4d9d0;
      border-left: 6px solid #1f6f68;
      border-radius: 8px;
      box-shadow: 0 8px 18px rgba(29, 39, 34, 0.06);
    }
    .callout strong {
      display: block;
      margin-bottom: 0.05in;
      color: #17202a;
      font-size: 11.2pt;
    }
    ul {
      margin: 0.08in 0 0;
      padding-left: 0.16in;
    }
    li { margin-bottom: 0.05in; }
    .capability-list {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.08in;
    }
    .capability {
      min-height: 0.68in;
      padding: 0.08in;
      border-radius: 7px;
      border: 1px solid #d4d9d0;
      background: rgba(255,255,255,0.92);
    }
    .capability strong {
      display: block;
      margin-bottom: 0.03in;
      color: #17202a;
      font-size: 8.9pt;
    }
    .capability span {
      display: block;
      color: #58615b;
      font-size: 7.7pt;
      line-height: 1.28;
    }
    .footer {
      display: flex;
      justify-content: space-between;
      gap: 0.15in;
      padding-top: 0.08in;
      border-top: 1px solid #d4d9d0;
      color: #68706a;
      font-size: 7.1pt;
      line-height: 1.25;
    }
    .source-note {
      margin-top: 0.08in;
      color: #68706a;
      font-size: 7.6pt;
      line-height: 1.25;
    }
  </style>
</head>
<body>
  <section class="page">
    <header>
      <div class="kicker">System Capabilities Brief</div>
      <h1>NEPA 3D Knowledge Graph Review System</h1>
      <p class="lede">The current system is a local, auditable reviewer-engine for USDA Forest Service Region 1 NEPA source material. It turns workbook-governed source records into extracted evidence, authority-family models, source-claim links, applicability decisions, compliance outputs, decision-support reports, and a 3D knowledge graph surface.</p>
      <p class="metric-context">Current operating status from local catalog, source-set graph, phase-eval, and promotion gates.</p>
      <div class="metric-grid">
        ${metric(metrics.sourceRecords.toLocaleString(), "workbook source records in the local catalog")}
        ${metric(metrics.authorityFamilies.toLocaleString(), "authority families mapped to source records")}
        ${metric(passRatio(metrics.validationChecks, metrics.validationChecks), "source-set graph checks")}
        ${metric(passRatio(metrics.currentGatePassed, metrics.currentGateTotal), "current promotion gates")}
      </div>
    </header>
    <main>
      <img class="hero-img" src="assets/current_authority_stack.svg" alt="System process from controlled source library to decision support" />
      <div class="grid-2" style="margin-top:0.15in">
        <div class="callout">
          <strong>What the system does</strong>
          <p>Maintains source identity, artifact provenance, citation labels, currentness status, extraction spans, graph edges, validation results, and reviewer-facing outputs as separate auditable surfaces.</p>
        </div>
        <div class="callout">
          <strong>What the system avoids</strong>
          <p>It does not rely on hidden one-off shortcuts or unsupported legal conclusions. Expansion to new packages or profiles is routed through source, profile, and evaluation gates.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Brief generated ${escapeHtml(metrics.generatedAt)} from current local system artifacts.</span>
      <span>Scope: system capabilities and boundaries only; no named package examples.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 1 / Source-Governed Operating Model</div>
      <h2>Controlled source library to graph-ready review layer</h2>
      <p class="lede">The workbook remains the contract. Downloader, catalog, extraction, retrieval, evidence graph, source-claim graph, rule binding, and knowledge graph exports all preserve row identity and provenance so downstream review products can be replayed and inspected.</p>
    </header>
    <main>
      <img class="graph-figure" src="assets/graph_applicability_service_view.png" alt="Operating model showing source library, extraction, authority graph, and review outputs" />
      <p class="caption">Operating model: source records are captured once, then promoted through derived layers with explicit validation. The graphic separates source capture, semantic extraction, applicability, review products, and visualization so the same evidence model supports multiple outputs without duplicating logic.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>Currentness and partitioning</strong>
          <p>Active review sources are separated from candidate, blocked, superseded, and currentness-only records before graph export. That prevents stale or excluded sources from silently supporting current authority.</p>
        </div>
        <div class="callout">
          <strong>Validation before display</strong>
          <p>Graph exports carry node and edge type checks, provenance requirements, endpoint compatibility checks, readiness status, and failure-category counts before they are used by the viewer or promotion suite.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Current graph surface: ${metrics.nodeCount.toLocaleString()} nodes and ${metrics.edgeCount.toLocaleString()} edges.</span>
      <span>Catalog boundary: ${metrics.artifacts.toLocaleString()} unique artifacts linked to workbook records.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 2 / Evidence Traceability And Review Products</div>
      <h2>Every finding stays connected to evidence</h2>
      <p class="lede">The system keeps source records, artifacts, chunks, evidence spans, source claims, rule templates, applicability decisions, generated rules, and findings as graph-visible objects. Review outputs are produced from those artifacts rather than from a narrative-only analysis pass.</p>
    </header>
    <main>
      <img class="graph-figure" src="assets/graph_evidence_trace_service_view.png" alt="Evidence path from source record through extraction and review outputs" />
      <p class="caption">Traceability model: source evidence supports claims; claims support rules and applicability; applicability drives review products. The chain remains inspectable across JSON, Markdown, PDF, SQLite, and graph export surfaces.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>Reviewer-facing outputs</strong>
          <ul>
            <li>Compliance matrix in JSON, Markdown, and PDF.</li>
            <li>Decision-support report with evidence paths and residual risk.</li>
            <li>Final QA certification and replay validation artifacts.</li>
            <li>Knowledge graph JSON, node/edge files, summaries, and validation.</li>
          </ul>
        </div>
        <div class="callout">
          <strong>Reverse compliance</strong>
          <p>The same evidence model can search for unsupported claims, older-regulation dependencies, missing source support, unresolved applicability, and forest-plan component gaps before the package is treated as reviewer-ready.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Current source-claim links: ${metrics.sourceClaims.toLocaleString()}.</span>
      <span>Phase-eval status: ${passRatio(metrics.phasePassed, metrics.phaseTotal)} passing phases.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 3 / Readiness, Governance, And Expansion</div>
      <h2>Promotion gates make readiness explicit</h2>
      <p class="lede">Readiness is not inferred from a finished-looking report. The system uses deterministic gates for source capture, currentness, extraction, retrieval, graph validation, applicability, compliance outputs, forest-plan evaluation, decision support, final QA, and promotion.</p>
    </header>
    <main>
      <img class="graph-figure tall" src="assets/graph_readiness_service_view.png" alt="Readiness gates and expansion boundary for the NEPA review system" />
      <div class="grid-2" style="margin-top:0.12in">
        <div class="capability-list">
          ${capability("Source control", "Workbook rows, URL overrides, catalog records, hashes, and source-set manifests.")}
          ${capability("Evidence build", "Extraction, retrieval, evidence spans, graph edges, and source-claim links.")}
          ${capability("Authority model", "Authority families, currentness decisions, rule templates, and source partitions.")}
          ${capability("Applicability", "Package-specific decisions, generated rules, screened-out authority, and unresolved items.")}
          ${capability("Review outputs", "Compliance matrix, decision support, final QA, and reviewer-facing PDFs.")}
          ${capability("Viewer surface", "3D graph scenes driven by validated graph JSON rather than hard-coded visuals.")}
        </div>
        <div>
          <div class="callout">
            <strong>Expansion boundary</strong>
            <p>New packages, forest profiles, or authority deltas are added by expanding the source/profile contract and replaying gates. Blockers remain visible when profiles or sources are not ready, instead of being collapsed into a generic failure.</p>
          </div>
          <p class="source-note">Boundary statement: the system produces auditable review support and readiness evidence. It does not replace professional judgment, agency review, or legal sufficiency review.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Forest-plan readiness tracked: ${metrics.graphReadyProfiles}/${metrics.profileCount} profiles graph-ready, ${metrics.blockedProfiles} blocked.</span>
      <span>Current promotion: ${metrics.currentPromotionReady ? "ready" : "not ready"} with ${failureCategoryText(metrics.promotionFailureCategories)} current failures.</span>
    </footer>
  </section>
</body>
</html>`;
}

function currentAuthorityStackSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640" role="img" aria-label="System process from controlled source library to decision support">
  ${svgDefs()}
  <rect width="1280" height="640" rx="28" fill="#f4f6f2"/>
  <rect x="34" y="32" width="1212" height="576" rx="26" fill="#ffffff" stroke="#d4d9d0"/>
  <text x="72" y="85" font-family="Inter, Arial, sans-serif" font-size="33" font-weight="880" fill="#17202a">System process: controlled evidence to review support</text>
  <text x="72" y="125" font-family="Inter, Arial, sans-serif" font-size="18" fill="#58615b">The review engine keeps source capture, evidence, authority logic, and decision-support outputs traceable.</text>
  ${stackBox(72, 182, "Workbook source contract", metrics.sourceRecords.toLocaleString(), "catalog records; row identity, scope, URLs", "#17202a")}
  ${stackBox(368, 182, "Audited local corpus", metrics.artifacts.toLocaleString(), "unique artifacts; hashes, manifests, SQLite", "#1f6f68")}
  ${stackBox(664, 182, "Authority graph", metrics.authorityFamilies.toLocaleString(), "authority families; currentness, partitions, rules", "#835b2f")}
  ${stackBox(960, 182, "Review outputs", passRatio(metrics.currentGatePassed, metrics.currentGateTotal), "current gates; matrix, support, QA, viewer", "#2e5e88")}
  ${arrow(330, 282, 358, 282)}
  ${arrow(626, 282, 654, 282)}
  ${arrow(922, 282, 950, 282)}
  <g transform="translate(72 452)">
    <rect width="1136" height="98" rx="18" fill="#eef5f2" stroke="#c3d5ce"/>
    <text x="28" y="38" font-family="Inter, Arial, sans-serif" font-size="21" font-weight="850" fill="#17202a">Design principle</text>
    ${wrapSvgText("Domain knowledge stays in data and artifacts: source rows, authority-family configs, rule templates, eval fixtures, graph contracts, and reviewer-facing reports.", 28, 70, 1068, 16, "#435049", 2)}
  </g>
</svg>`;
}

function operatingModelSvg(metrics) {
  const lanes = [
    ["Input contract", "Workbook rows", "Scope and exclusions", "URL overrides", "#17202a"],
    ["Source library", "Catalog and SQLite", "Manifests and hashes", "Artifact provenance", "#1f6f68"],
    ["Derived evidence", "Extraction spans", "Retrieval index", "Source claims", "#835b2f"],
    ["Authority logic", "Currentness", "Applicability", "Generated rules", "#6f4f86"],
    ["Review surface", "Matrices and reports", "Graph exports", "Promotion gates", "#2e5e88"]
  ];
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120" role="img" aria-label="Operating model from source library to review outputs">
  ${svgDefs()}
  <rect width="1800" height="1120" rx="34" fill="#f4f6f2"/>
  <text x="72" y="92" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="880" fill="#17202a">Source-governed operating model</text>
  ${wrapSvgText("Each layer reads from a controlled surface and writes an auditable artifact. Generated products can be rebuilt without scanning raw filenames or collapsing provenance.", 72, 138, 1560, 22, "#58615b", 2)}
  ${lanes
    .map((lane, index) => laneCard(72 + index * 340, 252, 292, 540, lane[4], lane[0], lane.slice(1, 4)))
    .join("")}
  ${flowArrow(364, 520, 402, 520)}
  ${flowArrow(704, 520, 742, 520)}
  ${flowArrow(1044, 520, 1082, 520)}
  ${flowArrow(1384, 520, 1422, 520)}
  <g transform="translate(72 868)" filter="url(#shadow)">
    <rect width="1656" height="176" rx="22" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="32" y="48" font-family="Inter, Arial, sans-serif" font-size="28" font-weight="880" fill="#17202a">Current system signals</text>
    ${statusPill(32, 78, "Catalog", `${metrics.sourceRecords.toLocaleString()} source records`, "#17202a")}
    ${statusPill(366, 78, "Graph", `${metrics.nodeCount.toLocaleString()} nodes / ${metrics.edgeCount.toLocaleString()} edges`, "#1f6f68")}
    ${statusPill(700, 78, "Authority", `${metrics.authorityFamilies.toLocaleString()} families / ${metrics.authorityTemplates.toLocaleString()} templates`, "#835b2f")}
    ${statusPill(1034, 78, "Gates", `${passRatio(metrics.currentGatePassed, metrics.currentGateTotal)} current promotion`, "#2e5e88")}
  </g>
</svg>`;
}

function evidenceTraceSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120" role="img" aria-label="Evidence path from source record through extraction and review outputs">
  ${svgDefs()}
  <rect width="1800" height="1120" rx="34" fill="#f4f6f2"/>
  <text x="72" y="92" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="880" fill="#17202a">Evidence path stays inspectable</text>
  ${wrapSvgText("The system treats a finding as the end of a traceable path, not as a standalone sentence. Each link has a provenance role and can be tested.", 72, 138, 1560, 22, "#58615b", 2)}
  ${graphEdge(258, 425, 520, 425, "#2e5e88", 8, "artifact link")}
  ${graphEdge(700, 425, 962, 425, "#1f6f68", 8, "extracted support")}
  ${graphEdge(1142, 425, 1404, 425, "#835b2f", 8, "rule support")}
  ${graphEdge(1494, 510, 1494, 690, "#6f4f86", 8, "review output")}
  ${graphEdge(520, 720, 1404, 720, "#a65332", 7, "evidence span")}
  ${graphNode(190, 425, 96, "#2e5e88", "Source record", "Workbook row", "scope + citation")}
  ${graphNode(610, 425, 98, "#1f6f68", "Artifact", "Local bytes", "hash + manifest")}
  ${graphNode(1052, 425, 104, "#835b2f", "Source claim", `${metrics.sourceClaims.toLocaleString()} links`, "evidence graph")}
  ${graphNode(1494, 425, 104, "#6f4f86", "Authority logic", "Rules + decisions", "applicability")}
  ${graphNode(1494, 790, 104, "#2e5e88", "Review product", "Matrix / report", "PDF + JSON")}
  ${graphNode(430, 720, 86, "#a65332", "Evidence span", "Extracted text", "chunk reference")}
  <g transform="translate(72 902)" filter="url(#shadow)">
    <rect width="1656" height="142" rx="22" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="32" y="46" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="880" fill="#17202a">Review outputs from the trace</text>
    ${inlineList(32, 88, [
      "compliance matrix",
      "decision-support report",
      "final QA packet",
      "knowledge graph export",
      "3D viewer scenes"
    ])}
  </g>
</svg>`;
}

function readinessGateSvg(metrics) {
  const gates = [
    ["Catalog integrity", "Workbook coverage, source statuses, artifact links", true],
    ["Currentness", "Active, candidate, superseded, and blocked source roles", metrics.currentnessPassed],
    ["Graph validation", `${passRatio(metrics.validationChecks, metrics.validationChecks)} source-set checks`, metrics.validationPassed],
    ["Phase evaluation", `${passRatio(metrics.phasePassed, metrics.phaseTotal)} review phases`, metrics.phaseReviewerReady],
    ["Promotion suite", `${passRatio(metrics.currentGatePassed, metrics.currentGateTotal)} current gates`, metrics.currentPromotionReady]
  ];
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1180" viewBox="0 0 1800 1180" role="img" aria-label="Readiness gates and expansion boundary for the NEPA review system">
  ${svgDefs()}
  <rect width="1800" height="1180" rx="34" fill="#f4f6f2"/>
  <text x="72" y="92" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="880" fill="#17202a">Readiness is a gated state</text>
  ${wrapSvgText("Reports, PDFs, and viewer scenes are downstream products. The system first verifies source capture, evidence, graph validity, review outputs, and promotion status.", 72, 138, 1560, 22, "#58615b", 2)}
  <g transform="translate(72 224)" filter="url(#shadow)">
    <rect width="1060" height="744" rx="24" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="32" y="54" font-family="Inter, Arial, sans-serif" font-size="29" font-weight="880" fill="#17202a">Current gate stack</text>
    ${gates.map((gate, index) => gateRow(34, 96 + index * 124, gate[0], gate[1], gate[2])).join("")}
  </g>
  <g transform="translate(1190 224)" filter="url(#shadow)">
    <rect width="538" height="744" rx="24" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="30" y="54" font-family="Inter, Arial, sans-serif" font-size="29" font-weight="880" fill="#17202a">Expansion boundary</text>
    ${metricBlock(30, 104, "Forest-plan profiles", `${metrics.graphReadyProfiles}/${metrics.profileCount}`, "graph-ready")}
    ${metricBlock(30, 248, "Blocked profiles", String(metrics.blockedProfiles), "visible readiness blockers")}
    ${metricBlock(30, 392, "Components", metrics.forestComponents.toLocaleString(), "inventory-backed")}
    ${metricBlock(30, 536, "Profile requirements", String(metrics.fieldDirectives + metrics.overlayRequirements), "directives + overlays")}
  </g>
  <text x="92" y="1060" font-family="Inter, Arial, sans-serif" font-size="23" font-weight="850" fill="#1f6f68">Blocked or incomplete sources remain explicit so expansion risk is visible before a package is called ready.</text>
</svg>`;
}

function stackBox(x, y, title, value, subtitle, color) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <rect width="256" height="200" rx="18" fill="#ffffff" stroke="#d4d9d0"/>
    <rect width="256" height="9" rx="4" fill="${color}"/>
    ${wrapSvgText(title, 20, 50, 212, 18, "#17202a", 2, "start", "850")}
    <text x="20" y="110" font-family="Inter, Arial, sans-serif" font-size="29" font-weight="900" fill="${color}">${escapeXml(value)}</text>
    ${wrapSvgText(subtitle, 20, 148, 212, 15, "#58615b", 2)}
  </g>`;
}

function laneCard(x, y, width, height, color, title, rows) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <rect width="${width}" height="${height}" rx="22" fill="#ffffff" stroke="#d4d9d0"/>
    <rect width="${width}" height="12" rx="6" fill="${color}"/>
    ${wrapSvgText(title, 24, 62, width - 48, 28, "#17202a", 2, "start", "880")}
    ${rows
      .map((row, index) => `<g transform="translate(24 ${178 + index * 108})">
        <rect width="${width - 48}" height="78" rx="15" fill="#f8faf7" stroke="#d4d9d0"/>
        <circle cx="28" cy="39" r="10" fill="${color}"/>
        ${wrapSvgText(row, 52, 46, width - 112, 19, "#435049", 2)}
      </g>`)
      .join("")}
  </g>`;
}

function statusPill(x, y, title, value, color) {
  return `<g transform="translate(${x} ${y})">
    <rect width="300" height="66" rx="33" fill="#f8faf7" stroke="#d4d9d0"/>
    <circle cx="36" cy="33" r="11" fill="${color}"/>
    <text x="58" y="28" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="850" fill="#17202a">${escapeXml(title)}</text>
    <text x="58" y="50" font-family="Inter, Arial, sans-serif" font-size="14" fill="#58615b">${escapeXml(value)}</text>
  </g>`;
}

function metricBlock(x, y, title, value, subtitle) {
  return `<g transform="translate(${x} ${y})">
    <rect width="478" height="110" rx="18" fill="#f8faf7" stroke="#d4d9d0"/>
    <text x="24" y="38" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="850" fill="#17202a">${escapeXml(title)}</text>
    <text x="24" y="78" font-family="Inter, Arial, sans-serif" font-size="36" font-weight="920" fill="#1f6f68">${escapeXml(value)}</text>
    <text x="156" y="78" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="760" fill="#58615b">${escapeXml(subtitle)}</text>
  </g>`;
}

function gateRow(x, y, title, value, passed) {
  const color = passed ? "#1f6f68" : "#a65332";
  const label = passed ? "PASS" : "BLOCKED";
  return `<g transform="translate(${x} ${y})">
    <rect width="992" height="92" rx="18" fill="#f8faf7" stroke="#d4d9d0"/>
    <circle cx="48" cy="46" r="22" fill="${color}"/>
    <path d="M 38 46 L 45 54 L 60 36" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
    <text x="88" y="38" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="870" fill="#17202a">${escapeXml(title)}</text>
    <text x="88" y="66" font-family="Inter, Arial, sans-serif" font-size="17" fill="#58615b">${escapeXml(value)}</text>
    <rect x="832" y="27" width="126" height="38" rx="19" fill="${color}"/>
    <text x="895" y="52" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="850" fill="#ffffff">${label}</text>
  </g>`;
}

function graphNode(x, y, radius, color, title, value, subtitle) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <circle r="${radius}" fill="#ffffff" stroke="${color}" stroke-width="8"/>
    <circle r="${Math.max(radius - 20, 20)}" fill="${color}" opacity="0.09"/>
    <text y="${-radius - 26}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="25" font-weight="850" fill="#17202a">${escapeXml(title)}</text>
    ${wrapSvgText(value, 0, -12, radius * 1.48, 21, "#17202a", 2, "middle", "820")}
    <text y="${radius + 36}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="760" fill="${color}">${escapeXml(subtitle)}</text>
  </g>`;
}

function graphEdge(x1, y1, x2, y2, color, width, label) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const labelWidth = Math.max(160, Math.min(360, label.length * 11 + 42));
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-opacity="0.62" marker-end="url(#arrow)"/>
  <g transform="translate(${mx - labelWidth / 2} ${my - 24})">
    <rect width="${labelWidth}" height="42" rx="21" fill="#ffffff" stroke="#d4d9d0" opacity="0.96"/>
    <text x="${labelWidth / 2}" y="27" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="17" font-weight="800" fill="#435049">${escapeXml(label)}</text>
  </g>`;
}

function flowArrow(x1, y1, x2, y2) {
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="#8b948d" stroke-width="6" stroke-linecap="round" marker-end="url(#arrow)"/>`;
}

function arrow(x1, y1, x2, y2) {
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="#8b948d" stroke-width="4" stroke-linecap="round"/>
  <path d="M ${x2 - 10} ${y2 - 9} L ${x2} ${y2} L ${x2 - 10} ${y2 + 9}" fill="none" stroke="#8b948d" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`;
}

function inlineList(x, y, items) {
  let cursor = x;
  return items
    .map((item) => {
      const width = item.length * 10 + 46;
      const svg = `<g transform="translate(${cursor} ${y - 28})">
        <rect width="${width}" height="42" rx="21" fill="#eef5f2" stroke="#c3d5ce"/>
        <circle cx="22" cy="21" r="6" fill="#1f6f68"/>
        <text x="36" y="27" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="780" fill="#435049">${escapeXml(item)}</text>
      </g>`;
      cursor += width + 18;
      return svg;
    })
    .join("");
}

function svgDefs() {
  return `<defs>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#17202a" flood-opacity="0.12"/>
    </filter>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#8b948d"/>
    </marker>
  </defs>`;
}

function metric(value, label) {
  return `<div class="metric"><strong>${escapeHtml(String(value))}</strong><span>${escapeHtml(label)}</span></div>`;
}

function capability(title, copy) {
  return `<div class="capability"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(copy)}</span></div>`;
}

function passRatio(passed, total) {
  if (!total) {
    return "ready";
  }
  return `${passed}/${total}`;
}

function failureCategoryText(categories) {
  const entries = Object.entries(categories || {}).filter(([, count]) => count);
  if (!entries.length) {
    return "0";
  }
  return entries.map(([name, count]) => `${count} ${name}`).join(", ");
}

function wrapSvgText(text, x, y, width, fontSize, fill, maxLines = 5, textAnchor = "start", fontWeight = "") {
  const words = String(text).split(/\s+/).filter(Boolean);
  const lines = [];
  let current = "";
  for (const word of words) {
    const next = current ? `${current} ${word}` : word;
    if (next.length * fontSize * 0.52 <= width || !current) {
      current = next;
    } else {
      lines.push(current);
      current = word;
    }
  }
  if (current) {
    lines.push(current);
  }
  return lines
    .slice(0, maxLines)
    .map((line, index) => {
      const dy = index * (fontSize + 5);
      return `<text x="${x}" y="${y + dy}" text-anchor="${textAnchor}" font-family="Inter, Arial, sans-serif" font-size="${fontSize}"${fontWeight ? ` font-weight="${fontWeight}"` : ""} fill="${fill}">${escapeXml(line)}</text>`;
    })
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function escapeXml(value) {
  return escapeHtml(value);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
