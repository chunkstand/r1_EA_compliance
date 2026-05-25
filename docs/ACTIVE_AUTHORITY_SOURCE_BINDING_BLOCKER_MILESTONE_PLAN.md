# Active Authority Source Binding Blocker Milestone Plan

Date: 2026-05-25

Status: Active packet (`Milestones 0-1 resolved locally; Milestone 2 governed repair next`)

Owner context: this is a fresh standalone blocker packet opened from
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` after Milestone `1`
replay work fixed ECID applicability universe routing bugs but still failed on
active-source authority coverage. It owns the governed authority-source
binding problem on `source-set-4fb59e9eb43045cb`. It does not reopen the
slot-driven promotion-suite contract packet, and it does not weaken the
reviewer-ready roster inside
`config/v1_real_package_review_coverage_v1.json`.

## Purpose

Restore truthful active-source authority binding for the reviewer-ready
applicability universe on `source-set-4fb59e9eb43045cb`.

The ECID replay-repair lane no longer fails first on mixed forest-plan
inventory shape or legacy source-ID aliasing. Those bugs are now repaired in
the applicability universe owners. The remaining blocker is upstream of
packet-local replay:

- `applicability-authority-universe` for
  `v1-cg-ecid-compliance-review` now rebuilds a correctly scoped authority
  universe with `candidate_authority_count=396` and
  `forest_plan_component_candidate_count=329`
- the same run still fails validation on
  `candidates_have_source_evidence_available` with `failure_count=21`
  and on
  `authority_family_template_candidates_cover_config` with
  `missing_source_record_count=19`
- because applicability validation cannot pass, generated reviewer-ready rule
  pack replay cannot resume truthfully, so the ECID reviewer-ready slot cannot
  be repaired inside the replay-local packet yet

This packet exists to classify and repair those authority-source binding gaps
through governed source-record reconciliation or active-source coverage, then
hand control back to the replay-repair packet.

## Current Evidence

- `source_library/reviews/v1-cg-ecid-compliance-review/applicability/authority_universe_snapshot.json`
  now reports:
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `validation_passed=false`,
  `failed_check_names=["candidates_have_source_evidence_available","authority_family_template_candidates_cover_config"]`,
  `source_evidence_failure_count=21`, and
  `missing_source_record_count=19`.
- The mixed Region 1 inventory boundary is now behaving correctly for ECID:
  `selected_component_forest_unit_ids=["custer-gallatin-nf"]` even though the
  default `component_inventory.json` is a batch inventory with
  `forest_unit_id=null`.
- Existing governed reconciliation already covers some active aliases, for
  example `R1EA-150 -> ["USFS-035","LEX-USFS-002","LEX-USFS-003","LEX-USFS-004","LEX-USFS-006","LEX-USFS-007"]`,
  and the active rule-claim links already use those reconciled source records.
- Remaining blocker examples after the alias repair include missing active
  source bindings for authority-family and rule-pack references such as
  `R1EA-092`, `R1EA-032`, `R1EA-037`, `R1EA-041`,
  `R1PLAN-custer-gallatin-nf-06`, and
  `R1PLAN-region-1-species-overlay-01`.

## Goal

Repair the governed authority-source binding layer so the active applicability
universe can pass on `source-set-4fb59e9eb43045cb` without weakening source
evidence requirements.

Completion means all of the following are true:

- The missing authority-source IDs are classified as either:
  governed reconciliation gaps, true active-source coverage gaps, or obsolete
  references that must be removed only through governed source-truth owners.
- The selected owner surface is repaired with focused tests and durable docs.
- `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  passes on the active source set.
- The replay-repair packet can resume from truthful applicability validation
  instead of stale artifacts or bypasses.

## Non-Goals

- Do not relax `candidates_have_source_evidence_available`.
- Do not bypass the blocker with stale reviewer-ready artifacts from an older
  source set.
- Do not mark ECID or South Plateau as reviewer-ready until the active source
  binding problem is repaired.
- Do not reopen the promotion-suite selector/quorum contract packet.

## Owner Surfaces

- canonical source-truth and active catalog evidence:
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `source_library/catalog/source_catalog.jsonl`,
  and any source-truth packet that governs missing active authority rows
- governed reconciliation and source-binding config:
  `config/compliance_source_record_reconciliation_v1.json`,
  `config/authority_family_rule_templates_nepa_ea_v1.json`,
  `config/compliance_rule_pack_nepa_ea_v0.json`,
  and any source-truth owner that legitimately governs missing active records
