from __future__ import annotations

import hashlib
import json
from pathlib import Path

from usfs_r1_ea_sources.graph_gate_review_quality_eval import (
    DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH,
    GRAPH_GATE_REVIEW_QUALITY_RESULTS_SCHEMA_VERSION,
    run_graph_gate_review_quality_eval,
)


def test_graph_gate_review_quality_eval_supports_manifest_owned_positive_delta(
    tmp_path: Path,
) -> None:
    frozen_input = tmp_path / "frozen-review-input.json"
    frozen_input.write_text('{"review_id": "review-1"}\n', encoding="utf-8")
    manifest_path = _write_manifest(
        tmp_path,
        cases=[
            {
                "case_id": "case-positive-delta",
                "review_id": "review-1",
                "case_role": "controlled_defect",
                "frozen_inputs": [
                    {
                        "path": str(frozen_input),
                        "sha256": hashlib.sha256(frozen_input.read_bytes()).hexdigest(),
                    }
                ],
                "control": {
                    "metrics": {
                        "citation_gap_count": 3,
                        "reviewer_traceability_score": 0.4,
                    }
                },
                "treatment": {
                    "metrics": {
                        "citation_gap_count": 1,
                        "reviewer_traceability_score": 0.8,
                    }
                },
            }
        ],
    )

    result = run_graph_gate_review_quality_eval(
        output_dir=tmp_path / "source_library",
        manifest_path=manifest_path,
    )

    assert result.output_path.exists()
    assert result.summary["schema_version"] == GRAPH_GATE_REVIEW_QUALITY_RESULTS_SCHEMA_VERSION
    assert result.summary["command_succeeded"] is True
    assert result.summary["hypothesis_supported"] is True
    assert result.summary["experiment_status"] == "hypothesis_supported"
    assert result.summary["positive_delta_case_count"] == 1
    assert result.summary["critical_regression_count"] == 0
    assert result.summary["net_quality_delta"] > 0


def test_graph_gate_review_quality_eval_records_null_without_command_failure(
    tmp_path: Path,
) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        cases=[
            {
                "case_id": "case-no-delta",
                "control": {
                    "metrics": {
                        "citation_gap_count": 1,
                        "reviewer_traceability_score": 0.5,
                    }
                },
                "treatment": {
                    "metrics": {
                        "citation_gap_count": 1,
                        "reviewer_traceability_score": 0.5,
                    }
                },
            }
        ],
    )

    result = run_graph_gate_review_quality_eval(
        output_dir=tmp_path / "source_library",
        manifest_path=manifest_path,
    )

    assert result.summary["command_succeeded"] is True
    assert result.summary["hypothesis_supported"] is False
    assert result.summary["experiment_status"] == "hypothesis_not_supported"
    assert _threshold_names(result.summary) == {"min_positive_delta_case_count"}


def test_graph_gate_review_quality_eval_fails_closed_for_critical_regression(
    tmp_path: Path,
) -> None:
    manifest_path = _write_manifest(
        tmp_path,
        cases=[
            {
                "case_id": "case-regression",
                "control": {
                    "metrics": {
                        "citation_gap_count": 1,
                        "reviewer_traceability_score": 0.5,
                    }
                },
                "treatment": {
                    "metrics": {
                        "citation_gap_count": 4,
                        "reviewer_traceability_score": 0.7,
                    }
                },
            }
        ],
    )

    result = run_graph_gate_review_quality_eval(
        output_dir=tmp_path / "source_library",
        manifest_path=manifest_path,
    )

    assert result.summary["command_succeeded"] is True
    assert result.summary["hypothesis_supported"] is False
    assert result.summary["experiment_status"] == "hypothesis_not_supported"
    assert result.summary["critical_regression_count"] == 1
    assert "max_critical_regression_count" in _threshold_names(result.summary)


