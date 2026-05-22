from __future__ import annotations

from collections import Counter
from pathlib import Path

from .compliance_review_eval_generated import _case_requires_generated_rule_pack
from .eval_metrics import read_json_payload
from .rule_packs import SAFE_ID_RE


COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION = "compliance-review-eval-v1"
SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS = {"claim_type", "rule_id", "status"}
VALID_FINDING_STATUSES = {"pass", "gap", "uncertain", "not_applicable"}
VALID_CLAIM_TYPES = {
    "no_compliance_claim",
    "package_evidence_gap",
    "supported_compliance_finding",
}


def load_compliance_review_eval_contract(path: Path) -> tuple[dict, list[dict], bool]:
    payload = read_json_payload(path, label="compliance review eval file")
    if isinstance(payload, list):
        cases = validated_compliance_review_eval_cases(payload, legacy_format=True)
        return (
            {
                "schema_version": "legacy-compliance-review-eval-list-v0",
                "eval_id": f"legacy-{path.stem}",
                "coverage_requirements": {},
                "metric_thresholds": {},
                "cases": cases,
            },
            cases,
            True,
        )
    if payload.get("schema_version") != COMPLIANCE_REVIEW_EVAL_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported compliance review eval schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    if not str(payload.get("eval_id") or "").strip():
        raise ValueError("Compliance review eval contract missing 'eval_id'.")
    if not isinstance(payload.get("coverage_requirements"), dict):
        raise ValueError("Compliance review eval contract missing 'coverage_requirements'.")
    if not isinstance(payload.get("metric_thresholds"), dict):
        raise ValueError("Compliance review eval contract missing 'metric_thresholds'.")
    validate_compliance_review_coverage_requirements(payload["coverage_requirements"])
    cases = validated_compliance_review_eval_cases(payload.get("cases"), legacy_format=False)
    return payload, cases, False


def validated_compliance_review_eval_cases(
    payload: object,
    *,
    legacy_format: bool,
) -> list[dict]:
    if not isinstance(payload, list) or not payload:
        raise ValueError(
            "Compliance review eval file must contain a non-empty JSON list."
            if legacy_format
            else "Compliance review eval contract must contain non-empty cases."
        )
    case_ids = []
    for index, case in enumerate(payload):
        if not isinstance(case, dict):
            raise ValueError(f"Compliance review eval case {index} must be an object.")
        case_id = str(case.get("id") or "").strip()
        if not case_id:
            raise ValueError(f"Compliance review eval case {index} is missing 'id'.")
        if not SAFE_ID_RE.fullmatch(case_id):
            raise ValueError(
                f"Compliance review eval case {index} id must contain only safe path characters."
            )
        case_ids.append(case_id)
        validate_eval_package_fixture(index, case)
        validate_eval_filters(index, case)
        validate_eval_expected_statuses(index, case)
        validate_eval_expected_claim_types(index, case)
        validate_eval_expected_bool_map(index, case, "expected_package_evidence")
        validate_eval_expected_bool_map(index, case, "expected_source_evidence")
        validate_eval_expected_bool_map(index, case, "expected_source_claim_links")
        validate_eval_expected_string_list_map(index, case, "expected_source_record_ids")
        validate_eval_expected_string_list_map(index, case, "expected_source_document_roles")
        validate_eval_status_counts(index, case)
        validate_eval_string_list(index, case, "expected_unsupported_finding_ids")
        validate_optional_bool(index, case, "expected_validation_passed")
        validate_optional_bool(index, case, "expected_reviewer_ready")
        validate_optional_bool(index, case, "require_graph_coverage")
        validate_optional_bool(index, case, "hard_negative_package")
        validate_optional_bool(index, case, "conditional_subset")
        validate_optional_bool(index, case, "all_authorities_control")
        validate_positive_eval_int(index, case, "min_findings")
        validate_positive_eval_int(index, case, "source_top_k")
        validate_positive_eval_int(index, case, "package_top_k")
    duplicates = sorted(case_id for case_id in set(case_ids) if case_ids.count(case_id) > 1)
    if duplicates:
        raise ValueError(f"Duplicate compliance review eval case IDs: {duplicates}")
    return payload


def validate_compliance_review_coverage_requirements(requirements: dict) -> None:
    for key in (
        "case_count",
        "hard_negative_package_case_count",
        "conditional_subset_case_count",
        "all_authorities_control_case_count",
    ):
        value = requirements.get(key)
        if not isinstance(value, int) or value < 0:
            raise ValueError(
                "Compliance review eval coverage_requirements."
                f"{key} must be a non-negative integer."
            )


