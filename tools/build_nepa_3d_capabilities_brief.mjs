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
const sourceSetGraphPath = path.join(
  repoRoot,
  "source_library",
  "derived",
  "source-set-ba8d0feae79501b8",
  "knowledge_graph",
  "nepa_3d_graph.json"
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
  const graph = await readJsonIfExists(sourceSetGraphPath);
  const catalog = await readJsonIfExists(catalogManifestPath);
  const promotion = await readJsonIfExists(promotionSuitePath);
  const phaseEval = await readJsonIfExists(phaseEvalPath);
  const validationChecks =
    summary?.validation_check_count || (Array.isArray(validation?.checks) ? validation.checks.length : 0);
  const currentGateTotal = promotion?.required_current_result_count || 0;
  const currentGatePassed = promotion?.passed_required_current_result_count || 0;
  const phaseTotal = phaseEval?.phase_count || (Array.isArray(phaseEval?.phases) ? phaseEval.phases.length : 0);
  const phasePassed = phaseEval?.passed_phase_count || 0;
  const authorityFamilyNodes = Array.isArray(graph?.nodes)
    ? graph.nodes.filter((node) => node.node_type === "authority_family")
    : [];
  const nepaFamilyCount = authorityFamilyNodes.filter((node) =>
    /nepa|national environmental policy act/i.test(`${node.node_id || ""} ${node.label || ""}`)
  ).length;

  return {
    activeReviewCorpus: summary?.source_partition_counts?.active_review_corpus || 0,
    candidateBlockedSources: summary?.source_partition_counts?.candidate_blocked_source || 0,
    sourceRecords: catalog?.source_count || summary?.catalog_source_record_count || 0,
    artifacts: catalog?.artifact_count || summary?.node_type_counts?.artifact || 0,
    sourceLinks: catalog?.link_count || summary?.edge_type_counts?.HAS_ARTIFACT || 0,
    nodeCount: summary?.node_count || 0,
    edgeCount: summary?.edge_count || 0,
    authorityFamilies: summary?.authority_family_count || summary?.node_type_counts?.authority_family || 0,
    nepaFamilyCount,
    regulationAuthorityCount: summary?.authority_category_counts?.regulation || 0,
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
    readinessBlockers: summary?.readiness_blocker_counts || {},
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
    ["graph_r1_showcase_view", r1GraphShowcaseSvg(metrics)]
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
    .hero-img { height: 5.25in; object-fit: contain; object-position: center; }
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
      <p class="lede">The system turns Region 1 NEPA source material into auditable review intelligence. It preserves source provenance, builds an authority graph, traces evidence to findings, and gates readiness before outputs reach reviewers. The result is a transparent operating layer for compliance review, decision support, and graph exploration.</p>
      <p class="metric-context">Current Region 1 implementation snapshot.</p>
      <div class="metric-grid">
        ${metric(metrics.nodeCount.toLocaleString(), "Region 1 graph nodes")}
        ${metric(metrics.edgeCount.toLocaleString(), "Region 1 graph edges")}
        ${metric(metrics.authorityFamilies.toLocaleString(), "authority families")}
        ${metric(metrics.sourceRecords.toLocaleString(), "source records")}
      </div>
    </header>
    <main>
      <img class="hero-img" src="assets/current_authority_stack.svg" alt="Architecture components for the NEPA review system" />
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
      <p class="lede">Every review starts with a controlled source contract. Workbook rows, exclusions, URL repairs, source partitions, catalog records, and artifact hashes define what can support review logic. Derived layers are rebuilt from those surfaces, not loose files.</p>
    </header>
    <main>
      <img class="graph-figure" src="assets/graph_applicability_service_view.png" alt="Operating model showing source library, extraction, authority graph, and review outputs" />
      <p class="caption">Source governance model: only eligible catalog records feed review logic. Superseded, candidate, blocked, or currentness-only records stay visible as context and readiness evidence.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>Contract enforced</strong>
          <p>Workbook scope, source identity, URL overrides, exclusions, and partitions are checked before downstream review artifacts can rely on a source.</p>
        </div>
        <div class="callout">
          <strong>Rebuildable layers</strong>
          <p>Extraction, retrieval, claims, graph exports, reports, and validation summaries are generated from catalog surfaces and can be replayed.</p>
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
      <p class="lede">Findings are produced from inspectable evidence paths. The system links source records, artifacts, evidence spans, claims, authority decisions, and review findings before it renders reports or graph views.</p>
    </header>
    <main>
      <img class="graph-figure" src="assets/graph_evidence_trace_service_view.png" alt="Evidence path from source record through extraction and review outputs" />
      <p class="caption">Traceability model: the finding is the end of a chain, not a free-standing conclusion. The same chain supports reports, QA replay, and graph exploration.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>Audit surface</strong>
          <p>Each product can be traced back to source record, artifact hash, evidence span, and decision path. Reviewers can inspect the basis without relying on narrative alone.</p>
        </div>
        <div class="callout">
          <strong>Reverse compliance</strong>
          <p>The evidence model flags unsupported claims, older-regulation dependencies, missing source support, unresolved applicability, and forest-plan gaps before readiness is claimed.</p>
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
      <div class="kicker">Capability 3 / Region 1 3D Graph</div>
      <h2>NEPA, USDA regulations, and forest plans in one graph</h2>
      <p class="lede">The Region 1 graph is the client-facing surface for the system. It shows NEPA authority, USDA regulations and procedures, source evidence, and forest-plan layers as connected but distinct parts of the review universe.</p>
    </header>
    <main>
      <img class="graph-figure tall" src="assets/graph_r1_showcase_view.png" alt="Region 1 3D graph showcase with NEPA, USDA regulations, source evidence, and forest-plan layers" />
      <div class="grid-2" style="margin-top:0.12in">
        <div class="callout">
          <strong>Separate forest-plan layer</strong>
          <p>Forest-plan profiles and components are graphed separately from NEPA and USDA authority, then linked into review context when ready.</p>
        </div>
        <div class="callout">
          <strong>Authority layer</strong>
          <p>NEPA authority, USDA procedures, and regulatory families stay visible beside source evidence so reviewers can inspect how findings are supported.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>R1 graph surface: ${metrics.nodeCount.toLocaleString()} nodes and ${metrics.edgeCount.toLocaleString()} edges.</span>
      <span>Forest plans: ${metrics.profileCount} profiles and ${metrics.forestComponents.toLocaleString()} components represented as a separate layer.</span>
    </footer>
  </section>
</body>
</html>`;
}

function currentAuthorityStackSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="840" viewBox="0 0 1280 840" role="img" aria-label="Architecture components for the NEPA review system">
  ${svgDefs()}
  <rect width="1280" height="840" rx="28" fill="#f4f6f2"/>
  <rect x="34" y="32" width="1212" height="776" rx="26" fill="#ffffff" stroke="#d4d9d0"/>
  <text x="72" y="86" font-family="Inter, Arial, sans-serif" font-size="34" font-weight="880" fill="#17202a">Architecture components at a glance</text>
  <text x="72" y="126" font-family="Inter, Arial, sans-serif" font-size="18" fill="#58615b">A source-governed review engine with traceable evidence, explicit authority logic, and gated outputs.</text>

  ${architectureCard(76, 188, 330, 150, "#17202a", "Source Contract", "Workbook rows set scope, exclusions, source identity, and review boundaries.")}
  ${architectureCard(474, 188, 330, 150, "#1f6f68", "Audited Source Library", "Catalogs, manifests, hashes, partitions, and SQLite preserve provenance.")}
  ${architectureCard(872, 188, 330, 150, "#835b2f", "Evidence Pipeline", "Extraction, retrieval, evidence spans, graph edges, and source claims.")}
  ${flowArrow(406, 263, 464, 263)}
  ${flowArrow(804, 263, 862, 263)}

  ${architectureCard(76, 416, 330, 150, "#6f4f86", "Authority Engine", "Authority families, currentness, rule templates, and applicability decisions.")}
  ${architectureCard(474, 416, 330, 150, "#2e5e88", "Reviewer Outputs", "Compliance matrix, decision support, final QA, and report PDFs.")}
  ${architectureCard(872, 416, 330, 150, "#a65332", "Graph Experience", "3D scenes, lenses, search, and evidence paths from validated graph JSON.")}
  ${flowArrow(406, 491, 464, 491)}
  ${flowArrow(804, 491, 862, 491)}

  <g transform="translate(76 640)" filter="url(#shadow)">
    <rect width="1126" height="98" rx="18" fill="#eef5f2" stroke="#c3d5ce"/>
    <text x="28" y="38" font-family="Inter, Arial, sans-serif" font-size="21" font-weight="850" fill="#17202a">Readiness layer</text>
    ${wrapSvgText("Validation, phase-eval, promotion, and expansion gates run across the architecture before the system claims reviewer readiness.", 28, 70, 1044, 17, "#435049", 2)}
  </g>
</svg>`;
}

function operatingModelSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120" role="img" aria-label="Operating model from source library to review outputs">
  ${svgDefs()}
  <rect width="1800" height="1120" rx="34" fill="#f4f6f2"/>
  <text x="72" y="92" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="880" fill="#17202a">Source governance before analysis</text>
  ${wrapSvgText("Only cataloged, eligible, current sources can feed review logic. Blocked and superseded material stays visible without becoming controlling authority.", 72, 138, 1560, 22, "#58615b", 2)}

  ${governanceCard(72, 222, 470, 188, "#17202a", "1. Workbook Contract", [
    "Defines review universe",
    "Preserves row identity",
    "Applies scope and exclusions"
  ])}
  ${governanceCard(665, 222, 470, 188, "#1f6f68", "2. Local Source Library", [
    "Catalog, manifests, hashes",
    "Artifact provenance",
    "SQLite review index"
  ])}
  ${governanceCard(1258, 222, 470, 188, "#835b2f", "3. Source Partitions", [
    "Active review corpus",
    "Candidate or blocked sources",
    "Currentness archive"
  ])}
  ${flowArrow(542, 316, 655, 316)}
  ${flowArrow(1135, 316, 1248, 316)}

  <g transform="translate(72 500)" filter="url(#shadow)">
    <rect width="1656" height="186" rx="22" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="32" y="48" font-family="Inter, Arial, sans-serif" font-size="27" font-weight="880" fill="#17202a">Partition rule</text>
    ${partitionPill(32, 82, 486, "#1f6f68", "Active review corpus", `${metrics.activeReviewCorpus.toLocaleString()} records may support review logic`)}
    ${partitionPill(584, 82, 486, "#a65332", "Candidate / blocked", `${metrics.candidateBlockedSources.toLocaleString()} record visible as a blocker`)}
    ${partitionPill(1136, 82, 486, "#68706a", "Superseded / currentness-only", "visible for context, not active authority")}
  </g>

  <g transform="translate(72 760)" filter="url(#shadow)">
    <rect width="1656" height="230" rx="22" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="32" y="50" font-family="Inter, Arial, sans-serif" font-size="27" font-weight="880" fill="#17202a">Derived after the source gate</text>
    ${processStep(34, 92, "#835b2f", "Extraction", "source text and evidence spans")}
    ${processStep(420, 92, "#1f6f68", "Retrieval", "indexed evidence for review")}
    ${processStep(806, 92, "#6f4f86", "Claims", "source claims and rule support")}
    ${processStep(1192, 92, "#2e5e88", "Graph Export", "validated nodes, edges, and reports")}
    ${flowArrow(316, 152, 410, 152)}
    ${flowArrow(702, 152, 796, 152)}
    ${flowArrow(1088, 152, 1182, 152)}
  </g>
</svg>`;
}

function evidenceTraceSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120" role="img" aria-label="Evidence path from source record through extraction and review outputs">
  ${svgDefs()}
  <rect width="1800" height="1120" rx="34" fill="#f4f6f2"/>
  <text x="72" y="92" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="880" fill="#17202a">Finding trace</text>
  ${wrapSvgText("The review product is only the final view. The underlying path stays inspectable from source record to finding.", 72, 138, 1560, 22, "#58615b", 2)}

  <g transform="translate(72 214)" filter="url(#shadow)">
    <rect width="1656" height="430" rx="24" fill="#ffffff" stroke="#d4d9d0"/>
    ${traceStep(44, 108, "#17202a", "Source Record", "row identity, scope, citation")}
    ${traceStep(374, 108, "#1f6f68", "Evidence Span", "extracted text with artifact hash")}
    ${traceStep(704, 108, "#835b2f", "Source Claim", `${metrics.sourceClaims.toLocaleString()} support links`)}
    ${traceStep(1034, 108, "#6f4f86", "Authority Decision", "applicable, screened out, unresolved")}
    ${traceStep(1364, 108, "#2e5e88", "Finding", "review result with evidence path")}
    ${flowArrow(300, 198, 364, 198)}
    ${flowArrow(630, 198, 694, 198)}
    ${flowArrow(960, 198, 1024, 198)}
    ${flowArrow(1290, 198, 1354, 198)}
    <text x="44" y="362" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="850" fill="#17202a">Reverse compliance uses the same path in the opposite direction.</text>
    <text x="44" y="397" font-family="Inter, Arial, sans-serif" font-size="19" fill="#58615b">Unsupported claims, stale authority language, missing evidence, and unresolved applicability are flagged before readiness.</text>
  </g>

  <g transform="translate(72 728)" filter="url(#shadow)">
    <rect width="1656" height="234" rx="22" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="32" y="50" font-family="Inter, Arial, sans-serif" font-size="27" font-weight="880" fill="#17202a">Outputs generated from the trace</text>
    ${outputTile(32, 88, "#2e5e88", "Compliance Matrix", "authorities, findings, evidence")}
    ${outputTile(432, 88, "#1f6f68", "Decision Support", "risks, gaps, signer readout")}
    ${outputTile(832, 88, "#835b2f", "Final QA", "replay checks and packet validation")}
    ${outputTile(1232, 88, "#6f4f86", "Knowledge Graph", "nodes, edges, scenes, validation")}
  </g>
</svg>`;
}

