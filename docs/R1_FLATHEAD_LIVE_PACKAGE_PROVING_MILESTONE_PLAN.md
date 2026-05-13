# Region 1 Flathead Live-Package Proving Milestone Plan

Date: 2026-05-12
Status: completed
Completed: 2026-05-13
Owner context: remaining Flathead-specific work after the Flathead profile-expansion and
direct-extraction-admission closeouts; target the first live Flathead reviewer-ready review on the
active full-canonical corpus

## Purpose

The remaining Flathead work is no longer profile depth, source completeness, or knowledge-base
admission. Those gates are already closed on `source-set-5e65d845ce77e1a0`.

The remaining gap is package-side proof: make one real Flathead EA package review pass the
reviewer-ready gate without weakening applicability, forest-plan evidence, component adjudication,
or phase-eval contracts.

This milestone uses the current West Reservoir package as the declared proving surface and closes
only the Flathead live-package gap. It does not reopen the implemented Flathead profile-expansion
milestone, and it does not widen into a broader multi-forest expansion pass.

## Closeout

- `west-reservoir-67436` is now the first live Flathead package review that closes green on the
  active full-canonical corpus. Review-bound `phase-eval` now passes `17/17` with
  `reviewer_ready=true`.
- Applicability is closed and replayable on tracked contracts:
  `applicability_validation.json` now reports `44` applicable authorities, `23` non-applicable
  authorities, `0` unresolved, `0` `needs_adjudication`, and `generated_rule_pack_ready=true`.
- The West Reservoir generated pack is now current and reviewer-ready:
  `generated_rule_pack_validation.json` passes with `44` rules under
  `generated-nepa-ea-v0-west-reservoir-67436`.
- Flathead supporting-plan evidence now validates with source-backed closure on the live package,
  and `forest_plan_context_validation.json` is green with `scope_status="flathead_nf"`.
- The Flathead component adjudication lane is complete and replayable on tracked adjudications:
  `forest_plan_component_adjudication_eval.json` now passes with `48` queue items,
  `48` resolved adjudications, `0` pending, and `reviewer_ready=true`.
- `compliance-review` now passes in generated-pack mode with `validation_passed=true`,
  `reviewer_ready=true`, and finding status counts `pass=26`, `uncertain=15`, `gap=3`.
- Review-local gold alignment is fresh for the same proving lane:
  `compliance_gold_eval_results.json` passes `10/10` cases with `promotion_ready=true`.
- The remaining Flathead-specific work is no longer this proving lane. Future work should route to
  the next selected post-V1 expansion or promotion boundary instead of reopening West Reservoir
  unless a new regression appears.

## Starting Evidence

- Flathead profile depth is already implemented in
  `docs/R1_FLATHEAD_PROFILE_EXPANSION_MILESTONE_PLAN.md`.
- Flathead direct extraction and knowledge-base admission are already implemented on
  `source-set-5e65d845ce77e1a0`; all `17` required `R1PLAN-flathead-nf-01..17` records are
  directly extracted and admitted with `0` blocked.
- The active full-canonical Flathead component inventory is already validated at `80` components
  and `20` standards on `source-set-5e65d845ce77e1a0`.
- The current live proving candidate is the local package at
  `/Users/chunkstand/Downloads/West Reservoir (67436)`, reviewed as `review_id=west-reservoir-67436`
  on `source-set-5e65d845ce77e1a0`.
- `ea-review` already passes for West Reservoir with `12` package files, `659` package chunks,
  `5/5` checklist findings `pass`, and `reviewer_ready=true` at the package-checklist layer.
- Review-bound `phase-eval` does not pass. Current artifact truth in
  `source_library/reviews/west-reservoir-67436/phase_eval_results.json` is `11/16` phases passed,
  `reviewer_ready=false`, with blockers in:
  `authority_universe`,
  `applicability_validation`,
  `generated_rule_pack`,
  `compliance_gold_eval`, and
  `compliance_review`.
- Applicability currently fails in
  `source_library/reviews/west-reservoir-67436/applicability/applicability_validation.json`
  because `3` authority families remain unresolved:
  `clean_air_act_conformity_air_quality`,
  `species_supporting_sources_and_overlays`, and
  `vegetation_wildfire_forest_health_authorities`.
