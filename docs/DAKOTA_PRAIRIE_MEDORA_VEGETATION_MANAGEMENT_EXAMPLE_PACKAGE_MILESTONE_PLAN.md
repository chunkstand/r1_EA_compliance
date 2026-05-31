# Dakota Prairie Medora Vegetation Management Example Package Milestone Plan

Date: 2026-05-31
Status: Resolved locally through Milestone 4 contract-backed registry and
aggregate coverage promotion.
Plan class: implementation
High-risk implementation: yes
Owner context: child packet under
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Intent lock: advance only the Dakota Prairie Medora Vegetation Management
candidate; keep it parallel to `Document_Register_Master` and promote only the
tracked reviewer-ready Medora package.

## Purpose And Current Evidence

Advance the Dakota Prairie Grasslands Medora Vegetation Management Project
example candidate to governed primary-example status only after tracked V1
eval, component eval, review `phase-eval`, aggregate coverage, registry eval,
docs, and focused tests pass.

Identity:

- `forest_unit_id="dakota-prairie-grasslands"`
- `review_id="region1-example-dakota-prairie-medora-vegetation-management-66886"`
- `source_set_id="source-set-f70ea11e04ae3d53"`
- official project page `https://www.fs.usda.gov/r01/dpg/projects/66886`
- official Box/Pinyon documents page
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/284408882208`

Current evidence:

- Forest Service project readback on 2026-05-31 identifies project `66886` as
  `Medora Vegetation Management Project`, status `Completed`, expected analysis
  type `Environmental Assessment`, lead unit `Medora Ranger District`, and
  decision signed date `12/04/2025`.
- Local ignored package authority under
  `source_library/reviews/_intake/region1-example-dakota-prairie-medora-vegetation-management-66886/`
  records `7` files across `4` folders, `40,860,421` actual bytes, and
  `failure_count=0`.
- Base `ea-review` passes on `source-set-f70ea11e04ae3d53` with `7/7`
  extracted files, `417` package chunks, `package_failed_count=0`, `5` pass
  findings, and `reviewer_ready=true`.
- The review-local Dakota component inventory builds on f70 with `394`
  components: `9` goals, `223` guidelines, `1` objective, and `161` standards.
  Component inventory coverage and source accuracy pass.
- The refreshed Dakota profile resolves Medora package scope with
  `scope_status="dakota_prairie_grasslands"`, `project_location_signal_count=1`,
  `geographic_area_count=2`, `management_area_count=9`, `overlay_count=0`, and
  no blocking missing Dakota source records. Component findings now report
  `394` applicable components: `10` supported and `384` gap findings.
- Tracked component adjudication at
  `config/forest_plan_component_adjudications/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
  resolves the current `384/384` queue as `evidence_linking_miss` system misses
  with `0` pending items and `0` real EA omissions.
- Tracked applicability adjudication at
  `config/applicability_adjudications/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
  resolves the single species-supporting authority conflict as
  `human_applicable`; applicability validation now reports `460` candidate
  authorities, `47` applicable, `413` not applicable, `0` unresolved, and a
  generated `47`-rule pack.
- `compliance-review` is reviewer-ready and validation-passed with `47`
  findings: `28` pass, `18` uncertain, and `1` gap.
- Tracked V1 eval contract
  `config/v1_dakota_prairie_medora_real_ea_eval.json` passes with
  `contract_status="reviewer_ready"`, and tracked component eval contract
  `config/forest_plan_component_evals/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
  passes `394/394` cases with `161` applicable standards.
- Real-package coverage passes with `covered_slot_count=10`,
  `reviewer_ready_slot_count=10`, `distinct_forest_count=9`, and
  `distinct_package_style_count=16`; component coverage passes
  `covered_review_count=11/11`; registry eval passes with
  `review_example_count=10`, `reviewer_ready_example_count=10`,
  `distinct_governed_example_forest_count=9`, and
  `profile_guidance_only_count=1`.
