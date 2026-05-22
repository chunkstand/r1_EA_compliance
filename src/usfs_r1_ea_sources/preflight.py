from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from urllib.parse import urlsplit
import json
import subprocess

from .capture_run_support import (
    build_capture_manifest_record,
    is_failure_status,
    write_failures_csv,
    write_jsonl,
)
from .config import DownloaderConfig, NetworkConfig, ValidationConfig
from .dry_run import _apply_filters, _override_count, new_run_id, utc_now, write_event
from .preflight_transport import (
    CurlTransportResult,
    PreflightFetchResult,
    _base_content_type,
    _body_looks_blocked,
    _body_looks_not_found,
    _classify_response,
    _fetch_once,
    _int_or_none,
    _request_headers,
    _respect_host_delay,
    _run_curl_request,
    _uses_browser_compatible_user_agent,
    _uses_verified_curl_transport,
)
from .records import WorkbookSource, planned_artifact_path, sha256_file
from .workbook import (
    ensure_supplemental_sources_allowed,
    load_canonical_sources,
    load_excluded_urls,
    merge_supplemental_sources,
)


__all__ = [
    "CurlTransportResult",
    "PreflightFetchResult",
    "PreflightResult",
    "fetch_url_metadata",
    "run_preflight",
    "subprocess",
    "_base_content_type",
    "_body_looks_blocked",
    "_body_looks_not_found",
    "_classify_response",
    "_fetch_once",
    "_int_or_none",
    "_request_headers",
    "_run_curl_request",
    "_uses_browser_compatible_user_agent",
    "_uses_verified_curl_transport",
]


@dataclass(frozen=True)
class PreflightResult:
    run_id: str
    manifest_path: Path
    summary_path: Path
    validation_report_path: Path
    failures_path: Path
    summary: dict


def fetch_url_metadata(
    url: str,
    network: NetworkConfig,
    validation: ValidationConfig,
) -> PreflightFetchResult:
    last_result: PreflightFetchResult | None = None
    max_attempts = max(1, network.max_attempts)
    for attempt in range(1, max_attempts + 1):
        for method in ("HEAD", "GET"):
            result = _fetch_once(url, method, network, validation, attempt, original_url=url)
            last_result = result
            if method == "HEAD" and result.status in {
                "blocked",
                "failed",
                "rate_limited",
                "unsupported_content_type",
            }:
                continue
            if method == "HEAD" and result.http_status in {403, 405, 406}:
                continue
            break
        if last_result and not _is_transient_status(last_result.status):
            return last_result
    if last_result is None:
        raise RuntimeError("No preflight attempt completed")
    return last_result


