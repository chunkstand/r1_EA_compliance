from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .final_qa_certification_common import _output_paths
from .final_qa_certification_common import _read_json
from .final_qa_certification_common import _selector_value
from .final_qa_certification_common import _sha256_file
from .final_qa_certification_common import _utc_now
from .final_qa_certification_common import _write_json
from .final_qa_certification_common import DEFAULT_CONFIG_PATH
from .final_qa_certification_common import DEFAULT_EXPECTED_SUMMARY_PATH
from .final_qa_certification_runtime import validate_final_qa_certification_report


FINAL_QA_DIRECT_EVAL_SCHEMA_VERSION = "final-qa-direct-eval-results-v1"
FINAL_QA_FAILURE_INTAKE_SCHEMA_VERSION = "final-qa-failure-intake-cases-v1"
FINAL_QA_DIRECT_EVAL_CONTRACT_ID = "final-qa-direct-eval-v1"
FINAL_QA_DIRECT_EVAL_SCORER_VERSION = "final-qa-direct-eval-deterministic-v1"
FINAL_QA_DIRECT_EVAL_FILENAME = "final_qa_direct_eval_results.json"
FINAL_QA_FAILURE_INTAKE_FILENAME = "final_qa_failure_intake_cases.json"

REQUIRED_METRIC_GROUP_IDS = [
    "identity_and_freshness",
    "machine_gate_replay",
    "artifact_hash_alignment",
    "review_packet_and_decision_alignment",
    "human_boundary",
]


@dataclass(frozen=True)
class FinalQADirectEvalResult:
    summary: dict[str, Any]
    output_path: Path
    failure_intake_path: Path


def run_final_qa_direct_eval(
    *,
    output_dir: Path = Path("source_library"),
    review_id: str | None = None,
    config_path: Path = DEFAULT_CONFIG_PATH,
    expected_summary_path: Path = DEFAULT_EXPECTED_SUMMARY_PATH,
    results_dir: Path | None = None,
) -> FinalQADirectEvalResult:
    """Score the generated final-QA packet as a deterministic direct-eval artifact."""

    config = _read_json(config_path)
    expected = _read_json(expected_summary_path)
    resolved_review_id = review_id or str(config["review_id"])
    source_set_id = str(config.get("source_set_id") or "")
    paths = _output_paths(output_dir, resolved_review_id, results_dir)
    output_path = paths.results_dir / FINAL_QA_DIRECT_EVAL_FILENAME
    failure_intake_path = paths.results_dir / FINAL_QA_FAILURE_INTAKE_FILENAME

    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id=resolved_review_id,
        config_path=config_path,
        expected_summary_path=expected_summary_path,
        results_dir=paths.results_dir,
    )
    report = _read_json(paths.report_path) if paths.report_path.exists() else {}
    manifest = _read_json(paths.manifest_path) if paths.manifest_path.exists() else {}
    validation_payload = (
        _read_json(paths.validation_path) if paths.validation_path.exists() else {}
    )

    metric_groups = _metric_groups(
        validation_summary=validation.summary,
        report=report,
        manifest=manifest,
        validation_payload=validation_payload,
        config=config,
        expected=expected,
        paths=paths,
        review_id=resolved_review_id,
        source_set_id=source_set_id,
    )
    failed_groups = [group for group in metric_groups if not group["passed"]]
    failure_cases = [
        _failure_case(
            group=group,
            review_id=resolved_review_id,
            source_set_id=source_set_id,
            paths=paths,
            config_path=config_path,
            expected_summary_path=expected_summary_path,
        )
        for group in failed_groups
    ]
    failure_intake = {
        "schema_version": FINAL_QA_FAILURE_INTAKE_SCHEMA_VERSION,
        "contract_id": FINAL_QA_DIRECT_EVAL_CONTRACT_ID,
        "scorer_version": FINAL_QA_DIRECT_EVAL_SCORER_VERSION,
        "created_at": _utc_now(),
        "review_id": resolved_review_id,
        "source_set_id": source_set_id,
        "case_count": len(failure_cases),
        "cases": failure_cases,
    }
    paths.results_dir.mkdir(parents=True, exist_ok=True)
    _write_json(failure_intake_path, failure_intake)

    required_present_missing = sorted(
        set(REQUIRED_METRIC_GROUP_IDS) - {group["id"] for group in metric_groups}
    )
    blocking_gap_group_ids = sorted(group["id"] for group in failed_groups)
    summary = {
        "schema_version": FINAL_QA_DIRECT_EVAL_SCHEMA_VERSION,
        "contract_id": FINAL_QA_DIRECT_EVAL_CONTRACT_ID,
        "scorer_version": FINAL_QA_DIRECT_EVAL_SCORER_VERSION,
        "created_at": _utc_now(),
        "review_id": resolved_review_id,
        "source_set_id": source_set_id,
        "direct_eval_present": True,
        "passed": not failed_groups and not required_present_missing,
        "metric_group_count": len(metric_groups),
        "required_metric_group_ids": REQUIRED_METRIC_GROUP_IDS,
        "required_metric_group_ids_present": required_present_missing,
        "blocking_gap_group_ids": blocking_gap_group_ids,
        "failure_intake_path": str(failure_intake_path),
        "failure_intake_case_count": len(failure_cases),
        "source_artifacts": _source_artifacts(
            paths=paths,
            config_path=config_path,
            expected_summary_path=expected_summary_path,
        ),
        "metric_groups": metric_groups,
    }
    _write_json(output_path, summary)
    return FinalQADirectEvalResult(
        summary=summary,
        output_path=output_path,
        failure_intake_path=failure_intake_path,
    )


