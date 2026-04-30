# Downloader Output Schemas

The downloader writes durable, auditable outputs under `source_library/`.

## Row Manifest JSONL

Path: `source_library/manifests/dry_run_<run_id>.jsonl`

One JSON object per workbook data row.

Required fields:

- `run_id`
- `source_record_id`
- `workbook_path`
- `workbook_sha256`
- `sheet`
- `excel_row`
- `source_id`
- `title`
- `original_url`
- `normalized_url`
- `final_url`
- `redirect_chain`
- `status`
- `artifact_path`
- `artifact_sha256`
- `artifact_byte_size`
- `content_type`
- `fetch_timestamp`
- `validation`
- `duplicate_of`
- `failure`
- `metadata`

For dry runs, network-derived fields are `null` or empty, and `status` is one of `planned`, `duplicate_url`, or `skipped_excluded`.

## Run Summary JSON

Path: `source_library/runs/<run_id>/summary.json`

Required fields:

- `run_id`
- `started_at`
- `completed_at`
- `mode`
- `workbook_path`
- `workbook_sha256`
- `canonical_rows`
- `unique_canonical_urls`
- `excluded_url_count`
- `planned_count`
- `duplicate_url_count`
- `skipped_excluded_count`
- `downloaded_count`
- `failed_count`
- `needs_review_count`
- `status_counts`
- `top_hosts`
- `manifest_path`

## Validation Report JSON

Path: `source_library/runs/<run_id>/validation_report.json`

Required fields:

- `run_id`
- `mode`
- `checks`
- `passed`

Each check includes:

- `name`
- `passed`
- `expected`
- `actual`
- `details`

## Event Log JSONL

Path: `source_library/runs/<run_id>/events.jsonl`

One JSON object per event.

Required fields:

- `run_id`
- `timestamp`
- `event_type`
- `source_record_id`
- `url`
- `host`
- `details`

## Failures CSV

Path: `source_library/runs/<run_id>/failures.csv`

Headers:

- `source_record_id`
- `sheet`
- `excel_row`
- `source_id`
- `title`
- `original_url`
- `status`
- `error_class`
- `error_message`
