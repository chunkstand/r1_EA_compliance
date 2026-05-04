# Current System State

This project is a local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA
Forest Service Region 1 source material.

The workbook `usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx` remains the source-of-truth
input for the knowledge base. The generated `source_library/` is the audited local capture and
derived reviewer corpus used by extraction, retrieval, evidence graph, source-claim extraction,
rule-claim binding, and deterministic EA package review commands.

## Current Workbook Contract

The uploaded workbook now defines the active source contract:

- `Ingest_Checklist` ingest rows: `162`
- `Scope=Baseline` rows: `26`
- `Scope=Conditional` rows: `136`
- `R1_Forest_Plans` unit/overlay rows: `28`
- Total rows in the default ingest-driving sheets: `190`

The 26 `Scope=Baseline` rows are the baseline source records every EA compliance review must
evaluate. They are identified by the workbook `Scope` column, not by row position.

Baseline source record IDs:

```text
R1EA-001, R1EA-002, R1EA-003, R1EA-004, R1EA-008, R1EA-009, R1EA-010,
R1EA-013, R1EA-014, R1EA-015, R1EA-017, R1EA-018, R1EA-019, R1EA-020,
R1EA-021, R1EA-022, R1EA-023, R1EA-024, R1EA-025, R1EA-028, R1EA-029,
R1EA-031, R1EA-033, R1EA-034, R1EA-035, R1EA-067
```

The current generated downloader/catalog corpus now covers the full 190-row workbook contract:

- Parent batch run: `corpus-update-2026-05-01-cg-support-batches`
- Canonical workbook rows: `190`
- Batch count: `52`
- Passed batches: `52`
- Failed batches: `0`
- Repair-needed batches: `0`
- Repair queue: empty except the CSV header
- Unique effective URLs: `172`
- Reviewer catalog source set: `source-set-ba8d0feae79501b8`
- Reviewer catalog source rows: `190`
- Reviewer catalog unique artifacts: `160`
- Reviewer catalog source-artifact links: `189`
- Source statuses: `downloaded=8`, `downloaded_existing=170`, `duplicate_content=2`,
  `duplicate_url=9`, `skipped_excluded=1`

`R1EA-160` is present in the workbook/catalog as a `project_reference`, but has no artifact because
its URL remains in `Scope_Exclusions`. The current catalog validation passes, and the
captured-library integrity test suite passes against these generated outputs.

## Verified State Snapshot

Latest corpus-update verification was run locally on 2026-05-01 after adding the missed Custer
Gallatin FEIS and ESA-supporting plan documents.

- Active catalog source set: `source-set-ba8d0feae79501b8`
- Download/catalog batch: `corpus-update-2026-05-01-cg-support-batches`, `52/52` batches passed
- Catalog: `190` source rows, `160` unique raw artifacts, `189` source-artifact links
- Custer Gallatin supporting PDF records added: `R1PLAN-custer-gallatin-nf-04` through
  `R1PLAN-custer-gallatin-nf-07`
- Reuse inventory for the current source set is implemented and has been run locally. It classified
  `7` sources as already current in the Custer Gallatin slice, `181` sources as reusable from prior
  extraction outputs, `1` source as needing extraction, and `1` source as excluded.
- Reuse-first extraction assembly has been run for the full source set. It produced `190` terminal
  extraction manifest rows: `189` extracted rows, `1` scope-excluded row, `18,822` chunks,
  `188` reused rows, and `0` failed rows. `R1PLAN-dakota-prairie-grasslands-02` was parsed as the
  one fresh HTML extraction.
- Retrieval has been rebuilt from the assembled extraction layer with `18,822` chunks and
  `reviewer_ready: true`.
- Extraction accuracy audit passed for the current source set: `190` records checked, `189`
  extracted records, `18,822` chunks, no text-hash, raw-hash, offset, gap-coverage, markup, eCFR
  scope, or PDF token cross-check failures.
- Evidence graph has been rebuilt and is reviewer-ready with `38,601` nodes, `134,501` edges, and
  `0` retrieval-binding mismatches.
- Source-claim extraction has been rebuilt and is reviewer-ready with `43,353` claims, `9,818`
  entities, and `1.0` claim evidence/topic/authority coverage rates.
- Rule-claim binding for rule pack `nepa-ea-v0` version `0.4.0` has been rebuilt with `191` links
  across `44/44` rules, `0` gaps, and no rules without source-claim links.
- Compliance coverage has been refreshed for the `44`-rule matrix and `3` seed eval cases.
- Compliance review eval passed `3/3` seed cases. The Custer-scoped all-authorities fixture now
  expects `reviewer_ready: false` when the full forest-plan component gate is unmet.
- Compliance gold eval passed `10/10` adjudicated cases in the pre-applicability V1 artifact set.
  Under the current Milestone 8 gate, base-rule-pack gold eval reruns are diagnostic and are not
  `promotion_ready`; promotion readiness now requires a reviewer-ready generated applicability rule
  pack. Custer-scoped gold fixtures likewise preserve rule-level expected statuses while expecting
  the overall forest-plan component gate to fail readiness unless component evidence coverage is
  complete.
- Phase eval passed `17/17` phases with `reviewer_ready: true` for
  `source-set-ba8d0feae79501b8` and `v1-cg-ecid-compliance-review`, including the post-V1
  applicability artifact family and generated rule-pack gate.
- The current Custer Gallatin LMP component inventory was generated from the active source-set
  chunks: `329` components, `58` standards, `536` selected plan chunks, `0` missing component IDs,
  `0` duplicate component or standard IDs, and `2` non-blocking inventory-quality issues.
  Component-like labels with nonnumeric number tokens, such as cross-reference/table headings, are
  suppressed from generated component IDs and surfaced in build coverage.
- Final V1 EA gate promotion was verified locally on 2026-05-03 for
  `v1-cg-ecid-compliance-review`. The regenerated compliance review is reviewer-ready with `44`
  findings, `40` pass findings, `4` not-applicable findings, all `26` baseline source records
  evaluated, `191` rule-claim links, and `0` rule-claim gaps.
- Forest-plan component eval passed `35/35` adjudicated cases for the promoted review. The current
  component findings have `329` components, `79` supported components, `250` not applicable
  components, `0` gaps, `12/12` applicable standards applied, and `0` reviewer-resolution items.
- The final pre-applicability V1 gate commands passed: `phase-eval` `10/10`, `v1-ea-eval` with
  `broader_ea_passed=true` and `forest_plan_passed=true`, `compliance-review-eval` `3/3`, and
  `compliance-gold-eval` `10/10`. Current Milestone 8 code excludes base-pack gold eval outputs
  from promotion readiness until generated applicability artifacts are present.
- The post-V1 applicability run for `v1-cg-ecid-compliance-review` validates cleanly with `373`
  candidate authorities, `34` applicable authorities, `339` not-applicable authorities, no
  unresolved/adjudication decisions, and `generated_rule_pack_ready=true`.
- The post-V1 promotion suite is implemented at `config/promotion_suite_v1.json`. A local run on
  2026-05-04 reported `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"package_fixture_missing": 2}`, and
  `open_expansion_slot_count=2`. This means the current East Crazy V1 evidence and post-V1
  applicability artifacts are promotable; broader readiness is blocked only when strict expansion
  requires additional real Region 1 EA package fixtures.

