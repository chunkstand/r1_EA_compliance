from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.ea_consistency_decision_support import (
    run_ea_consistency_decision_support,
)
from usfs_r1_ea_sources.ea_consistency_decision_support import (
    validate_ea_consistency_decision_support_report,
)
from usfs_r1_ea_sources.phase_eval import run_phase_aligned_eval

from tests.support.ea_consistency_decision_support_fixtures import _failed_check
from tests.support.ea_consistency_decision_support_fixtures import _phase
from tests.support.ea_consistency_decision_support_fixtures import _read_json
from tests.support.ea_consistency_decision_support_fixtures import _write_json_file
from tests.support.ea_consistency_decision_support_fixtures import _write_sequence_2_fixture


def test_sequence_4_validation_gate_accepts_current_generated_report_family(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    result = validate_ea_consistency_decision_support_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["passed"] is True
    assert result.summary["reviewer_ready"] is True
    assert result.summary["source_artifact_validation_passed"] is True
    assert result.summary["pdf_header_valid"] is True
    assert result.summary["counts"]["authority_finding_count"] == 1
    assert result.summary["counts"]["non_applicable_authority_count"] == 1


def test_sequence_4_validation_gate_fails_on_stale_manifest_hash(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )
    manifest = _read_json(result.manifest_path)
    manifest["input_hashes"]["compliance_matrix_sha256"] = "stale"
    _write_json_file(result.manifest_path, manifest)

    validation = validate_ea_consistency_decision_support_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert validation.summary["passed"] is False
    assert "input_hash_mismatch" in validation.summary["failure_categories"]


def test_sequence_4_validation_gate_fails_on_invalid_pdf(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )
    result.pdf_path.write_bytes(b"not a pdf\n")

    validation = validate_ea_consistency_decision_support_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert validation.summary["passed"] is False
    assert "invalid_report_pdf_header" in validation.summary["failure_categories"]


def test_sequence_4_validation_gate_fails_on_packet_local_count_drift(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )
    report = _read_json(result.report_path)
    report["applicable_authority_summary"]["applicable_authority_count"] = 99
    _write_json_file(result.report_path, report)

    validation = validate_ea_consistency_decision_support_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert validation.summary["passed"] is False
    assert "count_drift" in validation.summary["failure_categories"]


def test_gap_close_validation_gate_fails_on_missing_markdown_supervisor_context(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )
    markdown = result.markdown_path.read_text(encoding="utf-8").replace(
        "## Review Snapshot",
        "## Review Context",
    )
    result.markdown_path.write_text(markdown, encoding="utf-8")

    validation = validate_ea_consistency_decision_support_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert validation.summary["passed"] is False
    assert "false_negative_synthesis_omission" in validation.summary["failure_categories"]
    assert _failed_check(
        validation.summary,
        "markdown_supervisor_rendering_contract",
    )["source_selector"] == "decision_support_markdown.supervisor_rendering_contract"


def test_gap_close_validation_gate_fails_on_missing_pdf_supervisor_context(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )
    pdf = result.pdf_path.read_bytes().replace(b"Review Snapshot", b"Review Context ")
    result.pdf_path.write_bytes(pdf)

    validation = validate_ea_consistency_decision_support_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert validation.summary["passed"] is False
    assert "false_negative_synthesis_omission" in validation.summary["failure_categories"]
    assert _failed_check(
        validation.summary,
        "pdf_supervisor_rendering_contract",
    )["source_selector"] == "decision_support_pdf.supervisor_rendering_contract"


def test_sequence_4_phase_eval_includes_decision_support_report_phase(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    phase_result = run_phase_aligned_eval(
        output_dir=output_dir,
        source_set_id="source-set-test",
        review_id="review-test",
    )

    phase = _phase(phase_result.summary, "decision_support_report")
    assert phase["passed"] is True
    assert phase["reviewer_ready"] is True
    assert phase["details"]["pdf_header_valid"] is True
    assert phase["details"]["counts"]["authority_finding_count"] == 1