- Review `phase-eval` passes and is reviewer-ready for `28/28` phases with
  `blockers=[]`, `declared_review_contract=true`, and
  `contract_backed_promotion_ready=true`.
- The Dakota registry row now routes as `real_package_examples_available` with
  `primary_example_id="dpg-medora-vegetation-management-forest-specific"`.

## Intent Hierarchy

- Invariant: Medora remains Dakota Prairie-only package evidence and stays
  parallel to `Document_Register_Master`.
- Optimization target: preserve package authority, f70 source readiness,
  component-inventory evidence, and contract-backed promotion evidence.
- Acceptable tradeoff: no workbook promotion; the package remains a parallel
  forest-specific example.
- Non-negotiables: do not weaken tests, evals, registry thresholds, component
  adjudication requirements, or downstream reviewer gates to make promotion
  pass.

## Goal, Non-Goals, And Scope

Goal: promote Dakota Prairie Grasslands to a governed primary real-package
example after contract-backed reviewer-stack and aggregate gates pass.

Non-goals:

- Do not stage ignored `source_library/` package or derived artifacts.
- Do not change workbook `Document_Register_Master` or promote Medora as a
  workbook source row.

Scope:

- In scope: Dakota V1 eval and component eval contracts, real-package coverage,
  component coverage, registry promotion, aggregate gates, routing/current-state
  docs, focused tests, and this plan.
- Out of scope: ignored `source_library/` package artifacts and workbook
  source-register changes.

## Owner Surfaces And Placement

- packet:
  `docs/DAKOTA_PRAIRIE_MEDORA_VEGETATION_MANAGEMENT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- replay context:
  `config/replay_contexts/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
- registry, coverage, and component manifests:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`
- eval contracts:
  `config/v1_dakota_prairie_medora_real_ea_eval.json`,
  `config/forest_plan_component_evals/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
- docs:
  `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- tests:
  `tests/test_dakota_prairie_medora_contracts.py`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_forest_plan_component_eval_coverage.py`,
  `tests/test_forest_plan_inventory_build_manifest.py`,
  `tests/test_forest_specific_example_package_registry.py`

## Risk And Weak-Point Prevention

| Weak point | Owner surface | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| Component adjudication hides real EA omissions | Component adjudication config | `forest-plan-component-adjudication-eval` and rerun `forest-plan-resolve` | Any pending item, unsupported rationale, or unresolved expectation remains |
| Applicability conflict remains unresolved | Applicability adjudication config | `applicability-adjudication-eval`, `applicability-validate`, and generated rule-pack validation | Any unresolved authority remains or generated rule pack is not ready |
| Dakota component inventory drifts across source sets | Inventory manifest and focused test | `tests/test_forest_plan_inventory_build_manifest.py` | Dakota f70 support is dropped or active full-canonical support is lost |
| Registry promotion outruns tracked contracts | Registry, coverage, V1 eval, component eval, and focused tests | `v1-ea-eval`, `forest-plan-component-eval`, `phase-eval`, aggregate evals, and focused tests | Dakota promotes without `declared_review_contract=true`, `contract_backed_promotion_ready=true`, and green aggregate coverage |

## Milestone Sequence

### Milestone 1 - Package Authority And Base Review

Outcome label: `reduced`

- Box intake and download artifacts exist locally with `7` downloaded files,
  `40,860,421` actual bytes, and `failure_count=0`.
- `ea-review` passes on the local intake package with `7/7` extracted files,
  `417` package chunks, and `reviewer_ready=true`.
- A tracked replay context records official authority URLs, intake paths,
  source set, and forest unit.

### Milestone 2 - Forest-Plan Source And Component Preflight

Outcome label: `reduced`

- Dakota component inventory build is allowed on both
  `source-set-4fb59e9eb43045cb` and `source-set-f70ea11e04ae3d53`.
- Review-local component inventory builds on f70 with `394` components and
  `161` standards.
