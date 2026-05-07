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

const mdPath = path.join(repoRoot, "docs", "EAST_CRAZIES_SOILS_RESOURCE_AREA_SOW.md");
const htmlPath = path.join(repoRoot, "docs", "EAST_CRAZIES_SOILS_RESOURCE_AREA_SOW.html");
const pdfPath = path.join(repoRoot, "docs", "EAST_CRAZIES_SOILS_RESOURCE_AREA_SOW.pdf");
const defaultChromiumExecutable =
  "/Users/chunkstand/Library/Caches/ms-playwright/chromium-1178/chrome-mac/Chromium.app/Contents/MacOS/Chromium";

async function main() {
  const markdown = await fs.readFile(mdPath, "utf8");
  const document = parseMarkdown(markdown);
  const html = renderHtml(document);
  await fs.writeFile(htmlPath, html, "utf8");

  const browser = await launchBrowser();
  try {
    await renderPdf(browser, htmlPath, pdfPath);
  } finally {
    await browser.close();
  }

  const pdf = await PDFDocument.load(await fs.readFile(pdfPath));
  const pageCount = pdf.getPageCount();
  if (pageCount > 10) {
    throw new Error(`Expected readable SOW PDF to be 10 pages or fewer, got ${pageCount}.`);
  }
  console.log(`Wrote ${path.relative(repoRoot, htmlPath)}`);
  console.log(`Wrote ${path.relative(repoRoot, pdfPath)} (${pageCount} pages)`);
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

async function renderPdf(browser, inputHtmlPath, outputPdfPath) {
  const page = await browser.newPage({ viewport: { width: 1320, height: 1700 }, deviceScaleFactor: 1 });
  await page.goto(`file://${inputHtmlPath}`, { waitUntil: "load" });
  await page.pdf({
    path: outputPdfPath,
    format: "Letter",
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: "0.42in", right: "0.42in", bottom: "0.42in", left: "0.42in" }
  });
  await page.close();
}

function parseMarkdown(markdown) {
  const lines = markdown.split(/\r?\n/);
  let index = 0;
  const titleLine = lines[index] || "";
  const title = titleLine.startsWith("# ") ? titleLine.slice(2).trim() : "Soils Scope Of Work";
  if (titleLine.startsWith("# ")) {
    index += 1;
  }
  const metadataLabels = new Set([
    "Date",
    "Audience",
    "Purpose",
    "Example project",
    "Forest",
    "District",
    "Districts",
    "Resource area"
  ]);
  const metadata = [];
  while (index < lines.length) {
    while (lines[index]?.trim() === "") {
      index += 1;
    }
    const line = lines[index] || "";
    const match = line.match(/^([^:]+):\s*(.*)$/);
    if (!match || !metadataLabels.has(match[1].trim())) {
      break;
    }
    const currentMeta = { label: match[1].trim(), value: match[2].trim() };
    index += 1;
    while (index < lines.length) {
      const continuation = lines[index] || "";
      const nextMatch = continuation.match(/^([^:]+):\s*(.*)$/);
      if (
        !continuation.trim() ||
        continuation.startsWith("#") ||
        continuation.startsWith("- ") ||
        continuation.startsWith("## ") ||
        (nextMatch && metadataLabels.has(nextMatch[1].trim()))
      ) {
        break;
      }
      currentMeta.value = `${currentMeta.value} ${continuation.trim()}`.trim();
      index += 1;
    }
    metadata.push(currentMeta);
  }

  const blocks = parseBlocks(lines.slice(index));
  const firstSectionIndex = blocks.findIndex((block) => block.type === "h2");
  const intro = firstSectionIndex === -1 ? blocks : blocks.slice(0, firstSectionIndex);
  const sections = firstSectionIndex === -1 ? [] : groupSections(blocks.slice(firstSectionIndex));
  return { title, metadata, intro, sections };
}

