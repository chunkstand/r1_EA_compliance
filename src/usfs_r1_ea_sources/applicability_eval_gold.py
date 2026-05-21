from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .applicability_eval_runtime import run_applicability_eval
from .applicability_eval_summary import _gold_source_chunk_count
from .applicability_eval_support import APPLICABILITY_EVAL_SCHEMA_VERSION
from .applicability_eval_support import APPLICABILITY_GOLD_EVAL_RESULT_SCHEMA_VERSION
from .applicability_eval_support import APPLICABILITY_GOLD_EVAL_SCHEMA_VERSION
from .applicability_eval_support import ApplicabilityGoldEvalResult
from .applicability_eval_support import DEFAULT_APPLICABILITY_GOLD_EVAL_PATH
from .applicability_eval_support import _case_list
from .applicability_eval_support import _load_eval_payload
from .applicability_eval_support import _strings
from .applicability_eval_support import _utc_now
from .applicability_eval_support import _validate_safe_segment
from .applicability_eval_support import _write_json
from .applicability_eval_support import REQUIRED_GOLD_PROFILES
from .applicability import DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH
from .rule_packs import DEFAULT_RULE_PACK_PATH


def run_applicability_gold_eval(
    *,
    output_dir: Path,
    gold_file: Path = DEFAULT_APPLICABILITY_GOLD_EVAL_PATH,
    base_rule_pack_path: Path = DEFAULT_RULE_PACK_PATH,
    authority_family_templates_path: Path | None = DEFAULT_AUTHORITY_FAMILY_TEMPLATES_PATH,
    source_set_id: str | None = None,
    results_dir: Path | None = None,
    top_k: int = 5,
) -> ApplicabilityGoldEvalResult:
    """Run adjudicated applicability gold eval cases through applicability-eval."""

    output_dir = Path(output_dir)
    gold_file = Path(gold_file)
    base_rule_pack_path = Path(base_rule_pack_path)
    authority_family_templates_path = (
        Path(authority_family_templates_path) if authority_family_templates_path else None
    )
    gold = _load_eval_payload(gold_file, APPLICABILITY_GOLD_EVAL_SCHEMA_VERSION)
    eval_output_dir = (
        Path(results_dir) if results_dir else output_dir / "reviews" / "applicability_gold_eval"
    )
    eval_output_dir.mkdir(parents=True, exist_ok=True)
    eval_payload = {
        "schema_version": APPLICABILITY_EVAL_SCHEMA_VERSION,
        "id": gold.get("id"),
        "version": gold.get("version"),
        "source_set_id": gold.get("source_set_id"),
        "source_chunks": gold.get("source_chunks") or [],
        "cases": gold.get("cases") or [],
    }
    eval_file = eval_output_dir / "adjudicated_cases.applicability_eval.json"
    _write_json(eval_file, eval_payload)
    checks = [
        _check_gold_identity(gold),
        _check_gold_cases(gold),
        _check_gold_profiles(gold),
        _check_gold_adjudication(gold),
        _check_gold_arbitration_expectations(gold),
    ]
    adjudication_passed = all(check["passed"] for check in checks)
    eval_summary = None
    eval_error = None
    if adjudication_passed:
        try:
            eval_result = run_applicability_eval(
                output_dir=output_dir,
                eval_file=eval_file,
                base_rule_pack_path=base_rule_pack_path,
                authority_family_templates_path=authority_family_templates_path,
                source_set_id=source_set_id,
                results_dir=eval_output_dir / "applicability_eval",
                top_k=top_k,
            )
            eval_summary = eval_result.summary
        except (FileNotFoundError, ValueError) as error:
            eval_error = str(error)

    cases = _case_list(gold)
    profile_counts = dict(Counter(str(case.get("profile") or "") for case in cases))
    eval_passed = bool(eval_summary and eval_summary.get("passed"))
    source_chunk_count = _gold_source_chunk_count(gold)
    family_group_coverage = _authority_family_group_coverage(
        gold=gold,
        family_coverage=(eval_summary or {}).get("authority_family_template_coverage", {}),
    )
    checks.extend(
        [
            _check_gold_source_chunk_coverage(gold, source_chunk_count),
            _check_gold_family_group_mapping(gold, family_group_coverage),
            _check_gold_family_group_coverage(gold, family_group_coverage),
        ]
    )
    nested_checks_passed = all(check["passed"] for check in checks)
    summary = {
        "schema_version": APPLICABILITY_GOLD_EVAL_RESULT_SCHEMA_VERSION,
        "created_at": _utc_now(),
        "gold_file": str(gold_file),
        "gold_eval_id": gold.get("id"),
        "gold_eval_version": gold.get("version"),
        "output_dir": str(eval_output_dir),
        "output_path": str(eval_output_dir / "applicability_gold_eval_results.json"),
        "applicability_eval_file": str(eval_file),
        "applicability_eval_path": str(
            eval_output_dir / "applicability_eval" / "applicability_eval_results.json"
        ),
        "base_rule_pack_path": str(base_rule_pack_path),
        "authority_family_templates_path": (
            str(authority_family_templates_path)
            if authority_family_templates_path
            else None
        ),
        "source_set_id": source_set_id or (eval_summary or {}).get("source_set_id"),
        "source_set_ids": (eval_summary or {}).get("source_set_ids", []),
        "case_count": len(cases),
        "source_chunk_count": source_chunk_count,
        "adjudicated_case_count": sum(
            1 for case in cases if isinstance(case.get("adjudication"), dict)
        ),
        "passed_case_count": int((eval_summary or {}).get("passed_count") or 0),
        "failed_case_count": len(cases)
        - int((eval_summary or {}).get("passed_count") or 0),
        "profile_counts": profile_counts,
        "required_profiles": sorted(REQUIRED_GOLD_PROFILES),
        "required_profiles_present": sorted(
            REQUIRED_GOLD_PROFILES.intersection(profile_counts)
        ),
        "adjudication_checks_passed": adjudication_passed,
        "applicability_eval_passed": eval_passed,
        "applicability_eval_error": eval_error,
        "promotion_ready": nested_checks_passed and eval_passed,
        "passed": nested_checks_passed and eval_passed,
        "checks": checks,
        "metrics": (eval_summary or {}).get("metrics", {}),
        "arbitration_summary": (eval_summary or {}).get("arbitration_summary", {}),
        "authority_family_template_coverage": (eval_summary or {}).get(
            "authority_family_template_coverage",
            {},
        ),
        "family_group_coverage": family_group_coverage,
        "failure_category_counts": (eval_summary or {}).get(
            "failure_category_counts",
            {},
        ),
        "cases": (eval_summary or {}).get("cases", []),
    }
    _write_json(Path(summary["output_path"]), summary)
    return ApplicabilityGoldEvalResult(
        gold_file=gold_file,
        output_dir=eval_output_dir,
        output_path=Path(summary["output_path"]),
        summary=summary,
    )


