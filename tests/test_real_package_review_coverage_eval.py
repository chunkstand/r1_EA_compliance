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


def test_real_package_review_coverage_eval_accepts_declared_reviewer_ready_and_typed_blocked_slots() -> None:
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
        assert result.summary["phase_eval_required_slot_count"] == 2
        assert result.summary["phase_eval_ready_slot_count"] == 2
        assert result.summary["missing_phase_eval_count"] == 0
        assert result.summary["failed_phase_eval_count"] == 0
        assert result.summary["decision_document_identity_required_slot_count"] == 2
        assert result.summary["decision_document_identity_ready_slot_count"] == 2
        assert result.summary["missing_decision_document_identity_count"] == 0
        assert result.summary["failed_decision_document_identity_count"] == 0
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


def test_real_package_review_coverage_eval_blocks_forest_specific_without_runtime_scope() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(root)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        east_results_path = Path(manifest["slots"][0]["results_path"])
        east_summary = json.loads(east_results_path.read_text(encoding="utf-8"))
        east_summary.pop("runtime_forest_scope")
        east_results_path.write_text(json.dumps(east_summary, sort_keys=True), encoding="utf-8")

        result = run_real_package_review_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        slot = next(
            slot
            for slot in result.summary["slots"]
            if slot["slot_id"] == "east-crazies-current-promotion"
        )
        assert slot["runtime_forest_scope_gate"]["required"] is True
        assert slot["runtime_forest_scope_gate"]["passed"] is False
        assert "runtime_forest_scope_missing" in slot["failure_reasons"]
        assert result.summary["failure_category_counts"]["runtime_forest_scope_missing"] == 1


def test_real_package_review_coverage_eval_requires_reviewer_ready_phase_eval() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(
            root,
            missing_phase_eval_review_id="v1-cg-ecid-compliance-review",
        )

        result = run_real_package_review_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        assert result.summary["missing_phase_eval_count"] == 1
        assert result.summary["failed_phase_eval_count"] == 1
        slot = next(
            slot
            for slot in result.summary["slots"]
            if slot["slot_id"] == "east-crazies-current-promotion"
        )
        assert slot["phase_eval_gate"]["required"] is True
        assert slot["phase_eval_gate"]["passed"] is False
        assert "phase_eval_missing" in slot["failure_reasons"]
        assert result.summary["failure_category_counts"]["phase_eval_missing"] == 1


def test_real_package_review_coverage_eval_allows_phase_eval_outer_gate_self_reference() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(root)
        phase_eval_path = (
            output_dir
            / "reviews"
            / "v1-cg-ecid-compliance-review"
            / "phase_eval_results.json"
        )
        phase_eval = json.loads(phase_eval_path.read_text(encoding="utf-8"))
        phase_eval["passed"] = False
        phase_eval["reviewer_ready"] = False
        phase_eval["phase_count"] = 5
        phase_eval["passed_phase_count"] = 2
        phase_eval["reviewer_ready_phase_count"] = 2
        phase_eval["blockers"] = [
            {"phase": "evaluation_coverage", "reason": "phase_validation_failed"},
            {"phase": "final_qa_certification_report", "reason": "phase_validation_failed"},
            {"phase": "first_class_eval_trace", "reason": "eval_trace_store_stale"},
        ]
        phase_eval["phases"] = [
            {"name": "catalog_capture", "passed": True, "reviewer_ready": True},
            {"name": "v1_ea_eval", "passed": True, "reviewer_ready": True},
            {"name": "evaluation_coverage", "passed": False, "reviewer_ready": False},
            {
                "name": "final_qa_certification_report",
                "passed": False,
                "reviewer_ready": False,
            },
            {"name": "first_class_eval_trace", "passed": False, "reviewer_ready": False},
        ]
        phase_eval_path.write_text(json.dumps(phase_eval, sort_keys=True), encoding="utf-8")

        result = run_real_package_review_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is True
        slot = next(
            slot
            for slot in result.summary["slots"]
            if slot["slot_id"] == "east-crazies-current-promotion"
        )
        assert slot["phase_eval_gate"]["passed"] is True
        assert slot["phase_eval_gate"]["self_reference_allowed"] is True
        assert slot["phase_eval_gate"]["self_reference_phase_names"] == [
            "evaluation_coverage",
            "final_qa_certification_report",
            "first_class_eval_trace",
        ]


