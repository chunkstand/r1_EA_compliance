from __future__ import annotations

from pathlib import Path
import json

from tests.support.promotion_suite_fixtures import write_json
from tests.support.promotion_suite_fixtures import write_suite_fixture
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


def test_promotion_suite_current_contract_ignores_review_case_order(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"].insert(
        0,
        {
            "id": "case-0",
            "review_id": "review-stale",
            "results": [
                {
                    "id": "v1_ea_eval",
                    "path": "reviews/{review_id}/v1_ea_eval_results.json",
                    "failure_category": "stale_artifact",
                    "checks": [
                        {
                            "name": "v1_passed",
                            "json_path": "summary.passed",
                            "equals": True,
                        }
                    ],
                }
            ],
        },
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_json(
        output_dir / "reviews" / "review-stale" / "v1_ea_eval_results.json",
        {"summary": {"passed": False}},
    )

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)
    current_contract = result.summary["current_promotion_contract"]

    assert result.summary["current_promotion_ready"] is True
    assert current_contract["eligible_slot_count"] == 1
    assert current_contract["passing_slot_count"] == 1
    assert current_contract["governed_slots"][0]["review_id"] == "review-1"


def test_promotion_suite_reports_reference_canary_separately_from_current_contract(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"].append(
        {
            "id": "case-2",
            "review_id": "review-canary",
            "results": [
                {
                    "id": "v1_ea_eval",
                    "path": "reviews/{review_id}/v1_ea_eval_results.json",
                    "failure_category": "stale_artifact",
                    "checks": [
                        {
                            "name": "v1_passed",
                            "json_path": "summary.passed",
                            "equals": True,
                        }
                    ],
                }
            ],
        }
    )
    manifest["current_promotion_contract"]["reference_canaries"] = [
        {
            "id": "case-2-canary",
            "review_case_id": "case-2",
            "required": True,
        }
    ]
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_json(
        output_dir / "reviews" / "review-canary" / "v1_ea_eval_results.json",
        {"summary": {"passed": False}},
    )

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)
    current_contract = result.summary["current_promotion_contract"]

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["failure_category_counts"] == {}
    assert result.summary["reference_canary_failure_category_counts"] == {
        "stale_artifact": 1
    }
    assert current_contract["reference_canary_ready"] is False
    assert current_contract["reference_canaries"][0]["review_id"] == "review-canary"


def test_promotion_suite_current_contract_fails_source_set_bound_slot_family(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    coverage_results_path = (
        output_dir
        / "reviews"
        / "real_package_review_coverage_eval"
        / "real_package_review_coverage_eval_results.json"
    )
    coverage_results = json.loads(coverage_results_path.read_text(encoding="utf-8"))
    coverage_results["slots"][0]["source_set_id"] = "source-set-other"
    coverage_results_path.write_text(
        json.dumps(coverage_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)
    current_contract = result.summary["current_promotion_contract"]
    review_family = next(
        family
        for family in current_contract["family_results"]
        if family["family_scope"] == "review_slot"
    )

    assert result.summary["current_promotion_ready"] is False
    assert result.summary["failure_category_counts"] == {"stale_artifact": 1}
    assert current_contract["eligible_slot_count"] == 1
    assert current_contract["passing_slot_count"] == 0
    assert current_contract["governed_slots"][0]["source_set_matches_current_promotion"] is False
    assert review_family["failure_categories"] == ["stale_artifact"]
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "## Current Promotion Contract" in markdown


def test_promotion_suite_fails_current_promotion_on_ratcheted_eval_trace_gate(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    phase_eval_path = (
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json"
    )
    phase_eval = json.loads(phase_eval_path.read_text(encoding="utf-8"))
    phase_eval["eval_trace_gate"] = {
        "schema_version": "eval-trace-gate-status-v1",
        "mode": "ratcheted",
        "ratchet_scope_enabled": True,
        "passed": False,
        "failure_reasons": ["eval_trace_store_missing_trace_rows"],
    }
    phase_eval_path.write_text(json.dumps(phase_eval, indent=2, sort_keys=True) + "\n")

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)

    assert result.summary["current_promotion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert result.summary["failure_category_counts"] == {"eval_trace_gate_failed": 1}
    gate_summary = result.summary["eval_trace_gate_summary"]
    assert gate_summary["reported_gate_count"] == 2
    assert gate_summary["ratcheted_gate_count"] == 2
    assert gate_summary["failed_current_gate_count"] == 1
    assert gate_summary["failed_current_gates"][0]["id"] == "phase_eval_core"
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "## Eval Trace Gate" in markdown


def test_promotion_suite_current_contract_fails_when_review_slot_family_is_split_across_slots(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    review_slot_family = manifest["current_promotion_contract"]["artifact_families"][1]
    review_slot_family["review_result_ids"] = ["v1_ea_eval", "matrix_pdf"]
    manifest["review_cases"][0]["results"] = [
        {
            "id": "v1_ea_eval",
            "path": "reviews/{review_id}/v1_ea_eval_results.json",
            "failure_category": "stale_artifact",
            "checks": [
                {
                    "name": "v1_passed",
                    "json_path": "summary.passed",
                    "equals": True,
                }
            ],
        }
    ]
    manifest["review_cases"].append(
        {
            "id": "case-2",
            "review_id": "review-2",
            "results": [
                {
                    "id": "matrix_pdf",
                    "path": "reviews/{review_id}/compliance_matrix.pdf",
                    "format": "binary",
                    "failure_category": "stale_artifact",
                    "checks": [
                        {
                            "name": "pdf_header",
                            "starts_with": "%PDF-",
                        }
                    ],
                }
            ],
        }
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    coverage_results_path = (
        output_dir
        / "reviews"
        / "real_package_review_coverage_eval"
        / "real_package_review_coverage_eval_results.json"
    )
    coverage_results = json.loads(coverage_results_path.read_text(encoding="utf-8"))
    coverage_results["slots"].append(
        {
            "slot_id": "fixture-current-promotion-slot-2",
            "label": "Fixture current promotion slot 2",
            "review_id": "review-2",
            "package_label": "Fixture package 2",
            "coverage_class_id": "current_promotion_reviewer_ready",
            "required": True,
            "contract_status": "reviewer_ready",
            "actual_contract_status": "reviewer_ready",
            "passed": True,
            "source_set_id": "source-set-1",
            "summary_path": "reviews/review-2/compliance_matrix.pdf",
            "failure_category_counts": {},
            "forest_plan_failure_category_counts": {},
            "package_authority": {
                "passed": True,
                "failure_reasons": [],
                "mode": "replay_context",
            },
        }
    )
    coverage_results_path.write_text(
        json.dumps(coverage_results, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "reviews" / "review-2").mkdir(parents=True, exist_ok=True)
    (output_dir / "reviews" / "review-2" / "compliance_matrix.pdf").write_bytes(b"%PDF-1.4\n")

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)
    current_contract = result.summary["current_promotion_contract"]
    review_family = next(
        family
        for family in current_contract["family_results"]
        if family["family_scope"] == "review_slot"
    )
    slot_results = {row["review_id"]: row for row in review_family["slot_results"]}

    assert result.summary["current_promotion_ready"] is False
    assert result.summary["failure_category_counts"] == {"unsupported_package_evidence": 1}
    assert current_contract["eligible_slot_count"] == 2
    assert current_contract["passing_slot_count"] == 0
    assert review_family["passed"] is False
    assert slot_results["review-1"]["missing_result_ids"] == ["matrix_pdf"]
    assert slot_results["review-2"]["missing_result_ids"] == ["v1_ea_eval"]
