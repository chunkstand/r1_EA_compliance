from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep
from urllib.parse import urlsplit
import hashlib
import json

from .adapters import adapt_download_url
from .capture_run_support import (
    build_capture_manifest_record,
    is_failure_status,
    write_failures_csv,
    write_jsonl,
)
from .config import DownloaderConfig, ValidationConfig
from .download_transport import (
    DownloadFetchResult,
    _classify_download_response,
    download_url,
)
from .dry_run import _apply_filters, _override_count, new_run_id, utc_now, write_event
from .preflight import (
    _body_looks_blocked,
    _body_looks_not_found,
    _respect_host_delay,
)
from .records import WorkbookSource, planned_artifact_path, sha256_file
from .workbook import (
    ensure_supplemental_sources_allowed,
    load_canonical_sources,
    load_excluded_urls,
    merge_supplemental_sources,
)


__all__ = [
    "DownloadFetchResult",
    "DownloadResult",
    "download_url",
    "run_download",
    "_classify_download_response",
    "_content_type_for_suffix",
    "_suffix_for_content_type",
]


@dataclass(frozen=True)
class DownloadResult:
    run_id: str
    manifest_path: Path
    summary_path: Path
    validation_report_path: Path
    failures_path: Path
    summary: dict


def run_download(
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
    force: bool = False,
    fetcher=None,
    sleep_fn=sleep,
) -> DownloadResult:
    run_id = run_id or new_run_id()
    started_at = utc_now()
    output_root = output_dir
    run_dir = output_root / config.outputs.run_dir / run_id
    manifest_dir = output_root / config.outputs.manifest_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)

    events_path = run_dir / "events.jsonl"
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    summary_path = run_dir / "summary.json"
    validation_report_path = run_dir / "validation_report.json"
    failures_path = run_dir / "failures.csv"

    write_event(events_path, run_id, "run_started", details={"mode": "download", "force": force})
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

    fetcher = fetcher or download_url
    downloaded_by_url: dict[str, dict] = {}
    first_record_by_url: dict[str, str] = {}
    host_last_fetch: dict[str, float] = {}
    artifact_by_sha: dict[str, str] = {}
    records: list[dict] = []

    for source in filtered_sources:
        duplicate_of = None
        planned_path = planned_artifact_path(output_root, source)

        if source.normalized_url in excluded_urls:
            record = _manifest_record(
                run_id=run_id,
                workbook_path=workbook_path,
                workbook_sha256=workbook_sha256,
                source=source,
                status="skipped_excluded",
                planned_path=planned_path,
                final_url=None,
                redirect_chain=[],
                content_type=None,
                content_length=None,
                http_status=None,
                attempt_count=0,
                artifact_path=None,
                artifact_sha256=None,
                artifact_byte_size=None,
                duplicate_of=None,
                failure=None,
                validation={"mode": "download", "passed": True, "reason": "scope exclusion"},
            )
            records.append(record)
            write_event(events_path, run_id, "exclusion_applied", source=source)
            write_event(events_path, run_id, "record_finalized", source=source, details={"status": record["status"]})
            continue

        if source.normalized_url in downloaded_by_url:
            duplicate_of = first_record_by_url[source.normalized_url]
            prior = downloaded_by_url[source.normalized_url]
            record = dict(prior)
            record.update(
                {
                    "source_record_id": source.source_record_id,
                    "sheet": source.sheet,
                    "excel_row": source.excel_row,
                    "source_id": source.source_id,
                    "title": source.title,
                    "original_url": source.original_url,
                    "effective_url": source.effective_url,
                    "normalized_url": source.normalized_url,
                    "status": "duplicate_url",
                    "duplicate_of": duplicate_of,
                    "validation": {
                        "mode": "download",
                        "passed": True,
                        "reason": "duplicate URL reference",
                    },
                    "failure": None,
                    "metadata": source.metadata,
                }
            )
            records.append(record)
            write_event(events_path, run_id, "duplicate_detected", source=source, details={"duplicate_of": duplicate_of})
            write_event(events_path, run_id, "record_finalized", source=source, details={"status": record["status"]})
            continue

        first_record_by_url[source.normalized_url] = source.source_record_id
        preferred_existing_artifact_suffixes = _preferred_existing_artifact_suffixes(source.effective_url)
        if preferred_existing_artifact_suffixes is None:
            preferred_existing_artifact_suffixes = _adapted_existing_artifact_suffixes(
                source.effective_url,
                config.network,
            )
        existing = None if force else _find_existing_artifact(
            planned_path,
            preferred_suffixes=preferred_existing_artifact_suffixes,
        )
        if existing:
            artifact_sha256 = sha256_file(existing)
            artifact_byte_size = existing.stat().st_size
            existing_validation = _validate_existing_artifact(existing, config.validation)
            if existing_validation["passed"]:
                record = _manifest_record(
                    run_id=run_id,
                    workbook_path=workbook_path,
                    workbook_sha256=workbook_sha256,
                    source=source,
                    status="downloaded_existing",
                    planned_path=planned_path,
                    final_url=None,
                    redirect_chain=[],
                    content_type=_content_type_for_suffix(existing.suffix),
                    content_length=artifact_byte_size,
                    http_status=None,
                    attempt_count=0,
                    artifact_path=existing,
                    artifact_sha256=artifact_sha256,
                    artifact_byte_size=artifact_byte_size,
                    duplicate_of=None,
                    failure=None,
                    validation=existing_validation,
                )
                downloaded_by_url[source.normalized_url] = record
                artifact_by_sha.setdefault(artifact_sha256, str(existing))
                records.append(record)
                write_event(events_path, run_id, "artifact_reused", source=source, details={"artifact_path": str(existing)})
                write_event(events_path, run_id, "record_finalized", source=source, details={"status": record["status"]})
                continue
            write_event(
                events_path,
                run_id,
                "artifact_invalid",
                source=source,
                details={"artifact_path": str(existing), "reason": existing_validation["reason"]},
            )

        host = urlsplit(source.normalized_url).netloc.lower()
        _respect_host_delay(host, host_last_fetch, config.network, sleep_fn)
        write_event(events_path, run_id, "fetch_attempt_started", source=source)
        fetch_result = fetcher(source.effective_url, config.network, config.validation)
        host_last_fetch[host] = monotonic()
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
                "attempt_count": fetch_result.attempt_count,
            },
        )

        artifact_path = None
        artifact_sha256 = None
        artifact_byte_size = None
        status = fetch_result.status
        failure = fetch_result.failure
        validation = fetch_result.validation
        duplicate_content_of = None

        if fetch_result.status == "downloaded":
            artifact_sha256 = hashlib.sha256(fetch_result.body).hexdigest()
            artifact_byte_size = len(fetch_result.body)
            if artifact_sha256 in artifact_by_sha:
                duplicate_content_of = artifact_by_sha[artifact_sha256]
                artifact_path = Path(duplicate_content_of)
                status = "duplicate_content"
            else:
                artifact_path = _artifact_path_for_hash(planned_path, artifact_sha256, fetch_result.content_type)
                artifact_path = _write_artifact(artifact_path, fetch_result.body, force=force)
                artifact_by_sha[artifact_sha256] = str(artifact_path)
                write_event(
                    events_path,
                    run_id,
                    "artifact_written",
                    source=source,
                    details={
                        "artifact_path": str(artifact_path),
                        "artifact_sha256": artifact_sha256,
                        "artifact_byte_size": artifact_byte_size,
                    },
                )
            write_event(
                events_path,
                run_id,
                "hash_computed",
                source=source,
                details={"artifact_sha256": artifact_sha256},
            )

        record = _manifest_record(
            run_id=run_id,
            workbook_path=workbook_path,
            workbook_sha256=workbook_sha256,
            source=source,
            status=status,
            planned_path=planned_path,
            final_url=fetch_result.final_url,
            redirect_chain=fetch_result.redirect_chain,
            content_type=fetch_result.content_type,
            content_length=fetch_result.content_length,
            http_status=fetch_result.http_status,
            attempt_count=fetch_result.attempt_count,
            artifact_path=artifact_path,
            artifact_sha256=artifact_sha256,
            artifact_byte_size=artifact_byte_size,
            duplicate_of=duplicate_content_of,
            failure=failure,
            validation=validation,
        )
        downloaded_by_url[source.normalized_url] = record
        records.append(record)
        write_event(events_path, run_id, "record_finalized", source=source, details={"status": record["status"]})

    write_jsonl(manifest_path, records)
    write_failures_csv(failures_path, records)

    status_counts = Counter(record["status"] for record in records)
    top_hosts = Counter(urlsplit(record["normalized_url"]).netloc.lower() for record in records)
    completed_at = utc_now()
    summary = {
        "run_id": run_id,
        "started_at": started_at,
        "completed_at": completed_at,
        "mode": "download",
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
        "checked_url_count": len(
            {record["normalized_url"] for record in records if record["status"] != "duplicate_url"}
        ),
        "downloaded_count": status_counts.get("downloaded", 0),
        "downloaded_existing_count": status_counts.get("downloaded_existing", 0),
        "duplicate_url_count": status_counts.get("duplicate_url", 0),
        "duplicate_content_count": status_counts.get("duplicate_content", 0),
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

    return DownloadResult(
        run_id=run_id,
        manifest_path=manifest_path,
        summary_path=summary_path,
        validation_report_path=validation_report_path,
        failures_path=failures_path,
        summary=summary,
    )


def _artifact_path_for_hash(planned_path: Path, sha256: str, content_type: str | None) -> Path:
    suffix = _suffix_for_content_type(content_type)
    stem = planned_path.with_suffix("").name
    return planned_path.parent / f"{stem}_{sha256[:12]}{suffix}"


def _suffix_for_content_type(content_type: str | None) -> str:
    if content_type == "application/pdf":
        return ".pdf"
    if content_type == "application/msword":
        return ".doc"
    if content_type in {"text/html", "application/xhtml+xml"}:
        return ".html"
    if content_type in {"application/xml", "text/xml"}:
        return ".xml"
    if content_type == "application/zip":
        return ".zip"
    if content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return ".docx"
    if content_type == "image/jpeg":
        return ".jpg"
    return ".bin"


def _content_type_for_suffix(suffix: str) -> str | None:
    return {
        ".doc": "application/msword",
        ".pdf": "application/pdf",
        ".html": "text/html",
        ".xml": "application/xml",
        ".zip": "application/zip",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }.get(suffix.lower())


def _validate_existing_artifact(path: Path, validation: ValidationConfig) -> dict:
    try:
        body = path.read_bytes()
    except OSError as error:
        return {"mode": "download", "passed": False, "reason": str(error)}
    if len(body) < validation.minimum_body_bytes:
        return {
            "mode": "download",
            "passed": False,
            "reason": f"Existing artifact smaller than minimum: {len(body)} bytes",
        }
    content_type = _content_type_for_suffix(path.suffix)
    if content_type == "application/pdf" and not body[:1024].lstrip().startswith(b"%PDF"):
        return {"mode": "download", "passed": False, "reason": "Existing PDF failed header check"}
    sample = body[:8192].decode("utf-8", errors="ignore").lower()
    if sample and _body_looks_not_found(sample):
        return {"mode": "download", "passed": False, "reason": "Existing artifact is not-found content"}
    if sample and _body_looks_blocked(sample):
        return {"mode": "download", "passed": False, "reason": "Existing artifact is challenge content"}
    return {"mode": "download", "passed": True, "reason": "existing artifact reused"}


def _write_artifact(path: Path, body: bytes, *, force: bool) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        existing_hash = sha256_file(path)
        incoming_hash = hashlib.sha256(body).hexdigest()
        if existing_hash == incoming_hash:
            return path
        path = _next_version_path(path)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_bytes(body)
    temp_path.replace(path)
    return path


def _next_version_path(path: Path) -> Path:
    for index in range(2, 10_000):
        candidate = path.with_name(f"{path.stem}_v{index}{path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Could not allocate versioned artifact path for {path}")


def _find_existing_artifact(
    planned_path: Path,
    *,
    preferred_suffixes: set[str] | None = None,
) -> Path | None:
    directory = planned_path.parent
    if not directory.exists():
        return None
    prefix = planned_path.with_suffix("").name + "_"
    matches = sorted(
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.name.startswith(prefix)
        and not path.name.endswith(".tmp")
        and (not preferred_suffixes or path.suffix.lower() in preferred_suffixes)
    )
    return matches[0] if matches else None


def _preferred_existing_artifact_suffixes(url: str | None) -> set[str] | None:
    path = urlsplit(url or "").path.lower()
    if path.endswith(".pdf"):
        return {".pdf"}
    if path.endswith(".docx"):
        return {".docx"}
    if path.endswith(".doc"):
        return {".doc"}
    if path.endswith(".xml"):
        return {".xml"}
    if path.endswith(".zip"):
        return {".zip"}
    if path.endswith(".jpg"):
        return {".jpg"}
    if path.endswith(".jpeg"):
        return {".jpeg"}
    if path.endswith(".png"):
        return {".png"}
    return None


def _adapted_existing_artifact_suffixes(url: str | None, network) -> set[str] | None:
    parsed = urlsplit(url or "")
    if parsed.netloc.lower() not in {"www.fs.usda.gov", "fs.usda.gov"}:
        return None
    if not parsed.path.startswith("/cgi-bin/Directives/get_dirs/"):
        return None
    adapted = adapt_download_url(url or "", network)
    if adapted is None:
        return None
    suffixes = _preferred_existing_artifact_suffixes(adapted.url)
    if suffixes is not None:
        return suffixes
    expected_content_type = (adapted.expected_content_type or "").lower()
    if expected_content_type == "application/pdf":
        return {".pdf"}
    if expected_content_type == "application/msword":
        return {".doc"}
    if expected_content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return {".docx"}
    if expected_content_type in {"application/xml", "text/xml"}:
        return {".xml"}
    return None


def _manifest_record(
    *,
    run_id: str,
    workbook_path: Path,
    workbook_sha256: str,
    source: WorkbookSource,
    status: str,
    planned_path: Path,
    final_url: str | None,
    redirect_chain: list[str],
    content_type: str | None,
    content_length: int | None,
    http_status: int | None,
    attempt_count: int,
    artifact_path: Path | None,
    artifact_sha256: str | None,
    artifact_byte_size: int | None,
    duplicate_of: str | None,
    failure: dict | None,
    validation: dict,
) -> dict:
    return build_capture_manifest_record(
        run_id=run_id,
        workbook_path=workbook_path,
        workbook_sha256=workbook_sha256,
        source=source,
        status=status,
        final_url=final_url,
        redirect_chain=redirect_chain,
        content_type=content_type,
        content_length=content_length,
        http_status=http_status,
        attempt_count=attempt_count,
        fetch_timestamp=utc_now() if attempt_count else None,
        validation=validation,
        duplicate_of=duplicate_of,
        failure=failure,
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        artifact_byte_size=artifact_byte_size,
        extra_fields={"planned_artifact_path": str(planned_path)},
    )


def _validation_report(
    run_id: str,
    summary: dict,
    records: list[dict],
    excluded_urls: set[str],
) -> dict:
    excluded_downloads = [
        record
        for record in records
        if record["normalized_url"] in excluded_urls and record["status"] != "skipped_excluded"
    ]
    invalid_downloads = [
        record
        for record in records
        if record["status"] in {"downloaded", "downloaded_existing", "duplicate_content"}
        and (
            not record.get("artifact_path")
            or not record.get("artifact_sha256")
            or not record.get("artifact_byte_size")
            or not record.get("validation", {}).get("passed")
        )
    ]
    challenge_successes = [
        record
        for record in records
        if record["status"] in {"downloaded", "downloaded_existing"}
        and record.get("final_url")
        and "unblock.federalregister.gov" in record["final_url"].lower()
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
            "name": "excluded_urls_not_downloaded",
            "passed": not excluded_downloads,
            "expected": 0,
            "actual": len(excluded_downloads),
            "details": None,
        },
        {
            "name": "downloaded_rows_have_artifact_hash_and_validation",
            "passed": not invalid_downloads,
            "expected": 0,
            "actual": len(invalid_downloads),
            "details": None,
        },
        {
            "name": "challenge_pages_not_downloaded",
            "passed": not challenge_successes,
            "expected": 0,
            "actual": len(challenge_successes),
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
        "mode": "download",
        "checks": checks,
        "passed": all(check["passed"] for check in checks),
    }
