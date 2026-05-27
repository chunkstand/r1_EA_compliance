# Lolo Tyler's Kitchen Source-Record Identity Reconciliation Blocker Milestone Plan

Date: 2026-05-27

Status: Active blocker packet. This plan was opened from
`docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
Milestone 1 after the governed replay slice reached an exact local-replay stop. The tracked
Lolo/Tyler's Kitchen replay and eval contract still points at historical source set
`source-set-5e65d845ce77e1a0`; the current-workbook candidate source set
`source-set-f70ea11e04ae3d53` cannot be promoted into that replay lane until source-record identity
is reconciled through a governed owner surface.

## Why This Exists

Milestone 0 of the current-workbook source-set rebaseline proved that
`source-set-f70ea11e04ae3d53` is not a drop-in replacement for historical source set
`source-set-5e65d845ce77e1a0`. Milestone 1 then found the narrower blocker:

- `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json` still binds the review to
  `source-set-5e65d845ce77e1a0`.
- The applicability CLI rejects a direct `--source-set-id source-set-f70ea11e04ae3d53` override
  against that tracked replay context with `ReplayContextMismatchError`.
- The Lolo v1 eval contract expects 60 source-record IDs. Only 8 of those IDs are present directly
  in the current-workbook `source-set-f70ea11e04ae3d53` catalog surface.
- `config/compliance_source_record_reconciliation_v1.json` maps 51 of the absent expected IDs to
  source records present in the current-workbook candidate catalog, but the forest-plan ID
  `R1PLAN-lolo-nf-02` is reconciled separately by
  `config/r1_forest_plan_identity_reconciliation_v1.json` to `FPS-298`.
- Five compliance-reconciled expected IDs currently map to multiple current catalog records; those
  mappings are coverage evidence, not yet a replay-ready one-to-one identity contract.
- Hash matching is not sufficient as the owner contract: the historical extraction manifest has
  221 hash matches into the current-workbook extraction manifest, 129 unmatched historical rows, and
  match fanout that includes one-to-many cases.

This packet makes the identity contract explicit before any tracked replay context, v1 eval config,
applicability adjudication, forest-plan component eval, or compliance-review artifact is pointed at
`source-set-f70ea11e04ae3d53`.

## Goal

Create or identify one governed source-record identity owner that can resolve the Lolo/Tyler's
Kitchen historical replay and eval source-record expectations against the current-workbook candidate
catalog without ad hoc command overrides, hidden source-ID rewrites, hash-only matching, or
review-specific special cases.

## Non-Goals

- Do not admit or promote the current-workbook source set into the Lolo/Tyler's Kitchen replay lane
  before the identity gate is green.
- Do not weaken v1 eval, phase-eval, applicability, compliance-review, forest-plan, or architecture
  thresholds to produce a passing result.
- Do not edit ignored generated artifacts by hand.
- Do not rerun broad downloader, network, or corpus-regeneration workflows.
- Do not implement Tyler's Kitchen-specific code paths when a generic identity resolver or contract
  is the required owner.

## Owner Surfaces

- Historical replay context:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
- Lolo v1 eval contract:
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`
- Applicability adjudication contract:
  `config/applicability_adjudications/region1-example-lolo-tylers-kitchen-66344.json`
