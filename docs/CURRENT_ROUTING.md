# Current Routing
Date: 2026-05-28
Use this file as the short current route before opening the append-only docs.
## New Session Start
- Read this file first, then the top of `docs/SESSION_HANDOFF.md`, then `docs/CURRENT_SYSTEM_STATE.md`.
- Latest resolved packet:
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- Continuing forest-specific example lane:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- Active forest-specific example packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- Active West Reservoir child blocker:
  `docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
- Historical lineage only:
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_SET_CONTRACT_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_REPLACEMENT_FEASIBILITY_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/ECID_PRELIMINARY_HISTORICAL_LANE_RESOLUTION_MILESTONE_PLAN.md`,
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`
## Active Route
- West Reservoir reviewer-readiness planning is now the active
  forest-specific example packet. Use
  `docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`
  for the next implementation slice, with
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md` as the parent
  context. The parent plan starts after package-authority provenance was
  verified against the official Flathead project page and public Pinyon/Box
  folder, and it keeps West Reservoir typed blocked until current review
  artifacts, component eval, compliance, V1 eval, and phase eval pass on
  `source-set-f70ea11e04ae3d53`.
- Milestone 0 in the West Reservoir packet is resolved locally. Package
  authority remains green, current V1 eval remains a truthful typed-blocked
  baseline with only allowed blocker categories, and the pre-migration
  component eval baseline remains red with `0/27` cases passing on
  `source-set-4fb59e9eb43045cb`; it is not current f70 readiness proof.
  Milestone 1 has started: `ea-review` and `applicability-context-build`
  rebuilt successfully on the verified package cache and current source set.
  The Flathead authority-universe/base-rule-pack/source-record identity repair
  is now reduced locally: `applicability-authority-universe` reads
  `forest_unit_id="flathead-nf"` from the tracked replay context, scopes out
  the Custer Gallatin base forest-plan rule, selects `80` Flathead component
  candidates, and uses `FINAL-FLAT-001` as the forest-plan source. The command
  still fails closed on `source-set-4fb59e9eb43045cb` because authority source
  evidence is missing for non-forest families and baseline rules
  (`candidates_have_source_evidence_available.failure_count=9`,
  `authority_family_template_candidates_cover_config.missing_source_record_count=10`).
  The source-evidence blocker is now reduced through
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`.
  Fresh 4fb feasibility confirmed the failing snapshot needs `59` unique
  source-record IDs; `49` legacy IDs have governed current mappings, `0` of
  those mapped current IDs are present in the active 4fb catalog, and all `49`
  are present only in the later f70 current-source-gap closeout catalog. The
  migration packet Milestone 1 is now reduced locally: replay context, V1 eval
  contract, component eval contract, component coverage, and the replay
  catalog surface all now point to `source-set-f70ea11e04ae3d53`, while
  `tests/test_west_reservoir_source_set_migration.py` fails on a controlled
  mixed-source-set case and preserves typed-blocked status. Migration packet
  Milestone 2 is now resolved locally: the f70 component inventory batch now
  includes Custer Gallatin, Flathead, and Lolo and passes with
  `component_count=410`, `standard_count=79`, and
  `blocked_forest_unit_ids=[]`; the selected f70 authority-universe rerun
  reports `passed=true`, `validation_passed=true`,
  `candidate_authority_count=146`, and
  `forest_plan_component_candidate_count=80`. Parent Milestone 1 then reran
  the f70 artifact freshness and applicability spine: `ea-review`,
  `applicability-context-build`, `applicability-authority-universe`,
  `applicability-retrieve`, `applicability-determine`,
  `applicability-adjudication-eval`, `applicability-adjudication-apply`,
  `applicability-validate`, and `applicability-generate-rule-pack` are green
  on f70. Applicability validation reports `44` applicable authorities, `102`
  non-applicable authorities, `0` unresolved authorities, and
  `generated_rule_pack_ready=true`; the generated rule pack contains `44`
  rules. The next implementation slice is
  `docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`:
  `forest-plan-resolve` stops before current Flathead context generation
  because `config/r1_forest_plan_identity_reconciliation_v1.json` is still
  anchored to `source-set-4fb59e9eb43045cb` and leaves nine required Flathead
  legacy source-record IDs unresolved. Do not proceed to component readiness,
  compliance, V1 promotion, phase eval, or registry promotion until the
  identity blocker lets `forest-plan-resolve` emit current f70 Flathead
  context and component artifacts.
- Local commit anchors for the active West Reservoir packet: Milestone 0
  baseline guard `d5d97ad`, Flathead authority-universe scoping `267ba9d`,
  source-evidence blocker route `0773ef7`, and docs-only Bitter Lesson
  alignment `3a5e6b3`; source-set migration Milestone 1 closeout is
  `f17474b` (`Migrate West Reservoir source-set contract`).
- Do not reuse the historical green West Reservoir
  `phase_eval_results.json` on `source-set-5e65d845ce77e1a0` as current
  readiness proof. It is historical evidence only; the active packet requires
  a current rerun on `source-set-f70ea11e04ae3d53`.
- South Otter Milestone 3 is resolved locally, and the current registry policy
  now promotes South Otter as the primary Custer Gallatin example. South Otter
  is a governed Custer Gallatin example in
  `config/forest_specific_example_package_registry_v1.json`, a required slot in
  `config/v1_real_package_review_coverage_v1.json`, and a required passing slot
  in `config/forest_plan_component_eval_coverage_v1.json`. It remains parallel
  to `Document_Register_Master`; no source-register queue row was rerouted.
  The primary-selection closeout commit is `c56039b` (`Promote South Otter as
  Custer Gallatin primary`); the underlying Milestone 3 promotion closeout
  commit is `21eb2fa` (`Promote South Otter supplemental example`).
- The full official Pinyon/Box root for the South Otter Landscape Restoration and
  Resilience Project (`58396`) remains ignored local authority evidence at
  `source_library/reviews/_intake/region1-example-custer-gallatin-south-otter-58396/`
  with `58` folders, `639` files, `2,926,223,134` bytes, and `0` download
  failures. The tracked replay context stays at
  `config/replay_contexts/region1-example-custer-gallatin-south-otter-58396.json`
  on `source-set-f70ea11e04ae3d53` and uses the narrowed official
  `Final EA and Decision Notice Documents` package path.
- Latest South Otter reviewer-stack truth: applicability validation passes
  with `61` applicable authorities, `335` non-applicable authorities, `0`
  unresolved authorities, and `reviewer_ready=true`; tracked applicability
  adjudication resolves `8/8` items. Compliance review is
  `reviewer_ready=true` and `validation_passed=true` with `61` findings
  (`pass=42`, `uncertain=17`, `gap=2`). `v1-ea-eval` passes with
  `contract_status="reviewer_ready"`, `broader_ea_passed=true`, and
  `forest_plan_passed=true`. Forest-plan component eval passes `56/56` cases,
  and component adjudication resolves all `169` current queue items
  (`132` applicability false positives, `37` evidence-linking misses, `0`
  real-EA omissions). Review `phase-eval` passes `28/28` with `blockers=[]`,
  `review_direct_eval_status="direct_eval_present"`, and required review-scope
  summaries for `v1_ea_eval`, `real_package_review_coverage`, and
  `forest_plan_component_eval_coverage`.
- South Otter registry identity is
  `example_id="cgnf-south-otter-forest-specific"`,
  `coverage_slot_id="cgnf-south-otter-forest-specific"`,
  `forest_unit_id="custer-gallatin-nf"`, and
  `applicable_forest_unit_ids=["custer-gallatin-nf"]`. The Custer Gallatin row
  now sets South Otter as `primary_example_id` and lists East Crazy as the
  only supplemental example. South Plateau
  (`cgnf-south-plateau-expansion`) is archived as historical evidence only due
  to litigation and Forest Plan compliance challenge risk, and must not be used
  as a Custer Gallatin or Region 1 example.
- `config/v1_real_package_review_coverage_v1.json` now has four load-bearing
  active slots, including South Otter and Lolo as two required
  `forest_specific_reviewer_ready` slots. The governed aggregate rerun reports
  `passed=true`, `covered_slot_count=4`, `required_slot_count=4`,
  `reviewer_ready_slot_count=3`, `typed_blocked_slot_count=1`,
  `distinct_forest_count=3`, `distinct_package_style_count=5`, and no missing
  required slots or coverage classes.
- `config/forest_specific_example_package_registry_v1.json` now has four
  active governed examples: East Crazy and South Otter for Custer Gallatin,
  West Reservoir for Flathead, and Tyler's Kitchen for Lolo. South Plateau is
  retained only under `archived_review_examples` with
  `usage_policy="historical_evidence_only_not_example"`. The
  governed forest-specific aggregate rerun reports `passed=true`,
  `review_example_count=4`, `reviewer_ready_example_count=3`,
  `distinct_governed_example_forest_count=3`,
  `profile_guidance_only_count=7`, and no threshold failures.
- West Reservoir's Flathead package authority is now verified against the
  official Flathead project page
  `https://www.fs.usda.gov/r01/flathead/projects/67436` and linked Pinyon/Box
  folder `https://usfs-public.app.box.com/v/PinyonPublic/folder/299363475796`.
  The tracked verification manifest
  `config/review_package_authority_verifications/west-reservoir-67436.json`
  records `12` official PDFs, `12` local package-manifest rows, byte-size and
  SHA-256 matches for every document, and `omitted_document_count=0`. This
  repairs package-authority provenance only; West Reservoir remains typed
  blocked until its component-review artifacts and eval pass.
