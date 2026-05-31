# Dakota Prairie Medora Vegetation Management Example Package Milestone Plan

Date: 2026-05-31
Status: Active reduced packet; package authority and f70 forest-plan preflight
are closed locally, but registry promotion is blocked by component adjudication.
Plan class: implementation
High-risk implementation: yes
Owner context: child packet under
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Intent lock: advance only the Dakota Prairie Medora Vegetation Management
candidate; keep it parallel to `Document_Register_Master` and unpromoted until
reviewer-stack gates pass.

## Purpose And Current Evidence

Open the Dakota Prairie Grasslands Medora Vegetation Management Project example
candidate without claiming governed reviewer-ready status.

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
- `forest-plan-resolve` resolves `scope_status="dakota_prairie_grasslands"`
  and source-record readiness with no blocking missing Dakota source records.
  Component findings validate, but all `394` component findings remain
  `needs_reviewer_resolution`; the adjudication template has `384`
  `missing_package_evidence` items and `10` `needs_reviewer_resolution` items.
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

Goal: preserve the verified local evidence needed for a future governed Dakota
promotion while preventing accidental registry or coverage promotion before
component adjudication and downstream review gates pass.

Non-goals:

- Do not promote Dakota Prairie Grasslands to
  `real_package_examples_available`.
- Do not create V1 eval, component-eval, compliance, or real-package coverage
  slots before the reviewer stack is green.
- Do not auto-classify the `394` component adjudication items without
  evidence-backed review.
- Do not stage ignored `source_library/` package or derived artifacts.

Scope:

- In scope: replay context, component-inventory source-set compatibility,
  registry guidance, routing/current-state docs, focused tests, and this plan.
- Out of scope: component adjudication content, V1 eval, compliance review,
  real-package coverage, registry promotion, and workbook source-register
  changes.

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
| Component adjudication hides real EA omissions | Future component adjudication config | `forest-plan-component-adjudication-eval` and rerun `forest-plan-resolve` | Any pending item, unsupported rationale, or unresolved expectation remains |
| Dakota component inventory drifts across source sets | Inventory manifest and focused test | `tests/test_forest_plan_inventory_build_manifest.py` | Dakota f70 support is dropped or active full-canonical support is lost |
| Registry promotion outruns review evidence | Registry, coverage, and focused test | `tests/test_forest_specific_example_package_registry.py` plus aggregate eval | Dakota leaves `profile_eval_guidance_only` before reviewer-stack gates pass |

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
- Stop before registry promotion because the component adjudication template
  still has `394` pending items.

### Milestone 3 - Reviewer-Stack Promotion

Outcome label: `resolved`

Not started. Preconditions:

- Produce governed component adjudication for all `394` current queue items and
  pass `forest-plan-component-adjudication-eval`.
- Rerun `forest-plan-resolve` to `validation_passed=true` and
  `reviewer_ready=true` without pending adjudication.
- Run applicability validation/adjudication, generated rule-pack validation,
  compliance review, V1 eval, component eval, review `phase-eval`, real-package
  coverage eval, forest-specific registry eval, and component-coverage eval.
- Only then update registry, coverage, eval contracts, and promotion docs.

## Verification Gates

Run before committing this reduced packet:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_specific_example_package_registry.py
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
```

Expected current reduced result: the final `forest-plan-resolve` command exits
closed until adjudication exists, even though source readiness and component
finding validation are green.

## Acceptance Criteria

- Replay context exists and points to official authority URLs, the local intake
  package, f70 source set, and Dakota forest unit.
- Dakota component-inventory manifest compatibility includes both
  `source-set-4fb59e9eb43045cb` and `source-set-f70ea11e04ae3d53`.
- Dakota registry guidance names the active Medora packet while preserving
  `routing_status="profile_eval_guidance_only"` and
  `primary_example_id=null`.
- Focused tests and `forest-specific-example-package-eval` pass with
  `review_example_count=9`, `reviewer_ready_example_count=9`, and
  `profile_guidance_only_count=2`.
- Routing, current-state, handoff, and umbrella docs identify Medora as active
  and reduced, with the `394`-item component-adjudication blocker explicit.

## Documentation And Handoff

Update `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`,
`docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, and
`docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` before
commit. These docs must say Dakota is active but unpromoted and preserve the
component-adjudication blocker count.

## Stop Conditions

- Stop if `forest-plan-resolve` reports scope other than
  `dakota_prairie_grasslands`.
- Stop if any required Dakota source records are missing from f70 retrieval.
- Stop if a change would promote Dakota before component adjudication and
  downstream reviewer gates pass.
- Stop if future adjudication finds true EA omissions that require typed-blocked
  status instead of reviewer-ready promotion.

## Commit Closeout

Commit only the tracked reduced packet slice: replay context, manifest
compatibility, focused tests, this plan, and routing/current-state docs. Do not
stage ignored `source_library/` package or review artifacts.

## Residual Risks And Next Routing

The next executable slice is Milestone 3 component adjudication and
reviewer-stack promotion. Until that closes, Dakota Prairie remains one of the
two `profile_eval_guidance_only` forest rows and this package is not a governed
example.

## Closeout Outcome Record

- Outcome label: `reduced locally`.
- Closeout scope: package authority, base review, f70 component inventory,
  source readiness, unpromoted registry guidance, routing docs, and focused
  contract tests.
- Residual blocker: `394` component adjudication items remain pending before
  promotion.
