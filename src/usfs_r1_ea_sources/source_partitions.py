from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any


SOURCE_PARTITION_CONTRACT_SCHEMA_VERSION = "source-partition-contract-v1"
DEFAULT_SOURCE_PARTITION_CONTRACT_PATH = Path("config/source_partition_contract_nepa_3d_v1.json")

ACTIVE_REVIEW_CORPUS = "active_review_corpus"
CURRENTNESS_SUPERSESSION_ARCHIVE = "currentness_supersession_archive"
CANDIDATE_BLOCKED_SOURCE = "candidate_blocked_source"

VALID_SOURCE_PARTITIONS = {
    ACTIVE_REVIEW_CORPUS,
    CURRENTNESS_SUPERSESSION_ARCHIVE,
    CANDIDATE_BLOCKED_SOURCE,
}
REQUIRED_SOURCE_PARTITIONS = {
    ACTIVE_REVIEW_CORPUS,
    CURRENTNESS_SUPERSESSION_ARCHIVE,
    CANDIDATE_BLOCKED_SOURCE,
}
NON_ACTIVE_ALLOWED_RELATIONSHIPS = {
    "SUPERSEDED_BY",
    "REPLACES_RESERVED_AUTHORITY",
    "HAS_CURRENTNESS_STATUS",
    "BLOCKED_BY",
}
EXPECTED_PARTITION_ACTIVE_ELIGIBILITY = {
    ACTIVE_REVIEW_CORPUS: True,
    CURRENTNESS_SUPERSESSION_ARCHIVE: False,
    CANDIDATE_BLOCKED_SOURCE: False,
}
REQUIRED_WORKBOOK_SOURCE_DELTA_PLAN_KEYS = {
    "environmental_justice_civil_rights",
    "fsh_1909_15",
    "reserved_36_cfr_part_220",
}

SUCCESSFUL_SOURCE_STATUSES = {
    "downloaded",
    "downloaded_existing",
    "duplicate_content",
    "duplicate_url",
}
BLOCKED_SOURCE_STATUSES = {
    "blocked",
    "challenge_page",
    "empty_body",
    "failed",
    "invalid_content",
    "not_found",
    "not_in_run",
    "planned",
    "rate_limited",
    "skipped_excluded",
    "ssl_error",
    "timeout",
    "unsupported_content_type",
}


def load_source_partition_contract(path: Path = DEFAULT_SOURCE_PARTITION_CONTRACT_PATH) -> dict:
    if not path.exists():
        return _default_source_partition_contract()
    contract = json.loads(path.read_text(encoding="utf-8"))
    return {**_default_source_partition_contract(), **contract}


def catalog_source_partition(row: dict, contract: dict | None = None) -> tuple[str, str]:
    contract = contract or _default_source_partition_contract()
    explicit_partition = _explicit_source_partition(row)
    if explicit_partition:
        return explicit_partition, "explicit_source_partition"

    source_status = str(row.get("source_status") or "")
    if source_status in BLOCKED_SOURCE_STATUSES:
        return CANDIDATE_BLOCKED_SOURCE, f"blocked_or_unavailable_status:{source_status}"

    if _has_non_current_source_marker(row):
        return CURRENTNESS_SUPERSESSION_ARCHIVE, "non_current_source_marker"

    if source_status in SUCCESSFUL_SOURCE_STATUSES:
        return ACTIVE_REVIEW_CORPUS, f"successful_status:{source_status}"

    return CANDIDATE_BLOCKED_SOURCE, f"unrecognized_status:{source_status or 'missing'}"


def catalog_source_partition_record(row: dict, contract: dict | None = None) -> dict:
    contract = contract or _default_source_partition_contract()
    source_partition, source_partition_basis = catalog_source_partition(row, contract)
    return {
        "source_record_id": row.get("source_record_id"),
        "source_title": row.get("title"),
        "citation_label": row.get("citation_label"),
        "source_status": row.get("source_status"),
        "source_partition": source_partition,
        "source_partition_basis": source_partition_basis,
        "eligible_for_active_review_rules": _partition_eligibility(source_partition, contract),
        "graph_allowed_relationships": graph_relationships_for_partition(
            source_partition,
            contract,
        ),
        "fsh_1909_15_chapter_kind": fsh_1909_15_chapter_kind(row),
        "artifact_path": row.get("artifact_path"),
        "artifact_sha256": row.get("artifact_sha256"),
    }