Previous full downstream promotion snapshot was verified locally on 2026-04-30 before the rule-pack
`0.4.0` baseline expansion and before the later 186-row and 190-row catalog updates.

- Active source set: `source-set-e364ea220cffd938`
- Base phase eval: passed, `8/8` phases reviewer-ready
- Compliance phase eval: passed, `9/9` phases reviewer-ready for
  `demo-compliance-matrix-authority-v03-ecid-2026-04-30`
- Catalog: `147` source rows, `131` unique raw artifacts
- Extraction: `147/147` selected sources extracted, validation passed
- Retrieval: `13,619` chunks indexed, validation passed, reviewer-ready
- Evidence graph: `36,578` nodes, `106,182` edges, validation passed, reviewer-ready
- Retrieval-to-graph binding mismatches: `0`
- Source claim graph: `35,348` claims, `8,479` entities, `90,153` nodes, `231,214`
  edges, validation passed, reviewer-ready
- Claim eval seed: passed, `2/2` cases
- Rule-claim binding: `92` links across `20/20` authority compliance rules, `0` explicit no-claim
  gaps, validation passed, reviewer-ready
- Rule-claim eval seed: passed, `20/20` authority cases
- Compliance coverage: `20/20` rules covered by matrix rows, source-claim links, source-claim
  terms, and compliance review eval cases
- EA review smoke: `review_validation.json` passed for `smoke-ea-review-v0-hardened`
- Compliance demo review: authority-first `compliance_validation.json`, `compliance_matrix.json`,
  and `compliance_matrix.pdf` passed for
  `demo-compliance-matrix-authority-v03-ecid-2026-04-30` under the pre-`0.4.0` 20-rule pack
- Compliance review eval seed: passed, `3/3` cases
- Compliance gold eval: passed, `10/10` adjudicated cases in the pre-applicability gate; base-pack
  reruns are now diagnostic and not `promotion_ready`
- Unit suite: `132` tests passed

Post-baseline-expansion verification on 2026-04-30:

- `config/compliance_rule_pack_nepa_ea_v0.json` validates with `26` declared baseline source records
  and `44` total rules.
- `tests/test_compliance_review.py` passes with `32` tests.
- `git diff --check` passed before commit `720d75c`.
- Superseded by the 2026-05-01 current-source-set refresh above, which closed the
  `forest_service_directives_portal` / `R1EA-028` source-claim link gap and promoted coverage/gold
  eval artifacts for rule-pack `0.4.0`.

The full downstream promotion verification set for the prior 147-row source set was:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src python -m compileall src
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --review-id demo-compliance-matrix-authority-v03-ecid-2026-04-30 \
  --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id demo-compliance-matrix-authority-v03-ecid-2026-04-30
```

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

Current parent batch path:

```text
source_library/runs/corpus-update-2026-05-01-cg-support-batches/
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

The reviewer catalog links every artifact-bearing workbook row to an artifact, including
duplicate-content rows. Scope-excluded rows remain in the catalog with `skipped_excluded` status and
no artifact link.

## Extraction, Retrieval, Review, And Graph Status

The raw source library does not store semantic chunks. A derived extraction layer is implemented
through `extract-build`; it reads the reviewer catalog, rehashes artifacts, and writes rebuildable
extracted text, chunk JSONL, and extraction diagnostics under
`source_library/derived/<source_set_id>/`.

The first retrieval layer is also implemented through `retrieval-build`. It indexes extracted
chunks into a local SQLite evidence index and supports deterministic text queries filtered by
document role, authority level, source record, review topic, citation label, and host.

The document evidence graph layer is implemented through `evidence-graph-build`. It turns extracted
chunks and retrieval metadata into graph artifacts for source documents, raw artifacts, extracted
text, sections, chunks, evidence spans, parsers, and review topics. It is a graph substrate for
auditable review; source-text legal claims are handled by the separate claim graph layer.

Source Claim Graph V0 is implemented through `claim-extract`. It extracts deterministic legal-style
claims from exact chunk text spans, links entities and authorities, validates offsets and retrieval
bindings, and writes claim graph artifacts under
`source_library/derived/<source_set_id>/claims/`.

EA Package Review V0 is implemented through `ea-review`. It extracts a local EA package, runs the
seed checklist, retrieves source-library evidence for each item, and writes package evidence,
source-library evidence, finding status, limitations, and validation artifacts.

Custer Gallatin Forest Plan Resolver V0 is implemented through `forest-plan-resolve` as the first
configured forest-plan profile. It extracts or reuses a local EA package, resolves whether the
package matches the selected profile, extracts ranger-district and project-location signals,
extracts geographic areas, management areas, and overlays from profile data, and binds resolved plan
context to profile-declared source-library records. The default Custer Gallatin profile requires the
complete plan-review bundle in the retrieval index: planning page, Land Management Plan, Record of
Decision, FEIS Volume 1, FEIS Volume 2, Biological Assessment, and Biological Opinion. Triggered
ROD, FEIS, designated-area/allocation, and ESA cues are routed to profile-declared supporting
records in addition to the primary LMP area/component evidence. Supporting routes are trigger-gated
and emit `trigger_evidence`, so broad EA section labels do not silently activate FEIS records and
uppercase acronym triggers do not match ordinary lowercase words. Generic project decision labels
such as `selected alternative`, `decision basis`, or `plan approval` do not activate the Custer
Gallatin ROD route unless the package explicitly references `Record of Decision` or `ROD`; generic
`plan consistency` labels do not activate FEIS routing unless an explicit FEIS, tiering, or
incorporation cue is present.

Forest Plan Component Evaluation V0 is implemented as a default `forest-plan-resolve` stage for
packages resolved to the selected forest-plan profile. It reads a source-set component inventory when
present, falls back to the seed inventory, validates component provenance and source-set alignment,
retrieves current plan evidence from the local retrieval index, searches package chunks for component
evidence terms, and writes
`forest_plan_component_findings.json`, `forest_plan_component_findings.md`, and
`forest_plan_reviewer_resolution_queue.json`. NFMA standard coverage V0 also writes
`forest_plan_component_inventory_coverage.json` and
`forest_plan_applicable_standard_coverage.json`; applicable standards must have plan-source evidence,
EA package evidence, and a resolved compliance status before component validation can pass. The seed
inventory
`config/forest_plan_component_inventory_seed.json` covers the first East Crazies-relevant Custer
Gallatin Crazy Mountains Backcountry Area components. Supported and partial findings require both
plan-source evidence and package evidence; gaps and stale source-set IDs become reviewer-resolution
items instead of legal conclusions.

Compliance Rule Pack + Matrix + Finding Graph V0.4 is implemented through `compliance-review`. It
identifies applicable statutory, regulatory, policy, state, executive-order, and forest-plan
authorities from `config/compliance_rule_pack_nepa_ea_v0.json`, evaluates the EA against each
applicable authority, reuses the `ea-review` package/retrieval gates, requires validated
rule-to-source-claim bindings, and writes compliance validation, a compliance review report, a
reviewer-facing compliance matrix, and a finding graph for rules, findings, source claims, source
evidence, package evidence, and package gaps.

