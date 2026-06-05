from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .ea_consistency_decision_support_inputs import _report_paths
from .ea_consistency_decision_support_models import DEFAULT_CONFIG_PATH
from .ea_consistency_decision_support_models import DEFAULT_EXPECTED_SUMMARY_PATH
from .ea_consistency_decision_support_models import _dict
from .ea_consistency_decision_support_models import _read_json
from .ea_consistency_decision_support_models import _sha256_file
from .ea_consistency_decision_support_models import _utc_now
from .ea_consistency_decision_support_models import _write_json
from .ea_consistency_decision_support_runtime import (
    validate_ea_consistency_decision_support_report,
)


DECISION_SUPPORT_DIRECT_EVAL_SCHEMA_VERSION = (
    "ea-consistency-decision-support-direct-eval-results-v1"
)
DECISION_SUPPORT_FAILURE_INTAKE_SCHEMA_VERSION = (
    "ea-consistency-decision-support-failure-intake-cases-v1"
)
DECISION_SUPPORT_DIRECT_EVAL_CONTRACT_ID = "ea-consistency-decision-support-direct-eval-v1"
DECISION_SUPPORT_DIRECT_EVAL_SCORER_VERSION = (
    "ea-consistency-decision-support-direct-eval-deterministic-v1"
)
DECISION_SUPPORT_DIRECT_EVAL_FILENAME = (
    "ea_consistency_decision_support_direct_eval_results.json"
)
DECISION_SUPPORT_FAILURE_INTAKE_FILENAME = (
    "ea_consistency_decision_support_failure_intake_cases.json"
)

REQUIRED_METRIC_GROUP_IDS = [
    "identity_and_freshness",
    "source_artifact_replay",
    "authority_and_count_alignment",
    "evidence_traceability",
    "artifact_hash_alignment",
    "supervisor_boundary",
]


@dataclass(frozen=True)
class DecisionSupportDirectEvalResult:
    summary: dict[str, Any]
    output_path: Path
    failure_intake_path: Path


def run_ea_consistency_decision_support_direct_eval(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_summary_path: Path = DEFAULT_EXPECTED_SUMMARY_PATH,
    results_dir: Path | None = None,
) -> DecisionSupportDirectEvalResult:
    """Score an existing EA consistency decision-support report family."""

    output_dir = Path(output_dir)
    config = _read_json(Path(config_path))
    expected = _read_json(Path(expected_summary_path))
    selected_review_id = str(review_id or config.get("review_id") or expected["review_id"])
    source_set_id = str(config.get("source_set_id") or expected.get("source_set_id") or "")
    review_dir = output_dir / "reviews" / selected_review_id
    report_dir = Path(results_dir) if results_dir is not None else review_dir / "decision_support"
    report_path, markdown_path, pdf_path, manifest_path = _report_paths(report_dir)
    output_path = report_dir / DECISION_SUPPORT_DIRECT_EVAL_FILENAME
    failure_intake_path = report_dir / DECISION_SUPPORT_FAILURE_INTAKE_FILENAME

    validation = validate_ea_consistency_decision_support_report(
        output_dir=output_dir,
        review_id=selected_review_id,
        config_path=Path(config_path),
        expected_summary_path=Path(expected_summary_path),
        results_dir=report_dir,
    ).summary
    report = _read_optional_json(report_path)
    manifest = _read_optional_json(manifest_path)
    markdown = _read_text(markdown_path)
    source_artifacts = _source_artifacts(
        report_path=report_path,
        markdown_path=markdown_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        config_path=Path(config_path),
        expected_summary_path=Path(expected_summary_path),
    )
    metric_groups = _metric_groups(
        review_id=selected_review_id,
        source_set_id=source_set_id,
        expected=expected,
        report=report,
        manifest=manifest,
        markdown=markdown,
        validation=validation,
        source_artifacts=source_artifacts,
    )
    failed_groups = [group for group in metric_groups if not group["passed"]]
    failure_cases = [
        _failure_case(
            group=group,
            review_id=selected_review_id,
            source_set_id=source_set_id,
            report_path=report_path,
            markdown_path=markdown_path,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
            config_path=Path(config_path),
            expected_summary_path=Path(expected_summary_path),
        )
        for group in failed_groups
    ]
    report_dir.mkdir(parents=True, exist_ok=True)
    failure_intake = {
        "schema_version": DECISION_SUPPORT_FAILURE_INTAKE_SCHEMA_VERSION,
        "contract_id": DECISION_SUPPORT_DIRECT_EVAL_CONTRACT_ID,
        "scorer_version": DECISION_SUPPORT_DIRECT_EVAL_SCORER_VERSION,
        "created_at": _utc_now(),
        "review_id": selected_review_id,
        "source_set_id": source_set_id,
        "case_count": len(failure_cases),
        "cases": failure_cases,
    }
    _write_json(failure_intake_path, failure_intake)

    required_present_missing = sorted(
        set(REQUIRED_METRIC_GROUP_IDS) - {group["id"] for group in metric_groups}
    )
    blocking_gap_group_ids = sorted(group["id"] for group in failed_groups)
    summary = {
        "schema_version": DECISION_SUPPORT_DIRECT_EVAL_SCHEMA_VERSION,
        "contract_id": DECISION_SUPPORT_DIRECT_EVAL_CONTRACT_ID,
        "scorer_version": DECISION_SUPPORT_DIRECT_EVAL_SCORER_VERSION,
        "created_at": _utc_now(),
        "review_id": selected_review_id,
        "source_set_id": source_set_id,
        "direct_eval_present": True,
        "passed": not failed_groups and not required_present_missing,
        "metric_group_count": len(metric_groups),
        "required_metric_group_ids": REQUIRED_METRIC_GROUP_IDS,
        "required_metric_group_ids_present": required_present_missing,
        "blocking_gap_group_ids": blocking_gap_group_ids,
        "failure_intake_path": str(failure_intake_path),
        "failure_intake_case_count": len(failure_cases),
        "source_artifacts": source_artifacts,
        "metric_groups": metric_groups,
    }
    _write_json(output_path, summary)
    return DecisionSupportDirectEvalResult(
        summary=summary,
        output_path=output_path,
        failure_intake_path=failure_intake_path,
    )


