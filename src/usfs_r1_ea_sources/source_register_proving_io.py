from __future__ import annotations

from pathlib import Path
import json
import re

from .preflight import PreflightFetchResult
from .records import planned_artifact_path, sha256_file


LATEST_PROVING_CONTEXT_SCHEMA_VERSION = "source-register-proving-context-v1"
DEFAULT_LATEST_PROVING_CONTEXT_RELATIVE_PATH = Path(
    "derived/source_register_proving/latest_context.json"
)


def _write_synthetic_download_run(
    *,
    workbook_path: Path,
    output_dir: Path,
    run_id: str,
    rows: list,
    preflight_records: list[dict],
) -> Path:
    run_dir = output_dir / "runs" / run_id
    manifest_dir = output_dir / "manifests"
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    rows_by_id = {row.source_record_id: row for row in rows}
    artifact_details_by_source_record_id: dict[str, dict] = {}
    records = []
    workbook_sha256 = sha256_file(workbook_path)
    for preflight_record in preflight_records:
        source_record_id = str(preflight_record["source_record_id"])
        row = rows_by_id[source_record_id]
        source = row.to_workbook_source()
        status = str(preflight_record["status"])
        if status not in {"preflight_ok", "duplicate_url"}:
            raise ValueError(
                "Proving slice preflight produced non-admissible status for "
                f"{source_record_id}: {status!r}"
            )
        if status == "duplicate_url":
            duplicate_of = str(preflight_record["duplicate_of"] or "")
            if duplicate_of not in artifact_details_by_source_record_id:
                raise ValueError(
                    "Duplicate preflight record referenced missing primary source: "
                    f"{source_record_id} -> {duplicate_of}"
                )
            artifact_details = artifact_details_by_source_record_id[duplicate_of]
            record_status = "duplicate_url"
        else:
            artifact_path = planned_artifact_path(output_dir, source)
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_bytes = json.dumps(
                {
                    "schema_version": "source-register-proving-artifact-v1",
                    "source_record_id": source_record_id,
                    "title": row.title,
                    "expected_parser": row.expected_parser,
                    "parser_admission_class": row.parser_admission_class,
                    "authority_document_id": row.authority_document_id,
                    "direct_file_readiness_class": row.direct_file_readiness_class,
                    "original_url": row.original_url,
                },
                indent=2,
                sort_keys=True,
            ).encode("utf-8")
            artifact_path.write_bytes(artifact_bytes)
            artifact_details = {
                "artifact_path": str(artifact_path),
                "artifact_sha256": sha256_file(artifact_path),
                "artifact_byte_size": artifact_path.stat().st_size,
                "content_type": _content_type_for_parser(row.expected_parser),
            }
            artifact_details_by_source_record_id[source_record_id] = artifact_details
            record_status = "downloaded_existing"
        records.append(
            {
                "run_id": run_id,
                "source_record_id": source_record_id,
                "workbook_path": str(workbook_path),
                "workbook_sha256": workbook_sha256,
                "sheet": source.sheet,
                "excel_row": source.excel_row,
                "source_id": source.source_id,
                "title": source.title,
                "original_url": source.original_url,
                "effective_url": source.effective_url,
                "normalized_url": source.normalized_url,
                "final_url": preflight_record["final_url"],
                "redirect_chain": preflight_record["redirect_chain"],
                "status": record_status,
                "planned_artifact_path": str(planned_artifact_path(output_dir, source)),
                "artifact_path": artifact_details["artifact_path"],
                "artifact_sha256": artifact_details["artifact_sha256"],
                "artifact_byte_size": artifact_details["artifact_byte_size"],
                "content_type": artifact_details["content_type"],
                "content_length": preflight_record.get("content_length"),
                "http_status": 200,
                "attempt_count": 1,
                "fetch_timestamp": preflight_record.get("fetch_timestamp"),
                "validation": {
                    "mode": "source-register-proving-slice",
                    "passed": True,
                    "reason": "Synthetic proving artifact created from canonical row contract.",
                },
                "duplicate_of": preflight_record.get("duplicate_of"),
                "failure": None,
                "metadata": source.metadata,
            }
        )
    manifest_path = manifest_dir / f"download_{run_id}.jsonl"
    _write_jsonl(manifest_path, records)
    summary_path = run_dir / "summary.json"
    summary = {
        "run_id": run_id,
        "mode": "download",
        "manifest_path": str(manifest_path),
        "workbook_path": str(workbook_path),
        "workbook_sha256": workbook_sha256,
        "filtered_rows": len(records),
        "downloaded_existing_count": sum(
            1 for record in records if record["status"] == "downloaded_existing"
        ),
        "duplicate_url_count": sum(1 for record in records if record["status"] == "duplicate_url"),
        "validation_passed": True,
    }
    _write_json(summary_path, summary)
    return manifest_path


def _proving_fetcher(selected_rows: list):
    rows_by_url = {row.original_url: row for row in selected_rows}

    def fetcher(url, network, validation):  # noqa: ANN001, ARG001
        row = rows_by_url[url]
        return PreflightFetchResult(
            status="preflight_ok",
            http_status=200,
            final_url=url,
            redirect_chain=[],
            content_type=_content_type_for_parser(row.expected_parser),
            content_length=2048,
            method="HEAD",
            failure=None,
            validation={
                "mode": "source-register-proving-slice",
                "passed": True,
                "reason": None,
            },
            attempt_count=1,
        )

    return fetcher


def _write_latest_context(
    *,
    output_dir: Path,
    source_set_id: str,
    report_path: Path,
    catalog_dir: Path,
    source_catalog_path: Path,
    source_set_manifest_path: Path,
    authority_inventory_path: Path,
    source_addition_decisions_path: Path,
) -> None:
    context_path = output_dir / DEFAULT_LATEST_PROVING_CONTEXT_RELATIVE_PATH
    context_path.parent.mkdir(parents=True, exist_ok=True)
    _write_json(
        context_path,
        {
            "schema_version": LATEST_PROVING_CONTEXT_SCHEMA_VERSION,
            "source_set_id": source_set_id,
            "report_path": str(report_path),
            "catalog_dir": str(catalog_dir),
            "source_catalog_path": str(source_catalog_path),
            "source_set_manifest_path": str(source_set_manifest_path),
            "authority_inventory_path": str(authority_inventory_path),
            "source_addition_decisions_path": str(source_addition_decisions_path),
        },
    )


def _content_type_for_parser(expected_parser: str) -> str:
    parser_to_content_type = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "pdf": "application/pdf",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xml": "application/xml",
    }
    return parser_to_content_type.get(expected_parser, "application/octet-stream")


def _normalize_identity_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _read_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
