from __future__ import annotations

from pathlib import Path
import json
import tempfile

from usfs_r1_ea_sources.forest_plan_profile_eval import run_forest_plan_profile_eval


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "config" / "region1_forest_plan_profile_eval_coverage_v1.json"
READINESS = ROOT / "config" / "region1_forest_plan_readiness_nepa_3d_v1.json"
PROFILES = ROOT / "config" / "forest_plan_profiles.json"


def test_profile_eval_writes_outputs_and_fails_closed_on_live_incomplete_roster() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        result = run_forest_plan_profile_eval(
            output_dir=Path(tmp),
            manifest_path=MANIFEST,
        )

        assert result.summary["passed"] is False
        assert result.output_path.exists()
        assert result.report_path.exists()
        assert result.summary["covered_profile_count"] == 3
        assert result.summary["fixture_contract_defined_profile_count"] == 0
        assert result.summary["not_started_profile_count"] == 7
        assert result.summary["profile_failure_count"] == 7
        assert result.summary["active_source_set_ids"] == ["source-set-5e65d845ce77e1a0"]
        assert _threshold_failure_names(result.summary) == {
            "covered_profile_count_below_minimum",
            "not_started_profile_count_above_maximum",
        }
        assert "beaverhead-deerlodge-nf" not in result.summary["profiles_below_floor_ids"]
        assert "flathead-nf" not in result.summary["profiles_below_floor_ids"]


def test_profile_eval_rejects_missing_profile_floors() -> None:
    manifest = _read_json(MANIFEST)
    manifest["profiles"][0].pop("minimum_positive_case_count")

    with tempfile.TemporaryDirectory() as tmp:
        manifest_path = Path(tmp) / "manifest.json"
        _write_json(manifest_path, manifest)
        result = run_forest_plan_profile_eval(
            output_dir=Path(tmp),
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        check = _check(result.summary, "manifest_profile_contracts_well_formed")
        assert check["passed"] is False
        assert check["details"]["invalid_profile_contracts"]


def test_profile_eval_rejects_duplicate_manifest_profile_ids() -> None:
    manifest = _read_json(MANIFEST)
    manifest["profiles"].append(dict(manifest["profiles"][0]))

    with tempfile.TemporaryDirectory() as tmp:
        manifest_path = Path(tmp) / "manifest.json"
        _write_json(manifest_path, manifest)
        result = run_forest_plan_profile_eval(
            output_dir=Path(tmp),
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        check = _check(result.summary, "manifest_profile_ids_are_unique")
        assert check["passed"] is False
        assert check["details"]["duplicate_profile_ids"] == ["custer-gallatin-nf"]


def test_profile_eval_rejects_missing_readiness_row() -> None:
    readiness = _read_json(READINESS)
    readiness["profile_rows"] = [
        row for row in readiness["profile_rows"] if row["forest_unit_id"] != "lolo-nf"
    ]

    with tempfile.TemporaryDirectory() as tmp:
        readiness_path = Path(tmp) / "readiness.json"
        manifest_path = Path(tmp) / "manifest.json"
        _write_json(readiness_path, readiness)

        manifest = _read_json(MANIFEST)
        manifest["readiness_path"] = str(readiness_path)
        manifest["forest_plan_profiles_path"] = str(PROFILES)
        _write_json(manifest_path, manifest)

        result = run_forest_plan_profile_eval(
            output_dir=Path(tmp),
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        check = _check(result.summary, "readiness_roster_matches_manifest")
        assert check["passed"] is False
        assert check["details"]["missing_in_readiness"] == ["lolo-nf"]


def test_profile_eval_rejects_milestone_2_profile_that_slips_back_to_placeholder_contract() -> None:
    readiness = _read_json(READINESS)
    flathead = next(
        row for row in readiness["profile_rows"] if row["forest_unit_id"] == "flathead-nf"
    )
    flathead["applicability_eval_coverage"] = {
        "status": "fixture_contract_defined",
        "positive_case_count": 1,
        "hard_negative_case_count": 1,
        "selected_profile_compliance_case_count": 0,
        "fixture_family_ids": [
            "scope_positive",
            "custer_hard_negative",
        ],
    }

    with tempfile.TemporaryDirectory() as tmp:
        readiness_path = Path(tmp) / "readiness.json"
        manifest_path = Path(tmp) / "manifest.json"
        _write_json(readiness_path, readiness)

        manifest = _read_json(MANIFEST)
        manifest["readiness_path"] = str(readiness_path)
        manifest["forest_plan_profiles_path"] = str(PROFILES)
        _write_json(manifest_path, manifest)

        result = run_forest_plan_profile_eval(
            output_dir=Path(tmp),
            manifest_path=manifest_path,
        )

        assert result.summary["passed"] is False
        flathead_result = next(
            profile
            for profile in result.summary["profiles"]
            if profile["forest_unit_id"] == "flathead-nf"
        )
        assert flathead_result["passed"] is False
        assert set(flathead_result["failure_reasons"]) == {
            "coverage_status_below_required_floor",
            "positive_case_floor_not_met",
            "hard_negative_case_floor_not_met",
            "selected_profile_compliance_floor_not_met",
            "required_fixture_families_missing",
        }


def _check(summary: dict, name: str) -> dict:
    return next(check for check in summary["contract_checks"] if check["name"] == name)


def _threshold_failure_names(summary: dict) -> set[str]:
    return {failure["name"] for failure in summary["threshold_failures"]}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
