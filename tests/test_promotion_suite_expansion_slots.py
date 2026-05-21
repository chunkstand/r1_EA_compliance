from __future__ import annotations

from pathlib import Path
import json

import pytest

from tests.support.promotion_suite_fixtures import sha256_bytes
from tests.support.promotion_suite_fixtures import write_json
from tests.support.promotion_suite_fixtures import write_suite_fixture
from usfs_r1_ea_sources.promotion_suite import PROMOTION_SUITE_SCHEMA_VERSION
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


def test_promotion_suite_reports_current_ready_and_expansion_gap(tmp_path: Path) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is True
    assert result.summary["failure_category_counts"] == {}
    assert result.summary["expansion_failure_category_counts"] == {
        "applicability_miss": 1,
        "package_fixture_missing": 1,
    }
    assert result.summary["open_expansion_slot_count"] == 1
    assert result.output_path.exists()
    assert result.markdown_path.exists()


def test_promotion_suite_strict_expansion_blocks_promotion(tmp_path: Path) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
        strict_expansion=True,
    )

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert result.summary["failure_category_counts"] == {
        "applicability_miss": 1,
        "package_fixture_missing": 1,
    }
    assert result.summary["expansion_failure_category_counts"] == {
        "applicability_miss": 1,
        "package_fixture_missing": 1,
    }


def test_promotion_suite_fails_stale_validation_sidecar_file_hash(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "source_library"
    manifest_path = tmp_path / "promotion_suite.json"
    write_json(
        tmp_path / "rule_pack.json",
        {
            "rule_pack_id": "rules-v0",
            "version": "1.0.0",
            "baseline_source_record_ids": ["R1EA-001"],
            "rules": [{"id": "rule-1"}],
        },
    )
    report_path = (
        output_dir / "reviews" / "review-1" / "final_qa" / "final_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("first version\n", encoding="utf-8")
    validation_path = report_path.parent / "validation.json"
    write_json(
        validation_path,
        {
            "passed": True,
            "output_files": {"json": "source_library/reviews/review-1/final_qa/final_report.json"},
            "output_hashes": {"json_sha256": sha256_bytes(b"different version\n")},
        },
    )
    write_json(
        manifest_path,
        {
            "schema_version": PROMOTION_SUITE_SCHEMA_VERSION,
            "id": "suite-1",
            "source_set_id": "source-set-1",
            "rule_pack_path": "rule_pack.json",
            "rule_pack_id": "rules-v0",
            "rule_pack_version": "1.0.0",
            "expected_rule_count": 1,
            "expected_baseline_source_record_count": 1,
            "review_cases": [
                {
                    "id": "case-1",
                    "review_id": "review-1",
                    "results": [
                        {
                            "id": "final_qa_certification_validation",
                            "path": "reviews/{review_id}/final_qa/validation.json",
                            "failure_category": "stale_artifact",
                            "checks": [
                                {
                                    "name": "final_qa_validation_passed",
                                    "json_path": "passed",
                                    "equals": True,
                                },
                                {
                                    "name": "final_qa_validation_report_hash_matches_file",
                                    "file_sha256_matches": {
                                        "path_json_path": "output_files.json",
                                        "sha256_json_path": "output_hashes.json_sha256",
                                    },
                                },
                            ],
                        }
                    ],
                }
            ],
            "suite_results": [],
            "expansion_slots": [],
        },
    )

    result = run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)

    assert result.summary["current_promotion_ready"] is False
    failed_result = result.summary["review_cases"][0]["results"][0]
    failed_check = next(
        check
        for check in failed_result["checks"]
        if check["name"] == "final_qa_validation_report_hash_matches_file"
    )
    assert failed_check["passed"] is False
    assert failed_check["failure_category"] == "stale_artifact"


def test_promotion_suite_reports_selected_not_ready_slot_metadata(tmp_path: Path) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "label": "Selected package fixture",
        "status": "selected_not_run",
        "ready": False,
        "failure_category": "applicability_miss",
        "review_id": "selected-review",
        "package_path": "source_library/reviews/_intake/selected-review",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "package_manifest",
                "path": "reviews/{review_id}/package/package_manifest.jsonl",
            }
        ],
        "next_action": "Run package context and applicability gates.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": True},
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )
    slot = result.summary["expansion_slots"][0]

    assert result.summary["expansion_failure_category_counts"] == {"applicability_miss": 1}
    assert result.summary["open_expansion_slot_count"] == 1
    assert slot["failure_categories"] == ["applicability_miss"]
    assert slot["review_id"] == "selected-review"
    assert slot["package_path"] == "source_library/reviews/_intake/selected-review"
    assert slot["source_set_id"] == "source-set-1"
    assert slot["expected_gate_artifacts"][0]["id"] == "package_manifest"
    markdown = result.markdown_path.read_text(encoding="utf-8")
    assert "selected-review" in markdown
    assert "source_library/reviews/_intake/selected-review" in markdown
    assert "applicability_miss" in markdown


