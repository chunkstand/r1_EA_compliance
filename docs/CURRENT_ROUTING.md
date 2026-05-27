# Current Routing
Date: 2026-05-27
Use this file as the short current route before opening the append-only docs.
## New Session Start
- Read this file first, then the top of `docs/SESSION_HANDOFF.md`, then `docs/CURRENT_SYSTEM_STATE.md`.
- Latest resolved packet:
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
- Continuing forest-specific example lane:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- Active forest-specific example packet:
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
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
- The next forest-specific example packet is now opened locally for the
  South Otter Landscape Restoration and Resilience Project (`58396`) on the
  Custer Gallatin National Forest. Use
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` for the active packet.
  The frozen review ID is
  `region1-example-custer-gallatin-south-otter-58396`, the official project
  page is `https://www.fs.usda.gov/r01/custergallatin/projects/58396`, and the
  linked Pinyon/Box folder is
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158227182465`. The
  review ID is intentionally forest-qualified because each forest-specific
  example is relevant to its applicable forest. If promoted later, South Otter
  must use `example_id="cgnf-south-otter-forest-specific"` and remain
  supplemental to `custer-gallatin-nf`, not generic Region 1 guidance.
- South Otter is only an opened packet at this checkpoint. It is not in the
  active workbook, not in the forest-specific registry, not a real-package
  coverage slot, and not a reviewer-ready claim. Do not update registry or
  coverage thresholds until package intake, replay context, `v1-ea-eval`,
  forest-plan component eval, and review `phase-eval` pass for the frozen
  South Otter review ID.
- The Lolo Tyler's Kitchen example-package Milestone 3 implementation is
  resolved locally. The tracked Lolo review
  `region1-example-lolo-tylers-kitchen-66344` is now the governed primary
  `lolo-nf` forest-specific example package, while the package remains
  parallel to `Document_Register_Master`.
- `config/v1_real_package_review_coverage_v1.json` now has four load-bearing
  slots and includes the Lolo `forest_specific_reviewer_ready` slot. The
  governed aggregate rerun reports `passed=true`, `covered_slot_count=4`,
  `reviewer_ready_slot_count=3`, `typed_blocked_slot_count=1`,
  `distinct_forest_count=3`, `distinct_package_style_count=4`, and no missing
  required slots or coverage classes.
- `config/forest_specific_example_package_registry_v1.json` now routes
  `lolo-nf` as `real_package_examples_available`, sets
  `primary_example_id="lolo-tylers-kitchen-forest-specific"`, and keeps
  `queue_boundary_source_ids=["FOR-029"]`. The governed forest-specific
  aggregate rerun reports `review_example_count=4`,
  `reviewer_ready_example_count=3`,
  `distinct_governed_example_forest_count=3`,
  `profile_guidance_only_count=7`, and no threshold failures.
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
- Forest-plan component eval coverage is not a blocker for this Lolo replay
  closeout: the Lolo slot is now aligned and passes on `f70...`. The aggregate
  `forest-plan-component-eval-coverage` command still fails on non-Lolo
  source-delta and West Reservoir slots (`covered_review_count=2/4`,
  `stale_identity_count=1`, `unresolved_review_count=2`), so do not describe
  aggregate component coverage as green.
- Aggregate truth:
  ECID current promotion, South Plateau reviewer-ready expansion, and Lolo
  forest-specific example promotion remain green in the non-strict promotion
  suite. Strict expansion remains blocked only on the ECID historical slot
  under `historical_source_set_split`.
- Do not flip the ECID historical slot to `ready`, reopen the older Lolo or
  replay-repair packets as live runtime work, or treat the remaining
  non-Lolo component-coverage aggregate red as part of the Lolo example
  promotion.
## Deep Reads
- Core:
  `docs/SOUTH_OTTER_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_RECORD_IDENTITY_RECONCILIATION_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_CURRENT_WORKBOOK_SOURCE_SET_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_SOURCE_REGISTER_CURRENTNESS_BLOCKER_MILESTONE_PLAN.md`,
  `docs/LOLO_TYLERS_KITCHEN_ALIGNED_RUNTIME_REBASELINE_BLOCKER_MILESTONE_PLAN.md`,
  `docs/CURRENT_SYSTEM_STATE.md`, `docs/SESSION_HANDOFF.md`
- Architecture and document routing:
  `docs/ARCHITECTURE_GOVERNANCE_REBASELINE_MILESTONE_PLAN.md`, `docs/AGENT_START_HERE.md`
