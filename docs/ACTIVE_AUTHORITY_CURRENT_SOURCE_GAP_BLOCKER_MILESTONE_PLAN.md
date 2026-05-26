# Active Authority Current-Source Gap Blocker Milestone Plan

Date: 2026-05-25

Status: Historical upstream blocker packet (`Milestone 1 resolved locally; Milestone 2 reduced locally through current-source closeout; remaining replay-local blocker handed back upstream`)

Owner context: this is a fresh standalone blocker packet opened from
`docs/ACTIVE_AUTHORITY_SOURCE_BINDING_BLOCKER_MILESTONE_PLAN.md` after
Milestone `2` reduced the ECID applicability-universe blocker to a smaller
remaining current-source truth set. It owns the source-truth, template, and
rule-pack work still required on the ECID current-source-gap replay gate. It
does not
reopen the replay-local ECID packet, the slot-driven promotion-suite contract
packet, or the already-landed governed reconciliation and alias repairs.

## Purpose

Restore truthful current-source coverage for the remaining ECID
applicability-universe authorities after exact-match governed reconciliation is
exhausted.

The prior blocker packet repaired the shared binding layer honestly:

- `records.py` now resolves active authority aliases through governed
  reconciliation plus the committed forest-plan identity registry snapshot
- `config/compliance_source_record_reconciliation_v1.json` now binds the
  evidence-backed exact current rows that were already present in the active
  catalog
- the same ECID applicability-universe replay is now smaller but still red:
  the remaining blocker is no longer “find the current row that already exists”
  work; it is now “add, replace, or retire stale source references through
  governed current-source owners” work

This packet exists to close that remaining current-source gap without weakening
applicability validation. The reviewer-facing default catalog and promotion
suite remain pinned to historical `source-set-4fb59e9eb43045cb`; this packet
may use a same-slice scoped catalog gate when the governed workbook truth moves
ahead of that downstream stack.

## Current Evidence

- The reviewer-facing default catalog still lives at
  `source_library/catalog/source_set_manifest.json` as
  `source-set-4fb59e9eb43045cb` with `source_count=647`,
  `artifact_count=635`, and
  `source_partition_counts={"active_review_corpus": 594, "currentness_supersession_archive": 53}`.
- `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx --output-dir source_library --config config/downloader.toml --run-id queue-m3-full-canonical-merged-download-20260525-current-gap-closeout --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  now builds the blocker closeout replay gate as
  `source-set-f70ea11e04ae3d53` with `source_count=708`,
  `artifact_count=696`, and
  `source_partition_counts={"active_review_corpus": 655, "currentness_supersession_archive": 53}`.
- `PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe --output-dir source_library --review-id v1-cg-ecid-compliance-review --catalog-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl --source-set-manifest-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json`
  now rebuilds the ECID applicability universe at
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=5a7f58afc84a4701bfc23e3da53651f674a0975394514dfa4d815d23ca6a2094`,
  and `validation_passed=false`.
- `candidates_have_source_evidence_available` now passes with
  `failure_count=0`.
- `authority_family_template_candidates_cover_config` now passes with
  `missing_source_record_count=0`. The admitted-current replacement lane plus
  the governed land-exchange retirement closeout now cover `R1EA-038`,
  `R1EA-043`, `R1EA-068`, `R1EA-125` through `R1EA-149` (except
  already-bound `R1EA-146`), `R1EA-151` through `R1EA-156`, and the retired
  non-controlling project-reference rows `R1EA-160` through `R1EA-162`. The
  governed `R1EA-093` current-source addition is now closed through workbook
  row `FED-044` plus same-slice reconciliation, and the governed water-family
  additions are now closed through workbook rows `FED-045` through `FED-051`
  plus `STP-031` through `STP-034`, the governed cultural-resource lane is
  now closed through workbook rows `FED-052` through `FED-059` plus `STP-035`,
  and the governed wildlife lane is now closed through workbook rows
  `FED-060` through `FED-062`, while the governed hazardous-material lane is
  now closed through workbook row `FED-063` and the governed
  invasive/farmland/drinking-water lane is now closed through workbook rows
  `FED-064` through `FED-069`, while the governed minerals lane is now closed
  through workbook row `FED-070`, the governed forest-plan support lane is
  now closed through the admitted `R1PLAN-*` planning and index pages, the
  governed vegetation/fire lane is now closed through workbook rows
  `FED-071` through `FED-077`, and the governed wilderness/designated-area
  plus base-rule closeout is now closed through workbook rows `FED-078`
  through `FED-087`.
