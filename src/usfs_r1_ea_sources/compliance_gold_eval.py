from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
import re

from .compliance_review_eval import run_compliance_review_eval
from .compliance_validation import VALID_FINDING_STATUSES
from .forest_plan_profiles import DEFAULT_FOREST_PLAN_PROFILES_PATH
from .forest_plan_resolver import DEFAULT_FOREST_PLAN_PROFILE_ID
from .rule_packs import DEFAULT_RULE_PACK_PATH
from .rule_packs import GENERATED_RULE_PACK_SCHEMA_VERSION
from .rule_packs import load_rule_pack
from .rule_packs import validate_rule_pack


COMPLIANCE_GOLD_EVAL_SCHEMA_VERSION = "compliance-gold-eval-v0"
COMPLIANCE_GOLD_EVAL_RESULT_SCHEMA_VERSION = "compliance-gold-eval-results-v0"
DEFAULT_COMPLIANCE_GOLD_EVAL_PATH = Path("config/compliance_gold_eval_v0.json")
REQUIRED_CASE_PROFILES = {"mixed", "negative", "positive"}
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_.-]+$")


@dataclass(frozen=True)
class ComplianceGoldEvalResult:
    gold_file: Path
    output_dir: Path
    output_path: Path
    summary: dict


def run_compliance_gold_eval(
    *,
    output_dir: Path,
    gold_file: Path = DEFAULT_COMPLIANCE_GOLD_EVAL_PATH,
    rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    source_set_id: str | None = None,
    index_path: Path | None = None,
    forest_unit_id: str = DEFAULT_FOREST_PLAN_PROFILE_ID,
    forest_plan_profiles_path: Path = DEFAULT_FOREST_PLAN_PROFILES_PATH,
    results_dir: Path | None = None,
    source_top_k: int = 3,
    package_top_k: int = 3,
    chunk_max_chars: int = 1800,
    chunk_overlap_chars: int = 200,
    docling_ocr: bool = False,
    docling_timeout_seconds: float | None = 120.0,
) -> ComplianceGoldEvalResult:
    """Run the adjudicated gold eval gate through the real compliance-review path."""

    output_dir = Path(output_dir)
    gold_file = Path(gold_file)
    rule_pack_path = Path(rule_pack_path)
    gold = _load_gold_eval(gold_file)
    rule_pack = load_rule_pack(rule_pack_path)
    rule_pack_validation = validate_rule_pack(rule_pack)
    cases = _case_list(gold)
    eval_output_dir = Path(results_dir) if results_dir else output_dir / "reviews" / "compliance_gold_eval"
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    output_path = eval_output_dir / "compliance_gold_eval_results.json"
    compliance_review_eval_dir = eval_output_dir / "compliance_review_eval"
    compliance_review_eval_file = eval_output_dir / "adjudicated_cases.compliance_review_eval.json"

    checks = [
        _check_rule_pack_valid(rule_pack_validation, rule_pack_path),
        _check_gold_identity(gold, gold_file),
        _check_gold_rule_pack_identity(gold, rule_pack),
        _check_cases_present(gold, gold_file, cases),
        _check_case_adjudication(cases),
        _check_case_rule_coverage(cases, rule_pack),
        _check_case_profiles(cases),
        _check_case_status_counts(cases, rule_pack),
    ]
    adjudication_passed = all(check["passed"] for check in checks)
    review_eval_summary = None
    review_eval_error = None
    if adjudication_passed:
        review_eval_cases = _review_eval_cases(cases, gold_file)
        compliance_review_eval_file.write_text(
            json.dumps(review_eval_cases, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        try:
            review_eval = run_compliance_review_eval(
                output_dir=output_dir,
                eval_file=compliance_review_eval_file,
                rule_pack_path=rule_pack_path,
                source_set_id=source_set_id,
                index_path=index_path,
                forest_unit_id=forest_unit_id,
                forest_plan_profiles_path=forest_plan_profiles_path,
                results_dir=compliance_review_eval_dir,
                source_top_k=source_top_k,
                package_top_k=package_top_k,
                chunk_max_chars=chunk_max_chars,
                chunk_overlap_chars=chunk_overlap_chars,
                docling_ocr=docling_ocr,
                docling_timeout_seconds=docling_timeout_seconds,
            )
            review_eval_summary = review_eval.summary
        except (FileNotFoundError, ValueError) as error:
            review_eval_error = str(error)

    case_results = list((review_eval_summary or {}).get("cases", []))
    case_count = len(cases)
    passed_case_count = int((review_eval_summary or {}).get("passed_count") or 0)
    source_set_ids = list((review_eval_summary or {}).get("source_set_ids") or [])
    profile_counts = _profile_counts(cases)
    compliance_review_eval_passed = bool(
        review_eval_summary and review_eval_summary.get("passed")
    )
    reviewer_ready_rule_pack = (
        rule_pack.get("schema_version") == GENERATED_RULE_PACK_SCHEMA_VERSION
    )
    summary = {
        "schema_version": COMPLIANCE_GOLD_EVAL_RESULT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "gold_file": str(gold_file),
        "output_dir": str(eval_output_dir),
        "output_path": str(output_path),
        "compliance_review_eval_file": str(compliance_review_eval_file),
        "compliance_review_eval_path": str(
            compliance_review_eval_dir / "compliance_review_eval_results.json"
        ),
        "rule_pack_path": str(rule_pack_path),
        "gold_eval_id": gold.get("id"),
        "gold_eval_version": gold.get("version"),
        "rule_pack_id": rule_pack.get("rule_pack_id"),
        "rule_pack_version": rule_pack.get("version"),
        "source_set_id": source_set_id or (source_set_ids[0] if len(source_set_ids) == 1 else None),
        "source_set_ids": source_set_ids,
        "source_top_k": source_top_k,
        "package_top_k": package_top_k,
        "case_count": case_count,
        "adjudicated_case_count": _adjudicated_case_count(cases),
        "passed_case_count": passed_case_count,
        "failed_case_count": case_count - passed_case_count,
        "profile_counts": profile_counts,
        "required_profiles": sorted(REQUIRED_CASE_PROFILES),
        "required_profiles_present": sorted(
            REQUIRED_CASE_PROFILES.intersection(profile_counts)
        ),
        "adjudication_checks_passed": adjudication_passed,
        "compliance_review_eval_passed": compliance_review_eval_passed,
        "compliance_review_eval_error": review_eval_error,
        "reviewer_ready_rule_pack": reviewer_ready_rule_pack,
        "promotion_ready": reviewer_ready_rule_pack
        and adjudication_passed
        and compliance_review_eval_passed,
        "passed": adjudication_passed and compliance_review_eval_passed,
        "checks": checks,
        "metrics": (review_eval_summary or {}).get("metrics", {}),
        "failure_category_counts": (review_eval_summary or {}).get(
            "failure_category_counts",
            {},
        ),
        "cases": [_gold_case_result(case, case_results) for case in cases],
    }
    _write_json(output_path, summary)
    return ComplianceGoldEvalResult(
        gold_file=gold_file,
        output_dir=eval_output_dir,
        output_path=output_path,
        summary=summary,
    )


def _load_gold_eval(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing compliance gold eval file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Compliance gold eval file must be a JSON object.")
    return value


def _case_list(gold: dict) -> list[dict]:
    cases = gold.get("cases")
    return cases if isinstance(cases, list) else []


def _review_eval_cases(cases: list[dict], gold_file: Path) -> list[dict]:
    eval_cases = deepcopy(cases)
    for case in eval_cases:
        package_path = str(case.get("package_path") or "").strip()
        if package_path:
            case["package_path"] = str((gold_file.parent / package_path).resolve())
    return eval_cases


def _check_rule_pack_valid(rule_pack_validation: dict, rule_pack_path: Path) -> dict:
    return {
        "name": "rule_pack_valid",
        "passed": bool(rule_pack_validation.get("passed")),
        "details": {
            "path": str(rule_pack_path),
            "failed_checks": [
                str(check.get("name"))
                for check in rule_pack_validation.get("checks", [])
                if not check.get("passed")
            ],
        },
    }


def _check_gold_identity(gold: dict, gold_file: Path) -> dict:
    failures = []
    if gold.get("schema_version") != COMPLIANCE_GOLD_EVAL_SCHEMA_VERSION:
        failures.append(
            {
                "field": "schema_version",
                "expected": COMPLIANCE_GOLD_EVAL_SCHEMA_VERSION,
                "actual": gold.get("schema_version"),
            }
        )
    for field in ("id", "version", "title"):
        value = str(gold.get(field) or "").strip()
        if not value:
            failures.append({"field": field, "reason": "missing"})
        elif field in {"id", "version"} and not SAFE_ID_RE.fullmatch(value):
            failures.append({"field": field, "reason": "unsafe_id", "actual": value})
    adjudication = gold.get("adjudication")
    if not isinstance(adjudication, dict):
        failures.append({"field": "adjudication", "reason": "missing_or_invalid"})
    else:
        missing = [
            field
            for field in ("adjudicated_at", "method", "status")
            if not str(adjudication.get(field) or "").strip()
        ]
        if not _string_list(adjudication.get("adjudicated_by")):
            missing.append("adjudicated_by")
        if adjudication.get("promotion_gate") is not True:
            missing.append("promotion_gate")
        if missing:
            failures.append(
                {
                    "field": "adjudication",
                    "reason": "missing_adjudication_fields",
                    "fields": sorted(missing),
                }
            )
    return {
        "name": "gold_eval_identity_valid",
        "passed": not failures,
        "details": {"path": str(gold_file), "failures": failures},
    }


def _check_gold_rule_pack_identity(gold: dict, rule_pack: dict) -> dict:
    failures = []
    for gold_field, rule_field in (
        ("rule_pack_id", "rule_pack_id"),
        ("rule_pack_version", "version"),
    ):
        if gold.get(gold_field) != rule_pack.get(rule_field):
            failures.append(
                {
                    "field": gold_field,
                    "expected": rule_pack.get(rule_field),
                    "actual": gold.get(gold_field),
                }
            )
    return {
        "name": "gold_eval_rule_pack_matches",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_cases_present(gold: dict, gold_file: Path, cases: list[dict]) -> dict:
    failures = []
    gold_root = gold_file.parent.resolve()
    raw_cases = gold.get("cases")
    if "cases" not in gold:
        failures.append({"reason": "missing_cases"})
    elif not isinstance(raw_cases, list):
        failures.append(
            {
                "reason": "cases_must_be_list",
                "actual_type": type(raw_cases).__name__,
            }
        )
    if len(cases) < 3:
        failures.append({"reason": "minimum_three_cases_required", "case_count": len(cases)})
    case_ids = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            failures.append({"index": index, "reason": "case_must_be_object"})
            continue
        case_id = str(case.get("id") or "").strip()
        if not case_id:
            failures.append({"index": index, "reason": "missing_id"})
        elif not SAFE_ID_RE.fullmatch(case_id):
            failures.append({"index": index, "case_id": case_id, "reason": "unsafe_id"})
        else:
            case_ids.append(case_id)
        has_text = bool(str(case.get("package_text") or "").strip())
        has_path = bool(str(case.get("package_path") or "").strip())
        if has_text == has_path:
            failures.append(
                {
                    "index": index,
                    "case_id": case_id,
                    "reason": "exactly_one_package_fixture_required",
                }
            )
        if has_path:
            package_path = Path(str(case.get("package_path") or "").strip())
            if package_path.is_absolute() or ".." in package_path.parts:
                failures.append(
                    {
                        "index": index,
                        "case_id": case_id,
                        "reason": "package_path_must_be_relative_child",
                        "package_path": str(package_path),
                    }
                )
            else:
                resolved_package_path = (gold_root / package_path).resolve()
                try:
                    resolved_package_path.relative_to(gold_root)
                except ValueError:
                    failures.append(
                        {
                            "index": index,
                            "case_id": case_id,
                            "reason": "package_path_must_resolve_under_gold_file",
                            "package_path": str(package_path),
                            "resolved_package_path": str(resolved_package_path),
                        }
                    )
    for case_id, count in sorted(Counter(case_ids).items()):
        if count > 1:
            failures.append(
                {
                    "case_id": case_id,
                    "count": count,
                    "reason": "duplicate_id",
                }
            )
    return {
        "name": "gold_eval_cases_present",
        "passed": not failures,
        "details": {"case_count": len(cases), "failures": failures},
    }


def _check_case_adjudication(cases: list[dict]) -> dict:
    failures = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("id") or "")
        adjudication = case.get("adjudication")
        if not isinstance(adjudication, dict):
            failures.append({"index": index, "case_id": case_id, "reason": "missing_adjudication"})
            continue
        missing = []
        for field in ("adjudicated_at", "rationale", "source_type", "status"):
            if not str(adjudication.get(field) or "").strip():
                missing.append(field)
        if not _string_list(adjudication.get("adjudicated_by")):
            missing.append("adjudicated_by")
        if missing:
            failures.append(
                {
                    "index": index,
                    "case_id": case_id,
                    "reason": "missing_adjudication_fields",
                    "fields": sorted(missing),
                }
            )
    return {
        "name": "gold_eval_cases_have_adjudication",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_case_rule_coverage(cases: list[dict], rule_pack: dict) -> dict:
    expected_rule_ids = _rule_ids(rule_pack)
    failures = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("id") or "")
        statuses = case.get("expected_statuses")
        if not isinstance(statuses, dict):
            failures.append({"index": index, "case_id": case_id, "reason": "missing_statuses"})
            continue
        actual = {str(rule_id) for rule_id in statuses}
        invalid_statuses = sorted(
            str(status)
            for status in statuses.values()
            if str(status) not in VALID_FINDING_STATUSES
        )
        missing = sorted(expected_rule_ids - actual)
        unexpected = sorted(actual - expected_rule_ids)
        if missing or unexpected or invalid_statuses:
            failures.append(
                {
                    "index": index,
                    "case_id": case_id,
                    "missing_rule_ids": missing,
                    "unexpected_rule_ids": unexpected,
                    "invalid_statuses": invalid_statuses,
                }
            )
    return {
        "name": "gold_eval_cases_cover_rule_pack",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _check_case_profiles(cases: list[dict]) -> dict:
    profile_counts = _profile_counts(cases)
    missing_profiles = sorted(REQUIRED_CASE_PROFILES - set(profile_counts))
    invalid_profiles = sorted(
        {
            str(case.get("profile") or "")
            for case in cases
            if isinstance(case, dict)
            and str(case.get("profile") or "") not in REQUIRED_CASE_PROFILES
        }
    )
    return {
        "name": "gold_eval_required_profiles_present",
        "passed": not missing_profiles and not invalid_profiles,
        "details": {
            "profile_counts": profile_counts,
            "missing_profiles": missing_profiles,
            "invalid_profiles": invalid_profiles,
        },
    }


def _check_case_status_counts(cases: list[dict], rule_pack: dict) -> dict:
    rule_count = len(_rule_ids(rule_pack))
    failures = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("id") or "")
        statuses = case.get("expected_statuses")
        expected_counts = case.get("expected_finding_status_counts") or {}
        if not isinstance(statuses, dict) or not isinstance(expected_counts, dict):
            failures.append({"index": index, "case_id": case_id, "reason": "invalid_counts"})
            continue
        try:
            normalized_counts = {
                str(status): int(count)
                for status, count in expected_counts.items()
                if int(count) != 0
            }
        except (TypeError, ValueError):
            failures.append({"index": index, "case_id": case_id, "reason": "invalid_counts"})
            continue
        actual_counts = dict(Counter(str(status) for status in statuses.values()))
        if sum(normalized_counts.values()) != rule_count or normalized_counts != actual_counts:
            failures.append(
                {
                    "index": index,
                    "case_id": case_id,
                    "reason": "counts_do_not_match_expected_statuses",
                    "expected": normalized_counts,
                    "actual": actual_counts,
                }
            )
    return {
        "name": "gold_eval_status_counts_match_expected_statuses",
        "passed": not failures,
        "details": {"failures": failures},
    }


def _gold_case_result(case: dict, case_results: list[dict]) -> dict:
    if not isinstance(case, dict):
        return {
            "id": None,
            "profile": None,
            "adjudication": {},
            "passed": False,
            "failure_reasons": ["case_must_be_object"],
            "expected_statuses": {},
            "actual_statuses": {},
            "finding_status_counts": {},
            "failure_taxonomy": [
                {
                    "category": "validation_gate_miss",
                    "rule_ids": [],
                    "checks": ["case_must_be_object"],
                    "evidence": ["case_must_be_object"],
                }
            ],
            "review_dir": None,
            "package_path": None,
            "compliance_matrix_path": None,
        }
    case_id = str(case.get("id") or "")
    result = next((item for item in case_results if item.get("id") == case_id), {})
    adjudication = case.get("adjudication")
    failure_reasons = result.get("failure_reasons")
    if not result:
        failure_reasons = ["compliance_review_eval_not_run"]
    return {
        "id": case_id,
        "profile": case.get("profile"),
        "adjudication": adjudication if isinstance(adjudication, dict) else {},
        "passed": bool(result.get("passed")),
        "failure_reasons": failure_reasons or [],
        "expected_statuses": case.get("expected_statuses", {}),
        "actual_statuses": result.get("actual_statuses", {}),
        "finding_status_counts": result.get("finding_status_counts", {}),
        "failure_taxonomy": result.get("failure_taxonomy", []),
        "failure_category_counts": result.get("failure_category_counts", {}),
        "source_record_mismatches": result.get("source_record_mismatches", []),
        "source_document_role_mismatches": result.get("source_document_role_mismatches", []),
        "review_dir": result.get("review_dir"),
        "package_path": result.get("package_path"),
        "compliance_matrix_path": result.get("compliance_matrix_path"),
    }


def _rule_ids(rule_pack: dict) -> set[str]:
    return {
        str(rule.get("id"))
        for rule in rule_pack.get("rules", [])
        if isinstance(rule, dict) and str(rule.get("id") or "").strip()
    }


def _profile_counts(cases: list[dict]) -> dict[str, int]:
    counts = Counter(
        str(case.get("profile") or "")
        for case in cases
        if isinstance(case, dict) and str(case.get("profile") or "") in REQUIRED_CASE_PROFILES
    )
    return {profile: counts[profile] for profile in sorted(counts)}


def _adjudicated_case_count(cases: list[dict]) -> int:
    return sum(1 for case in cases if _case_adjudication_complete(case))


def _case_adjudication_complete(case: object) -> bool:
    if not isinstance(case, dict):
        return False
    adjudication = case.get("adjudication")
    if not isinstance(adjudication, dict):
        return False
    required = ("adjudicated_at", "rationale", "source_type", "status")
    return all(str(adjudication.get(field) or "").strip() for field in required) and bool(
        _string_list(adjudication.get("adjudicated_by"))
    )


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
