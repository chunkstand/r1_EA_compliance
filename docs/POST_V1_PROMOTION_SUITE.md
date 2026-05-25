# Post-V1 Promotion Suite

Date: 2026-05-06

The post-V1 promotion suite is the manifest-driven readiness path for agents. It does not replace
the underlying deterministic gates. It records which review artifacts, eval artifacts, source set,
rule pack, and package-expansion slots are required for a readiness claim.

Default manifest:

```text
config/promotion_suite_v1.json
```

The manifest now uses schema version `promotion-suite-v1`. Milestone 1 adds a
typed `current_promotion_contract` section that declares:

- governed slot selection from `config/v1_real_package_review_coverage_v1.json`
  plus the aggregate
  `reviews/real_package_review_coverage_eval/real_package_review_coverage_eval_results.json`
- same-slot review artifact families and suite-level families for the
  current-promotion lane
- quorum settings for eligible and passing current-promotion slots
- explicit reference canaries so a fixed proving packet remains visible after
  slot-driven runtime separation lands

The runtime now computes `current_promotion_ready` from the governed
coverage-class selector, same-slot family evaluation, and quorum checks. Fixed
reference canaries are reported separately and do not define the
`current_promotion_ready` gate.

Default outputs:

```text
source_library/reviews/promotion_suite/<suite_id>/promotion_suite_results.json
source_library/reviews/promotion_suite/<suite_id>/promotion_suite_report.md
```

Run the current suite:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite --output-dir source_library
```

Run it as a strict post-V1 expansion gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources promotion-suite \
  --output-dir source_library \
  --manifest config/promotion_suite_v1.json \
  --results-dir source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite-strict-expansion \
  --strict-expansion
```

When capturing normal and strict expansion signals in the same closeout pass, write the strict run
to a separate `--results-dir` or rerun the normal suite last. Otherwise both modes write to the
default `<suite_id>/promotion_suite_results.json` path, which can leave the default local result in
strict mode even though current promotion remains ready without `--strict-expansion`.

## Readiness Semantics

The result now separates four statuses:

- `current_promotion_ready`: the governed current-promotion slot selector finds
  enough eligible reviewer-ready slots, the same-slot and suite families pass,
  and the current-promotion quorum is satisfied for the current Custer
  Gallatin proving case.
- `full_canonical_corpus_ready`: the active `source_library/catalog/` contract matches the promoted
  full canonical corpus under the current code, and the active full-canonical source set also has
  its own `authority_currentness` plus NEPA 3D source-set graph artifacts. This is intentionally
  separate from reviewer-ready V1 promotion because the active catalog can move ahead of the
  current review-ready proving package lane.
- `expansion_ready`: every declared post-V1 real-package slot is filled and ready, and every
  manifest-declared `required_for_expansion` artifact check passes.
- `promotion_ready`: equal to `current_promotion_ready` unless `--strict-expansion` is supplied;
  strict mode also requires `expansion_ready`.

The results summary now also records the slot-driven current-promotion
contract details:

- governed slot rows with eligibility, source-set match, and contract-pass
  status
- family results for suite-level and same-slot review artifact families
- separate reference-canary pass/fail state and failure categories

Packet-local ECID semantic counts now stay in their focused owners such as
`config/ea_consistency_decision_support_v1.json`,
`config/east_crazies_final_qa_certification_v1.json`, and the matching focused
validator tests. The shared `promotion-suite` manifest keeps aggregate
freshness, status, and canary truth, not duplicate packet-local count locks.

The default manifest keeps two real-package expansion slots: the ECID preliminary-EA slot is ready,
and the South Plateau Area Landscape Treatment Project slot is selected but blocked on
`forest_plan_reviewer_not_ready`. Open expansion slots do not block the current V1 promotion claim,
but they make broader readiness gaps visible to future agents. Current promotion does require the
applicability seed and gold eval artifacts that prove
positive, negative, unresolved, replay-adjudicated, and arbitration-field coverage for the expanded
authority-family templates. It also requires the authority-family reviewer-report artifacts for the
promoted V1 review: authority-family provenance, non-applicable authority appendix,
reviewer-resolution report, and deterministic litigation-risk summary.

