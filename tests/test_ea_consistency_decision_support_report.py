from __future__ import annotations

from pathlib import Path
import hashlib
import json

from usfs_r1_ea_sources.ea_consistency_decision_support import (
    run_ea_consistency_decision_support,
)

from tests.support.ea_consistency_decision_support_fixtures import _assert_evidence
from tests.support.ea_consistency_decision_support_fixtures import _assert_traceable_row
from tests.support.ea_consistency_decision_support_fixtures import _read_json
from tests.support.ea_consistency_decision_support_fixtures import _write_sequence_2_fixture


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_sequence_2_generator_writes_canonical_report_family(tmp_path: Path) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)

    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["passed"] is True
    assert result.summary["output_written"] is True
    assert result.report_path.exists()
    assert result.markdown_path.exists()
    assert result.pdf_path.read_bytes().startswith(b"%PDF-")
    assert result.manifest_path.exists()

    report = _read_json(result.report_path)
    assert report["schema_version"] == "ea-consistency-decision-support-report-v1"
    assert report["manifest"]["schema_version"] == "ea-consistency-decision-support-manifest-v1"
    assert report["executive_determination"]["legal_conclusion"] is False
    assert report["applicable_authority_summary"]["applicable_authority_count"] == 1
    assert len(report["authority_findings"]) == 1
    assert len(report["non_applicable_authority_boundary"]["summary_rows"]) == 1
    assert len(report["forest_plan_consistency"]["component_rows"]) == 1
    assert len(report["applicable_forest_plan_standards"]) == 1
    assert report["implementation_confirmation_checklist"][0]["status"] == (
        "requires_confirmation"
    )
    assert report["residual_risk_register"][0]["legal_conclusion"] is False

    authority = report["authority_findings"][0]
    _assert_evidence(authority["ea_package_evidence"][0])
    _assert_evidence(authority["source_library_evidence"][0])
    _assert_traceable_row(authority)

    non_applicable = report["non_applicable_authority_boundary"]["summary_rows"][0]
    assert non_applicable["status"] == "not_applicable"
    assert non_applicable["search_coverage"][0]["coverage_result"] == "sufficient"
    _assert_traceable_row(non_applicable)


def test_sequence_2_generator_uses_source_claim_link_fallback_when_matrix_row_lacks_source_evidence(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    review_dir = output_dir / "reviews" / "review-test"

    matrix = _read_json(review_dir / "compliance_matrix.json")
    matrix["rows"][0].pop("source_library_evidence", None)
    _write_json(review_dir / "compliance_matrix.json", matrix)

    review = _read_json(review_dir / "compliance_review.json")
    review["findings"] = [
        {
            "rule_id": "sample_authority",
            "source_claim_links": [
                {
                    "artifact_path": "source.html",
                    "artifact_sha256": "sha256-source-artifact",
                    "chunk_id": "chunk:source-claim",
                    "citation_label": "R1EA-TEST-CLAIM (test)",
                    "claim_text": "Synthetic claim evidence excerpt.",
                    "content_sha256": "sha256-source-content",
                    "document_role": "executive_order",
                    "parser_name": "parser",
                    "parser_version": "1.0",
                    "source_char_end": 33,
                    "source_char_start": 0,
                    "source_record_id": "R1EA-TEST",
                }
            ],
        }
    ]
    _write_json(review_dir / "compliance_review.json", review)

    expected = _read_json(expected_path)
    expected["input_hashes"]["compliance_matrix_sha256"] = _sha256(
        review_dir / "compliance_matrix.json"
    )
    expected["input_hashes"]["compliance_review_sha256"] = _sha256(
        review_dir / "compliance_review.json"
    )
    _write_json(expected_path, expected)

    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["passed"] is True
    report = _read_json(result.report_path)
    authority = report["authority_findings"][0]
    _assert_evidence(authority["source_library_evidence"][0])
    assert authority["source_library_evidence"][0]["citation_label"] == "R1EA-TEST-CLAIM (test)"


def test_sequence_5_rendering_frontloads_supervisor_review_context(tmp_path: Path) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)

    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "## How To Use This Document" in markdown
    assert "does not replace responsible official, line officer, counsel" in markdown
    assert "## Review Snapshot" in markdown
    assert markdown.index("## Review Snapshot") < markdown.index("## Authority Findings")
    assert "Bottom-line determination: reviewer_ready decision-support status" in markdown
    assert "Authority categories: executive_order=1" in markdown
    assert "Forest Plan basis: EA-PACKAGE-042 Plan Consistency Table" in markdown
    assert "Applicable standards: 1 of 1 applicable Forest Plan standards" in markdown
    assert "Non-applicable boundary: 1 authorities remain non-applicable" in markdown
    assert "Implementation confirmations: 1 evidence-linked checklist rows" in markdown
    assert "Residual risks: 3 deterministic decision-support notes; 0 legal-conclusion flags." in markdown
    assert "Summary: generated applicable authority findings with package and source citations" in markdown
    assert "Summary: non-applicable authorities stay out of compliance findings" in markdown
    assert (
        "| Rule | Category | Status | EA evidence | Source evidence | Implementation confirmations |"
        in markdown
    )
    assert "| Confirmation | Status | Decision-support wording | Evidence selectors |" in markdown
    assert "source_library/reviews/review-test/compliance_matrix.json :: rule_id=sample_authority" in markdown
    assert "Source: `" in markdown
    assert "litigation_risk_summary.json" in markdown

    pdf_text = result.pdf_path.read_bytes().decode("latin-1", errors="ignore")
    assert "How To Use This Document" in pdf_text
    assert "Review Snapshot" in pdf_text
    assert "Table Summaries" in pdf_text
    assert "Non-Applicable Authority Boundary" in pdf_text
    assert "Implementation Confirmations" in pdf_text
    assert "Residual Risks" in pdf_text


def test_sequence_2_generator_fails_closed_on_missing_required_artifact(
    tmp_path: Path,
) -> None:
    output_dir, config_path, expected_path = _write_sequence_2_fixture(tmp_path)
    (
        output_dir
        / "reviews"
        / "review-test"
        / "applicability"
        / "non_applicable_authorities.json"
    ).unlink()

    result = run_ea_consistency_decision_support(
        output_dir=output_dir,
        review_id="review-test",
        config_path=config_path,
        expected_summary_path=expected_path,
    )

    assert result.summary["passed"] is False
    assert "missing_required_artifact" in result.summary["failure_categories"]
    assert result.summary["output_written"] is False
    assert not result.report_path.exists()
