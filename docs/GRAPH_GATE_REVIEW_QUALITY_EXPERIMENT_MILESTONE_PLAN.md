# Graph Gate Review Quality Experiment Milestone Plan

Date: 2026-06-04
Status: Proposed
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

## Goal, Hypothesis, Non-Goals, And Scope

Goal: implement a deterministic graph-gate review-quality experiment that can support or reject the
hypothesis that NEPA graph gates improve review quality before compliance-review or phase-eval
runtime consumption is widened.

Hypothesis:

- H1: graph-gate enforcement improves review quality by reducing closed-branch authority leakage,
  blocked-branch progression, missing open-branch generated rules, unsupported compliance findings,
  Forest Plan subgate mistakes, and stale/identity-mismatched graph use.
- H0: graph-gate enforcement does not improve review quality, or it introduces any critical
  regression.

Completion means:

- `config/graph_gate_review_quality_eval_v1.json` pre-registers cases, frozen inputs, control and
  treatment definitions, metrics, thresholds, and stop conditions.
- `graph-gate-review-quality-eval` writes
  `source_library/evaluations/graph_gate_review_quality/graph_gate_review_quality_results.json`
  with paired control/treatment results, metric deltas, failed thresholds, and
  `hypothesis_supported`.
- The experiment includes both live/readback cases and controlled graph-gate mutation cases so a
  quality gain can be observed without weakening existing reviewer-ready artifacts.
- The result can only set `hypothesis_supported=true` when all critical regressions are zero and the
  treatment shows a positive quality delta on at least one pre-registered graph-gate defect class.

Non-goals:

- Do not make compliance-review or phase-eval consume the graph gate as a runtime blocker in this
  packet.
- Do not add a global ratchet, promotion gate, hosted scorer, model judge, or new EA package intake.
- Do not mutate production ignored `source_library/` as the proof path; use read-only existing
  artifacts plus temp or fixture-backed mutation outputs.
- Do not allow the graph gate to invent applicability decisions. It may only enforce consistency
  against the authority universe, applicability decisions, generated rule pack, and compliance
  outputs.

Scope:

- Add a manifest-driven graph-gate review-quality eval command and result schema.
- Score paired control/treatment review quality using deterministic metrics.
- Add controlled defect cases for closed-branch leakage, blocked-branch progression, stale graph
  identity, and Forest Plan subgate propagation.
- Add focused tests, CLI registration, output-schema docs, current-state/routing/handoff updates,
  and architecture ownership if a new module is added.

## Intent Hierarchy

- North-star intent: prove feature value through falsifiable evidence before widening runtime gates.
- Invariant: every paired comparison preserves source-set, review, package, source-record, citation,
  artifact hash, graph hash, and scorer contract identity.
- Optimization target: measure reviewer-quality deltas, not graph publication or structural graph
  completeness alone.
- Acceptable tradeoffs: controlled mutation cases may prove defect detection when current live
  reviewer-ready cases are already green; live cases still must prove zero regression.
- Explicit non-negotiables: no post-hoc thresholds, no model-judge substitution, no hidden
  applicability decisions, no global ratchets, and no weakening existing eval or compliance gates.
- Intent lock: this packet implements the hypothesis test only. Runtime compliance/phase-eval
  graph-gate consumption becomes a later packet only after this experiment supports the hypothesis.

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

## Experimental Design

Pre-register each case with:

- `case_id`, `review_id`, `source_set_id`, package/artifact paths, graph paths, and expected
  quality-defect class.
- Control path: current generated-rule-pack/compliance/phase-eval behavior without graph-gate
  enforcement.
- Treatment path: the same inputs evaluated with graph-gate enforcement semantics applied to
  generated rules, compliance findings, and phase readiness.
- Required readbacks: applicability decision partition, gate graph validation, generated rule pack,
  compliance matrix, authority explanation paths, citation/source support, and phase-eval result
  when available.

Minimum case mix:

- One live reviewer-ready no-regression case where all current quality metrics must be preserved.
- One closed-branch leakage mutation where control permits or fails to catch a rule/finding from a
  closed graph branch and treatment catches it.
- One blocked-branch progression mutation where unresolved or needs-adjudication gate state would
  incorrectly proceed without enforcement.
- One Forest Plan subgate mutation covering selected forest, active plan, management area, or
  component/standard propagation.
- One stale or identity-mismatched graph mutation.

Primary metrics:

- `closed_branch_leak_count`
- `blocked_branch_progression_count`
- `missing_open_branch_rule_count`
- `unsupported_compliance_finding_count`
- `forest_plan_subgate_error_count`
- `stale_or_identity_mismatched_graph_count`
- `citation_support_regression_count`
- `critical_regression_count`
- `net_quality_delta`

## Weak-Point Prevention