- The generated-rule-pack gate is still open because
  `source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json` does not
  yet exist.
- Flathead forest-plan context is selected correctly as `scope_status="flathead_nf"`, but
  `source_library/reviews/west-reservoir-67436/forest_plan_context_validation.json` still fails
  `triggered_supporting_plan_evidence_has_source_evidence`.
- The six currently triggered Flathead supporting-plan routes missing source-evidence closure are:
  `support-bull-trout-biological-opinion`,
  `support-esa-biological-assessment`,
  `support-feis-plan-context`,
  `support-grizzly-biological-opinion`,
  `support-monitoring-program`, and
  `support-rod-decision-basis`.
- The current West Reservoir component queue is `80` items in
  `source_library/reviews/west-reservoir-67436/forest_plan_component_adjudication_template.json`,
  with reason counts:
  `missing_package_evidence=54`,
  `missing_plan_source_evidence=18`, and
  `needs_reviewer_resolution=8`.
- `source_library/reviews/west-reservoir-67436/forest_plan_context_summary.json` records
  `component_adjudication.eval_exists=false`, so the component-adjudication eval artifact is still
  missing.
- `source_library/reviews/west-reservoir-67436/compliance_validation.json` currently fails only:
  `applicability_generated_rule_pack_gate` and
  `forest_plan_component_gate_reviewer_ready`.
- `source_library/reviews/west-reservoir-67436/phase_eval_results.json` shows the current
  `compliance_gold_eval` failure is not a Flathead extraction problem; it is a proving-lane issue
  caused by stale review-local gold alignment (`source_set_mismatch` and
  `gold_eval_not_promotion_ready`).

## Goal

Make `west-reservoir-67436` the first live Flathead package review that passes the full
reviewer-ready boundary on `source-set-5e65d845ce77e1a0`.

Completion means:

- applicability validates with `0` unresolved and `0` `needs_adjudication` decisions;
- a current generated rule pack exists and validates for the West Reservoir review;
- Flathead forest-plan context validates with the required supporting-plan source evidence;
- the Flathead component adjudication/eval lane is complete and reviewer-ready;
- `compliance-review` passes with the generated rule pack, not base-pack diagnostic mode;
- review-local `compliance-gold-eval` is fresh for the same source set and reviewer-ready pack;
- `phase-eval --review-id west-reservoir-67436` passes green and reports `reviewer_ready=true`.

## Non-Goals

- Do not reopen the implemented Flathead profile-expansion milestone except where package-proof
  defects require narrow supporting fixes.
- Do not widen this plan into a multi-forest expansion or promotion-suite milestone.
- Do not replace the live-package claim with a synthetic-only proving fixture.
- Do not weaken `forest_plan_component_gate_reviewer_ready`,
  `applicability_generated_rule_pack_gate`, or review-bound `phase-eval` just to get a green run.
- Do not stage ignored `source_library/` artifacts.
- Do not turn unresolved reviewer judgments into hidden automatic passes.
- Do not claim that one green West Reservoir review makes every future Flathead package
  reviewer-ready.

## Scope

- current local package boundary:
  `/Users/chunkstand/Downloads/West Reservoir (67436)`
- review-local ignored artifacts under:
  `source_library/reviews/west-reservoir-67436/`
- tracked replay context:
  `config/replay_contexts/west-reservoir-67436.json`
- tracked applicability adjudication contract:
  `config/applicability_adjudications/west-reservoir-67436.json`
- tracked forest-plan component adjudication contract:
  `config/forest_plan_component_adjudications/west-reservoir-67436.json`
- tracked forest-plan component eval contract, if needed:
  `config/forest_plan_component_evals/west-reservoir-67436.json`
- generic review/runtime surfaces only where the West Reservoir blockers prove they are needed:
  `src/usfs_r1_ea_sources/replay_context.py`,
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_validation.py`,
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`,
  `src/usfs_r1_ea_sources/forest_plan_component_adjudication.py`,
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/evidence_graph.py`, and
  `src/usfs_r1_ea_sources/phase_eval.py`
- focused regression surfaces:
  `tests/test_applicability_decisions.py`,
  `tests/test_forest_plan_resolver.py`,
  `tests/test_compliance_review.py`,
  `tests/test_forest_plan_component_adjudication.py`,
  `tests/test_replay_context.py`,
  `tests/test_cli.py`, and
  `tests/test_architecture_contract.py`
- durable docs for this lane:
  `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  this plan, and
  `docs/SESSION_HANDOFF.md`

