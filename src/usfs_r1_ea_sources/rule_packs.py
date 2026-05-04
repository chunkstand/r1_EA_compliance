from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
import json
import re


RULE_PACK_SCHEMA_VERSION = "compliance-rule-pack-v0"
GENERATED_RULE_PACK_SCHEMA_VERSION = "generated-compliance-rule-pack-v0"
SUPPORTED_RULE_PACK_SCHEMA_VERSIONS = {
    RULE_PACK_SCHEMA_VERSION,
    GENERATED_RULE_PACK_SCHEMA_VERSION,
}
DEFAULT_RULE_PACK_PATH = Path("config/compliance_rule_pack_nepa_ea_v0.json")
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
AUTHORITY_CATEGORIES = {
    "agency_policy",
    "case_law",
    "executive_order",
    "forest_plan",
    "law",
    "regulation",
    "state_requirement",
}
APPLICABILITY_MODES = {"baseline", "conditional"}
ALLOWED_SOURCE_FILTER_KEYS = {
    "authority_level",
    "citation",
    "document_role",
    "host",
    "review_topic",
    "source_record_id",
    "topic",
}


def load_rule_pack(path: Path) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Compliance rule pack must be a JSON object.")
    return value


def validate_rule_pack(rule_pack: dict) -> dict:
    checks = [
        _check_rule_pack_schema(rule_pack),
        _check_rule_pack_identity(rule_pack),
        _check_rule_pack_identity_safe(rule_pack),
        _check_rules_present(rule_pack),
        _check_rule_ids_unique(rule_pack),
        _check_rule_ids_safe(rule_pack),
        _check_required_rule_fields(rule_pack),
        _check_rule_queries_and_terms(rule_pack),
        _check_rule_package_section_preferences(rule_pack),
        _check_rule_source_filters(rule_pack),
        _check_rule_source_filter_keys(rule_pack),
        _check_rule_authority_metadata(rule_pack),
        _check_rule_pack_baseline_source_records(rule_pack),
    ]
    return {
        "schema_version": "compliance-rule-pack-validation-v0",
        "created_at": _utc_now(),
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
    }


def _check_rule_pack_schema(rule_pack: dict) -> dict:
    actual = rule_pack.get("schema_version")
    return {
        "name": "rule_pack_schema_version",
        "passed": actual in SUPPORTED_RULE_PACK_SCHEMA_VERSIONS,
        "details": {
            "expected": sorted(SUPPORTED_RULE_PACK_SCHEMA_VERSIONS),
            "actual": actual,
        },
    }


def _check_rule_pack_identity(rule_pack: dict) -> dict:
    missing = [
        field
        for field in ("rule_pack_id", "version", "title")
        if not str(rule_pack.get(field) or "").strip()
    ]
    return {
        "name": "rule_pack_identity_present",
        "passed": not missing,
        "details": {"missing": missing},
    }


def _check_rule_pack_identity_safe(rule_pack: dict) -> dict:
    unsafe = [
        field
        for field in ("rule_pack_id", "version")
        if str(rule_pack.get(field) or "").strip()
        and not SAFE_ID_RE.fullmatch(str(rule_pack.get(field)))
    ]
    return {
        "name": "rule_pack_identity_values_are_safe",
        "passed": not unsafe,
        "details": {"unsafe_fields": unsafe},
    }


