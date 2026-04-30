# USFS Region 1 EA Sources

Local source-library project for USDA Forest Service Region 1 Environmental Assessment review sources.

The workbook is the source-of-truth input. The first implementation milestone is a dry-run manifest generator that proves row counts, exclusions, duplicate URL handling, planned artifact paths, and output schemas before any network downloader is built.

## Current Inputs

- `usfs_region1_ea_document_checklist_current_2026.xlsx`
- `DOWNLOADER_RULES.md`
- `config/downloader.toml`

## Expected Workflow

```bash
python -m usfs_r1_ea_sources dry-run \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library
```

The dry run writes:

```text
source_library/
  manifests/
    dry_run_<run_id>.jsonl
  runs/
    <run_id>/
      events.jsonl
      summary.json
      validation_report.json
      failures.csv
```

Generated `source_library` artifacts, run logs, and JSONL manifests are ignored by git by default.

After the dry-run contract passes, use preflight to check URL reachability without saving source artifacts:

```bash
python -m usfs_r1_ea_sources preflight \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --limit 10
```

Preflight records HTTP status, final URL, redirect chain, content type, content length, challenge-page detection, and failure status for each workbook row while fetching each unique URL only once.

After preflight results are acceptable, download raw artifacts:

```bash
python -m usfs_r1_ea_sources download \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --limit 5
```

The downloader saves immutable raw artifacts under `source_library/artifacts/raw/`, computes SHA256 hashes, reuses existing artifacts on resume, and writes a row-level manifest for every workbook source row.

Build an operator report for any run:

```bash
python -m usfs_r1_ea_sources report \
  --output-dir source_library \
  --run-id pilot-core-sources
```

The report writes `source_library/runs/<run_id>/operator_report.md` and lists status counts, host counts, adapter usage, and rows that need manual URL repair.

Before scaling a pilot into a full download, run the acceptance gate:

```bash
python -m usfs_r1_ea_sources validate-run \
  --output-dir source_library \
  --run-id pilot-core-sources-adapted
```

The gate writes `source_library/runs/<run_id>/acceptance_gate.json` and exits nonzero if artifact hashes, byte sizes, duplicate links, status counts, exclusion safety, or repair-queue coverage fail.

Run staged host pilots before the full download:

```bash
python -m usfs_r1_ea_sources pilot-hosts \
  --workbook usfs_region1_ea_document_checklist_current_2026.xlsx \
  --output-dir source_library \
  --run-id-prefix staged-pilot \
  --host www.ecfr.gov \
  --host uscode.house.gov
```

Each host pilot runs `download`, `report`, and `validate-run`. The command writes a parent summary under `source_library/runs/<run-id-prefix>-host-pilots/` and exits nonzero if any selected host has failed rows or a failed acceptance gate.

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

The downloader should not perform network downloads until the dry-run manifest and tests pass.
