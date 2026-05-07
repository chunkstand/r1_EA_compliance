# System Output Schemas

The system writes durable, auditable outputs under `source_library/`. This file covers downloader,
batch, catalog, EA review, extraction, retrieval, evidence graph, source claim graph,
applicability-first review, and phase-eval artifacts.

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
Package evidence search requires at least one configured package term to match. Single-word package
terms match whole tokens; phrase terms match contiguous text.

`review_validation.json` records gate-facing checks for:

- source retrieval index readiness
- all package files extracted
- package chunks exist
- finding statuses are valid
- `pass` findings have both package and source-library evidence
- `gap` findings have source-library evidence
- no unsupported compliance claims are emitted

## Custer Gallatin Forest Plan Context Outputs

Path: `source_library/reviews/<review_id>/`

The `forest-plan-resolve` command writes:

- `package/package_manifest.jsonl`
- `package/package_chunks.jsonl`
- `package/extracted_text/<source_record_id>_<artifact_sha256_prefix>.txt`
- `forest_plan_context.json`
- `forest_plan_context_validation.json`
- `forest_plan_context_summary.json`
- for packages resolved to the selected forest-plan profile:
  - `forest_plan_component_findings.json`
  - `forest_plan_component_findings.md`
  - `forest_plan_reviewer_resolution_queue.json`
  - `forest_plan_component_inventory_coverage.json`
  - `forest_plan_applicable_standard_coverage.json`

`forest-plan-resolve` reads:

- a local EA package file or directory passed with `--package-path`
- the selected forest-plan profile from `config/forest_plan_profiles.json`, or the path passed with
  `--forest-plan-profiles-path`
- the profile-declared plan source-record IDs
- the source-library retrieval index when the package is resolved to the selected profile

For Custer Gallatin-scoped packages, retrieval readiness is satisfied only when the index contains
all required records declared by the Custer Gallatin profile: the planning page, Land Management
Plan, Record of Decision, FEIS Volume 1, FEIS Volume 2, Biological Assessment, and Biological
Opinion. This allows a Custer Gallatin extraction/retrieval slice to support the first proving case
while still preventing reviews against an incomplete profile-required plan bundle.

When `--reuse-package-cache` is supplied, the review directory must already contain:

- `package/package_manifest.jsonl`
- `package/package_chunks.jsonl`

In that mode the command preserves those package cache files and reruns forest-plan context
resolution without re-extracting the package files.

`forest_plan_context.json` has schema version `forest-plan-context-v0` and includes:

- summary paths and package extraction counts
- `scope_status`: `custer_gallatin`, `not_custer_gallatin`, or `ambiguous`
- forest unit and ranger district signals from the selected profile
- profile source records used by the resolver
- project location signals found in the EA package
- resolved geographic areas
- resolved management areas
- resolved overlays
- `supporting_plan_evidence`: triggered ROD, FEIS, designated-area/allocation, ESA Biological
  Assessment, and Biological Opinion evidence routes
  - each route includes `trigger_terms` and `trigger_evidence` so reviewers can inspect why the
    supporting plan record was applied
- `source_record_readiness`: required profile source-record IDs, indexed chunk counts, and
  missing source IDs
- package evidence snippets
- source-library plan evidence snippets
- unresolved mentions that require reviewer attention
- `needs_reviewer_resolution`
- validation results

The default resolver profile is scoped to the Custer Gallatin National Forest. It does not infer
Custer Gallatin scope from ambiguous `Gallatin`-only mentions. Custer Gallatin packages with no
resolved geographic area, management area, or overlay set `needs_reviewer_resolution` and are not
reviewer-ready. Other configured forest profiles block Custer Gallatin scope only when they appear
as operative project-scope evidence; incidental background, reference, bibliography, or coordination
mentions do not force `ambiguous`. Negative package-location evidence, such as `not part of the
project area`, `there are no <area/overlay> in the parcels`, or `outside of <area/overlay>`, is
filtered before geographic, management-area, or overlay resolution. If an entry has negative
package-location evidence, table-only or incidental mentions are suppressed unless the package also
contains affirmative project-location evidence for that entry.

`forest_plan_context_validation.json` records gate-facing checks for:

- required context fields
- resolved scope status
- Custer Gallatin packages having at least one resolved geographic area, management area, or overlay
- required profile source records being indexed
- plan-context entries carrying package evidence
- plan-context entries carrying source-library plan evidence
- triggered supporting plan-evidence routes carrying trigger evidence and source-library evidence

Supporting plan routes are trigger-gated. Broad EA section labels such as `purpose and need` or
`alternatives` can be captured as package context after a FEIS route is triggered, but they do not
activate FEIS routing by themselves. Uppercase acronym triggers such as `ROD`, `FEIS`, `BA`, `BO`,
and `ESA` require uppercase matches, preventing ordinary lowercase words from activating supporting
plan records.

`forest_plan_context_summary.json` has schema version `forest-plan-context-summary-v0` and includes
the context, validation, and package-cache paths; scope status; resolved area counts; unresolved
mention count; supporting plan-evidence route count; `needs_reviewer_resolution`; retrieval
readiness; and `reviewer_ready`. For packages resolved to the selected forest-plan profile, it also
includes a `component_evaluation` summary with component counts, finding status counts,
standard counts, compliance-status counts, all-applicable-standards coverage, reviewer-resolution
counts, provenance-complete counts, validation status, and component-evaluator reviewer readiness.

## Forest Plan Component Evaluation Outputs

Path: `source_library/reviews/<review_id>/`

For packages resolved to the selected forest-plan profile, `forest-plan-resolve` runs the forest-plan
component evaluator after context resolution. By default, it reads the source-set component inventory
at `source_library/derived/<source_set_id>/forest_plan_components/component_inventory.json` when
present and falls back to `config/forest_plan_component_inventory_seed.json`;
`--forest-plan-component-inventory-path <path>` overrides that inventory path. The evaluator reads a
component inventory with schema version `forest-plan-component-inventory-v0`, filters it to the
selected forest-plan profile, checks that each component belongs to the active source set, binds
plan-source evidence from the inventory's exact source chunk IDs, searches the EA package chunks for
component-specific evidence terms, and writes structured findings plus reviewer-resolution work
items. The resolver still requires retrieval readiness for profile scope, context, and supporting
source-record evidence, but component plan-source citations come from the generated inventory
binding rather than a per-component retrieval query.

The `forest-plan-components-build` command builds the source-set component inventory from extracted
forest-plan chunks and writes:

- `source_library/derived/<source_set_id>/forest_plan_components/component_inventory.json`
- `source_library/derived/<source_set_id>/forest_plan_components/components.jsonl`
- `source_library/derived/<source_set_id>/forest_plan_components/component_inventory_build_coverage.json`
- `source_library/derived/<source_set_id>/forest_plan_components/summary.json`

The builder is deterministic and only consumes chunks whose `source_set_id`, `source_record_id`, and
`document_role=forest_plan` match the requested source. It extracts labeled plan components such as
`Standards (BC-STD-CMBCA) 01 ...`, requires a numeric component number after the label, preserves
source chunk IDs, hashes, citation labels, and provenance, and fails validation if generated
component records are malformed. This avoids treating cross-reference labels such as `Guidelines
(FW-GDL-VEGNF) See ...` or table captions as plan components, stops valid component text before
those malformed labels, and records the suppressed label as an inventory-quality issue.

`component_inventory_build_coverage.json` has schema version
`forest-plan-component-inventory-build-coverage-v0` and records selected chunk count, detected
component labels, detected standard labels, built component counts, missing detected component IDs,
missing detected standard IDs, duplicate component IDs, duplicate standard IDs, validation errors,
inventory-quality issues for component-like labels with nonnumeric number tokens, and pass/fail
checks. Inventory-quality issues are non-blocking warnings unless they are emitted with
`severity=error`; the `blocking_inventory_quality_issues_absent` check keeps build coverage fail
closed if a future inventory-quality rule is promoted to blocking. Source-set generated inventories under
`source_library/derived/<source_set_id>/forest_plan_components/` require passing build coverage
before component evaluation can mark inventory coverage as passed.

The component inventory is data, not runtime branching. The seed inventory at
`config/forest_plan_component_inventory_seed.json` currently covers the East Crazies-relevant Crazy
Mountains Backcountry Area components from the 2022 Custer Gallatin Land Management Plan. Each
component includes:

- `component_id`
- `forest_unit_id`
- `plan_version`
- `source_set_id`
- `source_record_id`
- `component_type`: one of `desired_condition`, `goal`, `guideline`, `monitoring`, `objective`,
  `plan_amendment`, `standard`, or `suitability`
- `section_id`
- `section_heading`
- `page`
- `citation_label`
- `component_text`
- `geographic_area_ids`
- `management_area_ids`
- `overlay_ids`
- `resource_topics`
- `activity_tags`
- `package_evidence_terms`
- `source_chunk_ids`
- `artifact_sha256`
- `content_sha256`
- `provenance` with non-empty `entity`, `activity`, and `agent` objects

`forest_plan_component_findings.json` has schema version `forest-plan-component-findings-v0` and
includes:

- review ID, source set, component inventory path, summary, validation, component records, and
  findings
- one finding per selected component
- finding status: `supported`, `partial`, `gap`, `not_applicable`, or
  `needs_reviewer_resolution`
- compliance status: `complies`, `potential_noncompliance`, `insufficient_evidence`,
  `not_applicable`, `needs_reviewer_resolution`, or `not_evaluated_for_compliance`
- applicability status: `applicable`, `candidate`, `not_applicable`, or
  `needs_reviewer_resolution`
- applicability basis with source-set match status, matched context IDs, component context IDs,
  package query, package evidence terms, normalized component key, and explicit package component
  determination when a plan-consistency row is present
- plan-source evidence from the inventory-backed LMP component source chunk
- EA package evidence from package chunks, annotated with matched component/core terms,
  `review_section`, and `section_binding` metadata
- rationale
- embedded reviewer-resolution items
- W3C PROV-style finding provenance with `entity`, `activity`, and `agent`

The evaluator is fail-closed for source-set drift. If a component inventory points to a different
`source_set_id` than the active review, component findings become `needs_reviewer_resolution`, the
reviewer-resolution queue receives refresh items, and the component validation check
`component_source_sets_match_review_source_set` fails.

Validation embedded in `forest_plan_component_findings.json` records gate-facing checks for:

- component inventory presence
- component source-set alignment with the active review source set
- component provenance completeness
- valid finding and applicability statuses
- valid compliance statuses
- `supported` and `partial` findings having both package evidence and plan-source evidence
- `supported` and `partial` package evidence having matched section bindings, except explicit
  Plan Consistency Table determinations
- `gap` findings having plan-source evidence
- finding provenance completeness
- reviewer-resolution queue coverage for `gap`, `partial`, and `needs_reviewer_resolution`
  findings
- component inventory coverage passing
- applicable standards having package evidence, plan-source evidence, and a resolved compliance
  status before reviewer-ready status can pass

Component package matching is section-aware. The package query combines component text, component
code, package evidence terms, resource topics, activity tags, and non-generic component keywords.
Candidate package evidence is filtered by negative Plan Consistency Table rows, section family
binding, and core-term matches before it can support a finding. Section families currently include
hydrology, wildlife, botany, scenery, sustainability, recreation/access, land exchange, and
minerals. Non-standard components use the `strict_nonstandard_section_family` binding policy: outside
explicit Plan Consistency Table determinations, desired conditions, goals, guidelines, objectives,
and suitability components need a matching package section family plus substantive component-term
evidence before package evidence can support the finding. The section-family label is derived from
the evidence span and section metadata rather than unrelated text elsewhere in the same chunk. Plan
Consistency Table rows are
component-code aware, tolerate spacing variants introduced by extraction, can read rows split across
adjacent chunks from the same package document, can recover duplicated or split component-key cells,
and can bind conservative empty-code or plain-text rows when the row's component text matches the
LMP component text. Affirmative rows are annotated with
`section_binding.explicit_plan_consistency_component_row=true` so they are auditable as deliberate
Plan Consistency Table bindings rather than broad section-family matches.

`forest_plan_reviewer_resolution_queue.json` has schema version
`forest-plan-reviewer-resolution-queue-v0` and includes review ID, source set, item count, and
resolution items. Queue items identify the finding, component, reason, severity, message, source-set
IDs, status fields, and provenance. Missing package evidence, missing current plan evidence, and
component source-set drift are represented as reviewer work rather than hidden passes.

`forest_plan_component_inventory_coverage.json` has schema version
`forest-plan-component-inventory-coverage-v0` and records selected-inventory coverage for the review:
component counts by type, standard component IDs, source-set alignment, source-chunk coverage, and
provenance coverage. This V0 artifact proves the selected inventory is internally usable; it does not
yet prove that a full Forest Plan extraction command captured every standard in the plan.

`forest_plan_applicable_standard_coverage.json` has schema version
`forest-plan-applicable-standard-coverage-v0` and records one row per selected standard component.
Each row includes `component_key`, `ea_review_section`, package component determination details when
available, plan-source citation labels, package-evidence citation labels, evidence counts, status
fields, `standard_applied`, and failure reasons. For applicable standards, reviewer-ready requires
both plan-source evidence and EA package evidence plus a resolved compliance status. Missing package
evidence, missing plan evidence, unresolved standard applicability, or invalid compliance status
makes `all_applicable_standards_applied` false and causes component validation to fail. Every
standard row, including rows determined not applicable, must retain LMP plan-source evidence so
excluded standards remain auditable against the correct source component.

When EA package text contains a plan-consistency row keyed to the LMP component code, a `Yes`
determination is treated as package evidence and a `No` determination marks that standard
`not_applicable`. Determination provenance includes `chunk_window_ids` when the table row was
reconstructed from adjacent package chunks. Context-excluded standards remain outside the
applicable count but retain the LMP component key and plan-source citation so reviewers can verify
which source component was excluded.

`forest_plan_component_findings.md` is a compact human-readable rendering generated from the JSON
findings. The JSON findings and queue remain the stable machine contracts.

### Forest Plan Component Eval

The `forest-plan-component-eval` command reads an existing forest-plan review directory with:

- `forest_plan_component_findings.json`
- `forest_plan_applicable_standard_coverage.json`
- `forest_plan_reviewer_resolution_queue.json`

It writes `forest_plan_component_eval_results.json` by default. The eval contract defaults to
`config/forest_plan_component_eval_seed.json`, has schema version `forest-plan-component-eval-v0`,
and records adjudicated component cases with expected applicability, EA package section, plan-source
citations, package-evidence citations, compliance status, and reviewer-resolution state. Contracts
may also include `coverage_requirements` for minimum case coverage and a hard requirement that every
currently applicable standard in `forest_plan_applicable_standard_coverage.json` has an expected
applicable-standard case.

