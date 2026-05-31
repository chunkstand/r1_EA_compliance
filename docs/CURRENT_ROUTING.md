# Current Routing
Date: 2026-05-31
Use this file as the short current route before opening the append-only docs.
## New Session Start
- Read this file first, then the top of `docs/SESSION_HANDOFF.md`, then `docs/CURRENT_SYSTEM_STATE.md`.
- Latest resolved packet:
  `docs/FIRST_CLASS_EVAL_TRACE_IMPLEMENTATION_MILESTONE_PLAN.md` Milestone 5
- Active packet:
  no active first-class eval trace implementation slice; future model-judge or
  hosted scoring work requires a new approved milestone
- Latest resolved West Reservoir packet:
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md` Milestone 4
- Continuing forest-specific example lane:
  `docs/FOREST_SPECIFIC_EXAMPLE_PACKAGE_BOUNDARY_MILESTONE_PLAN.md`
- Latest resolved forest-specific example packet:
  `docs/DAKOTA_PRAIRIE_MEDORA_VEGETATION_MANAGEMENT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  Milestone 4
- Predecessor resolved forest-specific example packet:
  `docs/NEZ_PERCE_CLEARWATER_DEAD_LAUNDRY_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  Milestone 4
- Predecessor resolved forest-specific example packet:
  `docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  Milestone 4
- Earlier resolved forest-specific example packet:
  `docs/BEAVERHEAD_DEERLODGE_SOUTH_TOBACCO_ROOTS_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`
  Milestone 4
- Earlier resolved forest-specific example packet:
  `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` Milestone 4
  registry and coverage promotion resolved locally
- Latest resolved HLC forest-specific example packet:
  `docs/HLC_BONANZA_EXAMPLE_PACKAGE_MILESTONE_PLAN.md` Milestone 4
- Latest resolved West Reservoir parent slice:
  Milestone 4 signer-facing packet and phase-eval closeout in
  `docs/WEST_RESERVOIR_REVIEWER_READINESS_MILESTONE_PLAN.md`
- Latest resolved West Reservoir child blocker:
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
- Critical forest-specific example constraint: these packages are fail-closed
  unless runtime forest-plan resolution identifies the same forest as
  applicable. `v1-ea-eval` emits `summary.runtime_forest_scope`, and
  `real-package-review-coverage-eval` / `forest-specific-example-package-eval`
  block non-matching forest reuse even when a review contract is otherwise
  green.
- ECID source-delta residual status as of 2026-05-31: ECID remains important as
  a historical Custer Gallatin source-delta replay and component-eval coverage
  slot, but it is not the active forest-specific example route. The replay
  context now points at archived merged source set
  `source-set-8a4005c8a083af1a` and its merged catalog. The old `4fb` versus
  `8a40` identity split is resolved for `phase-eval`; base rule-claim direct
  eval now passes `24/24`, compliance-review direct eval passes `5/5` on
  `8a40`, and `phase-eval --review-id v1-cg-ecid-source-delta-review` passes
  `22/22` with `reviewer_ready=true` and `blockers=[]`. It remains
  `contract_backed_promotion_ready=false` only because this historical
  source-delta lane has no declared review contract. Do not reopen ECID current
  promotion or route this replay into the governed forest-specific example
  packets.