The default manifest now binds both active source-set identities to the same
current local corpus:

- `current_promotion_source_set_id=source-set-4fb59e9eb43045cb`
- `full_canonical_source_set_id=source-set-4fb59e9eb43045cb`

Older source-set references below are historical run notes. The current local
question is no longer which source set owns the repo contract; it is whether
the review-local ECID compliance/applicability artifacts have been fully
replayed onto that active source set.

## Failure Taxonomy

The suite uses explicit failure categories so a failed run points at the next engineering lane:

- `missing_source`
- `extraction_miss`
- `retrieval_miss`
- `applicability_miss`
- `unsupported_package_evidence`
- `stale_artifact`
- `adjudication_needed`
- `forest_plan_reviewer_not_ready`
- `package_fixture_missing`
- `graph_missing_authority_family`
- `graph_missing_candidate_authority`
- `graph_missing_source_record`
- `graph_missing_source_partition`
- `graph_missing_currentness_status`
- `graph_missing_applicability_decision`
- `graph_dangling_edge`
- `graph_stale_artifact`
- `graph_noncurrent_document_in_main_corpus`
- `graph_superseded_as_current`
- `graph_handbook_chapter_collapsed`
- `graph_viewer_export_invalid`
- `graph_region1_profile_gap`

Current-promotion failures are reported in `failure_category_counts`. Expansion-only failures are
reported separately in `expansion_failure_category_counts`; they enter `failure_category_counts`
only when strict mode is used.
Reference-canary failures are reported separately in
`reference_canary_failure_category_counts`.

Selected expansion slots are validated as contracts, not placeholders. A selected not-ready slot
must define review ID, source set, package path, expected gate artifacts, next action, and a typed
failure category other than `package_fixture_missing`. A ready slot must not retain a failure
category, must still carry the review/package/source-set contract, and its expected gate artifacts
must cover the matching review case's `required_for_expansion` artifact IDs. The generated Markdown
report includes selected-slot review IDs, package paths, and failure categories so the typed
blocker is visible without inspecting raw JSON. A slot that declares `forest_plan_profile` must also
have expansion gate contracts for `compliance_review`, `forest_plan_context_summary`, and
`phase_eval`; the runtime slot check fails closed if the artifact scope, validation, reviewer-ready
status, or last local signal does not prove the declared profile.

## Current Local Result

The current routed truth on 2026-05-25 is now red at the review-local replay
layer rather than the slot-driven contract layer.

- `source_library/reviews/real_package_review_coverage_eval/real_package_review_coverage_eval_results.json`
  reports `passed=false`, `reviewer_ready_slot_count=0`, and reviewer-ready
  slot mismatches for ECID current promotion plus South Plateau reviewer-ready
  expansion, while West Reservoir still truthfully passes as `typed_blocked`.