- `forest-plan-resolve` resolves Dakota scope and source readiness with no
  blocking missing Dakota source records.
- This milestone originally stopped before registry promotion because the
  component adjudication template still had `394` pending items; Milestone 3
  supersedes that blocker with a tracked `384/384` current-queue adjudication.

### Milestone 3 - Reviewer-Stack Replay

Outcome label: `reduced`

- Dakota profile context terms resolve Medora package scope to
  `scope_status="dakota_prairie_grasslands"` with `2` geographic areas,
  `9` management areas, no blocking missing source records, and no unresolved
  component adjudication items.
- Tracked component adjudication resolves `384/384` current queue items as
  system misses with `0` pending items.
- Applicability validation resolves the `460`-authority universe to `47`
  applicable and `413` not applicable authorities with `0` unresolved
  authorities, and generated rule-pack validation produces `47` rules.
- Compliance review is reviewer-ready with `47` findings.
- Review `phase-eval` passes and is reviewer-ready for `27/27` phases.
- At Milestone 3 closeout, registry promotion stopped because tracked review
  contracts and aggregate coverage gates were not yet present.

### Milestone 4 - Contract-Backed Registry Promotion

Outcome label: `resolved`

Completed locally:

- Tracked Dakota V1 eval contract
  `config/v1_dakota_prairie_medora_real_ea_eval.json` passes with
  `contract_status="reviewer_ready"` and `21/21` conditional source
  expectations.
- Tracked Dakota forest-plan component eval contract
  `config/forest_plan_component_evals/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
  passes `394/394` cases, including `161` applicable standards and the
  adjudicated `384` open reviewer-resolution items.
- Dakota is load-bearing in real-package coverage and component coverage:
  real-package coverage passes `10/10` reviewer-ready slots, component
  coverage passes `11/11` required reviews, and registry eval passes `10`
  reviewer-ready examples across `9` governed forests.
- Review `phase-eval` reruns green at `28/28` phases with
  `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`.
- `config/forest_specific_example_package_registry_v1.json` promotes
  `dakota-prairie-grasslands` to `real_package_examples_available` with
  `primary_example_id="dpg-medora-vegetation-management-forest-specific"`.

## Verification Gates

Run before committing this resolved packet:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --eval-file config/v1_dakota_prairie_medora_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --eval-file config/forest_plan_component_evals/region1-example-dakota-prairie-medora-vegetation-management-66886.json
PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library --manifest config/forest_plan_component_eval_coverage_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886
PYTHONPATH=src uv run --extra dev pytest tests/test_dakota_prairie_medora_contracts.py tests/test_forest_plan_component_eval_coverage.py tests/test_forest_specific_example_package_registry.py tests/test_real_package_review_coverage_eval.py tests/test_forest_specific_example_package_eval.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py
python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --new-plan docs/DAKOTA_PRAIRIE_MEDORA_VEGETATION_MANAGEMENT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md
git diff --check
```