- Dakota Prairie Grasslands Medora Vegetation Management is resolved locally
  through Milestone 4 and is now the governed primary example for
  `dakota-prairie-grasslands`. The packet is
  `docs/DAKOTA_PRAIRIE_MEDORA_VEGETATION_MANAGEMENT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`;
  the working review identity is
  `review_id="region1-example-dakota-prairie-medora-vegetation-management-66886"`
  for `forest_unit_id="dakota-prairie-grasslands"` on
  `source-set-f70ea11e04ae3d53`. Reduced packet closeout commit: `7ac8e08`;
  Milestone 4 promotion closeout commit: `bef9258` (`Promote Dakota Prairie
  Medora example`). The governed example ID is
  `example_id="dpg-medora-vegetation-management-forest-specific"`.
  The selected authorities are the official project page
  `https://www.fs.usda.gov/r01/dpg/projects/66886` and supplied Pinyon/Box root
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/284408882208`.
  Live readback on 2026-05-31 identifies project `66886` as `Completed`, with
  expected analysis type `Environmental Assessment`, lead management unit
  `Medora Ranger District`, decision signed date `12/04/2025`, and project
  name `Medora Vegetation Management Project`. Local ignored package authority
  under
  `source_library/reviews/_intake/region1-example-dakota-prairie-medora-vegetation-management-66886/`
  records `7` downloaded files, `40,860,421` bytes, and `failure_count=0`.
  The tracked replay context is
  `config/replay_contexts/region1-example-dakota-prairie-medora-vegetation-management-66886.json`.
  Base `ea-review` passes with `7/7` extracted files, `417` package chunks,
  `package_failed_count=0`, and `reviewer_ready=true`. A review-local Dakota
  component inventory builds on f70 with `394` components and `161` standards;
  component inventory coverage and source accuracy pass. The refreshed Dakota
  profile lets `forest-plan-resolve` resolve
  `scope_status="dakota_prairie_grasslands"` with
  `project_location_signal_count=1`, `geographic_area_count=2`,
  `management_area_count=9`, `overlay_count=0`, and no blocking missing Dakota
  source records. Component findings now report `394` applicable components:
  `10` supported and `384` gaps. Tracked component adjudication resolves the
  current `384/384` queue as `evidence_linking_miss` system misses with `0`
  pending and `0` real EA omissions. Tracked applicability adjudication
  resolves the single species-supporting conflict as `human_applicable`;
  applicability validation reports `460` candidate authorities, `47`
  applicable, `413` not applicable, `0` unresolved, and a generated `47`-rule
  pack. Compliance review is reviewer-ready with `47` findings (`28` pass,
  `18` uncertain, `1` gap). The tracked Dakota V1 eval contract
  `config/v1_dakota_prairie_medora_real_ea_eval.json` passes with
  `contract_status="reviewer_ready"`, and the tracked component eval contract
  `config/forest_plan_component_evals/region1-example-dakota-prairie-medora-vegetation-management-66886.json`
  passes `394/394` cases with `161` applicable standards. Aggregate promotion
  gates are green locally: `real-package-review-coverage-eval` passes with
  `covered_slot_count=10`, `reviewer_ready_slot_count=10`,
  `distinct_forest_count=9`, and `distinct_package_style_count=16`;
  `forest-specific-example-package-eval` passes with `review_example_count=10`,
  `reviewer_ready_example_count=10`,
  `distinct_governed_example_forest_count=9`, and
  `profile_guidance_only_count=1`; `forest-plan-component-eval-coverage`
  passes with `covered_review_count=11/11`, `stale_identity_count=0`, and
  `unresolved_review_count=0`. Review `phase-eval` passes `28/28` phases with
  `reviewer_ready=true`, `declared_review_contract=true`, and
  `contract_backed_promotion_ready=true`. `config/forest_specific_example_package_registry_v1.json`
  now routes `dakota-prairie-grasslands` as
  `real_package_examples_available` with
  `primary_example_id="dpg-medora-vegetation-management-forest-specific"`.
  Kootenai National Forest is now the only remaining
  `profile_eval_guidance_only` forest without a governed real package example.
- Nez Perce-Clearwater Dead Laundry is the predecessor resolved
  forest-specific example packet. It is resolved locally through Milestone 4 and
  is now the governed primary example for `nez-perce-clearwater-nfs`.
  The packet is
  `docs/NEZ_PERCE_CLEARWATER_DEAD_LAUNDRY_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`;
  the resolved review identity is
  `review_id="region1-example-nez-perce-clearwater-dead-laundry-57827"` for
  `forest_unit_id="nez-perce-clearwater-nfs"` and
  `example_id="npc-dead-laundry-forest-specific"`. The selected authorities
  are the official project page
  `https://www.fs.usda.gov/r01/nezperce-clearwater/projects/57827` and
  Pinyon/Box root
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158227433225`.
  Live readback on 2026-05-30 identifies project `57827` as `Completed`, with
  expected analysis type `Environmental Assessment`, lead management unit
  `North Fork Ranger District`, decision signed date `2024-12-23`, and Box
  root label `Dead Laundry (57827)`. The Box root currently exposes
  `Analysis` (`455` visible files; `1,802,724,968` bytes),
  `Decision` (`2,186` visible files; `6,997,388,791` bytes), and
  `Scoping` (`13` visible files; `76,930,655` bytes), totaling `2,654`
  visible files and `8,877,044,414` top-level bytes. The governed replay
  boundary is durable under
  `source_library/reviews/_intake/region1-example-nez-perce-clearwater-dead-laundry-57827/`:
  `box_inventory.json` records `82` files across `13` folders with
  `234,693,626` expected bytes, and `box_import_manifest.json` records `82`
  downloaded files with `failure_count=0`, while excluding
  `Analysis/EA references` and `Decision/2023 Objection Materials Submitted`.
  Base `ea-review` passes on `source-set-f70ea11e04ae3d53` with `82/82`
  extracted files, `2,991` package chunks, `package_failed_count=0`, and
  `reviewer_ready=true`. `forest-plan-resolve` reports
  `scope_status="nez_perce_clearwater_nfs"`, `validation_passed=true`,
  `overlay_count=2`, `unresolved_mention_count=0`, and
  `needs_reviewer_resolution=false`. Applicability validation passes with `53`
  applicable authorities, `147` not-applicable authorities, `0` unresolved
  authorities, and `53` generated rules. Component adjudication resolves
  `121/121` current queue items, compliance review is reviewer-ready, V1 eval
  contract
  `config/v1_nez_perce_clearwater_dead_laundry_real_ea_eval.json` passes,
  component eval contract
  `config/forest_plan_component_evals/region1-example-nez-perce-clearwater-dead-laundry-57827.json`
  passes `134/134` cases, and review `phase-eval` passes `28/28` phases with
  `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`. `config/forest_specific_example_package_registry_v1.json`
  now routes `nez-perce-clearwater-nfs` as
  `real_package_examples_available` with
  `primary_example_id="npc-dead-laundry-forest-specific"`, and `FOR-034` is
  resolved as a `forest_specific_example_package` queue boundary. Aggregate
  promotion gates are green locally: `real-package-review-coverage-eval`
  passes with `covered_slot_count=10`, `reviewer_ready_slot_count=10`,
  `distinct_forest_count=9`, and `distinct_package_style_count=16`;
  `forest-specific-example-package-eval` passes with `review_example_count=10`,
  `reviewer_ready_example_count=10`,
  `distinct_governed_example_forest_count=9`, and
  `profile_guidance_only_count=1`. The Dead Laundry component-coverage slot is
  covered, source-set aligned, and passing, and the standalone
  `forest-plan-component-eval-coverage` aggregate is now green locally with
  `covered_review_count=11/11`, `stale_identity_count=0`, and
  `unresolved_review_count=0` after refreshing the inherited
  `v1-cg-ecid-source-delta-review` replay contracts to archived merged source
  set `source-set-8a4005c8a083af1a` and rerunning its `36/36`-case component
  eval. There is no active unresolved NPC child packet; continue the umbrella
  lane if selecting the next forest-specific slice. If the inherited ECID
  replay is pursued further, the next truthful route is no longer component
  coverage, source-set contract reconciliation, rule-claim direct-eval quality,
  or stale compliance-review direct eval; those are resolved locally. The lane
  is reviewer-ready historical replay evidence, not a current promotion route.
- Idaho Panhandle Lacy Lemoosh is the predecessor resolved forest-specific example
  packet.
  The packet is
  `docs/IDAHO_PANHANDLE_LACY_LEMOOSH_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`; the
  resolved review identity is
  `review_id="region1-example-idaho-panhandle-lacy-lemoosh-60853"` for
  `forest_unit_id="idaho-panhandle-nfs"` and
  `example_id="ipnf-lacy-lemoosh-forest-specific"`. The official project page
  is `https://www.fs.usda.gov/r01/idahopanhandle/projects/60853`; the selected
  Pinyon/Box root is
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158229569265`.
  Live readback on 2026-05-29 identifies project `60853` as `Completed`, with
  expected analysis type `Environmental Assessment`, lead management unit
  `St. Maries Ranger District`, decision signed date `2025-05-22`, and Box
  root label `Lacy Lemoosh (60853)`. The Box root currently exposes
  `Decision`, `Final EA`, `Draft EA`, and `Scoping` folders with `186` listed
  files and `555,066,969` bytes at the top level. Local ignored package
  authority now exists under
  `source_library/reviews/_intake/region1-example-idaho-panhandle-lacy-lemoosh-60853/`:
  `box_inventory.json` records `29` folder-page records, `186` files, and
  `553,664,116` expected file bytes; `box_import_manifest.json` records `186`
  downloaded files, `553,664,116` actual bytes, and `failure_count=0`. The
  tracked replay context is
  `config/replay_contexts/region1-example-idaho-panhandle-lacy-lemoosh-60853.json`.
  `ea-review` on `source-set-f70ea11e04ae3d53` passes with `186/186`
  extracted files, `7,404` package chunks, `package_failed_count=0`,
  `reviewer_ready=true`, and `validation_passed=true`. Milestone 2 reconciled
  the Idaho profile to active catalog IDs proven by
  `config/r1_forest_plan_identity_reconciliation_v1.json`, added the
  package-backed `St. Joe Ranger District` scope term, built a review-local
  component inventory with `52` components and `8` standards, and reran
  `forest-plan-resolve` in local commit `a1574b3`. Treat `St. Maries Ranger
  District` as the project-page/Box authority label and `St. Joe Ranger
  District` as package-local resolver scope evidence. Commit `ba3718b` closed
  the FEIS source-readiness slice: the local f70
  catalog/retrieval surface now overlays `R1PLAN-idaho-panhandle-nfs-04` and
  `R1PLAN-idaho-panhandle-nfs-05` from the archived source-delta gate; f70
  extraction/retrieval pass with `719` sources, `707` artifacts, `11`
  supplemental overlay rows, and `113,830` chunks. Direct retrieval readback
  indexes `R1PLAN-idaho-panhandle-nfs-04=1,606` chunks and
  `R1PLAN-idaho-panhandle-nfs-05=991` chunks. The resolver now reports
  `scope_status="idaho_panhandle_nfs"`, `unresolved_mention_count=0`,
  `project_location_signal_count=1`, `geographic_area_count=1`,
  `management_area_count=1`, `overlay_count=2`, retrieval readiness passed
  with `blocking_missing_source_record_ids=[]`, and overall
  `validation_passed=true`. The current component adjudication is refreshed
  against the `36`-item queue: `forest-plan-component-adjudication-eval` passes
  with `36/36` resolved system-miss items, `0` pending items, disposition
  counts `25` `evidence_linking_miss`, `10`
  `applicability_false_positive`, and `1`
  `component_inventory_overreach`, and no expectation mismatches.
  `forest-plan-resolve` now reports `reviewer_ready=true` and
  `validation_passed=true`; component evaluation still records `16` supported
  findings, `36` gaps, `8` applicable standards, `3` applied standards, and
  `5` insufficient-evidence standards, all closed as component-adjudication
  system misses for this preflight slice. Milestone 3 reviewer-stack replay
  closed in commit `3cea9fe` and now passes: applicability adjudication
  resolves `9/9` conflicts, applicability validation reports `56` applicable
  authorities, `62` non-applicable authorities, `0` unresolved authorities, and
  generated rule-pack readiness;
  compliance review passes with `56` findings and reviewer-ready matrix/PDF
  artifacts; V1 eval passes with `30/30` conditional expectations and reviewer
  status `reviewer_ready`; component eval passes `52/52` cases; review
  `phase-eval` passes with `28/28` phases reviewer-ready. Milestone 4 registry
  and aggregate coverage promotion now passes locally: `idaho-panhandle-nfs`
  routes as `real_package_examples_available` with
  `primary_example_id="ipnf-lacy-lemoosh-forest-specific"`;
  `real-package-review-coverage-eval` passes with `covered_slot_count=10`,
  `reviewer_ready_slot_count=10`, `distinct_forest_count=9`, and
  `distinct_package_style_count=16`; `forest-specific-example-package-eval`
  passes with `covered_forest_count=10`, `review_example_count=10`,
  `reviewer_ready_example_count=10`,
  `distinct_governed_example_forest_count=9`, and
  `profile_guidance_only_count=1`. The Idaho component-coverage slot is
  covered, source-set aligned, and passing; later ECID repairs also made the
  standalone `forest-plan-component-eval-coverage` aggregate green locally with
  `covered_review_count=11/11`, `stale_identity_count=0`, and
  `unresolved_review_count=0`. Review `phase-eval` now reports
  `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`. No active forest-specific example
  packet remains after this closeout. Keep Lacy Lemoosh parallel to
  `Document_Register_Master`;
  do not route unrelated Idaho Panhandle queue rows such as `FOR-020` or
  `FOR-022` into this packet.
- Beaverhead-Deerlodge South Tobacco Roots example-package work is resolved
  locally through Milestone 4 registry and coverage promotion. The packet is
  `docs/BEAVERHEAD_DEERLODGE_SOUTH_TOBACCO_ROOTS_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`;
  the resolved review identity is
  `review_id="region1-example-beaverhead-deerlodge-south-tobacco-roots-63754"`
  for `forest_unit_id="beaverhead-deerlodge-nf"` and planned
  `example_id="bdnf-south-tobacco-roots-forest-specific"`. The official
  project page is
  `https://www.fs.usda.gov/r01/beaverhead-deerlodge/projects/63754`; the
  selected Pinyon/Box root is
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/199281418011`.
  Local ignored package authority under
  `source_library/reviews/_intake/region1-example-beaverhead-deerlodge-south-tobacco-roots-63754/`
  records `16` downloaded files, `176,594,060` bytes, and `failure_count=0`.
  `ea-review` on the package passes with `16/16` extracted files, `1,382`
  package chunks, `package_failed_count=0`, and `validation_passed=true`.
  A review-local Beaverhead-Deerlodge component inventory builds with `90`
  components and `89` standards, and `forest-plan-resolve` now reports
  `scope_status="beaverhead_deerlodge_nf"`, `validation_passed=true`,
  `geographic_area_count=2`, `management_area_count=3`, `overlay_count=2`,
  `project_location_signal_count=3`, and `unresolved_mention_count=0`.
  Component adjudication now resolves all `60/60` current reviewer-resolution
  items with `0` pending items and `disposition_counts={"evidence_linking_miss":60}`.
  Applicability adjudication resolves the `3` positive/negative trigger
  conflicts as `human_applicable`; applicability validation passes with `52`
  applicable authorities, `104` not-applicable authorities, and `0` unresolved
  authorities; generated rule-pack validation passes with `52` rules.
  `compliance-review` passes with `52` findings, V1 eval passes with `26`
  conditional expectations and `contract_status="reviewer_ready"`, component
  eval passes `90/90` cases covering all `89` applicable standards, and review
  `phase-eval` passes `28/28` with `blockers=[]`.
  `beaverhead-deerlodge-nf` now routes as `real_package_examples_available`
  with `primary_example_id="bdnf-south-tobacco-roots-forest-specific"`.
  `real-package-review-coverage-eval` passes with `covered_slot_count=10`,
  `reviewer_ready_slot_count=10`, `distinct_forest_count=9`, and
  `distinct_package_style_count=16`.
  `forest-specific-example-package-eval` passes with `covered_forest_count=10`,
  `review_example_count=10`, `reviewer_ready_example_count=10`,
  `distinct_governed_example_forest_count=9`, and
  `profile_guidance_only_count=1`. The Beaverhead component-coverage slot
  passes on `source-set-f70ea11e04ae3d53`; later packets resolved the inherited
  ECID component-coverage aggregate and the remaining `8a40`
  rule-claim/compliance direct-eval residuals. Review `phase-eval` now
  reports `declared_review_contract=true` and
  `contract_backed_promotion_ready=true`. Keep South Tobacco Roots parallel to
  `Document_Register_Master`; do not route the inherited ECID source-delta
  blocker back into this Beaverhead packet.
- Bitterroot Front is now the governed primary Bitterroot National Forest
  example package. The packet is
  `docs/BITTERROOT_FRONT_EXAMPLE_PACKAGE_MILESTONE_PLAN.md`; the resolved
  review identity is `review_id="region1-example-bitterroot-front-57341"` for
  `forest_unit_id="bitterroot-nf"` and
  `example_id="bitterroot-front-forest-specific"`. The official project page is
  `https://www.fs.usda.gov/r01/bitterroot/projects/57341`; the selected
  Pinyon/Box root is
  `https://usfs-public.app.box.com/v/PinyonPublic/folder/158226983588`.
  Local ignored package authority under
  `source_library/reviews/_intake/region1-example-bitterroot-front-57341/`
  records `132` downloaded files, `632,912,037` bytes, and `failure_count=0`.
  `ea-review`, applicability validation, generated rule-pack validation,
  `compliance-review`, `v1-ea-eval`, forest-plan component eval,
  component-adjudication eval, and review `phase-eval` are green on
  `source-set-f70ea11e04ae3d53`; review `phase-eval` now passes `28/28` with
  `blockers=[]`.
  `config/v1_real_package_review_coverage_v1.json` now includes required
  `slot_id="bitterroot-front-forest-specific"` coverage and
  `real-package-review-coverage-eval` passes with `covered_slot_count=6`,
  `reviewer_ready_slot_count=6`, `distinct_forest_count=5`, and
  `distinct_package_style_count=7`.
  `config/forest_specific_example_package_registry_v1.json` routes
  `bitterroot-nf` as `real_package_examples_available` with
  `primary_example_id="bitterroot-front-forest-specific"`, and
  `forest-specific-example-package-eval` passes with `review_example_count=6`,
  `reviewer_ready_example_count=6`,
  `distinct_governed_example_forest_count=5`, and
  `profile_guidance_only_count=5`.
  `config/forest_plan_component_eval_coverage_v1.json` includes the required
  Bitterroot component slot, which is covered, source-set aligned, and passing.
  Later packets reduced the inherited ECID component-coverage aggregate; do not
  route the remaining ECID rule-claim/compliance direct-eval residual back into
  Bitterroot Front. `FOR-007` is now resolved as
  `planned_disposition="forest_specific_example_package"` and remains parallel
  to `Document_Register_Master`.
