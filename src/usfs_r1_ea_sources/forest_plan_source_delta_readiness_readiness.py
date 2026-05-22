from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import sqlite3

from .forest_plan_profiles import load_forest_plan_profiles
from .forest_plan_source_delta_readiness_io import _read_json_if_exists
from .forest_plan_source_delta_readiness_io import _read_jsonl_if_exists
from .workbook import R1ForestPlanDocumentRegister

def _extraction_readiness(
    *,
    output_dir: Path,
    source_set_id: str,
    expected_source_ids: set[str],
    reuse_inventory_path: Path | None = None,
) -> dict[str, Any]:
    derived_dir = output_dir / "derived" / source_set_id if source_set_id else output_dir / "derived"
    manifest_path = derived_dir / "diagnostics" / "extraction_manifest.jsonl"
    validation_path = derived_dir / "diagnostics" / "extraction_validation.json"
    summary_path = derived_dir / "diagnostics" / "summary.json"
    chunks_path = derived_dir / "chunks" / "chunks.jsonl"
    manifest_records = _read_jsonl_if_exists(manifest_path)
    summary = _read_json_if_exists(summary_path)
    expected_records = [
        record
        for record in manifest_records
        if str(record.get("source_record_id") or "") in expected_source_ids
    ]
    accounted_source_ids = {
        str(record.get("source_record_id") or "") for record in expected_records
    }
    missing_source_ids = sorted(expected_source_ids - accounted_source_ids)
    status_counts = Counter(str(record.get("status") or "") for record in expected_records)
    blocked_records = [
        record
        for record in expected_records
        if record.get("status") != "extracted"
        and record.get("source_status") not in {"skipped_excluded"}
    ]
    blocked_status_counts = Counter(str(record.get("status") or "") for record in blocked_records)
    blocker_error_class_counts = Counter(
        str((record.get("failure") or {}).get("error_class") or "")
        for record in blocked_records
        if (record.get("failure") or {}).get("error_class")
    )
    nonterminal_source_ids = sorted(
        record.get("source_record_id")
        for record in expected_records
        if record.get("status") not in {
            "extracted",
            "skipped_excluded",
            "no_artifact",
            "artifact_missing",
            "hash_mismatch",
            "parser_error",
            "parser_timeout",
            "empty_text",
        }
    )
    extracted_without_chunks = sorted(
        str(record.get("source_record_id") or "")
        for record in expected_records
        if record.get("status") == "extracted" and int(record.get("chunk_count") or 0) <= 0
    )
    extracted_without_text = sorted(
        str(record.get("source_record_id") or "")
        for record in expected_records
        if record.get("status") == "extracted" and int(record.get("text_char_count") or 0) <= 0
    )
    validation = _read_json_if_exists(validation_path)
    status = "not_started"
    if manifest_path.exists() or chunks_path.exists() or validation_path.exists():
        if (
            not missing_source_ids
            and not nonterminal_source_ids
            and not extracted_without_chunks
            and not extracted_without_text
        ):
            status = "ready_with_blockers" if blocked_records else "ready"
        else:
            status = "partial"
    reuse_inventory = _reuse_inventory_readiness(
        path=reuse_inventory_path,
        expected_source_ids=expected_source_ids,
        expected_source_set_id=source_set_id,
    )
    return {
        "status": status,
        "source_set_id": source_set_id or None,
        "extraction_manifest_path": str(manifest_path),
        "extraction_manifest_exists": manifest_path.exists(),
        "extraction_validation_path": str(validation_path),
        "extraction_validation_exists": validation_path.exists(),
        "extraction_validation_passed": bool(validation.get("passed")),
        "extraction_summary_path": str(summary_path),
        "extraction_summary_exists": summary_path.exists(),
        "extraction_summary": summary or None,
        "chunks_path": str(chunks_path),
        "chunks_exists": chunks_path.exists(),
        "manifest_record_count_for_expected_sources": len(expected_records),
        "status_counts": dict(status_counts),
        "extracted_source_record_count": status_counts.get("extracted", 0),
        "blocked_source_record_count": len(blocked_records),
        "blocked_status_counts": dict(blocked_status_counts),
        "blocker_error_class_counts": {
            key: count for key, count in blocker_error_class_counts.items() if key
        },
        "blocked_source_record_ids_sample": [
            str(record.get("source_record_id") or "") for record in blocked_records[:20]
        ],
        "expected_source_record_count": len(expected_source_ids),
        "coverage_complete": not missing_source_ids
        and not nonterminal_source_ids
        and not extracted_without_chunks
        and not extracted_without_text,
        "missing_source_record_count": len(missing_source_ids),
        "missing_source_record_ids_sample": missing_source_ids[:20],
        "nonterminal_source_record_ids": nonterminal_source_ids[:20],
        "extracted_without_chunks_source_record_ids": extracted_without_chunks[:20],
        "extracted_without_text_source_record_ids": extracted_without_text[:20],
        "reuse_inventory": reuse_inventory,
    }

