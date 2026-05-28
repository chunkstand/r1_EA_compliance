from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.final_qa_certification import run_final_qa_certification
from usfs_r1_ea_sources.final_qa_certification import validate_final_qa_certification_report
from usfs_r1_ea_sources.final_qa_certification_validation import _finding_trace_ids_present

from tests.support.final_qa_certification_fixtures import _read_json
from tests.support.final_qa_certification_fixtures import _write_json_file
from tests.support.final_qa_certification_fixtures import _write_sequence_2_fixture


def test_sequence_2_validate_only_fails_closed_when_packet_missing(tmp_path: Path) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)

    result = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=tmp_path / "missing-final-qa-output",
    )

    assert result.summary["passed"] is False
    assert result.summary["failure_category_counts"]["missing_required_artifact"] == 5


def test_final_qa_validate_allows_phase_eval_pending_only_final_qa_gate(
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

    review_dir = output_dir / "reviews" / "review-test"
    phase_eval = _read_json(review_dir / "phase_eval_results.json")
    phase_eval["passed"] = False
    phase_eval["reviewer_ready"] = False
    phase_eval["phase_count"] = 3
    phase_eval["passed_phase_count"] = 2
    phase_eval["reviewer_ready_phase_count"] = 2
    phase_eval["phases"] = [
        {"name": "base_1", "passed": True, "reviewer_ready": True},
        {"name": "base_2", "passed": True, "reviewer_ready": True},
        {
            "name": "final_qa_certification_report",
            "passed": False,
            "reviewer_ready": False,
        },
    ]
    _write_json_file(review_dir / "phase_eval_results.json", phase_eval)

    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert validation.summary["passed"] is True
    assert validation.summary["failure_category_counts"] == {}


def test_final_qa_validate_fails_when_validation_sidecar_output_hash_is_stale(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    results_dir = tmp_path / "final-qa-output"

    result = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert result.summary["passed"] is True
    result.report_path.write_text(
        result.report_path.read_text(encoding="utf-8") + "\n",
        encoding="utf-8",
    )

    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert validation.summary["passed"] is False
    assert validation.summary["failure_category_counts"]["stale_artifact"] == 1


def test_final_qa_trace_validation_keeps_dual_evidence_for_pass_rows() -> None:
    gap_row = {
        "rule_id": "rule-gap",
        "candidate_authority_id": "candidate:rule-gap",
        "applicability_decision_id": "decision:rule-gap",
        "source_claim_ids": ["claim:rule-gap"],
        "status": "gap",
        "source_pointers": {
            "ea_package_evidence": {
                "artifact_path": "source_library/reviews/review-test/package.json",
                "chunk_id": "chunk:package",
            },
            "source_library_evidence": None,
        },
    }
    pass_row = {
        **gap_row,
        "rule_id": "rule-pass",
        "status": "pass",
    }
    policy_config = {
        "authority_evidence_policy": {
            "allow_single_evidence_statuses": ["gap", "uncertain"]
        }
    }

    assert _finding_trace_ids_present([gap_row], policy_config) is True
    assert _finding_trace_ids_present([gap_row], {}) is False
    assert _finding_trace_ids_present([pass_row], policy_config) is False
