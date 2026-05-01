from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import json

from .forest_plan_resolver import CUSTER_GALLATIN_REQUIRED_SOURCE_IDS


REUSE_INVENTORY_SCHEMA_VERSION = "reuse-inventory-v0"
EXTRACTION_REUSE_CLASSIFICATIONS = {
    "already_current",
    "already_current_cg_slice",
    "excluded",
    "needs_extract",
    "reuse_extraction",
}


@dataclass(frozen=True)
class ReuseInventoryResult:
    source_set_id: str
    inventory_dir: Path
    inventory_path: Path
    records_path: Path
    summary_path: Path
    summary: dict


def build_reuse_inventory(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    previous_source_set_ids: list[str] | None = None,
    catalog_path: Path | None = None,
    verify_artifact_hashes: bool = True,
) -> ReuseInventoryResult:
    """Inventory extraction reuse opportunities for the current source set."""

    output_dir = Path(output_dir)
    catalog_dir = output_dir / "catalog"
    source_set_manifest_path = catalog_dir / "source_set_manifest.json"
    if source_set_id is None:
        source_set_id = _read_json(source_set_manifest_path)["source_set_id"]
    catalog_path = Path(catalog_path) if catalog_path else catalog_dir / "source_catalog.jsonl"
    catalog_rows = [
        row
        for row in _read_jsonl(catalog_path)
        if str(row.get("source_set_id") or source_set_id) == source_set_id
    ]

    derived_dir = output_dir / "derived"
    current_records = _load_manifest_by_source_id(
        derived_dir / source_set_id / "diagnostics" / "extraction_manifest.jsonl"
    )
    previous_source_set_ids = previous_source_set_ids or _discover_previous_source_sets(
        derived_dir,
        source_set_id,
    )
    previous_records = _load_previous_manifests(derived_dir, previous_source_set_ids)

    records = [
        _inventory_record(
            row=row,
            output_dir=output_dir,
            current_source_set_id=source_set_id,
            current_extraction=current_records.get(str(row.get("source_record_id") or "")),
            prior_extractions=previous_records.get(str(row.get("source_record_id") or ""), []),
            verify_artifact_hashes=verify_artifact_hashes,
        )
        for row in catalog_rows
    ]
    summary = _summary(
        source_set_id=source_set_id,
        catalog_path=catalog_path,
        catalog_rows=catalog_rows,
        records=records,
        previous_source_set_ids=previous_source_set_ids,
        current_records=current_records,
        verify_artifact_hashes=verify_artifact_hashes,
    )

    inventory_dir = derived_dir / source_set_id / "reuse_inventory"
    inventory_path = inventory_dir / "reuse_inventory.json"
    records_path = inventory_dir / "reuse_inventory_records.jsonl"
    summary_path = inventory_dir / "summary.json"
    summary["inventory_path"] = str(inventory_path)
    summary["records_path"] = str(records_path)
    summary["summary_path"] = str(summary_path)
    inventory = {
        "schema_version": REUSE_INVENTORY_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "summary": summary,
        "records": records,
    }
    inventory_dir.mkdir(parents=True, exist_ok=True)
    _write_json(inventory_path, inventory)
    _write_jsonl(records_path, records)
    _write_json(summary_path, summary)

    return ReuseInventoryResult(
        source_set_id=source_set_id,
        inventory_dir=inventory_dir,
        inventory_path=inventory_path,
        records_path=records_path,
        summary_path=summary_path,
        summary=summary,
    )


