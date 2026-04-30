# System Output Schemas

The system writes durable, auditable outputs under `source_library/`. This file covers downloader,
batch, catalog, EA review, extraction, retrieval, evidence graph, source claim graph, and phase-eval
artifacts.

## Row Manifest JSONL

Path: `source_library/manifests/dry_run_<run_id>.jsonl`

One JSON object per workbook data row.

Required fields:

- `run_id`
- `source_record_id`
- `workbook_path`
- `workbook_sha256`
- `sheet`
- `excel_row`
- `source_id`
- `title`
- `original_url`
- `effective_url`
- `normalized_url`
- `final_url`
- `redirect_chain`
- `status`
- `artifact_path`
- `artifact_sha256`
- `artifact_byte_size`
- `content_type`
- `fetch_timestamp`
- `validation`
- `duplicate_of`
- `failure`
- `metadata`

For dry runs, network-derived fields are `null` or empty, and `status` is one of `planned`, `duplicate_url`, or `skipped_excluded`.

`original_url` is always the workbook cell value. `effective_url` is the URL actually used for planning/fetching after applying `config/url_overrides.toml`. When no override exists, both values are the same.
Override records must also carry `metadata.override_url` and `metadata.override_reason` so repairs remain traceable.

For preflight runs, the manifest path is `source_library/manifests/preflight_<run_id>.jsonl`.
Preflight records use the same row-level schema and add:

- `http_status`
- `content_length`
- `fetch_method`
- `attempt_count`

Preflight `status` values include:

- `preflight_ok`
- `duplicate_url`
- `skipped_excluded`
- `blocked`
- `challenge_page`
- `not_found`
- `timeout`
- `rate_limited`
- `ssl_error`
- `unsupported_content_type`
- `failed`

For download runs, the manifest path is `source_library/manifests/download_<run_id>.jsonl`.
Download records use the same row-level schema and add:

- `planned_artifact_path`
- `content_length`
- `http_status`
- `attempt_count`

Download `status` values include:

- `downloaded`
- `downloaded_existing`
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

## Run Summary JSON

Path: `source_library/runs/<run_id>/summary.json`

Required fields:

- `run_id`
- `started_at`
- `completed_at`
- `mode`
- `workbook_path`
- `workbook_sha256`
- `canonical_rows`
- `unique_canonical_urls`
- `excluded_url_count`
- `override_count`
- `filtered_override_count`
- `planned_count`
- `duplicate_url_count`
- `skipped_excluded_count`
- `downloaded_count`
- `failed_count`
- `needs_review_count`
- `status_counts`
- `top_hosts`
- `manifest_path`

Preflight summaries also include:

- `checked_url_count`
- `preflight_ok_count`

Download summaries also include:

- `checked_url_count`
- `downloaded_count`
- `downloaded_existing_count`
- `duplicate_content_count`

## Validation Report JSON

Path: `source_library/runs/<run_id>/validation_report.json`

Required fields:

- `run_id`
- `mode`
- `checks`
- `passed`

Each check includes:

- `name`
- `passed`
- `expected`
- `actual`
- `details`

## Event Log JSONL

Path: `source_library/runs/<run_id>/events.jsonl`

One JSON object per event.

Required fields:

- `run_id`
- `timestamp`
- `event_type`
- `source_record_id`
- `url`
- `host`
- `details`

## Failures CSV

Path: `source_library/runs/<run_id>/failures.csv`

Headers:

- `source_record_id`
- `sheet`
- `excel_row`
- `source_id`
- `title`
- `original_url`
- `status`
- `error_class`
- `error_message`
- `attempt_count`

## Operator Report

Path: `source_library/runs/<run_id>/operator_report.md`

The report command reads a run summary and manifest, then writes a Markdown operator view with:

- status counts
- host counts
- adapter counts
- failed rows requiring manual review
- suggested next action per failed row

## Acceptance Gate

Path: `source_library/runs/<run_id>/acceptance_gate.json`

The `validate-run` command writes:

- `run_id`
- `mode`
- `passed`
- `checks`
- `summary`

Checks cover:

- all rows have final status
- excluded rows have no artifact or fetch evidence
- failed rows appear in the repair queue
- successful artifacts exist and match SHA256/byte-size metadata
- duplicate-content rows link to a canonical artifact
- URL provenance is traceable for workbook URLs and override URLs
- summary counts match manifest records

## Host Pilot Summary

Path: `source_library/runs/<run-id-prefix>-host-pilots/summary.json`

The `pilot-hosts` command writes:

- `run_id`
- `run_id_prefix`
- `hosts_requested`
- `host_count`
- `ready_host_count`
- `blocked_host_count`
- `all_ready`
- `host_results`

Each host result includes:

- `host`
- `run_id`
- row and status counts
- `filtered_override_count`
- `gate_passed`
- `ready_for_full_download`
- manifest, report, and acceptance-gate paths

## Batch Download Outputs

Path: `source_library/runs/<run-id-prefix>-batches/`

The `batch-download` command writes:

- `batch_plan.json`
- `batch_ledger.json`
- `summary.json`
- `operator_report.md`
- `repair_queue.csv`

`batch_plan.json` includes:

- `run_id`
- `run_id_prefix`
- `batch_size`
- `limit_per_host`
- `hosts_requested`
- `batch_count`
- `planned_row_count`
- `batches`

Each planned batch includes:

- `batch_id`
- `host`
- `sequence`
- `host_sequence`
- `row_count`
- `source_record_ids`
- `workbook_rows`

`batch_ledger.json` tracks every batch with:

- `status`
- row and status counts
- `artifact_count`
- `browser_compatible_user_agent_count`
- `gate_passed`
- `manifest_path`
- `report_path`
- `acceptance_gate_path`
- `error`

Batch statuses are:

- `planned`
- `running`
- `passed`
- `needs_repair`
- `failed`

`repair_queue.csv` consolidates failed or review-needed rows across executed batches.

## Reviewer Catalog Outputs

Path: `source_library/catalog/`

The `catalog-build` command writes:

- `source_catalog.jsonl`
- `source_set_manifest.json`
- `catalog_validation.json`
- `review_sources.sqlite`
- `source_graph_nodes.jsonl`
- `source_graph_edges.jsonl`

`source_catalog.jsonl` contains one reviewer-facing record per workbook source row, including:

- workbook row identity and source provenance
- `document_role`
- `authority_level`
- issuer, scope, layer, document type, applicability, and currentness fields
- original, effective, normalized, and final URLs
- expected parser strategy
- source status
- artifact SHA256/path/byte size/content type when linked to a download run
- review topics
- citation label

`source_set_manifest.json` versions the source set with:

- workbook SHA256
- config SHA256
- override registry SHA256
- git commit
- optional download run ID
- optional parent batch-download run ID
- source, artifact, URL, authority, topic, host, role, parser, and status counts

`catalog_validation.json` is the reviewer-engine gate. Checks cover:

- unique source record IDs
- required reviewer fields
- valid artifact path, byte size, and SHA256 metadata for successful downloads
- review graph links, including role, authority level, and review topics
- duplicate or unknown rows in linked download manifests
- parent batch-download completion, child manifest availability, and ledger-to-manifest row matching when `--batch-run-id` is used

`review_sources.sqlite` exposes graph-ready review tables:

- `source_sets`
- `sources`
- `artifacts`
- `source_artifacts`
- `authorities`
- `source_authorities`
- `applicability`
- `review_topics`
- `source_review_topics`
- `citations`

The graph JSONL files provide portable seed nodes and edges for a later GraphRAG import.

## EA Review Outputs

Path: `source_library/reviews/<review_id>/`

The `ea-review` command writes:

- `package/package_manifest.jsonl`
- `package/package_chunks.jsonl`
- `package/extracted_text/<source_record_id>_<artifact_sha256_prefix>.txt`
- `package/docling_json/<source_record_id>_<artifact_sha256_prefix>.json` when Docling produced
  document JSON
- `review_validation.json`
- `review_report.json`
- `review_report.md`

`ea-review` reads:

- a local EA package file or directory passed with `--package-path`
- the source-library retrieval index, normally
  `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`
- a checklist JSON file, defaulting to `config/ea_review_checklist_seed.json`

Supported package file suffixes are `.pdf`, `.html`, `.htm`, `.xml`, `.docx`, `.txt`, and `.md`.
Package files are extracted through the same parser layer used for source-library extraction.
The command requires the source-library retrieval index's adjacent `summary.json` and
`retrieval_validation.json` to exist, match the requested source set, pass validation, and report
`reviewer_ready: true`. When a fixed review ID is reused, prior package extraction artifacts and
reports are replaced before the new review is written.

`package_manifest.jsonl` contains one row per supported package file:

- local package source record ID
- artifact path, SHA256, byte size, and content type
- parser name/version and parser metadata
- extracted text path, text SHA256, text character count, and chunk count
- terminal status and failure object when parsing did not succeed

