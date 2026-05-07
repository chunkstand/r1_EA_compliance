# EA Consistency Decision Support Preflight Plan

Date: 2026-05-06

This preflight is the implementation gate before the full
`EA_CONSISTENCY_DECISION_SUPPORT_MILESTONE_PLAN.md` begins. It is a Sequence 0
readiness check over the current East Crazy Inspiration Divide review artifacts, repo boundaries,
and report-contract assumptions. Its purpose is to prevent the full milestone from starting on stale
inputs, manual draft prose, unclear output ownership, or unproven Forest Plan and authority counts.

The preflight should be completed and closed before Sequence 1 of the full milestone starts.

## Goal

Prove that the system has the current, complete, and replayable inputs needed to implement a
Responsible Official-facing EA consistency decision-support document for
`v1-cg-ecid-compliance-review`, and define the exact go/no-go conditions for starting the full
report-contract and generator work.

The preflight produces no final supervisor-facing report. It produces a readiness decision and a
small set of implementation instructions for the full milestone.

## Non-Goals

- Do not implement the decision-support report schema, generator, renderer, or validation gate.
- Do not rerun downloader, catalog, extraction, retrieval, graph, source-claim, rule-binding, or
  compliance-review workflows unless the preflight proves existing artifacts are stale.
- Do not treat root-level East Crazies draft exports as canonical pipeline evidence.
- Do not stage ignored `source_library/` outputs.
- Do not broaden the claim beyond the East Crazy Inspiration Divide proving review.
- Do not resolve legal sufficiency, counsel review, or line-officer discretion.

## Preflight Task Packet

Goal:
Confirm the full decision-support milestone can start from current audited artifacts.

Non-goals:
No report generator, no corpus regeneration, no source-library staging, no manual draft promotion.

Relevant files or surfaces:

- `docs/EA_CONSISTENCY_DECISION_SUPPORT_MILESTONE_PLAN.md`
- `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md`
- `docs/SESSION_HANDOFF.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `source_library/reviews/v1-cg-ecid-compliance-review/`
- `source_library/catalog/source_set_manifest.json`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/review_sources.sqlite`
- root-level `East_Crazies_*` draft exports, treated only as non-canonical comparison material

Required eval signal:
Current East Crazies review remains reviewer-ready, phase-eval passing, and promotion-suite current
promotion ready. Broader Region 1 expansion readiness is not required.

Required tests:
For this preflight plan artifact, `git diff --check` is sufficient. When the preflight is executed,
run the preflight verification commands below.

Commit/push policy:
Commit this preflight plan as a docs-only milestone. Later preflight execution or tooling should be
committed separately. Do not push unless explicitly requested.

Stop conditions:
Stop before full implementation if required artifacts are missing, stale, count-drifted,
non-reviewer-ready, dependent on manual draft prose, or require ignored generated outputs to be
tracked.

## Canonical Review Boundary

The preflight is scoped to:

- review ID: `v1-cg-ecid-compliance-review`
- source set: `source-set-ba8d0feae79501b8`
- EA package:
  `source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`
- Forest Plan consistency source: `EA-PACKAGE-042`, the extracted Plan Consistency Table
- report output boundary for the full milestone:
  `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`

The preflight should explicitly record these identifiers in its readiness result. A mismatch is a
hard stop unless the full milestone plan is amended.

## Required Artifact Presence

Before Sequence 1 starts, verify these artifacts exist and are parseable where applicable:

- `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.md`
- `source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.pdf`
- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/search_coverage_certificates.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicability_validation.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack_validation.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.md`
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/non_applicable_authority_appendix.md`
- `source_library/reviews/v1-cg-ecid-compliance-review/authority_reviewer_resolution_report.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/litigation_risk_summary.json`
- `source_library/reviews/v1-cg-ecid-compliance-review/package/package_manifest.jsonl`
- `source_library/reviews/v1-cg-ecid-compliance-review/package/package_chunks.jsonl`
- `source_library/reviews/v1-cg-ecid-compliance-review/package/extracted_text/EA-PACKAGE-042_bebc890bc3da89c0.txt`