- HLC Bonanza example packet is resolved locally through registry and coverage
  promotion. The selected package is Bonanza project `66532` for
  `helena-lewis-and-clark-nf`, using the official project page
  `https://www.fs.usda.gov/r01/helena-lewisclark/projects/66532` and Pinyon/Box
  folder `https://usfs-public.app.box.com/v/PinyonPublic/folder/272939272513`.
  Local ignored package authority exists under
  `source_library/reviews/_intake/region1-example-helena-lewis-and-clark-bonanza-66532/`
  with `5` folders, `47` files, `65,761,583` bytes, and `0` download failures.
  `ea-review` on the full package passes with `47/47` files extracted,
  `2,227` package chunks, `package_failed_count=0`, and
  `validation_passed=true`. HLC single-forest component inventory builds with
  `258` components and `28` standards. HLC profile context terms now include
  `White Sulphur Springs Ranger District` and `Castles Geographic Area`.
  Component adjudication is tracked at
  `config/forest_plan_component_adjudications/region1-example-helena-lewis-and-clark-bonanza-66532.json`
  and passes with `178/178` resolved items, `0` pending items,
  `132` applicability false positives, and `46` evidence-linking misses.
  `forest-plan-resolve` now reports `scope_status="helena_lewis_and_clark_nf"`,
  `geographic_area_count=1`, `validation_passed=true`, and
  `reviewer_ready=true`. Milestone 3 reviewer-stack replay is green:
  applicability replay applies `5` tracked adjudications and validates `51`
  applicable authorities, the generated Bonanza rule pack has `51` rules,
  `compliance-review` passes with `51` findings and matrix JSON/Markdown/PDF
  artifacts present, V1 eval passes with `25` conditional expectations,
  component eval passes `28/28` HLC standards, and review `phase-eval` now
  passes `28/28` with `blockers=[]`, `declared_review_contract=true`, and
  `contract_backed_promotion_ready=true`. Bonanza is now
  `example_id="hlc-bonanza-forest-specific"` and the HLC primary example in
  `config/forest_specific_example_package_registry_v1.json`.
  `docs/AGENT_START_HERE.md` also names the HLC Bonanza packet as the latest
  resolved forest-specific example packet and tells HLC workflows to inspect
  Bonanza first.
  After Bitterroot Front promotion, `real-package-review-coverage-eval` passes
  with `covered_slot_count=6`, `reviewer_ready_slot_count=6`,
  `distinct_forest_count=5`, and `distinct_package_style_count=7`.
  `forest-specific-example-package-eval` passes with
  `review_example_count=6`, `reviewer_ready_example_count=6`,
  `distinct_governed_example_forest_count=5`, and
  `profile_guidance_only_count=5`. The Bonanza component-coverage slot is
  required, source-set aligned, and passing. Later packets reduced the
  inherited ECID component-coverage aggregate; do not route the remaining ECID
  rule-claim/compliance direct-eval residual back into the HLC packet.
