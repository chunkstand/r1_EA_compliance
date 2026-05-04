from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .records import sha256_file


AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION = "authority-currentness-report-v0"
DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
DEFAULT_SOURCE_ADDITION_DECISIONS_PATH = Path(
    "config/authority_source_addition_decisions_nepa_ea_v1.json"
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
REQUIRED_SOURCE_CURRENTNESS_FIELDS = {
    "authority_family_id",
    "capture_date",
    "citation_label",
    "source_record_id",
    "source_title",
    "supersession_status",
    "url",
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
    catalog_path: Path | None = None,
    source_set_manifest_path: Path | None = None,
    output_path: Path | None = None,
) -> AuthorityCurrentnessResult:
    """Build a deterministic source-currentness report for the authority inventory."""

    output_dir = Path(output_dir)
    authority_inventory_path = Path(authority_inventory_path)
    source_addition_decisions_path = Path(source_addition_decisions_path)
    catalog_path = Path(catalog_path) if catalog_path else output_dir / "catalog" / "source_catalog.jsonl"
    source_set_manifest_path = (
        Path(source_set_manifest_path)
        if source_set_manifest_path
        else output_dir / "catalog" / "source_set_manifest.json"
    )

    inventory = _read_json(authority_inventory_path)
    source_addition_decisions = _read_source_addition_decisions(source_addition_decisions_path)
    manifest = _read_json(source_set_manifest_path)
    source_set_id = source_set_id or str(manifest["source_set_id"])
    catalog_rows = [
        row
        for row in _read_jsonl(catalog_path)
        if str(row.get("source_set_id") or source_set_id) == source_set_id
    ]
    catalog_by_source_record_id = {
        str(row.get("source_record_id") or ""): row
        for row in catalog_rows
        if row.get("source_record_id")
    }
    decisions_by_family_id = {
        str(decision.get("authority_family_id") or ""): decision
        for decision in source_addition_decisions.get("decisions", [])
        if decision.get("authority_family_id")
    }

    source_currentness_records = []
    family_currentness = []
    for family in inventory["authority_families"]:
        family_records = [
            _source_currentness_record(
                family=family,
                source_record_id=source_record_id,
                catalog_row=catalog_by_source_record_id.get(source_record_id),
                manifest=manifest,
            )
            for source_record_id in family.get("source_record_ids", [])
        ]
        source_currentness_records.extend(family_records)
        family_currentness.append(
            _family_currentness_record(
                family=family,
                source_records=family_records,
                source_addition_decision=decisions_by_family_id.get(family["family_id"]),
            )
        )

    validation = _validation(
        inventory=inventory,
        manifest=manifest,
        catalog_rows=catalog_rows,
        catalog_by_source_record_id=catalog_by_source_record_id,
        source_addition_decisions=source_addition_decisions,
        decisions_by_family_id=decisions_by_family_id,
        family_currentness=family_currentness,
        source_currentness_records=source_currentness_records,
        requested_source_set_id=source_set_id,
    )
    summary = _summary(
        source_set_id=source_set_id,
        inventory=inventory,
        manifest=manifest,
        family_currentness=family_currentness,
        source_currentness_records=source_currentness_records,
        validation=validation,
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
            "catalog_path": str(catalog_path),
            "catalog_sha256": sha256_file(catalog_path) if catalog_path.exists() else None,
            "source_set_manifest_path": str(source_set_manifest_path),
            "source_set_manifest_sha256": sha256_file(source_set_manifest_path)
            if source_set_manifest_path.exists()
            else None,
        },
        "source_addition_decisions": source_addition_decisions,
        "family_currentness": family_currentness,
        "source_currentness_records": source_currentness_records,
        "validation": validation,
        "summary": summary,
    }
    _write_json(output_path, report)

    return AuthorityCurrentnessResult(report_path=output_path, summary=summary)


def _source_currentness_record(
    *,
    family: dict,
    source_record_id: str,
    catalog_row: dict | None,
    manifest: dict,
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
        }

    source_status = str(catalog_row.get("source_status") or "")
    supersession_status = _supersession_status(family=family, source_status=source_status)
    currentness_status = _currentness_status(family=family, source_status=source_status)
    counts_as_current_authority = (
        family.get("status") != "superseded" and source_status in SUCCESSFUL_SOURCE_STATUSES
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
    }


def _family_currentness_record(
    *,
    family: dict,
    source_records: list[dict],
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
    replacement_source_record_ids = [
        record["source_record_id"]
        for record in source_records
        if record["supersession_status"] == "superseded_replacement_source"
    ]
    source_addition_decision_status = (
        source_addition_decision.get("decision_status") if source_addition_decision else None
    )

    status = family["status"]
    if status == "candidate" and not family.get("source_record_ids"):
        currentness_status = (
            "documented_source_non_addition"
            if source_addition_decision
            else "missing_source_addition_decision"
        )
    elif status == "superseded":
        currentness_status = (
            "superseded_replacement_sources_confirmed"
            if replacement_source_record_ids
            and not failed_source_record_ids
            and not missing_catalog_record_ids
            else "superseded_source_gap"
        )
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
    }


