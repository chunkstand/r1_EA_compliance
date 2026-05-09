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

async function main() {
  await fs.mkdir(assetDir, { recursive: true });
  const browser = await launchBrowser();
  try {
    await writeAssets();
    await fs.writeFile(briefHtmlPath, briefHtml(), "utf8");
    await renderPdf(browser, briefHtmlPath, briefPdfPath);
    const pdf = await PDFDocument.load(await fs.readFile(briefPdfPath));
    if (pdf.getPageCount() !== 2) {
      throw new Error(`Expected a 2-page PDF, got ${pdf.getPageCount()} pages.`);
    }
    console.log(`Wrote ${path.relative(repoRoot, briefHtmlPath)}`);
    console.log(`Wrote ${path.relative(repoRoot, briefPdfPath)}`);
    console.log("Verified 2 PDF pages.");
  } finally {
    await browser.close();
  }
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

async function writeAssets() {
  const assets = [
    ["project_sow_system_capabilities_view", systemCapabilitiesSvg()]
  ];
  await fs.writeFile(path.join(assetDir, "project_sow_delivery_stack.svg"), deliveryStackSvg(), "utf8");
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

function briefHtml() {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Project Scope of Work Capabilities Brief</title>
  <style>
    @page { size: Letter; margin: 0; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: #171713;
      background: #f7f6f1;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      -webkit-font-smoothing: antialiased;
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
      text-wrap: balance;
    }
    h2 {
      font-size: 19pt;
      line-height: 1.05;
      letter-spacing: 0;
      text-wrap: balance;
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
      text-wrap: pretty;
    }
    .lede {
      margin-top: 0.12in;
      max-width: 7.05in;
      color: #30342f;
      font-size: 11.8pt;
      line-height: 1.32;
    }
    .proof-note {
      margin-top: 0.12in;
      color: #26786f;
      font-size: 9.2pt;
      font-weight: 800;
      letter-spacing: 0;
    }
    .purpose {
      display: grid;
      grid-template-columns: 1.05in 1fr;
      gap: 0.14in;
      align-items: center;
      margin-top: 0.13in;
      padding: 0.12in 0.14in;
      background: #eef6f3;
      border: 1px solid #b8d6cf;
      border-left: 6px solid #26786f;
      border-radius: 8px;
    }
    .purpose strong {
      display: block;
      color: #171713;
      font-size: 11.4pt;
      line-height: 1.1;
    }
    .purpose span {
      display: block;
      color: #3f4842;
      font-size: 8.8pt;
      line-height: 1.32;
      font-weight: 700;
      text-wrap: pretty;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.16in;
      align-items: start;
    }
    .fact-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.09in;
      margin-top: 0.16in;
    }
    .fact {
      min-height: 1.04in;
      padding: 0.12in;
      background: #ffffff;
      border: 1px solid #d8d3c6;
      border-left: 5px solid #26786f;
      border-radius: 8px;
    }
    .fact strong {
      display: block;
      font-size: 10.2pt;
      line-height: 1.15;
      color: #171713;
    }
    .fact span {
      display: block;
      margin-top: 0.06in;
      font-size: 8.2pt;
      line-height: 1.26;
      color: #5f625b;
      font-weight: 700;
      text-wrap: pretty;
    }
    .hero-img {
      width: 100%;
      border: 1px solid #d8d3c6;
      border-radius: 10px;
      background: #ffffff;
    }
    .graph-figure {
      display: block;
      width: 100%;
      height: auto;
      border: 1px solid #d8d3c6;
      border-radius: 10px;
      background: #fff;
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
    .capability-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.08in;
      margin-top: 0.14in;
    }
    .capability {
      min-height: 1.16in;
      padding: 0.12in;
      border-radius: 7px;
      border: 1px solid #d8d3c6;
      background: rgba(255,255,255,0.88);
    }
    .capability strong {
      display: block;
      font-size: 10pt;
      margin-bottom: 0.05in;
    }
    .capability span {
      display: block;
      color: #5f625b;
      font-size: 8.2pt;
      line-height: 1.32;
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
  </style>
</head>
<body>
  <section class="page">
    <header>
      <div class="kicker">Standing Framework / Capabilities Brief</div>
      <h1>NEPA Scope of Work System</h1>
      <p class="lede">This system turns a structured proposed-action intake into a contract-ready scope of work package. It explains why resource workstreams are selected, renders the work needed from each resource area, and carries reviewer decisions forward without converting planning support into compliance conclusions.</p>
      <div class="purpose">
        <strong>Purpose</strong>
        <span>Scope of work development is a common project bottleneck. Agency staff may inflate resource-area requirements beyond what laws, regulations, and project facts require. This system identifies only the required work and excludes preference-driven additions.</span>
      </div>
      <p class="proof-note">Overall system facts</p>
      <div class="fact-grid">
        <div class="fact"><strong>Structured intake</strong><span>Captures proposed action, project profile, resource indicators, evidence references, and review assumptions as data.</span></div>
        <div class="fact"><strong>Traceable selection</strong><span>Shows why resource workstreams were selected and where reviewer confirmation is still needed.</span></div>
        <div class="fact"><strong>Contract package</strong><span>Outputs tasks, data needs, deliverables, acceptance criteria, roles, timing, and signoff fields.</span></div>
        <div class="fact"><strong>Planning boundary</strong><span>Keeps scope planning separate from compliance determinations, legal conclusions, and future EA artifacts.</span></div>
      </div>
    </header>
    <main>
      <img class="hero-img" src="assets/project_sow_delivery_stack.svg" alt="Project scope of work delivery process from intake to EA package handoff" />
      <div class="grid-2" style="margin-top:0.15in">
        <div class="callout">
          <strong>What the model produces</strong>
          <p>Resource-specific work records that distinguish tasks, data needs, deliverables, assumptions, dependencies, acceptance criteria, reviewer roles, timing, and signoff.</p>
        </div>
        <div class="callout">
          <strong>What reviewers control</strong>
          <p>Unresolved selections, optional deliverables, and handoff readiness remain visible as adjudication items before the accepted package moves into EA assembly planning.</p>
        </div>
      </div>
    </main>
    <footer class="footer">
      <span>Generated from current scope of work system design artifacts.</span>
      <span>Canonical package data remains JSON; PDF and Markdown are rendered views.</span>
    </footer>
  </section>

  <section class="page">
    <header>
      <div class="kicker">System Design / Core Capabilities</div>
      <h2>Traceable planning package before EA assembly</h2>
      <p class="lede">The design keeps three things explicit: the evidence path from proposed action to selected resource scope, the contract fields needed to order specialist work, and the reviewer gate that decides what is ready to hand off.</p>
    </header>
    <main>
      <img class="graph-figure" src="assets/project_sow_system_capabilities_view.png" alt="System capability view for intake, work package rendering, operational gate, and handoff" />
      <div class="capability-grid">
        <div class="capability"><strong>Evidence graph</strong><span>Preserves the chain from proposed action to action element, evidence reference, resource area, and selected resource scope.</span></div>
        <div class="capability"><strong>Package renderer</strong><span>Keeps work tasks, deliverables, assumptions, dependencies, acceptance checks, timing, and signoff fields explicit.</span></div>
        <div class="capability"><strong>Operational gate</strong><span>Validates the package path before handoff and routes unresolved choices through reviewer adjudication.</span></div>
      </div>
    </main>
    <footer class="footer">
      <span>System purpose: prepare a defensible, inspectable scope of work package.</span>
      <span>Boundary: the package scopes future work; it does not assert that future EA artifacts already exist.</span>
    </footer>
  </section>
</body>
</html>`;
}

function deliveryStackSvg() {
  const steps = [
    "Proposed action",
    "Intake graph",
    "Work package",
    "Adjudication",
    "EA handoff"
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
        <text x="${x + 18}" y="166" class="step-title">${escapeHtml(step)}</text>`;
    })
    .join("");
  return svgShell(
    1120,
    420,
    `<text x="70" y="52" class="eyebrow">Scope of work delivery stack</text>
     ${stepCards}
     <rect x="70" y="282" width="980" height="68" rx="18" fill="#eef6f3" stroke="#b8d6cf" stroke-width="2"/>
     <text x="96" y="323" class="title">Planning boundary</text>
     <text x="365" y="311" class="muted">Scope selection and contract fields stay separate</text>
     <text x="365" y="335" class="muted">from compliance and legal conclusions.</text>`
  );
}