def _authority_family_group_coverage(
    *,
    gold: dict[str, Any],
    family_coverage: dict[str, Any],
) -> dict[str, Any]:
    required_groups = _strings(gold.get("required_real_package_coverage_tags"))
    required_family_ids = _strings(gold.get("high_priority_authority_family_ids"))
    raw_mapping = (
        gold.get("required_high_priority_family_group_by_id")
        if isinstance(gold.get("required_high_priority_family_group_by_id"), dict)
        else {}
    )
    mapping = {
        str(family_id): str(group_id)
        for family_id, group_id in raw_mapping.items()
        if str(family_id).strip() and str(group_id).strip()
    }
    unmapped_family_ids = sorted(
        family_id
        for family_id in required_family_ids
        if mapping.get(family_id) not in required_groups
    )
    positive_families = set(_strings(family_coverage.get("positive_covered_family_ids")))
    negative_families = set(_strings(family_coverage.get("negative_covered_family_ids")))
    unresolved_families = set(_strings(family_coverage.get("unresolved_covered_family_ids")))
    adjudicated_families = set(
        _strings(family_coverage.get("adjudicated_covered_family_ids"))
    )
    group_details: dict[str, Any] = {}
    for group_id in required_groups:
        group_family_ids = sorted(
            family_id
            for family_id in required_family_ids
            if mapping.get(family_id) == group_id
        )
        group_details[group_id] = {
            "family_ids": group_family_ids,
            "positive_family_ids": sorted(positive_families.intersection(group_family_ids)),
            "negative_family_ids": sorted(negative_families.intersection(group_family_ids)),
            "unresolved_family_ids": sorted(
                unresolved_families.intersection(group_family_ids)
            ),
            "adjudicated_family_ids": sorted(
                adjudicated_families.intersection(group_family_ids)
            ),
        }
    positive_groups = sorted(
        group_id for group_id, detail in group_details.items() if detail["positive_family_ids"]
    )
    negative_groups = sorted(
        group_id for group_id, detail in group_details.items() if detail["negative_family_ids"]
    )
    unresolved_groups = sorted(
        group_id for group_id, detail in group_details.items() if detail["unresolved_family_ids"]
    )
    adjudicated_groups = sorted(
        group_id for group_id, detail in group_details.items() if detail["adjudicated_family_ids"]
    )
    return {
        "schema_version": "authority-family-group-coverage-v1",
        "configured": bool(mapping),
        "required_group_ids": required_groups,
        "required_group_count": len(required_groups),
        "required_high_priority_family_ids": required_family_ids,
        "required_high_priority_family_id_count": len(required_family_ids),
        "family_group_by_high_priority_family_id": {
            family_id: mapping.get(family_id)
            for family_id in required_family_ids
            if mapping.get(family_id)
        },
        "unmapped_high_priority_family_ids": unmapped_family_ids,
        "unmapped_high_priority_family_count": len(unmapped_family_ids),
        "positive_covered_group_ids": positive_groups,
        "positive_covered_family_group_count": len(positive_groups),
        "negative_covered_group_ids": negative_groups,
        "negative_covered_family_group_count": len(negative_groups),
        "unresolved_covered_group_ids": unresolved_groups,
        "unresolved_covered_family_group_count": len(unresolved_groups),
        "adjudicated_covered_group_ids": adjudicated_groups,
        "adjudicated_covered_family_group_count": len(adjudicated_groups),
        "group_details": group_details,
        "passed": not unmapped_family_ids,
    }


