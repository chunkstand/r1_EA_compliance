from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from .catalog_surface import resolve_catalog_dir_for_source_set
from .authority_currentness_projection import _project_source_register_currentness_inputs
from .authority_currentness_validation import _summary, _validation
from .records import aliased_source_record_ids
from .records import sha256_file
from .source_partitions import ACTIVE_REVIEW_CORPUS
from .source_partitions import CURRENTNESS_SUPERSESSION_ARCHIVE
from .source_partitions import DEFAULT_SOURCE_PARTITION_CONTRACT_PATH
from .source_partitions import catalog_source_partition
from .source_partitions import catalog_source_partition_record
from .source_partitions import graph_relationships_for_family_source
from .source_partitions import load_source_partition_contract


AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION = "authority-currentness-report-v0"
DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
DEFAULT_SOURCE_ADDITION_DECISIONS_PATH = Path(
    "config/authority_source_addition_decisions_nepa_ea_v1.json"
)
DEFAULT_SOURCE_REGISTER_CURRENTNESS_LINEAGE_PATH = Path(
    "config/source_register_currentness_lineage_v1.json"
)
SUCCESSFUL_SOURCE_STATUSES = {
    "downloaded",
    "downloaded_existing",
    "duplicate_content",
    "duplicate_url",
}
EXCLUDED_SOURCE_STATUSES = {"skipped_excluded"}
FAILED_OR_UNVERIFIED_SOURCE_STATUSES = {
    "blocked",
    "challenge_page",
    "empty_body",
    "failed",
    "invalid_content",
    "not_found",
    "rate_limited",
    "ssl_error",
    "timeout",
    "unsupported_content_type",
}
NO_REPLACEMENT_LINEAGE_DISPOSITIONS = {
    "historical_no_replacement",
    "reserved_without_replacement",
    "revoked_without_replacement",
    "rescinded_without_replacement",
}


@dataclass(frozen=True)
class AuthorityCurrentnessResult:
    report_path: Path
    summary: dict