def validate_eval_package_fixture(index: int, case: dict) -> None:
    has_text = bool(str(case.get("package_text") or "").strip())
    has_path = bool(str(case.get("package_path") or "").strip())
    if has_text == has_path:
        raise ValueError(
            f"Compliance review eval case {index} must define exactly one of "
            "package_text or package_path."
        )


def validate_compliance_review_eval_cases_against_rule_pack(
    cases: list[dict],
    rule_pack: dict,
) -> None:
    expected_rule_ids = {str(rule["id"]) for rule in rule_pack["rules"]}
    rule_count = len(expected_rule_ids)
    for index, case in enumerate(cases):
        case_id = str(case["id"])
        status_rule_ids = set(string_map(case["expected_statuses"]))
        generated_rule_pack_case = _case_requires_generated_rule_pack(case)
        if status_rule_ids != expected_rule_ids:
            missing = sorted(expected_rule_ids - status_rule_ids)
            unexpected = [] if generated_rule_pack_case else sorted(status_rule_ids - expected_rule_ids)
            if missing or unexpected:
                raise ValueError(
                    f"Compliance review eval case {index} ({case_id}) expected_statuses must "
                    f"cover every rule in the rule pack. Missing: {missing}; unexpected: {unexpected}."
                )
        allowed_rule_ids = status_rule_ids if generated_rule_pack_case else expected_rule_ids
        for key in (
            "expected_claim_types",
            "expected_package_evidence",
            "expected_source_evidence",
            "expected_source_claim_links",
            "expected_source_record_ids",
            "expected_source_document_roles",
        ):
            validate_eval_rule_map_keys(index, case_id, case.get(key) or {}, allowed_rule_ids, key)
        unsupported_ids = set(str(value) for value in case.get("expected_unsupported_finding_ids", []))
        unexpected_unsupported = sorted(unsupported_ids - allowed_rule_ids)
        if unexpected_unsupported:
            raise ValueError(
                f"Compliance review eval case {index} ({case_id}) expected_unsupported_finding_ids "
                f"contains unknown rule IDs: {unexpected_unsupported}."
            )
        filters = case.get("filters") or {}
        if "rule_id" in filters:
            rule_filter_ids = set(filter_values(filters["rule_id"]))
            unknown_filters = sorted(rule_filter_ids - allowed_rule_ids)
            if unknown_filters:
                raise ValueError(
                    f"Compliance review eval case {index} ({case_id}) rule_id filter "
                    f"contains unknown rule IDs: {unknown_filters}."
                )
        expected_counts = {
            str(status): int(count)
            for status, count in (case.get("expected_finding_status_counts") or {}).items()
        }
        if expected_counts:
            if _case_requires_generated_rule_pack(case):
                min_findings = int(case.get("min_findings") or 1)
                if sum(expected_counts.values()) < min_findings:
                    raise ValueError(
                        f"Compliance review eval case {index} ({case_id}) expected_finding_status_counts "
                        "must cover at least min_findings for generated-rule-pack cases."
                    )
            else:
                counts_from_statuses = dict(
                    Counter(str(status) for status in case["expected_statuses"].values())
                )
                normalized_expected_counts = {
                    status: count for status, count in expected_counts.items() if count
                }
                if (
                    sum(expected_counts.values()) != rule_count
                    or normalized_expected_counts != counts_from_statuses
                ):
                    raise ValueError(
                        f"Compliance review eval case {index} ({case_id}) expected_finding_status_counts "
                        "must match expected_statuses and sum to the rule count."
                    )


def validate_eval_rule_map_keys(
    index: int,
    case_id: str,
    values: dict,
    expected_rule_ids: set[str],
    key: str,
) -> None:
    actual = set(str(rule_id) for rule_id in values)
    unexpected = sorted(actual - expected_rule_ids)
    if unexpected:
        raise ValueError(
            f"Compliance review eval case {index} ({case_id}) {key} contains unknown rule IDs: "
            f"{unexpected}."
        )


