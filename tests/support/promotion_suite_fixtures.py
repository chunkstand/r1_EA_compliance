from __future__ import annotations

from pathlib import Path
import hashlib
import json

from usfs_r1_ea_sources.promotion_suite import PROMOTION_SUITE_SCHEMA_VERSION


REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_PROMOTION_SUITE = REPO_ROOT / "config" / "promotion_suite_v1.json"
FULL_CANONICAL_SOURCE_SET_ID = "source-set-4fb59e9eb43045cb"
FULL_CANONICAL_DOWNLOAD_RUN_ID = "queue-m3-full-canonical-merged-download-20260523"


def write_suite_fixture(tmp_path: Path) -> tuple[Path, Path]:
    output_dir = tmp_path / "source_library"
    manifest_path = tmp_path / "promotion_suite.json"
    write_json(
        tmp_path / "rule_pack.json",
        {
            "rule_pack_id": "rules-v0",
            "version": "1.0.0",
            "baseline_source_record_ids": ["R1EA-001", "R1EA-002"],
            "rules": [{"id": "rule-1"}, {"id": "rule-2"}],
        },
    )
    write_json(
        tmp_path / "config" / "review_coverage.json",
        {
            "schema_version": "real-package-review-coverage-v1",
            "id": "fixture-review-coverage",
            "required_coverage_class_ids": ["current_promotion_reviewer_ready"],
            "slots": [],
            "coverage_thresholds": {},
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
            "expected_rule_count": 2,
            "expected_baseline_source_record_count": 2,
            "current_promotion_contract": {
                "require_rule_pack_result": True,
                "slot_selector": {
                    "selector_type": "governed_coverage_class",
                    "coverage_manifest_path": "config/review_coverage.json",
                    "coverage_results_path": "reviews/real_package_review_coverage_eval/real_package_review_coverage_eval_results.json",
                    "coverage_class_ids": ["current_promotion_reviewer_ready"],
                    "allowed_contract_statuses": ["reviewer_ready"],
                },
                "quorum": {
                    "eligible_slot_count_min": 1,
                    "passing_slot_count_min": 1,
                },
                "artifact_families": [
                    {
                        "id": "suite-baseline",
                        "family_scope": "suite",
                        "suite_result_ids": ["phase_eval_core"],
                    },
                    {
                        "id": "review-slot-artifacts",
                        "family_scope": "review_slot",
                        "review_result_ids": ["v1_ea_eval", "matrix_pdf"],
                        "slot_binding": "same_slot",
                        "source_set_binding": "current_promotion_source_set",
                        "passing_slot_count_min": 1,
                    },
                ],
                "reference_canaries": [
                    {
                        "id": "case-1-canary",
                        "review_case_id": "case-1",
                        "required": True,
                    }
                ],
            },
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
    write_json(
        output_dir / "reviews" / "review-1" / "v1_ea_eval_results.json",
        {"source_set_id": "source-set-1", "summary": {"passed": True}},
    )
    write_json(
        output_dir
        / "reviews"
        / "real_package_review_coverage_eval"
        / "real_package_review_coverage_eval_results.json",
        {
            "schema_version": "real-package-review-coverage-results-v1",
            "passed": True,
            "slots": [
                {
                    "slot_id": "fixture-current-promotion-slot",
                    "label": "Fixture current promotion slot",
                    "review_id": "review-1",
                    "package_label": "Fixture package",
                    "coverage_class_id": "current_promotion_reviewer_ready",
                    "required": True,
                    "contract_status": "reviewer_ready",
                    "actual_contract_status": "reviewer_ready",
                    "passed": True,
                    "source_set_id": "source-set-1",
                    "summary_path": "reviews/review-1/v1_ea_eval_results.json",
                    "failure_category_counts": {},
                    "forest_plan_failure_category_counts": {},
                    "package_authority": {
                        "passed": True,
                        "failure_reasons": [],
                        "mode": "replay_context",
                    },
                }
            ],
        },
    )
    (output_dir / "reviews" / "review-1").mkdir(parents=True, exist_ok=True)
    (output_dir / "reviews" / "review-1" / "compliance_matrix.pdf").write_bytes(
        b"%PDF-1.4\n"
    )
    write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": False},
    )
    return manifest_path, output_dir


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()
