# Dakota Prairie Medora Vegetation Management Example Package Milestone Plan

Date: 2026-05-31
Status: Active promotion-progress packet; package authority, f70 forest-plan
preflight, component adjudication, applicability, compliance review, and
review `phase-eval` are closed locally, but registry promotion is blocked by
missing tracked V1/component eval contracts and aggregate coverage promotion.
Plan class: implementation
High-risk implementation: yes
Owner context: child packet under
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Intent lock: advance only the Dakota Prairie Medora Vegetation Management
candidate; keep it parallel to `Document_Register_Master` and unpromoted until
reviewer-stack gates pass.

## Purpose And Current Evidence

Advance the Dakota Prairie Grasslands Medora Vegetation Management Project
example candidate toward promotion without claiming governed primary-example
status before contract-backed promotion gates exist.

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
- Review `phase-eval` passes and is reviewer-ready for `27/27` phases with
  `blockers=[]`, but `declared_review_contract=false` and
  `contract_backed_promotion_ready=false`.
- The Dakota registry row remains `profile_eval_guidance_only` with
  `primary_example_id=null`.

## Intent Hierarchy

- Invariant: Medora remains Dakota Prairie-only package evidence and stays
  parallel to `Document_Register_Master`.
- Optimization target: preserve package authority, f70 source readiness, and
  component-inventory evidence for a future reviewer-stack promotion.
- Acceptable tradeoff: close this slice as `reduced` while promotion surfaces
  stay unpromoted.
- Non-negotiables: do not weaken tests, evals, registry thresholds, component
  adjudication requirements, or downstream reviewer gates to make promotion
  pass.

## Goal, Non-Goals, And Scope

Goal: preserve the verified local reviewer-stack evidence needed for governed
Dakota promotion while preventing accidental registry or coverage promotion
before V1 eval, component eval, and aggregate promotion contracts pass.

Non-goals:

- Do not promote Dakota Prairie Grasslands to
  `real_package_examples_available`.
- Do not create V1 eval, component-eval, or real-package coverage slots before
  the corresponding tracked contract artifacts are authored and pass.
- Do not stage ignored `source_library/` package or derived artifacts.

Scope:

- In scope: Dakota profile context terms, component and applicability
  adjudication configs, reviewer-stack reruns, registry guidance,
  routing/current-state docs, focused tests, and this plan.
- Out of scope: V1 eval contract, component-eval contract, real-package
  coverage, registry promotion, and workbook source-register changes.

## Owner Surfaces And Placement

- packet:
  `docs/DAKOTA_PRAIRIE_MEDORA_VEGETATION_MANAGEMENT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- replay context:
  `config/replay_contexts/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
- registry and component manifest:
  `config/forest_specific_example_package_registry_v1.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`
- docs:
  `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- tests:
  `tests/test_forest_plan_inventory_build_manifest.py`,
  `tests/test_forest_specific_example_package_registry.py`

## Risk And Weak-Point Prevention

| Weak point | Owner surface | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| Component adjudication hides real EA omissions | Component adjudication config | `forest-plan-component-adjudication-eval` and rerun `forest-plan-resolve` | Any pending item, unsupported rationale, or unresolved expectation remains |
| Applicability conflict remains unresolved | Applicability adjudication config | `applicability-adjudication-eval`, `applicability-validate`, and generated rule-pack validation | Any unresolved authority remains or generated rule pack is not ready |
| Dakota component inventory drifts across source sets | Inventory manifest and focused test | `tests/test_forest_plan_inventory_build_manifest.py` | Dakota f70 support is dropped or active full-canonical support is lost |
| Registry promotion outruns tracked contracts | Registry, coverage, V1 eval, component eval, and focused tests | `phase-eval`, `tests/test_forest_specific_example_package_registry.py`, and aggregate evals | Dakota leaves `profile_eval_guidance_only` before `declared_review_contract=true` and aggregate coverage gates pass |

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
- Stop before registry promotion because `declared_review_contract=false` and
  `contract_backed_promotion_ready=false`.

### Milestone 4 - Contract-Backed Registry Promotion

Outcome label: `resolved`

Not started. Preconditions:

- Author and pass a tracked Dakota V1 eval contract.
- Author and pass a tracked Dakota forest-plan component eval contract.
- Rerun review `phase-eval` to `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`.
- Add real-package coverage and forest-plan component coverage slots only after
  the tracked review contracts pass.
- Promote the Dakota registry row only when real-package coverage,
  forest-specific registry eval, component-coverage eval, and docs all pass.

## Verification Gates

Run before committing this reduced packet:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_specific_example_package_registry.py
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_profiles.py
PYTHONPATH=src python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library --manifest config/forest_specific_example_package_registry_v1.json
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

Expected current reduced result: `phase-eval` passes `27/27` phases and
reports `reviewer_ready=true`, while promotion remains blocked by
`declared_review_contract=false` and `contract_backed_promotion_ready=false`.

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
  review `phase-eval` passes `27/27` phases.
- Dakota registry guidance names the active Medora packet while preserving
  `routing_status="profile_eval_guidance_only"` and
  `primary_example_id=null`.
- Focused tests and `forest-specific-example-package-eval` pass with
  `review_example_count=9`, `reviewer_ready_example_count=9`, and
  `profile_guidance_only_count=2`.
- Routing, current-state, handoff, and umbrella docs identify Medora as active
  and reduced, with the missing tracked V1/component eval and coverage
  promotion blockers explicit.

## Documentation And Handoff

Update `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` before
commit. These docs must say Dakota is active but unpromoted and preserve the
contract-backed promotion blockers.

## Stop Conditions

- Stop if `forest-plan-resolve` reports scope other than
  `dakota_prairie_grasslands`.
- Stop if any required Dakota source records are missing from f70 retrieval.
- Stop if a change would promote Dakota before V1 eval, component eval,
  coverage, and registry gates pass.
- Stop if future adjudication finds true EA omissions that require typed-blocked
  status instead of reviewer-ready promotion.

## Commit Closeout

Commit only the tracked promotion-progress packet slice: profile context,
component/applicability adjudication configs, focused tests, this plan, and
routing/current-state docs. Do not stage ignored `source_library/` package or
review artifacts.

## Residual Risks And Next Routing

The next executable slice is Milestone 4 contract-backed registry promotion.
Until that closes, Dakota Prairie remains one of the two
`profile_eval_guidance_only` forest rows and this package is not a governed
example.

## Closeout Outcome Record

- Outcome label: `reduced locally`.
- Reduced packet closeout commit: `7ac8e08` (`Open Dakota Prairie Medora
  example packet`).
- Closeout scope: package authority, base review, f70 component inventory,
  source readiness, unpromoted registry guidance, routing docs, and focused
  contract tests.
- Promotion-progress scope: Dakota profile context, component adjudication,
  applicability adjudication, generated rule pack, compliance review, and
  review `phase-eval` are green locally.
- Residual blocker: tracked V1 eval, tracked component eval, real-package
  coverage, component coverage, and registry promotion remain before governed
  primary-example promotion.
