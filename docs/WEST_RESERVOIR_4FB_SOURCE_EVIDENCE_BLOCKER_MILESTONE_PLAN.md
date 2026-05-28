# West Reservoir 4fb Source-Evidence Blocker Milestone Plan

Date: 2026-05-28
Status: Active blocker packet; Milestone 0 opened locally; Milestone 1 reduced
locally by same-source-set feasibility and routed to
`docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`; parent West
Reservoir readiness packet is stopped before applicability
retrieval/determination
Owner context: Child blocker for `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md` Milestone 1

## Purpose

Resolve the remaining West Reservoir Milestone 1 blocker without weakening the
reviewer-readiness contract.

`west-reservoir-67436` is locked to
`source-set-4fb59e9eb43045cb` by the current replay context, V1 eval contract,
and component-coverage manifest. The current `applicability-authority-universe`
rerun proves Flathead forest-plan scoping is correct, but fails because the
active 4fb catalog lacks the current source records needed by non-forest
authority families and baseline rules.

This packet exists to decide that issue explicitly: either prove and implement
a governed same-source-set repair, or open a separate source-set migration
packet. Do not silently borrow a newer catalog or promote West Reservoir on a
different source set inside the parent readiness plan.

## Bitter Lesson Alignment Lock

This blocker is a Bitter Lesson guardrail for the parent readiness plan. It
keeps the repair focused on scalable evidence and eval machinery instead of a
handcrafted West Reservoir workaround.

Allowed repairs must work through durable data and repeatable gates:

- catalog/source-set evidence for the selected source set;
- source-record reconciliation data in tracked config;
- authority-universe validation and generated snapshots;
- replay, V1, component, registry, and coverage contract parity; and
- current routing, current-system-state, and session handoff updates that
  record the exact pass/fail signal.

Disallowed repairs include hidden runtime branches for West Reservoir, deleting
authority-family source requirements, lowering `failure_count` or
`missing_source_record_count` by weakening validation, treating f70 evidence as
4fb evidence, or letting a human judgment replace catalog-backed source
presence. If 4fb cannot supply the required current rows through a governed
repair, the aligned next step is a source-set migration packet with parity
checks, not a local exception.

## Current Evidence

- Parent packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- Current review:
  `review_id="west-reservoir-67436"`
- Current locked source set:
  `source-set-4fb59e9eb43045cb`
- Current active catalog:
  `source_library/catalog/source_catalog.jsonl` and
  `source_library/catalog/source_set_manifest.json`
- Current replay context:
  `config/replay_contexts/west-reservoir-67436.json`
- Current reconciliation surface:
  `config/compliance_source_record_reconciliation_v1.json`