The result has schema version `forest-plan-component-eval-results-v0` and records:

- review identity: `review_id`, `source_set_id`, `eval_id`, and artifact paths
- pass/fail summary, threshold checks, coverage-requirement checks, case counts, and
  failure-category counts
- metrics for component applicability precision/recall, applicable-standard recall,
  false-applicable component rate, package-section match rate, plan-source citation correctness,
  package-evidence citation correctness, resolved compliance-status rate, compliance-status match
  rate, reviewer-resolution closure rate, and reviewer-resolution state match rate
- per-case actual/expected values for applicability, package section, plan citations, package
  evidence citations, compliance status, reviewer-resolution state, and failure categories

The eval fails closed on missing review artifacts, review/source-set identity drift in any consumed
review artifact, missing expected cases, uncovered applicable standards, unmet minimum component
type/applicability/section-bound case counts, unexpected applicability, package-section mismatch,
exact plan citation mismatch, exact package evidence citation mismatch, unresolved or incorrect
compliance status, reviewer-resolution state mismatch, or unmet metric thresholds.

### Forest Plan Component Adjudication

The `forest-plan-component-adjudication-template` command reads an existing review directory with:

- `forest_plan_component_findings.json`
- `forest_plan_reviewer_resolution_queue.json`

It writes `forest_plan_component_adjudication_template.json` by default, plus a companion
`forest_plan_component_adjudication_template.md` reviewer worklist. The JSON template has schema
version `forest-plan-component-adjudication-v0` and includes:

- review identity: `adjudication_id`, `review_id`, and `source_set_id`
- top-level adjudication metadata fields for method, reviewer, date, and status
- `allowed_dispositions` and `resolved_dispositions`
- one item for each current reviewer-resolution queue item
- current and expected finding/applicability/compliance status values
- queue reason, component type, matched context, component context, evidence counts, component text,
  and package evidence terms
- compact trace references for the component, plan-source evidence, and package evidence when
  available, including source-record IDs, citation labels, artifact/content hashes, chunk IDs,
  pages, and evidence-span offsets/text

The Markdown worklist is a human-readable rendering of the same queue items for review and triage.
The JSON template remains the authoritative contract consumed by the adjudication eval.

Reviewers should copy or rename the template to `forest_plan_component_adjudication.json`, replace
`disposition: pending` with a resolved disposition, and fill `adjudicated_at`, `adjudicated_by`,
`source_type`, and `rationale`. Resolved dispositions are:

- `true_ea_omission`
- `retrieval_miss`
- `package_section_chunking_miss`
- `component_inventory_overreach`
- `applicability_false_positive`
- `evidence_linking_miss`

The `forest-plan-component-adjudication-eval` command reads the completed adjudication file and
writes `forest_plan_component_adjudication_eval.json` by default. The eval result has schema version
`forest-plan-component-adjudication-eval-v0` and records:

- pass/fail summary, completion rate, expectation match rate, disposition counts, adjudication
  outcome counts, and failure category counts
- real EA omission versus system-miss counts/rates; `true_ea_omission` is counted as a real EA
  omission, while retrieval, chunking, inventory, applicability, and evidence-linking dispositions
  are counted as system misses to feed improvement work. Outcome rates are calculated over the
  current reviewer-resolution queue item count.
- checks for review/source-set identity, adjudication coverage of the current queue, completed
  adjudication metadata, required trace references, and status expectation matches
- per-item results with current statuses, expected statuses, disposition, adjudication outcome, and
  failure categories, plus compact current evidence trace references for source audit

The eval fails closed on missing queue items, unexpected adjudications, duplicate items, pending
dispositions, incomplete adjudication metadata, missing trace references, invalid dispositions, or
status expectation mismatches. A `true_ea_omission` can be a completed adjudication; it documents a
real review gap rather than silently marking the component supported.

## Authority Universe Family Inventory Config

Path: `config/authority_universe_families_nepa_ea_v1.json`

The authority-family inventory is a committed configuration artifact, not a generated
`source_library/` artifact. It is the Milestone 1 crosswalk that makes the bounded USFS Region 1 EA
authority universe explicit and now records the Milestone 3 authority-family rule templates that
promote source-currentness-confirmed families into active applicability contracts.

The file has schema version `authority-universe-families-v1` and includes:

- `authority_universe_family_inventory_id`
- `as_of_date`
- workbook identity and baseline source-record IDs
- source-set/catalog paths for the current generated corpus being crosswalked
- rule-pack identity for the current base candidate rule pack
- status definitions for `active`, `source_only`, `candidate`, `out_of_scope`, and `superseded`
- `required_authority_family_coverage`, mapping each required authority requirement group to one or
  more concrete family IDs
- `authority_families`
- `source_record_crosswalk`
- `summary`, including family counts, status counts, mapped rule/source counts, and orphan-rule or
  orphan-source arrays

Each `authority_families` entry includes:

- `family_id`
- `name`
- `status`
- `rationale`
- `source_record_ids`
- `rule_ids`
- `rule_template_ids`, when the family is represented by a Milestone 3 authority-family template
  rather than a base rule-pack rule
- `source_record_mapping`
- `applicability_predicates`
- `package_fact_types`
- `coverage_requirements`
- `source_evidence_requirements`
- `open_inventory_gaps`
- `supersession`, when the family is replaced, reserved, repealed, or otherwise superseded
- `required_authority_requirement_ids`

Each `source_record_mapping` includes:

- `mapping_status`
- `source_set_id`
- `mapped_source_record_ids`
- `catalog_source_record_ids`
- `excluded_source_record_ids`
- `missing_source_record_requirements`

`source_record_crosswalk` contains one row per active workbook source record. Each row includes:

- `source_record_id`
- `sheet`
- `excel_row`
- `scope`
- `primary_family_id`
- `related_family_ids`
- `mapping_status`

The inventory must preserve these closeout invariants:

- every current rule-pack rule maps to exactly one authority family;
- every rule's `authority_source_record_id` is present in that family's source-record mapping;
- every canonical workbook source record maps to a primary family;
- every active family carries either base rule-pack IDs or authority-family rule-template IDs;
- every Milestone 3 authority-family template has source evidence, package fact requirements,
  positive and negative triggers, and coverage metadata;
- every `candidate` family carries explicit missing source-record requirements;
- `candidate` families remain visible as future work instead of being hidden in runtime code;
- superseded/reserved authorities carry replacement/current-source evidence.

## Authority Family Rule Templates Config

Path: `config/authority_family_rule_templates_nepa_ea_v1.json`

The authority-family rule-template config is a committed Milestone 3 builder input. It does not
replace `config/compliance_rule_pack_nepa_ea_v0.json`; it adds conditional, applicability-first
templates for source-currentness-confirmed authority families that were not base compliance
findings. The authority universe builder loads this repo default automatically. Use
`--authority-family-templates-path` to test a replacement template set, or
`--no-authority-family-templates` only for narrow legacy/unit runs.

The file has schema version `authority-family-rule-templates-v1` and includes:

- `template_set_id`
- `version`
- `base_rule_pack_id` and `base_rule_pack_version`
- `authority_inventory_path`
- `source_set_id`
- `templates`

Each template includes:

- `template_id`
- `authority_family_id`
- `rule_id`
- `authority_category`, `authority_document_role`, and `authority_source_record_id`
- `source_record_ids`, `supporting_source_record_ids`, and `excluded_source_record_ids`
- `applicability_mode`
- `question`, `requirement`, `severity`, `package_query`, `package_terms`, and
  `package_fact_types`
- `applies_if_package_terms` or `applies_if_package_term_groups`
- `does_not_apply_if_package_terms`
- `source_query`, `source_filters`, `source_evidence_requirements`, and `evidence_expectation`
- `dependency_contract` and `supersession`

Path: `config/authority_family_rule_template_coverage_nepa_ea_v1.json`

The coverage config has schema version `authority-family-rule-template-coverage-v1` and maps each
template to an authority family, source-record set, package fact types, positive and negative
trigger terms, and the Milestone 4 eval follow-up flag.

## Authority Source Addition Decisions Config

Path: `config/authority_source_addition_decisions_nepa_ea_v1.json`

The source-addition decisions file is a committed Milestone 2 configuration artifact. It documents
source additions, documented non-additions, and not-current source candidates for authority families
whose inventory status is `candidate` or whose source coverage needs explicit currentness review.
It is not a replacement for workbook row identity; when new sources are added, they still must move
through the workbook, downloader, catalog, and validation gates.

The file has schema version `authority-source-addition-decisions-v1` and includes:

- `authority_inventory_id`
- `as_of_date`
- `decisions`
- `summary`

Each decision includes:

- `authority_family_id`
- `family_status_at_decision`
- `decision_status`
- `decision_date`
- `rationale`
- `recommended_source_records`, when a later workbook/source delta is recommended
- `not_current_source_candidates`, when revoked, repealed, superseded, or otherwise not-current
  sources must not satisfy authority coverage
- `next_action`

## Source Partition Contract

Path: `config/source_partition_contract_nepa_3d_v1.json`

The source-partition contract is the committed NEPA 3D Milestone 2A boundary. It defines which
catalog source records can be used as active review authority and which records are visible only as
currentness, supersession, candidate, excluded, failed, or blocker evidence.

The file has schema version `source-partition-contract-v1` and includes:

- `source_partition_contract_id`
- `as_of_date`
- `source_partitions`
- `graph_relationship_rules`
- `reserved_superseded_authority_rules`
- `handbook_chapter_requirements`
- `workbook_source_delta_plan`

Current source partition values are:

- `active_review_corpus`: current source records eligible for extraction, source claims,
  applicability decisions, generated rules, and compliance findings.
- `currentness_supersession_archive`: rescinded, revoked, superseded, reserved, or
  currentness-only records visible only through supersession/currentness graph relationships.
- `candidate_blocked_source`: candidate, blocked, excluded, failed, or unresolved source records
  visible as graph blockers but not active review authority.

Catalog records include:

- `source_partition`
- `source_partition_basis`

The graph relationship rules intentionally keep `currentness_supersession_archive` records limited
to `SUPERSEDED_BY`, `REPLACES_RESERVED_AUTHORITY`, `HAS_CURRENTNESS_STATUS`, and `BLOCKED_BY`
relationships. They cannot derive active rules, source claims, generated rules, or compliance
findings. The `authority-currentness` gate also validates that the committed contract defines the
required partitions, keeps only active review-corpus sources eligible for active review rules,
defines the reserved `36 CFR part 220` archive boundary, and carries the scoped
workbook/source-delta plan. The FSH 1909.15 handbook rule fails validation when the handbook is
represented only as a collapsed source record instead of separate chapter records once active FSH
1909.15 sources are used by EA review.

## Authority Currentness Report

Path:
`source_library/derived/<source_set_id>/authority_currentness/authority_currentness_report.json`

The `authority-currentness` command writes the Milestone 2 source-currentness gate for the
authority-family inventory. It reads:

- `config/authority_universe_families_nepa_ea_v1.json`, or the path passed with
  `--authority-inventory`
- `config/authority_source_addition_decisions_nepa_ea_v1.json`, or the path passed with
  `--source-addition-decisions`
