# Evidence Arbitration Milestone Plan

Date: 2026-05-05

This plan fixes the applicability decision gap exposed by the first Milestone 10 real-package
expansion pass for `region1-expansion-ecid-preliminary-ea`. The issue is not missing retrieval or
missing authority coverage. The system found strong roads, trails, access, right-of-way, travel
management, and special-use evidence, but the deterministic predicate marked the whole authority
family as `needs_adjudication` because unrelated or conditional trigger evidence was also labeled
`weak_signal`.

## Goal

Make applicability evidence arbitration strong enough to distinguish:

- strong package evidence that independently satisfies an authority-family trigger;
- weak package evidence that is relevant but conditional, background, speculative, or incomplete;
- weak auxiliary evidence that should be retained for reviewer traceability but should not
  contaminate an otherwise decisive positive trigger;
- true conflicts that must remain `needs_adjudication`;
- explicit negative or out-of-scope evidence that can support a `not_applicable` decision.

The fix must remain general. Do not add East Crazies-specific branches, NEPA project-type shortcuts,
or hidden rule exceptions. Domain knowledge belongs in rule templates, trigger contracts, eval
fixtures, and auditable decision artifacts.

## Triggering Finding

The ECID preliminary EA roads/access authority decision:

- Decision ID: `b6b7ba14323bf2c74c2318e8`
- Authority family: `roads_access_special_use_action_authorities`
- Current status: `needs_adjudication`
- Current basis: `unresolved_evidence_conflict`

The package contains strong evidence that the action involves trail relocation, trail construction,
road/trail rights-of-way, access easements, travel-plan access objectives, special-use
authorizations, outfitter-guide permit modifications, and related reserved access. The current
predicate still blocked the decision because some matched evidence also carried weak phrases such as
`if needed`, `potentially`, and `may be possible`.

Current failure mode:

```text
positive trigger matched
  + any matched weak_signal evidence
  -> requires_adjudication=true
  -> needs_adjudication
```

Target behavior:

```text
strong positive trigger independently sufficient
  + weak auxiliary trigger retained as trace evidence
  -> applicable, with arbitration notes

only weak positive trigger evidence
  -> needs_adjudication

strong positive and explicit negative/out-of-scope evidence both present
  -> needs_adjudication unless the rule contract gives precedence
```

## Non-Goals

- Do not weaken validation, generated-rule-pack, compliance-review, or phase-eval gates.
- Do not make weak evidence disappear. Weak evidence should stay visible in traces, reports, and
  adjudication diagnostics.
- Do not make every positive term hit reviewer-ready.
- Do not hard-code East Crazies text, file names, parcel IDs, trail names, or one-off legal
  conclusions into runtime logic.
- Do not bypass human adjudication for genuinely uncertain water, wetlands, floodplain, grazing,
  roadless, permit, or special-use questions.
- Do not rerun broad live download or corpus-refresh workflows.

## Relevant Surfaces

- Applicability decision predicate:
  `src/usfs_r1_ea_sources/applicability_decisions.py`
- Package fact graph and signal classification:
  `src/usfs_r1_ea_sources/package_fact_graph.py`
- Applicability validation and adjudication replay:
  `src/usfs_r1_ea_sources/applicability_validation.py`
- Applicability evaluation:
  `src/usfs_r1_ea_sources/applicability_eval.py`
- Current tests:
  `tests/test_applicability_decisions.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_promotion_suite.py`
- Schemas and current-state docs:
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`
- Current real-package evidence:
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/`

## Target Invariant

Applicability decisions must be derived from an auditable arbitration record, not from a single
global weak-signal flag. A candidate authority can be marked `applicable` only when the decision
artifact proves that at least one rule-contract-sufficient positive trigger was supported by strong
package evidence and current source-library evidence. Weak evidence may add notes or reviewer
questions, but it should force `needs_adjudication` only when it is necessary to the decision or
conflicts with the decisive evidence.

## Milestone 1: Diagnostic Arbitration Artifact

Status: implemented

Add a behavior-preserving diagnostic layer that makes the current arbitration failure explicit
without changing status outcomes.

Implementation scope:

- Add per-trigger evidence accounting to applicability decision rows:
  - trigger group;
  - matched evidence IDs;
  - evidence strength counts;
  - weak-signal reasons;
  - selected package/source/retrieval refs;
  - whether the group was treated as decisive, auxiliary, weak-only, or conflicting.
- Include the arbitration summary in `applicability_report.md` for any `needs_adjudication`
  decision.
- Add a synthetic unit fixture that reproduces the ECID shape:
  - strong `right-of-way` and `road` evidence;
  - weak `trail` evidence caused by `if needed`;
  - weak `grazing` evidence caused by speculative effects language.

Acceptance signal:

- Existing status behavior is unchanged.
- The synthetic fixture produces an arbitration summary explaining why the current predicate blocks
  the decision.
