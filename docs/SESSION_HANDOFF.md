# Session Handoff

Date: 2026-05-03

## Current State

The East Crazy Inspiration Divide V1 compliance review has been rerun against the real package at
`source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)`.
The review ID is `v1-cg-ecid-compliance-review`, source set is
`source-set-ba8d0feae79501b8`, rule pack is `nepa-ea-v0` version `0.4.0`, and generated review
artifacts are under `source_library/reviews/v1-cg-ecid-compliance-review/`.

Current cached rerun command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --docling-timeout-seconds 180
```

Current run result:

- Package extraction wrote `43` manifest rows and `1,265` package chunks.
- Compliance review wrote JSON, Markdown, PDF matrix, and finding graph artifacts.
- Compliance findings: `44` total, with `43` pass and `1` not applicable.
- All `26` baseline source records were evaluated.
- The profile-driven forest-plan resolver now resolves the package to `scope_status:
  custer_gallatin`; context validation passes and `needs_reviewer_resolution` is `false`.
- Forest-plan component artifacts are now produced from the current source-set inventory:
  `329` component findings, `58` standards, `12` applicable standards, and `12` applied standards.
- Compliance validation passes; the compliance review is reviewer-ready. The stricter
  applicable-standard coverage gate now passes with `all_applicable_standards_applied=true`; the
  prior `AB-STD-RCREA-01` gap is supported by recreation/access package evidence for the proposed
  nonmotorized Sweet Trunk Trail.
- Component-level forest-plan eval now passes all `35` adjudicated cases from
  `config/forest_plan_component_eval_seed.json`: every applicable standard is covered, the case set
  includes representative non-standard component types and hard negatives, case coverage
  requirements pass, and all scored accuracy/citation/section/closure metrics meet strict
  thresholds. Non-standard package evidence now uses strict section-family binding, including
  hydrology, wildlife, botany, scenery, sustainability, recreation/access, land exchange, and
  minerals; regenerated findings have `79` supported components, `0` gaps, and no non-plan package
  evidence with mismatched section binding.
- Phase eval passes `10/10` phases after stale component adjudication artifacts are removed;
  `forest_plan_component_eval` passes, and the review is `reviewer_ready=true` at the phase gate.
  Phase eval now rejects stale component-adjudication eval artifacts whose recorded queue count
  differs from the current reviewer-resolution queue.
- V1 real-EA eval still fails, as intended for the current gap state. Good signals: all `13`
  required EA section families were detected, all `26` baseline authorities matched source records
  and document roles, all baseline document roles matched, citation/source-record match rates are
  `1.0`, and all Custer Gallatin forest-plan expectations pass, including zero open standard
  reviewer-resolution items.
- Remaining V1 blockers: three categorical-exclusion conditionals treated as applicable where the
  V1 contract expects not-applicable, and two rule/conditional section mismatches. The forest-plan
  adjudication worklist is complete and no longer blocks `phase-eval`.

Primary failing artifacts/checks:

- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_context_summary.json` reports
  `scope_status: custer_gallatin`, `reviewer_ready: true`, `validation_passed: true`,
  `needs_reviewer_resolution: false`, `geographic_area_count: 2`, `management_area_count: 1`,
  `overlay_count: 2`, and `supporting_plan_evidence_count: 5`.
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_findings.json`
  reports `329` findings: `79` supported, `0` gap, and `250` not applicable.
- `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_applicable_standard_coverage.json`
  reports `12` applicable standards, `12` applied standards, and
  `all_applicable_standards_applied=true`.
- `source_library/reviews/v1-cg-ecid-compliance-review/compliance_validation.json` passes.
- `v1_ea_eval_results.json` failure categories:
  `conditional_false_positive=3` and `rule_section_mismatch=2`. Forest-plan expectation match rate
  is now `1.0`.
- The forest-plan component adjudication template from the prior run contained `21` pending
  non-standard items: `8` desired conditions, `2` goals, `7` guidelines, `3` objectives, and
  `1` suitability component. Those adjudications classified every item as a system miss, and the
  current resolver fixes now close them with package/plan evidence or correct not-applicable
  determinations. The current reviewer-resolution queue has `0` items, so no component adjudication
  phase is required for the latest phase eval.
- The forest-plan component eval result has been written locally at
  `source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_eval_results.json`.
  `phase-eval --review-id v1-cg-ecid-compliance-review` includes it as the passing
  `forest_plan_component_eval` phase.
- A follow-up audit tightened the last two milestone gates: component eval now checks
  review/source-set identity across component findings, applicable-standard coverage, and
  reviewer-resolution queue artifacts; citation correctness requires exact plan/package citation
  sets; phase eval rejects a stale component-eval result schema; and applicable-standard coverage
  fails if any selected standard loses LMP plan-source evidence, even when the standard is not
  applicable.

Next implementation target:

Repair the remaining V1 eval issues in the conditional-source and rule-section expectations. The
scope, applicable-standard, component eval, and non-standard component adjudication blockers are
closed; the remaining non-ready state is conditional/rule-section evaluation, not missing
forest-plan context, standard coverage, or component adjudication.

The forest-plan review evaluator now runs component-evaluation V0 by default for packages resolved
to the selected forest-plan profile. Mandatory component evaluation is committed at `8f607e4`; the
current follow-on slice adds the first NFMA standard-coverage gate.

Current session update:

- Forest-plan component adjudication tooling has been added. The template command exports current
  reviewer-resolution queue items to a stable adjudication contract plus a Markdown reviewer
  worklist; the eval command checks identity, queue coverage, completed adjudication metadata,
  resolved dispositions, and expected current status matches. Phase eval now surfaces the
  adjudication eval as a readiness phase when that artifact is present.
- The adjudication disposition taxonomy is explicit data: `true_ea_omission`, `retrieval_miss`,
  `package_section_chunking_miss`, `component_inventory_overreach`,
  `applicability_false_positive`, and `evidence_linking_miss`.
- The adjudication eval separates dispositions into `real_ea_omission` versus `system_miss`
  outcome metrics. The prior East Crazies forest-plan adjudication classified all `21` resolved
  non-standard component items as system misses and none as real EA omissions; the current queue is
  closed through resolver fixes.
- Profile-driven forest-plan scope resolution now distinguishes operative selected-profile evidence
  from incidental references to other forests. Background/reference mentions of another configured
  forest no longer force `ambiguous`, while operative evidence that the project is on another forest
  still blocks Custer Gallatin resolution.
- Negative package-location rows such as `not part of the project area` are filtered before
  geographic or management area entries are resolved.
- The real East Crazy Inspiration Divide package now resolves to Custer Gallatin scope and produces
  forest-plan component artifacts from the source-set inventory; the V1 eval contract now expects
  the generated `R1PLAN-custer-gallatin-nf-02-...` component IDs instead of the old seed fixture IDs.
- Forest-plan component evaluation V0 has been added as a required `forest-plan-resolve` stage for
  packages resolved to the selected forest-plan profile; `--forest-plan-component-inventory-path`
  only overrides the inventory path.
- New component outputs are `forest_plan_component_findings.json`,
  `forest_plan_component_findings.md`, and `forest_plan_reviewer_resolution_queue.json`.
- `config/forest_plan_component_inventory_seed.json` contains the first narrow Custer Gallatin seed
  inventory for East Crazies-relevant Crazy Mountains Backcountry Area components.
- Component validation now fails closed on source-set drift, requires supported/partial findings to
  carry both package and plan-source evidence, and turns missing package evidence into
  reviewer-resolution queue items.
- NFMA standard coverage V0 writes `forest_plan_component_inventory_coverage.json` and
  `forest_plan_applicable_standard_coverage.json`.
- Component findings now carry a structured `compliance_status`; applicable standards require
  plan-source evidence, EA package evidence, and a resolved compliance status before component
  validation can pass.
- `forest-plan-components-build` now writes source-set inventory artifacts plus
  `component_inventory_build_coverage.json`, proving selected forest-plan chunks, detected component
  labels, detected standard labels, missing detected standards, duplicate standards, and generated
  record validation before a built inventory can pass. Current build coverage also records `2`
  suppressed component-like labels with nonnumeric number tokens, such as cross-reference/table
  headings, as non-blocking inventory-quality issues instead of allowing rough IDs into the
  inventory.
- Source-set generated component inventories under
  `source_library/derived/<source_set_id>/forest_plan_components/` must have passing build coverage
  before `forest_plan_component_inventory_coverage.json` can pass during NFMA component evaluation.
- Sequence 3 forest-plan improvement work has started with a durable East Crazies fixture under
  `tests/fixtures/forest_plan_evaluator/east_crazies_profile_driven.txt`.
- The fixture proves Custer Gallatin scope, Bridger/Bangtail/Crazy Mountains Geographic Area, Crazy
  Mountains Backcountry Area, required Custer Gallatin source-record readiness, FEIS/BA/BO
  supporting routes from explicit package evidence, and reviewer-ready gating.
- Custer Gallatin ROD trigger terms were tightened so generic project decision labels such as
  `selected alternative`, `decision basis`, `objection resolution`, or `plan approval` do not route
  to the forest-plan ROD unless the package explicitly says `Record of Decision` or `ROD`.
- FEIS trigger terms were tightened so generic `plan consistency` labels do not activate FEIS
  routing unless an explicit FEIS, tiering, or incorporation cue is present.
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md` was rewritten around current RAG/legal
  RAG research: structured authority components, precise snippet retrieval, graph relationships,
  W3C PROV-style provenance, RAG-triad-style evaluation, and fail-closed audit gates.