function r1GraphShowcaseSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1180" viewBox="0 0 1800 1180" role="img" aria-label="Region 1 3D graph showcase with NEPA, USDA regulations, evidence, and forest plan layers">
  ${graphShowcaseDefs()}
  <rect width="1800" height="1180" rx="34" fill="#f4f6f2"/>
  <g transform="translate(72 82)" filter="url(#shadow)">
    <rect width="1656" height="940" rx="30" fill="#0d1821"/>
    <rect x="18" y="18" width="1620" height="904" rx="24" fill="url(#nightGlow)" stroke="#314653"/>
    <text x="54" y="78" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="900" fill="#f8faf7">Region 1 3D knowledge graph</text>
    <text x="54" y="118" font-family="Inter, Arial, sans-serif" font-size="21" fill="#c8d7d3">Authority, evidence, and forest-plan layers remain distinct but connected.</text>

    ${showcaseEdge(820, 430, 430, 285, "#2ad0bc", 0.72)}
    ${showcaseEdge(820, 430, 1220, 285, "#e7aa54", 0.72)}
    ${showcaseEdge(820, 430, 830, 695, "#71d58a", 0.72)}
    ${showcaseEdge(820, 430, 420, 690, "#66a9e7", 0.5)}
    ${showcaseEdge(820, 430, 1240, 690, "#b38ee8", 0.5)}
    ${showcaseEdge(430, 285, 1220, 285, "#45606c", 0.42)}
    ${showcaseEdge(420, 690, 830, 695, "#45606c", 0.42)}
    ${showcaseEdge(1240, 690, 830, 695, "#45606c", 0.42)}

    ${showcaseHub(820, 430, "#f8faf7", "R1 Graph", `${metrics.nodeCount.toLocaleString()} nodes / ${metrics.edgeCount.toLocaleString()} edges`)}
    ${showcaseCluster(430, 285, "#2ad0bc", "NEPA", `${metrics.nepaFamilyCount || 4} authority families`, [
      "Core statute",
      "EA duties",
      "FS NEPA policy",
      "supersession flags"
    ])}
    ${showcaseCluster(1220, 285, "#e7aa54", "USDA Regulations", `${metrics.regulationAuthorityCount.toLocaleString()} regulation families`, [
      "7 CFR part 1b",
      "agency procedures",
      "rule templates",
      "currentness checks"
    ])}
    ${showcaseCluster(830, 695, "#71d58a", "Forest Plans", `${metrics.profileCount} profiles / ${metrics.forestComponents.toLocaleString()} components`, [
      "separate graph layer",
      "plan components",
      "profile readiness",
      "overlay requirements"
    ])}
    ${showcaseCluster(420, 690, "#66a9e7", "Source Evidence", `${metrics.sourceRecords.toLocaleString()} records / ${metrics.sourceClaims.toLocaleString()} claim links`, [
      "catalog rows",
      "artifact hashes",
      "evidence spans",
      "citation labels"
    ])}
    ${showcaseCluster(1240, 690, "#b38ee8", "Review Views", "lenses, search, scenes", [
      "authority graph",
      "evidence paths",
      "readiness blockers",
      "review outputs"
    ])}

    <g transform="translate(54 798)">
      ${showcaseLegend(0, 0, "#2ad0bc", "NEPA graphed")}
      ${showcaseLegend(270, 0, "#e7aa54", "USDA regulations graphed")}
      ${showcaseLegend(640, 0, "#71d58a", "Forest plans graphed separately")}
      ${showcaseLegend(1110, 0, "#66a9e7", "Source evidence linked")}
    </g>
  </g>
