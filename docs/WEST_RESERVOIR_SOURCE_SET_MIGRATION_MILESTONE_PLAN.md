# West Reservoir Source-Set Migration Milestone Plan

Date: 2026-05-28
Status: Active migration packet opened from
`docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
Milestone 1; Milestone 1 contract migration reduced locally with the tracked
parity gate on `source-set-f70ea11e04ae3d53`; Milestone 2 authority-universe
proof is blocked on the f70 Flathead component inventory
Owner context: source-set contract migration child for
`docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`

## Purpose

Move the West Reservoir reviewer-readiness contract only if the move is
governed, reproducible, and source-set coherent.

The active parent packet is stopped on `source-set-4fb59e9eb43045cb` because
`applicability-authority-universe` cannot find the current authority-source
records required by non-forest authority families and baseline rules. The
same required current records exist in the later current-source-gap closeout
catalog on `source-set-f70ea11e04ae3d53`, but that catalog cannot be borrowed
as proof for the 4fb-locked contract.

This packet owns the explicit migration decision and parity gates. It updates
the West Reservoir source-set contract only as one coherent migration slice,
then returns the review to the parent readiness plan after the authority
universe is green on the selected source set.

## Current Evidence

- Parent readiness packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- Source-evidence blocker packet:
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- Current review ID:
  `west-reservoir-67436`
- Current forest unit:
  `flathead-nf`
- Previous locked source set:
  `source-set-4fb59e9eb43045cb`
- Selected migrated source set:
  `source-set-f70ea11e04ae3d53`
- Current failing command:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-4fb59e9eb43045cb`
- Fresh 4fb failure signal:
  `passed=false`, `validation_passed=false`,
  `candidates_have_source_evidence_available.failure_count=9`, and
  `authority_family_template_candidates_cover_config.missing_source_record_count=10`
- Feasibility inventory:
  the failing snapshot requires `59` unique source-record IDs. Of those, `49`
  legacy IDs have governed current mappings in
  `config/compliance_source_record_reconciliation_v1.json`; none of those
  mapped current IDs are present in the active 4fb catalog, and all `49` are
  present in the f70 current-source-gap closeout catalog.
- Current 4fb catalog:
  `source_library/catalog/source_catalog.jsonl` with manifest
  `source_set_id="source-set-4fb59e9eb43045cb"` and `source_count=647`
- Candidate f70 catalog:
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl`
  with manifest `source_set_id="source-set-f70ea11e04ae3d53"` and
  `source_count=708`
- Current West Reservoir contract surfaces migrated to f70:
  `config/replay_contexts/west-reservoir-67436.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/forest_plan_component_evals/west-reservoir-67436.json`, and
  the West Reservoir slot in
  `config/forest_plan_component_eval_coverage_v1.json`
- Current replay catalog surface:
  `config/replay_contexts/west-reservoir-67436.json` now points
  `catalog_dir` at
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`,
  whose manifest declares `source-set-f70ea11e04ae3d53`.
- Fresh migrated authority-universe signal:
  `applicability-authority-universe --review-id west-reservoir-67436
  --source-set-id source-set-f70ea11e04ae3d53` reads the selected f70 catalog,
  reports `candidates_have_source_evidence_available.failure_count=0` and
  `authority_family_template_candidates_cover_config.missing_source_record_count=0`,
  but still exits red because
  `forest_plan_component_candidates_use_profile_inventory` has
  `component_inventory_present=false`, `component_candidate_count=0`, and
  `required_profile_source_record_ids=["FINAL-FLAT-001"]`.
- Milestone 0 parity gate:
  `tests/test_west_reservoir_source_set_migration.py` now proves the tracked
  source-set contract surfaces have one identity and includes a controlled
  mixed-source-set case.

## Source-Set Parity Inventory

Current tracked West Reservoir source-set surfaces after migration:

| Surface | Current source-set ID |
| --- | --- |
| `config/replay_contexts/west-reservoir-67436.json` `source_set_id` | `source-set-f70ea11e04ae3d53` |
| `config/v1_west_reservoir_real_ea_eval.json` `source_set_id` | `source-set-f70ea11e04ae3d53` |
| `config/forest_plan_component_evals/west-reservoir-67436.json` `source_set_id` | `source-set-f70ea11e04ae3d53` |
| `config/forest_plan_component_eval_coverage_v1.json` West Reservoir `expected_source_set_id` | `source-set-f70ea11e04ae3d53` |
| `config/replay_contexts/west-reservoir-67436.json` `catalog_dir` manifest | `source-set-f70ea11e04ae3d53` |

Status surfaces that must remain typed blocked during migration:

