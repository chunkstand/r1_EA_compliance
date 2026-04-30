from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

from .report import _read_jsonl, _resolve_manifest_path, is_repair_status, summarize_records


ARTIFACT_SUCCESS_STATUSES = {"downloaded", "downloaded_existing", "duplicate_content"}
KNOWN_STATUSES = {
    "blocked",
    "challenge_page",
    "downloaded",
    "downloaded_existing",
    "duplicate_content",
    "duplicate_url",
    "failed",
    "invalid_content",
    "needs_review",
    "not_found",
    "planned",
    "preflight_ok",
    "rate_limited",
    "skipped_excluded",
    "ssl_error",
    "timeout",
    "unsupported_content_type",
}


@dataclass(frozen=True)
class ValidationGateResult:
    run_id: str
    validation_path: Path
    passed: bool
    report: dict


def validate_run(*, output_dir: Path, run_id: str) -> ValidationGateResult:
    run_dir = output_dir / "runs" / run_id
    summary_path = run_dir / "summary.json"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing run summary: {summary_path}")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    manifest_path = _resolve_manifest_path(output_dir, summary)
    records = _read_jsonl(manifest_path)
    report_summary = summarize_records(summary, records)

    checks = [
        _check_all_rows_have_status(records),
        _check_known_status_values(records),
        _check_excluded_urls_not_touched(records),
        _check_failure_rows_are_in_repair_queue(records, report_summary),
        _check_artifacts(records),
        _check_duplicate_content_links(records),
        _check_summary_counts(summary, records),
    ]
    gate_report = {
        "run_id": run_id,
        "mode": summary.get("mode"),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "summary": summary,
    }
    validation_path = run_dir / "acceptance_gate.json"
    validation_path.write_text(json.dumps(gate_report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ValidationGateResult(
        run_id=run_id,
        validation_path=validation_path,
        passed=gate_report["passed"],
        report=gate_report,
    )


def _check_all_rows_have_status(records: list[dict]) -> dict:
    missing = [record.get("source_record_id") for record in records if not record.get("status")]
    return {
        "name": "all_rows_have_status",
        "passed": not missing,
        "details": {"missing_source_record_ids": missing},
    }


def _check_known_status_values(records: list[dict]) -> dict:
    unknown = [
        {
            "source_record_id": record.get("source_record_id"),
            "status": record.get("status"),
        }
        for record in records
        if record.get("status") and record.get("status") not in KNOWN_STATUSES
    ]
    return {
        "name": "known_status_values",
        "passed": not unknown,
        "details": {"unknown": unknown},
    }


def _check_excluded_urls_not_touched(records: list[dict]) -> dict:
    violations = [
        record["source_record_id"]
        for record in records
        if record.get("status") == "skipped_excluded"
        and (
            record.get("artifact_path")
            or record.get("artifact_sha256")
            or record.get("http_status")
            or record.get("fetch_timestamp")
        )
    ]
    return {
        "name": "excluded_urls_not_touched",
        "passed": not violations,
        "details": {"violating_source_record_ids": violations},
    }


def _check_failure_rows_are_in_repair_queue(records: list[dict], report_summary: dict) -> dict:
    failure_ids = {
        record["source_record_id"] for record in records if _is_failure_or_unknown_status(record)
    }
    repair_ids = {row["source_record_id"] for row in report_summary.get("repair_rows", [])}
    missing = sorted(failure_ids - repair_ids)
    return {
        "name": "failure_rows_are_in_repair_queue",
        "passed": not missing,
        "details": {"missing_source_record_ids": missing},
    }


def _check_artifacts(records: list[dict]) -> dict:
    failures = []
    for record in records:
        if record.get("status") not in ARTIFACT_SUCCESS_STATUSES:
            continue
        artifact_path = record.get("artifact_path")
        if not artifact_path:
            failures.append(_artifact_failure(record, "missing artifact_path"))
            continue
        path = Path(artifact_path)
        if not path.exists():
            failures.append(_artifact_failure(record, f"artifact missing: {artifact_path}"))
            continue
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        if record.get("artifact_sha256") != digest:
            failures.append(_artifact_failure(record, "artifact_sha256 mismatch"))
        if record.get("artifact_byte_size") != len(body):
            failures.append(_artifact_failure(record, "artifact_byte_size mismatch"))
        if not record.get("validation", {}).get("passed"):
            failures.append(_artifact_failure(record, "validation did not pass"))
    return {
        "name": "successful_artifacts_exist_and_match_hash",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_duplicate_content_links(records: list[dict]) -> dict:
    artifact_paths = {
        record.get("artifact_path")
        for record in records
        if record.get("artifact_path") and record.get("status") in ARTIFACT_SUCCESS_STATUSES
    }
    failures = [
        _artifact_failure(record, "duplicate_content does not link to a canonical artifact")
        for record in records
        if record.get("status") == "duplicate_content" and record.get("duplicate_of") not in artifact_paths
    ]
    return {
        "name": "duplicate_content_links_to_canonical_artifact",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_summary_counts(summary: dict, records: list[dict]) -> dict:
    failures = []
    if summary.get("filtered_rows") != len(records):
        failures.append(
            {
                "field": "filtered_rows",
                "expected": len(records),
                "actual": summary.get("filtered_rows"),
            }
        )
    summary_status_counts = summary.get("status_counts") or {}
    actual_status_counts: dict[str, int] = {}
    for record in records:
        actual_status_counts[record["status"]] = actual_status_counts.get(record["status"], 0) + 1
    if summary_status_counts != actual_status_counts:
        failures.append(
            {
                "field": "status_counts",
                "expected": actual_status_counts,
                "actual": summary_status_counts,
            }
        )
    return {
        "name": "summary_counts_match_manifest",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _artifact_failure(record: dict, reason: str) -> dict:
    return {
        "source_record_id": record.get("source_record_id"),
        "status": record.get("status"),
        "artifact_path": record.get("artifact_path"),
        "reason": reason,
    }


def _is_failure_or_unknown_status(record: dict) -> bool:
    return is_repair_status(record.get("status", ""))