</svg>`;
}

function architectureCard(x, y, width, height, color, title, body) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <rect width="${width}" height="${height}" rx="18" fill="#ffffff" stroke="#d4d9d0"/>
    <rect width="${width}" height="10" rx="5" fill="${color}"/>
    <circle cx="28" cy="48" r="10" fill="${color}"/>
    ${wrapSvgText(title, 48, 55, width - 74, 21, "#17202a", 1, "start", "870")}
    ${wrapSvgText(body, 24, 92, width - 48, 16, "#58615b", 3)}
  </g>`;
}

function graphShowcaseDefs() {
  return `<defs>
    <radialGradient id="nightGlow" cx="50%" cy="42%" r="72%">
      <stop offset="0" stop-color="#183342"/>
      <stop offset="0.58" stop-color="#0f202b"/>
      <stop offset="1" stop-color="#0a131b"/>
    </radialGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#17202a" flood-opacity="0.18"/>
    </filter>
    <filter id="glow" x="-70%" y="-70%" width="240%" height="240%">
      <feGaussianBlur stdDeviation="8" result="blur"/>
      <feMerge>
        <feMergeNode in="blur"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>`;
}

function showcaseEdge(x1, y1, x2, y2, color, opacity) {
  const cx = (x1 + x2) / 2;
  const cy = Math.min(y1, y2) - 80;
  return `<path d="M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}" fill="none" stroke="${color}" stroke-width="5" stroke-opacity="${opacity}" stroke-linecap="round"/>`;
}