def test_graph_gate_review_quality_eval_derives_full_review_artifact_metrics(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "source_library"
    review_id = "full-review-1"
    source_set_id = "source-set-full-review"
    _write_full_review_fixture(output_dir, review_id=review_id, source_set_id=source_set_id)
    manifest_path = _write_manifest(
        tmp_path,
        quality_dimensions=[
            {
                "metric_id": "graph_gate_gap_count",
                "direction": "lower_is_better",
                "critical": True,
            },
            {
                "metric_id": "unsupported_gate_pass_count",
                "direction": "lower_is_better",
                "critical": True,
            },
            {
                "metric_id": "graph_gate_consistency_score",
                "direction": "higher_is_better",
                "critical": False,
            },
            {
                "metric_id": "reviewer_traceability_score",
                "direction": "higher_is_better",
                "critical": False,
            },
        ],
        threshold_policy={
            "min_case_count": 1,
            "min_complete_case_count": 1,
            "min_distinct_review_count": 1,
            "min_positive_delta_case_count": 1,
            "max_critical_regression_count": 0,
            "max_case_contract_failure_count": 0,
        },
        cases=[
            {
                "case_id": "full-review-artifact-derived",
                "review_id": review_id,
                "source_set_id": source_set_id,
                "case_role": "full_review_artifact_readback",
                "control": {
                    "type": "full_review_artifact_metrics",
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "graph_gate_mode": "ungated_control",
                },
                "treatment": {
                    "type": "full_review_artifact_metrics",
                    "review_id": review_id,
                    "source_set_id": source_set_id,
                    "graph_gate_mode": "gated_treatment",
                    "require_graph_gate": True,
                },
            }
        ],
    )

    result = run_graph_gate_review_quality_eval(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    case = result.summary["cases"][0]
    assert result.summary["hypothesis_supported"] is True
    assert result.summary["distinct_review_count"] == 1
    assert case["control_observation"]["metrics"]["graph_gate_gap_count"] == 1
    assert case["treatment_observation"]["metrics"]["graph_gate_gap_count"] == 0
    assert case["treatment_observation"]["metrics"]["gate_node_count"] == 12
    assert "gate_graph" in case["treatment_observation"]["evidence"]


def test_default_manifest_declares_three_full_review_cases() -> None:
    manifest = json.loads(
        DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert manifest["intent"]
    assert manifest["stop_condition"]
    assert manifest["threshold_policy"]["min_case_count"] == 3
    assert manifest["threshold_policy"]["min_distinct_review_count"] == 3
    assert len(manifest["cases"]) == 3
    assert {
        case["control"]["graph_gate_mode"] for case in manifest["cases"]
    } == {"ungated_control"}
    assert {
        case["treatment"]["graph_gate_mode"] for case in manifest["cases"]
    } == {"gated_treatment"}


def _write_manifest(
    tmp_path: Path,
    *,
    cases: list[dict],
    quality_dimensions: list[dict] | None = None,
    threshold_policy: dict | None = None,
) -> Path:
    manifest = {
        "schema_version": "graph-gate-review-quality-eval-v1",
        "contract_id": "test-graph-gate-review-quality",
        "version": "test",
        "intent": "Test graph-gate review-quality improvement without scorer-owned cases.",
        "stop_condition": "Stop when support would require post-hoc threshold tuning.",
        "hypothesis": {
            "h1": "Treatment improves review quality.",
            "h0": "Treatment does not improve review quality.",
        },
        "threshold_policy": threshold_policy
        or {
            "min_case_count": 1,
            "min_positive_delta_case_count": 1,
            "max_critical_regression_count": 0,
            "max_case_contract_failure_count": 0,
        },
        "quality_dimensions": quality_dimensions
        or [
            {
                "metric_id": "citation_gap_count",
                "direction": "lower_is_better",
                "critical": True,
            },
            {
                "metric_id": "reviewer_traceability_score",
                "direction": "higher_is_better",
                "critical": False,
            },
        ],
        "cases": cases,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def _write_full_review_fixture(
    output_dir: Path, *, review_id: str, source_set_id: str
) -> None:
    review_dir = output_dir / "reviews" / review_id
    app_dir = review_dir / "applicability"
    app_dir.mkdir(parents=True)
    _write_json(
        review_dir / "phase_eval_results.json",
        {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "reviewer_ready": True,
            "blockers": [],
            "phase_count": 2,
            "passed_phase_count": 2,
        },
    )
    _write_json(
        review_dir / "v1_ea_eval_results.json",
        {"summary": {"review_id": review_id, "source_set_id": source_set_id, "passed": True}},
    )
    _write_json(
        review_dir / "compliance_review.json",
        {
            "summary": {
                "review_id": review_id,
                "source_set_id": source_set_id,
                "reviewer_ready": True,
                "validation_passed": True,
                "rule_claim_gap_count": 0,
                "unsupported_finding_ids": [],
                "finding_count": 4,
            }
        },
    )
    _write_json(
        review_dir / "compliance_matrix.json",
        {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "summary": {"reviewer_ready": True, "validated": True},
        },
    )
    _write_json(review_dir / "compliance_validation.json", {"passed": True})
    _write_json(
        app_dir / "applicability_validation.json",
        {"summary": {"review_id": review_id, "source_set_id": source_set_id, "passed": True, "reviewer_ready": True}},
    )
    _write_json(
        app_dir / "generated_rule_pack_validation.json",
        {"summary": {"review_id": review_id, "source_set_id": source_set_id, "passed": True}},
    )
    _write_json(
        app_dir / "applicability_gate_graph.json",
        {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "validation": {"passed": True},
        },
    )
    _write_json(
        app_dir / "applicability_gate_graph_summary.json",
        {
            "review_id": review_id,
            "source_set_id": source_set_id,
            "passed": True,
            "node_count": 12,
            "edge_count": 11,
            "failed_check_count": 0,
        },
    )
    _write_json(app_dir / "applicability_gate_graph_validation.json", {"passed": True})


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _threshold_names(summary: dict) -> set[str]:
    return {str(failure["name"]) for failure in summary["threshold_failures"]}