The preflight should compute and retain hashes for the JSON, JSONL, Markdown, PDF, and extracted
Plan Consistency Table inputs that the full milestone will depend on. Hashes should be used as the
baseline for the later decision-support manifest.

## Required Count Baseline

The preflight readiness result must assert the current expected counts:

- applicable authority findings: `33`
- non-applicable authorities: `340`
- total applicability candidates: `373`
- Forest Plan component findings: `329`
- supported/applicable Forest Plan components: `79`
- not-applicable Forest Plan components: `250`
- Custer Gallatin standards in source-set inventory: `58`
- applicable Forest Plan standards: `12`
- applied Forest Plan standards: `12`
- open reviewer-resolution items: `0`
- unresolved applicable Forest Plan standards: `0`
- phase-eval phases passing: `16/16`

Any count drift is a stop condition unless the preflight explains the upstream rerun or artifact
change that caused it and updates the full milestone expectations.

## Preflight Workstreams

### 1. Workspace And Generated-Output Boundary

Run `git status -sb` and classify the worktree before implementation:

- tracked changes must be absent or explicitly part of the preflight slice;
- root-level `East_Crazies_*` files are manual draft exports and must remain non-canonical;
- generated `source_library/` outputs must remain ignored unless repository policy changes;
- no unrelated dirty files may be staged for the preflight or later full milestone commits.

Go condition:
The tracked worktree is clean or contains only the preflight slice.

Stop condition:
The full milestone would need to stage unrelated work or promote manual drafts as canonical
pipeline evidence.

### 2. Artifact Freshness And Hash Baseline

Inspect the required artifacts and build a small readiness summary with:

- artifact path;
- artifact type;
- parse status;
- hash;
- source-set ID or review ID when present;
- validation status when present;
- whether the artifact is an input to JSON, Markdown, PDF, or manifest generation.

Go condition:
All required artifacts exist, parse cleanly, and agree on the review/source-set/package boundary.

Stop condition:
Any required artifact is missing, unparsable, stale against recorded validation, or tied to a
different review/source-set/package.

### 3. Current Gate Replay

