# Kootenai Trojan Defense Example Package Milestone Plan

Date: 2026-05-31
Status: Resolved locally through governed primary-example promotion; package-local gates are green, while review `phase-eval` still reports inherited shared rule-claim direct-eval debt outside the Kootenai slot.
Plan class: implementation
High-risk implementation: yes
Owner context: child packet under `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
Commit policy: close the milestone with implementation, tests, docs, handoff, verification evidence, and one atomic local commit.

## Purpose And Current Evidence

Promote the Kootenai National Forest Trojan Defense Hazardous Fuels Reduction Project as the governed primary Kootenai forest-specific example package, while keeping the package parallel to `Document_Register_Master`.

Identity:

- `example_id="knf-trojan-defense-forest-specific"`
- `review_id="region1-example-kootenai-trojan-defense-64354"`
- `forest_unit_id="kootenai-nf"`
- `source_set_id="source-set-f70ea11e04ae3d53"`
- official project page `https://www.fs.usda.gov/r01/kootenai/projects/64354`
- official Box/Pinyon documents page `https://usfs-public.app.box.com/v/PinyonPublic/folder/214150735755`

Current evidence:

- Box intake downloaded `74/74` files with `152,732,803` actual bytes and `failure_count=0`.
- Base `ea-review` passes with `74/74` extracted files, `3,750` package chunks, `package_failed_count=0`, and `reviewer_ready=true`.
- Kootenai forest-plan profile terms resolve Three Rivers Ranger District, Bull Geographic Area, MA2, MA3, MA6, RHCA, and WUI scope.
- Review-local component inventory builds on f70 with `53` components: `18` desired conditions, `15` objectives, `12` guidelines, and `8` standards.
- `forest-plan-resolve` resolves `scope_status="kootenai_nf"` with `1` geographic area, `3` management areas, `2` overlays, and all required Kootenai source records indexed.
- Component adjudication resolves the current `34/34` queue items as system misses with `0` pending items and `0` real EA omissions.
- Applicability adjudication resolves `6/6` items as applicable; applicability validation reports `47` applicable, `72` not applicable, and `0` unresolved authorities.
- `compliance-review` passes with reviewer-ready matrix/PDF artifacts and `47` findings: `28` pass, `18` uncertain, and `1` gap.
- V1 eval passes with `contract_status="reviewer_ready"`; component eval passes `53/53` cases with `8` applicable standards.
- Aggregate gates pass with `real-package-review-coverage-eval` at `covered_slot_count=11`, `reviewer_ready_slot_count=11`, `distinct_forest_count=10`; `forest-plan-component-eval-coverage` at `covered_review_count=12/12`, `distinct_forest_count=10`; and `forest-specific-example-package-eval` at `review_example_count=11`, `reviewer_ready_example_count=11`, `distinct_governed_example_forest_count=10`, `profile_guidance_only_count=0`.
- Review `phase-eval` confirms `declared_review_contract=true`, `contract_backed_promotion_ready=true`, and Kootenai review-scope summaries present, but remains red on inherited shared `rule_claim_binding` direct-eval identity/validation debt.

## Goal, Non-Goals, And Scope

Goal: make Kootenai route to a governed Trojan Defense primary example after package authority, forest-plan, applicability, compliance, V1, component, and aggregate coverage gates pass.

Non-goals:

- Do not stage ignored `source_library/` package bytes or generated review outputs.
- Do not add Trojan Defense rows to `Document_Register_Master`.
- Do not repair unrelated shared rule-claim direct-eval debt inside this Kootenai promotion commit.

Scope:

- In scope: Kootenai profile terms, replay context, adjudication contracts, V1/component eval contracts, aggregate manifests, registry routing, focused tests, docs, and handoff.
- Out of scope: workbook promotion, source-capture policy changes, and broad downstream rule-claim recalibration.

## Intent Lock

This packet is locked to Kootenai National Forest Trojan Defense only. Success
means `kootenai-nf` has a governed package-local example whose runtime
forest-plan scope, registry route, replay context, V1 eval, component eval, and
aggregate coverage slots agree on
`review_id="region1-example-kootenai-trojan-defense-64354"` and
`example_id="knf-trojan-defense-forest-specific"`. Do not use this packet to
repair unrelated rule-claim direct-eval quality debt or to generalize Trojan
Defense as non-Kootenai Region 1 guidance.

## Intent Hierarchy

- Invariant: Trojan Defense is Kootenai-only example evidence and remains parallel to `Document_Register_Master`.
- Optimization target: preserve package authority, f70 source-set identity, reviewer-ready V1/component contracts, and per-forest aggregate coverage.
- Acceptable tradeoff: record inherited shared rule-claim direct-eval red separately from the Kootenai package-local green state.
- Non-negotiables: no weakened tests, no relaxed registry thresholds, no early workbook promotion, and no hidden reuse for non-Kootenai forests.

## Owner Surfaces And Placement

- Packet: `docs/KOOTENAI_TROJAN_DEFENSE_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- Replay context: `config/replay_contexts/region1-example-kootenai-trojan-defense-64354.json`
- Eval contracts: `config/v1_kootenai_trojan_defense_real_ea_eval.json`, `config/forest_plan_component_evals/region1-example-kootenai-trojan-defense-64354.json`
- Adjudication contracts: `config/applicability_adjudications/region1-example-kootenai-trojan-defense-64354.json`, `config/forest_plan_component_adjudications/region1-example-kootenai-trojan-defense-64354.json`
- Registry and coverage manifests: `config/forest_specific_example_package_registry_v1.json`, `config/v1_real_package_review_coverage_v1.json`, `config/forest_plan_component_eval_coverage_v1.json`, `config/r1_forest_plan_component_inventory_build_manifest.json`
- Docs and handoff: `README.md`, `docs/AGENT_START_HERE.md`, `docs/CURRENT_ROUTING.md`, `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`, `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- Tests: `tests/test_kootenai_trojan_defense_contracts.py`, manifest/registry/profile focused tests.