def validate_eval_filters(index: int, case: dict) -> None:
    filters = case.get("filters") or {}
    if not isinstance(filters, dict):
        raise ValueError(f"Compliance review eval case {index} filters must be an object.")
    unknown_keys = sorted(set(filters) - SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS)
    empty_values = [
        key
        for key, value in filters.items()
        if key in SUPPORTED_COMPLIANCE_REVIEW_EVAL_FILTERS and not filter_values(value)
    ]
    if unknown_keys or empty_values:
        details = []
        if unknown_keys:
            details.append(f"unsupported filters: {unknown_keys}")
        if empty_values:
            details.append(f"empty filters: {empty_values}")
        raise ValueError(
            f"Compliance review eval case {index} has invalid filters; " + "; ".join(details)
        )
    if "status" in filters:
        unsupported = sorted(set(filter_values(filters["status"])) - VALID_FINDING_STATUSES)
        if unsupported:
            raise ValueError(
                f"Compliance review eval case {index} has unsupported status filters: "
                f"{unsupported}."
            )
    if "claim_type" in filters:
        unsupported = sorted(set(filter_values(filters["claim_type"])) - VALID_CLAIM_TYPES)
        if unsupported:
            raise ValueError(
                f"Compliance review eval case {index} has unsupported claim_type filters: "
                f"{unsupported}."
            )


def validate_eval_expected_statuses(index: int, case: dict) -> None:
    expected = case.get("expected_statuses")
    if not isinstance(expected, dict) or not expected:
        raise ValueError(
            f"Compliance review eval case {index} expected_statuses must be a non-empty object."
        )
    invalid = sorted(
        str(status)
        for status in expected.values()
        if str(status) not in VALID_FINDING_STATUSES
    )
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} has unsupported expected_statuses: {invalid}."
        )


def validate_eval_expected_claim_types(index: int, case: dict) -> None:
    expected = case.get("expected_claim_types") or {}
    if not isinstance(expected, dict):
        raise ValueError(
            f"Compliance review eval case {index} expected_claim_types must be an object."
        )
    invalid = sorted(
        str(claim_type)
        for claim_type in expected.values()
        if str(claim_type) not in VALID_CLAIM_TYPES
    )
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} has unsupported expected_claim_types: "
            f"{invalid}."
        )


def validate_eval_expected_bool_map(index: int, case: dict, key: str) -> None:
    expected = case.get(key) or {}
    if not isinstance(expected, dict):
        raise ValueError(f"Compliance review eval case {index} {key} must be an object.")
    invalid = sorted(str(rule_id) for rule_id, value in expected.items() if not isinstance(value, bool))
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} {key} values must be booleans: {invalid}."
        )


def validate_eval_expected_string_list_map(index: int, case: dict, key: str) -> None:
    expected = case.get(key) or {}
    if not isinstance(expected, dict):
        raise ValueError(f"Compliance review eval case {index} {key} must be an object.")
    invalid = []
    for rule_id, values in expected.items():
        if not isinstance(values, list) or not values:
            invalid.append(str(rule_id))
            continue
        if any(not str(value).strip() for value in values):
            invalid.append(str(rule_id))
    if invalid:
        raise ValueError(
            f"Compliance review eval case {index} {key} values must be non-empty "
            f"lists of strings: {invalid}."
        )


def validate_eval_status_counts(index: int, case: dict) -> None:
    expected = case.get("expected_finding_status_counts") or {}
    if not isinstance(expected, dict):
        raise ValueError(
            f"Compliance review eval case {index} expected_finding_status_counts must be an object."
        )
    unsupported = sorted(set(str(status) for status in expected) - VALID_FINDING_STATUSES)
    invalid_counts = []
    for status, value in expected.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            invalid_counts.append(str(status))
            continue
        if count < 0:
            invalid_counts.append(str(status))
    if unsupported or invalid_counts:
        raise ValueError(
            f"Compliance review eval case {index} has invalid expected_finding_status_counts."
        )


def validate_eval_string_list(index: int, case: dict, key: str) -> None:
    values = case.get(key, [])
    if not isinstance(values, list) or any(not str(value).strip() for value in values):
        raise ValueError(f"Compliance review eval case {index} {key} must be a list of strings.")


def validate_optional_bool(index: int, case: dict, key: str) -> None:
    if key in case and not isinstance(case[key], bool):
        raise ValueError(f"Compliance review eval case {index} {key} must be a boolean.")


def validate_positive_eval_int(index: int, case: dict, key: str) -> None:
    if key not in case:
        return
    try:
        value = int(case[key])
    except (TypeError, ValueError) as error:
        raise ValueError(f"Compliance review eval case {index} {key} must be an integer.") from error
    if value < 1:
        raise ValueError(f"Compliance review eval case {index} {key} must be at least 1.")


def filter_values(value) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if str(value or "").strip():
        return [str(value)]
    return []


def string_map(value: dict) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items()}
