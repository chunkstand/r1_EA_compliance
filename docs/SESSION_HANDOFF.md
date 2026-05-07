# Session Handoff

Date: 2026-05-06

## Current Project SOW Package Branch Handoff

Branch/worktree:

- Branch: `codex/nepa-project-sow-package`
- Worktree: `/Users/chunkstand/projects/usfs-r1-EA-sources-nepa-project-sow-package`

Sequence 2 is implemented for the proposed-action-to-resource-SOW lane. This sequence intentionally
stays upstream of South Plateau applicability closure and does not read or write South Plateau
review outputs. The new public command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
```

Implemented surfaces:

- `config/project_sow_resource_scopes_v1.json`
- `config/fixtures/project_sow/east_crazies_land_exchange_intake.json`
- `src/usfs_r1_ea_sources/project_sow_package.py`
- `src/usfs_r1_ea_sources/cli_project_planning.py`
- `tests/test_project_sow_package.py`
- `tests/test_cli.py`
- `docs/OUTPUT_SCHEMAS.md`
- `docs/ARCHITECTURE.md`
- `docs/architecture_contract.toml`

The command writes `project_sow_package.json`, `project_sow_package.md`, and
`project_sow_package_manifest.json` under
`source_library/projects/<project_id>/requirements_package/`. A local CLI smoke run to `/tmp`
selected ten East Crazies land-exchange resource scopes: NEPA project management, lands/realty,
Forest Plan consistency, wildlife/species/botany, cultural/tribal, hydrology/wetlands/water
quality, roads/access/recreation/designated areas, vegetation/soils/air-quality/climate/carbon,
minerals/energy/hazardous materials, and public involvement/coordination.

Sequence 2 added an East Crazies calibration comparison. The intake now records structured
`proposed_action_elements`, `resource_analysis_expectations`, and observed specialist/supporting
reports from the completed East Crazies package. The generated JSON/Markdown now includes a
`resource_analysis_matrix` that compares proposed-action-derived resource areas to selected SOW
scopes and the observed report set: mineral potential, aquatics, at-risk plants/botany, carbon,
cultural resources, recreation special areas, recreation special uses, roads/trails/access, tribal
relations, wetlands, wildlife, water rights, and the plan-consistency table. Validation fails if an
observed report resource area is not derived from the proposed action or lacks selected SOW scope
coverage.

Next sequence: add richer intake evidence references and optional PDF rendering only after this
resource-analysis coverage slice is reviewed. Do not convert SOW scopes into applicability or
compliance findings in this lane.

## Current Applicability/Expansion Handoff

`docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` Sequence 4 is complete. The South Plateau
Area Landscape Treatment Project package now exists locally as
`region1-expansion-south-plateau-landscape-treatment`: `26` official PDFs were imported from the
official project Box folder into
`source_library/reviews/_intake/region1-expansion-south-plateau-landscape-treatment`, with an
ignored `box_import_manifest.json` recording Box IDs, source URLs, byte sizes, and hashes. The
package cache was rebuilt with `.venv-docling`; `26/26` files extracted, `0` failed, and `3,671`
chunks were written under
`source_library/reviews/region1-expansion-south-plateau-landscape-treatment/package/`.

The South Plateau applicability-first path ran through validation. Authority universe and package
context validation passed, retrieval trace validation passed, and determination produced `55`
applicable authorities, `331` non-applicable authorities, and `6` authorities requiring
adjudication. `applicability-validate` failed as designed with `generated_rule_pack_ready=false`,
`reviewer_ready=false`, and `failure_category_counts={"unresolved_authority": 12}`. The generated
adjudication template/worklist are:

- `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/applicability_adjudication_template.json`
- `source_library/reviews/region1-expansion-south-plateau-landscape-treatment/applicability/applicability_adjudication_worklist.md`

The six pending authority-family conflicts are
`cultural_resource_protection_and_state_shpo_sources`,
`invasive_pesticide_soils_farmland_drinking_water`,
`roads_access_special_use_action_authorities`,
`species_supporting_sources_and_overlays`,
`vegetation_wildfire_forest_health_authorities`, and
`wilderness_wsr_trails_designated_areas`. The promotion-suite slot now carries typed
`adjudication_needed`, remains `ready=false`, and has not run generated rule-pack, compliance
review, or review-scoped phase eval.

Promotion suite was rerun after the Sequence 4 manifest/docs update. Non-strict reports
`current_promotion_ready=true`, `promotion_ready=true`, `expansion_ready=false`,
`expansion_artifacts_ready=true`, `failure_category_counts={}`,
`expansion_failure_category_counts={"adjudication_needed": 1}`,
`open_expansion_artifact_count=0`, and `open_expansion_slot_count=1`. Strict expansion was written
to the separate strict results directory and failed as expected with `promotion_ready=false` and
`failure_category_counts={"adjudication_needed": 1}`; the normal suite was rerun last so the default
promotion-suite output remains the current-promotion signal.

The ECID preliminary-EA expansion slot remains ready. Its Forest Plan component adjudication eval
for the current `158`-row queue resolves all `158` rows as true EA package-evidence omissions,
`pending_adjudication_count=0`, and `system_miss_count=0`; those adjudications keep the missing
package evidence visible as gaps and do not mark components supported or create legal conclusions.
ECID compliance review reports `reviewer_ready=true`, ECID review-scoped phase eval passes `16/16`,
and the required ECID expansion artifacts pass.

Next sequence: Sequence 5, South Plateau applicability adjudication closure. Complete the six-item
applicability adjudication template, run `applicability-adjudication-eval`, apply it with
`applicability-adjudication-apply`, and rerun `applicability-validate`. Only after validation passes
should generated rule-pack validation, compliance review, and review-scoped phase eval run.

## Current Architecture Hardening State

The agentic coding architecture sequence has implemented the architecture map, contract, first
fitness gate, rule-pack ownership split, CLI lane split, hotspot report, and ADR set through
Milestone 6. The operative architecture references are:

- `docs/ARCHITECTURE.md`
- `docs/architecture_contract.toml`
- `docs/HOTSPOT_REPORT_2026_05_04.md`
- `docs/adr/0001-architecture-fitness-gates.md`
- `docs/adr/0002-applicability-before-compliance.md`
- `docs/adr/0003-rule-pack-ownership.md`
- `docs/adr/0004-untrusted-source-content.md`
- `docs/adr/0005-architecture-gates-in-milestone-closeout.md`

### Compliance Review Hotspot Reduction

Sequence 6 is implemented for the compliance-review hotspot split. The new
`src/usfs_r1_ea_sources/compliance_review_eval.py` module owns the deterministic
compliance-review eval harness only: eval case loading and validation, fixture package
materialization, eval review invocation, case scoring, mismatch metrics, failure taxonomy, and
reproduction metadata. Sequence 5 kept
`src/usfs_r1_ea_sources/compliance_findings.py` as the owner for compliance finding construction
only: authority-family inventory indexing, authority-family ID resolution for generated/base rules,
source-claim evidence compaction, citation-label extraction, and claim-type assignment. Sequence 4
kept
`src/usfs_r1_ea_sources/compliance_finding_graph.py` as the owner for finding-graph artifact assembly
only: compliance review/rule/finding nodes, source-library evidence nodes, source-claim nodes,
package-evidence and package-gap nodes, graph edges, and the Forest Plan review/component-eval graph
projection. Sequence 3 kept
`src/usfs_r1_ea_sources/compliance_authority_integration.py` as the owner for authority-integration
artifact assembly only: authority-family provenance, non-applicable authority appendix JSON and
Markdown, authority reviewer-resolution report, deterministic litigation-risk summary, and the
private row/risk helpers needed to assemble those artifacts. Sequence 2 kept
`src/usfs_r1_ea_sources/compliance_validation.py` as the owner for compliance validation and
review-summary assembly helpers, and Sequence 1 kept
`src/usfs_r1_ea_sources/compliance_inputs.py` as the owner for compliance-review input and
identity/gate-context helpers.

The current post-split line-count baseline is `compliance_review.py` `398`,
`compliance_review_eval.py` `954`, `compliance_findings.py` `217`,
`compliance_finding_graph.py` `340`, `compliance_authority_integration.py` `493`,
`compliance_validation.py` `762`, `compliance_inputs.py` `561`, and
`compliance_outputs.py` `1,019`; the deferred hotspot baselines remain
`nepa_knowledge_graph_export.py` `3,391`, `forest_plan_components.py` `3,302`,
`ea_consistency_decision_support.py` `3,090`, and `viewer/nepa-3d/app.js` `2,202`.

Sequence 6 does not intentionally change finding selection, compliance status decisions, generated
rule-pack semantics, Forest Plan component evaluation, matrix/PDF output, finding graph output,
eval scoring semantics, CLI flags, or generated artifact schemas. No Sequence 7 split is selected
yet; rerank remaining hotspots before continuing beyond this eval-harness boundary.

Sequence 6 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 5 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 4 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 3 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 2 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 1 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`.