- Focused tests prove the diagnostic artifact is deterministic and stable.

Implemented state:

- `applicability_decisions.jsonl` decision rows include diagnostic-only `arbitration_summary`
  records with per-trigger evidence IDs, package chunk/fact refs, selected retrieval refs, evidence
  strength counts, weak-signal reasons, and trigger-group diagnostic treatments.
- `applicability_report.md` renders arbitration diagnostics for `needs_adjudication` decisions.
- `tests/test_applicability_decisions.py` includes a roads/access synthetic fixture with strong
  road and right-of-way evidence plus weak trail and grazing evidence, preserving the current
  `needs_adjudication` status while making the current failure mode explicit.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:

Commit Milestone 1 as a standalone diagnostic/schema-doc slice.

## Milestone 2: Evidence Strength Model

Status: implemented

Replace the current boolean weak-signal interpretation with a structured evidence-strength model.

Implementation scope:

- Keep the current `confidence_class` values for compatibility, but add structured reason fields
  where evidence is classified:
  - `observed`;
  - `conditional`;
  - `speculative`;
  - `background`;
  - `negative_context`;
  - `weak_signal`.
- Preserve the matched phrase and local evidence window for weak classifications.
- Distinguish a weak term hit in a no-action, cumulative-effects, or speculative resource-effects
  sentence from a strong proposed-action trigger.
- Add tests for uncertainty phrases:
  - `if needed` near trail construction;
  - `potentially` near parcel scope;
  - `may be possible` near resource effects;
  - explicit no-change/no-action statements;
  - decisive ROW/access language in the same package.

Acceptance signal:

- Weak evidence remains visible and traceable.
- Strong evidence in the same candidate decision is not collapsed into the same bucket as weak
  auxiliary evidence.
- Existing negative-context behavior remains fail-closed.

Implemented state:

- `evidence_strength.py` provides one deterministic classifier for observed, conditional,
  speculative, background, negative-context, and legacy weak-signal evidence.
- `package_fact_graph.json` fact/evidence-span nodes and `package_applicability_context.json`
  compact facts now retain `evidence_strength` while preserving the existing `confidence_class`
  compatibility field.
- `applicability_retrieval_trace.jsonl` package-result provenance carries package graph
  `evidence_strength` forward.
- `applicability_decisions.jsonl` package evidence spans carry `evidence_strength`, and
  `arbitration_summary.positive_trigger_groups[]` / `negative_trigger_groups[]` include both
  compatibility `evidence_strength_counts` and structured `evidence_strength_class_counts` plus
  `weak_signal_details`.
- The milestone remains behavior-preserving for applicability status outcomes. Milestone 3 now
  consumes these diagnostics as the behavior-changing trigger-arbitration predicate.

Milestone 1/2 gap-close state:

- Weak-signal reason strings now include the structured strength class, classifier reason, and
  matched phrase when available instead of only generic evidence IDs.
- No-action/no-change background classification covers explicit action-negating phrases such as
  `would not occur` and `does not include`, not only headings or `No Action Alternative` labels.
- Negative-context evidence records preserve the matched negative phrase when the classifier can
  identify it.
- Package fact graph tests now assert that fact nodes, compact context facts, and uncertainty
  records carry `evidence_strength` details, including matched phrases and evidence windows for
  weak facts.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

Commit policy:

Commit Milestone 2 as the evidence-strength/schema slice.

## Milestone 3: Trigger Arbitration Predicate

Status: implemented

Implement the actual arbitration rule that lets strong independent evidence carry a decision while
preserving adjudication for genuine uncertainty.

Implementation scope:

- Add a trigger-level arbitration function used by `applicability-determine`.
- Decide positive applicability using rule-contract sufficiency, not a global weak flag.
- Default arbitration policy:
  - strong positive evidence for a sufficient trigger group -> `applicable`;
  - strong positive evidence plus weak auxiliary evidence -> `applicable` with arbitration notes;
  - only weak positive evidence -> `needs_adjudication`;
  - strong positive evidence plus explicit negative or out-of-scope evidence -> `needs_adjudication`
    unless the rule contract declares precedence;
  - no positive evidence with sufficient search coverage -> `not_applicable`;
  - insufficient search coverage -> `unresolved`.
- Add optional rule-template metadata for future stricter contracts, such as required trigger groups
  or minimum strong groups, while preserving current template compatibility.
- Add decision fields such as `arbitration_status`, `decisive_trigger_groups`,
  `weak_auxiliary_trigger_groups`, and `arbitration_rationale`.

Acceptance signal:

- The synthetic ECID-shaped roads/access fixture changes from `needs_adjudication` to `applicable`
  because strong ROW/road/access evidence is independently sufficient.
