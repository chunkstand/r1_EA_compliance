from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .records import sha256_file
from .records import slugify
from .source_partitions import ACTIVE_REVIEW_CORPUS
from .source_partitions import CURRENTNESS_SUPERSESSION_ARCHIVE
from .source_partitions import DEFAULT_SOURCE_PARTITION_CONTRACT_PATH
from .source_partitions import catalog_source_partition
from .source_partitions import catalog_source_partition_record
from .source_partitions import graph_relationships_for_family_source
from .source_partitions import load_source_partition_contract
from .source_partitions import validate_catalog_source_partitions
from .source_register import read_source_register_tables


AUTHORITY_CURRENTNESS_REPORT_SCHEMA_VERSION = "authority-currentness-report-v0"
DEFAULT_AUTHORITY_INVENTORY_PATH = Path("config/authority_universe_families_nepa_ea_v1.json")
DEFAULT_SOURCE_ADDITION_DECISIONS_PATH = Path(
    "config/authority_source_addition_decisions_nepa_ea_v1.json"
)
DEFAULT_SOURCE_REGISTER_CURRENTNESS_LINEAGE_PATH = Path(
    "config/source_register_currentness_lineage_v1.json"
)
PROJECTED_AUTHORITY_INVENTORY_SCHEMA_VERSION = "source-register-authority-inventory-v1"
PROJECTED_SOURCE_ADDITION_DECISIONS_SCHEMA_VERSION = (
    "source-register-source-addition-decisions-v1"
)
NO_REPLACEMENT_LINEAGE_DISPOSITIONS = {
    "historical_no_replacement",
    "reserved_without_replacement",
    "revoked_without_replacement",
    "rescinded_without_replacement",
}

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
    "source_partition",
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
    source_partition_contract_path: Path = DEFAULT_SOURCE_PARTITION_CONTRACT_PATH,
    catalog_path: Path | None = None,
    source_set_manifest_path: Path | None = None,
    output_path: Path | None = None,
) -> AuthorityCurrentnessResult:
    """Build a deterministic source-currentness report for the authority inventory."""

    output_dir = Path(output_dir)
    authority_inventory_path = Path(authority_inventory_path)
    source_addition_decisions_path = Path(source_addition_decisions_path)
    source_partition_contract_path = Path(source_partition_contract_path)
    catalog_path = Path(catalog_path) if catalog_path else output_dir / "catalog" / "source_catalog.jsonl"
    source_set_manifest_path = (
        Path(source_set_manifest_path)
        if source_set_manifest_path
        else output_dir / "catalog" / "source_set_manifest.json"
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
    )
    summary = _summary(
        source_set_id=source_set_id,
        inventory=inventory,
        manifest=manifest,
        family_currentness=family_currentness,
        source_currentness_records=source_currentness_records,
        catalog_source_partitions=catalog_source_partitions,
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


def _validation(
    *,
    inventory: dict,
    manifest: dict,
    catalog_rows: list[dict],
    catalog_by_source_record_id: dict[str, dict],
    source_addition_decisions: dict,
    source_partition_contract: dict,
    catalog_source_partitions: list[dict],
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
    catalog_source_record_ids = set(catalog_by_source_record_id)
    inventory_source_record_id_set = set(inventory_source_record_ids)
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
        and not _family_has_lineage_metadata(family)
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
    source_partition_checks = validate_catalog_source_partitions(
        catalog_rows=catalog_rows,
        catalog_source_partitions=catalog_source_partitions,
        contract=source_partition_contract,
    )
    non_active_source_records_counted_current = [
        record["source_record_id"]
        for record in source_currentness_records
        if record["counts_as_current_authority"]
        and record.get("source_partition") != ACTIVE_REVIEW_CORPUS
    ]
    superseded_family_active_relationship_records = [
        record["source_record_id"]
        for record in source_currentness_records
        if record["family_status"] == "superseded"
        and (
            record.get("eligible_for_active_review_rules_for_family")
            or "RULE_DERIVES_FROM_AUTHORITY"
            in record.get("graph_allowed_relationships_for_family", [])
            or "CLAIM_SUPPORTS_RULE" in record.get("graph_allowed_relationships_for_family", [])
            or "SUPPORTS_FINDING" in record.get("graph_allowed_relationships_for_family", [])
        )
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
            inventory_source_set_id == manifest_source_set_id
            or inventory_source_record_id_set <= catalog_source_record_ids,
            {
                "manifest_source_set_id": manifest_source_set_id,
                "inventory_source_record_ids_subset_of_catalog": True,
            },
            {
                "inventory_source_set_id": inventory_source_set_id,
                "inventory_source_record_ids_subset_of_catalog": (
                    inventory_source_record_id_set <= catalog_source_record_ids
                ),
            },
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
            "superseded_families_have_lineage_metadata",
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
            "only_active_review_corpus_counts_as_current_authority",
            not non_active_source_records_counted_current,
            [],
            non_active_source_records_counted_current,
        ),
        _check(
            "superseded_family_sources_have_only_currentness_relationships",
            not superseded_family_active_relationship_records,
            [],
            superseded_family_active_relationship_records,
        ),
        _check(
            "source_addition_decisions_schema_loaded",
            bool(source_addition_decisions.get("schema_version")),
            "schema_version",
            source_addition_decisions.get("schema_version"),
        ),
    ]
    checks.extend(source_partition_checks)
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
    catalog_source_partitions: list[dict],
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
    catalog_source_partition_counts = Counter(
        record["source_partition"] for record in catalog_source_partitions
    )
    family_source_role_counts = Counter(
        record.get("authority_family_source_role") for record in source_currentness_records
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
        "catalog_source_partition_counts": dict(sorted(catalog_source_partition_counts.items())),
        "authority_family_source_role_counts": dict(sorted(family_source_role_counts.items())),
        "candidate_family_count": family_status_counts["candidate"],
        "documented_source_non_addition_count": family_currentness_counts[
            "documented_source_non_addition"
        ],
        "documented_source_gap_count": family_currentness_counts["documented_source_gap"],
        "source_currentness_confirmed_family_count": family_currentness_counts[
            "source_currentness_confirmed"
        ],
        "superseded_replacement_confirmed_family_count": family_currentness_counts[
            "superseded_replacement_sources_confirmed"
        ],
        "superseded_no_replacement_confirmed_family_count": family_currentness_counts[
            "superseded_no_replacement_confirmed"
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
        "temporal_lineage_record_count": len(
            _temporal_lineage_records(
                inventory=inventory,
                source_currentness_records=source_currentness_records,
            )
        ),
        "validation_passed": validation["passed"],
        "inventory_summary": inventory.get("summary", {}),
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
        authority_inventory_path == DEFAULT_AUTHORITY_INVENTORY_PATH
        and source_addition_decisions_path == DEFAULT_SOURCE_ADDITION_DECISIONS_PATH
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


def _manifest_date(manifest: dict) -> str:
    created_at = str(manifest.get("created_at") or "")
    match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", created_at)
    if match:
        return match.group(1)
    return _utc_now()[:10]


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


def _dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item)]


def _check(name: str, passed: bool, expected: object, actual: object) -> dict:
    return {
        "name": name,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