def _retrieval_readiness(
    *,
    output_dir: Path,
    source_set_id: str,
    register: R1ForestPlanDocumentRegister,
    expected_source_ids: set[str],
) -> dict[str, Any]:
    derived_dir = output_dir / "derived" / source_set_id if source_set_id else output_dir / "derived"
    diagnostics_dir = derived_dir / "diagnostics"
    retrieval_dir = derived_dir / "retrieval"
    index_path = retrieval_dir / "evidence_index.sqlite"
    validation_path = retrieval_dir / "retrieval_validation.json"
    summary_path = retrieval_dir / "summary.json"
    eval_path = retrieval_dir / "retrieval_eval_results.json"
    extraction_manifest_path = diagnostics_dir / "extraction_manifest.jsonl"
    validation = _read_json_if_exists(validation_path)
    eval_results = _read_json_if_exists(eval_path)
    manifest_records = _read_jsonl_if_exists(extraction_manifest_path)
    extracted_source_ids = {
        str(record.get("source_record_id") or "")
        for record in manifest_records
        if str(record.get("source_record_id") or "") in expected_source_ids
        and str(record.get("status") or "") == "extracted"
    }
    indexed_source_ids = _retrieval_index_source_ids(index_path, expected_source_ids)
    missing_indexed_extracted_source_ids = sorted(extracted_source_ids - indexed_source_ids)
    upstream_blocked_source_ids = sorted(expected_source_ids - extracted_source_ids)
    coverage_by_unit = _retrieval_coverage_by_unit(
        register=register,
        expected_source_ids=expected_source_ids,
        extracted_source_ids=extracted_source_ids,
        indexed_source_ids=indexed_source_ids,
    )
    started = index_path.exists() or validation_path.exists() or summary_path.exists() or eval_path.exists()
    status = "not_started"
    if started:
        validation_passed = bool(validation.get("passed"))
        eval_passed = bool(eval_results.get("passed"))
        if validation_passed and eval_passed and not missing_indexed_extracted_source_ids:
            status = "ready_with_blockers" if upstream_blocked_source_ids else "ready"
        else:
            status = "partial"
    return {
        "started": started,
        "status": status,
        "source_set_id": source_set_id or None,
        "index_path": str(index_path),
        "index_exists": index_path.exists(),
        "retrieval_validation_path": str(validation_path),
        "retrieval_validation_exists": validation_path.exists(),
        "retrieval_validation_passed": bool(validation.get("passed")),
        "retrieval_summary_path": str(summary_path),
        "retrieval_summary_exists": summary_path.exists(),
        "retrieval_summary": _read_json_if_exists(summary_path) or None,
        "retrieval_eval_path": str(eval_path),
        "retrieval_eval_exists": eval_path.exists(),
        "retrieval_eval_passed": bool(eval_results.get("passed")),
        "retrieval_eval_query_count": int(eval_results.get("query_count") or 0),
        "retrieval_eval_failed_case_ids": [
            str(case.get("id") or "")
            for case in (eval_results.get("cases") or [])
            if not case.get("passed")
        ],
        "expected_source_record_count": len(expected_source_ids),
        "expected_extracted_source_record_count": len(extracted_source_ids),
        "indexed_source_record_count_for_expected_sources": len(indexed_source_ids),
        "missing_indexed_extracted_source_record_ids": missing_indexed_extracted_source_ids[:20],
        "upstream_blocked_source_record_ids": upstream_blocked_source_ids[:20],
        "document_role_counts": coverage_by_unit["document_role_counts"],
        "forest_units": coverage_by_unit["forest_units"],
    }

def _retrieval_index_source_ids(index_path: Path, expected_source_ids: set[str]) -> set[str]:
    if not index_path.exists():
        return set()
    try:
        with sqlite3.connect(index_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT source_record_id FROM chunks WHERE source_record_id IS NOT NULL"
            ).fetchall()
    except sqlite3.Error:
        return set()
    return {
        str(row[0] or "")
        for row in rows
        if str(row[0] or "") in expected_source_ids
    }