Rule-pack `0.4.0` contains `44` rules. It declares `baseline_source_record_ids` for the 26
workbook rows where `Scope=Baseline`, and rule-pack validation enforces that each declared baseline
source record has a corresponding `applicability_mode=baseline` rule.

Applicability-First Review has a post-V1 schema contract and implemented slices for authority
universe snapshotting, package fact graph/context building, retrieval/graph tracing, deterministic
decisions, validation, and adjudication replay. `applicability-authority-universe` reads the current
catalog, base rule pack, forest-plan profiles, component inventory, source-claim artifacts, and
rule-claim links, then writes
`source_library/reviews/<review_id>/applicability/authority_universe_snapshot.json` with all
rule-template candidates and Forest Plan component candidates. Each candidate carries required
package fact types, positive and negative trigger groups, required source evidence, source-role
filters, package-section filters, retrieval contracts, graph-expansion contracts,
dependency/exception/supersession fields, and search coverage requirements for later
non-applicability proof. `applicability-context-build` reads the existing EA package cache and
writes `package_fact_graph.json`, `package_applicability_context.json`, and
`package_fact_graph_validation.json` with typed, span-bound package facts for project/action,
agency, NEPA level, geography, Forest Plan areas/overlays, resource topics, consultations, permits,
public involvement, alternatives, and decision/finding signals. It records negative or
out-of-scope location statements as negative-context facts instead of positive geography facts, and
records weakly worded or missing common fact types as graph uncertainty rather than resolving them
as package applicability decisions. `applicability-retrieve` reads the authority universe, package
fact graph, local retrieval index, and available graph/link artifacts, then writes
`applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`, and
`applicability_retrieval_graph_diagnostics.json` with replayable per-candidate query rows, fused RRF
result rows, bounded graph paths, and retrieval/graph diagnostics. Graph trace rows now explicitly
preserve authority-category hierarchy, source-claim/rule-claim-link bindings, supporting source
records, package facts, and Forest Plan component provenance when those artifacts are available.
`applicability-determine` reads those artifacts and writes `applicability_decisions.jsonl`,
`applicable_authorities.json`, `non_applicable_authorities.json`,
`search_coverage_certificates.json`, `applicability_provenance.json`, and
`applicability_report.md` with one deterministic decision row per authority candidate. Weak or
conflicting trigger evidence is recorded as `needs_adjudication`, and not-applicable decisions cite
search coverage certificates with required source-index hashes. Decision rows retain inspected
source-library evidence spans or declared authority-universe source evidence when source retrieval
records coverage without selecting a source chunk. Explicit negative Forest Plan scope evidence,
such as package statements that a component area is not part of the project area, overrides broad
component-text positives instead of producing contradictory ready decisions. Provenance includes
package manifest/chunk entities.
`applicability-validate` now writes `applicability_validation.json` and fails closed on missing or
duplicated candidate decisions, unresolved or `needs_adjudication` decisions, stale artifacts,
missing retrieval/graph traceability, non-applicable decisions without coverage/adjudication, and
provenance gaps. `applicability-adjudication-template`, `applicability-adjudication-eval`, and
`applicability-adjudication-apply` provide a machine-readable replay path for resolving open
decisions into `human_adjudication` bases before validation can pass.
`applicability-generate-rule-pack` now writes and validates generated compliance rule packs from the
validated applicable-authority partition only, and reviewer-ready `compliance-review` is gated on
that generated pack plus current applicability validation, generated-pack validation,
non-applicable-authority, search-coverage, package, source-set, and provenance artifacts. The base
rule pack remains available only through an explicit non-reviewer-ready diagnostic path.
`applicability-eval` and `applicability-gold-eval` now score applicability decision quality before
compliance quality is promoted.

Compliance Review Eval V0 is implemented through `compliance-review-eval`. The current seed fixtures
target rule pack `0.4.0` and run deterministic package fixtures through the real compliance-review
path. The gate scores expected rule statuses, claim types, evidence presence, source-claim links,
expected source record IDs, expected source document roles, citation coverage, unsupported finding
IDs, failure taxonomy, compact reproduction paths, and finding-graph coverage.

Compliance Gold Eval V0.4 is implemented through `compliance-gold-eval`. It validates a structured
adjudication file, requires positive, mixed, and negative package profiles, runs ten adjudicated
package fixtures through the real compliance-review eval path, and emits `promotion_ready` only
when the rule pack is a reviewer-ready generated applicability rule pack and both adjudication
checks and generated findings pass.

Compliance Coverage V0 is implemented through `compliance-coverage`. It validates the coverage
matrix, rule-pack identity, eval-case coverage, current source-claim links, source-claim terms, and
source-record alignment for each compliance rule.

Current state:

- Raw source documents are captured and cataloged for the 190-row workbook contract, except the
  intentionally scope-excluded `R1EA-160` project page.
- Source metadata is normalized into JSONL and SQLite.
- Derived extraction builds text and chunks from the catalog. The newest source set now has a
  full-source-set extraction layer, reviewer-ready retrieval index, evidence graph, source-claim
  graph, rule-claim bindings, compliance coverage, compliance-review eval, compliance-gold eval, and
  phase-eval promotion evidence for `source-set-ba8d0feae79501b8`.
- The extraction accuracy audit verifies text hashes, raw artifact hashes, chunk offset fidelity,
  gap-free chunk coverage, eCFR section/subpart scoping, markup cleanup, and PDF token coverage.
- Retrieval builds and queries a provenance-bearing local evidence index.
- The document evidence graph builds source, artifact, extracted-text, section, chunk, evidence-span,
  parser, and review-topic nodes with health metrics.
- The source claim graph builds claim, entity, authority, and claim-evidence-span nodes with exact
  chunk and source-text offsets.
- The rule-claim binding layer links compliance rules to validated source claims and records explicit
  no-claim gaps when no validated source claim matches a rule.
- Phase eval reports catalog, extraction, retrieval, evidence-graph, claim-extraction,
  rule-claim-binding, optional compliance-coverage, optional compliance-gold-eval, and review-bound
  applicability plus compliance-review readiness separately when those artifacts exist or are
  requested.
- EA review runs deterministic checklist execution against a local package and emits JSON/Markdown
  reports plus `review_validation.json`.
- Custer Gallatin forest-plan context resolution runs against a local EA package and emits
  `forest_plan_context.json`, `forest_plan_context_validation.json`, and
  `forest_plan_context_summary.json`. The current Custer Gallatin path requires all seven
  Custer Gallatin plan/supporting records in retrieval, resolves management areas from the EA
  package, and adds `supporting_plan_evidence` routes for ROD, FEIS Volumes 1 and 2, Biological
  Assessment, and Biological Opinion triggers.
- Forest-plan component evaluation writes component findings, selected-inventory coverage,
  applicable-standard coverage, and a reviewer-resolution queue from a versioned inventory for
  packages resolved to the selected forest-plan profile. The current source-set inventory for the
  2022 Custer Gallatin Land Management Plan is generated from extracted chunks and has passing build
  coverage; the seed inventory remains only a fallback/test fixture.
- Compliance review runs a versioned rule pack and emits `compliance_validation.json`,
  `compliance_review.json`, `compliance_matrix.json`, `compliance_matrix.md`,
  `compliance_matrix.pdf`,
  `finding_graph_nodes.jsonl`, and `finding_graph_edges.jsonl`.