def run_preflight(
    *,
    workbook_path: Path,
    output_dir: Path,
    config: DownloaderConfig,
    run_id: str | None = None,
    sheet_filter: str | None = None,
    id_filter: str | None = None,
    host_filter: str | None = None,
    limit: int | None = None,
    source_record_ids: set[str] | None = None,
    supplemental_sources: list[WorkbookSource] | None = None,
    source_delta_input: dict | None = None,
    fetcher=None,
    sleep_fn=sleep,
) -> PreflightResult:
    run_id = run_id or new_run_id()
    started_at = utc_now()
    output_root = output_dir
    run_dir = output_root / config.outputs.run_dir / run_id
    manifest_dir = output_root / config.outputs.manifest_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    events_path = run_dir / "events.jsonl"
    manifest_path = manifest_dir / f"preflight_{run_id}.jsonl"
    summary_path = run_dir / "summary.json"
    validation_report_path = run_dir / "validation_report.json"
    failures_path = run_dir / "failures.csv"

    write_event(events_path, run_id, "run_started", details={"mode": "preflight"})
    workbook_sha256 = sha256_file(workbook_path)
    workbook_sources = load_canonical_sources(workbook_path, config.workbook)
    ensure_supplemental_sources_allowed(
        config.workbook,
        supplemental_sources=supplemental_sources,
        source_delta_input=source_delta_input,
    )
    sources = merge_supplemental_sources(workbook_sources, supplemental_sources)
    excluded_urls = load_excluded_urls(workbook_path, config.workbook)
    filtered_sources = _apply_filters(
        sources,
        sheet_filter,
        id_filter,
        host_filter,
        limit,
        source_record_ids=source_record_ids,
    )
    write_event(
        events_path,
        run_id,
        "workbook_parsed",
        details={
            "workbook_path": str(workbook_path),
            "workbook_sha256": workbook_sha256,
            "workbook_rows": len(workbook_sources),
            "canonical_rows": len(sources),
            "supplemental_source_count": len(supplemental_sources or []),
            "source_delta_input": source_delta_input,
            "filtered_rows": len(filtered_sources),
            "override_count": _override_count(sources),
            "filtered_override_count": _override_count(filtered_sources),
            "excluded_url_count": len(excluded_urls),
        },
    )

    fetcher = fetcher or fetch_url_metadata
    fetched_by_url: dict[str, PreflightFetchResult] = {}
    first_record_by_url: dict[str, str] = {}
    artifact_by_url: dict[str, Path] = {}
    host_last_fetch: dict[str, float] = {}
    records: list[dict] = []

    for source in filtered_sources:
        artifact_path = planned_artifact_path(output_root, source)
        duplicate_of = None

        if source.normalized_url in excluded_urls:
            fetch_result = PreflightFetchResult(
                status="skipped_excluded",
                http_status=None,
                final_url=None,
                redirect_chain=[],
                content_type=None,
                content_length=None,
                method=None,
                failure=None,
                validation={"mode": "preflight", "passed": True, "reason": "scope exclusion"},
            )
            artifact_path = None
            write_event(events_path, run_id, "exclusion_applied", source=source)
        elif source.normalized_url in fetched_by_url:
            fetch_result = fetched_by_url[source.normalized_url]
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
            host = urlsplit(source.normalized_url).netloc.lower()
            _respect_host_delay(host, host_last_fetch, config.network, sleep_fn)
            write_event(events_path, run_id, "fetch_attempt_started", source=source)
            fetch_result = fetcher(source.effective_url, config.network, config.validation)
            fetched_by_url[source.normalized_url] = fetch_result
            first_record_by_url[source.normalized_url] = source.source_record_id
            artifact_by_url[source.normalized_url] = artifact_path
            write_event(
                events_path,
                run_id,
                "response_received",
                source=source,
                details={
                    "status": fetch_result.status,
                    "http_status": fetch_result.http_status,
                    "final_url": fetch_result.final_url,
                    "content_type": fetch_result.content_type,
                    "content_length": fetch_result.content_length,
                },
            )

        record = _manifest_record(
            run_id=run_id,
            workbook_path=workbook_path,
            workbook_sha256=workbook_sha256,
            source=source,
            fetch_result=fetch_result,
            artifact_path=artifact_path,
            duplicate_of=duplicate_of,
        )
        records.append(record)
        write_event(
            events_path,
            run_id,
            "record_finalized",
            source=source,
            details={"status": record["status"]},
        )

    write_jsonl(manifest_path, records)
    write_failures_csv(failures_path, records)

    status_counts = Counter(record["status"] for record in records)
    top_hosts = Counter(urlsplit(record["normalized_url"]).netloc.lower() for record in records)
    completed_at = utc_now()
    summary = {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "mode": "preflight",
        "workbook_path": str(workbook_path),
        "workbook_sha256": workbook_sha256,
        "workbook_rows": len(workbook_sources),
        "canonical_rows": len(sources),
        "supplemental_source_count": len(supplemental_sources or []),
        "source_delta_input": source_delta_input,
        "filtered_rows": len(records),
        "override_count": _override_count(sources),
        "filtered_override_count": _override_count(filtered_sources),
        "unique_canonical_urls": len({source.normalized_url for source in sources}),
        "excluded_url_count": len(excluded_urls),
        "checked_url_count": len(fetched_by_url),
        "preflight_ok_count": status_counts.get("preflight_ok", 0),
        "duplicate_url_count": status_counts.get("duplicate_url", 0),
        "skipped_excluded_count": status_counts.get("skipped_excluded", 0),
        "failed_count": sum(1 for record in records if is_failure_status(record["status"])),
        "needs_review_count": status_counts.get("needs_review", 0),
        "status_counts": dict(status_counts),
        "top_hosts": top_hosts.most_common(20),
        "manifest_path": str(manifest_path),
    }
    validation_report = _validation_report(run_id, summary, records, excluded_urls)
    summary["validation_passed"] = validation_report["passed"]

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

    return PreflightResult(
        run_id=run_id,
        manifest_path=manifest_path,
        summary_path=summary_path,
        validation_report_path=validation_report_path,
        failures_path=failures_path,
        summary=summary,
    )


def _manifest_record(
    *,
    run_id: str,
    workbook_path: Path,
    workbook_sha256: str,
    source: WorkbookSource,
    fetch_result: PreflightFetchResult,
    artifact_path: Path | None,
    duplicate_of: str | None,
) -> dict:
    status = "duplicate_url" if duplicate_of else fetch_result.status
    validation = dict(fetch_result.validation)
    if duplicate_of:
        validation = {"mode": "preflight", "passed": True, "reason": "duplicate URL reference"}
    return build_capture_manifest_record(
        run_id=run_id,
        workbook_path=workbook_path,
        workbook_sha256=workbook_sha256,
        source=source,
        status=status,
        final_url=fetch_result.final_url,
        redirect_chain=fetch_result.redirect_chain,
        content_type=fetch_result.content_type,
        content_length=fetch_result.content_length,
        http_status=fetch_result.http_status,
        attempt_count=fetch_result.attempt_count,
        fetch_timestamp=utc_now() if fetch_result.method else None,
        validation=validation,
        duplicate_of=duplicate_of,
        failure=None if duplicate_of else fetch_result.failure,
        artifact_path=artifact_path,
        extra_fields={"fetch_method": fetch_result.method},
    )


def _validation_report(
    run_id: str,
    summary: dict,
    records: list[dict],
    excluded_urls: set[str],
) -> dict:
    invalid_successes = [
        record
        for record in records
        if record["status"] == "preflight_ok" and not record["validation"].get("passed")
    ]
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
            "name": "excluded_urls_not_checked",
            "passed": not downloaded_excluded,
            "expected": 0,
            "actual": len(downloaded_excluded),
            "details": None,
        },
        {
            "name": "preflight_ok_records_pass_validation",
            "passed": not invalid_successes,
            "expected": 0,
            "actual": len(invalid_successes),
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
        "mode": "preflight",
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }


def _is_transient_status(status: str) -> bool:
    return status in {"failed", "rate_limited", "timeout"}