def _retrieval_coverage_by_unit(
    *,
    register: R1ForestPlanDocumentRegister,
    expected_source_ids: set[str],
    extracted_source_ids: set[str],
    indexed_source_ids: set[str],
) -> dict[str, Any]:
    document_role_counts = Counter()
    extracted_role_counts = Counter()
    indexed_role_counts = Counter()
    rows_by_unit = defaultdict(list)
    for row in register.rows:
        if (
            row["draft_status"] == "source_delta_required"
            and row["proposed_source_record_id"] in expected_source_ids
        ):
            rows_by_unit[row["forest_unit_id"]].append(row)
            document_role_counts[row["document_role"]] += 1
            if row["proposed_source_record_id"] in extracted_source_ids:
                extracted_role_counts[row["document_role"]] += 1
            if row["proposed_source_record_id"] in indexed_source_ids:
                indexed_role_counts[row["document_role"]] += 1

    forest_units = []
    for forest_unit_id, rows in sorted(rows_by_unit.items()):
        forest_units.append(
            {
                "forest_unit_id": forest_unit_id,
                "expected_source_record_count": len(rows),
                "expected_extracted_source_record_count": sum(
                    1 for row in rows if row["proposed_source_record_id"] in extracted_source_ids
                ),
                "indexed_source_record_count": sum(
                    1 for row in rows if row["proposed_source_record_id"] in indexed_source_ids
                ),
                "document_role_counts": dict(Counter(row["document_role"] for row in rows)),
                "extracted_document_role_counts": dict(
                    Counter(
                        row["document_role"]
                        for row in rows
                        if row["proposed_source_record_id"] in extracted_source_ids
                    )
                ),
                "indexed_document_role_counts": dict(
                    Counter(
                        row["document_role"]
                        for row in rows
                        if row["proposed_source_record_id"] in indexed_source_ids
                    )
                ),
                "missing_indexed_extracted_source_record_ids": [
                    row["proposed_source_record_id"]
                    for row in rows
                    if row["proposed_source_record_id"] in extracted_source_ids
                    and row["proposed_source_record_id"] not in indexed_source_ids
                ][:20],
            }
        )

    return {
        "document_role_counts": {
            "expected": dict(document_role_counts),
            "extracted": dict(extracted_role_counts),
            "indexed": dict(indexed_role_counts),
        },
        "forest_units": forest_units,
    }

def _retrieval_eval_passed_check(retrieval_readiness: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": "source_delta_retrieval_eval_passed",
        "passed": bool(retrieval_readiness.get("retrieval_eval_passed")),
        "details": {
            "retrieval_eval_exists": bool(retrieval_readiness.get("retrieval_eval_exists")),
            "retrieval_eval_path": retrieval_readiness.get("retrieval_eval_path"),
            "retrieval_eval_query_count": retrieval_readiness.get("retrieval_eval_query_count"),
            "retrieval_eval_failed_case_ids": retrieval_readiness.get(
                "retrieval_eval_failed_case_ids"
            )
            or [],
        },
    }