- Compliance review now invokes the forest-plan resolver against the same package cache. For Custer
  Gallatin packages, `forest_plan_component_gate_reviewer_ready` must pass, the matrix summary links
  to `forest_plan_review`, and the finding graph includes forest-plan review/component-evaluation
  nodes.
- EA review and compliance review can rerun checklist/rule evaluation against existing
  `package_manifest.jsonl` and `package_chunks.jsonl` with `--reuse-package-cache`; use this for
  rule-pack refreshes when the EA package was already extracted.
- Compliance review eval runs deterministic package fixtures and emits
  `compliance_review_eval_results.json` with failure taxonomy and reproduction paths.
- Compliance gold eval runs adjudicated positive/mixed/negative package fixtures and emits
  `compliance_gold_eval_results.json`; the current gate has ten adjudicated cases.
- Compliance coverage runs the coverage matrix against the current rule pack, rule-claim links,
  source-claim terms, and compliance review eval cases.
- V1 real-EA review eval is implemented through `v1-ea-eval`. It reads an existing East Crazy
  Inspiration Divide compliance review directory and scores required EA section detection,
  rule-to-section matches, source-record/document-role correctness, all 26 baseline source records,
  conditional applicability, applicable conditional source/section alignment, missing conditional
  expectations, Custer Gallatin forest-plan source/component/standard expectations, citation
  requirements, and reviewer-resolution queue size against `config/v1_ecid_real_ea_eval.json`.
- The first real East Crazy Inspiration Divide V1 compliance review run exists locally at
  `source_library/reviews/v1-cg-ecid-compliance-review/`. It extracted `43` package files into
  `1,265` chunks, produced compliance review/matrix/PDF/graph artifacts, and passed
  the upstream source-set phases. After the section-aware forest-plan retrieval pass, the package
  resolves to `scope_status: custer_gallatin`; forest-plan context validation passes with
  `2` geographic areas, `1` management area, `2` overlays, and `5` supporting plan evidence
  records. The retained context is Bridger/Bangtail/Crazy, Madison/Henrys Lake/Gallatin, Crazy
  Mountains BCA, Inventoried Roadless Area, and Recommended Wilderness Area. Forest-plan component
  artifacts are produced from the generated source-set inventory with `329` component findings,
  `58` standards, `12` applicable standards, and `12` applied standards. The stricter
  applicable-standard coverage gate now passes with `all_applicable_standards_applied=true`; the
  prior `AB-STD-RCREA-01` gap is supported by recreation/access package evidence for the proposed
  nonmotorized Sweet Trunk Trail. The non-standard reviewer-resolution queue is now closed:
  `forest_plan_component_findings.json` reports `79` supported findings, `250` not applicable
  findings, `0` gaps, and `0` reviewer-resolution items. The resolver now reads split Plan
  Consistency Table rows across adjacent package chunks, handles duplicated/split component-key
  cells and plain-text rows, and suppresses cross-reference pseudo-components that do not have a
  numeric component number.
  Component-level forest-plan eval runs against `config/forest_plan_component_eval_seed.json` and
  passes all `35` adjudicated cases. The eval now covers every one of the `12` applicable standards,
  `11` representative non-standard applicable components across desired conditions, goals,
  guidelines, objectives, and suitability, and `12` hard-negative not-applicable cases. Case coverage
  requirements pass, and component applicability precision/recall, applicable-standard recall,
  package-section match rate, plan-source citation correctness, package-evidence citation
  correctness, resolved compliance-status rate, compliance-status match rate, reviewer-resolution
  state match rate, false-applicable component rate, and reviewer-resolution closure rate all meet
  their strict thresholds. Non-standard component package evidence now uses strict section-family
  binding: outside explicit Plan Consistency Table determinations, desired conditions, goals,
  guidelines, objectives, and suitability components require a matching EA package section family
  plus substantive component terms. The component validation gate now fails supported package
  evidence with missing or mismatched section bindings unless the evidence is an explicit Plan
  Consistency Table determination. Current regenerated findings have `79` supported components,
  `0` gaps, zero supported package evidence entries with mismatched section binding, and `51`
  affirmative Plan Consistency Table component-row bindings marked explicitly. The prior completed
  non-standard component
  adjudication artifact classified the old `21` items as system misses; those adjudications are
  superseded by evidence-backed resolver fixes, and phase eval now rejects stale component
  adjudication evals whose queue count differs from the current queue. `phase-eval --review-id
  v1-cg-ecid-compliance-review` now reports `10/10` passing phases and `reviewer_ready=true`.
  The stricter V1 eval now passes all forest-plan expectations, including zero open standard
  reviewer-resolution items and a capped `0` total forest-plan reviewer-resolution items. It also
  passes the broader EA source/section gate after CE/FANEC conditional-applicability, baseline
  section-attribution, and programmatic-tiering section-routing repairs. `v1-ea-eval` now reports
  `passed=true`, `broader_ea_passed=true`, `forest_plan_passed=true`, empty failure-category
  counts, `failed_rule_ids=[]`, `conditional_false_positive=0`, `conditional_false_negative=0`,
  and `rule_section_match_rate=1.0`. The V1 eval contract now carries explicit policy coverage for
  `14` adjudication-pending conditional rules, so those rows are visible accepted V1 risk rather
  than a hidden pass condition.
- Forest-plan component adjudication tooling is implemented through
  `forest-plan-component-adjudication-template` and `forest-plan-component-adjudication-eval`. The
  template command exports one adjudication item for each open component reviewer-resolution queue
  item, with current status expectations and reviewer-fillable dispositions, and writes a companion
  Markdown worklist for human triage. The eval command fails closed until every current queue item
  has explicit adjudication metadata and a resolved disposition such as `true_ea_omission`,
  `retrieval_miss`, `package_section_chunking_miss`, `component_inventory_overreach`,
  `applicability_false_positive`, or `evidence_linking_miss`.
  Earlier runs against `v1-cg-ecid-compliance-review` produced `21` pending non-standard items:
  `8` desired conditions, `2` goals, `7` guidelines, `3` objectives, and `1` suitability
  component. Those items were adjudicated as system misses, then closed by the resolver and
  component-inventory fixes described above. The current generated queue has `0` items, so no
  component adjudication phase is required for the latest review artifacts. When an adjudication
  eval artifact is present in a review directory, `phase-eval --review-id` includes it as a
  `forest_plan_component_adjudication` phase and now checks it against the current queue count so
  pending, stale, or mismatched adjudication work blocks reviewer readiness at the phase gate.
- The V1 real-EA eval now records explicit diagnostic lanes in `v1_ea_eval_results.json`. The
  current East Crazies package passes the lane split with `broader_ea_passed=true`,
  `forest_plan_passed=true`, `forest_plan_component_adjudication_required=false`, and no broader-EA
  or forest-plan failure categories. `nepa_4336b_programmatic_tiering` remains visible as an
  adjudication-pending conditional rule, but its actual package sections are `alternatives` and
  `environmental_consequences`, its actual source record is `R1EA-005`, and its actual source
  document role is `law`.