- `config/source_partition_contract_nepa_3d_v1.json`, or the path passed with
  `--source-partition-contract`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`

The report has schema version `authority-currentness-report-v0` and includes:

- `created_at`
- `source_set_id`
- `inputs` with paths and SHA256 hashes for the authority inventory, source-addition decisions,
  source catalog, and source-set manifest
- `source_addition_decisions`
- `source_partition_contract`
- `catalog_source_partitions`
- `family_currentness`
- `source_currentness_records`
- `validation`
- `summary`

Each `source_currentness_records` entry records one authority-family/source-record mapping and
includes:

- `authority_family_id`
- `family_status`
- `source_record_id`
- `source_title`
- `citation_label`
- `url`
- `effective_date`, when a row-level date can be parsed from catalog metadata
- `capture_date`, using row-level capture metadata when available and the source-set manifest
  `created_at` as a fallback
- `supersession_status`
- `source_status`
- `source_partition`
- `source_partition_basis`
- `currentness_status`
- `counts_as_current_authority`
- `authority_family_source_role`
- `eligible_for_active_review_rules_for_family`
- `graph_allowed_relationships_for_family`
- document role, authority level, issuer, scope, currentness notes, and artifact path/hash

`source_status` values `downloaded`, `downloaded_existing`, `duplicate_content`, and
`duplicate_url` are the only statuses allowed to count as current source coverage. `skipped_excluded`
records are reported as excluded and do not count as current authority. Live-web failure or
unverified statuses such as `blocked`, `challenge_page`, `not_found`, `timeout`, `empty_body`, and
`unsupported_content_type` fail validation and cannot count as current authority. Families marked
`superseded` must carry replacement metadata and their records are reported as replacement sources,
not as current controlling authority for the superseded family.

The validation block checks source-set identity, inventory/catalog alignment, candidate-family
source-addition decisions, required currentness fields, successful-status-only current coverage,
excluded-source handling, failed-capture handling, superseded replacement metadata, source
partition presence/validity, non-current source partitioning, reserved/superseded authority
partitioning, source-partition contract structure, FSH 1909.15 chapter boundaries, and inventory
alignment so stale Milestone 2
currentness gap text cannot remain after the gate passes.

## NEPA 3D Knowledge Graph Export

Contract path: `config/nepa_3d_graph_contract_v1.json`

Source-set export paths:

- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph.json`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_nodes.jsonl`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_edges.jsonl`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_summary.json`
- `source_library/derived/<source_set_id>/knowledge_graph/nepa_3d_graph_validation.json`

Review-specific export paths:

- `source_library/reviews/<review_id>/knowledge_graph/nepa_3d_graph.json`
- `source_library/reviews/<review_id>/knowledge_graph/nepa_3d_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/knowledge_graph/nepa_3d_graph_edges.jsonl`
- `source_library/reviews/<review_id>/knowledge_graph/nepa_3d_graph_summary.json`
- `source_library/reviews/<review_id>/knowledge_graph/nepa_3d_graph_validation.json`

The NEPA 3D graph export has schema version `nepa-3d-knowledge-graph-v1`. Milestone 1 defines the
contract, Milestone 3 implements the source-set exporter, Milestone 4 adds the review overlay, and
Milestone 5 adds Region 1 forest-plan readiness blockers. Milestone 7 adds graph failure
categories, phase-eval graph phases, and promotion-suite gates for source-set plus V1 review graph
validation/summary artifacts. The graph is a visualization/export layer over audited artifacts, not
a separate legal knowledge base.

Top-level graph shape:

- `schema_version`
- `graph_id`
- `created_at`
- `export_scope`, with `scope_type` of `source_set` or `review`; review exports must also carry
  `review_id`
- `inputs`, including upstream path and SHA256 values when available
- `lens_metadata`
- `nodes`
- `edges`
- `summary`
- `validation`

Required node types:

- `source_set`
- `review`
- `authority_family`
- `source_record`
- `artifact`
- `chunk`
- `evidence_span`
- `source_claim`
- `rule_template`
- `applicability_decision`
- `generated_rule`
- `compliance_finding`
- `forest_unit`
- `forest_plan`
- `forest_plan_component`
- `readiness_blocker`
- `graph_lens`

Required edge types:

- `CONTAINS_AUTHORITY_FAMILY`
- `HAS_SOURCE_RECORD`
- `HAS_ARTIFACT`
- `HAS_CHUNK`
- `HAS_EVIDENCE_SPAN`
- `SUPPORTS_SOURCE_CLAIM`
- `SUPPORTS_RULE_TEMPLATE`
- `PRODUCES_APPLICABILITY_DECISION`
- `GENERATES_RULE`
- `SUPPORTS_COMPLIANCE_FINDING`
- `SUPERSEDED_BY`
- `REPLACES_RESERVED_AUTHORITY`
- `HAS_CURRENTNESS_STATUS`
- `BLOCKED_BY`
- `APPLIES_TO_REVIEW`
- `NOT_APPLICABLE_TO_REVIEW`
- `NEEDS_ADJUDICATION`
- `ADJUDICATED_BY`
- `BELONGS_TO_FOREST_UNIT`
- `HAS_FOREST_PLAN`
- `HAS_FOREST_COMPONENT`
- `HAS_READINESS_BLOCKER`
- `DISPLAYED_IN_LENS`

Required display states are `active`, `superseded`, `reserved`, `candidate`, `out_of_scope`,
`applicable`, `not_applicable`, `unresolved`, `adjudicated`, and `readiness_blocked`. Required
review-readiness states are `reviewer_ready`, `not_reviewer_ready`, `not_review_specific`,
`source_currentness_only`, `blocked`, and `needs_adjudication`.

Required readiness blocker types are `missing_source`, `stale_artifact`, `superseded_source`,
`retrieval_miss`, `graph_trace_gap`, `search_coverage_gap`, `adjudication_needed`,
`package_fixture_missing`, `forest_profile_not_ready`, and `fsh_chapter_delta_required`.

Validation enforces contract-required provenance for each emitted node type, edge source/target node
types against the contract's declared endpoint rules, required lens metadata fields and lenses, and
known node, edge, and display-status values inside each lens definition.

Node example:

```json
{
  "node_id": "source_record:R1EA-001",
  "node_type": "source_record",
  "label": "7 CFR part 1b",
  "display_status": "active",
  "review_readiness_status": "reviewer_ready",
  "provenance": {
    "source_set_id": "source-set-ba8d0feae79501b8",
    "source_record_id": "R1EA-001",
    "citation_label": "R1EA-001 citation",
    "artifact_sha256": "..."
  },
  "currentness_metadata": {
    "source_partition": "active_review_corpus",
    "source_partition_basis": "successful_status:downloaded",
    "supersession_status": "current_authoritative_source",
    "counts_as_current_authority": true
  },
  "readiness_blockers": []
}
```

Edge example:

```json
{
  "edge_id": "authority_family:usda_nepa_procedures->source_record:R1EA-001:HAS_SOURCE_RECORD",
  "edge_type": "HAS_SOURCE_RECORD",
  "source_node_id": "authority_family:usda_nepa_procedures",
  "target_node_id": "source_record:R1EA-001",
  "display_status": "active",
  "review_readiness_status": "reviewer_ready",
  "provenance": {
    "source_set_id": "source-set-ba8d0feae79501b8",
    "authority_family_id": "usda_nepa_procedures",
    "source_record_id": "R1EA-001"
  },
  "readiness_blockers": []
}
```

Lens metadata example:

```json
{
  "lens_id": "authority_currentness",
  "label": "Authority Currentness",
  "description": "Display active, reserved, superseded, and candidate authority source state.",
  "supported_node_types": ["authority_family", "source_record", "readiness_blocker"],
  "supported_edge_types": ["HAS_SOURCE_RECORD", "REPLACES_RESERVED_AUTHORITY", "BLOCKED_BY"],
  "display_status_values": ["active", "reserved", "readiness_blocked"]
}
```

Summary example:

```json
{
  "node_count": 6,
  "edge_count": 6,
  "node_type_counts": {"source_record": 2},
  "edge_type_counts": {"HAS_SOURCE_RECORD": 2},
  "display_status_counts": {"active": 7, "reserved": 3},
  "review_readiness_status_counts": {"reviewer_ready": 3},
  "authority_category_counts": {"regulation": 2},
  "source_status_counts": {"downloaded": 2},
  "source_partition_counts": {"active_review_corpus": 2},
  "source_currentness_status_counts": {"confirmed_from_catalog": 2},
  "applicability_status_counts": {"applicable": 1},
  "readiness_blocker_counts": {"superseded_source": 2},
  "validation_passed": true,
  "validation_check_count": 1,
  "failed_validation_check_count": 0,
  "failure_category_counts": {}
}
```

Validation example:

```json
{
  "passed": true,
  "checks": [
    {
      "name": "nepa_3d_graph_edges_resolve_to_nodes",
      "passed": true,
      "failure_category": "graph_dangling_edge",
      "expected": [],
      "actual": []
    }
  ],
  "failure_category_counts": {}
}
```

## NEPA 3D Static Viewer

NEPA 3D Milestone 6 adds a checked-in static viewer under `viewer/nepa-3d/`. The viewer is a
projection over the normalized graph export files; it does not write legal conclusions, does not
promote readiness, and does not replace export validation. Its local manifest has schema version
`nepa-3d-viewer-manifest-v1`:

```json
{
  "schema_version": "nepa-3d-viewer-manifest-v1",
  "default_source_set_id": "source-set-ba8d0feae79501b8",
  "default_review_id": null,
  "runtime": {
    "three_runtime_url": "https://unpkg.com/three@0.149.0/build/three.min.js",
    "graph_runtime": "3d-force-graph",
    "graph_runtime_url": "https://unpkg.com/3d-force-graph@1.76.0/dist/3d-force-graph.min.js"
  },
  "datasets": [
    {
      "dataset_id": "source-set-ba8d0feae79501b8",
      "scope": "source_set",
      "source_set_id": "source-set-ba8d0feae79501b8",
      "review_id": null,
      "graph_path": "../../source_library/derived/source-set-ba8d0feae79501b8/knowledge_graph/nepa_3d_graph.json"
    },
    {
      "dataset_id": "v1-cg-ecid-compliance-review",
      "scope": "review_overlay",
      "source_set_id": "source-set-ba8d0feae79501b8",
      "review_id": "v1-cg-ecid-compliance-review",
      "graph_path": "../../source_library/reviews/v1-cg-ecid-compliance-review/knowledge_graph/nepa_3d_graph.json"
    }
  ]
}
```

The viewer expects each dataset target to use the `nepa-3d-knowledge-graph-v1` export contract. It
derives selectors from `lens_metadata`, graph node fields, edge fields, `provenance`,
`currentness_metadata`, `metadata`, and `readiness_blockers`. It also exposes
`window.__NEPA_3D_VIEWER_READY__` in the browser for local smoke checks; that marker reports the
loaded dataset ID, source set, review, selected lens, rendered node and edge counts, canvas count,
and export validation status.

Committed fixtures for the smallest contract slices live under
`tests/fixtures/nepa_3d_graph/`. `minimal_source_set_graph.json` proves source-set currentness and
source partition display. `minimal_review_graph.json` proves review-specific applicability,
generated-rule, compliance-finding, and adjudication-blocker display.

The Milestone 3 source-set builder is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8
```

It reads catalog and derived review surfaces, including source graph seeds, authority currentness,
authority inventory, evidence graph nodes/edges, source claims, rule-claim links, the base rule
pack, authority-family templates, forest-plan profiles, the Region 1 forest-plan readiness matrix,
and forest-plan component inventory. It does not scan raw artifact filenames. The live source-set
export for `source-set-ba8d0feae79501b8` passes `62` validation checks with `1,410` nodes,
`2,564` edges, `35` authority-family nodes, `190` source-record nodes, `63` rule-template nodes,
`191` source-claim nodes, `329` inventory forest-plan component nodes, `10` forest-unit nodes, `10`
forest-plan nodes, `387` total forest-plan component/requirement nodes, and zero failed validation
checks. It reports node, edge, authority-category, source-status, source-partition,
applicability-status, and readiness-blocker count dimensions. It tracks `10` Region 1
forest/grassland profiles while blocking `9` broader profiles from Region 1 completeness claims
until their source, component-inventory, and eval gates are ready.

The Milestone 4 review overlay uses the same command with `--review-id`:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review
```

Review overlays are written to `source_library/reviews/<review_id>/knowledge_graph/`. The overlay
adds `review`, `applicability_decision`, `generated_rule`, `compliance_finding`, and review evidence
span nodes over the source-set graph, then validates that every candidate authority in
`authority_universe_snapshot.json` has a graph node and exactly one decision, non-applicable
decisions carry search coverage or adjudication support, generated rules derive only from validated
applicable decisions, and compliance findings link to generated rules plus evidence spans. The live
V1 review export passes `76` validation checks with `1,916` nodes, `3,442` edges, `373` candidate
authorities/decisions, `33` generated rules/findings, `340` non-applicable authorities, and the
same Region 1 forest-plan readiness blockers.

## Applicability-First Review Outputs

Path: `source_library/reviews/<review_id>/applicability/`

The applicability-first review contract is the post-V1 pre-review gate for legal-authority,
policy-authority, and Forest Plan applicability. Later implementation milestones must determine
applicability before compliance findings are generated. The compliance review must consume a
validated applicability run and generated rule pack; it must not be the first stage that decides
which authorities apply.

The reviewer-ready compliance-review path now consumes the generated rule pack from this
applicability directory. The base authority rule pack remains a candidate-authority template and can
be run only as an explicit non-reviewer-ready diagnostic. Applicability commands determine and
validate authority applicability before review; compliance findings evaluate generated applicable
rules only.

Required artifacts:

- `authority_universe_snapshot.json`
- `package_fact_graph.json`
- `package_applicability_context.json`
- `package_fact_graph_validation.json`
- `applicability_retrieval_trace.jsonl`
- `applicability_graph_trace.jsonl`
- `applicability_retrieval_graph_diagnostics.json`
- `applicability_decisions.jsonl`
- `applicable_authorities.json`
- `non_applicable_authorities.json`
- `search_coverage_certificates.json`
- `applicability_validation.json`
- `applicability_provenance.json`
- `applicability_report.md`
- `generated_rule_pack.json`
- `generated_rule_pack_validation.json`

Optional artifacts used once adjudication is introduced:

- `applicability_adjudication_template.json`
- `applicability_adjudication_worklist.md`
- `applicability_adjudication_eval.json`
- `applicability_adjudication_apply.json`
- `llm_evidence_proposals.jsonl`

All applicability artifacts share these run identity fields when known:

- `applicability_run_id`
- `review_id`
- `source_set_id`
- `authority_universe_sha256`
- `package_fact_graph_sha256`
- `retrieval_trace_sha256`
- `graph_trace_sha256`
- `search_coverage_certificates_sha256`
- `package_manifest_sha256`
- `package_chunks_sha256`
- `catalog_sha256`
- `base_rule_pack_id`
- `base_rule_pack_version`
- `base_rule_pack_sha256`

Hash fields identify upstream inputs and previously generated artifacts. An artifact's own SHA256 is
recorded by downstream artifacts, validation, and `applicability_provenance.json`; it is not
required to embed a self-referential hash over its own final bytes.

The target review sequence is:

```text
EA package + source library + authority universe
  -> package fact graph
  -> per-authority hybrid retrieval
  -> graph expansion and dependency tracing
  -> deterministic applicability decision ledger
  -> applicable_authorities artifact
  -> non_applicable_authorities artifact
  -> search coverage certificates
  -> applicability validation and adjudication gate
  -> generated review rule pack
  -> compliance review
