# Active Authority Source Binding Blocker Milestone Plan

Date: 2026-05-25

Status: Reduced locally through Milestone `2`; live route moved to
`docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`

Owner context: this is a fresh standalone blocker packet opened from
`docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` after Milestone `1`
replay work fixed ECID applicability universe routing bugs but still failed on
active-source authority coverage. It owns the governed authority-source
binding problem on `source-set-4fb59e9eb43045cb`. It does not reopen the
slot-driven promotion-suite contract packet, and it does not weaken the
reviewer-ready roster inside
`config/v1_real_package_review_coverage_v1.json`.

## Purpose

Record the now-reduced authority-source binding packet honestly and route the
remaining ECID applicability residue to its new governed owner.

This packet opened to repair the shared authority-source binding layer for the
reviewer-ready applicability universe on `source-set-4fb59e9eb43045cb`. That
binding lane is now reduced, not live:

- the applicability-universe owners already repaired the earlier mixed
  forest-plan inventory and legacy source-ID routing bugs
- this packet then landed the exact current-row reconciliation and shared alias
  reuse that were already supported by the active catalog and committed
  forest-plan identity registry
- after that repair, the ECID applicability replay no longer stops on the old
  `21` / `19` binding baseline; it now stops on a smaller remaining
  current-source truth blocker (`11` source-evidence failures and `17`
  missing-source template groups) that is owned by
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`

This packet therefore remains as the reduced closeout record for the governed
binding layer rather than as the live blocker plan.

## Current Evidence

- This packet's historical Milestone `0-1` baseline was the
  `21`-candidate / `19`-template blocker inventory frozen before governed
  repair began.
- After Milestone `2`, the live ECID replay now reports
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=2f99cee2bf5bdbb148cc4b97b5c8d00d370baf9e1a8cb72e623a99226534dc22`,
  `validation_passed=false`,
  `source_evidence_failure_count=11`, and
  `missing_source_record_count=17`.
- The mixed Region 1 inventory boundary is now behaving correctly for ECID:
  `selected_component_forest_unit_ids=["custer-gallatin-nf"]` even though the
  default `component_inventory.json` is a batch inventory with
  `forest_unit_id=null`.
- Existing governed reconciliation now also covers the exact current rows that
  were already present in the active catalog for legacy IDs such as
  `R1EA-030`, `R1EA-032`, `R1EA-037`, `R1EA-082`, `R1EA-092`,
  `R1EA-155`, and Region 1 overlay support rows such as
  `R1PLAN-region-1-grassland-overlay-01` and
  `R1PLAN-region-1-species-overlay-01`.
- No untouched exact current-catalog URL matches remain for the reduced
  missing-ID inventory. The remaining blocker is now current-source truth
  debt rather than more shared binding drift.

## Goal

Preserve an honest record of what this packet closed and where the remaining
blocker moved.

This packet's scoped goal is now reduced and closed by routing:

- the shared authority-source binding layer is reduced through the exact
  current-row repair it honestly owned
- the remaining applicability blocker is explicitly rerouted to
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`
  instead of staying mislabeled as live binding work here
- packet-local replay remains blocked until that new current-source truth
  packet clears

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

Outcome label: reduced

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

Milestone 2 reduction on 2026-05-25:

- The governed binding layer now lands in the shared owners rather than inside
  packet-local replay code: `records.py` now reuses the committed
  forest-plan identity registry snapshot when building alias sets, and
  `config/compliance_source_record_reconciliation_v1.json` now binds the
  exact active catalog rows that already existed for the remaining
  reconciliation-owned ECID authorities.
- The live ECID applicability-universe replay now reduces from
  `21` source-evidence failures and `19` missing source-record template groups
  to `11` and `17` respectively on
  `authority_universe_sha256=2f99cee2bf5bdbb148cc4b97b5c8d00d370baf9e1a8cb72e623a99226534dc22`.
- The exact-match binding lane is now exhausted: a local audit across
  `source_library/manifests/*.jsonl` and
  `source_library/catalog/source_catalog.jsonl` returns no untouched exact
  current-catalog URL matches for the remaining missing IDs.
- The remaining blocker is therefore no longer principally a source-binding
  problem. It is now a governed current-source truth problem spanning stale
  template/rule-pack references and forest-plan support rows that still lack
  current canonical coverage.
- The next truthful slice is no longer Milestone `3` in this packet. The live
  route now moves to
  `docs/ACTIVE_AUTHORITY_CURRENT_SOURCE_GAP_BLOCKER_MILESTONE_PLAN.md`,
  which freezes the reduced `11` / `17` residue and owns the remaining
  current-source repair before the replay-repair packet can resume.

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