def build_authority_currentness_report(
    *,
    output_dir: Path,
    source_set_id: str | None = None,
    authority_inventory_path: Path = DEFAULT_AUTHORITY_INVENTORY_PATH,
    source_addition_decisions_path: Path = DEFAULT_SOURCE_ADDITION_DECISIONS_PATH,
    source_partition_contract_path: Path = DEFAULT_SOURCE_PARTITION_CONTRACT_PATH,
    catalog_path: Path | None = None,
    source_set_manifest_path: Path | None = None,
    output_path: Path | None = None,
) -> AuthorityCurrentnessResult:
    output_dir = Path(output_dir)
    authority_inventory_path = Path(authority_inventory_path)
    source_addition_decisions_path = Path(source_addition_decisions_path)
    source_partition_contract_path = Path(source_partition_contract_path)
    resolved_catalog_dir = _resolved_catalog_dir(
        output_dir=output_dir,
        source_set_id=source_set_id,
        catalog_path=catalog_path,
        source_set_manifest_path=source_set_manifest_path,
    )
    catalog_path = Path(catalog_path) if catalog_path else resolved_catalog_dir / "source_catalog.jsonl"
    source_set_manifest_path = (
        Path(source_set_manifest_path)
        if source_set_manifest_path
        else resolved_catalog_dir / "source_set_manifest.json"
    )

    inventory = _read_json(authority_inventory_path)
    source_addition_decisions = _read_source_addition_decisions(source_addition_decisions_path)
    source_partition_contract = load_source_partition_contract(source_partition_contract_path)
    manifest = _read_json(source_set_manifest_path)
    source_set_id = source_set_id or str(manifest["source_set_id"])
    catalog_rows = [
        row
        for row in _read_jsonl(catalog_path)
        if str(row.get("source_set_id") or source_set_id) == source_set_id
    ]
    projected_inputs = _project_source_register_currentness_inputs(
        output_dir=output_dir,
        source_set_id=source_set_id,
        manifest=manifest,
        catalog_rows=catalog_rows,
        authority_inventory_path=authority_inventory_path,
        source_addition_decisions_path=source_addition_decisions_path,
        lineage_path=DEFAULT_SOURCE_REGISTER_CURRENTNESS_LINEAGE_PATH,
    )
    if projected_inputs is not None:
        authority_inventory_path = projected_inputs["authority_inventory_path"]
        source_addition_decisions_path = projected_inputs["source_addition_decisions_path"]

    inventory = _read_json(authority_inventory_path)
    source_addition_decisions = _read_source_addition_decisions(source_addition_decisions_path)
    catalog_by_source_record_id = _catalog_rows_by_aliased_source_record_id(catalog_rows)
    decisions_by_family_id = {
        str(decision.get("authority_family_id") or ""): decision
        for decision in source_addition_decisions.get("decisions", [])
        if decision.get("authority_family_id")
    }
    catalog_source_partitions = [
        catalog_source_partition_record(row, source_partition_contract) for row in catalog_rows
    ]

    source_currentness_records = []
    family_currentness = []
    for family in inventory["authority_families"]:
        family_records = [
            _source_currentness_record(
                family=family,
                source_record_id=source_record_id,
                catalog_row=catalog_by_source_record_id.get(source_record_id),
                manifest=manifest,
                source_partition_contract=source_partition_contract,
            )
            for source_record_id in family.get("source_record_ids", [])
        ]
        source_currentness_records.extend(family_records)
        family_currentness.append(
            _family_currentness_record(
                family=family,
                source_records=family_records,
                catalog_by_source_record_id=catalog_by_source_record_id,
                source_addition_decision=decisions_by_family_id.get(family["family_id"]),
            )
        )
    temporal_lineage_records = _temporal_lineage_records(
        inventory=inventory,
        source_currentness_records=source_currentness_records,
    )

    validation = _validation(
        inventory=inventory,
        manifest=manifest,
        catalog_rows=catalog_rows,
        catalog_by_source_record_id=catalog_by_source_record_id,
        source_addition_decisions=source_addition_decisions,
        source_partition_contract=source_partition_contract,
        catalog_source_partitions=catalog_source_partitions,
        decisions_by_family_id=decisions_by_family_id,
        family_currentness=family_currentness,
        source_currentness_records=source_currentness_records,
        requested_source_set_id=source_set_id,
        failed_or_unverified_source_statuses=FAILED_OR_UNVERIFIED_SOURCE_STATUSES,
        excluded_source_statuses=EXCLUDED_SOURCE_STATUSES,
        successful_source_statuses=SUCCESSFUL_SOURCE_STATUSES,
    )
    summary = _summary(
        source_set_id=source_set_id,
        inventory=inventory,
        manifest=manifest,
        family_currentness=family_currentness,
        source_currentness_records=source_currentness_records,
        catalog_source_partitions=catalog_source_partitions,
        validation=validation,
        temporal_lineage_records=temporal_lineage_records,
    )

    if output_path is None:
        output_path = (
            output_dir
            / "derived"
            / source_set_id
            / "authority_currentness"
            / "authority_currentness_report.json"
        )
    output_path = Path(output_path)
    summary["report_path"] = str(output_path)
    report = {
        "schema_version": AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
        "created_at": summary["created_at"],
        "source_set_id": source_set_id,
        "inputs": {
            "authority_inventory_path": str(authority_inventory_path),
            "authority_inventory_sha256": sha256_file(authority_inventory_path)
            if authority_inventory_path.exists()
            else None,
            "source_addition_decisions_path": str(source_addition_decisions_path),
            "source_addition_decisions_sha256": sha256_file(source_addition_decisions_path)
            if source_addition_decisions_path.exists()
            else None,
            "source_partition_contract_path": str(source_partition_contract_path),
            "source_partition_contract_sha256": sha256_file(source_partition_contract_path)
            if source_partition_contract_path.exists()
            else None,
            "catalog_path": str(catalog_path),
            "catalog_sha256": sha256_file(catalog_path) if catalog_path.exists() else None,
            "source_set_manifest_path": str(source_set_manifest_path),
            "source_set_manifest_sha256": sha256_file(source_set_manifest_path)
            if source_set_manifest_path.exists()
            else None,
        },
        "source_partition_contract": source_partition_contract,
        "catalog_source_partitions": catalog_source_partitions,
        "source_addition_decisions": source_addition_decisions,
        "family_currentness": family_currentness,
        "source_currentness_records": source_currentness_records,
        "temporal_lineage_records": temporal_lineage_records,
        "validation": validation,
        "summary": summary,
    }
    _write_json(output_path, report)

    return AuthorityCurrentnessResult(report_path=output_path, summary=summary)


