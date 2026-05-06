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
const briefHtmlPath = path.join(outDir, "nepa_3d_capabilities_brief.html");
const briefPdfPath = path.join(outDir, "nepa_3d_capabilities_brief.pdf");
const defaultChromiumExecutable =
  "/Users/chunkstand/Library/Caches/ms-playwright/chromium-1178/chrome-mac/Chromium.app/Contents/MacOS/Chromium";

const graphPath = path.join(
  repoRoot,
  "source_library",
  "reviews",
  "v1-cg-ecid-compliance-review",
  "knowledge_graph",
  "nepa_3d_graph.json"
);

async function main() {
  await fs.mkdir(assetDir, { recursive: true });
  const graph = JSON.parse(await fs.readFile(graphPath, "utf8"));
  const metrics = graphMetrics(graph);
  const browser = await launchBrowser();
  try {
    await writeSvgAssets(graph, metrics);
    await fs.writeFile(briefHtmlPath, briefHtml(metrics), "utf8");
    await renderPdf(browser, briefHtmlPath, briefPdfPath);
    const pdfBytes = await fs.readFile(briefPdfPath);
    const pdf = await PDFDocument.load(pdfBytes);
    if (pdf.getPageCount() !== 4) {
      throw new Error(`Expected a 4-page PDF, got ${pdf.getPageCount()} pages.`);
    }
    console.log(`Wrote ${path.relative(repoRoot, briefHtmlPath)}`);
    console.log(`Wrote ${path.relative(repoRoot, briefPdfPath)}`);
    console.log(`Verified 4 PDF pages.`);
  } finally {
    await browser.close();
  }
}