```

`authority_universe_snapshot.json` has schema version `authority-universe-snapshot-v0` and includes:

- `authority_universe_id`
- `authority_universe_version`
- `created_at`
- `review_id`
- `source_set_id`
- `source_set_manifest_sha256`
- `catalog_sha256`
- `base_rule_pack_id`
- `base_rule_pack_version`
- `base_rule_pack_sha256`
- `artifact_paths`
- `summary`
- `validation`
- source-claim artifact hashes when source claims are part of candidate evidence
- rule-claim binding artifact hashes when claim-bearing rules are part of the candidate universe
- forest-plan profile IDs and component inventory IDs used for candidate discovery
- forest-plan component inventory hash when Forest Plan candidates are present
- candidate authority records

Each candidate authority record includes:

- `candidate_authority_id`
- `candidate_authority_type`: `rule_template`, `authority_family_rule_template`, or
  `forest_plan_component`
- rule-template ID when derived from a base rule
- authority-family ID and rule-template metadata when derived from the Milestone 3
  authority-family template config
- source record IDs, citation labels, authority category, authority document role, and currentness
  metadata
- forest-plan profile, component inventory, component ID, and component type when applicable
- source evidence availability, required source-claim link IDs, rule-claim link IDs, or an explicit
  no-claim expectation
- required package fact types, such as action, agency, decision posture, NEPA level, geography,
  management area, overlay, resource topic, package section, and evidence span
- positive trigger groups and negative trigger groups carried as explicit candidate-universe data,
  not hidden runtime branches
- required source evidence, source-role filters, and package-section filters
- deterministic applicability test contract, including package trigger terms, trigger term groups,
  section expectations, negative trigger terms, source filters, and baseline-required rationale
- retrieval contract, including exact keyword, citation, optional vector, metadata-filter, and
  package-section query requirements
- graph expansion contract, including allowed start nodes, relationship types, traversal depth,
  dependency, exception, supersession, Forest Plan profile, geography, overlay, rule-claim, and
  source-record neighbor requirements
- dependency, exception, and supersession contract fields, even when the candidate has no known
  dependencies, exceptions, or superseded authorities
- search coverage requirements for each allowed `not_applicable` decision class

`package_fact_graph.json` has schema version `package-fact-graph-v0` and includes the typed package
facts used before applicability decisions are attempted. It includes:

- `applicability_run_id`, `review_id`, `source_set_id`, `package_manifest_sha256`,
  `package_chunks_sha256`, and `package_fact_graph_sha256`
- package fact graph metadata: `package_fact_graph_id`, `created_at`, extraction method versions,
  source package path, and extraction summary
- `nodes`, where each node has `node_id`, `node_type`, `label`, normalized value fields,
  confidence class, structured `evidence_strength`, extraction method, package chunk IDs, section
  family, citation label, page label, character offsets, text hash, and evidence-span IDs
- `evidence_strength` preserves the compatibility `confidence_class` and adds `strength_class`,
  `reason`, matched phrase/text when available, local evidence window, evidence-window offsets, and
  section family. Strength classes include `observed`, `conditional`, `speculative`, `background`,
  `negative_context`, and legacy `weak_signal`.
- required package fact node types:
  - `action`
  - `agency`
  - `decision_posture`
  - `nepa_level`
  - `geography`
  - `management_area`
  - `overlay`
  - `consultation`
  - `permit`
  - `public_involvement`
  - `alternative`
  - `resource_topic`
  - `package_section`
  - `evidence_span`
- `edges`, where each edge has `edge_id`, `edge_type`, `from_node_id`, `to_node_id`,
  evidence-span IDs, path rationale, and selected/rejected status when the edge was considered for
  applicability
- expected package fact edge types:
  - `describes`
  - `located_in`
  - `intersects_management_area`
  - `has_overlay`
  - `requires_consultation`
  - `mentions_permit`
  - `analyzes_resource_topic`
  - `evaluates_alternative`
  - `supports_fact`
  - `contradicts_fact`
  - `derived_from_section`
- validation fields proving every asserted fact has package evidence spans and hashes

Unsupported inferred facts cannot make an applicability run reviewer-ready. A fact can be proposed
by a later model-assisted evidence layer, but the reviewer-ready graph must bind final facts to
deterministic package spans or human adjudication.

`package_applicability_context.json` has schema version `package-applicability-context-v0` and
includes:

- `review_id`
- `package_path`
- `package_manifest_sha256`
- `package_chunks_sha256`
- `package_fact_graph_sha256`
- `package_context_sha256`
- package section map and section-family bindings
- project type, federal action signals, forest unit, project location signals, geography,
  management areas, overlays, consultations, permits, public-involvement signals, decision posture,
  and supporting-document signals used for applicability
- extracted package facts with chunk IDs, citations, page labels, character offsets, and extraction
  source metadata

`package_fact_graph_validation.json` has schema version `package-fact-graph-validation-v0` and
summarizes the package graph validation result. It includes `review_id`, `source_set_id`,
`package_manifest_sha256`, `package_chunks_sha256`, `package_fact_graph_sha256`,
`package_context_sha256`, validation checks, negative-context location facts, uncertainty records,
and fact-count summaries. Uncertainty records include contradictory package evidence, weakly worded
facts with structured `evidence_strength` details, and missing common fact types that later
applicability stages must handle. It is a Milestone 3 validation artifact only; it does not contain
applicability decisions or compliance findings.

`applicability_retrieval_trace.jsonl` has schema version `applicability-retrieval-trace-v0`; each
line records one query execution or fused result set for one candidate authority. Each trace row
includes:

- `applicability_run_id`, `review_id`, `source_set_id`, `candidate_authority_id`, and
  `retrieval_trace_id`
- `query_plan_id`, query text, query type, query terms, query timestamp, and query source
- allowed query types: `exact_keyword`, `citation`, `bm25`, `vector`, `metadata_filter`,
  `package_section`, `source_role`, `authority_category`, `graph_seed`, and `fused`
- source filters, package-section filters, source-record filters, authority-category filters,
  forest-plan component filters, and currentness filters
- searched index identity, including index path, index type, index build ID, and searched index hash
- ranked results with result ID, result kind, rank, score, fused score, selected/rejected status,
  rejection reason, source record ID, package chunk ID, source chunk ID, claim ID, section family,
  citation label, page label, offsets, matched terms, and text hash
- package-result provenance carries package graph `confidence_class` and `evidence_strength` when
  the retrieval row was seeded by a package fact node
- fusion metadata when multiple searches are combined, including the fusion strategy, input result
  sets, reciprocal-rank-fusion parameters when used, and final rank order

Retrieval traces are evidence-discovery records only. A high retrieval rank, vector score, fused
score, or model-proposed query expansion cannot by itself decide applicability.

`applicability_graph_trace.jsonl` has schema version `applicability-graph-trace-v0`; each line
records an inspected graph path for one candidate authority. Each graph trace row includes:

- `applicability_run_id`, `review_id`, `source_set_id`, `candidate_authority_id`, and
  `graph_path_id`
- graph artifact identity, graph build ID, graph artifact path, and graph artifact hash
- start node ID, end node ID, traversed node IDs, relationship types, traversal depth, and path
  rationale
- selected/rejected status and rejection reason
- evidence references to authority categories, source records, source claims, rule-claim links,
  Forest Plan components, package facts, package chunks, evidence spans, retrieval result IDs, and
  retrieval trace IDs when present

Graph traces are bounded evidence-discovery records only. Graph paths may support a deterministic
predicate or an adjudication item, but graph expansion is not the final legal decision maker.

`applicability_retrieval_graph_diagnostics.json` has schema version
`applicability-trace-diagnostics-v0` and records the Milestone 4 trace-build validation summary,
diagnostics, and trace artifact hashes. Diagnostics include retrieval misses, low-confidence
retrieval, graph dead ends, excessive graph fan-out, and missing local retrieval indexes. It is an
evidence-discovery diagnostic artifact only; it does not contain applicability decisions or
compliance findings.

`applicability_decisions.jsonl` has schema version `applicability-decisions-v0`; each line is one
decision record for one candidate authority. Every candidate in `authority_universe_snapshot.json`
must have exactly one decision record before validation can pass.

Each applicability decision includes:

- `applicability_run_id`
- `decision_id`
- `candidate_authority_id`
- `status`: `applicable`, `not_applicable`, `unresolved`, or `needs_adjudication`
- `basis_type`: `mandatory_baseline`, `positive_package_trigger`, `negative_package_evidence`,
  `absent_trigger_evidence`, `forest_plan_profile_resolution`, `forest_plan_component`,
  `source_set_required`, `unresolved_evidence_conflict`, or `human_adjudication`
- `basis`
- deterministic predicate name, predicate version, predicate input hashes, and predicate result
- source-record IDs, authority category, authority document role, and source-set identity
- package evidence spans with package chunk IDs, citation labels, section families, page labels,
  offsets, matched terms, text snippets, compatibility confidence classes, and structured
  `evidence_strength`
- `arbitration_summary` with schema version `applicability-evidence-arbitration-v0`, recording
  active per-trigger evidence arbitration. The summary includes positive and negative trigger
  group results, matched evidence IDs, package chunk/fact/retrieval refs, evidence strength counts,
  structured evidence-strength class counts, weak-signal reasons/details, source evidence IDs,
  selected retrieval result IDs, graph path IDs, the current decision effect, arbitration status,
  decisive trigger groups, weak auxiliary trigger groups, weak-only trigger groups, missing
  required trigger groups, and whether evidence made adjudication necessary. Weak-signal reasons
  include classifier strength class, reason, and matched phrase when available;
  `weak_signal_details` carries the local evidence window.
- active arbitration fields: `arbitration_status`, `decisive_trigger_groups`,
  `weak_auxiliary_trigger_groups`, `weak_only_trigger_groups`, and `arbitration_rationale`. Strong
  decisive trigger groups can support `applicable` status while weak auxiliary groups remain
  visible; all-weak positives and positive-plus-negative conflicts remain adjudication blockers.
- source-library evidence spans with source record IDs, chunk IDs, citation labels, page labels,
  offsets, source-claim IDs, text snippets, and `evidence_origin` when the span is carried forward
  from the authority universe because source retrieval recorded coverage but selected no source
  chunk
- retrieval trace IDs and selected/rejected retrieval-result IDs that support the decision
- graph path IDs and selected/rejected graph-path IDs when graph evidence supports the decision
- negative evidence spans, explicit trigger-miss evidence, search coverage certificate IDs, or
  human adjudication references when status is `not_applicable`
- Forest Plan component scope-miss decisions record `explicit_trigger_miss_evidence` with
  `missing_package_values`, `missing_trigger_groups`, coverage sufficiency, and executed query
  variants so validation can distinguish supported component non-applicability from a basis gap
- missing evidence, contradiction notes, confidence classification, adjudication state, and reviewer
  notes
- freshness fields: `authority_universe_sha256`, `package_manifest_sha256`,
  `package_chunks_sha256`, `package_fact_graph_sha256`, `retrieval_trace_sha256`,
  `graph_trace_sha256`, `search_coverage_certificates_sha256`, `source_set_id`, and
  `catalog_sha256`

`applicable_authorities.json` has schema version `applicable-authorities-v0` and contains only
decision records whose final status is `applicable`. It includes:

- `applicability_run_id`
- `review_id`
- `source_set_id`
- `authority_universe_sha256`
- `package_manifest_sha256`
- `applicability_decisions_sha256`
- `package_chunks_sha256`
- `package_fact_graph_sha256`
- `retrieval_trace_sha256`
- `graph_trace_sha256`
- `search_coverage_certificates_sha256`
- `catalog_sha256`
- applicable authority count
- one selected-authority record per applicable decision

Each selected-authority record includes:

- `decision_id`
- `candidate_authority_id`
- generated-rule metadata, including source base rule ID when applicable
- evidence-backed applicability basis
- predicate result, retrieval trace IDs, and graph path IDs used for applicability
- source-record IDs, document roles, authority category, source-claim link requirements, package
  section expectations, and Forest Plan component references when relevant

`non_applicable_authorities.json` has schema version `non-applicable-authorities-v0` and contains only
decision records whose final status is `not_applicable`. It includes the same run, source-set,
authority-universe, package, and decision hashes as `applicable_authorities.json`.

Each non-applicable authority record includes:

- `decision_id`
- `candidate_authority_id`
- `non_applicability_basis`
- negative evidence spans, explicit trigger-miss evidence, absent-trigger rationale, and search
  coverage certificate IDs
- human adjudication reference when the final non-applicability decision is adjudicated
- retrieval trace IDs and graph path IDs inspected before exclusion
- source-record IDs, document roles, authority category, and Forest Plan component references when
  relevant

`search_coverage_certificates.json` has schema version `search-coverage-certificates-v0` and records
the replayable negative-proof boundary for not-applicable or unresolved decision classes. It
includes:

- `applicability_run_id`, `review_id`, `source_set_id`, `authority_universe_sha256`,
  `package_fact_graph_sha256`, `retrieval_trace_sha256`, and `graph_trace_sha256`
- one certificate per not-applicable or unresolved decision class, authority category, or explicit
  candidate authority when class-level coverage is not sufficient
- `coverage_certificate_id`, covered candidate authority IDs, covered decision IDs, coverage class,
  required query variants, executed query variants, package sections searched, source indexes
  searched, metadata filters searched, graph neighborhoods searched, searched artifact hashes, and
  source-index hash presence when the authority contract requires hashed source search
- `coverage_result`: `sufficient`, `insufficient`, or `adjudication_required`
- trigger terms searched, negative trigger terms searched, missing trigger groups, rejected
  evidence IDs, and rationale for why the search boundary is sufficient for the authority predicate

A `not_applicable` decision cannot be reviewer-ready unless it cites a sufficient coverage
certificate or a completed human adjudication. Affirmative negative evidence and explicit trigger
misses still require enough search coverage to show the predicate was actually tested.

`applicability_provenance.json` has schema version `applicability-provenance-v0` and records
W3C PROV-style run lineage. It includes:

- entities for the EA package manifest, package chunks, source-set manifest, catalog, authority
  universe, package fact graph, retrieval trace, graph trace, decision ledger, coverage
  certificates, adjudication artifacts, validation artifact, applicable/non-applicable artifacts,
  generated rule pack, and generated rule-pack validation
- activities for package fact extraction, retrieval, graph expansion, deterministic predicate
  evaluation, adjudication replay, validation, and generated-rule-pack production
- agents for deterministic commands, software versions, configured rule packs, and human
  adjudicators when adjudication is present
- relations such as `used`, `wasGeneratedBy`, `wasDerivedFrom`, and `wasAttributedTo`
- artifact paths, SHA256 hashes, command names, configuration hashes, start/end timestamps, and
  replay notes

Provenance proves lineage and replayability; it does not replace evidence spans, search coverage,
deterministic predicates, or adjudication.

`applicability_report.md` is the reviewer-facing rendering of the same machine artifacts. It
includes:

- review ID, applicability run ID, source set, base rule pack, package manifest hash, and authority
  universe hash
- counts for candidate, applicable, non-applicable, unresolved, needs-adjudication, and adjudicated
  authorities
- links to `authority_universe_snapshot.json`, `package_fact_graph.json`,
  `applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`,
  `applicability_decisions.jsonl`, `applicable_authorities.json`,
  `non_applicable_authorities.json`, `search_coverage_certificates.json`,
  `applicability_validation.json`, and `applicability_provenance.json`
- applicable authority summaries with evidence citations and generated-rule metadata
- non-applicable authority summaries with negative evidence, trigger-miss rationale, coverage
  certificate references, or adjudication references
- unresolved or needs-adjudication summaries with missing evidence and contradiction notes
- validation status and failure categories

`applicability_validation.json` has schema version `applicability-validation-v0` and includes:

- `applicability_run_id`
- `review_id`
- `source_set_id`
- `passed`
- `reviewer_ready`
- status counts by applicability decision status
- candidate, applicable, non-applicable, unresolved, and needs-adjudication counts
- hashes for the authority universe, package manifest, package chunks, decisions, applicable
  authorities, non-applicable authorities, package fact graph, retrieval trace, graph trace, search
  coverage certificates, provenance, generated rule pack when present, catalog, source claims,
  rule-claim links, and Forest Plan component inventory when present
- validation failure records with failure category, affected authority IDs, and artifact paths
- generated-rule-pack readiness status

The validation gate also proves that `package_fact_graph_validation.json` passed for the current
package artifacts, human-adjudicated decisions can be replayed from a passing adjudication eval,
contradictory final package evidence has a human adjudication record, partition and coverage hashes
match the current upstream artifacts, and required provenance entities point at non-stale hashes.

Hard validation failures include:

- `missing_applicability_artifact`: a required applicability artifact is absent
- `missing_candidate_decision`: a candidate authority is missing from `applicability_decisions.jsonl`
- `duplicate_decision`: a candidate authority has more than one decision record
- `partition_gap`: a final decision is absent from both applicable and non-applicable artifacts
- `partition_overlap`: an authority appears in both applicable and non-applicable artifacts
- `unresolved_authority`: a decision with `unresolved` or `needs_adjudication` is treated as
  review-ready
- `non_applicable_basis_gap`: a non-applicable authority has no negative evidence, no-trigger
  rationale, search coverage certificate, or adjudication basis
- `applicable_evidence_gap`: an applicable authority has no package/source basis unless explicitly
  baseline-required and the baseline-required basis is evidenced
- `retrieval_trace_gap`: retrieval-backed evidence lacks query, result, rank, selected/rejected, or
  searched-index traceability
- `graph_trace_gap`: graph-supported evidence lacks graph path, traversal depth, selected/rejected,
  or graph-artifact traceability
- `search_coverage_gap`: a not-applicable or unresolved authority lacks a sufficient search
  coverage certificate or completed adjudication
- `contradictory_package_evidence`: package evidence supports both applicable and non-applicable
  outcomes without adjudication
- `forest_plan_scope_unresolved`: Forest Plan profile or component applicability lacks required
  source and package context
- `source_set_stale`: source-set, catalog, source-claim, or authority-universe hashes do not match the
  evaluated source set
- `package_cache_stale`: package manifest, package chunk, or package fact graph hashes do not match
  the applicability context
- `retrieval_trace_stale`: retrieval trace hashes do not match the searched package, source, or index
  artifacts
- `graph_trace_stale`: graph trace hashes do not match the searched graph artifacts
- `search_coverage_stale`: search coverage certificates do not match the retrieval trace, graph
  trace, package fact graph, or authority universe
- `adjudication_missing`: a human-adjudicated decision lacks a complete adjudication reference or a
  passing replayable adjudication eval
- `provenance_gap`: required provenance entities, paths, or entity hashes are missing or stale
- `generated_rule_pack_mismatch`: the generated rule pack does not match the
  `applicable_authorities.json` artifact
- `generated_rule_pack_stale`: the generated rule pack is stale relative to package, source set,
  authority universe, package fact graph, retrieval trace, graph trace, search coverage
  certificates, or validation artifact

`applicability_adjudication_template.json` has schema version `applicability-adjudication-template-v0`
and contains one editable adjudication item per `unresolved` or `needs_adjudication` decision. Each
item includes the decision ID, candidate authority ID, current status, missing evidence, contradiction
notes, cited package/source snippets, allowed final statuses, adjudicator fields, decision rationale,
and required citation fields.

`applicability_adjudication_worklist.md` is a reviewer-facing rendering of the same template. It
groups unresolved authorities by failure category, authority category, Forest Plan profile/component
context, and missing evidence type.

`applicability_adjudication_eval.json` has schema version `applicability-adjudication-eval-v0` and
records whether every adjudication item was completed, whether the adjudicated final statuses are
valid, whether required rationale/citations are present, and whether the completed adjudication can be
replayed deterministically into `applicability_decisions.jsonl`.

`applicability_adjudication_apply.json` has schema version `applicability-adjudication-apply-v0` and
records the replay result when a completed adjudication is applied to the decision ledger. It
includes original and applied decision-ledger hashes, applied item count, remaining unresolved count,
applicable/non-applicable partition hashes, and the adjudication/eval artifact paths. Applying
adjudication rewrites `applicability_decisions.jsonl`, `applicable_authorities.json`, and
`non_applicable_authorities.json` with `human_adjudication` bases and updates provenance after the
apply artifact is written so provenance records the final apply-artifact hash.

`llm_evidence_proposals.jsonl`, when present, is diagnostic-only. It may propose evidence spans,
query expansions, graph neighbors, or reviewer questions, but it cannot write final applicability
statuses, satisfy search coverage by itself, or make generated rule packs reviewer-ready.

`generated_rule_pack.json` has schema version `generated-compliance-rule-pack-v0` and is the only
rule pack accepted by the target downstream compliance-review path. It includes:

- `base_rule_pack_id`
- `base_rule_pack_version`
- `base_rule_pack_sha256`
- `generated_rule_pack_id`
- `generated_rule_pack_version`
- `applicability_run_id`
- `applicability_validation_sha256`
- `authority_universe_sha256`
- `applicable_authorities_sha256`
- `non_applicable_authorities_sha256`
- `applicability_provenance_sha256`
- `package_fact_graph_sha256`
- `retrieval_trace_sha256`
- `graph_trace_sha256`
- `search_coverage_certificates_sha256`
- `package_manifest_sha256`
- `package_chunks_sha256`
- `catalog_sha256`
- `source_set_id`
- `review_id`
- generated rules

Each generated rule carries:

- explicit base rule ID and generated rule ID
- applicability decision ID
- applicability evidence references, including package fact node IDs, retrieval trace IDs, graph path
  IDs, and search coverage certificate IDs when relevant
- source-record IDs and document roles
- source-claim link requirements
- package-section expectations
- Forest Plan component references when relevant
- per-rule source, package, authority-universe, applicability-validation, applicable-authorities,
  non-applicable-authorities, and provenance hashes

`generated_rule_pack_validation.json` has schema version `generated-rule-pack-validation-v0` and
records:

- `generated_rule_pack_id`
- `generated_rule_pack_sha256`
- `applicability_run_id`
- `applicability_validation_sha256`
- `base_rule_pack_id`
- `base_rule_pack_version`
- `base_rule_pack_sha256`
- `authority_universe_sha256`
- `applicable_authorities_sha256`
- `non_applicable_authorities_sha256`
- `applicability_provenance_sha256`
- `package_fact_graph_sha256`
- `retrieval_trace_sha256`
- `graph_trace_sha256`
- `search_coverage_certificates_sha256`
- `package_manifest_sha256`
- `package_chunks_sha256`
- `catalog_sha256`
- `source_set_id`
- `review_id`
- `passed`
- whether the generated rule count equals the validated applicable-authority count
- whether all generated rules trace to applicable decisions
- whether non-applicable authorities are absent
- whether source-claim links are present for claim-bearing generated rules
- whether the applicability validation still matches current upstream artifacts
- whether package, source-set, catalog, authority-universe, package-fact-graph, retrieval-trace,
  graph-trace, search-coverage, validation, provenance, applicable-authority, and
  non-applicable-authority hashes match the validated applicability artifacts

`applicability-generate-rule-pack --validate-only` rechecks an existing generated pack without
rewriting it. Validation requires the previously recorded generated-pack hash, so a hand-written pack
cannot be blessed by its first validate-only run. Manual edits fail with
`generated_rule_pack_mismatch`; upstream artifact drift or stale applicability validation fails with
`generated_rule_pack_stale`.

The non-applicable authority artifact is separate from the compliance matrix. A combined
reviewer-facing report may link to `non_applicable_authorities.json`, but the target compliance
matrix evaluates compliance findings only for generated applicable rules.

### Applicability Eval Outputs

`applicability-eval` writes
`source_library/reviews/applicability_eval/applicability_eval_results.json` unless `--results-dir`
is supplied. The result schema is `applicability-eval-results-v0` and records:

- eval ID, eval version, eval file, base rule-pack path, base rule-pack ID/version, source set IDs,
  output path, authority-family template config path when loaded, and created timestamp
- case count, passed/failed counts, generated-rule-pack-ready case count, aggregate metrics, and
  failure-category counts
- one case summary per fixture, including review ID, source set ID, artifact paths, actual and
  expected statuses, applicable/non-applicable/generated rule IDs, package fact types, source-record
  and document-role alignment status, package-section alignment status, graph path/non-path status,
  basis-type alignment status, expected and actual arbitration statuses, expected and actual
  arbitration decision effects, per-case arbitration summary counts, authority-family IDs by rule
  ID, adjudicated rule IDs, required artifact gaps, coverage gaps, generated-rule-pack readiness,
  generated-pack hash and coverage mismatch status, and failure taxonomy
- `arbitration_summary`, which aggregates arbitration status/effect counts and the readiness
  buckets for applicable-with-weak-auxiliary, weak-only needs-adjudication,
  insufficient-strong-trigger needs-adjudication, and positive/negative conflict
  needs-adjudication cases
- `authority_family_template_coverage`, which records high-priority authority-family IDs,
  positive/negative/unresolved/adjudicated coverage counts, real-package coverage tags, and missing
  coverage lists

Each eval case materializes a review directory under
`source_library/reviews/applicability-eval-<case_id>/` and runs the same applicability artifact
sequence used by the reviewer path: authority universe, package fact graph, applicability
retrieval/graph traces, deterministic decisions, validation, and generated-rule-pack validation.
The eval fails when expected applicability statuses or partitions drift, non-applicable authorities
lack coverage certificates, expected retrieval or graph traces are missing, expected graph non-paths
are violated, package facts are not found, source-record/document-role/package-section alignment
fails, expected arbitration statuses or decision effects drift, negative/no-trigger evidence is
absent, required applicability artifacts are missing, the generated rule-pack hash differs from
validation, or generated rule-pack rules do not match validated applicable authorities.

`applicability-gold-eval` writes
`source_library/reviews/applicability_gold_eval/applicability_gold_eval_results.json` unless
`--results-dir` is supplied. The result schema is `applicability-gold-eval-results-v0` and records
gold eval identity, adjudication checks, required profile coverage, nested applicability-eval
metrics, arbitration summary counts, failure categories, and `promotion_ready`. Promotion readiness
is true only when positive, mixed, negative, unresolved, and replay-adjudicated profiles are
present, every case has adjudication metadata, at least one gold case has explicit arbitration-field
expectations, and the nested applicability eval passes. Gold evals carry forward the nested
`authority_family_template_coverage` and `arbitration_summary` summaries so promotion checks can
prove adjudication and arbitration coverage for expanded authority-family templates.

## Compliance Review Outputs

Path: `source_library/reviews/<review_id>/`

The `compliance-review` command writes the base EA review outputs plus:

- `compliance_validation.json`
- `compliance_review.json`
- `compliance_matrix.json`
- `compliance_matrix.md`
- `compliance_matrix.pdf`
- `authority_family_provenance.json`
- `non_applicable_authority_appendix.json`
- `non_applicable_authority_appendix.md`
- `authority_reviewer_resolution_report.json`
- `litigation_risk_summary.json`
- `finding_graph_nodes.jsonl`
- `finding_graph_edges.jsonl`

It also invokes the forest-plan resolver against the same package cache. For packages resolved to
the selected forest-plan profile, the review directory includes the forest-plan context,
component-finding, component-inventory coverage, applicable-standard coverage, and
reviewer-resolution artifacts described above. Custer Gallatin compliance review fails closed when
that forest-plan component evaluation is absent, stale, or not reviewer-ready.

`compliance-review` reads:

- a local EA package file or directory passed with `--package-path`
- a generated applicability rule pack, normally
  `source_library/reviews/<review_id>/applicability/generated_rule_pack.json`
- adjacent applicability artifacts:
  `applicability_validation.json`, `generated_rule_pack_validation.json`,
  `non_applicable_authorities.json`, `search_coverage_certificates.json`, and
  `applicability_provenance.json`
- reviewer-ready source claim artifacts and rule-claim bindings under
  `source_library/derived/<source_set_id>/claims/` and
  `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/`
- the source-library retrieval index, normally
  `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`
- the source-set forest-plan component inventory at
  `source_library/derived/<source_set_id>/forest_plan_components/component_inventory.json` when the
  package resolves to the selected forest-plan profile

When `--reuse-package-cache` is supplied, the review directory must already contain:

- `package/package_manifest.jsonl`
- `package/package_chunks.jsonl`

In that mode the command preserves those package cache files and reruns checklist/compliance
evaluation without re-extracting the package files.

Reviewer-ready runs reject the base `compliance-rule-pack-v0` rule pack. Passing
`--allow-base-rule-pack-review` allows a diagnostic run, but that output is not reviewer-ready and
is excluded from promotion readiness. The reviewer-ready generated rule pack has schema version
`generated-compliance-rule-pack-v0` and includes the generated-pack fields above.

- `rule_pack_id`
- `version`
- `title`
- optional description, domain, and jurisdiction
- optional `baseline_source_record_ids`
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
- `authority_category`
- `authority_source_record_id`
- `applicability_mode`
- `package_query`
- `package_terms`
- optional `package_section_terms`, which are section-context preference terms used to rank and
  anchor package evidence only after the required package terms match
- optional `package_section_term_groups`, where each inner list is an OR group and every group must
  match in one package chunk before the section context is preferred
- optional `applies_if_package_terms`
- optional `applies_if_package_term_groups`, where each inner list is an OR group and every group
  must match in one package chunk before a conditional rule is applicable
- optional `does_not_apply_if_package_terms`, which records explicit non-applicability phrases that
  keep a conditional rule not applicable when the same package chunk only discusses why the
  authority path is not used
- `source_query`
- `source_filters`
- optional `evidence_expectation`

`authority_document_role` may be supplied explicitly on a rule; otherwise generated artifacts derive
it from `source_filters.document_role`.

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
When `baseline_source_record_ids` is present, rule-pack validation requires every listed source
record ID to be safe, unique, covered by at least one rule, and covered only by rules whose
`applicability_mode` is `baseline`.

`compliance_review.json` has schema version `compliance-review-v0` and includes:

- summary paths and counts
- rule-pack ID and version
- rule count, baseline source-record count/list, evaluated baseline source-record list, finding
  count, claim-bearing finding count, finding status counts, and authority identification summary
- unsupported finding IDs
- `forest_plan_review`, with forest-plan resolver paths, scope status, reviewer-ready status, and
  component-evaluation artifact paths when applicable
- `applicability_gate`, with generated-pack validation, applicability validation,
  non-applicable-authority, search-coverage, provenance, and package-manifest gate paths/status
- authority integration paths and summary counts for authority-family provenance,
  non-applicable appendices, reviewer-resolution reporting, and deterministic litigation-risk
  categories
- validation
- compliance findings

Each compliance finding includes:

- rule-pack ID and version
- rule ID, title, question, requirement, and severity
- authority category, authority source record ID, authority document role, and applicability mode
- candidate authority ID, applicability decision ID, candidate authority type, authority-family IDs,
  generated-applicability marker, search-coverage certificate IDs, and adjudication references when
  present
- status: `pass`, `gap`, or `uncertain` for generated applicable rules; base diagnostic runs may
  still emit `not_applicable`
- claim type: `supported_compliance_finding`, `package_evidence_gap`, or `no_compliance_claim`
- package query, package terms, source query, and source filters
- applicability status, applicability terms, optional applicability term groups, optional
  non-applicability terms, applicability rationale, applicability evidence, and explicit
  non-applicability evidence
- package and source-library evidence statuses
- package and source-library citation labels when present
- source-claim link count, source claim IDs, source-claim evidence citations, and source-claim links
- top package and source-library evidence results
- limitations

`compliance_matrix.json` has schema version `compliance-matrix-v0` and includes:

- review ID, package path, source set, rule-pack summary, and matrix summary
- status counts, applicability counts, applicable source records, claim row count, validation status,
  reviewer-ready status, PDF path, `applicability_gate`, authority integration paths,
  `non_applicable_authorities.json`, `search_coverage_certificates.json`, and
  `forest_plan_review` links when present
- row columns for authority, applicability, status, EA evidence, source evidence, source claims, and
  limitations
- one NEPA/authority table row per compliance finding
- a separate `forest_plan_compliance` section when forest-plan component review artifacts are
  present

The matrix rule-pack summary includes `baseline_source_record_ids` when the active rule pack
declares them.

Each matrix row includes:

- rule ID, rule title, question, requirement, severity, status, claim type, confidence, and rationale
- authority category, authority source record ID, authority document role, applicability mode,
  applicability status, candidate authority ID, applicability decision ID, authority-family IDs,
  search-coverage certificate IDs, adjudication references, and applicability basis
- applicability basis fields including source filters, package terms, conditional applicability
  terms, optional conditional applicability term groups, optional explicit non-applicability terms,
  source query, applied source record IDs, and applied source document roles
- package query, source query, EA package citation, compact EA evidence span, source-library
  citation, and compact source evidence span
- source-claim IDs, source-claim citations, source-claim count, citation-gate status, limitations,
  and failure category when applicable

When present, `forest_plan_compliance` has schema version `forest-plan-compliance-matrix-v0` and
contains a separate Forest Plan Compliance table. Its rows are derived from
`forest_plan_component_findings.json` and `forest_plan_applicable_standard_coverage.json`; each row
records component ID/type, applicability status, compliance status, finding status, EA-package
evidence, Forest Plan source evidence, plan-consistency determination text, rationale, and reviewer
resolution count. This keeps Forest Plan component compliance visible without mixing component rows
into the NEPA/generated-rule compliance table.

`compliance_matrix.md` is a compact human-readable rendering with a `NEPA / Authority Compliance`
table plus the separate `Forest Plan Compliance` table when available.
`compliance_matrix.pdf` is generated for every compliance review from the same JSON matrix data. The
JSON matrix is the stable machine contract.

Authority integration sidecars are generated for every compliance review. In diagnostic base-pack
runs they are present but marked non-reviewer-ready through validation; in generated-pack runs they
are required promotion artifacts.

`authority_family_provenance.json` has schema version `authority-family-provenance-v0` and records:

- review/source-set/rule-pack identity and links back to compliance review, matrix, and validation
- one finding-provenance row per generated compliance finding
- rule ID, finding ID, candidate authority ID, applicability decision ID, candidate authority type,
  authority-family IDs, basis type, source record IDs, applicability status/mode, coverage
  certificate IDs, and adjudication references
- summary lists for findings missing candidate authority IDs or authority-family IDs

`non_applicable_authority_appendix.json` has schema version
`non-applicable-authority-appendix-v0`; `.md` renders the same appendix for reviewers. Each row
records candidate authority ID/type, decision ID, authority-family IDs when known, status, basis
type, rationale, source records, search-coverage certificate IDs, compact coverage-certificate
details, negative evidence spans, trigger-miss evidence, and adjudication references. Generated
review validation requires every row to have coverage certificates and rationale.

`authority_reviewer_resolution_report.json` has schema version
`authority-reviewer-resolution-report-v0`. Its summary records pending-resolution count,
adjudicated-authority count, whether reviewer-ready output is blocked, and a pass flag. Pending
`unresolved` or `needs_adjudication` items block reviewer-ready compliance output until an
adjudication artifact resolves them.

`litigation_risk_summary.json` has schema version `litigation-risk-summary-v0`. It records
deterministic risk categories such as `package_evidence_gap`,
`non_applicable_authority_coverage_boundary`, `unresolved_authority_family_requires_resolution`,
and `human_adjudicated_authority_family`. Each flag has rule IDs, authority-family IDs, candidate
authority IDs, evidence/artifact refs, rationale, `deterministic_basis=true`, and
`legal_conclusion=false`; this artifact is not a legal conclusion generator.

## EA Consistency Decision-Support Outputs

Path: `source_library/reviews/<review_id>/decision_support/`

The EA consistency decision-support artifact family is the generated supervisor-facing synthesis
layer over existing audited review artifacts. It is decision support only: it does not create legal
advice, a legal sufficiency determination, or a final agency decision. It must read generated review
artifacts and tracked config/fixtures, not root-level manual East Crazies draft exports.

Sequence 1 defines the tracked report contract, and Sequence 2 adds the deterministic generator and
CLI command:

- `config/ea_consistency_decision_support_v1.json`
- `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json`
- `tests/fixtures/decision_support/minimal_decision_support_report.json`
- `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`
- `src/usfs_r1_ea_sources/cli_decision_support.py`

Generate the artifact family with:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
```