| Surface | Current status |
| --- | --- |
| `config/v1_real_package_review_coverage_v1.json` West Reservoir slot | `coverage_class_id="alternate_package_typed_blocked"`, `expected_contract_status="typed_blocked"` |
| `config/forest_specific_example_package_registry_v1.json` West Reservoir example | `coverage_class_id="alternate_package_typed_blocked"`, `expected_contract_status="typed_blocked"` |
| `config/forest_specific_example_package_registry_v1.json` Flathead route | `routing_status="typed_blocked_example_available"` |

## Goal

Either migrate all West Reservoir source-set contract surfaces to one selected
source set and prove the authority universe is green there, or stop with an
explicit blocker that names the exact contract surface that cannot migrate.

The expected candidate is `source-set-f70ea11e04ae3d53`, but the migration is
not complete until every West Reservoir source-set contract agrees and the
authority-universe rerun uses catalog rows from that same source set.

## Non-Goals

- Do not promote West Reservoir to reviewer-ready in this packet.
- Do not run applicability retrieval, applicability determination,
  generated-rule-pack refresh, forest-plan context, component adjudication,
  compliance review, V1 promotion, phase eval, or aggregate promotion until
  the source-set migration and authority-universe gate pass.
- Do not stage generated `source_library/` artifacts.
- Do not edit authority-family templates, delete source-record requirements,
  lower thresholds, or weaken `candidates_have_source_evidence_available`.
- Do not treat f70 catalog rows as evidence for 4fb.
- Do not reopen Lolo, South Otter, South Plateau, Custer Gallatin, or ECID
  packets except to preserve truthful aggregate residual language.

## Scope

- West Reservoir source-set contract parity
- Replay context, V1 eval contract, component eval contract, and component
  coverage manifest source-set IDs
- Parent and blocker plan routing prose
- Current routing, current-system-state, and session handoff docs
- Focused tests or parity checks needed to prevent mixed-source-set migration

## Out Of Scope

- Full-register network capture or downloader rebuild
- Broad catalog, extraction, graph, compliance, or eval refactors
- Reviewer-ready registry promotion
- Forest-plan component adjudication or compliance review content decisions
- ECID source-delta repair

## Owner Surfaces

- Migration packet:
  `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`
