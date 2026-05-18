# Canonical Source Register Workbook Audit

Date: 2026-05-18

This audit freezes the delivered workbook
`usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` as the canonical
replacement candidate for the legacy Region 1 workbook contract. It records the
workbook identity, the frozen load-table and row-state contracts, the
legacy-to-canonical migration baseline, and the governed adjunct contracts that
must exist before runtime cutover.

## Workbook Identity

- repo workbook path:
  `usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx`
- workbook SHA256:
  `46006b05052e90abdc80f8d23e074f1b4649eecb603de7479ddc7d250a462f7e`
- sheet count: `13`
- canonical load sheet: `Document_Register_Master`
- deferred queue sheet: `Direct_File_Capture_Queue`
- removed-not-applicable sheet: `Removed_Not_Applicable_Final`

Frozen sheet contract and row-state contract live at:

- `config/source_register_sheet_contract_v1.json`
- `config/source_register_schema_v1.json`
- `config/source_register_vocabularies_v1.json`
- `config/source_register_row_states_v1.json`
- `config/direct_file_readiness_contract_v1.json`
- `config/parser_admission_contract_v1.json`

## Frozen Workbook Facts

`source-register-validate` on the staged workbook currently proves:

- `635` retained load-ready rows in `Document_Register_Master`
- `51` deferred queue rows in `Direct_File_Capture_Queue`
- `2` removed-not-applicable rows in `Removed_Not_Applicable_Final`
- `5` `Applicable - stale-source detector only` rows
- `29` direct-media reclassifications from manual-export priority to direct
  extraction
- zero duplicate `Source_ID` values in the master load table
- zero duplicate `Source_URL` values in the master load table
- zero blank or non-HTTP(S) master URLs
- `635` explicit `EA_System_Applicability_Status` values on retained load rows

The retained master applicability distribution is:

- `238` `Applicable - forest/grassland plan-specific`
- `208` `Applicable - species/ESA/wildlife trigger`
- `50` `Applicable - land exchange trigger`
- `31` `Applicable - federal resource/trigger authority`
- `30` `Applicable - state/partner data or permit source`
- `29` `Applicable - Region 1 resource guidance/order`
- `24` `Applicable - USFS directive/source-control`
- `11` `Applicable - USDA cross-cutting EA source`
- `6` `Applicable - core federal EA authority`
- `5` `Applicable - stale-source detector only`
- `2` `Applicable - USFS resource directive`
- `1` `Applicable - programmatic/tiering or consultation source`

The deferred queue is governed, not incidental. The dominant queue classes are:

- `21` `Folder/listing/manual-export placeholder`
- `10` `Forest plan support row needs direct document file URL`
- `4` `Manual/project-record placeholder`
- `4` `Placeholder row`
- `3` `Specific FEIS volume listed on official page but direct file URL unresolved`

## Legacy-To-Canonical Migration Baseline

`source-register-diff` currently records the runtime replacement baseline as:

- legacy workbook selected rows: `190`
- promoted source-delta rows: `160`
- documented official-source gaps: `1`
- legacy runtime unique source rows after workbook plus source-delta merge:
  `350`
- canonical retained master rows: `635`
- canonical deferred queue rows: `51`
- canonical removed rows: `2`
- canonical shared `Source_ID` values with the legacy workbook: `0`
- canonical shared `Source_ID` values with the promoted source-delta register:
  `0`
- canonical-only retained master rows: `635`
- legacy-only runtime rows: `350`

This is therefore a source-contract replacement, not an incremental merge of
shared row identities. The new workbook introduces a fully new `Source_ID`
universe starting at `FED-*`, while the live runtime still operates on the
older `R1EA-*` plus `R1PLAN-*` identity families.

## Legacy Baseline Lock

The repo must distinguish inherited green surfaces from inherited red surfaces
before any canonical ingestion run is allowed to replace the active workbook.
The current baseline lock is:

- inherited green surface:
  `source_library/reviews/promotion_suite/post-v1-region1-ea-promotion-suite/promotion_suite_results.json`
  reports `current_promotion_ready=true`, `full_canonical_corpus_ready=true`,
  `expansion_ready=true`, and `promotion_ready=true`
- inherited red surface:
  `source_library/derived/source-set-5e65d845ce77e1a0/evidence_graph/phase_eval_results.json`
  reports `reviewer_ready=false`, `passed_phase_count=9`, `phase_count=12`,
  and `threshold_failed_phase_count=1`
- active catalog baseline:
  `source_library/catalog/source_set_manifest.json` remains
  `source-set-5e65d845ce77e1a0` with `350` source rows and `319` artifacts

Any new canonical-register run must compare against this locked mixed baseline
rather than retroactively treating inherited legacy red or green results as
proof of canonical-register behavior.

## Workbook Contract Versus Adjunct Semantic Contracts

The workbook now directly carries:

- source-row identity via `Source_ID`
- authority tier, sub-tier, and issuing-entity metadata
- jurisdiction or unit labels
- resource-area labels
- document type, title, and citation text
- currentness-status labels
- applicability-status and applicability-scope labels
- load versus queue versus removed row-state signals
- source URL, URL class, validation status, and ingest action

The workbook does not by itself carry normalized semantic graph identity for
review-time reasoning. Those seams remain governed adjunct contracts:

- authority ontology:
  `config/authority_document_ontology_v1.json`
- relationship vocabulary and starter path patterns:
  `config/authority_relationship_types_v1.json`
- relationship register activation boundary:
  `config/authority_relationship_register_v1.json`
- citation and alias normalization:
  `config/citation_alias_register_v1.json`
- jurisdiction and scope register:
  `config/jurisdiction_scope_register_v1.json`
- ontology and relationship eval manifests:
  `config/authority_ontology_eval_v1.json`,
  `config/authority_relationship_eval_v1.json`

The adjunct contracts are currently explicit and verified as starter baselines,
but they are intentionally not yet populated with runtime rows beyond governed
starter examples. That is acceptable for Phase 0 because the refoundation goal
here is to make the contracts explicit before loader/capture migration, not to
pretend that semantic identity population is already complete.

## Pre-Ingestion Contract Packet

The repo now has the minimum governed packet required before Phase 1 loader
replacement and Phase 1.5 proving-slice work:

- sheet roster, load-table boundary, header-row positions, and count
  reconciliation:
  `config/source_register_sheet_contract_v1.json`
- required fields, uniqueness, and controlled-vocabulary checks:
  `config/source_register_schema_v1.json`
- authority-tier, applicability-status, and row-state vocabularies:
  `config/source_register_vocabularies_v1.json`,
  `config/source_register_row_states_v1.json`
- direct-file readiness classes and deferred-queue resolution patterns:
  `config/direct_file_readiness_contract_v1.json`
- starter parser admission classes:
  `config/parser_admission_contract_v1.json`
- semantic ontology, relationship, alias, and scope starter baselines:
  `config/authority_document_ontology_v1.json`,
  `config/authority_relationship_types_v1.json`,
  `config/authority_relationship_register_v1.json`,
  `config/citation_alias_register_v1.json`,
  `config/jurisdiction_scope_register_v1.json`
- executable contract commands:
  `source-register-validate`,
  `source-register-diff`

The packet is sufficient to prevent hidden manual judgment about:

- which sheet is load-bearing
- which rows are retained, deferred, or removed
- which vocabularies are legal
- which queue rows remain placeholders
- which parser classes are currently admitted
- which semantic seams must stay outside raw workbook rows

## Verification

The current audit is backed by:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_cli.py tests/test_architecture_contract.py tests/test_authority_ontology_starter.py -q
```

## Next Routing

Phase 0 workbook freeze is now explicit enough to permit the next refoundation
step: Phase 1 foundation refactor to a canonical register loader. Runtime
cutover is still blocked until that loader exists and the Phase 1.5 proving
slice passes.
