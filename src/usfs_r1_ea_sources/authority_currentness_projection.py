from __future__ import annotations

from pathlib import Path
import json
import re

from .records import slugify
from .source_register import read_source_register_tables


NO_REPLACEMENT_LINEAGE_DISPOSITIONS = {
    "historical_no_replacement",
    "reserved_without_replacement",
    "revoked_without_replacement",
    "rescinded_without_replacement",
}
PROJECTED_AUTHORITY_INVENTORY_SCHEMA_VERSION = "source-register-authority-inventory-v1"
PROJECTED_SOURCE_ADDITION_DECISIONS_SCHEMA_VERSION = (
    "source-register-source-addition-decisions-v1"
)


def _project_source_register_currentness_inputs(
    *,
    output_dir: Path,
    source_set_id: str,
    manifest: dict,
    catalog_rows: list[dict],
    authority_inventory_path: Path,
    source_addition_decisions_path: Path,
    lineage_path: Path,
) -> dict | None:
    if not _should_project_source_register_currentness_inputs(
        authority_inventory_path=authority_inventory_path,
        source_addition_decisions_path=source_addition_decisions_path,
        catalog_rows=catalog_rows,
    ):
        return None
    queue_rows = _source_register_queue_rows(manifest)
    lineage = _read_json(lineage_path) if lineage_path.exists() else {"lineage_rules": []}
    inventory = _build_projected_source_register_authority_inventory(
        source_set_id=source_set_id,
        manifest=manifest,
        catalog_rows=catalog_rows,
        queue_rows=queue_rows,
        lineage=lineage,
    )
    decisions = _build_projected_source_register_source_addition_decisions(
        authority_families=inventory["authority_families"],
        queue_rows=queue_rows,
        manifest=manifest,
    )
    projection_dir = output_dir / "derived" / source_set_id / "authority_currentness"
    projected_inventory_path = projection_dir / "authority_inventory_projected.json"
    projected_decisions_path = projection_dir / "source_addition_decisions_projected.json"
    _write_json(projected_inventory_path, inventory)
    _write_json(projected_decisions_path, decisions)
    return {
        "authority_inventory_path": projected_inventory_path,
        "source_addition_decisions_path": projected_decisions_path,
    }


def _should_project_source_register_currentness_inputs(
    *,
    authority_inventory_path: Path,
    source_addition_decisions_path: Path,
    catalog_rows: list[dict],
) -> bool:
    return (
        authority_inventory_path == Path("config/authority_universe_families_nepa_ea_v1.json")
        and source_addition_decisions_path == Path("config/authority_source_addition_decisions_nepa_ea_v1.json")
        and _catalog_uses_source_register_contract(catalog_rows)
    )


def _catalog_uses_source_register_contract(catalog_rows: list[dict]) -> bool:
    return any(
        str(_row_metadata(row).get("loader_contract") or "") == "source_register_v1"
        for row in catalog_rows
    )