Recent sequence commits:

- `aadbc53` - Add forest plan review harness contract
- `f11191c` - Sequence 1: add forest plan profile loader
- `c0da944` - Sequence 1 hardening: tighten profile validation
- `270bfa7` - Sequence 2: drive forest plan resolver from profiles
- `3ca34f7` - Sequence 2 hardening: close profile resolution gaps
- `8f607e4` - Add mandatory forest plan component review
- `21d30b6` - Add NFMA standard coverage gate
- `ab7f034` - Fix forest plan component inventory CLI override
- `ca29dfa` - Add forest plan component inventory builder

Implemented behavior:

- `config/forest_plan_profiles.json` contains the first forest-plan profile for Custer Gallatin.
- `forest-plan-resolve` reads forest names, ambiguous terms, required source records, area terms,
  overlays, and supporting evidence routes from the selected profile.
- `forest-plan-resolve` writes component findings, a Markdown rendering, and a reviewer-resolution
  queue from a data inventory for packages resolved to the selected forest-plan profile.
- `forest-plan-resolve` also writes selected-inventory coverage and applicable-standard coverage;
  reviewer-ready status fails when an applicable standard lacks plan evidence, package evidence, or a
  resolved compliance status.
- `forest-plan-components-build` can produce rebuildable source-set component inventories and build
  coverage from extracted forest-plan chunks.