`package_chunks.jsonl` contains package-local chunks with parser provenance, character offsets,
page/section/heading when available, content hashes, and text.

`review_report.json` has schema version `ea-review-v0` and includes:

- summary paths and counts
- package extraction counts and parser counts
- finding status counts
- unsupported finding IDs
- `reviewer_ready`, true only when package extraction succeeded and all non-not-applicable findings
  have source-library evidence
- findings
- validation

Each finding includes:

- checklist item ID, title, question, severity, status, confidence, and rationale
- status: `pass`, `gap`, `uncertain`, or `not_applicable`
- package query, searched package terms, and package evidence status
- source-library query, source filters, and source-library evidence status
- top package evidence and source-library evidence spans when found
- full top result lists for audit
- limitations

A `gap` is allowed to have no package evidence span because the missing package evidence is the
finding. It must still have source-library evidence. An `uncertain` finding does not make a
compliance claim.

`review_validation.json` records gate-facing checks for:

- source retrieval index readiness
- all package files extracted
- package chunks exist
- finding statuses are valid
- `pass` findings have both package and source-library evidence
- `gap` findings have source-library evidence
- no unsupported compliance claims are emitted

## Compliance Review Outputs

Path: `source_library/reviews/<review_id>/`

The `compliance-review` command writes the base EA review outputs plus:

- `compliance_validation.json`
- `compliance_review.json`
- `finding_graph_nodes.jsonl`
- `finding_graph_edges.jsonl`

`compliance-review` reads:

- a local EA package file or directory passed with `--package-path`
- a versioned compliance rule pack, defaulting to
  `config/compliance_rule_pack_nepa_ea_v0.json`
- the source-library retrieval index, normally
  `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`

The rule pack has schema version `compliance-rule-pack-v0` and includes:

- `rule_pack_id`
- `version`
- `title`
- optional description, domain, and jurisdiction
- `rules`

`rule_pack_id`, `version`, and each rule `id` must contain only letters, numbers, dots,
underscores, or hyphens. Fixed review IDs passed to `ea-review`, `compliance-review`, or
`phase-eval --review-id` use the same safe segment rule.

Each rule includes:

- stable `id`
- `title`
- `question`
- `requirement`
- `severity`
- `package_query`
- `package_terms`
- `source_query`
- `source_filters`
- optional `evidence_expectation`

Supported `source_filters` keys are:

- `document_role`
- `authority_level`
- `source_record_id`
- `review_topic`
- `topic`
- `citation`
- `host`

Unknown filter keys and empty filter values fail rule-pack validation so typoed filters cannot
silently broaden retrieval.

`compliance_review.json` has schema version `compliance-review-v0` and includes:

- summary paths and counts
- rule-pack ID and version
- rule count, finding count, claim-bearing finding count, and finding status counts
- unsupported finding IDs
- validation
- compliance findings

Each compliance finding includes:

- rule-pack ID and version
- rule ID, title, question, requirement, and severity
- status: `pass`, `gap`, `uncertain`, or `not_applicable`
- claim type: `supported_compliance_finding`, `package_evidence_gap`, or `no_compliance_claim`
- package query, package terms, source query, and source filters
- package and source-library evidence statuses
- package and source-library citation labels when present
- top package and source-library evidence results
- limitations

`finding_graph_nodes.jsonl` contains:

- `ComplianceRulePack`
- `ComplianceReview`
- `ComplianceRule`
- `ComplianceFinding`
- `SourceLibraryEvidence`
- `PackageEvidence`
- `PackageEvidenceGap`

`finding_graph_edges.jsonl` relationships include:

- `RULE_PACK_USED_BY_REVIEW`
- `RULE_PACK_HAS_RULE`
- `REVIEW_EVALUATED_RULE`
- `RULE_PRODUCED_FINDING`
- `FINDING_SUPPORTED_BY_SOURCE_EVIDENCE`
- `FINDING_SUPPORTED_BY_PACKAGE_EVIDENCE`
- `FINDING_HAS_PACKAGE_GAP`

`compliance_validation.json` records gate-facing checks for:

- rule-pack validity
- base EA review validation
- every rule evaluated
- valid finding statuses
- `pass` findings have both package and source-library evidence
- `gap` findings have source-library evidence
- claim-bearing findings have source-library citation labels
- no unsupported compliance claims are emitted
- finding graph evidence edges match each finding claim type
- finding graph node/edge integrity
- finding graph rule and finding coverage

## Derived Extraction Outputs

