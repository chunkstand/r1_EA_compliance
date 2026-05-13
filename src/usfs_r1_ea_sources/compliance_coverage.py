from __future__ import annotations

from collections import Counter
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .compliance_review_eval import DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH
from .rule_claim_binding import default_rule_claim_links_path
from .rule_claim_binding import _load_validated_links_for_eval
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


COVERAGE_MATRIX_SCHEMA_VERSION = "compliance-rule-pack-coverage-v0"
COVERAGE_RESULT_SCHEMA_VERSION = "compliance-coverage-results-v0"
DEFAULT_COVERAGE_MATRIX_PATH = Path("config/compliance_rule_pack_coverage_nepa_ea_v0.json")
TEXT_TOKEN_RE = re.compile(r"[a-z0-9]+")
REQUIRED_COVERAGE_FIELDS = {
    "eval_case_ids",
    "expected_package_evidence",
    "obligation_area",
    "rule_id",
    "source_claim_terms",
    "source_record_ids",
}


@dataclass(frozen=True)
class ComplianceCoverageResult:
    output_path: Path
    summary: dict


def run_compliance_coverage(
    *,
    output_dir: Path,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    coverage_matrix_path: Path = DEFAULT_COVERAGE_MATRIX_PATH,
    eval_file: Path = DEFAULT_COMPLIANCE_REVIEW_EVAL_PATH,
    source_set_id: str | None = None,
    links_path: Path | None = None,
    results_dir: Path | None = None,
) -> ComplianceCoverageResult:
    """Validate rule-pack, source-claim, and final-review eval coverage."""

    output_dir = Path(output_dir)
    rule_pack_path = Path(rule_pack_path)
    coverage_matrix_path = Path(coverage_matrix_path)
    eval_file = Path(eval_file)
    rule_pack = load_rule_pack(rule_pack_path)
    rule_pack_validation = validate_rule_pack(rule_pack)
    matrix = _load_coverage_matrix(coverage_matrix_path)
    eval_cases = _load_eval_cases(eval_file)
    if links_path is None:
        links_path = default_rule_claim_links_path(
            output_dir,
            source_set_id=source_set_id,
            rule_pack_path=rule_pack_path,
        )
    links_path = Path(links_path)
    try:
        links = _load_validated_links_for_eval(links_path)
        link_error = None
    except (FileNotFoundError, ValueError) as error:
        links = []
        link_error = str(error)

    checks = [
        _check_rule_pack_valid(rule_pack_validation, rule_pack_path),
        _check_matrix_identity(matrix, rule_pack, coverage_matrix_path),
        _check_matrix_covers_rules(matrix, rule_pack),
        _check_matrix_required_fields(matrix),
        _check_eval_cases_cover_rules(eval_cases, rule_pack, eval_file),
        _check_matrix_eval_case_ids(matrix, eval_cases),
        _check_rule_claim_links_ready(links_path, links, link_error),
        _check_rules_have_source_claim_links(rule_pack, links),
        _check_matrix_source_records_match_links(matrix, links),
        _check_matrix_source_claim_terms_match_links(matrix, links),
    ]
    passed = all(check["passed"] for check in checks)
    output_path = (
        Path(results_dir) / "compliance_coverage_results.json"
        if results_dir
        else links_path.parent / "compliance_coverage_results.json"
    )
    summary = {
        "schema_version": COVERAGE_RESULT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "passed": passed,
        "reviewer_ready": passed,
        "output_path": str(output_path),
        "output_dir": str(output_dir),
        "source_set_id": _source_set_from_links(links) or source_set_id,
        "rule_pack_path": str(rule_pack_path),
        "rule_pack_id": rule_pack.get("rule_pack_id"),
        "rule_pack_version": rule_pack.get("version"),
        "coverage_matrix_path": str(coverage_matrix_path),
        "eval_file": str(eval_file),
        "links_path": str(links_path),
        "rule_count": len(rule_pack.get("rules", [])),
        "coverage_item_count": len(matrix.get("coverage_items", []))
        if isinstance(matrix.get("coverage_items"), list)
        else 0,
        "eval_case_count": len(eval_cases),
        "rule_claim_link_count": len(links),
        "rules_without_coverage_items": _rules_without_coverage_items(rule_pack, matrix),
        "rules_without_eval_cases": _rules_without_eval_cases(rule_pack, eval_cases),
        "rules_without_source_claim_links": _rules_without_source_claim_links(rule_pack, links),
        "source_record_mismatch_rule_ids": _source_record_mismatch_rule_ids(matrix, links),
        "source_claim_term_mismatch_rule_ids": _source_claim_term_mismatch_rule_ids(
            matrix,
            links,
        ),
        "links_per_rule": _links_per_rule(rule_pack, links),
        "checks": checks,
    }
    _write_json(output_path, summary)
    return ComplianceCoverageResult(output_path=output_path, summary=summary)