def _build_projected_source_register_authority_inventory(
    *,
    source_set_id: str,
    manifest: dict,
    catalog_rows: list[dict],
    queue_rows: list[dict],
    lineage: dict,
) -> dict:
    lineage_by_source_record_id = {
        str(entry.get("source_record_id") or ""): entry
        for entry in _dict_list(lineage.get("lineage_rules"))
        if entry.get("source_record_id")
    }
    grouped_families: dict[str, dict] = {}
    family_id_by_source_record_id: dict[str, str] = {}
    for row in catalog_rows:
        source_record_id = str(row.get("source_record_id") or "")
        if not source_record_id:
            continue
        metadata = _row_metadata(row)
        authority_document_id = str(metadata.get("authority_document_id") or source_record_id)
        family_id = _source_register_family_id(authority_document_id)
        family = grouped_families.setdefault(
            family_id,
            {
                "family_id": family_id,
                "name": str(row.get("title") or authority_document_id),
                "authority_category": metadata.get("authority_document_class_id"),
                "authority_document_ids": set(),
                "source_record_ids": [],
                "status_values": set(),
                "open_inventory_gaps": [],
            },
        )
        family["authority_document_ids"].add(authority_document_id)
        family["source_record_ids"].append(source_record_id)
        family["status_values"].add(
            _source_register_family_status(
                row=row,
                lineage_rule=lineage_by_source_record_id.get(source_record_id),
            )
        )
        family_id_by_source_record_id[source_record_id] = family_id

    authority_families = []
    for family in grouped_families.values():
        status_values = set(family.pop("status_values"))
        if "superseded" in status_values:
            status = "superseded"
        elif status_values == {"out_of_scope"}:
            status = "out_of_scope"
        else:
            status = "active"
        record = {
            "family_id": family["family_id"],
            "name": family["name"],
            "status": status,
            "authority_category": family["authority_category"],
            "authority_document_ids": sorted(family["authority_document_ids"]),
            "source_record_ids": list(family["source_record_ids"]),
            "open_inventory_gaps": list(family["open_inventory_gaps"]),
        }
        if status == "superseded":
            lineage_rule = None
            for source_record_id in record["source_record_ids"]:
                if source_record_id in lineage_by_source_record_id:
                    lineage_rule = lineage_by_source_record_id[source_record_id]
                    break
            supersession = {
                "lineage_disposition": str(
                    _dict(lineage_rule).get("lineage_disposition") or "historical_no_replacement"
                ),
                "lineage_basis": str(
                    _dict(lineage_rule).get("lineage_basis")
                    or "Canonical source register marks this source as superseded or historical currentness evidence."
                ),
            }
            replacement_source_record_ids = _strings(
                _dict(lineage_rule).get("replacement_source_record_ids")
            )
            if replacement_source_record_ids:
                supersession["current_source_record_ids"] = replacement_source_record_ids
                replacement_family_ids = sorted(
                    {
                        family_id_by_source_record_id[source_record_id]
                        for source_record_id in replacement_source_record_ids
                        if source_record_id in family_id_by_source_record_id
                    }
                )
                if replacement_family_ids:
                    supersession["replacement_family_id"] = replacement_family_ids[0]
            record["supersession"] = supersession
            if not _family_has_lineage_metadata(record):
                record["open_inventory_gaps"].append(
                    "Superseded canonical family is missing governed lineage metadata."
                )
        authority_families.append(record)

    for queue_row in queue_rows:
        source_id = str(queue_row.get("Source_ID") or "").strip()
        if not source_id:
            continue
        authority_families.append(
            {
                "family_id": _queue_family_id(source_id),
                "name": str(queue_row.get("Document_Title") or source_id),
                "status": "candidate",
                "authority_category": "direct_file_capture_queue",
                "authority_document_ids": [],
                "source_record_ids": [],
                "queue_source_ids": [source_id],
                "open_inventory_gaps": [
                    value
                    for value in (
                        str(queue_row.get("Queue_Reason") or "").strip() or None,
                        str(queue_row.get("Resolution_Required") or "").strip() or None,
                    )
                    if value
                ],
            }
        )

    return {
        "schema_version": PROJECTED_AUTHORITY_INVENTORY_SCHEMA_VERSION,
        "authority_universe_family_inventory_id": f"projected-{source_set_id}",
        "source_set": {"source_set_id": source_set_id},
        "summary": {
            "authority_family_count": len(authority_families),
            "families_requiring_milestone_2_source_currentness": 0,
            "canonical_catalog_source_count": len(catalog_rows),
            "queue_candidate_family_count": sum(
                1 for family in authority_families if family.get("status") == "candidate"
            ),
            "projection_basis": "source_register_v1_catalog_and_queue_rows",
            "workbook_path": manifest.get("workbook_path"),
        },
        "authority_families": authority_families,
    }