- `config/forest_plan_component_eval_coverage_v1.json` now requires South
  Otter as a fifth component-eval review slot. The South Otter slot is covered,
  source-set aligned, and passing. The aggregate
  `forest-plan-component-eval-coverage` command still fails on non-South Otter
  slots: ECID source-delta has `result_not_passed` plus
  `result_source_set_id_mismatch`, and West Reservoir has `result_not_passed`.
  Current aggregate counts are `covered_review_count=3/5`,
  `stale_identity_count=1`, and `unresolved_review_count=2`; do not describe
  aggregate component coverage as green.
- The Lolo Tyler's Kitchen example-package Milestone 3 implementation is
  resolved locally. The tracked Lolo review
  `region1-example-lolo-tylers-kitchen-66344` is now the governed primary
  `lolo-nf` forest-specific example package, while the package remains
  parallel to `Document_Register_Master`.
- `config/forest_specific_example_package_registry_v1.json` continues to route
  `lolo-nf` as `real_package_examples_available`, sets
  `primary_example_id="lolo-tylers-kitchen-forest-specific"`, and keeps
  `queue_boundary_source_ids=["FOR-029"]`.
- `config/source_register_queue_resolution_ledger_v1.json` now resolves
  `FOR-029` with
  `planned_disposition="forest_specific_example_package"` and
  `resolution_status="resolved"`. The queue audit now reads
  `resolution_status_counts={"blocked":9,"planned":33,"resolved":9}` and
  `blocked_current_or_project_applicable_count=9`.