- The current Custer Gallatin LMP inventory for `source-set-ba8d0feae79501b8` has been generated
  from extracted chunks with `329` components, `58` standards, and passing build coverage. The seed
  inventory is now a fallback/test fixture.
- Built source-set inventories fail inventory coverage when their adjacent build coverage is missing
  or failed, which prevents them from being silently used as NFMA compliance evidence.
- Default Custer Gallatin V0 output compatibility is preserved: `scope_status` still uses
  `custer_gallatin`, `not_custer_gallatin`, or `ambiguous`.
- `--forest-unit-id` and `--forest-plan-profiles-path` allow the resolver to run against another
  configured profile path.
- Other configured profiles are treated as known out-of-scope forests when Custer Gallatin is the
  selected profile.
- Default profile loading works from outside the repository working directory.

Latest verification:

Current profile-driven resolver fix verification on 2026-05-03:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --review-id v1-cg-ecid-compliance-review --reuse-package-cache
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" --output-dir source_library --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --source-set-id source-set-ba8d0feae79501b8 --review-id v1-cg-ecid-compliance-review --reuse-package-cache --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/forest_plan_component_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/v1_ecid_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --adjudication-file source_library/reviews/v1-cg-ecid-compliance-review/forest_plan_component_adjudication_template.json
UV_CACHE_DIR=/private/tmp/usfs_uv_cache PYTHONPATH=src uv run --extra dev pytest
UV_CACHE_DIR=/private/tmp/usfs_uv_cache PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/v1_ecid_real_ea_eval.json /private/tmp/v1_ecid_real_ea_eval.validated.json
git diff --check
```

Results from the latest live rerun: compliance review still passes with `43` pass findings and `1`
not applicable finding; forest-plan context validation passes with `2` geographic areas, `1`
management area, `2` overlays, and `5` supporting plan-evidence routes. Forest-plan component
validation now passes: `329` components, `58` standards, `12` applicable standards, `12` applied
standards, `0` reviewer-resolution items, and zero unresolved applicable standards. The prior
`AB-STD-RCREA-01` standard gap and the prior `21` non-standard queue items now have evidence-backed
support or correct not-applicable determinations. Component-level forest-plan eval passes all `35`
adjudicated cases with all-applicable-standard coverage. `phase-eval` passes `10/10` phases and
reports `reviewer_ready=true`;
`v1-ea-eval` reports forest-plan expectation match rate `1.0`,
section detection/source-record/document-role rates `1.0`, zero open standard reviewer-resolution
items, and remaining non-forest-plan failure categories `conditional_false_positive=3` and
`rule_section_mismatch=2`.

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_components.py tests/test_compliance_review.py tests/test_forest_plan_resolver.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --source-record-id R1PLAN-custer-gallatin-nf-02 --forest-unit-id custer-gallatin-nf --plan-version 2022
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/forest_plan_component_eval_seed.json
PYTHONPATH=src uv run --extra dev python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
python -m json.tool config/forest_plan_profiles.json /tmp/forest_plan_profiles.validated.json
python -m json.tool config/forest_plan_component_inventory_seed.json /tmp/forest_plan_component_inventory_seed.validated.json
python -m json.tool config/forest_plan_component_eval_seed.json /tmp/forest_plan_component_eval_seed.validated.json
git diff --check
```

