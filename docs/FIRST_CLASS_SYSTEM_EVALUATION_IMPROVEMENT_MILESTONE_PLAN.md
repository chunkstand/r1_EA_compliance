# First-Class System Evaluation Improvement Milestone Plan

Date: 2026-06-04
Status: Milestone 0 implemented; Milestone 1 summary-contract slice implemented; Milestone 1 residuals next
Plan class: implementation
High-risk implementation: yes
Owner context: repo-native goal for extending first-class evaluations across the USFS R1 EA
reviewer-engine pipeline, with applicability evaluation as the first critical improvement lane.

## Purpose And Current Evidence

The repo already has a first-class eval/trace substrate, direct-eval-aware phase-eval, an
observability/eval context graph, and an evaluation coverage register. Those surfaces make eval
state inspectable, but they do not yet prove that every pipeline boundary has a strong improvement
loop, nor do they make applicability quality visible enough to guide systematic improvement.

Applicability is the critical decision boundary between source/retrieval evidence and downstream
rule-pack, compliance, Forest Plan, V1, and promotion readiness. A weak applicability decision can
hide relevant authority, create false compliance obligations, or route a package into the wrong
Forest Plan branch. The next improvement goal is therefore not a generic graph-publication gate. It
is a staged system-evaluation program that measures every step and starts by strengthening
applicability as its own evaluated subsystem.

Current evidence:

- `docs/EVALUATION_COVERAGE_REGISTER.md` tracks structural validation and direct-eval coverage by
  subsystem, including meta-eval, upstream, semantic graph, retrieval, compliance, forest-plan, V1,
  gold, and promotion lanes.
- `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md` defines the local eval/trace substrate, SQLite store,
  canonical/OpenInference export, ratchet scope policy, and trace-to-case promotion.
- `config/phase_eval_direct_eval_v1.json` makes source-set phases consume direct-eval artifacts,
  but applicability is not yet a source-set direct-eval phase with its own granular improvement
  metrics.
- `docs/CURRENT_SYSTEM_STATE.md` records that applicability-gate-graph now emits a review-scoped
  NEPA EA Graph of Gates, but compliance-review does not yet consume that graph.

## Goal, Non-Goals, And Scope

Goal: implement a staged first-class system-evaluation improvement program that measures each
pipeline step, starts with applicability evaluation hardening, and turns failures into durable
cases, traces, and scoped phase or promotion gates.

Completion means:

- every pipeline stage has a named structural owner, direct-eval owner or explicit gap status,
  improvement metrics, generated artifacts, and failure-intake route;
- applicability evaluation reports authority-universe coverage, retrieval/graph trace quality,
  decision partition fidelity, generated rule-pack fidelity, gate-graph consistency, Forest Plan
  subgate behavior, and hard-negative false-positive controls;
- applicability failures can be promoted into tracked cases without losing source-set, review,
  source-record, citation, artifact-hash, trace, and scorer provenance;
- phase-eval can fail closed for one explicit scoped applicability ratchet before any wider gate
  expansion; and
- docs and handoff explain which system steps are evaluated, which remain planned, and what gate
  proves improvement.

Non-goals:

- Do not replace existing domain eval commands or the eval-trace SQLite substrate.
- Do not add model-judge or hosted scoring as a gate before deterministic and human-label contracts
  exist.
- Do not make global fail-closed ratchets or wildcard source-set/review scopes.
- Do not mutate ignored production `source_library/` as the primary proof path.
- Do not implement compliance-review consumption of the applicability gate graph in the first
  applicability-eval milestone unless that proves necessary for measurement.

Scope:

- Applicability owner surfaces, eval contracts, fixtures, generated summaries, traces, and
  phase-eval integration.
- Evaluation coverage register rows and gap statuses for every pipeline step.
- Eval-trace case promotion for applicability failures and later stage failures.
- One scoped ratchet over an existing governed review/source-set before broader rollout.