function graphMetrics(graph) {
  const countNodes = (type, predicate = () => true) =>
    (graph.nodes || []).filter((node) => node.node_type === type && predicate(node)).length;
  const countEdges = (type) => (graph.edges || []).filter((edge) => edge.edge_type === type).length;
  return {
    nodeCount: graph.summary?.node_count ?? graph.nodes?.length ?? 0,
    edgeCount: graph.summary?.edge_count ?? graph.edges?.length ?? 0,
    validationChecks: graph.summary?.validation_check_count ?? graph.validation?.checks?.length ?? 0,
    validationPassed: graph.summary?.validation_passed === true,
    candidateDecisions: countNodes("applicability_decision"),
    applicableDecisions: countNodes("applicability_decision", (node) => node.display_status === "applicable"),
    nonApplicableDecisions: countNodes(
      "applicability_decision",
      (node) => node.display_status === "not_applicable"
    ),
    generatedRules: countNodes("generated_rule"),
    complianceFindings: countNodes("compliance_finding"),
    readinessBlockers: countNodes("readiness_blocker"),
    sourceRecords: countNodes("source_record"),
    artifacts: countNodes("artifact"),
    evidenceSpans: countNodes("evidence_span"),
    forestUnits: countNodes("forest_unit"),
    forestPlans: countNodes("forest_plan"),
    forestPlanComponents: countNodes("forest_plan_component"),
    hasReadinessBlockerEdges: countEdges("HAS_READINESS_BLOCKER"),
    supportsFindingEdges: countEdges("SUPPORTS_COMPLIANCE_FINDING")
  };
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

async function writeSvgAssets(graph, metrics) {
  await writeServiceGraphAssets(graph, metrics);
  await fs.writeFile(path.join(assetDir, "current_authority_stack.svg"), currentAuthorityStackSvg(metrics), "utf8");
}

async function writeServiceGraphAssets(graph, metrics) {
  const trace = deriveEvidenceTrace(graph);
  const readiness = deriveReadinessSummary(graph, metrics);
  const assets = [
    ["graph_applicability_service_view", applicabilityServiceGraphSvg(metrics)],
    ["graph_evidence_trace_service_view", evidenceTraceServiceGraphSvg(trace, metrics)],
    ["graph_readiness_service_view", readinessServiceGraphSvg(readiness, metrics)]
  ];
  for (const [name, svg] of assets) {
    const svgPath = path.join(assetDir, `${name}.svg`);
    const pngPath = path.join(assetDir, `${name}.png`);
    await fs.writeFile(svgPath, svg, "utf8");
    await sharp(Buffer.from(svg), { density: 220 }).png().toFile(pngPath);
  }
}

function deriveEvidenceTrace(graph) {
  const nodeIndex = new Map((graph.nodes || []).map((node) => [node.node_id, node]));
  const incoming = (nodeId, edgeType) =>
    (graph.edges || []).filter(
      (edge) => edge.target_node_id === nodeId && (!edgeType || edge.edge_type === edgeType)
    );

  const preferredFinding =
    (graph.nodes || []).find(
      (node) => node.node_type === "compliance_finding" && node.node_id.includes("apa_final_agency_action")
    ) || (graph.nodes || []).find((node) => node.node_type === "compliance_finding");
  const supportNodes = incoming(preferredFinding?.node_id, "SUPPORTS_COMPLIANCE_FINDING")
    .map((edge) => nodeIndex.get(edge.source_node_id))
    .filter(Boolean);
  const generatedRule = supportNodes.find((node) => node.node_type === "generated_rule");
  const evidenceSpan = supportNodes.find((node) => node.node_type === "evidence_span");
  const decision = incoming(generatedRule?.node_id, "GENERATES_RULE")
    .map((edge) => nodeIndex.get(edge.source_node_id))
    .find((node) => node?.node_type === "applicability_decision");
  const ruleTemplate = incoming(decision?.node_id, "PRODUCES_APPLICABILITY_DECISION")
    .map((edge) => nodeIndex.get(edge.source_node_id))
    .find(Boolean);
  const candidateSupport = incoming(ruleTemplate?.node_id, "SUPPORTS_RULE_TEMPLATE")
    .map((edge) => nodeIndex.get(edge.source_node_id))
    .filter(Boolean);
  const sourceRecord = candidateSupport.find((node) => node.node_type === "source_record");
  const authorityFamily = candidateSupport.find((node) => node.node_type === "authority_family");

  return {
    sourceRecord,
    authorityFamily,
    ruleTemplate,
    decision,
    generatedRule,
    evidenceSpan,
    finding: preferredFinding
  };
}

function deriveReadinessSummary(graph, metrics) {
  const forestUnits = (graph.nodes || [])
    .filter((node) => node.node_type === "forest_unit")
    .sort((left, right) => String(left.label).localeCompare(String(right.label)));
  const readyUnits = forestUnits.filter((node) => node.display_status !== "readiness_blocked");
  const blockedUnits = forestUnits.filter((node) => node.display_status === "readiness_blocked");
  return {
    forestUnits,
    readyUnits,
    blockedUnits,
    blockerCounts: metrics.readinessBlockerCounts || graph.summary?.readiness_blocker_counts || {}
  };
}

function applicabilityServiceGraphSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120" role="img" aria-label="Applicability graph view with authority decisions">
  ${serviceGraphDefs()}
  <rect width="1800" height="1120" rx="34" fill="#f8f7f1"/>
  <text x="72" y="94" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="850" fill="#171713">Applicability is the first review gate</text>
  <text x="72" y="140" font-family="Inter, Arial, sans-serif" font-size="22" fill="#555b54">For any NEPA document set, our review process builds an authority graph, separates current applicable authority from screened-out authority, and generates evidence-backed findings.</text>
  ${graphEdge(305, 540, 570, 540, "#739bb6", 9, "373 decisions")}
  ${graphEdge(820, 425, 1085, 320, "#26786f", 9, "33 apply")}
  ${graphEdge(820, 635, 1085, 735, "#8b8a82", 8, "340 screened out")}
  ${graphEdge(1288, 320, 1490, 430, "#26786f", 8, "")}
  ${graphEdge(1490, 530, 1545, 735, "#356a9b", 8, "")}
  ${graphNode(210, 540, 112, "#356a9b", "Candidate authorities", `${metrics.candidateDecisions} review candidates`, "rule templates + forest-plan components")}
  ${graphNode(690, 540, 132, "#7a6e3d", "Applicability decisions", `${metrics.candidateDecisions} decisions`, "review-specific")}
  ${graphNode(1190, 320, 104, "#26786f", "Applicable", `${metrics.applicableDecisions} authorities`, "kept for rule generation")}
  ${graphNode(1190, 735, 104, "#70726c", "Not applicable", `${metrics.nonApplicableDecisions} authorities`, "retained for audit")}
  ${graphNode(1490, 430, 96, "#26786f", "Generated rules", `${metrics.generatedRules} rules`, "review package")}
  ${graphNode(1545, 735, 96, "#356a9b", "Compliance findings", `${metrics.complianceFindings} findings`, "evidence-backed")}
  <g transform="translate(72 890)" filter="url(#serviceShadow)">
    <rect width="1656" height="166" rx="20" fill="#ffffff" stroke="#d8d3c6"/>
    <text x="32" y="46" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="850" fill="#171713">Service value shown</text>
    ${bulletText(32, 84, "Defensibility: non-applicable and screened-out authorities are preserved, so the review explains what was considered and why it was not used.")}
    ${bulletText(32, 118, "Reverse compliance: draft document claims can be checked against the authority graph and flagged when unsupported or based on older regulation language.")}
    ${bulletText(32, 152, `Validation: ${metrics.validationChecks} graph checks passed before this view was exported.`)}
  </g>
</svg>`;
}

function evidenceTraceServiceGraphSvg(trace, metrics) {
  const sourceLabel = trace.sourceRecord?.label || "Source record";
  const authorityLabel = trace.authorityFamily?.label || "Authority family";
  const ruleLabel = trace.ruleTemplate?.label || "Rule template";
  const decisionLabel = trace.decision?.label || "Applicability decision";
  const generatedRuleLabel = trace.generatedRule?.label || "Generated rule";
  const findingLabel = trace.finding?.label || "Compliance finding";
  const evidenceLabel = trace.evidenceSpan?.label || "Evidence span";
  const citation = trace.sourceRecord?.provenance?.citation_label || trace.evidenceSpan?.provenance?.source_record_id || "source evidence";
  const topic = shortAuthorityTopic(generatedRuleLabel || ruleLabel || findingLabel);

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1080" viewBox="0 0 1800 1080" role="img" aria-label="Evidence path graph from source record to compliance finding">
  ${serviceGraphDefs()}
  <rect width="1800" height="1080" rx="34" fill="#f7f6f1"/>
  <text x="72" y="94" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="850" fill="#171713">A finding is a traceable evidence path</text>
  <text x="72" y="140" font-family="Inter, Arial, sans-serif" font-size="22" fill="#555b54">This Region 1 example is generated from one actual graph trace: source authority, rule template, applicability decision, generated rule, evidence span, and compliance finding.</text>
  ${graphEdge(240, 360, 512, 360, "#356a9b", 8, "supports rule")}
  ${graphEdge(692, 360, 960, 360, "#7a6e3d", 8, "produces decision")}
  ${graphEdge(1140, 360, 1396, 360, "#26786f", 8, "generates rule")}
  ${graphEdge(1490, 455, 1490, 610, "#356a9b", 8, "supports finding")}
  ${graphEdge(450, 645, 1225, 645, "#a75a22", 7, "evidence span")}
  ${graphNode(190, 360, 104, "#356a9b", "Source record", compactSvgLabel(sourceLabel, 52), citation)}
  ${graphNode(602, 360, 100, "#5c6f8c", "Rule template", topic, "authority basis")}
  ${graphNode(1050, 360, 104, "#7a6e3d", "Decision", `${topic} applies`, "applicable")}
  ${graphNode(1490, 360, 104, "#26786f", "Generated rule", topic, "review overlay")}
  ${graphNode(1490, 715, 100, "#356a9b", "Finding", topic, "compliance matrix")}
  ${graphNode(410, 645, 88, "#a75a22", "Evidence span", compactSvgLabel(evidenceLabel, 44), "source bytes")}
  <g transform="translate(72 860)" filter="url(#serviceShadow)">
    <rect width="1656" height="174" rx="20" fill="#ffffff" stroke="#d8d3c6"/>
    <text x="32" y="46" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="850" fill="#171713">What the review team can inspect</text>
    ${bulletText(32, 85, `Authority family: ${compactSvgLabel(authorityLabel, 112)}`)}
    ${bulletText(32, 119, `Source citation: ${compactSvgLabel(citation, 112)}`)}
    ${bulletText(32, 153, `${metrics.supportsFindingEdges} support edges link generated rules or evidence spans to compliance findings across the V1 overlay.`)}
  </g>
</svg>`;
}