def _inventory_record(
    *,
    row: dict,
    output_dir: Path,
    current_source_set_id: str,
    current_extraction: dict | None,
    prior_extractions: list[dict],
    verify_artifact_hashes: bool,
) -> dict:
    source_record_id = str(row.get("source_record_id") or "")
    artifact_check = _artifact_check(
        row=row,
        output_dir=output_dir,
        verify_artifact_hashes=verify_artifact_hashes,
    )
    if _is_excluded(row):
        classification = "excluded"
        reason = "scope_excluded"
        current_match = None
        reuse_candidate = None
        candidate_failures: list[dict] = []
    else:
        current_match = _valid_extraction(
            catalog_row=row,
            record=current_extraction,
            output_dir=output_dir,
            expected_source_set_id=current_source_set_id,
        )
        if current_match["valid"]:
            if source_record_id in CUSTER_GALLATIN_REQUIRED_SOURCE_IDS:
                classification = "already_current_cg_slice"
                reason = "current_custer_gallatin_slice_has_matching_extraction"
            else:
                classification = "already_current"
                reason = "current_source_set_has_matching_extraction"
            reuse_candidate = None
            candidate_failures = []
        elif not artifact_check["passed"]:
            classification = "needs_extract"
            reason = artifact_check["reason"]
            reuse_candidate = None
            candidate_failures = []
        else:
            reuse_candidate, candidate_failures = _best_reuse_candidate(
                catalog_row=row,
                prior_extractions=prior_extractions,
                output_dir=output_dir,
            )
            if reuse_candidate is not None:
                classification = "reuse_extraction"
                reason = "prior_extraction_matches_source_id_artifact_and_text_hash"
            else:
                classification = "needs_extract"
                reason = "no_valid_prior_extraction"

    if classification not in EXTRACTION_REUSE_CLASSIFICATIONS:
        raise AssertionError(f"Unsupported reuse classification: {classification}")
    return {
        "schema_version": REUSE_INVENTORY_SCHEMA_VERSION,
        "source_record_id": source_record_id,
        "title": row.get("title"),
        "source_set_id": current_source_set_id,
        "source_status": row.get("source_status"),
        "scope": row.get("scope"),
        "document_role": row.get("document_role"),
        "authority_level": row.get("authority_level"),
        "expected_parser": row.get("expected_parser"),
        "content_type": row.get("content_type"),
        "artifact_path": row.get("artifact_path"),
        "artifact_sha256": row.get("artifact_sha256"),
        "artifact_byte_size": row.get("artifact_byte_size"),
        "classification": classification,
        "reason": reason,
        "artifact_check": artifact_check,
        "current_extraction": _candidate_payload(current_match["record"])
        if current_match and current_match.get("record")
        else None,
        "current_extraction_valid": bool(current_match and current_match["valid"]),
        "current_extraction_failures": current_match.get("failures", []) if current_match else [],
        "reuse_candidate": _candidate_payload(reuse_candidate) if reuse_candidate else None,
        "candidate_failures": candidate_failures,
    }


def _best_reuse_candidate(
    *,
    catalog_row: dict,
    prior_extractions: list[dict],
    output_dir: Path,
) -> tuple[dict | None, list[dict]]:
    failures = []
    for candidate in sorted(
        prior_extractions,
        key=lambda item: (
            str(item.get("source_set_id") or ""),
            str(item.get("extracted_at") or ""),
        ),
        reverse=True,
    ):
        validation = _valid_extraction(
            catalog_row=catalog_row,
            record=candidate,
            output_dir=output_dir,
            expected_source_set_id=None,
        )
        if validation["valid"]:
            return candidate, failures
        failures.append(
            {
                "source_set_id": candidate.get("source_set_id"),
                "text_path": candidate.get("text_path"),
                "failures": validation["failures"],
            }
        )
    return None, failures[:5]


def _valid_extraction(
    *,
    catalog_row: dict,
    record: dict | None,
    output_dir: Path,
    expected_source_set_id: str | None,
) -> dict:
    failures = []
    if not record:
        return {"valid": False, "record": None, "failures": ["missing_extraction_record"]}
    if expected_source_set_id and record.get("source_set_id") != expected_source_set_id:
        failures.append("source_set_mismatch")
    for field in ("source_record_id", "artifact_sha256", "expected_parser", "content_type"):
        expected = catalog_row.get(field)
        actual = record.get(field)
        if expected is not None and actual is not None and str(expected) != str(actual):
            failures.append(f"{field}_mismatch")
    if record.get("status") != "extracted":
        failures.append("status_not_extracted")
    if int(record.get("chunk_count") or 0) <= 0:
        failures.append("missing_chunks")
    text_path = _resolve_path(record.get("text_path"), output_dir)
    if text_path is None or not text_path.exists():
        failures.append("text_path_missing")
    elif record.get("text_sha256"):
        actual_text_sha = _sha256_extracted_text(text_path)
        if actual_text_sha != record.get("text_sha256"):
            failures.append("text_sha256_mismatch")
    return {"valid": not failures, "record": record, "failures": failures}


