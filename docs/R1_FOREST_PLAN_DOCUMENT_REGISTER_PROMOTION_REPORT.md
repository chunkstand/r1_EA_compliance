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
- No full download was run in this slice.

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

## Gap Closure

The promotion gap-close slice extends `batch-download` to accept the same
`--r1-forest-plan-register ... --source-delta-only` contract as `dry-run`, `preflight`, and
`download`. Parent batch plans and summaries now record `source_delta_input`,
`supplemental_source_count`, and `source_record_id_filter_count`, and child download runs receive
the supplemental `WorkbookSource` records needed to resolve the emitted `R1PLAN-*` source-delta
IDs.

Full repository verification passed after removing a domain-specific token from the general
evidence-graph runtime while preserving the existing knowledge-graph artifact filenames.

## Promotion Boundary

The register is ready for controlled source-delta capture execution. The next slice should run the
planned batch download against only the `159` emitted source-delta rows, preserving the two gap rows
as non-corpus-ready until replacement official sources are acquired or a documented gap policy is
accepted.