- Forest-plan component eval contract:
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`
- Compliance source-record reconciliation:
  `config/compliance_source_record_reconciliation_v1.json`
- Forest-plan identity reconciliation:
  `config/r1_forest_plan_identity_reconciliation_v1.json`
- Current-workbook candidate catalog surface:
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl`
- Current-workbook candidate source-set manifest:
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json`
- Source-record identity, replay-context, eval, applicability, rule-claim, and forest-plan tests under
  `tests/`

Ignored `source_library/` artifacts remain local evidence unless repository policy changes.

## Weak-Point Prevention Contract

| Weak point forecast | Owner surface | Prevention gate | Fail threshold | Controlled violation | Future-Codex misuse scenario |
| --- | --- | --- | --- | --- | --- |
| Ad hoc source-set override bypasses the tracked replay context | replay context and replay CLI | Replay commands must use tracked config or fail with an intentional stop | Any successful replay that depends on an untracked `--source-set-id` mismatch | Negative case: mismatched `f70...` override must keep raising `ReplayContextMismatchError` | A future Codex run claims replay success by passing only command-line overrides |
| Current-workbook source IDs are substituted by hand | eval contracts and ignored generated review artifacts | Identity resolution must be owned by tracked config or a reusable resolver with tests | Any generated artifact or eval expectation edited manually to hide ID drift | Regression test or docs readback must show no ignored JSON patching | A future Codex run rewrites source IDs in outputs instead of fixing the identity owner |
| Compliance and forest-plan reconciliation remain split in practice | compliance reconciliation and forest-plan identity reconciliation | A single replay-facing gate must prove all Lolo expected IDs resolve to current catalog IDs | Any expected ID is unmapped, mapped to a missing current ID, or ambiguously mapped | Negative case: ambiguous or unmapped fixture fails the resolver gate | A future Codex run uses the compliance map for forest-plan IDs without proving coverage |
| Hash equality is treated as identity | extraction manifests and catalog rows | Hash matches may support evidence but cannot be the only owner contract | Any one-to-many or unmatched hash case feeds replay config without a governed mapping | Regression fixture covers one-to-many hash fanout | A future Codex run turns byte hash matches into a hidden source-record crosswalk |
| Eval threshold is relaxed to pass the rebaseline | v1 eval, phase-eval, and direct-eval configs | Existing eval and phase thresholds stay intact | Any skip, xfail, relaxed assertion, or lower threshold without explicit debt approval | Negative coverage proves stale or missing identity remains red | A future Codex run weakens gates to make Lolo look ready |
| Tyler's Kitchen receives special-case runtime branches | identity resolver and config loader | Resolver behavior must be source-set/review generic and fixture-covered | Any hard-coded review ID branch outside config loading and test fixtures | Regression fixture exercises a non-Tyler review or generic identity map | A future Codex run adds a one-off Tyler branch in shared runtime code |

## Milestone Sequence

| Milestone | Scope | Outcome label |
| --- | --- | --- |
| `0` | Identity coverage inventory | `reduced` |
| `1` | Unified source-record identity contract | `reduced` |
| `2` | Governed Lolo replay config update or exact stop | `reduced` |
| `3` | Parent route return | `resolved` |

### Milestone 0 - Identity Coverage Inventory

Status: Active next slice.

Implementation:

1. Read the Lolo v1 eval expected source-record IDs from
   `config/v1_lolo_tylers_kitchen_real_ea_eval.json`.
2. Compare those IDs against the current-workbook candidate source catalog and source-set manifest.
3. Compare absent historical IDs against the compliance source-record reconciliation and
   forest-plan identity reconciliation registries.
4. Produce a tracked evidence summary in this plan or a companion docs section with direct counts:
   direct current-workbook hits, compliance-reconciled hits, forest-plan-reconciled hits, missing
   IDs, ambiguous IDs, and mappings that point to records absent from the current catalog.

Acceptance:

- The inventory proves whether all 60 Lolo eval-expected IDs can resolve to records present in
  `source-set-f70ea11e04ae3d53`.
- Any missing or ambiguous identity is named exactly.
- No replay config or eval contract is changed in this milestone.

Verification:

```bash
PYTHONPATH=src python - <<'PY'
import json
from pathlib import Path

from usfs_r1_ea_sources.catalog_surface import catalog_source_record_ids

output_dir = Path("source_library")
catalog_path = output_dir / "runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl"
current_ids = catalog_source_record_ids(catalog_path)

contract = json.loads(Path("config/v1_lolo_tylers_kitchen_real_ea_eval.json").read_text())
expected = set(contract.get("baseline_policy", {}).get("expected_source_record_ids", []))
for item in contract.get("conditional_source_expectations", []):
    expected.update(item.get("expected_source_record_ids", []))
expected.update(contract.get("forest_plan", {}).get("required_source_record_ids", []))

