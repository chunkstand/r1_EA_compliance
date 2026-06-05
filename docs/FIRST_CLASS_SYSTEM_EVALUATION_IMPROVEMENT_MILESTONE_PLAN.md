# First-Class System Evaluation Improvement Milestone Plan

Date: 2026-06-04
Status: Milestone 4 Final QA, review-packet, and decision-support direct-eval slices implemented
Plan class: implementation
High-risk implementation: yes
Owner context: repo-native goal for making evaluations the improvement control plane for the USFS
R1 EA reviewer-engine pipeline, with applicability as the first ratcheted subsystem.

## Purpose And Current Evidence

Broader goal: make each material pipeline change pass through artifact lineage, deterministic direct
eval, failure intake, scoped ratchet, and current-state/handoff truth.

The repo already has eval/trace storage, direct-eval-aware phase-eval, an observability/eval context
graph, and a coverage register. Applicability has the first scoped ratchet; later-stage gates need
the same pattern. The goal is staged measurement, not graph publication.

Current evidence: coverage register tracks subsystem status; eval-trace owns storage/export,
tracked case promotion, and case-file validation; phase-eval consumes direct-eval artifacts; the
first scoped applicability ratchet is active for West Reservoir/f70; and Milestone 4 adds Final QA,
review-packet, and decision-support direct eval plus promotion gates for East Crazies/f70.

## Goal, Non-Goals, And Scope

Goal: turn each pipeline boundary into a measured loop, starting with applicability, and widen only
after scoped evidence proves identity, freshness, replayability, and non-regression.

Completion means:

- every pipeline stage has an owner, direct-eval or explicit gap, metrics, artifacts, and intake;
- applicability reports coverage, retrieval/graph trace quality, partition fidelity, rule-pack
  fidelity, gate-graph consistency, Forest Plan subgates, and hard negatives;
- failures promote into tracked cases with source-set, review, source-record, citation, artifact,
  trace, and scorer provenance;
- phase-eval fails closed for one explicit scoped applicability ratchet before widening; and
- docs/handoff explain evaluated steps, gaps, and proving gates.

Non-goals:

- Do not replace existing domain eval commands or the eval-trace SQLite substrate.
- Do not add model-judge or hosted scoring as a gate before deterministic and human-label contracts
  exist.
- Do not make global fail-closed ratchets or wildcard source-set/review scopes.
- Do not mutate ignored production `source_library/` as the primary proof path.
- Do not implement compliance-review consumption of the applicability gate graph in the first
  applicability-eval milestone unless that proves necessary for measurement.

Scope:

- Applicability owner surfaces, contracts, fixtures, summaries, traces, and phase-eval integration.
- Coverage-register status for every step.
- Eval-trace case promotion for applicability and later-stage failures.
- One scoped ratchet before rollout.

## Intent Hierarchy

- North-star intent: evals are the system's learning loop; replayable evidence must show a review
  boundary became more reliable, observable, or governable.
- Invariant: source-set, review, workbook row, source-record, citation, artifact hash, trace hash,
  and scorer contract identity stay visible through evals, cases, ratchets, and promotion claims.
- Optimization target: deterministic metrics, hard negatives, failure cases, and scoped gates before
  breadth or UI/product expansion.
- Acceptable tradeoffs: fixture or manifest coverage may precede full live replay when it preserves
  readiness and names the widening gate.
- Explicit non-negotiables: no hidden heuristics, global ratchets, uncalibrated model judges, stale
  generated proof, or weakened gates.
- Intent lock: this advances eval-governed improvement of the reviewer-engine; it does not open
  hosted scoring, broad promotion, compliance gate-graph consumption, or graph publication.

## Owner Surfaces And Placement

- Evaluation coverage truth: `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_ROUTING.md`, `docs/SESSION_HANDOFF.md`.
- Existing first-class substrate: eval-trace contract/config/cases and eval-trace modules.
- Applicability implementation and eval owners: applicability modules, eval seed/gold files, and
  gate-graph config.
- Phase and promotion consumers: phase-eval direct-eval config/modules and promotion suite config.
- Tests: focused applicability eval, phase-eval direct-eval, eval-trace case-promotion, and
  architecture-contract tests.

Placement rules:

- Add new applicability eval orchestration in focused applicability-owned helpers. Do not enlarge
  phase-eval or compliance-review with scorer implementation details.