- First-class eval trace Milestones 0-5 are resolved locally. The tracked contract
  lives in `config/eval_trace_inventory_contract_v1.json`; the contract doc is
  `docs/FIRST_CLASS_EVAL_TRACE_CONTRACT.md`; and
  `src/usfs_r1_ea_sources/eval_trace_contract.py` validates the canonical
  object model, enum values, artifact-family linkability, required link
  checks, scorer metadata, export preconditions, and no-global-ratchet policy.
  The read-only `eval-trace-inventory` CLI now lives in
  `src/usfs_r1_ea_sources/eval_trace_inventory.py` and inventories source-set
  and review scopes without mutating existing artifacts. The West Reservoir f70
  seed run passed with `18` required artifact rows present, `0` missing
  required artifacts, `0` source-set or review-ID mismatches, `0` trace-hash
  mismatches, and `export_readiness.reason="sqlite_store_not_built"`.
  The `eval-trace-store-build` CLI now lives in
  `src/usfs_r1_ea_sources/eval_trace_store.py` and builds the generated local
  SQLite store from inventory JSON. The West Reservoir f70 seed store passed
  with `18` rows in each canonical table, `0` orphan rows, `0` duplicate IDs,
  `0` stale artifacts, `0` source artifact deletions, and `0` missing required
  links. The final closeout pass allows a parseable failed `phase_eval` artifact
  to seed its own store refresh before `phase-eval` rewrites it, while failed
  non-`phase_eval` origin artifacts still block. The `eval-trace-export` CLI now
  lives in `src/usfs_r1_ea_sources/eval_trace_export.py` and writes local
  canonical JSON plus OpenInference-shaped spans from the store. The West
  Reservoir f70 seed export passed with `18` traces, `36` exported spans, `0`
  missing tables, and `0` missing provenance fields. The `eval_trace_gate.py`
  helper now validates default inventory/store evidence for phase and promotion
  consumers. `phase-eval` reports top-level `eval_trace_gate` state and appends
  `first_class_eval_trace` only for matching evidence or ratcheted scopes.
  `promotion-suite` reports `eval_trace_gate_summary` and fails current
  promotion when a current-promotion phase-eval artifact reports a failed
  ratcheted eval-trace gate. The only enabled ratcheted scope is review
  `west-reservoir-67436`; there is no global or source-set-wide ratchet. The
  `eval-trace-case-promote` CLI now promotes selected trace/span rows from the
  local SQLite store into the tracked
  `config/eval_trace_cases/system_eval_trace_cases_v1.json` schema, requiring
  source artifact refs/hashes, owner/risk/tags, assertion or expected-output
  contract, review/removal conditions, deterministic scorer contracts, and
  human-label metadata. `llm_judge` remains reserved/deferred until a separate
  calibrated model-judge milestone.
