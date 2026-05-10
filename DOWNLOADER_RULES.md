# USFS Region 1 EA Source Downloader Rules

These rules define the accuracy, traceability, validation, and operational guardrails for the source-library downloader.

## 1. Input Contract

- The workbook is the source-of-truth input.
- Default ingest tabs are `Ingest_Checklist` and `R1_Forest_Plans`.
- `Scope_Exclusions` is a hard blocklist. A blocked URL must not be downloaded unless an explicit override is recorded.
- Do not treat `Audit_Trail`, `Legend`, `EA_Record_Checklist`, or `Project_AddOns` as default download targets. They may contribute metadata or optional follow-up sources only when explicitly enabled.
- Read URLs from the workbook cells, not by regex over text exports.
- Compute and record the workbook SHA256 before each run.
- Region 1 forest-plan support-document expansion may be loaded only through the explicit
  supplemental register option
  `--r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv`.
  The loader emits only `source_delta_required` rows. `catalog_confirmed` rows remain de-duplicated
  against the workbook/catalog contract, and `official_source_gap_documented` rows are reported as
  skipped gaps, not corpus-ready download targets.

## 2. Row Identity And Provenance

- Every workbook data row must receive a stable source record.
- Preserve workbook provenance for every record:
  - workbook path
  - workbook SHA256
  - sheet name
  - Excel row number
  - source ID or unit name
  - source title
  - original URL
  - scope
  - layer
  - issuer
  - document type
  - applies-to text
  - trigger text
  - review-engine checks
  - currentness or notes
- Do not collapse workbook rows just because they share a URL. Many workbook rows may map to one downloaded artifact.

## 3. URL Rules

- Store the original URL exactly as read, after trimming surrounding whitespace.
- Use a separate normalized URL only for deduplication.
- Normalization may lowercase scheme and host and remove fragments, but must not rewrite path or query semantics.
- Follow redirects, but record the full redirect chain.
- Store both `original_url` and `final_url`.
- Do not silently repair broken URLs. Any manually corrected URL must be recorded as `override_url` with a reason.
- URL overrides must be unique by `source_record_id`, must use absolute HTTP(S) URLs with hosts, and
  must not target a URL listed in `Scope_Exclusions`.
- Overridden rows must preserve both the workbook URL and effective URL, plus `metadata.override_url`
  and `metadata.override_reason`.
- Reject final URLs that resolve to known challenge, block, or not-found pages, even when the HTTP status is `200`.

## 4. Blocked, Excluded, And Failed URLs

- A URL found in `Scope_Exclusions` must be marked `skipped_excluded`.
- Known challenge pages must be marked `challenge_page`, not `downloaded`.
- Use explicit status values:
  - `planned`
  - `downloaded`
  - `duplicate_url`
  - `duplicate_content`
  - `skipped_excluded`
  - `blocked`
  - `challenge_page`
  - `not_found`
  - `timeout`
  - `rate_limited`
  - `ssl_error`
  - `invalid_content`
  - `unsupported_content_type`
  - `failed`
  - `needs_review`
- Capture failure evidence:
  - error class
  - error message
  - HTTP status
  - final URL
  - attempt count
  - timestamp
  - host
- Retry only transient failures: timeouts, `429`, selected `5xx`, and connection resets.
- Do not retry permanent failures indefinitely: `404`, blocked exclusions, unsupported schemes, known not-found pages.

## 5. Download Safety

- Use a clear user agent identifying the local downloader.
- If a public source blocks the project user agent but allows normal browser access, require an
  explicit host-level browser-compatible user-agent setting and record that fact in validation
  metadata.
- Set connect and read timeouts on every request.
- Apply per-host rate limits.
- Apply bounded concurrency. Global concurrency and per-host concurrency must be configurable.
- Honor `Retry-After` when present.
- Support resume by default. Existing validated artifacts must not be fetched again unless `--force` is passed.
- Support `--dry-run` with no network writes.
- Support `--limit`, `--sheet`, `--id`, and `--host` filters for controlled testing.
- Support `--source-delta-only` with an explicit Region 1 forest-plan register when planning,
  preflighting, downloading, batching, or cataloging only supplemental `R1PLAN-*` source-delta rows.