- A local exact-current-match audit against
  `source_library/manifests/*.jsonl` and
  `source_library/catalog/source_catalog.jsonl` now returns no untouched exact
  current-catalog URL matches for the remaining missing IDs. The exact-match
  reconciliation lane is exhausted.
- The only remaining failing applicability check is now
  `rule_template_candidates_have_source_claim_linkage`
  (`failure_count=48`) because the scoped gate has no
  extraction/retrieval/claim/rule-claim derived artifacts yet and therefore
  records `rule_claim_links_path=null`. That replay-local gap is outside this
  packet's source-truth owner boundary.

## Goal

Repair or retire the remaining stale current-source references through governed
source-truth owners so the ECID applicability universe can pass on the active
current-source-gap replay gate.

Completion means all of the following are true:

- The remaining missing source IDs are classified to one governed owner:
  current catalog/workbook addition,
  template/rule-pack replacement,
  or explicit retirement of obsolete authority references.
- `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  passes on the active current-source-gap replay gate.
- The replay-repair packet can resume from truthful applicability validation
  rather than stale or partial current-source coverage.

## Non-Goals

- Do not weaken `candidates_have_source_evidence_available`.
- Do not weaken `authority_family_template_candidates_cover_config`.
- Do not reopen the already-landed binding, selector, quorum, or replay-local
  bug repairs.
- Do not stage ignored `source_library/` artifacts.

## Scope

- Remaining ECID applicability-universe current-source gaps on the active
  current-source-gap replay gate
- Governed workbook/current-catalog/template/rule-pack changes needed to add,
  replace, or retire the remaining stale authority references
- Focused docs and handoff updates that route the next truthful slice

## Out Of Scope

- Promotion-suite architecture or replay-local slot-roster redesign
- South Plateau replay repair
- Downloader, catalog-build, extraction, or retrieval owner changes unrelated
  to the remaining source-truth gap
- Broader forest/example or queue packet work

## Owner Surfaces

- current source-truth and active catalog evidence:
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`,
  `source_library/runs/current-source-gap-clean-water-catalog-gate/catalog_gate/source_catalog.jsonl`,
  `source_library/runs/current-source-gap-clean-water-catalog-gate/catalog_gate/source_set_manifest.json`,
  `source_library/manifests/*.jsonl`
- governed authority-source config:
  `config/authority_family_rule_templates_nepa_ea_v1.json`,
  `config/compliance_rule_pack_nepa_ea_v0.json`,
  `config/compliance_source_record_reconciliation_v1.json`,
  `config/authority_family_rule_template_coverage_nepa_ea_v1.json`,
  `config/authority_universe_families_nepa_ea_v1.json`
- remaining forest-plan support/source-truth owners:
  `config/r1_forest_plan_identity_reconciliation_v1.json`,
  `config/r1_forest_plan_document_register_draft.csv`,
  and any governed source-truth packet that owns adding or retiring the
  remaining `R1PLAN-*` support rows
- runtime surfaces that must stay honest but should not be broadened unless the
  source-truth repair proves a new runtime bug:
  `src/usfs_r1_ea_sources/records.py`,
  `src/usfs_r1_ea_sources/applicability_contract_support.py`,
  `src/usfs_r1_ea_sources/applicability_authority_family_templates.py`,
  `src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py`
- focused tests:
  `tests/test_source_register_loader.py`,
  `tests/test_source_register_schema.py`,
  `tests/test_catalog.py`,
  `tests/test_dry_run.py`,
  `tests/test_preflight.py`,
  `tests/test_applicability_authority_family_templates.py`,
  `tests/test_authority_family_rule_templates.py`,
  `tests/test_authority_universe_inventory.py`,
  `tests/test_rule_claim_binding_runtime.py`,
  `tests/test_architecture_contract.py`
- routing docs:
  `README.md`,
  `docs/POST_V1_PROMOTION_SUITE.md`,
  `docs/CURRENT_ROUTING.md`,
  `docs/CURRENT_SYSTEM_STATE.md`,
  `docs/SESSION_HANDOFF.md`,
  this plan

## Placement Rules

- Add current-source truth in workbook or governed source-truth config first,
  not by hard-coding special cases into the applicability runtime.
- Use `config/compliance_source_record_reconciliation_v1.json` only for
  evidence-backed current replacements. Do not use it to guess or invent
  current rows that do not yet exist in the active catalog.
- If an authority reference is obsolete, retire or replace it in the owning
  template/rule-pack config with an explicit doc note; do not silently delete
  evidence requirements.
- Preserve the existing applicability validation gates. The packet must end
  with greener truth, not easier truth.

## Weak-Point Prevention Contract

- Weak point forecast: a later session makes the ECID applicability universe
  greener by weakening validation rather than fixing current-source truth.
  Owner surface:
  `src/usfs_r1_ea_sources/applicability_authority_universe_contracts.py`,
  `tests/test_applicability_authority_universe_contracts.py`,
  this plan
  Prevention gate:
  `applicability-authority-universe` must still fail closed on missing source
  evidence and missing configured source records.
  Fail threshold: the remaining blocker disappears only because validation got
  easier.
  Controlled violation: remove a required source row from a focused fixture or
  config and confirm the validation still fails.
  Future-Codex misuse scenario: a future agent flips a validation rule instead
  of repairing current-source truth; the gate must still catch the missing
  source.

- Weak point forecast: a later session adds speculative reconciliation mappings
  for remaining IDs that have no current catalog row.
  Owner surface:
  `config/compliance_source_record_reconciliation_v1.json`,
  `source_library/catalog/source_catalog.jsonl`,
  `source_library/manifests/*.jsonl`
  Prevention gate: every new reconciliation row in this packet must cite an
  active catalog row or a same-slice governed source-truth addition.
  Fail threshold: a new reconciliation entry points to a current row that did
  not exist in the active catalog or workbook/source-truth closeout.
  Controlled violation: attempt to map one remaining unresolved `R1EA-*` ID to
  a non-existent current row; the packet must stop instead of committing.
  Future-Codex misuse scenario: a future agent guesses at a current canonical
  row because the IDs look similar; the evidence gate must block that shortcut.

- Weak point forecast: a later session removes stale authorities from templates
  or rule packs without recording the governed replacement or retirement.
  Owner surface:
  `config/authority_family_rule_templates_nepa_ea_v1.json`,
  `config/compliance_rule_pack_nepa_ea_v0.json`,
  this plan
  Prevention gate: every template/rule-pack diff must name the old source ID,
  the new owner or retirement reason, and the exact applicability replay that
  justified the change.
  Fail threshold: a stale authority disappears from config without a documented
  replacement or retirement owner.
  Controlled violation: delete a remaining source ID from a template without
  routing it to a new current row; the packet must stay open.
  Future-Codex misuse scenario: a future agent trims hard cases out of config
  to get green; the doc and replay gate must reject that move.

## Milestone Sequence

### Milestone 0 - Post-Binding Baseline Freeze

Outcome label: resolved

Purpose: freeze the remaining current-source gap inventory after the governed
binding repair exhausts exact-match aliases.

Implementation:

1. Re-run ECID `applicability-authority-universe` on the active source set
   after the governed binding changes land.
2. Record the reduced remaining failure counts and family inventory.
3. Confirm that no remaining missing source ID still has an untouched exact
   current-catalog URL match.
4. Route this new packet as the active current slice.

Acceptance criteria:

- The packet records the live `11` source-evidence failures and `17`
  missing-source template groups on
  `authority_universe_sha256=2f99cee2bf5bdbb148cc4b97b5c8d00d370baf9e1a8cb72e623a99226534dc22`.
- The remaining missing-ID audit returns no untouched exact current-catalog URL
  matches.

Verification:

```bash
PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --source-set-id source-set-4fb59e9eb43045cb
```

Milestone 0 resolution on 2026-05-25:

- The post-binding replay is now reduced to `11`
  `candidates_have_source_evidence_available` failures and `17`
  `authority_family_template_candidates_cover_config` groups.
- The remaining source-evidence failures are now limited to six
  authority-family candidates plus five base-rule current-source gaps.
- The remaining missing-source inventory no longer contains any untouched exact
  current-catalog URL matches, so the next slice must move to governed
  source-truth ownership rather than more reconciliation-only edits.
- Historical next truthful slice at the Milestone `0` baseline-freeze
  checkpoint:
  Milestone `1` in this same packet; the live route after the Milestone `1`
  owner-map closeout is Milestone `2` governed repair.

### Milestone 1 - Remaining Gap Classification

Outcome label: resolved

Purpose: classify the remaining current-source gaps into one governed repair
owner each.