def _load_coverage_matrix(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing compliance coverage matrix: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Compliance coverage matrix must be a JSON object.")
    return value


def _load_eval_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing compliance review eval file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, dict):
        value = value.get("cases")
    if not isinstance(value, list) or not value:
        raise ValueError(
            "Compliance review eval file must contain a non-empty JSON list or contract cases array."
        )
    for index, case in enumerate(value):
        if not isinstance(case, dict):
            raise ValueError(f"Compliance review eval case {index} must be an object.")
    return value


def _check_rule_pack_valid(rule_pack_validation: dict, rule_pack_path: Path) -> dict:
    return {
        "name": "rule_pack_valid",
        "passed": bool(rule_pack_validation.get("passed")),
        "details": {
            "path": str(rule_pack_path),
            "failed_checks": _failed_check_names(rule_pack_validation),
        },
    }


def _check_matrix_identity(matrix: dict, rule_pack: dict, coverage_matrix_path: Path) -> dict:
    failures = []
    if matrix.get("schema_version") != COVERAGE_MATRIX_SCHEMA_VERSION:
        failures.append(
            {
                "field": "schema_version",
                "expected": COVERAGE_MATRIX_SCHEMA_VERSION,
                "actual": matrix.get("schema_version"),
            }
        )
    for matrix_field, rule_field in (
        ("rule_pack_id", "rule_pack_id"),
        ("rule_pack_version", "version"),
    ):
        if matrix.get(matrix_field) != rule_pack.get(rule_field):
            failures.append(
                {
                    "field": matrix_field,
                    "expected": rule_pack.get(rule_field),
                    "actual": matrix.get(matrix_field),
                }
            )
    return {
        "name": "coverage_matrix_matches_rule_pack_identity",
        "passed": not failures,
        "details": {"path": str(coverage_matrix_path), "failures": failures},
    }


def _check_matrix_covers_rules(matrix: dict, rule_pack: dict) -> dict:
    expected = _rule_ids(rule_pack)
    items = _coverage_items(matrix)
    actual = [str(item.get("rule_id") or "") for item in items]
    actual_set = {rule_id for rule_id in actual if rule_id}
    duplicates = sorted(rule_id for rule_id, count in Counter(actual).items() if rule_id and count > 1)
    missing = sorted(expected - actual_set)
    unexpected = sorted(actual_set - expected)
    return {
        "name": "coverage_matrix_covers_every_rule",
        "passed": not missing and not unexpected and not duplicates and len(items) == len(expected),
        "details": {
            "missing_rule_ids": missing,
            "unexpected_rule_ids": unexpected,
            "duplicate_rule_ids": duplicates,
        },
    }