def _metric_groups(
    *,
    validation_summary: dict[str, Any],
    report: dict[str, Any],
    manifest: dict[str, Any],
    validation_payload: dict[str, Any],
    config: dict[str, Any],
    expected: dict[str, Any],
    paths: Any,
    review_id: str,
    source_set_id: str,
) -> list[dict[str, Any]]:
    return [
        _metric_group(
            "identity_and_freshness",
            passed=(
                validation_summary.get("review_id") == review_id
                and validation_summary.get("source_set_id") == source_set_id
                and report.get("review_id") == review_id
                and report.get("source_set_id") == source_set_id
                and manifest.get("review_id") == review_id
                and manifest.get("source_set_id") == source_set_id
                and expected.get("review_id") == review_id
                and expected.get("source_set_id") == source_set_id
            ),
            failure_category="review_source_set_mismatch",
            metrics={
                "validation_passed": validation_summary.get("passed"),
                "validation_check_count": validation_summary.get("check_count"),
                "validation_failed_check_count": validation_summary.get("failed_check_count"),
            },
        ),
        _metric_group(
            "machine_gate_replay",
            passed=(
                validation_summary.get("passed") is True
                and _selector_value(report, "gate_replay_summary.machine_replay_status")
                == "passed"
                and _selector_value(report, "gate_replay_summary.phase_eval.phase_count")
                == expected.get("expected_counts", {}).get("phase_eval_phase_count")
                and _selector_value(
                    report,
                    "gate_replay_summary.phase_eval.passed_phase_count",
                )
                == expected.get("expected_counts", {}).get("phase_eval_passed_phase_count")
                and _selector_value(
                    report,
                    "gate_replay_summary.current_promotion_suite.required_current_result_count",
                )
                == expected.get("expected_counts", {}).get(
                    "promotion_suite_required_current_result_count"
                )
                and _selector_value(
                    report,
                    "gate_replay_summary.current_promotion_suite."
                    "passed_required_current_result_count",
                )
                == expected.get("expected_counts", {}).get(
                    "promotion_suite_passed_required_current_result_count"
                )
            ),
            failure_category="stale_artifact",
            metrics={
                "machine_replay_status": _selector_value(
                    report,
                    "gate_replay_summary.machine_replay_status",
                ),
                "failure_category_counts": validation_summary.get(
                    "failure_category_counts",
                    {},
                ),
            },
        ),
        _metric_group(
            "artifact_hash_alignment",
            passed=_artifact_hashes_align(
                paths=paths,
                validation_payload=validation_payload,
                manifest=manifest,
                expected=expected,
            ),
            failure_category="input_hash_mismatch",
            metrics={
                "declared_output_hash_count": len(
                    validation_payload.get("output_hashes", {})
                    if isinstance(validation_payload.get("output_hashes"), dict)
                    else {}
                ),
                "declared_input_hash_count": len(
                    manifest.get("input_hashes", {})
                    if isinstance(manifest.get("input_hashes"), dict)
                    else {}
                ),
            },
        ),
        _metric_group(
            "review_packet_and_decision_alignment",
            passed=(
                _selector_value(report, "review_packet_index_qa.validation_failed_check_count")
                == 0
                and _selector_value(report, "finding_qa.rule_claim_gap_count") == 0
                and _selector_value(
                    report,
                    "decision_support_qa.litigation_risk_legal_conclusion_count",
                )
                == 0
                and _selector_value(report, "finding_qa.authority_finding_count")
                == expected.get("expected_counts", {}).get("authority_finding_count")
                and _selector_value(
                    report,
                    "review_packet_index_qa.applicable_authority_count",
                )
                == expected.get("expected_counts", {}).get(
                    "review_packet_index_applicable_authority_count"
                )
            ),
            failure_category="count_drift",
            metrics={
                "authority_finding_count": _selector_value(
                    report,
                    "finding_qa.authority_finding_count",
                ),
                "review_packet_applicable_authority_count": _selector_value(
                    report,
                    "review_packet_index_qa.applicable_authority_count",
                ),
                "rule_claim_gap_count": _selector_value(
                    report,
                    "finding_qa.rule_claim_gap_count",
                ),
            },
        ),
        _metric_group(
            "human_boundary",
            passed=(
                _selector_value(report, "certification_statement.legal_conclusion") is False
                and bool(_selector_value(report, "certification_statement.caveat"))
                and str(_selector_value(report, "gate_replay_summary.machine_replay_status"))
                == "passed"
            ),
            failure_category="legal_conclusion_leak",
            metrics={
                "legal_conclusion": _selector_value(
                    report,
                    "certification_statement.legal_conclusion",
                ),
                "accepted_v1_risk_count": _selector_value(
                    report,
                    "accepted_v1_risk_ledger.accepted_pending_count",
                ),
            },
        ),
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


def _artifact_hashes_align(
    *,
    paths: Any,
    validation_payload: dict[str, Any],
    manifest: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    output_hashes = validation_payload.get("output_hashes")
    if not isinstance(output_hashes, dict):
        return False
    required_output_hashes = {
        "json_sha256": paths.report_path,
        "markdown_sha256": paths.markdown_path,
        "pdf_sha256": paths.pdf_path,
        "manifest_sha256": paths.manifest_path,
    }
    for key, path in required_output_hashes.items():
        if not path.exists() or output_hashes.get(key) != _sha256_file(path):
            return False
    input_hashes = manifest.get("input_hashes")
    expected_hashes = expected.get("input_hashes")
    return isinstance(input_hashes, dict) and input_hashes == expected_hashes


def _failure_case(
    *,
    group: dict[str, Any],
    review_id: str,
    source_set_id: str,
    paths: Any,
    config_path: Path,
    expected_summary_path: Path,
) -> dict[str, Any]:
    group_id = str(group["id"])
    return {
        "case_id": f"final-qa:{review_id}:{group_id}",
        "review_id": review_id,
        "source_set_id": source_set_id,
        "metric_group_id": group_id,
        "failure_category": group.get("failure_category"),
        "owner": "final_qa",
        "risk_level": "blocking",
        "lifecycle_status": "open",
        "assertion": f"Final QA direct-eval metric group {group_id} must pass.",
        "review_condition": "Inspect the cited final QA packet artifacts and source gate outputs.",
        "removal_condition": "Remove only after the metric group is green in a regenerated direct-eval artifact.",
        "scorer_version": FINAL_QA_DIRECT_EVAL_SCORER_VERSION,
        "source_artifacts": _source_artifacts(
            paths=paths,
            config_path=config_path,
            expected_summary_path=expected_summary_path,
        ),
    }


def _source_artifacts(
    *,
    paths: Any,
    config_path: Path,
    expected_summary_path: Path,
) -> list[dict[str, Any]]:
    artifact_paths = [
        ("report", paths.report_path),
        ("manifest", paths.manifest_path),
        ("validation", paths.validation_path),
        ("markdown", paths.markdown_path),
        ("pdf", paths.pdf_path),
        ("config", config_path),
        ("expected_summary", expected_summary_path),
    ]
    artifacts = []
    for artifact_id, path in artifact_paths:
        record: dict[str, Any] = {
            "artifact_id": artifact_id,
            "path": str(path),
            "exists": path.exists(),
        }
        if path.exists():
            record["sha256"] = _sha256_file(path)
            record["size_bytes"] = path.stat().st_size
        artifacts.append(record)
    return artifacts