- Parent and blocker packets:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`,
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- Current route and state:
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
- Replay context:
  `config/replay_contexts/west-reservoir-67436.json`
- V1 eval contract:
  `config/v1_west_reservoir_real_ea_eval.json`
- Component eval contract:
  `config/forest_plan_component_evals/west-reservoir-67436.json`
- Component coverage manifest:
  `config/forest_plan_component_eval_coverage_v1.json`
- Real-package and forest-specific manifests that must stay typed blocked:
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_specific_example_package_registry_v1.json`
- Catalog evidence:
  `source_library/catalog/`,
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/`
- Focused tests:
  `tests/test_replay_context.py`,
  `tests/test_v1_ea_eval.py`,
  `tests/test_forest_plan_component_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_forest_specific_example_package_registry.py`

## Placement Rules

- Keep `review_id="west-reservoir-67436"` stable.
- Keep `forest_unit_id="flathead-nf"` stable.
- Migrate source-set identity as an all-or-nothing West Reservoir contract
  change across replay, V1 eval, component eval, component coverage, current
  docs, and stale-artifact guards.
- Keep real-package coverage and forest-specific registry status typed blocked
  until the parent readiness plan's V1, component, compliance, phase, and
  aggregate gates pass.
- Use only catalog records whose `source_set_id` matches the selected migrated
  source set for readiness proof.
- Leave generated `source_library/` artifacts unstaged unless repository
  policy changes explicitly.

## Required Implementation Artifacts

- A source-set parity inventory for every West Reservoir contract surface.
- Tracked config updates for every migrated source-set contract surface.
- A fresh `authority_universe_snapshot.json` generated for the selected source
  set after migration.
- Focused tests or eval gates proving mixed 4fb/f70 source-set IDs fail.
- Current routing, current-system-state, and handoff docs refreshed with exact
  source-set IDs, pass/fail counts, and the next parent-plan route.

## Weak-Point Prevention Contract

| Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse scenario |
| --- | --- | --- | --- | --- | --- |
| Only one config moves to f70 while another West Reservoir contract remains pinned to 4fb. | Replay context, V1 eval, component eval, component coverage manifest | Source-set parity check across all West Reservoir config surfaces plus focused tests. | Any mixed 4fb/f70 source-set ID in tracked West Reservoir contracts fails. | Fixture or test case with one stale manifest ID must fail the parity gate. | Future Codex updates replay context only and resumes downstream work with stale eval contracts. |
| f70 catalog evidence is borrowed without changing contracts. | Authority-universe snapshot and catalog manifests | `applicability-authority-universe` must report the selected source-set ID and source catalog manifest must match it. | Any proof whose snapshot source set differs from replay context or catalog manifest fails. | Run the command against f70 while configs still say 4fb and assert it is not accepted as closeout. | Future Codex points a command at the f70 catalog and calls the 4fb packet green. |
| Migration becomes a hidden reviewer-ready promotion. | Real-package coverage, forest-specific registry, current docs | Registry and coverage manifests must remain typed blocked until parent readiness gates pass. | Any reviewer-ready status change before V1, component, compliance, phase, and aggregate proof fails. | Test or review check verifies West Reservoir remains typed blocked after source-set migration. | Future Codex combines source-set migration with status promotion to avoid the parent gates. |
| Source-evidence checks are weakened instead of satisfying them on the migrated source set. | Authority-family templates, authority-universe contracts, generated snapshot | Existing source-evidence checks must pass with `failure_count=0` and `missing_source_record_count=0`. | Deleted source requirements, lowered thresholds, or skipped validation fail the milestone. | Remove one mapped current row from a fixture catalog and verify the authority-universe gate fails. | Future Codex edits rule templates to hide the missing evidence instead of using catalog-backed sources. |
| Stale historical phase or component artifacts are mistaken for migrated proof. | Review directory, parent plan, current docs | Docs and tests must continue to reject stale `5e65...` phase proof and stale 4fb component proof. | Any readiness claim from a source-set-mismatched generated artifact fails. | Preserve the stale-result guard and add source-set mismatch checks if touched. | Future Codex sees old green artifacts and skips reruns after migration. |

## Milestone Sequence

### Milestone 0 - Migration Baseline And Parity Inventory

Status: Reduced locally on 2026-05-28.

Outcome label: reduced.

Required actions:

- Enumerate every West Reservoir source-set contract surface and record its
  current ID.
- Add or identify a focused parity gate that fails on mixed source-set IDs.
- Confirm f70 is the only current catalog in scope with all `49` governed
  mapped current authority IDs needed by the failed 4fb source-evidence gate.
- Keep all reviewer-ready status fields typed blocked.

Exit criteria:

- The exact source-set surfaces to edit in Milestone 1 are named.
- A mixed-source-set condition has an explicit failing gate.
- No downstream readiness commands have run.

Implementation note:

- Source-set parity inventory is now recorded above for replay context, V1
  eval contract, component eval contract, and component coverage.
- `tests/test_west_reservoir_source_set_migration.py` verified all four
  surfaces agreed on `source-set-4fb59e9eb43045cb` at the Milestone 0
  checkpoint.
- The same test file includes a controlled violation where the component
  coverage slot is changed to `source-set-stale` and the parity gate reports
  that mismatch.
- The typed-blocked real-package slot, forest-specific example, and Flathead
  route are guarded so source-set migration cannot silently become
  reviewer-ready promotion.
- No tracked config was migrated in Milestone 0 and no downstream readiness
  command was run.

### Milestone 1 - Contract Migration To The Selected Source Set

Status: Reduced locally on 2026-05-28.

Outcome label: resolved for source-set contract parity; reduced for reviewer
readiness.

Required actions:

- Update all tracked West Reservoir source-set contract surfaces from 4fb to
  the selected migrated source set in one slice.
- Preserve review ID, forest ID, package authority, typed-blocked registry
  status, and package manifest identity.
- Update parent and blocker plans to state the new selected source set and the
  parent resume point.
- Rerun focused tests for the touched config surfaces.

Exit criteria:

- Every tracked West Reservoir source-set contract agrees on one selected
  source set.
- Typed-blocked status remains unchanged.
- No generated `source_library/` artifacts are staged.

Implementation note:

- Replay context, V1 eval contract, component eval contract, and component
  coverage now agree on `source-set-f70ea11e04ae3d53`.
- The replay context catalog surface now points at the f70
  current-source-gap closeout catalog so the CLI no longer rejects a selected
  f70 authority-universe run as a tracked-context mismatch.
- `tests/test_west_reservoir_source_set_migration.py` now expects f70 parity,
  guards the selected replay catalog surface, keeps the controlled stale
  source-set violation, and preserves typed-blocked status.
- The real-package coverage slot, forest-specific example, and Flathead route
  remain typed blocked; no reviewer-ready promotion occurred.
- The closeout gate reran the selected f70 authority universe and surfaced the
  next blocker in Milestone 2 rather than folding component-inventory repair
  into this contract-migration slice.

### Milestone 2 - Migrated Authority-Universe Proof And Parent Resume Route

Status: Blocked after the Milestone 1 closeout gate.

Outcome label: resolved for the migration packet.

Required actions:

- Rerun:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id <selected-source-set-id>`
- Confirm the fresh snapshot uses the selected source set, the selected
  catalog manifest, `forest_unit_id="flathead-nf"`, and
  `FINAL-FLAT-001`.