def _resolved_catalog_dir(
    *,
    output_dir: Path,
    source_set_id: str | None,
    catalog_path: Path | None,
    source_set_manifest_path: Path | None,
) -> Path:
    if catalog_path is not None:
        return Path(catalog_path).parent
    if source_set_manifest_path is not None:
        return Path(source_set_manifest_path).parent
    return resolve_catalog_dir_for_source_set(
        output_dir=output_dir,
        source_set_id=source_set_id,
    )


def _catalog_rows_by_aliased_source_record_id(catalog_rows: list[dict]) -> dict[str, dict]:
    rows_by_source_record_id = {
        str(row.get("source_record_id") or ""): row
        for row in catalog_rows
        if str(row.get("source_record_id") or "").strip()
    }
    for row in catalog_rows:
        source_record_id = str(row.get("source_record_id") or "").strip()
        if not source_record_id:
            continue
        for alias_source_record_id in aliased_source_record_ids([source_record_id]):
            rows_by_source_record_id.setdefault(alias_source_record_id, row)
    return rows_by_source_record_id


def _source_currentness_record(
    *,
    family: dict,
    source_record_id: str,
    catalog_row: dict | None,
    manifest: dict,
    source_partition_contract: dict,
) -> dict:
    family_id = family["family_id"]
    if catalog_row is None:
        return {
            "schema_version": AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
            "authority_family_id": family_id,
            "family_status": family["status"],
            "source_record_id": source_record_id,
            "source_title": None,
            "citation_label": None,
            "url": None,
            "effective_date": None,
            "capture_date": _capture_date({}, manifest),
            "supersession_status": "missing_catalog_record",
            "source_status": None,
            "currentness_status": "missing_catalog_record",
            "counts_as_current_authority": False,
            "document_role": None,
            "authority_level": None,
            "issuer": None,
            "scope": None,
            "currentness_notes": None,
            "artifact_path": None,
            "artifact_sha256": None,
            "source_partition": None,
            "source_partition_basis": "missing_catalog_record",
            "authority_family_source_role": "missing_catalog_record",
            "eligible_for_active_review_rules_for_family": False,
            "graph_allowed_relationships_for_family": [],
        }

    source_status = str(catalog_row.get("source_status") or "")
    supersession_status = _supersession_status(family=family, source_status=source_status)
    source_partition, source_partition_basis = catalog_source_partition(
        catalog_row,
        source_partition_contract,
    )
    currentness_status = _currentness_status(
        family=family,
        source_status=source_status,
        source_partition=source_partition,
    )
    (
        authority_family_source_role,
        eligible_for_active_review_rules_for_family,
        graph_allowed_relationships_for_family,
    ) = graph_relationships_for_family_source(
        family_status=str(family.get("status") or ""),
        source_partition=source_partition,
        source_status=source_status,
        contract=source_partition_contract,
    )
    counts_as_current_authority = (
        family.get("status") != "superseded"
        and source_status in SUCCESSFUL_SOURCE_STATUSES
        and source_partition == ACTIVE_REVIEW_CORPUS
    )
    supersession = _dict(family.get("supersession"))
    replacement_source_record_ids = _strings(supersession.get("current_source_record_ids"))
    temporal_lineage_disposition = (
        str(supersession.get("lineage_disposition") or "")
        if family.get("status") == "superseded"
        else _temporal_lineage_disposition(catalog_row)
    )
    temporal_lineage_basis = (
        str(supersession.get("lineage_basis") or "")
        if family.get("status") == "superseded"
        else _temporal_lineage_basis(catalog_row)
    )

    return {
        "schema_version": AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
        "authority_family_id": family_id,
        "family_status": family["status"],
        "source_record_id": source_record_id,
        "source_title": catalog_row.get("title"),
        "citation_label": catalog_row.get("citation_label"),
        "url": catalog_row.get("effective_url") or catalog_row.get("original_url"),
        "effective_date": _effective_date(catalog_row),
        "capture_date": _capture_date(catalog_row, manifest),
        "supersession_status": supersession_status,
        "source_status": source_status,
        "currentness_status": currentness_status,
        "counts_as_current_authority": counts_as_current_authority,
        "document_role": catalog_row.get("document_role"),
        "authority_level": catalog_row.get("authority_level"),
        "issuer": catalog_row.get("issuer"),
        "scope": catalog_row.get("scope"),
        "currentness_notes": catalog_row.get("currentness_notes"),
        "artifact_path": catalog_row.get("artifact_path"),
        "artifact_sha256": catalog_row.get("artifact_sha256"),
        "source_partition": source_partition,
        "source_partition_basis": source_partition_basis,
        "authority_family_source_role": authority_family_source_role,
        "eligible_for_active_review_rules_for_family": eligible_for_active_review_rules_for_family,
        "graph_allowed_relationships_for_family": graph_allowed_relationships_for_family,
        "replacement_source_record_ids": replacement_source_record_ids,
        "replacement_authority_family_id": supersession.get("replacement_family_id"),
        "temporal_lineage_disposition": temporal_lineage_disposition or None,
        "temporal_lineage_basis": temporal_lineage_basis or None,
    }