- A seed retrieval eval file exists at `config/retrieval_eval_seed.json`.
- A seed claim extraction eval file exists at `config/claim_eval_seed.json`.
- A seed rule-claim binding eval file exists at `config/rule_claim_link_eval_seed.json`.
- A seed compliance review eval file exists at `config/compliance_review_eval_seed.json`.
- A seed compliance gold eval file exists at `config/compliance_gold_eval_v0.json`.
- A seed compliance coverage matrix exists at
  `config/compliance_rule_pack_coverage_nepa_ea_v0.json`.
- A seed forest-plan component eval file exists at
  `config/forest_plan_component_eval_seed.json`.
- A V1 real-EA review eval contract exists at `config/v1_ecid_real_ea_eval.json`.
- A post-V1 promotion-suite manifest exists at `config/promotion_suite_v1.json`.
- A seed EA review checklist exists at `config/ea_review_checklist_seed.json`.
- A seed NEPA EA compliance rule pack exists at `config/compliance_rule_pack_nepa_ea_v0.json`.
- Catalog graph seed files exist for source-level relationships.
- No embeddings exist yet.
- No model-generated compliance narrative is trusted without deterministic package and source
  evidence.
- Page/section offsets are available only where the selected parser can infer them; all chunks carry
  extracted-text character offsets.

The catalog graph seed is a source metadata graph. It includes relationships such as:

- source to artifact
- source to authority
- source to review topic
- source to applicability

The document evidence graph is the implemented content graph. It includes document sections, chunks,
evidence spans, parser provenance, and review-topic edges. It does not include table structure
recovery, embeddings, or vector chunks.

The source claim graph is the implemented claim/entity graph. It includes extracted source-text
claims, entities, authority nodes, claim evidence spans, and edges back to chunk/source provenance.
It is deterministic pattern extraction with strict validation, not a model-generated interpretation
of compliance meaning.

The rule-claim binding layer is the implemented bridge from compliance rules to source claims. It
uses rule-pack queries and source filters to rank validated source claims, writes exact provenance
for each link, and treats missing rule support as explicit no-claim gaps rather than silent evidence.

The finding graph is the implemented compliance-review graph. It includes rule packs, compliance
rules, findings, source-claim references, evidence-span references, and package-gap nodes. It does
not replace human reviewer adjudication.

## Accuracy Guarantees

The current downloader and catalog guarantee capture integrity, not legal interpretation.

Validated downloader/catalog guarantees for the current 190-row corpus:

- Every generated-corpus source row has one final captured status.
- The combined batch ledger covers all `190` generated-corpus workbook rows.
- The repair queue is empty after URL repairs.
- Every artifact-bearing successful row links to an artifact.
- The one scope-excluded row, `R1EA-160`, has no artifact or fetch evidence.
- Every artifact path exists.
- Artifact byte sizes match manifest metadata.
- Artifact SHA256 values recompute from saved bytes.
- Duplicate-content rows link to canonical artifacts.
- URL overrides preserve the workbook `original_url` and record the `effective_url`.
- Override metadata includes `override_url` and `override_reason`.
- The reviewer catalog matches batch manifests.
- SQLite source-artifact links match the JSONL catalog.
- The prior 38-source land-exchange delta extraction for `source-set-572d6384a59a7b2a` matched raw
  artifact hashes and manifest text hashes, but it is superseded by the current reuse-first
  extraction assembly for `source-set-ba8d0feae79501b8`.
- Chunk text matches extracted-text offset slices.
- Retrieval chunks validate against source-set IDs, content hashes, offsets, required provenance, and
  catalog linkage.
- Evidence graph chunks validate against the retrieval index before graph artifacts are marked
  reviewer-ready.
- EA review `pass` findings require both package evidence and source-library evidence.
- EA review `gap` findings require source-library evidence and explicitly mean package evidence was
  not found.
- Package evidence search requires configured package-term hits; single-word terms match whole
  tokens and phrase terms match contiguous text.
- EA review validation rejects unsupported compliance claims.
- Compliance review validates the rule pack, requires every authority rule to carry authority and
  applicability metadata, requires all declared baseline source records to be covered, requires
  every rule to be evaluated, requires all declared baseline source records to appear in findings,
  requires source citations for claim-bearing findings, and validates finding graph node/edge
  integrity.
- Rule-pack validation rejects unsafe rule-pack or rule IDs, unsupported source-filter keys, and
  empty source-filter values.
- Compliance review eval rejects unsafe case IDs, ambiguous package fixtures, unsupported filters,
  unsupported expected statuses, unsupported expected claim types, non-boolean evidence
  expectations, partial rule-pack coverage, unknown rule IDs, and status counts that do not match
  per-rule expectations.
- Compliance coverage rejects malformed matrix rows, missing matrix/eval/link coverage, and
  source-record or source-claim-term mismatches against current rule-claim links.
- Compliance gold eval rejects missing adjudication metadata, missing required profiles, duplicate
  case IDs, unsafe or escaping package fixture paths, partial rule-pack expectations, status count
  mismatches, and generated finding mismatches. Missing package fixture files are recorded as failed
  gold eval results instead of escaping without a machine-readable artifact.
- Phase eval rejects stale compliance coverage artifacts when the coverage source set or rule pack
  does not match the evaluated source set and rule-claim binding.
- Phase eval rejects stale compliance review artifacts when the review source set does not match the
  evaluated source set.

Full extraction, retrieval, evidence-graph, source-claim, rule-claim, coverage, compliance-review
eval, compliance-gold eval, and phase-eval guarantees now exist for the current 190-row source set
`source-set-ba8d0feae79501b8`.

Boundaries:

- A successful download means the source bytes were captured and validated.
- It does not prove that the source is legally current beyond the workbook metadata and retrieval evidence.
- It proves the current generated extraction artifacts pass deterministic extraction validation and
  extraction accuracy audit checks for text hashes, raw artifact hashes, chunk offsets, chunk
  coverage, scoped XML, markup cleanup, and sampled PDF token coverage.
- It proves the current retrieval, evidence graph, source-claim graph, rule-claim binding,
  compliance coverage, compliance review eval, compliance gold eval, and phase eval artifacts passed
  deterministic provenance, coverage, freshness, and binding gates.
- It proves the current EA review V0 cannot mark a finding as `pass` without both package and
  source-library evidence.
- It proves the current compliance review V0 cannot produce claim-bearing findings without
  source-library citations.
- It proves a Custer Gallatin-scoped compliance review cannot be reviewer-ready when forest-plan
  component evaluation is absent, stale, or not reviewer-ready.
- It proves component-level forest-plan accuracy can be scored against adjudicated cases for
  applicability, standard recall, package-section binding, plan-source citations, package-evidence
  citations, resolved compliance status, and reviewer-resolution closure before running additional
  real EA packages. The component eval checks review/source-set identity across every consumed
  review artifact, enforces all-applicable-standard and minimum representative-case coverage, and
  treats extra citations as citation mismatches, not harmless surplus evidence.
- It proves the profile-driven forest-plan resolver can resolve the real East Crazy Inspiration
  Divide package to Custer Gallatin scope without treating incidental references to other forests as
  ambiguity, while still failing closed when component coverage is not reviewer-ready.
- It proves forest-plan component reviewer-resolution items can be exported into a stable
  adjudication contract and evaluated for queue coverage, completion, disposition counts, and status
  expectation drift before those reviewer decisions are used as improvement data.
