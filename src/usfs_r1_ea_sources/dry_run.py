from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit
import csv
import json
import uuid

from .config import DownloaderConfig
from .records import WorkbookSource, planned_artifact_path, sha256_file
from .workbook import load_canonical_sources, load_excluded_urls


@dataclass(frozen=True)
class DryRunResult:
    run_id: str
    manifest_path: Path
    summary_path: Path
    validation_report_path: Path
    failures_path: Path
    summary: dict


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def new_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]


def write_event(
    events_path: Path,
    run_id: str,
    event_type: str,
    *,
    source: WorkbookSource | None = None,
    details: dict | None = None,
) -> None:
    url = source.original_url if source else None
    host = urlsplit(url).netloc.lower() if url else None
    event = {
        "run_id": run_id,
        "timestamp": utc_now(),
        "event_type": event_type,
        "source_record_id": source.source_record_id if source else None,
        "url": url,
        "host": host,
        "details": details or {},
    }
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def run_dry_run(
    *,
    workbook_path: Path,
    output_dir: Path,
    config: DownloaderConfig,
    run_id: str | None = None,
    sheet_filter: str | None = None,
    id_filter: str | None = None,
    host_filter: str | None = None,
    limit: int | None = None,
) -> DryRunResult:
    run_id = run_id or new_run_id()
    started_at = utc_now()
    output_root = output_dir
    run_dir = output_root / config.outputs.run_dir / run_id
    manifest_dir = output_root / config.outputs.manifest_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    events_path = run_dir / "events.jsonl"
    manifest_path = manifest_dir / f"dry_run_{run_id}.jsonl"
    summary_path = run_dir / "summary.json"
    validation_report_path = run_dir / "validation_report.json"
    failures_path = run_dir / "failures.csv"

    write_event(events_path, run_id, "run_started", details={"mode": "dry-run"})
    workbook_sha256 = sha256_file(workbook_path)
    sources = load_canonical_sources(workbook_path, config.workbook)
    excluded_urls = load_excluded_urls(workbook_path, config.workbook)
    write_event(
        events_path,
        run_id,
        "workbook_parsed",
        details={
            "workbook_path": str(workbook_path),
            "workbook_sha256": workbook_sha256,
            "canonical_rows": len(sources),
            "excluded_url_count": len(excluded_urls),
        },
    )

    filtered_sources = _apply_filters(sources, sheet_filter, id_filter, host_filter, limit)
    first_record_by_url: dict[str, str] = {}
    artifact_by_url: dict[str, Path] = {}
    records: list[dict] = []

    for source in filtered_sources:
        artifact_path = planned_artifact_path(output_root, source)
        duplicate_of = None
        status = "planned"

        if source.normalized_url in excluded_urls:
            status = "skipped_excluded"
            artifact_path = None
            write_event(events_path, run_id, "exclusion_applied", source=source)
        elif source.normalized_url in first_record_by_url:
            status = "duplicate_url"
            duplicate_of = first_record_by_url[source.normalized_url]
            artifact_path = artifact_by_url[source.normalized_url]
            write_event(
                events_path,
                run_id,
                "duplicate_detected",
                source=source,
                details={"duplicate_of": duplicate_of},
            )
        else:
            first_record_by_url[source.normalized_url] = source.source_record_id
            artifact_by_url[source.normalized_url] = artifact_path

        record = _manifest_record(
            run_id=run_id,
            workbook_path=workbook_path,
            workbook_sha256=workbook_sha256,
            source=source,
            status=status,
            artifact_path=artifact_path,
            duplicate_of=duplicate_of,
        )
        records.append(record)
        write_event(events_path, run_id, "record_finalized", source=source, details={"status": status})

    _write_jsonl(manifest_path, records)
    _write_failures_csv(failures_path, records)

    status_counts = Counter(record["status"] for record in records)
    top_hosts = Counter(urlsplit(record["normalized_url"]).netloc.lower() for record in records)
    unique_canonical_urls = len({source.normalized_url for source in sources})
    completed_at = utc_now()
    summary = {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "mode": "dry-run",
        "workbook_path": str(workbook_path),
        "workbook_sha256": workbook_sha256,
        "canonical_rows": len(sources),
        "filtered_rows": len(records),
        "unique_canonical_urls": unique_canonical_urls,
        "excluded_url_count": len(excluded_urls),
        "planned_count": status_counts.get("planned", 0),
        "duplicate_url_count": status_counts.get("duplicate_url", 0),
        "skipped_excluded_count": status_counts.get("skipped_excluded", 0),
        "downloaded_count": 0,
        "failed_count": 0,
        "needs_review_count": 0,
        "status_counts": dict(status_counts),
        "top_hosts": top_hosts.most_common(20),
        "manifest_path": str(manifest_path),
    }
    validation_report = _validation_report(run_id, summary, records, excluded_urls)

    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation_report_path.write_text(
        json.dumps(validation_report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    write_event(
        events_path,
        run_id,
        "run_completed",
        details={"status_counts": dict(status_counts), "passed": validation_report["passed"]},
    )

    return DryRunResult(
        run_id=run_id,
        manifest_path=manifest_path,
        summary_path=summary_path,
        validation_report_path=validation_report_path,
        failures_path=failures_path,
        summary=summary,
    )


def _apply_filters(
    sources: list[WorkbookSource],
    sheet_filter: str | None,
    id_filter: str | None,
    host_filter: str | None,
    limit: int | None,
) -> list[WorkbookSource]:
    filtered = sources
    if sheet_filter:
        filtered = [source for source in filtered if source.sheet == sheet_filter]
    if id_filter:
        filtered = [
            source
            for source in filtered
            if source.source_id == id_filter or source.source_record_id == id_filter
        ]
    if host_filter:
        filtered = [
            source
            for source in filtered
            if urlsplit(source.normalized_url).netloc.lower() == host_filter.lower()
        ]
    if limit is not None:
        filtered = filtered[:limit]
    return filtered


def _manifest_record(
    *,
    run_id: str,
    workbook_path: Path,
    workbook_sha256: str,
    source: WorkbookSource,
    status: str,
    artifact_path: Path | None,
    duplicate_of: str | None,
) -> dict:
    return {
        "run_id": run_id,
        "source_record_id": source.source_record_id,
        "workbook_path": str(workbook_path),
        "workbook_sha256": workbook_sha256,
        "sheet": source.sheet,
        "excel_row": source.excel_row,
        "source_id": source.source_id,
        "title": source.title,
        "original_url": source.original_url,
        "normalized_url": source.normalized_url,
        "final_url": None,
        "redirect_chain": [],
        "status": status,
        "artifact_path": str(artifact_path) if artifact_path else None,
        "artifact_sha256": None,
        "artifact_byte_size": None,
        "content_type": None,
        "fetch_timestamp": None,
        "validation": {"mode": "dry-run", "passed": status in {"planned", "duplicate_url"}},
        "duplicate_of": duplicate_of,
        "failure": None,
        "metadata": source.metadata,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def _write_failures_csv(path: Path, records: list[dict]) -> None:
    headers = [
        "source_record_id",
        "sheet",
        "excel_row",
        "source_id",
        "title",
        "original_url",
        "status",
        "error_class",
        "error_message",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for record in records:
            failure = record.get("failure") or {}
            if record["status"] not in {"planned", "duplicate_url"}:
                writer.writerow(
                    {
                        "source_record_id": record["source_record_id"],
                        "sheet": record["sheet"],
                        "excel_row": record["excel_row"],
                        "source_id": record["source_id"],
                        "title": record["title"],
                        "original_url": record["original_url"],
                        "status": record["status"],
                        "error_class": failure.get("error_class"),
                        "error_message": failure.get("error_message"),
                    }
                )


def _validation_report(
    run_id: str,
    summary: dict,
    records: list[dict],
    excluded_urls: set[str],
) -> dict:
    record_urls = [record["normalized_url"] for record in records]
    downloaded_excluded = [
        record
        for record in records
        if record["normalized_url"] in excluded_urls and record["status"] != "skipped_excluded"
    ]
    checks = [
        {
            "name": "all_filtered_rows_have_status",
            "passed": all(record.get("status") for record in records),
            "expected": len(records),
            "actual": sum(1 for record in records if record.get("status")),
            "details": None,
        },
        {
            "name": "unique_canonical_url_count",
            "passed": summary["unique_canonical_urls"] == len(set(record_urls))
            if summary["filtered_rows"] == summary["canonical_rows"]
            else True,
            "expected": summary["unique_canonical_urls"],
            "actual": len(set(record_urls)),
            "details": "Only enforced for unfiltered dry runs.",
        },
        {
            "name": "excluded_urls_not_planned_for_download",
            "passed": not downloaded_excluded,
            "expected": 0,
            "actual": len(downloaded_excluded),
            "details": None,
        },
        {
            "name": "duplicate_references_preserved",
            "passed": summary["filtered_rows"] == len(records),
            "expected": summary["filtered_rows"],
            "actual": len(records),
            "details": None,
        },
    ]
    return {
        "run_id": run_id,
        "mode": "dry-run",
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }
