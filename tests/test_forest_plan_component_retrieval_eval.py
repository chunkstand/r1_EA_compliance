from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.forest_plan_component_retrieval_eval import (
    FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION,
)
from usfs_r1_ea_sources.forest_plan_component_retrieval_eval import (
    run_forest_plan_component_retrieval_eval,
)


SOURCE_SET_ID = "source-set-test-component-retrieval"


def test_component_retrieval_eval_writes_outputs_and_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_inventory(root, _base_components())
        manifest_path = _write_manifest(root, _base_manifest())

        result = run_forest_plan_component_retrieval_eval(
            output_dir=root,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is True
        assert result.summary["schema_version"] == (
            FOREST_PLAN_COMPONENT_RETRIEVAL_EVAL_RESULTS_SCHEMA_VERSION
        )
        assert result.summary["case_count"] == 6
        assert result.summary["expected_pass_case_count"] == 4
        assert result.summary["hard_negative_case_count"] == 2
        assert result.summary["metrics"]["component_retrieval_precision"] == 1.0
        assert result.summary["metrics"]["component_retrieval_recall"] == 1.0
        assert result.summary["metrics"]["applicable_standard_component_recall"] == 1.0
        assert result.summary["metrics"]["wrong_forest_component_rate"] == 0.0
        assert result.summary["metrics"]["hard_negative_zero_match_rate"] == 1.0
        assert result.output_path.exists()
        assert result.report_path.exists()


def test_component_retrieval_eval_fails_when_required_component_is_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        components = [
            component
            for component in _base_components()
            if component["component_id"] != "CG-STD-SOIL-01"
        ]
        _write_inventory(root, components)
        manifest_path = _write_manifest(root, _base_manifest())

        result = run_forest_plan_component_retrieval_eval(
            output_dir=root,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        case = _case(result.summary, "custer-standard-soil")
        assert case["passed"] is False
        assert "expected_component_not_retrieved" in case["failure_reasons"]
        assert result.summary["metrics"]["component_retrieval_recall"] < 1.0


def test_component_retrieval_eval_fails_on_wrong_forest_selection() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        components = list(_base_components())
        components.append(
            _component(
                component_id="WRONG-FOREST-SOIL-01",
                forest_unit_id="beaverhead-deerlodge-nf",
                component_type="standard",
                component_text=(
                    "Vegetation management activities do not create detrimental soil conditions "
                    "on more than 15 percent of an activity area."
                ),
                package_evidence_terms=[
                    "vegetation management activities do not create detrimental soil conditions on more than 15 percent of an activity area"
                ],
            )
        )
        _write_inventory(root, components)
        manifest = _base_manifest()
        manifest["search_config"]["top_k"] = 3
        manifest_path = _write_manifest(root, manifest)

        result = run_forest_plan_component_retrieval_eval(
            output_dir=root,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        case = _case(result.summary, "flathead-standard-soil")
        assert case["passed"] is False
        assert "wrong_forest_component_selected" in case["failure_reasons"]
        assert result.summary["metrics"]["wrong_forest_component_rate"] > 0.0


def test_component_retrieval_eval_fails_when_hard_negative_returns_components() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_inventory(root, _base_components())
        manifest = _base_manifest()
        for case in manifest["cases"]:
            if case["case_id"] == "hard-negative-plan-consistency":
                case["query"] = (
                    "commercial timber harvest is prohibited in recommended wilderness"
                )
        manifest_path = _write_manifest(root, manifest)

        result = run_forest_plan_component_retrieval_eval(
            output_dir=root,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        case = _case(result.summary, "hard-negative-plan-consistency")
        assert case["passed"] is False
        assert "hard_negative_query_returned_components" in case["failure_reasons"]
        assert result.summary["metrics"]["hard_negative_zero_match_rate"] < 1.0


def _base_manifest() -> dict:
    return {
        "schema_version": "forest-plan-component-retrieval-eval-v1",
        "contract_id": "test-forest-plan-component-retrieval-eval",
        "version": "1",
        "source_set_id": SOURCE_SET_ID,
        "expected_active_source_set_ids": [SOURCE_SET_ID],
        "search_config": {"top_k": 1},
        "coverage_requirements": {
            "minimum_expected_pass_case_count": 4,
            "minimum_hard_negative_case_count": 2,
            "required_forest_unit_ids": [
                "beaverhead-deerlodge-nf",
                "custer-gallatin-nf",
                "flathead-nf",
            ],
        },
        "metric_thresholds": {
            "case_count": {"min": 6},
            "expected_pass_case_count": {"min": 4},
            "hard_negative_case_count": {"min": 2},
            "component_retrieval_precision": {"min": 1.0},
            "component_retrieval_recall": {"min": 1.0},
            "applicable_standard_component_recall": {"min": 1.0},
            "wrong_forest_component_rate": {"max": 0.0},
            "hard_negative_zero_match_rate": {"min": 1.0},
        },
        "output_schema": {
            "required_summary_fields": [
                "schema_version",
                "contract_id",
                "source_set_id",
                "case_count",
                "metrics",
                "contract_checks",
                "cases",
                "failed_case_ids",
            ]
        },
        "cases": [
            {
                "case_id": "custer-standard-soil",
                "case_type": "expected_pass",
                "query": "new management activities shall not create detrimental soil conditions on more than 15 percent of an activity area",
                "expected_forest_unit_id": "custer-gallatin-nf",
                "expected_component_ids": ["CG-STD-SOIL-01"],
                "applicable_standard_case": True,
            },
            {
                "case_id": "custer-goal-air",
                "case_type": "expected_pass",
                "query": "the custer gallatin national forest cooperates with tribal federal and state agencies to meet air quality regulations as necessary",
                "expected_forest_unit_id": "custer-gallatin-nf",
                "expected_component_ids": ["CG-GO-AQ-01"],
                "applicable_standard_case": False,
            },
            {
                "case_id": "flathead-standard-soil",
                "case_type": "expected_pass",
                "query": "vegetation management activities do not create detrimental soil conditions on more than 15 percent of an activity area",
                "expected_forest_unit_id": "flathead-nf",
                "expected_component_ids": ["FH-STD-SOIL-01"],
                "applicable_standard_case": True,
            },
            {
                "case_id": "beaverhead-standard-wilderness",
                "case_type": "expected_pass",
                "query": "commercial timber harvest is prohibited in recommended wilderness",
                "expected_forest_unit_id": "beaverhead-deerlodge-nf",
                "expected_component_ids": ["BD-STD-WILD-01"],
                "applicable_standard_case": True,
            },
            {
                "case_id": "hard-negative-forest-plan",
                "case_type": "hard_negative",
                "query": "forest plan",
            },
            {
                "case_id": "hard-negative-plan-consistency",
                "case_type": "hard_negative",
                "query": "plan consistency",
            },
        ],
    }


def _base_components() -> list[dict]:
    return [
        _component(
            component_id="CG-STD-SOIL-01",
            forest_unit_id="custer-gallatin-nf",
            component_type="standard",
            component_text=(
                "New management activities shall not create detrimental soil conditions on more "
                "than 15 percent of an activity area."
            ),
            package_evidence_terms=[
                "new management activities shall not create detrimental soil conditions on more than 15 percent of an activity area"
            ],
        ),
        _component(
            component_id="CG-GO-AQ-01",
            forest_unit_id="custer-gallatin-nf",
            component_type="goal",
            component_text=(
                "The Custer Gallatin National Forest cooperates with tribal federal and state "
                "agencies to meet air quality regulations as necessary."
            ),
            package_evidence_terms=[
                "the custer gallatin national forest cooperates with tribal federal and state agencies to meet air quality regulations as necessary"
            ],
        ),
        _component(
            component_id="FH-STD-SOIL-01",
            forest_unit_id="flathead-nf",
            component_type="standard",
            component_text=(
                "Vegetation management activities do not create detrimental soil conditions on "
                "more than 15 percent of an activity area."
            ),
            package_evidence_terms=[
                "vegetation management activities do not create detrimental soil conditions on more than 15 percent of an activity area"
            ],
        ),
        _component(
            component_id="BD-STD-WILD-01",
            forest_unit_id="beaverhead-deerlodge-nf",
            component_type="standard",
            component_text="Commercial timber harvest is prohibited in recommended wilderness.",
            package_evidence_terms=[
                "commercial timber harvest is prohibited in recommended wilderness"
            ],
        ),
    ]


def _component(
    *,
    component_id: str,
    forest_unit_id: str,
    component_type: str,
    component_text: str,
    package_evidence_terms: list[str],
) -> dict:
    return {
        "component_id": component_id,
        "forest_unit_id": forest_unit_id,
        "component_type": component_type,
        "component_text": component_text,
        "package_evidence_terms": package_evidence_terms,
        "section_heading": f"{forest_unit_id} section",
        "resource_topics": [],
        "activity_tags": [],
    }


def _write_inventory(root: Path, components: list[dict]) -> None:
    inventory_path = (
        root
        / "derived"
        / SOURCE_SET_ID
        / "forest_plan_components"
        / "component_inventory.json"
    )
    inventory_path.parent.mkdir(parents=True, exist_ok=True)
    inventory = {
        "schema_version": "forest-plan-component-inventory-v0",
        "inventory_id": "test-component-inventory",
        "source_set_id": SOURCE_SET_ID,
        "components": components,
    }
    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_manifest(root: Path, manifest: dict) -> Path:
    manifest_path = root / "component-retrieval-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def _case(summary: dict, case_id: str) -> dict:
    return next(case for case in summary["cases"] if case["case_id"] == case_id)