Validate an existing generated family without rewriting it with:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only
```

The generated artifact family includes:

- `ea_consistency_decision_support.json`
- `ea_consistency_decision_support.md`
- `ea_consistency_decision_support.pdf`
- `ea_consistency_decision_support_manifest.json`

`ea_consistency_decision_support.json` has schema version
`ea-consistency-decision-support-report-v1` and is the canonical report. Markdown and PDF renderings
must derive from that JSON. The report must include these top-level sections:

- `executive_determination`
- `record_and_artifact_inventory`
- `applicable_authority_summary`
- `authority_findings`
- `forest_plan_consistency`
- `applicable_forest_plan_standards`
- `non_applicable_authority_boundary`
- `implementation_confirmation_checklist`
- `residual_risk_register`
- `validation_and_replay`

Sequence 5 defines the supervisor-readable rendering contract for the Markdown/PDF derivatives.
Those renderings must front-load a "How To Use This Document" note, bottom-line
decision-support status, authority category/status counts, Forest Plan basis, applicable-standard
coverage, non-applicable authority boundary, implementation-confirmation count, residual-risk count,
validation status, and concise table summaries before long evidence sections. The note must state
that the document supports review and does not replace responsible official, line officer, counsel,
or specialist judgment. Implementation-confirmation tables must preserve constrained
decision-support wording plus evidence selectors, and residual-risk rows must preserve source
artifact and selector pointers. Validation fails closed with
`false_negative_synthesis_omission` when otherwise-current Markdown or PDF renderings omit the
required supervisor-review front matter, section order, table summaries, counts, or source-pointer
content.

The schema keeps four statuses separate:

- applicability status, sourced from applicability artifacts;
- compliance status, sourced from compliance findings or Forest Plan standard coverage;
- implementation-confirmation status, sourced from tracked config plus evidence selectors;
- residual-risk category and `legal_conclusion`, sourced from generated risk/resolution artifacts.

Every row that can appear in a reviewer-facing section must include row-level traceability:

- `trace_ids[]`, with `trace_id`, `trace_type`, `source_artifact_path`, and `source_selector`;
- `source_selectors[]`, with artifact paths and row/chunk/standard/candidate selectors;
- evidence objects with `chunk_id`, `source_record_id`, `citation_label`, `artifact_sha256`,
  `content_sha256`, and `text_span`.

`ea_consistency_decision_support_manifest.json` has schema version
`ea-consistency-decision-support-manifest-v1`. It records review ID, source set ID, generator
version, generation timestamp, validation status, input artifact paths, per-section dependencies,
and SHA-256 values for the package manifest/chunks, applicability validation, applicable and
non-applicable authority artifacts, search coverage, generated rule-pack validation, compliance
matrix/review, Forest Plan component findings, applicable-standard coverage, Forest Plan context,
authority reviewer-resolution report, litigation-risk summary, Plan Consistency Table text, and
tracked decision-support config. The generator fails closed before writing outputs when required
artifacts are missing, unparsable, stale against the expected hash baseline, count-drifted,
non-reviewer-ready, missing required package/source evidence, missing non-applicable search
coverage, carrying unresolved implementation selectors, or carrying residual-risk legal
conclusions.

Sequence 4 makes the generated family a readiness gate. `phase-eval --review-id` includes a
`decision_support_report` phase for a review with a generated decision-support directory and for the
configured East Crazies proving review. That phase revalidates current source-artifact hashes,
required report sections, applicable and non-applicable authority counts, Forest Plan component
counts, applicable-standard counts, PDF validity, reviewer-ready source status, residual-risk
boundaries, and manual-draft quarantine. The promotion suite also checks the report JSON, manifest,
and PDF as required current-promotion artifacts for `v1-cg-ecid-compliance-review`.

`config/ea_consistency_decision_support_v1.json` has schema version
`ea-consistency-decision-support-config-v1`. It owns synthesis-only labels, grouping, display order,
allowed caveat text, residual-risk grouping, report-quality eval expectations, and
implementation-confirmation selectors. Implementation-confirmation rows are not compliance
findings. Each config row must have a stable confirmation ID, display label, evidence status,
allowed status values, source selectors, and constrained wording guidance.

`config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json` has schema version
`ea-consistency-decision-support-expected-summary-v1`. It locks the East Crazies proving-review
contract: required sections, expected counts, input hashes, representative applicable authority,
representative non-applicable authority with search coverage, representative Forest Plan component,
all 12 applicable Forest Plan standards, row trace requirements, fail-closed categories, and
manual-draft quarantine policy.

The minimal test fixture at
`tests/fixtures/decision_support/minimal_decision_support_report.json` is synthetic. It proves the
schema boundary without copying full East Crazies evidence text. It must include at least one
applicable authority with package and source evidence, one non-applicable summary with search
coverage, one Forest Plan component, one applicable Forest Plan standard, one implementation
confirmation, one residual-risk row with `deterministic_basis=true` and `legal_conclusion=false`,
manifest-shaped input hashes, and passing validation metadata.

Decision-support validation must fail closed on:

- missing or unparseable required artifacts;
- stale generated artifacts;
- review/source-set mismatch;
- input hash mismatch;
- count drift;
- missing required report sections;
- missing or duplicated applicable authority rows;
- applicable authorities missing package or source evidence;
- missing non-applicable summaries or search coverage;
- non-applicable authorities promoted into compliance findings;
- missing Forest Plan component summaries;
- missing applicable standards or standard evidence;
- open authority or Forest Plan reviewer-resolution queues;
- unresolved implementation-confirmation selectors;
- residual-risk rows with `legal_conclusion=true`;
- dependency on root-level `East_Crazies_*` manual draft exports;
- missing report PDF or a PDF that does not start with `%PDF-`;
- synthesis false positives such as unsupported overclaims, reported as
  `false_positive_synthesis_claim`;
- synthesis false negatives such as omitted required rows, reported as
  `false_negative_synthesis_omission`.

## East Crazies Final QA And Certification Outputs

Path: `source_library/reviews/<review_id>/final_qa/`

The East Crazies final QA and certification artifact family is a replayable closeout packet over
existing audited artifacts for the promoted East Crazy Inspiration Divide review. It is not a new
compliance review, legal sufficiency determination, responsible-official approval, line-officer
approval, counsel certification, or Region 1 expansion claim. The configured proving review is
`v1-cg-ecid-compliance-review` over source set `source-set-ba8d0feae79501b8`.

Sequence 1 defines the tracked contract and fixtures, and Sequence 2 implements the deterministic
generator/validator CLI:

- `config/east_crazies_final_qa_certification_v1.json`
- `config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json`
- `tests/fixtures/final_qa/minimal_final_qa_certification_report.json`
- `src/usfs_r1_ea_sources/final_qa_certification.py`
- `src/usfs_r1_ea_sources/cli_final_qa.py`

The generated artifact family includes:

- `east_crazies_final_qa_certification.json`
- `east_crazies_final_qa_certification.md`
- `east_crazies_final_qa_certification.pdf`
- `east_crazies_final_qa_certification_manifest.json`
- `east_crazies_final_qa_certification_validation.json`

Generate or validate the packet with:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only
```

