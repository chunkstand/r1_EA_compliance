# USFS Region 1 EA Sources

Local source-library project for USDA Forest Service Region 1 Environmental Assessment review sources.

The workbook is the source-of-truth input. The system now captures the full canonical workbook source set into a local, auditable source library for a downstream EA review engine. It stores immutable raw artifacts, row-level provenance manifests, batch evidence, a reviewer-facing catalog, a SQLite index, and graph seed files.

Current full-library capture:

- Run ID: `full-library-batches`
- Workbook rows covered: `147`
- Batch result: `28/28` batches passed
- Repair queue: empty except header
- Unique workbook/effective URLs: `144`
- Unique raw artifacts in reviewer catalog: `131`
- Source-to-artifact links: `147`

See `docs/CURRENT_SYSTEM_STATE.md` for the current architecture, storage model, and reviewer-engine read path.

## Current Inputs

- `usfs_region1_ea_document_checklist_current_2026.xlsx`
- `DOWNLOADER_RULES.md`
- `config/downloader.toml`
- `config/url_overrides.toml`

## Stored Data

Generated outputs are written under `source_library/` and ignored by git:

- Raw downloaded artifacts: `source_library/artifacts/raw/`
- Row manifests: `source_library/manifests/download_<run_id>.jsonl`
- Batch ledgers and reports: `source_library/runs/<run_id>/`
- Reviewer catalog: `source_library/catalog/source_catalog.jsonl`
- Reviewer SQLite index: `source_library/catalog/review_sources.sqlite`
- Source-set manifest: `source_library/catalog/source_set_manifest.json`
- Graph seed files:
  - `source_library/catalog/source_graph_nodes.jsonl`
  - `source_library/catalog/source_graph_edges.jsonl`

The raw artifacts are not semantic chunks. They are source bytes plus provenance. Chunking, text extraction, embeddings, and claim/section graphs should be built downstream from the catalog and artifacts.

## Reviewer Engine Entry Points

The EA review engine should start from one of these catalog surfaces rather than scanning filenames:

- `source_library/catalog/review_sources.sqlite`
- `source_library/catalog/source_catalog.jsonl`
- `source_library/catalog/source_set_manifest.json`

For each selected source row, the engine should:

1. Read the source metadata from SQLite or `source_catalog.jsonl`.
2. Open `artifact_path`.
3. Recompute SHA256 and byte size before parsing.
4. Choose a parser using `expected_parser` and `content_type`.
5. Attach `source_record_id`, `artifact_sha256`, `citation_label`, URL provenance, and page/section offsets to every extracted chunk.

The graph JSONL files are source metadata graph seeds only. They link sources to artifacts, authorities, review topics, applicability, and related reviewer concepts. They do not yet contain semantic document chunks, extracted claims, or content-level citations.

## Common Commands

Dry-run workbook parsing without network access:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources dry-run \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library
```

Preflight URL reachability without saving artifacts:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --limit 10
```

Preflight records HTTP status, final URL, redirect chain, content type, content length, challenge-page detection, and failure status for each workbook row while fetching each unique URL only once.

Download a small controlled slice:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources download \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --limit 5
```

The downloader saves immutable raw artifacts under `source_library/artifacts/raw/`, computes SHA256 hashes, reuses existing artifacts on resume, and writes a row-level manifest for every workbook source row.

Build an operator report for any run:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources report \
  --output-dir source_library \
  --run-id pilot-core-sources
```

The report writes `source_library/runs/<run_id>/operator_report.md` and lists status counts, host counts, adapter usage, and rows that need manual URL repair.

Before scaling a pilot into a full download, run the acceptance gate:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources validate-run \
  --output-dir source_library \
  --run-id pilot-core-sources-adapted
```

The gate writes `source_library/runs/<run_id>/acceptance_gate.json` and exits nonzero if artifact hashes, byte sizes, duplicate links, status counts, exclusion safety, or repair-queue coverage fail.

Run staged host pilots before the full download:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources pilot-hosts \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix staged-pilot \
  --host www.ecfr.gov \
  --host uscode.house.gov
```

Each host pilot runs `download`, `report`, and `validate-run`. The command writes a parent summary under `source_library/runs/<run-id-prefix>-host-pilots/` and exits nonzero if any selected host has failed rows or a failed acceptance gate.

Plan controlled download batches before scaling beyond pilots:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix first-batch \
  --batch-size 5 \
  --limit-per-host 1 \
  --plan-only
```

Remove `--plan-only` to execute the planned batches. Each batch runs `download`, `report`, and `validate-run`, writes a parent `batch_plan.json`, `batch_ledger.json`, and `repair_queue.csv`, then stops on the first failed or repair-needed batch unless `--continue-on-failure` is passed.
Use `--resume` to skip already passed batches under the same run prefix.

Run or refresh the full captured library:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources batch-download \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix full-library \
  --batch-size 10 \
  --continue-on-failure
```

Build the reviewer-engine catalog from the full batch:

```bash
PYTHONPATH=src python -m usfs_r1_ea_sources catalog-build \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --batch-run-id full-library-batches
```

The catalog command writes `source_library/catalog/source_catalog.jsonl`, `source_set_manifest.json`, `catalog_validation.json`, `review_sources.sqlite`, and graph seed node/edge JSONL.
Pass `--run-id <download-run-id>` after downloads to link artifact hashes, paths, content types, and retrieval timestamps into the same reviewer-facing catalog.
Pass `--batch-run-id <run-id-prefix>-batches` after controlled batch downloads to link artifacts from every passed child batch through the parent batch ledger.

Repair stale or blocked workbook URLs through `config/url_overrides.toml`:

```toml
[[overrides]]
source_record_id = "R1EA-000"
override_url = "https://example.gov/current-official-source"
reason = "Replaces stale workbook URL after manual source verification."
```

Manifests preserve the workbook cell as `original_url` and use `effective_url` for fetching, deduplication, host pilots, and artifact paths.
Overrides must be unique by `source_record_id`, use absolute HTTP(S) URLs with hosts, and avoid workbook scope-exclusion URLs.
Run summaries include `override_count` and `filtered_override_count`, and `validate-run` fails if override provenance or counts drift from the manifest.

## Development

Use the bundled Python runtime or any Python 3.11+ environment with `openpyxl` installed.

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

The captured-library integrity tests validate the current generated `source_library` when present. They check full-batch coverage, manifest-to-ledger consistency, artifact SHA256 and byte sizes, override provenance, catalog linkage, and SQLite/catalog agreement.