- Resolved West Reservoir predecessor context: reviewer-readiness Milestone 4 is resolved locally on
  `source-set-f70ea11e04ae3d53`. West Reservoir-owned decision-support and
  final-QA configs/fixtures now drive the signer-facing packet artifacts;
  `review-packet-index --review-id west-reservoir-67436` passes with
  `check_count=30` and `failed_check_count=0`;
  `final-qa-certification --validate-only` passes `200/200`; and
  `phase-eval --review-id west-reservoir-67436` passes `32/32` with
  `first_class_eval_trace` ratcheted and `blockers=[]`. The real-package aggregate and forest-specific registry
  aggregate pass with West Reservoir as reviewer-ready. The inherited ECID
  source-delta component-coverage blocker is now closed locally as well:
  `forest-plan-component-eval-coverage` passes with all `10/10` required
  review slots covered, and the West Reservoir slot remains covered,
  source-set aligned, and passing. There is no active West follow-on slice
  until a new packet is explicitly opened.
- Milestone 0 in the West Reservoir packet is resolved locally as a historical
  baseline. Package authority remains green, the Milestone 0 V1 eval was a
  truthful typed-blocked baseline with only allowed blocker categories, and the
  pre-migration
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
  rules. The f70 forest-plan identity blocker Milestone 1 is reduced:
  `config/r1_forest_plan_identity_reconciliation_v1.json` declares
  `active_source_set_id="source-set-f70ea11e04ae3d53"`, governs
  `R1PLAN-flathead-nf-02 -> FINAL-FLAT-001`,
  `R1PLAN-flathead-nf-03 -> FPS-180`, and
  `R1PLAN-flathead-nf-05 -> FINAL-FLAT-003`, and leaves seven Flathead rows
  unresolved in tracked identity metadata. Child Milestone 2 supplied the six
  originally missing required Flathead support records to the local f70
  catalog/retrieval surface from the archived source-delta merged gate. F70
  extraction and retrieval pass with `714` sources and `110941` chunks, and
  direct readback indexes
  `R1PLAN-flathead-nf-04`, `R1PLAN-flathead-nf-06`,
  `R1PLAN-flathead-nf-07`, `R1PLAN-flathead-nf-10`,
  `R1PLAN-flathead-nf-12`, and `R1PLAN-flathead-nf-16`.
  Child Milestone 3 supplied the triggered monitoring-program support record
  `R1PLAN-flathead-nf-08` to the same local f70 generated catalog from the
  archived source-delta merged gate. At that child checkpoint, extraction and
  retrieval passed with `715` sources, `110982` chunks, `failed_count=0`, and
  `reviewer_ready=true`. Later Bitterroot and Idaho Panhandle source-delta
  slices raised the repo-current f70 contract to `719` sources, `707` artifacts,
  and `11` supplemental overlay rows. Direct retrieval SQLite readback indexes
  `R1PLAN-flathead-nf-08=41` chunks. `forest-plan-resolve` now emits current
  f70 Flathead context and component artifacts, retrieval readiness passes with
  `blocking_missing_source_record_ids=[]`, and
  `forest_plan_context_validation.json` passes. Parent Milestone 2 component
  readiness is now resolved locally: component adjudication eval passes with
  `48/48` resolved and `pending=0`, component eval passes `27/27` on
  `source-set-f70ea11e04ae3d53`, and the West Reservoir aggregate component
  slot now passes/source-set aligns. Parent Milestone 3 later promoted West
  Reservoir to reviewer-ready in the V1 contract, real-package manifest, and
  forest-specific registry. Milestone 4 later closed packet index validation,
  phase eval, and aggregate reporting for West Reservoir; the remaining ECID
  residual is separate rule-claim/compliance direct-eval work on the historical
  source-delta lane.
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
- `config/v1_real_package_review_coverage_v1.json` now has six load-bearing
  active slots, including Bitterroot Front, South Otter, Lolo, and HLC Bonanza
  as required `forest_specific_reviewer_ready` slots. The governed aggregate
  rerun reports `passed=true`, `covered_slot_count=6`,
  `required_slot_count=6`, `reviewer_ready_slot_count=6`,
  `typed_blocked_slot_count=0`, `distinct_forest_count=5`,
  `distinct_package_style_count=7`, and no missing required slots or coverage
  classes.
