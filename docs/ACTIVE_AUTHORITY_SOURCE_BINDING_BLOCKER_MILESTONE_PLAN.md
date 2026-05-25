# Active Authority Source Binding Blocker Milestone Plan

Date: 2026-05-25

Status: Milestone 0 opened locally

Owner context: this is a fresh standalone blocker packet opened from
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` after Milestone `1`
replay work fixed ECID applicability universe routing bugs but still failed on
active-source authority coverage. It owns the governed authority-source
binding problem on `source-set-4fb59e9eb43045cb`. It does not reopen the
slot-driven promotion-suite contract packet, and it does not weaken the
reviewer-ready roster inside
`config/v1_real_package_review_coverage_v1.json`.

## Purpose

Restore truthful active-source authority binding for the reviewer-ready
applicability universe on `source-set-4fb59e9eb43045cb`.

The ECID replay-repair lane no longer fails first on mixed forest-plan
inventory shape or legacy source-ID aliasing. Those bugs are now repaired in
the applicability universe owners. The remaining blocker is upstream of
packet-local replay:

- `applicability-authority-universe` for
  `v1-cg-ecid-compliance-review` now rebuilds a correctly scoped authority
  universe with `candidate_authority_count=396` and
  `forest_plan_component_candidate_count=329`
- the same run still fails validation on
  `candidates_have_source_evidence_available` with `failure_count=21`
  and on
  `authority_family_template_candidates_cover_config` with
  `missing_source_record_count=19`
- because applicability validation cannot pass, generated reviewer-ready rule
  pack replay cannot resume truthfully, so the ECID reviewer-ready slot cannot
  be repaired inside the replay-local packet yet

This packet exists to classify and repair those authority-source binding gaps
through governed source-record reconciliation or active-source coverage, then
hand control back to the replay-repair packet.

## Current Evidence

- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/authority_universe_snapshot.json`
  now reports:
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `validation_passed=false`,
  `failed_check_names=["candidates_have_source_evidence_available","authority_family_template_candidates_cover_config"]`,
  `source_evidence_failure_count=21`, and
  `missing_source_record_count=19`.
- The mixed Region 1 inventory boundary is now behaving correctly for ECID:
  `selected_component_forest_unit_ids=["custer-gallatin-nf"]` even though the
  default `component_inventory.json` is a batch inventory with
  `forest_unit_id=null`.
- Existing governed reconciliation already covers some active aliases, for
  example `R1EA-150 -> ["USFS-035","LEX-USFS-002","LEX-USFS-003","LEX-USFS-004","LEX-USFS-006","LEX-USFS-007"]`,
  and the active rule-claim links already use those reconciled source records.
- Remaining blocker examples after the alias repair include missing active
  source bindings for authority-family and rule-pack references such as
  `R1EA-092`, `R1EA-032`, `R1EA-037`, `R1EA-041`,
  `R1PLAN-custer-gallatin-nf-06`, and
  `R1PLAN-region-1-species-overlay-01`.

## Goal

Repair the governed authority-source binding layer so the active applicability
universe can pass on `source-set-4fb59e9eb43045cb` without weakening source
evidence requirements.

Completion means all of the following are true:

- The missing authority-source IDs are classified as either:
  governed reconciliation gaps, true active-source coverage gaps, or obsolete
  references that must be removed only through governed source-truth owners.
- The selected owner surface is repaired with focused tests and durable docs.
- `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  passes on the active source set.
- The replay-repair packet can resume from truthful applicability validation
  instead of stale artifacts or bypasses.

## Non-Goals

- Do not relax `candidates_have_source_evidence_available`.
- Do not bypass the blocker with stale reviewer-ready artifacts from an older
  source set.
- Do not mark ECID or South Plateau as reviewer-ready until the active source
  binding problem is repaired.
- Do not reopen the promotion-suite selector/quorum contract packet.

## Owner Surfaces

- governed reconciliation and source-binding config:
  `config/compliance_source_record_reconciliation_v1.json`,
  `config/authority_family_rule_templates_nepa_ea_v1.json`,
  `config/compliance_rule_pack_nepa_ea_v0.json`,
  and any source-truth owner that legitimately governs missing active records
- applicability universe runtime owners:
  `src/usfs_r1_ea_sources/applicability_contract_support.py`,
  `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`,
  `src/usfs_r1_ea_sources/applicability_authority_family_templates.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_builder.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py`
- focused tests:
  `tests/test_applicability_candidate_assembly.py`,
  `tests/test_applicability_authority_family_templates.py`,
  `tests/test_applicability.py`,
  `tests/test_applicability_authority_universe_contracts.py`,
  `tests/test_applicability_authority_universe_builder.py`
- replay-routing docs:
  `README.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Milestone Sequence

### Milestone 0 - Missing Binding Baseline

Outcome label: opened

Purpose: freeze the post-repair blocker set before any governed source-binding
 edits begin.

Implementation:

1. Record the current failing authority-universe checks and counts on the
   active source set.
2. Separate already-fixed routing bugs from remaining missing authority-source
   binding failures.
3. Route this blocker packet from the replay-repair packet and current docs.

Acceptance criteria:

- The packet records the active `396`-candidate / `329`-component authority
  universe result and the remaining `21` source-evidence + `19` missing-source
  failures.
- Repo routing no longer claims ECID replay can continue directly from
  Milestone `1` inside the replay-local packet.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --source-set-id source-set-4fb59e9eb43045cb
```

### Milestone 1 - Classification And Owner Selection

Outcome label: resolved

Purpose: classify every remaining missing authority-source reference into the
correct governed owner.

Implementation:

1. Audit the failing source IDs against
   `config/compliance_source_record_reconciliation_v1.json`,
   active catalog evidence, and source-truth docs.
2. Split the failures into:
   reconciliation gaps,
   missing active source coverage,
   or obsolete references that must be retired through governed owners.
3. Write the resulting owner map back into this packet and the handoff.

Acceptance criteria:

- Every remaining blocker ID has one owner and one next command surface.
- No missing ID remains as an unclassified “maybe stale” note.

### Milestone 2 - Governed Repair

Outcome label: resolved

Purpose: repair the chosen owner surfaces without weakening applicability
validation.

Implementation:

1. Land the minimal governed config/code/source-truth changes required to make
   the active source set satisfy the missing authority-source bindings.
2. Add or update focused tests for the chosen repair.
3. Re-run the applicability universe on ECID until validation passes.

Acceptance criteria:

- `applicability-authority-universe` passes for ECID on
  `source-set-4fb59e9eb43045cb`.
- No new skips, xfails, or relaxed checks are introduced.

### Milestone 3 - Replay Resume Handoff

Outcome label: resolved

Purpose: return control to the replay-repair packet with the blocker removed.

Implementation:

1. Update routing docs so the active replay-repair packet resumes from ECID
   applicability validation rather than from stale reviewer-ready assumptions.
2. Record the exact replay-resume commands for the next packet.
3. Close this blocker packet with one local atomic commit.

Acceptance criteria:

- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` becomes the next
  truthful packet again only after this blocker is cleared.
- The docs name the exact resume command chain.
