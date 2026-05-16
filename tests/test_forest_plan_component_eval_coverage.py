from __future__ import annotations

import json
import tempfile
from pathlib import Path

from usfs_r1_ea_sources.forest_plan_component_eval_coverage import (
    DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
)
from usfs_r1_ea_sources.forest_plan_component_eval_coverage import (
    evaluate_forest_plan_component_eval_coverage,
)
from usfs_r1_ea_sources.forest_plan_component_eval_coverage import (
    resolve_forest_plan_component_eval_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED_MANIFEST = REPO_ROOT / "config" / "forest_plan_component_eval_coverage_v1.json"


def test_committed_manifest_tracks_three_review_slots() -> None:
    manifest = json.loads(COMMITTED_MANIFEST.read_text())

    assert manifest["schema_version"] == "forest-plan-component-eval-coverage-v1"
    assert manifest["required_review_ids"] == [
        "v1-cg-ecid-compliance-review",
        "v1-cg-ecid-source-delta-review",
        "west-reservoir-67436",
    ]
    slots = {slot["review_id"]: slot for slot in manifest["slots"]}
    assert slots["v1-cg-ecid-compliance-review"]["eval_file"] == "forest_plan_component_eval_seed.json"
    assert (
        slots["v1-cg-ecid-source-delta-review"]["eval_file"]
        == "forest_plan_component_evals/v1-cg-ecid-source-delta-review.json"
    )
    assert (
        slots["west-reservoir-67436"]["eval_file"]
        == "forest_plan_component_evals/west-reservoir-67436.json"
    )


def test_resolve_component_eval_file_reads_tracked_manifest_slot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        eval_file = root / "tracked.json"
        _write_contract(eval_file, review_id="component-review", source_set_id="source-set-a")
        _write_manifest(
            root,
            slots=[
                _slot(
                    review_id="component-review",
                    forest_unit_id="flathead-nf",
                    source_set_id="source-set-a",
                    eval_file=eval_file,
                )
            ],
        )

        resolved = resolve_forest_plan_component_eval_file(
            review_id="component-review",
            manifest_path=root / DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
        )

        assert resolved == eval_file


def test_component_eval_coverage_passes_for_complete_tracked_roster() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        eval_a = root / "component-a.json"
        eval_b = root / "component-b.json"
        eval_c = root / "component-c.json"
        _write_contract(eval_a, review_id="review-a", source_set_id="source-set-a")
        _write_contract(eval_b, review_id="review-b", source_set_id="source-set-b")
        _write_contract(eval_c, review_id="review-c", source_set_id="source-set-c")
        _write_result(output_dir, review_id="review-a", source_set_id="source-set-a", eval_file=eval_a)
        _write_result(output_dir, review_id="review-b", source_set_id="source-set-b", eval_file=eval_b)
        _write_result(output_dir, review_id="review-c", source_set_id="source-set-c", eval_file=eval_c)
        _write_manifest(
            root,
            slots=[
                _slot(
                    review_id="review-a",
                    forest_unit_id="custer-gallatin-nf",
                    source_set_id="source-set-a",
                    eval_file=eval_a,
                ),
                _slot(
                    review_id="review-b",
                    forest_unit_id="custer-gallatin-nf",
                    source_set_id="source-set-b",
                    eval_file=eval_b,
                ),
                _slot(
                    review_id="review-c",
                    forest_unit_id="flathead-nf",
                    source_set_id="source-set-c",
                    eval_file=eval_c,
                ),
            ],
        )

        result = evaluate_forest_plan_component_eval_coverage(
            output_dir=output_dir,
            manifest_path=root / DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
        )

        assert result.summary["passed"] is True
        assert result.summary["required_review_count"] == 3
        assert result.summary["covered_review_count"] == 3
        assert result.summary["distinct_forest_count"] == 2
        assert result.summary["missing_contract_count"] == 0
        assert result.summary["missing_result_count"] == 0
        assert result.summary["stale_identity_count"] == 0
        assert result.summary["unresolved_review_count"] == 0


def test_component_eval_coverage_fails_on_missing_contract_and_stale_result_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        eval_a = root / "component-a.json"
        eval_c = root / "component-c.json"
        _write_contract(eval_a, review_id="review-a", source_set_id="source-set-a")
        _write_contract(eval_c, review_id="review-c", source_set_id="source-set-c")
        _write_result(output_dir, review_id="review-a", source_set_id="source-set-a", eval_file=eval_a)
        _write_result(
            output_dir,
            review_id="review-c",
            source_set_id="source-set-stale",
            eval_file=eval_c,
        )
        _write_manifest(
            root,
            slots=[
                _slot(
                    review_id="review-a",
                    forest_unit_id="custer-gallatin-nf",
                    source_set_id="source-set-a",
                    eval_file=eval_a,
                ),
                _slot(
                    review_id="review-b",
                    forest_unit_id="custer-gallatin-nf",
                    source_set_id="source-set-b",
                    eval_file=root / "missing-contract.json",
                ),
                _slot(
                    review_id="review-c",
                    forest_unit_id="flathead-nf",
                    source_set_id="source-set-c",
                    eval_file=eval_c,
                ),
            ],
        )

        result = evaluate_forest_plan_component_eval_coverage(
            output_dir=output_dir,
            manifest_path=root / DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
        )

        assert result.summary["passed"] is False
        assert result.summary["missing_contract_count"] == 1
        assert result.summary["stale_identity_count"] == 1
        assert result.summary["unresolved_review_count"] == 1
        assert result.summary["failure_category_counts"] == {
            "missing_required_review_contract": 2,
            "missing_required_review_result": 2,
            "stale_review_identity": 2,
            "unresolved_review_eval": 1,
        }


def _write_manifest(root: Path, *, slots: list[dict]) -> None:
    _write_json(
        root / DEFAULT_FOREST_PLAN_COMPONENT_EVAL_COVERAGE_MANIFEST_PATH,
        {
            "schema_version": "forest-plan-component-eval-coverage-v1",
            "id": "unit-component-coverage",
            "version": "0.1.0",
            "required_review_ids": [slot["review_id"] for slot in slots if slot["required"]],
            "coverage_thresholds": {
                "required_review_count": len(slots),
                "distinct_forest_count_min": 2,
                "missing_contract_count_max": 0,
                "missing_result_count_max": 0,
                "stale_identity_count_max": 0,
                "unresolved_review_count_max": 0,
            },
            "slots": slots,
        },
    )


def _slot(
    *,
    review_id: str,
    forest_unit_id: str,
    source_set_id: str,
    eval_file: Path,
) -> dict:
    return {
        "slot_id": f"{review_id}-slot",
        "label": f"{review_id} slot",
        "review_id": review_id,
        "forest_unit_id": forest_unit_id,
        "expected_source_set_id": source_set_id,
        "eval_file": str(eval_file),
        "required": True,
    }


def _write_contract(path: Path, *, review_id: str, source_set_id: str) -> None:
    _write_json(
        path,
        {
            "schema_version": "forest-plan-component-eval-v0",
            "eval_id": f"{review_id}-eval",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "cases": [
                {
                    "case_id": f"{review_id}-case",
                    "component_id": "component-1",
                    "applicability_status": "applicable",
                }
            ],
        },
    )


def _write_result(
    output_dir: Path,
    *,
    review_id: str,
    source_set_id: str,
    eval_file: Path,
) -> None:
    review_dir = output_dir / "reviews" / review_id
    _write_json(
        review_dir / "forest_plan_component_eval_results.json",
        {
            "schema_version": "forest-plan-component-eval-results-v0",
            "review_id": review_id,
            "source_set_id": source_set_id,
            "eval_file": str(eval_file),
            "passed": True,
            "summary": {
                "review_id": review_id,
                "source_set_id": source_set_id,
                "eval_file": str(eval_file),
                "passed": True,
            },
        },
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