def _reuse_inventory_readiness(
    *,
    path: Path | None,
    expected_source_ids: set[str],
    expected_source_set_id: str,
) -> dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False, "status": "not_provided"}

    inventory_dir = path if path.is_dir() else path.parent
    inventory_path = None
    records_path = None
    summary_path = None
    if path.is_dir():
        inventory_path = path / "reuse_inventory.json"
        records_path = path / "reuse_inventory_records.jsonl"
        summary_path = path / "summary.json"
    elif path.name == "reuse_inventory.json":
        inventory_path = path
        records_path = inventory_dir / "reuse_inventory_records.jsonl"
        summary_path = inventory_dir / "summary.json"
    elif path.name == "reuse_inventory_records.jsonl":
        records_path = path
        inventory_path = inventory_dir / "reuse_inventory.json"
        summary_path = inventory_dir / "summary.json"
    elif path.name == "summary.json":
        summary_path = path
        inventory_path = inventory_dir / "reuse_inventory.json"
        records_path = inventory_dir / "reuse_inventory_records.jsonl"
    else:
        inventory_path = path
        records_path = inventory_dir / "reuse_inventory_records.jsonl"
        summary_path = inventory_dir / "summary.json"

    inventory = _read_json_if_exists(inventory_path) if inventory_path else {}
    summary = _read_json_if_exists(summary_path) if summary_path else {}
    records = _read_jsonl_if_exists(records_path) if records_path else []
    expected_records = [
        record
        for record in records
        if str(record.get("source_record_id") or "") in expected_source_ids
    ]
    record_ids = {str(record.get("source_record_id") or "") for record in expected_records}
    classification_counts = Counter(
        str(record.get("classification") or "") for record in expected_records
    )
    status = "ready"
    if not (inventory_path and inventory_path.exists()) and not (records_path and records_path.exists()):
        status = "missing"
    elif expected_source_ids - record_ids:
        status = "partial"
    return {
        "path": str(path),
        "exists": bool(path.exists()),
        "status": status,
        "inventory_path": str(inventory_path) if inventory_path else None,
        "inventory_exists": bool(inventory_path and inventory_path.exists()),
        "records_path": str(records_path) if records_path else None,
        "records_exists": bool(records_path and records_path.exists()),
        "summary_path": str(summary_path) if summary_path else None,
        "summary_exists": bool(summary_path and summary_path.exists()),
        "source_set_id": summary.get("source_set_id")
        or (inventory.get("summary") or {}).get("source_set_id"),
        "source_set_id_matches_extraction_source_set": (
            summary.get("source_set_id")
            or (inventory.get("summary") or {}).get("source_set_id")
            or expected_source_set_id
        )
        == expected_source_set_id,
        "record_count_for_expected_sources": len(expected_records),
        "missing_source_record_ids": sorted(expected_source_ids - record_ids)[:20],
        "classification_counts": {key: count for key, count in classification_counts.items() if key},
    }

