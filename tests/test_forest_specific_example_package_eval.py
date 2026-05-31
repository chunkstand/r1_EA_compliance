from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.forest_specific_example_package_eval import (
    FOREST_SPECIFIC_EXAMPLE_PACKAGE_EVAL_RESULTS_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.forest_specific_example_package_eval import (
    FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.forest_specific_example_package_eval import (
    run_forest_specific_example_package_eval,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_REGISTRY = (
    REPO_ROOT / "config" / "forest_specific_example_package_registry_v1.json"
)


def test_forest_specific_example_package_eval_accepts_mixed_reviewer_ready_typed_blocked_and_profile_guidance() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(root)

        result = run_forest_specific_example_package_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["schema_version"] == (
            FOREST_SPECIFIC_EXAMPLE_PACKAGE_EVAL_RESULTS_SCHEMA_VERSION
        )
        assert result.summary["passed"] is True
        assert result.summary["forest_unit_count"] == 3
        assert result.summary["covered_forest_count"] == 3
        assert result.summary["failed_forest_count"] == 0
        assert result.summary["review_example_count"] == 3
        assert result.summary["reviewer_ready_example_count"] == 2
        assert result.summary["typed_blocked_example_count"] == 1
        assert result.summary["distinct_governed_example_forest_count"] == 2
        assert result.summary["profile_guidance_only_count"] == 1
        assert result.summary["declared_routing_status_counts"] == {
            "profile_eval_guidance_only": 1,
            "real_package_examples_available": 1,
            "typed_blocked_example_available": 1,
        }
        assert result.summary["actual_routing_status_counts"] == {
            "profile_eval_guidance_only": 1,
            "real_package_examples_available": 1,
            "typed_blocked_example_available": 1,
        }
        assert result.summary["threshold_failures"] == []


def test_forest_specific_example_package_eval_rejects_primary_example_contract_status_drift() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(
            root,
            east_actual_contract_status="typed_blocked",
        )

        result = run_forest_specific_example_package_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        assert result.summary["failed_forest_count"] == 1
        assert result.summary["failure_category_counts"][
            "coverage_slot_contract_status_mismatch"
        ] >= 1
        assert result.summary["failure_category_counts"][
            "primary_example_contract_status_mismatch"
        ] >= 1
        assert result.summary["failure_category_counts"]["routing_status_mismatch"] >= 1
        cgnf = next(
            forest
            for forest in result.summary["forests"]
            if forest["forest_unit_id"] == "custer-gallatin-nf"
        )
        assert cgnf["passed"] is False
        assert cgnf["actual_routing_status"] == "missing_or_failed"
        assert "routing_status_mismatch" in cgnf["failure_reasons"]
        assert "primary_example_contract_status_mismatch" in cgnf["failure_reasons"]


def test_committed_registry_declares_output_contract_and_thresholds() -> None:
    registry = json.loads(COMMITTED_REGISTRY.read_text(encoding="utf-8"))

    assert registry["schema_version"] == FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_SCHEMA_VERSION
    assert registry["coverage_thresholds"] == {
        "required_forest_unit_count": 10,
        "review_example_count_min": 10,
        "reviewer_ready_example_count_min": 10,
        "typed_blocked_example_count_min": 0,
        "distinct_governed_example_forest_count_min": 9,
        "profile_guidance_only_count_max": 1,
        "failed_forest_count_max": 0,
    }
    assert registry["output_schema"]["required_summary_fields"] == [
        "schema_version",
        "manifest_schema_version",
        "created_at",
        "manifest_path",
        "output_dir",
        "output_path",
        "real_package_review_coverage_manifest_path",
        "real_package_review_coverage_results_path",
        "forest_plan_profile_eval_manifest_path",
        "forest_plan_profile_eval_results_path",
        "forest_specific_example_package_id",
        "forest_specific_example_package_version",
        "passed",
        "forest_unit_count",
        "covered_forest_count",
        "failed_forest_count",
        "review_example_count",
        "reviewer_ready_example_count",
        "typed_blocked_example_count",
        "distinct_governed_example_forest_count",
        "profile_guidance_only_count",
        "declared_routing_status_counts",
        "actual_routing_status_counts",
        "threshold_failures",
        "failure_category_counts",
        "contract_checks",
        "forests",
    ]


def _write_manifest(
    root: Path,
    *,
    east_actual_contract_status: str = "reviewer_ready",
) -> Path:
    output_dir = root / "source_library"
    review_results_path = (
        output_dir
        / "reviews"
        / "real_package_review_coverage_eval"
        / "real_package_review_coverage_eval_results.json"
    )
    profile_results_path = (
        output_dir
        / "evaluations"
        / "forest_plan_profile"
        / "forest_plan_profile_eval_results.json"
    )
    _write_json(
        review_results_path,
        {
            "schema_version": "real-package-review-coverage-results-v1",
            "slots": [
                {
                    "slot_id": "east-crazies-current-promotion",
                    "review_id": "v1-cg-ecid-compliance-review",
                    "actual_contract_status": east_actual_contract_status,
                    "passed": east_actual_contract_status == "reviewer_ready",
                    "summary_path": "reviews/east.json",
                    "package_authority": {"passed": True},
                },
                {
                    "slot_id": "west-reservoir-typed-blocked",
                    "review_id": "west-reservoir-67436",
                    "actual_contract_status": "typed_blocked",
                    "passed": True,
                    "summary_path": "reviews/west.json",
                    "package_authority": {"passed": True},
                },
                {
                    "slot_id": "south-plateau-reviewer-ready",
                    "review_id": "region1-expansion-south-plateau-landscape-treatment",
                    "actual_contract_status": "reviewer_ready",
                    "passed": True,
                    "summary_path": "reviews/south.json",
                    "package_authority": {"passed": True},
                },
            ],
        },
    )
    _write_json(
        profile_results_path,
        {
            "schema_version": "region1-forest-plan-profile-eval-results-v1",
            "profiles": [
                {
                    "forest_unit_id": "custer-gallatin-nf",
                    "passed": True,
                    "coverage_status": "covered",
                    "required_fixture_family_ids": [
                        "scope_positive",
                        "custer_hard_negative",
                    ],
                    "failure_reasons": [],
                },
                {
                    "forest_unit_id": "flathead-nf",
                    "passed": True,
                    "coverage_status": "covered",
                    "required_fixture_family_ids": [
                        "scope_positive",
                        "flathead_hard_negative",
                    ],
                    "failure_reasons": [],
                },
                {
                    "forest_unit_id": "lolo-nf",
                    "passed": True,
                    "coverage_status": "covered",
                    "required_fixture_family_ids": [
                        "scope_positive",
                        "lolo_hard_negative",
                    ],
                    "failure_reasons": [],
                },
            ],
        },
    )

    shared_contract_dir = root / "contracts"
    _write_json(shared_contract_dir / "real_package_manifest.json", {"id": "real-package"})
    _write_json(shared_contract_dir / "profile_manifest.json", {"id": "forest-profile"})

    manifest_path = root / "forest_specific_example_package_registry_v1.json"
    _write_json(
        manifest_path,
        {
            "schema_version": FOREST_SPECIFIC_EXAMPLE_PACKAGE_REGISTRY_SCHEMA_VERSION,
            "contract_id": "unit-forest-specific-example-packages",
            "version": "0.1.0",
            "coverage_thresholds": {
                "required_forest_unit_count": 3,
                "review_example_count_min": 3,
                "reviewer_ready_example_count_min": 2,
                "typed_blocked_example_count_min": 1,
                "distinct_governed_example_forest_count_min": 2,
                "profile_guidance_only_count_max": 1,
                "failed_forest_count_max": 0,
            },
            "output_schema": {
                "required_summary_fields": [
                    "schema_version",
                    "manifest_schema_version",
                    "created_at",
                    "manifest_path",
                    "output_dir",
                    "output_path",
                    "real_package_review_coverage_manifest_path",
                    "real_package_review_coverage_results_path",
                    "forest_plan_profile_eval_manifest_path",
                    "forest_plan_profile_eval_results_path",
                    "forest_specific_example_package_id",
                    "forest_specific_example_package_version",
                    "passed",
                    "forest_unit_count",
                    "covered_forest_count",
                    "failed_forest_count",
                    "review_example_count",
                    "reviewer_ready_example_count",
                    "typed_blocked_example_count",
                    "distinct_governed_example_forest_count",
                    "profile_guidance_only_count",
                    "declared_routing_status_counts",
                    "actual_routing_status_counts",
                    "threshold_failures",
                    "failure_category_counts",
                    "contract_checks",
                    "forests",
                ]
            },
            "summary": {
                "forest_unit_count": 3,
                "profile_guidance_only_count": 1,
                "review_example_count": 3,
                "reviewer_ready_example_count": 2,
                "typed_blocked_example_count": 1,
            },
            "shared_contract_catalog": [
                {
                    "shared_contract_id": "real_package_review_coverage_manifest",
                    "path": str(shared_contract_dir / "real_package_manifest.json"),
                },
                {
                    "shared_contract_id": "forest_plan_profile_eval_coverage_manifest",
                    "path": str(shared_contract_dir / "profile_manifest.json"),
                },
            ],
            "review_examples": [
                {
                    "example_id": "cgnf-east-crazy-current-promotion",
                    "review_id": "v1-cg-ecid-compliance-review",
                    "forest_unit_id": "custer-gallatin-nf",
                    "coverage_slot_id": "east-crazies-current-promotion",
                    "expected_contract_status": "reviewer_ready",
                    "applicable_forest_unit_ids": ["custer-gallatin-nf"],
                },
                {
                    "example_id": "cgnf-south-plateau-expansion",
                    "review_id": "region1-expansion-south-plateau-landscape-treatment",
                    "forest_unit_id": "custer-gallatin-nf",
                    "coverage_slot_id": "south-plateau-reviewer-ready",
                    "expected_contract_status": "reviewer_ready",
                    "applicable_forest_unit_ids": ["custer-gallatin-nf"],
                },
                {
                    "example_id": "flathead-west-reservoir-typed-blocked",
                    "review_id": "west-reservoir-67436",
                    "forest_unit_id": "flathead-nf",
                    "coverage_slot_id": "west-reservoir-typed-blocked",
                    "expected_contract_status": "typed_blocked",
                    "applicable_forest_unit_ids": ["flathead-nf"],
                },
            ],
            "forest_routing": [
                {
                    "forest_unit_id": "custer-gallatin-nf",
                    "forest_unit_label": "Custer Gallatin National Forest",
                    "routing_status": "real_package_examples_available",
                    "applicable_to_forest_unit_ids": ["custer-gallatin-nf"],
                    "primary_example_id": "cgnf-east-crazy-current-promotion",
                    "supplemental_example_ids": ["cgnf-south-plateau-expansion"],
                    "required_fixture_family_ids": [
                        "scope_positive",
                        "custer_hard_negative",
                    ],
                    "guidance_note": "Use reviewer-ready East Crazy first.",
                },
                {
                    "forest_unit_id": "flathead-nf",
                    "forest_unit_label": "Flathead National Forest",
                    "routing_status": "typed_blocked_example_available",
                    "applicable_to_forest_unit_ids": ["flathead-nf"],
                    "primary_example_id": "flathead-west-reservoir-typed-blocked",
                    "supplemental_example_ids": [],
                    "required_fixture_family_ids": [
                        "scope_positive",
                        "flathead_hard_negative",
                    ],
                    "guidance_note": "Use typed-blocked West Reservoir only as guidance.",
                },
                {
                    "forest_unit_id": "lolo-nf",
                    "forest_unit_label": "Lolo National Forest",
                    "routing_status": "profile_eval_guidance_only",
                    "applicable_to_forest_unit_ids": ["lolo-nf"],
                    "primary_example_id": None,
                    "supplemental_example_ids": [],
                    "required_fixture_family_ids": [
                        "scope_positive",
                        "lolo_hard_negative",
                    ],
                    "guidance_note": "No governed package example yet.",
                },
            ],
        },
    )
    return manifest_path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
