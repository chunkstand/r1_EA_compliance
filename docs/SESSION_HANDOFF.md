# Session Handoff

Date: 2026-05-06

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

Next implementation target:

The evidence-arbitration milestone plan is complete through Milestone 5. There are now two explicit
next-target lanes:

- `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md` Milestone 10: either complete and replay the
  three-item ECID applicability adjudication worklist for
  `region1-expansion-ecid-preliminary-ea`, or add the third real Region 1 EA package fixture if the
  user wants to broaden expansion coverage first.
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
  `35/35`, review-bound `phase-eval` passes `16/16`, and `v1-ea-eval` passes broader EA and
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

Next sequence for the current applicability lane: return to
`docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md` Milestone 10. The evidence-arbitration plan is
complete; the outstanding expansion blocker is the three-item ECID applicability adjudication
worklist, followed by replaying applicability validation, generated-rule-pack creation, compliance
review, and phase eval for `region1-expansion-ecid-preliminary-ea`.

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