Implementation:

1. Split the remaining IDs into:
   workbook/current-catalog additions,
   template or rule-pack replacements,
   forest-plan support/source-truth additions,
   or explicit retirements of obsolete authority references.
2. Record the owner map back into this packet and the handoff.
3. Stop if any remaining ID still lacks one governed owner.

Acceptance criteria:

- Every remaining missing source ID has one next repair owner and no
  “maybe stale” ambiguity.
- The packet names the exact next command or config surface for each owner
  class.

Milestone 1 resolution on 2026-05-25:

- The live replay is unchanged at
  `candidate_authority_count=396`,
  `forest_plan_component_candidate_count=329`,
  `authority_universe_sha256=2f99cee2bf5bdbb148cc4b97b5c8d00d370baf9e1a8cb72e623a99226534dc22`,
  `source_evidence_failure_count=11`, and
  `missing_source_record_count=17`. This milestone is owner classification
  only; it does not repair current-source truth yet.
- Template replacement or explicit retirement in
  `config/authority_family_rule_templates_nepa_ea_v1.json` now owns the
  remaining legacy-only rows that already have an admitted current cluster in
  the active catalog:
  `R1EA-038` in `grassland_bankhead_jones_authorities`;
  `R1EA-125` through `R1EA-136` in
  `land_exchange_regulatory_requirements`;
  `R1EA-138` through `R1EA-149` in
  `land_exchange_statutory_authorities`;
  `R1EA-151`, `R1EA-152`, `R1EA-153`, `R1EA-154`, and `R1EA-156` in
  `land_exchange_fs_policy_and_project_references`;
  `R1EA-160`, `R1EA-161`, and `R1EA-162` as explicit retirements from that
  shared authority family because no admitted project-page/news/Box current
  rows survive in the active catalog;
  `R1EA-043` and `R1EA-143` in
  `roads_access_special_use_action_authorities`; and
  `R1EA-068` in `species_supporting_sources_and_overlays`.
- Governed current-source additions now own the remaining rows that still have
  no admitted active-catalog successor after targeted scans of
  `source_library/catalog/source_catalog.jsonl` for the surviving air,
  water, cultural, wildlife, hazardous-material, invasive/farmland/drinking
  water, wildfire/minerals, and designated-areas clusters:
  `R1EA-083` through `R1EA-090` and `R1EA-115` through `R1EA-118`;
  `R1EA-072`, `R1EA-074`, `R1EA-076` through `R1EA-080`,
  `R1EA-113`, `R1EA-114`, and `R1EA-120` through `R1EA-123`;
  `R1EA-097` through `R1EA-100`;
  `R1EA-101`, `R1EA-102`, `R1EA-105`, `R1EA-106`,
  `R1EA-109`, `R1EA-111`, and `R1EA-112`;
  `R1EA-056` through `R1EA-063`; and
  `R1EA-045`, `R1EA-046`, `R1EA-051`, `R1EA-054`, and `R1EA-055`.
- Forest-plan support/source-truth additions now own the remaining
  `R1PLAN-*` support rows in
  `region1_forest_plan_source_records`:
  `R1PLAN-beaverhead-deerlodge-nf-01`,
  `R1PLAN-bitterroot-nf-01`,
  `R1PLAN-custer-gallatin-nf-01`,
  `R1PLAN-dakota-prairie-grasslands-01`,
  `R1PLAN-flathead-nf-01`,
  `R1PLAN-helena-lewis-and-clark-nf-01`,
  `R1PLAN-idaho-panhandle-nfs-01`,
  `R1PLAN-kootenai-nf-01`,
  `R1PLAN-lolo-nf-01`,
  `R1PLAN-nez-perce-clearwater-nfs-01`,
  `R1PLAN-nez-perce-clearwater-nfs-02`, and
  `R1PLAN-region-1-northern-region-02`.
  The next repair surface for that class is
  `config/r1_forest_plan_document_register_draft.csv` plus the governed
  forest-plan source-truth admission owner.
- Base-rule current-source decisions now stay owned by
  `config/compliance_rule_pack_nepa_ea_v0.json` for
  `R1EA-020`, `R1EA-021`, `R1EA-027`, `R1EA-033`, and `R1EA-034`.
  `config/compliance_source_record_reconciliation_v1.json` already records
  empty `current_source_record_ids` for all five, and only `R1EA-034`
  currently has an admitted broad replacement candidate in the active catalog
  (`LEX-FED-008`).
