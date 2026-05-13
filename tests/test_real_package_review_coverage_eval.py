from __future__ import annotations

from pathlib import Path
import json
import tempfile

import pytest

from usfs_r1_ea_sources.real_package_review_coverage_eval import (
    REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.real_package_review_coverage_eval import (
    run_real_package_review_coverage_eval,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_MANIFEST = REPO_ROOT / "config" / "v1_real_package_review_coverage_v1.json"


def test_real_package_review_coverage_eval_accepts_declared_ready_and_blocked_slots() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(root)

        result = run_real_package_review_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is True
        assert result.summary["covered_slot_count"] == 3
        assert result.summary["reviewer_ready_slot_count"] == 2
        assert result.summary["typed_blocked_slot_count"] == 1
        assert result.summary["distinct_forest_count"] == 2
        assert result.summary["distinct_package_style_count"] == 3
        assert result.summary["missing_package_authority_count"] == 0
        assert result.summary["threshold_failures"] == []


def test_real_package_review_coverage_eval_fails_missing_authority() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(
            root,
            missing_ready_authority=True,
        )

        result = run_real_package_review_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        assert result.summary["missing_package_authority_count"] == 1
        assert result.summary["failure_category_counts"]["missing_package_authority"] >= 1


def test_real_package_review_coverage_eval_rejects_missing_required_slot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(
            root,
            include_blocked_slot=False,
        )

        with pytest.raises(
            ValueError,
            match="required_coverage_class_ids must exactly match",
        ):
            run_real_package_review_coverage_eval(
                output_dir=output_dir,
                manifest_path=manifest_path,
            )


def test_committed_real_package_review_coverage_manifest_tracks_three_slots() -> None:
    manifest = json.loads(COMMITTED_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION
    assert manifest["required_coverage_class_ids"] == [
        "alternate_package_reviewer_ready",
        "current_promotion_reviewer_ready",
        "typed_blocked_expansion",
    ]
    assert [item["review_id"] for item in manifest["slots"]] == [
        "v1-cg-ecid-compliance-review",
        "west-reservoir-67436",
        "region1-expansion-south-plateau-landscape-treatment",
    ]
    thresholds = manifest["coverage_thresholds"]
    assert thresholds["required_slot_count"] == 3
    assert thresholds["required_coverage_class_count"] == 3
    assert thresholds["distinct_forest_count_min"] == 2
    assert thresholds["distinct_package_style_count_min"] == 3
    assert thresholds["reviewer_ready_slot_count_min"] == 2
    assert thresholds["typed_blocked_slot_count_min"] == 1


def _write_manifest(
    root: Path,
    *,
    include_blocked_slot: bool = True,
    missing_ready_authority: bool = False,
) -> Path:
    results_dir = root / "results"
    authorities_dir = root / "authorities"
    (authorities_dir / "catalog-east").mkdir(parents=True)
    (authorities_dir / "package-east").mkdir(parents=True)
    (authorities_dir / "package-west").mkdir(parents=True)
    (authorities_dir / "south-intake").mkdir(parents=True)
    replay_context_path = root / "config" / "replay_contexts" / "east.json"
    replay_context_path.parent.mkdir(parents=True, exist_ok=True)
    replay_context_path.write_text(
        json.dumps(
            {
                "review_id": "v1-cg-ecid-compliance-review",
                "source_set_id": "source-set-east",
                "catalog_dir": "authorities/catalog-east",
                "package_path": "authorities/package-east",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    review_payloads = [
        {
            "review_id": "v1-cg-ecid-compliance-review",
            "passed": True,
            "contract_status": "reviewer_ready",
            "forest_unit_id": "custer-gallatin-nf",
            "package_style_tags": ["clean_baseline"],
            "actual_overall_passed": True,
            "broader_ea_passed": True,
            "forest_plan_passed": True,
            "failure_category_counts": {},
            "forest_plan_failure_category_counts": {},
        },
        {
            "review_id": "west-reservoir-67436",
            "passed": True,
            "contract_status": "reviewer_ready",
            "forest_unit_id": "flathead-nf",
            "package_style_tags": ["live_external_noisy"],
            "actual_overall_passed": True,
            "broader_ea_passed": True,
            "forest_plan_passed": True,
            "failure_category_counts": {},
            "forest_plan_failure_category_counts": {},
        },
    ]
    if include_blocked_slot:
        review_payloads.append(
            {
                "review_id": "region1-expansion-south-plateau-landscape-treatment",
                "passed": True,
                "contract_status": "typed_blocked",
                "forest_unit_id": "custer-gallatin-nf",
                "package_style_tags": ["typed_blocked_expansion"],
                "actual_overall_passed": False,
                "broader_ea_passed": True,
                "forest_plan_passed": False,
                "failure_category_counts": {
                    "forest_plan_reviewer_resolution_open": 1,
                },
                "forest_plan_failure_category_counts": {
                    "forest_plan_reviewer_resolution_open": 1,
                },
                "contract_expectations": {
                    "allowed_blocker_categories": [
                        "forest_plan_reviewer_resolution_open",
                    ],
                    "matched_blocker_categories": [
                        "forest_plan_reviewer_resolution_open",
                    ],
                    "unexpected_blocker_categories": [],
                },
            }
        )
    review_paths = []
    for index, payload in enumerate(review_payloads, start=1):
        path = results_dir / f"review-{index}.json"
        _write_json(path, payload)
        review_paths.append(path)
    slots = [
        {
            "slot_id": "east-crazies-current-promotion",
            "label": "East Crazies current promotion",
            "review_id": "v1-cg-ecid-compliance-review",
            "package_label": "East Crazies",
            "coverage_class_id": "current_promotion_reviewer_ready",
            "forest_unit_id": "custer-gallatin-nf",
            "eval_file": "config/v1_ecid_real_ea_eval.json",
            "results_path": str(review_paths[0]),
            "required": True,
            "expected_contract_status": "reviewer_ready",
            "package_authority": {
                "replay_context_path": str(replay_context_path),
            },
        },
        {
            "slot_id": "west-reservoir-reviewer-ready",
            "label": "West Reservoir reviewer-ready proving lane",
            "review_id": "west-reservoir-67436",
            "package_label": "West Reservoir",
            "coverage_class_id": "alternate_package_reviewer_ready",
            "forest_unit_id": "flathead-nf",
            "eval_file": "config/v1_west_reservoir_real_ea_eval.json",
            "results_path": str(review_paths[1]),
            "required": True,
            "expected_contract_status": "reviewer_ready",
            "package_authority": {
                "intake_package_path": str(
                    authorities_dir / ("missing-west" if missing_ready_authority else "package-west")
                ),
            },
        },
    ]
    if include_blocked_slot:
        slots.append(
            {
                "slot_id": "south-plateau-typed-blocked",
                "label": "South Plateau typed blocked expansion lane",
                "review_id": "region1-expansion-south-plateau-landscape-treatment",
                "package_label": "South Plateau",
                "coverage_class_id": "typed_blocked_expansion",
                "forest_unit_id": "custer-gallatin-nf",
                "eval_file": "config/v1_south_plateau_real_ea_eval.json",
                "results_path": str(review_paths[2]),
                "required": True,
                "expected_contract_status": "typed_blocked",
                "package_authority": {
                    "intake_package_path": str(authorities_dir / "south-intake"),
                },
            }
        )
    manifest_path = root / "v1_real_package_review_coverage_v1.json"
    _write_json(
        manifest_path,
        {
            "schema_version": REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION,
            "id": "unit-real-package-review-coverage",
            "version": "0.1.0",
            "required_coverage_class_ids": [
                "alternate_package_reviewer_ready",
                "current_promotion_reviewer_ready",
                "typed_blocked_expansion",
            ],
            "coverage_thresholds": {
                "required_slot_count": 3,
                "required_coverage_class_count": 3,
                "distinct_forest_count_min": 2,
                "distinct_package_style_count_min": 3,
                "reviewer_ready_slot_count_min": 2,
                "typed_blocked_slot_count_min": 1,
                "missing_required_slot_count_max": 0,
                "missing_package_authority_count_max": 0,
            },
            "slots": slots,
        },
    )
    return manifest_path


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