- It proves the current final compliance-review eval seed passes deterministic all-pass, mixed
  pass/gap, and all-gap package fixtures.
- It proves the current seed compliance-gold-eval promotion gate passes one positive, one mixed, and
  one negative adjudicated fixture profile.
- It defines a V1 real-EA eval contract for the East Crazy Inspiration Divide run, but that contract
  does not prove real-world EA review quality until `v1-ea-eval` passes against the actual review
  artifacts and the remaining component/conditional/section failures are adjudicated.
- It does not prove semantic legal interpretation of the extracted text.
- It does not prove that future web versions will remain unchanged.

## Reviewer Engine Read Path

The EA review engine should not scan `artifacts/raw/` directly as its source of truth. It should
read through the catalog, extraction outputs, and retrieval index in order.

Recommended read path:

1. Read `source_library/catalog/source_set_manifest.json`.
2. Confirm the intended `source_set_id`, `download_batch_run_id`, source counts, artifact counts, and validation status.
3. Query `source_library/catalog/review_sources.sqlite` or read `source_library/catalog/source_catalog.jsonl`.
4. Select source rows by `document_role`, `authority_level`, `review_topics`, `applies_to`, `host`, or `expected_parser`.
5. For each source row, open `artifact_path`.
6. Recompute SHA256 and byte size before parsing.
7. Parse by `expected_parser` and `content_type`.
8. Emit downstream chunks with immutable provenance fields.
9. Build `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`.
10. Retrieve evidence spans through `retrieval-query` or the retrieval module before generating any
    compliance answer.
11. For package review, run `ea-review` so each checklist item records both package evidence and
    source-library evidence, or marks the item as a gap/uncertain without unsupported claims.

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

## EA Package Review V0

The current package-review milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

The command writes `source_library/reviews/<review_id>/review_report.json` and
`review_report.md`, `review_validation.json`, plus package extraction artifacts under
`source_library/reviews/<review_id>/package/`.
Findings use the statuses `pass`, `gap`, `uncertain`, and `not_applicable`.

A `gap` means the source library returned supporting review authority but matching package evidence
was not found. An `uncertain` finding does not make a compliance claim.
The command fails fast if the source-library retrieval index is not reviewer-ready, and rerunning a
fixed review ID replaces prior package artifacts before writing the new report.
When a package was already extracted for the same review ID, pass `--reuse-package-cache` to preserve
and reuse `package/package_manifest.jsonl` and `package/package_chunks.jsonl` instead of
re-extracting package PDFs.

`review_validation.json` is the gate-facing artifact. It checks source retrieval readiness, package
extraction, package chunk creation, valid finding statuses, dual evidence for `pass` findings, source
evidence for `gap` findings, and absence of unsupported compliance claims.

## Custer Gallatin Forest Plan Resolver V0

The first forest-plan-specific review milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

The command writes `source_library/reviews/<review_id>/forest_plan_context.json`,
`forest_plan_context_validation.json`, and `forest_plan_context_summary.json`, plus package
extraction artifacts under `source_library/reviews/<review_id>/package/`.

The default resolver profile is Custer Gallatin and preserves the V0 output contract. It returns
`scope_status=custer_gallatin`, `not_custer_gallatin`, or `ambiguous`; ambiguous `Gallatin`-only
packages are not guessed. The command now accepts `--forest-unit-id` and
`--forest-plan-profiles-path` so profile data, not Python constants, defines forest names, required
source records, area terms, overlays, and supporting evidence routes. Other configured forest
profiles are still blocking evidence when mentioned as operative project scope, but incidental
background, reference, bibliography, or coordination mentions do not force an otherwise
Custer-Gallatin package to `ambiguous`. Negative package-location text such as `not part of the
project area` is also filtered before area resolution. For Custer Gallatin packages it extracts:

- forest unit and ranger district signals
- project location snippets
- Custer Gallatin geographic areas
- Custer Gallatin management areas
- overlays such as inventoried roadless areas
- package evidence and source-library LMP evidence
- triggered supporting plan evidence from the Custer Gallatin ROD, FEIS Volumes 1 and 2,
  Biological Assessment, and Biological Opinion
- trigger evidence showing why each supporting plan record was applied
- required source-record readiness for all Custer Gallatin profile-required plan/supporting records
- unresolved mentions that need human reviewer resolution

The East Crazies profile-driven fixture proves the minimum V1 forest-plan support slice: Custer
Gallatin scope, Bridger/Bangtail/Crazy Mountains Geographic Area, Crazy Mountains Backcountry Area,
all seven required Custer Gallatin source records, FEIS/BA/BO supporting routes from explicit
package evidence, and no Custer Gallatin ROD routing from generic project decision labels.

Custer Gallatin packages are reviewer-ready only when validation passes and at least one geographic
area, management area, or overlay is resolved. They also require every Custer Gallatin
profile-required plan/supporting record to be indexed. Packages that appear Custer Gallatin scoped
but lack a resolved plan area, or trigger a supporting record without source evidence, set
`needs_reviewer_resolution` instead of silently passing.

Forest-plan improvement work uses sequence discipline: each implemented sequence updates repo docs,
passes focused verification, and is committed before the next sequence starts.

## Compliance Rule Pack And Finding Graph V0

The rule-pack milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

For rule-pack-only refreshes against an existing package extraction, keep the same review ID and add
`--reuse-package-cache`.

The command writes these artifacts beside the base EA review artifacts:

- `source_library/reviews/<review_id>/compliance_validation.json`
- `source_library/reviews/<review_id>/compliance_review.json`
- `source_library/reviews/<review_id>/compliance_matrix.json`
- `source_library/reviews/<review_id>/compliance_matrix.md`
- `source_library/reviews/<review_id>/compliance_matrix.pdf`
- `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/finding_graph_edges.jsonl`

The post-V1 applicability-first artifact contract reserves
`source_library/reviews/<review_id>/applicability/` for:

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

Those artifacts are the target source of truth for applicability and non-applicability. The
non-applicable authority list must not be buried only as compliance matrix rows. A not-applicable
decision must carry negative evidence, trigger-miss rationale, search coverage, or adjudication, and
a reviewer-ready compliance review must eventually consume a generated rule pack tied to a passing
applicability validation hash plus the package fact graph, retrieval trace, graph trace, search
coverage, and provenance hashes. This is a documented contract at the current milestone, not yet an
implemented command sequence.

The rule pack is data, not hidden code. Each rule includes identity, title, question, requirement,
severity, authority category, authority source record, applicability mode, package query and terms,
optional conditional applicability terms, optional grouped conditional applicability terms, source
query, source filters, and an evidence expectation.
The authority document role is derived from explicit rule metadata when present, otherwise from
`source_filters.document_role`.
Rule-pack `0.4.0` also declares `baseline_source_record_ids`; these are the 26
`Ingest_Checklist` rows where `Scope=Baseline`.

The finding graph contains:

- `ComplianceRulePack`
- `ComplianceReview`
- `ComplianceRule`
- `ComplianceFinding`
- `SourceLibraryEvidence`
- `PackageEvidence`
- `PackageEvidenceGap`

The compliance matrix is the first reviewer-facing matrix artifact. Each row records the authority,
applicability mode and status, rule status, requirement, applicability basis, package evidence
citation, source evidence citation, source-claim IDs, applied source record IDs, applied source
document roles, citation-gate status, limitations, and failure category when an applicable finding is
not a supported pass.