function systemCapabilitiesSvg() {
  const columns = [
    {
      x: 72,
      title: "Structured intake",
      lines: ["Proposed-action facts enter", "the system as inspectable data."],
      items: ["Project profile", "Action elements", "Evidence references", "Resource indicators"]
    },
    {
      x: 407,
      title: "Work package",
      lines: ["Selected resource scopes become", "contract-ready planning records."],
      items: ["Tasks and data needs", "Required deliverables", "Assumptions", "Acceptance and signoff"]
    },
    {
      x: 742,
      title: "Gate and handoff",
      lines: ["Review decisions are resolved", "before EA assembly planning."],
      items: ["Validate intake", "Render package", "Adjudicate choices", "EA assembly checklist"]
    }
  ];
  const columnMarkup = columns
    .map((column, index) => {
      const itemMarkup = column.items
        .map((item, itemIndex) => {
          const y = 244 + itemIndex * 58;
          return `<rect x="${column.x + 24}" y="${y}" width="258" height="40" rx="12" fill="#f7f6f1" stroke="#d8d3c6" stroke-width="2"/>
            <circle cx="${column.x + 48}" cy="${y + 20}" r="7" fill="#26786f"/>
            <text x="${column.x + 66}" y="${y + 25}" class="muted">${escapeHtml(item)}</text>`;
        })
        .join("");
      const arrow =
        index < columns.length - 1
          ? `<path d="M${column.x + 304} 302 C${column.x + 314} 302 ${column.x + 324} 302 ${column.x + 332} 302" stroke="#26786f" stroke-width="5" stroke-linecap="round"/>
             <path d="M${column.x + 332} 302 l-12 -9 v18 z" fill="#26786f"/>`
          : "";
      const arrowMarkup = arrow ? `\n        ${arrow}` : "";
      return `<rect x="${column.x}" y="82" width="306" height="414" rx="20" fill="#ffffff" stroke="#d8d3c6" stroke-width="2"/>
        <rect x="${column.x}" y="82" width="306" height="14" rx="7" fill="#26786f"/>
        <text x="${column.x + 24}" y="138" class="cap-title">${escapeHtml(column.title)}</text>
        <text x="${column.x + 24}" y="174" class="cap-copy">${escapeHtml(column.lines[0])}</text>
        <text x="${column.x + 24}" y="198" class="cap-copy">${escapeHtml(column.lines[1])}</text>
        ${itemMarkup}${arrowMarkup}`;
    })
    .join("");
  return svgShell(
    1120,
    620,
    `<text x="70" y="50" class="eyebrow">System capability view</text>
     ${columnMarkup}
     <rect x="72" y="530" width="976" height="48" rx="16" fill="#eef6f3" stroke="#b8d6cf" stroke-width="2"/>
     <text x="96" y="560" class="muted">The same canonical package supports inspection, review, and downstream planning without changing the source of truth.</text>`
  );
}