## Weak-Point Prevention

| Weak point | Owner surface | Prevention gate | Fail threshold |
| --- | --- | --- | --- |
| Kootenai package gets reused as generic Region 1 evidence | registry and docs | registry row, example ID, and latest-routing tests | Any non-Kootenai forest points to `knf-trojan-defense-forest-specific` |
| Profile-only status remains after promotion | registry and aggregate eval | `forest-specific-example-package-eval` | `profile_guidance_only_count` is not `0` |
| Component gaps are mistaken for real EA omissions | component adjudication contract | `forest-plan-component-adjudication-eval` | Any pending item or real EA omission remains |
| Shared direct-eval red gets reported as Kootenai package failure | handoff/current-state docs | `phase-eval` readback and residual-risk note | Kootenai review-scope summaries are missing or not reviewer-ready |

## Milestone Sequence

1. Package authority and base review: run Box intake, download the governed package subset, and prove `ea-review` reviewer readiness.
2. Forest-plan and component scope: add Kootenai profile terms, build component inventory on f70, resolve forest-plan context, and adjudicate current queue items.
3. Applicability and compliance: adjudicate applicability conflicts, validate generated rule pack, and run `compliance-review` with matrix/PDF outputs.
4. Promotion contracts: add V1/component eval contracts, replay context, coverage slots, registry routing, focused tests, and docs/handoff.
5. Closeout: rerun focused evals and tests, record inherited shared residuals, and commit only the tracked milestone slice.

## Verification Gates

- `box-folder-intake` passed: `74` downloaded, `failure_count=0`.
- `ea-review` passed: `74/74` extracted, `3,750` chunks, `reviewer_ready=true`.
- `forest-plan-components-build` passed for Kootenai f70 manifest path with `53` components and `8` standards.
- `forest-plan-resolve` passed with `scope_status="kootenai_nf"` and `reviewer_ready=true`.
- `forest-plan-component-adjudication-eval` passed `34/34` current queue items with `0` pending.
- `applicability-validate` passed with `47` applicable, `72` not applicable, `0` unresolved.
- `compliance-review` passed with reviewer-ready matrix/PDF artifacts.
- `v1-ea-eval` passed with `contract_status="reviewer_ready"`.
- `forest-plan-component-eval` passed `53/53` cases.
- `real-package-review-coverage-eval`, `forest-plan-component-eval-coverage`, and `forest-specific-example-package-eval` passed.
- `phase-eval` readback: Kootenai review scope is contract-backed and present, but inherited shared rule-claim direct-eval debt keeps the whole phase aggregate red.

## Acceptance Criteria

- `kootenai-nf` routes `real_package_examples_available` with primary example `knf-trojan-defense-forest-specific`.
- All ten Region 1 forests have governed real package examples in the registry.
- Aggregate registry summary reports `review_example_count=11`, `reviewer_ready_example_count=11`, `distinct_governed_example_forest_count=10`, and `profile_guidance_only_count=0`.
- Focused tests and doc parity reflect Kootenai as the latest resolved forest-specific example.

## Documentation And Handoff

Update README, current routing, current system state, session handoff, agent-start guidance, and the umbrella forest-specific packet with Kootenai promotion evidence and the inherited rule-claim residual.

## Commit Closeout

Stage only tracked Kootenai milestone surfaces: configs, tests, docs, and this plan. Do not stage ignored `source_library/` outputs.

Executable closeout commands:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_kootenai_trojan_defense_contracts.py tests/test_forest_plan_profiles.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_component_eval_coverage.py tests/test_forest_specific_example_package_registry.py tests/test_real_package_review_coverage_eval.py tests/test_forest_specific_example_package_eval.py
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
```

## Closeout Outcome Record

- Package-local gates: green through intake, `ea-review`, component inventory,
  `forest-plan-resolve`, component adjudication, applicability, generated rule
  pack, compliance review, V1 eval, component eval, real-package coverage,
  component coverage, and registry eval.
- Aggregate route outcome: all `10` Region 1 forests now have governed real
  package examples; `profile_guidance_only_count=0`.
- Residual route outcome: review `phase-eval` remains red only on inherited
  shared `rule_claim_binding` direct-eval debt, not Kootenai package-local
  promotion scope.

## Stop Conditions

- Stop if any Kootenai review-local V1/component/applicability/compliance/aggregate gate fails.
- Stop if registry promotion requires weakening thresholds.
- Stop if resolving shared rule-claim direct-eval debt requires source-code or generated-artifact scope beyond this Kootenai packet.

## Residual Risks And Next Routing

The only known residual after Kootenai promotion is inherited shared rule-claim direct-eval debt: `phase-eval` reports `rule_claim_binding` as stale/unsupported, and a direct `rule-claim-eval` refresh stops at `rule_claim_link_scores_are_supported`. Route that to a separate downstream rule-claim quality packet; do not reopen the Kootenai example package unless a Kootenai-specific gate regresses.
