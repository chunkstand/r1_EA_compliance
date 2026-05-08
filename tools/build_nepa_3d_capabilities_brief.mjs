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
  if (pdf.getPageCount() !== 3) {
    throw new Error(`Expected a 3-page PDF, got ${pdf.getPageCount()} pages.`);
  }
  console.log(`Wrote ${path.relative(repoRoot, briefHtmlPath)}`);
  console.log(`Wrote ${path.relative(repoRoot, briefPdfPath)}`);
  console.log(`Wrote visual QA PNGs under ${qaDir}`);
  console.log("Verified 3 PDF pages.");
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
  for (const entry of await fs.readdir(outputDir)) {
    if (/^page-\d+\.png$/.test(entry)) {
      await fs.rm(path.join(outputDir, entry));
    }
  }
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
  <title>Region 1 Knowledge System Capabilities Brief</title>
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
    .proof-grid {
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 0.16in;
      align-items: stretch;
      margin-top: 0.15in;
    }
    .proof-panel {
      background: #ffffff;
      border: 1px solid #d4d9d0;
      border-radius: 8px;
      padding: 0.14in;
      box-shadow: 0 8px 18px rgba(29, 39, 34, 0.06);
    }
    .proof-panel strong {
      display: block;
      margin-bottom: 0.06in;
      color: #17202a;
      font-size: 11.1pt;
    }
    .proof-panel ul {
      margin: 0;
      padding-left: 0.16in;
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
    .hero-img { height: 4.05in; object-fit: contain; object-position: center; }
    .graph-figure { height: 5.65in; object-fit: contain; object-position: center; }
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
  </style>
</head>
<body>
  <section class="page">
    <header>
      <div class="kicker">Client Brief / Core System</div>
      <h1>Region 1 Knowledge System</h1>
      <p class="lede">A fully functional Region 1 knowledge system turns fragmented source, authority, evidence, and forest-plan data into a structured relational graph. It supports defensible, efficient land exchange execution now through NEPA review, with the same foundation ready to expand into additional workflows.</p>
      <p class="metric-context">Current Region 1 knowledge graph surface.</p>
      <div class="metric-grid">
        ${metric(metrics.nodeCount.toLocaleString(), "Region 1 graph nodes")}
        ${metric(metrics.edgeCount.toLocaleString(), "Region 1 graph edges")}
        ${metric(metrics.authorityFamilies.toLocaleString(), "authority families")}
        ${metric(metrics.sourceRecords.toLocaleString(), "source records")}
      </div>
    </header>
    <main>
      <img class="hero-img" src="assets/current_authority_stack.svg" alt="Region 1 knowledge system architecture" />
      <div class="proof-grid">
        <div class="proof-panel">
          <strong>What the system organizes</strong>
          <ul>
            <li>Source records, artifacts, and evidence spans.</li>
            <li>NEPA, USDA, Forest Service, and Forest Plan authority.</li>
            <li>Forest-plan profiles, components, and readiness state.</li>
            <li>V1 review outputs that can be traced back to source data.</li>
          </ul>
        </div>
        <div class="proof-panel">
          <strong>Why it matters</strong>
          <p>Teams can prepare packages faster, inspect support paths, and extend the same graph foundation to new services.</p>
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
      <div class="kicker">Traceability Architecture</div>
      <h2>Trace Every Output to Governed Evidence</h2>
      <p class="lede">Each capability is generated from governed sources. The trail runs from workbook scope and artifact hash to evidence span, source claim, authority decision, and output.</p>
    </header>
    <main>
      <img class="graph-figure" src="assets/graph_evidence_trace_service_view.png" alt="Evidence path from source record through extraction and review outputs" />
      <p class="caption">Traceability model: the output is the end of a chain, not a free-standing conclusion. The same path supports reports, QA replay, graph views, and reverse checks.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>Source boundary</strong>
          <p>Workbook scope, exclusions, partitions, catalog records, and hashes determine which materials can support review logic.</p>
        </div>
        <div class="callout">
          <strong>Reverse check</strong>
          <p>Generated outputs can be tested backward for unsupported claims, stale authority dependencies, missing support, unresolved applicability, and forest-plan gaps.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Current graph surface: ${metrics.nodeCount.toLocaleString()} nodes and ${metrics.edgeCount.toLocaleString()} edges.</span>
      <span>Catalog boundary: ${metrics.artifacts.toLocaleString()} cataloged artifacts linked to workbook records.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Knowledge Graph / Region 1</div>
      <h2>NEPA, USDA regulations, forest plans, and source evidence in one graph</h2>
      <p class="lede">The Region 1 graph presents NEPA authority, USDA regulations and procedures, source evidence, review views, and forest-plan data as connected layers without collapsing them into one undifferentiated network.</p>
    </header>
    <main>
      <img class="graph-figure tall" src="assets/graph_r1_showcase_view.png" alt="Region 1 3D graph showcase with NEPA, USDA regulations, source evidence, and forest-plan layers" />
      <div class="grid-2" style="margin-top:0.12in">
        <div class="callout">
          <strong>Forest plans stay separate</strong>
          <p>Forest-plan profiles and components are represented as their own layer, with readiness linked into review context instead of mixed into NEPA authority.</p>
        </div>
        <div class="callout">
          <strong>Authority and evidence stay inspectable</strong>
          <p>NEPA and USDA authority remain visible beside source records and evidence traces so reviewers can inspect the basis for a finding.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Graph layers: NEPA, USDA regulation, source evidence, review views, and forest plans.</span>
      <span>Forest plans: ${metrics.profileCount} profiles, ${metrics.graphReadyProfiles} graph-ready profile, and ${metrics.forestComponents.toLocaleString()} components.</span>
    </footer>
  </section>
</body>
</html>`;
}

function currentAuthorityStackSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="760" viewBox="0 0 1280 760" role="img" aria-label="Region 1 knowledge system architecture">
  ${svgDefs()}
  <rect width="1280" height="760" rx="28" fill="#f4f6f2"/>
  <rect x="34" y="32" width="1212" height="696" rx="26" fill="#ffffff" stroke="#d4d9d0"/>
  <text x="72" y="86" font-family="Inter, Arial, sans-serif" font-size="34" font-weight="880" fill="#17202a">From fragmented data to structured knowledge</text>
  <text x="72" y="126" font-family="Inter, Arial, sans-serif" font-size="18" fill="#58615b">Source records, authority logic, evidence traces, and forest-plan data resolve into a governed Region 1 graph for land exchange execution.</text>

  ${systemNode(150, 378, "#17202a", "Source Records", "workbook rows, artifacts, citations")}
  ${systemNode(418, 248, "#1f6f68", "Authority Layer", "NEPA, USDA, Forest Service, Forest Plan")}
  ${systemNode(418, 508, "#835b2f", "Evidence Layer", "spans, claims, support links")}
  ${systemHub(700, 378, "#2e5e88", "Structured R1 Knowledge", "relational graph foundation")}
  ${systemNode(982, 248, "#6f4f86", "NEPA V1 Review", "current function")}
  ${systemNode(982, 508, "#a65332", "Expandable Services", "future workflows and views")}

  ${flowArrow(270, 378, 565, 378)}
  ${flowArrow(520, 280, 610, 330)}
  ${flowArrow(520, 476, 610, 426)}
  ${flowArrow(795, 344, 882, 282)}
  ${flowArrow(795, 412, 882, 480)}

  <g transform="translate(76 628)" filter="url(#shadow)">
    <rect width="1126" height="70" rx="18" fill="#eef5f2" stroke="#c3d5ce"/>
    <text x="28" y="43" font-family="Inter, Arial, sans-serif" font-size="20" font-weight="850" fill="#1f6f68">Reusable value: turn fragmented Region 1 knowledge into a governed execution system.</text>
  </g>
</svg>`;
}

function evidenceTraceSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120" role="img" aria-label="Evidence path from source record through extraction and review outputs">
  ${svgDefs()}
  <rect width="1800" height="1120" rx="34" fill="#f4f6f2"/>
  <text x="72" y="92" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="880" fill="#17202a">Evidence trace</text>
  ${wrapSvgText("Every generated output remains linked to source identity, text evidence, authority status, and the graph record.", 72, 138, 1560, 22, "#58615b", 2)}

  <g transform="translate(72 214)" filter="url(#shadow)">
    <rect width="1656" height="430" rx="24" fill="#ffffff" stroke="#d4d9d0"/>
    ${traceStep(44, 108, "#17202a", "Source Record", "row identity, scope, citation")}
    ${traceStep(374, 108, "#1f6f68", "Evidence Span", "extracted text with artifact hash")}
    ${traceStep(704, 108, "#835b2f", "Source Claim", `${metrics.sourceClaims.toLocaleString()} support links`)}
    ${traceStep(1034, 108, "#6f4f86", "Authority Decision", "applies, screened out, unresolved")}
    ${traceStep(1364, 108, "#2e5e88", "Generated Output", "review result with evidence path")}
    ${flowArrow(300, 198, 364, 198)}
    ${flowArrow(630, 198, 694, 198)}
    ${flowArrow(960, 198, 1024, 198)}
    ${flowArrow(1290, 198, 1354, 198)}
    <text x="44" y="362" font-family="Inter, Arial, sans-serif" font-size="22" font-weight="850" fill="#17202a">Backward checks test the output against the record.</text>
    <text x="44" y="397" font-family="Inter, Arial, sans-serif" font-size="19" fill="#58615b">The trace exposes missing evidence, stale authority language, and unresolved applicability.</text>
  </g>

  <g transform="translate(72 728)" filter="url(#shadow)">
    <rect width="1656" height="234" rx="22" fill="#ffffff" stroke="#d4d9d0"/>
    <text x="32" y="50" font-family="Inter, Arial, sans-serif" font-size="27" font-weight="880" fill="#17202a">Outputs generated from the trace</text>
    ${outputTile(32, 88, "#2e5e88", "Compliance Matrix", "authorities, findings, evidence")}
    ${outputTile(432, 88, "#1f6f68", "Decision Support", "gaps, findings, signer readout")}
    ${outputTile(832, 88, "#835b2f", "Final QA", "replay checks and packet validation")}
    ${outputTile(1232, 88, "#6f4f86", "Knowledge Graph", "nodes, edges, scenes, validation")}
  </g>
