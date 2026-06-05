# EA Review Scientific-Method Run Protocol

Date: 2026-06-05

## Purpose

Use this protocol whenever a new EA review run is used to claim system
improvement or regression. The goal is to preserve causal interpretability:
each measured run changes one variable, surfaces every trace needed to evaluate
that variable, and records stop conditions before the next change is made.

## Single-Variable Rule

One review-quality run may change exactly one intervention variable.

Examples of separate variables:

- selected/proposed action extraction or selected-action scoping
- authority-family trigger template terms
- retrieval scoring or package-result filtering
- graph expansion depth or graph path selection
- arbitration policy
- generated rule-pack validation
- compliance-review consumption of graph gates

If two changes are needed, run them as separate experiments:

1. Baseline run: frozen code/config/artifacts before the intervention.
2. Intervention A run: change only intervention A, record the full trace bundle.
3. Intervention B run: change only intervention B on top of the accepted A
   baseline, record the full trace bundle.

A run that changes more than one intervention variable may be used as
engineering evidence, but it cannot be used as a clean causal hypothesis test.
Docs must label it `multi_factor_engineering_replay`, not
`hypothesis_supported`.

## Scalability Rule

Every intervention must be designed for any Region 1 EA, not for the proving
EA that exposed the failure. Runtime code must not hardcode a review ID,
project ID, EA title, package name, or forest-specific example slot. Named EAs
may appear in docs, manifests, replay contexts, adjudication files, and tests
only as transparent evidence fixtures.

Allowed:

- generic extraction, retrieval, graph, arbitration, validation, and reporting
  changes;
- data-driven authority-family, Forest Plan, rule-pack, eval, replay, and
  adjudication configs;
- tests that use named EAs as fixtures to prove reusable behavior.

Forbidden:

- runtime branches keyed to one review ID, project title, project number,
  package path, or example slot;
- hidden lexical rules added only because one EA used a phrase;
- claims that a specific EA replay proves general readiness without a generic
  mechanism and regression traces.

If a clean run requires EA-specific runtime logic, stop at
`ea_specific_hardcoding_required`; do not claim improvement.

## Required Run Record

Every measured run must record:

- `run_id`
- `review_id`
- `source_set_id`
- exact commit SHA
- intervention variable
- intervention description
- generic mechanism changed
- named proving EA, if any
- baseline artifact refs and hashes
- treatment artifact refs and hashes
- stop condition
- expected improvement metric
- regression metrics
- pass/fail status
- residual risk

## Required Trace Bundle

Every run must surface the trace artifacts that let reviewers measure
performance and regressions:

- package manifest and package chunks hash
- selected-action artifact path, validation path, and hash when applicability
  uses package triggers
- authority universe path and hash
- package fact graph path, validation path, and hash
- package applicability context path and hash
- applicability retrieval trace path, row count, and hash
- applicability graph trace path, row count, and hash
- retrieval graph diagnostics path and hash
- search coverage certificates path and hash
- applicability decisions path, status counts, and hash
- applicable and non-applicable authority partitions and hashes
- applicability provenance path and hash
- applicability validation path, pass/fail status, and failure categories
- applicability gate graph path, summary path, validation path, activation
  counts, blocked-gate counts, and hashes
- generated rule-pack path, validation path, rule count, and hashes when
  generated-rule-pack readiness is part of the claim
- compliance review, compliance matrix JSON/Markdown/PDF, and validation
  artifacts when compliance quality is part of the claim
- phase-eval result path, phase counts, blockers, and hash

If a required trace is missing, the run stops at `trace_incomplete` and cannot
support an improvement claim.

## Stop Conditions

Stop before applying another change when:

- the current run lacks any required trace artifact;
- the intervention changed more than one variable;
- the intervention requires EA-specific runtime logic;
- source-set, review, package, or authority-universe identity drifted without
  preregistration;
- a trace hash does not match the artifact it is supposed to represent;
- a regression appears in applicability status, citation/source support,
  generated-rule fidelity, compliance findings, graph-gate state, or phase-eval
  readiness;
- the result would require post-hoc threshold changes or hidden adjudication.

## Mud Creek Methodology Note

The 2026-06-05 Mud Creek selected-action replay is useful engineering evidence,
but it changed two variables in the same replay:

- selected-action scoping became a first-class applicability artifact; and
- the `minerals_energy_authorities` trigger template removed broad bare
  minerals terms.

Therefore that replay cannot isolate which variable caused the measured
minerals-family improvement. A clean scientific follow-up must run the selected
action intervention and the minerals trigger-template intervention separately,
with the required trace bundle surfaced for each run.
