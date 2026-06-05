from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.ea_consistency_decision_support import (
    run_ea_consistency_decision_support,
)
from usfs_r1_ea_sources.ea_consistency_decision_support import (
    run_ea_consistency_decision_support_direct_eval,
)
from usfs_r1_ea_sources.ea_consistency_decision_support_direct_eval import (
    DECISION_SUPPORT_DIRECT_EVAL_CONTRACT_ID,
)
from usfs_r1_ea_sources.ea_consistency_decision_support_direct_eval import (
    DECISION_SUPPORT_DIRECT_EVAL_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.ea_consistency_decision_support_direct_eval import (
    DECISION_SUPPORT_FAILURE_INTAKE_SCHEMA_VERSION,
)

from tests.support.ea_consistency_decision_support_fixtures import _read_json
from tests.support.ea_consistency_decision_support_fixtures import _write_json_file
from tests.support.ea_consistency_decision_support_fixtures import _write_sequence_2_fixture


def test_decision_support_direct_eval_writes_green_summary_and_empty_intake(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    generated = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )
    assert generated.summary["passed"] is True

    result = run_ea_consistency_decision_support_direct_eval(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["schema_version"] == DECISION_SUPPORT_DIRECT_EVAL_SCHEMA_VERSION
    assert result.summary["contract_id"] == DECISION_SUPPORT_DIRECT_EVAL_CONTRACT_ID
    assert result.summary["direct_eval_present"] is True
    assert result.summary["passed"] is True
    assert result.summary["metric_group_count"] == 6
    assert result.summary["blocking_gap_group_ids"] == []
    assert result.summary["required_metric_group_ids_present"] == []
    assert result.summary["failure_intake_case_count"] == 0
    intake = _read_json(result.failure_intake_path)
    assert intake["schema_version"] == DECISION_SUPPORT_FAILURE_INTAKE_SCHEMA_VERSION
    assert intake["case_count"] == 0
    assert intake["cases"] == []


def test_decision_support_direct_eval_fails_closed_for_stale_manifest_hash(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    generated = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )
    assert generated.summary["passed"] is True
    manifest = _read_json(generated.manifest_path)
    manifest["input_hashes"]["compliance_matrix_sha256"] = "stale"
    _write_json_file(generated.manifest_path, manifest)

    result = run_ea_consistency_decision_support_direct_eval(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["passed"] is False
    assert "artifact_hash_alignment" in result.summary["blocking_gap_group_ids"]
    assert result.summary["failure_intake_case_count"] >= 1
    intake = _read_json(result.failure_intake_path)
    case = next(
        case
        for case in intake["cases"]
        if case["metric_group_id"] == "artifact_hash_alignment"
    )
    assert case["owner"] == "decision_support"
    assert case["risk_level"] == "blocking"
    assert case["source_set_id"] == "source-set-test"
    assert {artifact["artifact_id"] for artifact in case["source_artifacts"]} >= {
        "report",
        "manifest",
        "config",
        "expected_summary",
    }