Generated-evidence gates already run for this packet:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources box-folder-intake --root-folder-url https://usfs-public.app.box.com/v/PinyonPublic/folder/284408882208 --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --output-dir source_library --download
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review --package-path source_library/reviews/_intake/region1-example-dakota-prairie-medora-vegetation-management-66886 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-dakota-prairie-medora-vegetation-management-66886
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library/reviews/region1-example-dakota-prairie-medora-vegetation-management-66886/component_inventory_build --source-set-id source-set-f70ea11e04ae3d53 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json --forest-unit-id dakota-prairie-grasslands --chunks-path source_library/derived/source-set-f70ea11e04ae3d53/chunks/chunks.jsonl
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve --package-path source_library/reviews/_intake/region1-example-dakota-prairie-medora-vegetation-management-66886 --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --forest-unit-id dakota-prairie-grasslands --forest-plan-component-inventory-path source_library/reviews/region1-example-dakota-prairie-medora-vegetation-management-66886/component_inventory_build/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json --reuse-package-cache
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-template --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --adjudication-file config/forest_plan_component_adjudications/region1-example-dakota-prairie-medora-vegetation-management-66886.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-determine --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-eval --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --source-set-id source-set-f70ea11e04ae3d53 --adjudication-file config/applicability_adjudications/region1-example-dakota-prairie-medora-vegetation-management-66886.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-adjudication-apply --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --source-set-id source-set-f70ea11e04ae3d53 --adjudication-file config/applicability_adjudications/region1-example-dakota-prairie-medora-vegetation-management-66886.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886 --source-set-id source-set-f70ea11e04ae3d53
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-dakota-prairie-medora-vegetation-management-66886
```

Expected current resolved result: `phase-eval` passes `28/28` phases and
reports `reviewer_ready=true`, `declared_review_contract=true`, and
`contract_backed_promotion_ready=true`.

## Acceptance Criteria

- Replay context exists and points to official authority URLs, the local intake
  package, f70 source set, and Dakota forest unit.
- Dakota component-inventory manifest compatibility includes both
  `source-set-4fb59e9eb43045cb` and `source-set-f70ea11e04ae3d53`.
- Dakota profile context includes Medora Ranger District, Badlands/Rolling
  Prairie geographic areas, and management-area terms needed by the package
  replay.
- Component adjudication resolves the current `384/384` queue with `0` pending
  items and `0` real EA omissions.
- Applicability adjudication resolves the single conflict, generated rule-pack
  validation produces `47` rules, compliance review is reviewer-ready, and
  review `phase-eval` passes `28/28` phases with contract-backed promotion
  readiness.
- Dakota V1 eval and component eval contracts are tracked and pass.
- Dakota registry guidance names Medora as the governed primary example with
  `routing_status="real_package_examples_available"` and
  `primary_example_id="dpg-medora-vegetation-management-forest-specific"`.
- Focused tests and aggregate evals pass with `review_example_count=10`,
  `reviewer_ready_example_count=10`, `profile_guidance_only_count=1`,
  `covered_slot_count=10`, and `covered_review_count=11/11`.
- Routing, current-state, handoff, and umbrella docs identify Medora as
  resolved and promoted while preserving the parallel-to-workbook boundary.

## Documentation And Handoff

Update `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` before
commit. These docs must say Dakota is resolved and promoted, and must preserve
the parallel-to-`Document_Register_Master` boundary.

## Stop Conditions

- Stop if `forest-plan-resolve` reports scope other than
  `dakota_prairie_grasslands`.
- Stop if any required Dakota source records are missing from f70 retrieval.
- Stop if a change would promote Dakota while V1 eval, component eval,
  coverage, registry eval, or `phase-eval` is red.
- Stop if future adjudication finds true EA omissions that require typed-blocked
  status instead of reviewer-ready promotion.

## Commit Closeout

Commit only the tracked promotion slice: V1/component eval contracts,
coverage/registry manifests, focused tests, this plan, and routing/current-state
docs. Do not stage ignored `source_library/` package or review artifacts.

## Residual Risks And Next Routing

No active Dakota child slice remains after Milestone 4. Kootenai National
Forest is now the only `profile_eval_guidance_only` forest row without a
governed real package example.

## Closeout Outcome Record

- Outcome label: `resolved locally`.
- Reduced packet closeout commit: `7ac8e08` (`Open Dakota Prairie Medora
  example packet`).
- Milestone 4 promotion closeout commit: `bef9258` (`Promote Dakota Prairie
  Medora example`).
- Closeout scope: package authority, base review, f70 component inventory,
  source readiness, governed registry guidance, routing docs, and focused
  contract tests.
- Promotion scope: Dakota V1 eval, component eval, real-package coverage,
  component coverage, registry promotion, focused tests, docs, and review
  `phase-eval` are green locally.
- Residual blocker: none in the Dakota-owned packet. Remaining forest-specific
  expansion work is Kootenai example selection, if the lane continues.