Path: `source_library/derived/<source_set_id>/`

The `extract-build` command writes:

- `extracted_text/<source_record_id>_<artifact_sha256_prefix>.txt`
- `docling_json/<artifact_sha256_prefix>.json` when Docling produced document JSON
- `chunks/chunks.jsonl`
- `diagnostics/extraction_manifest.jsonl`
- `diagnostics/extraction_validation.json`
- `diagnostics/extraction_accuracy_audit.json` when `extraction-accuracy-audit` is run
- `diagnostics/summary.json`

The command replaces the derived directory for the selected `source_set_id` on each run so stale
text or chunk files cannot survive from a previous extraction attempt. The `source_set_id` is
validated as a safe path segment before the derived directory is deleted.

`extract-build` reads `source_library/catalog/review_sources.sqlite`; it does not scan
`source_library/artifacts/raw/` as its authority source. For each selected catalog row it:

- verifies the catalog validation gate unless `--allow-invalid-catalog` is passed
- opens the linked `artifact_path`
- recomputes the artifact SHA256 before parsing
- routes by `expected_parser`, `content_type`, and file suffix
- uses a built-in legal XML parser for XML sources
- scopes eCFR XML section and subpart records to the matching source XML element when the source
  URL includes `/section-...` or `/subpart-...`
- uses built-in HTML and DOCX parsers unless `--prefer-docling` is passed
- uses Docling first for PDF parsing
- disables Docling OCR by default for born-digital PDFs; `--docling-ocr` enables OCR explicitly
- isolates Docling conversion in a child process and applies a hard per-document timeout;
  `--docling-timeout-seconds 0` disables the hard timeout
- falls back to `pypdf_text_fallback` for born-digital PDFs when Docling exceeds the timeout, and
  records that parser name/version in the manifest and chunks

`extraction_manifest.jsonl` contains one terminal row per selected source:

- `source_set_id`
- `source_record_id`
- title, role, authority, host, expected parser, and source status
- artifact path, SHA256, byte size, and content type
- citation label and URL provenance
- extraction timestamp
- terminal extraction `status`
- parser name and version when parsing succeeded
- parser metadata when fallback extraction or source-scoped XML extraction is used
- extracted text path, Docling JSON path, text SHA256, text character count, and chunk count
- failure object when parsing did not succeed

Terminal extraction statuses are:

- `extracted`
- `no_artifact`
- `artifact_missing`
- `hash_mismatch`
- `parser_error`
- `parser_timeout`
- `empty_text`

`chunks/chunks.jsonl` contains retrieval-ready text chunks with:

- stable `chunk_id`
- `source_set_id`
- `source_record_id`
- `artifact_sha256`
- `artifact_path`
- `citation_label`
- original, effective, and final URLs
- parser name and version
- extraction timestamp
- character offsets in extracted text
- page, section, and heading when the parser can infer them
- chunk `content_sha256`
- chunk `text`

`extraction_validation.json` is the extraction gate. Checks cover:

- every selected catalog row has a terminal extraction status
- every selected row extracted successfully
- extracted records have non-empty text and chunks
- artifact hashes still match the reviewer catalog
- parser errors are absent
- parser timeouts are absent
- fallback parser records include audit metadata
- scoped XML records include source-scope metadata
- chunk IDs are unique
- chunks have required provenance

`extraction-accuracy-audit` writes `diagnostics/extraction_accuracy_audit.json`. It is a stricter
accuracy-oriented gate for generated extraction artifacts and checks:

- `extraction_validation.json` passed
- extracted text files match manifest text hashes and character counts
- raw artifact SHA256 values still match the manifest
- chunk text exactly equals the extracted-text character offset slices
- chunks cover each extracted text without gaps
- scoped eCFR XML records contain the target heading and do not leak sibling headings
- extracted text has no raw markup or common escaped HTML entity leakage
- PDF text has token coverage against independent `pypdf` extraction, with a stricter threshold for
  `pypdf_text_fallback` records

## Evidence Retrieval Outputs

Path: `source_library/derived/<source_set_id>/retrieval/`

The `retrieval-build` command writes:

- `evidence_index.sqlite`
- `retrieval_manifest.json`
- `retrieval_validation.json`
- `summary.json`

`retrieval-build` reads:

- `source_library/derived/<source_set_id>/chunks/chunks.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/extraction_validation.json`
- `source_library/derived/<source_set_id>/diagnostics/extraction_manifest.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/summary.json`
- `source_library/catalog/review_sources.sqlite`