def _family_currentness_record(
    *,
    family: dict,
    source_records: list[dict],
    catalog_by_source_record_id: dict[str, dict],
    source_addition_decision: dict | None,
) -> dict:
    current_source_record_ids = [
        record["source_record_id"]
        for record in source_records
        if record["counts_as_current_authority"]
    ]
    excluded_source_record_ids = [
        record["source_record_id"]
        for record in source_records
        if record["source_status"] in EXCLUDED_SOURCE_STATUSES
    ]
    failed_source_record_ids = [
        record["source_record_id"]
        for record in source_records
        if record["currentness_status"] == "failed_or_unverified_capture"
    ]
    missing_catalog_record_ids = [
        record["source_record_id"]
        for record in source_records
        if record["currentness_status"] == "missing_catalog_record"
    ]
    source_addition_decision_status = (
        source_addition_decision.get("decision_status") if source_addition_decision else None
    )
    supersession = _dict(family.get("supersession"))
    replacement_source_record_ids = [
        source_record_id
        for source_record_id in _strings(supersession.get("current_source_record_ids"))
        if source_record_id in catalog_by_source_record_id
    ]
    has_lineage_metadata = _family_has_lineage_metadata(family)

    status = family["status"]
    if status == "candidate" and not family.get("source_record_ids"):
        if not source_addition_decision:
            currentness_status = "missing_source_addition_decision"
        elif _is_documented_source_gap_decision(source_addition_decision):
            currentness_status = "documented_source_gap"
        else:
            currentness_status = "documented_source_non_addition"
    elif status == "superseded":
        if failed_source_record_ids or missing_catalog_record_ids or not has_lineage_metadata:
            currentness_status = "superseded_source_gap"
        elif replacement_source_record_ids:
            currentness_status = "superseded_replacement_sources_confirmed"
        else:
            currentness_status = "superseded_no_replacement_confirmed"
    elif failed_source_record_ids or missing_catalog_record_ids:
        currentness_status = "source_currentness_failed"
    elif current_source_record_ids:
        currentness_status = "source_currentness_confirmed"
    else:
        currentness_status = "no_current_source_record"

    return {
        "schema_version": AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
        "authority_family_id": family["family_id"],
        "family_status": status,
        "source_record_count": len(source_records),
        "current_source_record_count": len(current_source_record_ids),
        "current_source_record_ids": current_source_record_ids,
        "excluded_source_record_count": len(excluded_source_record_ids),
        "excluded_source_record_ids": excluded_source_record_ids,
        "failed_source_record_count": len(failed_source_record_ids),
        "failed_source_record_ids": failed_source_record_ids,
        "missing_catalog_record_count": len(missing_catalog_record_ids),
        "missing_catalog_record_ids": missing_catalog_record_ids,
        "replacement_source_record_count": len(replacement_source_record_ids),
        "replacement_source_record_ids": replacement_source_record_ids,
        "currentness_status": currentness_status,
        "source_addition_decision_status": source_addition_decision_status,
        "open_inventory_gaps": family.get("open_inventory_gaps", []),
        "supersession": family.get("supersession"),
        "queue_source_ids": family.get("queue_source_ids", []),
    }