def _metric_groups(
    *,
    review_id: str,
    source_set_id: str,
    expected: dict[str, Any],
    report: dict[str, Any],
    manifest: dict[str, Any],
    markdown: str,
    validation: dict[str, Any],
    source_artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    checks = _checks_by_name(validation)
    counts = _dict(validation.get("counts"))
    return [
        _metric_group(
            "identity_and_freshness",
            passed=(
                all(record["exists"] and record.get("parse_ok", True) for record in source_artifacts)
                and validation.get("review_id") == review_id
                and validation.get("source_set_id") == source_set_id
                and report.get("review_id") == review_id
                and report.get("source_set_id") == source_set_id
                and manifest.get("review_id") == review_id
                and manifest.get("source_set_id") == source_set_id
                and _check_passed(checks, "report_schema_version")
                and _check_passed(checks, "manifest_schema_version")
                and _check_passed(checks, "decision_support_status")
            ),
            failure_category="review_source_set_mismatch",
            metrics={
                "validation_passed": validation.get("passed"),
                "validation_reviewer_ready": validation.get("reviewer_ready"),
                "failure_count": validation.get("failure_count"),
            },
        ),
        _metric_group(
            "source_artifact_replay",
            passed=(
                validation.get("source_artifact_validation_passed") is True
                and _check_passed(checks, "decision_support_source_artifacts_revalidate")
            ),
            failure_category="stale_artifact",
            metrics={
                "source_artifact_validation_passed": validation.get(
                    "source_artifact_validation_passed"
                ),
                "source_failure_categories": validation.get("failure_categories", []),
            },
        ),
        _metric_group(
            "authority_and_count_alignment",
            passed=(
                _safe_int(counts.get("authority_finding_count")) > 0
                and _safe_int(counts.get("non_applicable_authority_count")) > 0
                and _safe_int(counts.get("review_packet_index_validation_failed_check_count")) == 0
                and all(_check_passed(checks, name) for name in _COUNT_CHECK_NAMES)
            ),
            failure_category="count_drift",
            metrics={
                "authority_finding_count": counts.get("authority_finding_count"),
                "non_applicable_authority_count": counts.get("non_applicable_authority_count"),
                "forest_plan_applicable_standard_count": counts.get(
                    "forest_plan_applicable_standard_count"
                ),
                "review_packet_index_validation_failed_check_count": counts.get(
                    "review_packet_index_validation_failed_check_count"
                ),
            },
        ),
        _metric_group(
            "evidence_traceability",
            passed=(
                all(_check_passed(checks, name) for name in _EVIDENCE_CHECK_NAMES)
                and _required_applicable_rows_passed(checks, expected)
            ),
            failure_category="applicable_authority_missing_dual_evidence",
            metrics={
                "required_applicable_authority_rows_present": (
                    _required_applicable_rows_passed(checks, expected)
                ),
                "non_applicable_rows_have_search_coverage": _check_passed(
                    checks,
                    "report_non_applicable_rows_have_search_coverage",
                ),
                "applicable_standards_have_evidence": _check_passed(
                    checks,
                    "report_applicable_standards_have_evidence",
                ),
            },
        ),
        _metric_group(
            "artifact_hash_alignment",
            passed=all(_check_passed(checks, name) for name in _HASH_CHECK_NAMES),
            failure_category="input_hash_mismatch",
            metrics={
                "manifest_file_input_hashes_are_current": _check_passed(
                    checks,
                    "manifest_file_input_hashes_are_current",
                ),
                "embedded_manifest_input_hashes_are_current": _check_passed(
                    checks,
                    "embedded_manifest_input_hashes_are_current",
                ),
            },
        ),
        _metric_group(
            "supervisor_boundary",
            passed=(
                _dict(report.get("executive_determination")).get("legal_conclusion") is False
                and all(_check_passed(checks, name) for name in _BOUNDARY_CHECK_NAMES)
                and "does not replace" in markdown
            ),
            failure_category="residual_risk_legal_conclusion",
            metrics={
                "legal_conclusion": _dict(report.get("executive_determination")).get(
                    "legal_conclusion"
                ),
                "markdown_has_supervisor_boundary": "does not replace" in markdown,
            },
        ),
    ]


_COUNT_CHECK_NAMES = [
    "report_authority_finding_count_matches_current_artifacts",
    "report_applicable_authority_count_matches_current_artifacts",
    "report_non_applicable_authority_count_matches_current_artifacts",
    "report_forest_plan_component_finding_count_matches_current_artifacts",
    "report_forest_plan_applicable_standard_count_matches_current_artifacts",
    "report_applicable_forest_plan_standard_row_count_matches_current_artifacts",
]

_EVIDENCE_CHECK_NAMES = [
    "report_non_applicable_rows_have_search_coverage",
    "report_applicable_standards_complete",
    "report_applicable_standards_have_evidence",
    "report_implementation_confirmations_complete",
]

_HASH_CHECK_NAMES = [
    "manifest_file_matches_embedded_manifest",
    "manifest_file_input_hashes_are_current",
    "embedded_manifest_input_hashes_are_current",
]

_BOUNDARY_CHECK_NAMES = [
    "report_residual_risks_are_not_legal_conclusions",
    "report_does_not_reference_manual_root_drafts",
    "markdown_supervisor_rendering_contract",
    "pdf_supervisor_rendering_contract",
]


def _metric_group(
    group_id: str,
    *,
    passed: bool,
    failure_category: str,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": group_id,
        "passed": bool(passed),
        "failure_category": None if passed else failure_category,
        "metrics": metrics,
    }


def _failure_case(
    *,
    group: dict[str, Any],
    review_id: str,
    source_set_id: str,
    report_path: Path,
    markdown_path: Path,
    pdf_path: Path,
    manifest_path: Path,
    config_path: Path,
    expected_summary_path: Path,
) -> dict[str, Any]:
    group_id = str(group["id"])
    return {
        "case_id": f"decision-support:{review_id}:{group_id}",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "metric_group_id": group_id,
        "failure_category": group.get("failure_category"),
        "owner": "decision_support",
        "risk_level": "blocking",
        "lifecycle_status": "open",
        "assertion": f"Decision-support direct-eval metric group {group_id} must pass.",
        "review_condition": "Inspect the cited decision-support report family and source artifacts.",
        "removal_condition": "Remove only after the metric group is green in a regenerated direct-eval artifact.",
        "scorer_version": DECISION_SUPPORT_DIRECT_EVAL_SCORER_VERSION,
        "source_artifacts": _source_artifacts(
            report_path=report_path,
            markdown_path=markdown_path,
            pdf_path=pdf_path,
            manifest_path=manifest_path,
            config_path=config_path,
            expected_summary_path=expected_summary_path,
        ),
    }


def _source_artifacts(
    *,
    report_path: Path,
    markdown_path: Path,
    pdf_path: Path,
    manifest_path: Path,
    config_path: Path,
    expected_summary_path: Path,
) -> list[dict[str, Any]]:
    artifact_paths = [
        ("report", report_path, "json"),
        ("markdown", markdown_path, "text"),
        ("pdf", pdf_path, "pdf"),
        ("manifest", manifest_path, "json"),
        ("config", config_path, "json"),
        ("expected_summary", expected_summary_path, "json"),
    ]
    return [_artifact_record(*artifact) for artifact in artifact_paths]


def _artifact_record(artifact_id: str, path: Path, artifact_type: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "artifact_id": artifact_id,
        "path": str(path),
        "exists": path.exists(),
        "artifact_type": artifact_type,
    }
    if not path.exists():
        record["parse_ok"] = False
        return record
    record["sha256"] = _sha256_file(path)
    record["size_bytes"] = path.stat().st_size
    if artifact_type == "json":
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
            record["parse_ok"] = isinstance(parsed, dict)
        except json.JSONDecodeError as exc:
            record["parse_ok"] = False
            record["error"] = str(exc)
    elif artifact_type == "pdf":
        record["parse_ok"] = path.read_bytes().startswith(b"%PDF-")
    else:
        record["parse_ok"] = True
    return record


def _read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _checks_by_name(validation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    checks = validation.get("checks")
    if not isinstance(checks, list):
        return {}
    return {
        str(check.get("name")): check
        for check in checks
        if isinstance(check, dict) and check.get("name")
    }


def _check_passed(checks_by_name: dict[str, dict[str, Any]], name: str) -> bool:
    return checks_by_name.get(name, {}).get("passed") is True


def _required_applicable_rows_passed(
    checks_by_name: dict[str, dict[str, Any]],
    expected: dict[str, Any],
) -> bool:
    required_rows = expected.get("required_applicable_authority_rows")
    if not isinstance(required_rows, list) or not required_rows:
        return True
    return _check_passed(checks_by_name, "required_applicable_authority_rows_present")


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