def _build_projected_source_register_source_addition_decisions(
    *,
    authority_families: list[dict],
    queue_rows: list[dict],
    manifest: dict,
) -> dict:
    queue_row_by_source_id = {
        str(row.get("Source_ID") or "").strip(): row
        for row in queue_rows
        if str(row.get("Source_ID") or "").strip()
    }
    decisions = []
    decision_date = _manifest_date(manifest)
    for family in authority_families:
        if family.get("status") != "candidate":
            continue
        queue_source_ids = _strings(family.get("queue_source_ids"))
        if not queue_source_ids:
            continue
        queue_row = queue_row_by_source_id.get(queue_source_ids[0], {})
        decisions.append(
            {
                "authority_family_id": family["family_id"],
                "decision_date": decision_date,
                "decision_status": "direct_file_capture_required",
                "family_status_at_decision": "candidate",
                "next_action": str(queue_row.get("Resolution_Required") or "").strip() or None,
                "rationale": str(
                    queue_row.get("Queue_Reason")
                    or queue_row.get("Validation_Status")
                    or queue_row.get("Notes")
                    or "Direct file capture is required before the family can become load-ready."
                ).strip(),
                "recommended_source_records": [
                    {
                        "title": str(queue_row.get("Document_Title") or queue_source_ids[0]),
                        "official_url": str(queue_row.get("Source_URL") or "").strip() or None,
                        "issuer": str(queue_row.get("Issuing_Entity") or "").strip() or None,
                        "authority_level": str(queue_row.get("Authority_Tier") or "").strip().lower()
                        or None,
                        "document_role": "direct_file_capture_required",
                        "recommended_scope": "Conditional",
                    }
                ],
            }
        )
    return {
        "schema_version": PROJECTED_SOURCE_ADDITION_DECISIONS_SCHEMA_VERSION,
        "authority_inventory_id": f"projected-{manifest.get('source_set_id')}",
        "as_of_date": decision_date,
        "decisions": decisions,
        "summary": {
            "decision_count": len(decisions),
            "documented_non_addition_count": 0,
            "documented_source_gap_count": len(decisions),
            "recommended_source_record_count": len(decisions),
        },
    }


def _source_register_queue_rows(manifest: dict) -> list[dict]:
    workbook_path = manifest.get("workbook_path")
    if not workbook_path:
        return []
    path = Path(str(workbook_path))
    if not path.exists():
        return []
    tables = read_source_register_tables(path)
    queue_table = tables.get("Direct_File_Capture_Queue")
    if not isinstance(queue_table, dict):
        return []
    rows = queue_table.get("rows")
    return rows if isinstance(rows, list) else []


def _source_register_family_id(authority_document_id: str) -> str:
    return f"authority_family:{slugify(authority_document_id, max_length=96)}"


def _queue_family_id(source_id: str) -> str:
    return f"authority_family:queue:{slugify(source_id, max_length=96)}"


def _source_register_family_status(*, row: dict, lineage_rule: dict | None) -> str:
    metadata = _row_metadata(row)
    if lineage_rule or str(metadata.get("authority_tier") or "") == "Superseded":
        return "superseded"
    if _temporal_lineage_disposition(row) in {
        "historical_amendment",
        "historical_transition_support",
        "historical_no_replacement",
    }:
        return "out_of_scope"
    return "active"


def _family_has_lineage_metadata(family: dict) -> bool:
    supersession = _dict(family.get("supersession"))
    replacement_source_record_ids = _strings(supersession.get("current_source_record_ids"))
    if replacement_source_record_ids and supersession.get("replacement_family_id"):
        return True
    return bool(
        str(supersession.get("lineage_disposition") or "") in NO_REPLACEMENT_LINEAGE_DISPOSITIONS
        and str(supersession.get("lineage_basis") or "").strip()
    )


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


def _manifest_date(manifest: dict) -> str:
    created_at = str(manifest.get("created_at") or "")
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", created_at)
    if match:
        return match.group(1)
    return _utc_now()[:10]


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def _dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _utc_now() -> str:
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