- `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  reports `full_canonical_corpus_ready=true`,
  `passed_required_full_canonical_result_count=10/10`,
  `current_promotion_ready=false`, `promotion_ready=false`,
  `expansion_ready=false`, and `passed_required_current_result_count=11/32`.
  Inside the slot-driven contract,
  `current_promotion_contract.selector_passed=false`,
  `matched_slot_count=0`, `eligible_slot_count=0`,
  `passing_slot_count=0`, and
  `current_promotion_contract.quorum_passed=false`, so the contract refactor
  itself is still not the blocker; the governed reviewer-ready slot result is
  simply not currently eligible.
- The active follow-on is
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md`, which owns ECID
  and South Plateau packet-local replay repair on
  `source-set-4fb59e9eb43045cb`. Milestone `1` of that packet is now reduced
  locally: ECID applicability replay now correctly rebuilds a
  `396`-candidate authority universe with `329` Custer Gallatin component
  candidates from the active Region 1 batch inventory and honors governed
  legacy-to-current source-record reconciliation, but the same run still fails
  on `candidates_have_source_evidence_available` (`failure_count=21`) and
  `authority_family_template_candidates_cover_config`
  (`missing_source_record_count=19`). The authority-source binding blocker
  packet in `docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md`
  is now reduced locally through Milestone `2`: the exact current rows already
  present in the active catalog are now governably bound, the live ECID
  applicability replay is reduced to `11` source-evidence failures and `17`
  missing source-record template groups on
  `authority_universe_sha256=2f99cee2bf5bdbb148cc4b97b5c8d00d370baf9e1a8cb72e623a99226534dc22`,
  and no untouched exact current-catalog URL matches remain for the reduced
  missing-ID inventory. The new active blocker packet is now
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`.

Historical South Plateau expansion build context from the earlier green
expansion pass remains below:

- imported `26` official South Plateau PDFs from the project Box folder;
- extracted `26/26` package files into `3,671` chunks with `.venv-docling`;
- `applicability-authority-universe`: passed with `392` candidate authorities;
- `applicability-context-build`: passed package fact/context validation;
- `applicability-retrieve`: passed trace validation, with diagnostics retained for all candidates;
- `applicability-determine`: initially produced `55` applicable, `331` non-applicable, and `6`
  `needs_adjudication` authority-family decisions;
- `applicability-adjudication-eval`: passed with `6` resolved adjudications and `0` pending
  adjudications;
- `applicability-adjudication-apply`: passed with `applied_item_count=6` and
  `remaining_unresolved_authority_count=0`;
- `applicability-validate`: now passes with `61` applicable, `331` non-applicable, no unresolved
  or `needs_adjudication` decisions, and `generated_rule_pack_ready=true`;
- `applicability-generate-rule-pack`: passed with `61` generated rules and
  `generated_rule_pack_ready=true`;
- `compliance-review`: runs from the cached package and generated rule pack, resolves
  `scope_status="custer_gallatin"` with forest-plan context `validation_passed=true`, but now
  exits nonzero because the required forest-plan component gate is pending;
- forest-plan component evaluation: `329` components, `152` applicable components, `24`
  applicable standards, `21` applied standards, `31` gaps, and `31` reviewer-resolution items;
- `forest-plan-component-adjudication-template`: generated a `31`-item worklist; the paired
  `forest-plan-component-adjudication-eval` currently fails with `31` pending adjudications;
- South Plateau review-scoped `phase-eval`: fails `15/17` with blockers limited to
  `compliance_review` and `forest_plan_component_adjudication`;
- the promoted V1 review-scoped `phase-eval` was rerun after the South Plateau review-scoped pass
  to restore the shared current-promotion phase-eval artifact at `20/20`;
- non-strict `promotion-suite`: `current_promotion_ready=true`, `promotion_ready=true`,
  `expansion_ready=false`, `expansion_artifacts_ready=false`, `failure_category_counts={}`,
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`,
  `open_expansion_artifact_count=5`, and `open_expansion_slot_count=1`;
- strict expansion `promotion-suite`: expected command failure with `current_promotion_ready=true`,
  `promotion_ready=false`, `expansion_ready=false`,
  `failure_category_counts={"forest_plan_reviewer_not_ready": 6}`, and
  `expansion_failure_category_counts={"forest_plan_reviewer_not_ready": 6}`.

A later final-QA promotion pass added current-promotion checks for the final QA packet family. The
V1 review-bound phase eval now passes `20/20` phases, the non-strict promotion suite passes
`26/26` required current-promotion results, and the current gates report `failure_category_counts={}`.
Strict expansion now fails closed only on the South Plateau forest-plan blocker while still passing
`26/26` required current-promotion results.

Full-corpus promotion closeout on 2026-05-10 added active-catalog checks to the
default manifest. The latest local non-strict run on 2026-05-24 now reports
`full_canonical_corpus_ready=true` and
`passed_required_full_canonical_result_count=10/10` on
`source-set-4fb59e9eb43045cb`, while `current_promotion_ready=false`,
`promotion_ready=false`, and `expansion_ready=false`. The active catalog checks
now pin `source_library/catalog/source_set_manifest.json`,
`catalog_validation.json`, `authority_currentness`, and the NEPA 3D graph
surfaces to the active source set with `647` source rows, `635` artifacts,
`594` admitted active-review rows, and `53` explicit archive/currentness rows.
The refreshed active NEPA 3D source-set export now passes with `72` checks,
`0` failed checks, `3,677` nodes, `7,262` edges,
`region1_forest_plan_graph_ready_profile_count=10`, and
`region1_forest_plan_blocked_profile_count=0`. The remaining blocker is no
longer a split source-set graph ownership problem; it is the stale or missing
review-local artifact family across the governed ECID and South Plateau slots.
ECID still keeps current promotion red through stale compliance/applicability,
packet-index, decision-support, final-QA, provenance, and review-graph
surfaces, including `compliance_review_eval` still carrying the older
review-local source-set identity; South Plateau also still mismatches its
governed reviewer-ready slot through `review_artifact_missing` and
`forest_plan_matrix_miss`.