- All-weak fixtures remain `needs_adjudication`.
- Positive-plus-negative conflict fixtures remain `needs_adjudication`.
- Not-applicable decisions still require coverage certificates.

Implemented state:

- `applicability-determine` now evaluates positive trigger groups through a trigger-level
  arbitration function before assigning conditional-rule status.
- Default sufficiency requires at least one strong positive trigger group. Optional
  `trigger_arbitration_contract` metadata can require specific strong trigger groups, set a
  minimum strong group count, or declare positive/negative conflict precedence.
- Strong positive evidence can carry an `applicable` decision even when weak auxiliary trigger
  groups are present. Weak auxiliary evidence remains visible in arbitration notes, reviewer notes,
  report diagnostics, and decision evidence spans.
- All-weak positive evidence remains `needs_adjudication`, and strong positive evidence plus
  explicit negative/out-of-scope evidence remains `needs_adjudication` by default.
- Decision rows now carry active arbitration fields: `arbitration_status`,
  `decisive_trigger_groups`, `weak_auxiliary_trigger_groups`, `weak_only_trigger_groups`, and
  `arbitration_rationale`.

Verification:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev pytest tests/test_package_fact_graph.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Closeout verification on 2026-05-06 passed all listed commands:
`24` applicability-decision tests, `11` applicability-eval tests, `5` architecture-contract tests,
`4` package fact graph tests, ruff, compileall, and whitespace checks.

Commit policy:

Commit Milestone 3 as the behavior-changing predicate slice.

## Milestone 4: Real-Package Replay And Gate Alignment

Status: implemented

Replay the ECID preliminary EA applicability run and prove the new arbitration behavior closes only
the roads/access gap it is designed to close.

Implementation scope:

- Regenerate the ECID applicability decision ledger from current package/source artifacts.
- Verify `roads_access_special_use_action_authorities` becomes `applicable` with strong
  roads/access/ROW evidence and weak auxiliary evidence retained in arbitration notes.
- Verify the Clean Water Act/WOTUS and EO 11988 floodplain decisions remain handled according to
  their own evidence:
  - mark them applicable only if their independent trigger evidence is strong under the same general
    arbitration rules;
  - otherwise leave them `needs_adjudication` and keep the adjudication worklist accurate.
- Update the promotion-suite expansion slot only to the extent supported by replayed artifacts.
- Do not force `expansion_ready=true` unless all applicability validation, generated rule-pack,
  compliance-review, and phase-eval gates pass.

Acceptance signal:

- ECID roads/access no longer blocks on weak auxiliary evidence.
- Any remaining blocker is a genuine unresolved authority decision, not an arbitration artifact.
- `applicability_validation.json` and promotion-suite status accurately reflect the replay.

Implemented state:

- The ECID preliminary EA applicability decision ledger has been replayed against the active
  trigger-arbitration predicate. The decision partition is now `43` applicable, `346`
  non-applicable, and `3` `needs_adjudication` out of `392` candidates.
- `roads_access_special_use_action_authorities` is now `applicable` with decisive road, trail,
  travel-management, special-use, right-of-way, and grazing trigger groups. Weak and negated
  auxiliary evidence remains visible in reviewer notes.
- Clean Water Act/WOTUS and EO 11988 floodplain authorities are now `applicable` because their own
  strong package evidence independently satisfies the same general arbitration rule.
- The remaining adjudication worklist is no longer the roads/access arbitration artifact. It is
  limited to positive/negative evidence conflicts for cultural-resource/SHPO sources,
  minerals/energy authorities, and species-supporting sources/overlays.
- Forest Plan component not-applicable decisions now emit explicit scope-miss evidence with
  `missing_package_values` and search coverage, so applicability validation reports only the three
  unresolved authority conflicts instead of noisy component basis gaps.
- `config/promotion_suite_v1.json` records the updated expansion-slot local signal while keeping
  `status=blocked_needs_adjudication`, `ready=false`, and `expansion_ready=false`.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-template \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/promotion_suite_v1.json /tmp/promotion_suite_v1.validated.json
git diff --check
```

Closeout verification on 2026-05-06:

- `applicability-determine` replayed `392` candidate authorities to `43` applicable, `346`
  non-applicable, and `3` `needs_adjudication`.
- `applicability-validate` correctly failed reviewer readiness only on unresolved authority
  decisions: failure categories were limited to `unresolved_authority`.
- `applicability-adjudication-template` emitted the three-item worklist for cultural-resource/SHPO,
  minerals/energy, and species-supporting authority conflicts.
- `promotion-suite` kept current promotion ready and expansion not ready with
  `adjudication_needed` and `package_fixture_missing` as the expansion failure categories.
- Focused tests, architecture contract, ruff, compileall, JSON validation, and whitespace checks
  passed.

If all decisions validate after replay or adjudication:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea \
  --source-set-id source-set-ba8d0feae79501b8

PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)/Preliminary Environmental Assessment" \
  --output-dir source_library \
  --rule-pack source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id region1-expansion-ecid-preliminary-ea \
  --reuse-package-cache

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id region1-expansion-ecid-preliminary-ea
```