The command validates that extraction passed, extraction scope is complete, chunk IDs are unique,
chunk text hashes still match, chunk offsets are valid, catalog topics are available, linked
artifact/text paths still exist, and each indexed chunk carries retrieval provenance. A filtered
diagnostic index can be built with `--allow-partial-extraction`, but that summary records
`reviewer_ready: false`.

`retrieval_manifest.json` and `summary.json` include:

- source-set ID
- source chunks path
- catalog SQLite path
- extraction validation, manifest, and summary paths
- chunk count and indexed source count
- catalog source count, selected source count, and extracted source count
- extraction filters
- FTS5 availability
- validation status
- `reviewer_ready`, which is true only when the index validates and extraction coverage is complete

`evidence_index.sqlite` contains:

- `metadata`: index schema, source-set ID, source chunk path, catalog path, creation timestamp
- `chunks`: chunk text, reviewer metadata, review topics, citation labels, artifact provenance,
  parser provenance, offsets, and content hashes
- `chunks_fts`: optional SQLite FTS5 table for lexical retrieval support when the local SQLite
  build provides FTS5

`retrieval-query` prints JSON with:

- `query`
- applied reviewer filters
- `hit_count`
- ranked `results`

Each result includes:

- `rank`
- `score`
- `chunk_id`
- `source_record_id`
- `title`
- `document_role`
- `authority_level`
- `citation_label`
- `review_topics`
- `evidence_span`
- `provenance`

The `evidence_span` includes the returned text and both chunk-local and extracted-text character
offsets. `provenance` includes source-set ID, artifact SHA256/path, original/effective/final URLs,
parser name/version, extraction timestamp, source text path, page/section/heading when available,
and chunk content hash.

`retrieval-eval` writes `retrieval_eval_results.json` by default beside the index. It records:

- eval file path
- top-k setting
- query count, passed count, failed count
- pass rate
- source hit rate
- expected-term hit rate
- citation coverage rate
- unsupported-answer rate
- zero-result rate
- per-case query, filters, expectations, failure reasons, missing expected source IDs, missing
  expected terms, top source IDs, and top evidence results

## Source Claim Graph Outputs

Path: `source_library/derived/<source_set_id>/claims/`

The `claim-extract` command writes:

- `claims.jsonl`
- `entities.jsonl`
- `claim_graph_nodes.jsonl`
- `claim_graph_edges.jsonl`
- `claim_graph.sqlite`
- `claim_validation.json`
- `summary.json`

`claim-extract` reads:

- `source_library/derived/<source_set_id>/chunks/chunks.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/extraction_validation.json`
- `source_library/derived/<source_set_id>/diagnostics/summary.json`
- `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`
- `source_library/derived/<source_set_id>/retrieval/retrieval_validation.json`
- `source_library/derived/<source_set_id>/retrieval/summary.json`
- `source_library/catalog/review_sources.sqlite`

`claims.jsonl` contains exact source-text claim spans. Each claim includes:

- stable `claim_id`
- `source_set_id`
- `source_record_id`
- `chunk_id`
- claim type: `obligation`, `prohibition`, `condition`, `authorization`, `definition`,
  `exemption`, or `guidance`
- exact `claim_text`
- citation label, authority level, document role, title, and review topics
- artifact path/SHA256 and URL provenance
- parser name/version
- source text path
- chunk-local and extracted-text character offsets
- claim text hash and source chunk hash
- extractor name/version, pattern ID, confidence, and validation status

`entities.jsonl` contains deterministic entity records extracted from claim text, including legal
citations, section references, acronyms, and named actors. Each entity records its claim IDs, source
record IDs, citation labels, mention count, and extractor version.

Claim graph node types:

- `SourceSet`
- `SourceDocument`
- `DocumentChunk`
- `Claim`
- `ClaimEvidenceSpan`
- `Entity`
- `Authority`
- `ReviewTopic`

Claim graph edge relationships include:

- `SOURCE_SET_HAS_SOURCE`
- `SOURCE_HAS_CHUNK`
- `CHUNK_HAS_CLAIM`
- `CLAIM_HAS_EVIDENCE_SPAN`
- `CLAIM_EVIDENCE_FROM_CHUNK`
- `CLAIM_MENTIONS_ENTITY`
- `CLAIM_HAS_AUTHORITY`
- `SOURCE_HAS_AUTHORITY`
- `CLAIM_SUPPORTS_REVIEW_TOPIC`

`claim_validation.json` checks:

- extraction validation passed
- extraction scope is complete
- retrieval validation passed
- retrieval is reviewer-ready, unless `--allow-partial-retrieval` is used for diagnostics
- retrieval index exists and is readable
- claim/entity/graph JSONL files exist
- claim IDs and entity IDs are unique
- every claim has required provenance
- claim types are supported
- claim source-set IDs match the evaluated source set
- claim chunk IDs resolve to extracted chunks
- claim offsets match chunk text and source text files
- claim text hashes match
- claims match the retrieval index binding for their source chunks
- unsupported claims are not emitted
- entities resolve to claims
- graph nodes and edges are internally consistent
- graph health metrics pass

`summary.json` includes claim count, entity count, graph counts, claim-type counts, authority and
document-role counts, retrieval binding mismatch count, offset mismatch count, graph health metrics,
validation status, and `reviewer_ready`.

`claim-eval` writes `claim_eval_results.json` by default beside the claims file. It records eval
case count, pass rate, source hit rate, claim-type hit rate, expected-term hit rate, citation
coverage rate, zero-result rate, and per-case top claim results with provenance.

## Document Evidence Graph Outputs

Path: `source_library/derived/<source_set_id>/evidence_graph/`

The `evidence-graph-build` command writes:

- `document_graph_nodes.jsonl`
- `document_graph_edges.jsonl`
- `evidence_graph.sqlite`
- `evidence_graph_validation.json`
- `summary.json`

`evidence-graph-build` reads:

- `source_library/derived/<source_set_id>/chunks/chunks.jsonl`
- `source_library/derived/<source_set_id>/diagnostics/extraction_validation.json`
- `source_library/derived/<source_set_id>/diagnostics/summary.json`
- `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`
- `source_library/derived/<source_set_id>/retrieval/retrieval_validation.json`
- `source_library/derived/<source_set_id>/retrieval/summary.json`
- `source_library/catalog/catalog_validation.json`
- `source_library/catalog/review_sources.sqlite`

Graph node types:

- `SourceSet`
- `SourceDocument`
- `RawArtifact`
- `ExtractedText`
- `DocumentSection`
- `DocumentChunk`
- `EvidenceSpan`
- `Parser`
- `ReviewTopic`

Graph edge relationships include:

- `SOURCE_SET_HAS_SOURCE`
- `SOURCE_HAS_ARTIFACT`
- `ARTIFACT_PARSED_TO_TEXT`
- `SOURCE_HAS_SECTION`
- `SECTION_HAS_CHUNK`
- `SOURCE_HAS_CHUNK`
- `CHUNK_DERIVED_FROM_ARTIFACT`
- `CHUNK_HAS_EVIDENCE_SPAN`
- `EVIDENCE_SUPPORTS_SOURCE`
- `EVIDENCE_TRACES_TO_ARTIFACT`
- `SOURCE_SUPPORTS_REVIEW_TOPIC`
- `CHUNK_SUPPORTS_REVIEW_TOPIC`

`evidence_graph_validation.json` checks:

- catalog validation passed
- extraction validation passed
- extraction scope is complete
- retrieval validation passed
- retrieval is reviewer-ready, unless `--allow-partial-retrieval` is used for diagnostics
- retrieval index exists and is readable
- chunk source-set IDs match the requested source set
- chunk `content_sha256` values match chunk text
- chunk IDs, provenance fields, offsets, hashes, text, and review topics match the retrieval index
- evidence span text and hashes match their source chunks
- node IDs and edge IDs are unique
- edges resolve to existing nodes
- every chunk has a graph node, evidence span, artifact trace, and review-topic edge
- graph health metrics pass

`summary.json` includes graph health metrics:

- node count and edge count
- source document, artifact, section, evidence span, and review topic counts
- connected component count
- isolated node count
- dangling edge count
- evidence coverage rate
- chunk topic coverage rate
- source artifact coverage rate
- retrieval index path and indexed chunk count
- retrieval binding mismatch count
- chunk hash mismatch count
- `reviewer_ready`

The `phase-eval` command writes `phase_eval_results.json` in the same directory. It evaluates
catalog capture, extraction, retrieval, evidence graph, and claim extraction as separate phases and
records phase blockers so downstream compliance review cannot hide an upstream failure. When
`--review-id` or `--review-dir` is supplied, it also evaluates a `compliance_review` phase and
requires the review report to exist, validation to pass, the review ID to match when supplied, and
the review source set to match the evaluated source set. The evidence-graph and claim-extraction
phases report failed validation check names, retrieval index path, and retrieval binding mismatch
counts.