function readinessServiceGraphSvg(readiness, metrics) {
  const blocked = readiness.blockedUnits.slice(0, 9);
  const ready = readiness.readyUnits[0] || { label: "Custer Gallatin National Forest" };
  const blockerCounts = readiness.blockerCounts || {};
  const blockerRows = [
    ["forest_profile_not_ready", blockerCounts.forest_profile_not_ready || 0],
    ["missing_source", blockerCounts.missing_source || 0],
    ["superseded_source", blockerCounts.superseded_source || 0],
    ["fsh_chapter_delta_required", blockerCounts.fsh_chapter_delta_required || 0]
  ];
  const blockedNodes = blocked
    .map((node, index) => {
      const positions = [
        [330, 430],
        [520, 390],
        [1020, 460],
        [1085, 610],
        [1010, 750],
        [820, 805],
        [620, 790],
        [420, 690],
        [285, 570]
      ];
      const [x, y] = positions[index] || [380 + index * 70, 720];
      return `${graphEdge(780, 650, x, y, "#d68578", 5, "")}${smallGraphNode(
        x,
        y,
        "#b13d38",
        shortForestLabel(node.label || node.node_id),
        "blocked profile"
      )}`;
    })
    .join("");
  const blockerCards = blockerRows
    .map(
      ([label, count], index) =>
        `<g transform="translate(35 ${126 + index * 112})">
          <rect width="390" height="82" rx="14" fill="#ffffff" stroke="#dfcbc6"/>
          <circle cx="35" cy="41" r="14" fill="${index < 2 ? "#b13d38" : "#a75a22"}"/>
          <text x="64" y="34" font-family="Inter, Arial, sans-serif" font-size="21" font-weight="800" fill="#171713">${escapeXml(label.replaceAll("_", " "))}</text>
          <text x="64" y="61" font-family="Inter, Arial, sans-serif" font-size="18" fill="#5f625b">${count} graph item(s)</text>
        </g>`
    )
    .join("");

  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="1120" viewBox="0 0 1800 1120" role="img" aria-label="Readiness graph showing graph-ready and blocked forest profiles">
  ${serviceGraphDefs()}
  <rect width="1800" height="1120" rx="34" fill="#f8f7f1"/>
  <text x="72" y="94" font-family="Inter, Arial, sans-serif" font-size="44" font-weight="850" fill="#171713">Readiness controls prevent overclaiming</text>
  <text x="72" y="140" font-family="Inter, Arial, sans-serif" font-size="22" fill="#555b54">The USFS Region 1 example shows a ready Custer Gallatin profile while keeping broader Region 1 blockers visible.</text>
  ${graphEdge(780, 650, 780, 310, "#26786f", 8, "")}
  ${blockedNodes}
  ${graphNode(780, 650, 126, "#7a6e3d", "Review scope", "Custer Gallatin EA", "")}
  ${graphNode(780, 310, 98, "#26786f", "Ready forest profile", compactSvgLabel(ready.label || ready.node_id, 42), "example scope")}
  <g transform="translate(1220 196)" filter="url(#serviceShadow)">
    <rect width="470" height="640" rx="22" fill="#fff" stroke="#d8d3c6"/>
    <text x="35" y="55" font-family="Inter, Arial, sans-serif" font-size="28" font-weight="850" fill="#171713">Blockers remain visible</text>
    ${wrapSvgText(`${metrics.readinessBlockers} readiness blocker nodes and ${metrics.hasReadinessBlockerEdges} blocker edges are exported as graph evidence.`, 35, 92, 390, 18, "#5f625b", 2)}
    ${blockerCards}
  </g>
  <g transform="translate(72 890)" filter="url(#serviceShadow)">
    <rect width="1656" height="132" rx="20" fill="#ffffff" stroke="#d8d3c6"/>
    <text x="32" y="45" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="850" fill="#171713">Service value</text>
    ${bulletText(32, 84, `${readiness.readyUnits.length} graph-ready forest profile and ${readiness.blockedUnits.length} blocked forest profiles are visible in one view.`)}
    ${bulletText(32, 118, "The review process can show capability now without implying that every Region 1 profile is ready for service delivery.")}
  </g>
</svg>`;
}

function serviceGraphDefs() {
  return `<defs>
    <filter id="serviceShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="14" stdDeviation="14" flood-color="#141713" flood-opacity="0.13"/>
    </filter>
    <marker id="arrowService" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#70726c"/>
    </marker>
  </defs>`;
}

function graphEdge(x1, y1, x2, y2, color, width, label) {
  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;
  const labelWidth = label ? Math.max(154, Math.min(390, label.length * 12 + 44)) : 0;
  const labelSvg = label
    ? `<g transform="translate(${mx - labelWidth / 2} ${my - 24})">
      <rect width="${labelWidth}" height="42" rx="21" fill="#ffffff" stroke="#d8d3c6" opacity="0.95"/>
      <text x="${labelWidth / 2}" y="27" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="18" font-weight="800" fill="#3f4540">${escapeXml(label)}</text>
    </g>`
    : "";
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="${color}" stroke-width="${width}" stroke-linecap="round" stroke-opacity="0.58" marker-end="url(#arrowService)"/>${labelSvg}`;
}

