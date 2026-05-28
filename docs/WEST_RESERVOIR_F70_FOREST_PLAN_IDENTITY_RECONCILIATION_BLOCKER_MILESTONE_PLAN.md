# West Reservoir f70 Forest-Plan Identity Reconciliation Blocker Milestone Plan

Date: 2026-05-28
Status: Milestone 2 reduced on 2026-05-28. The registry is rebound to
`source-set-f70ea11e04ae3d53`, and the six originally blocking Flathead
required support records are now indexed in the f70 retrieval index. The
pre-commit closeout gate exposed the next source-capture boundary:
`forest-plan-resolve` now emits current f70 context and component artifacts,
but context validation fails on the triggered Flathead monitoring-program
support route `R1PLAN-flathead-nf-08`.
Owner context: Flathead forest-plan resolver identity blocker for
`review_id="west-reservoir-67436"` on `source-set-f70ea11e04ae3d53`

## Purpose

Route the remaining West Reservoir Milestone 1 blocker to the real owner:
forest-plan source-record identity reconciliation for Flathead on the migrated
f70 source set.

The parent slice rebuilt West Reservoir review and applicability artifacts on
`source-set-f70ea11e04ae3d53`. `ea-review`,
`applicability-context-build`, `applicability-authority-universe`,
`applicability-retrieve`, `applicability-determine`,
`applicability-adjudication-eval`, `applicability-adjudication-apply`,
`applicability-validate`, and `applicability-generate-rule-pack` all ran on
the migrated source set. Applicability validation is now green with `44`
applicable authorities, `102` non-applicable authorities, `0` unresolved
authorities, and `generated_rule_pack_ready=true`.

The first f70 identity slice could not proceed to forest-plan context or
component readiness because `forest-plan-resolve` failed before context
generation with `required_custer_source_records_indexed` and
`retrieval_ready_for_forest_plan_resolver`. The follow-on source-capture slice
supplied the six missing required support records from the archived
`source-set-8a4005c8a083af1a` merged source-delta gate into the selected f70
catalog/retrieval surface without rerunning network capture. The historical
readiness check name remains, but the original missing-six gate is now green.
The next blocker is narrower: the Flathead profile triggered the monitoring
support route, and `R1PLAN-flathead-nf-08` is not yet indexed under f70.

## Current Evidence

- Parent packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- Current review ID:
  `west-reservoir-67436`
- Current source set:
  `source-set-f70ea11e04ae3d53`
- Current forest unit:
  `flathead-nf`
- Fresh applicability validation:
  `passed=true`, `reviewer_ready=true`, `generated_rule_pack_ready=true`,
  `applicable_authority_count=44`, `non_applicable_authority_count=102`,
  `needs_adjudication_authority_count=0`, and
  `unresolved_authority_count=0`
- Fresh generated rule pack:
  `generated_rule_count=44`, `passed=true`, and
  `generated_rule_pack_ready=true`
- Latest resolver command:
  `PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/west-reservoir-67436/package --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --forest-unit-id flathead-nf --reuse-package-cache`
- Latest resolver result:
  exits nonzero after emitting current f70 `forest_plan_context.json`,
  `forest_plan_context_summary.json`, `forest_plan_component_findings.json`,
  `forest_plan_applicable_standard_coverage.json`, and
  `forest_plan_reviewer_resolution_queue.json`. Retrieval readiness now passes,
  including `required_custer_source_records_indexed` and
  `retrieval_ready_for_forest_plan_resolver`.
- Current identity owner:
  `config/r1_forest_plan_identity_reconciliation_v1.json`
- Current identity-owner state:
  `active_source_set_id="source-set-f70ea11e04ae3d53"`,
  `exact_url_matched_source_record_count=74`,
  `governed_catalog_rebound_source_record_count=3`, and
  `unresolved_source_record_count=22`
- Flathead governed identity bindings:
  `R1PLAN-flathead-nf-02 -> FINAL-FLAT-001`,
  `R1PLAN-flathead-nf-03 -> FPS-180`, and
  `R1PLAN-flathead-nf-05 -> FINAL-FLAT-003`.
- Flathead residual identity/source-capture gap before Milestone 2:
  `R1PLAN-flathead-nf-01` remains unresolved-but-catalog-confirmed as the
  planning page. The six blocking required source records that were absent
  from the f70 retrieval index were `R1PLAN-flathead-nf-04`,
  `R1PLAN-flathead-nf-06`, `R1PLAN-flathead-nf-07`,
  `R1PLAN-flathead-nf-10`, `R1PLAN-flathead-nf-12`, and
  `R1PLAN-flathead-nf-16`.