- Proven failing command:
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-4fb59e9eb43045cb`
- Current failure signal:
  `passed=false`, `validation_passed=false`,
  `candidates_have_source_evidence_available.failure_count=9`, and
  `authority_family_template_candidates_cover_config.missing_source_record_count=10`
- Failing candidate families include clean air, clean water, cultural
  resources/SHPO, eagle/EFH/wildlife, hazardous materials,
  invasive/pesticide/soils/farmland/drinking water, minerals/energy, tribal
  consultation, vegetation/wildfire/forest health, and
  wilderness/WSR/trails/designated areas.
- The missing legacy source records already have governed current mappings in
  `config/compliance_source_record_reconciliation_v1.json`; examples include
  `R1EA-093 -> FED-044`, `R1EA-083 -> FED-045`,
  `R1EA-077 -> FED-055`, `R1EA-056 -> FED-071`,
  `R1EA-045 -> FED-083`, and state water/SHPO rows such as
  `STP-031` through `STP-035`.
- Those current rows are absent from the active 4fb catalog and present in the
  later current-source-gap closeout catalog
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  on `source-set-f70ea11e04ae3d53`.
- Milestone 1 feasibility closeout confirmed the failing snapshot requires
  `59` unique source-record IDs. `49` legacy IDs have governed current
  mappings in `config/compliance_source_record_reconciliation_v1.json`; none
  of those mapped current IDs are present in the active 4fb catalog, and all
  `49` are present in the f70 current-source-gap closeout catalog.

## Goal

Make the West Reservoir source-evidence route truthful before any downstream
readiness work continues.

The blocker is resolved only if one of these outcomes is proven by generated
artifacts and current docs:

- a governed same-source-set repair makes
  `applicability-authority-universe --review-id west-reservoir-67436 --source-set-id source-set-4fb59e9eb43045cb`
  pass without borrowing f70 artifacts; or
- a separate source-set migration packet supersedes the parent readiness
  contract and updates every replay, V1, component, registry, phase-eval, and
  routing surface together.

## Non-Goals

- Do not run applicability retrieval, applicability determination,
  applicability validation, generated-rule-pack refresh, forest-plan context,
  compliance review, V1 eval promotion, phase eval promotion, or registry
  promotion while this blocker is open.
- Do not rewrite `source-set-f70ea11e04ae3d53` catalog rows to appear as 4fb
  evidence.
- Do not stage generated `source_library/` artifacts.
- Do not edit eval thresholds, delete source-record requirements, or relax
  `candidates_have_source_evidence_available` or
  `authority_family_template_candidates_cover_config`.
- Do not reopen unrelated Lolo, South Otter, Custer Gallatin, South Plateau, or
  ECID packets except to preserve truthful aggregate residual language.

## Scope

- West Reservoir source-evidence routing and blocker documentation
- Active 4fb catalog/source-set evidence inspection
- Source-record reconciliation and catalog identity checks
- Parent West Reservoir readiness routing docs
- Any focused test needed to prevent cross-source-set borrowing if a code or
  config repair is implemented later

## Out Of Scope

- Full-register network capture unless a later user-approved repair packet
  requires it
- Broad downloader, extraction, retrieval, graph, compliance, or eval
  refactors
- Forest-plan component adjudication or compliance review work
- Registry promotion from typed blocked to reviewer ready

## Owner Surfaces

- Child blocker packet:
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- Parent readiness packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- Current docs and handoff:
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`
- Replay and eval contracts:
  `config/replay_contexts/west-reservoir-67436.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/forest_plan_component_evals/west-reservoir-67436.json`,
  `config/forest_plan_component_eval_coverage_v1.json`
- Source-record reconciliation:
  `config/compliance_source_record_reconciliation_v1.json`
