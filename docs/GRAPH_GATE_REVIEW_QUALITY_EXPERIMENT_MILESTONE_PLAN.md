# Graph Gate Review Quality Experiment Milestone Plan

Date: 2026-06-04
Status: Resolved; three-review artifact-derived hypothesis test supported
Plan class: implementation
High-risk implementation: yes
Owner context: scientific-method proof for whether NEPA applicability gate-graph enforcement improves
USFS R1 EA reviewer-engine quality before runtime widening.

## Purpose And Current Evidence

The NEPA EA Gate Graph is now a structural and evaluated applicability artifact, and the scoped
West Reservoir/f70 applicability ratchet is green. Existing evidence proves identity, freshness,
parent/child consistency, Forest Plan subgate behavior, and phase-eval direct-eval consumption of
the applicability summary.

That evidence does not yet prove the causal claim that graph-gate enforcement produces a higher
quality EA review. The missing step is a pre-registered paired experiment that compares the current
review path against a graph-gated treatment path on the same frozen inputs.

## Goal, Intent, Stop Condition, Non-Goals, And Scope

Goal: implement an experiment harness that can test whether NEPA graph gates improve EA review
quality without deciding the final case mix, metric set, or thresholds in code.

Intent: make the hypothesis falsifiable while preserving scientific freedom. Each experiment run
must pre-register its own cases, quality dimensions, thresholds, and frozen inputs in a manifest;
the evaluator should enforce that contract and report the measured result, not hardcode what the
test must discover.

Stop condition: stop when proof would require post-hoc threshold tuning, runtime
compliance/phase-eval graph-gate adoption, new applicability or legal conclusions, hidden domain
heuristics, non-frozen full-review inputs, or production `source_library/` mutation outside scoped
gate-graph/eval commands.

Hypothesis:

- H1: graph-gate enforcement improves review quality by reducing closed-branch authority leakage,
  blocked-branch progression, missing open-branch generated rules, unsupported compliance findings,
  Forest Plan subgate mistakes, and stale/identity-mismatched graph use.
- H0: graph-gate enforcement does not improve review quality, or it introduces any critical
  regression.

Completion means the manifest pre-registers intent, stop conditions, cases, frozen inputs, quality
dimensions, and thresholds; `graph-gate-review-quality-eval` writes paired control/treatment
results, metric deltas, failed thresholds, and `hypothesis_supported`; and the scorer can accept
live/readback, controlled mutation, exploratory, or later reviewer-labeled cases without code
changes. `hypothesis_supported=true` requires zero critical regressions and a positive
manifest-declared quality delta.

Non-goals:

- Do not make compliance-review or phase-eval consume the graph gate as a runtime blocker in this
  packet.
- Do not add a global ratchet, promotion gate, hosted scorer, model judge, or new EA package intake.
- Do not mutate production ignored `source_library/` outside scoped gate-graph and eval artifact
  generation for the selected cases.
- Do not allow the graph gate to invent applicability decisions. It may only enforce consistency
  against the authority universe, applicability decisions, generated rule pack, and compliance
  outputs.

Scope:

- Add a manifest-driven graph-gate review-quality eval command and result schema.
- Score paired control/treatment review quality using deterministic metrics.
- Allow controlled defect cases, live no-regression cases, and future reviewer-labeled cases through
  the same manifest contract.
- Add focused tests, CLI registration, output-schema docs, current-state/routing/handoff updates,
  and architecture ownership if a new module is added.

## Intent Hierarchy

- North-star intent: prove feature value through falsifiable evidence before widening runtime gates.
- Invariant: preserve source-set, review, package, source-record, citation, artifact hash, graph hash, and
  scorer-contract identity for each paired comparison.
- Optimization target: measure reviewer-quality deltas, not graph publication or structural
  completeness alone.
- Acceptable tradeoffs: controlled mutation cases may run when live reviewer-ready cases are green; live cases still
  must prove zero regression.
- Explicit non-negotiables: no post-hoc thresholds, model judges, hidden applicability decisions,
  global ratchets, or test weakening.
- Intent lock: runtime compliance/phase-eval graph-gate consumption becomes a later packet only after this
  experiment supports the hypothesis.

## Owner Surfaces And Placement

- `config/graph_gate_review_quality_eval_v1.json` owns the pre-registered experiment design.
- `src/usfs_r1_ea_sources/graph_gate_review_quality_eval.py` owns deterministic scoring and paired
  control/treatment comparison.