def _check_rules_present(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules")
    return {
        "name": "rules_present",
        "passed": isinstance(rules, list) and bool(rules),
        "details": {"rule_count": len(rules) if isinstance(rules, list) else 0},
    }


def _check_rule_ids_unique(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    ids = [str(rule.get("id") or "") for rule in rules if isinstance(rule, dict)]
    counts = Counter(ids)
    duplicates = sorted(rule_id for rule_id, count in counts.items() if rule_id and count > 1)
    missing = sum(1 for rule_id in ids if not rule_id)
    return {
        "name": "rule_ids_unique",
        "passed": not duplicates and missing == 0 and len(ids) == len(rules),
        "details": {"duplicate_ids": duplicates, "missing_id_count": missing},
    }


def _check_rule_ids_safe(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    unsafe = [
        rule.get("id")
        for rule in rules
        if isinstance(rule, dict)
        and str(rule.get("id") or "").strip()
        and not SAFE_ID_RE.fullmatch(str(rule.get("id")))
    ]
    return {
        "name": "rule_ids_are_safe",
        "passed": not unsafe,
        "details": {"rule_ids": unsafe},
    }


def _check_required_rule_fields(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    required = {
        "id",
        "title",
        "question",
        "requirement",
        "severity",
        "package_query",
        "source_query",
    }
    missing = []
    for rule in rules:
        if not isinstance(rule, dict):
            missing.append({"rule_id": None, "missing": sorted(required)})
            continue
        rule_missing = sorted(field for field in required if not str(rule.get(field) or "").strip())
        if rule_missing:
            missing.append({"rule_id": rule.get("id"), "missing": rule_missing})
    return {
        "name": "required_rule_fields_present",
        "passed": not missing,
        "details": {"missing": missing},
    }


def _check_rule_queries_and_terms(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        terms = rule.get("package_terms")
        if not isinstance(terms, list) or not any(str(term).strip() for term in terms):
            failures.append(rule.get("id"))
    return {
        "name": "rule_package_terms_present",
        "passed": not failures,
        "details": {"rule_ids": failures},
    }


def _check_rule_package_section_preferences(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        invalid = []
        section_terms = rule.get("package_section_terms")
        section_term_groups = rule.get("package_section_term_groups")
        if section_terms is not None and not _valid_nonempty_term_list(section_terms):
            invalid.append("package_section_terms")
        if section_term_groups is not None and not _valid_nonempty_term_groups(section_term_groups):
            invalid.append("package_section_term_groups")
        if invalid:
            failures.append(
                {
                    "rule_id": rule.get("id"),
                    "invalid": sorted(invalid),
                }
            )
    return {
        "name": "rule_package_section_preferences_are_valid",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_rule_source_filters(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        filters = rule.get("source_filters")
        if not isinstance(filters, dict) or not filters:
            failures.append(rule.get("id"))
    return {
        "name": "rule_source_filters_present",
        "passed": not failures,
        "details": {"rule_ids": failures},
    }


def _check_rule_source_filter_keys(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        filters = rule.get("source_filters")
        if not isinstance(filters, dict):
            continue
        unknown_keys = sorted(set(filters) - ALLOWED_SOURCE_FILTER_KEYS)
        empty_values = sorted(
            key
            for key, value in filters.items()
            if key in ALLOWED_SOURCE_FILTER_KEYS and not str(value or "").strip()
        )
        if unknown_keys or empty_values:
            failures.append(
                {
                    "rule_id": rule.get("id"),
                    "unknown_keys": unknown_keys,
                    "empty_values": empty_values,
                }
            )
    return {
        "name": "rule_source_filter_keys_are_supported",
        "passed": not failures,
        "details": {
            "allowed_keys": sorted(ALLOWED_SOURCE_FILTER_KEYS),
            "failures": failures,
        },
    }


def _check_rule_authority_metadata(rule_pack: dict) -> dict:
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    failures = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
        authority_category = str(rule.get("authority_category") or "").strip()
        applicability_mode = str(rule.get("applicability_mode") or "").strip()
        source_record_id = str(
            rule.get("authority_source_record_id") or filters.get("source_record_id") or ""
        ).strip()
        missing = []
        invalid = []
        if not authority_category:
            missing.append("authority_category")
        elif authority_category not in AUTHORITY_CATEGORIES:
            invalid.append("authority_category")
        if not applicability_mode:
            missing.append("applicability_mode")
        elif applicability_mode not in APPLICABILITY_MODES:
            invalid.append("applicability_mode")
        if not source_record_id:
            missing.append("source_record_id")
        if applicability_mode == "conditional":
            terms = rule.get("applies_if_package_terms")
            term_groups = rule.get("applies_if_package_term_groups")
            negative_terms = rule.get("does_not_apply_if_package_terms")
            has_terms = isinstance(terms, list) and any(str(term).strip() for term in terms)
            has_term_groups = _valid_nonempty_term_groups(term_groups)
            if not has_terms and not has_term_groups:
                missing.append("applies_if_package_terms")
            if term_groups is not None and not has_term_groups:
                invalid.append("applies_if_package_term_groups")
            if negative_terms is not None and not _valid_nonempty_term_list(negative_terms):
                invalid.append("does_not_apply_if_package_terms")
        if missing or invalid:
            failures.append(
                {
                    "rule_id": rule.get("id"),
                    "missing": sorted(missing),
                    "invalid": sorted(invalid),
                }
            )
    return {
        "name": "rule_authority_metadata_present",
        "passed": not failures,
        "details": {
            "allowed_authority_categories": sorted(AUTHORITY_CATEGORIES),
            "allowed_applicability_modes": sorted(APPLICABILITY_MODES),
            "failures": failures,
        },
    }


def _check_rule_pack_baseline_source_records(rule_pack: dict) -> dict:
    expected = _baseline_source_record_ids(rule_pack)
    raw_expected = rule_pack.get("baseline_source_record_ids")
    if raw_expected is None:
        return {
            "name": "baseline_source_records_covered",
            "passed": True,
            "details": {
                "enforced": False,
                "baseline_source_record_count": 0,
                "missing_source_record_ids": [],
                "non_baseline_rule_ids": [],
            },
        }
    invalid_shape = (
        not isinstance(raw_expected, list) or not expected or len(expected) != len(raw_expected)
    )
    duplicate_ids = sorted(
        source_record_id for source_record_id, count in Counter(expected).items() if count > 1
    )
    unsafe_ids = sorted(
        source_record_id
        for source_record_id in expected
        if not SAFE_ID_RE.fullmatch(source_record_id)
    )
    rules = rule_pack.get("rules") if isinstance(rule_pack.get("rules"), list) else []
    rules_by_source_record_id = defaultdict(list)
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        source_record_id = _rule_source_record_id(rule)
        if source_record_id:
            rules_by_source_record_id[source_record_id].append(rule)
    missing = sorted(
        source_record_id
        for source_record_id in expected
        if source_record_id not in rules_by_source_record_id
    )
    non_baseline = sorted(
        str(rule.get("id"))
        for source_record_id in expected
        for rule in rules_by_source_record_id.get(source_record_id, [])
        if str(rule.get("applicability_mode") or "") != "baseline"
    )
    return {
        "name": "baseline_source_records_covered",
        "passed": not invalid_shape
        and not duplicate_ids
        and not unsafe_ids
        and not missing
        and not non_baseline,
        "details": {
            "enforced": True,
            "baseline_source_record_count": len(expected),
            "missing_source_record_ids": missing,
            "duplicate_source_record_ids": duplicate_ids,
            "unsafe_source_record_ids": unsafe_ids,
            "non_baseline_rule_ids": non_baseline,
        },
    }


def _valid_nonempty_term_groups(value) -> bool:
    return isinstance(value, list) and all(
        isinstance(group, list) and any(str(term).strip() for term in group)
        for group in value
    ) and bool(value)


def _valid_nonempty_term_list(value) -> bool:
    return isinstance(value, list) and all(str(term).strip() for term in value) and bool(value)


def _baseline_source_record_ids(rule_pack: dict) -> list[str]:
    value = rule_pack.get("baseline_source_record_ids")
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _rule_source_record_id(rule: dict) -> str | None:
    filters = rule.get("source_filters") if isinstance(rule.get("source_filters"), dict) else {}
    value = rule.get("authority_source_record_id") or filters.get("source_record_id")
    value = str(value or "").strip()
    return value or None


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