## Out Of Scope

- new Flathead source capture, parser recovery, or extraction-admission work
- broader Flathead graph-promotion work; the graph is already updated
- Beaverhead, Bitterroot, Dakota Prairie, Helena-Lewis-and-Clark, Idaho Panhandle, Kootenai,
  Lolo, or Nez Perce-Clearwater profile work
- East Crazies replay repair
- promotion-suite manifest changes unless a later closeout proves they are necessary for this
  review-specific claim

## Owner Surfaces

- proving review identity and catalog/source-set routing:
  `config/replay_contexts/west-reservoir-67436.json`,
  `src/usfs_r1_ea_sources/replay_context.py`,
  `tests/test_replay_context.py`
- applicability conflict closure:
  `config/applicability_adjudications/west-reservoir-67436.json`,
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_validation.py`,
  `tests/test_applicability_decisions.py`
- Flathead supporting-plan evidence and context routing:
  `config/forest_plan_profiles.json` only if a proven package-side bug requires a narrower
  Flathead route repair,
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`,
  `tests/test_forest_plan_resolver.py`
- component adjudication and eval contract:
  `config/forest_plan_component_adjudications/west-reservoir-67436.json`,
  `config/forest_plan_component_evals/west-reservoir-67436.json`,
  `src/usfs_r1_ea_sources/forest_plan_component_adjudication.py`,
  `tests/test_forest_plan_component_adjudication.py`
- reviewer-ready compliance and review-bound eval:
  `src/usfs_r1_ea_sources/compliance_review.py`,
  `src/usfs_r1_ea_sources/compliance_gold_eval.py`,
  `src/usfs_r1_ea_sources/phase_eval.py`,
  `tests/test_compliance_review.py`,
  `tests/test_cli.py`