</svg>`;
}

function r1GraphShowcaseSvg(metrics) {
  const scene = simplifiedGraphSceneSvg(metrics);
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1180" viewBox="0 0 1800 1180" role="img" aria-label="Simplified Region 1 3D graph model with NEPA, USDA regulations, evidence, review views, and forest plan layers">
  ${graphShowcaseDefs()}
  <rect width="1800" height="1180" rx="34" fill="#f4f6f2"/>
  <g transform="translate(72 82)" filter="url(#shadow)">
    <rect width="1656" height="940" rx="30" fill="#0d1821"/>
    <rect x="18" y="18" width="1620" height="904" rx="24" fill="url(#nightGlow)" stroke="#314653"/>
    <text x="54" y="78" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="900" fill="#f8faf7">Region 1 graph control model</text>
    <text x="54" y="118" font-family="Inter, Arial, sans-serif" font-size="21" fill="#c8d7d3">A reduced industrial view of the graph: distinct layers, conduit paths, and readable depth.</text>

    <g transform="translate(54 150)">
      ${scene}
    </g>

    <g transform="translate(54 812)">
      ${graphLegendChip(0, 0, "#2ad0bc", "NEPA")}
      ${graphLegendChip(186, 0, "#e7aa54", "USDA regulations")}
      ${graphLegendChip(472, 0, "#66a9e7", "Source evidence")}
      ${graphLegendChip(764, 0, "#71d58a", "Forest plans")}
      ${graphLegendChip(1038, 0, "#b38ee8", "Review views")}
    </g>
  </g>
</svg>`;
}