Sequence 0 verification passed: `tests/test_compliance_review.py` `55 passed`,
`tests/test_cli.py tests/test_architecture_contract.py` `11 passed`, `ruff check src tests`,
`compileall src`, and `git diff --check`. Existing untracked root-level East Crazies manual draft
exports and `docs/capabilities/Draft_nepa_3d_capabilities_brief.pdf` remain non-canonical and were
left untouched.

## Current Applicability-First State

The current active implementation lane is the post-V1 applicability-first review architecture in
`docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`. The V1 EA gate remains promoted for the Custer
Gallatin East Crazy proving package, but new work has moved into a pre-review applicability
pipeline that separates authority applicability from compliance findings.

Current completed applicability milestones:

- Milestone 1 schema plan: artifact contracts for package fact graph, retrieval trace, graph trace,
  search coverage certificates, applicability decisions, provenance, validation/adjudication, and
  generated rule pack are documented in `docs/OUTPUT_SCHEMAS.md`.
- Milestone 2 authority universe: `applicability-authority-universe` writes
  `authority_universe_snapshot.json` with rule-template and Forest Plan component candidates,
  source evidence requirements, package/source filters, retrieval contracts, graph-expansion
  contracts, dependency/exception/supersession fields, and search coverage requirements.
- Milestone 3 package context: `applicability-context-build` reads the existing EA package cache and
  writes `package_fact_graph.json`, `package_applicability_context.json`, and
  `package_fact_graph_validation.json` with typed, span-bound package facts and uncertainty records.
- Milestone 4 retrieval/graph traces: `applicability-retrieve` writes
  `applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`, and
  `applicability_retrieval_graph_diagnostics.json` with replayable per-candidate retrieval rows,
  RRF fused result rows, bounded graph paths, and diagnostics.
- Milestone 5 deterministic decisions: `applicability-determine` writes
  `applicability_decisions.jsonl`, `applicable_authorities.json`,
  `non_applicable_authorities.json`, `search_coverage_certificates.json`,
  `applicability_provenance.json`, and `applicability_report.md` without producing compliance
  findings or a generated rule pack.
- Milestone 6 validation/adjudication: `applicability-validate` writes
  `applicability_validation.json` and fails closed on missing, duplicated, stale, unsupported, or
  unresolved decisions. `applicability-adjudication-template`,
  `applicability-adjudication-eval`, and `applicability-adjudication-apply` provide replayable
  machine-readable adjudication; apply rewrites the decision ledger and applicable/non-applicable
  partitions with `human_adjudication` bases and updates provenance. The gap-close pass hardened
  validation around package fact-graph validation status, contradiction/adjudication handling,
  adjudication eval replayability, partition/coverage freshness, and provenance entity hashes.
- Milestone 7 generated rule pack: `applicability-generate-rule-pack` writes
  `generated_rule_pack.json` and `generated_rule_pack_validation.json` only from a passing and
  current applicability validation. Generated packs contain validated applicable authorities only
  and carry explicit base/generated rule IDs, decision, retrieval, graph, source-record,
  source-claim, package-section, Forest Plan, per-rule artifact hashes, freshness, and provenance
  metadata. `--validate-only` requires a previously recorded generated-pack hash and detects manual
  edits, stale applicability validation, and upstream artifact drift.
- Milestone 8 compliance-review gate: reviewer-ready `compliance-review` now requires a generated
  applicability rule pack plus passing applicability/generated-pack validation, matching package
  manifest, package-chunk, source-set, and provenance hashes, a valid
  `non_applicable_authorities.json`, and search coverage for non-applicable authorities. Generated
  validation must explicitly record `generated_rule_pack_ready=true`. The base rule pack can still
  be run with `--allow-base-rule-pack-review`, but that diagnostic output is not reviewer-ready and
  cannot make compliance-gold eval promotion-ready.
- Milestone 9 applicability eval gates: `applicability-eval` runs deterministic seed packages
  through the full applicability sequence and checks expected statuses, package facts,
  retrieval/graph traces, source-record/document-role/package-section alignment, non-applicable
  coverage, required artifact presence, and generated-rule-pack identity/hash alignment.
  `applicability-gold-eval` requires adjudicated positive, mixed, and negative profiles before
  promotion. `phase-eval --review-id/--review-dir` now includes authority-universe, package-fact
  graph, applicability retrieval trace, applicability graph trace, applicability determination,
  applicability validation, and generated-rule-pack phases before compliance review. The
  gap-closure pass added regression coverage for missing non-applicable artifacts, graph trace gaps,
  generated-pack hash edits, source/document-role/package-section mismatches, and stale
  file-backed applicability validation hashes.

Latest applicability and evidence-arbitration commits:

- `8018648` - Harden applicability authority universe
- `f5a3db1` - Close authority universe contract gaps
- `0f4a851` - Add applicability package fact graph
- `4656283` - Close package fact graph gaps
- `0f30761` - Add applicability retrieval traces
- `e9e3abe` - Close applicability retrieval graph gaps
- `08b1aae` - Add deterministic applicability decisions
- `aa0c1da` - Close applicability decision gaps
- `6bed025` - Add applicability validation adjudication gate
- `a60c382` - Close applicability validation gate gaps
- `99ae407` - Add applicability generated rule pack
- `53061f6` - Close generated rule pack gate gaps
- `75672da` - Gate compliance review on generated rule pack
- `69e83bb` - Implement authority applicability eval coverage
- `0d48d4b` - Close authority applicability milestone gaps
- `992a079` - Implement authority report integration
- `9a9d256` - Implement evidence arbitration diagnostics
- `a3c967a` - Implement evidence strength model
- `8f8b15d` - Close evidence arbitration diagnostic gaps
- `cf325ba` - Implement trigger arbitration predicate
- `34fca93` - Implement ECID arbitration replay
- `f304e2e` - Add arbitration eval reporting coverage

Important current behavior:

- Applicability artifacts are produced before compliance review and do not contain `pass`, `gap`, or
  `uncertain` compliance findings.
- Trigger arbitration now distinguishes decisive strong package evidence from weak auxiliary
  evidence. All-weak trigger evidence and unresolved positive/negative conflicts are still recorded
  as `needs_adjudication`.
- Evidence-arbitration Milestones 1 and 2 are implemented as behavior-preserving diagnostics:
  decisions carry `arbitration_summary`, evidence spans carry structured `evidence_strength`, and
  reports show weak/auxiliary/conflicting trigger-group diagnostics without changing final
  applicability status outcomes. The gap-close pass added structured weak-signal reason notes,
  broader no-action/no-change background classification, negative-phrase preservation, and package
  graph assertions for fact/context/uncertainty evidence-strength propagation.
- Evidence-arbitration Milestone 3 is implemented as active trigger arbitration. Strong,
  rule-contract-sufficient positive trigger groups can carry `applicable` status with weak
  auxiliary evidence retained in notes and diagnostics. All-weak positive evidence and
  positive-plus-negative conflicts remain `needs_adjudication`.
- Not-applicable decisions cite search coverage certificates.
- Validation now fails if a final contradictory decision lacks human adjudication, if a
  human-adjudicated decision cannot be replayed from a passing adjudication eval, if
  `package_fact_graph_validation.json` is stale or failed, or if partition/coverage/provenance
  hashes drift from current applicability artifacts.
- Milestone 5 gap closure added raw package-chunk checks for explicit negative evidence,
  source-index hash requirements for sufficient coverage, retained source-library evidence spans on
  non-applicable decisions, local-evidence trigger-group matching, and package manifest/chunk
  provenance entities.
- `compliance-review` no longer runs reviewer-ready reviews directly against the base rule pack.
  Generated-rule-pack review evaluates generated applicable rules only; non-applicable authorities
  stay in `non_applicable_authorities.json`, which the compliance matrix links as the source of
  truth.
- `compliance-review-eval` may still score deterministic compliance fixtures with the base rule
  pack, but those runs are diagnostic and default to non-reviewer-ready validation expectations.
  `compliance-gold-eval` now emits `promotion_ready=true` only for reviewer-ready generated
  applicability rule packs. Applicability-quality evals now exist so generated review success is no
  longer the only proxy for applicability correctness.

Latest verification for the current applicability/evidence-arbitration lane:

```bash
PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_eval.py tests/test_promotion_suite.py tests/test_applicability_decisions.py
PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json --eval-file config/applicability_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval --output-dir source_library --source-set-id source-set-ba8d0feae79501b8 --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json --gold-file config/applicability_gold_eval_v0.json
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
python -m json.tool config/applicability_eval_seed.json /tmp/applicability_eval_seed.validated.json
python -m json.tool config/applicability_gold_eval_v0.json /tmp/applicability_gold_eval_v0.validated.json
python -m json.tool config/promotion_suite_v1.json /tmp/promotion_suite_v1.validated.json
git diff --check
```

Verified results from the latest Milestone 5 arbitration coverage pass:

- Focused applicability/promotion regression suite: `42 passed`
- Architecture contract: `5 passed`
- `applicability-eval`: passed `9/9` seed cases; arbitration status/effect match rates were `1.0`
- `applicability-gold-eval`: passed `5/5` adjudicated cases and emitted `promotion_ready=true`
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `16/16` phases with
  `applicability_arbitration_summary` emitted
- `promotion-suite`: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`; expansion blockers remain `adjudication_needed` and
  `package_fixture_missing`
- The current V1 applicability artifact family remains reviewer-ready with `373` candidates, `33`
  applicable authorities, `340` non-applicable authorities, no unresolved/adjudication decisions,
  and `generated_rule_pack_ready=true`.
- Ruff, compileall, JSON validation, and `git diff --check`: passed

Latest evidence-arbitration Milestone 3 closeout verification:

- `tests/test_applicability_decisions.py`: `24 passed`
- `tests/test_applicability_eval.py`: `11 passed`
- `tests/test_architecture_contract.py`: `5 passed`
- `tests/test_package_fact_graph.py`: `4 passed`
- `ruff check src tests`: passed
- `python -m compileall src`: passed
- `git diff --check`: passed

Latest evidence-arbitration Milestone 4 closeout verification:

- `applicability-determine`: replayed `392` ECID candidate authorities to `43` applicable, `346`
  non-applicable, and `3` `needs_adjudication`.
- `applicability-validate`: expected reviewer-readiness failure; failure categories were limited to
  `unresolved_authority` for the three positive/negative authority conflicts.
- `applicability-adjudication-template`: emitted the three-item worklist for cultural-resource/SHPO,
  minerals/energy, and species-supporting authorities.
- `promotion-suite`: kept current promotion ready and expansion not ready; expansion blockers are
  `adjudication_needed` and `package_fixture_missing`.
- `tests/test_applicability_decisions.py`: `25 passed`
- `tests/test_promotion_suite.py`: `6 passed`
- `tests/test_applicability_eval.py`: `11 passed`
- `tests/test_architecture_contract.py`: `5 passed`
- `ruff check src tests`, `python -m compileall src`, JSON validation, and `git diff --check`:
  passed.

Latest evidence-arbitration Milestone 5 closeout verification:

- `applicability-eval`: passed `9/9` seed cases with arbitration status/effect match rates of
  `1.0`; aggregate arbitration counts include `1` applicable-with-weak-auxiliary, `2` weak-only
  needs-adjudication, `1` insufficient-strong-trigger needs-adjudication, and `1`
  positive/negative-conflict needs-adjudication.
- `applicability-gold-eval`: passed `5/5` cases with `promotion_ready=true` and a passing
  `gold_eval_cases_have_arbitration_expectations` check.
- `phase-eval --review-id v1-cg-ecid-compliance-review`: passed `16/16` phases and emitted
  `applicability_arbitration_summary`.
- `promotion-suite`: kept current promotion ready and expansion not ready; expansion blockers remain
  `adjudication_needed` and `package_fixture_missing`.
- `tests/test_applicability_decisions.py`: `25 passed`
- `tests/test_applicability_eval.py`: `11 passed`
- `tests/test_promotion_suite.py`: `6 passed`
- `tests/test_architecture_contract.py`: `5 passed`
- `ruff check src tests`, `python -m compileall src`, JSON validation, and `git diff --check`:
  passed.

Latest post-V1 real-package expansion Sequence 0 baseline lock:

- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` Sequence 0 is complete. This pass did
  not adjudicate ECID, add a third package fixture, or change the promotion manifest.