## Intent Hierarchy

Invariant: source-set, review, workbook row, source-record, citation, artifact hash, trace hash,
and scorer contract identity must remain visible through every eval and promoted case.

Optimization target: improve applicability quality by measuring decision correctness, not by adding
hidden NEPA or Forest Service heuristics.

Acceptable tradeoffs: first milestones may add deterministic fixture and manifest coverage before
full live replay, provided they leave current live readiness unchanged.

Explicit non-negotiables: applicability direct eval must include hard negatives, unresolved or
adjudication-needed decisions, Forest Plan component/subgate cases, and generated-rule-pack
partition checks.

Intent lock: this plan advances evaluation and improvement loops for the existing reviewer-engine
pipeline. It does not open hosted scoring, model-judge scoring, new package promotion, or a new
graph publication system.

## Owner Surfaces And Placement

- Evaluation coverage truth:
  `docs/EVALUATION_COVERAGE_REGISTER.md`, `docs/OUTPUT_SCHEMAS.md`,
  `docs/CURRENT_ROUTING.md`, `docs/SESSION_HANDOFF.md`.
- Existing first-class substrate:
  `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md`,
  `config/eval_trace_inventory_contract_v1.json`,
  `config/eval_trace_cases/system_eval_trace_cases_v1.json`,
  eval-trace implementation modules.
- Applicability implementation and eval owners:
  `src/usfs_r1_ea_sources/applicability_*`,
  `src/usfs_r1_ea_sources/applicability_eval.py`,
  `config/applicability_gold_eval_v1.json`,
  `config/applicability_gate_graph_nepa_ea_v1.json`.
- Phase and promotion consumers:
  `config/phase_eval_direct_eval_v1.json`,
  phase-eval implementation modules,
  `config/promotion_suite_v1.json`.
- Tests:
  focused applicability eval tests, phase-eval direct-eval tests, eval-trace case-promotion tests,
  and architecture-contract tests.

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
| Applicability looks green from aggregate counts while critical authority families regress | `applicability_eval.py`, `config/applicability_gold_eval_v1.json` | Per-family slice floors, hard negatives, and prior-failure replay | Any critical family below floor or prior failure regresses |
| Retrieval/graph traces are present but not quality-scored | applicability trace/eval helpers | Score trace coverage, selected evidence quality, no-evidence certificates, and graph-path support | Decision passes without scored supporting or negative trace evidence |
| Generated rule pack drifts from applicability partition | generated-rule-pack validation and phase-eval | Compare applicable partition, generated rules, omitted rules, and unexpected rules | Missing or extra generated rule passes |
| Gate graph becomes structural-only decoration | applicability gate graph and gate-graph eval | Eval parent/child open/closed/blocked consistency against decisions | Gate state contradicts applicability decisions |
| Failures stay as logs instead of learning cases | eval-trace case promotion and applicability case files | Promote selected failures with source refs, hashes, assertion, owner, risk, review/removal conditions | Failed case cannot be replayed from tracked artifacts |
| Global ratchet blocks unrelated work | `phase_eval_direct_eval_v1.json`, `eval_trace_gate.py` | One explicit scoped ratchet first; no wildcard scopes | Missing scoped proof or wildcard ratchet |

## Milestone Sequence

### Milestone 0 - System Evaluation Coverage Goal And Gap Register

Outcome label: reduced.

- Update the coverage register so every pipeline step has one of:
  `direct_eval_present`, `direct_eval_strengthening_planned`, or `direct_eval_missing`.
- Add applicability sub-rows for authority universe, retrieval trace, graph trace, decision
  partition, generated rule pack, gate graph, Forest Plan subgate, and adjudication/failure intake.
- Record the first scoped applicability ratchet target and the stop conditions for widening it.