- The Lolo replay chain remains green on `source-set-f70ea11e04ae3d53`:
  `v1-ea-eval` reports `contract_status="reviewer_ready"`,
  `broader_ea_passed=true`, and `forest_plan_passed=true`; review
  `phase-eval` passes `28/28` with `blockers=[]` and
  `review_direct_eval_status="direct_eval_present"`.
- The source-register currentness, current-workbook source-set rebaseline,
  source-record identity, aligned-runtime, and broader Lolo example-package
  Milestone 3 blocker family is now historical for Lolo. Do not route new work
  back there unless a future command regresses one of the verified gates.
- Forest-plan component eval coverage is not a blocker for the Lolo or South
  Otter review-scope closeouts: both slots are aligned and pass on `f70...`.
  The aggregate `forest-plan-component-eval-coverage` command still fails on
  non-Lolo/non-South Otter source-delta and West Reservoir slots, so do not
  describe aggregate component coverage as green.
- Aggregate truth:
  ECID current promotion, Lolo forest-specific example promotion, and South
  Otter primary-example selection remain green in the non-strict promotion
  suite. South Plateau is not an active promotion-suite expansion slot.
  Strict expansion remains blocked only on the ECID historical slot under
  `historical_source_set_split`.
- Do not flip the ECID historical slot to `ready`, reopen the older Lolo or
  replay-repair packets as live runtime work, or treat the remaining
  non-Lolo/non-South Otter component-coverage aggregate red as part of the
  Lolo or South Otter example promotions.
## Deep Reads
- Core:
  `docs/WEST_RESERVOIR_F70_FOREST_PLAN_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`,
  `docs/WEST_RESERVOIR_SOURCE_SET_MIGRATION_MILESTONE_PLAN.md`,
  `docs/WEST_RESERVOIR_4FB_SOURCE_EVIDENCE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`,
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- Architecture and document routing:
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`, `docs/AGENT_START_HERE.md`