print(
    {
        "expected": len(expected),
        "direct_current_hits": len(expected & current_ids),
        "missing_direct_current_hits": len(expected - current_ids),
    }
)
PY
```

Closeout state: `complete-after-commit` only after docs and handoff identify the exact next owner
for Milestone 1.

### Milestone 1 - Unified Source-Record Identity Contract

Status: Pending Milestone 0 inventory.

Implementation:

1. Choose the governed owner for replay-facing source-record identity. This may be a new generic
   identity resolver or an extension of an existing reconciliation module, but it must keep
   compliance and forest-plan identity data explicit and test-covered.
2. Add tests proving the resolver can map both ordinary source-record aliases and forest-plan source
   aliases into current catalog IDs.
3. Add a gate that fails on unmapped IDs, mapped IDs absent from the target catalog, and ambiguous
   mappings.
4. Keep the resolver generic. Review ID may select config fixtures; it must not select bespoke
   runtime branches.

Acceptance:

- All 60 Lolo v1 eval expected source-record IDs resolve to records present in the
  `source-set-f70ea11e04ae3d53` catalog surface, or the command stops with an exact missing/ambiguous
  ID report.
- Existing compliance and forest-plan reconciliation tests still pass.
- No replay context, eval contract, or adjudication config is changed until this contract is green.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_rule_claim_binding.py tests/test_forest_plan_identity_reconciliation.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Closeout state: `complete-after-commit` after implementation, tests, docs, and handoff prove the
identity contract is the replay-facing owner.

### Milestone 2 - Governed Lolo Replay Config Update Or Exact Stop

Status: Pending Milestone 1.

Implementation:

1. Only after the identity contract is green, update tracked Lolo replay and eval config surfaces to
   use the current-workbook candidate source-set owner or its governed identity resolver.
2. Run the smallest governed local replay chain needed for applicability, forest-plan component eval,
   compliance review, `v1-ea-eval`, and `phase-eval`.
3. If any command cannot consume the identity owner without runtime changes, stop and open the
   narrower implementation blocker instead of editing generated outputs or loosening gates.

Acceptance:

- Tracked config and review-local artifacts agree on one current-workbook source-set owner, or the
  exact command/surface that cannot consume the identity contract is named as the next blocker.
- `v1-ea-eval` and `phase-eval` are rerun after any replay.
- Roster/admission thresholds are unchanged.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval \
  --contract config/v1_lolo_tylers_kitchen_real_ea_eval.json \
  --output-dir source_library

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-example-lolo-tylers-kitchen-66344
```

Closeout state: `complete-after-commit` after replay evidence, docs, and handoff identify either a
green current-workbook replay baseline or the exact next blocker.

### Milestone 3 - Parent Route Return

Status: Pending Milestone 2.

Implementation:

1. Update this plan with the final identity outcome.
2. Update
   `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
   to resume or close its replay milestone.
3. Update routing, handoff, and current-state docs so agents land on the live packet rather than the
   older aligned-runtime or source-register parent plans.

Acceptance:

- `docs/CURRENT_ROUTING.md`, `docs/SESSION_HANDOFF.md`, `docs/CURRENT_SYSTEM_STATE.md`, and
  `docs/AGENT_START_HERE.md` name the same active packet and next milestone.
- Parent plans no longer imply that runtime alignment, source-register currentness, or source-set
  rebaseline is waiting on an uninspected replay command.

Verification:

```bash
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md
git diff --check
```

Closeout state: `complete-after-commit` after the parent route and this blocker agree.

## Required Documentation And Handoff Updates

Every milestone must update the affected subset of:

- `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`
- `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- `docs/CURRENT_ROUTING.md`
- `docs/SESSION_HANDOFF.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/AGENT_START_HERE.md`
- `docs/POST_V1_PROMOTION_SUITE.md`

## Required Verification Gates

Minimum closeout gate for every milestone:

```bash
git status -sb
git diff --check
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict \
  docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md
```

Behavior-changing milestones must also run the focused tests for the touched owner surface and
`PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py`. Replay-changing
milestones must rerun `v1-ea-eval` and `phase-eval` after replay.

## Stop Conditions

Stop and record the narrower blocker when:

- The current-workbook candidate catalog or source-set manifest is missing locally.
- Any expected Lolo eval source-record ID cannot be mapped to a current catalog record through a
  governed identity owner.
- A mapping points to more than one current record without an explicit conflict rule.
- A required replay or eval command cannot consume the identity owner without a generic runtime
  implementation change.
- Passing the milestone would require weakening tests, eval thresholds, roster thresholds, or
  citation requirements.

## Local Commit Closeout Policy

`complete-after-commit` rule: a milestone is not complete until verification
passes, durable docs and handoff updates land, and the local atomic commit
exists. A verified but uncommitted slice is ready-to-close only.

Each milestone closes with one atomic commit containing only the verified milestone slice:
implementation, tests, docs, and tracked evidence summaries. Ignored `source_library/` artifacts
remain unstaged unless the repository policy changes. Push only when explicitly requested.