`east_crazies_final_qa_certification.json` has schema version
`east-crazies-final-qa-certification-report-v1`. Markdown and PDF renderings must derive from that
JSON. The report must include these top-level sections:

- `review_boundary`
- `gate_replay_summary`
- `artifact_freshness_ledger`
- `applicability_partition`
- `finding_qa`
- `forest_plan_qa`
- `decision_support_qa`
- `accepted_v1_risk_ledger`
- `certification_statement`
- `residual_blockers_and_stop_conditions`

`review_boundary` records the review ID, source set, package path, review artifact root, and the
policy that root-level `East_Crazies_*` draft exports are not canonical. `gate_replay_summary`
records replay status for applicability validation, generated rule-pack validation, compliance
validation, compliance matrix, Forest Plan context, Forest Plan component eval, decision-support
validation, phase eval, V1 EA eval, and current-promotion suite. For the outer gates it records
both baseline counts that exclude the final QA self-reference (`19/19` phase eval and `22/22`
current-promotion results for this packet) and live integrated counts after gate integration
(`20/20` phase eval and `26/26` current-promotion results). `artifact_freshness_ledger` records
required artifact paths, schema versions where applicable, SHA-256 values, and selectors.

`applicability_partition` preserves the applicability boundary before compliance: `33` applicable
authorities, `340` non-applicable authorities, `0` unresolved authorities, and search-coverage
support for the non-applicable boundary. `finding_qa` records all `33` generated findings, finding
status counts, citation/source selectors, package-evidence selectors, per-finding package/source
evidence pointers, trace IDs, `142` rule-claim links, and `0` rule-claim gaps. `forest_plan_qa`
records Custer Gallatin context, `329` Forest Plan components, `58` standards, `12/12` applicable
standards, component-eval status, limitations, and
reviewer-resolution status. `decision_support_qa` records the existing decision-support validation
result, PDF-header validity, residual-risk rows, implementation-confirmation rows, and
legal-conclusion safeguards.

`accepted_v1_risk_ledger` is required. It records
`conditional_adjudication.policy_mode=accepted_pending_v1`, `accepted_pending_count=14`,
`actual_pending_count=14`, `actual_pending_applicable_count=7`, all accepted pending rule IDs, a
pointer to `v1_ea_eval_results.json`, and representative pending rows. These rows are explicit
accepted V1 reviewer risk; they must not be hidden as final pass findings or converted into legal
conclusions.

`certification_statement` records machine replay status, optional `reviewer_signoff` fields
(`reviewer_name`, `reviewer_role`, `reviewer_signature`, `review_date`, and `reviewer_notes`), and
a caveat that the packet supports review but does not replace responsible official, line officer,
counsel, or specialist judgment. Empty signoff fields do not fail machine validation.