function showcaseHub(x, y, color, title, subtitle) {
  return `<g transform="translate(${x} ${y})" filter="url(#glow)">
    <circle r="100" fill="#132734" stroke="${color}" stroke-width="4"/>
    <circle r="67" fill="#1f6f68" opacity="0.38"/>
    <circle r="22" fill="${color}"/>
    <text y="-12" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="30" font-weight="900" fill="#f8faf7">${escapeXml(title)}</text>
    <text y="28" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="760" fill="#c8d7d3">${escapeXml(subtitle)}</text>
  </g>`;
}

function showcaseCluster(x, y, color, title, subtitle, labels) {
  const satellites = [
    [-118, -72],
    [118, -72],
    [-118, 72],
    [118, 72]
  ];
  return `<g transform="translate(${x} ${y})">
    ${satellites
      .map(([sx, sy], index) => {
        const pulse = index % 2 === 0 ? 20 : 14;
        return `<line x1="0" y1="0" x2="${sx}" y2="${sy}" stroke="${color}" stroke-opacity="0.42" stroke-width="3"/>
        <g transform="translate(${sx} ${sy})">
          <circle r="35" fill="#0d1821" stroke="${color}" stroke-width="3" filter="url(#glow)"/>
          <circle r="${pulse}" fill="${color}" opacity="0.16"/>
        </g>`;
      })
      .join("")}
    <circle r="78" fill="#102431" stroke="${color}" stroke-width="5" filter="url(#glow)"/>
    <circle r="46" fill="${color}" opacity="0.22"/>
    <text y="-8" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="28" font-weight="900" fill="#f8faf7">${escapeXml(title)}</text>
    <text y="28" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="17" font-weight="760" fill="${color}">${escapeXml(subtitle)}</text>
  </g>`;
}

