# USFS Region 1 EA Source Downloader Rules

These rules define the accuracy, traceability, validation, and operational guardrails for the source-library downloader.

## 1. Input Contract

- The workbook is the source-of-truth input.
- Default ingest tabs are `Ingest_Checklist` and `R1_Forest_Plans`.
- `Scope_Exclusions` is a hard blocklist. A blocked URL must not be downloaded unless an explicit override is recorded.
- Do not treat `Audit_Trail`, `Legend`, `EA_Record_Checklist`, or `Project_AddOns` as default download targets. They may contribute metadata or optional follow-up sources only when explicitly enabled.
- Read URLs from the workbook cells, not by regex over text exports.
- Compute and record the workbook SHA256 before each run.

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
- Set connect and read timeouts on every request.
- Apply per-host rate limits.
- Apply bounded concurrency. Global concurrency and per-host concurrency must be configurable.
- Honor `Retry-After` when present.
- Support resume by default. Existing validated artifacts must not be fetched again unless `--force` is passed.
- Support `--dry-run` with no network writes.
- Support `--limit`, `--sheet`, `--id`, and `--host` filters for controlled testing.
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
- The downloader can be rerun without corrupting or overwriting existing validated artifacts.

## 15. First Milestone

The first implementation milestone is manifest-only dry run:

- parse workbook
- compute workbook SHA256
- identify canonical rows
- apply exclusions
- normalize URLs
- detect duplicate URLs
- assign planned artifact paths
- write a dry-run manifest and summary
- perform no downloads

No network downloader should be implemented until the dry-run manifest proves the row counts, exclusions, duplicate handling, and planned paths.