function systemNode(x, y, color, title, body) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <rect x="-112" y="-62" width="224" height="124" rx="18" fill="#ffffff" stroke="#d4d9d0"/>
    <rect x="-112" y="-62" width="224" height="8" rx="4" fill="${color}"/>
    <circle cx="-78" cy="-16" r="9" fill="${color}"/>
    ${wrapSvgText(title, -58, -10, 148, 18, "#17202a", 1, "start", "870")}
    ${wrapSvgText(body, 0, 30, 172, 14, "#58615b", 2, "middle")}
  </g>`;
}

function systemHub(x, y, color, title, body) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <circle r="100" fill="#ffffff" stroke="${color}" stroke-width="7"/>
    <circle r="64" fill="${color}" opacity="0.12"/>
    ${wrapSvgText(title, 0, -14, 150, 20, "#17202a", 2, "middle", "900")}
    ${wrapSvgText(body, 0, 38, 154, 14, "#58615b", 2, "middle")}
  </g>`;
}

function graphShowcaseDefs() {
  return `<defs>
    <radialGradient id="nightGlow" cx="50%" cy="42%" r="72%">
      <stop offset="0" stop-color="#183342"/>
      <stop offset="0.58" stop-color="#0f202b"/>
      <stop offset="1" stop-color="#0a131b"/>
    </radialGradient>
    <radialGradient id="floorGlow" cx="50%" cy="42%" r="68%">
      <stop offset="0" stop-color="#203c4b" stop-opacity="0.72"/>
      <stop offset="0.72" stop-color="#122633" stop-opacity="0.42"/>
      <stop offset="1" stop-color="#0d1821" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="nodeHub" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f8faf7"/>
      <stop offset="0.48" stop-color="#7da49d"/>
      <stop offset="1" stop-color="#163b40"/>
    </linearGradient>
    <linearGradient id="nodeNep" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#65fff0"/>
      <stop offset="0.46" stop-color="#178d83"/>
      <stop offset="1" stop-color="#073b3a"/>
    </linearGradient>
    <linearGradient id="nodeUsda" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ffd179"/>
      <stop offset="0.48" stop-color="#a56822"/>
      <stop offset="1" stop-color="#3d280f"/>
    </linearGradient>
    <linearGradient id="nodeSource" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#9bd4ff"/>
      <stop offset="0.48" stop-color="#326a98"/>
      <stop offset="1" stop-color="#102f49"/>
    </linearGradient>
    <linearGradient id="nodeForest" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#9cffaa"/>
      <stop offset="0.48" stop-color="#347449"/>
      <stop offset="1" stop-color="#12391f"/>
    </linearGradient>
    <linearGradient id="nodeReview" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#d6b4ff"/>
      <stop offset="0.48" stop-color="#7656a6"/>
      <stop offset="1" stop-color="#301d49"/>
    </linearGradient>
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
    <filter id="softBlur" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="4"/>
    </filter>
  </defs>`;
}

function simplifiedGraphSceneSvg(metrics) {
  const nodes = simplifiedGraphNodes(metrics);
  const lookup = Object.fromEntries(nodes.map((node) => [node.id, { ...node, ...graphProject(node) }]));
  const edges = simplifiedGraphEdges()
    .map(([from, to, color, width = 3, opacity = 0.48]) => graphSceneEdge(lookup[from], lookup[to], color, width, opacity))
    .join("");
  const nodeMarkup = Object.values(lookup)
    .sort((a, b) => a.screenY - b.screenY)
    .map((node) => graphSceneNode(node))
    .join("");

  return `<rect x="0" y="0" width="1548" height="624" rx="22" fill="#0b151e" stroke="#314653"/>
    <rect x="18" y="18" width="1512" height="588" rx="18" fill="url(#nightGlow)" stroke="#213a48"/>
    ${graphSceneFloor()}
    <g opacity="0.9">${edges}</g>
    <g>${nodeMarkup}</g>
    ${graphLayerLabel(58, 36, "#2ad0bc", "NEPA", `${metrics.nepaFamilyCount || 4} authority families`)}
    ${graphLayerLabel(1106, 34, "#e7aa54", "USDA Regulations", `${metrics.regulationAuthorityCount.toLocaleString()} regulation families`)}
    ${graphLayerLabel(64, 486, "#66a9e7", "Source Evidence", `${metrics.sourceRecords.toLocaleString()} source records`)}
    ${graphLayerLabel(642, 508, "#71d58a", "Forest Plans", `${metrics.profileCount} profiles / ${metrics.forestComponents.toLocaleString()} components`)}
    ${graphLayerLabel(1120, 476, "#b38ee8", "Review Views", "lenses, scenes, outputs")}`;
}