function showcaseLegend(x, y, color, label) {
  const width = Math.max(210, label.length * 11 + 54);
  return `<g transform="translate(${x} ${y})">
    <rect width="${width}" height="54" rx="27" fill="#122633" stroke="#314653"/>
    <circle cx="28" cy="27" r="10" fill="${color}"/>
    <text x="48" y="34" font-family="Inter, Arial, sans-serif" font-size="17" font-weight="820" fill="#f8faf7">${escapeXml(label)}</text>
  </g>`;
}

function governanceCard(x, y, width, height, color, title, rows) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <rect width="${width}" height="${height}" rx="20" fill="#ffffff" stroke="#d4d9d0"/>
    <rect width="${width}" height="10" rx="5" fill="${color}"/>
    <text x="28" y="54" font-family="Inter, Arial, sans-serif" font-size="25" font-weight="880" fill="#17202a">${escapeXml(title)}</text>
    ${rows.map((row, index) => checklistRow(30, 88 + index * 30, color, row)).join("")}
  </g>`;
}

function checklistRow(x, y, color, label) {
  return `<g transform="translate(${x} ${y})">
    <circle cx="8" cy="-6" r="7" fill="${color}"/>
    <text x="26" y="0" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="730" fill="#435049">${escapeXml(label)}</text>
  </g>`;
}

function partitionPill(x, y, width, color, title, value) {
  return `<g transform="translate(${x} ${y})">
    <rect width="${width}" height="72" rx="18" fill="#f8faf7" stroke="#d4d9d0"/>
    <circle cx="30" cy="36" r="11" fill="${color}"/>
    <text x="52" y="30" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="850" fill="#17202a">${escapeXml(title)}</text>
    <text x="52" y="54" font-family="Inter, Arial, sans-serif" font-size="15" fill="#58615b">${escapeXml(value)}</text>
  </g>`;
}

function processStep(x, y, color, title, body) {
  return `<g transform="translate(${x} ${y})">
    <rect width="284" height="98" rx="18" fill="#f8faf7" stroke="#d4d9d0"/>
    <rect width="284" height="8" rx="4" fill="${color}"/>
    <text x="24" y="42" font-family="Inter, Arial, sans-serif" font-size="21" font-weight="860" fill="#17202a">${escapeXml(title)}</text>
    ${wrapSvgText(body, 24, 70, 236, 15, "#58615b", 2)}
  </g>`;
}

function traceStep(x, y, color, title, body) {
  return `<g transform="translate(${x} ${y})">
    <rect width="256" height="180" rx="20" fill="#f8faf7" stroke="#d4d9d0"/>
    <rect width="256" height="9" rx="5" fill="${color}"/>
    <text x="24" y="52" font-family="Inter, Arial, sans-serif" font-size="24" font-weight="870" fill="#17202a">${escapeXml(title)}</text>
    ${wrapSvgText(body, 24, 92, 210, 18, "#58615b", 3)}
  </g>`;
}

function outputTile(x, y, color, title, body) {
  return `<g transform="translate(${x} ${y})">
    <rect width="342" height="92" rx="18" fill="#f8faf7" stroke="#d4d9d0"/>
    <circle cx="28" cy="46" r="10" fill="${color}"/>
    <text x="50" y="39" font-family="Inter, Arial, sans-serif" font-size="21" font-weight="860" fill="#17202a">${escapeXml(title)}</text>
    <text x="50" y="66" font-family="Inter, Arial, sans-serif" font-size="16" fill="#58615b">${escapeXml(body)}</text>
  </g>`;
}

function blockerTile(x, y, color, title, count, body) {
  return `<g transform="translate(${x} ${y})">
    <rect width="508" height="112" rx="18" fill="#f8faf7" stroke="#d4d9d0"/>
    <text x="24" y="36" font-family="Inter, Arial, sans-serif" font-size="19" font-weight="850" fill="#17202a">${escapeXml(title)}</text>
    <text x="24" y="78" font-family="Inter, Arial, sans-serif" font-size="34" font-weight="920" fill="${color}">${escapeXml(String(count))}</text>
    <text x="108" y="78" font-family="Inter, Arial, sans-serif" font-size="17" fill="#58615b">${escapeXml(body)}</text>
  </g>`;
}

function readinessCount(metrics, key) {
  return Number(metrics.readinessBlockers?.[key] || 0).toLocaleString();
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
    <rect width="920" height="78" rx="18" fill="#f8faf7" stroke="#d4d9d0"/>
    <circle cx="48" cy="46" r="22" fill="${color}"/>
    <path d="M 38 46 L 45 54 L 60 36" fill="none" stroke="#ffffff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>
    <text x="88" y="38" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="870" fill="#17202a">${escapeXml(title)}</text>
    <text x="88" y="66" font-family="Inter, Arial, sans-serif" font-size="17" fill="#58615b">${escapeXml(value)}</text>
    <rect x="760" y="20" width="126" height="38" rx="19" fill="${color}"/>
    <text x="823" y="45" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="16" font-weight="850" fill="#ffffff">${label}</text>
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