- applicability universe runtime owners:
  `src/usfs_r1_ea_sources/applicability_contract_support.py`,
  `src/usfs_r1_ea_sources/applicability_candidate_assembly.py`,
  `src/usfs_r1_ea_sources/applicability_authority_family_templates.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_builder.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py`
- focused tests:
  `tests/test_applicability_candidate_assembly.py`,
  `tests/test_applicability_authority_family_templates.py`,
  `tests/test_applicability.py`,
  `tests/test_applicability_authority_universe_contracts.py`,
  `tests/test_applicability_authority_universe_builder.py`
- replay-routing docs:
  `README.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Milestone Sequence

### Milestone 0 - Missing Binding Baseline

Outcome label: resolved

Purpose: freeze the post-repair blocker set before any governed source-binding
 edits begin.

Implementation:

1. Record the current failing authority-universe checks and counts on the
   active source set.
2. Separate already-fixed routing bugs from remaining missing authority-source
   binding failures.
3. Route this blocker packet from the replay-repair packet and current docs.

Acceptance criteria:

- The packet records the active `396`-candidate / `329`-component authority
  universe result and the remaining `21` source-evidence + `19` missing-source
  failures.
- Repo routing no longer claims ECID replay can continue directly from
  Milestone `1` inside the replay-local packet.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --source-set-id source-set-4fb59e9eb43045cb
```

Milestone 0 resolution on 2026-05-25:

- The baseline rerun still fails exactly where the replay-repair Milestone `1`
  reduction handed off: `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `selected_component_forest_unit_ids=["custer-gallatin-nf"]`, and
  `validation_passed=false` on `source-set-4fb59e9eb43045cb`.
- The old routing bugs are now frozen as repaired rather than live blockers:
  `forest_plan_component_candidates_use_profile_inventory` passes on the ECID
  review forest, and governed legacy source-ID reconciliation still resolves
  examples such as `R1EA-150` against active catalog aliases.
- `candidates_have_source_evidence_available` now freezes a `21`-candidate
  blocker set: `16` authority-family templates
  (`clean_air_act_conformity_air_quality`,
  `clean_water_act_wotus_permits`,
  `cultural_resource_protection_and_state_shpo_sources`,
  `eagle_efh_and_special_wildlife_sources`,
  `floodplain_management_eo11988`,
  `forest_service_planning_handbook_amendments`,
  `grassland_bankhead_jones_authorities`,
  `hazardous_materials_site_condition`,
  `invasive_pesticide_soils_farmland_drinking_water`,
  `minerals_energy_authorities`,
  `region1_forest_plan_source_records`,
  `roads_access_special_use_action_authorities`,
  `species_supporting_sources_and_overlays`,
  `tribal_consultation_trust_sacred_sites`,
  `vegetation_wildfire_forest_health_authorities`,
  `wilderness_wsr_trails_designated_areas`) plus `5` rule templates
  (`apa_final_agency_action`, `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`, `organic_act_16usc_475`,
  `seven_county_nepa_scope`).
- `authority_family_template_candidates_cover_config` now freezes a `19`
  family-template coverage blocker set. Representative missing source-record
  clusters include `R1EA-092` and `R1EA-093` (air quality),
  `R1EA-082` through `R1EA-091` plus `R1EA-115` through `R1EA-118`
  (clean water / WOTUS), `R1EA-072` through `R1EA-080` plus
  `R1EA-113`, `R1EA-114`, and `R1EA-120` through `R1EA-123`
  (cultural / SHPO / tribal), `R1EA-032`, `R1EA-037`, `R1EA-038`,
  `R1EA-041`, `R1EA-063`, `R1EA-143`, `R1PLAN-custer-gallatin-nf-06`,
  `R1PLAN-custer-gallatin-nf-07`,
  `R1PLAN-region-1-grassland-overlay-01`,
  `R1PLAN-region-1-species-overlay-01`,
  `R1PLAN-region-1-species-overlay-02`, and the land-exchange-only
  `R1EA-125` through `R1EA-162` family.
- Historical next truthful slice at the Milestone `0` baseline-freeze
  checkpoint:
  Milestone `1` in this same packet; the live route after the Milestone `1`
  owner-selection closeout is Milestone `2` governed repair.

### Milestone 1 - Classification And Owner Selection

Outcome label: resolved

Purpose: classify every remaining missing authority-source reference into the
correct governed owner.

Implementation:

1. Audit the failing source IDs against
   `config/compliance_source_record_reconciliation_v1.json`,
   active catalog evidence, and source-truth docs.
2. Split the failures into:
   reconciliation gaps,
   missing active source coverage,
   or obsolete references that must be retired through governed owners.
3. Write the resulting owner map back into this packet and the handoff.

Acceptance criteria:

- Every remaining blocker ID has one owner and one next command surface.
- No missing ID remains as an unclassified “maybe stale” note.

Milestone 1 resolution on 2026-05-25:

- The frozen blocker inventory now resolves into three governed owner classes
  with one next repair surface each.
- Reconciliation expansion owner:
  `config/compliance_source_record_reconciliation_v1.json` is the next repair
  surface for `clean_air_act_conformity_air_quality`,
  `clean_water_act_wotus_permits`,
  `cultural_resource_protection_and_state_shpo_sources`,
  `eagle_efh_and_special_wildlife_sources`,
  `floodplain_management_eo11988`,
  `forest_service_planning_handbook_amendments`,
  `hazardous_materials_site_condition`,
  `invasive_pesticide_soils_farmland_drinking_water`,
  `land_exchange_fs_policy_and_project_references`,
  `land_exchange_regulatory_requirements`,
  `land_exchange_statutory_authorities`,
  `minerals_energy_authorities`,
  `roads_access_special_use_action_authorities`,
  `tribal_consultation_trust_sacred_sites`,
  `vegetation_wildfire_forest_health_authorities`, and
  `wilderness_wsr_trails_designated_areas`. The active catalog already carries
  current rows for those families under current IDs such as `FED-023`,
  `FED-022`, `FED-024`, `FED-042`, `FED-036`, `USFS-033`, `USFS-034`,
  `R1-030`, `STP-026`, `LEX-USFS-002`, `LEX-USFS-012`, `LEX-FED-003`, and
  `USFS-035`, but the legacy `R1EA-*` family members are not yet governably
  rebound in the reconciliation file.
- Forest-plan identity rebind owner:
  the next repair surface for
  `grassland_bankhead_jones_authorities`,
  `region1_forest_plan_source_records`, and
  `species_supporting_sources_and_overlays` is the combined
  `config/compliance_source_record_reconciliation_v1.json` plus
  `config/authority_family_rule_templates_nepa_ea_v1.json` forest-plan
  identity boundary. These families still depend on stale `R1PLAN-*`
  overlays/support rows such as
  `R1PLAN-region-1-grassland-overlay-01`,
  `R1PLAN-custer-gallatin-nf-06`,
  `R1PLAN-custer-gallatin-nf-07`,
  `R1PLAN-region-1-species-overlay-01`, and
  `R1PLAN-region-1-species-overlay-02`, while the active plan/supporting
  corpus now lives under `FOR-*`, `FINAL-*`, `FPS-*`, and `R1-*` IDs; the
  reconciliation file currently binds only `R1PLAN-custer-gallatin-nf-02` to
  `FOR-009`.
- Source-truth addition-or-retirement owner:
  the next repair surface for
  `apa_final_agency_action`,
  `directives_notice_comment_36cfr_216`,
  `musuya_multiple_use_sustained_yield`,
  `organic_act_16usc_475`, and
  `seven_county_nepa_scope`
  is the canonical source-truth/workbook boundary plus
  `config/compliance_rule_pack_nepa_ea_v0.json`. Their reconciliation entries
  already exist but each records `current_source_record_ids=[]`, and active
  catalog scans found no current canonical row for Seven County, APA final
  agency action, 36 CFR part 216, MUSYA, or Organic Administration Act
  section 475, so Milestone `2` must either add current rows or formally
  retire those authorities through governed owners.
- No blocker family remains unowned after classification. The next truthful
  slice is now Milestone `2` in this same packet: land the governed repair
  against those three owner classes and rerun the ECID applicability universe.

### Milestone 2 - Governed Repair

Outcome label: resolved

Purpose: repair the chosen owner surfaces without weakening applicability
validation.

Implementation:

1. Land the minimal governed config/code/source-truth changes required to make
   the active source set satisfy the missing authority-source bindings.
2. Add or update focused tests for the chosen repair.
3. Re-run the applicability universe on ECID until validation passes.

Acceptance criteria:

- `applicability-authority-universe` passes for ECID on
  `source-set-4fb59e9eb43045cb`.
- No new skips, xfails, or relaxed checks are introduced.

### Milestone 3 - Replay Resume Handoff

Outcome label: resolved

Purpose: return control to the replay-repair packet with the blocker removed.

Implementation:

1. Update routing docs so the active replay-repair packet resumes from ECID
   applicability validation rather than from stale reviewer-ready assumptions.
2. Record the exact replay-resume commands for the next packet.
3. Close this blocker packet with one local atomic commit.

Acceptance criteria:

- `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` becomes the next
  truthful packet again only after this blocker is cleared.
- The docs name the exact resume command chain.
