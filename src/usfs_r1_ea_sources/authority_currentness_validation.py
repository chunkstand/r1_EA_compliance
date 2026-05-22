from __future__ import annotations

from collections import Counter

from .source_partitions import ACTIVE_REVIEW_CORPUS, validate_catalog_source_partitions


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
    failed_or_unverified_source_statuses: set[str],
    excluded_source_statuses: set[str],
    successful_source_statuses: set[str],
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
        if record["source_status"] in failed_or_unverified_source_statuses
        and record["counts_as_current_authority"]
    ]
    excluded_records_counted_current = [
        record["source_record_id"]
        for record in source_currentness_records
        if record["source_status"] in excluded_source_statuses
        and record["counts_as_current_authority"]
    ]
    unsupported_current_statuses = sorted(
        {
            str(record["source_status"])
            for record in source_currentness_records
            if record["counts_as_current_authority"]
            and record["source_status"] not in successful_source_statuses
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
        "schema_version": "authority-currentness-report-v0",
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
    temporal_lineage_records: list[dict],
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
        "schema_version": "authority-currentness-report-v0",
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
        "temporal_lineage_record_count": len(temporal_lineage_records),
        "validation_passed": validation["passed"],
        "inventory_summary": inventory.get("summary", {}),
    }


def _family_has_lineage_metadata(family: dict) -> bool:
    supersession = family.get("supersession")
    if not isinstance(supersession, dict):
        return False
    replacement_source_record_ids = _strings(supersession.get("current_source_record_ids"))
    if replacement_source_record_ids and supersession.get("replacement_family_id"):
        return True
    return bool(
        str(supersession.get("lineage_disposition") or "")
        in {
            "historical_no_replacement",
            "reserved_without_replacement",
            "revoked_without_replacement",
            "rescinded_without_replacement",
        }
        and str(supersession.get("lineage_basis") or "").strip()
    )


def _is_stale_milestone_2_gap(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return (
        value.startswith("Milestone 2 must confirm current authoritative source coverage")
        or value.startswith("Milestone 2 currentness validation must prevent")
    )


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
    from datetime import UTC, datetime

    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