| Weak point | Owner surface | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| Experiment proves only graph validity, not review quality | eval manifest and result schema | Require control/treatment quality metrics over generated rules, compliance findings, citations, and phase readiness | Result lacks paired review-quality deltas |
| Treatment wins by changing non-graph variables | scorer module and tests | Freeze source-set, review, package, applicability decisions, generated-rule inputs, and graph hashes per case | Any paired comparison changes an unapproved input |
| Mutation cases become artificial and irrelevant | manifest and docs | Include at least one live/readback no-regression case and map each mutation to a real graph-gate failure mode | No live case or no defect-class mapping |
| False positive improvement claim | result schema | `hypothesis_supported=true` requires zero critical regressions and positive delta in at least one pre-registered defect class | Positive claim with zero measurable defect reduction |
| Graph gate hides missing evidence | scorer and compliance readbacks | Citation/source support cannot regress; unsupported findings stay critical | Any citation support regression or unsupported treatment finding |
| Runtime adoption sneaks into experiment | routing docs and tests | Keep compliance-review/phase-eval runtime blockers out of scope until result is green | Runtime gate consumption lands in this packet |

Anti-test-weakening rule: do not delete, skip, xfail, narrow, or relax existing applicability,
phase-eval, compliance, graph, or architecture tests to make the experiment pass.

## Milestone Sequence

### Milestone 1 - Pre-Registered Experiment Contract

- Add `config/graph_gate_review_quality_eval_v1.json` with H1/H0, cases, frozen artifact refs,
  metrics, thresholds, and failure categories.
- Add schema docs for the result artifact and the meaning of `hypothesis_supported`.
- Outcome label: reduced when the manifest validates and plan/docs make the hypothesis falsifiable.

### Milestone 2 - Paired Quality Scorer

- Add `graph-gate-review-quality-eval` and the scorer module.
- Compare control and treatment on frozen case inputs without mutating production artifacts.
- Write deterministic results with per-case metric deltas, aggregate deltas, failed thresholds,
  source artifact hashes, and failure-intake candidates for failed cases.
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

- The manifest pre-registers H1, H0, frozen inputs, case mix, metrics, thresholds, and stop
  conditions before the scorer result is used as proof.
- The result artifact records control and treatment outputs for every case, with paired metric
  deltas and artifact hashes.
- `hypothesis_supported=true` is impossible unless treatment has zero critical regressions, no
  citation-support regression, no missing open-branch rule regression, and positive quality delta in
  at least one pre-registered graph-gate defect class.
- Tests prove the evaluator fails closed for stale graph identity, closed-branch leakage,
  blocked-branch progression, unsupported treatment findings, and a no-improvement null result.
- Live/readback cases prove graph-gate treatment does not degrade existing reviewer-ready outputs.
- Docs and handoff state the measured outcome and the correct next route without claiming runtime
  graph-gate consumption prematurely.

## Documentation And Handoff

Update `docs/OUTPUT_SCHEMAS.md` for the new command and result artifact. Update
`docs/EVALUATION_COVERAGE_REGISTER.md`, `docs/CURRENT_SYSTEM_STATE.md`,
`docs/CURRENT_ROUTING.md`, and `docs/SESSION_HANDOFF.md` with the experiment state and measured
outcome. If the experiment is blocked or null, route the blocker or hypothesis rejection instead of
opening runtime graph-gate consumption.

## Stop Conditions

- Stop if the manifest cannot define a paired control/treatment comparison with identical frozen
  source-set, review, package, applicability, and graph inputs except for graph-gate enforcement.
- Stop if no live/readback case and no controlled mutation case can show a measurable graph-gate
  defect delta.
- Stop if treatment requires new applicability decisions, new legal conclusions, or hidden domain
  heuristics instead of enforcing existing graph/decision artifacts.
- Stop if proving the hypothesis requires model-judge scoring, hosted scoring, or uncalibrated
  human-label substitution.
- Stop if any treatment case loses a known applicable authority, adds an unsupported finding,
  drops citation/source support, or weakens a Forest Plan reviewer-ready gate.
- Stop if runtime compliance-review or phase-eval graph-gate consumption becomes necessary before
  the experiment result is green; open a separate packet after the experiment.
- Stop if passing requires broad corpus regeneration, destructive cleanup, or mutation of ignored
  production `source_library/` outside the scoped eval command.
- Stop if any existing applicability, phase-eval, compliance, graph, or architecture gate must be
  weakened to make the experiment pass.
- Stop before push or PR creation unless explicitly requested.

## Commit Closeout

Stage only the verified experiment slice after implementation, focused verification, result
readback, docs/handoff updates, strict plan lint, and whitespace diff check pass. Do not stage ignored
`source_library/`. If multiple implementation slices are needed, commit the verified manifest,
scorer, and routing/doc closeout as separate atomic milestones rather than one aggregate commit.

## Closeout Outcome Record

Status: not started.

- Result artifact: not generated.
- Hypothesis result: not evaluated.
- Verification result: not run.
- Commit identifier: not committed.

## Residual Risks And Next Routing

If the experiment supports H1, the next bounded packet is compliance/phase-eval graph-gate runtime
consumption. If H0 is not rejected, the next packet should inspect the failed or neutral defect
classes and improve graph-gate evidence, case design, or applicability decision quality before
runtime adoption.