function parseBlocks(lines) {
  const blocks = [];
  let index = 0;
  while (index < lines.length) {
    const raw = lines[index];
    const line = raw.trimEnd();
    if (!line.trim()) {
      index += 1;
      continue;
    }
    if (line.startsWith("## ")) {
      blocks.push({ type: "h2", text: line.slice(3).trim() });
      index += 1;
      continue;
    }
    if (line.startsWith("### ")) {
      blocks.push({ type: "h3", text: line.slice(4).trim() });
      index += 1;
      continue;
    }
    if (line.startsWith("- ")) {
      const items = [];
      while (index < lines.length) {
        const itemLine = lines[index].trimEnd();
        if (!itemLine.startsWith("- ")) {
          break;
        }
        let item = itemLine.slice(2).trim();
        index += 1;
        while (index < lines.length) {
          const continuation = lines[index];
          if (continuation.startsWith("  ") && continuation.trim()) {
            item = `${item} ${continuation.trim()}`.trim();
            index += 1;
            continue;
          }
          break;
        }
        items.push(item);
        while (index < lines.length && !lines[index].trim()) {
          index += 1;
        }
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    const paragraph = [line.trim()];
    index += 1;
    while (index < lines.length) {
      const next = lines[index].trimEnd();
      if (
        !next.trim() ||
        next.startsWith("## ") ||
        next.startsWith("### ") ||
        next.startsWith("- ")
      ) {
        break;
      }
      paragraph.push(next.trim());
      index += 1;
    }
    blocks.push({ type: "p", text: paragraph.join(" ") });
  }
  return blocks;
}

function groupSections(blocks) {
  const sections = [];
  let current = null;
  for (const block of blocks) {
    if (block.type === "h2") {
      current = { title: block.text, blocks: [] };
      sections.push(current);
      continue;
    }
    if (current) {
      current.blocks.push(block);
    }
  }
  return sections;
}

function renderHtml(document) {
  return `<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>${escapeHtml(document.title)}</title>
  <style>${styles()}</style>
</head>
<body>
  <article class="report">
    <header class="cover">
      <div class="kicker">WLG Demonstration Package</div>
      <h1>${escapeHtml(document.title)}</h1>
      <dl class="meta">${document.metadata.map(renderMeta).join("")}</dl>
      <div class="intro">${document.intro.map(renderBlock).join("")}</div>
    </header>
    ${document.sections.map(renderSection).join("")}
  </article>
</body>
</html>`;
}

function renderMeta(item) {
  return `<div><dt>${escapeHtml(item.label)}</dt><dd>${escapeLinks(item.value)}</dd></div>`;
}

function renderSection(section) {
  const slug = section.title.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-").replaceAll(/^-|-$/g, "");
  if (section.title === "Deliverables") {
    return `<section class="section deliverables" id="${slug}">
      <h2>${escapeHtml(section.title)}</h2>
      <div class="deliverable-list">${renderDeliverables(section.blocks)}</div>
    </section>`;
  }
  if (section.title.startsWith("Appendix")) {
    return `<section class="section appendix" id="${slug}">
      <h2>${escapeHtml(section.title)}</h2>
      ${renderAppendix(section.blocks)}
    </section>`;
  }
  const className = section.title === "Sources Cited" ? "section sources" : "section compact";
  return `<section class="${className}" id="${slug}">
    <h2>${escapeHtml(section.title)}</h2>
    <div class="section-body">${section.blocks.map(renderBlock).join("")}</div>
  </section>`;
}

function renderDeliverables(blocks) {
  const deliverables = [];
  let current = null;
  for (const block of blocks) {
    if (block.type === "h3") {
      current = { title: block.text, blocks: [] };
      deliverables.push(current);
      continue;
    }
    if (current) {
      current.blocks.push(block);
    }
  }
  return deliverables
    .map(
      (deliverable) => `<div class="deliverable-item">
        <h3>${escapeHtml(deliverable.title)}</h3>
        ${deliverable.blocks.map(renderBlock).join("")}
      </div>`
    )
    .join("");
}

function renderAppendix(blocks) {
  const lead = [];
  const entries = [];
  let current = null;
  for (const block of blocks) {
    if (block.type === "h3") {
      current = { title: block.text, blocks: [] };
      entries.push(current);
      continue;
    }
    if (current) {
      current.blocks.push(block);
    } else {
      lead.push(block);
    }
  }
  return `<div class="appendix-lead">${lead.map(renderBlock).join("")}</div>
    <div class="appendix-list">
      ${entries
        .map(
          (entry) => `<div class="appendix-entry">
            <h3>${escapeHtml(entry.title)}</h3>
            ${entry.blocks.map(renderAppendixBlock).join("")}
          </div>`
        )
        .join("")}
    </div>`;
}

function renderBlock(block) {
  if (block.type === "p") {
    return `<p>${escapeLinks(block.text)}</p>`;
  }
  if (block.type === "h3") {
    return `<h3>${escapeHtml(block.text)}</h3>`;
  }
  if (block.type === "ul") {
    return `<ul>${block.items.map((item) => `<li>${escapeLinks(item)}</li>`).join("")}</ul>`;
  }
  return "";
}

function renderAppendixBlock(block) {
  if (block.type !== "ul") {
    return renderBlock(block);
  }
  return `<dl class="crosswalk">${block.items.map(renderCrosswalkItem).join("")}</dl>`;
}

function renderCrosswalkItem(item) {
  const match = item.match(/^([^:]+):\s*(.*)$/);
  if (!match) {
    return `<div><dt>Note</dt><dd>${escapeLinks(item)}</dd></div>`;
  }
  return `<div><dt>${escapeHtml(match[1])}</dt><dd>${escapeLinks(match[2])}</dd></div>`;
}

function escapeLinks(value) {
  const escaped = escapeHtml(value);
  return escaped.replaceAll(/(https:\/\/[^\s<]+)/g, '<a href="$1">$1</a>');
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function styles() {
  return `
    @page { size: Letter; margin: 0.46in; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      color: #1d221f;
      background: #fbfaf7;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    .report { max-width: 7.66in; margin: 0 auto; }
    .cover {
      padding: 0 0 0.18in;
      border-bottom: 2px solid #23776e;
      break-inside: avoid;
    }
    .kicker {
      color: #23776e;
      font-size: 8.4pt;
      font-weight: 850;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    h1, h2, h3, p, dl, dd, ul { margin: 0; }
    h1 {
      margin-top: 0.04in;
      font-size: 25pt;
      line-height: 1.05;
      letter-spacing: 0;
      color: #141814;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.09in 0.18in;
      margin-top: 0.16in;
      padding-top: 0.14in;
      border-top: 1px solid #e1ddd2;
    }
    .meta div { min-width: 0; }
    dt {
      color: #667065;
      font-size: 6.9pt;
      line-height: 1.1;
      font-weight: 850;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }
    dd {
      margin-top: 0.025in;
      color: #1d221f;
      font-size: 9.1pt;
      line-height: 1.28;
      font-weight: 650;
    }
    .intro {
      margin-top: 0.18in;
      column-count: 2;
      column-gap: 0.28in;
    }
    p, li {
      color: #414a42;
      font-size: 9.35pt;
      line-height: 1.38;
      text-wrap: pretty;
    }
    p { margin-bottom: 0.08in; }
    .section {
      margin-top: 0.22in;
      padding-top: 0.02in;
      break-inside: auto;
    }
    h2 {
      margin-bottom: 0.11in;
      padding: 0 0 0.045in;
      color: #1b5f58;
      background: transparent;
      border-bottom: 2px solid #23776e;
      border-radius: 0;
      font-size: 13.2pt;
      line-height: 1.08;
      letter-spacing: 0.02em;
      text-transform: uppercase;
    }
    h3 {
      margin: 0.12in 0 0.055in;
      color: #171b17;
      font-size: 10.6pt;
      line-height: 1.22;
      break-after: avoid;
    }
    .section-body {
      max-width: 6.95in;
    }
    .section-body > h3:first-child { margin-top: 0; }
    ul {
      margin: 0 0 0.1in 0.18in;
      padding: 0;
    }
    li { margin-bottom: 0.05in; }
    li::marker { color: #23776e; }
    .deliverable-list {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.18in;
      align-items: start;
    }
    .deliverable-item {
      padding-top: 0.08in;
      border-top: 4px solid #23776e;
      break-inside: avoid;
    }
    .deliverable-item h3 {
      margin-top: 0;
      color: #141814;
      font-size: 10.7pt;
    }
    .deliverable-item ul { margin-bottom: 0; }
    .appendix-lead {
      margin-bottom: 0.12in;
      max-width: 6.6in;
    }
    .appendix-list {
      display: block;
    }
    .appendix-entry {
      padding: 0.09in 0;
      border-top: 1px solid #d8d3c6;
      break-inside: avoid;
    }
    .appendix-entry h3 {
      margin: 0 0 0.05in;
      color: #1b5f58;
      font-size: 10pt;
    }
    .crosswalk {
      display: grid;
      grid-template-columns: 0.95in 1fr;
      gap: 0.035in 0.12in;
      margin: 0;
    }
    .crosswalk div { display: contents; }
    .crosswalk dt {
      color: #52615a;
      font-size: 7.2pt;
      line-height: 1.22;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      font-weight: 850;
    }
    .crosswalk dd {
      color: #3d463f;
      font-size: 8.55pt;
      line-height: 1.32;
      font-weight: 450;
    }
    .sources .section-body {
      max-width: 7in;
    }
    .sources li {
      font-size: 8pt;
      line-height: 1.26;
      overflow-wrap: anywhere;
    }
    a { color: #175e57; text-decoration: none; }
    @media print {
      .cover, .deliverable-item, .appendix-entry { box-shadow: none; }
    }
  `;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