`compliance_validation.json` checks rule-pack validity, base EA review validation, all-rules
coverage, valid finding statuses, dual evidence for `pass`, source evidence for `gap`, source
citations for claim-bearing findings, unsupported-claim absence, finding graph evidence-edge
coverage, and finding graph integrity.

Rule-pack IDs, rule IDs, and fixed review IDs are constrained to letters, numbers, dots,
underscores, and hyphens so review outputs cannot escape the intended review directory. Rule
`source_filters` must use supported retrieval filter keys; typoed keys fail validation instead of
silently widening retrieval.

## Derived Extraction Layer

The extraction layer builds a derived text/chunk index without modifying raw artifacts.
PDF extraction uses Docling first; born-digital PDFs that exceed the Docling timeout can fall back
to `pypdf_text_fallback`, with parser name/version preserved in manifests and chunks and fallback
metadata preserved in the extraction manifest.

Derived layout:

```text
source_library/
  derived/
    <source_set_id>/
      extracted_text/
      docling_json/
      chunks/
        chunks.jsonl
      diagnostics/
        extraction_manifest.jsonl
        extraction_validation.json
        extraction_accuracy_audit.json
        summary.json
```

Derived outputs:

- extracted text per artifact
- Docling JSON when Docling is used by the parser
- HTML/XML section extraction
- chunk JSONL with stable chunk IDs
- chunk-level SHA256 or content hash
- parser diagnostics
- extraction validation report
- chunk-to-source and chunk-to-artifact links

Derived data should always be rebuildable from raw artifacts and the reviewer catalog.

## Evidence Retrieval Layer

Retrieval layout:

```text
source_library/
  derived/
    <source_set_id>/
      retrieval/
        evidence_index.sqlite
        retrieval_manifest.json
        retrieval_validation.json
        summary.json
        retrieval_eval_results.json
```

The retrieval layer is intentionally lexical and auditable for v1. It stores the source chunk text
and the provenance required for a reviewer to verify the citation back to raw artifacts and extracted
text offsets.

Retrieval validation checks:

- extraction validation passed unless explicitly overridden
- extraction scope is complete unless `--allow-partial-extraction` is passed for diagnostics
- chunks JSONL exists and contains chunks
- catalog SQLite exists
- chunk source-set IDs match the target source set
- chunk IDs are unique
- indexed source IDs match extracted source IDs in `extraction_manifest.jsonl`
- chunk hashes match the stored text
- chunk offsets are valid
- linked artifact and extracted-text paths still exist
- required citation, artifact, URL, parser, and offset fields are present

`retrieval-build` records `reviewer_ready`. This is true only when the index validates and the
extraction summary shows complete catalog coverage for all required non-excluded sources.
Scope-excluded rows count toward selected catalog coverage but do not require chunks. A filtered
one-document slice can still be indexed with `--allow-partial-extraction`, but it remains a
diagnostic index, not a reviewer-ready corpus.

## Document Evidence Graph Layer

Evidence graph layout:

```text
source_library/
  derived/
    <source_set_id>/
      evidence_graph/
        document_graph_nodes.jsonl
        document_graph_edges.jsonl
        evidence_graph.sqlite
        evidence_graph_validation.json
        summary.json
        phase_eval_results.json
```

The evidence graph contains these node types:

- `SourceSet`
- `SourceDocument`
- `RawArtifact`
- `ExtractedText`
- `DocumentSection`
- `DocumentChunk`
- `EvidenceSpan`
- `Parser`
- `ReviewTopic`

Every `EvidenceSpan` traces to a chunk, source document, raw artifact, parser version, content
hash, citation label, URL provenance, and extracted-text offsets. The graph build also reopens the
retrieval SQLite index and requires chunk IDs, source-set IDs, provenance fields, offsets, content
hashes, text, and review topics to match before graph artifacts are persisted. The graph records
health metrics: connected components, isolated nodes, dangling edges, evidence coverage, topic
coverage, source-artifact coverage, retrieval binding mismatches, and chunk hash mismatches.

`phase-eval` keeps readiness checks phase-aligned:

- catalog capture
- extraction
- retrieval
- evidence graph
- claim extraction
- rule-claim binding
- authority universe when `--review-id` or `--review-dir` is supplied
- package fact graph when `--review-id` or `--review-dir` is supplied
- applicability retrieval trace when `--review-id` or `--review-dir` is supplied
- applicability graph trace when `--review-id` or `--review-dir` is supplied
- applicability determination when `--review-id` or `--review-dir` is supplied
- applicability validation when `--review-id` or `--review-dir` is supplied
- generated rule pack when `--review-id` or `--review-dir` is supplied
- optional compliance coverage when `compliance_coverage_results.json` exists beside the
  rule-claim outputs
- optional compliance gold eval when `compliance_gold_eval_results.json` exists under
  `source_library/reviews/compliance_gold_eval/`
- optional compliance review when `--review-id` or `--review-dir` is passed
- optional forest-plan component eval when the review directory contains
  `forest_plan_component_eval_results.json`
- optional forest-plan component adjudication when the review directory contains
  `forest_plan_component_adjudication_eval.json` or a completed
  `forest_plan_component_adjudication.json`

When a compliance coverage phase is included, `phase-eval` requires the matrix gate to pass, the
rule pack to match, and the coverage source set to match the evaluated source set. When a gold eval
phase is included, `phase-eval` requires the gold eval to pass, the rule pack to match, and the
gold eval source set to match the evaluated source set; stale or failed gold artifacts report
specific failed checks such as source-set or rule-pack mismatch. For review-bound generated rule
packs, a passing base-pack gold eval can satisfy the phase when the generated pack declares the same
base identity; the phase records this as `rule_pack_match_mode=generated_base`. When review-bound applicability
phases are included, `phase-eval` requires a current authority universe, package fact graph and
validation, retrieval and graph trace diagnostics, complete candidate decisions, complete
applicable/non-applicable partitions, search coverage certificates for non-applicable authorities,
a passing `applicability_validation.json`, and a generated rule pack whose rules exactly match the
applicable-authority partition. It also rechecks file-backed applicability-validation hashes for
decision, partition, retrieval/graph trace, search-coverage, and provenance artifacts. When a
compliance review phase is included, `phase-eval` requires
the review report to exist, validation to pass, the review ID to match when supplied, and the review
source set to match the evaluated source set. It also requires the compliance matrix artifact to
exist and match the review's schema version, review ID, source set, rule pack, row count, and status
counts. When a forest-plan component eval phase is included,
`phase-eval` requires the component eval result schema version to match, pass, match the evaluated
source set, and match the supplied review ID when one is provided. The phase reports case counts,
component metrics, failed checks, and failure-category counts. When a forest-plan component
adjudication phase is included,
`phase-eval` requires the adjudication eval to exist, pass, match the evaluated source set, and match
the supplied review ID when one is provided. The phase reports queue count, resolved and pending
adjudication counts, real EA omission and system-miss counts/rates, completion rate, expectation
match rate, disposition counts, adjudication-outcome counts, and failure-category counts.

## Alignment And Next Milestone