The South Plateau expansion slot remains `ready=false` and carries
`forest_plan_reviewer_not_ready`. The previous ambiguous-scope blocker is closed:
`forest_plan_context_summary.json` now records `scope_status="custer_gallatin"` and
`validation_passed=true`. The blocker is the `31` pending component adjudications required before
the component gate, compliance validation, South Plateau phase eval, and strict expansion can pass.
The promotion manifest includes the component findings, reviewer-resolution queue, adjudication
template, adjudication eval, compliance outputs, forest-plan context summary, and review-scoped
phase-eval artifact checks rather than a slot flag alone.

The Sequence 6 alignment pass also reconciled each ready expansion slot's `expected_gate_artifacts`
with its matching `required_for_expansion` review-case checks. Manifest validation now rejects ready
slots whose expected gate list omits required expansion artifact IDs, preventing a future ready-slot
flag from drifting away from the concrete artifact gate.

The Sequence 7 hardening pass added the declared-profile boundary: a selected slot with
`forest_plan_profile` must either resolve to that profile with `validation_passed=true` and
`reviewer_ready=true`, or stay blocked with the typed forest-plan failure category.

The post-V1 applicability artifact family exists for the promoted review and is included in
`phase-eval --review-id`. The applicability seed eval now covers all `19` high-priority
authority-family templates with positive and negative cases, plus explicit arbitration cases for
weak auxiliary evidence, weak-only evidence, positive/negative conflicts, no-action/background-only
evidence, and rule-template-specific trigger sufficiency. The gold eval includes unresolved and
replay-adjudicated authority-family profiles and now carries explicit arbitration-field
expectations. The promoted review also writes the authority-family sidecars and the promotion
manifest requires them before current promotion passes.

The first expansion slot is now a concrete local pass:
`region1-expansion-ecid-preliminary-ea`, using the preliminary EA package under the ECID intake.
The package cache extracted `7` PDFs into `160` chunks, and applicability determination produced
`43` applicable authorities, `346` non-applicable authorities, and `3` decisions requiring
adjudication after the evidence-arbitration replay. Sequence 1 completed and replayed those three
adjudications as `human_applicable`; `applicability-validate` now passes with `46` applicable
authorities, `346` non-applicable authorities, `0` unresolved, `0` `needs_adjudication`,
`generated_rule_pack_ready=true`, and `reviewer_ready=true`. Sequence 2 generated and validated the
ECID rule pack with `46` rules, wrote the compliance review/matrix/PDF artifacts, wrote
review-scoped phase eval at `source_library/reviews/region1-expansion-ecid-preliminary-ea/`, and
added ECID artifact checks to the promotion suite. Sequence 2A closed the ECID source-claim gap:
the compliance artifact now has `rule_claim_gap_count=0` and `rule_claim_link_count=211`. Sequence
2B completed the `158`-row Forest Plan component adjudication queue, and
`forest-plan-component-adjudication-eval` reports `resolved_adjudication_count=158`,
`real_ea_omission_count=158`, `pending_adjudication_count=0`, and `system_miss_count=0`. ECID
compliance review now reports `reviewer_ready=true`, review-scoped phase eval passes, and the ECID
expansion slot is `ready=true`. The second real-package slot is South Plateau Area Landscape
Treatment Project. It now has an imported package, package cache, applicability context, retrieval
trace, decision ledger, adjudication eval/apply artifacts, passing generated rule-pack artifacts,
resolved Custer Gallatin forest-plan context, forest-plan component findings, a reviewer-resolution
queue, and a pending component-adjudication eval. Its expansion slot is blocked on
`forest_plan_reviewer_not_ready` until the `31`-item component adjudication worklist is completed
and the downstream compliance/phase/promotion gates are replayed.