- Non-strict promotion-suite run wrote
  `source_library/reviews/promotion_suite/sequence0-baseline-nonstrict/promotion_suite_results.json`
  and reported `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  and `open_expansion_slot_count=2`.
- Strict promotion-suite run wrote
  `source_library/reviews/promotion_suite/sequence0-baseline-strict/promotion_suite_results.json`
  and failed as expected with `current_promotion_ready=true`, `promotion_ready=false`,
  `expansion_ready=false`,
  `failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  `expansion_failure_category_counts={"adjudication_needed": 1, "package_fixture_missing": 1}`,
  and `open_expansion_slot_count=2`.
- At Sequence 0, the ECID adjudication template/worklist at
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/` had three pending
  `needs_adjudication` items: `cultural_resource_protection_and_state_shpo_sources`
  (`decision_id=6f349222ecfa557b7d163d68`), `minerals_energy_authorities`
  (`decision_id=add0df8c2b513d6068b4edcc`), and
  `species_supporting_sources_and_overlays` (`decision_id=58df28f23d0b2222f32eb687`).

Latest post-V1 real-package expansion Sequence 1 adjudication closure:

- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` Sequence 1 is complete. The ECID
  adjudication template was completed for the three pending authority-family conflicts and left in
  ignored `source_library/` evidence artifacts.
- The three adjudicated families are now `human_applicable`:
  `cultural_resource_protection_and_state_shpo_sources`,
  `minerals_energy_authorities`, and `species_supporting_sources_and_overlays`.
- `applicability-adjudication-eval` passed with `3` resolved adjudications, `0` pending
  adjudications, and `failure_category_counts={}`.
- `applicability-adjudication-apply` passed with `applied_item_count=3`,
  `remaining_unresolved_authority_count=0`, and applied decision-ledger hash
  `207f2c17c8e13708dc46b6b50581183f5ea6af523cc3aeb76d585557fcfb77cd`.
- `applicability-validate` passed with `46` applicable authorities, `346` non-applicable
  authorities, `0` unresolved, `0` `needs_adjudication`, `generated_rule_pack_ready=true`,
  `reviewer_ready=true`, and `failure_category_counts={}`.
- Sequence 1 did not generate the ECID rule pack, run compliance review, run phase eval, update the
  promotion manifest, or add the missing third real-package fixture. Sequence 2 has since completed
  the artifact-generation and promotion-manifest pass described below.

Latest post-V1 real-package expansion Sequence 2B/3 status:

- `applicability-generate-rule-pack` passed for
  `region1-expansion-ecid-preliminary-ea`, producing a generated ECID rule pack with `46` rules and
  `generated_rule_pack_ready=true`.
- `compliance-review` against the generated ECID rule pack wrote
  `compliance_review.json`, `compliance_validation.json`, `compliance_matrix.json/.md/.pdf`,
  authority-family provenance, non-applicable authority appendix, authority reviewer-resolution,
  litigation-risk, rule-claim, and finding-graph artifacts. Sequence 2A closed the source-claim
  blocker: `rule_claim_gap_count=0`, `rule_claim_link_count=211`, and
  `rule_claim_rules_without_links=[]`. Sequence 2B closed the Forest Plan component blocker:
  compliance review now reports `reviewer_ready=true` and validation passes.
- ECID Forest Plan component status: `29` applicable standards, `7` applied standards, `158`
  reviewer-resolution rows, all queued as `missing_package_evidence`; Sequence 2B adjudication
  eval resolves all `158` as true EA package-evidence omissions with `0` system misses.
- `phase-eval --review-id region1-expansion-ecid-preliminary-ea` now writes a review-scoped copy at
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/phase_eval_results.json`; the ECID
  Sequence 2B run passes with `16/16` phases and `reviewer_ready=true`.
- The shared source-set phase-eval artifact was restored by rerunning
  `phase-eval --review-id v1-cg-ecid-compliance-review`, which passed `17/17` phases for the
  promoted V1 review.
- `forest-plan-component-adjudication-template` generated a `158`-item ECID worklist at
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/forest_plan_component_adjudication_template.json`
  and `.md`.
- `config/promotion_suite_v1.json` now includes ECID `required_for_expansion` artifact checks and
  treats expansion readiness as both slot readiness and required expansion artifact readiness. The
  ECID slot is now `ready=true`; it is no longer blocked by `forest_plan_reviewer_not_ready`,
  `adjudication_needed`, or `missing_source`.
- Non-strict promotion suite after Sequence 4 reports `current_promotion_ready=true`,
  `promotion_ready=true`, `expansion_ready=false`, `expansion_artifacts_ready=true`,
  `failure_category_counts={}`, `expansion_failure_category_counts={"adjudication_needed": 1}`,
  `open_expansion_artifact_count=0`, and `open_expansion_slot_count=1`.

Next implementation target:

The current active lane is `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` Sequence 5:
complete the six South Plateau applicability adjudications, evaluate/apply them, and rerun
applicability validation. The older lane notes below are retained for continuity, but they are not
the current next pass unless the user redirects.

Sequence 2B alignment/gap close note: strict and non-strict promotion-suite evidence were kept
separate, and non-strict was rerun last so the default suite output remains the current-promotion
signal. The ECID implementation reused the existing package/cache, turned each of the `158` rows
into an actionable QA/QC disposition, preserved compact component/source refs on every resolved
item, and preserved the missing evidence as visible gaps rather than converting the review into a
legal conclusion.

