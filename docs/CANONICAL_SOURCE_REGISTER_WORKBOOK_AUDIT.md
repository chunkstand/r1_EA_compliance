# Canonical Source Register Workbook Audit

Date: 2026-05-18

This audit freezes the delivered workbook
`usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx` as the canonical
replacement candidate for the legacy Region 1 workbook contract. It records the
workbook identity, the frozen load-table and row-state contracts, the
legacy-to-canonical migration baseline, and the governed adjunct contracts that
must exist before and after runtime cutover.

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

## Phase 2 Capture And Catalog Status

The Phase 2 capture/catalog cutover is now live:

- `config/downloader.toml` is now pinned to `loader_contract = "source_register_v1"`
- active `dry-run`, `preflight`, `download`, `batch-download`, and
  `catalog-build` calls now consume `Document_Register_Master`
- active `source_register_v1` runs reject the legacy
  `--r1-forest-plan-register` supplemental lane so the canonical workbook
  remains the sole active source ledger
- the legacy `config/url_overrides.toml` registry is now a `legacy_v0`
  comparison surface only; canonical rows must carry the active official URL
  directly in the workbook
- the first isolated canonical catalog gate now lives at
  `source_library/runs/canonical-source-register-phase2-catalog-gate-20260518/catalog_gate/`
  as `source-set-ae989382c52344db` with `635` planned rows, `635` unique URLs,
  and `catalog_validation.json` passing
- the upstream direct-eval aggregate now requires `12` categories and `24`
  cases, including `canonical_source_delta_reintroduction_blocked`, and the
  live replay passes `24/24`

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

## Phase 1 Foundation Loader Status

The repo now also ships a canonical loader path for this packet:

- `WorkbookConfig.loader_contract` is now explicit, with active runtime config
  still pinned to `legacy_v0`
- `load_canonical_sources(...)` now dispatches by loader contract instead of
  assuming the legacy workbook is the only workbook shape
- `load_source_register_rows(...)` now emits a normalized canonical row object
  carrying:
  `authority_document_id`,
  `authority_document_class_id`,
  `authority_section_id`,
  `jurisdiction_scope_id`,
  `source_authority_link_id`,
  `direct_file_readiness_class`,
  `parser_route_id`,
  `parser_admission_class`, and
  `expected_parser`
- the canonical loader rejects blocked alias terms without enough identity
  context and uses the staged alias/scope contracts as explicit seams instead
  of hiding those decisions in the old workbook parser
- `load_source_register_workbook_sources(...)` provides the narrow compatibility
  seam back to `WorkbookSource` so downstream capture and catalog callers can
  migrate later without a broad rewrite in the same checkpoint

This closes the Phase 1 foundation boundary and is now followed by the live
Phase 2 runtime cutover described above.

## Phase 1.5 Proving Slice Status

The repo now also ships the executable proving packet that the audit called for
before any canonical capture/catalog cutover:

- `config/source_register_proving_slice_v1.json` defines the active mixed
  proving slice: `26` load-ready canonical rows plus `5` deferred queue rows
- `source-register-proving-slice` now materializes the scoped proving catalog,
  currentness inputs, semantic relationships, alias report, graph summary, and
  justification-path export under
  `source_library/derived/<source_set_id>/source_register_proving/`
- `source_library/derived/source_register_proving/latest_context.json` now
  records the latest proving source set, report path, and currentness inputs
- `authority-relationship-eval`, `citation-alias-eval`, `graph-health-eval`,
  and `graph-accuracy-eval` are now implemented as first-class proving gates
- `config/graph_health_contract_v1.json` and
  `config/graph_accuracy_eval_v1.json` now hold the starter graph-health and
  graph-accuracy contracts for this checkpoint

The proving packet remains a hard gate even after runtime cutover. Full
downloaded canonical-corpus promotion is still blocked until the later
currentness, extraction, and downstream rebase packets are complete.

## Verification

The current audit is backed by:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-validate --workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src python -m usfs_r1_ea_sources source-register-diff --legacy-workbook usfs_region1_ea_document_checklist_land_exchange_review_2026.xlsx --legacy-register config/r1_forest_plan_document_register_draft.csv --canonical-workbook usfs_region1_ea_source_register_FINAL_INGEST_READY_2026.xlsx
PYTHONPATH=src uv run --extra dev pytest tests/test_source_register_schema.py tests/test_cli.py tests/test_architecture_contract.py tests/test_authority_ontology_starter.py -q
```

## Next Routing

Phases 0, 1, 1.5, and 2 are now explicit enough to permit the next
refoundation step: Phase 3 authority-currentness, supersession, and
source-partition rebase on top of the canonical register. Bulk canonical
ingestion still may not bypass the proving gate.