- CLI registration owns the public `graph-gate-review-quality-eval` command.
- `docs/OUTPUT_SCHEMAS.md` owns result-schema and command contract text.
- `docs/EVALUATION_COVERAGE_REGISTER.md`, `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/CURRENT_ROUTING.md`, and `docs/SESSION_HANDOFF.md` own route and current-truth updates.
- Tests own control/treatment parity, mutation detection, regression failure, stale graph failure,
  CLI propagation, and architecture-contract coverage.

Placement rules:

- Keep experiment scoring in the eval owner module. Do not put scorer logic inside
  `compliance_review.py` or `phase_eval.py`.
- Any runtime graph consumption discovered during the experiment must be opened as a separate
  packet after the experiment result is green.
- The result artifact is the truth surface for the hypothesis; docs may summarize it but must not
  replace it.

## Experimental Design Contract

Pre-register each case with `case_id`, review/source-set identity, frozen package/artifact and graph
paths, control observations, treatment observations, and any readbacks needed to score the declared
quality dimensions.

The evaluator must not hardcode a mandatory case family. The manifest should be free to include:

- live reviewer-ready no-regression cases;
- controlled defect cases for graph-gate failure modes;
- exploratory cases that identify weak measurement surfaces; and
- later reviewer-labeled cases once human labels exist.

Candidate dimensions include closed-branch leakage, blocked-branch progression, missing open-branch
rules, unsupported findings, Forest Plan subgate errors, stale/identity-mismatched graph use,
citation regression, critical regressions, and net quality delta.

## Single-Variable Run Discipline

Follow-on EA review quality runs must follow
`docs/EA_REVIEW_SCIENTIFIC_METHOD_RUN_PROTOCOL.md`: one intervention per run,
complete trace bundle surfaced, and multi-variable replays labeled
`multi_factor_engineering_replay`, not causal hypothesis support.

## Weak-Point Prevention

| Weak point | Owner surface | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| Experiment proves only graph validity, not review quality | eval manifest and result schema | Require control/treatment quality metrics over generated rules, compliance findings, citations, and phase readiness | Result lacks paired review-quality deltas |
| Treatment wins by changing non-graph variables | scorer module and tests | Freeze source-set, review, package, applicability decisions, generated-rule inputs, and graph hashes per case | Any paired comparison changes an unapproved input |
| Multiple variables change before measurement | run protocol, manifest, docs | One intervention variable per run; trace bundle must identify commit, input hashes, and artifact hashes | Improvement claim after selected-action, trigger-template, retrieval, or graph changes are combined in one run |
| Code constrains the scientific test too early | manifest and scorer | Keep case families, quality dimensions, and thresholds manifest-owned | Scorer hardcodes a mandatory defect family or West Reservoir-only proof |
| False positive improvement claim | result schema | `hypothesis_supported=true` requires zero critical regressions and positive delta in at least one pre-registered defect class | Positive claim with zero measurable defect reduction |
| Graph gate hides missing evidence | scorer and compliance readbacks | Citation/source support cannot regress; unsupported findings stay critical | Any citation support regression or unsupported treatment finding |
| Runtime adoption sneaks into experiment | routing docs and tests | Keep compliance-review/phase-eval runtime blockers out of scope until result is green | Runtime gate consumption lands in this packet |

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing applicability,
phase-eval, compliance, graph, or architecture tests to make the experiment pass.

## Milestone Sequence

### Milestone 1 - Pre-Registered Experiment Contract

- Add `config/graph_gate_review_quality_eval_v1.json` with H1/H0, cases, frozen artifact refs,
  intent, stop conditions, quality dimensions, optional candidate cases, and threshold policy.
- Add schema docs for the result artifact, `command_succeeded`, and `hypothesis_supported`.
- Outcome label: reduced when the manifest validates and plan/docs make the hypothesis falsifiable.

### Milestone 2 - Paired Quality Scorer

- Add `graph-gate-review-quality-eval` and the scorer module.
- Compare control and treatment on manifest-declared frozen case inputs without mutating production
  artifacts.
- Write deterministic results with per-case metric deltas, aggregate deltas, failed thresholds, and
  source artifact hashes.
- Outcome label: reduced when focused tests prove positive, null, regression, and stale-artifact
  paths.

### Milestone 3 - Scoped Live Proof And Routing Closeout

- Run the eval against the pre-registered manifest and read back the generated result.
- Update current-state/routing/handoff only with the measured outcome:
  `hypothesis_supported=true`, `hypothesis_supported=false`, or `experiment_blocked`.