- `docs/EA_CONSISTENCY_DECISION_SUPPORT_MILESTONE_PLAN.md`: close the gap between reviewer-ready
  East Crazies evidence artifacts and a single Forest Supervisor-facing EA consistency
  decision-support document. This lane must generate a report from audited review artifacts,
  not from root-level manual draft prose, and must preserve the applicable/non-applicable authority
  boundary, Forest Plan component coverage, applicable-standard coverage, residual risk register,
  and implementation confirmation checklist. Sequence 0 preflight is complete in
  `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PLAN.md` and the pass artifacts below. Sequences 1
  through 5 are complete; the EA consistency decision-support milestone has no remaining planned
  sequence. Future work should be a new milestone or a targeted copy-review pass, not a continuation
  of this implementation lane.
  - Sequence 0 pass 1 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_1_WORKSPACE_BOUNDARY.md`: tracked
    worktree status was clean at pass start, root-level `East_Crazies_*` exports are quarantined as
    non-canonical manual draft comparison material, and `source_library/` remains ignored. The next
    preflight pass is artifact freshness and hash baseline.
  - Sequence 0 pass 2 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_2_ARTIFACT_FRESHNESS.md`: all required
    review artifacts exist and parse, validation-owned artifact hashes match current files, the
    review/source-set/package boundary agrees, and the Plan Consistency Table hash baseline records
    both raw-file and normalized-text hash shapes. The next preflight pass is current gate replay.
  - Sequence 0 pass 3 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_3_CURRENT_GATE_REPLAY.md`: `phase-eval`
    passed `16/16` with `reviewer_ready=true`, `promotion-suite` reported
    `current_promotion_ready=true` and `promotion_ready=true`, and broader expansion blockers
    remain separated from the current East Crazies promotion gate. The next preflight pass is Forest
    Plan consistency baseline.
  - Sequence 0 pass 4 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_4_FOREST_PLAN_CONSISTENCY_BASELINE.md`:
    `EA-PACKAGE-042` is present once as extracted Plan Consistency Table package evidence,
    generated Forest Plan artifacts remain canonical, component findings report `329` findings with
    `79` supported/applicable and `250` not applicable, applicable-standard coverage reports `58`
    standards with `12/12` applied, Custer Gallatin context remains reviewer-ready, and manual
    root-level East Crazies prose remains quarantined. The next preflight pass is Authority Universe
    Boundary.
  - Sequence 0 pass 5 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_5_AUTHORITY_UNIVERSE_BOUNDARY.md`:
    applicable and non-applicable authority partitions are disjoint and cover all `373` candidates,
    with `33` applicable authorities, `340` non-applicable authorities, `340` search coverage
    certificates, exact non-applicable appendix alignment, generated-rule-pack validation proving
    generated rules derive only from applicable authorities, and the compliance matrix linking to
    non-applicable artifacts instead of double-counting them as findings. The next preflight pass is
    Residual Risk And Implementation Confirmation Source Mapping.
  - Sequence 0 pass 6 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_6_RESIDUAL_RISK_IMPLEMENTATION_SOURCE_MAPPING.md`:
    residual-risk rows are mapped to `litigation_risk_summary.json`,
    `authority_reviewer_resolution_report.json`, compliance limitation fields, Forest Plan
    applicable-standard limitations, and Forest Plan reviewer-resolution artifacts; the current
    risk state has `340` deterministic informational non-applicable-boundary flags, `0` legal
    conclusion flags, `0` open authority-resolution items, `0` open Forest Plan reviewer-resolution
    items, no compliance limitations, and no applicable-standard failure reasons. Every required
    implementation-confirmation checklist item has current generated evidence selectors plus a
    planned tracked configuration owner in `config/ea_consistency_decision_support_v1.json` for
    Sequence 1. The next preflight pass is CLI, Module, And Renderer Ownership.
  - Sequence 0 pass 7 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_7_CLI_MODULE_RENDERER_OWNERSHIP.md`:
    the full milestone implementation surface is now fixed as the `ea-consistency-document` CLI
    command, a new `cli_decision_support.py` command lane, canonical module
    `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`, a new architecture-contract
    `decision_support` layer and command group when code is introduced, generated artifacts under
    `source_library/reviews/<review_id>/decision_support/`, schema documentation in
    `docs/OUTPUT_SCHEMAS.md`, config ownership in `config/ea_consistency_decision_support_v1.json`,
    and focused tests in `tests/test_ea_consistency_decision_support.py`, `tests/test_cli.py`, and
    `tests/test_architecture_contract.py`. The renderer path should follow the existing
    compliance-output JSON-to-Markdown/PDF pattern without importing private helpers or adding
    system PDF dependencies. The next preflight pass is Fixture And Regression Contract.
  - Sequence 0 pass 8 is complete in
    `docs/EA_CONSISTENCY_DECISION_SUPPORT_PREFLIGHT_PASS_8_FIXTURE_REGRESSION_CONTRACT.md`:
    fixture/regression expectations are fixed for required report sections, current count fields,
    required input hash fields, representative applicable authority row (`eo_11990_wetlands`),
    representative non-applicable authority row (`directives_notice_comment_36cfr_216`) with search
    coverage, representative Forest Plan row (`FW-STD-RMZ-01`), all `12` applicable standards, and
    fail-closed categories for missing, stale, or mismatched inputs, count drift, missing
    non-applicable summaries, unresolved implementation selectors, residual-risk legal conclusions,
    manual-draft dependency, and invalid or missing PDF output. Sequence 0 preflight is complete
    with `go`; the next boundary is Sequence 1 Report Contract And Fixtures.
  - Sequence 1 is complete: `docs/OUTPUT_SCHEMAS.md` now documents the
    `ea-consistency-decision-support-report-v1` artifact family; tracked config
    `config/ea_consistency_decision_support_v1.json` owns section order, grouping, caveat wording,
    implementation-confirmation selectors, residual-risk rules, and report-quality eval
    expectations; `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json`
    locks the current East Crazies sections/counts/hashes/sample rows/applicable standards/failure
    categories; `tests/fixtures/decision_support/minimal_decision_support_report.json` proves the
    synthetic schema boundary; and `tests/test_ea_consistency_decision_support.py` validates
    schema/config/fixture contracts including row-level `trace_ids`, `source_selectors`,
    false-positive synthesis claims, and false-negative synthesis omissions.
  - Sequence 2 is complete: `src/usfs_r1_ea_sources/ea_consistency_decision_support.py` implements
    the deterministic report generator, `src/usfs_r1_ea_sources/cli_decision_support.py` registers
    `ea-consistency-document`, and `docs/architecture_contract.toml` now owns the
    `decision_support` layer, command group, and generated artifact family. The generator validates
    required audited inputs, compares the Sequence 1 hash/count contract, fails closed on missing,
    stale, hash-mismatched, non-reviewer-ready, unresolved-selector, missing-evidence, or
    legal-conclusion conditions, and writes canonical JSON plus Markdown, PDF, and manifest outputs
    under `source_library/reviews/<review_id>/decision_support/`. A local run for
    `v1-cg-ecid-compliance-review` passed and wrote the ignored generated report family with `33`
    applicable authority findings, `340` non-applicable authorities, `329` Forest Plan component
    rows, `12/12` applicable standards applied, `0` open authority/Forest Plan resolution items, and
    a valid `%PDF-` PDF header. Sequence 3 closed out that first real report output; Sequence 4 now
    owns gate integration.
  - Sequence 3 is complete: the 2026-05-06 local closeout run generated the ignored East Crazies
    decision-support family under
    `source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`:
    `ea_consistency_decision_support.json`, `.md`, `.pdf`, and `_manifest.json`. The generated
    report validation passed with `33` applicable authority findings rendered as `pass`, `340`
    non-applicable authorities summarized with search coverage, `329` Forest Plan component rows,
    all `12/12` applicable Forest Plan standards carrying package and plan evidence, `9`
    implementation-confirmation rows with evidence, `3` residual-risk notes, `0` legal-conclusion
    risk flags, and a valid `%PDF-` PDF header. No `source_library/` outputs were staged.
  - Sequence 4 is complete: `ea-consistency-document --validate-only` validates the existing
    generated report family without rewriting it; `phase-eval --review-id
    v1-cg-ecid-compliance-review` now includes the `decision_support_report` phase and passed
    `17/17` phases with `reviewer_ready=true`; `promotion-suite` requires the decision-support
    report JSON, manifest, and PDF for current promotion and reports `current_promotion_ready=true`,
    `promotion_ready=true`, and `expansion_ready=false`. The validator fails closed on stale input
    hashes, missing sections, missing non-applicable summaries, missing applicable standards,
    invalid PDF output, manual-draft dependency, unresolved implementation confirmations, and
    residual-risk legal conclusions.
  - Sequence 5 is complete: the Markdown/PDF renderer now front-loads a "How To Use This Document"
    note, bottom-line reviewer-ready status, authority categories/status counts, Forest Plan basis,
    applicable-standard coverage, non-applicable authority boundary, implementation confirmations,
    residual risks, validation status, and concise table summaries before the long authority and
    Forest Plan evidence sections. Implementation-confirmation rows show constrained
    decision-support wording plus evidence selectors; residual-risk rows preserve source artifact
    and selector pointers; and the caveat states the document supports review but does not replace
    responsible official, line officer, counsel, or specialist judgment. The generated
    `source_library/` report family remains ignored and should not be staged unless policy changes.
  - Post-sequence gap close is complete: validation now checks the Markdown/PDF supervisor rendering
    contract directly. Missing front matter, review snapshot, table summaries, key counts, required
    sections, source pointers, or Markdown section ordering fails as
    `false_negative_synthesis_omission` with `decision_support_markdown.*` or
    `decision_support_pdf.*` source selectors. This closes the gap against the
    thought-leader review's report-quality eval guidance without adding a new sequence.
- `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md` Milestone 10: the ECID three-item
  applicability adjudication worklist, generated-rule-pack/artifact-check pass, source-claim gap
  closure, Forest Plan component adjudication replay, and third package fixture selection are
  complete. The next implementation slice is the selected South Plateau applicability-first run.
- `docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md`: focused closure plan for resolving
  `expansion_ready=false` by running the selected South Plateau package through the
  applicability-first sequence and then strict expansion promotion.
- `docs/NEPA_3D_KNOWLEDGE_GRAPH_MILESTONE_PLAN.md`: build a source-set and review-specific
  knowledge graph export plus local 3D viewer for all USDA/Forest Service Region 1 EA authority
  families, applicability decisions, evidence paths, supersession/currentness states, and readiness
  blockers. This lane must start as a visualization/export layer over existing audited artifacts,
  not as a separate legal knowledge base.
- NEPA 3D Milestone 2A is implemented. `config/source_partition_contract_nepa_3d_v1.json` and
  `source_partitions.py` define `active_review_corpus`,
  `currentness_supersession_archive`, and `candidate_blocked_source`; future `catalog-build`
  outputs carry `source_partition` and `source_partition_basis`; and `authority-currentness` now
  reports catalog partitions, per-family graph roles, and fail-closed checks for non-current active
  sources, reserved/superseded active authority, superseded-family graph relationships, and
  collapsed FSH 1909.15 handbook records. The gap-closure pass also validates the contract's
  required partitions, active/non-active eligibility boundary, non-active graph relationship limits,
  reserved `36 CFR part 220` archive boundary, and scoped workbook/source-delta plan. The live
  currentness gate passed with `189` active review-corpus records and `1` candidate/blocked source.
- NEPA 3D Milestone 1 is implemented. `config/nepa_3d_graph_contract_v1.json`,
  `nepa_3d_graph_contract.py`, `docs/OUTPUT_SCHEMAS.md`, and
  `tests/fixtures/nepa_3d_graph/` now define and validate the source-set/review graph export schema,
  node and edge types, display states, review-readiness states, required per-node provenance fields,
  edge endpoint compatibility, required lens metadata, currentness metadata, validation shape, and
  readiness blockers before exporter implementation.
- NEPA 3D Milestone 3 is implemented. `nepa_knowledge_graph_export.py` and the
  `nepa-knowledge-graph-export` CLI command build the source-set graph from catalog graph seeds,
  authority inventory/currentness, evidence graph inputs, source claims, rule-claim links, the base
  rule pack, authority-family templates, forest-plan profiles, and forest-plan component inventory.
  The refreshed `source-set-ba8d0feae79501b8` export passed `57` validation checks with `1,401`
  nodes, `2,552` edges, all `35` authority families, all `190` catalog source records, all `44` base
  rules, all `19` authority-family templates, `191` rule-claim links, and `329` forest-plan
  components.
- NEPA 3D Milestone 4 is implemented. `nepa-knowledge-graph-export --review-id` writes the
  review-specific graph under `source_library/reviews/<review_id>/knowledge_graph/` from existing
  applicability-first and compliance artifacts. The refreshed `v1-cg-ecid-compliance-review`
  overlay passed `75` validation checks with `1,916` nodes, `3,442` edges, `373` candidate
  authorities/decisions, `33` generated rules and compliance findings, and `340` non-applicable
  authorities with search coverage. The gap-close checks now also require hashed review artifact
  inputs and resolving search-coverage, retrieval-trace, and graph-trace references.
- NEPA 3D Milestone 5 is implemented. `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  tracks `10` Region 1 forest/grassland profiles, `3` field-directive requirements, and `5`
  overlay requirement groups. `config/forest_plan_profiles.json` now contains the first added
  Beaverhead-Deerlodge profile contract with catalog-confirmed planning page/LMP source rows,
  positive and hard-negative applicability fixture contracts, and a component-inventory blocker
  before graph promotion. The source-set graph passed `61` validation checks with `1,410` nodes and
  `2,564` edges, `1` graph-ready profile, `9` broader Region 1 profiles blocked from completeness
  claims, and graph-visible field-directive/overlay requirement nodes linked to catalog sources.
