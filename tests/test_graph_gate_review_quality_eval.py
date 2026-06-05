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


def test_default_manifest_declares_goal_without_claiming_proof(tmp_path: Path) -> None:
    manifest = json.loads(
        DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH.read_text(
            encoding="utf-8"
        )
    )

    assert manifest["intent"]
    assert manifest["stop_condition"]
    assert manifest["cases"] == []

    result = run_graph_gate_review_quality_eval(
        output_dir=tmp_path / "source_library",
        manifest_path=DEFAULT_GRAPH_GATE_REVIEW_QUALITY_EVAL_MANIFEST_PATH,
    )

    assert result.summary["command_succeeded"] is True
    assert result.summary["experiment_status"] == "experiment_blocked"
    assert result.summary["hypothesis_supported"] is False
    assert result.summary["case_count"] == 0
    assert "min_case_count" in _threshold_names(result.summary)


def _write_manifest(tmp_path: Path, *, cases: list[dict]) -> Path:
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
        "threshold_policy": {
            "min_case_count": 1,
            "min_positive_delta_case_count": 1,
            "max_critical_regression_count": 0,
            "max_case_contract_failure_count": 0,
        },
        "quality_dimensions": [
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


def _threshold_names(summary: dict) -> set[str]:
    return {str(failure["name"]) for failure in summary["threshold_failures"]}