- The exact next repair surfaces are now explicit:
  template retire/replace work in
  `config/authority_family_rule_templates_nepa_ea_v1.json`,
  current-source additions through the governed workbook/current-catalog owner,
  forest-plan support additions through
  `config/r1_forest_plan_document_register_draft.csv`, and
  base-rule replacement or retirement in
  `config/compliance_rule_pack_nepa_ea_v0.json`.
- The historical next truthful slice at this owner-map checkpoint was
  Milestone `2` in this same packet: land the governed template, source-truth,
  and rule-pack repairs while preserving the failing applicability gates. The
  live route after the later Milestone `2` reduction is recorded in the newer
  reduction note below.

### Milestone 2 - Governed Source-Truth Repair

Outcome label: reduced

Purpose: land the chosen source-truth, template, or rule-pack repairs without
weakening the applicability gates.

Implementation:

1. Add, replace, or retire the remaining references only through their governed
   owners.
2. Add or update focused tests and docs for the chosen repair.
3. Re-run ECID `applicability-authority-universe` until validation passes.

Acceptance criteria:

- `applicability-authority-universe` passes for ECID on
  the active current-source-gap replay gate.
- No new skips, xfails, or relaxed checks are introduced.

Milestone 2 reduction on 2026-05-25:

- `config/compliance_source_record_reconciliation_v1.json` now binds admitted
  current catalog replacements for the template-owned legacy rows in
  `grassland_bankhead_jones_authorities`,
  `roads_access_special_use_action_authorities`,
  `species_supporting_sources_and_overlays`,
  `land_exchange_regulatory_requirements`,
  `land_exchange_statutory_authorities`, and the non-retired handbook/policy
  rows in `land_exchange_fs_policy_and_project_references`.
- `config/authority_family_rule_templates_nepa_ea_v1.json`,
  `config/compliance_rule_pack_nepa_ea_v0.json`,
  `config/authority_family_rule_template_coverage_nepa_ea_v1.json`, and
  `config/authority_universe_families_nepa_ea_v1.json` now retire
  `R1EA-160`, `R1EA-161`, and `R1EA-162` into the excluded non-controlling
  mapping class while preserving governed family membership for workbook
  traceability.
- The governed land-exchange retirement closeout now moves `R1EA-160`,
  `R1EA-161`, and `R1EA-162` into the excluded non-controlling mapping class
  for `land_exchange_fs_policy_and_project_references`. The land-exchange
  template no longer appears in the missing-template inventory.
- The governed `R1EA-093` current-source addition lane is now closed: the
  canonical workbook admits `FED-044` (`General Conformity`, `40 CFR part 93
  subpart B`), `config/compliance_source_record_reconciliation_v1.json` now
  maps `R1EA-093` to that current row, and the earlier same-slice scoped
  catalog gate at
  `source_library/runs/current-source-gap-fed-044-catalog-gate/catalog_gate`
  proved `source-set-583e2d0ca9c793f6` with `648` source rows, `636`
  artifacts, and `595` admitted active-current rows.
- The governed water-family current-source addition lane is now also closed:
  the canonical workbook admits `FED-045` through `FED-051` plus `STP-031`
  through `STP-034`,
  `config/compliance_source_record_reconciliation_v1.json` now maps
  `R1EA-083` through `R1EA-090` and `R1EA-115` through `R1EA-118` to those
  current rows, and a same-slice scoped catalog gate at
  `source_library/runs/current-source-gap-clean-water-catalog-gate/catalog_gate`
  now proves `source-set-d5c008d39a65eb11` with `659` source rows, `647`
  artifacts, and `606` admitted active-current rows.
- The governed cultural-resource/state-SHPO and shared tribal-overlap
  current-source addition lanes are now also closed: the canonical workbook
  admits `FED-052` through `FED-059` plus `STP-035`,
  `config/compliance_source_record_reconciliation_v1.json` now maps
  `R1EA-072`, `R1EA-074`, `R1EA-076` through `R1EA-080`,
  `R1EA-113`, `R1EA-114`, and `R1EA-120` through `R1EA-123` to those current
  rows, and a same-slice scoped catalog gate at
  `source_library/runs/current-source-gap-cultural-catalog-gate/catalog_gate`
  now proves `source-set-0de012afc6fc589c` with `668` source rows, `656`
  artifacts, and `615` admitted active-current rows.