def graph_relationships_for_partition(source_partition: str, contract: dict | None = None) -> list[str]:
    contract = contract or _default_source_partition_contract()
    rules = _dict(contract.get("graph_relationship_rules"))
    partition_rules = _dict(rules.get(source_partition))
    return _strings(partition_rules.get("allowed_relationships"))


def graph_relationships_for_family_source(
    *,
    family_status: str,
    source_partition: str,
    source_status: str | None = None,
    contract: dict | None = None,
) -> tuple[str, bool, list[str]]:
    contract = contract or _default_source_partition_contract()
    if family_status == "superseded":
        return (
            "supersession_or_replacement_source",
            False,
            graph_relationships_for_partition(CURRENTNESS_SUPERSESSION_ARCHIVE, contract),
        )
    if source_partition != ACTIVE_REVIEW_CORPUS:
        return (
            "candidate_blocked_or_currentness_only_source",
            False,
            graph_relationships_for_partition(source_partition, contract),
        )
    return (
        "active_authority_source",
        str(source_status or "") in SUCCESSFUL_SOURCE_STATUSES,
        graph_relationships_for_partition(ACTIVE_REVIEW_CORPUS, contract),
    )


def validate_catalog_source_partitions(
    *,
    catalog_rows: list[dict],
    catalog_source_partitions: list[dict],
    contract: dict,
) -> list[dict]:
    contract_checks = validate_source_partition_contract(contract)
    partition_by_source_record_id = {
        str(record.get("source_record_id") or ""): record for record in catalog_source_partitions
    }
    invalid_partition_records = [
        {
            "source_record_id": record.get("source_record_id"),
            "source_partition": record.get("source_partition"),
        }
        for record in catalog_source_partitions
        if record.get("source_partition") not in VALID_SOURCE_PARTITIONS
    ]
    missing_partition_source_record_ids = sorted(
        str(row.get("source_record_id") or "")
        for row in catalog_rows
        if str(row.get("source_record_id") or "") not in partition_by_source_record_id
    )
    non_current_active_source_record_ids = sorted(
        str(row.get("source_record_id") or "")
        for row in catalog_rows
        if _has_non_current_source_marker(row)
        and partition_by_source_record_id.get(str(row.get("source_record_id") or ""), {}).get(
            "source_partition"
        )
        == ACTIVE_REVIEW_CORPUS
    )
    reserved_220_active_source_record_ids = sorted(
        str(row.get("source_record_id") or "")
        for row in catalog_rows
        if _is_reserved_36_cfr_part_220_source(row)
        and partition_by_source_record_id.get(str(row.get("source_record_id") or ""), {}).get(
            "source_partition"
        )
        == ACTIVE_REVIEW_CORPUS
    )
    fsh_validation = _validate_fsh_1909_15_chapter_records(
        catalog_rows=catalog_rows,
        partition_by_source_record_id=partition_by_source_record_id,
        contract=contract,
    )
    return contract_checks + [
        _check(
            "catalog_source_records_have_source_partitions",
            not missing_partition_source_record_ids,
            [],
            missing_partition_source_record_ids,
        ),
        _check(
            "source_partitions_use_valid_values",
            not invalid_partition_records,
            [],
            invalid_partition_records,
        ),
        _check(
            "non_current_sources_not_in_active_review_corpus",
            not non_current_active_source_record_ids,
            [],
            non_current_active_source_record_ids,
        ),
        _check(
            "reserved_or_superseded_authorities_not_active_controlling",
            not reserved_220_active_source_record_ids,
            [],
            reserved_220_active_source_record_ids,
        ),
        _check(
            "fsh_1909_15_chapter_records_are_not_collapsed",
            fsh_validation["passed"],
            fsh_validation["expected"],
            fsh_validation["actual"],
        ),
    ]