def _supersession_status(*, family: dict, source_status: str) -> str:
    if family.get("status") == "superseded":
        return "superseded_source_record"
    if source_status in EXCLUDED_SOURCE_STATUSES:
        return "excluded_no_current_authority"
    if source_status in FAILED_OR_UNVERIFIED_SOURCE_STATUSES:
        return "failed_or_unverified_capture"
    return "current_authoritative_source"


def _currentness_status(*, family: dict, source_status: str, source_partition: str) -> str:
    if source_status in EXCLUDED_SOURCE_STATUSES:
        return "excluded_no_artifact"
    if source_status not in SUCCESSFUL_SOURCE_STATUSES:
        return "failed_or_unverified_capture"
    if family.get("status") == "superseded":
        return "replacement_source_confirmed"
    if source_partition == CURRENTNESS_SUPERSESSION_ARCHIVE:
        return "currentness_archive_only"
    return "confirmed_from_catalog"


def _is_stale_milestone_2_gap(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return (
        value.startswith("Milestone 2 must confirm current authoritative source coverage")
        or value.startswith("Milestone 2 currentness validation must prevent")
    )


def _effective_date(row: dict) -> str | None:
    for field in ("effective_date", "publication_date", "last_modified"):
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            parsed = _parse_date(value.strip())
            if parsed:
                return parsed
    notes = row.get("currentness_notes")
    if isinstance(notes, str) and notes.strip():
        return _parse_date(notes.strip())
    return None


def _capture_date(row: dict, manifest: dict) -> str | None:
    for field in ("fetch_timestamp", "retrieved_at", "captured_at", "downloaded_at"):
        value = row.get(field)
        if isinstance(value, str) and value.strip():
            return value
    created_at = manifest.get("created_at")
    return str(created_at) if created_at else None


def _parse_date(value: str) -> str | None:
    iso_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", value)
    if iso_match:
        return iso_match.group(1)
    effective_match = re.search(
        r"\b(?:Effective|Published)\s+([A-Za-z]{3,9})\.?\s+(\d{1,2}),\s+(\d{4})\b",
        value,
        flags=re.IGNORECASE,
    )
    if effective_match:
        month_name, day, year = effective_match.groups()
        month = _MONTHS.get(month_name.lower().rstrip("."))
        if month:
            return f"{year}-{month:02d}-{int(day):02d}"
    return None


_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def _family_has_lineage_metadata(family: dict) -> bool:
    supersession = _dict(family.get("supersession"))
    replacement_source_record_ids = _strings(supersession.get("current_source_record_ids"))
    if replacement_source_record_ids and supersession.get("replacement_family_id"):
        return True
    return bool(
        str(supersession.get("lineage_disposition") or "") in NO_REPLACEMENT_LINEAGE_DISPOSITIONS
        and str(supersession.get("lineage_basis") or "").strip()
    )


def _is_documented_source_gap_decision(decision: dict) -> bool:
    decision_status = str(decision.get("decision_status") or "")
    if decision_status in {"direct_file_capture_required", "documented_source_gap"}:
        return True
    next_action = str(decision.get("next_action") or "").lower()
    return "capture" in next_action or "direct file" in next_action


def _temporal_lineage_disposition(row: dict) -> str:
    text = _row_text(row)
    if "retained/historical plan amendment" in text:
        return "historical_amendment"
    if "historical/current transition support" in text:
        return "historical_transition_support"
    if "retained/historical" in text:
        return "historical_no_replacement"
    if "revoked" in text:
        return "revoked_without_replacement"
    if "rescinded" in text:
        return "rescinded_without_replacement"
    if "reserved" in text:
        return "reserved_without_replacement"
    if "superseded" in text or "noncurrent" in text or "not current" in text:
        return "historical_no_replacement"
    return ""


def _temporal_lineage_basis(row: dict) -> str:
    notes = row.get("currentness_notes")
    if isinstance(notes, str) and notes.strip():
        return notes.strip()
    metadata_notes = _row_metadata(row).get("currentness_status")
    if isinstance(metadata_notes, str) and metadata_notes.strip():
        return metadata_notes.strip()
    return ""


def _temporal_lineage_records(*, inventory: dict, source_currentness_records: list[dict]) -> list[dict]:
    lineage_records = []
    family_by_id = {
        str(family.get("family_id") or ""): family for family in inventory.get("authority_families", [])
    }
    for record in source_currentness_records:
        lineage_disposition = str(record.get("temporal_lineage_disposition") or "")
        replacement_source_record_ids = _strings(record.get("replacement_source_record_ids"))
        if not lineage_disposition and not replacement_source_record_ids and not record.get("effective_date"):
            continue
        lineage_records.append(
            {
                "authority_family_id": record.get("authority_family_id"),
                "source_record_id": record.get("source_record_id"),
                "family_status": record.get("family_status"),
                "lineage_disposition": lineage_disposition or None,
                "lineage_basis": record.get("temporal_lineage_basis"),
                "effective_date": record.get("effective_date"),
                "replacement_source_record_ids": replacement_source_record_ids,
                "replacement_authority_family_id": record.get("replacement_authority_family_id"),
            }
        )
    for family in family_by_id.values():
        if family.get("status") != "candidate" or not family.get("queue_source_ids"):
            continue
        lineage_records.append(
            {
                "authority_family_id": family.get("family_id"),
                "queue_source_ids": _strings(family.get("queue_source_ids")),
                "family_status": family.get("status"),
                "lineage_disposition": "direct_file_capture_required",
                "lineage_basis": "; ".join(_strings(family.get("open_inventory_gaps"))),
                "effective_date": None,
                "replacement_source_record_ids": [],
                "replacement_authority_family_id": None,
            }
        )
    return lineage_records


def _read_source_addition_decisions(path: Path) -> dict:
    if not path.exists():
        return {"schema_version": None, "decisions": []}
    decisions = _read_json(path)
    decisions.setdefault("decisions", [])
    return decisions


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _row_text(row: dict) -> str:
    fields: list[str] = []
    for field in (
        "title",
        "document_type",
        "currentness_notes",
        "layer",
        "effective_url",
        "original_url",
    ):
        value = row.get(field)
        if isinstance(value, str):
            fields.append(value)
    metadata = _row_metadata(row)
    for field in (
        "title",
        "document_type",
        "authority_tier",
        "currentness_status",
        "currentness_notes",
        "source_currentness_status",
        "supersession_status",
        "workbook_url",
    ):
        value = metadata.get(field)
        if isinstance(value, str):
            fields.append(value)
    return " ".join(fields).lower()


def _row_metadata(row: dict) -> dict:
    metadata = row.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]
