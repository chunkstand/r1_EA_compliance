# Post-V1 Promotion Suite

Date: 2026-05-06

The post-V1 promotion suite is the manifest-driven readiness path for agents. It does not replace
the underlying deterministic gates. It records which review artifacts, eval artifacts, source set,
rule pack, and package-expansion slots are required for a readiness claim.

Default manifest:

```text
config/promotion_suite_v1.json
```

Default outputs:

```text
source_library/reviews/promotion_suite/<suite_id>/promotion_suite_results.json
source_library/reviews/promotion_suite/<suite_id>/promotion_suite_report.md
```

Run the current suite:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library
```

Run it as a strict post-V1 expansion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion
```

When capturing normal and strict expansion signals in the same closeout pass, write the strict run
to a separate `--results-dir` or rerun the normal suite last. Otherwise both modes write to the
default `<suite_id>/promotion_suite_results.json` path, which can leave the default local result in
strict mode even though current promotion remains ready without `--strict-expansion`.

## Readiness Semantics

The result separates three statuses:

- `current_promotion_ready`: the tracked V1 review and suite-level eval artifacts satisfy the
  manifest for the current Custer Gallatin proving case.
- `expansion_ready`: every declared post-V1 real-package slot is filled and ready, and every
  manifest-declared `required_for_expansion` artifact check passes.
- `promotion_ready`: equal to `current_promotion_ready` unless `--strict-expansion` is supplied;
  strict mode also requires `expansion_ready`.

The default manifest keeps two real-package expansion slots: the ECID preliminary-EA slot is ready,
and the South Plateau Area Landscape Treatment Project slot is selected but blocked on
`forest_plan_reviewer_not_ready`. Open expansion slots do not block the current V1 promotion claim,
but they make broader readiness gaps visible to future agents. Current promotion does require the
applicability seed and gold eval artifacts that prove
positive, negative, unresolved, replay-adjudicated, and arbitration-field coverage for the expanded
authority-family templates. It also requires the authority-family reviewer-report artifacts for the
promoted V1 review: authority-family provenance, non-applicable authority appendix,
reviewer-resolution report, and deterministic litigation-risk summary.

## Failure Taxonomy

The suite uses explicit failure categories so a failed run points at the next engineering lane:

- `missing_source`
- `extraction_miss`
- `retrieval_miss`
- `applicability_miss`
- `unsupported_package_evidence`
- `stale_artifact`
- `adjudication_needed`
- `forest_plan_reviewer_not_ready`
- `package_fixture_missing`
- `graph_missing_authority_family`
- `graph_missing_candidate_authority`
- `graph_missing_source_record`
- `graph_missing_source_partition`
- `graph_missing_currentness_status`
- `graph_missing_applicability_decision`
- `graph_dangling_edge`
- `graph_stale_artifact`
- `graph_noncurrent_document_in_main_corpus`
- `graph_superseded_as_current`
- `graph_handbook_chapter_collapsed`
- `graph_viewer_export_invalid`
- `graph_region1_profile_gap`

Current-promotion failures are reported in `failure_category_counts`. Expansion-only failures are
reported separately in `expansion_failure_category_counts`; they enter `failure_category_counts`
only when strict mode is used.

Selected expansion slots are validated as contracts, not placeholders. A selected not-ready slot
must define review ID, source set, package path, expected gate artifacts, next action, and a typed
failure category other than `package_fixture_missing`. A ready slot must not retain a failure
category, must still carry the review/package/source-set contract, and its expected gate artifacts
must cover the matching review case's `required_for_expansion` artifact IDs. The generated Markdown
report includes selected-slot review IDs, package paths, and failure categories so the typed
blocker is visible without inspecting raw JSON. A slot that declares `forest_plan_profile` must also
have expansion gate contracts for `compliance_review`, `forest_plan_context_summary`, and
`phase_eval`; the runtime slot check fails closed if the artifact scope, validation, reviewer-ready
status, or last local signal does not prove the declared profile.

## Current Local Result

The latest South Plateau forest-plan context pass was run locally on 2026-05-07 for the selected
South Plateau fixture contract. The package import, applicability-first run, adjudication replay,
generated review artifacts, and Custer Gallatin context resolution are now in place; strict
expansion remains intentionally blocked until the forest-plan component adjudication worklist is
completed:

- imported `26` official South Plateau PDFs from the project Box folder;
- extracted `26/26` package files into `3,671` chunks with `.venv-docling`;
- `applicability-authority-universe`: passed with `392` candidate authorities;
- `applicability-context-build`: passed package fact/context validation;
- `applicability-retrieve`: passed trace validation, with diagnostics retained for all candidates;
- `applicability-determine`: initially produced `55` applicable, `331` non-applicable, and `6`
  `needs_adjudication` authority-family decisions;
- `applicability-adjudication-eval`: passed with `6` resolved adjudications and `0` pending
  adjudications;
- `applicability-adjudication-apply`: passed with `applied_item_count=6` and
  `remaining_unresolved_authority_count=0`;
- `applicability-validate`: now passes with `61` applicable, `331` non-applicable, no unresolved
  or `needs_adjudication` decisions, and `generated_rule_pack_ready=true`;
- `applicability-generate-rule-pack`: passed with `61` generated rules and
  `generated_rule_pack_ready=true`;
