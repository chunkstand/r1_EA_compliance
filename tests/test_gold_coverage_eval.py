from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.gold_coverage_eval import GOLD_COVERAGE_EVAL_SCHEMA_VERSION
from usfs_r1_ea_sources.gold_coverage_eval import run_gold_coverage_eval


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_MANIFEST = REPO_ROOT / "config" / "gold_coverage_v1.json"
THEMES = [
    "land_exchange",
    "water_wetlands",
    "migratory_birds",
    "cultural_tribal",
    "roadless",
    "forest_plan_consistency",
    "multi_forest_plan_trigger",
]


def test_gold_coverage_eval_accepts_declared_reviewer_ready_mix() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(root)

        result = run_gold_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is True
        assert result.summary["passed_theme_count"] == 7
        assert result.summary["distinct_forest_count"] == 2
        assert result.summary["distinct_package_style_count"] == 3
        assert result.summary["reviewer_ready_review_count"] == 3
        assert result.summary["typed_blocked_review_count"] == 0
        assert result.summary["missing_package_authority_count"] == 0
        assert result.summary["threshold_failures"] == []


def test_gold_coverage_eval_fails_missing_theme_and_package_diversity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(
            root,
            compliance_tags=[theme for theme in THEMES if theme != "roadless"],
            review_package_styles=[
                ["clean_baseline"],
                ["clean_baseline"],
                ["reviewer_ready_expansion"],
            ],
        )

        result = run_gold_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        assert "roadless" in result.summary["theme_failure_ids"]
        assert result.summary["failure_category_counts"]["missing_named_theme_coverage"] >= 1
        assert (
            result.summary["failure_category_counts"]["insufficient_package_style_diversity"]
            >= 1
        )