- status routing and closeout:
  `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  this plan, and
  `docs/SESSION_HANDOFF.md`

## Placement Rules

- Keep the proving package contract explicit. Use tracked replay context under
  `config/replay_contexts/west-reservoir-67436.json`; do not bury the review/source-set binding in
  chat or ad hoc shell history.
- Keep human review decisions replayable. Applicability and component adjudications must live in
  tracked config files, not only in edited JSON under `source_library/reviews/`.
- Keep runtime logic generic. Do not add `if review_id == "west-reservoir-67436"` or other
  one-off review special cases.
- Keep Flathead profile data as the source of forest-plan knowledge. Only change
  `config/forest_plan_profiles.json` if the live West Reservoir review proves a concrete package
  routing defect.
- Do not convert the `80`-item component queue into a pass by loosening the reviewer gate. Reduce
  deterministic system misses first, then adjudicate the residual queue explicitly.
- Do not call the base-rule-pack diagnostic review reviewer-ready. This milestone closes only from
  the generated rule-pack path.

## Weak-Point Prevention Contract

### Weak point 1: the live-package claim drifts back into an untracked or synthetic proving surface

- Weak point forecast: a future session may reuse the West Reservoir review ID but silently point at
  a different package or fall back to synthetic fixtures while still claiming live-package proof.
- Owner surface: `config/replay_contexts/west-reservoir-67436.json`, this plan, and the handoff
- Prevention gate: tracked replay-context validation plus review-bound `phase-eval`
- Fail threshold: the review ID, source set, or catalog/source-set routing no longer matches the
  declared proving contract
- Controlled violation: `tests/test_replay_context.py` or review-bound phase replay fails if the
  replay context drifts
- Future-Codex misuse scenario: a future session reruns the review against a different source set
  and keeps the old review ID; this milestone prevents that through tracked replay context

### Weak point 2: applicability is forced green without replayable adjudication

- Weak point forecast: the three unresolved authority-family conflicts could be patched by editing
  partition artifacts or by suppressing the unresolved-decision gate
- Owner surface: `config/applicability_adjudications/west-reservoir-67436.json`,
  `applicability_validation.py`, and `tests/test_applicability_decisions.py`
- Prevention gate: `applicability-adjudication-eval`, `applicability-adjudication-apply`,
  `applicability-validate`, and `applicability-generate-rule-pack --validate-only`
- Fail threshold: any unresolved or `needs_adjudication` decision remains, or the generated pack is
  missing/stale
- Controlled violation: negative tests and validation checks fail if the partition leaves any of the
  three current authority families unresolved
- Future-Codex misuse scenario: a future session edits `applicable_authorities.json` directly; this
  milestone requires tracked adjudication plus regenerated provenance

### Weak point 3: Flathead supporting-plan evidence is overmatched or left ungrounded

- Weak point forecast: the six triggered support routes may be satisfied by broad lexical matching
  instead of source-backed evidence, or left red while the review still claims readiness
- Owner surface: `forest_plan_resolver.py`, `forest_plan_context_validation.json`, and
  `tests/test_forest_plan_resolver.py`
- Prevention gate: `forest-plan-resolve` or `compliance-review` with validation of
  `triggered_supporting_plan_evidence_has_source_evidence`
- Fail threshold: any of the six currently triggered routes remains without source-backed closure,
  or background-only references start satisfying them
- Controlled violation: add or preserve negative fixtures for generic FEIS/ROD/monitoring language
  and positive fixtures for explicit route cues
- Future-Codex misuse scenario: a future session broadens support triggers just to erase the queue;
  this milestone preserves fail-closed supporting-route tests

### Weak point 4: the component queue is closed by weakening the reviewer gate instead of resolving system misses and adjudicating the rest

- Weak point forecast: the `80`-item queue could be cleared by changing finding status rules or by
  hiding unresolved component items from the gate
- Owner surface: `forest_plan_component_adjudication.py`,
  `config/forest_plan_component_adjudications/west-reservoir-67436.json`,
  `config/forest_plan_component_evals/west-reservoir-67436.json`, and
  `tests/test_forest_plan_component_adjudication.py`
- Prevention gate: `forest-plan-component-adjudication-eval`, optional
  `forest-plan-component-eval`, and `forest_plan_component_gate_reviewer_ready` inside
  `compliance_validation.json`
- Fail threshold: pending component adjudications remain, the adjudication eval artifact is
  missing, or the compliance gate turns green while unresolved queue items still exist
- Controlled violation: queue-driven tests fail if adjudication metadata is incomplete or if the
  reviewer gate ignores an open queue
- Future-Codex misuse scenario: a future session edits the queue or findings in `source_library/`
  directly; this milestone requires tracked adjudication contracts and replayable evals

### Weak point 5: review-bound gold eval stays stale or non-promotion-ready

- Weak point forecast: the review could still fail phase eval because it reads a stale global gold
  result or a base-pack diagnostic gold run
- Owner surface: `compliance_gold_eval.py`, `phase_eval.py`, and review-local gold artifacts under
  `source_library/reviews/west-reservoir-67436/`
- Prevention gate: review-local `compliance-gold-eval` using the reviewer-ready generated rule pack
  and matching source set
- Fail threshold: `compliance_gold_eval` still reports `source_set_mismatch`,
  `gold_eval_not_promotion_ready`, or missing review-local results
- Controlled violation: review-bound phase replay fails if the gold artifact is stale or written for
  the wrong pack/source set
- Future-Codex misuse scenario: a future session assumes the current global gold result is good
  enough; this milestone requires review-local gold freshness

### Weak point 6: docs claim Flathead is fully resolved while West Reservoir is still red

- Weak point forecast: README or current-state prose may overstate Flathead readiness from profile
  and extraction proof alone
- Owner surface: `README.md`, `docs/CURRENT_SYSTEM_STATE.md`, this plan, and the handoff
- Prevention gate: review-bound `phase-eval` plus doc refresh in the same milestone slice
- Fail threshold: docs claim the remaining Flathead work is closed before
  `phase-eval --review-id west-reservoir-67436` passes green
- Controlled violation: leave a red phase-eval and confirm docs still describe the lane as pending
- Future-Codex misuse scenario: a future session copies an old “Flathead is done” claim from the
  profile-expansion closeout into current-state docs; this milestone keeps package-proof truth tied
  to the live review artifact

## Milestone Sequence

### Sequence 0: Lock the proving review contract and baseline

Outcome label: resolved

- Create tracked replay context for `west-reservoir-67436` under
  `config/replay_contexts/west-reservoir-67436.json`, bound to
  `source-set-5e65d845ce77e1a0` and the active canonical catalog.
- Reconfirm the live package checklist baseline on the current local West Reservoir package.
- Record the current baseline blocker set in the handoff and this plan:
  `11/16` phases passed,
  `3` unresolved applicability families,
  `6` missing supporting-plan source-evidence routes, and
  `80` component-adjudication queue items.
- Freeze the review ID, source set, catalog boundary, and package path before changing
  applicability or compliance logic.

Required implementation artifacts:

- `config/replay_contexts/west-reservoir-67436.json`
- this plan
- `docs/SESSION_HANDOFF.md`

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path '/Users/chunkstand/Downloads/West Reservoir (67436)' \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --review-id west-reservoir-67436

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id west-reservoir-67436
```

