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
  if (pageCount > 8) {
    throw new Error(`Expected compact SOW PDF to be 8 pages or fewer, got ${pageCount}.`);
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
      <div class="cards">${renderH3Cards(section.blocks)}</div>
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

function renderH3Cards(blocks) {
  const cards = [];
  let current = null;
  for (const block of blocks) {
    if (block.type === "h3") {
      current = { title: block.text, blocks: [] };
      cards.push(current);
      continue;
    }
    if (current) {
      current.blocks.push(block);
    }
  }
  return cards
    .map(
      (card) => `<div class="card">
        <h3>${escapeHtml(card.title)}</h3>
        ${card.blocks.map(renderBlock).join("")}
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
    <div class="appendix-grid">
      ${entries
        .map(
          (entry) => `<div class="appendix-card">
            <h3>${escapeHtml(entry.title)}</h3>
            ${entry.blocks.map(renderBlock).join("")}
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
    @page { size: Letter; margin: 0.42in; }
    * { box-sizing: border-box; }
    html, body { margin: 0; padding: 0; }
    body {
      color: #1d221f;
      background: #f7f6f1;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      -webkit-font-smoothing: antialiased;
    }
    .report { max-width: 7.66in; margin: 0 auto; }
    .cover {
      padding: 0.2in 0.22in 0.18in;
      background: #ffffff;
      border: 1px solid #d7d2c5;
      border-left: 7px solid #23776e;
      border-radius: 10px;
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
      font-size: 22pt;
      line-height: 1.05;
      letter-spacing: 0;
      color: #141814;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.07in 0.12in;
      margin-top: 0.13in;
      padding-top: 0.12in;
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
      font-size: 8.5pt;
      line-height: 1.22;
      font-weight: 650;
    }
    .intro {
      margin-top: 0.14in;
      column-count: 2;
      column-gap: 0.22in;
    }
    p, li {
      color: #414a42;
      font-size: 8.45pt;
      line-height: 1.25;
      text-wrap: pretty;
    }
    p { margin-bottom: 0.055in; }
    .section {
      margin-top: 0.15in;
      padding-top: 0.03in;
      break-inside: auto;
    }
    h2 {
      margin-bottom: 0.08in;
      padding: 0.055in 0.08in;
      color: #ffffff;
      background: #23776e;
      border-radius: 5px;
      font-size: 11.2pt;
      line-height: 1.08;
      letter-spacing: 0.015em;
      text-transform: uppercase;
    }
    h3 {
      margin: 0.06in 0 0.04in;
      color: #171b17;
      font-size: 9.1pt;
      line-height: 1.18;
      break-after: avoid;
    }
    .section-body {
      column-count: 2;
      column-gap: 0.24in;
    }
    .section-body > h3:first-child { margin-top: 0; }
    ul {
      margin: 0 0 0.07in 0.13in;
      padding: 0;
    }
    li { margin-bottom: 0.028in; }
    li::marker { color: #23776e; }
    .cards {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 0.08in;
    }
    .card, .appendix-card {
      padding: 0.1in 0.11in;
      background: #ffffff;
      border: 1px solid #d9d5ca;
      border-left: 4px solid #23776e;
      border-radius: 7px;
      break-inside: avoid;
    }
    .card h3, .appendix-card h3 {
      margin-top: 0;
      color: #141814;
      font-size: 9.4pt;
    }
    .card ul { margin-bottom: 0; }
    .appendix-lead {
      margin-bottom: 0.08in;
      max-width: 6.6in;
    }
    .appendix-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.075in;
    }
    .appendix-card p,
    .appendix-card li {
      font-size: 7.72pt;
      line-height: 1.2;
    }
    .appendix-card ul { margin-bottom: 0; }
    .sources .section-body {
      column-count: 2;
      column-gap: 0.2in;
    }
    .sources li {
      font-size: 7.7pt;
      line-height: 1.18;
      overflow-wrap: anywhere;
    }
    a { color: #175e57; text-decoration: none; }
    @media print {
      .cover, .card, .appendix-card { box-shadow: none; }
    }
  `;
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