- Active and comparison catalogs:
  `source_library/catalog/`,
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/`
- Authority-universe builders and contracts if code changes are required:
  `src/usfs_r1_ea_sources/applicability_authority_universe_builder.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py`,
  `src/usfs_r1_ea_sources/applicability_contract_support.py`
- Focused tests if code changes are required:
  `tests/test_applicability_authority_universe_builder.py`,
  `tests/test_applicability_authority_universe_contracts.py`,
  `tests/test_replay_context.py`

## Placement Rules

- Keep `review_id="west-reservoir-67436"` stable.
- Keep the parent readiness packet locked to
  `source-set-4fb59e9eb43045cb` until a separate migration packet explicitly
  changes that contract.
- Catalog evidence must come from records whose `source_set_id` matches the
  selected readiness source set.
- Legacy-to-current source-record reconciliation is allowed only when the
  resolved current source IDs exist in the selected catalog.
- Any migration away from 4fb must update replay context, V1 eval contract,
  component eval contract, component coverage manifest, registry/coverage
  manifests, current docs, and stale-artifact guards in one verified slice.

## Required Implementation Artifacts

For this blocker-opening slice:

- this child blocker plan;
- parent readiness plan status updated to route here;
- `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/SESSION_HANDOFF.md` updated with the new stop condition and next route.

For a future repair slice:

- a fresh `authority_universe_snapshot.json` for West Reservoir on the selected
  source set;
- exact catalog/manifest evidence showing whether all required current source
  records are present in that selected source set;
- focused tests if code or config behavior changes; and
- current docs refreshed with the verified pass/fail counts.

For the Milestone 1 feasibility closeout slice:

- fresh 4fb authority-universe failure was rerun and recorded;
- required legacy/current source-record inventory was compared against active
  4fb and comparison f70 catalog evidence; and
- `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md` was opened as
  the follow-on owner because no governed same-source-set 4fb repair exists.
- The migration packet Milestone 0 parity gate now exists in
  `tests/test_west_reservoir_source_set_migration.py`; the next blocker
  follow-on is the migration packet's Milestone 1 contract migration.

## Weak-Point Prevention Contract

| Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse scenario |
| --- | --- | --- | --- | --- | --- |
| A newer f70 catalog could be treated as proof for the 4fb-locked West Reservoir contract. | Replay context, active catalog, authority-universe snapshot, current docs | `applicability-authority-universe` must report the same selected source set as the replay context and catalog records. | Any readiness proof with catalog rows from a different `source_set_id` fails. | Seed or point to a borrowed-catalog run and assert source-set mismatch remains blocked. | Future Codex points the command at `current-source-gap-closeout-catalog-gate` and promotes readiness without migrating contracts. |
| The source-evidence gate could be weakened instead of repairing evidence. | `applicability_authority_universe_contracts.py`, authority-family templates, tests | Existing checks stay fail-closed: `candidates_have_source_evidence_available` and `authority_family_template_candidates_cover_config`. | Lowered failure counts caused by deleted requirements or disabled checks fail the milestone. | Remove a mapped current row from a fixture catalog and verify the gate fails. | Future Codex deletes `R1EA-*` source requirements to get a green authority universe. |
| A same-source-set repair could mutate ignored generated catalog data without durable routing truth. | `source_library/catalog/`, current docs, handoff | Current docs must record exact source-set ID, source counts, command output, and whether generated artifacts were left unstaged. | A repair that only edits ignored artifacts and leaves tracked docs/config unchanged fails closeout. | Compare `git status --ignored=matching source_library/` and tracked docs after a repair attempt. | Future Codex gets a local green run that cannot be reproduced from tracked contracts. |
| A migration could update only the replay context and leave eval/coverage manifests pinned to 4fb. | Replay context, V1 eval contract, component eval contract, coverage manifests | Source-set identity parity check across all West Reservoir contracts before downstream reruns. | Mixed 4fb/f70 West Reservoir source-set IDs fail the migration milestone. | Add a focused fixture with one stale manifest ID and verify the parity check fails. | Future Codex migrates one config file and creates another stale-green source-set split. |
| Downstream readiness commands could run while the source-evidence blocker is still red. | Parent plan, routing docs, generated review directory | Handoff and routing must say no retrieval/determination/compliance/promotion until authority universe is green. | Any new downstream readiness claim while authority-universe validation is red fails this packet. | Preserve a current-doc assertion or review checklist that blocks downstream steps on red authority universe. | Future Codex skips the blocked Milestone 1 gate and starts component/compliance work from stale artifacts. |

## Milestone Sequence

### Milestone 0 - Blocker Packet Opened

Status: Opened locally in this slice.

Outcome label: reduced.

Required actions:

- Rerun the current authority-universe command on 4fb and record the exact
  failure counts.
- Confirm the active 4fb catalog lacks the required reconciled current IDs.
- Confirm the newer f70 current-source-gap closeout catalog is a different
  source set, so it cannot be used as current 4fb proof.
- Add this blocker plan and update the parent/readiness routing docs.

Exit criteria:

- Current docs route the next implementation slice here.
- Parent West Reservoir readiness remains stopped before applicability
  retrieval/determination.
- No registry, coverage, V1, component, compliance, or phase readiness status
  is promoted.
- Local route commit is `0773ef7` (`Open West Reservoir source evidence
  blocker`). The later docs-only Bitter Lesson alignment commit is `3a5e6b3`
  (`Align West Reservoir plans with Bitter Lesson`).

### Milestone 1 - Same-Source-Set Repair Feasibility

Status: Reduced locally on 2026-05-28; no governed 4fb repair found.

Outcome label: reduced if a migration packet is required; resolved only if 4fb
can be repaired and rerun green under the existing contract.

Required actions:

- Inventory every required legacy and reconciled current source-record ID from
  the failing authority-universe snapshot.
- Compare those IDs against `source_library/catalog/source_catalog.jsonl` and
  `source_library/catalog/source_set_manifest.json`.
- Determine whether a governed same-source-set repair exists that keeps
  `source-set-4fb59e9eb43045cb` truthful and reproducible.
- If yes, implement only that governed repair and rerun
  `applicability-authority-universe` on 4fb.
- If no, stop and open a source-set migration packet instead of changing the
  parent plan silently.

Exit criteria:

- Either the authority universe passes on 4fb with `failure_count=0` and
  `missing_source_record_count=0`, or a migration packet owns all follow-on
  changes.

Implementation note:

- Fresh 4fb authority-universe rerun still exits red with
  `passed=false`, `validation_passed=false`, `candidate_authority_count=146`,
  `forest_plan_component_candidate_count=80`, and the known fail-closed
  source-evidence checks.
- The feasibility inventory found `59` unique required IDs across the failing
  source-evidence candidates and missing authority-family template source
  records.
- `49` required legacy IDs map to current source records through
  `config/compliance_source_record_reconciliation_v1.json`.
- The active 4fb catalog has `source_count=647` and no mapped current IDs for
  those `49` governed rows.
- The f70 current-source-gap closeout catalog has `source_count=708` and all
  `49` mapped current IDs, but it is a different source set and cannot be used
  as 4fb proof.
- No source/config/code repair was made in this blocker because any truthful
  repair must migrate the West Reservoir source-set contract as a separate
  governed slice.
- Follow-on owner:
  `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`.

### Milestone 2 - Source-Set Migration Packet If Required

Status: Routed locally through
`docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`; migration
Milestone 0 parity inventory is reduced locally and Milestone 1 contract
migration is pending.

Outcome label: reduced for this blocker; resolved for routing if the migration
packet supersedes the parent contract.

Required actions:

- Create a dedicated migration plan if Milestone 1 proves 4fb cannot support
  the required current source records.
- Enumerate every West Reservoir source-set contract surface before edits.
- Require a parity gate proving all West Reservoir configs and generated
  readiness artifacts agree on one new source set before downstream commands
  resume.

Exit criteria:

- The parent West Reservoir readiness plan either remains locked to a repaired
  4fb source set, or explicitly yields to the migration packet.

## Required Documentation And Handoff Updates

Every closeout slice for this blocker must refresh:

- `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`

Do not update `README.md` unless stable public entrypoints or repo-level
contracts change.

## Required Verification Gates

For the blocker-opening and same-source-set feasibility slices:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id west-reservoir-67436 --source-set-id source-set-4fb59e9eb43045cb
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md
git diff --check
```

