from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.final_qa_certification import run_final_qa_certification
from usfs_r1_ea_sources.final_qa_certification import run_final_qa_direct_eval
from usfs_r1_ea_sources.final_qa_direct_eval import FINAL_QA_DIRECT_EVAL_CONTRACT_ID
from usfs_r1_ea_sources.final_qa_direct_eval import FINAL_QA_DIRECT_EVAL_SCHEMA_VERSION
from usfs_r1_ea_sources.final_qa_direct_eval import (
    FINAL_QA_FAILURE_INTAKE_SCHEMA_VERSION,
)

from tests.support.final_qa_certification_fixtures import _read_json
from tests.support.final_qa_certification_fixtures import _write_sequence_2_fixture


def test_final_qa_direct_eval_writes_green_summary_and_empty_intake(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    results_dir = tmp_path / "final-qa-output"
    generated = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert generated.summary["passed"] is True

    result = run_final_qa_direct_eval(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert result.summary["schema_version"] == FINAL_QA_DIRECT_EVAL_SCHEMA_VERSION
    assert result.summary["contract_id"] == FINAL_QA_DIRECT_EVAL_CONTRACT_ID
    assert result.summary["direct_eval_present"] is True
    assert result.summary["passed"] is True
    assert result.summary["blocking_gap_group_ids"] == []
    assert result.summary["required_metric_group_ids_present"] == []
    assert result.summary["failure_intake_case_count"] == 0
    assert result.output_path.exists()
    intake = _read_json(result.failure_intake_path)
    assert intake["schema_version"] == FINAL_QA_FAILURE_INTAKE_SCHEMA_VERSION
    assert intake["case_count"] == 0
    assert intake["cases"] == []


def test_final_qa_direct_eval_fails_closed_with_replayable_case_for_stale_hash(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    results_dir = tmp_path / "final-qa-output"
    generated = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert generated.summary["passed"] is True
    generated.report_path.write_text(
        generated.report_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    result = run_final_qa_direct_eval(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert result.summary["passed"] is False
    assert "artifact_hash_alignment" in result.summary["blocking_gap_group_ids"]
    assert result.summary["failure_intake_case_count"] >= 1
    intake = _read_json(result.failure_intake_path)
    assert intake["case_count"] == result.summary["failure_intake_case_count"]
    case = next(
        case
        for case in intake["cases"]
        if case["metric_group_id"] == "artifact_hash_alignment"
    )
    assert case["owner"] == "final_qa"
    assert case["risk_level"] == "blocking"
    assert case["source_set_id"] == "source-set-test"
    assert {artifact["artifact_id"] for artifact in case["source_artifacts"]} >= {
        "report",
        "validation",
        "manifest",
        "config",
        "expected_summary",
    }