function simplifiedGraphNodes(metrics) {
  return [
    { id: "hub", x: 0, y: -18, z: 188, r: 45, gradient: "nodeHub", color: "#f8faf7", label: "R1 Graph", sublabel: `${metrics.nodeCount.toLocaleString()} / ${metrics.edgeCount.toLocaleString()}` },
    ...clusterNodes("nepa", { x: -440, y: -118, z: 112 }, "nodeNep", "#2ad0bc", [
      [-84, -42, 0, 20],
      [0, -72, 26, 15],
      [66, -35, 8, 14],
      [-96, 36, -10, 14],
      [-10, 24, 34, 23],
      [78, 42, -12, 12],
      [-4, -4, 54, 28]
    ]),
    ...clusterNodes("usda", { x: 360, y: -128, z: 124 }, "nodeUsda", "#e7aa54", [
      [-86, -42, 0, 17],
      [-10, -66, 22, 16],
      [74, -44, 4, 14],
      [-92, 34, -12, 14],
      [0, 22, 42, 28],
      [82, 36, -10, 13],
      [24, -8, 18, 21]
    ]),
    ...clusterNodes("source", { x: -408, y: 162, z: 22 }, "nodeSource", "#66a9e7", [
      [-112, -30, -8, 14],
      [-48, -56, 16, 14],
      [22, -44, 8, 13],
      [86, -18, -4, 12],
      [-124, 42, -20, 12],
      [-58, 54, 8, 16],
      [16, 42, 28, 22],
      [90, 44, -10, 13],
      [-2, -2, 48, 25]
    ]),
    ...clusterNodes("forest", { x: 60, y: 220, z: -18 }, "nodeForest", "#71d58a", [
      [-116, -58, -8, 15],
      [-48, -70, 16, 15],
      [38, -56, 8, 14],
      [112, -18, -10, 12],
      [-126, 36, -22, 12],
      [-62, 58, 10, 17],
      [16, 58, 24, 24],
      [90, 48, -12, 13],
      [-4, -10, 42, 29]
    ]),
    ...clusterNodes("review", { x: 432, y: 118, z: 58 }, "nodeReview", "#b38ee8", [
      [-90, -48, -8, 15],
      [-18, -66, 24, 16],
      [62, -38, 4, 13],
      [-94, 32, -14, 13],
      [-2, 22, 38, 24],
      [76, 38, -8, 12],
      [34, -8, 18, 19]
    ])
  ];
}

function clusterNodes(prefix, center, gradient, color, points) {
  return points.map(([x, y, z, r], index) => ({
    id: `${prefix}-${index}`,
    x: center.x + x,
    y: center.y + y,
    z: center.z + z,
    r,
    gradient,
    color
  }));
}

function simplifiedGraphEdges() {
  return [
    ["hub", "nepa-4", "#2ad0bc", 5, 0.62],
    ["hub", "nepa-6", "#2ad0bc", 4, 0.48],
    ["hub", "usda-4", "#e7aa54", 5, 0.62],
    ["hub", "usda-6", "#e7aa54", 4, 0.48],
    ["hub", "source-8", "#66a9e7", 4, 0.44],
    ["hub", "forest-8", "#71d58a", 5, 0.62],
    ["hub", "review-4", "#b38ee8", 4, 0.5],
    ["source-8", "forest-8", "#6fa6b7", 3, 0.36],
    ["source-6", "review-4", "#6f85ba", 3, 0.34],
    ["forest-8", "review-4", "#8fb6a1", 3, 0.36],
    ["nepa-6", "usda-4", "#526b78", 2, 0.32],
    ...clusterEdgeSet("nepa", "#2ad0bc"),
    ...clusterEdgeSet("usda", "#e7aa54"),
    ...clusterEdgeSet("source", "#66a9e7"),
    ...clusterEdgeSet("forest", "#71d58a"),
    ...clusterEdgeSet("review", "#b38ee8")
  ];
}