def _validation(
    *,
    inventory: dict,
    manifest: dict,
    catalog_rows: list[dict],
    catalog_by_source_record_id: dict[str, dict],
    source_addition_decisions: dict,
    decisions_by_family_id: dict[str, dict],
    family_currentness: list[dict],
    source_currentness_records: list[dict],
    requested_source_set_id: str,
) -> dict:
    inventory_source_set_id = inventory.get("source_set", {}).get("source_set_id")
    manifest_source_set_id = manifest.get("source_set_id")
    candidate_families_without_sources = [
        family["family_id"]
        for family in inventory["authority_families"]
        if family.get("status") == "candidate" and not family.get("source_record_ids")
    ]
    candidate_families_without_decisions = [
        family_id
        for family_id in candidate_families_without_sources
        if family_id not in decisions_by_family_id
    ]
    inventory_source_record_ids = [
        source_record_id
        for family in inventory["authority_families"]
        for source_record_id in family.get("source_record_ids", [])
    ]
    missing_catalog_record_ids = sorted(
        {
            source_record_id
            for source_record_id in inventory_source_record_ids
            if source_record_id not in catalog_by_source_record_id
        }
    )
    records_with_missing_required_fields = [
        {
            "authority_family_id": record["authority_family_id"],
            "source_record_id": record["source_record_id"],
            "missing_fields": sorted(
                field
                for field in REQUIRED_SOURCE_CURRENTNESS_FIELDS
                if not record.get(field)
                and record["currentness_status"] != "missing_catalog_record"
            ),
        }
        for record in source_currentness_records
    ]
    records_with_missing_required_fields = [
        record for record in records_with_missing_required_fields if record["missing_fields"]
    ]
    failure_records_counted_current = [
        record["source_record_id"]
        for record in source_currentness_records
        if record["source_status"] in FAILED_OR_UNVERIFIED_SOURCE_STATUSES
        and record["counts_as_current_authority"]
    ]
    excluded_records_counted_current = [
        record["source_record_id"]
        for record in source_currentness_records
        if record["source_status"] in EXCLUDED_SOURCE_STATUSES
        and record["counts_as_current_authority"]
    ]
    unsupported_current_statuses = sorted(
        {
            str(record["source_status"])
            for record in source_currentness_records
            if record["counts_as_current_authority"]
            and record["source_status"] not in SUCCESSFUL_SOURCE_STATUSES
        }
    )
    superseded_records_counted_current = [
        record["source_record_id"]
        for record in source_currentness_records
        if record["family_status"] == "superseded" and record["counts_as_current_authority"]
    ]
    superseded_families_without_metadata = [
        family["family_id"]
        for family in inventory["authority_families"]
        if family.get("status") == "superseded"
        and not (
            family.get("supersession")
            and family["supersession"].get("replacement_family_id")
            and family["supersession"].get("current_source_record_ids")
        )
    ]
    stale_milestone_2_gap_family_ids = [
        family["family_id"]
        for family in inventory["authority_families"]
        if any(_is_stale_milestone_2_gap(gap) for gap in family.get("open_inventory_gaps", []))
        or any(
            _is_stale_milestone_2_gap(gap)
            for gap in family.get("source_record_mapping", {}).get(
                "missing_source_record_requirements",
                [],
            )
        )
    ]
    milestone_2_requirement_count = int(
        inventory.get("summary", {}).get("families_requiring_milestone_2_source_currentness") or 0
    )
    non_candidate_current_source_gaps = [
        family["authority_family_id"]
        for family in family_currentness
        if family["family_status"] not in {"candidate", "superseded", "out_of_scope"}
        and family["current_source_record_count"] == 0
    ]
    failed_family_ids = [
        family["authority_family_id"]
        for family in family_currentness
        if family["failed_source_record_count"] or family["missing_catalog_record_count"]
    ]

    checks = [
        _check(
            "source_set_manifest_matches_requested_source_set",
            manifest_source_set_id == requested_source_set_id,
            requested_source_set_id,
            manifest_source_set_id,
        ),
        _check(
            "inventory_source_set_matches_manifest",
            inventory_source_set_id == manifest_source_set_id,
            manifest_source_set_id,
            inventory_source_set_id,
        ),
        _check(
            "catalog_has_rows_for_source_set",
            bool(catalog_rows),
            "non-empty catalog rows",
            len(catalog_rows),
        ),
        _check(
            "all_family_source_records_found_in_catalog",
            not missing_catalog_record_ids,
            [],
            missing_catalog_record_ids,
        ),
        _check(
            "candidate_families_have_source_addition_decisions",
            not candidate_families_without_decisions,
            [],
            candidate_families_without_decisions,
        ),
        _check(
            "source_currentness_records_have_required_fields",
            not records_with_missing_required_fields,
            [],
            records_with_missing_required_fields,
        ),
        _check(
            "only_successful_statuses_count_as_current",
            not unsupported_current_statuses,
            [],
            unsupported_current_statuses,
        ),
        _check(
            "failed_web_captures_do_not_count_as_current",
            not failure_records_counted_current,
            [],
            failure_records_counted_current,
        ),
        _check(
            "excluded_sources_do_not_count_as_current",
            not excluded_records_counted_current,
            [],
            excluded_records_counted_current,
        ),
        _check(
            "superseded_families_do_not_count_as_current_authority",
            not superseded_records_counted_current,
            [],
            superseded_records_counted_current,
        ),
        _check(
            "superseded_families_have_replacement_metadata",
            not superseded_families_without_metadata,
            [],
            superseded_families_without_metadata,
        ),
        _check(
            "inventory_has_no_stale_milestone_2_currentness_gaps",
            not stale_milestone_2_gap_family_ids,
            [],
            stale_milestone_2_gap_family_ids,
        ),
        _check(
            "inventory_summary_has_no_remaining_milestone_2_currentness_requirements",
            milestone_2_requirement_count == 0,
            0,
            milestone_2_requirement_count,
        ),
        _check(
            "non_candidate_families_have_current_source_coverage",
            not non_candidate_current_source_gaps,
            [],
            non_candidate_current_source_gaps,
        ),
        _check(
            "no_family_has_failed_or_missing_capture",
            not failed_family_ids,
            [],
            failed_family_ids,
        ),
        _check(
            "source_addition_decisions_schema_loaded",
            bool(source_addition_decisions.get("schema_version")),
            "schema_version",
            source_addition_decisions.get("schema_version"),
        ),
    ]
    return {
        "schema_version": AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _summary(
    *,
    source_set_id: str,
    inventory: dict,
    manifest: dict,
    family_currentness: list[dict],
    source_currentness_records: list[dict],
    validation: dict,
) -> dict:
    family_status_counts = Counter(family["family_status"] for family in family_currentness)
    family_currentness_counts = Counter(family["currentness_status"] for family in family_currentness)
    source_currentness_counts = Counter(
        record["currentness_status"] for record in source_currentness_records
    )
    supersession_counts = Counter(
        record["supersession_status"] for record in source_currentness_records
    )
    return {
        "schema_version": AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "source_set_id": source_set_id,
        "manifest_source_count": manifest.get("source_count"),
        "manifest_artifact_count": manifest.get("artifact_count"),
        "manifest_status_counts": manifest.get("status_counts", {}),
        "authority_family_count": len(family_currentness),
        "family_status_counts": dict(sorted(family_status_counts.items())),
        "family_currentness_counts": dict(sorted(family_currentness_counts.items())),
        "source_currentness_record_count": len(source_currentness_records),
        "source_currentness_counts": dict(sorted(source_currentness_counts.items())),
        "supersession_status_counts": dict(sorted(supersession_counts.items())),
        "candidate_family_count": family_status_counts["candidate"],
        "documented_source_non_addition_count": family_currentness_counts[
            "documented_source_non_addition"
        ],
        "source_currentness_confirmed_family_count": family_currentness_counts[
            "source_currentness_confirmed"
        ],
        "superseded_replacement_confirmed_family_count": family_currentness_counts[
            "superseded_replacement_sources_confirmed"
        ],
        "failed_family_count": sum(
            1
            for family in family_currentness
            if family["failed_source_record_count"] or family["missing_catalog_record_count"]
        ),
        "current_authority_source_record_count": sum(
            1 for record in source_currentness_records if record["counts_as_current_authority"]
        ),
        "excluded_source_record_count": source_currentness_counts["excluded_no_artifact"],
        "validation_passed": validation["passed"],
        "inventory_summary": inventory.get("summary", {}),
    }


def _supersession_status(*, family: dict, source_status: str) -> str:
    if family.get("status") == "superseded":
        return "superseded_replacement_source"
    if source_status in EXCLUDED_SOURCE_STATUSES:
        return "excluded_no_current_authority"
    if source_status in FAILED_OR_UNVERIFIED_SOURCE_STATUSES:
        return "failed_or_unverified_capture"
    return "current_authoritative_source"


def _currentness_status(*, family: dict, source_status: str) -> str:
    if source_status in EXCLUDED_SOURCE_STATUSES:
        return "excluded_no_artifact"
    if source_status not in SUCCESSFUL_SOURCE_STATUSES:
        return "failed_or_unverified_capture"
    if family.get("status") == "superseded":
        return "replacement_source_confirmed"
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


def _check(name: str, passed: bool, expected: object, actual: object) -> dict:
    return {
        "name": name,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
