# Post-V1 Promotion Suite

Date: 2026-05-04

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
  --strict-expansion
```

## Readiness Semantics

The result separates three statuses:

- `current_promotion_ready`: the tracked V1 review and suite-level eval artifacts satisfy the
  manifest for the current Custer Gallatin proving case.
- `expansion_ready`: every declared post-V1 real-package slot is filled and ready.
- `promotion_ready`: equal to `current_promotion_ready` unless `--strict-expansion` is supplied;
  strict mode also requires `expansion_ready`.

The default manifest keeps two open real-package expansion slots. Those slots do not block the
current V1 promotion claim, but they make broader readiness gaps visible to future agents. Current
promotion does require the Milestone 4 applicability seed and gold eval artifacts that prove
positive, negative, unresolved, and replay-adjudicated coverage for the expanded authority-family
templates. It also requires the Milestone 5 reviewer-report artifacts for the promoted V1 review:
authority-family provenance, non-applicable authority appendix, reviewer-resolution report, and
deterministic litigation-risk summary.

## Failure Taxonomy

The suite uses explicit failure categories so a failed run points at the next engineering lane:

- `missing_source`
- `extraction_miss`
- `retrieval_miss`
- `applicability_miss`
- `unsupported_package_evidence`
- `stale_artifact`
- `adjudication_needed`
- `package_fixture_missing`

Current-promotion failures are reported in `failure_category_counts`. Expansion-only failures are
reported separately in `expansion_failure_category_counts`; they enter `failure_category_counts`
only when strict mode is used.

## Current Local Result

The suite was run locally on 2026-05-04 after implementation:

- `current_promotion_ready=true`
- `promotion_ready=true`
- `expansion_ready=false`
- `failure_category_counts={}`
- `expansion_failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`
- `open_expansion_slot_count=2`

The post-V1 applicability artifact family exists for the promoted review and is included in
`phase-eval --review-id`. The applicability seed eval now covers all `19` high-priority
authority-family templates with positive and negative cases, and the gold eval includes unresolved
and replay-adjudicated authority-family profiles. The promoted review also writes the Milestone 5
authority-family sidecars and the promotion manifest requires them before current promotion passes.

The first expansion slot is now a concrete local pass:
`region1-expansion-ecid-preliminary-ea`, using the preliminary EA package under the ECID intake.
The package cache extracted `7` PDFs into `160` chunks, and applicability determination produced
`40` applicable authorities, `349` non-applicable authorities, and `3` decisions requiring
adjudication. The slot remains `ready=false` because validation correctly blocks generated rule-pack
creation until those decisions are adjudicated and replayed. The second real-package slot remains
open with `package_fixture_missing`.