- `config/forest_specific_example_package_registry_v1.json` now has six active
  governed examples: East Crazy and South Otter for Custer Gallatin,
  Bitterroot Front for Bitterroot, West Reservoir for Flathead, Tyler's Kitchen
  for Lolo, and Bonanza for HLC.
  South Plateau is retained only under `archived_review_examples` with
  `usage_policy="historical_evidence_only_not_example"`. The
  governed forest-specific aggregate rerun reports `passed=true`,
  `review_example_count=6`, `reviewer_ready_example_count=6`,
  `distinct_governed_example_forest_count=5`,
  `profile_guidance_only_count=5`, and no threshold failures.
- West Reservoir's Flathead package authority is now verified against the
  official Flathead project page
  `https://www.fs.usda.gov/r01/flathead/projects/67436` and linked Pinyon/Box
  folder `https://usfs-public.app.box.com/v/PinyonPublic/folder/299363475796`.
  The tracked verification manifest
  `config/review_package_authority_verifications/west-reservoir-67436.json`
  records `12` official PDFs, `12` local package-manifest rows, byte-size and
  SHA-256 matches for every document, and `omitted_document_count=0`. This
  repairs package-authority provenance only; West Reservoir is now a
  reviewer-ready Flathead example.
- `config/forest_plan_component_eval_coverage_v1.json` now requires Bitterroot
  Front and HLC Bonanza as forest-specific component-eval review slots. Both
  slots are covered, source-set aligned, and passing. Later packets resolved
  the inherited ECID source-delta component-coverage slot and the remaining
  `8a40` rule-claim/compliance direct-eval residuals; ECID is now
  reviewer-ready historical replay evidence, not a current promotion route.
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
- Forest-plan component eval coverage is not a blocker for the Lolo, South
  Otter, or HLC Bonanza review-scope closeouts: all three slots are aligned and
  pass on `f70...`.
  The aggregate `forest-plan-component-eval-coverage` command is now green
  after later source-delta repairs; no ECID residual remains for the Lolo,
  South Otter, HLC, or Bitterroot component-coverage closeouts.
- Aggregate truth:
  Lolo forest-specific example promotion and South Otter primary-example
  selection remain green in the non-strict promotion suite. South Plateau is
  not an active promotion-suite expansion slot. The old strict-expansion
  `historical_source_set_split` label is no longer the live `phase-eval`
  blocker after the replay-context repair, and the later `8a40`
  rule-claim/compliance direct-eval residuals are resolved locally. ECID is
  reviewer-ready historical replay evidence and remains outside current
  contract-backed promotion because it has no declared review contract.
- Do not route the ECID historical slot into current promotion, reopen the
  older Lolo or replay-repair packets as live runtime work, or treat ECID as
  residual work for the Lolo, South Otter, HLC, Bitterroot, Beaverhead, Idaho,
  Nez Perce-Clearwater, or Dakota example promotions.
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