function clusterEdgeSet(prefix, color) {
  return [
    [`${prefix}-0`, `${prefix}-1`, color, 2, 0.4],
    [`${prefix}-1`, `${prefix}-2`, color, 2, 0.4],
    [`${prefix}-0`, `${prefix}-4`, color, 2, 0.34],
    [`${prefix}-4`, `${prefix}-5`, color, 2, 0.34],
    [`${prefix}-3`, `${prefix}-4`, color, 2, 0.34],
    [`${prefix}-4`, `${prefix}-6`, color, 2, 0.4]
  ];
}

function graphProject(node) {
  const z = node.z || 0;
  const scale = 1 + z / 880;
  return {
    screenX: 774 + node.x + z * 0.34,
    screenY: 366 + node.y * 0.62 - z * 0.52,
    screenR: Math.max(7, node.r * scale)
  };
}

function graphSceneFloor() {
  const horizontal = [-210, -150, -90, -30, 30, 90, 150, 210]
    .map((y) => {
      const a = graphProject({ x: -650, y, z: -92, r: 1 });
      const b = graphProject({ x: 650, y, z: -92, r: 1 });
      const controlY = ((a.screenY + b.screenY) / 2 - 28).toFixed(1);
      return `<path d="M ${a.screenX.toFixed(1)} ${a.screenY.toFixed(1)} Q 774 ${controlY} ${b.screenX.toFixed(1)} ${b.screenY.toFixed(1)}" fill="none" stroke="#355363" stroke-width="1.6" stroke-opacity="0.32"/>`;
    })
    .join("");
  const vertical = [-600, -450, -300, -150, 0, 150, 300, 450, 600]
    .map((x) => {
      const a = graphProject({ x, y: -236, z: -92, r: 1 });
      const b = graphProject({ x, y: 236, z: -92, r: 1 });
      return `<path d="M ${a.screenX.toFixed(1)} ${a.screenY.toFixed(1)} L ${b.screenX.toFixed(1)} ${b.screenY.toFixed(1)}" fill="none" stroke="#355363" stroke-width="1.4" stroke-opacity="0.24"/>`;
    })
    .join("");
  return `<g>
    <ellipse cx="774" cy="420" rx="675" ry="248" fill="url(#floorGlow)"/>
    ${horizontal}
    ${vertical}
  </g>`;
}

function graphSceneEdge(from, to, color, width, opacity) {
  if (!from || !to) {
    return "";
  }
  const railY = Math.min(from.screenY, to.screenY) - 22;
  const startX = from.screenX.toFixed(1);
  const startY = from.screenY.toFixed(1);
  const endX = to.screenX.toFixed(1);
  const endY = to.screenY.toFixed(1);
  const rail = railY.toFixed(1);
  return `<path d="M ${startX} ${startY} L ${startX} ${rail} L ${endX} ${rail} L ${endX} ${endY}" fill="none" stroke="#07121a" stroke-width="${width + 4}" stroke-opacity="${opacity * 0.32}" stroke-linecap="square" stroke-linejoin="miter"/>
  <path d="M ${startX} ${startY} L ${startX} ${rail} L ${endX} ${rail} L ${endX} ${endY}" fill="none" stroke="${color}" stroke-width="${width}" stroke-opacity="${opacity}" stroke-linecap="square" stroke-linejoin="miter"/>`;
}