- Flathead Milestone 2 source-capture repair:
  the archived f70 catalog gate
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  now has a local generated overlay for those six source records from archived
  source-delta gate
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate`
  (`source-set-8a4005c8a083af1a`). The f70 extraction summary now reports
  `catalog_source_count=714`, `selected_source_count=714`,
  `extracted_count=714`, `failed_count=0`, `chunk_count=110941`, and
  `validation_passed=true`. The f70 retrieval summary reports
  `source_count=714`, `chunk_count=110941`, `reviewer_ready=true`, and
  `validation_passed=true`.
- New closeout-discovered blocker:
  context validation fails only on
  `triggered_supporting_plan_evidence_has_source_evidence` for
  `route_id="support-monitoring-program"` and
  `source_record_id="R1PLAN-flathead-nf-08"`. The resolver summary also sees a
  stale component adjudication eval on historical
  `source-set-5e65d845ce77e1a0`; that belongs after the monitoring support
  context gate is repaired.
- Current f70 catalog evidence:
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl`
  includes current Flathead rows such as `R1PLAN-flathead-nf-01`,
  `FINAL-FLAT-001`, `FINAL-FLAT-003`, and `FPS-180`, plus the local generated
  overlay rows for the six originally missing FEIS volume 1, BA, BO,
  administrative-change, FEIS volume 2 response, and revised BO expectations.

## Goal

Make Flathead forest-plan identity reconciliation honest for West Reservoir on
`source-set-f70ea11e04ae3d53`, then stop at the source-capture or
component-readiness boundary when the selected f70 catalog cannot satisfy a
triggered Flathead support route.

## Non-Goals

- Do not promote West Reservoir to reviewer-ready in this blocker packet.
- Do not run compliance review, V1 promotion, phase eval, registry promotion,
  or aggregate promotion before the parent readiness gates pass.
- Do not weaken resolver readiness checks, source-record expectations, or
  component thresholds to get past the stop.
- Do not hand-edit ignored `source_library/` context or component artifacts.
- Do not solve unrelated Custer Gallatin, Lolo, South Otter, South Plateau, or
  ECID residuals except where identity reconciliation tests require preserving
  existing truthful residual status.

## Scope

- Flathead rows in `config/r1_forest_plan_identity_reconciliation_v1.json`
- Any required Flathead identity metadata in
  `config/r1_forest_plan_component_inventory_build_manifest.json` and
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- Forest-plan identity reconciliation tests and resolver-readiness tests
- Parent/current routing docs and session handoff updates

## Out Of Scope

- Broad workbook capture, network download, or full-register rebuilds
- Compliance source-record reconciliation for non-forest authority families
- West Reservoir registry promotion
- Global forest-plan resolver refactors unrelated to source-record identity

## Owner Surfaces

- `config/r1_forest_plan_identity_reconciliation_v1.json`
- `config/r1_forest_plan_component_inventory_build_manifest.json`
- `config/region1_forest_plan_readiness_nepa_3d_v1.json`
- `config/forest_plan_profiles.json`
- `src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py`
- `src/usfs_r1_ea_sources/forest_plan_resolver_validation.py`
- `tests/test_forest_plan_identity_reconciliation.py`
- `tests/test_forest_plan_inventory_build_manifest.py`
- `tests/test_forest_plan_resolver_scope.py`
- `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`

## Weak-Point Prevention Contract

| Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse scenario |
| --- | --- | --- | --- | --- | --- |
| Resolver aliases stay pinned to 4fb while West Reservoir runs on f70. | `config/r1_forest_plan_identity_reconciliation_v1.json` | Identity reconciliation tests plus `forest-plan-resolve` on `west-reservoir-67436` / f70. | Registry active source set or Flathead aliases disagree with f70 readiness proof. | A fixture with a stale registry source set must keep failing resolver readiness. | Future Codex updates only replay context and wonders why resolver still reports missing Flathead records. |
| Missing Flathead legacy IDs are bypassed by deleting required readiness roles. | `forest_plan_profiles.json`, inventory manifest, readiness config | Existing readiness role tests and forest-plan identity tests. | Any required Flathead readiness role is removed or marked optional without governed evidence. | Remove one Flathead required readiness role and confirm tests fail. | Future Codex makes the resolver pass by lowering the source-record set. |
| Direct f70 catalog hits are treated as hidden aliases without a governed registry update. | Identity reconciliation registry and catalog evidence | Registry readback must name each Flathead mapping or direct current ID status. | Any resolver proof depends on current catalog rows not represented in tracked identity metadata. | Remove one Flathead mapping from registry while catalog row remains present; resolver must fail. | Future Codex assumes the catalog alone is enough and leaves stale tracked identity surfaces. |
| Parent readiness continues past forest-plan context without current component artifacts. | Parent plan and generated review directory | `forest-plan-resolve` must emit context, component findings, standard coverage, and queue artifacts before Milestone 2 starts. | Missing `forest_plan_context.json` or component artifacts fail the parent gate. | Delete one generated context artifact before component eval and verify eval fails. | Future Codex skips resolver output and jumps directly to compliance. |

## Milestone Sequence

### Milestone 0 - Identity Blocker Inventory

Outcome label: reduced.

Goal: prove the forest-plan resolver stop is an identity-reconciliation blocker
rather than an applicability, retrieval, package-authority, or source-set
migration failure.

Implementation tasks:

- Record the fresh f70 applicability and generated-rule-pack signals.
- Confirm `forest-plan-resolve` fails only at resolver retrieval-readiness
  identity checks.
- Inventory Flathead legacy IDs that remain unresolved in
  `config/r1_forest_plan_identity_reconciliation_v1.json`.
- Route the next slice to this blocker packet.

Acceptance criteria:

- Current docs name the exact blocker command and failing check names.
- The parent plan remains stopped before component readiness, compliance, V1
  promotion, phase eval, or registry promotion.
- No ignored `source_library/` artifacts are staged.

### Milestone 1 - Governed f70 Flathead Identity Reconciliation

Outcome label: reduced. The stale-registry blocker is gone, and the remaining
failure is a narrower Flathead source-capture gap.

Implementation tasks:

- Rebuild or update the identity reconciliation registry against the selected
  f70 catalog without deleting required Flathead readiness roles.
- Rebind any affected inventory/readiness identity metadata through the
  existing reconciliation helpers.
- Add or update tests proving the f70 Flathead aliases are governed and that a
  stale registry still fails.
- Rerun `forest-plan-resolve` for West Reservoir on f70.

Acceptance criteria:

- The identity reconciliation registry no longer blocks the required Flathead
  source-record readiness checks for West Reservoir on f70.
- `forest-plan-resolve` emits current `forest_plan_context.json`,
  `forest_plan_context_summary.json`, `forest_plan_component_findings.json`,
  `forest_plan_applicable_standard_coverage.json`, and
  `forest_plan_reviewer_resolution_queue.json`.
- Any remaining blocker is named exactly and routed before parent Milestone 2.

Closeout result on 2026-05-28:

- `config/r1_forest_plan_identity_reconciliation_v1.json` now declares
  `active_source_set_id="source-set-f70ea11e04ae3d53"`.
- `config/r1_forest_plan_document_register_draft.csv` governs the Flathead ROD
  and FEIS appendices to f70 catalog rows without deleting required readiness
  roles.