Closeout note: implemented docs-only in `docs/EVALUATION_COVERAGE_REGISTER.md`. The register states
the eval goal, maps pipeline steps, adds applicability gaps, and names `west-reservoir-67436` on
`source-set-f70ea11e04ae3d53` as the first scoped target after Milestones 1-2. No runtime gate,
source-library artifact, hosted scorer, or model judge changed.

### Milestone 1 - Applicability Direct-Eval Contract Hardening

Outcome label: resolved.

- Add or extend applicability eval contract coverage for authority-family floors, hard negatives,
  Forest Plan component/subgate cases, unresolved/adjudication-needed cases, generated-rule-pack
  partition fidelity, and gate-graph consistency.
- Emit summary metrics that can be indexed by eval-trace inventory and read by phase-eval.
- Add focused tests proving missing categories, wrong source-set/review identity, stale trace
  hashes, wrong generated-rule partitions, and gate-graph contradictions fail closed.

### Milestone 2 - Applicability Failure Intake And Trace-To-Case Promotion

Outcome label: resolved.

- Route applicability failures into durable promoted cases or domain case fixtures with preserved
  source-set, review, source-record, citation, artifact hash, trace, scorer, owner, risk, assertion,
  review condition, and removal condition.
- Add replay tests for at least one promoted failure from retrieval evidence, one from decision
  partition drift, and one from generated rule-pack drift.

### Milestone 3 - Scoped Applicability Phase-Eval Ratchet

Outcome label: resolved.

- Add an explicit applicability direct-eval phase for one governed review/source-set scope.
- Prove phase-eval fails closed on missing, stale, mismatched, or below-threshold applicability
  eval summaries and remains non-blocking for unrelated scopes.
- Update promotion consumers only if the selected governed scope already participates in promotion.

### Milestone 4 - All-Step Evaluation Expansion

Outcome label: reduced.

- Repeat the Milestone 0-3 pattern for remaining gaps in capture, catalog, extraction, retrieval,
  evidence graph, source claims, rule binding, compliance, review packet, final QA, document
  generation, and promotion.
- Keep each expansion as a separate bounded packet with its own owner surfaces, metrics, fixtures,
  phase-eval or promotion gates, docs, and commit closeout.

## Verification Gates

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/FIRST_CLASS_SYSTEM_EVALUATION_IMPROVEMENT_MILESTONE_PLAN.md --strict`
- For docs-only Milestone 0: `git diff --check`.
- For applicability implementation milestones:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py tests/test_eval_trace_case_promote.py tests/test_architecture_contract.py`
- For source changes: `PYTHONPATH=src uv run --extra dev ruff check src tests` and
  `PYTHONPATH=src python -m compileall src`.
- For any live readiness claim: run the scoped applicability gold, gate-graph, and phase-eval
  commands named by that milestone.

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

Commit closeout policy: a milestone is not complete until implementation or docs, focused
verification, required docs/handoff updates, and one local atomic commit have all landed. Stage only
the verified milestone slice. Do not stage ignored `source_library/` outputs.

## Closeout Outcome Record

Status: Milestone 0 implemented; Milestone 1 summary-contract slice implemented; residuals pending.

- Milestone 0 closeout command summary: plan lint and diff whitespace checks passed.
- Applicability implementation closeout command summary: focused tests and lint passed for the
  summary-contract slice; residual gates remain pending.
- Docs and handoff freshness: schema, coverage, routing, current-state, and handoff docs updated.
- Commit identifier: this commit.
- Residual risk after closeout: Forest Plan subgates, failure intake, selected-review summaries,
  and the scoped phase-eval ratchet remain Milestones 1-3.

## Stop Conditions

- Stop if applicability cannot be evaluated without weakening existing validation or compliance
  gates.
- Stop if a proposed scorer would replace deterministic checks with an uncalibrated model judge.
- Stop if the first applicability ratchet would block unrelated scopes.
- Stop if failures cannot be replayed from durable artifacts and hashes.
- Stop if the work expands into compliance-review gate-graph consumption or package promotion before
  applicability measurement is itself proven.
