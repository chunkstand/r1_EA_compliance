# Region 1 Forest-Plan Document Register Promotion Report

Date: 2026-05-10

## Scope

This slice promotes `config/r1_forest_plan_document_register_draft.csv` from a reviewed draft
register into an explicit supplemental source-delta input for the existing capture pipeline.

The promotion is controlled:

- `source_delta_required` rows emit supplemental `WorkbookSource` records.
- `catalog_confirmed` rows remain documented in the register but are not re-emitted because their
  source record IDs already exist in the workbook/catalog contract.
- `official_source_gap_documented` rows are counted as skipped gaps and are not planned for corpus
  download.
- No broad workbook or canonical corpus redownload was run in this slice.

## Register Acceptance

- Register rows: `189`
- Catalog-confirmed rows: `28`
- Corpus-ready source-delta rows: `159`
- Skipped official-source gaps: `2`
- Duplicate emitted source IDs: `0`
- Source-delta rows overlapping current workbook source IDs: `0`

Skipped gap source IDs:

- `R1PLAN-kootenai-nf-18`
- `R1PLAN-nez-perce-clearwater-nfs-18`

## Generated Validation Runs

Dry-run:

- Run ID: `r1-forest-plan-promotion-dry-run-20260510`
- Manifest: `source_library/manifests/dry_run_r1-forest-plan-promotion-dry-run-20260510.jsonl`
- Filtered rows: `159`
- Planned rows: `159`
- Duplicate URL rows: `0`
- Skipped exclusions: `0`
- Validation: passed

Scoped live preflight:

- Run ID: `r1-forest-plan-promotion-preflight-20260510`
- Manifest: `source_library/manifests/preflight_r1-forest-plan-promotion-preflight-20260510.jsonl`
- Filtered rows: `159`
- Checked URLs: `159`
- `preflight_ok`: `158`
- `rate_limited`: `1`
- Rate-limited row: `R1PLAN-dakota-prairie-grasslands-19`
- Validation report: passed

Targeted retry:

- Run ID: `r1-forest-plan-promotion-preflight-retry-dpg19-20260510`
- Checked URLs: `1`
- `preflight_ok`: `1`
- Failed rows: `0`

Plan-only batch smoke:

- Parent run ID: `r1-forest-plan-source-delta-capture-plan-20260510-batches`
- Planned rows: `159`
- Planned batches: `33`
- Host split: `139` `www.fs.usda.gov`, `18` `usfs-public.app.box.com`, and `2`
  `federalregister.gov`
- Supplemental source count: `159`
- Source-record filter count: `159`
- Downloads executed: `0`

Controlled source-delta capture:

- Parent run ID: `r1-forest-plan-source-delta-capture-20260510-batches`
- Planned rows: `159`
- Passed batches: `33/33`
- Repair queue: empty except header
- Unique artifacts: `158`
- Batch status counts: `passed=33`

Scoped source-delta catalog gate:

- Source set ID: `source-set-411b3736b3691eed`
- Batch run ID: `r1-forest-plan-source-delta-capture-20260510-batches`
- Archived catalog gate path:
  `source_library/runs/r1-forest-plan-source-delta-capture-20260510-batches/catalog_gate/`
- Source rows: `159`
- Artifact count: `158`
- Source statuses: `downloaded=158`, `duplicate_content=1`
- Document roles: `forest_plan_support=159`
- Source partitions: `active_review_corpus=159`
- Catalog validation: passed

After the scoped source-delta catalog gate was archived, `source_library/catalog/` was restored to
the canonical 190-row workbook catalog from `corpus-update-2026-05-01-cg-support-batches` so the
captured-library integrity gate continues to validate the canonical catalog view.

## Gap Closure

The promotion gap-close slice extends `batch-download` to accept the same
`--r1-forest-plan-register ... --source-delta-only` contract as `dry-run`, `preflight`, and
`download`. Parent batch plans and summaries now record `source_delta_input`,
`supplemental_source_count`, and `source_record_id_filter_count`, and child download runs receive
the supplemental `WorkbookSource` records needed to resolve the emitted `R1PLAN-*` source-delta
IDs.

The capture execution slice extends `catalog-build` to accept the same register contract. Scoped
catalog builds now validate promoted `R1PLAN-*` source-delta manifests against supplemental
`R1_Forest_Plan_Document_Register` rows instead of weakening unknown-source checks.

Full repository verification passed after removing a domain-specific token from the general
evidence-graph runtime while preserving the existing knowledge-graph artifact filenames.

## Promotion Boundary

The register has completed controlled source-delta capture and scoped catalog validation. The next
slice should build extraction/retrieval readiness for the `159` captured support-document rows while
preserving the two gap rows as non-corpus-ready until replacement official sources are acquired or a
documented gap policy is accepted.