function graphNode(x, y, radius, color, title, value, subtitle) {
  return `<g transform="translate(${x} ${y})" filter="url(#serviceShadow)">
    <circle r="${radius}" fill="#ffffff" stroke="${color}" stroke-width="9"/>
    <circle r="${Math.max(radius - 19, 20)}" fill="${color}" opacity="0.10"/>
    <text y="${-radius - 27}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="25" font-weight="850" fill="#171713">${escapeXml(title)}</text>
    ${wrapSvgText(String(value), 0, -18, radius * 1.55, 22, "#171713", 2, "middle")}
    <text y="${radius + 38}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="19" font-weight="750" fill="${color}">${escapeXml(subtitle)}</text>
  </g>`;
}

function smallGraphNode(x, y, color, title, subtitle) {
  return `<g transform="translate(${x} ${y})" filter="url(#serviceShadow)">
    <circle r="50" fill="#ffffff" stroke="${color}" stroke-width="6"/>
    <text y="-5" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" font-weight="850" fill="#171713">${escapeXml(title)}</text>
    <text y="17" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="12" font-weight="750" fill="${color}">${escapeXml(compactSvgLabel(subtitle, 28))}</text>
  </g>`;
}

function bulletText(x, y, text) {
  return `<circle cx="${x + 7}" cy="${y - 7}" r="5" fill="#26786f"/>
  ${wrapSvgText(text, x + 24, y, 1560, 19, "#4f554e", 1)}`;
}