def _forest_profile_readiness(
    *,
    register: R1ForestPlanDocumentRegister,
    forest_plan_profiles_path: Path,
    scoped_catalog_ids: set[str],
    merged_catalog_ids: set[str],
    canonical_catalog_ids: set[str],
    output_dir: Path,
    source_set_id: str,
) -> dict[str, Any]:
    collection = load_forest_plan_profiles(forest_plan_profiles_path)
    configured_profiles = {
        profile.forest_unit_id: profile for profile in collection.profiles
    }
    configured_profile_ids = sorted(configured_profiles)
    rows_by_unit = defaultdict(list)
    rows_by_source_id = {}
    for row in register.rows:
        rows_by_unit[row["forest_unit_id"]].append(row)
        rows_by_source_id[row["proposed_source_record_id"]] = row

    catalog_surfaces_by_source_id: dict[str, set[str]] = defaultdict(set)
    for source_id in scoped_catalog_ids:
        catalog_surfaces_by_source_id[source_id].add("scoped_source_delta_catalog")
    for source_id in merged_catalog_ids:
        catalog_surfaces_by_source_id[source_id].add("merged_source_delta_catalog")
    for source_id in canonical_catalog_ids:
        catalog_surfaces_by_source_id[source_id].add("active_canonical_catalog")

    extraction_manifest_path = (
        output_dir / "derived" / source_set_id / "diagnostics" / "extraction_manifest.jsonl"
        if source_set_id
        else output_dir / "derived" / "diagnostics" / "extraction_manifest.jsonl"
    )
    retrieval_index_path = (
        output_dir / "derived" / source_set_id / "retrieval" / "evidence_index.sqlite"
        if source_set_id
        else output_dir / "derived" / "retrieval" / "evidence_index.sqlite"
    )
    extraction_manifest_records = _read_jsonl_if_exists(extraction_manifest_path)
    extraction_records_by_source_id = {
        str(record.get("source_record_id") or ""): record for record in extraction_manifest_records
    }
    indexed_source_ids = _retrieval_index_all_source_ids(retrieval_index_path)

    tracked_forest_unit_ids = sorted(set(register.forest_unit_ids) | set(configured_profile_ids))
    profile_rows = []
    for forest_unit_id in tracked_forest_unit_ids:
        profile = configured_profiles.get(forest_unit_id)
        register_rows = sorted(
            rows_by_unit.get(forest_unit_id, []),
            key=lambda row: (row["document_role"], row["proposed_source_record_id"]),
        )
        source_requirements = []
        seen_source_ids = set()

        if profile is not None:
            for role, source_record in sorted(
                profile.supporting_source_record_ids_by_role.items(),
                key=lambda item: item[0],
            ):
                source_id = source_record.source_record_id
                source_requirements.append(
                    _forest_profile_source_requirement(
                        forest_unit_id=forest_unit_id,
                        role=role,
                        required_for=source_record.required_for,
                        source_record_id=source_id,
                        required_readiness=role in profile.required_readiness_source_roles,
                        register_row=rows_by_source_id.get(source_id),
                        catalog_surfaces=sorted(catalog_surfaces_by_source_id.get(source_id, set())),
                        extraction_record=extraction_records_by_source_id.get(source_id),
                        indexed_source_ids=indexed_source_ids,
                    )
                )
                seen_source_ids.add(source_id)

        for row in register_rows:
            source_id = row["proposed_source_record_id"]
            if source_id in seen_source_ids:
                continue
            source_requirements.append(
                _forest_profile_source_requirement(
                    forest_unit_id=forest_unit_id,
                    role=row["document_role"],
                    required_for=row["required_for"],
                    source_record_id=source_id,
                    required_readiness=False,
                    register_row=row,
                    catalog_surfaces=sorted(catalog_surfaces_by_source_id.get(source_id, set())),
                    extraction_record=extraction_records_by_source_id.get(source_id),
                    indexed_source_ids=indexed_source_ids,
                )
            )
            seen_source_ids.add(source_id)

        requirement_status_counts = Counter(
            requirement["readiness_status"] for requirement in source_requirements
        )
        blocker_types = sorted(
            {
                blocker
                for requirement in source_requirements
                for blocker in requirement["blocker_types"]
            }
        )
        blocker_source_record_ids = sorted(
            {
                requirement["source_record_id"]
                for requirement in source_requirements
                if requirement["blocker_types"] and requirement["source_record_id"]
            }
        )
        ready_required_count = sum(
            1
            for requirement in source_requirements
            if requirement["required_readiness"]
            and requirement["readiness_status"] == "retrieval_ready"
        )
        required_count = sum(
            1 for requirement in source_requirements if requirement["required_readiness"]
        )
        retrieval_ready_count = sum(
            1
            for requirement in source_requirements
            if requirement["readiness_status"] == "retrieval_ready"
        )
        profile_rows.append(
            {
                "forest_unit_id": forest_unit_id,
                "forest_unit_names": _forest_profile_unit_names(
                    forest_unit_id=forest_unit_id,
                    profile=profile,
                    register_rows=register_rows,
                ),
                "configured_profile": profile is not None,
                "profile_kind": "configured_profile" if profile is not None else "register_tracking_only",
                "profile_readiness_status": "ready" if not blocker_types else "blocked",
                "active_plan_source_record_id": (
                    profile.active_plan_source_record_id if profile is not None else None
                ),
                "required_source_record_count": required_count,
                "required_retrieval_ready_count": ready_required_count,
                "source_requirement_count": len(source_requirements),
                "retrieval_ready_source_record_count": retrieval_ready_count,
                "readiness_status_counts": dict(requirement_status_counts),
                "blocker_types": blocker_types,
                "blocker_source_record_ids": blocker_source_record_ids,
                "register_status_counts": dict(Counter(row["draft_status"] for row in register_rows)),
                "source_requirements": source_requirements,
            }
        )

    configured_rows = [row for row in profile_rows if row["configured_profile"]]
    tracking_only_rows = [row for row in profile_rows if not row["configured_profile"]]
    ready_profile_ids = sorted(
        row["forest_unit_id"]
        for row in configured_rows
        if row["profile_readiness_status"] == "ready"
    )
    blocked_profile_ids = sorted(
        row["forest_unit_id"]
        for row in configured_rows
        if row["profile_readiness_status"] != "ready"
    )
    ready_tracking_only_ids = sorted(
        row["forest_unit_id"]
        for row in tracking_only_rows
        if row["profile_readiness_status"] == "ready"
    )
    blocked_tracking_only_ids = sorted(
        row["forest_unit_id"]
        for row in tracking_only_rows
        if row["profile_readiness_status"] != "ready"
    )

    return {
        "status": "ready" if not blocked_profile_ids and not blocked_tracking_only_ids else "ready_with_blockers",
        "forest_plan_profiles_path": str(forest_plan_profiles_path),
        "source_set_id": source_set_id or None,
        "extraction_manifest_path": str(extraction_manifest_path),
        "extraction_manifest_exists": extraction_manifest_path.exists(),
        "retrieval_index_path": str(retrieval_index_path),
        "retrieval_index_exists": retrieval_index_path.exists(),
        "configured_profile_count": len(configured_profile_ids),
        "configured_profile_ids": configured_profile_ids,
        "tracked_forest_unit_count": len(tracked_forest_unit_ids),
        "tracked_forest_unit_ids": tracked_forest_unit_ids,
        "tracking_only_row_count": len(tracking_only_rows),
        "ready_profile_count": len(ready_profile_ids),
        "ready_profile_ids": ready_profile_ids,
        "blocked_profile_count": len(blocked_profile_ids),
        "blocked_profile_ids": blocked_profile_ids,
        "ready_tracking_only_count": len(ready_tracking_only_ids),
        "ready_tracking_only_ids": ready_tracking_only_ids,
        "blocked_tracking_only_count": len(blocked_tracking_only_ids),
        "blocked_tracking_only_ids": blocked_tracking_only_ids,
        "profile_rows": profile_rows,
    }

