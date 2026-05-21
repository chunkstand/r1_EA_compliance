from __future__ import annotations

from pathlib import Path

from usfs_r1_ea_sources.final_qa_certification import run_final_qa_certification
from usfs_r1_ea_sources.final_qa_certification import validate_final_qa_certification_report

from tests.support.final_qa_certification_fixtures import _read_json
from tests.support.final_qa_certification_fixtures import _sha256
from tests.support.final_qa_certification_fixtures import _write_json_file
from tests.support.final_qa_certification_fixtures import _write_sequence_2_fixture


def test_sequence_2_generator_writes_and_validates_report_family(tmp_path: Path) -> None:
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
    assert result.summary["output_written"] is True
    assert result.report_path.exists()
    assert result.markdown_path.exists()
    assert result.pdf_path.read_bytes().startswith(b"%PDF-")
    assert result.manifest_path.exists()
    assert result.validation_path.exists()
    validation_payload = _read_json(result.validation_path)
    assert validation_payload["output_hashes"]["json_sha256"] == _sha256(result.report_path)
    assert validation_payload["output_hashes"]["markdown_sha256"] == _sha256(
        result.markdown_path
    )
    assert validation_payload["output_hashes"]["pdf_sha256"] == _sha256(result.pdf_path)
    assert validation_payload["output_hashes"]["manifest_sha256"] == _sha256(
        result.manifest_path
    )

    report = _read_json(result.report_path)
    assert report["schema_version"] == "east-crazies-final-qa-certification-report-v1"
    assert report["gate_replay_summary"]["machine_replay_status"] == "passed"
    assert report["applicability_partition"]["non_applicable_authority_count"] == 1
    assert len(report["finding_qa"]["findings"]) == 2
    assert report["finding_qa"]["authority_finding_status_counts"]["pass"] == 2
    assert all(finding["source_pointers"] for finding in report["finding_qa"]["findings"])
    assert report["accepted_v1_risk_ledger"]["accepted_pending_count"] == 2
    assert report["accepted_v1_risk_ledger"]["risks"][0]["hidden_as_pass_finding"] is False
    assert report["certification_statement"]["legal_conclusion"] is False
    assert "does not replace responsible official" in report["certification_statement"]["caveat"]

    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert validation.summary["passed"] is True
    assert validation.summary["output_written"] is False


def test_final_qa_validate_allows_only_outer_gate_self_reference(tmp_path: Path) -> None:
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
    phase_eval["phase_count"] = 3
    phase_eval["passed_phase_count"] = 3
    phase_eval["reviewer_ready_phase_count"] = 3
    phase_eval["phases"] = [
        {"name": "base_1", "passed": True, "reviewer_ready": True},
        {"name": "base_2", "passed": True, "reviewer_ready": True},
        {
            "name": "final_qa_certification_report",
            "passed": True,
            "reviewer_ready": True,
        },
    ]
    _write_json_file(review_dir / "phase_eval_results.json", phase_eval)

    suite_path = (
        output_dir
        / "reviews"
        / "promotion_suite"
        / "post-v1-region1-ea-promotion-suite"
        / "promotion_suite_results.json"
    )
    suite = _read_json(suite_path)
    suite["required_current_result_count"] = 6
    suite["passed_required_current_result_count"] = 5
    suite["current_promotion_ready"] = False
    suite["review_cases"] = [
        {
            "id": "v1-cg-ecid",
            "results": [
                {
                    "id": result_id,
                    "required_for_current_promotion": True,
                    "passed": result_id != "final_qa_certification_report",
                }
                for result_id in [
                    "final_qa_certification_report",
                    "final_qa_certification_manifest",
                    "final_qa_certification_pdf",
                    "final_qa_certification_validation",
                ]
            ],
        }
    ]
    _write_json_file(suite_path, suite)

    regenerated = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )

    assert regenerated.summary["passed"] is True
    validation = validate_final_qa_certification_report(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert validation.summary["passed"] is True

    regenerated = run_final_qa_certification(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
        results_dir=results_dir,
    )
    assert regenerated.summary["passed"] is True
    report = _read_json(regenerated.report_path)
    phase_summary = report["gate_replay_summary"]["phase_eval"]
    promotion_summary = report["gate_replay_summary"]["current_promotion_suite"]
    assert phase_summary["phase_count"] == 2
    assert phase_summary["passed_phase_count"] == 2
    assert phase_summary["live_phase_count"] == 3
    assert phase_summary["live_passed_phase_count"] == 3
    assert phase_summary["final_qa_self_reference_phase_count"] == 1
    assert promotion_summary["required_current_result_count"] == 2
    assert promotion_summary["passed_required_current_result_count"] == 2
    assert promotion_summary["live_required_current_result_count"] == 6
    assert promotion_summary["live_passed_required_current_result_count"] == 5
    assert promotion_summary["final_qa_current_result_count"] == 4
    assert promotion_summary["final_qa_current_passed_result_count"] == 3
    markdown = regenerated.markdown_path.read_text(encoding="utf-8")
    assert "Phase eval baseline excluding final QA self-reference: `2/2`" in markdown
    assert "Phase eval live gate: `3/3`" in markdown
    assert (
        "Current promotion suite baseline excluding final QA packet gates: `2/2`"
        in markdown
    )
    assert "Current promotion suite live gate: `5/6`" in markdown