def validate_source_partition_contract(contract: dict) -> list[dict]:
    source_partitions = _dict_list(contract.get("source_partitions"))
    partition_ids = {
        str(partition.get("partition_id") or "")
        for partition in source_partitions
        if partition.get("partition_id")
    }
    partition_eligibility_by_id = {
        str(partition.get("partition_id") or ""): partition.get("eligible_for_active_review_rules")
        for partition in source_partitions
        if partition.get("partition_id")
    }
    partition_eligibility_violations = {
        partition_id: partition_eligibility_by_id.get(partition_id)
        for partition_id, expected in EXPECTED_PARTITION_ACTIVE_ELIGIBILITY.items()
        if partition_eligibility_by_id.get(partition_id) is not expected
    }
    missing_partition_ids = sorted(REQUIRED_SOURCE_PARTITIONS - partition_ids)
    unknown_partition_ids = sorted(partition_ids - VALID_SOURCE_PARTITIONS)
    graph_relationship_rules = _dict(contract.get("graph_relationship_rules"))
    missing_graph_rule_partition_ids = sorted(
        partition_id
        for partition_id in REQUIRED_SOURCE_PARTITIONS
        if partition_id not in graph_relationship_rules
    )
    malformed_graph_rule_partition_ids = sorted(
        partition_id
        for partition_id in REQUIRED_SOURCE_PARTITIONS
        if partition_id in graph_relationship_rules
        and not isinstance(graph_relationship_rules.get(partition_id), dict)
    )
    malformed_relationship_list_partition_ids = sorted(
        partition_id
        for partition_id in REQUIRED_SOURCE_PARTITIONS
        if partition_id in graph_relationship_rules
        and not isinstance(
            _graph_rule(graph_relationship_rules, partition_id).get("allowed_relationships"),
            list,
        )
    )
    non_active_relationship_violations = {
        partition_id: sorted(
            set(
                _strings(
                    _graph_rule(graph_relationship_rules, partition_id).get("allowed_relationships")
                )
            )
            - NON_ACTIVE_ALLOWED_RELATIONSHIPS
        )
        for partition_id in (CURRENTNESS_SUPERSESSION_ARCHIVE, CANDIDATE_BLOCKED_SOURCE)
    }
    non_active_relationship_violations = {
        partition_id: relationships
        for partition_id, relationships in non_active_relationship_violations.items()
        if relationships
    }
    active_rule = _graph_rule(graph_relationship_rules, ACTIVE_REVIEW_CORPUS)
    non_active_eligibility_violations = [
        partition_id
        for partition_id in (CURRENTNESS_SUPERSESSION_ARCHIVE, CANDIDATE_BLOCKED_SOURCE)
        if _graph_rule(graph_relationship_rules, partition_id).get("eligible_for_active_review_rules")
        is True
    ]
    fsh_contract = _fsh_contract(contract)
    fsh_minimum = _int_or_none(fsh_contract.get("minimum_distinct_chapter_records_when_used"))
    source_delta_plan = contract.get("workbook_source_delta_plan")
    missing_delta_plan_keys = sorted(
        key
        for key in REQUIRED_WORKBOOK_SOURCE_DELTA_PLAN_KEYS
        if not isinstance(source_delta_plan, dict) or not source_delta_plan.get(key)
    )
    reserved_rules = _dict_list(contract.get("reserved_superseded_authority_rules"))
    has_reserved_220_boundary = any(
        str(rule.get("authority_label") or "").lower() == "36 cfr part 220"
        and rule.get("required_partition_when_source_record_exists")
        == CURRENTNESS_SUPERSESSION_ARCHIVE
        for rule in reserved_rules
    )
    return [
        _check(
            "source_partition_contract_schema_loaded",
            contract.get("schema_version") == SOURCE_PARTITION_CONTRACT_SCHEMA_VERSION,
            SOURCE_PARTITION_CONTRACT_SCHEMA_VERSION,
            contract.get("schema_version"),
        ),
        _check(
            "source_partition_contract_defines_required_partitions",
            not missing_partition_ids,
            [],
            missing_partition_ids,
        ),
        _check(
            "source_partition_contract_uses_known_partition_ids",
            not unknown_partition_ids,
            [],
            unknown_partition_ids,
        ),
        _check(
            "source_partition_contract_partition_eligibility_matches_boundary",
            not partition_eligibility_violations,
            EXPECTED_PARTITION_ACTIVE_ELIGIBILITY,
            partition_eligibility_violations,
        ),
        _check(
            "source_partition_contract_defines_graph_rules_for_each_partition",
            not missing_graph_rule_partition_ids,
            [],
            missing_graph_rule_partition_ids,
        ),
        _check(
            "source_partition_contract_graph_rules_are_objects",
            not malformed_graph_rule_partition_ids,
            [],
            malformed_graph_rule_partition_ids,
        ),
        _check(
            "source_partition_contract_graph_relationships_are_lists",
            not malformed_relationship_list_partition_ids,
            [],
            malformed_relationship_list_partition_ids,
        ),
        _check(
            "active_review_corpus_is_eligible_for_active_review_rules",
            active_rule.get("eligible_for_active_review_rules") is True,
            True,
            active_rule.get("eligible_for_active_review_rules"),
        ),
        _check(
            "non_active_partitions_are_not_eligible_for_active_review_rules",
            not non_active_eligibility_violations,
            [],
            non_active_eligibility_violations,
        ),
        _check(
            "non_active_partition_relationships_are_limited_to_currentness",
            not non_active_relationship_violations,
            {},
            non_active_relationship_violations,
        ),
        _check(
            "source_partition_contract_defines_fsh_1909_15_chapter_boundary",
            bool(fsh_minimum and fsh_minimum >= 2),
            "minimum_distinct_chapter_records_when_used >= 2",
            fsh_contract,
        ),
        _check(
            "source_partition_contract_defines_reserved_36_cfr_part_220_boundary",
            has_reserved_220_boundary,
            {
                "authority_label": "36 CFR part 220",
                "required_partition_when_source_record_exists": CURRENTNESS_SUPERSESSION_ARCHIVE,
            },
            reserved_rules,
        ),
        _check(
            "source_partition_contract_defines_workbook_source_delta_plan",
            not missing_delta_plan_keys,
            [],
            missing_delta_plan_keys,
        ),
    ]


