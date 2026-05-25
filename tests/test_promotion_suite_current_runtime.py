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