### Sequence 1: Resolve applicability and generate the reviewer-ready rule pack

Outcome label: resolved

- Complete a tracked applicability adjudication contract for the three currently unresolved
  authority families in `config/applicability_adjudications/west-reservoir-67436.json`.
- Evaluate and apply the adjudication against the live West Reservoir decision set.
- If `authority_universe` still fails after adjudication, repair the generic
  authority-universe/component-candidate contract so the review no longer carries a hidden
  `forest_plan_component_candidate_count=0` validation failure.
- Regenerate and validate the reviewer-ready generated rule pack.

Required implementation artifacts:

- `config/applicability_adjudications/west-reservoir-67436.json`
- any minimal generic applicability or validation/runtime fixes required by the live failure
- focused tests in `tests/test_applicability_decisions.py` and adjacent review tests if the generic
  contract changes

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval \
  --output-dir source_library \
  --review-id west-reservoir-67436 \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --adjudication-file config/applicability_adjudications/west-reservoir-67436.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply \
  --output-dir source_library \
  --review-id west-reservoir-67436 \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --adjudication-file config/applicability_adjudications/west-reservoir-67436.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id west-reservoir-67436 \
  --source-set-id source-set-5e65d845ce77e1a0

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id west-reservoir-67436 \
  --source-set-id source-set-5e65d845ce77e1a0
```

### Sequence 2: Repair Flathead supporting-plan evidence and deterministic component misses

Outcome label: reduced

- Close the six currently triggered supporting-plan routes that still lack source-backed evidence.
- Re-run the Flathead forest-plan review path and verify that
  `triggered_supporting_plan_evidence_has_source_evidence` passes.
- Inspect the `80`-item component queue and fix deterministic system-side misses first:
  `missing_plan_source_evidence`,
  package-evidence linking misses,
  section-chunking misses,
  retrieval misses, and
  applicability false positives where proven.
- Regenerate the component adjudication template after system-side fixes and keep the residual queue
  explicit for Sequence 3.

This sequence is intentionally `reduced`, not `resolved`, because the residual reviewer queue must
still be adjudicated before the reviewer-ready gate can close.

Required implementation artifacts:

- narrow Flathead route fixes in `config/forest_plan_profiles.json` only if the package proves the
  current route contract is incomplete
- any minimal generic forest-plan resolver or evidence-linking fixes required by the live review
- updated tests in `tests/test_forest_plan_resolver.py` and `tests/test_compliance_review.py`

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path '/Users/chunkstand/Downloads/West Reservoir (67436)' \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --review-id west-reservoir-67436 \
  --forest-unit-id flathead-nf \
  --rule-pack source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template \
  --output-dir source_library \
  --review-id west-reservoir-67436
```

### Sequence 3: Close the Flathead component-adjudication lane

Outcome label: resolved

- Complete the residual West Reservoir component adjudication contract in tracked config under
  `config/forest_plan_component_adjudications/west-reservoir-67436.json`.
