from __future__ import annotations

from pathlib import Path
import csv
import json
from typing import Any

from .records import WorkbookSource


FAILURE_STATUSES = {
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


def build_capture_manifest_record(
    *,
    run_id: str,
    workbook_path: Path,
    workbook_sha256: str,
    source: WorkbookSource,
    status: str,
    final_url: str | None,
    redirect_chain: list[str],
    content_type: str | None,
    content_length: int | None,
    http_status: int | None,
    attempt_count: int,
    fetch_timestamp: str | None,
    validation: dict[str, Any],
    duplicate_of: str | None,
    failure: dict[str, Any] | None,
    artifact_path: Path | None = None,
    artifact_sha256: str | None = None,
    artifact_byte_size: int | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
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
        "final_url": final_url,
        "redirect_chain": redirect_chain,
        "status": status,
        "artifact_path": str(artifact_path) if artifact_path else None,
        "artifact_sha256": artifact_sha256,
        "artifact_byte_size": artifact_byte_size,
        "content_type": content_type,
        "content_length": content_length,
        "http_status": http_status,
        "attempt_count": attempt_count,
        "fetch_timestamp": fetch_timestamp,
        "validation": validation,
        "duplicate_of": duplicate_of,
        "failure": failure,
        "metadata": source.metadata,
    }
    if extra_fields:
        record.update(extra_fields)
    return record


def is_failure_status(status: str) -> bool:
    return status in FAILURE_STATUSES


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def resolve_manifest_path(output_dir: Path, summary: dict[str, Any]) -> Path:
    manifest_value = Path(summary["manifest_path"])
    candidates = []
    if manifest_value.is_absolute():
        candidates.append(manifest_value)
    else:
        candidates.extend(
            [
                manifest_value,
                output_dir / manifest_value,
                output_dir.parent / manifest_value,
            ]
        )
    candidates.append(output_dir / "manifests" / f"{summary['mode']}_{summary['run_id']}.jsonl")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "Missing manifest. Checked: " + ", ".join(str(candidate) for candidate in candidates)
    )


def write_failures_csv(path: Path, records: list[dict[str, Any]]) -> None:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers)
        writer.writeheader()
        for record in records:
            if not is_failure_status(str(record.get("status") or "")):
                continue
            failure = record.get("failure") or {}
            writer.writerow(
                {
                    "source_record_id": record.get("source_record_id"),
                    "sheet": record.get("sheet"),
                    "excel_row": record.get("excel_row"),
                    "source_id": record.get("source_id"),
                    "title": record.get("title"),
                    "original_url": record.get("original_url"),
                    "status": record.get("status"),
                    "error_class": failure.get("error_class"),
                    "error_message": failure.get("error_message"),
                    "attempt_count": failure.get("attempt_count") or record.get("attempt_count"),
                }
            )


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
