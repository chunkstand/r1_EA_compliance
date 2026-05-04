from __future__ import annotations

from pathlib import Path
import json

from usfs_r1_ea_sources.promotion_suite import PROMOTION_SUITE_SCHEMA_VERSION
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_PROMOTION_SUITE = REPO_ROOT / "config" / "promotion_suite_v1.json"


def test_committed_promotion_suite_requires_milestone_4_applicability_gates() -> None:
    manifest = json.loads(COMMITTED_PROMOTION_SUITE.read_text(encoding="utf-8"))
    suite_results = {result["id"]: result for result in manifest["suite_results"]}

    seed_gate = suite_results["applicability_eval_authority_family_coverage"]
    assert seed_gate["required_for_current_promotion"] is True
    assert seed_gate["path"] == "reviews/applicability_eval/applicability_eval_results.json"
    seed_checks = {check["name"]: check for check in seed_gate["checks"]}
    assert seed_checks["applicability_eval_passed"]["equals"] is True
    assert seed_checks["applicability_eval_case_count"]["min"] == 5
    assert seed_checks["authority_family_high_priority_count"]["equals"] == 19
    assert seed_checks["authority_family_positive_coverage"]["equals"] == 19
    assert seed_checks["authority_family_negative_coverage"]["equals"] == 19
    assert seed_checks["authority_family_unresolved_coverage"]["min"] == 1
    assert seed_checks["authority_family_real_package_tags"]["equals"] is True

    gold_gate = suite_results["applicability_gold_eval_authority_family_adjudication"]
    assert gold_gate["required_for_current_promotion"] is True
    assert gold_gate["path"] == "reviews/applicability_gold_eval/applicability_gold_eval_results.json"
    gold_checks = {check["name"]: check for check in gold_gate["checks"]}
    assert gold_checks["applicability_gold_eval_passed"]["equals"] is True
    assert gold_checks["applicability_gold_eval_promotion_ready"]["equals"] is True
    assert gold_checks["applicability_gold_eval_case_count"]["min"] == 5
    assert gold_checks["applicability_gold_eval_unresolved_profile"]["min"] == 1
    assert gold_checks["applicability_gold_eval_adjudicated_profile"]["min"] == 1
    assert gold_checks["authority_family_adjudicated_coverage"]["min"] == 1


def test_promotion_suite_reports_current_ready_and_expansion_gap(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)

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
    manifest_path, output_dir = _write_suite_fixture(tmp_path)

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


def test_promotion_suite_fails_missing_required_artifact(tmp_path: Path) -> None:
    manifest_path, output_dir = _write_suite_fixture(tmp_path)
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


def _write_suite_fixture(tmp_path: Path) -> tuple[Path, Path]:
    output_dir = tmp_path / "source_library"
    manifest_path = tmp_path / "promotion_suite.json"
    _write_json(
        tmp_path / "rule_pack.json",
        {
            "rule_pack_id": "rules-v0",
            "version": "1.0.0",
            "baseline_source_record_ids": ["R1EA-001", "R1EA-002"],
            "rules": [{"id": "rule-1"}, {"id": "rule-2"}],
        },
    )
    _write_json(
        manifest_path,
        {
            "schema_version": PROMOTION_SUITE_SCHEMA_VERSION,
            "id": "suite-1",
            "source_set_id": "source-set-1",
            "rule_pack_path": "rule_pack.json",
            "rule_pack_id": "rules-v0",
            "rule_pack_version": "1.0.0",
            "expected_rule_count": 2,
            "expected_baseline_source_record_count": 2,
            "review_cases": [
                {
                    "id": "case-1",
                    "review_id": "review-1",
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
                        },
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
                        },
                    ],
                }
            ],
            "suite_results": [
                {
                    "id": "phase_eval_core",
                    "path": "derived/{source_set_id}/evidence_graph/phase_eval_results.json",
                    "failure_category": "stale_artifact",
                    "checks": [
                        {
                            "name": "phase_count",
                            "json_path": "passed_phase_count",
                            "min": 2,
                        }
                    ],
                },
                {
                    "id": "post_v1_applicability_phase",
                    "path": "derived/{source_set_id}/evidence_graph/phase_eval_results.json",
                    "required_for_current_promotion": False,
                    "required_for_expansion": True,
                    "failure_category": "applicability_miss",
                    "checks": [
                        {
                            "name": "phase_ready_with_applicability",
                            "json_path": "reviewer_ready",
                            "equals": True,
                        }
                    ],
                },
            ],
            "expansion_slots": [
                {
                    "id": "slot-1",
                    "ready": False,
                    "failure_category": "package_fixture_missing",
                }
            ],
        },
    )
    _write_json(
        output_dir / "reviews" / "review-1" / "v1_ea_eval_results.json",
        {"summary": {"passed": True}},
    )
    (output_dir / "reviews" / "review-1").mkdir(parents=True, exist_ok=True)
    (output_dir / "reviews" / "review-1" / "compliance_matrix.pdf").write_bytes(
        b"%PDF-1.4\n"
    )
    _write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": False},
    )
    return manifest_path, output_dir


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