- Support repeated `catalog-build --batch-run-id` values for explicit merged catalog gates. Merged
  catalog gates must use `--catalog-dir` when they are archived evidence and must not silently
  replace the canonical `source_library/catalog/` view.
- Do not disable TLS verification by default. If a site requires a certificate exception, record the exception and mark the record `needs_review` unless a project-level allowlist is approved.

## 6. Artifact Storage

- Save raw downloaded bytes before any extraction or transformation.
- Raw artifacts are immutable. If content changes on a later run, write a new artifact version instead of overwriting.
- Use deterministic, filesystem-safe paths.
- Include a short hash or stable source ID in filenames to avoid collisions.
- Keep extracted text, parsed metadata, screenshots, or derived files separate from raw artifacts.
- Recommended layout:

```text
source_library/
  artifacts/
    raw/
    extracted/
  manifests/
  runs/
    <run_id>/
      events.jsonl
      summary.json
      validation_report.json
      failures.csv
```

## 7. SHA256 Hashing

- Compute SHA256 for the input workbook.
- Compute SHA256 for every raw artifact.
- Compute SHA256 on bytes exactly as saved.
- Store artifact byte size and SHA256 in the manifest.
- If two URLs produce the same SHA256, mark a content duplicate and link both source rows to the same canonical artifact.
- If one URL produces a different SHA256 on a later run, record a new version and flag `content_changed`.

## 8. Manifest Rules

- The manifest is the durable state of the run.
- Write row-level manifest records as JSONL.
- Each row-level record must include:
  - run ID
  - source record ID
  - workbook provenance fields
  - original URL
  - normalized URL
  - final URL
  - redirect chain
  - status
  - artifact path
  - artifact SHA256
  - artifact byte size
  - content type
  - fetch timestamp
  - validation result
  - duplicate linkage
  - failure evidence, when applicable
- The manifest must be append-safe or atomically replaced after a successful run.
- Never mark a row `downloaded` unless bytes are saved, SHA256 is computed, and validation passes.

## 9. Logging Rules

- Logs must be structured JSONL.
- Every event must include:
  - run ID
  - timestamp
  - event type
  - source record ID when applicable
  - URL when applicable
  - host when applicable
- Log these events:
  - run started
  - workbook parsed
  - exclusion applied
  - duplicate detected
  - fetch attempt started
  - redirect observed
  - response received
  - artifact written
  - hash computed
  - validation passed
  - validation failed
  - retry scheduled
  - record finalized
  - run completed
- Logs are event history. The manifest is final state. Do not use logs as the only source of truth.

## 10. Validation Rules

- Validate at three levels.
- Fetch validation:
  - HTTP status is acceptable.
  - Final URL is not a known block, challenge, or not-found URL.
  - Body is non-empty.
  - Content type is expected or explicitly allowed.
- Content validation:
  - PDFs must start with or parse as PDF.
  - HTML must not be a login page, challenge page, generic error page, or `docnotfound` page.
  - Saved content must be large enough to plausibly contain the source.
- Workbook consistency validation:
  - Every ingest row receives exactly one final status.
  - Every downloaded row links to an artifact.
  - Every artifact links back to at least one workbook row.
  - Excluded URLs are not downloaded.
  - Duplicate URLs and duplicate hashes are reported.
- Treat `200 OK` as necessary but not sufficient.

## 11. Host-Specific Rules