def _gold_thresholds(gold: dict[str, Any]) -> dict[str, int]:
    value = gold.get("coverage_thresholds")
    if not isinstance(value, dict):
        return {}
    thresholds: dict[str, int] = {}
    for key, raw in value.items():
        try:
            thresholds[str(key)] = int(raw)
        except (TypeError, ValueError):
            continue
    return thresholds


def _gold_family_group_contract_configured(gold: dict[str, Any]) -> bool:
    raw_mapping = gold.get("required_high_priority_family_group_by_id")
    if isinstance(raw_mapping, dict) and any(
        str(family_id).strip() and str(group_id).strip()
        for family_id, group_id in raw_mapping.items()
    ):
        return True
    thresholds = _gold_thresholds(gold)
    return any(
        key in thresholds
        for key in (
            "required_high_priority_family_id_count",
            "positive_covered_family_group_count",
            "negative_covered_family_group_count",
            "adjudicated_covered_family_group_count",
            "unresolved_covered_family_group_count_min",
            "required_theme_count",
        )
    )


def _check_gold_source_chunk_coverage(
    gold: dict[str, Any],
    source_chunk_count: int,
) -> dict[str, Any]:
    thresholds = _gold_thresholds(gold)
    minimum = thresholds.get("source_chunk_count_min")
    if minimum is None:
        return _check(
            "gold_eval_source_chunk_count",
            True,
            {"source_chunk_count": source_chunk_count, "required_minimum": None},
        )
    return _check(
        "gold_eval_source_chunk_count",
        source_chunk_count >= minimum,
        {"source_chunk_count": source_chunk_count, "required_minimum": minimum},
    )


def _check_gold_family_group_mapping(
    gold: dict[str, Any],
    family_group_coverage: dict[str, Any],
) -> dict[str, Any]:
    if not _gold_family_group_contract_configured(gold):
        return _check(
            "gold_eval_high_priority_family_mapping",
            True,
            {
                "required_high_priority_family_id_count": family_group_coverage.get(
                    "required_high_priority_family_id_count"
                ),
                "unmapped_high_priority_family_ids": [],
                "skipped": True,
            },
        )
    passed = int(family_group_coverage.get("unmapped_high_priority_family_count") or 0) == 0
    return _check(
        "gold_eval_high_priority_family_mapping",
        passed,
        {
            "required_high_priority_family_id_count": family_group_coverage.get(
                "required_high_priority_family_id_count"
            ),
            "unmapped_high_priority_family_ids": family_group_coverage.get(
                "unmapped_high_priority_family_ids",
                [],
            ),
        },
    )