- `compliance-review`: runs from the cached package and generated rule pack, resolves
  `scope_status="custer_gallatin"` with forest-plan context `validation_passed=true`, but now
  exits nonzero because the required forest-plan component gate is pending;
- forest-plan component evaluation: `329` components, `152` applicable components, `24`
  applicable standards, `21` applied standards, `31` gaps, and `31` reviewer-resolution items;
- `forest-plan-component-adjudication-template`: generated a `31`-item worklist; the paired
  `forest-plan-component-adjudication-eval` currently fails with `31` pending adjudications;
- South Plateau review-scoped `phase-eval`: fails `15/17` with blockers limited to
  `compliance_review` and `forest_plan_component_adjudication`;
- the promoted V1 review-scoped `phase-eval` was rerun after the South Plateau review-scoped pass
  to restore the shared current-promotion phase-eval artifact at `20/20`;
- non-strict `promotion-suite`: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `open_expansion_artifact_count=5`, and `open_expansion_slot_count=1`;
- strict expansion `promotion-suite`: expected command failure with `current_promotion_ready=true`,
  `promotion_ready=false`, `expansion_ready=false`,
  `failure_category_counts={"forest_plan_reviewer_not_ready": 6}`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.

A later final-QA promotion pass added current-promotion checks for the final QA packet family. The
V1 review-bound phase eval now passes `20/20` phases, the non-strict promotion suite passes
`26/26` required current-promotion results, and the current gates report `failure_category_counts={}`.
Strict expansion now fails closed only on the South Plateau forest-plan blocker while still passing
`26/26` required current-promotion results.

The South Plateau expansion slot remains `ready=false` and carries
`forest_plan_reviewer_not_ready`. The previous ambiguous-scope blocker is closed:
`forest_plan_context_summary.json` now records `scope_status="custer_gallatin"` and
`validation_passed=true`. The blocker is the `31` pending component adjudications required before
the component gate, compliance validation, South Plateau phase eval, and strict expansion can pass.
The promotion manifest includes the component findings, reviewer-resolution queue, adjudication
template, adjudication eval, compliance outputs, forest-plan context summary, and review-scoped
phase-eval artifact checks rather than a slot flag alone.

The Sequence 6 alignment pass also reconciled each ready expansion slot's `expected_gate_artifacts`
with its matching `required_for_expansion` review-case checks. Manifest validation now rejects ready
slots whose expected gate list omits required expansion artifact IDs, preventing a future ready-slot
flag from drifting away from the concrete artifact gate.

The Sequence 7 hardening pass added the declared-profile boundary: a selected slot with
`forest_plan_profile` must either resolve to that profile with `validation_passed=true` and
`reviewer_ready=true`, or stay blocked with the typed forest-plan failure category.

The post-V1 applicability artifact family exists for the promoted review and is included in
`phase-eval --review-id`. The applicability seed eval now covers all `19` high-priority
authority-family templates with positive and negative cases, plus explicit arbitration cases for
weak auxiliary evidence, weak-only evidence, positive/negative conflicts, no-action/background-only
evidence, and rule-template-specific trigger sufficiency. The gold eval includes unresolved and
replay-adjudicated authority-family profiles and now carries explicit arbitration-field
expectations. The promoted review also writes the authority-family sidecars and the promotion
manifest requires them before current promotion passes.

The first expansion slot is now a concrete local pass:
`region1-expansion-ecid-preliminary-ea`, using the preliminary EA package under the ECID intake.
The package cache extracted `7` PDFs into `160` chunks, and applicability determination produced
`43` applicable authorities, `346` non-applicable authorities, and `3` decisions requiring
adjudication after the evidence-arbitration replay. Sequence 1 completed and replayed those three
adjudications as `human_applicable`; `applicability-validate` now passes with `46` applicable
authorities, `346` non-applicable authorities, `0` unresolved, `0` `needs_adjudication`,
`generated_rule_pack_ready=true`, and `reviewer_ready=true`. Sequence 2 generated and validated the
ECID rule pack with `46` rules, wrote the compliance review/matrix/PDF artifacts, wrote
review-scoped phase eval at `source_library/reviews/region1-expansion-ecid-preliminary-ea/`, and
added ECID artifact checks to the promotion suite. Sequence 2A closed the ECID source-claim gap:
the compliance artifact now has `rule_claim_gap_count=0` and `rule_claim_link_count=211`. Sequence
2B completed the `158`-row Forest Plan component adjudication queue, and
`forest-plan-component-adjudication-eval` reports `resolved_adjudication_count=158`,
`real_ea_omission_count=158`, `pending_adjudication_count=0`, and `system_miss_count=0`. ECID
compliance review now reports `reviewer_ready=true`, review-scoped phase eval passes, and the ECID
expansion slot is `ready=true`. The second real-package slot is South Plateau Area Landscape
Treatment Project. It now has an imported package, package cache, applicability context, retrieval
trace, decision ledger, adjudication eval/apply artifacts, passing generated rule-pack artifacts,
resolved Custer Gallatin forest-plan context, forest-plan component findings, a reviewer-resolution
queue, and a pending component-adjudication eval. Its expansion slot is blocked on
`forest_plan_reviewer_not_ready` until the `31`-item component adjudication worklist is completed
and the downstream compliance/phase/promotion gates are replayed.