- eCFR and Federal Register pages may return challenge/interstitial pages. Detect and reject `unblock.federalregister.gov`.
- For eCFR and Federal Register, prefer official structured export/API endpoints when normal HTML capture is blocked or unstable.
- For `usfs-public.app.box.com` or `usfs-public.box.com` public file links, preserve the official Box share URL in workbook/register rows and let the downloader resolve the temporary BoxCloud file URL at fetch time; do not store expiring access tokens in source rows.
- For `uscode.house.gov`, detect `docnotfound.xhtml` as invalid content.
- For `fs.usda.gov`, preserve final redirected media URLs, especially PDF redirects from `/media/<id>`.
- For state agency pages, expect certificate, redirect, and content-type irregularities. Do not weaken TLS globally to accommodate one host.

## 12. Accuracy Boundaries

- Downloader success proves capture, not legal correctness or currentness.
- Do not infer applicability beyond workbook metadata.
- Do not rewrite, summarize, or normalize legal text during download.
- Preserve retrieval timestamp because many sources are live current-web pages.
- Record currentness notes from the workbook unchanged.

## 13. Review Reports

- Every run must produce a summary report with:
  - workbook SHA256
  - run ID
  - total planned rows
  - total unique URLs
  - downloaded count
  - skipped excluded count
  - duplicate URL count
  - duplicate content count
  - failed count
  - needs-review count
  - top failure hosts
- Every run must produce a failures report suitable for manual review.
- Reports must distinguish row failures from URL failures.

## 14. Acceptance Gates

Before a run is considered complete:

- Workbook parsing count matches expected canonical rows.
- All canonical rows have a final status.
- No `Scope_Exclusions` URL was downloaded.
- Every `downloaded` row has a saved artifact, SHA256, byte size, content type, and validation pass.
- Challenge pages, not-found pages, and zero-byte files are not counted as successful downloads.
- Duplicate references are preserved in the manifest.
- Failures and `needs_review` rows are listed in the run report.
- URL override provenance and `filtered_override_count` match the run manifest.
- The downloader can be rerun without corrupting or overwriting existing validated artifacts.

## 15. Batch Gates

Before batch downloads begin:

- Write a deterministic `batch_plan.json` with source record IDs for every planned batch.
- Write a durable `batch_ledger.json` and update it after every batch state change.
- Run `download`, `report`, and `validate-run` for each batch.
- Stop on the first failed or repair-needed batch unless an operator explicitly chooses to continue.
- Summarize artifact counts and browser-compatible user-agent usage in the batch ledger.
- Consolidate failed and review-needed rows into `repair_queue.csv`.
- Support resume by skipping already passed batches under the same run prefix.

## 16. Reviewer Catalog Gates

Before the source library is used by an EA review engine:

- Build `source_catalog.jsonl` with one record per workbook source row.
- Build `source_set_manifest.json` with workbook, config, override, and git provenance.
- Build `catalog_validation.json`; the catalog command must fail if reviewer catalog validation fails.
- Build `review_sources.sqlite` as the queryable reviewer-engine catalog.
- Preserve stable reviewer citation labels based on `source_record_id` and artifact SHA256 when
  available.
- Classify every row with `document_role`, `authority_level`, expected parser, applicability, and
  review topics.
- Export graph seed nodes and edges for source, authority, applicability, topic, and artifact
  relationships.
- Rebuild the catalog after download batches so artifact hashes, paths, retrieval timestamps, and
  final URLs are linked.

## 17. Captured-Library Integrity Gates

Before the captured library is treated as ready for reviewer-engine ingestion:

- The full parent batch summary must report `all_passed`.
- The parent batch ledger must contain one passed entry for every planned batch.
- The consolidated repair queue must be empty except for the header.
- Child batch manifests must cover every canonical workbook row exactly once.
- Each child manifest's source IDs must match its parent ledger entry.
- Every successful row must have an artifact path, SHA256, byte size, and content type.
- Every artifact path must exist on disk.
- Every artifact SHA256 must recompute from saved bytes.
- Every artifact byte size must match saved bytes.
- Duplicate-content rows must point to an existing canonical artifact.
- Every URL override row must preserve the workbook URL as `original_url`, use the repaired URL as
  `effective_url`, and carry `metadata.override_url` plus `metadata.override_reason`.