function svgShell(width, height, content) {
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <style>
    .eyebrow { font: 800 20px Inter, Arial, sans-serif; fill: #26786f; letter-spacing: 1.5px; text-transform: uppercase; }
    .title { font: 800 22px Inter, Arial, sans-serif; fill: #171713; }
    .step-title { font: 800 20px Inter, Arial, sans-serif; fill: #171713; }
    .cap-title { font: 850 24px Inter, Arial, sans-serif; fill: #171713; }
    .cap-copy { font: 700 16px Inter, Arial, sans-serif; fill: #5f625b; }
    .scope-title { font: 800 16px Inter, Arial, sans-serif; fill: #171713; }
    .muted { font: 700 15px Inter, Arial, sans-serif; fill: #5f625b; }
    .tiny { font: 700 12px Inter, Arial, sans-serif; fill: #5f625b; }
    .small-label { font: 800 14px Inter, Arial, sans-serif; fill: #26786f; letter-spacing: 1px; text-transform: uppercase; }
  </style>
  <rect width="${width}" height="${height}" fill="#ffffff"/>
  <rect x="24" y="24" width="${width - 48}" height="${height - 48}" rx="24" fill="#f7f6f1" stroke="#d8d3c6" stroke-width="2"/>
  <g>${content}</g>
</svg>`;
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