function graphSceneNode(node) {
  const shadowOpacity = node.id === "hub" ? 0.34 : 0.22;
  const plateWidth = node.screenR * (node.id === "hub" ? 2.9 : 2.42);
  const plateHeight = node.screenR * (node.id === "hub" ? 1.38 : 1.14);
  const depth = Math.max(8, node.screenR * 0.24);
  const bevel = Math.min(18, plateHeight * 0.34);
  const halfWidth = plateWidth / 2;
  const halfHeight = plateHeight / 2;
  const topPoints = [
    [-halfWidth + bevel, -halfHeight],
    [halfWidth, -halfHeight],
    [halfWidth - bevel, halfHeight],
    [-halfWidth, halfHeight],
    [-halfWidth + bevel, -halfHeight]
  ]
    .map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  const sidePoints = [
    [-halfWidth, halfHeight],
    [halfWidth - bevel, halfHeight],
    [halfWidth - bevel - depth * 0.75, halfHeight + depth],
    [-halfWidth - depth * 0.75, halfHeight + depth],
    [-halfWidth, halfHeight]
  ]
    .map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  const label = node.label
    ? `<text y="-7" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="20" font-weight="900" fill="#f8faf7">${escapeXml(node.label)}</text>
      <text y="19" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="13" font-weight="760" fill="#d6e6e2">${escapeXml(node.sublabel)}</text>`
    : "";
  const filter = node.id === "hub" ? ' filter="url(#glow)"' : "";
  const labelMarkup = label ? `\n    ${label}` : "";
  return `<g transform="translate(${node.screenX.toFixed(1)} ${node.screenY.toFixed(1)})"${filter}>
    <ellipse cx="${(-depth * 0.34).toFixed(1)}" cy="${(halfHeight + depth * 0.86).toFixed(1)}" rx="${(plateWidth * 0.58).toFixed(1)}" ry="${(plateHeight * 0.34).toFixed(1)}" fill="#000000" opacity="${shadowOpacity}" filter="url(#softBlur)"/>
    <polygon points="${sidePoints}" fill="#07131b" stroke="${node.color}" stroke-width="1.2" stroke-opacity="0.48"/>
    <polygon points="${topPoints}" fill="url(#${node.gradient})" stroke="${node.color}" stroke-width="${node.id === "hub" ? 3.2 : 1.8}"/>
    <polyline points="${(-halfWidth + bevel + 7).toFixed(1)},${(-halfHeight + 7).toFixed(1)} ${(halfWidth - 9).toFixed(1)},${(-halfHeight + 7).toFixed(1)} ${(halfWidth - bevel - 9).toFixed(1)},${(halfHeight - 7).toFixed(1)}" fill="none" stroke="#ffffff" stroke-width="1.5" stroke-opacity="0.22"/>
    <rect x="${(-halfWidth + 10).toFixed(1)}" y="${(-halfHeight + 10).toFixed(1)}" width="${Math.max(7, node.screenR * 0.22).toFixed(1)}" height="${Math.max(7, node.screenR * 0.22).toFixed(1)}" fill="#f8faf7" opacity="0.42"/>${labelMarkup}
  </g>`;
}

function graphLayerLabel(x, y, color, title, subtitle) {
  const width = Math.max(232, Math.min(342, title.length * 14 + subtitle.length * 6 + 42));
  return `<g transform="translate(${x} ${y})">
    <path d="M 0 0 H ${width} V 70 H 14 L 0 56 Z" fill="#102431" stroke="#314653" opacity="0.96"/>
    <rect x="0" y="0" width="${width}" height="4" fill="${color}"/>
    <rect x="24" y="29" width="14" height="14" fill="${color}"/>
    <text x="48" y="30" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="900" fill="#f8faf7">${escapeXml(title)}</text>
    <text x="48" y="52" font-family="Inter, Arial, sans-serif" font-size="14" font-weight="720" fill="${color}">${escapeXml(subtitle)}</text>
  </g>`;
}

function graphLegendChip(x, y, color, label) {
  const width = Math.max(210, label.length * 11 + 54);
  return `<g transform="translate(${x} ${y})">
    <path d="M 0 0 H ${width} V 54 H 12 L 0 42 Z" fill="#122633" stroke="#314653"/>
    <rect x="18" y="21" width="14" height="14" fill="${color}"/>
    <text x="48" y="34" font-family="Inter, Arial, sans-serif" font-size="17" font-weight="820" fill="#f8faf7">${escapeXml(label)}</text>
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

function flowArrow(x1, y1, x2, y2) {
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="#8b948d" stroke-width="6" stroke-linecap="round" marker-end="url(#arrow)"/>`;
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