`east_crazies_final_qa_certification_manifest.json` has schema version
`east-crazies-final-qa-certification-manifest-v1`. It records review ID, source set ID, validation
status, input artifact paths, required gate names, per-section dependencies, and SHA-256 values for
the decision-support report family, V1 EA eval, review-scoped phase eval, non-strict promotion
suite, compliance validation, applicability validation, generated rule-pack validation, compliance
matrix/PDF/review, Forest Plan context summary, and Forest Plan component eval.

`east_crazies_final_qa_certification_validation.json` has schema version
`east-crazies-final-qa-certification-validation-v1`. It records the generator validation result
used by outer readiness gates: review ID, source set ID, machine replay status, check counts, failed
check count, failure-category counts, output-file paths for the JSON, Markdown, PDF, manifest, and
validation sidecar, and SHA-256 hashes for the non-circular JSON, Markdown, PDF, and manifest
outputs. Sequence 3 makes this sidecar a required current-promotion artifact, verifies those
sidecar hashes back against local files in `promotion-suite`, and adds an optional
`final_qa_certification_report` phase to review-scoped `phase-eval` when the sidecar exists.

`config/east_crazies_final_qa_certification_v1.json` has schema version
`east-crazies-final-qa-certification-config-v1`. It owns section order, expected review/source-set
IDs, required gate names, required count fields, artifact selectors, caveat text, reviewer signoff
fields, prohibited certification phrases, rendering requirements, manual-draft policy, and
fail-closed categories. Its `required_count_fields` must cover every scalar expected-summary count,
and its `validation_expectations` map the Sequence 1 acceptance criteria to the failure categories
that later runtime validation must use.

`config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json` has schema version
`east-crazies-final-qa-expected-summary-v1`. It locks current East Crazies semantic counts, source
selectors, current artifact hashes, representative applicable authority and non-applicable
authority rows, a representative Forest Plan standard, a representative decision-support residual
risk row, selected Markdown/PDF rendering requirements, and the accepted V1 risk ledger. It does
not pin full rendered Markdown/PDF body text.

The minimal test fixture at
`tests/fixtures/final_qa/minimal_final_qa_certification_report.json` is synthetic. It proves the
schema boundary without depending on local `source_library/`; it must include one gate replay,
artifact freshness rows, one applicable finding with citations/selectors, one non-applicable
boundary row with search coverage, one Forest Plan standard, one decision-support residual-risk row
with `legal_conclusion=false`, one accepted V1 risk row, a certification statement, optional
`reviewer_signoff`, and empty blockers.

Final QA validation must fail closed on:

- missing or unparseable required artifacts;
- stale generated artifacts;
- review/source-set mismatch;
- input hash mismatch;
- count drift;
- missing required gate sections;
- missing citations or source selectors;
- missing non-applicable boundary evidence;
- unresolved reviewer items;
- invalid report PDF header;
- dependency on root-level `East_Crazies_*` manual draft exports;
- hidden accepted V1 risk, reported as `accepted_v1_risk_hidden`;
- legal-conclusion wording, reported as `legal_conclusion_leak`;
- human-certification overclaim, reported as `human_certification_overclaim`.

`finding_graph_nodes.jsonl` contains:

- `ComplianceRulePack`
- `ComplianceReview`
- `ForestPlanReview`
- `ForestPlanComponentEvaluation` when component evaluation runs
- `ComplianceRule`
- `ComplianceFinding`
- `SourceClaim`
- `SourceLibraryEvidence`
- `PackageEvidence`
- `PackageEvidenceGap`

`finding_graph_edges.jsonl` relationships include:

- `RULE_PACK_USED_BY_REVIEW`
- `RULE_PACK_HAS_RULE`
- `REVIEW_EVALUATED_RULE`
- `RULE_PRODUCED_FINDING`
- `RULE_BOUND_TO_SOURCE_CLAIM`
- `FINDING_SUPPORTED_BY_SOURCE_CLAIM`
- `FINDING_SUPPORTED_BY_SOURCE_EVIDENCE`
- `FINDING_SUPPORTED_BY_PACKAGE_EVIDENCE`
- `FINDING_HAS_PACKAGE_GAP`
- `REVIEW_INCLUDES_FOREST_PLAN_REVIEW`
- `FOREST_PLAN_REVIEW_HAS_COMPONENT_EVALUATION`

`compliance_validation.json` records gate-facing checks for:

- rule-pack validity, including `baseline_source_records_covered` inside the nested rule-pack
  validation when `baseline_source_record_ids` is declared
- rule-claim binding readiness
- base EA review validation
- Custer Gallatin forest-plan component reviewer readiness through
  `forest_plan_component_gate_reviewer_ready`
- every rule evaluated
- declared baseline source records evaluated in the findings
- valid finding statuses
- `pass` findings have both package and source-library evidence
- `gap` findings have source-library evidence
- claim-bearing findings have source-library citation labels
- claim-bearing findings have source-claim links
- no unsupported compliance claims are emitted
- finding graph evidence edges match each finding claim type
- finding graph node/edge integrity
- finding graph rule and finding coverage

## Compliance Review Eval Outputs

Path: `source_library/reviews/compliance_review_eval/`

The `compliance-review-eval` command writes:

- `compliance_review_eval_results.json`
- `packages/<case_id>.txt` for package text fixtures embedded in the eval file
- `reviews/<case_id>/` containing the generated compliance review artifacts for that case

The default eval file is `config/compliance_review_eval_seed.json`.

Each eval case includes:

- stable `id`
- exactly one package fixture, either `package_text` or `package_path`
- `expected_statuses`, mapping every rule-pack rule ID to `pass`, `gap`, `uncertain`, or
  `not_applicable`
- optional expected claim types, package evidence, source evidence, source-claim links, status
  counts, expected source record IDs, expected source document roles, unsupported finding IDs, and
  graph coverage requirements
- optional filters over `rule_id`, `status`, or `claim_type`

Unknown filters, empty filters, unsupported statuses, unsupported claim types, unsafe case IDs, and
invalid package fixture definitions fail before reviews run. Rule-scoped expectations must refer to
current rule-pack rule IDs, and expected status counts must match `expected_statuses` and sum to the
rule count.

`compliance_review_eval_results.json` has schema version `compliance-review-eval-v0` and records:

- eval file, output path, rule pack, source set, top-k values, and creation timestamp
- case count, passed count, failed count, and aggregate pass status
- metrics for validation matching, reviewer-ready matching, status matching, claim-type matching,
  package evidence matching, source evidence matching, source-claim link matching, source-record
  matching, source-document-role matching, citation coverage, graph coverage, unsupported finding
  matching, and zero-finding rate
- per-case generated review paths, expected and actual statuses, expected and actual claim types,
  evidence mismatches, source-record mismatches, source-document-role mismatches, unsupported
  finding IDs, validation failed checks, compact finding summaries, failure reasons, failure
  taxonomy, compact reproduction paths, and pass/fail status

## V1 Real EA Review Eval Outputs

Default contract: `config/v1_ecid_real_ea_eval.json`

Default output:
`source_library/reviews/<review_id>/v1_ea_eval_results.json`

The `v1-ea-eval` command reads an existing real review directory. It does not create package
fixtures or rerun `compliance-review`. The gate expects these review artifacts:

- `compliance_review.json`
- `compliance_matrix.json`
- `compliance_validation.json`
- `package/package_chunks.jsonl`
- Custer Gallatin forest-plan artifacts when the contract has `forest_plan` expectations

The contract has schema version `v1-ea-real-review-eval-contract-v0` and records:

- review identity: eval ID, review ID, source-set ID, rule-pack ID, and rule-pack version
- `section_expectations` for required real-EA section families and detection terms
- `rule_review_expectations` for rule-to-package-section, source-record, document-role, and
  citation checks
- `conditional_source_expectations` for `applicable`, `not_applicable`,
  `needs_reviewer_resolution`, or `adjudicate` conditional-rule expectations. Each conditional
  expectation must include `classification_rationale` so the contract records why the real EA row is
  considered applicable, not applicable, or pending reviewer adjudication.
- `conditional_adjudication_policy` when any conditional expectation uses `adjudicate`. The current
  accepted policy mode is `accepted_pending_v1`, with an explicit pending count, accepted pending
  rule IDs, and rationale. The evaluator fails closed if pending adjudication rows are not covered
  by this policy or if the accepted pending count/rule-ID fields are malformed.
- `forest_plan` expectations for required plan source records, resolved geographic/management
  areas, component IDs, applicable standards, reviewer readiness, total open reviewer-resolution
  items, and open standard reviewer-resolution items

`v1_ea_eval_results.json` has schema version `v1-ea-real-review-eval-results-v0` and records:

- summary identity, output path, overall pass/fail status, lane pass/fail status, checks, metrics,
  and failure-category counts
- `generated_at`; reruns preserve the existing timestamp when the semantic payload is unchanged so
  final QA input hashes do not churn only because the eval command was replayed
- `broader_ea_passed`, `forest_plan_passed`, `forest_plan_component_adjudication_required`,
  `broader_ea_failure_category_counts`, `forest_plan_failure_category_counts`,
  `failed_rule_expectation_count`, `failed_rule_ids`, `failed_rule_ids_by_category`,
  `failed_rule_expectations`, and `eval_lanes`. The failed-rule summaries name rule IDs,
  expectation type, failure categories, actual applicability/status, expected and actual package
  sections, and expected and actual source records so CLI output can identify the blocking rule rows
  without manual JSON inspection. `eval_lanes.overall` preserves the full readiness gate,
  `eval_lanes.broader_ea` isolates package sections, baseline authority alignment, rule bindings,
  conditional sources, and non-forest-plan artifact failures, and `eval_lanes.forest_plan` isolates
  Custer Gallatin source records, scope, components, applicable standards, reviewer readiness,
  forest-plan artifacts, the forest-plan compliance-validation gate, and component adjudication
  counts.
- `conditional_adjudication`, a summary of the gate-facing pending-conditional policy: policy mode,
  accepted pending count/rule IDs, actual pending count/rule IDs, actual applicable pending count,
  unexpected or missing pending rule IDs, and policy failure reasons
- `section_results` with detected package chunks and missed required section families
- `baseline_results` verifying baseline findings use their authority source records and document
  roles
- `rule_results` with expected and actual section IDs, source record IDs, document roles, citation
  status, and failure categories
- `conditional_results` with expected/actual applicability, adjudication-pending status, false
  positive/false negative counts, missing conditional-contract expectations, and source/section
  alignment. Results also carry the contract `classification_rationale`. When the review marks a
  conditional rule applicable, source/section alignment is enforced even if the contract still marks
  final applicability as `adjudicate`.
- top-level `conditional_adjudication` with the full pending-results queue for every accepted
  `adjudicate` row, including actual applicability/status, source/section alignment, expected and
  actual source records, expected and actual document roles, and the classification rationale
- `forest_plan_results` for required source records, resolved areas, component coverage,
  applicable-standard coverage, reviewer readiness, and reviewer-resolution queue size

Key metrics include section detection rate, baseline source/document-role match rates,
rule-section/source/document-role match rates, citation requirement match rate, conditional
expectation match rate, conditional adjudication completion rate, accepted/missing/unexpected
conditional adjudication counts, actual-applicable conditional source and section match rates,
missing conditional expectation count, conditional false positive and false negative counts,
forest-plan expectation match rate, reviewer-resolution item count, and standard reviewer-resolution
item count.

## Promotion Suite Outputs

Default manifest: `config/promotion_suite_v1.json`

Default path:
`source_library/reviews/promotion_suite/<suite_id>/`

The `promotion-suite` command writes:

- `promotion_suite_results.json`
- `promotion_suite_report.md`

The manifest has schema version `promotion-suite-v0` and records:

- suite ID, source-set ID, rule-pack path, rule-pack ID, rule-pack version, expected rule count, and
  expected baseline source-record count
- review cases with review IDs, package labels, required current-promotion results, artifact paths,
  and JSON or file-header checks
- suite-level results such as core phase-eval readiness, post-V1 applicability phase readiness,
  applicability seed/gold eval coverage, arbitration-summary checks, compliance-review eval, and
  compliance-gold eval
- review-case results that may be marked `required_for_expansion` so expansion readiness depends on
  verified review artifacts, not only expansion-slot manifest text
- expansion slots for additional real Region 1 EA packages, with acceptance signals and next actions

`promotion_suite_results.json` has schema version `promotion-suite-results-v0` and records:

- `current_promotion_ready`, `expansion_artifacts_ready`, `expansion_ready`, and `promotion_ready`
- manifest path, output path, Markdown report path, source set, rule-pack identity, and strict mode
- rule-pack check results
- per-review artifact checks, including compliance validation, compliance review, compliance
  matrix, compliance matrix PDF header, V1 real-EA eval, and NEPA 3D review graph
  validation/summary artifacts
- suite-level eval artifact checks
- NEPA 3D source-set graph validation and summary artifact checks for the current graph-readiness
  claim
- arbitration diagnostics from applicability eval, applicability gold eval, and review-bound
  phase-eval artifacts so promotion reports distinguish weak/conservative arbitration blockers from
  positive/negative adjudication conflicts
- open expansion slots and their required next actions, including selected package metadata such as
  review ID, source set, package path, forest-plan profile, official project metadata, expected gate
  artifacts, `manifest_ready`, dynamic `forest_plan_profile_checks`, and last local signal fields
  when the manifest provides them
- current-promotion `failure_category_counts` and expansion-only
  `expansion_failure_category_counts`
- failure-category counts using `missing_source`, `extraction_miss`, `retrieval_miss`,
  `applicability_miss`, `unsupported_package_evidence`, `stale_artifact`, `adjudication_needed`,
  `forest_plan_reviewer_not_ready`, `package_fixture_missing`, and graph-specific categories such
  as `graph_missing_authority_family`, `graph_missing_candidate_authority`,
  `graph_missing_source_record`, `graph_missing_applicability_decision`,
  `graph_viewer_export_invalid`, and `graph_region1_profile_gap`

By default, open expansion slots do not block `promotion_ready`; they are reported in
`expansion_failure_category_counts` and `open_expansion_slot_count`. Expansion artifacts marked
`required_for_expansion` also contribute to `expansion_artifacts_ready`,
`open_expansion_artifact_count`, and expansion failure categories. With `--strict-expansion`, open
expansion slots and failed expansion artifacts block `promotion_ready` and enter
`failure_category_counts`.

Selected not-ready expansion slots are validated fail-closed. A selected slot must carry
`review_id`, `source_set_id`, `package_path`, `expected_gate_artifacts`, `next_action`, and a typed
`failure_category` other than `package_fixture_missing`; each expected gate artifact must have an
ID and path. Ready slots must not retain `failure_category`. The Markdown report's expansion-slot
table includes review ID, package path, and failed categories in addition to status, readiness, and
next action.