- The governed wildlife current-source addition lane is now also closed: the
  canonical workbook admits `FED-060` through `FED-062`,
  `config/compliance_source_record_reconciliation_v1.json` now maps
  `R1EA-097` through `R1EA-100` to those current rows, and a same-slice
  scoped catalog gate at
  `source_library/runs/current-source-gap-wildlife-catalog-gate/catalog_gate`
  now proves `source-set-d5243d000edd5bf9` with `671` source rows, `659`
  artifacts, and `618` admitted active-current rows.
- The governed hazardous-material current-source addition lane is now also
  closed: the canonical workbook admits `FED-063`
  (`National Contingency Plan, 40 CFR part 300`),
  `config/compliance_source_record_reconciliation_v1.json` now maps
  `R1EA-109` to that current row, and a same-slice scoped catalog gate at
  `source_library/runs/current-source-gap-hazardous-catalog-gate/catalog_gate`
  now proves `source-set-87f6d2c309e0c88b` with `672` source rows, `660`
  artifacts, and `619` admitted active-current rows.
- The governed invasive/farmland/drinking-water current-source addition lane
  is now also closed: the canonical workbook admits `FED-064` through
  `FED-069`,
  `config/compliance_source_record_reconciliation_v1.json` now maps
  `R1EA-101`, `R1EA-102`, `R1EA-105`, `R1EA-106`, `R1EA-111`, and
  `R1EA-112` to those current rows, and a same-slice scoped catalog gate at
  `source_library/runs/current-source-gap-invasive-catalog-gate/catalog_gate`
  now proves `source-set-ef887e7bfb6fa76f` with `678` source rows, `666`
  artifacts, and `625` admitted active-current rows.
- The governed forest-plan support admission lane is now also closed: the
  canonical workbook admits the `12` missing `R1PLAN-*` planning/index pages,
  and a same-slice scoped catalog gate at
  `source_library/runs/current-source-gap-forest-plan-support-catalog-gate/catalog_gate`
  now proves `source-set-1cbc5bbb602b60bc` with `691` source rows, `679`
  artifacts, and `638` admitted active-current rows.
- The governed vegetation/fire current-source addition lane is now also
  closed: the canonical workbook admits `FED-071` through `FED-077`,
  `config/compliance_source_record_reconciliation_v1.json` now maps
  `R1EA-056` through `R1EA-062` to those current rows, and a same-slice
  scoped catalog gate at
  `source_library/runs/current-source-gap-vegetation-catalog-gate/catalog_gate`
  now proves `source-set-e57ea1d39b859bc8` with `698` source rows, `686`
  artifacts, and `645` admitted active-current rows.
- The governed wilderness/designated-area and five base-rule current-source
  addition lane is now also closed: the canonical workbook admits `FED-078`
  through `FED-087`,
  `config/compliance_source_record_reconciliation_v1.json` now maps
  `R1EA-020`, `R1EA-021`, `R1EA-027`, `R1EA-033`, `R1EA-034`,
  `R1EA-045`, `R1EA-046`, `R1EA-051`, `R1EA-054`, and `R1EA-055` to those
  current rows, and a same-slice scoped catalog gate at
  `source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate`
  now proves `source-set-f70ea11e04ae3d53` with `708` source rows, `696`
  artifacts, and `655` admitted active-current rows.
- On that scoped gate, `candidates_have_source_evidence_available` now passes
  with `failure_count=0` and
  `authority_family_template_candidates_cover_config` now passes with
  `missing_source_record_count=0`.
- The live ECID replay still remains red, but only on
  `rule_template_candidates_have_source_claim_linkage`
  (`failure_count=48`) because the scoped gate has no
  extraction/retrieval/claim/rule-claim derived artifacts yet and therefore
  records `rule_claim_links_path=null`.
- Milestone `2` therefore exhausts the source-truth owner inventory even
  though the broader applicability replay does not yet pass. The remaining
  blocker is replay-local rather than workbook/current-source truth.

### Milestone 3 - Replay Resume Handoff

Outcome label: resolved

Purpose: return control to the replay-repair packet only after the
current-source blocker is actually cleared.

Implementation:

1. Update routing docs so
   `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` becomes the
   active packet again once the governed current-source inventory is closed and
   any remaining red checks fall outside this packet's owner boundary.
2. Record the exact replay-resume command chain for the next packet.
3. Close this blocker packet with one local atomic commit.

