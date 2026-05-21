from __future__ import annotations

from pathlib import Path
import json

import pytest

from tests.support.promotion_suite_fixtures import write_json
from tests.support.promotion_suite_fixtures import write_suite_fixture
from usfs_r1_ea_sources.promotion_suite import run_promotion_suite


def test_promotion_suite_blocks_declared_forest_profile_false_pass(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].extend(
        [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "compliance_review_reviewer_ready",
                        "json_path": "summary.reviewer_ready",
                        "equals": True,
                    },
                    {
                        "name": "forest_plan_scope_status_matches_declared_profile",
                        "json_path": "summary.forest_plan_review.scope_status",
                        "equals": "custer_gallatin",
                        "failure_category": "forest_plan_reviewer_not_ready",
                    },
                ],
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_context_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "phase_eval_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
        ]
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "forest_plan_profile": "custer_gallatin",
        "expected_gate_artifacts": [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
            },
        ],
        "last_local_signal": {
            "forest_plan_scope_status": "ambiguous",
            "forest_plan_component_gate_required": False,
        },
        "next_action": "Resolve the declared forest-plan context.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": True},
    )
    write_json(
        output_dir / "reviews" / "review-1" / "compliance_review.json",
        {
            "summary": {
                "reviewer_ready": True,
                "forest_plan_review": {
                    "scope_status": "ambiguous",
                    "validation_passed": False,
                    "reviewer_ready": False,
                    "needs_reviewer_resolution": True,
                },
            }
        },
    )
    write_json(
        output_dir / "reviews" / "review-1" / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "scope_status": "ambiguous",
            "validation_passed": False,
            "reviewer_ready": False,
            "needs_reviewer_resolution": True,
        },
    )
    write_json(
        output_dir / "reviews" / "review-1" / "phase_eval_results.json",
        {
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "passed": True,
            "reviewer_ready": True,
            "passed_phase_count": 2,
            "phase_count": 2,
            "phases": [
                {"name": "applicability_validation", "passed": True, "reviewer_ready": True},
                {"name": "compliance_review", "passed": True, "reviewer_ready": True},
            ],
        },
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
        strict_expansion=True,
    )
    slot = result.summary["expansion_slots"][0]

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert set(result.summary["failure_category_counts"]) == {
        "forest_plan_reviewer_not_ready"
    }
    assert slot["manifest_ready"] is True
    assert slot["ready"] is False
    assert slot["failure_categories"] == ["forest_plan_reviewer_not_ready"]
    profile_checks = {
        check["name"]: check for check in slot["forest_plan_profile_checks"]
    }
    assert profile_checks["forest_plan_scope_status_matches_declared_profile"][
        "actual"
    ] == "ambiguous"
    assert profile_checks["forest_plan_reviewer_ready"]["passed"] is False


def test_promotion_suite_rejects_forest_profile_slot_missing_gate_artifact(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].extend(
        [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_reviewer_ready",
                        "json_path": "summary.forest_plan_review.reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_context_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "phase_eval_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
        ]
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "blocked_forest_plan_review",
        "ready": False,
        "failure_category": "forest_plan_reviewer_not_ready",
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "forest_plan_profile": "custer_gallatin",
        "expected_gate_artifacts": [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
            },
        ],
        "next_action": "Resolve the declared forest-plan context.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    with pytest.raises(ValueError, match="forest_plan_context_summary"):
        run_promotion_suite(output_dir=output_dir, manifest_path=manifest_path)


def test_promotion_suite_blocks_missing_required_forest_component_phase(
    tmp_path: Path,
) -> None:
    manifest_path, output_dir = write_suite_fixture(tmp_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["review_cases"][0]["results"].extend(
        [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_reviewer_ready",
                        "json_path": "summary.forest_plan_review.reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "forest_plan_context_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
                "required_for_current_promotion": False,
                "required_for_expansion": True,
                "failure_category": "forest_plan_reviewer_not_ready",
                "checks": [
                    {
                        "name": "phase_eval_reviewer_ready",
                        "json_path": "reviewer_ready",
                        "equals": True,
                    }
                ],
            },
        ]
    )
    manifest["expansion_slots"][0] = {
        "id": "slot-1",
        "status": "ready",
        "ready": True,
        "review_id": "review-1",
        "package_path": "source_library/reviews/_intake/review-1",
        "source_set_id": "source-set-1",
        "forest_plan_profile": "custer_gallatin",
        "expected_gate_artifacts": [
            {
                "id": "compliance_review",
                "path": "reviews/{review_id}/compliance_review.json",
            },
            {
                "id": "forest_plan_context_summary",
                "path": "reviews/{review_id}/forest_plan_context_summary.json",
            },
            {
                "id": "phase_eval",
                "path": "reviews/{review_id}/phase_eval_results.json",
            },
        ],
        "last_local_signal": {
            "forest_plan_scope_status": "custer_gallatin",
            "forest_plan_component_gate_required": True,
        },
        "next_action": "Run Forest Plan component evaluation.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    write_json(
        output_dir / "derived" / "source-set-1" / "evidence_graph" / "phase_eval_results.json",
        {"source_set_id": "source-set-1", "passed_phase_count": 2, "reviewer_ready": True},
    )
    write_json(
        output_dir / "reviews" / "review-1" / "compliance_review.json",
        {
            "summary": {
                "reviewer_ready": True,
                "forest_plan_review": {
                    "scope_status": "custer_gallatin",
                    "validation_passed": True,
                    "reviewer_ready": True,
                },
            }
        },
    )
    write_json(
        output_dir / "reviews" / "review-1" / "forest_plan_context_summary.json",
        {
            "schema_version": "forest-plan-context-summary-v0",
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "scope_status": "custer_gallatin",
            "validation_passed": True,
            "reviewer_ready": True,
        },
    )
    write_json(
        output_dir / "reviews" / "review-1" / "phase_eval_results.json",
        {
            "review_id": "review-1",
            "source_set_id": "source-set-1",
            "passed": True,
            "reviewer_ready": True,
            "passed_phase_count": 2,
            "phase_count": 2,
            "phases": [
                {"name": "applicability_validation", "passed": True, "reviewer_ready": True},
                {"name": "compliance_review", "passed": True, "reviewer_ready": True},
            ],
        },
    )

    result = run_promotion_suite(
        output_dir=output_dir,
        manifest_path=manifest_path,
        strict_expansion=True,
    )
    slot = result.summary["expansion_slots"][0]
    profile_checks = {
        check["name"]: check for check in slot["forest_plan_profile_checks"]
    }

    assert result.summary["current_promotion_ready"] is True
    assert result.summary["expansion_artifacts_ready"] is True
    assert result.summary["expansion_ready"] is False
    assert result.summary["promotion_ready"] is False
    assert slot["manifest_ready"] is True
    assert slot["ready"] is False
    assert profile_checks["forest_plan_component_phase_present_when_required"][
        "passed"
    ] is False
    assert profile_checks["forest_plan_component_phase_present_when_required"][
        "actual"
    ] == ["applicability_validation", "compliance_review"]