- Confirm `candidates_have_source_evidence_available.failure_count=0` and
  `authority_family_template_candidates_cover_config.missing_source_record_count=0`.
- Update current docs and handoff with the exact pass/fail counts and parent
  resume point.

Exit criteria:

- Authority universe is green on the migrated source set, or the packet stops
  with the exact remaining authority-universe blocker.
- If green, the parent West Reservoir readiness plan resumes at
  applicability retrieval/determination on the migrated source set.

Current blocker:

- The migrated authority-universe rerun uses
  `source-set-f70ea11e04ae3d53`, the f70 catalog path, and
  `forest_unit_id="flathead-nf"`.
- Source evidence is no longer the failing check:
  `candidates_have_source_evidence_available.failure_count=0` and
  `authority_family_template_candidates_cover_config.missing_source_record_count=0`.
- The remaining failing check is
  `forest_plan_component_candidates_use_profile_inventory` with
  `component_inventory_present=false`, `component_candidate_count=0`,
  `forest_plan_component_candidate_count=0`, and
  `required_profile_source_record_ids=["FINAL-FLAT-001"]`.
- The next slice must repair or rebuild the f70 Flathead component inventory
  proof before applicability retrieval, determination, compliance, V1
  promotion, phase eval, or registry promotion.

## Required Documentation And Handoff Updates

Every closeout slice for this migration packet must refresh:

- `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`
- `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`

Do not update `README.md` unless stable public entrypoints or repo-level
contracts change.

## Required Verification Gates

For this migration-packet opening slice:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-4fb59e9eb43045cb
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md
git diff --check
```

For contract migration slices, add focused tests for every touched config
surface plus the migrated authority-universe command.

For the Milestone 1 contract migration slice, run:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_west_reservoir_source_set_migration.py tests/test_replay_context.py
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src uv run --extra dev ruff check tests/test_west_reservoir_source_set_migration.py tests/test_replay_context.py
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md
git diff --check
```

For the Milestone 0 parity slice, run:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_west_reservoir_source_set_migration.py
PYTHONPATH=src uv run --extra dev ruff check tests/test_west_reservoir_source_set_migration.py
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md
git diff --check
```

## Acceptance Criteria

- The 4fb feasibility slice records that no governed same-source-set repair is
  available from the active 4fb catalog.
- The migration packet names the selected candidate source set and every
  contract surface that must move together.
- No registry, coverage, V1, component, compliance, phase, or reviewer-ready
  status is promoted by this packet-opening slice.
- Future migration work has an explicit mixed-source-set prevention gate.
- Current routing, current system state, and session handoff point here for
  the next implementation slice.
- No generated `source_library/` artifacts are staged.
- The parity gate fails on a controlled mixed-source-set condition and passes
  only when replay context, V1 eval, component eval, and component coverage
  agree on one source set.

## Stop Conditions

Stop instead of continuing downstream if:

- any West Reservoir source-set contract cannot be migrated with the rest;
- the migrated authority-universe snapshot still reports source-evidence
  failures;
- any command proves the selected catalog does not match the selected source
  set;
- migration would require weakening source-evidence validation; or
- verification fails and the fix would require broad downloader/corpus rebuild
  work outside this packet.

## Local Commit Closeout Policy

- Stage only this migration packet and matching tracked docs/config/source/test
  changes from the verified slice.
- Do not stage ignored generated `source_library/` artifacts.
- Make one atomic local commit per resolved or routed migration slice.
- Do not push unless the user explicitly asks.

## Residual Risks And Next Milestone Routing

- The next slice is Milestone 2 here: make the migrated f70
  authority-universe proof green by resolving the Flathead component
  inventory gap for `FINAL-FLAT-001`, then preserve typed-blocked status until
  downstream parent gates prove reviewer-ready.
- The parent West Reservoir readiness packet remains stopped before
  applicability retrieval/determination until this packet resolves.
- Aggregate component coverage remains red for non-South Otter/non-Lolo
  residual slots and must not be described as green.

## Closeout Checklist

- [x] Source-set parity inventory updated.
- [x] Mixed-source-set gate identified or added.
- [x] West Reservoir contracts migrated together when Milestone 1 starts.
- [x] Authority universe rerun on the selected source set.
- [x] Current docs and handoff updated with exact gate output.
- [x] Generated `source_library/` artifacts left unstaged.
- [x] Local atomic commit created for the verified slice.