def _forest_profile_source_requirement(
    *,
    forest_unit_id: str,
    role: str,
    required_for: str,
    source_record_id: str,
    required_readiness: bool,
    register_row: dict[str, str] | None,
    catalog_surfaces: list[str],
    extraction_record: dict[str, Any] | None,
    indexed_source_ids: set[str],
) -> dict[str, Any]:
    register_status = (
        register_row.get("draft_status") if register_row is not None else "profile_source_missing_from_register"
    )
    readiness_status = "retrieval_ready"
    blocker_types: list[str] = []
    extraction_status = None
    extraction_error_class = None

    if register_status == "profile_source_missing_from_register":
        readiness_status = "profile_source_missing_from_register"
        blocker_types = ["missing_register_row"]
    elif register_status == "official_source_gap_documented":
        readiness_status = "official_source_gap"
        blocker_types = ["official_source_gap"]
    elif source_record_id in indexed_source_ids:
        readiness_status = "retrieval_ready"
    elif extraction_record is not None:
        extraction_status = str(extraction_record.get("status") or "")
        failure = extraction_record.get("failure") or {}
        extraction_error_class = str(failure.get("error_class") or "") or None
        if extraction_status == "extracted":
            readiness_status = "extracted_not_retrieval_ready"
            blocker_types = ["retrieval_gap"]
        elif extraction_status in {
            "parser_error",
            "parser_timeout",
            "empty_text",
            "artifact_missing",
            "hash_mismatch",
            "no_artifact",
        }:
            readiness_status = "extraction_blocked"
            blocker_types = ["extraction_blocked"]
        else:
            readiness_status = "extraction_pending"
            blocker_types = ["extraction_pending"]
    elif catalog_surfaces:
        readiness_status = (
            "captured_source_delta"
            if register_status == "source_delta_required"
            else "catalog_confirmed"
        )
        blocker_types = ["downstream_readiness_pending"]
    elif register_status == "source_delta_required":
        readiness_status = "source_delta_capture_missing"
        blocker_types = ["catalog_capture_missing"]
    else:
        readiness_status = "catalog_confirmed_missing_from_catalog"
        blocker_types = ["catalog_missing"]

    return {
        "forest_unit_id": forest_unit_id,
        "role": role,
        "required_for": required_for,
        "source_record_id": source_record_id,
        "required_readiness": required_readiness,
        "register_status": register_status,
        "catalog_surfaces": catalog_surfaces,
        "readiness_status": readiness_status,
        "extraction_status": extraction_status,
        "extraction_error_class": extraction_error_class,
        "retrieval_ready": source_record_id in indexed_source_ids,
        "blocker_types": blocker_types,
        "readiness_tier": register_row.get("readiness_tier") if register_row is not None else None,
        "notes": register_row.get("notes") if register_row is not None else None,
    }

def _forest_profile_unit_names(
    *,
    forest_unit_id: str,
    profile: Any,
    register_rows: list[dict[str, str]],
) -> list[str]:
    if profile is not None:
        return list(profile.forest_unit_names)
    names = []
    for row in register_rows:
        name = str(row.get("forest_unit_name") or "").strip()
        if name and name not in names:
            names.append(name)
    return names or [forest_unit_id]

def _retrieval_index_all_source_ids(index_path: Path) -> set[str]:
    if not index_path.exists():
        return set()
    try:
        with sqlite3.connect(index_path) as connection:
            rows = connection.execute(
                "SELECT DISTINCT source_record_id FROM chunks WHERE source_record_id IS NOT NULL"
            ).fetchall()
    except sqlite3.Error:
        return set()
    return {str(row[0] or "") for row in rows if str(row[0] or "")}