- Run `forest-plan-component-adjudication-eval` and require `0` pending adjudications.
- If a replay-scoped component eval contract is needed to keep future drift measurable, add
  `config/forest_plan_component_evals/west-reservoir-67436.json` and run
  `forest-plan-component-eval` against it.
- Do not close this sequence while unresolved system misses still masquerade as reviewer
  adjudications; if systematic misses remain, loop back into Sequence 2 first.

Required implementation artifacts:

- `config/forest_plan_component_adjudications/west-reservoir-67436.json`
- `config/forest_plan_component_evals/west-reservoir-67436.json` if the live closure needs a
  tracked replay-scoped component contract
- any focused component-adjudication tests required by generic behavior changes

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval \
  --output-dir source_library \
  --review-id west-reservoir-67436 \
  --adjudication-file config/forest_plan_component_adjudications/west-reservoir-67436.json

PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval \
  --output-dir source_library \
  --review-id west-reservoir-67436 \
  --eval-file config/forest_plan_component_evals/west-reservoir-67436.json
```

### Sequence 4: Prove reviewer-ready compliance and review-local gold alignment

Outcome label: resolved

- Rerun `compliance-review` with the generated applicability rule pack, the Flathead selected
  profile, and `--reuse-package-cache`.
- Write a review-local `compliance_gold_eval_results.json` under
  `source_library/reviews/west-reservoir-67436/` using the current reviewer-ready generated rule
  pack and the current source set.
- Rerun review-bound `phase-eval` and require all current West Reservoir phases to pass green.

Required implementation artifacts:

- any minimal generic compliance or phase-eval fixes required by the live review path
- focused tests in `tests/test_compliance_review.py`, `tests/test_cli.py`, and
  `tests/test_architecture_contract.py` if generic behavior changes

Required verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path '/Users/chunkstand/Downloads/West Reservoir (67436)' \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --review-id west-reservoir-67436 \
  --forest-unit-id flathead-nf \
  --rule-pack source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --source-set-id source-set-5e65d845ce77e1a0 \
  --rule-pack source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json \
  --gold-file config/compliance_gold_eval_v0.json \
  --results-dir source_library/reviews/west-reservoir-67436

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id west-reservoir-67436
```

### Sequence 5: Close out docs, handoff, and the remaining Flathead live-package gap

Outcome label: resolved for the remaining Flathead live-package proving gap; reduced for the
broader post-V1 multi-forest expansion lane

- Refresh repo docs and handoff with the actual green West Reservoir state, exact verification
  commands, pass counts, and residual risk boundary.
- Keep the stronger distinctions explicit:
  profile-depth proof,
  source-document extraction proof, and
  live-package proving proof.
- If the implementation changed generic review/compliance/eval behavior, run the required focused
  test suite, `ruff`, `compileall`, and `git diff --check` before commit.

Required implementation artifacts:

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

Required verification:

```bash
PYTHONPATH=src uv run --extra dev pytest \
  tests/test_applicability_decisions.py \
  tests/test_forest_plan_resolver.py \
  tests/test_forest_plan_component_adjudication.py \
  tests/test_compliance_review.py \
  tests/test_replay_context.py \
  tests/test_cli.py \
  tests/test_architecture_contract.py

PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

## Required Implementation Artifacts

- `config/replay_contexts/west-reservoir-67436.json`
- `config/applicability_adjudications/west-reservoir-67436.json`
- `config/forest_plan_component_adjudications/west-reservoir-67436.json`
- `config/forest_plan_component_evals/west-reservoir-67436.json` if replay-scoped component-eval
  coverage is needed
- review-local generated artifacts under `source_library/reviews/west-reservoir-67436/`
- only the minimal generic runtime or test changes required by the live West Reservoir blockers

## Required Documentation And Handoff Updates

Before milestone closeout, update as applicable:

- `README.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- this plan
- `docs/SESSION_HANDOFF.md`

The handoff update must record:

- the completed milestone name
- the fixed review ID `west-reservoir-67436`
- the fixed source set `source-set-5e65d845ce77e1a0`
- the declared West Reservoir package path used for the live proving run
- exact verification commands
- pass/fail counts
- whether any tracked adjudication contracts were added
- residual risks
- the closing commit hash
- the next routing boundary after Flathead live-package proof

## Required Verification Gates