For any source/config/code repair slice, add focused tests for the touched
surface plus the parent plan's applicable verification commands.

## Acceptance Criteria

- The active 4fb authority-universe run remains red for the recorded
  source-evidence failures, and the feasibility slice records that no governed
  same-source-set repair exists from the active 4fb catalog.
- The blocker plan names the exact stop condition and next route.
- The migration packet owns the all-or-nothing West Reservoir source-set
  contract change before downstream readiness resumes.
- The parent West Reservoir readiness plan does not proceed past Milestone 1.
- Current routing, current system state, and session handoff all point to this
  blocker packet and the migration packet for the next slice.
- No generated `source_library/` artifacts are staged.
- No tests, thresholds, source requirements, or eval manifests are weakened.
- The blocker-opening slice is locally committed before it is called complete.

## Stop Conditions

Stop instead of continuing downstream if:

- 4fb cannot supply the required current source records through a governed
  same-source-set repair;
- any proposed repair requires silently mixing 4fb and f70 catalog evidence;
- any eval or coverage contract would still refer to the old source set after a
  proposed migration;
- authority-universe validation remains red after the intended repair; or
- verification fails and the fix would require broad downloader/corpus rebuild
  work outside this blocker packet.

## Local Commit Closeout Policy

- Stage only this blocker plan and matching tracked docs/config/source/test
  changes from the verified slice.
- Do not stage ignored generated `source_library/` artifacts.
- Make one atomic local commit per resolved or routed blocker slice.
- Do not push unless the user explicitly asks.

## Residual Risks And Next Routing

- The follow-on is
  `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md` because the
  current source rows are proven in the later f70 current-source-gap closeout
  catalog, not in the active 4fb catalog.
- That migration packet now has a Milestone 0 parity gate; its next slice is
  Milestone 1 all-or-nothing West Reservoir contract migration.
- If a reproducible 4fb repair is found, resume the parent West Reservoir
  Milestone 1 sequence only after `applicability-authority-universe` is green.
- If migration is required, downstream applicability/compliance/component/V1
  work must wait until all West Reservoir source-set contracts are updated and
  stale-artifact guards are refreshed.