- If and only if the hypothesis is supported, route the next packet as runtime
  compliance/phase-eval graph-gate consumption.
- Outcome label: resolved if the experiment result is generated, thresholds are evaluated, docs are
  current, and the verified slice is committed.

## Verification Gates

- `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/GRAPH_GATE_REVIEW_QUALITY_EXPERIMENT_MILESTONE_PLAN.md --strict`
- `PYTHONPATH=src uv run --extra dev pytest tests/test_graph_gate_review_quality_eval.py tests/test_cli.py tests/test_applicability_eval.py tests/test_phase_eval.py tests/test_compliance_review.py tests/test_architecture_contract.py -q`
- `PYTHONPATH=src python -m usfs_r1_ea_sources graph-gate-review-quality-eval --manifest config/graph_gate_review_quality_eval_v1.json --output-dir source_library`
- Repo hygiene gates from `AGENTS.md`: Ruff, compileall, and whitespace diff check.
- Read back `case_count`, `critical_regression_count`, `net_quality_delta`, `failed_thresholds`,
  and `hypothesis_supported` from the result artifact.

## Acceptance Criteria

- The manifest pre-registers H1, H0, intent, stop conditions, frozen inputs, quality dimensions,
  and threshold policy before the scorer result is used as proof.
- The result artifact records control/treatment observations, paired metric deltas, and artifact
  hashes for every case.
- `hypothesis_supported=true` is impossible unless treatment has zero critical regressions, no
  citation-support regression, no missing open-branch rule regression, and positive quality delta in
  at least one pre-registered graph-gate defect class.
- Tests prove positive, null, critical-regression, stale-artifact, and CLI/architecture paths.
- Live/readback or controlled cases can be added without scorer-code changes when the manifest
  declares their quality dimensions and threshold policy.
- Docs and handoff state the measured outcome and the correct next route without claiming runtime
  graph-gate consumption prematurely.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md` for the new command and result artifact. Update
`docs/EVALUATION_COVERAGE_REGISTER.md`, `docs/CURRENT_SYSTEM_STATE.md`,
`docs/CURRENT_ROUTING.md`, and `docs/SESSION_HANDOFF.md` with the experiment state and measured
outcome. If the experiment is blocked or null, route the blocker or hypothesis rejection instead of
opening runtime graph-gate consumption.

## Stop Conditions

- Stop if a paired comparison cannot keep source-set, review, package, applicability, graph, and
  scorer inputs frozen except for graph-gate treatment.
- Stop if no live/readback or controlled mutation case can show a measurable graph-gate defect
  delta.
- Stop if treatment requires new applicability decisions, legal conclusions, hidden heuristics,
  model-judge scoring, hosted scoring, or uncalibrated labels.
- Stop if any treatment case loses applicable authority, adds an unsupported finding, drops
  citation/source support, or weakens a Forest Plan reviewer-ready gate.
- Stop if runtime compliance-review or phase-eval graph-gate consumption is needed before a green
  experiment result; open a later packet instead.
- Stop if passing requires broad corpus regeneration, destructive cleanup, production
  `source_library/` mutation outside the eval command, or weakened existing gates.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified experiment slice after implementation, focused verification, result
readback, docs/handoff updates, strict plan lint, and whitespace diff check pass. Do not stage ignored
`source_library/`. If multiple implementation slices are needed, commit the verified manifest,
scorer, and routing/doc closeout as separate atomic milestones rather than one aggregate commit.

## Closeout Outcome Record

Status: resolved; three-review artifact-derived test supports H1.

- Result artifact:
  `source_library/evaluations/graph_gate_review_quality/graph_gate_review_quality_results.json`.
- Tracked metrics brief:
  `docs/GRAPH_GATE_REVIEW_QUALITY_THREE_REVIEW_RESULTS.md`.
- Hypothesis result: `hypothesis_supported=true`, `case_count=3`, `complete_case_count=3`,
  `distinct_review_count=3`, `positive_delta_case_count=3`, `critical_regression_count=0`,
  `net_quality_delta=9.428571`, and `threshold_failures=[]`.
- Verification result: focused tests, live eval command, Ruff, compileall, architecture-contract,
  strict plan lint, and whitespace diff check passed.
- Commit identifier: see the milestone commit in git history after closeout.

## Residual Risks And Next Routing

Next bounded packet: scoped compliance/phase-eval graph-gate runtime consumption. Residual risk:
the supported result is artifact-derived and not a human-labeled legal-quality benchmark.
