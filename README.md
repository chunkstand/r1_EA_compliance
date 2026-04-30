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

## Development

Use the bundled Python runtime or any Python 3.11+ environment with `openpyxl` installed.

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

The downloader should not perform network downloads until the dry-run manifest and tests pass.