- `config/r1_forest_plan_component_inventory_build_manifest.json` and
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` now use
  `FPS-180` for the Flathead ROD and `FINAL-FLAT-003` for the Flathead FEIS
  appendices/glossary.
- `forest-plan-resolve` still fails before context generation, but the
  blocking missing IDs are now exactly `R1PLAN-flathead-nf-04`,
  `R1PLAN-flathead-nf-06`, `R1PLAN-flathead-nf-07`,
  `R1PLAN-flathead-nf-10`, `R1PLAN-flathead-nf-12`, and
  `R1PLAN-flathead-nf-16`.

### Milestone 2 - Flathead f70 Required Support Source-Capture Overlay

Outcome label: reduced. The six originally blocking required support records
are indexed under f70, and the resolver reaches current context/component
generation. The remaining blocker is a newly surfaced monitoring-program
support record, not the original required-source readiness gate.

Implementation tasks:

- Extend the selected archived f70 catalog gate locally with exactly
  `R1PLAN-flathead-nf-04`, `R1PLAN-flathead-nf-06`,
  `R1PLAN-flathead-nf-07`, `R1PLAN-flathead-nf-10`,
  `R1PLAN-flathead-nf-12`, and `R1PLAN-flathead-nf-16` from the archived
  source-delta merged gate.
- Reuse the existing verified extracted text and payload cache from
  `source-set-8a4005c8a083af1a`; do not rerun live network capture or broaden
  to unrelated Flathead rows.
- Regenerate f70 extraction and retrieval artifacts through project commands.
- Rerun `forest-plan-resolve` and stop if the pre-commit closeout gate exposes
  a new source-capture or component-readiness owner.

Closeout result on 2026-05-28:

- Local generated f70 catalog gate source count increased from `708` to `714`
  and artifact count from `696` to `702`; ignored `source_library/` artifacts
  remain unstaged.
- `extract-build` passed with `extracted_count=714`,
  `failed_count=0`, `chunk_count=110941`, and `validation_passed=true`.
- `retrieval-build` passed with `source_count=714`, `chunk_count=110941`,
  `reviewer_ready=true`, and `validation_passed=true`.
- Direct SQLite readback proved the six repaired IDs are now indexed:
  `R1PLAN-flathead-nf-04=1122`, `R1PLAN-flathead-nf-06=918`,
  `R1PLAN-flathead-nf-07=901`, `R1PLAN-flathead-nf-10=5`,
  `R1PLAN-flathead-nf-12=1535`, and `R1PLAN-flathead-nf-16=964` chunks.
- `forest-plan-resolve` now passes retrieval readiness with
  `blocking_missing_source_record_ids=[]` and emits current f70 context plus
  component artifacts. It remains non-ready because context validation lacks
  plan-source evidence for `R1PLAN-flathead-nf-08` on the triggered
  monitoring-program support route.

### Milestone 3 - Monitoring Support Context Gate

Outcome label: pending.

Goal: decide whether `R1PLAN-flathead-nf-08` should be supplied to the selected
f70 retrieval surface or governed as a non-required triggered support route,
then rerun `forest-plan-resolve` without changing component thresholds.

Stop rule:

- Do not refresh component adjudication or promote parent Milestone 2 until
  `forest_plan_context_validation.json` passes on f70. The stale historical
  component adjudication eval on `source-set-5e65d845ce77e1a0` is downstream
  of this context gate.

## Required Verification Gates

For Milestone 0 closeout:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/west-reservoir-67436/package --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --forest-unit-id flathead-nf --reuse-package-cache
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md
git diff --check
```

For Milestone 1 implementation, add:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_identity_reconciliation.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver_scope.py
PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py src/usfs_r1_ea_sources/forest_plan_resolver_validation.py tests/test_forest_plan_identity_reconciliation.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profiles.py tests/test_forest_plan_resolver_scope.py
```

For Milestone 2 source-capture overlay, add:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extract-build --output-dir source_library --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate --id R1PLAN-flathead-nf-04 --id R1PLAN-flathead-nf-06 --id R1PLAN-flathead-nf-07 --id R1PLAN-flathead-nf-10 --id R1PLAN-flathead-nf-12 --id R1PLAN-flathead-nf-16 --reuse-existing --merge-selected-into-existing
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/west-reservoir-67436/package --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id west-reservoir-67436 --forest-unit-id flathead-nf --reuse-package-cache
```

## Required Documentation And Handoff Updates

- `docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`

## Stop Conditions

Stop instead of broadening the parent milestone if:

- resolving Flathead identity requires workbook/source-capture changes outside
  the selected f70 catalog;
- identity reconciliation would weaken required Flathead readiness roles;
- resolver fixes require broad forest-plan runtime refactors unrelated to
  source-record identity; or
- any verification gate fails in a way that belongs to component readiness,
  compliance review, V1 promotion, or registry promotion rather than this
  identity blocker.

## Local Commit Closeout Policy

- Stage only the verified blocker packet slice, docs, tests, and config
  changes owned by the current milestone.
- Do not stage ignored `source_library/` artifacts.
- Make one local atomic commit for the reduced slice before calling it closed.
- Do not push unless explicitly requested.

## Residual Risks And Next Routing

- West Reservoir remains typed blocked.
- The parent readiness plan must not resume to component adjudication or
  compliance until Milestone 3 supplies or governs `R1PLAN-flathead-nf-08` and
  `forest_plan_context_validation.json` passes on f70.
- Aggregate component coverage remains red for unrelated non-West-Reservoir
  residual slots and must not be described as green.