- NEPA 3D Milestone 6 is implemented. `viewer/nepa-3d/` is a checked-in static viewer over the
  normalized graph export. It uses `viewer/nepa-3d/manifest.json` to load the current source-set
  graph and selectable V1 review overlay graph, uses Three.js plus `3d-force-graph`, defaults to a
  bounded readiness-blocker lens, exposes the required selectors/search/filters/layout controls,
  and keeps readiness tied to graph validation rather than layout. Static tests now lock the pinned
  runtime URLs, relative graph paths, and `node_id`/edge endpoint mapping; local browser
  verification covered desktop source-set, desktop review overlay, and mobile graph canvas
  screenshots with nonblank graph-root pixel checks.
- NEPA 3D Milestone 6 dropdown gap closure is implemented in the isolated worktree branch
  `codex/nepa-3d-dropdown-gaps`. The viewer now separates authority category and authority family,
  labels status/readiness and currentness/partition filters more accurately, splits node/edge type
  from evidence/basis values, reads forest-unit filters from exported `forest_code` values, adds
  graph-export counts plus grounding metadata to lens and filter options, adds a Clear filters
  action, and treats dropdown/search selections as context seeds so populated options no longer
  blank the graph. Live browser sweep on the isolated viewer covered all populated source-set and
  review-overlay lens/filter dropdown selections with `0` zero-node selections; some selections
  still show nodes without edges when the active lens has no matching edge path, and the status line
  now tells reviewers to try All validated graph data or clear filters.