- The reviewer catalog must link every workbook row to the corresponding manifest artifact.
- The SQLite index must match `source_catalog.jsonl` for source rows, artifacts, citations, and
  source-artifact links.

These checks are implemented in `tests/test_captured_library.py`.

## 18. Extraction Gates

Before derived text and chunks are treated as ready for reviewer-engine retrieval:

- Run `extract-build` from the reviewer catalog, not by scanning `artifacts/raw/`.
- Verify `catalog_validation.json` has passed unless an operator explicitly permits an invalid
  catalog for diagnostics.
- Recompute each artifact SHA256 before parsing.
- Route each source by `expected_parser`, `content_type`, and file suffix.
- Use the built-in legal XML parser for XML legal sources.
- Use Docling first for PDF extraction with OCR disabled by default for born-digital PDFs, and keep
  a hard child-process timeout so large PDFs do not hang an extraction run.
- If a born-digital PDF exceeds the Docling timeout, fall back to `pypdf_text_fallback` and record
  that parser name/version plus fallback audit metadata in the extraction manifest and chunks.
- Enable OCR explicitly with `--docling-ocr` for scanned PDFs and adjust
  `--docling-timeout-seconds` only with operator intent.
- HTML and DOCX may use built-in parsers or Docling with `--prefer-docling`.
- Write one terminal `extraction_manifest.jsonl` row per selected source.
- Replace only the safe derived directory for the active `source_set_id`; do not leave stale
  chunks or text files from earlier attempts.
- Preserve `source_set_id`, `source_record_id`, artifact SHA256, citation label, URL provenance,
  parser name/version, extraction timestamp, and offsets on every chunk.
- Fail the extraction gate when hashes mismatch, parsers error, selected rows do not extract, chunk
  IDs duplicate, or chunks lack required provenance.

## 19. Retrieval Gates

Before retrieved evidence is used in an EA compliance review:

- Run `retrieval-build` from `chunks/chunks.jsonl` and `review_sources.sqlite`, not from raw
  filenames.
- Require `extraction_validation.json` to pass unless an operator explicitly permits failed
  extraction output for diagnostics.
- Require full extraction coverage by default. A filtered extraction slice must fail reviewer-ready
  retrieval gates unless `--allow-partial-extraction` is passed for diagnostics, and even then the
  resulting summary must record `reviewer_ready: false`.
- Preserve `source_record_id`, artifact SHA256/path, citation label, URL provenance, parser
  name/version, extraction timestamp, extracted-text offsets, and content hash on every indexed
  chunk.
- Attach catalog review topics to indexed chunks so retrieval can filter by reviewer topic.
- Fail the retrieval gate when chunks are missing, source-set IDs drift, chunk IDs duplicate,
  extracted sources are missing indexed chunks, linked artifact/text paths are missing, content
  hashes mismatch, offsets are invalid, or required provenance is absent.
- Query results must return evidence spans with offsets and citation-bearing provenance. Do not use
  uncited snippets for compliance conclusions.
- Run `retrieval-eval` before treating the index as reviewer-ready. Track pass rate, expected-term
  hit rate, citation coverage rate, unsupported-answer rate, and zero-result rate.

## 20. Document Evidence Graph Gates

Before the graph layer is used by a compliance reviewer:

- Run `evidence-graph-build` from extracted chunks, catalog metadata, and retrieval diagnostics.
- Require catalog validation, extraction validation, and retrieval validation to pass.
- Require a reviewer-ready retrieval index by default. A partial retrieval graph must be explicitly
  diagnostic through `--allow-partial-retrieval`, and must still record `reviewer_ready: false`.
- Require the graph builder to reopen the retrieval SQLite index and prove chunks still match the
  indexed source-set IDs, provenance fields, offsets, text, review topics, and content hashes.
- Preserve source document, raw artifact, extracted text, section, chunk, evidence span, parser, and
  review topic nodes.