Latest verification: full test suite passed with `220 passed, 5 subtests passed`; focused
forest-plan component eval tests passed with `5 passed`; focused component-eval phase test passed;
lint, compile, JSON validation, and whitespace checks passed. The current milestone reran component
eval (`35/35` cases), phase eval (`10/10` phases, `reviewer_ready=true`), and V1 EA eval
(`passed=false` only on `conditional_false_positive=3` and `rule_section_mismatch=2`).

## Next Sequence

Next sequence: repair the remaining V1 eval issues in the conditional-source and rule-section
expectations.

Goal:
Produce a reviewer-ready or explicitly fail-closed V1 Custer Gallatin compliance review from the
real proving package, using the current source-set component inventory and downstream source-set
promotion artifacts.

Non-goals:

- Do not rebuild the full 190-row downstream corpus unless the proving run exposes stale artifacts.
- Do not add East Crazies-specific resolver branches.
- Do not scan raw artifact filenames to decide forest-plan behavior.
- Do not broaden the output schema unless the fixture requires a minimal test-only assertion.

Relevant files:

- `docs/FOREST_PLAN_REVIEW_EVALUATOR_V1.md`
- `docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md`
- `docs/FOREST_PLAN_COMPONENT_EVALUATION_MILESTONE_PLAN.md`
- `config/forest_plan_profiles.json`
- `config/forest_plan_component_inventory_seed.json`
- `src/usfs_r1_ea_sources/forest_plan_components.py`
- `src/usfs_r1_ea_sources/forest_plan_resolver.py`
- `tests/test_forest_plan_resolver.py`
- Optional new fixture file under `tests/fixtures/` if a durable text fixture is cleaner than an
  inline package string.

Required eval signal:

- The package resolves to `scope_status=custer_gallatin` through selected profile names.
- The package resolves the Bridger, Bangtail, and Crazy Mountains Geographic Area.
- The package resolves the Crazy Mountains Backcountry Area.
- Required Custer Gallatin profile source records are present in retrieval readiness.
- FEIS, Biological Assessment, and Biological Opinion routes trigger only from explicit package
  evidence.
- ROD evidence does not trigger from generic decision labels unless explicit ROD terms are present.
- Reviewer-ready status remains citation/evidence gated.
- Component findings are produced from the inventory path with plan-source evidence, package
  evidence where present, and reviewer-resolution items for gaps.
- Stale component inventory source-set IDs fail closed.
- Applicable standards are represented in `forest_plan_applicable_standard_coverage.json`; missing
  standard package evidence blocks reviewer-ready status.

Required tests:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_resolver.py tests/test_forest_plan_profiles.py
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/forest_plan_component_inventory_seed.json /tmp/forest_plan_component_inventory_seed.validated.json
git diff --check
```

Run the full suite before committing if resolver behavior or generated output schemas change.

Commit policy:
Stage only the current sequence files, verify, and commit atomically.

Stop conditions:

- The fixture cannot prove profile-driven behavior without adding a special East Crazies runtime
  branch.
- Required source-record readiness fails because the test source library lacks a profile-required
  supporting record.
- An applicable standard would pass reviewer-ready without plan-source evidence, package evidence,
  and a resolved compliance status.

Expert alignment check for Sequence 4:

- Scott Vandegrift: readiness and reuse should be explicit; avoid unnecessary full-corpus rebuilds.
- Chuck Nicholson: the fixture should look like practitioner QA/QC, with transparent criteria and
  actionable gaps.
- Liz Esposito: every supported result must keep source-record IDs and evidence basis visible; do
  not convert the fixture into a legal conclusion.