Commit policy:

Commit Milestone 4 only after the replayed repo artifacts and docs accurately describe the new
state. Do not stage ignored `source_library/` artifacts unless repository policy changes.

## Milestone 5: Evaluation And Promotion Coverage

Status: implemented

Make evidence arbitration a permanent eval dimension so the same failure does not reappear in later
real-package expansion.

Implementation scope:

- Add applicability eval cases for:
  - strong positive plus weak auxiliary evidence;
  - only weak positive evidence;
  - positive evidence plus explicit negative package evidence;
  - no-action/background-only evidence;
  - rule-template-specific trigger sufficiency.
- Add gold-eval expectations for arbitration fields, not just final status.
- Update `phase-eval` readiness summaries to expose arbitration counts:
  - applicable with weak auxiliary evidence;
  - needs adjudication because only weak evidence exists;
  - needs adjudication because positive and negative evidence conflict.
- Update `docs/OUTPUT_SCHEMAS.md`, `docs/CURRENT_SYSTEM_STATE.md`, and the relevant milestone plan
  notes after implementation.

Acceptance signal:

- Arbitration behavior is covered by unit, eval, and phase-level checks.
- Promotion reports can distinguish "blocked by genuine adjudication" from "blocked by conservative
  arbitration."
- The next real-package expansion slot has a clear diagnostic if evidence strength is mixed.

Implemented state:

- `applicability-eval` now supports `expected_arbitration_statuses_by_rule_id` and
  `expected_arbitration_decision_effects_by_rule_id`, reports per-case and aggregate
  `applicability-arbitration-summary-v0` counts, and includes arbitration status/effect match rates.
- The committed seed eval now has `9` cases. The four Milestone 5 arbitration cases cover
  strong-positive plus weak auxiliary evidence, positive/negative conflict, no-action/background-only
  weak evidence, and rule-template-specific trigger sufficiency. The existing weak-only CWA case now
  asserts arbitration fields explicitly.
- `applicability-gold-eval` now carries nested arbitration summaries and requires at least one gold
  case with explicit arbitration-field expectations.
- `phase-eval` now writes top-level `applicability_arbitration_summary` and mirrors it into the
  `applicability_determination` phase details.
- `promotion-suite` now checks arbitration summary presence in phase eval and seed/gold arbitration
  coverage counts. The current promotion remains ready while expansion remains blocked by
  adjudication and the missing third-package fixture.

Verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/applicability_eval_seed.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/applicability_gold_eval_v0.json

PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review

PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json

PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/applicability_eval_seed.json /tmp/applicability_eval_seed.validated.json
python -m json.tool config/applicability_gold_eval_v0.json /tmp/applicability_gold_eval_v0.validated.json
python -m json.tool config/promotion_suite_v1.json /tmp/promotion_suite_v1.validated.json
git diff --check
```

Closeout verification on 2026-05-06:

- `applicability-eval` passed `9/9` cases, with arbitration status/effect match rates of `1.0` and
  aggregate arbitration counts covering weak auxiliary, weak-only, insufficient-strong-trigger, and
  positive/negative-conflict cases.
- `applicability-gold-eval` passed `5/5` cases with `promotion_ready=true` and a passing
  `gold_eval_cases_have_arbitration_expectations` check.
- `phase-eval --review-id v1-cg-ecid-compliance-review` passed `16/16` phases and emitted
  `applicability_arbitration_summary`.
- `promotion-suite` kept `current_promotion_ready=true`, `promotion_ready=true`, and
  `expansion_ready=false`; expansion blockers remain `adjudication_needed` and
  `package_fixture_missing`.
- Focused tests, architecture contract, ruff, compileall, JSON validation, and whitespace checks
  passed.

Commit policy:

Commit Milestone 5 as the eval/docs/promotion-alignment slice.

## Stop Conditions

Stop and report instead of continuing if:

- the proposed arbitration requires project-specific logic;
- rule-template contracts cannot express sufficiency without hidden code branches;
- tests show all-weak or positive-negative conflict cases becoming reviewer-ready;
- validation or compliance-review gates need to be weakened to pass;
- ECID replay requires broad source-library regeneration or live network capture outside this
  milestone scope.

## Next Implementation Pass

The evidence-arbitration milestone plan is complete through Milestone 5. The next implementation
pass should return to the broader real-package expansion lane: complete the three-item ECID
applicability adjudication worklist, replay validation/generated-rule-pack/compliance/phase gates
for `region1-expansion-ecid-preliminary-ea`, or add the third real Region 1 EA package fixture if
the user chooses to advance expansion coverage first.