- Keep domain truth in domain eval artifacts; the eval-trace store indexes and links results but
  must not synthesize pass/fail decisions.
- Keep ratchets explicit by source-set or review ID. A scoped ratchet must prove no unrelated lane
  is blocked before it can enter phase-eval or promotion.

## Anti-Test-Weakening Rule

Do not delete, skip, xfail, narrow, or loosen existing applicability, phase-eval, compliance,
eval-trace, or architecture tests to make a new evaluator pass. Replacement coverage is allowed
only when it proves the old assertion was pointed at the wrong contract and the replacement is
equivalent or stronger. Any approved temporary weakening must be recorded in
`docs/TECH_DEBT_REGISTER.md` with owner, reason, and removal condition before closeout.

## Weak-Point Prevention

| Weak point | Owner surface | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| Applicability looks green while critical families regress | `applicability_eval.py`, `config/applicability_gold_eval_v1.json` | Per-family floors, hard negatives, prior-failure replay | Critical family below floor or prior failure regresses |
| Retrieval/graph traces are present but unscored | applicability trace/eval helpers | Score coverage, evidence quality, no-evidence certificates, and graph support | Decision passes without scored positive or negative trace evidence |
| Generated rule pack drifts from applicability partition | generated-rule-pack validation and phase-eval | Compare applicable, omitted, unexpected, and generated rules | Missing or extra generated rule passes |
| Gate graph becomes structural-only decoration | applicability gate graph and gate-graph eval | Eval parent/child open/closed/blocked consistency against decisions | Gate state contradicts applicability decisions |
| Failures stay as logs instead of learning cases | eval-trace case promotion and applicability case files | Promote selected failures with source refs, hashes, assertion, owner, risk, review/removal conditions | Failed case cannot be replayed from tracked artifacts |
| Global ratchet blocks unrelated work | `phase_eval_direct_eval_v1.json`, `eval_trace_gate.py` | One scoped ratchet first; no wildcard scopes | Missing scoped proof or wildcard ratchet |

## Milestone Sequence

### Milestone 0 - System Evaluation Coverage Goal And Gap Register

Outcome label: reduced.

- Update the coverage register so every pipeline step has one of:
  `direct_eval_present`, `direct_eval_strengthening_planned`, or `direct_eval_missing`.
- Add applicability sub-rows for authority universe, retrieval trace, graph trace, decision
  partition, generated rule pack, gate graph, Forest Plan subgate, and adjudication/failure intake.
- Record the first scoped applicability ratchet target and the stop conditions for widening it.

Closeout note: docs-only coverage register update. No runtime gate, hosted scorer, or model judge
changed.

### Milestone 1 - Applicability Direct-Eval Contract Hardening

Outcome label: reduced.

- Add or extend applicability eval contract coverage for authority-family floors, hard negatives,
  Forest Plan component/subgate cases, unresolved/adjudication-needed cases, generated-rule-pack
  partition fidelity, and gate-graph consistency.
- Emit summary metrics that can be indexed by eval-trace inventory and read by phase-eval.
- Add focused tests proving missing categories, wrong source-set/review identity, stale trace
  hashes, wrong generated-rule partitions, and gate-graph contradictions fail closed.

Closeout note: summary-contract, Forest Plan subgate, and trajectory/process scoring slices are
implemented in the scoped ratchet.

### Milestone 2 - Applicability Failure Intake And Trace-To-Case Promotion

Outcome label: resolved.

- Route applicability failures into durable promoted cases or domain case fixtures with preserved
  source-set, review, source-record, citation, artifact hash, trace, scorer, owner, risk, assertion,
  review condition, and removal condition.
- Add replay tests for at least one promoted failure from retrieval evidence, one from decision
  partition drift, and one from generated rule-pack drift.

Closeout note: reduced by failure-intake artifacts with hashes, lineage, assertions, scorer
metadata, lifecycle fields, and human-label placeholders. Trace-to-case promotion now has one
tracked West Reservoir/f70 retrieval case plus case-file validation.

### Milestone 3 - Scoped Applicability Phase-Eval Ratchet

Outcome label: resolved.

- Add an explicit applicability direct-eval phase for one governed review/source-set scope.
- Prove phase-eval fails closed on missing, stale, mismatched, or below-threshold applicability
  eval summaries and remains non-blocking for unrelated scopes.
- Update promotion consumers only if the selected governed scope already participates in promotion.