- Preserve edges from evidence spans back to source documents, artifacts, chunks, parser versions,
  citation labels, content hashes, and offsets.
- Fail the graph gate when retrieval binding fails, chunk hashes do not match text, node IDs or edge
  IDs duplicate, edges dangle, chunks lack evidence spans, chunks lack artifact traces, chunks lack
  review-topic edges, or graph health metrics fail.
- Run `phase-eval` before compliance execution so catalog, extraction, retrieval, evidence graph,
  claim extraction, rule-claim binding, optional coverage, optional gold eval, and optional review
  readiness are reported separately.

## 21. Source Claim Gates

Before source claims are used by compliance findings:

- Run `claim-extract` from extracted chunks, catalog topics, and the reviewer-ready retrieval index.
- Preserve claim IDs, claim type, source text, entity links, authority links, citation labels, chunk
  IDs, artifact hashes, content hashes, and exact source-text offsets.
- Fail the claim gate when source offsets drift, content hashes mismatch, chunk IDs are missing,
  claim evidence spans are unbound, retrieval-index bindings drift, or claim graph edges dangle.
- Run `claim-eval` before treating claim artifacts as reviewer-ready. Eval filters must be known and
  non-empty so typoed filters cannot silently broaden scoring.

## 22. Rule-Claim Binding Gates

Before rule-pack findings rely on source authorities:

- Run `rule-claim-link` from reviewer-ready claim artifacts and the versioned compliance rule pack.
- Require safe rule-pack IDs and rule IDs.
- Preserve deterministic rule-to-claim links with claim type, score, matched terms, citation label,
  chunk ID, artifact hash, and exact source offsets.
- Record explicit no-claim gaps when a rule has no validated source-claim support.
- Run `rule-claim-eval` and require current link artifacts to validate before scoring eval cases.

## 23. Compliance Review Gates

Before compliance findings are treated as reviewer-ready:

- Run `compliance-review` through the same package extraction and source retrieval gates as
  `ea-review`.
- Require rule-pack validation, rule-claim binding readiness, every rule evaluated, source
  citations for claim-bearing findings, and finding graph node/edge integrity.
- A `pass` finding must have package evidence and source-library evidence.
- A `gap` finding must have source-library evidence and must explicitly mean matching package
  evidence was not found.
- Claim-bearing findings must link to validated source claims and citation-bearing source evidence.
- Run `compliance-review-eval` against deterministic package fixtures before promotion.

## 24. Compliance Coverage and Gold Eval Gates

Before a rule pack is promoted beyond seed checks:

- Run `compliance-coverage` so every rule has coverage-matrix support, current source-claim links,
  source-claim term support, source-record agreement, and compliance-review eval coverage.
- Run `compliance-gold-eval` so adjudicated positive, mixed, and negative package profiles pass
  through the real compliance-review eval path.
- Gold eval cases must have unique safe IDs, complete top-level and per-case adjudication metadata,
  positive/mixed/negative profile coverage, complete rule-pack expectations, and matching status
  counts.
- Gold `package_path` fixtures must be relative child paths under the gold file directory; absolute,
  parent-traversal, and resolved path escapes must fail closed.
- Missing package fixture files must be recorded in `compliance_gold_eval_results.json` as failed
  results instead of escaping without a machine-readable artifact.

## 25. Current Boundary

The source library stores raw artifacts and source-level metadata. The extraction layer builds
rebuildable derived text and chunks under `source_library/derived/<source_set_id>/`, the retrieval
layer builds a local evidence index from those chunks, and the evidence graph layer builds a
document/chunk/evidence graph. The current system also stores deterministic source-claim graph
artifacts, rule-claim bindings, EA package review outputs, compliance finding graphs,
compliance-review eval outputs, compliance coverage results, and compliance-gold-eval promotion
artifacts. The system does not yet store embeddings, broad real-package adjudication coverage, or
model-generated compliance synthesis trusted beyond deterministic evidence and eval gates.