def test_promotion_suite_rejects_selected_slot_missing_contract_fields(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "selected_not_run",
        "ready": False,
        "failure_category": "applicability_miss",
        "review_id": "selected-review",
        "package_path": "source_library/reviews/_intake/selected-review",
        "next_action": "Run package context and applicability gates.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="source_set_id"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_rejects_selected_slot_package_fixture_missing(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "selected_not_run",
        "ready": False,
        "failure_category": "package_fixture_missing",
        "review_id": "selected-review",
        "package_path": "source_library/reviews/_intake/selected-review",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "package_manifest",
                "path": "reviews/{review_id}/package/package_manifest.jsonl",
            }
        ],
        "next_action": "Run package context and applicability gates.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="typed failure_category"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_rejects_ready_slot_with_failure_category(tmp_path: Path) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["expansion_slots"][0]["ready"] = True
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="ready but still has failure_category"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_rejects_ready_slot_missing_review_gate_contract(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].append(
        {
            "id": "expansion_review",
            "path": "reviews/{review_id}/expansion_review.json",
            "required_for_current_promotion": False,
            "required_for_expansion": True,
            "failure_category": "applicability_miss",
            "checks": [
                {
                    "name": "expansion_review_passed",
                    "json_path": "summary.passed",
                    "equals": True,
                }
            ],
        }
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "package_manifest",
                "path": "reviews/{review_id}/package/package_manifest.jsonl",
            }
        ],
        "next_action": "Keep the slot ready.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="expansion_review"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)

def test_promotion_suite_expansion_requires_required_expansion_artifacts(tmp_path: Path) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].append(
        {
            "id": "expansion_review",
            "path": "reviews/{review_id}/expansion_review.json",
            "required_for_current_promotion": False,
            "required_for_expansion": True,
            "failure_category": "applicability_miss",
            "checks": [
                {
                    "name": "expansion_review_passed",
                    "json_path": "summary.passed",
                    "equals": True,
                }
            ],
        }
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "expected_gate_artifacts": [
            {
                "id": "expansion_review",
                "path": "reviews/{review_id}/expansion_review.json",
            }
        ],
        "next_action": "Keep the slot ready.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_json(
        output_dir / "reviews" / "review-1" / "expansion_review.json",
        {"summary": {"passed": True}},
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["expansion_artifacts_ready"] is False
    assert result.summary["promotion_ready"] is True
    assert result.summary["failure_category_counts"] == {}
    assert result.summary["expansion_failure_category_counts"] == {
        "applicability_miss": 1,
    }
    assert result.summary["open_expansion_slot_count"] == 0
    assert result.summary["open_expansion_artifact_count"] == 1


def test_promotion_suite_fails_missing_required_artifact(tmp_path: Path) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    (output_dir / "reviews" / "review-1" / "v1_ea_eval_results.json").unlink()

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
    )

    assert result.summary["current_promotion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert result.summary["failure_category_counts"]["stale_artifact"] == 1
    review_case = result.summary["review_cases"][0]
    missing_result = next(item for item in review_case["results"] if item["id"] == "v1_ea_eval")
    assert missing_result["checks"][0]["name"] == "artifact_exists"
    assert missing_result["checks"][0]["passed"] is False