def _check_gold_family_group_coverage(
    gold: dict[str, Any],
    family_group_coverage: dict[str, Any],
) -> dict[str, Any]:
    if not _gold_family_group_contract_configured(gold):
        return _check(
            "gold_eval_family_group_coverage",
            True,
            {
                "required_group_ids": family_group_coverage.get("required_group_ids", []),
                "positive_covered_group_ids": [],
                "negative_covered_group_ids": [],
                "unresolved_covered_group_ids": [],
                "adjudicated_covered_group_ids": [],
                "failures": [],
                "skipped": True,
            },
        )
    thresholds = _gold_thresholds(gold)
    failures = []
    for key, actual_key in (
        ("case_count_min", "case_count"),
        ("required_high_priority_family_id_count", "required_high_priority_family_id_count"),
        ("positive_covered_family_group_count", "positive_covered_family_group_count"),
        ("negative_covered_family_group_count", "negative_covered_family_group_count"),
        ("adjudicated_covered_family_group_count", "adjudicated_covered_family_group_count"),
    ):
        expected = thresholds.get(key)
        if expected is None:
            continue
        actual = (
            len(_case_list(gold))
            if actual_key == "case_count"
            else int(family_group_coverage.get(actual_key) or 0)
        )
        if actual < expected:
            failures.append(
                {"metric": actual_key, "expected_min": expected, "actual": actual}
            )
    unresolved_minimum = thresholds.get("unresolved_covered_family_group_count_min")
    if unresolved_minimum is not None:
        actual = int(
            family_group_coverage.get("unresolved_covered_family_group_count") or 0
        )
        if actual < unresolved_minimum:
            failures.append(
                {
                    "metric": "unresolved_covered_family_group_count",
                    "expected_min": unresolved_minimum,
                    "actual": actual,
                }
            )
    expected_theme_count = thresholds.get("required_theme_count")
    if expected_theme_count is not None:
        actual = int(family_group_coverage.get("required_group_count") or 0)
        if actual != expected_theme_count:
            failures.append(
                {
                    "metric": "required_group_count",
                    "expected": expected_theme_count,
                    "actual": actual,
                }
            )
    return _check(
        "gold_eval_family_group_coverage",
        not failures and bool(family_group_coverage.get("passed")),
        {
            "required_group_ids": family_group_coverage.get("required_group_ids", []),
            "positive_covered_group_ids": family_group_coverage.get(
                "positive_covered_group_ids",
                [],
            ),
            "negative_covered_group_ids": family_group_coverage.get(
                "negative_covered_group_ids",
                [],
            ),
            "unresolved_covered_group_ids": family_group_coverage.get(
                "unresolved_covered_group_ids",
                [],
            ),
            "adjudicated_covered_group_ids": family_group_coverage.get(
                "adjudicated_covered_group_ids",
                [],
            ),
            "failures": failures,
        },
    )


def _check_gold_identity(gold: dict[str, Any]) -> dict[str, Any]:
    passed = gold.get("schema_version") == APPLICABILITY_GOLD_EVAL_SCHEMA_VERSION
    return _check(
        "gold_eval_identity_valid",
        passed,
        {"schema_version": gold.get("schema_version")},
    )


def _check_gold_cases(gold: dict[str, Any]) -> dict[str, Any]:
    cases = _case_list(gold)
    ids = [str(case.get("id") or "") for case in cases]
    duplicate_ids = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    unsafe_ids = sorted(case_id for case_id in ids if not _safe_segment(case_id))
    passed = bool(cases) and not duplicate_ids and not unsafe_ids
    return _check(
        "gold_eval_cases_present",
        passed,
        {
            "case_count": len(cases),
            "duplicate_ids": duplicate_ids,
            "unsafe_ids": unsafe_ids,
        },
    )


def _check_gold_profiles(gold: dict[str, Any]) -> dict[str, Any]:
    profile_counts = Counter(str(case.get("profile") or "") for case in _case_list(gold))
    missing = sorted(REQUIRED_GOLD_PROFILES - set(profile_counts))
    return _check(
        "gold_eval_required_profiles_present",
        not missing,
        {"profile_counts": dict(profile_counts), "missing_profiles": missing},
    )


def _check_gold_adjudication(gold: dict[str, Any]) -> dict[str, Any]:
    failures = []
    for case in _case_list(gold):
        adjudication = case.get("adjudication")
        if not isinstance(adjudication, dict):
            failures.append({"case_id": case.get("id"), "fields": ["adjudication"]})
            continue
        missing = [
            field
            for field in ("status", "rationale", "adjudicated_by", "adjudicated_at")
            if not adjudication.get(field)
        ]
        if missing:
            failures.append({"case_id": case.get("id"), "fields": missing})
    return _check("gold_eval_cases_have_adjudication", not failures, {"failures": failures})


def _check_gold_arbitration_expectations(gold: dict[str, Any]) -> dict[str, Any]:
    case_ids = [
        str(case.get("id") or "")
        for case in _case_list(gold)
        if isinstance(case.get("expected_arbitration_statuses_by_rule_id"), dict)
        or isinstance(
            case.get("expected_arbitration_decision_effects_by_rule_id"),
            dict,
        )
    ]
    return _check(
        "gold_eval_cases_have_arbitration_expectations",
        bool(case_ids),
        {"case_ids": sorted(case_ids)},
    )


def _check(name: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"name": name, "passed": bool(passed), "details": details}


def _safe_segment(value: str) -> bool:
    try:
        _validate_safe_segment(value, "case id")
    except ValueError:
        return False
    return True