- NEPA 3D Milestone 6 demo-mode closeout is implemented in the same isolated worktree branch. The
  viewer defaults to `v1-cg-ecid-compliance-review`, adds scene buttons above Lens, keeps the
  original dropdowns under Advanced filters, adds Reset demo, adds a right-side Capability shown
  panel with rendered graph counts and proof labels, and derives the evidence-path spotlight from
  actual graph edges so source record, artifact, chunk, evidence span, source claim, rule, decision,
  generated rule, and compliance finding steps are clickable rather than hard-coded.
- NEPA 3D graph legibility closeout adds scene labels and progressive node labels to the graph
  surface. Labels are generated from rendered graph nodes as Three.js sprites, show scene/anchor
  labels while zoomed out, reveal focus labels at mid zoom, and reveal additional node labels when
  zoomed closer. This is a visual legibility layer only; it does not alter graph validation,
  readiness, or source evidence.
- NEPA 3D service capabilities brief closeout adds a generated 4-page brief at
  `docs/capabilities/nepa_3d_capabilities_brief.pdf` with a matching HTML source and high-resolution
  graph figures under `docs/capabilities/assets/`. The brief is built by
  `tools/build_nepa_3d_capabilities_brief.mjs` from the validated
  `v1-cg-ecid-compliance-review` graph export and presents the professional NEPA review process:
  document intake, authority graph updates with the most current applicable regulations and
  procedures, applicability, reverse compliance,
  Forest Plan and full profile consistency review, evidence-path traceability, responsible-official
  decision support, and readiness blockers.
- The next NEPA 3D implementation boundary is Milestone 7 graph validation and promotion gates,
  unless the user chooses to deepen the Milestone 5 Beaverhead-Deerlodge component-inventory build
  first.
  The FSH 1909.15 chapter rows remain a scoped workbook/source delta before any graph export can
  claim handbook completeness.

Current stop conditions for the next session:

- Do not treat generated review success as proof of applicability correctness.
- Do not promote compliance-review eval outputs without applicability decision-quality evals.
- Do not let unresolved or `needs_adjudication` decisions become reviewer-ready by default.
- Do not let `compliance-review` override applicability decisions.
- Do not call the raw generated matrix or root-level manual review exports a Forest
  Supervisor-ready EA consistency decision-support document. The generated decision-support report
  is now the gated readiness artifact; root-level `East_Crazies_*` files remain non-canonical manual
  comparison material.
- Do not stage generated `source_library/` artifacts unless repository policy changes explicitly.

## Historical V1 Gate State

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
  --rule-pack source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review \
  --reuse-package-cache \
  --docling-timeout-seconds 180