def test_committed_gold_coverage_manifest_tracks_three_review_contracts() -> None:
    manifest = json.loads(COMMITTED_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == GOLD_COVERAGE_EVAL_SCHEMA_VERSION
    assert manifest["required_theme_ids"] == THEMES
    assert manifest["real_package_review_coverage"]["manifest_path"] == (
        "v1_real_package_review_coverage_v1.json"
    )
    thresholds = manifest["coverage_thresholds"]
    assert thresholds["required_theme_count"] == 7
    assert thresholds["required_high_priority_family_id_count"] == 19
    assert thresholds["applicability_gold_case_count_min"] == 12
    assert thresholds["compliance_gold_case_count_min"] == 14
    assert thresholds["required_review_contract_count"] == 3
    assert thresholds["distinct_forest_count_min"] == 2
    assert thresholds["distinct_package_style_count_min"] == 3
    assert thresholds["reviewer_ready_review_count_min"] == 3
    assert thresholds["typed_blocked_review_count_min"] == 0


def _write_manifest(
    root: Path,
    *,
    compliance_tags: list[str] | None = None,
    review_package_styles: list[list[str]] | None = None,
) -> Path:
    results_dir = root / "results"
    _write_json(
        results_dir / "applicability.json",
        {
            "passed": True,
            "promotion_ready": True,
            "case_count": 12,
            "source_chunk_count": 12,
            "family_group_coverage": {
                "required_group_ids": THEMES,
                "required_high_priority_family_id_count": 19,
                "unmapped_high_priority_family_count": 0,
                "positive_covered_group_ids": THEMES,
                "negative_covered_group_ids": THEMES,
                "adjudicated_covered_group_ids": THEMES,
            },
        },
    )
    _write_json(
        results_dir / "compliance.json",
        {
            "passed": True,
            "promotion_ready": False,
            "case_count": 14,
            "coverage_tags": compliance_tags or THEMES,
            "package_style_tags": [
                "clean_baseline",
                "live_external_noisy",
                "reviewer_ready_expansion",
            ],
        },
    )
    review_package_styles = review_package_styles or [
        ["clean_baseline"],
        ["live_external_noisy"],
        ["reviewer_ready_expansion"],
    ]
    review_payloads = [
        {
            "review_id": "v1-cg-ecid-compliance-review",
            "passed": True,
            "contract_status": "reviewer_ready",
            "forest_unit_id": "custer-gallatin-nf",
            "package_style_tags": review_package_styles[0],
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
            "package_style_tags": review_package_styles[1],
            "actual_overall_passed": True,
            "broader_ea_passed": True,
            "forest_plan_passed": True,
            "failure_category_counts": {},
            "forest_plan_failure_category_counts": {},
        },
        {
            "review_id": "region1-expansion-south-plateau-landscape-treatment",
            "passed": True,
            "contract_status": "reviewer_ready",
            "forest_unit_id": "custer-gallatin-nf",
            "package_style_tags": review_package_styles[2],
            "actual_overall_passed": True,
            "broader_ea_passed": True,
            "forest_plan_passed": True,
            "failure_category_counts": {},
            "forest_plan_failure_category_counts": {},
        },
    ]
    review_paths = []
    for index, payload in enumerate(review_payloads, start=1):
        path = results_dir / f"review-{index}.json"
        _write_json(path, payload)
        review_paths.append(path)
    real_package_manifest_path = _write_real_package_manifest(root, review_paths=review_paths)
    manifest_path = root / "gold_coverage_v1.json"
    _write_json(
        manifest_path,
        {
            "schema_version": GOLD_COVERAGE_EVAL_SCHEMA_VERSION,
            "id": "unit-gold-coverage",
            "version": "0.1.0",
            "required_theme_ids": THEMES,
            "coverage_thresholds": {
                "required_theme_count": 7,
                "required_high_priority_family_id_count": 19,
                "unmapped_high_priority_family_count_max": 0,
                "applicability_gold_case_count_min": 12,
                "compliance_gold_case_count_min": 14,
                "required_review_contract_count": 3,
                "distinct_forest_count_min": 2,
                "distinct_package_style_count_min": 3,
                "reviewer_ready_review_count_min": 3,
                "typed_blocked_review_count_min": 0,
                "missing_required_review_contract_count_max": 0,
                "missing_package_authority_count_max": 0,
            },
            "applicability_gold": {"results_path": str(results_dir / "applicability.json")},
            "compliance_gold": {"results_path": str(results_dir / "compliance.json")},
            "real_package_review_coverage": {
                "manifest_path": str(real_package_manifest_path),
            },
        },
    )
    return manifest_path


def _write_real_package_manifest(root: Path, *, review_paths: list[Path]) -> Path:
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
    manifest_path = root / "v1_real_package_review_coverage_v1.json"
    _write_json(
        manifest_path,
        {
            "schema_version": "real-package-review-coverage-v1",
            "id": "unit-real-package-review-coverage",
            "version": "0.1.0",
            "required_coverage_class_ids": [
                "alternate_package_reviewer_ready",
                "current_promotion_reviewer_ready",
                "expansion_reviewer_ready",
            ],
            "coverage_thresholds": {
                "required_slot_count": 3,
                "required_coverage_class_count": 3,
                "distinct_forest_count_min": 2,
                "distinct_package_style_count_min": 3,
                "reviewer_ready_slot_count_min": 3,
                "typed_blocked_slot_count_min": 0,
                "missing_required_slot_count_max": 0,
                "missing_package_authority_count_max": 0,
            },
            "slots": [
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
                        "intake_package_path": str(authorities_dir / "package-west"),
                    },
                },
                {
                    "slot_id": "south-plateau-reviewer-ready",
                    "label": "South Plateau reviewer-ready expansion lane",
                    "review_id": "region1-expansion-south-plateau-landscape-treatment",
                    "package_label": "South Plateau",
                    "coverage_class_id": "expansion_reviewer_ready",
                    "forest_unit_id": "custer-gallatin-nf",
                    "eval_file": "config/v1_south_plateau_real_ea_eval.json",
                    "results_path": str(review_paths[2]),
                    "required": True,
                    "expected_contract_status": "reviewer_ready",
                    "package_authority": {
                        "intake_package_path": str(authorities_dir / "south-intake"),
                    },
                },
            ],
        },
    )
    return manifest_path


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