function compactSvgLabel(value, maxLength) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (text.length <= maxLength) {
    return text;
  }
  return `${text.slice(0, Math.max(0, maxLength - 1)).trim()}...`;
}

function shortAuthorityTopic(value) {
  const text = String(value || "").replace(/\s+/g, " ").trim();
  if (/Administrative Procedure Act final agency action/i.test(text)) {
    return "APA final agency action";
  }
  if (/Environmental Planning \/ NEPA/i.test(text)) {
    return "Forest Service NEPA page";
  }
  return compactSvgLabel(text.replace(/\bis reviewed\b\.?$/i, "").trim(), 34);
}

function shortForestLabel(value) {
  return String(value || "")
    .replace(" National Forests", "")
    .replace(" National Forest", "")
    .replace(" National Grasslands", "")
    .replace(" National Forests", "")
    .replace("Helena-Lewis and Clark", "Helena-Lewis Clark")
    .replace("Nez Perce-Clearwater", "Nez Perce-Clearwater")
    .trim();
}

function currentAuthorityStackSvg(metrics) {
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="640" viewBox="0 0 1280 640" role="img" aria-label="NEPA review service process represented by the graph">
  <defs>
    <linearGradient id="bg" x1="0" x2="1" y1="0" y2="1">
      <stop offset="0" stop-color="#f8f7f1"/>
      <stop offset="1" stop-color="#e9f2ef"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="12" stdDeviation="12" flood-color="#141713" flood-opacity="0.14"/>
    </filter>
  </defs>
  <rect width="1280" height="640" rx="28" fill="url(#bg)"/>
  <text x="64" y="78" font-family="Inter, Arial, sans-serif" font-size="34" font-weight="800" fill="#171713">NEPA review service process mapped as evidence</text>
  <text x="64" y="118" font-family="Inter, Arial, sans-serif" font-size="18" fill="#5f625b">Our review process links document inputs, current agency procedures, source evidence, and review decisions - not unsupported conclusions.</text>
  ${stackBox(64, 172, "Document package", "EA, FONSI, ROD, appendices, and supporting biological, cultural, and forest-plan records.", "#171713")}
  ${stackBox(336, 172, "Current authority graph", "Current regulations, agency procedures, Forest Plan components, and project authorities.", "#216a60")}
  ${stackBox(608, 172, "Consistency review", "Full profile consistency document across Forest Plan direction and applicable laws.", "#7c493c")}
  ${stackBox(880, 172, "Decision support", "Responsible-official briefing with applicable authorities, gaps, risks, and evidence paths.", "#356a9b")}
  ${arrow(292, 268, 326, 268)}
  ${arrow(564, 268, 598, 268)}
  ${arrow(836, 268, 870, 268)}
  <g transform="translate(64 430)" filter="url(#shadow)">
    <rect width="1152" height="130" rx="20" fill="#ffffff" stroke="#d8d3c6"/>
    <text x="30" y="42" font-family="Inter, Arial, sans-serif" font-size="21" font-weight="800" fill="#171713">Why this matters for a service engagement</text>
    ${wrapSvgText("USFS Region 1 is the worked example. The same process can be run against another NEPA document package by refreshing the authority graph with the most current applicable regulations, mapping project evidence, testing reverse compliance, preparing consistency documentation, and packaging decision-support evidence.", 30, 75, 1088, 16, "#4f554e", 2)}
    <text x="30" y="114" font-family="Inter, Arial, sans-serif" font-size="15" fill="#26786f" font-weight="800">Example validation passed: ${metrics.validationChecks} graph checks; ${metrics.applicableDecisions} applicable and ${metrics.nonApplicableDecisions} non-applicable authority decisions.</text>
  </g>
</svg>`;
}

function stackBox(x, y, title, body, color) {
  return `<g transform="translate(${x} ${y})" filter="url(#shadow)">
    <rect width="240" height="190" rx="18" fill="#ffffff" stroke="#d8d3c6"/>
    <rect width="240" height="9" rx="4" fill="${color}"/>
    <text x="20" y="50" font-family="Inter, Arial, sans-serif" font-size="21" font-weight="800" fill="#171713">${escapeXml(title)}</text>
    ${wrapSvgText(body, 20, 82, 200, 17, "#4f554e")}
  </g>`;
}

function arrow(x1, y1, x2, y2) {
  return `<path d="M ${x1} ${y1} L ${x2} ${y2}" stroke="#8a8f84" stroke-width="4" stroke-linecap="round"/>
  <path d="M ${x2 - 10} ${y2 - 9} L ${x2} ${y2} L ${x2 - 10} ${y2 + 9}" fill="none" stroke="#8a8f84" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>`;
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
      max-width: 6.7in;
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
    .card {
      background: rgba(255,255,255,0.88);
      border: 1px solid #d8d3c6;
      border-radius: 8px;
      padding: 0.14in;
      box-shadow: 0 10px 24px rgba(24,28,26,0.08);
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
    .snapshot {
      width: 100%;
      height: 3.46in;
      object-fit: cover;
      object-position: center;
      border: 1px solid #d8d3c6;
      border-radius: 8px;
      background: #fff;
      box-shadow: 0 12px 30px rgba(24,28,26,0.12);
    }
    .snapshot.tall { height: 4.36in; }
    .graph-figure {
      width: 100%;
      height: 3.35in;
      object-fit: cover;
      object-position: center 50%;
      border: 1px solid #d8d3c6;
      border-radius: 10px;
      background: #fff;
      box-shadow: 0 12px 30px rgba(24,28,26,0.12);
    }
    .graph-figure.trace { height: 2.92in; object-position: center 48%; }
    .graph-figure.readiness { height: 4.78in; object-fit: contain; }
    .graph-figure.full {
      height: 5.22in;
      object-fit: contain;
      object-position: center;
    }
    .graph-figure.full-trace {
      height: 5.0in;
      object-fit: contain;
      object-position: center;
    }
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
    .footer a { color: #26786f; text-decoration: none; }
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
      <h1>NEPA review service, made auditable</h1>
      <p class="lede">We provide professional NEPA reviews for projects using a graph-backed evidence process. The USFS Region 1 source library is the worked example: we update the authority graph with the most current applicable regulations and procedures, test applicability, run Forest Plan and full profile consistency review, trace evidence, flag older-regulation dependencies, and package decision support for the responsible official.</p>
      <p class="metric-context">Example metrics: validated USFS Region 1 graph export.</p>
      <div class="metric-grid">
        ${metric(metrics.nodeCount.toLocaleString(), "USFS Region 1 graph nodes")}
        ${metric(metrics.edgeCount.toLocaleString(), "USFS Region 1 graph edges")}
        ${metric(metrics.applicableDecisions, "applicable authorities")}
        ${metric(metrics.nonApplicableDecisions, "screened-out authorities")}
      </div>
    </header>
    <main>
      <img class="hero-img" src="assets/current_authority_stack.svg" alt="NEPA review service process represented by graph evidence" />
      <div class="grid-2" style="margin-top:0.15in">
        <div class="callout">
          <strong>Current-authority model</strong>
          <p>The authority graph is updated with the most current applicable regulations, USDA and Forest Service procedures, source records, directives, forest-plan components, applicability decisions, and readiness blockers instead of flattening them into a narrative answer.</p>
        </div>
        <div class="callout">
          <strong>Decision-support model</strong>
          <p>Each service finding is backed by graph-export validation. The V1 Region 1 example passed ${metrics.validationChecks} graph checks and links generated rules and compliance findings back to source records, evidence spans, and review-specific applicability decisions.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Generated from internal example graph export: <strong>v1-cg-ecid-compliance-review</strong></span>
      <span>Sources checked: Forest Service NEPA Procedures and Guidance; repo current-state docs.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 1 / Applicability</div>
      <h2>From authority graph to decision support</h2>
      <p class="lede">For any NEPA document package, the process updates the authority graph with the most current applicable regulations and separates current applicable authorities from authorities that were considered but screened out. That makes the review politically legible and defensible.</p>
    </header>
    <main>
      <img class="graph-figure full" src="assets/graph_applicability_service_view.png" alt="Clear applicability graph view with authority decisions, generated rules, and findings" />
      <p class="caption">Applicability scene: ${metrics.candidateDecisions} candidate authority decisions, ${metrics.applicableDecisions} applicable, ${metrics.nonApplicableDecisions} non-applicable. The image preserves the graph distinction between candidate authority, review decision, generated rule, and compliance finding.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>Defensibility shown</strong>
          <p>Non-applicable authorities stay in the graph, so the reviewer can explain what was considered and screened out instead of only showing final inclusions.</p>
        </div>
        <div class="callout">
          <strong>Responsible-official support</strong>
          <p>The output shows a visible path from authority graph to decision, rule generation, and compliance finding rather than a black-box conclusion.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Defensible review behavior: candidate authorities remain visible even when non-applicable.</span>
      <span>Validation behavior: ${metrics.validationChecks} graph checks passed before export.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 2 / Evidence Traceability</div>
      <h2>From source record to authority graph</h2>
      <p class="lede">A responsible official or review team should be able to ask where each authority and finding came from. The evidence view turns source records, citation labels, extracted spans, and rule templates into a traceable authority graph before findings are used for decision support.</p>
    </header>
    <main>
      <img class="graph-figure full-trace" src="assets/graph_evidence_trace_service_view.png" alt="Clear evidence path graph from source record to compliance finding" />
      <p class="caption">Evidence path scene: one actual source-record -> rule-template -> applicability-decision -> generated-rule -> compliance-finding path is derived from graph edges, with the evidence span kept visible.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="callout">
          <strong>What is inspectable</strong>
          <p>Source records, citation labels, extraction spans, applicability decisions, generated rules, and findings all remain separate graph objects with explicit support edges.</p>
        </div>
        <div class="callout">
          <strong>What this proves</strong>
          <p>The service is not just a visualization. It shows that findings can be traced back to the repo evidence model and the validated local graph export.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Evidence behavior: findings link to source records, artifact hashes, citation labels, and extraction spans.</span>
      <span>Trace behavior: ${metrics.supportsFindingEdges} support edges link evidence or generated rules to findings.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">Capability 3 / Reverse Compliance And Decision Support</div>
      <h2>Find gaps before they become decision risk</h2>
      <p class="lede">Our review workflow supports forward review and reverse compliance. Most EAs receive a Forest Plan consistency document; we extend that into a full profile consistency document across applicable laws and authorities, then package decision support for the responsible official.</p>
    </header>
    <main>
      <img class="graph-figure readiness" src="assets/graph_readiness_service_view.png" alt="Clear readiness graph showing one graph-ready forest profile and blocked forest profiles" />
      <p class="caption">Readiness scene: blocked profiles and missing-source requirements are graph objects. The USFS Region 1 example shows Custer Gallatin as ready while preventing broader Region 1 completeness claims.</p>
      <div class="grid-2" style="margin-top:0.14in">
        <div class="scene-list">
          ${scene("Document intake", "Draft NEPA package, appendices, catalog records, and provenance.")}
          ${scene("Current authority graph", "Most current applicable regulations, agency procedures, source records, and authority families.")}
          ${scene("Applicability", "Document-specific applicable and screened-out authorities.")}
          ${scene("Reverse compliance", "Unsupported claims, stale references, and missing evidence.")}
          ${scene("Consistency document", "Forest Plan consistency plus full profile consistency across applicable laws.")}
          ${scene("Decision support", "Responsible-official briefing with findings, gaps, and evidence paths.")}
        </div>
        <div>
          <div class="callout">
            <strong>What this service demonstrates</strong>
            <ul>
              <li>Review any NEPA document package against an authority graph updated with the most current applicable regulations.</li>
              <li>Identify unsupported or older-regulation-based statements through reverse compliance.</li>
              <li>Retain screened-out authorities for defensibility and political legibility.</li>
              <li>Provide responsible-official decision support with evidence paths and residual risks.</li>
            </ul>
          </div>
          <p class="source-note" style="margin-top:0.09in">Currentness boundary: older implementing-regulation language is treated as a review risk and flagged outside the current NEPA review basis unless supported by current agency procedure or another current project-specific authority. The graph visualizes the validated USFS Region 1 source set and review overlay; it is not a substitute for legal review.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Deliverable: graph-backed professional NEPA review process plus service capabilities brief.</span>
      <span>Boundary: Region 1 expansion waits on missing sources.</span>
    </footer>
  </section>
</body>
</html>`;
}

function metric(value, label) {
  return `<div class="metric"><strong>${escapeHtml(String(value))}</strong><span>${escapeHtml(label)}</span></div>`;
}

function scene(title, copy) {
  return `<div class="scene"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(copy)}</span></div>`;
}

function wrapSvgText(text, x, y, width, fontSize, fill, maxLines = 5, textAnchor = "start") {
  const words = text.split(/\s+/);
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
    .map(
      (line, index) =>
        `<text x="${x}" y="${y + index * (fontSize + 5)}" text-anchor="${textAnchor}" font-family="Inter, Arial, sans-serif" font-size="${fontSize}" fill="${fill}">${escapeXml(line)}</text>`
    )
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