def _check_matrix_required_fields(matrix: dict) -> dict:
    failures = []
    raw_items = matrix.get("coverage_items")
    if not isinstance(raw_items, list):
        failures.append(
            {
                "index": None,
                "rule_id": None,
                "reason": "coverage_items_must_be_list",
            }
        )
        raw_items = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            failures.append(
                {
                    "index": index,
                    "rule_id": None,
                    "reason": "coverage_item_must_be_object",
                }
            )
            continue
        missing = []
        for field in REQUIRED_COVERAGE_FIELDS:
            value = item.get(field)
            if value in (None, "") or (isinstance(value, list) and not value):
                missing.append(field)
        if missing:
            failures.append(
                {
                    "index": index,
                    "rule_id": item.get("rule_id"),
                    "reason": "missing_required_fields",
                    "missing_fields": sorted(missing),
                }
            )
            continue
        invalid_list_fields = []
        duplicate_list_values = {}
        for field in ("eval_case_ids", "source_claim_terms", "source_record_ids"):
            value = item.get(field)
            if not isinstance(value, list) or not all(_is_non_empty_string(entry) for entry in value):
                invalid_list_fields.append(field)
                continue
            counts = Counter(str(entry).strip() for entry in value)
            duplicates = sorted(entry for entry, count in counts.items() if count > 1)
            if duplicates:
                duplicate_list_values[field] = duplicates
        invalid_text_fields = []
        for field in ("expected_package_evidence", "obligation_area", "rule_id"):
            if not _is_non_empty_string(item.get(field)):
                invalid_text_fields.append(field)
        if invalid_list_fields or invalid_text_fields or duplicate_list_values:
            failures.append(
                {
                    "index": index,
                    "rule_id": item.get("rule_id"),
                    "reason": "invalid_field_shape",
                    "invalid_list_fields": sorted(invalid_list_fields),
                    "invalid_text_fields": sorted(invalid_text_fields),
                    "duplicate_list_values": duplicate_list_values,
                }
            )
    return {
        "name": "coverage_matrix_items_have_required_fields",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_eval_cases_cover_rules(eval_cases: list[dict], rule_pack: dict, eval_file: Path) -> dict:
    expected = _rule_ids(rule_pack)
    failures = []
    for case in eval_cases:
        case_id = str(case.get("id") or "")
        statuses = case.get("expected_statuses")
        if not isinstance(statuses, dict):
            failures.append({"case_id": case_id, "reason": "missing_expected_statuses"})
            continue
        actual = {str(rule_id) for rule_id in statuses}
        if actual != expected:
            failures.append(
                {
                    "case_id": case_id,
                    "missing_rule_ids": sorted(expected - actual),
                    "unexpected_rule_ids": sorted(actual - expected),
                }
            )
    return {
        "name": "compliance_eval_cases_cover_every_rule",
        "passed": not failures,
        "details": {"eval_file": str(eval_file), "failures": failures},
    }


def _check_matrix_eval_case_ids(matrix: dict, eval_cases: list[dict]) -> dict:
    case_ids = {str(case.get("id") or "") for case in eval_cases}
    failures = []
    for item in _coverage_items(matrix):
        ids = _string_list(item.get("eval_case_ids"))
        missing = sorted(set(ids) - case_ids)
        if missing:
            failures.append({"rule_id": item.get("rule_id"), "missing_eval_case_ids": missing})
    return {
        "name": "coverage_matrix_eval_cases_exist",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_rule_claim_links_ready(links_path: Path, links: list[dict], link_error: str | None) -> dict:
    return {
        "name": "rule_claim_links_reviewer_ready",
        "passed": link_error is None and bool(links),
        "details": {
            "links_path": str(links_path),
            "link_count": len(links),
            "error": link_error,
        },
    }


def _check_rules_have_source_claim_links(rule_pack: dict, links: list[dict]) -> dict:
    missing = _rules_without_source_claim_links(rule_pack, links)
    return {
        "name": "every_rule_has_source_claim_links",
        "passed": not missing,
        "details": {"rule_ids": missing, "links_per_rule": _links_per_rule(rule_pack, links)},
    }


def _check_matrix_source_records_match_links(matrix: dict, links: list[dict]) -> dict:
    links_by_rule = _links_by_rule(links)
    failures = []
    for item in _coverage_items(matrix):
        expected_sources = set(_string_list(item.get("source_record_ids")))
        if not expected_sources:
            continue
        actual_sources = {
            str(link.get("source_record_id"))
            for link in links_by_rule.get(str(item.get("rule_id") or ""), [])
        }
        if not actual_sources.intersection(expected_sources):
            failures.append(
                {
                    "rule_id": item.get("rule_id"),
                    "expected_source_record_ids": sorted(expected_sources),
                    "actual_source_record_ids": sorted(actual_sources),
                }
            )
    return {
        "name": "coverage_matrix_source_records_match_rule_claim_links",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_matrix_source_claim_terms_match_links(matrix: dict, links: list[dict]) -> dict:
    links_by_rule = _links_by_rule(links)
    failures = []
    for item in _coverage_items(matrix):
        rule_id = str(item.get("rule_id") or "")
        expected_terms = _string_list(item.get("source_claim_terms"))
        if not rule_id or not expected_terms:
            continue
        rule_links = links_by_rule.get(rule_id, [])
        missing_terms = [
            term
            for term in expected_terms
            if not any(_link_supports_term(link, term) for link in rule_links)
        ]
        if missing_terms:
            failures.append(
                {
                    "rule_id": rule_id,
                    "missing_source_claim_terms": missing_terms,
                    "link_count": len(rule_links),
                    "link_ids": [str(link.get("link_id")) for link in rule_links[:5]],
                }
            )
    return {
        "name": "coverage_matrix_source_claim_terms_match_rule_claim_links",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _rule_ids(rule_pack: dict) -> set[str]:
    return {str(rule["id"]) for rule in rule_pack.get("rules", [])}


def _coverage_items(matrix: dict) -> list[dict]:
    items = matrix.get("coverage_items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _links_by_rule(links: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for link in links:
        grouped[str(link.get("rule_id") or "")].append(link)
    return grouped


def _rules_without_coverage_items(rule_pack: dict, matrix: dict) -> list[str]:
    expected = _rule_ids(rule_pack)
    covered = {str(item.get("rule_id") or "") for item in _coverage_items(matrix)}
    return sorted(expected - covered)


def _rules_without_eval_cases(rule_pack: dict, eval_cases: list[dict]) -> list[str]:
    expected = _rule_ids(rule_pack)
    covered = set()
    for case in eval_cases:
        statuses = case.get("expected_statuses")
        if isinstance(statuses, dict):
            covered.update(str(rule_id) for rule_id in statuses)
    return sorted(expected - covered)


def _rules_without_source_claim_links(rule_pack: dict, links: list[dict]) -> list[str]:
    linked = {str(link.get("rule_id") or "") for link in links}
    return sorted(_rule_ids(rule_pack) - linked)


def _source_record_mismatch_rule_ids(matrix: dict, links: list[dict]) -> list[str]:
    check = _check_matrix_source_records_match_links(matrix, links)
    return [str(item["rule_id"]) for item in check["details"]["failures"]]


def _source_claim_term_mismatch_rule_ids(matrix: dict, links: list[dict]) -> list[str]:
    check = _check_matrix_source_claim_terms_match_links(matrix, links)
    return [str(item["rule_id"]) for item in check["details"]["failures"]]


def _links_per_rule(rule_pack: dict, links: list[dict]) -> dict[str, int]:
    counts = Counter(str(link.get("rule_id") or "") for link in links)
    return {rule_id: counts.get(rule_id, 0) for rule_id in sorted(_rule_ids(rule_pack))}


def _source_set_from_links(links: list[dict]) -> str | None:
    source_sets = sorted({str(link.get("source_set_id")) for link in links if link.get("source_set_id")})
    return source_sets[0] if len(source_sets) == 1 else None


def _failed_check_names(validation: dict) -> list[str]:
    return [
        str(check.get("name"))
        for check in validation.get("checks", [])
        if not check.get("passed")
    ]


def _is_non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if _is_non_empty_string(item)]


def _link_supports_term(link: dict, term: str) -> bool:
    term_text = _normalize_text(term)
    if not term_text:
        return False
    link_text = _normalize_text(
        " ".join(
            str(value)
            for value in (
                link.get("claim_text"),
                link.get("title"),
                link.get("citation_label"),
                " ".join(str(value) for value in link.get("matched_terms", [])),
                " ".join(str(value) for value in link.get("review_topics", [])),
            )
            if str(value or "").strip()
        )
    )
    if " " in term_text:
        return term_text in link_text
    return term_text in set(link_text.split())


def _normalize_text(value: str) -> str:
    return " ".join(TEXT_TOKEN_RE.findall(str(value).lower()))


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