def fsh_1909_15_chapter_kind(row: dict) -> str | None:
    text = _row_text(row)
    if "1909.15" not in text or "fsh" not in text:
        return None
    if re.search(r"\b(contents?|zero[- ]code|chapter\s*0|ch\.\s*0)\b", text):
        return "contents_zero_code"
    if re.search(r"\b(environmental analysis|chapter\s*10|ch\.\s*10)\b", text):
        return "environmental_analysis"
    if re.search(
        r"\b(environmental impact statement|eis|chapter\s*20|ch\.\s*20)\b",
        text,
    ):
        return "environmental_impact_statement"
    if re.search(r"\b(environmental assessment|ea|chapter\s*30|ch\.\s*30)\b", text):
        return "environmental_assessment"
    if re.search(r"\b(related documents?|chapter\s*40|ch\.\s*40)\b", text):
        return "related_documents"
    return "collapsed_handbook"


def _validate_fsh_1909_15_chapter_records(
    *,
    catalog_rows: list[dict],
    partition_by_source_record_id: dict[str, dict],
    contract: dict,
) -> dict:
    fsh_rows = [
        row
        for row in catalog_rows
        if fsh_1909_15_chapter_kind(row)
        and partition_by_source_record_id.get(str(row.get("source_record_id") or ""), {}).get(
            "source_partition"
        )
        == ACTIVE_REVIEW_CORPUS
    ]
    if not fsh_rows:
        return {"passed": True, "expected": "no active FSH 1909.15 records or chapterized records", "actual": []}

    fsh_contract = _fsh_contract(contract)
    minimum_chapter_records = int(
        fsh_contract.get("minimum_distinct_chapter_records_when_used") or 2
    )
    chapter_kinds = sorted(
        {
            fsh_1909_15_chapter_kind(row)
            for row in fsh_rows
            if fsh_1909_15_chapter_kind(row) != "collapsed_handbook"
        }
    )
    collapsed_source_record_ids = sorted(
        str(row.get("source_record_id") or "")
        for row in fsh_rows
        if fsh_1909_15_chapter_kind(row) == "collapsed_handbook"
    )
    passed = len(chapter_kinds) >= minimum_chapter_records and not (
        collapsed_source_record_ids and len(chapter_kinds) < minimum_chapter_records
    )
    return {
        "passed": passed,
        "expected": {
            "minimum_distinct_chapter_records_when_used": minimum_chapter_records,
            "collapsed_record_disallowed_when_chapter_records_available": bool(
                fsh_contract.get("collapsed_record_disallowed_when_chapter_records_available")
            ),
        },
        "actual": {
            "chapter_kinds": chapter_kinds,
            "collapsed_source_record_ids": collapsed_source_record_ids,
        },
    }


def _explicit_source_partition(row: dict) -> str | None:
    explicit = row.get("source_partition")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        explicit = metadata.get("source_partition")
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip()
    return None