Acceptance criteria:

- The replay-repair packet is routed live again only after the current-source
  inventory is honestly cleared and the remaining blocker is no longer
  source-truth owned.
- The docs name the exact resume commands and the post-clear owner boundary.

## Required Implementation Artifacts

- Current-source truth changes in the workbook or governed source config
- Any matching template/rule-pack replacements or retirement notes
- Focused tests proving the repaired current rows or governed retirements
- Updated blocker packet(s), routing docs, and handoff

## Required Documentation And Handoff Updates

- `README.md`
- `docs/POST_V1_PROMOTION_SUITE.md`
- `docs/CURRENT_ROUTING.md`
- `docs/CURRENT_SYSTEM_STATE.md`
- `docs/SESSION_HANDOFF.md`
- this plan
- the upstream blocker packet that handed work here
- the blocked replay-repair packet, if the active route changes

## Required Verification Gates

```bash
PYTHONPATH=src .venv/bin/python -m pytest \
  tests/test_source_register_loader.py \
  tests/test_source_register_schema.py \
  tests/test_catalog.py \
  tests/test_dry_run.py \
  tests/test_preflight.py \
  tests/test_applicability_authority_family_templates.py \
  tests/test_authority_family_rule_templates.py \
  tests/test_authority_universe_inventory.py \
  tests/test_rule_claim_binding_runtime.py \
  tests/test_architecture_contract.py -q

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources source-register-validate \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx

PYTHONPATH=src .venv/bin/python -m ruff check \
  tests/test_source_register_loader.py \
  tests/test_source_register_schema.py \
  tests/test_catalog.py \
  tests/test_dry_run.py \
  tests/test_preflight.py \
  tests/test_applicability_authority_family_templates.py \
  tests/test_authority_family_rule_templates.py \
  tests/test_authority_universe_inventory.py

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources download \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --config config/downloader.toml \
  --run-id queue-m3-full-canonical-merged-download-20260525-current-gap-closeout

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx \
  --output-dir source_library \
  --config config/downloader.toml \
  --run-id queue-m3-full-canonical-merged-download-20260525-current-gap-closeout \
  --catalog-dir source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate

PYTHONPATH=src .venv/bin/python -m usfs_r1_ea_sources applicability-authority-universe \
  --output-dir source_library \
  --review-id v1-cg-ecid-compliance-review \
  --catalog-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_catalog.jsonl \
  --source-set-manifest-path source_library/runs/current-source-gap-closeout-catalog-gate/catalog_gate/source_set_manifest.json

jq empty \
  config/compliance_source_record_reconciliation_v1.json
git diff --check
```

## Acceptance Criteria

- Remaining blocker claims are backed by the live
  `authority_universe_snapshot.json`, not by stale chat context.
- No new current-source mapping is added without active-catalog or same-slice
  governed source-truth evidence.
- No stale authority reference is removed without a documented replacement or
  explicit retirement owner.
- The replay-repair packet stays blocked only while the remaining blocker is
  still source-truth owned; once the current-source inventory is honestly
  clear, any remaining replay-local failure must route back upstream instead of
  being misclassified as another workbook gap.

## Stop Conditions

- Stop if a remaining gap requires adding or changing current workbook/catalog
  rows outside this packet's governed owner surfaces.
- Stop if closing a remaining gap would require weakening applicability
  validation.
- Stop if a proposed reconciliation row has no active catalog or same-slice
  workbook/source-truth proof.

## Local Commit Closeout Policy

- Close each milestone with one local atomic commit after verification passes.
- Stage only the verified milestone slice: code/config/tests/docs/handoff that
  belong to this packet.
- Do not stage ignored `source_library/` outputs.

## Residual Risks And Next Milestone Routing

- Residual risk: the scoped closeout gate still lacks
  extraction/retrieval/claim/rule-claim derived artifacts, so a future agent
  could mistake the remaining replay-local linkage failure for another
  source-truth miss.
- Next truthful slice: return to
  `docs/REAL_PACKAGE_REVIEW_REPLAY_REPAIR_MILESTONE_PLAN.md` on scoped gate
  `source-set-f70ea11e04ae3d53`. Reuse or rebuild the required
  extraction/retrieval artifacts, then run `claim-extract`, then
  `rule-claim-link`, then rerun
  `applicability-authority-universe --review-id v1-cg-ecid-compliance-review`
  before resuming broader ECID reviewer-ready replay repair.