def test_real_package_review_coverage_eval_requires_decision_document_identity() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(
            root,
            missing_decision_identity_review_id="v1-cg-ecid-compliance-review",
        )

        result = run_real_package_review_coverage_eval(
            output_dir=output_dir,
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        assert result.summary["missing_decision_document_identity_count"] == 1
        assert result.summary["failed_decision_document_identity_count"] == 1
        slot = next(
            slot
            for slot in result.summary["slots"]
            if slot["slot_id"] == "east-crazies-current-promotion"
        )
        assert slot["decision_document_identity_gate"]["required"] is True
        assert slot["decision_document_identity_gate"]["passed"] is False
        assert "decision_document_identity_missing" in slot["failure_reasons"]
        assert (
            result.summary["failure_category_counts"]["decision_document_identity_missing"]
            == 1
        )


def test_real_package_review_coverage_eval_rejects_missing_required_slot() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        output_dir = root / "source_library"
        manifest_path = _write_manifest(
            root,
            include_expansion_slot=False,
        )

        with pytest.raises(
            ValueError,
            match="required_coverage_class_ids must exactly match",
        ):
            run_real_package_review_coverage_eval(
                output_dir=output_dir,
                manifest_path=manifest_path,
            )


def test_committed_real_package_review_coverage_manifest_archives_south_plateau_slot() -> None:
    manifest = json.loads(COMMITTED_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == REAL_PACKAGE_REVIEW_COVERAGE_SCHEMA_VERSION
    assert manifest["required_coverage_class_ids"] == [
        "current_promotion_reviewer_ready",
        "forest_specific_reviewer_ready",
    ]
    assert manifest["forest_specific_runtime_scope_policy"] == {
        "mode": "fail_closed",
        "applies_to_coverage_class_ids": [
            "current_promotion_reviewer_ready",
            "forest_specific_reviewer_ready",
        ],
        "required_runtime_signal": "v1_ea_eval.summary.runtime_forest_scope",
        "rule": (
            "Required current-promotion and forest-specific reviewer-ready slots "
            "must fail unless the V1 eval runtime forest-plan scope identifies the "
            "slot forest_unit_id as applicable."
        ),
    }
    assert manifest["phase_eval_policy"] == {
        "mode": "fail_closed",
        "applies_to_expected_contract_statuses": [
            "reviewer_ready",
        ],
        "required_runtime_signal": "source_library/reviews/<review_id>/phase_eval_results.json",
        "rule": (
            "Required reviewer-ready real-package slots must fail unless phase-eval "
            "exists, matches the review and source set, passes, reports "
            "reviewer_ready=true, and has no blockers."
        ),
    }
    assert manifest["decision_document_identity_policy"] == {
        "mode": "fail_closed",
        "applies_to_coverage_class_ids": [
            "forest_specific_reviewer_ready",
        ],
        "applies_to_expected_contract_statuses": [
            "reviewer_ready",
        ],
        "required_runtime_signal": (
            "source_library/reviews/<review_id>/forest_plan_context_summary.json."
            "title_page_project_location"
        ),
        "rule": (
            "Required reviewer-ready forest-specific slots must fail unless the "
            "forest-plan resolver summary carries title-page administrative "
            "location evidence for the selected forest or grassland, ranger "
            "district, county, state, and no competing title-page forest unit."
        ),
    }
    assert [item["review_id"] for item in manifest["slots"]] == [
        "v1-cg-ecid-compliance-review",
        "region1-example-beaverhead-deerlodge-south-tobacco-roots-63754",
        "region1-example-bitterroot-front-57341",
        "west-reservoir-67436",
        "region1-example-custer-gallatin-south-otter-58396",
        "region1-example-lolo-tylers-kitchen-66344",
        "region1-example-helena-lewis-and-clark-bonanza-66532",
        "region1-example-idaho-panhandle-lacy-lemoosh-60853",
        "region1-example-nez-perce-clearwater-dead-laundry-57827",
        "region1-example-dakota-prairie-medora-vegetation-management-66886",
        "region1-example-kootenai-trojan-defense-64354",
    ]
    archived_slots = {
        item["review_id"]: item for item in manifest["archived_slots"]
    }
    south_plateau = archived_slots["region1-expansion-south-plateau-landscape-treatment"]
    assert south_plateau["slot_id"] == "south-plateau-reviewer-ready"
    assert south_plateau["usage_policy"] == "historical_evidence_only_not_example"
    assert south_plateau["active_example"] is False
    assert [
        item["coverage_class_id"]
        for item in manifest["slots"]
        if item["coverage_class_id"] == "forest_specific_reviewer_ready"
    ] == [
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
        "forest_specific_reviewer_ready",
    ]
    thresholds = manifest["coverage_thresholds"]
    assert thresholds["required_slot_count"] == 11
    assert thresholds["required_coverage_class_count"] == 2
    assert thresholds["distinct_forest_count_min"] == 10
    assert thresholds["distinct_package_style_count_min"] == 16
    assert thresholds["reviewer_ready_slot_count_min"] == 11
    assert thresholds["typed_blocked_slot_count_min"] == 0


def _write_manifest(
    root: Path,
    *,
    include_expansion_slot: bool = True,
    missing_ready_authority: bool = False,
    missing_phase_eval_review_id: str | None = None,
    missing_decision_identity_review_id: str | None = None,
) -> Path:
    results_dir = root / "results"
    authorities_dir = root / "authorities"
    (authorities_dir / "catalog-east").mkdir(parents=True)
    (authorities_dir / "catalog-south").mkdir(parents=True)
    (authorities_dir / "package-east").mkdir(parents=True)
    (authorities_dir / "package-west").mkdir(parents=True)
    (authorities_dir / "south-intake").mkdir(parents=True)
    replay_context_path = root / "config" / "replay_contexts" / "east.json"
    south_replay_context_path = (
        root
        / "config"
        / "replay_contexts"
        / "region1-expansion-south-plateau-landscape-treatment.json"
    )
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
    south_replay_context_path.write_text(
        json.dumps(
            {
                "review_id": "region1-expansion-south-plateau-landscape-treatment",
                "source_set_id": "source-set-south",
                "catalog_dir": "authorities/catalog-south",
                "package_path": "authorities/south-intake",
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    review_payloads = [
        {
            "review_id": "v1-cg-ecid-compliance-review",
            "source_set_id": "source-set-east",
            "passed": True,
            "contract_status": "reviewer_ready",
            "forest_unit_id": "custer-gallatin-nf",
            "package_style_tags": ["clean_baseline"],
            "runtime_forest_scope": _runtime_scope(
                "custer-gallatin-nf",
                "custer_gallatin",
                "custer_gallatin",
            ),
            "actual_overall_passed": True,
            "broader_ea_passed": True,
            "forest_plan_passed": True,
            "failure_category_counts": {},
            "forest_plan_failure_category_counts": {},
        },
        {
            "review_id": "west-reservoir-67436",
            "source_set_id": "source-set-west",
            "passed": True,
            "contract_status": "typed_blocked",
            "forest_unit_id": "flathead-nf",
            "package_style_tags": ["live_external_noisy"],
            "actual_overall_passed": False,
            "broader_ea_passed": False,
            "forest_plan_passed": False,
            "failure_category_counts": {"review_artifact_missing": 4},
            "forest_plan_failure_category_counts": {"review_artifact_missing": 4},
        },
    ]
    if include_expansion_slot:
        review_payloads.append(
            {
                "review_id": "region1-expansion-south-plateau-landscape-treatment",
                "source_set_id": "source-set-south",
                "passed": True,
                "contract_status": "reviewer_ready",
                "forest_unit_id": "custer-gallatin-nf",
                "package_style_tags": ["reviewer_ready_expansion"],
                "actual_overall_passed": True,
                "broader_ea_passed": True,
                "forest_plan_passed": True,
                "failure_category_counts": {},
                "forest_plan_failure_category_counts": {},
            }
        )
    review_paths = []
    for index, payload in enumerate(review_payloads, start=1):
        path = results_dir / f"review-{index}.json"
        _write_json(path, payload)
        review_paths.append(path)
        if (
            payload["contract_status"] == "reviewer_ready"
            and payload["review_id"] != missing_phase_eval_review_id
        ):
            _write_phase_eval(root, payload)
        if (
            payload["contract_status"] == "reviewer_ready"
            and payload["review_id"] != missing_decision_identity_review_id
        ):
            _write_forest_context_summary(root, payload)
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
            "slot_id": "west-reservoir-typed-blocked",
            "label": "West Reservoir typed-blocked replay quarantine",
            "review_id": "west-reservoir-67436",
            "package_label": "West Reservoir",
            "coverage_class_id": "alternate_package_typed_blocked",
            "forest_unit_id": "flathead-nf",
            "eval_file": "config/v1_west_reservoir_real_ea_eval.json",
            "results_path": str(review_paths[1]),
            "required": True,
            "expected_contract_status": "typed_blocked",
            "package_authority": {
                "intake_package_path": str(
                    authorities_dir / ("missing-west" if missing_ready_authority else "package-west")
                ),
            },
        },
    ]
    if include_expansion_slot:
        slots.append(
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
                    "replay_context_path": str(south_replay_context_path),
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
                "alternate_package_typed_blocked",
                "current_promotion_reviewer_ready",
                "expansion_reviewer_ready",
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
            "phase_eval_policy": {
                "mode": "fail_closed",
                "applies_to_expected_contract_statuses": ["reviewer_ready"],
                "required_runtime_signal": "source_library/reviews/<review_id>/phase_eval_results.json",
                "rule": (
                    "Required reviewer-ready real-package slots must fail unless phase-eval "
                    "exists, matches the review and source set, passes, reports "
                    "reviewer_ready=true, and has no blockers."
                ),
            },
            "decision_document_identity_policy": {
                "mode": "fail_closed",
                "applies_to_coverage_class_ids": [
                    "current_promotion_reviewer_ready",
                    "expansion_reviewer_ready",
                ],
                "applies_to_expected_contract_statuses": ["reviewer_ready"],
                "required_runtime_signal": (
                    "source_library/reviews/<review_id>/forest_plan_context_summary.json."
                    "title_page_project_location"
                ),
                "rule": (
                    "Required reviewer-ready all-forest slots must fail unless the "
                    "forest-plan resolver summary carries title-page administrative "
                    "location evidence."
                ),
            },
            "slots": slots,
        },
    )
    return manifest_path


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")


def _write_phase_eval(root: Path, review_payload: dict) -> None:
    phase_count = 3
    _write_json(
        root
        / "source_library"
        / "reviews"
        / review_payload["review_id"]
        / "phase_eval_results.json",
        {
            "review_id": review_payload["review_id"],
            "source_set_id": review_payload["source_set_id"],
            "passed": True,
            "reviewer_ready": True,
            "phase_count": phase_count,
            "passed_phase_count": phase_count,
            "reviewer_ready_phase_count": phase_count,
            "blockers": [],
        },
    )


def _write_forest_context_summary(root: Path, review_payload: dict) -> None:
    review_id = review_payload["review_id"]
    runtime_scope = review_payload.get("runtime_forest_scope")
    scope_status = (
        runtime_scope.get("actual_scope_status")
        if isinstance(runtime_scope, dict)
        else "custer_gallatin"
    )
    _write_json(
        root / "source_library" / "reviews" / review_id / "forest_plan_context_summary.json",
        {
            "review_id": review_id,
            "source_set_id": review_payload["source_set_id"],
            "scope_status": scope_status,
            "title_page_project_location": {
                "present": True,
                "resolution_basis": "decision_notice_fonsi_title_page",
                "forest_unit_name": review_payload["forest_unit_id"],
                "forest_unit_resolved": True,
                "ranger_district_names": ["Example Ranger District"],
                "ranger_district_count": 1,
                "counties": ["Example County"],
                "county_count": 1,
                "state": "Montana",
                "other_forest_unit_names": [],
                "other_forest_unit_count": 0,
                "evidence_refs": [
                    {
                        "source_record_id": "EA-PACKAGE-001",
                        "citation_label": "EA-PACKAGE-001",
                        "chunk_id": "chunk:example",
                        "title": "Decision Notice and FONSI",
                        "page": 1,
                        "artifact_path": "/tmp/example.pdf",
                        "artifact_sha256": "sha",
                        "resolution_basis": "decision_notice_fonsi_title_page",
                    }
                ],
            },
        },
    )


def _runtime_scope(
    forest_unit_id: str,
    expected_scope_status: str,
    actual_scope_status: str,
) -> dict:
    return {
        "required": True,
        "passed": actual_scope_status == expected_scope_status,
        "expected_forest_unit_id": forest_unit_id,
        "expected_scope_status": expected_scope_status,
        "actual_scope_status": actual_scope_status,
        "scope_status_expectation_present": True,
        "scope_status_expectation_passed": actual_scope_status == expected_scope_status,
        "failure_reasons": (
            []
            if actual_scope_status == expected_scope_status
            else ["runtime_scope_status_mismatch"]
        ),
    }
