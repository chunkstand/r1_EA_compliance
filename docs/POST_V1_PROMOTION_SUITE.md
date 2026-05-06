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
and the South Plateau slot is selected but not run. Open expansion slots do not block the current V1
promotion claim, but they make broader readiness gaps visible to future agents. Current promotion
does require the applicability seed and gold eval artifacts that prove positive, negative,
unresolved, replay-adjudicated, and arbitration-field coverage for the expanded authority-family
templates. It also requires the authority-family reviewer-report artifacts for the promoted V1
review: authority-family provenance, non-applicable authority appendix, reviewer-resolution report,
and deterministic litigation-risk summary.

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

Current-promotion failures are reported in `failure_category_counts`. Expansion-only failures are
reported separately in `expansion_failure_category_counts`; they enter `failure_category_counts`
only when strict mode is used.

Selected not-ready expansion slots are validated as contracts, not placeholders. A selected slot
must define review ID, source set, package path, expected gate artifacts, next action, and a typed
failure category other than `package_fixture_missing`. A ready slot must not retain a failure
category. The generated Markdown report includes selected-slot review IDs, package paths, and
failure categories so the typed blocker is visible without inspecting raw JSON.

## Current Local Result

The latest Sequence 3 promotion-suite pass was run locally on 2026-05-06 after the third
real-package slot was replaced with a selected South Plateau fixture contract:

- `current_promotion_ready=true`
- `promotion_ready=true`
- `expansion_ready=false`
- `expansion_artifacts_ready=true`
- `failure_category_counts={}`
- `expansion_failure_category_counts={"applicability_miss": 1}`
- `open_expansion_artifact_count=0`
- `open_expansion_slot_count=1`

Strict expansion mode is expected to fail at this boundary with `promotion_ready=false` and
`failure_category_counts={"applicability_miss": 1}`.
The generated Markdown report now surfaces the South Plateau review ID, declared package path, and
`applicability_miss` blocker in the expansion-slot table.

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
expansion slot is `ready=true`. The second real-package slot is now selected but not run:
`region1-expansion-south-plateau-landscape-treatment` points at the South Plateau Area Landscape
Treatment Project, official project/document pages, the `custer_gallatin` forest-plan profile, and
the expected package/applicability/generated-rule/compliance/phase-eval artifacts. Its typed
remaining blocker is `applicability_miss` until Sequence 4 imports the package and runs the
applicability-first gates.

Resolution plan:

```text
docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md
```

That plan closes the weakness in sequence: lock the current promotion-suite blocker baseline,
complete the three-item ECID adjudication replay, generate and review the ECID expansion rule pack,
close the ECID source-claim gaps, close the ECID Forest Plan component adjudication blocker, select
the third package fixture, run that package through the applicability-first sequence, and close with
strict expansion promotion.