Closeout note: implemented for `west-reservoir-67436` on `source-set-f70ea11e04ae3d53`; tests
prove fail-closed and unrelated-review behavior. No global ratchet was added.

Live proof note: f70 `applicability-eval` passes `10/10`; West Reservoir/f70 `phase-eval`
passes `36/36` with `applicability_validation=direct_eval_present` and `blockers=[]`.

Trajectory note: the ratchet now requires `trajectory_process_quality` with no expected gaps.

### Milestone 4 - All-Step Evaluation Expansion

Outcome label: reduced.

- Repeat the Milestone 0-3 pattern for remaining gaps in capture, catalog, extraction, retrieval,
  evidence graph, source claims, rule binding, compliance, review packet, final QA, document
  generation, and promotion.
- Keep each expansion as a separate bounded packet with its own owner surfaces, metrics, fixtures,
  phase-eval or promotion gates, docs, and commit closeout.

Closeout note: Milestone 4 now has current-promotion `final-qa-direct-eval`,
`review-packet-direct-eval`, and `ea-consistency-direct-eval` slices for East Crazies/f70. They
write direct-eval results plus failure-intake cases, score five, six, and six metric groups, and
are required by `promotion-suite`. Live replay is green with no blocking gaps, zero failure-intake
cases, Final QA `198/198`, and current-promotion `35/35`.

## Verification Gates

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/FIRST_CLASS_SYSTEM_EVALUATION_IMPROVEMENT_MILESTONE_PLAN.md --strict`
- For applicability implementation milestones:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py tests/test_eval_trace_case_promote.py tests/test_architecture_contract.py`
- For source changes: run the repo's focused pytest, ruff, and compileall gates from `AGENTS.md`.
- For any live readiness claim: run the scoped applicability gold, gate-graph, and phase-eval
  commands named by that milestone.
- For current-promotion all-step expansion: run the direct-eval, Final QA, and promotion-suite
  commands listed in `docs/OUTPUT_SCHEMAS.md`.

## Acceptance Criteria

- The repo has a durable implementation goal and staged plan for all-step system evaluation.
- Applicability is explicitly first because it governs downstream compliance and Forest Plan
  routing.
- The plan names applicability metrics, owner surfaces, failure intake, and scoped phase-eval
  ratchet behavior.
- The plan forbids global ratchets, model-judge substitution, hosted source-of-record drift, and
  source-library mutation as proof.
- Future implementation sessions can execute one bounded milestone at a time and commit each
  verified slice atomically.

## Documentation, Handoff, And Commit Closeout

Milestone 0 must update this plan, `docs/EVALUATION_COVERAGE_REGISTER.md`,
`docs/CURRENT_ROUTING.md`, and `docs/SESSION_HANDOFF.md` when the active next packet changes.
Behavior-changing milestones must also update `docs/OUTPUT_SCHEMAS.md`,
`docs/CURRENT_SYSTEM_STATE.md`, architecture contracts, and tests that enforce new owners.

Commit closeout policy: a milestone is not complete until implementation/docs, focused
verification, docs/handoff updates, and one local atomic commit have landed. Stage only
the verified milestone slice. Do not stage ignored `source_library/` outputs.

## Closeout Outcome Record

Status: Milestones 0 and 3 are implemented; Milestone 1 summary/subgate and Milestone 2
failure-intake slices are reduced; trace-to-case promotion has a tracked case-file gate; Milestone 4
now has current-promotion Final QA, review-packet, and decision-support direct eval plus
promotion-suite consumption.
- Residual risk after closeout: broader promotion ratchets and remaining all-step expansion remain
  future packets.

## Stop Conditions

- Stop if a slice cannot preserve source-set/review/workbook/citation/artifact-hash identity.
- Stop if the proposed evaluator weakens, deletes, skips, xfails, or narrows an existing gate.
- Stop if the proof depends on stale ignored `source_library/` outputs or broad regeneration that
  was not scoped in the packet.
- Stop if a scorer substitutes an uncalibrated model judge for deterministic or human-label-backed
  checks.
- Stop if a ratchet would block unrelated reviews/source sets or widen without scoped green proof.
- Stop if failures cannot become replayable cases with owner, risk, assertion, source refs, hashes,
  and removal conditions.
- Stop if the work expands into promotion, hosted scoring, package intake, compliance-review
  gate-graph consumption, or graph publication before the current packet's eval gate is green.