Before full implementation starts, replay the current readiness gates:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```

Expected result:

- `phase-eval` passes `16/16` phases for `v1-cg-ecid-compliance-review`;
- `promotion-suite` reports current promotion ready;
- broader expansion readiness may remain blocked by expansion-specific work and does not block this
  preflight.

Go condition:
Current review readiness remains green.

Stop condition:
The current review is not reviewer-ready, phase-eval fails, or promotion readiness fails for the
current proving review.

### 4. Forest Plan Consistency Baseline

Verify that the Plan Consistency Table is present as `EA-PACKAGE-042` and that the generated Forest
Plan artifacts remain the canonical source for the full report:

- `forest_plan_component_findings.json` owns component-level findings;
- `forest_plan_applicable_standard_coverage.json` owns applicable-standard coverage;
- `forest_plan_context_summary.json` owns selected forest-plan context;
- the extracted Plan Consistency Table is cited as package evidence, not manually interpreted as a
  substitute for generated findings.

Go condition:
The preflight can map the Plan Consistency Table to generated Forest Plan findings and applicable
standards without relying on manual root-level prose.

Stop condition:
Forest Plan consistency would need hand-authored conclusions, uncited standards, or a different
forest-plan profile than the promoted Custer Gallatin profile.

### 5. Authority Universe Boundary

Confirm that applicable and non-applicable authorities are both first-class inputs:

- applicable authority rows come from generated compliance findings and applicable-authority
  artifacts;
- non-applicable authorities come from `non_applicable_authorities.json`,
  `search_coverage_certificates.json`, and `non_applicable_authority_appendix.md`;
- generated-rule-pack validation proves the compliance review used validated applicable
  authorities only;
- no report section may collapse the `340` non-applicable authorities into a generic disclaimer.

Go condition:
The full report can show both sides of the authority boundary with counts, categories, coverage,
and artifact pointers.

Stop condition:
The report would omit non-applicable authorities, double-count them as compliance findings, or lose
search-coverage traceability.

### 6. Residual Risk And Implementation Confirmation Source Mapping

Before generator implementation, decide where each implementation-confirmation and residual-risk
entry will come from:

- generated compliance limitations;
- `litigation_risk_summary.json`;
- `authority_reviewer_resolution_report.json`;
- Forest Plan applicable-standard limitations;
- package evidence spans and source evidence spans;
- a new tracked config or fixture if a risk/checklist item is needed but not already represented
  in current artifacts.

Go condition:
Every checklist item and residual-risk row has a deterministic source path or a planned tracked
configuration owner.

Stop condition:
The report would require manual narrative judgment that cannot be traced to a generated artifact or
tracked config.

### 7. CLI, Module, And Renderer Ownership

Before Sequence 1 starts, choose and document the implementation surface:

- preferred CLI command name: `ea-consistency-document`
- canonical JSON owner: a new decision-support report module under
  `src/usfs_r1_ea_sources/`
- Markdown/PDF rendering: reuse the existing compliance-matrix rendering pattern unless the
  preflight proves it cannot support the report structure;
- docs/schema owner: `docs/OUTPUT_SCHEMAS.md` plus the full milestone plan;
- tests: focused schema/generator/gate tests plus `tests/test_architecture_contract.py` when CLI or
  module boundaries change.

Go condition:
The full milestone has a clear implementation surface and verification path before code edits.

Stop condition:
The command, module ownership, or PDF renderer path is ambiguous enough to risk broad refactoring.

### 8. Fixture And Regression Contract

Define the minimum fixture expectations before Sequence 1:

- required report sections;
- required count fields;
- required artifact hash fields;
- at least one applicable authority row with package and source evidence;
- at least one non-applicable authority summary row with search coverage;
- at least one Forest Plan component summary;
- all `12` applicable standards present in the real-review expectation;
- fail-closed cases for missing required artifacts, count drift, stale hashes, missing PDF, and
  missing non-applicable authority summary.

Go condition:
The first implementation sequence can add schema/fixture tests without needing to design the
contract during generator implementation.

Stop condition:
The test contract cannot distinguish applicability status, compliance status, implementation
confirmation, and residual risk.

## Preflight Readiness Result

When executed, the preflight should produce a short go/no-go result. A tracked Markdown summary may
be enough for a manual preflight. If a command is implemented later, use:

```text
source_library/reviews/v1-cg-ecid-compliance-review/decision_support_preflight/
```

Suggested generated files:

- `ea_consistency_decision_support_preflight.json`
- `ea_consistency_decision_support_preflight.md`

These files should remain generated local artifacts unless repository policy changes.

The readiness result should include:

- overall status: `go` or `stop`;
- review ID, source-set ID, package path, and Plan Consistency Table package record;
- required artifact presence and hashes;
- required count assertions;
- gate replay result;
- manual-draft quarantine confirmation;
- residual-risk/checklist source mapping status;
- implementation surface decision;
- blockers and next action.

## Verification Commands

Use these commands when executing the preflight:

```bash
git status -sb
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/compliance_matrix.json \
  /tmp/ecid_compliance_matrix.validated.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/applicable_authorities.json \
  /tmp/ecid_applicable_authorities.validated.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/applicability/non_applicable_authorities.json \
  /tmp/ecid_non_applicable_authorities.validated.json
python -m json.tool \
  source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json \
  /tmp/ecid_forest_plan_component_findings.validated.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
git diff --check
```

For this docs-only plan commit, run:

```bash
git diff --check
```

## Handoff To Full Milestone

Start Sequence 1 of the full decision-support milestone only after the preflight result is `go`.

If the preflight stops, convert each blocker into a scoped milestone before resuming. Do not patch
around blockers inside the decision-support generator.

If the preflight passes, Sequence 1 should begin with:

- the confirmed artifact hash baseline;
- the confirmed count baseline;
- the chosen command/module/renderer ownership;
- the fixture and fail-closed test contract;
- a clear statement that root-level East Crazies draft exports are non-canonical comparison
  artifacts only.
