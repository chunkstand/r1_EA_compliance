# Current System State

This project is a local v1 NEPA Environmental Assessment reviewer-engine foundation for USDA
Forest Service Region 1 source material.

The workbook `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
is now the active capture and catalog source-of-truth input. The generated
`source_library/` remains the audited local evidence store used by extraction,
retrieval, evidence graph, source-claim extraction, rule-claim binding, and
deterministic EA package review commands, and it now contains preserved legacy
baseline artifacts, the active full-register canonical import, and
reviewer-ready downstream lanes.

For a fresh session start before this append-only state log, read
`docs/CURRENT_ROUTING.md` first and then the newest section at the top of
`docs/SESSION_HANDOFF.md`.

## West Reservoir Component Readiness Resolved To Compliance/V1 Gate

Latest implementation update on 2026-05-28 UTC:

- update:
  parent `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
  Milestone 2 is resolved locally on `source-set-f70ea11e04ae3d53`. The f70
  review/applicability spine is fresh through generated-rule-pack validation,
  the stale forest-plan identity registry has been rebound to f70, the seven
  Flathead support/overlay records supplied by the child packet are indexed
  under f70, `forest_plan_context_validation.json` passes, component
  adjudication eval passes with `48/48` resolved and `pending=0`, and component
  eval passes `27/27`. The remaining stop is parent Milestone 3 compliance
  review and V1 readiness promotion.
- resolved child blocker:
  `docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- current review identity:
  `review_id="west-reservoir-67436"`, `forest_unit_id="flathead-nf"`, and
  `source_set_id="source-set-f70ea11e04ae3d53"`
- fresh f70 review rebuild:
  `ea-review` passed with `reviewer_ready=true`,
  `validation_passed=true`, `package_file_count=12`,
  `package_chunk_count=659`, and `finding_status_counts={"pass":5}`.
- fresh f70 applicability context:
  `applicability-context-build` passed with `validation_passed=true`,
  `package_file_count=12`, `package_chunk_count=659`, and
  `fact_node_count=8116`.
- fresh f70 authority universe:
  `applicability-authority-universe` passed with
  `candidate_authority_count=146`,
  `forest_plan_component_candidate_count=80`,
  `forest_unit_id="flathead-nf"`, and
  `FINAL-FLAT-001` as the active plan source record.
- fresh f70 retrieval:
  `applicability-retrieve` passed with `candidate_authority_count=146`,
  `retrieval_trace_row_count=1314`, and `graph_trace_row_count=3650`.
- current applicability determination:
  the first f70 determination found `41` applicable, `102` non-applicable,
  and `3` `needs_adjudication` authority-family conflicts.
- tracked applicability adjudication:
  `config/applicability_adjudications/west-reservoir-67436.json` now matches
  the f70 decision hash and resolves all three conflicts as
  `human_applicable`: Clean Air Act conformity/air quality, species supporting
  sources and overlays, and vegetation/wildfire/forest health authorities.
- adjudication gates:
  `applicability-adjudication-eval` passed with
  `resolved_adjudication_count=3`, `pending_adjudication_count=0`, and no
  failure categories; `applicability-adjudication-apply` passed with
  `remaining_unresolved_authority_count=0`.
- final applicability validation:
  `applicability-validate` passed with `applicable_authority_count=44`,
  `non_applicable_authority_count=102`,
  `needs_adjudication_authority_count=0`,
  `unresolved_authority_count=0`, `reviewer_ready=true`, and
  `generated_rule_pack_ready=true`.
- generated rule pack:
  `applicability-generate-rule-pack` passed with
  `generated_rule_count=44`, `passed=true`, and
  `generated_rule_pack_ready=true`.
- identity-reconciliation closeout:
  `config/r1_forest_plan_identity_reconciliation_v1.json` now declares
  `active_source_set_id="source-set-f70ea11e04ae3d53"`,
  `exact_url_matched_source_record_count=74`,
  `governed_catalog_rebound_source_record_count=3`, and
  `unresolved_source_record_count=22`. Flathead governed bindings are
  `R1PLAN-flathead-nf-02 -> FINAL-FLAT-001`,
  `R1PLAN-flathead-nf-03 -> FPS-180`, and
  `R1PLAN-flathead-nf-05 -> FINAL-FLAT-003`.
- source-capture overlay closeout:
  the local generated f70 catalog gate
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  was overlaid with exactly `R1PLAN-flathead-nf-04`,
  `R1PLAN-flathead-nf-06`, `R1PLAN-flathead-nf-07`,
  `R1PLAN-flathead-nf-08`, `R1PLAN-flathead-nf-10`,
  `R1PLAN-flathead-nf-12`, and `R1PLAN-flathead-nf-16` from archived merged
  source-delta gate
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate`.
  The generated f70 extraction summary now reports
  `catalog_source_count=715`, `selected_source_count=715`,
  `extracted_count=715`, `failed_count=0`, `chunk_count=110982`, and
  `validation_passed=true`. The generated f70 retrieval summary reports
  `source_count=715`, `chunk_count=110982`, `reviewer_ready=true`, and
  `validation_passed=true`.
- repaired source-record readback:
  direct retrieval SQLite readback returns `R1PLAN-flathead-nf-04=1122`,
  `R1PLAN-flathead-nf-06=918`, `R1PLAN-flathead-nf-07=901`,
  `R1PLAN-flathead-nf-08=41`, `R1PLAN-flathead-nf-10=5`,
  `R1PLAN-flathead-nf-12=1535`, and `R1PLAN-flathead-nf-16=964` chunks.
- current resolver result:
  `forest-plan-resolve --review-id west-reservoir-67436 --source-set-id
  source-set-f70ea11e04ae3d53 --forest-unit-id flathead-nf` now emits
  current f70 `forest_plan_context.json`, `forest_plan_context_summary.json`,
  `forest_plan_component_findings.json`,
  `forest_plan_applicable_standard_coverage.json`, and
  `forest_plan_reviewer_resolution_queue.json`. Retrieval readiness passes
  with `blocking_missing_source_record_ids=[]`, and
  `forest_plan_context_validation.json` passes. Generated component findings
  now report `component_count=80`, `applicability_status_counts={"applicable":56,"not_applicable":24}`,
  `finding_status_counts={"gap":48,"not_applicable":24,"supported":8}`,
  `needs_reviewer_resolution_count=0`, and `reviewer_resolution_count=48`.
- component adjudication closeout:
  `config/forest_plan_component_adjudications/west-reservoir-67436.json` now
  matches the current f70 queue. `forest-plan-component-adjudication-eval`
  passes with `adjudication_item_count=48`, `resolved_adjudication_count=48`,
  `pending_adjudication_count=0`, `system_miss_count=48`,
  `real_ea_omission_count=0`, and disposition counts
  `applicability_false_positive=30` and `evidence_linking_miss=18`.
- component eval closeout:
  `config/forest_plan_component_evals/west-reservoir-67436.json` now matches
  current f70 generated evidence and the Flathead plan citation
  `FINAL-FLAT-001 (92d78498664e)` while preserving all `27` cases. The current
  `forest-plan-component-eval --review-id west-reservoir-67436` passes on
  `source-set-f70ea11e04ae3d53` with `passed_case_count=27`,
  `failed_case_count=0`, `expected_applicable_standard_count=14`, and empty
  failure categories.
- component aggregate truth:
  `forest-plan-component-eval-coverage` still reports `passed=false`, but West
  Reservoir now passes and source-set aligns. Aggregate counts are
  `covered_review_count=4/5`, `stale_identity_count=1`, and
  `unresolved_review_count=1`; the remaining failing slot is
  `ecid-source-delta-replay` / `v1-cg-ecid-source-delta-review` with
  `result_not_passed` and `result_source_set_id_mismatch`.
- stop condition:
  no compliance review, V1 promotion, phase eval, registry promotion, or
  aggregate promotion was run in this Milestone 2 slice.
- next implementation slice:
  run parent Milestone 3 compliance review and V1 readiness promotion in
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`. Keep West
  Reservoir typed blocked until compliance review, V1 eval, review-scoped phase
  eval, and registry/coverage promotion gates pass.

## West Reservoir Source-Set Migration Authority-Universe Proof Resolved

Latest implementation update on 2026-05-28 UTC:

- update:
  migration packet Milestone 2 is now resolved locally. Replay context, V1
  eval contract, component eval contract, component coverage, replay catalog
  surface, f70 forest-plan component inventory, and the West Reservoir
  authority universe now agree on `source-set-f70ea11e04ae3d53`.
- parity gate:
  `tests/test_west_reservoir_source_set_migration.py` verifies the tracked
  source-set surfaces agree on f70, verifies the selected f70 replay catalog
  surface, and includes a controlled mixed-source-set case that reports the
  stale surface.
- current source-set surfaces:
  `config/replay_contexts/west-reservoir-67436.json`,
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/forest_plan_component_evals/west-reservoir-67436.json`, and the
  West Reservoir component slot in
  `config/forest_plan_component_eval_coverage_v1.json` all now point to
  `source-set-f70ea11e04ae3d53`.
- current replay catalog surface:
  `config/replay_contexts/west-reservoir-67436.json` now points
  `catalog_dir` at
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`,
  whose manifest declares `source-set-f70ea11e04ae3d53`.
- typed-blocked status preserved:
  `config/v1_real_package_review_coverage_v1.json` still keeps West Reservoir
  as `alternate_package_typed_blocked` with
  `expected_contract_status="typed_blocked"`;
  `config/forest_specific_example_package_registry_v1.json` still keeps the
  West Reservoir example typed blocked and the Flathead route at
  `routing_status="typed_blocked_example_available"`.
- stop condition:
  no applicability retrieval, applicability determination, generated
  rule-pack refresh, forest-plan context, compliance review, V1 promotion,
  phase eval, registry promotion, or aggregate coverage promotion was run.
- f70 forest-plan component inventory rebuild:
  `forest-plan-components-build --source-set-id source-set-f70ea11e04ae3d53
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  passed with `component_count=410`, `standard_count=79`,
  `profile_result_count=3`, `blocked_forest_unit_ids=[]`, and
  `forest_unit_ids=["custer-gallatin-nf","flathead-nf","lolo-nf"]`.
- selected f70 authority-universe rerun:
  `applicability-authority-universe --review-id west-reservoir-67436
  --source-set-id source-set-f70ea11e04ae3d53` reads the selected f70 catalog
  and reports `candidate_authority_count=146`,
  `forest_plan_component_candidate_count=80`, `passed=true`, and
  `validation_passed=true`.
- resolved authority-universe checks:
  `candidates_have_source_evidence_available.failure_count=0`,
  `rule_template_candidates_have_source_claim_linkage.failure_count=0`, and
  `authority_family_template_candidates_cover_config.missing_source_record_count=0`.
- resolved component-inventory check:
  `forest_plan_component_candidates_use_profile_inventory` is green with
  `component_inventory_present=true`, `component_inventory_count=80`,
  `component_candidate_count=80`,
  `selected_component_forest_unit_ids=["flathead-nf"]`, and
  `required_profile_source_record_ids=["FINAL-FLAT-001"]`.
- next implementation slice:
  start with
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md` Milestone 1 on
  f70. Rerun the f70 artifact freshness steps before applicability
  retrieval/determination because the existing package applicability context
  was last rebuilt on pre-migration 4fb, and keep reviewer-ready promotion
  blocked until the parent gates pass.

- active parent packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- reduced child blocker:
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- active migration packet:
  `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`
- current status:
  West Reservoir remains stopped before applicability retrieval/determination.
  The same-source-set 4fb feasibility slice found no governed repair from the
  active 4fb catalog, so the migration packet moved the tracked contract to
  f70. The migrated authority universe is now green; the current next step is
  parent-plan f70 artifact freshness before applicability
  retrieval/determination.
- pre-migration 4fb authority-universe signal:
  `applicability-authority-universe --review-id west-reservoir-67436
  --source-set-id source-set-4fb59e9eb43045cb` still exits red with
  `passed=false`, `validation_passed=false`, `candidate_authority_count=146`,
  `forest_plan_component_candidate_count=80`,
  `candidates_have_source_evidence_available.failure_count=9`, and
  `authority_family_template_candidates_cover_config.missing_source_record_count=10`
- source-evidence feasibility:
  the failing snapshot requires `59` unique source-record IDs. `49` legacy IDs
  have governed current mappings in
  `config/compliance_source_record_reconciliation_v1.json`; none of those
  mapped current IDs are present in active
  `source-set-4fb59e9eb43045cb` (`source_count=647`), and all `49` are present
  in the later `source-set-f70ea11e04ae3d53` current-source-gap closeout
  catalog (`source_count=708`).
- migration boundary:
  the f70 catalog is now used only through the migrated tracked contract. Do
  not borrow any different catalog or promote reviewer-ready status without
  the parent readiness gates.
- stop condition:
  no applicability retrieval, applicability determination, generated rule-pack
  refresh, forest-plan context, compliance review, V1 promotion, phase eval,
  registry promotion, or aggregate coverage promotion was run after the
  feasibility finding.
- next implementation slice:
  start with
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md` Milestone 1.
  Rerun f70 artifact freshness, then applicability retrieval/determination on
  the selected migrated source set.

## West Reservoir Milestone 1 Source-Evidence Blocker Routed

Latest implementation update on 2026-05-28 UTC:

- active packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- active child blocker:
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`
- current status:
  Milestone 0 is committed locally; Milestone 1 started and is blocked before
  applicability retrieval/determination; the remaining source-evidence gap is
  now routed through the active child blocker
- local commit anchors:
  Milestone 0 baseline guard `d5d97ad`, Flathead authority-universe scoping
  `267ba9d`, source-evidence blocker route `0773ef7`, and docs-only Bitter
  Lesson alignment `3a5e6b3`
- successful Milestone 1 rebuilds:
  `ea-review` rebuilt `review_report.json` on
  `source-set-4fb59e9eb43045cb` with `reviewer_ready=true`,
  `validation_passed=true`, `package_file_count=12`,
  `package_chunk_count=659`, and `finding_status_counts={"pass":5}`;
  `applicability-context-build` rebuilt the package applicability context and
  fact graph with `validation_passed=true`
- reduced repair:
  the authority-universe builder now reads `forest_unit_id="flathead-nf"` from
  `config/replay_contexts/west-reservoir-67436.json`, records that forest unit
  in `authority_universe_snapshot.json`, removes the nonmatching
  `custer_gallatin_lmp_2022` base forest-plan rule from the review-scoped rule
  universe, selects `80` Flathead forest-plan component candidates, and uses
  `FINAL-FLAT-001` as the only forest-plan source record for West Reservoir
- current blocker:
  `applicability-authority-universe --review-id west-reservoir-67436
  --source-set-id source-set-4fb59e9eb43045cb` returned
  `passed=false` and `validation_passed=false`
- failing checks:
  `candidates_have_source_evidence_available` has `failure_count=9`, and
  `authority_family_template_candidates_cover_config` has
  `missing_source_record_count=10`
- resolved placement risk:
  the validation now reports
  `selected_component_forest_unit_ids=["flathead-nf"]`,
  `forest_plan_rule_source_record_ids=["FINAL-FLAT-001"]`, and
  `removed_forest_plan_rule_ids=["custer_gallatin_lmp_2022"]`; no Custer
  Gallatin forest-plan source record remains in the West Reservoir forest-plan
  authority candidates
- blocker evidence:
  the failing source records already map through
  `config/compliance_source_record_reconciliation_v1.json` to governed current
  rows such as `FED-044`, `FED-045`, `FED-055`, `FED-071`, `FED-083`, and
  `STP-031` through `STP-035`; direct active-catalog inspection found those
  current rows absent from `source_library/catalog/source_catalog.jsonl` on
  `source-set-4fb59e9eb43045cb` and present only in the later
  `source-set-f70ea11e04ae3d53` current-source-gap closeout catalog
- stop condition:
  no applicability retrieval, applicability determination, generated rule-pack
  refresh, forest-plan context, compliance review, V1 promotion, registry
  promotion, or aggregate coverage promotion was run after the blocker.
- next implementation slice:
  work from
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`. Prove a
  governed same-source-set repair for 4fb or route a dedicated source-set
  migration packet. Do not silently move West Reservoir to another source set.

## West Reservoir Milestone 0 Baseline Resolved

Latest implementation update on 2026-05-28 UTC:

- active packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- resolved slice:
  Milestone 0 current-contract baseline and stale-green guard
- closeout commit:
  `d5d97ad` (`Resolve West Reservoir baseline guard`)
- current target:
  `review_id="west-reservoir-67436"` on
  `source-set-4fb59e9eb43045cb` for `flathead-nf`
- package-authority status:
  `tests/test_west_reservoir_package_authority.py` passed `2/2`, preserving
  `12` official PDFs, `12` local package rows, byte-size and SHA-256 matches,
  and `omitted_document_count=0`
- V1 baseline:
  current `v1-ea-eval --review-id west-reservoir-67436` remains a truthful
  typed-blocked baseline with `contract_status="typed_blocked"`,
  `actual_overall_passed=false`, `broader_ea_passed=false`,
  `forest_plan_passed=false`, and only the allowed blocker categories:
  `review_artifact_missing=8`, `forest_plan_matrix_miss=1`,
  `forest_plan_reviewer_not_ready=1`, and `forest_plan_scope_miss=1`
- component baseline:
  current `forest-plan-component-eval --review-id west-reservoir-67436`
  remains red on `source-set-4fb59e9eb43045cb` with `0/27` cases passing and
  `failed_case_count=27`
- stale-artifact guard:
  the historical green `phase_eval_results.json` on
  `source-set-5e65d845ce77e1a0` is still historical only. A focused
  regression test now proves a review-scoped phase-eval rerun overwrites a
  pre-existing green result with the tracked replay-context source set.
- next implementation slice at that checkpoint:
  Milestone 1 review artifact spine rebuild on `source-set-4fb59e9eb43045cb`;
  this is superseded by the Milestone 1 authority-universe blocker section
  above.

## West Reservoir Reviewer Readiness Plan Opened

Latest planning update on 2026-05-28 UTC:

- active packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- current scope:
  make `west-reservoir-67436` reviewer-ready as the Flathead governed example
  on `source-set-4fb59e9eb43045cb`
- current boundary:
  the prior West Reservoir package-authority slice is resolved, but this
  planning update does not promote the review to reviewer-ready and does not
  change generated `source_library/` artifacts
- readiness blocker:
  current `v1_ea_eval_results.json` remains `contract_status="typed_blocked"`
  and the current component eval remains `0/27` passed until missing review,
  component, compliance, and phase artifacts are rebuilt on
  `source-set-4fb59e9eb43045cb`
- stale-artifact guard:
  the historical green West Reservoir `phase_eval_results.json` on
  `source-set-5e65d845ce77e1a0` is not current readiness proof for this
  packet
- next implementation slice at that checkpoint:
  Milestone 0 in the new plan: current-contract baseline,
  package-authority verification, and false-green source-set guard. This is
  superseded by the Milestone 0 baseline-resolved section above.

## West Reservoir Public Pinyon Authority Verified

Latest verification update on 2026-05-28 UTC:

- resolved provenance slice:
  the official Flathead National Forest project page for West Reservoir
  (`https://www.fs.usda.gov/r01/flathead/projects/67436`) was used to locate
  the linked Pinyon/Box folder
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/299363475796`
- document-completeness truth:
  `config/review_package_authority_verifications/west-reservoir-67436.json`
  records the complete visible public Pinyon tree for the West Reservoir
  project package: `12` PDFs across the root folder, `Project File Exhibits`,
  and `Scoping`; the existing local package manifest also has `12` rows
- byte-level verification:
  each official Box file was streamed from its public file URL and compared to
  `source_library/reviews/west-reservoir-67436/package/package_manifest.jsonl`;
  every document matched the manifest byte size and SHA-256, with
  `missing_from_local_manifest=[]`, `extra_in_local_manifest=[]`, and
  `omitted_document_count=0`
- updated authority surfaces:
  `config/replay_contexts/west-reservoir-67436.json`,
  `config/v1_real_package_review_coverage_v1.json`, and
  `config/forest_specific_example_package_registry_v1.json` now point to the
  official project page, Pinyon/Box folder, and verification manifest
- invariant truth:
  this proves package-authority completeness only. West Reservoir remains the
  governed Flathead typed-blocked example until the missing component-review
  generated artifacts are rebuilt and
  `forest-plan-component-eval --review-id west-reservoir-67436` passes.

## South Plateau Example Archived

Latest implementation update on 2026-05-27 MDT:

- resolved policy slice:
  user-directed archive of South Plateau as an example because the South
  Plateau EA is litigation-tainted for Forest Plan compliance
- updated routing truth:
  `config/forest_specific_example_package_registry_v1.json` now removes
  `cgnf-south-plateau-expansion` from active `review_examples` and from the
  Custer Gallatin `supplemental_example_ids`. The archived record remains
  under `archived_review_examples` with
  `usage_policy="historical_evidence_only_not_example"`.
- active coverage truth:
  `config/v1_real_package_review_coverage_v1.json` now removes the
  `south-plateau-reviewer-ready` slot from active `slots`, removes
  `expansion_reviewer_ready` from required active coverage classes, and keeps
  the former slot under `archived_slots`.
- promotion-suite truth:
  `config/promotion_suite_v1.json` now removes South Plateau from active
  `expansion_slots`, marks the South Plateau review case as archived-only, and
  keeps the former slot under `archived_expansion_slots`.
- Custer Gallatin example order:
  South Otter remains the primary Custer Gallatin example and East Crazy is
  the only supplemental active example. South Plateau must not be used as a
  Custer Gallatin or Region 1 example unless a future user-approved
  requalification packet restores it after the legal and Forest Plan concerns
  are resolved.
- evidence sources:
  official Forest Service project archive
  `https://www.fs.usda.gov/r01/custergallatin/projects/archive/57353` and
  court order PDF
  `https://westernlaw.org/wp-content/uploads/2025/12/2025.12.11-South-Plateau-Victory-Order.pdf`
- invariant truth:
  this archive slice does not modify workbook rows, source-register queue
  rows, source sets, generated `source_library/` evidence, or South Otter
  reviewer-stack artifacts.

## South Otter Primary Custer Gallatin Example Selection

Historical implementation update on 2026-05-27 UTC, superseded by the South
Plateau archive section above for Custer Gallatin supplemental-example routing:

- resolved policy slice:
  user-directed Custer Gallatin primary-example selection update after the
  South Otter Milestone 3 closeout
- primary-selection closeout commit:
  `c56039b` (`Promote South Otter as Custer Gallatin primary`)
- updated routing truth at that checkpoint:
  `config/forest_specific_example_package_registry_v1.json` set
  `primary_example_id="cgnf-south-otter-forest-specific"` for
  `custer-gallatin-nf`. East Crazy
  (`cgnf-east-crazy-current-promotion`) remained a governed supplemental
  example for the same forest. South Plateau was still listed as supplemental
  at that checkpoint, but the archive section above now supersedes that
  routing and removes South Plateau from active example use.
- invariant truth:
  South Otter remains outside `Document_Register_Master`; no source-register
  queue row was rerouted. The update changes Custer Gallatin example-selection
  priority only. It does not change South Otter's source set, replay context,
  required real-package coverage slot, required component-coverage slot, or
  distinct-forest thresholds.
- residual aggregate truth:
  aggregate component coverage still must not be described as green until the
  separate non-South Otter ECID source-delta and West Reservoir slots are
  repaired.

## South Otter Example Package Milestone 3 Resolved Locally

Historical implementation update on 2026-05-27 UTC, superseded by the primary
selection section above for Custer Gallatin example ordering:

- resolved packet:
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- continuing lane owner:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- packet outcome:
  `Milestone 3 resolved locally`; at this historical checkpoint South Otter
  became a governed supplemental Custer Gallatin example in
  `config/forest_specific_example_package_registry_v1.json`, a required
  real-package coverage slot in
  `config/v1_real_package_review_coverage_v1.json`, and a required passing
  component-eval coverage slot in
  `config/forest_plan_component_eval_coverage_v1.json`. It remains outside
  `Document_Register_Master`; no source-register queue row was rerouted.
- implementation closeout commit:
  `21eb2fa` (`Promote South Otter supplemental example`)
- registry identity truth:
  South Otter uses `example_id="cgnf-south-otter-forest-specific"`,
  `review_id="region1-example-custer-gallatin-south-otter-58396"`,
  `forest_unit_id="custer-gallatin-nf"`,
  `coverage_slot_id="cgnf-south-otter-forest-specific"`, and
  `applicable_forest_unit_ids=["custer-gallatin-nf"]`. At this historical
  checkpoint, the Custer Gallatin row kept East Crazy as primary and listed
  South Plateau plus South Otter as supplemental examples; the primary
  selection section above supersedes that ordering.
- real-package coverage truth:
  `real-package-review-coverage-eval` passes with `covered_slot_count=5`,
  `required_slot_count=5`, `reviewer_ready_slot_count=4`,
  `typed_blocked_slot_count=1`, `distinct_forest_count=3`,
  `distinct_package_style_count=6`, and no threshold failures.
- forest-specific registry truth:
  `forest-specific-example-package-eval` passes with `review_example_count=5`,
  `reviewer_ready_example_count=4`,
  `distinct_governed_example_forest_count=3`,
  `profile_guidance_only_count=7`, and no threshold failures.
- component coverage truth:
  the South Otter component slot is required, covered, source-set aligned, and
  passing. The aggregate `forest-plan-component-eval-coverage` command still
  fails on pre-existing non-South Otter slots: ECID source-delta has
  `result_not_passed` plus `result_source_set_id_mismatch`, and West Reservoir
  has `result_not_passed`. Current aggregate counts are
  `covered_review_count=3/5`, `stale_identity_count=1`, and
  `unresolved_review_count=2`.
- phase truth:
  review `phase-eval --review-id region1-example-custer-gallatin-south-otter-58396`
  now passes with `passed_phase_count=28`, `phase_count=28`, `blockers=[]`,
  and `review_direct_eval_status="direct_eval_present"`. The review-scope
  coverage summaries for `v1_ea_eval`, `real_package_review_coverage`, and
  `forest_plan_component_eval_coverage` are present and passing for South
  Otter.
- next routing:
  no additional South Otter milestone is selected. Future forest-specific
  example expansion should start from
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`; component
  aggregate repair remains a separate non-South Otter lane if selected.
- verification:
  JSON manifest validation; focused registry, coverage, component-coverage,
  CLI, and South Otter contract tests; focused Ruff; real-package coverage
  eval; forest-specific example-package eval; component-coverage aggregate
  rerun with named non-South blockers; and South Otter review `phase-eval`

## South Otter Example Package Milestone 2 Resolved Locally

Historical implementation update on 2026-05-27 UTC, superseded by the
Milestone 3 section above:

- historical packet:
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- continuing lane owner:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- packet outcome:
  `Milestone 2 resolved locally`; at this checkpoint South Otter was
  reviewer-ready under the local review stack, but it had not been promoted into
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/forest_plan_component_eval_coverage_v1.json`, or the queue ledger
- replay identity truth:
  the frozen review ID is
  `region1-example-custer-gallatin-south-otter-58396`, the forest identity is
  `custer-gallatin-nf`, the source set is `source-set-f70ea11e04ae3d53`, and
  the tracked replay context remains
  `config/replay_contexts/region1-example-custer-gallatin-south-otter-58396.json`
  against the narrowed `Final EA and Decision Notice Documents` package path
- applicability truth:
  the governed applicability replay now passes with `61` applicable
  authorities, `335` non-applicable authorities, `0` unresolved authorities,
  and `reviewer_ready=true`. The tracked applicability adjudication at
  `config/applicability_adjudications/region1-example-custer-gallatin-south-otter-58396.json`
  resolves all `8` items (`6` human applicable and `2` human not applicable).
- compliance truth:
  `compliance-review` with the generated South Otter rule pack now reports
  `reviewer_ready=true`, `validation_passed=true`, `61` findings, and status
  counts `pass=42`, `uncertain=17`, `gap=2`. Rule-claim binding remains
  reviewer-ready with one explicit no-claim gap for
  `forest_service_planning_handbook_amendments_authority_template`; the V1
  contract binds that authority through current source alias `USFS-008`.
- eval-contract truth:
  `config/v1_custer_gallatin_south_otter_real_ea_eval.json` now passes with
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`,
  `forest_plan_passed=true`, and `35` conditional source expectations.
- forest-plan component truth:
  `config/forest_plan_component_evals/region1-example-custer-gallatin-south-otter-58396.json`
  now passes `56/56` cases, covering all `43` raw applicable standards, the
  `5` standard-level reviewer-resolution items, representative non-standard
  queue cases, and hard negatives. The tracked component adjudication at
  `config/forest_plan_component_adjudications/region1-example-custer-gallatin-south-otter-58396.json`
  resolves `169/169` current queue items with `132`
  `applicability_false_positive`, `37` `evidence_linking_miss`, and `0`
  real-EA omissions.
- phase truth:
  review `phase-eval --review-id region1-example-custer-gallatin-south-otter-58396`
  passes with `passed_phase_count=28`, `phase_count=28`, `blockers=[]`, and
  `review_direct_eval_status="not_required_for_ad_hoc_review"` at the
  Milestone 2 checkpoint. Milestone 3 later promoted the governed registry and
  coverage manifest entries.
- next routing:
  superseded by the Milestone 3 closeout section above.
- verification:
  governed applicability replay and adjudication eval, generated rule-pack,
  compliance review, V1 eval, forest-plan component eval, forest-plan component
  adjudication eval, review `phase-eval`, focused South Otter contract test,
  and docs closeout gates

## Historical South Otter Example Package Milestone 1 Resolved Locally

Historical implementation update on 2026-05-27 UTC, superseded by the
Milestone 3 section above:

- historical packet:
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- continuing lane owner:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- packet outcome:
  `Milestone 1 resolved locally`; South Otter package authority is locally
  inventoried, downloaded, hash-recorded, and replay-context-ready. At the time
  of this Milestone 1 checkpoint, it had not been promoted into the governed
  registry or coverage manifests and was not reviewer-ready; Milestone 2 has
  since resolved the local reviewer stack above.
- selected package truth:
  the official project page is
  `https://www.fs.usda.gov/r01/custergallatin/projects/58396`, the linked
  Pinyon/Box folder is
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158227182465`, and
  the frozen review ID is `region1-example-custer-gallatin-south-otter-58396`
- intent truth:
  the South Otter packet now explicitly locks the example to
  `custer-gallatin-nf`; governed registry promotion uses
  `example_id="cgnf-south-otter-forest-specific"`,
  `coverage_slot_id="cgnf-south-otter-forest-specific"`, and
  `applicable_forest_unit_ids=["custer-gallatin-nf"]`. South Otter is now
  a supplemental Custer Gallatin example, but it must not count as a new
  distinct forest or be reused as generic Region 1 example guidance.
- workbook and queue truth:
  an active workbook search for `South Otter`, `projects/58396`, and `58396`
  found no matching row; no queue-ledger row was rerouted in this opening slice
- package authority truth:
  the full official Pinyon/Box root is present under ignored local evidence at
  `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/`.
  `box_inventory.json` and `box_import_manifest.json` record `58` folders,
  `639` files, `2,926,223,134` bytes, and `0` download failures
- replay package truth:
  the full Box root is retained as authority evidence, but it is too broad for
  replay because references and implementation-review material mention other
  Custer Gallatin districts. The tracked replay context now exists at
  `config/replay_contexts/region1-example-custer-gallatin-south-otter-58396.json`
  and uses
  `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/Final EA and Decision Notice Documents`
  as the package path on `source-set-f70ea11e04ae3d53`.
- review gate truth:
  `ea-review` on the narrowed replay package passes with `24/24` extracted
  files, `1,165` chunks, `5/5` checklist findings, `0` package failures, and
  `reviewer_ready=true`. A full-root `ea-review` also proved package cache
  viability (`517` supported files, `29,459` chunks, `0` extraction failures),
  but the root is not the replay package path.
- forest-plan context truth:
  full-root `forest-plan-resolve` reduced to an ambiguous scope because the
  root package includes broad references and implementation-review files.
  Narrowed-package `forest-plan-resolve` resolves the South Otter context with
  `validation_passed=true`, `scope_status="custer_gallatin"`,
  `geographic_area_count=1`, `management_area_count=33`, `overlay_count=9`,
  `supporting_plan_evidence_count=5`, and `unresolved_mention_count=0`.
  At this historical checkpoint the command still exited nonzero because
  downstream component evaluation was not reviewer-ready
  (`needs_reviewer_resolution_count=5`, `insufficient_evidence=8`, and missing
  component adjudication eval); Milestone 2 has since resolved that blocker
  through tracked component eval and component adjudication.
- registry and coverage truth:
  at this historical checkpoint,
  `config/forest_specific_example_package_registry_v1.json`,
  `config/v1_real_package_review_coverage_v1.json`, and
  `config/forest_plan_component_eval_coverage_v1.json` remained unchanged and
  South Otter stayed out of those governed manifests. Milestone 3 later
  promoted it into all three governed surfaces.
- next routing:
  this historical section originally routed to Milestone 2; the current route
  is now the Milestone 3 closeout section above.
- verification:
  full Box inventory/download readback, narrowed `ea-review`, narrowed
  `forest-plan-resolve` readback, focused replay-context test, strict
  milestone-plan lint, and `git diff --check`

## Lolo Tyler's Kitchen Example Package Milestone 3 Resolved Locally

Historical implementation update on 2026-05-27 UTC. It remains true for the
Lolo slot, but aggregate example and coverage counts are superseded by the
South Otter Milestone 3 section above:

- resolved packet:
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- continuing lane owner:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; Lolo National Forest now has a governed
  forest-specific example package through
  `region1-example-lolo-tylers-kitchen-66344`, and that package remains
  parallel to `Document_Register_Master`
- registry truth:
  `config/forest_specific_example_package_registry_v1.json` now routes
  `lolo-nf` as `real_package_examples_available`, sets
  `primary_example_id="lolo-tylers-kitchen-forest-specific"`, and records
  `queue_boundary_source_ids=["FOR-029"]`. The registry summary is now
  `review_example_count=4`, `reviewer_ready_example_count=3`,
  `typed_blocked_example_count=1`, and
  `profile_guidance_only_count=7`.
- real-package coverage truth:
  `config/v1_real_package_review_coverage_v1.json` now includes the required
  Lolo slot `lolo-tylers-kitchen-forest-specific` with coverage class
  `forest_specific_reviewer_ready`. The coverage thresholds now require
  `required_slot_count=4`, `required_coverage_class_count=4`,
  `distinct_forest_count_min=3`, `distinct_package_style_count_min=4`, and
  `reviewer_ready_slot_count_min=3`.
- queue truth:
  `config/source_register_queue_resolution_ledger_v1.json` now resolves
  `FOR-029` as
  `planned_disposition="forest_specific_example_package"` with
  `resolution_status="resolved"` while preserving the workbook queue identity
  text. The queue audit now reports
  `resolution_status_counts={"blocked":9,"planned":33,"resolved":9}`,
  `planned_disposition_counts={"forest_specific_example_package":1,"historical_scope_only":2,"named_blocker":9,"promote_direct_file":35,"promote_structured_export":4}`,
  `blocked_current_or_project_applicable_count=9`, and
  `resolved_current_or_project_applicable_count=9`.
- replay truth:
  Lolo `v1-ea-eval` remains `contract_status="reviewer_ready"` with
  `broader_ea_passed=true` and `forest_plan_passed=true`; Lolo review
  `phase-eval` now passes `28/28` with `blockers=[]` and
  `review_direct_eval_status="direct_eval_present"`.
- aggregate truth:
  `real-package-review-coverage-eval` passes with `covered_slot_count=4`,
  `reviewer_ready_slot_count=3`, `typed_blocked_slot_count=1`,
  `distinct_forest_count=3`, `distinct_package_style_count=4`, no missing
  required slots, and no missing coverage classes.
  `forest-specific-example-package-eval` passes with
  `review_example_count=4`, `reviewer_ready_example_count=3`,
  `distinct_governed_example_forest_count=3`,
  `profile_guidance_only_count=7`, and no threshold failures.
- gold and promotion truth:
  the gold coverage thresholds now require four tracked review contracts,
  three distinct forests, four package styles, and three reviewer-ready
  reviews. The quick existing-results gold coverage parity run passes those
  ratchets, and the non-strict promotion suite remains green for current
  promotion while strict expansion still truthfully fails only on
  `historical_source_set_split`.
- component-coverage boundary:
  the Lolo slot in `config/forest_plan_component_eval_coverage_v1.json` passes
  on `source-set-f70ea11e04ae3d53`, but the aggregate
  `forest-plan-component-eval-coverage` command remains red for non-Lolo
  source-delta and West Reservoir slots with `covered_review_count=2/4`,
  `stale_identity_count=1`, and `unresolved_review_count=2`.
- verification:
  focused coverage, registry, queue, CLI, gold, promotion, and architecture
  tests; Lolo `v1-ea-eval`; real-package coverage eval; forest-specific
  example-package eval; Lolo review `phase-eval`; source-register queue audit;
  quick existing-results gold coverage parity; non-strict promotion suite;
  expected-red component-coverage aggregate readback; ruff; strict plan lint;
  closeout doc parity; and `git diff --check`

## Lolo Current-Workbook Replay Rebaseline Resolved Locally

Latest implementation update on 2026-05-27 UTC:

- parent packet:
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- resolved packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- parent route:
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the tracked Tyler's Kitchen Lolo replay now consumes the
  current-workbook owner `source-set-f70ea11e04ae3d53` through
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`,
  and the source-register/current-workbook/source-record/aligned-runtime
  blocker chain is no longer the active route
- local closeout commit:
  `e28b373` (`Rebaseline Lolo replay on current source set`)
- implementation truth:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `config/applicability_adjudications/region1-example-lolo-tylers-kitchen-66344.json`,
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`,
  and
  `config/forest_plan_component_adjudications/region1-example-lolo-tylers-kitchen-66344.json`
  now align to `source-set-f70ea11e04ae3d53`. The Lolo forest-plan component
  inventory row now uses a Lolo replay-compatible source-set reference in
  `config/r1_forest_plan_component_inventory_build_manifest.json`.
- eval-contract truth:
  the Lolo v1 eval expected source-record set is now `59` IDs. The legacy
  duplicate `R1PLAN-lolo-nf-02` expectation was removed because current replay
  owns that forest-plan source through `FPS-298`; `R1PLAN-lolo-nf-01` remains
  in the eval contract.
- gate truth:
  `source-record-identity-gate` on the current `f70...` catalog passes with
  `expected_source_record_count=59`, `catalog_covered_source_record_count=59`,
  `identity_resolved_source_record_count=59`,
  `unmapped_source_record_ids=[]`,
  `mapped_targets_absent_from_catalog={}`, and `ambiguous_mappings={}`.
- replay truth:
  applicability validation passes with `54` applicable and `342`
  non-applicable authorities, the generated rule pack has `54` rules,
  compliance review is `reviewer_ready=true` with `scope_status="lolo_nf"`,
  forest-plan component eval and component adjudication eval pass, and
  `v1-ea-eval` reports `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`.
- phase truth:
  review `phase-eval --review-id region1-example-lolo-tylers-kitchen-66344`
  passes with `passed_phase_count=28`, `phase_count=28`, `blockers=[]`,
  `identity_mismatch_phase_count=0`, and
  `review_direct_eval_status="not_required_for_ad_hoc_review"`.
- aggregate component-coverage truth:
  the Lolo slot in `config/forest_plan_component_eval_coverage_v1.json` is now
  aligned to `source-set-f70ea11e04ae3d53` and passes, but the aggregate
  `forest-plan-component-eval-coverage` command remains red for non-Lolo slots:
  `covered_review_count=2/4`, `stale_identity_count=1`, and
  `unresolved_review_count=2`.
- next routing:
  Lolo is not automatically admitted into the forest-specific example registry
  by this blocker closeout. If continuing the lane, start from
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` Milestone 3 to
  update registry/coverage/queue thresholds and run the governed aggregate
  gates.
- verification:
  final source-record identity gate, governed applicability replay chain,
  compliance review with `--forest-unit-id lolo-nf`, forest-plan component eval,
  forest-plan component adjudication eval, `v1-ea-eval`, review `phase-eval`,
  strict plan lint, closeout doc parity, and `git diff --check`

## Lolo Source-Record Identity Reconciliation Milestone 1 Resolved Locally

Latest implementation update on 2026-05-27 UTC:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the replay-facing identity owner now exists as a generic
  `source-record-identity-gate`, and the Lolo current-workbook candidate gate
  now passes after explicit governed identity selectors resolved the five
  multi-target mappings
- local closeout commit:
  `dd3c322` (`Resolve Lolo source-record identity gate`)
- implementation truth:
  `src/usfs_r1_ea_sources/records.py` now owns the reusable source-record
  identity gate, with CLI exposure through `source-record-identity-gate`.
  The gate reads v1 eval expected source-record IDs plus optional explicit IDs,
  resolves them against a selected catalog, and keeps
  `config/compliance_source_record_reconciliation_v1.json` and
  `config/r1_forest_plan_identity_reconciliation_v1.json` as explicit owner
  inputs. Multi-target compliance coverage remains in `current_source_record_ids`,
  while replay-facing one-to-one identity uses `identity_source_record_id`
- governed selector truth:
  the five former ambiguous legacy IDs now resolve as
  `R1EA-018 -> USDA-007`, `R1EA-028 -> USDA-008`, `R1EA-124 -> FED-011`,
  `R1EA-137 -> FED-032`, and `R1EA-150 -> USFS-035`
- Lolo gate truth:
  running the gate against
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  for `source-set-f70ea11e04ae3d53` and
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json` returns `passed=true`,
  `expected_source_record_count=60`, `catalog_source_record_count=708`,
  `catalog_covered_source_record_count=60`,
  `identity_resolved_source_record_count=60`,
  `unmapped_source_record_ids=[]`,
  `mapped_targets_absent_from_catalog={}`, and `ambiguous_mappings={}`
- config boundary:
  no replay context, v1 eval contract, applicability adjudication config,
  forest-plan component eval config, compliance review artifact, or ignored
  `source_library/` JSON was patched in the Milestone 1 slice
- next routing:
  this is historical predecessor evidence. The newer section above records the
  Milestone 2-3 replay-config closeout on `source-set-f70ea11e04ae3d53`.
- verification:
  focused source-record identity and CLI tests, the actual green Lolo
  `source-record-identity-gate`, existing rule-claim and forest-plan
  reconciliation tests, architecture contract, ruff, strict plan lint, closeout
  doc parity, and `git diff --check`

## Lolo Source-Record Identity Reconciliation Milestone 0 Reduced Locally

Latest implementation update on 2026-05-27 UTC:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- predecessor packet:
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; current-workbook source-set rebaseline Milestone 1 reduced
  by exact stop because the remaining blocker was source-record identity, and
  source-record identity reconciliation Milestone 0 proved complete
  current-catalog coverage with then-unresolved ambiguity
- replay guard truth:
  a direct current-workbook `source-set-f70ea11e04ae3d53` applicability replay
  override against `region1-example-lolo-tylers-kitchen-66344` fails closed with
  `ReplayContextMismatchError` while the tracked replay context still declares
  `source-set-5e65d845ce77e1a0`
- identity truth:
  the current-workbook candidate manifest remains
  `source-set-f70ea11e04ae3d53` with workbook SHA
  `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97` and
  `708` catalog source-record IDs. The Lolo v1 eval contract expects `60`
  source-record IDs; `8` are direct hits in the `f70...` catalog surface, `51`
  absent expected IDs are covered by
  `config/compliance_source_record_reconciliation_v1.json`, and
  `R1PLAN-lolo-nf-02` is covered separately by
  `config/r1_forest_plan_identity_reconciliation_v1.json` as `FPS-298`.
  `missing_after_reconciliation=[]` and
  `mapped_targets_absent_from_current_catalog={}`, but five
  compliance-covered IDs still needed a replay-facing identity rule at that
  checkpoint: `R1EA-018`, `R1EA-028`, `R1EA-124`, `R1EA-137`, and
  `R1EA-150`. The newer Milestone 1 section above resolves those mappings.
- boundary truth:
  extraction-manifest hash matching is supporting evidence only. It is not the
  replay owner because historical-to-current hash comparison still has
  unmatched historical rows and one-to-many fanout
- next routing:
  continue at Milestone 1 of the routed packet to implement or choose a
  governed replay-facing identity contract that fails closed on unresolved
  ambiguity and can resolve direct, compliance-reconciled, and
  forest-plan-reconciled IDs before any tracked replay/eval config moves from
  `5e65...` to `f70...`
- verification:
  source-record identity inventory, replay-context override guard,
  reconciliation owner readback, strict plan lint, focused reconciliation tests,
  review `v1-ea-eval`, review `phase-eval`, closeout doc parity sweep, and
  `git diff --check`; no ignored `source_library/` JSON was patched

## Lolo Current-Workbook Source-Set Rebaseline Milestone 0 Reduced Locally

Latest implementation update on 2026-05-27 UTC:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the source-register currentness child resolved by stop
  because no exact current `source-set-5e65d845ce77e1a0` manifest/currentness
  surface exists locally, and this packet's Milestone 0 ruled out a silent
  `source-set-f70ea11e04ae3d53` manifest swap
- implementation truth:
  exact readback found the tracked Lolo replay context still on `5e65...` with
  `catalog_dir="source_library/catalog"`, while the active global catalog
  manifest is still `source-set-4fb59e9eb43045cb` with workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`
- current-workbook candidate truth:
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json`
  declares `source-set-f70ea11e04ae3d53` with the current active workbook SHA
  `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97`, but
  it is not a valid drop-in currentness owner for `5e65...`: the `5e65...`
  extraction manifest selects `350` source-record IDs, the `f70...` catalog
  has `708`, and the sets differ. Sampled mismatch shape shows `R1EA-*`
  source-record IDs on the `5e65...` side and `FED-*` IDs on the `f70...`
  side, so source-record identity compatibility must be handled by governed
  replay or an explicit narrower stop
- stale currentness truth:
  the historical `5e65...` authority-currentness report was generated on
  `2026-05-11T00:40:55.190598Z` from `source_library/catalog/source_set_manifest.json`
  with SHA `77361eec5963677104bf06dabe3f3d2934bfb75eae18990532d6054ba58152eb`;
  no local `source_set_manifest.json` currently has that hash
- remaining blocker truth:
  fresh review `phase-eval` remains red at `18/23` with failing phases
  `retrieval`, `rule_claim_binding`, `downstream_direct_evaluation`,
  `source_register_contract`, and `evaluation_coverage`; `v1-ea-eval` remains
  `reviewer_ready` but is not sufficient to claim Lolo ready while phase eval
  is red
- next routing:
  continue in
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 1 to run the smallest governed local replay path that can bind
  Lolo to a coherent current-workbook owner, or stop at the exact
  source-record identity, catalog, package-cache, extraction, or direct-eval
  surface that cannot be replayed locally
- verification:
  replay-context, active manifest, archived manifest, currentness-report input
  hash, source-record-set compatibility, `v1-ea-eval`, review `phase-eval`,
  focused phase-eval tests, strict plan lint, and `git diff --check`; no
  ignored manifest JSON was patched

## Lolo Source Register Currentness Blocker Opened Locally

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `opened locally`; aligned-runtime Milestone 1 reduced the Lolo blocker by
  refreshing review-local applicability, generated rule pack, and
  forest-plan component eval on `source-set-5e65d845ce77e1a0`, but
  `source_register_contract` still needs a narrower currentness owner before
  direct-eval rebaseline continues
- implementation truth:
  `applicability-authority-universe` now passes on `5e65...` with
  `candidate_authority_count=396` and
  `forest_plan_component_candidate_count=329`; the applicability refresh
  covered all `396` candidates, replayed the existing four-item Lolo
  applicability adjudication, and `applicability-validate` now passes with
  `54` applicable, `342` non-applicable, and
  `needs_adjudication_authority_count=0`. `applicability-generate-rule-pack`
  now passes with `generated_rule_count=54`, and
  `forest-plan-component-eval` now passes after the tracked eval contract
  moved to `source-set-5e65d845ce77e1a0`
- remaining blocker truth:
  fresh review `phase-eval` now reports `passed_phase_count=18/23` with
  failing phases `retrieval`, `rule_claim_binding`,
  `downstream_direct_evaluation`, `source_register_contract`, and
  `evaluation_coverage`. The review-local phases that were red at Milestone 0
  (`authority_universe`, `generated_rule_pack`, and
  `forest_plan_component_eval`) are now green
- source-register stop:
  `source_register_contract` still fails because `phase-eval` reads
  `source_library/catalog/source_set_manifest.json` through the tracked
  replay context's `catalog_dir`. That manifest still declares
  `source-set-4fb59e9eb43045cb` and workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`,
  while the active workbook hashes to
  `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97`.
  No exact archived `source-set-5e65d845ce77e1a0` manifest was found under
  `source_library/runs/**/source_set_manifest.json`
- live blocker truth:
  governed aggregates and roster contracts remain unchanged; Lolo is not a
  ready replacement, and current promotion / strict expansion semantics are
  not weakened
- next routing:
  historical route at that checkpoint was to continue in
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 0 to rebaseline the source-register manifest/currentness owner.
  That child later stopped to the current-workbook source-set rebaseline
  packet, then to the source-record identity packet. The newest section above
  records the current closeout: Lolo now replays on `source-set-f70ea11e04ae3d53`
  and review `phase-eval` passes `28/28`.
- verification:
  governed applicability and forest-plan component refresh commands,
  adjudication eval/apply, review `phase-eval`, source-register phase readback,
  replay-context and manifest/currentness source inspection, and no manual
  ignored JSON patching

## Lolo Aligned Runtime Rebaseline Milestone 0 Freshness Lock

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; Milestone 0 freshness-locked the aligned runtime family
  before any reruns and kept the blocker out of source-set contract drift
- previous committed active-packet closeout:
  `a7b4141` (`Open Lolo aligned runtime rebaseline blocker`)
- implementation truth:
  the tracked replay context and tracked `v1-ea-eval` contract both bind
  `region1-example-lolo-tylers-kitchen-66344` to
  `source-set-5e65d845ce77e1a0`, and live `v1_ea_eval_results.json` remains
  `contract_status="reviewer_ready"`, `passed=true`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`. Live
  `phase_eval_results.json` remains red at `15/23` on the same `5e65...`
  owner path with failing phases `retrieval`, `rule_claim_binding`,
  `downstream_direct_evaluation`, `source_register_contract`,
  `authority_universe`, `generated_rule_pack`,
  `forest_plan_component_eval`, and `evaluation_coverage`
- exact Milestone 0 inventory:
  `retrieval_eval_results.json` is contract-stale (`3ea1...` recorded versus
  current seed hash `394aa7...`) and semantically red on failed cases
  `nepa-alternatives-environmental-effects` and `scoping-public-comment` plus
  metric threshold misses; `rule_claim_link_eval_results.json` is
  contract-stale (`34faf3...` recorded versus current seed hash `59bce8...`)
  but its cases and metrics pass; shared
  `compliance_review_eval_results.json` passes with current contract hash
  `b229f5...` but still records `source-set-f70ea11e04ae3d53` instead of the
  aligned Lolo `5e65...` owner path; `authority_universe_snapshot.json` and
  `generated_rule_pack_validation.json` still declare
  `source-set-4fb59e9eb43045cb`; and
  `forest_plan_component_eval_results.json` records live `5e65...` artifacts
  but fails because
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`
  still declares `4fb...`
- source-register stop watch:
  the replay context has no review-local `source_manifest_path` or
  `workbook_path`, so `source_register_contract` still compares the active
  workbook SHA
  `1b62348930fa9c3595bea24b6ab4cfa4c7b0a3d2c29c1f1cfefebcf9d270cf97`
  against the global catalog manifest SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`
  on `source-set-4fb59e9eb43045cb`
- live blocker truth:
  the governed aggregates remain unchanged. This Milestone 0 readback did not
  admit Lolo into the governed roster, did not alter ECID historical slot
  semantics, and did not rerun or manually patch ignored `source_library/`
  runtime outputs
- next routing:
  continue in the same packet at Milestone 1 to rerun the governed
  review-local applicability companion chain and forest-plan component eval on
  `source-set-5e65d845ce77e1a0`, then classify whether
  `source_register_contract` can stay in-scope or must stop to a narrower
  manifest/currentness owner
- verification:
  exact `jq` readback of the tracked replay context, tracked `v1-ea-eval`
  contract, live `v1_ea_eval_results.json`, live `phase_eval_results.json`,
  global `source_set_manifest.json`, review-local
  `authority_universe_snapshot.json`, `generated_rule_pack_validation.json`,
  `forest_plan_component_eval_results.json`, the tracked forest-plan component
  eval contract, current eval seed hashes, live `5e65...` retrieval and
  rule-claim direct-eval result files, and the shared
  `compliance_review_eval_results.json`

## Lolo Aligned Runtime Rebaseline Blocker Opened Locally

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `opened locally`; source-set contract blocker Milestone 3 is now resolved
  locally because the remaining tracked Lolo red no longer belongs to contract
  alignment and now narrows to one aligned-runtime rebaseline family
- latest committed active-packet closeout:
  `a7b4141` (`Open Lolo aligned runtime rebaseline blocker`)
- implementation truth:
  the tracked replay context and tracked `v1-ea-eval` contract both already
  bind `region1-example-lolo-tylers-kitchen-66344` to
  `source-set-5e65d845ce77e1a0`, and fresh `v1-ea-eval` remains
  `contract_status="reviewer_ready"`. Fresh `phase-eval` stays red at
  `15/23`, but the remaining red is now one narrower aligned-runtime family:
  `retrieval_eval_results.json` and `rule_claim_link_eval_results.json`
  already exist on `5e65...` yet still fail current direct-eval identity
  checks; `retrieval-eval` is also semantically red on failing cases and
  metric thresholds; `compliance_review_eval_results.json` still records only
  shared `f70...` coverage; `authority_universe_snapshot.json` and
  `generated_rule_pack_validation.json` still declare `4fb...`; the tracked
  forest-plan component eval file still declares `4fb...` even though the
  live result already runs on `5e65...`; and `source_register_contract`
  currently falls back to the global `source_set_manifest.json`, which still
  declares `4fb...` and an older workbook SHA
- live blocker truth:
  the governed aggregates remain unchanged. Fresh coverage and promotion
  routing still admit only East Crazies, West Reservoir, and South Plateau as
  covered reviewer-facing reviews; non-strict `promotion-suite` remains
  `current_promotion_ready=true`, `promotion_ready=true`, and
  `expansion_ready=false`, with the only live expansion failure still
  `historical_source_set_split` on the ECID historical slot
- next routing:
  historical route at that checkpoint was to continue in
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 0 to freshness-lock the stale aligned-runtime surfaces before
  any reruns. That packet has since reduced through Milestone 1 and routed to
  source-register/current-workbook rebaseline and then through source-record
  identity. The newest section above records the current closeout: Lolo now
  replays on `source-set-f70ea11e04ae3d53` and review `phase-eval` passes
  `28/28`. Treat
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
  as the exact predecessor that resolved the tracked source-set contract
  split, keep
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  as the older predecessor that reduced the generic feasibility lane, and
  keep
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  as historical package-authority context only
- verification:
  `jq` readback of the tracked replay context, tracked `v1-ea-eval`
  contract, live `phase_eval_results.json`, live
  `authority_universe_snapshot.json`, live
  `generated_rule_pack_validation.json`, live
  `forest_plan_component_eval_results.json`, current
  `config/forest_plan_component_evals/region1-example-lolo-tylers-kitchen-66344.json`,
  current `source_library/catalog/source_set_manifest.json`, and the live
  `5e65...` retrieval/rule-claim direct-eval results plus shared
  `compliance_review_eval_results.json`

## Historical Lolo Source-Set Contract Blocker Milestone 2 Checkpoint

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; Milestone 2 now realigns the tracked replay context and
  tracked review eval contract to the chosen `5e65...` owner path, and live
  work now moves to Milestone 3 exact child-route or feasibility-stop
  closeout inside the same packet
- latest committed active-packet closeout:
  `e2b6941` (`Reduce Lolo source-set blocker Milestone 2`)
- implementation truth:
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  and `config/v1_lolo_tylers_kitchen_real_ea_eval.json` now both declare
  `source-set-5e65d845ce77e1a0`. Fresh
  `v1-ea-eval --review-id region1-example-lolo-tylers-kitchen-66344 --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json`
  now closes green with `passed=true`, `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`. Fresh review
  `phase-eval --review-id region1-example-lolo-tylers-kitchen-66344`
  remains red at `15/23` on the aligned owner path. The remaining failing
  phases are `retrieval`, `rule_claim_binding`,
  `downstream_direct_evaluation`, `source_register_contract`,
  `authority_universe`, `generated_rule_pack`,
  `forest_plan_component_eval`, and `evaluation_coverage`. That residual red
  is no longer a generic tracked-contract split: retrieval now reads a
  `5e65...` direct-eval artifact that is stale against the current retrieval
  eval seed and still fails thresholds; rule-claim direct eval also reads a
  `5e65...` artifact that is stale against the current rule-claim eval seed;
  downstream compliance direct eval still only exists on `f70...`;
  `generated_rule_pack_validation.json` still reports `4fb...`;
  `source_register_contract` now fails on workbook SHA drift;
  `authority_universe_snapshot.json` still fails `source_set_matches`; and
  `forest_plan_component_eval_results.json` still fails
  `component_eval_failed`
- live blocker truth:
  the governed aggregates remain unchanged. Fresh coverage and promotion
  routing still admit only East Crazies, West Reservoir, and South Plateau as
  covered reviewer-facing reviews; non-strict `promotion-suite` remains
  `current_promotion_ready=true`, `promotion_ready=true`, and
  `expansion_ready=false`, with the only live expansion failure still
  `historical_source_set_split` on the ECID historical slot
- next routing:
  continue in
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 3 to name one exact narrower runtime owner or one explicit
  stop condition for the residual `phase-eval` families above. Treat
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  as the exact predecessor that reduced the generic replacement-feasibility
  lane into this narrower packet, and keep
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  as historical package-authority context only
- verification:
  `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-example-lolo-tylers-kitchen-66344 --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-lolo-tylers-kitchen-66344`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  plus readback of the residual failing phases and the aligned tracked config
  surfaces named in
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`

## Historical Lolo Source-Set Contract Blocker Milestone 1 Checkpoint

Historical checkpoint on 2026-05-26 before Milestone 2 closeout commit
`e2b6941`:

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; Milestone 1 now classifies one bounded review-local owner
  path inside the source-set contract blocker, so live work now moves to
  Milestone 2 in the same packet
- closeout commit:
  `20b51b6` (`Advance Lolo source-set blocker to Milestone 2`)
- implementation truth:
  fresh tracked readback now classifies a bounded review-local owner path for
  `region1-example-lolo-tylers-kitchen-66344` on
  `source-set-5e65d845ce77e1a0`. The replay context
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  and `config/v1_lolo_tylers_kitchen_real_ea_eval.json` still declare
  `source-set-4fb59e9eb43045cb`, and the live review
  `phase_eval_results.json` still uses `4fb...` expectations. But the live
  `v1_ea_eval_results.json`, `review_validation.json`,
  `applicability/applicability_validation.json`,
  `forest_plan_context_summary.json`,
  `authority_reviewer_resolution_report.json`,
  `compliance_matrix.json`, and
  `forest_plan_component_eval_results.json` now all report `5e65...`, and
  `applicability_validation.json` on that owner reports
  `passed=true` with `generated_rule_pack_ready=true`. The stale
  `4fb...` `generated_rule_pack_validation.json` is therefore now classified
  as bounded rerun debt rather than as a second review-local owner.
  `phase-eval` still shows one separate shared-runtime debt family:
  `downstream_direct_evaluation` remains partially anchored to stale
  compliance direct-eval coverage on `source-set-f70ea11e04ae3d53`
- live blocker truth:
  the governed aggregates remain unchanged. Fresh coverage and promotion
  routing still admit only East Crazies, West Reservoir, and South Plateau as
  covered reviewer-facing reviews; non-strict `promotion-suite` remains
  `current_promotion_ready=true`, `promotion_ready=true`, and
  `expansion_ready=false`, with the only live expansion failure still
  `historical_source_set_split` on the ECID historical slot
- next routing:
  continue in
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 2 to classify whether the remaining stale tracked `4fb...`
  contract surfaces plus shared `f70...` downstream direct-eval coverage are
  bounded rerun and realignment work on the chosen `5e65...` owner path or
  still require a narrower runtime owner. Treat
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  as the exact predecessor that reduced the generic replacement-feasibility
  lane into this narrower packet, and keep
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  as historical package-authority context only
- verification:
  `jq '{review_id, source_set_id, package_path, catalog_dir, source_manifest_path}' config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`,
  `jq '{review_id, source_set_id, package_path, required_review_artifact_ids, expected_summary}' config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `jq '{review_id: .summary.review_id, source_set_id: .summary.source_set_id, passed: .summary.passed, contract_status: .summary.contract_status, failed_checks: [.summary.checks[] | select(.passed == false) | {name, details}]}' source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`,
  `jq '{review_id, source_set_id, passed, passed_phase_count, phase_count, reviewer_ready, missing_direct_eval_phase_count, threshold_failed_phase_count, failed_phase_names: [.phases[] | select(.passed == false) | .name]}' source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`,
  and readback of the representative review-local artifact files named in
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`

## Historical Lolo Replacement Feasibility Blocker Checkpoint

Historical predecessor checkpoint on 2026-05-26 before closeout commit
`013b5d1`:

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; ECID blocker Milestone 3 is now closed because the
  exact next owner has been named, and live work now moves to tracked Lolo
  replacement-feasibility classification
- closeout commit:
  `6a4e87d` (`Open Lolo replacement feasibility blocker`)
- implementation truth:
  fresh tracked Lolo readback now proves a three-surface identity split that
  the broader Lolo example packet no longer owns truthfully. The replay
  context
  `config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`
  still declares `source_set_id="source-set-4fb59e9eb43045cb"`, and
  `config/v1_lolo_tylers_kitchen_real_ea_eval.json` still declares the same
  `4fb...` source set. But the live
  `source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`
  now reports `source_set_id="source-set-5e65d845ce77e1a0"`,
  `contract_status="mismatch"`, and one failing check:
  `review_identity_matches_contract`. The live
  `phase_eval_results.json` for that same review still reports
  `source_set_id="source-set-4fb59e9eb43045cb"`, `passed=false`, and
  `passed_phase_count=12/29`, with failing phases spanning direct-eval,
  graph, authority-universe, applicability, compliance, forest-plan component,
  and evaluation-coverage families
- live blocker truth:
  the governed aggregates remain unchanged. Fresh
  `real-package-review-coverage-eval` still admits only East Crazies,
  West Reservoir, and South Plateau; fresh non-strict `promotion-suite`
  remains `current_promotion_ready=true`, `promotion_ready=true`, and
  `expansion_ready=false` with the only live expansion failure still
  `historical_source_set_split` on the ECID historical slot. The broader
  Lolo example packet is now historical package-authority and registry
  context only; it no longer owns the current replacement-feasibility truth
- next routing:
  continue in
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 1 to classify the tracked contract and review-identity owner
  surfaces before any roster, slot, or ready-state changes are considered.
  Treat
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  and
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  as historical predecessors only
- verification:
  `jq '{review_id: .summary.review_id, source_set_id: .summary.source_set_id, passed: .summary.passed, contract_status: .summary.contract_status, actual_overall_passed: .summary.actual_overall_passed, broader_ea_passed: .summary.broader_ea_passed, forest_plan_passed: .summary.forest_plan_passed, failed_checks: [.summary.checks[] | select(.passed == false) | {name, details}]}' source_library/reviews/region1-example-lolo-tylers-kitchen-66344/v1_ea_eval_results.json`,
  `jq '{review_id, source_set_id, passed, passed_phase_count, phase_count, reviewer_ready, missing_direct_eval_phase_count, threshold_failed_phase_count, failed_phase_names: [.phases[] | select(.passed == false) | .name]}' source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`,
  `jq '{review_id, source_set_id, package_path, required_review_artifact_ids, expected_summary}' config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  and
  `jq '{review_id, source_set_id, package_path, catalog_dir, source_manifest_path}' config/replay_contexts/region1-example-lolo-tylers-kitchen-66344.json`

## Historical ECID Preliminary Governed Replacement Still Unproven Locally

Historical Milestone 2 checkpoint on 2026-05-26 before closeout commit
`6a4e87d`:

- routed packet:
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; blocker Milestone 2 is now complete, and no tracked
  governed replacement is currently proven under live artifacts
- Milestone 2 closeout commit:
  `191fc3e` (`Close ECID blocker Milestone 2`)
- implementation truth:
  fresh Lolo candidate proving now fails before any replacement-ready route
  can be named. `v1-ea-eval --review-id region1-example-lolo-tylers-kitchen-66344 --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json`
  exits red with `contract_status="mismatch"` because the eval contract still
  expects `source-set-4fb59e9eb43045cb` while the live review artifacts now
  report `source-set-5e65d845ce77e1a0`. Fresh review
  `phase-eval --review-id region1-example-lolo-tylers-kitchen-66344`
  also remains red at `12/29` on `source-set-4fb59e9eb43045cb`, with failing
  phases spanning missing direct-eval coverage
  (`retrieval`, `claim_extraction`, `rule_claim_binding`,
  `evaluation_coverage`) plus review-local source-set mismatch phases
  including `applicability_validation`, `compliance_review`,
  `forest_plan_component_eval`, and
  `forest_plan_component_adjudication`
- live blocker truth:
  the governed coverage and promotion aggregates remain stable and do not open
  a replacement route on their own. Fresh
  `real-package-review-coverage-eval` stays green with
  `reviewer_ready_slot_count=2`, `typed_blocked_slot_count=1`,
  `missing_required_slot_count=0`, and covered reviews still limited to
  East Crazies, West Reservoir, and South Plateau. Fresh non-strict
  `promotion-suite` remains `current_promotion_ready=true`,
  `promotion_ready=true`, and `expansion_ready=false`, with the only live
  expansion failure still
  `expansion_failure_category_counts={"historical_source_set_split":1}` on
  the ECID historical slot. No governed Lolo slot is admitted from current
  manifest truth
- next routing:
  continue in
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 3 to name one exact child packet or one narrower feasibility
  stop from the Milestones 1-2 evidence bundle. Do not open a replacement-ready
  child packet from the current tracked candidate set
- verification:
  `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-example-lolo-tylers-kitchen-66344 --eval-file config/v1_lolo_tylers_kitchen_real_ea_eval.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-example-lolo-tylers-kitchen-66344`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`,
  and
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`

## ECID Preliminary Historical Rebuild Path Exhausted Locally

Historical Milestone 1 checkpoint on 2026-05-26 before Milestone 2 closeout
`191fc3e`:

- routed packet:
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; blocker Milestone 1 is now complete, and no bounded
  historical-source-set rebuild path remains under current artifacts
- Milestone 1 closeout commit:
  `2149825` (`Route ECID historical blocker to Milestone 2`)
- implementation truth:
  `source-set-4fb59e9eb43045cb` is not a narrow rebuild lane. Its current
  source-set `phase_eval_results.json` still reports `passed=false` with
  `passed_phase_count=10/33`, and the failing phases still span upstream and
  downstream families including `extraction`, `retrieval`,
  `claim_extraction`, `rule_claim_binding`, `downstream_direct_evaluation`,
  `generated_rule_pack`, `compliance_review`, `review_packet_index`, and
  `evaluation_coverage`, with missing direct-eval and proxy-only failure
  reasons still present. `source-set-ba8d0feae79501b8` is also not a bounded
  rebuild lane: a fresh
  `applicability-validate --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8`
  still exits red, and the validation artifact continues to show
  `missing_candidate_decision=4`, `partition_gap=329`, `provenance_gap=1`,
  `source_set_stale=398`, and a candidate-authority split between four
  missing land-exchange rule-template authorities and a large unexpected
  Custer Gallatin forest-plan component family. Fresh
  `applicability-generate-rule-pack` on `ba8...` still fails closed because
  `applicability_validation.json` is stale for current artifacts
- live blocker truth:
  strict expansion still fails only on the ECID preliminary historical slot
  under `historical_source_set_split`; `source-set-4fb59e9eb43045cb` remains
  source-set `phase-eval` red at `10/33`;
  `source-set-ba8d0feae79501b8` still fails fresh
  `applicability-validate` with `source_set_stale=398`, `partition_gap=329`,
  `missing_candidate_decision=4`, `unresolved_authority=4`, and
  `provenance_gap=1`. At that Milestone 1 checkpoint the tracked governed
  replacement candidate had only been re-read as review `phase-eval` red at
  `19/23`; the fresher Milestone 2 rerun above is now the current blocker
  truth
- historical next routing at that checkpoint:
  continue in
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`
  at Milestone 2 to classify whether any tracked governed replacement can
  become ready without weakening the manifest floor. Do not open a historical
  source-set rebuild child packet from current artifacts
- verification:
  `jq '{source_set_id, passed, passed_phase_count, phase_count}' source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json`,
  `jq '.phases | map(select(.passed == false) | {name, reviewer_ready, failure_reasons})' source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8 --validation-path /tmp/ecid_preliminary_ba8_applicability_validation_20260526.json`,
  `jq '{source_set_id, passed, reviewer_ready, failed_checks: [.checks[] | select(.passed == false) | .details]}' /tmp/ecid_preliminary_ba8_applicability_validation_20260526.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-generate-rule-pack --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8`,
  and `git diff --check`

## ECID Preliminary Historical Lane Rebaseline Blocked Locally

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`
- packet outcome:
  `blocked locally`; Sequence 0 landed the fail-closed ready-slot source-set
  gate, but fresh Sequence 1 proving found no current truthful closure path
- implementation truth:
  ready expansion slots now fail closed when any JSON
  `expected_gate_artifact` proves a different `source_set_id` than the slot's
  declared `source_set_id`. This closes the loophole where a later session
  could flip `region1-real-ea-slot-1` to `ready` while its gate artifacts
  still came from mixed historical source sets
- live blocker truth:
  `source-set-4fb59e9eb43045cb` is not a viable rebuild lane under the current
  code: its source-set `phase_eval_results.json` is still
  `passed=false` with `passed_phase_count=10/33`. The older
  `source-set-ba8d0feae79501b8` closure assumption is also stale under current
  artifacts: a fresh
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8`
  now fails with `source_set_stale=398`, `partition_gap=329`,
  `missing_candidate_decision=4`, `unresolved_authority=4`, and
  `provenance_gap=1`, so rule-pack regeneration stops before compliance
  review. The tracked governed replacement candidate
  `region1-example-lolo-tylers-kitchen-66344` is also not currently ready for
  this slot. At that blocked-parent checkpoint its review
  `phase_eval_results.json` was only re-read at `passed=false` with
  `passed_phase_count=19/23`; the newer blocker rerun above is now the
  current truth
- next routing:
  this section is now historical blocked-parent context only. Continue in
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  which owns the exact blocker classification and next-packet routing. Do not
  flip the ECID historical slot to `ready`, shrink the manifest, or reuse
  another non-ready placeholder
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_promotion_suite_expansion_slots.py tests/test_promotion_suite.py tests/test_real_package_review_coverage_eval.py -q`,
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/promotion_suite_expansion.py tests/test_promotion_suite_expansion_slots.py`,
  `jq '{source_set_id, passed, passed_phase_count, phase_count}' source_library/derived/source-set-4fb59e9eb43045cb/evidence_graph/phase_eval_results.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-expansion-ecid-preliminary-ea --source-set-id source-set-ba8d0feae79501b8 --validation-path /tmp/<temp>/applicability_validation.json`,
  and
  `jq '{source_set_id, passed, passed_phase_count, phase_count}' source_library/reviews/region1-example-lolo-tylers-kitchen-66344/phase_eval_results.json`

## ECID Preliminary Historical Expansion Truthfully Rerouted Locally

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the remaining strict-expansion drift is no longer
  reported as six live required artifacts. The historical ECID
  preliminary-EA lane is now a selected-not-ready slot on an explicit split
  source-set contract while current promotion and the governed South Plateau
  slot remain green
- implementation truth:
  `config/promotion_suite_v1.json` now truthfully reroutes the historical
  ECID preliminary-EA slot by keeping only its applicability validation,
  generated rule-pack validation, forest-plan component adjudication
  template/eval, and review-scoped phase-eval as live required expansion
  artifacts. The six missing downstream compliance/provenance artifacts are no
  longer counted as active strict-expansion requirements on this packet. The
  slot now reports `status="selected_not_ready"` with
  `failure_category="historical_source_set_split"` and explicit
  `source-set-ba8d0feae79501b8` / `source-set-4fb59e9eb43045cb` split-signal
  evidence in its last-local-signal payload; `tests/test_promotion_suite.py`
  now enforces that committed contract
- live replay truth:
  `real-package-review-coverage-eval` still reports `passed=true`,
  `reviewer_ready_slot_count=2`, `missing_required_slot_count=0`, and
  `missing_coverage_class_ids=[]`. Non-strict `promotion-suite` now reports
  `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `open_expansion_slot_count=1`,
  `open_expansion_artifact_count=0`,
  `passed_required_current_result_count=32/32`,
  `passed_required_expansion_result_count=19/20`, and
  `expansion_failure_category_counts={"historical_source_set_split":1}`.
  Strict expansion now fails closed only because that rerouted historical slot
  is selected-not-ready:
  `failure_category_counts={"historical_source_set_split":1}`,
  `open_expansion_slot_count=1`, and `open_expansion_artifact_count=0`
- remaining blocker truth:
  the historical lane still spans `source-set-ba8d0feae79501b8` for
  applicability validation / phase eval and
  `source-set-4fb59e9eb43045cb` for generated rule-pack / slot identity. The
  six downstream compliance/provenance artifacts are still absent locally, but
  the suite no longer falsely claims they are live required expansion
  artifacts on this packet
- next routing:
  the later blocked-parent reroute above is now also historical. Current live
  work starts in
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`;
  see the top-of-file blocker-opened section for the current next slice
- verification:
  `PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  and
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion --strict-expansion`

## South Plateau Reviewer-Ready Expansion Restored Locally

Latest implementation update on 2026-05-26:

This section is now historical checkpoint context for the South Plateau repair
slice. The live aggregate truth moved forward in
`## ECID Preliminary Historical Expansion Truthfully Rerouted Locally` above.

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the governed South Plateau reviewer-ready expansion lane
  is now green on aligned reviewer-facing `source-set-f70ea11e04ae3d53`, and
  the remaining aggregate blocker has shifted to the historical ECID
  preliminary-EA expansion review-case artifact family rather than South
  forest-plan replay
- implementation truth:
  South replay-local applicability/source alignment, forest-plan adjudication,
  broader-EA source-evidence expectations, and promotion-suite slot contracts
  now line up on reviewer-facing `source-set-f70ea11e04ae3d53`. The packet
  now accepts adjudication-backed forest-plan readiness in
  `src/usfs_r1_ea_sources/compliance_validation_checks.py`, promotes
  applicability decision source evidence in
  `src/usfs_r1_ea_sources/v1_ea_eval_rule_expectations.py`, and refreshes the
  South contract and promotion manifest truth in
  `config/v1_south_plateau_real_ea_eval.json`,
  `config/forest_plan_component_adjudications/region1-expansion-south-plateau-landscape-treatment.json`,
  and `config/promotion_suite_v1.json` with matching regressions in
  `tests/test_v1_ea_eval.py`,
  `tests/test_forest_plan_component_adjudication.py`, and
  `tests/test_promotion_suite.py`
- live replay truth:
  `v1-ea-eval --review-id region1-expansion-south-plateau-landscape-treatment`
  now reports `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true` with
  `failure_category_counts={}`. Review `phase-eval` now passes `27/27` with
  `reviewer_ready=true`, `review_direct_eval_status="direct_eval_present"`,
  `missing_direct_eval_phase_count=0`, and
  `threshold_failed_phase_count=0`. `real-package-review-coverage-eval` now
  reports `passed=true`, `reviewer_ready_slot_count=2`,
  `missing_required_slot_count=0`, and `missing_coverage_class_ids=[]`. The
  later reroute closeout above now supersedes this section's older aggregate
  promotion counts
- remaining blocker truth:
  South Plateau is no longer the blocker. The remaining packet-local blocker is
  `region1-expansion-ecid-preliminary-ea`. In this historical checkpoint it
  was still expressed as a missing downstream compliance/provenance artifact
  family on a split source-set lane. The live top-of-file reroute section now
  records the later truthful selected-not-ready slot contract that superseded
  this earlier framing
- next routing:
  historical next routing at that checkpoint: resume
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` on the ECID
  preliminary-EA split historical lane. Current live routing is recorded in
  the reroute closeout section above
- verification:
  `PYTHONPATH=src python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  and
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion --strict-expansion`

## Architecture Governance Rebaseline Resolved Locally

Latest docs-and-gate rebaseline on 2026-05-26:

- routed packet:
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; architecture governance is green again against current
  repo truth, and the remaining issue is now the live oversized-file backlog
  itself rather than stale zero-oversized control-plane claims
- closeout commit:
  initial control-plane implementation landed in `182bfd6`
  (`Rebaseline architecture governance control plane`); this current-state
  readback keeps the resolved packet and docs parity aligned
- implementation truth:
  `config/architecture_large_file_inventory_v1.json` now records the exact
  reopened 2026-05-26 backlog at `9` code files above `800`, grouped as `4`
  source owners and `5` test owners with focused follow-on test surfaces.
  `README.md` is now a stable public entrypoint instead of a second
  current-state log, and `tests/test_architecture_quality.py` now fail-closes
  on exact inventory membership, stale empty-closeout payloads, an overlong
  `docs/CURRENT_ROUTING.md`, volatile README drift, and current-state
  duplication outside this file plus the top of `docs/SESSION_HANDOFF.md`
- live architecture truth:
  `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20`
  now reports `472` code files, `9` code files above `800`, no Python or JS/TS
  import cycles, and no source module above the `20`-import fan-out gate.
  `docs/CURRENT_ROUTING.md` is back under its enforced short-route cap, while
  the 2026-05-21 under-`800` closeout remains historical truth rather than a
  false record; the current weakness was later governance drift plus later code
  growth after that closeout
- remaining architecture debt:
  the live oversized backlog is now routed explicitly from the inventory:
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py`,
  `src/usfs_r1_ea_sources/extract_runtime.py`,
  `src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py`,
  `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`,
  `tests/test_applicability_authority_family_templates.py`,
  `tests/test_promotion_suite_full_canonical.py`,
  `tests/test_extraction_accuracy.py`,
  `tests/test_forest_plan_resolver_scope.py`, and `tests/test_catalog.py`
- next routing:
  keep the live implementation route on
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` for reviewer-facing
  replay repair. The next architecture-specific follow-on should be a separate
  owner-reduction packet opened from
  `config/architecture_large_file_inventory_v1.json`, starting with the four
  source owners above and then the five test owners
- verification:
  `git status -sb`,
  `python /Users/chunkstand/.codex/skills/code-architecture-governance/scripts/architecture_probe.py --format markdown --max-file-lines 800 --max-fan-out 20`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_architecture_contract.py tests/test_architecture_quality.py -q`,
  `PYTHONPATH=src uv run --extra dev ruff check tests/test_architecture_contract.py tests/test_architecture_quality.py`,
  `PYTHONPATH=src python -m compileall tests/test_architecture_quality.py tests/test_architecture_contract.py`,
  `wc -l docs/CURRENT_ROUTING.md README.md`,
  `rg -n "Canonical source-register refoundation status on|Historical local import baseline on|current_promotion_ready|reviewer_ready=true|source-set-[0-9a-f]{16}" README.md`,
  and `git diff --check`

## ECID Current-Promotion Replay Resolved Locally (Historical Mid-Packet Checkpoint)

This section records the intermediate packet state before the later South
Plateau repair summarized above.

Latest implementation update on 2026-05-26:

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; ECID current-promotion replay is green end to end on
  reviewer-facing `source-set-f70ea11e04ae3d53`. At this historical checkpoint,
  South Plateau still remained to be repaired; current top-of-file routing has
  since moved past South to the ECID preliminary-EA historical expansion lane
- implementation truth:
  the ECID repair now spans the broader review-local packet family: aligned
  direct-eval contracts for retrieval / claim / rule-claim, decision-support
  evidence fallback, review-packet and final-QA self-reference accounting,
  knowledge-graph proving backfill, and truthful promotion-suite graph
  expectations for the packet-scoped `source-set-f70ea11e04ae3d53`. The live
  ECID packet boundary remains `55` applicable, `341` non-applicable, and
  `396` candidate authorities
- live replay truth:
  `v1-ea-eval --review-id v1-cg-ecid-compliance-review` now reports
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`, and
  `forest_plan_passed=true` with no remaining failure categories. The
  governed real-package coverage gate is now narrowed to the remaining South
  slot: `real-package-review-coverage-eval` reports
  `reviewer_ready_slot_count=1`, `missing_required_slot_count=1`, and
  `missing_coverage_class_ids=["expansion_reviewer_ready"]`.
  West Reservoir remains truthful `typed_blocked`. The current South slot
  still reports `contract_status="mismatch"` with
  `failure_category_counts={"conditional_false_negative":9,"forest_plan_matrix_miss":1,"review_artifact_missing":4,"rule_missing":9}`.
  The non-strict promotion path now stays green only for current promotion,
  while strict expansion still fails closed on South Plateau debt. The
  current non-strict `promotion-suite` result reports
  `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, and `passed_required_current_result_count=32/32`;
  the strict-expansion result reports `current_promotion_ready=true`,
  `promotion_ready=false`, `expansion_ready=false`,
  `open_expansion_slot_count=1`, and `open_expansion_artifact_count=19`.
  The strict-expansion failure categories are
  `{"adjudication_needed":2,"forest_plan_reviewer_not_ready":7,"stale_artifact":10,"unsupported_package_evidence":2}`.
  The
  `review_packet_index` validation is green with `failed_check_count=0`.
  `ea-consistency-document` is green on the aligned packet, source-set graph
  evals now pass with `authority_path_count=17`,
  `relationship_type_count=7`, `orphan_node_count=0`, and
  `disconnected_component_count=1`, `draft-generation-eval` passes `5/5`,
  `final-qa-certification` reruns green with `198` passing checks and
  `machine_replay_status="passed"`, review-scoped `phase-eval` now passes
  `33/33` with `reviewer_ready=true`,
  `review_direct_eval_status="direct_eval_present"`,
  `missing_direct_eval_phase_count=0`, and
  `threshold_failed_phase_count=0`, and non-strict `promotion-suite` now
  reports `current_promotion_ready=true`, `promotion_ready=true`, and
  `passed_required_current_result_count=32/32`. The truthful packet-scoped
  source-set graph still carries `region1_forest_plan_blocked_profile_count=9`
  rather than a fake zero-blocker full-Region-1 claim
- remaining blocker truth:
  At this checkpoint, South Plateau carried the remaining packet-local replay
  debt on the same aligned source set. ECID broader-EA, direct-eval, final-QA,
  and current-promotion aggregate replay were no longer the blocker. Current
  top-of-file routing has since moved past South to the ECID preliminary-EA
  historical expansion lane
- next routing:
  historical next routing at that checkpoint: resume
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`, beginning with
  South Plateau packet-local forest-plan replay / adjudication refresh on
  aligned `source-set-f70ea11e04ae3d53`, then finish the packet's aggregate
  docs / closeout slice
- verification:
  `PYTHONPATH=src python -m usfs_r1_ea_sources draft-generate --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources draft-generation-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources final-qa-certification --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_authority_currentness.py tests/test_claim_extraction_eval.py tests/test_ea_consistency_decision_support.py tests/test_ea_consistency_decision_support_report.py tests/test_final_qa_certification.py tests/test_graph_accuracy_eval.py tests/test_nepa_knowledge_graph_export.py tests/test_nepa_knowledge_graph_export_review.py tests/test_phase_eval_direct_eval_contracts.py tests/test_promotion_suite.py tests/test_promotion_suite_full_canonical.py tests/test_retrieval.py tests/test_retrieval_eval.py tests/test_review_packet_index.py tests/test_rule_claim_binding_eval.py tests/test_rule_claim_binding_runtime.py tests/test_v1_ea_eval.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_compliance_phase_eval.py tests/test_phase_eval.py tests/test_draft_generation.py tests/test_draft_generation_eval.py tests/test_cli_derived.py tests/test_cli_eval.py -q`,
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/authority_currentness.py src/usfs_r1_ea_sources/authority_relationship_eval.py src/usfs_r1_ea_sources/citation_alias_eval.py src/usfs_r1_ea_sources/claim_extraction_eval.py src/usfs_r1_ea_sources/cli_derived.py src/usfs_r1_ea_sources/cli_derived_registration.py src/usfs_r1_ea_sources/ea_consistency_decision_support_inputs.py src/usfs_r1_ea_sources/ea_consistency_decision_support_models.py src/usfs_r1_ea_sources/ea_consistency_decision_support_report.py src/usfs_r1_ea_sources/final_qa_certification_counts.py src/usfs_r1_ea_sources/final_qa_certification_report.py src/usfs_r1_ea_sources/final_qa_certification_runtime.py src/usfs_r1_ea_sources/graph_accuracy_eval.py src/usfs_r1_ea_sources/graph_health_eval.py src/usfs_r1_ea_sources/nepa_knowledge_graph_export_common.py src/usfs_r1_ea_sources/nepa_knowledge_graph_export_forest_plan.py src/usfs_r1_ea_sources/nepa_knowledge_graph_export_region1.py src/usfs_r1_ea_sources/nepa_knowledge_graph_export_review_validation.py src/usfs_r1_ea_sources/nepa_knowledge_graph_export_runtime.py src/usfs_r1_ea_sources/phase_eval.py src/usfs_r1_ea_sources/phase_eval_direct_eval_review.py src/usfs_r1_ea_sources/phase_eval_direct_eval_source_set.py src/usfs_r1_ea_sources/retrieval_eval_runtime.py src/usfs_r1_ea_sources/retrieval_query.py src/usfs_r1_ea_sources/review_packet_index_outputs.py src/usfs_r1_ea_sources/rule_claim_binding_eval.py src/usfs_r1_ea_sources/rule_claim_binding_runtime.py src/usfs_r1_ea_sources/rule_claim_binding_validation.py src/usfs_r1_ea_sources/source_register_proving.py src/usfs_r1_ea_sources/v1_ea_eval_rule_expectations.py tests/test_authority_currentness.py tests/test_claim_extraction_eval.py tests/test_ea_consistency_decision_support.py tests/test_ea_consistency_decision_support_report.py tests/test_final_qa_certification.py tests/test_graph_accuracy_eval.py tests/test_nepa_knowledge_graph_export.py tests/test_nepa_knowledge_graph_export_review.py tests/test_phase_eval_direct_eval_contracts.py tests/test_promotion_suite.py tests/test_promotion_suite_full_canonical.py tests/test_retrieval.py tests/test_retrieval_eval.py tests/test_review_packet_index.py tests/test_rule_claim_binding_eval.py tests/test_rule_claim_binding_runtime.py tests/test_v1_ea_eval.py tests/support/compliance_phase_eval_fixtures.py tests/test_compliance_phase_eval.py tests/test_phase_eval.py tests/test_draft_generation.py tests/test_draft_generation_eval.py tests/test_cli_derived.py tests/test_cli_eval.py`,
  `PYTHONPATH=src python -m compileall src/usfs_r1_ea_sources tests/test_authority_currentness.py tests/test_claim_extraction_eval.py tests/test_ea_consistency_decision_support.py tests/test_ea_consistency_decision_support_report.py tests/test_final_qa_certification.py tests/test_graph_accuracy_eval.py tests/test_nepa_knowledge_graph_export.py tests/test_nepa_knowledge_graph_export_review.py tests/test_phase_eval.py tests/test_phase_eval_direct_eval_contracts.py tests/test_promotion_suite.py tests/test_promotion_suite_full_canonical.py tests/test_retrieval.py tests/test_retrieval_eval.py tests/test_review_packet_index.py tests/test_rule_claim_binding_eval.py tests/test_rule_claim_binding_runtime.py tests/test_v1_ea_eval.py tests/test_draft_generation.py tests/test_draft_generation_eval.py tests/test_cli_derived.py tests/test_cli_eval.py`,
  and `git diff --check`

## Aligned ECID Compliance Replay And Inventory Mapping Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; aligned ECID Custer inventory and compliance replay are
  now green on reviewer-facing `source-set-f70ea11e04ae3d53`, but ECID
  broader-EA contract drift and South Plateau forest-plan replay remain open
- implementation truth:
  `src/usfs_r1_ea_sources/forest_plan_inventory_build_manifest.py` now
  supports `explicit_source_set_ids` references, and
  `src/usfs_r1_ea_sources/forest_plan_components_inventory_build.py` now
  matches forest-plan inventory profile rows through that governed
  multi-source-set surface. The Custer Gallatin profile row in
  `config/r1_forest_plan_component_inventory_build_manifest.json` now binds to
  both `source-set-4fb59e9eb43045cb` and
  `source-set-f70ea11e04ae3d53` through the shared `FOR-009` mapping, with
  focused regressions in
  `tests/test_forest_plan_inventory_build_manifest.py` and
  `tests/test_forest_plan_components_manifest.py`. The committed zero-item
  ECID adjudication template now also lives at
  `config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.json`
  with companion worklist
  `config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.md`
- live replay truth:
  `forest-plan-components-build --source-set-id source-set-f70ea11e04ae3d53
  --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  now rebuilds the aligned Custer inventory through `FOR-009` with
  `component_count=329`, `standard_count=58`,
  `coverage_passed=true`, and `component_source_accuracy_passed=true`.
  `forest-plan-component-adjudication-eval` now passes with
  `pending_adjudication_count=0`, and `compliance-review --review-id
  v1-cg-ecid-compliance-review` now passes with `reviewer_ready=true`,
  `validation_passed=true`, and forest-plan component adjudication/evaluation
  both `reviewer_ready=true`. ECID `v1-ea-eval` now remains
  `contract_status="mismatch"` with `forest_plan_passed=true`,
  `broader_ea_passed=false`,
  `failure_category_counts={"baseline_source_record_mismatch":26,"conditional_expectation_missing":18,"source_record_mismatch":17}`,
  and `forest_plan_failure_category_counts={}`. South remains the live
  forest-plan blocker with `reviewer_ready=false`, `component_count=329`,
  `reviewer_resolution_count=34`, `needs_reviewer_resolution_count=1`,
  `gap_count=33`, `applied_standard_count=22/25`, and stale component
  adjudication eval checks
  `["source_set_mismatch","queue_item_count_mismatch","resolved_item_count_mismatch"]`.
  `real-package-review-coverage-eval` remains red at
  `reviewer_ready_slot_count=0`: ECID is now mismatch-only on broader-EA
  categories, South remains mismatch on forest-plan plus broader-EA, and West
  Reservoir remains truthful `typed_blocked`. `phase-eval --review-id
  v1-cg-ecid-compliance-review` remains red at `15/31` passed phases with
  `review_direct_eval_status="direct_eval_identity_mismatch"`; the remaining
  blocker phases are retrieval, claim extraction, rule-claim binding,
  downstream direct evaluation, decision support, review packet, final QA,
  aggregate evaluation coverage, and the downstream graph/export families
- remaining blocker truth:
  ECID aligned compliance review and component replay are no longer the
  blocker. The next live blocker is ECID broader-EA review-local artifact /
  source-record alignment on `source-set-f70ea11e04ae3d53`, followed by South
  Plateau forest-plan replay / adjudication refresh and the still-unresolved
  source-delta / West / Lolo aggregate component-eval coverage slots
- next routing:
  resume `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  beginning with ECID broader-EA review-local artifact / source-record
  alignment on aligned `source-set-f70ea11e04ae3d53`, then South Plateau
  forest-plan replay / adjudication refresh on that same source set
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_components_manifest.py -q`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-component-adjudication-template --output-dir source_library --review-id v1-cg-ecid-compliance-review --output-path config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-component-adjudication-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review --adjudication-file config/forest_plan_component_adjudications/v1-cg-ecid-compliance-review.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources compliance-review --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" --output-dir source_library --rule-pack source_library/reviews/v1-cg-ecid-compliance-review/applicability/generated_rule_pack.json --source-set-id source-set-f70ea11e04ae3d53 --review-id v1-cg-ecid-compliance-review --reuse-package-cache --docling-timeout-seconds 180`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`

## Aligned ECID Forest-Plan Replay Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; aligned ECID forest-plan component replay drift is now
  cleared, but reviewer-facing packet-local compliance/matrix replay remains
  open and South Plateau still carries real forest-plan review debt
- implementation truth:
  the Region 1 forest-plan identity reconciliation path is now enforced
  consistently across component eval, adjudication eval, coverage validation,
  and review-level forest-plan expectations.
  `src/usfs_r1_ea_sources/forest_plan_components_common.py`,
  `src/usfs_r1_ea_sources/forest_plan_component_eval_cases.py`,
  `src/usfs_r1_ea_sources/forest_plan_component_eval_validation.py`,
  `src/usfs_r1_ea_sources/forest_plan_component_adjudication_eval.py`, and
  `src/usfs_r1_ea_sources/v1_ea_eval_forest_plan.py` now normalize
  `FOR-009-*` and `R1PLAN-custer-gallatin-nf-02-*` identities through the
  governed reconciliation registry. The ECID component direct-eval contract
  surfaces now also point at reviewer-facing
  `source-set-f70ea11e04ae3d53` in
  `config/forest_plan_component_eval_seed.json` and
  `config/forest_plan_component_eval_coverage_v1.json`, with focused
  regressions in `tests/test_forest_plan_component_eval.py`,
  `tests/test_forest_plan_component_adjudication.py`,
  `tests/test_forest_plan_component_eval_coverage.py`,
  `tests/test_v1_ea_eval_forest_plan.py`, and
  `tests/test_phase_eval_direct_eval_contracts.py`
- live replay truth:
  ECID `forest_plan_context_summary.json` on
  `source-set-f70ea11e04ae3d53` now reports `reviewer_ready=true` with
  `component_count=329`, `applicable_count=79`,
  `reviewer_resolution_count=0`, `applied_standard_count=12/12`, and
  `validation_passed=true`. `forest-plan-component-eval --review-id
  v1-cg-ecid-compliance-review` now passes `35/35`, and
  `forest-plan-component-eval-coverage` now covers
  `v1-cg-ecid-compliance-review` with current slot `passed=true`,
  `stale_identity=false`, and `unresolved_review=false`. South Plateau
  remains the live forest-plan blocker on the same source set:
  `forest_plan_context_summary.json` still reports `reviewer_ready=false`,
  `component_count=329`, `reviewer_resolution_count=34`,
  `needs_reviewer_resolution_count=1`, `gap_count=33`, and
  `applied_standard_count=22/25`. ECID `v1-ea-eval` still remains
  `contract_status="mismatch"`, but its forest-plan failure family is now
  reduced to `forest_plan_failure_category_counts={"forest_plan_matrix_miss":1}`;
  the remaining broader-EA categories are
  `failure_category_counts={"baseline_source_record_missing":26,"citation_requirement_miss":4,"review_artifact_missing":4,"rule_section_mismatch":8,"source_record_mismatch":17}`.
  South still remains `contract_status="mismatch"` with
  `failure_category_counts={"conditional_false_negative":9,"forest_plan_matrix_miss":1,"review_artifact_missing":4,"rule_missing":9,"source_record_mismatch":26}`.
  `real-package-review-coverage-eval` remains red at
  `reviewer_ready_slot_count=0`, but ECID is no longer missing from
  `forest-plan-component-eval-coverage`: that aggregate now reports
  `covered_review_count=1`, `covered_review_ids=["v1-cg-ecid-compliance-review"]`,
  `stale_identity_count=2`, and `unresolved_review_count=3`. ECID
  `phase-eval` still remains `review_direct_eval_status="direct_eval_identity_mismatch"`
  because `v1-ea-eval` is still mismatched and required direct evals are still
  missing for retrieval, claim extraction, and rule-claim binding
- remaining blocker truth:
  ECID aligned component replay is no longer the blocker. The next live
  blocker is packet-local ECID reviewer-facing compliance review /
  compliance-matrix / authority-explanation replay on
  `source-set-f70ea11e04ae3d53`, followed by South Plateau forest-plan replay
  repair and the still-unresolved source-delta / West / Lolo aggregate
  component-eval coverage slots
- next routing:
  resume `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  beginning with ECID packet-local compliance review / compliance-matrix
  replay on aligned `source-set-f70ea11e04ae3d53`, then South Plateau replay
  repair on that same source set
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_component_eval.py tests/test_forest_plan_component_adjudication.py tests/test_forest_plan_component_eval_coverage.py tests/test_phase_eval_direct_eval_contracts.py tests/test_v1_ea_eval_forest_plan.py tests/test_v1_ea_eval_contracts.py -q`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-component-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-component-eval-coverage --output-dir source_library`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`

## Reviewer-Facing Source-Set Alignment Resolved Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/REVIEWER_FACING_SOURCE_SET_ALIGNMENT_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; reviewer-facing source-set authority-surface debt is now
  cleared, and control truthfully returns to packet-local replay repair on the
  aligned reviewer-facing source set
- implementation truth:
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`,
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json`,
  `config/v1_ecid_real_ea_eval.json`, and
  `config/v1_south_plateau_real_ea_eval.json` now align ECID and South
  reviewer-facing replay to
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  on `source-set-f70ea11e04ae3d53`. `src/usfs_r1_ea_sources/cli_applicability.py`
  now auto-loads the tracked replay-context catalog and manifest surfaces for
  applicability commands and fails closed on explicit source-set or catalog
  mismatches. Focused regressions now live in
  `tests/test_applicability_cli.py`, `tests/test_replay_context.py`, and
  `tests/test_v1_ea_eval_contracts.py`, while the earlier extraction
  direct-eval owner split remains enforced by
  `tests/test_phase_eval_direct_eval_contracts.py` and
  `tests/test_phase_eval.py`
- live replay truth:
  both reviewer-facing `applicability-authority-universe` reruns now pass on
  `source-set-f70ea11e04ae3d53` and the tracked
  `current-source-gap-closeout-catalog-gate` catalog surface. ECID and South
  each now report
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=33355dce05cb0141840bf5ad6463570173294e6e1a368d0e24f8910961a04554`,
  and `validation_passed=true`. `applicability-context-build` and
  `applicability-retrieve` now also pass for both reviews on that same source
  set, and governed replay adjudication is now green there as well: committed
  current-review applicability adjudications now live at
  `config/applicability_adjudications/v1-cg-ecid-compliance-review.json` and
  `config/applicability_adjudications/region1-expansion-south-plateau-landscape-treatment.json`,
  `applicability-validate` now passes for both reviews
  (`55 applicable / 341 non-applicable` for ECID and
  `64 applicable / 332 non-applicable` for South), and
  `applicability-generate-rule-pack` now passes with `55` ECID generated rules
  and `64` South generated rules on `source-set-f70ea11e04ae3d53`. The newly
  exposed blocker is the aligned reviewer-facing forest-plan replay lane:
  live `forest-plan-resolve` reruns on `source-set-f70ea11e04ae3d53`
  currently drive both ECID and South to
  `needs_reviewer_resolution_count=329`,
  `reviewer_resolution_count=329`, `applicable_count=0`,
  `supported_count=0`, and `reviewer_ready=false`, so the old component
  direct-eval slot cannot simply be rebound to the reviewer-facing source set
  without a real repair. ECID `v1-ea-eval` now remains
  `contract_status="mismatch"` with
  `failure_category_counts={"applicable_standard_not_evaluated":2,"baseline_source_record_missing":26,"citation_requirement_miss":4,"conditional_false_negative":1,"forest_plan_component_miss":1,"forest_plan_matrix_miss":1,"forest_plan_reviewer_not_ready":1,"forest_plan_reviewer_resolution_open":1,"forest_plan_standard_reviewer_resolution_open":1,"review_artifact_missing":4,"rule_section_mismatch":10,"source_record_mismatch":19}`.
  South now remains `contract_status="mismatch"` with
  `failure_category_counts={"conditional_false_negative":9,"forest_plan_matrix_miss":1,"review_artifact_missing":4,"rule_missing":9,"source_record_mismatch":26}`.
  ECID `phase-eval` now runs on `source-set-f70ea11e04ae3d53` with
  `review_direct_eval_status="direct_eval_identity_mismatch"` and remains red
  on the downstream packet family plus evaluation coverage
- remaining blocker truth:
  the reviewer-facing authority-surface mismatch and the aligned applicability
  adjudication debt are gone. The remaining live blocker is packet-local
  replay repair on the aligned reviewer-facing source set, led by the
  forest-plan component replay lane and then the downstream compliance,
  matrix/render, decision-support, packet-index, final-QA, and evaluation
  coverage families
- next routing:
  resume `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`,
  beginning with the aligned reviewer-facing forest-plan component replay
  blocker and then the ECID and South packet-local reviewer-ready downstream
  artifact families on `source-set-f70ea11e04ae3d53`
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-context-build --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-context-build --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-retrieve --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-retrieve --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-validate --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources phase-eval --output-dir source_library --review-id v1-cg-ecid-compliance-review`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources v1-ea-eval --output-dir source_library --review-id region1-expansion-south-plateau-landscape-treatment`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_applicability_cli.py tests/test_replay_context.py tests/test_v1_ea_eval_contracts.py tests/test_phase_eval_direct_eval_contracts.py tests/test_phase_eval.py tests/test_architecture_contract.py -q`

## Scoped Replay Derived-Artifact Chain Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the scoped replay-precondition lane is now green, but the
  broader ECID reviewer-ready replay repair remains open
- implementation truth:
  on `source-set-f70ea11e04ae3d53`, `reuse-inventory` classified `647`
  reusable extraction rows and `61` fresh extraction rows. `extract-build`
  then completed `708/708` extracted rows with `105496` chunks and
  `validation_passed=true`; `extraction-accuracy-audit` passed on `655`
  admitted active-current rows and `102769` audited chunks; `retrieval-build`
  is `reviewer_ready=true` with
  `verified_extraction_admitted_source_count=655`,
  `verified_extraction_required_source_count=655`, and
  `verified_extraction_explicitly_non_admitted_source_count=53`;
  `claim-extract` is `reviewer_ready=true` with `claim_count=134828`,
  `source_record_count=606`, and zero retrieval-binding or offset mismatches;
  `rule-claim-link` is `reviewer_ready=true` with `48/48` linked rules,
  `233` links, and `0` gaps
- live replay truth:
  `applicability-authority-universe --review-id
  v1-cg-ecid-compliance-review --source-set-id source-set-f70ea11e04ae3d53`
  now passes with `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `rule_template_candidate_count=48`,
  `authority_family_rule_template_candidate_count=19`, and
  `authority_universe_sha256=33355dce05cb0141840bf5ad6463570173294e6e1a368d0e24f8910961a04554`
- remaining blocker truth:
  the current-source misses and derived-artifact prerequisites are no longer
  the blocker. The remaining live work returns to ECID packet-local
  reviewer-ready artifacts on the governed real-package replay lane
- next routing:
  resume Milestone `1` of
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`, beginning with
  ECID `v1-ea-eval`, `phase-eval`, and the mapped current-review owner
  commands for review packet, decision support, final QA, and supporting
  outputs
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources reuse-inventory --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate --previous-source-set-id source-set-4fb59e9eb43045cb`,
  `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extract-build --output-dir source_library --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate --reuse-existing --reuse-inventory-path source_library/derived/source-set-f70ea11e04ae3d53/reuse_inventory/reuse_inventory.json`,
  `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53 --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources claim-extract --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources rule-claim-link --output-dir source_library --source-set-id source-set-f70ea11e04ae3d53`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-f70ea11e04ae3d53 --catalog-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json`,
  `PYTHONPATH=src uv run --extra dev pytest tests/test_extract_pdf_fallbacks.py -q`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `git diff --check`

## Active Authority Current-Source Gap Closeout To Replay Boundary Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the governed current-source inventory is now exhausted,
  but the scoped ECID applicability replay still remains red on a replay-local
  derived-artifact gap
- implementation truth:
  the canonical workbook now carries `708` retained master rows after adding
  `FED-078` through `FED-087`,
  `config/compliance_source_record_reconciliation_v1.json` now also maps
  `R1EA-020`, `R1EA-021`, `R1EA-027`, `R1EA-033`, `R1EA-034`,
  `R1EA-045`, `R1EA-046`, `R1EA-051`, `R1EA-054`, and `R1EA-055` to those
  governed current rows, and matching regressions now live in
  `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_catalog.py`,
  `tests/test_dry_run.py`,
  `tests/test_preflight.py`,
  `tests/test_applicability_authority_family_templates.py`, and
  `tests/test_applicability_candidate_assembly.py`
- live replay truth:
  the reviewer-facing default catalog remains historical
  `source-set-4fb59e9eb43045cb` at `647` source rows, `635` artifacts, and
  `594` admitted `active_review_corpus` rows. The active same-slice replay
  gate now lives at
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  as `source-set-f70ea11e04ae3d53` with `708` source rows, `696` artifacts,
  and `655` admitted `active_review_corpus` rows. Because the closeout
  additions did not change forest-plan source membership, the scoped replay
  carries the existing Region 1 component inventory forward under
  `source_library/derived/source-set-f70ea11e04ae3d53/forest_plan_components/component_inventory.json`
  with the inventory ownership rebound to the active source set. On that
  scoped gate,
  `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=5a7f58afc84a4701bfc23e3da53651f674a0975394514dfa4d815d23ca6a2094`,
  `validation_passed=false`,
  `source_evidence_failure_count=0`, and
  `missing_source_record_count=0`
- remaining blocker truth:
  the wilderness/designated-area family and the five base-rule current-source
  gaps no longer appear in the missing-template or source-evidence inventory.
  The remaining failing applicability check is now
  `rule_template_candidates_have_source_claim_linkage`
  (`failure_count=48`) because the scoped gate has no
  extraction/retrieval/claim/rule-claim derived artifacts yet and therefore
  records `rule_claim_links_path=null`
- next routing:
  the next truthful slice returns to
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`, beginning with
  the scoped `source-set-f70ea11e04ae3d53` derived-artifact replay chain:
  reuse or rebuild extraction/retrieval as needed, then `claim-extract`, then
  `rule-claim-link`, then rerun `applicability-authority-universe`
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_source_register_loader.py tests/test_dry_run.py tests/test_preflight.py tests/test_catalog.py tests/test_applicability_authority_family_templates.py tests/test_applicability_candidate_assembly.py tests/test_authority_family_rule_templates.py tests/test_authority_universe_inventory.py tests/test_rule_claim_binding_runtime.py tests/test_architecture_contract.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources download --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-current-gap-closeout`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources validate-run --output-dir source_library --run-id queue-m3-full-canonical-merged-download-20260525-current-gap-closeout`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-current-gap-closeout --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --catalog-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json`,
`jq empty config/compliance_source_record_reconciliation_v1.json`,
`git diff --check`

## Active Authority Current-Source Gap Blocker Milestone 2 Vegetation Lane Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the admitted-current replacement class, the governed
  land-exchange retirement sub-slice, the governed `FED-044`
  air/conformity current-source addition, the governed water-family
  current-source additions, the governed cultural-resource/state-SHPO and
  shared tribal-overlap current-source additions, the governed wildlife
  current-source additions, the governed hazardous-material
  current-source addition, the governed
  invasive/farmland/drinking-water current-source additions, the governed
  minerals current-source addition, the governed forest-plan support
  admission lane, and the governed vegetation/fire current-source addition
  lane are now repaired, but the ECID applicability blocker still remains
  open
- implementation truth:
  the canonical workbook now carries `698` retained master rows after adding
  `FED-071` through `FED-077`,
  `config/compliance_source_record_reconciliation_v1.json` now also maps
  `R1EA-056` through `R1EA-062` to those governed current rows, and matching
  regressions now live in `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_catalog.py`,
  `tests/test_dry_run.py`,
  `tests/test_preflight.py`, and
  `tests/test_applicability_authority_family_templates.py`
- live replay truth:
  the reviewer-facing default catalog remains historical
  `source-set-4fb59e9eb43045cb` at `647` source rows, `635` artifacts, and
  `594` admitted `active_review_corpus` rows. The active same-slice replay
  gate now lives at
  `source_library/runs/current-source-gap-vegetation-catalog-gate/catalog_gate`
  as `source-set-e57ea1d39b859bc8` with `698` source rows, `686` artifacts,
  and `645` admitted `active_review_corpus` rows. Because the
  vegetation/fire additions did not change forest-plan source membership, the
  scoped replay carries the existing Region 1 component inventory forward
  under
  `source_library/derived/source-set-e57ea1d39b859bc8/forest_plan_components/component_inventory.json`
  with the inventory ownership rebound to the active source set. On that
  scoped gate,
  `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=c1a89b1e1f9c78d07a2d72f78413f9a3bdbb8668c5b01fded7c8cc19f69febe8`,
  `validation_passed=false`,
  `source_evidence_failure_count=6`, and
  `missing_source_record_count=1`
- remaining blocker truth:
  the land-exchange template, the air/conformity lane, the water-family lane,
  the cultural-resource/state-SHPO lane, the shared tribal-overlap lane, the
  wildlife lane, the hazardous-material lane, the
  invasive/farmland/drinking-water lane, the minerals lane, the
  forest-plan support lane, and the vegetation/fire lane no longer appear in
  the missing-template inventory. The remaining missing-template family is now
  the governed wilderness/designated-area owner group, while the separate `6`
  source-evidence failures still consist of that remaining authority-family
  candidate plus the five base-rule current-source gaps
- next routing:
  the next truthful slice remains Milestone `2` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`,
  beginning with `wilderness_wsr_trails_designated_areas`
  (`R1EA-045`, `R1EA-046`, `R1EA-051`, `R1EA-054`, `R1EA-055`)
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_source_register_loader.py tests/test_dry_run.py tests/test_preflight.py tests/test_catalog.py tests/test_applicability_authority_family_templates.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources download --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-vegetation`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources validate-run --output-dir source_library --run-id queue-m3-full-canonical-merged-download-20260525-vegetation`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-vegetation --catalog-dir source_library/runs/current-source-gap-vegetation-catalog-gate/catalog_gate`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --catalog-path source_library/runs/current-source-gap-vegetation-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-vegetation-catalog-gate/catalog_gate/source_set_manifest.json`,
  `jq empty config/compliance_source_record_reconciliation_v1.json`,
  `git diff --check`

## Active Authority Current-Source Gap Blocker Milestone 2 Forest-Plan Support Lane Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the admitted-current replacement class, the governed
  land-exchange retirement sub-slice, the governed `FED-044`
  air/conformity current-source addition, the governed water-family
  current-source additions, the governed cultural-resource/state-SHPO and
  shared tribal-overlap current-source additions, the governed wildlife
  current-source additions, the governed hazardous-material
  current-source addition, the governed
  invasive/farmland/drinking-water current-source additions, the governed
  minerals current-source addition, and the governed forest-plan support
  admission lane are now repaired, but the ECID applicability blocker still
  remains open
- implementation truth:
  the canonical workbook now carries `691` retained master rows after
  admitting `R1PLAN-region-1-northern-region-02`,
  `R1PLAN-beaverhead-deerlodge-nf-01`,
  `R1PLAN-bitterroot-nf-01`,
  `R1PLAN-custer-gallatin-nf-01`,
  `R1PLAN-dakota-prairie-grasslands-01`,
  `R1PLAN-flathead-nf-01`,
  `R1PLAN-helena-lewis-and-clark-nf-01`,
  `R1PLAN-idaho-panhandle-nfs-01`,
  `R1PLAN-kootenai-nf-01`,
  `R1PLAN-lolo-nf-01`,
  `R1PLAN-nez-perce-clearwater-nfs-01`, and
  `R1PLAN-nez-perce-clearwater-nfs-02`, and matching regressions now live
  in `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_catalog.py`,
  `tests/test_dry_run.py`,
  `tests/test_preflight.py`, and
  `tests/test_applicability_authority_family_templates.py`
- live replay truth:
  the reviewer-facing default catalog remains historical
  `source-set-4fb59e9eb43045cb` at `647` source rows, `635` artifacts, and
  `594` admitted `active_review_corpus` rows. The active same-slice replay
  gate now lives at
  `source_library/runs/current-source-gap-forest-plan-support-catalog-gate/catalog_gate`
  as `source-set-1cbc5bbb602b60bc` with `691` source rows, `679` artifacts,
  and `638` admitted `active_review_corpus` rows. Because the forest-plan
  support admissions only added planning/index pages, the scoped replay
  carries the existing Region 1 component inventory forward under
  `source_library/derived/source-set-1cbc5bbb602b60bc/forest_plan_components/component_inventory.json`
  with the inventory ownership rebound to the active source set. On that
  scoped gate,
  `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=cd7fef2e31ee124d123ec188c8f9555092dc13d5ad14bd0c4fe07d8d8f46c698`,
  `validation_passed=false`,
  `source_evidence_failure_count=7`, and
  `missing_source_record_count=2`
- remaining blocker truth:
  the land-exchange template, the air/conformity lane, the water-family lane,
  the cultural-resource/state-SHPO lane, the shared tribal-overlap lane, the
  wildlife lane, the hazardous-material lane, the
  invasive/farmland/drinking-water lane, the minerals lane, and the
  forest-plan support lane no longer appear in the missing-template
  inventory. The remaining missing-template families are now the governed
  vegetation/fire and wilderness/designated-area owner groups, while the
  separate `7` source-evidence failures still consist of the two remaining
  authority-family candidates plus the five base-rule current-source gaps
- next routing:
  the next truthful slice remains Milestone `2` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`,
  beginning with `vegetation_wildfire_forest_health_authorities`
  (`R1EA-056` through `R1EA-062`)
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_source_register_loader.py tests/test_dry_run.py tests/test_preflight.py tests/test_catalog.py tests/test_applicability_authority_family_templates.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources download --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-forest-plan-support`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources validate-run --output-dir source_library --run-id queue-m3-full-canonical-merged-download-20260525-forest-plan-support`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-forest-plan-support --catalog-dir source_library/runs/current-source-gap-forest-plan-support-catalog-gate/catalog_gate`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --catalog-path source_library/runs/current-source-gap-forest-plan-support-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-forest-plan-support-catalog-gate/catalog_gate/source_set_manifest.json`,
  `jq empty config/compliance_source_record_reconciliation_v1.json`,
  `git diff --check`

## Active Authority Current-Source Gap Blocker Milestone 2 Minerals Lane Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the admitted-current replacement class, the governed
  land-exchange retirement sub-slice, the governed `FED-044`
  air/conformity current-source addition, the governed water-family
  current-source additions, the governed cultural-resource/state-SHPO and
  shared tribal-overlap current-source additions, the governed wildlife
  current-source additions, the governed hazardous-material
  current-source addition, the governed
  invasive/farmland/drinking-water current-source additions, and the governed
  minerals current-source addition are now repaired, but the ECID
  applicability blocker still remains open
- implementation truth:
  the canonical workbook now carries `679` retained master rows after adding
  `FED-070` (`Executive Order 14241 - Immediate Measures To Increase American
  Mineral Production`),
  `config/compliance_source_record_reconciliation_v1.json` now also maps
  `R1EA-063` to that governed current row, and matching regressions now live
  in `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_catalog.py`,
  `tests/test_dry_run.py`,
  `tests/test_preflight.py`, and
  `tests/test_applicability_authority_family_templates.py`
- live replay truth:
  the reviewer-facing default catalog remains historical
  `source-set-4fb59e9eb43045cb` at `647` source rows, `635` artifacts, and
  `594` admitted `active_review_corpus` rows. The active same-slice replay
  gate now lives at
  `source_library/runs/current-source-gap-minerals-catalog-gate/catalog_gate`
  as `source-set-a57779ac966f0bda` with `679` source rows, `667` artifacts,
  and `626` admitted `active_review_corpus` rows. Because the minerals
  addition did not change forest-plan source membership, the scoped replay
  carries the existing Region 1 component inventory forward under
  `source_library/derived/source-set-a57779ac966f0bda/forest_plan_components/component_inventory.json`
  with the inventory ownership rebound to the active source set. On that
  scoped gate,
  `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=5ae1aeab77f1ff775ad4d012c9ae65b2fd70d09b33363922fa535207dc72333e`,
  `validation_passed=false`,
  `source_evidence_failure_count=8`, and
  `missing_source_record_count=3`
- remaining blocker truth:
  the land-exchange template, the air/conformity lane, the water-family lane,
  the cultural-resource/state-SHPO lane, the shared tribal-overlap lane, the
  wildlife lane, the hazardous-material lane, the
  invasive/farmland/drinking-water lane, and the minerals lane no longer
  appear in the missing-template inventory. The remaining missing-template
  families are now the governed forest-plan support, vegetation/fire, and
  wilderness-designated-area owner groups, while the separate `8`
  source-evidence failures still consist of the three remaining
  authority-family candidates plus the five base-rule current-source gaps
- next routing:
  the next truthful slice remains Milestone `2` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`,
  beginning with the governed forest-plan support admissions in
  `region1_forest_plan_source_records`
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_source_register_loader.py tests/test_dry_run.py tests/test_preflight.py tests/test_catalog.py tests/test_applicability_authority_family_templates.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources download --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-minerals`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources validate-run --output-dir source_library --run-id queue-m3-full-canonical-merged-download-20260525-minerals`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-minerals --catalog-dir source_library/runs/current-source-gap-minerals-catalog-gate/catalog_gate`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --catalog-path source_library/runs/current-source-gap-minerals-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-minerals-catalog-gate/catalog_gate/source_set_manifest.json`,
  `jq empty config/compliance_source_record_reconciliation_v1.json`,
  `git diff --check`

## Active Authority Current-Source Gap Blocker Milestone 2 Invasive Lane Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the admitted-current replacement class, the governed
  land-exchange retirement sub-slice, the governed `FED-044`
  air/conformity current-source addition, the governed water-family
  current-source additions, the governed cultural-resource/state-SHPO and
  shared tribal-overlap current-source additions, the governed wildlife
  current-source additions, the governed hazardous-material
  current-source addition, and the governed
  invasive/farmland/drinking-water current-source additions are now repaired,
  but the ECID applicability blocker still remains open
- implementation truth:
  the canonical workbook now carries `678` retained master rows after adding
  `FED-064` through `FED-069`,
  `config/compliance_source_record_reconciliation_v1.json` now also maps
  `R1EA-101`, `R1EA-102`, `R1EA-105`, `R1EA-106`, `R1EA-111`, and
  `R1EA-112` to those governed current rows, and matching regressions now
  live in `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_catalog.py`,
  `tests/test_dry_run.py`,
  `tests/test_preflight.py`, and
  `tests/test_applicability_authority_family_templates.py`
- live replay truth:
  the reviewer-facing default catalog remains historical
  `source-set-4fb59e9eb43045cb` at `647` source rows, `635` artifacts, and
  `594` admitted `active_review_corpus` rows. The active same-slice replay
  gate now lives at
  `source_library/runs/current-source-gap-invasive-catalog-gate/catalog_gate`
  as `source-set-ef887e7bfb6fa76f` with `678` source rows, `666` artifacts,
  and `625` admitted `active_review_corpus` rows. Because the
  invasive/farmland/drinking-water additions did not change forest-plan source
  membership, the scoped replay carries the existing Region 1 component
  inventory forward under
  `source_library/derived/source-set-ef887e7bfb6fa76f/forest_plan_components/component_inventory.json`
  with the inventory ownership rebound to the active source set. On that
  scoped gate,
  `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=7b8fc39075cccf3f98b26fde246c3fb3b14932361797e035accccf895ecd43bb`,
  `validation_passed=false`,
  `source_evidence_failure_count=8`, and
  `missing_source_record_count=4`
- remaining blocker truth:
  the land-exchange template, the air/conformity lane, the water-family lane,
  the cultural-resource/state-SHPO lane, the shared tribal-overlap lane, the
  wildlife lane, the hazardous-material lane, and the
  invasive/farmland/drinking-water lane no longer appear in the
  missing-template inventory. The remaining missing-template families are now
  the governed minerals, forest-plan support, vegetation/fire, and
  wilderness-designated-area owner groups, while the separate `8`
  source-evidence failures still consist of the three remaining
  authority-family candidates plus the five base-rule current-source gaps
- next routing:
  the next truthful slice remains Milestone `2` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`,
  beginning with the governed minerals current-source addition in
  `minerals_energy_authorities` (`R1EA-063`)
- verification:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_source_register_loader.py tests/test_dry_run.py tests/test_preflight.py tests/test_catalog.py tests/test_applicability_authority_family_templates.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src uv run --extra dev ruff check src tests`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources download --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-invasive`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources validate-run --output-dir source_library --run-id queue-m3-full-canonical-merged-download-20260525-invasive`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-invasive --catalog-dir source_library/runs/current-source-gap-invasive-catalog-gate/catalog_gate`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --catalog-path source_library/runs/current-source-gap-invasive-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-invasive-catalog-gate/catalog_gate/source_set_manifest.json`,
  `jq empty config/compliance_source_record_reconciliation_v1.json`,
  `git diff --check`

## Active Authority Current-Source Gap Blocker Milestone 2 Hazardous Lane Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the admitted-current replacement class, the governed
  land-exchange retirement sub-slice, the governed `FED-044`
  air/conformity current-source addition, the governed water-family
  current-source additions, the governed cultural-resource/state-SHPO and
  shared tribal-overlap current-source additions, the governed wildlife
  current-source additions, and the governed hazardous-material
  current-source addition are now repaired, but the ECID applicability
  blocker still remains open
- implementation truth:
  the canonical workbook now carries `672` retained master rows after adding
  `FED-063` (`National Contingency Plan, 40 CFR part 300`),
  `config/compliance_source_record_reconciliation_v1.json` now also maps
  `R1EA-109` to that governed current row, and matching regressions now live in
  `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_catalog.py`,
  `tests/test_dry_run.py`,
  `tests/test_preflight.py`, and
  `tests/test_applicability_authority_family_templates.py`
- live replay truth:
  the reviewer-facing default catalog remains historical
  `source-set-4fb59e9eb43045cb` at `647` source rows, `635` artifacts, and
  `594` admitted `active_review_corpus` rows. The active same-slice replay
  gate now lives at
  `source_library/runs/current-source-gap-hazardous-catalog-gate/catalog_gate`
  as `source-set-87f6d2c309e0c88b` with `672` source rows, `660` artifacts,
  and `619` admitted `active_review_corpus` rows. Because the hazardous
  addition did not change forest-plan source membership, the scoped replay
  carries the existing Region 1 component inventory forward under
  `source_library/derived/source-set-87f6d2c309e0c88b/forest_plan_components/component_inventory.json`.
  On that scoped gate,
  `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=588d3abc81e0e4129943d5ed0087f2cb268844d4f062ddde70b5fccad194b33e`,
  `validation_passed=false`,
  `source_evidence_failure_count=8`, and
  `missing_source_record_count=5`
- remaining blocker truth:
  the land-exchange template, the air/conformity lane, the water-family lane,
  the cultural-resource/state-SHPO lane, the shared tribal-overlap lane, the
  wildlife lane, and the hazardous-material lane no longer appear in the
  missing-template inventory. The remaining missing-template families are now
  the governed invasive/farmland/drinking-water, minerals, forest-plan
  support, vegetation/fire, and wilderness-designated-area owner groups,
  while the separate `8` source-evidence failures now consist of the three
  remaining authority-family candidates plus the five base-rule current-source
  gaps
- next routing:
  the next truthful slice remains Milestone `2` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`,
  beginning with the governed invasive/farmland/drinking-water
  current-source additions in
  `invasive_pesticide_soils_farmland_drinking_water`
  (`R1EA-101`, `R1EA-102`, `R1EA-105`, `R1EA-106`, `R1EA-111`, `R1EA-112`)
- verification:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_catalog.py tests/test_dry_run.py tests/test_preflight.py tests/test_applicability_authority_family_templates.py tests/test_authority_family_rule_templates.py tests/test_authority_universe_inventory.py tests/test_rule_claim_binding_runtime.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m ruff check tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_catalog.py tests/test_dry_run.py tests/test_preflight.py tests/test_applicability_authority_family_templates.py tests/test_authority_family_rule_templates.py tests/test_authority_universe_inventory.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources download --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-hazardous`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-hazardous --catalog-dir source_library/runs/current-source-gap-hazardous-catalog-gate/catalog_gate`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --catalog-path source_library/runs/current-source-gap-hazardous-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-hazardous-catalog-gate/catalog_gate/source_set_manifest.json`,
  `jq empty config/compliance_source_record_reconciliation_v1.json`,
  `git diff --check`

## Historical Current-Source Gap Milestone 2 Retirement Checkpoint

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the admitted-current replacement class plus the governed
  land-exchange retirement sub-slice are now repaired, but the ECID
  applicability blocker still remains open
- implementation truth:
  the governed land-exchange retirement closeout now lives in
  `config/authority_family_rule_templates_nepa_ea_v1.json`,
  `config/compliance_rule_pack_nepa_ea_v0.json`,
  `config/authority_family_rule_template_coverage_nepa_ea_v1.json`, and
  `config/authority_universe_families_nepa_ea_v1.json`; `R1EA-160`,
  `R1EA-161`, and `R1EA-162` now remain mapped only as excluded
  non-controlling project-reference rows while the active family contract
  stays on the current directive/support rows. Matching regressions now live
  in `tests/test_applicability_authority_family_templates.py`,
  `tests/test_authority_family_rule_templates.py`, and
  `tests/test_authority_universe_inventory.py`
- live replay truth:
  `applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=fbadccedec1ae953ba751dfe95e73f43e6e44731141f06b291cd7294e68afdfd`,
  `validation_passed=false`,
  `source_evidence_failure_count=11`, and
  `missing_source_record_count=11`
- remaining blocker truth:
  the land-exchange template no longer appears in the missing-template
  inventory; the remaining missing-template families are now only true
  current-source additions or forest-plan support admissions, while the
  separate `11` source-evidence failures still consist of the six remaining
  authority-family candidates plus the five base-rule current-source gaps
- historical next routing at that retirement checkpoint:
  the next truthful slice remains Milestone `2` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`,
  continuing with the true current-source addition and forest-plan support
  owner classes now that the governed `R1EA-160` / `R1EA-161` / `R1EA-162`
  retirement closeout is done
- verification:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_applicability_authority_family_templates.py tests/test_authority_family_rule_templates.py tests/test_authority_universe_inventory.py tests/test_rule_claim_binding_runtime.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check tests/test_applicability_authority_family_templates.py tests/test_authority_family_rule_templates.py tests/test_authority_universe_inventory.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`,
  `jq empty config/authority_family_rule_templates_nepa_ea_v1.json config/compliance_rule_pack_nepa_ea_v0.json config/authority_family_rule_template_coverage_nepa_ea_v1.json config/authority_universe_families_nepa_ea_v1.json`,
  `git diff --check`

## Active Authority Current-Source Gap Blocker Milestone 1 Resolved Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the remaining stale current-source IDs now have one
  governed owner map before any repair lands
- owner map truth:
  template retire/replace work in
  `config/authority_family_rule_templates_nepa_ea_v1.json` now owns
  `R1EA-038`, `R1EA-043`, `R1EA-068`, `R1EA-125` through `R1EA-149`,
  `R1EA-151` through `R1EA-156`, and explicit retirement of
  `R1EA-160` through `R1EA-162`; governed current-source additions now own
  the remaining air, water, cultural, wildlife, hazardous-material,
  invasive/farmland/drinking-water, wildfire/minerals, and
  designated-areas rows; forest-plan support admission now owns the remaining
  `R1PLAN-*` support rows; and
  `config/compliance_rule_pack_nepa_ea_v0.json` now stays the owner for the
  five base-rule current-source decisions
- live replay truth:
  `applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`
  remains unchanged at `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=2f99cee2bf5bdbb148cc4b97b5c8d00d370baf9e1a8cb72e623a99226534dc22`,
  `validation_passed=false`,
  `source_evidence_failure_count=11`, and
  `missing_source_record_count=17`
- historical next routing at that owner-map checkpoint:
  Milestone `2` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
  owned the governed source-truth, template, forest-plan, and rule-pack
  repair work itself; the live route after the later Milestone `2` reduction
  is recorded in the newer section above
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`,
  `git diff --check`

## Active Authority Current-Source Gap Blocker Milestone 0 Resolved Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the post-binding ECID applicability residue is now
  frozen as a separate current-source truth packet before any workbook or
  template retirement/addition work begins
- baseline truth:
  `applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`
  now reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=2f99cee2bf5bdbb148cc4b97b5c8d00d370baf9e1a8cb72e623a99226534dc22`,
  `validation_passed=false`,
  `source_evidence_failure_count=11`, and
  `missing_source_record_count=17`
- current-source gap truth:
  the exact-match binding lane is now exhausted; a local audit across
  `source_library/manifests/*.jsonl` and
  `source_library/catalog/source_catalog.jsonl` returns no untouched exact
  current-catalog URL matches for the remaining missing IDs, so the live
  blocker is now governed workbook/template/rule-pack current-source debt
- historical next routing at that baseline-freeze checkpoint:
  the next truthful slice was Milestone `1` of
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`; the
  live route after the Milestone `1` owner-map closeout is recorded in the
  newer section above
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`,
  `git diff --check`

## Active Authority Source Binding Blocker Milestone 2 Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the governed binding layer now covers the exact current
  rows already present in the active catalog, but the ECID applicability
  universe still stops on a smaller remaining current-source truth blocker
- binding repair truth:
  `src/usfs_r1_ea_sources/records.py` now reuses the committed forest-plan
  identity registry snapshot while building shared alias sets, and
  `config/compliance_source_record_reconciliation_v1.json` now binds the
  exact current catalog rows already present for the remaining
  reconciliation-owned ECID authorities and Region 1 overlay support rows
- reduced blocker truth:
  the live replay is now reduced from `21` source-evidence failures and `19`
  missing source-record template groups to `11` and `17`; the remaining
  blocker is no longer principally a source-binding problem
- historical next routing at that binding-repair reduction checkpoint:
  the next truthful slice was no longer Milestone `3` in this packet; the
  route then moved to
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`. The
  live route after the Milestone `1` owner-map closeout is recorded in the
  newer section above
- verification:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_applicability_authority_family_templates.py tests/test_applicability_candidate_assembly.py tests/test_applicability.py tests/test_applicability_authority_universe_contracts.py tests/test_applicability_authority_universe_builder.py tests/test_rule_claim_binding_runtime.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/records.py src/usfs_r1_ea_sources/applicability_contract_support.py tests/test_applicability_authority_family_templates.py`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`,
  `jq empty config/compliance_source_record_reconciliation_v1.json`,
  `git diff --check`

## Active Authority Source Binding Blocker Milestone 1 Resolved Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the frozen ECID authority-source blocker inventory now
  has a governed owner map before any repair begins
- owner map truth:
  the live `21` source-evidence candidate failures and `19` missing
  source-record template groups now split into three repair owners:
  `16` template families are reconciliation-owned in
  `config/compliance_source_record_reconciliation_v1.json`,
  `3` `R1PLAN-*`-dependent template families
  (`grassland_bankhead_jones_authorities`,
  `region1_forest_plan_source_records`,
  `species_supporting_sources_and_overlays`) are forest-plan identity rebind
  work across reconciliation plus template config, and the `5` base rule rows
  (`apa_final_agency_action`,
  `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`,
  `organic_act_16usc_475`,
  `seven_county_nepa_scope`) remain true current-source gaps with explicit
  empty reconciliation entries
- evidence boundary:
  the reconciliation-owned families already have current active-row evidence in
  the catalog under current IDs such as `FED-023`, `FED-022`, `FED-024`,
  `FED-042`, `FED-036`, `USFS-033`, `USFS-034`, `R1-030`, `STP-026`,
  `LEX-USFS-002`, `LEX-USFS-012`, `LEX-FED-003`, and `USFS-035`; the
  forest-plan identity owner still depends on rebinding stale `R1PLAN-*`
  overlays/support rows to the active `FOR-*`, `FINAL-*`, `FPS-*`, and
  `R1-*` plan-supporting corpus; and the five rule rows still have no current
  canonical row in the active catalog
- historical next routing at this Milestone `1` owner-map checkpoint:
  the next truthful slice was Milestone `2` of
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`; the live
  route after the Milestone `2` reduction is recorded in the newer sections
  above
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`,
  `git diff --check`

## Active Authority Source Binding Blocker Milestone 0 Resolved Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the active-source authority binding blocker is now
  frozen as a concrete baseline on the active source set before any governed
  repair begins
- baseline truth:
  `applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`
  still reports `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `selected_component_forest_unit_ids=["custer-gallatin-nf"]`, and
  `validation_passed=false`
- blocker split:
  the repaired routing bugs stay retired as blockers:
  `forest_plan_component_candidates_use_profile_inventory` now passes on the
  ECID review forest, and governed legacy source-ID reconciliation still
  covers active aliases such as `R1EA-150`; the live blocker inventory is now
  frozen as `21` failing `candidates_have_source_evidence_available`
  candidates (`16` authority-family templates plus `5` rule templates) and
  `19` failing `authority_family_template_candidates_cover_config`
  family-template groups, including Region 1 forest-plan/species overlays and
  the land-exchange-only `R1EA-125` through `R1EA-162` family
- historical next routing at this baseline-freeze checkpoint:
  the next truthful slice was Milestone `1` of
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`; the live
  route after the Milestone `1` owner-map closeout is recorded in the newer
  section above
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`,
  `git diff --check`

## Real Package Review Replay Repair Milestone 1 Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; ECID applicability replay now gets past the old mixed
  inventory and legacy source-ID routing bugs, but the reviewer-ready slot
  still cannot resume because the active applicability universe now stops on a
  smaller governed authority-source binding blocker
- applicability universe truth:
  `applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`
  now rebuilds `candidate_authority_count=396` with
  `forest_plan_component_candidate_count=329`,
  `selected_component_forest_unit_ids=["custer-gallatin-nf"]`, and
  `validation_passed=false`
- remaining blocker truth:
  the only failing authority-universe checks are now
  `candidates_have_source_evidence_available` with `failure_count=21` and
  `authority_family_template_candidates_cover_config` with
  `missing_source_record_count=19`; existing governed reconciliation already
  covers examples such as `R1EA-150`, but active-source binding gaps remain
  for families that still reference records such as `R1EA-092`, `R1EA-032`,
  `R1EA-037`, `R1EA-041`, `R1PLAN-custer-gallatin-nf-06`, and
  `R1PLAN-region-1-species-overlay-01`
- historical next routing at this replay-repair reduction checkpoint:
  the next truthful slice was Milestone `0` of
  `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`; the live
  route after the blocker Milestones `0-1` closeouts is recorded in the newer
  section above
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --source-set-id source-set-4fb59e9eb43045cb`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_applicability_candidate_assembly.py tests/test_applicability.py tests/test_applicability_authority_family_templates.py tests/test_applicability_authority_universe_contracts.py tests/test_applicability_authority_universe_builder.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/applicability_contract_support.py src/usfs_r1_ea_sources/applicability_candidate_assembly.py src/usfs_r1_ea_sources/applicability_authority_family_templates.py src/usfs_r1_ea_sources/applicability_authority_universe_builder.py src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py tests/test_applicability_candidate_assembly.py tests/test_applicability.py tests/test_applicability_authority_family_templates.py`

## Real Package Review Replay Repair Milestone 0 Reduced Locally

Latest implementation update on 2026-05-25:

- routed packet:
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the packet now carries a fresh replay baseline over the
  active `source-set-4fb59e9eb43045cb` truth before ECID or South Plateau
  repair begins
- aggregate coverage truth:
  `real-package-review-coverage-eval` now reports `passed=false`,
  `reviewer_ready_slot_count=0`,
  `missing_coverage_class_ids=["current_promotion_reviewer_ready","expansion_reviewer_ready"]`,
  and reviewer-ready slot mismatches for both ECID current promotion and South
  Plateau reviewer-ready expansion while West Reservoir still truthfully passes
  as `typed_blocked`
- current-promotion selector truth:
  non-strict `promotion-suite` still reports
  `current_promotion_ready=false`,
  `promotion_ready=false`, and `expansion_ready=false`, but the
  current-promotion contract now fails at the selector layer with
  `selector_passed=false`, `matched_slot_count=0`,
  `eligible_slot_count=0`, `passing_slot_count=0`,
  `quorum_passed=false`, and `reference_canary_ready=false`
- owner-command truth:
  Milestone `0` now records the concrete repair entrypoints for the failing
  families: `phase-eval`, `compliance-review-eval`, `v1-ea-eval`,
  `review-packet-index`, `ea-consistency-document`,
  `final-qa-certification`, ECID/South Plateau replay-context-backed
  `compliance-review`, and the ECID review overlay
  `nepa-knowledge-graph-export`
- historical next routing at this replay baseline checkpoint:
  the next truthful slice was Milestone `1` ECID reviewer-ready replay repair
  inside `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`; that
  route was later reduced and then handed off to the authority-source blocker
  packet recorded above
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  `git diff --check`

## Promotion Suite Slot-Driven Contract Milestone 4 Resolved Locally

Latest implementation update on 2026-05-24:

- routed packet:
  `docs/PROMOTION_SUITE_SLOT_DRIVEN_CONTRACT_MILESTONE_PLAN.md`
- packet outcome:
  `resolved locally`; the aggregate promotion contract now keeps slot-driven
  freshness/status truth in the shared manifest, packet-local ECID counts stay
  owned by focused validators and tests, and the live replay proves the
  remaining red is review-local replay debt rather than contract drift
- replay truth:
  `real-package-review-coverage-eval` now reports `passed=false`,
  `reviewer_ready_slot_count=0`, and reviewer-ready slot mismatches for ECID
  current promotion plus South Plateau reviewer-ready expansion, while West
  Reservoir still truthfully passes as `typed_blocked`
- historical aggregate readiness truth at 2026-05-24 closeout:
  non-strict `promotion-suite` now reports
  `full_canonical_corpus_ready=true`,
  `passed_required_full_canonical_result_count=10/10`,
  `current_promotion_ready=false`, `promotion_ready=false`,
  and `expansion_ready=false`; inside the slot-driven contract,
  `current_promotion_contract.selector_passed=true` but
  `current_promotion_contract.quorum_passed=false` at
  `eligible_slot_count=1` and `passing_slot_count=0`, and the ECID reference
  canary stays red because its packet-local artifact family is stale
- runtime-owner truth:
  the focused `src/usfs_r1_ea_sources/promotion_suite_current.py` owner now
  resolves governed slots, same-slot family pass state, source-set binding,
  quorum checks, and separate canary status; `promotion_suite_results.json`
  remains schema version `promotion-suite-results-v1`
- next routing:
  the active follow-on is now
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`, which owns the
  ECID and South Plateau review-local replay repair lane on
  `source-set-4fb59e9eb43045cb`
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources real-package-review-coverage-eval --output-dir source_library --manifest config/v1_real_package_review_coverage_v1.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_promotion_suite.py tests/test_promotion_suite_full_canonical.py tests/test_ea_consistency_decision_support.py tests/test_final_qa_certification.py tests/test_phase_eval.py tests/test_cli_eval.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m compileall src`,
  `jq empty config/promotion_suite_v1.json config/v1_real_package_review_coverage_v1.json`,
  `git diff --check`

Routing note: this section is a historical 2026-05-24 contract closeout
snapshot. The current live selector truth is the 2026-05-25 replay-repair
baseline recorded in `Real Package Review Replay Repair Milestone 0 Reduced
Locally` above.

## Lolo Tyler's Kitchen Packet Reduced Locally

Latest implementation update on 2026-05-24:

- routed packet:
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- packet outcome:
  `reduced locally`; the root Tyler's Kitchen package authority, replay
  context, `FOR-029` queue reroute, packet-local Lolo review contracts, and
  Lolo forest-plan component coverage are now tracked, but the packet stops
  before registry promotion because the inherited review-scoped `phase-eval`
  gate stays red against the active `source-set-4fb59e9eb43045cb` contract
- queue and registry truth:
  `FOR-029` now routes to
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` as an explicit
  `blocked` `named_blocker` row; `source-register-queue-audit` now passes
  with `resolution_status_counts={"blocked":10,"planned":33,"resolved":8}`,
  `blocked_current_or_project_applicable_count=10`,
  `unresolved_current_or_project_applicable_count=31`, and the same governed
  historical rows `FPS-380` and `SUP-007`; `lolo-nf` still remains
  `profile_eval_guidance_only` in
  `config/forest_specific_example_package_registry_v1.json`, but the row now
  carries `queue_boundary_source_ids=["FOR-029"]` plus the active packet
  guidance note
- packet-local review truth:
  `v1-ea-eval` for
  `region1-example-lolo-tylers-kitchen-66344` now passes with
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`, and
  `forest_plan_passed=true`; the tracked Lolo forest-plan component eval also
  passes with `case_count=1`; and
  `forest-plan-component-eval-coverage` now passes with
  `required_review_count=4`, `covered_review_count=4`, and
  `distinct_forest_count=3`
- inherited blocker truth:
  review-scoped `phase-eval` for
  `region1-example-lolo-tylers-kitchen-66344` remains red with
  `passed=false`, `reviewer_ready=false`,
  `missing_direct_eval_phase_count=1`, and
  `threshold_failed_phase_count=1`; the blocking reasons are missing direct
  extraction eval coverage plus retrieval direct-eval threshold failures, so
  promotion into `config/v1_real_package_review_coverage_v1.json` and the
  forest-specific example registry remains deferred
- aggregate lane truth:
  `real-package-review-coverage-eval` stays green at the pre-Lolo `3`-slot
  reviewer-ready/typed-blocked boundary, and
  `forest-specific-example-package-eval` also stays green at
  `review_example_count=3`, `reviewer_ready_example_count=2`,
  `typed_blocked_example_count=1`, and `profile_guidance_only_count=8`

Routing note: older references below that still describe the Lolo packet as
queued-only, still report queue counts
`resolution_status_counts={"blocked":9,"planned":34,"resolved":8}`, or still
imply `lolo-nf` is next for immediate reviewer-ready promotion are historical
after the 2026-05-24 Lolo reduced closeout described above.

## Forest Specific Example Package Boundary Opened Locally

Latest implementation update on 2026-05-23:

- routed packet:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- boundary outcome:
  the repo now carries a tracked parallel example-package lane instead of
  treating East Crazy as pending master-promotion work
- new tracked contract:
  `config/forest_specific_example_package_registry_v1.json` now covers all
  `10` Region 1 forest units, tracks `3` governed example reviews
  (`2 reviewer_ready`, `1 typed_blocked`), maps each example to
  `applicable_to_forest_unit_ids`, and keeps the remaining `8` forests on
  `profile_eval_guidance_only`
- queue truth:
  `FOR-012` and `LEX-Q-001` now route to
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md` as
  explicit `blocked` `named_blocker` rows; `source-register-queue-audit` now
  passes with `resolution_status_counts={"blocked":9,"planned":34,"resolved":8}`,
  `blocked_current_or_project_applicable_count=9`,
  `unresolved_current_or_project_applicable_count=32`, and governed
  historical rows `FPS-380` and `SUP-007`
- master/catalog boundary:
  the active full-canonical catalog remains
  `source-set-4fb59e9eb43045cb` with `source_count=647`,
  `artifact_count=635`,
  `source_partition_counts={"active_review_corpus":594,"currentness_supersession_archive":53}`,
  and `status_counts={"downloaded_existing":635,"duplicate_content":12}`;
  this slice changes queue governance and agent-routing surfaces only and does
  not change `Document_Register_Master`, extraction, retrieval, or downstream
  promotion results
- next routing:
  the forest-specific example packet is now the active per-forest guidance
  lane, while
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  continues on the remaining planned direct-file roster outside East Crazy
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_forest_specific_example_package_registry.py tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check tests/test_forest_specific_example_package_registry.py tests/test_source_register_queue_resolution.py`,
  and `git diff --check`

## Forest Specific Example Package Coverage Eval Added Locally

Latest implementation update on 2026-05-23:

- routed packet:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- boundary outcome:
  the parallel forest-specific example lane now has its own fail-closed
  aggregate eval instead of relying only on indirect registry and shared-lane
  checks
- new aggregate owner:
  `src/usfs_r1_ea_sources/forest_specific_example_package_eval.py` and
  `forest-specific-example-package-eval`
- live eval truth:
  `source_library/reviews/forest_specific_example_package_eval/forest_specific_example_package_eval_results.json`
  now passes with `forest_unit_count=10`, `covered_forest_count=10`,
  `failed_forest_count=0`, `review_example_count=3`,
  `2 reviewer_ready + 1 typed_blocked` governed examples,
  `distinct_governed_example_forest_count=2`, and
  `profile_guidance_only_count=8`
- routing truth:
  declared and actual routing counts both now stay
  `{"profile_eval_guidance_only":8,"real_package_examples_available":1,"typed_blocked_example_available":1}`
  with zero threshold failures and zero aggregate failure categories
- master/catalog boundary:
  this slice does not change `Document_Register_Master`, queue counts, the
  active catalog, or downstream promotion truth; it raises governance on the
  parallel example lane only
- next routing:
  the first concrete follow-on is now
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`, which aims to
  move `lolo-nf` off `profile_eval_guidance_only` by governing the
  `Tyler's Kitchen Fuels Reduction and Forest Health Project (66344)` package
  as a parallel example package and rerouting `FOR-029` out of
  master-promotion semantics; Flathead still lacks a reviewer-ready benchmark
  and the remaining non-Lolo forests still stay on governed
  `profile_eval_guidance_only`
- verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-specific-example-package-eval --output-dir source_library`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_forest_specific_example_package_eval.py tests/test_forest_specific_example_package_registry.py tests/test_cli_eval.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/forest_specific_example_package_eval.py tests/test_forest_specific_example_package_eval.py tests/test_forest_specific_example_package_registry.py tests/test_cli_eval.py`,
  and `git diff --check`

Routing note: the newest forest-plan identity-reconciliation closeout, full-canonical final-blocker closeout,
downstream-freshness reduced closeout, import-completion closeout,
operational-recovery, and gold-coverage sections below supersede older
historical lane notes when they disagree. In particular,
older references below that still treat `source-set-5e65d845ce77e1a0`,
`source-set-9dcf819bc4cca486`, or the planned Phase 2 gate
`source-set-ae989382c52344db` as the active local import catalog are
historical only after the 2026-05-19 import-completion closeout, unless a
later milestone explicitly reruns those lanes. For the full-canonical live
promotion lane specifically, references below that still treat
`source-set-9e7d85759951c279` as the active follow-on target, still route
Milestone 4 as pending, or still describe archived
`source-set-732a5a91d31736f8` as the governing live downstream contract are
historical only after the 2026-05-20 live-promotion Milestone 4 docs-only
sole-truth closeout `f464fa9` on `source-set-f775524ab233ff27`. Older
references below that still treat Applicability-First Milestone 10 as open,
still describe South Plateau strict expansion as blocked on
`forest_plan_reviewer_not_ready`, or still claim a fresh rerun of the
aggregate real-package coverage gate is green without the preserved West
Reservoir package authority are historical only after the 2026-05-20
Applicability-First Milestone 10 closeout and alignment described below.
Older architecture references below that still route the oversized-test packet
as open or still list pre-closeout Milestone 8 hotspot sizes such as
`tests/test_phase_eval.py=954` are historical only after the 2026-05-21
Milestone 8 alignment closeout described below. Older references below that
still treat West Reservoir as reviewer-ready or still report aggregate
real-package and gold coverage with `3` reviewer-ready tracked reviews and `0`
typed-blocked reviews are historical only after the 2026-05-21 Milestone 9
Sequence 51 quarantine closeout described below. Older references below that
still route the overall architecture umbrella as open or still claim a fresh
full-canonical bounded gold aggregate is green are historical only after the
2026-05-21 Milestone 10 Sequence 52 rebaseline closeout described below.
Older architecture references below that still route the under-`800` hotspot
packet as pending on Milestone `7` or still report the pre-closeout
compliance/eval baseline of `445` code files and `4` files above `800` are
historical only after the 2026-05-21 Under-800 Hotspot Reduction Milestone
`7` closeout described below.
Older architecture references below that still route the under-`800` hotspot
packet as pending on Milestone `8` or still report the pre-closeout
viewer baseline of `454` code files and `1` file above `800` are historical
only after the 2026-05-21 Under-800 Hotspot Reduction Milestone `8` closeout
described below.
Older architecture references below that still route the under-`800` hotspot
packet as pending on Milestone `9` or still describe the packet as queued
active debt are historical only after the 2026-05-21 Under-800 Hotspot
Reduction Milestone `9` closeout described below.
Older architecture references below that still route the under-`800` hotspot
packet as pending on Milestone `6` or still report the pre-closeout
capture/catalog/source-register baseline of `437` code files and `10` files
above `800` are historical only after the 2026-05-21 Under-800 Hotspot
Reduction Milestone `6` closeout described below. Older references below that still
treat the live
full-canonical gold replay as
the earlier `14/14` rule/retrieval failure bundle or as a pre-scored
applicability abort are historical only after the 2026-05-21 generated-case
routing repair, owner-family split, diagnostic generated-pack slice, and
legacy/current source-record reconciliation slice
described below.
Older references below that still route the full-canonical source-truth packet
as pending on Milestone `3`, still report `582/52` as the live active/archive
split, or still treat the archive-lineage decision as open are historical only
after the 2026-05-23 source-truth archive-boundary closeout described below.
Older references below that still route the downstream compliance-gold packet
as active, still report fresh full-canonical gold or aggregate gold replays
as red, or still describe the current-promotion lane as red only on
downstream gold adjudication are historical only after the 2026-05-23
downstream gold closeout described below.
Older references below that still treat `source-set-3f7d4578cafb0704`,
`585/585` admitted rows, or
`resolution_status_counts={"blocked":3,"planned":44,"resolved":4}` as the
live full-canonical or queue truth are historical only after the 2026-05-23
SCC structured-export slice described below.
Older references below that still report
`resolution_status_counts={"blocked":3,"planned":40,"resolved":8}` or treat
`FINAL-Q-FLAT-001` as a generic planned structured-export row are historical
only after the 2026-05-23 Flathead reading-room blocker opener described
below.
Older references below that still report
`resolution_status_counts={"blocked":4,"planned":39,"resolved":8}` or still
route `WILD-ESA-Q001` as a generic planned export family are historical only
after the 2026-05-23 NCDE amendment export blocker opener described below.
Older references below that still report
`resolution_status_counts={"blocked":5,"planned":38,"resolved":8}` or still
route `FINAL-Q-LOLO-001` as a generic planned export family are historical
only after the 2026-05-23 Lolo Pinyon blocker opener described below.
Older references below that still report
`resolution_status_counts={"blocked":6,"planned":37,"resolved":8}` or still
route `FINAL-Q-NPC-001` as a generic planned export family are historical only
after the 2026-05-23 NPC planning-record blocker opener described below.

## Full Canonical Direct-File Queue Milestone 3 NPC Planning Record Blocker Reduced Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced locally` for Milestone `3`; `FINAL-Q-NPC-001` is now an explicit
  mixed planning-record blocker family, the earlier SCC, Flathead, NCDE, and
  Lolo slices remain resolved/reduced, and the next routed slice stays on the
  remaining generic export-backed family.
- Workbook and queue truth:
  `source-register-diff` remains unchanged at
  `canonical_master_row_count=647`, `canonical_only_source_count=647`,
  `canonical_queue_row_count=51`, and workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`;
  `source-register-queue-audit` now passes with
  `resolution_status_counts={"blocked":7,"planned":36,"resolved":8}`,
  `resolved_current_or_project_applicable_count=8`,
  `blocked_current_or_project_applicable_count=7`,
  `unresolved_current_or_project_applicable_count=34`, and the same governed
  historical/noncurrent rows (`FPS-380`, `SUP-007`).
- New blocker family:
  `FINAL-Q-NPC-001` now routes to
  `docs/NEZ_PERCE_CLEARWATER_PLANNING_RECORD_BLOCKER_MILESTONE_PLAN.md`
  because the live public Box share is a multi-page NPC planning-record
  library whose visible top-level folders already mix core plan documents with
  high-volume FEIS-reference, objection-reference, consultation, amendment,
  infrastructure, and misc-support surfaces.
- Closeout commit:
  `2625aa2` (`Open NPC planning-record blocker packet`).
- Active full-canonical catalog truth:
  the live source set remains `source-set-4fb59e9eb43045cb` with
  `source_count=647`, `artifact_count=635`,
  `source_partition_counts={"active_review_corpus":594,"currentness_supersession_archive":53}`,
  `status_counts={"downloaded_existing":635,"duplicate_content":12}`, and the
  same strengthened extraction, currentness, and retrieval truth already
  described below; this blocker opener changes queue governance only and does
  not change the catalog or downstream derived artifacts.
- Next routing:
  stay on Milestone `3` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for the remaining export-backed family `LEX-Q-001`. The active blocker
  packets are now
  `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`,
  `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md`,
  `docs/NEZ_PERCE_CLEARWATER_PLANNING_RECORD_BLOCKER_MILESTONE_PLAN.md`, and
  `docs/PROJECT_SPECIFIC_PUBLIC_PRIVATE_SOURCE_BOUNDARY_BLOCKER_MILESTONE_PLAN.md`.
- Verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check tests/test_source_register_queue_resolution.py`,
  and `git diff --check`.

## Full Canonical Direct-File Queue Milestone 3 Lolo Pinyon Blocker Reduced Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced locally` for Milestone `3`; `FINAL-Q-LOLO-001` is now an explicit
  mixed planning-library blocker family, the earlier SCC, Flathead, and NCDE
  slices remain resolved/reduced, and the next routed slice stays on the
  remaining generic export-backed families.
- Workbook and queue truth:
  `source-register-diff` remains unchanged at
  `canonical_master_row_count=647`, `canonical_only_source_count=647`,
  `canonical_queue_row_count=51`, and workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`;
  `source-register-queue-audit` now passes with
  `resolution_status_counts={"blocked":6,"planned":37,"resolved":8}`,
  `resolved_current_or_project_applicable_count=8`,
  `blocked_current_or_project_applicable_count=6`,
  `unresolved_current_or_project_applicable_count=35`, and the same governed
  historical/noncurrent rows (`FPS-380`, `SUP-007`).
- New blocker family:
  `FINAL-Q-LOLO-001` now routes to
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md` because the live
  public root folder is a 14-section planning library that overlaps existing
  Lolo plan and SCC rows while also carrying broader assessment, legal-notice,
  geospatial, and topical support surfaces.
- Closeout commit:
  `2d7d7c2` (`Open Lolo Pinyon blocker packet`).
- Active full-canonical catalog truth:
  the live source set remains `source-set-4fb59e9eb43045cb` with
  `source_count=647`, `artifact_count=635`,
  `source_partition_counts={"active_review_corpus":594,"currentness_supersession_archive":53}`,
  `status_counts={"downloaded_existing":635,"duplicate_content":12}`, and the
  same strengthened extraction, currentness, and retrieval truth already
  described below; this blocker opener changes queue governance only and does
  not change the catalog or downstream derived artifacts.
- Next routing:
  stay on Milestone `3` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for the remaining export-backed families `FINAL-Q-NPC-001` and `LEX-Q-001`.
  The active blocker packets are now
  `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`,
  `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_PINYON_FILE_SET_BLOCKER_MILESTONE_PLAN.md`, and
  `docs/PROJECT_SPECIFIC_PUBLIC_PRIVATE_SOURCE_BOUNDARY_BLOCKER_MILESTONE_PLAN.md`.
- Verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check tests/test_source_register_queue_resolution.py`,
  and `git diff --check`.

## Full Canonical Direct-File Queue Milestone 3 NCDE Amendment Export Blocker Reduced Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced locally` for Milestone `3`; `WILD-ESA-Q001` is now an explicit
  mixed export blocker family, the earlier SCC and Flathead slices remain
  resolved/reduced, and the next routed slice stays on the remaining generic
  export-backed families.
- Workbook and queue truth:
  `source-register-diff` remains unchanged at
  `canonical_master_row_count=647`, `canonical_only_source_count=647`,
  `canonical_queue_row_count=51`, and workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`;
  `source-register-queue-audit` now passes with
  `resolution_status_counts={"blocked":5,"planned":38,"resolved":8}`,
  `resolved_current_or_project_applicable_count=8`,
  `blocked_current_or_project_applicable_count=5`,
  `unresolved_current_or_project_applicable_count=36`, and the same governed
  historical/noncurrent rows (`FPS-380`, `SUP-007`).
- New blocker family:
  `WILD-ESA-Q001` now routes to
  `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`
  because the live public Pinyon/Box roster mixes overlapping Flathead plan,
  ROD, and FEIS documents with distinct multi-forest NCDE amendment records
  and still-missing Flathead map appendices.
- Active full-canonical catalog truth:
  the live source set remains `source-set-4fb59e9eb43045cb` with
  `source_count=647`, `artifact_count=635`,
  `source_partition_counts={"active_review_corpus":594,"currentness_supersession_archive":53}`,
  `status_counts={"downloaded_existing":635,"duplicate_content":12}`, and the
  same strengthened extraction, currentness, and retrieval truth already
  described below; this blocker opener changes queue governance only and does
  not change the catalog or downstream derived artifacts.
- Next routing:
  stay on Milestone `3` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for the remaining export-backed families `FINAL-Q-LOLO-001`,
  `FINAL-Q-NPC-001`, and `LEX-Q-001`. The active blocker packets are now
  `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`,
  `docs/NCDE_GRIZZLY_BEAR_AMENDMENT_EXPORT_BLOCKER_MILESTONE_PLAN.md`, and
  `docs/PROJECT_SPECIFIC_PUBLIC_PRIVATE_SOURCE_BOUNDARY_BLOCKER_MILESTONE_PLAN.md`.
- Closeout commit:
  `3a8dd2d` (`Open WILD-ESA NCDE blocker packet`).
- Verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check tests/test_source_register_queue_resolution.py`,
  and `git diff --check`.

## Full Canonical Direct-File Queue Milestone 3 Flathead Reading-Room Blocker Reduced Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced locally` for Milestone `3`; the Flathead reading-room placeholder
  is now an explicit blocker family, the SCC structured-export family remains
  resolved, and the next routed slice stays on the remaining export-backed
  families.
- Workbook and queue truth:
  `source-register-diff` remains unchanged at
  `canonical_master_row_count=647`, `canonical_only_source_count=647`,
  `canonical_queue_row_count=51`, and workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`;
  `source-register-queue-audit` now passes with
  `resolution_status_counts={"blocked":4,"planned":39,"resolved":8}`,
  `resolved_current_or_project_applicable_count=8`,
  `blocked_current_or_project_applicable_count=4`,
  `unresolved_current_or_project_applicable_count=37`, and the same governed
  historical/noncurrent rows (`FPS-380`, `SUP-007`).
- New blocker family:
  `FINAL-Q-FLAT-001` now routes to
  `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md` because the
  Flathead public reading-room family is only partially represented by
  current canonical rows; it cannot be honestly marked `resolved` until the
  remaining public documents are promoted or explicitly excluded with direct
  evidence.
- Active full-canonical catalog truth:
  the live source set remains `source-set-4fb59e9eb43045cb` with
  `source_count=647`, `artifact_count=635`,
  `source_partition_counts={"active_review_corpus":594,"currentness_supersession_archive":53}`,
  `status_counts={"downloaded_existing":635,"duplicate_content":12}`, and the
  same strengthened extraction, currentness, and retrieval truth already
  described in the preceding SCC structured-export section; this blocker
  opener does not change the catalog or downstream derived artifacts.
- Next routing:
  stay on Milestone `3` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for the remaining export-backed families
  `WILD-ESA-Q001`, `FINAL-Q-LOLO-001`, `FINAL-Q-NPC-001`, and `LEX-Q-001`.
  The active blocker packets are now
  `docs/FLATHEAD_READING_ROOM_FILE_SET_BLOCKER_MILESTONE_PLAN.md`
  and
  `docs/PROJECT_SPECIFIC_PUBLIC_PRIVATE_SOURCE_BOUNDARY_BLOCKER_MILESTONE_PLAN.md`.
- Closeout commit:
  `eb09556` (`Open Flathead reading-room blocker packet`).
- Verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check tests/test_source_register_queue_resolution.py`,
  and `git diff --check`.

## Full Canonical Direct-File Queue Milestone 3 SCC Structured-Export Slice Reduced Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced locally` for Milestone `3`; the SCC structured-export family is
  now closed locally, the project-specific blocker family remains explicit,
  and the next routed slice stays on the remaining export-backed families.
- Workbook and queue truth:
  `source-register-diff` now records `canonical_master_row_count=647`,
  `canonical_only_source_count=647`, `canonical_queue_row_count=51`, and
  workbook SHA
  `2c5117842370d31715af011d98b0d9a0a32141662821cfc1aeb9b17ad39fcf49`;
  `source-register-queue-audit` now passes with
  `resolution_status_counts={"blocked":3,"planned":40,"resolved":8}`,
  `resolved_current_or_project_applicable_count=8`,
  `blocked_current_or_project_applicable_count=3`,
  `unresolved_current_or_project_applicable_count=38`, and the same governed
  historical/noncurrent rows (`FPS-380`, `SUP-007`).
- Resolved queue families:
  `R1-SCC-Q-CGNF-RATIONALES`, `R1-SCC-Q-FLAT-RATIONALES`,
  `R1-SCC-Q-HLC-RATIONALES`, and `R1-SCC-Q-NPC-RATIONALES` now promote nine
  workbook successors:
  `R1-SCC-CGNF-005`, `R1-SCC-CGNF-006`, `R1-SCC-FLAT-005`,
  `R1-SCC-FLAT-006`, `R1-SCC-FLAT-007`, `R1-SCC-HLC-005`,
  `R1-SCC-HLC-006`, `R1-SCC-NPC-004`, and `R1-SCC-NPC-005`.
- Active full-canonical catalog truth:
  `catalog-build` now promotes the live catalog to
  `source-set-4fb59e9eb43045cb` with download run
  `queue-m3-full-canonical-merged-download-20260523`,
  `source_count=647`, `artifact_count=635`,
  `source_partition_counts={"active_review_corpus":594,"currentness_supersession_archive":53}`,
  `status_counts={"downloaded_existing":635,"duplicate_content":12}`, and
  the same workbook SHA.
- Downstream truth on the strengthened source set:
  `extract-build --reuse-existing --reuse-inventory-path .../source-set-4fb59e9eb43045cb/reuse_inventory/reuse_inventory.json`
  now passes with `extracted_count=647`, `reused_count=646`,
  `chunk_count=103063`, and `validation_passed=true`;
  `extraction-accuracy-audit --source-set-id source-set-4fb59e9eb43045cb`
  is green with `knowledge_base_admitted_source_record_ids=594`,
  `knowledge_base_blocked_source_record_ids=0`, and
  `explicitly_non_admitted_source_record_ids=53`;
  `authority-currentness --source-set-id source-set-4fb59e9eb43045cb` is
  green with `authority_family_count=460` and
  `current_authority_source_record_count=594`; and
  `retrieval-build --source-set-id source-set-4fb59e9eb43045cb` is
  `validation_passed=true`, `reviewer_ready=true`, and
  `verified_extraction_admitted_source_count=594`.
- Extraction/runtime gate truth:
  the live extraction manifest now records governed reuse provenance for
  payload-cache reuse (`reused_existing`, `reuse_from`,
  `reuse_source_set_id`, `reuse_payload_cache_path`,
  `verified_reuse_admissible`), and the direct-document audit now treats
  `.xlsx` workbook artifacts as admissible direct files rather than wrapper
  pages.
- Residual downstream split:
  the live extraction/retrieval truth now sits on
  `source-set-4fb59e9eb43045cb`, but `promotion-suite --manifest config/promotion_suite_v1.json`
  remains pinned to `full_canonical_source_set_id=source-set-3f7d4578cafb0704`
  and now truthfully reports
  `full_canonical_failure_category_counts={"stale_artifact":2}` with
  `full_canonical_corpus_ready=false`. Rebinding that downstream contract is
  successor work under the source-truth lane rather than this queue slice.
- Next routing:
  stay on Milestone `3` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for the remaining export-backed families and named blockers.
- Verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extract-build --output-dir source_library --reuse-existing --reuse-inventory-path source_library/derived/source-set-4fb59e9eb43045cb/reuse_inventory/reuse_inventory.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-4fb59e9eb43045cb`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --manifest config/promotion_suite_v1.json`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_loader.py tests/test_source_register_queue_resolution.py tests/test_source_register_schema.py tests/test_catalog.py tests/test_extract.py tests/test_extract_reuse.py tests/test_extraction_accuracy.py tests/test_download.py tests/test_preflight.py tests/test_dry_run.py tests/test_cli.py tests/test_retrieval_validation.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src tests`,
  and `git diff --check`.

## Historical Full Canonical Direct-File Queue Milestone 3 Alignment Pass

Latest docs alignment on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `aligned locally`; the routed docs stack now pins the Milestone `3`
  blocker-family opener, the earlier Milestone `2` direct-file promotion
  closeout, the then-live `585/585` successor boundary on
  `source-set-3f7d4578cafb0704`, and the same next routed slice.
- Closeout commit:
  `8b889a9` (`Open project-specific queue blocker packet`).
- Stale-reference audit:
  `README.md`, `docs/CURRENT_ROUTING.md`, this current-state log,
  `docs/SESSION_HANDOFF.md`,
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`,
  and the successor note in
  `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md` now agree
  on the Milestone `3` blocker-family opener `8b889a9`, the earlier
  Milestone `2` promotion checkpoint `85f087b`, the then-live `638/585`
  successor boundary, and Milestone `3` export-backed families as the next
  routed slice.
- Next routing:
  the packet remains active and the next executable slice is still Milestone
  `3` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for the export-backed families.
- Verification:
  targeted route grep across the routed queue docs,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  and `git diff --check`.

## Historical Full Canonical Direct-File Queue Milestone 3 Reduced Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced locally` for Milestone `3`; the low-complexity direct-file
  promotion slice remains closed from Milestone `2`, and the
  project-specific blocker-family opening slice is now closed locally while
  the next routed slice remains Milestone `3`.
- Promoted workbook rows:
  `FINAL-Q-HLC-001`, `FINAL-Q-HLC-002`, `FINAL-Q-HLC-003`, and `PROG-010`
  are now promoted into `Document_Register_Master` with governed direct-file
  capture rather than remaining queue-only placeholders.
- Blocked project-specific queue rows:
  `PROG-011`, `PROG-012`, and `PROG-013` now route to
  `docs/PROJECT_SPECIFIC_PUBLIC_PRIVATE_SOURCE_BOUNDARY_BLOCKER_MILESTONE_PLAN.md`
  as explicit project-specific blockers instead of generic unresolved queue
  placeholders.
- Closeout commit:
  `8b889a9` (`Open project-specific queue blocker packet`).
- Workbook and queue truth:
  `source-register-diff` now records `canonical_master_row_count=638`,
  `canonical_only_source_count=638`, `canonical_queue_row_count=51`, and
  workbook SHA
  `b0e78bb90336a01f73cd7489c109e45260d1a98fc0165f6b713d99311f029e5a`;
  `source-register-queue-audit` now passes with
  `resolution_status_counts={"blocked":3,"planned":44,"resolved":4}`,
  `blocked_current_or_project_applicable_count=3`,
  `unresolved_current_or_project_applicable_count=42`, and the same `2`
  governed historical/noncurrent rows (`FPS-380`, `SUP-007`).
- Active full-canonical catalog truth:
  `catalog-build` now promotes the live catalog to
  `source-set-3f7d4578cafb0704` with download run
  `queue-m2-full-canonical-merged-download-20260523`,
  `source_count=638`, `artifact_count=626`,
  `source_partition_counts={"active_review_corpus":585,"currentness_supersession_archive":53}`,
  `status_counts={"downloaded":4,"downloaded_existing":622,"duplicate_content":12}`,
  and the same workbook SHA as above.
- Downstream revalidation truth:
  `extraction-accuracy-audit --source-set-id source-set-3f7d4578cafb0704`
  is green with `knowledge_base_admitted_source_record_ids=585`,
  `knowledge_base_blocked_source_record_ids=0`, and
  `explicitly_non_admitted_source_record_ids=53`;
  `authority-currentness --source-set-id source-set-3f7d4578cafb0704` is
  green with `authority_family_count=456`,
  `current_authority_source_record_count=585`,
  `source_currentness_counts={"confirmed_from_catalog":585,"currentness_archive_only":47,"replacement_source_confirmed":6}`;
  `retrieval-build --source-set-id source-set-3f7d4578cafb0704` is
  `validation_passed=true` and `reviewer_ready=true` with
  `verified_extraction_required_source_count=585`,
  `verified_extraction_admitted_source_count=585`, and
  `verified_extraction_explicitly_non_admitted_source_count=53`;
  `forest-plan-components-build` is green with `component_count=1416` and
  `standard_count=397`;
  `nepa-knowledge-graph-export` is green with
  `catalog_source_record_count=638`, `validation_check_count=72`, and
  `failed_validation_check_count=0`;
  `forest-plan-profile-eval` is green with `covered_profile_count=10`;
  `forest-plan-component-retrieval-eval` is green with `6/6` cases passed;
  and `promotion-suite --manifest config/promotion_suite_v1.json` again
  reports `full_canonical_source_set_id=source-set-3f7d4578cafb0704`,
  `passed_required_full_canonical_result_count=10`,
  `required_full_canonical_result_count=10`,
  `full_canonical_corpus_ready=true`, `current_promotion_ready=true`,
  `expansion_ready=true`, and `promotion_ready=true`.
- Residual truth:
  the ad hoc full-canonical
  `phase-eval --source-set-id source-set-3f7d4578cafb0704` replay still
  lacks extraction, retrieval, claim-extraction, and rule-claim direct-eval
  coverage on the strengthened full-canonical source set and therefore
  remains outside this Milestone `2` acceptance boundary.
- Next routing:
  execute Milestone `3` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for export-backed families and named blockers.
- Verification:
  `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library --source-set-id source-set-3f7d4578cafb0704`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-3f7d4578cafb0704`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-3f7d4578cafb0704`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-components-build --output-dir source_library --source-set-id source-set-3f7d4578cafb0704 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources nepa-knowledge-graph-export --output-dir source_library --source-set-id source-set-3f7d4578cafb0704`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-profile-eval --output-dir source_library --manifest config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources forest-plan-component-retrieval-eval --output-dir source_library --manifest config/forest_plan_component_retrieval_eval_v1.json`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  and
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_loader.py tests/test_source_register_schema.py tests/test_source_register_queue_resolution.py tests/test_dry_run.py tests/test_preflight.py tests/test_catalog.py tests/test_phase_eval_direct_eval_contracts.py tests/test_forest_plan_profile_eval_contracts.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_identity_reconciliation.py tests/test_phase_eval.py tests/test_promotion_suite_full_canonical.py tests/test_architecture_contract.py -q`.

## Full Canonical Direct-File Queue Milestones 0-1 Resolved Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved locally` for Milestones `0` and `1`; the queue now has a tracked
  machine-readable ledger plus a fail-closed audit gate, but no queue rows
  have been promoted yet.
- Baseline truth:
  `config/source_register_queue_resolution_ledger_v1.json` now records all
  `51` `Direct_File_Capture_Queue` rows exactly once with `49`
  current/project-applicable rows, `2` governed historical/noncurrent rows
  (`FPS-380`, `SUP-007`), and planned disposition counts of `37`
  `promote_direct_file`, `9` `promote_structured_export`, `3`
  `named_blocker`, and `2` `historical_scope_only`.
- Audit truth:
  `source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
  now passes with zero missing, unexpected, duplicated, or drifted queue
  rows, `unresolved_current_or_project_applicable_count=49`, and the full
  unresolved roster exposed as a machine-readable output field.
- Next routing:
  execute Milestone `2` in
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  for the low-complexity direct-file promotion families without reopening the
  resolved source-truth or downstream-gold packets.
- Verification:
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-queue-audit --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_source_register_schema.py tests/test_source_register_proving.py tests/test_source_register_queue_resolution.py tests/test_cli.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/source_register_queue_resolution.py src/usfs_r1_ea_sources/cli_capture.py tests/test_source_register_queue_resolution.py tests/test_cli.py tests/test_source_register_schema.py tests/test_source_register_proving.py tests/test_architecture_contract.py`,
  and `git diff --check`.

## Extraction Fidelity Eval Milestone 4 Gap-Close Alignment Pass

Latest docs alignment on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `aligned locally`; routing truth is unchanged, and the resolved plan no
  longer carries stale `Current Evidence` prose claiming a remaining
  Milestone `4` live-closeout gap after the actual closeout landed.
- Closeout commit:
  `abd0e4d` (`Resolve extraction fidelity Milestone 4`).
- Gap-close audit:
  the packet stays resolved locally through Milestone `4`, the next
  executable packet remains
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`,
  and the only stale packet-local wording found in the active docs stack was
  the now-retired plan sentence that still described live closeout and docs
  alignment as an open gap.
- Verification:
  targeted route grep across the routed extraction-fidelity docs plus
  `git diff --check`.

## Extraction Fidelity Eval Milestone 4 Alignment Pass

Latest docs alignment on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `aligned locally`; the top docs stack now records the actual Milestone `4`
  closeout commit and retires the remaining implementation-only wording plus
  older Milestone `3` next-step references below as historical for routing.
- Closeout commit:
  `abd0e4d` (`Resolve extraction fidelity Milestone 4`).
- Stale-reference audit:
  the immediately following Milestone `4` closeout section remains the live
  closeout summary, but the lower Milestone `3`, Milestone `2`, and
  Milestones `0`/`1` sections are historical only wherever they still treat
  the extraction-fidelity packet as active or still route the next slice to
  Milestone `4` after `abd0e4d`.
- Next routing:
  the next executable packet is now
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.

## Extraction Fidelity Eval Milestone 4 Resolved Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved locally` for Milestone `4`; the extraction-fidelity packet is now
  fully closed locally.
- Closeout commit:
  `abd0e4d` (`Resolve extraction fidelity Milestone 4`).
- Final owner split:
  `extraction_validation.json` remains structural validation,
  `extraction_accuracy_audit.json` remains the live generated-corpus audit,
  `extraction_fidelity_eval_results.json` remains the dedicated offline
  direct-fidelity artifact, `upstream-eval` remains the capture/catalog
  umbrella proof, and full-canonical `promotion-suite` now consumes the
  dedicated extraction-fidelity artifact directly for readiness.
- Fixture replay truth:
  `extraction-fidelity-eval --manifest config/extraction_fidelity_eval_v1.json --output-dir source_library`
  remains green at `required_category_count=12`, `case_count=24`,
  `matched_case_count=24`, `parser_route_mismatch_count=1`,
  `anchor_mismatch_count=13`, `span_mismatch_count=10`,
  `boundary_mismatch_count=4`, `negative_case_pass_count=12`,
  `negative_case_fail_count=0`, and `required_check_mismatch_count=0`.
- Live audit truth:
  the Docling-backed
  `extraction-accuracy-audit --output-dir source_library` rerun on
  `source-set-f775524ab233ff27` remains green with
  `audited_record_count=581`, `audited_chunk_count=96997`,
  `knowledge_base_admitted_source_record_ids=581`,
  `knowledge_base_blocked_source_record_ids=0`, and
  `explicitly_non_admitted_source_record_ids=53`.
- Upstream replay truth:
  `upstream-eval --manifest config/upstream_evaluation_v1.json --output-dir source_library`
  remains green with `required_lane_count=2`, `required_category_count=8`,
  `case_count=16`, and `matched_case_count=16`.
- Promotion replay truth:
  `promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`
  remains green with `passed_required_full_canonical_result_count=10`,
  `required_full_canonical_result_count=10`,
  `full_canonical_source_set_id=source-set-f775524ab233ff27`,
  `full_canonical_corpus_ready=true`, `current_promotion_ready=true`,
  `expansion_ready=true`, and `promotion_ready=true`.
- Next routing:
  the next executable packet is now
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`.

## Extraction Fidelity Eval Milestone 3 Alignment Pass

Latest docs alignment on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `aligned locally`; the top docs stack now records the actual Milestone `3`
  closeout commit and removes the remaining active-looking drift between the
  local Milestone `3` implementation state and the older upper sections below
  that still route the packet to Milestone `3` or still cite the older `9/9`
  full-canonical baseline.
- Closeout commit:
  `4269f5e` (`Implement extraction fidelity Milestone 3`).
- Stale-reference audit:
  the immediately following Milestone `3` closeout section is still live, but
  the lower `Milestone 2 Alignment Pass`, `Milestone 2 Resolved Locally`,
  `Milestones 0-1 Alignment Pass`, and `Milestone 1 Started Locally`
  sections become historical-only for next-step routing after `4269f5e`
  wherever they still say the next routed slice is Milestone `3` or still
  cite the older `9/9` full-canonical result floor.
- Next routing:
  the packet remains active and the next routed slice is now Milestone `4` in
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.

## Extraction Fidelity Eval Milestone 3 Resolved Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved locally` for Milestone `3`; Milestones `0` through `2` remain
  closed, and Milestone `4` remains open.
- Owner split:
  `extraction_validation.json` remains structural validation,
  `extraction_accuracy_audit.json` remains the live generated-corpus audit,
  `extraction_fidelity_eval_results.json` is now the load-bearing direct
  extraction-fidelity artifact, and `upstream-eval` is now narrowed to the
  capture/catalog umbrella only.
- Upstream replay truth:
  `config/upstream_evaluation_v1.json` now declares `required_lane_count=2`,
  `required_category_count=8`, and `case_count=16`, and the real
  `upstream-eval` replay stays green at `matched_case_count=16`.
- Promotion routing truth:
  `config/promotion_suite_v1.json` now requires
  `source_library/evaluations/extraction_fidelity/extraction_fidelity_eval_results.json`
  directly for full-canonical readiness, and the strengthened replay now
  stays green at `passed_required_full_canonical_result_count=10`,
  `required_full_canonical_result_count=10`,
  `full_canonical_corpus_ready=true`, and `current_promotion_ready=true`.
- Closeout commit:
  `4269f5e` (`Implement extraction fidelity Milestone 3`).
- Stale-reference audit:
  the immediately following Milestone `2` alignment and Milestone `2`
  closeout sections remain historical context only wherever they still route
  the packet to Milestone `3` or still cite the older `9/9` full-canonical
  baseline after `4269f5e`.
- Next routing:
  execute Milestone `4` in
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md` to rerun the live
  extraction audit plus the strengthened upstream/promotion route and finish
  packet closeout/alignment.

## Extraction Fidelity Eval Milestone 2 Alignment Pass

Latest docs alignment on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `aligned locally`; the top docs stack now records the actual Milestone `2`
  closeout commit and removes the remaining active-looking drift between the
  local Milestone `2` implementation state and the older upper sections below
  that still route the packet to Milestone `2`.
- Closeout commit:
  `16fb8b2` (`Implement extraction fidelity Milestone 2`).
- Stale-reference audit:
  the immediately following Milestone `2` closeout section is still live, but
  the lower `Milestones 0-1 Alignment Pass` and `Milestone 1 Started Locally`
  sections become historical-only for next-step routing after `16fb8b2`
  wherever they still say the next routed slice is Milestone `2`.
- Next routing:
  the packet remains active and the next routed slice is now Milestone `3` in
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.

## Extraction Fidelity Eval Milestone 2 Resolved Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved locally` for Milestone `2`; Milestones `0` and `1` remain closed,
  and Milestones `3` through `4` remain open.
- Owner surface:
  the repo now ships a dedicated
  `src/usfs_r1_ea_sources/extraction_fidelity_eval.py` producer plus
  `extraction-fidelity-eval` CLI registration and durable outputs under
  `source_library/evaluations/extraction_fidelity/`.
- Replay truth:
  the committed manifest `config/extraction_fidelity_eval_v1.json` now runs
  green at `required_category_count=12`, `case_count=24`,
  `matched_case_count=24`, `parser_route_mismatch_count=1`,
  `anchor_mismatch_count=13`, `span_mismatch_count=10`,
  `boundary_mismatch_count=4`, `negative_case_pass_count=12`,
  `negative_case_fail_count=0`, and `required_check_mismatch_count=0`.
- Closeout commit:
  `16fb8b2` (`Implement extraction fidelity Milestone 2`).
- Owner split:
  `extraction_validation.json` remains structural extraction validation,
  `extraction_accuracy_audit.json` remains live generated-corpus audit truth,
  and `extraction_fidelity_eval_results.json` now exists as the dedicated
  offline direct-fidelity artifact instead of a planned future owner only.
- Next routing:
  execute Milestone `3` in
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md` to narrow the older
  `upstream-eval` extraction umbrella and make the new artifact load-bearing
  in upstream/promotion routing.

## Extraction Fidelity Eval Milestones 0-1 Alignment Pass

Latest docs alignment on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `aligned locally`; the top docs stack now records the actual first-slice
  closeout commit and removes the remaining active-looking drift between the
  local Milestone `0`/`1` implementation state and the older proposed-only
  packet entry below.
- Closeout commit:
  `f2afa8f` (`Resolve extraction fidelity Milestones 0-1`).
- Stale-reference audit:
  the immediately following `Extraction Fidelity Eval Packet Proposed`
  section is historical only after `f2afa8f`; use the newer Milestone `0`/`1`
  state plus `docs/CURRENT_ROUTING.md` as live routing truth.
- Next routing:
  the packet remains active and the next routed slice is still Milestone `2`
  in `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.

## Extraction Fidelity Eval Milestone 1 Started Locally

Latest implementation update on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved locally` for Milestone `0` and Milestone `1`; Milestones `2`
  through `4` remain open.
- Owner boundary:
  this remains a fresh upstream-standard packet, not a reopened
  source-truth or downstream gold lane.
- Milestone 0 lock:
  the live owner split is re-locked from repo artifacts only:
  `extraction_validation.json` remains structural validation,
  `extraction_accuracy_audit.json` remains live generated-corpus audit truth,
  the future `extraction_fidelity_eval_results.json` remains the dedicated
  direct-eval owner target, and the current full-canonical promotion baseline
  remains green at `passed_required_full_canonical_result_count=9`,
  `required_full_canonical_result_count=9`.
- Milestone 1 substrate:
  the repo now ships `config/extraction_fidelity_eval_v1.json`,
  `12` required fidelity families, `24` tracked cases, `12`
  fixture-backed category files under
  `config/fixtures/extraction_fidelity_eval/`, and contract-negative
  manifests under `tests/fixtures/extraction_fidelity_eval/`.
- Closeout commit:
  `f2afa8f` (`Resolve extraction fidelity Milestones 0-1`).
- Acceptance proof:
  `tests/test_extraction_fidelity_eval.py` now passes the real manifest plus
  the missing-category and out-of-tree fixture fail-closed checks.
- Next routing:
  implement Milestone `2` in
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md` to add the dedicated
  `extraction-fidelity-eval` command, durable artifact schema, and report
  owner before touching upstream/promotion wiring.

## Extraction Fidelity Eval Packet Proposed

Latest planning update on 2026-05-23:

- Routed packet:
  `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md`.
- Outcome label:
  `proposed follow-on`; no implementation has landed yet.
- Owner boundary:
  this is a fresh upstream-standard packet, not a reopened source-truth or
  downstream gold lane.
- Current truth the plan is anchored to:
  `config/upstream_evaluation_v1.json` still provides a green aggregate
  upstream extraction lane with `11` required extraction categories and `22`
  extraction cases inside `upstream-eval`, while the live full-canonical
  `extraction_accuracy_audit.json` on `source-set-f775524ab233ff27` still
  records `audited_record_count=581`,
  `knowledge_base_admitted_source_record_ids=581`,
  `knowledge_base_blocked_source_record_ids=0`, and
  `explicitly_non_admitted_source_record_ids=53`.
- Weakness being routed:
  the repo still lacks a dedicated fixture-backed extraction-fidelity producer
  with its own thresholds, per-category metrics, parser-route expectations,
  and hard-negative ownership. Extraction direct-eval truth remains too
  aggregate inside `upstream-eval` to be the long-term fidelity standard.
- Planned owner split:
  `extraction_validation.json` remains structural validation,
  `extraction_accuracy_audit.json` remains live generated-corpus audit truth,
  and the queued packet will add a dedicated
  `extraction-fidelity-eval` direct-eval owner rather than pushing more
  burden into `gold-coverage-eval`.
- Readiness implication:
  the current full-canonical promotion route remains green at
  `passed_required_full_canonical_result_count=9`,
  `required_full_canonical_result_count=9`. The queued packet is expected to
  strengthen, and likely expand, the full-canonical readiness contract after a
  dedicated fidelity artifact exists.
- Next routing:
  start with `docs/EXTRACTION_FIDELITY_EVAL_MILESTONE_PLAN.md` for the next
  upstream implementation slice if the goal is to raise import/extraction
  proof rather than downstream package breadth.

## Full Canonical Downstream Freshness Packet Retired For Live Routing

Latest docs-only routing retirement on 2026-05-23:

- Routed packet:
  `docs/FULL_CANONICAL_DOWNSTREAM_FRESHNESS_REFRESH_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved historical reference`; the preserved `source-set-cac9c7d02b280825`
  freshness reduction is append-only blocker evidence only, not a live reduced
  owner.
- Closeout commit:
  `4cf9451` (`Retire stale downstream freshness routing`).
- Successor chain:
  the live full-canonical route has since closed through
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`,
  `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`,
  `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`, and
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`.
- Live routing truth:
  `source-set-f775524ab233ff27` is the sole active full-canonical catalog;
  source-truth now admits `581/581` active-current rows while explicitly
  keeping `53` archive/currentness rows outside verified admission; default
  `compliance-gold-eval` now passes `14/14`; default `gold-coverage-eval`
  passes `7/7`; and the default `promotion-suite` now reports
  `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `expansion_ready=true`, and `promotion_ready=true`.
- Stale-reference audit:
  the downstream freshness packet's reduced `source-set-cac9c7d02b280825`
  checkpoint is historical only after the later live-promotion closeout
  `f464fa9`, source-truth closeout `93a23b0`, and downstream gold closeout
  `8e0e02b`.
- Verification:
  targeted route grep over the top docs, milestone-plan lint on
  `docs/FULL_CANONICAL_DOWNSTREAM_FRESHNESS_REFRESH_MILESTONE_PLAN.md`, and
  `git diff --check`.

## Full Canonical Compliance Gold Rebaseline Resolved Locally

Latest worktree implementation on 2026-05-23:

- Routed implementation packet:
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved locally`; the current worktree closes the downstream
  full-canonical gold packet by refreshing the active claim surface,
  restricting source-record and document-role expectation checks to
  source-backed statuses, and rebaselining the five still-unmapped
  authorities as explicit `uncertain` package-only adjudication rather than
  false source-backed misses.
- Closeout commit:
  `8e0e02b` (`Resolve full canonical compliance gold rebaseline`).
- Implementation surfaces:
  `config/compliance_gold_eval_v1.json`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `src/usfs_r1_ea_sources/compliance_review_eval_scoring.py`,
  `tests/test_compliance_review_eval.py`, and the local ignored refreshed
  claim, compliance-gold, gold-coverage, and promotion-suite artifacts under
  `source_library/`.
- Live replay truth:
  the refreshed claim summary on `source-set-f775524ab233ff27` now records
  `claim_count=124458`, `source_record_count=539`,
  `validation_passed=true`, and `reviewer_ready=true`. The refreshed default
  `compliance_gold_eval_results.json` now records `passed_case_count=14`,
  `failed_case_count=0`, `authority_trace_coverage_rate=1.0`,
  `status_match_rate=1.0`, `source_record_match_rate=1.0`,
  `source_document_role_match_rate=1.0`,
  `source_claim_link_match_rate=1.0`, and
  `package_evidence_match_rate=1.0`, while
  `promotion_ready=false` remains explained only by
  `reviewer_ready_rule_pack=false` on the base `nepa-ea-v0` rule pack.
- Aggregate truth:
  the canonical `gold_coverage_eval_results.json` now records `passed=true`,
  `required_theme_count=7`, `passed_theme_count=7`,
  `required_review_contract_count=3`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_review_count=2`,
  `typed_blocked_review_count=1`,
  `missing_required_review_contract_count=0`,
  `missing_package_authority_count=0`, and
  `unmapped_high_priority_family_count=0`.
- Promotion truth:
  the refreshed default `promotion_suite_results.json` now records
  `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `expansion_ready=true`, `promotion_ready=true`,
  `passed_required_current_result_count=32`,
  `required_current_result_count=32`,
  `passed_required_full_canonical_result_count=9`,
  `required_full_canonical_result_count=9`, and
  `failure_category_counts={}`.
- Remaining boundary:
  no active full-canonical source-truth or gold blocker remains routed in
  this lane. `51` `Direct_File_Capture_Queue` rows remain outside the active
  load-bearing surface by workbook contract, but that queue boundary is now
  explicitly routed through
  `docs/FULL_CANONICAL_DIRECT_FILE_CAPTURE_QUEUE_RESOLUTION_MILESTONE_PLAN.md`
  instead of remaining ownerless. West Reservoir remains an intentional
  `typed_blocked` replay quarantine rather than a promotion blocker.
- Stale-reference audit:
  the immediately following source-truth section and older append-only
  references that still route the downstream gold packet as active, still
  report `0/14` gold results, or still describe the five unmapped
  authorities as live source-backed mismatches are historical only; this
  latest local closeout supersedes them for live routing.
- Verification:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_retrieval.py tests/test_rule_claim_binding_runtime.py tests/test_rule_claim_binding.py tests/test_ea_review.py tests/test_compliance_review_eval.py tests/test_compliance_review_contracts.py tests/test_compliance_gold_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/compliance_review_eval.py src/usfs_r1_ea_sources/compliance_review_eval_scoring.py tests/test_compliance_review_eval.py tests/test_compliance_gold_eval.py tests/test_gold_coverage_eval.py tests/test_promotion_suite.py tests/test_architecture_contract.py`,
  `PYTHONPATH=src .venv/bin/python -m compileall src`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources compliance-gold-eval --output-dir source_library --gold-file config/compliance_gold_eval_v1.json --rule-pack config/compliance_rule_pack_nepa_ea_v0.json`,
  `PYTHONPATH=src .venv/bin/python - <<'PY' ... run_gold_coverage_eval(... results_path=existing default applicability/compliance/review coverage artifacts ...) ... PY`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`, and
  `git diff --check`.

## Full Canonical Source Truth Rebaseline Resolved Locally

Latest worktree implementation on 2026-05-23:

- Routed implementation packet:
  `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved locally`; the current worktree closes the remaining
  archive-lineage governance gap by declaring the `53`
  `currentness_supersession_archive` rows as explicit full-canonical lineage
  outside verified admission, while preserving the earlier Milestone `2`
  blocker closeout that captured the live `FSH 2509.18` transmittal and
  archived `USFS-026` with replacement `USFS-023`.
- Closeout commit:
  `93a23b0` (`Resolve source-truth archive boundary rebaseline`).
- Previous reduced-slice closeout:
  the manual-redirect slice remains recorded in `53d59da`
  (`Reduce source-truth Milestone 2 manual redirect blockers`).
- Earlier reduced-slice closeout:
  `96450be` (`Reduce source-truth Milestone 2 manual wrapper blockers`).
- Earlier reduced-slice closeout:
  the handbook-wrapper slice remains recorded in `4650837`
  (`Reduce source-truth Milestone 2 handbook wrapper blockers`).
- Implementation surfaces:
  `config/verified_extraction_admission_contract.json`,
  `config/promotion_suite_v1.json`,
  `src/usfs_r1_ea_sources/extraction_admission.py`,
  `src/usfs_r1_ea_sources/extraction_accuracy.py`,
  `src/usfs_r1_ea_sources/retrieval_runtime.py`,
  `tests/test_extraction_accuracy.py`,
  `tests/test_promotion_suite_full_canonical.py`, and the local ignored
  refreshed extraction, authority-currentness, retrieval, and promotion-suite
  replays under `source_library/derived/source-set-f775524ab233ff27/` and
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/`.
- Live replay truth:
  the refreshed `extraction-accuracy-audit` on
  `source-set-f775524ab233ff27` now records `audited_record_count=581`,
  `knowledge_base_admitted_source_record_ids=581`,
  `knowledge_base_blocked_source_record_ids=0`, and
  `explicitly_non_admitted_source_record_ids=53`. The refreshed retrieval
  replay on `source-set-f775524ab233ff27` now records
  `verified_extraction_required_source_count=581`,
  `verified_extraction_admitted_source_count=581`,
  `verified_extraction_explicitly_non_admitted_source_count=53`,
  `verified_extraction_contract_ids=["canonical-source-register-active-current-admission"]`,
  `validation_passed=true`, and `reviewer_ready=true`. The refreshed
  `authority-currentness` report now records
  `catalog_source_partition_counts={"active_review_corpus":581,"currentness_supersession_archive":53}`,
  `source_currentness_counts={"confirmed_from_catalog":581,"currentness_archive_only":47,"replacement_source_confirmed":6}`,
  `families_requiring_milestone_2_source_currentness=0`, and
  `validation_passed=true`. The refreshed `promotion-suite` result now
  records `full_canonical_corpus_ready=true`,
  `passed_required_full_canonical_result_count=9`,
  `required_full_canonical_result_count=9`, and
  `full_canonical_failure_category_counts={}`; the downstream
  compliance-gold closeout above now also lifts the same default
  promotion-suite lane to `current_promotion_ready=true`,
  `expansion_ready=true`, and `promotion_ready=true`.
- Blocked roster:
  none. `USFS-026` remains governed archive lineage evidence with replacement
  `USFS-023`, while `USFS-018` (`FSM 2410`) and `USFS-024` (`FSM 2580`)
  remain admitted through live current official Forest Service static-file
  PDFs and the archive boundary is now explicit rather than implied by
  selector omission.
- Remaining boundary:
  `51` `Direct_File_Capture_Queue` rows remain outside the active load-bearing
  surface by workbook contract; the downstream compliance-gold packet above is
  now also resolved locally, so no full-canonical owner remains active in
  this route.
- Stale-reference audit:
  the immediately following Milestone `1` section and older append-only
  references to `582/52`, `581/582`, `579/582`, `569/582`, `560/582`, or
  `559/582`, open Milestone `3` routing, broader manual-family owner
  language, and `USFS-026` as an active-current direct-document blocker are
  now historical only; this latest local closeout supersedes them for live
  routing.
- Verification:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_extraction_accuracy.py tests/test_promotion_suite_full_canonical.py tests/test_source_partitions.py tests/test_authority_currentness.py tests/test_retrieval_validation.py tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/extraction_admission.py src/usfs_r1_ea_sources/extraction_accuracy.py src/usfs_r1_ea_sources/retrieval_runtime.py tests/test_extraction_accuracy.py tests/test_promotion_suite_full_canonical.py tests/test_source_partitions.py tests/test_authority_currentness.py tests/test_retrieval_validation.py tests/test_architecture_contract.py`,
  `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources authority-currentness --output-dir source_library --source-set-id source-set-f775524ab233ff27`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-f775524ab233ff27`, and
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources promotion-suite --output-dir source_library --manifest config/promotion_suite_v1.json`,
  `git diff --check`.

## Full Canonical Source Truth Rebaseline Milestone 1 Resolved

Latest worktree implementation on 2026-05-22:

- Routed implementation packet:
  `docs/FULL_CANONICAL_SOURCE_TRUTH_REBASELINE_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `1`; the packet now advances to Milestone `2`
  reduced with the widened verified-admission replay landed locally.
- Closeout commit:
  `46bff61` (`Resolve source-truth rebaseline Milestone 1`).
- Live replay truth:
  the refreshed retrieval replay on `source-set-f775524ab233ff27` records
  `verified_extraction_required_source_count=582`,
  `verified_extraction_admitted_source_count=559`,
  `verified_extraction_contract_ids=["canonical-source-register-active-current-admission"]`,
  `validation_passed=false`, and `reviewer_ready=false`.
- Blocked roster:
  `extraction-accuracy-audit` and retrieval validation now agree on `23`
  blocked active-current rows under the rebaselined contract:
  `22` Official USFS source-page wrappers and `1` Federal Register XML source
  (`FPS-344`).
- Remaining boundary:
  `51` `Direct_File_Capture_Queue` rows remain outside the active load-bearing
  surface, and the `52` `currentness_supersession_archive` rows still await the
  Milestone `3` lineage decision in the same packet.
- Stale-reference audit:
  the immediately following packet-open section in `docs/SESSION_HANDOFF.md`
  and older `343`-row historical sections below in this append-only file remain
  preserved history only; this Milestone `1` closeout and commit `46bff61`
  supersede them for live routing.
- Verification:
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_extraction_accuracy.py -q`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_retrieval_validation.py -q`,
  `PYTHONPATH=src .venv/bin/python -m pytest tests/test_architecture_contract.py -q`,
  `PYTHONPATH=src .venv/bin/python -m ruff check src/usfs_r1_ea_sources/extraction_accuracy.py tests/test_extraction_accuracy.py`,
  `PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources extraction-accuracy-audit --output-dir source_library`,
  `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources retrieval-build --output-dir source_library --source-set-id source-set-f775524ab233ff27`, and
  `git diff --check`.

## Under-800 Hotspot Reduction Milestone 9 Alignment Closeout

Latest docs-only alignment on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved`; the packet was already closed, and this pass updates the remaining secondary docs and
  metadata so they no longer imply queued work or the historical `24`-file baseline.
- Alignment truth:
  `config/architecture_large_file_inventory_v1.json` now records this packet as
  `resolved_historical_closeout`, `README.md` no longer points readers to a current oversized-file
  follow-on queue, and `docs/AGENTIC_REPO_BEST_PRACTICES_GUIDE.md` now reflects the live
  `462`-file / `0`-oversized baseline.
- Stale-reference audit:
  no remaining live doc or metadata surface in this repo-wide sweep still instructs users to
  finish Milestone `9` or still describes the under-`800` packet as active queued work; older
  append-only sections below remain historical only.

## Under-800 Hotspot Reduction Milestone 9 Closeout

Latest docs-and-readback closeout on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved`; Milestone `9` closes the under-`800` packet and retires the last queued-route
  wording.
- Closeout commit:
  `a6c5459` (`Resolve under-800 Milestone 9 closeout`).
- Closeout truth:
  the fresh architecture probe still reports `462` code files, `0` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, and an empty
  oversized-file inventory in `config/architecture_large_file_inventory_v1.json`.
- Last owner truth:
  the viewer family was the final oversized owner closed in this packet at Milestone `8`; this
  Milestone `9` slice closes only the final zero-oversized rebaseline and live-doc routing
  readback.
- Routing truth:
  `README.md`, `docs/CURRENT_ROUTING.md`, `docs/SESSION_HANDOFF.md`, and
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md` now treat this packet as resolved
  historical closeout rather than queued active debt.

## Under-800 Hotspot Reduction Milestone 8 Alignment Closeout

Latest docs-only alignment on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved`; this pass did not change the live routed implementation slice, but it closed the
  remaining post-Milestone `8` plan drift.
- Alignment truth:
  the remaining live gap was stale packet wording that still described the scope as an exact live
  `1`-file oversized inventory and still described the remaining packet work as owner-family
  reduction. The packet now correctly reflects the Milestone `8` zero-oversized baseline and a
  Milestone `9` closeout/readback-only finish.
- Stale-reference audit:
  the only remaining viewer-family `1`-file wording is confined to older Milestone `7` historical
  sections in append-only docs, where it is explicitly superseded by the Milestone `8` closeout
  and this alignment pass.
- Live architecture truth:
  the fresh architecture probe remains at `462` code files, `0` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, and an empty
  oversized-file inventory in `config/architecture_large_file_inventory_v1.json`.

## Under-800 Hotspot Reduction Milestone 8

Latest implementation on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `8`; the viewer owner family is now closed under the
  `800`-line gate, and the packet advances to Milestone `9`.
- Implementation surfaces:
  `viewer/nepa-3d/app.js`,
  `viewer/nepa-3d/index.html`,
  `viewer/nepa-3d/viewer-utils.js`,
  `viewer/nepa-3d/viewer-config.js`,
  `viewer/nepa-3d/viewer-controls.js`,
  `viewer/nepa-3d/viewer-data.js`,
  `viewer/nepa-3d/viewer-scenes.js`,
  `viewer/nepa-3d/viewer-graph.js`,
  `viewer/nepa-3d/viewer-details.js`,
  `viewer/nepa-3d/viewer-labels.js`,
  `tests/test_nepa_3d_viewer.py`,
  `tests/test_architecture_quality.py`, and
  `config/architecture_large_file_inventory_v1.json`.
- Closeout truth:
  the old viewer monolith is now a thin bootstrap over named viewer siblings for shared utilities,
  configuration, controls, dataset discovery, scene routing, graph logic, details, and labels;
  every viewer-local script is `<=800` lines; the viewer test suite now fails closed on the exact
  local script roster plus per-file budgets; and the oversized-file inventory is now empty.
- Debt-shift audit:
  the largest new viewer siblings are
  `viewer-graph.js=636`,
  `viewer-labels.js=461`,
  `viewer-config.js=357`,
  `viewer-utils.js=256`,
  `viewer-controls.js=209`,
  `viewer-data.js=209`,
  `viewer-details.js=267`, and
  `viewer-scenes.js=127`; none reopened the oversized queue or created a JS/TS cycle.
- Live architecture truth:
  the fresh architecture probe now reports `462` code files, `0` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, top overall
  hotspot `tests/test_compliance_review.py` at score `35420`, and an empty oversized-file
  inventory in `config/architecture_large_file_inventory_v1.json`.
- Next routing:
  keep the broader repo default route on
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; when the under-`800`
  architecture queue resumes, continue at Milestone `9` in
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.

## Under-800 Hotspot Reduction Milestone 7

Latest implementation on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `7`; the compliance and eval owner family is now
  closed under the `800`-line gate, and the packet advances to Milestone `8`.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  the new `src/usfs_r1_ea_sources/compliance_review_eval_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/compliance_outputs.py`,
  the new `src/usfs_r1_ea_sources/compliance_outputs_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/compliance_validation.py`,
  `src/usfs_r1_ea_sources/compliance_validation_checks.py`,
  `tests/test_compliance_review_test_boundary.py`,
  `tests/test_architecture_quality.py`,
  `config/architecture_large_file_inventory_v1.json`, and
  `docs/architecture_contract.toml`.
- Closeout truth:
  the oversized compliance/eval owners are now thin facades over explicit sibling owners; every
  file in the `compliance_review_eval*`, `compliance_outputs*`, and
  `compliance_validation*` families is `<=800` lines; the compliance boundary test now
  fails closed on the exact source-family roster plus per-file budgets; the oversized-file
  inventory now contains only the viewer family; and `tests/test_architecture_quality.py`
  now ratchets the live oversized queue to `1`.
- Debt-shift audit:
  the largest new sibling files are
  `compliance_review_eval_scoring.py=728`,
  `compliance_validation_checks.py=533`,
  `compliance_outputs_matrix.py=469`,
  `compliance_outputs_common.py=413`,
  and `compliance_review_eval_generated.py=373`; none reopened the oversized queue, created an
  import cycle, or exceeded the fan-out gate.
- Live architecture truth:
  the fresh architecture probe now reports `454` code files, `1` code file above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, top
  overall hotspot `tests/test_compliance_review.py` at score `35420`, and only remaining
  oversized file `viewer/nepa-3d/app.js` at `2547` lines.
- Bounded gold replay:
  `source_library/reviews/compliance_gold_eval_under800/compliance_gold_eval_results.json`
  stayed red at `0/14` with `authority_trace_coverage_rate=1.0`; the same five still-unmapped
  live authorities remain the only failing rule IDs
  (`apa_final_agency_action`, `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`, `organic_act_16usc_475`, and
  `seven_county_nepa_scope`), so this slice did not change active gold semantics.
- Next routing:
  keep the broader repo default route on
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; when the under-`800`
  architecture queue resumes, continue at Milestone `8` in
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.

## Under-800 Hotspot Reduction Milestone 6

Latest implementation on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `6`; the capture, catalog, and source-register owner family is now
  closed under the `800`-line gate, and the packet advances to Milestone `7`.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/catalog.py`,
  the new `src/usfs_r1_ea_sources/catalog_outputs.py`,
  `src/usfs_r1_ea_sources/authority_currentness.py`,
  the new `src/usfs_r1_ea_sources/authority_currentness_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/source_register.py`,
  the new `src/usfs_r1_ea_sources/source_register_validation.py`,
  `src/usfs_r1_ea_sources/source_register_proving.py`,
  the new `src/usfs_r1_ea_sources/source_register_proving_graph.py`,
  `src/usfs_r1_ea_sources/download.py`,
  the new `src/usfs_r1_ea_sources/download_transport.py`,
  `src/usfs_r1_ea_sources/preflight.py`,
  the new `src/usfs_r1_ea_sources/preflight_transport.py`,
  `tests/test_capture_catalog_source_register_test_boundary.py`,
  `tests/test_architecture_quality.py`,
  `config/architecture_large_file_inventory_v1.json`, and
  `docs/architecture_contract.toml`.
- Closeout truth:
  the six oversized capture/catalog/source-register owners are now thin public facades over
  explicit sibling owner modules; the new boundary test fails closed on the exact source-family
  roster plus per-file budgets; the oversized-file inventory no longer tracks this family; and
  `tests/test_architecture_quality.py` now ratchets the live oversized queue at `4` files.
- Debt-shift audit:
  the largest new sibling files are
  `catalog.py=782`,
  `source_register_proving.py=741`,
  `source_register.py=729`,
  `catalog_outputs.py=723`,
  `authority_currentness.py=670`, and
  `download.py=616`; none reopened the oversized queue, created an import cycle, or exceeded the
  fan-out gate.
- Live architecture truth:
  the fresh architecture probe now reports `445` code files, `4` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, and top
  overall hotspot `tests/test_compliance_review.py` at score `35420`. The largest remaining
  oversized source owner is `src/usfs_r1_ea_sources/compliance_review_eval.py` at `1714` lines.
- Next routing:
  keep the broader repo default route on
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; when the under-`800`
  architecture queue resumes, continue at Milestone `7` in
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.

## Under-800 Hotspot Reduction Milestone 5

Latest implementation on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `5`; the extraction, retrieval, and review-artifact owner family is now
  closed under the `800`-line gate, and the packet advances to Milestone `6`.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/extract.py`,
  the new `src/usfs_r1_ea_sources/extract_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/retrieval.py`,
  the new `src/usfs_r1_ea_sources/retrieval*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/final_qa_certification.py`,
  the new `src/usfs_r1_ea_sources/final_qa_certification*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/draft_generation.py`,
  the new `src/usfs_r1_ea_sources/draft_generation*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/review_packet_index.py`,
  the new `src/usfs_r1_ea_sources/review_packet_index*.py` sibling owner modules,
  `tests/test_extract_test_boundary.py`,
  `tests/test_retrieval_test_boundary.py`,
  `tests/test_final_qa_certification_test_boundary.py`,
  `tests/test_draft_generation_test_boundary.py`,
  `tests/test_review_packet_index_test_boundary.py`,
  `tests/test_architecture_quality.py`,
  `config/architecture_large_file_inventory_v1.json`, and
  `docs/architecture_contract.toml`.
- Closeout truth:
  the five oversized extraction/retrieval/review owners are now thin public facades over explicit
  sibling owner modules; the new boundary tests fail-close on exact source-family rosters plus
  per-file budgets; the oversized-file inventory no longer tracks this family; and
  `tests/test_architecture_quality.py` now ratchets the live oversized queue at `10` files.
- Debt-shift audit:
  the largest new sibling files are
  `extract_runtime.py=796`,
  `final_qa_certification_validation.py=741`,
  `final_qa_certification_report.py=627`,
  `draft_generation_outputs.py=604`,
  `review_packet_index_inventory.py=545`, and
  `review_packet_index_outputs.py=542`; none reopened the oversized queue, created an import cycle,
  or exceeded the fan-out gate.
- Live architecture truth:
  the fresh architecture probe now reports `437` code files, `10` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, and top
  overall hotspot `tests/test_compliance_review.py` at score `35420`. The largest remaining
  oversized source owner is `src/usfs_r1_ea_sources/catalog.py` at `1496` lines.
- Next routing:
  keep the broader repo default route on
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; when the under-`800`
  architecture queue resumes, continue at Milestone `6` in
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.

## Under-800 Hotspot Reduction Milestone 4

Latest implementation on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `4`; the forest-plan runtime owner family is now closed under the
  `800`-line gate, and the packet advances to Milestone `5`.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/forest_plan_components.py`,
  the new `src/usfs_r1_ea_sources/forest_plan_components_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/forest_plan_resolver.py`,
  the new `src/usfs_r1_ea_sources/forest_plan_resolver_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/forest_plan_source_delta_readiness.py`,
  the new `src/usfs_r1_ea_sources/forest_plan_source_delta_readiness_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/forest_plan_component_adjudication.py`,
  the new `src/usfs_r1_ea_sources/forest_plan_component_adjudication_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/forest_plan_component_eval.py`,
  the new `src/usfs_r1_ea_sources/forest_plan_component_eval_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/rule_packs.py`,
  `tests/test_forest_plan_components_test_boundary.py`,
  `tests/test_forest_plan_resolver_test_boundary.py`,
  `tests/test_architecture_quality.py`,
  `config/architecture_large_file_inventory_v1.json`, and
  `docs/architecture_contract.toml`.
- Closeout truth:
  the five oversized forest-plan runtime owners are now thin public facades over explicit sibling
  modules; every new family file is `<=800` lines; the component and resolver boundary tests now
  fail-close on exact source rosters plus per-file budgets; the oversized-file inventory no longer
  tracks the forest-plan runtime family; and `rule_packs.py` now preserves the
  `aliased_source_record_ids` compatibility import used by CLI-bound component/adjudication tests.
- Debt-shift audit:
  the largest new forest-plan sibling files are
  `forest_plan_component_eval_coverage.py=764`,
  `forest_plan_source_delta_readiness_readiness.py=676`, and
  `forest_plan_components_inventory_quality.py=672`; none reopened the oversized queue, created an
  import cycle, or exceeded the fan-out gate.
- Live architecture truth:
  the fresh architecture probe now reports `409` code files, `15` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, and top
  hotspot `src/usfs_r1_ea_sources/extract.py` at score `57060`.
- Next routing:
  keep the broader repo default route on
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; when the under-`800`
  architecture queue resumes, continue at Milestone `5` in
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.

## Under-800 Hotspot Reduction Milestone 3

Latest implementation on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `3`; the knowledge-graph and decision-support owner family is now closed
  under the `800`-line gate, and the packet advances to Milestone `4`.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/nepa_3d_graph_contract.py`,
  the new `src/usfs_r1_ea_sources/nepa_3d_graph_contract_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`,
  the new `src/usfs_r1_ea_sources/nepa_knowledge_graph_export_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`,
  the new `src/usfs_r1_ea_sources/ea_consistency_decision_support_*.py` sibling owner modules,
  `src/usfs_r1_ea_sources/rule_packs.py`,
  `tests/test_nepa_knowledge_graph_export_test_boundary.py`,
  `tests/test_ea_consistency_decision_support_test_boundary.py`,
  `tests/test_architecture_quality.py`, and
  `docs/architecture_contract.toml`.
- Closeout truth:
  `nepa_3d_graph_contract.py`, `nepa_knowledge_graph_export.py`, and
  `ea_consistency_decision_support.py` are now thin public facades over explicit owner modules for
  contract models and validation, export/runtime/overlay/readiness concerns, and decision-support
  inputs/report/rendering/runtime seams. The family boundary tests now check exact rosters plus
  per-file budgets so the hotspot cannot regrow in a hidden sibling while the architecture
  contract owns the new first-class modules directly.
- Live architecture truth:
  the fresh architecture probe now reports `377` code files, `20` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, and top
  hotspot `src/usfs_r1_ea_sources/forest_plan_components.py` at score `77022`.
- Next routing:
  keep the broader repo default route on
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; when the under-`800`
  architecture queue resumes, continue at Milestone `4` in
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.

## Full Canonical Compliance Gold Rebaseline Milestones 0 Through 3 Slice

Latest implementation on 2026-05-21:

- Routed implementation packet:
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`.
- Outcome label:
  Milestone `0` freshness lock is resolved, Milestone `1` owner-family split
  is resolved, Milestone `2` is reduced again, and the closeout for this
  reduced slice is complete; the packet remains active on Milestone `2`.
- Implementation surfaces:
  `config/compliance_gold_eval_v1.json`,
  `src/usfs_r1_ea_sources/claim_extraction_runtime.py`,
  `src/usfs_r1_ea_sources/claim_extraction_validation.py`,
  `src/usfs_r1_ea_sources/compliance_review_eval.py`,
  `tests/test_claim_extraction.py`, and
  `tests/test_compliance_review_eval.py`.
- Runtime repair:
  claim extraction now applies a role-scoped duty-list pattern for
  `agency_policy` and `state_requirement` chunks, which restores normative
  Montana SHPO claims without broadening unsupported patterns. In the gold-eval
  layer, `compliance_review_eval.py` now merges generated source-claim-link
  expectations from the effective case map instead of the pre-merge case map
  and no longer synthesizes blanket positive source-claim-link expectations for
  every generated `uncertain` rule. `config/compliance_gold_eval_v1.json` now
  declares explicit generated source-claim-link positives only for
  `land_exchange_statutory_authorities_authority_template` and
  `region1_forest_plan_source_records_authority_template`, which are the only
  generated authority-template rules that resolve live links in the active
  replay.
- Fresh claim-extraction truth:
  `claim-extract --source-set-id source-set-f775524ab233ff27` now records
  `claim_count=122655`, `source_record_count=548`,
  `document_role_counts.state_requirement=298`,
  `validation_passed=true`, and `reviewer_ready=true`.
  `STP-026` now emits `6` claims, including the Montana SHPO duty statements
  that had been missing from the live source-claim surface.
- Fresh isolated replay truth:
  `compliance-gold-eval --results-dir source_library/reviews/compliance_gold_eval_seq52_fix6`
  still fails closed at `0/14` passed cases, but the earlier generated
  source-claim-link drift is gone. The replay records
  `authority_trace_coverage_rate=1.0`; `gold-all-authorities-supported` still
  scores `39` live `pass` findings and `20` `uncertain` findings, and its
  generated diagnostic rule-claim surface now records `rule_claim_link_count=200`.
- Artifact alignment truth:
  the base `nepa-ea-v0` rule-claim-link summary still records `link_count=0`
  and remains a separate zero-link structural surface, but the generated
  diagnostic gold rule packs now emit non-zero rule-claim-link artifacts under
  `source_library/derived/source-set-f775524ab233ff27/rule_claim_links/generated-diagnostic-*/`.
  For example, the generated diagnostic all-authorities-supported summary now
  records `link_count=200`, `source_record_count=32`, and `linked_rule_count=41`, so the packet
  remains routed on five still-unmapped live authorities rather than a hidden generated-link
  collapse.
- Residual owner truth:
  the only remaining status / claim-type / source-evidence / source-claim-link /
  source-record / source-document-role mismatches are the five authorities with
  no current canonical row:
  `apa_final_agency_action`,
  `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`,
  `organic_act_16usc_475`, and
  `seven_county_nepa_scope`.
- Bounded aggregate truth:
  `gold_coverage_eval_seq52_fix6` stays red only because
  `compliance_gold_failed=1`; it still records `required_theme_count=7`,
  `passed_theme_count=7`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_review_count=2`, and
  `typed_blocked_review_count=1` with no threshold failures.
- Next routing:
  keep the same packet active on Milestone `2`, with the remaining owner
  surface now narrowed to five unmapped live authorities rather than the
  earlier applicability abort, broad source-ID mismatch, or review-time
  generated-link expectation drift.

## Under-800 Hotspot Reduction Milestone 2

Latest closeout on 2026-05-21:

- Routed implementation packet:
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone `2`; the Project SOW owner family is now closed under the `800`-line
  gate, and the packet advances to Milestone `3`.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/project_sow_package.py`,
  the new `src/usfs_r1_ea_sources/project_sow_package_*.py` sibling owner modules,
  `tests/test_project_sow_package_test_boundary.py`,
  `tests/test_architecture_quality.py`, and
  `docs/architecture_contract.toml`.
- Closeout truth:
  `project_sow_package.py` is now a `71`-line public facade over explicit owner modules for
  intake, validation, graph assembly, rendering, package assembly, eval, operational gate,
  adjudication, and EA handoff. The Project SOW boundary test now checks the exact family module
  roster plus per-file budgets so the hotspot cannot regrow as a hidden sibling.
- Live architecture truth:
  the fresh architecture probe now reports `357` code files, `23` code files above `800`, no
  Python or JS/TS import cycles, no local module above the `20`-import fan-out gate, and top
  hotspot `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py` at score `77392`.
- Next routing:
  keep the broader repo default route on
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`; when the under-`800`
  architecture queue resumes, continue at Milestone `3` in
  `docs/UNDER_800_HOTSPOT_REDUCTION_MILESTONE_PLAN.md`.

## Overall Architecture Refactor Milestone 10 Sequence 52

Latest closeout on 2026-05-21:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 10; sequence 52 closes the architecture umbrella on truthful routed
  docs, live architecture proof, and explicit residual rerouting instead of leaving the remaining
  full-canonical gold regression implicit inside the architecture packet.
- Implementation surfaces:
  `config/v1_west_reservoir_real_ea_eval.json`,
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`,
  `README.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/AGENT_START_HERE.md`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `tests/test_v1_ea_eval_contracts.py`.
- Architecture closeout:
  the fresh architecture probe still reports `344` code files, `24` files above `800`, no Python
  or JS/TS import cycles, no local module above the `20`-import fan-out gate, and no
  `tests/` or `tests/support/` owner above the `800`-line reviewability gate.
- Full-canonical gold rebaseline evidence:
  an isolated `compliance-gold-eval` replay against the active local catalog
  `source-set-f775524ab233ff27` finished red with `passed_case_count=0`,
  `failed_case_count=14`, and `failure_category_counts={"rule_claim_binding_miss": 14,
  "rule_wording_issue": 14, "source_applicability_miss": 14, "source_retrieval_miss": 14}`
  even though the required coverage tags and package-style tags were present.
- Bounded aggregate truth:
  a bounded `gold-coverage-eval` replay against fresh applicability results, the isolated red
  compliance-gold result, and the fresh tracked review-contract aggregate remains red only because
  `compliance_gold.passed=false`; the aggregate still records `required_theme_count=7`,
  `passed_theme_count=7`, `distinct_forest_count=2`, `distinct_package_style_count=3`,
  `reviewer_ready_review_count=2`, and `typed_blocked_review_count=1` with no threshold failures.
- Next routing:
  the overall architecture umbrella is complete. Advance the remaining live red lane to
  `docs/FULL_CANONICAL_COMPLIANCE_GOLD_REBASELINE_MILESTONE_PLAN.md`.

## Overall Architecture Refactor Milestone 9 Sequence 51

Latest closeout on 2026-05-21:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 9; sequence 51 explicitly retires the stale West Reservoir
  reviewer-ready replay claim behind a machine-checked typed-blocked contract and advances the
  umbrella route to Milestone 10.
- Implementation surfaces:
  `config/v1_west_reservoir_real_ea_eval.json`,
  `config/v1_real_package_review_coverage_v1.json`,
  `config/gold_coverage_v1.json`,
  `config/promotion_suite_v1.json`,
  `README.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/AGENT_START_HERE.md`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/EVALUATION_COVERAGE_REGISTER.md`,
  `docs/OUTPUT_SCHEMAS.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`,
  `tests/test_real_package_review_coverage_eval.py`,
  `tests/test_gold_coverage_eval.py`,
  `tests/test_promotion_suite.py`, and
  `tests/test_v1_ea_eval_contracts.py`.
- Quarantine closeout:
  `v1-ea-eval --review-id west-reservoir-67436` now passes as `contract_status="typed_blocked"`
  with the live blocker categories
  `review_artifact_missing`, `forest_plan_matrix_miss`, `forest_plan_reviewer_not_ready`, and
  `forest_plan_scope_miss` explicitly declared in the committed contract.
- Aggregate coverage closeout:
  the shipped real-package and gold coverage manifests now require `2` reviewer-ready tracked
  reviews plus `1` typed-blocked tracked review, so the aggregate gates reflect the live replayable
  state instead of the stale `3` reviewer-ready claim.
- Next routing:
  Milestone 9 is complete. Advance the same umbrella packet to Milestone 10 on the final
  architecture rebaseline and debt-shift closeout.

## Overall Architecture Refactor Milestone 9 Sequence 50

Latest closeout on 2026-05-21:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 9; sequence 50 removes the tracked user-home replay-context path and
  adds a short current-routing surface, but the broader West Reservoir review-contract replay is
  still not reproducible from current repo-local evidence.
- Implementation surfaces:
  `config/replay_contexts/west-reservoir-67436.json`,
  `docs/CURRENT_ROUTING.md`,
  `README.md`,
  `docs/AGENT_START_HERE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `tests/test_architecture_quality.py`.
- Hermeticity closeout:
  West Reservoir replay-context package authority now points at
  `source_library/reviews/west-reservoir-67436/package` instead of a user-home path;
  `real-package-review-coverage-eval` no longer fails on missing package authority for West
  Reservoir, and the remaining failure is the stale broader-EA contract mismatch.
- Cold-start routing closeout:
  `docs/CURRENT_ROUTING.md` is now the concise first stop for active workbook, catalog, and
  architecture routing; `README.md` and `docs/AGENT_START_HERE.md` now route through it before the
  larger current-state and handoff docs.
- Live probe evidence:
  the fresh architecture probe still reports `344` code files, `24` files above `800`, no local
  module above the `20`-import fan-out gate, and no Python or JS/TS import cycles.
- Residual system state:
  `v1-ea-eval --review-id west-reservoir-67436` still fails on missing
  `authority_explanation_paths.json`; a cache-backed `compliance-review` reentry using the repo
  package cache is blocked because archived `source-set-5e65d845ce77e1a0` no longer has a
  reviewer-ready retrieval index in this checkout.
- Next routing:
  keep Milestone 9 active on restoring or explicitly retiring that stale West Reservoir
  broader-EA contract before Milestone 10 rebaseline.

## Overall Architecture Refactor Milestone 8 Sequence 49

Latest closeout on 2026-05-21:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 8; sequence 49 closes the remaining documentation and routing drift
  after the Sequence 48 test-owner split.
- Implementation surfaces:
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`, and
  `docs/SESSION_HANDOFF.md`.
- Documentation alignment closeout:
  the umbrella plan weak-point register, current-system-state route, and canonical handoff now
  agree that the oversized test/support owner packet is complete and that the next routed
  architecture slice is Milestone 9 on the West Reservoir user-home proving dependency plus
  cold-start doc routing drift.
- Debt-shift audit:
  the fresh architecture probe reports `344` code files, `24` files above `800`, top hotspot
  `src/usfs_r1_ea_sources/project_sow_package.py` at score `104370`, no remaining modules above
  the `20`-import fan-out gate, and no Python or JS/TS import cycles; no `tests/` or
  `tests/support/` owner remains above the `800`-line reviewability gate.
- Residual system state:
  runtime behavior is unchanged in this slice; the work closes stale architecture/doc routing only.
- Next routing:
  Milestone 8 is complete. Advance the same umbrella packet to Milestone 9 on the West Reservoir
  user-home proving dependency plus cold-start doc routing drift.

## Overall Architecture Refactor Milestone 6 Sequence 24

Latest closeout on 2026-05-21:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 6; sequence 24 closes the remaining `applicability_eval`
  owner family and completes the broader applicability/evidence hotspot packet.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_eval.py`,
  `src/usfs_r1_ea_sources/applicability_eval_runtime.py`,
  `src/usfs_r1_ea_sources/applicability_eval_authority_universe.py`,
  `src/usfs_r1_ea_sources/applicability_eval_fixture_runtime.py`,
  `src/usfs_r1_ea_sources/applicability_eval_scoring.py`,
  `src/usfs_r1_ea_sources/applicability_eval_summary.py`,
  `src/usfs_r1_ea_sources/applicability_eval_gold.py`,
  `src/usfs_r1_ea_sources/applicability_eval_support.py`,
  `src/usfs_r1_ea_sources/gold_coverage_eval.py`,
  `tests/test_applicability_eval.py`,
  `tests/test_gold_coverage_eval.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/architecture_contract.toml`, and
  `tests/test_architecture_quality.py`.
- Eval owner split closeout:
  `applicability_eval_runtime.py` now owns deterministic applicability-eval orchestration and
  adjudication-apply flow; `applicability_eval_authority_universe.py` now owns eval-scoped
  authority-universe fixture assembly and template/rule selection;
  `applicability_eval_fixture_runtime.py` now owns package/source fixture materialization;
  `applicability_eval_scoring.py` now owns case rescoring, artifact rereads, retrieval/graph
  alignment, and generated-rule-pack identity checks; `applicability_eval_summary.py` now owns
  aggregate arbitration and authority-family coverage summaries; and
  `applicability_eval_gold.py` now owns adjudicated gold-eval contract checks.
- Facade-preserving routing:
  `applicability_eval.py` now keeps the public defaults, result types, eval runners, and
  compatibility re-exports used by CLI, gold coverage, and the existing test surface.
- Direct contract coverage:
  `tests/test_applicability_eval.py` and `tests/test_gold_coverage_eval.py` still verify the
  public applicability/gold eval surfaces end to end after the split.
- Live probe evidence:
  the fresh architecture probe reports `259` code files, `46` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_eval.py` reduced to `32` lines from the pre-sequence `2655`-line
  baseline, `applicability_eval_runtime.py` at `373` lines,
  `applicability_eval_authority_universe.py` at `653` lines,
  `applicability_eval_fixture_runtime.py` at `261` lines,
  `applicability_eval_scoring.py` at `767` lines,
  `applicability_eval_summary.py` at `149` lines,
  `applicability_eval_gold.py` at `498` lines,
  `applicability_eval_support.py` at `197` lines, and one allowed fan-out hotspot at
  `cli_derived=22`.
- Next routing:
  Milestone 6 is complete. Advance to Milestone 7 on `phase_eval.py`; do not reopen the
  applicability/evidence hotspot packet unless a fresh downstream gap appears.

## Overall Architecture Refactor Milestone 6 Sequence 23

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 23 closes the `applicability-rule-pack-support`,
  `applicability-rule-pack-runtime`, and `applicability-rule-pack-validation` owner seams and
  closes the downstream final-QA/phase-eval replay-contract gap exposed by the split, but the
  broader applicability/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_rule_pack.py`,
  `src/usfs_r1_ea_sources/applicability_rule_pack_support.py`,
  `src/usfs_r1_ea_sources/applicability_rule_pack_runtime.py`,
  `src/usfs_r1_ea_sources/applicability_rule_pack_validation.py`,
  `src/usfs_r1_ea_sources/final_qa_certification.py`,
  `src/usfs_r1_ea_sources/phase_eval_optional_phases.py`,
  `tests/support/compliance_phase_eval_fixtures.py`,
  `tests/support/compliance_phase_eval_contracts.py`,
  `tests/test_compliance_phase_eval.py`,
  `tests/test_applicability_rule_pack_runtime.py`,
  `tests/test_applicability_rule_pack_validation.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/architecture_contract.toml`, and
  `tests/test_architecture_quality.py`.
- Support, runtime, and validation seam closeout:
  `applicability_rule_pack_support.py` now owns rule-pack artifact paths, IO, identity helpers,
  and validation-hash support; `applicability_rule_pack_runtime.py` now owns deterministic
  generated-rule-pack assembly and rule applicability metadata shaping;
  `applicability_rule_pack_validation.py` now owns required-artifact checks, validation/hash
  freshness checks, generated-rule metadata validation, and trace/readiness checks; and
  `applicability_rule_pack.py` now keeps the public generate/validate facade.
- Direct contract coverage:
  `tests/test_applicability_rule_pack_runtime.py` and
  `tests/test_applicability_rule_pack_validation.py` now pin the extracted seams directly, while
  `tests/test_applicability_decisions.py` still verifies generated-rule-pack behavior end to end.
- Downstream replay-contract closeout:
  `phase_eval_optional_phases.py` now validates final-QA packets against the contract paths
  recorded inside the packet instead of hard-coding the canonical East Crazies fixture contract,
  `final_qa_certification.py` now exposes that contract-path inference explicitly, and the
  compliance phase-eval fixture support is split across
  `tests/support/compliance_phase_eval_fixtures.py` and
  `tests/support/compliance_phase_eval_contracts.py` so the synthetic review lane generates
  replayable decision-support and final-QA packets without creating a new `>800`-line test owner.
- Live probe evidence:
  the fresh architecture probe reports `252` code files, `47` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_rule_pack.py` reduced to `331` lines from the pre-sequence
  `1440`-line baseline, `applicability_rule_pack_support.py` at `219` lines,
  `applicability_rule_pack_runtime.py` at `363` lines,
  `applicability_rule_pack_validation.py` at `581` lines,
  `tests/support/compliance_phase_eval_fixtures.py` reduced to `672` lines after splitting out
  `tests/support/compliance_phase_eval_contracts.py` at `761` lines,
  `tests/test_applicability_rule_pack_runtime.py` at `122` lines, and
  `tests/test_applicability_rule_pack_validation.py` at `80` lines.
- Next routing:
  continue inside Milestone 6 on `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 22

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 22 closes the `applicability-retrieval-runtime` and
  `applicability-retrieval-graph` owner seams, but the broader applicability/evidence hotspot
  family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_retrieval.py`,
  `src/usfs_r1_ea_sources/applicability_retrieval_runtime.py`,
  `src/usfs_r1_ea_sources/applicability_retrieval_graph.py`,
  `tests/test_applicability_retrieval_runtime.py`,
  `tests/test_applicability_retrieval_graph.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/architecture_contract.toml`, and
  `tests/test_architecture_quality.py`.
- Runtime and graph seam closeout:
  `applicability_retrieval_runtime.py` now owns deterministic query planning and execution,
  source/package result rows, fusion, and query helpers; `applicability_retrieval_graph.py` now
  owns bounded graph expansion and graph trace assembly; `applicability_retrieval.py` now keeps
  the public retrieval-trace facade plus validation, diagnostics, summary assembly, artifact IO,
  and identity helpers.
- Direct contract coverage:
  `tests/test_applicability_retrieval_runtime.py` and `tests/test_applicability_retrieval_graph.py`
  now pin the extracted seams directly, while `tests/test_applicability_retrieval.py` still
  verifies the public retrieval-trace build workflow end to end.
- Live probe evidence:
  the fresh architecture probe reports `246` code files, `48` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_retrieval.py` reduced to `589` lines from the pre-sequence
  `1741`-line baseline, `applicability_retrieval_runtime.py` at `704` lines,
  `applicability_retrieval_graph.py` at `479` lines,
  `tests/test_applicability_retrieval_runtime.py` at `134` lines, and
  `tests/test_applicability_retrieval_graph.py` at `113` lines.
- Next routing:
  continue inside Milestone 6 on `applicability_rule_pack.py`, then `applicability_eval.py`. Do
  not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 21

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 21 closes the `package-fact-runtime` owner seam, but the
  broader claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/package_fact_graph.py`,
  `src/usfs_r1_ea_sources/package_fact_graph_runtime.py`,
  `src/usfs_r1_ea_sources/package_fact_graph_terms.py`,
  `tests/test_package_fact_graph_runtime.py`,
  `tests/test_package_fact_graph_terms.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/architecture_contract.toml`, and
  `tests/test_architecture_quality.py`.
- Runtime seam closeout:
  `package_fact_graph_runtime.py` now owns deterministic package-fact extraction, node and edge
  assembly, uncertainty-record construction, section/runtime helpers, and extraction-summary
  assembly; `package_fact_graph_terms.py` now owns deterministic term specifications,
  profile-derived term expansion, extraction-method constants, and term deduplication support;
  `package_fact_graph.py` now keeps the public package-fact facade plus validation, context
  assembly, source-package metadata, and artifact IO.
- Direct contract coverage:
  `tests/test_package_fact_graph_runtime.py` and `tests/test_package_fact_graph_terms.py` now pin
  the extracted seams directly, while `tests/test_package_fact_graph.py` still verifies the public
  package-fact build workflow end to end.
- Live probe evidence:
  the fresh architecture probe reports `242` code files, `49` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `package_fact_graph.py` reduced to `597` lines from the pre-sequence `1469`-line
  baseline, `package_fact_graph_runtime.py` at `610` lines, `package_fact_graph_terms.py` at
  `534` lines, `tests/test_package_fact_graph_runtime.py` at `124` lines, and
  `tests/test_package_fact_graph_terms.py` at `21` lines.
- Next routing:
  continue inside Milestone 6 on `applicability_retrieval.py`, then `applicability_rule_pack.py`,
  and `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 20

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 20 closes the `evidence-graph-validation` owner seam, but
  the broader claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/evidence_graph.py`,
  `src/usfs_r1_ea_sources/evidence_graph_validation.py`,
  `tests/test_evidence_graph_validation.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/architecture_contract.toml`, and
  `tests/test_architecture_quality.py`.
- Validation seam closeout:
  `evidence_graph_validation.py` now owns retrieval-index readability, validation-report assembly,
  chunk/retrieval binding checks, graph-integrity and graph-health checks, review-topic and
  evidence-span checks, replay-path resolution, and sqlite graph validation support;
  `evidence_graph.py` now keeps the public evidence-graph facade plus the graph build/runtime,
  source metadata enrichment, metrics, sqlite write, and graph identity helpers.
- Direct contract coverage:
  `tests/test_evidence_graph_validation.py` now pins the extracted validation seam directly, while
  `tests/test_evidence_graph.py` still verifies the public evidence-graph build workflow end to
  end.
- Live probe evidence:
  the fresh architecture probe reports `238` code files, `50` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `evidence_graph.py` reduced to `758` lines from the pre-sequence `1205`-line
  baseline, `evidence_graph_validation.py` at `640` lines, `tests/test_evidence_graph.py` at
  `364` lines, and `tests/test_evidence_graph_validation.py` at `110` lines.
- Next routing:
  continue inside Milestone 6 on `package_fact_graph.py`, then `applicability_retrieval.py`,
  `applicability_rule_pack.py`, and `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 19

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 19 closes the `rule-claim-runtime` owner seam, but the
  broader claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/rule_claim_binding.py`,
  `src/usfs_r1_ea_sources/rule_claim_binding_runtime.py`,
  `src/usfs_r1_ea_sources/rule_claim_binding_validation.py`,
  `tests/test_rule_claim_binding_runtime.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/architecture_contract.toml`, and
  `tests/test_architecture_quality.py`.
- Runtime seam closeout:
  `rule_claim_binding_runtime.py` now owns deterministic rule-query assembly, filter matching,
  scoring, link/gap record construction, safe path-segment validation, and deterministic
  link/gap identity helpers; `rule_claim_binding.py` now keeps the public rule-claim facade plus
  sqlite-write and artifact-readiness support.
- Direct contract coverage:
  `tests/test_rule_claim_binding_runtime.py` now pins the extracted runtime seam directly, while
  `tests/test_rule_claim_binding.py` still verifies the public rule-claim build and eval workflow
  end to end.
- Live probe evidence:
  the fresh architecture probe reports `236` code files, `51` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `rule_claim_binding.py` reduced to `508` lines from the post-sequence-18 `849`-line
  baseline and the pre-sequence `2017`-line baseline, `rule_claim_binding_runtime.py` at `349`
  lines, `rule_claim_binding_validation.py` at `592` lines, `tests/test_rule_claim_binding.py` at
  `600` lines, and `tests/test_rule_claim_binding_runtime.py` at `172` lines.
- Next routing:
  continue inside Milestone 6 on `evidence_graph.py`, then `package_fact_graph.py`,
  `applicability_retrieval.py`, `applicability_rule_pack.py`, and `applicability_eval.py`. Do not
  advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 18

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 18 closes the `rule-claim-validation` owner seam, but the
  broader claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/rule_claim_binding.py`,
  `src/usfs_r1_ea_sources/rule_claim_binding_validation.py`,
  `tests/test_rule_claim_binding.py`,
  `tests/test_rule_claim_binding_validation.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Validation seam closeout:
  `rule_claim_binding_validation.py` now owns rule-claim artifact validation, rule-pack and claim
  readiness checks, deterministic link/gap identity validation, provenance/filter/score/rank
  checks, and sqlite validation support; `rule_claim_binding.py` now keeps the public rule-claim
  facade plus the remaining rule-matching and build core.
- Direct contract coverage:
  `tests/test_rule_claim_binding_validation.py` now pins the extracted validation seam directly,
  while `tests/test_rule_claim_binding.py` still verifies the public rule-claim build and eval
  workflow end to end.
- Live probe evidence:
  the fresh architecture probe reports `234` code files, `52` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `rule_claim_binding.py` reduced to `849` lines from the post-sequence-17 `1360`-line
  baseline, `rule_claim_binding_validation.py` at `592` lines, `tests/test_rule_claim_binding.py`
  reduced to `600` lines, and `tests/test_rule_claim_binding_validation.py` at `163` lines.
- Next routing:
  continue inside Milestone 6 on the remaining `rule_claim_binding.py` build core, then
  `evidence_graph.py`, `package_fact_graph.py`, `applicability_retrieval.py`,
  `applicability_rule_pack.py`, and `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 17

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 17 closes the `rule-claim-eval` owner seam, but the broader
  claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/rule_claim_binding.py`,
  `src/usfs_r1_ea_sources/rule_claim_binding_eval.py`,
  `tests/test_rule_claim_binding_eval.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Eval seam closeout:
  `rule_claim_binding_eval.py` now owns deterministic rule-claim eval scoring, legacy/current eval
  contract loading, coverage and metric-threshold checks, and rule-claim readiness revalidation;
  `rule_claim_binding.py` now keeps the public rule-claim facade plus the remaining
  rule-matching and validation core.
- Direct contract coverage:
  `tests/test_rule_claim_binding_eval.py` now pins the extracted eval-contract, query/ranking, and
  readiness seam directly, while `tests/test_rule_claim_binding.py` still verifies the public
  rule-claim build, validation, and eval workflow end to end.
- Live probe evidence:
  the fresh architecture probe reports `232` code files, `52` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `rule_claim_binding.py` reduced to `1360` lines from the pre-sequence `2017`-line
  baseline, `rule_claim_binding_eval.py` at `708` lines, `tests/test_rule_claim_binding.py` at
  `753` lines, and `tests/test_rule_claim_binding_eval.py` at `178` lines.
- Next routing:
  continue inside Milestone 6 on the remaining `rule_claim_binding.py` build and validation core,
  then `evidence_graph.py`, `package_fact_graph.py`, `applicability_retrieval.py`,
  `applicability_rule_pack.py`, and `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 16

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 16 closes the `claim-runtime` owner seam, but the broader
  claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/claim_extraction.py`,
  `src/usfs_r1_ea_sources/claim_extraction_runtime.py`,
  `src/usfs_r1_ea_sources/claim_extraction_validation.py`,
  `tests/test_claim_extraction.py`,
  `tests/test_claim_extraction_runtime.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `claim_extraction_runtime.py` now owns deterministic claim-pattern definitions, sentence/window
  handling, claim record assembly, IDs/hashes, and extraction metrics; `claim_extraction.py` now
  keeps the public claim-extraction facade plus orchestration support.
- Direct contract coverage:
  `tests/test_claim_extraction_runtime.py` now pins the extracted runtime seam directly, while
  `tests/test_claim_extraction.py` still verifies the public claim-extraction workflow end to end.
- Live probe evidence:
  the fresh architecture probe reports `230` code files, `52` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `claim_extraction.py` reduced to `458` lines from the post-sequence-15 `783`-line
  baseline, `claim_extraction_runtime.py` at `342` lines, `claim_extraction_validation.py` at
  `614` lines, and `tests/test_claim_extraction.py` reduced to `712` lines.
- Next routing:
  continue inside Milestone 6 on `rule_claim_binding.py`, then `evidence_graph.py`,
  `package_fact_graph.py`, `applicability_retrieval.py`, `applicability_rule_pack.py`, and
  `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 15

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 15 closes the `claim-validation` owner seam, but the
  broader claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/claim_extraction.py`,
  `src/usfs_r1_ea_sources/claim_extraction_validation.py`,
  `tests/test_claim_extraction.py`,
  `tests/test_claim_extraction_validation.py`,
  `tests/test_architecture_quality.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `claim_extraction_validation.py` now owns claim-artifact validation, retrieval-index
  readability/loading, claim provenance/type/offset consistency checks, claim-graph integrity and
  health checks, and partial-retrieval gating; `claim_extraction.py` now keeps the public
  claim-extraction facade plus the remaining extraction core.
- Direct contract coverage:
  `tests/test_claim_extraction_validation.py` now pins the extracted validation seam directly,
  while `tests/test_claim_extraction.py` still verifies the public claim-extraction workflow end
  to end.
- Live probe evidence:
  the fresh architecture probe reports `228` code files, `52` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `claim_extraction.py` reduced to `783` lines from the post-sequence-14 `1328`-line
  baseline, `claim_extraction_validation.py` at `617` lines, and
  `tests/test_claim_extraction.py` reduced to `781` lines.
- Next routing:
  continue inside Milestone 6 on the remaining claim extraction core in `claim_extraction.py`,
  then `rule_claim_binding.py`, `evidence_graph.py`, `package_fact_graph.py`,
  `applicability_retrieval.py`, `applicability_rule_pack.py`, and `applicability_eval.py`.
  Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 14

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 14 closes the `claim-eval` owner seam, but the broader
  claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/claim_extraction.py`,
  `src/usfs_r1_ea_sources/claim_extraction_eval.py`,
  `tests/test_claim_extraction.py`,
  `tests/test_claim_extraction_eval.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `claim_extraction_eval.py` now owns deterministic claim eval scoring, legacy/current eval
  contract loading, coverage and metric-threshold checks, and claim-readiness revalidation;
  `claim_extraction.py` now keeps the public claim-extraction facade plus the remaining claim
  extraction and validation core, and re-exports the readiness helper still used by
  `rule_claim_binding.py`.
- Direct contract coverage:
  `tests/test_claim_extraction_eval.py` now pins the extracted eval-contract and query/ranking seam
  directly, while `tests/test_claim_extraction.py` still verifies the public claim-extraction and
  claim-eval behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `226` code files, `54` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `claim_extraction.py` reduced to `1328` lines from the post-sequence-13 `2084`-line
  baseline, and `claim_extraction_eval.py` lands at the `800`-line gate.
- Next routing:
  continue inside Milestone 6 on the remaining claim extraction and validation core in
  `claim_extraction.py`, then `rule_claim_binding.py`, `evidence_graph.py`,
  `package_fact_graph.py`, `applicability_retrieval.py`, `applicability_rule_pack.py`, and
  `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 13

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 13 closes the first `claim_extraction.py` graph-owner
  seam, but the broader claims/evidence hotspot family remains active.
- Sequence 13 closeout commit:
  `a3363ca` (`Reduce architecture refactor Milestone 6 claim-graph seam`).
- Implementation surfaces:
  `src/usfs_r1_ea_sources/claim_extraction.py`,
  `src/usfs_r1_ea_sources/claim_extraction_graph.py`,
  `tests/test_claim_extraction.py`,
  `tests/test_claim_extraction_graph.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `claim_extraction_graph.py` now owns entity extraction and aggregation, claim graph
  node/edge assembly, and claim-graph SQLite writer/checks; `claim_extraction.py` now keeps the
  public claim-extraction facade plus the remaining claim extraction, validation, and eval core.
- Direct contract coverage:
  `tests/test_claim_extraction_graph.py` now pins the extracted claim-graph seam directly, while
  `tests/test_claim_extraction.py` still verifies the public claim-extraction workflow end to end.
- Live probe evidence:
  the fresh architecture probe reports `224` code files, `54` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `claim_extraction.py` reduced to `2084` lines from the pre-sequence `2503`-line
  baseline, and the new `claim_extraction_graph.py` seam remains below the `800`-line gate at
  `457` lines.
- Next routing:
  continue inside Milestone 6 on the remaining claim extraction, validation, and eval core in
  `claim_extraction.py`, then `rule_claim_binding.py`, `evidence_graph.py`,
  `package_fact_graph.py`, `applicability_retrieval.py`, `applicability_rule_pack.py`, and
  `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 12

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 12 closes the remaining applicability validation
  artifact/freshness/provenance seam, but the broader claims/evidence hotspot family remains
  active.
- Sequence 12 closeout commit:
  `46d0d6b` (`Reduce architecture refactor Milestone 6 validation-facade seam`).
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_validation.py`,
  `src/usfs_r1_ea_sources/applicability_validation_artifacts.py`,
  `src/usfs_r1_ea_sources/applicability_validation_freshness.py`,
  `tests/test_applicability_validation_artifacts.py`,
  `tests/test_applicability_validation_checks.py`,
  `tests/test_applicability_decisions.py`,
  `tests/test_applicability_adjudication.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_validation_artifacts.py` now owns validation artifact-path resolution,
  artifact loading, artifact-hash summary assembly, and source-set/run-id inference;
  `applicability_validation_freshness.py` now owns artifact-freshness and provenance validation;
  and `applicability_validation.py` is now a thin public validation facade.
- Direct contract coverage:
  `tests/test_applicability_validation_artifacts.py` now pins the extracted artifact and
  freshness/provenance seams directly, while the existing applicability decision, adjudication, and
  validation-check tests still verify the public validation behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `222` code files, `54` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_validation.py` reduced to `178` lines from the post-sequence-11
  `607`-line baseline, and the new `applicability_validation_artifacts.py` and
  `applicability_validation_freshness.py` seams remain below the `800`-line gate at `173` and
  `304` lines.
- Next routing:
  continue inside Milestone 6 on the broader claims/evidence hotspot family, starting with
  `claim_extraction.py`, then `rule_claim_binding.py`, `evidence_graph.py`,
  `package_fact_graph.py`, `applicability_retrieval.py`, `applicability_rule_pack.py`, and
  `applicability_eval.py`. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 11

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 11 closes the applicability validation-check seam, but the
  broader applicability freshness/provenance plus claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_validation.py`,
  `src/usfs_r1_ea_sources/applicability_validation_checks.py`,
  `src/usfs_r1_ea_sources/applicability_validation_support.py`,
  `tests/test_applicability_validation_checks.py`,
  `tests/test_applicability_decisions.py`,
  `tests/test_applicability_adjudication.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_validation_checks.py` now owns the non-freshness validation check family,
  `applicability_validation_support.py` now owns shared validation helpers, and
  `applicability_validation.py` now keeps the remaining artifact-loading, artifact-freshness, and
  provenance facade.
- Direct contract coverage:
  `tests/test_applicability_validation_checks.py` now pins the extracted validation-check seam
  directly, while the existing applicability decision and adjudication tests still verify the
  public validation behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `219` code files, `54` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_validation.py` reduced to `607` lines from the post-sequence-10
  `1502`-line baseline, and the new `applicability_validation_checks.py` and
  `applicability_validation_support.py` seams remain below the `800`-line gate at `791` and `171`
  lines.
- Next routing:
  continue inside Milestone 6 on the remaining artifact-loading, artifact-freshness, and
  provenance core in `applicability_validation.py`, then the broader claims/evidence hotspot
  families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 10

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 10 closes the applicability adjudication seam, but the
  broader applicability validation plus claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_adjudication.py`,
  `src/usfs_r1_ea_sources/applicability_adjudication_apply.py`,
  `src/usfs_r1_ea_sources/applicability_validation.py`,
  `tests/test_applicability_adjudication.py`,
  `tests/test_applicability_decisions.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_adjudication.py` now owns adjudication template rendering plus adjudication
  evaluation/replayability checks, `applicability_adjudication_apply.py` now owns adjudication
  replay plus partition/report/provenance updates, and `applicability_validation.py` now keeps the
  remaining validation-check core.
- Direct contract coverage:
  `tests/test_applicability_adjudication.py` now pins the extracted adjudication seam directly,
  while the existing applicability decision tests still verify the public validation and
  adjudication behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `216` code files, `55` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_validation.py` reduced to `1502` lines from the pre-sequence
  `2494`-line baseline, and the new `applicability_adjudication.py` and
  `applicability_adjudication_apply.py` seams remain below the `800`-line gate at `740` and `443`
  lines.
- Next routing:
  continue inside Milestone 6 on the remaining validation-check, artifact-freshness, and
  provenance core in `applicability_validation.py`, then the broader claims/evidence hotspot
  families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 9

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 9 closes the applicability decision forest-plan predicate
  seam, but the broader applicability decision/validation plus claims/evidence hotspot family
  remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_decision_forest_plan.py`,
  `src/usfs_r1_ea_sources/applicability_decision_coverage.py`,
  `src/usfs_r1_ea_sources/applicability_decisions.py`,
  `tests/test_applicability_decision_forest_plan.py`,
  `tests/test_applicability_decision_coverage.py`,
  `tests/test_applicability_decisions.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_decision_forest_plan.py` now owns Forest Plan component predicate evaluation that
  previously remained inside `applicability_decisions.py`, while
  `applicability_decision_coverage.py` also owns candidate-row grouping support used by the public
  decision builder.
- Direct contract coverage:
  `tests/test_applicability_decision_forest_plan.py` now pins the extracted forest-plan predicate
  seam directly, while `tests/test_applicability_decision_coverage.py` also covers the moved
  candidate-row grouping helper and the existing decision tests still verify the public
  `build_applicability_decisions` behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `213` code files, `55` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_decisions.py` reduced to `793` lines from the earlier `916`-line
  post-sequence-8 baseline, and the new `applicability_decision_forest_plan.py` seam remains below
  the `800`-line gate at `128` lines.
- Next routing:
  continue inside Milestone 6 on `applicability_validation.py`, then the broader claims/evidence
  hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 8

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 8 closes the applicability decision-coverage seam, but the
  broader applicability decision/validation plus claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_decision_coverage.py`,
  `src/usfs_r1_ea_sources/applicability_decisions.py`,
  `tests/test_applicability_decision_coverage.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Sequence 8 closeout commit:
  `b316e20` (`Reduce architecture refactor Milestone 6 decision-coverage seam`).
- Runtime seam closeout:
  `applicability_decision_coverage.py` now owns search-coverage boundary evaluation plus
  search-coverage certificate assembly/rationale that previously remained inside
  `applicability_decisions.py`, while `applicability_decisions.py` keeps the public decision
  builder and the remaining forest-plan predicate core.
- Direct contract coverage:
  `tests/test_applicability_decision_coverage.py` now pins the extracted decision-coverage seam
  directly, while the existing applicability decision tests still verify the public
  `build_applicability_decisions` behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `211` code files, `56` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_decisions.py` reduced to `916` lines from the earlier `1123`-line
  post-sequence-7 baseline, and the new `applicability_decision_coverage.py` seam remains below
  the `800`-line gate at `219` lines.
- Next routing:
  continue inside Milestone 6 on the remaining forest-plan predicate core in
  `applicability_decisions.py`, then `applicability_validation.py`, and the broader claims/evidence
  hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 7

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 7 closes the applicability decision-evidence seam, but the
  broader applicability decision/validation plus claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_decision_evidence.py`,
  `src/usfs_r1_ea_sources/applicability_decisions.py`,
  `tests/test_applicability_decisions.py`,
  `tests/test_applicability_decision_evidence.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_decision_evidence.py` now owns trigger matching, evidence-span assembly,
  source-library evidence fallback, retrieval lineage support, and decision-evidence text/window
  helpers that previously remained inside `applicability_decisions.py`, while
  `applicability_decisions.py` keeps the public decision builder and the remaining
  coverage-certificate plus forest-plan predicate core.
- Direct contract coverage:
  `tests/test_applicability_decision_evidence.py` now pins the extracted decision-evidence seam
  directly, while the existing applicability decision tests still verify the public
  `build_applicability_decisions` behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `209` code files, `56` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_decisions.py` reduced to `1123` lines from the earlier `1710`-line
  post-sequence-6 baseline, and the new `applicability_decision_evidence.py` seam remains below
  the `800`-line gate at `590` lines.
- Next routing:
  continue inside Milestone 6 on the remaining coverage-certificate and forest-plan predicate core
  in `applicability_decisions.py`, then `applicability_validation.py`, and the broader
  claims/evidence hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 6

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 6 closes the applicability decision-arbitration seam, but
  the broader applicability decision/validation plus claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_decision_arbitration.py`,
  `src/usfs_r1_ea_sources/applicability_decisions.py`,
  `tests/test_applicability_decisions.py`,
  `tests/test_applicability_decision_arbitration.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_decision_arbitration.py` now owns trigger-group normalization, rule-contract
  arbitration, missing-trigger reporting, and arbitration summary/effect assembly that previously
  remained inside `applicability_decisions.py`, while `applicability_decisions.py` keeps the public
  decision builder and the remaining evidence-matching plus forest-plan/coverage predicate core.
- Direct contract coverage:
  `tests/test_applicability_decision_arbitration.py` now pins the extracted arbitration seam
  directly, while the existing applicability decision tests still verify the public
  `build_applicability_decisions` behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `207` code files, `56` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_decisions.py` reduced to `1710` lines from the earlier `2036`-line
  post-sequence-5 baseline, and the new `applicability_decision_arbitration.py` seam remains below
  the `800`-line gate at `349` lines.
- Next routing:
  continue inside Milestone 6 on the remaining evidence-matching, coverage-certificate, and
  forest-plan predicate core in `applicability_decisions.py`, then `applicability_validation.py`,
  and the broader claims/evidence hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 5

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 5 closes the applicability decision-output seam, but the
  broader applicability decision/validation plus claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability_decision_outputs.py`,
  `src/usfs_r1_ea_sources/applicability_decisions.py`,
  `src/usfs_r1_ea_sources/applicability_validation.py`,
  `tests/test_applicability_decisions.py`,
  `tests/test_applicability_decision_outputs.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_decision_outputs.py` now owns decision partition records, provenance payload
  assembly, summary aggregation, and applicability report rendering that previously remained inside
  `applicability_decisions.py`, while `applicability_decisions.py` keeps the public decision
  builder and predicate engine.
- Direct contract coverage:
  `tests/test_applicability_decision_outputs.py` now pins the extracted decision-output seam
  directly, while the existing applicability decision tests still verify the public
  `build_applicability_decisions` behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `205` code files, `56` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability_decisions.py` reduced to `2036` lines from the earlier `2374`-line
  post-sequence-4 baseline, and the new `applicability_decision_outputs.py` seam remains below the
  `800`-line gate at `375` lines.
- Next routing:
  continue inside Milestone 6 on the remaining predicate/arbitration and evidence-matching core in
  `applicability_decisions.py`, then `applicability_validation.py`, and the broader
  claims/evidence hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 4

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 4 closes the remaining authority-universe snapshot builder
  seam, but the broader applicability decision/validation plus claims/evidence hotspot family
  remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_builder.py`,
  `tests/test_applicability_authority_universe_builder.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_authority_universe_builder.py` now owns the remaining authority-universe snapshot
  orchestration, catalog/template loading, hashing, and snapshot artifact writing that previously
  remained inside `applicability.py`, while `applicability.py` is now a thin public facade for
  `build_authority_universe_snapshot`.
- Direct contract coverage:
  `tests/test_applicability_authority_universe_builder.py` now pins the extracted snapshot-builder
  and loader support surface directly, while the existing applicability snapshot tests still verify
  the public authority-universe behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `203` code files, `56` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability.py` reduced to `48` lines from the earlier `501`-line post-sequence-3
  baseline, and the new `applicability_authority_universe_builder.py` seam remains below the
  `800`-line gate at `501` lines.
- Next routing:
  continue inside Milestone 6 on `applicability_decisions.py`, `applicability_validation.py`, and
  the broader claims/evidence hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 3

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 3 closes the authority-universe validation and summary seam,
  but the broader applicability decision/validation plus claims/evidence hotspot family remains
  active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py`,
  `tests/test_applicability_authority_universe_contracts.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_authority_universe_contracts.py` now owns the authority-universe snapshot
  validation checks and summary contract that previously remained inside `applicability.py`, while
  the public `build_authority_universe_snapshot` entrypoint stays in `applicability.py`.
- Direct contract coverage:
  `tests/test_applicability_authority_universe_contracts.py` now pins the extracted
  authority-universe validation and summary surface directly, while the existing applicability
  snapshot tests still verify the public authority-universe behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `201` code files, `56` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability.py` reduced to `501` lines from the earlier `1082`-line post-sequence-2
  baseline, and the new `applicability_authority_universe_contracts.py` seam remains below the
  `800`-line gate at `594` lines.
- Next routing:
  continue inside Milestone 6 on the remaining authority-universe orchestration plus
  `applicability_decisions.py`, `applicability_validation.py`, and the broader claims/evidence
  hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 2

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 2 closes the remaining candidate-assembly seam, but the
  broader applicability decision/validation plus claims/evidence hotspot family remains active.
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`,
  `tests/test_applicability_candidate_assembly.py`,
  `docs/ARCHITECTURE.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_candidate_assembly.py` now owns rule-template and forest-plan-component candidate
  assembly plus the required package-fact, retrieval, graph-expansion, dependency, and
  search-coverage contract builders that previously remained inside `applicability.py`, while the
  public `build_authority_universe_snapshot` entrypoint stays in `applicability.py`.
- Direct contract coverage:
  `tests/test_applicability_candidate_assembly.py` now pins the extracted rule-template and
  forest-plan-component contract surface directly, while the existing applicability snapshot tests
  still verify the public authority-universe behavior end to end.
- Live probe evidence:
  the fresh architecture probe reports `199` code files, `57` files above `800`, no Python or
  JS/TS import cycles, top hotspot `src/usfs_r1_ea_sources/project_sow_package.py` at score
  `104370`, `applicability.py` reduced to `1082` lines from the earlier `1791`-line post-sequence-1
  baseline, and the new `applicability_candidate_assembly.py` seam remains below the `800`-line
  gate at `722` lines.
- Next routing:
  continue inside Milestone 6 on the remaining authority-universe orchestration plus
  `applicability_decisions.py`, `applicability_validation.py`, and the broader claims/evidence
  hotspot families. Do not advance to Milestone 7 yet.

## Overall Architecture Refactor Milestone 6 Sequence 1

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`.
- Outcome label:
  `reduced` for Milestone 6; sequence 1 is implemented, but the broader
  applicability/claims/evidence hotspot family remains active.
- Milestone 6 sequence 1 closeout commit:
  `f96a396` (`Reduce architecture refactor Milestone 6 authority-family seam`).
- Implementation surfaces:
  `src/usfs_r1_ea_sources/applicability.py`,
  `src/usfs_r1_ea_sources/applicability_authority_family_templates.py`,
  `src/usfs_r1_ea_sources/applicability_contract_support.py`,
  `tests/test_applicability_authority_family_templates.py`,
  `docs/ARCHITECTURE.md`,
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/architecture_contract.toml`.
- Runtime seam closeout:
  `applicability_authority_family_templates.py` now owns authority-family
  template candidate assembly, source-evidence availability, and
  retrieval/graph/dependency/search-coverage contract construction that
  previously lived inside `applicability.py`, while
  `applicability_contract_support.py` now owns the shared
  authority-document-role, source-record, string-normalization, and
  source-record-summary helpers consumed by both modules.
- Alignment pass:
  the latest docs-only follow-up pins the same runtime truth across
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/ARCHITECTURE.md`,
  `docs/SESSION_HANDOFF.md`, and
  `docs/OVERALL_ARCHITECTURE_REFACTOR_MILESTONE_PLAN.md`, refreshes the
  umbrella plan's stale `applicability.py` large-file inventory entry from the
  pre-sequence `2315`-line value to the live `1791`-line value, and keeps the
  new applicability owner modules explicit in the routed owner-surface lists.
- Live probe evidence:
  the fresh architecture probe reports `197` code files, `57` files above
  `800`, no Python or JS/TS import cycles, top hotspot
  `src/usfs_r1_ea_sources/project_sow_package.py` at score `104370`,
  `applicability.py` reduced to `1791` lines, and no new `>800` line file
  introduced by the seam.
- Next routing:
  continue inside Milestone 6 for the remaining rule-template and
  forest-plan-component candidate assembly still in `applicability.py`, then
  the broader applicability decision/validation and claims/evidence owner
  families. Do not advance to Milestone 7 yet.

## Applicability-First Milestone 10 Closeout

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/APPLICABILITY_FIRST_REVIEW_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 10; the umbrella applicability-first architecture
  plan is now locally complete and no further continuation is routed through
  it.
- Milestone 10 closeout commit:
  `aa97e59` (`Resolve applicability-first Milestone 10`).
- Alignment pass:
  the latest docs-only follow-up pins the same runtime closeout across the
  routed README/current-state/handoff/plan surfaces and marks older
  append-only South Plateau blocked references as historical only.
- Runtime truth refresh:
  a bounded South Plateau `compliance-review` replay regenerated
  `authority_explanation_paths.json`; fresh
  `v1-ea-eval --review-id region1-expansion-south-plateau-landscape-treatment`
  now passes with `contract_status="reviewer_ready"`; and fresh
  `promotion-suite --manifest config/promotion_suite_v1.json --strict-expansion`
  now passes with `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=true`, and `open_expansion_slot_count=0`.
- Routing truth:
  Milestones 1 through 9 remain implemented, Milestone 10 is closed through
  post-V1 real-package expansion plus South Plateau reviewer-ready conversion,
  and future applicability-first work should start as a new standalone
  milestone.
- Residual caveat outside this packet:
  a fresh local rerun of `real-package-review-coverage-eval` still depends on
  the preserved West Reservoir replay-context package path under
  `/Users/chunkstand/Downloads/West Reservoir (67436)`. That package-authority
  drift belongs to the separate real-package review coverage lane and was not
  reopened in this milestone.

## Full Canonical Live Source-Set Promotion Milestone 4 Closeout

Latest closeout on 2026-05-20:

- Routed implementation packet:
  `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 4; the live-promotion packet is now locally
  complete as the governing full-canonical closeout boundary.
- Milestone 4 closeout commit:
  `f464fa9` (`Resolve live source-set promotion Milestone 4`).
- Implementation surfaces:
  `README.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`,
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`, and
  `docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`.
- Sole-truth closeout:
  those durable packet surfaces now describe live successor
  `source-set-f775524ab233ff27` as the sole active full-canonical source set,
  preserve archived `source-set-732a5a91d31736f8` as historical evidence
  only, and route no further live-promotion follow-on through this boundary.
- Active-config proof:
  targeted `rg -n "source-set-732a5a91d31736f8"` over
  `config/promotion_suite_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`,
  `config/phase_eval_direct_eval_v1.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`, and
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  returns no matches, so archived `732a...` is no longer an active
  full-canonical dependency.
- Next routing:
  none through this packet; the live full-canonical promotion boundary is now
  locally resolved.

## Full Canonical Live Source-Set Promotion Milestone 3 Closeout

Latest closeout on 2026-05-19:

- Routed implementation packet:
  `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 3; the runtime full-canonical downstream split is
  now closed on the live successor.
- Milestone 3 closeout commit:
  `a299450` (`Resolve live source-set promotion Milestone 3`).
- Implementation surfaces:
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`,
  `config/phase_eval_direct_eval_v1.json`,
  `config/promotion_suite_v1.json`,
  `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`,
  focused graph/promotion contract tests, and the durable docs/handoff set.
- Downstream replay truth on `source-set-f775524ab233ff27`:
  a no-reuse `extract-build` replay rebuilt the live extraction family to
  `extracted_count=634`, `failed_count=0`, `chunk_count=98827`, and
  `reused_count=0` after the targeted Docling refresh of `WILD-ESA-094`;
  `extraction-accuracy-audit` now passes with `audited_record_count=343`;
  `authority-currentness` passes with `authority_family_count=454`;
  `forest-plan-components-build` passes with `component_count=1416` and
  `standard_count=397`; `forest-plan-profile-eval` passes with
  `active_source_set_ids=["source-set-f775524ab233ff27"]`; `forest-plan-component-retrieval-eval`
  passes `6/6`; `retrieval-build` is reviewer-ready with `chunk_count=98827`
  and `verified_extraction_admitted_source_count=343`; `claim-extract` passes
  with `claim_count=122510`; `rule-claim-link` validates with `rule_count=48`,
  `link_count=0`, and `gap_count=48`; bare `nepa-knowledge-graph-export`
  passes with `72` validation checks, `3,636` nodes, and `7,185` edges; and
  `promotion-suite` now reports
  `full_canonical_source_set_id=source-set-f775524ab233ff27`,
  `full_canonical_corpus_ready=true`, `promotion_ready=true`, and `8/8`
  required full-canonical results passing.
- Graph-export durability truth:
  `nepa_knowledge_graph_export.py` now accepts the governed proving-context
  pointer when its cached context ID is stale but its manifest path already
  resolves to the active source set, so the live canonical graph replay no
  longer depends on a manual `--authority-inventory` override.
- Routing truth:
  live successor `source-set-f775524ab233ff27` now governs the active
  catalog, extraction, currentness, component inventory, profile eval,
  component retrieval, direct-eval contract, graph export, and promotion
  surfaces; archived `source-set-732a5a91d31736f8` remains preserved
  historical evidence only.
- Historical next routing before the later Milestone 4 closeout above:
  Milestone 4 docs-only sole-truth closeout on
  `source-set-f775524ab233ff27`: collapse remaining historical routing prose
  and pin the runtime closeout hash across the durable docs set.

## Full Canonical Live Source-Set Promotion Milestone 2 Closeout

Latest closeout on 2026-05-19:

- Routed implementation packet:
  `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 2; the next routed slice is the live
  downstream rebind/replay boundary.
- Milestone 2 closeout commit:
  `c08e480` (`Resolve live source-set promotion Milestone 2`).
- The committed forest-plan component-inventory boundary now binds to live
  successor `source-set-f775524ab233ff27`:
  `config/r1_forest_plan_component_inventory_build_manifest.json` now points
  `source_set_references.active_full_canonical.source_set_id` and
  `identity_reconciliation.registry_active_source_set_id` at the live
  successor; `config/region1_forest_plan_readiness_nepa_3d_v1.json` now points
  its top-level `source_set_id`, every
  `component_inventory_validation.artifact_path`, and
  `identity_reconciliation.registry_active_source_set_id` at the live
  successor; and
  `config/r1_forest_plan_identity_reconciliation_v1.json` now records
  `active_source_set_id=source-set-f775524ab233ff27`.
- `forest-plan-components-build --output-dir source_library --source-set-id source-set-f775524ab233ff27 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  now passes on the live successor with `component_count=1416`,
  `standard_count=397`, `blocked_forest_unit_ids=[]`,
  `coverage_passed=true`, and `component_source_accuracy_passed=true`.
- Historical routing note:
  this Milestone 2 section is preserved runtime context only after the later
  Milestone 3 closeout above closed the downstream live replay on
  `source-set-f775524ab233ff27`.

## Full Canonical Live Source-Set Promotion Milestone 1 Closeout

Latest closeout on 2026-05-19:

- Routed implementation packet:
  `docs/FULL_CANONICAL_LIVE_SOURCE_SET_PROMOTION_MILESTONE_PLAN.md`.
- Outcome label:
  `resolved` for Milestone 1; the next routed slice is the live
  forest-plan component-inventory boundary.
- Milestone 1 closeout commit:
  `09a85f7` (`Resolve live source-set promotion Milestone 1`).
- `catalog-build --run-id phase2-canonical-download-full-post-fps005-removal-20260519`
  now emits live successor source set `source-set-f775524ab233ff27` in
  `source_library/catalog/` with `source_count=634`, `artifact_count=622`,
  `unique_url_count=634`,
  `source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`,
  `status_counts={"downloaded": 1, "downloaded_existing": 621, "duplicate_content": 12}`,
  `document_role_counts.forest_plan=34`,
  `document_role_counts.forest_plan_support=315`, and
  `document_role_counts.regulation=44`.
- The governed reuse-first extraction path for a brand-new live source set is
  now explicit in this lane:
  `reuse-inventory --source-set-id source-set-f775524ab233ff27 --previous-source-set-id source-set-732a5a91d31736f8`
  classified `reuse_extraction=634` and `needs_extract=0`, and
  `extract-build --reuse-existing --reuse-inventory-path source_library/derived/source-set-f775524ab233ff27/reuse_inventory/reuse_inventory.json`
  then passed with `extracted_count=634`, `failed_count=0`,
  `chunk_count=98699`, `reused_count=634`, and `validation_passed=true`.
- `authority-currentness --source-set-id source-set-f775524ab233ff27` now
  passes on the live successor with `authority_family_count=454`,
  `source_currentness_record_count=634`,
  `catalog_source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`,
  and `validation_passed=true`.
- Split truth is reduced but not closed: archived
  `source-set-732a5a91d31736f8` still remains the governing green downstream
  full-canonical contract, active full-canonical configs still point at that
  archived source set, and `promotion-suite` still reports
  `full_canonical_source_set_id=source-set-732a5a91d31736f8`.
- Historical next routing before Milestone 2 closeout `c08e480`:
  repoint the component-inventory manifest/readiness boundary at live
  successor `source-set-f775524ab233ff27`, rerun
  `forest-plan-components-build`, and stop if the live lane cannot truthfully
  close the `1416`-component / `397`-standard parity gate.

## Full Canonical Archived Forest-Plan Source-Set Refresh/Rebind

Latest closeout on 2026-05-19:

- The broader full-canonical source-set refresh/rebind decision now lands as
  an archived classifier-refresh gate at
  `source_library/runs/phase2-canonical-full-canonical-classifier-refresh-20260519/catalog_gate/`
  with refreshed full-canonical source set
  `source-set-732a5a91d31736f8`.
- That archived gate preserves the real canonical run lineage
  `phase2-canonical-download-full-post-fps005-removal-20260519` while
  carrying the committed classifier fix on current `HEAD`. It records
  `source_count=634`, `artifact_count=622`,
  `source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`,
  and the corrected canonical primary-plan/support split.
- The refreshed gate now records `status_counts={"downloaded": 1, "downloaded_existing": 621, "duplicate_content": 12}` and remains the
  governing archived full-canonical replay boundary for downstream
  forest-plan work.
- The archived extraction lane now passes on
  `source_library/derived/source-set-732a5a91d31736f8/` with
  `extracted_count=634`, `failed_count=0`, `chunk_count=98699`,
  `reused_count=291`, and `validation_passed=true`.
- `authority-currentness` now passes on
  `source-set-732a5a91d31736f8` with
  `authority_family_count=454`,
  `source_currentness_record_count=634`,
  `catalog_source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`, and
  `validation_passed=true`.
- `forest-plan-profile-eval` now passes on the refreshed full-canonical
  contract with
  `active_source_set_ids=["source-set-732a5a91d31736f8"]`,
  `covered_profile_count=10`, and `profile_failure_count=0`.
- `forest-plan-components-build` on the refreshed archived source set now
  passes with `component_count=1416`, `standard_count=397`,
  `blocked_forest_unit_ids=[]`, `coverage_passed=true`, and
  `component_source_accuracy_passed=true`.
- The governed identity registry in
  `config/r1_forest_plan_identity_reconciliation_v1.json` now records
  `74` exact official-URL matches, `1` governed catalog rebound
  (`R1PLAN-flathead-nf-02 -> FINAL-FLAT-001`), and only `24` unresolved
  rows with
  `unresolved_status_counts={"catalog_confirmed": 11, "source_delta_required": 13}`.
- The bound manifest/readiness/profile surfaces now point the Flathead primary
  plan at `FINAL-FLAT-001`, and `forest-plan-component-retrieval-eval` now
  passes `6/6` on canonical component IDs including
  `FINAL-FLAT-001-FW-STD-SOIL-01`.
- The managed `extraction` extra now includes `rapidocr` and `cryptography`,
  which closes the Python 3.14 fallback-runtime gap behind raster OCR and AES
  PDF crosschecks for archived extraction/audit replays.
- The workbook direct-document repair slice is now closed: `WILD-ESA-075` and
  the `LEX-USFS-002/003/007/008/011/012/013/016/017` rows now point at direct
  USDA/FWS PDF targets in the workbook contract, `FPS-420` now admits through
  ZIP metadata extraction, and stale HTML artifact reuse is blocked when a row
  now governs a direct PDF artifact.
- `extraction-accuracy-audit` on
  `source-set-732a5a91d31736f8` now passes with
  `audited_record_count=343`,
  `knowledge_base_admitted_source_record_ids=343`,
  `knowledge_base_blocked_source_record_ids=0`, and every audit check green,
  including `direct_document_required_records_use_document_artifacts`.
- `retrieval-build` on the refreshed archived source set is now
  reviewer-ready with `chunk_count=98699`,
  `verified_extraction_admitted_source_count=343`,
  `verified_extraction_required_source_count=343`, and
  `validation_passed=true`.
- `claim-extract` now passes on
  `source-set-732a5a91d31736f8` with `claim_count=122285` and
  `validation_passed=true`.
- `rule-claim-link` now validates truthfully on
  `source-set-732a5a91d31736f8` with `rule_count=48`, `link_count=0`,
  `gap_count=48`, and zero validation failures.
- `nepa-knowledge-graph-export` now passes on
  `source-set-732a5a91d31736f8` with `72` validation checks,
  `failed_validation_check_count=0`,
  `region1_forest_plan_graph_ready_profile_count=10`, and
  `region1_forest_plan_blocked_profile_count=0`.
- `promotion-suite --manifest config/promotion_suite_v1.json` now points
  `full_canonical_source_set_id=source-set-732a5a91d31736f8` and reports
  `current_promotion_ready=true`,
  `full_canonical_corpus_ready=true`,
  `expansion_ready=true`,
  `promotion_ready=true`,
  `passed_required_full_canonical_result_count=8`,
  `required_full_canonical_result_count=8`, and
  `full_canonical_failure_category_counts={}`.
- Milestone 4 runtime closeout landed in
  `237c45d` (`Resolve archived full-canonical Milestone 4 lane`).
- Milestone 5 docs-only closeout landed in
  `df2bd28` (`Resolve archived full-canonical Milestone 5 closeout`).
  The archived full-canonical downstream runtime lane remains green, and no
  further blocked rerun is routed on the archived corpus through that packet.

## Source-Register Forest Plan Role Classification Code Closeout

Latest closeout on 2026-05-19:

- Historical routing note:
  this section records the earlier code-only classifier closeout before the
  archived full-canonical refresh/rebind landed. The section above is now the
  active source-set truth when they disagree.
- Closing commit hash:
  `f220b7a` (`Fix source-register forest plan role classification`).
- Outcome label:
  `reduced`
- The active full-canonical forest-plan blocker is no longer truthfully described as only a
  legacy-identity problem. A fresh
  `forest-plan-components-build --source-set-id source-set-9e7d85759951c279 --manifest-path config/r1_forest_plan_component_inventory_build_manifest.json`
  replay now stops with `component_count=754`, `standard_count=186`, and only `5` blocked forests:
  `dakota-prairie-grasslands`, `flathead-nf`, `kootenai-nf`, `lolo-nf`, and
  `nez-perce-clearwater-nfs`.
- That replay showed a second blocker family on the active canonical lane: canonical
  `source_register_v1` primary-plan rows such as `FPS-130`-`FPS-134`, `FPS-267`, `FPS-298`, and
  `FPS-347` were still entering the catalog/chunk surfaces as `document_role=regulation`, so the
  manifest-driven inventory builder filtered them out before parsing.
- `src/usfs_r1_ea_sources/catalog.py` now fixes that regression by applying a manifest-driven
  primary-plan override for `source_register_v1` rows before the generic `regulation` fallback.
  The canonical workbook proof now classifies `FPS-130`-`FPS-134`, `FPS-267`, `FPS-298`, and
  `FPS-347` as `forest_plan`, while `FPS-165`, `FINAL-KOOT-011`, and `FOR-033` remain
  `forest_plan_support`.
- A scoped archived
  `catalog-build --run-id phase2-canonical-download-full-post-fps005-removal-20260519`
  replay on current HEAD now proves the same role split against the real canonical run without
  mutating the live active catalog. That archived gate emitted
  `source-set-2b6cb7d17da08906` with
  `document_role_counts.forest_plan=33` and
  `document_role_counts.forest_plan_support=316`.
- Focused verification for the code closeout passed:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_catalog.py tests/test_forest_plan_source_delta_readiness.py -q`
  (`19/19`) and
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/catalog.py tests/test_catalog.py tests/test_forest_plan_source_delta_readiness.py`.
- No active `source_library/` catalog or extraction refresh landed in this code-only closeout.
  `source_library/catalog/source_catalog.jsonl` and
  `source_library/derived/source-set-9e7d85759951c279/chunks/chunks.jsonl`
  still reflect the pre-fix roles until a separate replay regenerates them.
- Next routing:
  the next slice is broader than an in-place active-catalog refresh. Because catalog identity is
  commit-sensitive, promoting the current-HEAD replay would require a broader full-canonical
  source-set refresh/rebind decision before the narrowed remaining blocker family can be remeasured
  truthfully.

## Full Canonical Forest Plan Identity Reconciliation Milestone 1 Reduced Closeout

Latest closeout on 2026-05-19:

- Routed implementation packet:
  `docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`.
- The Milestone 1 reduced closeout commit is
  `7dd4fb5` (`Reduce identity reconciliation Milestone 1 source-record mix`).
- Milestone 0 remains resolved through
  `d3606ad` (`Close identity reconciliation Milestone 0 baseline`).
- Milestone 1 is now reduced through governed source-record rebinds in
  `config/r1_forest_plan_component_inventory_build_manifest.json` and
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`, driven by
  `src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py` plus
  focused contract coverage in
  `tests/test_forest_plan_identity_reconciliation.py`,
  `tests/test_forest_plan_inventory_build_manifest.py`,
  `tests/test_forest_plan_profiles.py`, and
  `tests/test_forest_plan_profile_eval_contracts.py`.
- The committed manifest/readiness pair now reduces the live identity mix to
  `74` canonical source-record IDs plus the explicit unresolved `25`-row
  legacy blocker set from
  `config/r1_forest_plan_identity_reconciliation_v1.json`
  (`11` `catalog_confirmed`, `14` `source_delta_required`).
- Both configs now carry committed top-level and per-profile
  `identity_reconciliation` metadata so the remaining blocker family is
  explicit rather than hidden inside mixed legacy/canonical source IDs.
- The remaining unresolved blocker family is concentrated in
  `flathead-nf=10`, `bitterroot-nf=3`, `idaho-panhandle-nfs=3`,
  `nez-perce-clearwater-nfs=3`, and single-row planning/document-set blockers
  in `custer-gallatin-nf`, `beaverhead-deerlodge-nf`,
  `dakota-prairie-grasslands`, `helena-lewis-and-clark-nf`, `kootenai-nf`,
  and `lolo-nf`.
- Focused verification for the reduced closeout passed:
  `PYTHONPATH=src uv run --extra dev pytest tests/test_forest_plan_identity_reconciliation.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profiles.py tests/test_forest_plan_profile_eval_contracts.py -q`
  (`38/38`);
  `PYTHONPATH=src uv run --extra dev ruff check src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py tests/test_forest_plan_identity_reconciliation.py tests/test_forest_plan_inventory_build_manifest.py tests/test_forest_plan_profiles.py tests/test_forest_plan_profile_eval_contracts.py`;
  `python /Users/chunkstand/.codex/skills/milestone-plan-writer/scripts/lint_milestone_plan.py --strict docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`;
  and `git diff --check`.
- Historical note:
  older forest-plan sections below that still mention the pre-registry
  `23`/`76` blocker split are preserved Milestone 3 evidence only and are
  superseded by the governed Milestone 0/1 `74`/`25` identity-reconciliation
  census above.
- Historical routing note:
  at the Milestone 1 reduced closeout, the next slice was the unresolved
  `25`-row blocker family only. That routing is now superseded by the
  source-register role-classification closeout above: a broader full-canonical
  source-set refresh/rebind decision must land before the remaining blocker
  family can be remeasured truthfully.

## Full Canonical Forest Plan Identity Reconciliation Milestone 0 Closeout

Latest closeout on 2026-05-19:

- Routed implementation packet:
  `docs/FULL_CANONICAL_FOREST_PLAN_IDENTITY_RECONCILIATION_MILESTONE_PLAN.md`.
- This packet is now the active implementation surface for the blocked
  forest-plan lane. The older
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`
  packet is now reduced historical context after its Milestone 3 stop at
  `933c667`.
- The Milestone 0 closeout commit for the new packet is
  `d3606ad` (`Close identity reconciliation Milestone 0 baseline`).
- Milestone 0 in the new packet is now resolved
  through `config/r1_forest_plan_identity_reconciliation_v1.json` and the new
  generator/test surface in
  `src/usfs_r1_ea_sources/forest_plan_identity_reconciliation.py` plus
  `tests/test_forest_plan_identity_reconciliation.py`.
- The committed registry records the live identity census against active source
  set `source-set-9e7d85759951c279`:
  `referenced_legacy_source_record_count=99`,
  `exact_url_matched_source_record_count=74`,
  `unresolved_source_record_count=25`,
  `unresolved_status_counts={"catalog_confirmed": 11, "source_delta_required": 14}`.
- The `74` exact URL-backed bindings are the governed canonical source-record
  IDs available for the next manifest/readiness rebind slice. The unresolved
  `25` rows remain explicit blocker data rather than hidden manifest debt.
- Focused verification for the new packet now passes on the new registry/test
  surface. The next routed slice is Milestone 1 only: rebind the
  inventory/readiness source-record IDs from legacy `R1PLAN-*` values onto the
  `74` exact URL-backed canonical source-record IDs while preserving the
  unresolved `25` as explicit blockers.

## Full Canonical Final Blocker Milestone 3 Reduced Closeout

Latest reduced closeout on 2026-05-19:

- Routed implementation packet:
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`.
- Milestones 0-2 remain closed through
  `4660d11` (`Close Milestone 2 FPS-005 workbook contract removal`).
- The reduced Milestone 3 closeout commit is
  `933c667` (`Reduce Milestone 3 to forest-plan identity blocker`).
- The workbook contract is now explicitly reduced to
  `Document_Register_Master=634`,
  `Direct_File_Capture_Queue=51`,
  `Removed_Not_Applicable_Final=3`, with
  `source-register-validate` passing on workbook SHA
  `999c773bb5d6183a391f03b7346084f046389f7ede52d07139cee1dfc9f073f6`.
- `FPS-005` is no longer in the active load-bearing sheet. It now lives in
  `Removed_Not_Applicable_Final` with a governed removal reason after a
  2026-05-19 planning-page recheck confirmed that
  `https://www.fs.usda.gov/media/228272` still serves a structurally invalid
  Chapter 4 PDF and no exact official replacement chapter artifact was
  available.
- The active local catalog in `source_library/catalog/` is now source set
  `source-set-9e7d85759951c279`, created on `2026-05-19T17:50:42.212832Z`,
  with `source_count=634`, `artifact_count=622`, `unique_url_count=634`,
  `source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`,
  `status_counts={"downloaded_existing": 622, "duplicate_content": 12}`, and
  governing download run
  `phase2-canonical-download-full-post-fps005-removal-20260519`.
- The workbook-contract refresh is now proven through:
  `phase2-canonical-dry-run-post-fps005-removal-20260519`
  (`planned_count=634`);
  `phase2-canonical-download-full-post-fps005-removal-20260519`
  (`downloaded_existing=622`, `duplicate_content=12`, `failed_count=0`,
  `needs_review_count=0`);
  `validate-run --run-id phase2-canonical-download-full-post-fps005-removal-20260519`
  (`8/8` checks passed); and
  `catalog-build --run-id phase2-canonical-download-full-post-fps005-removal-20260519`
  (`validation_passed=true`).
- A reuse-first extraction rebuild on `source-set-9e7d85759951c279` classified
  `reuse_extraction=624` and `needs_extract=10`, reused `620` records, then
  cleared the pre-existing scoped XML audit red with a targeted merged
  reextract of `USDA-002`, `USDA-003`, `USDA-004`, and `USDA-006`.
  `source_library/derived/source-set-9e7d85759951c279/diagnostics/summary.json`
  now records `extracted_count=634`, `failed_count=0`, `chunk_count=98155`,
  `reused_count=620`, and `validation_passed=true`.
- `authority-currentness --source-set-id source-set-9e7d85759951c279` now
  passes with `authority_family_count=454`,
  `catalog_source_partition_counts={"active_review_corpus": 582, "currentness_supersession_archive": 52}`,
  `source_currentness_record_count=634`, and `validation_passed=true`.
- The active full-canonical contract surfaces in
  `config/promotion_suite_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`, and
  `config/phase_eval_direct_eval_v1.json`
  are now rebound to active import source set `source-set-9e7d85759951c279`.
- Focused contract coverage for that rebind is now green:
  `tests/test_promotion_suite.py`,
  `tests/test_forest_plan_inventory_build_manifest.py`,
  `tests/test_forest_plan_profile_eval_contracts.py`,
  `tests/test_phase_eval_direct_eval_contracts.py`, and
  `tests/test_phase_eval.py`
  pass `59/59`.
- A fresh local non-strict
  `promotion-suite --manifest config/promotion_suite_v1.json`
  rerun now reports
  `current_promotion_ready=true`,
  `promotion_ready=true`,
  `expansion_ready=true`,
  `full_canonical_corpus_ready=false`,
  `passed_required_full_canonical_result_count=4`,
  `required_full_canonical_result_count=8`, and
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2, "stale_artifact": 2}`
  against active source set `source-set-9e7d85759951c279`.
- The attempted `forest-plan-components-build` prerequisite replay on
  `source-set-9e7d85759951c279` failed closed. The resulting
  `source_library/derived/source-set-9e7d85759951c279/forest_plan_components/summary.json`
  records `passed=false`, `component_count=0`, `standard_count=0`, and all
  `10` tracked forests blocked by
  `no_selected_forest_plan_chunks`,
  `plan_component_labels_not_detected`, and
  `plan_standard_labels_not_detected`.
- The blocker is now explicit: the active canonical catalog and chunk store
  contain `0` `R1PLAN-*` rows, while
  `config/r1_forest_plan_component_inventory_build_manifest.json` plus
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`
  still reference `99` legacy `R1PLAN-*` IDs. The preserved forest-plan
  register crosswalk accounts for all `99`; `23` are
  `catalog_confirmed`/mapped to existing canonical rows, and the remaining
  `76` stay `source_delta_required`.
- No graph/profile/component-retrieval reruns landed in this reduced slice,
  because the forest-plan identity mismatch blocks the prerequisite inventory
  lane before those downstream artifacts can be regenerated truthfully.
- Next routing:
  route a dedicated canonical-vs-legacy forest-plan identity reconciliation
  packet, then resume the blocked
  `nepa-knowledge-graph-export`,
  `forest-plan-profile-eval`,
  `forest-plan-component-retrieval-eval`, and
  `promotion-suite`
  reruns on `source-set-9e7d85759951c279`.

## Full Canonical Downstream Freshness Refresh Reduced Closeout

Latest reduced closeout on 2026-05-19:

- Routed reduction plan:
  `docs/FULL_CANONICAL_DOWNSTREAM_FRESHNESS_REFRESH_MILESTONE_PLAN.md`.
- The active full-canonical contract surfaces in
  `config/promotion_suite_v1.json`,
  `config/region1_forest_plan_profile_eval_coverage_v1.json`,
  `config/region1_forest_plan_readiness_nepa_3d_v1.json`,
  `config/r1_forest_plan_component_inventory_build_manifest.json`,
  `config/forest_plan_component_retrieval_eval_v1.json`, and
  `config/phase_eval_direct_eval_v1.json`
  are now rebound to active import source set `source-set-cac9c7d02b280825`.
- Focused contract coverage for that rebind is now green:
  `tests/test_promotion_suite.py`,
  `tests/test_forest_plan_inventory_build_manifest.py`,
  `tests/test_forest_plan_profile_eval_contracts.py`,
  `tests/test_phase_eval_direct_eval_contracts.py`, and
  `tests/test_phase_eval.py`
  pass `59/59`.
- `authority-currentness --source-set-id source-set-cac9c7d02b280825`
  now passes with `authority_family_count=454`,
  `catalog_source_partition_counts={"active_review_corpus": 583, "currentness_supersession_archive": 52}`,
  `source_currentness_record_count=635`, and `validation_passed=true`.
- The first full-source-set extraction replay is now historical blocker
  evidence only. The live extraction summary has moved forward through a
  targeted external-Docling OCR merge replay on the failed IDs plus three
  in-environment no-timeout Docling retries on `WILD-ESA-038`,
  `WILD-ESA-054`, and `FPS-241`.
- `source_library/derived/source-set-cac9c7d02b280825/diagnostics/summary.json`
  now records `extracted_count=634`,
  `failed_count=1`,
  `chunk_count=98109`,
  `validation_passed=false`, and
  `failure_counts={"docling_conversion_failed": 1}`.
- The residual extraction blocker set is now exact:
  `FPS-005` alone fails with
  `docling_conversion_failed` because the PDF structure is invalid and a
  fresh upstream redownload still reproduces the same xref/pages corruption.
- `src/usfs_r1_ea_sources/extract.py` now routes larger scanned PDFs through a
  governed Swift-backed Apple Vision raster OCR lane on macOS before falling
  back to the slower RapidOCR CPU pool, while retaining the existing
  fail-closed page-error handling and chunked Docling OCR fallback.
- The plan-mandated rerun of the older reduced raster path on `FPS-125`
  remained compute-bound for `163.82` real seconds with the bounded
  `4`-worker RapidOCR pool active and no merged record, which justified the
  new large-scan Apple Vision lane for this checkout.
- A follow-on targeted replay now clears `FPS-125` on the active source set
  with `parser_name=apple_vision_pdf_raster`,
  `parser_metadata.pdf_raster_ocr_backend=apple_vision_swift`,
  `chunk_count=861`, and `text_char_count=1244371`.
- Focused extractor coverage in `tests/test_extract.py` now passes `33/33`.
- Fresh rebased `promotion-suite --manifest config/promotion_suite_v1.json`
  now reports `current_promotion_ready=true`,
  `promotion_ready=true`,
  `expansion_ready=true`,
  `full_canonical_corpus_ready=false`,
  `passed_required_full_canonical_result_count=4`,
  `required_full_canonical_result_count=8`, and
  `full_canonical_failure_category_counts={"graph_viewer_export_invalid": 2, "stale_artifact": 2}`.
- The remaining failed required full-canonical results are now exact:
  missing
  `source_library/derived/source-set-cac9c7d02b280825/knowledge_graph/nepa_3d_graph_validation.json`,
  missing
  `source_library/derived/source-set-cac9c7d02b280825/knowledge_graph/nepa_3d_graph_summary.json`,
  stale `forest_plan_profile` eval source-set identity, and stale
  `forest_plan_component_retrieval` eval source-set identity.
- Next routing:
  route a governed repair/replacement decision for `FPS-005`, then rerun
  `nepa-knowledge-graph-export`,
  `forest-plan-profile-eval`, and
  `forest-plan-component-retrieval-eval`
  on `source-set-cac9c7d02b280825`.
- Active implementation packet:
  `docs/FULL_CANONICAL_FINAL_BLOCKER_RESOLUTION_MILESTONE_PLAN.md`.
- Milestones 0-1 on that packet are now resolved. Live
  `summary.json`, `extraction_manifest.jsonl`, workbook rows `FPS-005` and
  `FPS-125`, `source_catalog.jsonl`, and the last promotion-suite result now
  agree that the extraction blocker lane is down to one row and that the exact
  remaining failed required full-canonical slots are still the same four
  downstream artifacts.
- Milestone 1 closeout commit is `d9373c4` (`Close Milestone 1 FPS-125 OCR recovery`).
- Current implementation slice:
  Milestone 2 workbook-contract action on `FPS-005`, followed by Milestone 3
  downstream reruns once the active extraction blocker set is empty.

## Canonical Source Register Import Completion Closeout

Latest closeout on 2026-05-19:

- The active local catalog in `source_library/catalog/` is now full-register
  source set `source-set-cac9c7d02b280825`, created on
  `2026-05-19T02:35:26.205014Z`, with `source_count=635`,
  `artifact_count=623`, `unique_url_count=635`,
  `source_partition_counts={"active_review_corpus": 583, "currentness_supersession_archive": 52}`,
  `status_counts={"downloaded": 615, "downloaded_existing": 8, "duplicate_content": 12}`,
  and governing download run
  `phase2-canonical-download-full-post-head429-fallback-20260519`.
- The proving-slice active catalog `source-set-9dcf819bc4cca486` and the
  planned-only Phase 2 gate `source-set-ae989382c52344db` are now explicit
  historical pre-import baselines for this checkout, not the live
  `source_library/catalog/` truth.
- The canonical workbook contract remains:
  `Document_Register_Master=635`,
  `Direct_File_Capture_Queue=51`,
  `Removed_Not_Applicable_Final=2`.
  `source-register-validate` now passes with `issue_count=0` on workbook SHA
  `4d236682fcd26c26056b142cf4f41078afb36ed52e916ef6414066132df7914f`.
- Milestone 1 is closed through
  `source_library/runs/phase2-canonical-preflight-full-post-head429-fallback-20260519/summary.json`:
  `checked_url_count=635`,
  `preflight_ok_count=635`,
  `failed_count=0`.
  `preflight.py` now falls through from `HEAD` `rate_limited` results to the
  existing ranged `GET` probe, and the regression is covered in
  `tests/test_preflight.py`.
- Milestone 2 is closed through:
  `source_library/runs/phase2-canonical-dry-run-post-head429-fallback-20260519/summary.json`
  (`planned_count=635`);
  `source_library/runs/phase2-canonical-download-full-post-head429-fallback-20260519/summary.json`
  (`downloaded=615`, `downloaded_existing=8`, `duplicate_content=12`,
  `failed_count=0`, `needs_review_count=0`);
  `validate-run --run-id phase2-canonical-download-full-post-head429-fallback-20260519`
  (`8/8` checks passed); and
  `catalog-build --run-id phase2-canonical-download-full-post-head429-fallback-20260519`
  (`validation_passed=true`).
- The unsupported-format direct-document slice remains green and preserved:
  scoped preflight passed `8/8`, scoped download passed `8/8`, scoped catalog
  gate `source-set-a0402de124943920` records `artifact_count=8`, scoped
  extraction admitted all `8/8`, and upstream direct eval remains green at
  `38/38`.
- At import-completion closeout time, fresh non-strict
  `promotion-suite --manifest config/promotion_suite_v1.json`
  on `2026-05-19` still reported `current_promotion_ready=true`,
  `promotion_ready=true`, and `expansion_ready=true`, while
  `full_canonical_corpus_ready=false` remained explained by preserved
  historical full-canonical downstream artifacts and
  `full_canonical_failure_category_counts={"stale_artifact": 2}`.
- Current reviewer-ready downstream evidence still lives on review-oriented
  source set `source-set-ba8d0feae79501b8`. The imported canonical catalog is
  now truthful and active, but that import-closeout follow-on has since been
  routed as
  `docs/FULL_CANONICAL_DOWNSTREAM_FRESHNESS_REFRESH_MILESTONE_PLAN.md`; see
  the reduced closeout section above for the current blocker truth.
- Older deeper references below that still describe the Milestone 0 rebaseline,
  the single-row `FPS-117` blocker, or the proving-slice catalog as live are
  historical pre-closeout context only.

## Historical Canonical Source Register Import Completion Milestone 0 Local Rebaseline

Historical closeout on 2026-05-18:

- Milestone 0 chose the docs-rebaseline path, not a local
  `source_library/catalog/` restore. The current checkout already carries a
  reproducible proving-slice active catalog plus a reproducible planned-only
  Phase 2 full-register gate, while a restore would mutate ignored local
  evidence before the import packet has closed its active-truth boundary.
- The active local catalog in `source_library/catalog/` is now explicitly
  pinned as proving source set `source-set-9dcf819bc4cca486`, created on
  `2026-05-18T10:56:21Z`, with `source_count=26`, `artifact_count=26`,
  `unique_url_count=26`,
  `source_partition_counts={"active_review_corpus": 25, "currentness_supersession_archive": 1}`,
  `status_counts={"downloaded_existing": 26}`, and governing download run
  `source-register-proving-download-20260518T105620Z-08363bef`.
- The full-register Phase 2 gate is now explicitly pinned as planned-only
  source set `source-set-ae989382c52344db`, created on
  `2026-05-18T11:32:46Z`, with `source_count=635`, `artifact_count=0`,
  `unique_url_count=635`,
  `source_partition_counts={"candidate_blocked_source": 635}`,
  `status_counts={"planned": 635}`, and `download_run_id=null`.
- The local full-register dry run `phase2-canonical-dry-run-20260518` planned
  all `635` canonical master-sheet rows. The sampled local preflight
  `phase2-canonical-preflight-20260518` checked `25` URLs and recorded
  `7` `preflight_ok` plus `18` `ssl_error`, dominated by `ecos.fws.gov`
  (`18`) and `www.fws.gov` (`5`).
- The local non-strict `promotion-suite` artifact currently reports
  `current_promotion_ready=true` and `promotion_ready=true`, but also
  `full_canonical_corpus_ready=false`,
  `expansion_ready=false`, and
  `full_canonical_source_set_id=source-set-5e65d845ce77e1a0`.
- Milestone 0 is closed through local commit `6a949ae`
  (`Resolve Milestone 0 canonical import rebaseline`), so the next live
  executable slice for this packet is Milestone 1 in
  `docs/CANONICAL_SOURCE_REGISTER_IMPORT_COMPLETION_MILESTONE_PLAN.md`.
- Older deeper references below to `source-set-5e65d845ce77e1a0` as active full
  canonical truth or to all-green local full-canonical / expansion readiness
  are historical preserved baseline evidence for this checkout until a later
  import-completion milestone explicitly restores or reruns them.
- In those preserved lower sections, phrases like `active`, `current`, or
  readiness-green refer to the historical `source-set-5e65d845ce77e1a0`
  replay boundary, not the live `source_library/catalog/` import baseline
  recorded above.

## Historical Canonical Source Register Import Completion Milestone 1 Federal Blocker Slice Checkpoint

Historical checkpoint on 2026-05-18 after implementation commit `c1dc100`
(`Repair federal canonical blocker rows`), the earlier unsupported-format
implementation commit `cf2d5f6`
(`Resolve unsupported-format canonical blocker slice`), the earlier workbook
repair slices, replay `phase2-canonical-preflight-full-repaired-20260518`, and
the scoped unsupported-format direct-document validation set:

- The first Milestone 1 code slice is now live in capture code and config:
  `config/downloader.toml` assigns `verified_transport="curl"` to
  `ecos.fws.gov`, `preflight.py` and `download.py` now honor that
  host-configured verified transport without disabling certificate checks, and
  focused coverage landed in `tests/test_preflight.py` and
  `tests/test_download.py`.
- This host-specific transport is intentionally narrow. It exists because
  `ecos.fws.gov` currently presents an incomplete TLS chain to the
  Python/OpenSSL path in this environment, while verified `curl` succeeds
  cleanly. The repo does not use `curl -k`, does not disable TLS verification,
  and does not broaden the override beyond the named host.
- The completed host replay
  `source_library/runs/phase2-canonical-preflight-ecos-replay-20260518/summary.json`
  now passes `27/27` `preflight_ok` with `failed_count=0` across the full
  `ecos.fws.gov` canonical-master host set.
- The governed workbook repair lane is now live on the canonical master sheet.
  `Document_Register_Master` now carries `61` governed URL repairs total:
  `45` earlier directive/USDA repairs,
  `3` stale-URL repairs for `PROG-008`, `STP-015`, and `STP-011`,
  `1` direct-artifact repair for `WILD-ESA-094`,
  `6` federal/challenge repairs for `FED-042`, `FED-041`, `FED-039`,
  `FED-043`, `FED-029`, and `FPS-344`, plus
  `6` USDA-family host repairs for `USDA-008`, `USDA-009`, `USDA-010`,
  `USDA-011`, `USDA-012`, and `USDA-013`.
  `config/parser_admission_contract_v1.json` now also recognizes
  `www.archives.gov`, `www.govinfo.gov`, `www.ams.usda.gov`,
  `securefoia.usda.gov`, `www.rma.usda.gov`, and `www.ers.usda.gov` as
  official structured web/authority hosts for the repaired federal and
  USDA-family lanes.
  `source-register-validate` now passes with `issue_count=0` on workbook SHA
  `659463445ec6fb02a8669744d0318988b404a68f6f39c8069d21f95f13ad52d8`.
- The earlier federal-blocker checkpoint built on the unsupported-format
  implementation commit `cf2d5f6`
  (`Resolve unsupported-format canonical blocker slice`) and the federal
  blocker repair commit `c1dc100` (`Repair federal canonical blocker rows`).
  The new USDA-family repair slice now closes the last known host-specific
  blocker family before the fresh full-master replay.
  The historical USDA-family repair checkpoint commit for that routed slice is
  `21ffc9e` (`Resolve USDA canonical blocker packet`), but the active
  full-replay checkpoint commit is now `34f5b30`
  (`Record post-USDA full replay checkpoint`).
- Scoped repair replay
  `source_library/runs/phase2-canonical-preflight-directives-repair-validated-20260518/summary.json`
  now passes `45/45` `preflight_ok` with `failed_count=0` across the repaired
  directive-family rows.
- Scoped USDA-family replay
  `source_library/runs/phase2-canonical-preflight-usda-final-blocker-repair-validated-20260518/summary.json`
  now passes `6/6` `preflight_ok` with `failed_count=0` across `USDA-008`,
  `USDA-009`, `USDA-010`, `USDA-011`, `USDA-012`, and `USDA-013`.
- The fresh full-master replay
  `source_library/runs/phase2-canonical-preflight-full-post-usda-repair-20260518/summary.json`
  is now the live Milestone 1 checkpoint. It checked all `635` canonical URLs
  and finished with `634` `preflight_ok` plus only `1` failed row:
  `status_counts={"preflight_ok": 634, "rate_limited": 1}`.
- The fresh full-master replay
  `source_library/runs/phase2-canonical-preflight-full-repaired-20260518/summary.json`
  is now complete against the repaired workbook. It checked all `635`
  canonical URLs and finished with `607` `preflight_ok` plus `28` failed rows:
  `8` `not_found`, `8` `timeout`, `8` `unsupported_content_type`,
  `3` `rate_limited`, and `1` `challenge_page`.
- Scoped blocker replay
  `source_library/runs/phase2-canonical-preflight-blocker-repair-slice-20260518/summary.json`
  now passes `8/8` `preflight_ok` with `failed_count=0` across the `3`
  repaired stale-URL rows (`PROG-008`, `STP-015`, `STP-011`) plus the `5`
  previously failing `www.fs.usda.gov/media/...` rows
  (`FOR-005`, `FPS-296`, `FPS-425`, `FPS-095`, `FPS-079`). Those media rows
  are no longer active blockers for routing, but the full-master replay still
  needs a later rerun after the remaining blocker families close.
- Scoped federal replay
  `source_library/runs/phase2-canonical-preflight-federal-blocker-repair-validated-20260518/summary.json`
  now passes `6/6` `preflight_ok` with `failed_count=0` across the repaired
  federal/challenge rows:
  `FED-042`, `FED-041`, `FED-039`, `FED-043`, `FED-029`, and `FPS-344`.
- A broader replay under
  `source_library/runs/phase2-canonical-preflight-full-complete-20260518/`
  was intentionally stopped after `105` finalized rows once a second blocker
  family surfaced on `www.fs.usda.gov`. The partial event log already records
  timeout rows for `USFS-024`, `USFS-034`, `USFS-008`, `USFS-016`, and
  `USFS-033` from the pre-repair workbook state. Those wrapper rows are now
  covered by the `45`-row Directives CGI repair slice above.
- Despite its `full-complete` run ID, that broader replay remains partial
  blocker evidence only and must not be cited as a completed Milestone 1
  validation artifact.
- The structural unsupported-format boundary slice is now live in code and
  workbook contract. `config/downloader.toml` now admits
  `application/msword` and `image/jpeg`,
  `config/parser_admission_contract_v1.json` now classifies `.doc` and
  image suffixes as `direct_document`,
  `download.py` plus `catalog.py` preserve those direct-artifact parser
  routes, and `extract.py` now uses macOS `textutil` for legacy `.doc`
  artifacts plus Docling for image artifacts.
- Scoped replay
  `source_library/runs/phase2-canonical-preflight-unsupported-format-replay-20260518/summary.json`
  now passes `8/8` `preflight_ok` with `failed_count=0` across
  `R1-021`, `R1-020`, `R1-019`, `R1-023`, `R1-022`, `R1-015`, `R1-009`, and
  `WILD-ESA-094`.
- Scoped download replay
  `source_library/runs/phase2-canonical-download-unsupported-format-replay-20260518/summary.json`
  now finishes with `downloaded_count=8`, `failed_count=0`, and
  `status_counts={"downloaded": 8}`.
- Archived scoped catalog gate
  `source_library/runs/phase2-canonical-catalog-unsupported-format-replay-20260518/catalog_gate/source_set_manifest.json`
  is now live as source set `source-set-a0402de124943920` with
  `source_count=8`,
  `artifact_count=8`, and
  `expected_parser_counts={"doc": 7, "image": 1}`.
- Scoped extraction on `source-set-a0402de124943920` now passes with
  `selected_source_count=8`,
  `extracted_count=8`,
  `parser_counts={"docling": 1, "macos_textutil_doc": 7}`, and
  `source_library/derived/source-set-a0402de124943920/diagnostics/extraction_accuracy_audit.json`
  admits all `8` direct-document rows with
  `knowledge_base_blocked_source_record_ids=[]`.
- Upstream direct eval remains green after the new admission path:
  `source_library/evaluations/upstream/upstream_evaluation_results.json`
  now reports `passed=true`, `case_count=38`, and `failed_case_ids=[]`.
- The known USDA-family blocker lane is now closed in scoped evidence, and the
  live remaining blocker surface is down to one row: `FPS-117` finalized as
  `rate_limited` on `https://www.fs.usda.gov/media/51967` after `3` attempts,
  even though the response chain resolves to the direct PDF
  `https://www.fs.usda.gov/sites/nfs/files/legacy-media/custergallatin/CNF%20FPAdjustment%20001.pdf`.
- The historical `phase2-canonical-preflight-full-repaired-20260518` replay
  now remains pre-USDA-repair evidence only; the live blocker truth is the new
  `634/635` result above.
- Milestone 1 is still not resolved. The next truthful slice is the governed
  single-row `FPS-117` rate-limit closure packet, then one final confirming
  full-master canonical preflight replay before any full `download`,
  `batch-download`, or `catalog-build` for the entire master sheet.

## Canonical Source Register Phase 8 Aggregate Readiness And Legacy Contract Retirement

Latest closeout on 2026-05-18 after implementation commit `5c1d45d`:

- The canonical source-register refoundation aggregate packet is now live. On
  the active reviewer-ready East Crazies lane
  `source_library/reviews/v1-cg-ecid-compliance-review/`, review-scoped
  `phase-eval` now passes `26/26` with `reviewer_ready=true` on
  `source-set-ba8d0feae79501b8`, `final-qa-certification` passes `196/196`,
  `draft-generation-eval` passes `5/5`, and non-strict `promotion-suite`
  stays green with `current_promotion_ready=true` and `32/32` required
  current-promotion results passing.
- The aggregate self-reference loop is now fail-closed instead of operationally
  circular. `draft_generation_manifest.json` records a semantic fingerprint
  for the optional final-QA input, so review-scoped `phase-eval` can tolerate
  final-QA file-hash drift only when the legal-conclusion guard and accepted
  V1 risk ledger are unchanged. Real decision-support or final-QA semantic
  drift still forces reviewed-draft regeneration.
- The controlled source-change refresh proof is now live on proving source set
  `source-set-9dcf819bc4cca486`. `incremental-graph-refresh-eval` passes with
  `documented_source_change_count=51`,
  `superseded_replacement_confirmed_family_count=1`,
  `temporal_lineage_record_count=55`, and required blocker coverage for both
  `superseded_source` and `fsh_chapter_delta_required`.
- The proving-slice aggregate boundary remains explicit. Source-set
  `phase-eval --source-set-id source-set-9dcf819bc4cca486` is still red only
  on inherited Phase 4 placeholder downstream lanes:
  `extraction`, `retrieval`, `evidence_graph`, `claim_extraction`,
  `rule_claim_binding`, `downstream_direct_evaluation`, and
  `evaluation_coverage`. That red state is now a documented proving-slice
  residual, not a reason to preserve the old workbook contract as active truth.
- The canonical workbook refoundation plan is now resolved. Older top-level
  references below that still route to “Phase 8 next” are historical only.
  Older deeper East Crazies aggregate references below that still state
  `phase-eval` `21/21` or current promotion `31/31` are likewise historical
  pre-aggregate values superseded by this Phase 8 closeout.

## Canonical Source Register Phase 7 Legally Defensible Draft-Document Generation

Latest closeout on 2026-05-18:

- `draft-generate` now owns the governed reviewed-draft lane under
  `source_library/reviews/<review_id>/draft_generation/`. The canonical output
  family is `draft_generation_package.json`, `draft_generation.md`,
  `draft_generation_manifest.json`, `draft_generation_traceability.json`,
  `draft_generation_refusals.json`, `draft_defensibility_packet.json`, and
  `draft_generation_validation.json`.
- The generator now consumes reviewed and traced evidence surfaces only:
  `compliance_review.json`, `compliance_validation.json`,
  `authority_explanation_paths.json`,
  `decision_support/ea_consistency_decision_support.json`,
  `review_packet_index/review_packet_index.json`,
  `non_applicable_authority_appendix.json`, and
  `litigation_risk_summary.json`, with optional
  `final_qa/east_crazies_final_qa_certification.json` and
  `authority_reviewer_resolution_report.json` when present. It does not draft
  from workbook rows, raw source files, or unreviewed prompt-only inputs.
- The active reviewer-ready East Crazies review
  `source_library/reviews/v1-cg-ecid-compliance-review/draft_generation/`
  now passes with `ready_section_count=5`, `paragraph_count=41`,
  `warning_section_count=4`, `refusal_count=0`, and
  `validation_passed=true`. The live section states are:
  `issue_summaries=ready_with_reviewer_warnings`,
  `compliance_narrative=ready`,
  `authority_coverage_appendix=ready_with_reviewer_warnings`,
  `affected_environment_and_environmental_consequences=ready_with_reviewer_warnings`,
  and `unresolved_issue_statements=ready_with_reviewer_warnings`.
- Paragraph-level traceability is now first class. Every generated paragraph is
  mapped in `draft_generation_traceability.json` to source passages,
  authority-family IDs, retrieval trace IDs, graph path IDs, reviewed artifact
  selectors, unresolved-issue refs, and residual-risk refs. The paired
  `draft_defensibility_packet.json` summarizes those same boundaries section by
  section for reviewer audit.
- `draft-generation-eval` is now the governed direct-eval lane for reviewed
  draft generation. The live East Crazies eval passed `5/5` at
  `source_library/reviews/v1-cg-ecid-compliance-review/draft_generation/draft_generation_eval_results.json`
  and proves fail-closed handling for unsupported legal-conclusion requests,
  missing citations, stale authority traces, contradictory evidence, and
  reviewer-warning insertion.
- The live proving boundary is still the reviewer-ready East Crazies lane on
  `source-set-ba8d0feae79501b8`, not the canonical proving slice
  `source-set-9dcf819bc4cca486`. That proving slice still carries Phase 4
  placeholder artifacts, so Phase 7 closes the reviewed-draft contract and
  live reviewer lane only; it does not yet prove direct-document-backed
  canonical-corpus draft generation on the placeholder source set.
- This packet is now historical routing context only. Phase 8 has since
  landed, and the canonical source-register refoundation plan is now resolved.

## Canonical Source Register Phase 6 Applicability, Rule-Pack, And Legally Accurate Review

Latest closeout on 2026-05-18 after implementation commit `15d117a`:

- Reviewer-facing authority explanation paths are now first-class compliance
  review outputs. `compliance-review` writes
  `source_library/reviews/<review_id>/authority_explanation_paths.json` and
  threads authority-path classifications, retrieval traces, graph path IDs,
  search-coverage certificate IDs, supporting source-record IDs, unresolved
  issue refs, and residual legal-risk categories into
  `compliance_review.json`, `compliance_matrix.json`,
  `compliance_matrix.md`, and `compliance_matrix.pdf`.
- The active reviewer-ready East Crazies review
  `source_library/reviews/v1-cg-ecid-compliance-review/` was replayed through
  the generated rule pack on `source-set-ba8d0feae79501b8`. The regenerated
  review stays `reviewer_ready=true`, writes
  `authority_explanation_paths.json`, and records `finding_count=37`,
  `finding_path_count=37`, `all_findings_have_path_classification=true`, and
  `all_applicable_findings_have_trace_evidence=true`.
- `v1-ea-eval` now treats `authority_explanation_paths.json` as a required
  broader-EA artifact. The live East Crazies gate passed at
  `source_library/reviews/v1-cg-ecid-compliance-review/v1_ea_eval_results.json`
  with `passed=true`, `broader_ea_passed=true`, `forest_plan_passed=true`,
  `authority_explanation_path_count=37`, and
  `authority_trace_coverage_rate=1.0`.
- `compliance-review-eval` now enforces the explanation-path surface. The live
  direct eval passed `5/5` at
  `source_library/reviews/compliance_review_eval/compliance_review_eval_results.json`
  with `authority_explanation_artifact_rate=1.0`,
  `authority_path_classification_rate=1.0`, and
  `authority_trace_coverage_rate=1.0`.
- `applicability-eval` remains green on the same live reviewer-ready source
  set at
  `source_library/reviews/applicability_eval/applicability_eval_results.json`
  with `9/9` cases passing, all `19` high-priority authority families covered
  across positive and negative fixtures, and arbitration coverage still green
  for positive/negative conflict, weak-positive-only, and template-specific
  sufficiency cases.
- The Phase 6 live reviewer verification is still routed through the active
  East Crazies reviewer-ready lane rather than the canonical proving slice
  `source-set-9dcf819bc4cca486`. That proving slice still carries governed
  Phase 4 placeholder artifacts and therefore cannot yet prove
  real-direct-document compliance review readiness.
- This packet is now historical routing context only. Phase 7 has since
  landed, and Phase 8 is now the next routed implementation packet.

## Canonical Source Register Phase 5 Graph Accuracy, Provenance Completeness, And Knowledge-Graph Gating

Latest closeout on 2026-05-18:

- `nepa-knowledge-graph-export` now writes a canonical source-set semantic
  graph for `source_register_v1` catalogs even when document evidence-graph
  files are absent because the active proving slice still carries governed
  placeholder artifacts. The source-set export now emits
  `authority_document`, `authority_section`, `jurisdiction_scope`,
  `authority_path`, and `justification_path` nodes plus semantic relationship,
  currentness, and support-source provenance.
- The active proving source set `source-set-9dcf819bc4cca486` now passes at
  `source_library/derived/source-set-9dcf819bc4cca486/knowledge_graph/nepa_3d_graph_summary.json`
  with `147` nodes, `193` edges, `26` source records, `26` authority
  documents, `14` authority sections, `5` jurisdiction scopes, `7`
  authority paths, `7` justification paths, and `validation_passed=true`.
- The five new semantic graph gates now pass on that exported graph:
  `authority-ontology-validate` records `graph_scope=source_set` and
  `required_graph_node_type_count=8`;
  `authority-relationship-eval` records `relationship_count=7`;
  `citation-alias-eval` records `alias_row_count=26` with
  `blocked_alias_row_count=8`;
  `graph-health-eval` records `orphan_node_count=0` and
  `disconnected_component_count=1`; and
  `graph-accuracy-eval` records `authority_path_count=7`,
  `justification_path_count=7`, and `relationship_type_count=7`.
- The Phase 5 contract/eval manifests are no longer marked as starter-only.
  `config/authority_ontology_eval_v1.json`,
  `config/authority_relationship_eval_v1.json`,
  `config/graph_health_contract_v1.json`, and
  `config/graph_accuracy_eval_v1.json` now all carry live Phase 5 status.
- Focused negative semantic-graph coverage now fails representative regressions
  for missing required source-set ontology nodes, missing semantic lens
  metadata, and broken `JUSTIFIED_BY` authority-path linkage in
  `tests/test_graph_accuracy_eval.py`.
- `phase-eval` now appends separate `authority_ontology`,
  `authority_relationships`, `citation_aliases`, `graph_health`, and
  `graph_accuracy` source-set phases. For `source-set-9dcf819bc4cca486`, all
  five new semantic phases pass and `nepa_3d_source_set_graph` passes.
- The inherited Phase 4 placeholder boundary remains explicit. Live
  `evidence-graph-build` still exits non-green on the same proving slice with
  `chunk_count=0`, `validation_passed=false`, `reviewer_ready=false`, and only
  the synthetic `SourceSet` node, so overall root `phase-eval` remains blocked
  by extraction, retrieval, evidence-graph, claim-extraction, rule-claim
  binding, and downstream review lanes. This packet closes the semantic graph
  boundary only; it does not widen reviewer-ready or promotion-ready claims.
- This packet is now historical routing context only. Phases 6 and 7 have
  since landed, and Phase 8 is now the next routed implementation packet.

## Canonical Source Register Phase 4 Extraction Fidelity And Verified Source Admission

Latest closeout on 2026-05-18:

- `extract-build` now records canonical extraction-planning truth directly in
  `diagnostics/extraction_manifest.jsonl`. Each manifest row can now carry the
  canonical loader contract, source partition, document type, currentness
  status, URL class, parser-admission class, direct-file-readiness class,
  docling instructions, extraction priority, direct-document requirement, and
  proving-placeholder status instead of relying only on parser/output fields.
- Canonical row planning is now metadata-aware. HTML/structured-web rows with
  curated Docling instructions can prefer Docling without a blanket global
  flag, while strong direct-document signals now remain explicit rather than
  being inferred only from file suffixes.
- The active proving slice extraction build on
  `source-set-9dcf819bc4cca486` now passes structurally at
  `source_library/derived/source-set-9dcf819bc4cca486/diagnostics/summary.json`
  with `26` terminal `placeholder_artifact` rows, `0` parser errors, and
  `validation_passed=true`. This is intentional: the proving slice currently
  contains governed `source-register-proving-artifact-v1` placeholder bytes for
  all `26` active rows, so Phase 4 now treats them as auditable placeholders
  rather than trying to parse them as real PDFs/DOCX files.
- `extraction-accuracy-audit` now understands selector-driven verified
  extraction admission contracts. The default canonical contract can resolve
  against manifest metadata such as `loader_contract`, `source_partition`,
  docling-instruction phrases, and placeholder-artifact state instead of only
  matching hard-coded source ID lists.
- The live root audit now passes fail-closed for the same proving slice at
  `source_library/derived/source-set-9dcf819bc4cca486/diagnostics/extraction_accuracy_audit.json`
  with `audited_record_count=0`, `knowledge_base_admitted_source_record_ids=[]`,
  and `knowledge_base_blocked_source_record_ids=[]`. No canonical proving-slice
  sources are admitted downstream until real direct documents replace the
  governed placeholder artifacts.
- The upstream direct-eval lane now covers `19` required categories and `38`
  cases. The extraction portion now spans statutes/code chapters, CFR section
  scoping, directives, forest-plan chapters, appendices, maps, monitoring
  reports, split-page PDFs, OCR/table-heavy PDFs, and direct-file wrapper-page
  negatives under `config/upstream_evaluation_v1.json`.
- This packet is now historical routing context only. Phase 5 graph accuracy,
  Phase 6 review-contract closure, Phase 7 draft-generation closeout, and the
  newer Phase 8 routing all supersede this earlier note.

## Canonical Source Register Phase 3 Currentness, Supersession, And Source-Partition Rebase

Latest closeout on 2026-05-18:

- `authority-currentness` no longer needs the old `R1EA-*`-keyed authority
  inventory when the active catalog is canonical. If the active catalog rows
  carry `metadata.loader_contract = "source_register_v1"` and the default
  legacy currentness inputs are requested, the command now projects
  `authority_inventory_projected.json` and
  `source_addition_decisions_projected.json` directly from the active
  canonical catalog plus the workbook `Direct_File_Capture_Queue`.
- Canonical supersession lineage is now governed by
  `config/source_register_currentness_lineage_v1.json`. Superseded canonical
  rows can now prove either explicit replacement lineage or governed
  no-replacement dispositions such as reserved, revoked, or historical-only.
- The live root currentness gate now passes for
  `source-set-9dcf819bc4cca486` at
  `source_library/derived/source-set-9dcf819bc4cca486/authority_currentness/authority_currentness_report.json`
  with `77` authority families, `26` source-currentness records, `51`
  documented queue/source gaps, `24` catalog-confirmed current families, `1`
  superseded replacement confirmation, `active_review_corpus=24`,
  `currentness_supersession_archive=2`, and `validation_passed=true`.
- Canonical partition governance now overrides stale derived `source_partition`
  values when a `source_register_v1` row is historical, superseded, reserved,
  or otherwise currentness-only. Historical plan-amendment and transition
  support rows can no longer remain silently active just because an older
  catalog artifact serialized `active_review_corpus`.
- This packet is now historical routing context only. Phase 4 extraction
  fidelity, Phase 5 semantic graph gating, and the newer Phase 6 routing all
  supersede this earlier note.

## Canonical Source Register Phase 2 Capture And Catalog Cutover

Latest closeout on 2026-05-18:

- `config/downloader.toml` is now pinned to
  `loader_contract = "source_register_v1"`, so active `dry-run`,
  `preflight`, `download`, `batch-download`, and `catalog-build` calls now
  consume `Document_Register_Master` rather than the older
  `Ingest_Checklist` plus `R1_Forest_Plans` contract.
- Active capture commands now reject
  `--r1-forest-plan-register ... --source-delta-only`. The Region 1
  forest-plan source-delta register remains preserved `legacy_v0` baseline
  evidence only, not a second active ledger under the canonical runtime.
- The legacy `config/url_overrides.toml` registry is now ignored by active
  canonical runs. Canonical rows must carry their active official URL directly
  in the workbook until a governed canonical override surface exists.
- Live Phase 2 verification now includes:
  `source-register-validate` passing with `13` sheets, `635` retained load
  rows, `51` queue rows, and `2` removed rows;
  dry-run run `phase2-canonical-dry-run-20260518` passing with `635` planned
  rows, `635` unique URLs, and zero duplicate or excluded rows; and
  preflight run `phase2-canonical-preflight-20260518` passing its validation
  gate over the first `25` canonical rows while surfacing `18` live
  non-ready URLs and `7` `preflight_ok` rows.
- The first isolated canonical-register-driven catalog gate now lives at
  `source_library/runs/canonical-source-register-phase2-catalog-gate-20260518/catalog_gate/`
  as `source-set-ae989382c52344db` with `635` planned source rows,
  `635` unique URLs, zero artifacts, and `catalog_validation.json` passing.
- The upstream direct-eval bundle is now refreshed to `12` required category
  families and `24` total cases after adding the
  `canonical_source_delta_reintroduction_blocked` capture category. The live
  replay under `source_library/evaluations/upstream/` now passes `24/24`
  matched cases.
- Runtime cutover is complete, but this is not yet a full downloaded canonical
  corpus. The preserved legacy source-set baseline and downstream derived
  surfaces remain historical comparison points until the later currentness,
  extraction, and downstream rebase packets land.
- This packet is now historical routing context only. Phase 3 currentness and
  source-partition rebase has since landed, and Phase 4 is now the next routed
  implementation packet.

## Canonical Source Register Phase 1.5 Proving Slice

Latest closeout on 2026-05-18:

- The Phase 1.5 mixed proving packet is now implemented. The repo now ships:
  `config/source_register_proving_slice_v1.json`,
  `src/usfs_r1_ea_sources/source_register_proving.py`,
  `src/usfs_r1_ea_sources/authority_relationship_eval.py`,
  `src/usfs_r1_ea_sources/citation_alias_eval.py`,
  `src/usfs_r1_ea_sources/graph_health_eval.py`, and
  `src/usfs_r1_ea_sources/graph_accuracy_eval.py`.
- `source-register-proving-slice` now runs a governed `26`-row load-ready
  slice plus `5` queue rows from
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` through
  canonical loader validation, contract-based preflight, synthetic proving
  capture, scoped cataloging, authority-currentness input generation,
  relationship materialization, alias evaluation, graph-health assembly, and
  justification-path export without switching the active runtime workbook.
- The proving run now writes a latest-context pointer at
  `source_library/derived/source_register_proving/latest_context.json`.
  Historical note:
  Phase 3 now gives bare `authority-currentness` calls a higher-priority
  canonical path that projects currentness inputs from the active
  `source_register_v1` catalog and workbook queue when available. The proving
  context remains the fallback for narrow proving-only replays.
- The semantic proving bundle now has explicit contracts and eval surfaces:
  `config/graph_health_contract_v1.json`,
  `config/graph_accuracy_eval_v1.json`,
  `authority-relationship-eval`,
  `citation-alias-eval`,
  `graph-health-eval`, and
  `graph-accuracy-eval`.
- The proving packet also closed two contract gaps surfaced by the slice:
  canonical-register catalog rows now classify more source-register document
  types into review-graph roles instead of falling through to
  `document_role=source_document`, and source-partition logic no longer treats
  notes like `Current unless superseded ...` as inherently historical-only.
- The active runtime still remains pinned to `legacy_v0`, and the no-bulk-ingest
  boundary is now explicit in code, docs, and the proving report: bulk
  canonical-register ingestion may not bypass this Phase 1.5 packet.
- Historical note:
  at that closeout the next routed implementation packet was Phase 2 in
  `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md`. That
  boundary is now implemented; see the Phase 2 and Phase 3 sections above for
  the live runtime cutover, currentness rebase, and current next routing to
  Phase 4.

## Canonical Source Register Phase 1 Loader Refactor

Latest closeout on 2026-05-18:

- `WorkbookConfig.loader_contract` is now explicit, and the active runtime
  remains pinned to `legacy_v0` in `config/downloader.toml`.
- `load_canonical_sources(...)` in `src/usfs_r1_ea_sources/workbook.py` now
  dispatches between the legacy workbook parser and the new canonical
  source-register loader instead of assuming the old workbook contract is the
  only foundation path.
- `load_source_register_rows(...)` in
  `src/usfs_r1_ea_sources/source_register.py` now emits normalized canonical
  rows from `Document_Register_Master` only. Queue and audit sheets remain
  metadata surfaces and do not leak into downstream source-row emission.
- The normalized canonical row surface now carries explicit identity and routing
  seams:
  `authority_document_id`,
  `authority_document_class_id`,
  `authority_section_id`,
  `jurisdiction_scope_id`,
  `source_authority_link_id`,
  `direct_file_readiness_class`,
  `parser_route_id`,
  `parser_admission_class`, and
  `expected_parser`.
- The canonical loader now uses the staged alias and scope contracts as explicit
  seams and fails closed on blocked alias terms that do not have enough context
  to resolve a stable authority identity.
- The compatibility seam remains narrow:
  `load_source_register_workbook_sources(...)` adapts normalized canonical rows
  back to `WorkbookSource`, while the active runtime still uses the legacy
  workbook path until a later cutover packet changes the config.
- Legacy compatibility verification remained green after the refactor, and the
  stale dry-run expectation for the promoted forest-plan source-delta lane is
  now aligned to the live `160`-row, `1`-gap register baseline.
- At that closeout, the next routed implementation packet was Phase 1.5 in
  `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md`. That
  boundary is now implemented; see the Phase 1.5 section above for the live
  proving packet and current next routing to Phase 2.

## Canonical Source Register Phase 0 Freeze

Latest closeout on 2026-05-18:

- The final replacement workbook is now tracked in-repo at
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` with SHA256
  `46006b05052e90abdc80f8d23e074f1b4649eecb603de7479ddc7d250a462f7e`.
- `source-register-validate` and `source-register-diff` now exist as explicit
  contract commands for the staged canonical workbook.
- The frozen workbook-contract packet now lives in:
  `config/source_register_sheet_contract_v1.json`,
  `config/source_register_schema_v1.json`,
  `config/source_register_vocabularies_v1.json`,
  `config/source_register_row_states_v1.json`,
  `config/direct_file_readiness_contract_v1.json`, and
  `config/parser_admission_contract_v1.json`.
- The staged canonical workbook currently validates with `13` sheets,
  `635` retained load rows, `51` deferred queue rows, `2` removed rows, zero
  duplicate `Source_ID` values, zero duplicate master URLs, zero blank or
  non-HTTP(S) master URLs, and `5` stale-source-detector rows.
- The migration diff now locks the replacement boundary explicitly:
  the live runtime still owns `350` unique source rows (`190` legacy workbook
  rows plus `160` promoted source-delta rows, with `1` documented official
  source gap), while the staged canonical master owns `635` retained load rows
  with zero shared `Source_ID` values against either the legacy workbook or the
  promoted source-delta register.
- The semantic adjunct contract packet already present in the repo remains the
  governed baseline for normalized identity and graph semantics:
  `config/authority_document_ontology_v1.json`,
  `config/authority_relationship_types_v1.json`,
  `config/authority_relationship_register_v1.json`,
  `config/citation_alias_register_v1.json`,
  `config/jurisdiction_scope_register_v1.json`,
  `config/authority_ontology_eval_v1.json`, and
  `config/authority_relationship_eval_v1.json`.
- The baseline lock for inherited legacy behavior is now explicit:
  the active catalog remains `source-set-5e65d845ce77e1a0` with `350` rows and
  `319` artifacts, the current-promotion suite remains green, and the active
  full-canonical `phase-eval` artifact remains inherited-red at `9/12` with
  `reviewer_ready=false`.
- At that closeout, the next routed implementation packet was Phase 1 in
  `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md`. That
  boundary is now implemented; see the Phase 1 and Phase 1.5 sections above
  for the live loader split, proving packet, and current next routing to
  Phase 2.

## Compliance Review Test Boundary

Latest closeout on 2026-05-15:

- `tests/test_compliance_review.py` is now a `1388`-line core orchestration suite for
  `run_compliance_review(...)`, rule-pack gates, component gates, and package-search behavior
  only.
- Mixed-owner eval, coverage, gold-eval, and compliance-derived `phase-eval` coverage now lives in
  dedicated owner suites:
  `tests/test_compliance_review_eval.py` (`356` lines),
  `tests/test_compliance_coverage.py` (`242` lines),
  `tests/test_compliance_gold_eval.py` (`293` lines), and
  `tests/test_compliance_phase_eval.py` (`728` lines).
- Shared synthetic source-library and artifact builders now live under `tests/support/` in
  `compliance_review_fixtures.py` (`1096` lines),
  `compliance_component_fixtures.py` (`872` lines), and
  `compliance_phase_eval_fixtures.py` (`100` lines). `tests/__init__.py` and
  `tests/support/__init__.py` now make those shared helpers importable under pytest.
- `tests/test_compliance_review_test_boundary.py` now fails closed on core-suite forbidden imports,
  builder-helper regressions, sentinel ownership drift, and suite line-budget regressions.
- Focused compliance verification should now route by owner surface rather than treating
  `tests/test_compliance_review.py` as the catch-all command for eval, gold-eval, or
  `phase-eval` behavior.
- Closeout verification passed:
  `tests/test_compliance_review_test_boundary.py` `4/4`,
  the five focused compliance suites `68` tests with `3` subtests,
  the full closeout bundle `151` tests with `3` subtests,
  `ruff check src tests`,
  `python -m compileall src`,
  and the 2026-05-15 architecture probe.
- The fresh architecture probe no longer ranks `tests/test_compliance_review.py` as the repo's top
  hotspot. It remains active at `49` revisions and hotspot score `68012`, but
  `src/usfs_r1_ea_sources/evidence_graph.py` is now the top hotspot.

## Legacy Workbook Baseline Lock

The older workbook and promoted source-delta lane remain the preserved
`legacy_v0` baseline for comparison and replay:

- `Ingest_Checklist` ingest rows: `162`
- `Scope=Baseline` rows: `26`
- `Scope=Conditional` rows: `136`
- `R1_Forest_Plans` unit/overlay rows: `28`
- Total rows in the default ingest-driving sheets: `190`

The Region 1 forest-plan support-document register is promoted as a controlled supplemental
source-delta input at `config/r1_forest_plan_document_register_draft.csv`. The register has `189`
reviewed rows: `28` rows already confirmed in the workbook/catalog contract, `160`
`source_delta_required` rows that can be emitted as supplemental `WorkbookSource` records, and `1`
documented official-source gap that is counted but not planned for corpus download. The promoted
CLI path is:

```text
--r1-forest-plan-register config/r1_forest_plan_document_register_draft.csv --source-delta-only
```

The promotion validation is documented in
`docs/R1_FOREST_PLAN_DOCUMENT_REGISTER_PROMOTION_REPORT.md`. Under an explicit
`legacy_v0` config override, the register options are still accepted by
`dry-run`, `preflight`, `download`, `batch-download`, and `catalog-build`.
Active `source_register_v1` runs reject that lane so the canonical workbook
remains the sole active source ledger. The live source-delta
capture run `r1-forest-plan-source-delta-capture-20260510-batches` passed `33/33` batches for all
`159` emitted rows, with an empty repair queue and `158` unique artifacts. The scoped source-delta
catalog gate is archived under
`source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/catalog_gate/` as
`source-set-411b3736b3691eed` with `159` forest-plan support rows, `158` artifacts, `159`
`active_review_corpus` rows, and `catalog_validation.json` passing.

## Upstream Evaluation Coverage

Latest closeout on 2026-05-18:

- The repo now ships a tracked upstream direct-eval contract at
  `config/upstream_evaluation_v1.json`.
- Deterministic upstream fixtures now live under `config/fixtures/upstream_eval/` and
  `tests/fixtures/upstream_eval/`.
- The upstream contract now requires `12` named category families across
  capture, catalog, and extraction, with one expected-pass case plus one
  controlled-violation case per category for `24` total aggregate cases.
- The new Phase 2 capture category
  `canonical_source_delta_reintroduction_blocked` proves that active
  `source_register_v1` runs reject the legacy source-delta lane while explicit
  `legacy_v0` comparison runs still expose the old mixed-ledger behavior as a
  controlled violation.
- The promoted output family is
  `source_library/evaluations/upstream/upstream_evaluation_results.json` plus
  `source_library/evaluations/upstream/upstream_evaluation_report.md`.
- The closeout replay on 2026-05-18 passed `24/24` matched cases with
  `required_category_count=12`, `failed_case_ids=[]`, and lane summaries
  `capture`, `catalog`, and `extraction` all marked `direct_eval_present`.
- `docs/EVALUATION_COVERAGE_REGISTER.md` now separates structural validation from direct-eval
  coverage. The upstream rows `preflight`, `validate_run`, `catalog_validation`, and
  `extraction_accuracy` remain tracked as `direct_eval_present`; the downstream retrieval, claim,
  rule-claim, and compliance-review rows are now also promoted as `direct_eval_present` under the
  downstream contract described below.
- `phase-eval` now includes a separate `upstream_evaluation` phase sourced from the upstream
  aggregate summary and fails closed when that summary is missing or failing.
- The current active source-set readiness replay now passes `9/9` phases on
  `source-set-5e65d845ce77e1a0`, with `upstream_evaluation` present and passing alongside catalog,
  extraction, retrieval, evidence graph, claims, rule-claim binding, compliance coverage, NEPA 3D
  graph, and downstream direct evaluation phases.

## Downstream Direct Eval Strengthening

Latest closeout on 2026-05-13:

- The repo now ships a tracked downstream direct-eval manifest at
  `config/downstream_direct_eval_v1.json`.
- The default shipped downstream eval files are now contract objects:
  `config/retrieval_eval_seed.json`, `config/claim_eval_seed.json`,
  `config/rule_claim_link_eval_seed.json`, and `config/compliance_review_eval_seed.json`.
- Retrieval, claim, and rule-claim eval outputs now record locked coverage/threshold checks plus
  `recall@k`, `mrr`, `nDCG@k`, `false_positive_rate`, and
  `missing_required_source_rate`; hard negatives and multi-source cases are first-class shipped
  coverage rather than unit-test-only behavior.
- Compliance review direct eval now ships `5` governed cases covering `1` all-authorities control,
  `2` unrelated-package hard negatives, and `2` conditional subsets. Base-pack and
  generated-rule-pack cases are both supported, and generated-pack omissions are normalized as
  `not_applicable` for contract comparison.
- `compliance-coverage` now accepts the contract-object compliance eval format, so rule-pack
  coverage, eval-case coverage, and rule-claim link coverage fail closed against the same shipped
  downstream contract.
- The historical full-canonical downstream closeout on `2026-05-14` for
  `source-set-5e65d845ce77e1a0` passed retrieval `12/12`, claims `10/10`, rule-claim `24/24`,
  compliance review `5/5`, `compliance-coverage` with all rule-pack coverage checks green, and
  source-set `phase-eval` `9/9` with `downstream_direct_evaluation` present and passing.
- The latest bounded replay on `2026-05-15` for active source set `source-set-5e65d845ce77e1a0`
  is no longer fully green: `retrieval-eval` now fails `2/12` cases
  (`nepa-alternatives-environmental-effects`, `scoping-public-comment`) with
  `false_positive_rate=0.166667`, `missing_required_source_rate=0.076923`,
  `recall_at_k=0.923077`, `mrr=0.87037`, and `ndcg_at_k=0.867538`; source-set `phase-eval`
  therefore remains red, and the shared
  `reviews/compliance_review_eval/compliance_review_eval_results.json` artifact is also stale for
  this source set.
- `docs/EVALUATION_COVERAGE_REGISTER.md` now marks all four downstream lanes as
  `direct_eval_present`.
- The next evaluation-strengthening boundary remains
  `docs/PHASE_EVAL_DIRECT_EVAL_GATING_MILESTONE_PLAN.md`, but that seam is now resolved on
  2026-05-14 and is consumed by the broader operational recovery packet.
  Fresh ba8d source-set replays still auto-resolve the compatible archived current-promotion
  catalog gate at
  `source_library/runs/corpus-update-2026-05-01-cg-support-batches/catalog_gate/`, which carries
  `source-set-66c807eca2441d8a`. The exact catalog `source_set_id` differs because catalog identity
  includes workbook/config/override/git-commit lineage, but the archived gate's `sources` table
  exactly matches the `190` selected source-record IDs in
  `source_library/derived/source-set-ba8d0feae79501b8/diagnostics/extraction_manifest.jsonl`.
  `retrieval.py` now diversifies duplicate-source hits and rebalances title/topic/role/body
  scoring without double-counting metadata text, and the shipped retrieval contract in
  `config/retrieval_eval_seed.json` now excludes `source_delta_required` forest-plan-only rows that
  fall outside the ba8d current-promotion source universe while preserving `12` governed cases,
  `3` hard negatives, and `4` multi-source cases. The new regression guard in
  `tests/test_downstream_direct_eval_contracts.py` fails closed if those impossible rows drift back
  into the shipped contract.
- Fresh ba8d `retrieval-build` now passes again and emits a fresh SQLite index, fresh ba8d
  `retrieval-eval` now passes `12/12` with `false_positive_rate=0.0`,
  `missing_required_source_rate=0.0`, `recall_at_k=1.0`, `mrr=1.0`, and `ndcg_at_k=0.986357`, and
  source-set `phase-eval` now passes `11/11` with `threshold_failed_phase_count=0`.
- Fresh review-scoped current-promotion replay on 2026-05-14 is also green:
  `phase-eval --review-id v1-cg-ecid-compliance-review` now passes `23/23` with
  `contract_backed_promotion_ready=true`, `threshold_failed_phase_count=0`, and
  `review_direct_eval_status=direct_eval_present`.
- Current-promotion promotion-suite alignment is now repaired on `2026-05-14`:
  `config/promotion_suite_v1.json` now resolves `phase_eval_core` from
  `reviews/v1-cg-ecid-compliance-review/phase_eval_results.json`, and
  `tests/test_promotion_suite.py` now fails closed if the committed manifest drifts back to the ad
  hoc source-set artifact.
- Milestone `4` full-canonical promotion repair is now also resolved on `2026-05-14`:
  `config/promotion_suite_v1.json` now requires the actual active-source-set graph completeness
  signal for `full_canonical_nepa_3d_source_set_graph_summary`
  (`region1_forest_plan_graph_ready_profile_count>=10` and
  `region1_forest_plan_blocked_profile_count=0`) instead of the stale expectation that at least
  one promoted Region 1 profile must still be blocked.
- Fresh non-strict `promotion-suite --manifest config/promotion_suite_v1.json` now reports
  `current_promotion_ready=true`, `promotion_ready=true`,
  `full_canonical_corpus_ready=true`,
  `full_canonical_failure_category_counts={}`, and
  `expansion_ready=true`.
- Milestone `5` South Plateau strict-expansion recovery is now also resolved on `2026-05-15`:
  `config/replay_contexts/region1-expansion-south-plateau-landscape-treatment.json` now pins the
  South Plateau review to the archived ba8d-compatible catalog surface,
  `config/forest_plan_component_adjudications/region1-expansion-south-plateau-landscape-treatment.json`
  tracks the closed `31`-item component queue as `applicability_false_positive` system misses, and
  the shipped real-package/gold/promotion manifests now treat South Plateau as
  `reviewer_ready_expansion` rather than a typed blocked lane.
- Fresh South Plateau closeout replay on 2026-05-15 is green end to end:
  `forest-plan-component-adjudication-eval` passes with `resolved_adjudication_count=31`,
  `pending_adjudication_count=0`, and `system_miss_count=31`; `compliance-review` returns
  `reviewer_ready=true`; `v1-ea-eval --review-id region1-expansion-south-plateau-landscape-treatment`
  passes with `contract_status="reviewer_ready"`; and review-scoped
  `phase-eval --review-id region1-expansion-south-plateau-landscape-treatment` passes `19/19` with
  `contract_backed_promotion_ready=true`.
- Fresh ECID expansion replay on 2026-05-15 also refreshed the ad hoc expansion artifact to the
  correct ba8d current-promotion source set:
  `phase-eval --source-set-id source-set-ba8d0feae79501b8 --review-id region1-expansion-ecid-preliminary-ea`
  now passes `19/19` with `declared_review_contract=false` and no identity-mismatch blockers.
- Fresh `promotion-suite --manifest config/promotion_suite_v1.json` and
  `promotion-suite --manifest config/promotion_suite_v1.json --strict-expansion` now both pass
  with `current_promotion_ready=true`, `full_canonical_corpus_ready=true`, `expansion_ready=true`,
  `promotion_ready=true`, and `expansion_failure_category_counts={}`.
- The broader operational blocker-recovery packet in
  `docs/SYSTEM_OPERATIONAL_RECOVERY_MILESTONE_PLAN.md` is now fully resolved. Cross-forest profile
  eval coverage Milestones `1-4` are now resolved in code/docs, and forest-plan component-eval
  coverage Milestones `0-4` are now also resolved in code/docs. If the queued follow-on stack is
  resumed, the next active packet is now Phase `0` in
  `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md`.
- Forest-plan component-eval coverage Milestone `0` is now resolved through local commit
  `8fdcf25` (`docs: close component eval coverage milestone 0`): the live contract/result roster,
  West Reservoir in-scope decision, South Plateau routed-out decision, and ECID-only defaulting
  baseline are all pinned as the starting point for the broader component-coverage packet.
- Forest-plan component-eval coverage Milestone `1` is now resolved through local commit
  `965201e` (`eval: add component retrieval coverage gate`): the standalone source-set
  component-retrieval eval producer is live, the active-source-set contract replay is green, and
  the next routed slice is Milestone `2`.
- Forest-plan component-eval coverage Milestone `2` is now resolved through local commit
  `a69d09d`: the
  tracked review-scoped component coverage manifest exists, West Reservoir now has its own
  governed review contract, tracked `forest-plan-component-eval --review-id ...` no longer
  silently falls back to the ECID seed contract, and the next routed slice is Milestone `3`.
- Forest-plan component-eval coverage Milestone `3` is now resolved through local commit
  `e45d47e`: the
  aggregate `forest-plan-component-eval-coverage` lane is live, it consumes the standalone
  component-retrieval eval plus the tracked review-slot roster, it emits the governed aggregate
  results artifact under `source_library/evaluations/forest_plan_component_eval_coverage/`, and
  the next routed slice is Milestone `4`.

## Forest Plan Component Eval Coverage

Latest closeout on 2026-05-16:

- Milestone `2` closeout commit is `a69d09d`
  (`eval: broaden tracked component review coverage`).
- Milestone `3` closeout commit is `e45d47e`
  (`eval: add aggregate component coverage gate`).
- Milestone `4` closeout commit is `6cd5fd9`
  (`eval: wire component coverage gates`).
- The packet now resolves both the missing aggregate component-coverage gate and the missing
  readiness integration for that lane.
- The tracked manifest `config/forest_plan_component_eval_coverage_v1.json` now declares:
  the standalone retrieval-eval input,
  an explicit one-review-at-a-time future-forest expansion policy,
  and zero typed-blocked slots in scope for this packet.
- The repo now ships the public aggregate command
  `forest-plan-component-eval-coverage`, implemented in
  `src/usfs_r1_ea_sources/forest_plan_component_eval_coverage.py` and registered through
  `src/usfs_r1_ea_sources/cli_eval.py`.
- The aggregate producer writes
  `source_library/evaluations/forest_plan_component_eval_coverage/forest_plan_component_eval_coverage_results.json`
  and fails closed when the standalone retrieval lane is missing/red, when a tracked review slot
  is missing or unresolved, when West Reservoir lacks a valid contract/result, or when review or
  retrieval identities drift.
- `config/phase_eval_direct_eval_v1.json` now consumes:
  the standalone retrieval producer as the `forest_plan_component_retrieval` direct-eval-required
  phase for the active full-canonical source set, and
  the aggregate component-coverage summary as a tracked review-scope direct-eval input when the
  declared review ID is in the manifest-owned roster.
- `config/promotion_suite_v1.json` now requires:
  the full-canonical standalone component-retrieval eval artifact,
  the full-canonical aggregate component-coverage artifact, and
  a `phase_eval_core` summary whose `required_review_eval_ids` include
  `forest_plan_component_eval_coverage` for the tracked East Crazies current-promotion review.
- The latest live governed replays are green and fail-closed:
  `forest-plan-component-retrieval-eval` passes on `source-set-5e65d845ce77e1a0`,
  and `forest-plan-component-eval-coverage` now passes with
  `required_review_count=3`,
  `covered_review_count=3`,
  `missing_contract_count=0`,
  `missing_result_count=0`,
  `stale_identity_count=0`,
  `unresolved_review_count=0`,
  and `blocked_typed_slot_count=0`.
- The lane boundary remains explicit:
  standalone component retrieval proves source-set retrieval coverage only;
  aggregate component coverage proves tracked review-slot coverage only;
  neither artifact by itself proves reviewer-ready, adjudication closure, or live-package status.
- South Plateau remains explicitly out of this packet’s minimum governed review set.
- This milestone plan is now resolved.
- The next routed packet in the repo debt queue is now Phase `0` in
  `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md`.

## Phase Eval Orchestration Boundary

Latest closeout on 2026-05-16:

- Sequence `0` closeout commit remains `a983bdc`
  (`docs: close phase eval boundary sequence 0`).
- Sequence `1` closeout commit is `d013216`
  (`architecture: create phase eval owner boundary`).
- Sequence `2` closeout commit is `a29cee8`
  (`architecture: split phase eval helper owners`).
- Sequence `3` closeout commit is `708fd14`
  (`tests: split phase eval owner coverage`).
- Sequence `4` closeout commit is `fee4185`
  (`docs: close phase eval boundary packet`).
- `src/usfs_r1_ea_sources/phase_eval.py` now exists as the canonical owner for
  `PhaseEvalResult` and `run_phase_aligned_eval(...)`, and `src/usfs_r1_ea_sources/cli_eval.py`
  now imports the stable `phase-eval` command owner from that module.
- `docs/architecture_contract.toml` now defines a dedicated `phase_eval` layer for
  `phase_eval`, `phase_eval_support`, `phase_eval_optional_phases`,
  `phase_eval_direct_eval`, and `replay_context`, while the shared helper foundation now includes
  `artifact_utils`. Phase-eval result artifacts still belong to that owner boundary instead of the
  generic eval layer.
- `src/usfs_r1_ea_sources/evidence_graph.py` no longer defines the phase-eval entrypoints or
  provides the remaining neutral helper family. The graph owner is now `1205` lines;
  `src/usfs_r1_ea_sources/phase_eval.py` is `1376` lines;
  `src/usfs_r1_ea_sources/phase_eval_optional_phases.py` is `782` lines;
  `src/usfs_r1_ea_sources/phase_eval_support.py` is `176` lines; and
  `src/usfs_r1_ea_sources/phase_eval_direct_eval.py` remains `1675` lines.
- `tests/test_phase_eval_boundary_contract.py` now fail-closes canonical owner presence, stale
  entrypoint definitions in `evidence_graph.py`, stale phase-eval owner imports inside
  `evidence_graph.py`, reintroduced moved-helper definitions, and CLI import drift.
- `tests/test_phase_eval.py` now owns the focused phase-eval orchestration coverage, while
  `tests/test_evidence_graph.py` is down to `364` lines and no longer imports or exercises
  `run_phase_aligned_eval`. Shared setup builders for those suites now live in
  `tests/support/phase_eval_fixtures.py` (`412` lines), and `tests/test_phase_eval.py` is `730`
  lines.
- The final post-closeout size baseline for this resolved packet is:
  `src/usfs_r1_ea_sources/evidence_graph.py` `1205` lines,
  `src/usfs_r1_ea_sources/phase_eval.py` `1376` lines,
  `tests/test_evidence_graph.py` `364` lines, and
  `tests/test_phase_eval.py` `730` lines.
- The fresh architecture probe now reports `50` code files above `800` lines, no import cycles,
  `src/usfs_r1_ea_sources/project_sow_package.py` as the top hotspot, and
  `src/usfs_r1_ea_sources/evidence_graph.py` is no longer the top hotspot.
  `src/usfs_r1_ea_sources/phase_eval.py` remains below the `1800`-line budget.
- This packet is now resolved. The next routed packet is Phase `0` in
  `docs/CANONICAL_SOURCE_REGISTER_REFOUNDATION_MILESTONE_PLAN.md`.

## Cross-Forest Profile Eval Coverage

Latest closeout on 2026-05-15:

- Milestone `1` closeout commit is `46a2d49` (`eval: add cross-forest profile coverage gate`).
- Milestone `2` closeout commit is `5aaa5d4`
  (`eval: promote beaverhead and flathead profile coverage`).
- Milestone `3` closeout commit is `1999277`
  (`eval: cover remaining region1 tracking profiles`).
- Milestone `4` closeout commit is `a958dc8`
  (`eval: wire cross-forest profile coverage gates`).
- Milestone `2` promotes Beaverhead-Deerlodge and Flathead from thin fixture contracts to
  governed `covered` status under the aggregate lane. Both rows record
  `positive_case_count>=4`,
  `hard_negative_case_count>=3`,
  `selected_profile_compliance_case_count>=1`,
  and explicit richer `fixture_family_ids` instead of the older `1` / `1`
  placeholder contract.
- Milestone `3` now promotes the seven tracking-only Region 1 profiles from
  validated-but-`not_started` placeholders to governed scope-only covered status under the same
  aggregate lane. Each row now records
  `positive_case_count>=2`,
  `hard_negative_case_count>=2`,
  `selected_profile_compliance_case_count=0`,
  and explicit fixture-family coverage for
  `scope_positive`,
  `scope_positive_with_ambiguous_context`,
  `custer_hard_negative`, and
  `non_selected_non_custer_hard_negative`.
- The repo now ships a tracked aggregate cross-forest profile-eval contract at
  `config/region1_forest_plan_profile_eval_coverage_v1.json`.
- The new owner command is `forest-plan-profile-eval`, implemented in
  `src/usfs_r1_ea_sources/forest_plan_profile_eval.py` and registered through
  `src/usfs_r1_ea_sources/cli_eval.py`.
- The aggregate lane writes
  `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_results.json` and
  `source_library/evaluations/forest_plan_profile/forest_plan_profile_eval_report.md`.
- The producer reads the live readiness roster from
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` plus the runtime profile roster from
  `config/forest_plan_profiles.json`; it does not keep a second hand-maintained forest list.
- The current live replay on `source-set-5e65d845ce77e1a0` is green and fail-closed:
  `covered_profile_count=10`,
  `fixture_contract_defined_profile_count=0`,
  `not_started_profile_count=0`,
  `validated_not_started_profile_count=0`,
  and `profile_failure_count=0`.
- All `10` Region 1 rows now pass the governed aggregate lane. The tracking-only profiles are still
  evaluation-scoped rather than reviewer-ready scoped, but they no longer rely on `not_started` or
  thin `1` / `1` placeholder coverage.
- The NEPA 3D graph gate now refuses to treat promoted Region 1 profiles as sufficiently covered
  unless they meet the governed eval-fixture floor. The live source-set graph now reports
  `region1_forest_plan_promoted_profiles_with_eval_fixture_count=10` with `0` validation
  failures.
- `config/phase_eval_direct_eval_v1.json` now makes that same aggregate summary a required
  direct-eval input for the source-set `nepa_3d_source_set_graph` phase. Missing, stale,
  source-set-mismatched, or below-floor profile summaries now fail `phase-eval` instead of letting
  the full-canonical roster claim rely only on proxy graph counts.
- `config/promotion_suite_v1.json` now includes `full_canonical_forest_plan_profile_eval`, which
  fails the full-canonical promotion claim when the aggregate profile-eval summary is missing,
  stale, source-set-mismatched, or below the declared floor
  (`covered_profile_count=10`, `fixture_contract_defined_profile_count=0`,
  `not_started_profile_count=0`, `profile_failure_count=0`).
- The latest bounded source-set `phase-eval` replay on `2026-05-15` is still red overall, but the
  new `nepa_3d_source_set_graph` phase itself is green with
  `direct_eval_status=direct_eval_present`,
  `covered_profile_count=10`,
  `fixture_contract_defined_profile_count=0`,
  `not_started_profile_count=0`,
  and `profile_failure_count=0`. The remaining live blockers are outside this packet:
  `retrieval-eval` is red on `2/12` cases, and the shared
  `reviews/compliance_review_eval/compliance_review_eval_results.json` artifact is stale for this
  source set.
- `docs/EVALUATION_COVERAGE_REGISTER.md` now tracks this lane as
  `direct_eval_present`: the aggregate owner exists, the live roster is green, and the lane now
  feeds source-set `phase-eval` plus the full-canonical promotion suite without turning profile
  coverage into a reviewer-ready or live-package proof claim.
- The next routed follow-on after this packet is Milestone `0` in
  `docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`, which must refresh the now-closed
  cross-forest predecessor state before widening multi-review component-eval coverage.

## Gold Coverage Expansion

Latest closeout on 2026-05-13:

- The repo now ships widened gold contracts at `config/applicability_gold_eval_v1.json`,
  `config/compliance_gold_eval_v1.json`, `config/gold_coverage_v1.json`,
  `config/v1_west_reservoir_real_ea_eval.json`, `config/v1_south_plateau_real_ea_eval.json`, and
  `config/replay_contexts/v1-cg-ecid-compliance-review.json`.
- `applicability-gold-eval` now passes `12/12` adjudicated cases with `source_chunk_count=19`,
  all `19` high-priority families mapped into seven named coverage groups, and
  `promotion_ready=true`.
- `compliance-gold-eval` now passes `14/14` adjudicated cases, records the same seven named
  coverage tags plus the three package-style tags `clean_baseline`, `live_external_noisy`, and
  `typed_blocked_expansion`, and fails closed when those tags drift.
- `v1-ea-eval` now resolves tracked per-review contracts from
  `config/v1_real_package_review_coverage_v1.json` when `--review-id` is supplied, and still
  supports explicit typed blocked lane semantics. The current shipped contracts cover East Crazies
  (`reviewer_ready`), West Reservoir (`typed_blocked`), and South Plateau
  (`reviewer_ready_expansion`).
- `real-package-review-coverage-eval` is now the aggregate fail-closed owner for the three tracked
  real-package slots. The current routed manifest now requires
  `required_slot_count=3`, `covered_slot_count=3`, `distinct_forest_count=2`,
  `distinct_package_style_count=3`, `reviewer_ready_slot_count=2`,
  `typed_blocked_slot_count=1`, and `missing_package_authority_count=0`.
- `gold-coverage-eval` now reuses that manifest-owned real-package aggregate instead of owning a
  second review roster. The current aggregate contract now requires `required_theme_count=7`,
  `passed_theme_count=7`, `required_high_priority_family_id_count=19`,
  `distinct_forest_count=2`, `distinct_package_style_count=3`,
  `reviewer_ready_review_count=2`, and `typed_blocked_review_count=1`.
- `docs/EVALUATION_COVERAGE_REGISTER.md` now carries gold and real-review rows for
  `applicability_gold_eval`, `compliance_gold_eval`, `v1_ea_eval`,
  `real_package_review_coverage_eval`, and `gold_coverage_eval`, all marked
  `direct_eval_present`.
- `config/promotion_suite_v1.json` now consumes the widened applicability/compliance thresholds and
  the aggregate `gold_coverage_eval` artifact. The final closeout also patched legacy replay
  compatibility so current-promotion artifacts could be refreshed on
  `source-set-ba8d0feae79501b8`: `retrieval.py` now accepts old retrieval indexes that lack
  `support_document_role`, and `applicability.py` now falls back to the source set's archived
  extraction manifest when the merged top-level catalog has already moved on to a newer source set.
- The current non-strict promotion-suite replay now reports `current_promotion_ready=true`,
  `promotion_ready=true`, `full_canonical_corpus_ready=true`, and `expansion_ready=true`. Strict
  expansion is now green on the same manifest rather than carrying a separate South Plateau blocker.

## Full Canonical Corpus Promotion

Latest closeout on 2026-05-12:

- Active full canonical catalog in `source_library/catalog/` is now
  `source-set-5e65d845ce77e1a0`.
- The live active catalog was rebuilt from
  `corpus-update-2026-05-01-cg-support-batches` plus
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches` under the current working tree.
- Active catalog counts are `350` source rows, `319` unique artifacts, `332` unique URLs,
  `349` `active_review_corpus` rows, `1` `candidate_blocked_source` row, and `160` supplemental
  source-delta rows.
- The preserved Kootenai gap remains explicit through
  `source_delta_input.skipped_gap_source_record_ids=["R1PLAN-kootenai-nf-18"]` and
  `config/r1_forest_plan_official_source_gap_evidence.json`; it is not silently promoted into a
  downloaded source row.
- The active full-canonical derived lane is now materially refreshed on
  `source-set-5e65d845ce77e1a0`. That source set now owns fresh
  `authority_currentness`, `forest_plan_components`, `retrieval`, `evidence_graph`, `claims`,
  `rule_claim_links`, and `knowledge_graph` artifact families under
  `source_library/derived/source-set-5e65d845ce77e1a0/`.
- The refreshed full-canonical inventory on `source-set-5e65d845ce77e1a0` now builds `1416`
  components and `397` standards across all `10` tracked readiness profiles:
  `custer-gallatin-nf` (`329/58`), `beaverhead-deerlodge-nf` (`90/89`),
  `bitterroot-nf` (`23/3`), `dakota-prairie-grasslands` (`394/161`), `flathead-nf` (`80/20`),
  `helena-lewis-and-clark-nf` (`258/28`), `idaho-panhandle-nfs` (`52/8`),
  `kootenai-nf` (`53/8`), `lolo-nf` (`1/1`), and `nez-perce-clearwater-nfs` (`136/21`).
- The active inventory coverage now also verifies source-text accuracy for every emitted
  forest-plan component. `forest-plan-components-build` fail-closes if the canonical primary source
  chunk is missing, points at the wrong source record or artifact hash, or fails to re-emit the
  same component through `_components_from_chunk(...)`. The current active build on
  `source-set-5e65d845ce77e1a0` passed with `component_source_accuracy_passed=true` and
  `component_source_accuracy_failure_count=0`.
- The refreshed currentness and downstream derived surfaces on `source-set-5e65d845ce77e1a0`
  validate locally: `authority_currentness` reports `35` authority families and `207`
  source-currentness records; retrieval rebuilds with `75,745` chunks and `reviewer_ready=true`;
  evidence graph rebuilds with `157,315` nodes and `538,066` edges; claim extraction rebuilds with
  `101,856` claims; rule-claim binding rebuilds with `211` links and `0` gaps; and the active
  NEPA 3D source-set export passes with `66` checks, `0` failed checks, `2,889` nodes, and
  `6,212` edges.
- Flathead now also has an explicit source-backed extraction-admission gate on the active source
  set. On `2026-05-12`, all `17` required `R1PLAN-flathead-nf-01..17` records were refreshed by
  direct extraction into `source-set-5e65d845ce77e1a0`; the targeted
  `extraction-accuracy-audit --contract-path config/verified_extraction_admission_contract.json`
  passed `required_source_records_are_present_and_direct`,
  `chunks_match_extracted_text_offsets`, `chunk_coverage_has_no_gaps`,
  `extracted_text_has_no_markup_leakage`, and `pdf_text_crosscheck_against_pypdf`; and the audit
  admitted all `17` required Flathead records with `0` blocked. Retrieval now records
  `verified_extraction_contract_ids=["flathead-forest-plan-direct-extraction"]`,
  `verified_extraction_required_source_count=17`, and
  `verified_extraction_admitted_source_count=17`, so only verified accurate Flathead extractions
  are allowed into the knowledge-base lane.
- The Flathead live-package proving lane is now closed on the active source set. Review
  `west-reservoir-67436` on `source-set-5e65d845ce77e1a0` now passes package checklist,
  applicability validation, generated-rule-pack validation, Flathead forest-plan context
  validation, component adjudication, `compliance-review`, review-local `compliance-gold-eval`,
  and review-bound `phase-eval` `17/17` with `reviewer_ready=true`. The proving lane now records
  `44` applicable authorities, `23` non-applicable authorities, `0` unresolved decisions, a
  reviewer-ready `44`-rule generated pack, `48` resolved component adjudications with `0` pending,
  and gold-eval `10/10` passing cases with `promotion_ready=true`.
- The post-V1 promotion suite still separates current-promotion truth from full-corpus truth, but
  its full-canonical contract is now aligned to the refreshed active source set. The latest
  non-strict replay reports
  `current_promotion_source_set_id=source-set-ba8d0feae79501b8`,
  `current_promotion_ready=true`, `full_canonical_source_set_id=source-set-5e65d845ce77e1a0`,
  `full_canonical_corpus_ready=true`,
  `full_canonical_failure_category_counts={}`, and
  `expansion_ready=true`. The matching strict-expansion replay is also green on the same manifest.
- Sequence 1 of the Region 1 forest-plan inventory promotion plan is now closed as a config-owned
  contract. `config/r1_forest_plan_component_inventory_build_manifest.json` now covers all `10`
  readiness profiles for active full-canonical source set `source-set-5e65d845ce77e1a0`, keeps
  `plan_version` plus grouped build `source_record_id` inputs in tracked config, and validates
  against the live readiness roster through
  `src/usfs_r1_ea_sources/forest_plan_inventory_build_manifest.py`.
- Sequence 2 multi-forest builder hardening is now implemented in code and tests.
  `forest-plan-components-build` now supports `--manifest-path` for tracked Region 1 batch builds,
  preserves the existing single-forest `--source-record-id` / `--plan-version` path, and emits
  aggregate build coverage with per-profile results plus fail-closed cross-profile duplicate-ID
  checks.
- Sequence 3 of the Region 1 forest-plan inventory promotion plan is now implemented on the active
  source set. The live build writes `1416` components and `397` standards and validates all `10`
  tracked readiness profiles on `source-set-5e65d845ce77e1a0`.
- Sequence 4 readiness and promotion alignment is now closed for stale-surface repair, and the
  final parser/component recovery slice has promoted the remaining forests into tracked readiness.
  `config/region1_forest_plan_readiness_nepa_3d_v1.json` now promotes all `10` validated
  inventories, points at the refreshed `5e65...` coverage artifact, and the active NEPA 3D
  source-set export now reports `region1_forest_plan_graph_ready_profile_count=10` plus
  `region1_forest_plan_blocked_profile_count=0` without weakening
  `region1_completeness_claim=false`.
- The primary-plan role-classification milestone is now implemented in code and focused tests.
  When `catalog-build` runs with the Region 1 register, the five supplemental manifest-declared
  primary plan PDFs for `dakota-prairie-grasslands`, `flathead-nf`, `kootenai-nf`, `lolo-nf`, and
  `nez-perce-clearwater-nfs` classify as `document_role=forest_plan`, while ordinary supplemental
  register rows remain `forest_plan_support`.
- The live active catalog source set is now `source-set-5e65d845ce77e1a0`. In that current
  catalog, manifest-selected component-bearing plan chunks now parse successfully even when the
  selected source rows are `forest_plan_support`, legacy period-numbered forms such as
  `Standard 2.` and `Guideline 7.` now emit deterministic IDs, and `Standard No. 21.` style
  headings now parse without reopening duplicate-ID regressions.
- `config/forest_plan_profiles.json` now carries explicit resolver-profile entries for all `10`
  tracked readiness units rather than only the original Custer Gallatin plus the earlier
  Beaverhead and Flathead expansion slices. The newly added non-Custer profiles flatten
  readiness-contract multi-record document families into tracked per-part source roles so resolver
  selection can now be profile-owned across the full roster. The first two non-Custer
  reviewer-ready depth slices are now implemented for Beaverhead-Deerlodge and Flathead.
  Beaverhead carries district, landscape, management-area, overlay, and supporting-trigger
  vocabularies derived from the active local BDNF plan/support records; Flathead now adds
  district, geographic-area, focused-recreation, overlay, currentness, and supporting-route depth
  derived from the active local Flathead plan/support records. The compliance-review path now
  threads explicit `forest_unit_id` / `forest_plan_profiles_path` selection through
  `compliance-review`, `compliance-review-eval`, and `compliance-gold-eval`.
- `forest_plan_component_gate_reviewer_ready` is no longer hard-coded to
  `scope_status="custer_gallatin"`. Any explicitly selected in-scope forest-plan profile now has
  to pass the same reviewer-ready component/adjudication gate, while ambiguous or out-of-scope
  packages still remain non-required.
- The separate post-V1 expansion lane is now closed for the declared ECID preliminary-EA and South
  Plateau package set. Cross-forest profile eval coverage Milestones `1-4` are now resolved in
  code/docs, and component-eval coverage Milestone `0` is now closed as the live baseline
  rebaseline, so if this broader follow-on stack is resumed, the next step is Milestone `1` in
  `docs/FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MILESTONE_PLAN.md`.
- Expansion planning still proceeds one forest at a time:
  `docs/R1_BEAVERHEAD_PROFILE_EXPANSION_MILESTONE_PLAN.md` is the original reference slice,
  `docs/R1_FLATHEAD_PROFILE_EXPANSION_MILESTONE_PLAN.md` is the implemented second slice, and
  `docs/R1_MULTI_FOREST_PROFILE_EXPANSION_MILESTONE_PLAN.md` is retired to routing-note status
  only.
- If the older Flathead-specific expansion sub-lane is resumed later, its next step is not another
  profile-expansion sequence. It is the package-side proving lane in
  `docs/R1_FLATHEAD_LIVE_PACKAGE_PROVING_MILESTONE_PLAN.md`.
- The freshest fully replayed merged source-set evidence surface remains archived under
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`
  as `source-set-8a4005c8a083af1a`. That archived replay is still the all-green merged
  extraction/retrieval/graph/phase surface, while the merged-corpus East Crazies review replay on
  `source-set-8a4005c8a083af1a` now has tracked applicability adjudications at
  `config/applicability_adjudications/v1-cg-ecid-source-delta-review.json`. The replay-scoped
  applicability lane now passes with `56` applicable authorities, `340` non-applicable
  authorities, `0` unresolved decisions, and a regenerated `56`-rule generated rule pack. Replay
  compliance regeneration now writes `compliance_review.json` and a review-local
  `compliance_gold_eval_results.json` under
  `source_library/reviews/v1-cg-ecid-source-delta-review/`, and review-bound phase eval now
  prefers that review-local gold artifact over the unrelated global proving-lane result. The
  tracked gold contract now includes the current land-exchange rules, completed replay forest-plan
  adjudications no longer block review readiness merely because they are classified as
  `system_miss`, and the broader review replay now closes green at review `phase-eval` `18/18`
  with `reviewer_ready=true`.

The source-delta readiness gate is implemented by `forest-plan-source-delta-readiness`. The live
gate over `r1-forest-plan-source-delta-capture-20260510-batches` passed the earlier scoped source
delta baseline and now serves as the promotion guardrail for the active full catalog. The generated
JSON/Markdown report uses schema `r1-forest-plan-source-delta-readiness-v3` and is under the
source-delta run's ignored `source_delta_readiness/` directory. Historical Sequence 4 through
Sequence 6 readiness results:

- merged reuse inventory: `reuse_extraction=189`, `needs_extract=159`, `excluded=1`
- merged extraction summary: `341` extracted rows, `7` explicit `parser_error` rows, `1`
  scope-excluded row, `75,708` chunks
- support-document extraction readiness: `159` expected source-delta rows covered, `152` extracted
  rows, `7` explicit parser blockers, status `ready_with_blockers`
- current blocker classes: `pdf_text_fallback_empty=5`, `pdf_text_fallback_failed=2`
- retrieval validation: passed on `source-set-7e2652d23e764068` with
  `--catalog-dir source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/merged_catalog_gate`
  plus `--allow-failed-extraction --allow-partial-extraction`
- source-delta retrieval eval: `12/12` passed from
  `config/r1_forest_plan_source_delta_retrieval_eval.json`
- retrieval readiness: `ready_with_blockers`, with `152/152` extracted support-document rows
  indexed and the same `7` upstream parser blockers kept explicit
- Sequence 5 alignment closeout: merged-corpus chunks now carry register-backed
  `support_document_role` values for matching `R1PLAN-*` rows, including catalog-confirmed rows
  such as `R1PLAN-custer-gallatin-nf-06`, so the current retrieval eval pass is based on actual
  role-aware filters rather than source-ID-targeted shortcuts
- forest-profile readiness: `ready_with_blockers`, with configured profile readiness separated from
  register-only tracking coverage
- this archived readiness snapshot is now superseded by the active full-canonical truth on
  `source-set-5e65d845ce77e1a0`, which reports `10` graph-ready configured profiles and `0`
  blocked profiles
- current blocked forest-profile source IDs:
  `R1PLAN-beaverhead-deerlodge-nf-08`, `R1PLAN-bitterroot-nf-07`,
  `R1PLAN-dakota-prairie-grasslands-25`, `R1PLAN-idaho-panhandle-nfs-09`,
  `R1PLAN-idaho-panhandle-nfs-10`, `R1PLAN-kootenai-nf-08`, `R1PLAN-kootenai-nf-18`,
  `R1PLAN-lolo-nf-12`, and `R1PLAN-nez-perce-clearwater-nfs-18`

Sequence 4 runtime alignment update after that artifact:

- `extract-build` now treats `docling_unavailable` the same way it already treated
  `docling_timeout`: it falls back to `pypdf_text_fallback` when born-digital PDF text is
  extractable.
- external Docling execution is now opt-in through `USFS_R1_DOCLING_PYTHON` instead of being
  assumed from a repo-local `.venv-docling`.
- targeted live smoke over merged-catalog PDFs `R1PLAN-beaverhead-deerlodge-nf-02`, `-03`, and
  `-04` succeeded with `parser_name=pypdf_text_fallback`,
  `fallback_error_class=docling_unavailable`, and large extracted text payloads.
- the remaining blocker set is now narrow and explicit:
  `R1PLAN-beaverhead-deerlodge-nf-08`, `R1PLAN-bitterroot-nf-07`,
  `R1PLAN-dakota-prairie-grasslands-25`, `R1PLAN-idaho-panhandle-nfs-09`,
  `R1PLAN-idaho-panhandle-nfs-10`, `R1PLAN-kootenai-nf-08`, and `R1PLAN-lolo-nf-12`.
- Sequence 7 corpus incorporation and downstream replay is now implemented for merged support-document
  source set `source-set-7e2652d23e764068`.
- live downstream replay against the merged corpus is fresh through the source-set graph layer:
  `claim-extract --allow-partial-retrieval` now validates with `101,824` claims and
  `reviewer_ready=false`; `evidence-graph-build --allow-partial-retrieval` validates with
  `178,912` nodes and `559,467` edges while keeping inherited extraction blockers explicit;
  `rule-claim-link --allow-partial-claims` validates with `211` links, `0` gaps, and
  `reviewer_ready=false`; `nepa-knowledge-graph-export` validates with `1,837` nodes and `2,842`
  edges; and source-set `phase-eval` now passes `6/7` phases while remaining `reviewer_ready=false`
  only because extraction and inherited downstream reviewer-ready gates remain blocked.
- the stale-source-set gaps are closed for source-set replay: archived-catalog routing is explicit
  for evidence graph and phase eval, source-set-only phase replay ignores an unrelated root
  `compliance_gold_eval`, and the NEPA 3D graph contract now recognizes `extraction_blocked` and
  `official_source_gap`.
- the next work is not another source-set alignment pass. It is parser recovery for the seven
  blocked source IDs, resolution of the two official-source gaps, or an explicit review replay
  request against the merged corpus.

Latest refresh on 2026-05-10 supersedes that partial Sequence 7 state:

- `R1PLAN-nez-perce-clearwater-nfs-18` is now promoted from official-source gap to live
  `project_record`, so the Region 1 register now carries `160` source-delta rows and `1`
  preserved official-source gap (`R1PLAN-kootenai-nf-18`).
- refreshed source-delta capture is archived under
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/`, with scoped
  source set `source-set-bfe49a94e22fd1e2` and merged source set `source-set-8a4005c8a083af1a`.
- external Docling OCR replay clears all seven former PDF parser blockers. The merged extraction
  replay now validates with `349/349` required rows extracted, `0` failed rows, and `75,745`
  chunks.
- merged source-set replay is fully green: retrieval eval passes `12/12`, evidence graph validates
  with `153,198` nodes and `533,949` edges, claim extraction validates with `101,856` claims,
  rule-claim binding validates with `211` links and `0` gaps, the refreshed NEPA 3D source-set
  export validates with `1,789` nodes, `2,808` edges, `65` checks, and `0` failed checks, and
  source-set `phase-eval` passes `7/7` with `reviewer_ready=true`.
- `forest-plan-source-delta-readiness` now reports `160` source-delta rows, `0` extraction
  blockers, retrieval `ready`, and one official-source gap. Source readiness is broad enough to
  mark `beaverhead-deerlodge-nf` source-ready, but NEPA 3D graph promotion remains limited to
  `custer-gallatin-nf` until Beaverhead has a validated component inventory.
- merged-corpus review replay is now explicit under
  `source_library/reviews/v1-cg-ecid-source-delta-review/`. The review-scoped replay against
  `source-set-8a4005c8a083af1a` now carries a tracked applicability adjudication contract at
  `config/applicability_adjudications/v1-cg-ecid-source-delta-review.json`. Replaying that
  contract closes all `7` prior applicability conflicts: applicability validation now passes with
  `56` applicable authorities, `340` non-applicable authorities, `0` unresolved decisions, and a
  regenerated `56`-rule generated rule pack. The replay also now carries tracked forest-plan
  component eval and adjudication contracts at
  `config/forest_plan_component_evals/v1-cg-ecid-source-delta-review.json` and
  `config/forest_plan_component_adjudications/v1-cg-ecid-source-delta-review.json`. Replaying
  those contracts moves review `phase-eval` to `16/18` with `reviewer_ready=false`. Replay-scoped
  compliance regeneration now writes `compliance_review.json` and a review-local
  `compliance_gold_eval_results.json` under
  `source_library/reviews/v1-cg-ecid-source-delta-review/`, and review-bound phase eval now
  prefers that review-local gold artifact over the unrelated global proving-lane result. The
  tracked gold contract now includes the current land-exchange rules, completed replay forest-plan
  adjudications no longer block review readiness merely because they are classified as
  `system_miss`, and the replay now closes green at review `phase-eval` `18/18` with
  `reviewer_ready=true`.
- replay-context hardening is now implemented for that archived review lane. Tracked replay
  authority lives at `config/replay_contexts/v1-cg-ecid-source-delta-review.json`, and
  `phase-eval --review-id v1-cg-ecid-source-delta-review` now auto-resolves the archived
  `source-set-8a4005c8a083af1a` plus merged catalog gate instead of silently falling back to the
  active catalog. The replay repair lane is now closed: replay-scoped compliance review, review-local
  gold eval, and review-bound phase evaluation all pass against the archived merged catalog.
- `applicability-authority-universe` now accepts `--catalog-path` and `--source-set-manifest-path`
  so noncanonical merged-corpus review replays can use archived merged catalog gates without
  replacing `source_library/catalog/`.

The merged-catalog contract now supports both archived replay gates and active-catalog promotion.
`catalog-build` accepts repeated `--batch-run-id` values and an explicit `--catalog-dir` archive
target. The freshest fully replayed merged gate is archived at
`source_library/runs/r1-forest-plan-source-delta-capture-20260510-refresh-batches/merged_catalog_gate/`
as `source-set-8a4005c8a083af1a`. The active `source_library/catalog/` view is now the promoted
current-code full canonical source set `source-set-5e65d845ce77e1a0`, built from
`corpus-update-2026-05-01-cg-support-batches` plus
`r1-forest-plan-source-delta-capture-20260510-refresh-batches`, and validates `350` source rows,
`319` artifacts, `332` unique URLs, `349` `active_review_corpus` rows, `1`
`candidate_blocked_source` row, `160` supplemental source-delta rows, and one preserved official
source gap carried through `source_delta_input`.

The 26 `Scope=Baseline` rows are the baseline source records every EA compliance review must
evaluate. They are identified by the workbook `Scope` column, not by row position.

Baseline source record IDs:

```text
R1EA-001, R1EA-002, R1EA-003, R1EA-004, R1EA-008, R1EA-009, R1EA-010,
R1EA-013, R1EA-014, R1EA-015, R1EA-017, R1EA-018, R1EA-019, R1EA-020,
R1EA-021, R1EA-022, R1EA-023, R1EA-024, R1EA-025, R1EA-028, R1EA-029,
R1EA-031, R1EA-033, R1EA-034, R1EA-035, R1EA-067
```

The active full canonical downloader/catalog corpus now combines the full 190-row workbook contract
with the completed 160-row supplemental support-document capture:

- Parent batch runs:
  `corpus-update-2026-05-01-cg-support-batches` and
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches`
- Active full canonical catalog source set: `source-set-5e65d845ce77e1a0`
- Current-promotion reviewer-ready V1 source set: `source-set-ba8d0feae79501b8`
- Active reviewer catalog source rows: `350`
- Active reviewer catalog unique artifacts: `319`
- Active reviewer catalog source-artifact links: `349`
- Active source partitions: `active_review_corpus=349`, `candidate_blocked_source=1`
- Supplemental source-delta rows carried in the active catalog: `160`
- Preserved official-source gaps carried in `source_delta_input`: `1`

`R1EA-160` is still present in the catalog as a blocked `project_reference` because its URL remains
in `Scope_Exclusions`. `R1PLAN-kootenai-nf-18` remains explicit through the register/gap-evidence
contract rather than as a downloaded catalog row. The active catalog validation passes, the
captured-library integrity test suite passes against the promoted `source_library/catalog/`, and
the archived merged replay gate remains available as a separate downstream evidence surface.

## Authority Universe Family Inventory

Milestone 1 of the authority-universe completion plan is represented by
`config/authority_universe_families_nepa_ea_v1.json`. This file is the machine-readable crosswalk
between the required Region 1 EA authority families, the active workbook/catalog source records, the
current `nepa-ea-v0` rule pack, applicability predicate surfaces, package fact types, coverage
requirements, and eval cases.

Current inventory summary:

- Authority families: `35`
- Required authority requirement groups covered: `18`
- Family statuses: `active=33`, `candidate=1`, `superseded=1`
- Workbook source records crosswalked: `190/190`
- Current rule-pack rules crosswalked: `48/48`
- Authority-family rule templates: `19`
- Orphan rule IDs: none
- Orphan workbook source record IDs: none
- Families still requiring Milestone 2 source-currentness confirmation: `0`
- Families confirmed or documented by the Milestone 2 source-currentness gate: `21`
- Families requiring Milestone 3 rule-template work after currentness: `0`
- Families confirmed by Milestone 4 applicability eval expansion: `19`
- Families requiring Milestone 4 applicability eval expansion: `0`
- Milestone 5 compliance/report integration: implemented for generated compliance reviews through
  authority-family provenance, non-applicable authority appendix, reviewer-resolution report, and
  deterministic litigation-risk summary artifacts.

The only current `candidate` family is environmental justice and civil-rights authority coverage;
Milestone 2 documents a non-addition for revoked environmental-justice executive-order text and
keeps the family visible as a source-record gap for a later scoped workbook/source delta.
Reserved or superseded Forest Service NEPA regulations, including former 36 CFR part 220 references,
are represented as a `superseded` family and point reviewers back to current USDA NEPA procedure
sources under 7 CFR part 1b plus the Forest Service NEPA policy/currentness sources.

## Authority Family Rule Templates

Milestone 3 is implemented by `config/authority_family_rule_templates_nepa_ea_v1.json` and
`config/authority_family_rule_template_coverage_nepa_ea_v1.json`. The template config promotes the
`19` source-currentness-confirmed former `source_only` families into active, data-backed
authority-family rule templates without modifying the base `nepa-ea-v0` rule pack. Each template
records the authority-family ID, rule-template ID, primary and supporting source records, package
fact types, positive and negative package triggers, source filters, evidence expectations,
dependency/exception/supersession fields, and coverage follow-up metadata.

With the current 48-rule base pack, the full real-source authority universe comprises `48` base
rule-template candidates, `19` authority-family rule-template candidates, and `329` forest-plan
component candidates. The `19` template candidates are conditional and are included by default when
`applicability-authority-universe` runs from the repo with:

```text
config/authority_family_rule_templates_nepa_ea_v1.json
```

Use `--authority-family-templates-path` to point at a replacement template set, or
`--no-authority-family-templates` only for narrow legacy/unit runs that intentionally exclude the
expanded authority-family templates.

The templates map Clean Water Act, floodplain, tribal consultation, wilderness/designated-area, and
land-exchange package-fact cues to active authority families. Milestone 4 now supplies independent
positive/negative package fixtures and adjudication-quality scoring for these expanded families.

## Authority Currentness Gate

Phase 3 of the canonical source-register refoundation is now the active
currentness gate. The command still accepts explicit legacy authority-universe
inputs, but when the active catalog rows carry
`metadata.loader_contract = "source_register_v1"` and the default legacy
inputs are requested it now projects:

- `source_library/derived/<source_set_id>/authority_currentness/authority_inventory_projected.json`
- `source_library/derived/<source_set_id>/authority_currentness/source_addition_decisions_projected.json`

from the active canonical catalog plus the workbook `Direct_File_Capture_Queue`
and applies governed supersession lineage from
`config/source_register_currentness_lineage_v1.json`.

The latest local canonical report was generated for
`source-set-9dcf819bc4cca486` at:

```text
source_library/derived/source-set-9dcf819bc4cca486/authority_currentness/authority_currentness_report.json
```

Report summary:

- Schema: `authority-currentness-report-v0`
- Authority families checked: `77`
- Family status counts: `active=22`, `candidate=51`, `out_of_scope=3`,
  `superseded=1`
- Family/source currentness records: `26`
- Current authority family/source mappings confirmed from catalog: `24`
- Currentness-only archive source mappings: `1`
- Superseded source-record confirmations: `1`
- Family currentness: `source_currentness_confirmed=24`,
  `documented_source_gap=51`,
  `superseded_replacement_sources_confirmed=1`,
  `no_current_source_record=1`
- Failed families: `0`
- Validation: passed

This is now both a source-currentness and explicit source-gap gate for the
canonical ledger. It proves that active current coverage is driven by the
canonical register, that deferred queue rows remain visible candidate blockers
instead of silently disappearing, and that superseded or historical rows can
stay graph-visible without satisfying active rule coverage. The older
`source-set-ba8d0feae79501b8` legacy authority-universe report remains a
historical comparison surface only.

## Source Partition Contract For NEPA 3D

NEPA 3D Milestone 2A is implemented by `config/source_partition_contract_nepa_3d_v1.json`,
`src/usfs_r1_ea_sources/source_partitions.py`, new `catalog-build` `source_partition` fields, and
expanded `authority-currentness` validation. The source-partition contract is the pre-graph
boundary that keeps displayable currentness/supersession evidence separate from sources eligible to
derive active review rules. The current generated catalog was not regenerated for this docs/code
milestone, so the live partition proof is the `authority-currentness` report over the current
catalog surfaces.

Current partition values:

- `active_review_corpus`: current source records eligible for extraction, claims, applicability,
  generated rules, and compliance findings.
- `currentness_supersession_archive`: rescinded, revoked, superseded, reserved, or
  currentness-only records that may support only supersession/currentness graph relationships.
- `candidate_blocked_source`: candidate, blocked, excluded, failed, or unresolved source records
  visible as graph blockers but not active review authority.

The live `authority-currentness` run for `source-set-9dcf819bc4cca486` now records:

- catalog source partitions: `active_review_corpus=24`,
  `currentness_supersession_archive=2`;
- authority-family source roles: `active_authority_source=24`,
  `candidate_blocked_or_currentness_only_source=1`, and
  `supersession_or_replacement_source=1`;
- passing fail-closed checks that the source-partition contract defines the
  required partitions, active/non-active eligibility boundaries, non-active
  graph relationship limits, reserved `36 CFR part 220` archive handling,
  scoped workbook/source deltas, superseded-lineage metadata, and canonical
  catalog behavior where historical/currentness-only rows cannot remain active
  just because an older derived partition field serialized `active_review_corpus`.

The current source set does not yet add FSH 1909.15 chapter records. The contract keeps that as a
scoped workbook/source delta before any NEPA 3D graph export claims handbook completeness.

## NEPA 3D Graph Export Contract

NEPA 3D Milestone 1 is implemented by `config/nepa_3d_graph_contract_v1.json`,
`src/usfs_r1_ea_sources/nepa_3d_graph_contract.py`, `docs/OUTPUT_SCHEMAS.md`, and the smallest
source-set/review graph fixtures under `tests/fixtures/nepa_3d_graph/`. This is a contract slice
only: it defines the graph schema before the Milestone 3 source-set exporter or later 3D viewer is
built.

The contract validates:

- source-set and review export scopes, with `review_id` required for review-specific graphs;
- required node types for source sets, reviews, authority families, source records, artifacts,
  chunks, evidence spans, source claims, rule templates, applicability decisions, generated rules,
  compliance findings, forest-plan entities, readiness blockers, and graph lenses;
- required edge types for evidence paths, source/currentness relationships, package
  applicability, forest-plan overlays, compliance findings, and readiness blockers;
- required per-node provenance fields for each node type, including source-record, artifact,
  chunk, evidence-span, source-claim, rule-template, forest-plan, readiness-blocker, and graph-lens
  provenance;
- edge endpoint compatibility against the contract-declared source and target node types;
- display states for active, superseded, reserved, candidate, out-of-scope, applicable,
  not-applicable, unresolved, adjudicated, and readiness-blocked records;
- review-readiness states and blocker types so graph display status cannot be confused with
  reviewer readiness; and
- explicit `readiness_semantic_class` values so red graph items are exported as synthetic blocker
  nodes, blocked domain nodes, explicit blocker edges, or blocked relationship edges instead of
  relying on `display_status="readiness_blocked"` alone.
- lens metadata fields, required lenses, and referenced node, edge, and display-status values.

## NEPA 3D Source-Set Knowledge Graph Export

NEPA 3D Milestone 3 is implemented by `src/usfs_r1_ea_sources/nepa_knowledge_graph_export.py`, the
`nepa-knowledge-graph-export` CLI command, `tests/test_nepa_knowledge_graph_export.py`, and the
generated source-set graph outputs under
`source_library/derived/<source_set_id>/knowledge_graph/`. The builder is read-only over audited
catalog and derived surfaces; it does not scan raw artifact filenames.

The live export command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8
```

The live export for `source-set-ba8d0feae79501b8` now records:

- `validation_passed=true`, `62` validation checks, `0` failed checks, and
  `failure_category_counts={}`;
- `1,470` nodes and `2,648` edges;
- source-set content: `35` authority families, `190` catalog source records, `160` artifact nodes,
  `48` base rules, `19` authority-family templates, `211` source-claim nodes, and `329`
  forest-plan component nodes;
- source input joins: `740` catalog graph seed nodes, `759` catalog graph seed edges, `211`
  rule-claim links, current authority-currentness validation, evidence graph node/edge inputs, and
  forest-plan component inventory;
- Region 1 profile readiness: `10` tracked forest/grassland profiles, `1` graph-ready profile, `9`
  blocked broader Region 1 profiles, `1` Milestone 5 added profile with positive and hard-negative
  applicability fixture contracts, `3` graph-visible field-directive requirements, and `5`
  graph-visible overlay requirement groups;
- readiness blockers remain visible as graph nodes and edges, including the scoped
  `fsh_chapter_delta_required`, `forest_profile_not_ready`, and `missing_source` blockers.
- exporter-owned red semantics now distinguish blocker records from blocked domain surfaces and
  explicit blocker edges from inherited blocked relationships. The archived merged graph export for
  `source-set-8a4005c8a083af1a` has now been refreshed under this code path and records
  `validation_passed=true`, `65` checks, `0` failed checks, `1,789` nodes, `2,808` edges, `350`
  catalog source records, source partitions `active_review_corpus=349` plus
  `candidate_blocked_source=1`, and readiness blocker counts
  `forest_profile_not_ready=62`, `fsh_chapter_delta_required=2`, `missing_source=33`, and
  `superseded_source=3`.

## NEPA 3D Review-Specific Applicability Overlay

NEPA 3D Milestone 4 is implemented by the same
`nepa-knowledge-graph-export` CLI command with `--review-id`. The review overlay writes
`nepa_3d_graph.json`, nodes, edges, summary, and validation files under
`source_library/reviews/<review_id>/knowledge_graph/`. It reads the existing applicability-first and
compliance artifacts for the selected review; it does not rerun applicability or compliance review.

The live review overlay command:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources nepa-knowledge-graph-export \
  --output-dir source_library \
  --source-set-id source-set-ba8d0feae79501b8 \
  --review-id v1-cg-ecid-compliance-review
```

The live overlay for `v1-cg-ecid-compliance-review` now records:

- `validation_passed=true`, `76` validation checks, `0` failed checks, and
  `failure_category_counts={}`;
- `1,996` nodes and `3,550` edges;
- review content: `377` candidate authority nodes/decisions, `37` applicable decisions, `340`
  non-applicable decisions, `37` generated rules, `37` compliance findings, and `340` search
  coverage certificates;
- review graph checks that every candidate maps to exactly one decision, every non-applicable
  decision has search coverage or adjudication support, search-coverage certificate IDs resolve to
  covering certificate records, referenced retrieval and graph trace IDs resolve, generated rules
  derive only from applicable decisions, and compliance findings link to generated rules plus
  evidence spans.

## NEPA 3D Region 1 Forest-Plan Readiness Expansion

NEPA 3D Milestone 5 is implemented by
`config/region1_forest_plan_readiness_nepa_3d_v1.json`, the Beaverhead-Deerlodge and Flathead
profile additions in `config/forest_plan_profiles.json`, and expanded
`nepa-knowledge-graph-export` validation. This is a graph-readiness slice, not a broad
source-capture rerun: it makes the broader Region 1 forest-plan universe visible while blocking
any claim that Custer Gallatin artifacts prove Region 1 forest-plan completeness.

The readiness matrix now records:

- `10` tracked Region 1 forest/grassland profiles;
- `10` graph-ready profiles on the active full-canonical source set;
- `2` Milestone 5 added active profile contracts: Beaverhead-Deerlodge and Flathead, each with
  positive and hard-negative applicability fixture contracts;
- `0` active full-canonical blocked profiles, while archived blocker nodes remain visible for older
  readiness states and archived exports;
- `3` field-directive requirements and `5` overlay requirement groups, now rendered as
  graph-visible requirement nodes with source-record links where the readiness matrix has
  catalog-confirmed sources.

The graph export now validates that configured profiles and known Region 1 units are covered by the
readiness matrix, added profiles have source requirements and eval fixture contracts, promoted
profiles have catalog-confirmed sources and component inventory coverage, field-directive and
overlay requirements have graph nodes and source links, and `region1_completeness_claim=false`
even after the active full-canonical roster reaches `region1_forest_plan_graph_ready_profile_count=10`
with `region1_forest_plan_added_profile_count=2`,
`region1_forest_plan_added_profiles_with_eval_fixture_count=2`, and
`region1_forest_plan_blocked_profile_count=0`.
Sequence 0 of the Region 1 component-inventory promotion plan now also requires the forest-plan
component inventory input to be owned by the exporting source set. Borrowing
`source-set-8a4005c8a083af1a` component inventory artifacts while exporting
`source-set-5e65d845ce77e1a0` is treated as an explicit validation failure until the active source
set owns its own `forest_plan_components/` artifact family. That ownership gate is now satisfied on
the refreshed active-source-set replay; the remaining stale surfaces are readiness config and
promotion-suite full-canonical pointers.

## NEPA 3D Local Viewer

NEPA 3D Milestone 6 is implemented as a checked-in static viewer under `viewer/nepa-3d/`. The
chosen option is a repo-local browser surface over the normalized graph exports, not a generated
`source_library/` artifact and not a second knowledge base. The viewer uses Three.js plus
`3d-force-graph` from pinned CDN URLs, reads `viewer/nepa-3d/manifest.json` as a fallback manifest,
resolves the live dataset from `source_library/catalog/source_set_manifest.json` when possible, and
can load either the source-set graph or a matching review overlay graph. If the active catalog
source set has no graph export yet, the viewer falls back to the newest graph-capable source set
under `source_library/derived/`. It also accepts a local graph JSON file through the browser file
picker for ad hoc inspection.

Current viewer resolution state:

- active catalog source set:
  `source-set-5e65d845ce77e1a0`
- newest graph-capable source set on disk:
  `source-set-5e65d845ce77e1a0`
- current checked-in fallback manifest default:
  `source_library/derived/source-set-8a4005c8a083af1a/knowledge_graph/nepa_3d_graph.json`
- matching review overlays currently available for the resolved source set:
  none
- older review overlay still available for manual selection from the fallback manifest:
  `source_library/reviews/v1-cg-ecid-compliance-review/knowledge_graph/nepa_3d_graph.json`

Launch locally from the repo root:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8765/viewer/nepa-3d/
```

The first viewport opens directly into the graph experience. It now defaults to the
full validated knowledge base for the resolved current dataset, with laws, regulations, policies,
forest plans, and supporting documents visible before any review-specific narrowing. No review
overlay is attached unless the user selects or demos into one. Demo buttons above the Lens
dropdown switch among source library, authority graph, applicability, evidence path, forest plan,
readiness, and knowledge-base scenes; Reset demo returns to that full-knowledge-base starting
scene.
The evidence-path scene derives a source-record -> artifact -> chunk -> evidence-span ->
source-claim -> rule -> decision -> generated-rule -> compliance-finding spotlight from graph
edges, then exposes each step as a clickable item in the right-side Capability shown panel. Advanced
search and category controls remain available under Advanced filters. The graph surface now includes
scene labels for each demo scene and graph-native node labels rendered as Three.js sprites. Label
visibility is camera-distance aware: zoomed-out views show scene anchors, mid-zoom adds focus
labels, and close zoom adds additional node labels while preserving the same graph export and
readiness boundary. Controls cover source set, review, lens, search, status/readiness, authority
category, authority family, document role, currentness/partition, readiness blocker, node/edge type,
evidence/basis, forest unit, review phase, neighbor depth, high-degree hiding, selected-node
pinning, fit/reset, Clear filters, PNG export, and viewer-state JSON export. Lens and filter
dropdowns use graph-export counts and grounding metadata,
separate authority category from authority family, keep node/edge type distinct from evidence and
basis fields, read forest-unit values from exported forest codes, and treat selections as context
seeds so matching nodes remain visible even when the selected lens has no matching edges. The
detail panel shows node/edge provenance, citation labels, artifact hashes, source paths,
currentness metadata, validation status, and exported readiness classes for red items. Static tests
now lock the runtime URLs, relative graph-export manifest paths, category/filter boundaries, and
the `node_id`/edge endpoint mapping used by `3d-force-graph`. The viewer status line explicitly
records that layout does not change readiness. Legend, tooltip, detail, and status/readiness
filters now distinguish synthetic blocker nodes, blocked domain nodes, explicit blocker edges, and
blocked relationship edges when the export supplies the semantic field. Local browser smoke against
the refreshed `source-set-8a4005c8a083af1a` export verified the legend/filter taxonomy plus detail
rail rendering for one blocked forest-plan node and one explicit `HAS_READINESS_BLOCKER` edge.

## NEPA 3D Graph Validation And Promotion Gates

NEPA 3D Milestone 7 has its first promotion-gate slice implemented for the current source-set and
V1 review overlay graphs. Each graph validation check now carries a graph-specific
`failure_category`, and validation plus summary artifacts record `failure_category_counts`.
The summary now reports the Milestone 7 count dimensions explicitly: node type, edge type,
authority category, source status, source partition, source currentness status, applicability
status, and readiness blocker.
`phase-eval` adds `nepa_3d_source_set_graph` and `nepa_3d_review_graph` phases when those artifacts
exist. After review-packet row-completeness integration, the latest V1 review-bound phase eval
passes `21/21` phases with `reviewer_ready=true`, including both graph phases, the
`review_packet_index` phase, the final QA certification report, the post-V1 applicability family,
generated rule pack, decision-support report, compliance review, forest-plan component eval, and
gold eval.

## Review Packet Row Completeness

The East Crazies review packet now has a first-class row ledger and signer-facing index under
`source_library/reviews/v1-cg-ecid-compliance-review/review_packet_index/`. The generated family
includes `review_packet_row_inventory.json`, `review_packet_row_inventory.md`,
`compliance_matrix_render_manifest.json`, `review_packet_index.json`, `review_packet_index.md`,
`review_packet_index.pdf`, and `review_packet_index_validation.json`. The validation sidecar passes
with `37` applicable authority rows, `340` non-applicable authority boundary rows, `79` Forest Plan
component rows, `12` applicable Forest Plan standards, `4` dedicated land-exchange rows, `116`
rendered matrix rows, and no failed checks across `30` validation checks. It also keeps root-level
`East_Crazies_*` drafts out of the canonical packet boundary.

Decision support now live-validates that packet row sets match the compliance matrix and render
manifest without hashing downstream packet artifacts into the decision-support manifest. Final QA
does hash and gate the packet artifacts, exposes a `review_packet_index_qa` section, and validates
the refreshed packet at `196/196` checks. The current promotion suite requires the packet index
family plus final QA and passes current promotion with `31/31` required current results; South
Plateau no longer blocks expansion after the 2026-05-15 reviewer-ready closeout.

`config/promotion_suite_v1.json` now requires the source-set graph validation/summary artifacts and
the V1 review graph validation/summary artifacts before current promotion passes. The current live
graph gates pass with `62/62` source-set graph checks, `76/76` review graph checks,
`failure_category_counts={}`, `1,470` source-set graph nodes, `2,648` source-set graph edges,
`1,996` review graph nodes, and `3,550` review graph edges. Broader Region 1 profile readiness
blockers remain visible in the graph summaries and do not claim handbook or Region 1 forest-plan
completeness.

A NEPA 3D service capabilities brief is generated at
`docs/capabilities/nepa_3d_capabilities_brief.pdf` with matching HTML at
`docs/capabilities/nepa_3d_capabilities_brief.html`. The generator
`tools/build_nepa_3d_capabilities_brief.mjs` reads the current catalog manifest, source-set graph
summary and validation, phase-eval results, and promotion-suite status. It writes high-resolution
system graphics for the Region 1 knowledge-system architecture, evidence traceability, and the
Region 1 graph surface.
The brief presents reusable client-facing system capabilities and boundaries without named project
examples: the system structures fragmented Region 1 source, authority, evidence, and forest-plan
data for defensible, efficient land exchange execution. NEPA review is the V1 function, and the same
graph foundation can expand to additional workflows. Its three pages cover the core message,
supporting traceability architecture, and the R1 knowledge graph showcase with separate NEPA, USDA
regulation, source-evidence, and forest-plan layers.

## EA Consistency Decision-Support Generator

The East Crazies decision-support lane is complete through Sequence 5. Sequence 0 preflight recorded
the current artifact/count/hash baseline and closed with `go`; Sequence 1 added the tracked report
contract; Sequence 2 added the deterministic generator and public CLI command; Sequence 3 generated
the first local report family for the promoted East Crazies review; Sequence 4 made that family a
checked validation, phase-eval, and promotion-suite gate; Sequence 5 polished the Markdown/PDF
renderings for responsible official review without changing the canonical JSON schema. The tracked surfaces
are:

- `config/ea_consistency_decision_support_v1.json`
- `config/fixtures/decision_support/v1_ecid_decision_support_expected_summary.json`
- `tests/fixtures/decision_support/minimal_decision_support_report.json`
- `tests/test_ea_consistency_decision_support.py`
- `src/usfs_r1_ea_sources/ea_consistency_decision_support.py`
- `src/usfs_r1_ea_sources/cli_decision_support.py`
- `docs/OUTPUT_SCHEMAS.md`

The command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review
```

The existing generated report can be validated without rewriting it with:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-consistency-document \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --validate-only
```

The generator reads existing audited review artifacts and tracked config/fixture contracts, compares
the Sequence 1 hash/count baseline, fails closed on stale, missing, non-reviewer-ready, or
hash-mismatched inputs, and writes:

- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support.json`
- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support.md`
- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support.pdf`
- `source_library/reviews/<review_id>/decision_support/ea_consistency_decision_support_manifest.json`

The generated report keeps applicability status, compliance status, implementation-confirmation
status, and residual risk/legal-conclusion flags separate. The 2026-05-06 East Crazies run wrote the
ignored local report family under
`source_library/reviews/v1-cg-ecid-compliance-review/decision_support/`:

- `ea_consistency_decision_support.json`
- `ea_consistency_decision_support.md`
- `ea_consistency_decision_support.pdf`
- `ea_consistency_decision_support_manifest.json`

The latest Sequence 5 closeout regenerated and then validated that ignored local report family.
Validation returned `passed=true` and `reviewer_ready=true`, rechecked all current input hashes and
required report sections, kept all `37` applicable authority findings with package/source evidence,
kept the `340` non-applicable authority boundary with search coverage, represented all `329` Forest
Plan component rows, covered all `12/12` applicable standards with package and plan evidence, kept
`9` implementation-confirmation rows with evidence and `3` residual-risk notes with `0`
legal-conclusion risk flags, and confirmed the PDF starts with `%PDF-`. The Markdown/PDF now
front-load a use note, bottom-line reviewer-ready status, authority categories, Forest Plan basis,
applicable standards, non-applicable boundary, implementation confirmations, residual risks,
validation status, and concise table summaries before long evidence sections. The same closeout
replayed `phase-eval --review-id v1-cg-ecid-compliance-review`, which includes
`decision_support_report`; the current graph-gate pass now has V1 review-bound phase eval passing
`21/21` phases with `review_packet_index` and `reviewer_ready=true`. `promotion-suite` also reports the decision-support
JSON, manifest, PDF, and NEPA 3D graph validation/summary artifacts as required current-promotion
artifacts.
The post-sequence gap-close pass also makes validation fail closed when otherwise-current Markdown
or PDF outputs omit the supervisor-review front matter, review snapshot, table summaries, key
counts, required sections, or source-pointer content; those failures use
`false_negative_synthesis_omission` with explicit rendering source selectors. Generated
`source_library/` outputs remain ignored and are not staged. The EA consistency decision-support
milestone has no remaining planned sequence; future work should be a new milestone or a targeted
copy-review pass.

## East Crazies Final QA And Certification Replay Plan

`docs/EAST_CRAZIES_FINAL_QA_CERTIFICATION_MILESTONE_PLAN.md` is the completed focused plan for
turning the promoted East Crazy review into a replayable final QA packet. Sequence 0 baseline
replay, Sequence 1 contract/fixture work, Sequence 2 deterministic generator/CLI work, Sequence 3
gate integration, and Sequence 4 final packet QA/closeout are complete. The milestone is bounded to
review ID
`v1-cg-ecid-compliance-review` and source set `source-set-ba8d0feae79501b8`; it does not broaden
the claim to other Region 1 packages, does not resolve the South Plateau strict-expansion blocker,
and does not treat root-level `East_Crazies_*` draft exports as canonical artifacts.

Sequence 0 verified the promoted final-QA baseline from generated artifacts: `37` applicable
authorities, `340` non-applicable authorities, `0` unresolved authorities, `377` candidate
authorities, `37` generated compliance findings, `162` generated-pack rule-claim links,
`0` rule-claim gaps,
`43` package files, `1,265` package chunks, `329` Forest Plan component rows, `58` Forest Plan
standards, `12/12` Custer Gallatin applicable standards, passing decision-support validation, and
review-bound baseline `phase-eval` at `19/19` before final QA gate integration. Sequence 3 added
the final QA validation sidecar, review-scoped `phase-eval` passed `20/20` with
`final_qa_certification_report`, and non-strict `promotion-suite` passed `26/26` required
current-promotion results. The later row-completeness closeout adds the `review_packet_index` phase,
and the current replay passes `21/21` phase results and `31/31` current-promotion results. Later
recovery work also cleared the separate South Plateau strict-expansion blocker, so these older
packet notes no longer represent the current promotion-suite state.
Generated final QA outputs live under
`source_library/reviews/v1-cg-ecid-compliance-review/final_qa/` and stay ignored unless repository
policy changes.

The replay sequences are:

- Sequence 0: baseline replay and drift check over existing generated artifacts; complete on
  2026-05-07.
- Sequence 1: final QA contract and fixtures; complete on 2026-05-07.
- Sequence 2: deterministic generator and CLI with `--validate-only`; complete on 2026-05-07.
- Sequence 3: `phase-eval` and promotion-suite integration; complete on 2026-05-07.
- Sequence 4: rendered packet QA, docs/handoff closeout, and atomic commit; complete on
  2026-05-07.

Sequence 4 closed the remaining packet QA issues. `v1-ea-eval` now preserves `generated_at` when
the semantic payload is unchanged, so reruns no longer churn the final QA input hash. After the
row-completeness closeout, the final QA report renders both baseline counts that exclude final-QA
self-reference (`20/20` phase eval and `27/27` current-promotion results) and live integrated
counts (`21/21` phase eval and `31/31` current-promotion results). The final closeout stack is
ordered so mutating V1 eval output runs before the final QA refresh; the final validate-only replay
then still passes after `phase-eval` and non-strict `promotion-suite` add only the permitted final-QA
outer-gate drift.

The 2026-05-08 gap-close replay accepted the land-exchange row-contract hardening. The
decision-support expected summary and final-QA expected summary now carry
`required_applicable_authority_rows` for all four first-class land-exchange rows, and validation
fails closed with `missing_applicable_authority_row` if any required row is absent or loses its
expected source record, authority family, applicability mode/status, or pass status.
`final-qa-certification` refreshed the ignored packet and passed `196/196`;
`final-qa-certification --validate-only` also passed `196/196` without rewriting outputs after the
outer gate replay. The CLI result includes the review packet index, render-manifest, outer
self-reference, freshness, and required-row checks around that sidecar. The rendered Markdown
exposes the required caveats, source pointers, accepted V1 risk ledger, residual blockers,
baseline/live gate counts, and root-level draft exclusion, and the generated PDF starts with
`%PDF-1.4`.

Sequence 1 added `config/east_crazies_final_qa_certification_v1.json`,
`config/fixtures/final_qa/v1_ecid_final_qa_expected_summary.json`,
`tests/fixtures/final_qa/minimal_final_qa_certification_report.json`,
`tests/test_final_qa_certification.py`, and the schema docs. The contract pins semantic counts,
source selectors, current artifact hashes, selected Markdown/PDF rendering requirements, optional
human reviewer signoff fields, accepted V1 risk visibility, and fail-closed categories without
pinning full rendered body text. The Sequence 1 gap-close pass now requires every scalar
expected-summary count to appear in `required_count_fields`, keeps config and expected-summary
sections/output files/failure categories aligned by test, and records `validation_expectations`
that map missing gates, stale hashes/artifacts, count drift, missing selectors, missing
non-applicable boundary evidence, unresolved reviewer items, invalid PDF output, manual draft
dependency, hidden accepted V1 risk, legal-conclusion leaks, and human-certification overclaims to
fail-closed categories.

Sequence 2 added the `final-qa-certification` CLI command and the
`src/usfs_r1_ea_sources/final_qa_certification.py` artifact reader. Sequence 3 added
`east_crazies_final_qa_certification_validation.json` as the validation result consumed by
outer readiness gates. A live generation pass for `v1-cg-ecid-compliance-review` wrote the ignored
JSON, Markdown, PDF, manifest, and validation outputs under
`source_library/reviews/v1-cg-ecid-compliance-review/final_qa/`; a follow-up `--validate-only`
replay passed `168/168` checks without rewriting outputs. The command validates required gate
selectors, pinned input hashes, source/source-set identity, semantic counts, configured source
selectors, required applicable authority rows, PDF headers, accepted V1 risk visibility,
legal-conclusion safeguards, and the non-canonical root-level draft boundary. The validator tolerates
the self-referential outer
phase-eval/promotion-suite hash drift only when the extra passing gates are exactly the final QA
outer gates. The Sequence 3 gap-close pass records JSON/Markdown/PDF/manifest output hashes in the
validation sidecar and makes `promotion-suite` compare those hashes against the local files before
current promotion can pass. The Sequence 2 gap-close pass carries all `37`
compliance-matrix authority findings in `finding_qa.findings`, with per-row compliance-matrix
selectors, package/source evidence pointers, and trace IDs.

Certification in this plan means deterministic machine replay plus optional human reviewer signoff
fields. It does not mean final legal sufficiency, responsible-official approval, or counsel
certification.

## Project SOW Requirements Package

Project SOW package generation and operationalization through Sequence 7 are implemented as an
upstream planning lane for proposed-action intake before a complete EA review package exists. The
core package command is:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-package \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
```

The command reads a structured `project-sow-intake-v0` JSON file, the tracked resource-scope config
at `config/project_sow_resource_scopes_v1.json`, and
`config/authority_universe_families_nepa_ea_v1.json`. It writes a local requirements package under
`source_library/projects/<project_id>/requirements_package/`:

- `project_sow_package.json`
- `project_sow_package.md`
- `project_sow_package.pdf`
- `project_sow_package_manifest.json`

The package scopes resource-specialist work needed to prepare a defensible EA package. It selects
resource scopes from explicit intake fields, project type, trigger terms, resource indicator keys,
and proposed-action resource-area IDs, then records scope of work tasks, data needs, deliverables,
defensibility checks, selected authority families, an authority-to-resource matrix, and a
resource-analysis coverage matrix, and a compact reviewer summary with package boundaries and a
review checklist. The reviewer summary separates unresolved resource areas from calibration gaps
where scope of work content is required but no observed East Crazies report was supplied for that area. It also
emits a package-local intake evidence graph connecting project, proposed action, action elements,
evidence refs, triggered resource areas, selected resource scopes, required deliverables, and observed
specialist/supporting reports. JSON is canonical; Markdown and PDF are renderings from the same
package JSON. The first checked-in intake fixture is the East Crazies
land-exchange proposed action and currently selects ten resource scopes: NEPA project management,
lands/realty land exchange, Forest Plan consistency, wildlife/species/botany, cultural/tribal
resources, hydrology/wetlands/water quality, roads/access/recreation/designated areas,
vegetation/soils/air-quality/climate/carbon, minerals/energy/hazardous materials, and public
involvement/coordination.

The East Crazies fixture now also compares proposed-action-derived resource areas to the actual
specialist/supporting reports observed in the completed package: mineral potential, aquatics,
at-risk plants/botany, carbon, cultural resources, recreation special areas, recreation special
uses, roads/trails/access, tribal relations, wetlands, wildlife, water rights, and the
plan-consistency table. Validation requires every observed report resource area to have selected
resource scope coverage and to be traceable to a proposed-action resource area in the intake.

Operationalization Sequence 5 adds the reviewer adjudication loop:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-template \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-eval \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --adjudication <completed-project-sow-adjudication.json>
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-adjudication-apply \
  --intake config/fixtures/project_sow/east_crazies_land_exchange_intake.json \
  --adjudication <completed-project-sow-adjudication.json> \
  --output-intake <adjudicated-intake.json>
```

The template/worklist covers unresolved resource areas, missing evidence refs, unknown resource-area
IDs, calibration gaps, and optional deliverable decisions. Eval fails closed on stale input hashes,
missing, duplicated, unexpected, pending, invalid, or queue-identity-tampered rows, and incomplete
top-level or per-item reviewer metadata. Apply reruns eval and writes an adjudicated intake copy
with `project_sow_adjudication` replay metadata, including top-level reviewer metadata. Generated
packages from that intake surface adjudication status and decision counts in the reviewer snapshot
and command summaries. It does not mutate the original intake and does not edit generated package
outputs by hand.

Operationalization Sequence 6 adds the downstream EA package assembly handoff:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-ea-package-handoff \
  --package source_library/projects/<project_id>/requirements_package/project_sow_package.json
```

The command reads a passing canonical `project_sow_package.json` plus
`config/project_sow_ea_handoff_rules_v1.json` and writes
`project_sow_ea_package_handoff.json` plus `project_sow_ea_package_handoff.md`. East Crazies
currently emits `27` expected future-artifact slots: `10` source-collection, `10`
specialist-report-production, `1` public-involvement, `3` consultation, `1` Forest Plan
consistency, and `2` decision-record-support slots. Future artifacts are checklist expectations
only; the command does not require them to exist.

The Sequence 6 gap-close pass adds an explicit downstream consumption contract and tightens
handoff-rules validation. Future commands may consume package identity, input hashes, assembly
categories, assembly slots, and downstream boundaries, but must not infer artifact existence,
artifact sufficiency, authority applicability, generated rule-pack readiness, compliance findings,
legal advice, legal sufficiency conclusions, or final agency decisions from the handoff alone.

Operationalization Sequence 7 adds the local-only operational readiness gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources project-sow-operational-gate \
  --output-dir source_library/project_sow_operational_gate
```

The gate runs no-write intake validation for the minimal template and the three proving intakes,
the three-case `project-sow-eval`, package/rendering smoke checks for generated proving packages,
an East Crazies EA handoff smoke, and tracked JSON/docs checks before writing
`project_sow_operational_gate_summary.json` and `project_sow_operational_readiness_report.md`.
The command is intentionally not broad CI yet; the Sequence 7 closeout records it as local-only
until CI adoption is scoped as a separate milestone.
The Sequence 7 gap-close pass adds a machine-readable `closeout_contract`, expands tracked
docs/schema checks across the durable closeout set, fails closed on missing closeout-doc references,
and records output hashes for the gate report, proving eval summary, and EA handoff smoke artifacts.
The milestone closeout alignment pass adds
`docs/PROJECT_SOW_OPERATIONALIZATION_ACCEPTANCE_MATRIX.md`, which maps Sequences 1 through 7 to
their acceptance criteria and verification evidence; the operational gate now checks that matrix as
part of the durable-doc closeout set.

A scope of work service capabilities brief is generated at
`docs/capabilities/project_sow_capabilities_brief.pdf` with matching HTML at
`docs/capabilities/project_sow_capabilities_brief.html`. The generator
`tools/build_project_sow_capabilities_brief.mjs` mirrors the NEPA 3D capabilities-brief style and
uses the tracked system design artifacts rather than a single project example. The brief explains the service lane
for producing scopes of work: structured proposed-action intake, traceable resource selection,
contract-ready work package rendering, reviewer adjudication, operational-readiness gate, and
downstream EA package assembly handoff. It is two pages and intentionally general, with page-one
purpose and system facts sections plus a consolidated system-capability graphic replacing
project-example metric tiles.

An earlier requirements-package Sequence 5 CLI smoke run for the East Crazies intake selected `10`
resource scopes, found `23` proposed-action resource areas, emitted a `115`-node and `134`-edge intake
evidence graph, wrote a PDF with a valid `%PDF-` header, and reported `0` validation failures. Each
proposed-action-derived resource area has the canonical planning path:

```text
proposed_action -> action_element -> evidence_ref -> resource_area -> sow_scope
```

The requirements-package sequence plan for this lane is
`docs/PROJECT_SOW_REQUIREMENTS_PACKAGE_MILESTONE_PLAN.md`. The successor operationalization plan is
`docs/PROJECT_SOW_OPERATIONALIZATION_MILESTONE_PLAN.md`; Sequence 7 closes the operational gate and
release-closeout boundary for this branch.

This is a planning artifact only. It does not create applicability decisions, generated rule packs,
compliance findings, legal advice, legal sufficiency determinations, or final agency decisions.
Validation fails closed on missing required intake fields, unsupported intake schema, empty or
duplicated resource-scope config, unknown authority-family IDs, proposed-action resource areas that
cannot resolve to selected resource scope coverage, observed specialist-report resource areas that are
not derived from the proposed action or lack selected resource scope coverage, no selected resource
scopes, selected scopes without scope of work content, duplicate intake-derived graph IDs including
observed-report and required-deliverable collisions before graph assembly deduplicates nodes and
edges, dangling graph edges, missing action-element evidence refs, evidence-bearing action elements
with no triggered resource area, incomplete canonical resource-area graph paths, observed
specialist report areas without a proposed-action support path, land-exchange intakes with no
federal land action, or Markdown/PDF renderings missing required reviewer-facing sections.
Project-SOW adjudication eval additionally fails closed on stale hashes, missing queue rows,
unexpected or duplicate rows, changed queue identity fields, invalid item types, invalid decisions,
pending decisions, or incomplete reviewer metadata.
Project-SOW EA handoff validation additionally fails closed on invalid package schema, failed
package validation, missing selected scopes, unsupported handoff rules schema, incomplete handoff
categories, missing required handoff categories, unresolved or incomplete category rules,
incomplete downstream boundaries, missing explicit downstream boundary IDs, empty slots, or slots
without expected future artifact content.

## Verified State Snapshot

Latest full-corpus promotion verification was run locally on 2026-05-10 after the completed
forest-plan support-document refresh was promoted into the active catalog.

- Active catalog source set: `source-set-5e65d845ce77e1a0`
- Active download/catalog batch inputs:
  `corpus-update-2026-05-01-cg-support-batches` and
  `r1-forest-plan-source-delta-capture-20260510-refresh-batches`
- Catalog: `350` source rows, `319` unique raw artifacts, `349` source-artifact links, `332`
  unique URLs
- Supplemental support-document rows carried in the active catalog: `160`
- Preserved official-source gaps carried in `source_delta_input`: `1`
- Reuse inventory for the current source set is implemented and has been run locally. It classified
  `7` sources as already current in the Custer Gallatin slice, `181` sources as reusable from prior
  extraction outputs, `1` source as needing extraction, and `1` source as excluded.
- Reuse-first extraction assembly has been run for the full source set. It produced `190` terminal
  extraction manifest rows: `189` extracted rows, `1` scope-excluded row, `18,822` chunks,
  `188` reused rows, and `0` failed rows. `R1PLAN-dakota-prairie-grasslands-02` was parsed as the
  one fresh HTML extraction.
- Retrieval has been rebuilt from the assembled extraction layer with `18,822` chunks and
  `reviewer_ready: true`.
- Extraction accuracy audit passed for the current source set: `190` records checked, `189`
  extracted records, `18,822` chunks, no text-hash, raw-hash, offset, gap-coverage, markup, eCFR
  scope, or PDF token cross-check failures.
- Evidence graph has been rebuilt and is reviewer-ready with `38,601` nodes, `134,501` edges, and
  `0` retrieval-binding mismatches.
- Source-claim extraction has been rebuilt and is reviewer-ready with `43,353` claims, `9,818`
  entities, and `1.0` claim evidence/topic/authority coverage rates.
- Rule-claim binding for rule pack `nepa-ea-v0` version `0.4.0` has been rebuilt with `211` links
  across `48/48` rules, `0` gaps, and no rules without source-claim links.
- Compliance coverage has been refreshed for the `48`-rule matrix and `3` seed eval cases.
- Compliance review eval passed `3/3` seed cases. The Custer-scoped all-authorities fixture now
  expects `reviewer_ready: false` when the full forest-plan component gate is unmet.
- Compliance gold eval passed `10/10` adjudicated cases in the pre-applicability V1 artifact set.
  Under the current Milestone 8 gate, base-rule-pack gold eval reruns are diagnostic and are not
  `promotion_ready`; promotion readiness now requires a reviewer-ready generated applicability rule
  pack. Custer-scoped gold fixtures likewise preserve rule-level expected statuses while expecting
  the overall forest-plan component gate to fail readiness unless component evidence coverage is
  complete.
- Phase eval passed `19/19` phases with `reviewer_ready: true` for
  `source-set-ba8d0feae79501b8` and `v1-cg-ecid-compliance-review`, including the post-V1
  applicability artifact family, generated rule-pack gate, decision-support-report gate, and
  NEPA 3D source-set/review graph gates.
- The current Custer Gallatin LMP component inventory was generated from the active source-set
  chunks: `329` components, `58` standards, `536` selected plan chunks, `0` missing component IDs,
  `0` duplicate component or standard IDs, and `2` non-blocking inventory-quality issues.
  Component-like labels with nonnumeric number tokens, such as cross-reference/table headings, are
  suppressed from generated component IDs and surfaced in build coverage.
- Current generated-pack V1 EA gate artifacts were verified locally on 2026-05-08 for
  `v1-cg-ecid-compliance-review`. The regenerated compliance review is reviewer-ready with `37`
  generated compliance findings, `37` pass findings, all `26` baseline source records evaluated
  through the generated applicability rule pack, `162` generated-pack rule-claim links, and `0`
  rule-claim gaps.
- Forest-plan component eval passed `35/35` adjudicated cases for the promoted review. The current
  component findings have `329` components, `79` supported components, `250` not applicable
  components, `0` gaps, `12/12` applicable standards applied, and `0` reviewer-resolution items.
- The final pre-applicability V1 gate commands passed: `phase-eval` `10/10`, `v1-ea-eval` with
  `broader_ea_passed=true` and `forest_plan_passed=true`, `compliance-review-eval` `3/3`, and
  `compliance-gold-eval` `10/10`. Direct base-pack review/gold reruns are diagnostic; the current
  generated-pack review-bound phase eval can use the passing base-pack gold suite through
  `rule_pack_match_mode=generated_base`.
- The post-V1 applicability run for `v1-cg-ecid-compliance-review` validates cleanly with `377`
  candidate authorities, `37` applicable authorities, `340` not-applicable authorities, no
  unresolved/adjudication decisions, and `generated_rule_pack_ready=true`; the generated rule pack
  contains `37` rules and validates against the applicability artifacts.
- Authority-universe Milestone 5 is implemented in the compliance review layer. Generated review
  findings now carry candidate authority IDs, applicability decision IDs, authority-family IDs,
  generated applicability provenance, and coverage/adjudication references. The promoted review
  writes `authority_family_provenance.json`, `non_applicable_authority_appendix.json/.md`,
  `authority_reviewer_resolution_report.json`, and `litigation_risk_summary.json`; promotion
  checks require those artifacts before current promotion can pass.
- The post-V1 promotion suite is implemented at `config/promotion_suite_v1.json`. Sequences 1, 2,
  2A, and 2B have closed the ECID `adjudication_needed`, `missing_source`, and
  `forest_plan_reviewer_not_ready` expansion blockers. Sequence 3 selected the South Plateau Area
  Landscape Treatment Project as the third real package under review ID
  `region1-expansion-south-plateau-landscape-treatment`. Sequence 4 imported `26` official South
  Plateau PDFs from the project Box folder, built the package cache with `.venv-docling`, extracted
  `26/26` files into `3,671` chunks, and ran the applicability-first path through validation.
  Sequence 5 completed the six positive/negative-trigger adjudications as replayable
  `human_applicable` decisions, evaluated and applied them, and reran validation. Sequence 6 then
  generated and validated the South Plateau rule pack, ran compliance review, matrix/PDF output,
  review-scoped phase eval, and added South Plateau required expansion artifact checks to the
  promotion suite. South Plateau applicability validation passes: `61` authorities are applicable,
  `331` are non-applicable, `0` are unresolved or `needs_adjudication`, and
  `generated_rule_pack_ready=true`. Generated rule-pack validation passes with `61` rules and hash
  `39663183f91ad309fcfad60a17d0d88b371e184df8f06664cadd612b5c7aebec`. The authority-review layer
  still emits `61` findings, `41` pass, `19` uncertain, `1` gap, `280` rule-claim links, and `0`
  rule-claim gaps. The South Plateau forest-plan context pass now resolves the package to
  `scope_status="custer_gallatin"` with context `validation_passed=true`, `2` geographic areas,
  `9` management areas, `4` overlays, `5` supporting-plan routes, and `0` unresolved mentions.
  The remaining blocker is narrower: forest-plan component evaluation has `329` components,
  `152` applicable components, `24` applicable standards, `21` applied standards, and `31`
  `missing_package_evidence` items in the component adjudication worklist. The South Plateau
  expansion slot remains `ready=false` with `failure_category="forest_plan_reviewer_not_ready"`,
  and the manifest now records the component findings, reviewer queue, adjudication template, and
  pending adjudication eval as expected gate artifacts. Strict
  promotion suite was written to
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion/`
  and now fails as expected with `current_promotion_ready=true`, `promotion_ready=false`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`,
  `failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `open_expansion_artifact_count=5`, and `open_expansion_slot_count=1`. Non-strict promotion suite
  was rerun last and keeps current promotion green with `current_promotion_ready=true`,
  `promotion_ready=true`, `failure_category_counts={}`, and the same expansion-only blocker counts.
  Promotion-suite manifest validation now fails selected not-ready slots that omit
  review/package/source-set metadata, expected gate artifacts, next action, or a typed
  non-`package_fixture_missing` failure category. Ready slots must retain that
  review/package/source-set contract, omit failure categories, and list expected gate artifacts
  covering the matching review case's `required_for_expansion` artifact IDs; declared forest-plan
  profile slots must also prove reviewer-ready profile context before strict expansion can pass.
- The first Milestone 10 expansion pass has a local review ID:
  `region1-expansion-ecid-preliminary-ea`. The package cache extracted `7` PDFs into `160` chunks.
  Evidence-arbitration Milestone 4 replay covered `392` candidate authorities, with `43`
  applicable, `346` non-applicable, and `3` `needs_adjudication` authorities. The Sequence 1
  adjudication replay resolved cultural-resource/SHPO, minerals/energy, and species-supporting
  sources/overlays to `human_applicable`; `applicability-validate` now passes with `46` applicable
  authorities, `346` non-applicable authorities, `0` unresolved, `0` `needs_adjudication`,
  `generated_rule_pack_ready=true`, and `reviewer_ready=true`.
- The Sequence 2 ECID artifact pass generated and validated
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/applicability/generated_rule_pack.json`
  with `46` rules, ran compliance review with that generated rule pack, wrote the compliance
  matrix JSON/Markdown/PDF, wrote
  `source_library/reviews/region1-expansion-ecid-preliminary-ea/phase_eval_results.json`, and
  generated `forest_plan_component_adjudication_template.json/.md`. The generated-pack gate passes,
  and Sequence 2A reports `rule_claim_gap_count=0` and `rule_claim_link_count=211`. Sequence 2B
  completed the `158`-item Forest Plan component adjudication replay, ran
  `forest-plan-component-adjudication-eval`, reran ECID compliance review with
  `--reuse-package-cache`, and reran review-scoped phase eval. The adjudication eval resolved all
  `158` rows as true EA package-evidence omissions with `0` system misses; compliance review now
  reports `reviewer_ready=true` and validation passes without treating those omissions as component
  support. The Sequence 2B closeout pass also tightened the adjudication template/eval contract so
  resolved items carry compact component/source trace references and fail if source-record,
  citation, hash, chunk/page, or available offset/span fields are dropped.
- The ECID roads/access/special-use adjudication item exposed the pre-Milestone-3
  evidence-arbitration gap: weak auxiliary trigger evidence could block an authority family even
  when strong independent roads/access/right-of-way evidence was present. The repair sequence is
  documented in `docs/EVIDENCE_ARBITRATION_MILESTONE_PLAN.md`.
- Evidence-arbitration Milestones 1 and 2 are implemented as behavior-preserving diagnostics.
  Applicability decision rows include `arbitration_summary` records, `applicability_report.md`
  renders arbitration diagnostics for `needs_adjudication` rows, and package/decision evidence now
  carries structured `evidence_strength` details while preserving existing `confidence_class`
  values. The Milestone 1/2 gap-close pass tightened weak-signal reason strings, expanded
  no-action/no-change background classification, preserved matched negative phrases when available,
  and added package graph assertions for fact/context/uncertainty `evidence_strength` fields. This
  diagnostic foundation is now used by Milestone 3.
- Evidence-arbitration Milestone 3 is implemented as the behavior-changing trigger-arbitration
  predicate. Strong, rule-contract-sufficient positive trigger groups can now carry an
  `applicable` decision while weak auxiliary trigger evidence stays visible in arbitration notes,
  reviewer notes, report diagnostics, and decision evidence. All-weak positives still require
  adjudication, and strong positive evidence plus explicit negative/out-of-scope evidence still
  requires adjudication by default.
- Evidence-arbitration Milestone 4 is implemented as the real-package replay/gate-alignment slice.
  ECID roads/access/special-use, Clean Water Act/WOTUS, and EO 11988 floodplain authority-family
  templates now resolve to `applicable` from strong independent trigger evidence. The later
  post-V1 expansion Sequence 1 replay resolved the remaining ECID cultural-resource/SHPO,
  minerals/energy, and species-supporting sources/overlays conflicts through replayable
  adjudication. Forest Plan component non-applicable decisions carry explicit scope-miss evidence,
  and ECID applicability validation now passes with no unresolved authority conflicts.
- Evidence-arbitration Milestone 5 is implemented as the eval and promotion/phase reporting slice.
  `applicability-eval` now has `9` seed cases with explicit arbitration expectations covering
  strong-positive plus weak auxiliary evidence, weak-only evidence, positive/negative conflicts,
  no-action/background-only evidence, and rule-template-specific trigger sufficiency. The latest
  local eval run passed `9/9` seed cases with arbitration status/effect match rates of `1.0` and
  arbitration summary counts of `1` applicable-with-weak-auxiliary, `2` weak-only
  needs-adjudication, `1` insufficient-strong-trigger needs-adjudication, and `1`
  positive/negative-conflict needs-adjudication. `applicability-gold-eval` passed `5/5` cases and
  now requires at least one gold case with explicit arbitration-field expectations.
- Latest South Plateau forest-plan context verification on 2026-05-07 reran the cached South
  Plateau compliance review, generated the `31`-item forest-plan component adjudication template,
  evaluated it in pending state, reran South Plateau phase eval at `15/17`, restored the promoted
  V1 review-scoped phase eval at `20/20`, passed non-strict promotion with
  `current_promotion_ready=true`, and proved strict expansion fails only on
  `forest_plan_reviewer_not_ready`.
- Latest NEPA 3D graph-gate verification on 2026-05-06 regenerated the source-set and V1 review
  graph exports, reran V1 review-scoped phase eval at `19/19`, and passed non-strict promotion
  suite with `22/22` required current-promotion results, `failure_category_counts={}`, and
  `expansion_failure_category_counts={}`. Latest post-V1 real-package expansion verification on
  2026-05-06 reran South Plateau review-scoped phase eval at `16/16`, restored the promoted V1
  review-scoped phase-eval artifact at `19/19`, kept non-strict current promotion green, and made
  strict expansion fail closed only on `forest_plan_reviewer_not_ready`. Focused pytest,
  architecture-contract, ruff, compileall, JSON validation, and `git diff --check` gates are the
  closeout verification for the
  tracked slice.
- The evidence-arbitration plan is complete through commit `f304e2e`. The post-V1 real-package
  expansion milestone is complete through Sequence 7 for the declared ECID preliminary-EA and South
  Plateau expansion slots. The South Plateau forest-plan context milestone is complete in the
  typed-blocker state: Custer Gallatin context is resolved, but strict expansion is intentionally
  blocked until the 31-item component adjudication queue is completed and passes eval. Future
  expansion should add a new
  verified real-package slot and matching promotion-suite review-case artifact checks rather than
  weakening the current gate.

Previous full downstream promotion snapshot was verified locally on 2026-04-30 before the rule-pack
`0.4.0` baseline expansion and before the later 186-row and 190-row catalog updates.

- Active source set: `source-set-e364ea220cffd938`
- Base phase eval: passed, `8/8` phases reviewer-ready
- Compliance phase eval: passed, `9/9` phases reviewer-ready for
  `demo-compliance-matrix-authority-v03-ecid-2026-04-30`
- Catalog: `147` source rows, `131` unique raw artifacts
- Extraction: `147/147` selected sources extracted, validation passed
- Retrieval: `13,619` chunks indexed, validation passed, reviewer-ready
- Evidence graph: `36,578` nodes, `106,182` edges, validation passed, reviewer-ready
- Retrieval-to-graph binding mismatches: `0`
- Source claim graph: `35,348` claims, `8,479` entities, `90,153` nodes, `231,214`
  edges, validation passed, reviewer-ready
- Claim eval seed: passed, `2/2` cases
- Rule-claim binding: `92` links across `20/20` authority compliance rules, `0` explicit no-claim
  gaps, validation passed, reviewer-ready
- Rule-claim eval seed: passed, `20/20` authority cases
- Compliance coverage: `20/20` rules covered by matrix rows, source-claim links, source-claim
  terms, and compliance review eval cases
- EA review smoke: `review_validation.json` passed for `smoke-ea-review-v0-hardened`
- Compliance demo review: authority-first `compliance_validation.json`, `compliance_matrix.json`,
  and `compliance_matrix.pdf` passed for
  `demo-compliance-matrix-authority-v03-ecid-2026-04-30` under the pre-`0.4.0` 20-rule pack
- Compliance review eval seed: passed, `3/3` cases
- Compliance gold eval: passed, `10/10` adjudicated cases in the pre-applicability gate; base-pack
  reruns are now diagnostic and not `promotion_ready`
- Unit suite: `132` tests passed

Post-baseline-expansion verification on 2026-04-30:

- `config/compliance_rule_pack_nepa_ea_v0.json` validates with `26` declared baseline source records
  and `44` total rules.
- `tests/test_compliance_review.py` passes with `32` tests.
- `git diff --check` passed before commit `720d75c`.
- Superseded by the 2026-05-01 current-source-set refresh above, which closed the
  `forest_service_directives_portal` / `R1EA-028` source-claim link gap and promoted coverage/gold
  eval artifacts for rule-pack `0.4.0`.

The full downstream promotion verification set for the prior 147-row source set was:

```bash
PYTHONPATH=src uv run --extra dev pytest
PYTHONPATH=src python -m compileall src
PYTHONPATH=src uv run --extra dev ruff check src tests
git diff --check
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v0.json
PYTHONPATH=src .venv-docling/bin/python -m usfs_r1_ea_sources compliance-review \
  --package-path "source_library/reviews/_intake/demo-ea-2026-04-30/East Crazy Inspiration Divide Land Exchange (63115)" \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --review-id demo-compliance-matrix-authority-v03-ecid-2026-04-30 \
  --docling-timeout-seconds 180
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library \
  --review-id demo-compliance-matrix-authority-v03-ecid-2026-04-30
```

## Storage Model

The system stores source material in layers.

### Raw Artifacts

Path:

```text
source_library/artifacts/raw/
```

Raw artifacts are downloaded bytes saved before extraction or transformation. They are grouped by host and named with stable source/title slug information plus a SHA256 prefix. The downloader does not overwrite validated artifacts during normal resume behavior.

Artifact metadata is recorded in manifests and catalog records:

- `artifact_path`
- `artifact_sha256`
- `artifact_byte_size`
- `content_type`
- `fetch_timestamp`
- `final_url`

### Row Manifests

Path:

```text
source_library/manifests/download_<run_id>.jsonl
```

Each manifest is JSONL with one row per workbook source in that run. A row records workbook provenance, original URL, effective URL after overrides, normalized URL, final URL, artifact metadata, status, duplicate links, validation result, and failure evidence when applicable.

For full-batch operation, the parent batch ledger points to many child download manifests.

### Batch Evidence

Current parent batch path:

```text
source_library/runs/corpus-update-2026-05-01-cg-support-batches/
```

The parent batch run contains:

- `batch_plan.json`
- `batch_ledger.json`
- `summary.json`
- `operator_report.md`
- `repair_queue.csv`

Each child batch also has its own run directory under `source_library/runs/<child-run-id>/` with its own summary, report, events, failures, and acceptance gate.

### Reviewer Catalog

Path:

```text
source_library/catalog/
```

The catalog contains:

- `source_catalog.jsonl`: one reviewer-facing source record per workbook row
- `source_set_manifest.json`: versioned source-set metadata and counts
- `catalog_validation.json`: reviewer-catalog acceptance gate
- `review_sources.sqlite`: queryable index for the EA review engine
- `source_graph_nodes.jsonl`: portable graph seed nodes
- `source_graph_edges.jsonl`: portable graph seed edges

The reviewer catalog links every artifact-bearing workbook row to an artifact, including
duplicate-content rows. Scope-excluded rows remain in the catalog with `skipped_excluded` status and
no artifact link.

## Extraction, Retrieval, Review, And Graph Status

The raw source library does not store semantic chunks. A derived extraction layer is implemented
through `extract-build`; it reads the reviewer catalog, rehashes artifacts, and writes rebuildable
extracted text, chunk JSONL, and extraction diagnostics under
`source_library/derived/<source_set_id>/`.

The first retrieval layer is also implemented through `retrieval-build`. It indexes extracted
chunks into a local SQLite evidence index and supports deterministic text queries filtered by
document role, authority level, source record, review topic, citation label, and host.

The document evidence graph layer is implemented through `evidence-graph-build`. It turns extracted
chunks and retrieval metadata into graph artifacts for source documents, raw artifacts, extracted
text, sections, chunks, evidence spans, parsers, and review topics. It is a graph substrate for
auditable review; source-text legal claims are handled by the separate claim graph layer.

Source Claim Graph V0 is implemented through `claim-extract`. It extracts deterministic legal-style
claims from exact chunk text spans, links entities and authorities, validates offsets and retrieval
bindings, and writes claim graph artifacts under
`source_library/derived/<source_set_id>/claims/`.

EA Package Review V0 is implemented through `ea-review`. It extracts a local EA package, runs the
seed checklist, retrieves source-library evidence for each item, and writes package evidence,
source-library evidence, finding status, limitations, and validation artifacts.

Custer Gallatin Forest Plan Resolver V0 is implemented through `forest-plan-resolve` as the first
configured forest-plan profile. It extracts or reuses a local EA package, resolves whether the
package matches the selected profile, extracts ranger-district and project-location signals,
extracts geographic areas, management areas, and overlays from profile data, and binds resolved plan
context to profile-declared source-library records. The default Custer Gallatin profile requires the
complete plan-review bundle in the retrieval index: planning page, Land Management Plan, Record of
Decision, FEIS Volume 1, FEIS Volume 2, Biological Assessment, and Biological Opinion. Triggered
ROD, FEIS, designated-area/allocation, and ESA cues are routed to profile-declared supporting
records in addition to the primary LMP area/component evidence. Supporting routes are trigger-gated
and emit `trigger_evidence`, so broad EA section labels do not silently activate FEIS records and
uppercase acronym triggers do not match ordinary lowercase words. Generic project decision labels
such as `selected alternative`, `decision basis`, or `plan approval` do not activate the Custer
Gallatin ROD route unless the package explicitly references `Record of Decision` or `ROD`; generic
`plan consistency` labels do not activate FEIS routing unless an explicit FEIS, tiering, or
incorporation cue is present.

Forest Plan Component Evaluation V0 is implemented as a default `forest-plan-resolve` stage for
packages resolved to the selected forest-plan profile. It reads a source-set component inventory when
present, falls back to the seed inventory, validates component provenance and source-set alignment,
retrieves current plan evidence from the local retrieval index, searches package chunks for component
evidence terms, and writes
`forest_plan_component_findings.json`, `forest_plan_component_findings.md`, and
`forest_plan_reviewer_resolution_queue.json`. NFMA standard coverage V0 also writes
`forest_plan_component_inventory_coverage.json` and
`forest_plan_applicable_standard_coverage.json`; applicable standards must have plan-source evidence,
EA package evidence, and a resolved compliance status before component validation can pass. The seed
inventory
`config/forest_plan_component_inventory_seed.json` covers the first East Crazies-relevant Custer
Gallatin Crazy Mountains Backcountry Area components. Supported and partial findings require both
plan-source evidence and package evidence; gaps and stale source-set IDs become reviewer-resolution
items instead of legal conclusions.

Compliance Rule Pack + Matrix + Finding Graph V0.4 is implemented through `compliance-review`. It
identifies applicable statutory, regulatory, policy, state, executive-order, and forest-plan
authorities from `config/compliance_rule_pack_nepa_ea_v0.json`, evaluates the EA against each
applicable authority, reuses the `ea-review` package/retrieval gates, requires validated
rule-to-source-claim bindings, and writes compliance validation, a compliance review report, a
reviewer-facing compliance matrix, and a finding graph for rules, findings, source claims, source
evidence, package evidence, and package gaps.

Rule-pack `0.4.0` contains `48` rules. It declares `baseline_source_record_ids` for the 26
workbook rows where `Scope=Baseline`, and rule-pack validation enforces that each declared baseline
source record has a corresponding `applicability_mode=baseline` rule.

Applicability-First Review has a post-V1 schema contract and implemented slices for authority
universe snapshotting, package fact graph/context building, retrieval/graph tracing, deterministic
decisions, validation, and adjudication replay. `applicability-authority-universe` reads the current
catalog, base rule pack, default authority-family template config, forest-plan profiles, component
inventory, source-claim artifacts, and rule-claim links, then writes
`source_library/reviews/<review_id>/applicability/authority_universe_snapshot.json` with all
base rule-template candidates, authority-family rule-template candidates when configured, and
Forest Plan component candidates. Each candidate carries required package fact types, positive and
negative trigger groups, required source evidence, source-role filters, package-section filters,
retrieval contracts, graph-expansion contracts,
dependency/exception/supersession fields, and search coverage requirements for later
non-applicability proof. `applicability-context-build` reads the existing EA package cache and
writes `package_fact_graph.json`, `package_applicability_context.json`, and
`package_fact_graph_validation.json` with typed, span-bound package facts for project/action,
agency, NEPA level, authority signals, geography, Forest Plan areas/overlays, resource topics,
consultations, permits, public involvement, alternatives, and decision/finding signals.
Land-exchange authority signals are extracted at intake as `authority` facts before applicability
or compliance decisions are attempted: FLPMA Section 206
(`authority:flpma_section_206_land_exchange`, `R1EA-146`), land-exchange statutory authorities
(`R1EA-137`), 36 CFR part 254 regulations (`R1EA-124`), and Forest Service land-exchange
policy/project references (`R1EA-150`). It
records negative or out-of-scope location statements as negative-context facts instead of positive
geography facts, and
records weakly worded or missing common fact types as graph uncertainty rather than resolving them
as package applicability decisions. `applicability-retrieve` reads the authority universe, package
fact graph, local retrieval index, and available graph/link artifacts, then writes
`applicability_retrieval_trace.jsonl`, `applicability_graph_trace.jsonl`, and
`applicability_retrieval_graph_diagnostics.json` with replayable per-candidate query rows, fused RRF
result rows, bounded graph paths, and retrieval/graph diagnostics. Graph trace rows now explicitly
preserve authority-category hierarchy, source-claim/rule-claim-link bindings, supporting source
records, package facts, and Forest Plan component provenance when those artifacts are available.
`applicability-determine` reads those artifacts and writes `applicability_decisions.jsonl`,
`applicable_authorities.json`, `non_applicable_authorities.json`,
`search_coverage_certificates.json`, `applicability_provenance.json`, and
`applicability_report.md` with one deterministic decision row per authority candidate. Weak or
auxiliary trigger evidence no longer blocks a decision when rule-contract-sufficient strong
positive trigger evidence is independently present; all-weak positive evidence and unresolved
positive/negative conflicts still become `needs_adjudication`. Not-applicable decisions cite search
coverage certificates with required source-index hashes. Decision rows retain inspected
source-library evidence spans or declared authority-universe source evidence when source retrieval
records coverage without selecting a source chunk. Explicit negative Forest Plan scope evidence,
such as package statements that a component area is not part of the project area, overrides broad
component-text positives instead of producing contradictory ready decisions. Provenance includes
package manifest/chunk entities.
`applicability-validate` now writes `applicability_validation.json` and fails closed on missing or
duplicated candidate decisions, unresolved or `needs_adjudication` decisions, stale artifacts,
missing retrieval/graph traceability, non-applicable decisions without coverage/adjudication, and
provenance gaps. `applicability-adjudication-template`, `applicability-adjudication-eval`, and
`applicability-adjudication-apply` provide a machine-readable replay path for resolving open
decisions into `human_adjudication` bases before validation can pass. The same adjudication schema
can live in tracked repo config and be replayed with `--adjudication-file`; the live merged East
Crazies replay currently uses
`config/applicability_adjudications/v1-cg-ecid-source-delta-review.json`.
`applicability-generate-rule-pack` now writes and validates generated compliance rule packs from the
validated applicable-authority partition only, and reviewer-ready `compliance-review` is gated on
that generated pack plus current applicability validation, generated-pack validation,
non-applicable-authority, search-coverage, package, source-set, and provenance artifacts. The base
rule pack remains available only through an explicit non-reviewer-ready diagnostic path.
`applicability-eval` and `applicability-gold-eval` now score applicability decision quality before
compliance quality is promoted. Milestone 4 expands those evals across the `19` authority-family
templates added in Milestone 3. The seed eval now includes positive and negative cases for every
high-priority authority family, an unresolved weak-signal case, and the
`config/fixtures/applicability/region1-land-exchange-expanded-authority.txt` package fixture
covering land exchange, water/wetlands, cultural/tribal, wildlife/species, designated-area, and
forest-plan consistency triggers. The gold eval now requires positive, mixed, negative,
unresolved, and replay-adjudicated profiles, including a human-adjudication replay for a weak Clean
Water Act authority-family decision.

Compliance Review Eval V0 is implemented through `compliance-review-eval`. The current seed fixtures
target rule pack `0.4.0` and run deterministic package fixtures through the real compliance-review
path. The gate scores expected rule statuses, claim types, evidence presence, source-claim links,
expected source record IDs, expected source document roles, citation coverage, unsupported finding
IDs, failure taxonomy, compact reproduction paths, and finding-graph coverage.

Compliance Gold Eval V0.4 is implemented through `compliance-gold-eval`. It validates a structured
adjudication file, requires positive, mixed, and negative package profiles, runs ten adjudicated
package fixtures through the real compliance-review eval path, and emits `promotion_ready` only
when the rule pack is a reviewer-ready generated applicability rule pack and both adjudication
checks and generated findings pass.

Compliance Coverage V0 is implemented through `compliance-coverage`. It validates the coverage
matrix, rule-pack identity, eval-case coverage, current source-claim links, source-claim terms, and
source-record alignment for each compliance rule.

Current state:

- Raw source documents are captured and cataloged for the 190-row workbook contract, except the
  intentionally scope-excluded `R1EA-160` project page.
- Source metadata is normalized into JSONL and SQLite.
- Derived extraction builds text and chunks from the catalog. The newest source set now has a
  full-source-set extraction layer, reviewer-ready retrieval index, evidence graph, source-claim
  graph, rule-claim bindings, compliance coverage, compliance-review eval, compliance-gold eval, and
  phase-eval promotion evidence for `source-set-ba8d0feae79501b8`.
- The extraction accuracy audit verifies text hashes, raw artifact hashes, chunk offset fidelity,
  gap-free chunk coverage, eCFR section/subpart scoping, markup cleanup, and PDF token coverage.
- Retrieval builds and queries a provenance-bearing local evidence index.
- The document evidence graph builds source, artifact, extracted-text, section, chunk, evidence-span,
  parser, and review-topic nodes with health metrics.
- The source claim graph builds claim, entity, authority, and claim-evidence-span nodes with exact
  chunk and source-text offsets.
- The rule-claim binding layer links compliance rules to validated source claims and records explicit
  no-claim gaps when no validated source claim matches a rule.
- Phase eval reports catalog, extraction, retrieval, evidence-graph, claim-extraction,
  rule-claim-binding, optional compliance-coverage, optional compliance-gold-eval, and review-bound
  applicability plus compliance-review readiness separately when those artifacts exist or are
  requested.
- EA review runs deterministic checklist execution against a local package and emits JSON/Markdown
  reports plus `review_validation.json`.
- Custer Gallatin forest-plan context resolution runs against a local EA package and emits
  `forest_plan_context.json`, `forest_plan_context_validation.json`, and
  `forest_plan_context_summary.json`. The current Custer Gallatin path requires all seven
  Custer Gallatin plan/supporting records in retrieval, resolves management areas from the EA
  package, and adds `supporting_plan_evidence` routes for ROD, FEIS Volumes 1 and 2, Biological
  Assessment, and Biological Opinion triggers.
- Forest-plan component evaluation writes component findings, selected-inventory coverage,
  applicable-standard coverage, and a reviewer-resolution queue from a versioned inventory for
  packages resolved to the selected forest-plan profile. The current source-set inventory for the
  2022 Custer Gallatin Land Management Plan is generated from extracted chunks and has passing build
  coverage; the seed inventory remains only a fallback/test fixture.
- Compliance review runs a versioned rule pack and emits `compliance_validation.json`,
  `compliance_review.json`, `compliance_matrix.json`, `compliance_matrix.md`,
  `compliance_matrix.pdf`,
  `finding_graph_nodes.jsonl`, and `finding_graph_edges.jsonl`.
- Compliance review now invokes the forest-plan resolver against the same package cache. For Custer
  Gallatin packages, `forest_plan_component_gate_reviewer_ready` must pass, the matrix summary links
  to `forest_plan_review`, `compliance_matrix.json/md/pdf` render Forest Plan Compliance as a
  separate table from NEPA/generated-rule compliance, and the finding graph includes forest-plan
  review/component-evaluation nodes.
- EA review and compliance review can rerun checklist/rule evaluation against existing
  `package_manifest.jsonl` and `package_chunks.jsonl` with `--reuse-package-cache`; use this for
  rule-pack refreshes when the EA package was already extracted.
- Compliance review eval runs deterministic package fixtures and emits
  `compliance_review_eval_results.json` with failure taxonomy and reproduction paths.
- Compliance gold eval runs adjudicated positive/mixed/negative package fixtures and emits
  `compliance_gold_eval_results.json`; the current gate has ten adjudicated cases.
- Compliance coverage runs the coverage matrix against the current rule pack, rule-claim links,
  source-claim terms, and compliance review eval cases.
- V1 real-EA review eval is implemented through `v1-ea-eval`. It reads an existing East Crazy
  Inspiration Divide compliance review directory and scores required EA section detection,
  rule-to-section matches, source-record/document-role correctness, all 26 baseline source records,
  conditional applicability, applicable conditional source/section alignment, missing conditional
  expectations, Custer Gallatin forest-plan source/component/standard expectations, citation
  requirements, and reviewer-resolution queue size against `config/v1_ecid_real_ea_eval.json`.
- The first real East Crazy Inspiration Divide V1 compliance review run exists locally at
  `source_library/reviews/v1-cg-ecid-compliance-review/`. It extracted `43` package files into
  `1,265` chunks, produced compliance review/matrix/PDF/graph artifacts, and passed
  the upstream source-set phases. After the section-aware forest-plan retrieval pass, the package
  resolves to `scope_status: custer_gallatin`; forest-plan context validation passes with
  `2` geographic areas, `1` management area, `2` overlays, and `5` supporting plan evidence
  records. The retained context is Bridger/Bangtail/Crazy, Madison/Henrys Lake/Gallatin, Crazy
  Mountains BCA, Inventoried Roadless Area, and Recommended Wilderness Area. Forest-plan component
  artifacts are produced from the generated source-set inventory with `329` component findings,
  `58` standards, `12` applicable standards, and `12` applied standards. The stricter
  applicable-standard coverage gate now passes with `all_applicable_standards_applied=true`; the
  prior `AB-STD-RCREA-01` gap is supported by recreation/access package evidence for the proposed
  nonmotorized Sweet Trunk Trail. The non-standard reviewer-resolution queue is now closed:
  `forest_plan_component_findings.json` reports `79` supported findings, `250` not applicable
  findings, `0` gaps, and `0` reviewer-resolution items. The resolver now reads split Plan
  Consistency Table rows across adjacent package chunks, handles duplicated/split component-key
  cells and plain-text rows, and suppresses cross-reference pseudo-components that do not have a
  numeric component number.
  Component-level forest-plan eval runs against `config/forest_plan_component_eval_seed.json` and
  passes all `35` adjudicated cases. The eval now covers every one of the `12` applicable standards,
  `11` representative non-standard applicable components across desired conditions, goals,
  guidelines, objectives, and suitability, and `12` hard-negative not-applicable cases. Case coverage
  requirements pass, and component applicability precision/recall, applicable-standard recall,
  package-section match rate, plan-source citation correctness, package-evidence citation
  correctness, resolved compliance-status rate, compliance-status match rate, reviewer-resolution
  state match rate, false-applicable component rate, and reviewer-resolution closure rate all meet
  their strict thresholds. Non-standard component package evidence now uses strict section-family
  binding: outside explicit Plan Consistency Table determinations, desired conditions, goals,
  guidelines, objectives, and suitability components require a matching EA package section family
  plus substantive component terms. The component validation gate now fails supported package
  evidence with missing or mismatched section bindings unless the evidence is an explicit Plan
  Consistency Table determination. Current regenerated findings have `79` supported components,
  `0` gaps, zero supported package evidence entries with mismatched section binding, and `51`
  affirmative Plan Consistency Table component-row bindings marked explicitly. The prior completed
  non-standard component
  adjudication artifact classified the old `21` items as system misses; those adjudications are
  superseded by evidence-backed resolver fixes, and phase eval now rejects stale component
  adjudication evals whose queue count differs from the current queue. `phase-eval --review-id
  v1-cg-ecid-compliance-review` now reports `10/10` passing phases and `reviewer_ready=true`.
  The stricter V1 eval now passes all forest-plan expectations, including zero open standard
  reviewer-resolution items and a capped `0` total forest-plan reviewer-resolution items. It also
  passes the broader EA source/section gate after CE/FANEC conditional-applicability, baseline
  section-attribution, and programmatic-tiering section-routing repairs. `v1-ea-eval` now reports
  `passed=true`, `broader_ea_passed=true`, `forest_plan_passed=true`, empty failure-category
  counts, `failed_rule_ids=[]`, `conditional_false_positive=0`, `conditional_false_negative=0`,
  and `rule_section_match_rate=1.0`. The V1 eval contract now carries explicit policy coverage for
  `14` adjudication-pending conditional rules, so those rows are visible accepted V1 risk rather
  than a hidden pass condition.
- Forest-plan component adjudication tooling is implemented through
  `forest-plan-component-adjudication-template` and `forest-plan-component-adjudication-eval`. The
  template command exports one adjudication item for each open component reviewer-resolution queue
  item, with current status expectations, compact component/source trace refs, and
  reviewer-fillable dispositions, and writes a companion Markdown worklist for human triage. The
  eval command fails closed until every current queue item has explicit adjudication metadata,
  required trace refs, and a resolved disposition such as `true_ea_omission`, `retrieval_miss`,
  `package_section_chunking_miss`, `component_inventory_overreach`, `applicability_false_positive`,
  or `evidence_linking_miss`.
  Earlier runs against `v1-cg-ecid-compliance-review` produced `21` pending non-standard items:
  `8` desired conditions, `2` goals, `7` guidelines, `3` objectives, and `1` suitability
  component. Those items were adjudicated as system misses, then closed by the resolver and
  component-inventory fixes described above. The current generated queue has `0` items, so no
  component adjudication phase is required for the latest review artifacts. When an adjudication
  eval artifact is present in a review directory, `phase-eval --review-id` includes it as a
  `forest_plan_component_adjudication` phase and now checks it against the current queue count so
  pending, stale, or mismatched adjudication work blocks reviewer readiness at the phase gate.
- The V1 real-EA eval now records explicit diagnostic lanes in `v1_ea_eval_results.json`. The
  current East Crazies package passes the lane split with `broader_ea_passed=true`,
  `forest_plan_passed=true`, `forest_plan_component_adjudication_required=false`, and no broader-EA
  or forest-plan failure categories. `nepa_4336b_programmatic_tiering` remains visible as an
  adjudication-pending conditional rule, but its actual package sections are `alternatives` and
  `environmental_consequences`, its actual source record is `R1EA-005`, and its actual source
  document role is `law`.
- A seed retrieval eval file exists at `config/retrieval_eval_seed.json`.
- A seed claim extraction eval file exists at `config/claim_eval_seed.json`.
- A seed rule-claim binding eval file exists at `config/rule_claim_link_eval_seed.json`.
- A seed compliance review eval file exists at `config/compliance_review_eval_seed.json`.
- A seed compliance gold eval file exists at `config/compliance_gold_eval_v0.json`.
- A seed compliance coverage matrix exists at
  `config/compliance_rule_pack_coverage_nepa_ea_v0.json`.
- A seed forest-plan component eval file exists at
  `config/forest_plan_component_eval_seed.json`.
- A V1 real-EA review eval contract exists at `config/v1_ecid_real_ea_eval.json`.
- A post-V1 promotion-suite manifest exists at `config/promotion_suite_v1.json`.
- A seed EA review checklist exists at `config/ea_review_checklist_seed.json`.
- A seed NEPA EA compliance rule pack exists at `config/compliance_rule_pack_nepa_ea_v0.json`.
- Catalog graph seed files exist for source-level relationships.
- No embeddings exist yet.
- No model-generated compliance narrative is trusted without deterministic package and source
  evidence.
- Page/section offsets are available only where the selected parser can infer them; all chunks carry
  extracted-text character offsets.

The catalog graph seed is a source metadata graph. It includes relationships such as:

- source to artifact
- source to authority
- source to review topic
- source to applicability

The document evidence graph is the implemented content graph. It includes document sections, chunks,
evidence spans, parser provenance, and review-topic edges. It does not include table structure
recovery, embeddings, or vector chunks.

The source claim graph is the implemented claim/entity graph. It includes extracted source-text
claims, entities, authority nodes, claim evidence spans, and edges back to chunk/source provenance.
It is deterministic pattern extraction with strict validation, not a model-generated interpretation
of compliance meaning.

The rule-claim binding layer is the implemented bridge from compliance rules to source claims. It
uses rule-pack queries and source filters to rank validated source claims, writes exact provenance
for each link, and treats missing rule support as explicit no-claim gaps rather than silent evidence.

The finding graph is the implemented compliance-review graph. It includes rule packs, compliance
rules, findings, source-claim references, evidence-span references, and package-gap nodes. It does
not replace human reviewer adjudication.

## Accuracy Guarantees

The current downloader and catalog guarantee capture integrity, not legal interpretation.

Validated downloader/catalog guarantees for the current 190-row corpus:

- Every generated-corpus source row has one final captured status.
- The combined batch ledger covers all `190` generated-corpus workbook rows.
- The repair queue is empty after URL repairs.
- Every artifact-bearing successful row links to an artifact.
- The one scope-excluded row, `R1EA-160`, has no artifact or fetch evidence.
- Every artifact path exists.
- Artifact byte sizes match manifest metadata.
- Artifact SHA256 values recompute from saved bytes.
- Duplicate-content rows link to canonical artifacts.
- URL overrides preserve the workbook `original_url` and record the `effective_url`.
- Override metadata includes `override_url` and `override_reason`.
- The reviewer catalog matches batch manifests.
- SQLite source-artifact links match the JSONL catalog.
- The prior 38-source land-exchange delta extraction for `source-set-572d6384a59a7b2a` matched raw
  artifact hashes and manifest text hashes, but it is superseded by the current reuse-first
  extraction assembly for `source-set-ba8d0feae79501b8`.
- Chunk text matches extracted-text offset slices.
- Retrieval chunks validate against source-set IDs, content hashes, offsets, required provenance, and
  catalog linkage.
- Evidence graph chunks validate against the retrieval index before graph artifacts are marked
  reviewer-ready.
- EA review `pass` findings require both package evidence and source-library evidence.
- EA review `gap` findings require source-library evidence and explicitly mean package evidence was
  not found.
- Package evidence search requires configured package-term hits; single-word terms match whole
  tokens and phrase terms match contiguous text.
- EA review validation rejects unsupported compliance claims.
- Compliance review validates the rule pack, requires every authority rule to carry authority and
  applicability metadata, requires all declared baseline source records to be covered, requires
  every rule to be evaluated, requires all declared baseline source records to appear in findings,
  requires source citations for claim-bearing findings, and validates finding graph node/edge
  integrity.
- Rule-pack validation rejects unsafe rule-pack or rule IDs, unsupported source-filter keys, and
  empty source-filter values.
- Compliance review eval rejects unsafe case IDs, ambiguous package fixtures, unsupported filters,
  unsupported expected statuses, unsupported expected claim types, non-boolean evidence
  expectations, partial rule-pack coverage, unknown rule IDs, and status counts that do not match
  per-rule expectations.
- Compliance coverage rejects malformed matrix rows, missing matrix/eval/link coverage, and
  source-record or source-claim-term mismatches against current rule-claim links.
- Compliance gold eval rejects missing adjudication metadata, missing required profiles, duplicate
  case IDs, unsafe or escaping package fixture paths, partial rule-pack expectations, status count
  mismatches, and generated finding mismatches. Missing package fixture files are recorded as failed
  gold eval results instead of escaping without a machine-readable artifact.
- Phase eval rejects stale compliance coverage artifacts when the coverage source set or rule pack
  does not match the evaluated source set and rule-claim binding.
- Phase eval rejects stale compliance review artifacts when the review source set does not match the
  evaluated source set.

Full extraction, retrieval, evidence-graph, source-claim, rule-claim, coverage, compliance-review
eval, compliance-gold eval, and phase-eval guarantees now exist for the current 190-row source set
`source-set-ba8d0feae79501b8`.

Boundaries:

- A successful download means the source bytes were captured and validated.
- It does not prove that the source is legally current beyond the workbook metadata and retrieval evidence.
- It proves the current generated extraction artifacts pass deterministic extraction validation and
  extraction accuracy audit checks for text hashes, raw artifact hashes, chunk offsets, chunk
  coverage, scoped XML, markup cleanup, and sampled PDF token coverage.
- It proves the current retrieval, evidence graph, source-claim graph, rule-claim binding,
  compliance coverage, compliance review eval, compliance gold eval, and phase eval artifacts passed
  deterministic provenance, coverage, freshness, and binding gates.
- It proves the current EA review V0 cannot mark a finding as `pass` without both package and
  source-library evidence.
- It proves the current compliance review V0 cannot produce claim-bearing findings without
  source-library citations.
- It proves a Custer Gallatin-scoped compliance review cannot be reviewer-ready when forest-plan
  component evaluation is absent, stale, or not reviewer-ready.
- It proves component-level forest-plan accuracy can be scored against adjudicated cases for
  applicability, standard recall, package-section binding, plan-source citations, package-evidence
  citations, resolved compliance status, and reviewer-resolution closure before running additional
  real EA packages. The component eval checks review/source-set identity across every consumed
  review artifact, enforces all-applicable-standard and minimum representative-case coverage, and
  treats extra citations as citation mismatches, not harmless surplus evidence.
- It proves the profile-driven forest-plan resolver can resolve the real East Crazy Inspiration
  Divide package to Custer Gallatin scope without treating incidental references to other forests as
  ambiguity, while still failing closed when component coverage is not reviewer-ready.
- It proves forest-plan component reviewer-resolution items can be exported into a stable
  adjudication contract and evaluated for queue coverage, completion, disposition counts, and status
  expectation drift before those reviewer decisions are used as improvement data.
- It proves the current final compliance-review eval seed passes deterministic all-pass, mixed
  pass/gap, and all-gap package fixtures.
- It proves the current seed compliance-gold-eval promotion gate passes one positive, one mixed, and
  one negative adjudicated fixture profile.
- It defines a V1 real-EA eval contract for the East Crazy Inspiration Divide run, but that contract
  does not prove real-world EA review quality until `v1-ea-eval` passes against the actual review
  artifacts and the remaining component/conditional/section failures are adjudicated.
- It does not prove semantic legal interpretation of the extracted text.
- It does not prove that future web versions will remain unchanged.

## Reviewer Engine Read Path

The EA review engine should not scan `artifacts/raw/` directly as its source of truth. It should
read through the catalog, extraction outputs, and retrieval index in order.

Recommended read path:

1. Read `source_library/catalog/source_set_manifest.json`.
2. Confirm the intended `source_set_id`, `download_batch_run_id`, source counts, artifact counts, and validation status.
3. Query `source_library/catalog/review_sources.sqlite` or read `source_library/catalog/source_catalog.jsonl`.
4. Select source rows by `document_role`, `authority_level`, `review_topics`, `applies_to`, `host`, or `expected_parser`.
5. For each source row, open `artifact_path`.
6. Recompute SHA256 and byte size before parsing.
7. Parse by `expected_parser` and `content_type`.
8. Emit downstream chunks with immutable provenance fields.
9. Build `source_library/derived/<source_set_id>/retrieval/evidence_index.sqlite`.
10. Retrieve evidence spans through `retrieval-query` or the retrieval module before generating any
    compliance answer.
11. For package review, run `ea-review` so each checklist item records both package evidence and
    source-library evidence, or marks the item as a gap/uncertain without unsupported claims.

Every downstream text chunk should carry:

- `source_set_id`
- `source_record_id`
- `artifact_sha256`
- `artifact_path`
- `citation_label`
- `original_url`
- `effective_url`
- `final_url`
- parser name and parser version
- extraction timestamp
- page, section, heading, byte, or character offsets when available

The review engine should cite `citation_label` and offset metadata, not raw filenames.

## EA Package Review V0

The current package-review milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources ea-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

The command writes `source_library/reviews/<review_id>/review_report.json` and
`review_report.md`, `review_validation.json`, plus package extraction artifacts under
`source_library/reviews/<review_id>/package/`.
Findings use the statuses `pass`, `gap`, `uncertain`, and `not_applicable`.

A `gap` means the source library returned supporting review authority but matching package evidence
was not found. An `uncertain` finding does not make a compliance claim.
The command fails fast if the source-library retrieval index is not reviewer-ready, and rerunning a
fixed review ID replaces prior package artifacts before writing the new report.
When a package was already extracted for the same review ID, pass `--reuse-package-cache` to preserve
and reuse `package/package_manifest.jsonl` and `package/package_chunks.jsonl` instead of
re-extracting package PDFs.

`review_validation.json` is the gate-facing artifact. It checks source retrieval readiness, package
extraction, package chunk creation, valid finding statuses, dual evidence for `pass` findings, source
evidence for `gap` findings, and absence of unsupported compliance claims.

## Custer Gallatin Forest Plan Resolver V0

The first forest-plan-specific review milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources forest-plan-resolve \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library
```

The command writes `source_library/reviews/<review_id>/forest_plan_context.json`,
`forest_plan_context_validation.json`, and `forest_plan_context_summary.json`, plus package
extraction artifacts under `source_library/reviews/<review_id>/package/`.

The default resolver profile is Custer Gallatin and preserves the V0 output contract. It returns
`scope_status=custer_gallatin`, `not_custer_gallatin`, or `ambiguous`; ambiguous `Gallatin`-only
packages are not guessed. The command now accepts `--forest-unit-id` and
`--forest-plan-profiles-path` so profile data, not Python constants, defines forest names, required
source records, area terms, overlays, and supporting evidence routes. The config now has explicit
profiles for all `10` tracked Region 1 units, but only the long-lived Custer Gallatin profile
currently has authored district, geographic-area, management-area, overlay, and supporting-route
vocabularies. Other configured forest profiles now carry their source-record contracts in tracked
config, but they are still blocking evidence when mentioned as operative project scope until those
richer vocabularies are authored. Incidental background, reference, bibliography, or coordination
mentions do not force an otherwise Custer-Gallatin package to `ambiguous`. Location evidence now
carries `evidence_role` metadata and the context includes `background_location_mentions` so
reviewers can see which references were excluded from project-location resolution. Negative
package-location text such as `not part of the project area` is also filtered before area
resolution. For Custer Gallatin packages it extracts:

- forest unit and ranger district signals
- project location snippets
- Custer Gallatin geographic areas
- Custer Gallatin management areas
- overlays such as inventoried roadless areas
- package evidence and source-library LMP evidence
- triggered supporting plan evidence from the Custer Gallatin ROD, FEIS Volumes 1 and 2,
  Biological Assessment, and Biological Opinion
- trigger evidence showing why each supporting plan record was applied
- required source-record readiness for all Custer Gallatin profile-required plan/supporting records
- unresolved mentions that need human reviewer resolution

The East Crazies profile-driven fixture proves the minimum V1 forest-plan support slice: Custer
Gallatin scope, Bridger/Bangtail/Crazy Mountains Geographic Area, Crazy Mountains Backcountry Area,
all seven required Custer Gallatin source records, FEIS/BA/BO supporting routes from explicit
package evidence, and no Custer Gallatin ROD routing from generic project decision labels.

Custer Gallatin packages are reviewer-ready only when validation passes and at least one geographic
area, management area, or overlay is resolved. They also require every Custer Gallatin
profile-required plan/supporting record to be indexed. Packages that appear Custer Gallatin scoped
but lack a resolved plan area, or trigger a supporting record without source evidence, set
`needs_reviewer_resolution` instead of silently passing.

Forest-plan improvement work uses sequence discipline: each implemented sequence updates repo docs,
passes focused verification, and is committed before the next sequence starts.

## Compliance Rule Pack And Finding Graph V0

The rule-pack milestone is implemented through:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review \
  --package-path /absolute/path/to/ea-package-or-folder \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
```

For rule-pack-only refreshes against an existing package extraction, keep the same review ID and add
`--reuse-package-cache`.

The command writes these artifacts beside the base EA review artifacts:

- `source_library/reviews/<review_id>/compliance_validation.json`
- `source_library/reviews/<review_id>/compliance_review.json`
- `source_library/reviews/<review_id>/compliance_matrix.json`
- `source_library/reviews/<review_id>/compliance_matrix.md`
- `source_library/reviews/<review_id>/compliance_matrix.pdf`
- `source_library/reviews/<review_id>/finding_graph_nodes.jsonl`
- `source_library/reviews/<review_id>/finding_graph_edges.jsonl`

The post-V1 applicability-first artifact contract reserves
`source_library/reviews/<review_id>/applicability/` for:

- `authority_universe_snapshot.json`
- `package_fact_graph.json`
- `package_applicability_context.json`
- `package_fact_graph_validation.json`
- `applicability_retrieval_trace.jsonl`
- `applicability_graph_trace.jsonl`
- `applicability_retrieval_graph_diagnostics.json`
- `applicability_decisions.jsonl`
- `applicable_authorities.json`
- `non_applicable_authorities.json`
- `search_coverage_certificates.json`
- `applicability_validation.json`
- `applicability_provenance.json`
- `applicability_report.md`
- `generated_rule_pack.json`
- `generated_rule_pack_validation.json`

Those artifacts are the target source of truth for applicability and non-applicability. The
non-applicable authority list must not be buried only as compliance matrix rows. A not-applicable
decision must carry negative evidence, trigger-miss rationale, search coverage, or adjudication, and
a reviewer-ready compliance review consumes a generated rule pack tied to a passing applicability
validation hash plus the package fact graph, retrieval trace, graph trace, search coverage, and
provenance hashes.

The rule pack is data, not hidden code. Each rule includes identity, title, question, requirement,
severity, authority category, authority source record, applicability mode, package query and terms,
optional conditional applicability terms, optional grouped conditional applicability terms, source
query, source filters, and an evidence expectation.
The authority document role is derived from explicit rule metadata when present, otherwise from
`source_filters.document_role`.
Rule-pack `0.4.0` also declares `baseline_source_record_ids`; these are the 26
`Ingest_Checklist` rows where `Scope=Baseline`.

The finding graph contains:

- `ComplianceRulePack`
- `ComplianceReview`
- `ComplianceRule`
- `ComplianceFinding`
- `SourceLibraryEvidence`
- `PackageEvidence`
- `PackageEvidenceGap`

The compliance matrix is the first reviewer-facing matrix artifact. Its `NEPA / Authority
Compliance` table records one NEPA/generated-rule compliance row per finding: authority,
applicability mode and status, rule status, requirement, applicability basis, package evidence
citation, source evidence citation, source-claim IDs, applied source record IDs, applied source
document roles, citation-gate status, limitations, and failure category when an applicable finding is
not a supported pass. For Custer Gallatin Forest Plan reviews, the matrix also includes a separate
`Forest Plan Compliance` table from component findings and applicable-standard coverage. The
Markdown/PDF rendering now opens with a Responsible Official Readout and Accuracy Audit in plain
decision language so the signing review can distinguish pass/fail authority rows, inapplicable
authority traceability, applicable Forest Plan standards, and non-standard plan-consistency support.

`compliance_validation.json` checks rule-pack validity, base EA review validation, all-rules
coverage, valid finding statuses, dual evidence for `pass`, source evidence for `gap`, source
citations for claim-bearing findings, unsupported-claim absence, finding graph evidence-edge
coverage, and finding graph integrity.

Rule-pack IDs, rule IDs, and fixed review IDs are constrained to letters, numbers, dots,
underscores, and hyphens so review outputs cannot escape the intended review directory. Rule
`source_filters` must use supported retrieval filter keys; typoed keys fail validation instead of
silently widening retrieval.

## Derived Extraction Layer

The extraction layer builds a derived text/chunk index without modifying raw artifacts.
PDF extraction uses Docling first; born-digital PDFs that exceed the Docling timeout can fall back
to `pypdf_text_fallback`, with parser name/version preserved in manifests and chunks and fallback
metadata preserved in the extraction manifest.

Derived layout:

```text
source_library/
  derived/
    <source_set_id>/
      extracted_text/
      docling_json/
      chunks/
        chunks.jsonl
      diagnostics/
        extraction_manifest.jsonl
        extraction_validation.json
        extraction_accuracy_audit.json
        summary.json
```

Derived outputs:

- extracted text per artifact
- Docling JSON when Docling is used by the parser
- HTML/XML section extraction
- chunk JSONL with stable chunk IDs
- chunk-level SHA256 or content hash
- parser diagnostics
- extraction validation report
- chunk-to-source and chunk-to-artifact links

Derived data should always be rebuildable from raw artifacts and the reviewer catalog.

## Evidence Retrieval Layer

Retrieval layout:

```text
source_library/
  derived/
    <source_set_id>/
      retrieval/
        evidence_index.sqlite
        retrieval_manifest.json
        retrieval_validation.json
        summary.json
        retrieval_eval_results.json
```

The retrieval layer is intentionally lexical and auditable for v1. It stores the source chunk text
and the provenance required for a reviewer to verify the citation back to raw artifacts and extracted
text offsets.

Retrieval validation checks:

- extraction validation passed unless explicitly overridden
- extraction scope is complete unless `--allow-partial-extraction` is passed for diagnostics
- chunks JSONL exists and contains chunks
- catalog SQLite exists
- chunk source-set IDs match the target source set
- chunk IDs are unique
- indexed source IDs match extracted source IDs in `extraction_manifest.jsonl`
- chunk hashes match the stored text
- chunk offsets are valid
- linked artifact and extracted-text paths still exist
- required citation, artifact, URL, parser, and offset fields are present

`retrieval-build` records `reviewer_ready`. This is true only when the index validates and the
extraction summary shows complete catalog coverage for all required non-excluded sources.
Scope-excluded rows count toward selected catalog coverage but do not require chunks. A filtered
one-document slice can still be indexed with `--allow-partial-extraction`, but it remains a
diagnostic index, not a reviewer-ready corpus.

## Document Evidence Graph Layer

Evidence graph layout:

```text
source_library/
  derived/
    <source_set_id>/
      evidence_graph/
        document_graph_nodes.jsonl
        document_graph_edges.jsonl
        evidence_graph.sqlite
        evidence_graph_validation.json
        summary.json
        phase_eval_results.json
```

The evidence graph contains these node types:

- `SourceSet`
- `SourceDocument`
- `RawArtifact`
- `ExtractedText`
- `DocumentSection`
- `DocumentChunk`
- `EvidenceSpan`
- `Parser`
- `ReviewTopic`

Every `EvidenceSpan` traces to a chunk, source document, raw artifact, parser version, content
hash, citation label, URL provenance, and extracted-text offsets. The graph build also reopens the
retrieval SQLite index and requires chunk IDs, source-set IDs, provenance fields, offsets, content
hashes, text, and review topics to match before graph artifacts are persisted. The graph records
health metrics: connected components, isolated nodes, dangling edges, evidence coverage, topic
coverage, source-artifact coverage, retrieval binding mismatches, and chunk hash mismatches.

`phase-eval` keeps readiness checks phase-aligned:

- catalog capture
- extraction
- retrieval
- evidence graph
- claim extraction
- rule-claim binding
- authority universe when `--review-id` or `--review-dir` is supplied
- package fact graph when `--review-id` or `--review-dir` is supplied
- applicability retrieval trace when `--review-id` or `--review-dir` is supplied
- applicability graph trace when `--review-id` or `--review-dir` is supplied
- applicability determination when `--review-id` or `--review-dir` is supplied
- applicability validation when `--review-id` or `--review-dir` is supplied
- generated rule pack when `--review-id` or `--review-dir` is supplied
- optional compliance coverage when `compliance_coverage_results.json` exists beside the
  rule-claim outputs
- optional compliance gold eval when `compliance_gold_eval_results.json` exists under
  `source_library/reviews/compliance_gold_eval/`
- optional compliance review when `--review-id` or `--review-dir` is passed
- optional forest-plan component eval when the review directory contains
  `forest_plan_component_eval_results.json`
- optional forest-plan component adjudication when the review directory contains
  `forest_plan_component_adjudication_eval.json` or a completed
  `forest_plan_component_adjudication.json`

When a compliance coverage phase is included, `phase-eval` requires the matrix gate to pass, the
rule pack to match, and the coverage source set to match the evaluated source set. When a gold eval
phase is included, `phase-eval` requires the gold eval to pass, the rule pack to match, and the
gold eval source set to match the evaluated source set; stale or failed gold artifacts report
specific failed checks such as source-set or rule-pack mismatch. For review-bound generated rule
packs, a passing base-pack gold eval can satisfy the phase when the generated pack declares the same
base identity; the phase records this as `rule_pack_match_mode=generated_base`. When review-bound applicability
phases are included, `phase-eval` requires a current authority universe, package fact graph and
validation, retrieval and graph trace diagnostics, complete candidate decisions, complete
applicable/non-applicable partitions, search coverage certificates for non-applicable authorities,
a passing `applicability_validation.json`, and a generated rule pack whose rules exactly match the
applicable-authority partition. It also rechecks file-backed applicability-validation hashes for
decision, partition, retrieval/graph trace, search-coverage, and provenance artifacts. When a
compliance review phase is included, `phase-eval` requires
the review report to exist, validation to pass, the review ID to match when supplied, and the review
source set to match the evaluated source set. It also requires the compliance matrix artifact to
exist and match the review's schema version, review ID, source set, rule pack, row count, and status
counts. For reviewer-ready Custer Gallatin Forest Plan reviews, it also requires the separate Forest
Plan Compliance matrix section to exist and expose applicable standard rows. When a forest-plan
component eval phase is included,
`phase-eval` requires the component eval result schema version to match, pass, match the evaluated
source set, and match the supplied review ID when one is provided. The phase reports case counts,
component metrics, failed checks, and failure-category counts. When a forest-plan component
adjudication phase is included,
`phase-eval` requires the adjudication eval to exist, pass, match the evaluated source set, and match
the supplied review ID when one is provided. The phase reports queue count, resolved and pending
adjudication counts, real EA omission and system-miss counts/rates, completion rate, expectation
match rate, disposition counts, adjudication-outcome counts, and failure-category counts.

## Alignment And Next Milestone

The current implementation remains aligned with the v1 reviewer-engine goal: accurate, auditable,
verifiable compliance review against a local knowledge base. Domain knowledge lives in versioned
data artifacts such as workbook rows, review topics, eval fixtures, rule packs, and the coverage
matrix. Runtime code performs general capture, extraction, retrieval, graph construction, rule
binding, coverage validation, and phase evaluation.

Authority-universe Milestone 4 is aligned with that design because applicability quality is scored
before compliance quality: the seed eval covers positive and negative outcomes for all `19`
high-priority authority-family templates, includes an unresolved weak-signal validation-failure
case, and the gold eval replays an adjudicated Clean Water Act decision through the same
applicability adjudication artifacts used by review runs. The next authority-universe milestone is
Milestone 5: compliance review and report integration for authority-family provenance,
non-applicable authority appendices, reviewer-resolution reporting, and evidence-backed
litigation-risk summaries.

The Authority-First Compliance Matrix V0.4 milestone is implemented for the current local source-set
promotion gate. The active rule pack contains 48 authority rows and explicitly requires all 26
workbook `Scope=Baseline` source records in every EA review, with additional conditional rules for
triggered authorities. The refreshed coverage and gold gates contain ten adjudicated realistic
package profiles, expected source rows, expected source document classes, per-case failure taxonomy,
compact reproduction paths, and generated compliance matrices for the `0.4.0`/48-rule pack.

The current system has a complete 190-row downloader/catalog corpus that includes the four missed
Custer Gallatin FEIS and ESA-supporting plan documents. Full-source-set reuse-first extraction has
now been assembled for `source-set-ba8d0feae79501b8`: the current manifest has `189` extracted rows,
`1` scope-excluded row, `0` failures, and `18,822` chunks. The assembly reused `181` validated prior
extractions and `7` already-current Custer Gallatin slice records, then parsed
`R1PLAN-dakota-prairie-grasslands-02` as the only fresh extraction. Retrieval, evidence graph,
source claims, rule-claim bindings, compliance coverage, compliance-review eval, compliance-gold
eval, and phase eval have also been rebuilt and are reviewer-ready for the full current source set.
The Custer Gallatin LMP component inventory has also been generated for the current source set with
`329` components and `58` standards, and its build coverage passes with no missing or duplicate
component/standard IDs. Build coverage also records `2` suppressed component-like labels with
nonnumeric number tokens as inventory-quality issues instead of allowing rough IDs such as
`FW-GDL-VEGNF-See` into the inventory.
The prior 147-row downstream corpus remains useful for historical comparison only and should not be
treated as current promotion evidence for the expanded workbook.

The V1 CE/FANEC conditional-applicability milestone is implemented: grouped positive trigger
semantics and token-boundary matching for short acronyms now keep
`nepa_4336c_ce_adoption_screen`, `usda_nepa_ce_fanec_7cfr_1b3`, and
`usda_nepa_subcomponent_ce_7cfr_1b4` not applicable for the East Crazies package unless package
evidence shows an adopted CE, CE/FANEC screen, categorical-exclusion path, USDA CE screening, or
extraordinary-circumstances review. The milestone also carries explicit
`does_not_apply_if_package_terms` guards so negated same-chunk phrases such as a categorical
exclusion path not being used remain non-applicable evidence instead of positive CE triggers. The
live V1 eval now reports `conditional_false_positive=0` and `conditional_false_negative=0`.

The V1 baseline section-attribution milestone is implemented for `nepa_statute_chapter_55`: package
evidence routing now selects the EA purpose-and-need environmental-assessment span, and the live V1
eval reports `rule_source_section_expectations_met=true`, `rule_section_match_rate=1.0`,
`baseline_source_record_match_rate=1.0`, `baseline_document_role_match_rate=1.0`, and
`citation_requirement_match_rate=1.0`.

The V1 programmatic-tiering section-routing milestone is implemented: `nepa_4336b_programmatic_tiering`
now declares package section term groups for alternatives and environmental consequences, and
package evidence ranking uses those rule-declared groups as a context preference after the normal
tiering evidence match succeeds. The rule-pack validator and schema docs now cover these optional
section-preference fields so malformed `package_section_terms` or `package_section_term_groups`
fail validation instead of silently changing review behavior. The live V1 eval reports actual
package sections `alternatives` and `environmental_consequences`, actual source record `R1EA-005`,
actual document role `law`, `adjudication_pending=true`, and no `rule_section_mismatch`.

The V1 conditional-adjudication milestone is implemented. Each of the `18`
`conditional_source_expectations` in `config/v1_ecid_real_ea_eval.json` now has a
classification rationale, and the contract declares
`conditional_adjudication_policy.mode=accepted_pending_v1` with `accepted_pending_count=14`.
`v1-ea-eval` now emits a `conditional_adjudication` summary and full pending-results queue, fails
if accepted pending rule IDs/counts drift from the actual `adjudicate` rows, and keeps
source/section alignment enforced for actual applicable pending rows. The gap-close pass hardens
that policy contract so malformed accepted pending count/rule-ID fields fail with explicit contract
validation errors.

The V1 EA gate repair plan is complete through Milestone 6. The promoted review is
`v1-cg-ecid-compliance-review` for the East Crazy Inspiration Divide package on source set
`source-set-ba8d0feae79501b8`. The V1 eval contract still references base rule pack `nepa-ea-v0`
version `0.4.0`, while the reviewer-ready compliance review consumes the generated applicability
rule pack `generated-nepa-ea-v0-v1-cg-ecid-compliance-review` version `applicability-v0`. The gate
passes with `passed=true`, `broader_ea_passed=true`, `forest_plan_passed=true`,
`failure_category_counts={}`, `failed_rule_ids=[]`, `rule_section_match_rate=1.0`,
`conditional_false_positive=0`, `conditional_false_negative=0`, and `14` accepted-pending
conditional adjudication rows carried as explicit V1 reviewer risk. Review-bound `phase-eval` now
passes `21/21` phases with `review_packet_index` and `reviewer_ready=true`; the compliance gold
phase is satisfied by the passing base-pack gold suite through
`rule_pack_match_mode=generated_base`. Embeddings, reranking, model-assisted synthesis, and broader
Region 1 package expansion remain post-V1 work and should start under a new milestone plan.

## Verification Commands

Run all tests:

```bash
PYTHONPATH=src python -m pytest -q
```

Run captured-library integrity tests only:

```bash
PYTHONPATH=src python -m pytest tests/test_captured_library.py -q
```

Rebuild the full reviewer catalog from the current full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx \
  --output-dir source_library \
  --batch-run-id corpus-update-2026-05-01-cg-support-batches
```

Build derived extraction outputs from the current reviewer catalog:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library
```

Inventory extraction reuse opportunities before a reuse-first rebuild:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources reuse-inventory \
  --output-dir source_library
```

Assemble the current source set with reuse first, then parse only records without a valid current
or prior extraction candidate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources extract-build \
  --output-dir source_library \
  --reuse-existing \
  --reuse-inventory-path source_library/derived/source-set-ba8d0feae79501b8/reuse_inventory/reuse_inventory.json
```

For a delta-only extraction, repeat `--id` for each selected source record. The 2026-04-30
land-exchange update used this mode for the 38 new artifact-bearing rows and left `R1EA-160`
unextracted because it is scope-excluded.

Build the evidence retrieval index:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-build \
  --output-dir source_library
```

Run a retrieval query:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-query \
  --output-dir source_library \
  --review-topic alternatives \
  "alternatives environmental effects"
```

Run the seed retrieval eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources retrieval-eval \
  --output-dir source_library \
  --eval-file config/retrieval_eval_seed.json
```

Build the evidence graph:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources evidence-graph-build \
  --output-dir source_library
```

Build source claims and run the seed claim eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources claim-extract \
  --output-dir source_library
PYTHONPATH=src python -m usfs_r1_ea_sources claim-eval \
  --output-dir source_library \
  --eval-file config/claim_eval_seed.json
```

Build rule-claim bindings and run the seed rule-claim eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-link \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json
PYTHONPATH=src python -m usfs_r1_ea_sources rule-claim-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/rule_claim_link_eval_seed.json
```

Run the rule-pack coverage gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-coverage \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --coverage-matrix config/compliance_rule_pack_coverage_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

Run the seed compliance review eval:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-review-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/compliance_review_eval_seed.json
```

Run applicability decision-quality evals:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources applicability-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --eval-file config/applicability_eval_seed.json

PYTHONPATH=src python -m usfs_r1_ea_sources applicability-gold-eval \
  --output-dir source_library \
  --base-rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/applicability_gold_eval_v1.json
```

Run the adjudicated gold eval promotion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources compliance-gold-eval \
  --output-dir source_library \
  --rule-pack config/compliance_rule_pack_nepa_ea_v0.json \
  --gold-file config/compliance_gold_eval_v1.json
```

Run the aggregate gold coverage gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources gold-coverage-eval \
  --output-dir source_library \
  --manifest config/gold_coverage_v1.json
```

Run phase-aligned readiness evaluation:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources phase-eval \
  --output-dir source_library
```

Run the manifest-driven post-V1 promotion suite:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json
```
