from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, HTTPSHandler, Request, build_opener
import csv
import json
import socket
import ssl

from .adapters import adapt_download_url
from .config import DownloaderConfig, NetworkConfig, ValidationConfig
from .dry_run import _apply_filters, _override_count, new_run_id, utc_now, write_event
from .records import WorkbookSource, planned_artifact_path, sha256_file
from .workbook import (
    ensure_supplemental_sources_allowed,
    load_canonical_sources,
    load_excluded_urls,
    merge_supplemental_sources,
)


BROWSER_COMPATIBLE_USER_AGENT = "Mozilla/5.0"


@dataclass(frozen=True)
class PreflightFetchResult:
    status: str
    http_status: int | None
    final_url: str | None
    redirect_chain: list[str]
    content_type: str | None
    content_length: int | None
    method: str | None
    failure: dict | None
    validation: dict
    attempt_count: int = 1


@dataclass(frozen=True)
class PreflightResult:
    run_id: str
    manifest_path: Path
    summary_path: Path
    validation_report_path: Path
    failures_path: Path
    summary: dict


class RecordingRedirectHandler(HTTPRedirectHandler):
    def __init__(self) -> None:
        super().__init__()
        self.redirect_chain: list[str] = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        self.redirect_chain.append(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


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
            host_last_fetch[host] = monotonic()
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

    _write_jsonl(manifest_path, records)
    _write_failures_csv(failures_path, records)

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
        "failed_count": sum(1 for record in records if _is_failure_status(record["status"])),
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


def fetch_url_metadata(
    url: str,
    network: NetworkConfig,
    validation: ValidationConfig,
) -> PreflightFetchResult:
    adapted = adapt_download_url(url, network)
    fetch_url = adapted.url if adapted else url
    last_result: PreflightFetchResult | None = None
    max_attempts = max(1, network.max_attempts)
    for attempt in range(1, max_attempts + 1):
        for method in ("HEAD", "GET"):
            result = _fetch_once(fetch_url, method, network, validation, attempt, original_url=url)
            if adapted and result.status == "preflight_ok":
                result = _with_adapter_metadata(result, adapted.adapter, adapted.expected_content_type)
            last_result = result
            if method == "HEAD" and result.status in {"blocked", "failed", "unsupported_content_type"}:
                continue
            if method == "HEAD" and result.http_status in {403, 405, 406}:
                continue
            break
        if last_result and not _is_transient_status(last_result.status):
            return last_result
    if last_result is None:
        return _error_result("failed", "NoAttempt", "No preflight attempt completed", None, 0)
    return last_result


def _fetch_once(
    url: str,
    method: str,
    network: NetworkConfig,
    validation: ValidationConfig,
    attempt_count: int,
    *,
    original_url: str | None = None,
) -> PreflightFetchResult:
    redirect_handler = RecordingRedirectHandler()
    opener = build_opener(HTTPSHandler(context=ssl.create_default_context()), redirect_handler)
    headers = _request_headers(url, network)
    if method == "GET":
        headers["Range"] = "bytes=0-0"

    request = Request(url, headers=headers, method=method)
    timeout = max(network.connect_timeout_seconds, network.read_timeout_seconds)
    try:
        with opener.open(request, timeout=timeout) as response:
            body_sample = response.read(4096) if method == "GET" else b""
            http_status = response.status
            final_url = response.geturl()
            content_type = _base_content_type(response.headers.get("content-type"))
            content_length = _int_or_none(response.headers.get("content-length"))
            result = _classify_response(
                http_status=http_status,
                final_url=final_url,
                redirect_chain=redirect_handler.redirect_chain,
                content_type=content_type,
                content_length=content_length,
                method=method,
                attempt_count=attempt_count,
                body_sample=body_sample,
                validation=validation,
                original_url=original_url,
            )
            if _uses_browser_compatible_user_agent(url, network):
                return _with_browser_compatible_metadata(result)
            return result
    except HTTPError as error:
        return _http_error_result(error, redirect_handler.redirect_chain, method, validation, attempt_count)
    except TimeoutError as error:
        return _error_result("timeout", "TimeoutError", str(error), method, attempt_count)
    except socket.timeout as error:
        return _error_result("timeout", "TimeoutError", str(error), method, attempt_count)
    except ssl.SSLError as error:
        return _error_result("ssl_error", "SSLError", str(error), method, attempt_count)
    except URLError as error:
        reason = getattr(error, "reason", None)
        if isinstance(reason, ssl.SSLError):
            return _error_result("ssl_error", "SSLError", str(reason), method, attempt_count)
        if isinstance(reason, TimeoutError):
            return _error_result("timeout", "TimeoutError", str(reason), method, attempt_count)
        return _error_result("failed", "URLError", str(error), method, attempt_count)
    except Exception as error:
        return _error_result("failed", type(error).__name__, str(error), method, attempt_count)


def _classify_response(
    *,
    http_status: int,
    final_url: str,
    redirect_chain: list[str],
    content_type: str | None,
    content_length: int | None,
    method: str,
    attempt_count: int,
    body_sample: bytes,
    validation: ValidationConfig,
    original_url: str | None = None,
) -> PreflightFetchResult:
    final_url_lower = final_url.lower()
    body_text = body_sample[:4096].decode("utf-8", errors="ignore").lower()
    chain_lower = " ".join([final_url_lower, *(url.lower() for url in redirect_chain)])

    status = "preflight_ok"
    reason = None
    if http_status == 429:
        status = "rate_limited"
        reason = "HTTP 429"
    elif http_status == 404:
        status = "not_found"
        reason = "HTTP 404"
    elif http_status >= 500:
        status = "failed"
        reason = f"HTTP {http_status}"
    elif any(pattern.lower() in chain_lower for pattern in validation.challenge_url_patterns):
        status = "challenge_page"
        reason = "Challenge URL pattern matched"
    elif any(pattern.lower() in final_url_lower for pattern in validation.not_found_url_patterns):
        status = "not_found"
        reason = "Not-found URL pattern matched"
    elif body_text and _body_looks_not_found(body_text):
        status = "not_found"
        reason = "Not-found body pattern matched"
    elif body_text and _body_looks_blocked(body_text):
        status = "challenge_page"
        reason = "Challenge body pattern matched"
    elif body_sample[:1024].lstrip().startswith((b"<?xml", b"<RULE", b"<ECFR")):
        content_type = content_type if content_type in {"application/xml", "text/xml"} else "application/xml"
    elif content_type and content_type not in validation.allowed_content_types:
        status = "unsupported_content_type"
        reason = f"Unsupported content type: {content_type}"

    validation_result = {
        "mode": "preflight",
        "passed": status == "preflight_ok",
        "reason": reason,
    }
    return PreflightFetchResult(
        status=status,
        http_status=http_status,
        final_url=original_url or final_url,
        redirect_chain=redirect_chain + ([final_url] if original_url and final_url != original_url else []),
        content_type=content_type,
        content_length=content_length,
        method=method,
        attempt_count=attempt_count,
        failure=None if status == "preflight_ok" else _failure(status, reason or status, attempt_count),
        validation=validation_result,
    )


def _http_error_result(
    error: HTTPError,
    redirect_chain: list[str],
    method: str,
    validation: ValidationConfig,
    attempt_count: int,
) -> PreflightFetchResult:
    content_type = _base_content_type(error.headers.get("content-type")) if error.headers else None
    content_length = _int_or_none(error.headers.get("content-length")) if error.headers else None
    status = "failed"
    if error.code == 404:
        status = "not_found"
    elif error.code == 429:
        status = "rate_limited"
    elif error.code in {401, 403}:
        status = "blocked"
    return PreflightFetchResult(
        status=status,
        http_status=error.code,
        final_url=error.url,
        redirect_chain=redirect_chain,
        content_type=content_type,
        content_length=content_length,
        method=method,
        attempt_count=attempt_count,
        failure=_failure(status, str(error), attempt_count),
        validation={"mode": "preflight", "passed": False, "reason": str(error)},
    )


def _error_result(
    status: str,
    error_class: str,
    message: str,
    method: str | None,
    attempt_count: int,
) -> PreflightFetchResult:
    return PreflightFetchResult(
        status=status,
        http_status=None,
        final_url=None,
        redirect_chain=[],
        content_type=None,
        content_length=None,
        method=method,
        attempt_count=attempt_count,
        failure={"error_class": error_class, "error_message": message, "attempt_count": attempt_count},
        validation={"mode": "preflight", "passed": False, "reason": message},
    )


def _failure(error_class: str, message: str, attempt_count: int) -> dict:
    return {"error_class": error_class, "error_message": message, "attempt_count": attempt_count}


def _base_content_type(value: str | None) -> str | None:
    if not value:
        return None
    return value.split(";", 1)[0].strip().lower()


def _int_or_none(value: str | None) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _body_looks_blocked(body_text: str) -> bool:
    patterns = [
        "unblock.federalregister.gov",
        "access denied",
        "enable javascript",
        "verify you are human",
    ]
    return any(pattern in body_text for pattern in patterns)


def _body_looks_not_found(body_text: str) -> bool:
    patterns = [
        "docnotfound",
        "document not found",
        "page not found",
        "404 not found",
    ]
    return any(pattern in body_text for pattern in patterns)


def _with_adapter_metadata(
    result: PreflightFetchResult,
    adapter: str,
    expected_content_type: str | None,
) -> PreflightFetchResult:
    validation = dict(result.validation)
    validation["adapter"] = adapter
    return PreflightFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=expected_content_type or result.content_type,
        content_length=result.content_length,
        method=result.method,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )


def _with_browser_compatible_metadata(result: PreflightFetchResult) -> PreflightFetchResult:
    validation = dict(result.validation)
    validation["browser_compatible_user_agent"] = True
    return PreflightFetchResult(
        status=result.status,
        http_status=result.http_status,
        final_url=result.final_url,
        redirect_chain=result.redirect_chain,
        content_type=result.content_type,
        content_length=result.content_length,
        method=result.method,
        attempt_count=result.attempt_count,
        failure=result.failure,
        validation=validation,
    )


def _request_headers(url: str, network: NetworkConfig) -> dict[str, str]:
    if _uses_browser_compatible_user_agent(url, network):
        return {
            "User-Agent": BROWSER_COMPATIBLE_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
    return {
        "User-Agent": network.user_agent,
        "Accept": "text/html,application/pdf,application/xhtml+xml,*/*;q=0.8",
    }


def _uses_browser_compatible_user_agent(url: str, network: NetworkConfig) -> bool:
    host_config = network.hosts.get(urlsplit(url).netloc.lower())
    return bool(host_config and host_config.browser_compatible_user_agent)


def _respect_host_delay(
    host: str,
    host_last_fetch: dict[str, float],
    network: NetworkConfig,
    sleep_fn,
) -> None:
    last_fetch = host_last_fetch.get(host)
    if last_fetch is None:
        return
    host_config = network.hosts.get(host)
    delay = host_config.delay_seconds if host_config else network.default_host_delay_seconds
    remaining = delay - (monotonic() - last_fetch)
    if remaining > 0:
        sleep_fn(remaining)


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
        "effective_url": source.effective_url,
        "normalized_url": source.normalized_url,
        "final_url": fetch_result.final_url,
        "redirect_chain": fetch_result.redirect_chain,
        "status": status,
        "artifact_path": str(artifact_path) if artifact_path else None,
        "artifact_sha256": None,
        "artifact_byte_size": None,
        "content_type": fetch_result.content_type,
        "content_length": fetch_result.content_length,
        "http_status": fetch_result.http_status,
        "fetch_method": fetch_result.method,
        "attempt_count": fetch_result.attempt_count,
        "fetch_timestamp": utc_now() if fetch_result.method else None,
        "validation": validation,
        "duplicate_of": duplicate_of,
        "failure": None if duplicate_of else fetch_result.failure,
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
        "attempt_count",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for record in records:
            if not _is_failure_status(record["status"]):
                continue
            failure = record.get("failure") or {}
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
                    "attempt_count": failure.get("attempt_count") or record.get("attempt_count"),
                }
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


def _is_failure_status(status: str) -> bool:
    return status in {
        "blocked",
        "challenge_page",
        "failed",
        "invalid_content",
        "needs_review",
        "not_found",
        "rate_limited",
        "ssl_error",
        "timeout",
        "unsupported_content_type",
    }


def _is_transient_status(status: str) -> bool:
    return status in {"failed", "rate_limited", "timeout"}