Selected slots that declare `forest_plan_profile` are an additional fail-closed contract. The
manifest must provide required expansion result IDs and expected gate artifacts for
`compliance_review`, `forest_plan_context_summary`, and `phase_eval`. Runtime slot checks compare
the declared profile to `summary.forest_plan_review.scope_status`, require
`validation_passed=true` and `reviewer_ready=true`, verify the slot's last local forest-plan signal
matches the artifact, and require a Forest Plan component phase when the slot records that component
gating is required.

## Compliance Coverage Outputs

Default path:
`source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/compliance_coverage_results.json`

The `compliance-coverage` command reads:

- a versioned compliance rule pack
- a coverage matrix, defaulting to `config/compliance_rule_pack_coverage_nepa_ea_v0.json`
- compliance-review eval cases, defaulting to `config/compliance_review_eval_seed.json`
- reviewer-ready rule-claim links for the same source set and rule pack

The coverage matrix has schema version `compliance-rule-pack-coverage-v0` and contains one
`coverage_items` row per rule. Each row includes rule ID, obligation area, expected package
evidence, source record IDs, source-claim terms, and eval case IDs.

`compliance_coverage_results.json` has schema version `compliance-coverage-results-v0` and records:

- rule-pack identity, coverage-matrix path, eval file, rule-claim link path, and source set
- rule count, coverage item count, eval case count, and rule-claim link count
- rules without coverage items
- rules without compliance-review eval cases
- rules without source-claim links
- rules whose coverage-matrix source records do not match current rule-claim links
- rules whose coverage-matrix source-claim terms do not match current rule-claim links
- links per rule
- gate checks for rule-pack validity, matrix identity, matrix rule coverage, required fields,
  eval-case rule coverage, eval-case ID references, rule-claim readiness, source-claim link
  coverage, matrix/source-record agreement, and matrix/source-claim-term agreement

## Compliance Gold Eval Outputs

Default path:
`source_library/reviews/compliance_gold_eval/compliance_gold_eval_results.json`

Related generated artifacts:

- `adjudicated_cases.compliance_review_eval.json`, the gold cases normalized into the underlying
  compliance-review eval format
- `compliance_review_eval/compliance_review_eval_results.json`, the nested compliance-review eval
  result used by the promotion gate
- `compliance_review_eval/packages/<case_id>.txt` for inline package-text fixtures
- `compliance_review_eval/reviews/<case_id>/` for per-case generated compliance review artifacts

The `compliance-gold-eval` command reads:

- a versioned compliance rule pack
- a gold adjudication file, defaulting to `config/compliance_gold_eval_v0.json`
- reviewer-ready source-library artifacts used by the underlying `compliance-review-eval` path

The gold adjudication file has schema version `compliance-gold-eval-v0` and records:

- gold eval ID, version, title, rule-pack ID, and rule-pack version
- top-level adjudication metadata and promotion-gate intent
- at least three cases with positive, mixed, and negative profiles; the current project gold file
  contains ten adjudicated realistic profiles
- per-case adjudication metadata, package fixture, expected statuses for every rule, expected
  status counts, expected source record IDs, expected source document roles, unsupported finding
  IDs, and minimum finding count
- unique safe case IDs; package fixture paths must be relative child paths under the gold file
  directory when `package_path` is used instead of inline `package_text`

`compliance_gold_eval_results.json` has schema version `compliance-gold-eval-results-v0` and records:

- gold eval identity, rule-pack identity, source-set IDs, paths, and top-k values
- adjudication check status and underlying compliance-review eval pass status
- `compliance_review_eval_error` when the underlying eval could not execute because of a contract
  or missing-fixture problem
- `reviewer_ready_rule_pack`, which is true only for generated applicability rule packs accepted by
  the reviewer-ready compliance-review gate
- case count, adjudicated case count, passed/failed case counts, profile counts, and required
  profiles present
- aggregate failure-category counts from the underlying compliance-review eval
- `promotion_ready`, which is true only when the rule pack is reviewer-ready and adjudication checks
  plus the underlying compliance-review eval pass
- per-case adjudication metadata, expected and actual statuses, finding counts, review paths,
  matrix paths, failure taxonomy, failure reasons, and pass/fail status

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

The command replaces the derived directory for the selected `source_set_id` on each non-reuse run
so stale text or chunk files cannot survive from a previous extraction attempt. The `source_set_id`
is validated as a safe path segment before the derived directory is deleted. Reuse-first runs keep
the directory in place so validated current text/cache can be reused, but still rewrite the
manifest, chunks, validation, and summary files for the current source set.

`--id` may be supplied more than once for a delta extraction. A filtered extraction is valid for
repair or update work, but downstream retrieval remains non-reviewer-ready unless it is explicitly
built with partial-extraction allowance.

`--reuse-existing` reuses matching current source-set text/cache entries. `--reuse-inventory-path`
points to `reuse_inventory_records.jsonl` and lets extraction copy validated prior source-set text
for `reuse_extraction` candidates before reparsing any remaining `needs_extract` rows.

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
- `skipped_excluded`
- `no_artifact`
- `artifact_missing`
- `hash_mismatch`
- `parser_error`
- `parser_timeout`
- `empty_text`

`diagnostics/summary.json` includes source-set ID, catalog source count, required extraction source
count, selected source count, selected required extraction source count, skipped-excluded count,
extracted count, failed count, chunk count, parser counts, validation status, and extraction
filters. The `filters` object includes the legacy singular `id`, the repeated `ids` list when
multiple source records were selected, `parser`, and `limit`.

## Extraction Reuse Inventory Outputs

Path: `source_library/derived/<source_set_id>/reuse_inventory/`

The `reuse-inventory` command is read-only with respect to extraction/retrieval/review layers. It
reads the current catalog, the current extraction manifest if one exists, and prior derived
extraction manifests, then writes:

- `reuse_inventory.json`
- `reuse_inventory_records.jsonl`
- `summary.json`

`reuse_inventory_records.jsonl` contains one row per current catalog source with:

- `source_record_id`, title, source status, scope, document role, authority level, expected parser,
  and content type
- artifact path, artifact SHA256, artifact byte size, and artifact verification result
- `classification`, one of `already_current`, `already_current_cg_slice`, `reuse_extraction`,
  `needs_extract`, or `excluded`
- `current_extraction` metadata when the current source set already has matching extracted text
- `reuse_candidate` metadata when a prior source-set extraction can be reused
- candidate failure details when prior records were found but rejected

Reuse candidates require matching `source_record_id`, artifact SHA256, expected parser, content type,
existing extracted text, nonzero chunk count, and matching text SHA256. The inventory does not copy
text, rebuild chunks, build retrieval, or run any EA/compliance review.

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
artifact/text paths still exist, and each indexed chunk carries retrieval provenance. Scope-excluded
rows count toward selected catalog coverage but not required extraction coverage. A filtered
diagnostic index can be built with `--allow-partial-extraction`, but that summary records
`reviewer_ready: false`.

`retrieval_manifest.json` and `summary.json` include:

- source-set ID
- source chunks path
- catalog SQLite path
- extraction validation, manifest, and summary paths
- chunk count and indexed source count
- catalog source count, selected source count, required extraction source count, selected required
  extraction source count, skipped-excluded count, and extracted source count
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

`claim-eval` revalidates the current claim artifacts before scoring cases. It requires
`claim_validation.json` to have passed, `summary.json` to report `reviewer_ready: true`, and the
current files to still pass the claim validation checks. Tampered claim files fail before an eval
result is written.

`claim-eval` supports these eval filter keys:

- `source_record_id`
- `claim_type`
- `document_role`
- `authority_level`
- `citation_label`
- `review_topic`
- `topic`

Unknown filter keys and empty filter values fail eval-file validation so typoed filters cannot
silently broaden the eval. Supported expected claim types are the same claim types emitted by
`claim-extract`.

`claim-eval` writes `claim_eval_results.json` by default beside the claims file. It records eval
case count, pass rate, source hit rate, claim-type hit rate, expected-term hit rate, citation
coverage rate, zero-result rate, and per-case top claim results with provenance.

## Rule-Claim Binding Outputs

Path: `source_library/derived/<source_set_id>/rule_claim_links/<rule_pack_id>/<version>/`

The `rule-claim-link` command writes:

- `rule_claim_links.jsonl`
- `rule_claim_link_gaps.jsonl`
- `rule_claim_links.sqlite`
- `rule_claim_link_validation.json`
- `summary.json`

`rule-claim-link` reads:

- reviewer-ready source claims from `source_library/derived/<source_set_id>/claims/claims.jsonl`
- the claim readiness artifacts beside that file
- a versioned compliance rule pack, defaulting to
  `config/compliance_rule_pack_nepa_ea_v0.json`

Each `rule_claim_links.jsonl` record includes:

- `rule_pack_id`, `rule_pack_version`, and `rule_id`
- deterministic `link_id`
- rule query, requirement, and source filters
- rank, score, and matched terms
- `claim_id`, claim type, and exact claim text
- source record ID, chunk ID, citation label, authority level, document role, and review topics
- artifact path/SHA256, URL provenance, parser name/version, and source text path
- chunk-local and extracted-text character offsets
- claim text hash, chunk hash, and validation status

`rule_claim_link_gaps.jsonl` records explicit no-claim gaps for rules that have no validated source
claim match. A rule is covered only when it has at least one validated link or one explicit gap.

`rule_claim_link_validation.json` checks:

- rule pack validity
- source claims are reviewer-ready and still validate
- link and gap files exist
- link and gap records contain required fields and schema versions
- link IDs and gap IDs are unique
- link and gap records match the requested source set and rule-pack version
- link IDs and gap IDs are deterministic for the current source set, rule pack, and claim/gap
- link and gap rule metadata matches the current rule pack
- every rule has a validated claim link or explicit no-claim gap
- gap records are explicit, use supported gap reasons, and do not overlap linked rules
- links resolve to current source claims
- link provenance fields match current claim records
- links still satisfy rule source filters
- link scores and matched terms recompute from the current rule and claim text
- link ranks are contiguous per rule
- link claim types are supported
- SQLite counts match JSONL outputs

`summary.json` includes source set, rule-pack identity, top-k, rule count, claim count, link count,
gap count, linked-rule count, gap-rule count, rules without links, links per rule, claim-type counts,
source-record count, validation status, and `reviewer_ready`.

`rule-claim-eval` revalidates current rule-claim link artifacts before scoring cases. It writes
`rule_claim_link_eval_results.json` by default beside the link file and records pass rate, min-link
rate, claim-type hit rate, source hit rate, expected-term hit rate, citation coverage rate,
zero-result rate, and per-case top link results with provenance.

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

The `phase-eval` command writes `phase_eval_results.json` in the same directory. When
`--review-id` or `--review-dir` is supplied, it also writes a review-scoped copy at
`source_library/reviews/<review_id>/phase_eval_results.json` (or the supplied review directory) with
the same summary plus `review_id` and `review_dir`, so promotion checks can evaluate multiple
review-specific phase results without relying on the shared source-set phase artifact. It evaluates
catalog capture, extraction, retrieval, evidence graph, claim extraction, and rule-claim binding as
separate phases and records phase blockers so downstream compliance review cannot hide an upstream
failure. When `compliance_coverage_results.json` exists beside the rule-claim outputs, phase eval
also includes a `compliance_coverage` phase for matrix, source-claim, source-claim-term, and
eval-case coverage. When NEPA 3D graph validation/summary artifacts exist, phase eval also includes
`nepa_3d_source_set_graph` and, for review-scoped runs, `nepa_3d_review_graph` phases with
source-set/review identity checks, validation check counts, failed check names, graph paths,
readiness blocker counts, and graph failure-category counts. When `compliance_gold_eval_results.json` exists under
`source_library/reviews/compliance_gold_eval/`, phase eval also includes a `compliance_gold_eval`
promotion phase with explicit failed-check details for stale source-set, rule-pack, failed-gold, or
not-promotion-ready artifacts. For generated review rule packs, a passing gold eval against the
generated pack's declared base rule pack can satisfy this phase and is reported with
`rule_pack_match_mode=generated_base`. When `--review-id` or `--review-dir` is supplied, phase eval also
requires the applicability phases `authority_universe`, `package_fact_graph`,
`applicability_retrieval_trace`, `applicability_graph_trace`, `applicability_determination`,
`applicability_validation`, and `generated_rule_pack` before evaluating `compliance_review`.
Those applicability phases fail when the authority universe is missing or stale, package-fact graph
validation is missing or hash-mismatched, retrieval/graph trace diagnostics are stale, candidate
decisions do not exactly cover the authority universe, non-applicable authorities lack search
coverage certificates, applicability validation is missing or failed, or generated-rule-pack rules
do not exactly match the validated applicable-authority partition. The applicability-validation
phase also rechecks file-backed validation hashes for decision, partition, retrieval/graph trace,
search-coverage, and provenance artifacts so reviewer-ready phase output cannot rely on stale
validation. The phase result also includes `applicability_arbitration_summary`, and the
`applicability_determination` phase details embed the same summary. That summary reports
arbitration status/effect counts plus the explicit buckets for applicable decisions with weak
auxiliary evidence, weak-only needs-adjudication decisions, insufficient-strong-trigger
needs-adjudication decisions, and positive/negative conflict needs-adjudication decisions. The
compliance-review phase
requires the review report to exist, validation to pass, the review ID to match when supplied, and
the review source set to match the evaluated source set. It also requires `compliance_matrix.json`
to exist and match the review's schema version, review ID, source set, rule pack, row count, and
status counts, and requires `compliance_matrix.pdf` to exist with a valid PDF header. If that review
directory contains `forest_plan_component_eval_results.json`, phase eval
also includes a `forest_plan_component_eval` phase. That phase requires the component eval to exist,
use schema version `forest-plan-component-eval-results-v0`, pass, match the evaluated source set,
and match the supplied review ID when one is provided; its details include case counts, component
metrics, failed checks, and failure-category counts. If that
review directory contains `forest_plan_component_adjudication_eval.json`, or a completed
`forest_plan_component_adjudication.json` before the eval has been run, phase eval also includes a
`forest_plan_component_adjudication` phase. That phase requires the adjudication eval to exist,
pass, match the evaluated source set, and match the supplied review ID when one is provided; its
details include queue count, current reviewer-resolution queue count when available, whether those
counts match, resolved and pending adjudication counts, real EA omission and system-miss
counts/rates, completion rate, expectation match rate, disposition counts, adjudication-outcome
counts, and failure-category counts. Stale adjudication evals whose recorded queue count differs
from the current queue fail the phase. The evidence-graph and claim-extraction
phases report failed validation check names, retrieval index path, and retrieval binding mismatch
counts. The rule-claim-binding phase reports rule-pack identity, link count, gap count, and rules
without links.