```

Current run result:

- Package extraction wrote `43` manifest rows and `1,265` package chunks.
- Compliance review wrote JSON, Markdown, PDF matrix, and finding graph artifacts.
- Applicability validation covers `373` candidates with `33` applicable and `340` non-applicable
  authorities, no unresolved/adjudication decisions, and `generated_rule_pack_ready=true`.
- Compliance findings: `33` generated-pack findings, all `33` pass.
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
  minerals; regenerated findings have `79` supported components, `0` gaps, no supported package
  evidence with mismatched section binding, and `51` explicit affirmative Plan Consistency Table
  component-row bindings.
- Phase eval passes `10/10` phases after stale component adjudication artifacts are removed;
  `forest_plan_component_eval` passes, and the review is `reviewer_ready=true` at the phase gate.
  Phase eval now rejects stale component-adjudication eval artifacts whose recorded queue count
  differs from the current reviewer-resolution queue.
- V1 real-EA eval now passes the current source/section gate. All `13` required EA section families
  were detected, all `26` baseline authorities matched source records and document roles, citation
  requirements matched, and all Custer Gallatin forest-plan expectations pass, including zero open
  standard reviewer-resolution items.
- `nepa_4336b_programmatic_tiering` remains present and adjudication-pending, but Milestone 4 now
  routes its package evidence to the `alternatives`/`environmental_consequences` context expected by
  the V1 contract. The rule remains source-aligned to `R1EA-005` and document-role aligned to `law`.
- `v1-ea-eval` records separate lanes in `v1_ea_eval_results.json`: `broader_ea`, `forest_plan`,
  and `overall` all pass. Pending conditional adjudication is an explicit accepted V1 risk under
  `conditional_adjudication_policy.mode=accepted_pending_v1`, with exactly `14` pending
  `adjudicate` rows carried in the eval output.

Primary gate artifacts/checks:

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
- `v1_ea_eval_results.json` now reports `passed=true`, `broader_ea_passed=true`,
  `forest_plan_passed=true`, empty failure-category counts, `failed_rule_ids=[]`,
  `rule_section_match_rate=1.0`, `conditional_false_positive=0`, and
  `conditional_false_negative=0`.
- V1 EA gate repair milestone 1 locked the failure reproduction without changing applicability,
  trigger, or section-routing behavior. The eval summary now includes
  `failed_rule_expectation_count`, `failed_rule_ids`, `failed_rule_ids_by_category`, and
  `failed_rule_expectations`, naming the three CE false positives
  (`nepa_4336c_ce_adoption_screen`, `usda_nepa_ce_fanec_7cfr_1b3`,
  `usda_nepa_subcomponent_ce_7cfr_1b4`) and the two section mismatches
  (`nepa_statute_chapter_55`, `nepa_4336b_programmatic_tiering`).
- V1 EA gate repair milestone 2 added grouped positive applicability triggers for the three CE/FANEC
  conditional rules. The East Crazies review now keeps those rules `not_applicable` unless package
  evidence shows an adopted CE, CE/FANEC screen, categorical-exclusion path, USDA CE screening, or
  extraordinary-circumstances review. A follow-up gap pass added explicit
  `does_not_apply_if_package_terms` guards so negated same-chunk CE/FANEC language remains
  non-applicable evidence rather than a positive trigger.
- V1 EA gate repair milestone 3 routes `nepa_statute_chapter_55` package evidence to
  purpose-and-need environmental-assessment text. The live V1 eval now reports
  `rule_source_section_expectations_met=true`, `rule_section_match_rate=1.0`, and no
  `nepa_statute_chapter_55` section failure.
- V1 EA gate repair milestone 4 adds rule-declared package section term groups for
  `nepa_4336b_programmatic_tiering` and uses them as a package-evidence ranking/span preference.
  The live V1 eval now reports `nepa_4336b_programmatic_tiering` with actual package sections
  `alternatives` and `environmental_consequences`, actual source record `R1EA-005`, actual source
  document role `law`, and `adjudication_pending=true`. The follow-up gap pass made the new
  package section preference contract explicit in rule-pack validation and output-schema docs.
- V1 EA gate repair milestone 5 makes conditional adjudication explicit. All `18`
  conditional-source expectations now carry classification rationales, the contract accepts exactly
  `14` pending `adjudicate` rows under `conditional_adjudication_policy.mode=accepted_pending_v1`,
  and `v1-ea-eval` emits both a summary and full pending-results queue for those rows.
- V1 EA gate repair milestone 6 promoted the final pre-applicability V1 gate on 2026-05-03. That
  base-pack rerun had `44` findings, `40` pass findings, `4` not-applicable findings, all `26`
  baseline source records evaluated, `191` rule-claim links, and `0` rule-claim gaps. The current
  generated-pack V1 review supersedes it with `33` generated findings, `33` pass findings, `142`
generated-pack rule-claim links, and `0` rule-claim gaps. `forest-plan-component-eval` passes
  `35/35`, review-bound `phase-eval` passes `17/17`, and `v1-ea-eval` passes broader EA and
  forest-plan lanes. Base-pack compliance-gold eval outputs remain useful through
  `rule_pack_match_mode=generated_base`, but direct base-pack compliance-review reruns are
  diagnostic unless explicitly allowed.
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

Historical next implementation target, now superseded:

The V1 EA gate repair plan is complete through Milestone 6. This historical handoff originally
pointed to the revised `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md` as the next target.
Milestones 1 through 9 of that applicability-first plan are now implemented, and the separate
evidence-arbitration gap plan is complete through Milestone 5. The remaining target is Milestone 10
real-package expansion: resolve the ECID preliminary-EA adjudication worklist or add the third real
package fixture. Do not broaden the V1 claim beyond the current Custer Gallatin proving package
without a new evidence-backed plan and gate.

The forest-plan review evaluator now runs component-evaluation V0 by default for packages resolved
to the selected forest-plan profile. Mandatory component evaluation is committed at `8f607e4`, and
the NFMA standard-coverage gate is committed at `21d30b6`.

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
- Component outputs are `forest_plan_component_findings.json`,
  `forest_plan_component_findings.md`, `forest_plan_reviewer_resolution_queue.json`,
  `forest_plan_component_inventory_coverage.json`, and
  `forest_plan_applicable_standard_coverage.json`; forest-plan rows are linked from the
  review-level compliance matrix JSON, Markdown, and PDF.
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

Results from the latest pre-applicability live rerun: compliance review passed with `40` pass
findings and `4` not applicable findings; the current generated-pack review supersedes that with
`33` pass findings and `0` compliance not-applicable rows because non-applicable authorities now
live in `non_applicable_authorities.json`. Forest-plan context validation passes with `2`
geographic areas, `1` management area, `2` overlays, and `5` supporting plan-evidence routes.
Forest-plan component validation now passes: `329` components, `58` standards, `12` applicable
standards, `12` applied standards, `0` reviewer-resolution items, and zero unresolved applicable
standards. The prior
`AB-STD-RCREA-01` standard gap and the prior `21` non-standard queue items now have evidence-backed
support or correct not-applicable determinations. Component-level forest-plan eval passes all `35`
adjudicated cases with all-applicable-standard coverage. `phase-eval` passes `10/10` phases and
reports `reviewer_ready=true`;
`v1-ea-eval` now passes with forest-plan expectation match rate `1.0`,
section detection/source-record/document-role rates `1.0`, zero open standard reviewer-resolution
items, empty failure-category counts, and `failed_rule_ids=[]`.

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

Earlier forest-plan sequence verification: full test suite passed with `220 passed, 5 subtests
passed`; focused forest-plan component eval tests passed with `5 passed`; focused component-eval
phase test passed; lint, compile, JSON validation, and whitespace checks passed. The current
EA-gate milestone reran the compliance review and all promotion gates; `v1-ea-eval` now passes
with `broader_ea_passed=true`, `forest_plan_passed=true`, empty failure-category counts,
`conditional_false_positive=0`, `conditional_false_negative=0`, and forest-plan expectation match
rate `1.0`.

## Next Sequence

Next sequence for the current applicability lane:
`docs/POST_V1_REAL_PACKAGE_EXPANSION_MILESTONE_PLAN.md` Sequence 5. Sequence 4 imported and
extracted the South Plateau package, ran package context, applicability retrieval, applicability
determination, validation, and generated the six-item adjudication worklist. The next pass should
complete the adjudication template, run `applicability-adjudication-eval`, apply it, rerun
`applicability-validate`, and only then proceed to generated rule-pack, compliance review, and
review-scoped phase eval in a later sequence.

The V1 EA gate repair plan is closed. The current East Crazy Inspiration Divide review artifacts
were regenerated and verified, and the V1 EA gate is promoted after the broader EA lane,
forest-plan lane, phase eval, compliance-review eval, and gold eval all passed.

Candidate post-V1 goals:

- Broaden from the Custer Gallatin proving package to additional real Region 1 EA packages.
- Add embeddings/reranking behind the existing deterministic source, citation, and eval gates.
- Add model-assisted synthesis as a report layer without changing the deterministic readiness
  contract.
- Expand the adjudicated real-package eval set beyond the current Custer Gallatin V1 package and
  10-case compliance-gold fixture.

Non-goals:

- Do not broaden the claim to all Region 1 forests.
- Do not stage ignored generated `source_library/` outputs unless repository policy changes.
- Do not weaken source-record, document-role, citation, section, forest-plan, phase-eval, or
  validation gates.

Relevant files:

- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- `docs/V1_DEMO_DOCUMENT_REVIEW_MILESTONE_PLAN.md`
- `README.md`
- focused source/test/config changes from the prior gate-repair milestones

Current promoted eval signal:

- `v1-ea-eval` reports `passed=true`, `broader_ea_passed=true`, and `forest_plan_passed=true`.
- `phase-eval --review-id v1-cg-ecid-compliance-review` reports all phases passing.
- Compliance review eval and gold eval remain promotion-ready.

Promotion verification:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review
PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --eval-file config/v1_ecid_real_ea_eval.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval --output-dir source_library --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --rule-pack config/compliance_rule_pack_nepa_ea_v0.json --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src uv run --extra dev ruff check src tests
PYTHONPATH=src python -m compileall src
git diff --check
```

Commit policy:
Future post-V1 sequences should stage only their verified slice and commit atomically.

Stop conditions for the next plan:

- The proposed post-V1 scope would weaken source-record, document-role, citation, section,
  forest-plan, phase-eval, or validation gates.
- The proposed work would broaden the reviewer-ready claim beyond the current evidence-backed
  Custer Gallatin package without new eval coverage.
- Generated `source_library/` artifacts would need to become tracked without an explicit repository
  policy change.

Expert alignment notes retained from the earlier forest-plan sequence:

- Scott Vandegrift: readiness and reuse should be explicit; avoid unnecessary full-corpus rebuilds.
- Chuck Nicholson: the fixture should look like practitioner QA/QC, with transparent criteria and
  actionable gaps.
- Liz Esposito: every supported result must keep source-record IDs and evidence basis visible; do
  not convert the fixture into a legal conclusion.

Milestone 5 alignment closeout:

- Pending conditional rows are explicit accepted V1 risk, not resolved legal conclusions.
- Malformed conditional-adjudication policy counts or rule-ID lists fail contract validation.

Milestone 6 alignment closeout:

- The final V1 gate promotion passed through phase eval, V1 eval, compliance-review eval, gold eval,
  full tests, lint, compile, JSON validation, and docs promotion.
- The next milestone is outside the V1 EA gate repair plan.