def _artifact_check(*, row: dict, output_dir: Path, verify_artifact_hashes: bool) -> dict:
    if _is_excluded(row):
        return {"passed": True, "reason": "scope_excluded", "path_exists": False}
    artifact_path = _resolve_path(row.get("artifact_path"), output_dir)
    if artifact_path is None:
        return {"passed": False, "reason": "artifact_path_missing", "path_exists": False}
    if not artifact_path.exists():
        return {
            "passed": False,
            "reason": "artifact_file_missing",
            "path": str(artifact_path),
            "path_exists": False,
        }
    expected_sha = row.get("artifact_sha256")
    actual_sha = None
    if verify_artifact_hashes and expected_sha:
        actual_sha = _sha256_file(artifact_path)
        if actual_sha != expected_sha:
            return {
                "passed": False,
                "reason": "artifact_sha256_mismatch",
                "path": str(artifact_path),
                "path_exists": True,
                "expected_sha256": expected_sha,
                "actual_sha256": actual_sha,
            }
    expected_size = row.get("artifact_byte_size")
    actual_size = artifact_path.stat().st_size
    size_matches = expected_size is None or int(expected_size) == actual_size
    return {
        "passed": size_matches,
        "reason": "ok" if size_matches else "artifact_byte_size_mismatch",
        "path": str(artifact_path),
        "path_exists": True,
        "expected_sha256": expected_sha,
        "actual_sha256": actual_sha,
        "expected_byte_size": expected_size,
        "actual_byte_size": actual_size,
    }


def _candidate_payload(record: dict | None) -> dict | None:
    if not record:
        return None
    return {
        "source_set_id": record.get("source_set_id"),
        "status": record.get("status"),
        "source_record_id": record.get("source_record_id"),
        "artifact_sha256": record.get("artifact_sha256"),
        "expected_parser": record.get("expected_parser"),
        "content_type": record.get("content_type"),
        "parser_name": record.get("parser_name"),
        "parser_version": record.get("parser_version"),
        "parser_metadata": record.get("parser_metadata"),
        "chunk_count": record.get("chunk_count"),
        "text_path": record.get("text_path"),
        "text_sha256": record.get("text_sha256"),
        "docling_json_path": record.get("docling_json_path"),
        "extracted_at": record.get("extracted_at"),
    }


def _summary(
    *,
    source_set_id: str,
    catalog_path: Path,
    catalog_rows: list[dict],
    records: list[dict],
    previous_source_set_ids: list[str],
    current_records: dict[str, dict],
    verify_artifact_hashes: bool,
) -> dict:
    counts = Counter(record["classification"] for record in records)
    artifact_failures = [
        record["source_record_id"]
        for record in records
        if record["classification"] != "excluded" and not record["artifact_check"]["passed"]
    ]
    return {
        "schema_version": REUSE_INVENTORY_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "catalog_path": str(catalog_path),
        "catalog_source_count": len(catalog_rows),
        "artifact_bearing_source_count": sum(0 if _is_excluded(row) else 1 for row in catalog_rows),
        "current_extraction_record_count": len(current_records),
        "previous_source_set_ids": previous_source_set_ids,
        "previous_source_set_count": len(previous_source_set_ids),
        "classification_counts": dict(sorted(counts.items())),
        "already_current_count": counts["already_current"] + counts["already_current_cg_slice"],
        "reuse_extraction_count": counts["reuse_extraction"],
        "needs_extract_count": counts["needs_extract"],
        "excluded_count": counts["excluded"],
        "artifact_failure_count": len(artifact_failures),
        "artifact_failure_source_record_ids": artifact_failures[:50],
        "verify_artifact_hashes": verify_artifact_hashes,
    }


def _discover_previous_source_sets(derived_dir: Path, current_source_set_id: str) -> list[str]:
    if not derived_dir.exists():
        return []
    source_set_ids = []
    for path in sorted(derived_dir.iterdir()):
        if not path.is_dir() or path.name == current_source_set_id:
            continue
        if (path / "diagnostics" / "extraction_manifest.jsonl").exists():
            source_set_ids.append(path.name)
    return source_set_ids


def _load_previous_manifests(
    derived_dir: Path,
    previous_source_set_ids: list[str],
) -> dict[str, list[dict]]:
    records_by_source_id: dict[str, list[dict]] = defaultdict(list)
    for previous_source_set_id in previous_source_set_ids:
        manifest_path = (
            derived_dir / previous_source_set_id / "diagnostics" / "extraction_manifest.jsonl"
        )
        for record in _read_jsonl(manifest_path):
            source_record_id = str(record.get("source_record_id") or "")
            if source_record_id:
                records_by_source_id[source_record_id].append(record)
    return records_by_source_id


def _load_manifest_by_source_id(manifest_path: Path) -> dict[str, dict]:
    records = {}
    for record in _read_jsonl(manifest_path):
        source_record_id = str(record.get("source_record_id") or "")
        if source_record_id:
            records[source_record_id] = record
    return records


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
        encoding="utf-8",
    )


def _resolve_path(value: object, output_dir: Path) -> Path | None:
    if not value:
        return None
    path = Path(str(value))
    if path.is_absolute():
        return path
    return output_dir.parent / path


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_extracted_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_excluded(row: dict) -> bool:
    return row.get("source_status") == "skipped_excluded"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
