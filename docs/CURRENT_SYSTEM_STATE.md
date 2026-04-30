# Current System State

This project is a local source-library builder for USDA Forest Service Region 1 Environmental Assessment review sources.

The workbook `usfs_region1_ea_document_checklist_current_2026.xlsx` remains the source-of-truth input. The generated `source_library/` is the audited local capture of those workbook sources for downstream EA review-engine ingestion.

## Current Capture

The current full-library capture is:

- Parent batch run: `full-library-batches`
- Canonical workbook rows: `147`
- Batch count: `28`
- Passed batches: `28`
- Failed batches: `0`
- Repair-needed batches: `0`
- Repair queue: empty except the CSV header
- Unique effective URLs: `144`
- Reviewer catalog source rows: `147`
- Reviewer catalog unique artifacts: `131`
- Reviewer catalog source-artifact links: `147`

The current catalog validation passes. The captured-library integrity test suite also passes against these generated outputs.

## Storage Model

The system stores source material in layers.

### Raw Artifacts

Path:

```text
source_library/artifacts/raw/
```

Raw artifacts are downloaded bytes saved before extraction or transformation. They are grouped by host and named with stable source/title slug information plus a SHA256 prefix. The downloader does not overwrite validated artifacts during normal resume behavior.

Artifact metadata is recorded in manifests and catalog records:

- `artifact_path`
- `artifact_sha256`
- `artifact_byte_size`
- `content_type`
- `fetch_timestamp`
- `final_url`

### Row Manifests

Path:

```text
source_library/manifests/download_<run_id>.jsonl
```

Each manifest is JSONL with one row per workbook source in that run. A row records workbook provenance, original URL, effective URL after overrides, normalized URL, final URL, artifact metadata, status, duplicate links, validation result, and failure evidence when applicable.

For full-batch operation, the parent batch ledger points to many child download manifests.

### Batch Evidence

Path:

```text
source_library/runs/full-library-batches/
```

The parent batch run contains:

- `batch_plan.json`
- `batch_ledger.json`
- `summary.json`
- `operator_report.md`
- `repair_queue.csv`

Each child batch also has its own run directory under `source_library/runs/<child-run-id>/` with its own summary, report, events, failures, and acceptance gate.

### Reviewer Catalog

Path:

```text
source_library/catalog/
```

The catalog contains:

- `source_catalog.jsonl`: one reviewer-facing source record per workbook row
- `source_set_manifest.json`: versioned source-set metadata and counts
- `catalog_validation.json`: reviewer-catalog acceptance gate
- `review_sources.sqlite`: queryable index for the EA review engine
- `source_graph_nodes.jsonl`: portable graph seed nodes
- `source_graph_edges.jsonl`: portable graph seed edges

The reviewer catalog links every workbook row to an artifact, including duplicate-content rows.

## Chunking And Graph Status

The system has not yet chunked document contents.

Current state:

- Raw source documents are captured.
- Source metadata is normalized into JSONL and SQLite.
- Graph seed files exist for source-level relationships.
- No semantic text chunks exist yet.
- No embeddings exist yet.
- No content-level claim graph exists yet.
- No page/section-level citation offsets exist yet.

The current graph is a source metadata graph. It includes relationships such as:

- source to artifact
- source to authority
- source to review topic
- source to applicability

It does not include extracted claims, document sections, paragraphs, tables, pages, or vector chunks.

## Accuracy Guarantees

The current downloader and catalog guarantee capture integrity, not legal interpretation.

Validated guarantees:

- Every canonical workbook source row has one final captured status.
- The full-library batch covers all `147` workbook rows.
- The repair queue is empty after URL repairs.
- Every successful row links to an artifact.
- Every artifact path exists.
- Artifact byte sizes match manifest metadata.
- Artifact SHA256 values recompute from saved bytes.
- Duplicate-content rows link to canonical artifacts.
- URL overrides preserve the workbook `original_url` and record the `effective_url`.
- Override metadata includes `override_url` and `override_reason`.
- The reviewer catalog matches batch manifests.
- SQLite source-artifact links match the JSONL catalog.

Boundaries:

- A successful download means the source bytes were captured and validated.
- It does not prove that the source is legally current beyond the workbook metadata and retrieval evidence.
- It does not prove that a downstream parser extracted all content correctly.
- It does not prove that future web versions will remain unchanged.

## Reviewer Engine Read Path

The EA review engine should not scan `artifacts/raw/` directly as its source of truth. It should read through the catalog.

Recommended read path:

1. Read `source_library/catalog/source_set_manifest.json`.
2. Confirm the intended `source_set_id`, `download_batch_run_id`, source counts, artifact counts, and validation status.
3. Query `source_library/catalog/review_sources.sqlite` or read `source_library/catalog/source_catalog.jsonl`.
4. Select source rows by `document_role`, `authority_level`, `review_topics`, `applies_to`, `host`, or `expected_parser`.
5. For each source row, open `artifact_path`.
6. Recompute SHA256 and byte size before parsing.
7. Parse by `expected_parser` and `content_type`.
8. Emit downstream chunks with immutable provenance fields.

Every downstream text chunk should carry:

- `source_set_id`
- `source_record_id`
- `artifact_sha256`
- `artifact_path`
- `citation_label`
- `original_url`
- `effective_url`
- `final_url`
- parser name and parser version
- extraction timestamp
- page, section, heading, byte, or character offsets when available

The review engine should cite `citation_label` and offset metadata, not raw filenames.

## Next Processing Layer

The next system layer should build a derived extraction/chunk index without modifying raw artifacts.

Recommended derived layout:

```text
source_library/
  derived/
    extracted_text/
    chunks/
    embeddings/
    content_graph/
```

Recommended derived outputs:

- extracted text per artifact
- page-aware PDF extraction where possible
- HTML/XML section extraction
- chunk JSONL with stable chunk IDs
- chunk-level SHA256 or content hash
- parser diagnostics
- extraction validation report
- chunk-to-source and chunk-to-artifact links
- optional content graph for sections, claims, citations, and review findings

Derived data should always be rebuildable from raw artifacts and the reviewer catalog.

## Verification Commands

Run all tests:

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

Run captured-library integrity tests only:

```bash
PYTHONPATH=src python -m unittest tests.test_captured_library
```

Rebuild the full reviewer catalog from the current full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --batch-run-id full-library-batches
```