def _has_non_current_source_marker(row: dict) -> bool:
    text = _row_text(row)
    if re.search(r"\b(rescinded|revoked|repealed|superseded|not[- ]current)\b", text):
        return True
    if re.search(
        r"\b(reserved\s+(?:authority|regulation|source|cfr|code|part)|"
        r"(?:authority|regulation|source|cfr|code|part)\s+reserved)\b",
        text,
    ):
        return True
    return _is_reserved_36_cfr_part_220_source(row)


def _is_reserved_36_cfr_part_220_source(row: dict) -> bool:
    text = _row_text(row)
    return bool(
        re.search(r"\b36\s+cfr\s+part\s+220\b", text)
        and re.search(r"\b(reserved|superseded|former|removed|not[- ]current)\b", text)
    )


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
    metadata = row.get("metadata")
    if isinstance(metadata, dict):
        for field in (
            "title",
            "document_type",
            "currentness_notes",
            "source_currentness_status",
            "supersession_status",
            "workbook_url",
        ):
            value = metadata.get(field)
            if isinstance(value, str):
                fields.append(value)
    return " ".join(fields).lower()


def _partition_eligibility(source_partition: str, contract: dict) -> bool:
    rules = _dict(contract.get("graph_relationship_rules"))
    return bool(_graph_rule(rules, source_partition).get("eligible_for_active_review_rules"))


def _fsh_contract(contract: dict) -> dict:
    for entry in _dict_list(contract.get("handbook_chapter_requirements")):
        if entry.get("handbook_id") == "fsh_1909_15":
            return entry
    return {}


def _dict(value: object) -> dict:
    return value if isinstance(value, dict) else {}


def _dict_list(value: object) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _graph_rule(graph_relationship_rules: dict, partition_id: str) -> dict:
    return _dict(graph_relationship_rules.get(partition_id))


def _int_or_none(value: object) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _strings(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _default_source_partition_contract() -> dict[str, Any]:
    return {
        "schema_version": SOURCE_PARTITION_CONTRACT_SCHEMA_VERSION,
        "source_partition_contract_id": "builtin-source-partitions-v1",
        "source_partitions": [
            {"partition_id": ACTIVE_REVIEW_CORPUS, "eligible_for_active_review_rules": True},
            {
                "partition_id": CURRENTNESS_SUPERSESSION_ARCHIVE,
                "eligible_for_active_review_rules": False,
            },
            {"partition_id": CANDIDATE_BLOCKED_SOURCE, "eligible_for_active_review_rules": False},
        ],
        "graph_relationship_rules": {
            ACTIVE_REVIEW_CORPUS: {
                "eligible_for_active_review_rules": True,
                "allowed_relationships": [
                    "SUPPORTED_BY_SOURCE",
                    "CLAIM_SUPPORTS_RULE",
                    "RULE_DERIVES_FROM_AUTHORITY",
                    "SUPPORTS_FINDING",
                    "HAS_CURRENTNESS_STATUS",
                ],
            },
            CURRENTNESS_SUPERSESSION_ARCHIVE: {
                "eligible_for_active_review_rules": False,
                "allowed_relationships": [
                    "SUPERSEDED_BY",
                    "REPLACES_RESERVED_AUTHORITY",
                    "HAS_CURRENTNESS_STATUS",
                    "BLOCKED_BY",
                ],
            },
            CANDIDATE_BLOCKED_SOURCE: {
                "eligible_for_active_review_rules": False,
                "allowed_relationships": ["HAS_CURRENTNESS_STATUS", "BLOCKED_BY"],
            },
        },
        "handbook_chapter_requirements": [
            {
                "handbook_id": "fsh_1909_15",
                "minimum_distinct_chapter_records_when_used": 2,
                "collapsed_record_disallowed_when_chapter_records_available": True,
            }
        ],
        "reserved_superseded_authority_rules": [
            {
                "authority_label": "36 CFR part 220",
                "required_partition_when_source_record_exists": CURRENTNESS_SUPERSESSION_ARCHIVE,
            }
        ],
        "workbook_source_delta_plan": {
            "environmental_justice_civil_rights": "Add official sources before active review use.",
            "fsh_1909_15": "Add separate current chapter records before claiming completeness.",
            "reserved_36_cfr_part_220": "Archive reserved or superseded records if added.",
        },
    }


def _check(name: str, passed: bool, expected: object, actual: object) -> dict:
    return {
        "name": name,
        "passed": bool(passed),
        "expected": expected,
        "actual": actual,
    }
