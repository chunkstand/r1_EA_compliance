# Agent Start Here

Date: 2026-05-21

Use this file as the first stop for agent-driven document work in this repo.
It tells you which existing lane to use and when to refuse the request.
For non-document repo state, route through `docs/CURRENT_ROUTING.md` after this
quick read.

## First Step

Start with the dry-run planner:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources document-plan \
  --request /tmp/document_request.json \
  --output-dir source_library
```

The planner:

- validates the request against `docs/schemas/document_request_v1.schema.json`
- reads `config/document_lanes_v1.json`
- routes to exactly one supported document lane or fails closed
- writes planning-only artifacts under `source_library/document_plans/<request_id>/`
- never writes canonical lane outputs

## Active Workbook

- Active workbook: `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- Active workbook table: `Document_Register_Master`

## Parallel Example Guidance

- Forest-specific example packages are not part of
  `Document_Register_Master`.
- For benchmark/example-package work, read
  `config/forest_specific_example_package_registry_v1.json` and
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` before
  pulling review artifacts.
- The registry maps examples to `applicable_to_forest_unit_ids`, tells you
  which shared eval contracts to read first, and lists the per-review artifact
  families to read for each governed example.
- The aggregate gate for that lane is
  `forest-specific-example-package-eval`, which writes
  `source_library/reviews/forest_specific_example_package_eval/forest_specific_example_package_eval_results.json`
  and proves the typed per-forest routing status still aligns with governed
  review coverage and profile-eval fallback.

## Current Routing

- `docs/CURRENT_ROUTING.md` is the concise first stop for live repo routing.
- Live corpus/runtime truth is tracked in `docs/CURRENT_SYSTEM_STATE.md`.
- Current routed work and recent closeout facts are tracked in
  `docs/SESSION_HANDOFF.md`.
- The umbrella architecture packet in
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md` is now resolved
  through Milestone 10 Sequence 52; the next routed follow-on is
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md` after the
  West Reservoir replay contract was explicitly typed-blocked and quarantined.

## Supported Lanes

- `project_sow_requirements_package`: proposed-action planning support before a complete EA review package exists; downstream command is `project-sow-package`.
- `decision_support_report`: responsible-official-facing synthesis over audited review artifacts; downstream command is `ea-consistency-document`.
- `reviewed_draft_packet`: governed reviewed-draft generation over audited review artifacts; downstream command is `draft-generate`.

## Required Inputs

- `project_sow_requirements_package`: `project_id` and `intake_path`
- `decision_support_report`: `review_id`
- `reviewed_draft_packet`: `review_id`

## Adjacent But Scoped Out

- `review-packet-index`
- `final-qa-certification`

These are real lanes, but they are not the first routed planner targets in this packet.

## Refuse These Requests

- `legal_sufficiency_determination`
- `final_agency_decision`
- `responsible_official_approval`

This repo supports auditable planning support and reviewed-draft generation. It does not generate
legal sufficiency determinations, final agency decisions, or human approvals.

## Go Deeper

- `README.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/ARCHITECTURE.md`
- `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/PROJECT_SOW_PACKAGE_RUNBOOK.md`