Applicability and rule-pack gates:

- `applicability-adjudication-eval`
- `applicability-adjudication-apply`
- `applicability-validate`
- `applicability-generate-rule-pack`

Flathead forest-plan gates:

- `compliance-review` with the generated West Reservoir rule pack and `--forest-unit-id flathead-nf`
- `forest-plan-component-adjudication-template`
- `forest-plan-component-adjudication-eval`
- `forest-plan-component-eval` if a replay-scoped component contract is added

Review-bound promotion gates:

- review-local `compliance-gold-eval` written under `source_library/reviews/west-reservoir-67436/`
- `phase-eval --review-id west-reservoir-67436`

Focused regression gates when code changes:

- `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_adjudication.py`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_review.py tests/test_cli.py`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_replay_context.py tests/test_architecture_contract.py`

Repository hygiene:

- `PYTHONPATH=src uv run --extra dev ruff check src tests`
- `PYTHONPATH=src python -m compileall src`
- `git diff --check`

## Acceptance Criteria

- `config/replay_contexts/west-reservoir-67436.json` exists and binds the proving review to
  `source-set-5e65d845ce77e1a0`.
- West Reservoir applicability validation passes with `0` unresolved and `0`
  `needs_adjudication` decisions.
- The three currently unresolved authority families are closed through a replayable tracked
  adjudication contract, not by hand-editing generated outputs.
- `source_library/reviews/west-reservoir-67436/applicability/generated_rule_pack.json` exists,
  validates, and is current.
- `forest_plan_context_validation.json` passes and the six currently triggered Flathead
  supporting-plan routes no longer fail `triggered_supporting_plan_evidence_has_source_evidence`.
- The West Reservoir component adjudication contract evaluates green with no pending items, and the
  reviewer-ready component gate no longer fails.
- `compliance_validation.json` passes without
  `applicability_generated_rule_pack_gate` or
  `forest_plan_component_gate_reviewer_ready` failures.
- Review-local `compliance_gold_eval_results.json` for West Reservoir is fresh for
  `source-set-5e65d845ce77e1a0` and does not fail on `gold_eval_not_promotion_ready` or
  `source_set_mismatch`.
- `phase-eval --review-id west-reservoir-67436` passes green and reports `reviewer_ready=true`.
- Durable docs and handoff accurately separate Flathead profile completion from Flathead
  live-package proof.
- The milestone closes with one local atomic commit containing only the verified Flathead
  live-package slice.

## Stop Conditions

- The local West Reservoir package is unavailable, materially different from the declared proving
  package, or cannot be kept stable enough for a replayable contract.
- Applicability or component closure would require direct edits under `source_library/` instead of
  replayable tracked contracts and reruns.
- Fixing the remaining Flathead blockers would require a broader repo-wide gold-eval or review-pack
  redesign outside this milestone boundary.
- The residual component queue is dominated by generic retrieval/chunking/evidence-linking defects
  that need a separate system repair milestone before reviewer adjudication can be trusted.
- Required verification fails.
- Unrelated dirty work cannot be isolated from the verified milestone slice.

## Local Commit Closeout Policy

- Stage only the verified Flathead live-package milestone slice.
- Leave unrelated viewer changes, draft exports, and other dirty or untracked files alone.
- Include implementation, tests, tracked adjudication contracts, plan updates, current-state
  updates, and handoff updates in the same local atomic commit.
- Record the closing commit hash in `docs/SESSION_HANDOFF.md`.
- Treat the milestone as incomplete until that commit exists.

## Residual Risks And Next Milestone Routing

- A green West Reservoir review proves one live Flathead package, not every future Flathead EA
  package.
- If the milestone closes with minimal Flathead profile-data changes, the stronger claim remains
  package-side proof rather than a new profile-expansion milestone.
- If generic system misses remain after West Reservoir review closure, route them into a separate
  evidence-linking or component-evaluation repair milestone rather than hiding them in Flathead
  docs.
- If this milestone closes green, the next forest-specific proving lane should be either:
  1. another selected remaining non-Custer forest live-package proving milestone; or
  2. a broader post-V1 expansion-routing milestone that uses Beaverhead, Flathead, and West
     Reservoir as completed reference slices.