The current implementation remains aligned with the v1 reviewer-engine goal: accurate, auditable,
verifiable compliance review against a local knowledge base. Domain knowledge lives in versioned
data artifacts such as workbook rows, review topics, eval fixtures, rule packs, and the coverage
matrix. Runtime code performs general capture, extraction, retrieval, graph construction, rule
binding, coverage validation, and phase evaluation.

The Authority-First Compliance Matrix V0.4 milestone is implemented for the current local source-set
promotion gate. The active rule pack contains 44 authority rows and explicitly requires all 26
workbook `Scope=Baseline` source records in every EA review, with additional conditional rules for
triggered authorities. The refreshed coverage and gold gates contain ten adjudicated realistic
package profiles, expected source rows, expected source document classes, per-case failure taxonomy,
compact reproduction paths, and generated compliance matrices for the `0.4.0`/44-rule pack.

The current system has a complete 190-row downloader/catalog corpus that includes the four missed
Custer Gallatin FEIS and ESA-supporting plan documents. Full-source-set reuse-first extraction has
now been assembled for `source-set-ba8d0feae79501b8`: the current manifest has `189` extracted rows,
`1` scope-excluded row, `0` failures, and `18,822` chunks. The assembly reused `181` validated prior
extractions and `7` already-current Custer Gallatin slice records, then parsed
`R1PLAN-dakota-prairie-grasslands-02` as the only fresh extraction. Retrieval, evidence graph,
source claims, rule-claim bindings, compliance coverage, compliance-review eval, compliance-gold
eval, and phase eval have also been rebuilt and are reviewer-ready for the full current source set.
The Custer Gallatin LMP component inventory has also been generated for the current source set with
`329` components and `58` standards, and its build coverage passes with no missing or duplicate
component/standard IDs. Build coverage also records `2` suppressed component-like labels with
nonnumeric number tokens as inventory-quality issues instead of allowing rough IDs such as
`FW-GDL-VEGNF-See` into the inventory.
The prior 147-row downstream corpus remains useful for historical comparison only and should not be
treated as current promotion evidence for the expanded workbook.

The V1 CE/FANEC conditional-applicability milestone is implemented: grouped positive trigger
semantics and token-boundary matching for short acronyms now keep
`nepa_4336c_ce_adoption_screen`, `usda_nepa_ce_fanec_7cfr_1b3`, and
`usda_nepa_subcomponent_ce_7cfr_1b4` not applicable for the East Crazies package unless package
evidence shows an adopted CE, CE/FANEC screen, categorical-exclusion path, USDA CE screening, or
extraordinary-circumstances review. The milestone also carries explicit
`does_not_apply_if_package_terms` guards so negated same-chunk phrases such as a categorical
exclusion path not being used remain non-applicable evidence instead of positive CE triggers. The
live V1 eval now reports `conditional_false_positive=0` and `conditional_false_negative=0`.

The V1 baseline section-attribution milestone is implemented for `nepa_statute_chapter_55`: package
evidence routing now selects the EA purpose-and-need environmental-assessment span, and the live V1
eval reports `rule_source_section_expectations_met=true`, `rule_section_match_rate=1.0`,
`baseline_source_record_match_rate=1.0`, `baseline_document_role_match_rate=1.0`, and
`citation_requirement_match_rate=1.0`.

The V1 programmatic-tiering section-routing milestone is implemented: `nepa_4336b_programmatic_tiering`
now declares package section term groups for alternatives and environmental consequences, and
package evidence ranking uses those rule-declared groups as a context preference after the normal
tiering evidence match succeeds. The rule-pack validator and schema docs now cover these optional
section-preference fields so malformed `package_section_terms` or `package_section_term_groups`
fail validation instead of silently changing review behavior. The live V1 eval reports actual
package sections `alternatives` and `environmental_consequences`, actual source record `R1EA-005`,
actual document role `law`, `adjudication_pending=true`, and no `rule_section_mismatch`.

The V1 conditional-adjudication milestone is implemented. Each of the `18`
`conditional_source_expectations` in `config/v1_ecid_real_ea_eval.json` now has a
classification rationale, and the contract declares
`conditional_adjudication_policy.mode=accepted_pending_v1` with `accepted_pending_count=14`.
`v1-ea-eval` now emits a `conditional_adjudication` summary and full pending-results queue, fails
if accepted pending rule IDs/counts drift from the actual `adjudicate` rows, and keeps
source/section alignment enforced for actual applicable pending rows. The gap-close pass hardens
that policy contract so malformed accepted pending count/rule-ID fields fail with explicit contract
validation errors.

The V1 EA gate repair plan is complete through Milestone 6. The promoted review is
`v1-cg-ecid-compliance-review` for the East Crazy Inspiration Divide package on source set
`source-set-ba8d0feae79501b8`, rule pack `nepa-ea-v0` version `0.4.0`. The gate passes with
`passed=true`, `broader_ea_passed=true`, `forest_plan_passed=true`,
`failure_category_counts={}`, `failed_rule_ids=[]`, `rule_section_match_rate=1.0`,
`conditional_false_positive=0`, `conditional_false_negative=0`, and `14` accepted-pending
conditional adjudication rows carried as explicit V1 reviewer risk. Review-bound `phase-eval` now
passes `16/16` phases with `reviewer_ready=true`; the compliance gold phase is satisfied by the
passing base-pack gold suite through `rule_pack_match_mode=generated_base`. Embeddings, reranking,
model-assisted synthesis, and broader Region 1 package expansion remain post-V1 work and should
start under a new milestone plan.

## Verification Commands

Run all tests:

```bash
PYTHONPATH=src python -m pytest -q
```

Run captured-library integrity tests only:

```bash
PYTHONPATH=src python -m pytest tests/test_captured_library.py -q
```

Rebuild the full reviewer catalog from the current full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --batch-run-id corpus-update-2026-05-01-cg-support-batches
```

Build derived extraction outputs from the current reviewer catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
```

Inventory extraction reuse opportunities before a reuse-first rebuild:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory \
  --output-dir source_library
```

Assemble the current source set with reuse first, then parse only records without a valid current
or prior extraction candidate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library \
  --reuse-existing \
  --reuse-inventory-path source_library/derived/source-set-ba8d0feae79501b8/reuse_inventory/reuse_inventory_records.jsonl
```

For a delta-only extraction, repeat `--id` for each selected source record. The 2026-04-30
land-exchange update used this mode for the 38 new artifact-bearing rows and left `R1EA-160`
unextracted because it is scope-excluded.

Build the evidence retrieval index:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library
```

Run a retrieval query:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-query \
  --output-dir source_library \
  --review-topic alternatives \
  "alternatives environmental effects"
```

Run the seed retrieval eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --eval-file config/retrieval_eval_seed.json
```

Build the evidence graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build \
  --output-dir source_library
```

Build source claims and run the seed claim eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval \
  --output-dir source_library \
  --eval-file config/claim_eval_seed.json
```

Build rule-claim bindings and run the seed rule-claim eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
```

Run the rule-pack coverage gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

Run the seed compliance review eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

Run applicability decision-quality evals:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/applicability_eval_seed.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/applicability_gold_eval_v0.json
```

Run the adjudicated gold eval promotion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
```

Run phase-aligned readiness evaluation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library
```

Run the manifest-driven post-V1 promotion suite:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```
